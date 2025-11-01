"""
Scanner Engine - Core Scanning Engine

This module provides the core scanning engine with configurable scan schedules,
multi-threaded operations, and priority-based scanning.

Features:
- Multi-threaded scanning operations
- Priority-based scan queue management
- Automatic retry and error recovery
- Performance tracking and metrics
- Circuit breaker pattern for fault tolerance
- Configurable scan frequencies and limits
"""

import asyncio
import logging
import time
import traceback
import heapq
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from uuid import uuid4, UUID
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from threading import Lock, RLock
import json
from functools import wraps

from ..storage.models import Sport, ArbitrageOpportunity
from ..vlm.error_recovery import ErrorRecoveryManager, VLMRecoveryConfig
from .scan_scheduler import ScanPriority


# ============================================================================
# ENUMS AND DATA MODELS
# ============================================================================

class ScanStatus(str, Enum):
    """Status of individual scans."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class ScanType(str, Enum):
    """Types of scan operations."""
    BOOKMAKER_SCAN = "bookmaker_scan"
    MARKET_SCAN = "market_scan"
    FULL_SCAN = "full_scan"
    QUICK_SCAN = "quick_scan"
    PRIORITY_SCAN = "priority_scan"


@dataclass
class ScanResult:
    """Result of a scan operation."""
    scan_id: UUID
    success: bool
    bookmaker: Optional[str] = None
    sport: Optional[Sport] = None
    opportunities_found: List[ArbitrageOpportunity] = field(default_factory=list)
    execution_time: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_at: Optional[datetime] = None


@dataclass
class ScanTask:
    """Represents a scan task in the engine."""
    scan_id: UUID
    scan_type: ScanType
    priority: ScanPriority
    bookmaker: str
    sport: Sport
    image_data: Union[str, bytes]
    market_type: str = "match_winner"
    event_name: str = ""
    
    # Execution tracking
    status: ScanStatus = ScanStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    
    # Result data
    opportunities: List[ArbitrageOpportunity] = field(default_factory=list)
    execution_time: float = 0.0
    confidence_score: float = 0.0
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time for this scan."""
        if self.started_at:
            end_time = self.completed_at or datetime.now(timezone.utc)
            return (end_time - self.started_at).total_seconds()
        return 0.0
    
    @property
    def is_active(self) -> bool:
        """Check if scan is currently active."""
        return self.status in [ScanStatus.RUNNING, ScanStatus.RETRYING]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scan task to dictionary."""
        return {
            'scan_id': str(self.scan_id),
            'scan_type': self.scan_type.value,
            'priority': self.priority.value,
            'bookmaker': self.bookmaker,
            'sport': self.sport.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'elapsed_time': self.elapsed_time,
            'opportunities_found': len(self.opportunities),
            'error_message': self.error_message
        }


class EngineMetrics:
    """Metrics for scanner engine performance tracking."""
    
    def __init__(self):
        self.total_scans = 0
        self.successful_scans = 0
        self.failed_scans = 0
        self.cancelled_scans = 0
        self.retried_scans = 0
        self.average_execution_time = 0.0
        self.throughput_scans_per_minute = 0.0
        self.queue_size = 0
        self.active_scans = 0
        self.errors_by_type: Dict[str, int] = defaultdict(int)
        self.performance_history: deque = deque(maxlen=100)
        self.start_time = datetime.now(timezone.utc)
        
        # Concurrency metrics
        self.max_concurrent_scans = 0
        self.avg_wait_time = 0.0
        self.last_reset = datetime.now(timezone.utc)
    
    def record_scan_result(self, result: ScanResult):
        """Record a scan result for metrics."""
        self.total_scans += 1
        
        if result.success:
            self.successful_scans += 1
        else:
            self.failed_scans += 1
            if result.error_message:
                self.errors_by_type[result.error_message[:50]] += 1
        
        # Update execution time metrics
        if self.total_scans > 0:
            self.average_execution_time = (
                (self.average_execution_time * (self.total_scans - 1) + result.execution_time) / self.total_scans
            )
        
        # Record performance history
        self.performance_history.append({
            'timestamp': datetime.now(timezone.utc),
            'success': result.success,
            'execution_time': result.execution_time,
            'retry_count': result.retry_count
        })
    
    def update_concurrency_metrics(self, active_scans: int, queue_size: int, avg_wait_time: float):
        """Update concurrency-related metrics."""
        self.active_scans = active_scans
        self.queue_size = queue_size
        self.max_concurrent_scans = max(self.max_concurrent_scans, active_scans)
        self.avg_wait_time = avg_wait_time
        
        # Calculate throughput (scans per minute)
        time_elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds() / 60
        if time_elapsed > 0:
            self.throughput_scans_per_minute = self.total_scans / time_elapsed
    
    def reset(self):
        """Reset metrics."""
        self.__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        uptime_minutes = (datetime.now(timezone.utc) - self.start_time).total_seconds() / 60
        
        return {
            'total_scans': self.total_scans,
            'successful_scans': self.successful_scans,
            'failed_scans': self.failed_scans,
            'cancelled_scans': self.cancelled_scans,
            'retried_scans': self.retried_scans,
            'success_rate': self.successful_scans / max(self.total_scans, 1),
            'average_execution_time': self.average_execution_time,
            'throughput_scans_per_minute': self.throughput_scans_per_minute,
            'current_queue_size': self.queue_size,
            'active_scans': self.active_scans,
            'max_concurrent_scans': self.max_concurrent_scans,
            'average_wait_time': self.avg_wait_time,
            'uptime_minutes': uptime_minutes,
            'errors_by_type': dict(self.errors_by_type),
            'recent_performance': list(self.performance_history)[-10:]
        }


# ============================================================================
# PRIORITY QUEUE IMPLEMENTATION
# ============================================================================

class PriorityQueue:
    """Thread-safe priority queue for scan tasks."""
    
    def __init__(self):
        self._queue: List[Tuple[int, ScanTask]] = []
        self._lock = Lock()
        self._condition = asyncio.Condition(self._lock)
    
    async def put(self, task: ScanTask):
        """Add a task to the priority queue."""
        async with self._condition:
            # Priority values: 0 = highest, higher numbers = lower priority
            priority_value = self._get_priority_value(task.priority)
            heapq.heappush(self._queue, (priority_value, task))
            self._condition.notify_all()
    
    async def get(self) -> Optional[ScanTask]:
        """Get the highest priority task from the queue."""
        async with self._condition:
            while not self._queue:
                await self._condition.wait()
            
            if self._queue:
                priority, task = heapq.heappop(self._queue)
                return task
            return None
    
    async def put_front(self, task: ScanTask):
        """Add a task to the front of the queue (highest priority)."""
        async with self._condition:
            priority_value = -1000  # Very high priority
            heapq.heappush(self._queue, (priority_value, task))
            self._condition.notify_all()
    
    def qsize(self) -> int:
        """Get the current queue size."""
        return len(self._queue)
    
    def _get_priority_value(self, priority: ScanPriority) -> int:
        """Convert ScanPriority to numerical priority value."""
        priority_mapping = {
            ScanPriority.CRITICAL: 0,
            ScanPriority.HIGH: 1,
            ScanPriority.NORMAL: 2,
            ScanPriority.LOW: 3,
            ScanPriority.IDLE: 4
        }
        return priority_mapping.get(priority, 2)


# ============================================================================
# SCANNER ENGINE CORE
# ============================================================================

class ScannerEngine:
    """
    Core scanning engine with multi-threaded operations, priority-based scanning,
    and comprehensive error recovery.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the scanner engine.
        
        Args:
            config: Engine configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Engine configuration
        self.max_concurrent_scans = self.config.get('max_concurrent_scans', 10)
        self.thread_pool_size = self.config.get('thread_pool_size', 20)
        self.retry_failed_scans = self.config.get('retry_failed_scans', True)
        self.max_retries = self.config.get('max_retries', 3)
        self.scan_timeout = self.config.get('scan_timeout', 60)
        self.enable_circuit_breaker = self.config.get('enable_circuit_breaker', True)
        
        # Core components
        self.priority_queue = PriorityQueue()
        self.thread_pool = ThreadPoolExecutor(max_workers=self.thread_pool_size)
        self.active_scans: Dict[UUID, ScanTask] = {}
        self.completed_scans: deque = deque(maxlen=1000)
        self.metrics = EngineMetrics()
        
        # Error recovery
        recovery_config = VLMRecoveryConfig(
            enable_circuit_breaker=self.enable_circuit_breaker,
            max_retry_attempts=self.max_retries
        )
        self.error_recovery = ErrorRecoveryManager(recovery_config)
        
        # Threading controls
        self._running = False
        self._scan_workers: List[asyncio.Task] = []
        self._lock = RLock()
        self._event_handlers: List[Callable] = []
        
        # Circuit breaker for overall engine health
        self.engine_circuit_breaker_failure_threshold = 10
        self.engine_circuit_breaker_failure_window = 300  # 5 minutes
        self.engine_failures = deque(maxlen=self.engine_circuit_breaker_failure_threshold)
        
        self.logger.info("ScannerEngine initialized with max_concurrent_scans=%d", self.max_concurrent_scans)
    
    async def start(self):
        """Start the scanner engine."""
        if self._running:
            self.logger.warning("Scanner engine already running")
            return
        
        self._running = True
        
        # Start scan workers
        for i in range(self.max_concurrent_scans):
            worker_task = asyncio.create_task(self._scan_worker(f"worker-{i}"))
            self._scan_workers.append(worker_task)
        
        self.logger.info("ScannerEngine started with %d workers", self.max_concurrent_scans)
    
    async def stop(self):
        """Stop the scanner engine."""
        if not self._running:
            return
        
        self.logger.info("Stopping ScannerEngine...")
        
        # Stop accepting new tasks
        self._running = False
        
        # Cancel all workers
        for worker in self._scan_workers:
            worker.cancel()
        
        # Wait for workers to complete
        if self._scan_workers:
            await asyncio.gather(*self._scan_workers, return_exceptions=True)
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        self._scan_workers.clear()
        self.logger.info("ScannerEngine stopped")
    
    def add_scan_task(
        self,
        scan_type: ScanType,
        bookmaker: str,
        sport: Sport,
        image_data: Union[str, bytes],
        priority: ScanPriority = ScanPriority.NORMAL,
        market_type: str = "match_winner",
        event_name: str = "",
        max_retries: Optional[int] = None
    ) -> UUID:
        """
        Add a new scan task to the engine.
        
        Args:
            scan_type: Type of scan to perform
            bookmaker: Bookmaker to scan
            sport: Sport type
            image_data: Image data (URL or bytes)
            priority: Scan priority
            market_type: Market type
            event_name: Event name
            max_retries: Maximum retry attempts (overrides default)
            
        Returns:
            UUID of the created scan task
        """
        scan_id = uuid4()
        task = ScanTask(
            scan_id=scan_id,
            scan_type=scan_type,
            priority=priority,
            bookmaker=bookmaker,
            sport=sport,
            image_data=image_data,
            market_type=market_type,
            event_name=event_name,
            max_retries=max_retries or self.max_retries
        )
        
        with self._lock:
            self.active_scans[scan_id] = task
        
        # Add to appropriate queue
        if priority == ScanPriority.CRITICAL:
            asyncio.create_task(self.priority_queue.put_front(task))
        else:
            asyncio.create_task(self.priority_queue.put(task))
        
        self.logger.debug("Added scan task %s for %s (%s)", scan_id, bookmaker, sport.value)
        return scan_id
    
    async def cancel_scan(self, scan_id: UUID) -> bool:
        """Cancel an active scan task."""
        with self._lock:
            if scan_id in self.active_scans:
                task = self.active_scans[scan_id]
                task.status = ScanStatus.CANCELLED
                task.completed_at = datetime.now(timezone.utc)
                
                # Move to completed scans
                self.completed_scans.append(task)
                del self.active_scans[scan_id]
                
                self.metrics.cancelled_scans += 1
                
                self.logger.info("Cancelled scan task %s", scan_id)
                return True
        
        return False
    
    def get_scan_status(self, scan_id: UUID) -> Optional[Dict[str, Any]]:
        """Get status of a specific scan task."""
        with self._lock:
            if scan_id in self.active_scans:
                return self.active_scans[scan_id].to_dict()
            
            # Check completed scans
            for task in self.completed_scans:
                if task.scan_id == scan_id:
                    return task.to_dict()
        
        return None
    
    def get_engine_metrics(self) -> Dict[str, Any]:
        """Get comprehensive engine metrics."""
        with self._lock:
            queue_size = self.priority_queue.qsize()
            active_count = len(self.active_scans)
            
            # Calculate average wait time
            now = datetime.now(timezone.utc)
            wait_times = []
            for task in self.active_scans.values():
                wait_time = (now - task.created_at).total_seconds()
                wait_times.append(wait_time)
            
            avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0.0
            self.metrics.update_concurrency_metrics(active_count, queue_size, avg_wait_time)
        
        return self.metrics.to_dict()
    
    def add_event_handler(self, handler: Callable):
        """Add an event handler for engine events."""
        self._event_handlers.append(handler)
    
    async def _scan_worker(self, worker_name: str):
        """Worker function that processes scan tasks from the queue."""
        self.logger.debug("Scan worker %s started", worker_name)
        
        try:
            while self._running:
                # Get next task from queue
                task = await self.priority_queue.get()
                
                if not task:
                    continue
                
                # Check if engine circuit breaker is open
                if not self._can_execute_scan():
                    self.logger.warning("Engine circuit breaker is open, skipping scan")
                    await asyncio.sleep(1)
                    continue
                
                # Execute the scan
                await self._execute_scan_task(task, worker_name)
                
        except asyncio.CancelledError:
            self.logger.debug("Scan worker %s cancelled", worker_name)
        except Exception as e:
            self.logger.error("Error in scan worker %s: %s", worker_name, str(e))
        
        self.logger.debug("Scan worker %s stopped", worker_name)
    
    async def _execute_scan_task(self, task: ScanTask, worker_name: str):
        """Execute a single scan task."""
        start_time = time.time()
        
        try:
            # Update task status
            task.status = ScanStatus.RUNNING
            task.started_at = datetime.now(timezone.utc)
            
            self.logger.debug(
                "Worker %s executing scan %s for %s (%s)",
                worker_name, task.scan_id, task.bookmaker, task.sport.value
            )
            
            # Execute scan with timeout
            result = await asyncio.wait_for(
                self._perform_scan(task),
                timeout=self.scan_timeout
            )
            
            # Update task with result
            task.completed_at = datetime.now(timezone.utc)
            task.execution_time = time.time() - start_time
            task.opportunities = result.opportunities_found
            task.confidence_score = result.confidence_score
            
            if result.success:
                task.status = ScanStatus.COMPLETED
                self.logger.debug(
                    "Scan %s completed successfully in %.2fs (%d opportunities)",
                    task.scan_id, task.execution_time, len(result.opportunities_found)
                )
            else:
                task.status = ScanStatus.FAILED
                task.error_message = result.error_message
                self.logger.warning(
                    "Scan %s failed: %s",
                    task.scan_id, result.error_message
                )
            
            # Record metrics
            self.metrics.record_scan_result(result)
            
        except asyncio.TimeoutError:
            task.status = ScanStatus.FAILED
            task.error_message = f"Scan timed out after {self.scan_timeout} seconds"
            task.completed_at = datetime.now(timezone.utc)
            task.execution_time = time.time() - start_time
            
            self.logger.error("Scan %s timed out", task.scan_id)
            self._record_engine_failure("timeout")
            
        except Exception as e:
            task.status = ScanStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)
            task.execution_time = time.time() - start_time
            
            self.logger.error("Scan %s failed with exception: %s", task.scan_id, str(e))
            self.logger.error("Traceback: %s", traceback.format_exc())
            
            # Check if we should retry
            if self.retry_failed_scans and task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = ScanStatus.RETRYING
                
                # Re-queue the task with exponential backoff
                retry_delay = 2 ** task.retry_count
                self.logger.info("Retrying scan %s in %d seconds (attempt %d/%d)",
                               task.scan_id, retry_delay, task.retry_count, task.max_retries)
                
                await asyncio.sleep(retry_delay)
                
                # Reset status for retry
                task.status = ScanStatus.PENDING
                task.started_at = None
                await self.priority_queue.put(task)
                
                self.metrics.retried_scans += 1
                return
            
            self._record_engine_failure("exception")
        
        finally:
            # Move to completed scans and remove from active
            with self._lock:
                if task.scan_id in self.active_scans:
                    self.completed_scans.append(task)
                    del self.active_scans[task.scan_id]
            
            # Emit event
            await self._emit_event('scan_completed', task.to_dict())
    
    async def _perform_scan(self, task: ScanTask) -> ScanResult:
        """
        Perform the actual scan operation.
        
        This is where the VLM extraction would be called.
        For now, this is a placeholder that simulates the scan.
        """
        try:
            # Simulate scan delay
            await asyncio.sleep(0.1)
            
            # This would be the actual VLM extraction call
            # For now, return a mock result
            return ScanResult(
                scan_id=task.scan_id,
                success=True,
                bookmaker=task.bookmaker,
                sport=task.sport,
                opportunities_found=[],
                execution_time=task.execution_time,
                confidence_score=0.8
            )
            
        except Exception as e:
            return ScanResult(
                scan_id=task.scan_id,
                success=False,
                bookmaker=task.bookmaker,
                sport=task.sport,
                error_message=str(e),
                execution_time=task.execution_time,
                retry_count=task.retry_count
            )
    
    def _can_execute_scan(self) -> bool:
        """Check if we can execute a new scan (circuit breaker check)."""
        if not self.enable_circuit_breaker:
            return True
        
        now = time.time()
        
        # Clean old failures outside the window
        while self.engine_failures and (now - self.engine_failures[0]) > self.engine_circuit_breaker_failure_window:
            self.engine_failures.popleft()
        
        # Check if we've exceeded the failure threshold
        if len(self.engine_failures) >= self.engine_circuit_breaker_failure_threshold:
            return False
        
        return True
    
    def _record_engine_failure(self, failure_type: str):
        """Record an engine failure for circuit breaker purposes."""
        self.engine_failures.append(time.time())
        self.logger.warning(f"Engine failure recorded: {failure_type}")
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to registered handlers."""
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                self.logger.error("Error in event handler: %s", str(e))
    
    def get_queue_summary(self) -> Dict[str, Any]:
        """Get a summary of the current queue state."""
        with self._lock:
            queue_size = self.priority_queue.qsize()
            active_scans = len(self.active_scans)
            
            # Count scans by priority
            priority_counts = defaultdict(int)
            for task in self.active_scans.values():
                priority_counts[task.priority.value] += 1
            
            # Count scans by status
            status_counts = defaultdict(int)
            for task in self.active_scans.values():
                status_counts[task.status.value] += 1
            
            return {
                'queue_size': queue_size,
                'active_scans': active_scans,
                'priority_distribution': dict(priority_counts),
                'status_distribution': dict(status_counts),
                'max_concurrent_scans': self.max_concurrent_scans,
                'utilization': active_scans / self.max_concurrent_scans
            }
    
    async def health_check(self) -> bool:
        """Perform a health check of the scanner engine."""
        try:
            # Check if workers are still running
            running_workers = 0
            for worker in self._scan_workers:
                if not worker.done():
                    running_workers += 1
            
            if running_workers < self.max_concurrent_scans / 2:
                self.logger.warning("Less than half of scan workers are running")
                return False
            
            # Check circuit breaker state
            if not self._can_execute_scan():
                self.logger.warning("Engine circuit breaker is open")
                return False
            
            # Check memory usage (basic check)
            import psutil
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 90:
                self.logger.warning(f"High memory usage: {memory_percent}%")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error("Health check failed: %s", str(e))
            return False
    
    def reset_metrics(self):
        """Reset all engine metrics."""
        with self._lock:
            self.metrics.reset()
        self.logger.info("Engine metrics reset")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def scan_task(
    scan_type: ScanType = ScanType.BOOKMAKER_SCAN,
    priority: ScanPriority = ScanPriority.NORMAL
):
    """Decorator to convert a function into a scan task."""
    def decorator(func):
        @wraps(func)
        async def wrapper(engine: ScannerEngine, *args, **kwargs):
            # Extract scan parameters from function arguments
            # This is a simplified implementation
            bookmaker = kwargs.get('bookmaker', 'unknown')
            sport = kwargs.get('sport', Sport.FOOTBALL)
            image_data = kwargs.get('image_data', b'')
            
            # Add task to engine
            task_id = engine.add_scan_task(
                scan_type=scan_type,
                bookmaker=bookmaker,
                sport=sport,
                image_data=image_data,
                priority=priority
            )
            
            # Wait for completion
            while True:
                status = engine.get_scan_status(task_id)
                if status and status['status'] in ['completed', 'failed', 'cancelled']:
                    break
                await asyncio.sleep(0.1)
            
            return status
        
        return wrapper
    return decorator


async def create_scan_batch(
    engine: ScannerEngine,
    scan_requests: List[Dict[str, Any]],
    batch_priority: ScanPriority = ScanPriority.NORMAL
) -> List[UUID]:
    """
    Create a batch of scan tasks.
    
    Args:
        engine: Scanner engine instance
        scan_requests: List of scan request dictionaries
        batch_priority: Priority for all tasks in the batch
        
    Returns:
        List of task IDs
    """
    task_ids = []
    
    for request in scan_requests:
        task_id = engine.add_scan_task(
            scan_type=ScanType(request['scan_type']),
            bookmaker=request['bookmaker'],
            sport=Sport(request['sport']),
            image_data=request['image_data'],
            priority=batch_priority,
            market_type=request.get('market_type', 'match_winner'),
            event_name=request.get('event_name', '')
        )
        task_ids.append(task_id)
    
    return task_ids


def get_engine_performance_summary(engine: ScannerEngine) -> Dict[str, Any]:
    """Get a comprehensive performance summary of the scanner engine."""
    metrics = engine.get_engine_metrics()
    queue_summary = engine.get_queue_summary()
    
    return {
        'metrics': metrics,
        'queue_summary': queue_summary,
        'health_status': 'healthy',  # This would be calculated based on metrics
        'recommendations': [
            'Monitor queue utilization',
            'Check for high error rates',
            'Optimize scan frequencies'
        ]
    }