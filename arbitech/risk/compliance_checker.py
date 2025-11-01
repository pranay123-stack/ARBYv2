"""
Compliance Checker - Regulatory Compliance Validation System

This module provides comprehensive regulatory compliance checking including:
- Jurisdictional rules validation
- Responsible gambling controls
- Audit requirements compliance
- Regional restrictions checking
- Legal framework compliance
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json

# Import from other modules
# from .safety_pipeline import RiskLevel, ValidationStatus, ValidationRule


class ComplianceLevel(Enum):
    """Compliance level enumeration"""
    NOT_REQUIRED = "not_required"
    BASIC = "basic"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    STRICT = "strict"
    FORBIDDEN = "forbidden"


class RegulatoryRegion(Enum):
    """Major regulatory regions"""
    US_FEDERAL = "us_federal"
    US_STATE = "us_state"
    EU = "eu"
    UK = "uk"
    AU = "au"
    CA = "ca"
    OTHER = "other"


class ComplianceStatus(Enum):
    """Compliance check status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    REQUIRES_REVIEW = "requires_review"
    RESTRICTED = "restricted"
    PROHIBITED = "prohibited"
    UNKNOWN = "unknown"


@dataclass
class ComplianceRule:
    """Individual compliance rule definition"""
    rule_id: str
    name: str
    region: RegulatoryRegion
    compliance_level: ComplianceLevel
    description: str
    enabled: bool = True
    priority: int = 100
    enforcement_action: str = "block"  # "block", "warn", "monitor", "log"
    required_documentation: List[str] = field(default_factory=list)
    violation_penalty: Optional[str] = None
    
    def __post_init__(self):
        if self.priority < 1 or self.priority > 1000:
            raise ValueError("Priority must be between 1 and 1000")


@dataclass
class ComplianceCheck:
    """Individual compliance check result"""
    rule_id: str
    rule_name: str
    status: ComplianceStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    evidence_required: List[str] = field(default_factory=list)
    documentation_provided: List[str] = field(default_factory=list)
    compliance_score: float = 0.0
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ComplianceReport:
    """Comprehensive compliance report"""
    opportunity_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    overall_status: ComplianceStatus
    overall_score: float = 0.0
    
    # Regional analysis
    applicable_regions: List[RegulatoryRegion] = field(default_factory=list)
    region_compliance: Dict[str, ComplianceStatus] = field(default_factory=dict)
    
    # Detailed checks
    checks: List[ComplianceCheck] = field(default_factory=list)
    
    # Compliance categories
    jurisdiction_compliance: ComplianceStatus = ComplianceStatus.UNKNOWN
    responsible_gambling_compliance: ComplianceStatus = ComplianceStatus.UNKNOWN
    audit_compliance: ComplianceStatus = ComplianceStatus.UNKNOWN
    
    # Requirements
    documentation_required: List[str] = field(default_factory=list)
    approvals_required: List[str] = field(default_factory=list)
    monitoring_required: List[str] = field(default_factory=list)
    
    # Actions required
    immediate_actions: List[str] = field(default_factory=list)
    corrective_actions: List[str] = field(default_factory=list)
    preventive_actions: List[str] = field(default_factory=list)
    
    # Audit trail
    compliance_officer: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    review_notes: List[str] = field(default_factory=list)


@dataclass
class ComplianceConfig:
    """Comprehensive compliance configuration"""
    # Global settings
    strict_mode: bool = False
    require_all_approvals: bool = True
    auto_escalation: bool = True
    
    # Regional settings
    primary_region: RegulatoryRegion = RegulatoryRegion.US_FEDERAL
    secondary_regions: List[RegulatoryRegion] = field(default_factory=list)
    region_specific_rules: Dict[RegulatoryRegion, Dict[str, Any]] = field(default_factory=dict)
    
    # Responsible gambling
    enable_gambling_controls: bool = True
    max_stake_by_user_type: Dict[str, float] = field(default_factory=dict)
    session_limits: Dict[str, Any] = field(default_factory=dict)
    self_exclusion_support: bool = True
    
    # Audit requirements
    enable_audit_logging: bool = True
    require_transaction_audit: bool = True
    require_user_verification: bool = True
    data_retention_period: int = 2555  # 7 years in days
    
    # Performance settings
    compliance_timeout: float = 30.0
    parallel_checks: bool = True
    cache_results: bool = True
    
    # Documentation requirements
    required_documents: List[str] = field(default_factory=list)
    verification_methods: List[str] = field(default_factory=list)


