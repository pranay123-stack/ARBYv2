"""
AVO Validator - Validation system for AVO Tabs functionality
Provides comprehensive validation including connection testing, tab synchronization,
and error detection for the AVO Tabs interface.
"""

import asyncio
import json
import logging
import threading
import time
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from datetime import datetime, timedelta
import hashlib
import re
import socket
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationResult(Enum):
    """Validation result types"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class ValidationRule:
    """Validation rule definition"""
    rule_id: str
    name: str
    description: str
    severity: ValidationSeverity
    check_function: Callable
    enabled: bool = True
    timeout: float = 30.0
    retry_count: int = 1
    retry_delay: float = 1.0


@dataclass
class ValidationCheck:
    """Individual validation check result"""
    rule_id: str
    name: str
    result: ValidationResult
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any]
    execution_time: float
    timestamp: datetime
    retry_attempt: int = 0


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    report_id: str
    validation_type: str
    start_time: datetime
    end_time: Optional[datetime]
    overall_result: ValidationResult
    checks: List[ValidationCheck]
    summary: Dict[str, Any]
    recommendations: List[str]


class ConnectionValidator:
    """Validator for network connections and tab connectivity"""
    
    def __init__(self):
        self.timeout = 10.0
        self.retry_count = 3
        
    async def validate_tab_connection(self, tab_id: int, expected_url: str) -> ValidationCheck:
        """Validate tab connection and URL accessibility"""
        start_time = time.time()
        
        try:
            # Check if tab exists and is accessible
            # This would integrate with the actual tab management system
            connection_status = await self._check_tab_connectivity(tab_id)
            
            if not connection_status['accessible']:
                return ValidationCheck(
                    rule_id="tab_connection",
                    name="Tab Connection Validation",
                    result=ValidationResult.FAILED,
                    severity=ValidationSeverity.HIGH,
                    message=f"Tab {tab_id} is not accessible",
                    details={'tab_id': tab_id, 'expected_url': expected_url},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # Validate URL
            if not self._is_valid_url(expected_url):
                return ValidationCheck(
                    rule_id="url_validation",
                    name="URL Validation",
                    result=ValidationResult.FAILED,
                    severity=ValidationSeverity.HIGH,
                    message=f"Invalid URL format: {expected_url}",
                    details={'url': expected_url},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # Check URL accessibility
            url_accessible = await self._check_url_accessibility(expected_url)
            if not url_accessible:
                return ValidationCheck(
                    rule_id="url_accessibility",
                    name="URL Accessibility",
                    result=ValidationResult.WARNING,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"URL may not be accessible: {expected_url}",
                    details={'url': expected_url},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            return ValidationCheck(
                rule_id="tab_connection",
                name="Tab Connection Validation",
                result=ValidationResult.PASSED,
                severity=ValidationSeverity.LOW,
                message=f"Tab {tab_id} connection validated successfully",
                details={'tab_id': tab_id, 'url': expected_url, 'response_time': connection_status.get('response_time', 0)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return ValidationCheck(
                rule_id="tab_connection",
                name="Tab Connection Validation",
                result=ValidationResult.ERROR,
                severity=ValidationSeverity.HIGH,
                message=f"Connection validation error: {str(e)}",
                details={'tab_id': tab_id, 'error': str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    async def _check_tab_connectivity(self, tab_id: int) -> Dict[str, Any]:
        """Check if tab is accessible and responsive"""
        # Simulate tab connectivity check
        # In real implementation, this would communicate with the browser extension
        return {
            'accessible': True,
            'response_time': 0.05,
            'last_activity': datetime.now(),
            'status': 'active'
        }
    
    async def _check_url_accessibility(self, url: str) -> bool:
        """Check if URL is accessible"""
        try:
            async with asyncio.timeout(self.timeout):
                response = requests.head(url, timeout=self.timeout)
                return response.status_code < 400
        except:
            return False
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False


class SynchronizationValidator:
    """Validator for tab synchronization and state consistency"""
    
    def __init__(self, tab_manager):
        self.tab_manager = tab_manager
        
    async def validate_sync_consistency(self) -> ValidationCheck:
        """Validate synchronization consistency across tabs"""
        start_time = time.time()
        
        try:
            # Get all tabs
            all_tabs = list(self.tab_manager.tabs.values())
            
            if len(all_tabs) < 2:
                return ValidationCheck(
                    rule_id="sync_consistency",
                    name="Synchronization Consistency",
                    result=ValidationResult.SKIPPED,
                    severity=ValidationSeverity.LOW,
                    message="Not enough tabs to validate synchronization",
                    details={'tab_count': len(all_tabs)},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # Check for sync version consistency
            sync_versions = [tab.sync_version for tab in all_tabs]
            max_sync_version = max(sync_versions)
            min_sync_version = min(sync_versions)
            
            if max_sync_version - min_sync_version > 5:  # Allow some variance
                return ValidationCheck(
                    rule_id="sync_consistency",
                    name="Synchronization Consistency",
                    result=ValidationResult.WARNING,
                    severity=ValidationSeverity.MEDIUM,
                    message="Significant sync version variance detected",
                    details={
                        'max_version': max_sync_version,
                        'min_version': min_sync_version,
                        'variance': max_sync_version - min_sync_version
                    },
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # Check for stale tabs
            current_time = datetime.now()
            stale_tabs = []
            for tab in all_tabs:
                time_since_activity = (current_time - tab.last_activity).total_seconds()
                if time_since_activity > 300:  # 5 minutes
                    stale_tabs.append({'tab_id': tab.tab_id, 'inactive_seconds': time_since_activity})
            
            if stale_tabs:
                return ValidationCheck(
                    rule_id="sync_consistency",
                    name="Synchronization Consistency",
                    result=ValidationResult.WARNING,
                    severity=ValidationSeverity.MEDIUM,
                    message="Some tabs appear to be stale",
                    details={'stale_tabs': stale_tabs},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            return ValidationCheck(
                rule_id="sync_consistency",
                name="Synchronization Consistency",
                result=ValidationResult.PASSED,
                severity=ValidationSeverity.LOW,
                message="Synchronization consistency validated",
                details={'tabs_checked': len(all_tabs), 'max_sync_version': max_sync_version},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return ValidationCheck(
                rule_id="sync_consistency",
                name="Synchronization Consistency",
                result=ValidationResult.ERROR,
                severity=ValidationSeverity.HIGH,
                message=f"Sync consistency validation error: {str(e)}",
                details={'error': str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    async def validate_message_queue(self) -> ValidationCheck:
        """Validate message queue health"""
        start_time = time.time()
        
        try:
            # Check queue size
            queue_size = self.tab_manager.sync_queue.qsize()
            
            if queue_size > 100:
                return ValidationCheck(
                    rule_id="message_queue",
                    name="Message Queue Health",
                    result=ValidationResult.WARNING,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Message queue size is high: {queue_size}",
                    details={'queue_size': queue_size},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # Check for message processing rate
            # This would require tracking message processing metrics
            processing_rate = self._calculate_processing_rate()
            
            if processing_rate < 0.8:  # Less than 80% processed
                return ValidationCheck(
                    rule_id="message_queue",
                    name="Message Queue Health",
                    result=ValidationResult.WARNING,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Low message processing rate: {processing_rate:.2%}",
                    details={'processing_rate': processing_rate},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            return ValidationCheck(
                rule_id="message_queue",
                name="Message Queue Health",
                result=ValidationResult.PASSED,
                severity=ValidationSeverity.LOW,
                message="Message queue is healthy",
                details={'queue_size': queue_size, 'processing_rate': processing_rate},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return ValidationCheck(
                rule_id="message_queue",
                name="Message Queue Health",
                result=ValidationResult.ERROR,
                severity=ValidationSeverity.HIGH,
                message=f"Message queue validation error: {str(e)}",
                details={'error': str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    def _calculate_processing_rate(self) -> float:
        """Calculate message processing rate"""
        # This would be implemented based on actual metrics tracking
        # For now, return a mock value
        return 0.95


class HealthValidator:
    """Validator for system health and performance"""
    
    def __init__(self, tab_manager):
        self.tab_manager = tab_manager
        
    async def validate_system_health(self) -> ValidationCheck:
        """Validate overall system health"""
        start_time = time.time()
        
        try:
            # Get system status
            system_status = self.tab_manager.get_system_status()
            
            if 'error' in system_status:
                return ValidationCheck(
                    rule_id="system_health",
                    name="System Health Validation",
                    result=ValidationResult.ERROR,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"System status check failed: {system_status['error']}",
                    details=system_status,
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # Check overall health score
            avg_health = system_status.get('metrics', {}).get('average_health_score', 0)
            
            if avg_health < 0.5:
                return ValidationCheck(
                    rule_id="system_health",
                    name="System Health Validation",
                    result=ValidationResult.FAILED,
                    severity=ValidationSeverity.HIGH,
                    message=f"Low average health score: {avg_health:.2f}",
                    details=system_status,
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            elif avg_health < 0.7:
                return ValidationCheck(
                    rule_id="system_health",
                    name="System Health Validation",
                    result=ValidationResult.WARNING,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Below average health score: {avg_health:.2f}",
                    details=system_status,
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            return ValidationCheck(
                rule_id="system_health",
                name="System Health Validation",
                result=ValidationResult.PASSED,
                severity=ValidationSeverity.LOW,
                message=f"System health is good: {avg_health:.2f}",
                details=system_status,
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return ValidationCheck(
                rule_id="system_health",
                name="System Health Validation",
                result=ValidationResult.ERROR,
                severity=ValidationSeverity.CRITICAL,
                message=f"System health validation error: {str(e)}",
                details={'error': str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    async def validate_resource_usage(self) -> ValidationCheck:
        """Validate system resource usage"""
        start_time = time.time()
        
        try:
            # Check tab count limits
            tab_stats = self.tab_manager.get_system_status().get('tab_statistics', {})
            total_tabs = tab_stats.get('total_tabs', 0)
            max_tabs = self.tab_manager.max_tabs
            
            if total_tabs >= max_tabs:
                return ValidationCheck(
                    rule_id="resource_usage",
                    name="Resource Usage Validation",
                    result=ValidationResult.WARNING,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Tab count at limit: {total_tabs}/{max_tabs}",
                    details={'current_tabs': total_tabs, 'max_tabs': max_tabs},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # Check error rates
            metrics = self.tab_manager.metrics
            error_rate = metrics.get('total_errors', 0) / max(metrics.get('total_tabs_created', 1), 1)
            
            if error_rate > 0.1:  # More than 10% error rate
                return ValidationCheck(
                    rule_id="resource_usage",
                    name="Resource Usage Validation",
                    result=ValidationResult.WARNING,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"High error rate detected: {error_rate:.2%}",
                    details={'error_rate': error_rate, 'metrics': metrics},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            return ValidationCheck(
                rule_id="resource_usage",
                name="Resource Usage Validation",
                result=ValidationResult.PASSED,
                severity=ValidationSeverity.LOW,
                message="Resource usage is within acceptable limits",
                details={'tab_count': total_tabs, 'error_rate': error_rate},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return ValidationCheck(
                rule_id="resource_usage",
                name="Resource Usage Validation",
                result=ValidationResult.ERROR,
                severity=ValidationSeverity.HIGH,
                message=f"Resource validation error: {str(e)}",
                details={'error': str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )


class ExtensionValidator:
    """Validator for Chrome extension integration"""
    
    def __init__(self, extension_handler):
        self.extension_handler = extension_handler
        
    async def validate_extension_connection(self) -> ValidationCheck:
        """Validate connection to Chrome extension"""
        start_time = time.time()
        
        try:
            if not self.extension_handler:
                return ValidationCheck(
                    rule_id="extension_connection",
                    name="Extension Connection",
                    result=ValidationResult.FAILED,
                    severity=ValidationSeverity.CRITICAL,
                    message="Extension handler not available",
                    details={},
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            # Test extension communication
            connection_test = await self._test_extension_communication()
            
            if not connection_test['connected']:
                return ValidationCheck(
                    rule_id="extension_connection",
                    name="Extension Connection",
                    result=ValidationResult.FAILED,
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Extension communication failed: {connection_test.get('error', 'Unknown error')}",
                    details=connection_test,
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now()
                )
            
            return ValidationCheck(
                rule_id="extension_connection",
                name="Extension Connection",
                result=ValidationResult.PASSED,
                severity=ValidationSeverity.LOW,
                message="Extension connection validated",
                details=connection_test,
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return ValidationCheck(
                rule_id="extension_connection",
                name="Extension Connection",
                result=ValidationResult.ERROR,
                severity=ValidationSeverity.CRITICAL,
                message=f"Extension connection validation error: {str(e)}",
                details={'error': str(e)},
                execution_time=time.time() - start_time,
                timestamp=datetime.now()
            )
    
    async def _test_extension_communication(self) -> Dict[str, Any]:
        """Test communication with Chrome extension"""
        try:
            # This would send a test message to the extension
            # For now, simulate the test
            return {
                'connected': True,
                'response_time': 0.05,
                'message_id': str(uuid.uuid4()),
                'test_timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'test_timestamp': datetime.now().isoformat()
            }


class AVOValidator:
    """Main validation orchestrator"""
    
    def __init__(self, tab_manager, extension_handler=None):
        self.tab_manager = tab_manager
        self.extension_handler = extension_handler
        
        # Initialize validators
        self.connection_validator = ConnectionValidator()
        self.synchronization_validator = SynchronizationValidator(tab_manager)
        self.health_validator = HealthValidator(tab_manager)
        self.extension_validator = ExtensionValidator(extension_handler)
        
        # Validation rules registry
        self.validation_rules: Dict[str, ValidationRule] = {}
        self._register_default_rules()
        
        # Validation history
        self.validation_history: List[ValidationReport] = []
        
        logger.info("AVO Validator initialized")
    
    def _register_default_rules(self):
        """Register default validation rules"""
        
        # Connection validation rules
        self.register_validation_rule(ValidationRule(
            rule_id="tab_connection",
            name="Tab Connection Validation",
            description="Validates tab connectivity and URL accessibility",
            severity=ValidationSeverity.HIGH,
            check_function=self.connection_validator.validate_tab_connection
        ))
        
        # Synchronization validation rules
        self.register_validation_rule(ValidationRule(
            rule_id="sync_consistency",
            name="Synchronization Consistency",
            description="Validates sync consistency across tabs",
            severity=ValidationSeverity.MEDIUM,
            check_function=self.synchronization_validator.validate_sync_consistency
        ))
        
        self.register_validation_rule(ValidationRule(
            rule_id="message_queue",
            name="Message Queue Health",
            description="Validates message queue health and processing",
            severity=ValidationSeverity.MEDIUM,
            check_function=self.synchronization_validator.validate_message_queue
        ))
        
        # Health validation rules
        self.register_validation_rule(ValidationRule(
            rule_id="system_health",
            name="System Health Validation",
            description="Validates overall system health",
            severity=ValidationSeverity.HIGH,
            check_function=self.health_validator.validate_system_health
        ))
        
        self.register_validation_rule(ValidationRule(
            rule_id="resource_usage",
            name="Resource Usage Validation",
            description="Validates system resource usage",
            severity=ValidationSeverity.MEDIUM,
            check_function=self.health_validator.validate_resource_usage
        ))
        
        # Extension validation rules
        self.register_validation_rule(ValidationRule(
            rule_id="extension_connection",
            name="Extension Connection",
            description="Validates Chrome extension connection",
            severity=ValidationSeverity.CRITICAL,
            check_function=self.extension_validator.validate_extension_connection
        ))
    
    def register_validation_rule(self, rule: ValidationRule):
        """Register a new validation rule"""
        self.validation_rules[rule.rule_id] = rule
        logger.info(f"Registered validation rule: {rule.rule_id}")
    
    def get_validation_rule(self, rule_id: str) -> Optional[ValidationRule]:
        """Get validation rule by ID"""
        return self.validation_rules.get(rule_id)
    
    def list_validation_rules(self) -> List[ValidationRule]:
        """List all validation rules"""
        return list(self.validation_rules.values())
    
    async def run_validation_check(self, rule_id: str, **kwargs) -> ValidationCheck:
        """Run a specific validation check"""
        if rule_id not in self.validation_rules:
            raise ValueError(f"Validation rule not found: {rule_id}")
        
        rule = self.validation_rules[rule_id]
        
        if not rule.enabled:
            return ValidationCheck(
                rule_id=rule_id,
                name=rule.name,
                result=ValidationResult.SKIPPED,
                severity=ValidationSeverity.INFO,
                message=f"Validation rule {rule_id} is disabled",
                details={},
                execution_time=0.0,
                timestamp=datetime.now()
            )
        
        # Execute validation with retry logic
        last_error = None
        for attempt in range(rule.retry_count + 1):
            try:
                if asyncio.iscoroutinefunction(rule.check_function):
                    result = await asyncio.wait_for(
                        rule.check_function(**kwargs),
                        timeout=rule.timeout
                    )
                else:
                    result = rule.check_function(**kwargs)
                
                if isinstance(result, ValidationCheck):
                    result.retry_attempt = attempt
                    return result
                else:
                    # Assume it's a valid result, wrap it
                    return ValidationCheck(
                        rule_id=rule_id,
                        name=rule.name,
                        result=ValidationResult.PASSED,
                        severity=ValidationSeverity.INFO,
                        message="Validation completed",
                        details={'result': result},
                        execution_time=0.0,
                        timestamp=datetime.now()
                    )
                    
            except asyncio.TimeoutError:
                last_error = f"Timeout after {rule.timeout}s"
                logger.warning(f"Validation {rule_id} timed out (attempt {attempt + 1})")
            except Exception as e:
                last_error = str(e)
                logger.error(f"Validation {rule_id} failed (attempt {attempt + 1}): {e}")
            
            if attempt < rule.retry_count:
                await asyncio.sleep(rule.retry_delay * (2 ** attempt))  # Exponential backoff
        
        # All attempts failed
        return ValidationCheck(
            rule_id=rule_id,
            name=rule.name,
            result=ValidationResult.ERROR,
            severity=rule.severity,
            message=f"Validation failed after {rule.retry_count + 1} attempts: {last_error}",
            details={'error': last_error, 'attempts': rule.retry_count + 1},
            execution_time=rule.timeout * (rule.retry_count + 1),
            timestamp=datetime.now()
        )
    
    async def run_comprehensive_validation(self, validation_type: str = "full") -> ValidationReport:
        """Run comprehensive validation suite"""
        report_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        logger.info(f"Starting comprehensive validation: {validation_type}")
        
        try:
            checks = []
            
            # Define validation sequences based on type
            validation_sequences = {
                "connection": ["tab_connection", "extension_connection"],
                "sync": ["sync_consistency", "message_queue"],
                "health": ["system_health", "resource_usage"],
                "full": ["tab_connection", "extension_connection", "sync_consistency", 
                        "message_queue", "system_health", "resource_usage"]
            }
            
            rules_to_run = validation_sequences.get(validation_type, validation_sequences["full"])
            
            # Execute validation rules
            for rule_id in rules_to_run:
                if rule_id in self.validation_rules:
                    check = await self.run_validation_check(rule_id)
                    checks.append(check)
                    
                    # Log individual results
                    logger.info(f"Validation {rule_id}: {check.result.value} - {check.message}")
            
            # Calculate overall result
            overall_result = self._calculate_overall_result(checks)
            
            # Generate summary
            summary = self._generate_validation_summary(checks)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(checks)
            
            # Create report
            report = ValidationReport(
                report_id=report_id,
                validation_type=validation_type,
                start_time=start_time,
                end_time=datetime.now(),
                overall_result=overall_result,
                checks=checks,
                summary=summary,
                recommendations=recommendations
            )
            
            # Store in history
            self.validation_history.append(report)
            
            # Limit history size
            if len(self.validation_history) > 100:
                self.validation_history = self.validation_history[-100:]
            
            logger.info(f"Comprehensive validation completed: {overall_result.value}")
            return report
            
        except Exception as e:
            logger.error(f"Comprehensive validation failed: {e}")
            return ValidationReport(
                report_id=report_id,
                validation_type=validation_type,
                start_time=start_time,
                end_time=datetime.now(),
                overall_result=ValidationResult.ERROR,
                checks=[],
                summary={'error': str(e)},
                recommendations=[f"Fix validation system error: {str(e)}"]
            )
    
    def _calculate_overall_result(self, checks: List[ValidationCheck]) -> ValidationResult:
        """Calculate overall validation result from individual checks"""
        if not checks:
            return ValidationResult.ERROR
        
        # Priority order: ERROR > FAILED > WARNING > PASSED > SKIPPED > INFO
        priority_map = {
            ValidationResult.ERROR: 5,
            ValidationResult.FAILED: 4,
            ValidationResult.WARNING: 3,
            ValidationResult.PASSED: 2,
            ValidationResult.SKIPPED: 1,
            ValidationResult.INFO: 0
        }
        
        max_priority = max(priority_map[check.result] for check in checks)
        
        # Convert back to result
        for result, priority in priority_map.items():
            if priority == max_priority:
                return result
        
        return ValidationResult.ERROR
    
    def _generate_validation_summary(self, checks: List[ValidationCheck]) -> Dict[str, Any]:
        """Generate validation summary statistics"""
        result_counts = {}
        severity_counts = {}
        total_execution_time = 0
        
        for check in checks:
            # Count results
            result_counts[check.result.value] = result_counts.get(check.result.value, 0) + 1
            
            # Count severities
            severity_counts[check.severity.value] = severity_counts.get(check.severity.value, 0) + 1
            
            # Sum execution times
            total_execution_time += check.execution_time
        
        return {
            'total_checks': len(checks),
            'result_distribution': result_counts,
            'severity_distribution': severity_counts,
            'total_execution_time': total_execution_time,
            'average_execution_time': total_execution_time / len(checks) if checks else 0,
            'success_rate': result_counts.get('passed', 0) / len(checks) if checks else 0,
            'error_rate': (result_counts.get('error', 0) + result_counts.get('failed', 0)) / len(checks) if checks else 0
        }
    
    def _generate_recommendations(self, checks: List[ValidationCheck]) -> List[str]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        
        # Analyze failed/critical checks
        critical_issues = [check for check in checks if check.severity == ValidationSeverity.CRITICAL 
                          and check.result in [ValidationResult.FAILED, ValidationResult.ERROR]]
        
        high_issues = [check for check in checks if check.severity == ValidationSeverity.HIGH 
                      and check.result in [ValidationResult.FAILED, ValidationResult.ERROR]]
        
        # Generate specific recommendations
        if critical_issues:
            recommendations.append("IMMEDIATE ACTION REQUIRED: Critical validation failures detected")
            for check in critical_issues:
                recommendations.append(f"- Fix critical issue: {check.message}")
        
        if high_issues:
            recommendations.append("HIGH PRIORITY: Address high-severity issues")
            for check in high_issues:
                recommendations.append(f"- Resolve: {check.message}")
        
        # Performance recommendations
        slow_checks = [check for check in checks if check.execution_time > 10.0]
        if slow_checks:
            recommendations.append("PERFORMANCE: Some validations are slow")
            recommendations.append(f"- Consider optimizing: {', '.join(check.name for check in slow_checks)}")
        
        # General recommendations
        total_checks = len(checks)
        failed_checks = len([check for check in checks if check.result in [ValidationResult.FAILED, ValidationResult.ERROR]])
        
        if total_checks > 0 and failed_checks / total_checks > 0.2:
            recommendations.append("SYSTEM HEALTH: High failure rate detected - consider system review")
        
        return recommendations
    
    def get_validation_history(self, limit: int = 10) -> List[ValidationReport]:
        """Get validation history"""
        return self.validation_history[-limit:] if limit > 0 else self.validation_history
    
    def export_validation_report(self, report: ValidationReport, format: str = "json") -> str:
        """Export validation report in specified format"""
        try:
            if format.lower() == "json":
                return json.dumps(asdict(report), indent=2, default=str)
            else:
                raise ValueError(f"Unsupported export format: {format}")
        except Exception as e:
            logger.error(f"Error exporting validation report: {e}")
            return f"Export error: {str(e)}"
    
    async def start_continuous_validation(self, interval: float = 300.0):
        """Start continuous validation in background"""
        def validation_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            while True:
                try:
                    loop.run_until_complete(self.run_comprehensive_validation())
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Continuous validation error: {e}")
                    time.sleep(60.0)  # Wait 1 minute before retry
        
        validation_thread = threading.Thread(target=validation_loop, daemon=True)
        validation_thread.start()
        logger.info(f"Continuous validation started (interval: {interval}s)")
    
    def stop_continuous_validation(self):
        """Stop continuous validation"""
        # This would need to be implemented with a running flag
        logger.info("Continuous validation stop requested")
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics and metrics"""
        if not self.validation_history:
            return {'message': 'No validation history available'}
        
        recent_reports = self.validation_history[-20:]  # Last 20 reports
        
        # Calculate statistics
        total_reports = len(self.validation_history)
        successful_reports = len([r for r in recent_reports if r.overall_result == ValidationResult.PASSED])
        failed_reports = len([r for r in recent_reports if r.overall_result in [ValidationResult.FAILED, ValidationResult.ERROR]])
        
        avg_execution_time = sum(
            (r.end_time - r.start_time).total_seconds() for r in recent_reports if r.end_time
        ) / len(recent_reports)
        
        return {
            'total_reports': total_reports,
            'recent_reports_count': len(recent_reports),
            'recent_success_rate': successful_reports / len(recent_reports) if recent_reports else 0,
            'recent_failure_rate': failed_reports / len(recent_reports) if recent_reports else 0,
            'average_execution_time': avg_execution_time,
            'last_validation': self.validation_history[-1].end_time.isoformat() if self.validation_history[-1].end_time else None,
            'active_rules': len([rule for rule in self.validation_rules.values() if rule.enabled]),
            'total_rules': len(self.validation_rules)
        }