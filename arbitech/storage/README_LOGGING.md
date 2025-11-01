# ARBitech Logging and Audit System

A comprehensive, production-ready logging and audit system for the ARBitech Trading Platform. This system provides structured logging, audit trails, and monitoring capabilities for trade execution, security events, user actions, and system performance.

## Features

### Core Capabilities
- **Structured Logging**: JSON-based structured logs using `structlog`
- **Audit Trail**: Complete audit trail for sensitive operations
- **Trade Execution Logging**: Detailed logging of all trading activities
- **Security Event Monitoring**: Security event detection and logging
- **Performance Metrics**: System and application performance monitoring
- **User Action Tracking**: Complete user activity logging
- **Error Capture**: Comprehensive error logging with tracebacks
- **Log Rotation**: Automatic log rotation and management
- **Sensitive Data Redaction**: Automatic redaction of sensitive information
- **Correlation IDs**: Request tracing and correlation

### Log Types
1. **Trade Execution Logs** - All trading activities
2. **Security Event Logs** - Security-related events and alerts
3. **Audit Trail Logs** - User actions and system changes
4. **System Error Logs** - System errors and exceptions
5. **Performance Metrics** - Application and system performance
6. **Configuration Change Logs** - System configuration updates

## Quick Start

### 1. Basic Setup

```python
from utils.logger import setup_logging
from storage.audit_logger import get_audit_logger

# Setup logging for your environment
factory = setup_logging('development')  # or 'testing' or 'production'

# Get logger instance
logger = factory.get_logger('my_application')
logger.info("Application started", version="1.0.0")

# Get audit logger
audit_logger = get_audit_logger()
```

### 2. Basic Logging

```python
from utils.logger import get_logger

logger = get_logger('trading_engine')

# Log with context
logger.info("Trade order received", 
           order_id="ORD-12345",
           symbol="AAPL",
           quantity=100)

# Log with structured data
logger.warning("Risk threshold exceeded",
               user_id="user123",
               risk_score=0.85,
               threshold=0.80)
```

### 3. Trade Execution Logging

```python
from storage.audit_logger import TradeExecutionLog, LogLevel
from datetime import datetime, timezone

trade_data = TradeExecutionLog(
    timestamp=datetime.now(timezone.utc).isoformat(),
    trade_id="TRD-001",
    symbol="AAPL",
    side="BUY",
    quantity=100,
    price=150.50,
    order_type="MARKET",
    user_id="trader123",
    status="SUCCESS",
    execution_time_ms=45.2,
    exchange="NASDAQ",
    details={"strategy": "momentum"}
)

audit_logger.log_trade_execution(trade_data)
```

### 4. Security Event Logging

```python
from storage.audit_logger import SecurityEventLog, LogLevel

audit_logger.log_security_event(SecurityEventLog(
    timestamp=datetime.now(timezone.utc).isoformat(),
    event_type="FAILED_LOGIN_ATTEMPT",
    severity=LogLevel.WARNING,
    user_id="user456",
    ip_address="192.168.1.1",
    description="Multiple failed login attempts",
    details={"attempts": 3, "window_minutes": 5}
))
```

### 5. User Action Logging

```python
from storage.audit_logger import set_user_context, log_user_action

# Set user context
set_user_context(
    user_id="user123",
    session_id="sess_abc123",
    ip_address="192.168.1.50"
)

# Log user actions
log_user_action(
    action="Portfolio update",
    resource="portfolio:user123",
    details={"action_type": "REBALANCE"}
)
```

## Configuration

### Environment Configuration

#### Development
```python
from utils.logger import EnvironmentConfig

config = EnvironmentConfig.get_development_config()
# - Console output enabled
- Debug logging enabled
- Pretty-printed JSON
- Performance logging enabled
```

#### Production
```python
config = EnvironmentConfig.get_production_config()
# - File output only
- JSON format
- 500MB max file size
- 20 backup files
- Sensitive data redaction
```

### Custom Configuration

```python
from utils.logger import LoggerConfig

config = LoggerConfig(
    logs_dir="/var/log/arbitech",
    environment="production",
    log_level="INFO",
    enable_json_logs=True,
    enable_file_output=True,
    max_log_size_mb=100,
    backup_count=10,
    sensitive_data_redaction=True,
    capture_exceptions=True,
    performance_logging=True
)

factory = setup_logging(config=config.to_dict())
```

### Environment Variables

```bash
# Set environment
export ENVIRONMENT=production

# Override log level
export LOG_LEVEL=DEBUG

# Custom log directory
export LOG_DIR=/var/log/myapp

# Enable/disable JSON logs
export ENABLE_JSON_LOGS=true
```

