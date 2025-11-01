"""
Demo Client for Real-time Dashboard System

This module provides example implementations of dashboard clients
that can connect to the real-time dashboard system and receive updates.

Author: ARBitech Development Team
Version: 1.0.0
"""

import asyncio
import json
import websockets
from datetime import datetime
from typing import Dict, Any, Optional


class DashboardClient:
    """Example dashboard client that connects to the real-time system."""
    
    def __init__(self, user_id: str, server_url: str = "ws://localhost:8765"):
        """Initialize dashboard client."""
        self.user_id = user_id
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        self.subscriptions = set()
        self.preferences = {}
        
    async def connect(self):
        """Connect to the dashboard WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            print(f"Connected to dashboard server: {self.server_url}")
            
            # Authenticate
            await self.authenticate()
            
            # Start message handler
            asyncio.create_task(self._message_handler())
            
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.connected = False
    
    async def authenticate(self):
        """Authenticate with the server."""
        auth_message = {
            "type": "authenticate",
            "user_id": self.user_id,
            "preferences": {
                "subscriptions": ["opportunity", "trade", "system_health", "performance_metrics"],
                "sports": ["football", "basketball"],
                "min_profit": 5.0,
                "max_risk_tier": "tier_b",
                "active_view": "dashboard",
                "collaboration_mode": False
            }
        }
        
        await self.send_message(auth_message)
    
    async def send_message(self, message: Dict[str, Any]):
        """Send message to server."""
        if self.websocket and self.connected:
            await self.websocket.send(json.dumps(message))
    
    async def subscribe_to_updates(self, update_types: list):
        """Subscribe to specific update types."""
        subscription_message = {
            "type": "subscribe",
            "update_types": update_types
        }
        
        await self.send_message(subscription_message)
        
        for update_type in update_types:
            self.subscriptions.add(update_type)
    
    async def unsubscribe_from_updates(self, update_types: list):
        """Unsubscribe from update types."""
        unsubscription_message = {
            "type": "unsubscribe",
            "update_types": update_types
        }
        
        await self.send_message(unsubscription_message)
        
        for update_type in update_types:
            self.subscriptions.discard(update_type)
    
    async def update_preferences(self, preferences: Dict[str, Any]):
        """Update client preferences."""
        preference_message = {
            "type": "update_preferences",
            "preferences": preferences
        }
        
        await self.send_message(preference_message)
        self.preferences.update(preferences)
    
    async def invite_collaboration(self, partner_user_id: str):
        """Invite user for collaboration."""
        collaboration_message = {
            "type": "collaboration",
            "action": "invite",
            "partner_id": partner_user_id
        }
        
        await self.send_message(collaboration_message)
    
    async def accept_collaboration(self, inviter_user_id: str):
        """Accept collaboration invitation."""
        collaboration_message = {
            "type": "collaboration",
            "action": "accept",
            "inviter_id": inviter_user_id
        }
        
        await self.send_message(collaboration_message)
    
    async def leave_collaboration(self):
        """Leave collaboration session."""
        collaboration_message = {
            "type": "collaboration",
            "action": "leave"
        }
        
        await self.send_message(collaboration_message)
    
    async def mark_notification_read(self, notification_id: str):
        """Mark notification as read."""
        read_message = {
            "type": "mark_notification_read",
            "notification_id": notification_id
        }
        
        await self.send_message(read_message)
    
    async def _message_handler(self):
        """Handle incoming messages from server."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._process_message(data)
                
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed by server")
            self.connected = False
        except Exception as e:
            print(f"Error handling message: {e}")
            self.connected = False
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming message and take appropriate action."""
        message_type = data.get("type")
        
        if message_type == "connection_established":
            print("✅ Connection established with dashboard server")
            print(f"Client ID: {data.get('client_id')}")
            
        elif message_type == "authenticated":
            print("✅ Successfully authenticated")
            print(f"User ID: {data.get('user_id')}")
            
        elif message_type == "subscription_confirmed":
            print("📡 Subscriptions updated:")
            for subscription in data.get('subscriptions', []):
                print(f"  - {subscription}")
                
        elif message_type == "opportunity_update":
            opportunity = data.get('data', {})
            print(f"\n🎯 New Opportunity:")
            print(f"  ID: {opportunity.get('opportunity_id')}")
            print(f"  Sport: {opportunity.get('sport')}")
            print(f"  Event: {opportunity.get('event_name')}")
            print(f"  Profit Margin: {opportunity.get('profit_margin'):.2%}")
            print(f"  Expected Profit: ${opportunity.get('expected_profit', 0):.2f}")
            print(f"  Risk Tier: {opportunity.get('risk_tier')}")
            print(f"  Urgency: {opportunity.get('urgency')}")
            print(f"  Time Remaining: {opportunity.get('time_remaining', 0)}s")
            
        elif message_type == "trade_update":
            trade = data.get('data', {})
            print(f"\n🔄 Trade Update:")
            print(f"  Trade ID: {trade.get('trade_id')}")
            print(f"  Status: {trade.get('status')}")
            print(f"  Progress: {trade.get('progress_percentage', 0):.1f}%")
            print(f"  Completed: {trade.get('completed_legs', 0)}/{trade.get('total_legs', 0)} legs")
            print(f"  Current Leg: {trade.get('current_leg', {}).get('bookmaker', 'Unknown')}")
            print(f"  Profit Projection: ${trade.get('profit_projection', 0):.2f}")
            print(f"  Estimated Completion: {trade.get('estimated_completion')}")
            
        elif message_type == "system_health_update":
            health = data.get('data', {})
            print(f"\n💓 System Health:")
            print(f"  Status: {health.get('status')}")
            print(f"  CPU Usage: {health.get('cpu_usage', 0):.1f}%")
            print(f"  Memory Usage: {health.get('memory_usage', 0):.1f}%")
            print(f"  Active Connections: {health.get('active_connections', 0)}")
            print(f"  Database Response Time: {health.get('database_response_time', 0):.0f}ms")
            print(f"  Circuit Breakers Active: {health.get('circuit_breakers_active', 0)}")
            print(f"  Risk Alerts: {health.get('risk_alerts', 0)}")
            
            if health.get('issues'):
                print(f"  Issues:")
                for issue in health.get('issues', []):
                    print(f"    - {issue.get('type')}: {issue.get('message')}")
            
        elif message_type == "performance_metrics_update":
            metrics = data.get('data', {})
            print(f"\n📈 Performance Metrics:")
            print(f"  Timeframe: {metrics.get('timeframe')}")
            print(f"  Total Profit: ${metrics.get('total_profit', 0):.2f}")
            print(f"  Profit Rate: ${metrics.get('profit_rate', 0):.2f}/hour")
            print(f"  Win Rate: {metrics.get('win_rate', 0):.1%}")
            print(f"  Trade Count: {metrics.get('trade_count', 0)}")
            print(f"  Average Trade Time: {metrics.get('average_trade_time', 0):.0f}s")
            print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
            print(f"  Max Drawdown: {metrics.get('max_drawdown', 0):.1%}")
            print(f"  Execution Success Rate: {metrics.get('execution_success_rate', 0):.1%}")
            
        elif message_type == "presence_update":
            presence = data.get('data', {})
            print(f"\n👥 User Presence:")
            for user_id, info in presence.items():
                status = "🟢 Online" if info.get('online') else "🔴 Offline"
                print(f"  {user_id}: {status} ({info.get('clients_count', 0)} connections)")
            
        elif message_type == "notification":
            notification = data.get('data', {})
            print(f"\n🔔 Notification:")
            print(f"  Type: {notification.get('type')}")
            print(f"  Priority: {notification.get('priority', 'medium')}")
            print(f"  Title: {notification.get('title', 'No title')}")
            print(f"  Body: {notification.get('body', 'No body')}")
            
        elif message_type == "risk_alert":
            alert = data.get('data', {})
            severity_emoji = {
                'low': '🟡',
                'medium': '🟠', 
                'high': '🔴',
                'critical': '🚨'
            }
            emoji = severity_emoji.get(alert.get('severity', 'medium'), '⚠️')
            print(f"\n{emoji} Risk Alert:")
            print(f"  Type: {alert.get('type')}")
            print(f"  Severity: {alert.get('severity', 'unknown').upper()}")
            print(f"  Message: {alert.get('message', 'No message')}")
            
        elif message_type == "critical_alert":
            print(f"\n🚨 CRITICAL ALERT:")
            print(f"  {data.get('data', {}).get('message', 'System critical error')}")
            
        elif message_type == "collaboration_invite":
            print(f"\n🤝 Collaboration Invite:")
            print(f"  From client: {data.get('from_client')}")
            print(f"  Use accept_collaboration() to accept")
            
        elif message_type == "collaboration_accepted":
            print(f"\n🤝 Collaboration Started:")
            print(f"  Partners: {data.get('partners', [])}")
            
        elif message_type == "collaboration_declined":
            print(f"\n❌ Collaboration Declined by: {data.get('from_client')}")
            
        elif message_type == "collaboration_left":
            print(f"\n👋 Left collaboration session")
            
        elif message_type == "error":
            print(f"\n❌ Error: {data.get('error', 'Unknown error')}")
            
        elif message_type == "ping":
            # Respond to ping
            await self.send_message({
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def disconnect(self):
        """Disconnect from the server."""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            print("Disconnected from dashboard server")


async def demo_multiple_clients():
    """Demonstrate multiple clients connecting and receiving updates."""
    print("Starting Multi-Client Dashboard Demo...")
    
    # Create multiple clients
    clients = []
    for i in range(3):
        client = DashboardClient(f"user_{i+1}")
        clients.append(client)
    
    try:
        # Connect all clients
        connection_tasks = [client.connect() for client in clients]
        await asyncio.gather(*connection_tasks)
        
        print(f"\n✅ {len(clients)} clients connected")
        
        # Wait for updates
        print("\n📡 Receiving real-time updates... (Press Ctrl+C to stop)")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nStopping demo...")
    finally:
        # Disconnect all clients
        disconnect_tasks = [client.disconnect() for client in clients]
        await asyncio.gather(*disconnect_tasks)
        
        print("Demo completed")


async def demo_single_client():
    """Demonstrate single client with interactive features."""
    print("Starting Interactive Dashboard Client Demo...")
    
    # Create client
    client = DashboardClient("demo_user")
    
    try:
        # Connect
        await client.connect()
        
        print("\n🎮 Interactive Demo Controls:")
        print("1. Subscribe to updates")
        print("2. Update preferences") 
        print("3. Invite collaboration")
        print("4. Leave collaboration")
        print("5. Show subscriptions")
        print("q. Quit")
        
        while client.connected:
            try:
                choice = input("\nChoose option: ").strip().lower()
                
                if choice == '1':
                    updates = input("Enter update types (comma-separated): ").strip()
                    update_types = [u.strip() for u in updates.split(',')]
                    await client.subscribe_to_updates(update_types)
                    
                elif choice == '2':
                    preferences = {
                        'min_profit': float(input("Min profit: ") or "10"),
                        'sports': input("Sports (comma-separated): ").strip().split(',') if input("Sports? (y/N): ").lower() == 'y' else []
                    }
                    await client.update_preferences(preferences)
                    
                elif choice == '3':
                    partner = input("Partner user ID: ").strip()
                    if partner:
                        await client.invite_collaboration(partner)
                        
                elif choice == '4':
                    await client.leave_collaboration()
                    
                elif choice == '5':
                    print(f"Current subscriptions: {list(client.subscriptions)}")
                    
                elif choice == 'q':
                    break
                    
            except (ValueError, KeyboardInterrupt):
                break
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted")
    finally:
        await client.disconnect()
        print("Demo completed")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "multi":
        # Run multi-client demo
        asyncio.run(demo_multiple_clients())
    else:
        # Run single client demo
        asyncio.run(demo_single_client())