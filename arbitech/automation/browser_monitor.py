"""
Comprehensive Browser State Monitoring System for ARBitech Trading Platform

This module provides enterprise-grade browser state monitoring with:
- Real-time browser instance tracking and health monitoring
- Performance metrics collection and analysis
- Risk assessment and alert integration
- Resource utilization monitoring
- Browser lifecycle management
- Comprehensive reporting and analytics

Features:
- Multi-browser instance monitoring
- Real-time state tracking
- Performance optimization
- Risk-based alerting
- Integration with Phase 4 risk management
- Dashboard-ready data export
"""

import asyncio
import time
import psutil
import threading
import weakref
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from uuid import UUID, uuid4
import json
from collections import deque, defaultdict
import statistics
import logging
import psutil
import importlib.util

from arbitech.risk.monitoring_system import (
    MonitoringSystem, HealthStatus, MetricType, AlertSeverity, 
    PerformanceMetric, get_monitoring_system as get_risk_monitoring_system
)
from arbitech.storage.audit_logger import get_audit_logger, log_performance_metric
from arbitech.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import Selenium for browser control
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.common.exceptions import WebDriverException, TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available - browser monitoring will be limited")


class BrowserState(Enum):
    """Browser state enumeration"""
    UNKNOWN = "unknown"
    LAUNCHING = "launching"
    RUNNING = "running"
    LOADING = "loading"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    CRASHED = "crashed"
    CLOSED = "closed"


class BrowserType(Enum):
    """Supported browser types"""
    CHROME = "chrome"
    FIREFOX = "firefox"
    SAFARI = "safari"
    EDGE = "edge"


