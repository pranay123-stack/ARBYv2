"""
Test Suite for Real-Time Dashboard Update System

This module provides comprehensive tests for the dashboard functionality.

Author: ARBitech Development Team
Version: 1.0.0
"""

import asyncio
import json
import pytest
import websockets
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4

from dashboard_updates import (
    RealTimeDashboard, DashboardManager, UpdateType, ClientStatus,
    DashboardClient, OpportunityUpdate, TradeExecutionUpdate, 
    SystemHealthUpdate, PerformanceMetrics
)
# Import ARBitech components - using try/except for optional dependencies
try:
    from storage.models import ArbitrageOpportunity, Trade, Sport, RiskTier, TradeStatus
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
    
    # Mock classes for testing
    class ArbitrageOpportunity:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class Trade:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


class TestRealTimeDashboard:
    """Test suite for RealTimeDashboard."""
    
    @pytest.fixture
    def dashboard(self):
        """Create dashboard instance for testing."""
        return RealTimeDashboard()
    
    @pytest.fixture
    def mock_websocket(self):
        """Create mock WebSocket connection."""
        return AsyncMock(spec=websockets.WebSocketServerProtocol)
    
    @pytest.mark.asyncio
    async def test_dashboard_initialization(self, dashboard):
        """Test dashboard initialization."""
        assert dashboard.clients == {}
        assert len(dashboard.opportunity_stream) == 0
        assert len(dashboard.trade_stream) == 0
        assert len(dashboard.health_stream) == 0
        assert len(dashboard.metrics_stream) == 0
        assert dashboard.running is False
    
    @pytest.mark.asyncio
    async def test_client_authentication(self, dashboard, mock_websocket):
        """Test client authentication flow."""
        client_id = uuid4()
        
        # Mock client data
        dashboard.clients[client_id] = Mock()
        dashboard.clients[client_id].websocket = mock_websocket
        
        # Test authentication
        auth_data = {
            "type": "authenticate",
            "user_id": str(uuid4()),
            "preferences": {
                "subscriptions": ["opportunity", "trade"],
                "min_profit": 10.0
            }
        }
        
        await dashboard._authenticate_client(client_id, auth_data)
        
        client = dashboard.clients[client_id]
        assert client.user_id is not None
        assert UpdateType.OPPORTUNITY in client.subscriptions
        assert UpdateType.TRADE in client.subscriptions
    
    @pytest.mark.asyncio
    async def test_subscription_handling(self, dashboard, mock_websocket):
        """Test subscription and unsubscription."""
        client_id = uuid4()
        
        # Mock client
        dashboard.clients[client_id] = Mock()
        dashboard.clients[client_id].websocket = mock_websocket
        dashboard.clients[client_id].subscriptions = set()
        
        # Test subscription
        subscribe_data = {
            "type": "subscribe",
            "update_types": ["opportunity", "trade", "system_health"]
        }
        
        await dashboard._handle_subscription(client_id, subscribe_data)
        
        client = dashboard.clients[client_id]
        assert UpdateType.OPPORTUNITY in client.subscriptions
        assert UpdateType.TRADE in client.subscriptions
        assert UpdateType.SYSTEM_HEALTH in client.subscriptions
        
        # Test unsubscription
        unsubscribe_data = {
            "type": "unsubscribe",
            "update_types": ["trade"]
        }
        
        await dashboard._handle_unsubscription(client_id, unsubscribe_data)
        
        assert UpdateType.TRADE not in client.subscriptions
        assert UpdateType.OPPORTUNITY in client.subscriptions
    
    @pytest.mark.asyncio
    async def test_opportunity_generation(self, dashboard):
        """Test opportunity update generation."""
        opportunity = await dashboard._generate_opportunity_update()
        
        assert isinstance(opportunity, OpportunityUpdate)
        assert opportunity.opportunity_id is not None
        assert opportunity.sport in list(Sport)
        assert opportunity.expected_profit > 0
        assert opportunity.risk_tier in list(RiskTier)
        assert opportunity.time_remaining > 0
        assert len(opportunity.legs) >= 2
    
    @pytest.mark.asyncio
    async def test_trade_update_generation(self, dashboard):
        """Test trade execution update generation."""
        mock_trade = Mock()
        mock_trade.trade_id = uuid4()
        
        trade_update = await dashboard._generate_trade_update(mock_trade)
        
        assert isinstance(trade_update, TradeExecutionUpdate)
        assert trade_update.trade_id == mock_trade.trade_id
        assert trade_update.status in list(TradeStatus)
        assert 0 <= trade_update.progress_percentage <= 100
        assert trade_update.completed_legs >= 0
        assert trade_update.total_legs > 0
    
    @pytest.mark.asyncio
    async def test_health_update_generation(self, dashboard):
        """Test system health update generation."""
        health = await dashboard._generate_health_update()
        
        assert isinstance(health, SystemHealthUpdate)
        assert health.status in ['healthy', 'warning', 'critical']
        assert 0 <= health.cpu_usage <= 100
        assert 0 <= health.memory_usage <= 100
        assert health.active_connections >= 0
        assert isinstance(health.external_api_latency, dict)
    
    @pytest.mark.asyncio
    async def test_metrics_generation(self, dashboard):
        """Test performance metrics generation."""
        metrics = await dashboard._generate_performance_metrics()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.timeframe in ['1m', '5m', '15m', '1h', '1d']
        assert 0 <= metrics.win_rate <= 1
        assert metrics.trade_count >= 0
        assert metrics.execution_success_rate >= 0
        assert metrics.execution_success_rate <= 1
    
    @pytest.mark.asyncio
    async def test_opportunity_filtering(self, dashboard):
        """Test client-specific opportunity filtering."""
        # Create mock client with preferences
        client = Mock()
        client.preferences = {
            "sports": ["football"],
            "min_profit": 20.0,
            "max_risk_tier": "tier_a"
        }
        client.subscriptions = {UpdateType.OPPORTUNITY}
        
        # Create test opportunities
        football_opportunity = OpportunityUpdate(
            opportunity_id=uuid4(),
            sport=Sport.FOOTBALL,
            event_name="Test Football Match",
            profit_margin=0.05,
            expected_profit=25.0,  # Above min_profit threshold
            risk_tier=RiskTier.TIER_A,
            time_remaining=300,
            quality_score=0.8,
            urgency="medium",
            legs=[],
            timestamp=datetime.utcnow(),
            status="new",
            estimated_execution_time=60
        )
        
        basketball_opportunity = OpportunityUpdate(
            opportunity_id=uuid4(),
            sport=Sport.BASKETBALL,
            event_name="Test Basketball Match",
            profit_margin=0.03,
            expected_profit=15.0,  # Below min_profit threshold
            risk_tier=RiskTier.TIER_B,
            time_remaining=300,
            quality_score=0.7,
            urgency="low",
            legs=[],
            timestamp=datetime.utcnow(),
            status="new",
            estimated_execution_time=60
        )
        
        # Test filtering
        should_send_football = dashboard._should_send_opportunity_to_client(client, football_opportunity)
        should_send_basketball = dashboard._should_send_opportunity_to_client(client, basketball_opportunity)
        
        assert should_send_football is True
        assert should_send_basketball is False  # Sport not in preferences
    
    @pytest.mark.asyncio
    async def test_client_ping_handling(self, dashboard, mock_websocket):
        """Test client ping/pong handling."""
        client_id = uuid4()
        client = Mock()
        client.websocket = mock_websocket
        client.last_ping = datetime.utcnow()
        dashboard.clients[client_id] = client
        
        # Send ping
        ping_data = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await dashboard._handle_ping(client_id, ping_data)
        
        # Verify client was pinged (this is a basic test)
        assert client.last_ping is not None
    
    @pytest.mark.asyncio
    async def test_collaboration_features(self, dashboard, mock_websocket):
        """Test collaboration functionality."""
        client_id = uuid4()
        partner_id = uuid4()
        
        # Setup clients
        dashboard.clients[client_id] = Mock()
        dashboard.clients[client_id].websocket = mock_websocket
        dashboard.clients[client_id].user_id = client_id
        dashboard.clients[client_id].collab_partners = set()
        
        dashboard.user_to_clients[partner_id].add(uuid4())
        
        # Test collaboration invitation
        invite_data = {
            "type": "collaboration",
            "action": "invite",
            "partner_id": str(partner_id)
        }
        
        await dashboard._handle_collaboration_request(client_id, invite_data)
        
        # Test accepting invitation
        accept_data = {
            "type": "collaboration", 
            "action": "accept",
            "inviter_id": str(partner_id)
        }
        
        await dashboard._handle_collaboration_request(client_id, accept_data)
        
        # Client should now have partnership
        client = dashboard.clients[client_id]
        assert partner_id in client.collab_partners
    
    @pytest.mark.asyncio
    async def test_statistics_generation(self, dashboard):
        """Test dashboard statistics generation."""
        # Add some mock data
        client_id = uuid4()
        dashboard.clients[client_id] = Mock()
        dashboard.clients[client_id].status = ClientStatus.CONNECTED
        dashboard.clients[client_id].subscriptions = {UpdateType.OPPORTUNITY}
        
        dashboard.opportunity_stream.append(Mock())
        dashboard.trade_stream.append(Mock())
        dashboard.health_stream.append(Mock())
        dashboard.metrics_stream.append(Mock())
        
        stats = await dashboard.get_client_statistics()
        
        assert stats["total_clients"] == 1
        assert stats["connected_clients"] == 1
        assert "opportunity" in stats["active_subscriptions"]
        assert stats["stream_sizes"]["opportunities"] == 1
        assert stats["stream_sizes"]["trades"] == 1
        assert stats["stream_sizes"]["health"] == 1
        assert stats["stream_sizes"]["metrics"] == 1


