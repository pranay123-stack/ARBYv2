"""
Specialized Arbitrage Executor

Advanced executor for arbitrage trades with sophisticated profit calculation,
stake distribution optimization, and risk validation. Provides specialized
execution capabilities for arbitrage-specific scenarios.
"""

import asyncio
import logging
import time
import math
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid
import json
import threading
from decimal import Decimal, ROUND_HALF_UP
from contextlib import asynccontextmanager

from ..storage.models import ArbitrageOpportunity, ArbitrageLeg, OrderType, ExecutionMode


class StakeDistributionStrategy(str, Enum):
    """Stake distribution strategies."""
    EQUAL_PERCENTAGE = "equal_percentage"  # Equal percentage allocation
    ODDS_WEIGHTED = "odds_weighted"  # Weight by odds
    PROFIT_MAXIMIZING = "profit_maximizing"  # Maximize profit
    RISK_MINIMIZING = "risk_minimizing"  # Minimize risk
    DYNAMIC = "dynamic"  # Dynamic based on conditions
    KELLY_OPTIMAL = "kelly_optimal"  # Kelly criterion based


class OddsMovementType(str, Enum):
    """Types of odds movements."""
    IMPROVEMENT = "improvement"  # Odds improved
    DETERIORATION = "deterioration"  # Odds deteriorated
    STABLE = "stable"  # No significant change
    ERROR = "error"  # Odds error detected


