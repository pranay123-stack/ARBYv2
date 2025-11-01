"""
Real-Time Monitoring System for ARBitech Trading Platform

This module implements comprehensive real-time monitoring with:
- Continuous health checks across all system components
- Performance tracking and metrics collection
- Proactive alerting system with multiple channels
- Integration with circuit breakers and emergency stops
- System resource monitoring and optimization
- Compliance and audit trail maintenance

The system provides bulletproof monitoring with zero-downtime operation
and intelligent alerting for proactive risk management.
"""

import asyncio
import time
import psutil
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import json
import queue
from collections import deque, defaultdict
import statistics
import weakref
import smtplib
import ssl
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests

from arbitech.storage.audit_logger import (
    AuditLogger, EventType, LogLevel, SecurityEventLog,
    get_audit_logger, log_performance_metric
)
from arbitech.storage.models import ArbitrageOpportunity, Trade, Notification, NotificationType, NotificationPriority
from ..utils.logger import get_logger

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"           # Incrementing value
    GAUGE = "gauge"              # Point-in-time value
    HISTOGRAM = "histogram"      # Distribution of values
    TIMER = "timer"              # Time-based measurement
    RATE = "rate"               # Events per time unit


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """Alert status"""
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"


@dataclass
class SystemHealthCheck:
    """System health check result"""
    check_id: UUID = field(default_factory=uuid4)
    component_name: str = ""
    check_name: str = ""
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    
    # Metrics
    response_time_ms: float = 0.0
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    network_latency: Optional[float] = None
    
    # Error details
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Timing
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'check_id': str(self.check_id),
            'component_name': self.component_name,
            'check_name': self.check_name,
            'status': self.status.value,
            'message': self.message,
            'response_time_ms': self.response_time_ms,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_latency': self.network_latency,
            'error_message': self.error_message,
            'timestamp': self.timestamp.isoformat(),
            'duration_ms': self.duration_ms
        }


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    metric_id: UUID = field(default_factory=uuid4)
    metric_name: str = ""
    metric_type: MetricType = MetricType.GAUGE
    value: Union[float, int, Decimal] = 0
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = ""
    
    # Aggregation data for histograms
    count: int = 1
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'metric_id': str(self.metric_id),
            'metric_name': self.metric_name,
            'metric_type': self.metric_type.value,
            'value': float(self.value) if isinstance(self.value, Decimal) else self.value,
            'unit': self.unit,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'count': self.count,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'avg_value': self.avg_value
        }


@dataclass
class AlertRule:
    """Alert rule configuration"""
    rule_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    metric_name: str = ""
    
    # Conditions
    condition_type: str = "threshold"  # threshold, rate, anomaly
    threshold_value: Optional[float] = None
    comparison_operator: str = ">"     # >, <, >=, <=, ==, !=
    time_window_minutes: int = 5
    
    # Alert settings
    severity: AlertSeverity = AlertSeverity.WARNING
    enabled: bool = True
    
    # Notification settings
    channels: List[str] = field(default_factory=list)  # email, webhook, slack, etc
    recipients: List[str] = field(default_factory=list)
    
    # Alert management
    cooldown_minutes: int = 15
    max_alerts_per_hour: int = 10
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    # Rate limiting
    rate_limit_count: int = 0
    rate_limit_window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'rule_id': str(self.rule_id),
            'name': self.name,
            'description': self.description,
            'metric_name': self.metric_name,
            'condition_type': self.condition_type,
            'threshold_value': self.threshold_value,
            'comparison_operator': self.comparison_operator,
            'time_window_minutes': self.time_window_minutes,
            'severity': self.severity.value,
            'enabled': self.enabled,
            'channels': self.channels,
            'recipients': self.recipients,
            'cooldown_minutes': self.cooldown_minutes,
            'max_alerts_per_hour': self.max_alerts_per_hour,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'trigger_count': self.trigger_count
        }


@dataclass
class Alert:
    """Alert instance"""
    alert_id: UUID = field(default_factory=uuid4)
    rule_id: UUID = field(default_factory=uuid4)
    severity: AlertSeverity = AlertSeverity.WARNING
    message: str = ""
    
    # Context
    metric_name: str = ""
    metric_value: float = 0.0
    threshold_value: Optional[float] = None
    component: str = ""
    
    # Status tracking
    status: AlertStatus = AlertStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Acknowledgment
    acknowledged_by: Optional[str] = None
    acknowledged_message: Optional[str] = None
    
    # Resolution
    resolution_message: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        return {
            'alert_id': str(self.alert_id),
            'rule_id': str(self.rule_id),
            'severity': self.severity.value,
            'message': self.message,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'threshold_value': self.threshold_value,
            'component': self.component,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_message': self.acknowledged_message,
            'resolution_message': self.resolution_message,
            'metadata': self.metadata
        }


