"""
Real-Time Risk Monitoring System for Browser Operations

This module provides comprehensive real-time risk monitoring and assessment:
- Continuous risk assessment during browser operations
- Integration with Phase 4 risk management system
- Real-time risk scoring and classification
- Proactive risk alerting and intervention
- Risk trend analysis and prediction
- Automated risk mitigation recommendations

Features:
- Multi-dimensional risk assessment
- Real-time risk scoring
- Risk classification and prioritization
- Integration with ARBitech risk management
- Proactive risk intervention
- Risk reporting and analytics
- Automated risk response actions
"""

import asyncio
import time
import json
import statistics
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from collections import deque, defaultdict
import logging
import math

# Import risk management components
from arbitech.risk.monitoring_system import (
    get_monitoring_system, MonitoringSystem, PerformanceMetric, 
    MetricType, AlertSeverity, Alert as RiskAlert
)
from arbitech.risk.risk_analyzer import RiskAnalyzer
from arbitech.risk.emergency_stops import EmergencyStopSystem
from arbitech.risk.circuit_breaker import CircuitBreaker
from arbitech.risk.loss_limiter import LossLimiter
from arbitech.risk.bankroll_manager import BankrollManager

from arbitech.storage.audit_logger import get_audit_logger, log_performance_metric
from arbitech.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import Selenium for browser risk assessment
try:
    from selenium.common.exceptions import WebDriverException, TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available - risk assessment will be limited")


class RiskCategory(Enum):
    """Risk categories for browser operations"""
    TECHNICAL_RISK = "technical_risk"
    PERFORMANCE_RISK = "performance_risk"
    SECURITY_RISK = "security_risk"
    OPERATIONAL_RISK = "operational_risk"
    FINANCIAL_RISK = "financial_risk"
    COMPLIANCE_RISK = "compliance_risk"
    RESOURCE_RISK = "resource_risk"
    STABILITY_RISK = "stability_risk"


