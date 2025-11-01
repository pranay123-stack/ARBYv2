"""
Professional Position Sizing System

This module provides sophisticated position sizing algorithms with maximum position limits,
diversification requirements, correlation adjustment, and liquidity constraints for
optimal risk management in arbitrage betting.
"""

import math
from typing import List, Dict, Optional, Tuple, Union, NamedTuple
from decimal import Decimal, getcontext
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import warnings
import logging

# Configure decimal precision for financial calculations
getcontext().prec = 50


class SizingMethod(Enum):
    """Position sizing methods."""
    FIXED_AMOUNT = "fixed_amount"
    FIXED_PERCENTAGE = "fixed_percentage"
    KELLY_OPTIMAL = "kelly_optimal"
    FRACTIONAL_KELLY = "fractional_kelly"
    RISK_PARITY = "risk_parity"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    CORRELATION_ADJUSTED = "correlation_adjusted"
    LIQUIDITY_CONSTRAINED = "liquidity_constrained"
    DIVERSIFICATION_AWARE = "diversification_aware"


class RiskLevel(Enum):
    """Risk levels for position sizing."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


@dataclass
class PositionConfig:
    """Configuration for position sizing."""
    method: SizingMethod = SizingMethod.KELLY_OPTIMAL
    risk_level: RiskLevel = RiskLevel.MODERATE
    
    # Position limits
    max_position_size: Decimal = '0.1'  # 10% of bankroll
    min_position_size: Decimal = '0.001'  # 0.1% of bankroll
    max_total_exposure: Decimal = '0.8'  # 80% of bankroll
    max_positions_per_market: int = 5
    max_positions_total: int = 20
    
    # Risk parameters
    volatility_adjustment: bool = True
    correlation_threshold: Decimal = '0.7'
    diversification_ratio_min: Decimal = '0.3'
    
    # Liquidity constraints
    max_liquidity_utilization: Decimal = '0.1'  # 10% of market liquidity
    liquidity_buffer: Decimal = '0.05'  # 5% buffer for slippage
    
    # Advanced parameters
    kelly_fraction: Decimal = '0.25'
    confidence_adjustment: bool = True
    time_decay_factor: Decimal = '0.95'
    rebalancing_threshold: Decimal = '0.05'  # 5% change triggers rebalance
    correlation_adjustment: bool = True


@dataclass
class PositionSize:
    """Position size calculation results."""
    opportunity_id: str
    recommended_stake: Decimal
    max_stake: Decimal
    min_stake: Decimal
    risk_score: Decimal
    confidence_score: Decimal
    liquidity_requirement: Decimal
    expected_return: Decimal
    var_95: Decimal
    correlations: Dict[str, Decimal]
    sizing_method: SizingMethod
    reasoning: str
    warnings: List[str] = field(default_factory=list)


@dataclass
class PositionLimit:
    """Position size limits and constraints."""
    absolute_max: Decimal
    percentage_max: Decimal
    risk_budget_max: Decimal
    liquidity_max: Decimal
    correlation_limit: Decimal
    diversification_requirement: Decimal
    
    def check_limit(self, stake: Decimal, bankroll: Decimal) -> Tuple[bool, str]:
        """Check if stake is within limits."""
        percentage = stake / bankroll if bankroll > 0 else '0'
        
        if stake > self.absolute_max:
            return False, f"Stake {stake} exceeds absolute max {self.absolute_max}"
        
        if percentage > self.percentage_max:
            return False, f"Stake percentage {percentage:.1%} exceeds max {self.percentage_max:.1%}"
        
        return True, "Within limits"


@dataclass
class LiquidityConstraint:
    """Liquidity constraint information."""
    available_liquidity: Decimal
    required_liquidity: Decimal
    utilization_rate: Decimal
    slippage_estimate: Decimal
    market_impact: Decimal
    
    def is_satisfied(self, max_utilization: Decimal = '0.1') -> bool:
        """Check if liquidity constraint is satisfied."""
        return self.utilization_rate <= max_utilization
    
    def adjusted_stake(self, original_stake: Decimal) -> Decimal:
        """Calculate adjusted stake based on liquidity."""
        max_liquidity_stake = self.available_liquidity * ('1' - self.liquidity_buffer)
        return min(original_stake, max_liquidity_stake)


@dataclass
class DiversificationConstraint:
    """Diversification constraint information."""
    portfolio_weights: Dict[str, Decimal]
    correlation_matrix: np.ndarray
    diversification_ratio: Decimal
    concentration_risk: Decimal
    sector_exposure: Dict[str, Decimal]
    geographic_exposure: Dict[str, Decimal]
    
    def check_diversification(self, min_ratio: Decimal = '0.3') -> Tuple[bool, str]:
        """Check if diversification requirements are met."""
        if self.diversification_ratio < min_ratio:
            return False, f"Diversification ratio {self.diversification_ratio:.3f} below minimum {min_ratio:.3f}"
        
        return True, "Diversification requirements met"
    
    def max_position_weight(self, opportunity_id: str) -> Decimal:
        """Calculate maximum weight for an opportunity based on diversification."""
        if opportunity_id not in self.portfolio_weights:
            return '0.1'  # Default 10% max
        
        # Reduce maximum weight if portfolio is concentrated
        current_weight = self.portfolio_weights[opportunity_id]
        concentration_adjustment = '1' - (self.concentration_risk * '0.5')
        
        return current_weight * concentration_adjustment


@dataclass
class CorrelationAdjustment:
    """Correlation-based position adjustments."""
    correlation_matrix: np.ndarray
    opportunity_ids: List[str]
    correlation_adjustments: Dict[str, Decimal]
    diversification_penalty: Decimal
    
    def get_correlation_penalty(self, opportunity_id: str) -> Decimal:
        """Get correlation penalty for an opportunity."""
        return self.correlation_adjustments.get(opportunity_id, '0')
    
    def adjusted_position_size(self, base_size: Decimal, opportunity_id: str) -> Decimal:
        """Adjust position size based on correlation."""
        penalty = self.get_correlation_penalty(opportunity_id)
        return base_size * ('1' - penalty)


class PositionSizer:
    """
    Professional Position Sizer
    
    Provides sophisticated position sizing algorithms with support for:
    - Multiple sizing methodologies
    - Risk-based position limits
    - Liquidity constraints
    - Diversification requirements
    - Correlation adjustments
    - Real-time portfolio management
    """
    
    def __init__(self, config: PositionConfig = None):
        """Initialize position sizer with configuration."""
        self.config = config or PositionConfig()
        self.logger = self._setup_logger()
        self._position_history = []
        self._portfolio_state = {
            'positions': {},
            'total_exposure': '0',
            'diversification_ratio': '1',
            'correlation_matrix': None
        }
        
    def calculate_position_size(
        self,
        opportunity: Dict[str, Union[str, Decimal, Decimal, Decimal]],
        bankroll: Decimal,
        existing_positions: Dict[str, Decimal] = None,
        market_data: Dict[str, LiquidityConstraint] = None
    ) -> PositionSize:
        """
        Calculate optimal position size for a betting opportunity.
        
        Args:
            opportunity: Betting opportunity details
            bankroll: Current bankroll amount
            existing_positions: Current portfolio positions
            market_data: Market liquidity data
            
        Returns:
            PositionSize with calculation results
        """
        # Validate inputs
        self._validate_opportunity(opportunity, bankroll)
        
        existing_positions = existing_positions or {}
        market_data = market_data or {}
        
        # Extract opportunity data
        opp_id = opportunity['id']
        win_probability = str(opportunity['win_probability'])
        odds = str(opportunity['odds'])
        confidence = str(opportunity.get('confidence', '1'))
        
        # Calculate base position size based on method
        base_size = self._calculate_base_position_size(
            opportunity, bankroll, win_probability, odds, confidence
        )
        
        # Apply position limits
        limited_size = self._apply_position_limits(base_size, opportunity, bankroll)
        
        # Apply liquidity constraints
        if market_data and opp_id in market_data:
            liquidity_size = market_data[opp_id].adjusted_stake(limited_size)
        else:
            liquidity_size = limited_size
        
        # Apply diversification constraints
        diversified_size = self._apply_diversification_constraints(
            liquidity_size, opportunity, existing_positions, bankroll
        )
        
        # Apply correlation adjustments
        correlation_size = self._apply_correlation_adjustments(
            diversified_size, opportunity, existing_positions
        )
        
        # Apply risk adjustments
        risk_adjusted_size = self._apply_risk_adjustments(
            correlation_size, opportunity, bankroll
        )
        
        # Final size validation
        final_size = self._validate_final_size(risk_adjusted_size, bankroll)
        
        # Calculate metrics
        risk_score = self._calculate_risk_score(opportunity, final_size, bankroll)
        confidence_score = self._calculate_confidence_score(confidence, win_probability, odds)
        var_95 = self._calculate_var(opportunity, final_size, bankroll)
        
        # Generate reasoning
        reasoning = self._generate_position_reasoning(
            base_size, limited_size, diversified_size, correlation_size, final_size
        )
        
        # Check for warnings
        warnings = self._generate_position_warnings(
            final_size, bankroll, existing_positions, market_data, opp_id
        )
        
        result = PositionSize(
            opportunity_id=opp_id,
            recommended_stake=final_size,
            max_stake=limited_size,
            min_stake=self.config.min_position_size * bankroll,
            risk_score=risk_score,
            confidence_score=confidence_score,
            liquidity_requirement=final_size * ('1' + self.config.liquidity_buffer),
            expected_return=win_probability * (odds - '1') * final_size,
            var_95=var_95,
            correlations=self._get_correlations(opportunity, existing_positions),
            sizing_method=self.config.method,
            reasoning=reasoning,
            warnings=warnings
        )
        
        # Update portfolio state
        self._update_portfolio_state(opp_id, final_size, existing_positions)
        
        return result
    
    def calculate_portfolio_sizes(
        self,
        opportunities: List[Dict[str, Union[str, Decimal, Decimal, Decimal]]],
        bankroll: Decimal,
        existing_positions: Dict[str, Decimal] = None,
        market_data: Dict[str, LiquidityConstraint] = None
    ) -> Dict[str, PositionSize]:
        """
        Calculate position sizes for a portfolio of opportunities.
        
        Args:
            opportunities: List of betting opportunities
            bankroll: Current bankroll
            existing_positions: Current portfolio positions
            market_data: Market liquidity data
            
        Returns:
            Dictionary mapping opportunity IDs to PositionSize results
        """
        if not opportunities:
            raise ValueError("No opportunities provided for portfolio sizing")
        
        existing_positions = existing_positions or {}
        market_data = market_data or {}
        
        # Calculate initial position sizes
        position_sizes = {}
        
        for opportunity in opportunities:
            opp_id = opportunity['id']
            position_size = self.calculate_position_size(
                opportunity, bankroll, existing_positions, market_data
            )
            position_sizes[opp_id] = position_size
        
        # Apply portfolio-level constraints
        adjusted_sizes = self._apply_portfolio_constraints(
            position_sizes, bankroll, opportunities, existing_positions
        )
        
        # Ensure total exposure doesn't exceed limits
        total_exposure = sum(size.recommended_stake for size in adjusted_sizes.values())
        if total_exposure > bankroll * self.config.max_total_exposure:
            # Scale down proportionally
            scale_factor = (bankroll * self.config.max_total_exposure) / total_exposure
            
            for opp_id in adjusted_sizes:
                adjusted_sizes[opp_id].recommended_stake *= scale_factor
        
        # Update portfolio state
        self._update_portfolio_state_all(adjusted_sizes, existing_positions)
        
        return adjusted_sizes
    
    def rebalance_positions(
        self,
        current_positions: Dict[str, Decimal],
        target_positions: Dict[str, Decimal],
        bankroll: Decimal,
        rebalancing_threshold: Decimal = None
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Calculate rebalancing actions needed to reach target positions.
        
        Args:
            current_positions: Current position sizes
            target_positions: Target position sizes
            bankroll: Current bankroll
            rebalancing_threshold: Threshold for triggering rebalance
            
        Returns:
            Dictionary with rebalancing actions (buy/sell amounts)
        """
        if rebalancing_threshold is None:
            rebalancing_threshold = self.config.rebalancing_threshold
        
        rebalancing_actions = {}
        total_current = sum(current_positions.values())
        total_target = sum(target_positions.values())
        
        # Calculate deviations
        for opp_id in target_positions:
            current_size = current_positions.get(opp_id, '0')
            target_size = target_positions[opp_id]
            
            deviation = abs(target_size - current_size) / bankroll
            
            if deviation > rebalancing_threshold:
                action = 'buy' if target_size > current_size else 'sell'
                amount = abs(target_size - current_size)
                
                rebalancing_actions[opp_id] = {
                    'action': action,
                    'amount': amount,
                    'deviation': deviation,
                    'current_size': current_size,
                    'target_size': target_size
                }
        
        # Calculate rebalancing costs
        total_rebalancing_cost = self._calculate_rebalancing_costs(rebalancing_actions, bankroll)
        
        return {
            'actions': rebalancing_actions,
            'total_rebalancing_cost': total_rebalancing_cost,
            'positions_to_rebalance': len(rebalancing_actions),
            'rebalancing_threshold': rebalancing_threshold
        }
    
    def assess_portfolio_risk(
        self,
        positions: Dict[str, Decimal],
        opportunities: List[Dict[str, Union[str, Decimal, Decimal, Decimal]]]
    ) -> Dict[str, Decimal]:
        """
        Assess overall portfolio risk metrics.
        
        Args:
            positions: Current portfolio positions
            opportunities: Opportunity details
            
        Returns:
            Dictionary with portfolio risk metrics
        """
        total_exposure = sum(positions.values())
        bankroll = total_exposure / '0.5'  # Estimate bankroll from exposure
        
        if len(positions) == 0:
            return {
                'total_exposure': '0',
                'concentration_risk': '0',
                'diversification_ratio': '1',
                'portfolio_var_95': '0',
                'correlation_risk': '0',
                'liquidity_risk': '0'
            }
        
        # Calculate weights
        weights = {
            opp_id: stake / total_exposure
            for opp_id, stake in positions.items()
        }
        
        # Concentration risk (Herfindahl index)
        concentration_risk = sum(weight ** 2 for weight in weights.values())
        diversification_ratio = '1' - concentration_risk
        
        # Portfolio variance
        portfolio_variance = '0'
        for opp_id, weight in weights.items():
            # Find opportunity data
            opp_data = next((opp for opp in opportunities if opp['id'] == opp_id), None)
            if opp_data:
                prob = str(opp_data['win_probability'])
                odds = str(opp_data['odds'])
                variance = prob * (odds - 1) ** 2 + (1 - prob)
                portfolio_variance += (weight ** 2) * variance
        
        # Value at Risk (95%)
        portfolio_var_95 = str(1.65 * math.sqrt(float(portfolio_variance))) * total_exposure
        
        # Correlation risk (simplified)
        correlation_risk = self._calculate_correlation_risk(weights, opportunities)
        
        # Liquidity risk
        liquidity_risk = self._calculate_liquidity_risk(positions, opportunities)
        
        return {
            'total_exposure': total_exposure,
            'concentration_risk': concentration_risk,
            'diversification_ratio': diversification_ratio,
            'portfolio_var_95': portfolio_var_95,
            'correlation_risk': correlation_risk,
            'liquidity_risk': liquidity_risk,
            'num_positions': str(len(positions)),
            'largest_position': max(weights.values()) if weights else '0'
        }
    
    def get_position_limits(
        self,
        opportunity: Dict[str, Union[str, Decimal, Decimal, Decimal]],
        bankroll: Decimal,
        existing_positions: Dict[str, Decimal] = None
    ) -> PositionLimit:
        """
        Calculate position limits for an opportunity.
        
        Args:
            opportunity: Betting opportunity
            bankroll: Current bankroll
            existing_positions: Current positions
            
        Returns:
            PositionLimit with calculated limits
        """
        existing_positions = existing_positions or {}
        
        # Basic limits
        absolute_max = bankroll * self.config.max_position_size
        percentage_max = self.config.max_position_size
        
        # Risk budget calculation
        total_exposure = sum(existing_positions.values())
        available_risk_budget = (bankroll * self.config.max_total_exposure) - total_exposure
        risk_budget_max = available_risk_budget
        
        # Liquidity limit (placeholder - would integrate with market data)
        liquidity_max = absolute_max * '0.8'  # 80% of absolute max due to liquidity
        
        # Correlation limit
        correlation_limit = self._calculate_correlation_limit(opportunity, existing_positions)
        
        # Diversification requirement
        current_positions_count = len(existing_positions)
        if current_positions_count >= self.config.max_positions_total:
            diversification_requirement = '0'  # No new positions allowed
        else:
            diversification_requirement = '1' / (current_positions_count + 1)
        
        return PositionLimit(
            absolute_max=absolute_max,
            percentage_max=percentage_max,
            risk_budget_max=risk_budget_max,
            liquidity_max=liquidity_max,
            correlation_limit=correlation_limit,
            diversification_requirement=diversification_requirement
        )
    
    # Private helper methods
    
    def _setup_logger(self):
        """Setup logging for the position sizer."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        return logger
    
    def _validate_opportunity(self, opportunity: Dict, bankroll: Decimal):
        """Validate opportunity data."""
        required_keys = ['id', 'win_probability', 'odds']
        if not all(key in opportunity for key in required_keys):
            raise ValueError("Opportunity must have id, win_probability, and odds")
        
        if bankroll <= 0:
            raise ValueError("Bankroll must be positive")
        
        prob = str(opportunity['win_probability'])
        odds = str(opportunity['odds'])
        
        if not ('0' <= prob <= '1'):
            raise ValueError("Win probability must be between 0 and 1")
        
        if odds <= '1':
            raise ValueError("Odds must be greater than 1")
    
    def _calculate_base_position_size(
        self,
        opportunity: Dict,
        bankroll: Decimal,
        win_probability: Decimal,
        odds: Decimal,
        confidence: Decimal
    ) -> Decimal:
        """Calculate base position size using the configured method."""
        if self.config.method == SizingMethod.FIXED_AMOUNT:
            return self.config.min_position_size * bankroll
        
        elif self.config.method == SizingMethod.FIXED_PERCENTAGE:
            return bankroll * self.config.max_position_size * confidence
        
        elif self.config.method == SizingMethod.KELLY_OPTIMAL:
            return self._calculate_kelly_size(win_probability, odds, bankroll)
        
        elif self.config.method == SizingMethod.FRACTIONAL_KELLY:
            return self._calculate_kelly_size(win_probability, odds, bankroll) * self.config.kelly_fraction
        
        elif self.config.method == SizingMethod.RISK_PARITY:
            return self._calculate_risk_parity_size(opportunity, bankroll)
        
        elif self.config.method == SizingMethod.VOLATILITY_ADJUSTED:
            return self._calculate_volatility_adjusted_size(opportunity, bankroll)
        
        elif self.config.method == SizingMethod.CORRELATION_ADJUSTED:
            return self._calculate_correlation_adjusted_size(opportunity, bankroll)
        
        elif self.config.method == SizingMethod.LIQUIDITY_CONSTRAINED:
            return self._calculate_liquidity_constrained_size(opportunity, bankroll)
        
        elif self.config.method == SizingMethod.DIVERSIFICATION_AWARE:
            return self._calculate_diversification_aware_size(opportunity, bankroll)
        
        else:
            # Default to conservative size
            return bankroll * self.config.max_position_size * '0.5'
    
    def _calculate_kelly_size(
        self,
        win_probability: Decimal,
        odds: Decimal,
        bankroll: Decimal
    ) -> Decimal:
        """Calculate Kelly optimal position size."""
        b = odds - '1'
        p = win_probability
        q = '1' - p
        
        if b <= 0:
            return '0'
        
        kelly_fraction = (b * p - q) / b
        kelly_fraction = max(kelly_fraction, '0')
        kelly_fraction = min(kelly_fraction, self.config.max_position_size)
        
        return bankroll * kelly_fraction
    
    def _calculate_risk_parity_size(
        self,
        opportunity: Dict,
        bankroll: Decimal
    ) -> Decimal:
        """Calculate risk parity position size."""
        # Simplified risk parity - equal risk contribution
        prob = str(opportunity['win_probability'])
        odds = str(opportunity['odds'])
        
        # Calculate risk (standard deviation)
        variance = prob * (odds - 1) ** 2 + (1 - prob)
        risk = math.sqrt(float(variance))
        
        # Inverse relationship: higher risk = smaller position
        base_size = bankroll * self.config.max_position_size
        risk_adjusted_size = base_size / str(max(risk, 0.1))
        
        return min(risk_adjusted_size, bankroll * self.config.max_position_size)
    
    def _calculate_volatility_adjusted_size(
        self,
        opportunity: Dict,
        bankroll: Decimal
    ) -> Decimal:
        """Calculate volatility-adjusted position size."""
        prob = str(opportunity['win_probability'])
        odds = str(opportunity['odds'])
        
        # Calculate implied volatility from odds
        variance = prob * (odds - 1) ** 2 + (1 - prob)
        volatility = math.sqrt(float(variance))
        
        # Adjust size based on volatility
        base_size = bankroll * self.config.max_position_size
        vol_adjustment = '1' / ('1' + volatility)
        
        return base_size * vol_adjustment
    
    def _calculate_correlation_adjusted_size(
        self,
        opportunity: Dict,
        bankroll: Decimal
    ) -> Decimal:
        """Calculate correlation-adjusted position size."""
        base_size = bankroll * self.config.max_position_size
        
        # Check correlation with existing positions
        correlation_penalty = self._calculate_correlation_penalty(opportunity)
        
        return base_size * ('1' - correlation_penalty)
    
    def _calculate_liquidity_constrained_size(
        self,
        opportunity: Dict,
        bankroll: Decimal
    ) -> Decimal:
        """Calculate liquidity-constrained position size."""
        base_size = bankroll * self.config.max_position_size
        
        # Get market liquidity (would integrate with real data)
        market_liquidity = opportunity.get('market_liquidity', bankroll * '10')
        
        # Limit to percentage of market liquidity
        liquidity_limit = market_liquidity * self.config.max_liquidity_utilization
        
        return min(base_size, liquidity_limit)
    
    def _calculate_diversification_aware_size(
        self,
        opportunity: Dict,
        bankroll: Decimal
    ) -> Decimal:
        """Calculate diversification-aware position size."""
        base_size = bankroll * self.config.max_position_size
        
        # Check if adding this position would hurt diversification
        current_positions = self._portfolio_state['positions']
        
        if len(current_positions) >= self.config.max_positions_total:
            return '0'  # No room for more positions
        
        # Reduce size if we're approaching position limits
        position_utilization = len(current_positions) / self.config.max_positions_total
        diversification_adjustment = '1' - position_utilization * '0.5'
        
        return base_size * diversification_adjustment
    
    def _apply_position_limits(
        self,
        base_size: Decimal,
        opportunity: Dict,
        bankroll: Decimal
    ) -> Decimal:
        """Apply position size limits."""
        # Maximum absolute size
        max_size = bankroll * self.config.max_position_size
        
        # Minimum size
        min_size = bankroll * self.config.min_position_size
        
        # Apply limits
        limited_size = max(min_size, min(base_size, max_size))
        
        return limited_size
    
    def _apply_diversification_constraints(
        self,
        base_size: Decimal,
        opportunity: Dict,
        existing_positions: Dict[str, Decimal],
        bankroll: Decimal
    ) -> Decimal:
        """Apply diversification constraints."""
        # Check total number of positions
        total_positions = len(existing_positions)
        if total_positions >= self.config.max_positions_total:
            return '0'
        
        # Check positions per market (simplified)
        market_key = opportunity.get('market', 'general')
        positions_in_market = sum(1 for pos in existing_positions.keys() 
                                if existing_positions.get(pos, '').startswith(market_key))
        
        if positions_in_market >= self.config.max_positions_per_market:
            return base_size * '0.5'  # Reduce size for market concentration
        
        # Diversification ratio consideration
        total_exposure = sum(existing_positions.values()) + base_size
        concentration_risk = self._calculate_concentration_risk(existing_positions, base_size)
        
        if concentration_risk > ('1' - self.config.diversification_ratio_min):
            return base_size * '0.7'  # Reduce for concentration
        
        return base_size
    
    def _apply_correlation_adjustments(
        self,
        base_size: Decimal,
        opportunity: Dict,
        existing_positions: Dict[str, Decimal]
    ) -> Decimal:
        """Apply correlation-based adjustments."""
        correlation_penalty = self._calculate_correlation_penalty(opportunity)
        adjustment_factor = '1' - correlation_penalty
        
        return base_size * adjustment_factor
    
    def _apply_risk_adjustments(
        self,
        base_size: Decimal,
        opportunity: Dict,
        bankroll: Decimal
    ) -> Decimal:
        """Apply additional risk adjustments."""
        # Risk level adjustments
        risk_multipliers = {
            RiskLevel.CONSERVATIVE: '0.5',
            RiskLevel.MODERATE: '0.75',
            RiskLevel.AGGRESSIVE: '1.0',
            RiskLevel.VERY_AGGRESSIVE: '1.25'
        }
        
        risk_multiplier = risk_multipliers.get(self.config.risk_level, '0.75')
        
        # Confidence adjustment
        confidence = str(opportunity.get('confidence', '1'))
        if self.config.confidence_adjustment:
            confidence_factor = confidence
        else:
            confidence_factor = '1'
        
        return base_size * risk_multiplier * confidence_factor
    
    def _validate_final_size(self, size: Decimal, bankroll: Decimal) -> Decimal:
        """Validate and adjust final position size."""
        if size <= 0:
            return '0'
        
        # Ensure size is reasonable relative to bankroll
        percentage = size / bankroll
        if percentage > self.config.max_position_size:
            return bankroll * self.config.max_position_size
        
        if percentage < self.config.min_position_size:
            return bankroll * self.config.min_position_size
        
        return size
    
    def _calculate_risk_score(
        self,
        opportunity: Dict,
        stake: Decimal,
        bankroll: Decimal
    ) -> Decimal:
        """Calculate risk score for the position."""
        prob = str(opportunity['win_probability'])
        odds = str(opportunity['odds'])
        
        # Basic risk components
        loss_probability = '1' - prob
        position_percentage = stake / bankroll
        
        # Value at Risk estimate
        var_estimate = stake * loss_probability
        
        # Combine risk factors
        risk_score = (loss_probability * '0.4' + 
                     position_percentage * '0.4' + 
                     var_estimate / bankroll * '0.2')
        
        return min(risk_score, '1')
    
    def _calculate_confidence_score(
        self,
        confidence: Decimal,
        win_probability: Decimal,
        odds: Decimal
    ) -> Decimal:
        """Calculate confidence score for the position."""
        # Adjust confidence based on probability and odds
        implied_probability = '1' / odds
        
        # Higher confidence if our probability differs from implied
        probability_adjustment = abs(win_probability - implied_probability)
        
        # Final confidence score
        confidence_score = confidence * ('1' + probability_adjustment)
        
        return min(confidence_score, '2')  # Cap at 2x
    
    def _calculate_var(
        self,
        opportunity: Dict,
        stake: Decimal,
        bankroll: Decimal
    ) -> Decimal:
        """Calculate 95% Value at Risk."""
        prob = str(opportunity['win_probability'])
        loss_probability = '1' - prob
        
        # Simplified VaR calculation
        var_95 = stake * loss_probability * '1.65'
        
        return var_95
    
    def _get_correlations(
        self,
        opportunity: Dict,
        existing_positions: Dict[str, Decimal]
    ) -> Dict[str, Decimal]:
        """Get correlations with existing positions (placeholder)."""
        # In practice, this would calculate actual correlations
        # For now, return empty dict
        return {}
    
    def _generate_position_reasoning(
        self,
        base_size: Decimal,
        limited_size: Decimal,
        diversified_size: Decimal,
        correlation_size: Decimal,
        final_size: Decimal
    ) -> str:
        """Generate human-readable reasoning for position size."""
        reasoning_parts = []
        
        # Base calculation
        if base_size != final_size:
            reasoning_parts.append(f"Base size: {base_size:.4f}")
        
        # Size adjustments
        adjustments = []
        if limited_size != base_size:
            adjustments.append("position limits")
        if diversified_size != limited_size:
            adjustments.append("diversification")
        if correlation_size != diversified_size:
            adjustments.append("correlation")
        
        if adjustments:
            reasoning_parts.append(f"Adjusted for: {', '.join(adjustments)}")
        
        reasoning_parts.append(f"Final size: {final_size:.4f}")
        
        return "; ".join(reasoning_parts)
    
    def _generate_position_warnings(
        self,
        stake: Decimal,
        bankroll: Decimal,
        existing_positions: Dict[str, Decimal],
        market_data: Dict[str, LiquidityConstraint],
        opp_id: str
    ) -> List[str]:
        """Generate warnings for the position."""
        warnings = []
        
        # High position size warning
        position_percentage = stake / bankroll
        if position_percentage > self.config.max_position_size * '0.8':
            warnings.append("Large position size relative to bankroll")
        
        # Total exposure warning
        total_exposure = sum(existing_positions.values()) + stake
        if total_exposure > bankroll * self.config.max_total_exposure * '0.9':
            warnings.append("High total portfolio exposure")
        
        # Liquidity warnings
        if opp_id in market_data and not market_data[opp_id].is_satisfied():
            warnings.append("Insufficient market liquidity")
        
        # Concentration warnings
        if len(existing_positions) >= self.config.max_positions_total * '0.8':
            warnings.append("Approaching maximum positions limit")
        
        return warnings
    
    def _apply_portfolio_constraints(
        self,
        position_sizes: Dict[str, PositionSize],
        bankroll: Decimal,
        opportunities: List[Dict],
        existing_positions: Dict[str, Decimal]
    ) -> Dict[str, PositionSize]:
        """Apply portfolio-level constraints to all positions."""
        # Check total exposure
        total_exposure = sum(size.recommended_stake for size in position_sizes.values())
        
        if total_exposure > bankroll * self.config.max_total_exposure:
            # Scale down proportionally
            scale_factor = (bankroll * self.config.max_total_exposure) / total_exposure
            
            for opp_id in position_sizes:
                position_sizes[opp_id].recommended_stake *= scale_factor
        
        return position_sizes
    
    def _update_portfolio_state(
        self,
        opp_id: str,
        new_size: Decimal,
        existing_positions: Dict[str, Decimal]
    ):
        """Update internal portfolio state."""
        self._portfolio_state['positions'][opp_id] = new_size
        self._portfolio_state['total_exposure'] = sum(self._portfolio_state['positions'].values())
        
        # Update diversification ratio
        if self._portfolio_state['total_exposure'] > 0:
            weights = {
                pos_id: size / self._portfolio_state['total_exposure']
                for pos_id, size in self._portfolio_state['positions'].items()
            }
            concentration = sum(weight ** 2 for weight in weights.values())
            self._portfolio_state['diversification_ratio'] = '1' - concentration
    
    def _update_portfolio_state_all(
        self,
        position_sizes: Dict[str, PositionSize],
        existing_positions: Dict[str, Decimal]
    ):
        """Update portfolio state with all position sizes."""
        self._portfolio_state['positions'] = {
            opp_id: size.recommended_stake
            for opp_id, size in position_sizes.items()
        }
        self._portfolio_state['total_exposure'] = sum(
            size.recommended_stake for size in position_sizes.values()
        )
    
    def _calculate_rebalancing_costs(
        self,
        rebalancing_actions: Dict[str, Dict],
        bankroll: Decimal
    ) -> Decimal:
        """Calculate total rebalancing costs."""
        total_rebalancing_amount = sum(
            action['amount'] for action in rebalancing_actions.values()
        )
        
        # Transaction costs plus rebalancing costs
        transaction_cost = total_rebalancing_amount * self.config.transaction_cost_rate
        rebalancing_cost = total_rebalancing_amount * '0.001'  # 0.1% rebalancing cost
        
        return transaction_cost + rebalancing_cost
    
    def _calculate_correlation_penalty(self, opportunity: Dict) -> Decimal:
        """Calculate correlation penalty for an opportunity."""
        # Placeholder - would calculate actual correlation with existing positions
        # For now, return small penalty based on opportunity characteristics
        
        # Higher penalty for similar markets/sports
        market = opportunity.get('market', '')
        sport = opportunity.get('sport', '')
        
        penalty = '0'
        if len(market) > 0:
            penalty += '0.1'
        if len(sport) > 0:
            penalty += '0.05'
        
        return min(penalty, '0.3')  # Cap at 30%
    
    def _calculate_concentration_risk(
        self,
        existing_positions: Dict[str, Decimal],
        new_position: Decimal
    ) -> Decimal:
        """Calculate portfolio concentration risk after adding new position."""
        total_existing = sum(existing_positions.values())
        new_total = total_existing + new_position
        
        if new_total <= 0:
            return '0'
        
        # Calculate Herfindahl-Hirschman Index
        weights = [pos / new_total for pos in existing_positions.values()]
        weights.append(new_position / new_total)
        
        hhi = sum(w ** 2 for w in weights)
        return str(hhi)
    
    def _calculate_correlation_risk(
        self,
        weights: Dict[str, Decimal],
        opportunities: List[Dict]
    ) -> Decimal:
        """Calculate correlation risk for the portfolio."""
        # Simplified correlation risk calculation
        # In practice, would use actual correlation matrix
        
        num_positions = len(weights)
        if num_positions <= 1:
            return '0'
        
        # Estimate correlation risk based on position count and weights
        concentration = max(weights.values()) if weights else '0'
        
        # Higher correlation risk if portfolio is concentrated
        correlation_risk = concentration * '0.5'
        
        return min(correlation_risk, '0.5')  # Cap at 50%
    
    def _calculate_liquidity_risk(
        self,
        positions: Dict[str, Decimal],
        opportunities: List[Dict]
    ) -> Decimal:
        """Calculate liquidity risk for the portfolio."""
        # Placeholder - would integrate with real market liquidity data
        
        total_exposure = sum(positions.values())
        if total_exposure <= 0:
            return '0'
        
        # Estimate liquidity risk based on position sizes
        # Larger positions relative to bankroll = higher liquidity risk
        
        avg_position = total_exposure / len(positions)
        liquidity_risk = avg_position / total_exposure  # Normalized
        
        return min(liquidity_risk, '0.3')  # Cap at 30%
    
    def _calculate_correlation_limit(
        self,
        opportunity: Dict,
        existing_positions: Dict[str, Decimal]
    ) -> Decimal:
        """Calculate correlation-based position limit."""
        correlation_penalty = self._calculate_correlation_penalty(opportunity)
        correlation_limit = self.config.max_position_size * ('1' - correlation_penalty)
        
        return correlation_limit
    
    def get_portfolio_state(self) -> Dict:
        """Get current portfolio state."""
        return self._portfolio_state.copy()
    
    def reset_portfolio_state(self):
        """Reset portfolio state."""
        self._portfolio_state = {
            'positions': {},
            'total_exposure': '0',
            'diversification_ratio': '1',
            'correlation_matrix': None
        }