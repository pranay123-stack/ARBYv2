"""
Retry Logic - Intelligent retry mechanisms with exponential backoff and different strategies
"""

import logging
import time
import random
import asyncio
from typing import Dict, List, Optional, Any, Callable, Union, Type
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Different retry strategies"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    EXPONENTIAL_BACKOFF_JITTER = "exponential_backoff_jitter"
    LINEAR_BACKOFF = "linear_backoff"
    ADAPTIVE_BACKOFF = "adaptive_backoff"
    FIBONACCI_BACKOFF = "fibonacci_backoff"
    CUSTOM = "custom"


class RetryCondition(Enum):
    """Conditions for triggering retry"""
    ALWAYS = "always"
    ON_SPECIFIC_ERRORS = "on_specific_errors"
    ON_ERROR_TYPES = "on_error_types"
    ON_STATUS_CODES = "on_status_codes"
    ON_EXCEPTIONS = "on_exceptions"
    NEVER = "never"


@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    timeout: float = 300.0
    
    # Strategy settings
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF_JITTER
    
    # Condition settings
    retry_condition: RetryCondition = RetryCondition.ON_SPECIFIC_ERRORS
    retryable_exceptions: List[Type[Exception]] = None
    retryable_error_types: List[str] = None
    retryable_status_codes: List[int] = None
    non_retryable_errors: List[str] = None
    
    # Adaptive settings
    adaptive_scaling_factor: float = 0.8
    adaptive_min_attempts: int = 2
    adaptive_max_attempts: int = 5
    
    # Circuit breaker integration
    circuit_breaker_integration: bool = True
    
    def __post_init__(self):
        if self.retryable_exceptions is None:
            self.retryable_exceptions = [ConnectionError, TimeoutError, ValueError]
        
        if self.retryable_error_types is None:
            self.retryable_error_types = ["network_error", "timeout", "rate_limit"]
        
        if self.retryable_status_codes is None:
            self.retryable_status_codes = [408, 429, 502, 503, 504]
        
        if self.non_retryable_errors is None:
            self.non_retryable_errors = ["authentication_error", "authorization_error", "validation_error"]


class BackoffCalculator(ABC):
    """Abstract base class for backoff calculators"""
    
    @abstractmethod
    def calculate_delay(self, attempt: int, base_delay: float, config: RetryConfig) -> float:
        """Calculate delay for given attempt"""
        pass


class FixedDelayCalculator(BackoffCalculator):
    """Fixed delay calculator"""
    
    def calculate_delay(self, attempt: int, base_delay: float, config: RetryConfig) -> float:
        return base_delay


class ExponentialBackoffCalculator(BackoffCalculator):
    """Exponential backoff calculator"""
    
    def calculate_delay(self, attempt: int, base_delay: float, config: RetryConfig) -> float:
        delay = base_delay * (config.multiplier ** (attempt - 1))
        return min(delay, config.max_delay)


class ExponentialBackoffJitterCalculator(BackoffCalculator):
    """Exponential backoff with jitter calculator"""
    
    def calculate_delay(self, attempt: int, base_delay: float, config: RetryConfig) -> float:
        delay = base_delay * (config.multiplier ** (attempt - 1))
        
        if config.jitter:
            jitter_range = delay * config.jitter_factor
            jitter = random.uniform(-jitter_range, jitter_range)
            delay += jitter
        
        return min(max(0, delay), config.max_delay)


class LinearBackoffCalculator(BackoffCalculator):
    """Linear backoff calculator"""
    
    def calculate_delay(self, attempt: int, base_delay: float, config: RetryConfig) -> float:
        delay = base_delay * attempt
        return min(delay, config.max_delay)


class FibonacciBackoffCalculator(BackoffCalculator):
    """Fibonacci backoff calculator"""
    
    def __init__(self):
        self.fib_cache = {1: 1, 2: 1}
    
    def calculate_delay(self, attempt: int, base_delay: float, config: RetryConfig) -> float:
        fib_value = self._get_fibonacci(attempt)
        delay = base_delay * fib_value
        return min(delay, config.max_delay)
    
    def _get_fibonacci(self, n: int) -> int:
        """Get nth Fibonacci number"""
        if n in self.fib_cache:
            return self.fib_cache[n]
        
        self.fib_cache[n] = self._get_fibonacci(n - 1) + self._get_fibonacci(n - 2)
        return self.fib_cache[n]