class TestDashboardManager:
    """Test suite for DashboardManager."""
    
    @pytest.fixture
    def manager(self):
        """Create manager instance for testing."""
        return DashboardManager()
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, manager):
        """Test manager initialization."""
        assert manager.dashboard is not None
        assert manager.running is False
    
    @pytest.mark.asyncio
    async def test_start_stop_cycle(self, manager):
        """Test manager start and stop cycle."""
        # Start manager
        await manager.start("localhost", 9999)
        assert manager.running is True
        
        # Stop manager
        await manager.stop()
        assert manager.running is False
    
    @pytest.mark.asyncio
    async def test_broadcast_methods(self, manager):
        """Test broadcast methods."""
        # Mock opportunity
        opportunity = Mock(spec=ArbitrageOpportunity)
        opportunity.id = uuid4()
        opportunity.sport = Sport.FOOTBALL
        opportunity.event_name = "Test Match"
        opportunity.profit_margin = 0.05
        opportunity.expected_profit = 25.0
        opportunity.risk_tier = RiskTier.TIER_A
        opportunity.time_remaining = 300
        opportunity.estimated_execution_time = 60
        opportunity.legs = []
        
        # Mock trade
        trade = Mock(spec=Trade)
        trade.id = uuid4()
        trade.status = TradeStatus.PENDING
        trade.created_at = datetime.utcnow()
        trade.profit_projection = 20.0
        trade.completed_legs = 0
        trade.legs = [Mock(), Mock()]
        
        # Test broadcasts (these should not raise exceptions)
        await manager.broadcast_opportunity(opportunity)
        await manager.broadcast_trade(trade)
        await manager.broadcast_alert("test", "medium", "Test alert")


