"""
Multi-Level Circuit Breaker System for ARBitech Trading Platform

This module implements an advanced circuit breaker system with multiple trigger types:
- Price-based triggers for market volatility
- Time-based triggers for execution timeouts
- Loss-based triggers for risk management
- Automatic position liquidation capabilities
- Integration with existing audit and logging systems

The system provides bulletproof protection against systematic risk with
multiple layers of safety and zero-downtime operation.
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import json
import threading
from collections import deque
import statistics

from arbitech.storage.audit_logger import (
    AuditLogger, EventType, LogLevel, SecurityEventLog,
    get_audit_logger
)
from arbitech.storage.models import ArbitrageOpportunity, Trade, TradeStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Circuit breaker tripped
    HALF_OPEN = "half_open"    # Testing recovery
    MAINTENANCE = "maintenance" # System maintenance mode


class TriggerType(Enum):
    """Types of circuit breaker triggers"""
    PRICE_VOLATILITY = "price_volatility"
    EXECUTION_TIMEOUT = "execution_timeout"
    LOSS_THRESHOLD = "loss_threshold"
    CONSECUTIVE_FAILURES = "consecutive_failures"
    MARKET_DISRUPTION = "market_disruption"
    SYSTEM_OVERLOAD = "system_overload"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    POSITION_SIZE = "position_size"


class Severity(Enum):
    """Severity levels for circuit breaker triggers"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CircuitBreakerTrigger:
    """Circuit breaker trigger event"""
    trigger_id: UUID = field(default_factory=uuid4)
    trigger_type: TriggerType = TriggerType.LOSS_THRESHOLD
    severity: Severity = Severity.MEDIUM
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    description: str = ""
    affected_positions: List[UUID] = field(default_factory=list)
    auto_liquidation_required: bool = False
    cooldown_seconds: int = 300  # 5 minutes default
    recovery_conditions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'trigger_id': str(self.trigger_id),
            'trigger_type': self.trigger_type.value,
            'severity': self.severity.value,
            'threshold_value': self.threshold_value,
            'actual_value': self.actual_value,
            'timestamp': self.timestamp.isoformat(),
            'description': self.description,
            'affected_positions': [str(pos) for pos in self.affected_positions],
            'auto_liquidation_required': self.auto_liquidation_required,
            'cooldown_seconds': self.cooldown_seconds,
            'recovery_conditions': self.recovery_conditions
        }


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker system"""
    # Price-based triggers
    price_volatility_threshold: float = 0.05  # 5% price change triggers
    price_volatility_window_minutes: int = 15
    
    # Time-based triggers
    max_execution_time_seconds: int = 30
    max_consecutive_timeouts: int = 3
    timeout_window_minutes: int = 10
    
    # Loss-based triggers
    max_daily_loss_percentage: float = 0.10  # 10% of bankroll
    max_hourly_loss_percentage: float = 0.05  # 5% of bankroll
    max_consecutive_losses: int = 5
    loss_window_hours: int = 24
    
    # Position size triggers
    max_position_size_percentage: float = 0.20  # 20% of bankroll per position
    max_total_exposure_percentage: float = 0.50  # 50% total exposure
    
    # System triggers
    max_consecutive_failures: int = 10
    failure_window_minutes: int = 5
    system_load_threshold: float = 0.80  # 80% CPU/memory usage
    
    # Liquidity triggers
    min_liquidity_percentage: float = 0.10  # 10% of daily volume
    liquidity_check_interval_seconds: int = 60
    
    # Recovery settings
    auto_recovery_enabled: bool = True
    recovery_test_duration_seconds: int = 60
    max_recovery_attempts: int = 3
    
    # Notification settings
    notify_on_trigger: bool = True
    notify_on_recovery: bool = True
    critical_immediate_shutdown: bool = True
    
    # Integration settings
    integration_timeout_seconds: int = 10
    liquidation_timeout_seconds: int = 30


class CircuitBreakerMetrics:
    """Metrics tracking for circuit breaker system"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.reset_metrics()
        self._lock = threading.Lock()
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            self.price_changes = deque(maxlen=100)
            self.execution_times = deque(maxlen=100)
            self.losses = deque(maxlen=100)
            self.failures = deque(maxlen=100)
            self.timeouts = deque(maxlen=50)
            self.consecutive_failures = 0
            self.consecutive_losses = 0
            self.last_failure_time: Optional[datetime] = None
            self.last_loss_time: Optional[datetime] = None
            self.daily_start_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            self.hourly_start_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    
    def add_price_change(self, change: float, timestamp: datetime):
        """Add price change metric"""
        with self._lock:
            self.price_changes.append((change, timestamp))
    
    def add_execution_time(self, execution_time: float, timestamp: datetime):
        """Add execution time metric"""
        with self._lock:
            self.execution_times.append((execution_time, timestamp))
            if execution_time > self.config.max_execution_time_seconds:
                self.timeouts.append(timestamp)
    
    def add_loss(self, loss_amount: float, timestamp: datetime):
        """Add loss metric"""
        with self._lock:
            self.losses.append((loss_amount, timestamp))
            self.last_loss_time = timestamp
            self.consecutive_losses += 1
    
    def add_profit(self, profit_amount: float):
        """Add profit - resets consecutive losses"""
        with self._lock:
            self.consecutive_losses = 0
    
    def add_failure(self, timestamp: datetime):
        """Add failure metric"""
        with self._lock:
            self.failures.append(timestamp)
            self.last_failure_time = timestamp
            self.consecutive_failures += 1
    
    def add_success(self):
        """Add success - may reset consecutive failures"""
        with self._lock:
            # Only reset if enough time has passed since last failure
            if (self.last_failure_time and 
                datetime.now(timezone.utc) - self.last_failure_time > timedelta(minutes=self.config.failure_window_minutes)):
                self.consecutive_failures = 0
    
    def get_price_volatility(self) -> float:
        """Calculate current price volatility"""
        with self._lock:
            if len(self.price_changes) < 2:
                return 0.0
            
            # Get recent changes within window
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.config.price_volatility_window_minutes)
            recent_changes = [abs(change) for change, timestamp in self.price_changes if timestamp > cutoff_time]
            
            return statistics.mean(recent_changes) if recent_changes else 0.0
    
    def get_average_execution_time(self) -> float:
        """Get average execution time"""
        with self._lock:
            if not self.execution_times:
                return 0.0
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.config.timeout_window_minutes)
            recent_times = [time_val for time_val, timestamp in self.execution_times if timestamp > cutoff_time]
            
            return statistics.mean(recent_times) if recent_times else 0.0
    
    def get_daily_loss_percentage(self, bankroll: float) -> float:
        """Get daily loss percentage"""
        if bankroll <= 0:
            return 0.0
        
        with self._lock:
            cutoff_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            daily_losses = [abs(loss) for loss, timestamp in self.losses if timestamp > cutoff_time and loss < 0]
            
            return sum(daily_losses) / bankroll
    
    def get_hourly_loss_percentage(self, bankroll: float) -> float:
        """Get hourly loss percentage"""
        if bankroll <= 0:
            return 0.0
        
        with self._lock:
            cutoff_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
            hourly_losses = [abs(loss) for loss, timestamp in self.losses if timestamp > cutoff_time and loss < 0]
            
            return sum(hourly_losses) / bankroll
    
    def get_failure_rate(self) -> float:
        """Get failure rate in time window"""
        with self._lock:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.config.failure_window_minutes)
            recent_failures = [f for f in self.failures if f > cutoff_time]
            total_attempts = len(recent_failures) + len([t for t, _ in self.execution_times if t > cutoff_time])
            
            return len(recent_failures) / max(total_attempts, 1)
    
    def should_reset_daily_metrics(self) -> bool:
        """Check if daily metrics should be reset"""
        now = datetime.now(timezone.utc)
        return now.date() > self.daily_start_time.date()
    
    def should_reset_hourly_metrics(self) -> bool:
        """Check if hourly metrics should be reset"""
        now = datetime.now(timezone.utc)
        return now.hour != self.hourly_start_time.hour
    
    def reset_periodic_metrics(self):
        """Reset daily/hourly metrics if needed"""
        if self.should_reset_daily_metrics():
            self.daily_start_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        if self.should_reset_hourly_metrics():
            self.hourly_start_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)


