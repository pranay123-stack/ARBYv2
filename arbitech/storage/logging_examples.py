"""
Comprehensive Examples for ARBitech Audit Logging System

This file demonstrates how to use the audit logging and structured logging
systems in real-world scenarios.
"""

import sys
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.logger import setup_logging, get_logger, LoggerUtils
from storage.audit_logger import (
    get_audit_logger,
    LogLevel,
    EventType,
    TradeExecutionLog,
    SecurityEventLog,
    AuditEntry,
    set_user_context,
    clear_user_context,
    log_trade_execution,
    log_security_event,
    log_user_action,
    log_system_error,
    log_performance_metric
)


def example_basic_usage():
    """Example of basic logging usage"""
    print("\n=== Basic Logging Example ===")
    
    # Setup logging
    factory = setup_logging('development')
    logger = factory.get_logger('example')
    
    # Basic logging
    logger.info("Application started", version="1.0.0", environment="development")
    logger.debug("Debug information", component="main", status="initialized")
    logger.warning("This is a warning", warning_code="W001", suggestion="Check configuration")
    logger.error("This is an error", error_code="E001", component="database")
    
    print("✓ Basic logging completed")


def example_trade_execution_logging():
    """Example of trade execution logging"""
    print("\n=== Trade Execution Logging Example ===")
    
    # Setup audit logging
    audit_logger = get_audit_logger()
    
    # Simulate trade execution
    trade_data = TradeExecutionLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        trade_id=f"TRD-{uuid.uuid4().hex[:8].upper()}",
        symbol="AAPL",
        side="BUY",
        quantity=100,
        price=150.25,
        order_type="LIMIT",
        user_id="trader123",
        status="SUCCESS",
        execution_time_ms=45.7,
        exchange="NASDAQ",
        details={
            "strategy": "momentum",
            "risk_score": 0.25,
            "market_impact": 0.02
        }
    )
    
    audit_logger.log_trade_execution(trade_data)
    
    # Log a failed trade
    failed_trade = TradeExecutionLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        trade_id=f"TRD-{uuid.uuid4().hex[:8].upper()}",
        symbol="GOOGL",
        side="SELL",
        quantity=50,
        price=2800.00,
        order_type="LIMIT",
        user_id="trader123",
        status="FAILED",
        execution_time_ms=None,
        exchange="NASDAQ",
        error_message="Insufficient balance",
        details={"available_balance": 5000.00, "required_balance": 7000.00}
    )
    
    audit_logger.log_trade_execution(failed_trade)
    
    print("✓ Trade execution logging completed")


def example_security_event_logging():
    """Example of security event logging"""
    print("\n=== Security Event Logging Example ===")
    
    audit_logger = get_audit_logger()
    
    # Failed login attempt
    log_security_event(SecurityEventLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type="FAILED_LOGIN_ATTEMPT",
        severity=LogLevel.WARNING,
        user_id="user456",
        ip_address="192.168.1.100",
        session_id=None,
        description="Multiple failed login attempts",
        details={
            "attempts": 3,
            "window_minutes": 5,
            "last_attempt_timestamp": datetime.now(timezone.utc).isoformat()
        }
    ))
    
    # Suspicious activity
    log_security_event(SecurityEventLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type="SUSPICIOUS_ACTIVITY",
        severity=LogLevel.ERROR,
        user_id="user789",
        ip_address="10.0.0.50",
        session_id=str(uuid.uuid4()),
        description="Large withdrawal request from unusual location",
        details={
            "withdrawal_amount": 100000.0,
            "currency": "USD",
            "location": "Unknown",
            "device_fingerprint": "fp_abc123"
        }
    ))
    
    # System intrusion attempt
    log_security_event(SecurityEventLog(
        timestamp=datetime.now(timezone.utc).isoformat(),
        event_type="INTRUSION_ATTEMPT",
        severity=LogLevel.CRITICAL,
        user_id=None,
        ip_address="203.0.113.42",
        session_id=None,
        description="Multiple failed admin login attempts detected",
        details={
            "attempts": 10,
            "target_account": "admin",
            "geolocation": "High-risk country"
        }
    ))
    
    print("✓ Security event logging completed")


def example_user_action_logging():
    """Example of user action logging"""
    print("\n=== User Action Logging Example ===")
    
    # Set user context
    set_user_context(
        user_id="user123",
        session_id=str(uuid.uuid4()),
        ip_address="192.168.1.50"
    )
    
    audit_logger = get_audit_logger()
    
    # Log various user actions
    audit_logger.log_user_action(
        action="Portfolio view",
        resource="portfolio:user123",
        details={"view_type": "summary", "filters": ["stocks", "bonds"]}
    )
    
    audit_logger.log_user_action(
        action="Trade order placed",
        resource="order:ORD-001",
        details={
            "symbol": "MSFT",
            "side": "BUY",
            "quantity": 200,
            "order_type": "MARKET"
        }
    )
    
    audit_logger.log_user_action(
        action="Settings updated",
        resource="settings:user123",
        details={
            "changed_fields": ["notification_preferences", "risk_tolerance"],
            "old_values": {"risk_tolerance": "moderate"},
            "new_values": {"risk_tolerance": "conservative"}
        },
        severity=LogLevel.WARNING
    )
    
    # Clear context
    clear_user_context()
    
    print("✓ User action logging completed")


