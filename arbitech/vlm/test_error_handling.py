"""
Test Suite for VLM Error Handling and Fallback System

Comprehensive tests for all components of the error handling and fallback system.
Tests validate integration, error scenarios, and quality assessment.
"""

import unittest
import asyncio
import time
import random
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import all VLM error handling components
from vlm import (
    # Fallback System
    FallbackHandler, FallbackTier, FallbackStatus, FallbackConfig,
    VLMPrimaryStrategy, OCRFallbackStrategy, PatternMatchingStrategy, ManualInterventionStrategy,
    
    # Error Recovery
    ErrorRecoveryManager, ErrorClassifier, VLMRecoveryConfig, NetworkRetryStrategy,
    RateLimitBackoffStrategy, ResourceScalingStrategy, AuthenticationRefreshStrategy,
    ErrorSeverity, ErrorCategory, ErrorType,
    
    # Quality Assessment
    QualityAssessmentEngine, QualityConfig, QualityMetrics, QualityLevel,
    ConfidenceValidator, CompletenessValidator, ConsistencyValidator,
    
    # Retry Logic
    IntelligentRetryEngine, RetryConfig, RetryStrategy, RetryCondition,
    ExponentialBackoffJitterCalculator
)


class TestFallbackHandler(unittest.TestCase):
    """Test the Fallback Handler system"""
    
    def setUp(self):
        self.config = FallbackConfig(
            confidence_threshold=0.6,
            circuit_breaker_threshold=3,
            enable_ocr_fallback=True,
            enable_pattern_matching=True
        )
        self.handler = FallbackHandler(self.config)
    
    def test_fallback_config_initialization(self):
        """Test fallback configuration initialization"""
        self.assertEqual(self.config.confidence_threshold, 0.6)
        self.assertTrue(self.config.enable_ocr_fallback)
        self.assertEqual(self.config.circuit_breaker_threshold, 3)
    
    def test_vlm_primary_strategy_success(self):
        """Test successful VLM primary strategy"""
        mock_client = Mock()
        mock_client.analyze.return_value = {
            "result": "success",
            "confidence": 0.9
        }
        
        strategy = VLMPrimaryStrategy(mock_client, timeout=30)
        result = strategy.execute("test_data", {})
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["confidence"], 0.9)
        self.assertEqual(result["tier"], FallbackTier.VLM_PRIMARY.value)
    
    def test_vlm_primary_strategy_failure(self):
        """Test VLM primary strategy failure"""
        mock_client = Mock()
        mock_client.analyze.side_effect = Exception("Service unavailable")
        
        strategy = VLMPrimaryStrategy(mock_client, timeout=30)
        result = strategy.execute("test_data", {})
        
        self.assertEqual(result["status"], "failed")
        self.assertIn("Service unavailable", result["error"])
        self.assertEqual(result["confidence"], 0.0)
    
    def test_circuit_breaker_functionality(self):
        """Test circuit breaker opens after threshold failures"""
        mock_client = Mock()
        mock_client.analyze.side_effect = Exception("Service unavailable")
        
        strategy = VLMPrimaryStrategy(mock_client, timeout=30)
        
        # Initial state should be closed
        self.assertTrue(self.handler.circuit_breaker.can_execute())
        self.assertEqual(self.handler.circuit_breaker.state, "closed")
        
        # Execute multiple times to trigger circuit breaker
        for i in range(self.config.circuit_breaker_threshold):
            self.handler.process_with_fallback("test_data", {})
        
        # Circuit breaker should be open
        self.assertEqual(self.handler.circuit_breaker.state, "open")
        self.assertFalse(self.handler.circuit_breaker.can_execute())
    
    def test_ocr_fallback_strategy(self):
        """Test OCR fallback strategy"""
        mock_ocr = Mock()
        mock_ocr.extract_text.return_value = [
            {"text": "extracted text", "confidence": 0.8}
        ]
        
        strategy = OCRFallbackStrategy(mock_ocr, timeout=15)
        result = strategy.execute("test_data", {})
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tier"], FallbackTier.OCR_FALLBACK.value)
        self.assertIn("ocr_text", result["result"])
    
    def test_pattern_matching_strategy(self):
        """Test pattern matching strategy"""
        patterns = {
            "betting_pattern": {
                "match_type": "filename",
                "keywords": ["odds", "betting"],
                "confidence": 0.6
            }
        }
        
        strategy = PatternMatchingStrategy(patterns, timeout=5)
        
        # Mock file-like object with betting keywords
        mock_file = Mock()
        mock_file.filename = "betting_odds_image.jpg"
        
        result = strategy.execute(mock_file, {})
        
        self.assertIn(result["status"], ["success", "partial_success"])
        self.assertEqual(result["tier"], FallbackTier.PATTERN_MATCHING.value)
    
    def test_manual_intervention_strategy(self):
        """Test manual intervention strategy"""
        def mock_handler(input_data, context, timeout):
            return {
                "status": "completed",
                "manual_result": "User processed result",
                "confidence": 0.8
            }
        
        strategy = ManualInterventionStrategy(mock_handler, timeout=300)
        result = strategy.execute("test_data", {})
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tier"], FallbackTier.MANUAL_INTERVENTION.value)


