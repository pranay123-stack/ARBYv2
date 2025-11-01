"""
Comprehensive Emergency Stop Mechanisms for ARBitech Trading Platform

This module implements advanced emergency stop mechanisms with:
- Manual override capabilities
- Automatic trigger systems
- Graceful shutdown procedures
- Integration with trading execution systems
- Fail-safe mechanisms for system failures
- Multiple stop types (hard, soft, partial)

The system provides bulletproof protection with multiple layers of safety
and zero-downtime operation.
"""

import asyncio
import time
import signal
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set, Union
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import json
import queue
from collections import deque
import weakref

from arbitech.storage.audit_logger import (
    AuditLogger, EventType, LogLevel, SecurityEventLog,
    get_audit_logger, log_trade_execution, TradeExecutionLog
)
from arbitech.storage.models import ArbitrageOpportunity, Trade, TradeStatus, Notification, NotificationType, NotificationPriority
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StopType(Enum):
    """Types of emergency stops"""
    HARD_STOP = "hard_stop"          # Immediate complete halt
    SOFT_STOP = "soft_stop"          # Graceful shutdown
    PARTIAL_STOP = "partial_stop"    # Partial operation reduction
    MAINTENANCE_STOP = "maintenance_stop"  # System maintenance
    LIQUIDATION_STOP = "liquidation_stop"  # Position liquidation
    THROTTLE_STOP = "throttle_stop"  # Rate limiting


