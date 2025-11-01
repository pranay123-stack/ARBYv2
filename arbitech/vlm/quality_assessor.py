"""
Quality Assessor - Confidence scoring and quality validation for VLM outputs
"""

import logging
import time
import statistics
from typing import Dict, List, Optional, Any, Tuple, Union
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
import re

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """Quality levels for VLM outputs"""
    EXCELLENT = "excellent"  # 0.9 - 1.0
    GOOD = "good"            # 0.7 - 0.9
    ACCEPTABLE = "acceptable" # 0.5 - 0.7
    POOR = "poor"            # 0.3 - 0.5
    UNACCEPTABLE = "unacceptable" # 0.0 - 0.3


class ValidationType(Enum):
    """Types of quality validation"""
    CONFIDENCE_SCORE = "confidence_score"
    COMPLETENESS_CHECK = "completeness_check"
    CONSISTENCY_CHECK = "consistency_check"
    FORMAT_VALIDATION = "format_validation"
    CONTENT_VALIDATION = "content_validation"
    CROSS_VALIDATION = "cross_validation"


@dataclass
class QualityMetrics:
    """Quality assessment metrics"""
    overall_score: float
    confidence_score: float
    completeness_score: float
    consistency_score: float
    format_score: float
    content_score: float
    quality_level: QualityLevel
    validation_details: Dict[str, Any]
    timestamp: float
    issues: List[str]
    recommendations: List[str]


@dataclass
class QualityConfig:
    """Configuration for quality assessment"""
    min_confidence_threshold: float = 0.5
    min_completeness_threshold: float = 0.6
    min_consistency_threshold: float = 0.7
    min_format_threshold: float = 0.8
    min_content_threshold: float = 0.5
    overall_quality_threshold: float = 0.6
    
    # Weight multipliers for different aspects
    confidence_weight: float = 0.3
    completeness_weight: float = 0.25
    consistency_weight: float = 0.2
    format_weight: float = 0.15
    content_weight: float = 0.1
    
    # Cross-validation settings
    enable_cross_validation: bool = True
    cross_validation_threshold: float = 0.8
    cross_validation_methods: List[str] = None
    
    # Auto-rejection settings
    auto_reject_threshold: float = 0.3
    auto_reject_criteria: List[str] = None
    
    def __post_init__(self):
        if self.cross_validation_methods is None:
            self.cross_validation_methods = ["consistency_check", "format_validation"]
        
        if self.auto_reject_criteria is None:
            self.auto_reject_criteria = ["very_low_confidence", "incomplete_output", "format_violation"]