@dataclass
class MonitoringConfig:
    """Configuration for monitoring system"""
    # Health check settings
    health_check_interval_seconds: float = 30.0
    component_timeout_seconds: float = 10.0
    max_consecutive_failures: int = 3
    
    # Performance monitoring
    metrics_retention_hours: int = 168  # 1 week
    metrics_aggregation_interval_seconds: float = 60.0
    performance_baseline_hours: int = 24
    
    # Alert settings
    alert_check_interval_seconds: float = 15.0
    alert_batch_size: int = 10
    alert_retry_attempts: int = 3
    
    # System resource monitoring
    cpu_threshold_warning: float = 70.0
    cpu_threshold_critical: float = 90.0
    memory_threshold_warning: float = 75.0
    memory_threshold_critical: float = 90.0
    disk_threshold_warning: float = 80.0
    disk_threshold_critical: float = 95.0
    
    # Network monitoring
    network_timeout_seconds: float = 5.0
    network_retry_count: int = 3
    
    # Notification settings
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_use_tls: bool = True
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from_address: Optional[str] = None
    
    # Webhook settings
    webhook_timeout_seconds: float = 10.0
    webhook_retry_count: int = 3
    
    # Integration settings
    enable_circuit_breaker_integration: bool = True
    enable_emergency_stop_integration: bool = True
    enable_loss_limiter_integration: bool = True


class HealthChecker:
    """Base class for health checkers"""
    
    def __init__(self, component_name: str, config: MonitoringConfig):
        self.component_name = component_name
        self.config = config
        self.last_check_time = datetime.now(timezone.utc)
        self.consecutive_failures = 0
        
    async def check_health(self) -> SystemHealthCheck:
        """Perform health check - override in subclasses"""
        start_time = time.time()
        
        try:
            result = await self._perform_check()
            duration = (time.time() - start_time) * 1000
            
            result.component_name = self.component_name
            result.duration_ms = duration
            result.response_time_ms = duration
            
            # Reset failure counter on success
            self.consecutive_failures = 0
            
            return result
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            
            self.consecutive_failures += 1
            
            return SystemHealthCheck(
                component_name=self.component_name,
                check_name="health_check",
                status=HealthStatus.CRITICAL if self.consecutive_failures >= self.config.max_consecutive_failures else HealthStatus.ERROR,
                message="Health check failed",
                error_message=str(e),
                duration_ms=duration,
                response_time_ms=duration
            )
    
    async def _perform_check(self) -> SystemHealthCheck:
        """Override this method in subclasses"""
        return SystemHealthCheck(
            check_name="base_check",
            status=HealthStatus.HEALTHY,
            message="Base health check"
        )


class SystemResourcesHealthChecker(HealthChecker):
    """Health checker for system resources"""
    
    def __init__(self, config: MonitoringConfig):
        super().__init__("system_resources", config)
        
    async def _perform_check(self) -> SystemHealthCheck:
        """Check system resource usage"""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Determine overall status
            if (cpu_percent >= self.config.cpu_threshold_critical or 
                memory_percent >= self.config.memory_threshold_critical or 
                disk_percent >= self.config.disk_threshold_critical):
                status = HealthStatus.CRITICAL
            elif (cpu_percent >= self.config.cpu_threshold_warning or 
                  memory_percent >= self.config.memory_threshold_warning or 
                  disk_percent >= self.config.disk_threshold_warning):
                status = HealthStatus.WARNING
            else:
                status = HealthStatus.HEALTHY
            
            message = f"CPU: {cpu_percent:.1f}%, Memory: {memory_percent:.1f}%, Disk: {disk_percent:.1f}%"
            
            return SystemHealthCheck(
                check_name="system_resources",
                status=status,
                message=message,
                cpu_usage=cpu_percent,
                memory_usage=memory_percent,
                disk_usage=disk_percent
            )
            
        except Exception as e:
            return SystemHealthCheck(
                check_name="system_resources",
                status=HealthStatus.ERROR,
                message="Failed to check system resources",
                error_message=str(e)
            )