class ExecutionResult(str, Enum):
    """Execution result statuses."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ODDS_CHANGED = "odds_changed"
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"
    BOOKMAKER_ERROR = "bookmaker_error"


@dataclass
class StakeAllocation:
    """Individual stake allocation for a leg."""
    leg_id: str
    bookmaker: str
    selection: str
    
    # Calculated allocations
    stake_amount: float
    stake_percentage: float
    
    # Odds information
    original_odds: float
    current_odds: float
    odds_movement: OddsMovementType
    
    # Expected outcomes
    expected_return: float
    profit_amount: float
    profit_margin: float
    
    # Validation
    within_limits: bool = True
    liquidity_checked: bool = False
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class ArbitrageCalculation:
    """Comprehensive arbitrage calculation results."""
    opportunity_id: str
    
    # Basic calculations
    total_stake: float
    total_potential_return: float
    gross_profit: float
    profit_margin: float
    
    # Stake distribution
    stake_allocations: List[StakeAllocation] = field(default_factory=list)
    distribution_strategy: StakeDistributionStrategy
    
    # Optimization results
    optimal_stake_distribution: List[float] = field(default_factory=list)
    expected_profit_variance: float = 0.0
    risk_adjusted_return: float = 0.0
    
    # Validation results
    calculation_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Performance metrics
    calculation_time_ms: float = 0.0
    optimization_iterations: int = 0
    
    # Metadata
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LegExecutionPlan:
    """Execution plan for a single leg."""
    leg_id: str
    bookmaker: str
    selection: str
    
    # Execution parameters
    order_type: OrderType
    target_odds: float
    actual_odds: Optional[float] = None
    
    # Stake information
    stake_amount: float
    stake_percentage: float
    
    # Timing
    execution_timeout: float = 10.0
    retry_attempts: int = 2
    
    # Validation checks
    pre_execution_checks: List[str] = field(default_factory=list)
    post_execution_checks: List[str] = field(default_factory=list)
    
    # Fallback options
    fallback_bookmakers: List[str] = field(default_factory=list)
    alternative_selections: List[str] = field(default_factory=list)
    
    # Monitoring
    enable_odds_monitoring: bool = True
    odds_monitoring_interval: float = 0.5  # seconds
    max_odds_deviation: float = 0.02  # 2% deviation allowed


@dataclass
class ArbitrageExecutionConfig:
    """Configuration for arbitrage execution."""
    # Calculation settings
    default_distribution_strategy: StakeDistributionStrategy = StakeDistributionStrategy.EQUAL_PERCENTAGE
    enable_kelly_optimization: bool = True
    enable_dynamic_distribution: bool = True
    calculation_precision: int = 2  # decimal places
    
    # Stake validation
    min_stake_amount: float = 1.0
    max_stake_amount: float = 10000.0
    stake_precision: float = 0.01
    enable_stake_rounding: bool = True
    
    # Odds validation
    max_odds_deviation: float = 0.02  # 2% allowed deviation
    odds_monitoring_duration: float = 5.0  # seconds
    odds_change_threshold: float = 0.001  # 0.1% change threshold
    
    # Risk validation
    enable_risk_validation: bool = True
    max_profit_variance: float = 0.05  # 5% variance allowed
    min_profit_margin: float = 0.005  # 0.5% minimum profit margin
    
    # Execution settings
    default_leg_timeout: float = 10.0
    default_retry_attempts: int = 3
    enable_parallel_legs: bool = True
    
    # Liquidity validation
    enable_liquidity_check: bool = True
    liquidity_buffer: float = 1.1  # 10% buffer
    min_liquidity_ratio: float = 1.2  # 1.2x stake requirement
    
    # Performance settings
    max_calculation_time_ms: float = 1000.0
    cache_calculations: bool = True
    cache_ttl: float = 300.0  # 5 minutes
    
    # Safety settings
    enable_emergency_stops: bool = True
    max_concurrent_executions: int = 5
    enable_audit_logging: bool = True


class ArbitrageExecutor:
    """
    Specialized Arbitrage Executor
    
    Provides sophisticated arbitrage execution capabilities including:
    - Advanced profit calculation and optimization
    - Intelligent stake distribution strategies
    - Comprehensive risk validation
    - Real-time odds monitoring and adaptation
    - Liquidity assessment and validation
    - Emergency stop mechanisms
    """
    
    def __init__(self, config: Optional[ArbitrageExecutionConfig] = None):
        """
        Initialize the arbitrage executor.
        
        Args:
            config: Arbitrage execution configuration
        """
        self.config = config or ArbitrageExecutionConfig()
        self.logger = logging.getLogger(__name__)
        
        # Calculation caching
        self._calculation_cache: Dict[str, Tuple[ArbitrageCalculation, datetime]] = {}
        self._cache_lock = threading.RLock()
        
        # Odds monitoring
        self._active_odds_monitors: Dict[str, asyncio.Task] = {}
        self._odds_data: Dict[str, Dict[str, Any]] = {}
        self._monitoring_lock = asyncio.Lock()
        
        # Execution tracking
        self._active_executions: Dict[str, Dict[str, Any]] = {}
        self._execution_lock = asyncio.Lock()
        
        # Performance tracking
        self._performance_stats = {
            'total_calculations': 0,
            'successful_calculations': 0,
            'failed_calculations': 0,
            'average_calculation_time_ms': 0.0,
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time_ms': 0.0,
            'cache_hit_rate': 0.0
        }
        self._stats_lock = threading.RLock()
        
        # Safety mechanisms
        self._emergency_stop = False
        self._emergency_stop_lock = threading.RLock()
        
        self.logger.info("Arbitrage Executor initialized successfully")
    
    async def calculate_arbitrage(
        self,
        opportunity: ArbitrageOpportunity,
        strategy: Optional[StakeDistributionStrategy] = None,
        total_stake: Optional[float] = None
    ) -> ArbitrageCalculation:
        """
        Calculate arbitrage with sophisticated stake distribution.
        
        Args:
            opportunity: The arbitrage opportunity
            strategy: Stake distribution strategy
            total_stake: Total stake amount
            
        Returns:
            ArbitrageCalculation: Comprehensive calculation results
        """
        start_time = time.time()
        strategy = strategy or self.config.default_distribution_strategy
        
        self.logger.debug(f"Calculating arbitrage for opportunity {opportunity.id} using {strategy.value}")
        
        try:
            # Check cache first
            cache_key = f"{opportunity.id}_{strategy.value}_{total_stake}"
            cached_result = await self._get_cached_calculation(cache_key)
            if cached_result:
                self.logger.debug(f"Using cached calculation for opportunity {opportunity.id}")
                return cached_result
            
            # Validate opportunity
            validation_errors = await self._validate_opportunity(opportunity)
            if validation_errors:
                return ArbitrageCalculation(
                    opportunity_id=str(opportunity.id),
                    total_stake=total_stake or 0.0,
                    total_potential_return=0.0,
                    gross_profit=0.0,
                    profit_margin=0.0,
                    distribution_strategy=strategy,
                    calculation_valid=False,
                    validation_errors=validation_errors,
                    calculation_time_ms=0.0
                )
            
            # Set total stake
            stake_amount = total_stake or float(opportunity.total_stake)
            
            # Calculate optimal distribution
            stake_distribution = await self._calculate_stake_distribution(
                opportunity, strategy, stake_amount
            )
            
            # Create stake allocations
            stake_allocations = await self._create_stake_allocations(
                opportunity, stake_distribution, strategy
            )
            
            # Calculate comprehensive metrics
            calculation = ArbitrageCalculation(
                opportunity_id=str(opportunity.id),
                total_stake=stake_amount,
                total_potential_return=sum(alloc.expected_return for alloc in stake_allocations),
                gross_profit=sum(alloc.profit_amount for alloc in stake_allocations),
                profit_margin=float(opportunity.profit_margin),
                stake_allocations=stake_allocations,
                distribution_strategy=strategy,
                optimal_stake_distribution=stake_distribution,
                calculation_time_ms=(time.time() - start_time) * 1000
            )
            
            # Perform optimization
            if strategy == StakeDistributionStrategy.KELLY_OPTIMAL and self.config.enable_kelly_optimization:
                calculation = await self._apply_kelly_optimization(calculation, opportunity)
            elif strategy == StakeDistributionStrategy.DYNAMIC and self.config.enable_dynamic_distribution:
                calculation = await self._apply_dynamic_optimization(calculation, opportunity)
            
            # Validate final calculation
            calculation.validation_errors.extend(await self._validate_calculation(calculation))
            calculation.calculation_valid = len(calculation.validation_errors) == 0
            
            # Cache result
            if self.config.cache_calculations:
                await self._cache_calculation(cache_key, calculation)
            
            # Update statistics
            with self._stats_lock:
                self._performance_stats['total_calculations'] += 1
                if calculation.calculation_valid:
                    self._performance_stats['successful_calculations'] += 1
                else:
                    self._performance_stats['failed_calculations'] += 1
                
                # Update average calculation time
                total_calcs = self._performance_stats['total_calculations']
                current_avg = self._performance_stats['average_calculation_time_ms']
                self._performance_stats['average_calculation_time_ms'] = (
                    (current_avg * (total_calcs - 1) + calculation.calculation_time_ms) / total_calcs
                )
            
            return calculation
            
        except Exception as e:
            self.logger.error(f"Arbitrage calculation failed: {str(e)}")
            return ArbitrageCalculation(
                opportunity_id=str(opportunity.id),
                total_stake=stake_amount if 'stake_amount' in locals() else 0.0,
                total_potential_return=0.0,
                gross_profit=0.0,
                profit_margin=0.0,
                distribution_strategy=strategy,
                calculation_valid=False,
                validation_errors=[f"Calculation error: {str(e)}"],
                calculation_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _validate_opportunity(self, opportunity: ArbitrageOpportunity) -> List[str]:
        """Validate opportunity data for calculation."""
        
        errors = []
        
        # Basic validation
        if not opportunity.legs or len(opportunity.legs) < 2:
            errors.append("Opportunity must have at least 2 legs")
        
        if float(opportunity.profit_margin) <= 0:
            errors.append("Profit margin must be positive")
        
        # Leg validation
        for i, leg in enumerate(opportunity.legs):
            if not leg.bookmaker:
                errors.append(f"Leg {i+1} missing bookmaker")
            if not leg.selection:
                errors.append(f"Leg {i+1} missing selection")
            if float(leg.odds) <= 1.0:
                errors.append(f"Leg {i+1} invalid odds: {leg.odds}")
        
        return errors
    
    async def _calculate_stake_distribution(
        self,
        opportunity: ArbitrageOpportunity,
        strategy: StakeDistributionStrategy,
        total_stake: float
    ) -> List[float]:
        """Calculate optimal stake distribution."""
        
        legs = opportunity.legs
        leg_count = len(legs)
        
        if strategy == StakeDistributionStrategy.EQUAL_PERCENTAGE:
            # Equal percentage distribution
            return [total_stake / leg_count] * leg_count
        
        elif strategy == StakeDistributionStrategy.ODDS_WEIGHTED:
            # Weight by odds (inverse relationship)
            odds_values = [float(leg.odds) for leg in legs]
            total_inverse_odds = sum(1 / odds for odds in odds_values)
            return [total_stake / (odds * total_inverse_odds) for odds in odds_values]
        
        elif strategy == StakeDistributionStrategy.PROFIT_MAXIMIZING:
            # Distribute to maximize profit (favor higher odds)
            odds_values = [float(leg.odds) for leg in legs]
            max_odds = max(odds_values)
            weights = [(odds / max_odds) ** 2 for odds in odds_values]  # Square for emphasis
            total_weight = sum(weights)
            return [(weight / total_weight) * total_stake for weight in weights]
        
        elif strategy == StakeDistributionStrategy.RISK_MINIMIZING:
            # Distribute to minimize risk (favor lower odds)
            odds_values = [float(leg.odds) for leg in legs]
            min_odds = min(odds_values)
            weights = [1 / ((odds / min_odds) ** 2) for odds in odds_values]  # Inverse square
            total_weight = sum(weights)
            return [(weight / total_weight) * total_stake for weight in weights]
        
        else:
            # Default to equal distribution
            return [total_stake / leg_count] * leg_count
    
    async def _create_stake_allocations(
        self,
        opportunity: ArbitrageOpportunity,
        stake_distribution: List[float],
        strategy: StakeDistributionStrategy
    ) -> List[StakeAllocation]:
        """Create detailed stake allocations for each leg."""
        
        allocations = []
        total_stake = sum(stake_distribution)
        
        for i, (leg, stake_amount) in enumerate(zip(opportunity.legs, stake_distribution)):
            # Apply rounding if enabled
            if self.config.enable_stake_rounding:
                stake_amount = round(stake_amount, self.config.stake_precision)
            
            # Calculate metrics
            odds = float(leg.odds)
            expected_return = stake_amount * odds
            profit_amount = expected_return - stake_amount
            profit_margin = profit_amount / stake_amount if stake_amount > 0 else 0
            
            # Determine stake percentage
            stake_percentage = (stake_amount / total_stake * 100) if total_stake > 0 else 0
            
            allocation = StakeAllocation(
                leg_id=str(leg.id) if hasattr(leg, 'id') else f"leg_{i}",
                bookmaker=leg.bookmaker,
                selection=leg.selection,
                stake_amount=stake_amount,
                stake_percentage=stake_percentage,
                original_odds=odds,
                current_odds=odds,  # Will be updated by monitoring
                odds_movement=OddsMovementType.STABLE,
                expected_return=expected_return,
                profit_amount=profit_amount,
                profit_margin=profit_margin
            )
            
            allocations.append(allocation)
        
        return allocations
    
    async def _apply_kelly_optimization(
        self,
        calculation: ArbitrageCalculation,
        opportunity: ArbitrageOpportunity
    ) -> ArbitrageCalculation:
        """Apply Kelly criterion optimization."""
        
        # This is a simplified Kelly implementation
        # In practice, you'd need historical win rates and more sophisticated calculations
        
        legs = opportunity.legs
        odds_values = [float(leg.odds) for leg in legs]
        profit_margin = float(opportunity.profit_margin)
        
        # Kelly fraction calculation (simplified)
        # Kelly = (bp - q) / b
        # where b = odds - 1, p = probability of winning, q = probability of losing
        
        # Assume equal probability for all legs (this would be calculated from historical data)
        total_legs = len(legs)
        win_probability = 1.0 / total_legs  # Simplified assumption
        
        kelly_fractions = []
        for odds in odds_values:
            b = odds - 1  # net odds received
            p = win_probability
            q = 1 - p
            
            kelly_fraction = (b * p - q) / b
            kelly_fraction = max(0, kelly_fraction)  # Kelly can't be negative
            kelly_fractions.append(kelly_fraction)
        
        # Normalize Kelly fractions
        total_kelly = sum(kelly_fractions)
        if total_kelly > 0:
            normalized_fractions = [kf / total_kelly for kf in kelly_fractions]
            
            # Apply Kelly optimization to allocations
            for i, allocation in enumerate(calculation.stake_allocations):
                kelly_multiplier = normalized_fractions[i] * 2  # Conservative multiplier
                allocation.stake_amount *= kelly_multiplier
                allocation.stake_percentage *= kelly_multiplier
                
                # Recalculate expected outcomes
                allocation.expected_return = allocation.stake_amount * allocation.original_odds
                allocation.profit_amount = allocation.expected_return - allocation.stake_amount
                allocation.profit_margin = allocation.profit_amount / allocation.stake_amount
        
        return calculation
    
    async def _apply_dynamic_optimization(
        self,
        calculation: ArbitrageCalculation,
        opportunity: ArbitrageOpportunity
    ) -> ArbitrageCalculation:
        """Apply dynamic optimization based on conditions."""
        
        # Dynamic optimization factors
        liquidity_score = await self._assess_liquidity(opportunity)
        risk_score = await self._assess_risk(opportunity)
        market_conditions = await self._assess_market_conditions(opportunity)
        
        # Adjust stake distribution based on dynamic factors
        for i, allocation in enumerate(calculation.stake_allocations):
            # Get leg characteristics
            leg = opportunity.legs[i]
            bookmaker = leg.bookmaker
            
            # Adjust based on bookmaker reliability
            reliability_factor = await self._get_bookmaker_reliability_factor(bookmaker)
            
            # Adjust based on selection popularity
            popularity_factor = await self._get_selection_popularity_factor(leg.selection)
            
            # Apply adjustments
            dynamic_multiplier = (liquidity_score + reliability_factor + popularity_factor) / 3
            allocation.stake_amount *= dynamic_multiplier
            allocation.stake_percentage *= dynamic_multiplier
            
            # Recalculate outcomes
            allocation.expected_return = allocation.stake_amount * allocation.original_odds
            allocation.profit_amount = allocation.expected_return - allocation.stake_amount
            allocation.profit_margin = allocation.profit_amount / allocation.stake_amount
        
        return calculation
    
    async def _assess_liquidity(self, opportunity: ArbitrageOpportunity) -> float:
        """Assess liquidity conditions for the opportunity."""
        
        # Simplified liquidity assessment
        # In practice, this would check real market depth, betting limits, etc.
        
        leg_count = len(opportunity.legs)
        total_stake = float(opportunity.total_stake)
        
        # Higher leg count = better liquidity (more diversified)
        leg_factor = min(1.0, leg_count / 4.0)
        
        # Lower total stake = better liquidity
        stake_factor = max(0.1, 1.0 - (total_stake / 1000))
        
        return (leg_factor + stake_factor) / 2
    
    async def _assess_risk(self, opportunity: ArbitrageOpportunity) -> float:
        """Assess risk conditions for the opportunity."""
        
        # Simplified risk assessment
        profit_margin = float(opportunity.profit_margin)
        
        # Higher profit margin = higher risk
        profit_factor = max(0.1, 1.0 - (profit_margin / 0.1))
        
        # More legs = lower risk
        leg_count = len(opportunity.legs)
        leg_factor = min(1.0, leg_count / 3.0)
        
        return (profit_factor + leg_factor) / 2
    
    async def _assess_market_conditions(self, opportunity: ArbitrageOpportunity) -> float:
        """Assess overall market conditions."""
        
        # This would analyze market volatility, news events, etc.
        # For now, return a neutral score
        
        return 0.5
    
    async def _get_bookmaker_reliability_factor(self, bookmaker: str) -> float:
        """Get bookmaker reliability factor."""
        
        # Simplified reliability factors
        reliability_factors = {
            'Bet365': 0.9,
            'WilliamHill': 0.8,
            'DraftKings': 0.7,
            'FanDuel': 0.7,
            'Betfair': 0.85
        }
        
        return reliability_factors.get(bookmaker, 0.5)
    
    async def _get_selection_popularity_factor(self, selection: str) -> float:
        """Get selection popularity factor."""
        
        # This would analyze betting volume, public sentiment, etc.
        # For now, return neutral factor
        
        return 0.5
    
    async def _validate_calculation(self, calculation: ArbitrageCalculation) -> List[str]:
        """Validate the arbitrage calculation."""
        
        errors = []
        
        # Check calculation validity
        if calculation.total_stake <= 0:
            errors.append("Total stake must be positive")
        
        if calculation.gross_profit <= 0:
            errors.append("Gross profit must be positive")
        
        if calculation.profit_margin <= self.config.min_profit_margin:
            errors.append(f"Profit margin below minimum: {calculation.profit_margin:.4f}")
        
        # Check stake allocations
        total_allocated_stake = sum(alloc.stake_amount for alloc in calculation.stake_allocations)
        stake_difference = abs(total_allocated_stake - calculation.total_stake)
        
        if stake_difference > calculation.total_stake * 0.01:  # 1% tolerance
            errors.append(f"Stake allocation mismatch: {stake_difference:.2f}")
        
        # Check individual allocations
        for allocation in calculation.stake_allocations:
            if allocation.stake_amount < self.config.min_stake_amount:
                errors.append(f"Stake below minimum: {allocation.stake_amount} for {allocation.bookmaker}")
            
            if allocation.stake_amount > self.config.max_stake_amount:
                errors.append(f"Stake above maximum: {allocation.stake_amount} for {allocation.bookmaker}")
        
        return errors
    
    async def prepare_legs(
        self,
        legs: List[ArbitrageLeg],
        execution_context: Any,
        validation_result: Dict[str, Any]
    ) -> List[LegExecutionPlan]:
        """Prepare legs for execution with detailed planning."""
        
        self.logger.debug(f"Preparing {len(legs)} legs for execution")
        
        execution_plans = []
        
        for i, leg in enumerate(legs):
            # Get stake allocation from validation result
            stake_amount = self._get_stake_from_validation(validation_result, leg, i)
            
            # Create execution plan
            plan = LegExecutionPlan(
                leg_id=str(leg.id) if hasattr(leg, 'id') else f"leg_{i}",
                bookmaker=leg.bookmaker,
                selection=leg.selection,
                order_type=OrderType.MARKET,  # Default to market orders
                target_odds=float(leg.odds),
                stake_amount=stake_amount,
                stake_percentage=(stake_amount / sum(
                    self._get_stake_from_validation(validation_result, l, j)
                    for j, l in enumerate(legs)
                )) * 100
            )
            
            # Add pre-execution checks
            plan.pre_execution_checks = [
                "odds_verification",
                "stake_limit_check",
                "liquidity_check",
                "bookmaker_availability"
            ]
            
            # Add post-execution checks
            plan.post_execution_checks = [
                "bet_confirmation",
                "odds_verification",
                "stake_verification",
                "payout_calculation"
            ]
            
            # Add fallback options
            plan.fallback_bookmakers = await self._get_fallback_bookmakers(leg.bookmaker)
            plan.alternative_selections = await self._get_alternative_selections(leg.selection)
            
            execution_plans.append(plan)
        
        return execution_plans
    
    def _get_stake_from_validation(
        self,
        validation_result: Dict[str, Any],
        leg: ArbitrageLeg,
        leg_index: int
    ) -> float:
        """Extract stake amount for a leg from validation results."""
        
        # This would extract stakes from the validation result
        # For now, use a simple calculation based on leg odds
        
        total_stake = validation_result.get('total_stake', 100.0)
        legs = validation_result.get('legs', [])
        
        if legs and leg_index < len(legs):
            return legs[leg_index].get('stake', total_stake / len(legs))
        
        # Fallback: equal distribution
        return total_stake / len(legs) if hasattr(leg, '__len__') else total_stake
    
    async def _get_fallback_bookmakers(self, bookmaker: str) -> List[str]:
        """Get fallback bookmakers for a given bookmaker."""
        
        # This would maintain a database of bookmaker alternatives
        fallback_map = {
            'DraftKings': ['FanDuel', 'BetMGM'],
            'FanDuel': ['DraftKings', 'BetMGM'],
            'Bet365': ['WilliamHill', 'Betfair'],
            'WilliamHill': ['Bet365', 'Betfair']
        }
        
        return fallback_map.get(bookmaker, [])
    
    async def _get_alternative_selections(self, selection: str) -> List[str]:
        """Get alternative selections for a given selection."""
        
        # This would maintain a database of equivalent selections
        # For now, return empty list
        
        return []
    
    async def execute_leg(
        self,
        leg: ArbitrageLeg,
        execution_context: Any
    ) -> Dict[str, Any]:
        """Execute a single leg with comprehensive validation and monitoring."""
        
        start_time = time.time()
        
        self.logger.info(f"Executing leg: {leg.bookmaker} - {leg.selection}")
        
        try:
            # Pre-execution validation
            validation_result = await self._validate_leg_execution(leg, execution_context)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': 'Pre-execution validation failed',
                    'details': validation_result,
                    'execution_time_ms': (time.time() - start_time) * 1000
                }
            
            # Monitor odds during execution
            odds_monitor_task = None
            if execution_context.order_type == OrderType.MARKET:
                odds_monitor_task = asyncio.create_task(
                    self._monitor_odds_during_execution(leg, execution_context)
                )
            
            # Execute the bet
            execution_result = await self._execute_bet(leg, execution_context)
            
            # Cancel odds monitoring
            if odds_monitor_task:
                odds_monitor_task.cancel()
                try:
                    await odds_monitor_task
                except asyncio.CancelledError:
                    pass
            
            # Post-execution validation
            if execution_result['success']:
                validation_result = await self._validate_bet_execution(leg, execution_result)
                execution_result['post_validation'] = validation_result
            
            execution_result['execution_time_ms'] = (time.time() - start_time) * 1000
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Leg execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'execution_time_ms': (time.time() - start_time) * 1000
            }
    
    async def _validate_leg_execution(self, leg: ArbitrageLeg, context: Any) -> Dict[str, Any]:
        """Validate leg before execution."""
        
        validation_result = {
            'valid': True,
            'checks': [],
            'warnings': [],
            'errors': []
        }
        
        # Check bookmaker availability
        bookmaker_available = await self._check_bookmaker_availability(leg.bookmaker)
        validation_result['checks'].append(('bookmaker_available', bookmaker_available))
        if not bookmaker_available:
            validation_result['errors'].append(f"Bookmaker {leg.bookmaker} not available")
            validation_result['valid'] = False
        
        # Check odds validity
        odds_valid = 1.01 <= float(leg.odds) <= 100.0
        validation_result['checks'].append(('odds_valid', odds_valid))
        if not odds_valid:
            validation_result['errors'].append(f"Invalid odds: {leg.odds}")
            validation_result['valid'] = False
        
        # Check stake limits
        stake_amount = getattr(context, 'stake_amount', 0)
        stake_valid = self.config.min_stake_amount <= stake_amount <= self.config.max_stake_amount
        validation_result['checks'].append(('stake_valid', stake_valid))
        if not stake_valid:
            validation_result['errors'].append(f"Stake {stake_amount} outside limits")
            validation_result['valid'] = False
        
        # Check liquidity
        if self.config.enable_liquidity_check:
            liquidity_adequate = await self._check_liquidity(leg, stake_amount)
            validation_result['checks'].append(('liquidity_adequate', liquidity_adequate))
            if not liquidity_adequate:
                validation_result['warnings'].append(f"Insufficient liquidity for {stake_amount}")
        
        return validation_result
    
    async def _check_bookmaker_availability(self, bookmaker: str) -> bool:
        """Check if bookmaker is available for betting."""
        
        # This would check bookmaker status, API availability, etc.
        # For now, assume all configured bookmakers are available
        
        available_bookmakers = ['Bet365', 'WilliamHill', 'DraftKings', 'FanDuel', 'Betfair']
        return bookmaker in available_bookmakers
    
    async def _check_liquidity(self, leg: ArbitrageLeg, stake_amount: float) -> bool:
        """Check if there's sufficient liquidity for the stake."""
        
        # This would check real market depth and betting limits
        # For now, use a simple heuristic
        
        estimated_liquidity = 1000.0  # Estimated available liquidity
        return stake_amount <= estimated_liquidity * self.config.liquidity_buffer
    
    async def _monitor_odds_during_execution(
        self,
        leg: ArbitrageLeg,
        context: Any
    ) -> Dict[str, Any]:
        """Monitor odds changes during execution."""
        
        monitoring_data = {
            'leg_id': str(leg.id) if hasattr(leg, 'id') else 'unknown',
            'original_odds': float(leg.odds),
            'odds_changes': [],
            'final_odds': None,
            'significant_change': False
        }
        
        target_odds = float(leg.odds)
        max_deviation = self.config.max_odds_deviation
        
        try:
            # Monitor for specified duration
            monitoring_end = time.time() + self.config.odds_monitoring_duration
            
            while time.time() < monitoring_end:
                # Get current odds (this would be a real API call)
                current_odds = await self._get_current_odds(leg.bookmaker, leg.selection)
                
                if current_odds:
                    deviation = abs(current_odds - target_odds) / target_odds
                    
                    monitoring_data['odds_changes'].append({
                        'timestamp': datetime.utcnow().isoformat(),
                        'odds': current_odds,
                        'deviation': deviation
                    })
                    
                    if deviation > max_deviation:
                        monitoring_data['significant_change'] = True
                        monitoring_data['final_odds'] = current_odds
                        break
                
                await asyncio.sleep(self.config.odds_monitoring_interval)
            
            monitoring_data['final_odds'] = monitoring_data.get('final_odds') or target_odds
            
        except asyncio.CancelledError:
            self.logger.debug(f"Odds monitoring cancelled for {leg.bookmaker}")
        
        return monitoring_data
    
    async def _get_current_odds(self, bookmaker: str, selection: str) -> Optional[float]:
        """Get current odds for a selection from a bookmaker."""
        
        # This would make a real API call to get current odds
        # For now, simulate small random variations
        
        base_odds = 2.0  # Base odds (this would come from the actual leg)
        variation = (time.time() % 10) / 1000  # Small time-based variation
        
        return base_odds + variation
    
    async def _execute_bet(self, leg: ArbitrageLeg, context: Any) -> Dict[str, Any]:
        """Execute the actual bet placement."""
        
        # This would implement actual bet placement with bookmaker APIs
        # For now, simulate the execution
        
        execution_start = time.time()
        
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # Simulate success/failure (95% success rate)
        import random
        success = random.random() > 0.05
        
        if success:
            return {
                'success': True,
                'order_id': f"bet_{uuid.uuid4().hex[:8]}",
                'bookmaker': leg.bookmaker,
                'selection': leg.selection,
                'odds': float(leg.odds),
                'stake': context.stake_amount,
                'expected_return': context.stake_amount * float(leg.odds),
                'execution_time_ms': (time.time() - execution_start) * 1000,
                'placed_at': datetime.utcnow().isoformat()
            }
        else:
            return {
                'success': False,
                'error': 'Bookmaker API error',
                'bookmaker': leg.bookmaker,
                'selection': leg.selection,
                'execution_time_ms': (time.time() - execution_start) * 1000
            }
    
    async def _validate_bet_execution(self, leg: ArbitrageLeg, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the bet execution after placement."""
        
        validation_result = {
            'valid': True,
            'checks': [],
            'errors': [],
            'warnings': []
        }
        
        # Check if bet was confirmed
        bet_confirmed = 'order_id' in execution_result
        validation_result['checks'].append(('bet_confirmed', bet_confirmed))
        if not bet_confirmed:
            validation_result['errors'].append("Bet confirmation not received")
            validation_result['valid'] = False
        
        # Check if odds match
        expected_odds = float(leg.odds)
        actual_odds = execution_result.get('odds', expected_odds)
        odds_match = abs(actual_odds - expected_odds) / expected_odds <= self.config.max_odds_deviation
        validation_result['checks'].append(('odds_match', odds_match))
        if not odds_match:
            validation_result['warnings'].append(
                f"Odds changed from {expected_odds} to {actual_odds}"
            )
        
        # Check if stake matches
        expected_stake = getattr(leg, 'stake_amount', 0)
        actual_stake = execution_result.get('stake', 0)
        stake_match = abs(actual_stake - expected_stake) <= 0.01
        validation_result['checks'].append(('stake_match', stake_match))
        if not stake_match:
            validation_result['errors'].append(
                f"Stake mismatch: expected {expected_stake}, got {actual_stake}"
            )
            validation_result['valid'] = False
        
        return validation_result
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an outstanding order."""
        
        self.logger.info(f"Cancelling order {order_id}")
        
        try:
            # This would implement actual order cancellation
            # For now, simulate success
            
            await asyncio.sleep(0.1)  # Simulate API call
            
            self.logger.info(f"Order {order_id} cancelled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            return False
    
    async def _get_cached_calculation(self, cache_key: str) -> Optional[ArbitrageCalculation]:
        """Get cached calculation if available."""
        
        if not self.config.cache_calculations:
            return None
        
        with self._cache_lock:
            if cache_key in self._calculation_cache:
                calculation, timestamp = self._calculation_cache[cache_key]
                
                # Check if cache is still valid
                if (datetime.utcnow() - timestamp).total_seconds() < self.config.cache_ttl:
                    return calculation
                else:
                    # Remove expired cache
                    del self._calculation_cache[cache_key]
        
        return None
    
    async def _cache_calculation(self, cache_key: str, calculation: ArbitrageCalculation):
        """Cache calculation result."""
        
        if not self.config.cache_calculations:
            return
        
        with self._cache_lock:
            self._calculation_cache[cache_key] = (calculation, datetime.utcnow())
            
            # Clean old cache entries
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.config.cache_ttl)
            expired_keys = [
                key for key, (_, timestamp) in self._calculation_cache.items()
                if timestamp < cutoff_time
            ]
            for key in expired_keys:
                del self._calculation_cache[key]
    
    def set_emergency_stop(self, active: bool = True):
        """Activate or deactivate emergency stop."""
        
        with self._emergency_stop_lock:
            self._emergency_stop = active
            
            if active:
                self.logger.critical("EMERGENCY STOP ACTIVATED")
            else:
                self.logger.info("Emergency stop deactivated")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        
        with self._stats_lock:
            # Calculate cache hit rate
            total_requests = self._performance_stats['total_calculations']
            cache_hits = total_requests - self._performance_stats['failed_calculations']
            
            self._performance_stats.update({
                'cache_hit_rate': cache_hits / max(1, total_requests),
                'active_executions': len(self._active_executions),
                'emergency_stop_active': self._emergency_stop
            })
            
            return self._performance_stats.copy()
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an active execution."""
        
        async with self._execution_lock:
            return self._active_executions.get(execution_id)
    
    async def shutdown(self):
        """Graceful shutdown of the arbitrage executor."""
        
        self.logger.info("Shutting down Arbitrage Executor...")
        
        # Cancel all odds monitoring tasks
        for task in self._active_odds_monitors.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._active_odds_monitors:
            await asyncio.gather(*self._active_odds_monitors.values(), return_exceptions=True)
        
        # Deactivate emergency stop
        self.set_emergency_stop(False)
        
        self.logger.info("Arbitrage Executor shutdown complete")