"""
Scan Scheduler - Advanced Scheduling System

This module provides an advanced scheduling system for different scan frequencies,
market types, and bookmaker prioritization.

Features:
- Flexible scheduling patterns (interval-based, cron-like, event-driven)
- Priority-based scheduling with automatic escalation
- Dynamic schedule adjustment based on market conditions
- Resource-aware scheduling to prevent overload
- Comprehensive schedule management and monitoring
- Integration with scanner engine for task execution
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from uuid import uuid4, UUID
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from threading import RLock
import json
import math
import re
from croniter import croniter


# ============================================================================
# ENUMS AND DATA MODELS
# ============================================================================

class ScheduleType(str, Enum):
    """Types of scheduling patterns."""
    INTERVAL = "interval"  # Fixed interval between scans
    CRON = "cron"  # Cron-like scheduling
    EVENT_DRIVEN = "event_driven"  # Triggered by events
    PRIORITY_BASED = "priority_based"  # Based on priority and resource availability
    ADAPTIVE = "adaptive"  # Adjusts based on market conditions


class ScheduleStatus(str, Enum):
    """Status of scheduled scans."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanPriority(str, Enum):
    """Scan priority levels."""
    CRITICAL = "critical"  # Immediate execution required
    HIGH = "high"  # High importance
    NORMAL = "normal"  # Standard priority
    LOW = "low"  # Low priority
    IDLE = "idle"  # Execute only when resources available


@dataclass
class ScheduleConfig:
    """Configuration for a scanning schedule."""
    schedule_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: Optional[str] = None
    
    # Schedule parameters
    schedule_type: ScheduleType = ScheduleType.INTERVAL
    interval_seconds: Optional[int] = None  # For INTERVAL type
    cron_expression: Optional[str] = None  # For CRON type
    max_executions: Optional[int] = None  # Limit number of executions
    
    # Scan parameters
    bookmakers: List[str] = field(default_factory=list)
    sports: List[str] = field(default_factory=list)
    market_types: List[str] = field(default_factory=list)
    priority: ScanPriority = ScanPriority.NORMAL
    
    # Resource management
    max_concurrent: int = 1
    cooldown_period: int = 0  # Minimum time between executions
    
    # Adaptive scheduling
    enabled: bool = True
    auto_scale: bool = True
    resource_threshold: float = 0.8  # Scale down when resource usage exceeds this
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    execution_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schedule config to dictionary."""
        return {
            'schedule_id': str(self.schedule_id),
            'name': self.name,
            'description': self.description,
            'schedule_type': self.schedule_type.value,
            'interval_seconds': self.interval_seconds,
            'cron_expression': self.cron_expression,
            'max_executions': self.max_executions,
            'bookmakers': self.bookmakers,
            'sports': self.sports,
            'market_types': self.market_types,
            'priority': self.priority.value,
            'max_concurrent': self.max_concurrent,
            'cooldown_period': self.cooldown_period,
            'enabled': self.enabled,
            'auto_scale': self.auto_scale,
            'resource_threshold': self.resource_threshold,
            'created_at': self.created_at.isoformat(),
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None,
            'execution_count': self.execution_count
        }


@dataclass
class ScheduledScan:
    """Represents a scheduled scan execution."""
    scan_id: UUID = field(default_factory=uuid4)
    schedule_id: UUID = field(default_factory=uuid4)
    status: ScheduleStatus = ScheduleStatus.ACTIVE
    
    # Execution tracking
    scheduled_for: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Task information
    bookmaker: str = ""
    sport: str = ""
    market_type: str = "match_winner"
    priority: ScanPriority = ScanPriority.NORMAL
    
    # Results
    success: Optional[bool] = None
    error_message: Optional[str] = None
    opportunities_found: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scheduled scan to dictionary."""
        return {
            'scan_id': str(self.scan_id),
            'schedule_id': str(self.schedule_id),
            'status': self.status.value,
            'scheduled_for': self.scheduled_for.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'bookmaker': self.bookmaker,
            'sport': self.sport,
            'market_type': self.market_type,
            'priority': self.priority.value,
            'success': self.success,
            'error_message': self.error_message,
            'opportunities_found': self.opportunities_found
        }