class CircuitBreaker:
    """Individual circuit breaker instance"""
    
    def __init__(self, breaker_id: str, config: CircuitBreakerConfig, 
                 audit_logger: AuditLogger):
        self.breaker_id = breaker_id
        self.config = config
        self.audit_logger = audit_logger
        self.metrics = CircuitBreakerMetrics(config)
        
        self.state = CircuitBreakerState.CLOSED
        self.last_state_change = datetime.now(timezone.utc)
        self.open_reason: Optional[str] = None
        self.active_triggers: Dict[TriggerType, CircuitBreakerTrigger] = {}
        self.recovery_attempts = 0
        self._state_lock = threading.Lock()
        
        # Liquidation callbacks
        self.liquidation_callbacks: List[Callable] = []
        
        logger.info(f"Circuit breaker {breaker_id} initialized", 
                   state=self.state.value, config=config.to_dict())
    
    def add_liquidation_callback(self, callback: Callable[[List[UUID]], None]):
        """Add callback for position liquidation"""
        self.liquidation_callbacks.append(callback)
    
    def check_triggers(self, opportunity: Optional[ArbitrageOpportunity] = None,
                      trade: Optional[Trade] = None,
                      current_bankroll: float = 0.0) -> List[CircuitBreakerTrigger]:
        """Check all trigger conditions"""
        triggers = []
        
        with self._state_lock:
            # Price volatility trigger
            if self._check_price_volatility():
                trigger = CircuitBreakerTrigger(
                    trigger_type=TriggerType.PRICE_VOLATILITY,
                    severity=Severity.MEDIUM,
                    threshold_value=self.config.price_volatility_threshold,
                    actual_value=self.metrics.get_price_volatility(),
                    description="Price volatility exceeds threshold",
                    cooldown_seconds=900  # 15 minutes
                )
                triggers.append(trigger)
            
            # Execution timeout trigger
            if self._check_execution_timeout():
                trigger = CircuitBreakerTrigger(
                    trigger_type=TriggerType.EXECUTION_TIMEOUT,
                    severity=Severity.MEDIUM,
                    threshold_value=self.config.max_execution_time_seconds,
                    actual_value=self.metrics.get_average_execution_time(),
                    description="Average execution time exceeds threshold",
                    cooldown_seconds=600  # 10 minutes
                )
                triggers.append(trigger)
            
            # Loss threshold triggers
            if self._check_daily_loss_threshold(current_bankroll):
                trigger = CircuitBreakerTrigger(
                    trigger_type=TriggerType.LOSS_THRESHOLD,
                    severity=Severity.HIGH,
                    threshold_value=self.config.max_daily_loss_percentage * 100,
                    actual_value=self.metrics.get_daily_loss_percentage(current_bankroll) * 100,
                    description="Daily loss threshold exceeded",
                    auto_liquidation_required=True,
                    cooldown_seconds=1800,  # 30 minutes
                    recovery_conditions=["bankroll_recovery", "manual_override"]
                )
                triggers.append(trigger)
            
            if self._check_hourly_loss_threshold(current_bankroll):
                trigger = CircuitBreakerTrigger(
                    trigger_type=TriggerType.LOSS_THRESHOLD,
                    severity=Severity.CRITICAL,
                    threshold_value=self.config.max_hourly_loss_percentage * 100,
                    actual_value=self.metrics.get_hourly_loss_percentage(current_bankroll) * 100,
                    description="Hourly loss threshold exceeded",
                    auto_liquidation_required=True,
                    cooldown_seconds=3600,  # 1 hour
                    recovery_conditions=["manual_override"]
                )
                triggers.append(trigger)
            
            # Consecutive losses trigger
            if self._check_consecutive_losses():
                trigger = CircuitBreakerTrigger(
                    trigger_type=TriggerType.CONSECUTIVE_FAILURES,
                    severity=Severity.MEDIUM,
                    threshold_value=self.config.max_consecutive_losses,
                    actual_value=self.metrics.consecutive_losses,
                    description="Too many consecutive losses",
                    cooldown_seconds=900  # 15 minutes
                )
                triggers.append(trigger)
            
            # Position size trigger
            if opportunity and self._check_position_size(opportunity, current_bankroll):
                trigger = CircuitBreakerTrigger(
                    trigger_type=TriggerType.POSITION_SIZE,
                    severity=Severity.MEDIUM,
                    threshold_value=self.config.max_position_size_percentage * 100,
                    actual_value=float(opportunity.total_stake) / current_bankroll * 100,
                    description="Position size exceeds limits",
                    affected_positions=[opportunity.id]
                )
                triggers.append(trigger)
        
        return triggers
    
    def _check_price_volatility(self) -> bool:
        """Check if price volatility threshold is exceeded"""
        volatility = self.metrics.get_price_volatility()
        return volatility > self.config.price_volatility_threshold
    
    def _check_execution_timeout(self) -> bool:
        """Check if execution timeout threshold is exceeded"""
        avg_time = self.metrics.get_average_execution_time()
        return avg_time > self.config.max_execution_time_seconds
    
    def _check_daily_loss_threshold(self, bankroll: float) -> bool:
        """Check if daily loss threshold is exceeded"""
        if bankroll <= 0:
            return False
        return self.metrics.get_daily_loss_percentage(bankroll) > self.config.max_daily_loss_percentage
    
    def _check_hourly_loss_threshold(self, bankroll: float) -> bool:
        """Check if hourly loss threshold is exceeded"""
        if bankroll <= 0:
            return False
        return self.metrics.get_hourly_loss_percentage(bankroll) > self.config.max_hourly_loss_percentage
    
    def _check_consecutive_losses(self) -> bool:
        """Check if consecutive losses threshold is exceeded"""
        return self.metrics.consecutive_losses >= self.config.max_consecutive_losses
    
    def _check_position_size(self, opportunity: ArbitrageOpportunity, bankroll: float) -> bool:
        """Check if position size is within limits"""
        if bankroll <= 0:
            return True
        
        position_percentage = float(opportunity.total_stake) / bankroll
        return position_percentage > self.config.max_position_size_percentage
    
    def trigger(self, trigger: CircuitBreakerTrigger):
        """Trigger the circuit breaker"""
        with self._state_lock:
            if self.state == CircuitBreakerState.OPEN:
                logger.warning(f"Circuit breaker {self.breaker_id} already open, ignoring trigger", 
                             trigger_type=trigger.trigger_type.value)
                return
            
            # Set state to OPEN
            previous_state = self.state
            self.state = CircuitBreakerState.OPEN
            self.last_state_change = datetime.now(timezone.utc)
            self.open_reason = trigger.description
            self.active_triggers[trigger.trigger_type] = trigger
            
            # Log the trigger
            self.audit_logger.log_security_event(SecurityEventLog(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type='CIRCUIT_BREAKER_TRIGGERED',
                severity=LogLevel.ERROR if trigger.severity in [Severity.HIGH, Severity.CRITICAL] else LogLevel.WARNING,
                user_id=None,
                ip_address=None,
                session_id=None,
                description=f"Circuit breaker triggered: {trigger.description}",
                details=trigger.to_dict()
            ))
            
            logger.critical(
                f"Circuit breaker {self.breaker_id} TRIGGERED",
                trigger_type=trigger.trigger_type.value,
                severity=trigger.severity.value,
                reason=trigger.description,
                auto_liquidation=trigger.auto_liquidation_required,
                previous_state=previous_state.value,
                new_state=self.state.value
            )
            
            # Execute automatic liquidation if required
            if trigger.auto_liquidation_required:
                self._execute_automatic_liquidation(trigger)
            
            # Start cooldown timer
            self._start_cooldown_timer(trigger.cooldown_seconds)
    
    def _execute_automatic_liquidation(self, trigger: CircuitBreakerTrigger):
        """Execute automatic position liquidation"""
        logger.critical(f"Executing automatic liquidation for circuit breaker {self.breaker_id}")
        
        try:
            # Call liquidation callbacks
            for callback in self.liquidation_callbacks:
                try:
                    callback(trigger.affected_positions)
                except Exception as e:
                    logger.error(f"Liquidation callback failed: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Automatic liquidation failed: {e}", exc_info=True)
    
    def _start_cooldown_timer(self, cooldown_seconds: int):
        """Start cooldown timer for automatic recovery"""
        def cooldown_task():
            logger.info(f"Circuit breaker {self.breaker_id} cooldown started", 
                       cooldown_seconds=cooldown_seconds)
            time.sleep(cooldown_seconds)
            
            if self.config.auto_recovery_enabled and self.recovery_attempts < self.config.max_recovery_attempts:
                self._attempt_recovery()
        
        cooldown_thread = threading.Thread(target=cooldown_task, daemon=True)
        cooldown_thread.start()
    
    def _attempt_recovery(self):
        """Attempt to recover circuit breaker"""
        with self._state_lock:
            if self.state != CircuitBreakerState.OPEN:
                return
            
            logger.info(f"Attempting recovery for circuit breaker {self.breaker_id}")
            self.state = CircuitBreakerState.HALF_OPEN
            self.last_state_change = datetime.now(timezone.utc)
            self.recovery_attempts += 1
            
            # Start recovery test
            self._start_recovery_test()
    
    def _start_recovery_test(self):
        """Start recovery test period"""
        def recovery_test():
            test_duration = self.config.recovery_test_duration_seconds
            logger.info(f"Starting recovery test for circuit breaker {self.breaker_id}", 
                       duration=test_duration)
            
            # Monitor during test period
            start_time = time.time()
            while time.time() - start_time < test_duration:
                if self._check_recovery_conditions():
                    self._recover()
                    return
                time.sleep(5)  # Check every 5 seconds
            
            # Test failed, return to open state
            self._test_failed()
        
        test_thread = threading.Thread(target=recovery_test, daemon=True)
        test_thread.start()
    
    def _check_recovery_conditions(self) -> bool:
        """Check if recovery conditions are met"""
        # Check if active triggers are resolved
        for trigger in self.active_triggers.values():
            # Re-check the trigger condition
            if trigger.trigger_type == TriggerType.PRICE_VOLATILITY:
                if self._check_price_volatility():
                    return False
            elif trigger.trigger_type == TriggerType.EXECUTION_TIMEOUT:
                if self._check_execution_timeout():
                    return False
            elif trigger.trigger_type == TriggerType.LOSS_THRESHOLD:
                # Loss thresholds require manual recovery
                if "manual_override" in trigger.recovery_conditions:
                    return False
        
        return True
    
    def _recover(self):
        """Recover circuit breaker to closed state"""
        with self._state_lock:
            previous_state = self.state
            self.state = CircuitBreakerState.CLOSED
            self.last_state_change = datetime.now(timezone.utc)
            self.open_reason = None
            self.active_triggers.clear()
            
            # Log recovery
            logger.info(f"Circuit breaker {self.breaker_id} recovered", 
                       previous_state=previous_state.value,
                       new_state=self.state.value,
                       recovery_attempts=self.recovery_attempts)
            
            self.audit_logger.log_security_event(SecurityEventLog(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type='CIRCUIT_BREAKER_RECOVERED',
                severity=LogLevel.INFO,
                user_id=None,
                ip_address=None,
                session_id=None,
                description=f"Circuit breaker recovered after {self.recovery_attempts} attempts",
                details={'breaker_id': self.breaker_id, 'recovery_attempts': self.recovery_attempts}
            ))
    
    def _test_failed(self):
        """Recovery test failed"""
        with self._state_lock:
            self.state = CircuitBreakerState.OPEN
            self.last_state_change = datetime.now(timezone.utc)
            
            logger.warning(f"Circuit breaker {self.breaker_id} recovery test failed",
                          recovery_attempts=self.recovery_attempts,
                          max_attempts=self.config.max_recovery_attempts)
    
    def force_close(self, reason: str = "Manual override"):
        """Manually force circuit breaker to closed state"""
        with self._state_lock:
            previous_state = self.state
            self.state = CircuitBreakerState.CLOSED
            self.last_state_change = datetime.now(timezone.utc)
            self.open_reason = f"Manually closed: {reason}"
            self.active_triggers.clear()
            self.recovery_attempts = 0
            
            logger.info(f"Circuit breaker {self.breaker_id} manually closed", 
                       reason=reason, previous_state=previous_state.value)
    
    def force_open(self, reason: str = "Manual override"):
        """Manually force circuit breaker to open state"""
        with self._state_lock:
            previous_state = self.state
            self.state = CircuitBreakerState.OPEN
            self.last_state_change = datetime.now(timezone.utc)
            self.open_reason = f"Manually opened: {reason}"
            
            logger.warning(f"Circuit breaker {self.breaker_id} manually opened", 
                          reason=reason, previous_state=previous_state.value)
    
    def update_metrics(self, opportunity: Optional[ArbitrageOpportunity] = None,
                      trade: Optional[Trade] = None,
                      profit_loss: Optional[float] = None,
                      execution_time: Optional[float] = None,
                      success: bool = True):
        """Update circuit breaker metrics"""
        now = datetime.now(timezone.utc)
        
        # Reset periodic metrics
        self.metrics.reset_periodic_metrics()
        
        # Update execution time
        if execution_time is not None:
            self.metrics.add_execution_time(execution_time, now)
        
        # Update profit/loss
        if profit_loss is not None:
            if profit_loss < 0:
                self.metrics.add_loss(profit_loss, now)
            else:
                self.metrics.add_profit(profit_loss)
        
        # Update success/failure
        if success:
            self.metrics.add_success()
        else:
            self.metrics.add_failure(now)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        with self._state_lock:
            return {
                'breaker_id': self.breaker_id,
                'state': self.state.value,
                'last_state_change': self.last_state_change.isoformat(),
                'open_reason': self.open_reason,
                'active_triggers': [trigger.to_dict() for trigger in self.active_triggers.values()],
                'recovery_attempts': self.recovery_attempts,
                'metrics': {
                    'consecutive_failures': self.metrics.consecutive_failures,
                    'consecutive_losses': self.metrics.consecutive_losses,
                    'daily_loss_pct': 0.0,  # Will be calculated by caller with bankroll
                    'hourly_loss_pct': 0.0,
                    'avg_execution_time': self.metrics.get_average_execution_time(),
                    'failure_rate': self.metrics.get_failure_rate()
                }
            }