## Log Files

The system creates the following log files:

```
/workspace/arbitech/logs/
├── app.log              # Main application logs
├── errors.log           # Error logs only
├── debug.log            # Debug logs (development only)
├── security.log         # Security events
├── performance.log      # Performance metrics
├── audit.log            # General audit logs
├── audit_trail.jsonl    # Structured audit trail
├── trade_execution.jsonl # Trade execution logs
├── security_events.jsonl # Security event logs
└── performance_metrics.jsonl # Performance metrics
```

## Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General informational messages
- **WARNING**: Warning messages for unusual conditions
- **ERROR**: Error messages for recoverable errors
- **CRITICAL**: Critical system errors
- **AUDIT**: Audit trail entries (informational)
- **SECURITY**: Security-related events
- **TRADE**: Trade execution events

## Event Types

### Audit Event Types
- `TRADE_EXECUTION`: Trade order and execution events
- `USER_ACTION`: User actions and operations
- `SYSTEM_ERROR`: System errors and exceptions
- `SECURITY_EVENT`: Security-related events
- `PERFORMANCE_METRIC`: Performance measurements
- `CONFIGURATION_CHANGE`: System configuration changes
- `DATA_ACCESS`: Data access events
- `AUTHENTICATION`: Authentication events
- `SYSTEM_STARTUP`: System startup events
- `SYSTEM_SHUTDOWN`: System shutdown events

## Security Features

### Sensitive Data Redaction

The system automatically redacts sensitive fields:

```python
# These fields will be redacted:
sensitive_patterns = [
    'password', 'passwd', 'pwd',
    'token', 'auth_token', 'access_token',
    'secret', 'api_key', 'key',
    'credit_card', 'cc_number',
    'private_key', 'secret_key'
]
```

### Security Event Monitoring

```python
# Failed authentication
audit_logger.log_authentication_event(
    event_type="LOGIN",
    user_id="user123",
    success=False,
    ip_address="192.168.1.1",
    details={"reason": "invalid_credentials"}
)

# Suspicious activity
audit_logger.log_security_event(SecurityEventLog(
    event_type="SUSPICIOUS_ACTIVITY",
    severity=LogLevel.ERROR,
    # ... other parameters
))
```

## Performance Monitoring

### Performance Metrics

```python
# Log performance metrics
audit_logger.log_performance_metric(
    metric_name="order_processing_time",
    value=125.5,
    unit="milliseconds",
    tags={
        "exchange": "NASDAQ",
        "order_type": "market"
    }
)
```

### Function Performance Decorator

```python
from utils.logger import LoggerUtils

@LoggerUtils.measure_performance
def my_function():
    # Your code here
    time.sleep(0.1)
    return "Done"

# Automatically logs execution time
result = my_function()
```

## Audit Trail Queries

### Retrieve Audit Trail

```python
from datetime import datetime, timedelta
from storage.audit_logger import EventType

audit_logger = get_audit_logger()

# Get entries from last hour
end_time = datetime.now()
start_time = end_time - timedelta(hours=1)

entries = audit_logger.get_audit_trail(
    start_time=start_time,
    end_time=end_time,
    user_id="user123",
    event_type=EventType.USER_ACTION
)
```

### Retrieve Security Events

```python
from storage.audit_logger import LogLevel

# Get critical security events
events = audit_logger.get_security_events(
    severity=LogLevel.CRITICAL,
    start_time=start_time,
    end_time=end_time
)
```

## Best Practices

### 1. Always Set User Context

```python
# Set context at request start
set_user_context(
    user_id=request.user.id,
    session_id=request.session.id,
    ip_address=request.client.ip
)

# Clear context at request end
clear_user_context()
```

### 2. Use Structured Logging

```python
# Good: Structured logging
logger.info("Trade executed", 
           trade_id="TRD-123",
           symbol="AAPL",
           quantity=100)

# Bad: String formatting
logger.info(f"Trade executed: TRD-123 for AAPL quantity 100")
```

### 3. Include Correlation IDs

```python
from utils.logger import LoggerUtils

corr_logger = LoggerUtils.setup_correlation_logging(logger)
corr_logger.info("Processing request", request_id="req123")
```

### 4. Log at Appropriate Levels

```python
# Use DEBUG for detailed debugging
logger.debug("Processing trade", trade_data=trade_data)

# Use INFO for general information
logger.info("Trade completed", trade_id="TRD-123")

# Use WARNING for unusual but not error conditions
logger.warning("High latency detected", latency_ms=500)

# Use ERROR for recoverable errors
logger.error("Failed to connect to database", error=str(e))

# Use CRITICAL for system-critical errors
logger.critical("System out of memory", memory_usage="95%")
```