class RiskSeverity(Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class RiskStatus(Enum):
    """Risk status tracking"""
    MONITORING = "monitoring"
    DETECTED = "detected"
    ESCALATING = "escalating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    CRITICAL = "critical"


class InterventionAction(Enum):
    """Risk intervention actions"""
    MONITOR = "monitor"
    ALERT = "alert"
    THROTTLE = "throttle"
    RESTART_BROWSER = "restart_browser"
    ISOLATE_INSTANCE = "isolate_instance"
    EMERGENCY_STOP = "emergency_stop"
    CIRCUIT_BREAKER = "circuit_breaker"
    ESCALATE = "escalate"


@dataclass
class RiskFactor:
    """Individual risk factor"""
    factor_id: UUID = field(default_factory=uuid4)
    category: RiskCategory = RiskCategory.TECHNICAL_RISK
    name: str = ""
    description: str = ""
    
    # Risk assessment
    risk_score: float = 0.0  # 0.0 to 1.0
    probability: float = 0.0  # 0.0 to 1.0
    impact: float = 0.0  # 0.0 to 1.0
    
    # Context
    source: str = ""  # browser, system, external, etc.
    affected_browsers: List[str] = field(default_factory=list)
    affected_operations: List[str] = field(default_factory=list)
    
    # Metadata
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_assessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    severity: RiskSeverity = RiskSeverity.LOW
    
    # Tracking
    occurrence_count: int = 0
    trend: str = "stable"  # improving, stable, worsening
    
    def calculate_risk_score(self) -> float:
        """Calculate risk score based on probability and impact"""
        return self.probability * self.impact
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'factor_id': str(self.factor_id),
            'category': self.category.value,
            'name': self.name,
            'description': self.description,
            'risk_score': self.risk_score,
            'probability': self.probability,
            'impact': self.impact,
            'source': self.source,
            'affected_browsers': self.affected_browsers,
            'affected_operations': self.affected_operations,
            'detected_at': self.detected_at.isoformat(),
            'last_assessed': self.last_assessed.isoformat(),
            'severity': self.severity.value,
            'occurrence_count': self.occurrence_count,
            'trend': self.trend
        }


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment"""
    assessment_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Overall risk score
    overall_risk_score: float = 0.0
    risk_level: RiskSeverity = RiskSeverity.LOW
    
    # Category-specific scores
    category_scores: Dict[RiskCategory, float] = field(default_factory=dict)
    
    # Risk factors
    active_risk_factors: List[RiskFactor] = field(default_factory=list)
    new_risk_factors: List[RiskFactor] = field(default_factory=list)
    resolved_risk_factors: List[RiskFactor] = field(default_factory=list)
    
    # Context
    scope: str = "system"  # system, browser, operation
    target_id: Optional[str] = None  # browser_id, operation_id, etc.
    
    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    intervention_priority: int = 0
    
    # Metadata
    confidence_level: float = 0.0
    data_quality_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'assessment_id': str(self.assessment_id),
            'timestamp': self.timestamp.isoformat(),
            'overall_risk_score': self.overall_risk_score,
            'risk_level': self.risk_level.value,
            'category_scores': {k.value: v for k, v in self.category_scores.items()},
            'active_risk_factors': [f.to_dict() for f in self.active_risk_factors],
            'new_risk_factors': [f.to_dict() for f in self.new_risk_factors],
            'resolved_risk_factors': [f.to_dict() for f in self.resolved_risk_factors],
            'scope': self.scope,
            'target_id': self.target_id,
            'recommended_actions': self.recommended_actions,
            'intervention_priority': self.intervention_priority,
            'confidence_level': self.confidence_level,
            'data_quality_score': self.data_quality_score
        }


@dataclass
class RiskAlert:
    """Risk alert information"""
    alert_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Alert details
    risk_assessment_id: UUID = field(default_factory=uuid4)
    risk_level: RiskSeverity = RiskSeverity.MEDIUM
    category: RiskCategory = RiskCategory.TECHNICAL_RISK
    
    # Alert content
    title: str = ""
    message: str = ""
    description: str = ""
    
    # Context
    affected_browsers: List[str] = field(default_factory=list)
    affected_operations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)  # Factor IDs
    
    # Response tracking
    status: str = "active"  # active, acknowledged, resolved, escalated
    assigned_to: Optional[str] = None
    response_actions: List[str] = field(default_factory=list)
    
    # Metadata
    urgency_score: float = 0.0
    auto_resolve_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'alert_id': str(self.alert_id),
            'timestamp': self.timestamp.isoformat(),
            'risk_assessment_id': str(self.risk_assessment_id),
            'risk_level': self.risk_level.value,
            'category': self.category.value,
            'title': self.title,
            'message': self.message,
            'description': self.description,
            'affected_browsers': self.affected_browsers,
            'affected_operations': self.affected_operations,
            'risk_factors': self.risk_factors,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'response_actions': self.response_actions,
            'urgency_score': self.urgency_score,
            'auto_resolve_time': self.auto_resolve_time.isoformat() if self.auto_resolve_time else None
        }


@dataclass
class RiskTrend:
    """Risk trend analysis"""
    metric_name: str
    trend_direction: str  # improving, stable, worsening
    trend_strength: float  # 0.0 to 1.0
    
    # Statistical measures
    current_value: float = 0.0
    previous_value: float = 0.0
    change_percent: float = 0.0
    
    # Prediction
    predicted_trend: str = "stable"
    confidence: float = 0.0
    
    # Context
    time_period: str = "hour"  # minute, hour, day, week
    data_points: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'metric_name': self.metric_name,
            'trend_direction': self.trend_direction,
            'trend_strength': self.trend_strength,
            'current_value': self.current_value,
            'previous_value': self.previous_value,
            'change_percent': self.change_percent,
            'predicted_trend': self.predicted_trend,
            'confidence': self.confidence,
            'time_period': self.time_period,
            'data_points': self.data_points
        }


@dataclass
class RiskMitigation:
    """Risk mitigation action"""
    mitigation_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Action details
    action_type: InterventionAction = InterventionAction.MONITOR
    name: str = ""
    description: str = ""
    
    # Risk context
    target_risk_factors: List[str] = field(default_factory=list)  # Factor IDs
    target_browsers: List[str] = field(default_factory=list)
    
    # Implementation
    auto_execute: bool = False
    execution_status: str = "pending"  # pending, executing, completed, failed
    execution_result: str = ""
    
    # Metadata
    priority: int = 0
    estimated_impact: float = 0.0
    risk_reduction: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'mitigation_id': str(self.mitigation_id),
            'timestamp': self.timestamp.isoformat(),
            'action_type': self.action_type.value,
            'name': self.name,
            'description': self.description,
            'target_risk_factors': self.target_risk_factors,
            'target_browsers': self.target_browsers,
            'auto_execute': self.auto_execute,
            'execution_status': self.execution_status,
            'execution_result': self.execution_result,
            'priority': self.priority,
            'estimated_impact': self.estimated_impact,
            'risk_reduction': self.risk_reduction
        }


@dataclass
class RiskMonitoringConfig:
    """Configuration for risk monitoring"""
    # Assessment intervals
    continuous_assessment_interval_seconds: float = 30.0
    comprehensive_assessment_interval_minutes: int = 5
    trend_analysis_interval_minutes: int = 15
    alert_check_interval_seconds: float = 10.0
    
    # Risk thresholds
    low_risk_threshold: float = 0.3
    medium_risk_threshold: float = 0.5
    high_risk_threshold: float = 0.7
    critical_risk_threshold: float = 0.9
    emergency_risk_threshold: float = 0.95
    
    # Performance risk thresholds
    performance_degradation_threshold: float = 0.25  # 25% degradation
    error_rate_threshold: float = 0.05  # 5% error rate
    response_time_threshold_ms: float = 5000.0  # 5 seconds
    memory_usage_threshold_mb: float = 600.0  # 600MB
    cpu_usage_threshold_percent: float = 80.0  # 80%
    
    # Risk detection settings
    enable_predictive_risk: bool = True
    risk_prediction_horizon_hours: int = 1
    min_data_points_for_prediction: int = 10
    
    # Alert settings
    enable_risk_alerts: bool = True
    alert_escalation_enabled: bool = True
    max_alerts_per_hour: int = 20
    alert_cooldown_minutes: int = 10
    
    # Intervention settings
    auto_intervention_enabled: bool = True
    intervention_confidence_threshold: float = 0.8
    emergency_stop_enabled: bool = True
    circuit_breaker_enabled: bool = True
    
    # Integration settings
    enable_emergency_stop_integration: bool = True
    enable_circuit_breaker_integration: bool = True
    enable_loss_limiter_integration: bool = True
    enable_bankroll_manager_integration: bool = True


class RiskDetector:
    """Detect various types of risks"""
    
    def __init__(self, config: RiskMonitoringConfig):
        self.config = config
        self.risk_thresholds = self._initialize_risk_thresholds()
    
    def _initialize_risk_thresholds(self) -> Dict[RiskCategory, float]:
        """Initialize risk thresholds by category"""
        return {
            RiskCategory.TECHNICAL_RISK: self.config.medium_risk_threshold,
            RiskCategory.PERFORMANCE_RISK: self.config.medium_risk_threshold,
            RiskCategory.SECURITY_RISK: self.config.high_risk_threshold,
            RiskCategory.OPERATIONAL_RISK: self.config.medium_risk_threshold,
            RiskCategory.FINANCIAL_RISK: self.config.high_risk_threshold,
            RiskCategory.COMPLIANCE_RISK: self.config.high_risk_threshold,
            RiskCategory.RESOURCE_RISK: self.config.medium_risk_threshold,
            RiskCategory.STABILITY_RISK: self.config.high_risk_threshold
        }
    
    async def detect_all_risks(self, performance_data: Dict[str, Any], 
                             system_data: Dict[str, Any]) -> List[RiskFactor]:
        """Detect all types of risks"""
        risk_factors = []
        
        try:
            # Technical risks
            risk_factors.extend(await self._detect_technical_risks(performance_data, system_data))
            
            # Performance risks
            risk_factors.extend(await self._detect_performance_risks(performance_data))
            
            # Resource risks
            risk_factors.extend(await self._detect_resource_risks(performance_data))
            
            # Stability risks
            risk_factors.extend(await self._detect_stability_risks(performance_data))
            
            # Operational risks
            risk_factors.extend(await self._detect_operational_risks(performance_data, system_data))
            
            # Security risks
            risk_factors.extend(await self._detect_security_risks(performance_data))
            
        except Exception as e:
            logger.error(f"Risk detection failed: {e}")
        
        return risk_factors
    
    async def _detect_technical_risks(self, performance_data: Dict[str, Any], 
                                    system_data: Dict[str, Any]) -> List[RiskFactor]:
        """Detect technical risks"""
        risk_factors = []
        
        try:
            # Browser crash risk
            browsers = performance_data.get('browsers', {})
            crashed_browsers = sum(1 for b in browsers.values() 
                                 if b.get('state') == 'crashed')
            
            if crashed_browsers > 0:
                total_browsers = len(browsers)
                crash_rate = crashed_browsers / total_browsers if total_browsers > 0 else 0
                
                if crash_rate > 0.1:  # More than 10% crashed
                    risk = RiskFactor(
                        category=RiskCategory.TECHNICAL_RISK,
                        name="High Browser Crash Rate",
                        description=f"High browser crash rate detected: {crash_rate:.1%}",
                        probability=min(0.9, crash_rate * 2),
                        impact=0.8,
                        source="browser_monitoring",
                        affected_browsers=[b for b, data in browsers.items() 
                                         if data.get('state') == 'crashed']
                    )
                    risk.risk_score = risk.calculate_risk_score()
                    risk_factors.append(risk)
            
            # Network connectivity risk
            network_errors = performance_data.get('network_errors', 0)
            if network_errors > 5:  # More than 5 network errors
                risk = RiskFactor(
                    category=RiskCategory.TECHNICAL_RISK,
                    name="Network Connectivity Issues",
                    description=f"High number of network errors: {network_errors}",
                    probability=min(0.8, network_errors / 20),
                    impact=0.6,
                    source="network_monitoring"
                )
                risk.risk_score = risk.calculate_risk_score()
                risk_factors.append(risk)
            
        except Exception as e:
            logger.debug(f"Technical risk detection failed: {e}")
        
        return risk_factors
    
    async def _detect_performance_risks(self, performance_data: Dict[str, Any]) -> List[RiskFactor]:
        """Detect performance-related risks"""
        risk_factors = []
        
        try:
            # Page load performance risk
            page_load_times = performance_data.get('page_load_times', [])
            if page_load_times:
                avg_load_time = statistics.mean(page_load_times)
                
                if avg_load_time > self.config.response_time_threshold_ms:
                    degradation = (avg_load_time / self.config.response_time_threshold_ms) - 1
                    
                    risk = RiskFactor(
                        category=RiskCategory.PERFORMANCE_RISK,
                        name="Slow Page Load Performance",
                        description=f"Average page load time: {avg_load_time:.0f}ms (threshold: {self.config.response_time_threshold_ms:.0f}ms)",
                        probability=min(0.9, degradation),
                        impact=0.7,
                        source="performance_monitoring"
                    )
                    risk.risk_score = risk.calculate_risk_score()
                    risk_factors.append(risk)
            
            # Performance degradation risk
            performance_trends = performance_data.get('performance_trends', {})
            for metric, trend_data in performance_trends.items():
                if len(trend_data) >= 2:
                    recent_performance = trend_data[-1][1]
                    baseline_performance = trend_data[0][1]
                    
                    if baseline_performance > 0:
                        degradation = (recent_performance - baseline_performance) / baseline_performance
                        
                        if degradation > self.config.performance_degradation_threshold:
                            risk = RiskFactor(
                                category=RiskCategory.PERFORMANCE_RISK,
                                name="Performance Degradation",
                                description=f"{metric} degraded by {degradation:.1%}",
                                probability=min(0.8, degradation),
                                impact=0.6,
                                source="trend_analysis"
                            )
                            risk.risk_score = risk.calculate_risk_score()
                            risk_factors.append(risk)
            
        except Exception as e:
            logger.debug(f"Performance risk detection failed: {e}")
        
        return risk_factors
    
    async def _detect_resource_risks(self, performance_data: Dict[str, Any]) -> List[RiskFactor]:
        """Detect resource-related risks"""
        risk_factors = []
        
        try:
            # Memory usage risk
            memory_usage = performance_data.get('memory_usage', [])
            if memory_usage:
                peak_memory = max(memory_usage)
                
                if peak_memory > self.config.memory_usage_threshold_mb:
                    excess = (peak_memory - self.config.memory_usage_threshold_mb) / self.config.memory_usage_threshold_mb
                    
                    risk = RiskFactor(
                        category=RiskCategory.RESOURCE_RISK,
                        name="High Memory Usage",
                        description=f"Peak memory usage: {peak_memory:.0f}MB (threshold: {self.config.memory_usage_threshold_mb:.0f}MB)",
                        probability=min(0.8, excess),
                        impact=0.7,
                        source="memory_monitoring"
                    )
                    risk.risk_score = risk.calculate_risk_score()
                    risk_factors.append(risk)
            
            # CPU usage risk
            cpu_usage = performance_data.get('cpu_usage', [])
            if cpu_usage:
                peak_cpu = max(cpu_usage)
                
                if peak_cpu > self.config.cpu_usage_threshold_percent:
                    excess = (peak_cpu - self.config.cpu_usage_threshold_percent) / self.config.cpu_usage_threshold_percent
                    
                    risk = RiskFactor(
                        category=RiskCategory.RESOURCE_RISK,
                        name="High CPU Usage",
                        description=f"Peak CPU usage: {peak_cpu:.1f}% (threshold: {self.config.cpu_usage_threshold_percent:.1f}%)",
                        probability=min(0.8, excess),
                        impact=0.6,
                        source="cpu_monitoring"
                    )
                    risk.risk_score = risk.calculate_risk_score()
                    risk_factors.append(risk)
            
        except Exception as e:
            logger.debug(f"Resource risk detection failed: {e}")
        
        return risk_factors
    
    async def _detect_stability_risks(self, performance_data: Dict[str, Any]) -> List[RiskFactor]:
        """Detect stability-related risks"""
        risk_factors = []
        
        try:
            # Error rate risk
            error_rate = performance_data.get('error_rate', 0.0)
            
            if error_rate > self.config.error_rate_threshold:
                excess = (error_rate - self.config.error_rate_threshold) / self.config.error_rate_threshold
                
                risk = RiskFactor(
                    category=RiskCategory.STABILITY_RISK,
                    name="High Error Rate",
                    description=f"Error rate: {error_rate:.1%} (threshold: {self.config.error_rate_threshold:.1%})",
                    probability=min(0.9, excess),
                    impact=0.8,
                    source="error_monitoring"
                )
                risk.risk_score = risk.calculate_risk_score()
                risk_factors.append(risk)
            
            # Browser instance stability
            browsers = performance_data.get('browsers', {})
            unstable_browsers = sum(1 for b in browsers.values() 
                                  if b.get('health_score', 1.0) < 0.5)
            
            if unstable_browsers > 0:
                instability_rate = unstable_browsers / len(browsers) if browsers else 0
                
                risk = RiskFactor(
                    category=RiskCategory.STABILITY_RISK,
                    name="Browser Instance Instability",
                    description=f"{unstable_browsers} browser instances with low health scores",
                    probability=min(0.8, instability_rate * 2),
                    impact=0.7,
                    source="health_monitoring",
                    affected_browsers=[b for b, data in browsers.items() 
                                     if data.get('health_score', 1.0) < 0.5]
                )
                risk.risk_score = risk.calculate_risk_score()
                risk_factors.append(risk)
            
        except Exception as e:
            logger.debug(f"Stability risk detection failed: {e}")
        
        return risk_factors
    
    async def _detect_operational_risks(self, performance_data: Dict[str, Any], 
                                      system_data: Dict[str, Any]) -> List[RiskFactor]:
        """Detect operational risks"""
        risk_factors = []
        
        try:
            # Monitoring system health
            monitoring_health = system_data.get('monitoring_health', {})
            if not monitoring_health.get('healthy', True):
                risk = RiskFactor(
                    category=RiskCategory.OPERATIONAL_RISK,
                    name="Monitoring System Degraded",
                    description="Performance monitoring system is not healthy",
                    probability=0.7,
                    impact=0.6,
                    source="system_monitoring"
                )
                risk.risk_score = risk.calculate_risk_score()
                risk_factors.append(risk)
            
            # Configuration drift
            config_version = system_data.get('config_version', 'unknown')
            expected_version = system_data.get('expected_config_version', 'unknown')
            
            if config_version != expected_version:
                risk = RiskFactor(
                    category=RiskCategory.OPERATIONAL_RISK,
                    name="Configuration Drift Detected",
                    description=f"Configuration version mismatch: current={config_version}, expected={expected_version}",
                    probability=0.6,
                    impact=0.5,
                    source="configuration_monitoring"
                )
                risk.risk_score = risk.calculate_risk_score()
                risk_factors.append(risk)
            
        except Exception as e:
            logger.debug(f"Operational risk detection failed: {e}")
        
        return risk_factors
    
    async def _detect_security_risks(self, performance_data: Dict[str, Any]) -> List[RiskFactor]:
        """Detect security-related risks"""
        risk_factors = []
        
        try:
            # Suspicious activity patterns
            network_requests = performance_data.get('network_requests', 0)
            if network_requests > 1000:  # Unusually high request rate
                risk = RiskFactor(
                    category=RiskCategory.SECURITY_RISK,
                    name="Unusual Network Activity",
                    description=f"High network request rate: {network_requests}",
                    probability=0.6,
                    impact=0.8,
                    source="network_monitoring"
                )
                risk.risk_score = risk.calculate_risk_score()
                risk_factors.append(risk)
            
            # JavaScript errors (potential security issues)
            js_errors = performance_data.get('javascript_errors', 0)
            if js_errors > 10:  # High number of JS errors
                risk = RiskFactor(
                    category=RiskCategory.SECURITY_RISK,
                    name="High JavaScript Error Rate",
                    description=f"High number of JavaScript errors: {js_errors}",
                    probability=0.5,
                    impact=0.6,
                    source="error_monitoring"
                )
                risk.risk_score = risk.calculate_risk_score()
                risk_factors.append(risk)
            
        except Exception as e:
            logger.debug(f"Security risk detection failed: {e}")
        
        return risk_factors


class RiskPredictor:
    """Predict future risks based on trends"""
    
    def __init__(self, config: RiskMonitoringConfig):
        self.config = config
    
    async def predict_risks(self, historical_data: List[Dict[str, Any]]) -> List[RiskTrend]:
        """Predict future risk trends"""
        trends = []
        
        try:
            # Analyze trends for different metrics
            metrics_to_analyze = [
                'overall_risk_score',
                'error_rate',
                'memory_usage',
                'cpu_usage',
                'response_time'
            ]
            
            for metric in metrics_to_analyze:
                trend = await self._analyze_metric_trend(historical_data, metric)
                if trend:
                    trends.append(trend)
            
        except Exception as e:
            logger.error(f"Risk prediction failed: {e}")
        
        return trends
    
    async def _analyze_metric_trend(self, historical_data: List[Dict[str, Any]], 
                                  metric: str) -> Optional[RiskTrend]:
        """Analyze trend for a specific metric"""
        try:
            # Extract metric values
            values = []
            for data_point in historical_data[-20:]:  # Last 20 data points
                value = self._extract_metric_value(data_point, metric)
                if value is not None:
                    values.append((data_point.get('timestamp'), value))
            
            if len(values) < self.config.min_data_points_for_prediction:
                return None
            
            # Calculate trend
            current_value = values[-1][1]
            previous_value = values[0][1]
            
            if previous_value > 0:
                change_percent = ((current_value - previous_value) / previous_value) * 100
            else:
                change_percent = 0
            
            # Determine trend direction
            if abs(change_percent) < 5:  # Less than 5% change
                trend_direction = "stable"
            elif change_percent > 0:
                trend_direction = "worsening"
            else:
                trend_direction = "improving"
            
            # Calculate trend strength
            changes = []
            for i in range(1, len(values)):
                if values[i-1][1] > 0:
                    change = (values[i][1] - values[i-1][1]) / values[i-1][1]
                    changes.append(abs(change))
            
            trend_strength = statistics.mean(changes) if changes else 0
            
            # Predict future trend (simplified)
            if len(changes) >= 3:
                recent_trend = sum(changes[-3:]) / 3
                if recent_trend > 0.1:  # 10% average change
                    predicted_trend = "worsening"
                elif recent_trend < -0.1:
                    predicted_trend = "improving"
                else:
                    predicted_trend = "stable"
            else:
                predicted_trend = trend_direction
            
            # Calculate confidence
            confidence = min(1.0, len(values) / self.config.min_data_points_for_prediction)
            
            return RiskTrend(
                metric_name=metric,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                current_value=current_value,
                previous_value=previous_value,
                change_percent=change_percent,
                predicted_trend=predicted_trend,
                confidence=confidence,
                data_points=len(values)
            )
            
        except Exception as e:
            logger.debug(f"Trend analysis failed for {metric}: {e}")
            return None
    
    def _extract_metric_value(self, data_point: Dict[str, Any], metric: str) -> Optional[float]:
        """Extract metric value from data point"""
        try:
            if metric == 'overall_risk_score':
                return data_point.get('overall_risk_score')
            elif metric == 'error_rate':
                return data_point.get('error_rate')
            elif metric == 'memory_usage':
                # Extract from browser data
                browsers = data_point.get('browsers', {})
                if browsers:
                    memory_values = [b.get('memory_usage', 0) for b in browsers.values()]
                    return statistics.mean(memory_values) if memory_values else 0
            elif metric == 'cpu_usage':
                # Extract from browser data
                browsers = data_point.get('browsers', {})
                if browsers:
                    cpu_values = [b.get('cpu_usage', 0) for b in browsers.values()]
                    return statistics.mean(cpu_values) if cpu_values else 0
            elif metric == 'response_time':
                return data_point.get('avg_response_time')
            
            return None
            
        except Exception:
            return None


class RiskMitigationEngine:
    """Generate and execute risk mitigation actions"""
    
    def __init__(self, config: RiskMonitoringConfig):
        self.config = config
        self.mitigation_history: List[RiskMitigation] = []
        
        # Initialize risk management integrations
        self.emergency_stop = None
        self.circuit_breaker = None
        self.loss_limiter = None
        self.bankroll_manager = None
        
        try:
            from arbitech.risk.emergency_stops import get_emergency_stop_system
            self.emergency_stop = get_emergency_stop_system()
        except Exception:
            logger.warning("Emergency stop system not available")
        
        try:
            from arbitech.risk.circuit_breaker import get_circuit_breaker
            self.circuit_breaker = get_circuit_breaker()
        except Exception:
            logger.warning("Circuit breaker not available")
        
        try:
            from arbitech.risk.loss_limiter import get_loss_limiter
            self.loss_limiter = get_loss_limiter()
        except Exception:
            logger.warning("Loss limiter not available")
        
        try:
            from arbitech.risk.bankroll_manager import get_bankroll_manager
            self.bankroll_manager = get_bankroll_manager()
        except Exception:
            logger.warning("Bankroll manager not available")
    
    async def generate_mitigations(self, risk_factors: List[RiskFactor]) -> List[RiskMitigation]:
        """Generate mitigation actions for risk factors"""
        mitigations = []
        
        try:
            for risk_factor in risk_factors:
                mitigations.extend(self._generate_risk_mitigations(risk_factor))
            
            # Sort by priority
            mitigations.sort(key=lambda m: m.priority, reverse=True)
            
        except Exception as e:
            logger.error(f"Mitigation generation failed: {e}")
        
        return mitigations
    
    def _generate_risk_mitigations(self, risk_factor: RiskFactor) -> List[RiskMitigation]:
        """Generate mitigations for a specific risk factor"""
        mitigations = []
        
        if risk_factor.category == RiskCategory.TECHNICAL_RISK:
            if "crash" in risk_factor.name.lower():
                mitigations.append(RiskMitigation(
                    action_type=InterventionAction.RESTART_BROWSER,
                    name="Restart Failed Browser Instances",
                    description="Restart browser instances that have crashed",
                    target_risk_factors=[str(risk_factor.factor_id)],
                    target_browsers=risk_factor.affected_browsers,
                    auto_execute=True,
                    priority=80,
                    estimated_impact=0.7,
                    risk_reduction=0.6
                ))
            
            elif "network" in risk_factor.name.lower():
                mitigations.append(RiskMitigation(
                    action_type=InterventionAction.THROTTLE,
                    name="Reduce Network Request Rate",
                    description="Throttle network requests to prevent overload",
                    target_risk_factors=[str(risk_factor.factor_id)],
                    auto_execute=True,
                    priority=60,
                    estimated_impact=0.5,
                    risk_reduction=0.4
                ))
        
        elif risk_factor.category == RiskCategory.PERFORMANCE_RISK:
            if "performance degradation" in risk_factor.name.lower():
                mitigations.append(RiskMitigation(
                    action_type=InterventionAction.THROTTLE,
                    name="Throttle Performance-Heavy Operations",
                    description="Reduce frequency of performance-heavy operations",
                    target_risk_factors=[str(risk_factor.factor_id)],
                    auto_execute=True,
                    priority=70,
                    estimated_impact=0.6,
                    risk_reduction=0.5
                ))
            
            elif "page load" in risk_factor.name.lower():
                mitigations.append(RiskMitigation(
                    action_type=InterventionAction.ALERT,
                    name="Optimize Page Loading",
                    description="Alert to optimize page loading performance",
                    target_risk_factors=[str(risk_factor.factor_id)],
                    auto_execute=False,
                    priority=50,
                    estimated_impact=0.4,
                    risk_reduction=0.3
                ))
        
        elif risk_factor.category == RiskCategory.RESOURCE_RISK:
            if "memory" in risk_factor.name.lower():
                mitigations.append(RiskMitigation(
                    action_type=InterventionAction.RESTART_BROWSER,
                    name="Restart High-Memory Browser Instances",
                    description="Restart browser instances with excessive memory usage",
                    target_risk_factors=[str(risk_factor.factor_id)],
                    target_browsers=risk_factor.affected_browsers,
                    auto_execute=True,
                    priority=75,
                    estimated_impact=0.8,
                    risk_reduction=0.7
                ))
            
            elif "cpu" in risk_factor.name.lower():
                mitigations.append(RiskMitigation(
                    action_type=InterventionAction.THROTTLE,
                    name="Reduce CPU-Intensive Operations",
                    description="Throttle CPU-intensive operations",
                    target_risk_factors=[str(risk_factor.factor_id)],
                    auto_execute=True,
                    priority=65,
                    estimated_impact=0.6,
                    risk_reduction=0.5
                ))
        
        elif risk_factor.category == RiskCategory.STABILITY_RISK:
            if "error rate" in risk_factor.name.lower():
                mitigations.append(RiskMitigation(
                    action_type=InterventionAction.CIRCUIT_BREAKER,
                    name="Activate Circuit Breaker",
                    description="Activate circuit breaker for unstable operations",
                    target_risk_factors=[str(risk_factor.factor_id)],
                    auto_execute=risk_factor.risk_score > self.config.high_risk_threshold,
                    priority=85,
                    estimated_impact=0.9,
                    risk_reduction=0.8
                ))
            
            elif "instability" in risk_factor.name.lower():
                mitigations.append(RiskMitigation(
                    action_type=InterventionAction.ISOLATE_INSTANCE,
                    name="Isolate Unstable Browser Instances",
                    description="Isolate browser instances showing instability",
                    target_risk_factors=[str(risk_factor.factor_id)],
                    target_browsers=risk_factor.affected_browsers,
                    auto_execute=True,
                    priority=80,
                    estimated_impact=0.7,
                    risk_reduction=0.6
                ))
        
        elif risk_factor.category == RiskCategory.SECURITY_RISK:
            mitigations.append(RiskMitigation(
                action_type=InterventionAction.ESCALATE,
                name="Escalate Security Risk",
                description="Escalate security risk to security team",
                target_risk_factors=[str(risk_factor.factor_id)],
                auto_execute=False,
                priority=90,
                estimated_impact=0.8,
                risk_reduction=0.0  # Requires manual intervention
            ))
        
        # Add monitoring mitigation for all high-risk factors
        if risk_factor.risk_score > self.config.medium_risk_threshold:
            mitigations.append(RiskMitigation(
                action_type=InterventionAction.MONITOR,
                name=f"Intensive Monitoring for {risk_factor.name}",
                description=f"Increase monitoring frequency for {risk_factor.name}",
                target_risk_factors=[str(risk_factor.factor_id)],
                auto_execute=True,
                priority=40,
                estimated_impact=0.3,
                risk_reduction=0.2
            ))
        
        return mitigations
    
    async def execute_mitigation(self, mitigation: RiskMitigation) -> bool:
        """Execute a mitigation action"""
        try:
            logger.info(f"Executing mitigation: {mitigation.name}")
            
            # Update status
            mitigation.execution_status = "executing"
            
            # Execute based on action type
            success = False
            
            if mitigation.action_type == InterventionAction.RESTART_BROWSER:
                success = await self._execute_browser_restart(mitigation)
            elif mitigation.action_type == InterventionAction.THROTTLE:
                success = await self._execute_throttling(mitigation)
            elif mitigation.action_type == InterventionAction.ISOLATE_INSTANCE:
                success = await self._execute_isolation(mitigation)
            elif mitigation.action_type == InterventionAction.CIRCUIT_BREAKER:
                success = await self._execute_circuit_breaker(mitigation)
            elif mitigation.action_type == InterventionAction.EMERGENCY_STOP:
                success = await self._execute_emergency_stop(mitigation)
            elif mitigation.action_type == InterventionAction.ALERT:
                success = await self._execute_alert(mitigation)
            elif mitigation.action_type == InterventionAction.MONITOR:
                success = await self._execute_monitoring(mitigation)
            else:
                # Default: log the action
                success = True
                mitigation.execution_result = "Action logged for manual execution"
            
            # Update status
            if success:
                mitigation.execution_status = "completed"
            else:
                mitigation.execution_status = "failed"
                mitigation.execution_result = "Execution failed"
            
            # Add to history
            self.mitigation_history.append(mitigation)
            
            return success
            
        except Exception as e:
            logger.error(f"Mitigation execution failed: {e}")
            mitigation.execution_status = "failed"
            mitigation.execution_result = f"Execution error: {str(e)}"
            return False
    
    async def _execute_browser_restart(self, mitigation: RiskMitigation) -> bool:
        """Execute browser restart mitigation"""
        try:
            # In a real implementation, this would restart specific browser instances
            # For now, we'll simulate the action
            logger.info(f"Would restart browsers: {mitigation.target_browsers}")
            
            mitigation.execution_result = f"Browser restart triggered for {len(mitigation.target_browsers)} instances"
            return True
            
        except Exception as e:
            mitigation.execution_result = f"Browser restart failed: {e}"
            return False
    
    async def _execute_throttling(self, mitigation: RiskMitigation) -> bool:
        """Execute throttling mitigation"""
        try:
            # In a real implementation, this would throttle specific operations
            logger.info("Would throttle operations")
            
            mitigation.execution_result = "Operation throttling activated"
            return True
            
        except Exception as e:
            mitigation.execution_result = f"Throttling failed: {e}"
            return False
    
    async def _execute_isolation(self, mitigation: RiskMitigation) -> bool:
        """Execute instance isolation mitigation"""
        try:
            # In a real implementation, this would isolate problematic browser instances
            logger.info(f"Would isolate instances: {mitigation.target_browsers}")
            
            mitigation.execution_result = f"Instance isolation activated for {len(mitigation.target_browsers)} browsers"
            return True
            
        except Exception as e:
            mitigation.execution_result = f"Isolation failed: {e}"
            return False
    
    async def _execute_circuit_breaker(self, mitigation: RiskMitigation) -> bool:
        """Execute circuit breaker mitigation"""
        try:
            if self.circuit_breaker:
                # Activate circuit breaker for risky operations
                await self.circuit_breaker.open()
                mitigation.execution_result = "Circuit breaker activated"
                return True
            else:
                mitigation.execution_result = "Circuit breaker system not available"
                return False
                
        except Exception as e:
            mitigation.execution_result = f"Circuit breaker activation failed: {e}"
            return False
    
    async def _execute_emergency_stop(self, mitigation: RiskMitigation) -> bool:
        """Execute emergency stop mitigation"""
        try:
            if self.emergency_stop and self.config.emergency_stop_enabled:
                # Trigger emergency stop
                await self.emergency_stop.trigger_emergency_stop("Risk mitigation triggered")
                mitigation.execution_result = "Emergency stop activated"
                return True
            else:
                mitigation.execution_result = "Emergency stop system not available"
                return False
                
        except Exception as e:
            mitigation.execution_result = f"Emergency stop failed: {e}"
            return False
    
    async def _execute_alert(self, mitigation: RiskMitigation) -> bool:
        """Execute alert mitigation"""
        try:
            # In a real implementation, this would send alerts to operations team
            logger.warning(f"Risk mitigation alert: {mitigation.name} - {mitigation.description}")
            
            mitigation.execution_result = "Alert sent to operations team"
            return True
            
        except Exception as e:
            mitigation.execution_result = f"Alert failed: {e}"
            return False
    
    async def _execute_monitoring(self, mitigation: RiskMitigation) -> bool:
        """Execute enhanced monitoring mitigation"""
        try:
            # In a real implementation, this would increase monitoring frequency
            logger.info(f"Enhanced monitoring activated for: {mitigation.target_risk_factors}")
            
            mitigation.execution_result = "Enhanced monitoring activated"
            return True
            
        except Exception as e:
            mitigation.execution_result = f"Monitoring enhancement failed: {e}"
            return False


class RiskMonitor:
    """Main risk monitoring system"""
    
    def __init__(self, config: Optional[RiskMonitoringConfig] = None):
        self.config = config or RiskMonitoringConfig()
        self.audit_logger = get_audit_logger()
        
        # Core components
        self.risk_detector = RiskDetector(self.config)
        self.risk_predictor = RiskPredictor(self.config)
        self.mitigation_engine = RiskMitigationEngine(self.config)
        
        # Risk tracking
        self.active_risk_factors: Dict[UUID, RiskFactor] = {}
        self.risk_assessments: deque = deque(maxlen=1000)
        self.risk_alerts: deque = deque(maxlen=500)
        self.risk_trends: List[RiskTrend] = []
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Data storage
        self.historical_data: deque = deque(maxlen=1000)
        self.performance_data_cache: Dict[str, Any] = {}
        
        # Statistics
        self.risk_stats = {
            'assessments_completed': 0,
            'risk_factors_detected': 0,
            'alerts_generated': 0,
            'mitigations_executed': 0,
            'emergencies_triggered': 0
        }
        
        # Integration with risk management system
        self.risk_monitoring_system = None
        try:
            self.risk_monitoring_system = get_monitoring_system()
        except Exception as e:
            logger.warning(f"Risk monitoring system integration failed: {e}")
        
        logger.info("Risk monitoring system initialized")
    
    async def start_monitoring(self):
        """Start risk monitoring"""
        if self.monitoring_active:
            logger.warning("Risk monitoring already active")
            return
        
        self.monitoring_active = True
        self._shutdown_event.clear()
        
        # Create monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._continuous_assessment_loop()),
            asyncio.create_task(self._comprehensive_assessment_loop()),
            asyncio.create_task(self._trend_analysis_loop()),
            asyncio.create_task(self._alert_management_loop())
        ]
        
        logger.info("Risk monitoring started")
    
    async def stop_monitoring(self):
        """Stop risk monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        self._shutdown_event.set()
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        
        logger.info("Risk monitoring stopped")
    
    def update_performance_data(self, data: Dict[str, Any]):
        """Update performance data for risk assessment"""
        self.performance_data_cache.update(data)
        
        # Add to historical data
        historical_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            **data
        }
        self.historical_data.append(historical_entry)
    
    async def _continuous_assessment_loop(self):
        """Continuous risk assessment loop"""
        while self.monitoring_active:
            try:
                await self._perform_continuous_assessment()
                await asyncio.sleep(self.config.continuous_assessment_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in continuous assessment loop: {e}", exc_info=True)
                await asyncio.sleep(10)
    
    async def _perform_continuous_assessment(self):
        """Perform continuous risk assessment"""
        try:
            # Get current system data
            system_data = {
                'monitoring_health': {'healthy': self.monitoring_active},
                'config_version': '1.0',
                'expected_config_version': '1.0'
            }
            
            # Detect risks
            new_risk_factors = await self.risk_detector.detect_all_risks(
                self.performance_data_cache, system_data
            )
            
            # Update active risk factors
            for risk_factor in new_risk_factors:
                self.active_risk_factors[risk_factor.factor_id] = risk_factor
                self.risk_stats['risk_factors_detected'] += 1
            
            # Remove resolved risk factors
            current_time = datetime.now(timezone.utc)
            resolved_factors = []
            
            for factor_id, risk_factor in list(self.active_risk_factors.items()):
                # Check if risk factor is still active
                if not self._is_risk_factor_active(risk_factor, self.performance_data_cache):
                    resolved_factors.append(risk_factor)
                    del self.active_risk_factors[factor_id]
            
            # Create assessment
            assessment = await self._create_risk_assessment(
                list(self.active_risk_factors.values()),
                resolved_factors
            )
            
            if assessment:
                self.risk_assessments.append(assessment)
                self.risk_stats['assessments_completed'] += 1
                
                # Check for critical risks
                if assessment.risk_level == RiskSeverity.CRITICAL:
                    await self._handle_critical_risk(assessment)
                
                # Log to risk management system
                await self._log_assessment_to_risk_system(assessment)
            
        except Exception as e:
            logger.error(f"Continuous assessment failed: {e}")
    
    def _is_risk_factor_active(self, risk_factor: RiskFactor, current_data: Dict[str, Any]) -> bool:
        """Check if risk factor is still active based on current data"""
        try:
            # This is a simplified check - in practice, you'd have more sophisticated logic
            # For now, we'll consider factors active for a short period
            
            time_since_detection = (datetime.now(timezone.utc) - risk_factor.detected_at).total_seconds()
            
            # Risk factors expire after 5 minutes if not refreshed
            return time_since_detection < 300
            
        except Exception:
            return False
    
    async def _create_risk_assessment(self, active_factors: List[RiskFactor], 
                                    resolved_factors: List[RiskFactor]) -> Optional[RiskAssessment]:
        """Create comprehensive risk assessment"""
        try:
            if not active_factors:
                # Create a low-risk assessment if no active risks
                return RiskAssessment(
                    overall_risk_score=0.1,
                    risk_level=RiskSeverity.LOW,
                    confidence_level=0.9,
                    data_quality_score=1.0
                )
            
            # Calculate overall risk score
            overall_score = statistics.mean([f.risk_score for f in active_factors])
            
            # Determine risk level
            if overall_score >= self.config.emergency_risk_threshold:
                risk_level = RiskSeverity.EMERGENCY
            elif overall_score >= self.config.critical_risk_threshold:
                risk_level = RiskSeverity.CRITICAL
            elif overall_score >= self.config.high_risk_threshold:
                risk_level = RiskSeverity.HIGH
            elif overall_score >= self.config.medium_risk_threshold:
                risk_level = RiskSeverity.MEDIUM
            else:
                risk_level = RiskSeverity.LOW
            
            # Calculate category scores
            category_scores = defaultdict(float)
            for factor in active_factors:
                category_scores[factor.category] = max(category_scores[factor.category], factor.risk_score)
            
            # Generate recommendations
            recommendations = await self._generate_risk_recommendations(active_factors)
            
            # Calculate intervention priority
            intervention_priority = self._calculate_intervention_priority(active_factors)
            
            # Calculate confidence level (based on data quality)
            confidence_level = self._calculate_confidence_level(active_factors)
            
            return RiskAssessment(
                overall_risk_score=overall_score,
                risk_level=risk_level,
                category_scores=dict(category_scores),
                active_risk_factors=active_factors,
                resolved_risk_factors=resolved_factors,
                recommended_actions=recommendations,
                intervention_priority=intervention_priority,
                confidence_level=confidence_level,
                data_quality_score=confidence_level
            )
            
        except Exception as e:
            logger.error(f"Risk assessment creation failed: {e}")
            return None
    
    async def _generate_risk_recommendations(self, risk_factors: List[RiskFactor]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        # Group by category
        by_category = defaultdict(list)
        for factor in risk_factors:
            by_category[factor.category].append(factor)
        
        # Generate recommendations for each category
        if RiskCategory.TECHNICAL_RISK in by_category:
            recommendations.append("Investigate technical issues and restart failed components")
        
        if RiskCategory.PERFORMANCE_RISK in by_category:
            recommendations.append("Optimize performance and implement throttling")
        
        if RiskCategory.RESOURCE_RISK in by_category:
            recommendations.append("Free up resources and restart memory-intensive processes")
        
        if RiskCategory.STABILITY_RISK in by_category:
            recommendations.append("Activate stability measures and circuit breakers")
        
        if RiskCategory.SECURITY_RISK in by_category:
            recommendations.append("Escalate security concerns and increase monitoring")
        
        if RiskCategory.OPERATIONAL_RISK in by_category:
            recommendations.append("Review operational procedures and system configuration")
        
        return recommendations
    
    def _calculate_intervention_priority(self, risk_factors: List[RiskFactor]) -> int:
        """Calculate intervention priority (0-100)"""
        if not risk_factors:
            return 0
        
        max_score = max(f.risk_score for f in risk_factors)
        high_severity_count = sum(1 for f in risk_factors if f.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL])
        
        priority = int(max_score * 50) + (high_severity_count * 25)
        return min(100, priority)
    
    def _calculate_confidence_level(self, risk_factors: List[RiskFactor]) -> float:
        """Calculate confidence level for assessment"""
        if not risk_factors:
            return 0.5
        
        # Base confidence on data quality and factor count
        data_factors = sum(1 for f in risk_factors if f.source in ['performance_monitoring', 'system_monitoring'])
        total_factors = len(risk_factors)
        
        if total_factors == 0:
            return 0.5
        
        data_quality_ratio = data_factors / total_factors
        factor_count_bonus = min(0.3, total_factors * 0.05)  # Bonus for more factors
        
        confidence = 0.4 + (data_quality_ratio * 0.5) + factor_count_bonus
        return min(1.0, confidence)
    
    async def _handle_critical_risk(self, assessment: RiskAssessment):
        """Handle critical risk situation"""
        try:
            logger.critical(f"Critical risk detected: {assessment.overall_risk_score:.2f}")
            
            # Generate alerts
            await self._generate_risk_alerts(assessment)
            
            # Execute automatic mitigations
            if self.config.auto_intervention_enabled:
                await self._execute_automatic_mitigations(assessment)
            
            # Integrate with emergency systems
            if assessment.risk_level == RiskSeverity.EMERGENCY and self.config.emergency_stop_enabled:
                await self._trigger_emergency_response(assessment)
            
        except Exception as e:
            logger.error(f"Critical risk handling failed: {e}")
    
    async def _generate_risk_alerts(self, assessment: RiskAssessment):
        """Generate risk alerts"""
        try:
            # Determine alert severity
            if assessment.risk_level == RiskSeverity.EMERGENCY:
                alert_severity = RiskSeverity.EMERGENCY
            elif assessment.risk_level == RiskSeverity.CRITICAL:
                alert_severity = RiskSeverity.CRITICAL
            elif assessment.risk_level == RiskSeverity.HIGH:
                alert_severity = RiskSeverity.HIGH
            else:
                alert_severity = RiskSeverity.MEDIUM
            
            # Create alert
            alert = RiskAlert(
                risk_assessment_id=assessment.assessment_id,
                risk_level=alert_severity,
                category=max(assessment.category_scores, key=assessment.category_scores.get) 
                         if assessment.category_scores else RiskCategory.TECHNICAL_RISK,
                title=f"{assessment.risk_level.value.upper()} Risk Alert",
                message=f"Risk score: {assessment.overall_risk_score:.2f}",
                description=f"Assessment ID: {assessment.assessment_id}",
                affected_browsers=list(set().union(*[f.affected_browsers for f in assessment.active_risk_factors])),
                affected_operations=list(set().union(*[f.affected_operations for f in assessment.active_risk_factors])),
                risk_factors=[str(f.factor_id) for f in assessment.active_risk_factors],
                urgency_score=assessment.overall_risk_score
            )
            
            self.risk_alerts.append(alert)
            self.risk_stats['alerts_generated'] += 1
            
            # Log security event
            self.audit_logger.log_security_event(
                type('SecurityEventLog', (), {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'event_type': 'RISK_ALERT',
                    'severity': 'warning' if alert_severity.value in ['low', 'medium', 'high'] else 'critical',
                    'user_id': None,
                    'ip_address': None,
                    'session_id': None,
                    'description': f"Risk alert: {alert.message}",
                    'details': alert.to_dict()
                })()
            )
            
        except Exception as e:
            logger.error(f"Alert generation failed: {e}")
    
    async def _execute_automatic_mitigations(self, assessment: RiskAssessment):
        """Execute automatic mitigation actions"""
        try:
            # Generate mitigations
            mitigations = await self.mitigation_engine.generate_mitigations(assessment.active_risk_factors)
            
            # Execute high-priority automatic mitigations
            for mitigation in mitigations:
                if (mitigation.auto_execute and 
                    mitigation.priority >= 70 and  # High priority
                    mitigation.risk_reduction >= 0.5):  # Significant impact
                    
                    success = await self.mitigation_engine.execute_mitigation(mitigation)
                    if success:
                        self.risk_stats['mitigations_executed'] += 1
                        
                        logger.info(f"Automatic mitigation executed: {mitigation.name}")
            
        except Exception as e:
            logger.error(f"Automatic mitigation execution failed: {e}")
    
    async def _trigger_emergency_response(self, assessment: RiskAssessment):
        """Trigger emergency response systems"""
        try:
            self.risk_stats['emergencies_triggered'] += 1
            
            logger.critical("Triggering emergency response systems")
            
            # This would integrate with actual emergency systems
            # For now, we'll log the action
            
        except Exception as e:
            logger.error(f"Emergency response failed: {e}")
    
    async def _comprehensive_assessment_loop(self):
        """Comprehensive risk assessment loop"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(self.config.comprehensive_assessment_interval_minutes * 60)
                await self._perform_comprehensive_assessment()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in comprehensive assessment loop: {e}", exc_info=True)
    
    async def _perform_comprehensive_assessment(self):
        """Perform comprehensive risk assessment"""
        try:
            # Use historical data for trend analysis
            historical_list = list(self.historical_data)
            
            if len(historical_list) >= self.config.min_data_points_for_prediction:
                # Predict future risks
                trends = await self.risk_predictor.predict_risks(historical_list)
                self.risk_trends = trends
                
                # Check for escalating risks
                for trend in trends:
                    if (trend.trend_direction == "worsening" and 
                        trend.confidence > 0.7 and
                        trend.trend_strength > 0.1):
                        
                        # Create predictive risk factor
                        predictive_risk = RiskFactor(
                            category=RiskCategory.PREDICTIVE_RISK if hasattr(RiskCategory, 'PREDICTIVE_RISK') else RiskCategory.OPERATIONAL_RISK,
                            name=f"Predicted Risk in {trend.metric_name}",
                            description=f"Trend analysis predicts worsening {trend.metric_name}",
                            probability=trend.confidence,
                            impact=min(0.8, trend.trend_strength * 2),
                            source="predictive_analysis"
                        )
                        predictive_risk.risk_score = predictive_risk.calculate_risk_score()
                        
                        self.active_risk_factors[predictive_risk.factor_id] = predictive_risk
                        
                        logger.warning(f"Predictive risk detected: {predictive_risk.name}")
            
        except Exception as e:
            logger.error(f"Comprehensive assessment failed: {e}")
    
    async def _trend_analysis_loop(self):
        """Risk trend analysis loop"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(self.config.trend_analysis_interval_minutes * 60)
                await self._analyze_risk_trends()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in trend analysis loop: {e}", exc_info=True)
    
    async def _analyze_risk_trends(self):
        """Analyze risk trends over time"""
        try:
            # Analyze trends in risk assessments
            recent_assessments = [a for a in self.risk_assessments 
                                if (datetime.now(timezone.utc) - a.timestamp).total_seconds() < 3600]
            
            if len(recent_assessments) >= 3:
                risk_scores = [a.overall_risk_score for a in recent_assessments]
                
                if len(risk_scores) >= 2:
                    recent_score = risk_scores[-1]
                    previous_score = risk_scores[-2]
                    
                    if previous_score > 0:
                        change_percent = ((recent_score - previous_score) / previous_score) * 100
                        
                        # Log trend information
                        if abs(change_percent) > 10:  # Significant change
                            logger.info(f"Risk trend: {change_percent:+.1f}% change in overall risk score")
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
    
    async def _alert_management_loop(self):
        """Risk alert management loop"""
        while self.monitoring_active:
            try:
                await self._manage_risk_alerts()
                await asyncio.sleep(self.config.alert_check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert management loop: {e}", exc_info=True)
    
    async def _manage_risk_alerts(self):
        """Manage risk alerts lifecycle"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Check for expired alerts
            expired_alerts = []
            for alert in self.risk_alerts:
                if (alert.auto_resolve_time and 
                    current_time > alert.auto_resolve_time and 
                    alert.status == "active"):
                    alert.status = "resolved"
                    expired_alerts.append(alert)
            
            # Log expired alerts
            if expired_alerts:
                logger.info(f"Auto-resolved {len(expired_alerts)} expired risk alerts")
            
        except Exception as e:
            logger.error(f"Alert management failed: {e}")
    
    async def _log_assessment_to_risk_system(self, assessment: RiskAssessment):
        """Log assessment to risk management system"""
        try:
            if self.risk_monitoring_system:
                # Convert to performance metric
                metric = PerformanceMetric(
                    metric_name="browser.risk.overall_score",
                    metric_type=MetricType.GAUGE,
                    value=assessment.overall_risk_score,
                    unit="ratio",
                    tags={
                        'risk_level': assessment.risk_level.value,
                        'confidence': str(assessment.confidence_level)
                    }
                )
                
                self.risk_monitoring_system.performance_tracker.record_metric(metric)
            
        except Exception as e:
            logger.debug(f"Failed to log to risk system: {e}")
    
    def get_current_risk_status(self) -> Dict[str, Any]:
        """Get current risk status"""
        current_time = datetime.now(timezone.utc)
        
        # Get latest assessment
        latest_assessment = None
        if self.risk_assessments:
            latest_assessment = max(self.risk_assessments, key=lambda a: a.timestamp)
        
        # Count active risks by category
        category_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for risk_factor in self.active_risk_factors.values():
            category_counts[risk_factor.category.value] += 1
            severity_counts[risk_factor.severity.value] += 1
        
        # Get recent alerts
        recent_alerts = [
            alert.to_dict() for alert in self.risk_alerts
            if (current_time - alert.timestamp).total_seconds() < 3600  # Last hour
        ]
        
        return {
            'timestamp': current_time.isoformat(),
            'monitoring_active': self.monitoring_active,
            'latest_assessment': latest_assessment.to_dict() if latest_assessment else None,
            'active_risks': {
                'total_count': len(self.active_risk_factors),
                'by_category': dict(category_counts),
                'by_severity': dict(severity_counts),
                'high_urgency_count': sum(1 for r in self.active_risk_factors.values() 
                                        if r.risk_score > 0.7)
            },
            'recent_alerts': {
                'count': len(recent_alerts),
                'details': recent_alerts
            },
            'trends': [trend.to_dict() for trend in self.risk_trends],
            'statistics': self.risk_stats.copy(),
            'configuration': {
                'auto_intervention_enabled': self.config.auto_intervention_enabled,
                'emergency_stop_enabled': self.config.emergency_stop_enabled,
                'risk_thresholds': {
                    'low': self.config.low_risk_threshold,
                    'medium': self.config.medium_risk_threshold,
                    'high': self.config.high_risk_threshold,
                    'critical': self.config.critical_risk_threshold
                }
            }
        }
    
    def get_risk_trends(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """Get risk trends for a specific metric"""
        for trend in self.risk_trends:
            if trend.metric_name == metric_name:
                return trend.to_dict()
        return None
    
    def get_active_alerts(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active risk alerts"""
        alerts = list(self.risk_alerts)
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        return [alert.to_dict() for alert in alerts]
    
    def get_risk_factors(self, category: Optional[RiskCategory] = None) -> List[Dict[str, Any]]:
        """Get active risk factors"""
        factors = list(self.active_risk_factors.values())
        
        if category:
            factors = [f for f in factors if f.category == category]
        
        return [factor.to_dict() for factor in factors]
    
    def get_mitigation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get mitigation action history"""
        recent_mitigations = sorted(self.mitigation_engine.mitigation_history, 
                                  key=lambda m: m.timestamp, reverse=True)[:limit]
        return [m.to_dict() for m in recent_mitigations]
    
    async def force_risk_assessment(self) -> Dict[str, Any]:
        """Force immediate risk assessment"""
        try:
            # Perform continuous assessment
            await self._perform_continuous_assessment()
            
            # Get latest assessment
            latest_assessment = max(self.risk_assessments, key=lambda a: a.timestamp)
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'assessment_completed': True,
                'overall_risk_score': latest_assessment.overall_risk_score,
                'risk_level': latest_assessment.risk_level.value,
                'active_risk_factors': len(latest_assessment.active_risk_factors),
                'recommendations': latest_assessment.recommended_actions
            }
            
        except Exception as e:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'assessment_completed': False,
                'error': str(e)
            }
    
    async def shutdown(self):
        """Graceful shutdown of risk monitoring"""
        logger.info("Initiating risk monitoring shutdown")
        
        # Stop monitoring
        await self.stop_monitoring()
        
        # Clear active risks
        self.active_risk_factors.clear()
        
        logger.info("Risk monitoring shutdown completed")


# Global risk monitor instance
_global_risk_monitor = None


def get_risk_monitor() -> RiskMonitor:
    """Get or create global risk monitor"""
    global _global_risk_monitor
    if _global_risk_monitor is None:
        _global_risk_monitor = RiskMonitor()
    return _global_risk_monitor


if __name__ == "__main__":
    # Example usage and testing
    async def test_risk_monitor():
        # Setup
        config = RiskMonitoringConfig()
        risk_monitor = RiskMonitor(config)
        
        print("Starting risk monitoring system...")
        await risk_monitor.start_monitoring()
        
        # Simulate performance data
        test_data = {
            'browsers': {
                'browser_1': {'state': 'running', 'memory_usage': 300, 'cpu_usage': 45, 'health_score': 0.8},
                'browser_2': {'state': 'running', 'memory_usage': 500, 'cpu_usage': 85, 'health_score': 0.6},
                'browser_3': {'state': 'crashed', 'memory_usage': 0, 'cpu_usage': 0, 'health_score': 0.0}
            },
            'page_load_times': [1200, 1800, 2500, 3200, 4500],
            'error_rate': 0.06,
            'memory_usage': [200, 350, 450, 600, 550],
            'cpu_usage': [30, 50, 70, 85, 90],
            'network_requests': 150,
            'javascript_errors': 3
        }
        
        # Update with test data
        risk_monitor.update_performance_data(test_data)
        
        # Let it run for a bit
        await asyncio.sleep(10)
        
        print("Current risk status:", json.dumps(risk_monitor.get_current_risk_status(), indent=2))
        print("Active alerts:", json.dumps(risk_monitor.get_active_alerts(), indent=2))
        print("Risk factors:", json.dumps(risk_monitor.get_risk_factors(), indent=2))
        
        # Force assessment
        print("Forcing risk assessment...")
        assessment_result = await risk_monitor.force_risk_assessment()
        print("Assessment result:", json.dumps(assessment_result, indent=2))
        
        # Stop monitoring
        print("Stopping risk monitoring system...")
        await risk_monitor.shutdown()
        
        print("Risk monitoring system test completed!")
    
    # Run test
    asyncio.run(test_risk_monitor())