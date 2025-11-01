"""
Real-Time Dashboard Update System for ARBitech

This module provides comprehensive real-time dashboard functionality including:
- WebSocket connections for live client updates
- Multi-client support with personalized notifications
- Real-time opportunity streaming with profit calculations
- Live trade execution monitoring with progress tracking
- System health monitoring with instant alerts
- Performance metrics streaming for visualizations
- User presence indicators and collaborative features
- Supabase real-time subscription integration

Author: ARBitech Development Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from uuid import uuid4, UUID
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
import threading
from concurrent.futures import ThreadPoolExecutor

# Import ARBitech components - using try/except for optional dependencies
try:
    from storage.models import (
        ArbitrageOpportunity, Trade, TradeStatus, NotificationType,
        NotificationPriority, Sport, RiskTier
    )
    from storage.supabase_layer import SupabaseDataLayer
except ImportError:
    # Fallback imports for testing
    from enum import Enum
    
    class Sport(str, Enum):
        FOOTBALL = "football"
        BASKETBALL = "basketball"
        TENNIS = "tennis"
    
    class TradeStatus(str, Enum):
        PENDING = "pending"
        PLACING_BETS = "placing_bets"
        FILLED = "filled"
    
    class RiskTier(str, Enum):
        TIER_A = "tier_a"
        TIER_B = "tier_b"
        TIER_C = "tier_c"
        TIER_D = "tier_d"
    
    class NotificationType(str, Enum):
        OPPORTUNITY_ALERT = "opportunity_alert"
        SYSTEM_ERROR = "system_error"
    
    class NotificationPriority(str, Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    # Mock classes for testing
    class ArbitrageOpportunity:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class Trade:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class SupabaseDataLayer:
        def __init__(self, *args, **kwargs):
            pass
        
        async def subscribe(self, *args, **kwargs):
            pass

logger = logging.getLogger(__name__)


class UpdateType(str, Enum):
    """Types of real-time dashboard updates."""
    OPPORTUNITY = "opportunity"
    TRADE = "trade"
    SYSTEM_HEALTH = "system_health"
    PERFORMANCE_METRICS = "performance_metrics"
    USER_PRESENCE = "user_presence"
    NOTIFICATION = "notification"
    PROFIT_CALCULATION = "profit_calculation"
    RISK_ALERT = "risk_alert"
    COLLABORATION = "collaboration"


class ClientStatus(str, Enum):
    """Dashboard client connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    PAUSED = "paused"


@dataclass
class DashboardClient:
    """Represents a connected dashboard client."""
    client_id: UUID
    websocket: websockets.WebSocketServerProtocol
    user_id: Optional[UUID]
    connected_at: datetime
    last_ping: datetime
    preferences: Dict[str, Any]
    status: ClientStatus = ClientStatus.CONNECTED
    subscriptions: Set[UpdateType] = None
    active_view: Optional[str] = None
    collaboration_mode: bool = False
    collab_partners: Set[UUID] = None

    def __post_init__(self):
        if self.subscriptions is None:
            self.subscriptions = set()
        if self.collab_partners is None:
            self.collab_partners = set()


@dataclass
class OpportunityUpdate:
    """Real-time opportunity data for dashboard."""
    opportunity_id: UUID
    sport: Sport
    event_name: str
    profit_margin: float
    expected_profit: float
    risk_tier: RiskTier
    time_remaining: int  # seconds
    quality_score: float
    urgency: str
    legs: List[Dict[str, Any]]
    timestamp: datetime
    status: str  # 'new', 'updated', 'expired', 'executed'
    estimated_execution_time: int  # seconds


@dataclass
class TradeExecutionUpdate:
    """Real-time trade execution progress."""
    trade_id: UUID
    status: TradeStatus
    progress_percentage: float
    completed_legs: int
    total_legs: int
    current_leg: Dict[str, Any]
    estimated_completion: datetime
    profit_projection: float
    risk_assessment: str
    execution_time_elapsed: int  # seconds
    timestamp: datetime
    logs: List[Dict[str, Any]]


@dataclass
class SystemHealthUpdate:
    """System health monitoring data."""
    timestamp: datetime
    status: str  # 'healthy', 'warning', 'critical'
    cpu_usage: float
    memory_usage: float
    active_connections: int
    database_response_time: float
    external_api_latency: Dict[str, float]
    circuit_breakers_active: int
    risk_alerts: int
    system_load: float
    uptime: int  # seconds
    issues: List[Dict[str, Any]]


@dataclass
class PerformanceMetrics:
    """Performance metrics for streaming charts."""
    timestamp: datetime
    timeframe: str  # '1m', '5m', '15m', '1h', '1d'
    total_profit: float
    profit_rate: float  # profit per hour
    win_rate: float
    trade_count: int
    average_trade_time: float
    risk_adjusted_return: float
    sharpe_ratio: float
    max_drawdown: float
    active_opportunities: int
    execution_success_rate: float