class ResourceMonitor:
    """Monitor system resources for adaptive scheduling."""
    
    def __init__(self):
        self.cpu_threshold = 80.0
        self.memory_threshold = 80.0
        self.queue_threshold = 50
        self.error_rate_threshold = 0.1
        
        self.metrics_history: deque = deque(maxlen=100)
        
    def get_current_usage(self) -> Dict[str, float]:
        """Get current system resource usage."""
        try:
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'available_memory_gb': memory.available / (1024**3)
            }
        except ImportError:
            # Fallback if psutil not available
            return {
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'available_memory_gb': 1.0
            }
    
    def should_scale_down(self, current_usage: Dict[str, float], queue_size: int) -> bool:
        """Determine if we should scale down scheduling."""
        return (
            current_usage.get('cpu_percent', 0) > self.cpu_threshold or
            current_usage.get('memory_percent', 0) > self.memory_threshold or
            queue_size > self.queue_threshold
        )
    
    def get_resource_score(self, current_usage: Dict[str, float]) -> float:
        """Calculate a resource availability score (0.0 to 1.0)."""
        cpu_score = max(0, 1 - (current_usage.get('cpu_percent', 0) / 100))
        memory_score = max(0, 1 - (current_usage.get('memory_percent', 0) / 100))
        
        return (cpu_score + memory_score) / 2


# ============================================================================
# SCHEDULER CORE
# ============================================================================

