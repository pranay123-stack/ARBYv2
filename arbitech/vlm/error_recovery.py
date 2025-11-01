"""
Error Recovery - Error classification, recovery strategies, and circuit breakers for VLM operations
"""

import logging
import time
import json
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of VLM errors"""
    NETWORK = "network"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    RESOURCE = "resource"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    MODEL_ERROR = "model_error"
    DATA_CORRUPTION = "data_corruption"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


class ErrorType(Enum):
    """Specific error types"""
    CONNECTION_TIMEOUT = "connection_timeout"
    READ_TIMEOUT = "read_timeout"
    BAD_REQUEST = "bad_request"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    GATEWAY_TIMEOUT = "gateway_timeout"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    QUOTA_EXCEEDED = "quota_exceeded"
    MODEL_OVERLOADED = "model_overloaded"
    INVALID_RESPONSE = "invalid_response"
    PARSING_ERROR = "parsing_error"
    MEMORY_ERROR = "memory_error"
    DISK_FULL = "disk_full"


@dataclass
class VLMRecoveryConfig:
    """Configuration for error recovery"""
    enable_circuit_breaker: bool = True
    enable_retry_logic: bool = True
    enable_fallback: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: int = 60
    circuit_breaker_recovery_timeout: int = 30
    max_retry_attempts: int = 3
    retry_delay_base: float = 1.0
    retry_delay_multiplier: float = 2.0
    max_retry_delay: float = 60.0
    recovery_timeout: int = 300
    alert_threshold: int = 10
    auto_recovery_enabled: bool = True


class ErrorClassifier:
    """Classifies and categorizes VLM errors"""
    
    # Error type to category mapping
    ERROR_MAPPINGS = {
        ErrorType.CONNECTION_TIMEOUT: ErrorCategory.NETWORK,
        ErrorType.READ_TIMEOUT: ErrorCategory.TIMEOUT,
        ErrorType.GATEWAY_TIMEOUT: ErrorCategory.TIMEOUT,
        ErrorType.BAD_REQUEST: ErrorCategory.VALIDATION,
        ErrorType.UNAUTHORIZED: ErrorCategory.AUTHENTICATION,
        ErrorType.FORBIDDEN: ErrorCategory.AUTHENTICATION,
        ErrorType.NOT_FOUND: ErrorCategory.VALIDATION,
        ErrorType.INTERNAL_ERROR: ErrorCategory.SYSTEM,
        ErrorType.SERVICE_UNAVAILABLE: ErrorCategory.SYSTEM,
        ErrorType.RATE_LIMIT_EXCEEDED: ErrorCategory.RATE_LIMIT,
        ErrorType.QUOTA_EXCEEDED: ErrorCategory.RATE_LIMIT,
        ErrorType.MODEL_OVERLOADED: ErrorCategory.RESOURCE,
        ErrorType.INVALID_RESPONSE: ErrorCategory.MODEL_ERROR,
        ErrorType.PARSING_ERROR: ErrorCategory.MODEL_ERROR,
        ErrorType.MEMORY_ERROR: ErrorCategory.RESOURCE,
        ErrorType.DISK_FULL: ErrorCategory.RESOURCE,
    }
    
    # HTTP status codes to error types
    HTTP_STATUS_MAPPINGS = {
        400: ErrorType.BAD_REQUEST,
        401: ErrorType.UNAUTHORIZED,
        403: ErrorType.FORBIDDEN,
        404: ErrorType.NOT_FOUND,
        408: ErrorType.CONNECTION_TIMEOUT,
        429: ErrorType.RATE_LIMIT_EXCEEDED,
        500: ErrorType.INTERNAL_ERROR,
        502: ErrorType.GATEWAY_TIMEOUT,
        503: ErrorType.SERVICE_UNAVAILABLE,
        504: ErrorType.GATEWAY_TIMEOUT,
    }
    
    @classmethod
    def classify_error(cls, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Classify an error and determine recovery strategy"""
        if context is None:
            context = {}
        
        error_type = cls._determine_error_type(error, context)
        category = cls.ERROR_MAPPINGS.get(error_type, ErrorCategory.SYSTEM)
        severity = cls._determine_severity(error_type, category, context)
        
        return {
            "error_type": error_type,
            "category": category,
            "severity": severity,
            "message": str(error),
            "timestamp": time.time(),
            "context": context,
            "recoverable": cls._is_recoverable(error_type),
            "retry_count": context.get("retry_count", 0),
            "original_exception": error
        }
    
    @classmethod
    def _determine_error_type(cls, error: Exception, context: Dict[str, Any]) -> ErrorType:
        """Determine specific error type from exception"""
        error_message = str(error).lower()
        error_name = type(error).__name__.lower()
        
        # Check for timeout errors
        if any(keyword in error_message for keyword in ["timeout", "timed out"]):
            if "read" in error_message or "response" in error_message:
                return ErrorType.READ_TIMEOUT
            return ErrorType.CONNECTION_TIMEOUT
        
        # Check for rate limiting
        if any(keyword in error_message for keyword in ["rate limit", "quota", "too many requests"]):
            if "quota" in error_message:
                return ErrorType.QUOTA_EXCEEDED
            return ErrorType.RATE_LIMIT_EXCEEDED
        
        # Check for authentication errors
        if any(keyword in error_message for keyword in ["unauthorized", "auth", "token"]):
            return ErrorType.UNAUTHORIZED
        
        # Check for model errors
        if any(keyword in error_message for keyword in ["model", "parse", "invalid response"]):
            if "parse" in error_message:
                return ErrorType.PARSING_ERROR
            return ErrorType.INVALID_RESPONSE
        
        # Check for resource errors
        if any(keyword in error_message for keyword in ["memory", "disk", "resource"]):
            if "memory" in error_message:
                return ErrorType.MEMORY_ERROR
            if "disk" in error_message:
                return ErrorType.DISK_FULL
            return ErrorType.MODEL_OVERLOADED
        
        # Check HTTP status code if available
        if hasattr(error, 'status_code'):
            return cls.HTTP_STATUS_MAPPINGS.get(error.status_code, ErrorType.INTERNAL_ERROR)
        
        # Default to internal error
        return ErrorType.INTERNAL_ERROR
    
    @classmethod
    def _determine_severity(cls, error_type: ErrorType, category: ErrorCategory, context: Dict[str, Any]) -> ErrorSeverity:
        """Determine error severity"""
        # Critical errors
        if error_type in [ErrorType.DISK_FULL, ErrorType.MEMORY_ERROR, ErrorType.SERVICE_UNAVAILABLE]:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.DATA_CORRUPTION]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.RATE_LIMIT, ErrorCategory.RESOURCE]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors (most network and timeout issues)
        return ErrorSeverity.LOW
    
    @classmethod
    def _is_recoverable(cls, error_type: ErrorType) -> bool:
        """Determine if error is recoverable through retry"""
        non_recoverable = [
            ErrorType.BAD_REQUEST,
            ErrorType.UNAUTHORIZED,
            ErrorType.FORBIDDEN,
            ErrorType.NOT_FOUND,
            ErrorType.DISK_FULL
        ]
        
        return error_type not in non_recoverable