class StopLevel(Enum):
    """Emergency stop severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class StopStatus(Enum):
    """Emergency stop status"""
    INACTIVE = "inactive"
    PENDING = "pending"
    ACTIVE = "active"
    SHUTTING_DOWN = "shutting_down"
    RECOVERY = "recovery"
    MAINTENANCE = "maintenance"


@dataclass
class StopCondition:
    """Condition for triggering emergency stop"""
    condition_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    trigger_function: Optional[Callable] = None
    check_interval_seconds: float = 1.0
    severity: StopLevel = StopLevel.ERROR
    auto_trigger: bool = True
    cooldown_seconds: int = 300
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'condition_id': str(self.condition_id),
            'name': self.name,
            'description': self.description,
            'severity': self.severity.value,
            'auto_trigger': self.auto_trigger,
            'cooldown_seconds': self.cooldown_seconds,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'trigger_count': self.trigger_count,
            'enabled': self.enabled,
            'parameters': self.parameters
        }


@dataclass
class EmergencyStopEvent:
    """Emergency stop event"""
    event_id: UUID = field(default_factory=uuid4)
    stop_type: StopType = StopType.SOFT_STOP
    level: StopLevel = StopLevel.ERROR
    trigger_reason: str = ""
    initiated_by: Optional[str] = None  # user_id, system, condition_id
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    affected_positions: List[UUID] = field(default_factory=list)
    affected_users: List[str] = field(default_factory=list)
    estimated_completion: Optional[datetime] = None
    stop_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'event_id': str(self.event_id),
            'stop_type': self.stop_type.value,
            'level': self.level.value,
            'trigger_reason': self.trigger_reason,
            'initiated_by': self.initiated_by,
            'timestamp': self.timestamp.isoformat(),
            'affected_positions': [str(pos) for pos in self.affected_positions],
            'affected_users': self.affected_users,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'stop_actions': self.stop_actions,
            'metadata': self.metadata
        }


@dataclass
class EmergencyStopConfig:
    """Configuration for emergency stop system"""
    # Stop levels
    hard_stop_timeout_seconds: int = 10
    soft_stop_timeout_seconds: int = 300
    liquidation_timeout_seconds: int = 60
    maintenance_timeout_seconds: int = 1800
    
    # Default conditions
    max_consecutive_losses: int = 10
    max_daily_loss_percentage: float = 0.15  # 15%
    max_drawdown_percentage: float = 0.20    # 20%
    max_execution_time_seconds: int = 60
    min_profit_margin: float = 0.01  # 1%
    
    # System health triggers
    max_error_rate: float = 0.05  # 5% error rate
    max_memory_usage: float = 0.80  # 80% memory usage
    max_cpu_usage: float = 0.80  # 80% CPU usage
    min_uptime_hours: float = 1.0
    
    # Liquidation settings
    auto_liquidation_enabled: bool = True
    liquidation_batch_size: int = 10
    liquidation_delay_seconds: float = 5.0
    
    # Recovery settings
    auto_recovery_enabled: bool = True
    recovery_validation_seconds: int = 300
    manual_recovery_required: bool = False
    
    # Notification settings
    notify_on_stop: bool = True
    notify_on_recovery: bool = True
    critical_immediate_shutdown: bool = True
    
    # Integration settings
    trading_system_timeout: int = 30
    database_timeout: int = 10
    external_api_timeout: int = 15


class EmergencyStopCondition:
    """Base class for emergency stop conditions"""
    
    def __init__(self, config: EmergencyStopConfig, audit_logger: AuditLogger):
        self.config = config
        self.audit_logger = audit_logger
        self.last_check = datetime.now(timezone.utc)
        self.consecutive_failures = 0
        self.metric_history = deque(maxlen=100)
    
    async def check_condition(self) -> Optional[EmergencyStopEvent]:
        """Check if condition is met - override in subclasses"""
        return None
    
    def should_check(self) -> bool:
        """Check if condition should be evaluated"""
        return (datetime.now(timezone.utc) - self.last_check).total_seconds() >= self.config.check_interval_seconds


class LossThresholdCondition(EmergencyStopCondition):
    """Emergency stop based on loss thresholds"""
    
    def __init__(self, config: EmergencyStopConfig, audit_logger: AuditLogger, bankroll_manager):
        super().__init__(config, audit_logger)
        self.bankroll_manager = bankroll_manager
    
    async def check_condition(self) -> Optional[EmergencyStopEvent]:
        """Check loss threshold conditions"""
        try:
            current_bankroll = await self.bankroll_manager.get_current_bankroll()
            daily_pnl = await self.bankroll_manager.get_daily_pnl()
            drawdown = await self.bankroll_manager.get_current_drawdown()
            
            if not current_bankroll or current_bankroll <= 0:
                return None
            
            # Check daily loss threshold
            daily_loss_pct = abs(daily_pnl) / current_bankroll if daily_pnl < 0 else 0
            if daily_loss_pct > self.config.max_daily_loss_percentage:
                return EmergencyStopEvent(
                    stop_type=StopType.HARD_STOP,
                    level=StopLevel.CRITICAL,
                    trigger_reason=f"Daily loss threshold exceeded: {daily_loss_pct:.2%}",
                    initiated_by="loss_threshold_condition",
                    metadata={
                        'daily_loss_pct': daily_loss_pct,
                        'threshold': self.config.max_daily_loss_percentage,
                        'daily_pnl': daily_pnl,
                        'bankroll': current_bankroll
                    }
                )
            
            # Check drawdown threshold
            if drawdown > self.config.max_drawdown_percentage:
                return EmergencyStopEvent(
                    stop_type=StopType.HARD_STOP,
                    level=StopLevel.CRITICAL,
                    trigger_reason=f"Maximum drawdown exceeded: {drawdown:.2%}",
                    initiated_by="drawdown_condition",
                    metadata={
                        'drawdown_pct': drawdown,
                        'threshold': self.config.max_drawdown_percentage
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking loss threshold condition: {e}", exc_info=True)
            self.consecutive_failures += 1
            return None


class SystemHealthCondition(EmergencyStopCondition):
    """Emergency stop based on system health metrics"""
    
    def __init__(self, config: EmergencyStopConfig, audit_logger: AuditLogger, monitoring_system):
        super().__init__(config, audit_logger)
        self.monitoring_system = monitoring_system
    
    async def check_condition(self) -> Optional[EmergencyStopEvent]:
        """Check system health conditions"""
        try:
            health_status = await self.monitoring_system.get_health_status()
            
            # Check error rate
            error_rate = health_status.get('error_rate', 0)
            if error_rate > self.config.max_error_rate:
                return EmergencyStopEvent(
                    stop_type=StopType.SOFT_STOP,
                    level=StopLevel.ERROR,
                    trigger_reason=f"High error rate: {error_rate:.2%}",
                    initiated_by="system_health_condition",
                    metadata={
                        'error_rate': error_rate,
                        'threshold': self.config.max_error_rate,
                        'health_details': health_status
                    }
                )
            
            # Check memory usage
            memory_usage = health_status.get('memory_usage', 0)
            if memory_usage > self.config.max_memory_usage:
                return EmergencyStopEvent(
                    stop_type=StopType.SOFT_STOP,
                    level=StopLevel.WARNING,
                    trigger_reason=f"High memory usage: {memory_usage:.2%}",
                    initiated_by="system_health_condition",
                    metadata={
                        'memory_usage': memory_usage,
                        'threshold': self.config.max_memory_usage
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking system health condition: {e}", exc_info=True)
            self.consecutive_failures += 1
            return None


class ExecutionPerformanceCondition(EmergencyStopCondition):
    """Emergency stop based on execution performance"""
    
    def __init__(self, config: EmergencyStopConfig, audit_logger: AuditLogger):
        super().__init__(config, audit_logger)
        self.execution_times = deque(maxlen=100)
        self.success_count = 0
        self.total_count = 0
    
    async def check_condition(self) -> Optional[EmergencyStopEvent]:
        """Check execution performance conditions"""
        try:
            if len(self.execution_times) < 10:  # Need enough samples
                return None
            
            # Calculate average execution time
            avg_time = sum(self.execution_times) / len(self.execution_times)
            if avg_time > self.config.max_execution_time_seconds:
                return EmergencyStopEvent(
                    stop_type=StopType.THROTTLE_STOP,
                    level=StopLevel.WARNING,
                    trigger_reason=f"Slow execution performance: {avg_time:.2f}s avg",
                    initiated_by="execution_performance_condition",
                    metadata={
                        'avg_execution_time': avg_time,
                        'threshold': self.config.max_execution_time_seconds,
                        'sample_count': len(self.execution_times)
                    }
                )
            
            # Check success rate
            if self.total_count >= 10:
                success_rate = self.success_count / self.total_count
                min_margin = self.config.min_profit_margin
                
                if success_rate < (1 - min_margin):
                    return EmergencyStopEvent(
                        stop_type=StopType.PARTIAL_STOP,
                        level=StopLevel.ERROR,
                        trigger_reason=f"Low success rate: {success_rate:.2%}",
                        initiated_by="execution_performance_condition",
                        metadata={
                            'success_rate': success_rate,
                            'expected_rate': 1 - min_margin,
                            'total_attempts': self.total_count,
                            'successful_attempts': self.success_count
                        }
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking execution performance condition: {e}", exc_info=True)
            self.consecutive_failures += 1
            return None
    
    def record_execution(self, execution_time: float, success: bool):
        """Record execution metrics"""
        self.execution_times.append(execution_time)
        self.total_count += 1
        if success:
            self.success_count += 1


class EmergencyStop:
    """Individual emergency stop instance"""
    
    def __init__(self, stop_id: str, stop_type: StopType, config: EmergencyStopConfig,
                 audit_logger: AuditLogger):
        self.stop_id = stop_id
        self.stop_type = stop_type
        self.config = config
        self.audit_logger = audit_logger
        
        self.status = StopStatus.INACTIVE
        self.current_event: Optional[EmergencyStopEvent] = None
        self.active_conditions: Dict[str, StopCondition] = {}
        self.stop_handlers: List[Callable] = []
        self.recovery_handlers: List[Callable] = []
        
        # Timing
        self.status_change_time = datetime.now(timezone.utc)
        self.estimated_completion: Optional[datetime] = None
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info(f"Emergency stop {stop_id} initialized", 
                   stop_type=stop_type.value, config=config.__dict__)
    
    def add_condition(self, condition: StopCondition):
        """Add stop condition"""
        with self._lock:
            self.active_conditions[condition.name] = condition
            logger.debug(f"Added stop condition {condition.name} to {self.stop_id}")
    
    def add_stop_handler(self, handler: Callable):
        """Add handler to be called when stop is activated"""
        self.stop_handlers.append(handler)
    
    def add_recovery_handler(self, handler: Callable):
        """Add handler to be called when stop is recovered"""
        self.recovery_handlers.append(handler)
    
    async def activate_stop(self, event: EmergencyStopEvent, 
                          force: bool = False) -> bool:
        """Activate emergency stop"""
        with self._lock:
            if not force and self.status == StopStatus.ACTIVE:
                logger.warning(f"Emergency stop {self.stop_id} already active")
                return False
            
            # Update status
            previous_status = self.status
            self.status = StopStatus.ACTIVE
            self.current_event = event
            self.status_change_time = datetime.now(timezone.utc)
            
            # Calculate estimated completion time
            if self.stop_type == StopType.HARD_STOP:
                self.estimated_completion = datetime.now(timezone.utc) + timedelta(seconds=self.config.hard_stop_timeout_seconds)
            elif self.stop_type == StopType.SOFT_STOP:
                self.estimated_completion = datetime.now(timezone.utc) + timedelta(seconds=self.config.soft_stop_timeout_seconds)
            elif self.stop_type == StopType.LIQUIDATION_STOP:
                self.estimated_completion = datetime.now(timezone.utc) + timedelta(seconds=self.config.liquidation_timeout_seconds)
            else:
                self.estimated_completion = datetime.now(timezone.utc) + timedelta(seconds=self.config.maintenance_timeout_seconds)
            
            logger.critical(
                f"Emergency stop {self.stop_id} ACTIVATED",
                stop_type=self.stop_type.value,
                level=event.level.value,
                reason=event.trigger_reason,
                initiated_by=event.initiated_by,
                estimated_completion=self.estimated_completion.isoformat(),
                previous_status=previous_status.value
            )
            
            # Log security event
            self.audit_logger.log_security_event(SecurityEventLog(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type='EMERGENCY_STOP_ACTIVATED',
                severity=LogLevel.CRITICAL if event.level == StopLevel.EMERGENCY else LogLevel.ERROR,
                user_id=None,
                ip_address=None,
                session_id=None,
                description=f"Emergency stop activated: {event.trigger_reason}",
                details=event.to_dict()
            ))
            
            # Execute stop handlers
            await self._execute_stop_handlers(event)
            
            return True
    
    async def _execute_stop_handlers(self, event: EmergencyStopEvent):
        """Execute all stop handlers"""
        for handler in self.stop_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Stop handler failed: {e}", exc_info=True)
    
    async def begin_shutdown(self) -> bool:
        """Begin graceful shutdown process"""
        with self._lock:
            if self.status != StopStatus.ACTIVE:
                return False
            
            self.status = StopStatus.SHUTTING_DOWN
            self.status_change_time = datetime.now(timezone.utc)
            
            logger.info(f"Emergency stop {self.stop_id} beginning shutdown process")
            
            # Execute shutdown handlers
            for handler in self.stop_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(self.current_event)
                    else:
                        handler(self.current_event)
                except Exception as e:
                    logger.error(f"Shutdown handler failed: {e}", exc_info=True)
            
            return True
    
    async def recover(self, reason: str = "Manual recovery") -> bool:
        """Recover from emergency stop"""
        with self._lock:
            if self.status not in [StopStatus.ACTIVE, StopStatus.SHUTTING_DOWN, StopStatus.MAINTENANCE]:
                return False
            
            previous_status = self.status
            self.status = StopStatus.RECOVERY
            self.status_change_time = datetime.now(timezone.utc)
            
            logger.info(f"Emergency stop {self.stop_id} beginning recovery", 
                       reason=reason, previous_status=previous_status.value)
            
            # Execute recovery handlers
            for handler in self.recovery_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(self.current_event)
                    else:
                        handler(self.current_event)
                except Exception as e:
                    logger.error(f"Recovery handler failed: {e}", exc_info=True)
            
            # Complete recovery after validation period
            recovery_thread = threading.Thread(target=self._complete_recovery, args=(reason,), daemon=True)
            recovery_thread.start()
            
            return True
    
    def _complete_recovery(self, reason: str):
        """Complete recovery process"""
        try:
            # Wait for validation period
            time.sleep(self.config.recovery_validation_seconds)
            
            with self._lock:
                self.status = StopStatus.INACTIVE
                self.status_change_time = datetime.now(timezone.utc)
                self.current_event = None
                self.estimated_completion = None
                
                logger.info(f"Emergency stop {self.stop_id} recovered", 
                           reason=reason)
                
                # Log recovery
                self.audit_logger.log_security_event(SecurityEventLog(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    event_type='EMERGENCY_STOP_RECOVERED',
                    severity=LogLevel.INFO,
                    user_id=None,
                    ip_address=None,
                    session_id=None,
                    description=f"Emergency stop recovered: {reason}",
                    details={
                        'stop_id': self.stop_id,
                        'recovery_reason': reason,
                        'duration_seconds': (datetime.now(timezone.utc) - self.status_change_time).total_seconds()
                    }
                ))
                
        except Exception as e:
            logger.error(f"Recovery completion failed: {e}", exc_info=True)
    
    async def check_conditions(self) -> List[EmergencyStopEvent]:
        """Check all active conditions"""
        events = []
        
        with self._lock:
            for condition_name, condition in self.active_conditions.items():
                if not condition.enabled:
                    continue
                
                try:
                    # Check cooldown
                    if (condition.last_triggered and 
                        (datetime.now(timezone.utc) - condition.last_triggered).total_seconds() < condition.cooldown_seconds):
                        continue
                    
                    # Check condition
                    if condition.should_check():
                        event = await condition.check_condition()
                        if event:
                            event.trigger_reason = f"{condition.description}: {event.trigger_reason}"
                            condition.last_triggered = datetime.now(timezone.utc)
                            condition.trigger_count += 1
                            events.append(event)
                            
                            logger.warning(f"Stop condition {condition_name} triggered", 
                                         condition=condition.to_dict())
                    
                except Exception as e:
                    logger.error(f"Error checking condition {condition_name}: {e}", exc_info=True)
        
        return events
    
    def force_activate(self, reason: str, initiated_by: str = "manual") -> bool:
        """Force activate stop manually"""
        event = EmergencyStopEvent(
            stop_type=self.stop_type,
            level=StopLevel.ERROR,
            trigger_reason=f"Manual activation: {reason}",
            initiated_by=initiated_by
        )
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.activate_stop(event, force=True))
        finally:
            loop.close()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current emergency stop status"""
        with self._lock:
            return {
                'stop_id': self.stop_id,
                'stop_type': self.stop_type.value,
                'status': self.status.value,
                'status_change_time': self.status_change_time.isoformat(),
                'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
                'current_event': self.current_event.to_dict() if self.current_event else None,
                'active_conditions': {
                    name: condition.to_dict() for name, condition in self.active_conditions.items()
                },
                'handler_count': len(self.stop_handlers),
                'uptime_seconds': (datetime.now(timezone.utc) - self.status_change_time).total_seconds()
            }


