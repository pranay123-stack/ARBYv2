"""
Performance Monitoring System for Browser Operations

This module provides comprehensive performance monitoring and optimization:
- Response time tracking and analysis
- Throughput measurement and optimization
- Performance bottleneck identification
- Resource utilization monitoring
- Optimization recommendations
- Performance trend analysis
- Automated performance alerting

Features:
- Real-time performance metrics collection
- Historical performance analysis
- Performance regression detection
- Automated optimization suggestions
- Performance reporting and dashboards
- Integration with monitoring systems
"""

import asyncio
import time
import statistics
import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from collections import deque, defaultdict
import logging
import threading
import weakref

from arbitech.risk.monitoring_system import get_monitoring_system, PerformanceMetric, MetricType
from arbitech.storage.audit_logger import get_audit_logger, log_performance_metric
from arbitech.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import Selenium for performance testing
try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available - performance testing will be limited")


class MetricCategory(Enum):
    """Performance metric categories"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    RESOURCE_USAGE = "resource_usage"
    ERROR_RATE = "error_rate"
    PAGE_PERFORMANCE = "page_performance"
    NETWORK = "network"
    MEMORY = "memory"
    CPU = "cpu"


class PerformanceLevel(Enum):
    """Performance levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class OptimizationType(Enum):
    """Types of performance optimizations"""
    MEMORY_OPTIMIZATION = "memory_optimization"
    CPU_OPTIMIZATION = "cpu_optimization"
    NETWORK_OPTIMIZATION = "network_optimization"
    PAGE_OPTIMIZATION = "page_optimization"
    CACHING_OPTIMIZATION = "caching_optimization"
    SCRIPT_OPTIMIZATION = "script_optimization"
    RESOURCE_OPTIMIZATION = "resource_optimization"


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration"""
    metric_name: str
    category: MetricCategory
    
    # Thresholds for different performance levels
    excellent_threshold: Optional[float] = None
    good_threshold: Optional[float] = None
    fair_threshold: Optional[float] = None
    poor_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    
    # Unit of measurement
    unit: str = ""
    
    # Direction: lower is better or higher is better
    lower_is_better: bool = True
    
    def evaluate_performance(self, value: float) -> PerformanceLevel:
        """Evaluate performance level based on value"""
        if self.lower_is_better:
            # Lower values are better
            if self.excellent_threshold is not None and value <= self.excellent_threshold:
                return PerformanceLevel.EXCELLENT
            elif self.good_threshold is not None and value <= self.good_threshold:
                return PerformanceLevel.GOOD
            elif self.fair_threshold is not None and value <= self.fair_threshold:
                return PerformanceLevel.FAIR
            elif self.poor_threshold is not None and value <= self.poor_threshold:
                return PerformanceLevel.POOR
            else:
                return PerformanceLevel.CRITICAL
        else:
            # Higher values are better
            if self.excellent_threshold is not None and value >= self.excellent_threshold:
                return PerformanceLevel.EXCELLENT
            elif self.good_threshold is not None and value >= self.good_threshold:
                return PerformanceLevel.GOOD
            elif self.fair_threshold is not None and value >= self.fair_threshold:
                return PerformanceLevel.FAIR
            elif self.poor_threshold is not None and value >= self.poor_threshold:
                return PerformanceLevel.POOR
            else:
                return PerformanceLevel.CRITICAL


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    metric_id: UUID = field(default_factory=uuid4)
    metric_name: str = ""
    category: MetricCategory = MetricCategory.RESPONSE_TIME
    
    # Value and unit
    value: float = 0.0
    unit: str = ""
    
    # Context
    browser_id: Optional[str] = None
    page_url: str = ""
    operation_type: str = ""  # page_load, element_find, click, etc.
    
    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Additional metrics
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None
    
    # Performance level
    performance_level: Optional[PerformanceLevel] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'metric_id': str(self.metric_id),
            'metric_name': self.metric_name,
            'category': self.category.value,
            'value': self.value,
            'unit': self.unit,
            'browser_id': self.browser_id,
            'page_url': self.page_url,
            'operation_type': self.operation_type,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat(),
            'min_value': self.min_value,
            'max_value': self.max_value,
            'avg_value': self.avg_value,
            'performance_level': self.performance_level.value if self.performance_level else None
        }


@dataclass
class PerformanceBottleneck:
    """Identified performance bottleneck"""
    bottleneck_id: UUID = field(default_factory=uuid4)
    category: MetricCategory = MetricCategory.RESPONSE_TIME
    severity: str = "medium"  # low, medium, high, critical
    
    # Bottleneck details
    metric_name: str = ""
    current_value: float = 0.0
    threshold_value: float = 0.0
    deviation_percent: float = 0.0
    
    # Context
    affected_browsers: List[str] = field(default_factory=list)
    affected_pages: List[str] = field(default_factory=list)
    
    # Analysis
    root_cause_analysis: str = ""
    impact_description: str = ""
    recommended_actions: List[str] = field(default_factory=list)
    
    # Metadata
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    first_detected: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    occurrence_count: int = 1
    last_occurrence: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'bottleneck_id': str(self.bottleneck_id),
            'category': self.category.value,
            'severity': self.severity,
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'deviation_percent': self.deviation_percent,
            'affected_browsers': self.affected_browsers,
            'affected_pages': self.affected_pages,
            'root_cause_analysis': self.root_cause_analysis,
            'impact_description': self.impact_description,
            'recommended_actions': self.recommended_actions,
            'detected_at': self.detected_at.isoformat(),
            'first_detected': self.first_detected.isoformat(),
            'occurrence_count': self.occurrence_count,
            'last_occurrence': self.last_occurrence.isoformat()
        }


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""
    recommendation_id: UUID = field(default_factory=uuid4)
    optimization_type: OptimizationType = OptimizationType.MEMORY_OPTIMIZATION
    
    # Recommendation details
    title: str = ""
    description: str = ""
    priority: str = "medium"  # low, medium, high, critical
    
    # Impact analysis
    expected_improvement: str = ""  # e.g., "20-30% faster page loads"
    effort_level: str = "medium"  # low, medium, high
    risk_level: str = "low"  # low, medium, high
    
    # Implementation details
    steps: List[str] = field(default_factory=list)
    configuration_changes: Dict[str, Any] = field(default_factory=dict)
    code_changes: List[str] = field(default_factory=list)
    
    # Context
    affected_metrics: List[str] = field(default_factory=list)
    target_browsers: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    applicable_conditions: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'recommendation_id': str(self.recommendation_id),
            'optimization_type': self.optimization_type.value,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'expected_improvement': self.expected_improvement,
            'effort_level': self.effort_level,
            'risk_level': self.risk_level,
            'steps': self.steps,
            'configuration_changes': self.configuration_changes,
            'code_changes': self.code_changes,
            'affected_metrics': self.affected_metrics,
            'target_browsers': self.target_browsers,
            'created_at': self.created_at.isoformat(),
            'applicable_conditions': self.applicable_conditions
        }


@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    report_id: UUID = field(default_factory=uuid4)
    report_period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    report_period_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Summary statistics
    total_measurements: int = 0
    unique_browsers: int = 0
    unique_pages: int = 0
    measurement_duration_minutes: int = 0
    
    # Performance metrics summary
    metrics_summary: Dict[str, Dict[str, float]] = field(default_factory=dict)
    bottleneck_summary: List[Dict[str, Any]] = field(default_factory=list)
    recommendations_summary: List[Dict[str, Any]] = field(default_factory=list)
    
    # Trends and analysis
    performance_trends: Dict[str, List[Tuple[datetime, float]]] = field(default_factory=dict)
    regression_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Alert summary
    performance_alerts: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'report_id': str(self.report_id),
            'report_period': {
                'start': self.report_period_start.isoformat(),
                'end': self.report_period_end.isoformat(),
                'duration_minutes': self.measurement_duration_minutes
            },
            'summary': {
                'total_measurements': self.total_measurements,
                'unique_browsers': self.unique_browsers,
                'unique_pages': self.unique_pages
            },
            'metrics_summary': self.metrics_summary,
            'bottleneck_summary': self.bottleneck_summary,
            'recommendations_summary': self.recommendations_summary,
            'performance_trends': {
                k: [(t.isoformat(), v) for t, v in v_list]
                for k, v_list in self.performance_trends.items()
            },
            'regression_analysis': self.regression_analysis,
            'performance_alerts': self.performance_alerts
        }


@dataclass
class PerformanceMonitoringConfig:
    """Configuration for performance monitoring"""
    # Monitoring intervals
    collection_interval_seconds: float = 10.0
    analysis_interval_seconds: float = 60.0
    report_generation_interval_minutes: int = 60
    cleanup_interval_minutes: int = 120
    
    # Data retention
    metric_retention_hours: int = 168  # 1 week
    history_retention_days: int = 30
    
    # Thresholds for performance detection
    response_time_threshold_ms: float = 2000.0
    memory_threshold_mb: float = 500.0
    cpu_threshold_percent: float = 80.0
    error_rate_threshold: float = 0.05  # 5%
    
    # Analysis settings
    baseline_window_hours: int = 24
    regression_detection_enabled: bool = True
    automated_optimization_enabled: bool = True
    
    # Alert settings
    performance_alert_enabled: bool = True
    performance_alert_threshold: str = "poor"  # poor or critical
    alert_cooldown_minutes: int = 15
    
    # Optimization settings
    max_recommendations: int = 20
    recommendation_confidence_threshold: float = 0.7
    
    # Performance measurement
    enable_real_time_monitoring: bool = True
    enable_historical_analysis: bool = True
    enable_predictive_analysis: bool = False  # Future enhancement


class PerformanceCollector:
    """Collect performance metrics from browser instances"""
    
    def __init__(self, config: PerformanceMonitoringConfig):
        self.config = config
        self.thresholds = self._initialize_thresholds()
        
        # Browser performance data
        self.browser_performance_data: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        # Page performance data
        self.page_performance_data: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=500)
        )
    
    def _initialize_thresholds(self) -> Dict[str, PerformanceThreshold]:
        """Initialize performance thresholds"""
        return {
            'page_load_time': PerformanceThreshold(
                metric_name='page_load_time',
                category=MetricCategory.RESPONSE_TIME,
                excellent_threshold=1000.0,  # 1 second
                good_threshold=3000.0,      # 3 seconds
                fair_threshold=5000.0,      # 5 seconds
                poor_threshold=10000.0,     # 10 seconds
                critical_threshold=15000.0, # 15 seconds
                unit='milliseconds',
                lower_is_better=True
            ),
            'memory_usage': PerformanceThreshold(
                metric_name='memory_usage',
                category=MetricCategory.RESOURCE_USAGE,
                excellent_threshold=100.0,  # 100MB
                good_threshold=250.0,       # 250MB
                fair_threshold=400.0,       # 400MB
                poor_threshold=600.0,       # 600MB
                critical_threshold=800.0,   # 800MB
                unit='MB',
                lower_is_better=True
            ),
            'cpu_usage': PerformanceThreshold(
                metric_name='cpu_usage',
                category=MetricCategory.RESOURCE_USAGE,
                excellent_threshold=20.0,   # 20%
                good_threshold=40.0,        # 40%
                fair_threshold=60.0,        # 60%
                poor_threshold=80.0,        # 80%
                critical_threshold=90.0,    # 90%
                unit='percent',
                lower_is_better=True
            ),
            'error_rate': PerformanceThreshold(
                metric_name='error_rate',
                category=MetricCategory.ERROR_RATE,
                excellent_threshold=0.01,   # 1%
                good_threshold=0.02,        # 2%
                fair_threshold=0.05,        # 5%
                poor_threshold=0.10,        # 10%
                critical_threshold=0.20,    # 20%
                unit='ratio',
                lower_is_better=True
            )
        }
    
    async def collect_browser_performance(self, browser_id: str, driver) -> List[PerformanceMetric]:
        """Collect performance metrics from browser"""
        metrics = []
        
        try:
            # Memory usage
            memory_metrics = await self._collect_memory_metrics(browser_id, driver)
            metrics.extend(memory_metrics)
            
            # CPU usage (estimated from performance metrics)
            cpu_metrics = await self._collect_cpu_metrics(browser_id, driver)
            metrics.extend(cpu_metrics)
            
            # Page performance
            page_metrics = await self._collect_page_metrics(browser_id, driver)
            metrics.extend(page_metrics)
            
            # Network metrics
            network_metrics = await self._collect_network_metrics(browser_id, driver)
            metrics.extend(network_metrics)
            
        except Exception as e:
            logger.error(f"Performance collection failed for browser {browser_id}: {e}")
        
        return metrics
    
    async def _collect_memory_metrics(self, browser_id: str, driver) -> List[PerformanceMetric]:
        """Collect memory performance metrics"""
        metrics = []
        
        try:
            if SELENIUM_AVAILABLE:
                # Get memory usage from browser
                memory_script = """
                return {
                    usedJSHeapSize: performance.memory ? performance.memory.usedJSHeapSize : 0,
                    totalJSHeapSize: performance.memory ? performance.memory.totalJSHeapSize : 0,
                    jsHeapSizeLimit: performance.memory ? performance.memory.jsHeapSizeLimit : 0
                };
                """
                
                memory_data = driver.execute_script(memory_script)
                
                if memory_data and memory_data.get('usedJSHeapSize'):
                    used_mb = memory_data['usedJSHeapSize'] / (1024 * 1024)
                    total_mb = memory_data['totalJSHeapSize'] / (1024 * 1024)
                    
                    metric = PerformanceMetric(
                        metric_name='memory_usage',
                        category=MetricCategory.MEMORY,
                        value=used_mb,
                        unit='MB',
                        browser_id=browser_id,
                        page_url=driver.current_url,
                        operation_type='monitoring'
                    )
                    
                    # Evaluate performance level
                    threshold = self.thresholds.get('memory_usage')
                    if threshold:
                        metric.performance_level = threshold.evaluate_performance(used_mb)
                    
                    metrics.append(metric)
                    
                    # Store in data structure
                    self.browser_performance_data[f"{browser_id}_memory"].append(metric)
            
        except Exception as e:
            logger.debug(f"Memory metrics collection failed: {e}")
        
        return metrics
    
    async def _collect_cpu_metrics(self, browser_id: str, driver) -> List[PerformanceMetric]:
        """Collect CPU performance metrics"""
        metrics = []
        
        try:
            # Estimate CPU usage from page performance timing
            if SELENIUM_AVAILABLE:
                cpu_script = """
                var timing = performance.timing;
                var loadTime = timing.loadEventEnd - timing.navigationStart;
                var domTime = timing.domContentLoadedEventEnd - timing.responseEnd;
                var cpuEstimate = Math.min(95, Math.max(5, (loadTime + domTime) / 50));
                return cpuEstimate;
                """
                
                cpu_estimate = driver.execute_script(cpu_script)
                
                if cpu_estimate:
                    metric = PerformanceMetric(
                        metric_name='cpu_usage',
                        category=MetricCategory.CPU,
                        value=cpu_estimate,
                        unit='percent',
                        browser_id=browser_id,
                        page_url=driver.current_url,
                        operation_type='monitoring'
                    )
                    
                    # Evaluate performance level
                    threshold = self.thresholds.get('cpu_usage')
                    if threshold:
                        metric.performance_level = threshold.evaluate_performance(cpu_estimate)
                    
                    metrics.append(metric)
                    
                    # Store in data structure
                    self.browser_performance_data[f"{browser_id}_cpu"].append(metric)
            
        except Exception as e:
            logger.debug(f"CPU metrics collection failed: {e}")
        
        return metrics
    
    async def _collect_page_metrics(self, browser_id: str, driver) -> List[PerformanceMetric]:
        """Collect page performance metrics"""
        metrics = []
        
        try:
            if SELENIUM_AVAILABLE:
                # Get page load timing
                timing_script = """
                var timing = performance.timing;
                return {
                    navigationStart: timing.navigationStart,
                    loadEventEnd: timing.loadEventEnd,
                    domContentLoaded: timing.domContentLoadedEventEnd,
                    responseEnd: timing.responseEnd,
                    domInteractive: timing.domInteractive
                };
                """
                
                timing_data = driver.execute_script(timing_script)
                
                if timing_data:
                    load_time = timing_data['loadEventEnd'] - timing_data['navigationStart']
                    dom_time = timing_data['domContentLoaded'] - timing_data['responseEnd']
                    tti = timing_data['domInteractive'] - timing_data['navigationStart']
                    
                    # Page load time metric
                    load_metric = PerformanceMetric(
                        metric_name='page_load_time',
                        category=MetricCategory.RESPONSE_TIME,
                        value=load_time,
                        unit='milliseconds',
                        browser_id=browser_id,
                        page_url=driver.current_url,
                        operation_type='page_load'
                    )
                    
                    # Time to interactive metric
                    tti_metric = PerformanceMetric(
                        metric_name='time_to_interactive',
                        category=MetricCategory.RESPONSE_TIME,
                        value=tti,
                        unit='milliseconds',
                        browser_id=browser_id,
                        page_url=driver.current_url,
                        operation_type='page_load'
                    )
                    
                    # Evaluate performance levels
                    threshold = self.thresholds.get('page_load_time')
                    if threshold:
                        load_metric.performance_level = threshold.evaluate_performance(load_time)
                        tti_metric.performance_level = threshold.evaluate_performance(tti)
                    
                    metrics.extend([load_metric, tti_metric])
                    
                    # Store in page data
                    page_key = f"{browser_id}_{driver.current_url}"
                    self.page_performance_data[f"{page_key}_load"].extend(metrics)
            
        except Exception as e:
            logger.debug(f"Page metrics collection failed: {e}")
        
        return metrics
    
    async def _collect_network_metrics(self, browser_id: str, driver) -> List[PerformanceMetric]:
        """Collect network performance metrics"""
        metrics = []
        
        try:
            if SELENIUM_AVAILABLE:
                # Get network timing
                network_script = """
                return performance.getEntriesByType('navigation')[0] || performance.timing;
                """
                
                network_data = driver.execute_script(network_script)
                
                if network_data:
                    # Response time (time to first byte)
                    response_time = network_data.responseStart - network_data.requestStart
                    
                    # Resource load time
                    resource_time = network_data.responseEnd - network_data.requestStart
                    
                    metric = PerformanceMetric(
                        metric_name='network_response_time',
                        category=MetricCategory.NETWORK,
                        value=response_time,
                        unit='milliseconds',
                        browser_id=browser_id,
                        page_url=driver.current_url,
                        operation_type='network'
                    )
                    
                    metrics.append(metric)
                    
                    # Store in browser data
                    self.browser_performance_data[f"{browser_id}_network"].append(metric)
            
        except Exception as e:
            logger.debug(f"Network metrics collection failed: {e}")
        
        return metrics
    
    def get_metric_statistics(self, metric_name: str, hours: int = 1) -> Dict[str, float]:
        """Get statistics for a metric"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Collect all values for the metric
        values = []
        
        for data_deque in self.browser_performance_data.values():
            for metric in data_deque:
                if (metric.metric_name == metric_name and 
                    metric.timestamp > cutoff_time):
                    values.append(metric.value)
        
        for data_deque in self.page_performance_data.values():
            for metric in data_deque:
                if (metric.metric_name == metric_name and 
                    metric.timestamp > cutoff_time):
                    values.append(metric.value)
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0,
            'p95': self._percentile(values, 95),
            'p99': self._percentile(values, 99)
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (index - int(index)) * (upper - lower)