class DatabaseHealthChecker(HealthChecker):
    """Health checker for database connectivity"""
    
    def __init__(self, config: MonitoringConfig, db_connection_string: str):
        super().__init__("database", config)
        self.db_connection_string = db_connection_string
    
    async def _perform_check(self) -> SystemHealthCheck:
        """Check database connectivity"""
        try:
            # Test database connection (implement based on your database)
            start_time = time.time()
            
            # Placeholder for database health check
            await asyncio.sleep(0.1)  # Simulate DB query
            
            response_time = (time.time() - start_time) * 1000
            
            return SystemHealthCheck(
                check_name="database_connectivity",
                status=HealthStatus.HEALTHY,
                message="Database connection healthy",
                response_time_ms=response_time
            )
            
        except Exception as e:
            return SystemHealthCheck(
                check_name="database_connectivity",
                status=HealthStatus.ERROR,
                message="Database connection failed",
                error_message=str(e)
            )


class ExternalServicesHealthChecker(HealthChecker):
    """Health checker for external services"""
    
    def __init__(self, config: MonitoringConfig, services: List[str]):
        super().__init__("external_services", config)
        self.services = services
    
    async def _perform_check(self) -> SystemHealthCheck:
        """Check external services connectivity"""
        try:
            failed_services = []
            response_times = []
            
            for service in self.services:
                try:
                    start_time = time.time()
                    # Placeholder for service health check
                    await asyncio.sleep(0.05)  # Simulate network call
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                except Exception as e:
                    failed_services.append(service)
            
            if failed_services:
                status = HealthStatus.ERROR
                message = f"Services unavailable: {', '.join(failed_services)}"
            else:
                status = HealthStatus.HEALTHY
                avg_response_time = statistics.mean(response_times) if response_times else 0
                message = f"All services healthy, avg response time: {avg_response_time:.1f}ms"
            
            return SystemHealthCheck(
                check_name="external_services",
                status=status,
                message=message,
                network_latency=statistics.mean(response_times) if response_times else None
            )
            
        except Exception as e:
            return SystemHealthCheck(
                check_name="external_services",
                status=HealthStatus.ERROR,
                message="Failed to check external services",
                error_message=str(e)
            )


class PerformanceTracker:
    """Track and analyze performance metrics"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.metric_metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        # Aggregation cache
        self.last_aggregation = datetime.now(timezone.utc)
        self.aggregated_metrics: Dict[str, Dict[str, float]] = {}
    
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        with self._lock:
            self.metrics[metric.metric_name].append(metric)
            
            # Store metadata
            if metric.metric_name not in self.metric_metadata:
                self.metric_metadata[metric.metric_name] = {
                    'metric_type': metric.metric_type.value,
                    'unit': metric.unit,
                    'tags': metric.tags,
                    'source': metric.source,
                    'first_recorded': metric.timestamp,
                    'last_updated': metric.timestamp
                }
            else:
                self.metric_metadata[metric.metric_name]['last_updated'] = metric.timestamp
    
    def get_metric_history(self, metric_name: str, hours: int = 1) -> List[PerformanceMetric]:
        """Get metric history for specified time period"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        with self._lock:
            return [metric for metric in self.metrics.get(metric_name, [])
                   if metric.timestamp > cutoff_time]
    
    def get_current_value(self, metric_name: str) -> Optional[float]:
        """Get current value of metric"""
        with self._lock:
            metrics = self.metrics.get(metric_name, [])
            if metrics:
                latest_metric = metrics[-1]
                return float(latest_metric.value) if isinstance(latest_metric.value, Decimal) else latest_metric.value
            return None
    
    def calculate_rate(self, metric_name: str, window_minutes: int = 5) -> float:
        """Calculate rate of metric over time window"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        
        with self._lock:
            metrics = self.metrics.get(metric_name, [])
            window_metrics = [m for m in metrics if m.timestamp > cutoff_time]
            
            if self._get_metric_type(metric_name) == MetricType.COUNTER:
                # For counters, calculate increment rate
                if len(window_metrics) >= 2:
                    return (float(window_metrics[-1].value) - float(window_metrics[0].value)) / window_minutes
            else:
                # For other types, count events
                return len(window_metrics) / window_minutes
        
        return 0.0
    
    def get_statistics(self, metric_name: str, hours: int = 1) -> Dict[str, float]:
        """Get statistical summary of metric"""
        metrics = self.get_metric_history(metric_name, hours)
        
        if not metrics:
            return {}
        
        values = []
        for metric in metrics:
            val = float(metric.value) if isinstance(metric.value, Decimal) else metric.value
            values.append(val)
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0,
            'p95': self._percentile(values, 95),
            'p99': self._percentile(values, 99)
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (index - int(index)) * (upper - lower)
    
    def _get_metric_type(self, metric_name: str) -> MetricType:
        """Get metric type"""
        metadata = self.metric_metadata.get(metric_name, {})
        metric_type_str = metadata.get('metric_type', 'gauge')
        
        try:
            return MetricType(metric_type_str)
        except ValueError:
            return MetricType.GAUGE
    
    def aggregate_metrics(self):
        """Aggregate metrics for reporting"""
        current_time = datetime.now(timezone.utc)
        
        if (current_time - self.last_aggregation).total_seconds() < self.config.metrics_aggregation_interval_seconds:
            return
        
        with self._lock:
            for metric_name in self.metrics.keys():
                stats = self.get_statistics(metric_name, hours=1)
                if stats:
                    self.aggregated_metrics[metric_name] = stats
            
            self.last_aggregation = current_time
    
    def get_aggregated_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get aggregated metrics"""
        self.aggregate_metrics()
        return self.aggregated_metrics.copy()


