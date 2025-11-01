"""
Comprehensive validation pipeline with pre-trade checks, real-time monitoring,
and post-trade analysis for safe trading operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from uuid import UUID, uuid4
import json
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

from arbitech.storage.models import (
    ArbitrageOpportunity, Trade, Sport, RiskTier, 
    BookmakerAccount, TradeStatus, RiskConfig,
    StakeData, ArbitrageLeg, NotificationType, 
    NotificationPriority, NotificationChannel
)

from .bankroll_validator import BankrollValidator, ValidationResult as BankrollValidation
from .limit_manager import LimitManager, AlertSeverity as LimitAlertSeverity
from .exposure_tracker import ExposureTracker


logger = logging.getLogger(__name__)


class ValidationStage(str, Enum):
    """Stages of the validation pipeline."""
    PRE_TRADE_CHECKS = "pre_trade_checks"
    REAL_TIME_MONITORING = "real_time_monitoring"
    POST_TRADE_ANALYSIS = "post_trade_analysis"
    CIRCUIT_BREAKER_CHECKS = "circuit_breaker_checks"
    COMPLIANCE_VALIDATION = "compliance_validation"


class ValidationLevel(str, Enum):
    """Levels of validation intensity."""
    BASIC = "basic"        # Minimal checks
    STANDARD = "standard"  # Standard checks
    STRICT = "strict"      # Comprehensive checks
    EMERGENCY = "emergency" # Maximum checks


class RiskAssessment(str, Enum):
    """Overall risk assessment results."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNACCEPTABLE = "unacceptable"