class TestErrorRecovery(unittest.TestCase):
    """Test Error Recovery system"""
    
    def setUp(self):
        self.config = VLMRecoveryConfig(
            max_retry_attempts=3,
            circuit_breaker_failure_threshold=5,
            auto_recovery_enabled=True
        )
        self.recovery_manager = ErrorRecoveryManager(self.config)
    
    def test_error_classification_network_error(self):
        """Test error classification for network errors"""
        error = ConnectionError("Network connection failed")
        error_info = ErrorClassifier.classify_error(error, {})
        
        self.assertEqual(error_info["category"], ErrorCategory.NETWORK)
        self.assertEqual(error_info["severity"], ErrorSeverity.LOW)
        self.assertTrue(error_info["recoverable"])
    
    def test_error_classification_rate_limit(self):
        """Test error classification for rate limiting"""
        error = Exception("Rate limit exceeded")
        error_info = ErrorClassifier.classify_error(error, {})
        
        self.assertEqual(error_info["category"], ErrorCategory.RATE_LIMIT)
        self.assertEqual(error_info["severity"], ErrorSeverity.MEDIUM)
        self.assertTrue(error_info["recoverable"])
    
    def test_error_classification_auth_error(self):
        """Test error classification for authentication errors"""
        error = Exception("Unauthorized access")
        error_info = ErrorClassifier.classify_error(error, {})
        
        self.assertEqual(error_info["category"], ErrorCategory.AUTHENTICATION)
        self.assertEqual(error_info["severity"], ErrorSeverity.HIGH)
        self.assertFalse(error_info["recoverable"])
    
    def test_network_retry_strategy(self):
        """Test network retry strategy"""
        error_info = {
            "category": ErrorCategory.NETWORK,
            "error_type": ErrorType.CONNECTION_TIMEOUT,
            "retry_count": 1
        }
        
        strategy = NetworkRetryStrategy(max_attempts=3, base_delay=1.0)
        
        self.assertTrue(strategy.can_recover(error_info))
        
        recovery_action = strategy.recover(error_info, {})
        
        self.assertEqual(recovery_action["strategy"], "network_retry")
        self.assertEqual(recovery_action["action"], "retry")
        self.assertIn("delay", recovery_action)
    
    def test_rate_limit_backoff_strategy(self):
        """Test rate limit backoff strategy"""
        error_info = {
            "category": ErrorCategory.RATE_LIMIT,
            "error_type": ErrorType.RATE_LIMIT_EXCEEDED,
            "retry_count": 1
        }
        
        strategy = RateLimitBackoffStrategy(max_attempts=5, base_delay=60.0)
        
        self.assertTrue(strategy.can_recover(error_info))
        
        recovery_action = strategy.recover(error_info, {})
        
        self.assertEqual(recovery_action["strategy"], "rate_limit_backoff")
        self.assertEqual(recovery_action["action"], "backoff")
        self.assertGreater(recovery_action["delay"], 60.0)
    
    def test_resource_scaling_strategy(self):
        """Test resource scaling strategy"""
        error_info = {
            "category": ErrorCategory.RESOURCE,
            "error_type": ErrorType.MEMORY_ERROR
        }
        
        context = {
            "batch_size": 10,
            "max_image_size": 2048
        }
        
        strategy = ResourceScalingStrategy(scaling_factor=0.8)
        
        self.assertTrue(strategy.can_recover(error_info))
        
        recovery_action = strategy.recover(error_info, context)
        
        self.assertEqual(recovery_action["strategy"], "resource_scaling")
        self.assertEqual(recovery_action["action"], "scale_down")
        self.assertEqual(recovery_action["scaled_context"]["batch_size"], 8)
        self.assertEqual(recovery_action["scaled_context"]["max_image_size"], 1638)
    
    def test_circuit_breaker_advanced(self):
        """Test advanced circuit breaker functionality"""
        cb = self.recovery_manager.circuit_breaker
        
        # Initially closed
        self.assertEqual(cb.state, "closed")
        self.assertTrue(cb.can_execute())
        
        # Record failures
        for i in range(3):
            cb.record_failure()
        
        # Should still be closed
        self.assertEqual(cb.state, "closed")
        
        # Record more failures to reach threshold
        for i in range(2):
            cb.record_failure()
        
        # Should now be open
        self.assertEqual(cb.state, "open")
        self.assertFalse(cb.can_execute())
        
        # Wait and check half-open transition
        time.sleep(1)  # Wait for timeout
        cb._should_attempt_reset()  # Manually trigger reset check
        
        self.assertEqual(cb.state, "half-open")
    
    def test_metrics_collection(self):
        """Test metrics collection and reporting"""
        # Generate some errors
        error1 = ConnectionError("Network error")
        error2 = Exception("Rate limit")
        
        self.recovery_manager.handle_error(error1, {})
        self.recovery_manager.handle_error(error2, {})
        
        metrics = self.recovery_manager.get_recovery_metrics()
        
        self.assertEqual(metrics["total_errors"], 2)
        self.assertIn("network", metrics["error_categories"])
        self.assertIn("rate_limit", metrics["error_categories"])


