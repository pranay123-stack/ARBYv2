"""
Safety Monitor - Real-Time Safety Monitoring System

This module provides comprehensive real-time safety monitoring including:
- Continuous risk assessment
- Anomaly detection for unusual patterns
- Proactive intervention capabilities
- Real-time alerting and notifications
- Behavioral analysis and monitoring
"""

import asyncio
import logging
import time
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import statistics

# Statistical imports for anomaly detection
from collections import deque, defaultdict
import math


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MonitoringStatus(Enum):
    """Monitoring status"""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""
    PRICE_VOLATILITY = "price_volatility"
    UNUSUAL_VOLUME = "unusual_volume"
    PATTERN_DEVIATION = "pattern_deviation"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    SYSTEM_ANOMALY = "system_anomaly"
    REGULATORY_CONCERN = "regulatory_concern"


@dataclass
class SafetyMetric:
    """Individual safety metric data point"""
    metric_name: str
    value: float
    timestamp: datetime
    threshold: Optional[float] = None
    status: str = "normal"  # normal, warning, critical
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyAlert:
    """Anomaly detection alert"""
    alert_id: str
    anomaly_type: AnomalyType
    severity: AlertSeverity
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_timestamp: Optional[datetime] = None
    actions_taken: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class SafetyEvent:
    """Safety event for audit trail"""
    event_id: str
    event_type: str
    severity: AlertSeverity
    description: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "safety_monitor"
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    follow_up_required: bool = False


@dataclass
class InterventionAction:
    """Proactive intervention action"""
    action_id: str
    trigger_type: str
    action_type: str  # "block", "limit", "alert", "review", "suspend"
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    auto_execute: bool = True
    confirmation_required: bool = False
    escalation_level: int = 1


@dataclass
class MonitoringConfig:
    """Real-time monitoring configuration"""
    # General settings
    monitoring_enabled: bool = True
    real_time_interval: float = 1.0  # seconds
    alert_cooldown: float = 300.0    # 5 minutes
    
    # Anomaly detection settings
    enable_anomaly_detection: bool = True
    statistical_window_size: int = 100
    anomaly_threshold_multiplier: float = 2.5
    min_data_points: int = 20
    
    # Behavioral monitoring
    enable_behavioral_analysis: bool = True
    behavioral_baseline_period: int = 1440  # 24 hours in minutes
    behavioral_deviation_threshold: float = 0.3
    
    # Risk monitoring
    continuous_risk_assessment: bool = True
    risk_threshold_warning: float = 60.0
    risk_threshold_critical: float = 80.0
    auto_escalation: bool = True
    
    # Alert settings
    enable_real_time_alerts: bool = True
    alert_channels: List[str] = field(default_factory=lambda: ["log", "email"])
    max_alerts_per_hour: int = 50
    
    # Performance settings
    max_metrics_per_second: int = 1000
    metric_retention_hours: int = 24
    alert_retention_days: int = 30
    
    # Integration settings
    external_alert_webhooks: List[str] = field(default_factory=list)
    regulatory_reporting_enabled: bool = True


