"""
Safety Pipeline - Main Safety Validation Engine

This module orchestrates all safety checks and provides comprehensive
validation before any trade execution to ensure maximum safety and compliance.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json

from .pre_trade_validator import PreTradeValidator
from .compliance_checker import ComplianceChecker  
from .safety_monitor import SafetyMonitor


class RiskLevel(Enum):
    """Risk level enumeration"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    FORBIDDEN = "forbidden"


class ValidationStatus(Enum):
    """Validation status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    BLOCKED = "blocked"


@dataclass
class ValidationRule:
    """Individual validation rule configuration"""
    name: str
    enabled: bool = True
    priority: int = 100
    timeout_seconds: int = 30
    retry_attempts: int = 2
    description: str = ""
    
    def __post_init__(self):
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts cannot be negative")


@dataclass
class SafetyResult:
    """Result of safety validation process"""
    opportunity_id: str
    overall_status: ValidationStatus
    risk_level: RiskLevel
    timestamp: datetime = field(default_factory=datetime.utcnow)
    validation_duration: float = 0.0
    
    # Detailed validation results
    pre_trade_validation: Dict[str, Any] = field(default_factory=dict)
    compliance_validation: Dict[str, Any] = field(default_factory=dict)
    safety_monitoring: Dict[str, Any] = field(default_factory=dict)
    
    # Risk metrics
    risk_score: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    max_stake_recommended: float = 0.0
    confidence_level: float = 0.0
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)
    
    # Audit information
    validation_rules_checked: List[str] = field(default_factory=list)
    skipped_rules: List[str] = field(default_factory=list)
    failed_rules: List[str] = field(default_factory=list)


@dataclass
class SafetyConfig:
    """Comprehensive safety pipeline configuration"""
    # Global safety settings
    enable_all_checks: bool = True
    fail_fast: bool = False
    parallel_validation: bool = True
    cache_validation_results: bool = True
    
    # Risk thresholds
    max_risk_score: float = 75.0
    min_confidence_level: float = 80.0
    high_risk_threshold: float = 60.0
    critical_risk_threshold: float = 85.0
    
    # Timing constraints
    max_validation_time: float = 30.0  # seconds
    validation_timeout: float = 60.0   # seconds
    
    # Rate limiting
    max_validations_per_minute: int = 10
    validation_burst_limit: int = 3
    
    # Logging
    log_validation_details: bool = True
    log_performance_metrics: bool = True
    
    # Component configurations
    pre_trade_validator_config: Dict[str, Any] = field(default_factory=dict)
    compliance_checker_config: Dict[str, Any] = field(default_factory=dict)
    safety_monitor_config: Dict[str, Any] = field(default_factory=dict)


class SafetyPipeline:
    """
    Main Safety Validation Engine
    
    Orchestrates comprehensive multi-layer safety checks including:
    - Risk tier validation
    - Bankroll limits
    - Exposure limits  
    - Compliance checks
    - Pre-trade validation
    - Real-time monitoring
    """
    
    def __init__(self, config: Optional[SafetyConfig] = None):
        """
        Initialize the safety pipeline
        
        Args:
            config: Safety configuration. If None, uses default config.
        """
        self.config = config or SafetyConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize validation rules
        self._validation_rules = self._initialize_validation_rules()
        
        # Initialize validation components
        self._pre_trade_validator = PreTradeValidator(
            self.config.pre_trade_validator_config
        )
        self._compliance_checker = ComplianceChecker(
            self.config.compliance_checker_config
        )
        self._safety_monitor = SafetyMonitor(
            self.config.safety_monitor_config
        )
        
        # Performance tracking
        self._performance_metrics = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'average_validation_time': 0.0,
            'validation_rate_per_minute': 0.0
        }
        
        # Rate limiting
        self._validation_timestamps = []
        
        self.logger.info("Safety Pipeline initialized successfully")
    
    def _initialize_validation_rules(self) -> Dict[str, ValidationRule]:
        """Initialize all validation rules"""
        return {
            'pre_trade_basic': ValidationRule(
                name='pre_trade_basic',
                priority=1,
                description='Basic pre-trade validation checks'
            ),
            'pre_trade_advanced': ValidationRule(
                name='pre_trade_advanced',
                priority=2,
                description='Advanced pre-trade validation including risk assessment'
            ),
            'compliance_jurisdiction': ValidationRule(
                name='compliance_jurisdiction',
                priority=1,
                description='Jurisdiction-specific compliance validation'
            ),
            'compliance_responsible_gambling': ValidationRule(
                name='compliance_responsible_gambling',
                priority=1,
                description='Responsible gambling controls'
            ),
            'compliance_audit': ValidationRule(
                name='compliance_audit',
                priority=2,
                description='Audit requirements compliance'
            ),
            'safety_real_time': ValidationRule(
                name='safety_real_time',
                priority=1,
                description='Real-time safety monitoring'
            ),
            'safety_anomaly_detection': ValidationRule(
                name='safety_anomaly_detection',
                priority=2,
                description='Anomaly detection for unusual patterns'
            ),
            'safety_proactive_intervention': ValidationRule(
                name='safety_proactive_intervention',
                priority=1,
                description='Proactive intervention capabilities'
            )
        }
    
    async def validate_opportunity(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> SafetyResult:
        """
        Perform comprehensive safety validation for an opportunity
        
        Args:
            opportunity_data: Opportunity data to validate
            user_preferences: User-specific safety preferences
            
        Returns:
            SafetyResult: Comprehensive validation result
        """
        start_time = time.time()
        opportunity_id = opportunity_data.get('id', 'unknown')
        
        # Rate limiting check
        if not await self._check_rate_limit():
            return SafetyResult(
                opportunity_id=opportunity_id,
                overall_status=ValidationStatus.BLOCKED,
                risk_level=RiskLevel.CRITICAL,
                critical_issues=["Rate limit exceeded"]
            )
        
        self.logger.info(f"Starting safety validation for opportunity {opportunity_id}")
        
        # Initialize result
        result = SafetyResult(
            opportunity_id=opportunity_id,
            overall_status=ValidationStatus.IN_PROGRESS,
            risk_level=RiskLevel.VERY_LOW
        )
        
        try:
            # Sort validation rules by priority
            sorted_rules = sorted(
                self._validation_rules.items(),
                key=lambda x: x[1].priority
            )
            
            validation_failures = []
            
            if self.config.parallel_validation:
                # Run validations in parallel
                validation_results = await self._run_parallel_validations(
                    opportunity_data, user_preferences, sorted_rules
                )
            else:
                # Run validations sequentially
                validation_results = await self._run_sequential_validations(
                    opportunity_data, user_preferences, sorted_rules
                )
            
            # Process validation results
            for rule_name, rule_result in validation_results.items():
                result.validation_rules_checked.append(rule_name)
                
                if not rule_result['success']:
                    result.failed_rules.append(rule_name)
                    validation_failures.append(f"{rule_name}: {rule_result['error']}")
                    
                    if self.config.fail_fast:
                        break
                elif rule_result.get('warnings'):
                    result.warnings.extend(rule_result['warnings'])
            
            # Aggregate results and calculate risk score
            await self._aggregate_validation_results(
                result, validation_results, user_preferences
            )
            
            # Determine final status
            if validation_failures:
                result.overall_status = ValidationStatus.FAILED
                result.critical_issues = validation_failures
            elif result.warnings:
                result.overall_status = ValidationStatus.WARNING
            else:
                result.overall_status = ValidationStatus.PASSED
            
            # Performance metrics
            result.validation_duration = time.time() - start_time
            await self._update_performance_metrics(result.validation_duration)
            
            # Generate recommendations
            await self._generate_recommendations(result, validation_results)
            
            # Cache result if enabled
            if self.config.cache_validation_results:
                await self._cache_validation_result(opportunity_id, result)
            
            self.logger.info(
                f"Validation completed for {opportunity_id}: "
                f"status={result.overall_status.value}, "
                f"risk_level={result.risk_level.value}, "
                f"duration={result.validation_duration:.3f}s"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Validation error for {opportunity_id}: {str(e)}")
            return SafetyResult(
                opportunity_id=opportunity_id,
                overall_status=ValidationStatus.FAILED,
                risk_level=RiskLevel.CRITICAL,
                critical_issues=[f"Validation system error: {str(e)}"],
                validation_duration=time.time() - start_time
            )
    
    async def _run_parallel_validations(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]],
        sorted_rules: List[Tuple[str, ValidationRule]]
    ) -> Dict[str, Dict[str, Any]]:
        """Run validation rules in parallel"""
        tasks = []
        
        for rule_name, rule in sorted_rules:
            if not rule.enabled:
                continue
                
            task = asyncio.create_task(
                self._execute_validation_rule(rule_name, rule, opportunity_data, user_preferences)
            )
            tasks.append((rule_name, task))
        
        # Wait for all tasks to complete
        results = {}
        for rule_name, task in tasks:
            try:
                results[rule_name] = await task
            except Exception as e:
                self.logger.error(f"Validation rule {rule_name} failed: {str(e)}")
                results[rule_name] = {
                    'success': False,
                    'error': str(e),
                    'data': {}
                }
        
        return results
    
    async def _run_sequential_validations(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]],
        sorted_rules: List[Tuple[str, ValidationRule]]
    ) -> Dict[str, Dict[str, Any]]:
        """Run validation rules sequentially"""
        results = {}
        
        for rule_name, rule in sorted_rules:
            if not rule.enabled:
                self._log_skipped_rule(rule_name, "Rule disabled")
                continue
            
            try:
                start_time = time.time()
                result = await asyncio.wait_for(
                    self._execute_validation_rule(rule_name, rule, opportunity_data, user_preferences),
                    timeout=rule.timeout_seconds
                )
                
                duration = time.time() - start_time
                self.logger.debug(f"Rule {rule_name} completed in {duration:.3f}s")
                results[rule_name] = result
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Rule {rule_name} timed out")
                results[rule_name] = {
                    'success': False,
                    'error': 'Timeout',
                    'data': {}
                }
            except Exception as e:
                self.logger.error(f"Rule {rule_name} failed: {str(e)}")
                results[rule_name] = {
                    'success': False,
                    'error': str(e),
                    'data': {}
                }
        
        return results
    
    async def _execute_validation_rule(
        self,
        rule_name: str,
        rule: ValidationRule,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a specific validation rule"""
        self.logger.debug(f"Executing validation rule: {rule_name}")
        
        try:
            if rule_name.startswith('pre_trade'):
                # Pre-trade validation rules
                if 'basic' in rule_name:
                    result = await self._pre_trade_validator.validate_basic_checks(
                        opportunity_data, user_preferences
                    )
                elif 'advanced' in rule_name:
                    result = await self._pre_trade_validator.validate_advanced_checks(
                        opportunity_data, user_preferences
                    )
                else:
                    result = {'success': True, 'data': {}}
                    
            elif rule_name.startswith('compliance'):
                # Compliance validation rules
                if 'jurisdiction' in rule_name:
                    result = await self._compliance_checker.validate_jurisdiction(
                        opportunity_data, user_preferences
                    )
                elif 'responsible_gambling' in rule_name:
                    result = await self._compliance_checker.validate_responsible_gambling(
                        opportunity_data, user_preferences
                    )
                elif 'audit' in rule_name:
                    result = await self._compliance_checker.validate_audit_requirements(
                        opportunity_data, user_preferences
                    )
                else:
                    result = {'success': True, 'data': {}}
                    
            elif rule_name.startswith('safety'):
                # Safety monitoring rules
                if 'real_time' in rule_name:
                    result = await self._safety_monitor.check_real_time_safety(
                        opportunity_data, user_preferences
                    )
                elif 'anomaly_detection' in rule_name:
                    result = await self._safety_monitor.detect_anomalies(
                        opportunity_data, user_preferences
                    )
                elif 'proactive_intervention' in rule_name:
                    result = await self._safety_monitor.check_proactive_intervention(
                        opportunity_data, user_preferences
                    )
                else:
                    result = {'success': True, 'data': {}}
            else:
                result = {'success': True, 'data': {}}
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }
    
    async def _aggregate_validation_results(
        self,
        result: SafetyResult,
        validation_results: Dict[str, Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]]
    ):
        """Aggregate and analyze validation results"""
        
        # Collect all validation data
        pre_trade_data = {}
        compliance_data = {}
        safety_data = {}
        
        for rule_name, rule_result in validation_results.items():
            if not rule_result['success']:
                result.risk_factors.append(f"Failed validation: {rule_name}")
                continue
                
            rule_data = rule_result.get('data', {})
            
            if rule_name.startswith('pre_trade'):
                pre_trade_data.update(rule_data)
            elif rule_name.startswith('compliance'):
                compliance_data.update(rule_data)
            elif rule_name.startswith('safety'):
                safety_data.update(rule_data)
        
        # Store aggregated data
        result.pre_trade_validation = pre_trade_data
        result.compliance_validation = compliance_data
        result.safety_monitoring = safety_data
        
        # Calculate risk score
        await self._calculate_risk_score(result, pre_trade_data, compliance_data, safety_data)
        
        # Determine risk level
        if result.risk_score >= self.config.critical_risk_threshold:
            result.risk_level = RiskLevel.CRITICAL
        elif result.risk_score >= self.config.high_risk_threshold:
            result.risk_level = RiskLevel.HIGH
        elif result.risk_score >= 40.0:
            result.risk_level = RiskLevel.MEDIUM
        elif result.risk_score >= 20.0:
            result.risk_level = RiskLevel.LOW
        else:
            result.risk_level = RiskLevel.VERY_LOW
        
        # Calculate confidence level
        total_checks = len(self._validation_rules)
        failed_checks = len(result.failed_rules)
        result.confidence_level = max(0, 100 * (1 - failed_checks / max(total_checks, 1)))
    
    async def _calculate_risk_score(
        self,
        result: SafetyResult,
        pre_trade_data: Dict[str, Any],
        compliance_data: Dict[str, Any],
        safety_data: Dict[str, Any]
    ):
        """Calculate comprehensive risk score"""
        
        base_score = 0.0
        
        # Pre-trade risk factors
        if pre_trade_data.get('exceeds_limits', False):
            base_score += 25.0
        if pre_trade_data.get('high_volatility', False):
            base_score += 15.0
        if pre_trade_data.get('low_liquidity', False):
            base_score += 20.0
        
        # Compliance risk factors
        if compliance_data.get('jurisdiction_risk', False):
            base_score += 30.0
        if compliance_data.get('regulatory_concerns', False):
            base_score += 20.0
        
        # Safety risk factors
        if safety_data.get('anomaly_detected', False):
            base_score += 25.0
        if safety_data.get('unusual_pattern', False):
            base_score += 15.0
        if safety_data.get('requires_intervention', False):
            base_score += 35.0
        
        # Apply confidence adjustment
        confidence_penalty = max(0, (100 - result.confidence_level) * 0.2)
        base_score += confidence_penalty
        
        result.risk_score = min(100.0, max(0.0, base_score))
    
    async def _generate_recommendations(
        self,
        result: SafetyResult,
        validation_results: Dict[str, Dict[str, Any]]
    ):
        """Generate detailed safety recommendations"""
        
        # Risk-based recommendations
        if result.risk_score >= 75.0:
            result.recommendations.append(
                "HIGH RISK: Consider reducing stake size or skipping this opportunity"
            )
        
        if result.risk_score >= 50.0:
            result.recommendations.append(
                "Increase monitoring frequency for this trade"
            )
        
        # Compliance recommendations
        if result.compliance_validation.get('jurisdiction_risk'):
            result.recommendations.append(
                "Verify local gambling regulations before proceeding"
            )
        
        if result.compliance_validation.get('audit_required'):
            result.recommendations.append(
                "Ensure all audit requirements are met"
            )
        
        # Safety recommendations
        if result.safety_monitoring.get('anomaly_detected'):
            result.recommendations.append(
                "Investigate detected anomalies before proceeding"
            )
        
        # Stake size recommendations
        if result.max_stake_recommended > 0:
            result.recommendations.append(
                f"Recommended maximum stake: {result.max_stake_recommended:.2f}"
            )
        
        # Confidence-based recommendations
        if result.confidence_level < 80.0:
            result.recommendations.append(
                "Low confidence level - consider additional verification"
            )
    
    async def _check_rate_limit(self) -> bool:
        """Check if validation rate limit is exceeded"""
        now = time.time()
        
        # Remove old timestamps (older than 1 minute)
        self._validation_timestamps = [
            ts for ts in self._validation_timestamps if now - ts < 60
        ]
        
        # Check rate limits
        if len(self._validation_timestamps) >= self.config.max_validations_per_minute:
            return False
        
        # Check burst limit
        recent_timestamps = [ts for ts in self._validation_timestamps if now - ts < 10]
        if len(recent_timestamps) >= self.config.validation_burst_limit:
            return False
        
        # Add current timestamp
        self._validation_timestamps.append(now)
        return True
    
    async def _cache_validation_result(
        self,
        opportunity_id: str,
        result: SafetyResult
    ):
        """Cache validation result for future reference"""
        # This would typically use Redis or similar caching system
        # For now, just log that caching would occur
        self.logger.debug(f"Would cache validation result for {opportunity_id}")
    
    def _log_skipped_rule(self, rule_name: str, reason: str):
        """Log skipped validation rule"""
        self.logger.debug(f"Skipping validation rule {rule_name}: {reason}")
    
    async def _update_performance_metrics(self, duration: float):
        """Update performance metrics"""
        self._performance_metrics['total_validations'] += 1
        
        if duration <= 10.0:  # Consider "successful" if under 10 seconds
            self._performance_metrics['successful_validations'] += 1
        else:
            self._performance_metrics['failed_validations'] += 1
        
        # Update average validation time
        total = self._performance_metrics['total_validations']
        current_avg = self._performance_metrics['average_validation_time']
        self._performance_metrics['average_validation_time'] = (
            (current_avg * (total - 1) + duration) / total
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self._performance_metrics.copy()
    
    def get_validation_rules(self) -> Dict[str, ValidationRule]:
        """Get all configured validation rules"""
        return self._validation_rules.copy()
    
    def update_validation_rule(
        self,
        rule_name: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a specific validation rule"""
        if rule_name not in self._validation_rules:
            return False
        
        rule = self._validation_rules[rule_name]
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
            else:
                self.logger.warning(f"Unknown rule attribute: {key}")
                return False
        
        self.logger.info(f"Updated validation rule: {rule_name}")
        return True
    
    async def get_safety_report(
        self,
        time_period_hours: int = 24
    ) -> Dict[str, Any]:
        """Generate comprehensive safety report"""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_period_hours)
        
        report = {
            'report_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_hours': time_period_hours
            },
            'performance_metrics': self._performance_metrics,
            'configuration': {
                'validation_rules': len(self._validation_rules),
                'parallel_validation': self.config.parallel_validation,
                'fail_fast': self.config.fail_fast,
                'rate_limits': {
                    'max_per_minute': self.config.max_validations_per_minute,
                    'burst_limit': self.config.validation_burst_limit
                }
            },
            'risk_thresholds': {
                'max_risk_score': self.config.max_risk_score,
                'min_confidence_level': self.config.min_confidence_level,
                'high_risk_threshold': self.config.high_risk_threshold,
                'critical_risk_threshold': self.config.critical_risk_threshold
            },
            'recommendations': [
                "Consider implementing additional validation rules for specialized scenarios",
                "Monitor performance metrics and adjust rate limits as needed",
                "Regular review of risk thresholds based on trading patterns"
            ]
        }
        
        return report
    
    async def export_configuration(self) -> Dict[str, Any]:
        """Export current configuration for backup/transfer"""
        return {
            'safety_config': {
                'enable_all_checks': self.config.enable_all_checks,
                'fail_fast': self.config.fail_fast,
                'parallel_validation': self.config.parallel_validation,
                'cache_validation_results': self.config.cache_validation_results,
                'max_risk_score': self.config.max_risk_score,
                'min_confidence_level': self.config.min_confidence_level,
                'high_risk_threshold': self.config.high_risk_threshold,
                'critical_risk_threshold': self.config.critical_risk_threshold,
                'max_validation_time': self.config.max_validation_time,
                'validation_timeout': self.config.validation_timeout,
                'max_validations_per_minute': self.config.max_validations_per_minute,
                'validation_burst_limit': self.config.validation_burst_limit,
                'log_validation_details': self.config.log_validation_details,
                'log_performance_metrics': self.config.log_performance_metrics
            },
            'validation_rules': {
                name: {
                    'enabled': rule.enabled,
                    'priority': rule.priority,
                    'timeout_seconds': rule.timeout_seconds,
                    'retry_attempts': rule.retry_attempts,
                    'description': rule.description
                }
                for name, rule in self._validation_rules.items()
            }
        }