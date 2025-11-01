"""
Logging Configuration and Utilities for ARBitech Trading Platform

This module provides centralized logging configuration, setup utilities,
and helper functions for consistent logging across the application.
"""

import os
import sys
import logging
import structlog
from typing import Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
from enum import Enum


class LoggerConfig:
    """Logging configuration class"""
    
    def __init__(self,
                 logs_dir: Optional[str] = None,
                 environment: str = "development",
                 log_level: str = "INFO",
                 enable_json_logs: bool = True,
                 enable_console_output: bool = True,
                 enable_file_output: bool = True,
                 max_log_size_mb: int = 100,
                 backup_count: int = 10,
                 enable_log_rotation: bool = True,
                 sensitive_data_redaction: bool = True,
                 capture_exceptions: bool = True,
                 performance_logging: bool = True):
        """
        Initialize logging configuration
        
        Args:
            logs_dir: Directory for log files
            environment: Application environment (development, testing, production)
            log_level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_json_logs: Use JSON format for structured logs
            enable_console_output: Output logs to console
            enable_file_output: Output logs to files
            max_log_size_mb: Maximum log file size in MB
            backup_count: Number of backup files to keep
            enable_log_rotation: Enable log file rotation
            sensitive_data_redaction: Redact sensitive data from logs
            capture_exceptions: Capture and log exceptions
            performance_logging: Enable performance metric logging
        """
        self.logs_dir = logs_dir or os.getenv('LOG_DIR', '/workspace/arbitech/logs')
        self.environment = environment
        self.log_level = log_level
        self.enable_json_logs = enable_json_logs
        self.enable_console_output = enable_console_output
        self.enable_file_output = enable_file_output
        self.max_log_size_mb = max_log_size_mb
        self.backup_count = backup_count
        self.enable_log_rotation = enable_log_rotation
        self.sensitive_data_redaction = sensitive_data_redaction
        self.capture_exceptions = capture_exceptions
        self.performance_logging = performance_logging
        
        # Create logs directory if it doesn't exist
        Path(self.logs_dir).mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'logs_dir': self.logs_dir,
            'environment': self.environment,
            'log_level': self.log_level,
            'enable_json_logs': self.enable_json_logs,
            'enable_console_output': self.enable_console_output,
            'enable_file_output': self.enable_file_output,
            'max_log_size_mb': self.max_log_size_mb,
            'backup_count': self.backup_count,
            'enable_log_rotation': self.enable_log_rotation,
            'sensitive_data_redaction': self.sensitive_data_redaction,
            'capture_exceptions': self.capture_exceptions,
            'performance_logging': self.performance_logging
        }


class LoggerSetup:
    """Centralized logging setup and configuration"""
    
    def __init__(self, config: Optional[LoggerConfig] = None):
        """Initialize logger setup"""
        self.config = config or LoggerConfig()
        self._configured = False
    
    def setup(self) -> None:
        """Setup logging system"""
        if self._configured:
            return
        
        # Configure processors
        processors = self._get_processors()
        
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
        
        self._configured = True
    
    def _get_processors(self):
        """Get list of processors for structlog"""
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info if self.config.capture_exceptions else structlog.processors.UnicodeDecoder(),
            structlog.processors.UnicodeDecoder(),
        ]
        
        # Add sensitive data redaction
        if self.config.sensitive_data_redaction:
            processors.append(self._redact_sensitive_data)
        
        # Add appropriate renderer
        if self.config.enable_json_logs and self.config.environment != 'development':
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
        
        return processors
    
    def _redact_sensitive_data(self, logger, method_name, event_dict):
        """Redact sensitive data from logs"""
        sensitive_patterns = [
            'password', 'passwd', 'pwd',
            'token', 'auth_token', 'access_token', 'refresh_token',
            'secret', 'api_key', 'apikey', 'key',
            'credit_card', 'cc_number', 'ssn',
            'private_key', 'secret_key'
        ]
        
        def redact_dict(obj):
            """Recursively redact sensitive data"""
            if isinstance(obj, dict):
                redacted = {}
                for key, value in obj.items():
                    key_lower = key.lower()
                    if any(pattern in key_lower for pattern in sensitive_patterns):
                        redacted[key] = '***REDACTED***'
                    else:
                        redacted[key] = redact_dict(value)
                return redacted
            elif isinstance(obj, list):
                return [redact_dict(item) for item in obj]
            else:
                return obj
        
        if 'event' in event_dict:
            event_dict['event'] = redact_dict(event_dict['event'])
        
        return event_dict
    
    def _setup_stdlib_logging(self):
        """Setup standard library logging with appropriate handlers"""
        import logging
        import logging.handlers
        
        # Get or create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if self.config.enable_console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.config.log_level.upper()))
            
            if self.config.environment == 'development' and not self.config.enable_json_logs:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            else:
                formatter = logging.Formatter('%(message)s')
            
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File handlers with rotation
        if self.config.enable_file_output:
            self._setup_file_handlers(root_logger)
    
    def _setup_file_handlers(self, root_logger):
        """Setup file handlers with rotation"""
        import logging.handlers
        
        logs_dir = Path(self.config.logs_dir)
        
        # Main application log
        app_handler = self._create_rotating_handler(
            logs_dir / 'app.log',
            logging.INFO
        )
        root_logger.addHandler(app_handler)
        
        # Error log
        error_handler = self._create_rotating_handler(
            logs_dir / 'errors.log',
            logging.ERROR
        )
        root_logger.addHandler(error_handler)
        
        # Debug log (only in development)
        if self.config.environment == 'development':
            debug_handler = self._create_rotating_handler(
                logs_dir / 'debug.log',
                logging.DEBUG
            )
            root_logger.addHandler(debug_handler)
        
        # Security log
        security_handler = self._create_rotating_handler(
            logs_dir / 'security.log',
            logging.INFO
        )
        root_logger.addHandler(security_handler)
        
        # Performance log
        if self.config.performance_logging:
            performance_handler = self._create_rotating_handler(
                logs_dir / 'performance.log',
                logging.INFO
            )
            root_logger.addHandler(performance_handler)
    
    def _create_rotating_handler(self, log_file, level):
        """Create a rotating file handler"""
        import logging.handlers
        
        max_bytes = self.config.max_log_size_mb * 1024 * 1024
        
        if self.config.enable_log_rotation:
            handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
        else:
            handler = logging.FileHandler(log_file, encoding='utf-8')
        
        handler.setLevel(level)
        
        if self.config.enable_json_logs:
            formatter = logging.Formatter('%(message)s')
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        handler.setFormatter(formatter)
        return handler