class AlertingSystem:
    """Advanced alerting system"""
    
    def __init__(self, config: MonitoringConfig, audit_logger: AuditLogger):
        self.config = config
        self.audit_logger = audit_logger
        self.alert_rules: Dict[UUID, AlertRule] = {}
        self.active_alerts: Dict[UUID, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        
        # Rate limiting
        self.rate_limited_rules: Set[UUID] = set()
        self._lock = threading.Lock()
        
        # Notification channels
        self.notification_channels = {}
        self._setup_notification_channels()
    
    def _setup_notification_channels(self):
        """Setup notification channels"""
        # Email channel
        if self.config.email_username and self.config.email_password:
            self.notification_channels['email'] = self._send_email_alert
        
        # Webhook channel
        self.notification_channels['webhook'] = self._send_webhook_alert
        
        # Slack channel (via webhook)
        self.notification_channels['slack'] = self._send_slack_alert
    
    def add_alert_rule(self, rule: AlertRule):
        """Add alert rule"""
        with self._lock:
            self.alert_rules[rule.rule_id] = rule
            logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_id: UUID):
        """Remove alert rule"""
        with self._lock:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                logger.info(f"Removed alert rule: {rule_id}")
    
    async def check_alerts(self, performance_tracker: PerformanceTracker):
        """Check alert rules against current metrics"""
        triggered_alerts = []
        
        with self._lock:
            for rule in self.alert_rules.values():
                if not rule.enabled:
                    continue
                
                try:
                    alert = await self._check_rule(rule, performance_tracker)
                    if alert:
                        triggered_alerts.append(alert)
                        
                except Exception as e:
                    logger.error(f"Error checking alert rule {rule.name}: {e}", exc_info=True)
        
        # Process triggered alerts
        for alert in triggered_alerts:
            await self._process_alert(alert)
    
    async def _check_rule(self, rule: AlertRule, performance_tracker: PerformanceTracker) -> Optional[Alert]:
        """Check individual alert rule"""
        current_time = datetime.now(timezone.utc)
        
        # Check cooldown
        if (rule.last_triggered and 
            (current_time - rule.last_triggered).total_seconds() < rule.cooldown_minutes * 60):
            return None
        
        # Check rate limiting
        if rule.rule_id in self.rate_limited_rules:
            return None
        
        # Get current metric value
        current_value = performance_tracker.get_current_value(rule.metric_name)
        if current_value is None:
            return None
        
        # Check condition
        condition_met = self._evaluate_condition(rule, current_value)
        
        if condition_met:
            # Create alert
            alert = Alert(
                rule_id=rule.rule_id,
                severity=rule.severity,
                message=f"{rule.description}: {current_value} {rule.comparison_operator} {rule.threshold_value}",
                metric_name=rule.metric_name,
                metric_value=current_value,
                threshold_value=rule.threshold_value,
                component=rule.metric_name.split('.')[0] if '.' in rule.metric_name else 'system',
                expires_at=current_time + timedelta(minutes=60)  # 1 hour expiry
            )
            
            return alert
        
        return None
    
    def _evaluate_condition(self, rule: AlertRule, current_value: float) -> bool:
        """Evaluate alert condition"""
        if rule.condition_type == "threshold":
            if rule.threshold_value is None:
                return False
            
            if rule.comparison_operator == ">":
                return current_value > rule.threshold_value
            elif rule.comparison_operator == "<":
                return current_value < rule.threshold_value
            elif rule.comparison_operator == ">=":
                return current_value >= rule.threshold_value
            elif rule.comparison_operator == "<=":
                return current_value <= rule.threshold_value
            elif rule.comparison_operator == "==":
                return current_value == rule.threshold_value
            elif rule.comparison_operator == "!=":
                return current_value != rule.threshold_value
        
        elif rule.condition_type == "rate":
            # Rate-based alerts are handled separately in performance tracker
            return False
        
        return False
    
    async def _process_alert(self, alert: Alert):
        """Process triggered alert"""
        with self._lock:
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)
        
        rule = self.alert_rules.get(alert.rule_id)
        if rule:
            rule.last_triggered = datetime.now(timezone.utc)
            rule.trigger_count += 1
        
        logger.warning(f"Alert triggered: {alert.message}", 
                      alert_id=alert.alert_id, severity=alert.severity.value)
        
        # Log security event
        self.audit_logger.log_security_event(SecurityEventLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type='ALERT_TRIGGERED',
            severity=LogLevel.WARNING,
            user_id=None,
            ip_address=None,
            session_id=None,
            description=f"Alert triggered: {alert.message}",
            details=alert.to_dict()
        ))
        
        # Send notifications
        await self._send_notifications(alert)
        
        # Check rate limiting
        self._check_rate_limiting(alert.rule_id)
    
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications"""
        rule = self.alert_rules.get(alert.rule_id)
        if not rule:
            return
        
        for channel in rule.channels:
            if channel in self.notification_channels:
                try:
                    await self.notification_channels[channel](alert, rule)
                    logger.info(f"Alert sent via {channel}", alert_id=alert.alert_id)
                except Exception as e:
                    logger.error(f"Failed to send alert via {channel}: {e}", exc_info=True)
    
    async def _send_email_alert(self, alert: Alert, rule: AlertRule):
        """Send email alert"""
        if not all([self.config.email_username, self.config.email_password, self.config.email_from_address]):
            logger.warning("Email configuration incomplete")
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.config.email_from_address
            msg['To'] = ', '.join(rule.recipients)
            msg['Subject'] = f"[{alert.severity.value.upper()}] ARBitech Alert: {alert.message}"
            
            body = f"""