class RiskLevel(Enum):
    """Risk levels for browser operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BrowserInstance:
    """Represents a browser instance"""
    instance_id: UUID = field(default_factory=uuid4)
    browser_type: BrowserType = BrowserType.CHROME
    driver: Optional[Any] = None
    
    # State tracking
    state: BrowserState = BrowserState.UNKNOWN
    current_url: str = ""
    page_title: str = ""
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Performance metrics
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    response_times: List[float] = field(default_factory=list)
    page_load_times: List[float] = field(default_factory=list)
    error_count: int = 0
    success_count: int = 0
    
    # Resource tracking
    open_tabs: int = 1
    network_requests: int = 0
    javascript_errors: int = 0
    cookies_count: int = 0
    
    # Risk assessment
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    last_risk_assessment: Optional[datetime] = None
    
    # Lifecycle
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    health_score: float = 1.0
    
    # Error tracking
    last_error: Optional[str] = None
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'instance_id': str(self.instance_id),
            'browser_type': self.browser_type.value,
            'state': self.state.value,
            'current_url': self.current_url,
            'page_title': self.page_title,
            'last_activity': self.last_activity.isoformat(),
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'response_times_avg': statistics.mean(self.response_times) if self.response_times else 0,
            'page_load_times_avg': statistics.mean(self.page_load_times) if self.page_load_times else 0,
            'error_count': self.error_count,
            'success_count': self.success_count,
            'open_tabs': self.open_tabs,
            'network_requests': self.network_requests,
            'javascript_errors': self.javascript_errors,
            'cookies_count': self.cookies_count,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level.value,
            'last_risk_assessment': self.last_risk_assessment.isoformat() if self.last_risk_assessment else None,
            'created_at': self.created_at.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'health_score': self.health_score,
            'last_error': self.last_error,
            'uptime_seconds': (datetime.now(timezone.utc) - self.created_at).total_seconds()
        }


@dataclass
class BrowserMonitoringConfig:
    """Configuration for browser monitoring"""
    # Monitoring intervals
    health_check_interval_seconds: float = 10.0
    performance_check_interval_seconds: float = 30.0
    risk_assessment_interval_seconds: float = 60.0
    cleanup_interval_seconds: float = 300.0  # 5 minutes
    
    # Browser lifecycle
    max_browser_instances: int = 50
    browser_timeout_seconds: float = 300.0  # 5 minutes
    session_timeout_seconds: float = 1800.0  # 30 minutes
    
    # Performance thresholds
    max_memory_usage_mb: float = 500.0
    max_cpu_usage_percent: float = 80.0
    max_response_time_seconds: float = 10.0
    max_page_load_time_seconds: float = 15.0
    max_error_rate: float = 0.05  # 5%
    
    # Risk thresholds
    risk_threshold_low: float = 0.3
    risk_threshold_medium: float = 0.6
    risk_threshold_high: float = 0.8
    risk_threshold_critical: float = 0.95
    
    # Resource limits
    max_concurrent_browsers: int = 20
    max_memory_total_mb: float = 4000.0
    max_cpu_total_percent: float = 500.0  # 5 cores at 100%
    
    # Alert settings
    enable_alerts: bool = True
    alert_cooldown_seconds: float = 300.0  # 5 minutes
    
    # Integration settings
    enable_risk_system_integration: bool = True
    enable_performance_optimization: bool = True


class BrowserHealthChecker:
    """Health checker for browser instances"""
    
    def __init__(self, browser_instance: BrowserInstance):
        self.browser = browser_instance
        self.failure_count = 0
        self.last_check = datetime.now(timezone.utc)
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform health check on browser instance"""
        start_time = time.time()
        check_result = {
            'instance_id': self.browser.instance_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'healthy': True,
            'checks_passed': 0,
            'checks_failed': 0,
            'issues': []
        }
        
        try:
            # Check if browser is running
            if not self._is_browser_alive():
                check_result['healthy'] = False
                check_result['issues'].append('Browser process not responding')
                check_result['checks_failed'] += 1
                return check_result
            
            check_result['checks_passed'] += 1
            
            # Check browser state
            if self.browser.state in [BrowserState.ERROR, BrowserState.CRASHED]:
                check_result['healthy'] = False
                check_result['issues'].append(f'Browser in error state: {self.browser.state.value}')
                check_result['checks_failed'] += 1
            
            check_result['checks_passed'] += 1
            
            # Check memory usage
            if self.browser.memory_usage > self._get_max_memory():
                check_result['issues'].append(f'High memory usage: {self.browser.memory_usage:.1f}MB')
                check_result['checks_failed'] += 1
            else:
                check_result['checks_passed'] += 1
            
            # Check CPU usage
            if self.browser.cpu_usage > self._get_max_cpu():
                check_result['issues'].append(f'High CPU usage: {self.browser.cpu_usage:.1f}%')
                check_result['checks_failed'] += 1
            else:
                check_result['checks_passed += 1
            
            # Check error rate
            total_operations = self.browser.error_count + self.browser.success_count
            if total_operations > 0:
                error_rate = self.browser.error_count / total_operations
                if error_rate > 0.05:  # 5% error rate
                    check_result['issues'].append(f'High error rate: {error_rate:.1%}')
                    check_result['checks_failed'] += 1
                else:
                    check_result['checks_passed'] += 1
            
            # Check last activity
            time_since_activity = (datetime.now(timezone.utc) - self.browser.last_activity).total_seconds()
            if time_since_activity > 300:  # 5 minutes
                check_result['issues'].append(f'No recent activity: {time_since_activity:.0f}s ago')
                check_result['checks_failed'] += 1
            else:
                check_result['checks_passed'] += 1
            
            check_result['total_checks'] = check_result['checks_passed'] + check_result['checks_failed']
            
            if not check_result['healthy']:
                self.failure_count += 1
            else:
                self.failure_count = 0
            
            self.last_check = datetime.now(timezone.utc)
            return check_result
            
        except Exception as e:
            check_result['healthy'] = False
            check_result['issues'].append(f'Health check failed: {str(e)}')
            check_result['checks_failed'] += 1
            logger.error(f"Health check failed for browser {self.browser.instance_id}: {e}")
            return check_result
    
    def _is_browser_alive(self) -> bool:
        """Check if browser process is alive"""
        try:
            if self.browser.driver is None:
                return False
            
            # Try to execute a simple JavaScript command
            if SELENIUM_AVAILABLE:
                self.browser.driver.execute_script("return 1;")
                return True
            else:
                # Fallback: check if we can access basic properties
                return hasattr(self.browser.driver, 'current_url')
                
        except Exception:
            return False
    
    def _get_max_memory(self) -> float:
        """Get max memory limit for browser type"""
        # Different browser types have different memory profiles
        memory_limits = {
            BrowserType.CHROME: 300.0,
            BrowserType.FIREFOX: 250.0,
            BrowserType.SAFARI: 200.0,
            BrowserType.EDGE: 280.0
        }
        return memory_limits.get(self.browser.browser_type, 300.0)
    
    def _get_max_cpu(self) -> float:
        """Get max CPU limit for browser type"""
        cpu_limits = {
            BrowserType.CHROME: 70.0,
            BrowserType.FIREFOX: 60.0,
            BrowserType.SAFARI: 50.0,
            BrowserType.EDGE: 65.0
        }
        return cpu_limits.get(self.browser.browser_type, 70.0)


class BrowserPerformanceAnalyzer:
    """Analyze browser performance metrics"""
    
    def __init__(self):
        self.baselines = {}
        self.learning_rate = 0.1
    
    def analyze_performance(self, browser: BrowserInstance) -> Dict[str, Any]:
        """Analyze browser performance"""
        analysis = {
            'instance_id': browser.instance_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'performance_score': 1.0,
            'issues': [],
            'recommendations': [],
            'metrics': {}
        }
        
        try:
            # Calculate performance score
            scores = []
            
            # Memory performance
            memory_score = self._score_memory_usage(browser)
            scores.append(memory_score)
            analysis['metrics']['memory'] = {
                'score': memory_score,
                'usage_mb': browser.memory_usage,
                'baseline': self.baselines.get('memory', 150.0)
            }
            
            # CPU performance
            cpu_score = self._score_cpu_usage(browser)
            scores.append(cpu_score)
            analysis['metrics']['cpu'] = {
                'score': cpu_score,
                'usage_percent': browser.cpu_usage,
                'baseline': self.baselines.get('cpu', 20.0)
            }
            
            # Response time performance
            response_score = self._score_response_times(browser)
            scores.append(response_score)
            analysis['metrics']['response_time'] = {
                'score': response_score,
                'avg_ms': statistics.mean(browser.response_times) if browser.response_times else 0,
                'baseline': self.baselines.get('response_time', 500.0)
            }
            
            # Page load performance
            load_score = self._score_page_load_times(browser)
            scores.append(load_score)
            analysis['metrics']['page_load'] = {
                'score': load_score,
                'avg_seconds': statistics.mean(browser.page_load_times) if browser.page_load_times else 0,
                'baseline': self.baselines.get('page_load', 3.0)
            }
            
            # Error rate performance
            error_score = self._score_error_rate(browser)
            scores.append(error_score)
            analysis['metrics']['error_rate'] = {
                'score': error_score,
                'rate': self._calculate_error_rate(browser),
                'baseline': self.baselines.get('error_rate', 0.02)
            }
            
            # Calculate overall performance score
            analysis['performance_score'] = statistics.mean(scores)
            
            # Identify issues
            if memory_score < 0.7:
                analysis['issues'].append('High memory usage detected')
                analysis['recommendations'].append('Consider restarting browser or reducing concurrent tabs')
            
            if cpu_score < 0.7:
                analysis['issues'].append('High CPU usage detected')
                analysis['recommendations'].append('Check for runaway processes or optimize page scripts')
            
            if response_score < 0.7:
                analysis['issues'].append('Slow response times detected')
                analysis['recommendations'].append('Investigate network latency or server performance')
            
            if load_score < 0.7:
                analysis['issues'].append('Slow page load times detected')
                analysis['recommendations'].append('Optimize page content or check network connection')
            
            if error_score < 0.7:
                analysis['issues'].append('High error rate detected')
                analysis['recommendations'].append('Review JavaScript errors and network issues')
            
            return analysis
            
        except Exception as e:
            logger.error(f"Performance analysis failed for browser {browser.instance_id}: {e}")
            analysis['error'] = str(e)
            return analysis
    
    def _score_memory_usage(self, browser: BrowserInstance) -> float:
        """Score memory usage (0-1, higher is better)"""
        if browser.memory_usage <= 100:
            return 1.0
        elif browser.memory_usage <= 200:
            return 0.9
        elif browser.memory_usage <= 300:
            return 0.7
        elif browser.memory_usage <= 500:
            return 0.5
        else:
            return 0.2
    
    def _score_cpu_usage(self, browser: BrowserInstance) -> float:
        """Score CPU usage (0-1, higher is better)"""
        if browser.cpu_usage <= 20:
            return 1.0
        elif browser.cpu_usage <= 40:
            return 0.8
        elif browser.cpu_usage <= 60:
            return 0.6
        elif browser.cpu_usage <= 80:
            return 0.4
        else:
            return 0.1
    
    def _score_response_times(self, browser: BrowserInstance) -> float:
        """Score response times (0-1, higher is better)"""
        if not browser.response_times:
            return 0.8
        
        avg_response = statistics.mean(browser.response_times)
        if avg_response <= 200:
            return 1.0
        elif avg_response <= 500:
            return 0.9
        elif avg_response <= 1000:
            return 0.7
        elif avg_response <= 2000:
            return 0.5
        else:
            return 0.2
    
    def _score_page_load_times(self, browser: BrowserInstance) -> float:
        """Score page load times (0-1, higher is better)"""
        if not browser.page_load_times:
            return 0.8
        
        avg_load_time = statistics.mean(browser.page_load_times)
        if avg_load_time <= 2:
            return 1.0
        elif avg_load_time <= 5:
            return 0.8
        elif avg_load_time <= 10:
            return 0.6
        elif avg_load_time <= 15:
            return 0.4
        else:
            return 0.1
    
    def _score_error_rate(self, browser: BrowserInstance) -> float:
        """Score error rate (0-1, higher is better)"""
        error_rate = self._calculate_error_rate(browser)
        if error_rate <= 0.01:
            return 1.0
        elif error_rate <= 0.02:
            return 0.9
        elif error_rate <= 0.05:
            return 0.7
        elif error_rate <= 0.1:
            return 0.5
        else:
            return 0.2
    
    def _calculate_error_rate(self, browser: BrowserInstance) -> float:
        """Calculate error rate"""
        total_ops = browser.error_count + browser.success_count
        if total_ops == 0:
            return 0.0
        return browser.error_count / total_ops
    
    def update_baselines(self, metrics: Dict[str, float]):
        """Update performance baselines"""
        for metric_name, value in metrics.items():
            if metric_name in self.baselines:
                # Exponential moving average
                self.baselines[metric_name] = (
                    self.baselines[metric_name] * (1 - self.learning_rate) + 
                    value * self.learning_rate
                )
            else:
                self.baselines[metric_name] = value


class BrowserMonitor:
    """Main browser monitoring system"""
    
    def __init__(self, config: Optional[BrowserMonitoringConfig] = None):
        self.config = config or BrowserMonitoringConfig()
        self.audit_logger = get_audit_logger()
        
        # Browser instances tracking
        self.browser_instances: Dict[UUID, BrowserInstance] = {}
        self.instance_health_checkers: Dict[UUID, BrowserHealthChecker] = {}
        self.instance_locks: Dict[UUID, asyncio.Lock] = {}
        
        # Monitoring components
        self.performance_analyzer = BrowserPerformanceAnalyzer()
        self.risk_monitoring = None
        
        # System state
        self.monitoring_active = False
        self.monitoring_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Statistics
        self.stats = {
            'total_browsers_created': 0,
            'total_browsers_destroyed': 0,
            'total_errors': 0,
            'total_performance_alerts': 0,
            'total_risk_alerts': 0,
            'monitoring_uptime': 0
        }
        
        # Alert tracking
        self.last_alert_times: Dict[str, datetime] = {}
        self.active_alerts: Set[UUID] = set()
        
        logger.info("Browser monitoring system initialized")
    
    async def start_monitoring(self):
        """Start browser monitoring"""
        if self.monitoring_active:
            logger.warning("Browser monitoring already active")
            return
        
        self.monitoring_active = True
        self._shutdown_event.clear()
        
        # Initialize risk monitoring integration
        if self.config.enable_risk_system_integration:
            try:
                self.risk_monitoring = get_risk_monitoring_system()
                logger.info("Risk monitoring integration enabled")
            except Exception as e:
                logger.warning(f"Risk monitoring integration failed: {e}")
        
        # Create monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._performance_monitoring_loop()),
            asyncio.create_task(self._risk_assessment_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
        logger.info("Browser monitoring started")
    
    async def stop_monitoring(self):
        """Stop browser monitoring"""
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
        
        logger.info("Browser monitoring stopped")
    
    def register_browser(self, browser_type: BrowserType, driver: Any) -> UUID:
        """Register a new browser instance"""
        if len(self.browser_instances) >= self.config.max_browser_instances:
            raise RuntimeError("Maximum browser instances reached")
        
        instance_id = uuid4()
        
        browser = BrowserInstance(
            instance_id=instance_id,
            browser_type=browser_type,
            driver=driver,
            state=BrowserState.LAUNCHING
        )
        
        # Store browser instance
        self.browser_instances[instance_id] = browser
        self.instance_locks[instance_id] = asyncio.Lock()
        
        # Create health checker
        self.instance_health_checkers[instance_id] = BrowserHealthChecker(browser)
        
        # Update stats
        self.stats['total_browsers_created'] += 1
        
        logger.info(f"Registered browser instance: {instance_id}")
        
        # Log security event
        self.audit_logger.log_security_event(
            type('SecurityEventLog', (), {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': 'BROWSER_REGISTERED',
                'severity': 'info',
                'user_id': None,
                'ip_address': None,
                'session_id': None,
                'description': f'Browser {browser_type.value} registered',
                'details': {'instance_id': str(instance_id), 'browser_type': browser_type.value}
            })()
        )
        
        return instance_id
    
    def unregister_browser(self, instance_id: UUID) -> bool:
        """Unregister a browser instance"""
        if instance_id not in self.browser_instances:
            return False
        
        browser = self.browser_instances[instance_id]
        
        # Update state
        browser.state = BrowserState.CLOSED
        browser.last_seen = datetime.now(timezone.utc)
        
        # Clean up resources
        try:
            if browser.driver:
                browser.driver.quit()
        except Exception as e:
            logger.warning(f"Error closing browser driver: {e}")
        
        # Remove from tracking
        del self.browser_instances[instance_id]
        del self.instance_health_checkers[instance_id]
        del self.instance_locks[instance_id]
        
        # Update stats
        self.stats['total_browsers_destroyed'] += 1
        
        logger.info(f"Unregistered browser instance: {instance_id}")
        
        return True
    
    async def update_browser_state(self, instance_id: UUID, state: BrowserState, **kwargs):
        """Update browser state"""
        if instance_id not in self.browser_instances:
            return
        
        async with self.instance_locks[instance_id]:
            browser = self.browser_instances[instance_id]
            browser.state = state
            browser.last_activity = datetime.now(timezone.utc)
            browser.last_seen = browser.last_activity
            
            # Update additional state information
            for key, value in kwargs.items():
                if hasattr(browser, key):
                    setattr(browser, key, value)
    
    async def record_browser_metric(self, instance_id: UUID, metric_type: str, value: float, **tags):
        """Record a browser performance metric"""
        if instance_id not in self.browser_instances:
            return
        
        async with self.instance_locks[instance_id]:
            browser = self.browser_instances[instance_id]
            browser.last_seen = datetime.now(timezone.utc)
            
            # Update appropriate metric
            if metric_type == "memory_usage_mb":
                browser.memory_usage = value
            elif metric_type == "cpu_usage_percent":
                browser.cpu_usage = value
            elif metric_type == "response_time_ms":
                browser.response_times.append(value)
                # Keep only recent measurements
                if len(browser.response_times) > 100:
                    browser.response_times = browser.response_times[-50:]
            elif metric_type == "page_load_time_seconds":
                browser.page_load_times.append(value)
                # Keep only recent measurements
                if len(browser.page_load_times) > 100:
                    browser.page_load_times = browser.page_load_times[-50:]
            elif metric_type == "error_count":
                browser.error_count = int(value)
            elif metric_type == "success_count":
                browser.success_count = int(value)
            elif metric_type == "open_tabs":
                browser.open_tabs = int(value)
            elif metric_type == "network_requests":
                browser.network_requests = int(value)
            elif metric_type == "javascript_errors":
                browser.javascript_errors = int(value)
            elif metric_type == "cookies_count":
                browser.cookies_count = int(value)
        
        # Log performance metric
        try:
            log_performance_metric(
                f"browser.{metric_type}",
                value,
                unit=self._get_metric_unit(metric_type),
                tags={'instance_id': str(instance_id), **tags}
            )
        except Exception as e:
            logger.warning(f"Failed to log performance metric: {e}")
    
    def _get_metric_unit(self, metric_type: str) -> str:
        """Get unit for metric type"""
        units = {
            'memory_usage_mb': 'MB',
            'cpu_usage_percent': 'percent',
            'response_time_ms': 'milliseconds',
            'page_load_time_seconds': 'seconds',
            'error_count': 'count',
            'success_count': 'count',
            'open_tabs': 'count',
            'network_requests': 'count',
            'javascript_errors': 'count',
            'cookies_count': 'count'
        }
        return units.get(metric_type, 'unit')
    
    async def _health_check_loop(self):
        """Health check monitoring loop"""
        while self.monitoring_active:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _perform_health_checks(self):
        """Perform health checks on all browser instances"""
        health_tasks = []
        
        for instance_id, checker in self.instance_health_checkers.items():
            if instance_id in self.browser_instances:
                health_tasks.append(checker.check_health())
        
        if health_tasks:
            results = await asyncio.gather(*health_tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, dict):
                    await self._process_health_check_result(result)
                elif isinstance(result, Exception):
                    logger.error(f"Health check task failed: {result}")
    
    async def _process_health_check_result(self, result: Dict[str, Any]):
        """Process health check result"""
        instance_id = UUID(result['instance_id'])
        
        if not result['healthy'] and len(result['issues']) > 0:
            # Check alert cooldown
            alert_key = f"health_{instance_id}"
            last_alert = self.last_alert_times.get(alert_key)
            current_time = datetime.now(timezone.utc)
            
            if not last_alert or (current_time - last_alert).total_seconds() > self.config.alert_cooldown_seconds:
                await self._trigger_health_alert(instance_id, result)
                self.last_alert_times[alert_key] = current_time
    
    async def _trigger_health_alert(self, instance_id: UUID, result: Dict[str, Any]):
        """Trigger health alert"""
        browser = self.browser_instances.get(instance_id)
        if not browser:
            return
        
        # Create alert
        alert = {
            'alert_id': uuid4(),
            'type': 'browser_health',
            'severity': AlertSeverity.WARNING.value,
            'message': f"Browser health issues detected: {', '.join(result['issues'])}",
            'instance_id': str(instance_id),
            'browser_type': browser.browser_type.value,
            'issues': result['issues'],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks_passed': result['checks_passed'],
            'checks_failed': result['checks_failed']
        }
        
        self.active_alerts.add(alert['alert_id'])
        self.stats['total_performance_alerts'] += 1
        
        # Log alert
        logger.warning(f"Browser health alert: {alert['message']}", extra=alert)
        
        # Integrate with risk system
        if self.risk_monitoring and self.config.enable_risk_system_integration:
            try:
                # Create performance metric for risk system
                metric = PerformanceMetric(
                    metric_name=f"browser.health_score",
                    metric_type=MetricType.GAUGE,
                    value=result['checks_passed'] / result['total_checks'] if result['total_checks'] > 0 else 0,
                    unit="ratio",
                    tags={'instance_id': str(instance_id), 'browser_type': browser.browser_type.value}
                )
                self.risk_monitoring.performance_tracker.record_metric(metric)
            except Exception as e:
                logger.warning(f"Failed to integrate with risk monitoring: {e}")
    
    async def _performance_monitoring_loop(self):
        """Performance monitoring loop"""
        while self.monitoring_active:
            try:
                await self._analyze_performance()
                await asyncio.sleep(self.config.performance_check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in performance monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _analyze_performance(self):
        """Analyze performance of all browser instances"""
        for browser in list(self.browser_instances.values()):
            try:
                analysis = self.performance_analyzer.analyze_performance(browser)
                await self._process_performance_analysis(browser, analysis)
            except Exception as e:
                logger.error(f"Performance analysis failed for browser {browser.instance_id}: {e}")
    
    async def _process_performance_analysis(self, browser: BrowserInstance, analysis: Dict[str, Any]):
        """Process performance analysis result"""
        # Update browser health score
        browser.health_score = analysis['performance_score']
        
        # Update baselines
        metrics_for_baseline = {}
        for metric_name, metric_data in analysis['metrics'].items():
            if metric_name == 'memory':
                metrics_for_baseline['memory'] = metric_data['usage_mb']
            elif metric_name == 'cpu':
                metrics_for_baseline['cpu'] = metric_data['usage_percent']
            elif metric_name == 'response_time':
                metrics_for_baseline['response_time'] = metric_data['avg_ms']
            elif metric_name == 'page_load':
                metrics_for_baseline['page_load'] = metric_data['avg_seconds']
            elif metric_name == 'error_rate':
                metrics_for_baseline['error_rate'] = metric_data['rate']
        
        self.performance_analyzer.update_baselines(metrics_for_baseline)
        
        # Check for performance alerts
        if len(analysis['issues']) > 0:
            alert_key = f"performance_{browser.instance_id}"
            last_alert = self.last_alert_times.get(alert_key)
            current_time = datetime.now(timezone.utc)
            
            if not last_alert or (current_time - last_alert).total_seconds() > self.config.alert_cooldown_seconds:
                await self._trigger_performance_alert(browser, analysis)
                self.last_alert_times[alert_key] = current_time
    
    async def _trigger_performance_alert(self, browser: BrowserInstance, analysis: Dict[str, Any]):
        """Trigger performance alert"""
        alert = {
            'alert_id': uuid4(),
            'type': 'browser_performance',
            'severity': AlertSeverity.WARNING.value,
            'message': f"Performance issues detected: {', '.join(analysis['issues'])}",
            'instance_id': str(browser.instance_id),
            'browser_type': browser.browser_type.value,
            'performance_score': analysis['performance_score'],
            'issues': analysis['issues'],
            'recommendations': analysis['recommendations'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.active_alerts.add(alert['alert_id'])
        self.stats['total_performance_alerts'] += 1
        
        logger.warning(f"Browser performance alert: {alert['message']}", extra=alert)
    
    async def _risk_assessment_loop(self):
        """Risk assessment monitoring loop"""
        while self.monitoring_active:
            try:
                await self._assess_risks()
                await asyncio.sleep(self.config.risk_assessment_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in risk assessment loop: {e}", exc_info=True)
                await asyncio.sleep(10)
    
    async def _assess_risks(self):
        """Assess risks for all browser instances"""
        for browser in list(self.browser_instances.values()):
            try:
                risk_assessment = await self._calculate_risk_score(browser)
                await self._process_risk_assessment(browser, risk_assessment)
            except Exception as e:
                logger.error(f"Risk assessment failed for browser {browser.instance_id}: {e}")
    
    async def _calculate_risk_score(self, browser: BrowserInstance) -> Dict[str, Any]:
        """Calculate risk score for browser instance"""
        risk_factors = []
        risk_score = 0.0
        
        # Memory risk
        if browser.memory_usage > 400:
            risk_factors.append('high_memory_usage')
            risk_score += 0.3
        elif browser.memory_usage > 250:
            risk_factors.append('medium_memory_usage')
            risk_score += 0.15
        
        # CPU risk
        if browser.cpu_usage > 80:
            risk_factors.append('high_cpu_usage')
            risk_score += 0.25
        elif browser.cpu_usage > 60:
            risk_factors.append('medium_cpu_usage')
            risk_score += 0.1
        
        # Error rate risk
        total_ops = browser.error_count + browser.success_count
        if total_ops > 0:
            error_rate = browser.error_count / total_ops
            if error_rate > 0.1:
                risk_factors.append('very_high_error_rate')
                risk_score += 0.4
            elif error_rate > 0.05:
                risk_factors.append('high_error_rate')
                risk_score += 0.2
            elif error_rate > 0.02:
                risk_factors.append('medium_error_rate')
                risk_score += 0.1
        
        # Age risk (older instances more risky)
        age_hours = (datetime.now(timezone.utc) - browser.created_at).total_seconds() / 3600
        if age_hours > 24:
            risk_factors.append('long_running_instance')
            risk_score += 0.1
        elif age_hours > 12:
            risk_factors.append('aging_instance')
            risk_score += 0.05
        
        # State risk
        if browser.state == BrowserState.ERROR:
            risk_factors.append('error_state')
            risk_score += 0.5
        elif browser.state == BrowserState.CRASHED:
            risk_factors.append('crashed_state')
            risk_score += 0.8
        
        # Activity risk (inactive browsers might be stuck)
        time_since_activity = (datetime.now(timezone.utc) - browser.last_activity).total_seconds()
        if time_since_activity > 900:  # 15 minutes
            risk_factors.append('inactive_too_long')
            risk_score += 0.15
        
        # Normalize risk score
        risk_score = min(risk_score, 1.0)
        
        # Determine risk level
        if risk_score >= self.config.risk_threshold_critical:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= self.config.risk_threshold_high:
            risk_level = RiskLevel.HIGH
        elif risk_score >= self.config.risk_threshold_medium:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def _process_risk_assessment(self, browser: BrowserInstance, assessment: Dict[str, Any]):
        """Process risk assessment result"""
        browser.risk_score = assessment['risk_score']
        browser.risk_level = assessment['risk_level']
        browser.last_risk_assessment = datetime.now(timezone.utc)
        
        # Check for high risk alerts
        if browser.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            alert_key = f"risk_{browser.instance_id}_{browser.risk_level.value}"
            last_alert = self.last_alert_times.get(alert_key)
            current_time = datetime.now(timezone.utc)
            
            if not last_alert or (current_time - last_alert).total_seconds() > self.config.alert_cooldown_seconds:
                await self._trigger_risk_alert(browser, assessment)
                self.last_alert_times[alert_key] = current_time
    
    async def _trigger_risk_alert(self, browser: BrowserInstance, assessment: Dict[str, Any]):
        """Trigger risk alert"""
        severity = AlertSeverity.ERROR if browser.risk_level == RiskLevel.CRITICAL else AlertSeverity.WARNING
        
        alert = {
            'alert_id': uuid4(),
            'type': 'browser_risk',
            'severity': severity.value,
            'message': f"High risk detected: {browser.risk_level.value} risk level ({assessment['risk_score']:.2f})",
            'instance_id': str(browser.instance_id),
            'browser_type': browser.browser_type.value,
            'risk_score': assessment['risk_score'],
            'risk_level': browser.risk_level.value,
            'risk_factors': assessment['risk_factors'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.active_alerts.add(alert['alert_id'])
        self.stats['total_risk_alerts'] += 1
        
        logger.warning(f"Browser risk alert: {alert['message']}", extra=alert)
        
        # Integrate with risk system
        if self.risk_monitoring and self.config.enable_risk_system_integration:
            try:
                metric = PerformanceMetric(
                    metric_name="browser.risk_score",
                    metric_type=MetricType.GAUGE,
                    value=assessment['risk_score'],
                    unit="ratio",
                    tags={
                        'instance_id': str(browser.instance_id),
                        'browser_type': browser.browser_type.value,
                        'risk_level': browser.risk_level.value
                    }
                )
                self.risk_monitoring.performance_tracker.record_metric(metric)
            except Exception as e:
                logger.warning(f"Failed to integrate risk with monitoring system: {e}")
    
    async def _cleanup_loop(self):
        """Cleanup monitoring loop"""
        while self.monitoring_active:
            try:
                await self._cleanup_stale_instances()
                await asyncio.sleep(self.config.cleanup_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    async def _cleanup_stale_instances(self):
        """Cleanup stale browser instances"""
        current_time = datetime.now(timezone.utc)
        instances_to_remove = []
        
        for browser in list(self.browser_instances.values()):
            # Check if instance is too old
            age_seconds = (current_time - browser.created_at).total_seconds()
            if age_seconds > self.config.session_timeout_seconds:
                instances_to_remove.append(browser.instance_id)
                continue
            
            # Check if instance hasn't been seen recently
            time_since_seen = (current_time - browser.last_seen).total_seconds()
            if time_since_seen > self.config.browser_timeout_seconds:
                # Try to reconnect or mark as stale
                try:
                    if browser.state not in [BrowserState.CLOSED, BrowserState.CRASHED]:
                        # Attempt to check if browser is still responsive
                        checker = self.instance_health_checkers.get(browser.instance_id)
                        if checker and not checker._is_browser_alive():
                            logger.warning(f"Browser {browser.instance_id} appears to be dead, marking as crashed")
                            browser.state = BrowserState.CRASHED
                except Exception as e:
                    logger.warning(f"Error checking browser responsiveness: {e}")
        
        # Remove stale instances
        for instance_id in instances_to_remove:
            logger.info(f"Removing stale browser instance: {instance_id}")
            self.unregister_browser(instance_id)
    
    def get_browser_instances(self) -> List[Dict[str, Any]]:
        """Get all browser instances"""
        return [browser.to_dict() for browser in self.browser_instances.values()]
    
    def get_browser_instance(self, instance_id: UUID) -> Optional[Dict[str, Any]]:
        """Get specific browser instance"""
        browser = self.browser_instances.get(instance_id)
        return browser.to_dict() if browser else None
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring system summary"""
        current_time = datetime.now(timezone.utc)
        
        # Calculate system totals
        total_memory = sum(browser.memory_usage for browser in self.browser_instances.values())
        total_cpu = sum(browser.cpu_usage for browser in self.browser_instances.values())
        
        # Count browsers by state
        state_counts = defaultdict(int)
        risk_counts = defaultdict(int)
        
        for browser in self.browser_instances.values():
            state_counts[browser.state.value] += 1
            risk_counts[browser.risk_level.value] += 1
        
        # Calculate average health score
        health_scores = [browser.health_score for browser in self.browser_instances.values()]
        avg_health_score = statistics.mean(health_scores) if health_scores else 0.0
        
        return {
            'timestamp': current_time.isoformat(),
            'monitoring_active': self.monitoring_active,
            'total_browsers': len(self.browser_instances),
            'system_resources': {
                'total_memory_mb': total_memory,
                'total_cpu_percent': total_cpu,
                'memory_usage_percent': (total_memory / self.config.max_memory_total_mb) * 100,
                'cpu_usage_percent': (total_cpu / self.config.max_cpu_total_percent) * 100
            },
            'browser_states': dict(state_counts),
            'risk_distribution': dict(risk_counts),
            'average_health_score': avg_health_score,
            'active_alerts': len(self.active_alerts),
            'statistics': self.stats.copy(),
            'configuration': {
                'max_browser_instances': self.config.max_browser_instances,
                'max_memory_total_mb': self.config.max_memory_total_mb,
                'max_cpu_total_percent': self.config.max_cpu_total_percent,
                'health_check_interval': self.config.health_check_interval_seconds,
                'performance_check_interval': self.config.performance_check_interval_seconds,
                'risk_assessment_interval': self.config.risk_assessment_interval_seconds
            }
        }
    
    def get_performance_report(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance report for time period"""
        # This would typically query stored metrics
        # For now, return current state summary
        
        if not self.browser_instances:
            return {'message': 'No browser instances to report on'}
        
        reports = []
        for browser in self.browser_instances.values():
            analysis = self.performance_analyzer.analyze_performance(browser)
            reports.append({
                'instance_id': str(browser.instance_id),
                'browser_type': browser.browser_type.value,
                'current_state': browser.state.value,
                'performance_analysis': analysis,
                'resource_usage': {
                    'memory_mb': browser.memory_usage,
                    'cpu_percent': browser.cpu_usage
                },
                'activity_metrics': {
                    'uptime_hours': (datetime.now(timezone.utc) - browser.created_at).total_seconds() / 3600,
                    'total_operations': browser.error_count + browser.success_count,
                    'error_rate': self._calculate_error_rate(browser)
                }
            })
        
        return {
            'report_period_hours': hours,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_browsers': len(reports),
            'reports': reports
        }
    
    def _calculate_error_rate(self, browser: BrowserInstance) -> float:
        """Calculate error rate for browser"""
        total_ops = browser.error_count + browser.success_count
        if total_ops == 0:
            return 0.0
        return browser.error_count / total_ops
    
    async def force_health_check(self, instance_id: UUID) -> Optional[Dict[str, Any]]:
        """Force health check on specific browser instance"""
        checker = self.instance_health_checkers.get(instance_id)
        if not checker:
            return None
        
        return await checker.check_health()
    
    async def optimize_browser_resources(self, instance_id: UUID) -> Dict[str, Any]:
        """Attempt to optimize browser resources"""
        browser = self.browser_instances.get(instance_id)
        if not browser:
            return {'error': 'Browser instance not found'}
        
        optimization_result = {
            'instance_id': str(instance_id),
            'actions_taken': [],
            'results': {},
            'recommendations': []
        }
        
        try:
            # Memory optimization
            if browser.memory_usage > 300:
                optimization_result['actions_taken'].append('memory_cleanup_recommended')
                optimization_result['recommendations'].append('Consider restarting browser or closing unnecessary tabs')
            
            # CPU optimization
            if browser.cpu_usage > 70:
                optimization_result['actions_taken'].append('cpu_optimization_needed')
                optimization_result['recommendations'].append('Check for runaway JavaScript processes')
            
            # Tab optimization
            if browser.open_tabs > 5:
                optimization_result['actions_taken'].append('tab_reduction_needed')
                optimization_result['recommendations'].append('Close unnecessary tabs to reduce resource usage')
            
            # Error rate optimization
            total_ops = browser.error_count + browser.success_count
            if total_ops > 0 and browser.error_count / total_ops > 0.05:
                optimization_result['actions_taken'].append('error_investigation_needed')
                optimization_result['recommendations'].append('Review JavaScript console for errors')
            
            optimization_result['results'] = {
                'memory_before_mb': browser.memory_usage,
                'cpu_before_percent': browser.cpu_usage,
                'tabs_before': browser.open_tabs,
                'error_rate_before': self._calculate_error_rate(browser)
            }
            
            logger.info(f"Resource optimization analysis for browser {instance_id}: {optimization_result}")
            
        except Exception as e:
            optimization_result['error'] = str(e)
            logger.error(f"Resource optimization failed for browser {instance_id}: {e}")
        
        return optimization_result
    
    async def shutdown(self):
        """Graceful shutdown of browser monitoring"""
        logger.info("Initiating browser monitoring shutdown")
        
        # Stop monitoring loops
        await self.stop_monitoring()
        
        # Cleanup all browser instances
        for instance_id in list(self.browser_instances.keys()):
            self.unregister_browser(instance_id)
        
        # Clear active alerts
        self.active_alerts.clear()
        
        logger.info("Browser monitoring shutdown completed")


# Global browser monitoring instance
_global_browser_monitor = None


def get_browser_monitor() -> BrowserMonitor:
    """Get or create global browser monitor"""
    global _global_browser_monitor
    if _global_browser_monitor is None:
        _global_browser_monitor = BrowserMonitor()
    return _global_browser_monitor


if __name__ == "__main__":
    # Example usage and testing
    async def test_browser_monitor():
        # Setup
        config = BrowserMonitoringConfig()
        monitor = BrowserMonitor(config)
        
        print("Starting browser monitoring system...")
        await monitor.start_monitoring()
        
        # Simulate browser instances (if Selenium were available)
        print("Monitoring summary:", json.dumps(monitor.get_monitoring_summary(), indent=2))
        
        # Let it run for a bit
        await asyncio.sleep(5)
        
        print("Performance report:", json.dumps(monitor.get_performance_report(), indent=2))
        
        # Stop monitoring
        print("Stopping browser monitoring system...")
        await monitor.shutdown()
        
        print("Browser monitoring system test completed!")
    
    # Run test
    asyncio.run(test_browser_monitor())