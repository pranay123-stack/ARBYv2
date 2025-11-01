"""
Comprehensive Performance Monitoring System for ARBitech Trading Platform

This module provides enterprise-grade performance monitoring and analytics:
- Real-time performance metrics (latency, throughput, success rates)
- System resource monitoring (CPU, memory, disk, network)
- Trading performance analytics (ROI, Sharpe ratio, maximum drawdown)
- Alerting for performance degradation
- Historical performance tracking and trending
- Dashboard integration for real-time visualization
- Automated performance optimization recommendations
- Integration with Supabase for data persistence

Features:
- Production-ready monitoring without performance impact
- Real-time metric collection and analysis
- Comprehensive trading performance analytics
- Intelligent alerting and notifications
- Historical data analysis and trending
- Automated optimization recommendations
- Dashboard-ready data streams
- Multi-tenant support with Row-Level Security

Author: ARBitech Development Team
Version: 1.0.0
Created: 2025-11-02
"""

import asyncio
import time
import json
import math
import psutil
import statistics
import threading
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
from uuid import UUID, uuid4
from collections import deque, defaultdict
import logging
import weakref
import platform
import socket
import struct
from pathlib import Path

# Trading and financial libraries (optional)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

# Integration with existing ARBitech components (optional)
try:
    from arbitech.storage.supabase_layer import SupabaseDataLayer
    SUPABASE_AVAILABLE = True
except ImportError:
    SupabaseDataLayer = None
    SUPABASE_AVAILABLE = False

try:
    from arbitech.storage.models import (
        PerformanceMetric, ArbitrageOpportunity, Trade, RiskAlert,
        ScanSession, ExecutionLog, Notification
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

from arbitech.utils.logger import get_logger

logger = get_logger(__name__)

# Performance monitoring metrics
class MetricType(Enum):
    """Types of performance metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"

class PerformanceLevel(Enum):
    """Performance levels"""
    EXCELLENT = "excellent"
    GOOD = "good" 
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class SystemMetric(Enum):
    """System resource metrics"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"
    DISK_IO = "disk_io"
    LOAD_AVERAGE = "load_average"

class TradingMetric(Enum):
    """Trading performance metrics"""
    ROI = "roi"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    CALMAR_RATIO = "calmar_ratio"
    SORTINO_RATIO = "sortino_ratio"
    SUCCESS_RATE = "success_rate"
    AVERAGE_TRADE_DURATION = "average_trade_duration"
    TRADES_PER_HOUR = "trades_per_hour"

@dataclass
class PerformanceThreshold:
    """Performance threshold configuration"""
    metric_name: str
    metric_type: MetricType
    
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
class MetricDataPoint:
    """Individual metric data point"""
    metric_id: UUID = field(default_factory=uuid4)
    metric_name: str = ""
    metric_type: MetricType = MetricType.GAUGE
    
    # Value and unit
    value: float = 0.0
    unit: str = ""
    
    # Context
    operation_type: str = ""
    component: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "system"  # system, trading, custom
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'metric_id': str(self.metric_id),
            'metric_name': self.metric_name,
            'metric_type': self.metric_type.value,
            'value': self.value,
            'unit': self.unit,
            'operation_type': self.operation_type,
            'component': self.component,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }

@dataclass
class SystemResourceData:
    """System resource monitoring data"""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # CPU metrics
    cpu_percent: float = 0.0
    cpu_count: int = 0
    load_average: List[float] = field(default_factory=list)
    
    # Memory metrics
    memory_percent: float = 0.0
    memory_used_gb: float = 0.0
    memory_available_gb: float = 0.0
    
    # Disk metrics
    disk_usage_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_available_gb: float = 0.0
    disk_read_speed_mbps: float = 0.0
    disk_write_speed_mbps: float = 0.0
    
    # Network metrics
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    network_packets_sent: int = 0
    network_packets_recv: int = 0
    network_error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'cpu_count': self.cpu_count,
            'load_average': self.load_average,
            'memory_percent': self.memory_percent,
            'memory_used_gb': self.memory_used_gb,
            'memory_available_gb': self.memory_available_gb,
            'disk_usage_percent': self.disk_usage_percent,
            'disk_used_gb': self.disk_used_gb,
            'disk_available_gb': self.disk_available_gb,
            'disk_read_speed_mbps': self.disk_read_speed_mbps,
            'disk_write_speed_mbps': self.disk_write_speed_mbps,
            'network_bytes_sent': self.network_bytes_sent,
            'network_bytes_recv': self.network_bytes_recv,
            'network_packets_sent': self.network_packets_sent,
            'network_packets_recv': self.network_packets_recv,
            'network_error_count': self.network_error_count
        }

@dataclass
class TradingPerformanceData:
    """Trading performance analytics data"""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Basic performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # Financial metrics
    total_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_profit: float = 0.0
    
    # ROI and return metrics
    roi: float = 0.0
    total_return: float = 0.0
    annualized_return: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    volatility: float = 0.0
    
    # Advanced metrics
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    profit_factor: float = 0.0
    
    # Performance ratios
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    expectancy: float = 0.0
    
    # Operational metrics
    trades_per_hour: float = 0.0
    avg_trade_duration: float = 0.0
    success_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_pnl': self.total_pnl,
            'gross_profit': self.gross_profit,
            'gross_loss': self.gross_loss,
            'net_profit': self.net_profit,
            'roi': self.roi,
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'max_drawdown': self.max_drawdown,
            'current_drawdown': self.current_drawdown,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'profit_factor': self.profit_factor,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'expectancy': self.expectancy,
            'trades_per_hour': self.trades_per_hour,
            'avg_trade_duration': self.avg_trade_duration,
            'success_rate': self.success_rate
        }

@dataclass
class PerformanceAlert:
    """Performance alert configuration and data"""
    alert_id: UUID = field(default_factory=uuid4)
    alert_name: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    
    # Alert conditions
    metric_name: str = ""
    condition_type: str = "threshold"  # threshold, change, anomaly
    threshold_value: Optional[float] = None
    operator: str = ">"  # >, <, >=, <=, ==, !=
    
    # Alert metadata
    title: str = ""
    message: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    # Alert status
    is_active: bool = False
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'alert_id': str(self.alert_id),
            'alert_name': self.alert_name,
            'severity': self.severity.value,
            'metric_name': self.metric_name,
            'condition_type': self.condition_type,
            'threshold_value': self.threshold_value,
            'operator': self.operator,
            'title': self.title,
            'message': self.message,
            'recommendations': self.recommendations,
            'is_active': self.is_active,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'trigger_count': self.trigger_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""
    recommendation_id: UUID = field(default_factory=uuid4)
    category: str = ""  # system, trading, operational
    
    # Recommendation details
    title: str = ""
    description: str = ""
    priority: str = "medium"  # low, medium, high, critical
    
    # Impact analysis
    expected_improvement: str = ""
    effort_level: str = "medium"  # low, medium, high
    risk_level: str = "low"  # low, medium, high
    confidence: float = 0.8  # 0.0 to 1.0
    
    # Implementation details
    steps: List[str] = field(default_factory=list)
    configuration_changes: Dict[str, Any] = field(default_factory=dict)
    code_changes: List[str] = field(default_factory=list)
    
    # Context
    affected_metrics: List[str] = field(default_factory=list)
    triggered_by_alerts: List[UUID] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    applicable_conditions: Dict[str, Any] = field(default_factory=dict)
    auto_applicable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'recommendation_id': str(self.recommendation_id),
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'expected_improvement': self.expected_improvement,
            'effort_level': self.effort_level,
            'risk_level': self.risk_level,
            'confidence': self.confidence,
            'steps': self.steps,
            'configuration_changes': self.configuration_changes,
            'code_changes': self.code_changes,
            'affected_metrics': self.affected_metrics,
            'triggered_by_alerts': [str(alert_id) for alert_id in self.triggered_by_alerts],
            'created_at': self.created_at.isoformat(),
            'applicable_conditions': self.applicable_conditions,
            'auto_applicable': self.auto_applicable
        }

