"""
AVO Tabs Interface - Main interface for AVO Tabs integration
Provides comprehensive tab management, synchronization, and state coordination
for seamless operation with the Chrome extension.
"""

import asyncio
import json
import logging
import threading
import time
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from datetime import datetime, timedelta
import weakref
import queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TabState(Enum):
    """Tab state enumeration"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    LOADING = "loading"
    ERROR = "error"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class TabType(Enum):
    """Tab type enumeration for bookmaker differentiation"""
    BOOKMAKER_PRIMARY = "bookmaker_primary"
    BOOKMAKER_SECONDARY = "bookmaker_secondary"
    BOOKMAKER_BACKUP = "bookmaker_backup"
    ARBITRAGE_MONITOR = "arbitrage_monitor"
    TRADING_DASHBOARD = "trading_dashboard"
    SYSTEM_MONITOR = "system_monitor"


@dataclass
class TabInfo:
    """Tab information data structure"""
    tab_id: int
    url: str
    title: str
    state: TabState
    tab_type: TabType
    bookmaker_id: Optional[str]
    created_at: datetime
    last_activity: datetime
    health_score: float
    error_count: int
    retry_count: int
    sync_version: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['state'] = self.state.value
        data['tab_type'] = self.tab_type.value
        data['created_at'] = self.created_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        return data


@dataclass
class SyncMessage:
    """Synchronization message structure"""
    message_id: str
    source_tab_id: int
    target_tab_id: Optional[int]
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    priority: int
    ack_required: bool = True
    ack_timeout: float = 30.0


class AVOTabManager:
    """Main tab management interface for AVO Tabs integration"""
    
    def __init__(self, max_tabs: int = 50, sync_interval: float = 1.0):
        self.max_tabs = max_tabs
        self.sync_interval = sync_interval
        self.tabs: Dict[int, TabInfo] = {}
        self.tab_lock = threading.RLock()
        self.sync_queue: queue.Queue = queue.PriorityQueue()
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.running = False
        self.sync_thread: Optional[threading.Thread] = None
        self.extension_handler = None
        self.health_monitor_active = False
        
        # Performance metrics
        self.metrics = {
            'total_tabs_created': 0,
            'total_tabs_closed': 0,
            'total_sync_messages': 0,
            'total_errors': 0,
            'average_health_score': 0.0,
            'last_health_check': None
        }
        
        # Retry configuration
        self.retry_config = {
            'max_retries': 3,
            'retry_delay': 5.0,
            'backoff_multiplier': 2.0,
            'max_retry_delay': 60.0
        }
        
        logger.info("AVO Tabs Interface initialized")
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register event handler for tab events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler for {event_type}")
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to registered handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Event handler error for {event_type}: {e}")
    
    def create_tab(self, url: str, tab_type: TabType, bookmaker_id: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """Create a new tab with AVO Tabs integration"""
        try:
            if len(self.tabs) >= self.max_tabs:
                logger.warning(f"Maximum tabs limit reached ({self.max_tabs})")
                return None
            
            tab_info = TabInfo(
                tab_id=0,  # Will be assigned by browser extension
                url=url,
                title="",
                state=TabState.INITIALIZING,
                tab_type=tab_type,
                bookmaker_id=bookmaker_id,
                created_at=datetime.now(),
                last_activity=datetime.now(),
                health_score=1.0,
                error_count=0,
                retry_count=0,
                sync_version=0,
                metadata=metadata or {}
            )
            
            # Request tab creation through extension
            if self.extension_handler:
                actual_tab_id = self.extension_handler.create_tab(url, tab_type.value, metadata)
                if actual_tab_id:
                    tab_info.tab_id = actual_tab_id
                    tab_info.title = self.extension_handler.get_tab_title(actual_tab_id)
                    with self.tab_lock:
                        self.tabs[actual_tab_id] = tab_info
                    self.metrics['total_tabs_created'] += 1
                    self._emit_event('tab_created', {'tab_info': tab_info.to_dict()})
                    logger.info(f"Created tab {actual_tab_id} for {tab_type.value}")
                    return actual_tab_id
            else:
                logger.warning("Extension handler not available")
                
            return None
            
        except Exception as e:
            logger.error(f"Error creating tab: {e}")
            self.metrics['total_errors'] += 1
            return None
    
    def close_tab(self, tab_id: int) -> bool:
        """Close a specific tab"""
        try:
            with self.tab_lock:
                if tab_id not in self.tabs:
                    logger.warning(f"Tab {tab_id} not found")
                    return False
                
                tab_info = self.tabs[tab_id]
                if self.extension_handler:
                    success = self.extension_handler.close_tab(tab_id)
                    if success:
                        tab_info.state = TabState.CLOSED
                        tab_info.last_activity = datetime.now()
                        del self.tabs[tab_id]
                        self.metrics['total_tabs_closed'] += 1
                        self._emit_event('tab_closed', {'tab_id': tab_id, 'tab_info': tab_info.to_dict()})
                        logger.info(f"Closed tab {tab_id}")
                        return True
                return False
                
        except Exception as e:
            logger.error(f"Error closing tab {tab_id}: {e}")
            self.metrics['total_errors'] += 1
            return False
    
    def update_tab_state(self, tab_id: int, state: TabState, error_count: Optional[int] = None):
        """Update tab state and metrics"""
        try:
            with self.tab_lock:
                if tab_id in self.tabs:
                    tab_info = self.tabs[tab_id]
                    old_state = tab_info.state
                    tab_info.state = state
                    tab_info.last_activity = datetime.now()
                    
                    if error_count is not None:
                        tab_info.error_count = error_count
                    
                    # Calculate health score based on state and errors
                    tab_info.health_score = self._calculate_health_score(tab_info)
                    
                    if old_state != state:
                        self._emit_event('tab_state_changed', {
                            'tab_id': tab_id,
                            'old_state': old_state.value,
                            'new_state': state.value,
                            'tab_info': tab_info.to_dict()
                        })
                        logger.debug(f"Tab {tab_id} state changed: {old_state.value} -> {state.value}")
                        
        except Exception as e:
            logger.error(f"Error updating tab state for {tab_id}: {e}")
    
    def _calculate_health_score(self, tab_info: TabInfo) -> float:
        """Calculate health score for a tab based on various factors"""
        base_score = 1.0
        
        # Penalize for errors
        error_penalty = min(tab_info.error_count * 0.1, 0.5)
        
        # Adjust for state
        if tab_info.state == TabState.ACTIVE:
            state_multiplier = 1.0
        elif tab_info.state == TabState.LOADING:
            state_multiplier = 0.8
        elif tab_info.state == TabState.ERROR:
            state_multiplier = 0.3
        elif tab_info.state == TabState.SUSPENDED:
            state_multiplier = 0.5
        else:
            state_multiplier = 0.7
        
        # Calculate time since last activity
        time_since_activity = (datetime.now() - tab_info.last_activity).total_seconds()
        activity_penalty = min(time_since_activity / 3600, 0.3)  # Max 30% penalty for 1 hour inactivity
        
        health_score = (base_score - error_penalty - activity_penalty) * state_multiplier
        return max(0.0, min(1.0, health_score))
    
    def get_tab_info(self, tab_id: int) -> Optional[TabInfo]:
        """Get information about a specific tab"""
        with self.tab_lock:
            return self.tabs.get(tab_id)
    
    def get_tabs_by_type(self, tab_type: TabType) -> List[TabInfo]:
        """Get all tabs of a specific type"""
        with self.tab_lock:
            return [tab for tab in self.tabs.values() if tab.tab_type == tab_type]
    
    def get_tabs_by_bookmaker(self, bookmaker_id: str) -> List[TabInfo]:
        """Get all tabs for a specific bookmaker"""
        with self.tab_lock:
            return [tab for tab in self.tabs.values() if tab.bookmaker_id == bookmaker_id]
    
    def send_sync_message(self, source_tab_id: int, target_tab_id: Optional[int],
                         message_type: str, payload: Dict[str, Any],
                         priority: int = 5, ack_required: bool = True) -> str:
        """Send synchronization message between tabs"""
        try:
            message_id = str(uuid.uuid4())
            message = SyncMessage(
                message_id=message_id,
                source_tab_id=source_tab_id,
                target_tab_id=target_tab_id,
                message_type=message_type,
                payload=payload,
                timestamp=datetime.now(),
                priority=priority,
                ack_required=ack_required,
                ack_timeout=30.0
            )
            
            # Add to sync queue (priority queue, lower number = higher priority)
            self.sync_queue.put((priority, message))
            self.metrics['total_sync_messages'] += 1
            
            # Send through extension if available
            if self.extension_handler:
                self.extension_handler.send_message_to_tab(
                    target_tab_id, message_type, payload, message_id
                )
            
            logger.debug(f"Sent sync message {message_id} from {source_tab_id} to {target_tab_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error sending sync message: {e}")
            self.metrics['total_errors'] += 1
            return ""
    
    def process_sync_messages(self):
        """Process pending synchronization messages"""
        while not self.sync_queue.empty():
            try:
                priority, message = self.sync_queue.get_nowait()
                
                # Process message based on type
                if message.message_type == "state_sync":
                    self._handle_state_sync(message)
                elif message.message_type == "data_update":
                    self._handle_data_update(message)
                elif message.message_type == "heartbeat":
                    self._handle_heartbeat(message)
                elif message.message_type == "error_alert":
                    self._handle_error_alert(message)
                else:
                    logger.warning(f"Unknown message type: {message.message_type}")
                    
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error processing sync message: {e}")
    
    def _handle_state_sync(self, message: SyncMessage):
        """Handle state synchronization message"""
        try:
            if message.target_tab_id and message.target_tab_id in self.tabs:
                target_tab = self.tabs[message.target_tab_id]
                # Update target tab state based on source
                if 'state' in message.payload:
                    target_tab.state = TabState(message.payload['state'])
                    target_tab.last_activity = datetime.now()
                if 'health_score' in message.payload:
                    target_tab.health_score = message.payload['health_score']
                target_tab.sync_version += 1
        except Exception as e:
            logger.error(f"Error handling state sync: {e}")
    
    def _handle_data_update(self, message: SyncMessage):
        """Handle data update message"""
        try:
            # Store data update in tab metadata
            if message.target_tab_id and message.target_tab_id in self.tabs:
                tab = self.tabs[message.target_tab_id]
                if 'data_key' in message.payload and 'data_value' in message.payload:
                    tab.metadata[message.payload['data_key']] = message.payload['data_value']
                    tab.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"Error handling data update: {e}")
    
    def _handle_heartbeat(self, message: SyncMessage):
        """Handle heartbeat message"""
        try:
            if message.target_tab_id and message.target_tab_id in self.tabs:
                tab = self.tabs[message.target_tab_id]
                tab.last_activity = datetime.now()
                tab.health_score = max(tab.health_score, 0.8)  # Ensure minimum health
        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")
    
    def _handle_error_alert(self, message: SyncMessage):
        """Handle error alert message"""
        try:
            if message.target_tab_id and message.target_tab_id in self.tabs:
                tab = self.tabs[message.target_tab_id]
                tab.error_count += 1
                tab.health_score = max(0.0, tab.health_score - 0.1)
                tab.last_activity = datetime.now()
                
                # Emit error event
                self._emit_event('tab_error', {
                    'tab_id': message.target_tab_id,
                    'error_info': message.payload,
                    'tab_info': tab.to_dict()
                })
        except Exception as e:
            logger.error(f"Error handling error alert: {e}")
    
    def start_health_monitoring(self):
        """Start background health monitoring"""
        try:
            self.health_monitor_active = True
            self.health_thread = threading.Thread(target=self._health_monitor_loop, daemon=True)
            self.health_thread.start()
            logger.info("Health monitoring started")
        except Exception as e:
            logger.error(f"Error starting health monitoring: {e}")
    
    def stop_health_monitoring(self):
        """Stop background health monitoring"""
        self.health_monitor_active = False
        if hasattr(self, 'health_thread'):
            self.health_thread.join(timeout=5.0)
        logger.info("Health monitoring stopped")
    
    def _health_monitor_loop(self):
        """Background health monitoring loop"""
        while self.health_monitor_active:
            try:
                self.perform_health_check()
                time.sleep(30.0)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                time.sleep(5.0)
    
    def perform_health_check(self):
        """Perform comprehensive health check on all tabs"""
        try:
            current_time = datetime.now()
            unhealthy_tabs = []
            
            with self.tab_lock:
                for tab_id, tab_info in self.tabs.items():
                    # Check for stale tabs
                    time_since_activity = (current_time - tab_info.last_activity).total_seconds()
                    
                    if time_since_activity > 300:  # 5 minutes
                        if tab_info.state == TabState.ACTIVE:
                            tab_info.state = TabState.SUSPENDED
                            unhealthy_tabs.append(tab_id)
                    
                    # Check for high error rates
                    if tab_info.error_count > 10:
                        tab_info.health_score = max(0.0, tab_info.health_score - 0.2)
                        unhealthy_tabs.append(tab_id)
                    
                    # Update health score
                    old_health = tab_info.health_score
                    tab_info.health_score = self._calculate_health_score(tab_info)
                    
                    if old_health != tab_info.health_score:
                        self._emit_event('tab_health_changed', {
                            'tab_id': tab_id,
                            'old_health': old_health,
                            'new_health': tab_info.health_score,
                            'tab_info': tab_info.to_dict()
                        })
            
            # Update metrics
            total_health = sum(tab.health_score for tab in self.tabs.values())
            self.metrics['average_health_score'] = total_health / len(self.tabs) if self.tabs else 0.0
            self.metrics['last_health_check'] = current_time.isoformat()
            
            # Handle unhealthy tabs
            for tab_id in unhealthy_tabs:
                if self.tabs[tab_id].health_score < 0.3:
                    self._emit_event('tab_unhealthy', {
                        'tab_id': tab_id,
                        'reason': 'low_health_score',
                        'tab_info': self.tabs[tab_id].to_dict()
                    })
            
            logger.debug(f"Health check completed. Unhealthy tabs: {len(unhealthy_tabs)}")
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
    
    def start_sync_processing(self):
        """Start synchronization message processing"""
        if not self.running:
            self.running = True
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            logger.info("Sync processing started")
    
    def stop_sync_processing(self):
        """Stop synchronization message processing"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5.0)
        logger.info("Sync processing stopped")
    
    def _sync_loop(self):
        """Background synchronization processing loop"""
        while self.running:
            try:
                self.process_sync_messages()
                time.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                time.sleep(1.0)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            with self.tab_lock:
                tab_stats = {
                    'total_tabs': len(self.tabs),
                    'active_tabs': len([t for t in self.tabs.values() if t.state == TabState.ACTIVE]),
                    'loading_tabs': len([t for t in self.tabs.values() if t.state == TabState.LOADING]),
                    'error_tabs': len([t for t in self.tabs.values() if t.state == TabState.ERROR]),
                    'suspended_tabs': len([t for t in self.tabs.values() if t.state == TabState.SUSPENDED]),
                    'bookmaker_tabs': len([t for t in self.tabs.values() if t.tab_type in [TabType.BOOKMAKER_PRIMARY, TabType.BOOKMAKER_SECONDARY, TabType.BOOKMAKER_BACKUP]]),
                    'monitor_tabs': len([t for t in self.tabs.values() if t.tab_type in [TabType.ARBITRAGE_MONITOR, TabType.TRADING_DASHBOARD, TabType.SYSTEM_MONITOR]])
                }
                
                bookmaker_distribution = {}
                for tab in self.tabs.values():
                    if tab.bookmaker_id:
                        bookmaker_distribution[tab.bookmaker_id] = bookmaker_distribution.get(tab.bookmaker_id, 0) + 1
                
                return {
                    'system_status': 'healthy' if self.metrics['average_health_score'] > 0.7 else 'degraded',
                    'metrics': self.metrics.copy(),
                    'tab_statistics': tab_stats,
                    'bookmaker_distribution': bookmaker_distribution,
                    'extension_connected': self.extension_handler is not None,
                    'health_monitoring_active': self.health_monitor_active,
                    'sync_processing_active': self.running,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def export_tab_configuration(self) -> Dict[str, Any]:
        """Export current tab configuration for backup/transfer"""
        try:
            with self.tab_lock:
                return {
                    'tabs': {str(tab_id): tab.to_dict() for tab_id, tab in self.tabs.items()},
                    'metrics': self.metrics,
                    'retry_config': self.retry_config,
                    'export_timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            return {'error': str(e)}
    
    def import_tab_configuration(self, config: Dict[str, Any]) -> bool:
        """Import tab configuration from backup"""
        try:
            if 'tabs' in config:
                with self.tab_lock:
                    for tab_id_str, tab_data in config['tabs'].items():
                        try:
                            # Reconstruct tab info
                            tab_info = TabInfo(
                                tab_id=int(tab_id_str),
                                url=tab_data['url'],
                                title=tab_data['title'],
                                state=TabState(tab_data['state']),
                                tab_type=TabType(tab_data['tab_type']),
                                bookmaker_id=tab_data.get('bookmaker_id'),
                                created_at=datetime.fromisoformat(tab_data['created_at']),
                                last_activity=datetime.fromisoformat(tab_data['last_activity']),
                                health_score=tab_data['health_score'],
                                error_count=tab_data['error_count'],
                                retry_count=tab_data['retry_count'],
                                sync_version=tab_data['sync_version'],
                                metadata=tab_data['metadata']
                            )
                            self.tabs[int(tab_id_str)] = tab_info
                        except Exception as e:
                            logger.error(f"Error importing tab {tab_id_str}: {e}")
            
            if 'retry_config' in config:
                self.retry_config.update(config['retry_config'])
            
            logger.info("Tab configuration imported successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False
    
    def cleanup_closed_tabs(self):
        """Clean up closed or invalid tabs"""
        try:
            removed_count = 0
            with self.tab_lock:
                tabs_to_remove = []
                for tab_id, tab_info in self.tabs.items():
                    # Remove tabs that have been closed for more than 5 minutes
                    if (tab_info.state == TabState.CLOSED and 
                        (datetime.now() - tab_info.last_activity).total_seconds() > 300):
                        tabs_to_remove.append(tab_id)
                
                for tab_id in tabs_to_remove:
                    del self.tabs[tab_id]
                    removed_count += 1
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} closed tabs")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up tabs: {e}")
            return 0