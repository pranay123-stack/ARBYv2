"""
Data Synchronizer - Real-time data synchronization system for maintaining consistency.

This module provides a comprehensive system for real-time synchronization of market data
across multiple bookmaker sources, with automatic failover, conflict resolution, and
state management.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging
import hashlib
from collections import defaultdict, deque
import heapq
import weakref

try:
    # Try relative imports first (when used as part of arbitech package)
    from .data_aggregator import DataAggregator, get_data_aggregator, AggregatedEvent, MarketData
    from .bookmaker_manager import BookmakerManager, get_bookmaker_manager, BookmakerStatus
    from ..utils.logger import get_logger
except ImportError:
    # Fall back to absolute imports (when used standalone)
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    from data_aggregator import DataAggregator, get_data_aggregator, AggregatedEvent, MarketData
    from bookmaker_manager import BookmakerManager, get_bookmaker_manager, BookmakerStatus
    
    try:
        from utils.logger import get_logger
    except ImportError:
        import logging
        def get_logger(name):
            return logging.getLogger(name)


logger = get_logger(__name__)


class SyncStatus(str, Enum):
    """Synchronization status states."""
    IDLE = "idle"
    SYNCING = "syncing"
    STREAMING = "streaming"
    PAUSED = "paused"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving data conflicts."""
    LATEST_TIMESTAMP = "latest_timestamp"
    PRIORITY_SOURCE = "priority_source"
    CONSENSUS_BASED = "consensus_based"
    MANUAL_REVIEW = "manual_review"
    REJECT_CONFLICTING = "reject_conflicting"


class SyncEventType(str, Enum):
    """Types of synchronization events."""
    DATA_UPDATE = "data_update"
    CONFLICT_DETECTED = "conflict_detected"
    SOURCE_DISCONNECT = "source_disconnect"
    SOURCE_RECONNECT = "source_reconnect"
    SYNC_COMPLETE = "sync_complete"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class SyncEvent:
    """Represents a synchronization event."""
    event_id: str
    event_type: SyncEventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    priority: int = 0  # Higher number = higher priority
    processing_start: Optional[datetime] = None
    processing_end: Optional[datetime] = None
    error: Optional[str] = None
    
    def __lt__(self, other):
        """Priority queue ordering."""
        return self.priority > other.priority  # Inverted for max-heap behavior


@dataclass
class DataChange:
    """Represents a change in market data."""
    market_id: str
    event_id: str
    field_name: str
    old_value: Any
    new_value: Any
    source: str
    timestamp: datetime
    confidence: float = 1.0
    change_type: str = "update"  # update, insert, delete


@dataclass
class SyncState:
    """Current synchronization state for an event."""
    event_id: str
    sync_status: SyncStatus = SyncStatus.IDLE
    last_sync_time: Optional[datetime] = None
    last_data_timestamp: Optional[datetime] = None
    active_sources: Set[str] = field(default_factory=set)
    source_heartbeats: Dict[str, datetime] = field(default_factory=dict)
    pending_changes: List[DataChange] = field(default_factory=list)
    conflict_count: int = 0
    error_count: int = 0
    consecutive_failures: int = 0
    data_version: int = 0
    sync_latency_ms: float = 0.0
    
    # Performance metrics
    total_syncs: int = 0
    successful_syncs: int = 0
    avg_sync_time_ms: float = 0.0
    data_freshness_score: float = 100.0