class RealTimeDashboard:
    """
    Comprehensive real-time dashboard update system.
    
    Manages WebSocket connections, handles multiple clients, streams live data,
    and provides collaborative features for ARBitech trading dashboard.
    """
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize the real-time dashboard system."""
        self.supabase = SupabaseDataLayer(supabase_url, supabase_key)
        
        # Client management
        self.clients: Dict[UUID, DashboardClient] = {}
        self.user_to_clients: Dict[UUID, Set[UUID]] = defaultdict(set)
        
        # Data streams and buffers
        self.opportunity_stream = deque(maxlen=1000)
        self.trade_stream = deque(maxlen=500)
        self.health_stream = deque(maxlen=300)
        self.metrics_stream = deque(maxlen=1000)
        
        # Performance tracking
        self.update_metrics = {
            'updates_sent': 0,
            'clients_connected': 0,
            'average_latency': 0.0,
            'bytes_sent': 0,
            'errors': 0
        }
        
        # Threading and async management
        self.loop = None
        self.server = None
        self.running = False
        
        # Update processors
        self.processors = {
            UpdateType.OPPORTUNITY: self._process_opportunity_update,
            UpdateType.TRADE: self._process_trade_update,
            UpdateType.SYSTEM_HEALTH: self._process_health_update,
            UpdateType.PERFORMANCE_METRICS: self._process_metrics_update,
            UpdateType.USER_PRESENCE: self._process_presence_update,
            UpdateType.NOTIFICATION: self._process_notification_update,
            UpdateType.RISK_ALERT: self._process_risk_alert,
            UpdateType.COLLABORATION: self._process_collaboration_update
        }
        
        # Data producers
        self.data_producers = []
        
        # Client ping management
        self.ping_interval = 30  # seconds
        self.ping_timeout = 90   # seconds
        
        logger.info("Real-time dashboard system initialized")

    async def start_server(self, host: str = "localhost", port: int = 8765):
        """Start the WebSocket server for real-time updates."""
        self.loop = asyncio.get_event_loop()
        self.running = True
        
        # Start data producers
        self.loop.create_task(self._start_opportunity_producer())
        self.loop.create_task(self._start_trade_producer())
        self.loop.create_task(self._start_health_monitor())
        self.loop.create_task(self._start_metrics_producer())
        self.loop.create_task(self._start_presence_manager())
        self.loop.create_task(self._start_ping_sender())
        
        # Start WebSocket server
        self.server = await websockets.serve(
            self._handle_client_connection,
            host, port,
            ping_interval=20,
            ping_timeout=10,
            max_size=2**20  # 1MB max message size
        )
        
        logger.info(f"Real-time dashboard WebSocket server started on {host}:{port}")
        return self.server

    async def stop_server(self):
        """Stop the WebSocket server and clean up."""
        self.running = False
        
        # Close all client connections
        for client in list(self.clients.values()):
            try:
                await client.websocket.close()
            except Exception as e:
                logger.warning(f"Error closing client connection: {e}")
        
        # Stop server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("Real-time dashboard server stopped")

    async def _handle_client_connection(self, websocket, path):
        """Handle new client WebSocket connection."""
        client_id = uuid4()
        client = DashboardClient(
            client_id=client_id,
            websocket=websocket,
            user_id=None,  # Will be set during authentication
            connected_at=datetime.utcnow(),
            last_ping=datetime.utcnow(),
            preferences={}
        )
        
        self.clients[client_id] = client
        
        try:
            logger.info(f"New dashboard client connected: {client_id}")
            
            # Send welcome message
            await self._send_to_client(client_id, {
                'type': 'connection_established',
                'client_id': str(client_id),
                'timestamp': datetime.utcnow().isoformat(),
                'server_info': {
                    'version': '1.0.0',
                    'capabilities': list(UpdateType),
                    'max_clients': 1000
                }
            })
            
            # Handle client messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._process_client_message(client_id, data)
                except json.JSONDecodeError:
                    await self._send_error(client_id, "Invalid JSON")
                except Exception as e:
                    logger.error(f"Error processing client message: {e}")
                    await self._send_error(client_id, str(e))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected normally")
        except Exception as e:
            logger.error(f"Client {client_id} connection error: {e}")
        finally:
            await self._remove_client(client_id)

    async def _process_client_message(self, client_id: UUID, data: Dict[str, Any]):
        """Process incoming client messages."""
        message_type = data.get('type')
        
        if message_type == 'authenticate':
            await self._authenticate_client(client_id, data)
        elif message_type == 'subscribe':
            await self._handle_subscription(client_id, data)
        elif message_type == 'unsubscribe':
            await self._handle_unsubscription(client_id, data)
        elif message_type == 'update_preferences':
            await self._update_client_preferences(client_id, data)
        elif message_type == 'ping':
            await self._handle_ping(client_id, data)
        elif message_type == 'collaboration':
            await self._handle_collaboration_request(client_id, data)
        elif message_type == 'mark_notification_read':
            await self._handle_notification_read(client_id, data)
        else:
            await self._send_error(client_id, f"Unknown message type: {message_type}")

    async def _authenticate_client(self, client_id: UUID, data: Dict[str, Any]):
        """Authenticate client and set user preferences."""
        try:
            user_id = data.get('user_id')
            if not user_id:
                await self._send_error(client_id, "user_id required")
                return
            
            client = self.clients[client_id]
            client.user_id = UUID(user_id)
            client.preferences = data.get('preferences', {})
            
            # Add to user client mapping
            self.user_to_clients[client.user_id].add(client_id)
            
            # Load user-specific subscriptions from preferences
            if 'subscriptions' in client.preferences:
                for sub_type in client.preferences['subscriptions']:
                    try:
                        client.subscriptions.add(UpdateType(sub_type))
                    except ValueError:
                        logger.warning(f"Unknown subscription type: {sub_type}")
            
            await self._send_to_client(client_id, {
                'type': 'authenticated',
                'user_id': str(user_id),
                'preferences': client.preferences,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Send initial data burst
            await self._send_initial_data(client_id)
            
        except Exception as e:
            logger.error(f"Authentication error for client {client_id}: {e}")
            await self._send_error(client_id, "Authentication failed")

    async def _handle_subscription(self, client_id: UUID, data: Dict[str, Any]):
        """Handle client subscription requests."""
        try:
            client = self.clients[client_id]
            update_types = data.get('update_types', [])
            
            for update_type in update_types:
                try:
                    client.subscriptions.add(UpdateType(update_type))
                except ValueError:
                    await self._send_error(client_id, f"Unknown update type: {update_type}")
                    continue
            
            await self._send_to_client(client_id, {
                'type': 'subscription_confirmed',
                'subscriptions': [ut.value for ut in client.subscriptions],
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Subscription error for client {client_id}: {e}")
            await self._send_error(client_id, "Subscription failed")

    async def _handle_unsubscription(self, client_id: UUID, data: Dict[str, Any]):
        """Handle client unsubscription requests."""
        try:
            client = self.clients[client_id]
            update_types = data.get('update_types', [])
            
            for update_type in update_types:
                try:
                    client.subscriptions.discard(UpdateType(update_type))
                except ValueError:
                    logger.warning(f"Unknown update type for unsubscribe: {update_type}")
            
            await self._send_to_client(client_id, {
                'type': 'unsubscription_confirmed',
                'subscriptions': [ut.value for ut in client.subscriptions],
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Unsubscription error for client {client_id}: {e}")
            await self._send_error(client_id, "Unsubscription failed")

    async def _update_client_preferences(self, client_id: UUID, data: Dict[str, Any]):
        """Update client notification preferences."""
        try:
            client = self.clients[client_id]
            preferences = data.get('preferences', {})
            
            # Update client preferences
            client.preferences.update(preferences)
            
            # Apply immediate changes
            if 'active_view' in preferences:
                client.active_view = preferences['active_view']
            
            if 'collaboration_mode' in preferences:
                client.collaboration_mode = preferences['collaboration_mode']
            
            await self._send_to_client(client_id, {
                'type': 'preferences_updated',
                'preferences': client.preferences,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Broadcast presence update if needed
            if client.user_id:
                await self._broadcast_presence_update(client.user_id)
                
        except Exception as e:
            logger.error(f"Preference update error for client {client_id}: {e}")
            await self._send_error(client_id, "Preference update failed")

    async def _handle_collaboration_request(self, client_id: UUID, data: Dict[str, Any]):
        """Handle collaboration feature requests."""
        try:
            client = self.clients[client_id]
            action = data.get('action')
            
            if action == 'invite':
                partner_id = UUID(data.get('partner_id'))
                await self._send_collaboration_invite(client_id, partner_id)
            elif action == 'accept':
                inviter_id = UUID(data.get('inviter_id'))
                await self._accept_collaboration_invite(client_id, inviter_id)
            elif action == 'decline':
                inviter_id = UUID(data.get('inviter_id'))
                await self._decline_collaboration_invite(client_id, inviter_id)
            elif action == 'leave':
                await self._leave_collaboration(client_id)
                
        except Exception as e:
            logger.error(f"Collaboration error for client {client_id}: {e}")
            await self._send_error(client_id, "Collaboration request failed")

    async def _handle_notification_read(self, client_id: UUID, data: Dict[str, Any]):
        """Handle notification read confirmations."""
        try:
            notification_id = data.get('notification_id')
            if notification_id:
                # Mark notification as read in database
                if self.supabase:
                    await self.supabase.mark_notification_read(UUID(notification_id))
                
                await self._send_to_client(client_id, {
                    'type': 'notification_read_confirmed',
                    'notification_id': notification_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Notification read error for client {client_id}: {e}")

    async def _send_to_client(self, client_id: UUID, data: Dict[str, Any]):
        """Send data to specific client."""
        try:
            client = self.clients.get(client_id)
            if not client or client.status != ClientStatus.CONNECTED:
                return
            
            message = json.dumps(data)
            await client.websocket.send(message)
            
            # Update metrics
            self.update_metrics['updates_sent'] += 1
            self.update_metrics['bytes_sent'] += len(message.encode('utf-8'))
            
        except websockets.exceptions.ConnectionClosed:
            await self._remove_client(client_id)
        except Exception as e:
            logger.error(f"Error sending to client {client_id}: {e}")
            self.update_metrics['errors'] += 1

    async def _broadcast_to_clients(self, client_ids: Set[UUID], data: Dict[str, Any]):
        """Broadcast data to multiple clients."""
        if not client_ids:
            return
        
        message = json.dumps(data)
        tasks = []
        
        for client_id in client_ids:
            client = self.clients.get(client_id)
            if client and client.status == ClientStatus.CONNECTED:
                tasks.append(self._send_to_client(client_id, data))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_error(self, client_id: UUID, error_message: str):
        """Send error message to client."""
        await self._send_to_client(client_id, {
            'type': 'error',
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat()
        })

    async def _send_initial_data(self, client_id: UUID):
        """Send initial data burst to newly authenticated client."""
        client = self.clients[client_id]
        tasks = []
        
        # Send recent opportunities if subscribed
        if UpdateType.OPPORTUNITY in client.subscriptions:
            recent_opportunities = list(self.opportunity_stream)[-10:]
            tasks.append(self._send_to_client(client_id, {
                'type': 'initial_data',
                'category': 'opportunities',
                'data': [asdict(opp) for opp in recent_opportunities]
            }))
        
        # Send recent trades if subscribed
        if UpdateType.TRADE in client.subscriptions:
            recent_trades = list(self.trade_stream)[-5:]
            tasks.append(self._send_to_client(client_id, {
                'type': 'initial_data',
                'category': 'trades',
                'data': [asdict(trade) for trade in recent_trades]
            }))
        
        # Send current system health if subscribed
        if UpdateType.SYSTEM_HEALTH in client.subscriptions and self.health_stream:
            current_health = self.health_stream[-1]
            tasks.append(self._send_to_client(client_id, {
                'type': 'initial_data',
                'category': 'system_health',
                'data': asdict(current_health)
            }))
        
        # Send current metrics if subscribed
        if UpdateType.PERFORMANCE_METRICS in client.subscriptions and self.metrics_stream:
            current_metrics = self.metrics_stream[-1]
            tasks.append(self._send_to_client(client_id, {
                'type': 'initial_data',
                'category': 'performance_metrics',
                'data': asdict(current_metrics)
            }))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _remove_client(self, client_id: UUID):
        """Remove client and clean up resources."""
        client = self.clients.get(client_id)
        if not client:
            return
        
        # Remove from user mapping
        if client.user_id:
            self.user_to_clients[client.user_id].discard(client_id)
            
            # If no more clients for this user, broadcast offline status
            if not self.user_to_clients[client.user_id]:
                await self._broadcast_user_offline(client.user_id)
        
        # Remove from clients
        del self.clients[client_id]
        
        logger.info(f"Removed dashboard client: {client_id}")

    # Data Producers
    async def _start_opportunity_producer(self):
        """Start streaming real-time opportunities."""
        while self.running:
            try:
                # Simulate opportunity updates (replace with real data source)
                opportunity = await self._generate_opportunity_update()
                
                # Add to stream
                self.opportunity_stream.append(opportunity)
                
                # Process update
                await self.processors[UpdateType.OPPORTUNITY](opportunity)
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in opportunity producer: {e}")
                await asyncio.sleep(5)

    async def _start_trade_producer(self):
        """Start streaming real-time trade execution updates."""
        while self.running:
            try:
                # Get active trades and generate updates
                active_trades = await self._get_active_trades()
                
                for trade in active_trades:
                    update = await self._generate_trade_update(trade)
                    
                    # Add to stream
                    self.trade_stream.append(update)
                    
                    # Process update
                    await self.processors[UpdateType.TRADE](update)
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Error in trade producer: {e}")
                await asyncio.sleep(3)

    async def _start_health_monitor(self):
        """Start system health monitoring."""
        while self.running:
            try:
                health_update = await self._generate_health_update()
                
                # Add to stream
                self.health_stream.append(health_update)
                
                # Process update
                await self.processors[UpdateType.SYSTEM_HEALTH](health_update)
                
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(15)

    async def _start_metrics_producer(self):
        """Start performance metrics streaming."""
        while self.running:
            try:
                metrics = await self._generate_performance_metrics()
                
                # Add to stream
                self.metrics_stream.append(metrics)
                
                # Process update
                await self.processors[UpdateType.PERFORMANCE_METRICS](metrics)
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in metrics producer: {e}")
                await asyncio.sleep(60)

    async def _start_presence_manager(self):
        """Manage user presence indicators."""
        while self.running:
            try:
                # Clean up stale presence data
                await self._cleanup_stale_presence()
                
                # Broadcast presence updates
                await self._broadcast_presence_updates()
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in presence manager: {e}")
                await asyncio.sleep(10)

    async def _start_ping_sender(self):
        """Send ping messages to clients."""
        while self.running:
            try:
                await self._ping_all_clients()
                await asyncio.sleep(self.ping_interval)
            except Exception as e:
                logger.error(f"Error in ping sender: {e}")
                await asyncio.sleep(10)

    # Update Processors
    async def _process_opportunity_update(self, opportunity: OpportunityUpdate):
        """Process opportunity update and send to subscribed clients."""
        # Find clients interested in opportunities
        interested_clients = set()
        for client in self.clients.values():
            if (UpdateType.OPPORTUNITY in client.subscriptions and 
                client.status == ClientStatus.CONNECTED):
                
                # Apply user-specific filtering
                if self._should_send_opportunity_to_client(client, opportunity):
                    interested_clients.add(client.client_id)
        
        if interested_clients:
            await self._broadcast_to_clients(interested_clients, {
                'type': 'opportunity_update',
                'data': asdict(opportunity)
            })

    async def _process_trade_update(self, trade_update: TradeExecutionUpdate):
        """Process trade execution update and send to subscribed clients."""
        # Find clients interested in trade updates
        interested_clients = set()
        for client in self.clients.values():
            if (UpdateType.TRADE in client.subscriptions and 
                client.status == ClientStatus.CONNECTED):
                
                # Only send if user has access to this trade
                if self._should_send_trade_to_client(client, trade_update):
                    interested_clients.add(client.client_id)
        
        if interested_clients:
            await self._broadcast_to_clients(interested_clients, {
                'type': 'trade_update',
                'data': asdict(trade_update)
            })

    async def _process_health_update(self, health: SystemHealthUpdate):
        """Process system health update and send to subscribed clients."""
        # Find clients interested in system health
        interested_clients = set()
        for client in self.clients.values():
            if (UpdateType.SYSTEM_HEALTH in client.subscriptions and 
                client.status == ClientStatus.CONNECTED):
                interested_clients.add(client.client_id)
        
        if interested_clients:
            await self._broadcast_to_clients(interested_clients, {
                'type': 'system_health_update',
                'data': asdict(health)
            })
            
            # Send critical alerts immediately
            if health.status == 'critical':
                await self._broadcast_critical_alerts(health)

    async def _process_metrics_update(self, metrics: PerformanceMetrics):
        """Process performance metrics update and send to subscribed clients."""
        # Find clients interested in performance metrics
        interested_clients = set()
        for client in self.clients.values():
            if (UpdateType.PERFORMANCE_METRICS in client.subscriptions and 
                client.status == ClientStatus.CONNECTED):
                interested_clients.add(client.client_id)
        
        if interested_clients:
            await self._broadcast_to_clients(interested_clients, {
                'type': 'performance_metrics_update',
                'data': asdict(metrics)
            })

    async def _process_presence_update(self, update_data: Dict[str, Any]):
        """Process user presence update."""
        # Broadcast presence to relevant clients
        await self._broadcast_presence_updates()

    async def _process_notification_update(self, notification: Dict[str, Any]):
        """Process notification update."""
        # Send to specific user or broadcast
        if 'user_id' in notification:
            user_id = UUID(notification['user_id'])
            client_ids = self.user_to_clients.get(user_id, set())
            
            if client_ids:
                await self._broadcast_to_clients(client_ids, {
                    'type': 'notification',
                    'data': notification
                })
        else:
            # Broadcast to all clients
            await self._broadcast_to_clients(set(self.clients.keys()), {
                'type': 'notification',
                'data': notification
            })

    async def _process_risk_alert(self, alert: Dict[str, Any]):
        """Process risk alert."""
        # High priority - send to all active clients immediately
        await self._broadcast_to_clients(set(self.clients.keys()), {
            'type': 'risk_alert',
            'data': alert
        })

    async def _process_collaboration_update(self, update: Dict[str, Any]):
        """Process collaboration feature updates."""
        # Send to collaboration partners
        if 'partner_ids' in update:
            for partner_id in update['partner_ids']:
                client_ids = self.user_to_clients.get(partner_id, set())
                await self._broadcast_to_clients(client_ids, {
                    'type': 'collaboration_update',
                    'data': update
                })

    # Data Generators (Replace with real implementations)
    async def _generate_opportunity_update(self) -> OpportunityUpdate:
        """Generate simulated opportunity update (replace with real data)."""
        import random
        
        return OpportunityUpdate(
            opportunity_id=uuid4(),
            sport=random.choice(list(Sport)),
            event_name=f"Team A vs Team B - {random.choice(['Football', 'Basketball', 'Tennis'])}",
            profit_margin=random.uniform(0.02, 0.15),
            expected_profit=random.uniform(10, 100),
            risk_tier=random.choice(list(RiskTier)),
            time_remaining=random.randint(30, 3600),
            quality_score=random.uniform(0.6, 1.0),
            urgency=random.choice(['low', 'medium', 'high', 'critical']),
            legs=[
                {
                    'bookmaker': 'Bookmaker A',
                    'selection': 'Team A',
                    'odds': 2.1,
                    'stake': 50.0
                },
                {
                    'bookmaker': 'Bookmaker B', 
                    'selection': 'Team B',
                    'odds': 1.9,
                    'stake': 52.5
                }
            ],
            timestamp=datetime.utcnow(),
            status='new',
            estimated_execution_time=random.randint(30, 120)
        )

    async def _generate_trade_update(self, trade) -> TradeExecutionUpdate:
        """Generate trade execution update (replace with real data)."""
        import random
        
        return TradeExecutionUpdate(
            trade_id=trade.trade_id if hasattr(trade, 'trade_id') else uuid4(),
            status=random.choice(list(TradeStatus)),
            progress_percentage=random.uniform(0, 100),
            completed_legs=random.randint(0, 3),
            total_legs=3,
            current_leg={
                'bookmaker': 'Bookmaker A',
                'selection': 'Team A',
                'odds': 2.1,
                'status': 'placing'
            },
            estimated_completion=datetime.utcnow() + timedelta(minutes=random.randint(1, 5)),
            profit_projection=random.uniform(-20, 50),
            risk_assessment=random.choice(['low', 'medium', 'high']),
            execution_time_elapsed=random.randint(0, 300),
            timestamp=datetime.utcnow(),
            logs=[
                {'timestamp': datetime.utcnow().isoformat(), 'message': 'Trade initiated'},
                {'timestamp': datetime.utcnow().isoformat(), 'message': 'First leg placed'}
            ]
        )

    async def _generate_health_update(self) -> SystemHealthUpdate:
        """Generate system health update (replace with real monitoring)."""
        import random
        
        return SystemHealthUpdate(
            timestamp=datetime.utcnow(),
            status=random.choice(['healthy', 'warning', 'critical']),
            cpu_usage=random.uniform(10, 80),
            memory_usage=random.uniform(20, 70),
            active_connections=len(self.clients),
            database_response_time=random.uniform(10, 200),
            external_api_latency={
                'bookmaker_a': random.uniform(50, 300),
                'bookmaker_b': random.uniform(30, 250),
                'bookmaker_c': random.uniform(100, 500)
            },
            circuit_breakers_active=random.randint(0, 3),
            risk_alerts=random.randint(0, 5),
            system_load=random.uniform(0.1, 2.0),
            uptime=random.randint(3600, 86400),
            issues=[
                {'type': 'high_latency', 'severity': 'medium', 'message': 'Bookmaker C latency high'}
            ] if random.random() > 0.8 else []
        )

    async def _generate_performance_metrics(self) -> PerformanceMetrics:
        """Generate performance metrics (replace with real calculations)."""
        import random
        
        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            timeframe='1h',
            total_profit=random.uniform(100, 1000),
            profit_rate=random.uniform(50, 200),
            win_rate=random.uniform(0.6, 0.9),
            trade_count=random.randint(10, 50),
            average_trade_time=random.uniform(60, 300),
            risk_adjusted_return=random.uniform(0.1, 0.5),
            sharpe_ratio=random.uniform(1.0, 3.0),
            max_drawdown=random.uniform(0.05, 0.15),
            active_opportunities=random.randint(1, 10),
            execution_success_rate=random.uniform(0.85, 0.98)
        )

    # Utility Methods
    async def _get_active_trades(self) -> List[Any]:
        """Get currently active trades (replace with real data source)."""
        # This would integrate with your trade execution system
        return []  # Placeholder

    def _should_send_opportunity_to_client(self, client: DashboardClient, opportunity: OpportunityUpdate) -> bool:
        """Determine if opportunity should be sent to specific client."""
        # Apply user preference filters
        preferences = client.preferences
        
        # Filter by sport if specified
        if 'sports' in preferences and opportunity.sport.value not in preferences['sports']:
            return False
        
        # Filter by profit threshold
        if 'min_profit' in preferences and opportunity.expected_profit < preferences['min_profit']:
            return False
        
        # Filter by risk tier
        if 'max_risk_tier' in preferences:
            risk_tier_priority = {'tier_a': 1, 'tier_b': 2, 'tier_c': 3, 'tier_d': 4}
            if risk_tier_priority.get(opportunity.risk_tier.value, 4) > risk_tier_priority[preferences['max_risk_tier']]:
                return False
        
        return True

    def _should_send_trade_to_client(self, client: DashboardClient, trade_update: TradeExecutionUpdate) -> bool:
        """Determine if trade update should be sent to specific client."""
        # Only send if client is authenticated and has trade access
        if not client.user_id:
            return False
        
        # This would check if user has access to the specific trade
        # For now, allow all authenticated users
        return True

    async def _broadcast_critical_alerts(self, health: SystemHealthUpdate):
        """Broadcast critical system alerts to all clients."""
        await self._broadcast_to_clients(set(self.clients.keys()), {
            'type': 'critical_alert',
            'data': {
                'severity': 'critical',
                'message': 'System health is critical',
                'health_data': asdict(health),
                'timestamp': datetime.utcnow().isoformat()
            }
        })

    async def _ping_all_clients(self):
        """Send ping to all connected clients."""
        current_time = datetime.utcnow()
        tasks = []
        
        for client_id, client in list(self.clients.items()):
            if client.status == ClientStatus.CONNECTED:
                tasks.append(self._send_to_client(client_id, {
                    'type': 'ping',
                    'timestamp': current_time.isoformat()
                }))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _handle_ping(self, client_id: UUID, data: Dict[str, Any]):
        """Handle ping response from client."""
        if client_id in self.clients:
            self.clients[client_id].last_ping = datetime.utcnow()

    async def _broadcast_presence_updates(self):
        """Broadcast user presence information."""
        presence_data = {}
        
        for user_id, client_ids in self.user_to_clients.items():
            presence_data[str(user_id)] = {
                'online': True,
                'clients_count': len(client_ids),
                'last_activity': datetime.utcnow().isoformat(),
                'active_views': [
                    self.clients[cid].active_view 
                    for cid in client_ids 
                    if self.clients.get(cid) and self.clients[cid].active_view
                ]
            }
        
        # Broadcast to all connected clients
        await self._broadcast_to_clients(set(self.clients.keys()), {
            'type': 'presence_update',
            'data': presence_data
        })

    async def _cleanup_stale_presence(self):
        """Clean up stale presence data."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        
        for client_id, client in list(self.clients.items()):
            if client.last_ping < cutoff_time:
                client.status = ClientStatus.DISCONNECTED

    async def _broadcast_user_offline(self, user_id: UUID):
        """Broadcast when user goes offline."""
        await self._broadcast_to_clients(set(self.clients.keys()), {
            'type': 'user_offline',
            'user_id': str(user_id),
            'timestamp': datetime.utcnow().isoformat()
        })

    # Collaboration Features
    async def _send_collaboration_invite(self, client_id: UUID, partner_id: UUID):
        """Send collaboration invitation to partner."""
        partner_clients = self.user_to_clients.get(partner_id, set())
        
        for partner_client_id in partner_clients:
            await self._send_to_client(partner_client_id, {
                'type': 'collaboration_invite',
                'from_client': str(client_id),
                'timestamp': datetime.utcnow().isoformat()
            })

    async def _accept_collaboration_invite(self, client_id: UUID, inviter_id: UUID):
        """Accept collaboration invitation."""
        client = self.clients[client_id]
        inviter_clients = self.user_to_clients.get(inviter_id, set())
        
        # Add each other as collaboration partners
        for inviter_client_id in inviter_clients:
            self.clients[inviter_client_id].collab_partners.add(client.user_id)
            client.collab_partners.add(inviter_id)
        
        # Notify both parties
        await self._broadcast_to_clients({client_id, *inviter_clients}, {
            'type': 'collaboration_accepted',
            'partners': [str(inviter_id)],
            'timestamp': datetime.utcnow().isoformat()
        })

    async def _decline_collaboration_invite(self, client_id: UUID, inviter_id: UUID):
        """Decline collaboration invitation."""
        inviter_clients = self.user_to_clients.get(inviter_id, set())
        
        await self._broadcast_to_clients(inviter_clients, {
            'type': 'collaboration_declined',
            'from_client': str(client_id),
            'timestamp': datetime.utcnow().isoformat()
        })

    async def _leave_collaboration(self, client_id: UUID):
        """Leave collaboration session."""
        client = self.clients[client_id]
        
        # Remove collaboration partnerships
        for partner_id in list(client.collab_partners):
            partner_clients = self.user_to_clients.get(partner_id, set())
            for partner_client_id in partner_clients:
                if self.clients.get(partner_client_id):
                    self.clients[partner_client_id].collab_partners.discard(client.user_id)
        
        client.collab_partners.clear()
        
        await self._send_to_client(client_id, {
            'type': 'collaboration_left',
            'timestamp': datetime.utcnow().isoformat()
        })

    # Public API Methods
    async def send_opportunity_update(self, opportunity: ArbitrageOpportunity):
        """Send opportunity update to subscribed clients."""
        update = OpportunityUpdate(
            opportunity_id=opportunity.id,
            sport=opportunity.sport,
            event_name=opportunity.event_name,
            profit_margin=opportunity.profit_margin,
            expected_profit=opportunity.expected_profit,
            risk_tier=opportunity.risk_tier,
            time_remaining=opportunity.time_remaining,
            quality_score=getattr(opportunity, 'quality_score', 0.8),
            urgency='medium',
            legs=[{
                'bookmaker': leg.bookmaker,
                'selection': leg.selection,
                'odds': float(leg.odds),
                'stake': float(leg.stake)
            } for leg in opportunity.legs],
            timestamp=datetime.utcnow(),
            status='updated',
            estimated_execution_time=opportunity.estimated_execution_time
        )
        
        await self.processors[UpdateType.OPPORTUNITY](update)

    async def send_trade_update(self, trade: Trade):
        """Send trade execution update to subscribed clients."""
        # Convert trade to execution update
        update = TradeExecutionUpdate(
            trade_id=trade.id,
            status=trade.status,
            progress_percentage=self._calculate_trade_progress(trade),
            completed_legs=trade.completed_legs,
            total_legs=len(trade.legs),
            current_leg=getattr(trade, 'current_leg', {}),
            estimated_completion=getattr(trade, 'estimated_completion', datetime.utcnow()),
            profit_projection=float(trade.profit_projection),
            risk_assessment=getattr(trade, 'risk_assessment', 'medium'),
            execution_time_elapsed=int(time.time() - trade.created_at.timestamp()),
            timestamp=datetime.utcnow(),
            logs=getattr(trade, 'execution_logs', [])
        )
        
        await self.processors[UpdateType.TRADE](update)

    async def send_system_alert(self, alert_type: str, severity: str, message: str, data: Dict[str, Any] = None):
        """Send system alert to all clients."""
        alert = {
            'type': alert_type,
            'severity': severity,
            'message': message,
            'data': data or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.processors[UpdateType.RISK_ALERT](alert)

    async def get_client_statistics(self) -> Dict[str, Any]:
        """Get real-time client connection statistics."""
        return {
            'total_clients': len(self.clients),
            'connected_clients': sum(1 for c in self.clients.values() if c.status == ClientStatus.CONNECTED),
            'active_subscriptions': {
                update_type.value: sum(1 for c in self.clients.values() if update_type in c.subscriptions)
                for update_type in UpdateType
            },
            'user_presence': {str(uid): len(clients) for uid, clients in self.user_to_clients.items()},
            'update_metrics': self.update_metrics.copy(),
            'stream_sizes': {
                'opportunities': len(self.opportunity_stream),
                'trades': len(self.trade_stream),
                'health': len(self.health_stream),
                'metrics': len(self.metrics_stream)
            }
        }

    def _calculate_trade_progress(self, trade: Trade) -> float:
        """Calculate trade execution progress percentage."""
        if not hasattr(trade, 'legs') or not trade.legs:
            return 0.0
        
        total_legs = len(trade.legs)
        completed_legs = getattr(trade, 'completed_legs', 0)
        
        return (completed_legs / total_legs) * 100

    # Integration with Supabase Real-time
    async def subscribe_to_supabase_realtime(self):
        """Subscribe to Supabase real-time changes."""
        if not self.supabase:
            return
        
        try:
            # Subscribe to various tables for real-time updates
            self.supabase.subscribe('arbitrage_opportunities', self._handle_supabase_opportunity)
            self.supabase.subscribe('trades', self._handle_supabase_trade)
            self.supabase.subscribe('notifications', self._handle_supabase_notification)
            self.supabase.subscribe('system_events', self._handle_supabase_system_event)
            
            logger.info("Subscribed to Supabase real-time updates")
            
        except Exception as e:
            logger.error(f"Error subscribing to Supabase real-time: {e}")

    async def _handle_supabase_opportunity(self, payload):
        """Handle real-time opportunity changes from Supabase."""
        try:
            if payload['event_type'] == 'INSERT':
                # New opportunity detected
                opportunity = payload['new']
                # Convert and send update
                # This would need to convert Supabase record to our model
                
        except Exception as e:
            logger.error(f"Error handling Supabase opportunity update: {e}")

    async def _handle_supabase_trade(self, payload):
        """Handle real-time trade changes from Supabase."""
        try:
            if payload['event_type'] in ['UPDATE', 'INSERT']:
                trade = payload['new']
                # Convert and send update
                
        except Exception as e:
            logger.error(f"Error handling Supabase trade update: {e}")

    async def _handle_supabase_notification(self, payload):
        """Handle real-time notification changes from Supabase."""
        try:
            if payload['event_type'] == 'INSERT':
                notification = payload['new']
                await self.processors[UpdateType.NOTIFICATION](notification)
                
        except Exception as e:
            logger.error(f"Error handling Supabase notification update: {e}")

    async def _handle_supabase_system_event(self, payload):
        """Handle real-time system event changes from Supabase."""
        try:
            if payload['event_type'] == 'INSERT':
                event = payload['new']
                if event.get('severity') == 'critical':
                    await self.send_system_alert(
                        'system_event',
                        event.get('severity'),
                        event.get('message', 'System event occurred'),
                        event
                    )
                    
        except Exception as e:
            logger.error(f"Error handling Supabase system event: {e}")


# Dashboard Manager Class for easy integration
class DashboardManager:
    """
    High-level manager for real-time dashboard functionality.
    Provides easy integration with existing ARBitech components.
    """
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize dashboard manager."""
        self.dashboard = RealTimeDashboard(supabase_url, supabase_key)
        self.running = False
        
    async def start(self, host: str = "localhost", port: int = 8765):
        """Start the dashboard system."""
        if self.running:
            return
        
        self.running = True
        await self.dashboard.start_server(host, port)
        await self.dashboard.subscribe_to_supabase_realtime()
        
        logger.info(f"Dashboard manager started on {host}:{port}")
    
    async def stop(self):
        """Stop the dashboard system."""
        if not self.running:
            return
        
        self.running = False
        await self.dashboard.stop_server()
        
        logger.info("Dashboard manager stopped")
    
    async def broadcast_opportunity(self, opportunity: ArbitrageOpportunity):
        """Broadcast opportunity to dashboard clients."""
        await self.dashboard.send_opportunity_update(opportunity)
    
    async def broadcast_trade(self, trade: Trade):
        """Broadcast trade update to dashboard clients."""
        await self.dashboard.send_trade_update(trade)
    
    async def broadcast_alert(self, alert_type: str, severity: str, message: str, data: Dict[str, Any] = None):
        """Broadcast system alert to dashboard clients."""
        await self.dashboard.send_system_alert(alert_type, severity, message, data)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        return asyncio.create_task(self.dashboard.get_client_statistics())


# Example Usage and Testing
async def demo_dashboard_system():
    """Demonstrate the real-time dashboard system."""
    print("Starting ARBitech Real-time Dashboard Demo...")
    
    # Initialize dashboard manager
    dashboard = DashboardManager()
    
    try:
        # Start the dashboard
        await dashboard.start("localhost", 8765)
        
        print("Dashboard WebSocket server running on ws://localhost:8765")
        print("Available features:")
        print("- Real-time opportunity streaming")
        print("- Live trade execution monitoring") 
        print("- System health monitoring")
        print("- Performance metrics streaming")
        print("- User presence indicators")
        print("- Collaborative features")
        print("- Multi-client support with preferences")
        print("- Supabase real-time integration")
        
        # Simulate some updates
        await asyncio.sleep(2)
        
        # Show statistics
        stats = await dashboard.get_stats()
        print(f"Initial stats: {stats}")
        
        # Keep running
        print("\nDemo running... Press Ctrl+C to stop")
        while True:
            await asyncio.sleep(10)
            
    except KeyboardInterrupt:
        print("\nStopping dashboard...")
    except Exception as e:
        print(f"Demo error: {e}")
    finally:
        await dashboard.stop()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demo
    asyncio.run(demo_dashboard_system())