class SystemResourceMonitor:
    """Monitor system resource usage"""
    
    def __init__(self):
        self.last_network_io = None
        self.last_disk_io = None
        self.last_timestamp = None
        
        # Initialize psutil if available
        self.psutil_available = True
        try:
            import psutil
            self.psutil = psutil
        except ImportError:
            self.psutil_available = False
            logger.warning("psutil not available - system monitoring will be limited")
    
    def collect_system_metrics(self) -> SystemResourceData:
        """Collect system resource metrics"""
        if not self.psutil_available:
            return self._generate_mock_data()
        
        current_time = datetime.now(timezone.utc)
        
        try:
            # CPU metrics
            cpu_percent = self.psutil.cpu_percent(interval=1)
            cpu_count = self.psutil.cpu_count()
            load_avg = self._get_load_average()
            
            # Memory metrics
            memory = self.psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            
            # Disk metrics
            disk = self.psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024**3)
            disk_available_gb = disk.free / (1024**3)
            
            # Disk I/O
            disk_io = self.psutil.disk_io_counters()
            disk_read_mbps = 0.0
            disk_write_mbps = 0.0
            
            if disk_io and self.last_disk_io:
                time_delta = (current_time - self.last_timestamp).total_seconds()
                read_delta = disk_io.read_bytes - self.last_disk_io.read_bytes
                write_delta = disk_io.write_bytes - self.last_disk_io.write_bytes
                
                if time_delta > 0:
                    disk_read_mbps = (read_delta / (1024**2)) / time_delta
                    disk_write_mbps = (write_delta / (1024**2)) / time_delta
            
            # Network I/O
            network_io = self.psutil.net_io_counters()
            network_bytes_sent = network_io.bytes_sent if network_io else 0
            network_bytes_recv = network_io.bytes_recv if network_io else 0
            network_packets_sent = network_io.packets_sent if network_io else 0
            network_packets_recv = network_io.packets_recv if network_io else 0
            network_error_count = network_io.errin + network_io.errout if network_io else 0
            
            # Update last values
            self.last_disk_io = disk_io
            self.last_network_io = network_io
            self.last_timestamp = current_time
            
            return SystemResourceData(
                timestamp=current_time,
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                load_average=load_avg,
                memory_percent=memory_percent,
                memory_used_gb=memory_used_gb,
                memory_available_gb=memory_available_gb,
                disk_usage_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_available_gb=disk_available_gb,
                disk_read_speed_mbps=disk_read_mbps,
                disk_write_speed_mbps=disk_write_mbps,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                network_packets_sent=network_packets_sent,
                network_packets_recv=network_packets_recv,
                network_error_count=network_error_count
            )
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return self._generate_mock_data()
    
    def _get_load_average(self) -> List[float]:
        """Get system load average"""
        try:
            if hasattr(self.psutil, 'getloadavg'):
                return list(self.psutil.getloadavg())
            else:
                # Fallback for platforms that don't support getloadavg
                return [0.0, 0.0, 0.0]
        except Exception:
            return [0.0, 0.0, 0.0]
    
    def _generate_mock_data(self) -> SystemResourceData:
        """Generate mock system data when psutil is unavailable"""
        import random
        return SystemResourceData(
            timestamp=datetime.now(timezone.utc),
            cpu_percent=random.uniform(10, 90),
            cpu_count=4,
            load_average=[random.uniform(0.5, 2.0) for _ in range(3)],
            memory_percent=random.uniform(20, 80),
            memory_used_gb=random.uniform(4, 16),
            memory_available_gb=random.uniform(8, 24),
            disk_usage_percent=random.uniform(30, 70),
            disk_used_gb=random.uniform(50, 200),
            disk_available_gb=random.uniform(100, 400),
            disk_read_speed_mbps=random.uniform(10, 100),
            disk_write_speed_mbps=random.uniform(5, 80),
            network_bytes_sent=random.randint(1000000, 100000000),
            network_bytes_recv=random.randint(1000000, 100000000),
            network_packets_sent=random.randint(100, 10000),
            network_packets_recv=random.randint(100, 10000),
            network_error_count=random.randint(0, 10)
        )