class ConflictDetector:
    """Detects and analyzes data conflicts across sources."""
    
    def __init__(self, conflict_threshold: float = 0.1):
        self.conflict_threshold = conflict_threshold
    
    def detect_conflicts(self, 
                        current_data: MarketData, 
                        new_data: MarketData,
                        source_name: str) -> List[DataChange]:
        """Detect conflicts between current and new market data."""
        conflicts = []
        
        # Compare odds for each outcome
        current_odds_map = {odds.outcome: odds for odds in current_data.odds}
        new_odds_map = {odds.outcome: odds for odds in new_data.odds}
        
        # Check for updated odds
        for outcome in set(current_odds_map.keys()) | set(new_odds_map.keys()):
            current_odds = current_odds_map.get(outcome)
            new_odds = new_odds_map.get(outcome)
            
            if current_odds and new_odds:
                # Compare odds values
                if abs(current_odds.odds - new_odds.odds) > self.conflict_threshold * current_odds.odds:
                    change = DataChange(
                        market_id=current_data.market_id,
                        event_id=current_data.event_id,
                        field_name=f"odds_{outcome}",
                        old_value=current_odds.odds,
                        new_value=new_odds.odds,
                        source=source_name,
                        timestamp=datetime.utcnow(),
                        confidence=self._calculate_confidence(current_odds, new_odds)
                    )
                    conflicts.append(change)
            
            elif current_odds and not new_odds:
                # Outcome removed
                change = DataChange(
                    market_id=current_data.market_id,
                    event_id=current_data.event_id,
                    field_name=f"outcome_{outcome}",
                    old_value=current_odds,
                    new_value=None,
                    source=source_name,
                    timestamp=datetime.utcnow()
                )
                conflicts.append(change)
            
            elif not current_odds and new_odds:
                # New outcome added
                change = DataChange(
                    market_id=current_data.market_id,
                    event_id=current_data.event_id,
                    field_name=f"outcome_{outcome}",
                    old_value=None,
                    new_value=new_odds,
                    source=source_name,
                    timestamp=datetime.utcnow()
                )
                conflicts.append(change)
        
        return conflicts
    
    def _calculate_confidence(self, current_odds, new_odds) -> float:
        """Calculate confidence score for a data change."""
        # Higher confidence for newer timestamps and higher source reliability
        time_factor = 1.0
        if new_odds.last_updated and current_odds.last_updated:
            time_diff = (new_odds.last_updated - current_odds.last_updated).total_seconds()
            time_factor = min(1.0, time_diff / 300)  # Max confidence for 5+ minutes
        
        reliability_factor = new_odds.source_reliability / 100.0
        
        return (time_factor + reliability_factor) / 2.0


class ConflictResolver:
    """Resolves conflicts using various strategies."""
    
    def __init__(self, strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LATEST_TIMESTAMP):
        self.strategy = strategy
    
    def resolve_conflicts(self, 
                         conflicts: List[DataChange], 
                         event_data: AggregatedEvent,
                         source_priorities: Dict[str, int]) -> List[DataChange]:
        """Resolve conflicts using the configured strategy."""
        if not conflicts:
            return []
        
        if self.strategy == ConflictResolutionStrategy.LATEST_TIMESTAMP:
            return self._resolve_by_timestamp(conflicts)
        
        elif self.strategy == ConflictResolutionStrategy.PRIORITY_SOURCE:
            return self._resolve_by_priority(conflicts, source_priorities)
        
        elif self.strategy == ConflictResolutionStrategy.CONSENSUS_BASED:
            return self._resolve_by_consensus(conflicts, event_data)
        
        elif self.strategy == ConflictResolutionStrategy.REJECT_CONFLICTING:
            return self._resolve_by_rejection(conflicts)
        
        else:
            # Manual review - mark all as requiring review
            for conflict in conflicts:
                conflict.change_type = "manual_review"
            return conflicts
    
    def _resolve_by_timestamp(self, conflicts: List[DataChange]) -> List[DataChange]:
        """Keep the most recent changes."""
        # Group conflicts by field
        field_conflicts = defaultdict(list)
        for conflict in conflicts:
            field_conflicts[conflict.field_name].append(conflict)
        
        resolved = []
        for field_name, field_conflict_list in field_conflicts.items():
            if len(field_conflict_list) == 1:
                resolved.append(field_conflict_list[0])
            else:
                # Keep the most recent
                most_recent = max(field_conflict_list, key=lambda x: x.timestamp)
                resolved.append(most_recent)
        
        return resolved
    
    def _resolve_by_priority(self, 
                           conflicts: List[DataChange], 
                           source_priorities: Dict[str, int]) -> List[DataChange]:
        """Keep changes from highest priority sources."""
        field_conflicts = defaultdict(list)
        for conflict in conflicts:
            field_conflicts[conflict.field_name].append(conflict)
        
        resolved = []
        for field_name, field_conflict_list in field_conflicts.items():
            if len(field_conflict_list) == 1:
                resolved.append(field_conflict_list[0])
            else:
                # Get highest priority source
                highest_priority = max(
                    field_conflict_list, 
                    key=lambda x: source_priorities.get(x.source, 0)
                )
                resolved.append(highest_priority)
        
        return resolved
    
    def _resolve_by_consensus(self, 
                            conflicts: List[DataChange], 
                            event_data: AggregatedEvent) -> List[DataChange]:
        """Use consensus-based resolution."""
        # This would involve comparing against consensus odds
        # For now, keep the most recent changes
        return self._resolve_by_timestamp(conflicts)
    
    def _resolve_by_rejection(self, conflicts: List[DataChange]) -> List[DataChange]:
        """Reject conflicting changes."""
        return []  # No changes accepted


