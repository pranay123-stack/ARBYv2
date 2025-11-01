"""
Advanced Financial Mathematical Models

This module provides sophisticated financial mathematical models for arbitrage betting,
including expected value calculations, risk metrics, performance ratios, and portfolio optimization models.
"""

import math
from typing import List, Dict, Optional, Tuple, Union, Any, Callable
from decimal import Decimal, getcontext
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from scipy import stats
import logging
import numpy as np
from collections import deque
import statistics

# Configure decimal precision for financial calculations
getcontext().prec = 50


class RiskMetric(Enum):
    """Types of risk metrics."""
    VAR = "value_at_risk"
    CVAR = "conditional_value_at_risk"
    MAX_DRAWDOWN = "maximum_drawdown"
    VOLATILITY = "volatility"
    BETA = "beta"
    SHARPE = "sharpe_ratio"
    SORTINO = "sortino_ratio"
    CALMAR = "calmar_ratio"
    OMEGA = "omega_ratio"
    DRAWDOWN_DURATION = "drawdown_duration"


class OptimizationObjective(Enum):
    """Optimization objectives."""
    MAXIMIZE_SHARPE = "maximize_sharpe"
    MINIMIZE_VAR = "minimize_var"
    MAXIMIZE_EXPECTED_UTILITY = "maximize_expected_utility"
    MAXIMIZE_KELLY_CRITERION = "maximize_kelly_criterion"
    MINIMIZE_DRAWDOWN = "minimize_drawdown"
    MAXIMIZE_CALMAR = "maximize_calmar"


@dataclass
class RiskMetrics:
    """Container for various risk metrics."""
    volatility: Decimal
    var_95: Decimal
    var_99: Decimal
    cvar_95: Decimal
    cvar_99: Decimal
    maximum_drawdown: Decimal
    average_drawdown: Decimal
    drawdown_duration: timedelta
    beta_coefficient: Decimal
    alpha: Decimal
    correlation_coefficient: Decimal
    information_ratio: Decimal
    treynor_ratio: Decimal


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    calmar_ratio: Decimal
    omega_ratio: Decimal
    jen_alpha: Decimal
    jensen_alpha: Decimal
    treynor_ratio: Decimal
    information_ratio: Decimal
    sterling_ratio: Decimal
    burke_ratio: Decimal


@dataclass
class ExpectedUtilityResult:
    """Results from expected utility calculations."""
    utility_value: Decimal
    expected_return: Decimal
    risk_aversion_coefficient: Decimal
    certainty_equivalent: Decimal
    risk_premium: Decimal


@dataclass
class PortfolioOptimizationResult:
    """Results from portfolio optimization."""
    optimal_weights: Dict[str, Decimal]
    expected_return: Decimal
    expected_volatility: Decimal
    sharpe_ratio: Decimal
    optimization_objective: OptimizationObjective
    constraints_satisfied: bool
    convergence_achieved: bool
    iteration_count: int


