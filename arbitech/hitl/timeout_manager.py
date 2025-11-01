"""
Comprehensive Timeout Management System for Arbitrage Trading

This module provides sophisticated timeout handling for arbitrage opportunities,
including dynamic timeout calculation, escalation strategies, and performance
optimization for high-frequency trading environments.

Features:
- Dynamic timeout calculation based on opportunity urgency and profit margins
- Timeout escalation and notification system
- Graceful timeout scenario handling (auto-reject, extend, escalate)
- Opportunity aging and removal based on timeout thresholds
- Custom timeout rules per user/bookmaker/sport
- Integration with browser automation timing
- Performance optimization for high-frequency timeout checking
"""

import asyncio
import logging
import time
import threading
import heapq
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union, Set, Tuple
from uuid import UUID, uuid4
import weakref
import json
import statistics

from ..storage.models import (
    ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier, 
    NotificationType, NotificationPriority, NotificationChannel,
    Notification, MessageData
)
from ..core.config_manager import get_config


class TimeoutStatus(str, Enum):
    """Timeout status enumeration."""
    ACTIVE = "active"
    EXPIRED = "expired"
    EXTENDED = "extended"
    ESCALATED = "escalated"
    AUTO_REJECTED = "auto_rejected"
    EXECUTED = "executed"
    REMOVED = "removed"


