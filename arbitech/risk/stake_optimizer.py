"""
Multi-Strategy Stake Optimization System

This module provides comprehensive stake optimization algorithms including fixed-fractional,
optimal f, risk parity, and custom optimization strategies with sophisticated constraint handling.
"""

import math
from typing import List, Dict, Optional, Tuple, Union, Callable, NamedTuple
from decimal import Decimal, getcontext
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from scipy import optimize
from scipy.stats import norm
import warnings
import logging

# Configure decimal precision for financial calculations
getcontext().prec = 50


class OptimizationStrategy(Enum):
    """Types of optimization strategies."""
    FIXED_FRACTIONAL = "fixed_fractional"
    OPTIMAL_F = "optimal_f"
    RISK_PARITY = "risk_parity"
    KELLY_CRITERION = "kelly_criterion"
    MAXIMUM_SHARPE = "maximum_sharpe"
    MINIMUM_VAR = "minimum_var"
    MAXIMUM_UTILITY = "maximum_utility"
    CUSTOM = "custom"


class ConstraintType(Enum):
    """Types of optimization constraints."""
    MAX_POSITION = "max_position"
    TOTAL_EXPOSURE = "total_exposure"
    CORRELATION_LIMIT = "correlation_limit"
    LIQUIDITY_CONSTRAINT = "liquidity_constraint"
    DIVERSIFICATION_RATIO = "diversification_ratio"
    RISK_BUDGET = "risk_budget"


@dataclass
class OptimizationConfig:
    """Configuration for stake optimization."""
    strategy: OptimizationStrategy = OptimizationStrategy.KELLY_CRITERION
    max_iterations: int = 1000
    tolerance: Decimal = '1e-6'
    transaction_cost_rate: Decimal = '0.005'
    slippage_rate: Decimal = '0.002'
    rebalancing_cost: Decimal = '0.001'
    confidence_level: Decimal = '0.95'
    max_correlation: Decimal = '0.7'
    min_diversification: Decimal = '0.3'
    risk_free_rate: Decimal = '0.02'
    utility_function: str = "logarithmic"  # logarithmic, power, exponential
    objective_weights: Dict[str, Decimal] = field(default_factory=lambda: {
        'return': '0.4',
        'risk': '0.3',
        'diversification': '0.2',
        'liquidity': '0.1'
    })


@dataclass
class ConstraintSet:
    """Set of optimization constraints."""
    max_position_size: Optional[Decimal] = None
    min_position_size: Optional[Decimal] = None
    total_exposure_limit: Optional[Decimal] = None
    correlation_limit: Optional[Decimal] = None
    liquidity_limit: Optional[Decimal] = None
    diversification_min: Optional[Decimal] = None
    risk_budget: Optional[Decimal] = None
    sector_limits: Optional[Dict[str, Decimal]] = None
    geographic_limits: Optional[Dict[str, Decimal]] = None


@dataclass
class OptimizationResult:
    """Results from stake optimization."""
    optimal_stakes: Dict[str, Decimal]
    total_stake: Decimal
    expected_return: Decimal
    expected_variance: Decimal
    expected_sharpe_ratio: Decimal
    constraint_violations: List[str]
    optimization_status: str
    iterations_used: int
    objective_value: Decimal
    portfolio_metrics: Dict[str, Decimal]
    rebalancing_required: bool
    transaction_costs: Decimal


@dataclass
class MultiStrategyResult:
    """Results comparing multiple optimization strategies."""
    strategy_results: Dict[OptimizationStrategy, OptimizationResult]
    best_strategy: OptimizationStrategy
    best_objective_value: Decimal
    strategy_comparison: Dict[str, Dict[str, Decimal]]
    recommendation: str
    risk_adjusted_ranking: List[Tuple[OptimizationStrategy, Decimal]]