class BottleneckDetector:
    """Detect performance bottlenecks"""
    
    def __init__(self, config: PerformanceMonitoringConfig):
        self.config = config
        self.detected_bottlenecks: Dict[str, PerformanceBottleneck] = {}
    
    def analyze_bottlenecks(self, collector: PerformanceCollector) -> List[PerformanceBottleneck]:
        """Analyze and detect performance bottlenecks"""
        bottlenecks = []
        
        try:
            # Analyze different metric categories
            bottlenecks.extend(self._analyze_response_time_bottlenecks(collector))
            bottlenecks.extend(self._analyze_resource_usage_bottlenecks(collector))
            bottlenecks.extend(self._analyze_error_rate_bottlenecks(collector))
            
            # Update detected bottlenecks
            self._update_bottleneck_database(bottlenecks)
            
        except Exception as e:
            logger.error(f"Bottleneck analysis failed: {e}")
        
        return bottlenecks
    
    def _analyze_response_time_bottlenecks(self, collector: PerformanceCollector) -> List[PerformanceBottleneck]:
        """Analyze response time bottlenecks"""
        bottlenecks = []
        
        try:
            # Check page load times
            stats = collector.get_metric_statistics('page_load_time', hours=1)
            if stats:
                avg_load_time = stats['mean']
                threshold = self.config.response_time_threshold_ms
                
                if avg_load_time > threshold:
                    bottleneck = PerformanceBottleneck(
                        category=MetricCategory.RESPONSE_TIME,
                        severity='high' if avg_load_time > threshold * 1.5 else 'medium',
                        metric_name='page_load_time',
                        current_value=avg_load_time,
                        threshold_value=threshold,
                        deviation_percent=((avg_load_time - threshold) / threshold) * 100,
                        root_cause_analysis="High page load times detected across multiple pages",
                        impact_description="Slow page loading affects user experience and system throughput",
                        recommended_actions=[
                            "Optimize page content and images",
                            "Enable browser caching",
                            "Minimize JavaScript and CSS files",
                            "Use Content Delivery Network (CDN)"
                        ]
                    )
                    bottlenecks.append(bottleneck)
            
            # Check time to interactive
            stats = collector.get_metric_statistics('time_to_interactive', hours=1)
            if stats:
                avg_tti = stats['mean']
                if avg_tti > threshold:
                    bottleneck = PerformanceBottleneck(
                        category=MetricCategory.RESPONSE_TIME,
                        severity='medium',
                        metric_name='time_to_interactive',
                        current_value=avg_tti,
                        threshold_value=threshold,
                        deviation_percent=((avg_tti - threshold) / threshold) * 100,
                        root_cause_analysis="Pages taking too long to become interactive",
                        impact_description="Users cannot interact with pages quickly",
                        recommended_actions=[
                            "Optimize JavaScript execution",
                            "Reduce DOM complexity",
                            "Use web workers for heavy computations"
                        ]
                    )
                    bottlenecks.append(bottleneck)
            
        except Exception as e:
            logger.debug(f"Response time bottleneck analysis failed: {e}")
        
        return bottlenecks
    
    def _analyze_resource_usage_bottlenecks(self, collector: PerformanceCollector) -> List[PerformanceBottleneck]:
        """Analyze resource usage bottlenecks"""
        bottlenecks = []
        
        try:
            # Check memory usage
            stats = collector.get_metric_statistics('memory_usage', hours=1)
            if stats:
                avg_memory = stats['mean']
                threshold = self.config.memory_threshold_mb
                
                if avg_memory > threshold:
                    bottleneck = PerformanceBottleneck(
                        category=MetricCategory.RESOURCE_USAGE,
                        severity='high' if avg_memory > threshold * 1.5 else 'medium',
                        metric_name='memory_usage',
                        current_value=avg_memory,
                        threshold_value=threshold,
                        deviation_percent=((avg_memory - threshold) / threshold) * 100,
                        root_cause_analysis="High memory usage detected",
                        impact_description="Memory pressure may cause browser crashes or slowdowns",
                        recommended_actions=[
                            "Close unnecessary browser tabs",
                            "Clear browser cache and cookies",
                            "Restart browser instances periodically",
                            "Optimize JavaScript memory usage"
                        ]
                    )
                    bottlenecks.append(bottleneck)
            
            # Check CPU usage
            stats = collector.get_metric_statistics('cpu_usage', hours=1)
            if stats:
                avg_cpu = stats['mean']
                threshold = self.config.cpu_threshold_percent
                
                if avg_cpu > threshold:
                    bottleneck = PerformanceBottleneck(
                        category=MetricCategory.RESOURCE_USAGE,
                        severity='medium' if avg_cpu > threshold * 1.2 else 'low',
                        metric_name='cpu_usage',
                        current_value=avg_cpu,
                        threshold_value=threshold,
                        deviation_percent=((avg_cpu - threshold) / threshold) * 100,
                        root_cause_analysis="High CPU usage detected",
                        impact_description="CPU intensive operations slowing down browser performance",
                        recommended_actions=[
                            "Optimize JavaScript algorithms",
                            "Reduce polling frequency",
                            "Use requestAnimationFrame for animations",
                            "Implement throttling for frequent operations"
                        ]
                    )
                    bottlenecks.append(bottleneck)
            
        except Exception as e:
            logger.debug(f"Resource usage bottleneck analysis failed: {e}")
        
        return bottlenecks
    
    def _analyze_error_rate_bottlenecks(self, collector: PerformanceCollector) -> List[PerformanceBottleneck]:
        """Analyze error rate bottlenecks"""
        bottlenecks = []
        
        try:
            # Calculate error rates for each browser
            for browser_key in collector.browser_performance_data:
                if 'memory' in browser_key or 'cpu' in browser_key:
                    continue  # Skip resource metrics for error rate analysis
                
                # This is a simplified error rate calculation
                # In a real implementation, you would track actual error metrics
                browser_id = browser_key.split('_')[0]
                
                # Estimate error rate based on failed operations
                error_rate = self._estimate_error_rate(browser_key, collector)
                
                if error_rate > self.config.error_rate_threshold:
                    bottleneck = PerformanceBottleneck(
                        category=MetricCategory.ERROR_RATE,
                        severity='high' if error_rate > self.config.error_rate_threshold * 2 else 'medium',
                        metric_name='error_rate',
                        current_value=error_rate,
                        threshold_value=self.config.error_rate_threshold,
                        deviation_percent=((error_rate - self.config.error_rate_threshold) / self.config.error_rate_threshold) * 100,
                        affected_browsers=[browser_id],
                        root_cause_analysis="High error rate detected",
                        impact_description="Frequent errors indicate stability issues",
                        recommended_actions=[
                            "Review browser console errors",
                            "Implement proper error handling",
                            "Add retry logic for failed operations",
                            "Monitor and log all exceptions"
                        ]
                    )
                    bottlenecks.append(bottleneck)
            
        except Exception as e:
            logger.debug(f"Error rate bottleneck analysis failed: {e}")
        
        return bottlenecks
    
    def _estimate_error_rate(self, browser_key: str, collector: PerformanceCollector) -> float:
        """Estimate error rate for a browser"""
        # This is a simplified implementation
        # In practice, you would track actual error metrics
        data_deque = collector.browser_performance_data.get(browser_key, deque())
        
        if not data_deque:
            return 0.0
        
        # Estimate based on performance levels (assuming poor performance correlates with errors)
        poor_metrics = sum(1 for m in data_deque if m.performance_level == PerformanceLevel.POOR)
        total_metrics = len(data_deque)
        
        return poor_metrics / total_metrics if total_metrics > 0 else 0.0
    
    def _update_bottleneck_database(self, new_bottlenecks: List[PerformanceBottleneck]):
        """Update bottleneck database with new findings"""
        for bottleneck in new_bottlenecks:
            key = f"{bottleneck.category.value}_{bottleneck.metric_name}"
            
            if key in self.detected_bottlenecks:
                # Update existing bottleneck
                existing = self.detected_bottlenecks[key]
                existing.occurrence_count += 1
                existing.last_occurrence = datetime.now(timezone.utc)
                existing.current_value = bottleneck.current_value
                existing.deviation_percent = bottleneck.deviation_percent
                
                # Escalate severity if it gets worse
                severity_levels = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
                if (severity_levels.get(bottleneck.severity, 0) > 
                    severity_levels.get(existing.severity, 0)):
                    existing.severity = bottleneck.severity
            else:
                # Add new bottleneck
                self.detected_bottlenecks[key] = bottleneck