class TimeoutSeverity(str, Enum):
    """Timeout severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationAction(str, Enum):
    """Escalation action types."""
    NOTIFY_USER = "notify_user"
    EXTEND_TIMEOUT = "extend_timeout"
    AUTO_REJECT = "auto_reject"
    INCREASE_PRIORITY = "increase_priority"
    TRIGGER_SCAN = "trigger_scan"
    EMERGENCY_STOP = "emergency_stop"


@dataclass
class TimeoutRule:
    """Represents a timeout rule configuration."""
    rule_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: Optional[str] = None
    
    # Rule scope
    user_id: Optional[UUID] = None
    bookmaker: Optional[str] = None
    sport: Optional[Sport] = None
    market_type: Optional[str] = None
    risk_tier: Optional[RiskTier] = None
    
    # Timeout parameters
    base_timeout_seconds: int = 30
    min_timeout_seconds: int = 10
    max_timeout_seconds: int = 300
    
    # Dynamic adjustment factors
    profit_margin_multiplier: Decimal = Decimal('1.0')  # Multiply timeout by profit margin
    urgency_multiplier: Decimal = Decimal('1.0')  # Adjust for urgency
    liquidity_factor: Decimal = Decimal('1.0')  # Adjust for liquidity
    
    # Escalation rules
    enable_escalation: bool = True
    escalation_threshold_seconds: int = 20
    max_escalations: int = 3
    escalation_actions: List[EscalationAction] = field(default_factory=list)
    
    # Performance settings
    check_interval_ms: int = 100
    enable_performance_monitoring: bool = True
    
    is_active: bool = True
    priority: int = 1  # Higher numbers = higher priority
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TimeoutEvent:
    """Represents a timeout event."""
    event_id: UUID = field(default_factory=uuid4)
    opportunity_id: UUID
    event_type: str  # timeout_created, timeout_extended, timeout_expired, etc.
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Event data
    original_timeout: Optional[float] = None
    new_timeout: Optional[float] = None
    time_remaining: Optional[float] = None
    action_taken: Optional[str] = None
    
    # Performance metrics
    check_count: int = 0
    notification_sent: bool = False
    escalation_level: int = 0


@dataclass
class TimeoutMetrics:
    """Performance metrics for timeout management."""
    # Timing metrics
    average_check_time_ms: float = 0.0
    max_check_time_ms: float = 0.0
    min_check_time_ms: float = float('inf')
    
    # Opportunity metrics
    total_opportunities: int = 0
    active_opportunities: int = 0
    expired_opportunities: int = 0
    extended_opportunities: int = 0
    escalated_opportunities: int = 0
    
    # Escalation metrics
    total_escalations: int = 0
    escalations_by_type: Dict[EscalationAction, int] = field(default_factory=dict)
    
    # System performance
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    check_frequency_hz: float = 0.0
    
    # Error tracking
    timeout_errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None


class TimeoutManager:
    """
    Comprehensive timeout management system for arbitrage opportunities.
    
    Features:
    - Dynamic timeout calculation based on opportunity characteristics
    - High-performance timeout checking with optimized data structures
    - Intelligent escalation and notification system
    - Custom rules per user/bookmaker/sport
    - Integration with browser automation timing
    - Real-time performance monitoring
    """
    
    def __init__(self, 
                 check_interval_ms: int = 100,
                 enable_performance_monitoring: bool = True,
                 max_concurrent_checks: int = 1000):
        """
        Initialize timeout manager.
        
        Args:
            check_interval_ms: Interval between timeout checks in milliseconds
            enable_performance_monitoring: Whether to collect performance metrics
            max_concurrent_checks: Maximum concurrent timeout checks
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration
        self.check_interval_ms = check_interval_ms
        self.max_concurrent_checks = max_concurrent_checks
        
        # Core data structures
        self._active_timeouts: Dict[UUID, float] = {}  # opportunity_id -> expiration_time
        self._timeout_rules: Dict[UUID, TimeoutRule] = {}  # rule_id -> rule
        self._timeout_events: Dict[UUID, List[TimeoutEvent]] = defaultdict(list)  # opportunity_id -> events
        self._custom_timeout_calculators: Dict[str, Callable] = {}
        
        # Performance tracking
        self._check_heap: List[Tuple[float, UUID]] = []  # (expiration_time, opportunity_id)
        self._last_check_times: Dict[UUID, float] = {}
        self._metrics = TimeoutMetrics()
        
        # Threading and async support
        self._running = False
        self._check_thread: Optional[threading.Thread] = None
        self._check_lock = threading.RLock()
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Opportunity tracking
        self._opportunity_refs: Dict[UUID, weakref.WeakSet] = defaultdict(weakref.WeakSet)
        
        # Statistics and analytics
        self._check_history: deque = deque(maxlen=1000)
        self._performance_samples: deque = deque(maxlen=100)
        
        # Default rules
        self._initialize_default_rules()
        
        self.logger.info(f"TimeoutManager initialized with {check_interval_ms}ms check interval")
    
    def _initialize_default_rules(self):
        """Initialize default timeout rules."""
        
        # High-profit, low-risk rule
        high_profit_rule = TimeoutRule(
            name="High Profit Low Risk",
            description="Extended timeouts for high-profit, low-risk opportunities",
            risk_tier=RiskTier.TIER_A,
            base_timeout_seconds=60,
            profit_margin_multiplier=Decimal('1.5'),
            escalation_threshold_seconds=30,
            max_escalations=2
        )
        self.add_rule(high_profit_rule)
        
        # Standard arbitrage rule
        standard_rule = TimeoutRule(
            name="Standard Arbitrage",
            description="Standard timeout settings for typical arbitrage opportunities",
            base_timeout_seconds=30,
            profit_margin_multiplier=Decimal('1.0'),
            escalation_threshold_seconds=15,
            max_escalations=3
        )
        self.add_rule(standard_rule)
        
        # Urgency rule for volatile markets
        urgency_rule = TimeoutRule(
            name="High Urgency",
            description="Shorter timeouts for volatile or urgent opportunities",
            base_timeout_seconds=15,
            min_timeout_seconds=5,
            urgency_multiplier=Decimal('0.7'),
            escalation_threshold_seconds=8,
            max_escalations=1
        )
        self.add_rule(urgency_rule)
        
        # Sports-specific rules
        for sport in [Sport.FOOTBALL, Sport.TENNIS, Sport.BASKETBALL]:
            sport_rule = TimeoutRule(
                name=f"Sport Specific - {sport.value}",
                description=f"Timeouts optimized for {sport.value}",
                sport=sport,
                base_timeout_seconds=45 if sport == Sport.FOOTBALL else 30,
                liquidity_factor=Decimal('1.2') if sport == Sport.FOOTBALL else Decimal('1.0')
            )
            self.add_rule(sport_rule)
    
    def add_rule(self, rule: TimeoutRule) -> UUID:
        """
        Add a timeout rule.
        
        Args:
            rule: Timeout rule to add
            
        Returns:
            Rule ID
        """
        with self._check_lock:
            self._timeout_rules[rule.rule_id] = rule
            self.logger.info(f"Added timeout rule: {rule.name} (ID: {rule.rule_id})")
            return rule.rule_id
    
    def remove_rule(self, rule_id: UUID) -> bool:
        """
        Remove a timeout rule.
        
        Args:
            rule_id: ID of rule to remove
            
        Returns:
            True if rule was removed
        """
        with self._check_lock:
            if rule_id in self._timeout_rules:
                rule_name = self._timeout_rules[rule_id].name
                del self._timeout_rules[rule_id]
                self.logger.info(f"Removed timeout rule: {rule_name}")
                return True
            return False
    
    def register_timeout_callback(self, event_type: str, callback: Callable):
        """
        Register a callback for timeout events.
        
        Args:
            event_type: Type of event ('timeout_created', 'timeout_expired', etc.)
            callback: Callback function to register
        """
        self._callbacks[event_type].append(callback)
        self.logger.debug(f"Registered callback for {event_type}")
    
    def create_timeout(self, 
                      opportunity: ArbitrageOpportunity,
                      custom_timeout_seconds: Optional[float] = None,
                      rule_id: Optional[UUID] = None) -> Tuple[UUID, float]:
        """
        Create a timeout for an opportunity.
        
        Args:
            opportunity: Arbitrage opportunity
            custom_timeout_seconds: Custom timeout override
            rule_id: Specific rule to use
            
        Returns:
            Tuple of (timeout_id, expiration_timestamp)
        """
        with self._check_lock:
            start_time = time.time()
            
            try:
                # Calculate timeout
                if custom_timeout_seconds:
                    timeout_seconds = custom_timeout_seconds
                else:
                    timeout_seconds = self._calculate_timeout(opportunity, rule_id)
                
                # Create expiration time
                expiration_time = time.time() + timeout_seconds
                timeout_id = uuid4()
                
                # Store timeout
                self._active_timeouts[opportunity.id] = expiration_time
                heapq.heappush(self._check_heap, (expiration_time, opportunity.id))
                
                # Create initial event
                event = TimeoutEvent(
                    opportunity_id=opportunity.id,
                    event_type="timeout_created",
                    original_timeout=timeout_seconds,
                    new_timeout=timeout_seconds,
                    time_remaining=timeout_seconds
                )
                self._timeout_events[opportunity.id].append(event)
                
                # Update metrics
                self._metrics.total_opportunities += 1
                self._metrics.active_opportunities += 1
                
                # Track opportunity reference
                if not hasattr(opportunity, '_timeout_manager_ref'):
                    self._opportunity_refs[opportunity.id].add(opportunity)
                
                self.logger.info(
                    f"Created timeout for opportunity {opportunity.id}: "
                    f"{timeout_seconds:.1f}s (expires at {expiration_time:.1f})"
                )
                
                # Trigger callback
                self._trigger_callback('timeout_created', {
                    'opportunity_id': opportunity.id,
                    'timeout_seconds': timeout_seconds,
                    'expiration_time': expiration_time
                })
                
                check_time = (time.time() - start_time) * 1000
                self._update_performance_metrics(check_time)
                
                return timeout_id, expiration_time
                
            except Exception as e:
                self.logger.error(f"Failed to create timeout for opportunity {opportunity.id}: {e}")
                self._metrics.timeout_errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                raise
    
    def extend_timeout(self, 
                      opportunity_id: UUID,
                      additional_seconds: float,
                      reason: str = "manual_extension") -> bool:
        """
        Extend timeout for an opportunity.
        
        Args:
            opportunity_id: ID of opportunity
            additional_seconds: Additional seconds to add
            reason: Reason for extension
            
        Returns:
            True if timeout was extended
        """
        with self._check_lock:
            if opportunity_id not in self._active_timeouts:
                return False
            
            current_expiration = self._active_timeouts[opportunity_id]
            new_expiration = current_expiration + additional_seconds
            self._active_timeouts[opportunity_id] = new_expiration
            
            # Find and update heap entry
            for i, (exp_time, opp_id) in enumerate(self._check_heap):
                if opp_id == opportunity_id:
                    self._check_heap[i] = (new_expiration, opp_id)
                    heapq.heapify(self._check_heap)
                    break
            
            # Create event
            event = TimeoutEvent(
                opportunity_id=opportunity_id,
                event_type="timeout_extended",
                original_timeout=additional_seconds,
                new_timeout=new_expiration - time.time(),
                action_taken=reason
            )
            self._timeout_events[opportunity_id].append(event)
            
            # Update metrics
            self._metrics.extended_opportunities += 1
            
            self.logger.info(
                f"Extended timeout for opportunity {opportunity_id} "
                f"by {additional_seconds:.1f}s (new expiration: {new_expiration:.1f})"
            )
            
            # Trigger callback
            self._trigger_callback('timeout_extended', {
                'opportunity_id': opportunity_id,
                'additional_seconds': additional_seconds,
                'new_expiration': new_expiration,
                'reason': reason
            })
            
            return True
    
    def get_timeout_remaining(self, opportunity_id: UUID) -> Optional[float]:
        """
        Get remaining time for timeout.
        
        Args:
            opportunity_id: ID of opportunity
            
        Returns:
            Remaining time in seconds, or None if no timeout exists
        """
        with self._check_lock:
            if opportunity_id not in self._active_timeouts:
                return None
            
            expiration_time = self._active_timeouts[opportunity_id]
            return max(0.0, expiration_time - time.time())
    
    def get_timeout_status(self, opportunity_id: UUID) -> TimeoutStatus:
        """
        Get timeout status for an opportunity.
        
        Args:
            opportunity_id: ID of opportunity
            
        Returns:
            Current timeout status
        """
        with self._check_lock:
            if opportunity_id not in self._active_timeouts:
                return TimeoutStatus.REMOVED
            
            time_remaining = self.get_timeout_remaining(opportunity_id)
            if time_remaining is None:
                return TimeoutStatus.REMOVED
            
            if time_remaining <= 0:
                return TimeoutStatus.EXPIRED
            
            # Check if it was extended or escalated
            events = self._timeout_events[opportunity_id]
            if any(event.event_type == "timeout_extended" for event in events):
                return TimeoutStatus.EXTENDED
            
            if any(event.event_type == "timeout_escalated" for event in events):
                return TimeoutStatus.ESCALATED
            
            return TimeoutStatus.ACTIVE
    
    def remove_timeout(self, opportunity_id: UUID, reason: str = "manual_removal") -> bool:
        """
        Remove timeout for an opportunity.
        
        Args:
            opportunity_id: ID of opportunity
            reason: Reason for removal
            
        Returns:
            True if timeout was removed
        """
        with self._check_lock:
            if opportunity_id not in self._active_timeouts:
                return False
            
            # Create removal event
            event = TimeoutEvent(
                opportunity_id=opportunity_id,
                event_type="timeout_removed",
                action_taken=reason
            )
            self._timeout_events[opportunity_id].append(event)
            
            # Remove from active timeouts
            del self._active_timeouts[opportunity_id]
            
            # Remove from heap (lazy removal)
            self._check_heap = [(exp_time, opp_id) for exp_time, opp_id in self._check_heap 
                              if opp_id != opportunity_id]
            heapq.heapify(self._check_heap)
            
            # Update metrics
            self._metrics.active_opportunities -= 1
            
            self.logger.info(f"Removed timeout for opportunity {opportunity_id}: {reason}")
            
            # Trigger callback
            self._trigger_callback('timeout_removed', {
                'opportunity_id': opportunity_id,
                'reason': reason
            })
            
            return True
    
    def _calculate_timeout(self, 
                          opportunity: ArbitrageOpportunity,
                          rule_id: Optional[UUID] = None) -> float:
        """
        Calculate timeout duration for an opportunity.
        
        Args:
            opportunity: Arbitrage opportunity
            rule_id: Optional specific rule to use
            
        Returns:
            Timeout duration in seconds
        """
        # Get applicable rule
        rule = self._get_applicable_rule(opportunity, rule_id)
        if not rule:
            # Fallback to default
            base_timeout = 30.0
        else:
            base_timeout = float(rule.base_timeout_seconds)
        
        # Apply profit margin factor
        if rule and rule.profit_margin_multiplier != Decimal('1.0'):
            profit_multiplier = float(rule.profit_margin_multiplier)
            # Higher profit margins get more time
            profit_factor = 1.0 + (float(opportunity.profit_margin) * profit_multiplier * 0.5)
            base_timeout *= profit_factor
        
        # Apply urgency factor
        if rule and rule.urgency_multiplier != Decimal('1.0'):
            urgency_multiplier = float(rule.urgency_multiplier)
            base_timeout *= urgency_multiplier
        
        # Apply liquidity factor
        if rule and rule.liquidity_factor != Decimal('1.0'):
            liquidity_multiplier = float(rule.liquidity_factor)
            base_timeout *= liquidity_multiplier
        
        # Apply risk tier adjustments
        risk_multiplier = {
            RiskTier.TIER_A: 1.2,  # Low risk gets more time
            RiskTier.TIER_B: 1.0,  # Standard time
            RiskTier.TIER_C: 0.8,  # Higher risk gets less time
            RiskTier.TIER_D: 0.6   # Highest risk gets least time
        }.get(opportunity.risk_tier, 1.0)
        base_timeout *= risk_multiplier
        
        # Apply sport-specific adjustments
        sport_multiplier = {
            Sport.FOOTBALL: 1.3,  # More time for complex markets
            Sport.BASKETBALL: 1.1,
            Sport.TENNIS: 0.9,    # Less time for fast markets
            Sport.BASEBALL: 1.0,
            Sport.ESPORTS: 0.8,   # Very fast-moving markets
        }.get(opportunity.sport, 1.0)
        base_timeout *= sport_multiplier
        
        # Apply bookmaker-specific adjustments (if available)
        if opportunity.legs:
            bookmaker_timeouts = self._get_bookmaker_timeout_factors(opportunity.legs)
            if bookmaker_timeouts:
                avg_bookmaker_factor = statistics.mean(bookmaker_timeouts)
                base_timeout *= avg_bookmaker_factor
        
        # Apply market type adjustments
        market_multiplier = {
            'match_winner': 1.2,
            'over_under': 1.0,
            'handicap': 0.9,
            'correct_score': 0.8,
            'first_goal': 0.7,
        }.get(opportunity.market_type.lower(), 1.0)
        base_timeout *= market_multiplier
        
        # Apply user-specific adjustments
        if rule and rule.user_id:
            user_multiplier = self._get_user_timeout_multiplier(rule.user_id)
            base_timeout *= user_multiplier
        
        # Ensure within bounds
        min_timeout = float(rule.min_timeout_seconds) if rule else 10.0
        max_timeout = float(rule.max_timeout_seconds) if rule else 300.0
        
        return max(min_timeout, min(max_timeout, base_timeout))
    
    def _get_applicable_rule(self, 
                           opportunity: ArbitrageOpportunity,
                           rule_id: Optional[UUID] = None) -> Optional[TimeoutRule]:
        """
        Get the most applicable rule for an opportunity.
        
        Args:
            opportunity: Arbitrage opportunity
            rule_id: Optional specific rule ID
            
        Returns:
            Most applicable rule, or None
        """
        if rule_id and rule_id in self._timeout_rules:
            return self._timeout_rules[rule_id]
        
        # Find matching rules
        matching_rules = []
        
        for rule in self._timeout_rules.values():
            if not rule.is_active:
                continue
            
            score = 0
            
            # Exact matches get highest scores
            if rule.user_id and hasattr(opportunity, 'user_id'):
                if rule.user_id == opportunity.user_id:
                    score += 100
            
            if rule.sport and rule.sport == opportunity.sport:
                score += 50
            
            if rule.risk_tier and rule.risk_tier == opportunity.risk_tier:
                score += 40
            
            if rule.market_type and rule.market_type.lower() == opportunity.market_type.lower():
                score += 30
            
            if rule.bookmaker:
                # Check if any leg matches the bookmaker
                if opportunity.legs and any(
                    rule.bookmaker.lower() == leg.bookmaker.lower() 
                    for leg in opportunity.legs
                ):
                    score += 20
            
            if score > 0:
                matching_rules.append((score, rule))
        
        # Return highest scoring rule
        if matching_rules:
            matching_rules.sort(key=lambda x: (x[0], x[1].priority), reverse=True)
            return matching_rules[0][1]
        
        return None
    
    def _get_bookmaker_timeout_factors(self, legs: List[ArbitrageLeg]) -> List[float]:
        """
        Get timeout adjustment factors for bookmakers.
        
        Args:
            List of arbitrage legs
            
        Returns:
            List of timeout factors
        """
        factors = []
        
        # Bookmaker-specific timeout adjustments
        bookmaker_factors = {
            'bet365': 1.2,      # More stable, can take more time
            'william_hill': 1.1,
            'pinnacle': 1.3,    # Very stable odds
            'betfair': 1.0,     # Standard
            'draftkings': 0.9,  # Faster markets
            'fanduel': 0.9,
            'unibet': 1.0,
            'betway': 0.95,
        }
        
        for leg in legs:
            factor = bookmaker_factors.get(leg.bookmaker.lower(), 1.0)
            factors.append(factor)
        
        return factors
    
    def _get_user_timeout_multiplier(self, user_id: UUID) -> float:
        """
        Get timeout multiplier for a user based on their history.
        
        Args:
            user_id: User ID
            
        Returns:
            Timeout multiplier
        """
        # This would typically query user history, performance metrics, etc.
        # For now, return a neutral multiplier
        
        # Users with higher success rates might get more time
        # Users with frequent timeouts might get less time
        
        return 1.0  # Neutral
    
    def _trigger_callback(self, event_type: str, data: Dict[str, Any]):
        """
        Trigger callbacks for an event type.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        callbacks = self._callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # Run async callback in a new task
                    asyncio.create_task(callback(data))
                else:
                    # Run sync callback
                    callback(data)
            except Exception as e:
                self.logger.error(f"Callback error for {event_type}: {e}")
    
    def _update_performance_metrics(self, check_time_ms: float):
        """Update performance metrics."""
        self._check_history.append(check_time_ms)
        
        # Update timing metrics
        if self._check_history:
            self._metrics.average_check_time_ms = statistics.mean(self._check_history)
            self._metrics.max_check_time_ms = max(self._check_history)
            self._metrics.min_check_time_ms = min(self._check_history)
        
        # Update check frequency
        if len(self._check_history) > 1:
            time_span = self._check_history[-1] - self._check_history[0]
            if time_span > 0:
                self._metrics.check_frequency_hz = len(self._check_history) / time_span
    
    def start_monitoring(self):
        """Start the timeout monitoring thread."""
        if self._running:
            return
        
        self._running = True
        self._check_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._check_thread.start()
        
        self.logger.info("Timeout monitoring started")
    
    def stop_monitoring(self):
        """Stop the timeout monitoring thread."""
        if not self._running:
            return
        
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=5.0)
        
        self.logger.info("Timeout monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                start_time = time.time()
                
                # Check for expired timeouts
                self._check_expired_timeouts()
                
                # Check for escalations
                self._check_escalations()
                
                # Update metrics
                loop_time = time.time() - start_time
                self._update_metrics()
                
                # Sleep until next check
                sleep_time = max(0, self.check_interval_ms / 1000.0 - loop_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                self._metrics.timeout_errors += 1
                self._metrics.last_error = str(e)
                self._metrics.last_error_time = datetime.utcnow()
                time.sleep(0.1)  # Brief pause on error
    
    def _check_expired_timeouts(self):
        """Check for and handle expired timeouts."""
        current_time = time.time()
        
        # Find expired timeouts
        expired_ids = []
        for opp_id, expiration_time in list(self._active_timeouts.items()):
            if current_time >= expiration_time:
                expired_ids.append(opp_id)
        
        # Handle each expired timeout
        for opp_id in expired_ids:
            self._handle_timeout_expiration(opp_id)
    
    def _handle_timeout_expiration(self, opportunity_id: UUID):
        """
        Handle timeout expiration for an opportunity.
        
        Args:
            opportunity_id: ID of expired opportunity
        """
        with self._check_lock:
            # Create expiration event
            event = TimeoutEvent(
                opportunity_id=opportunity_id,
                event_type="timeout_expired",
                time_remaining=0.0
            )
            self._timeout_events[opportunity_id].append(event)
            
            # Remove from active timeouts
            if opportunity_id in self._active_timeouts:
                del self._active_timeouts[opportunity_id]
                self._metrics.active_opportunities -= 1
                self._metrics.expired_opportunities += 1
            
            self.logger.warning(f"Timeout expired for opportunity {opportunity_id}")
            
            # Trigger expiration callback
            self._trigger_callback('timeout_expired', {
                'opportunity_id': opportunity_id,
                'timestamp': datetime.utcnow()
            })
    
    def _check_escalations(self):
        """Check for opportunities that need escalation."""
        current_time = time.time()
        
        for opp_id, expiration_time in list(self._active_timeouts.items()):
            time_remaining = expiration_time - current_time
            
            # Check if opportunity needs escalation
            rule = self._get_applicable_rule_by_id(opp_id)
            if not rule or not rule.enable_escalation:
                continue
            
            escalation_threshold = rule.escalation_threshold_seconds
            if time_remaining <= escalation_threshold:
                self._escalate_opportunity(opp_id, rule, time_remaining)
    
    def _get_applicable_rule_by_id(self, opportunity_id: UUID) -> Optional[TimeoutRule]:
        """Get applicable rule for opportunity ID."""
        # This would need access to the actual opportunity object
        # For now, return a default escalation rule
        
        # Find any rule that has escalation enabled
        for rule in self._timeout_rules.values():
            if rule.is_active and rule.enable_escalation:
                return rule
        
        return None
    
    def _escalate_opportunity(self, 
                            opportunity_id: UUID, 
                            rule: TimeoutRule, 
                            time_remaining: float):
        """
        Escalate an opportunity that's about to timeout.
        
        Args:
            opportunity_id: ID of opportunity
            rule: Applicable timeout rule
            time_remaining: Time remaining in seconds
        """
        # Get escalation count
        events = self._timeout_events[opportunity_id]
        escalation_events = [e for e in events if e.event_type == "timeout_escalated"]
        
        if len(escalation_events) >= rule.max_escalations:
            # Max escalations reached, auto-reject
            self._trigger_escalation_action(
                opportunity_id, 
                EscalationAction.AUTO_REJECT, 
                "Maximum escalations reached"
            )
            return
        
        # Perform escalation actions
        for action in rule.escalation_actions:
            if action == EscalationAction.NOTIFY_USER:
                self._send_escalation_notification(opportunity_id, time_remaining)
            
            elif action == EscalationAction.EXTEND_TIMEOUT:
                extend_seconds = rule.base_timeout_seconds * 0.5
                self.extend_timeout(
                    opportunity_id, 
                    extend_seconds, 
                    f"escalation_extension_{len(escalation_events) + 1}"
                )
            
            elif action == EscalationAction.INCREASE_PRIORITY:
                # This would typically be handled by the opportunity ranking system
                self._trigger_callback('priority_increased', {
                    'opportunity_id': opportunity_id,
                    'escalation_level': len(escalation_events) + 1
                })
        
        # Create escalation event
        event = TimeoutEvent(
            opportunity_id=opportunity_id,
            event_type="timeout_escalated",
            escalation_level=len(escalation_events) + 1,
            time_remaining=time_remaining
        )
        self._timeout_events[opportunity_id].append(event)
        
        # Update metrics
        self._metrics.escalated_opportunities += 1
        self._metrics.total_escalations += 1
        
        for action in rule.escalation_actions:
            self._metrics.escalations_by_type[action] = \
                self._metrics.escalations_by_type.get(action, 0) + 1
        
        self.logger.info(
            f"Escalated opportunity {opportunity_id} "
            f"(level {len(escalation_events) + 1}, {time_remaining:.1f}s remaining)"
        )
    
    def _send_escalation_notification(self, opportunity_id: UUID, time_remaining: float):
        """
        Send escalation notification for an opportunity.
        
        Args:
            opportunity_id: ID of opportunity
            time_remaining: Time remaining in seconds
        """
        # This would integrate with the notification system
        # For now, just log the escalation
        
        self.logger.warning(
            f"ESCALATION: Opportunity {opportunity_id} has {time_remaining:.1f}s remaining"
        )
    
    def _trigger_escalation_action(self, 
                                  opportunity_id: UUID, 
                                  action: EscalationAction, 
                                  reason: str):
        """
        Trigger a specific escalation action.
        
        Args:
            opportunity_id: ID of opportunity
            action: Action to trigger
            reason: Reason for action
        """
        if action == EscalationAction.AUTO_REJECT:
            # Auto-reject the opportunity
            self.remove_timeout(opportunity_id, f"auto_reject: {reason}")
            self._trigger_callback('opportunity_auto_rejected', {
                'opportunity_id': opportunity_id,
                'reason': reason
            })
            
        elif action == EscalationAction.EMERGENCY_STOP:
            # Trigger emergency stop (would integrate with risk management)
            self._trigger_callback('emergency_stop_triggered', {
                'opportunity_id': opportunity_id,
                'reason': reason
            })
    
    def _update_metrics(self):
        """Update system performance metrics."""
        import psutil
        
        try:
            # Update memory usage
            process = psutil.Process()
            self._metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            
            # Update CPU usage
            self._metrics.cpu_usage_percent = process.cpu_percent()
            
        except Exception as e:
            self.logger.debug(f"Could not update system metrics: {e}")
    
    def get_opportunities_near_timeout(self, 
                                     threshold_seconds: float = 30.0,
                                     limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get opportunities that are approaching timeout.
        
        Args:
            threshold_seconds: Time threshold in seconds
            limit: Maximum number of opportunities to return
            
        Returns:
            List of opportunity information dictionaries
        """
        current_time = time.time()
        near_timeout = []
        
        with self._check_lock:
            for opp_id, expiration_time in self._active_timeouts.items():
                time_remaining = expiration_time - current_time
                
                if 0 <= time_remaining <= threshold_seconds:
                    near_timeout.append({
                        'opportunity_id': opp_id,
                        'time_remaining': time_remaining,
                        'expiration_time': expiration_time,
                        'status': self.get_timeout_status(opp_id)
                    })
            
            # Sort by time remaining (shortest first)
            near_timeout.sort(key=lambda x: x['time_remaining'])
            
            # Limit results
            return near_timeout[:limit]
    
    def get_metrics(self) -> TimeoutMetrics:
        """
        Get current performance metrics.
        
        Returns:
            Current metrics snapshot
        """
        return self._metrics
    
    def get_timeout_history(self, 
                          opportunity_id: UUID, 
                          limit: int = 10) -> List[TimeoutEvent]:
        """
        Get timeout history for an opportunity.
        
        Args:
            opportunity_id: ID of opportunity
            limit: Maximum number of events to return
            
        Returns:
            List of timeout events
        """
        events = self._timeout_events.get(opportunity_id, [])
        return events[-limit:] if limit > 0 else events
    
    def cleanup_expired_entries(self, max_age_hours: int = 24):
        """
        Clean up old timeout entries and events.
        
        Args:
            max_age_hours: Maximum age of entries to keep
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        with self._check_lock:
            # Clean up old events
            cleaned_count = 0
            for opp_id in list(self._timeout_events.keys()):
                events = self._timeout_events[opp_id]
                
                # Filter out old events
                recent_events = [
                    event for event in events 
                    if event.timestamp > cutoff_time
                ]
                
                if recent_events:
                    self._timeout_events[opp_id] = recent_events
                else:
                    # Remove entirely if no recent events
                    del self._timeout_events[opp_id]
                    cleaned_count += 1
            
            # Clean up opportunity refs
            for opp_id in list(self._opportunity_refs.keys()):
                if not self._opportunity_refs[opp_id]:
                    del self._opportunity_refs[opp_id]
            
            self.logger.info(f"Cleaned up {cleaned_count} expired timeout entries")
    
    def export_timeout_data(self) -> Dict[str, Any]:
        """
        Export timeout data for analysis.
        
        Returns:
            Dictionary containing timeout data
        """
        with self._check_lock:
            return {
                'active_timeouts': len(self._active_timeouts),
                'total_rules': len(self._timeout_rules),
                'metrics': self._metrics.__dict__,
                'recent_events': {
                    str(opp_id): len(events) 
                    for opp_id, events in self._timeout_events.items()
                },
                'performance_history': list(self._check_history)[-100:],  # Last 100 checks
            }
    
    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()


# Utility functions for integration with other components

def create_timeout_manager_from_config(config: Dict[str, Any]) -> TimeoutManager:
    """
    Create timeout manager from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured TimeoutManager instance
    """
    return TimeoutManager(
        check_interval_ms=config.get('timeout_check_interval_ms', 100),
        enable_performance_monitoring=config.get('enable_performance_monitoring', True),
        max_concurrent_checks=config.get('max_concurrent_checks', 1000)
    )


def integrate_with_opportunity_scanner(timeout_manager: TimeoutManager, scanner):
    """
    Integrate timeout manager with opportunity scanner.
    
    Args:
        timeout_manager: TimeoutManager instance
        scanner: Opportunity scanner instance
    """
    
    def on_opportunity_found(opportunity_data):
        """Handle new opportunity found."""
        try:
            timeout_manager.create_timeout(opportunity_data['opportunity'])
        except Exception as e:
            logging.error(f"Failed to create timeout for opportunity: {e}")
    
    # Register callback
    scanner.register_callback('opportunity_found', on_opportunity_found)
    
    logging.info("Integrated timeout manager with opportunity scanner")


def integrate_with_arbitrage_executor(timeout_manager: TimeoutManager, executor):
    """
    Integrate timeout manager with arbitrage executor.
    
    Args:
        timeout_manager: TimeoutManager instance
        executor: Arbitrage executor instance
    """
    
    def on_execution_start(execution_data):
        """Handle execution start."""
        try:
            # Remove timeout when execution starts
            opportunity_id = execution_data.get('opportunity_id')
            if opportunity_id:
                timeout_manager.remove_timeout(opportunity_id, "execution_started")
        except Exception as e:
            logging.error(f"Failed to remove timeout on execution start: {e}")
    
    def on_execution_timeout(execution_data):
        """Handle execution timeout."""
        try:
            opportunity_id = execution_data.get('opportunity_id')
            if opportunity_id:
                timeout_manager.remove_timeout(opportunity_id, "execution_timeout")
        except Exception as e:
            logging.error(f"Failed to remove timeout on execution timeout: {e}")
    
    # Register callbacks
    executor.register_callback('execution_started', on_execution_start)
    executor.register_callback('execution_timeout', on_execution_timeout)
    
    logging.info("Integrated timeout manager with arbitrage executor")


if __name__ == "__main__":
    # Example usage
    import sys
    import os
    
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Example usage
    async def main():
        # Create timeout manager
        timeout_manager = TimeoutManager()
        
        # Add custom rule
        custom_rule = TimeoutRule(
            name="Custom High-Frequency",
            description="Timeouts for high-frequency trading",
            base_timeout_seconds=10,
            min_timeout_seconds=5,
            max_timeout_seconds=30,
            enable_escalation=True,
            escalation_threshold_seconds=5,
            max_escalations=2
        )
        timeout_manager.add_rule(custom_rule)
        
        # Start monitoring
        timeout_manager.start_monitoring()
        
        try:
            # Simulate opportunity
            from storage.models import ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier
            from decimal import Decimal
            
            opportunity = ArbitrageOpportunity(
                sport=Sport.FOOTBALL,
                event_name="Manchester United vs Liverpool",
                event_date=datetime.utcnow(),
                market_type="match_winner",
                legs=[
                    ArbitrageLeg(
                        bookmaker="bet365",
                        event_outcome="Manchester United wins",
                        odds=Decimal("2.10"),
                        implied_probability=Decimal("0.476"),
                        stake_percentage=Decimal("0.5"),
                        actual_stake=Decimal("50.00"),
                        potential_payout=Decimal("105.00")
                    ),
                    ArbitrageLeg(
                        bookmaker="william_hill",
                        event_outcome="Liverpool wins",
                        odds=Decimal("1.90"),
                        implied_probability=Decimal("0.526"),
                        stake_percentage=Decimal("0.5"),
                        actual_stake=Decimal("50.00"),
                        potential_payout=Decimal("95.00")
                    )
                ],
                total_stake=Decimal("100.00"),
                profit_margin=Decimal("0.05"),
                profit_amount=Decimal("5.00"),
                risk_tier=RiskTier.TIER_A
            )
            
            # Create timeout
            timeout_id, expiration_time = timeout_manager.create_timeout(
                opportunity, 
                custom_timeout_seconds=20.0
            )
            
            print(f"Created timeout {timeout_id}, expires at {expiration_time}")
            
            # Monitor for a bit
            for i in range(5):
                await asyncio.sleep(2)
                remaining = timeout_manager.get_timeout_remaining(opportunity.id)
                status = timeout_manager.get_timeout_status(opportunity.id)
                print(f"Check {i+1}: {remaining:.1f}s remaining, status: {status}")
            
        finally:
            timeout_manager.stop_monitoring()
            print("Timeout manager stopped")
    
    # Run example
    asyncio.run(main())