class LoggerFactory:
    """Factory for creating configured loggers"""
    
    def __init__(self, config: Optional[LoggerConfig] = None):
        """Initialize factory with configuration"""
        self.config = config or LoggerConfig()
        self._setup = LoggerSetup(self.config)
        self._setup.setup()
    
    def get_logger(self, name: str) -> structlog.BoundLogger:
        """Get a structured logger instance"""
        return structlog.get_logger(name)
    
    def get_stdlib_logger(self, name: str) -> logging.Logger:
        """Get a standard library logger instance"""
        import logging
        return logging.getLogger(name)


class EnvironmentConfig:
    """Environment-specific logging configurations"""
    
    @staticmethod
    def get_development_config() -> LoggerConfig:
        """Get development environment configuration"""
        return LoggerConfig(
            environment="development",
            log_level="DEBUG",
            enable_json_logs=False,
            enable_console_output=True,
            sensitive_data_redaction=True,
            performance_logging=True
        )
    
    @staticmethod
    def get_testing_config() -> LoggerConfig:
        """Get testing environment configuration"""
        return LoggerConfig(
            environment="testing",
            log_level="WARNING",
            enable_json_logs=True,
            enable_console_output=False,
            sensitive_data_redaction=True,
            performance_logging=False
        )
    
    @staticmethod
    def get_production_config() -> LoggerConfig:
        """Get production environment configuration"""
        return LoggerConfig(
            environment="production",
            log_level="INFO",
            enable_json_logs=True,
            enable_console_output=False,
            enable_file_output=True,
            sensitive_data_redaction=True,
            capture_exceptions=True,
            performance_logging=True,
            max_log_size_mb=500,
            backup_count=20
        )
    
    @staticmethod
    def get_config_for_environment(env: str) -> LoggerConfig:
        """Get configuration for specified environment"""
        env = env.lower()
        if env in ['dev', 'development']:
            return EnvironmentConfig.get_development_config()
        elif env in ['test', 'testing']:
            return EnvironmentConfig.get_testing_config()
        elif env in ['prod', 'production']:
            return EnvironmentConfig.get_production_config()
        else:
            # Default to development
            return EnvironmentConfig.get_development_config()


