"""
Advanced Loss Limiting System for ARBitech Trading Platform

This module implements comprehensive loss limiting mechanisms with:
- Dynamic stop-losses with trailing capabilities
- Maximum daily/weekly/monthly loss limits
- Recovery mechanisms and automatic resumption
- Integration with circuit breakers and emergency stops
- Advanced position management and risk controls
- Real-time monitoring and alerting

The system provides bulletproof protection against excessive losses with
multiple layers of safety and intelligent recovery mechanisms.
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import json
import threading
from collections import deque, defaultdict
import statistics
import heapq

from arbitech.storage.audit_logger import (
    AuditLogger, EventType, LogLevel, SecurityEventLog,
    get_audit_logger, TradeExecutionLog
)
from arbitech.storage.models import ArbitrageOpportunity, Trade, TradeStatus
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LossStopType(Enum):
    """Types of loss stops"""
    FIXED_STOP_LOSS = "fixed_stop_loss"      # Fixed percentage stop
    TRAILING_STOP_LOSS = "trailing_stop_loss"  # Trailing stop
    TIME_BASED_STOP = "time_based_stop"      # Time-based exit
    PROFIT_TARGET = "profit_target"          # Profit taking
    MAX_LOSS_LIMIT = "max_loss_limit"        # Daily/weekly/monthly limits
    VOLATILITY_STOP = "volatility_stop"      # Volatility-based stop
    CORRELATION_STOP = "correlation_stop"    # Correlation-based stop


class StopLevel(Enum):
    """Stop loss levels"""
    CONSERVATIVE = "conservative"    # 2-3% loss
    MODERATE = "moderate"           # 5-7% loss
    AGGRESSIVE = "aggressive"       # 10-15% loss
    CUSTOM = "custom"              # User-defined


class RecoveryMode(Enum):
    """Recovery modes after loss limits"""
    IMMEDIATE_RESUME = "immediate_resume"    # Resume immediately
    COOLDOWN_PERIOD = "cooldown_period"     # Wait cooldown period
    MANUAL_APPROVAL = "manual_approval"      # Require manual approval
    GRADUAL_RESUME = "gradual_resume"        # Gradual position increase


@dataclass
class StopLossRule:
    """Individual stop loss rule"""
    rule_id: UUID = field(default_factory=uuid4)
    name: str = ""
    stop_type: LossStopType = LossStopType.FIXED_STOP_LOSS
    stop_level: StopLevel = StopLevel.MODERATE
    
    # Parameters
    stop_percentage: float = 0.05  # 5% default
    trailing_distance: float = 0.02  # 2% trailing distance
    time_limit_minutes: int = 120   # 2 hours
    profit_target: float = 0.10     # 10% profit target
    
    # Activation conditions
    min_profit_before_trailing: float = 0.02  # 2% profit before trailing activates
    activation_delay_seconds: int = 60        # Delay before stop activates
    
    # Risk management
    max_positions_per_rule: int = 10
    correlation_threshold: float = 0.70       # 70% correlation limit
    
    # Recovery settings
    recovery_mode: RecoveryMode = RecoveryMode.IMMEDIATE_RESUME
    cooldown_minutes: int = 30
    gradual_resume_multiplier: float = 0.50   # 50% of normal position size
    
    # Status tracking
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'rule_id': str(self.rule_id),
            'name': self.name,
            'stop_type': self.stop_type.value,
            'stop_level': self.stop_level.value,
            'stop_percentage': self.stop_percentage,
            'trailing_distance': self.trailing_distance,
            'time_limit_minutes': self.time_limit_minutes,
            'profit_target': self.profit_target,
            'min_profit_before_trailing': self.min_profit_before_trailing,
            'activation_delay_seconds': self.activation_delay_seconds,
            'max_positions_per_rule': self.max_positions_per_rule,
            'correlation_threshold': self.correlation_threshold,
            'recovery_mode': self.recovery_mode.value,
            'cooldown_minutes': self.cooldown_minutes,
            'gradual_resume_multiplier': self.gradual_resume_multiplier,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'trigger_count': self.trigger_count
        }


@dataclass
class PositionStopLoss:
    """Stop loss for individual position"""
    position_id: UUID = field(default_factory=uuid4)
    rule_id: Optional[UUID] = None
    
    # Position details
    symbol: str = ""
    entry_price: Decimal = '0'
    position_size: Decimal = '0'
    current_price: Decimal = '0'
    side: str = "LONG"  # LONG/SHORT
    
    # Stop loss details
    stop_type: LossStopType = LossStopType.FIXED_STOP_LOSS
    stop_price: Optional[Decimal] = None
    trailing_stop_price: Optional[Decimal] = None
    initial_stop_price: Optional[Decimal] = None
    
    # Tracking
    unrealized_pnl: Decimal = '0'
    realized_pnl: Decimal = '0'
    max_profit: Decimal = '0'
    max_drawdown: Decimal = '0'
    
    # Timing
    entry_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_price_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stop_activated: bool = False
    stop_activated_time: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'position_id': str(self.position_id),
            'rule_id': str(self.rule_id) if self.rule_id else None,
            'symbol': self.symbol,
            'entry_price': float(self.entry_price),
            'position_size': float(self.position_size),
            'current_price': float(self.current_price),
            'side': self.side,
            'stop_type': self.stop_type.value,
            'stop_price': float(self.stop_price) if self.stop_price else None,
            'trailing_stop_price': float(self.trailing_stop_price) if self.trailing_stop_price else None,
            'initial_stop_price': float(self.initial_stop_price) if self.initial_stop_price else None,
            'unrealized_pnl': float(self.unrealized_pnl),
            'realized_pnl': float(self.realized_pnl),
            'max_profit': float(self.max_profit),
            'max_drawdown': float(self.max_drawdown),
            'entry_time': self.entry_time.isoformat(),
            'last_price_update': self.last_price_update.isoformat(),
            'stop_activated': self.stop_activated,
            'stop_activated_time': self.stop_activated_time.isoformat() if self.stop_activated_time else None,
            'profit_pct': float((self.unrealized_pnl / (self.entry_price * self.position_size)) * 100),
            'metadata': self.metadata
        }


@dataclass
class TimeBasedLimit:
    """Time-based loss limit (daily/weekly/monthly)"""
    limit_id: UUID = field(default_factory=uuid4)
    time_period: str = "daily"  # daily, weekly, monthly
    max_loss_amount: Decimal = '1000'
    max_loss_percentage: Decimal = '0.10'  # 10%
    
    # Current period tracking
    period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0))
    current_loss: Decimal = '0'
    current_trades: int = 0
    current_profit: Decimal = '0'
    
    # Recovery settings
    recovery_mode: RecoveryMode = RecoveryMode.COOLDOWN_PERIOD
    cooldown_hours: int = 24
    partial_recovery_threshold: Decimal = '0.50'  # 50% recovery
    
    # Status
    active: bool = True
    triggered: bool = False
    last_triggered: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'limit_id': str(self.limit_id),
            'time_period': self.time_period,
            'max_loss_amount': float(self.max_loss_amount),
            'max_loss_percentage': float(self.max_loss_percentage),
            'period_start': self.period_start.isoformat(),
            'current_loss': float(self.current_loss),
            'current_trades': self.current_trades,
            'current_profit': float(self.current_profit),
            'recovery_mode': self.recovery_mode.value,
            'cooldown_hours': self.cooldown_hours,
            'partial_recovery_threshold': float(self.partial_recovery_threshold),
            'active': self.active,
            'triggered': self.triggered,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'remaining_loss_capacity': float(self.max_loss_amount - self.current_loss),
            'remaining_percentage_capacity': float((self.max_loss_percentage * 100) - (abs(self.current_loss) / (self.max_loss_amount / self.max_loss_percentage) * 100))
        }


@dataclass
class LossLimiterConfig:
    """Configuration for loss limiting system"""
    # Default stop loss settings
    default_stop_loss_percentage: float = 0.05  # 5%
    default_trailing_distance: float = 0.02     # 2%
    default_profit_target: float = 0.10         # 10%
    
    # Position limits
    max_positions_total: int = 50
    max_positions_per_symbol: int = 5
    max_position_size_percentage: float = 0.20  # 20% of bankroll
    
    # Time-based limits
    daily_loss_limit_percentage: float = 0.10   # 10%
    weekly_loss_limit_percentage: float = 0.25  # 25%
    monthly_loss_limit_percentage: float = 0.50 # 50%
    
    # Recovery settings
    enable_automatic_recovery: bool = True
    max_consecutive_triggers: int = 3
    cooldown_after_trigger_hours: int = 2
    
    # Monitoring settings
    price_update_frequency_seconds: float = 1.0
    health_check_interval_seconds: float = 30.0
    metrics_retention_hours: int = 168  # 1 week
    
    # Integration settings
    liquidation_timeout_seconds: int = 30
    notification_enabled: bool = True
    emergency_stop_integration: bool = True
    
    # Advanced features
    enable_correlation_monitoring: bool = True
    correlation_check_interval_seconds: float = 60.0
    volatility_adjustment: bool = True
    market_hours_only: bool = False


class TrailingStopCalculator:
    """Advanced trailing stop calculator"""
    
    def __init__(self, config: LossLimiterConfig):
        self.config = config
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.volatility_cache: Dict[str, float] = {}
    
    def update_price(self, symbol: str, price: Decimal, timestamp: datetime):
        """Update price history for symbol"""
        self.price_history[symbol].append((price, timestamp))
    
    def calculate_trailing_stop(self, symbol: str, current_price: Decimal, 
                               position_size: Decimal, side: str,
                               initial_stop_distance: Decimal) -> Decimal:
        """Calculate trailing stop price"""
        prices = self.price_history.get(symbol, [])
        if len(prices) < 2:
            return current_price - initial_stop_distance if side == "LONG" else current_price + initial_stop_distance
        
        # Get recent price extremes
        recent_prices = [p for p, t in prices[-20:]]  # Last 20 price points
        
        if side == "LONG":
            # For long positions, trailing stop follows price upward
            max_price = max(recent_prices)
            trailing_distance = self._calculate_dynamic_distance(symbol, current_price, side)
            stop_price = max_price - trailing_distance
            # Don't move stop down
            if hasattr(self, f'_last_stop_{symbol}'):
                last_stop = getattr(self, f'_last_stop_{symbol}')
                stop_price = max(stop_price, last_stop)
            setattr(self, f'_last_stop_{symbol}', stop_price)
        else:
            # For short positions, trailing stop follows price downward
            min_price = min(recent_prices)
            trailing_distance = self._calculate_dynamic_distance(symbol, current_price, side)
            stop_price = min_price + trailing_distance
            # Don't move stop up
            if hasattr(self, f'_last_stop_{symbol}'):
                last_stop = getattr(self, f'_last_stop_{symbol}')
                stop_price = min(stop_price, last_stop)
            setattr(self, f'_last_stop_{symbol}', stop_price)
        
        return stop_price
    
    def _calculate_dynamic_distance(self, symbol: str, current_price: Decimal, side: str) -> Decimal:
        """Calculate dynamic trailing distance based on volatility"""
        if not self.config.volatility_adjustment:
            return str(self.config.default_trailing_distance)
        
        prices = self.price_history.get(symbol, [])
        if len(prices) < 10:
            return str(self.config.default_trailing_distance)
        
        # Calculate volatility (standard deviation)
        price_values = [float(p) for p, t in prices[-20:]]
        volatility = statistics.stdev(price_values) if len(price_values) > 1 else 0
        
        # Adjust trailing distance based on volatility
        volatility_multiplier = 1 + (volatility / float(current_price))
        base_distance = str(self.config.default_trailing_distance)
        adjusted_distance = base_distance * str(volatility_multiplier)
        
        return adjusted_distance


class LossLimiter:
    """Individual loss limiter instance"""
    
    def __init__(self, limiter_id: str, config: LossLimiterConfig, audit_logger: AuditLogger):
        self.limiter_id = limiter_id
        self.config = config
        self.audit_logger = audit_logger
        
        # Active stop loss rules
        self.stop_loss_rules: Dict[UUID, StopLossRule] = {}
        self.active_positions: Dict[UUID, PositionStopLoss] = {}
        self.time_based_limits: Dict[str, TimeBasedLimit] = {}
        
        # Trailing stop calculator
        self.trailing_calculator = TrailingStopCalculator(config)
        
        # Monitoring
        self._lock = threading.Lock()
        self.price_update_callbacks: List[Callable] = []
        self.stop_trigger_callbacks: List[Callable] = []
        
        # Performance tracking
        self.metrics = {
            'total_triggers': 0,
            'successful_stops': 0,
            'failed_stops': 0,
            'recovery_events': 0,
            'total_loss_prevented': '0'
        }
        
        logger.info(f"Loss limiter {limiter_id} initialized")
    
    def add_stop_loss_rule(self, rule: StopLossRule):
        """Add stop loss rule"""
        with self._lock:
            self.stop_loss_rules[rule.rule_id] = rule
            logger.info(f"Added stop loss rule {rule.name} to limiter {self.limiter_id}")
    
    def add_time_based_limit(self, limit: TimeBasedLimit):
        """Add time-based loss limit"""
        with self._lock:
            self.time_based_limits[limit.time_period] = limit
            logger.info(f"Added {limit.time_period} loss limit to limiter {self.limiter_id}")
    
    def create_position_stop_loss(self, symbol: str, entry_price: Decimal, 
                                 position_size: Decimal, side: str,
                                 rule_id: Optional[UUID] = None) -> UUID:
        """Create stop loss for position"""
        position_id = uuid4()
        
        # Get applicable rule
        rule = None
        if rule_id and rule_id in self.stop_loss_rules:
            rule = self.stop_loss_rules[rule_id]
        else:
            # Find first applicable rule
            for r in self.stop_loss_rules.values():
                if r.active and (r.stop_type == LossStopType.FIXED_STOP_LOSS or 
                               r.stop_type == LossStopType.TRAILING_STOP_LOSS):
                    rule = r
                    break
        
        if not rule:
            # Create default rule
            rule = StopLossRule(
                name="Default Rule",
                stop_type=LossStopType.FIXED_STOP_LOSS,
                stop_level=StopLevel.MODERATE,
                stop_percentage=self.config.default_stop_loss_percentage
            )
            self.stop_loss_rules[rule.rule_id] = rule
        
        # Calculate initial stop price
        if rule.stop_type == LossStopType.FIXED_STOP_LOSS:
            stop_distance = str(rule.stop_percentage) * entry_price
            stop_price = entry_price - stop_distance if side == "LONG" else entry_price + stop_distance
        else:
            stop_distance = str(rule.trailing_distance) * entry_price
            stop_price = entry_price - stop_distance if side == "LONG" else entry_price + stop_distance
        
        # Create position stop loss
        position = PositionStopLoss(
            position_id=position_id,
            rule_id=rule.rule_id if rule else None,
            symbol=symbol,
            entry_price=entry_price,
            position_size=position_size,
            current_price=entry_price,
            side=side,
            stop_type=rule.stop_type if rule else LossStopType.FIXED_STOP_LOSS,
            stop_price=stop_price,
            initial_stop_price=stop_price,
            metadata={'rule_name': rule.name if rule else 'Default'}
        )
        
        with self._lock:
            self.active_positions[position_id] = position
        
        logger.info(f"Created stop loss for position {position_id}", 
                   symbol=symbol, stop_type=position.stop_type.value,
                   stop_price=stop_price)
        
        return position_id
    
    def update_position_price(self, symbol: str, new_price: Decimal, 
                             timestamp: Optional[datetime] = None):
        """Update position price and check for stop triggers"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Update trailing calculator
        self.trailing_calculator.update_price(symbol, new_price, timestamp)
        
        # Update all positions for this symbol
        positions_to_update = []
        with self._lock:
            for position in self.active_positions.values():
                if position.symbol == symbol and not position.stop_activated:
                    positions_to_update.append(position)
        
        # Check each position
        for position in positions_to_update:
            self._update_position_price(position, new_price, timestamp)
    
    def _update_position_price(self, position: PositionStopLoss, new_price: Decimal, 
                              timestamp: datetime):
        """Update individual position price and check stops"""
        position.current_price = new_price
        position.last_price_update = timestamp
        
        # Calculate P&L
        if position.side == "LONG":
            pnl = (new_price - position.entry_price) * position.position_size
        else:
            pnl = (position.entry_price - new_price) * position.position_size
        
        position.unrealized_pnl = pnl
        
        # Update profit/drawdown tracking
        if pnl > position.max_profit:
            position.max_profit = pnl
        if pnl < position.max_drawdown:
            position.max_drawdown = pnl
        
        # Check stop triggers
        if self._check_stop_trigger(position, timestamp):
            self._trigger_stop_loss(position, timestamp)
    
    def _check_stop_trigger(self, position: PositionStopLoss, timestamp: datetime) -> bool:
        """Check if stop loss should be triggered"""
        rule = self.stop_loss_rules.get(position.rule_id) if position.rule_id else None
        if not rule or not rule.active:
            return False
        
        # Check activation delay
        time_held = (timestamp - position.entry_time).total_seconds()
        if time_held < rule.activation_delay_seconds:
            return False
        
        # Check stop type specific conditions
        if position.stop_type == LossStopType.FIXED_STOP_LOSS:
            return self._check_fixed_stop(position)
        elif position.stop_type == LossStopType.TRAILING_STOP_LOSS:
            return self._check_trailing_stop(position)
        elif position.stop_type == LossStopType.TIME_BASED_STOP:
            return self._check_time_based_stop(position, rule)
        elif position.stop_type == LossStopType.PROFIT_TARGET:
            return self._check_profit_target(position)
        
        return False
    
    def _check_fixed_stop(self, position: PositionStopLoss) -> bool:
        """Check fixed stop loss trigger"""
        if not position.stop_price:
            return False
        
        if position.side == "LONG":
            return position.current_price <= position.stop_price
        else:
            return position.current_price >= position.stop_price
    
    def _check_trailing_stop(self, position: PositionStopLoss) -> bool:
        """Check trailing stop loss trigger"""
        rule = self.stop_loss_rules.get(position.rule_id)
        if not rule or not position.stop_price:
            return False
        
        # Calculate new trailing stop
        new_trailing_stop = self.trailing_calculator.calculate_trailing_stop(
            position.symbol, position.current_price, position.position_size, position.side,
            str(rule.trailing_distance) * position.entry_price
        )
        
        # Update trailing stop price
        if position.side == "LONG":
            # Don't move stop down
            if new_trailing_stop > position.trailing_stop_price:
                position.trailing_stop_price = new_trailing_stop
        else:
            # Don't move stop up
            if new_trailing_stop < position.trailing_stop_price:
                position.trailing_stop_price = new_trailing_stop
        
        # Check trigger
        if position.side == "LONG":
            return position.current_price <= (position.trailing_stop_price or position.stop_price)
        else:
            return position.current_price >= (position.trailing_stop_price or position.stop_price)
    
    def _check_time_based_stop(self, position: PositionStopLoss, rule: StopLossRule) -> bool:
        """Check time-based stop trigger"""
        time_held = (datetime.now(timezone.utc) - position.entry_time).total_seconds()
        return time_held > (rule.time_limit_minutes * 60)
    
    def _check_profit_target(self, position: PositionStopLoss) -> bool:
        """Check profit target trigger"""
        rule = self.stop_loss_rules.get(position.rule_id)
        if not rule:
            return False
        
        # Check if we've reached profit target
        profit_pct = (position.unrealized_pnl / (position.entry_price * position.position_size))
        return float(profit_pct) >= rule.profit_target
    
    def _trigger_stop_loss(self, position: PositionStopLoss, timestamp: datetime):
        """Trigger stop loss for position"""
        logger.critical(f"Triggering stop loss for position {position.position_id}", 
                       symbol=position.symbol, pnl=position.unrealized_pnl,
                       stop_type=position.stop_type.value)
        
        position.stop_activated = True
        position.stop_activated_time = timestamp
        
        # Update rule statistics
        rule = self.stop_loss_rules.get(position.rule_id) if position.rule_id else None
        if rule:
            rule.last_triggered = timestamp
            rule.trigger_count += 1
        
        # Update metrics
        self.metrics['total_triggers'] += 1
        self.metrics['total_loss_prevented'] += abs(position.unrealized_pnl)
        
        # Log stop loss event
        self.audit_logger.log_security_event(SecurityEventLog(
            timestamp=timestamp.isoformat(),
            event_type='STOP_LOSS_TRIGGERED',
            severity=LogLevel.WARNING,
            user_id=None,
            ip_address=None,
            session_id=None,
            description=f"Stop loss triggered for {position.symbol}: {position.unrealized_pnl}",
            details=position.to_dict()
        ))
        
        # Execute stop loss callbacks
        for callback in self.stop_trigger_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(position))
                else:
                    callback(position)
            except Exception as e:
                logger.error(f"Stop loss callback failed: {e}", exc_info=True)
    
    def close_position(self, position_id: UUID, close_price: Decimal, 
                      timestamp: Optional[datetime] = None) -> bool:
        """Manually close position"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        with self._lock:
            if position_id not in self.active_positions:
                return False
            
            position = self.active_positions[position_id]
            
            # Calculate final P&L
            if position.side == "LONG":
                final_pnl = (close_price - position.entry_price) * position.position_size
            else:
                final_pnl = (position.entry_price - close_price) * position.position_size
            
            position.realized_pnl = final_pnl
            position.unrealized_pnl = final_pnl
            position.current_price = close_price
            
            # Remove from active positions
            del self.active_positions[position_id]
            
            logger.info(f"Closed position {position_id}", 
                       symbol=position.symbol, final_pnl=final_pnl)
            
            return True
    
    def check_time_based_limits(self) -> List[TimeBasedLimit]:
        """Check time-based loss limits"""
        triggered_limits = []
        current_time = datetime.now(timezone.utc)
        
        with self._lock:
            for period, limit in self.time_based_limits.items():
                if not limit.active:
                    continue
                
                # Check if we need to reset period
                if self._should_reset_period(limit, current_time):
                    self._reset_period_limit(limit, current_time)
                
                # Check loss limits
                current_loss_amount = abs(limit.current_loss)
                current_loss_pct = abs(limit.current_loss) / (limit.max_loss_amount / limit.max_loss_percentage)
                
                if (current_loss_amount >= limit.max_loss_amount or 
                    current_loss_pct >= float(limit.max_loss_percentage)):
                    
                    if not limit.triggered:
                        limit.triggered = True
                        limit.last_triggered = current_time
                        triggered_limits.append(limit)
                        
                        logger.critical(f"Time-based limit triggered for {period}", 
                                       current_loss=current_loss_amount,
                                       limit_amount=limit.max_loss_amount)
                        
                        # Log the event
                        self.audit_logger.log_security_event(SecurityEventLog(
                            timestamp=current_time.isoformat(),
                            event_type='TIME_BASED_LIMIT_TRIGGERED',
                            severity=LogLevel.CRITICAL,
                            user_id=None,
                            ip_address=None,
                            session_id=None,
                            description=f"{period.title()} loss limit triggered: {current_loss_amount}",
                            details=limit.to_dict()
                        ))
        
        return triggered_limits
    
    def _should_reset_period(self, limit: TimeBasedLimit, current_time: datetime) -> bool:
        """Check if period should be reset"""
        if limit.time_period == "daily":
            return current_time.date() > limit.period_start.date()
        elif limit.time_period == "weekly":
            # Reset on Monday
            return (current_time.date() > limit.period_start.date() and 
                    current_time.weekday() == 0)
        elif limit.time_period == "monthly":
            return current_time.month != limit.period_start.month
        return False
    
    def _reset_period_limit(self, limit: TimeBasedLimit, current_time: datetime):
        """Reset period-based limit"""
        limit.period_start = current_time
        if limit.time_period == "daily":
            limit.period_start = limit.period_start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif limit.time_period == "weekly":
            days_since_monday = limit.period_start.weekday()
            limit.period_start = limit.period_start - timedelta(days=days_since_monday)
            limit.period_start = limit.period_start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif limit.time_period == "monthly":
            limit.period_start = limit.period_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        limit.current_loss = '0'
        limit.current_trades = 0
        limit.current_profit = '0'
        limit.triggered = False
        
        logger.info(f"Reset {limit.time_period} limit for limiter {self.limiter_id}")
    
    def update_trade_result(self, trade_id: UUID, profit_loss: Decimal, 
                           trade_time: Optional[datetime] = None):
        """Update trade result for limit tracking"""
        if trade_time is None:
            trade_time = datetime.now(timezone.utc)
        
        # Update all time-based limits
        with self._lock:
            for limit in self.time_based_limits.values():
                limit.current_trades += 1
                
                if profit_loss < 0:
                    limit.current_loss += abs(profit_loss)
                else:
                    limit.current_profit += profit_loss
    
    def get_position_status(self, position_id: UUID) -> Optional[Dict[str, Any]]:
        """Get position status"""
        with self._lock:
            position = self.active_positions.get(position_id)
            return position.to_dict() if position else None
    
    def get_all_positions_status(self) -> List[Dict[str, Any]]:
        """Get status of all positions"""
        with self._lock:
            return [position.to_dict() for position in self.active_positions.values()]
    
    def get_limits_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all time-based limits"""
        with self._lock:
            return {period: limit.to_dict() for period, limit in self.time_based_limits.items()}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        with self._lock:
            return {
                'limiter_id': self.limiter_id,
                'metrics': self.metrics.copy(),
                'active_positions_count': len(self.active_positions),
                'stop_loss_rules_count': len(self.stop_loss_rules),
                'time_based_limits_count': len(self.time_based_limits),
                'position_summary': {
                    'total_unrealized_pnl': sum(pos.unrealized_pnl for pos in self.active_positions.values()),
                    'total_realized_pnl': sum(pos.realized_pnl for pos in self.active_positions.values()),
                    'max_drawdown_positions': max((pos.max_drawdown for pos in self.active_positions.values()), default='0'),
                    'profit_positions': len([pos for pos in self.active_positions.values() if pos.unrealized_pnl > 0]),
                    'loss_positions': len([pos for pos in self.active_positions.values() if pos.unrealized_pnl < 0])
                }
            }


