"""
Comprehensive Trade Result Logging System for Human-in-the-Loop (HITL) Arbitrage Trading

This module provides a complete trade result logging system that tracks human decisions,
execution outcomes, performance analytics, and user interaction patterns. It integrates
with Phase 4 risk metrics and Phase 5 execution tracking to provide comprehensive
audit trails and real-time dashboards.

Features:
- Log all human decisions (approve/reject/timeout) with full context
- Track execution results and profit/loss outcomes
- Performance analytics and success rate tracking
- Detailed audit trails for compliance
- User interaction patterns and approval behavior analysis
- Real-time performance dashboards and reporting
- Integration with risk metrics and execution tracking
- Structured logging with JSON formatting and export capabilities
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import threading
import statistics
import numpy as np
from contextlib import asynccontextmanager

# Import existing ARBitech infrastructure
try:
    from ..storage.audit_logger import (
        AuditLogger, TradeExecutionLog, SecurityEventLog, 
        LogLevel, EventType, AuditEntry, get_audit_logger
    )
    from ..risk.risk_analyzer import RiskAlert, AlertSeverity, AlertType
    from ..automation.execution_tracker import (
        TrackingLevel, EventType as ExecEventType, AlertSeverity as ExecAlertSeverity
    )
    AUDIT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some ARBitech modules not available: {e}")
    # Define minimal fallback classes if imports fail
    AUDIT_AVAILABLE = False
    
    class AuditLogger:
        def __init__(self, *args, **kwargs):
            pass
        def log_user_action(self, *args, **kwargs):
            pass
        def log_system_error(self, *args, **kwargs):
            pass
        def _append_to_file(self, *args, **kwargs):
            pass
    
    class TradeExecutionLog:
        def __init__(self, *args, **kwargs):
            pass
    
    class SecurityEventLog:
        def __init__(self, *args, **kwargs):
            pass
    
    class LogLevel:
        INFO = "INFO"
        WARNING = "WARNING"
        ERROR = "ERROR"
        CRITICAL = "CRITICAL"
    
    class EventType:
        TRADE_EXECUTION = "TRADE_EXECUTION"
        USER_ACTION = "USER_ACTION"
    
    class AuditEntry:
        def __init__(self, *args, **kwargs):
            pass
        def to_dict(self):
            return {}
    
    def get_audit_logger(*args, **kwargs):
        return AuditLogger()
    
    class RiskAlert:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class AlertSeverity:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    class AlertType:
        MARKET_VOLATILITY_SPIKE = "market_volatility_spike"
        EXECUTION_FAILURE_RISK = "execution_failure_risk"
        PERFORMANCE_DEGRADATION = "performance_degradation"
    
    class TrackingLevel:
        BASIC = "basic"
        DETAILED = "detailed"
        COMPREHENSIVE = "comprehensive"
        VERBOSE = "verbose"
    
    class ExecEventType:
        EXECUTION_STARTED = "execution_started"
        EXECUTION_COMPLETED = "execution_completed"
    
    class ExecAlertSeverity:
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"


class DecisionType(Enum):
    """Types of human decisions."""
    APPROVE = "approve"
    REJECT = "reject"
    TIMEOUT = "timeout"
    MANUAL_OVERRIDE = "manual_override"


class TradeOutcome(Enum):
    """Types of trade outcomes."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    PENDING = "pending"


class InteractionPattern(Enum):
    """Types of user interaction patterns."""
    QUICK_APPROVAL = "quick_approval"
    THOROUGH_REVIEW = "thorough_review"
    PATTERN_REJECTION = "pattern_rejection"
    BATCH_PROCESSING = "batch_processing"
    MANUAL_INTERVENTION = "manual_intervention"
    SYSTEM_MONITORING = "system_monitoring"


@dataclass
class HumanDecision:
    """Records a human decision on a trade opportunity."""
    decision_id: str
    opportunity_id: str
    decision_type: DecisionType
    timestamp: datetime
    user_id: str
    session_id: str
    reasoning: Optional[str] = None
    confidence_score: Optional[float] = None
    time_to_decision_ms: Optional[float] = None
    risk_level: Optional[str] = None
    expected_profit: Optional[float] = None
    max_stake: Optional[float] = None
    bookmaker_count: Optional[int] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    ui_interactions: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'opportunity_id': self.opportunity_id,
            'decision_type': self.decision_type.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'session_id': self.session_id,
            'reasoning': self.reasoning,
            'confidence_score': self.confidence_score,
            'time_to_decision_ms': self.time_to_decision_ms,
            'risk_level': self.risk_level,
            'expected_profit': self.expected_profit,
            'max_stake': self.max_stake,
            'bookmaker_count': self.bookmaker_count,
            'context_data': self.context_data,
            'ui_interactions': self.ui_interactions
        }