class OptimizationEngine:
    """Generate performance optimization recommendations"""
    
    def __init__(self, config: PerformanceMonitoringConfig):
        self.config = config
        self.recommendations: List[OptimizationRecommendation] = []
    
    def generate_recommendations(self, bottlenecks: List[PerformanceBottleneck],
                               collector: PerformanceCollector) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on bottlenecks"""
        recommendations = []
        
        try:
            for bottleneck in bottlenecks:
                recommendations.extend(self._generate_bottleneck_recommendations(bottleneck))
            
            # Generate general optimization recommendations
            recommendations.extend(self._generate_general_recommendations(collector))
            
            # Remove duplicates and rank by priority
            recommendations = self._deduplicate_and_rank_recommendations(recommendations)
            
            # Update recommendations database
            self.recommendations.extend(recommendations)
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
        
        return recommendations
    
    def _generate_bottleneck_recommendations(self, bottleneck: PerformanceBottleneck) -> List[OptimizationRecommendation]:
        """Generate recommendations for a specific bottleneck"""
        recommendations = []
        
        if bottleneck.category == MetricCategory.RESPONSE_TIME:
            if bottleneck.metric_name == 'page_load_time':
                recommendations.append(OptimizationRecommendation(
                    optimization_type=OptimizationType.PAGE_OPTIMIZATION,
                    title="Optimize Page Load Performance",
                    description="Implement comprehensive page load optimization",
                    priority='high',
                    expected_improvement="30-50% faster page loads",
                    effort_level='medium',
                    risk_level='low',
                    steps=[
                        "Compress and optimize images",
                        "Minify CSS and JavaScript files",
                        "Enable browser caching",
                        "Use Content Delivery Network (CDN)",
                        "Optimize critical rendering path"
                    ],
                    affected_metrics=['page_load_time', 'time_to_interactive']
                ))
                
                recommendations.append(OptimizationRecommendation(
                    optimization_type=OptimizationType.CACHING_OPTIMIZATION,
                    title="Implement Advanced Caching Strategy",
                    description="Optimize browser and server-side caching",
                    priority='medium',
                    expected_improvement="20-40% faster repeat page loads",
                    effort_level='low',
                    risk_level='low',
                    steps=[
                        "Set appropriate cache headers",
                        "Implement service workers for offline caching",
                        "Use ETags for efficient cache validation",
                        "Configure browser cache duration"
                    ],
                    affected_metrics=['page_load_time']
                ))
            
            elif bottleneck.metric_name == 'time_to_interactive':
                recommendations.append(OptimizationRecommendation(
                    optimization_type=OptimizationType.SCRIPT_OPTIMIZATION,
                    title="Optimize JavaScript Execution",
                    description="Improve JavaScript performance for faster interactivity",
                    priority='high',
                    expected_improvement="25-35% faster time to interactive",
                    effort_level='medium',
                    risk_level='medium',
                    steps=[
                        "Use requestAnimationFrame for animations",
                        "Implement debouncing for frequent events",
                        "Optimize DOM queries and manipulations",
                        "Use Web Workers for heavy computations",
                        "Minimize synchronous JavaScript"
                    ],
                    affected_metrics=['time_to_interactive', 'cpu_usage']
                ))
        
        elif bottleneck.category == MetricCategory.RESOURCE_USAGE:
            if bottleneck.metric_name == 'memory_usage':
                recommendations.append(OptimizationRecommendation(
                    optimization_type=OptimizationType.MEMORY_OPTIMIZATION,
                    title="Optimize Memory Usage",
                    description="Reduce browser memory consumption",
                    priority='high',
                    expected_improvement="20-30% memory reduction",
                    effort_level='medium',
                    risk_level='low',
                    steps=[
                        "Close unnecessary browser tabs",
                        "Clear browser cache periodically",
                        "Implement memory cleanup in JavaScript",
                        "Use WeakMap for temporary data structures",
                        "Monitor and fix memory leaks"
                    ],
                    affected_metrics=['memory_usage']
                ))
                
                recommendations.append(OptimizationRecommendation(
                    optimization_type=OptimizationType.RESOURCE_OPTIMIZATION,
                    title="Implement Resource Management",
                    description="Optimize resource utilization",
                    priority='medium',
                    expected_improvement="15-25% better resource efficiency",
                    effort_level='medium',
                    risk_level='low',
                    steps=[
                        "Implement lazy loading for images",
                        "Use resource pooling for frequently created objects",
                        "Optimize data structures and algorithms",
                        "Implement garbage collection best practices"
                    ],
                    affected_metrics=['memory_usage', 'cpu_usage']
                ))
            
            elif bottleneck.metric_name == 'cpu_usage':
                recommendations.append(OptimizationRecommendation(
                    optimization_type=OptimizationType.CPU_OPTIMIZATION,
                    title="Reduce CPU Usage",
                    description="Optimize CPU-intensive operations",
                    priority='medium',
                    expected_improvement="25-40% CPU usage reduction",
                    effort_level='high',
                    risk_level='medium',
                    steps=[
                        "Implement throttling for frequent operations",
                        "Use batch processing for multiple operations",
                        "Optimize algorithms and data structures",
                        "Use hardware acceleration when available",
                        "Implement proper event handling"
                    ],
                    affected_metrics=['cpu_usage', 'response_time']
                ))
        
        elif bottleneck.category == MetricCategory.ERROR_RATE:
            recommendations.append(OptimizationRecommendation(
                optimization_type=OptimizationType.SCRIPT_OPTIMIZATION,
                title="Improve Error Handling",
                description="Implement comprehensive error handling and monitoring",
                priority='high',
                expected_improvement="50-80% error reduction",
                effort_level='medium',
                risk_level='low',
                steps=[
                    "Implement try-catch blocks for critical operations",
                    "Add comprehensive logging and monitoring",
                    "Implement retry logic for failed operations",
                    "Add input validation and sanitization",
                    "Monitor JavaScript console errors"
                ],
                affected_metrics=['error_rate', 'stability']
            ))
        
        return recommendations
    
    def _generate_general_recommendations(self, collector: PerformanceCollector) -> List[OptimizationRecommendation]:
        """Generate general optimization recommendations"""
        recommendations = []
        
        # Performance monitoring optimization
        recommendations.append(OptimizationRecommendation(
            optimization_type=OptimizationType.RESOURCE_OPTIMIZATION,
            title="Implement Performance Monitoring",
            description="Add comprehensive performance monitoring and alerting",
            priority='medium',
            expected_improvement="Better performance visibility and faster issue detection",
            effort_level='low',
            risk_level='low',
            steps=[
                "Set up real-time performance monitoring",
                "Configure performance alerts",
                "Implement performance regression testing",
                "Create performance dashboards"
            ],
            affected_metrics=['all']
        ))
        
        # Browser optimization
        recommendations.append(OptimizationRecommendation(
            optimization_type=OptimizationType.MEMORY_OPTIMIZATION,
            title="Browser Instance Management",
            description="Optimize browser instance lifecycle management",
            priority='medium',
            expected_improvement="15-20% better resource utilization",
            effort_level='low',
            risk_level='low',
            steps=[
                "Implement browser instance pooling",
                "Set up automatic browser restarts",
                "Monitor browser health and performance",
                "Implement graceful browser shutdown"
            ],
            affected_metrics=['memory_usage', 'cpu_usage', 'stability']
        ))
        
        return recommendations
    
    def _deduplicate_and_rank_recommendations(self, recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
        """Remove duplicate recommendations and rank by priority"""
        # Remove duplicates based on title
        seen_titles = set()
        unique_recommendations = []
        
        for rec in recommendations:
            if rec.title not in seen_titles:
                seen_titles.add(rec.title)
                unique_recommendations.append(rec)
        
        # Rank by priority
        priority_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        
        unique_recommendations.sort(
            key=lambda r: priority_order.get(r.priority, 0),
            reverse=True
        )
        
        # Limit to max recommendations
        return unique_recommendations[:self.config.max_recommendations]


class PerformanceAnalyzer:
    """Main performance analysis system"""
    
    def __init__(self, config: Optional[PerformanceMonitoringConfig] = None):
        self.config = config or PerformanceMonitoringConfig()
        self.audit_logger = get_audit_logger()
        
        # Core components
        self.collector = PerformanceCollector(self.config)
        self.bottleneck_detector = BottleneckDetector(self.config)
        self.optimization_engine = OptimizationEngine(self.config)
        
        # Performance history
        self.performance_history: deque = deque(maxlen=1000)
        self.reports: List[PerformanceReport] = []
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Browser tracking
        self.tracked_browsers: Set[str] = set()
        self.browser_drivers: Dict[str, Any] = {}
        
        # Statistics
        self.collection_stats = {
            'metrics_collected': 0,
            'bottlenecks_detected': 0,
            'recommendations_generated': 0,
            'reports_generated': 0,
            'errors_encountered': 0
        }
        
        # Risk monitoring integration
        self.risk_monitoring = None
        try:
            self.risk_monitoring = get_monitoring_system()
        except Exception as e:
            logger.warning(f"Risk monitoring integration unavailable: {e}")
        
        logger.info("Performance analyzer initialized")
    
    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self.monitoring_active = True
        self._shutdown_event.clear()
        
        # Create monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._collection_loop()),
            asyncio.create_task(self._analysis_loop()),
            asyncio.create_task(self._reporting_loop())
        ]
        
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
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
        
        logger.info("Performance monitoring stopped")
    
    def track_browser(self, browser_id: str, driver):
        """Add browser to performance tracking"""
        self.tracked_browsers.add(browser_id)
        self.browser_drivers[browser_id] = driver
        
        logger.info(f"Added browser {browser_id} to performance tracking")
    
    def untrack_browser(self, browser_id: str):
        """Remove browser from performance tracking"""
        self.tracked_browsers.discard(browser_id)
        self.browser_drivers.pop(browser_id, None)
        
        logger.info(f"Removed browser {browser_id} from performance tracking")
    
    async def _collection_loop(self):
        """Performance metrics collection loop"""
        while self.monitoring_active:
            try:
                await self._collect_performance_metrics()
                await asyncio.sleep(self.config.collection_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance collection loop: {e}", exc_info=True)
                self.collection_stats['errors_encountered'] += 1
                await asyncio.sleep(5)
    
    async def _collect_performance_metrics(self):
        """Collect performance metrics from all tracked browsers"""
        collection_tasks = []
        
        for browser_id in self.tracked_browsers:
            driver = self.browser_drivers.get(browser_id)
            if driver:
                task = self.collector.collect_browser_performance(browser_id, driver)
                collection_tasks.append(task)
        
        if collection_tasks:
            results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            # Process results
            total_metrics = 0
            for result in results:
                if isinstance(result, list):
                    total_metrics += len(result)
                    
                    # Log metrics to risk monitoring system
                    if self.risk_monitoring:
                        for metric in result:
                            await self._log_to_risk_system(metric)
                elif isinstance(result, Exception):
                    logger.warning(f"Performance collection failed: {result}")
            
            self.collection_stats['metrics_collected'] += total_metrics
    
    async def _log_to_risk_system(self, metric: PerformanceMetric):
        """Log performance metric to risk monitoring system"""
        try:
            risk_metric = PerformanceMetric(
                metric_name=f"browser.performance.{metric.metric_name}",
                metric_type=MetricType.GAUGE,
                value=metric.value,
                unit=metric.unit,
                tags={
                    'browser_id': metric.browser_id or 'unknown',
                    'page_url': metric.page_url,
                    'operation_type': metric.operation_type,
                    'performance_level': metric.performance_level.value if metric.performance_level else 'unknown'
                }
            )
            
            self.risk_monitoring.performance_tracker.record_metric(risk_metric)
            
        except Exception as e:
            logger.debug(f"Failed to log to risk system: {e}")
    
    async def _analysis_loop(self):
        """Performance analysis loop"""
        while self.monitoring_active:
            try:
                await self._analyze_performance()
                await asyncio.sleep(self.config.analysis_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance analysis loop: {e}", exc_info=True)
                self.collection_stats['errors_encountered'] += 1
                await asyncio.sleep(30)
    
    async def _analyze_performance(self):
        """Analyze performance data and detect issues"""
        try:
            # Detect bottlenecks
            bottlenecks = self.bottleneck_detector.analyze_bottlenecks(self.collector)
            self.collection_stats['bottlenecks_detected'] += len(bottlenecks)
            
            # Generate optimization recommendations
            recommendations = self.optimization_engine.generate_recommendations(
                bottlenecks, self.collector
            )
            self.collection_stats['recommendations_generated'] += len(recommendations)
            
            # Store analysis results
            analysis_result = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'bottlenecks_detected': len(bottlenecks),
                'recommendations_generated': len(recommendations),
                'bottlenecks': [b.to_dict() for b in bottlenecks],
                'recommendations': [r.to_dict() for r in recommendations]
            }
            
            self.performance_history.append(analysis_result)
            
            logger.debug(f"Performance analysis completed: {len(bottlenecks)} bottlenecks, "
                        f"{len(recommendations)} recommendations")
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
    
    async def _reporting_loop(self):
        """Performance reporting loop"""
        while self.monitoring_active:
            try:
                await self._generate_periodic_report()
                await asyncio.sleep(self.config.report_generation_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in reporting loop: {e}", exc_info=True)
                self.collection_stats['errors_encountered'] += 1
                await asyncio.sleep(300)  # 5 minutes
    
    async def _generate_periodic_report(self):
        """Generate periodic performance report"""
        try:
            report = await self.generate_performance_report()
            self.reports.append(report)
            self.collection_stats['reports_generated'] += 1
            
            logger.info(f"Generated performance report: {report.report_id}")
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
    
    async def generate_performance_report(self, hours: int = 1) -> PerformanceReport:
        """Generate comprehensive performance report"""
        current_time = datetime.now(timezone.utc)
        start_time = current_time - timedelta(hours=hours)
        
        # Get metrics summary
        metrics_summary = {}
        key_metrics = ['page_load_time', 'memory_usage', 'cpu_usage', 'time_to_interactive']
        
        for metric_name in key_metrics:
            stats = self.collector.get_metric_statistics(metric_name, hours)
            if stats:
                metrics_summary[metric_name] = stats
        
        # Get bottlenecks
        bottlenecks = []
        for bottleneck in self.bottleneck_detector.detected_bottlenecks.values():
            if bottleneck.last_occurrence > start_time:
                bottlenecks.append(bottleneck.to_dict())
        
        # Get recommendations
        recent_recommendations = [
            rec for rec in self.optimization_engine.recommendations
            if rec.created_at > start_time
        ]
        recommendations = [rec.to_dict() for rec in recent_recommendations]
        
        # Calculate trends
        performance_trends = {}
        for metric_name in key_metrics:
            trend_data = []
            
            # This is a simplified trend calculation
            # In practice, you would aggregate metrics over time windows
            stats = self.collector.get_metric_statistics(metric_name, hours)
            if stats and 'mean' in stats:
                trend_data.append((current_time, stats['mean']))
            
            performance_trends[metric_name] = trend_data
        
        # Create report
        report = PerformanceReport(
            report_period_start=start_time,
            report_period_end=current_time,
            measurement_duration_minutes=hours * 60,
            total_measurements=sum(
                len(data) for data in self.collector.browser_performance_data.values()
            ) + sum(
                len(data) for data in self.collector.page_performance_data.values()
            ),
            unique_browsers=len(self.tracked_browsers),
            metrics_summary=metrics_summary,
            bottleneck_summary=bottlenecks,
            recommendations_summary=recommendations,
            performance_trends=performance_trends
        )
        
        return report
    
    def get_current_performance(self) -> Dict[str, Any]:
        """Get current performance status"""
        current_time = datetime.now(timezone.utc)
        
        # Get latest metrics for each category
        latest_metrics = {}
        
        for browser_key, data_deque in self.collector.browser_performance_data.items():
            if data_deque:
                latest_metric = data_deque[-1]
                if latest_metric.metric_name not in latest_metrics:
                    latest_metrics[latest_metric.metric_name] = latest_metric
        
        return {
            'timestamp': current_time.isoformat(),
            'monitoring_active': self.monitoring_active,
            'tracked_browsers': len(self.tracked_browsers),
            'latest_metrics': {
                name: metric.to_dict() for name, metric in latest_metrics.items()
            },
            'statistics': self.collection_stats.copy(),
            'active_bottlenecks': len([
                b for b in self.bottleneck_detector.detected_bottlenecks.values()
                if (current_time - b.last_occurrence).total_seconds() < 3600  # Last hour
            ])
        }
    
    def get_performance_trends(self, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance trends for a specific metric"""
        stats = self.collector.get_metric_statistics(metric_name, hours)
        
        if not stats:
            return {'message': f'No data available for metric: {metric_name}'}
        
        return {
            'metric_name': metric_name,
            'time_period_hours': hours,
            'statistics': stats,
            'performance_level': self._evaluate_performance_level(metric_name, stats['mean'])
        }
    
    def _evaluate_performance_level(self, metric_name: str, value: float) -> str:
        """Evaluate performance level for a metric"""
        thresholds = self.collector.thresholds.get(metric_name)
        if thresholds:
            level = thresholds.evaluate_performance(value)
            return level.value
        return 'unknown'
    
    def get_bottlenecks(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get detected bottlenecks"""
        bottlenecks = list(self.bottleneck_detector.detected_bottlenecks.values())
        
        if severity:
            bottlenecks = [b for b in bottlenecks if b.severity == severity]
        
        return [b.to_dict() for b in bottlenecks]
    
    def get_recommendations(self, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get optimization recommendations"""
        recommendations = self.optimization_engine.recommendations
        
        if priority:
            recommendations = [r for r in recommendations if r.priority == priority]
        
        return [r.to_dict() for r in recommendations]
    
    def get_optimization_impact_analysis(self) -> Dict[str, Any]:
        """Get analysis of potential optimization impact"""
        recommendations = self.optimization_engine.recommendations
        
        # Group recommendations by type
        by_type = defaultdict(list)
        for rec in recommendations:
            by_type[rec.optimization_type.value].append(rec)
        
        # Calculate potential impact
        impact_analysis = {}
        total_effort = 0
        total_expected_improvement = 0
        
        for opt_type, recs in by_type.items():
            # Count recommendations by priority
            priority_counts = defaultdict(int)
            for rec in recs:
                priority_counts[rec.priority] += 1
            
            # Estimate impact (simplified)
            effort_score = 0
            for rec in recs:
                effort_mapping = {'low': 1, 'medium': 2, 'high': 3}
                effort_score += effort_mapping.get(rec.effort_level, 2)
            
            impact_analysis[opt_type] = {
                'recommendation_count': len(recs),
                'priority_distribution': dict(priority_counts),
                'estimated_effort': effort_score,
                'top_recommendations': [r.title for r in recs[:3]]
            }
            
            total_effort += effort_score
        
        return {
            'total_recommendations': len(recommendations),
            'optimization_types': len(by_type),
            'impact_by_type': impact_analysis,
            'overall_assessment': {
                'total_effort_estimate': total_effort,
                'high_priority_count': sum(1 for r in recommendations if r.priority == 'high'),
                'quick_wins': sum(1 for r in recommendations if r.effort_level == 'low' and r.priority in ['high', 'medium'])
            }
        }
    
    async def force_performance_analysis(self) -> Dict[str, Any]:
        """Force immediate performance analysis"""
        try:
            # Collect metrics
            await self._collect_performance_metrics()
            
            # Analyze
            await self._analyze_performance()
            
            # Generate report
            report = await self.generate_performance_report(hours=1)
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'analysis_completed': True,
                'bottlenecks_detected': len(self.bottleneck_detector.detected_bottlenecks),
                'recommendations_generated': len(self.optimization_engine.recommendations),
                'report_id': str(report.report_id)
            }
            
        except Exception as e:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'analysis_completed': False,
                'error': str(e)
            }
    
    async def shutdown(self):
        """Graceful shutdown of performance monitoring"""
        logger.info("Initiating performance monitoring shutdown")
        
        # Stop monitoring
        await self.stop_monitoring()
        
        # Clear tracked browsers
        self.tracked_browsers.clear()
        self.browser_drivers.clear()
        
        logger.info("Performance monitoring shutdown completed")