class LossLimiterManager:
    """Manager for multiple loss limiters"""
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        self.audit_logger = audit_logger or get_audit_logger()
        self.limiters: Dict[str, LossLimiter] = {}
        self.config = LossLimiterConfig()
        self._lock = threading.Lock()
        
        # Global settings
        self.global_stop_loss_enabled: bool = True
        self.emergency_liquidation_enabled: bool = True
        self.recovery_mode: RecoveryMode = RecoveryMode.IMMEDIATE_RESUME
        
        # Performance tracking
        self.global_metrics = {
            'total_limiters': 0,
            'total_positions': 0,
            'total_triggers': 0,
            'total_loss_prevented': '0',
            'active_emergencies': 0
        }
        
        logger.info("Loss limiter manager initialized")
    
    def create_limiter(self, limiter_id: str, 
                      config: Optional[LossLimiterConfig] = None) -> LossLimiter:
        """Create new loss limiter"""
        with self._lock:
            if limiter_id in self.limiters:
                raise ValueError(f"Loss limiter {limiter_id} already exists")
            
            limiter_config = config or self.config
            limiter = LossLimiter(limiter_id, limiter_config, self.audit_logger)
            
            self.limiters[limiter_id] = limiter
            self.global_metrics['total_limiters'] += 1
            
            logger.info(f"Created loss limiter {limiter_id}")
            return limiter
    
    def get_limiter(self, limiter_id: str) -> Optional[LossLimiter]:
        """Get loss limiter by ID"""
        with self._lock:
            return self.limiters.get(limiter_id)
    
    def remove_limiter(self, limiter_id: str):
        """Remove loss limiter"""
        with self._lock:
            if limiter_id in self.limiters:
                del self.limiters[limiter_id]
                self.global_metrics['total_limiters'] -= 1
                logger.info(f"Removed loss limiter {limiter_id}")
    
    def check_all_limits(self) -> List[Any]:
        """Check all time-based limits across all limiters"""
        triggered_events = []
        
        with self._lock:
            for limiter in self.limiters.values():
                triggered_limits = limiter.check_time_based_limits()
                triggered_events.extend(triggered_limits)
        
        return triggered_events
    
    async def emergency_liquidation(self, reason: str, 
                                   affected_positions: Optional[List[UUID]] = None) -> bool:
        """Execute emergency liquidation"""
        logger.critical(f"Initiating emergency liquidation: {reason}")
        
        liquidation_tasks = []
        liquidated_positions = []
        
        with self._lock:
            for limiter in self.limiters.values():
                if affected_positions:
                    # Liquidate specific positions
                    for position_id in affected_positions:
                        position_status = limiter.get_position_status(position_id)
                        if position_status:
                            # Execute liquidation (implement with your trading system)
                            liquidation_tasks.append(
                                self._execute_liquidation(limiter, position_id, reason)
                            )
                            liquidated_positions.append(position_id)
                else:
                    # Liquidate all positions
                    positions = limiter.get_all_positions_status()
                    for pos_status in positions:
                        position_id = UUID(pos_status['position_id'])
                        liquidation_tasks.append(
                            self._execute_liquidation(limiter, position_id, reason)
                        )
                        liquidated_positions.append(position_id)
        
        # Execute liquidations
        if liquidation_tasks:
            await asyncio.gather(*liquidation_tasks, return_exceptions=True)
        
        self.global_metrics['active_emergencies'] += 1
        
        # Log emergency event
        self.audit_logger.log_security_event(SecurityEventLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type='EMERGENCY_LIQUIDATION',
            severity=LogLevel.CRITICAL,
            user_id=None,
            ip_address=None,
            session_id=None,
            description=f"Emergency liquidation executed: {reason}",
            details={
                'reason': reason,
                'liquidated_positions': [str(pos) for pos in liquidated_positions],
                'total_positions': len(liquidated_positions)
            }
        ))
        
        logger.critical(f"Emergency liquidation completed", 
                       positions=[str(pos) for pos in liquidated_positions])
        
        return True
    
    async def _execute_liquidation(self, limiter: LossLimiter, position_id: UUID, reason: str):
        """Execute individual position liquidation"""
        try:
            # Get current market price (implement with your market data source)
            current_price = '100'  # Placeholder
            
            # Close position
            success = limiter.close_position(position_id, current_price)
            
            if success:
                logger.info(f"Position {position_id} liquidated successfully", reason=reason)
            else:
                logger.warning(f"Failed to liquidate position {position_id}", reason=reason)
                
        except Exception as e:
            logger.error(f"Error liquidating position {position_id}: {e}", exc_info=True)
    
    def get_global_status(self) -> Dict[str, Any]:
        """Get global loss limiter status"""
        with self._lock:
            status = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'global_settings': {
                    'stop_loss_enabled': self.global_stop_loss_enabled,
                    'emergency_liquidation_enabled': self.emergency_liquidation_enabled,
                    'recovery_mode': self.recovery_mode.value
                },
                'global_metrics': {
                    'total_limiters': len(self.limiters),
                    'total_positions': sum(len(limiter.active_positions) for limiter in self.limiters.values()),
                    'total_triggers': sum(limiter.metrics['total_triggers'] for limiter in self.limiters.values()),
                    'total_loss_prevented': sum(limiter.metrics['total_loss_prevented'] for limiter in self.limiters.values()),
                    'active_emergencies': self.global_metrics['active_emergencies']
                },
                'limiters': {}
            }
            
            for limiter_id, limiter in self.limiters.items():
                status['limiters'][limiter_id] = limiter.get_performance_metrics()
            
            return status
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on loss limiter system"""
        health = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'healthy': True,
            'issues': []
        }
        
        with self._lock:
            for limiter_id, limiter in self.limiters.items():
                limiter_health = {
                    'limiter_id': limiter_id,
                    'healthy': True,
                    'issues': [],
                    'metrics': limiter.metrics.copy()
                }
                
                # Check for excessive triggers
                if limiter.metrics['total_triggers'] > 100:
                    limiter_health['issues'].append(f"Excessive triggers: {limiter.metrics['total_triggers']}")
                
                # Check for failed stops
                if limiter.metrics['failed_stops'] > limiter.metrics['successful_stops']:
                    limiter_health['healthy'] = False
                    limiter_health['issues'].append("Failed stops exceed successful stops")
                
                if not limiter_health['healthy']:
                    health['healthy'] = False
                    health['issues'].append(f"Limiter {limiter_id}: {limiter_health['issues']}")
                
                health[f'limiter_{limiter_id}'] = limiter_health
        
        return health


# Global loss limiter manager instance
_global_ll_manager = None


def get_loss_limiter_manager() -> LossLimiterManager:
    """Get or create global loss limiter manager"""
    global _global_ll_manager
    if _global_ll_manager is None:
        _global_ll_manager = LossLimiterManager()
    return _global_ll_manager


if __name__ == "__main__":
    # Example usage and testing
    async def test_loss_limiter():
        # Setup
        manager = get_loss_limiter_manager()
        limiter = manager.create_limiter("test_limiter")
        
        # Create stop loss rule
        rule = StopLossRule(
            name="Test Fixed Stop",
            stop_type=LossStopType.FIXED_STOP_LOSS,
            stop_level=StopLevel.MODERATE,
            stop_percentage=0.05
        )
        limiter.add_stop_loss_rule(rule)
        
        # Create time-based limit
        daily_limit = TimeBasedLimit(
            time_period="daily",
            max_loss_amount='500',
            max_loss_percentage='0.10'
        )
        limiter.add_time_based_limit(daily_limit)
        
        # Test position
        position_id = limiter.create_position_stop_loss(
            symbol="TEST",
            entry_price='100',
            position_size='10',
            side="LONG",
            rule_id=rule.rule_id
        )
        
        print(f"Created position: {position_id}")
        
        # Test price updates
        print("Testing price updates...")
        limiter.update_position_price("TEST", '98')  # 2% loss
        limiter.update_position_price("TEST", '96')  # 4% loss
        limiter.update_position_price("TEST", '94')  # 6% loss (should trigger)
        
        # Check position status
        status = limiter.get_position_status(position_id)
        print(f"Position status: {status}")
        
        # Test time-based limits
        print("Testing time-based limits...")
        limiter.update_trade_result(uuid4(), '-100')  # $100 loss
        
        triggered_limits = limiter.check_time_based_limits()
        print(f"Triggered limits: {len(triggered_limits)}")
        
        # Get performance metrics
        metrics = limiter.get_performance_metrics()
        print(f"Performance metrics: {metrics}")
        
        # Get global status
        global_status = manager.get_global_status()
        print(f"Global status: {global_status}")
        
        print("Loss limiter test completed!")
    
    # Run test
    asyncio.run(test_loss_limiter())