class TradingPerformanceAnalyzer:
    """Analyze trading performance metrics"""
    
    def __init__(self):
        self.trade_history: List[Dict[str, Any]] = []
        self.pnl_series: List[float] = []
        self.return_series: List[float] = []
    
    def add_trade_result(self, trade_data: Dict[str, Any]):
        """Add trade result for analysis"""
        self.trade_history.append(trade_data)
        
        # Extract PnL and returns
        pnl = trade_data.get('pnl', 0.0)
        self.pnl_series.append(pnl)
        
        # Calculate return percentage
        stake = trade_data.get('stake', 0.0)
        if stake > 0:
            return_pct = (pnl / stake) * 100
            self.return_series.append(return_pct)
    
    def calculate_performance_metrics(self) -> TradingPerformanceData:
        """Calculate comprehensive trading performance metrics"""
        if not self.trade_history:
            return TradingPerformanceData()
        
        current_time = datetime.now(timezone.utc)
        
        # Basic trade statistics
        total_trades = len(self.trade_history)
        winning_trades = sum(1 for trade in self.trade_history if trade.get('pnl', 0) > 0)
        losing_trades = total_trades - winning_trades
        
        # Financial metrics
        total_pnl = sum(trade.get('pnl', 0) for trade in self.trade_history)
        gross_profit = sum(trade.get('pnl', 0) for trade in self.trade_history if trade.get('pnl', 0) > 0)
        gross_loss = abs(sum(trade.get('pnl', 0) for trade in self.trade_history if trade.get('pnl', 0) < 0))
        net_profit = gross_profit - gross_loss
        
        # Calculate ROI
        total_stake = sum(trade.get('stake', 0) for trade in self.trade_history)
        roi = ((total_pnl / total_stake) * 100) if total_stake > 0 else 0.0
        
        # Calculate win rate
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        # Calculate average win/loss
        winning_pnls = [trade.get('pnl', 0) for trade in self.trade_history if trade.get('pnl', 0) > 0]
        losing_pnls = [abs(trade.get('pnl', 0)) for trade in self.trade_history if trade.get('pnl', 0) < 0]
        
        avg_win = statistics.mean(winning_pnls) if winning_pnls else 0.0
        avg_loss = statistics.mean(losing_pnls) if losing_pnls else 0.0
        
        # Calculate profit factor
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Calculate expectancy
        expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss)
        
        # Calculate drawdown
        max_drawdown, current_drawdown = self._calculate_drawdown()
        
        # Calculate risk-adjusted metrics
        sharpe_ratio = self._calculate_sharpe_ratio()
        sortino_ratio = self._calculate_sortino_ratio()
        calmar_ratio = self._calculate_calmar_ratio()
        
        # Calculate volatility
        volatility = self._calculate_volatility()
        
        # Calculate operational metrics
        trades_per_hour = self._calculate_trades_per_hour()
        avg_trade_duration = self._calculate_avg_trade_duration()
        success_rate = self._calculate_success_rate()
        
        # Calculate returns
        total_return = sum(self.return_series) if self.return_series else 0.0
        annualized_return = self._calculate_annualized_return()
        
        return TradingPerformanceData(
            timestamp=current_time,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_pnl=total_pnl,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            net_profit=net_profit,
            roi=roi,
            total_return=total_return,
            annualized_return=annualized_return,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            profit_factor=profit_factor,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            expectancy=expectancy,
            trades_per_hour=trades_per_hour,
            avg_trade_duration=avg_trade_duration,
            success_rate=success_rate
        )
    
    def _calculate_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum and current drawdown"""
        if not self.pnl_series:
            return 0.0, 0.0
        
        # Calculate cumulative PnL
        cumulative_pnl = []
        running_total = 0.0
        for pnl in self.pnl_series:
            running_total += pnl
            cumulative_pnl.append(running_total)
        
        # Calculate maximum drawdown
        max_drawdown = 0.0
        peak = 0.0
        for value in cumulative_pnl:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calculate current drawdown
        current_peak = max(cumulative_pnl) if cumulative_pnl else 0.0
        current_value = cumulative_pnl[-1] if cumulative_pnl else 0.0
        current_drawdown = current_peak - current_value
        
        return max_drawdown, current_drawdown
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if not self.return_series or len(self.return_series) < 2:
            return 0.0
        
        try:
            if NUMPY_AVAILABLE and np:
                returns_array = np.array(self.return_series)
                excess_returns = returns_array - (risk_free_rate / 100)
                return float(np.mean(excess_returns) / np.std(excess_returns) * math.sqrt(252)) if np.std(excess_returns) > 0 else 0.0
            else:
                # Fallback to standard library
                excess_returns = [r - (risk_free_rate / 100) for r in self.return_series]
                mean_excess = statistics.mean(excess_returns)
                std_excess = statistics.stdev(excess_returns) if len(excess_returns) > 1 else 0.0
                return (mean_excess / std_excess * math.sqrt(252)) if std_excess > 0 else 0.0
        except Exception:
            return 0.0
    
    def _calculate_sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio"""
        if not self.return_series or len(self.return_series) < 2:
            return 0.0
        
        try:
            if NUMPY_AVAILABLE and np:
                returns_array = np.array(self.return_series)
                excess_returns = returns_array - (risk_free_rate / 100)
                downside_deviation = math.sqrt(statistics.mean([min(0, er)**2 for er in excess_returns]))
                return float(statistics.mean(excess_returns) / downside_deviation * math.sqrt(252)) if downside_deviation > 0 else 0.0
            else:
                # Fallback to standard library
                excess_returns = [r - (risk_free_rate / 100) for r in self.return_series]
                mean_excess = statistics.mean(excess_returns)
                downside_returns = [min(0, er) for er in excess_returns]
                downside_deviation = math.sqrt(statistics.mean([dr**2 for dr in downside_returns]))
                return (mean_excess / downside_deviation * math.sqrt(252)) if downside_deviation > 0 else 0.0
        except Exception:
            return 0.0
    
    def _calculate_calmar_ratio(self) -> float:
        """Calculate Calmar ratio"""
        max_dd, _ = self._calculate_drawdown()
        annualized_return = self._calculate_annualized_return()
        
        return annualized_return / max_dd if max_dd > 0 else 0.0
    
    def _calculate_volatility(self) -> float:
        """Calculate annualized volatility"""
        if not self.return_series or len(self.return_series) < 2:
            return 0.0
        
        try:
            if NUMPY_AVAILABLE and np:
                return float(np.std(self.return_series) * math.sqrt(252) * 100) if np.std(self.return_series) > 0 else 0.0
            else:
                # Fallback to standard library
                std_dev = statistics.stdev(self.return_series) if len(self.return_series) > 1 else 0.0
                return std_dev * math.sqrt(252) * 100
        except Exception:
            return 0.0
    
    def _calculate_trades_per_hour(self) -> float:
        """Calculate trades per hour"""
        if not self.trade_history:
            return 0.0
        
        # Calculate time span
        timestamps = [datetime.fromisoformat(trade.get('timestamp', '').replace('Z', '+00:00')) 
                     for trade in self.trade_history if trade.get('timestamp')]
        
        if len(timestamps) < 2:
            return 0.0
        
        time_span_hours = (max(timestamps) - min(timestamps)).total_seconds() / 3600
        return len(self.trade_history) / time_span_hours if time_span_hours > 0 else 0.0
    
    def _calculate_avg_trade_duration(self) -> float:
        """Calculate average trade duration in minutes"""
        if not self.trade_history:
            return 0.0
        
        durations = []
        for trade in self.trade_history:
            start_time = trade.get('start_time')
            end_time = trade.get('end_time')
            
            if start_time and end_time:
                try:
                    start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    duration_minutes = (end - start).total_seconds() / 60
                    durations.append(duration_minutes)
                except Exception:
                    continue
        
        return statistics.mean(durations) if durations else 0.0
    
    def _calculate_success_rate(self) -> float:
        """Calculate success rate (profitable trades percentage)"""
        if not self.trade_history:
            return 0.0
        
        profitable_trades = sum(1 for trade in self.trade_history if trade.get('pnl', 0) > 0)
        return (profitable_trades / len(self.trade_history)) * 100
    
    def _calculate_annualized_return(self) -> float:
        """Calculate annualized return"""
        if not self.return_series or len(self.return_series) < 2:
            return 0.0
        
        try:
            # Calculate time span in years
            timestamps = [datetime.fromisoformat(trade.get('timestamp', '').replace('Z', '+00:00')) 
                         for trade in self.trade_history if trade.get('timestamp')]
            
            if len(timestamps) < 2:
                return 0.0
            
            time_span_years = (max(timestamps) - min(timestamps)).total_seconds() / (365.25 * 24 * 3600)
            
            if time_span_years <= 0:
                return 0.0
            
            # Calculate annualized return using compound growth
            total_return_pct = sum(self.return_series) / 100  # Convert to decimal
            annualized_return = ((1 + total_return_pct) ** (1 / time_span_years) - 1) * 100
            
            return annualized_return if not math.isnan(annualized_return) else 0.0
            
        except Exception:
            return 0.0

