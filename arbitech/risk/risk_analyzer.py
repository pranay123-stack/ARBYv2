"""
Risk Analyzer for Arbitrage Trading System

This module provides real-time risk analysis with pattern recognition, anomaly detection,
and predictive risk modeling for arbitrage opportunities. It integrates with the risk
classifier and calculator to provide comprehensive real-time risk monitoring and alerts.

The analyzer provides:
- Real-time risk monitoring and alerting
- Pattern recognition for risk signals
- Anomaly detection for unusual market behavior
- Predictive risk modeling
- Dynamic risk reclassification
- Comprehensive risk reporting and audit trails
"""

import math
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from typing import List, Dict, Optional, Tuple, Union, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import asyncio
from collections import deque, defaultdict
from scipy import stats
from scipy.signal import find_peaks
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# Configure decimal precision
getcontext().prec = 50

from storage.models import ArbitrageOpportunity
from tier_definitions import MarketCondition, RiskToleranceLevel, get_all_tier_definitions
from risk_classifier import (
    RiskClassifier, RiskClassificationResult, RiskComponent,
    RiskComponentScore, ConfidenceLevel
)
from risk_calculator import RiskCalculator, RiskMetrics, StressTest


class AlertSeverity(str, Enum):
    """Risk alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of risk alerts."""
    MARKET_VOLATILITY_SPIKE = "market_volatility_spike"
    LIQUIDITY_DETERIORATION = "liquidity_deterioration"
    EXECUTION_FAILURE_RISK = "execution_failure_risk"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    ODDS_DISCREPANCY = "odds_discrepancy"
    TIME_SENSITIVITY = "time_sensitivity"
    MODEL_UNCERTAINTY = "model_uncertainty"
    REGIME_CHANGE = "regime_change"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"
    PERFORMANCE_DEGRADATION = "performance_degradation"


class PatternType(str, Enum):
    """Types of risk patterns."""
    VOLATILITY_CLUSTERING = "volatility_clustering"
    LIQUIDITY_CYCLES = "liquidity_cycles"
    EXECUTION_DELAY_SPIKES = "execution_delay_spikes"
    ODDS_DIVERGENCE = "odds_divergence"
    CORRELATION_SHIFTS = "correlation_shifts"
    SUCCESS_RATE_DECLINE = "success_rate_decline"
    MARKET_MICROSTRUCTURE = "market_microstructure"
    TEMPORAL_ANOMALIES = "temporal_anomalies"