### 5. Include Context in Errors

```python
try:
    result = risky_operation()
except Exception as e:
    logger.error("Operation failed",
                error=str(e),
                operation="risky_operation",
                user_id=user_id,
                retry_count=retry_count)
    raise
```

## Integration Examples

### Flask Integration

```python
from flask import Flask, request, g
from utils.logger import get_logger
from storage.audit_logger import set_user_context, clear_user_context

app = Flask(__name__)

@app.before_request
def setup_logging_context():
    set_user_context(
        user_id=g.user.id if g.user else None,
        session_id=request.headers.get('X-Session-ID'),
        ip_address=request.remote_addr
    )

@app.after_request
def cleanup_logging_context(response):
    clear_user_context()
    return response

@app.route('/api/trades', methods=['POST'])
def create_trade():
    logger = get_logger('api')
    logger.info("Trade creation request", 
               symbol=request.json['symbol'],
               quantity=request.json['quantity'])
```

### Django Integration

```python
import threading
from django.utils.deprecation import MiddlewareMixin
from storage.audit_logger import set_user_context, clear_user_context

thread_local = threading.local()

class LoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            thread_local.user_context = {
                'user_id': request.user.id,
                'session_id': request.session.session_key,
                'ip_address': self.get_client_ip(request)
            }
            set_user_context(**thread_local.user_context)
    
    def process_response(self, request, response):
        clear_user_context()
        return response
```

## Monitoring and Alerting

### Log Rotation Cleanup

```python
# Clean up logs older than 30 days
audit_logger.cleanup_old_logs(days_to_keep=30)
```

### Error Rate Monitoring

```python
# Monitor error rate
import time
error_count = 0
start_time = time.time()

# In your error logging code:
logger.error("Error occurred", error_code="E123")
error_count += 1

# Check error rate
if time.time() - start_time >= 60:  # Every minute
    if error_count > threshold:
        # Trigger alert
        logger.critical("High error rate detected", 
                       error_rate=error_count/60)
    error_count = 0
    start_time = time.time()
```

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure `structlog` is installed
   ```bash
   pip install structlog
   ```

2. **Log Files Not Created**: Check permissions on log directory
   ```bash
   chmod 755 /workspace/arbitech/logs
   ```

3. **JSON Parsing Errors**: Ensure log format matches expected structure

4. **Performance Impact**: Disable performance logging in high-throughput scenarios

### Debug Logging

```python
# Enable debug logging temporarily
factory = setup_logging('development')
logger = factory.get_logger('debug')
logger.debug("Debug information", key="value")
```

## Testing

### Unit Testing with Mock Logging

```python
import unittest.mock
from storage.audit_logger import log_trade_execution

# Mock the audit logger
with unittest.mock.patch('storage.audit_logger.get_audit_logger') as mock_logger:
    mock_instance = mock_logger.return_value
    mock_instance.log_trade_execution = unittest.mock.MagicMock()
    
    # Test your code
    your_trading_function()
    
    # Verify logging was called
    mock_instance.log_trade_execution.assert_called_once()
```

### Integration Testing

```python
import tempfile
import json
from pathlib import Path

def test_audit_logging():
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {'logs_directory': temp_dir}
        audit_logger = get_audit_logger(config)
        
        # Create test audit entry
        log_user_action("test_action", details={"test": "data"})
        
        # Verify log file was created and contains entry
        log_file = Path(temp_dir) / 'audit_trail.jsonl'
        assert log_file.exists()
        
        with open(log_file) as f:
            entries = [json.loads(line) for line in f]
            assert len(entries) > 0
            assert entries[-1]['action'] == 'test_action'
```

## Performance Considerations

- **Batch Operations**: Group multiple log entries when possible
- **Async Logging**: Consider async logging for high-throughput applications
- **Log Levels**: Use appropriate log levels to reduce noise
- **Rotation Settings**: Configure rotation based on disk space constraints
- **Retention Policy**: Implement proper log retention and cleanup

## Security Considerations

- **Sensitive Data**: Always enable sensitive data redaction
- **Access Control**: Restrict access to log files
- **Network Security**: Secure log transmission over networks
- **Audit Compliance**: Ensure logs meet regulatory requirements
- **Privacy**: Remove or anonymize personally identifiable information

## License

This logging system is part of the ARBitech Trading Platform.