class AdaptiveBackoffCalculator(BackoffCalculator):
    """Adaptive backoff calculator that adjusts based on success rates"""
    
    def __init__(self):
        self.success_history = []
        self.adaptation_factor = 1.0
    
    def calculate_delay(self, attempt: int, base_delay: float, config: RetryConfig) -> float:
        # Adjust adaptation factor based on recent success rate
        if len(self.success_history) >= 3:
            recent_success_rate = sum(self.success_history[-3:]) / 3
            if recent_success_rate > 0.7:
                self.adaptation_factor *= 0.9  # Decrease delay on high success
            elif recent_success_rate < 0.3:
                self.adaptation_factor *= 1.1  # Increase delay on low success
        
        # Calculate base delay
        base_delay_adjusted = base_delay * self.adaptation_factor
        delay = base_delay_adjusted * (config.multiplier ** (attempt - 1))
        
        if config.jitter:
            jitter_range = delay * config.jitter_factor
            jitter = random.uniform(-jitter_range, jitter_range)
            delay += jitter
        
        return min(max(0, delay), config.max_delay)
    
    def record_attempt_result(self, success: bool):
        """Record the result of an attempt for adaptation"""
        self.success_history.append(success)
        
        # Keep only recent history
        if len(self.success_history) > 20:
            self.success_history = self.success_history[-20:]


class RetryConditionEvaluator:
    """Evaluates whether a retry should be attempted based on conditions"""
    
    @staticmethod
    def should_retry(error: Exception, attempt: int, config: RetryConfig, context: Dict[str, Any] = None) -> bool:
        """Determine if retry should be attempted"""
        if context is None:
            context = {}
        
        # Check max attempts
        if attempt > config.max_attempts:
            return False
        
        # Check timeout
        start_time = context.get("start_time", time.time())
        if time.time() - start_time > config.timeout:
            return False
        
        # Evaluate condition
        condition_result = RetryConditionEvaluator._evaluate_condition(error, attempt, config, context)
        
        return condition_result
    
    @staticmethod
    def _evaluate_condition(error: Exception, attempt: int, config: RetryConfig, context: Dict[str, Any]) -> bool:
        """Evaluate specific retry condition"""
        if config.retry_condition == RetryCondition.NEVER:
            return False
        elif config.retry_condition == RetryCondition.ALWAYS:
            return True
        elif config.retry_condition == RetryCondition.ON_SPECIFIC_ERRORS:
            return RetryConditionEvaluator._check_specific_errors(error, config)
        elif config.retry_condition == RetryCondition.ON_ERROR_TYPES:
            return RetryConditionEvaluator._check_error_types(error, config)
        elif config.retry_condition == RetryCondition.ON_STATUS_CODES:
            return RetryConditionEvaluator._check_status_codes(error, config)
        elif config.retry_condition == RetryCondition.ON_EXCEPTIONS:
            return RetryConditionEvaluator._check_exceptions(error, config)
        
        return False
    
    @staticmethod
    def _check_specific_errors(error: Exception, config: RetryConfig) -> bool:
        """Check for specific error patterns"""
        error_message = str(error).lower()
        
        # Check non-retryable errors first
        for pattern in config.non_retryable_errors:
            if pattern.lower() in error_message:
                return False
        
        # Check retryable errors
        for pattern in config.retryable_error_types:
            if pattern.lower() in error_message:
                return True
        
        return False
    
    @staticmethod
    def _check_error_types(error: Exception, config: RetryConfig) -> bool:
        """Check for retryable error types"""
        error_type_name = type(error).__name__.lower()
        
        # Check non-retryable errors
        for pattern in config.non_retryable_errors:
            if pattern.lower() in error_type_name:
                return False
        
        return error_type_name in [et.lower() for et in config.retryable_error_types]
    
    @staticmethod
    def _check_status_codes(error: Exception, config: RetryConfig) -> bool:
        """Check for retryable status codes"""
        if hasattr(error, 'status_code'):
            return error.status_code in config.retryable_status_codes
        return False
    
    @staticmethod
    def _check_exceptions(error: Exception, config: RetryConfig) -> bool:
        """Check for retryable exception types"""
        return isinstance(error, tuple(config.retryable_exceptions))