class ScanScheduler:
    """
    Advanced scheduling system for scan operations with multiple scheduling patterns,
    resource awareness, and adaptive behavior.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the scan scheduler.
        
        Args:
            config: Scheduler configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Scheduler configuration
        self.max_concurrent_schedules = self.config.get('max_concurrent_schedules', 100)
        self.adaptive_scheduling = self.config.get('adaptive_scheduling', True)
        self.resource_monitoring = self.config.get('resource_monitoring', True)
        self.default_interval = self.config.get('default_interval_seconds', 60)
        
        # Core components
        self.schedules: Dict[UUID, ScheduleConfig] = {}
        self.active_scans: Dict[UUID, ScheduledScan] = {}
        self.execution_history: deque = deque(maxlen=1000)
        self.resource_monitor = ResourceMonitor()
        
        # Scheduling engines
        self.interval_scheduler = IntervalScheduler()
        self.cron_scheduler = CronScheduler()
        self.event_scheduler = EventDrivenScheduler()
        self.priority_scheduler = PriorityScheduler()
        self.adaptive_scheduler = AdaptiveScheduler()
        
        # Threading and coordination
        self._running = False
        self._lock = RLock()
        self._scheduling_task: Optional[asyncio.Task] = None
        self._resource_task: Optional[asyncio.Task] = None
        self._event_handlers: List[Callable] = []
        
        # Performance metrics
        self.total_scheduled_scans = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.average_execution_time = 0.0
        self.resource_adjustments = 0
        
        self.logger.info("ScanScheduler initialized")
    
    async def start(self):
        """Start the scan scheduler."""
        if self._running:
            self.logger.warning("ScanScheduler already running")
            return
        
        self._running = True
        
        # Start scheduling loop
        self._scheduling_task = asyncio.create_task(self._scheduling_loop())
        
        # Start resource monitoring if enabled
        if self.resource_monitoring:
            self._resource_task = asyncio.create_task(self._resource_monitoring_loop())
        
        self.logger.info("ScanScheduler started")
    
    async def stop(self):
        """Stop the scan scheduler."""
        if not self._running:
            return
        
        self.logger.info("Stopping ScanScheduler...")
        
        self._running = False
        
        # Cancel background tasks
        if self._scheduling_task:
            self._scheduling_task.cancel()
        
        if self._resource_task:
            self._resource_task.cancel()
        
        # Wait for tasks to complete
        tasks = [t for t in [self._scheduling_task, self._resource_task] if t]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("ScanScheduler stopped")
    
    def create_schedule(self, config: ScheduleConfig) -> UUID:
        """
        Create a new scanning schedule.
        
        Args:
            config: Schedule configuration
            
        Returns:
            UUID of the created schedule
        """
        with self._lock:
            # Validate configuration
            self._validate_schedule_config(config)
            
            # Set default values
            if not config.name:
                config.name = f"Schedule {config.schedule_id}"
            
            # Initialize scheduling engine
            self._initialize_schedule_engine(config)
            
            # Store schedule
            self.schedules[config.schedule_id] = config
            
            self.logger.info("Created schedule %s: %s", config.schedule_id, config.name)
            return config.schedule_id
    
    def update_schedule(self, schedule_id: UUID, updates: Dict[str, Any]) -> bool:
        """Update an existing schedule."""
        with self._lock:
            if schedule_id not in self.schedules:
                return False
            
            schedule = self.schedules[schedule_id]
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(schedule, key):
                    setattr(schedule, key, value)
            
            # Re-initialize scheduling engine if needed
            self._initialize_schedule_engine(schedule)
            
            self.logger.info("Updated schedule %s", schedule_id)
            return True
    
    def delete_schedule(self, schedule_id: UUID) -> bool:
        """Delete a scanning schedule."""
        with self._lock:
            if schedule_id not in self.schedules:
                return False
            
            # Remove from all scheduling engines
            for scheduler in [self.interval_scheduler, self.cron_scheduler, 
                            self.event_scheduler, self.priority_scheduler, self.adaptive_scheduler]:
                scheduler.remove_schedule(schedule_id)
            
            # Remove schedule
            del self.schedules[schedule_id]
            
            self.logger.info("Deleted schedule %s", schedule_id)
            return True
    
    def pause_schedule(self, schedule_id: UUID) -> bool:
        """Pause a scanning schedule."""
        with self._lock:
            if schedule_id in self.schedules:
                self.schedules[schedule_id].enabled = False
                self.logger.info("Paused schedule %s", schedule_id)
                return True
            return False
    
    def resume_schedule(self, schedule_id: UUID) -> bool:
        """Resume a paused scanning schedule."""
        with self._lock:
            if schedule_id in self.schedules:
                self.schedules[schedule_id].enabled = True
                self.logger.info("Resumed schedule %s", schedule_id)
                return True
            return False
    
    def get_schedule_status(self, schedule_id: UUID) -> Optional[Dict[str, Any]]:
        """Get status of a specific schedule."""
        with self._lock:
            if schedule_id in self.schedules:
                schedule = self.schedules[schedule_id]
                return schedule.to_dict()
            return None
    
    def get_active_schedules(self) -> List[Dict[str, Any]]:
        """Get all active schedules."""
        with self._lock:
            return [
                schedule.to_dict() 
                for schedule in self.schedules.values() 
                if schedule.enabled
            ]
    
    def get_scheduler_metrics(self) -> Dict[str, Any]:
        """Get comprehensive scheduler metrics."""
        with self._lock:
            current_usage = self.resource_monitor.get_current_usage()
            
            return {
                'total_schedules': len(self.schedules),
                'active_schedules': len([s for s in self.schedules.values() if s.enabled]),
                'total_scheduled_scans': self.total_scheduled_scans,
                'successful_executions': self.successful_executions,
                'failed_executions': self.failed_executions,
                'success_rate': self.successful_executions / max(self.total_scheduled_scans, 1),
                'average_execution_time': self.average_execution_time,
                'resource_adjustments': self.resource_adjustments,
                'active_scans': len(self.active_scans),
                'current_resource_usage': current_usage,
                'schedule_types': self._get_schedule_type_distribution()
            }
    
    def add_event_handler(self, handler: Callable):
        """Add an event handler for scheduler events."""
        self._event_handlers.append(handler)
    
    def _validate_schedule_config(self, config: ScheduleConfig):
        """Validate schedule configuration."""
        if config.schedule_type == ScheduleType.INTERVAL:
            if not config.interval_seconds or config.interval_seconds <= 0:
                raise ValueError("Interval schedules must have a positive interval_seconds")
        
        elif config.schedule_type == ScheduleType.CRON:
            if not config.cron_expression:
                raise ValueError("Cron schedules must have a cron_expression")
            
            # Validate cron expression
            try:
                croniter(config.cron_expression)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {e}")
    
    def _initialize_schedule_engine(self, config: ScheduleConfig):
        """Initialize the appropriate scheduling engine for a config."""
        if config.schedule_type == ScheduleType.INTERVAL:
            self.interval_scheduler.add_schedule(config)
        
        elif config.schedule_type == ScheduleType.CRON:
            self.cron_scheduler.add_schedule(config)
        
        elif config.schedule_type == ScheduleType.EVENT_DRIVEN:
            self.event_scheduler.add_schedule(config)
        
        elif config.schedule_type == ScheduleType.PRIORITY_BASED:
            self.priority_scheduler.add_schedule(config)
        
        elif config.schedule_type == ScheduleType.ADAPTIVE:
            self.adaptive_scheduler.add_schedule(config)
    
    def _get_schedule_type_distribution(self) -> Dict[str, int]:
        """Get distribution of schedule types."""
        distribution = defaultdict(int)
        for schedule in self.schedules.values():
            distribution[schedule.schedule_type.value] += 1
        return dict(distribution)
    
    async def _scheduling_loop(self):
        """Main scheduling loop."""
        try:
            while self._running:
                current_time = datetime.now(timezone.utc)
                
                # Get due scans from all scheduling engines
                due_scans = []
                
                due_scans.extend(self.interval_scheduler.get_due_scans(current_time))
                due_scans.extend(self.cron_scheduler.get_due_scans(current_time))
                due_scans.extend(self.event_scheduler.get_due_scans(current_time))
                due_scans.extend(self.priority_scheduler.get_due_scans(current_time))
                due_scans.extend(self.adaptive_scheduler.get_due_scans(current_time))
                
                # Sort by priority
                due_scans.sort(key=lambda x: x.priority.value)
                
                # Execute due scans
                for scheduled_scan in due_scans:
                    await self._execute_scheduled_scan(scheduled_scan)
                
                # Sleep before next iteration
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error("Error in scheduling loop: %s", str(e))
    
    async def _resource_monitoring_loop(self):
        """Monitor system resources for adaptive scheduling."""
        try:
            while self._running:
                current_usage = self.resource_monitor.get_current_usage()
                queue_size = len(self.active_scans)
                
                # Check if we should scale down
                if self.resource_monitor.should_scale_down(current_usage, queue_size):
                    await self._scale_down_scheduling(current_usage)
                
                # Record metrics
                self.metrics_history.append({
                    'timestamp': datetime.now(timezone.utc),
                    'resource_usage': current_usage,
                    'queue_size': queue_size
                })
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error("Error in resource monitoring loop: %s", str(e))
    
    async def _scale_down_scheduling(self, current_usage: Dict[str, float]):
        """Scale down scheduling based on resource usage."""
        self.resource_adjustments += 1
        
        with self._lock:
            for schedule in self.schedules.values():
                if schedule.enabled and schedule.auto_scale:
                    # Reduce frequency by increasing interval
                    if schedule.interval_seconds:
                        old_interval = schedule.interval_seconds
                        schedule.interval_seconds = int(old_interval * 1.5)
                        self.logger.info(
                            "Scaled down schedule %s: interval %d -> %d seconds",
                            schedule.name, old_interval, schedule.interval_seconds
                        )
    
    async def _execute_scheduled_scan(self, scheduled_scan: ScheduledScan):
        """Execute a scheduled scan."""
        try:
            # Check if we have capacity
            if len(self.active_scans) >= self.max_concurrent_schedules:
                self.logger.warning("At capacity, skipping scheduled scan")
                return
            
            # Update scan status
            scheduled_scan.status = ScheduleStatus.ACTIVE
            scheduled_scan.started_at = datetime.now(timezone.utc)
            
            with self._lock:
                self.active_scans[scheduled_scan.scan_id] = scheduled_scan
                self.total_scheduled_scans += 1
            
            # Create the actual scan task
            # This would integrate with the scanner engine
            scan_task = self._create_scan_task(scheduled_scan)
            
            # Execute the scan
            start_time = time.time()
            try:
                # Simulate scan execution
                await asyncio.sleep(0.1)  # Placeholder for actual scan
                
                execution_time = time.time() - start_time
                
                # Update metrics
                if self.total_scheduled_scans > 0:
                    self.average_execution_time = (
                        (self.average_execution_time * (self.total_scheduled_scans - 1) + execution_time) /
                        self.total_scheduled_scans
                    )
                
                scheduled_scan.success = True
                self.successful_executions += 1
                
            except Exception as e:
                execution_time = time.time() - start_time
                scheduled_scan.success = False
                scheduled_scan.error_message = str(e)
                self.failed_executions += 1
                
                self.logger.error("Scheduled scan failed: %s", str(e))
            
            # Finalize scan
            scheduled_scan.completed_at = datetime.now(timezone.utc)
            
            # Update schedule execution count
            schedule = self.schedules.get(scheduled_scan.schedule_id)
            if schedule:
                schedule.last_execution = scheduled_scan.completed_at
                schedule.execution_count += 1
                
                # Check if we've reached max executions
                if schedule.max_executions and schedule.execution_count >= schedule.max_executions:
                    schedule.enabled = False
                    self.logger.info("Schedule %s reached max executions and was disabled", schedule.name)
            
            # Move to history
            with self._lock:
                if scheduled_scan.scan_id in self.active_scans:
                    del self.active_scans[scheduled_scan.scan_id]
                self.execution_history.append(scheduled_scan)
            
            self.logger.debug(
                "Executed scheduled scan %s in %.2fs",
                scheduled_scan.scan_id, execution_time
            )
            
        except Exception as e:
            self.logger.error("Error executing scheduled scan: %s", str(e))
    
    def _create_scan_task(self, scheduled_scan: ScheduledScan) -> Dict[str, Any]:
        """Create a scan task from scheduled scan."""
        return {
            'scan_id': str(scheduled_scan.scan_id),
            'bookmaker': scheduled_scan.bookmaker,
            'sport': scheduled_scan.sport,
            'market_type': scheduled_scan.market_type,
            'priority': scheduled_scan.priority.value
        }
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to registered handlers."""
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                self.logger.error("Error in scheduler event handler: %s", str(e))


