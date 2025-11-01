"""
Comprehensive Audit and Logging System for ARBitech Trading Platform

This module provides structured logging, audit trails, and comprehensive logging
for trade execution, system errors, user actions, performance metrics, and security events.
"""

import structlog
import sys
import traceback
import time
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
import logging.handlers


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    AUDIT = "AUDIT"
    SECURITY = "SECURITY"
    TRADE = "TRADE"


class EventType(Enum):
    """Event type enumeration for audit logging"""
    TRADE_EXECUTION = "TRADE_EXECUTION"
    USER_ACTION = "USER_ACTION"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    SECURITY_EVENT = "SECURITY_EVENT"
    PERFORMANCE_METRIC = "PERFORMANCE_METRIC"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    DATA_ACCESS = "DATA_ACCESS"
    AUTHENTICATION = "AUTHENTICATION"
    SYSTEM_STARTUP = "SYSTEM_STARTUP"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"


@dataclass
class AuditEntry:
    """Audit entry data structure"""
    timestamp: str
    event_type: EventType
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    action: str
    resource: Optional[str]
    details: Dict[str, Any]
    severity: LogLevel
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit entry to dictionary"""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "action": self.action,
            "resource": self.resource,
            "details": self.details,
            "severity": self.severity.value,
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id
        }
    
    def to_json(self) -> str:
        """Convert audit entry to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class TradeExecutionLog:
    """Trade execution log data structure"""
    timestamp: str
    trade_id: str
    symbol: str
    side: str  # BUY/SELL
    quantity: float
    price: Optional[float]
    order_type: str
    user_id: str
    status: str
    execution_time_ms: Optional[float]
    exchange: str
    error_message: Optional[str] = None
    details: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SecurityEventLog:
    """Security event log data structure"""
    timestamp: str
    event_type: str
    severity: LogLevel
    user_id: Optional[str]
    ip_address: Optional[str]
    session_id: Optional[str]
    description: str
    details: Dict[str, Any]
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AuditLogger:
    """
    Comprehensive Audit and Logging System
    
    Provides structured logging for:
    - Trade execution
    - System errors
    - User actions
    - Performance metrics
    - Security events
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the audit logger"""
        self.config = config or self._get_default_config()
        self.logs_dir = Path(self.config.get('logs_directory', '/workspace/arbitech/logs'))
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize trace ID generator
        self.trace_counter = 0
        
        # Setup structured logging
        self._setup_structured_logging()
        
        # Initialize audit trail storage
        self.audit_trail_file = self.logs_dir / 'audit_trail.jsonl'
        self.trade_logs_file = self.logs_dir / 'trade_execution.jsonl'
        self.security_logs_file = self.logs_dir / 'security_events.jsonl'
        self.performance_logs_file = self.logs_dir / 'performance_metrics.jsonl'
        
        # User context
        self._user_context = {}
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'logs_directory': '/workspace/arbitech/logs',
            'max_log_size': 100 * 1024 * 1024,  # 100MB
            'backup_count': 10,
            'json_pretty_print': False,
            'include_source': True,
            'capture_exceptions': True,
            'sensitive_fields': ['password', 'token', 'secret', 'key', 'api_key'],
            'redact_sensitive_data': True
        }
    
    def _setup_structured_logging(self):
        """Setup structured logging with structlog"""
        
        # Configure processors
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]
        
        # Add sensitive data filter if enabled
        if self.config.get('redact_sensitive_data'):
            processors.append(self._redact_sensitive_data)
        
        # Add JSON renderer or pretty printer
        if self.config.get('json_pretty_print'):
            processors.append(structlog.processors.JSONRenderer(indent=2))
        else:
            processors.append(structlog.processors.JSONRenderer())
        
        # Configure structlog
        structlog.configure(
            processors=processors,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            cache_logger_on_first_use=True,
        )
        
        # Setup standard library logging
        self._setup_stdlib_logging()
    
    def _setup_stdlib_logging(self):
        """Setup standard library logging with rotation"""
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        json_formatter = logging.Formatter('%(message)s')
        
        # Setup different handlers
        
        # Error handler with rotation
        error_handler = logging.handlers.RotatingFileHandler(
            self.logs_dir / 'errors.log',
            maxBytes=self.config['max_log_size'],
            backupCount=self.config['backup_count']
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Audit handler with rotation
        audit_handler = logging.handlers.RotatingFileHandler(
            self.logs_dir / 'audit.log',
            maxBytes=self.config['max_log_size'],
            backupCount=self.config['backup_count']
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(detailed_formatter)
        
        # Security handler with rotation
        security_handler = logging.handlers.RotatingFileHandler(
            self.logs_dir / 'security.log',
            maxBytes=self.config['max_log_size'],
            backupCount=self.config['backup_count']
        )
        security_handler.setLevel(logging.INFO)
        security_handler.setFormatter(detailed_formatter)
        
        # Performance handler with rotation
        performance_handler = logging.handlers.RotatingFileHandler(
            self.logs_dir / 'performance.log',
            maxBytes=self.config['max_log_size'],
            backupCount=self.config['backup_count']
        )
        performance_handler.setLevel(logging.INFO)
        performance_handler.setFormatter(detailed_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(audit_handler)
        root_logger.addHandler(security_handler)
        root_logger.addHandler(performance_handler)
        
        # Add console handler for critical errors
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.CRITICAL)
        console_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(console_handler)
        
        # Store handlers for structured logging
        self.handlers = {
            'error': error_handler,
            'audit': audit_handler,
            'security': security_handler,
            'performance': performance_handler,
            'console': console_handler
        }
    
    def _redact_sensitive_data(self, logger, method_name, event_dict):
        """Redact sensitive data from logs"""
        sensitive_fields = self.config.get('sensitive_fields', [])
        
        def redact_dict(obj):
            """Recursively redact sensitive data from dictionaries"""
            if isinstance(obj, dict):
                return {k: redact_dict(v) if k.lower() not in sensitive_fields else '***REDACTED***'
                       for k, v in obj.items()}
            elif isinstance(obj, list):
                return [redact_dict(item) for item in obj]
            else:
                return obj
        
        event_dict['event'] = redact_dict(event_dict.get('event', {}))
        return event_dict
    
    def _generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        self.trace_counter += 1
        timestamp = int(time.time() * 1000)
        return f"{timestamp}-{self.trace_counter}"
    
    def set_user_context(self, user_id: str, session_id: Optional[str] = None,
                        ip_address: Optional[str] = None):
        """Set user context for logging"""
        self._user_context = {
            'user_id': user_id,
            'session_id': session_id,
            'ip_address': ip_address
        }
    
    def clear_user_context(self):
        """Clear user context"""
        self._user_context = {}
    
    def log_trade_execution(self, trade_data: TradeExecutionLog):
        """Log trade execution events"""
        trace_id = self._generate_trace_id()
        
        # Create structured log entry
        log_entry = {
            'trace_id': trace_id,
            'event_type': 'TRADE_EXECUTION',
            'timestamp': trade_data.timestamp,
            'trade_id': trade_data.trade_id,
            'symbol': trade_data.symbol,
            'side': trade_data.side,
            'quantity': trade_data.quantity,
            'price': trade_data.price,
            'order_type': trade_data.order_type,
            'user_id': trade_data.user_id,
            'status': trade_data.status,
            'execution_time_ms': trade_data.execution_time_ms,
            'exchange': trade_data.exchange,
            'error_message': trade_data.error_message,
            'details': trade_data.details or {}
        }
        
        # Log to structured logger
        logger = structlog.get_logger('trade')
        logger.info(
            "Trade execution",
            **log_entry,
            user_context=self._user_context
        )
        
        # Append to trade logs file
        self._append_to_file(self.trade_logs_file, log_entry)
        
        # Log critical errors to dedicated error logger
        if trade_data.status.upper() in ['FAILED', 'ERROR']:
            error_logger = structlog.get_logger('trade.error')
            error_logger.error(
                "Trade execution failed",
                **log_entry
            )
    
    def log_security_event(self, event_data: SecurityEventLog):
        """Log security events"""
        trace_id = self._generate_trace_id()
        
        # Create structured log entry
        log_entry = {
            'trace_id': trace_id,
            'event_type': 'SECURITY_EVENT',
            'timestamp': event_data.timestamp,
            'security_event_type': event_data.event_type,
            'severity': event_data.severity.value,
            'user_id': event_data.user_id,
            'ip_address': event_data.ip_address,
            'session_id': event_data.session_id,
            'description': event_data.description,
            'details': event_data.details,
            'resolved': event_data.resolved
        }
        
        # Log to security logger
        logger = structlog.get_logger('security')
        logger.info(
            "Security event",
            **log_entry,
            user_context=self._user_context
        )
        
        # Append to security logs file
        self._append_to_file(self.security_logs_file, log_entry)
        
        # Log critical security events immediately
        if event_data.severity in [LogLevel.CRITICAL, LogLevel.ERROR]:
            security_logger = structlog.get_logger('security.critical')
            security_logger.critical(
                "Critical security event detected",
                **log_entry
            )
    
    def log_user_action(self, action: str, resource: Optional[str] = None,
                       details: Optional[Dict[str, Any]] = None,
                       severity: LogLevel = LogLevel.INFO):
        """Log user actions for audit trail"""
        trace_id = self._generate_trace_id()
        
        # Create audit entry
        audit_entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=EventType.USER_ACTION,
            user_id=self._user_context.get('user_id'),
            session_id=self._user_context.get('session_id'),
            ip_address=self._user_context.get('ip_address'),
            action=action,
            resource=resource,
            details=details or {},
            severity=severity,
            trace_id=trace_id
        )
        
        # Log to audit logger
        logger = structlog.get_logger('audit')
        logger.info(
            "User action",
            **audit_entry.to_dict()
        )
        
        # Append to audit trail file
        self._append_to_file(self.audit_trail_file, audit_entry.to_dict())
    
    def log_system_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                        severity: LogLevel = LogLevel.ERROR):
        """Log system errors with full traceback"""
        trace_id = self._generate_trace_id()
        
        # Get traceback information
        tb_info = traceback.format_exc() if self.config.get('capture_exceptions') else None
        
        log_entry = {
            'trace_id': trace_id,
            'event_type': 'SYSTEM_ERROR',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': tb_info,
            'context': context or {},
            'severity': severity.value,
            'user_context': self._user_context
        }
        
        # Log to error logger
        logger = structlog.get_logger('system.error')
        logger.error(
            "System error occurred",
            **log_entry
        )
        
        # Append to error log file if needed
        error_logger = logging.getLogger('system.error.file')
        error_logger.error(f"System Error: {error}\nContext: {context}\nTraceback: {tb_info}")
    
    def log_performance_metric(self, metric_name: str, value: Union[float, int],
                              unit: Optional[str] = None, tags: Optional[Dict[str, Any]] = None):
        """Log performance metrics"""
        trace_id = self._generate_trace_id()
        
        log_entry = {
            'trace_id': trace_id,
            'event_type': 'PERFORMANCE_METRIC',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'tags': tags or {},
            'user_context': self._user_context
        }
        
        # Log to performance logger
        logger = structlog.get_logger('performance')
        logger.info(
            "Performance metric",
            **log_entry
        )
        
        # Append to performance log file
        self._append_to_file(self.performance_logs_file, log_entry)
    
    def log_configuration_change(self, config_key: str, old_value: Any, new_value: Any,
                                changed_by: str):
        """Log configuration changes"""
        trace_id = self._generate_trace_id()
        
        audit_entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=EventType.CONFIGURATION_CHANGE,
            user_id=changed_by,
            session_id=self._user_context.get('session_id'),
            ip_address=self._user_context.get('ip_address'),
            action=f"Configuration change: {config_key}",
            resource=f"config:{config_key}",
            details={
                'old_value': old_value,
                'new_value': new_value
            },
            severity=LogLevel.INFO,
            trace_id=trace_id
        )
        
        # Log to audit logger
        logger = structlog.get_logger('audit')
        logger.info(
            "Configuration change",
            **audit_entry.to_dict()
        )
        
        # Append to audit trail file
        self._append_to_file(self.audit_trail_file, audit_entry.to_dict())
    
    def log_data_access(self, data_type: str, operation: str, resource_id: str,
                       details: Optional[Dict[str, Any]] = None):
        """Log data access events"""
        trace_id = self._generate_trace_id()
        
        audit_entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=EventType.DATA_ACCESS,
            user_id=self._user_context.get('user_id'),
            session_id=self._user_context.get('session_id'),
            ip_address=self._user_context.get('ip_address'),
            action=f"{operation} {data_type}",
            resource=f"{data_type}:{resource_id}",
            details=details or {},
            severity=LogLevel.INFO,
            trace_id=trace_id
        )
        
        # Log to audit logger
        logger = structlog.get_logger('audit')
        logger.info(
            "Data access",
            **audit_entry.to_dict()
        )
        
        # Append to audit trail file
        self._append_to_file(self.audit_trail_file, audit_entry.to_dict())
    
    def log_authentication_event(self, event_type: str, user_id: str,
                                success: bool, ip_address: str,
                                details: Optional[Dict[str, Any]] = None):
        """Log authentication events"""
        trace_id = self._generate_trace_id()
        
        severity = LogLevel.INFO if success else LogLevel.WARNING
        
        audit_entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=EventType.AUTHENTICATION,
            user_id=user_id,
            session_id=None,  # Not available during auth events
            ip_address=ip_address,
            action=f"Authentication {event_type}",
            resource=None,
            details={
                'success': success,
                'event_type': event_type,
                **(details or {})
            },
            severity=severity,
            trace_id=trace_id
        )
        
        # Log to audit logger
        logger = structlog.get_logger('audit')
        logger.info(
            "Authentication event",
            **audit_entry.to_dict()
        )
        
        # Append to audit trail file
        self._append_to_file(self.audit_trail_file, audit_entry.to_dict())
        
        # Log security event for failed authentication
        if not success:
            self.log_security_event(SecurityEventLog(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type='AUTHENTICATION_FAILURE',
                severity=LogLevel.WARNING,
                user_id=user_id,
                ip_address=ip_address,
                session_id=None,
                description=f"Authentication {event_type} failed",
                details=details or {}
            ))
    
    def log_system_startup(self, version: str, components: List[str]):
        """Log system startup events"""
        audit_entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=EventType.SYSTEM_STARTUP,
            user_id=None,
            session_id=None,
            ip_address=None,
            action="System startup",
            resource=None,
            details={
                'version': version,
                'components': components
            },
            severity=LogLevel.INFO
        )
        
        # Log to audit logger
        logger = structlog.get_logger('audit')
        logger.info(
            "System startup",
            **audit_entry.to_dict()
        )
        
        # Append to audit trail file
        self._append_to_file(self.audit_trail_file, audit_entry.to_dict())
    
    def log_system_shutdown(self, reason: str = "Normal shutdown"):
        """Log system shutdown events"""
        audit_entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=EventType.SYSTEM_SHUTDOWN,
            user_id=None,
            session_id=None,
            ip_address=None,
            action="System shutdown",
            resource=None,
            details={'reason': reason},
            severity=LogLevel.INFO
        )
        
        # Log to audit logger
        logger = structlog.get_logger('audit')
        logger.info(
            "System shutdown",
            **audit_entry.to_dict()
        )
        
        # Append to audit trail file
        self._append_to_file(self.audit_trail_file, audit_entry.to_dict())
    
    def _append_to_file(self, file_path: Path, data: Dict[str, Any]):
        """Append JSON data to file"""
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        except Exception as e:
            # Fallback to error logger
            error_logger = structlog.get_logger('file.error')
            error_logger.error(
                "Failed to write to log file",
                file_path=str(file_path),
                error=str(e)
            )
    
    def get_audit_trail(self, start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       user_id: Optional[str] = None,
                       event_type: Optional[EventType] = None) -> List[Dict[str, Any]]:
        """Retrieve audit trail entries with optional filtering"""
        entries = []
        
        try:
            with open(self.audit_trail_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if start_time and entry['timestamp'] < start_time.isoformat():
                            continue
                        if end_time and entry['timestamp'] > end_time.isoformat():
                            continue
                        if user_id and entry.get('user_id') != user_id:
                            continue
                        if event_type and entry.get('event_type') != event_type.value:
                            continue
                        
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        return entries
    
    def get_security_events(self, start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           severity: Optional[LogLevel] = None) -> List[Dict[str, Any]]:
        """Retrieve security events with optional filtering"""
        events = []
        
        try:
            with open(self.security_logs_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        
                        # Apply filters
                        if start_time and event['timestamp'] < start_time.isoformat():
                            continue
                        if end_time and event['timestamp'] > end_time.isoformat():
                            continue
                        if severity and event.get('severity') != severity.value:
                            continue
                        
                        events.append(event)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        return events
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up log files older than specified days"""
        import time
        current_time = time.time()
        cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
        
        log_files = [
            self.audit_trail_file,
            self.trade_logs_file,
            self.security_logs_file,
            self.performance_logs_file,
            self.logs_dir / 'errors.log',
            self.logs_dir / 'audit.log',
            self.logs_dir / 'security.log',
            self.logs_dir / 'performance.log'
        ]
        
        for log_file in log_files:
            try:
                if log_file.exists() and log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
            except Exception as e:
                error_logger = structlog.get_logger('cleanup.error')
                error_logger.error(
                    "Failed to clean up log file",
                    file_path=str(log_file),
                    error=str(e)
                )


# Global instance
audit_logger = None


def get_audit_logger(config: Optional[Dict[str, Any]] = None) -> AuditLogger:
    """Get or create global audit logger instance"""
    global audit_logger
    if audit_logger is None:
        audit_logger = AuditLogger(config)
    return audit_logger


def log_trade_execution(trade_data: TradeExecutionLog):
    """Convenience function for trade execution logging"""
    logger = get_audit_logger()
    logger.log_trade_execution(trade_data)


def log_security_event(event_data: SecurityEventLog):
    """Convenience function for security event logging"""
    logger = get_audit_logger()
    logger.log_security_event(event_data)


def log_user_action(action: str, resource: Optional[str] = None,
                   details: Optional[Dict[str, Any]] = None):
    """Convenience function for user action logging"""
    logger = get_audit_logger()
    logger.log_user_action(action, resource, details)


def log_system_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Convenience function for system error logging"""
    logger = get_audit_logger()
    logger.log_system_error(error, context)


def log_performance_metric(metric_name: str, value: Union[float, int],
                          unit: Optional[str] = None, tags: Optional[Dict[str, Any]] = None):
    """Convenience function for performance metric logging"""
    logger = get_audit_logger()
    logger.log_performance_metric(metric_name, value, unit, tags)


def set_user_context(user_id: str, session_id: Optional[str] = None,
                    ip_address: Optional[str] = None):
    """Convenience function for setting user context"""
    logger = get_audit_logger()
    logger.set_user_context(user_id, session_id, ip_address)


def clear_user_context():
    """Convenience function for clearing user context"""
    logger = get_audit_logger()
    logger.clear_user_context()


if __name__ == "__main__":
    # Example usage and testing
    logger = get_audit_logger()
    
    # Test trade execution logging
    trade_data = TradeExecutionLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        trade_id="TRD-001",
        symbol="AAPL",
        side="BUY",
        quantity=100,
        price=150.50,
        order_type="MARKET",
        user_id="user123",
        status="SUCCESS",
        execution_time_ms=45.2,
        exchange="NASDAQ"
    )
    logger.log_trade_execution(trade_data)
    
    # Test security event logging
    security_event = SecurityEventLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type="FAILED_LOGIN_ATTEMPT",
        severity=LogLevel.WARNING,
        user_id="user123",
        ip_address="192.168.1.1",
        session_id=None,
        description="Multiple failed login attempts detected",
        details={"attempts": 3, "window_minutes": 5}
    )
    logger.log_security_event(security_event)
    
    # Test user action logging
    logger.log_user_action(
        action="Portfolio update",
        resource="portfolio:user123",
        details={"action_type": "REBALANCE", "changes": ["AAPL: +10", "GOOGL: -10"]}
    )
    
    # Test error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.log_system_error(e, {"component": "trading_engine", "user_id": "user123"})
    
    # Test performance logging
    logger.log_performance_metric(
        metric_name="order_processing_time",
        value=125.5,
        unit="milliseconds",
        tags={"exchange": "NASDAQ", "order_type": "market"}
    )
    
    print("Audit logging system test completed successfully!")
