"""
Multi-Leg Trade Execution Engine

Sophisticated execution engine for coordinated multi-bookmaker trades with atomic operations,
rollback capabilities, and comprehensive safety mechanisms. This is the core execution system
that orchestrates all trade executions with enterprise-grade reliability.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import uuid
import traceback
from contextlib import asynccontextmanager
import threading

from ..risk.pre_trade_validator import PreTradeValidator, PreTradeAnalysis
from ..risk.safety_pipeline import SafetyPipeline, SafetyResult, ValidationStatus, RiskLevel
from ..storage.models import ArbitrageOpportunity, ArbitrageLeg, TradeStatus, ExecutionMode, RiskTier
from .trade_coordinator import TradeCoordinator, CoordinationStrategy
from .execution_tracker import ExecutionTracker, TrackEvent
from .arbitrage_executor import ArbitrageExecutor


class ExecutionState(Enum):
    """Execution state machine states."""
    INITIATED = "initiated"
    VALIDATING = "validating"
    COORDINATING = "coordinating"
    EXECUTING = "executing"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ExecutionStrategy(Enum):
    """Multi-leg execution strategies."""
    ATOMIC = "atomic"  # All-or-nothing execution
    SEQUENTIAL = "sequential"  # Execute legs sequentially
    PARALLEL = "parallel"  # Execute legs in parallel
    ADAPTIVE = "adaptive"  # Choose strategy based on conditions
    TIMED = "timed"  # Timed execution with deadlines
    CONFIRMATION = "confirmation"  # Wait for confirmation between legs


class OrderType(Enum):
    """Supported order types."""
    MARKET = "market"  # Execute immediately at current odds
    LIMIT = "limit"  # Execute only if odds meet specified limit
    STOP = "stop"  # Stop-loss style order
    TRAILING = "trailing"  # Trailing stop order


class RollbackAction(Enum):
    """Types of rollback actions."""
    CANCEL = "cancel"  # Cancel unfilled orders
    HEDGE = "hedge"  # Hedge remaining positions
    LIQUIDATE = "liquidate"  # Liquidate all positions
    MANUAL = "manual"  # Manual intervention required


@dataclass
class ExecutionContext:
    """Execution context and metadata."""
    execution_id: str
    opportunity_id: str
    strategy: ExecutionStrategy
    order_type: OrderType
    execution_mode: ExecutionMode
    
    # Timing constraints
    max_execution_time: float = 30.0
    leg_timeout: float = 10.0
    confirmation_timeout: float = 5.0
    
    # Safety constraints
    max_attempts: int = 3
    require_all_confirmations: bool = True
    auto_rollback_on_failure: bool = True
    
    # Stake constraints
    total_stake: float = 0.0
    stake_distribution: List[float] = field(default_factory=list)
    
    # Rollback configuration
    rollback_actions: List[RollbackAction] = field(default_factory=list)
    rollback_timeout: float = 15.0
    
    # Monitoring
    enable_real_time_monitoring: bool = True
    monitoring_interval: float = 1.0
    
    # Created at
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutionResult:
    """Comprehensive execution result."""
    execution_id: str
    opportunity_id: str
    execution_state: ExecutionState
    
    # Timing information
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_duration: float = 0.0
    
    # Success metrics
    legs_attempted: int = 0
    legs_succeeded: int = 0
    legs_failed: int = 0
    legs_rolled_back: int = 0
    
    # Financial metrics
    total_stake_placed: float = 0.0
    total_potential_profit: float = 0.0
    realized_profit: float = 0.0
    execution_cost: float = 0.0
    
    # Risk metrics
    final_risk_score: float = 0.0
    risk_adjusted_return: float = 0.0
    max_drawdown: float = 0.0
    
    # Validation results
    pre_trade_validation: Optional[PreTradeAnalysis] = None
    safety_validation: Optional[SafetyResult] = None
    
    # Execution details
    leg_results: List[Dict[str, Any]] = field(default_factory=list)
    coordination_log: List[Dict[str, Any]] = field(default_factory=list)
    rollback_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Error information
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)


@dataclass
class ExecutionConfig:
    """Configuration for multi-leg execution."""
    # Global execution settings
    enable_atomic_execution: bool = True
    enable_parallel_execution: bool = True
    enable_rollback_mechanism: bool = True
    enable_real_time_monitoring: bool = True
    
    # Timing settings
    default_leg_timeout: float = 10.0
    default_execution_timeout: float = 30.0
    default_confirmation_timeout: float = 5.0
    max_execution_time: float = 120.0
    
    # Safety settings
    max_execution_attempts: int = 3
    require_safety_validation: bool = True
    require_pre_trade_validation: bool = True
    auto_rollback_on_timeout: bool = True
    
    # Coordination settings
    coordination_strategy: CoordinationStrategy = CoordinationStrategy.OPTIMIZED
    synchronization_tolerance: float = 0.5  # seconds
    
    # Monitoring settings
    monitoring_interval: float = 1.0
    track_all_events: bool = True
    enable_performance_tracking: bool = True
    
    # Performance settings
    max_concurrent_executions: int = 10
    enable_caching: bool = True
    cache_ttl: float = 300.0  # 5 minutes
    
    # Logging settings
    log_execution_details: bool = True
    log_performance_metrics: bool = True
    log_safety_events: bool = True


class MultiLegExecutor:
    """
    Sophisticated Multi-Leg Trade Execution Engine
    
    Provides atomic, coordinated execution across multiple bookmakers with:
    - Comprehensive safety validation
    - Atomic operations with rollback
    - Real-time monitoring and tracking
    - Adaptive execution strategies
    - Enterprise-grade error handling
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        """
        Initialize the multi-leg execution engine.
        
        Args:
            config: Execution configuration
        """
        self.config = config or ExecutionConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._pre_trade_validator = PreTradeValidator()
        self._safety_pipeline = SafetyPipeline()
        self._trade_coordinator = TradeCoordinator()
        self._execution_tracker = ExecutionTracker()
        self._arbitrage_executor = ArbitrageExecutor()
        
        # Execution management
        self._active_executions: Dict[str, ExecutionContext] = {}
        self._execution_locks = asyncio.Lock()
        self._execution_thread_pool = asyncio.Semaphore(self.config.max_concurrent_executions)
        
        # Performance tracking
        self._performance_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'rolled_back_executions': 0,
            'average_execution_time': 0.0,
            'execution_rate_per_hour': 0.0
        }
        
        # State management
        self._state_lock = threading.RLock()
        self._shutdown_event = asyncio.Event()
        
        self.logger.info("Multi-Leg Executor initialized successfully")
    
    async def execute_opportunity(
        self,
        opportunity: ArbitrageOpportunity,
        execution_strategy: ExecutionStrategy = ExecutionStrategy.ATOMIC,
        order_type: OrderType = OrderType.MARKET,
        execution_mode: ExecutionMode = ExecutionMode.AUTO_FULL,
        total_stake: Optional[float] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute an arbitrage opportunity with comprehensive safety checks.
        
        Args:
            opportunity: The arbitrage opportunity to execute
            execution_strategy: Strategy for multi-leg execution
            order_type: Order type (market, limit, etc.)
            execution_mode: Execution mode (manual, auto, etc.)
            total_stake: Total stake amount
            user_preferences: User-specific preferences
            
        Returns:
            ExecutionResult: Comprehensive execution result
        """
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        self.logger.info(f"Starting execution {execution_id} for opportunity {opportunity.id}")
        
        # Initialize execution context
        context = ExecutionContext(
            execution_id=execution_id,
            opportunity_id=str(opportunity.id),
            strategy=execution_strategy,
            order_type=order_type,
            execution_mode=execution_mode,
            total_stake=total_stake or float(opportunity.total_stake),
            stake_distribution=[float(leg.stake_percentage) for leg in opportunity.legs]
        )
        
        # Track execution start
        await self._execution_tracker.track_event(
            TrackEvent(
                execution_id=execution_id,
                event_type="execution_started",
                event_data={
                    'opportunity_id': str(opportunity.id),
                    'strategy': execution_strategy.value,
                    'order_type': order_type.value,
                    'total_stake': context.total_stake,
                    'legs_count': len(opportunity.legs)
                }
            )
        )
        
        async with self._execution_thread_pool:
            async with self._execution_locks:
                self._active_executions[execution_id] = context
                
                try:
                    # Update performance stats
                    self._performance_stats['total_executions'] += 1
                    
                    # Step 1: Comprehensive Validation
                    validation_result = await self._validate_opportunity(
                        opportunity, context, user_preferences
                    )
                    
                    if not validation_result.passed:
                        return await self._handle_validation_failure(
                            opportunity, context, validation_result, start_time
                        )
                    
                    # Step 2: Coordination Setup
                    await self._trade_coordinator.setup_coordination(
                        opportunity, context, validation_result
                    )
                    
                    # Step 3: Execute according to strategy
                    execution_result = await self._execute_by_strategy(
                        opportunity, context, validation_result
                    )
                    
                    # Step 4: Post-execution processing
                    final_result = await self._finalize_execution(
                        execution_result, context, start_time
                    )
                    
                    return final_result
                    
                except asyncio.TimeoutError:
                    self.logger.warning(f"Execution {execution_id} timed out")
                    return await self._handle_timeout(context, start_time)
                    
                except Exception as e:
                    self.logger.error(f"Execution {execution_id} failed: {str(e)}")
                    return await self._handle_execution_error(
                        context, start_time, str(e), traceback.format_exc()
                    )
                    
                finally:
                    # Cleanup
                    await self._cleanup_execution(execution_id)
    
    async def _validate_opportunity(
        self,
        opportunity: ArbitrageOpportunity,
        context: ExecutionContext,
        user_preferences: Optional[Dict[str, Any]]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Perform comprehensive opportunity validation."""
        
        self.logger.debug(f"Validating opportunity {opportunity.id} for execution {context.execution_id}")
        
        validation_results = {
            'pre_trade': None,
            'safety': None,
            'passed': False,
            'errors': [],
            'warnings': []
        }
        
        # Pre-trade validation
        if self.config.require_pre_trade_validation:
            try:
                opportunity_data = {
                    'id': str(opportunity.id),
                    'profit_margin': float(opportunity.profit_margin),
                    'legs': [
                        {
                            'bookmaker': leg.bookmaker,
                            'odds': float(leg.odds),
                            'stake': float(leg.stake_amount) if hasattr(leg, 'stake_amount') else 0,
                            'selection': leg.selection
                        }
                        for leg in opportunity.legs
                    ],
                    'sport': opportunity.sport.value if opportunity.sport else 'unknown',
                    'total_stake': float(opportunity.total_stake)
                }
                
                pre_trade_result = await self._pre_trade_validator.validate_advanced_checks(
                    opportunity_data, user_preferences
                )
                
                validation_results['pre_trade'] = pre_trade_result
                
                if not pre_trade_result['success']:
                    validation_results['errors'].extend(pre_trade_result.get('warnings', []))
                    
            except Exception as e:
                validation_results['errors'].append(f"Pre-trade validation failed: {str(e)}")
        
        # Safety validation
        if self.config.require_safety_validation:
            try:
                safety_result = await self._safety_pipeline.validate_opportunity(
                    {
                        'id': str(opportunity.id),
                        'profit_margin': float(opportunity.profit_margin),
                        'legs': [
                            {
                                'bookmaker': leg.bookmaker,
                                'odds': float(leg.odds),
                                'stake': float(leg.stake_amount) if hasattr(leg, 'stake_amount') else 0,
                                'selection': leg.selection
                            }
                            for leg in opportunity.legs
                        ],
                        'sport': opportunity.sport.value if opportunity.sport else 'unknown',
                        'risk_tier': opportunity.risk_tier.value
                    },
                    user_preferences
                )
                
                validation_results['safety'] = safety_result
                
                if safety_result.overall_status != ValidationStatus.PASSED:
                    validation_results['errors'].extend(safety_result.critical_issues)
                    
            except Exception as e:
                validation_results['errors'].append(f"Safety validation failed: {str(e)}")
        
        # Determine overall validation status
        validation_results['passed'] = len(validation_results['errors']) == 0
        
        # Track validation event
        await self._execution_tracker.track_event(
            TrackEvent(
                execution_id=context.execution_id,
                event_type="validation_completed",
                event_data={
                    'passed': validation_results['passed'],
                    'errors_count': len(validation_results['errors']),
                    'warnings_count': len(validation_results['warnings']),
                    'pre_trade_success': validation_results['pre_trade']['success'] if validation_results['pre_trade'] else None,
                    'safety_status': validation_results['safety'].overall_status.value if validation_results['safety'] else None
                }
            )
        )
        
        return validation_results
    
    async def _execute_by_strategy(
        self,
        opportunity: ArbitrageOpportunity,
        context: ExecutionContext,
        validation_result: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute opportunity using the specified strategy."""
        
        strategy_map = {
            ExecutionStrategy.ATOMIC: self._execute_atomic,
            ExecutionStrategy.SEQUENTIAL: self._execute_sequential,
            ExecutionStrategy.PARALLEL: self._execute_parallel,
            ExecutionStrategy.ADAPTIVE: self._execute_adaptive,
            ExecutionStrategy.TIMED: self._execute_timed,
            ExecutionStrategy.CONFIRMATION: self._execute_confirmation
        }
        
        strategy_function = strategy_map.get(context.strategy)
        if not strategy_function:
            raise ValueError(f"Unknown execution strategy: {context.strategy}")
        
        return await strategy_function(opportunity, context, validation_result)
    
    async def _execute_atomic(
        self,
        opportunity: ArbitrageOpportunity,
        context: ExecutionContext,
        validation_result: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute all legs atomically (all-or-nothing)."""
        
        self.logger.info(f"Executing atomic strategy for execution {context.execution_id}")
        
        leg_results = []
        all_succeeded = True
        
        # Track atomic execution start
        await self._execution_tracker.track_event(
            TrackEvent(
                execution_id=context.execution_id,
                event_type="atomic_execution_started",
                event_data={'legs_count': len(opportunity.legs)}
            )
        )
        
        try:
            # Prepare all legs for execution
            prepared_legs = await self._arbitrage_executor.prepare_legs(
                opportunity.legs, context, validation_result
            )
            
            # Execute all legs simultaneously with timeout
            execution_tasks = []
            for leg in prepared_legs:
                task = asyncio.create_task(
                    self._execute_single_leg(leg, context)
                )
                execution_tasks.append((leg, task))
            
            # Wait for all executions with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*(task for _, task in execution_tasks)),
                    timeout=context.max_execution_time
                )
            except asyncio.TimeoutError:
                self.logger.warning(f"Atomic execution {context.execution_id} timed out")
                # Rollback will be handled by caller
            
            # Collect results
            for leg, task in execution_tasks:
                try:
                    leg_result = await task
                    leg_results.append(leg_result)
                    
                    if not leg_result.get('success', False):
                        all_succeeded = False
                        
                except Exception as e:
                    self.logger.error(f"Leg execution failed: {str(e)}")
                    leg_results.append({
                        'success': False,
                        'error': str(e),
                        'leg': leg
                    })
                    all_succeeded = False
            
            # If not all succeeded, initiate rollback
            if not all_succeeded and self.config.enable_rollback_mechanism:
                await self._initiate_rollback(leg_results, context)
                all_succeeded = False
            
            return self._create_execution_result(
                context, opportunity, leg_results, all_succeeded
            )
            
        except Exception as e:
            self.logger.error(f"Atomic execution failed: {str(e)}")
            if self.config.enable_rollback_mechanism:
                await self._initiate_rollback(leg_results, context)
            raise
    
    async def _execute_sequential(
        self,
        opportunity: ArbitrageOpportunity,
        context: ExecutionContext,
        validation_result: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute legs sequentially."""
        
        self.logger.info(f"Executing sequential strategy for execution {context.execution_id}")
        
        leg_results = []
        all_succeeded = True
        total_stake_placed = 0.0
        
        await self._execution_tracker.track_event(
            TrackEvent(
                execution_id=context.execution_id,
                event_type="sequential_execution_started",
                event_data={'legs_count': len(opportunity.legs)}
            )
        )
        
        for i, leg in enumerate(opportunity.legs):
            try:
                # Execute leg with timeout
                leg_result = await asyncio.wait_for(
                    self._execute_single_leg(leg, context),
                    timeout=context.leg_timeout
                )
                
                leg_results.append(leg_result)
                total_stake_placed += leg_result.get('stake_placed', 0.0)
                
                if not leg_result.get('success', False):
                    all_succeeded = False
                    self.logger.warning(f"Leg {i+1} failed, continuing with remaining legs")
                    
                    if context.require_all_confirmations:
                        self.logger.error("Sequential execution aborted due to failure")
                        break
                else:
                    # Track successful leg
                    await self._execution_tracker.track_event(
                        TrackEvent(
                            execution_id=context.execution_id,
                            event_type="leg_completed",
                            event_data={
                                'leg_index': i,
                                'bookmaker': leg.bookmaker,
                                'stake_placed': leg_result.get('stake_placed', 0.0),
                                'success': True
                            }
                        )
                    )
                    
            except asyncio.TimeoutError:
                self.logger.warning(f"Leg {i+1} timed out")
                leg_results.append({
                    'success': False,
                    'error': 'Timeout',
                    'leg': leg,
                    'leg_index': i
                })
                all_succeeded = False
                break
                
            except Exception as e:
                self.logger.error(f"Leg {i+1} failed: {str(e)}")
                leg_results.append({
                    'success': False,
                    'error': str(e),
                    'leg': leg,
                    'leg_index': i
                })
                all_succeeded = False
        
        # Initiate rollback if required
        if not all_succeeded and self.config.enable_rollback_mechanism:
            await self._initiate_rollback(leg_results, context)
        
        return self._create_execution_result(
            context, opportunity, leg_results, all_succeeded, total_stake_placed
        )
    
    async def _execute_parallel(
        self,
        opportunity: ArbitrageOpportunity,
        context: ExecutionContext,
        validation_result: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute legs in parallel with coordination."""
        
        self.logger.info(f"Executing parallel strategy for execution {context.execution_id}")
        
        # Setup coordination for parallel execution
        await self._trade_coordinator.setup_parallel_coordination(
            opportunity, context
        )
        
        leg_results = []
        
        # Execute all legs in parallel
        execution_tasks = []
        for leg in opportunity.legs:
            task = asyncio.create_task(
                self._execute_single_leg(leg, context)
            )
            execution_tasks.append((leg, task))
        
        # Wait for all completions
        for leg, task in execution_tasks:
            try:
                leg_result = await task
                leg_results.append(leg_result)
            except Exception as e:
                leg_results.append({
                    'success': False,
                    'error': str(e),
                    'leg': leg
                })
        
        all_succeeded = all(result.get('success', False) for result in leg_results)
        
        return self._create_execution_result(
            context, opportunity, leg_results, all_succeeded
        )
    
    async def _execute_adaptive(
        self,
        opportunity: ArbitrageOpportunity,
        context: ExecutionContext,
        validation_result: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute using adaptive strategy based on opportunity characteristics."""
        
        # Analyze opportunity to determine best strategy
        if len(opportunity.legs) <= 2:
            # Simple opportunities - use atomic
            return await self._execute_atomic(opportunity, context, validation_result)
        elif len(opportunity.legs) > 4:
            # Complex opportunities - use sequential
            return await self._execute_sequential(opportunity, context, validation_result)
        else:
            # Medium complexity - use parallel
            return await self._execute_parallel(opportunity, context, validation_result)
    
    async def _execute_timed(
        self,
        opportunity: ArbitrageOpportunity,
        context: ExecutionContext,
        validation_result: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute with strict timing deadlines."""
        
        start_time = time.time()
        deadline = start_time + context.max_execution_time
        
        leg_results = []
        
        # Setup timed execution
        for i, leg in enumerate(opportunity.legs):
            remaining_time = deadline - time.time()
            if remaining_time <= 0:
                self.logger.warning("Timed execution deadline reached")
                break
            
            context.leg_timeout = min(context.leg_timeout, remaining_time)
            
            try:
                leg_result = await asyncio.wait_for(
                    self._execute_single_leg(leg, context),
                    timeout=context.leg_timeout
                )
                leg_results.append(leg_result)
            except asyncio.TimeoutError:
                self.logger.warning(f"Leg {i+1} timed out")
                break
        
        return self._create_execution_result(
            context, opportunity, leg_results, True  # Partial success considered success for timed
        )
    
    async def _execute_confirmation(
        self,
        opportunity: ArbitrageOpportunity,
        context: ExecutionContext,
        validation_result: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute with confirmation between legs."""
        
        leg_results = []
        all_succeeded = True
        
        for i, leg in enumerate(opportunity.legs):
            # Execute leg
            leg_result = await self._execute_single_leg(leg, context)
            leg_results.append(leg_result)
            
            if not leg_result.get('success', False):
                all_succeeded = False
                break
            
            # Wait for confirmation before next leg
            if i < len(opportunity.legs) - 1:  # Don't wait after last leg
                try:
                    await asyncio.wait_for(
                        self._wait_for_confirmation(leg_result, context),
                        timeout=context.confirmation_timeout
                    )
                except asyncio.TimeoutError:
                    self.logger.warning(f"Confirmation timeout for leg {i+1}")
                    break
        
        return self._create_execution_result(
            context, opportunity, leg_results, all_succeeded
        )
    
    async def _execute_single_leg(
        self,
        leg: ArbitrageLeg,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a single leg with the arbitrage executor."""
        
        self.logger.debug(f"Executing leg for {leg.bookmaker} in execution {context.execution_id}")
        
        # Use the arbitrage executor for actual bet placement
        result = await self._arbitrage_executor.execute_leg(
            leg, context
        )
        
        return result
    
    async def _wait_for_confirmation(
        self,
        leg_result: Dict[str, Any],
        context: ExecutionContext
    ) -> bool:
        """Wait for confirmation that leg was processed correctly."""
        
        # This would implement confirmation logic, such as:
        # - Checking bet status
        # - Verifying odds
        # - Confirming stake
        
        await asyncio.sleep(0.1)  # Simulate confirmation wait
        return True
    
    async def _initiate_rollback(
        self,
        leg_results: List[Dict[str, Any]],
        context: ExecutionContext
    ):
        """Initiate rollback process for failed execution."""
        
        self.logger.warning(f"Initiating rollback for execution {context.execution_id}")
        
        rollback_results = []
        
        for action in context.rollback_actions:
            if action == RollbackAction.CANCEL:
                await self._rollback_cancel_orders(leg_results, context, rollback_results)
            elif action == RollbackAction.HEDGE:
                await self._rollback_hedge_positions(leg_results, context, rollback_results)
            elif action == RollbackAction.LIQUIDATE:
                await self._rollback_liquidate_positions(leg_results, context, rollback_results)
        
        context.rollback_log = rollback_results
    
    async def _rollback_cancel_orders(
        self,
        leg_results: List[Dict[str, Any]],
        context: ExecutionContext,
        rollback_results: List[Dict[str, Any]]
    ):
        """Cancel unfilled orders as rollback action."""
        
        for leg_result in leg_results:
            if not leg_result.get('success', False) and 'order_id' in leg_result:
                # Cancel the order
                await self._arbitrage_executor.cancel_order(
                    leg_result['order_id']
                )
                rollback_results.append({
                    'action': 'cancel',
                    'order_id': leg_result['order_id'],
                    'success': True
                })
    
    async def _rollback_hedge_positions(
        self,
        leg_results: List[Dict[str, Any]],
        context: ExecutionContext,
        rollback_results: List[Dict[str, Any]]
    ):
        """Hedge remaining positions as rollback action."""
        
        # This would implement hedging logic
        # For now, log the action
        rollback_results.append({
            'action': 'hedge',
            'message': 'Hedging would be implemented here',
            'success': True
        })
    
    async def _rollback_liquidate_positions(
        self,
        leg_results: List[Dict[str, Any]],
        context: ExecutionContext,
        rollback_results: List[Dict[str, Any]]
    ):
        """Liquidate all positions as rollback action."""
        
        # This would implement liquidation logic
        # For now, log the action
        rollback_results.append({
            'action': 'liquidate',
            'message': 'Liquidation would be implemented here',
            'success': True
        })
    
    async def _handle_validation_failure(
        self,
        opportunity: ArbitrageOpportunity,
        context: ExecutionContext,
        validation_result: Dict[str, Any],
        start_time: datetime
    ) -> ExecutionResult:
        """Handle validation failure."""
        
        execution_result = ExecutionResult(
            execution_id=context.execution_id,
            opportunity_id=str(opportunity.id),
            execution_state=ExecutionState.FAILED,
            started_at=start_time,
            completed_at=datetime.utcnow(),
            execution_duration=(datetime.utcnow() - start_time).total_seconds(),
            errors=validation_result.get('errors', []),
            warnings=validation_result.get('warnings', [])
        )
        
        # Track failure
        await self._execution_tracker.track_event(
            TrackEvent(
                execution_id=context.execution_id,
                event_type="validation_failed",
                event_data={
                    'errors': validation_result.get('errors', []),
                    'warnings': validation_result.get('warnings', [])
                }
            )
        )
        
        return execution_result
    
    async def _handle_timeout(
        self,
        context: ExecutionContext,
        start_time: datetime
    ) -> ExecutionResult:
        """Handle execution timeout."""
        
        execution_result = ExecutionResult(
            execution_id=context.execution_id,
            opportunity_id=context.opportunity_id,
            execution_state=ExecutionState.TIMEOUT,
            started_at=start_time,
            completed_at=datetime.utcnow(),
            execution_duration=(datetime.utcnow() - start_time).total_seconds(),
            errors=["Execution timed out"]
        )
        
        # Initiate rollback if configured
        if context.auto_rollback_on_failure:
            await self._initiate_rollback([], context)
        
        return execution_result
    
    async def _handle_execution_error(
        self,
        context: ExecutionContext,
        start_time: datetime,
        error_message: str,
        error_trace: str
    ) -> ExecutionResult:
        """Handle execution error."""
        
        execution_result = ExecutionResult(
            execution_id=context.execution_id,
            opportunity_id=context.opportunity_id,
            execution_state=ExecutionState.FAILED,
            started_at=start_time,
            completed_at=datetime.utcnow(),
            execution_duration=(datetime.utcnow() - start_time).total_seconds(),
            errors=[error_message],
            rollback_log=[{
                'action': 'error_handling',
                'message': 'Error logged',
                'traceback': error_trace
            }]
        )
        
        return execution_result
    
    def _create_execution_result(
        self,
        context: ExecutionContext,
        opportunity: ArbitrageOpportunity,
        leg_results: List[Dict[str, Any]],
        success: bool,
        total_stake_placed: float = 0.0
    ) -> ExecutionResult:
        """Create execution result from context and results."""
        
        completed_at = datetime.utcnow()
        execution_duration = (completed_at - context.created_at).total_seconds()
        
        # Calculate metrics
        legs_attempted = len(leg_results)
        legs_succeeded = sum(1 for result in leg_results if result.get('success', False))
        legs_failed = legs_attempted - legs_succeeded
        
        if total_stake_placed == 0.0:
            total_stake_placed = sum(
                result.get('stake_placed', 0.0) for result in leg_results
            )
        
        total_potential_profit = float(opportunity.profit_amount)
        
        # Determine execution state
        if success:
            execution_state = ExecutionState.COMPLETED
        else:
            execution_state = ExecutionState.FAILED
        
        return ExecutionResult(
            execution_id=context.execution_id,
            opportunity_id=context.opportunity_id,
            execution_state=execution_state,
            started_at=context.created_at,
            completed_at=completed_at,
            execution_duration=execution_duration,
            legs_attempted=legs_attempted,
            legs_succeeded=legs_succeeded,
            legs_failed=legs_failed,
            total_stake_placed=total_stake_placed,
            total_potential_profit=total_potential_profit,
            leg_results=leg_results,
            coordination_log=await self._trade_coordinator.get_coordination_log(context.execution_id)
        )
    
    async def _finalize_execution(
        self,
        execution_result: ExecutionResult,
        context: ExecutionContext,
        start_time: datetime
    ) -> ExecutionResult:
        """Finalize execution and update performance metrics."""
        
        # Update performance statistics
        if execution_result.execution_state == ExecutionState.COMPLETED:
            self._performance_stats['successful_executions'] += 1
        else:
            self._performance_stats['failed_executions'] += 1
        
        # Track finalization
        await self._execution_tracker.track_event(
            TrackEvent(
                execution_id=execution_result.execution_id,
                event_type="execution_finalized",
                event_data={
                    'state': execution_result.execution_state.value,
                    'duration': execution_result.execution_duration,
                    'legs_succeeded': execution_result.legs_succeeded,
                    'legs_failed': execution_result.legs_failed
                }
            )
        )
        
        return execution_result
    
    async def _cleanup_execution(self, execution_id: str):
        """Cleanup execution resources."""
        
        async with self._execution_locks:
            if execution_id in self._active_executions:
                del self._active_executions[execution_id]
        
        self.logger.debug(f"Cleaned up execution {execution_id}")
    
    async def get_execution_status(self, execution_id: str) -> Optional[ExecutionState]:
        """Get current execution status."""
        
        context = self._active_executions.get(execution_id)
        return context.execution_state if context else None
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution."""
        
        if execution_id not in self._active_executions:
            return False
        
        context = self._active_executions[execution_id]
        context.execution_state = ExecutionState.CANCELLED
        
        # Initiate rollback
        if self.config.enable_rollback_mechanism:
            await self._initiate_rollback([], context)
        
        return True
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return self._performance_stats.copy()
    
    async def get_active_executions(self) -> List[Dict[str, Any]]:
        """Get list of active executions."""
        
        async with self._execution_locks:
            return [
                {
                    'execution_id': ctx.execution_id,
                    'opportunity_id': ctx.opportunity_id,
                    'state': ctx.execution_state.value,
                    'started_at': ctx.created_at.isoformat(),
                    'strategy': ctx.strategy.value,
                    'order_type': ctx.order_type.value
                }
                for ctx in self._active_executions.values()
            ]
    
    async def shutdown(self):
        """Graceful shutdown of the execution engine."""
        
        self.logger.info("Shutting down Multi-Leg Executor...")
        
        # Cancel all active executions
        execution_ids = list(self._active_executions.keys())
        for execution_id in execution_ids:
            await self.cancel_execution(execution_id)
        
        # Wait for cleanup
        await asyncio.sleep(1.0)
        
        # Set shutdown event
        self._shutdown_event.set()
        
        self.logger.info("Multi-Leg Executor shutdown complete")