class AdvancedMathematicalModels:
    """
    Advanced financial mathematical models for arbitrage betting.
    
    This class provides sophisticated mathematical models including:
    - Risk metrics calculation (VaR, CVaR, Maximum Drawdown, etc.)
    - Performance ratios (Sharpe, Sortino, Calmar, Omega)
    - Expected utility theory and Kelly criterion
    - Portfolio optimization models
    - Monte Carlo simulation for risk assessment
    - Statistical distribution fitting and analysis
    """
    
    def __init__(self, risk_free_rate: Decimal = Decimal('0.02')):
        """
        Initialize the mathematical models engine.
        
        Args:
            risk_free_rate: Risk-free rate for calculations (annualized)
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
        
        # Default parameters
        self.default_parameters = {
            'confidence_levels': [0.68, 0.95, 0.99],  # 1-sigma, 2-sigma, 3-sigma
            'var_confidence_levels': [0.95, 0.99, 0.999],
            'monte_carlo_simulations': 10000,
            'optimization_tolerance': Decimal('0.0001'),
            'max_iterations': 1000,
            'default_risk_aversion': Decimal('1.0'),
            'kelly_fraction_cap': Decimal('0.25'),  # Maximum 25% of bankroll
            'correlation_threshold': Decimal('0.7'),
            'drawdown_threshold': Decimal('0.1')  # 10% drawdown threshold
        }

    def calculate_expected_value(
        self,
        odds: Decimal,
        true_probability: Decimal,
        stake: Optional[Decimal] = None,
        commission: Optional[Decimal] = None
    ) -> Dict[str, Decimal]:
        """
        Calculate expected value for a bet with various adjustments.
        
        Args:
            odds: Decimal odds
            true_probability: True probability of winning (0 to 1)
            stake: Optional stake amount
            commission: Optional commission rate
            
        Returns:
            Dictionary containing expected value metrics
        """
        if odds <= 0 or true_probability < 0 or true_probability > 1:
            raise ValueError("Invalid odds or probability values")
        
        # Basic expected value
        basic_ev = (odds * true_probability) - Decimal('1')
        
        # Adjust for commission if provided
        adjusted_ev = basic_ev
        if commission is not None and commission > 0:
            commission_adjustment = odds * commission
            adjusted_ev = basic_ev - commission_adjustment
        
        # Calculate expected value with stake
        expected_return = Decimal('0')
        expected_profit = Decimal('0')
        
        if stake is not None:
            if stake < 0:
                raise ValueError("Stake must be non-negative")
            
            expected_return = adjusted_ev
            expected_profit = stake * adjusted_ev
        
        return {
            'basic_expected_value': basic_ev.quantize(Decimal('0.0001')),
            'adjusted_expected_value': adjusted_ev.quantize(Decimal('0.0001')),
            'expected_return': expected_return.quantize(Decimal('0.0001')),
            'expected_profit': expected_profit.quantize(Decimal('0.01')),
            'implied_probability': (Decimal('1') / odds).quantize(Decimal('0.0001')),
            'value_percentage': (adjusted_ev * Decimal('100')).quantize(Decimal('0.01'))
        }

    def calculate_sharpe_ratio(
        self,
        returns: List[Decimal],
        benchmark_returns: Optional[List[Decimal]] = None,
        risk_free_rate: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate Sharpe ratio for a series of returns.
        
        Args:
            returns: Series of returns
            benchmark_returns: Optional benchmark returns for information ratio
            risk_free_rate: Risk-free rate (uses default if not provided)
            
        Returns:
            Sharpe ratio (or information ratio if benchmark provided)
        """
        if len(returns) < 2:
            raise ValueError("At least 2 returns required for Sharpe ratio calculation")
        
        rf_rate = risk_free_rate or self.risk_free_rate
        
        # Convert to percentages
        excess_returns = [ret - rf_rate / Decimal('252') for ret in returns]  # Daily adjustment
        
        # Calculate mean excess return
        mean_excess_return = statistics.mean(excess_returns)
        
        # Calculate standard deviation
        returns_std = statistics.stdev(excess_returns) if len(excess_returns) > 1 else Decimal('0')
        
        if returns_std == 0:
            return Decimal('0')
        
        # Calculate Sharpe ratio
        sharpe_ratio = mean_excess_return / returns_std
        
        # Annualize (assuming daily returns)
        annualized_sharpe = sharpe_ratio * Decimal(str(math.sqrt(252)))
        
        return annualized_sharpe.quantize(Decimal('0.01'))

    def calculate_sortino_ratio(
        self,
        returns: List[Decimal],
        target_return: Optional[Decimal] = None,
        risk_free_rate: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate Sortino ratio (downside deviation based Sharpe ratio).
        
        Args:
            returns: Series of returns
            target_return: Target return (uses risk-free rate if not provided)
            risk_free_rate: Risk-free rate
            
        Returns:
            Sortino ratio
        """
        if len(returns) < 2:
            raise ValueError("At least 2 returns required for Sortino ratio calculation")
        
        target = target_return or (risk_free_rate or self.risk_free_rate) / Decimal('252')
        
        # Calculate excess returns below target
        downside_returns = [ret - target for ret in returns if ret < target]
        
        if not downside_returns:
            return Decimal('999')  # No downside returns = infinite Sortino ratio
        
        # Calculate downside deviation
        downside_deviation = statistics.stdev(downside_returns) if len(downside_returns) > 1 else Decimal('0')
        
        if downside_deviation == 0:
            return Decimal('999')
        
        # Calculate mean excess return
        mean_excess_return = statistics.mean([ret - target for ret in returns])
        
        # Calculate Sortino ratio
        sortino_ratio = mean_excess_return / downside_deviation
        
        # Annualize
        annualized_sortino = sortino_ratio * Decimal(str(math.sqrt(252)))
        
        return annualized_sortino.quantize(Decimal('0.01'))

    def calculate_maximum_drawdown(
        self,
        returns: List[Decimal],
        values: Optional[List[Decimal]] = None
    ) -> Dict[str, Any]:
        """
        Calculate maximum drawdown and related metrics.
        
        Args:
            returns: Series of returns
            values: Optional equity curve values
            
        Returns:
            Dictionary containing drawdown metrics
        """
        if values:
            equity_curve = values
        else:
            # Reconstruct equity curve from returns
            equity_curve = [Decimal('1')]
            for ret in returns:
                new_value = equity_curve[-1] * (Decimal('1') + ret)
                equity_curve.append(new_value)
        
        if len(equity_curve) < 2:
            raise ValueError("Insufficient data for drawdown calculation")
        
        # Calculate running maximum (peak)
        running_max = []
        current_max = equity_curve[0]
        for value in equity_curve:
            if value > current_max:
                current_max = value
            running_max.append(current_max)
        
        # Calculate drawdowns
        drawdowns = [(current - peak) / peak for current, peak in zip(equity_curve, running_max)]
        
        # Find maximum drawdown
        max_drawdown = min(drawdowns)
        max_dd_idx = drawdowns.index(max_drawdown)
        
        # Find the peak before maximum drawdown
        peak_idx = 0
        for i in range(max_dd_idx + 1):
            if equity_curve[i] == running_max[max_dd_idx]:
                peak_idx = i
                break
        
        # Calculate drawdown duration
        # Find when equity recovers above peak
        recovery_idx = None
        for i in range(max_dd_idx + 1, len(equity_curve)):
            if equity_curve[i] >= running_max[max_dd_idx]:
                recovery_idx = i
                break
        
        if recovery_idx is not None:
            drawdown_duration = recovery_idx - peak_idx
        else:
            drawdown_duration = len(equity_curve) - peak_idx - 1  # Still in drawdown
        
        # Calculate average drawdown
        non_zero_drawdowns = [dd for dd in drawdowns if dd < 0]
        avg_drawdown = statistics.mean(non_zero_drawdowns) if non_zero_drawdowns else Decimal('0')
        
        # Calculate ulcer index (measure of drawdown severity)
        ulcer_index = math.sqrt(statistics.mean([dd**2 for dd in drawdowns if dd < 0]))
        
        return {
            'maximum_drawdown': max_drawdown.quantize(Decimal('0.0001')),
            'maximum_drawdown_percentage': (max_drawdown * Decimal('100')).quantize(Decimal('0.01')),
            'peak_value': equity_curve[peak_idx],
            'trough_value': equity_curve[max_dd_idx],
            'peak_index': peak_idx,
            'trough_index': max_dd_idx,
            'drawdown_duration': drawdown_duration,
            'average_drawdown': avg_drawdown.quantize(Decimal('0.0001')),
            'average_drawdown_percentage': (avg_drawdown * Decimal('100')).quantize(Decimal('0.01')),
            'ulcer_index': Decimal(str(ulcer_index)).quantize(Decimal('0.0001')),
            'recovery_ratio': abs(max_drawdown) if max_drawdown != 0 else Decimal('999'),
            'pain_index': abs(avg_drawdown) if avg_drawdown != 0 else Decimal('0')
        }

    def calculate_var_cvar(
        self,
        returns: List[Decimal],
        confidence_levels: Optional[List[float]] = None
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Calculate Value at Risk (VaR) and Conditional VaR (CVaR).
        
        Args:
            returns: Series of returns
            confidence_levels: Confidence levels for VaR calculation
            
        Returns:
            Dictionary containing VaR and CVaR at different confidence levels
        """
        if not returns:
            raise ValueError("Returns list cannot be empty")
        
        conf_levels = confidence_levels or self.default_parameters['var_confidence_levels']
        
        # Convert to numpy array for percentile calculations
        returns_array = np.array([float(ret) for ret in returns])
        
        results = {}
        
        for conf_level in conf_levels:
            # Calculate VaR (percentile)
            var_percentile = np.percentile(returns_array, (1 - conf_level) * 100)
            var_value = Decimal(str(var_percentile))
            
            # Calculate CVaR (expected shortfall)
            tail_returns = returns_array[returns_array <= var_percentile]
            cvar_value = Decimal(str(np.mean(tail_returns))) if len(tail_returns) > 0 else var_value
            
            # Store results
            results[f'{int(conf_level*100)}%'] = {
                'var': var_value.quantize(Decimal('0.0001')),
                'cvar': cvar_value.quantize(Decimal('0.0001')),
                'var_percentage': (var_value * Decimal('100')).quantize(Decimal('0.01')),
                'cvar_percentage': (cvar_value * Decimal('100')).quantize(Decimal('0.01'))
            }
        
        return results

    def calculate_kelly_criterion(
        self,
        odds: Decimal,
        win_probability: Decimal,
        bankroll: Optional[Decimal] = None
    ) -> Dict[str, Decimal]:
        """
        Calculate Kelly criterion optimal bet size.
        
        Args:
            odds: Decimal odds
            win_probability: True probability of winning
            bankroll: Optional bankroll for stake calculation
            
        Returns:
            Dictionary containing Kelly metrics
        """
        if odds <= 0 or win_probability <= 0 or win_probability >= 1:
            raise ValueError("Invalid odds or probability values")
        
        # Calculate Kelly fraction: f = (bp - q) / b
        # where b = odds - 1, p = win probability, q = 1 - p
        b = odds - Decimal('1')
        p = win_probability
        q = Decimal('1') - p
        
        kelly_fraction = (b * p - q) / b
        
        # Apply constraints
        kelly_fraction = max(kelly_fraction, Decimal('0'))  # No negative bets
        kelly_fraction = min(kelly_fraction, self.default_parameters['kelly_fraction_cap'])  # Cap at maximum
        
        # Calculate half-Kelly (conservative approach)
        half_kelly = kelly_fraction / Decimal('2')
        
        # Calculate expected growth rate
        expected_growth = (b * p + q * (Decimal('1') / odds)) - Decimal('1')
        
        # Calculate optimal stake if bankroll provided
        optimal_stake = Decimal('0')
        if bankroll is not None and bankroll > 0:
            optimal_stake = bankroll * kelly_fraction
        
        return {
            'kelly_fraction': kelly_fraction.quantize(Decimal('0.0001')),
            'half_kelly_fraction': half_kelly.quantize(Decimal('0.0001')),
            'expected_growth_rate': expected_growth.quantize(Decimal('0.0001')),
            'expected_growth_percentage': (expected_growth * Decimal('100')).quantize(Decimal('0.01')),
            'optimal_stake': optimal_stake.quantize(Decimal('0.01')),
            'edge': (p - (Decimal('1') / odds)).quantize(Decimal('0.0001')),
            'edge_percentage': ((p - (Decimal('1') / odds)) * Decimal('100')).quantize(Decimal('0.01'))
        }

    def calculate_omega_ratio(
        self,
        returns: List[Decimal],
        threshold_return: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate Omega ratio (ratio of gains to losses relative to threshold).
        
        Args:
            returns: Series of returns
            threshold_return: Threshold return (uses risk-free rate if not provided)
            
        Returns:
            Omega ratio
        """
        if not returns:
            raise ValueError("Returns list cannot be empty")
        
        threshold = threshold_return or self.risk_free_rate / Decimal('252')
        
        # Separate gains and losses relative to threshold
        gains = [ret for ret in returns if ret > threshold]
        losses = [ret for ret in returns if ret < threshold]
        
        if not gains or not losses:
            return Decimal('999')  # Infinite ratio if no losses
        
        # Calculate sum of gains and losses
        total_gains = sum(gains)
        total_losses = abs(sum(losses))
        
        if total_losses == 0:
            return Decimal('999')
        
        # Calculate Omega ratio
        omega_ratio = total_gains / total_losses
        
        return omega_ratio.quantize(Decimal('0.01'))

    def calculate_information_ratio(
        self,
        portfolio_returns: List[Decimal],
        benchmark_returns: List[Decimal]
    ) -> Decimal:
        """
        Calculate Information ratio (tracking error based measure).
        
        Args:
            portfolio_returns: Portfolio returns
            benchmark_returns: Benchmark returns
            
        Returns:
            Information ratio
        """
        if len(portfolio_returns) != len(benchmark_returns):
            raise ValueError("Portfolio and benchmark returns must have same length")
        
        if len(portfolio_returns) < 2:
            raise ValueError("At least 2 return observations required")
        
        # Calculate active returns
        active_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        
        # Calculate mean active return
        mean_active_return = statistics.mean(active_returns)
        
        # Calculate tracking error (standard deviation of active returns)
        tracking_error = statistics.stdev(active_returns) if len(active_returns) > 1 else Decimal('0')
        
        if tracking_error == 0:
            return Decimal('0')
        
        # Calculate Information ratio
        information_ratio = mean_active_return / tracking_error
        
        return information_ratio.quantize(Decimal('0.01'))

    def monte_carlo_simulation(
        self,
        returns_distribution: Dict[str, Any],
        initial_value: Decimal,
        time_horizon: timedelta,
        simulations: Optional[int] = None,
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Perform Monte Carlo simulation for risk assessment.
        
        Args:
            returns_distribution: Distribution parameters (mean, std, type)
            initial_value: Initial portfolio value
            time_horizon: Simulation time horizon
            simulations: Number of simulations (uses default if not provided)
            confidence_level: Confidence level for results
            
        Returns:
            Dictionary containing simulation results
        """
        num_sims = simulations or self.default_parameters['monte_carlo_simulations']
        
        # Extract distribution parameters
        mean_return = returns_distribution.get('mean', Decimal('0'))
        std_return = returns_distribution.get('std', Decimal('0.01'))
        distribution_type = returns_distribution.get('type', 'normal')
        
        # Generate random returns
        simulated_paths = []
        
        for _ in range(num_sims):
            # Simple random walk simulation
            path = [float(initial_value)]
            current_value = float(initial_value)
            
            # Calculate number of periods (assuming daily periods)
            periods = max(1, int(time_horizon.total_seconds() / 86400))
            
            for period in range(periods):
                if distribution_type == 'normal':
                    # Normal distribution
                    random_return = np.random.normal(float(mean_return), float(std_return))
                elif distribution_type == 't_distribution':
                    # Student's t distribution (fat tails)
                    random_return = np.random.standard_t(3) * float(std_return) + float(mean_return)
                else:
                    # Default to normal
                    random_return = np.random.normal(float(mean_return), float(std_return))
                
                # Update value
                current_value *= (1 + random_return)
                path.append(current_value)
            
            simulated_paths.append(path)
        
        # Calculate statistics
        final_values = [path[-1] for path in simulated_paths]
        
        # Calculate percentiles
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        percentile_values = {f'p{p}': Decimal(str(np.percentile(final_values, p))) for p in percentiles}
        
        # Calculate probability of loss
        prob_loss = sum(1 for val in final_values if val < float(initial_value)) / len(final_values)
        
        # Calculate expected return
        expected_final_value = Decimal(str(np.mean(final_values)))
        expected_return = (expected_final_value / initial_value - Decimal('1'))
        
        # Calculate volatility of final values
        final_value_volatility = Decimal(str(np.std(final_values)))
        
        return {
            'simulations_count': num_sims,
            'initial_value': initial_value,
            'expected_final_value': expected_final_value.quantize(Decimal('0.01')),
            'expected_return': expected_return.quantize(Decimal('0.0001')),
            'expected_return_percentage': (expected_return * Decimal('100')).quantize(Decimal('0.01')),
            'probability_of_loss': Decimal(str(prob_loss)).quantize(Decimal('0.0001')),
            'final_value_volatility': final_value_volatility.quantize(Decimal('0.01')),
            'percentile_values': {k: v.quantize(Decimal('0.01')) for k, v in percentile_values.items()},
            'var_95': percentile_values['p5'].quantize(Decimal('0.01')),
            'var_99': percentile_values['p1'].quantize(Decimal('0.01')),
            'best_case': max(final_values),
            'worst_case': min(final_values),
            'median_outcome': percentile_values['p50'].quantize(Decimal('0.01'))
        }

    def optimize_portfolio_kelly(
        self,
        opportunities: List[Dict[str, Any]],
        bankroll: Decimal,
        constraints: Optional[Dict[str, Any]] = None
    ) -> PortfolioOptimizationResult:
        """
        Optimize portfolio allocation using Kelly criterion with constraints.
        
        Args:
            opportunities: List of opportunities with odds, probabilities, etc.
            bankroll: Total bankroll
            constraints: Optimization constraints
            
        Returns:
            PortfolioOptimizationResult
        """
        if not opportunities:
            raise ValueError("At least one opportunity required")
        
        # Default constraints
        default_constraints = {
            'max_single_exposure': Decimal('0.2'),  # Max 20% on single opportunity
            'min_opportunities': 1,
            'max_opportunities': len(opportunities)
        }
        
        if constraints:
            default_constraints.update(constraints)
        
        constraints = default_constraints
        
        # Calculate Kelly fractions for each opportunity
        kelly_fractions = []
        expected_returns = []
        
        for opp in opportunities:
            odds = opp['odds']
            win_prob = opp['win_probability']
            
            kelly_result = self.calculate_kelly_criterion(odds, win_prob)
            kelly_fractions.append(kelly_result['kelly_fraction'])
            expected_returns.append(kelly_result['expected_growth_rate'])
        
        # Apply constraints
        # Normalize to sum to 1 (or less with cash)
        total_kelly = sum(kelly_fractions)
        
        if total_kelly <= 0:
            # No positive Kelly opportunities
            return PortfolioOptimizationResult(
                optimal_weights={},
                expected_return=Decimal('0'),
                expected_volatility=Decimal('0'),
                sharpe_ratio=Decimal('0'),
                optimization_objective=OptimizationObjective.MAXIMIZE_KELLY_CRITERION,
                constraints_satisfied=True,
                convergence_achieved=True,
                iteration_count=1
            )
        
        # Normalize fractions
        normalized_fractions = [kf / total_kelly for kf in kelly_fractions]
        
        # Apply maximum exposure constraint
        max_single = constraints['max_single_exposure']
        constrained_fractions = [min(frac, max_single) for frac in normalized_fractions]
        
        # Renormalize if necessary
        total_constrained = sum(constrained_fractions)
        if total_constrained > 1:
            constrained_fractions = [frac / total_constrained for frac in constrained_fractions]
        
        # Calculate optimal weights in currency terms
        total_allocated = bankroll * sum(constrained_fractions)
        weights = {
            f"opp_{i}": bankroll * frac for i, frac in enumerate(constrained_fractions)
        }
        
        # Calculate expected portfolio metrics
        portfolio_expected_return = sum(er * frac for er, frac in zip(expected_returns, constrained_fractions))
        portfolio_volatility = self._calculate_portfolio_volatility(constrained_fractions, opportunities)
        portfolio_sharpe = self._calculate_portfolio_sharpe(
            portfolio_expected_return, portfolio_volatility
        )
        
        return PortfolioOptimizationResult(
            optimal_weights=weights,
            expected_return=portfolio_expected_return.quantize(Decimal('0.0001')),
            expected_volatility=portfolio_volatility.quantize(Decimal('0.0001')),
            sharpe_ratio=portfolio_sharpe.quantize(Decimal('0.01')),
            optimization_objective=OptimizationObjective.MAXIMIZE_KELLY_CRITERION,
            constraints_satisfied=True,
            convergence_achieved=True,
            iteration_count=1
        )

    def calculate_expected_utility(
        self,
        returns: List[Decimal],
        risk_aversion_coefficient: Optional[Decimal] = None,
        utility_function: str = 'crra'
    ) -> ExpectedUtilityResult:
        """
        Calculate expected utility from a series of returns.
        
        Args:
            returns: Series of returns
            risk_aversion_coefficient: Risk aversion parameter
            utility_function: Type of utility function ('crra', 'cara', 'quadratic')
            
        Returns:
            ExpectedUtilityResult
        """
        if not returns:
            raise ValueError("Returns list cannot be empty")
        
        risk_aversion = risk_aversion_coefficient or self.default_parameters['default_risk_aversion']
        
        # Calculate utility values
        utilities = []
        for ret in returns:
            utility = self._calculate_utility_value(ret, risk_aversion, utility_function)
            utilities.append(utility)
        
        # Calculate expected utility
        expected_utility = statistics.mean(utilities)
        
        # Calculate expected return
        expected_return = statistics.mean(returns)
        
        # Calculate certainty equivalent (return that gives same utility as expected utility)
        certainty_equivalent = self._calculate_certainty_equivalent(
            expected_utility, risk_aversion, utility_function
        )
        
        # Calculate risk premium
        risk_premium = expected_return - certainty_equivalent
        
        return ExpectedUtilityResult(
            utility_value=Decimal(str(expected_utility)).quantize(Decimal('0.0001')),
            expected_return=expected_return.quantize(Decimal('0.0001')),
            risk_aversion_coefficient=risk_aversion,
            certainty_equivalent=certainty_equivalent.quantize(Decimal('0.0001')),
            risk_premium=risk_premium.quantize(Decimal('0.0001'))
        )

    def fit_distribution(
        self,
        data: List[Decimal],
        distribution_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fit statistical distributions to return data.
        
        Args:
            data: Data to fit
            distribution_types: Types of distributions to try
            
        Returns:
            Dictionary containing distribution fitting results
        """
        if not data or len(data) < 10:
            raise ValueError("At least 10 data points required for distribution fitting")
        
        default_distributions = ['normal', 't', 'skewed_t', 'generalized_extreme_value']
        dist_types = distribution_types or default_distributions
        
        # Convert to numpy array
        data_array = np.array([float(d) for d in data])
        
        fitting_results = {}
        
        for dist_type in dist_types:
            try:
                if dist_type == 'normal':
                    # Normal distribution
                    params = stats.norm.fit(data_array)
                    dist = stats.norm(*params)
                    ks_stat, ks_p = stats.kstest(data_array, dist.cdf)
                    
                    fitting_results[dist_type] = {
                        'parameters': {'loc': params[0], 'scale': params[1]},
                        'ks_statistic': ks_stat,
                        'ks_p_value': ks_p,
                        'aic': self._calculate_aic(data_array, dist),
                        'bic': self._calculate_bic(data_array, dist),
                        'log_likelihood': np.sum(dist.logpdf(data_array))
                    }
                
                elif dist_type == 't':
                    # Student's t distribution
                    params = stats.t.fit(data_array)
                    dist = stats.t(*params)
                    ks_stat, ks_p = stats.kstest(data_array, dist.cdf)
                    
                    fitting_results[dist_type] = {
                        'parameters': {'df': params[0], 'loc': params[1], 'scale': params[2]},
                        'ks_statistic': ks_stat,
                        'ks_p_value': ks_p,
                        'aic': self._calculate_aic(data_array, dist),
                        'bic': self._calculate_bic(data_array, dist),
                        'log_likelihood': np.sum(dist.logpdf(data_array))
                    }
                
                elif dist_type == 'skewed_t':
                    # Skewed t distribution (simplified approximation)
                    # Using scipy's skewnorm as approximation
                    params = stats.skewnorm.fit(data_array)
                    dist = stats.skewnorm(*params)
                    ks_stat, ks_p = stats.kstest(data_array, dist.cdf)
                    
                    fitting_results[dist_type] = {
                        'parameters': {'a': params[0], 'loc': params[1], 'scale': params[2]},
                        'ks_statistic': ks_stat,
                        'ks_p_value': ks_p,
                        'aic': self._calculate_aic(data_array, dist),
                        'bic': self._calculate_bic(data_array, dist),
                        'log_likelihood': np.sum(dist.logpdf(data_array))
                    }
                
                elif dist_type == 'generalized_extreme_value':
                    # Generalized Extreme Value distribution
                    params = stats.genextreme.fit(data_array)
                    dist = stats.genextreme(*params)
                    ks_stat, ks_p = stats.kstest(data_array, dist.cdf)
                    
                    fitting_results[dist_type] = {
                        'parameters': {'c': params[0], 'loc': params[1], 'scale': params[2]},
                        'ks_statistic': ks_stat,
                        'ks_p_value': ks_p,
                        'aic': self._calculate_aic(data_array, dist),
                        'bic': self._calculate_bic(data_array, dist),
                        'log_likelihood': np.sum(dist.logpdf(data_array))
                    }
            
            except Exception as e:
                self.logger.warning(f"Failed to fit {dist_type} distribution: {str(e)}")
                fitting_results[dist_type] = {'error': str(e)}
        
        # Find best fitting distribution
        best_dist = None
        best_aic = float('inf')
        
        for dist_name, result in fitting_results.items():
            if 'aic' in result and result['aic'] < best_aic:
                best_aic = result['aic']
                best_dist = dist_name
        
        fitting_results['best_fit'] = best_dist
        fitting_results['best_aic'] = best_aic
        
        return fitting_results

    def calculate_comprehensive_risk_metrics(
        self,
        returns: List[Decimal],
        benchmark_returns: Optional[List[Decimal]] = None
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics for a return series.
        
        Args:
            returns: Series of returns
            benchmark_returns: Optional benchmark returns for relative metrics
            
        Returns:
            RiskMetrics object containing all risk metrics
        """
        if not returns or len(returns) < 2:
            raise ValueError("At least 2 returns required for risk metric calculation")
        
        # Basic volatility
        returns_array = np.array([float(ret) for ret in returns])
        volatility = Decimal(str(np.std(returns_array))).quantize(Decimal('0.0001'))
        
        # VaR and CVaR
        var_results = self.calculate_var_cvar(returns)
        var_95 = var_results['95%']['var']
        var_99 = var_results['99%']['var']
        cvar_95 = var_results['95%']['cvar']
        cvar_99 = var_results['99%']['cvar']
        
        # Maximum drawdown
        drawdown_results = self.calculate_maximum_drawdown(returns)
        max_drawdown = drawdown_results['maximum_drawdown']
        avg_drawdown = drawdown_results['average_drawdown']
        drawdown_duration = timedelta(days=drawdown_results['drawdown_duration'])
        
        # Beta and alpha (if benchmark provided)
        beta_coeff = Decimal('0')
        alpha = Decimal('0')
        
        if benchmark_returns and len(benchmark_returns) == len(returns):
            benchmark_array = np.array([float(ret) for ret in benchmark_returns])
            
            # Calculate correlation
            correlation = np.corrcoef(returns_array, benchmark_array)[0, 1]
            correlation_coeff = Decimal(str(correlation))
            
            # Calculate beta (covariance / variance of benchmark)
            covariance = np.cov(returns_array, benchmark_array)[0, 1]
            benchmark_variance = np.var(benchmark_array)
            
            if benchmark_variance > 0:
                beta_coeff = Decimal(str(covariance / benchmark_variance))
            
            # Calculate alpha
            portfolio_return = np.mean(returns_array)
            benchmark_return = np.mean(benchmark_array)
            alpha = Decimal(str(portfolio_return - (float(self.risk_free_rate/252) + beta_coeff * (benchmark_return - float(self.risk_free_rate/252)))))
        
        # Information ratio
        information_ratio = Decimal('0')
        if benchmark_returns:
            information_ratio = self.calculate_information_ratio(returns, benchmark_returns)
        
        # Treynor ratio
        treynor_ratio = Decimal('0')
        if beta_coeff != 0:
            portfolio_return = statistics.mean(returns)
            treynor_ratio = (portfolio_return - self.risk_free_rate / Decimal('252')) / beta_coeff
        
        return RiskMetrics(
            volatility=volatility,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
            maximum_drawdown=max_drawdown,
            average_drawdown=avg_drawdown,
            drawdown_duration=drawdown_duration,
            beta_coefficient=beta_coeff,
            alpha=alpha,
            correlation_coefficient=correlation_coeff if benchmark_returns else Decimal('0'),
            information_ratio=information_ratio,
            treynor_ratio=treynor_ratio
        )

    def calculate_comprehensive_performance_metrics(
        self,
        returns: List[Decimal],
        benchmark_returns: Optional[List[Decimal]] = None,
        risk_free_rate: Optional[Decimal] = None
    ) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            returns: Series of returns
            benchmark_returns: Optional benchmark returns
            risk_free_rate: Risk-free rate
            
        Returns:
            PerformanceMetrics object
        """
        rf_rate = risk_free_rate or self.risk_free_rate
        
        # Sharpe ratio
        sharpe_ratio = self.calculate_sharpe_ratio(returns, benchmark_returns, rf_rate)
        
        # Sortino ratio
        sortino_ratio = self.calculate_sortino_ratio(returns, rf_rate, rf_rate)
        
        # Calmar ratio
        drawdown_results = self.calculate_maximum_drawdown(returns)
        avg_return = statistics.mean(returns)
        calmar_ratio = Decimal('0')
        if drawdown_results['maximum_drawdown'] != 0:
            calmar_ratio = (avg_return * Decimal('252')) / abs(drawdown_results['maximum_drawdown'])  # Annualized
        
        # Omega ratio
        omega_ratio = self.calculate_omega_ratio(returns, rf_rate / Decimal('252'))
        
        # Information ratio
        information_ratio = Decimal('0')
        if benchmark_returns:
            information_ratio = self.calculate_information_ratio(returns, benchmark_returns)
        
        # Treynor ratio
        treynor_ratio = Decimal('0')
        if benchmark_returns:
            # Calculate beta
            returns_array = np.array([float(ret) for ret in returns])
            benchmark_array = np.array([float(ret) for ret in benchmark_returns])
            covariance = np.cov(returns_array, benchmark_array)[0, 1]
            benchmark_variance = np.var(benchmark_array)
            
            if benchmark_variance > 0:
                beta = covariance / benchmark_variance
                portfolio_return = statistics.mean(returns)
                treynor_ratio = (portfolio_return - rf_rate / Decimal('252')) / Decimal(str(beta))
        
        # Calculate alpha (Jensen's alpha)
        jensen_alpha = Decimal('0')
        if benchmark_returns and treynor_ratio != 0:
            benchmark_sharpe = self.calculate_sharpe_ratio(benchmark_returns, None, rf_rate)
            portfolio_return = statistics.mean(returns)
            jensen_alpha = (portfolio_return - rf_rate / Decimal('252')) - (sharpe_ratio - benchmark_sharpe) * (statistics.mean([r - rf_rate/252 for r in benchmark_returns]))
        
        # Sterling ratio (modified Sharpe with 3-year annualized return)
        sterling_ratio = Decimal('0')
        annualized_return = avg_return * Decimal('252')
        if drawdown_results['average_drawdown'] != 0:
            sterling_ratio = annualized_return / abs(drawdown_results['average_drawdown'])
        
        # Burke ratio (modified Sharpe with max drawdown)
        burke_ratio = Decimal('0')
        if drawdown_results['maximum_drawdown'] != 0:
            burke_ratio = annualized_return / (drawdown_results['maximum_drawdown'].sqrt())
        
        return PerformanceMetrics(
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio.quantize(Decimal('0.01')),
            omega_ratio=omega_ratio,
            jen_alpha=jensen_alpha.quantize(Decimal('0.0001')),
            jensen_alpha=jensen_alpha.quantize(Decimal('0.0001')),
            treynor_ratio=treynor_ratio.quantize(Decimal('0.01')),
            information_ratio=information_ratio,
            sterling_ratio=sterling_ratio.quantize(Decimal('0.01')),
            burke_ratio=burke_ratio.quantize(Decimal('0.01'))
        )

    # Helper methods
    def _calculate_portfolio_volatility(
        self,
        weights: List[Decimal],
        opportunities: List[Dict[str, Any]]
    ) -> Decimal:
        """Calculate portfolio volatility given weights and opportunities."""
        if len(weights) != len(opportunities):
            raise ValueError("Weights and opportunities must have same length")
        
        # For simplicity, assume no correlation between opportunities
        # In practice, would need correlation matrix
        individual_volatilities = []
        
        for opp, weight in zip(opportunities, weights):
            odds = opp['odds']
            win_prob = opp['win_probability']
            
            # Calculate individual volatility (simplified)
            expected_return = (odds - Decimal('1')) * win_prob - (Decimal('1') - win_prob)
            variance = win_prob * (expected_return ** 2) + (Decimal('1') - win_prob) * (Decimal('1') ** 2) - expected_return ** 2
            volatility = variance.sqrt()
            individual_volatilities.append(volatility)
        
        # Portfolio variance (assuming zero correlation)
        portfolio_variance = sum((w ** 2) * (v ** 2) for w, v in zip(weights, individual_volatilities))
        portfolio_volatility = portfolio_variance.sqrt()
        
        return portfolio_volatility

    def _calculate_portfolio_sharpe(
        self,
        expected_return: Decimal,
        volatility: Decimal
    ) -> Decimal:
        """Calculate portfolio Sharpe ratio."""
        if volatility == 0:
            return Decimal('0')
        
        excess_return = expected_return - self.risk_free_rate / Decimal('252')
        sharpe = excess_return / volatility
        
        # Annualize
        annualized_sharpe = sharpe * Decimal(str(math.sqrt(252)))
        
        return annualized_sharpe

    def _calculate_utility_value(
        self,
        return_value: Decimal,
        risk_aversion: Decimal,
        utility_function: str
    ) -> float:
        """Calculate utility value for a given return."""
        if utility_function == 'crra':
            # Constant Relative Risk Aversion (power utility)
            if risk_aversion == 1:
                return float(math.log(1 + return_value))
            else:
                return float(((1 + return_value) ** (1 - risk_aversion) - 1) / (1 - risk_aversion))
        
        elif utility_function == 'cara':
            # Constant Absolute Risk Aversion (exponential utility)
            return float(-math.exp(-risk_aversion * return_value))
        
        elif utility_function == 'quadratic':
            # Quadratic utility (decreasing absolute risk aversion)
            return float(return_value - (risk_aversion / 2) * (return_value ** 2))
        
        else:
            # Default to CRRA
            if risk_aversion == 1:
                return float(math.log(1 + return_value))
            else:
                return float(((1 + return_value) ** (1 - risk_aversion) - 1) / (1 - risk_aversion))

    def _calculate_certainty_equivalent(
        self,
        expected_utility: float,
        risk_aversion: Decimal,
        utility_function: str
    ) -> Decimal:
        """Calculate certainty equivalent from expected utility."""
        ra = float(risk_aversion)
        
        if utility_function == 'crra':
            if ra == 1:
                return Decimal(str(math.exp(expected_utility) - 1))
            else:
                return Decimal(str(((1 - ra) * expected_utility + 1) ** (1 / (1 - ra)) - 1))
        
        elif utility_function == 'cara':
            return Decimal(str(-math.log(-expected_utility) / ra))
        
        elif utility_function == 'quadratic':
            # Solve quadratic equation for quadratic utility
            discriminant = 1 + 2 * ra * expected_utility
            if discriminant >= 0:
                return Decimal(str((math.sqrt(discriminant) - 1) / ra))
            else:
                return Decimal('0')
        
        else:
            # Default to CRRA
            if ra == 1:
                return Decimal(str(math.exp(expected_utility) - 1))
            else:
                return Decimal(str(((1 - ra) * expected_utility + 1) ** (1 / (1 - ra)) - 1))

    def _calculate_aic(self, data: np.ndarray, distribution) -> float:
        """Calculate Akaike Information Criterion."""
        log_likelihood = np.sum(distribution.logpdf(data))
        num_params = len(distribution.fit(data))
        return -2 * log_likelihood + 2 * num_params

    def _calculate_bic(self, data: np.ndarray, distribution) -> float:
        """Calculate Bayesian Information Criterion."""
        log_likelihood = np.sum(distribution.logpdf(data))
        num_params = len(distribution.fit(data))
        num_data_points = len(data)
        return -2 * log_likelihood + num_params * math.log(num_data_points)


def create_mathematical_models(risk_free_rate: Decimal = Decimal('0.02')) -> AdvancedMathematicalModels:
    """
    Factory function to create and configure a mathematical models engine.
    
    Args:
        risk_free_rate: Risk-free rate for calculations
        
    Returns:
        Configured AdvancedMathematicalModels instance
    """
    return AdvancedMathematicalModels(risk_free_rate=risk_free_rate)