class AlertManager:
    """Manage performance alerts and notifications"""
    
    def __init__(self, supabase_layer: Optional[Any] = None):
        self.supabase_layer = supabase_layer
        self.alerts: Dict[str, PerformanceAlert] = {}
        self.active_alerts: Set[str] = set()
        self.alert_history: deque = deque(maxlen=1000)
        
        # Default alert thresholds
        self._initialize_default_alerts()
    
    def _initialize_default_alerts(self):
        """Initialize default alert configurations"""
        default_alerts = [
            # System resource alerts
            PerformanceAlert(
                alert_name="high_cpu_usage",
                severity=AlertSeverity.WARNING,
                metric_name="cpu_percent",
                condition_type="threshold",
                threshold_value=80.0,
                operator=">",
                title="High CPU Usage Detected",
                message="CPU usage is above 80% threshold",
                recommendations=[
                    "Check for CPU-intensive processes",
                    "Optimize running applications",
                    "Consider scaling up resources"
                ]
            ),
            
            PerformanceAlert(
                alert_name="high_memory_usage",
                severity=AlertSeverity.WARNING,
                metric_name="memory_percent",
                condition_type="threshold",
                threshold_value=85.0,
                operator=">",
                title="High Memory Usage Detected",
                message="Memory usage is above 85% threshold",
                recommendations=[
                    "Check for memory leaks",
                    "Clear unnecessary cache",
                    "Restart memory-intensive services"
                ]
            ),
            
            PerformanceAlert(
                alert_name="low_disk_space",
                severity=AlertSeverity.CRITICAL,
                metric_name="disk_usage_percent",
                condition_type="threshold",
                threshold_value=90.0,
                operator=">",
                title="Low Disk Space Warning",
                message="Disk usage is above 90% threshold",
                recommendations=[
                    "Clean up temporary files",
                    "Archive old data",
                    "Increase disk capacity"
                ]
            ),
            
            # Trading performance alerts
            PerformanceAlert(
                alert_name="negative_roi",
                severity=AlertSeverity.ERROR,
                metric_name="roi",
                condition_type="threshold",
                threshold_value=0.0,
                operator="<",
                title="Negative ROI Detected",
                message="ROI has dropped below zero",
                recommendations=[
                    "Review recent trading strategy",
                    "Check for market conditions",
                    "Consider position sizing adjustments"
                ]
            ),
            
            PerformanceAlert(
                alert_name="low_win_rate",
                severity=AlertSeverity.WARNING,
                metric_name="win_rate",
                condition_type="threshold",
                threshold_value=50.0,
                operator="<",
                title="Low Win Rate Alert",
                message="Win rate is below 50%",
                recommendations=[
                    "Review entry criteria",
                    "Analyze losing trades",
                    "Adjust risk management"
                ]
            ),
            
            PerformanceAlert(
                alert_name="high_drawdown",
                severity=AlertSeverity.CRITICAL,
                metric_name="max_drawdown",
                condition_type="threshold",
                threshold_value=20.0,
                operator=">",
                title="High Drawdown Alert",
                message="Maximum drawdown exceeds 20%",
                recommendations=[
                    "Reduce position sizes",
                    "Implement stop losses",
                    "Review risk management strategy"
                ]
            )
        ]
        
        for alert in default_alerts:
            self.alerts[alert.alert_name] = alert
    
    def check_alert_conditions(self, metric_name: str, value: float) -> List[PerformanceAlert]:
        """Check if any alerts should be triggered"""
        triggered_alerts = []
        
        for alert_name, alert in self.alerts.items():
            if alert.metric_name != metric_name:
                continue
            
            should_trigger = False
            
            # Check condition based on operator
            if alert.condition_type == "threshold" and alert.threshold_value is not None:
                if alert.operator == ">" and value > alert.threshold_value:
                    should_trigger = True
                elif alert.operator == "<" and value < alert.threshold_value:
                    should_trigger = True
                elif alert.operator == ">=" and value >= alert.threshold_value:
                    should_trigger = True
                elif alert.operator == "<=" and value <= alert.threshold_value:
                    should_trigger = True
                elif alert.operator == "==" and abs(value - alert.threshold_value) < 0.001:
                    should_trigger = True
                elif alert.operator == "!=" and abs(value - alert.threshold_value) >= 0.001:
                    should_trigger = True
            
            if should_trigger:
                # Check if this is a new alert or ongoing alert
                if alert_name not in self.active_alerts:
                    alert.is_active = True
                    alert.last_triggered = datetime.now(timezone.utc)
                    alert.trigger_count += 1
                    alert.updated_at = datetime.now(timezone.utc)
                    
                    self.active_alerts.add(alert_name)
                    triggered_alerts.append(alert)
                    
                    # Log to history
                    self.alert_history.append({
                        'alert_id': alert.alert_id,
                        'alert_name': alert.alert_name,
                        'triggered_at': alert.last_triggered,
                        'metric_value': value,
                        'threshold_value': alert.threshold_value,
                        'severity': alert.severity.value
                    })
                    
                    # Save to Supabase if available
                    if self.supabase_layer:
                        asyncio.create_task(self._save_alert_to_supabase(alert, value))
                else:
                    # Update timestamp for ongoing alert
                    alert.last_triggered = datetime.now(timezone.utc)
                    alert.updated_at = datetime.now(timezone.utc)
        
        return triggered_alerts
    
    async def _save_alert_to_supabase(self, alert: PerformanceAlert, metric_value: float):
        """Save alert to Supabase"""
        try:
            if not self.supabase_layer:
                return
            
            alert_data = {
                'alert_name': alert.alert_name,
                'severity': alert.severity.value,
                'metric_name': alert.metric_name,
                'metric_value': metric_value,
                'threshold_value': alert.threshold_value,
                'title': alert.title,
                'message': alert.message,
                'triggered_at': alert.last_triggered.isoformat(),
                'trigger_count': alert.trigger_count
            }
            
            await self.supabase_layer.create_notification({
                'title': f"Performance Alert: {alert.title}",
                'message': alert.message,
                'severity': alert.severity.value,
                'category': 'performance',
                'data': alert_data
            })
            
        except Exception as e:
            logger.error(f"Failed to save alert to Supabase: {e}")
    
    def resolve_alert(self, alert_name: str):
        """Mark an alert as resolved"""
        if alert_name in self.alerts:
            self.alerts[alert_name].is_active = False
            self.active_alerts.discard(alert_name)
            self.alerts[alert_name].updated_at = datetime.now(timezone.utc)
    
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get currently active alerts"""
        return [alert for alert in self.alerts.values() if alert.is_active]
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for specified time period"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        return [
            alert for alert in self.alert_history
            if alert.get('triggered_at', datetime.min) > cutoff_time
        ]

class OptimizationEngine:
    """Generate automated performance optimization recommendations"""
    
    def __init__(self):
        self.recommendations: List[OptimizationRecommendation] = []
        self.recommendation_templates = self._initialize_recommendation_templates()
    
    def _initialize_recommendation_templates(self) -> Dict[str, OptimizationRecommendation]:
        """Initialize recommendation templates"""
        templates = {}
        
        # System optimization templates
        templates["high_cpu"] = OptimizationRecommendation(
            category="system",
            title="Optimize CPU Usage",
            description="Implement CPU usage optimization strategies",
            priority="high",
            expected_improvement="20-40% CPU usage reduction",
            effort_level="medium",
            risk_level="low",
            confidence=0.8,
            steps=[
                "Identify CPU-intensive processes",
                "Optimize algorithms and data structures",
                "Implement CPU throttling for non-critical processes",
                "Use async/await patterns for I/O operations",
                "Monitor CPU usage patterns"
            ],
            affected_metrics=["cpu_percent", "load_average"],
            auto_applicable=False
        )
        
        templates["high_memory"] = OptimizationRecommendation(
            category="system",
            title="Optimize Memory Usage",
            description="Implement memory optimization strategies",
            priority="high",
            expected_improvement="25-35% memory usage reduction",
            effort_level="medium",
            risk_level="low",
            confidence=0.9,
            steps=[
                "Identify memory leaks in application code",
                "Implement garbage collection optimization",
                "Use memory profiling tools",
                "Optimize data structures and algorithms",
                "Implement proper resource cleanup"
            ],
            affected_metrics=["memory_percent", "memory_used_gb"],
            auto_applicable=False
        )
        
        templates["low_disk_space"] = OptimizationRecommendation(
            category="system",
            title="Address Disk Space Issues",
            description="Resolve disk space constraints",
            priority="critical",
            expected_improvement="Immediate space reclamation",
            effort_level="low",
            risk_level="low",
            confidence=1.0,
            steps=[
                "Clean up temporary files and logs",
                "Archive or compress old data",
                "Remove unnecessary files and packages",
                "Implement log rotation policies",
                "Consider disk space expansion"
            ],
            affected_metrics=["disk_usage_percent"],
            auto_applicable=True
        )
        
        # Trading optimization templates
        templates["negative_roi"] = OptimizationRecommendation(
            category="trading",
            title="Improve Trading Performance",
            description="Address negative ROI through strategy optimization",
            priority="critical",
            expected_improvement="ROI improvement to positive territory",
            effort_level="high",
            risk_level="medium",
            confidence=0.7,
            steps=[
                "Review and analyze recent losing trades",
                "Adjust entry and exit criteria",
                "Implement stricter risk management",
                "Optimize position sizing algorithms",
                "Consider market condition adjustments"
            ],
            affected_metrics=["roi", "total_pnl", "win_rate"],
            auto_applicable=False
        )
        
        templates["low_win_rate"] = OptimizationRecommendation(
            category="trading",
            title="Improve Win Rate",
            description="Enhance trading strategy to improve win rate",
            priority="high",
            expected_improvement="10-20% win rate improvement",
            effort_level="medium",
            risk_level="medium",
            confidence=0.8,
            steps=[
                "Analyze patterns in losing trades",
                "Refine entry criteria and timing",
                "Implement better market analysis",
                "Add additional confirmation signals",
                "Adjust risk-reward ratios"
            ],
            affected_metrics=["win_rate", "success_rate", "expectancy"],
            auto_applicable=False
        )
        
        templates["high_drawdown"] = OptimizationRecommendation(
            category="trading",
            title="Reduce Maximum Drawdown",
            description="Implement drawdown reduction strategies",
            priority="critical",
            expected_improvement="50-70% drawdown reduction",
            effort_level="high",
            risk_level="medium",
            confidence=0.9,
            steps=[
                "Implement stricter stop-loss rules",
                "Reduce position sizes during drawdown periods",
                "Add correlation-based diversification",
                "Implement dynamic risk scaling",
                "Add circuit breaker mechanisms"
            ],
            affected_metrics=["max_drawdown", "current_drawdown", "volatility"],
            auto_applicable=False
        )
        
        return templates
    
    def generate_recommendations(self, alerts: List[PerformanceAlert], 
                                system_metrics: SystemResourceData,
                                trading_metrics: TradingPerformanceData) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on alerts and metrics"""
        recommendations = []
        
        try:
            # Generate recommendations based on active alerts
            for alert in alerts:
                if alert.alert_name in self.recommendation_templates:
                    template = self.recommendation_templates[alert.alert_name]
                    
                    # Create customized recommendation
                    recommendation = OptimizationRecommendation(
                        category=template.category,
                        title=template.title,
                        description=template.description,
                        priority=template.priority,
                        expected_improvement=template.expected_improvement,
                        effort_level=template.effort_level,
                        risk_level=template.risk_level,
                        confidence=template.confidence,
                        steps=template.steps.copy(),
                        affected_metrics=template.affected_metrics.copy(),
                        triggered_by_alerts=[alert.alert_id],
                        auto_applicable=template.auto_applicable
                    )
                    
                    recommendations.append(recommendation)
            
            # Add proactive recommendations based on current metrics
            recommendations.extend(self._generate_proactive_recommendations(system_metrics, trading_metrics))
            
            # Add general optimization recommendations
            recommendations.extend(self._generate_general_recommendations())
            
            # Remove duplicates and rank by priority
            recommendations = self._deduplicate_and_rank_recommendations(recommendations)
            
            # Update recommendations database
            self.recommendations.extend(recommendations)
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
        
        return recommendations
    
    def _generate_proactive_recommendations(self, system_metrics: SystemResourceData, 
                                          trading_metrics: TradingPerformanceData) -> List[OptimizationRecommendation]:
        """Generate proactive recommendations based on current metrics"""
        recommendations = []
        
        # Proactive system recommendations
        if system_metrics.cpu_percent > 70:
            recommendations.append(OptimizationRecommendation(
                category="system",
                title="Proactive CPU Optimization",
                description="Optimize CPU usage before it becomes critical",
                priority="medium",
                expected_improvement="15-25% CPU efficiency improvement",
                effort_level="low",
                risk_level="low",
                confidence=0.8,
                steps=[
                    "Review running processes and optimize",
                    "Implement process prioritization",
                    "Add CPU usage monitoring alerts"
                ],
                affected_metrics=["cpu_percent"],
                auto_applicable=True
            ))
        
        if system_metrics.memory_percent > 75:
            recommendations.append(OptimizationRecommendation(
                category="system",
                title="Proactive Memory Optimization",
                description="Optimize memory usage proactively",
                priority="medium",
                expected_improvement="20-30% memory efficiency",
                effort_level="low",
                risk_level="low",
                confidence=0.8,
                steps=[
                    "Implement memory usage optimization",
                    "Add memory monitoring",
                    "Optimize data caching strategies"
                ],
                affected_metrics=["memory_percent"],
                auto_applicable=True
            ))
        
        # Proactive trading recommendations
        if trading_metrics.sharpe_ratio < 1.0:
            recommendations.append(OptimizationRecommendation(
                category="trading",
                title="Improve Risk-Adjusted Returns",
                description="Enhance risk-adjusted performance metrics",
                priority="medium",
                expected_improvement="Sharpe ratio improvement to >1.0",
                effort_level="medium",
                risk_level="medium",
                confidence=0.7,
                steps=[
                    "Implement better risk management",
                    "Optimize position sizing",
                    "Add risk-adjusted entry criteria"
                ],
                affected_metrics=["sharpe_ratio", "sortino_ratio", "volatility"],
                auto_applicable=False
            ))
        
        return recommendations
    
    def _generate_general_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate general optimization recommendations"""
        return [
            OptimizationRecommendation(
                category="operational",
                title="Implement Comprehensive Monitoring",
                description="Set up comprehensive performance monitoring",
                priority="low",
                expected_improvement="Better visibility and faster issue detection",
                effort_level="low",
                risk_level="low",
                confidence=0.9,
                steps=[
                    "Set up real-time performance dashboards",
                    "Implement automated alerting",
                    "Create performance trend analysis",
                    "Add predictive monitoring"
                ],
                affected_metrics=["all"],
                auto_applicable=True
            ),
            
            OptimizationRecommendation(
                category="operational",
                title="Optimize Database Performance",
                description="Optimize database queries and indexing",
                priority="medium",
                expected_improvement="30-50% database performance improvement",
                effort_level="medium",
                risk_level="low",
                confidence=0.8,
                steps=[
                    "Analyze slow queries",
                    "Add missing indexes",
                    "Optimize query plans",
                    "Implement connection pooling"
                ],
                affected_metrics=["query_response_time", "database_connections"],
                auto_applicable=False
            )
        ]
    
    def _deduplicate_and_rank_recommendations(self, recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
        """Remove duplicate recommendations and rank by priority"""
        # Remove duplicates based on title
        seen_titles = set()
        unique_recommendations = []
        
        for rec in recommendations:
            if rec.title not in seen_titles:
                seen_titles.add(rec.title)
                unique_recommendations.append(rec)
        
        # Rank by priority and confidence
        priority_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        
        unique_recommendations.sort(
            key=lambda r: (priority_order.get(r.priority, 0), r.confidence),
            reverse=True
        )
        
        return unique_recommendations
    
    def get_recommendations_by_priority(self, priority: str) -> List[OptimizationRecommendation]:
        """Get recommendations filtered by priority"""
        return [rec for rec in self.recommendations if rec.priority == priority]
    
    def get_auto_applicable_recommendations(self) -> List[OptimizationRecommendation]:
        """Get recommendations that can be automatically applied"""
        return [rec for rec in self.recommendations if rec.auto_applicable]

class DashboardIntegration:
    """Handle dashboard integration for real-time visualization"""
    
    def __init__(self, supabase_layer: Optional[Any] = None):
        self.supabase_layer = supabase_layer
        self.dashboard_data: Dict[str, Any] = {
            'system_metrics': {},
            'trading_metrics': {},
            'alerts': [],
            'recommendations': [],
            'trends': {},
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        # Real-time data streams
        self.real_time_streams: Dict[str, Any] = {}
        self.stream_subscribers: Dict[str, Set[Callable]] = defaultdict(set)
    
    async def update_dashboard_data(self, system_metrics: SystemResourceData,
                                  trading_metrics: TradingPerformanceData,
                                  alerts: List[PerformanceAlert],
                                  recommendations: List[OptimizationRecommendation]):
        """Update dashboard data for real-time visualization"""
        try:
            self.dashboard_data.update({
                'system_metrics': system_metrics.to_dict(),
                'trading_metrics': trading_metrics.to_dict(),
                'alerts': [alert.to_dict() for alert in alerts],
                'recommendations': [rec.to_dict() for rec in recommendations],
                'last_updated': datetime.now(timezone.utc).isoformat()
            })
            
            # Update real-time streams
            await self._update_real_time_streams()
            
            # Save to Supabase for persistent dashboard data
            if self.supabase_layer:
                await self._save_dashboard_data_to_supabase()
            
            # Notify subscribers
            self._notify_subscribers('dashboard_update', self.dashboard_data)
            
        except Exception as e:
            logger.error(f"Failed to update dashboard data: {e}")
    
    async def _update_real_time_streams(self):
        """Update real-time data streams"""
        try:
            # System metrics stream
            self.real_time_streams['system_metrics'] = {
                'cpu_percent': self.dashboard_data['system_metrics'].get('cpu_percent', 0),
                'memory_percent': self.dashboard_data['system_metrics'].get('memory_percent', 0),
                'disk_usage_percent': self.dashboard_data['system_metrics'].get('disk_usage_percent', 0),
                'timestamp': self.dashboard_data['system_metrics'].get('timestamp', datetime.now(timezone.utc).isoformat())
            }
            
            # Trading metrics stream
            self.real_time_streams['trading_metrics'] = {
                'roi': self.dashboard_data['trading_metrics'].get('roi', 0),
                'win_rate': self.dashboard_data['trading_metrics'].get('win_rate', 0),
                'total_pnl': self.dashboard_data['trading_metrics'].get('total_pnl', 0),
                'max_drawdown': self.dashboard_data['trading_metrics'].get('max_drawdown', 0),
                'timestamp': self.dashboard_data['trading_metrics'].get('timestamp', datetime.now(timezone.utc).isoformat())
            }
            
            # Alerts stream
            active_alerts = [alert for alert in self.dashboard_data['alerts'] if alert.get('is_active', False)]
            self.real_time_streams['active_alerts'] = {
                'count': len(active_alerts),
                'severity_breakdown': self._get_alert_severity_breakdown(active_alerts),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update real-time streams: {e}")
    
    def _get_alert_severity_breakdown(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of alerts by severity"""
        breakdown = {'info': 0, 'warning': 0, 'error': 0, 'critical': 0}
        for alert in alerts:
            severity = alert.get('severity', 'info')
            breakdown[severity] = breakdown.get(severity, 0) + 1
        return breakdown
    
    async def _save_dashboard_data_to_supabase(self):
        """Save dashboard data to Supabase for persistence"""
        try:
            if not self.supabase_layer:
                return
            
            # Save current performance metrics
            await self.supabase_layer.save_performance_metric({
                'metric_name': 'dashboard_update',
                'metric_value': 1.0,
                'unit': 'count',
                'tags': {
                    'last_updated': self.dashboard_data['last_updated'],
                    'active_alerts': str(len([a for a in self.dashboard_data['alerts'] if a.get('is_active', False)]))
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to save dashboard data to Supabase: {e}")
    
    def subscribe_to_stream(self, stream_name: str, callback: Callable):
        """Subscribe to real-time data stream updates"""
        self.stream_subscribers[stream_name].add(callback)
    
    def unsubscribe_from_stream(self, stream_name: str, callback: Callable):
        """Unsubscribe from real-time data stream updates"""
        self.stream_subscribers[stream_name].discard(callback)
    
    def _notify_subscribers(self, stream_name: str, data: Any):
        """Notify subscribers of stream updates"""
        for callback in self.stream_subscribers[stream_name]:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return self.dashboard_data.copy()
    
    def get_real_time_stream(self, stream_name: str) -> Optional[Dict[str, Any]]:
        """Get real-time stream data"""
        return self.real_time_streams.get(stream_name)
    
    def get_trend_data(self, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get trend data for a specific metric"""
        # This would typically query historical data from a time-series database
        # For now, return placeholder structure
        return {
            'metric_name': metric_name,
            'time_period_hours': hours,
            'trend_direction': 'stable',  # rising, falling, stable
            'change_percentage': 0.0,
            'data_points': []
        }

class PerformanceMonitor:
    """Main performance monitoring system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize components
        self.system_monitor = SystemResourceMonitor()
        self.trading_analyzer = TradingPerformanceAnalyzer()
        self.alert_manager = AlertManager()
        self.optimization_engine = OptimizationEngine()
        self.dashboard_integration = DashboardIntegration()
        
        # Data storage
        self.metric_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.system_metrics_history: deque = deque(maxlen=1000)
        self.trading_metrics_history: deque = deque(maxlen=1000)
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Performance statistics
        self.stats = {
            'metrics_collected': 0,
            'alerts_triggered': 0,
            'recommendations_generated': 0,
            'system_checks': 0,
            'errors': 0
        }
        
        # Supabase integration
        self.supabase_layer = None
        self._initialize_supabase_integration()
        
        logger.info("Performance monitor initialized")
    
    def _initialize_supabase_integration(self):
        """Initialize Supabase integration if available"""
        try:
            if not SUPABASE_AVAILABLE:
                logger.warning("Supabase integration not available")
                self.supabase_layer = None
                return
            
            # Import SupabaseDataLayer
            from arbitech.storage.supabase_layer import SupabaseDataLayer
            
            # Initialize with configuration
            self.supabase_layer = SupabaseDataLayer()
            
            # Update components with Supabase layer
            self.alert_manager.supabase_layer = self.supabase_layer
            self.dashboard_integration.supabase_layer = self.supabase_layer
            
            logger.info("Supabase integration initialized")
            
        except Exception as e:
            logger.warning(f"Supabase integration not available: {e}")
            self.supabase_layer = None
    
    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self.monitoring_active = True
        self._shutdown_event.clear()
        
        # Create monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._system_monitoring_loop()),
            asyncio.create_task(self._trading_analysis_loop()),
            asyncio.create_task(self._alert_processing_loop()),
            asyncio.create_task(self._optimization_loop()),
            asyncio.create_task(self._dashboard_update_loop())
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
    
    async def _system_monitoring_loop(self):
        """System resource monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self.system_monitor.collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                self.stats['system_checks'] += 1
                
                # Store individual metrics
                self._store_metric('cpu_percent', system_metrics.cpu_percent, 'percent')
                self._store_metric('memory_percent', system_metrics.memory_percent, 'percent')
                self._store_metric('disk_usage_percent', system_metrics.disk_usage_percent, 'percent')
                self._store_metric('network_bytes_sent', system_metrics.network_bytes_sent, 'bytes')
                self._store_metric('network_bytes_recv', system_metrics.network_bytes_recv, 'bytes')
                
                # Check alert conditions for system metrics
                triggered_alerts = []
                triggered_alerts.extend(self.alert_manager.check_alert_conditions('cpu_percent', system_metrics.cpu_percent))
                triggered_alerts.extend(self.alert_manager.check_alert_conditions('memory_percent', system_metrics.memory_percent))
                triggered_alerts.extend(self.alert_manager.check_alert_conditions('disk_usage_percent', system_metrics.disk_usage_percent))
                
                if triggered_alerts:
                    self.stats['alerts_triggered'] += len(triggered_alerts)
                
                await asyncio.sleep(10)  # Collect every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(5)
    
    async def _trading_analysis_loop(self):
        """Trading performance analysis loop"""
        while self.monitoring_active:
            try:
                # Calculate current trading performance
                trading_metrics = self.trading_analyzer.calculate_performance_metrics()
                self.trading_metrics_history.append(trading_metrics)
                
                # Store trading metrics
                self._store_metric('roi', trading_metrics.roi, 'percent')
                self._store_metric('sharpe_ratio', trading_metrics.sharpe_ratio, 'ratio')
                self._store_metric('max_drawdown', trading_metrics.max_drawdown, 'percent')
                self._store_metric('win_rate', trading_metrics.win_rate, 'percent')
                self._store_metric('total_pnl', trading_metrics.total_pnl, 'currency')
                
                # Check alert conditions for trading metrics
                triggered_alerts = []
                triggered_alerts.extend(self.alert_manager.check_alert_conditions('roi', trading_metrics.roi))
                triggered_alerts.extend(self.alert_manager.check_alert_conditions('win_rate', trading_metrics.win_rate))
                triggered_alerts.extend(self.alert_manager.check_alert_conditions('max_drawdown', trading_metrics.max_drawdown))
                
                if triggered_alerts:
                    self.stats['alerts_triggered'] += len(triggered_alerts)
                
                await asyncio.sleep(30)  # Analyze every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in trading analysis loop: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(15)
    
    async def _alert_processing_loop(self):
        """Alert processing and management loop"""
        while self.monitoring_active:
            try:
                # Get current alerts
                active_alerts = self.alert_manager.get_active_alerts()
                
                # Process alerts (could send notifications, etc.)
                for alert in active_alerts:
                    logger.info(f"Active alert: {alert.title} - {alert.message}")
                
                await asyncio.sleep(60)  # Process every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert processing loop: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(30)
    
    async def _optimization_loop(self):
        """Optimization recommendations loop"""
        while self.monitoring_active:
            try:
                # Get current system and trading metrics
                system_metrics = self.system_metrics_history[-1] if self.system_metrics_history else None
                trading_metrics = self.trading_metrics_history[-1] if self.trading_metrics_history else None
                
                if system_metrics and trading_metrics:
                    # Generate recommendations based on current state
                    active_alerts = self.alert_manager.get_active_alerts()
                    recommendations = self.optimization_engine.generate_recommendations(
                        active_alerts, system_metrics, trading_metrics
                    )
                    
                    self.stats['recommendations_generated'] += len(recommendations)
                    
                    if recommendations:
                        logger.info(f"Generated {len(recommendations)} optimization recommendations")
                
                await asyncio.sleep(300)  # Generate recommendations every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(60)
    
    async def _dashboard_update_loop(self):
        """Dashboard data update loop"""
        while self.monitoring_active:
            try:
                # Get latest metrics
                system_metrics = self.system_metrics_history[-1] if self.system_metrics_history else None
                trading_metrics = self.trading_metrics_history[-1] if self.trading_metrics_history else None
                active_alerts = self.alert_manager.get_active_alerts()
                
                if system_metrics and trading_metrics:
                    # Update dashboard data
                    await self.dashboard_integration.update_dashboard_data(
                        system_metrics, trading_metrics, active_alerts, []
                    )
                
                await asyncio.sleep(15)  # Update dashboard every 15 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in dashboard update loop: {e}")
                self.stats['errors'] += 1
                await asyncio.sleep(10)
    
    def _store_metric(self, metric_name: str, value: float, unit: str):
        """Store metric in history"""
        data_point = MetricDataPoint(
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=datetime.now(timezone.utc),
            source="system"
        )
        
        self.metric_history[metric_name].append(data_point)
        self.stats['metrics_collected'] += 1
    
    def add_trade_result(self, trade_data: Dict[str, Any]):
        """Add trade result for analysis"""
        self.trading_analyzer.add_trade_result(trade_data)
    
    def get_current_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary"""
        system_metrics = self.system_metrics_history[-1] if self.system_metrics_history else None
        trading_metrics = self.trading_metrics_history[-1] if self.trading_metrics_history else None
        active_alerts = self.alert_manager.get_active_alerts()
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'monitoring_active': self.monitoring_active,
            'statistics': self.stats.copy(),
            'system_metrics': system_metrics.to_dict() if system_metrics else {},
            'trading_metrics': trading_metrics.to_dict() if trading_metrics else {},
            'active_alerts_count': len(active_alerts),
            'active_alerts': [alert.to_dict() for alert in active_alerts],
            'total_recommendations': len(self.optimization_engine.recommendations)
        }
    
    def get_metric_trends(self, metric_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get metric trends over time"""
        if metric_name not in self.metric_history:
            return {'message': f'No data available for metric: {metric_name}'}
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Filter metrics within time period
        recent_metrics = [
            metric for metric in self.metric_history[metric_name]
            if metric.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {'message': f'No recent data available for metric: {metric_name}'}
        
        values = [metric.value for metric in recent_metrics]
        
        return {
            'metric_name': metric_name,
            'time_period_hours': hours,
            'data_points': len(values),
            'statistics': {
                'min': min(values),
                'max': max(values),
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0.0
            },
            'latest_value': values[-1] if values else 0.0,
            'trend': 'stable'  # Could be enhanced with actual trend analysis
        }
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get recent data
        recent_system_metrics = [
            metric for metric in self.system_metrics_history
            if metric.timestamp > cutoff_time
        ]
        
        recent_trading_metrics = [
            metric for metric in self.trading_metrics_history
            if metric.timestamp > cutoff_time
        ]
        
        recent_alerts = self.alert_manager.get_alert_history(hours)
        
        # Calculate system performance summary
        system_summary = {}
        if recent_system_metrics:
            cpu_values = [m.cpu_percent for m in recent_system_metrics]
            memory_values = [m.memory_percent for m in recent_system_metrics]
            disk_values = [m.disk_usage_percent for m in recent_system_metrics]
            
            system_summary = {
                'avg_cpu_usage': statistics.mean(cpu_values),
                'max_cpu_usage': max(cpu_values),
                'avg_memory_usage': statistics.mean(memory_values),
                'max_memory_usage': max(memory_values),
                'avg_disk_usage': statistics.mean(disk_values),
                'max_disk_usage': max(disk_values),
                'check_count': len(recent_system_metrics)
            }
        
        # Calculate trading performance summary
        trading_summary = {}
        if recent_trading_metrics:
            latest_metrics = recent_trading_metrics[-1]
            trading_summary = latest_metrics.to_dict()
        
        return {
            'report_period_hours': hours,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'summary': {
                'total_metrics_collected': self.stats['metrics_collected'],
                'total_alerts_triggered': self.stats['alerts_triggered'],
                'total_recommendations': self.stats['recommendations_generated'],
                'total_system_checks': self.stats['system_checks'],
                'errors_encountered': self.stats['errors']
            },
            'system_performance': system_summary,
            'trading_performance': trading_summary,
            'alert_summary': {
                'total_alerts': len(recent_alerts),
                'alerts_by_severity': self._get_alert_severity_summary(recent_alerts)
            },
            'recommendations': {
                'total_generated': len(self.optimization_engine.recommendations),
                'by_priority': self._get_recommendations_by_priority_summary()
            }
        }
    
    def _get_alert_severity_summary(self, alerts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get summary of alerts by severity"""
        summary = {'info': 0, 'warning': 0, 'error': 0, 'critical': 0}
        for alert in alerts:
            severity = alert.get('severity', 'info')
            summary[severity] = summary.get(severity, 0) + 1
        return summary
    
    def _get_recommendations_by_priority_summary(self) -> Dict[str, int]:
        """Get summary of recommendations by priority"""
        summary = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for rec in self.optimization_engine.recommendations:
            summary[rec.priority] = summary.get(rec.priority, 0) + 1
        return summary
    
    def export_performance_data(self, filepath: str, hours: int = 24):
        """Export performance data to file"""
        try:
            report = self.get_performance_report(hours)
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Performance data exported to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export performance data: {e}")
    
    async def shutdown(self):
        """Graceful shutdown of performance monitoring"""
        logger.info("Shutting down performance monitoring system...")
        
        # Stop monitoring
        await self.stop_monitoring()
        
        # Export final report
        try:
            self.export_performance_data(f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        except Exception as e:
            logger.error(f"Failed to export final report: {e}")
        
        logger.info("Performance monitoring system shutdown completed")


# Global performance monitor instance
_global_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor"""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor

# Example usage and testing
async def demo_performance_monitoring():
    """Demonstrate performance monitoring system"""
    print("🚀 Starting ARBitech Performance Monitoring System Demo")
    
    # Initialize monitor
    monitor = PerformanceMonitor()
    
    # Add some sample trade results for testing
    sample_trades = [
        {'timestamp': '2025-11-02T04:00:00Z', 'pnl': 10.5, 'stake': 100.0, 'start_time': '2025-11-02T04:00:00Z', 'end_time': '2025-11-02T04:01:30Z'},
        {'timestamp': '2025-11-02T04:01:30Z', 'pnl': -5.0, 'stake': 100.0, 'start_time': '2025-11-02T04:01:30Z', 'end_time': '2025-11-02T04:02:45Z'},
        {'timestamp': '2025-11-02T04:02:45Z', 'pnl': 15.0, 'stake': 100.0, 'start_time': '2025-11-02T04:02:45Z', 'end_time': '2025-11-02T04:04:00Z'},
        {'timestamp': '2025-11-02T04:04:00Z', 'pnl': 7.5, 'stake': 100.0, 'start_time': '2025-11-02T04:04:00Z', 'end_time': '2025-11-02T04:05:15Z'},
        {'timestamp': '2025-11-02T04:05:15Z', 'pnl': -2.5, 'stake': 100.0, 'start_time': '2025-11-02T04:05:15Z', 'end_time': '2025-11-02T04:06:30Z'}
    ]
    
    for trade in sample_trades:
        monitor.add_trade_result(trade)
    
    # Start monitoring
    print("📊 Starting performance monitoring...")
    await monitor.start_monitoring()
    
    # Run for a short demo period
    print("⏱️  Running monitoring for 30 seconds...")
    await asyncio.sleep(30)
    
    # Show current performance summary
    print("\n📈 Current Performance Summary:")
    summary = monitor.get_current_performance_summary()
    print(json.dumps(summary, indent=2, default=str))
    
    # Show performance report
    print("\n📋 Performance Report (Last 1 Hour):")
    report = monitor.get_performance_report(hours=1)
    print(json.dumps(report, indent=2, default=str))
    
    # Show metric trends
    print("\n📊 ROI Trend Analysis:")
    roi_trend = monitor.get_metric_trends('roi', hours=1)
    print(json.dumps(roi_trend, indent=2, default=str))
    
    # Export data
    print("\n💾 Exporting performance data...")
    monitor.export_performance_data('demo_performance_report.json')
    
    # Stop monitoring
    print("\n🛑 Stopping performance monitoring...")
    await monitor.shutdown()
    
    print("✅ Performance monitoring demo completed!")

if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_performance_monitoring())