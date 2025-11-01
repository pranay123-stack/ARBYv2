"""
Real-Time Execution Tracker

Advanced real-time tracking system for multi-leg trade execution with comprehensive
status monitoring, result validation, and performance analysis. Provides enterprise-grade
observability and alerting capabilities.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid
import json
import threading
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from ..storage.models import TradeStatus, ArbitrageOpportunity, ArbitrageLeg


class TrackingLevel(Enum):
    """Tracking detail levels."""
    BASIC = "basic"  # Basic execution tracking
    DETAILED = "detailed"  # Detailed step-by-step tracking
    COMPREHENSIVE = "comprehensive"  # Comprehensive tracking with all metrics
    VERBOSE = "verbose"  # Verbose tracking for debugging


class EventType(str, Enum):
    """Types of execution events."""
    # Execution lifecycle
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_CANCELLED = "execution_cancelled"
    
    # Leg-level events
    LEG_STARTED = "leg_started"
    LEG_COMPLETED = "leg_completed"
    LEG_FAILED = "leg_failed"
    LEG_TIMEOUT = "leg_timeout"
    LEG_ROLLED_BACK = "leg_rolled_back"
    
    # Coordination events
    COORDINATION_STARTED = "coordination_started"
    COORDINATION_SYNC_POINT = "coordination_sync_point"
    COORDINATION_COMPLETED = "coordination_completed"
    
    # Validation events
    VALIDATION_STARTED = "validation_started"
    VALIDATION_COMPLETED = "validation_completed"
    VALIDATION_FAILED = "validation_failed"
    
    # Safety events
    SAFETY_CHECK = "safety_check"
    RISK_ALERT = "risk_alert"
    EMERGENCY_STOP = "emergency_stop"
    
    # Performance events
    PERFORMANCE_THRESHOLD = "performance_threshold"
    TIMING_ANOMALY = "timing_anomaly"
    THROUGHPUT_ALERT = "throughput_alert"
    
    # System events
    SYSTEM_ERROR = "system_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    NETWORK_ISSUE = "network_issue"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Types of performance metrics."""
    TIMING = "timing"
    THROUGHPUT = "throughput"
    SUCCESS_RATE = "success_rate"
    RESOURCE_USAGE = "resource_usage"
    QUALITY = "quality"


@dataclass
class TrackEvent:
    """Individual tracking event."""
    event_id: str
    execution_id: str
    event_type: EventType
    timestamp: datetime
    
    # Event data
    event_data: Dict[str, Any] = field(default_factory=dict)
    
    # Context information
    leg_id: Optional[str] = None
    bookmaker: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Performance metrics
    latency_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        
        if not self.event_id:
            self.event_id = str(uuid.uuid4())


@dataclass
class ExecutionSnapshot:
    """Real-time execution snapshot."""
    execution_id: str
    snapshot_time: datetime
    
    # Basic execution info
    opportunity_id: str
    strategy: str
    current_state: str
    progress_percent: float
    
    # Timing information
    start_time: datetime
    elapsed_time: float
    estimated_completion: Optional[datetime] = None
    
    # Leg status
    legs_total: int = 0
    legs_completed: int = 0
    legs_failed: int = 0
    legs_in_progress: int = 0
    
    # Performance metrics
    success_rate: float = 0.0
    average_latency_ms: float = 0.0
    throughput_per_minute: float = 0.0
    
    # Resource usage
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    network_requests: int = 0
    
    # Risk metrics
    risk_score: float = 0.0
    active_alerts: int = 0
    critical_issues: List[str] = field(default_factory=list)
    
    # Quality metrics
    data_quality_score: float = 0.0
    execution_quality_score: float = 0.0