class SafetyMonitor:
    """
    Real-Time Safety Monitoring System
    
    Provides comprehensive real-time monitoring including:
    - Continuous risk assessment and scoring
    - Advanced anomaly detection algorithms
    - Proactive intervention capabilities
    - Real-time alerting and notifications
    - Behavioral pattern analysis
    - Performance and system monitoring
    """
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        """
        Initialize safety monitor
        
        Args:
            config: Monitoring configuration
        """
        self.config = config or MonitoringConfig()
        self.logger = logging.getLogger(__name__)
        
        # Monitoring state
        self.status = MonitoringStatus.ACTIVE
        self._monitoring_task = None
        self._monitoring_active = False
        
        # Metric storage
        self._metrics = defaultdict(lambda: deque(maxlen=1000))
        self._alert_history = deque(maxlen=10000)
        self._safety_events = deque(maxlen=5000)
        
        # Anomaly detection models
        self._anomaly_models = self._initialize_anomaly_models()
        
        # Behavioral baselines
        self._behavioral_baselines = {}
        self._behavioral_data = defaultdict(lambda: deque(maxlen=10000))
        
        # Alert management
        self._active_alerts = {}
        self._alert_cooldowns = {}
        self._suppressed_alerts = set()
        
        # Intervention system
        self._intervention_triggers = self._initialize_intervention_triggers()
        self._intervention_history = deque(maxlen=1000)
        
        # Performance tracking
        self._performance_stats = {
            'total_checks': 0,
            'anomalies_detected': 0,
            'interventions_executed': 0,
            'alerts_generated': 0,
            'uptime_percentage': 0.0,
            'average_response_time': 0.0
        }
        
        # Rate limiting
        self._check_rate_tracker = deque(maxlen=1000)
        
        self.logger.info("Safety Monitor initialized")
    
    def _initialize_anomaly_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize anomaly detection models"""
        return {
            'price_volatility': {
                'type': 'statistical',
                'method': 'z_score',
                'sensitivity': 2.0,
                'window_size': 50
            },
            'volume_anomaly': {
                'type': 'statistical',
                'method': 'iqr',
                'sensitivity': 1.5,
                'window_size': 100
            },
            'pattern_deviation': {
                'type': 'machine_learning',
                'method': 'isolation_forest',
                'sensitivity': 0.1,
                'contamination': 0.1
            },
            'behavioral_anomaly': {
                'type': 'behavioral',
                'method': 'baseline_deviation',
                'sensitivity': 0.3,
                'baseline_period': 168  # 1 week in hours
            },
            'system_anomaly': {
                'type': 'system',
                'method': 'threshold_breach',
                'thresholds': {
                    'cpu_usage': 80.0,
                    'memory_usage': 85.0,
                    'error_rate': 5.0,
                    'response_time': 5.0
                }
            }
        }
    
    def _initialize_intervention_triggers(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize intervention trigger configurations"""
        return {
            'high_risk_score': [
                {
                    'threshold': 85.0,
                    'action': 'block_trading',
                    'severity': 'high',
                    'auto_execute': True
                },
                {
                    'threshold': 75.0,
                    'action': 'increase_monitoring',
                    'severity': 'medium',
                    'auto_execute': True
                }
            ],
            'anomaly_detected': [
                {
                    'types': ['price_volatility', 'pattern_deviation'],
                    'severity': 'high',
                    'action': 'pause_opportunities',
                    'duration_minutes': 30,
                    'auto_execute': False
                }
            ],
            'behavioral_deviation': [
                {
                    'threshold': 0.5,
                    'action': 'require_verification',
                    'severity': 'medium',
                    'auto_execute': True
                }
            ],
            'system_issues': [
                {
                    'conditions': ['high_error_rate', 'slow_response'],
                    'action': 'emergency_shutdown',
                    'severity': 'critical',
                    'auto_execute': True
                }
            ]
        }
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        if self._monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self._monitoring_active = True
        self.status = MonitoringStatus.ACTIVE
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Real-time monitoring started")
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        self._monitoring_active = False
        self.status = MonitoringStatus.PAUSED
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Real-time monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("Starting monitoring loop")
        
        while self._monitoring_active:
            try:
                # Check rate limit
                if not self._check_rate_limit():
                    await asyncio.sleep(self.config.real_time_interval)
                    continue
                
                start_time = time.time()
                
                # Update behavioral baselines
                if self.config.enable_behavioral_analysis:
                    await self._update_behavioral_baselines()
                
                # Perform continuous risk assessment
                if self.config.continuous_risk_assessment:
                    await self._continuous_risk_assessment()
                
                # Check for anomalies
                if self.config.enable_anomaly_detection:
                    await self._check_anomalies()
                
                # Process intervention triggers
                await self._process_intervention_triggers()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                # Update performance stats
                duration = time.time() - start_time
                self._update_performance_stats(duration)
                
                # Sleep until next interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.config.real_time_interval - elapsed)
                await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                self.status = MonitoringStatus.ERROR
                await asyncio.sleep(5)  # Brief pause before retry
        
        self.logger.info("Monitoring loop stopped")
    
    async def check_real_time_safety(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check real-time safety for an opportunity
        
        Args:
            opportunity_data: Opportunity data
            user_preferences: User preferences
            
        Returns:
            Dict containing real-time safety assessment
        """
        start_time = time.time()
        opportunity_id = opportunity_data.get('id', 'unknown')
        
        self.logger.debug(f"Starting real-time safety check for {opportunity_id}")
        
        results = {
            'success': True,
            'data': {
                'safety_score': 100.0,
                'risk_factors': [],
                'anomalies_detected': [],
                'interventions_required': False,
                'monitoring_status': self.status.value
            },
            'warnings': [],
            'critical_issues': []
        }
        
        try:
            # Check current system status
            if self.status != MonitoringStatus.ACTIVE:
                results['warnings'].append(f"Monitoring status: {self.status.value}")
            
            # Perform real-time risk assessment
            risk_assessment = await self._perform_real_time_risk_assessment(
                opportunity_data, user_preferences
            )
            results['data']['safety_score'] = risk_assessment.get('safety_score', 100.0)
            results['data']['risk_factors'] = risk_assessment.get('risk_factors', [])
            
            # Check for current anomalies
            current_anomalies = await self._get_current_anomalies(
                opportunity_data, user_preferences
            )
            results['data']['anomalies_detected'] = current_anomalies
            
            if current_anomalies:
                results['warnings'].append(f"Detected {len(current_anomalies)} anomalies")
            
            # Check intervention requirements
            interventions = await self._check_intervention_requirements(
                opportunity_data, user_preferences, risk_assessment, current_anomalies
            )
            results['data']['interventions_required'] = len(interventions) > 0
            
            if interventions:
                results['critical_issues'].append(
                    f"Interventions required: {', '.join(interventions)}"
                )
            
            # Check system health
            system_health = await self._check_system_health()
            results['data']['system_health'] = system_health
            
            if not system_health.get('healthy', True):
                results['warnings'].append("System health issues detected")
            
            duration = time.time() - start_time
            self.logger.debug(f"Real-time safety check completed in {duration:.3f}s")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Real-time safety check error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {
                    'safety_score': 0.0,
                    'interventions_required': True,
                    'monitoring_error': True
                },
                'warnings': [f"Real-time safety check failed: {str(e)}"],
                'critical_issues': ["Unable to verify real-time safety"]
            }
    
    async def detect_anomalies(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect anomalies in opportunity data
        
        Args:
            opportunity_data: Opportunity data
            user_preferences: User preferences
            
        Returns:
            Dict containing anomaly detection results
        """
        start_time = time.time()
        opportunity_id = opportunity_data.get('id', 'unknown')
        
        self.logger.debug(f"Starting anomaly detection for {opportunity_id}")
        
        results = {
            'success': True,
            'data': {
                'anomalies': [],
                'anomaly_scores': {},
                'detection_confidence': 0.0
            },
            'warnings': [],
            'critical_issues': []
        }
        
        try:
            if not self.config.enable_anomaly_detection:
                return {
                    'success': True,
                    'data': {'anomaly_detection_disabled': True},
                    'warnings': ['Anomaly detection disabled'],
                    'critical_issues': []
                }
            
            anomalies = []
            anomaly_scores = {}
            
            # Price volatility anomaly detection
            price_anomaly = await self._detect_price_volatility_anomaly(
                opportunity_data
            )
            if price_anomaly['detected']:
                anomalies.append(price_anomaly)
            anomaly_scores['price_volatility'] = price_anomaly.get('score', 0.0)
            
            # Volume anomaly detection
            volume_anomaly = await self._detect_volume_anomaly(
                opportunity_data, user_preferences
            )
            if volume_anomaly['detected']:
                anomalies.append(volume_anomaly)
            anomaly_scores['volume_anomaly'] = volume_anomaly.get('score', 0.0)
            
            # Pattern deviation detection
            pattern_anomaly = await self._detect_pattern_deviation_anomaly(
                opportunity_data
            )
            if pattern_anomaly['detected']:
                anomalies.append(pattern_anomaly)
            anomaly_scores['pattern_deviation'] = pattern_anomaly.get('score', 0.0)
            
            # Behavioral anomaly detection
            if self.config.enable_behavioral_analysis:
                behavioral_anomaly = await self._detect_behavioral_anomaly(
                    opportunity_data, user_preferences
                )
                if behavioral_anomaly['detected']:
                    anomalies.append(behavioral_anomaly)
                anomaly_scores['behavioral_anomaly'] = behavioral_anomaly.get('score', 0.0)
            
            # System anomaly detection
            system_anomaly = await self._detect_system_anomaly()
            if system_anomaly['detected']:
                anomalies.append(system_anomaly)
            anomaly_scores['system_anomaly'] = system_anomaly.get('score', 0.0)
            
            # Calculate overall detection confidence
            detection_confidence = (
                sum(anomaly_scores.values()) / len(anomaly_scores)
                if anomaly_scores else 0.0
            )
            
            results['data']['anomalies'] = anomalies
            results['data']['anomaly_scores'] = anomaly_scores
            results['data']['detection_confidence'] = detection_confidence
            
            # Generate alerts for significant anomalies
            significant_anomalies = [
                anomaly for anomaly in anomalies
                if anomaly.get('severity') in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]
            ]
            
            if significant_anomalies:
                await self._generate_anomaly_alerts(significant_anomalies)
                results['warnings'].append(
                    f"Generated {len(significant_anomalies)} critical anomaly alerts"
                )
            
            duration = time.time() - start_time
            self.logger.debug(f"Anomaly detection completed in {duration:.3f}s")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Anomaly detection error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {'anomaly_detection_failed': True},
                'warnings': [f"Anomaly detection failed: {str(e)}"],
                'critical_issues': []
            }
    
    async def check_proactive_intervention(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check if proactive intervention is required
        
        Args:
            opportunity_data: Opportunity data
            user_preferences: User preferences
            
        Returns:
            Dict containing intervention assessment
        """
        start_time = time.time()
        opportunity_id = opportunity_data.get('id', 'unknown')
        
        self.logger.debug(f"Checking proactive intervention for {opportunity_id}")
        
        results = {
            'success': True,
            'data': {
                'intervention_required': False,
                'intervention_type': None,
                'intervention_actions': [],
                'escalation_level': 0
            },
            'warnings': [],
            'critical_issues': []
        }
        
        try:
            # Get current risk assessment
            risk_assessment = await self._perform_real_time_risk_assessment(
                opportunity_data, user_preferences
            )
            
            # Get current anomalies
            anomalies = await self._get_current_anomalies(
                opportunity_data, user_preferences
            )
            
            # Get behavioral analysis
            behavioral_analysis = {}
            if self.config.enable_behavioral_analysis:
                behavioral_analysis = await self._analyze_behavioral_patterns(
                    opportunity_data, user_preferences
                )
            
            # Check intervention triggers
            interventions = await self._evaluate_intervention_triggers(
                risk_assessment, anomalies, behavioral_analysis
            )
            
            if interventions:
                results['data']['intervention_required'] = True
                results['data']['intervention_actions'] = interventions
                results['data']['escalation_level'] = max(
                    intervention.get('escalation_level', 1) for intervention in interventions
                )
                
                # Determine primary intervention type
                intervention_types = [i.get('action_type') for i in interventions]
                if intervention_types:
                    results['data']['intervention_type'] = intervention_types[0]
                
                results['critical_issues'].append(
                    f"Proactive intervention required: {', '.join(intervention_types)}"
                )
                
                # Auto-execute immediate interventions
                await self._execute_auto_interventions(interventions)
            
            duration = time.time() - start_time
            self.logger.debug(f"Proactive intervention check completed in {duration:.3f}s")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Proactive intervention check error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {'intervention_check_failed': True},
                'warnings': [f"Intervention check failed: {str(e)}"],
                'critical_issues': []
            }
    
    async def _continuous_risk_assessment(self):
        """Perform continuous risk assessment"""
        
        # Update overall system risk score
        system_risk_factors = []
        
        # Check current anomalies
        current_anomalies = [alert for alert in self._active_alerts.values()
                           if not alert.resolved and alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]]
        
        if len(current_anomalies) > 0:
            system_risk_factors.append(f"{len(current_anomalies)} active high-severity anomalies")
        
        # Check system health
        system_health = await self._check_system_health()
        if not system_health.get('healthy', True):
            system_risk_factors.append("System health issues")
        
        # Store risk assessment metric
        risk_score = min(100.0, len(current_anomalies) * 20.0 + (0 if system_health.get('healthy', True) else 30.0))
        
        risk_metric = SafetyMetric(
            metric_name='system_risk_score',
            value=risk_score,
            timestamp=datetime.utcnow(),
            status='critical' if risk_score > 80 else 'warning' if risk_score > 60 else 'normal'
        )
        
        self._add_metric(risk_metric)
    
    async def _check_anomalies(self):
        """Check for various types of anomalies"""
        
        current_time = datetime.utcnow()
        
        # Price volatility anomaly detection
        await self._analyze_price_volatility()
        
        # Volume anomaly detection
        await self._analyze_volume_patterns()
        
        # System performance anomaly detection
        await self._analyze_system_performance()
        
        # Behavioral anomaly detection
        if self.config.enable_behavioral_analysis:
            await self._analyze_behavioral_patterns_background()
    
    async def _perform_real_time_risk_assessment(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform real-time risk assessment for opportunity"""
        
        risk_factors = []
        safety_score = 100.0
        
        # Check opportunity-specific risk factors
        profit_margin = opportunity_data.get('profit_margin', 0.0)
        if profit_margin > 15.0:
            risk_factors.append("High profit margin detected")
            safety_score -= 20.0
        
        # Check against current anomalies
        opportunity_anomalies = [alert for alert in self._active_alerts.values()
                               if not alert.resolved and 
                               alert.details.get('opportunity_id') == opportunity_data.get('id')]
        
        if opportunity_anomalies:
            risk_factors.append(f"{len(opportunity_anomalies)} opportunity-specific anomalies")
            safety_score -= 15.0 * len(opportunity_anomalies)
        
        # Check system-wide risk factors
        system_risk_metric = self._get_latest_metric('system_risk_score')
        if system_risk_metric and system_risk_metric.value > 70:
            risk_factors.append("High system-wide risk")
            safety_score -= 25.0
        
        return {
            'safety_score': max(0.0, safety_score),
            'risk_factors': risk_factors,
            'opportunity_anomalies': len(opportunity_anomalies)
        }
    
    async def _get_current_anomalies(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get current anomalies relevant to opportunity"""
        
        relevant_anomalies = []
        opportunity_id = opportunity_data.get('id')
        
        for alert_id, alert in self._active_alerts.items():
            if alert.resolved:
                continue
            
            # Check if anomaly is relevant to this opportunity
            if (alert.details.get('opportunity_id') == opportunity_id or
                alert.details.get('bookmaker') in [leg.get('bookmaker') for leg in opportunity_data.get('legs', [])] or
                alert.anomaly_type in [AnomalyType.SYSTEM_ANOMALY, AnomalyType.REGULATORY_CONCERN]):
                
                relevant_anomalies.append({
                    'alert_id': alert_id,
                    'type': alert.anomaly_type.value,
                    'severity': alert.severity.value,
                    'description': alert.description,
                    'confidence': alert.confidence_score,
                    'timestamp': alert.timestamp.isoformat()
                })
        
        return relevant_anomalies
    
    async def _detect_price_volatility_anomaly(
        self,
        opportunity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect price volatility anomalies"""
        
        legs = opportunity_data.get('legs', [])
        if len(legs) < 2:
            return {'detected': False, 'type': 'price_volatility'}
        
        # Extract odds values
        odds_values = []
        for leg in legs:
            if isinstance(leg, dict) and 'odds' in leg:
                odds_values.append(leg['odds'])
        
        if len(odds_values) < 2:
            return {'detected': False, 'type': 'price_volatility'}
        
        # Calculate volatility metrics
        odds_range = max(odds_values) - min(odds_values)
        avg_odds = sum(odds_values) / len(odds_values)
        coefficient_of_variation = odds_range / avg_odds if avg_odds > 0 else 0
        
        # Check historical volatility
        volatility_history = self._metrics.get('odds_volatility', deque())
        
        anomaly_detected = False
        severity = AlertSeverity.LOW
        score = 0.0
        
        if len(volatility_history) >= 10:
            historical_volatility = list(volatility_history)
            mean_volatility = statistics.mean(historical_volatility)
            std_volatility = statistics.stdev(historical_volatility) if len(historical_volatility) > 1 else 0
            
            if coefficient_of_variation > mean_volatility + 2 * std_volatility:
                anomaly_detected = True
                severity = AlertSeverity.MEDIUM
                score = min(100.0, (coefficient_of_variation - mean_volatility) * 10)
        
        # Very high coefficient of variation is always suspicious
        if coefficient_of_variation > 5.0:
            anomaly_detected = True
            severity = AlertSeverity.HIGH
            score = 80.0
        
        # Store current volatility
        current_volatility = SafetyMetric(
            metric_name='odds_volatility',
            value=coefficient_of_variation,
            timestamp=datetime.utcnow()
        )
        self._add_metric(current_volatility)
        
        return {
            'detected': anomaly_detected,
            'type': AnomalyType.PRICE_VOLATILITY,
            'severity': severity,
            'score': score,
            'details': {
                'coefficient_of_variation': coefficient_of_variation,
                'odds_range': odds_range,
                'average_odds': avg_odds,
                'threshold': '2 * std_dev + mean' if len(volatility_history) >= 10 else 'fixed threshold'
            }
        }
    
    async def _detect_volume_anomaly(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Detect volume anomalies"""
        
        # Simulate volume analysis based on opportunity characteristics
        legs = opportunity_data.get('legs', [])
        total_stake = sum(leg.get('stake', 0) for leg in legs if isinstance(leg, dict))
        
        # Check against historical volume patterns
        volume_history = self._metrics.get('opportunity_volume', deque())
        
        anomaly_detected = False
        severity = AlertSeverity.LOW
        score = 0.0
        
        if len(volume_history) >= 20:
            historical_volumes = list(volume_history)
            median_volume = statistics.median(historical_volumes)
            q75_volume = np.percentile(historical_volumes, 75)
            
            # Check if current volume is unusually high
            if total_stake > q75_volume * 3:  # 3x 75th percentile
                anomaly_detected = True
                severity = AlertSeverity.MEDIUM
                score = min(100.0, (total_stake / q75_volume - 3) * 20)
        
        # Unusual volume patterns
        if total_stake > 10000:  # Very large stake
            anomaly_detected = True
            severity = AlertSeverity.HIGH
            score = 90.0
        
        # Store volume metric
        volume_metric = SafetyMetric(
            metric_name='opportunity_volume',
            value=total_stake,
            timestamp=datetime.utcnow()
        )
        self._add_metric(volume_metric)
        
        return {
            'detected': anomaly_detected,
            'type': AnomalyType.UNUSUAL_VOLUME,
            'severity': severity,
            'score': score,
            'details': {
                'total_stake': total_stake,
                'legs_count': len(legs),
                'median_historical': statistics.median(list(volume_history)) if volume_history else 0
            }
        }
    
    async def _detect_pattern_deviation_anomaly(
        self,
        opportunity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect pattern deviation anomalies"""
        
        # Analyze opportunity patterns
        legs = opportunity_data.get('legs', [])
        profit_margin = opportunity_data.get('profit_margin', 0.0)
        
        # Check against known arbitrage patterns
        pattern_deviations = []
        
        # Check leg count
        if len(legs) > 5:  # Unusually many legs
            pattern_deviations.append("Unusually high number of legs")
        
        # Check profit margin consistency
        historical_profits = list(self._metrics.get('profit_margin', deque()))
        if len(historical_profits) >= 10:
            mean_profit = statistics.mean(historical_profits)
            std_profit = statistics.stdev(historical_profits) if len(historical_profits) > 1 else 0
            
            if abs(profit_margin - mean_profit) > 3 * std_profit:
                pattern_deviations.append("Profit margin deviates significantly from norm")
        
        # Check bookmaker diversity
        bookmakers = set(leg.get('bookmaker', '') for leg in legs if isinstance(leg, dict))
        if len(bookmakers) < 2:
            pattern_deviations.append("Single bookmaker opportunity - unusual")
        
        anomaly_detected = len(pattern_deviations) > 0
        severity = AlertSeverity.MEDIUM if len(pattern_deviations) > 1 else AlertSeverity.LOW
        score = min(100.0, len(pattern_deviations) * 30.0)
        
        # Store profit margin metric
        profit_metric = SafetyMetric(
            metric_name='profit_margin',
            value=profit_margin,
            timestamp=datetime.utcnow()
        )
        self._add_metric(profit_metric)
        
        return {
            'detected': anomaly_detected,
            'type': AnomalyType.PATTERN_DEVIATION,
            'severity': severity,
            'score': score,
            'details': {
                'deviations': pattern_deviations,
                'legs_count': len(legs),
                'bookmakers_count': len(bookmakers)
            }
        }
    
    async def _detect_behavioral_anomaly(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Detect behavioral anomalies"""
        
        if not user_preferences or not self.config.enable_behavioral_analysis:
            return {'detected': False, 'type': 'behavioral_anomaly'}
        
        user_id = user_preferences.get('user_id')
        if not user_id:
            return {'detected': False, 'type': 'behavioral_anomaly'}
        
        # Analyze user behavioral patterns
        behavioral_deviations = []
        
        # Check trading frequency
        user_trading_frequency = self._get_user_trading_frequency(user_id)
        typical_frequency = self._behavioral_baselines.get(f'{user_id}_frequency', 1.0)
        
        if user_trading_frequency > typical_frequency * 2:
            behavioral_deviations.append("Unusual increase in trading frequency")
        
        # Check stake size patterns
        user_stake_patterns = self._get_user_stake_patterns(user_id)
        typical_stake = self._behavioral_baselines.get(f'{user_id}_avg_stake', 100.0)
        
        if len(user_stake_patterns) > 0:
            recent_avg_stake = statistics.mean(list(user_stake_patterns)[-10:])
            if recent_avg_stake > typical_stake * 3:
                behavioral_deviations.append("Significantly increased stake sizes")
        
        anomaly_detected = len(behavioral_deviations) > 0
        severity = AlertSeverity.MEDIUM
        score = min(100.0, len(behavioral_deviations) * 40.0)
        
        return {
            'detected': anomaly_detected,
            'type': AnomalyType.BEHAVIORAL_ANOMALY,
            'severity': severity,
            'score': score,
            'details': {
                'deviations': behavioral_deviations,
                'user_id': user_id,
                'frequency_ratio': user_trading_frequency / max(typical_frequency, 0.1),
                'stake_ratio': (statistics.mean(list(user_stake_patterns)[-10:]) if user_stake_patterns else 0) / max(typical_stake, 0.1)
            }
        }
    
    async def _detect_system_anomaly(self) -> Dict[str, Any]:
        """Detect system performance anomalies"""
        
        # Simulate system metrics
        system_metrics = await self._get_system_metrics()
        
        anomalies = []
        
        # Check CPU usage
        if system_metrics.get('cpu_usage', 0) > 80:
            anomalies.append("High CPU usage")
        
        # Check memory usage
        if system_metrics.get('memory_usage', 0) > 85:
            anomalies.append("High memory usage")
        
        # Check error rate
        if system_metrics.get('error_rate', 0) > 5:
            anomalies.append("High error rate")
        
        # Check response time
        if system_metrics.get('avg_response_time', 0) > 5:
            anomalies.append("Slow response time")
        
        anomaly_detected = len(anomalies) > 0
        severity = AlertSeverity.HIGH if len(anomalies) > 1 else AlertSeverity.MEDIUM
        score = min(100.0, len(anomalies) * 25.0)
        
        return {
            'detected': anomaly_detected,
            'type': AnomalyType.SYSTEM_ANOMALY,
            'severity': severity,
            'score': score,
            'details': {
                'anomalies': anomalies,
                'system_metrics': system_metrics
            }
        }
    
    def _add_metric(self, metric: SafetyMetric):
        """Add metric to storage"""
        self._metrics[metric.metric_name].append(metric)
    
    def _get_latest_metric(self, metric_name: str) -> Optional[SafetyMetric]:
        """Get latest metric value"""
        metrics = self._metrics.get(metric_name, deque())
        return metrics[-1] if metrics else None
    
    def _check_rate_limit(self) -> bool:
        """Check if processing rate is within limits"""
        now = time.time()
        
        # Clean old timestamps
        self._check_rate_tracker = deque(
            [ts for ts in self._check_rate_tracker if now - ts < 1.0],
            maxlen=1000
        )
        
        # Check rate limit
        if len(self._check_rate_tracker) >= self.config.max_metrics_per_second:
            return False
        
        self._check_rate_tracker.append(now)
        return True
    
    async def _generate_anomaly_alerts(self, anomalies: List[Dict[str, Any]]):
        """Generate alerts for detected anomalies"""
        
        for anomaly in anomalies:
            alert_id = f"anomaly_{int(time.time())}_{np.random.randint(1000, 9999)}"
            
            # Check cooldown
            alert_type = anomaly.get('type', AnomalyType.SYSTEM_ANOMALY)
            if self._is_in_cooldown(alert_type):
                continue
            
            alert = AnomalyAlert(
                alert_id=alert_id,
                anomaly_type=alert_type,
                severity=anomaly.get('severity', AlertSeverity.MEDIUM),
                description=f"Anomaly detected: {anomaly.get('details', {})}",
                details=anomaly.get('details', {}),
                confidence_score=anomaly.get('score', 0.0)
            )
            
            self._active_alerts[alert_id] = alert
            self._alert_history.append(alert)
            
            # Set cooldown
            self._alert_cooldowns[alert_type] = time.time()
            
            # Log alert
            self.logger.warning(f"Anomaly alert generated: {alert_id} - {alert.description}")
            
            # Update performance stats
            self._performance_stats['anomalies_detected'] += 1
            self._performance_stats['alerts_generated'] += 1
    
    def _is_in_cooldown(self, anomaly_type: AnomalyType) -> bool:
        """Check if alert type is in cooldown period"""
        last_alert_time = self._alert_cooldowns.get(anomaly_type)
        if not last_alert_time:
            return False
        
        return time.time() - last_alert_time < self.config.alert_cooldown
    
    async def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        
        system_metrics = await self._get_system_metrics()
        
        issues = []
        healthy = True
        
        # Define health thresholds
        thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 85.0,
            'error_rate': 5.0,
            'avg_response_time': 5.0
        }
        
        for metric, value in system_metrics.items():
            threshold = thresholds.get(metric)
            if threshold and value > threshold:
                issues.append(f"{metric} ({value:.1f}) exceeds threshold ({threshold})")
                healthy = False
        
        return {
            'healthy': healthy,
            'issues': issues,
            'metrics': system_metrics,
            'uptime': self._calculate_uptime()
        }
    
    async def _get_system_metrics(self) -> Dict[str, float]:
        """Get current system metrics (simulated)"""
        
        # In a real implementation, this would gather actual system metrics
        return {
            'cpu_usage': np.random.uniform(10, 90),
            'memory_usage': np.random.uniform(20, 95),
            'disk_usage': np.random.uniform(30, 80),
            'network_latency': np.random.uniform(1, 100),
            'error_rate': np.random.uniform(0, 10),
            'avg_response_time': np.random.uniform(0.1, 10),
            'active_connections': np.random.randint(10, 200)
        }
    
    def _calculate_uptime(self) -> float:
        """Calculate system uptime percentage"""
        # This is a simplified calculation
        # In reality, it would track actual uptime
        return 99.5  # Simulated 99.5% uptime
    
    def _update_performance_stats(self, check_duration: float):
        """Update performance statistics"""
        self._performance_stats['total_checks'] += 1
        
        # Update average response time
        total_checks = self._performance_stats['total_checks']
        current_avg = self._performance_stats['average_response_time']
        self._performance_stats['average_response_time'] = (
            (current_avg * (total_checks - 1) + check_duration) / total_checks
        )
    
    async def _update_behavioral_baselines(self):
        """Update behavioral baselines"""
        
        current_time = datetime.utcnow()
        
        # Update baselines every hour
        # This is a simplified implementation
        if len(self._behavioral_data) > 0:
            for user_id, data_points in self._behavioral_data.items():
                if len(data_points) >= 24:  # At least 24 data points
                    trading_frequencies = [dp.get('frequency', 1.0) for dp in list(data_points)[-24:]]
                    avg_stakes = [dp.get('avg_stake', 100.0) for dp in list(data_points)[-24:]]
                    
                    self._behavioral_baselines[f'{user_id}_frequency'] = statistics.mean(trading_frequencies)
                    self._behavioral_baselines[f'{user_id}_avg_stake'] = statistics.mean(avg_stakes)
    
    def _get_user_trading_frequency(self, user_id: str) -> float:
        """Get user trading frequency (simulated)"""
        # In a real implementation, this would query the database
        return np.random.uniform(0.5, 3.0)
    
    def _get_user_stake_patterns(self, user_id: str) -> deque:
        """Get user stake patterns (simulated)"""
        # In a real implementation, this would query historical data
        return deque(np.random.exponential(100, 20))
    
    async def _analyze_behavioral_patterns(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze behavioral patterns"""
        
        if not user_preferences:
            return {'patterns_normal': True}
        
        user_id = user_preferences.get('user_id')
        if not user_id:
            return {'patterns_normal': True}
        
        # Get user behavioral data
        user_data = self._behavioral_data[user_id]
        
        patterns = {
            'frequency': self._get_user_trading_frequency(user_id),
            'stake_patterns': list(self._get_user_stake_patterns(user_id))[-10:],
            'trading_hours': self._analyze_trading_hours(user_data),
            'risk_tolerance': self._analyze_risk_tolerance(user_data)
        }
        
        return patterns
    
    def _analyze_trading_hours(self, user_data: deque) -> Dict[str, Any]:
        """Analyze user trading hour patterns"""
        # Simplified analysis
        return {
            'peak_hours': [9, 14, 20],  # Simulated peak hours
            'usual_start_hour': 8,
            'usual_end_hour': 22
        }
    
    def _analyze_risk_tolerance(self, user_data: deque) -> Dict[str, Any]:
        """Analyze user risk tolerance patterns"""
        # Simplified analysis
        return {
            'conservative_score': 0.7,
            'average_risk_level': 'medium',
            'volatility_tolerance': 0.6
        }
    
    # Placeholder methods for other functionality
    async def _analyze_price_volatility(self):
        """Background price volatility analysis"""
        pass
    
    async def _analyze_volume_patterns(self):
        """Background volume pattern analysis"""
        pass
    
    async def _analyze_system_performance(self):
        """Background system performance analysis"""
        pass
    
    async def _analyze_behavioral_patterns_background(self):
        """Background behavioral pattern analysis"""
        pass
    
    async def _process_intervention_triggers(self):
        """Process intervention triggers"""
        pass
    
    async def _check_intervention_requirements(
        self,
        opportunity_data: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]],
        risk_assessment: Dict[str, Any],
        anomalies: List[Dict[str, Any]]
    ) -> List[str]:
        """Check if interventions are required"""
        
        interventions = []
        
        # High risk score intervention
        safety_score = risk_assessment.get('safety_score', 100.0)
        if safety_score < 70.0:
            interventions.append("High risk score - require additional verification")
        
        # Anomaly-based intervention
        high_severity_anomalies = [
            a for a in anomalies
            if a.get('severity') in ['high', 'critical']
        ]
        
        if len(high_severity_anomalies) > 0:
            interventions.append(f"Address {len(high_severity_anomalies)} high-severity anomalies")
        
        return interventions
    
    async def _evaluate_intervention_triggers(
        self,
        risk_assessment: Dict[str, Any],
        anomalies: List[Dict[str, Any]],
        behavioral_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Evaluate intervention triggers"""
        
        interventions = []
        
        safety_score = risk_assessment.get('safety_score', 100.0)
        
        # High risk score trigger
        if safety_score < 75.0:
            interventions.append({
                'action_type': 'increase_monitoring',
                'severity': 'medium',
                'escalation_level': 1,
                'description': 'Increase monitoring frequency due to high risk score'
            })
        
        if safety_score < 60.0:
            interventions.append({
                'action_type': 'block_opportunity',
                'severity': 'high',
                'escalation_level': 2,
                'description': 'Block opportunity due to excessive risk'
            })
        
        return interventions
    
    async def _execute_auto_interventions(self, interventions: List[Dict[str, Any]]):
        """Execute automatic interventions"""
        
        for intervention in interventions:
            if intervention.get('auto_execute', False):
                self.logger.warning(f"Executing auto-intervention: {intervention['description']}")
                self._performance_stats['interventions_executed'] += 1
    
    async def _cleanup_old_data(self):
        """Clean up old metrics and alerts"""
        
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(hours=self.config.metric_retention_hours)
        
        # Clean old metrics
        for metric_name, metrics_deque in self._metrics.items():
            while metrics_deque and metrics_deque[0].timestamp < cutoff_time:
                metrics_deque.popleft()
        
        # Clean old resolved alerts
        alert_cutoff = current_time - timedelta(days=self.config.alert_retention_days)
        resolved_alerts = [
            alert_id for alert_id, alert in self._active_alerts.items()
            if alert.resolved and alert.resolved_timestamp and alert.resolved_timestamp < alert_cutoff
        ]
        
        for alert_id in resolved_alerts:
            del self._active_alerts[alert_id]
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            'status': self.status.value,
            'active': self._monitoring_active,
            'uptime': self._calculate_uptime(),
            'active_alerts': len([a for a in self._active_alerts.values() if not a.resolved]),
            'performance_stats': self._performance_stats.copy()
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [
            {
                'alert_id': alert_id,
                'type': alert.anomaly_type.value,
                'severity': alert.severity.value,
                'description': alert.description,
                'timestamp': alert.timestamp.isoformat(),
                'confidence': alert.confidence_score
            }
            for alert_id, alert in self._active_alerts.items()
            if not alert.resolved
        ]
    
    def resolve_alert(self, alert_id: str, actions_taken: List[str] = None) -> bool:
        """Resolve an active alert"""
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_timestamp = datetime.utcnow()
            alert.actions_taken = actions_taken or []
            
            self.logger.info(f"Alert resolved: {alert_id}")
            return True
        
        return False
    
    def clear_cache(self):
        """Clear monitoring cache"""
        self._metrics.clear()
        self._behavioral_data.clear()
        self._alert_cooldowns.clear()
        self.logger.info("Safety monitor cache cleared")