@dataclass
class TradeResult:
    """Records the actual outcome of a trade execution."""
    result_id: str
    decision_id: str
    opportunity_id: str
    execution_start: datetime
    execution_end: Optional[datetime] = None
    
    # Outcome tracking
    outcome: TradeOutcome = TradeOutcome.PENDING
    total_profit_loss: Optional[float] = None
    net_profit_loss: Optional[float] = None
    commission_costs: Optional[float] = None
    slippage: Optional[float] = None
    
    # Execution metrics
    legs_completed: int = 0
    legs_total: int = 0
    legs_failed: List[str] = field(default_factory=list)
    execution_time_ms: Optional[float] = None
    
    # Risk metrics
    max_drawdown: Optional[float] = None
    realized_risk: Optional[float] = None
    risk_adjusted_return: Optional[float] = None
    
    # Performance tracking
    expected_vs_actual_profit: Optional[float] = None
    efficiency_score: Optional[float] = None
    
    # Error tracking
    error_messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Additional context
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    system_performance: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'decision_id': self.decision_id,
            'opportunity_id': self.opportunity_id,
            'execution_start': self.execution_start.isoformat(),
            'execution_end': self.execution_end.isoformat() if self.execution_end else None,
            'outcome': self.outcome.value,
            'total_profit_loss': self.total_profit_loss,
            'net_profit_loss': self.net_profit_loss,
            'commission_costs': self.commission_costs,
            'slippage': self.slippage,
            'legs_completed': self.legs_completed,
            'legs_total': self.legs_total,
            'legs_failed': self.legs_failed,
            'execution_time_ms': self.execution_time_ms,
            'max_drawdown': self.max_drawdown,
            'realized_risk': self.realized_risk,
            'risk_adjusted_return': self.risk_adjusted_return,
            'expected_vs_actual_profit': self.expected_vs_actual_profit,
            'efficiency_score': self.efficiency_score,
            'error_messages': self.error_messages,
            'warnings': self.warnings,
            'market_conditions': self.market_conditions,
            'system_performance': self.system_performance
        }


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics for analysis."""
    period_start: datetime
    period_end: datetime
    user_id: str
    
    # Decision metrics
    total_decisions: int = 0
    approval_rate: float = 0.0
    rejection_rate: float = 0.0
    timeout_rate: float = 0.0
    avg_decision_time_ms: float = 0.0
    
    # Outcome metrics
    successful_trades: int = 0
    failed_trades: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    net_profit: float = 0.0
    success_rate: float = 0.0
    roi: float = 0.0
    
    # Risk metrics
    avg_risk_level: float = 0.0
    max_single_loss: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    
    # Efficiency metrics
    trades_per_hour: float = 0.0
    avg_execution_time_ms: float = 0.0
    system_uptime: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'user_id': self.user_id,
            'total_decisions': self.total_decisions,
            'approval_rate': self.approval_rate,
            'rejection_rate': self.rejection_rate,
            'timeout_rate': self.timeout_rate,
            'avg_decision_time_ms': self.avg_decision_time_ms,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'net_profit': self.net_profit,
            'success_rate': self.success_rate,
            'roi': self.roi,
            'avg_risk_level': self.avg_risk_level,
            'max_single_loss': self.max_single_loss,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'trades_per_hour': self.trades_per_hour,
            'avg_execution_time_ms': self.avg_execution_time_ms,
            'system_uptime': self.system_uptime
        }


@dataclass
class UserInteractionPattern:
    """Records user interaction patterns for behavior analysis."""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    pattern_type: Optional[InteractionPattern] = None
    
    # Interaction metrics
    total_decisions: int = 0
    quick_approvals: int = 0
    detailed_reviews: int = 0
    pattern_rejections: int = 0
    batch_operations: int = 0
    
    # Time-based patterns
    peak_activity_hours: List[int] = field(default_factory=list)
    avg_session_duration_minutes: float = 0.0
    break_frequency: float = 0.0
    
    # Behavioral metrics
    consistency_score: Optional[float] = None
    learning_curve_indicator: Optional[float] = None
    risk_appetite_evolution: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'pattern_type': self.pattern_type.value if self.pattern_type else None,
            'total_decisions': self.total_decisions,
            'quick_approvals': self.quick_approvals,
            'detailed_reviews': self.detailed_reviews,
            'pattern_rejections': self.pattern_rejections,
            'batch_operations': self.batch_operations,
            'peak_activity_hours': self.peak_activity_hours,
            'avg_session_duration_minutes': self.avg_session_duration_minutes,
            'break_frequency': self.break_frequency,
            'consistency_score': self.consistency_score,
            'learning_curve_indicator': self.learning_curve_indicator,
            'risk_appetite_evolution': self.risk_appetite_evolution
        }


class ResultLogger:
    """
    Comprehensive Trade Result Logging System
    
    Provides complete logging and analytics for HITL arbitrage trading including:
    - Human decision tracking and context logging
    - Trade outcome and P&L tracking
    - Performance analytics and user behavior analysis
    - Real-time dashboards and reporting
    - Audit trails for compliance
    - Integration with risk and execution systems
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the result logger."""
        self.config = config or self._get_default_config()
        self.logs_dir = Path(self.config.get('logs_directory', '/workspace/arbitech/logs'))
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage
        self._initialize_storage()
        
        # Performance tracking
        self._performance_cache = {}
        self._lock = threading.RLock()
        
        # Integration with existing systems
        self._audit_logger = None
        self._execution_tracker = None
        self._risk_analyzer = None
        
        # Analytics engine
        self._analytics_engine = AnalyticsEngine(self)
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'logs_directory': '/workspace/arbitech/logs',
            'hitl_directory': '/workspace/arbitech/logs/hitl',
            'enable_real_time_dashboards': True,
            'dashboard_update_interval': 5,  # seconds
            'enable_user_behavior_analysis': True,
            'enable_performance_prediction': True,
            'retention_days': 90,
            'max_cache_size': 10000,
            'enable_export_capabilities': True,
            'enable_audit_trail': True,
            'json_pretty_print': False,
            'enable_compression': True,
            'batch_size': 100,
            'enable_alerting': True
        }
    
    def _initialize_storage(self):
        """Initialize storage directories and files."""
        hitl_dir = Path(self.config.get('hitl_directory', '/workspace/arbitech/logs/hitl'))
        hitl_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (hitl_dir / 'decisions').mkdir(exist_ok=True)
        (hitl_dir / 'results').mkdir(exist_ok=True)
        (hitl_dir / 'performance').mkdir(exist_ok=True)
        (hitl_dir / 'patterns').mkdir(exist_ok=True)
        (hitl_dir / 'dashboards').mkdir(exist_ok=True)
        (hitl_dir / 'exports').mkdir(exist_ok=True)
        
        # Initialize log files
        self.log_files = {
            'decisions': hitl_dir / 'decisions' / 'human_decisions.jsonl',
            'results': hitl_dir / 'results' / 'trade_results.jsonl',
            'performance': hitl_dir / 'performance' / 'metrics.jsonl',
            'patterns': hitl_dir / 'patterns' / 'interaction_patterns.jsonl',
            'audit': hitl_dir / 'audit_trail.jsonl'
        }
    
    def integrate_with_audit_logger(self, audit_logger: AuditLogger):
        """Integrate with the main audit logger."""
        self._audit_logger = audit_logger
    
    def integrate_with_execution_tracker(self, execution_tracker):
        """Integrate with the execution tracker."""
        self._execution_tracker = execution_tracker
    
    def integrate_with_risk_analyzer(self, risk_analyzer):
        """Integrate with the risk analyzer."""
        self._risk_analyzer = risk_analyzer
    
    def log_human_decision(self, decision: HumanDecision):
        """Log a human decision with full context."""
        with self._lock:
            try:
                # Add to decisions log
                self._append_to_file(self.log_files['decisions'], decision.to_dict())
                
                # Update user interaction pattern
                self._update_interaction_pattern(decision)
                
                # Log to audit system
                if self._audit_logger:
                    self._audit_logger.log_user_action(
                        action=f"Trade decision: {decision.decision_type.value}",
                        resource=f"opportunity:{decision.opportunity_id}",
                        details={
                            'decision_id': decision.decision_id,
                            'expected_profit': decision.expected_profit,
                            'risk_level': decision.risk_level,
                            'time_to_decision_ms': decision.time_to_decision_ms,
                            'confidence_score': decision.confidence_score
                        }
                    )
                
                # Trigger real-time analytics
                self._analytics_engine.process_decision(decision)
                
                # Store in cache for real-time queries
                if decision.opportunity_id not in self._performance_cache:
                    self._performance_cache[decision.opportunity_id] = {}
                self._performance_cache[decision.opportunity_id]['last_decision'] = decision
                
                logging.info(f"Logged human decision: {decision.decision_id}")
                
            except Exception as e:
                logging.error(f"Failed to log human decision: {e}")
                if self._audit_logger:
                    self._audit_logger.log_system_error(e, {"component": "hitl.result_logger"})
    
    def log_trade_result(self, result: TradeResult):
        """Log a trade execution result."""
        with self._lock:
            try:
                # Add to results log
                self._append_to_file(self.log_files['results'], result.to_dict())
                
                # Update related decision with outcome
                self._update_decision_outcome(result)
                
                # Log to audit system
                if self._audit_logger:
                    audit_entry = AuditEntry(
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        event_type=EventType.TRADE_EXECUTION,
                        user_id="system",  # System logged outcome
                        session_id=None,
                        ip_address=None,
                        action=f"Trade execution completed",
                        resource=f"opportunity:{result.opportunity_id}",
                        details={
                            'result_id': result.result_id,
                            'outcome': result.outcome.value,
                            'total_profit_loss': result.total_profit_loss,
                            'execution_time_ms': result.execution_time_ms,
                            'success': result.outcome in [TradeOutcome.SUCCESS, TradeOutcome.PARTIAL_SUCCESS]
                        },
                        severity=LogLevel.INFO
                    )
                    self._audit_logger._append_to_file(
                        self._audit_logger.audit_trail_file, 
                        audit_entry.to_dict()
                    )
                
                # Trigger performance analytics
                self._analytics_engine.process_result(result)
                
                # Store in cache
                if result.opportunity_id not in self._performance_cache:
                    self._performance_cache[result.opportunity_id] = {}
                self._performance_cache[result.opportunity_id]['result'] = result
                
                logging.info(f"Logged trade result: {result.result_id}")
                
            except Exception as e:
                logging.error(f"Failed to log trade result: {e}")
                if self._audit_logger:
                    self._audit_logger.log_system_error(e, {"component": "hitl.result_logger"})
    
    def _update_interaction_pattern(self, decision: HumanDecision):
        """Update user interaction pattern for behavior analysis."""
        # This would typically update or create a UserInteractionPattern record
        # For now, we'll log pattern indicators to the patterns file
        
        pattern_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_id': decision.user_id,
            'session_id': decision.session_id,
            'decision_id': decision.decision_id,
            'decision_type': decision.decision_type.value,
            'decision_speed_ms': decision.time_to_decision_ms,
            'risk_level': decision.risk_level,
            'expected_profit': decision.expected_profit
        }
        
        self._append_to_file(self.log_files['patterns'], pattern_data)
    
    def _update_decision_outcome(self, result: TradeResult):
        """Update the related decision with execution outcome."""
        # In a real implementation, this would update the decision record
        # with the final outcome for correlation analysis
        pass
    
    def _append_to_file(self, file_path: Path, data: Dict[str, Any]):
        """Append JSON data to file."""
        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
        except Exception as e:
            logging.error(f"Failed to write to {file_path}: {e}")
            raise
    
    def get_performance_metrics(self, user_id: str, 
                               start_time: Optional[datetime] = None,
                               end_time: Optional[datetime] = None) -> PerformanceMetrics:
        """Get performance metrics for a user over a time period."""
        with self._lock:
            try:
                # Default to last 24 hours if no time range specified
                if not end_time:
                    end_time = datetime.now(timezone.utc)
                if not start_time:
                    start_time = end_time - timedelta(days=1)
                
                # Get decisions and results for the period
                decisions = self._get_decisions_in_range(user_id, start_time, end_time)
                results = self._get_results_in_range(user_id, start_time, end_time)
                
                # Calculate metrics
                metrics = self._calculate_performance_metrics(user_id, start_time, end_time, decisions, results)
                
                return metrics
                
            except Exception as e:
                logging.error(f"Failed to calculate performance metrics: {e}")
                if self._audit_logger:
                    self._audit_logger.log_system_error(e, {"component": "hitl.result_logger"})
                raise
    
    def _get_decisions_in_range(self, user_id: str, start_time: datetime, 
                               end_time: datetime) -> List[HumanDecision]:
        """Get decisions for a user in a time range."""
        decisions = []
        try:
            with open(self.log_files['decisions'], 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        decision_data = json.loads(line.strip())
                        if (decision_data.get('user_id') == user_id and
                            start_time.isoformat() <= decision_data.get('timestamp') <= end_time.isoformat()):
                            
                            # Convert back to HumanDecision object
                            decision = HumanDecision(
                                decision_id=decision_data['decision_id'],
                                opportunity_id=decision_data['opportunity_id'],
                                decision_type=DecisionType(decision_data['decision_type']),
                                timestamp=datetime.fromisoformat(decision_data['timestamp']),
                                user_id=decision_data['user_id'],
                                session_id=decision_data['session_id'],
                                reasoning=decision_data.get('reasoning'),
                                confidence_score=decision_data.get('confidence_score'),
                                time_to_decision_ms=decision_data.get('time_to_decision_ms'),
                                risk_level=decision_data.get('risk_level'),
                                expected_profit=decision_data.get('expected_profit'),
                                max_stake=decision_data.get('max_stake'),
                                bookmaker_count=decision_data.get('bookmaker_count'),
                                context_data=decision_data.get('context_data', {}),
                                ui_interactions=decision_data.get('ui_interactions', [])
                            )
                            decisions.append(decision)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        except FileNotFoundError:
            pass
        
        return decisions
    
    def _get_results_in_range(self, user_id: str, start_time: datetime,
                             end_time: datetime) -> List[TradeResult]:
        """Get trade results for a user in a time range."""
        results = []
        try:
            with open(self.log_files['results'], 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        result_data = json.loads(line.strip())
                        # We need to correlate results with decisions to get user_id
                        # For now, we'll get all results and filter later
                        if (start_time.isoformat() <= result_data.get('execution_start', '') <= end_time.isoformat()):
                            
                            # Convert back to TradeResult object
                            result = TradeResult(
                                result_id=result_data['result_id'],
                                decision_id=result_data['decision_id'],
                                opportunity_id=result_data['opportunity_id'],
                                execution_start=datetime.fromisoformat(result_data['execution_start']),
                                execution_end=datetime.fromisoformat(result_data['execution_end']) if result_data.get('execution_end') else None,
                                outcome=TradeOutcome(result_data['outcome']),
                                total_profit_loss=result_data.get('total_profit_loss'),
                                net_profit_loss=result_data.get('net_profit_loss'),
                                commission_costs=result_data.get('commission_costs'),
                                slippage=result_data.get('slippage'),
                                legs_completed=result_data.get('legs_completed', 0),
                                legs_total=result_data.get('legs_total', 0),
                                legs_failed=result_data.get('legs_failed', []),
                                execution_time_ms=result_data.get('execution_time_ms'),
                                max_drawdown=result_data.get('max_drawdown'),
                                realized_risk=result_data.get('realized_risk'),
                                risk_adjusted_return=result_data.get('risk_adjusted_return'),
                                expected_vs_actual_profit=result_data.get('expected_vs_actual_profit'),
                                efficiency_score=result_data.get('efficiency_score'),
                                error_messages=result_data.get('error_messages', []),
                                warnings=result_data.get('warnings', []),
                                market_conditions=result_data.get('market_conditions', {}),
                                system_performance=result_data.get('system_performance', {})
                            )
                            results.append(result)
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        except FileNotFoundError:
            pass
        
        return results
    
    def _calculate_performance_metrics(self, user_id: str, start_time: datetime,
                                      end_time: datetime, decisions: List[HumanDecision],
                                      results: List[TradeResult]) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        metrics = PerformanceMetrics(
            period_start=start_time,
            period_end=end_time,
            user_id=user_id
        )
        
        if not decisions:
            return metrics
        
        # Calculate decision metrics
        metrics.total_decisions = len(decisions)
        
        decision_types = [d.decision_type for d in decisions]
        metrics.approval_rate = decision_types.count(DecisionType.APPROVE) / metrics.total_decisions
        metrics.rejection_rate = decision_types.count(DecisionType.REJECT) / metrics.total_decisions
        metrics.timeout_rate = decision_types.count(DecisionType.TIMEOUT) / metrics.total_decisions
        
        # Calculate decision time metrics
        decision_times = [d.time_to_decision_ms for d in decisions if d.time_to_decision_ms]
        metrics.avg_decision_time_ms = statistics.mean(decision_times) if decision_times else 0.0
        
        # Calculate outcome metrics
        successful_results = [r for r in results if r.outcome in [TradeOutcome.SUCCESS, TradeOutcome.PARTIAL_SUCCESS]]
        failed_results = [r for r in results if r.outcome == TradeOutcome.FAILURE]
        
        metrics.successful_trades = len(successful_results)
        metrics.failed_trades = len(failed_results)
        
        # Calculate profit/loss metrics
        profits = [r.total_profit_loss for r in successful_results if r.total_profit_loss]
        losses = [r.total_profit_loss for r in failed_results if r.total_profit_loss]
        
        metrics.total_profit = sum(p for p in profits if p > 0)
        metrics.total_loss = abs(sum(l for l in losses if l < 0))
        metrics.net_profit = metrics.total_profit - metrics.total_loss
        metrics.success_rate = metrics.successful_trades / len(results) if results else 0.0
        
        # Calculate ROI
        total_stakes = sum(d.max_stake or 0 for d in decisions if d.decision_type == DecisionType.APPROVE)
        metrics.roi = (metrics.net_profit / total_stakes * 100) if total_stakes > 0 else 0.0
        
        # Calculate risk metrics
        risk_levels = [float(d.risk_level) for d in decisions if d.risk_level]
        metrics.avg_risk_level = statistics.mean(risk_levels) if risk_levels else 0.0
        
        # Calculate execution metrics
        execution_times = [r.execution_time_ms for r in results if r.execution_time_ms]
        metrics.avg_execution_time_ms = statistics.mean(execution_times) if execution_times else 0.0
        
        # Calculate throughput
        period_hours = (end_time - start_time).total_seconds() / 3600
        metrics.trades_per_hour = metrics.successful_trades / period_hours if period_hours > 0 else 0.0
        
        return metrics
    
    def generate_dashboard_data(self, user_id: Optional[str] = None,
                               real_time: bool = False) -> Dict[str, Any]:
        """Generate dashboard data for real-time monitoring."""
        try:
            dashboard_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'user_id': user_id,
                'real_time': real_time,
                'summary': {},
                'recent_activity': [],
                'performance_trends': {},
                'alerts': [],
                'system_status': {}
            }
            
            # Get current metrics
            if user_id:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=24)
                metrics = self.get_performance_metrics(user_id, start_time, end_time)
                dashboard_data['summary'] = metrics.to_dict()
            
            # Get recent activity
            dashboard_data['recent_activity'] = self._get_recent_activity(limit=50)
            
            # Get performance trends
            dashboard_data['performance_trends'] = self._get_performance_trends(user_id)
            
            # Get alerts
            dashboard_data['alerts'] = self._get_active_alerts()
            
            # Get system status
            dashboard_data['system_status'] = self._get_system_status()
            
            return dashboard_data
            
        except Exception as e:
            logging.error(f"Failed to generate dashboard data: {e}")
            return {}
    
    def _get_recent_activity(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent activity for dashboard."""
        activity = []
        try:
            # Get recent decisions
            with open(self.log_files['decisions'], 'r', encoding='utf-8') as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        decision_data = json.loads(line.strip())
                        activity.append({
                            'type': 'decision',
                            'timestamp': decision_data['timestamp'],
                            'data': decision_data
                        })
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            # Get recent results
            with open(self.log_files['results'], 'r', encoding='utf-8') as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        result_data = json.loads(line.strip())
                        activity.append({
                            'type': 'result',
                            'timestamp': result_data['execution_start'],
                            'data': result_data
                        })
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            # Sort by timestamp and limit
            activity.sort(key=lambda x: x['timestamp'], reverse=True)
            return activity[:limit]
            
        except FileNotFoundError:
            return []
    
    def _get_performance_trends(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get performance trends for dashboard."""
        trends = {
            'decision_trends': [],
            'outcome_trends': [],
            'profit_trends': []
        }
        
        # This would typically analyze historical data to show trends
        # For now, return empty structures
        return trends
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts for dashboard."""
        alerts = []
        
        try:
            # Integrate with risk analyzer for alerts
            if self._risk_analyzer:
                # This would get current risk alerts
                pass
            
            # Check for performance anomalies
            recent_metrics = self._check_performance_anomalies()
            alerts.extend(recent_metrics)
            
            return alerts
            
        except Exception as e:
            logging.error(f"Failed to get active alerts: {e}")
            return []
    
    def _check_performance_anomalies(self) -> List[Dict[str, Any]]:
        """Check for performance anomalies and generate alerts."""
        alerts = []
        
        # This would analyze recent performance for anomalies
        # For now, return empty list
        return alerts
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get system status information."""
        return {
            'logging_system': 'operational',
            'audit_logger': 'connected' if self._audit_logger else 'disconnected',
            'execution_tracker': 'connected' if self._execution_tracker else 'disconnected',
            'risk_analyzer': 'connected' if self._risk_analyzer else 'disconnected',
            'uptime': 'unknown'
        }
    
    def export_data(self, data_type: str, user_id: Optional[str] = None,
                   start_time: Optional[datetime] = None, 
                   end_time: Optional[datetime] = None,
                   format: str = 'json') -> str:
        """Export data in various formats."""
        try:
            export_dir = Path(self.config.get('hitl_directory')) / 'exports'
            export_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_file = export_dir / f"{data_type}_{user_id or 'all'}_{timestamp}.{format}"
            
            if data_type == 'decisions':
                data = self._get_decisions_in_range(user_id or '', start_time or datetime.min, 
                                                   end_time or datetime.max)
                export_data = [d.to_dict() for d in data]
            
            elif data_type == 'results':
                data = self._get_results_in_range(user_id or '', start_time or datetime.min,
                                                 end_time or datetime.max)
                export_data = [r.to_dict() for r in data]
            
            elif data_type == 'performance':
                if user_id:
                    metrics = self.get_performance_metrics(user_id, start_time, end_time)
                    export_data = [metrics.to_dict()]
                else:
                    export_data = []
            
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
            
            # Write export file
            if format == 'json':
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            elif format == 'csv':
                import csv
                with open(export_file, 'w', newline='', encoding='utf-8') as f:
                    if export_data:
                        writer = csv.DictWriter(f, fieldnames=export_data[0].keys())
                        writer.writeheader()
                        writer.writerows(export_data)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logging.info(f"Exported {len(export_data)} records to {export_file}")
            return str(export_file)
            
        except Exception as e:
            logging.error(f"Failed to export data: {e}")
            if self._audit_logger:
                self._audit_logger.log_system_error(e, {"component": "hitl.result_logger"})
            raise
    
    def cleanup_old_logs(self, days_to_keep: int = None):
        """Clean up old log files."""
        if days_to_keep is None:
            days_to_keep = self.config.get('retention_days', 90)
        
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        
        for file_path in self.log_files.values():
            try:
                if file_path.exists() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
            except Exception as e:
                logging.error(f"Failed to clean up {file_path}: {e}")
    
    def get_audit_trail(self, user_id: Optional[str] = None,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get comprehensive audit trail."""
        trail = []
        
        try:
            # Get audit entries from file
            if self.log_files['audit'].exists():
                with open(self.log_files['audit'], 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            
                            # Apply filters
                            if user_id and entry.get('user_id') != user_id:
                                continue
                            if start_time and entry.get('timestamp', '') < start_time.isoformat():
                                continue
                            if end_time and entry.get('timestamp', '') > end_time.isoformat():
                                continue
                            
                            trail.append(entry)
                        except (json.JSONDecodeError, KeyError):
                            continue
        except FileNotFoundError:
            pass
        
        return trail


class AnalyticsEngine:
    """Analytics engine for real-time performance analysis."""
    
    def __init__(self, result_logger: ResultLogger):
        self.result_logger = result_logger
        self.analytics_cache = {}
        self._lock = threading.RLock()
    
    def process_decision(self, decision: HumanDecision):
        """Process a new decision for real-time analytics."""
        with self._lock:
            try:
                # Update real-time metrics
                self._update_realtime_metrics(decision)
                
                # Check for patterns
                self._detect_patterns(decision)
                
                # Generate alerts if needed
                self._check_alert_conditions(decision)
                
            except Exception as e:
                logging.error(f"Failed to process decision analytics: {e}")
    
    def process_result(self, result: TradeResult):
        """Process a new result for real-time analytics."""
        with self._lock:
            try:
                # Update outcome metrics
                self._update_outcome_metrics(result)
                
                # Analyze performance vs expectations
                self._analyze_performance(result)
                
                # Update predictions
                self._update_predictions(result)
                
            except Exception as e:
                logging.error(f"Failed to process result analytics: {e}")
    
    def _update_realtime_metrics(self, decision: HumanDecision):
        """Update real-time metrics cache."""
        # Implementation for real-time metrics update
        pass
    
    def _detect_patterns(self, decision: HumanDecision):
        """Detect user behavior patterns."""
        # Implementation for pattern detection
        pass
    
    def _check_alert_conditions(self, decision: HumanDecision):
        """Check if decision triggers any alerts."""
        # Implementation for alert checking
        pass
    
    def _update_outcome_metrics(self, result: TradeResult):
        """Update outcome metrics."""
        # Implementation for outcome metrics update
        pass
    
    def _analyze_performance(self, result: TradeResult):
        """Analyze performance vs expectations."""
        # Implementation for performance analysis
        pass
    
    def _update_predictions(self, result: TradeResult):
        """Update performance predictions."""
        # Implementation for prediction updates
        pass


# Global instance and convenience functions
_result_logger = None


def get_result_logger(config: Optional[Dict[str, Any]] = None) -> ResultLogger:
    """Get or create global result logger instance."""
    global _result_logger
    if _result_logger is None:
        _result_logger = ResultLogger(config)
    return _result_logger


def log_human_decision(opportunity_id: str, decision_type: DecisionType, 
                      user_id: str, session_id: str, **kwargs) -> HumanDecision:
    """Convenience function to log a human decision."""
    logger = get_result_logger()
    
    decision = HumanDecision(
        decision_id=str(uuid.uuid4()),
        opportunity_id=opportunity_id,
        decision_type=decision_type,
        timestamp=datetime.now(timezone.utc),
        user_id=user_id,
        session_id=session_id,
        **kwargs
    )
    
    logger.log_human_decision(decision)
    return decision


def log_trade_result(decision_id: str, opportunity_id: str, **kwargs) -> TradeResult:
    """Convenience function to log a trade result."""
    logger = get_result_logger()
    
    result = TradeResult(
        result_id=str(uuid.uuid4()),
        decision_id=decision_id,
        opportunity_id=opportunity_id,
        execution_start=datetime.now(timezone.utc),
        **kwargs
    )
    
    logger.log_trade_result(result)
    return result


def get_performance_dashboard(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to get performance dashboard data."""
    logger = get_result_logger()
    return logger.generate_dashboard_data(user_id)


if __name__ == "__main__":
    # Example usage and testing
    logger = get_result_logger()
    
    # Test human decision logging
    decision = log_human_decision(
        opportunity_id="OPP-001",
        decision_type=DecisionType.APPROVE,
        user_id="trader123",
        session_id="session-456",
        reasoning="Good arbitrage opportunity with low risk",
        confidence_score=0.85,
        time_to_decision_ms=2500,
        risk_level="0.3",
        expected_profit=150.0,
        max_stake=1000.0,
        bookmaker_count=3
    )
    
    print(f"Logged decision: {decision.decision_id}")
    
    # Test trade result logging
    result = log_trade_result(
        decision_id=decision.decision_id,
        opportunity_id="OPP-001",
        outcome=TradeOutcome.SUCCESS,
        total_profit_loss=145.50,
        net_profit_loss=142.75,
        commission_costs=2.75,
        legs_completed=3,
        legs_total=3,
        execution_time_ms=1200.0
    )
    
    print(f"Logged result: {result.result_id}")
    
    # Test performance metrics
    metrics = logger.get_performance_metrics("trader123")
    print(f"Performance metrics: {metrics.total_decisions} decisions, {metrics.success_rate:.2%} success rate")
    
    # Test dashboard generation
    dashboard = logger.generate_dashboard_data("trader123")
    print(f"Dashboard generated with {len(dashboard.get('recent_activity', []))} recent activities")
    
    print("HITL Result Logger test completed successfully!")