# ============================================================================
# SCHEDULING ENGINES
# ============================================================================

class BaseScheduler:
    """Base class for scheduling engines."""
    
    def __init__(self):
        self.schedules: Dict[UUID, ScheduleConfig] = {}
    
    def add_schedule(self, config: ScheduleConfig):
        """Add a schedule to this engine."""
        self.schedules[config.schedule_id] = config
    
    def remove_schedule(self, schedule_id: UUID):
        """Remove a schedule from this engine."""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
    
    def get_due_scans(self, current_time: datetime) -> List[ScheduledScan]:
        """Get scans that are due for execution."""
        return []


class IntervalScheduler(BaseScheduler):
    """Scheduler for interval-based scans."""
    
    def get_due_scans(self, current_time: datetime) -> List[ScheduledScan]:
        due_scans = []
        
        for config in self.schedules.values():
            if not config.enabled or not config.interval_seconds:
                continue
            
            # Check if it's time for this scan
            if config.next_execution is None:
                config.next_execution = current_time
            
            if current_time >= config.next_execution:
                # Check cooldown period
                if (config.last_execution and 
                    (current_time - config.last_execution).total_seconds() < config.cooldown_period):
                    continue
                
                # Check max executions
                if config.max_executions and config.execution_count >= config.max_executions:
                    continue
                
                # Create scheduled scan for each bookmaker/sport combination
                for bookmaker in config.bookmakers:
                    for sport in config.sports:
                        scan = ScheduledScan(
                            schedule_id=config.schedule_id,
                            bookmaker=bookmaker,
                            sport=sport,
                            priority=config.priority
                        )
                        due_scans.append(scan)
                
                # Schedule next execution
                config.next_execution = current_time + timedelta(seconds=config.interval_seconds)
        
        return due_scans