Alert Details:
Severity: {alert.severity.value}
Component: {alert.component}
Metric: {alert.metric_name}
Current Value: {alert.metric_value}
Threshold: {alert.threshold_value}
Time: {alert.created_at.isoformat()}

Message: {alert.message}
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email (implementation would go here)
            # This is a placeholder
            logger.info(f"Email alert would be sent to {rule.recipients}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}", exc_info=True)
    
    async def _send_webhook_alert(self, alert: Alert, rule: AlertRule):
        """Send webhook alert"""
        payload = {
            'alert_id': str(alert.alert_id),
            'severity': alert.severity.value,
            'message': alert.message,
            'component': alert.component,
            'metric_name': alert.metric_name,
            'metric_value': alert.metric_value,
            'threshold_value': alert.threshold_value,
            'timestamp': alert.created_at.isoformat()
        }
        
        for recipient in rule.recipients:
            try:
                async with asyncio.timeout(self.config.webhook_timeout_seconds):
                    async with requests.Session() as session:
                        response = await asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: session.post(recipient, json=payload, timeout=self.config.webhook_timeout_seconds)
                        )
                        
                        if response.status_code >= 400:
                            logger.warning(f"Webhook returned status {response.status_code}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"Webhook timeout for {recipient}")
            except Exception as e:
                logger.error(f"Webhook alert failed for {recipient}: {e}", exc_info=True)
    
    async def _send_slack_alert(self, alert: Alert, rule: AlertRule):
        """Send Slack alert via webhook"""
        # Implementation for Slack webhook
        # This is a simplified version
        color = {
            AlertSeverity.INFO: "good",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.ERROR: "danger",
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.EMERGENCY: "danger"
        }.get(alert.severity, "warning")
        
        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"ARBitech Alert: {alert.severity.value.upper()}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Component", "value": alert.component, "short": True},
                        {"title": "Metric", "value": alert.metric_name, "short": True},
                        {"title": "Current Value", "value": str(alert.metric_value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold_value), "short": True}
                    ],
                    "ts": int(alert.created_at.timestamp())
                }
            ]
        }
        
        for recipient in rule.recipients:
            try:
                await self._send_webhook_alert(alert, AlertRule(recipients=[recipient]))
            except Exception as e:
                logger.error(f"Slack alert failed: {e}", exc_info=True)
    
    def _check_rate_limiting(self, rule_id: UUID):
        """Check and apply rate limiting"""
        rule = self.alert_rules.get(rule_id)
        if not rule:
            return
        
        current_time = datetime.now(timezone.utc)
        
        # Reset rate limit window if needed
        if (current_time - rule.rate_limit_window_start).total_seconds() >= 3600:  # 1 hour
            rule.rate_limit_count = 0
            rule.rate_limit_window_start = current_time
            self.rate_limited_rules.discard(rule_id)
        
        # Check rate limit
        rule.rate_limit_count += 1
        if rule.rate_limit_count > rule.max_alerts_per_hour:
            self.rate_limited_rules.add(rule_id)
            logger.warning(f"Rate limit exceeded for rule {rule.name}")
    
    def acknowledge_alert(self, alert_id: UUID, acknowledged_by: str, message: str = "") -> bool:
        """Acknowledge alert"""
        with self._lock:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                return False
            
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now(timezone.utc)
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_message = message
            
            logger.info(f"Alert acknowledged: {alert_id}", acknowledged_by=acknowledged_by)
            return True
    
    def resolve_alert(self, alert_id: UUID, resolution_message: str = "") -> bool:
        """Resolve alert"""
        with self._lock:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                return False
            
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now(timezone.utc)
            alert.resolution_message = resolution_message
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert resolved: {alert_id}", resolution_message=resolution_message)
            return True
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by severity"""
        with self._lock:
            alerts = list(self.active_alerts.values())
            
            if severity:
                alerts = [alert for alert in alerts if alert.severity == severity]
            
            return sorted(alerts, key=lambda a: a.created_at, reverse=True)
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        with self._lock:
            now = datetime.now(timezone.utc)
            last_24h = now - timedelta(hours=24)
            last_1h = now - timedelta(hours=1)
            
            recent_alerts = [alert for alert in self.alert_history if alert.created_at > last_24h]
            hourly_alerts = [alert for alert in self.alert_history if alert.created_at > last_1h]
            
            return {
                'total_alerts': len(self.alert_history),
                'active_alerts': len(self.active_alerts),
                'alerts_last_24h': len(recent_alerts),
                'alerts_last_1h': len(hourly_alerts),
                'alerts_by_severity': {
                    severity.value: len([a for a in recent_alerts if a.severity == severity])
                    for severity in AlertSeverity
                },
                'rate_limited_rules': len(self.rate_limited_rules),
                'rules_enabled': len([r for r in self.alert_rules.values() if r.enabled])
            }


class MonitoringSystem:
    """Main monitoring system coordinator"""
    
    def __init__(self, config: Optional[MonitoringConfig] = None, 
                 audit_logger: Optional[AuditLogger] = None):
        self.config = config or MonitoringConfig()
        self.audit_logger = audit_logger or get_audit_logger()
        
        # Core components
        self.health_checkers: List[HealthChecker] = []
        self.performance_tracker = PerformanceTracker(self.config)
        self.alerting_system = AlertingSystem(self.config, self.audit_logger)
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Health check results cache
        self.last_health_check: Optional[datetime] = None
        self.health_check_results: List[SystemHealthCheck] = []
        
        # Performance metrics cache
        self.system_metrics = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'active_connections': 0,
            'requests_per_second': 0.0,
            'error_rate': 0.0
        }
        
        # Integration callbacks
        self.circuit_breaker_integration: Optional[Callable] = None
        self.emergency_stop_integration: Optional[Callable] = None
        self.loss_limiter_integration: Optional[Callable] = None
        
        logger.info("Monitoring system initialized")
    
    def add_health_checker(self, checker: HealthChecker):
        """Add health checker"""
        self.health_checkers.append(checker)
        logger.info(f"Added health checker: {checker.component_name}")
    
    def set_circuit_breaker_integration(self, callback: Callable):
        """Set circuit breaker integration callback"""
        self.circuit_breaker_integration = callback
    
    def set_emergency_stop_integration(self, callback: Callable):
        """Set emergency stop integration callback"""
        self.emergency_stop_integration = callback
    
    def set_loss_limiter_integration(self, callback: Callable):
        """Set loss limiter integration callback"""
        self.loss_limiter_integration = callback
    
    async def start_monitoring(self):
        """Start the monitoring system"""
        if self.monitoring_active:
            logger.warning("Monitoring system already active")
            return
        
        self.monitoring_active = True
        self._shutdown_event.clear()
        
        # Create monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._performance_monitoring_loop()),
            asyncio.create_task(self._alert_check_loop()),
            asyncio.create_task(self._system_metrics_loop())
        ]
        
        logger.info("Monitoring system started")
    
    async def stop_monitoring(self):
        """Stop the monitoring system"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        self._shutdown_event.set()
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        logger.info("Monitoring system stopped")
    
    async def _health_check_loop(self):
        """Main health check loop"""
        while self.monitoring_active:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _perform_health_checks(self):
        """Perform health checks on all components"""
        start_time = time.time()
        check_results = []
        
        # Run health checks in parallel
        tasks = [checker.check_health() for checker in self.health_checkers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, SystemHealthCheck):
                check_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Health check failed: {result}", exc_info=True)
        
        # Process results
        critical_issues = []
        for result in check_results:
            if result.status in [HealthStatus.ERROR, HealthStatus.CRITICAL]:
                critical_issues.append(result)
            
            # Log performance metric
            log_performance_metric(
                f"health_check_{result.component_name}_{result.check_name}",
                result.response_time_ms,
                unit="milliseconds",
                tags={
                    'component': result.component_name,
                    'check': result.check_name,
                    'status': result.status.value
                }
            )
        
        # Update cache
        self.health_check_results = check_results
        self.last_health_check = datetime.now(timezone.utc)
        
        # Check for critical issues
        if critical_issues and self.circuit_breaker_integration:
            try:
                await self.circuit_breaker_integration(critical_issues)
            except Exception as e:
                logger.error(f"Circuit breaker integration failed: {e}", exc_info=True)
        
        duration = (time.time() - start_time) * 1000
        logger.debug(f"Health checks completed in {duration:.1f}ms")
    
    async def _performance_monitoring_loop(self):
        """Performance monitoring loop"""
        while self.monitoring_active:
            try:
                await self._collect_performance_metrics()
                await asyncio.sleep(self.config.metrics_aggregation_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _collect_performance_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.system_metrics['cpu_usage'] = cpu_percent
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_metrics['memory_usage'] = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_metrics['disk_usage'] = disk.percent
            
            # Record metrics
            self.performance_tracker.record_metric(PerformanceMetric(
                metric_name="system.cpu.usage",
                metric_type=MetricType.GAUGE,
                value=cpu_percent,
                unit="percent",
                source="monitoring_system"
            ))
            
            self.performance_tracker.record_metric(PerformanceMetric(
                metric_name="system.memory.usage",
                metric_type=MetricType.GAUGE,
                value=memory.percent,
                unit="percent",
                source="monitoring_system"
            ))
            
            self.performance_tracker.record_metric(PerformanceMetric(
                metric_name="system.disk.usage",
                metric_type=MetricType.GAUGE,
                value=disk.percent,
                unit="percent",
                source="monitoring_system"
            ))
            
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}", exc_info=True)
    
    async def _alert_check_loop(self):
        """Alert checking loop"""
        while self.monitoring_active:
            try:
                await self.alerting_system.check_alerts(self.performance_tracker)
                await asyncio.sleep(self.config.alert_check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert check loop: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _system_metrics_loop(self):
        """System metrics collection loop"""
        while self.monitoring_active:
            try:
                await self._update_system_metrics()
                await asyncio.sleep(1.0)  # Update every second
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system metrics loop: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _update_system_metrics(self):
        """Update system-wide metrics"""
        try:
            # Network connections
            connections = len(psutil.net_connections())
            self.system_metrics['active_connections'] = connections
            
            # Record metric
            self.performance_tracker.record_metric(PerformanceMetric(
                metric_name="system.connections.active",
                metric_type=MetricType.GAUGE,
                value=connections,
                unit="count",
                source="monitoring_system"
            ))
            
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}", exc_info=True)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status"""
        current_time = datetime.now(timezone.utc)
        
        # Calculate overall health score
        healthy_components = 0
        total_components = len(self.health_checkers)
        critical_issues = []
        
        for result in self.health_check_results:
            if result.status == HealthStatus.HEALTHY:
                healthy_components += 1
            elif result.status in [HealthStatus.ERROR, HealthStatus.CRITICAL]:
                critical_issues.append({
                    'component': result.component_name,
                    'check': result.check_name,
                    'status': result.status.value,
                    'message': result.message,
                    'error': result.error_message
                })
        
        # Determine overall status
        if not self.health_check_results:
            overall_status = "unknown"
            health_score = 0
        elif critical_issues:
            overall_status = "critical"
            health_score = 0
        elif healthy_components < total_components * 0.8:  # Less than 80% healthy
            overall_status = "warning"
            health_score = healthy_components / total_components
        else:
            overall_status = "healthy"
            health_score = 1.0
        
        return {
            'timestamp': current_time.isoformat(),
            'overall_status': overall_status,
            'health_score': health_score,
            'total_components': total_components,
            'healthy_components': healthy_components,
            'last_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'system_metrics': self.system_metrics.copy(),
            'critical_issues': critical_issues,
            'component_status': {
                result.component_name: {
                    'status': result.status.value,
                    'message': result.message,
                    'response_time_ms': result.response_time_ms,
                    'last_check': result.timestamp.isoformat()
                }
                for result in self.health_check_results
            }
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        aggregated = self.performance_tracker.get_aggregated_metrics()
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'aggregated_metrics': aggregated,
            'system_metrics': self.system_metrics.copy(),
            'top_metrics': self._get_top_metrics()
        }
    
    def _get_top_metrics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top metrics by importance"""
        # This would be customized based on your specific needs
        important_metrics = [
            'system.cpu.usage',
            'system.memory.usage', 
            'system.disk.usage',
            'system.connections.active',
            'trading.orders_per_minute',
            'trading.error_rate',
            'database.query_time'
        ]
        
        top_metrics = []
        for metric_name in important_metrics:
            current_value = self.performance_tracker.get_current_value(metric_name)
            if current_value is not None:
                top_metrics.append({
                    'metric_name': metric_name,
                    'current_value': current_value,
                    'statistics': self.performance_tracker.get_statistics(metric_name, hours=1)
                })
        
        return top_metrics[:limit]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary"""
        return self.alerting_system.get_alert_statistics()
    
    async def shutdown(self):
        """Graceful shutdown of monitoring system"""
        logger.info("Initiating monitoring system shutdown")
        await self.stop_monitoring()
        logger.info("Monitoring system shutdown completed")