def example_system_error_logging():
    """Example of system error logging"""
    print("\n=== System Error Logging Example ===")
    
    audit_logger = get_audit_logger()
    
    try:
        # Simulate some operations
        result = 1 / 0  # This will raise an exception
    except ZeroDivisionError as e:
        audit_logger.log_system_error(
            e,
            context={
                "component": "calculation_engine",
                "operation": "division",
                "numerator": 1,
                "denominator": 0,
                "user_id": "system"
            }
        )
    
    # Log custom error
    try:
        raise ValueError("Invalid trade parameters")
    except ValueError as e:
        audit_logger.log_system_error(
            e,
            context={
                "component": "trading_engine",
                "operation": "validate_trade",
                "parameters": {
                    "symbol": "INVALID",
                    "quantity": -100,
                    "price": "not_a_number"
                }
            },
            severity=LogLevel.CRITICAL
        )
    
    print("✓ System error logging completed")


def example_performance_logging():
    """Example of performance logging"""
    print("\n=== Performance Logging Example ===")
    
    audit_logger = get_audit_logger()
    
    # Log various performance metrics
    audit_logger.log_performance_metric(
        metric_name="order_processing_time",
        value=125.5,
        unit="milliseconds",
        tags={
            "exchange": "NASDAQ",
            "order_type": "market",
            "symbol": "AAPL"
        }
    )
    
    audit_logger.log_performance_metric(
        metric_name="database_query_time",
        value=23.4,
        unit="milliseconds",
        tags={
            "query_type": "SELECT",
            "table": "trades",
            "result_count": 150
        }
    )
    
    audit_logger.log_performance_metric(
        metric_name="memory_usage",
        value=512.7,
        unit="MB",
        tags={
            "component": "trading_engine",
            "heap_type": "young_gen"
        }
    )
    
    audit_logger.log_performance_metric(
        metric_name="cpu_utilization",
        value=65.2,
        unit="percent",
        tags={
            "core": "all",
            "measurement_period": "1min"
        }
    )
    
    print("✓ Performance logging completed")


def example_configuration_logging():
    """Example of configuration change logging"""
    print("\n=== Configuration Logging Example ===")
    
    audit_logger = get_audit_logger()
    
    # Set user context for configuration changes
    set_user_context(
        user_id="admin123",
        session_id=str(uuid.uuid4()),
        ip_address="192.168.1.10"
    )
    
    # Log configuration changes
    audit_logger.log_configuration_change(
        config_key="trading.max_order_size",
        old_value=10000.0,
        new_value=50000.0,
        changed_by="admin123"
    )
    
    audit_logger.log_configuration_change(
        config_key="security.max_login_attempts",
        old_value=5,
        new_value=3,
        changed_by="security_admin"
    )
    
    audit_logger.log_configuration_change(
        config_key="logging.level",
        old_value="INFO",
        new_value="DEBUG",
        changed_by="devops"
    )
    
    clear_user_context()
    
    print("✓ Configuration logging completed")


def example_data_access_logging():
    """Example of data access logging"""
    print("\n=== Data Access Logging Example ===")
    
    audit_logger = get_audit_logger()
    
    set_user_context(
        user_id="user456",
        session_id=str(uuid.uuid4()),
        ip_address="192.168.1.75"
    )
    
    # Log data access events
    audit_logger.log_data_access(
        data_type="user_portfolio",
        operation="READ",
        resource_id="portfolio:user456",
        details={
            "access_type": "api",
            "fields_accessed": ["holdings", "performance", "risk_metrics"],
            "data_sensitivity": "high"
        }
    )
    
    audit_logger.log_data_access(
        data_type="trade_history",
        operation="EXPORT",
        resource_id="trades:user456",
        details={
            "export_format": "CSV",
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            },
            "record_count": 1250
        }
    )
    
    audit_logger.log_data_access(
        data_type="sensitive_user_data",
        operation="UPDATE",
        resource_id="profile:user456",
        details={
            "updated_fields": ["email", "phone"],
            "change_reason": "user_request"
        }
    )
    
    clear_user_context()
    
    print("✓ Data access logging completed")