class StreamProcessor:
    """Processes real-time data streams from multiple sources."""
    
    def __init__(self, max_buffer_size: int = 1000):
        self.max_buffer_size = max_buffer_size
        self.event_buffers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_buffer_size))
        self.buffer_timestamps: Dict[str, datetime] = {}
        self.processors: List[Callable] = []
    
    def add_stream_processor(self, processor: Callable):
        """Add a stream data processor."""
        self.processors.append(processor)
    
    async def process_stream_data(self, 
                                event_id: str, 
                                source_data: Dict[str, Any], 
                                source_name: str) -> Optional[MarketData]:
        """Process incoming stream data."""
        try:
            # Parse stream data
            market_data = await self._parse_stream_data(source_data, source_name)
            
            if not market_data:
                return None
            
            # Add to buffer
            self.event_buffers[event_id].append({
                'data': market_data,
                'source': source_name,
                'timestamp': datetime.utcnow()
            })
            
            # Process through registered processors
            for processor in self.processors:
                try:
                    await processor(event_id, market_data, source_name)
                except Exception as e:
                    logger.warning(f"Stream processor failed: {e}")
            
            return market_data
        
        except Exception as e:
            logger.error(f"Stream processing failed for {event_id}: {e}")
            return None
    
    async def _parse_stream_data(self, 
                               source_data: Dict[str, Any], 
                               source_name: str) -> Optional[MarketData]:
        """Parse stream data into MarketData format."""
        # This would implement real stream data parsing
        # For now, return a mock MarketData
        return MarketData(
            sport=source_data.get('sport'),
            event_name=source_data.get('event_name', 'Unknown'),
            event_id=source_data.get('event_id'),
            market_type=source_data.get('market_type', 'unknown'),
            market_id=source_data.get('market_id'),
            start_time=datetime.utcnow(),
            participants=source_data.get('participants', []),
            odds=source_data.get('odds', []),
            last_update=datetime.utcnow()
        )
    
    def get_recent_data(self, event_id: str, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent data from buffer."""
        buffer = self.event_buffers.get(event_id, deque())
        return list(buffer)[-count:] if buffer else []
    
    def get_buffer_stats(self, event_id: str) -> Dict[str, Any]:
        """Get buffer statistics."""
        buffer = self.event_buffers.get(event_id, deque())
        return {
            'buffer_size': len(buffer),
            'max_size': buffer.maxlen,
            'last_update': self.buffer_timestamps.get(event_id)
        }


class DataSynchronizer:
    """Real-time data synchronization system."""
    
    def __init__(self, 
                 data_aggregator: Optional[DataAggregator] = None,
                 conflict_resolution_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LATEST_TIMESTAMP,
                 max_concurrent_syncs: int = 50):
        
        self.data_aggregator = data_aggregator or DataAggregator()
        self.logger = get_logger(__name__)
        
        # Conflict management
        self.conflict_detector = ConflictDetector()
        self.conflict_resolver = ConflictResolver(conflict_resolution_strategy)
        
        # Stream processing
        self.stream_processor = StreamProcessor()
        self.stream_processor.add_stream_processor(self._handle_stream_data)
        
        # Synchronization state
        self.sync_states: Dict[str, SyncState] = {}
        self.event_queues: Dict[str, asyncio.Queue] = defaultdict(lambda: asyncio.Queue())
        self.sync_workers: Dict[str, asyncio.Task] = {}
        
        # Event management
        self.sync_events = asyncio.PriorityQueue()
        self.event_subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Performance tracking
        self.performance_stats = {
            'total_syncs': 0,
            'successful_syncs': 0,
            'conflicts_detected': 0,
            'conflicts_resolved': 0,
            'average_latency_ms': 0.0,
            'data_freshness_score': 100.0
        }
        
        # Configuration
        self.max_concurrent_syncs = max_concurrent_syncs
        self.sync_timeout = 30  # seconds
        self.health_check_interval = 60  # seconds
        self.data_freshness_threshold = 5  # minutes
        
        # Control flags
        self.synchronizer_active = False
        self.event_processor_task: Optional[asyncio.Task] = None
        self.health_monitor_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.sync_complete_callbacks: List[Callable] = []
        self.conflict_callbacks: List[Callable] = []
        self.error_callbacks: List[Callable] = []
    
    async def initialize(self):
        """Initialize the data synchronizer."""
        try:
            await self.data_aggregator.initialize()
            self.synchronizer_active = True
            
            # Start event processing
            self.event_processor_task = asyncio.create_task(self._event_processor_loop())
            
            # Start health monitoring
            self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
            
            self.logger.info("Data synchronizer initialized")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize data synchronizer: {e}")
            raise
    
    async def start_synchronization(self, event_ids: List[str], 
                                  sync_mode: str = "continuous") -> Dict[str, bool]:
        """Start synchronization for specified events."""
        results = {}
        
        for event_id in event_ids:
            try:
                if event_id not in self.sync_states:
                    self.sync_states[event_id] = SyncState(event_id=event_id)
                
                sync_state = self.sync_states[event_id]
                
                if sync_state.sync_status == SyncStatus.IDLE:
                    sync_state.sync_status = SyncStatus.SYNCING
                    
                    # Start sync worker
                    if event_id not in self.sync_workers:
                        worker_task = asyncio.create_task(
                            self._sync_worker(event_id, sync_mode)
                        )
                        self.sync_workers[event_id] = worker_task
                    
                    results[event_id] = True
                    self.logger.info(f"Started synchronization for event {event_id}")
                else:
                    results[event_id] = False
                    self.logger.warning(f"Already synchronizing event {event_id}")
            
            except Exception as e:
                self.logger.error(f"Failed to start sync for event {event_id}: {e}")
                results[event_id] = False
        
        return results
    
    async def stop_synchronization(self, event_ids: List[str]) -> Dict[str, bool]:
        """Stop synchronization for specified events."""
        results = {}
        
        for event_id in event_ids:
            try:
                if event_id in self.sync_states:
                    sync_state = self.sync_states[event_id]
                    sync_state.sync_status = SyncStatus.IDLE
                
                if event_id in self.sync_workers:
                    worker_task = self.sync_workers[event_id]
                    worker_task.cancel()
                    del self.sync_workers[event_id]
                    
                    results[event_id] = True
                    self.logger.info(f"Stopped synchronization for event {event_id}")
                else:
                    results[event_id] = False
                    self.logger.warning(f"No active sync worker for event {event_id}")
            
            except Exception as e:
                self.logger.error(f"Failed to stop sync for event {event_id}: {e}")
                results[event_id] = False
        
        return results
    
    async def _sync_worker(self, event_id: str, sync_mode: str):
        """Individual event synchronization worker."""
        sync_state = self.sync_states[event_id]
        
        try:
            while (sync_state.sync_status == SyncStatus.SYNCING or 
                   sync_state.sync_status == SyncStatus.STREAMING):
                
                start_time = time.time()
                
                try:
                    # Perform synchronization
                    success = await self._sync_event_data(event_id)
                    
                    # Update performance metrics
                    sync_time = (time.time() - start_time) * 1000
                    sync_state.sync_latency_ms = sync_time
                    sync_state.total_syncs += 1
                    
                    if success:
                        sync_state.successful_syncs += 1
                        sync_state.consecutive_failures = 0
                        sync_state.last_sync_time = datetime.utcnow()
                    else:
                        sync_state.consecutive_failures += 1
                    
                    # Calculate rolling average sync time
                    if sync_state.avg_sync_time_ms == 0:
                        sync_state.avg_sync_time_ms = sync_time
                    else:
                        sync_state.avg_sync_time_ms = (
                            sync_state.avg_sync_time_ms * 0.8 + sync_time * 0.2
                        )
                    
                    # Calculate data freshness score
                    if sync_state.last_data_timestamp:
                        age_minutes = (
                            datetime.utcnow() - sync_state.last_data_timestamp
                        ).total_seconds() / 60
                        sync_state.data_freshness_score = max(0, 100 - (age_minutes * 2))
                    
                    # Update performance stats
                    self.performance_stats['total_syncs'] += 1
                    if success:
                        self.performance_stats['successful_syncs'] += 1
                    
                    # Handle sync mode
                    if sync_mode == "continuous":
                        await asyncio.sleep(5)  # Sync every 5 seconds
                    elif sync_mode == "adaptive":
                        # Adaptive sync based on event importance
                        await asyncio.sleep(self._calculate_adaptive_interval(sync_state))
                    else:
                        break  # One-time sync
                
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Sync worker error for {event_id}: {e}")
                    sync_state.error_count += 1
                    sync_state.consecutive_failures += 1
                    
                    if sync_state.consecutive_failures >= 5:
                        sync_state.sync_status = SyncStatus.ERROR
                        break
                    
                    await asyncio.sleep(10)  # Wait before retrying
        
        except Exception as e:
            self.logger.error(f"Sync worker failed for {event_id}: {e}")
        
        finally:
            # Clean up
            sync_state.sync_status = SyncStatus.IDLE
            if event_id in self.sync_workers:
                del self.sync_workers[event_id]
    
    async def _sync_event_data(self, event_id: str) -> bool:
        """Synchronize data for a specific event."""
        try:
            sync_state = self.sync_states[event_id]
            
            # Get current event data
            current_event = await self.data_aggregator.get_event_data(event_id)
            if not current_event:
                return False
            
            # Collect updates from all sources
            bookmaker_manager = await get_bookmaker_manager()
            source_data = await bookmaker_manager.collect_data_concurrent(
                sports=[current_event.sport.value]
            )
            
            # Process updates and detect conflicts
            conflicts_detected = 0
            changes_applied = 0
            
            for bookmaker_name, data in source_data.items():
                if data.get('status') != 'success':
                    continue
                
                # Parse source data
                new_market_data = await self._parse_source_data(data, bookmaker_name)
                if not new_market_data:
                    continue
                
                # Compare with current data
                for market_type, new_market in new_market_data.items():
                    if market_type in current_event.markets:
                        current_market = current_event.markets[market_type]
                        
                        # Detect conflicts
                        conflicts = self.conflict_detector.detect_conflicts(
                            current_market, new_market, bookmaker_name
                        )
                        
                        if conflicts:
                            conflicts_detected += len(conflicts)
                            self.performance_stats['conflicts_detected'] += 1
                            
                            # Resolve conflicts
                            source_priorities = self._get_source_priorities()
                            resolved_changes = self.conflict_resolver.resolve_conflicts(
                                conflicts, current_event, source_priorities
                            )
                            
                            # Apply changes
                            for change in resolved_changes:
                                await self._apply_data_change(current_market, change)
                                changes_applied += 1
                            self.performance_stats['conflicts_resolved'] += len(resolved_changes)
                
                # Update source heartbeat
                sync_state.source_heartbeats[bookmaker_name] = datetime.utcnow()
            
            # Update event metadata
            current_event.last_updated = datetime.utcnow()
            current_event.processing_time_ms += sync_state.sync_latency_ms
            
            # Emit sync event
            sync_event = SyncEvent(
                event_id=event_id,
                event_type=SyncEventType.SYNC_COMPLETE,
                source="data_synchronizer",
                data={
                    'conflicts_detected': conflicts_detected,
                    'changes_applied': changes_applied,
                    'sync_latency_ms': sync_state.sync_latency_ms
                }
            )
            await self._emit_sync_event(sync_event)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Event sync failed for {event_id}: {e}")
            return False
    
    async def _parse_source_data(self, source_data: Dict[str, Any], source_name: str) -> Dict[str, MarketData]:
        """Parse source data into MarketData format."""
        # This would implement detailed source data parsing
        # For now, return an empty dict
        return {}
    
    async def _apply_data_change(self, market_data: MarketData, change: DataChange):
        """Apply a data change to market data."""
        try:
            if change.field_name.startswith("odds_"):
                outcome = change.field_name[5:]  # Remove "odds_" prefix
                
                if change.new_value is None:
                    # Remove outcome
                    market_data.odds = [o for o in market_data.odds if o.outcome != outcome]
                else:
                    # Update or add outcome
                    existing_odds = next(
                        (o for o in market_data.odds if o.outcome == outcome), None
                    )
                    
                    if existing_odds:
                        existing_odds.odds = change.new_value
                        existing_odds.last_updated = datetime.utcnow()
                    else:
                        # Add new outcome
                        from .data_aggregator import MarketOdds
                        new_odds = MarketOdds(
                            bookmaker=change.source,
                            outcome=outcome,
                            odds=change.new_value,
                            last_updated=datetime.utcnow()
                        )
                        market_data.odds.append(new_odds)
            
            # Update market timestamp
            market_data.last_update = datetime.utcnow()
        
        except Exception as e:
            self.logger.error(f"Failed to apply data change: {e}")
    
    def _get_source_priorities(self) -> Dict[str, int]:
        """Get source priorities for conflict resolution."""
        # This would get priorities from configuration or health metrics
        return {
            'bet365': 10,
            'william_hill': 8,
            'ladbrokes': 7,
            'betfair': 9,
            'pinnacle': 9,
            '1xbet': 6
        }
    
    def _calculate_adaptive_interval(self, sync_state: SyncState) -> float:
        """Calculate adaptive sync interval based on event state."""
        # Higher frequency for important events or when data is stale
        base_interval = 5.0
        
        if sync_state.data_freshness_score < 50:
            return 1.0  # Very frequent updates for stale data
        elif sync_state.data_freshness_score < 80:
            return 2.0  # Frequent updates for moderately fresh data
        elif len(sync_state.active_sources) < 3:
            return 3.0  # More frequent when few sources available
        else:
            return base_interval
    
    async def _event_processor_loop(self):
        """Process synchronization events from priority queue."""
        while self.synchronizer_active:
            try:
                # Get next event (blocks if empty)
                sync_event = await asyncio.wait_for(self.sync_events.get(), timeout=1.0)
                
                # Process the event
                await self._process_sync_event(sync_event)
                
                # Mark task as done
                self.sync_events.task_done()
            
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Event processor error: {e}")
    
    async def _process_sync_event(self, event: SyncEvent):
        """Process a synchronization event."""
        try:
            event.processing_start = datetime.utcnow()
            
            # Emit to subscribers
            subscribers = self.event_subscribers.get(event.event_id, [])
            for subscriber in subscribers:
                try:
                    if asyncio.iscoroutinefunction(subscriber):
                        await subscriber(event)
                    else:
                        subscriber(event)
                except Exception as e:
                    self.logger.warning(f"Event subscriber failed: {e}")
            
            # Handle specific event types
            if event.event_type == SyncEventType.ERROR_OCCURRED:
                await self._handle_error_event(event)
            elif event.event_type == SyncEventType.CONFLICT_DETECTED:
                await self._handle_conflict_event(event)
            elif event.event_type == SyncEventType.SOURCE_DISCONNECT:
                await self._handle_disconnect_event(event)
            
            event.processing_end = datetime.utcnow()
        
        except Exception as e:
            self.logger.error(f"Event processing failed: {e}")
    
    async def _handle_stream_data(self, event_id: str, market_data: MarketData, source_name: str):
        """Handle incoming stream data."""
        try:
            sync_state = self.sync_states.get(event_id)
            if not sync_state:
                return
            
            # Add source to active sources
            sync_state.active_sources.add(source_name)
            sync_state.source_heartbeats[source_name] = datetime.utcnow()
            
            # Check if data is newer than current
            if (not sync_state.last_data_timestamp or 
                market_data.last_update > sync_state.last_data_timestamp):
                
                sync_state.last_data_timestamp = market_data.last_update
                
                # Emit data update event
                update_event = SyncEvent(
                    event_id=event_id,
                    event_type=SyncEventType.DATA_UPDATE,
                    source=source_name,
                    data={
                        'market_id': market_data.market_id,
                        'market_type': market_data.market_type,
                        'timestamp': market_data.last_update.isoformat()
                    },
                    priority=5  # High priority for stream data
                )
                await self._emit_sync_event(update_event)
        
        except Exception as e:
            self.logger.error(f"Stream data handling failed: {e}")
    
    async def _handle_error_event(self, event: SyncEvent):
        """Handle error events."""
        error_msg = event.data.get('error', 'Unknown error')
        self.logger.error(f"Synchronization error for {event.event_id}: {error_msg}")
        
        # Notify error callbacks
        for callback in self.error_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                self.logger.error(f"Error callback failed: {e}")
    
    async def _handle_conflict_event(self, event: SyncEvent):
        """Handle conflict events."""
        conflicts = event.data.get('conflicts', [])
        self.logger.warning(f"Data conflicts detected for {event.event_id}: {len(conflicts)} conflicts")
        
        # Notify conflict callbacks
        for callback in self.conflict_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                self.logger.error(f"Conflict callback failed: {e}")
    
    async def _handle_disconnect_event(self, event: SyncEvent):
        """Handle source disconnect events."""
        source_name = event.source
        self.logger.warning(f"Source disconnected: {source_name}")
        
        # Remove from active sources
        for sync_state in self.sync_states.values():
            sync_state.active_sources.discard(source_name)
    
    async def _emit_sync_event(self, event: SyncEvent):
        """Emit a synchronization event."""
        await self.sync_events.put(event)
    
    async def _health_monitor_loop(self):
        """Monitor health of synchronization processes."""
        while self.synchronizer_active:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _perform_health_checks(self):
        """Perform health checks on synchronization processes."""
        current_time = datetime.utcnow()
        
        # Check worker health
        failed_workers = []
        
        for event_id, task in self.sync_workers.items():
            if task.done():
                failed_workers.append(event_id)
                continue
            
            # Check heartbeat for event
            sync_state = self.sync_states.get(event_id)
            if not sync_state:
                continue
            
            # Check if event hasn't synced recently
            if (sync_state.last_sync_time and 
                current_time - sync_state.last_sync_time > timedelta(minutes=5)):
                
                self.logger.warning(f"Event {event_id} hasn't synced in 5+ minutes")
                
                # Emit error event
                error_event = SyncEvent(
                    event_id=event_id,
                    event_type=SyncEventType.ERROR_OCCURRED,
                    data={'error': 'Stale data detected'},
                    priority=10
                )
                await self._emit_sync_event(error_event)
        
        # Clean up failed workers
        for event_id in failed_workers:
            if event_id in self.sync_workers:
                del self.sync_workers[event_id]
            
            if event_id in self.sync_states:
                self.sync_states[event_id].sync_status = SyncStatus.ERROR
    
    # Public API methods
    
    def subscribe_to_events(self, event_id: str, callback: Callable):
        """Subscribe to events for a specific event."""
        self.event_subscribers[event_id].append(callback)
    
    def unsubscribe_from_events(self, event_id: str, callback: Callable):
        """Unsubscribe from events."""
        if event_id in self.event_subscribers:
            try:
                self.event_subscribers[event_id].remove(callback)
            except ValueError:
                pass
    
    def add_sync_complete_callback(self, callback: Callable):
        """Add callback for sync completion."""
        self.sync_complete_callbacks.append(callback)
    
    def add_conflict_callback(self, callback: Callable):
        """Add callback for conflicts."""
        self.conflict_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """Add callback for errors."""
        self.error_callbacks.append(callback)
    
    def get_sync_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get synchronization status for an event."""
        sync_state = self.sync_states.get(event_id)
        if not sync_state:
            return None
        
        return {
            'event_id': event_id,
            'sync_status': sync_state.sync_status,
            'last_sync_time': sync_state.last_sync_time.isoformat() if sync_state.last_sync_time else None,
            'active_sources': list(sync_state.active_sources),
            'consecutive_failures': sync_state.consecutive_failures,
            'data_freshness_score': sync_state.data_freshness_score,
            'sync_latency_ms': sync_state.sync_latency_ms,
            'success_rate': (
                sync_state.successful_syncs / max(1, sync_state.total_syncs)
            ) * 100
        }
    
    def get_all_sync_status(self) -> Dict[str, Dict[str, Any]]:
        """Get synchronization status for all events."""
        return {event_id: self.get_sync_status(event_id) 
                for event_id in self.sync_states.keys()}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get synchronization performance statistics."""
        if self.performance_stats['total_syncs'] > 0:
            success_rate = (
                self.performance_stats['successful_syncs'] / 
                self.performance_stats['total_syncs']
            ) * 100
        else:
            success_rate = 0
        
        return {
            **self.performance_stats,
            'success_rate': success_rate,
            'active_syncs': len(self.sync_workers),
            'total_monitored_events': len(self.sync_states)
        }
    
    async def pause_synchronization(self, event_ids: List[str] = None):
        """Pause synchronization for specified events or all events."""
        if event_ids is None:
            # Pause all
            for sync_state in self.sync_states.values():
                if sync_state.sync_status in [SyncStatus.SYNCING, SyncStatus.STREAMING]:
                    sync_state.sync_status = SyncStatus.PAUSED
            self.logger.info("Paused all synchronizations")
        else:
            # Pause specific events
            for event_id in event_ids:
                if event_id in self.sync_states:
                    sync_state = self.sync_states[event_id]
                    if sync_state.sync_status in [SyncStatus.SYNCING, SyncStatus.STREAMING]:
                        sync_state.sync_status = SyncStatus.PAUSED
            self.logger.info(f"Paused synchronizations for events: {event_ids}")
    
    async def resume_synchronization(self, event_ids: List[str] = None):
        """Resume synchronization for specified events or all events."""
        if event_ids is None:
            # Resume all
            for sync_state in self.sync_states.values():
                if sync_state.sync_status == SyncStatus.PAUSED:
                    sync_state.sync_status = SyncStatus.SYNCING
            self.logger.info("Resumed all synchronizations")
        else:
            # Resume specific events
            for event_id in event_ids:
                if event_id in self.sync_states:
                    sync_state = self.sync_states[event_id]
                    if sync_state.sync_status == SyncStatus.PAUSED:
                        sync_state.sync_status = SyncStatus.SYNCING
            self.logger.info(f"Resumed synchronizations for events: {event_ids}")
    
    async def shutdown(self):
        """Shutdown the data synchronizer."""
        self.logger.info("Shutting down data synchronizer...")
        
        # Stop accepting new events
        self.synchronizer_active = False
        
        # Cancel all workers
        for task in self.sync_workers.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.sync_workers:
            await asyncio.gather(*self.sync_workers.values(), return_exceptions=True)
        
        # Cancel background tasks
        if self.event_processor_task:
            self.event_processor_task.cancel()
            try:
                await self.event_processor_task
            except asyncio.CancelledError:
                pass
        
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Clear queues and buffers
        self.event_queues.clear()
        self.event_subscribers.clear()
        
        self.logger.info("Data synchronizer shutdown complete")


# Global instance
_data_synchronizer: Optional[DataSynchronizer] = None


async def get_data_synchronizer() -> DataSynchronizer:
    """Get global data synchronizer instance."""
    global _data_synchronizer
    
    if _data_synchronizer is None:
        data_aggregator = await get_data_aggregator()
        _data_synchronizer = DataSynchronizer(data_aggregator)
        await _data_synchronizer.initialize()
    
    return _data_synchronizer


async def shutdown_data_synchronizer():
    """Shutdown global data synchronizer."""
    global _data_synchronizer
    
    if _data_synchronizer:
        await _data_synchronizer.shutdown()
        _data_synchronizer = None