class QualityValidator(ABC):
    """Abstract base class for quality validators"""
    
    @abstractmethod
    def validate(self, output: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output and return results"""
        pass
    
    @abstractmethod
    def get_score(self, validation_result: Dict[str, Any]) -> float:
        """Get quality score from validation result"""
        pass


class ConfidenceValidator(QualityValidator):
    """Validator for confidence scores"""
    
    def validate(self, output: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate confidence score"""
        # Extract confidence from output
        confidence = self._extract_confidence(output)
        
        # Validate confidence score
        is_valid = confidence >= context.get("min_confidence_threshold", 0.5)
        
        return {
            "confidence": confidence,
            "is_valid": is_valid,
            "validation_type": "confidence",
            "issues": [] if is_valid else [f"Confidence too low: {confidence:.2f}"],
            "raw_score": confidence
        }
    
    def get_score(self, validation_result: Dict[str, Any]) -> float:
        return validation_result.get("raw_score", 0.0)
    
    def _extract_confidence(self, output: Any) -> float:
        """Extract confidence score from VLM output"""
        if isinstance(output, dict):
            return output.get("confidence", 0.0)
        elif hasattr(output, "confidence"):
            return getattr(output, "confidence", 0.0)
        else:
            # If no explicit confidence, estimate based on content
            return self._estimate_confidence(output)
    
    def _estimate_confidence(self, output: Any) -> float:
        """Estimate confidence when not explicitly provided"""
        # Simple heuristic: more structured output = higher confidence
        if isinstance(output, dict):
            if len(output) > 3 and "entities" in output:
                return 0.8
            return 0.6
        
        if isinstance(output, str):
            if len(output) > 50 and not output.strip().endswith("?"):
                return 0.7
            return 0.4
        
        return 0.5


class CompletenessValidator(QualityValidator):
    """Validator for output completeness"""
    
    def validate(self, output: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output completeness"""
        expected_fields = context.get("expected_fields", [])
        output_type = context.get("output_type", "dict")
        
        completeness_score = self._calculate_completeness(output, expected_fields, output_type, context)
        is_valid = completeness_score >= context.get("min_completeness_threshold", 0.6)
        
        issues = []
        if not is_valid:
            issues.append(f"Output incomplete: {completeness_score:.2f} < required threshold")
        
        return {
            "completeness": completeness_score,
            "is_valid": is_valid,
            "validation_type": "completeness",
            "issues": issues,
            "raw_score": completeness_score,
            "expected_fields": expected_fields,
            "missing_fields": self._find_missing_fields(output, expected_fields, output_type)
        }
    
    def get_score(self, validation_result: Dict[str, Any]) -> float:
        return validation_result.get("raw_score", 0.0)
    
    def _calculate_completeness(self, output: Any, expected_fields: List[str], output_type: str, context: Dict[str, Any] = None) -> float:
        """Calculate completeness score"""
        if context is None:
            context = {}
            
        if output_type == "dict" and isinstance(output, dict):
            return len([k for k in expected_fields if k in output and output[k] is not None]) / len(expected_fields) if expected_fields else 1.0
        
        if output_type == "text" and isinstance(output, str):
            # For text outputs, check for key sections
            expected_sections = context.get("expected_sections", [])
            if not expected_sections:
                return 1.0 if len(output) > 10 else 0.0
            
            found_sections = sum(1 for section in expected_sections if section.lower() in output.lower())
            return found_sections / len(expected_sections)
        
        return 1.0 if output is not None else 0.0
    
    def _find_missing_fields(self, output: Any, expected_fields: List[str], output_type: str) -> List[str]:
        """Find missing fields in output"""
        if output_type == "dict" and isinstance(output, dict):
            return [field for field in expected_fields if field not in output or output[field] is None]
        return []


class ConsistencyValidator(QualityValidator):
    """Validator for output consistency"""
    
    def validate(self, output: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output consistency"""
        consistency_score = self._calculate_consistency(output, context)
        is_valid = consistency_score >= context.get("min_consistency_threshold", 0.7)
        
        issues = []
        if not is_valid:
            issues.append(f"Output inconsistent: {consistency_score:.2f}")
        
        return {
            "consistency": consistency_score,
            "is_valid": is_valid,
            "validation_type": "consistency",
            "issues": issues,
            "raw_score": consistency_score,
            "consistency_details": self._get_consistency_details(output)
        }
    
    def get_score(self, validation_result: Dict[str, Any]) -> float:
        return validation_result.get("raw_score", 0.0)
    
    def _calculate_consistency(self, output: Any, context: Dict[str, Any]) -> float:
        """Calculate consistency score"""
        if isinstance(output, dict):
            return self._calculate_dict_consistency(output, context)
        elif isinstance(output, str):
            return self._calculate_text_consistency(output, context)
        return 1.0
    
    def _calculate_dict_consistency(self, output: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate consistency for dictionary outputs"""
        scores = []
        
        # Check type consistency
        for key, value in output.items():
            if isinstance(value, str):
                # Check if string contains contradictory information
                consistency = self._check_string_consistency(value)
                scores.append(consistency)
        
        return statistics.mean(scores) if scores else 1.0
    
    def _calculate_text_consistency(self, output: str, context: Dict[str, Any]) -> float:
        """Calculate consistency for text outputs"""
        # Simple consistency check: look for contradictions
        sentences = re.split(r'[.!?]+', output.strip())
        contradictions = 0
        
        for i, sentence1 in enumerate(sentences):
            for sentence2 in sentences[i+1:]:
                if self._are_contradictory(sentence1, sentence2):
                    contradictions += 1
        
        max_contradictions = len(sentences) * (len(sentences) - 1) / 2
        consistency = 1.0 - (contradictions / max_contradictions) if max_contradictions > 0 else 1.0
        
        return max(0.0, consistency)
    
    def _check_string_consistency(self, text: str) -> float:
        """Check consistency of a string"""
        # Simple check for self-contradiction
        # Look for opposing words
        positive_words = ["yes", "good", "true", "correct", "valid"]
        negative_words = ["no", "bad", "false", "incorrect", "invalid"]
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        if positive_count > 0 and negative_count > 0:
            return 0.3  # Potential contradiction
        
        return 1.0
    
    def _are_contradictory(self, text1: str, text2: str) -> bool:
        """Check if two texts are contradictory"""
        # Simple contradiction detection
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        contradiction_pairs = [
            ("yes", "no"), ("true", "false"), ("correct", "incorrect"),
            ("good", "bad"), ("valid", "invalid"), ("success", "failure")
        ]
        
        for pos, neg in contradiction_pairs:
            if (pos in text1_lower and neg in text2_lower) or \
               (neg in text1_lower and pos in text2_lower):
                return True
        
        return False
    
    def _get_consistency_details(self, output: Any) -> Dict[str, Any]:
        """Get detailed consistency information"""
        return {
            "output_size": len(str(output)),
            "complexity_score": self._calculate_complexity(output),
            "self_reference_consistent": True  # Placeholder
        }
    
    def _calculate_complexity(self, output: Any) -> float:
        """Calculate output complexity score"""
        if isinstance(output, dict):
            return min(1.0, len(output) / 10)  # Normalize by expected size
        elif isinstance(output, str):
            return min(1.0, len(output) / 100)  # Normalize by expected length
        return 0.5


class FormatValidator(QualityValidator):
    """Validator for output format compliance"""
    
    def __init__(self, expected_format: str = "dict"):
        self.expected_format = expected_format
    
    def validate(self, output: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output format"""
        format_score = self._validate_format(output, context)
        is_valid = format_score >= context.get("min_format_threshold", 0.8)
        
        issues = []
        if not is_valid:
            issues.append(f"Format invalid: {format_score:.2f}")
        
        return {
            "format": format_score,
            "is_valid": is_valid,
            "validation_type": "format",
            "issues": issues,
            "raw_score": format_score,
            "format_details": self._get_format_details(output)
        }
    
    def get_score(self, validation_result: Dict[str, Any]) -> float:
        return validation_result.get("raw_score", 0.0)
    
    def _validate_format(self, output: Any, context: Dict[str, Any]) -> float:
        """Validate output format"""
        expected_type = context.get("expected_output_type", "dict")
        
        if expected_type == "dict" and isinstance(output, dict):
            return self._validate_dict_format(output, context)
        elif expected_type == "text" and isinstance(output, str):
            return self._validate_text_format(output, context)
        elif expected_type == "structured" and isinstance(output, dict):
            return self._validate_structured_format(output, context)
        
        return 0.0
    
    def _validate_dict_format(self, output: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Validate dictionary format"""
        expected_keys = context.get("expected_keys", [])
        schema = context.get("schema", {})
        
        score = 1.0
        
        # Check for required keys
        missing_keys = [key for key in expected_keys if key not in output]
        score -= len(missing_keys) * 0.2
        
        # Check schema compliance if provided
        if schema:
            schema_compliance = self._check_schema_compliance(output, schema)
            score *= schema_compliance
        
        return max(0.0, score)
    
    def _validate_text_format(self, output: str, context: Dict[str, Any]) -> float:
        """Validate text format"""
        min_length = context.get("min_length", 10)
        max_length = context.get("max_length", 1000)
        
        if len(output) < min_length:
            return 0.3
        if len(output) > max_length:
            return 0.7
        
        # Check for proper structure
        has_sentences = bool(re.search(r'[.!?]', output))
        has_paragraphs = '\n\n' in output
        
        score = 0.5  # Base score
        if has_sentences:
            score += 0.3
        if has_paragraphs:
            score += 0.2
        
        return min(1.0, score)
    
    def _validate_structured_format(self, output: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Validate structured format (e.g., JSON-like)"""
        # Check for proper JSON structure
        try:
            # If it's a proper dict, give high score
            if isinstance(output, dict) and len(output) > 0:
                return 1.0
        except:
            pass
        
        return 0.5
    
    def _check_schema_compliance(self, output: Dict[str, Any], schema: Dict[str, Any]) -> float:
        """Check compliance with schema"""
        compliance_score = 1.0
        
        for field, field_schema in schema.items():
            if field in output:
                field_type = field_schema.get("type")
                if field_type and not self._check_field_type(output[field], field_type):
                    compliance_score -= 0.2
            else:
                compliance_score -= 0.1
        
        return max(0.0, compliance_score)
    
    def _check_field_type(self, value: Any, expected_type: str) -> bool:
        """Check if field value matches expected type"""
        type_map = {
            "string": str,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True
    
    def _get_format_details(self, output: Any) -> Dict[str, Any]:
        """Get detailed format information"""
        return {
            "output_type": type(output).__name__,
            "output_size": len(str(output)),
            "is_dict": isinstance(output, dict),
            "is_string": isinstance(output, str),
            "is_list": isinstance(output, list),
            "keys_count": len(output.keys()) if isinstance(output, dict) else 0,
            "characters_count": len(str(output))
        }


class ContentValidator(QualityValidator):
    """Validator for content quality"""
    
    def validate(self, output: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate content quality"""
        content_score = self._assess_content_quality(output, context)
        is_valid = content_score >= context.get("min_content_threshold", 0.5)
        
        issues = []
        if not is_valid:
            issues.append(f"Content quality poor: {content_score:.2f}")
        
        return {
            "content": content_score,
            "is_valid": is_valid,
            "validation_type": "content",
            "issues": issues,
            "raw_score": content_score,
            "content_details": self._get_content_details(output)
        }
    
    def get_score(self, validation_result: Dict[str, Any]) -> float:
        return validation_result.get("raw_score", 0.0)
    
    def _assess_content_quality(self, output: Any, context: Dict[str, Any]) -> float:
        """Assess content quality"""
        if isinstance(output, dict):
            return self._assess_dict_content(output, context)
        elif isinstance(output, str):
            return self._assess_text_content(output, context)
        return 0.5
    
    def _assess_dict_content(self, output: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Assess content quality of dictionary output"""
        scores = []
        
        # Check for meaningful data
        for key, value in output.items():
            if isinstance(value, str) and len(value.strip()) > 0:
                scores.append(self._assess_string_quality(value))
            elif isinstance(value, (int, float)):
                scores.append(0.8 if value is not None else 0.3)
            elif isinstance(value, list) and len(value) > 0:
                scores.append(0.7)
            else:
                scores.append(0.2)
        
        return statistics.mean(scores) if scores else 0.5
    
    def _assess_text_content(self, output: str, context: Dict[str, Any]) -> float:
        """Assess content quality of text output"""
        # Length check
        if len(output.strip()) < 10:
            return 0.2
        
        # Check for meaningful content
        has_keywords = any(keyword.lower() in output.lower() 
                          for keyword in context.get("expected_keywords", []))
        
        # Check for proper grammar indicators
        has_proper_ending = output.strip().endswith(('.', '!', '?'))
        
        # Check for repetitive content
        words = output.lower().split()
        unique_words = set(words)
        diversity_score = len(unique_words) / len(words) if words else 0
        
        score = 0.5  # Base score
        
        if has_keywords:
            score += 0.2
        
        if has_proper_ending:
            score += 0.1
        
        score += diversity_score * 0.2
        
        return min(1.0, score)
    
    def _assess_string_quality(self, text: str) -> float:
        """Assess quality of a string"""
        if not text or len(text.strip()) == 0:
            return 0.0
        
        # Check for meaningful content
        meaningful_words = sum(1 for word in text.split() if len(word) > 2)
        total_words = len(text.split())
        
        if total_words == 0:
            return 0.0
        
        return min(1.0, meaningful_words / total_words)
    
    def _get_content_details(self, output: Any) -> Dict[str, Any]:
        """Get detailed content information"""
        if isinstance(output, dict):
            return {
                "field_count": len(output),
                "non_empty_fields": len([v for v in output.values() if v is not None and v != ""]),
                "data_types": list(set(type(v).__name__ for v in output.values()))
            }
        elif isinstance(output, str):
            return {
                "character_count": len(output),
                "word_count": len(output.split()),
                "sentence_count": len(re.findall(r'[.!?]+', output)),
                "paragraph_count": len(output.split('\n\n'))
            }
        return {}


class CrossValidator(QualityValidator):
    """Validator for cross-validation between different methods"""
    
    def __init__(self, validators: List[QualityValidator]):
        self.validators = validators
    
    def validate(self, output: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform cross-validation"""
        validation_results = []
        
        for validator in self.validators:
            try:
                result = validator.validate(output, context)
                validation_results.append(result)
            except Exception as e:
                logger.warning(f"Cross-validation failed for {validator.__class__.__name__}: {str(e)}")
                validation_results.append({
                    "validation_type": "cross_validation_error",
                    "is_valid": False,
                    "issues": [f"Validator error: {str(e)}"],
                    "raw_score": 0.0
                })
        
        # Calculate consensus score
        individual_scores = [result["raw_score"] for result in validation_results]
        consensus_score = statistics.stdev(individual_scores) if len(individual_scores) > 1 else 0.0
        average_score = statistics.mean(individual_scores)
        
        # Lower standard deviation = higher consistency = higher cross-validation score
        cross_validation_score = max(0.0, 1.0 - consensus_score)
        
        is_valid = cross_validation_score >= context.get("cross_validation_threshold", 0.8)
        
        return {
            "cross_validation": cross_validation_score,
            "is_valid": is_valid,
            "validation_type": "cross_validation",
            "individual_scores": individual_scores,
            "consensus_score": consensus_score,
            "average_score": average_score,
            "raw_score": cross_validation_score,
            "validation_count": len(validation_results)
        }
    
    def get_score(self, validation_result: Dict[str, Any]) -> float:
        return validation_result.get("raw_score", 0.0)


class QualityAssessmentEngine:
    """Main quality assessment engine"""
    
    def __init__(self, config: QualityConfig):
        self.config = config
        self.validators = {}
        self.quality_history = []
        self._initialize_validators()
    
    def _initialize_validators(self):
        """Initialize quality validators"""
        self.validators = {
            ValidationType.CONFIDENCE_SCORE: ConfidenceValidator(),
            ValidationType.COMPLETENESS_CHECK: CompletenessValidator(),
            ValidationType.CONSISTENCY_CHECK: ConsistencyValidator(),
            ValidationType.FORMAT_VALIDATION: FormatValidator(),
            ValidationType.CONTENT_VALIDATION: ContentValidator(),
        }
        
        if self.config.enable_cross_validation:
            cross_validator = CrossValidator(list(self.validators.values()))
            self.validators[ValidationType.CROSS_VALIDATION] = cross_validator
    
    def assess_quality(self, output: Any, context: Dict[str, Any]) -> QualityMetrics:
        """Perform comprehensive quality assessment"""
        start_time = time.time()
        
        validation_results = {}
        total_score = 0.0
        issues = []
        recommendations = []
        
        # Run all validations
        for validation_type, validator in self.validators.items():
            try:
                result = validator.validate(output, context)
                validation_results[validation_type.value] = result
                
                # Add issues from this validation
                if not result["is_valid"]:
                    issues.extend(result.get("issues", []))
                
            except Exception as e:
                logger.error(f"Validation failed for {validation_type.value}: {str(e)}")
                validation_results[validation_type.value] = {
                    "is_valid": False,
                    "issues": [f"Validation error: {str(e)}"],
                    "raw_score": 0.0
                }
                issues.append(f"Validation error for {validation_type.value}")
        
        # Calculate weighted overall score
        scores = {}
        total_weight = 0.0
        
        scores["confidence_score"] = validation_results.get("confidence_score", {}).get("raw_score", 0.0)
        scores["completeness_score"] = validation_results.get("completeness_check", {}).get("raw_score", 0.0)
        scores["consistency_score"] = validation_results.get("consistency_check", {}).get("raw_score", 0.0)
        scores["format_score"] = validation_results.get("format_validation", {}).get("raw_score", 0.0)
        scores["content_score"] = validation_results.get("content_validation", {}).get("raw_score", 0.0)
        
        total_score = (
            scores["confidence_score"] * self.config.confidence_weight +
            scores["completeness_score"] * self.config.completeness_weight +
            scores["consistency_score"] * self.config.consistency_weight +
            scores["format_score"] * self.config.format_weight +
            scores["content_score"] * self.config.content_weight
        )
        
        # Determine quality level
        quality_level = self._determine_quality_level(total_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(validation_results, scores)
        
        # Create quality metrics
        metrics = QualityMetrics(
            overall_score=total_score,
            confidence_score=scores["confidence_score"],
            completeness_score=scores["completeness_score"],
            consistency_score=scores["consistency_score"],
            format_score=scores["format_score"],
            content_score=scores["content_score"],
            quality_level=quality_level,
            validation_details=validation_results,
            timestamp=time.time(),
            issues=issues,
            recommendations=recommendations
        )
        
        # Store in history
        self.quality_history.append(metrics)
        
        processing_time = time.time() - start_time
        logger.info(f"Quality assessment completed in {processing_time:.2f}s, score: {total_score:.3f}")
        
        return metrics
    
    def should_reject_output(self, metrics: QualityMetrics) -> Tuple[bool, str]:
        """Determine if output should be rejected based on quality"""
        
        # Check overall threshold
        if metrics.overall_score < self.config.auto_reject_threshold:
            return True, f"Overall quality below threshold: {metrics.overall_score:.2f} < {self.config.auto_reject_threshold}"
        
        # Check critical criteria
        for criterion in self.config.auto_reject_criteria:
            if criterion == "very_low_confidence" and metrics.confidence_score < 0.3:
                return True, f"Very low confidence: {metrics.confidence_score:.2f}"
            
            if criterion == "incomplete_output" and metrics.completeness_score < 0.2:
                return True, f"Incomplete output: {metrics.completeness_score:.2f}"
            
            if criterion == "format_violation" and metrics.format_score < 0.3:
                return True, f"Format violation: {metrics.format_score:.2f}"
        
        # Check for multiple critical issues
        critical_issues = [issue for issue in metrics.issues if any(word in issue.lower() for word in ["critical", "error", "invalid"])]
        if len(critical_issues) >= 3:
            return True, f"Multiple critical issues: {len(critical_issues)}"
        
        return False, ""
    
    def _determine_quality_level(self, overall_score: float) -> QualityLevel:
        """Determine quality level based on overall score"""
        if overall_score >= 0.9:
            return QualityLevel.EXCELLENT
        elif overall_score >= 0.7:
            return QualityLevel.GOOD
        elif overall_score >= 0.5:
            return QualityLevel.ACCEPTABLE
        elif overall_score >= 0.3:
            return QualityLevel.POOR
        else:
            return QualityLevel.UNACCEPTABLE
    
    def _generate_recommendations(self, validation_results: Dict[str, Any], scores: Dict[str, float]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if scores["confidence_score"] < 0.5:
            recommendations.append("Consider reprocessing with higher quality input or different model parameters")
        
        if scores["completeness_score"] < 0.5:
            recommendations.append("Output appears incomplete - consider checking input data or model constraints")
        
        if scores["consistency_score"] < 0.5:
            recommendations.append("Output contains inconsistencies - review for logical errors")
        
        if scores["format_score"] < 0.5:
            recommendations.append("Output format doesn't match expected structure")
        
        if scores["content_score"] < 0.5:
            recommendations.append("Content quality is low - consider improving input clarity or constraints")
        
        return recommendations
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get quality assessment statistics"""
        if not self.quality_history:
            return {"message": "No quality assessments performed"}
        
        recent_assessments = [m for m in self.quality_history if time.time() - m.timestamp < 3600]  # Last hour
        
        avg_scores = {
            "overall": statistics.mean([m.overall_score for m in recent_assessments]),
            "confidence": statistics.mean([m.confidence_score for m in recent_assessments]),
            "completeness": statistics.mean([m.completeness_score for m in recent_assessments]),
            "consistency": statistics.mean([m.consistency_score for m in recent_assessments]),
            "format": statistics.mean([m.format_score for m in recent_assessments]),
            "content": statistics.mean([m.content_score for m in recent_assessments])
        }
        
        quality_distribution = {}
        for level in QualityLevel:
            count = len([m for m in recent_assessments if m.quality_level == level])
            quality_distribution[level.value] = count
        
        rejection_rate = len([m for m in recent_assessments if self.should_reject_output(m)[0]]) / len(recent_assessments)
        
        return {
            "total_assessments": len(self.quality_history),
            "recent_assessments": len(recent_assessments),
            "average_scores": avg_scores,
            "quality_distribution": quality_distribution,
            "rejection_rate": rejection_rate,
            "config": self.config.__dict__
        }
    
    def reset_statistics(self):
        """Reset quality statistics"""
        self.quality_history.clear()
        logger.info("Quality statistics reset")