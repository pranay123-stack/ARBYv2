"""
High-Performance Priority Queue System

Efficient priority queue system for managing arbitrage opportunity queues with
real-time updates and optimized processing. Supports multiple priority strategies
and concurrent access patterns.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any, Tuple, Union
from dataclasses import dataclass, field
from heapq import heappush, heappop, heapify
from collections import defaultdict, deque
from threading import RLock, Condition
from concurrent.futures import ThreadPoolExecutor
import time
import logging
import weakref
from uuid import UUID

from ..storage.models import ArbitrageOpportunity
from .opportunity_ranker import OpportunityScore, RankingStrategy, RankingWeights


logger = logging.getLogger(__name__)


class PriorityStrategy(str, Enum):
    """Available priority strategies for queue management."""
    FIFO = "fifo"
    LIFO = "lifo"
    HIGHEST_SCORE = "highest_score"
    LOWEST_RISK = "lowest_risk"
    MOST_PROFITABLE = "most_profitable"
    URGENT_FIRST = "urgent_first"
    CUSTOM = "custom"


class QueueStatus(str, Enum):
    """Queue status indicators."""
    ACTIVE = "active"
    PAUSED = "paused"
    DRAINING = "draining"
    EMPTY = "empty"
    ERROR = "error"


@dataclass
class QueueEntry:
    """Entry in the priority queue."""
    opportunity_id: UUID
    priority_score: float
    created_at: datetime
    updated_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # For priority comparison
    def __lt__(self, other):
        if isinstance(other, QueueEntry):
            return self.priority_score > other.priority_score  # Reverse for max-heap behavior
        return NotImplemented


@dataclass
class QueueMetrics:
    """Performance metrics for queue operations."""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_wait_time_ms: float = 0.0
    peak_queue_size: int = 0
    current_queue_size: int = 0
    last_operation_time: Optional[datetime] = None
    throughput_per_second: float = 0.0


@dataclass
class BatchProcessingResult:
    """Result of batch processing operation."""
    processed_count: int
    success_count: int
    failure_count: int
    processing_time_ms: float
    average_time_per_item_ms: float
    errors: List[str] = field(default_factory=list)


class PriorityQueue:
    """
    High-performance priority queue for arbitrage opportunities.
    Supports multiple priority strategies and concurrent access.
    """
    
    def __init__(self, 
                 max_size: Optional[int] = None,
                 default_strategy: PriorityStrategy = PriorityStrategy.HIGHEST_SCORE,
                 auto_evict_expired: bool = True,
                 eviction_timeout_minutes: int = 60):
        """
        Initialize the priority queue.
        
        Args:
            max_size: Maximum queue size (None for unlimited)
            default_strategy: Default priority strategy
            auto_evict_expired: Whether to automatically evict expired items
            eviction_timeout_minutes: Timeout for automatic eviction
        """
        self.max_size = max_size
        self.default_strategy = default_strategy
        self.auto_evict_expired = auto_evict_expired
        self.eviction_timeout = timedelta(minutes=eviction_timeout_minutes)
        
        # Thread safety
        self._lock = RLock()
        self._condition = Condition(self._lock)
        
        # Queue storage
        self._heap: List[QueueEntry] = []
        self._id_to_entry: Dict[UUID, QueueEntry] = {}
        self._strategy_functions: Dict[PriorityStrategy, Callable] = {
            PriorityStrategy.FIFO: self._fifo_priority,
            PriorityStrategy.LIFO: self._lifo_priority,
            PriorityStrategy.HIGHEST_SCORE: self._score_priority,
            PriorityStrategy.LOWEST_RISK: self._risk_priority,
            PriorityStrategy.MOST_PROFITABLE: self._profit_priority,
            PriorityStrategy.URGENT_FIRST: self._urgency_priority,
            PriorityStrategy.CUSTOM: self._custom_priority
        }
        
        # Queue status and metrics
        self.status = QueueStatus.ACTIVE
        self.metrics = QueueMetrics()
        
        # Processing callbacks
        self._processing_callbacks: List[Callable] = []
        self._eviction_callbacks: List[Callable] = []
        
        # Performance optimization
        self._last_cleanup = datetime.utcnow()
        self._cleanup_interval = timedelta(minutes=10)
        
        # Batch processing
        self._batch_size = 100
        self._batch_timeout_ms = 1000
        
        logger.info(f"Initialized priority queue with max_size={max_size}, strategy={default_strategy}")
    
    def enqueue(self, 
                opportunity: ArbitrageOpportunity,
                priority_score: Optional[float] = None,
                strategy: Optional[PriorityStrategy] = None,
                custom_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add an opportunity to the queue.
        
        Args:
            opportunity: Arbitrage opportunity to enqueue
            priority_score: Custom priority score (uses opportunity score if None)
            strategy: Priority strategy to use
            custom_metadata: Additional metadata for the entry
            
        Returns:
            True if successfully enqueued, False if rejected or error
        """
        with self._lock:
            try:
                # Check if already exists
                if opportunity.id in self._id_to_entry:
                    logger.warning(f"Opportunity {opportunity.id} already in queue")
                    return False
                
                # Check size limits
                if self.max_size and len(self._heap) >= self.max_size:
                    if not self._evict_expired_entries():
                        logger.warning(f"Queue is at capacity ({self.max_size})")
                        return False
                
                # Calculate priority score
                if priority_score is None:
                    priority_score = self._calculate_default_priority(opportunity)
                
                effective_strategy = strategy or self.default_strategy
                
                # Create queue entry
                entry = QueueEntry(
                    opportunity_id=opportunity.id,
                    priority_score=priority_score,
                    created_at=datetime.utcnow(),
                    custom_metadata=custom_metadata or {}
                )
                
                # Add to queue
                heappush(self._heap, entry)
                self._id_to_entry[opportunity.id] = entry
                
                # Update metrics
                self._update_metrics_enqueue()
                
                # Notify waiting threads
                self._condition.notify()
                
                logger.debug(f"Enqueued opportunity {opportunity.id} with score {priority_score}")
                return True
                
            except Exception as e:
                logger.error(f"Error enqueuing opportunity {opportunity.id}: {e}")
                self.metrics.failed_operations += 1
                return False
    
    def dequeue(self, 
                timeout_seconds: Optional[float] = None,
                strategy: Optional[PriorityStrategy] = None) -> Optional[Tuple[UUID, Dict[str, Any]]]:
        """
        Remove and return the highest priority opportunity from the queue.
        
        Args:
            timeout_seconds: Timeout for blocking dequeue
            strategy: Override priority strategy for this operation
            
        Returns:
            Tuple of (opportunity_id, metadata) or None if timeout/empty
        """
        with self._lock:
            try:
                effective_strategy = strategy or self.default_strategy
                
                start_time = time.time()
                
                while True:
                    # Auto-cleanup expired entries
                    if self._should_cleanup():
                        self._cleanup_expired_entries()
                    
                    # Get next opportunity based on strategy
                    opportunity_id, metadata = self._get_next_opportunity(effective_strategy)
                    
                    if opportunity_id:
                        # Remove from tracking
                        del self._id_to_entry[opportunity_id]
                        
                        # Update metrics
                        self._update_metrics_dequeue(start_time)
                        
                        logger.debug(f"Dequeued opportunity {opportunity_id}")
                        return opportunity_id, metadata
                    
                    # Check timeout
                    if timeout_seconds and (time.time() - start_time) >= timeout_seconds:
                        logger.debug("Dequeue operation timed out")
                        return None
                    
                    # Wait for new items
                    if self.status != QueueStatus.ACTIVE:
                        return None
                    
                    self._condition.wait(timeout=min(timeout_seconds or 1.0, 1.0))
                    
            except Exception as e:
                logger.error(f"Error dequeuing opportunity: {e}")
                self.metrics.failed_operations += 1
                return None
    
    def peek(self, 
             count: int = 1,
             strategy: Optional[PriorityStrategy] = None) -> List[Tuple[UUID, Dict[str, Any]]]:
        """
        Peek at the highest priority opportunities without removing them.
        
        Args:
            count: Number of opportunities to peek at
            strategy: Priority strategy to use
            
        Returns:
            List of (opportunity_id, metadata) tuples
        """
        with self._lock:
            effective_strategy = strategy or self.default_strategy
            
            # Get top opportunities without removing them
            results = []
            temp_heap = self._heap.copy()
            
            for _ in range(min(count, len(temp_heap))):
                if not temp_heap:
                    break
                
                # Get highest priority item (but don't remove from original)
                # For peek, we'll use the custom priority functions
                entry = self._get_top_entry(temp_heap, effective_strategy)
                if entry:
                    results.append((entry.opportunity_id, entry.custom_metadata))
                    # Remove from temp heap to get next
                    temp_heap = [e for e in temp_heap if e.opportunity_id != entry.opportunity_id]
            
            return results
    
    def remove(self, opportunity_id: UUID) -> bool:
        """
        Remove a specific opportunity from the queue.
        
        Args:
            opportunity_id: ID of opportunity to remove
            
        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if opportunity_id in self._id_to_entry:
                del self._id_to_entry[opportunity_id]
                # Note: heap removal is complex, so we'll just mark as invalid
                # A full cleanup will remove it later
                logger.debug(f"Removed opportunity {opportunity_id} from queue")
                return True
            return False
    
    def update_priority(self, 
                       opportunity_id: UUID, 
                       new_priority_score: float,
                       strategy: Optional[PriorityStrategy] = None) -> bool:
        """
        Update the priority score of an opportunity in the queue.
        
        Args:
            opportunity_id: ID of opportunity to update
            new_priority_score: New priority score
            strategy: Priority strategy to apply
            
        Returns:
            True if updated, False if not found
        """
        with self._lock:
            if opportunity_id not in self._id_to_entry:
                return False
            
            entry = self._id_to_entry[opportunity_id]
            entry.priority_score = new_priority_score
            entry.updated_at = datetime.utcnow()
            
            # Rebuild heap (simpler than heap item update)
            heapify(self._heap)
            
            logger.debug(f"Updated priority for opportunity {opportunity_id} to {new_priority_score}")
            return True
    
    def batch_process(self, 
                     processor_func: Callable,
                     batch_size: Optional[int] = None,
                     timeout_seconds: float = 30.0) -> BatchProcessingResult:
        """
        Process opportunities in batches for improved performance.
        
        Args:
            processor_func: Function to process each opportunity
            batch_size: Size of batches to process
            timeout_seconds: Timeout for batch processing
            
        Returns:
            BatchProcessingResult with statistics
        """
        start_time = datetime.utcnow()
        effective_batch_size = batch_size or self._batch_size
        
        processed_count = 0
        success_count = 0
        failure_count = 0
        errors = []
        
        try:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                
                while True:
                    # Get batch of opportunities
                    batch = []
                    for _ in range(effective_batch_size):
                        result = self.dequeue(timeout_seconds=1.0)
                        if result:
                            opportunity_id, metadata = result
                            batch.append((opportunity_id, metadata))
                        else:
                            break
                    
                    if not batch:
                        break  # No more opportunities
                    
                    # Submit batch for processing
                    future = executor.submit(self._process_batch, batch, processor_func)
                    futures.append(future)
                    
                    # Wait for batch completion with timeout
                    for future in futures:
                        try:
                            batch_result = future.result(timeout=timeout_seconds / len(futures))
                            processed_count += batch_result['processed']
                            success_count += batch_result['success']
                            failure_count += batch_result['failure']
                            errors.extend(batch_result['errors'])
                        except Exception as e:
                            errors.append(f"Batch processing error: {str(e)}")
                            failure_count += 1
                    
                    # Clear completed futures
                    futures = [f for f in futures if not f.done()]
        
        except Exception as e:
            errors.append(f"Batch processing error: {str(e)}")
            failure_count += 1
        
        # Calculate metrics
        processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        avg_time_per_item = processing_time_ms / max(1, processed_count)
        
        result = BatchProcessingResult(
            processed_count=processed_count,
            success_count=success_count,
            failure_count=failure_count,
            processing_time_ms=processing_time_ms,
            average_time_per_item_ms=avg_time_per_item,
            errors=errors
        )
        
        logger.info(f"Batch processed {processed_count} opportunities in {processing_time_ms:.2f}ms")
        return result
    
    def get_queue_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the queue state."""
        with self._lock:
            return {
                'status': self.status.value,
                'current_size': len(self._heap),
                'max_size': self.max_size,
                'default_strategy': self.default_strategy.value,
                'max_size_reached': self.max_size and len(self._heap) >= self.max_size,
                'metrics': {
                    'total_operations': self.metrics.total_operations,
                    'successful_operations': self.metrics.successful_operations,
                    'failed_operations': self.metrics.failed_operations,
                    'success_rate': (
                        self.metrics.successful_operations / max(1, self.metrics.total_operations)
                    ),
                    'average_wait_time_ms': self.metrics.average_wait_time_ms,
                    'peak_queue_size': self.metrics.peak_queue_size,
                    'current_queue_size': len(self._heap),
                    'throughput_per_second': self.metrics.throughput_per_second
                },
                'recent_entries': [
                    {
                        'opportunity_id': str(entry.opportunity_id),
                        'priority_score': entry.priority_score,
                        'age_minutes': (datetime.utcnow() - entry.created_at).total_seconds() / 60,
                        'access_count': entry.access_count
                    }
                    for entry in sorted(self._heap, key=lambda x: x.created_at, reverse=True)[:10]
                ]
            }
    
    def pause(self):
        """Pause queue operations."""
        with self._lock:
            self.status = QueueStatus.PAUSED
            self._condition.notify_all()
            logger.info("Priority queue paused")
    
    def resume(self):
        """Resume queue operations."""
        with self._lock:
            self.status = QueueStatus.ACTIVE
            self._condition.notify_all()
            logger.info("Priority queue resumed")
    
    def drain(self, timeout_seconds: float = 60.0) -> int:
        """
        Drain the queue (remove all items).
        
        Args:
            timeout_seconds: Timeout for draining operations
            
        Returns:
            Number of items drained
        """
        with self._lock:
            self.status = QueueStatus.DRAINING
            count = 0
            
            try:
                while self._heap:
                    result = self.dequeue(timeout_seconds=1.0)
                    if result:
                        count += 1
                    else:
                        break
            finally:
                self.status = QueueStatus.ACTIVE
            
            logger.info(f"Drained {count} items from queue")
            return count
    
    def clear(self):
        """Clear all items from the queue."""
        with self._lock:
            self._heap.clear()
            self._id_to_entry.clear()
            logger.info("Cleared priority queue")
    
    def add_processing_callback(self, callback: Callable):
        """Add a callback for when items are processed."""
        self._processing_callbacks.append(callback)
    
    def add_eviction_callback(self, callback: Callable):
        """Add a callback for when items are evicted."""
        self._eviction_callbacks.append(callback)
    
    # Priority calculation methods
    
    def _calculate_default_priority(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate default priority score for an opportunity."""
        # Use profit margin as primary indicator, with time decay
        profit_score = float(opportunity.profit_margin) * 1000
        
        # Apply time decay
        age_minutes = (datetime.utcnow() - opportunity.discovered_at).total_seconds() / 60
        time_decay = max(0.1, 1.0 - (age_minutes / 60))  # Decay over 1 hour
        
        return profit_score * time_decay
    
    def _fifo_priority(self, entry: QueueEntry) -> float:
        """FIFO priority calculation."""
        return entry.created_at.timestamp()
    
    def _lifo_priority(self, entry: QueueEntry) -> float:
        """LIFO priority calculation."""
        return -entry.created_at.timestamp()
    
    def _score_priority(self, entry: QueueEntry) -> float:
        """Highest score priority."""
        return entry.priority_score
    
    def _risk_priority(self, entry: QueueEntry) -> float:
        """Lowest risk priority (placeholder - would need risk data)."""
        return -entry.priority_score  # Inverse for "lowest risk first"
    
    def _profit_priority(self, entry: QueueEntry) -> float:
        """Most profitable priority (same as score for now)."""
        return entry.priority_score
    
    def _urgency_priority(self, entry: QueueEntry) -> float:
        """Urgent first priority based on age."""
        age_minutes = (datetime.utcnow() - entry.created_at).total_seconds() / 60
        return age_minutes
    
    def _custom_priority(self, entry: QueueEntry) -> float:
        """Custom priority based on metadata."""
        return entry.custom_metadata.get('custom_priority', entry.priority_score)
    
    def _get_next_opportunity(self, strategy: PriorityStrategy) -> Optional[Tuple[UUID, Dict[str, Any]]]:
        """Get next opportunity based on priority strategy."""
        if not self._heap:
            return None
        
        # Auto-cleanup expired entries
        self._cleanup_expired_entries()
        
        if not self._heap:
            return None
        
        # Get top entry based on strategy
        priority_func = self._strategy_functions[strategy]
        
        # For non-heap-based strategies, sort the heap
        if strategy in [PriorityStrategy.FIFO, PriorityStrategy.LIFO, PriorityStrategy.URGENT_FIRST]:
            sorted_entries = sorted(self._heap, key=priority_func, reverse=(strategy == PriorityStrategy.URGENT_FIRST))
            if not sorted_entries:
                return None
            entry = sorted_entries[0]
        else:
            # For score-based strategies, heap gives us the highest score
            entry = heappop(self._heap)
        
        if entry:
            return entry.opportunity_id, entry.custom_metadata
        return None
    
    def _get_top_entry(self, heap: List[QueueEntry], strategy: PriorityStrategy) -> Optional[QueueEntry]:
        """Get top entry without removing from heap."""
        if not heap:
            return None
        
        priority_func = self._strategy_functions[strategy]
        
        if strategy in [PriorityStrategy.FIFO, PriorityStrategy.LIFO, PriorityStrategy.URGENT_FIRST]:
            return max(heap, key=priority_func)
        else:
            return max(heap, key=lambda e: e.priority_score)
    
    def _evict_expired_entries(self) -> bool:
        """Evict expired entries to make room for new ones."""
        if not self.auto_evict_expired:
            return False
        
        cutoff_time = datetime.utcnow() - self.eviction_timeout
        
        expired_ids = []
        for entry in self._heap:
            if entry.created_at < cutoff_time:
                expired_ids.append(entry.opportunity_id)
        
        if expired_ids:
            for opp_id in expired_ids:
                if opp_id in self._id_to_entry:
                    del self._id_to_entry[opp_id]
            
            # Remove from heap
            self._heap = [e for e in self._heap if e.opportunity_id not in expired_ids]
            heapify(self._heap)
            
            # Call eviction callbacks
            for callback in self._eviction_callbacks:
                try:
                    callback(expired_ids)
                except Exception as e:
                    logger.error(f"Error in eviction callback: {e}")
            
            logger.info(f"Evicted {len(expired_ids)} expired entries")
            return True
        
        return False
    
    def _cleanup_expired_entries(self):
        """Clean up expired entries (non-blocking)."""
        cutoff_time = datetime.utcnow() - self.eviction_timeout
        
        expired_ids = [entry.opportunity_id for entry in self._heap if entry.created_at < cutoff_time]
        
        if expired_ids:
            for opp_id in expired_ids:
                if opp_id in self._id_to_entry:
                    del self._id_to_entry[opp_id]
            
            self._heap = [e for e in self._heap if e.opportunity_id not in expired_ids]
            heapify(self._heap)
            
            # Call eviction callbacks
            for callback in self._eviction_callbacks:
                try:
                    callback(expired_ids)
                except Exception as e:
                    logger.error(f"Error in eviction callback: {e}")
    
    def _should_cleanup(self) -> bool:
        """Check if cleanup should be performed."""
        return (datetime.utcnow() - self._last_cleanup) >= self._cleanup_interval
    
    def _process_batch(self, 
                      batch: List[Tuple[UUID, Dict[str, Any]]], 
                      processor_func: Callable) -> Dict[str, Any]:
        """Process a batch of opportunities."""
        processed = 0
        success = 0
        failure = 0
        errors = []
        
        for opportunity_id, metadata in batch:
            try:
                processor_func(opportunity_id, metadata)
                processed += 1
                success += 1
            except Exception as e:
                processed += 1
                failure += 1
                errors.append(f"Error processing {opportunity_id}: {str(e)}")
        
        return {
            'processed': processed,
            'success': success,
            'failure': failure,
            'errors': errors
        }
    
    def _update_metrics_enqueue(self):
        """Update metrics for enqueue operation."""
        self.metrics.total_operations += 1
        self.metrics.successful_operations += 1
        self.metrics.current_queue_size = len(self._heap)
        self.metrics.peak_queue_size = max(self.metrics.peak_queue_size, len(self._heap))
        self.metrics.last_operation_time = datetime.utcnow()
    
    def _update_metrics_dequeue(self, start_time: float):
        """Update metrics for dequeue operation."""
        wait_time_ms = (time.time() - start_time) * 1000
        
        # Update average wait time
        total_ops = self.metrics.successful_operations
        current_avg = self.metrics.average_wait_time_ms
        new_avg = ((current_avg * (total_ops - 1)) + wait_time_ms) / total_ops
        self.metrics.average_wait_time_ms = new_avg
        
        # Update throughput (simplified calculation)
        if self.metrics.last_operation_time:
            time_diff = (datetime.utcnow() - self.metrics.last_operation_time).total_seconds()
            if time_diff > 0:
                self.metrics.throughput_per_second = 1.0 / time_diff
        
        self.metrics.current_queue_size = len(self._heap)


class OpportunityQueueManager:
    """
    Manager for multiple priority queues with different strategies.
    """
    
    def __init__(self):
        """Initialize the queue manager."""
        self.queues: Dict[str, PriorityQueue] = {}
        self.default_queue_name = "default"
        self._lock = RLock()
    
    def create_queue(self, 
                    name: str,
                    max_size: Optional[int] = None,
                    strategy: PriorityStrategy = PriorityStrategy.HIGHEST_SCORE,
                    **kwargs) -> PriorityQueue:
        """
        Create a new priority queue.
        
        Args:
            name: Unique name for the queue
            max_size: Maximum queue size
            strategy: Default priority strategy
            **kwargs: Additional arguments for PriorityQueue
            
        Returns:
            Created PriorityQueue instance
        """
        with self._lock:
            if name in self.queues:
                raise ValueError(f"Queue '{name}' already exists")
            
            queue = PriorityQueue(max_size=max_size, default_strategy=strategy, **kwargs)
            self.queues[name] = queue
            
            logger.info(f"Created queue '{name}' with strategy {strategy}")
            return queue
    
    def get_queue(self, name: str) -> Optional[PriorityQueue]:
        """Get a queue by name."""
        return self.queues.get(name)
    
    def get_default_queue(self) -> PriorityQueue:
        """Get or create the default queue."""
        with self._lock:
            if self.default_queue_name not in self.queues:
                self.create_queue(self.default_queue_name)
            return self.queues[self.default_queue_name]
    
    def enqueue(self, 
                opportunity: ArbitrageOpportunity,
                queue_name: Optional[str] = None,
                **kwargs) -> bool:
        """Enqueue opportunity to specified or default queue."""
        queue = self.get_queue(queue_name) if queue_name else self.get_default_queue()
        return queue.enqueue(opportunity, **kwargs)
    
    def dequeue(self, 
                queue_name: Optional[str] = None,
                **kwargs) -> Optional[Tuple[UUID, Dict[str, Any]]]:
        """Dequeue opportunity from specified or default queue."""
        queue = self.get_queue(queue_name) if queue_name else self.get_default_queue()
        return queue.dequeue(**kwargs)
    
    def get_all_queues_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all queues."""
        return {name: queue.get_queue_info() for name, queue in self.queues.items()}
    
    def remove_queue(self, name: str) -> bool:
        """Remove a queue."""
        with self._lock:
            if name in self.queues:
                del self.queues[name]
                logger.info(f"Removed queue '{name}'")
                return True
            return False