class TestQualityAssessment(unittest.TestCase):
    """Test Quality Assessment system"""
    
    def setUp(self):
        self.config = QualityConfig(
            overall_quality_threshold=0.6,
            min_confidence_threshold=0.5,
            auto_reject_threshold=0.3
        )
        self.quality_engine = QualityAssessmentEngine(self.config)
    
    def test_confidence_validation(self):
        """Test confidence validation"""
        validator = ConfidenceValidator()
        
        # High confidence output
        high_conf_output = {"result": "good result", "confidence": 0.9}
        result = validator.validate(high_conf_output, {})
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["raw_score"], 0.9)
        
        # Low confidence output
        low_conf_output = {"result": "poor result", "confidence": 0.2}
        result = validator.validate(low_conf_output, {})
        
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["raw_score"], 0.2)
    
    def test_completeness_validation(self):
        """Test completeness validation"""
        validator = CompletenessValidator()
        
        # Complete output
        complete_output = {
            "home_odds": 2.0,
            "away_odds": 1.8,
            "draw_odds": 3.2
        }
        context = {
            "expected_fields": ["home_odds", "away_odds", "draw_odds"],
            "output_type": "dict"
        }
        
        result = validator.validate(complete_output, context)
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["raw_score"], 1.0)
        self.assertEqual(len(result["missing_fields"]), 0)
        
        # Incomplete output
        incomplete_output = {
            "home_odds": 2.0,
            "away_odds": 1.8
            # Missing draw_odds
        }
        
        result = validator.validate(incomplete_output, context)
        
        self.assertFalse(result["is_valid"])
        self.assertIn("draw_odds", result["missing_fields"])
    
    def test_consistency_validation(self):
        """Test consistency validation"""
        validator = ConsistencyValidator()
        
        # Consistent text
        consistent_text = "The odds for team A are 2.0. Team B has odds of 1.8."
        result = validator.validate(consistent_text, {})
        
        # Should have reasonable consistency score
        self.assertGreaterEqual(result["raw_score"], 0.5)
        
        # Inconsistent text (contradictory)
        inconsistent_text = "Team A will win. Team B will also win."
        result = validator.validate(inconsistent_text, {})
        
        # Should have lower consistency score
        self.assertLess(result["raw_score"], 0.9)
    
    def test_format_validation(self):
        """Test format validation"""
        validator = FormatValidator()
        
        # Valid dictionary format
        valid_dict = {
            "home_odds": 2.0,
            "away_odds": 1.8,
            "draw_odds": 3.2
        }
        context = {
            "expected_output_type": "dict",
            "expected_keys": ["home_odds", "away_odds", "draw_odds"]
        }
        
        result = validator.validate(valid_dict, context)
        
        self.assertTrue(result["is_valid"])
        self.assertGreaterEqual(result["raw_score"], 0.8)
        
        # Invalid format
        invalid_output = "This is just text, not a dictionary"
        result = validator.validate(invalid_output, context)
        
        self.assertFalse(result["is_valid"])
    
    def test_comprehensive_quality_assessment(self):
        """Test comprehensive quality assessment"""
        # High quality output
        high_quality_output = {
            "home_odds": 2.0,
            "away_odds": 1.8,
            "confidence": 0.9,
            "processing_time": 1.2
        }
        
        context = {
            "expected_fields": ["home_odds", "away_odds"],
            "output_type": "dict",
            "min_confidence_threshold": 0.5
        }
        
        metrics = self.quality_engine.assess_quality(high_quality_output, context)
        
        self.assertEqual(metrics.quality_level, QualityLevel.EXCELLENT)
        self.assertGreaterEqual(metrics.overall_score, 0.8)
        self.assertEqual(len(metrics.issues), 0)
        
        # Test rejection logic
        should_reject, reason = self.quality_engine.should_reject_output(metrics)
        self.assertFalse(should_reject)
    
    def test_quality_rejection(self):
        """Test quality rejection logic"""
        # Low quality metrics
        low_quality_metrics = QualityMetrics(
            overall_score=0.2,
            confidence_score=0.1,
            completeness_score=0.3,
            consistency_score=0.2,
            format_score=0.3,
            content_score=0.1,
            quality_level=QualityLevel.UNACCEPTABLE,
            validation_details={},
            timestamp=time.time(),
            issues=["Low confidence", "Incomplete data"],
            recommendations=["Improve input quality"]
        )
        
        should_reject, reason = self.quality_engine.should_reject_output(low_quality_metrics)
        
        self.assertTrue(should_reject)
        self.assertIn("quality below threshold", reason.lower())