@dataclass
class AlertRule:
    """Alert rule configuration."""
    rule_id: str
    name: str
    event_type: EventType
    condition: str  # Python expression for alert condition
    severity: AlertSeverity
    
    # Alert settings
    enabled: bool = True
    cooldown_seconds: float = 60.0
    max_alerts_per_hour: int = 10
    
    # Notification settings
    notify_email: bool = False
    notify_webhook: bool = False
    notify_console: bool = True
    
    # Created at
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class Alert:
    """Generated alert."""
    alert_id: str
    rule_id: str
    execution_id: str
    alert_time: datetime
    
    # Alert details
    event_type: EventType
    severity: AlertSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Alert context
    event_count: int = 1
    first_occurrence: Optional[datetime] = None
    last_occurrence: Optional[datetime] = None
    
    # Status
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def __post_init__(self):
        if isinstance(self.alert_time, str):
            self.alert_time = datetime.fromisoformat(self.alert_time)
        if self.first_occurrence and isinstance(self.first_occurrence, str):
            self.first_occurrence = datetime.fromisoformat(self.first_occurrence)
        if self.last_occurrence and isinstance(self.last_occurrence, str):
            self.last_occurrence = datetime.fromisoformat(self.last_occurrence)


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    metric_id: str
    metric_type: MetricType
    metric_name: str
    value: float
    timestamp: datetime
    
    # Context
    execution_id: Optional[str] = None
    bookmaker: Optional[str] = None
    leg_id: Optional[str] = None
    
    # Unit and metadata
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        if not self.metric_id:
            self.metric_id = str(uuid.uuid4())


@dataclass
class TrackingConfig:
    """Configuration for execution tracking."""
    # Tracking settings
    tracking_level: TrackingLevel = TrackingLevel.DETAILED
    max_events_per_execution: int = 1000
    max_events_total: int = 10000
    event_retention_hours: int = 24
    
    # Performance settings
    enable_performance_metrics: bool = True
    metric_collection_interval: float = 1.0  # seconds
    max_metrics_stored: int = 50000
    
    # Alert settings
    enable_alerts: bool = True
    alert_check_interval: float = 5.0  # seconds
    max_alerts_stored: int = 1000
    
    # Monitoring settings
    enable_real_time_monitoring: bool = True
    monitoring_interval: float = 2.0  # seconds
    snapshot_interval: float = 10.0  # seconds
    
    # Storage settings
    enable_persistence: bool = True
    enable_in_memory_cache: bool = True
    cache_size_limit: int = 5000
    
    # Logging settings
    log_events_to_console: bool = False
    log_performance_metrics: bool = True
    log_alerts: bool = True