@dataclass
class ValidationRule:
    """Individual validation rule."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    stage: ValidationStage = ValidationStage.PRE_TRADE_CHECKS
    level: ValidationLevel = ValidationLevel.STANDARD
    is_active: bool = True
    weight: Decimal = '1'  # Rule weight in overall assessment
    threshold: Decimal = '0.5'  # Threshold for rule violation
    timeout_seconds: int = 30  # Maximum time for rule execution
    required: bool = True  # Whether this rule must pass
    
    # Rule-specific parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    execution_count: int = 0
    violation_count: int = 0
    average_execution_time_ms: Decimal = '0'
    last_execution: Optional[datetime] = None
    last_violation: Optional[datetime] = None


@dataclass
class ValidationResult:
    """Result from a single validation rule."""
    rule_id: UUID
    rule_name: str
    is_passed: bool
    score: Decimal  # 0-1 score (1 = perfect, 0 = violation)
    message: str
    details: Dict[str, Any]
    execution_time_ms: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    opportunity_id: UUID
    validation_id: UUID
    overall_score: Decimal
    risk_assessment: RiskAssessment
    stage: ValidationStage
    level: ValidationLevel
    
    # Individual rule results
    rule_results: List[ValidationResult]
    
    # Summary statistics
    total_rules: int
    passed_rules: int
    failed_rules: int
    skipped_rules: int
    
    # Timing information
    total_execution_time_ms: Decimal
    slowest_rule: Optional[str]
    fastest_rule: Optional[str]
    
    # Recommendations and alerts
    recommendations: List[str]
    critical_issues: List[str]
    warnings: List[str]
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    executor_id: str = ""  # ID of validator that executed this report


@dataclass
class MonitoringEvent:
    """Real-time monitoring event."""
    id: UUID = field(default_factory=uuid4)
    event_type: str = ""
    severity: str = "info"
    source: str = ""
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False


class ValidationEngine:
    """
    Comprehensive validation pipeline orchestrating bankroll validation,
    limit management, exposure tracking, and compliance checks.
    """
    
    def __init__(self, risk_config: RiskConfig):
        """
        Initialize the validation engine.
        
        Args:
            risk_config: Risk management configuration
        """
        self.risk_config = risk_config
        
        # Initialize sub-components
        self.bankroll_validator = BankrollValidator(risk_config)
        self.limit_manager = LimitManager(risk_config)
        self.exposure_tracker = ExposureTracker()
        
        # Validation rules
        self.rules: Dict[UUID, ValidationRule] = {}
        self.rule_results: Dict[UUID, List[ValidationResult]] = {}
        
        # Real-time monitoring
        self.monitoring_queue: deque = deque(maxlen=10000)
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Validation pipeline
        self.active_validations: Dict[UUID, ValidationReport] = {}
        self.validation_history: deque = deque(maxlen=1000)
        
        # Thread-safe operations
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=6)
        
        # Performance metrics
        self.total_validations = 0
        self.successful_validations = 0
        self.failed_validations = 0
        self.circuit_breaker_activations = 0
        self.average_validation_time_ms = '0'
        self.peak_concurrent_validations = 0
        
        # Circuit breaker state
        self.circuit_breaker_active = False
        self.circuit_breaker_triggered_at: Optional[datetime] = None
        self.emergency_stop_active = False
        self.daily_pnl: Decimal = '0'
        
        # Initialize default validation rules
        self._initialize_default_rules()
        
        logger.info("Validation engine initialized")
    
    def _initialize_default_rules(self):
        """Initialize default validation rules."""
        now = datetime.utcnow()
        
        # Pre-trade rules
        rule_id, rule = self._create_rule("Bankroll Check", ValidationStage.PRE_TRADE_CHECKS, 
                            ValidationLevel.BASIC, self._validate_bankroll_available)
        self.rules[rule_id] = rule
        
        rule_id, rule = self._create_rule("Minimum Profit Margin", ValidationStage.PRE_TRADE_CHECKS,
                            ValidationLevel.STANDARD, self._validate_profit_margin)
        self.rules[rule_id] = rule
        
        rule_id, rule = self._create_rule("Stake Size Limits", ValidationStage.PRE_TRADE_CHECKS,
                            ValidationLevel.STANDARD, self._validate_stake_size)
        self.rules[rule_id] = rule
        
        rule_id, rule = self._create_rule("Bookmaker Limits", ValidationStage.PRE_TRADE_CHECKS,
                            ValidationLevel.STANDARD, self._validate_bookmaker_limits)
        self.rules[rule_id] = rule
        
        rule_id, rule = self._create_rule("Opportunity Quality", ValidationStage.PRE_TRADE_CHECKS,
                            ValidationLevel.STRICT, self._validate_opportunity_quality)
        self.rules[rule_id] = rule
        
        rule_id, rule = self._create_rule("Risk Tier Compliance", ValidationStage.PRE_TRADE_CHECKS,
                            ValidationLevel.STANDARD, self._validate_risk_tier)
        self.rules[rule_id] = rule
        
        # Real-time monitoring rules
        rule_id, rule = self._create_rule("Real-time Exposure Check", ValidationStage.REAL_TIME_MONITORING,
                            ValidationLevel.STANDARD, self._validate_exposure_limits)
        self.rules[rule_id] = rule
        
        rule_id, rule = self._create_rule("Correlation Check", ValidationStage.REAL_TIME_MONITORING,
                            ValidationLevel.STRICT, self._validate_correlations)
        self.rules[rule_id] = rule
        
        # Circuit breaker rules
        rule_id, rule = self._create_rule("Circuit Breaker Trigger", ValidationStage.CIRCUIT_BREAKER_CHECKS,
                            ValidationLevel.EMERGENCY, self._validate_circuit_breaker, 
                            required=False, weight='2')
        self.rules[rule_id] = rule
        
        # Compliance rules
        rule_id, rule = self._create_rule("Regulatory Compliance", ValidationStage.COMPLIANCE_VALIDATION,
                            ValidationLevel.EMERGENCY, self._validate_compliance,
                            required=False, weight='3')
        self.rules[rule_id] = rule
        
        logger.info(f"Initialized {len(self.rules)} validation rules")
    
    def _create_rule(self, name: str, stage: ValidationStage, level: ValidationLevel, 
                    rule_function, required: bool = True, weight: Decimal = '1') -> Tuple[UUID, ValidationRule]:
        """Create a validation rule."""
        rule = ValidationRule(
            name=name,
            stage=stage,
            level=level,
            is_active=True,
            weight=weight,
            threshold='0.5',
            timeout_seconds=30,
            required=required
        )
        
        return rule.id, rule
    
    async def start_monitoring(self):
        """Start real-time validation monitoring."""
        if self.monitoring_active:
            return
        
        # Start sub-component monitoring
        await self.bankroll_validator.start_monitoring()
        await self.exposure_tracker.start_monitoring()
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Validation engine monitoring started")
    
    async def stop_monitoring(self):
        """Stop real-time validation monitoring."""
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Stop sub-component monitoring
        await self.bankroll_validator.stop_monitoring()
        await self.exposure_tracker.stop_monitoring()
        
        logger.info("Validation engine monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Process monitoring events
                await self._process_monitoring_events()
                
                # Run continuous validation checks
                await self._run_continuous_validations()
                
                # Update performance metrics
                await self._update_performance_metrics()
                
                # Check circuit breaker status
                await self._check_circuit_breaker()
                
                await asyncio.sleep(1)  # 1 second monitoring interval
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def validate_trade(self, opportunity: ArbitrageOpportunity, 
                           proposed_stake: Decimal, user_id: UUID,
                           validation_level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationReport:
        """
        Comprehensive pre-trade validation.
        
        Args:
            opportunity: Arbitrage opportunity to validate
            proposed_stake: Proposed stake amount
            user_id: User ID
            validation_level: Level of validation intensity
            
        Returns:
            ValidationReport with comprehensive validation results
        """
        validation_id = uuid4()
        start_time = datetime.utcnow()
        
        logger.info(f"Starting validation {validation_id} for opportunity {opportunity.id}")
        
        try:
            # Create validation report
            report = ValidationReport(
                opportunity_id=opportunity.id,
                validation_id=validation_id,
                overall_score='1',
                risk_assessment=RiskAssessment.LOW,
                stage=ValidationStage.PRE_TRADE_CHECKS,
                level=validation_level,
                rule_results=[],
                total_rules=0,
                passed_rules=0,
                failed_rules=0,
                skipped_rules=0,
                total_execution_time_ms='0',
                slowest_rule=None,
                fastest_rule=None,
                recommendations=[],
                critical_issues=[],
                warnings=[],
                executor_id="validation_engine"
            )
            
            # Check circuit breaker first
            if self.circuit_breaker_active:
                circuit_result = await self._validate_circuit_breaker()
                report.rule_results.append(circuit_result)
                if not circuit_result.is_passed:
                    report.overall_score = '0'
                    report.risk_assessment = RiskAssessment.UNACCEPTABLE
                    report.critical_issues.append("Circuit breaker is active - trading suspended")
                    return report
            
            # Run validation rules
            applicable_rules = self._get_applicable_rules(ValidationStage.PRE_TRADE_CHECKS, validation_level)
            
            max_concurrent = min(4, len(applicable_rules))
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def run_rule_with_semaphore(rule: ValidationRule):
                async with semaphore:
                    return await self._execute_rule(rule, opportunity, proposed_stake, user_id)
            
            # Execute rules concurrently
            tasks = [run_rule_with_semaphore(rule) for rule in applicable_rules]
            rule_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in rule_results:
                if isinstance(result, ValidationResult):
                    report.rule_results.append(result)
                elif isinstance(result, Exception):
                    # Handle rule execution exceptions
                    error_result = ValidationResult(
                        rule_id=uuid4(),
                        rule_name="Error in validation rule",
                        is_passed=False,
                        score='0',
                        message=f"Rule execution error: {str(result)}",
                        details={"error": str(result)},
                        execution_time_ms='0'
                    )
                    report.rule_results.append(error_result)
            
            # Calculate report statistics
            await self._calculate_report_statistics(report)
            
            # Determine overall risk assessment
            report.risk_assessment = await self._assess_overall_risk(report)
            
            # Generate recommendations
            await self._generate_recommendations(report)
            
            # Update performance metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            report.total_execution_time_ms = str(execution_time)
            
            self._update_validation_metrics(report)
            
            # Store report
            self.validation_history.append(report)
            self.active_validations[validation_id] = report
            
            logger.info(
                f"Validation {validation_id} completed: "
                f"score={report.overall_score:.3f}, "
                f"risk={report.risk_assessment.value}, "
                f"rules={report.passed_rules}/{report.total_rules}"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Validation {validation_id} failed with error: {e}")
            return ValidationReport(
                opportunity_id=opportunity.id,
                validation_id=validation_id,
                overall_score='0',
                risk_assessment=RiskAssessment.UNACCEPTABLE,
                stage=ValidationStage.PRE_TRADE_CHECKS,
                level=validation_level,
                rule_results=[],
                total_rules=0,
                passed_rules=0,
                failed_rules=0,
                skipped_rules=0,
                total_execution_time_ms='0',
                recommendations=[],
                critical_issues=[f"Validation pipeline error: {str(e)}"],
                warnings=[]
            )
    
    async def _execute_rule(self, rule: ValidationRule, opportunity: ArbitrageOpportunity,
                          proposed_stake: Decimal, user_id: UUID) -> ValidationResult:
        """Execute a single validation rule."""
        rule_start_time = datetime.utcnow()
        
        try:
            # Execute the rule function
            if rule.name == "Bankroll Check":
                result = await self._validate_bankroll_available(opportunity, proposed_stake, user_id)
            elif rule.name == "Minimum Profit Margin":
                result = await self._validate_profit_margin(opportunity, proposed_stake, user_id)
            elif rule.name == "Stake Size Limits":
                result = await self._validate_stake_size(opportunity, proposed_stake, user_id)
            elif rule.name == "Bookmaker Limits":
                result = await self._validate_bookmaker_limits(opportunity, proposed_stake, user_id)
            elif rule.name == "Opportunity Quality":
                result = await self._validate_opportunity_quality(opportunity, proposed_stake, user_id)
            elif rule.name == "Risk Tier Compliance":
                result = await self._validate_risk_tier(opportunity, proposed_stake, user_id)
            elif rule.name == "Real-time Exposure Check":
                result = await self._validate_exposure_limits(opportunity, proposed_stake, user_id)
            elif rule.name == "Correlation Check":
                result = await self._validate_correlations(opportunity, proposed_stake, user_id)
            elif rule.name == "Circuit Breaker Trigger":
                result = await self._validate_circuit_breaker(opportunity, proposed_stake, user_id)
            elif rule.name == "Regulatory Compliance":
                result = await self._validate_compliance(opportunity, proposed_stake, user_id)
            else:
                result = ValidationResult(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    is_passed=True,
                    score='1',
                    message="Rule not implemented",
                    details={},
                    execution_time_ms='0'
                )
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - rule_start_time).total_seconds() * 1000
            result.execution_time_ms = str(execution_time)
            
            # Update rule statistics
            rule.execution_count += 1
            rule.last_execution = datetime.utcnow()
            
            # Update average execution time
            rule.average_execution_time_ms = (
                rule.average_execution_time_ms * (rule.execution_count - 1) + result.execution_time_ms
            ) / rule.execution_count
            
            if not result.is_passed:
                rule.violation_count += 1
                rule.last_violation = datetime.utcnow()
            
            return result
            
        except asyncio.TimeoutError:
            return ValidationResult(
                rule_id=rule.id,
                rule_name=rule.name,
                is_passed=False,
                score='0',
                message="Rule execution timeout",
                details={"timeout": rule.timeout_seconds},
                execution_time_ms=str(rule.timeout_seconds * 1000)
            )
        except Exception as e:
            logger.error(f"Rule execution error for {rule.name}: {e}")
            return ValidationResult(
                rule_id=rule.id,
                rule_name=rule.name,
                is_passed=False,
                score='0',
                message=f"Rule execution failed: {str(e)}",
                details={"error": str(e)},
                execution_time_ms='0'
            )
    
    async def _validate_bankroll_available(self, opportunity: ArbitrageOpportunity,
                                         proposed_stake: Decimal, user_id: UUID) -> ValidationResult:
        """Validate sufficient bankroll availability."""
        try:
            bankroll_result = await self.bankroll_validator.validate_bankroll()
            
            # Check if we have enough available bankroll
            available_capacity = min(
                bankroll_result.remaining_capacity,
                bankroll_result.current_exposure + proposed_stake - bankroll_result.current_exposure
            )
            
            is_sufficient = proposed_stake <= available_capacity
            score = min('1', available_capacity / max(proposed_stake, '1'))
            
            message = f"Bankroll available: {available_capacity}, Required: {proposed_stake}"
            
            return ValidationResult(
                rule_id=uuid4(),
                rule_name="Bankroll Check",
                is_passed=is_sufficient,
                score=score,
                message=message,
                details={
                    "available_capacity": str(available_capacity),
                    "required_amount": str(proposed_stake),
                    "bankroll_validation": bankroll_result
                },
                execution_time_ms='0'
            )
            
        except Exception as e:
            return ValidationResult(
                rule_id=uuid4(),
                rule_name="Bankroll Check",
                is_passed=False,
                score='0',
                message=f"Bankroll validation failed: {str(e)}",
                details={"error": str(e)},
                execution_time_ms='0'
            )
    
    async def _validate_profit_margin(self, opportunity: ArbitrageOpportunity,
                                    proposed_stake: Decimal, user_id: UUID) -> ValidationResult:
        """Validate minimum profit margin requirements."""
        min_margin = self.risk_config.global_limits.system_min_profit_margin
        actual_margin = opportunity.profit_margin
        
        is_sufficient = actual_margin >= min_margin
        score = min('1', actual_margin / max(min_margin, '0.01'))
        
        message = f"Profit margin: {actual_margin:.2%}, Minimum required: {min_margin:.2%}"
        
        return ValidationResult(
            rule_id=uuid4(),
            rule_name="Minimum Profit Margin",
            is_passed=is_sufficient,
            score=score,
            message=message,
            details={
                "actual_margin": str(actual_margin),
                "minimum_margin": str(min_margin),
                "margin_ratio": str(actual_margin / min_margin) if min_margin > 0 else "0"
            },
            execution_time_ms='0'
        )
    
    async def _validate_stake_size(self, opportunity: ArbitrageOpportunity,
                                 proposed_stake: Decimal, user_id: UUID) -> ValidationResult:
        """Validate stake size against limits."""
        # Get appropriate limit based on risk tier
        if opportunity.risk_tier == RiskTier.TIER_A:
            max_stake = self.risk_config.tier_a_settings.max_stake_per_trade
        elif opportunity.risk_tier == RiskTier.TIER_B:
            max_stake = self.risk_config.tier_b_settings.max_stake_per_trade
        else:
            max_stake = '100'  # Default for other tiers
        
        # Check individual stake limit
        individual_limit_ok = proposed_stake <= max_stake
        
        # Check limit manager rules
        limit_result = await self.limit_manager.check_trade_limits(opportunity, proposed_stake, user_id)
        limits_ok = limit_result["is_valid"]
        
        overall_ok = individual_limit_ok and limits_ok
        
        # Calculate score
        max_allowed = min(max_stake, proposed_stake * 2)  # Conservative estimate
        score = min('1', max_allowed / max(proposed_stake, '1'))
        
        message = f"Stake: {proposed_stake}, Max allowed: {max_stake}, Limits valid: {limits_ok}"
        
        return ValidationResult(
            rule_id=uuid4(),
            rule_name="Stake Size Limits",
            is_passed=overall_ok,
            score=score,
            message=message,
            details={
                "proposed_stake": str(proposed_stake),
                "max_allowed": str(max_stake),
                "individual_limit_ok": individual_limit_ok,
                "limit_manager_result": limit_result
            },
            execution_time_ms='0'
        )
    
    async def _validate_bookmaker_limits(self, opportunity: ArbitrageOpportunity,
                                       proposed_stake: Decimal, user_id: UUID) -> ValidationResult:
        """Validate bookmaker-specific limits and capacity."""
        violations = []
        total_affected_bookmakers = 0
        
        for leg in opportunity.legs:
            # Check limit manager
            limit_result = await self.limit_manager.check_trade_limits(
                opportunity, leg.actual_stake, user_id
            )
            
            if not limit_result["is_valid"]:
                violations.extend(limit_result["violations"])
                total_affected_bookmakers += 1
        
        is_passed = len(violations) == 0
        score = '1' if is_passed else '0.5'
        
        message = f"Bookmakers checked: {len(opportunity.legs)}, Violations: {len(violations)}"
        
        return ValidationResult(
            rule_id=uuid4(),
            rule_name="Bookmaker Limits",
            is_passed=is_passed,
            score=score,
            message=message,
            details={
                "bookmakers_checked": len(opportunity.legs),
                "violations": violations,
                "affected_bookmakers": total_affected_bookmakers
            },
            execution_time_ms='0'
        )
    
    async def _validate_opportunity_quality(self, opportunity: ArbitrageOpportunity,
                                          proposed_stake: Decimal, user_id: UUID) -> ValidationResult:
        """Validate opportunity quality criteria."""
        quality_score = '1'
        quality_issues = []
        
        # Check odds freshness
        odds_age = (datetime.utcnow() - opportunity.odds_freshness).total_seconds() / 60  # minutes
        if odds_age > 30:  # 30 minutes
            quality_score *= '0.8'
            quality_issues.append(f"Old odds: {odds_age:.1f} minutes")
        
        # Check validation errors
        if opportunity.validation_errors:
            quality_score *= '0.7'
            quality_issues.append(f"Validation errors: {len(opportunity.validation_errors)}")
        
        # Check liquidity (simplified)
        if not opportunity.liquidity_checked:
            quality_score *= '0.9'
            quality_issues.append("Liquidity not verified")
        
        # Check guaranteed profit
        if not opportunity.guaranteed_profit:
            quality_score *= '0.5'
            quality_issues.append("Profit not guaranteed")
        
        is_passed = quality_score >= '0.6'
        message = f"Quality score: {quality_score:.2f}, Issues: {len(quality_issues)}"
        
        return ValidationResult(
            rule_id=uuid4(),
            rule_name="Opportunity Quality",
            is_passed=is_passed,
            score=quality_score,
            message=message,
            details={
                "quality_score": str(quality_score),
                "quality_issues": quality_issues,
                "odds_age_minutes": odds_age,
                "validation_errors": opportunity.validation_errors,
                "liquidity_checked": opportunity.liquidity_checked,
                "guaranteed_profit": opportunity.guaranteed_profit
            },
            execution_time_ms='0'
        )
    
    async def _validate_risk_tier(self, opportunity: ArbitrageOpportunity,
                                proposed_stake: Decimal, user_id: UUID) -> ValidationResult:
        """Validate risk tier compliance."""
        # Get tier-specific limits
        if opportunity.risk_tier == RiskTier.TIER_A:
            max_daily = self.risk_config.tier_a_settings.max_daily_exposure
            max_concurrent = self.risk_config.tier_a_settings.max_concurrent_opportunities
            min_margin = self.risk_config.tier_a_settings.min_profit_margin
        elif opportunity.risk_tier == RiskTier.TIER_B:
            max_daily = self.risk_config.tier_b_settings.max_daily_exposure
            max_concurrent = self.risk_config.tier_b_settings.max_concurrent_opportunities
            min_margin = self.risk_config.tier_b_settings.min_profit_margin
        else:
            # Use conservative defaults for other tiers
            max_daily = '500'
            max_concurrent = 3
            min_margin = '0.03'
        
        # Check profit margin
        margin_ok = opportunity.profit_margin >= min_margin
        
        # Check current exposure against tier limits
        bankroll_result = await self.bankroll_validator.validate_bankroll()
        exposure_ok = bankroll_result.current_exposure < max_daily
        
        # Check concurrent opportunities (simplified)
        concurrent_ok = len(self.active_validations) < max_concurrent
        
        is_passed = margin_ok and exposure_ok and concurrent_ok
        
        # Calculate score
        score_factors = [
            '1' if margin_ok else '0',
            '1' if exposure_ok else '0.5',
            '1' if concurrent_ok else '0.8'
        ]
        score = sum(score_factors) / len(score_factors)
        
        message = f"Risk tier: {opportunity.risk_tier.value}, Margin OK: {margin_ok}, Exposure OK: {exposure_ok}, Concurrent OK: {concurrent_ok}"
        
        return ValidationResult(
            rule_id=uuid4(),
            rule_name="Risk Tier Compliance",
            is_passed=is_passed,
            score=score,
            message=message,
            details={
                "risk_tier": opportunity.risk_tier.value,
                "max_daily_exposure": str(max_daily),
                "max_concurrent_opportunities": max_concurrent,
                "min_profit_margin": str(min_margin),
                "profit_margin_ok": margin_ok,
                "exposure_ok": exposure_ok,
                "concurrent_ok": concurrent_ok,
                "current_exposure": str(bankroll_result.current_exposure)
            },
            execution_time_ms='0'
        )
    
    async def _validate_exposure_limits(self, opportunity: ArbitrageOpportunity,
                                      proposed_stake: Decimal, user_id: UUID) -> ValidationResult:
        """Validate exposure limits in real-time."""
        try:
            exposure_summary = await self.exposure_tracker.get_exposure_summary()
            
            # Check total exposure limits
            total_exposure = str(exposure_summary.get("total_exposure", 0))
            new_total_exposure = total_exposure + proposed_stake
            
            max_total_exposure = self.risk_config.global_limits.max_total_exposure
            exposure_ok = new_total_exposure <= max_total_exposure
            
            # Check concentration limits
            concentrations = exposure_summary.get("top_concentrations", [])
            concentration_ok = True
            concentration_violations = []
            
            for conc in concentrations[:5]:  # Check top 5 concentrations
                if conc["concentration"] > '0.3':  # 30% concentration limit
                    concentration_ok = False
                    concentration_violations.append(
                        f"{conc['source']}: {conc['concentration']:.1%}"
                    )
            
            is_passed = exposure_ok and concentration_ok
            
            # Calculate score
            exposure_utilization = new_total_exposure / max_total_exposure if max_total_exposure > 0 else '0'
            score = min('1', ('1' - exposure_utilization))
            
            message = f"Total exposure: {new_total_exposure}/{max_total_exposure}, Concentration violations: {len(concentration_violations)}"
            
            return ValidationResult(
                rule_id=uuid4(),
                rule_name="Real-time Exposure Check",
                is_passed=is_passed,
                score=score,
                message=message,
                details={
                    "current_exposure": str(total_exposure),
                    "new_exposure": str(new_total_exposure),
                    "max_exposure": str(max_total_exposure),
                    "exposure_ok": exposure_ok,
                    "concentration_violations": concentration_violations,
                    "exposure_summary": exposure_summary
                },
                execution_time_ms='0'
            )
            
        except Exception as e:
            return ValidationResult(
                rule_id=uuid4(),
                rule_name="Real-time Exposure Check",
                is_passed=False,
                score='0',
                message=f"Exposure validation failed: {str(e)}",
                details={"error": str(e)},
                execution_time_ms='0'
            )
    
    async def _validate_correlations(self, opportunity: ArbitrageOpportunity,
                                   proposed_stake: Decimal, user_id: UUID) -> ValidationResult:
        """Validate correlation risks."""
        try:
            correlation_matrix = await self.exposure_tracker.get_correlation_matrix()
            significant_correlations = correlation_matrix.get("significant_correlations", [])
            
            # Check for high correlations that would increase risk
            high_correlation_risk = False
            correlation_risks = []
            
            for corr in significant_correlations:
                if abs(corr["correlation"]) > '0.7':  # High correlation threshold
                    high_correlation_risk = True
                    correlation_risks.append(
                        f"{corr['source_a']}-{corr['source_b']}: {corr['correlation']:.2f}"
                    )
            
            # Calculate position sizing recommendation
            sizing_recommendations = []
            for leg in opportunity.legs:
                recommendation = await self.exposure_tracker.calculate_position_sizing(
                    leg.actual_stake, 
                    opportunity.risk_tier.value,
                    leg.bookmaker
                )
                sizing_recommendations.append(recommendation)
            
            is_passed = not high_correlation_risk
            
            # Score based on correlation risk
            score = '1' if not high_correlation_risk else '0.7'
            
            message = f"Significant correlations: {len(significant_correlations)}, High risk correlations: {len(correlation_risks)}"
            
            return ValidationResult(
                rule_id=uuid4(),
                rule_name="Correlation Check",
                is_passed=is_passed,
                score=score,
                message=message,
                details={
                    "significant_correlations": significant_correlations,
                    "high_risk_correlations": correlation_risks,
                    "sizing_recommendations": sizing_recommendations
                },
                execution_time_ms='0'
            )
            
        except Exception as e:
            return ValidationResult(
                rule_id=uuid4(),
                rule_name="Correlation Check",
                is_passed=False,
                score='0',
                message=f"Correlation validation failed: {str(e)}",
                details={"error": str(e)},
                execution_time_ms='0'
            )
    
    async def _validate_circuit_breaker(self, opportunity: ArbitrageOpportunity,
                                      proposed_stake: Decimal, user_id: UUID) -> ValidationResult:
        """Validate circuit breaker status."""
        is_passed = not self.circuit_breaker_active
        
        message = f"Circuit breaker active: {self.circuit_breaker_active}"
        
        return ValidationResult(
            rule_id=uuid4(),
            rule_name="Circuit Breaker Trigger",
            is_passed=is_passed,
            score='1' if is_passed else '0',
            message=message,
            details={
                "circuit_breaker_active": self.circuit_breaker_active,
                "triggered_at": self.circuit_breaker_triggered_at.isoformat() if self.circuit_breaker_triggered_at else None
            },
            execution_time_ms='0'
        )
    
    async def _validate_compliance(self, opportunity: ArbitrageOpportunity,
                                 proposed_stake: Decimal, user_id: UUID) -> ValidationResult:
        """Validate regulatory compliance."""
        compliance_issues = []
        
        # Check sport restrictions
        restricted_sports = ["esports", "politics"]  # Would be configurable
        if opportunity.sport.value in restricted_sports:
            compliance_issues.append(f"Restricted sport: {opportunity.sport.value}")
        
        # Check market type restrictions
        restricted_markets = ["live_betting"]  # Would be configurable
        if "live" in opportunity.market_type.lower():
            compliance_issues.append("Live betting may have restrictions")
        
        # Check bet size limits
        if proposed_stake > '1000':
            compliance_issues.append(f"Large bet size: {proposed_stake} may require verification")
        
        is_passed = len(compliance_issues) == 0
        
        message = f"Compliance issues: {len(compliance_issues)}"
        
        return ValidationResult(
            rule_id=uuid4(),
            rule_name="Regulatory Compliance",
            is_passed=is_passed,
            score='1' if is_passed else '0.8',
            message=message,
            details={
                "compliance_issues": compliance_issues,
                "opportunity_sport": opportunity.sport.value,
                "market_type": opportunity.market_type,
                "proposed_stake": str(proposed_stake)
            },
            execution_time_ms='0'
        )
    
    def _get_applicable_rules(self, stage: ValidationStage, level: ValidationLevel) -> List[ValidationRule]:
        """Get validation rules applicable to a stage and level."""
        applicable_rules = []
        
        for rule in self.rules.values():
            if (rule.is_active and 
                rule.stage == stage and 
                self._is_rule_applicable_for_level(rule, level)):
                applicable_rules.append(rule)
        
        return sorted(applicable_rules, key=lambda r: r.weight, reverse=True)
    
    def _is_rule_applicable_for_level(self, rule: ValidationRule, level: ValidationLevel) -> bool:
        """Check if rule is applicable for validation level."""
        level_hierarchy = {
            ValidationLevel.BASIC: 1,
            ValidationLevel.STANDARD: 2,
            ValidationLevel.STRICT: 3,
            ValidationLevel.EMERGENCY: 4
        }
        
        rule_level_priority = level_hierarchy.get(rule.level, 1)
        required_level_priority = level_hierarchy.get(level, 1)
        
        # Emergency level includes all rules
        if level == ValidationLevel.EMERGENCY:
            return True
        
        # Other levels include rules up to their priority level
        return rule_level_priority <= required_level_priority
    
    async def _calculate_report_statistics(self, report: ValidationReport):
        """Calculate statistics for a validation report."""
        report.total_rules = len(report.rule_results)
        report.passed_rules = sum(1 for result in report.rule_results if result.is_passed)
        report.failed_rules = sum(1 for result in report.rule_results if not result.is_passed)
        report.skipped_rules = 0  # No skipped rules in current implementation
        
        # Calculate overall score (weighted)
        if report.total_rules > 0:
            weighted_score = sum(
                result.score * rule.weight 
                for result, rule in zip(report.rule_results, self._get_applicable_rules(report.stage, report.level))
            )
            total_weight = sum(rule.weight for rule in self._get_applicable_rules(report.stage, report.level))
            report.overall_score = weighted_score / total_weight if total_weight > 0 else '1'
        
        # Find slowest and fastest rules
        if report.rule_results:
            slowest_result = max(report.rule_results, key=lambda r: r.execution_time_ms)
            fastest_result = min(report.rule_results, key=lambda r: r.execution_time_ms)
            report.slowest_rule = slowest_result.rule_name
            report.fastest_rule = fastest_result.rule_name
    
    async def _assess_overall_risk(self, report: ValidationReport) -> RiskAssessment:
        """Determine overall risk assessment from validation report."""
        if report.overall_score >= '0.9':
            return RiskAssessment.LOW
        elif report.overall_score >= '0.7':
            return RiskAssessment.MEDIUM
        elif report.overall_score >= '0.5':
            return RiskAssessment.HIGH
        elif report.overall_score >= '0.2':
            return RiskAssessment.CRITICAL
        else:
            return RiskAssessment.UNACCEPTABLE
    
    async def _generate_recommendations(self, report: ValidationReport):
        """Generate recommendations based on validation results."""
        # Analyze failed rules
        for result in report.rule_results:
            if not result.is_passed:
                if "bankroll" in result.rule_name.lower():
                    report.recommendations.append("Consider reducing stake size or increasing available bankroll")
                elif "margin" in result.rule_name.lower():
                    report.recommendations.append("Seek opportunities with higher profit margins")
                elif "limit" in result.rule_name.lower():
                    report.recommendations.append("Review and adjust limit settings")
                elif "exposure" in result.rule_name.lower():
                    report.recommendations.append("Reduce position concentration across bookmakers")
                elif "quality" in result.rule_name.lower():
                    report.recommendations.append("Verify opportunity data freshness and accuracy")
        
        # Add general recommendations based on risk level
        if report.risk_assessment in [RiskAssessment.HIGH, RiskAssessment.CRITICAL]:
            report.recommendations.append("Consider using stricter validation level for this opportunity")
            report.warnings.append("High-risk opportunity detected - additional monitoring recommended")
    
    def _update_validation_metrics(self, report: ValidationReport):
        """Update validation performance metrics."""
        self.total_validations += 1
        
        if report.overall_score >= '0.5':
            self.successful_validations += 1
        else:
            self.failed_validations += 1
        
        # Update average validation time
        self.average_validation_time_ms = (
            self.average_validation_time_ms * (self.total_validations - 1) + report.total_execution_time_ms
        ) / self.total_validations
        
        # Update peak concurrent validations
        if len(self.active_validations) > self.peak_concurrent_validations:
            self.peak_concurrent_validations = len(self.active_validations)
    
    async def _process_monitoring_events(self):
        """Process real-time monitoring events."""
        while self.monitoring_queue:
            try:
                event = self.monitoring_queue.popleft()
                
                # Process based on event type
                if event.event_type == "limit_breach":
                    await self._handle_limit_breach(event)
                elif event.event_type == "exposure_warning":
                    await self._handle_exposure_warning(event)
                elif event.event_type == "circuit_breaker_trigger":
                    await self._handle_circuit_breaker_trigger(event)
                
                event.processed = True
                
            except Exception as e:
                logger.error(f"Error processing monitoring event: {e}")
                break
    
    async def _run_continuous_validations(self):
        """Run continuous validation checks for active positions."""
        # Check active positions for ongoing validation
        # This would implement real-time monitoring of existing trades
        
        # For now, just check circuit breaker status periodically
        if self.circuit_breaker_active and self.circuit_breaker_triggered_at:
            # Check if circuit breaker should be reset
            time_since_trigger = datetime.utcnow() - self.circuit_breaker_triggered_at
            if time_since_trigger > timedelta(minutes=30):  # 30-minute cooldown
                logger.info("Circuit breaker cooldown period elapsed - checking if safe to reset")
                # Would implement circuit breaker reset logic here
    
    async def _update_performance_metrics(self):
        """Update system performance metrics."""
        # Clean up old validation reports
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.validation_history = deque(
            [report for report in self.validation_history if report.timestamp > cutoff_time],
            maxlen=1000
        )
        
        # Clean up expired active validations
        expired_ids = [
            validation_id for validation_id, report in self.active_validations.items()
            if report.timestamp < cutoff_time
        ]
        
        for validation_id in expired_ids:
            del self.active_validations[validation_id]
    
    async def _check_circuit_breaker(self):
        """Check circuit breaker status and conditions."""
        # Get current bankroll validation
        try:
            bankroll_result = await self.bankroll_validator.validate_bankroll()
            
            # Trigger circuit breaker on severe violations
            if len(bankroll_result.violations) >= 3:
                await self._trigger_circuit_breaker("Multiple bankroll violations")
            
            # Check failsafe triggers
            failsafe_breaches = await self._check_failsafe_conditions()
            if failsafe_breaches:
                await self._trigger_circuit_breaker("Failsafe conditions breached")
                
        except Exception as e:
            logger.error(f"Error checking circuit breaker: {e}")
    
    async def _check_failsafe_conditions(self) -> List[str]:
        """Check if failsafe conditions are breached."""
        breaches = []
        
        try:
            # Check stop loss
            if self.daily_pnl <= -self.risk_config.failsafes.emergency_stop_loss:
                breaches.append(f"Emergency stop loss breached: {self.daily_pnl}")
            
            # Check loss per hour
            hourly_losses = await self._calculate_hourly_losses()
            if hourly_losses <= -self.risk_config.failsafes.max_loss_per_hour:
                breaches.append(f"Maximum hourly loss exceeded: {hourly_losses}")
            
            # Check consecutive losses (simplified)
            consecutive_losses = await self._count_consecutive_losses()
            if consecutive_losses >= self.risk_config.failsafes.max_consecutive_losses:
                breaches.append(f"Too many consecutive losses: {consecutive_losses}")
                
        except Exception as e:
            logger.error(f"Error checking failsafe conditions: {e}")
        
        return breaches
    
    async def _calculate_hourly_losses(self) -> Decimal:
        """Calculate current hourly losses."""
        # Simplified calculation - would use actual historical data
        return '0'
    
    async def _count_consecutive_losses(self) -> int:
        """Count consecutive losing trades."""
        # Simplified calculation - would use actual trade history
        return 0
    
    async def _handle_limit_breach(self, event: MonitoringEvent):
        """Handle limit breach monitoring event."""
        logger.warning(f"Limit breach detected: {event.message}")
        
        # Could trigger additional monitoring or position adjustments
    
    async def _handle_exposure_warning(self, event: MonitoringEvent):
        """Handle exposure warning monitoring event."""
        logger.info(f"Exposure warning: {event.message}")
    
    async def _handle_circuit_breaker_trigger(self, event: MonitoringEvent):
        """Handle circuit breaker trigger event."""
        logger.critical(f"CIRCUIT BREAKER TRIGGERED: {event.message}")
        
        # This would trigger emergency trading halt
    
    async def _trigger_circuit_breaker(self, reason: str):
        """Trigger circuit breaker."""
        if not self.circuit_breaker_active:
            self.circuit_breaker_active = True
            self.circuit_breaker_triggered_at = datetime.utcnow()
            self.circuit_breaker_activations += 1
            
            # Create monitoring event
            event = MonitoringEvent(
                event_type="circuit_breaker_trigger",
                severity="critical",
                source="validation_engine",
                message=f"Circuit breaker triggered: {reason}"
            )
            self.monitoring_queue.append(event)
            
            logger.critical(f"Circuit breaker activated: {reason}")
    
    async def activate_emergency_stop(self):
        """Activate emergency stop (manual override)."""
        self.emergency_stop_active = True
        await self._trigger_circuit_breaker("Manual emergency stop activated")
        
        logger.critical("EMERGENCY STOP ACTIVATED - ALL TRADING HALTED")
    
    async def reset_circuit_breaker(self):
        """Reset circuit breaker manually."""
        if self.circuit_breaker_active:
            self.circuit_breaker_active = False
            self.circuit_breaker_triggered_at = None
            
            logger.info("Circuit breaker reset - trading may resume")
    
    async def get_validation_summary(self) -> Dict[str, Any]:
        """Get comprehensive validation system summary."""
        with self._lock:
            # Calculate rule statistics
            rule_stats = {
                "total_rules": len(self.rules),
                "active_rules": sum(1 for rule in self.rules.values() if rule.is_active),
                "rules_by_stage": {},
                "rules_by_level": {}
            }
            
            for rule in self.rules.values():
                # Count by stage
                if rule.stage.value not in rule_stats["rules_by_stage"]:
                    rule_stats["rules_by_stage"][rule.stage.value] = 0
                rule_stats["rules_by_stage"][rule.stage.value] += 1
                
                # Count by level
                if rule.level.value not in rule_stats["rules_by_level"]:
                    rule_stats["rules_by_level"][rule.level.value] = 0
                rule_stats["rules_by_level"][rule.level.value] += 1
            
            # Recent validation history
            recent_validations = [
                {
                    "validation_id": str(report.validation_id),
                    "overall_score": float(report.overall_score),
                    "risk_assessment": report.risk_assessment.value,
                    "stage": report.stage.value,
                    "level": report.level.value,
                    "rules_passed": report.passed_rules,
                    "rules_failed": report.failed_rules,
                    "execution_time_ms": float(report.total_execution_time_ms),
                    "timestamp": report.timestamp.isoformat()
                }
                for report in list(self.validation_history)[-10:]  # Last 10
            ]
            
            # Circuit breaker status
            circuit_breaker_status = {
                "is_active": self.circuit_breaker_active,
                "triggered_at": self.circuit_breaker_triggered_at.isoformat() if self.circuit_breaker_triggered_at else None,
                "activations_count": self.circuit_breaker_activations,
                "emergency_stop_active": self.emergency_stop_active
            }
            
            return {
                "performance_metrics": {
                    "total_validations": self.total_validations,
                    "successful_validations": self.successful_validations,
                    "failed_validations": self.failed_validations,
                    "success_rate": self.successful_validations / max(self.total_validations, 1),
                    "average_validation_time_ms": float(self.average_validation_time_ms),
                    "peak_concurrent_validations": self.peak_concurrent_validations
                },
                "rule_statistics": rule_stats,
                "recent_validations": recent_validations,
                "circuit_breaker": circuit_breaker_status,
                "sub_component_status": {
                    "bankroll_validator_active": self.bankroll_validator._monitoring_active,
                    "limit_manager_alerts": self.limit_manager.alerts_sent,
                    "exposure_tracker_positions": len(self.exposure_tracker.active_positions)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def export_validation_data(self) -> Dict[str, Any]:
        """Export all validation system data."""
        with self._lock:
            return {
                "validation_rules": [
                    {
                        "id": str(rule.id),
                        "name": rule.name,
                        "stage": rule.stage.value,
                        "level": rule.level.value,
                        "is_active": rule.is_active,
                        "weight": str(rule.weight),
                        "threshold": str(rule.threshold),
                        "timeout_seconds": rule.timeout_seconds,
                        "required": rule.required,
                        "parameters": rule.parameters,
                        "execution_count": rule.execution_count,
                        "violation_count": rule.violation_count,
                        "average_execution_time_ms": float(rule.average_execution_time_ms)
                    }
                    for rule in self.rules.values()
                ],
                "validation_history": [
                    {
                        "validation_id": str(report.validation_id),
                        "opportunity_id": str(report.opportunity_id),
                        "overall_score": str(report.overall_score),
                        "risk_assessment": report.risk_assessment.value,
                        "stage": report.stage.value,
                        "level": report.level.value,
                        "rule_results": [
                            {
                                "rule_name": result.rule_name,
                                "is_passed": result.is_passed,
                                "score": str(result.score),
                                "message": result.message,
                                "execution_time_ms": float(result.execution_time_ms)
                            }
                            for result in report.rule_results
                        ],
                        "total_rules": report.total_rules,
                        "passed_rules": report.passed_rules,
                        "failed_rules": report.failed_rules,
                        "recommendations": report.recommendations,
                        "critical_issues": report.critical_issues,
                        "warnings": report.warnings,
                        "timestamp": report.timestamp.isoformat()
                    }
                    for report in self.validation_history
                ],
                "performance_metrics": {
                    "total_validations": self.total_validations,
                    "successful_validations": self.successful_validations,
                    "failed_validations": self.failed_validations,
                    "circuit_breaker_activations": self.circuit_breaker_activations,
                    "average_validation_time_ms": float(self.average_validation_time_ms),
                    "peak_concurrent_validations": self.peak_concurrent_validations
                },
                "export_timestamp": datetime.utcnow().isoformat()
            }
    
    async def shutdown(self):
        """Gracefully shutdown the validation engine."""
        logger.info("Shutting down validation engine...")
        
        # Stop monitoring
        await self.stop_monitoring()
        
        # Shutdown sub-components
        await self.bankroll_validator.shutdown()
        await self.exposure_tracker.shutdown()
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        # Log final metrics
        summary = await self.get_validation_summary()
        logger.info(f"Final validation summary: {json.dumps(summary, default=str)}")
        
        logger.info("Validation engine shutdown complete")