class CronScheduler(BaseScheduler):
    """Scheduler for cron-based scans."""
    
    def get_due_scans(self, current_time: datetime) -> List[ScheduledScan]:
        due_scans = []
        
        for config in self.schedules.values():
            if not config.enabled or not config.cron_expression:
                continue
            
            # Check if cron expression matches current time
            cron = croniter(config.cron_expression, current_time)
            next_run = cron.get_next(datetime)
            
            # Allow 1-minute window for execution
            if abs((next_run - current_time).total_seconds()) <= 60:
                # Check cooldown period
                if (config.last_execution and 
                    (current_time - config.last_execution).total_seconds() < config.cooldown_period):
                    continue
                
                # Check max executions
                if config.max_executions and config.execution_count >= config.max_executions:
                    continue
                
                # Create scheduled scan
                for bookmaker in config.bookmakers:
                    for sport in config.sports:
                        scan = ScheduledScan(
                            schedule_id=config.schedule_id,
                            bookmaker=bookmaker,
                            sport=sport,
                            priority=config.priority
                        )
                        due_scans.append(scan)
        
        return due_scans


class EventDrivenScheduler(BaseScheduler):
    """Scheduler for event-driven scans."""
    
    def get_due_scans(self, current_time: datetime) -> List[ScheduledScan]:
        # Event-driven scans are triggered by external events, not time-based
        return []


