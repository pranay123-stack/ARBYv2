"""
Pre-Trade Validator - Comprehensive Pre-Trade Validation System

This module provides comprehensive pre-trade validation including:
- Opportunity verification
- Risk assessment
- Limit checks
- Feasibility analysis
- User preference validation
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json

# Import from other modules (we'll create these next)
# from .compliance_checker import ComplianceChecker


class ValidationType(Enum):
    """Type of validation check"""
    BASIC = "basic"
    ADVANCED = "advanced"
    CUSTOM = "custom"


class ValidationSeverity(Enum):
    """Severity level of validation issue"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Individual validation check result"""
    check_name: str
    passed: bool
    severity: ValidationSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    risk_impact: float = 0.0
    recommended_action: str = ""


@dataclass
class PreTradeAnalysis:
    """Comprehensive pre-trade analysis result"""
    opportunity_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Core analysis
    opportunity_verified: bool = False
    risk_assessment_score: float = 0.0
    feasibility_score: float = 0.0
    viability_score: float = 0.0
    
    # Detailed checks
    validation_results: List[ValidationResult] = field(default_factory=list)
    
    # Risk metrics
    max_recommended_stake: float = 0.0
    risk_adjusted_return: float = 0.0
    volatility_estimate: float = 0.0
    liquidity_score: float = 0.0
    
    # Limit compliance
    within_bankroll_limits: bool = False
    within_exposure_limits: bool = False
    within_stake_limits: bool = False
    
    # Feasibility analysis
    execution_feasibility: float = 0.0
    timing_feasibility: float = 0.0
    technical_feasibility: float = 0.0
    
    # Recommendations
    recommended_stake: float = 0.0
    risk_mitigation_strategies: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)


@dataclass
class PreTradeConfig:
    """Configuration for pre-trade validation"""
    # Validation settings
    enable_basic_validation: bool = True
    enable_advanced_validation: bool = True
    enable_feasibility_analysis: bool = True
    require_opportunity_verification: bool = True
    
    # Risk thresholds
    min_viability_score: float = 70.0
    min_feasibility_score: float = 60.0
    max_risk_score: float = 80.0
    min_liquidity_score: float = 50.0
    
    # Stake validation
    max_stake_multiplier: float = 2.0  # Max multiple of base stake
    stake_precision_required: float = 0.01  # Minimum stake precision
    
    # Performance settings
    validation_timeout: float = 15.0
    parallel_checks: bool = True
    cache_results: bool = True
    
    # Logging
    log_validation_details: bool = True
    log_performance_metrics: bool = True