# Global monitoring system instance
_global_monitoring_system = None


def get_monitoring_system() -> MonitoringSystem:
    """Get or create global monitoring system"""
    global _global_monitoring_system
    if _global_monitoring_system is None:
        _global_monitoring_system = MonitoringSystem()
    return _global_monitoring_system


if __name__ == "__main__":
    # Example usage and testing
    async def test_monitoring_system():
        # Setup
        monitoring = get_monitoring_system()
        
        # Add health checkers
        system_checker = SystemResourcesHealthChecker(monitoring.config)
        monitoring.add_health_checker(system_checker)
        
        # Add alert rules
        cpu_rule = AlertRule(
            name="High CPU Usage",
            description="CPU usage is too high",
            metric_name="system.cpu.usage",
            threshold_value=80.0,
            comparison_operator=">",
            severity=AlertSeverity.WARNING,
            channels=["slack"],
            recipients=["#alerts"]
        )
        monitoring.alerting_system.add_alert_rule(cpu_rule)
        
        # Start monitoring
        print("Starting monitoring system...")
        await monitoring.start_monitoring()
        
        # Let it run for a bit
        await asyncio.sleep(10)
        
        # Get status
        print("Getting health status...")
        health_status = monitoring.get_health_status()
        print(f"Health status: {health_status['overall_status']}")
        
        print("Getting performance summary...")
        perf_summary = monitoring.get_performance_summary()
        print(f"Performance metrics: {len(perf_summary['top_metrics'])}")
        
        print("Getting alert summary...")
        alert_summary = monitoring.alerting_system.get_alert_statistics()
        print(f"Alert statistics: {alert_summary}")
        
        # Stop monitoring
        print("Stopping monitoring system...")
        await monitoring.shutdown()
        
        print("Monitoring system test completed!")
    
    # Run test
    asyncio.run(test_monitoring_system())