class RiskTrend(str, Enum):
    """Risk trend directions."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


@dataclass
class RiskAlert:
    """Risk alert for unusual or concerning conditions."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    opportunity_id: Optional[str] = None
    component_affected: Optional[RiskComponent] = None
    metrics_snapshot: Dict[str, Decimal] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    escalation_required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for serialization."""
        return {
            'alert_id': self.alert_id,
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'opportunity_id': self.opportunity_id,
            'component_affected': self.component_affected.value if self.component_affected else None,
            'metrics_snapshot': {k: float(v) for k, v in self.metrics_snapshot.items()},
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat(),
            'acknowledged': self.acknowledged,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'escalation_required': self.escalation_required
        }


@dataclass
class RiskTrend:
    """Risk trend analysis result."""
    component: RiskComponent
    trend_direction: RiskTrend
    trend_strength: Decimal  # 0.0 to 1.0
    trend_confidence: Decimal  # 0.0 to 1.0
    trend_duration: timedelta
    acceleration_rate: Decimal
    volatility_of_trend: Decimal
    projected_values: List[Decimal]
    turning_points: List[datetime]
    trend_explanation: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MarketRiskState:
    """Current market risk state assessment."""
    market_condition: MarketCondition
    volatility_regime: str
    liquidity_regime: str
    correlation_regime: str
    overall_risk_score: Decimal
    regime_stability: Decimal
    regime_transition_probability: Decimal
    time_since_last_change: timedelta
    next_regime_forecast: Optional[Tuple[MarketCondition, Decimal]] = None
    regime_confidence: Decimal = field(default_factory=lambda: '0.7')
    risk_factors_active: List[str] = field(default_factory=list)
    assessment_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PatternDetectionResult:
    """Pattern detection analysis result."""
    pattern_type: PatternType
    confidence: Decimal
    pattern_strength: Decimal
    pattern_start: datetime
    pattern_duration: timedelta
    pattern_amplitude: Decimal
    frequency_analysis: Dict[str, Decimal]
    pattern_significance: Decimal
    market_impact: Decimal
    predictive_power: Decimal
    supporting_evidence: List[str]
    prediction_horizon: timedelta
    detection_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AnomalyDetectionResult:
    """Anomaly detection analysis result."""
    anomaly_type: str
    severity: Decimal  # 0.0 to 1.0
    anomaly_score: Decimal
    affected_components: List[RiskComponent]
    time_window: timedelta
    statistical_significance: Decimal
    root_cause_indicators: List[str]
    market_context: Dict[str, Any]
    resolution_suggestions: List[str]
    detection_timestamp: datetime = field(default_factory=datetime.utcnow)


class PatternRecognitionEngine:
    """Advanced pattern recognition for risk signals."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pattern_cache = {}
        self.signal_processors = {}
        self.detection_thresholds = {
            'volatility_clustering': '0.7',
            'liquidity_cycles': '0.6',
            'execution_delays': '0.8',
            'odds_divergence': '0.75',
            'correlation_shifts': '0.8'
        }
    
    def detect_patterns(
        self,
        time_series_data: Dict[str, List[Tuple[datetime, Decimal]]],
        analysis_window: timedelta = timedelta(hours=24)
    ) -> List[PatternDetectionResult]:
        """
        Detect patterns in time series risk data.
        
        Args:
            time_series_data: Dictionary of {metric_name: [(timestamp, value), ...]}
            analysis_window: Time window for analysis
            
        Returns:
            List of detected patterns
        """
        patterns_detected = []
        
        for metric_name, time_series in time_series_data.items():
            if len(time_series) < 10:
                continue
            
            # Detect specific patterns based on metric type
            if 'volatility' in metric_name.lower():
                patterns = self._detect_volatility_clustering(time_series, analysis_window)
                patterns_detected.extend(patterns)
            
            elif 'liquidity' in metric_name.lower():
                patterns = self._detect_liquidity_cycles(time_series, analysis_window)
                patterns_detected.extend(patterns)
            
            elif 'execution' in metric_name.lower():
                patterns = self._detect_execution_delays(time_series, analysis_window)
                patterns_detected.extend(patterns)
            
            elif 'odds' in metric_name.lower():
                patterns = self._detect_odds_divergence(time_series, analysis_window)
                patterns_detected.extend(patterns)
            
            elif 'correlation' in metric_name.lower():
                patterns = self._detect_correlation_shifts(time_series, analysis_window)
                patterns_detected.extend(patterns)
        
        return patterns_detected
    
    def _detect_volatility_clustering(
        self,
        time_series: List[Tuple[datetime, Decimal]],
        analysis_window: timedelta
    ) -> List[PatternDetectionResult]:
        """Detect volatility clustering patterns."""
        if len(time_series) < 20:
            return []
        
        # Extract values and timestamps
        values = np.array([float(v) for t, v in time_series])
        timestamps = [t for t, v in time_series]
        
        # Calculate rolling volatility of the metric
        window_size = min(10, len(values) // 3)
        rolling_vol = []
        for i in range(window_size, len(values)):
            window_data = values[i-window_size:i]
            rolling_vol.append(np.std(window_data, ddof=1))
        
        if len(rolling_vol) < 5:
            return []
        
        # Find volatility clustering using peaks
        peaks, _ = find_peaks(rolling_vol, height=np.mean(rolling_vol) + np.std(rolling_vol))
        
        if len(peaks) < 2:
            return []
        
        # Analyze clustering
        peak_intervals = np.diff(peaks)
        avg_interval = np.mean(peak_intervals) if len(peak_intervals) > 0 else 1
        
        # Calculate pattern strength
        pattern_strength = min(len(peaks) / len(rolling_vol), '1.0')
        
        # Determine confidence based on regularity of peaks
        if len(peak_intervals) > 0:
            interval_cv = np.std(peak_intervals) / np.mean(peak_intervals)
            confidence = max('0.3', '1.0' - str(interval_cv))
        else:
            confidence = '0.5'
        
        pattern_duration = timestamps[peaks[-1]] - timestamps[peaks[0]]
        
        return [PatternDetectionResult(
            pattern_type=PatternType.VOLATILITY_CLUSTERING,
            confidence=confidence,
            pattern_strength=pattern_strength,
            pattern_start=timestamps[peaks[0]],
            pattern_duration=pattern_duration,
            pattern_amplitude=str(np.max(rolling_vol - np.min(rolling_vol))),
            frequency_analysis={
                'peak_frequency': str(len(peaks / (len(rolling_vol) / window_size))),
                'average_interval': str(avg_interval),
                'regularity_score': confidence
            },
            pattern_significance=min(pattern_strength * confidence, '1.0'),
            market_impact=pattern_strength * '0.7',  # Moderate impact
            predictive_power=confidence * '0.6',
            supporting_evidence=[
                f"Detected {len(peaks)} volatility clusters",
                f"Pattern duration: {pattern_duration}",
                f"Confidence score: {confidence:.3f}"
            ],
            prediction_horizon=timedelta(hours=6)
        )]
    
    def _detect_liquidity_cycles(
        self,
        time_series: List[Tuple[datetime, Decimal]],
        analysis_window: timedelta
    ) -> List[PatternDetectionResult]:
        """Detect liquidity cycle patterns."""
        if len(time_series) < 15:
            return []
        
        values = np.array([float(v) for t, v in time_series])
        timestamps = [t for t, v in time_series]
        
        # Smooth the series to identify cycles
        window_size = max(3, len(values) // 5)
        smoothed_values = self._moving_average(values, window_size)
        
        # Detect cyclical patterns using autocorrelation
        max_lag = min(len(smoothed_values) // 3, 10)
        autocorr = []
        for lag in range(1, max_lag):
            correlation = np.corrcoef(smoothed_values[:-lag], smoothed_values[lag:])[0, 1]
            autocorr.append(correlation if not np.isnan(correlation) else 0)
        
        # Find significant cycles
        significant_lags = [i+1 for i, corr in enumerate(autocorr) if corr > 0.3]
        
        if not significant_lags:
            return []
        
        # Analyze cycle characteristics
        primary_cycle_length = significant_lags[0]
        cycle_strength = max(autocorr) if autocorr else 0
        
        confidence = str(min(abs(cycle_strength, 1.0)))
        pattern_strength = str(min(abs(cycle_strength * 2, 1.0)))
        
        cycle_duration = timestamps[primary_cycle_length] - timestamps[0] if len(timestamps) > primary_cycle_length else timedelta(hours=1)
        
        return [PatternDetectionResult(
            pattern_type=PatternType.LIQUIDITY_CYCLES,
            confidence=confidence,
            pattern_strength=pattern_strength,
            pattern_start=timestamps[0],
            pattern_duration=analysis_window,
            pattern_amplitude=str(np.max(values - np.min(values))),
            frequency_analysis={
                'primary_cycle_length': str(primary_cycle_length),
                'cycle_strength': str(cycle_strength),
                'harmonic_ratio': str(0.5)  # Simplified
            },
            pattern_significance=pattern_strength * confidence,
            market_impact=pattern_strength * Decimal('0.5'),
            predictive_power=confidence * Decimal('0.7'),
            supporting_evidence=[
                f"Primary cycle length: {primary_cycle_length} periods",
                f"Cycle strength: {cycle_strength:.3f}",
                "Significant autocorrelation detected"
            ],
            prediction_horizon=cycle_duration
        )]
    
    def _detect_execution_delays(
        self,
        time_series: List[Tuple[datetime, Decimal]],
        analysis_window: timedelta
    ) -> List[PatternDetectionResult]:
        """Detect execution delay spike patterns."""
        if len(time_series) < 12:
            return []
        
        values = np.array([float(v) for t, v in time_series])
        timestamps = [t for t, v in time_series]
        
        # Calculate baseline execution time
        baseline = np.median(values)
        threshold = baseline * 1.5  # 50% above baseline
        
        # Find delay spikes
        spikes = np.where(values > threshold)[0]
        
        if len(spikes) < 2:
            return []
        
        # Analyze spike characteristics
        spike_intervals = np.diff(spikes)
        avg_interval = np.mean(spike_intervals) if len(spike_intervals) > 0 else 1
        
        # Calculate spike intensity
        spike_intensities = values[spikes]
        avg_intensity = np.mean(spike_intensities)
        max_intensity = np.max(spike_intensities)
        
        pattern_strength = min(len(spikes) / len(values), '1.0')
        confidence = '0.8' if len(spikes) >= 3 else '0.6'
        
        spike_duration = timestamps[spikes[-1]] - timestamps[spikes[0]] if len(spikes) > 1 else timedelta(minutes=30)
        
        return [PatternDetectionResult(
            pattern_type=PatternType.EXECUTION_DELAY_SPIKES,
            confidence=confidence,
            pattern_strength=pattern_strength,
            pattern_start=timestamps[spikes[0]],
            pattern_duration=spike_duration,
            pattern_amplitude=str(max_intensity - baseline),
            frequency_analysis={
                'spike_frequency': str(len(spikes / len(values))),
                'average_interval': str(avg_interval),
                'intensity_ratio': str(avg_intensity / baseline)
            },
            pattern_significance=pattern_strength * confidence,
            market_impact=pattern_strength * '0.8',  # High impact for execution
            predictive_power=confidence * '0.5',
            supporting_evidence=[
                f"Detected {len(spikes)} execution delay spikes",
                f"Average delay increase: {avg_intensity:.1%}",
                f"Pattern span: {spike_duration}"
            ],
            prediction_horizon=timedelta(hours=2)
        )]
    
    def _detect_odds_divergence(
        self,
        time_series: List[Tuple[datetime, Decimal]],
        analysis_window: timedelta
    ) -> List[PatternDetectionResult]:
        """Detect odds divergence patterns."""
        if len(time_series) < 8:
            return []
        
        values = np.array([float(v) for t, v in time_series])
        timestamps = [t for t, v in time_series]
        
        # Calculate odds drift
        drift_rate = (values[-1] - values[0]) / len(values)
        volatility = np.std(values, ddof=1)
        
        # Detect significant divergence
        threshold = 2 * volatility  # 2-sigma threshold
        divergence_points = np.where(np.abs(values - values[0]) > threshold)[0]
        
        if len(divergence_points) < 1:
            return []
        
        # Analyze divergence characteristics
        max_divergence = np.max(np.abs(values - values[0]))
        divergence_duration = timestamps[-1] - timestamps[0]
        
        pattern_strength = min(max_divergence / (3 * volatility), '1.0')
        confidence = '0.7' if max_divergence > 2.5 * volatility else '0.5'
        
        return [PatternDetectionResult(
            pattern_type=PatternType.ODDS_DIVERGENCE,
            confidence=confidence,
            pattern_strength=pattern_strength,
            pattern_start=timestamps[0],
            pattern_duration=divergence_duration,
            pattern_amplitude=str(max_divergence),
            frequency_analysis={
                'drift_rate': str(drift_rate),
                'volatility_ratio': str(volatility / np.mean(np.abs(values))),
                'divergence_points': str(len(divergence_points))
            },
            pattern_significance=pattern_strength * confidence,
            market_impact=pattern_strength * '0.9',  # Very high impact
            predictive_power=confidence * '0.8',
            supporting_evidence=[
                f"Maximum divergence: {max_divergence:.4f}",
                f"Drift rate: {drift_rate:.6f} per period",
                f"Significant divergence detected: {len(divergence_points)} points"
            ],
            prediction_horizon=timedelta(hours=1)
        )]
    
    def _detect_correlation_shifts(
        self,
        time_series: List[Tuple[datetime, Decimal]],
        analysis_window: timedelta
    ) -> List[PatternDetectionResult]:
        """Detect correlation shift patterns."""
        # This would require multiple time series for proper correlation analysis
        # For now, return empty as we need multiple assets/time series
        
        return []
    
    def _moving_average(self, data: np.ndarray, window: int) -> np.ndarray:
        """Calculate moving average."""
        if len(data) < window:
            return data
        
        result = np.convolve(data, np.ones(window)/window, mode='valid')
        return result


class AnomalyDetector:
    """Advanced anomaly detection engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.thresholds = {
            'isolation_forest_contamination': 0.1,
            'z_score_threshold': 3.0,
            'iqr_multiplier': 1.5,
            'dbscan_eps': 0.5,
            'dbscan_min_samples': 5
        }
    
    def detect_anomalies(
        self,
        current_metrics: Dict[str, Decimal],
        historical_data: Dict[str, List[Decimal]],
        model_data: Optional[Dict[str, List[Decimal]]] = None
    ) -> List[AnomalyDetectionResult]:
        """
        Detect anomalies in current metrics vs historical patterns.
        
        Args:
            current_metrics: Current metric values
            historical_data: Historical data for baseline comparison
            model_data: Model-based expected values
            
        Returns:
            List of detected anomalies
        """
        anomalies_detected = []
        
        # 1. Statistical anomaly detection
        for metric_name, current_value in current_metrics.items():
            if metric_name in historical_data:
                historical_values = historical_data[metric_name]
                
                # Z-score based detection
                z_score_anomaly = self._detect_z_score_anomaly(current_value, historical_values)
                if z_score_anomaly:
                    anomalies_detected.append(z_score_anomaly)
                
                # IQR based detection
                iqr_anomaly = self._detect_iqr_anomaly(current_value, historical_values)
                if iqr_anomaly:
                    anomalies_detected.append(iqr_anomaly)
        
        # 2. Multivariate anomaly detection
        if len(current_metrics) > 1 and len(historical_data) > 10:
            multivariate_anomaly = self._detect_multivariate_anomaly(current_metrics, historical_data)
            if multivariate_anomaly:
                anomalies_detected.append(multivariate_anomaly)
        
        # 3. Pattern-based anomaly detection
        pattern_anomalies = self._detect_pattern_anomalies(current_metrics, historical_data)
        anomalies_detected.extend(pattern_anomalies)
        
        # 4. Model-based anomaly detection
        if model_data:
            model_anomalies = self._detect_model_anomalies(current_metrics, model_data)
            anomalies_detected.extend(model_anomalies)
        
        return anomalies_detected
    
    def _detect_z_score_anomaly(
        self,
        current_value: Decimal,
        historical_values: List[Decimal]
    ) -> Optional[AnomalyDetectionResult]:
        """Detect anomalies using Z-score."""
        if len(historical_values) < 10:
            return None
        
        values_array = np.array([float(v) for v in historical_values])
        mean_val = np.mean(values_array)
        std_val = np.std(values_array, ddof=1)
        
        if std_val == 0:
            return None
        
        z_score = abs(float(current_value) - mean_val) / std_val
        
        if z_score > self.thresholds['z_score_threshold']:
            severity = min(z_score / 6.0, 1.0)  # Normalize severity
            
            return AnomalyDetectionResult(
                anomaly_type="statistical_zscore",
                severity=str(severity),
                anomaly_score=str(z_score),
                affected_components=[],  # Would map metric to component
                time_window=timedelta(hours=1),
                statistical_significance=str(min(1.0, z_score / 4.0)),
                root_cause_indicators=[
                    f"Z-score: {z_score:.2f}",
                    f"Mean: {mean_val:.4f}",
                    f"Std: {std_val:.4f}"
                ],
                market_context={'current_value': float(current_value)},
                resolution_suggestions=["Monitor closely", "Review data sources"]
            )
        
        return None
    
    def _detect_iqr_anomaly(
        self,
        current_value: Decimal,
        historical_values: List[Decimal]
    ) -> Optional[AnomalyDetectionResult]:
        """Detect anomalies using Interquartile Range."""
        if len(historical_values) < 20:
            return None
        
        values_array = np.array([float(v) for v in historical_values])
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - self.thresholds['iqr_multiplier'] * iqr
        upper_bound = q3 + self.thresholds['iqr_multiplier'] * iqr
        
        current_float = float(current_value)
        
        if current_float < lower_bound or current_float > upper_bound:
            # Determine severity based on distance from bounds
            if current_float < lower_bound:
                distance = lower_bound - current_float
            else:
                distance = current_float - upper_bound
            
            severity = min(distance / iqr, 1.0) if iqr > 0 else 0.5
            
            return AnomalyDetectionResult(
                anomaly_type="statistical_iqr",
                severity=str(severity),
                anomaly_score=str(distance / iqr) if iqr > 0 else '1.0',
                affected_components=[],
                time_window=timedelta(hours=1),
                statistical_significance=str(min(1.0, severity)),
                root_cause_indicators=[
                    f"Outside IQR bounds: [{lower_bound:.4f}, {upper_bound:.4f}]",
                    f"Current value: {current_float:.4f}",
                    f"IQR: {iqr:.4f}"
                ],
                market_context={'current_value': current_float},
                resolution_suggestions=["Validate data", "Check for data quality issues"]
            )
        
        return None
    
    def _detect_multivariate_anomaly(
        self,
        current_metrics: Dict[str, Decimal],
        historical_data: Dict[str, List[Decimal]]
    ) -> Optional[AnomalyDetectionResult]:
        """Detect multivariate anomalies."""
        # Prepare data for multivariate analysis
        common_metrics = set(current_metrics.keys()) & set(historical_data.keys())
        if len(common_metrics) < 3:
            return None
        
        # Create feature matrix
        features = []
        for metric in common_metrics:
            features.append([float(v) for v in historical_data[metric]])
        
        feature_matrix = np.array(features).T  # Transpose to have samples as rows
        
        if feature_matrix.shape[0] < 10:
            return None
        
        # Use Isolation Forest for anomaly detection
        try:
            clf = IsolationForest(contamination=self.thresholds['isolation_forest_contamination'])
            clf.fit(feature_matrix)
            
            # Predict current point
            current_point = np.array([[float(current_metrics[metric]) for metric in common_metrics]])
            anomaly_score = clf.decision_function(current_point)[0]
            is_anomaly = clf.predict(current_point)[0] == -1
            
            if is_anomaly or anomaly_score < -0.1:  # Threshold for anomaly score
                severity = min(abs(anomaly_score), 1.0)
                
                return AnomalyDetectionResult(
                    anomaly_type="multivariate_isolation_forest",
                    severity=str(severity),
                    anomaly_score=str(abs(anomaly_score)),
                    affected_components=[],  # Would map metrics to components
                    time_window=timedelta(hours=2),
                    statistical_significance=str(min(1.0, severity * 1.5)),
                    root_cause_indicators=[
                        f"Isolation Forest score: {anomaly_score:.3f}",
                        f"Number of features: {len(common_metrics)}",
                        "Multivariate pattern detected"
                    ],
                    market_context={'feature_vector': current_point.tolist()},
                    resolution_suggestions=["Review all affected metrics", "Investigate correlations"]
                )
        
        except Exception as e:
            self.logger.warning(f"Multivariate anomaly detection failed: {e}")
        
        return None
    
    def _detect_pattern_anomalies(
        self,
        current_metrics: Dict[str, Decimal],
        historical_data: Dict[str, List[Decimal]]
    ) -> List[AnomalyDetectionResult]:
        """Detect pattern-based anomalies."""
        anomalies = []
        
        for metric_name, current_value in current_metrics.items():
            if metric_name not in historical_data:
                continue
            
            historical_values = historical_data[metric_name]
            if len(historical_values) < 20:
                continue
            
            # Detect sudden changes
            recent_values = historical_values[-10:]
            older_values = historical_values[-20:-10] if len(historical_values) >= 20 else historical_values[:-10]
            
            if len(recent_values) > 0 and len(older_values) > 0:
                recent_mean = np.mean([float(v) for v in recent_values])
                older_mean = np.mean([float(v) for v in older_values])
                
                # Calculate change percentage
                change_pct = abs(recent_mean - older_mean) / abs(older_mean) if older_mean != 0 else 0
                
                if change_pct > 0.5:  # 50% change threshold
                    severity = min(change_pct, 1.0)
                    
                    anomalies.append(AnomalyDetectionResult(
                        anomaly_type="pattern_sudden_change",
                        severity=str(severity),
                        anomaly_score=str(change_pct),
                        affected_components=[],
                        time_window=timedelta(hours=6),
                        statistical_significance=str(min(1.0, change_pct / 2.0)),
                        root_cause_indicators=[
                            f"Sudden change: {change_pct:.1%}",
                            f"Recent mean: {recent_mean:.4f}",
                            f"Historical mean: {older_mean:.4f}"
                        ],
                        market_context={'change_magnitude': change_pct},
                        resolution_suggestions=["Monitor for continuation", "Check market events"]
                    ))
        
        return anomalies
    
    def _detect_model_anomalies(
        self,
        current_metrics: Dict[str, Decimal],
        model_data: Dict[str, List[Decimal]]
    ) -> List[AnomalyDetectionResult]:
        """Detect model-based anomalies."""
        anomalies = []
        
        for metric_name, current_value in current_metrics.items():
            if metric_name not in model_data:
                continue
            
            model_values = model_data[metric_name]
            if len(model_values) == 0:
                continue
            
            # Get model prediction (could be mean, median, or more sophisticated)
            model_prediction = np.mean([float(v) for v in model_values])
            current_float = float(current_value)
            
            # Calculate prediction error
            prediction_error = abs(current_float - model_prediction)
            relative_error = prediction_error / abs(model_prediction) if model_prediction != 0 else 0
            
            if relative_error > 0.3:  # 30% error threshold
                severity = min(relative_error, 1.0)
                
                anomalies.append(AnomalyDetectionResult(
                    anomaly_type="model_prediction_error",
                    severity=str(severity),
                    anomaly_score=str(relative_error),
                    affected_components=[],
                    time_window=timedelta(hours=3),
                    statistical_significance=str(min(1.0, relative_error / 2.0)),
                    root_cause_indicators=[
                        f"Prediction error: {relative_error:.1%}",
                        f"Expected: {model_prediction:.4f}",
                        f"Actual: {current_float:.4f}"
                    ],
                    market_context={
                        'predicted_value': model_prediction,
                        'actual_value': current_float,
                        'error_magnitude': prediction_error
                    },
                    resolution_suggestions=["Review model assumptions", "Retrain if necessary"]
                ))
        
        return anomalies


class PredictiveRiskModeler:
    """Advanced predictive risk modeling engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.models = {}
        self.prediction_horizons = {
            'short_term': timedelta(minutes=30),
            'medium_term': timedelta(hours=2),
            'long_term': timedelta(hours=24)
        }
        
    def predict_risk_evolution(
        self,
        historical_metrics: Dict[str, List[Tuple[datetime, Decimal]]],
        current_state: Dict[str, Decimal],
        external_factors: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict evolution of risk metrics over time.
        
        Args:
            historical_metrics: Historical time series data
            current_state: Current metric values
            external_factors: External factors affecting predictions
            
        Returns:
            Prediction results for different time horizons
        """
        predictions = {}
        
        # Short-term predictions (next 30 minutes)
        short_term = self._predict_short_term_risk(historical_metrics, current_state)
        predictions['short_term'] = short_term
        
        # Medium-term predictions (next 2 hours)
        medium_term = self._predict_medium_term_risk(historical_metrics, current_state)
        predictions['medium_term'] = medium_term
        
        # Long-term predictions (next 24 hours)
        long_term = self._predict_long_term_risk(historical_metrics, current_state)
        predictions['long_term'] = long_term
        
        # Combine predictions into overall risk forecast
        overall_forecast = self._generate_overall_risk_forecast(predictions)
        predictions['overall'] = overall_forecast
        
        return predictions
    
    def _predict_short_term_risk(
        self,
        historical_metrics: Dict[str, List[Tuple[datetime, Decimal]]],
        current_state: Dict[str, Decimal]
    ) -> Dict[str, Any]:
        """Predict short-term risk evolution."""
        horizon = self.prediction_horizons['short_term']
        predictions = {}
        
        for metric_name, time_series in historical_metrics.items():
            if len(time_series) < 10:
                continue
            
            # Extract recent trend
            recent_data = time_series[-10:]
            trend = self._calculate_trend(recent_data)
            
            # Simple linear extrapolation
            current_value = current_state.get(metric_name, recent_data[-1][1])
            time_diff_hours = horizon.total_seconds() / 3600
            predicted_value = current_value + trend * str(time_diff_hours)
            
            # Calculate prediction confidence
            confidence = self._calculate_prediction_confidence(recent_data, 'short_term')
            
            predictions[metric_name] = {
                'predicted_value': predicted_value,
                'confidence': confidence,
                'trend_direction': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable',
                'prediction_interval': self._calculate_prediction_interval(current_value, confidence)
            }
        
        return predictions
    
    def _predict_medium_term_risk(
        self,
        historical_metrics: Dict[str, List[Tuple[datetime, Decimal]]],
        current_state: Dict[str, Decimal]
    ) -> Dict[str, Any]:
        """Predict medium-term risk evolution."""
        horizon = self.prediction_horizons['medium_term']
        predictions = {}
        
        for metric_name, time_series in historical_metrics.items():
            if len(time_series) < 20:
                continue
            
            # Use moving average for medium-term prediction
            recent_data = time_series[-20:]
            ma_value = np.mean([float(v) for t, v in recent_data])
            
            # Apply trend adjustment
            trend = self._calculate_trend(recent_data)
            trend_adjustment = trend * str(horizon.total_seconds() / 3600)
            
            current_value = current_state.get(metric_name, recent_data[-1][1])
            predicted_value = str(ma_value) + trend_adjustment
            
            # Lower confidence for medium-term
            confidence = self._calculate_prediction_confidence(recent_data, 'medium_term')
            
            predictions[metric_name] = {
                'predicted_value': predicted_value,
                'confidence': confidence,
                'trend_direction': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable',
                'prediction_interval': self._calculate_prediction_interval(current_value, confidence),
                'volatility_factor': self._estimate_future_volatility(recent_data)
            }
        
        return predictions
    
    def _predict_long_term_risk(
        self,
        historical_metrics: Dict[str, List[Tuple[datetime, Decimal]]],
        current_state: Dict[str, Decimal]
    ) -> Dict[str, Any]:
        """Predict long-term risk evolution."""
        horizon = self.prediction_horizons['long_term']
        predictions = {}
        
        for metric_name, time_series in historical_metrics.items():
            if len(time_series) < 50:
                continue
            
            # Use seasonal/trend decomposition for long-term
            recent_data = time_series[-50:]
            
            # Calculate long-term mean and trend
            long_term_mean = np.mean([float(v) for t, v in recent_data])
            trend = self._calculate_trend(recent_data)
            
            # Mean reversion component
            current_value = current_state.get(metric_name, recent_data[-1][1])
            reversion_factor = '0.1'  # 10% reversion tendency
            reversion_component = (str(long_term_mean) - current_value) * reversion_factor
            
            # Apply trend and reversion
            time_diff_hours = horizon.total_seconds() / 3600
            trend_component = trend * str(time_diff_hours)
            
            predicted_value = current_value + trend_component + reversion_component
            
            # Significantly lower confidence for long-term
            confidence = self._calculate_prediction_confidence(recent_data, 'long_term') * '0.7'
            
            predictions[metric_name] = {
                'predicted_value': predicted_value,
                'confidence': confidence,
                'trend_direction': 'increasing' if trend > 0 else 'decreasing' if trend < 0 else 'stable',
                'prediction_interval': self._calculate_prediction_interval(current_value, confidence),
                'volatility_factor': self._estimate_future_volatility(recent_data),
                'mean_reversion_strength': reversion_factor
            }
        
        return predictions
    
    def _generate_overall_risk_forecast(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall risk forecast from component predictions."""
        overall = {}
        
        for horizon, horizon_predictions in predictions.items():
            if horizon == 'overall':
                continue
            
            # Aggregate risk across all metrics
            risk_scores = []
            confidences = []
            
            for metric_pred in horizon_predictions.values():
                if isinstance(metric_pred, dict) and 'predicted_value' in metric_pred:
                    # Calculate risk score from predicted value (assuming higher values = higher risk)
                    risk_score = float(metric_pred['predicted_value'])
                    confidence = float(metric_pred['confidence'])
                    
                    risk_scores.append(risk_score)
                    confidences.append(confidence)
            
            if risk_scores:
                # Weighted average based on confidence
                weighted_risk = np.average(risk_scores, weights=confidences)
                overall_confidence = np.mean(confidences)
                
                overall[horizon] = {
                    'predicted_risk_score': str(weighted_risk),
                    'confidence': str(overall_confidence),
                    'risk_trend': self._determine_overall_trend(horizon_predictions),
                    'key_risk_factors': self._identify_key_risk_factors(horizon_predictions)
                }
        
        return overall
    
    def _calculate_trend(self, time_series: List[Tuple[datetime, Decimal]]) -> Decimal:
        """Calculate trend from time series."""
        if len(time_series) < 2:
            return '0'
        
        values = [float(v) for t, v in time_series]
        n = len(values)
        
        # Simple linear trend
        x = np.arange(n)
        slope, _ = np.polyfit(x, values, 1)
        
        return str(slope)
    
    def _calculate_prediction_confidence(
        self,
        time_series: List[Tuple[datetime, Decimal]],
        horizon_type: str
    ) -> Decimal:
        """Calculate confidence in prediction based on data quality."""
        if len(time_series) < 5:
            return '0.3'
        
        # Base confidence on data length and consistency
        data_length_factor = min(len(time_series) / 50, 1.0)
        
        # Check for consistency (lower volatility = higher confidence)
        values = [float(v) for t, v in time_series[-20:]]  # Last 20 points
        volatility = np.std(values, ddof=1)
        mean_value = np.mean(values)
        
        if mean_value != 0:
            cv = volatility / abs(mean_value)  # Coefficient of variation
            consistency_factor = max(0.1, 1.0 - cv)
        else:
            consistency_factor = 0.5
        
        # Horizon adjustment
        horizon_adjustments = {
            'short_term': '1.0',
            'medium_term': '0.8',
            'long_term': '0.6'
        }
        
        horizon_factor = horizon_adjustments.get(horizon_type, '0.7')
        
        confidence = str(data_length_factor) * consistency_factor * horizon_factor
        
        return min(confidence, '1.0')
    
    def _calculate_prediction_interval(
        self,
        current_value: Decimal,
        confidence: Decimal
    ) -> Tuple[Decimal, Decimal]:
        """Calculate prediction interval."""
        # Wider intervals for lower confidence
        uncertainty_factor = '1.0' - confidence
        
        # Base interval width
        base_width = abs(current_value) * '0.1'  # 10% of current value
        
        # Adjust for uncertainty
        interval_width = base_width * ('1.0' + uncertainty_factor)
        
        lower_bound = current_value - interval_width
        upper_bound = current_value + interval_width
        
        return (lower_bound, upper_bound)
    
    def _estimate_future_volatility(self, time_series: List[Tuple[datetime, Decimal]]) -> Decimal:
        """Estimate future volatility."""
        if len(time_series) < 10:
            return '0.1'  # Default
        
        values = [float(v) for t, v in time_series]
        returns = np.diff(values) / values[:-1]  # Simple returns
        volatility = np.std(returns, ddof=1) if len(returns) > 0 else 0.1
        
        return str(volatility)
    
    def _determine_overall_trend(self, predictions: Dict[str, Any]) -> str:
        """Determine overall trend direction from predictions."""
        increasing_count = 0
        decreasing_count = 0
        stable_count = 0
        
        for pred in predictions.values():
            if isinstance(pred, dict) and 'trend_direction' in pred:
                direction = pred['trend_direction']
                if direction == 'increasing':
                    increasing_count += 1
                elif direction == 'decreasing':
                    decreasing_count += 1
                else:
                    stable_count += 1
        
        total = increasing_count + decreasing_count + stable_count
        if total == 0:
            return 'unknown'
        
        # Determine dominant trend
        if increasing_count > total * 0.6:
            return 'increasing'
        elif decreasing_count > total * 0.6:
            return 'decreasing'
        else:
            return 'stable'
    
    def _identify_key_risk_factors(self, predictions: Dict[str, Any]) -> List[str]:
        """Identify key risk factors from predictions."""
        risk_factors = []
        
        for metric_name, pred in predictions.items():
            if isinstance(pred, dict) and 'predicted_value' in pred:
                predicted_value = float(pred['predicted_value'])
                confidence = float(pred.get('confidence', 0.5))
                
                # High predicted values with good confidence are key risks
                if predicted_value > 0.7 and confidence > 0.6:
                    risk_factors.append(f"{metric_name}_elevated")
                elif predicted_value < 0.3 and confidence > 0.6:
                    risk_factors.append(f"{metric_name}_depressed")
        
        return risk_factors


class RealTimeRiskMonitor:
    """Real-time risk monitoring and alerting system."""
    
    def __init__(self, risk_classifier: RiskClassifier):
        self.risk_classifier = risk_classifier
        self.logger = logging.getLogger(__name__)
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        self.monitor_lock = threading.Lock()
        
        # Alert management
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.alert_thresholds = self._initialize_alert_thresholds()
        
        # Data storage
        self.metric_buffer = defaultdict(lambda: deque(maxlen=1000))
        self.risk_state_history = deque(maxlen=500)
        
        # Callback functions
        self.alert_callbacks = []
        self.risk_state_callbacks = []
        
    def start_monitoring(
        self,
        monitoring_interval: float = 30.0,
        enable_predictive_monitoring: bool = True
    ):
        """Start real-time risk monitoring."""
        with self.monitor_lock:
            if self.is_monitoring:
                self.logger.warning("Monitoring already active")
                return
            
            self.is_monitoring = True
            self.logger.info("Starting real-time risk monitoring")
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(
                target=self._monitoring_loop,
                args=(monitoring_interval, enable_predictive_monitoring),
                daemon=True
            )
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop real-time risk monitoring."""
        with self.monitor_lock:
            if not self.is_monitoring:
                return
            
            self.is_monitoring = False
            self.logger.info("Stopping real-time risk monitoring")
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)
    
    def register_alert_callback(self, callback: Callable[[RiskAlert], None]):
        """Register callback for alert notifications."""
        self.alert_callbacks.append(callback)
    
    def register_risk_state_callback(self, callback: Callable[[MarketRiskState], None]):
        """Register callback for risk state changes."""
        self.risk_state_callbacks.append(callback)
    
    def update_metrics(
        self,
        metrics: Dict[str, Decimal],
        timestamp: Optional[datetime] = None
    ):
        """Update monitoring metrics with new data."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        for metric_name, value in metrics.items():
            self.metric_buffer[metric_name].append((timestamp, value))
    
    def get_current_alerts(self) -> List[RiskAlert]:
        """Get currently active alerts."""
        return list(self.active_alerts.values())
    
    def get_risk_state_history(self, limit: int = 100) -> List[MarketRiskState]:
        """Get recent risk state history."""
        return list(self.risk_state_history)[-limit:]
    
    def _monitoring_loop(
        self,
        monitoring_interval: float,
        enable_predictive_monitoring: bool
    ):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                # Analyze current metrics
                self._analyze_current_risk_state()
                
                # Check for alerts
                self._check_alert_conditions()
                
                # Update predictive models if enabled
                if enable_predictive_monitoring:
                    self._update_predictive_models()
                
                time.sleep(monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(monitoring_interval)
    
    def _analyze_current_risk_state(self):
        """Analyze current risk state from metrics."""
        if not self.metric_buffer:
            return
        
        # Get latest values for each metric
        latest_metrics = {}
        for metric_name, buffer in self.metric_buffer.items():
            if buffer:
                latest_metrics[metric_name] = buffer[-1][1]
        
        if not latest_metrics:
            return
        
        # Assess market condition (simplified)
        market_condition = self._assess_market_condition(latest_metrics)
        
        # Assess overall risk score
        overall_risk_score = self._calculate_overall_risk_score(latest_metrics)
        
        # Create risk state
        risk_state = MarketRiskState(
            market_condition=market_condition,
            volatility_regime=self._assess_volatility_regime(latest_metrics),
            liquidity_regime=self._assess_liquidity_regime(latest_metrics),
            correlation_regime=self._assess_correlation_regime(latest_metrics),
            overall_risk_score=overall_risk_score,
            regime_stability=self._assess_regime_stability(),
            regime_transition_probability=self._calculate_regime_transition_probability(),
            time_since_last_change=timedelta(hours=1),  # Simplified
            regime_confidence='0.7'
        )
        
        # Store in history
        self.risk_state_history.append(risk_state)
        
        # Notify callbacks
        for callback in self.risk_state_callbacks:
            try:
                callback(risk_state)
            except Exception as e:
                self.logger.error(f"Error in risk state callback: {e}")
    
    def _check_alert_conditions(self):
        """Check for conditions that should trigger alerts."""
        if not self.metric_buffer:
            return
        
        # Check each alert threshold
        for alert_type, threshold_config in self.alert_thresholds.items():
            try:
                self._check_single_alert_condition(alert_type, threshold_config)
            except Exception as e:
                self.logger.error(f"Error checking alert condition {alert_type}: {e}")
    
    def _check_single_alert_condition(
        self,
        alert_type: str,
        threshold_config: Dict[str, Any]
    ):
        """Check a single alert condition."""
        metric_name = threshold_config.get('metric')
        if not metric_name or metric_name not in self.metric_buffer:
            return
        
        buffer = self.metric_buffer[metric_name]
        if len(buffer) < threshold_config.get('min_points', 5):
            return
        
        # Get recent values
        recent_values = [v for t, v in buffer[-threshold_config.get('window_size', 10):]]
        
        # Check threshold condition
        threshold_value = threshold_config['threshold']
        condition = threshold_config.get('condition', 'greater_than')
        
        current_value = recent_values[-1]
        
        should_alert = False
        if condition == 'greater_than' and current_value > threshold_value:
            should_alert = True
        elif condition == 'less_than' and current_value < threshold_value:
            should_alert = True
        elif condition == 'equals' and abs(current_value - threshold_value) < threshold_config.get('tolerance', '0.01'):
            should_alert = True
        
        if should_alert:
            self._trigger_alert(alert_type, current_value, threshold_config, recent_values)
    
    def _trigger_alert(
        self,
        alert_type: str,
        current_value: Decimal,
        threshold_config: Dict[str, Any],
        recent_values: List[Decimal]
    ):
        """Trigger an alert."""
        alert_id = f"{alert_type}_{int(time.time())}"
        
        # Determine severity
        severity = AlertSeverity.MEDIUM
        if alert_type in ['market_volatility_spike', 'execution_failure_risk']:
            severity = AlertSeverity.HIGH
        elif alert_type in ['model_uncertainty', 'regime_change']:
            severity = AlertSeverity.LOW
        
        # Create alert
        alert = RiskAlert(
            alert_id=alert_id,
            alert_type=AlertType(alert_type),
            severity=severity,
            title=threshold_config.get('title', f"{alert_type.replace('_', ' ').title()} Alert"),
            description=threshold_config.get('description', f"Threshold exceeded: {current_value}"),
            metrics_snapshot={'current_value': current_value},
            recommendations=threshold_config.get('recommendations', []),
            escalation_required=severity == AlertSeverity.HIGH
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
        
        self.logger.warning(f"Alert triggered: {alert.title} - {alert.description}")
    
    def _update_predictive_models(self):
        """Update predictive models with new data."""
        # This would update machine learning models
        # For now, just clear old data periodically
        if len(self.alert_history) % 100 == 0:
            self.logger.info("Maintaining predictive model data")
    
    def _initialize_alert_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Initialize alert thresholds."""
        return {
            'market_volatility_spike': {
                'metric': 'market_volatility',
                'threshold': '0.3',
                'condition': 'greater_than',
                'window_size': 10,
                'title': 'Market Volatility Spike',
                'description': 'Market volatility has increased significantly',
                'recommendations': ['Monitor positions closely', 'Consider reducing exposure']
            },
            'liquidity_deterioration': {
                'metric': 'liquidity_score',
                'threshold': '0.4',
                'condition': 'less_than',
                'window_size': 10,
                'title': 'Liquidity Deterioration',
                'description': 'Market liquidity has decreased significantly',
                'recommendations': ['Reduce position sizes', 'Avoid large orders']
            },
            'execution_failure_risk': {
                'metric': 'execution_success_rate',
                'threshold': '0.7',
                'condition': 'less_than',
                'window_size': 15,
                'title': 'High Execution Failure Risk',
                'description': 'Execution success rate has dropped',
                'recommendations': ['Review execution methods', 'Check bookmaker status']
            },
            'time_sensitivity': {
                'metric': 'timing_urgency',
                'threshold': '0.8',
                'condition': 'greater_than',
                'window_size': 5,
                'title': 'High Time Sensitivity',
                'description': 'Time-sensitive opportunities detected',
                'recommendations': ['Prioritize execution', 'Monitor closely']
            }
        }
    
    def _assess_market_condition(self, metrics: Dict[str, Decimal]) -> MarketCondition:
        """Assess current market condition."""
        volatility = metrics.get('market_volatility', '0.2')
        liquidity = metrics.get('liquidity_score', '0.7')
        
        if volatility > '0.4' and liquidity < '0.5':
            return MarketCondition.EMERGENCY
        elif volatility > '0.3':
            return MarketCondition.STRESSED
        elif volatility > '0.2':
            return MarketCondition.VOLATILE
        elif liquidity > '0.8':
            return MarketCondition.CALM
        else:
            return MarketCondition.NORMAL
    
    def _calculate_overall_risk_score(self, metrics: Dict[str, Decimal]) -> Decimal:
        """Calculate overall risk score from metrics."""
        if not metrics:
            return '0.5'
        
        # Weighted combination of key risk metrics
        weights = {
            'market_volatility': '0.3',
            'liquidity_score': '0.25',  # Inverted
            'execution_success_rate': '0.2',  # Inverted
            'timing_urgency': '0.15',
            'model_confidence': '0.1'  # Inverted
        }
        
        total_score = '0'
        total_weight = '0'
        
        for metric, weight in weights.items():
            if metric in metrics:
                value = metrics[metric]
                
                # Invert certain metrics (lower is better)
                if metric in ['liquidity_score', 'execution_success_rate', 'model_confidence']:
                    value = '1.0' - value
                
                total_score += value * weight
                total_weight += weight
        
        if total_weight > 0:
            return total_score / total_weight
        
        return '0.5'
    
    def _assess_volatility_regime(self, metrics: Dict[str, Decimal]) -> str:
        """Assess volatility regime."""
        volatility = metrics.get('market_volatility', '0.2')
        
        if volatility > '0.4':
            return "high_volatility"
        elif volatility > '0.25':
            return "elevated_volatility"
        elif volatility > '0.15':
            return "normal_volatility"
        else:
            return "low_volatility"
    
    def _assess_liquidity_regime(self, metrics: Dict[str, Decimal]) -> str:
        """Assess liquidity regime."""
        liquidity = metrics.get('liquidity_score', '0.7')
        
        if liquidity > '0.8':
            return "deep_liquid"
        elif liquidity > '0.6':
            return "adequate_liquid"
        elif liquidity > '0.4':
            return "shallow_liquid"
        else:
            return "illiquid"
    
    def _assess_correlation_regime(self, metrics: Dict[str, Decimal]) -> str:
        """Assess correlation regime."""
        correlation = metrics.get('correlation_coefficient', '0.5')
        
        if correlation > '0.8':
            return "high_correlation"
        elif correlation > '0.6':
            return "elevated_correlation"
        elif correlation > '0.3':
            return "normal_correlation"
        else:
            return "low_correlation"
    
    def _assess_regime_stability(self) -> Decimal:
        """Assess stability of current regime."""
        if len(self.risk_state_history) < 5:
            return '0.5'
        
        # Check for recent regime changes
        recent_states = list(self.risk_state_history)[-5:]
        unique_conditions = len(set(state.market_condition for state in recent_states))
        
        if unique_conditions == 1:
            return '0.9'  # Very stable
        elif unique_conditions == 2:
            return '0.7'  # Moderately stable
        else:
            return '0.4'  # Unstable
    
    def _calculate_regime_transition_probability(self) -> Decimal:
        """Calculate probability of regime transition."""
        stability = self._assess_regime_stability()
        return '1.0' - stability


class RiskAnalyzer:
    """
    Main risk analyzer providing real-time risk analysis with pattern recognition,
    anomaly detection, and predictive risk modeling.
    """
    
    def __init__(self):
        """Initialize the risk analyzer."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.risk_classifier = RiskClassifier()
        self.risk_calculator = RiskCalculator()
        self.pattern_engine = PatternRecognitionEngine()
        self.anomaly_detector = AnomalyDetector()
        self.predictive_modeler = PredictiveRiskModeler()
        self.monitor = RealTimeRiskMonitor(self.risk_classifier)
        
        # Analysis state
        self.analysis_cache = {}
        self.max_cache_size = 500
        
        # Performance metrics
        self.analysis_times = deque(maxlen=100)
        
        self.logger.info("Risk analyzer initialized")
    
    def analyze_opportunity_comprehensive(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None,
        historical_data: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive risk analysis of arbitrage opportunity.
        
        Args:
            opportunity: Arbitrage opportunity to analyze
            market_data: Market context data
            historical_data: Historical performance data
            user_preferences: User preferences and settings
            
        Returns:
            Comprehensive analysis results
        """
        start_time = time.time()
        
        try:
            # 1. Risk classification
            classification_result = self.risk_classifier.classify_arbitrage_risk(
                opportunity, market_data, historical_data, 
                user_preferences.get('risk_tolerance') if user_preferences else None
            )
            
            # 2. Pattern recognition
            if market_data and 'time_series' in market_data:
                patterns = self.pattern_engine.detect_patterns(
                    market_data['time_series']
                )
            else:
                patterns = []
            
            # 3. Anomaly detection
            current_metrics = self._extract_current_metrics(opportunity, classification_result)
            historical_metrics = self._extract_historical_metrics(historical_data)
            anomalies = self.anomaly_detector.detect_anomalies(
                current_metrics, historical_metrics
            )
            
            # 4. Predictive modeling
            if historical_metrics:
                prediction_results = self.predictive_modeler.predict_risk_evolution(
                    historical_metrics, current_metrics
                )
            else:
                prediction_results = {}
            
            # 5. Real-time risk assessment
            risk_state = self._assess_current_risk_state(
                opportunity, classification_result, market_data
            )
            
            # 6. Generate comprehensive report
            analysis_result = {
                'opportunity_id': str(opportunity.id),
                'analysis_timestamp': datetime.utcnow(),
                'classification': classification_result,
                'patterns_detected': patterns,
                'anomalies_detected': anomalies,
                'predictions': prediction_results,
                'risk_state': risk_state,
                'recommendations': self._generate_comprehensive_recommendations(
                    classification_result, patterns, anomalies, risk_state
                ),
                'risk_metrics': self._calculate_additional_risk_metrics(
                    opportunity, classification_result
                ),
                'monitoring_alerts': self.monitor.get_current_alerts(),
                'analysis_confidence': self._calculate_analysis_confidence(
                    classification_result, patterns, anomalies
                ),
                'performance_metrics': {
                    'analysis_time_seconds': str(time.time( - start_time)),
                    'cache_hit': False,
                    'components_analyzed': len(patterns) + len(anomalies)
                }
            }
            
            # Cache result
            self._cache_analysis_result(str(opportunity.id), analysis_result)
            
            self.logger.info(f"Comprehensive analysis completed for opportunity {opportunity.id}")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Comprehensive analysis failed: {e}")
            raise
    
    def start_real_time_monitoring(
        self,
        monitoring_interval: float = 30.0,
        alert_callbacks: Optional[List[Callable]] = None
    ):
        """Start real-time risk monitoring."""
        if alert_callbacks:
            for callback in alert_callbacks:
                self.monitor.register_alert_callback(callback)
        
        self.monitor.start_monitoring(monitoring_interval)
        self.logger.info("Real-time risk monitoring started")
    
    def stop_real_time_monitoring(self):
        """Stop real-time risk monitoring."""
        self.monitor.stop_monitoring()
        self.logger.info("Real-time risk monitoring stopped")
    
    def update_monitoring_data(
        self,
        metrics: Dict[str, Decimal],
        timestamp: Optional[datetime] = None
    ):
        """Update monitoring system with new data."""
        self.monitor.update_metrics(metrics, timestamp)
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'is_monitoring': self.monitor.is_monitoring,
            'active_alerts': len(self.monitor.active_alerts),
            'alert_history_size': len(self.monitor.alert_history),
            'risk_state_history_size': len(self.monitor.risk_state_history),
            'metric_buffers': {k: len(v) for k, v in self.monitor.metric_buffer.items()}
        }
    
    def generate_risk_report(
        self,
        time_period: timedelta = timedelta(hours=24),
        include_predictions: bool = True,
        include_patterns: bool = True,
        include_anomalies: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive risk report."""
        self.logger.info("Generating comprehensive risk report")
        
        # Get monitoring status
        monitoring_status = self.get_monitoring_status()
        
        # Get alert history
        recent_alerts = list(self.monitor.alert_history)
        if time_period != timedelta.max:
            cutoff_time = datetime.utcnow() - time_period
            recent_alerts = [alert for alert in recent_alerts if alert.created_at >= cutoff_time]
        
        # Get risk state history
        risk_state_history = self.monitor.get_risk_state_history()
        if time_period != timedelta.max:
            risk_state_history = [
                state for state in risk_state_history 
                if state.assessment_timestamp >= cutoff_time
            ]
        
        # Analyze trends
        alert_trends = self._analyze_alert_trends(recent_alerts)
        risk_trends = self._analyze_risk_trends(risk_state_history)
        
        # Compile report
        report = {
            'report_metadata': {
                'generation_time': datetime.utcnow(),
                'time_period': time_period,
                'include_predictions': include_predictions,
                'include_patterns': include_patterns,
                'include_anomalies': include_anomalies
            },
            'monitoring_status': monitoring_status,
            'alert_summary': {
                'total_alerts': len(recent_alerts),
                'active_alerts': len(self.monitor.active_alerts),
                'alert_severity_breakdown': self._get_alert_severity_breakdown(recent_alerts),
                'alert_type_breakdown': self._get_alert_type_breakdown(recent_alerts),
                'alert_trends': alert_trends
            },
            'risk_state_summary': {
                'current_state': risk_state_history[-1] if risk_state_history else None,
                'regime_stability': self._assess_regime_stability_summary(risk_state_history),
                'risk_trends': risk_trends,
                'state_transitions': self._count_regime_transitions(risk_state_history)
            },
            'performance_metrics': {
                'average_analysis_time': self._calculate_average_analysis_time(),
                'total_analyses_performed': len(self.analysis_times),
                'cache_performance': self._get_cache_performance()
            },
            'recommendations': self._generate_report_recommendations(
                recent_alerts, risk_state_history
            )
        }
        
        self.logger.info("Comprehensive risk report generated")
        return report
    
    def _extract_current_metrics(
        self,
        opportunity: ArbitrageOpportunity,
        classification_result: RiskClassificationResult
    ) -> Dict[str, Decimal]:
        """Extract current metrics from analysis results."""
        metrics = {}
        
        # Extract from classification result
        for component_score in classification_result.component_scores:
            metrics[f"{component_score.component.value}_score"] = component_score.score
        
        # Extract key opportunity metrics
        metrics['profit_margin'] = opportunity.profit_margin
        metrics['total_stake'] = opportunity.total_stake
        metrics['liquidity_score'] = self._estimate_current_liquidity_score(opportunity)
        metrics['execution_success_rate'] = self._estimate_execution_success_rate(classification_result)
        metrics['timing_urgency'] = self._calculate_timing_urgency(opportunity)
        metrics['model_confidence'] = classification_result.confidence_score
        
        return metrics
    
    def _extract_historical_metrics(
        self, 
        historical_data: Optional[Dict[str, Any]]
    ) -> Dict[str, List[Tuple[datetime, Decimal]]]:
        """Extract historical metrics from historical data."""
        if not historical_data:
            return {}
        
        # Convert historical data to time series format
        time_series = {}
        
        if 'returns' in historical_data:
            returns = historical_data['returns']
            time_series['returns'] = [
                (datetime.utcnow() - timedelta(hours=len(returns)-i), str(r))
                for i, r in enumerate(returns)
            ]
        
        if 'volatility' in historical_data:
            volatility = historical_data['volatility']
            time_series['market_volatility'] = [
                (datetime.utcnow() - timedelta(hours=len(volatility)-i), str(v))
                for i, v in enumerate(volatility)
            ]
        
        return time_series
    
    def _assess_current_risk_state(
        self,
        opportunity: ArbitrageOpportunity,
        classification_result: RiskClassificationResult,
        market_data: Optional[Dict[str, Any]]
    ) -> MarketRiskState:
        """Assess current risk state."""
        # Extract current metrics
        current_metrics = self._extract_current_metrics(opportunity, classification_result)
        
        # Assess components
        market_condition = self._assess_market_condition_from_metrics(current_metrics)
        volatility_regime = self._assess_volatility_regime_from_metrics(current_metrics)
        liquidity_regime = self._assess_liquidity_regime_from_metrics(current_metrics)
        correlation_regime = self._assess_correlation_regime_from_metrics(current_metrics)
        
        # Calculate overall risk score
        overall_risk_score = self._calculate_overall_risk_score_from_metrics(current_metrics)
        
        return MarketRiskState(
            market_condition=market_condition,
            volatility_regime=volatility_regime,
            liquidity_regime=liquidity_regime,
            correlation_regime=correlation_regime,
            overall_risk_score=overall_risk_score,
            regime_stability='0.7',  # Default assumption
            regime_transition_probability='0.3',
            time_since_last_change=timedelta(hours=1),
            regime_confidence=classification_result.confidence_score
        )
    
    def _generate_comprehensive_recommendations(
        self,
        classification_result: RiskClassificationResult,
        patterns: List[PatternDetectionResult],
        anomalies: List[AnomalyDetectionResult],
        risk_state: MarketRiskState
    ) -> List[str]:
        """Generate comprehensive recommendations."""
        recommendations = []
        
        # Add classification recommendations
        recommendations.extend(classification_result.recommendations)
        
        # Add pattern-based recommendations
        for pattern in patterns:
            if pattern.pattern_significance > '0.7':
                recommendations.append(f"Pattern detected: {pattern.pattern_type.value} - monitor closely")
        
        # Add anomaly-based recommendations
        for anomaly in anomalies:
            if anomaly.severity > '0.6':
                recommendations.extend(anomaly.resolution_suggestions)
        
        # Add risk state recommendations
        if risk_state.overall_risk_score > '0.7':
            recommendations.append("High overall risk detected - consider reducing exposure")
        
        if risk_state.market_condition in [MarketCondition.STRESSED, MarketCondition.EMERGENCY]:
            recommendations.append("Stressful market conditions - implement additional risk controls")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _calculate_additional_risk_metrics(
        self,
        opportunity: ArbitrageOpportunity,
        classification_result: RiskClassificationResult
    ) -> Dict[str, Decimal]:
        """Calculate additional risk metrics."""
        # This would integrate with the risk calculator for VaR, etc.
        # For now, return simplified metrics
        
        return {
            'position_concentration': min(opportunity.total_stake / '10000', '1.0'),
            'bookmaker_diversity': str(len(set(leg.bookmaker for leg in opportunity.legs))),
            'time_pressure': self._calculate_time_pressure(opportunity),
            'execution_complexity': str(len(opportunity.legs)) / '5',
            'profit_margin_risk': '1.0' - min(opportunity.profit_margin / '0.10', '1.0')
        }
    
    def _calculate_analysis_confidence(
        self,
        classification_result: RiskClassificationResult,
        patterns: List[PatternDetectionResult],
        anomalies: List[AnomalyDetectionResult]
    ) -> Decimal:
        """Calculate overall analysis confidence."""
        # Base confidence from classification
        base_confidence = classification_result.confidence_score
        
        # Adjust for patterns (more patterns = more insight)
        pattern_confidence = '1.0' - str(0.1 * len(patterns))
        
        # Adjust for anomalies (anomalies reduce confidence)
        anomaly_penalty = str(0.05 * len(anomalies))
        
        overall_confidence = base_confidence * pattern_confidence - anomaly_penalty
        
        return max(min(overall_confidence, '1.0'), '0.3')
    
    def _cache_analysis_result(self, opportunity_id: str, result: Dict[str, Any]):
        """Cache analysis result for performance."""
        if len(self.analysis_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.analysis_cache))
            del self.analysis_cache[oldest_key]
        
        self.analysis_cache[opportunity_id] = result
    
    # Helper methods for assessment and analysis
    
    def _estimate_current_liquidity_score(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Estimate current liquidity score."""
        # Simplified estimation based on opportunity characteristics
        base_score = '0.7'
        
        # Adjust for bookmaker count
        bookmaker_bonus = min(len(opportunity.legs) * '0.05', '0.2')
        
        # Adjust for profit margin (higher margin = potentially lower liquidity)
        margin_adjustment = max('0.0', '0.1' - opportunity.profit_margin * '0.5')
        
        return min(base_score + bookmaker_bonus + margin_adjustment, '1.0')
    
    def _estimate_execution_success_rate(
        self, 
        classification_result: RiskClassificationResult
    ) -> Decimal:
        """Estimate execution success rate."""
        # Extract from component scores
        execution_component = None
        for component in classification_result.component_scores:
            if component.component.value == 'execution_difficulty':
                execution_component = component
                break
        
        if execution_component:
            return execution_component.score
        else:
            return '0.8'  # Default
    
    def _calculate_timing_urgency(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Calculate timing urgency score."""
        time_to_event = opportunity.event_date - datetime.utcnow()
        hours_to_event = time_to_event.total_seconds() / 3600
        
        if hours_to_event <= 1:
            return '1.0'  # Maximum urgency
        elif hours_to_event <= 6:
            return '0.8'
        elif hours_to_event <= 24:
            return '0.6'
        else:
            return '0.3'  # Low urgency
    
    def _assess_market_condition_from_metrics(self, metrics: Dict[str, Decimal]) -> MarketCondition:
        """Assess market condition from metrics."""
        volatility = metrics.get('market_volatility', '0.2')
        liquidity = metrics.get('liquidity_score', '0.7')
        
        if volatility > '0.4' and liquidity < '0.4':
            return MarketCondition.EMERGENCY
        elif volatility > '0.3':
            return MarketCondition.STRESSED
        elif volatility > '0.2':
            return MarketCondition.VOLATILE
        else:
            return MarketCondition.NORMAL
    
    def _assess_volatility_regime_from_metrics(self, metrics: Dict[str, Decimal]) -> str:
        """Assess volatility regime from metrics."""
        volatility = metrics.get('market_volatility', '0.2')
        
        if volatility > '0.4':
            return "high_volatility"
        elif volatility > '0.25':
            return "elevated_volatility"
        elif volatility > '0.15':
            return "normal_volatility"
        else:
            return "low_volatility"
    
    def _assess_liquidity_regime_from_metrics(self, metrics: Dict[str, Decimal]) -> str:
        """Assess liquidity regime from metrics."""
        liquidity = metrics.get('liquidity_score', '0.7')
        
        if liquidity > '0.8':
            return "deep_liquid"
        elif liquidity > '0.6':
            return "adequate_liquid"
        elif liquidity > '0.4':
            return "shallow_liquid"
        else:
            return "illiquid"
    
    def _assess_correlation_regime_from_metrics(self, metrics: Dict[str, Decimal]) -> str:
        """Assess correlation regime from metrics."""
        correlation = metrics.get('correlation_coefficient', '0.5')
        
        if correlation > '0.8':
            return "high_correlation"
        elif correlation > '0.6':
            return "elevated_correlation"
        elif correlation > '0.3':
            return "normal_correlation"
        else:
            return "low_correlation"
    
    def _calculate_overall_risk_score_from_metrics(self, metrics: Dict[str, Decimal]) -> Decimal:
        """Calculate overall risk score from metrics."""
        if not metrics:
            return '0.5'
        
        # Similar to earlier implementation but adapted for metrics dict
        weights = {
            'market_volatility': '0.3',
            'liquidity_score': '0.25',
            'execution_success_rate': '0.2',
            'timing_urgency': '0.15',
            'model_confidence': '0.1'
        }
        
        total_score = '0'
        total_weight = '0'
        
        for metric, weight in weights.items():
            if metric in metrics:
                value = metrics[metric]
                
                # Invert certain metrics
                if metric in ['liquidity_score', 'execution_success_rate', 'model_confidence']:
                    value = '1.0' - value
                
                total_score += value * weight
                total_weight += weight
        
        if total_weight > 0:
            return total_score / total_weight
        
        return '0.5'
    
    def _calculate_time_pressure(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Calculate time pressure score."""
        time_to_event = opportunity.event_date - datetime.utcnow()
        minutes_to_event = time_to_event.total_seconds() / 60
        
        if minutes_to_event <= 30:
            return '1.0'  # Very high pressure
        elif minutes_to_event <= 120:
            return '0.8'
        elif minutes_to_event <= 480:
            return '0.6'
        else:
            return '0.3'  # Low pressure
    
    def _analyze_alert_trends(self, alerts: List[RiskAlert]) -> Dict[str, Any]:
        """Analyze trends in alerts."""
        if not alerts:
            return {'trend': 'stable', 'change_rate': '0.0'}
        
        # Sort by creation time
        sorted_alerts = sorted(alerts, key=lambda a: a.created_at)
        
        # Calculate alert frequency over time
        hourly_counts = defaultdict(int)
        for alert in sorted_alerts:
            hour = alert.created_at.replace(minute=0, second=0, microsecond=0)
            hourly_counts[hour] += 1
        
        if len(hourly_counts) < 2:
            return {'trend': 'stable', 'change_rate': '0.0'}
        
        # Calculate trend
        times = sorted(hourly_counts.keys())
        counts = [hourly_counts[t] for t in times]
        
        if len(counts) >= 2:
            recent_avg = np.mean(counts[-3:]) if len(counts) >= 3 else counts[-1]
            earlier_avg = np.mean(counts[:-3]) if len(counts) > 3 else np.mean(counts[:-1])
            
            if earlier_avg > 0:
                change_rate = (recent_avg - earlier_avg) / earlier_avg
            else:
                change_rate = 0
            
            if change_rate > 0.2:
                trend = 'increasing'
            elif change_rate < -0.2:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            return {
                'trend': trend,
                'change_rate': str(change_rate),
                'current_frequency': str(recent_avg),
                'previous_frequency': str(earlier_avg)
            }
        
        return {'trend': 'stable', 'change_rate': '0.0'}
    
    def _analyze_risk_trends(self, risk_states: List[MarketRiskState]) -> Dict[str, Any]:
        """Analyze trends in risk states."""
        if len(risk_states) < 2:
            return {'trend': 'stable', 'stability_score': '0.5'}
        
        # Calculate risk score trend
        recent_scores = [float(state.overall_risk_score) for state in risk_states[-10:]]
        overall_trend = 'increasing' if recent_scores[-1] > recent_scores[0] else 'decreasing' if recent_scores[-1] < recent_scores[0] else 'stable'
        
        # Calculate stability
        score_changes = np.diff(recent_scores)
        stability_score = 1.0 - min(np.std(score_changes), 1.0)
        
        return {
            'trend': overall_trend,
            'stability_score': str(stability_score),
            'current_risk_level': risk_states[-1].overall_risk_score,
            'risk_volatility': str(np.std(score_changes))
        }
    
    def _get_alert_severity_breakdown(self, alerts: List[RiskAlert]) -> Dict[str, int]:
        """Get breakdown of alerts by severity."""
        breakdown = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for alert in alerts:
            breakdown[alert.severity.value] += 1
        return breakdown
    
    def _get_alert_type_breakdown(self, alerts: List[RiskAlert]) -> Dict[str, int]:
        """Get breakdown of alerts by type."""
        breakdown = defaultdict(int)
        for alert in alerts:
            breakdown[alert.alert_type.value] += 1
        return dict(breakdown)
    
    def _assess_regime_stability_summary(self, risk_states: List[MarketRiskState]) -> Decimal:
        """Assess regime stability summary."""
        if len(risk_states) < 2:
            return '0.5'
        
        # Count regime changes
        changes = 0
        for i in range(1, len(risk_states)):
            if risk_states[i].market_condition != risk_states[i-1].market_condition:
                changes += 1
        
        change_rate = changes / (len(risk_states) - 1)
        stability = max(0.0, 1.0 - change_rate)
        
        return str(stability)
    
    def _count_regime_transitions(self, risk_states: List[MarketRiskState]) -> int:
        """Count number of regime transitions."""
        if len(risk_states) < 2:
            return 0
        
        transitions = 0
        for i in range(1, len(risk_states)):
            if risk_states[i].market_condition != risk_states[i-1].market_condition:
                transitions += 1
        
        return transitions
    
    def _calculate_average_analysis_time(self) -> Decimal:
        """Calculate average analysis time."""
        if not self.analysis_times:
            return '0.0'
        
        avg_time = np.mean(list(self.analysis_times))
        return str(avg_time)
    
    def _get_cache_performance(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        return {
            'cache_size': len(self.analysis_cache),
            'cache_hit_rate': '0.0',  # Would track actual hit rate
            'max_cache_size': self.max_cache_size
        }
    
    def _generate_report_recommendations(
        self,
        alerts: List[RiskAlert],
        risk_states: List[MarketRiskState]
    ) -> List[str]:
        """Generate recommendations based on report data."""
        recommendations = []
        
        # Alert-based recommendations
        if len(alerts) > 10:
            recommendations.append("High alert frequency detected - review monitoring thresholds")
        
        # High severity alerts
        high_severity_alerts = [a for a in alerts if a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]]
        if high_severity_alerts:
            recommendations.append(f"Investigate {len(high_severity_alerts)} high-severity alerts")
        
        # Risk state recommendations
        if risk_states:
            current_state = risk_states[-1]
            if current_state.overall_risk_score > '0.7':
                recommendations.append("Overall risk level is elevated - consider risk mitigation")
            
            if current_state.regime_transition_probability > '0.5':
                recommendations.append("High regime transition probability - prepare for market changes")
        
        return recommendations


# Create logger instance
logger = logging.getLogger(__name__)