def example_authentication_logging():
    """Example of authentication event logging"""
    print("\n=== Authentication Logging Example ===")
    
    audit_logger = get_audit_logger()
    
    # Log successful authentication
    audit_logger.log_authentication_event(
        event_type="LOGIN",
        user_id="user789",
        success=True,
        ip_address="192.168.1.90",
        details={
            "authentication_method": "password",
            "device_info": "Chrome on Windows",
            "session_duration": 3600
        }
    )
    
    # Log failed authentication
    audit_logger.log_authentication_event(
        event_type="LOGIN",
        user_id="user789",
        success=False,
        ip_address="192.168.1.90",
        details={
            "authentication_method": "password",
            "failure_reason": "invalid_credentials",
            "attempts": 2
        }
    )
    
    # Log logout
    audit_logger.log_authentication_event(
        event_type="LOGOUT",
        user_id="user789",
        success=True,
        ip_address="192.168.1.90",
        details={
            "session_duration": 7200,
            "logout_reason": "user_initiated"
        }
    )
    
    print("✓ Authentication logging completed")


def example_system_lifecycle_logging():
    """Example of system startup and shutdown logging"""
    print("\n=== System Lifecycle Logging Example ===")
    
    audit_logger = get_audit_logger()
    
    # Log system startup
    audit_logger.log_system_startup(
        version="2.1.0",
        components=[
            "trading_engine",
            "risk_manager",
            "order_router",
            "market_data_feed",
            "database_connector"
        ]
    )
    
    print("System startup logged. Simulating operation...")
    time.sleep(1)
    
    # Log system shutdown
    audit_logger.log_system_shutdown(
        reason="Scheduled maintenance"
    )
    
    print("✓ System lifecycle logging completed")


def example_correlation_logging():
    """Example of correlation ID logging for request tracing"""
    print("\n=== Correlation Logging Example ===")
    
    factory = setup_logging('development')
    logger = factory.get_logger('correlation')
    
    # Setup correlation logger
    corr_logger = LoggerUtils.setup_correlation_logging(logger)
    
    # Simulate request flow
    corr_logger.info("Request received", endpoint="/api/trades", method="POST")
    
    corr_logger.debug("Validating request", validation_steps=["auth", "params", "permissions"])
    corr_logger.info("Request validated", status="success")
    
    corr_logger.debug("Processing trade", trade_details={"symbol": "AAPL", "quantity": 100})
    corr_logger.info("Trade processed", status="success", trade_id="TRD-12345")
    
    corr_logger.info("Request completed", duration_ms=125.7)
    
    print("✓ Correlation logging completed")


def example_sensitive_data_redaction():
    """Example of sensitive data redaction in logs"""
    print("\n=== Sensitive Data Redaction Example ===")
    
    factory = setup_logging('development')
    logger = factory.get_logger('security')
    
    # These sensitive values should be redacted in logs
    sensitive_data = {
        "username": "john_doe",
        "password": "super_secret_password",  # Should be redacted
        "api_key": "ak_live_1234567890abcdef",  # Should be redacted
        "credit_card": "4532123456789012",  # Should be redacted
        "email": "john@example.com",
        "amount": 10000.50,
        "metadata": {
            "secret_key": "secret_xyz123",  # Should be redacted
            "public_info": "This is public"
        }
    }
    
    logger.info("User data processed", user_data=sensitive_data)
    
    print("✓ Sensitive data redaction example completed")


def example_audit_trail_retrieval():
    """Example of retrieving audit trail entries"""
    print("\n=== Audit Trail Retrieval Example ===")
    
    audit_logger = get_audit_logger()
    
    # Log some entries first
    audit_logger.log_user_action("Test action 1", details={"test": "data1"})
    audit_logger.log_user_action("Test action 2", details={"test": "data2"})
    audit_logger.log_user_action("Test action 3", details={"test": "data3"})
    
    # Retrieve audit trail
    from datetime import datetime, timedelta
    
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=10)
    
    audit_entries = audit_logger.get_audit_trail(
        start_time=start_time,
        end_time=end_time,
        event_type=EventType.USER_ACTION
    )
    
    print(f"Retrieved {len(audit_entries)} audit entries:")
    for entry in audit_entries:
        print(f"  - {entry['timestamp']}: {entry['action']}")
    
    print("✓ Audit trail retrieval completed")


def run_all_examples():
    """Run all logging examples"""
    print("Starting ARBitech Logging System Examples")
    print("=" * 50)
    
    try:
        example_basic_usage()
        example_trade_execution_logging()
        example_security_event_logging()
        example_user_action_logging()
        example_system_error_logging()
        example_performance_logging()
        example_configuration_logging()
        example_data_access_logging()
        example_authentication_logging()
        example_system_lifecycle_logging()
        example_correlation_logging()
        example_sensitive_data_redaction()
        example_audit_trail_retrieval()
        
        print("\n" + "=" * 50)
        print("✓ All logging examples completed successfully!")
        print("\nLog files have been created in /workspace/arbitech/logs/")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        raise


if __name__ == "__main__":
    run_all_examples()