# Global performance analyzer instance
_global_performance_analyzer = None


def get_performance_analyzer() -> PerformanceAnalyzer:
    """Get or create global performance analyzer"""
    global _global_performance_analyzer
    if _global_performance_analyzer is None:
        _global_performance_analyzer = PerformanceAnalyzer()
    return _global_performance_analyzer


if __name__ == "__main__":
    # Example usage and testing
    async def test_performance_analyzer():
        # Setup
        config = PerformanceMonitoringConfig()
        analyzer = PerformanceAnalyzer(config)
        
        print("Starting performance monitoring system...")
        await analyzer.start_monitoring()
        
        # Simulate browser tracking (if Selenium available)
        if SELENIUM_AVAILABLE:
            print("Selenium available - would track real browser performance")
        else:
            print("Selenium not available - running in simulation mode")
        
        # Let it run for a bit
        await asyncio.sleep(5)
        
        print("Current performance status:", json.dumps(analyzer.get_current_performance(), indent=2))
        
        print("Bottlenecks:", json.dumps(analyzer.get_bottlenecks(), indent=2))
        print("Recommendations:", json.dumps(analyzer.get_recommendations(), indent=2))
        
        # Stop monitoring
        print("Stopping performance monitoring system...")
        await analyzer.shutdown()
        
        print("Performance monitoring system test completed!")
    
    # Run test
    asyncio.run(test_performance_analyzer())