class RecoveryStrategy(ABC):
    """Abstract base class for recovery strategies"""
    
    @abstractmethod
    def can_recover(self, error_info: Dict[str, Any]) -> bool:
        """Check if this strategy can recover from the error"""
        pass
    
    @abstractmethod
    def recover(self, error_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to recover from the error"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this recovery strategy"""
        pass


class NetworkRetryStrategy(RecoveryStrategy):
    """Recovery strategy for network-related errors"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
    
    def can_recover(self, error_info: Dict[str, Any]) -> bool:
        """Check if this strategy can handle the error"""
        category = error_info.get("category")
        error_type = error_info.get("error_type")
        retry_count = error_info.get("retry_count", 0)
        
        return (
            category == ErrorCategory.NETWORK and
            error_type in [ErrorType.CONNECTION_TIMEOUT, ErrorType.GATEWAY_TIMEOUT] and
            retry_count < self.max_attempts
        )
    
    def recover(self, error_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt network recovery with exponential backoff"""
        retry_count = error_info.get("retry_count", 0)
        delay = self.base_delay * (2 ** retry_count)
        
        logger.info(f"Network retry strategy: attempt {retry_count + 1}, delay: {delay}s")
        
        return {
            "strategy": "network_retry",
            "action": "retry",
            "delay": delay,
            "retry_count": retry_count + 1,
            "estimated_recovery_time": delay
        }
    
    def get_strategy_name(self) -> str:
        return "network_retry"


class RateLimitBackoffStrategy(RecoveryStrategy):
    """Recovery strategy for rate limiting errors"""
    
    def __init__(self, max_attempts: int = 5, base_delay: float = 60.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
    
    def can_recover(self, error_info: Dict[str, Any]) -> bool:
        """Check if this strategy can handle the error"""
        category = error_info.get("category")
        error_type = error_info.get("error_type")
        retry_count = error_info.get("retry_count", 0)
        
        return (
            category == ErrorCategory.RATE_LIMIT and
            retry_count < self.max_attempts
        )
    
    def recover(self, error_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt rate limit recovery with exponential backoff"""
        retry_count = error_info.get("retry_count", 0)
        
        # Use longer delays for rate limiting
        delay = self.base_delay * (1.5 ** retry_count)
        
        logger.warning(f"Rate limit backoff strategy: attempt {retry_count + 1}, delay: {delay}s")
        
        return {
            "strategy": "rate_limit_backoff",
            "action": "backoff",
            "delay": delay,
            "retry_count": retry_count + 1,
            "estimated_recovery_time": delay,
            "message": f"Rate limit reached, backing off for {delay} seconds"
        }
    
    def get_strategy_name(self) -> str:
        return "rate_limit_backoff"


class ResourceScalingStrategy(RecoveryStrategy):
    """Recovery strategy for resource-related errors"""
    
    def __init__(self, scaling_factor: float = 0.8):
        self.scaling_factor = scaling_factor
    
    def can_recover(self, error_info: Dict[str, Any]) -> bool:
        """Check if this strategy can handle the error"""
        category = error_info.get("category")
        error_type = error_info.get("error_type")
        
        return (
            category == ErrorCategory.RESOURCE and
            error_type in [ErrorType.MEMORY_ERROR, ErrorType.MODEL_OVERLOADED]
        )
    
    def recover(self, error_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt resource scaling recovery"""
        # Scale down processing parameters
        scaled_context = context.copy()
        
        # Reduce batch size, image size, etc.
        if "batch_size" in scaled_context:
            scaled_context["batch_size"] = max(1, int(scaled_context["batch_size"] * self.scaling_factor))
        
        if "max_image_size" in scaled_context:
            scaled_context["max_image_size"] = max(512, int(scaled_context["max_image_size"] * self.scaling_factor))
        
        logger.info(f"Resource scaling strategy: scaling down processing parameters")
        
        return {
            "strategy": "resource_scaling",
            "action": "scale_down",
            "scaled_context": scaled_context,
            "estimated_recovery_time": 5.0
        }
    
    def get_strategy_name(self) -> str:
        return "resource_scaling"


class AuthenticationRefreshStrategy(RecoveryStrategy):
    """Recovery strategy for authentication errors"""
    
    def __init__(self, refresh_func: Callable):
        self.refresh_func = refresh_func
    
    def can_recover(self, error_info: Dict[str, Any]) -> bool:
        """Check if this strategy can handle the error"""
        category = error_info.get("category")
        error_type = error_info.get("error_type")
        
        return category == ErrorCategory.AUTHENTICATION
    
    def recover(self, error_info: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to refresh authentication"""
        logger.info("Authentication refresh strategy: attempting to refresh tokens")
        
        try:
            # Attempt to refresh authentication
            self.refresh_func()
            
            return {
                "strategy": "auth_refresh",
                "action": "refresh_auth",
                "success": True,
                "estimated_recovery_time": 10.0
            }
        except Exception as e:
            logger.error(f"Authentication refresh failed: {str(e)}")
            return {
                "strategy": "auth_refresh",
                "action": "refresh_auth",
                "success": False,
                "error": str(e),
                "estimated_recovery_time": 0.0
            }
    
    def get_strategy_name(self) -> str:
        return "auth_refresh"


class CircuitBreakerAdvanced:
    """Advanced circuit breaker with multiple states and recovery strategies"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, expected_exception: Exception = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self.success_count = 0
        self.half_open_success_threshold = 3
        self.expected_exception = expected_exception
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "state_changes": []
        }
    
    def can_execute(self) -> bool:
        """Check if operation can be executed based on current state"""
        self.metrics["total_requests"] += 1
        
        if self.state == "closed":
            return True
        elif self.state == "open":
            if self._should_attempt_reset():
                self._transition_to_half_open()
                return True
            return False
        else:  # half-open
            return True
    
    def record_success(self):
        """Record successful operation"""
        self.metrics["successful_requests"] += 1
        self.success_count += 1
        
        if self.state == "half-open":
            if self.success_count >= self.half_open_success_threshold:
                self._transition_to_closed()
        elif self.state == "closed":
            # Reset failure count on success
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record failed operation"""
        self.metrics["failed_requests"] += 1
        self.failure_count += 1
        self.success_count = 0  # Reset success counter
        self.last_failure_time = time.time()
        
        if self.state == "half-open":
            self._transition_to_open()
        elif self.state == "closed" and self.failure_count >= self.failure_threshold:
            self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset"""
        return (
            self.last_failure_time is not None and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _transition_to_half_open(self):
        """Transition circuit breaker to half-open state"""
        self._log_state_change("closed", "half-open")
        self.state = "half-open"
        self.success_count = 0
    
    def _transition_to_closed(self):
        """Transition circuit breaker to closed state"""
        self._log_state_change("half-open", "closed")
        self.state = "closed"
        self.failure_count = 0
        self.success_count = 0
    
    def _transition_to_open(self):
        """Transition circuit breaker to open state"""
        self._log_state_change(self.state, "open")
        self.state = "open"
    
    def _log_state_change(self, from_state: str, to_state: str):
        """Log state change"""
        logger.warning(f"Circuit breaker state change: {from_state} -> {to_state}")
        self.metrics["state_changes"].append({
            "from": from_state,
            "to": to_state,
            "timestamp": time.time(),
            "failure_count": self.failure_count
        })
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        total_requests = self.metrics["total_requests"]
        success_rate = (
            self.metrics["successful_requests"] / total_requests 
            if total_requests > 0 else 0.0
        )
        
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_requests": total_requests,
            "successful_requests": self.metrics["successful_requests"],
            "failed_requests": self.metrics["failed_requests"],
            "success_rate": success_rate,
            "last_failure_time": self.last_failure_time,
            "state_changes": self.metrics["state_changes"]
        }
    
    def reset(self):
        """Manually reset circuit breaker"""
        logger.info("Manually resetting circuit breaker")
        self.state = "closed"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.metrics["state_changes"].append({
            "from": "manual_reset",
            "to": "closed",
            "timestamp": time.time()
        })


class ErrorRecoveryManager:
    """Main error recovery manager"""
    
    def __init__(self, config: VLMRecoveryConfig):
        self.config = config
        self.circuit_breaker = None
        self.recovery_strategies = []
        self.error_history = []
        self.alert_count = 0
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize recovery components"""
        if self.config.enable_circuit_breaker:
            self.circuit_breaker = CircuitBreakerAdvanced(
                failure_threshold=self.config.circuit_breaker_failure_threshold,
                recovery_timeout=self.config.circuit_breaker_recovery_timeout
            )
        
        # Initialize default recovery strategies
        self.recovery_strategies = [
            NetworkRetryStrategy(
                max_attempts=self.config.max_retry_attempts,
                base_delay=self.config.retry_delay_base
            ),
            RateLimitBackoffStrategy(
                max_attempts=self.config.max_retry_attempts,
                base_delay=60.0
            ),
            ResourceScalingStrategy()
        ]
    
    def add_recovery_strategy(self, strategy: RecoveryStrategy):
        """Add a custom recovery strategy"""
        self.recovery_strategies.append(strategy)
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.circuit_breaker:
            return self.circuit_breaker.can_execute()
        return True
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle an error and determine recovery strategy"""
        if context is None:
            context = {}
        
        # Classify the error
        error_info = ErrorClassifier.classify_error(error, context)
        self.error_history.append(error_info)
        
        # Check if this triggers an alert
        self._check_alert_threshold(error_info)
        
        logger.error(f"Error classified: {error_info['category'].value} - {error_info['error_type'].value}")
        
        # Find appropriate recovery strategy
        recovery_action = self._find_recovery_strategy(error_info, context)
        
        if recovery_action:
            logger.info(f"Recovery strategy: {recovery_action['strategy']}")
            return recovery_action
        else:
            logger.error("No recovery strategy found for this error")
            return {
                "action": "fail",
                "error_info": error_info,
                "message": "No recovery strategy available"
            }
    
    def _find_recovery_strategy(self, error_info: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find appropriate recovery strategy for the error"""
        for strategy in self.recovery_strategies:
            if strategy.can_recover(error_info):
                return strategy.recover(error_info, context)
        
        return None
    
    def record_success(self):
        """Record successful operation"""
        if self.circuit_breaker:
            self.circuit_breaker.record_success()
    
    def record_failure(self):
        """Record failed operation"""
        if self.circuit_breaker:
            self.circuit_breaker.record_failure()
    
    def _check_alert_threshold(self, error_info: Dict[str, Any]):
        """Check if error triggers alert threshold"""
        self.alert_count += 1
        
        if self.alert_count >= self.config.alert_threshold:
            logger.critical(f"Alert threshold reached: {self.alert_count} errors")
            self._trigger_alert(error_info)
    
    def _trigger_alert(self, error_info: Dict[str, Any]):
        """Trigger alert for systematic failures"""
        alert_data = {
            "alert_type": "systematic_failures",
            "error_count": self.alert_count,
            "recent_errors": self.error_history[-10:],  # Last 10 errors
            "circuit_breaker_state": self.circuit_breaker.get_metrics() if self.circuit_breaker else None,
            "timestamp": time.time()
        }
        
        logger.critical(f"System alert triggered: {json.dumps(alert_data, indent=2)}")
        
        # In a real implementation, this would send to monitoring system
        # send_alert(alert_data)
    
    def get_recovery_metrics(self) -> Dict[str, Any]:
        """Get recovery system metrics"""
        metrics = {
            "total_errors": len(self.error_history),
            "recent_errors": len([e for e in self.error_history if time.time() - e["timestamp"] < 3600]),  # Last hour
            "error_categories": {},
            "recovery_strategies_used": {},
            "circuit_breaker": None
        }
        
        # Count error categories
        for error_info in self.error_history:
            category = error_info["category"].value
            metrics["error_categories"][category] = metrics["error_categories"].get(category, 0) + 1
        
        if self.circuit_breaker:
            metrics["circuit_breaker"] = self.circuit_breaker.get_metrics()
        
        return metrics
    
    def reset_metrics(self):
        """Reset recovery metrics"""
        self.error_history.clear()
        self.alert_count = 0
        if self.circuit_breaker:
            self.circuit_breaker.reset()
        
        logger.info("Recovery metrics reset")