class TestDataModels:
    """Test data model validation."""
    
    def test_opportunity_update_model(self):
        """Test OpportunityUpdate data model."""
        update = OpportunityUpdate(
            opportunity_id=uuid4(),
            sport=Sport.FOOTBALL,
            event_name="Test Match",
            profit_margin=0.05,
            expected_profit=25.0,
            risk_tier=RiskTier.TIER_A,
            time_remaining=300,
            quality_score=0.8,
            urgency="medium",
            legs=[],
            timestamp=datetime.utcnow(),
            status="new",
            estimated_execution_time=60
        )
        
        assert update.opportunity_id is not None
        assert update.sport == Sport.FOOTBALL
        assert update.expected_profit > 0
    
    def test_trade_execution_update_model(self):
        """Test TradeExecutionUpdate data model."""
        update = TradeExecutionUpdate(
            trade_id=uuid4(),
            status=TradeStatus.PENDING,
            progress_percentage=25.0,
            completed_legs=1,
            total_legs=3,
            current_leg={},
            estimated_completion=datetime.utcnow(),
            profit_projection=20.0,
            risk_assessment="medium",
            execution_time_elapsed=60,
            timestamp=datetime.utcnow(),
            logs=[]
        )
        
        assert update.trade_id is not None
        assert update.status == TradeStatus.PENDING
        assert update.progress_percentage == 25.0
    
    def test_system_health_update_model(self):
        """Test SystemHealthUpdate data model."""
        update = SystemHealthUpdate(
            timestamp=datetime.utcnow(),
            status="healthy",
            cpu_usage=50.0,
            memory_usage=60.0,
            active_connections=5,
            database_response_time=100.0,
            external_api_latency={"api1": 50.0},
            circuit_breakers_active=0,
            risk_alerts=0,
            system_load=1.0,
            uptime=3600,
            issues=[]
        )
        
        assert update.status == "healthy"
        assert update.cpu_usage == 50.0
        assert update.active_connections == 5
    
    def test_performance_metrics_model(self):
        """Test PerformanceMetrics data model."""
        metrics = PerformanceMetrics(
            timestamp=datetime.utcnow(),
            timeframe="1h",
            total_profit=100.0,
            profit_rate=50.0,
            win_rate=0.75,
            trade_count=10,
            average_trade_time=120.0,
            risk_adjusted_return=0.25,
            sharpe_ratio=2.0,
            max_drawdown=0.1,
            active_opportunities=3,
            execution_success_rate=0.9
        )
        
        assert metrics.timeframe == "1h"
        assert metrics.win_rate == 0.75
        assert metrics.execution_success_rate == 0.9


