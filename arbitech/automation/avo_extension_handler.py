"""
AVO Extension Handler - Handler for Chrome extension communication
Provides message passing, event handling, and extension API integration
for seamless operation with the Matrix Error Logger extension.
"""

import asyncio
import json
import logging
import threading
import time
import uuid
import websockets
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import queue
import weakref

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Chrome extension message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    EVENT = "event"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    SYNC = "sync"


class ConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ExtensionMessage:
    """Extension message structure"""
    message_id: str
    message_type: MessageType
    source: str
    destination: str
    action: str
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    priority: int = 5
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class TabOperation:
    """Tab operation request"""
    operation_id: str
    operation_type: str  # create, close, update, get_info
    tab_id: Optional[int]
    parameters: Dict[str, Any]
    timestamp: datetime
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ExtensionConfiguration:
    """Extension configuration settings"""
    extension_id: str
    extension_name: str
    version: str
    websocket_url: str
    api_endpoint: str
    authentication_token: Optional[str]
    max_message_size: int = 1024 * 1024  # 1MB
    heartbeat_interval: float = 30.0
    connection_timeout: float = 10.0
    retry_attempts: int = 3
    retry_delay: float = 5.0
    enabled_features: List[str]
    permissions: List[str]


class WebSocketHandler:
    """WebSocket handler for extension communication"""
    
    def __init__(self, config: ExtensionConfiguration):
        self.config = config
        self.connection_state = ConnectionState.DISCONNECTED
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.message_queue: queue.Queue = queue.PriorityQueue()
        self.response_handlers: Dict[str, Callable] = {}
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.running = False
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.reconnect_task: Optional[asyncio.Task] = None
        
        # Connection metrics
        self.connection_attempts = 0
        self.last_successful_connection: Optional[datetime] = None
        self.total_messages_sent = 0
        self.total_messages_received = 0
        self.total_errors = 0
        
        logger.info(f"WebSocket handler initialized for {config.extension_name}")
    
    async def start(self):
        """Start WebSocket handler"""
        self.running = True
        
        # Start connection
        await self._connect()
        
        # Start message processing
        asyncio.create_task(self._process_messages())
        
        # Start heartbeat
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info("WebSocket handler started")
    
    async def stop(self):
        """Stop WebSocket handler"""
        self.running = False
        
        # Cancel tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        if self.reconnect_task:
            self.reconnect_task.cancel()
        
        # Close WebSocket connection
        if self.websocket:
            await self.websocket.close()
        
        self.connection_state = ConnectionState.DISCONNECTED
        logger.info("WebSocket handler stopped")
    
    async def _connect(self):
        """Establish WebSocket connection"""
        try:
            self.connection_state = ConnectionState.CONNECTING
            self.connection_attempts += 1
            
            # Connect to extension WebSocket
            self.websocket = await websockets.connect(
                self.config.websocket_url,
                timeout=self.config.connection_timeout
            )
            
            self.connection_state = ConnectionState.CONNECTED
            self.last_successful_connection = datetime.now()
            
            logger.info(f"Connected to extension WebSocket (attempt {self.connection_attempts})")
            
            # Send authentication if configured
            if self.config.authentication_token:
                await self._authenticate()
            
            self.connection_state = ConnectionState.AUTHENTICATED
            
        except Exception as e:
            self.connection_state = ConnectionState.FAILED
            self.total_errors += 1
            logger.error(f"Failed to connect to extension: {e}")
            
            # Schedule reconnection
            if self.running:
                self.reconnect_task = asyncio.create_task(self._schedule_reconnect())
    
    async def _authenticate(self):
        """Authenticate with extension"""
        if not self.websocket:
            return
        
        auth_message = ExtensionMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.REQUEST,
            source="avo_interface",
            destination=self.config.extension_id,
            action="authenticate",
            payload={"token": self.config.authentication_token},
            timestamp=datetime.now()
        )
        
        await self._send_message(auth_message)
        self.connection_state = ConnectionState.AUTHENTICATING
    
    async def _schedule_reconnect(self):
        """Schedule reconnection attempt"""
        try:
            await asyncio.sleep(self.config.retry_delay)
            if self.running and self.connection_state == ConnectionState.FAILED:
                await self._connect()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Reconnection error: {e}")
    
    async def _process_messages(self):
        """Process incoming and outgoing messages"""
        while self.running:
            try:
                # Process incoming messages
                if self.websocket:
                    try:
                        message_data = await asyncio.wait_for(
                            self.websocket.recv(), 
                            timeout=1.0
                        )
                        await self._handle_incoming_message(message_data)
                    except asyncio.TimeoutError:
                        pass  # No message received
                    except Exception as e:
                        logger.error(f"Error receiving message: {e}")
                        self.total_errors += 1
                
                # Process outgoing messages
                if not self.message_queue.empty():
                    try:
                        _, message = self.message_queue.get_nowait()
                        await self._send_message(message)
                    except queue.Empty:
                        pass
                    except Exception as e:
                        logger.error(f"Error sending message: {e}")
                        self.total_errors += 1
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                self.total_errors += 1
                await asyncio.sleep(1.0)
    
    async def _handle_incoming_message(self, message_data: str):
        """Handle incoming WebSocket message"""
        try:
            self.total_messages_received += 1
            
            # Parse message
            message_dict = json.loads(message_data)
            
            # Convert to ExtensionMessage
            message = ExtensionMessage(
                message_id=message_dict.get('message_id'),
                message_type=MessageType(message_dict.get('message_type')),
                source=message_dict.get('source'),
                destination=message_dict.get('destination'),
                action=message_dict.get('action'),
                payload=message_dict.get('payload', {}),
                timestamp=datetime.fromisoformat(message_dict.get('timestamp')),
                correlation_id=message_dict.get('correlation_id'),
                priority=message_dict.get('priority', 5),
                timeout=message_dict.get('timeout', 30.0),
                retry_count=message_dict.get('retry_count', 0),
                max_retries=message_dict.get('max_retries', 3)
            )
            
            # Handle message based on type
            if message.message_type == MessageType.RESPONSE:
                await self._handle_response(message)
            elif message.message_type == MessageType.EVENT:
                await self._handle_event(message)
            elif message.message_type == MessageType.NOTIFICATION:
                await self._handle_notification(message)
            elif message.message_type == MessageType.HEARTBEAT:
                await self._handle_heartbeat(message)
            else:
                logger.warning(f"Unknown message type: {message.message_type}")
            
        except Exception as e:
            logger.error(f"Error handling incoming message: {e}")
            self.total_errors += 1
    
    async def _handle_response(self, message: ExtensionMessage):
        """Handle response message"""
        if message.correlation_id in self.response_handlers:
            handler = self.response_handlers[message.correlation_id]
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Response handler error: {e}")
            
            # Remove handler after execution
            del self.response_handlers[message.correlation_id]
    
    async def _handle_event(self, message: ExtensionMessage):
        """Handle event message"""
        if message.action in self.message_handlers:
            for handler in self.message_handlers[message.action]:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Event handler error for {message.action}: {e}")
    
    async def _handle_notification(self, message: ExtensionMessage):
        """Handle notification message"""
        logger.info(f"Extension notification: {message.action} - {message.payload}")
        
        if message.action in self.message_handlers:
            for handler in self.message_handlers[message.action]:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Notification handler error: {e}")
    
    async def _handle_heartbeat(self, message: ExtensionMessage):
        """Handle heartbeat message"""
        # Respond with heartbeat
        response = ExtensionMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.HEARTBEAT,
            source="avo_interface",
            destination=message.source,
            action="heartbeat_response",
            payload={"timestamp": datetime.now().isoformat()},
            timestamp=datetime.now(),
            correlation_id=message.message_id
        )
        
        await self._send_message(response)
    
    async def _send_message(self, message: ExtensionMessage):
        """Send message through WebSocket"""
        if not self.websocket or self.connection_state not in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]:
            raise Exception("WebSocket not connected")
        
        try:
            # Convert to dictionary
            message_dict = asdict(message)
            message_dict['message_type'] = message.message_type.value
            message_dict['timestamp'] = message.timestamp.isoformat()
            
            # Serialize message
            message_data = json.dumps(message_dict)
            
            # Check message size
            if len(message_data) > self.config.max_message_size:
                raise Exception(f"Message too large: {len(message_data)} bytes")
            
            # Send message
            await self.websocket.send(message_data)
            self.total_messages_sent += 1
            
        except Exception as e:
            self.total_errors += 1
            logger.error(f"Error sending message: {e}")
            raise
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        while self.running:
            try:
                if self.connection_state == ConnectionState.AUTHENTICATED:
                    heartbeat = ExtensionMessage(
                        message_id=str(uuid.uuid4()),
                        message_type=MessageType.HEARTBEAT,
                        source="avo_interface",
                        destination=self.config.extension_id,
                        action="heartbeat",
                        payload={"timestamp": datetime.now().isoformat()},
                        timestamp=datetime.now()
                    )
                    
                    await self._send_message(heartbeat)
                
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5.0)
    
    def send_message(self, message: ExtensionMessage) -> str:
        """Send message (non-async for convenience)"""
        # Add to queue with priority (lower number = higher priority)
        self.message_queue.put((message.priority, message))
        return message.message_id
    
    def register_response_handler(self, correlation_id: str, handler: Callable):
        """Register response handler for specific correlation ID"""
        self.response_handlers[correlation_id] = handler
    
    def register_message_handler(self, action: str, handler: Callable):
        """Register message handler for specific action"""
        if action not in self.message_handlers:
            self.message_handlers[action] = []
        self.message_handlers[action].append(handler)
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get connection status and metrics"""
        return {
            'state': self.connection_state.value,
            'connection_attempts': self.connection_attempts,
            'last_successful_connection': self.last_successful_connection.isoformat() if self.last_successful_connection else None,
            'total_messages_sent': self.total_messages_sent,
            'total_messages_received': self.total_messages_received,
            'total_errors': self.total_errors,
            'queue_size': self.message_queue.qsize(),
            'active_handlers': len(self.response_handlers) + sum(len(handlers) for handlers in self.message_handlers.values())
        }


class TabOperationHandler:
    """Handler for tab operations through extension"""
    
    def __init__(self, ws_handler: WebSocketHandler, config: ExtensionConfiguration):
        self.ws_handler = ws_handler
        self.config = config
        self.pending_operations: Dict[str, TabOperation] = {}
        self.operation_handlers: Dict[str, Callable] = {}
        self.lock = threading.RLock()
        
        # Register for tab-related messages
        self.ws_handler.register_message_handler('tab_created', self._handle_tab_created)
        self.ws_handler.register_message_handler('tab_closed', self._handle_tab_closed)
        self.ws_handler.register_message_handler('tab_updated', self._handle_tab_updated)
        self.ws_handler.register_message_handler('tab_error', self._handle_tab_error)
        
        logger.info("Tab operation handler initialized")
    
    async def create_tab(self, url: str, tab_type: str = "normal", 
                        metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """Create a new tab through extension"""
        try:
            operation_id = str(uuid.uuid4())
            operation = TabOperation(
                operation_id=operation_id,
                operation_type="create",
                tab_id=None,
                parameters={
                    "url": url,
                    "tab_type": tab_type,
                    "metadata": metadata or {}
                },
                timestamp=datetime.now(),
                status="pending"
            )
            
            with self.lock:
                self.pending_operations[operation_id] = operation
            
            # Send create tab request
            message = ExtensionMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.REQUEST,
                source="avo_interface",
                destination=self.config.extension_id,
                action="create_tab",
                payload={
                    "url": url,
                    "tab_type": tab_type,
                    "metadata": metadata or {}
                },
                timestamp=datetime.now(),
                correlation_id=operation_id
            )
            
            self.ws_handler.send_message(message)
            
            # Wait for response with timeout
            result = await self._wait_for_operation_completion(operation_id, timeout=30.0)
            
            if result and result.get('success') and 'tab_id' in result:
                tab_id = result['tab_id']
                logger.info(f"Created tab {tab_id} for {url}")
                return tab_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating tab: {e}")
            return None
    
    async def close_tab(self, tab_id: int) -> bool:
        """Close a tab through extension"""
        try:
            operation_id = str(uuid.uuid4())
            operation = TabOperation(
                operation_id=operation_id,
                operation_type="close",
                tab_id=tab_id,
                parameters={},
                timestamp=datetime.now(),
                status="pending"
            )
            
            with self.lock:
                self.pending_operations[operation_id] = operation
            
            # Send close tab request
            message = ExtensionMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.REQUEST,
                source="avo_interface",
                destination=self.config.extension_id,
                action="close_tab",
                payload={"tab_id": tab_id},
                timestamp=datetime.now(),
                correlation_id=operation_id
            )
            
            self.ws_handler.send_message(message)
            
            # Wait for response
            result = await self._wait_for_operation_completion(operation_id, timeout=15.0)
            
            if result and result.get('success'):
                logger.info(f"Closed tab {tab_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error closing tab {tab_id}: {e}")
            return False
    
    async def get_tab_info(self, tab_id: int) -> Optional[Dict[str, Any]]:
        """Get tab information through extension"""
        try:
            operation_id = str(uuid.uuid4())
            operation = TabOperation(
                operation_id=operation_id,
                operation_type="get_info",
                tab_id=tab_id,
                parameters={},
                timestamp=datetime.now(),
                status="pending"
            )
            
            with self.lock:
                self.pending_operations[operation_id] = operation
            
            # Send get tab info request
            message = ExtensionMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.REQUEST,
                source="avo_interface",
                destination=self.config.extension_id,
                action="get_tab_info",
                payload={"tab_id": tab_id},
                timestamp=datetime.now(),
                correlation_id=operation_id
            )
            
            self.ws_handler.send_message(message)
            
            # Wait for response
            result = await self._wait_for_operation_completion(operation_id, timeout=10.0)
            
            if result and result.get('success'):
                return result.get('tab_info')
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting tab info for {tab_id}: {e}")
            return None
    
    async def update_tab(self, tab_id: int, updates: Dict[str, Any]) -> bool:
        """Update tab properties through extension"""
        try:
            operation_id = str(uuid.uuid4())
            operation = TabOperation(
                operation_id=operation_id,
                operation_type="update",
                tab_id=tab_id,
                parameters=updates,
                timestamp=datetime.now(),
                status="pending"
            )
            
            with self.lock:
                self.pending_operations[operation_id] = operation
            
            # Send update tab request
            message = ExtensionMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.REQUEST,
                source="avo_interface",
                destination=self.config.extension_id,
                action="update_tab",
                payload={"tab_id": tab_id, "updates": updates},
                timestamp=datetime.now(),
                correlation_id=operation_id
            )
            
            self.ws_handler.send_message(message)
            
            # Wait for response
            result = await self._wait_for_operation_completion(operation_id, timeout=15.0)
            
            if result and result.get('success'):
                logger.info(f"Updated tab {tab_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating tab {tab_id}: {e}")
            return False
    
    async def _handle_tab_created(self, message: ExtensionMessage):
        """Handle tab created notification"""
        try:
            payload = message.payload
            operation_id = message.correlation_id
            
            if operation_id in self.pending_operations:
                operation = self.pending_operations[operation_id]
                operation.status = "completed"
                operation.result = {
                    "success": True,
                    "tab_id": payload.get("tab_id"),
                    "tab_info": payload.get("tab_info", {})
                }
                
                # Set operation tab_id if available
                if payload.get("tab_id"):
                    operation.tab_id = payload["tab_id"]
                
                logger.info(f"Tab creation completed: {payload.get('tab_id')}")
            
        except Exception as e:
            logger.error(f"Error handling tab created: {e}")
    
    async def _handle_tab_closed(self, message: ExtensionMessage):
        """Handle tab closed notification"""
        try:
            payload = message.payload
            tab_id = payload.get("tab_id")
            
            # Find and complete any pending close operations for this tab
            with self.lock:
                for operation_id, operation in list(self.pending_operations.items()):
                    if operation.operation_type == "close" and operation.tab_id == tab_id:
                        operation.status = "completed"
                        operation.result = {"success": True}
                        logger.info(f"Tab closure completed: {tab_id}")
            
        except Exception as e:
            logger.error(f"Error handling tab closed: {e}")
    
    async def _handle_tab_updated(self, message: ExtensionMessage):
        """Handle tab updated notification"""
        try:
            payload = message.payload
            tab_id = payload.get("tab_id")
            
            # Find and complete any pending update operations for this tab
            with self.lock:
                for operation_id, operation in list(self.pending_operations.items()):
                    if operation.operation_type == "update" and operation.tab_id == tab_id:
                        operation.status = "completed"
                        operation.result = {"success": True}
                        logger.info(f"Tab update completed: {tab_id}")
            
        except Exception as e:
            logger.error(f"Error handling tab updated: {e}")
    
    async def _handle_tab_error(self, message: ExtensionMessage):
        """Handle tab error notification"""
        try:
            payload = message.payload
            operation_id = message.correlation_id
            
            if operation_id in self.pending_operations:
                operation = self.pending_operations[operation_id]
                operation.status = "failed"
                operation.error = payload.get("error", "Unknown error")
                logger.error(f"Tab operation failed: {operation_id} - {operation.error}")
            else:
                # Log general tab errors
                logger.error(f"Tab error: {payload}")
            
        except Exception as e:
            logger.error(f"Error handling tab error: {e}")
    
    async def _wait_for_operation_completion(self, operation_id: str, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Wait for operation completion"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with self.lock:
                if operation_id in self.pending_operations:
                    operation = self.pending_operations[operation_id]
                    if operation.status in ["completed", "failed"]:
                        # Clean up completed operation
                        result = operation.result
                        del self.pending_operations[operation_id]
                        return result
            
            await asyncio.sleep(0.1)
        
        # Timeout - remove operation
        with self.lock:
            if operation_id in self.pending_operations:
                del self.pending_operations[operation_id]
        
        logger.warning(f"Operation timeout: {operation_id}")
        return None


class AVOExtensionHandler:
    """Main handler for Chrome extension communication"""
    
    def __init__(self, extension_config: Optional[ExtensionConfiguration] = None):
        # Default configuration
        if not extension_config:
            extension_config = ExtensionConfiguration(
                extension_id="matrix_error_logger",
                extension_name="Matrix Error Logger",
                version="1.0",
                websocket_url="ws://localhost:8765",  # Default extension WebSocket port
                api_endpoint="http://localhost:8765",
                authentication_token=None,
                enabled_features=[
                    "tab_management",
                    "error_capture",
                    "network_monitoring",
                    "performance_tracking"
                ],
                permissions=[
                    "tabs",
                    "scripting",
                    "webNavigation",
                    "webRequest",
                    "storage"
                ]
            )
        
        self.config = extension_config
        self.ws_handler = WebSocketHandler(extension_config)
        self.tab_handler = TabOperationHandler(self.ws_handler, extension_config)
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.notification_handlers: Dict[str, Callable] = {}
        
        # State management
        self.is_running = False
        self.connection_status = ConnectionState.DISCONNECTED
        self.message_handlers_active = False
        
        # Metrics
        self.metrics = {
            'total_messages_sent': 0,
            'total_messages_received': 0,
            'total_operations_completed': 0,
            'total_operations_failed': 0,
            'average_response_time': 0.0,
            'last_activity': None,
            'connection_uptime': 0.0
        }
        
        logger.info("AVO Extension Handler initialized")
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register event handler for extension events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler for {event_type}")
    
    def register_notification_handler(self, notification_type: str, handler: Callable):
        """Register notification handler"""
        self.notification_handlers[notification_type] = handler
        logger.info(f"Registered notification handler for {notification_type}")
    
    async def start(self):
        """Start extension handler"""
        try:
            if self.is_running:
                logger.warning("Extension handler already running")
                return
            
            self.is_running = True
            
            # Start WebSocket handler
            await self.ws_handler.start()
            
            # Update connection status
            self.connection_status = self.ws_handler.connection_state
            
            # Start message handlers
            self.message_handlers_active = True
            
            # Register for extension events
            self._register_extension_event_handlers()
            
            # Start monitoring loop
            asyncio.create_task(self._monitoring_loop())
            
            logger.info("AVO Extension Handler started")
            
        except Exception as e:
            logger.error(f"Error starting extension handler: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop extension handler"""
        try:
            self.is_running = False
            self.message_handlers_active = False
            
            # Stop WebSocket handler
            await self.ws_handler.stop()
            
            self.connection_status = ConnectionState.DISCONNECTED
            
            logger.info("AVO Extension Handler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping extension handler: {e}")
    
    def _register_extension_event_handlers(self):
        """Register handlers for extension events"""
        # Tab events
        self.ws_handler.register_message_handler('tab_event', self._handle_extension_event)
        self.ws_handler.register_message_handler('error_event', self._handle_extension_error)
        self.ws_handler.register_message_handler('performance_event', self._handle_extension_performance)
        self.ws_handler.register_message_handler('network_event', self._handle_extension_network)
        
        # Notification events
        for notification_type in ['info', 'warning', 'error']:
            self.ws_handler.register_message_handler(f'notification_{notification_type}', 
                                                   self._handle_extension_notification)
    
    async def _handle_extension_event(self, message: ExtensionMessage):
        """Handle extension event"""
        try:
            event_data = message.payload
            event_type = event_data.get('event_type')
            
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        await handler(event_data)
                    except Exception as e:
                        logger.error(f"Event handler error for {event_type}: {e}")
            
            logger.debug(f"Extension event: {event_type} - {event_data}")
            
        except Exception as e:
            logger.error(f"Error handling extension event: {e}")
    
    async def _handle_extension_error(self, message: ExtensionMessage):
        """Handle extension error"""
        try:
            error_data = message.payload
            error_type = error_data.get('error_type')
            error_message = error_data.get('error_message')
            
            logger.error(f"Extension error ({error_type}): {error_message}")
            
            # Emit to registered error handlers
            if 'extension_error' in self.event_handlers:
                for handler in self.event_handlers['extension_error']:
                    try:
                        await handler(error_data)
                    except Exception as e:
                        logger.error(f"Error handler error: {e}")
            
        except Exception as e:
            logger.error(f"Error handling extension error: {e}")
    
    async def _handle_extension_performance(self, message: ExtensionMessage):
        """Handle extension performance event"""
        try:
            performance_data = message.payload
            logger.debug(f"Extension performance event: {performance_data}")
            
            # Update metrics
            self._update_performance_metrics(performance_data)
            
        except Exception as e:
            logger.error(f"Error handling extension performance: {e}")
    
    async def _handle_extension_network(self, message: ExtensionMessage):
        """Handle extension network event"""
        try:
            network_data = message.payload
            logger.debug(f"Extension network event: {network_data}")
            
            # Process network data as needed
            # This could include API monitoring, request/response logging, etc.
            
        except Exception as e:
            logger.error(f"Error handling extension network: {e}")
    
    async def _handle_extension_notification(self, message: ExtensionMessage):
        """Handle extension notification"""
        try:
            notification_data = message.payload
            notification_type = message.action.replace('notification_', '')
            
            handler = self.notification_handlers.get(notification_type)
            if handler:
                await handler(notification_data)
            else:
                logger.info(f"Extension {notification_type} notification: {notification_data}")
            
        except Exception as e:
            logger.error(f"Error handling extension notification: {e}")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_running:
            try:
                # Update connection status
                self.connection_status = self.ws_handler.connection_state
                
                # Update metrics
                ws_metrics = self.ws_handler.get_connection_status()
                self.metrics.update({
                    'total_messages_sent': ws_metrics['total_messages_sent'],
                    'total_messages_received': ws_metrics['total_messages_received'],
                    'last_activity': datetime.now().isoformat()
                })
                
                # Check for connection issues
                if self.connection_status == ConnectionState.FAILED:
                    logger.warning("Extension connection failed - will retry")
                
                # Clean up old operations
                self._cleanup_old_operations()
                
                await asyncio.sleep(10.0)  # Monitor every 10 seconds
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5.0)
    
    def _update_performance_metrics(self, performance_data: Dict[str, Any]):
        """Update performance metrics from extension"""
        try:
            # Extract performance metrics
            response_time = performance_data.get('response_time', 0)
            memory_usage = performance_data.get('memory_usage', 0)
            cpu_usage = performance_data.get('cpu_usage', 0)
            
            # Update running averages
            current_avg_response = self.metrics['average_response_time']
            if current_avg_response == 0:
                self.metrics['average_response_time'] = response_time
            else:
                self.metrics['average_response_time'] = (current_avg_response * 0.9) + (response_time * 0.1)
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def _cleanup_old_operations(self):
        """Clean up old pending operations"""
        try:
            current_time = datetime.now()
            timeout_threshold = timedelta(minutes=5)
            
            with self.tab_handler.lock:
                operations_to_remove = []
                for operation_id, operation in self.tab_handler.pending_operations.items():
                    if (current_time - operation.timestamp) > timeout_threshold:
                        operations_to_remove.append(operation_id)
                
                for operation_id in operations_to_remove:
                    operation = self.tab_handler.pending_operations[operation_id]
                    operation.status = "timeout"
                    del self.tab_handler.pending_operations[operation_id]
                    logger.warning(f"Cleaned up timeout operation: {operation_id}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old operations: {e}")
    
    # Public API methods
    
    async def create_tab(self, url: str, tab_type: str = "normal", 
                        metadata: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """Create a new tab"""
        if not self.is_running:
            raise Exception("Extension handler not running")
        
        return await self.tab_handler.create_tab(url, tab_type, metadata)
    
    async def close_tab(self, tab_id: int) -> bool:
        """Close a tab"""
        if not self.is_running:
            raise Exception("Extension handler not running")
        
        return await self.tab_handler.close_tab(tab_id)
    
    async def get_tab_info(self, tab_id: int) -> Optional[Dict[str, Any]]:
        """Get tab information"""
        if not self.is_running:
            raise Exception("Extension handler not running")
        
        return await self.tab_handler.get_tab_info(tab_id)
    
    async def update_tab(self, tab_id: int, updates: Dict[str, Any]) -> bool:
        """Update tab properties"""
        if not self.is_running:
            raise Exception("Extension handler not running")
        
        return await self.tab_handler.update_tab(tab_id, updates)
    
    def get_tab_title(self, tab_id: int) -> str:
        """Get tab title"""
        # This would typically require async operation, but for compatibility
        # we provide a synchronous method that may need to be called after
        # the tab info is available
        try:
            # In a real implementation, this would fetch from a cache
            # or make an async call
            return f"Tab {tab_id}"
        except Exception as e:
            logger.error(f"Error getting tab title for {tab_id}: {e}")
            return f"Tab {tab_id}"
    
    def send_message_to_tab(self, tab_id: Optional[int], message_type: str, 
                          payload: Dict[str, Any], message_id: str):
        """Send message to specific tab or broadcast"""
        try:
            if not self.is_running:
                return
            
            message = ExtensionMessage(
                message_id=message_id or str(uuid.uuid4()),
                message_type=MessageType.NOTIFICATION,
                source="avo_interface",
                destination=f"tab_{tab_id}" if tab_id else "broadcast",
                action=message_type,
                payload=payload,
                timestamp=datetime.now()
            )
            
            self.ws_handler.send_message(message)
            
        except Exception as e:
            logger.error(f"Error sending message to tab: {e}")
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get comprehensive connection status"""
        try:
            ws_status = self.ws_handler.get_connection_status()
            
            return {
                'extension_config': {
                    'extension_id': self.config.extension_id,
                    'extension_name': self.config.extension_name,
                    'version': self.config.version,
                    'websocket_url': self.config.websocket_url,
                    'enabled_features': self.config.enabled_features,
                    'permissions': self.config.permissions
                },
                'connection_status': self.connection_status.value,
                'websocket_status': ws_status,
                'tab_operations': {
                    'pending_count': len(self.tab_handler.pending_operations),
                    'active_handlers': len(self.tab_handler.operation_handlers)
                },
                'metrics': self.metrics.copy(),
                'is_running': self.is_running,
                'message_handlers_active': self.message_handlers_active,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_extension_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent extension logs"""
        try:
            # This would typically fetch logs from the extension
            # For now, return a mock structure
            return [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'info',
                    'source': 'extension',
                    'message': 'Extension logs not yet implemented',
                    'data': {}
                }
            ]
        except Exception as e:
            logger.error(f"Error getting extension logs: {e}")
            return []
    
    def update_configuration(self, config_updates: Dict[str, Any]) -> bool:
        """Update extension configuration"""
        try:
            # Update allowed configuration fields
            allowed_fields = [
                'websocket_url', 'api_endpoint', 'authentication_token',
                'heartbeat_interval', 'connection_timeout', 'retry_attempts',
                'retry_delay', 'max_message_size'
            ]
            
            for field, value in config_updates.items():
                if field in allowed_fields:
                    setattr(self.config, field, value)
                    logger.info(f"Updated config field: {field}")
            
            # Restart WebSocket if needed
            if 'websocket_url' in config_updates and self.is_running:
                asyncio.create_task(self._restart_websocket())
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False
    
    async def _restart_websocket(self):
        """Restart WebSocket connection"""
        try:
            await self.ws_handler.stop()
            await asyncio.sleep(2.0)  # Brief pause
            await self.ws_handler.start()
            logger.info("WebSocket restarted")
        except Exception as e:
            logger.error(f"Error restarting WebSocket: {e}")
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Perform health check on extension handler"""
        try:
            current_time = datetime.now()
            
            # Check connection state
            connection_healthy = self.connection_status in [
                ConnectionState.CONNECTED, 
                ConnectionState.AUTHENTICATED
            ]
            
            # Check message queue
            queue_size = self.ws_handler.message_queue.qsize()
            queue_healthy = queue_size < 100
            
            # Check error rate
            total_messages = self.metrics['total_messages_sent'] + self.metrics['total_messages_received']
            error_rate = self.metrics.get('total_errors', 0) / max(total_messages, 1)
            error_rate_healthy = error_rate < 0.1  # Less than 10% error rate
            
            # Overall health
            overall_healthy = connection_healthy and queue_healthy and error_rate_healthy
            
            return {
                'healthy': overall_healthy,
                'connection_healthy': connection_healthy,
                'queue_healthy': queue_healthy,
                'error_rate_healthy': error_rate_healthy,
                'connection_status': self.connection_status.value,
                'queue_size': queue_size,
                'error_rate': error_rate,
                'metrics': self.metrics.copy(),
                'ws_status': self.ws_handler.get_connection_status(),
                'timestamp': current_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export current configuration"""
        try:
            return {
                'config': {
                    'extension_id': self.config.extension_id,
                    'extension_name': self.config.extension_name,
                    'version': self.config.version,
                    'websocket_url': self.config.websocket_url,
                    'api_endpoint': self.config.api_endpoint,
                    'authentication_token': self.config.authentication_token,
                    'max_message_size': self.config.max_message_size,
                    'heartbeat_interval': self.config.heartbeat_interval,
                    'connection_timeout': self.config.connection_timeout,
                    'retry_attempts': self.config.retry_attempts,
                    'retry_delay': self.config.retry_delay,
                    'enabled_features': self.config.enabled_features,
                    'permissions': self.config.permissions
                },
                'metrics': self.metrics.copy(),
                'export_timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            return {'error': str(e)}