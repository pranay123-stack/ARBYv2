"""
Fallback Handler - Multi-tier fallback system for VLM operations
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class FallbackTier(Enum):
    """Fallback tiers from highest to lowest reliability"""
    VLM_PRIMARY = "vlm_primary"
    OCR_FALLBACK = "ocr_fallback"
    PATTERN_MATCHING = "pattern_matching"
    MANUAL_INTERVENTION = "manual_intervention"


class FallbackStatus(Enum):
    """Status of fallback operations"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_required"


@dataclass
class FallbackConfig:
    """Configuration for fallback strategies"""
    enable_ocr_fallback: bool = True
    enable_pattern_matching: bool = True
    enable_manual_intervention: bool = True
    vlm_timeout: int = 30
    ocr_timeout: int = 15
    pattern_timeout: int = 5
    max_retries_per_tier: int = 3
    confidence_threshold: float = 0.7
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60


class FallbackStrategy(ABC):
    """Abstract base class for fallback strategies"""
    
    @abstractmethod
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the fallback strategy"""
        pass
    
    @abstractmethod
    def get_confidence(self) -> float:
        """Get confidence score for this strategy"""
        pass
    
    @abstractmethod
    def get_processing_time(self) -> float:
        """Get processing time for this strategy"""
        pass


class VLMPrimaryStrategy(FallbackStrategy):
    """Primary VLM strategy"""
    
    def __init__(self, vlm_client, timeout: int = 30):
        self.vlm_client = vlm_client
        self.timeout = timeout
        self.processing_time = 0.0
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            result = self.vlm_client.analyze(
                input_data,
                timeout=self.timeout,
                **context
            )
            self.processing_time = time.time() - start_time
            
            return {
                "status": "success",
                "result": result,
                "tier": FallbackTier.VLM_PRIMARY.value,
                "confidence": result.get("confidence", 0.9),
                "processing_time": self.processing_time
            }
        except Exception as e:
            self.processing_time = time.time() - start_time
            logger.error(f"VLM primary strategy failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "tier": FallbackTier.VLM_PRIMARY.value,
                "confidence": 0.0,
                "processing_time": self.processing_time
            }
    
    def get_confidence(self) -> float:
        return 0.9
    
    def get_processing_time(self) -> float:
        return self.processing_time


class OCRFallbackStrategy(FallbackStrategy):
    """OCR-based fallback strategy"""
    
    def __init__(self, ocr_engine, timeout: int = 15):
        self.ocr_engine = ocr_engine
        self.timeout = timeout
        self.processing_time = 0.0
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            # Extract text using OCR
            text_results = self.ocr_engine.extract_text(
                input_data,
                timeout=self.timeout
            )
            
            # Basic analysis of OCR results
            analysis_result = self._analyze_ocr_text(text_results, context)
            
            self.processing_time = time.time() - start_time
            
            return {
                "status": "success" if analysis_result["confidence"] > 0.5 else "partial_success",
                "result": {
                    "ocr_text": text_results,
                    "analysis": analysis_result
                },
                "tier": FallbackTier.OCR_FALLBACK.value,
                "confidence": analysis_result["confidence"],
                "processing_time": self.processing_time
            }
        except Exception as e:
            self.processing_time = time.time() - start_time
            logger.error(f"OCR fallback strategy failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "tier": FallbackTier.OCR_FALLBACK.value,
                "confidence": 0.0,
                "processing_time": self.processing_time
            }
    
    def _analyze_ocr_text(self, text_results: List[Dict], context: Dict[str, Any]) -> Dict[str, Any]:
        """Basic analysis of OCR text results"""
        # Combine all text
        full_text = " ".join([result.get("text", "") for result in text_results])
        
        # Simple confidence calculation based on text completeness
        confidence = min(0.7, len(full_text) / 100) if full_text else 0.3
        
        return {
            "text": full_text,
            "confidence": confidence,
            "word_count": len(full_text.split()) if full_text else 0,
            "extraction_method": "ocr"
        }
    
    def get_confidence(self) -> float:
        return 0.6
    
    def get_processing_time(self) -> float:
        return self.processing_time


class PatternMatchingStrategy(FallbackStrategy):
    """Pattern matching fallback strategy"""
    
    def __init__(self, patterns: Dict[str, Any], timeout: int = 5):
        self.patterns = patterns
        self.timeout = timeout
        self.processing_time = 0.0
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            # Apply pattern matching rules
            matches = self._match_patterns(input_data, context)
            
            self.processing_time = time.time() - start_time
            
            return {
                "status": "partial_success" if matches["confidence"] > 0.3 else "failed",
                "result": matches,
                "tier": FallbackTier.PATTERN_MATCHING.value,
                "confidence": matches["confidence"],
                "processing_time": self.processing_time
            }
        except Exception as e:
            self.processing_time = time.time() - start_time
            logger.error(f"Pattern matching strategy failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "tier": FallbackTier.PATTERN_MATCHING.value,
                "confidence": 0.0,
                "processing_time": self.processing_time
            }
    
    def _match_patterns(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply pattern matching to input data"""
        # Simplified pattern matching logic
        matches = []
        confidence = 0.0
        
        # Look for predefined patterns
        if hasattr(input_data, 'filename'):
            filename = input_data.filename.lower()
            for pattern_name, pattern_config in self.patterns.items():
                if pattern_config.get("match_type") == "filename":
                    if any(keyword in filename for keyword in pattern_config.get("keywords", [])):
                        matches.append({
                            "pattern": pattern_name,
                            "match_type": "filename",
                            "confidence": pattern_config.get("confidence", 0.4)
                        })
                        confidence = max(confidence, pattern_config.get("confidence", 0.4))
        
        return {
            "matches": matches,
            "confidence": min(confidence, 0.5),  # Cap pattern matching confidence
            "method": "pattern_matching"
        }
    
    def get_confidence(self) -> float:
        return 0.4
    
    def get_processing_time(self) -> float:
        return self.processing_time


