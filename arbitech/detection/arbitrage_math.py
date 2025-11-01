"""
Advanced Arbitrage Mathematical Engine

This module provides sophisticated mathematical calculations for arbitrage detection,
including market analysis, stake allocation algorithms, and overround calculations.
It extends the basic math_utils with advanced financial mathematics.
"""

import math
from typing import List, Dict, Optional, Tuple, Union, Any
from decimal import Decimal, getcontext, ROUND_HALF_UP
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import numpy as np
from enum import Enum

# Configure decimal precision for financial calculations
getcontext().prec = 50


class ArbitrageStrategy(Enum):
    """Types of arbitrage strategies supported."""
    TWO_WAY = "2-way"
    THREE_WAY = "3-way" 
    COMPLEX_MULTI = "complex_multi"
    CROSS_MARKET = "cross_market"
    TEMPORAL = "temporal"


class MarketType(Enum):
    """Types of betting markets."""
    MATCH_WINNER = "match_winner"
    OVER_UNDER = "over_under"
    HANDICAP = "handicap"
    CORRECT_SCORE = "correct_score"
    HT_FT = "half_time_full_time"
    ANOTHER_BETTING = "another_betting"


@dataclass
class MarketLeg:
    """Represents a single market leg in an arbitrage opportunity."""
    bookmaker: str
    market_type: MarketType
    selection: str
    odds: Decimal
    implied_probability: Decimal
    stake: Optional[Decimal] = None
    expected_return: Optional[Decimal] = None
    commission_rate: Decimal = Decimal('0')
    liquidity: Optional[Decimal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArbitrageOpportunity:
    """Represents a complete arbitrage opportunity."""
    opportunity_id: str
    strategy: ArbitrageStrategy
    legs: List[MarketLeg]
    total_implied_probability: Decimal
    profit_margin: Decimal
    roi_percentage: Decimal
    risk_score: Decimal
    confidence_level: Decimal
    detection_timestamp: datetime
    expiry_time: Optional[datetime] = None
    complexity_score: Decimal = Decimal('0')
    market_efficiency: Decimal = Decimal('0')
    calculation_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StakeAllocation:
    """Stake allocation result for an arbitrage opportunity."""
    opportunity_id: str
    total_stake: Decimal
    individual_stakes: Dict[str, Decimal]
    optimal_profit: Decimal
    risk_adjusted_return: Decimal
    kelly_percentage: Decimal
    allocation_metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedArbitrageMath:
    """
    Advanced mathematical engine for arbitrage calculations.
    
    This class provides sophisticated mathematical models for arbitrage detection,
    profit optimization, and risk management across different market types.
    """
    
    def __init__(self, risk_tolerance: Decimal = Decimal('0.1')):
        """
        Initialize the arbitrage math engine.
        
        Args:
            risk_tolerance: Risk tolerance for stake allocation (0.0 to 1.0)
        """
        self.risk_tolerance = risk_tolerance
        self.logger = logging.getLogger(__name__)
        
        # Mathematical constants
        self.E = Decimal(str(math.e))
        self.PI = Decimal(str(math.pi))
        
        # Market-specific parameters
        self.market_defaults = {
            MarketType.MATCH_WINNER: {
                'min_odds': Decimal('1.01'),
                'max_odds': Decimal('1000.0'),
                'typical_commission': Decimal('0.05'),
                'complexity_factor': Decimal('1.0')
            },
            MarketType.OVER_UNDER: {
                'min_odds': Decimal('1.01'),
                'max_odds': Decimal('1000.0'),
                'typical_commission': Decimal('0.05'),
                'complexity_factor': Decimal('1.2')
            },
            MarketType.HANDICAP: {
                'min_odds': Decimal('1.01'),
                'max_odds': Decimal('1000.0'),
                'typical_commission': Decimal('0.05'),
                'complexity_factor': Decimal('1.5')
            },
            MarketType.CORRECT_SCORE: {
                'min_odds': Decimal('1.01'),
                'max_odds': Decimal('1000.0'),
                'typical_commission': Decimal('0.05'),
                'complexity_factor': Decimal('2.0')
            }
        }

    def detect_arbitrage_opportunity(
        self,
        legs: List[MarketLeg],
        strategy: ArbitrageStrategy,
        minimum_profit_margin: Decimal = Decimal('0.5')
    ) -> Optional[ArbitrageOpportunity]:
        """
        Detect arbitrage opportunities from a list of market legs.
        
        Args:
            legs: List of MarketLeg objects
            strategy: Type of arbitrage strategy to apply
            minimum_profit_margin: Minimum profit margin required
            
        Returns:
            ArbitrageOpportunity object if found, None otherwise
            
        Raises:
            ValueError: If inputs are invalid
        """
        if not legs or len(legs) < 2:
            raise ValueError("At least 2 legs required for arbitrage detection")
        
        # Validate and sanitize legs
        validated_legs = self._validate_legs(legs)
        
        # Calculate total implied probability
        total_implied = self._calculate_total_implied_probability(validated_legs)
        
        # Check if arbitrage exists
        if total_implied >= Decimal('1') - minimum_profit_margin / Decimal('100'):
            return None
        
        # Calculate profit margin
        profit_margin = self._calculate_profit_margin(total_implied)
        
        if profit_margin < minimum_profit_margin:
            return None
        
        # Create opportunity
        opportunity = self._create_arbitrage_opportunity(
            legs=validated_legs,
            strategy=strategy,
            total_implied=total_implied,
            profit_margin=profit_margin
        )
        
        return opportunity

    def _validate_legs(self, legs: List[MarketLeg]) -> List[MarketLeg]:
        """Validate and sanitize market legs."""
        validated = []
        
        for leg in legs:
            # Validate odds
            if leg.odds <= 0:
                self.logger.warning(f"Invalid odds for {leg.bookmaker}: {leg.odds}")
                continue
            
            # Validate implied probability
            if leg.implied_probability <= 0 or leg.implied_probability > Decimal('2'):
                self.logger.warning(f"Invalid implied probability for {leg.bookmaker}: {leg.implied_probability}")
                continue
            
            # Check for duplicate bookmakers in same market type
            existing = next((l for l in validated if l.bookmaker == leg.bookmaker and l.market_type == leg.market_type), None)
            if existing:
                # Keep the better odds
                if leg.odds > existing.odds:
                    validated.remove(existing)
                    validated.append(leg)
            else:
                validated.append(leg)
        
        return validated

    def _calculate_total_implied_probability(self, legs: List[MarketLeg]) -> Decimal:
        """Calculate total implied probability accounting for commissions."""
        total = Decimal('0')
        
        for leg in legs:
            # Adjust for commission
            adjusted_probability = leg.implied_probability * (Decimal('1') - leg.commission_rate)
            total += adjusted_probability
        
        return total

    def _calculate_profit_margin(self, total_implied: Decimal) -> Decimal:
        """Calculate profit margin from total implied probability."""
        if total_implied <= 0:
            return Decimal('0')
        
        profit_margin = (Decimal('1') - Decimal('1') / total_implied) * Decimal('100')
        return profit_margin.quantize(Decimal('0.0001'))

    def _create_arbitrage_opportunity(
        self,
        legs: List[MarketLeg],
        strategy: ArbitrageStrategy,
        total_implied: Decimal,
        profit_margin: Decimal
    ) -> ArbitrageOpportunity:
        """Create a complete arbitrage opportunity object."""
        
        # Calculate ROI
        roi = profit_margin / Decimal('100')
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(legs, strategy)
        
        # Calculate confidence level
        confidence = self._calculate_confidence_level(legs, profit_margin)
        
        # Calculate complexity score
        complexity = self._calculate_complexity_score(legs, strategy)
        
        # Calculate market efficiency
        efficiency = self._calculate_market_efficiency(legs)
        
        return ArbitrageOpportunity(
            opportunity_id=f"ARB_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            strategy=strategy,
            legs=legs,
            total_implied_probability=total_implied,
            profit_margin=profit_margin,
            roi_percentage=roi * Decimal('100'),
            risk_score=risk_score,
            confidence_level=confidence,
            detection_timestamp=datetime.now(),
            complexity_score=complexity,
            market_efficiency=efficiency,
            calculation_metadata={
                'calculation_timestamp': datetime.now(),
                'math_engine_version': '2.0',
                'precision_used': getcontext().prec,
                'risk_tolerance': self.risk_tolerance
            }
        )

    def calculate_optimal_stake_allocation(
        self,
        opportunity: ArbitrageOpportunity,
        total_bankroll: Decimal,
        allocation_strategy: str = 'kelly_conservative'
    ) -> StakeAllocation:
        """
        Calculate optimal stake allocation for an arbitrage opportunity.
        
        Args:
            opportunity: ArbitrageOpportunity object
            total_bankroll: Total available bankroll
            allocation_strategy: Stake allocation strategy ('kelly', 'kelly_conservative', 'equal', 'risk_weighted')
            
        Returns:
            StakeAllocation object with optimal stakes
            
        Raises:
            ValueError: If opportunity is not profitable
        """
        if opportunity.profit_margin <= 0:
            raise ValueError("Opportunity must have positive profit margin")
        
        if total_bankroll <= 0:
            raise ValueError("Bankroll must be positive")
        
        # Calculate base stakes based on strategy
        if allocation_strategy == 'kelly':
            stakes = self._kelly_allocation(opportunity, total_bankroll)
        elif allocation_strategy == 'kelly_conservative':
            stakes = self._kelly_conservative_allocation(opportunity, total_bankroll)
        elif allocation_strategy == 'equal':
            stakes = self._equal_allocation(opportunity, total_bankroll)
        elif allocation_strategy == 'risk_weighted':
            stakes = self._risk_weighted_allocation(opportunity, total_bankroll)
        else:
            raise ValueError(f"Unknown allocation strategy: {allocation_strategy}")
        
        # Calculate metrics
        total_stake = sum(stakes.values())
        optimal_profit = self._calculate_optimal_profit(opportunity, stakes)
        risk_adjusted_return = self._calculate_risk_adjusted_return(opportunity, optimal_profit, total_stake)
        kelly_percentage = self._calculate_kelly_percentage(opportunity, total_stake, total_bankroll)
        
        return StakeAllocation(
            opportunity_id=opportunity.opportunity_id,
            total_stake=total_stake,
            individual_stakes=stakes,
            optimal_profit=optimal_profit,
            risk_adjusted_return=risk_adjusted_return,
            kelly_percentage=kelly_percentage,
            allocation_metadata={
                'allocation_strategy': allocation_strategy,
                'calculation_timestamp': datetime.now(),
                'stakes_normalized': any(stake > total_bankroll * Decimal('0.1') for stake in stakes.values())
            }
        )

    def _kelly_allocation(self, opportunity: ArbitrageOpportunity, bankroll: Decimal) -> Dict[str, Decimal]:
        """Calculate Kelly criterion allocation."""
        stakes = {}
        
        # Kelly fraction for arbitrage: f = (bp - q) / b
        # where b = odds - 1, p = implied probability, q = 1 - p
        profit_factor = opportunity.profit_margin / Decimal('100')
        
        for i, leg in enumerate(opportunity.legs):
            odds_minus_one = leg.odds - Decimal('1')
            
            if odds_minus_one <= 0:
                stake = Decimal('0')
            else:
                # Modified Kelly for arbitrage
                p = leg.implied_probability / opportunity.total_implied_probability
                q = Decimal('1') - p
                b = odds_minus_one
                
                kelly_fraction = (b * p - q) / b
                
                # Apply bankroll
                stake = bankroll * kelly_fraction * profit_factor
                
                # Ensure positive stake
                stake = max(stake, Decimal('0'))
            
            stakes[f"leg_{i}_{leg.bookmaker}"] = stake.quantize(Decimal('0.01'))
        
        return stakes

    def _kelly_conservative_allocation(self, opportunity: ArbitrageOpportunity, bankroll: Decimal) -> Dict[str, Decimal]:
        """Calculate conservative Kelly allocation."""
        stakes = self._kelly_allocation(opportunity, bankroll)
        
        # Apply conservative factor
        conservative_factor = Decimal('0.5')  # Use only 50% of full Kelly
        for key in stakes:
            stakes[key] *= conservative_factor
        
        return stakes

    def _equal_allocation(self, opportunity: ArbitrageOpportunity, bankroll: Decimal) -> Dict[str, Decimal]:
        """Calculate equal stake allocation."""
        num_legs = len(opportunity.legs)
        equal_stake = bankroll / num_legs
        
        stakes = {}
        for i, leg in enumerate(opportunity.legs):
            stakes[f"leg_{i}_{leg.bookmaker}"] = equal_stake
        
        return stakes

    def _risk_weighted_allocation(self, opportunity: ArbitrageOpportunity, bankroll: Decimal) -> Dict[str, Decimal]:
        """Calculate risk-weighted stake allocation."""
        stakes = {}
        
        # Calculate risk weights based on market complexity and confidence
        total_weight = Decimal('0')
        leg_weights = []
        
        for leg in opportunity.legs:
            # Base weight from confidence level
            base_weight = opportunity.confidence_level
            
            # Adjust for market type complexity
            complexity_factor = self.market_defaults.get(leg.market_type, {}).get('complexity_factor', Decimal('1.0'))
            adjusted_weight = base_weight / complexity_factor
            
            # Adjust for commission rate (lower commission = higher weight)
            commission_factor = Decimal('1') - (leg.commission_rate * Decimal('2'))
            final_weight = adjusted_weight * commission_factor
            
            leg_weights.append(final_weight)
            total_weight += final_weight
        
        # Normalize weights and calculate stakes
        for i, (leg, weight) in enumerate(zip(opportunity.legs, leg_weights)):
            normalized_weight = weight / total_weight if total_weight > 0 else Decimal('0')
            stake = bankroll * normalized_weight
            stakes[f"leg_{i}_{leg.bookmaker}"] = stake.quantize(Decimal('0.01'))
        
        return stakes

    def calculate_market_overround(self, odds_list: List[Decimal]) -> Dict[str, Decimal]:
        """
        Calculate market overround for a set of odds.
        
        Overround represents the bookmaker's margin built into the odds.
        
        Args:
            odds_list: List of decimal odds
            
        Returns:
            Dictionary containing overround metrics
            
        Raises:
            ValueError: If odds list is empty or invalid
        """
        if not odds_list:
            raise ValueError("Odds list cannot be empty")
        
        # Calculate implied probabilities
        implied_probs = [Decimal('1') / odds for odds in odds_list]
        total_implied = sum(implied_probs)
        
        # Calculate overround
        overround = (total_implied - Decimal('1')) * Decimal('100')
        overround_decimal = total_implied
        
        # Calculate bookmaker margin percentage
        margin_percentage = (overround / total_implied) * Decimal('100')
        
        # Calculate fair odds (odds without bookmaker margin)
        fair_odds = [Decimal('1') / (prob / total_implied) for prob in implied_probs]
        
        return {
            'total_implied_probability': total_implied,
            'overround_percentage': overround.quantize(Decimal('0.0001')),
            'overround_decimal': overround_decimal.quantize(Decimal('0.0001')),
            'bookmaker_margin_percentage': margin_percentage.quantize(Decimal('0.0001')),
            'fair_odds': [odds.quantize(Decimal('0.001')) for odds in fair_odds],
            'value_odds': [(odds - fair_odds[i]).quantize(Decimal('0.001')) 
                          for i, odds in enumerate(odds_list)],
            'market_efficiency': (Decimal('1') / total_implied).quantize(Decimal('0.0001'))
        }

    def calculate_complex_arbitrage_metrics(
        self,
        opportunities: List[ArbitrageOpportunity]
    ) -> Dict[str, Any]:
        """
        Calculate complex metrics for multiple arbitrage opportunities.
        
        Args:
            opportunities: List of ArbitrageOpportunity objects
            
        Returns:
            Dictionary containing complex arbitrage metrics
        """
        if not opportunities:
            return {}
        
        # Calculate portfolio-level metrics
        total_profit_margin = sum(opp.profit_margin for opp in opportunities)
        avg_profit_margin = total_profit_margin / len(opportunities)
        
        # Calculate risk metrics
        profit_margins = [float(opp.profit_margin) for opp in opportunities]
        margin_std_dev = np.std(profit_margins) if len(profit_margins) > 1 else 0
        margin_sharpe_ratio = (avg_profit_margin - 2.0) / margin_std_dev if margin_std_dev > 0 else 0  # Assuming 2% risk-free rate
        
        # Calculate diversification metrics
        market_types = [opp.strategy for opp in opportunities]
        unique_strategies = len(set(market_types))
        diversification_ratio = unique_strategies / len(opportunities)
        
        # Calculate temporal metrics
        timestamps = [opp.detection_timestamp for opp in opportunities]
        time_span = max(timestamps) - min(timestamps) if len(timestamps) > 1 else timedelta(0)
        opportunity_frequency = len(opportunities) / max(time_span.total_seconds() / 3600, 1)  # per hour
        
        return {
            'portfolio_metrics': {
                'total_opportunities': len(opportunities),
                'total_profit_margin': float(total_profit_margin),
                'average_profit_margin': float(avg_profit_margin),
                'profit_margin_std_dev': margin_std_dev,
                'profit_margin_sharpe_ratio': margin_sharpe_ratio
            },
            'diversification_metrics': {
                'unique_strategies': unique_strategies,
                'diversification_ratio': diversification_ratio,
                'strategy_distribution': {str(strategy): market_types.count(strategy) 
                                        for strategy in set(market_types)}
            },
            'temporal_metrics': {
                'time_span_hours': time_span.total_seconds() / 3600,
                'opportunity_frequency_per_hour': opportunity_frequency,
                'opportunity_density': len(opportunities) / max(time_span.total_seconds() / 86400, 1)  # per day
            },
            'risk_metrics': {
                'average_risk_score': float(sum(opp.risk_score for opp in opportunities) / len(opportunities)),
                'max_risk_opportunity': max(opportunities, key=lambda x: x.risk_score).opportunity_id,
                'risk_concentration': self._calculate_risk_concentration(opportunities)
            },
            'efficiency_metrics': {
                'average_market_efficiency': float(sum(opp.market_efficiency for opp in opportunities) / len(opportunities)),
                'efficiency_variance': float(np.var([float(opp.market_efficiency) for opp in opportunities])),
                'most_efficient_market': max(opportunities, key=lambda x: x.market_efficiency).opportunity_id
            }
        }

    def _calculate_risk_score(self, legs: List[MarketLeg], strategy: ArbitrageStrategy) -> Decimal:
        """Calculate risk score for an arbitrage opportunity."""
        risk_score = Decimal('0')
        
        # Base risk from number of legs
        leg_risk = len(legs) * Decimal('0.1')
        risk_score += leg_risk
        
        # Risk from market complexity
        complexity_risk = sum(
            self.market_defaults.get(leg.market_type, {}).get('complexity_factor', Decimal('1.0'))
            for leg in legs
        ) / len(legs)
        risk_score += complexity_risk * Decimal('0.2')
        
        # Risk from commission variance
        if legs:
            commission_rates = [leg.commission_rate for leg in legs]
            commission_std = np.std([float(rate) for rate in commission_rates])
            risk_score += Decimal(str(commission_std)) * Decimal('0.5')
        
        # Risk from strategy type
        strategy_risks = {
            ArbitrageStrategy.TWO_WAY: Decimal('0.1'),
            ArbitrageStrategy.THREE_WAY: Decimal('0.2'),
            ArbitrageStrategy.COMPLEX_MULTI: Decimal('0.5'),
            ArbitrageStrategy.CROSS_MARKET: Decimal('0.7'),
            ArbitrageStrategy.TEMPORAL: Decimal('0.9')
        }
        risk_score += strategy_risks.get(strategy, Decimal('0.5'))
        
        return risk_score.quantize(Decimal('0.01'))

    def _calculate_confidence_level(self, legs: List[MarketLeg], profit_margin: Decimal) -> Decimal:
        """Calculate confidence level for an opportunity."""
        if not legs:
            return Decimal('0')
        
        # Base confidence from profit margin
        base_confidence = min(profit_margin / Decimal('10'), Decimal('1'))  # Cap at 100%
        
        # Adjust for number of legs (more legs = lower confidence)
        leg_adjustment = Decimal('1') - (len(legs) - 2) * Decimal('0.1')
        leg_adjustment = max(leg_adjustment, Decimal('0.5'))  # Minimum 50%
        
        # Adjust for commission consistency
        if legs:
            commission_rates = [leg.commission_rate for leg in legs]
            commission_consistency = Decimal('1') - np.std([float(rate) for rate in commission_rates])
            commission_consistency = max(commission_consistency, Decimal('0.1'))
        else:
            commission_consistency = Decimal('0.5')
        
        confidence = base_confidence * leg_adjustment * commission_consistency
        return min(confidence, Decimal('1')).quantize(Decimal('0.01'))

    def _calculate_complexity_score(self, legs: List[MarketLeg], strategy: ArbitrageStrategy) -> Decimal:
        """Calculate complexity score for an opportunity."""
        complexity = Decimal('0')
        
        # Market type complexity
        market_complexities = [self.market_defaults.get(leg.market_type, {}).get('complexity_factor', Decimal('1.0'))
                             for leg in legs]
        avg_market_complexity = sum(market_complexities) / len(market_complexities)
        complexity += avg_market_complexity
        
        # Strategy complexity
        strategy_complexities = {
            ArbitrageStrategy.TWO_WAY: Decimal('1.0'),
            ArbitrageStrategy.THREE_WAY: Decimal('1.5'),
            ArbitrageStrategy.COMPLEX_MULTI: Decimal('2.0'),
            ArbitrageStrategy.CROSS_MARKET: Decimal('2.5'),
            ArbitrageStrategy.TEMPORAL: Decimal('3.0')
        }
        complexity += strategy_complexities.get(strategy, Decimal('2.0'))
        
        # Adjustment for leg count
        if len(legs) > 3:
            complexity += (len(legs) - 3) * Decimal('0.2')
        
        return complexity.quantize(Decimal('0.1'))

    def _calculate_market_efficiency(self, legs: List[MarketLeg]) -> Decimal:
        """Calculate market efficiency score."""
        if not legs:
            return Decimal('0')
        
        # Calculate implied probability variance
        implied_probs = [leg.implied_probability for leg in legs]
        prob_mean = sum(implied_probs) / len(implied_probs)
        prob_variance = sum((prob - prob_mean) ** 2 for prob in implied_probs) / len(implied_probs)
        prob_std = prob_variance.sqrt()
        
        # Efficiency is inverse of variance (higher variance = lower efficiency)
        efficiency = Decimal('1') / (Decimal('1') + prob_std)
        
        # Adjust for commission spread
        if legs:
            commission_rates = [leg.commission_rate for leg in legs]
            commission_spread = max(commission_rates) - min(commission_rates)
            commission_adjustment = Decimal('1') - commission_spread * Decimal('10')  # Penalize high spread
            efficiency *= max(commission_adjustment, Decimal('0.1'))
        
        return efficiency.quantize(Decimal('0.01'))

    def _calculate_optimal_profit(self, opportunity: ArbitrageOpportunity, stakes: Dict[str, Decimal]) -> Decimal:
        """Calculate optimal profit for given stakes."""
        if not stakes:
            return Decimal('0')
        
        # Calculate profit for each leg
        profits = []
        for leg in opportunity.legs:
            leg_key = f"leg_{opportunity.legs.index(leg)}_{leg.bookmaker}"
            if leg_key in stakes:
                stake = stakes[leg_key]
                profit = stake * (leg.odds - Decimal('1')) * (Decimal('1') - leg.commission_rate)
                profits.append(profit)
        
        # Return minimum profit (worst case)
        return min(profits) if profits else Decimal('0')

    def _calculate_risk_adjusted_return(self, opportunity: ArbitrageOpportunity, profit: Decimal, total_stake: Decimal) -> Decimal:
        """Calculate risk-adjusted return (Sharpe-like ratio)."""
        if total_stake <= 0:
            return Decimal('0')
        
        # Basic return
        basic_return = profit / total_stake
        
        # Adjust for risk
        risk_adjustment = Decimal('1') - (opportunity.risk_score / Decimal('10'))  # Normalize risk
        risk_adjustment = max(risk_adjustment, Decimal('0.1'))  # Minimum 10% of return
        
        return (basic_return * risk_adjustment).quantize(Decimal('0.0001'))

    def _calculate_kelly_percentage(self, opportunity: ArbitrageOpportunity, total_stake: Decimal, bankroll: Decimal) -> Decimal:
        """Calculate Kelly percentage used."""
        if bankroll <= 0:
            return Decimal('0')
        
        kelly_pct = (total_stake / bankroll) * Decimal('100')
        return kelly_pct.quantize(Decimal('0.01'))

    def _calculate_risk_concentration(self, opportunities: List[ArbitrageOpportunity]) -> float:
        """Calculate risk concentration (Herfindahl index)."""
        if not opportunities:
            return 0.0
        
        # Normalize risk scores
        risk_scores = [float(opp.risk_score) for opp in opportunities]
        total_risk = sum(risk_scores)
        
        if total_risk == 0:
            return 0.0
        
        # Calculate concentration
        weights = [risk / total_risk for risk in risk_scores]
        concentration = sum(weight ** 2 for weight in weights)
        
        return concentration

    def validate_arbitrage_calculation(self, opportunity: ArbitrageOpportunity) -> Dict[str, bool]:
        """
        Validate arbitrage calculations for mathematical consistency.
        
        Args:
            opportunity: ArbitrageOpportunity object to validate
            
        Returns:
            Dictionary of validation results
        """
        validation_results = {
            'odds_positive': all(leg.odds > 0 for leg in opportunity.legs),
            'probabilities_valid': all(
                0 < leg.implied_probability <= 2 for leg in opportunity.legs
            ),
            'total_probability_less_than_one': opportunity.total_implied_probability < Decimal('1'),
            'profit_margin_positive': opportunity.profit_margin > 0,
            'profit_margin_reasonable': opportunity.profit_margin < Decimal('50'),  # Reasonable upper bound
            'roi_positive': opportunity.roi_percentage > 0,
            'confidence_valid': Decimal('0') <= opportunity.confidence_level <= Decimal('1'),
            'risk_score_valid': opportunity.risk_score >= 0,
            'timestamp_valid': opportunity.detection_timestamp <= datetime.now(),
            'market_efficiency_valid': Decimal('0') <= opportunity.market_efficiency <= Decimal('1'),
            'complexity_reasonable': opportunity.complexity_score < Decimal('10')
        }
        
        return validation_results


def create_arbitrage_math_engine(risk_tolerance: Decimal = Decimal('0.1')) -> AdvancedArbitrageMath:
    """
    Factory function to create and configure an arbitrage math engine.
    
    Args:
        risk_tolerance: Risk tolerance for calculations (0.0 to 1.0)
        
    Returns:
        Configured AdvancedArbitrageMath instance
    """
    return AdvancedArbitrageMath(risk_tolerance=risk_tolerance)