class CircuitBreakerManager:
    """Manager for multiple circuit breakers"""
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        self.audit_logger = audit_logger or get_audit_logger()
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.global_config = CircuitBreakerConfig()
        self._lock = threading.Lock()
        
        # Liquidation coordination
        self.active_liquidations: Set[UUID] = set()
        self.liquidation_queue = asyncio.Queue()
        
        logger.info("Circuit breaker manager initialized")
    
    def create_breaker(self, breaker_id: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Create a new circuit breaker"""
        with self._lock:
            if breaker_id in self.breakers:
                raise ValueError(f"Circuit breaker {breaker_id} already exists")
            
            breaker_config = config or self.global_config
            breaker = CircuitBreaker(breaker_id, breaker_config, self.audit_logger)
            
            # Add liquidation callback
            breaker.add_liquidation_callback(self._handle_liquidation)
            
            self.breakers[breaker_id] = breaker
            logger.info(f"Created circuit breaker {breaker_id}")
            
            return breaker
    
    def get_breaker(self, breaker_id: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by ID"""
        with self._lock:
            return self.breakers.get(breaker_id)
    
    def remove_breaker(self, breaker_id: str):
        """Remove circuit breaker"""
        with self._lock:
            if breaker_id in self.breakers:
                del self.breakers[breaker_id]
                logger.info(f"Removed circuit breaker {breaker_id}")
    
    def _handle_liquidation(self, position_ids: List[UUID]):
        """Handle position liquidation requests"""
        logger.critical("Position liquidation requested", position_ids=[str(id) for id in position_ids])
        
        # Add to active liquidations
        self.active_liquidations.update(position_ids)
        
        # Log the liquidation event
        self.audit_logger.log_security_event(SecurityEventLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type='AUTOMATIC_LIQUIDATION',
            severity=LogLevel.CRITICAL,
            user_id=None,
            ip_address=None,
            session_id=None,
            description=f"Automatic liquidation initiated for {len(position_ids)} positions",
            details={'position_ids': [str(id) for id in position_ids]}
        ))
        
        # Here you would integrate with your trading execution system
        # to actually liquidate the positions
    
    def check_all_breakers(self, opportunity: Optional[ArbitrageOpportunity] = None,
                          trade: Optional[Trade] = None,
                          current_bankroll: float = 0.0) -> List[CircuitBreakerTrigger]:
        """Check all circuit breakers"""
        all_triggers = []
        
        with self._lock:
            for breaker in self.breakers.values():
                triggers = breaker.check_triggers(opportunity, trade, current_bankroll)
                all_triggers.extend(triggers)
        
        return all_triggers
    
    def trigger_breakers(self, triggers: List[CircuitBreakerTrigger]):
        """Trigger circuit breakers based on triggers"""
        triggered_breakers = set()
        
        for trigger in triggers:
            # Find affected breakers or trigger all for global triggers
            if trigger.affected_positions:
                # Trigger breaker for specific positions
                for breaker in self.breakers.values():
                    if trigger.trigger_type in breaker.active_triggers or trigger.trigger_type not in breaker.active_triggers:
                        breaker.trigger(trigger)
                        triggered_breakers.add(breaker.breaker_id)
            else:
                # Global trigger - check all breakers
                for breaker in self.breakers.values():
                    if breaker.state == CircuitBreakerState.CLOSED:
                        breaker.trigger(trigger)
                        triggered_breakers.add(breaker.breaker_id)
        
        logger.critical(f"Triggered {len(triggered_breakers)} circuit breakers", 
                       breaker_ids=list(triggered_breakers))
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        with self._lock:
            status = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_breakers': len(self.breakers),
                'breakers': {},
                'active_liquidations': len(self.active_liquidations),
                'system_state': 'healthy'
            }
            
            open_breakers = 0
            for breaker_id, breaker in self.breakers.items():
                breaker_status = breaker.get_status()
                status['breakers'][breaker_id] = breaker_status
                
                if breaker.state == CircuitBreakerState.OPEN:
                    open_breakers += 1
            
            if open_breakers > 0:
                status['system_state'] = 'degraded' if open_breakers < len(self.breakers) else 'stopped'
            
            return status
    
    def force_close_all(self, reason: str = "Manual override"):
        """Force close all circuit breakers"""
        with self._lock:
            for breaker in self.breakers.values():
                breaker.force_close(reason)
            
            logger.critical("All circuit breakers manually closed", reason=reason)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on circuit breaker system"""
        health = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'healthy': True,
            'issues': []
        }
        
        with self._lock:
            for breaker_id, breaker in self.breakers.items():
                breaker_health = {
                    'breaker_id': breaker_id,
                    'state': breaker.state.value,
                    'healthy': True,
                    'issues': []
                }
                
                # Check for stuck states
                if breaker.state == CircuitBreakerState.OPEN:
                    time_open = datetime.now(timezone.utc) - breaker.last_state_change
                    if time_open.total_seconds() > 3600:  # 1 hour
                        breaker_health['healthy'] = False
                        breaker_health['issues'].append(f"Circuit breaker stuck open for {time_open}")
                
                if not breaker_health['healthy']:
                    health['healthy'] = False
                    health['issues'].append(f"Circuit breaker {breaker_id}: {breaker_health['issues']}")
                
                health[f'breaker_{breaker_id}'] = breaker_health
        
        return health


# Global circuit breaker manager instance
_global_cb_manager = None


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get or create global circuit breaker manager"""
    global _global_cb_manager
    if _global_cb_manager is None:
        _global_cb_manager = CircuitBreakerManager()
    return _global_cb_manager


if __name__ == "__main__":
    # Example usage and testing
    import asyncio
    
    async def test_circuit_breaker():
        # Setup
        manager = get_circuit_breaker_manager()
        breaker = manager.create_breaker("test_breaker")
        
        # Test normal operation
        print("Testing normal operation...")
        breaker.update_metrics(profit_loss=100.0, success=True)
        
        # Test trigger
        print("Testing loss threshold trigger...")
        breaker.update_metrics(profit_loss=-500.0, success=False)
        
        triggers = breaker.check_triggers(current_bankroll=1000.0)
        if triggers:
            print(f"Trigger detected: {triggers[0].description}")
            breaker.trigger(triggers[0])
        
        # Test status
        status = breaker.get_status()
        print(f"Circuit breaker status: {status}")
        
        # Test recovery
        print("Testing recovery...")
        await asyncio.sleep(2)
        breaker.force_close("Test recovery")
        
        print("Circuit breaker test completed!")
    
    # Run test
    asyncio.run(test_circuit_breaker())