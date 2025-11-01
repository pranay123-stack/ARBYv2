"""
Advanced Kelly Criterion Implementation

This module provides sophisticated Kelly criterion calculations including fractional Kelly,
dynamic adjustment, portfolio-based optimization, and multi-outcome scenarios.
"""

import math
from typing import List, Dict, Optional, Tuple, Union, Callable, NamedTuple
from decimal import Decimal, getcontext
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from scipy import stats
import logging
import warnings

# Configure decimal precision for financial calculations
getcontext().prec = 50


class KellyMode(Enum):
    """Kelly calculation modes."""
    CLASSIC = "classic"
    FRACTIONAL = "fractional" 
    MULTI_OUTCOME = "multi_outcome"
    DYNAMIC = "dynamic"
    PORTFOLIO = "portfolio"


class AdjustmentType(Enum):
    """Types of Kelly adjustments."""
    VOLATILITY = "volatility"
    CONVEXITY = "convexity"
    CORRELATION = "correlation"
    DRAWDOWN = "drawdown"
    TIME_DECAY = "time_decay"


@dataclass
class KellyConfig:
    """Configuration for Kelly calculations."""
    mode: KellyMode = KellyMode.CLASSIC
    fractional_factor: Decimal = '0.25'  # Fractional Kelly multiplier
    max_kelly_fraction: Decimal = '0.5'  # Maximum Kelly fraction to use
    min_kelly_fraction: Decimal = '0.01'  # Minimum Kelly fraction
    volatility_adjustment: bool = True
    drawdown_threshold: Decimal = '0.2'  # 20% drawdown threshold
    confidence_level: Decimal = '0.95'  # Confidence level for adjustments
    rebalancing_frequency: int = 10  # Rebalance every N trades
    correlation_threshold: Decimal = '0.7'  # Correlation threshold for portfolio
    transaction_cost_rate: Decimal = '0.005'  # 0.5% transaction costs
    slippage_rate: Decimal = '0.002'  # 0.2% slippage


@dataclass
class KellyFraction:
    """Kelly fraction calculation results."""
    optimal_fraction: Decimal
    expected_growth_rate: Decimal
    variance: Decimal
    utility_score: Decimal
    risk_adjusted_fraction: Optional[Decimal] = None
    fractional_adjustment: Optional[Decimal] = None
    volatility_adjustment: Optional[Decimal] = None
    confidence_interval: Optional[Tuple[Decimal, Decimal]] = None


@dataclass 
class MultiOutcomeKellyResult:
    """Results from multi-outcome Kelly calculations."""
    outcome_fractions: Dict[str, Decimal]
    total_fraction: Decimal
    expected_return: Decimal
    portfolio_variance: Decimal
    correlations: Dict[Tuple[str, str], Decimal]
    diversification_ratio: Decimal
    optimal_weight: Decimal


@dataclass
class DynamicKellyResult:
    """Results from dynamic Kelly calculations."""
    current_fraction: Decimal
    adjusted_fraction: Decimal
    adjustment_reason: str
    market_conditions: Dict[str, Decimal]
    performance_metrics: Dict[str, Decimal]
    next_rebalance_date: datetime


@dataclass
class PortfolioKellyResult:
    """Results from portfolio Kelly calculations."""
    portfolio_weights: Dict[str, Decimal]
    total_kelly_fraction: Decimal
    expected_portfolio_return: Decimal
    portfolio_volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    var_95: Decimal
    constraint_satisfaction: bool