class PreTradeValidator:
    """
    Comprehensive Pre-Trade Validation System
    
    Validates opportunities before execution including:
    - Opportunity verification and validation
    - Risk assessment and scoring
    - Limit compliance checking
    - Feasibility analysis
    - User preference validation
    """
    
    def __init__(self, config: Optional[PreTradeConfig] = None):
        """
        Initialize pre-trade validator
        
        Args:
            config: Pre-trade validation configuration
        """
        self.config = config or PreTradeConfig()
        self.logger = logging.getLogger(__name__)
        
        # Validation check registry
        self._validation_checks = self._initialize_validation_checks()
        
        # Performance tracking
        self._performance_stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'average_check_time': 0.0,
            'validation_rate': 0.0
        }
        
        # Validation cache
        self._validation_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        self.logger.info("Pre-Trade Validator initialized")
    
    def _initialize_validation_checks(self) -> Dict[str, Dict[str, Any]]:
        """Initialize all validation checks"""
        return {
            # Basic validation checks
            'opportunity_format': {
                'enabled': True,
                'required_fields': ['id', 'profit_margin', 'legs'],
                'validation_function': self._validate_opportunity_format
            },
            'profit_margin': {
                'enabled': True,
                'min_profit': 0.5,
                'max_profit': 50.0,
                'validation_function': self._validate_profit_margin
            },
            'odds_validation': {
                'enabled': True,
                'min_odds': 1.01,
                'max_odds': 100.0,
                'validation_function': self._validate_odds
            },
            'stake_calculations': {
                'enabled': True,
                'validation_function': self._validate_stake_calculations
            },
            
            # Advanced validation checks
            'risk_assessment': {
                'enabled': True,
                'validation_function': self._perform_risk_assessment
            },
            'liquidity_analysis': {
                'enabled': True,
                'validation_function': self._analyze_liquidity
            },
            'volatility_estimation': {
                'enabled': True,
                'validation_function': self._estimate_volatility
            },
            'timing_analysis': {
                'enabled': True,
                'validation_function': self._analyze_timing
            },
            
            # Feasibility checks
            'execution_feasibility': {
                'enabled': True,
                'validation_function': self._check_execution_feasibility
            },
            'bookmaker_limits': {
                'enabled': True,
                'validation_function': self._check_bookmaker_limits
            },
            'market_conditions': {
                'enabled': True,
                'validation_function': self._analyze_market_conditions
            }
        }
    
    async def validate_basic_checks(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform basic pre-trade validation checks
        
        Args:
            opportunity_data: Opportunity to validate
            user_preferences: User-specific preferences
            
        Returns:
            Dict containing validation results
        """
        start_time = time.time()
        opportunity_id = opportunity_data.get('id', 'unknown')
        
        self.logger.debug(f"Starting basic validation for {opportunity_id}")
        
        results = {
            'success': True,
            'data': {},
            'warnings': [],
            'checks_performed': []
        }
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(opportunity_data, 'basic')
            if self.config.cache_results and cache_key in self._validation_cache:
                cached_result, timestamp = self._validation_cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    self.logger.debug(f"Using cached basic validation for {opportunity_id}")
                    return cached_result
            
            # Run basic validation checks
            validation_tasks = []
            
            for check_name, check_config in self._validation_checks.items():
                if not check_config.get('enabled', False):
                    continue
                    
                # Skip advanced checks for basic validation
                if check_name in ['risk_assessment', 'liquidity_analysis', 
                                'volatility_estimation', 'timing_analysis',
                                'execution_feasibility', 'bookmaker_limits', 'market_conditions']:
                    continue
                
                if self.config.parallel_checks:
                    task = asyncio.create_task(
                        self._run_validation_check(check_name, check_config, opportunity_data, user_preferences)
                    )
                    validation_tasks.append((check_name, task))
                else:
                    result = await self._run_validation_check(check_name, check_config, opportunity_data, user_preferences)
                    results['checks_performed'].append(check_name)
                    
                    if not result.passed:
                        results['success'] = False
                        results['data'][check_name] = {
                            'passed': False,
                            'message': result.message,
                            'severity': result.severity.value
                        }
                        
                        if result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                            break
                    else:
                        results['data'][check_name] = {
                            'passed': True,
                            'message': result.message,
                            'details': result.details
                        }
            
            # Process parallel tasks if enabled
            if self.config.parallel_checks:
                for check_name, task in validation_tasks:
                    try:
                        result = await asyncio.wait_for(task, timeout=self.config.validation_timeout)
                        results['checks_performed'].append(check_name)
                        
                        if not result.passed:
                            results['success'] = False
                            results['data'][check_name] = {
                                'passed': False,
                                'message': result.message,
                                'severity': result.severity.value
                            }
                            
                            if result.severity == ValidationSeverity.CRITICAL:
                                break
                        else:
                            results['data'][check_name] = {
                                'passed': True,
                                'message': result.message,
                                'details': result.details
                            }
                            
                    except asyncio.TimeoutError:
                        self.logger.warning(f"Validation check {check_name} timed out")
                        results['success'] = False
                        results['warnings'].append(f"Validation check {check_name} timed out")
            
            # Calculate aggregate scores
            if results['success']:
                results['data']['aggregate_scores'] = await self._calculate_basic_scores(
                    opportunity_data, results['data']
                )
            
            # Cache result
            if self.config.cache_results:
                self._validation_cache[cache_key] = (results, time.time())
            
            duration = time.time() - start_time
            self.logger.debug(f"Basic validation completed in {duration:.3f}s")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Basic validation error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {},
                'warnings': [f"Validation system error: {str(e)}"],
                'checks_performed': []
            }
    
    async def validate_advanced_checks(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform advanced pre-trade validation checks
        
        Args:
            opportunity_data: Opportunity to validate
            user_preferences: User-specific preferences
            
        Returns:
            Dict containing validation results
        """
        start_time = time.time()
        opportunity_id = opportunity_data.get('id', 'unknown')
        
        self.logger.debug(f"Starting advanced validation for {opportunity_id}")
        
        results = {
            'success': True,
            'data': {},
            'warnings': [],
            'checks_performed': []
        }
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(opportunity_data, 'advanced')
            if self.config.cache_results and cache_key in self._validation_cache:
                cached_result, timestamp = self._validation_cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    self.logger.debug(f"Using cached advanced validation for {opportunity_id}")
                    return cached_result
            
            # Run advanced validation checks
            validation_tasks = []
            
            for check_name, check_config in self._validation_checks.items():
                if not check_config.get('enabled', False):
                    continue
                    
                # Only run advanced checks
                if check_name not in ['risk_assessment', 'liquidity_analysis', 
                                    'volatility_estimation', 'timing_analysis',
                                    'execution_feasibility', 'bookmaker_limits', 'market_conditions']:
                    continue
                
                if self.config.parallel_checks:
                    task = asyncio.create_task(
                        self._run_validation_check(check_name, check_config, opportunity_data, user_preferences)
                    )
                    validation_tasks.append((check_name, task))
                else:
                    result = await self._run_validation_check(check_name, check_config, opportunity_data, user_preferences)
                    results['checks_performed'].append(check_name)
                    
                    if not result.passed:
                        results['success'] = False
                        results['data'][check_name] = {
                            'passed': False,
                            'message': result.message,
                            'severity': result.severity.value
                        }
                    else:
                        results['data'][check_name] = {
                            'passed': True,
                            'message': result.message,
                            'details': result.details
                        }
            
            # Process parallel tasks if enabled
            if self.config.parallel_checks:
                for check_name, task in validation_tasks:
                    try:
                        result = await asyncio.wait_for(task, timeout=self.config.validation_timeout)
                        results['checks_performed'].append(check_name)
                        
                        results['data'][check_name] = {
                            'passed': result.passed,
                            'message': result.message,
                            'details': result.details
                        }
                        
                        if not result.passed:
                            results['success'] = False
                            
                    except asyncio.TimeoutError:
                        self.logger.warning(f"Advanced validation check {check_name} timed out")
                        results['warnings'].append(f"Validation check {check_name} timed out")
            
            # Calculate advanced metrics
            if results['success']:
                results['data']['advanced_metrics'] = await self._calculate_advanced_metrics(
                    opportunity_data, results['data']
                )
            
            # Cache result
            if self.config.cache_results:
                self._validation_cache[cache_key] = (results, time.time())
            
            duration = time.time() - start_time
            self.logger.debug(f"Advanced validation completed in {duration:.3f}s")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Advanced validation error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {},
                'warnings': [f"Advanced validation error: {str(e)}"],
                'checks_performed': []
            }
    
    async def _run_validation_check(
        self,
        check_name: str,
        check_config: Dict[str, Any],
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> ValidationResult:
        """Execute a specific validation check"""
        
        validation_function = check_config.get('validation_function')
        if not validation_function:
            return ValidationResult(
                check_name=check_name,
                passed=False,
                severity=ValidationSeverity.ERROR,
                message=f"No validation function for {check_name}"
            )
        
        try:
            # Call the validation function
            if asyncio.iscoroutinefunction(validation_function):
                result = await validation_function(opportunity_data, user_preferences)
            else:
                result = validation_function(opportunity_data, user_preferences)
            
            # Ensure result is ValidationResult
            if isinstance(result, bool):
                result = ValidationResult(
                    check_name=check_name,
                    passed=result,
                    severity=ValidationSeverity.WARNING if not result else ValidationSeverity.INFO,
                    message="Validation check completed"
                )
            elif isinstance(result, dict):
                result = ValidationResult(
                    check_name=check_name,
                    passed=result.get('passed', False),
                    severity=ValidationSeverity(result.get('severity', 'info')),
                    message=result.get('message', ''),
                    details=result.get('details', {}),
                    risk_impact=result.get('risk_impact', 0.0)
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Validation check {check_name} failed: {str(e)}")
            return ValidationResult(
                check_name=check_name,
                passed=False,
                severity=ValidationSeverity.ERROR,
                message=f"Validation check failed: {str(e)}"
            )
    
    def _validate_opportunity_format(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate opportunity data format"""
        
        required_fields = ['id', 'profit_margin', 'legs']
        missing_fields = []
        
        for field in required_fields:
            if field not in opportunity_data:
                missing_fields.append(field)
        
        if missing_fields:
            return ValidationResult(
                check_name='opportunity_format',
                passed=False,
                severity=ValidationSeverity.ERROR,
                message=f"Missing required fields: {', '.join(missing_fields)}",
                details={'missing_fields': missing_fields}
            )
        
        # Validate legs structure
        legs = opportunity_data.get('legs', [])
        if not isinstance(legs, list) or len(legs) < 2:
            return ValidationResult(
                check_name='opportunity_format',
                passed=False,
                severity=ValidationSeverity.ERROR,
                message="Opportunity must have at least 2 legs",
                details={'legs_count': len(legs) if isinstance(legs, list) else 0}
            )
        
        return ValidationResult(
            check_name='opportunity_format',
            passed=True,
            severity=ValidationSeverity.INFO,
            message="Opportunity format is valid",
            details={'legs_count': len(legs)}
        )
    
    def _validate_profit_margin(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate profit margin is within acceptable range"""
        
        profit_margin = opportunity_data.get('profit_margin', 0.0)
        
        if not isinstance(profit_margin, (int, float)):
            return ValidationResult(
                check_name='profit_margin',
                passed=False,
                severity=ValidationSeverity.ERROR,
                message="Profit margin must be numeric"
            )
        
        min_profit = 0.5  # 0.5%
        max_profit = 50.0  # 50%
        
        if profit_margin < min_profit:
            return ValidationResult(
                check_name='profit_margin',
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Profit margin {profit_margin}% below minimum {min_profit}%",
                details={'profit_margin': profit_margin, 'min_profit': min_profit}
            )
        
        if profit_margin > max_profit:
            return ValidationResult(
                check_name='profit_margin',
                passed=False,
                severity=ValidationSeverity.WARNING,
                message=f"Profit margin {profit_margin}% above maximum {max_profit}%",
                details={'profit_margin': profit_margin, 'max_profit': max_profit}
            )
        
        return ValidationResult(
            check_name='profit_margin',
            passed=True,
            severity=ValidationSeverity.INFO,
            message=f"Profit margin {profit_margin}% is within acceptable range",
            details={'profit_margin': profit_margin}
        )
    
    def _validate_odds(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate odds are within acceptable range"""
        
        legs = opportunity_data.get('legs', [])
        if not isinstance(legs, list):
            return ValidationResult(
                check_name='odds_validation',
                passed=False,
                severity=ValidationSeverity.ERROR,
                message="Invalid legs structure"
            )
        
        min_odds = 1.01
        max_odds = 100.0
        invalid_odds = []
        
        for i, leg in enumerate(legs):
            if not isinstance(leg, dict):
                invalid_odds.append(f"leg_{i}_not_dict")
                continue
            
            odds = leg.get('odds')
            if not isinstance(odds, (int, float)):
                invalid_odds.append(f"leg_{i}_invalid_odds")
                continue
            
            if odds < min_odds or odds > max_odds:
                invalid_odds.append(f"leg_{i}_out_of_range")
        
        if invalid_odds:
            return ValidationResult(
                check_name='odds_validation',
                passed=False,
                severity=ValidationSeverity.ERROR,
                message=f"Invalid odds found: {', '.join(invalid_odds)}",
                details={'invalid_legs': invalid_odds}
            )
        
        return ValidationResult(
            check_name='odds_validation',
            passed=True,
            severity=ValidationSeverity.INFO,
            message="All odds are valid",
            details={'legs_count': len(legs)}
        )
    
    def _validate_stake_calculations(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate stake calculations are correct"""
        
        legs = opportunity_data.get('legs', [])
        if not isinstance(legs, list) or len(legs) < 2:
            return ValidationResult(
                check_name='stake_calculations',
                passed=False,
                severity=ValidationSeverity.ERROR,
                message="Insufficient legs for stake calculation"
            )
        
        # Check if stakes are provided
        stakes_provided = all(leg.get('stake') for leg in legs if isinstance(leg, dict))
        
        if not stakes_provided:
            return ValidationResult(
                check_name='stake_calculations',
                passed=True,  # Not critical - stakes can be calculated
                severity=ValidationSeverity.INFO,
                message="Stakes not provided - will be calculated",
                details={'stakes_calculated': True}
            )
        
        # Validate stake calculations (basic check)
        total_stakes = sum(leg.get('stake', 0) for leg in legs if isinstance(leg, dict))
        
        if total_stakes <= 0:
            return ValidationResult(
                check_name='stake_calculations',
                passed=False,
                severity=ValidationSeverity.ERROR,
                message="Total stake must be positive"
            )
        
        return ValidationResult(
            check_name='stake_calculations',
            passed=True,
            severity=ValidationSeverity.INFO,
            message="Stake calculations appear valid",
            details={'total_stake': total_stakes, 'legs_count': len(legs)}
        )
    
    async def _perform_risk_assessment(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Perform comprehensive risk assessment"""
        
        # This would integrate with risk models and historical data
        # For now, provide a simplified assessment
        
        legs = opportunity_data.get('legs', [])
        profit_margin = opportunity_data.get('profit_margin', 0.0)
        
        # Risk factors
        risk_factors = []
        risk_score = 0.0
        
        # High profit margin can indicate higher risk
        if profit_margin > 10.0:
            risk_factors.append("High profit margin")
            risk_score += 20.0
        
        # Multiple legs increase complexity
        if len(legs) > 3:
            risk_factors.append("Multiple legs increase complexity")
            risk_score += 15.0
        
        # Check for unusual patterns in odds
        odds_values = [leg.get('odds', 0) for leg in legs if isinstance(leg, dict)]
        if odds_values:
            avg_odds = sum(odds_values) / len(odds_values)
            if avg_odds < 2.0 or avg_odds > 10.0:
                risk_factors.append("Unusual average odds")
                risk_score += 10.0
        
        # Determine if risk level is acceptable
        max_acceptable_risk = self.config.max_risk_score
        risk_acceptable = risk_score <= max_acceptable_risk
        
        return ValidationResult(
            check_name='risk_assessment',
            passed=risk_acceptable,
            severity=ValidationSeverity.WARNING if not risk_acceptable else ValidationSeverity.INFO,
            message=f"Risk assessment completed - score: {risk_score:.1f}",
            details={
                'risk_score': risk_score,
                'max_acceptable_risk': max_acceptable_risk,
                'risk_factors': risk_factors
            },
            risk_impact=risk_score
        )
    
    async def _analyze_liquidity(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Analyze liquidity constraints"""
        
        legs = opportunity_data.get('legs', [])
        liquidity_issues = []
        liquidity_score = 100.0
        
        # Check bookmaker-specific liquidity
        for i, leg in enumerate(legs):
            if not isinstance(leg, dict):
                continue
            
            bookmaker = leg.get('bookmaker', 'unknown')
            odds = leg.get('odds', 0)
            
            # Simple liquidity estimation based on bookmaker and odds
            # In reality, this would check actual market depth
            if bookmaker in ['DraftKings', 'FanDuel'] and odds > 5.0:
                liquidity_issues.append(f"Low liquidity for {bookmaker} at odds {odds}")
                liquidity_score -= 20.0
            
            if odds > 20.0:
                liquidity_issues.append(f"Very high odds {odds} may indicate low liquidity")
                liquidity_score -= 15.0
        
        liquidity_acceptable = liquidity_score >= self.config.min_liquidity_score
        
        return ValidationResult(
            check_name='liquidity_analysis',
            passed=liquidity_acceptable,
            severity=ValidationSeverity.WARNING if not liquidity_acceptable else ValidationSeverity.INFO,
            message=f"Liquidity analysis completed - score: {liquidity_score:.1f}",
            details={
                'liquidity_score': liquidity_score,
                'min_required': self.config.min_liquidity_score,
                'liquidity_issues': liquidity_issues
            },
            risk_impact=max(0, 100 - liquidity_score)
        )
    
    async def _estimate_volatility(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Estimate price volatility"""
        
        legs = opportunity_data.get('legs', [])
        volatility_indicators = []
        volatility_score = 50.0  # Baseline
        
        # Analyze odds volatility
        odds_values = [leg.get('odds', 0) for leg in legs if isinstance(leg, dict)]
        if len(odds_values) >= 2:
            odds_range = max(odds_values) - min(odds_values)
            avg_odds = sum(odds_values) / len(odds_values)
            
            if odds_range / avg_odds > 0.5:  # High relative range
                volatility_indicators.append("High odds volatility")
                volatility_score += 20.0
        
        # Sports-specific volatility
        sport = opportunity_data.get('sport', '')
        if sport in ['esports', 'politics', 'entertainment']:
            volatility_indicators.append(f"{sport} markets are inherently volatile")
            volatility_score += 15.0
        
        return ValidationResult(
            check_name='volatility_estimation',
            passed=True,  # Volatility is informational
            severity=ValidationSeverity.INFO,
            message=f"Volatility estimation completed - score: {volatility_score:.1f}",
            details={
                'volatility_score': volatility_score,
                'volatility_indicators': volatility_indicators,
                'estimated_range': 'high' if volatility_score > 70 else 'medium' if volatility_score > 50 else 'low'
            }
        )
    
    async def _analyze_timing(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Analyze timing factors"""
        
        timing_factors = []
        timing_score = 80.0  # Assume good timing initially
        
        # Check event timing
        event_time = opportunity_data.get('event_time')
        if event_time:
            try:
                event_datetime = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
                time_to_event = (event_datetime - datetime.utcnow()).total_seconds()
                
                if time_to_event < 300:  # Less than 5 minutes
                    timing_factors.append("Event starting very soon")
                    timing_score -= 20.0
                elif time_to_event > 86400:  # More than 24 hours
                    timing_factors.append("Event far in future - odds may change")
                    timing_score -= 10.0
            except:
                timing_factors.append("Unable to parse event time")
                timing_score -= 10.0
        
        # Check market activity
        is_live = opportunity_data.get('is_live', False)
        if is_live:
            timing_factors.append("Live betting - faster execution required")
            timing_score -= 15.0
        
        return ValidationResult(
            check_name='timing_analysis',
            passed=timing_score >= 50.0,
            severity=ValidationSeverity.INFO,
            message=f"Timing analysis completed - score: {timing_score:.1f}",
            details={
                'timing_score': timing_score,
                'timing_factors': timing_factors,
                'urgency_level': 'high' if timing_score < 60 else 'medium' if timing_score < 80 else 'low'
            }
        )
    
    async def _check_execution_feasibility(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Check if opportunity can be executed"""
        
        feasibility_issues = []
        feasibility_score = 100.0
        
        # Check bookmaker availability
        legs = opportunity_data.get('legs', [])
        for leg in legs:
            if not isinstance(leg, dict):
                continue
            
            bookmaker = leg.get('bookmaker', '')
            # Simulate checking bookmaker availability
            if bookmaker in ['DraftKings', 'FanDuel']:
                feasibility_issues.append(f"{bookmaker} may have restrictions")
                feasibility_score -= 25.0
        
        # Check profit margin feasibility
        profit_margin = opportunity_data.get('profit_margin', 0.0)
        if profit_margin < 1.0:
            feasibility_issues.append("Very low profit margin - execution costs may exceed profit")
            feasibility_score -= 30.0
        
        return ValidationResult(
            check_name='execution_feasibility',
            passed=feasibility_score >= 60.0,
            severity=ValidationSeverity.WARNING if feasibility_score < 80.0 else ValidationSeverity.INFO,
            message=f"Execution feasibility: {feasibility_score:.1f}%",
            details={
                'feasibility_score': feasibility_score,
                'feasibility_issues': feasibility_issues
            }
        )
    
    async def _check_bookmaker_limits(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Check bookmaker-specific limits"""
        
        limit_issues = []
        limit_compliance = True
        
        legs = opportunity_data.get('legs', [])
        for leg in legs:
            if not isinstance(leg, dict):
                continue
            
            bookmaker = leg.get('bookmaker', '')
            stake = leg.get('stake', 0)
            
            # Simulate bookmaker limit checking
            bookmaker_limits = {
                'Bet365': 1000.0,
                'WilliamHill': 500.0,
                'DraftKings': 200.0,
                'Betfair': 2000.0
            }
            
            if bookmaker in bookmaker_limits:
                limit = bookmaker_limits[bookmaker]
                if stake > limit:
                    limit_issues.append(f"{bookmaker} stake {stake} exceeds limit {limit}")
                    limit_compliance = False
        
        return ValidationResult(
            check_name='bookmaker_limits',
            passed=limit_compliance,
            severity=ValidationSeverity.ERROR if not limit_compliance else ValidationSeverity.INFO,
            message="Bookmaker limits checked",
            details={
                'limit_compliance': limit_compliance,
                'limit_issues': limit_issues
            }
        )
    
    async def _analyze_market_conditions(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Analyze current market conditions"""
        
        market_conditions = {}
        conditions_score = 80.0
        
        # Simulate market condition analysis
        sport = opportunity_data.get('sport', '')
        time_of_day = datetime.utcnow().hour
        
        # Some sports are more volatile at certain times
        if sport == 'soccer' and 18 <= time_of_day <= 22:
            market_conditions['peak_hours'] = True
            conditions_score -= 10.0  # Peak hours can be more volatile
        
        if sport == 'basketball' and time_of_day < 8:
            market_conditions['off_hours'] = True
            conditions_score -= 5.0
        
        return ValidationResult(
            check_name='market_conditions',
            passed=True,
            severity=ValidationSeverity.INFO,
            message=f"Market conditions analysis completed - score: {conditions_score:.1f}",
            details={
                'conditions_score': conditions_score,
                'market_conditions': market_conditions
            }
        )
    
    async def _calculate_basic_scores(
        self,
        opportunity_data: Dict[str, Any],
        validation_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate aggregate scores from basic validation"""
        
        scores = {
            'format_score': 100.0 if validation_data.get('opportunity_format', {}).get('passed') else 0.0,
            'profit_score': self._calculate_profit_score(opportunity_data.get('profit_margin', 0.0)),
            'odds_score': self._calculate_odds_score(validation_data.get('odds_validation', {})),
            'stake_score': self._calculate_stake_score(validation_data.get('stake_calculations', {}))
        }
        
        # Calculate overall basic score
        scores['overall_basic_score'] = sum(scores.values()) / len(scores)
        
        return scores
    
    async def _calculate_advanced_metrics(
        self,
        opportunity_data: Dict[str, Any],
        validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate advanced metrics from validation results"""
        
        metrics = {}
        
        # Extract scores from individual checks
        risk_assessment = validation_data.get('risk_assessment', {})
        liquidity_analysis = validation_data.get('liquidity_analysis', {})
        timing_analysis = validation_data.get('timing_analysis', {})
        execution_feasibility = validation_data.get('execution_feasibility', {})
        
        metrics['risk_score'] = risk_assessment.get('details', {}).get('risk_score', 0.0)
        metrics['liquidity_score'] = liquidity_analysis.get('details', {}).get('liquidity_score', 0.0)
        metrics['timing_score'] = timing_analysis.get('details', {}).get('timing_score', 0.0)
        metrics['feasibility_score'] = execution_feasibility.get('details', {}).get('feasibility_score', 0.0)
        
        # Calculate composite scores
        metrics['composite_risk_score'] = (
            metrics['risk_score'] * 0.3 +
            (100 - metrics['liquidity_score']) * 0.2 +
            (100 - metrics['timing_score']) * 0.2 +
            (100 - metrics['feasibility_score']) * 0.3
        )
        
        return metrics
    
    def _calculate_profit_score(self, profit_margin: float) -> float:
        """Calculate score based on profit margin"""
        if profit_margin < 0.5:
            return 0.0
        elif profit_margin > 20.0:
            return 90.0  # Cap at 90% - very high margins can be suspicious
        else:
            return min(100.0, profit_margin * 5.0)  # Linear scaling
    
    def _calculate_odds_score(self, odds_validation: Dict[str, Any]) -> float:
        """Calculate score based on odds validation"""
        if not odds_validation.get('passed', False):
            return 0.0
        return 100.0
    
    def _calculate_stake_score(self, stake_validation: Dict[str, Any]) -> float:
        """Calculate score based on stake validation"""
        if not stake_validation.get('passed', False):
            return 0.0
        return 100.0
    
    def _generate_cache_key(self, opportunity_data: Dict[str, Any], validation_type: str) -> str:
        """Generate cache key for opportunity"""
        import hashlib
        import json
        
        # Create a simplified opportunity signature
        signature = {
            'id': opportunity_data.get('id'),
            'profit_margin': opportunity_data.get('profit_margin'),
            'legs_count': len(opportunity_data.get('legs', [])),
            'type': validation_type
        }
        
        signature_str = json.dumps(signature, sort_keys=True)
        return hashlib.md5(signature_str.encode()).hexdigest()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self._performance_stats.copy()
    
    def clear_cache(self):
        """Clear validation cache"""
        self._validation_cache.clear()
        self.logger.info("Validation cache cleared")
    
    def get_validation_summary(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of validation status"""
        cache_key = self._generate_cache_key(opportunity_data, 'basic')
        
        summary = {
            'cached': cache_key in self._validation_cache,
            'validation_rules_count': len(self._validation_checks),
            'configuration': {
                'basic_validation_enabled': self.config.enable_basic_validation,
                'advanced_validation_enabled': self.config.enable_advanced_validation,
                'parallel_checks': self.config.parallel_checks,
                'cache_enabled': self.config.cache_results
            }
        }
        
        if cache_key in self._validation_cache:
            cached_result, timestamp = self._validation_cache[cache_key]
            summary['cache_age_seconds'] = time.time() - timestamp
            summary['cached_result_summary'] = {
                'success': cached_result.get('success', False),
                'checks_performed': len(cached_result.get('checks_performed', [])),
                'warnings_count': len(cached_result.get('warnings', []))
            }
        
        return summary