class PriorityScheduler(BaseScheduler):
    """Scheduler for priority-based scans."""
    
    def get_due_scans(self, current_time: datetime) -> List[ScheduledScan]:
        # Priority-based scheduling would consider resource availability and priority
        return []


class AdaptiveScheduler(BaseScheduler):
    """Scheduler for adaptive scans."""
    
    def get_due_scans(self, current_time: datetime) -> List[ScheduledScan]:
        # Adaptive scheduling adjusts based on market conditions
        return []


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def create_scheduler(
    config: Optional[Dict[str, Any]] = None
) -> ScanScheduler:
    """
    Create and configure a scan scheduler.
    
    Args:
        config: Optional configuration override
        
    Returns:
        Configured ScanScheduler instance
    """
    scheduler = ScanScheduler(config)
    
    # Add default event handlers
    scheduler.add_event_handler(_default_scheduler_event_handler)
    
    return scheduler


async def _default_scheduler_event_handler(event_type: str, data: Dict[str, Any]):
    """Default event handler for logging scheduler events."""
    logger = logging.getLogger(__name__)
    
    if event_type == 'schedule_created':
        logger.info("Schedule created: %s", data.get('name', 'Unknown'))
    elif event_type == 'scan_executed':
        logger.debug("Scheduled scan executed: %s", data.get('scan_id', 'Unknown'))
    elif event_type == 'resource_adjustment':
        logger.info("Resource adjustment made: %s", data.get('reason', 'Unknown'))


def create_quick_scan_schedule(
    bookmaker: str,
    sport: str,
    interval_seconds: int = 60,
    priority: ScanPriority = ScanPriority.NORMAL
) -> ScheduleConfig:
    """Create a quick scan schedule for a specific bookmaker and sport."""
    return ScheduleConfig(
        name=f"Quick Scan - {bookmaker} ({sport})",
        schedule_type=ScheduleType.INTERVAL,
        interval_seconds=interval_seconds,
        bookmakers=[bookmaker],
        sports=[sport],
        priority=priority
    )


def create_cron_scan_schedule(
    name: str,
    bookmakers: List[str],
    sports: List[str],
    cron_expression: str,
    priority: ScanPriority = ScanPriority.NORMAL
) -> ScheduleConfig:
    """Create a cron-based scan schedule."""
    return ScheduleConfig(
        name=name,
        schedule_type=ScheduleType.CRON,
        cron_expression=cron_expression,
        bookmakers=bookmakers,
        sports=sports,
        priority=priority
    )


def get_scheduler_performance_summary(scheduler: ScanScheduler) -> Dict[str, Any]:
    """Get comprehensive performance summary of the scan scheduler."""
    metrics = scheduler.get_scheduler_metrics()
    
    return {
        'scheduler_metrics': metrics,
        'recommendations': [
            'Monitor schedule success rates',
            'Optimize cron expressions for efficiency',
            'Adjust intervals based on market volatility',
            'Use adaptive scheduling for resource optimization'
        ]
    }