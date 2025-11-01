"""
Mathematical utilities for arbitrage betting calculations.

This module provides core mathematical functions needed for arbitrage calculations
including implied probabilities, profit margins, Kelly staking, and validation.
"""

import math
from typing import List, Dict, Optional, Tuple, Union
from decimal import Decimal, getcontext
from dataclasses import dataclass


# Set precision for financial calculations
getcontext().prec = 28


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity with its legs."""
    legs: List[Dict]
    implied_probability: float
    profit_margin: float
    total_implied: float


@dataclass 
class BettingLeg:
    """Represents a single betting leg in an arbitrage opportunity."""
    bookmaker: str
    outcome: str
    odds: Decimal
    implied_probability: Decimal
    stake: Optional[Decimal] = None
    potential_return: Optional[Decimal] = None


def calculate_implied_probabilities(odds_list: List[Union[float, str, Decimal]]) -> List[Decimal]:
    """
    Calculate implied probabilities from a list of odds.
    
    Implied probability is calculated as 1/odds for decimal odds.
    For American odds, converts to decimal first.
    
    Args:
        odds_list: List of odds (can be decimal, American, or fractional)
        
    Returns:
        List of implied probabilities as Decimal objects
        
    Raises:
        ValueError: If odds are invalid or zero
        TypeError: If odds format is not supported
    """
    if not odds_list:
        raise ValueError("Odds list cannot be empty")
    
    implied_probs = []
    
    for odds in odds_list:
        # Convert to Decimal for precision
        decimal_odds = Decimal(str(odds))
        
        # Validate odds
        if decimal_odds <= 0:
            raise ValueError(f"Odds must be positive, got: {decimal_odds}")
        
        if decimal_odds < 1.01 and decimal_odds < 1.01:
            raise ValueError(f"Odds too low, minimum is 1.01: {decimal_odds}")
        
        # Calculate implied probability
        implied_prob = Decimal('1') / decimal_odds
        implied_probs.append(implied_prob)
        
    return implied_probs


def calculate_profit_margin(odds_list: List[Union[float, str, Decimal]]) -> float:
    """
    Calculate the profit margin from a list of odds.
    
    Profit margin = (1 - 1/sum(1/odds)) * 100%
    Positive margin indicates arbitrage opportunity
    
    Args:
        odds_list: List of decimal odds
        
    Returns:
        Profit margin as percentage (float)
        
    Raises:
        ValueError: If odds list is empty or invalid
    """
    if not odds_list:
        raise ValueError("Odds list cannot be empty")
    
    try:
        implied_probs = calculate_implied_probabilities(odds_list)
        total_implied = sum(implied_probs)
        
        # Profit margin calculation
        margin = (Decimal('1') - Decimal('1') / Decimal(str(total_implied))) * Decimal('100')
        
        return float(margin)
        
    except (ValueError, ZeroDivisionError, TypeError) as e:
        raise ValueError(f"Error calculating profit margin: {str(e)}")


def calculate_kelly_stakes(opportunity: ArbitrageOpportunity, bankroll: Union[float, str, Decimal]) -> Dict[str, Decimal]:
    """
    Calculate Kelly criterion stakes for an arbitrage opportunity.
    
    Kelly formula for optimal stake sizing.
    Modified for arbitrage to maximize guaranteed profit.
    
    Args:
        opportunity: ArbitrageOpportunity object
        bankroll: Total bankroll available for betting
        
    Returns:
        Dictionary mapping leg indices to optimal stakes
        
    Raises:
        ValueError: If bankroll is invalid or opportunity is not profitable
    """
    if opportunity.profit_margin <= 0:
        raise ValueError("No arbitrage opportunity - profit margin must be positive")
    
    bankroll_decimal = Decimal(str(bankroll))
    if bankroll_decimal <= 0:
        raise ValueError("Bankroll must be positive")
    
    # Kelly staking for arbitrage (simplified version)
    # Optimal stake = bankroll * margin / (odds - 1)
    stakes = {}
    
    for i, leg in enumerate(opportunity.legs):
        odds = Decimal(str(leg['odds']))
        
        # Calculate Kelly stake for this leg
        # stake = bankroll * profit_margin / 100 * (implied_prob / total_implied)
        stake = bankroll_decimal * Decimal(str(opportunity.profit_margin / 100)) * \
                Decimal(str(leg['implied_probability'])) / Decimal(str(opportunity.total_implied))
        
        stakes[f"leg_{i}"] = stake
    
    return stakes


def validate_arbitrage_opportunity(legs: List[Dict]) -> bool:
    """
    Validate if a set of legs constitutes a valid arbitrage opportunity.
    
    Args:
        legs: List of betting legs with 'odds' and 'outcome' fields
        
    Returns:
        True if valid arbitrage opportunity, False otherwise
    """
    if not legs or len(legs) < 2:
        return False
    
    try:
        # Extract odds and check if sum of implied probabilities < 1
        odds_list = [Decimal(str(leg['odds'])) for leg in legs]
        implied_probs = calculate_implied_probabilities(odds_list)
        total_implied = sum(implied_probs)
        
        # Arbitrage exists if total implied probability < 1 (i.e., positive margin)
        return total_implied < Decimal('1')
        
    except (ValueError, KeyError, TypeError):
        return False


def calculate_lay_bet_requirements(
    back_odds: Union[float, Decimal],
    lay_odds: Union[float, Decimal],
    stake: Union[float, Decimal],
    commission: float = 0.05
) -> Dict[str, Decimal]:
    """
    Calculate lay bet requirements for exchange betting.
    
    Args:
        back_odds: Back odds (decimal)
        lay_odds: Lay odds (decimal)
        stake: Stake amount
        commission: Exchange commission (default 5%)
        
    Returns:
        Dictionary with lay stake, liability, and potential returns
        
    Raises:
        ValueError: If odds or stake are invalid
    """
    back_decimal = Decimal(str(back_odds))
    lay_decimal = Decimal(str(lay_odds))
    stake_decimal = Decimal(str(stake))
    
    if back_decimal <= 0 or lay_decimal <= 0:
        raise ValueError("Odds must be positive")
    
    if stake_decimal <= 0:
        raise ValueError("Stake must be positive")
    
    # Calculate lay stake to match liability
    # Liability = lay_stake * (lay_odds - 1) * (1 - commission)
    # Should equal potential profit from back bet
    lay_stake = stake_decimal * back_decimal / (lay_decimal * (Decimal('1') - Decimal(str(commission))))
    
    # Calculate liability
    liability = lay_stake * (lay_decimal - Decimal('1')) * (Decimal('1') - Decimal(str(commission)))
    
    # Calculate potential returns/losses
    back_profit = stake_decimal * (back_decimal - Decimal('1'))
    lay_profit = lay_stake  # Win when lay bet wins
    lay_loss = -liability  # Lose when back bet wins
    
    return {
        'lay_stake': lay_stake.quantize(Decimal('0.01')),
        'liability': liability.quantize(Decimal('0.01')),
        'back_profit': back_profit.quantize(Decimal('0.01')),
        'lay_profit': lay_profit.quantize(Decimal('0.01')),
        'lay_loss': lay_loss.quantize(Decimal('0.01')),
        'net_profit_if_back_wins': (back_profit + lay_loss).quantize(Decimal('0.01')),
        'net_profit_if_lay_wins': (lay_profit - stake_decimal).quantize(Decimal('0.01'))
    }


def stake_optimization(
    opportunities: List[ArbitrageOpportunity],
    bankroll: Union[float, str, Decimal],
    max_stake_percentage: float = 0.1,
    min_profit_margin: float = 0.5
) -> Dict[str, Dict[str, Decimal]]:
    """
    Optimize stake allocation across multiple arbitrage opportunities.
    
    Args:
        opportunities: List of ArbitrageOpportunity objects
        bankroll: Total bankroll
        max_stake_percentage: Maximum percentage of bankroll per opportunity
        min_profit_margin: Minimum profit margin to consider
        
    Returns:
        Dictionary mapping opportunity IDs to optimal stakes
    """
    bankroll_decimal = Decimal(str(bankroll))
    max_stake_amount = bankroll_decimal * Decimal(str(max_stake_percentage))
    
    # Filter profitable opportunities
    profitable_ops = [
        opp for opp in opportunities 
        if opp.profit_margin >= min_profit_margin
    ]
    
    if not profitable_ops:
        return {}
    
    # Sort by profit margin (highest first)
    profitable_ops.sort(key=lambda x: x.profit_margin, reverse=True)
    
    allocation = {}
    remaining_bankroll = bankroll_decimal
    
    for i, opportunity in enumerate(profitable_ops):
        # Calculate optimal stake using Kelly criterion
        stakes = calculate_kelly_stakes(opportunity, remaining_bankroll)
        total_stake = sum(stakes.values())
        
        # Adjust if stake exceeds limits
        if total_stake > max_stake_amount:
            scale_factor = max_stake_amount / total_stake
            stakes = {k: v * scale_factor for k, v in stakes.items()}
            total_stake = sum(stakes.values())
        
        # Only allocate if we have sufficient bankroll
        if total_stake <= remaining_bankroll:
            allocation[f"opportunity_{i}"] = stakes
            remaining_bankroll -= total_stake
        else:
            # Scale down to fit available bankroll
            if total_stake > 0:
                scale_factor = remaining_bankroll / total_stake
                stakes = {k: v * scale_factor for k, v in stakes.items()}
                allocation[f"opportunity_{i}"] = stakes
                remaining_bankroll = Decimal('0')
            break
    
    return allocation


def calculate_arbitrage_metrics(odds_list: List[Union[float, str, Decimal]]) -> Dict[str, float]:
    """
    Calculate comprehensive arbitrage metrics for a set of odds.
    
    Args:
        odds_list: List of decimal odds
        
    Returns:
        Dictionary containing all relevant metrics
    """
    if not odds_list:
        raise ValueError("Odds list cannot be empty")
    
    implied_probs = calculate_implied_probabilities(odds_list)
    total_implied = sum(implied_probs)
    profit_margin = float((Decimal('1') - Decimal('1') / Decimal(str(total_implied))) * Decimal('100'))
    
    return {
        'total_implied_probability': float(total_implied),
        'profit_margin_percent': profit_margin,
        'is_arbitrage': profit_margin > 0,
        'num_legs': len(odds_list),
        'average_odds': float(sum(Decimal(str(odd)) for odd in odds_list) / len(odds_list)),
        'max_odds': float(max(Decimal(str(odd)) for odd in odds_list)),
        'min_odds': float(min(Decimal(str(odd)) for odd in odds_list)),
        'odds_range': float(max(Decimal(str(odd)) for odd in odds_list) - 
                          min(Decimal(str(odd)) for odd in odds_list))
    }


def calculate_combined_odds(odds_list: List[Union[float, str, Decimal]], combine_type: str = 'harmonic') -> Decimal:
    """
    Calculate combined odds from multiple legs using different methods.
    
    Args:
        odds_list: List of decimal odds
        combine_type: Method to combine odds ('harmonic', 'arithmetic', 'geometric')
        
    Returns:
        Combined odds as Decimal
        
    Raises:
        ValueError: If combine_type is not supported
    """
    if not odds_list:
        raise ValueError("Odds list cannot be empty")
    
    odds_decimals = [Decimal(str(odd)) for odd in odds_list]
    
    if combine_type == 'harmonic':
        # Harmonic mean (most common for arbitrage)
        reciprocal_sum = sum(Decimal('1') / odd for odd in odds_decimals)
        return Decimal(len(odds_decimals)) / reciprocal_sum
    
    elif combine_type == 'arithmetic':
        # Arithmetic mean
        return sum(odds_decimals) / len(odds_decimals)
    
    elif combine_type == 'geometric':
        # Geometric mean
        product = Decimal('1')
        for odd in odds_decimals:
            product *= odd
        return product ** (Decimal('1') / len(odds_decimals))
    
    else:
        raise ValueError(f"Unsupported combine_type: {combine_type}. Use 'harmonic', 'arithmetic', or 'geometric'")


def calculate_expected_value(odds: Union[float, Decimal], true_probability: float) -> Decimal:
    """
    Calculate expected value for a single bet.
    
    Args:
        odds: Decimal odds
        true_probability: True probability of winning (0 to 1)
        
    Returns:
        Expected value as Decimal
    """
    odds_decimal = Decimal(str(odds))
    prob_decimal = Decimal(str(true_probability))
    
    # EV = (odds * prob) - 1
    expected_value = (odds_decimal * prob_decimal) - Decimal('1')
    
    return expected_value.quantize(Decimal('0.0001'))