class RetryMetrics:
    """Metrics tracking for retry operations"""
    
    def __init__(self):
        self.total_attempts = 0
        self.successful_retries = 0
        self.failed_retries = 0
        self.retry_distribution = {}  # attempts -> count
        self.error_distribution = {}  # error_type -> count
        self.average_attempts = 0.0
        self.success_rate = 0.0
        self.avg_delay_history = []
    
    def record_attempt(self, attempt: int, success: bool, delay: float, error_type: str = None):
        """Record a retry attempt"""
        self.total_attempts += 1
        
        if success:
            self.successful_retries += 1
        else:
            self.failed_retries += 1
        
        # Update distribution
        self.retry_distribution[attempt] = self.retry_distribution.get(attempt, 0) + 1
        
        if error_type:
            self.error_distribution[error_type] = self.error_distribution.get(error_type, 0) + 1
        
        # Update averages
        if self.total_attempts > 0:
            self.success_rate = self.successful_retries / self.total_attempts
        
        self.avg_delay_history.append(delay)
        if len(self.avg_delay_history) > 100:
            self.avg_delay_history = self.avg_delay_history[-100:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        avg_delay = sum(self.avg_delay_history) / len(self.avg_delay_history) if self.avg_delay_history else 0.0
        
        return {
            "total_attempts": self.total_attempts,
            "successful_retries": self.successful_retries,
            "failed_retries": self.failed_retries,
            "success_rate": self.success_rate,
            "retry_distribution": self.retry_distribution,
            "error_distribution": self.error_distribution,
            "average_delay": avg_delay,
            "recent_avg_delay": avg_delay  # Alias for compatibility
        }
    
    def reset(self):
        """Reset metrics"""
        self.total_attempts = 0
        self.successful_retries = 0
        self.failed_retries = 0
        self.retry_distribution = {}
        self.error_distribution = {}
        self.success_rate = 0.0
        self.avg_delay_history = []


class IntelligentRetryEngine:
    """Main retry engine with intelligent retry mechanisms"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.backoff_calculators = self._initialize_backoff_calculators()
        self.metrics = RetryMetrics()
        self.adaptive_calculator = AdaptiveBackoffCalculator()
        
        # Choose appropriate backoff calculator
        self.calculator = self.backoff_calculators.get(self.config.strategy, ExponentialBackoffJitterCalculator())
    
    def _initialize_backoff_calculators(self) -> Dict[RetryStrategy, BackoffCalculator]:
        """Initialize backoff calculators"""
        adaptive_calc = AdaptiveBackoffCalculator()
        self.adaptive_calculator = adaptive_calc
        
        return {
            RetryStrategy.FIXED_DELAY: FixedDelayCalculator(),
            RetryStrategy.EXPONENTIAL_BACKOFF: ExponentialBackoffCalculator(),
            RetryStrategy.EXPONENTIAL_BACKOFF_JITTER: ExponentialBackoffJitterCalculator(),
            RetryStrategy.LINEAR_BACKOFF: LinearBackoffCalculator(),
            RetryStrategy.ADAPTIVE_BACKOFF: adaptive_calc,
            RetryStrategy.FIBONACCI_BACKOFF: FibonacciBackoffCalculator()
        }
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Execute function with retry logic (sync version)"""
        start_time = time.time()
        context = {"start_time": start_time}
        
        last_error = None
        result = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.debug(f"Attempt {attempt}/{self.config.max_attempts}")
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Success!
                self.metrics.record_attempt(attempt, True, 0.0)
                
                if self.config.strategy == RetryStrategy.ADAPTIVE_BACKOFF:
                    self.adaptive_calculator.record_attempt_result(True)
                
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt,
                    "total_time": time.time() - start_time
                }
            
            except Exception as error:
                last_error = error
                error_type = type(error).__name__
                
                # Record failed attempt
                delay = self._calculate_delay(attempt)
                self.metrics.record_attempt(attempt, False, delay, error_type)
                
                if self.config.strategy == RetryStrategy.ADAPTIVE_BACKOFF:
                    self.adaptive_calculator.record_attempt_result(False)
                
                logger.warning(f"Attempt {attempt} failed: {str(error)}")
                
                # Check if we should retry
                if not RetryConditionEvaluator.should_retry(error, attempt, self.config, context):
                    logger.error(f"Not retrying after attempt {attempt}")
                    break
                
                # If not the last attempt, wait before retrying
                if attempt < self.config.max_attempts:
                    self._wait_before_retry(attempt, delay)
        
        # All attempts failed
        return {
            "success": False,
            "result": None,
            "attempts": self.config.max_attempts,
            "total_time": time.time() - start_time,
            "error": str(last_error),
            "error_type": type(last_error).__name__ if last_error else None,
            "metrics": self.metrics.get_metrics()
        }
    
    async def execute_with_retry_async(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Execute function with retry logic (async version)"""
        start_time = time.time()
        context = {"start_time": start_time}
        
        last_error = None
        result = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.debug(f"Async attempt {attempt}/{self.config.max_attempts}")
                
                # Execute async function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                # Success!
                self.metrics.record_attempt(attempt, True, 0.0)
                
                if self.config.strategy == RetryStrategy.ADAPTIVE_BACKOFF:
                    self.adaptive_calculator.record_attempt_result(True)
                
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt,
                    "total_time": time.time() - start_time
                }
            
            except Exception as error:
                last_error = error
                error_type = type(error).__name__
                
                # Record failed attempt
                delay = self._calculate_delay(attempt)
                self.metrics.record_attempt(attempt, False, delay, error_type)
                
                if self.config.strategy == RetryStrategy.ADAPTIVE_BACKOFF:
                    self.adaptive_calculator.record_attempt_result(False)
                
                logger.warning(f"Async attempt {attempt} failed: {str(error)}")
                
                # Check if we should retry
                if not RetryConditionEvaluator.should_retry(error, attempt, self.config, context):
                    logger.error(f"Not retrying async attempt {attempt}")
                    break
                
                # If not the last attempt, wait before retrying
                if attempt < self.config.max_attempts:
                    await self._wait_before_retry_async(attempt, delay)
        
        # All attempts failed
        return {
            "success": False,
            "result": None,
            "attempts": self.config.max_attempts,
            "total_time": time.time() - start_time,
            "error": str(last_error),
            "error_type": type(last_error).__name__ if last_error else None,
            "metrics": self.metrics.get_metrics()
        }
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for current attempt"""
        delay = self.calculator.calculate_delay(attempt, self.config.base_delay, self.config)
        
        # Apply adaptive scaling if enabled
        if self.config.strategy == RetryStrategy.ADAPTIVE_BACKOFF:
            delay *= self.adaptive_calculator.adaptation_factor
        
        return delay
    
    def _wait_before_retry(self, attempt: int, delay: float):
        """Wait before retry (sync version)"""
        logger.info(f"Waiting {delay:.2f}s before attempt {attempt + 1}")
        time.sleep(delay)
    
    async def _wait_before_retry_async(self, attempt: int, delay: float):
        """Wait before retry (async version)"""
        logger.info(f"Async waiting {delay:.2f}s before attempt {attempt + 1}")
        await asyncio.sleep(delay)
    
    def estimate_total_time(self, max_attempts: int = None) -> float:
        """Estimate total time for all retry attempts"""
        if max_attempts is None:
            max_attempts = self.config.max_attempts
        
        total_delay = 0.0
        for attempt in range(2, max_attempts + 1):  # Start from 2 since first attempt has no delay
            delay = self.calculator.calculate_delay(attempt, self.config.base_delay, self.config)
            total_delay += delay
        
        return total_delay
    
    def get_recommended_attempts(self, error: Exception) -> int:
        """Get recommended number of attempts based on error type"""
        error_message = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Rate limiting errors need more attempts with longer delays
        if any(pattern in error_message for pattern in ["rate limit", "quota", "too many requests"]):
            return min(self.config.max_attempts, self.config.adaptive_max_attempts)
        
        # Network errors benefit from more attempts
        if any(pattern in error_message for pattern in ["connection", "timeout", "network"]):
            return min(self.config.max_attempts, self.config.adaptive_max_attempts)
        
        # Authentication errors should not be retried
        if any(pattern in error_message for pattern in ["auth", "token", "unauthorized"]):
            return self.config.adaptive_min_attempts
        
        # Validation errors should not be retried
        if any(pattern in error_message for pattern in ["validation", "bad request", "invalid"]):
            return self.config.adaptive_min_attempts
        
        # Default to reasonable number
        return min(self.config.max_attempts, self.config.adaptive_max_attempts)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get retry metrics"""
        base_metrics = self.metrics.get_metrics()
        
        # Add configuration info
        base_metrics["config"] = {
            "strategy": self.config.strategy.value,
            "max_attempts": self.config.max_attempts,
            "base_delay": self.config.base_delay,
            "max_delay": self.config.max_delay,
            "multiplier": self.config.multiplier,
            "jitter": self.config.jitter
        }
        
        # Add adaptive info if applicable
        if self.config.strategy == RetryStrategy.ADAPTIVE_BACKOFF:
            base_metrics["adaptive_info"] = {
                "adaptation_factor": self.adaptive_calculator.adaptation_factor,
                "recent_success_rate": sum(self.adaptive_calculator.success_history[-3:]) / 3 if len(self.adaptive_calculator.success_history) >= 3 else None
            }
        
        return base_metrics
    
    def reset_metrics(self):
        """Reset metrics"""
        self.metrics.reset()
        if self.config.strategy == RetryStrategy.ADAPTIVE_BACKOFF:
            self.adaptive_calculator.success_history = []
            self.adaptive_calculator.adaptation_factor = 1.0
        
        logger.info("Retry metrics reset")
    
    def update_config(self, **kwargs):
        """Update retry configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning(f"Unknown config parameter: {key}")
        
        # Reinitialize calculator if strategy changed
        if 'strategy' in kwargs:
            self.calculator = self.backoff_calculators.get(self.config.strategy, ExponentialBackoffJitterCalculator())
        
        logger.info(f"Retry configuration updated: {kwargs}")


# Decorator for easy retry integration
def retry_on_failure(config: RetryConfig = None, logger_name: str = None):
    """Decorator to add retry logic to functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            engine = IntelligentRetryEngine(config)
            
            # Set up logging
            if logger_name:
                logger = logging.getLogger(logger_name)
            else:
                logger = logging.getLogger(__name__)
            
            result = engine.execute_with_retry(func, *args, **kwargs)
            
            if result["success"]:
                logger.debug(f"Function {func.__name__} succeeded after {result['attempts']} attempts")
                return result["result"]
            else:
                logger.error(f"Function {func.__name__} failed after {result['attempts']} attempts: {result['error']}")
                raise Exception(result["error"])
        
        return wrapper
    return decorator


# Example usage function
def example_vlm_operation_with_retry():
    """Example of how to use the retry logic with VLM operations"""
    
    # Configure retry logic for different error scenarios
    network_retry_config = RetryConfig(
        max_attempts=5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF_JITTER,
        base_delay=2.0,
        max_delay=30.0,
        retryable_exceptions=[ConnectionError, TimeoutError],
        retryable_error_types=["network_error", "timeout"]
    )
    
    rate_limit_retry_config = RetryConfig(
        max_attempts=8,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF_JITTER,
        base_delay=60.0,
        max_delay=300.0,
        retryable_error_types=["rate_limit", "quota_exceeded"]
    )
    
    # Initialize retry engines
    network_engine = IntelligentRetryEngine(network_retry_config)
    rate_limit_engine = IntelligentRetryEngine(rate_limit_retry_config)
    
    # Example function to retry
    def vlm_operation_with_fallback(image_data):
        # This would be your actual VLM operation
        import random
        if random.random() < 0.3:  # 30% chance of failure
            raise ConnectionError("Network connection failed")
        return {"result": "success", "confidence": 0.9}
    
    # Execute with retry
    result = network_engine.execute_with_retry(vlm_operation_with_fallback, "sample_image")
    
    return result