class ManualInterventionStrategy(FallbackStrategy):
    """Manual intervention fallback strategy"""
    
    def __init__(self, intervention_handler: Callable, timeout: int = 300):
        self.intervention_handler = intervention_handler
        self.timeout = timeout
        self.processing_time = 0.0
    
    def execute(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        
        try:
            # Request manual intervention
            result = self.intervention_handler(input_data, context, self.timeout)
            
            self.processing_time = time.time() - start_time
            
            return {
                "status": "success" if result.get("status") == "completed" else "manual_required",
                "result": result,
                "tier": FallbackTier.MANUAL_INTERVENTION.value,
                "confidence": result.get("confidence", 0.5),
                "processing_time": self.processing_time
            }
        except Exception as e:
            self.processing_time = time.time() - start_time
            logger.error(f"Manual intervention strategy failed: {str(e)}")
            return {
                "status": "manual_required",
                "error": str(e),
                "tier": FallbackTier.MANUAL_INTERVENTION.value,
                "confidence": 0.0,
                "processing_time": self.processing_time
            }
    
    def get_confidence(self) -> float:
        return 0.5
    
    def get_processing_time(self) -> float:
        return self.processing_time


class CircuitBreaker:
    """Circuit breaker for VLM operations"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    def can_execute(self) -> bool:
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True
    
    def record_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class FallbackHandler:
    """Main fallback handler coordinating multi-tier fallback system"""
    
    def __init__(self, config: FallbackConfig):
        self.config = config
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker_threshold,
            timeout=config.circuit_breaker_timeout
        )
        self.strategies = {}
        self.success_rates = {}
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize fallback strategies"""
        # This would be populated with actual implementations
        self.strategies = {
            FallbackTier.VLM_PRIMARY: None,  # To be set by user
            FallbackTier.OCR_FALLBACK: None,  # To be set by user
            FallbackTier.PATTERN_MATCHING: None,  # To be set by user
            FallbackTier.MANUAL_INTERVENTION: None,  # To be set by user
        }
    
    def set_strategy(self, tier: FallbackTier, strategy: FallbackStrategy):
        """Set a specific fallback strategy"""
        self.strategies[tier] = strategy
    
    def process_with_fallback(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process input with multi-tier fallback"""
        logger.info("Starting fallback processing")
        
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            logger.warning("Circuit breaker is open, skipping VLM primary strategy")
        
        execution_log = []
        
        # Try strategies in order
        for tier in FallbackTier:
            strategy = self.strategies.get(tier)
            if not strategy:
                logger.warning(f"Strategy for tier {tier.value} not configured")
                continue
            
            logger.info(f"Attempting tier: {tier.value}")
            
            try:
                result = strategy.execute(input_data, context)
                execution_log.append({
                    "tier": tier.value,
                    "status": result["status"],
                    "confidence": result["confidence"],
                    "processing_time": result["processing_time"]
                })
                
                # Check if result meets quality threshold
                if result["confidence"] >= self.config.confidence_threshold:
                    self.circuit_breaker.record_success()
                    self._update_success_rates(tier, True)
                    
                    return {
                        "status": "success",
                        "final_result": result["result"],
                        "confidence": result["confidence"],
                        "tier_used": tier.value,
                        "execution_log": execution_log,
                        "processing_time": result["processing_time"]
                    }
                
                # Record partial success or failure
                if result["status"] == "success":
                    self.circuit_breaker.record_success()
                    self._update_success_rates(tier, True)
                else:
                    self.circuit_breaker.record_failure()
                    self._update_success_rates(tier, False)
                
                # Continue to next fallback tier
                if result["status"] not in ["failed", "manual_required"]:
                    continue
                    
            except Exception as e:
                logger.error(f"Error in tier {tier.value}: {str(e)}")
                self.circuit_breaker.record_failure()
                self._update_success_rates(tier, False)
                execution_log.append({
                    "tier": tier.value,
                    "status": "error",
                    "error": str(e),
                    "confidence": 0.0
                })
                continue
        
        # All tiers failed
        logger.error("All fallback tiers failed")
        
        return {
            "status": "failed",
            "final_result": None,
            "confidence": 0.0,
            "tier_used": None,
            "execution_log": execution_log,
            "message": "All fallback strategies exhausted",
            "manual_intervention_required": True
        }
    
    def _update_success_rates(self, tier: FallbackTier, success: bool):
        """Update success rates for optimization"""
        if tier.value not in self.success_rates:
            self.success_rates[tier.value] = {"total": 0, "successes": 0}
        
        self.success_rates[tier.value]["total"] += 1
        if success:
            self.success_rates[tier.value]["successes"] += 1
    
    def get_success_rates(self) -> Dict[str, Dict[str, float]]:
        """Get success rates for all tiers"""
        rates = {}
        for tier_name, stats in self.success_rates.items():
            if stats["total"] > 0:
                rates[tier_name] = {
                    "success_rate": stats["successes"] / stats["total"],
                    "total_attempts": stats["total"],
                    "successful_attempts": stats["successes"]
                }
        return rates
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "circuit_breaker_state": self.circuit_breaker.state,
            "failure_count": self.circuit_breaker.failure_count,
            "success_rates": self.get_success_rates(),
            "strategies_configured": list(self.strategies.keys()),
            "config": self.config.__dict__
        }