class LoggerUtils:
    """Utility functions for logging"""
    
    @staticmethod
    def setup_logging_from_env() -> LoggerFactory:
        """Setup logging based on environment variables"""
        env = os.getenv('ENVIRONMENT', 'development')
        config = EnvironmentConfig.get_config_for_environment(env)
        
        # Override with environment variables if present
        if os.getenv('LOG_LEVEL'):
            config.log_level = os.getenv('LOG_LEVEL').upper()
        if os.getenv('LOG_DIR'):
            config.logs_dir = os.getenv('LOG_DIR')
        if os.getenv('ENABLE_JSON_LOGS'):
            config.enable_json_logs = os.getenv('ENABLE_JSON_LOGS').lower() == 'true'
        
        return LoggerFactory(config)
    
    @staticmethod
    def log_function_entry_exit(logger, func_name: str, **kwargs):
        """Log function entry and exit for debugging"""
        logger.debug(f"Entering {func_name}", function=func_name, parameters=kwargs)
        
        def decorator(func):
            def wrapper(*args, **kw):
                try:
                    start_time = datetime.now()
                    result = func(*args, **kw)
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    logger.debug(
                        f"Exiting {func_name}",
                        function=func_name,
                        duration_seconds=duration,
                        status="success"
                    )
                    return result
                except Exception as e:
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    logger.error(
                        f"Error in {func_name}",
                        function=func_name,
                        duration_seconds=duration,
                        error=str(e),
                        exc_info=True,
                        status="error"
                    )
                    raise
            return wrapper
        return decorator
    
    @staticmethod
    def measure_performance(func):
        """Decorator to measure function performance"""
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            
            # Log performance metric
            try:
                from ..storage.audit_logger import log_performance_metric
                log_performance_metric(
                    metric_name=f"{func.__name__}_execution_time",
                    value=duration,
                    unit="seconds"
                )
            except ImportError:
                pass
            
            return result
        return wrapper
    
    @staticmethod
    def log_with_context(logger, message: str, **context):
        """Log message with additional context"""
        logger.info(message, **context)
    
    @staticmethod
    def setup_correlation_logging(logger):
        """Setup correlation ID for request tracing"""
        import uuid
        
        class CorrelationLogger:
            def __init__(self, base_logger):
                self.base_logger = base_logger
                self.correlation_id = str(uuid.uuid4())
            
            def _log(self, level, message, **kwargs):
                kwargs['correlation_id'] = self.correlation_id
                getattr(self.base_logger, level)(message, **kwargs)
            
            def debug(self, message, **kwargs):
                self._log('debug', message, **kwargs)
            
            def info(self, message, **kwargs):
                self._log('info', message, **kwargs)
            
            def warning(self, message, **kwargs):
                self._log('warning', message, **kwargs)
            
            def error(self, message, **kwargs):
                self._log('error', message, **kwargs)
            
            def critical(self, message, **kwargs):
                self._log('critical', message, **kwargs)
        
        return CorrelationLogger(logger)


# Global logger factory instance
_global_logger_factory = None


def get_logger_factory(config: Optional[LoggerConfig] = None) -> LoggerFactory:
    """Get or create global logger factory"""
    global _global_logger_factory
    if _global_logger_factory is None:
        _global_logger_factory = LoggerFactory(config)
    return _global_logger_factory


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    factory = get_logger_factory()
    return factory.get_logger(name)


def setup_logging(environment: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None) -> LoggerFactory:
    """
    Setup logging system with optional environment or custom configuration
    
    Args:
        environment: Environment name (development, testing, production)
        config: Custom configuration dictionary
    
    Returns:
        LoggerFactory instance
    """
    if config:
        # Create config from dictionary
        logger_config = LoggerConfig(**config)
    elif environment:
        # Create config from environment
        logger_config = EnvironmentConfig.get_config_for_environment(environment)
    else:
        # Use environment variables or defaults
        logger_config = EnvironmentConfig.get_config_for_environment(
            os.getenv('ENVIRONMENT', 'development')
        )
    
    factory = LoggerFactory(logger_config)
    
    # Update global factory
    global _global_logger_factory
    _global_logger_factory = factory
    
    return factory


# Convenience functions
def debug(message: str, **kwargs):
    """Log debug message"""
    logger = get_logger('application')
    logger.debug(message, **kwargs)


def info(message: str, **kwargs):
    """Log info message"""
    logger = get_logger('application')
    logger.info(message, **kwargs)


def warning(message: str, **kwargs):
    """Log warning message"""
    logger = get_logger('application')
    logger.warning(message, **kwargs)


def error(message: str, **kwargs):
    """Log error message"""
    logger = get_logger('application')
    logger.error(message, **kwargs)


def critical(message: str, **kwargs):
    """Log critical message"""
    logger = get_logger('application')
    logger.critical(message, **kwargs)


if __name__ == "__main__":
    # Example usage and testing
    print("Testing logging configuration...")
    
    # Setup development logging
    factory = setup_logging('development')
    logger = factory.get_logger('test')
    
    logger.info("Application started", version="1.0.0", environment="development")
    logger.debug("Debug message", test_data={"key": "value"})
    logger.warning("Warning message", warning_type="test")
    
    # Test performance logging
    @LoggerUtils.measure_performance
    def sample_function():
        import time
        time.sleep(0.1)
        return "Done"
    
    result = sample_function()
    print(f"Function result: {result}")
    
    print("Logging configuration test completed!")