class TestRetryLogic(unittest.TestCase):
    """Test Retry Logic system"""
    
    def setUp(self):
        self.config = RetryConfig(
            max_attempts=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF_JITTER,
            base_delay=1.0,
            max_delay=10.0,
            jitter=True
        )
        self.retry_engine = IntelligentRetryEngine(self.config)
    
    def test_successful_retry(self):
        """Test successful retry scenario"""
        call_count = 0
        
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"
        
        result = self.retry_engine.execute_with_retry(flaky_function)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["attempts"], 3)
        self.assertEqual(result["result"], "success")
    
    def test_max_attempts_exceeded(self):
        """Test when max attempts are exceeded"""
        def always_failing_function():
            raise Exception("Always fails")
        
        result = self.retry_engine.execute_with_retry(always_failing_function)
        
        self.assertFalse(result["success"])
        self.assertEqual(result["attempts"], self.config.max_attempts)
        self.assertIn("error", result)
    
    def test_retry_condition_evaluation(self):
        """Test retry condition evaluation"""
        # Test always retry condition
        always_config = RetryConfig(retry_condition=RetryCondition.ALWAYS)
        self.retry_engine.update_config(retry_condition=RetryCondition.ALWAYS)
        
        # Should retry even on non-retryable errors
        error = ValueError("Invalid input")
        should_retry = self.retry_engine.retry_engine.retry_condition_evaluator.should_retry(
            error, 1, always_config, {}
        )
        
        self.assertTrue(should_retry)
        
        # Test never retry condition
        never_config = RetryConfig(retry_condition=RetryCondition.NEVER)
        self.retry_engine.update_config(retry_condition=RetryCondition.NEVER)
        
        should_retry = self.retry_engine.retry_condition_evaluator.should_retry(
            error, 1, never_config, {}
        )
        
        self.assertFalse(should_retry)
    
    def test_backoff_calculation(self):
        """Test different backoff calculation strategies"""
        # Test exponential backoff
        exp_config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            multiplier=2.0
        )
        exp_engine = IntelligentRetryEngine(exp_config)
        
        delays = []
        for attempt in range(1, 4):
            delay = exp_engine.calculator.calculate_delay(attempt, 1.0, exp_config)
            delays.append(delay)
        
        # Should be exponential: 1, 2, 4
        self.assertEqual(delays[0], 1.0)
        self.assertEqual(delays[1], 2.0)
        self.assertEqual(delays[2], 4.0)
        
        # Test jitter
        jitter_config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF_JITTER,
            base_delay=1.0,
            multiplier=2.0,
            jitter=True,
            jitter_factor=0.1
        )
        jitter_engine = IntelligentRetryEngine(jitter_config)
        
        # Jittered delays should vary
        delays_jittered = []
        for attempt in range(1, 4):
            delay = jitter_engine.calculator.calculate_delay(attempt, 1.0, jitter_config)
            delays_jittered.append(delay)
        
        # All delays should be around expected values but with variation
        self.assertAlmostEqual(delays_jittered[0], 1.0, delta=0.2)
    
    def test_retry_metrics(self):
        """Test retry metrics collection"""
        # Successful retry
        call_count = 0
        
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return "success"
        
        self.retry_engine.execute_with_retry(flaky_function)
        
        metrics = self.retry_engine.get_metrics()
        
        self.assertGreater(metrics["total_attempts"], 0)
        self.assertGreaterEqual(metrics["success_rate"], 0.0)
        self.assertIn("config", metrics)
        self.assertIn("retry_distribution", metrics)
    
    def test_adaptive_retry_strategy(self):
        """Test adaptive retry strategy"""
        adaptive_config = RetryConfig(strategy=RetryStrategy.ADAPTIVE_BACKOFF)
        adaptive_engine = IntelligentRetryEngine(adaptive_config)
        
        # Simulate successful operations
        for _ in range(5):
            adaptive_engine.adaptive_calculator.record_attempt_result(True)
        
        # Check adaptation factor adjustment
        self.assertLess(adaptive_engine.adaptive_calculator.adaptation_factor, 1.0)
        
        # Simulate failed operations
        for _ in range(5):
            adaptive_engine.adaptive_calculator.record_attempt_result(False)
        
        # Check adaptation factor increase
        self.assertGreater(adaptive_engine.adaptive_calculator.adaptation_factor, 0.9)
    
    def test_retry_decorator(self):
        """Test retry decorator"""
        call_count = 0
        
        @retry_on_failure(RetryConfig(max_attempts=3))
        def decorated_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"
        
        result = decorated_function()
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        # Initialize all components
        self.fallback_config = FallbackConfig(confidence_threshold=0.7)
        self.recovery_config = VLMRecoveryConfig(max_retry_attempts=3)
        self.quality_config = QualityConfig(overall_quality_threshold=0.6)
        self.retry_config = RetryConfig(max_attempts=3)
        
        self.fallback_handler = FallbackHandler(self.fallback_config)
        self.error_recovery = ErrorRecoveryManager(self.recovery_config)
        self.quality_engine = QualityAssessmentEngine(self.quality_config)
        self.retry_engine = IntelligentRetryEngine(self.retry_config)
        
        # Setup mock strategies
        self._setup_mock_strategies()
    
    def _setup_mock_strategies(self):
        """Setup mock strategies for testing"""
        # Mock VLM strategy
        mock_vlm = Mock()
        mock_vlm.analyze.return_value = {
            "result": "Mock VLM Result",
            "confidence": 0.8
        }
        
        self.fallback_handler.set_strategy(
            FallbackTier.VLM_PRIMARY,
            VLMPrimaryStrategy(mock_vlm, timeout=30)
        )
        
        # Mock OCR strategy
        mock_ocr = Mock()
        mock_ocr.extract_text.return_value = [
            {"text": "Mock OCR text", "confidence": 0.7}
        ]
        
        self.fallback_handler.set_strategy(
            FallbackTier.OCR_FALLBACK,
            OCRFallbackStrategy(mock_ocr, timeout=15)
        )
    
    def test_fallback_quality_integration(self):
        """Test integration between fallback and quality assessment"""
        # Process with fallback
        fallback_result = self.fallback_handler.process_with_fallback("test_data", {})
        
        self.assertTrue(fallback_result["status"] in ["success", "partial_success"])
        
        # Assess quality of result
        quality_metrics = self.quality_engine.assess_quality(
            fallback_result["result"], {}
        )
        
        self.assertIsInstance(quality_metrics, QualityMetrics)
        self.assertGreaterEqual(quality_metrics.overall_score, 0.0)
    
    def test_retry_fallback_integration(self):
        """Test integration between retry and fallback"""
        call_count = 0
        
        def failing_vlm_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Network error")
            return self.fallback_handler.process_with_fallback("test_data", {})
        
        result = self.retry_engine.execute_with_retry(failing_vlm_operation)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["attempts"], 2)
    
    def test_end_to_end_quality_assessment(self):
        """Test end-to-end quality assessment pipeline"""
        # High quality result
        high_quality_result = {
            "home_odds": 2.0,
            "away_odds": 1.8,
            "confidence": 0.9,
            "completeness": True
        }
        
        context = {
            "expected_fields": ["home_odds", "away_odds"],
            "output_type": "dict"
        }
        
        # Full quality assessment
        metrics = self.quality_engine.assess_quality(high_quality_result, context)
        
        # Should meet quality standards
        should_reject, reason = self.quality_engine.should_reject_output(metrics)
        self.assertFalse(should_reject)
        self.assertGreaterEqual(metrics.overall_score, 0.6)
    
    def test_error_recovery_fallback_integration(self):
        """Test integration between error recovery and fallback"""
        # Test error recovery triggering fallback
        error = ConnectionError("Network failure")
        
        recovery_action = self.error_recovery.handle_error(error, {})
        
        self.assertIsNotNone(recovery_action)
        self.assertIn("strategy", recovery_action)
        
        # Error should be recoverable with network retry
        self.assertEqual(recovery_action["strategy"], "network_retry")