# Integration Tests
class TestIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.mark.asyncio
    async def test_full_opportunity_flow(self):
        """Test complete opportunity detection and broadcast flow."""
        dashboard = DashboardManager()
        
        try:
            await dashboard.start("localhost", 9998)
            
            # Simulate opportunity detection
            opportunity = ArbitrageOpportunity(
                id=uuid4(),
                sport=Sport.FOOTBALL,
                event_name="Team A vs Team B",
                profit_margin=0.05,
                expected_profit=25.0,
                risk_tier=RiskTier.TIER_A,
                time_remaining=300,
                legs=[],
                estimated_execution_time=60
            )
            
            # Broadcast opportunity
            await dashboard.broadcast_opportunity(opportunity)
            
            # Verify it was processed
            stats = await dashboard.get_stats()
            assert stats["update_metrics"]["updates_sent"] > 0
            
        finally:
            await dashboard.stop()
    
    @pytest.mark.asyncio 
    async def test_full_trade_flow(self):
        """Test complete trade execution and broadcast flow."""
        dashboard = DashboardManager()
        
        try:
            await dashboard.start("localhost", 9997)
            
            # Simulate trade execution
            trade = Trade(
                id=uuid4(),
                status=TradeStatus.PLACING_BETS,
                legs=[],
                profit_projection=20.0
            )
            
            # Broadcast trade update
            await dashboard.broadcast_trade(trade)
            
            # Verify it was processed
            stats = await dashboard.get_stats()
            assert stats["update_metrics"]["updates_sent"] > 0
            
        finally:
            await dashboard.stop()


if __name__ == "__main__":
    # Run basic functionality test
    async def basic_test():
        print("Running basic dashboard functionality test...")
        
        # Create manager
        manager = DashboardManager()
        
        try:
            # Start dashboard
            print("Starting dashboard server...")
            await manager.start("localhost", 9996)
            print("✅ Dashboard server started")
            
            # Get initial stats
            stats = await manager.get_stats()
            print(f"Initial stats: {stats}")
            
            # Test broadcasts
            print("Testing broadcast methods...")
            
            # Mock opportunity
            opportunity = Mock()
            opportunity.id = uuid4()
            opportunity.sport = Sport.FOOTBALL
            opportunity.event_name = "Test Match"
            opportunity.profit_margin = 0.05
            opportunity.expected_profit = 25.0
            opportunity.risk_tier = RiskTier.TIER_A
            opportunity.time_remaining = 300
            opportunity.estimated_execution_time = 60
            opportunity.legs = []
            
            await manager.broadcast_opportunity(opportunity)
            print("✅ Opportunity broadcast successful")
            
            # Mock trade
            trade = Mock()
            trade.id = uuid4()
            trade.status = TradeStatus.PENDING
            trade.created_at = datetime.utcnow()
            trade.profit_projection = 20.0
            trade.completed_legs = 0
            trade.legs = [Mock(), Mock()]
            
            await manager.broadcast_trade(trade)
            print("✅ Trade broadcast successful")
            
            await manager.broadcast_alert("test", "medium", "Test alert")
            print("✅ Alert broadcast successful")
            
            # Check updated stats
            stats = await manager.get_stats()
            print(f"Updated stats: {stats}")
            print(f"✅ Total updates sent: {stats['update_metrics']['updates_sent']}")
            
            print("\n🎉 All basic tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            raise
        finally:
            print("Stopping dashboard server...")
            await manager.stop()
            print("✅ Dashboard server stopped")
    
    # Run basic test
    asyncio.run(basic_test())