class StakeOptimizer:
    """
    Multi-Strategy Stake Optimizer
    
    Provides comprehensive stake optimization with support for:
    - Fixed-fractional betting
    - Optimal f (fixed ratio)
    - Risk parity allocation
    - Kelly criterion optimization
    - Maximum Sharpe ratio optimization
    - Custom utility functions
    - Sophisticated constraint handling
    """
    
    def __init__(self, config: OptimizationConfig = None):
        """Initialize stake optimizer with configuration."""
        self.config = config or OptimizationConfig()
        self.logger = self._setup_logger()
        
    def optimize_stakes(
        self,
        opportunities: List[Dict[str, Union[str, Decimal, Decimal, Decimal]]],
        bankroll: Decimal,
        constraints: ConstraintSet = None,
        historical_data: List[Dict] = None
    ) -> OptimizationResult:
        """
        Optimize stakes using the configured strategy.
        
        Args:
            opportunities: List of betting opportunities
            bankroll: Current bankroll amount
            constraints: Set of optimization constraints
            historical_data: Historical performance data for backtesting
            
        Returns:
            OptimizationResult with optimal stake allocation
        """
        if not opportunities:
            raise ValueError("No opportunities provided for optimization")
        
        constraints = constraints or ConstraintSet()
        
        # Validate inputs
        self._validate_opportunities(opportunities, bankroll)
        
        # Prepare data for optimization
        opportunity_data = self._prepare_optimization_data(opportunities, bankroll)
        
        # Apply optimization strategy
        if self.config.strategy == OptimizationStrategy.FIXED_FRACTIONAL:
            result = self._optimize_fixed_fractional(opportunity_data, bankroll, constraints)
        elif self.config.strategy == OptimizationStrategy.OPTIMAL_F:
            result = self._optimize_optimal_f(opportunity_data, bankroll, constraints)
        elif self.config.strategy == OptimizationStrategy.RISK_PARITY:
            result = self._optimize_risk_parity(opportunity_data, bankroll, constraints)
        elif self.config.strategy == OptimizationStrategy.KELLY_CRITERION:
            result = self._optimize_kelly(opportunity_data, bankroll, constraints)
        elif self.config.strategy == OptimizationStrategy.MAXIMUM_SHARPE:
            result = self._optimize_maximum_sharpe(opportunity_data, bankroll, constraints)
        elif self.config.strategy == OptimizationStrategy.MINIMUM_VAR:
            result = self._optimize_minimum_variance(opportunity_data, bankroll, constraints)
        elif self.config.strategy == OptimizationStrategy.MAXIMUM_UTILITY:
            result = self._optimize_maximum_utility(opportunity_data, bankroll, constraints)
        else:
            raise ValueError(f"Unsupported optimization strategy: {self.config.strategy}")
        
        # Validate constraints
        constraint_violations = self._check_constraints(result.optimal_stakes, constraints)
        result.constraint_violations = constraint_violations
        
        # Calculate transaction costs
        result.transaction_costs = self._calculate_transaction_costs(result.optimal_stakes)
        
        return result
    
    def compare_strategies(
        self,
        opportunities: List[Dict[str, Union[str, Decimal, Decimal, Decimal]]],
        bankroll: Decimal,
        strategies: List[OptimizationStrategy] = None,
        constraints: ConstraintSet = None
    ) -> MultiStrategyResult:
        """
        Compare multiple optimization strategies.
        
        Args:
            opportunities: List of betting opportunities
            bankroll: Current bankroll
            strategies: List of strategies to compare
            constraints: Optimization constraints
            
        Returns:
            MultiStrategyResult with strategy comparison
        """
        if strategies is None:
            strategies = list(OptimizationStrategy)
        
        strategy_results = {}
        strategy_metrics = {}
        
        # Run optimization for each strategy
        original_strategy = self.config.strategy
        
        for strategy in strategies:
            try:
                self.config.strategy = strategy
                result = self.optimize_stakes(opportunities, bankroll, constraints)
                strategy_results[strategy] = result
                
                # Calculate additional metrics for comparison
                metrics = {
                    'expected_return': result.expected_return,
                    'expected_variance': result.expected_variance,
                    'sharpe_ratio': result.expected_sharpe_ratio,
                    'total_stake': result.total_stake,
                    'constraint_violations': len(result.constraint_violations),
                    'objective_value': result.objective_value
                }
                strategy_metrics[strategy.value] = metrics
                
            except Exception as e:
                self.logger.warning(f"Strategy {strategy} failed: {str(e)}")
                continue
        
        # Restore original strategy
        self.config.strategy = original_strategy
        
        if not strategy_results:
            raise ValueError("No strategies completed successfully")
        
        # Determine best strategy
        best_strategy, best_objective = self._select_best_strategy(strategy_results)
        
        # Create risk-adjusted ranking
        risk_adjusted_ranking = self._create_risk_adjusted_ranking(strategy_results)
        
        # Generate recommendation
        recommendation = self._generate_strategy_recommendation(strategy_results, risk_adjusted_ranking)
        
        return MultiStrategyResult(
            strategy_results=strategy_results,
            best_strategy=best_strategy,
            best_objective_value=best_objective,
            strategy_comparison=strategy_metrics,
            recommendation=recommendation,
            risk_adjusted_ranking=risk_adjusted_ranking
        )
    
    def _optimize_fixed_fractional(
        self,
        data: Dict,
        bankroll: Decimal,
        constraints: ConstraintSet
    ) -> OptimizationResult:
        """Optimize using fixed-fractional strategy."""
        fixed_fraction = '0.02'  # 2% default
        
        optimal_stakes = {}
        total_stake = '0'
        
        for opp_id, opp_data in data.items():
            stake = bankroll * fixed_fraction
            optimal_stakes[opp_id] = stake
            total_stake += stake
        
        # Calculate expected metrics
        expected_return = sum(
            stake * opp_data['expected_return']
            for opp_id, stake in optimal_stakes.items()
        )
        
        expected_variance = self._calculate_portfolio_variance(optimal_stakes, data)
        sharpe_ratio = self._calculate_sharpe_ratio(expected_return, expected_variance)
        
        return OptimizationResult(
            optimal_stakes=optimal_stakes,
            total_stake=total_stake,
            expected_return=expected_return,
            expected_variance=expected_variance,
            expected_sharpe_ratio=sharpe_ratio,
            constraint_violations=[],
            optimization_status="success",
            iterations_used=1,
            objective_value=expected_return,
            portfolio_metrics={},
            rebalancing_required=False,
            transaction_costs='0'
        )
    
    def _optimize_optimal_f(
        self,
        data: Dict,
        bankroll: Decimal,
        constraints: ConstraintSet
    ) -> OptimizationResult:
        """Optimize using optimal f (fixed ratio) strategy."""
        # Calculate optimal f using Ralph Vince's method
        f_values = []
        
        for opp_id, opp_data in data.items():
            # Simplified optimal f calculation
            win_rate = opp_data['win_rate']
            avg_win = opp_data['avg_win']
            avg_loss = opp_data['avg_loss']
            
            if avg_loss > 0 and win_rate > 0:
                # Optimal f = (avg_win * win_rate - avg_loss * (1 - win_rate)) / avg_win
                optimal_f = (avg_win * win_rate - avg_loss * (1 - win_rate)) / avg_win
                f_values.append(max(optimal_f, '0'))
            else:
                f_values.append('0')
        
        # Average the f values and apply constraints
        avg_f = sum(f_values) / len(f_values) if f_values else '0'
        
        # Create stakes based on optimal f
        optimal_stakes = {}
        total_stake = '0'
        
        for i, (opp_id, opp_data) in enumerate(data.items()):
            stake = bankroll * avg_f * opp_data['confidence']
            optimal_stakes[opp_id] = stake
            total_stake += stake
        
        # Calculate portfolio metrics
        expected_return = sum(
            stake * opp_data['expected_return']
            for opp_id, stake in optimal_stakes.items()
        )
        
        expected_variance = self._calculate_portfolio_variance(optimal_stakes, data)
        sharpe_ratio = self._calculate_sharpe_ratio(expected_return, expected_variance)
        
        return OptimizationResult(
            optimal_stakes=optimal_stakes,
            total_stake=total_stake,
            expected_return=expected_return,
            expected_variance=expected_variance,
            expected_sharpe_ratio=sharpe_ratio,
            constraint_violations=[],
            optimization_status="success",
            iterations_used=len(data),
            objective_value=expected_return,
            portfolio_metrics={'optimal_f': avg_f},
            rebalancing_required=True,
            transaction_costs='0'
        )
    
    def _optimize_risk_parity(
        self,
        data: Dict,
        bankroll: Decimal,
        constraints: ConstraintSet
    ) -> OptimizationResult:
        """Optimize using risk parity strategy."""
        # Calculate risk contributions
        risks = {}
        total_risk = '0'
        
        for opp_id, opp_data in data.items():
            risk = math.sqrt(float(opp_data['variance']))
            risks[opp_id] = risk
            total_risk += risk
        
        # Equal risk contribution allocation
        optimal_stakes = {}
        total_stake = '0'
        
        for opp_id, risk in risks.items():
            if total_risk > 0:
                # Risk parity weight = (1/risk) / sum(1/risk_i)
                risk_weight = '1' / risk
                stake = (risk_weight / total_risk) * bankroll * '0.5'  # Use 50% of bankroll
            else:
                stake = '0'
            
            optimal_stakes[opp_id] = stake
            total_stake += stake
        
        # Calculate portfolio metrics
        expected_return = sum(
            stake * data[opp_id]['expected_return']
            for opp_id, stake in optimal_stakes.items()
        )
        
        expected_variance = self._calculate_portfolio_variance(optimal_stakes, data)
        sharpe_ratio = self._calculate_sharpe_ratio(expected_return, expected_variance)
        
        return OptimizationResult(
            optimal_stakes=optimal_stakes,
            total_stake=total_stake,
            expected_return=expected_return,
            expected_variance=expected_variance,
            expected_sharpe_ratio=sharpe_ratio,
            constraint_violations=[],
            optimization_status="success",
            iterations_used=len(data),
            objective_value=sharpe_ratio,
            portfolio_metrics={'risk_parity': True},
            rebalancing_required=True,
            transaction_costs='0'
        )
    
    def _optimize_kelly(
        self,
        data: Dict,
        bankroll: Decimal,
        constraints: ConstraintSet
    ) -> OptimizationResult:
        """Optimize using Kelly criterion strategy."""
        # Calculate individual Kelly fractions
        kelly_fractions = {}
        total_fraction = '0'
        
        for opp_id, opp_data in data.items():
            prob = opp_data['win_probability']
            odds = opp_data['odds']
            
            if odds > '1':
                b = odds - '1'
                kelly_fraction = (b * prob - ('1' - prob)) / b
                kelly_fraction = max(kelly_fraction, '0')
                kelly_fractions[opp_id] = kelly_fraction
                total_fraction += kelly_fraction
            else:
                kelly_fractions[opp_id] = '0'
        
        # Normalize fractions and apply constraints
        optimal_stakes = {}
        total_stake = '0'
        
        if total_fraction > '0':
            normalization_factor = min('1', '0.5' / total_fraction)  # Cap at 50% total exposure
            
            for opp_id, fraction in kelly_fractions.items():
                stake = bankroll * fraction * normalization_factor
                optimal_stakes[opp_id] = stake
                total_stake += stake
        else:
            for opp_id in data.keys():
                optimal_stakes[opp_id] = '0'
                total_stake = '0'
        
        # Calculate portfolio metrics
        expected_return = sum(
            stake * data[opp_id]['expected_return']
            for opp_id, stake in optimal_stakes.items()
        )
        
        expected_variance = self._calculate_portfolio_variance(optimal_stakes, data)
        sharpe_ratio = self._calculate_sharpe_ratio(expected_return, expected_variance)
        
        return OptimizationResult(
            optimal_stakes=optimal_stakes,
            total_stake=total_stake,
            expected_return=expected_return,
            expected_variance=expected_variance,
            expected_sharpe_ratio=sharpe_ratio,
            constraint_violations=[],
            optimization_status="success",
            iterations_used=len(data),
            objective_value=expected_return,
            portfolio_metrics={'kelly_fractions': kelly_fractions},
            rebalancing_required=True,
            transaction_costs='0'
        )
    
    def _optimize_maximum_sharpe(
        self,
        data: Dict,
        bankroll: Decimal,
        constraints: ConstraintSet
    ) -> OptimizationResult:
        """Optimize for maximum Sharpe ratio."""
        # Use scipy optimization for maximum Sharpe ratio
        num_assets = len(data)
        
        def objective(weights):
            """Objective function to minimize (negative Sharpe ratio)."""
            weights = np.array(weights)
            
            # Calculate portfolio return and risk
            returns = np.array([float(data[opp_id]['expected_return']) for opp_id in data.keys()])
            variances = np.array([float(data[opp_id]['variance']) for opp_id in data.keys()])
            
            portfolio_return = np.sum(weights * returns)
            portfolio_variance = np.sum(weights ** 2 * variances)  # Simplified
            
            if portfolio_variance <= 0:
                return 1000  # Penalty for invalid portfolio
            
            sharpe_ratio = (portfolio_return - float(self.config.risk_free_rate)) / math.sqrt(portfolio_variance)
            return -sharpe_ratio  # Minimize negative Sharpe ratio
        
        # Constraints and bounds
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},  # Weights sum to 1
        ]
        
        bounds = [(0, 1) for _ in range(num_assets)]
        
        # Initial guess
        x0 = np.array([1.0 / num_assets] * num_assets)
        
        # Optimize
        try:
            result = optimize.minimize(
                objective, x0, method='SLSQP',
                bounds=bounds, constraints=constraints_list,
                options={'maxiter': self.config.max_iterations}
            )
            
            if result.success:
                optimal_weights = result.x
                optimal_stakes = {
                    opp_id: str(weight) * bankroll * '0.5'  # Use 50% of bankroll
                    for opp_id, weight in zip(data.keys(), optimal_weights)
                }
                total_stake = sum(optimal_stakes.values())
                
                # Calculate metrics
                expected_return = sum(
                    stake * data[opp_id]['expected_return']
                    for opp_id, stake in optimal_stakes.items()
                )
                
                expected_variance = self._calculate_portfolio_variance(optimal_stakes, data)
                sharpe_ratio = self._calculate_sharpe_ratio(expected_return, expected_variance)
                
                return OptimizationResult(
                    optimal_stakes=optimal_stakes,
                    total_stake=total_stake,
                    expected_return=expected_return,
                    expected_variance=expected_variance,
                    expected_sharpe_ratio=sharpe_ratio,
                    constraint_violations=[],
                    optimization_status="success",
                    iterations_used=result.nit,
                    objective_value=-result.fun,  # Convert back to positive Sharpe
                    portfolio_metrics={'optimization_result': result},
                    rebalancing_required=True,
                    transaction_costs='0'
                )
            else:
                raise optimize.OptimizeError("Optimization failed to converge")
                
        except Exception as e:
            self.logger.warning(f"Maximum Sharpe optimization failed: {str(e)}")
            # Fallback to equal weights
            equal_weight = '1' / len(data)
            optimal_stakes = {
                opp_id: equal_weight * bankroll * '0.5'
                for opp_id in data.keys()
            }
            total_stake = sum(optimal_stakes.values())
            
            return self._create_fallback_result(optimal_stakes, data, "maximum_sharpe_fallback")
    
    def _optimize_minimum_variance(
        self,
        data: Dict,
        bankroll: Decimal,
        constraints: ConstraintSet
    ) -> OptimizationResult:
        """Optimize for minimum variance."""
        num_assets = len(data)
        
        def objective(weights):
            """Objective function to minimize (portfolio variance)."""
            weights = np.array(weights)
            variances = np.array([float(data[opp_id]['variance']) for opp_id in data.keys()])
            
            portfolio_variance = np.sum(weights ** 2 * variances)  # Simplified
            return portfolio_variance
        
        # Constraints and bounds
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},  # Weights sum to 1
        ]
        
        bounds = [(0, 1) for _ in range(num_assets)]
        
        # Initial guess
        x0 = np.array([1.0 / num_assets] * num_assets)
        
        try:
            result = optimize.minimize(
                objective, x0, method='SLSQP',
                bounds=bounds, constraints=constraints_list,
                options={'maxiter': self.config.max_iterations}
            )
            
            if result.success:
                optimal_weights = result.x
                optimal_stakes = {
                    opp_id: str(weight) * bankroll * '0.5'
                    for opp_id, weight in zip(data.keys(), optimal_weights)
                }
                total_stake = sum(optimal_stakes.values())
                
                expected_return = sum(
                    stake * data[opp_id]['expected_return']
                    for opp_id, stake in optimal_stakes.items()
                )
                
                expected_variance = self._calculate_portfolio_variance(optimal_stakes, data)
                sharpe_ratio = self._calculate_sharpe_ratio(expected_return, expected_variance)
                
                return OptimizationResult(
                    optimal_stakes=optimal_stakes,
                    total_stake=total_stake,
                    expected_return=expected_return,
                    expected_variance=expected_variance,
                    expected_sharpe_ratio=sharpe_ratio,
                    constraint_violations=[],
                    optimization_status="success",
                    iterations_used=result.nit,
                    objective_value=result.fun,
                    portfolio_metrics={'min_variance': True},
                    rebalancing_required=True,
                    transaction_costs='0'
                )
            else:
                raise optimize.OptimizeError("Optimization failed to converge")
                
        except Exception as e:
            self.logger.warning(f"Minimum variance optimization failed: {str(e)}")
            # Fallback to equal weights
            equal_weight = '1' / len(data)
            optimal_stakes = {
                opp_id: equal_weight * bankroll * '0.5'
                for opp_id in data.keys()
            }
            total_stake = sum(optimal_stakes.values())
            
            return self._create_fallback_result(optimal_stakes, data, "minimum_variance_fallback")
    
    def _optimize_maximum_utility(
        self,
        data: Dict,
        bankroll: Decimal,
        constraints: ConstraintSet
    ) -> OptimizationResult:
        """Optimize using utility function."""
        # Use logarithmic utility function by default
        risk_aversion = '0.5'  # Risk aversion parameter
        
        def utility_function(weights):
            """Calculate utility of portfolio."""
            weights = np.array(weights)
            
            returns = np.array([float(data[opp_id]['expected_return']) for opp_id in data.keys()])
            variances = np.array([float(data[opp_id]['variance']) for opp_id in data.keys()])
            
            portfolio_return = np.sum(weights * returns)
            portfolio_variance = np.sum(weights ** 2 * variances)
            
            # Logarithmic utility: U = E[R] - 0.5 * risk_aversion * Var[R]
            utility = portfolio_return - 0.5 * float(risk_aversion) * portfolio_variance
            return -utility  # Minimize negative utility
        
        # Constraints and bounds
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},
        ]
        
        bounds = [(0, 1) for _ in range(len(data))]
        x0 = np.array([1.0 / len(data)] * len(data))
        
        try:
            result = optimize.minimize(
                utility_function, x0, method='SLSQP',
                bounds=bounds, constraints=constraints_list,
                options={'maxiter': self.config.max_iterations}
            )
            
            if result.success:
                optimal_weights = result.x
                optimal_stakes = {
                    opp_id: str(weight) * bankroll * '0.5'
                    for opp_id, weight in zip(data.keys(), optimal_weights)
                }
                total_stake = sum(optimal_stakes.values())
                
                expected_return = sum(
                    stake * data[opp_id]['expected_return']
                    for opp_id, stake in optimal_stakes.items()
                )
                
                expected_variance = self._calculate_portfolio_variance(optimal_stakes, data)
                sharpe_ratio = self._calculate_sharpe_ratio(expected_return, expected_variance)
                
                return OptimizationResult(
                    optimal_stakes=optimal_stakes,
                    total_stake=total_stake,
                    expected_return=expected_return,
                    expected_variance=expected_variance,
                    expected_sharpe_ratio=sharpe_ratio,
                    constraint_violations=[],
                    optimization_status="success",
                    iterations_used=result.nit,
                    objective_value=-result.fun,  # Convert back to positive utility
                    portfolio_metrics={'utility_function': 'logarithmic'},
                    rebalancing_required=True,
                    transaction_costs='0'
                )
            else:
                raise optimize.OptimizeError("Utility optimization failed to converge")
                
        except Exception as e:
            self.logger.warning(f"Maximum utility optimization failed: {str(e)}")
            # Fallback to equal weights
            equal_weight = '1' / len(data)
            optimal_stakes = {
                opp_id: equal_weight * bankroll * '0.5'
                for opp_id in data.keys()
            }
            total_stake = sum(optimal_stakes.values())
            
            return self._create_fallback_result(optimal_stakes, data, "maximum_utility_fallback")
    
    def _create_fallback_result(
        self,
        optimal_stakes: Dict[str, Decimal],
        data: Dict,
        status: str
    ) -> OptimizationResult:
        """Create a fallback optimization result."""
        total_stake = sum(optimal_stakes.values())
        
        expected_return = sum(
            stake * data[opp_id]['expected_return']
            for opp_id, stake in optimal_stakes.items()
        )
        
        expected_variance = self._calculate_portfolio_variance(optimal_stakes, data)
        sharpe_ratio = self._calculate_sharpe_ratio(expected_return, expected_variance)
        
        return OptimizationResult(
            optimal_stakes=optimal_stakes,
            total_stake=total_stake,
            expected_return=expected_return,
            expected_variance=expected_variance,
            expected_sharpe_ratio=sharpe_ratio,
            constraint_violations=["fallback_used"],
            optimization_status=status,
            iterations_used=1,
            objective_value=expected_return,
            portfolio_metrics={'fallback': True},
            rebalancing_required=True,
            transaction_costs='0'
        )
    
    # Helper methods
    def _setup_logger(self):
        """Setup logging for the optimizer."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        return logger
    
    def _validate_opportunities(self, opportunities: List[Dict], bankroll: Decimal):
        """Validate optimization inputs."""
        if bankroll <= 0:
            raise ValueError("Bankroll must be positive")
        
        if not opportunities:
            raise ValueError("At least one opportunity required")
        
        for opp in opportunities:
            required_keys = ['id', 'win_probability', 'odds']
            if not all(key in opp for key in required_keys):
                raise ValueError("Each opportunity must have id, win_probability, and odds")
    
    def _prepare_optimization_data(self, opportunities: List[Dict], bankroll: Decimal) -> Dict:
        """Prepare data for optimization."""
        data = {}
        
        for opp in opportunities:
            opp_id = opp['id']
            prob = str(opp['win_probability'])
            odds = str(opp['odds'])
            
            # Calculate basic metrics
            expected_return = prob * (odds - '1') - ('1' - prob)
            variance = prob * (odds - '1') ** 2 + ('1' - prob)
            
            data[opp_id] = {
                'win_probability': prob,
                'odds': odds,
                'expected_return': expected_return,
                'variance': variance,
                'win_rate': prob,
                'avg_win': odds - '1',
                'avg_loss': '1',
                'confidence': opp.get('confidence', '1'),
                'correlation': opp.get('correlation', '0')
            }
        
        return data
    
    def _calculate_portfolio_variance(self, stakes: Dict[str, Decimal], data: Dict) -> Decimal:
        """Calculate portfolio variance (simplified)."""
        total_variance = '0'
        
        for opp_id, stake in stakes.items():
            weight = stake / sum(stakes.values()) if sum(stakes.values()) > 0 else '0'
            total_variance += weight ** 2 * data[opp_id]['variance']
        
        return total_variance
    
    def _calculate_sharpe_ratio(self, expected_return: Decimal, variance: Decimal) -> Decimal:
        """Calculate Sharpe ratio."""
        if variance <= 0:
            return '0'
        
        volatility = math.sqrt(float(variance))
        excess_return = float(expected_return - self.config.risk_free_rate)
        
        return str(excess_return / volatility) if volatility > 0 else '0'
    
    def _check_constraints(self, stakes: Dict[str, Decimal], constraints: ConstraintSet) -> List[str]:
        """Check if stakes satisfy all constraints."""
        violations = []
        total_stake = sum(stakes.values())
        
        # Check max position size
        if constraints.max_position_size:
            for stake in stakes.values():
                if stake > constraints.max_position_size:
                    violations.append(f"Position size {stake} exceeds max {constraints.max_position_size}")
        
        # Check total exposure
        if constraints.total_exposure_limit and total_stake > constraints.total_exposure_limit:
            violations.append(f"Total exposure {total_stake} exceeds limit {constraints.total_exposure_limit}")
        
        # Check minimum position size
        if constraints.min_position_size:
            for opp_id, stake in stakes.items():
                if stake < constraints.min_position_size and stake > 0:
                    violations.append(f"Position {opp_id} below minimum {constraints.min_position_size}")
        
        return violations
    
    def _calculate_transaction_costs(self, stakes: Dict[str, Decimal]) -> Decimal:
        """Calculate total transaction costs."""
        total_stake = sum(stakes.values())
        return total_stake * self.config.transaction_cost_rate
    
    def _select_best_strategy(self, strategy_results: Dict[OptimizationStrategy, OptimizationResult]) -> Tuple[OptimizationStrategy, Decimal]:
        """Select the best strategy based on objective value."""
        best_strategy = None
        best_objective = '-inf'
        
        for strategy, result in strategy_results.items():
            if result.objective_value > best_objective:
                best_strategy = strategy
                best_objective = result.objective_value
        
        return best_strategy, best_objective
    
    def _create_risk_adjusted_ranking(self, strategy_results: Dict[OptimizationStrategy, OptimizationResult]) -> List[Tuple[OptimizationStrategy, Decimal]]:
        """Create risk-adjusted ranking of strategies."""
        ranking = []
        
        for strategy, result in strategy_results.items():
            # Risk-adjusted score combines return and risk metrics
            return_score = float(result.expected_return)
            risk_penalty = float(result.expected_variance) * 10  # Penalize high variance
            risk_adjusted_score = return_score - risk_penalty
            
            ranking.append((strategy, str(risk_adjusted_score)))
        
        # Sort by risk-adjusted score
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking
    
    def _generate_strategy_recommendation(
        self,
        strategy_results: Dict[OptimizationStrategy, OptimizationResult],
        risk_adjusted_ranking: List[Tuple[OptimizationStrategy, Decimal]]
    ) -> str:
        """Generate strategy recommendation."""
        if not risk_adjusted_ranking:
            return "No strategies available for comparison"
        
        best_strategy, best_score = risk_adjusted_ranking[0]
        
        # Analyze strategy characteristics
        sharpe_ratios = {
            strategy: result.expected_sharpe_ratio
            for strategy, result in strategy_results.items()
        }
        
        highest_sharpe = max(sharpe_ratios.values())
        lowest_variance = min(result.expected_variance for result in strategy_results.values())
        
        recommendation = f"Recommended strategy: {best_strategy.value}\n"
        recommendation += f"Risk-adjusted score: {best_score:.4f}\n\n"
        
        # Add context about alternatives
        recommendation += "Alternative considerations:\n"
        for strategy, score in risk_adjusted_ranking[1:3]:  # Show top 3
            result = strategy_results[strategy]
            recommendation += f"- {strategy.value}: Sharpe {result.expected_sharpe_ratio:.3f}, Return {result.expected_return:.3f}\n"
        
        return recommendation