class ExecutionTracker:
    """
    Real-Time Execution Tracker
    
    Provides comprehensive tracking, monitoring, and alerting for multi-leg execution:
    - Real-time event tracking
    - Performance metrics collection
    - Alert generation and management
    - Execution snapshots and analysis
    - Historical data analysis
    """
    
    def __init__(self, config: Optional[TrackingConfig] = None):
        """
        Initialize the execution tracker.
        
        Args:
            config: Tracking configuration
        """
        self.config = config or TrackingConfig()
        self.logger = logging.getLogger(__name__)
        
        # Event storage
        self._events: deque = deque(maxlen=self.config.max_events_total)
        self._events_by_execution: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.config.max_events_per_execution))
        self._events_lock = threading.RLock()
        
        # Metric storage
        self._metrics: deque = deque(maxlen=self.config.max_metrics_stored)
        self._metrics_by_name: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._metrics_lock = threading.RLock()
        
        # Alert management
        self._alert_rules: Dict[str, AlertRule] = {}
        self._alerts: deque = deque(maxlen=self.config.max_alerts_stored)
        self._recent_alerts: Dict[str, datetime] = {}  # For cooldown tracking
        self._alerts_lock = threading.RLock()
        
        # Real-time monitoring
        self._active_executions: Dict[str, ExecutionSnapshot] = {}
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}
        self._monitoring_lock = asyncio.Lock()
        
        # Performance tracking
        self._performance_stats = {
            'total_events_tracked': 0,
            'total_metrics_collected': 0,
            'total_alerts_generated': 0,
            'average_events_per_execution': 0.0,
            'average_metrics_per_minute': 0.0,
            'alert_rate_per_hour': 0.0
        }
        self._stats_lock = threading.RLock()
        
        # Initialize alert rules
        self._initialize_default_alert_rules()
        
        # Start background tasks
        self._background_tasks = []
        self._shutdown_event = asyncio.Event()
        
        self.logger.info("Execution Tracker initialized successfully")
    
    def _initialize_default_alert_rules(self):
        """Initialize default alert rules."""
        
        default_rules = [
            AlertRule(
                rule_id=str(uuid.uuid4()),
                name="Execution Timeout",
                event_type=EventType.EXECUTION_FAILED,
                condition="event_data.get('error') == 'timeout'",
                severity=AlertSeverity.ERROR
            ),
            AlertRule(
                rule_id=str(uuid.uuid4()),
                name="Leg Execution Failure",
                event_type=EventType.LEG_FAILED,
                condition="True",  # Alert on any leg failure
                severity=AlertSeverity.WARNING
            ),
            AlertRule(
                rule_id=str(uuid.uuid4()),
                name="High Latency",
                event_type=EventType.PERFORMANCE_THRESHOLD,
                condition="event_data.get('latency_ms', 0) > 1000",
                severity=AlertSeverity.WARNING
            ),
            AlertRule(
                rule_id=str(uuid.uuid4()),
                name="Emergency Stop",
                event_type=EventType.EMERGENCY_STOP,
                condition="True",
                severity=AlertSeverity.CRITICAL
            ),
            AlertRule(
                rule_id=str(uuid.uuid4()),
                name="System Error",
                event_type=EventType.SYSTEM_ERROR,
                condition="True",
                severity=AlertSeverity.ERROR
            )
        ]
        
        for rule in default_rules:
            self._alert_rules[rule.rule_id] = rule
    
    async def track_event(self, event: TrackEvent):
        """
        Track an execution event.
        
        Args:
            event: The event to track
        """
        # Add timestamp if not present
        if event.timestamp is None:
            event.timestamp = datetime.utcnow()
        
        # Add performance metrics
        if self.config.enable_performance_metrics:
            await self._collect_performance_metrics(event)
        
        # Store event
        await self._store_event(event)
        
        # Check alerts
        if self.config.enable_alerts:
            await self._check_alert_rules(event)
        
        # Update execution snapshot
        await self._update_execution_snapshot(event)
        
        # Update statistics
        with self._stats_lock:
            self._performance_stats['total_events_tracked'] += 1
    
    async def _store_event(self, event: TrackEvent):
        """Store event in appropriate storage."""
        
        with self._events_lock:
            # Store in main event log
            self._events.append(event)
            
            # Store in execution-specific log
            self._events_by_execution[event.execution_id].append(event)
            
            # Clean up old events if needed
            await self._cleanup_old_events()
    
    async def _collect_performance_metrics(self, event: TrackEvent):
        """Collect performance metrics from event."""
        
        metrics_to_collect = []
        
        # Latency metric
        if event.latency_ms > 0:
            metrics_to_collect.append(PerformanceMetric(
                metric_type=MetricType.TIMING,
                metric_name="event_latency_ms",
                value=event.latency_ms,
                timestamp=event.timestamp,
                execution_id=event.execution_id,
                leg_id=event.leg_id,
                unit="milliseconds"
            ))
        
        # Memory usage metric
        if event.memory_usage_mb > 0:
            metrics_to_collect.append(PerformanceMetric(
                metric_type=MetricType.RESOURCE_USAGE,
                metric_name="memory_usage_mb",
                value=event.memory_usage_mb,
                timestamp=event.timestamp,
                execution_id=event.execution_id,
                unit="megabytes"
            ))
        
        # CPU usage metric
        if event.cpu_usage_percent > 0:
            metrics_to_collect.append(PerformanceMetric(
                metric_type=MetricType.RESOURCE_USAGE,
                metric_name="cpu_usage_percent",
                value=event.cpu_usage_percent,
                timestamp=event.timestamp,
                execution_id=event.execution_id,
                unit="percent"
            ))
        
        # Store metrics
        for metric in metrics_to_collect:
            await self._store_metric(metric)
    
    async def _store_metric(self, metric: PerformanceMetric):
        """Store performance metric."""
        
        with self._metrics_lock:
            # Store in main metric log
            self._metrics.append(metric)
            
            # Store in name-specific log
            self._metrics_by_name[metric.metric_name].append(metric)
            
            # Update statistics
            with self._stats_lock:
                self._performance_stats['total_metrics_collected'] += 1
    
    async def _check_alert_rules(self, event: TrackEvent):
        """Check event against alert rules."""
        
        with self._alerts_lock:
            for rule in self._alert_rules.values():
                if not rule.enabled:
                    continue
                
                try:
                    # Check cooldown
                    if self._is_in_cooldown(rule.rule_id):
                        continue
                    
                    # Evaluate condition
                    if self._evaluate_alert_condition(rule, event):
                        await self._generate_alert(rule, event)
                        self._recent_alerts[rule.rule_id] = datetime.utcnow()
                        
                except Exception as e:
                    self.logger.warning(f"Alert rule {rule.name} evaluation failed: {str(e)}")
    
    def _is_in_cooldown(self, rule_id: str) -> bool:
        """Check if rule is in cooldown period."""
        
        if rule_id not in self._recent_alerts:
            return False
        
        cooldown_end = self._recent_alerts[rule_id] + timedelta(seconds=self._alert_rules[rule_id].cooldown_seconds)
        return datetime.utcnow() < cooldown_end
    
    def _evaluate_alert_condition(self, rule: AlertRule, event: TrackEvent) -> bool:
        """Evaluate alert condition against event."""
        
        try:
            # Create evaluation context
            context = {
                'event': event,
                'event_type': event.event_type,
                'event_data': event.event_data,
                'execution_id': event.execution_id,
                'bookmaker': event.bookmaker,
                'latency_ms': event.latency_ms,
                'timestamp': event.timestamp
            }
            
            # Evaluate condition
            return eval(rule.condition, {"__builtins__": {}}, context)
            
        except Exception as e:
            self.logger.warning(f"Alert condition evaluation failed: {str(e)}")
            return False
    
    async def _generate_alert(self, rule: AlertRule, event: TrackEvent):
        """Generate alert from rule and event."""
        
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            rule_id=rule.rule_id,
            execution_id=event.execution_id,
            alert_time=datetime.utcnow(),
            event_type=event.event_type,
            severity=rule.severity,
            message=f"{rule.name}: {event.event_type.value}",
            details={
                'rule_name': rule.name,
                'event_data': event.event_data,
                'bookmaker': event.bookmaker,
                'leg_id': event.leg_id
            },
            first_occurrence=event.timestamp
        )
        
        # Add alert to storage
        self._alerts.append(alert)
        
        # Send notifications
        await self._send_alert_notifications(alert, rule)
        
        # Update statistics
        with self._stats_lock:
            self._performance_stats['total_alerts_generated'] += 1
        
        self.logger.info(f"Alert generated: {alert.message}")
    
    async def _send_alert_notifications(self, alert: Alert, rule: AlertRule):
        """Send alert notifications."""
        
        notifications_sent = []
        
        # Console notification
        if rule.notify_console:
            await self._send_console_notification(alert)
            notifications_sent.append("console")
        
        # Email notification
        if rule.notify_email:
            await self._send_email_notification(alert)
            notifications_sent.append("email")
        
        # Webhook notification
        if rule.notify_webhook:
            await self._send_webhook_notification(alert)
            notifications_sent.append("webhook")
        
        alert.details['notifications_sent'] = notifications_sent
    
    async def _send_console_notification(self, alert: Alert):
        """Send console notification for alert."""
        
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }.get(alert.severity, logging.INFO)
        
        self.logger.log(
            log_level,
            f"ALERT [{alert.severity.value.upper()}] {alert.message} "
            f"(Execution: {alert.execution_id})"
        )
    
    async def _send_email_notification(self, alert: Alert):
        """Send email notification for alert."""
        
        # This would implement email notification
        # For now, just log the action
        self.logger.debug(f"Would send email notification for alert {alert.alert_id}")
    
    async def _send_webhook_notification(self, alert: Alert):
        """Send webhook notification for alert."""
        
        # This would implement webhook notification
        # For now, just log the action
        self.logger.debug(f"Would send webhook notification for alert {alert.alert_id}")
    
    async def _update_execution_snapshot(self, event: TrackEvent):
        """Update execution snapshot with new event."""
        
        execution_id = event.execution_id
        
        async with self._monitoring_lock:
            # Get or create snapshot
            if execution_id not in self._active_executions:
                # This would typically be initialized when execution starts
                return
            
            snapshot = self._active_executions[execution_id]
            
            # Update based on event type
            if event.event_type in [EventType.EXECUTION_STARTED]:
                snapshot.current_state = "started"
                snapshot.progress_percent = 0.0
                
            elif event.event_type in [EventType.LEG_STARTED]:
                snapshot.legs_in_progress += 1
                snapshot.progress_percent = min(100.0, (snapshot.legs_completed + snapshot.legs_in_progress) / snapshot.legs_total * 100)
                
            elif event.event_type in [EventType.LEG_COMPLETED]:
                snapshot.legs_in_progress -= 1
                snapshot.legs_completed += 1
                snapshot.progress_percent = min(100.0, snapshot.legs_completed / snapshot.legs_total * 100)
                
            elif event.event_type in [EventType.LEG_FAILED]:
                snapshot.legs_in_progress -= 1
                snapshot.legs_failed += 1
                snapshot.progress_percent = min(100.0, snapshot.legs_completed / snapshot.legs_total * 100)
                
            elif event.event_type in [EventType.EXECUTION_COMPLETED]:
                snapshot.current_state = "completed"
                snapshot.progress_percent = 100.0
                snapshot.estimated_completion = datetime.utcnow()
                
            elif event.event_type in [EventType.EXECUTION_FAILED]:
                snapshot.current_state = "failed"
                snapshot.estimated_completion = datetime.utcnow()
            
            # Update timing information
            snapshot.elapsed_time = (datetime.utcnow() - snapshot.start_time).total_seconds()
            
            # Update performance metrics
            if snapshot.legs_total > 0:
                snapshot.success_rate = snapshot.legs_completed / snapshot.legs_total * 100
            
            # Update metrics from event
            if event.latency_ms > 0:
                # Update average latency (simple running average)
                if snapshot.average_latency_ms == 0:
                    snapshot.average_latency_ms = event.latency_ms
                else:
                    snapshot.average_latency_ms = (snapshot.average_latency_ms + event.latency_ms) / 2
            
            if event.memory_usage_mb > 0:
                snapshot.memory_usage_mb = event.memory_usage_mb
            
            if event.cpu_usage_percent > 0:
                snapshot.cpu_usage_percent = event.cpu_usage_percent
    
    async def start_monitoring_execution(
        self,
        execution_id: str,
        opportunity_id: str,
        strategy: str,
        total_legs: int
    ):
        """Start monitoring an execution."""
        
        async with self._monitoring_lock:
            # Create execution snapshot
            snapshot = ExecutionSnapshot(
                execution_id=execution_id,
                snapshot_time=datetime.utcnow(),
                opportunity_id=opportunity_id,
                strategy=strategy,
                current_state="starting",
                progress_percent=0.0,
                start_time=datetime.utcnow(),
                elapsed_time=0.0,
                legs_total=total_legs,
                legs_completed=0,
                legs_failed=0,
                legs_in_progress=0
            )
            
            self._active_executions[execution_id] = snapshot
            
            # Start monitoring task
            if execution_id not in self._monitoring_tasks:
                task = asyncio.create_task(self._monitor_execution_loop(execution_id))
                self._monitoring_tasks[execution_id] = task
        
        self.logger.info(f"Started monitoring execution {execution_id}")
    
    async def stop_monitoring_execution(self, execution_id: str):
        """Stop monitoring an execution."""
        
        async with self._monitoring_lock:
            if execution_id in self._monitoring_tasks:
                task = self._monitoring_tasks[execution_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self._monitoring_tasks[execution_id]
            
            if execution_id in self._active_executions:
                del self._active_executions[execution_id]
        
        self.logger.info(f"Stopped monitoring execution {execution_id}")
    
    async def _monitor_execution_loop(self, execution_id: str):
        """Main monitoring loop for an execution."""
        
        try:
            while execution_id in self._active_executions:
                # Update snapshot
                await self._update_monitoring_snapshot(execution_id)
                
                # Check for alerts
                await self._check_monitoring_alerts(execution_id)
                
                # Wait for next update
                await asyncio.sleep(self.config.monitoring_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Monitoring loop error for {execution_id}: {str(e)}")
    
    async def _update_monitoring_snapshot(self, execution_id: str):
        """Update monitoring snapshot with latest data."""
        
        snapshot = self._active_executions.get(execution_id)
        if not snapshot:
            return
        
        # Update elapsed time
        snapshot.elapsed_time = (datetime.utcnow() - snapshot.start_time).total_seconds()
        
        # Update throughput metrics
        execution_events = self._events_by_execution.get(execution_id, [])
        if execution_events and snapshot.elapsed_time > 0:
            events_per_minute = len(execution_events) / (snapshot.elapsed_time / 60)
            snapshot.throughput_per_minute = events_per_minute
        
        # Update snapshot timestamp
        snapshot.snapshot_time = datetime.utcnow()
    
    async def _check_monitoring_alerts(self, execution_id: str):
        """Check for monitoring-based alerts."""
        
        snapshot = self._active_executions.get(execution_id)
        if not snapshot:
            return
        
        # Check for slow execution
        if snapshot.elapsed_time > 300:  # 5 minutes
            await self._generate_monitoring_alert(
                execution_id,
                AlertSeverity.WARNING,
                "Slow Execution",
                f"Execution running for {snapshot.elapsed_time:.1f} seconds"
            )
        
        # Check for high failure rate
        if snapshot.legs_total > 0:
            failure_rate = snapshot.legs_failed / snapshot.legs_total * 100
            if failure_rate > 50:
                await self._generate_monitoring_alert(
                    execution_id,
                    AlertSeverity.ERROR,
                    "High Failure Rate",
                    f"Failure rate: {failure_rate:.1f}%"
                )
        
        # Check for resource usage
        if snapshot.cpu_usage_percent > 90:
            await self._generate_monitoring_alert(
                execution_id,
                AlertSeverity.WARNING,
                "High CPU Usage",
                f"CPU usage: {snapshot.cpu_usage_percent:.1f}%"
            )
    
    async def _generate_monitoring_alert(
        self,
        execution_id: str,
        severity: AlertSeverity,
        title: str,
        message: str
    ):
        """Generate monitoring alert."""
        
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            rule_id="monitoring",
            execution_id=execution_id,
            alert_time=datetime.utcnow(),
            event_type=EventType.PERFORMANCE_THRESHOLD,
            severity=severity,
            message=message,
            details={'title': title}
        )
        
        self._alerts.append(alert)
        
        self.logger.warning(f"Monitoring alert for {execution_id}: {title} - {message}")
    
    async def get_execution_events(
        self,
        execution_id: str,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get events for a specific execution."""
        
        with self._events_lock:
            events = list(self._events_by_execution.get(execution_id, []))
        
        # Filter by event type if specified
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Sort by timestamp and limit
        events.sort(key=lambda x: x.timestamp, reverse=True)
        events = events[:limit]
        
        return [
            {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'timestamp': event.timestamp.isoformat(),
                'event_data': event.event_data,
                'leg_id': event.leg_id,
                'bookmaker': event.bookmaker,
                'latency_ms': event.latency_ms
            }
            for event in events
        ]
    
    async def get_execution_metrics(
        self,
        execution_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        time_range: Optional[timedelta] = None
    ) -> List[Dict[str, Any]]:
        """Get performance metrics."""
        
        with self._metrics_lock:
            metrics = list(self._metrics)
        
        # Filter by execution ID
        if execution_id:
            metrics = [m for m in metrics if m.execution_id == execution_id]
        
        # Filter by metric name
        if metric_name:
            metrics = [m for m in metrics if m.metric_name == metric_name]
        
        # Filter by time range
        if time_range:
            cutoff_time = datetime.utcnow() - time_range
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]
        
        # Sort by timestamp
        metrics.sort(key=lambda x: x.timestamp)
        
        return [
            {
                'metric_id': metric.metric_id,
                'metric_name': metric.metric_name,
                'metric_type': metric.metric_type.value,
                'value': metric.value,
                'unit': metric.unit,
                'timestamp': metric.timestamp.isoformat(),
                'execution_id': metric.execution_id,
                'bookmaker': metric.bookmaker,
                'tags': metric.tags
            }
            for metric in metrics
        ]
    
    async def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get active alerts."""
        
        with self._alerts_lock:
            alerts = [a for a in self._alerts if not a.resolved]
        
        # Filter by severity
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Sort by alert time (most recent first)
        alerts.sort(key=lambda x: x.alert_time, reverse=True)
        alerts = alerts[:limit]
        
        return [
            {
                'alert_id': alert.alert_id,
                'rule_id': alert.rule_id,
                'execution_id': alert.execution_id,
                'event_type': alert.event_type.value,
                'severity': alert.severity.value,
                'message': alert.message,
                'details': alert.details,
                'alert_time': alert.alert_time.isoformat(),
                'acknowledged': alert.acknowledged,
                'event_count': alert.event_count
            }
            for alert in alerts
        ]
    
    async def acknowledge_alert(self, alert_id: str, user_id: str = "system") -> bool:
        """Acknowledge an alert."""
        
        with self._alerts_lock:
            for alert in self._alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    alert.details['acknowledged_by'] = user_id
                    alert.details['acknowledged_at'] = datetime.utcnow().isoformat()
                    return True
        
        return False
    
    async def resolve_alert(self, alert_id: str, user_id: str = "system") -> bool:
        """Resolve an alert."""
        
        with self._alerts_lock:
            for alert in self._alerts:
                if alert.alert_id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.utcnow()
                    alert.details['resolved_by'] = user_id
                    return True
        
        return False
    
    async def get_execution_snapshot(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current execution snapshot."""
        
        async with self._monitoring_lock:
            snapshot = self._active_executions.get(execution_id)
            if not snapshot:
                return None
        
        return {
            'execution_id': snapshot.execution_id,
            'opportunity_id': snapshot.opportunity_id,
            'strategy': snapshot.strategy,
            'current_state': snapshot.current_state,
            'progress_percent': snapshot.progress_percent,
            'start_time': snapshot.start_time.isoformat(),
            'elapsed_time': snapshot.elapsed_time,
            'estimated_completion': snapshot.estimated_completion.isoformat() if snapshot.estimated_completion else None,
            'legs_total': snapshot.legs_total,
            'legs_completed': snapshot.legs_completed,
            'legs_failed': snapshot.legs_failed,
            'legs_in_progress': snapshot.legs_in_progress,
            'success_rate': snapshot.success_rate,
            'average_latency_ms': snapshot.average_latency_ms,
            'throughput_per_minute': snapshot.throughput_per_minute,
            'memory_usage_mb': snapshot.memory_usage_mb,
            'cpu_usage_percent': snapshot.cpu_usage_percent,
            'network_requests': snapshot.network_requests,
            'risk_score': snapshot.risk_score,
            'active_alerts': snapshot.active_alerts,
            'critical_issues': snapshot.critical_issues,
            'data_quality_score': snapshot.data_quality_score,
            'execution_quality_score': snapshot.execution_quality_score,
            'snapshot_time': snapshot.snapshot_time.isoformat()
        }
    
    async def get_tracking_summary(self, execution_id: str) -> Dict[str, Any]:
        """Get comprehensive tracking summary for an execution."""
        
        # Get events
        events = await self.get_execution_events(execution_id, limit=1000)
        
        # Get metrics
        metrics = await self.get_execution_metrics(execution_id=execution_id)
        
        # Get snapshot
        snapshot = await self.get_execution_snapshot(execution_id)
        
        # Calculate summary statistics
        event_counts = defaultdict(int)
        timing_stats = []
        
        for event in events:
            event_counts[event['event_type']] += 1
            if event['latency_ms'] > 0:
                timing_stats.append(event['latency_ms'])
        
        avg_latency = sum(timing_stats) / len(timing_stats) if timing_stats else 0
        
        return {
            'execution_id': execution_id,
            'total_events': len(events),
            'event_counts': dict(event_counts),
            'average_latency_ms': avg_latency,
            'max_latency_ms': max(timing_stats) if timing_stats else 0,
            'total_metrics': len(metrics),
            'snapshot': snapshot,
            'tracking_level': self.config.tracking_level.value,
            'monitoring_active': execution_id in self._active_executions
        }
    
    async def _cleanup_old_events(self):
        """Clean up old events based on retention policy."""
        
        if self.config.event_retention_hours <= 0:
            return
        
        cutoff_time = datetime.utcnow() - timedelta(hours=self.config.event_retention_hours)
        
        with self._events_lock:
            # Clean main event log
            while self._events and self._events[0].timestamp < cutoff_time:
                self._events.popleft()
            
            # Clean execution-specific logs
            for execution_id in list(self._events_by_execution.keys()):
                execution_events = self._events_by_execution[execution_id]
                while execution_events and execution_events[0].timestamp < cutoff_time:
                    execution_events.popleft()
                
                # Remove empty execution logs
                if not execution_events:
                    del self._events_by_execution[execution_id]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get tracking performance statistics."""
        
        with self._stats_lock:
            # Calculate additional stats
            total_executions = len(self._active_executions)
            active_alerts = len([a for a in self._alerts if not a.resolved])
            
            self._performance_stats.update({
                'active_executions': total_executions,
                'total_events': len(self._events),
                'total_metrics': len(self._metrics),
                'active_alerts': active_alerts,
                'alert_rules_count': len(self._alert_rules)
            })
            
            return self._performance_stats.copy()
    
    async def export_tracking_data(
        self,
        execution_id: Optional[str] = None,
        time_range: Optional[timedelta] = None,
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """Export tracking data for analysis."""
        
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'execution_id': execution_id,
            'tracking_config': {
                'tracking_level': self.config.tracking_level.value,
                'enable_alerts': self.config.enable_alerts,
                'enable_performance_metrics': self.config.enable_performance_metrics
            }
        }
        
        if execution_id:
            # Export specific execution data
            events = await self.get_execution_events(execution_id, limit=10000)
            metrics = await self.get_execution_metrics(execution_id=execution_id)
            snapshot = await self.get_execution_snapshot(execution_id)
            
            export_data.update({
                'events': events,
                'metrics': metrics,
                'snapshot': snapshot,
                'summary': await self.get_tracking_summary(execution_id)
            })
        else:
            # Export all data
            with self._events_lock:
                all_events = list(self._events)
            
            with self._metrics_lock:
                all_metrics = list(self._metrics)
            
            export_data.update({
                'events': [
                    {
                        'event_id': event.event_id,
                        'execution_id': event.execution_id,
                        'event_type': event.event_type.value,
                        'timestamp': event.timestamp.isoformat(),
                        'event_data': event.event_data
                    }
                    for event in all_events
                ],
                'metrics': [
                    {
                        'metric_name': metric.metric_name,
                        'value': metric.value,
                        'timestamp': metric.timestamp.isoformat()
                    }
                    for metric in all_metrics
                ]
            })
        
        return export_data
    
    async def shutdown(self):
        """Graceful shutdown of the execution tracker."""
        
        self.logger.info("Shutting down Execution Tracker...")
        
        # Cancel monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self._monitoring_tasks:
            await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
        
        # Set shutdown event
        self._shutdown_event.set()
        
        self.logger.info("Execution Tracker shutdown complete")