class ComplianceChecker:
    """
    Regulatory Compliance Validation System
    
    Provides comprehensive compliance checking including:
    - Jurisdiction-specific regulatory validation
    - Responsible gambling controls and limits
    - Audit requirements and documentation
    - Regional restrictions and licensing
    - Legal framework compliance
    """
    
    def __init__(self, config: Optional[ComplianceConfig] = None):
        """
        Initialize compliance checker
        
        Args:
            config: Compliance configuration
        """
        self.config = config or ComplianceConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize compliance rules
        self._compliance_rules = self._initialize_compliance_rules()
        
        # Initialize jurisdiction knowledge base
        self._jurisdiction_rules = self._initialize_jurisdiction_rules()
        
        # Initialize responsible gambling controls
        self._gambling_controls = self._initialize_gambling_controls()
        
        # Performance tracking
        self._performance_stats = {
            'total_compliance_checks': 0,
            'compliance_violations': 0,
            'regions_monitored': set(),
            'average_check_time': 0.0
        }
        
        # Compliance cache
        self._compliance_cache = {}
        self._cache_ttl = 600  # 10 minutes
        
        self.logger.info("Compliance Checker initialized")
    
    def _initialize_compliance_rules(self) -> Dict[str, ComplianceRule]:
        """Initialize all compliance rules"""
        rules = {}
        
        # US Federal Rules
        rules['us_federal_合法性'] = ComplianceRule(
            rule_id='us_federal_legality',
            name='Federal Legality Check',
            region=RegulatoryRegion.US_FEDERAL,
            compliance_level=ComplianceLevel.STRICT,
            description='Verify arbitrage betting legality under federal law',
            enforcement_action='block',
            required_documentation=['federal_legal_opinion'],
            violation_penalty='Immediate trade blocking'
        )
        
        rules['us_federal_patriot_act'] = ComplianceRule(
            rule_id='us_federal_patriot_act',
            name='USA PATRIOT Act Compliance',
            region=RegulatoryRegion.US_FEDERAL,
            compliance_level=ComplianceLevel.STRICT,
            description='Anti-money laundering compliance',
            priority=1,
            enforcement_action='block',
            required_documentation=['aml_screening', 'customer_verification'],
            violation_penalty='Account suspension'
        )
        
        # US State Rules
        rules['us_state_licensed'] = ComplianceRule(
            rule_id='us_state_licensed',
            name='State Licensing Verification',
            region=RegulatoryRegion.US_STATE,
            compliance_level=ComplianceLevel.STRICT,
            description='Verify state-specific licensing requirements',
            enforcement_action='block',
            required_documentation=['state_license', 'operator_permit'],
            violation_penalty='Legal action'
        )
        
        rules['us_state_restrictions'] = ComplianceRule(
            rule_id='us_state_restrictions',
            name='State Betting Restrictions',
            region=RegulatoryRegion.US_STATE,
            compliance_level=ComplianceLevel.ENHANCED,
            description='Check state-specific betting restrictions',
            enforcement_action='block',
            violation_penalty='Legal penalties'
        )
        
        # EU Rules
        rules['eu_licensed_operator'] = ComplianceRule(
            rule_id='eu_licensed_operator',
            name='EU Licensed Operator Verification',
            region=RegulatoryRegion.EU,
            compliance_level=ComplianceLevel.STRICT,
            description='Verify operator holds valid EU gambling license',
            enforcement_action='block',
            required_documentation=['eu_license', 'operator_certificate'],
            violation_penalty='Regulatory action'
        )
        
        rules['eu_gdpr_compliance'] = ComplianceRule(
            rule_id='eu_gdpr_compliance',
            name='GDPR Data Protection Compliance',
            region=RegulatoryRegion.EU,
            compliance_level=ComplianceLevel.STRICT,
            description='GDPR data protection and privacy compliance',
            priority=1,
            enforcement_action='block',
            required_documentation=['privacy_policy', 'data_processing_agreement'],
            violation_penalty='GDPR fines'
        )
        
        # UK Rules
        rules['uk_ukgc_compliance'] = ComplianceRule(
            rule_id='uk_ukgc_compliance',
            name='UKGC Regulatory Compliance',
            region=RegulatoryRegion.UK,
            compliance_level=ComplianceLevel.STRICT,
            description='UK Gambling Commission regulatory compliance',
            enforcement_action='block',
            required_documentation=['ukgc_license', 'regulatory_report'],
            violation_penalty='License revocation'
        )
        
        rules['uk_affordability_checks'] = ComplianceRule(
            rule_id='uk_affordability_checks',
            name='Affordability Assessment',
            region=RegulatoryRegion.UK,
            compliance_level=ComplianceLevel.ENHANCED,
            description='Verify customer can afford to gamble responsibly',
            enforcement_action='monitor',
            required_documentation=['affordability_assessment', 'income_verification'],
            violation_penalty='Account restrictions'
        )
        
        # Australia Rules
        rules['au_acl_compliance'] = ComplianceRule(
            rule_id='au_acl_compliance',
            name='Australian Consumer Law Compliance',
            region=RegulatoryRegion.AU,
            compliance_level=ComplianceLevel.STRICT,
            description='ACL compliance for Australian consumers',
            enforcement_action='block',
            required_documentation=['acl_compliance_certificate'],
            violation_penalty='ACCC action'
        )
        
        # Responsible Gambling Rules
        rules['responsible_gambling_limits'] = ComplianceRule(
            rule_id='responsible_gambling_limits',
            name='Responsible Gambling Limit Enforcement',
            region=RegulatoryRegion.OTHER,
            compliance_level=ComplianceLevel.ENHANCED,
            description='Enforce responsible gambling limits and controls',
            enforcement_action='block',
            violation_penalty='Account suspension'
        )
        
        rules['self_exclusion_check'] = ComplianceRule(
            rule_id='self_exclusion_check',
            name='Self-Exclusion Database Check',
            region=RegulatoryRegion.OTHER,
            compliance_level=ComplianceLevel.STRICT,
            description='Check against national self-exclusion databases',
            priority=1,
            enforcement_action='block',
            violation_penalty='Legal action'
        )
        
        # Audit Rules
        rules['transaction_audit'] = ComplianceRule(
            rule_id='transaction_audit',
            name='Transaction Audit Trail',
            region=RegulatoryRegion.OTHER,
            compliance_level=ComplianceLevel.STANDARD,
            description='Maintain comprehensive transaction audit trail',
            enforcement_action='log',
            required_documentation=['audit_trail', 'transaction_records'],
            violation_penalty='Regulatory fine'
        )
        
        rules['reporting_compliance'] = ComplianceRule(
            rule_id='reporting_compliance',
            name='Regulatory Reporting Compliance',
            region=RegulatoryRegion.OTHER,
            compliance_level=ComplianceLevel.ENHANCED,
            description='Comply with regulatory reporting requirements',
            enforcement_action='monitor',
            required_documentation=['regulatory_reports', 'compliance_certificates'],
            violation_penalty='Regulatory action'
        )
        
        return rules
    
    def _initialize_jurisdiction_rules(self) -> Dict[RegulatoryRegion, Dict[str, Any]]:
        """Initialize jurisdiction-specific rules and restrictions"""
        return {
            RegulatoryRegion.US_FEDERAL: {
                'arbitrage_legality': {
                    'legal': False,  # Generally illegal
                    'restrictions': ['Wire Act', 'Unlawful Internet Gambling Enforcement Act'],
                    'exemptions': ['State licensed operations', 'Legal sports betting states']
                },
                'betting_limits': {
                    'max_stake': 2000.0,
                    'max_daily_loss': 10000.0,
                    'weekly_limits': True
                },
                'required_licenses': ['Federal gaming license', 'State gaming license']
            },
            
            RegulatoryRegion.US_STATE: {
                'legal_states': ['NV', 'NJ', 'PA', 'WV', 'CO', 'TN', 'MI', 'VA', 'IA', 'IN', 'IL', 'WY', 'MT', 'NH', 'OR', 'LA', 'AZ'],
                'restricted_states': ['WA', 'ID', 'UT'],
                'arbitrage_policies': {
                    'allowed': False,
                    'penalties': ['Account closure', 'Fund seizure']
                },
                'reporting_requirements': ['Monthly compliance reports', 'Suspicious activity reports']
            },
            
            RegulatoryRegion.EU: {
                'arbitrage_policies': {
                    'allowed': True,
                    'restrictions': ['Fair play requirements', 'Anti-fraud measures']
                },
                'gdpr_requirements': {
                    'data_protection': True,
                    'consent_required': True,
                    'right_to_erasure': True
                },
                'consumer_protection': {
                    'cooling_off_period': 14,  # days
                    'complaint_procedures': True,
                    'dispute_resolution': True
                }
            },
            
            RegulatoryRegion.UK: {
                'arbitrage_policies': {
                    'allowed': True,
                    'conditions': ['Fair and transparent practices', 'No market manipulation']
                },
                'affordability_checks': {
                    'required': True,
                    'frequency': 'quarterly',
                    'thresholds': {'monthly_income': 1000, 'net_worth': 5000}
                },
                'gamstop_compliance': True  # National self-exclusion scheme
            },
            
            RegulatoryRegion.AU: {
                'arbitrage_policies': {
                    'allowed': False,  # Generally prohibited
                    'penalties': ['Account closure', 'Fines up to AUD 1.8M']
                },
                'responsible_gambling': {
                    'mandatory_limits': True,
                    'reality_checks': True,
                    'self_exclusion_support': True
                }
            },
            
            RegulatoryRegion.CA: {
                'arbitrage_policies': {
                    'allowed': False,
                    'restrictions': ['Provincial regulations vary']
                },
                'consumer_protection': {
                    'cooling_off_period': 30,  # days
                    'dispute_resolution': True
                }
            }
        }
    
    def _initialize_gambling_controls(self) -> Dict[str, Any]:
        """Initialize responsible gambling controls"""
        return {
            'stake_limits': {
                'daily': 1000.0,
                'weekly': 5000.0,
                'monthly': 20000.0
            },
            'loss_limits': {
                'daily': 500.0,
                'weekly': 2000.0,
                'monthly': 5000.0
            },
            'session_controls': {
                'max_session_duration': 180,  # minutes
                'reality_check_interval': 60,  # minutes
                'break_requirement': 15  # minutes
            },
            'affordability_checks': {
                'required_for_stakes_above': 200.0,
                'documentation_required': ['income_proof', 'bank_statements'],
                'review_frequency': 'monthly'
            },
            'self_exclusion': {
                'database_check': True,
                'cooling_off_period': 24,  # hours
                'minimum_exclusion_period': 6  # months
            },
            'problem_gambling_indicators': {
                'chasing_losses': True,
                'increasing_stakes': True,
                'neglecting_responsibilities': True,
                'borrowing_money': True
            }
        }
    
    async def validate_jurisdiction(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate jurisdiction-specific compliance
        
        Args:
            opportunity_data: Opportunity data
            user_preferences: User preferences and location
            
        Returns:
            Dict containing jurisdiction validation results
        """
        start_time = time.time()
        opportunity_id = opportunity_data.get('id', 'unknown')
        
        self.logger.debug(f"Starting jurisdiction validation for {opportunity_id}")
        
        results = {
            'success': True,
            'data': {
                'applicable_regions': [],
                'region_compliance': {},
                'jurisdiction_risk': False,
                'compliance_score': 100.0
            },
            'warnings': [],
            'critical_issues': []
        }
        
        try:
            # Determine applicable regions
            user_location = user_preferences.get('location', {}) if user_preferences else {}
            applicable_regions = self._determine_applicable_regions(user_location, opportunity_data)
            results['data']['applicable_regions'] = [region.value for region in applicable_regions]
            
            # Check compliance for each applicable region
            region_compliance = {}
            compliance_score = 100.0
            
            for region in applicable_regions:
                region_result = await self._check_region_compliance(region, opportunity_data, user_preferences)
                region_compliance[region.value] = region_result
                
                # Update overall compliance score
                if not region_result['compliant']:
                    compliance_score -= 30.0
                    results['data']['jurisdiction_risk'] = True
                    
                    if region_result.get('prohibited', False):
                        results['critical_issues'].append(f"Activity prohibited in {region.value}")
            
            results['data']['region_compliance'] = region_compliance
            results['data']['compliance_score'] = max(0.0, compliance_score)
            
            # Check for cross-border issues
            cross_border_issues = await self._check_cross_border_compliance(
                applicable_regions, opportunity_data, user_preferences
            )
            
            if cross_border_issues:
                results['warnings'].extend(cross_border_issues)
            
            # Update performance stats
            self._performance_stats['total_compliance_checks'] += 1
            self._performance_stats['regions_monitored'].update(applicable_regions)
            
            duration = time.time() - start_time
            self._update_average_check_time(duration)
            
            self.logger.debug(f"Jurisdiction validation completed in {duration:.3f}s")
            return results
            
        except Exception as e:
            self.logger.error(f"Jurisdiction validation error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {
                    'jurisdiction_risk': True,
                    'compliance_score': 0.0
                },
                'warnings': [f"Jurisdiction validation failed: {str(e)}"],
                'critical_issues': ["Unable to verify jurisdictional compliance"]
            }
    
    async def validate_responsible_gambling(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate responsible gambling controls
        
        Args:
            opportunity_data: Opportunity data
            user_preferences: User preferences and gambling history
            
        Returns:
            Dict containing responsible gambling validation results
        """
        start_time = time.time()
        opportunity_id = opportunity_data.get('id', 'unknown')
        
        self.logger.debug(f"Starting responsible gambling validation for {opportunity_id}")
        
        results = {
            'success': True,
            'data': {
                'gambling_controls': {},
                'user_risk_assessment': {},
                'limit_compliance': {},
                'protection_measures': []
            },
            'warnings': [],
            'critical_issues': []
        }
        
        try:
            if not self.config.enable_gambling_controls:
                return {
                    'success': True,
                    'data': {'controls_disabled': True},
                    'warnings': ['Responsible gambling controls disabled'],
                    'critical_issues': []
                }
            
            # Check self-exclusion status
            self_exclusion_result = await self._check_self_exclusion(user_preferences)
            if self_exclusion_result['excluded']:
                return {
                    'success': False,
                    'data': {'self_exclusion': True},
                    'warnings': [],
                    'critical_issues': [f"User is self-excluded: {self_exclusion_result['reason']}"]
                }
            
            # Validate stake limits
            stake_validation = await self._validate_stake_limits(opportunity_data, user_preferences)
            results['data']['limit_compliance'] = stake_validation
            
            if not stake_validation['compliant']:
                results['warnings'].append(f"Stake limit violation: {stake_validation['violation']}")
            
            # Check affordability
            affordability_check = await self._check_affordability(opportunity_data, user_preferences)
            results['data']['user_risk_assessment'] = affordability_check
            
            if affordability_check.get('high_risk', False):
                results['warnings'].append("User may be at high risk for problem gambling")
            
            # Validate session controls
            session_validation = await self._validate_session_controls(user_preferences)
            results['data']['gambling_controls'] = session_validation
            
            # Generate protection measures
            protection_measures = await self._generate_protection_measures(
                stake_validation, affordability_check, session_validation
            )
            results['data']['protection_measures'] = protection_measures
            
            # Check for problem gambling indicators
            problem_gambling_indicators = await self._check_problem_gambling_indicators(
                user_preferences
            )
            
            if problem_gambling_indicators['detected']:
                results['warnings'].extend(problem_gambling_indicators['warnings'])
            
            duration = time.time() - start_time
            self.logger.debug(f"Responsible gambling validation completed in {duration:.3f}s")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Responsible gambling validation error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {'validation_failed': True},
                'warnings': [f"Responsible gambling validation failed: {str(e)}"],
                'critical_issues': []
            }
    
    async def validate_audit_requirements(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate audit requirements and documentation
        
        Args:
            opportunity_data: Opportunity data
            user_preferences: User preferences and compliance history
            
        Returns:
            Dict containing audit validation results
        """
        start_time = time.time()
        opportunity_id = opportunity_data.get('id', 'unknown')
        
        self.logger.debug(f"Starting audit validation for {opportunity_id}")
        
        results = {
            'success': True,
            'data': {
                'audit_trail_complete': True,
                'documentation_status': {},
                'compliance_certificates': {},
                'reporting_status': {}
            },
            'warnings': [],
            'critical_issues': []
        }
        
        try:
            if not self.config.enable_audit_logging:
                return {
                    'success': True,
                    'data': {'audit_logging_disabled': True},
                    'warnings': ['Audit logging disabled'],
                    'critical_issues': []
                }
            
            # Validate transaction audit trail
            audit_trail_status = await self._validate_audit_trail(opportunity_data, user_preferences)
            results['data']['audit_trail_complete'] = audit_trail_status['complete']
            
            if not audit_trail_status['complete']:
                results['warnings'].append(f"Incomplete audit trail: {audit_trail_status['missing']}")
            
            # Check documentation requirements
            documentation_status = await self._check_documentation_requirements(
                opportunity_data, user_preferences
            )
            results['data']['documentation_status'] = documentation_status
            
            missing_docs = [doc for doc, status in documentation_status.items() if not status['available']]
            if missing_docs:
                results['warnings'].append(f"Missing documentation: {', '.join(missing_docs)}")
            
            # Validate compliance certificates
            certificates_status = await self._validate_compliance_certificates(
                opportunity_data, user_preferences
            )
            results['data']['compliance_certificates'] = certificates_status
            
            # Check reporting requirements
            reporting_status = await self._validate_reporting_requirements(
                opportunity_data, user_preferences
            )
            results['data']['reporting_status'] = reporting_status
            
            # Generate audit trail entry
            await self._generate_audit_entry(opportunity_data, results)
            
            duration = time.time() - start_time
            self.logger.debug(f"Audit validation completed in {duration:.3f}s")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Audit validation error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {'audit_validation_failed': True},
                'warnings': [f"Audit validation failed: {str(e)}"],
                'critical_issues': []
            }
    
    def _determine_applicable_regions(
        self,
        user_location: Dict[str, Any],
        opportunity_data: Dict[str, Any]
    ) -> List[RegulatoryRegion]:
        """Determine which regulatory regions apply to this opportunity"""
        
        regions = [self.config.primary_region]
        
        # Add user location regions
        country = user_location.get('country', '').upper()
        state = user_location.get('state', '').upper()
        
        # Map country to regions
        country_mapping = {
            'US': [RegulatoryRegion.US_FEDERAL, RegulatoryRegion.US_STATE],
            'UK': [RegulatoryRegion.UK],
            'GB': [RegulatoryRegion.UK],
            'DE': [RegulatoryRegion.EU],
            'FR': [RegulatoryRegion.EU],
            'IT': [RegulatoryRegion.EU],
            'ES': [RegulatoryRegion.EU],
            'AU': [RegulatoryRegion.AU],
            'CA': [RegulatoryRegion.CA]
        }
        
        if country in country_mapping:
            regions.extend(country_mapping[country])
        
        # Add secondary regions from config
        regions.extend(self.config.secondary_regions)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_regions = []
        for region in regions:
            if region not in seen:
                seen.add(region)
                unique_regions.append(region)
        
        return unique_regions
    
    async def _check_region_compliance(
        self,
        region: RegulatoryRegion,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check compliance for a specific region"""
        
        region_rules = self._jurisdiction_rules.get(region, {})
        
        if not region_rules:
            return {'compliant': True, 'prohibited': False, 'issues': []}
        
        # Check arbitrage policies
        arbitrage_policy = region_rules.get('arbitrage_policies', {})
        arbitrage_allowed = arbitrage_policy.get('allowed', True)
        
        if not arbitrage_allowed:
            return {
                'compliant': False,
                'prohibited': True,
                'issues': [f"Arbitrage betting prohibited in {region.value}"],
                'penalties': arbitrage_policy.get('penalties', [])
            }
        
        # Check betting limits
        betting_limits = region_rules.get('betting_limits', {})
        profit_margin = opportunity_data.get('profit_margin', 0.0)
        
        # For this example, we'll check if profit margin seems reasonable
        if profit_margin > 20.0:  # Suspiciously high
            return {
                'compliant': True,
                'prohibited': False,
                'issues': [f"High profit margin may indicate risk in {region.value}"],
                'warnings': ['Unusual profit margin detected']
            }
        
        return {
            'compliant': True,
            'prohibited': False,
            'issues': [],
            'warnings': []
        }
    
    async def _check_cross_border_compliance(
        self,
        regions: List[RegulatoryRegion],
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Check for cross-border compliance issues"""
        
        issues = []
        
        # Check if multiple regions have conflicting requirements
        if len(regions) > 1:
            # EU + US might have conflicts
            has_us = RegulatoryRegion.US_FEDERAL in regions or RegulatoryRegion.US_STATE in regions
            has_eu = RegulatoryRegion.EU in regions
            
            if has_us and has_eu:
                issues.append("Cross-border operation between US and EU - additional compliance required")
        
        return issues
    
    async def _check_self_exclusion(
        self,
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check if user is self-excluded"""
        
        if not user_preferences:
            return {'excluded': False, 'reason': None}
        
        # Simulate self-exclusion database check
        user_id = user_preferences.get('user_id')
        excluded_users = ['user_123', 'user_456']  # Simulated
        
        if user_id in excluded_users:
            return {
                'excluded': True,
                'reason': 'User in national self-exclusion database',
                'exclusion_date': '2024-01-15',
                'remaining_period': '5 months'
            }
        
        return {'excluded': False, 'reason': None}
    
    async def _validate_stake_limits(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate user stake limits"""
        
        if not user_preferences:
            return {'compliant': True, 'violation': None}
        
        # Calculate suggested total stake
        legs = opportunity_data.get('legs', [])
        total_suggested_stake = sum(leg.get('stake', 0) for leg in legs if isinstance(leg, dict))
        
        # Get user limits
        user_limits = user_preferences.get('limits', {})
        daily_limit = user_limits.get('daily_stake_limit', 1000.0)
        
        # Check against daily limit
        if total_suggested_stake > daily_limit:
            return {
                'compliant': False,
                'violation': f"Suggested stake {total_suggested_stake} exceeds daily limit {daily_limit}",
                'suggested_stake': daily_limit,
                'excess_amount': total_suggested_stake - daily_limit
            }
        
        return {
            'compliant': True,
            'violation': None,
            'suggested_stake': total_suggested_stake,
            'remaining_daily_limit': daily_limit - total_suggested_stake
        }
    
    async def _check_affordability(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check user affordability for gambling"""
        
        if not user_preferences:
            return {'assessed': False, 'high_risk': False}
        
        # Simulate affordability assessment
        user_income = user_preferences.get('monthly_income', 5000.0)
        user_expenses = user_preferences.get('monthly_expenses', 3000.0)
        disposable_income = user_income - user_expenses
        
        # Calculate suggested stake impact
        legs = opportunity_data.get('legs', [])
        total_stake = sum(leg.get('stake', 0) for leg in legs if isinstance(leg, dict))
        
        # Risk assessment based on stake vs disposable income
        stake_percentage = (total_stake / max(disposable_income, 1)) * 100
        
        if stake_percentage > 10.0:  # More than 10% of disposable income
            return {
                'assessed': True,
                'high_risk': True,
                'stake_percentage': stake_percentage,
                'recommendation': 'Consider reducing stake size',
                'affordability_score': max(0, 100 - stake_percentage * 5)
            }
        
        return {
            'assessed': True,
            'high_risk': False,
            'stake_percentage': stake_percentage,
            'affordability_score': min(100, 100 - stake_percentage * 2)
        }
    
    async def _validate_session_controls(
        self,
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate session controls and limits"""
        
        if not user_preferences:
            return {'session_time_remaining': 180, 'break_required': False}
        
        # Simulate session tracking
        session_start = user_preferences.get('session_start_time')
        if session_start:
            try:
                session_datetime = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
                session_duration = (datetime.utcnow() - session_datetime).total_seconds() / 60
                max_session = self._gambling_controls['session_controls']['max_session_duration']
                
                if session_duration > max_session:
                    return {
                        'session_time_remaining': 0,
                        'break_required': True,
                        'session_duration': session_duration,
                        'recommendation': 'Take a mandatory break'
                    }
                
                return {
                    'session_time_remaining': max(0, max_session - session_duration),
                    'break_required': False,
                    'session_duration': session_duration
                }
                
            except:
                return {'session_time_remaining': 180, 'break_required': False}
        
        return {'session_time_remaining': 180, 'break_required': False}
    
    async def _check_problem_gambling_indicators(
        self,
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check for problem gambling indicators"""
        
        if not user_preferences:
            return {'detected': False, 'warnings': []}
        
        warnings = []
        
        # Simulate checking various indicators
        recent_losses = user_preferences.get('recent_losses', [])
        if len(recent_losses) > 5:
            warnings.append("Multiple consecutive losses detected")
        
        increasing_stakes = user_preferences.get('increasing_stake_trend', False)
        if increasing_stakes:
            warnings.append("Increasing stake pattern detected - potential chasing behavior")
        
        return {
            'detected': len(warnings) > 0,
            'warnings': warnings,
            'risk_level': 'high' if len(warnings) > 2 else 'medium' if len(warnings) > 0 else 'low'
        }
    
    async def _generate_protection_measures(
        self,
        stake_validation: Dict[str, Any],
        affordability_check: Dict[str, Any],
        session_validation: Dict[str, Any]
    ) -> List[str]:
        """Generate protection measures based on validation results"""
        
        measures = []
        
        if not stake_validation['compliant']:
            measures.append(f"Reduce stake to {stake_validation['suggested_stake']:.2f}")
        
        if affordability_check.get('high_risk', False):
            measures.append("Implement spending limit review")
        
        if session_validation.get('break_required', False):
            measures.append("Enforce mandatory break period")
        
        if affordability_check.get('affordability_score', 100) < 70:
            measures.append("Require additional financial verification")
        
        return measures
    
    async def _validate_audit_trail(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate audit trail completeness"""
        
        required_audit_elements = [
            'user_id', 'timestamp', 'opportunity_id', 'stake_amount',
            'expected_profit', 'bookmakers_involved', 'user_location'
        ]
        
        missing_elements = []
        for element in required_audit_elements:
            if element == 'user_id' and not user_preferences:
                missing_elements.append(element)
            elif element not in opportunity_data and element != 'user_id':
                missing_elements.append(element)
        
        return {
            'complete': len(missing_elements) == 0,
            'missing': missing_elements,
            'element_count': len(required_audit_elements) - len(missing_elements)
        }
    
    async def _check_documentation_requirements(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Check documentation requirements"""
        
        documentation_status = {}
        
        for doc_type in self.config.required_documents:
            # Simulate document availability check
            if doc_type == 'user_verification' and user_preferences:
                documentation_status[doc_type] = {
                    'available': user_preferences.get('verified', False),
                    'verification_date': user_preferences.get('verification_date')
                }
            elif doc_type == 'compliance_certificate':
                documentation_status[doc_type] = {
                    'available': True,
                    'expiry_date': '2025-12-31'
                }
            else:
                documentation_status[doc_type] = {
                    'available': True,
                    'status': 'current'
                }
        
        return documentation_status
    
    async def _validate_compliance_certificates(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate compliance certificates"""
        
        return {
            'gambling_license': {
                'valid': True,
                'expiry': '2025-12-31',
                'jurisdiction': 'UK'
            },
            'data_protection': {
                'compliant': True,
                'certificate': 'GDPR-2024-001',
                'last_audit': '2024-01-15'
            },
            'aml_certification': {
                'valid': True,
                'certificate': 'AML-2024-001',
                'expiry': '2025-06-30'
            }
        }
    
    async def _validate_reporting_requirements(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate reporting requirements"""
        
        return {
            'monthly_reports': {
                'submitted': True,
                'last_submission': '2024-10-01'
            },
            'suspicious_activity': {
                'flagged': False,
                'last_review': '2024-09-28'
            },
            'regulatory_updates': {
                'current': True,
                'last_update': '2024-09-15'
            }
        }
    
    async def _generate_audit_entry(
        self,
        opportunity_data: Dict[str, Any],
        results: Dict[str, Any]
    ):
        """Generate audit trail entry for this validation"""
        
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'opportunity_id': opportunity_data.get('id'),
            'validation_type': 'compliance',
            'results_summary': {
                'success': results['success'],
                'warnings_count': len(results['warnings']),
                'critical_issues_count': len(results['critical_issues'])
            },
            'compliance_score': results['data'].get('compliance_score', 0.0)
        }
        
        # In a real implementation, this would write to an audit database
        self.logger.info(f"Audit entry generated: {json.dumps(audit_entry, indent=2)}")
    
    def _update_average_check_time(self, duration: float):
        """Update average compliance check time"""
        total_checks = self._performance_stats['total_compliance_checks']
        current_avg = self._performance_stats['average_check_time']
        self._performance_stats['average_check_time'] = (
            (current_avg * (total_checks - 1) + duration) / total_checks
        ) if total_checks > 0 else duration
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = self._performance_stats.copy()
        stats['regions_monitored'] = list(stats['regions_monitored'])
        return stats
    
    def get_compliance_rules(self) -> Dict[str, ComplianceRule]:
        """Get all compliance rules"""
        return self._compliance_rules.copy()
    
    def update_compliance_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update a specific compliance rule"""
        if rule_id not in self._compliance_rules:
            return False
        
        rule = self._compliance_rules[rule_id]
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
            else:
                self.logger.warning(f"Unknown rule attribute: {key}")
                return False
        
        self.logger.info(f"Updated compliance rule: {rule_id}")
        return True
    
    def generate_compliance_report(
        self,
        opportunity_data: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> ComplianceReport:
        """Generate comprehensive compliance report"""
        
        report = ComplianceReport(
            opportunity_id=opportunity_data.get('id', 'unknown'),
            overall_status=ComplianceStatus.COMPLIANT if validation_results['success'] else ComplianceStatus.NON_COMPLIANT,
            overall_score=validation_results['data'].get('compliance_score', 0.0)
        )
        
        # Extract region information
        applicable_regions = validation_results['data'].get('applicable_regions', [])
        for region_str in applicable_regions:
            try:
                region = RegulatoryRegion(region_str)
                report.applicable_regions.append(region)
                report.region_compliance[region_str] = ComplianceStatus.COMPLIANT
            except ValueError:
                self.logger.warning(f"Unknown region: {region_str}")
        
        return report
    
    def clear_cache(self):
        """Clear compliance cache"""
        self._compliance_cache.clear()
        self.logger.info("Compliance cache cleared")