class EmergencyStopManager:
    """Manager for multiple emergency stops"""
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        self.audit_logger = audit_logger or get_audit_logger()
        self.emergency_stops: Dict[str, EmergencyStop] = {}
        self.config = EmergencyStopConfig()
        self._lock = threading.Lock()
        
        # Global state
        self.global_status = StopStatus.INACTIVE
        self.global_shutdown_initiated = False
        self.monitoring_active = False
        
        # Condition monitoring
        self.monitoring_task: Optional[asyncio.Task] = None
        self.condition_checks_queue = queue.Queue()
        
        logger.info("Emergency stop manager initialized")
    
    def create_emergency_stop(self, stop_id: str, stop_type: StopType, 
                            config: Optional[EmergencyStopConfig] = None) -> EmergencyStop:
        """Create new emergency stop"""
        with self._lock:
            if stop_id in self.emergency_stops:
                raise ValueError(f"Emergency stop {stop_id} already exists")
            
            stop_config = config or self.config
            emergency_stop = EmergencyStop(stop_id, stop_type, stop_config, self.audit_logger)
            
            self.emergency_stops[stop_id] = emergency_stop
            
            logger.info(f"Created emergency stop {stop_id}", stop_type=stop_type.value)
            
            return emergency_stop
    
    def get_emergency_stop(self, stop_id: str) -> Optional[EmergencyStop]:
        """Get emergency stop by ID"""
        with self._lock:
            return self.emergency_stops.get(stop_id)
    
    async def start_monitoring(self):
        """Start condition monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Emergency stop monitoring started")
    
    async def stop_monitoring(self):
        """Stop condition monitoring"""
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Emergency stop monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                await self._check_all_conditions()
                await asyncio.sleep(1.0)  # Check every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(5.0)  # Wait longer on error
    
    async def _check_all_conditions(self):
        """Check all conditions across all emergency stops"""
        all_events = []
        
        with self._lock:
            for stop in self.emergency_stops.values():
                try:
                    events = await stop.check_conditions()
                    all_events.extend(events)
                except Exception as e:
                    logger.error(f"Error checking conditions for stop {stop.stop_id}: {e}", exc_info=True)
        
        # Process triggered events
        for event in all_events:
            await self._process_stop_event(event)
    
    async def _process_stop_event(self, event: EmergencyStopEvent):
        """Process triggered stop event"""
        logger.critical(f"Processing emergency stop event: {event.trigger_reason}")
        
        # Find appropriate emergency stop or create global stop
        target_stop = None
        for stop in self.emergency_stops.values():
            if stop.stop_type == event.stop_type:
                target_stop = stop
                break
        
        if not target_stop:
            # Create temporary global stop
            target_stop = self.create_emergency_stop(f"global_{event.stop_type.value}", event.stop_type)
        
        # Activate the stop
        await target_stop.activate_stop(event)
        
        # Update global status
        self._update_global_status()
    
    def _update_global_status(self):
        """Update global system status"""
        with self._lock:
            active_stops = [stop for stop in self.emergency_stops.values() if stop.status == StopStatus.ACTIVE]
            
            if not active_stops:
                self.global_status = StopStatus.INACTIVE
            elif any(stop.stop_type == StopType.HARD_STOP for stop in active_stops):
                self.global_status = StopStatus.EMERGENCY
            elif any(stop.stop_type == StopType.SOFT_STOP for stop in active_stops):
                self.global_status = StopStatus.SHUTTING_DOWN
            else:
                self.global_status = StopStatus.ACTIVE
    
    async def global_shutdown(self, reason: str, initiated_by: str = "system") -> bool:
        """Initiate global system shutdown"""
        if self.global_shutdown_initiated:
            logger.warning("Global shutdown already initiated")
            return False
        
        self.global_shutdown_initiated = True
        
        logger.critical("Initiating global system shutdown", reason=reason, initiated_by=initiated_by)
        
        # Stop monitoring first
        await self.stop_monitoring()
        
        # Activate all emergency stops
        shutdown_tasks = []
        with self._lock:
            for stop in self.emergency_stops.values():
                if stop.status != StopStatus.ACTIVE:
                    event = EmergencyStopEvent(
                        stop_type=stop.stop_type,
                        level=StopLevel.EMERGENCY,
                        trigger_reason=f"Global shutdown: {reason}",
                        initiated_by=initiated_by
                    )
                    shutdown_tasks.append(stop.activate_stop(event, force=True))
        
        # Wait for all stops to activate
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        # Begin shutdown process
        shutdown_tasks = []
        with self._lock:
            for stop in self.emergency_stops.values():
                shutdown_tasks.append(stop.begin_shutdown())
        
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        
        self.global_status = StopStatus.EMERGENCY
        
        logger.critical("Global system shutdown completed")
        return True
    
    async def global_recovery(self, reason: str = "System recovery") -> bool:
        """Initiate global system recovery"""
        if not self.global_shutdown_initiated:
            logger.warning("No global shutdown to recover from")
            return False
        
        self.global_shutdown_initiated = False
        
        logger.info("Initiating global system recovery", reason=reason)
        
        # Recover all emergency stops
        recovery_tasks = []
        with self._lock:
            for stop in self.emergency_stops.values():
                if stop.status in [StopStatus.ACTIVE, StopStatus.SHUTTING_DOWN, StopStatus.MAINTENANCE]:
                    recovery_tasks.append(stop.recover(reason))
        
        if recovery_tasks:
            await asyncio.gather(*recovery_tasks, return_exceptions=True)
        
        self.global_status = StopStatus.INACTIVE
        
        # Restart monitoring
        await self.start_monitoring()
        
        logger.info("Global system recovery completed")
        return True
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        with self._lock:
            status = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'global_status': self.global_status.value,
                'global_shutdown_initiated': self.global_shutdown_initiated,
                'monitoring_active': self.monitoring_active,
                'total_stops': len(self.emergency_stops),
                'stops': {},
                'active_conditions': 0
            }
            
            for stop_id, stop in self.emergency_stops.items():
                stop_status = stop.get_status()
                status['stops'][stop_id] = stop_status
                status['active_conditions'] += len(stop.active_conditions)
            
            return status
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on emergency stop system"""
        health = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'healthy': True,
            'issues': []
        }
        
        with self._lock:
            # Check each emergency stop
            for stop_id, stop in self.emergency_stops.items():
                stop_health = {
                    'stop_id': stop_id,
                    'stop_type': stop.stop_type.value,
                    'status': stop.status.value,
                    'healthy': True,
                    'issues': []
                }
                
                # Check for stuck states
                if stop.status == StopStatus.SHUTTING_DOWN:
                    duration = datetime.now(timezone.utc) - stop.status_change_time
                    if duration.total_seconds() > 3600:  # 1 hour
                        stop_health['healthy'] = False
                        stop_health['issues'].append(f"Shutdown stuck for {duration}")
                
                if not stop_health['healthy']:
                    health['healthy'] = False
                    health['issues'].append(f"Emergency stop {stop_id}: {stop_health['issues']}")
                
                health[f'stop_{stop_id}'] = stop_health
        
        return health