class TestAdvancedScenarios(unittest.TestCase):
    """Test advanced scenarios and edge cases"""
    
    def test_cascade_failure_scenario(self):
        """Test cascade failure handling"""
        config = FallbackConfig(confidence_threshold=0.9)  # Very high threshold
        handler = FallbackHandler(config)
        
        # Mock all strategies to return low confidence
        low_confidence_strategy = Mock()
        low_confidence_strategy.execute.return_value = {
            "status": "success",
            "confidence": 0.3,  # Below threshold
            "result": "low confidence result"
        }
        
        for tier in [FallbackTier.VLM_PRIMARY, FallbackTier.OCR_FALLBACK, FallbackTier.PATTERN_MATCHING]:
            handler.set_strategy(tier, low_confidence_strategy)
        
        result = handler.process_with_fallback("test_data", {})
        
        # Should continue through all tiers but none should meet threshold
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["final_result"])
        self.assertTrue(result.get("manual_intervention_required"))
    
    def test_circuit_breaker_reset_scenario(self):
        """Test circuit breaker reset after recovery"""
        config = FallbackConfig(circuit_breaker_threshold=2, circuit_breaker_timeout=1)
        handler = FallbackHandler(config)
        
        # Mock failing VLM
        failing_vlm = Mock()
        failing_vlm.analyze.side_effect = Exception("Service down")
        
        handler.set_strategy(FallbackTier.VLM_PRIMARY, VLMPrimaryStrategy(failing_vlm))
        
        # Trigger circuit breaker
        for _ in range(config.circuit_breaker_threshold):
            handler.process_with_fallback("test_data", {})
        
        self.assertEqual(handler.circuit_breaker.state, "open")
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Set up working VLM
        working_vlm = Mock()
        working_vlm.analyze.return_value = {"result": "success", "confidence": 0.9}
        handler.set_strategy(FallbackTier.VLM_PRIMARY, VLMPrimaryStrategy(working_vlm))
        
        # Should transition to half-open
        result = handler.process_with_fallback("test_data", {})
        self.assertEqual(handler.circuit_breaker.state, "half-open")
        
        # Successful operation should close circuit breaker
        handler.circuit_breaker.record_success()
        self.assertEqual(handler.circuit_breaker.state, "closed")
    
    def test_adaptive_quality_thresholds(self):
        """Test adaptive quality threshold adjustment"""
        config = QualityConfig(
            overall_quality_threshold=0.7,
            min_confidence_threshold=0.6
        )
        engine = QualityAssessmentEngine(config)
        
        # Simulate series of low-quality results
        for _ in range(5):
            low_quality_result = {
                "home_odds": 2.0,  # Missing away_odds
                "confidence": 0.4
            }
            
            context = {
                "expected_fields": ["home_odds", "away_odds"],
                "output_type": "dict"
            }
            
            metrics = engine.assess_quality(low_quality_result, context)
            
            # Log for analysis (in real system, this would trigger threshold adjustment)
            self.assertLess(metrics.overall_score, 0.6)
    
    def test_complex_retry_scenarios(self):
        """Test complex retry scenarios with mixed error types"""
        config = RetryConfig(
            max_attempts=5,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF_JITTER
        )
        engine = IntelligentRetryEngine(config)
        
        error_sequence = [
            ConnectionError("Network error"),
            TimeoutError("Request timeout"),
            Exception("Rate limit exceeded"),
            ValueError("Invalid input")  # This should not be retried
        ]
        
        call_count = 0
        
        def complex_function():
            nonlocal call_count
            current_error = error_sequence[call_count % len(error_sequence)]
            call_count += 1
            
            if call_count <= 4:  # Retry first 4 errors
                raise current_error
            else:  # Fail on 5th
                raise ValueError("Invalid input")
        
        result = engine.execute_with_retry(complex_function)
        
        # Should retry first 4 errors but fail on validation error
        self.assertFalse(result["success"])
        self.assertLessEqual(result["attempts"], 5)
    
    def test_concurrent_quality_assessment(self):
        """Test concurrent quality assessment"""
        import concurrent.futures
        
        config = QualityConfig(overall_quality_threshold=0.6)
        engine = QualityAssessmentEngine(config)
        
        def assess_quality(worker_id):
            # Simulate different quality outputs
            quality_score = 0.5 + (worker_id * 0.1)
            result = {
                "home_odds": 2.0,
                "confidence": quality_score
            }
            
            context = {"output_type": "dict"}
            metrics = engine.assess_quality(result, context)
            
            return metrics.overall_score
        
        # Test with multiple workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(assess_quality, i) for i in range(5)]
            scores = [future.result() for future in futures]
        
        # All workers should complete successfully
        self.assertEqual(len(scores), 5)
        self.assertTrue(all(score >= 0.0 for score in scores))


def run_comprehensive_tests():
    """Run all test suites"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestFallbackHandler,
        TestErrorRecovery,
        TestQualityAssessment,
        TestRetryLogic,
        TestIntegration,
        TestAdvancedScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result


if __name__ == "__main__":
    print("Running comprehensive tests for VLM Error Handling and Fallback System")
    print("=" * 75)
    
    result = run_comprehensive_tests()
    
    print("\n" + "=" * 75)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("✅ All systems operational - High confidence in error handling system!")
    elif success_rate >= 75:
        print("⚠️  Most systems operational - Review failed tests")
    else:
        print("❌ Multiple system failures - Immediate attention required")