class KellyCalculator:
    """
    Advanced Kelly Criterion Calculator
    
    Provides sophisticated Kelly criterion calculations with support for:
    - Fractional Kelly strategies
    - Multi-outcome scenarios
    - Dynamic adjustment based on market conditions
    - Portfolio optimization
    - Risk-adjusted calculations
    """
    
    def __init__(self, config: KellyConfig = None):
        """Initialize Kelly calculator with configuration."""
        self.config = config or KellyConfig()
        self.logger = logging.getLogger(__name__)
        self._calculation_history = []
        self._performance_cache = {}
        
    def calculate_classic_kelly(
        self,
        win_probability: Decimal,
        odds: Decimal,
        bankroll: Decimal,
        transaction_costs: Decimal = None
    ) -> KellyFraction:
        """
        Calculate classic Kelly fraction.
        
        Args:
            win_probability: Probability of winning (0-1)
            odds: Decimal odds offered
            bankroll: Current bankroll amount
            transaction_costs: Transaction costs as fraction of stake
            
        Returns:
            KellyFraction with calculation results
            
        Raises:
            ValueError: If inputs are invalid
        """
        # Input validation
        if not self._validate_kelly_inputs(win_probability, odds, bankroll):
            raise ValueError("Invalid Kelly calculation inputs")
            
        # Calculate Kelly fraction using classic formula: f = (bp - q) / b
        # where b = odds - 1, p = win_probability, q = 1 - p
        b = odds - '1'
        p = win_probability
        q = '1' - p
        
        if b <= 0:
            self.logger.warning("Non-positive odds detected, returning zero fraction")
            return KellyFraction(
                optimal_fraction='0',
                expected_growth_rate='0',
                variance='0',
                utility_score='0'
            )
        
        kelly_fraction = (b * p - q) / b
        
        # Ensure fraction is positive and within bounds
        kelly_fraction = max(kelly_fraction, '0')
        kelly_fraction = min(kelly_fraction, self.config.max_kelly_fraction)
        
        # Calculate expected growth rate
        if transaction_costs is None:
            transaction_costs = self.config.transaction_cost_rate
            
        net_odds = odds * ('1' - transaction_costs - self.config.slippage_rate)
        expected_growth = p * float(math.log(float('1' + kelly_fraction * (net_odds - '1')))) + \
                         q * float(math.log(float('1' - kelly_fraction)))
        
        # Calculate variance
        variance = kelly_fraction ** 2 * (p * (net_odds - '1') ** 2 + q * ('1') ** 2)
        
        # Calculate utility score (risk-adjusted return)
        utility_score = expected_growth / math.sqrt(variance + '1e-10')
        
        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(
            kelly_fraction, variance, self.config.confidence_level
        )
        
        result = KellyFraction(
            optimal_fraction=kelly_fraction,
            expected_growth_rate=str(expected_growth),
            variance=variance,
            utility_score=str(utility_score),
            confidence_interval=confidence_interval
        )
        
        self._calculation_history.append({
            'timestamp': datetime.now(),
            'type': 'classic_kelly',
            'result': result
        })
        
        return result
    
    def calculate_fractional_kelly(
        self,
        win_probability: Decimal,
        odds: Decimal,
        bankroll: Decimal,
        fraction: Decimal = None
    ) -> KellyFraction:
        """
        Calculate fractional Kelly fraction.
        
        Args:
            win_probability: Probability of winning
            odds: Decimal odds
            bankroll: Bankroll amount
            fraction: Fractional multiplier (e.g., 0.25 for quarter Kelly)
            
        Returns:
            KellyFraction with fractional Kelly results
        """
        if fraction is None:
            fraction = self.config.fractional_factor
            
        # Calculate classic Kelly first
        classic_result = self.calculate_classic_kelly(win_probability, odds, bankroll)
        
        # Apply fractional adjustment
        fractional_fraction = classic_result.optimal_fraction * fraction
        
        # Recalculate metrics for fractional Kelly
        b = odds - '1'
        p = win_probability
        q = '1' - p
        
        net_odds = odds * ('1' - self.config.transaction_cost_rate - self.config.slippage_rate)
        expected_growth = p * float(math.log(float('1' + fractional_fraction * (net_odds - '1')))) + \
                         q * float(math.log(float('1' - fractional_fraction)))
        
        variance = fractional_fraction ** 2 * (p * (net_odds - '1') ** 2 + q * ('1') ** 2)
        
        return KellyFraction(
            optimal_fraction=fractional_fraction,
            expected_growth_rate=str(expected_growth),
            variance=variance,
            utility_score=str(expected_growth / math.sqrt(variance + Decimal('1e-10'))),
            fractional_adjustment=fraction,
            confidence_interval=classic_result.confidence_interval
        )
    
    def calculate_multi_outcome_kelly(
        self,
        outcomes: Dict[str, Tuple[Decimal, Decimal]],
        bankroll: Decimal
    ) -> MultiOutcomeKellyResult:
        """
        Calculate Kelly fraction for multi-outcome scenarios.
        
        Args:
            outcomes: Dict mapping outcome names to (probability, odds) tuples
            bankroll: Bankroll amount
            
        Returns:
            MultiOutcomeKellyResult with portfolio calculations
        """
        # Validate probabilities sum to 1
        total_prob = sum(prob for prob, _ in outcomes.values())
        if abs(total_prob - '1') > '1e-6':
            raise ValueError(f"Probabilities must sum to 1.0, got {total_prob}")
        
        outcome_fractions = {}
        total_fraction = '0'
        
        # Calculate individual Kelly fractions
        for outcome, (prob, odds) in outcomes.items():
            kelly_result = self.calculate_classic_kelly(prob, odds, bankroll)
            outcome_fractions[outcome] = kelly_result.optimal_fraction
            total_fraction += kelly_result.optimal_fraction
        
        # Calculate portfolio variance (simplified - assumes independent outcomes)
        portfolio_variance = sum(fraction ** 2 for fraction in outcome_fractions.values())
        
        # Calculate expected return
        expected_return = sum(
            prob * odds * fraction 
            for (outcome, (prob, odds)), fraction in zip(outcomes.items(), outcome_fractions.values())
        )
        
        # For simplicity, assume zero correlation (could be enhanced with actual correlation data)
        correlations = {}
        for i, outcome1 in enumerate(outcomes.keys()):
            for j, outcome2 in enumerate(outcomes.keys()):
                if i < j:
                    correlations[(outcome1, outcome2)] = '0'
        
        # Calculate diversification ratio
        if len(outcomes) > 1 and total_fraction > 0:
            individual_variance = sum(
                self.calculate_classic_kelly(prob, odds, bankroll).variance
                for prob, odds in outcomes.values()
            )
            diversification_ratio = math.sqrt(individual_variance / (portfolio_variance + '1e-10'))
        else:
            diversification_ratio = '1'
        
        # Optimal weight for multi-outcome betting
        optimal_weight = min(total_fraction, '1')
        
        return MultiOutcomeKellyResult(
            outcome_fractions=outcome_fractions,
            total_fraction=optimal_weight,
            expected_return=expected_return,
            portfolio_variance=portfolio_variance,
            correlations=correlations,
            diversification_ratio=str(diversification_ratio),
            optimal_weight=optimal_weight
        )
    
    def calculate_dynamic_kelly(
        self,
        win_probability: Decimal,
        odds: Decimal,
        bankroll: Decimal,
        market_conditions: Dict[str, Decimal],
        recent_performance: List[Decimal]
    ) -> DynamicKellyResult:
        """
        Calculate Kelly fraction with dynamic adjustments.
        
        Args:
            win_probability: Current win probability
            odds: Current odds
            bankroll: Current bankroll
            market_conditions: Market condition indicators
            recent_performance: Recent performance metrics
            
        Returns:
            DynamicKellyResult with adjusted calculations
        """
        # Calculate base Kelly
        base_result = self.calculate_classic_kelly(win_probability, odds, bankroll)
        
        adjusted_fraction = base_result.optimal_fraction
        adjustment_reasons = []
        
        # Volatility adjustment
        if self.config.volatility_adjustment and market_conditions.get('volatility', 0) > 0:
            vol_adjustment = self._calculate_volatility_adjustment(market_conditions['volatility'])
            adjusted_fraction *= vol_adjustment
            adjustment_reasons.append(f"volatility_{vol_adjustment:.3f}")
        
        # Drawdown protection
        if recent_performance:
            drawdown = self._calculate_current_drawdown(recent_performance)
            if drawdown > self.config.drawdown_threshold:
                dd_adjustment = self._calculate_drawdown_adjustment(drawdown)
                adjusted_fraction *= dd_adjustment
                adjustment_reasons.append(f"drawdown_{dd_adjustment:.3f}")
        
        # Market condition adjustments
        market_adjustments = self._apply_market_adjustments(market_conditions)
        for factor, adjustment in market_adjustments.items():
            adjusted_fraction *= adjustment
            adjustment_reasons.append(f"{factor}_{adjustment:.3f}")
        
        # Ensure fraction stays within bounds
        adjusted_fraction = max(
            self.config.min_kelly_fraction,
            min(adjusted_fraction, self.config.max_kelly_fraction)
        )
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(recent_performance)
        
        # Next rebalancing date
        next_rebalance = datetime.now() + timedelta(days=self.config.rebalancing_frequency)
        
        return DynamicKellyResult(
            current_fraction=base_result.optimal_fraction,
            adjusted_fraction=adjusted_fraction,
            adjustment_reason=" + ".join(adjustment_reasons) or "no_adjustment",
            market_conditions=market_conditions,
            performance_metrics=performance_metrics,
            next_rebalance_date=next_rebalance
        )
    
    def calculate_portfolio_kelly(
        self,
        opportunities: List[Dict[str, Union[str, Decimal, Decimal]]],
        bankroll: Decimal,
        risk_constraints: Dict[str, Decimal] = None
    ) -> PortfolioKellyResult:
        """
        Calculate optimal Kelly fractions for a portfolio of opportunities.
        
        Args:
            opportunities: List of opportunities with odds, probabilities, and IDs
            bankroll: Total bankroll
            risk_constraints: Risk constraints (max exposure, diversification limits)
            
        Returns:
            PortfolioKellyResult with portfolio optimization results
        """
        if not opportunities:
            raise ValueError("No opportunities provided for portfolio optimization")
        
        # Extract individual opportunity data
        opportunity_data = []
        for opp in opportunities:
            if not all(key in opp for key in ['id', 'probability', 'odds']):
                raise ValueError("Each opportunity must have 'id', 'probability', and 'odds'")
            
            opportunity_data.append({
                'id': opp['id'],
                'probability': str(opp['probability']),
                'odds': str(opp['odds']),
                'correlation': opp.get('correlation', '0')
            })
        
        # Calculate individual Kelly fractions
        individual_kelly = []
        expected_returns = []
        
        for data in opportunity_data:
            kelly_result = self.calculate_classic_kelly(
                data['probability'], data['odds'], bankroll
            )
            individual_kelly.append(kelly_result.optimal_fraction)
            expected_returns.append(
                data['probability'] * data['odds'] * kelly_result.optimal_fraction
            )
        
        # Apply correlation adjustment
        correlation_matrix = self._build_correlation_matrix(opportunity_data)
        adjusted_kelly = self._apply_correlation_adjustment(individual_kelly, correlation_matrix)
        
        # Apply portfolio constraints
        portfolio_weights = self._apply_portfolio_constraints(
            adjusted_kelly, opportunity_data, risk_constraints or {}
        )
        
        # Calculate portfolio metrics
        total_weight = sum(portfolio_weights.values())
        expected_portfolio_return = sum(
            weight * ret for weight, ret in zip(portfolio_weights.values(), expected_returns)
        )
        
        # Simplified portfolio volatility calculation
        portfolio_volatility = self._calculate_portfolio_volatility(
            portfolio_weights, opportunity_data, correlation_matrix
        )
        
        # Calculate risk metrics
        sharpe_ratio = expected_portfolio_return / (portfolio_volatility + '1e-10')
        max_drawdown = self._estimate_max_drawdown(portfolio_weights, individual_kelly)
        var_95 = self._calculate_var(portfolio_volatility, self.config.confidence_level)
        
        # Check constraint satisfaction
        constraint_satisfaction = self._check_portfolio_constraints(
            portfolio_weights, risk_constraints or {}
        )
        
        return PortfolioKellyResult(
            portfolio_weights=portfolio_weights,
            total_kelly_fraction=total_weight,
            expected_portfolio_return=expected_portfolio_return,
            portfolio_volatility=portfolio_volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            var_95=var_95,
            constraint_satisfaction=constraint_satisfaction
        )
    
    def backtest_kelly_strategy(
        self,
        historical_data: List[Dict[str, Union[Decimal, datetime]]],
        initial_bankroll: Decimal,
        strategy_type: KellyMode = KellyMode.FRACTIONAL
    ) -> Dict[str, Union[Decimal, List[Dict]]]:
        """
        Backtest Kelly strategy on historical data.
        
        Args:
            historical_data: List of historical betting outcomes
            initial_bankroll: Starting bankroll
            strategy_type: Kelly strategy to backtest
            
        Returns:
            Dictionary with backtest results
        """
        bankroll = initial_bankroll
        bankroll_history = [bankroll]
        trade_history = []
        
        for i, trade in enumerate(historical_data):
            probability = str(trade['probability'])
            odds = str(trade['odds'])
            actual_outcome = trade['outcome']  # True/False or 1/0
            
            # Calculate Kelly fraction based on strategy
            if strategy_type == KellyMode.CLASSIC:
                kelly_result = self.calculate_classic_kelly(probability, odds, bankroll)
            elif strategy_type == KellyMode.FRACTIONAL:
                kelly_result = self.calculate_fractional_kelly(probability, odds, bankroll)
            else:
                kelly_result = self.calculate_classic_kelly(probability, odds, bankroll)
            
            # Calculate stake
            stake = bankroll * kelly_result.optimal_fraction
            
            # Simulate trade outcome
            if actual_outcome:
                profit = stake * (odds - '1')
                bankroll += profit
            else:
                bankroll -= stake
            
            # Record trade
            trade_history.append({
                'trade_id': i,
                'timestamp': trade.get('timestamp', datetime.now()),
                'kelly_fraction': kelly_result.optimal_fraction,
                'stake': stake,
                'outcome': actual_outcome,
                'bankroll_after': bankroll,
                'profit_loss': profit if actual_outcome else -stake
            })
            
            bankroll_history.append(bankroll)
        
        # Calculate performance metrics
        total_return = (bankroll - initial_bankroll) / initial_bankroll
        num_trades = len(historical_data)
        win_rate = sum(1 for trade in trade_history if trade['outcome']) / num_trades
        
        # Calculate additional metrics
        returns_list = [(history[i] - history[i-1]) / history[i-1] 
                       for i in range(1, len(bankroll_history))]
        
        volatility = np.std(returns_list) if len(returns_list) > 1 else 0
        sharpe_ratio = (np.mean(returns_list) / (volatility + 1e-10)) * np.sqrt(252) if len(returns_list) > 1 else 0
        
        max_drawdown = self._calculate_max_drawdown_from_history(bankroll_history)
        
        return {
            'final_bankroll': bankroll,
            'total_return': total_return,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'bankroll_history': bankroll_history,
            'trade_history': trade_history,
            'strategy_used': strategy_type.value
        }
    
    # Private helper methods
    def _validate_kelly_inputs(self, win_probability: Decimal, odds: Decimal, bankroll: Decimal) -> bool:
        """Validate Kelly calculation inputs."""
        try:
            return (
                '0' <= win_probability <= '1' and
                odds > '1' and
                bankroll > '0'
            )
        except (TypeError, ValueError):
            return False
    
    def _calculate_confidence_interval(
        self,
        kelly_fraction: Decimal,
        variance: Decimal,
        confidence_level: Decimal
    ) -> Tuple[Decimal, Decimal]:
        """Calculate confidence interval for Kelly fraction."""
        z_score = stats.norm.ppf((confidence_level + '1') / 2)
        margin_of_error = z_score * math.sqrt(variance)
        
        lower = max(kelly_fraction - margin_of_error, '0')
        upper = min(kelly_fraction + margin_of_error, self.config.max_kelly_fraction)
        
        return (lower, upper)
    
    def _calculate_volatility_adjustment(self, volatility: Decimal) -> Decimal:
        """Calculate volatility-based adjustment factor."""
        # Inverse relationship: higher volatility = lower Kelly fraction
        base_adjustment = '1' / ('1' + volatility)
        return max(base_adjustment, '0.1')  # Minimum 10% of original
    
    def _calculate_current_drawdown(self, recent_performance: List[Decimal]) -> Decimal:
        """Calculate current drawdown from recent performance."""
        if len(recent_performance) < 2:
            return '0'
        
        peak = max(recent_performance)
        current = recent_performance[-1]
        return (peak - current) / peak
    
    def _calculate_drawdown_adjustment(self, drawdown: Decimal) -> Decimal:
        """Calculate drawdown protection adjustment."""
        # Reduce Kelly fraction as drawdown increases
        adjustment = '1' - (drawdown / self.config.drawdown_threshold)
        return max(adjustment, '0.1')
    
    def _apply_market_adjustments(self, market_conditions: Dict[str, Decimal]) -> Dict[str, Decimal]:
        """Apply market condition adjustments."""
        adjustments = {}
        
        # Liquidity adjustment
        if 'liquidity' in market_conditions:
            liquidity = market_conditions['liquidity']
            adjustments['liquidity'] = min(liquidity, '1')
        
        # Market efficiency adjustment
        if 'efficiency' in market_conditions:
            efficiency = market_conditions['efficiency']
            adjustments['efficiency'] = '1' - (efficiency * '0.5')
        
        return adjustments
    
    def _calculate_performance_metrics(self, recent_performance: List[Decimal]) -> Dict[str, Decimal]:
        """Calculate performance metrics from recent performance."""
        if len(recent_performance) < 2:
            return {'win_rate': '0', 'avg_return': '0', 'volatility': '0'}
        
        returns = [
            (recent_performance[i] - recent_performance[i-1]) / recent_performance[i-1]
            for i in range(1, len(recent_performance))
        ]
        
        win_rate = str(sum(1 for r in returns if r > 0 / len(returns)))
        avg_return = str(np.mean(returns))
        volatility = str(np.std(returns))
        
        return {
            'win_rate': win_rate,
            'avg_return': avg_return,
            'volatility': volatility
        }
    
    def _build_correlation_matrix(self, opportunities: List[Dict]) -> np.ndarray:
        """Build correlation matrix for opportunities."""
        n = len(opportunities)
        correlation_matrix = np.eye(n)
        
        # For now, use provided correlations or assume independence
        for i in range(n):
            for j in range(i + 1, n):
                corr = float(opportunities[i].get('correlation', 0))
                correlation_matrix[i][j] = corr
                correlation_matrix[j][i] = corr
        
        return correlation_matrix
    
    def _apply_correlation_adjustment(self, kelly_fractions: List[Decimal], correlation_matrix: np.ndarray) -> List[Decimal]:
        """Apply correlation adjustments to Kelly fractions."""
        # Simplified correlation adjustment
        adjusted_fractions = []
        for i, fraction in enumerate(kelly_fractions):
            # Reduce fraction based on average correlation with other opportunities
            correlations = [correlation_matrix[i][j] for j in range(len(kelly_fractions)) if j != i]
            if correlations:
                avg_correlation = np.mean(correlations)
                adjustment = '1' - (avg_correlation * '0.3')  # 30% max reduction
                adjusted_fractions.append(fraction * max(adjustment, '0.1'))
            else:
                adjusted_fractions.append(fraction)
        
        return adjusted_fractions
    
    def _apply_portfolio_constraints(
        self,
        kelly_fractions: List[Decimal],
        opportunities: List[Dict],
        constraints: Dict[str, Decimal]
    ) -> Dict[str, Decimal]:
        """Apply portfolio constraints to Kelly fractions."""
        weights = {}
        total_fraction = sum(kelly_fractions)
        
        # Normalize fractions
        if total_fraction > '0':
            normalized_fractions = [f / total_fraction for f in kelly_fractions]
        else:
            normalized_fractions = ['0'] * len(kelly_fractions)
        
        # Apply max position size constraint
        max_position = constraints.get('max_position_size', '0.2')  # 20% default
        
        for i, (opportunity, fraction) in enumerate(zip(opportunities, normalized_fractions)):
            weights[opportunity['id']] = min(fraction, max_position)
        
        # Renormalize to ensure weights sum to reasonable amount
        total_weight = sum(weights.values())
        if total_weight > '1':
            factor = '1' / total_weight
            weights = {k: v * factor for k, v in weights.items()}
        
        return weights
    
    def _calculate_portfolio_volatility(
        self,
        weights: Dict[str, Decimal],
        opportunities: List[Dict],
        correlation_matrix: np.ndarray
    ) -> Decimal:
        """Calculate portfolio volatility."""
        # Simplified volatility calculation
        individual_volatilities = []
        for opp in opportunities:
            prob = opp['probability']
            odds = opp['odds']
            variance = prob * (odds - 1) ** 2 + (1 - prob)
            individual_volatilities.append(math.sqrt(float(variance)))
        
        # Portfolio variance with correlations
        portfolio_variance = 0
        n = len(weights)
        
        for i in range(n):
            for j in range(n):
                weight_i = float(list(weights.values())[i])
                weight_j = float(list(weights.values())[j])
                correlation = correlation_matrix[i][j]
                vol_i = individual_volatilities[i]
                vol_j = individual_volatilities[j]
                
                portfolio_variance += weight_i * weight_j * correlation * vol_i * vol_j
        
        return str(math.sqrt(portfolio_variance))
    
    def _estimate_max_drawdown(self, weights: Dict[str, Decimal], individual_kelly: List[Decimal]) -> Decimal:
        """Estimate maximum drawdown for portfolio."""
        # Simplified drawdown estimation
        total_weight = sum(weights.values())
        weighted_kelly = sum(w * k for w, k in zip(weights.values(), individual_kelly))
        
        # Conservative estimate: 3x the expected Kelly fraction
        estimated_drawdown = weighted_kelly * '3'
        return min(estimated_drawdown, '0.5')  # Cap at 50%
    
    def _calculate_var(self, volatility: Decimal, confidence_level: Decimal) -> Decimal:
        """Calculate Value at Risk."""
        z_score = stats.norm.ppf(1 - confidence_level)
        return str(abs(z_score * float(volatility)))
    
    def _check_portfolio_constraints(self, weights: Dict[str, Decimal], constraints: Dict[str, Decimal]) -> bool:
        """Check if portfolio satisfies all constraints."""
        max_position = constraints.get('max_position_size', '0.2')
        total_exposure = constraints.get('total_exposure', '1.0')
        
        # Check max position size
        for weight in weights.values():
            if weight > max_position:
                return False
        
        # Check total exposure
        if sum(weights.values()) > total_exposure:
            return False
        
        return True
    
    def _calculate_max_drawdown_from_history(self, bankroll_history: List[Decimal]) -> Decimal:
        """Calculate maximum drawdown from bankroll history."""
        peak = bankroll_history[0]
        max_drawdown = '0'
        
        for bankroll in bankroll_history:
            if bankroll > peak:
                peak = bankroll
            else:
                drawdown = (peak - bankroll) / peak
                max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown
    
    def get_calculation_history(self) -> List[Dict]:
        """Get history of Kelly calculations."""
        return self._calculation_history.copy()
    
    def clear_history(self):
        """Clear calculation history."""
        self._calculation_history.clear()
        self._performance_cache.clear()