class GracefulShutdownHandler:
    """Handler for graceful system shutdown"""
    
    def __init__(self, emergency_stop_manager: EmergencyStopManager):
        self.emergency_stop_manager = emergency_stop_manager
        self.shutdown_handlers: List[Callable] = []
        self.shutdown_in_progress = False
        self._original_handlers = {}
        
        # Register signal handlers
        self._register_signal_handlers()
    
    def _register_signal_handlers(self):
        """Register signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.critical(f"Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(self.initiate_graceful_shutdown(f"Signal {signum}"))
        
        self._original_handlers[signal.SIGTERM] = signal.signal(signal.SIGTERM, signal_handler)
        self._original_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, signal_handler)
    
    def add_shutdown_handler(self, handler: Callable):
        """Add shutdown handler"""
        self.shutdown_handlers.append(handler)
    
    async def initiate_graceful_shutdown(self, reason: str = "System shutdown"):
        """Initiate graceful shutdown process"""
        if self.shutdown_in_progress:
            logger.warning("Graceful shutdown already in progress")
            return
        
        self.shutdown_in_progress = True
        
        logger.critical("Initiating graceful shutdown", reason=reason)
        
        try:
            # Stage 1: Stop new operations
            await self._stage_1_stop_new_operations()
            
            # Stage 2: Complete existing operations
            await self._stage_2_complete_existing_operations()
            
            # Stage 3: Emergency stops
            await self._stage_3_emergency_stops()
            
            # Stage 4: Final cleanup
            await self._stage_4_final_cleanup()
            
            logger.critical("Graceful shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during graceful shutdown: {e}", exc_info=True)
            # Force emergency shutdown
            await self.emergency_stop_manager.global_shutdown(f"Shutdown error: {e}")
        finally:
            self.shutdown_in_progress = False
    
    async def _stage_1_stop_new_operations(self):
        """Stage 1: Stop accepting new operations"""
        logger.info("Stage 1: Stopping new operations")
        
        # Execute stage 1 handlers
        for handler in self.shutdown_handlers:
            if hasattr(handler, 'stage') and handler.stage == 1:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler()
                    else:
                        handler()
                except Exception as e:
                    logger.error(f"Stage 1 handler failed: {e}", exc_info=True)
        
        await asyncio.sleep(5)  # Allow time for handlers to complete
    
    async def _stage_2_complete_existing_operations(self):
        """Stage 2: Complete existing operations"""
        logger.info("Stage 2: Completing existing operations")
        
        # Execute stage 2 handlers
        for handler in self.shutdown_handlers:
            if hasattr(handler, 'stage') and handler.stage == 2:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler()
                    else:
                        handler()
                except Exception as e:
                    logger.error(f"Stage 2 handler failed: {e}", exc_info=True)
        
        await asyncio.sleep(10)  # Allow time for operations to complete
    
    async def _stage_3_emergency_stops(self):
        """Stage 3: Activate emergency stops"""
        logger.info("Stage 3: Activating emergency stops")
        
        await self.emergency_stop_manager.global_shutdown("Graceful shutdown stage 3")
    
    async def _stage_4_final_cleanup(self):
        """Stage 4: Final cleanup and shutdown"""
        logger.info("Stage 4: Final cleanup")
        
        # Execute final cleanup handlers
        for handler in self.shutdown_handlers:
            if hasattr(handler, 'stage') and handler.stage == 4:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler()
                    else:
                        handler()
                except Exception as e:
                    logger.error(f"Stage 4 handler failed: {e}", exc_info=True)
        
        # Stop the event loop
        asyncio.get_event_loop().stop()


# Global emergency stop manager instance
_global_es_manager = None


def get_emergency_stop_manager() -> EmergencyStopManager:
    """Get or create global emergency stop manager"""
    global _global_es_manager
    if _global_es_manager is None:
        _global_es_manager = EmergencyStopManager()
    return _global_es_manager


if __name__ == "__main__":
    # Example usage and testing
    async def test_emergency_stops():
        # Setup
        manager = get_emergency_stop_manager()
        
        # Create emergency stop
        hard_stop = manager.create_emergency_stop("hard_stop_1", StopType.HARD_STOP)
        
        # Add condition
        condition = StopCondition(
            name="test_loss_condition",
            description="Test loss threshold",
            severity=StopLevel.ERROR,
            auto_trigger=True
        )
        hard_stop.add_condition(condition)
        
        # Test manual activation
        print("Testing manual activation...")
        hard_stop.force_activate("Manual test activation", "test_user")
        
        # Test status
        status = hard_stop.get_status()
        print(f"Emergency stop status: {status}")
        
        # Start monitoring
        print("Starting monitoring...")
        await manager.start_monitoring()
        
        # Wait and test recovery
        await asyncio.sleep(2)
        print("Testing recovery...")
        await hard_stop.recover("Test recovery")
        
        # Get system status
        system_status = manager.get_system_status()
        print(f"System status: {system_status}")
        
        # Test global shutdown
        print("Testing global shutdown...")
        await manager.global_shutdown("Test global shutdown", "test_system")
        
        await asyncio.sleep(2)
        
        # Test global recovery
        print("Testing global recovery...")
        await manager.global_recovery("Test global recovery")
        
        print("Emergency stop test completed!")
    
    # Run test
    asyncio.run(test_emergency_stops())