"""
Comprehensive Opportunity Presentation System for HITL Mode

This module provides a comprehensive system for presenting detected arbitrage opportunities
in Human-in-the-Loop (HITL) mode with multiple display formats, real-time updates,
and intelligent ranking capabilities.

Features:
- Multi-format presentation (Console, GUI, Web)
- Real-time opportunity updates
- Intelligent ranking and comparison
- Historical performance analysis
- Kelly criterion integration
- Risk assessment visualization
- Comprehensive logging and error handling

Author: ARBitech Framework
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Callable, Union, Tuple, NamedTuple
from uuid import UUID, uuid4
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod
import threading
from collections import deque
import statistics
import weakref
import traceback
import websockets
from concurrent.futures import ThreadPoolExecutor

# Import ARBitech models and components
try:
    # Try relative imports first (when used as part of arbitech package)
    from ..storage.models import (
        ArbitrageOpportunity, ArbitrageLeg, Trade, StakeData, TradeStatus,
        Sport, RiskTier, NotificationPriority, NotificationType
    )
    from ..detection.opportunity_scanner import OpportunityScanner, ScannerEventType
    from ..risk.kelly_calculator import KellyCalculator, KellyConfig, KellyMode
    from ..risk.risk_analyzer import RiskAnalyzer
    from ..storage.audit_logger import AuditLogger
    from ..utils.logger import get_logger
except ImportError:
    # Fall back to absolute imports (when used standalone or in tests)
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from storage.models import (
        ArbitrageOpportunity, ArbitrageLeg, Trade, StakeData, TradeStatus,
        Sport, RiskTier, NotificationPriority, NotificationType
    )
    from detection.opportunity_scanner import OpportunityScanner, ScannerEventType
    from risk.kelly_calculator import KellyCalculator, KellyConfig, KellyMode
    from risk.risk_analyzer import RiskAnalyzer
    from storage.audit_logger import AuditLogger
    from utils.logger import get_logger


# Configure logger
logger = get_logger(__name__)


class DisplayFormat(str, Enum):
    """Supported display formats."""
    CONSOLE = "console"
    GUI = "gui"
    WEB = "web"
    JSON = "json"


class OpportunityPriority(str, Enum):
    """Opportunity priority levels for presentation."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PresentationEventType(str, Enum):
    """Types of presentation events."""
    OPPORTUNITY_ADDED = "opportunity_added"
    OPPORTUNITY_UPDATED = "opportunity_updated"
    OPPORTUNITY_REMOVED = "opportunity_removed"
    OPPORTUNITY_RANKED = "opportunity_ranked"
    ERROR_OCCURRED = "error_occurred"
    DISPLAY_UPDATED = "display_updated"
    HISTORICAL_DATA_LOADED = "historical_data_loaded"
    USER_FEEDBACK_RECEIVED = "user_feedback_received"


@dataclass
class PresentationEvent:
    """Represents an event in the presentation system."""
    type: PresentationEventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str


@dataclass
class OpportunityMetrics:
    """Comprehensive metrics for an arbitrage opportunity."""
    opportunity_id: UUID
    profit_margin: Decimal
    profit_amount: Decimal
    kelly_fraction: Decimal
    kelly_stake: Decimal
    risk_score: Decimal
    liquidity_score: Decimal
    freshness_score: Decimal
    historical_success_rate: Decimal
    quality_score: Decimal
    priority_score: Decimal
    estimated_execution_time: int
    confidence_level: Decimal


@dataclass
class ComparisonData:
    """Data for opportunity comparison."""
    primary_opportunity: ArbitrageOpportunity
    secondary_opportunities: List[ArbitrageOpportunity]
    metrics: Dict[UUID, OpportunityMetrics]
    recommended_ranks: List[UUID]
    comparative_analysis: Dict[str, Any]


@dataclass
class HistoricalPerformance:
    """Historical performance data for similar opportunities."""
    sport: Sport
    market_type: str
    risk_tier: RiskTier
    profit_margin_range: Tuple[Decimal, Decimal]
    success_rate: Decimal
    average_profit: Decimal
    sample_size: int
    last_updated: datetime
    performance_score: Decimal


class HistoricalDataStore:
    """Manages historical performance data for opportunities."""
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self.data: deque = deque(maxlen=max_entries)
        self.aggregated_stats: Dict[str, HistoricalPerformance] = {}
        self._lock = threading.RLock()
    
    def add_performance_data(self, trade: Trade) -> None:
        """Add performance data from a completed trade."""
        try:
            with self._lock:
                opportunity = trade.opportunity
                
                # Calculate performance metrics
                profit_margin = opportunity.profit_margin
                profit_amount = trade.actual_profit or Decimal('0')
                
                # Aggregate by sport, market, and risk tier
                key = f"{opportunity.sport.value}_{opportunity.market_type}_{opportunity.risk_tier.value}"
                
                if key not in self.aggregated_stats:
                    self.aggregated_stats[key] = HistoricalPerformance(
                        sport=opportunity.sport,
                        market_type=opportunity.market_type,
                        risk_tier=opportunity.risk_tier,
                        profit_margin_range=(profit_margin, profit_margin),
                        success_rate=Decimal('1.0'),
                        average_profit=profit_amount,
                        sample_size=1,
                        last_updated=datetime.utcnow(),
                        performance_score=Decimal('1.0')
                    )
                else:
                    stats = self.aggregated_stats[key]
                    stats.sample_size += 1
                    stats.average_profit = (stats.average_profit * (stats.sample_size - 1) + profit_amount) / stats.sample_size
                    
                    # Update profit margin range
                    current_min, current_max = stats.profit_margin_range
                    stats.profit_margin_range = (
                        min(current_min, profit_margin),
                        max(current_max, profit_margin)
                    )
                    
                    # Recalculate success rate
                    if trade.status == TradeStatus.SETTLED:
                        # For simplicity, assume all settled trades with profit are successful
                        success_rate = Decimal('1.0') if profit_amount > 0 else Decimal('0')
                        stats.success_rate = (stats.success_rate * (stats.sample_size - 1) + success_rate) / stats.sample_size
                    
                    stats.last_updated = datetime.utcnow()
                    
                    # Calculate performance score
                    stats.performance_score = self._calculate_performance_score(stats)
                
                logger.debug(f"Updated historical data for {key}: {stats.success_rate:.2%} success rate")
                
        except Exception as e:
            logger.error(f"Error adding performance data: {e}")
            logger.error(traceback.format_exc())
    
    def get_historical_performance(
        self, 
        sport: Sport, 
        market_type: str, 
        risk_tier: RiskTier,
        profit_margin: Optional[Decimal] = None
    ) -> Optional[HistoricalPerformance]:
        """Get historical performance data for similar opportunities."""
        try:
            with self._lock:
                key = f"{sport.value}_{market_type}_{risk_tier.value}"
                
                if key in self.aggregated_stats:
                    stats = self.aggregated_stats[key]
                    
                    # If profit margin provided, check if it's within range
                    if profit_margin is not None:
                        min_margin, max_margin = stats.profit_margin_range
                        if profit_margin < min_margin or profit_margin > max_margin:
                            # Find closest match
                            return self._find_closest_match(sport, market_type, risk_tier, profit_margin)
                    
                    return stats
                
                # Find closest match
                return self._find_closest_match(sport, market_type, risk_tier, profit_margin)
                
        except Exception as e:
            logger.error(f"Error getting historical performance: {e}")
            return None
    
    def _find_closest_match(
        self, 
        sport: Sport, 
        market_type: str, 
        risk_tier: RiskTier,
        profit_margin: Optional[Decimal]
    ) -> Optional[HistoricalPerformance]:
        """Find the closest matching historical performance data."""
        try:
            with self._lock:
                best_match = None
                best_score = Decimal('0')
                
                for key, stats in self.aggregated_stats.items():
                    score = Decimal('0')
                    
                    # Score based on exact matches
                    if stats.sport == sport:
                        score += Decimal('0.4')
                    if stats.market_type == market_type:
                        score += Decimal('0.3')
                    if stats.risk_tier == risk_tier:
                        score += Decimal('0.3')
                    
                    # Bonus for profit margin similarity
                    if profit_margin is not None and stats.profit_margin_range:
                        min_margin, max_margin = stats.profit_margin_range
                        if min_margin <= profit_margin <= max_margin:
                            score += Decimal('0.1')
                    
                    if score > best_score:
                        best_score = score
                        best_match = stats
                
                return best_match if best_score >= Decimal('0.3') else None
                
        except Exception as e:
            logger.error(f"Error finding closest match: {e}")
            return None
    
    def _calculate_performance_score(self, stats: HistoricalPerformance) -> Decimal:
        """Calculate overall performance score."""
        try:
            # Weight success rate heavily
            success_score = stats.success_rate * Decimal('0.6')
            
            # Sample size factor (more data = higher confidence)
            sample_score = min(Decimal('1.0'), stats.sample_size / Decimal('100')) * Decimal('0.2')
            
            # Profitability factor
            profit_score = min(Decimal('1.0'), stats.average_profit / Decimal('100')) * Decimal('0.2')
            
            # Recency factor
            days_old = (datetime.utcnow() - stats.last_updated).days
            recency_score = max(Decimal('0.1'), Decimal('1.0') - (days_old / Decimal('365'))) * Decimal('0.1')
            
            total_score = success_score + sample_score + profit_score + recency_score
            return min(Decimal('1.0'), total_score)
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return Decimal('0.5')


class OpportunityPresenterInterface(ABC):
    """Abstract interface for opportunity presentation."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the presenter."""
        pass
    
    @abstractmethod
    async def display_opportunities(
        self, 
        opportunities: List[ArbitrageOpportunity],
        metrics: Dict[UUID, OpportunityMetrics]
    ) -> None:
        """Display opportunities with their metrics."""
        pass
    
    @abstractmethod
    async def update_opportunity(self, opportunity: ArbitrageOpportunity, metrics: OpportunityMetrics) -> None:
        """Update display for a single opportunity."""
        pass
    
    @abstractmethod
    async def remove_opportunity(self, opportunity_id: UUID) -> None:
        """Remove opportunity from display."""
        pass
    
    @abstractmethod
    async def display_comparison(self, comparison: ComparisonData) -> None:
        """Display opportunity comparison."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the presenter."""
        pass


class ConsolePresenter(OpportunityPresenterInterface):
    """Console-based opportunity presenter with rich formatting."""
    
    def __init__(self, max_opportunities: int = 20):
        self.max_opportunities = max_opportunities
        self._opportunities: Dict[UUID, ArbitrageOpportunity] = {}
        self._metrics: Dict[UUID, OpportunityMetrics] = {}
        self._lock = threading.RLock()
    
    async def initialize(self) -> None:
        """Initialize console presenter."""
        try:
            logger.info("Initializing console presenter")
            # Clear screen
            print("\033[2J\033[H", end="")
            print("=" * 100)
            print("🎯 ARBitech HITL - Arbitrage Opportunity Monitor")
            print("=" * 100)
            print(f"Maximum opportunities displayed: {self.max_opportunities}")
            print("-" * 100)
            
        except Exception as e:
            logger.error(f"Error initializing console presenter: {e}")
            raise
    
    async def display_opportunities(
        self, 
        opportunities: List[ArbitrageOpportunity],
        metrics: Dict[UUID, OpportunityMetrics]
    ) -> None:
        """Display opportunities in console format."""
        try:
            with self._lock:
                self._opportunities.clear()
                self._metrics.clear()
                
                # Sort by priority score
                sorted_opportunities = sorted(
                    opportunities,
                    key=lambda opp: metrics.get(opp.id, OpportunityMetrics(
                        opportunity_id=opp.id,
                        profit_margin=Decimal('0'),
                        profit_amount=Decimal('0'),
                        kelly_fraction=Decimal('0'),
                        kelly_stake=Decimal('0'),
                        risk_score=Decimal('1'),
                        liquidity_score=Decimal('1'),
                        freshness_score=Decimal('1'),
                        historical_success_rate=Decimal('0'),
                        quality_score=Decimal('0'),
                        priority_score=Decimal('0'),
                        estimated_execution_time=0,
                        confidence_level=Decimal('1')
                    )).priority_score,
                    reverse=True
                )[:self.max_opportunities]
                
                # Store opportunities and metrics
                for opp in sorted_opportunities:
                    self._opportunities[opp.id] = opp
                    self._metrics[opp.id] = metrics[opp.id]
                
                # Clear screen and display
                print("\033[2J\033[H", end="")
                await self._display_header()
                await self._display_opportunity_table(sorted_opportunities, metrics)
                
        except Exception as e:
            logger.error(f"Error displaying opportunities: {e}")
            logger.error(traceback.format_exc())
    
    async def _display_header(self) -> None:
        """Display header information."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"🕐 Last Updated: {current_time}")
        print(f"📊 Total Opportunities: {len(self._opportunities)}")
        print("=" * 100)
    
    async def _display_opportunity_table(
        self, 
        opportunities: List[ArbitrageOpportunity],
        metrics: Dict[UUID, OpportunityMetrics]
    ) -> None:
        """Display opportunities in table format."""
        try:
            # Table headers
            headers = [
                "Rank", "Event", "Sport", "Profit", "Kelly Stake", "Risk", 
                "Success Rate", "Quality", "Time Left"
            ]
            col_widths = [5, 25, 10, 12, 12, 8, 12, 10, 10]
            
            # Print headers
            header_line = "|".join([f" {h:<{w-1}}" for h, w in zip(headers, col_widths)])
            print(f"|{header_line}|")
            print("|" + "|".join(["-" * (w-1) for w in col_widths]) + "|")
            
            # Print opportunities
            for i, opportunity in enumerate(opportunities, 1):
                metric = metrics.get(opportunity.id)
                if not metric:
                    continue
                
                event_name = opportunity.event_name[:22] + "..." if len(opportunity.event_name) > 22 else opportunity.event_name
                profit_text = f"{metric.profit_margin:.2%} (${metric.profit_amount:.2f})"
                kelly_text = f"{metric.kelly_fraction:.1%} (${metric.kelly_stake:.2f})"
                risk_emoji = "🟢" if metric.risk_score < 0.3 else "🟡" if metric.risk_score < 0.7 else "🔴"
                success_text = f"{metric.historical_success_rate:.1%}"
                quality_text = f"{metric.quality_score:.1%}"
                
                # Calculate time remaining
                if opportunity.expires_at:
                    time_left = max(0, int((opportunity.expires_at - datetime.utcnow()).total_seconds()))
                    if time_left > 3600:
                        time_text = f"{time_left//3600}h"
                    elif time_left > 60:
                        time_text = f"{time_left//60}m"
                    else:
                        time_text = f"{time_left}s"
                else:
                    time_text = "∞"
                
                row_data = [
                    str(i),
                    event_name,
                    opportunity.sport.value.title()[:8],
                    profit_text,
                    kelly_text,
                    risk_emoji,
                    success_text,
                    quality_text,
                    time_text
                ]
                
                row_line = "|".join([f" {data:<{w-1}}" for data, w in zip(row_data, col_widths)])
                print(f"|{row_line}|")
                
                # Print leg details for top opportunities
                if i <= 5:
                    await self._display_leg_details(opportunity, i)
            
            print("=" * 100)
            
        except Exception as e:
            logger.error(f"Error displaying opportunity table: {e}")
    
    async def _display_leg_details(self, opportunity: ArbitrageOpportunity, rank: int) -> None:
        """Display detailed leg information for an opportunity."""
        try:
            print(f"\n  📋 Rank #{rank} - Leg Details:")
            for i, leg in enumerate(opportunity.legs, 1):
                print(f"    {i}. {leg.bookmaker}: {leg.event_outcome}")
                print(f"       Odds: {leg.odds:.3f} | Stake: ${leg.actual_stake:.2f} ({leg.stake_percentage:.1%})")
            
        except Exception as e:
            logger.error(f"Error displaying leg details: {e}")
    
    async def update_opportunity(self, opportunity: ArbitrageOpportunity, metrics: OpportunityMetrics) -> None:
        """Update single opportunity display."""
        try:
            with self._lock:
                self._opportunities[opportunity.id] = opportunity
                self._metrics[opportunity.id] = metrics
                
                # Refresh display
                await self.display_opportunities(list(self._opportunities.values()), self._metrics)
                
        except Exception as e:
            logger.error(f"Error updating opportunity: {e}")
    
    async def remove_opportunity(self, opportunity_id: UUID) -> None:
        """Remove opportunity from display."""
        try:
            with self._lock:
                self._opportunities.pop(opportunity_id, None)
                self._metrics.pop(opportunity_id, None)
                
                # Refresh display
                await self.display_opportunities(list(self._opportunities.values()), self._metrics)
                
        except Exception as e:
            logger.error(f"Error removing opportunity: {e}")
    
    async def display_comparison(self, comparison: ComparisonData) -> None:
        """Display opportunity comparison."""
        try:
            print("\n" + "=" * 80)
            print("🔍 OPPORTUNITY COMPARISON")
            print("=" * 80)
            
            # Display primary opportunity
            primary = comparison.primary_opportunity
            print(f"\n📊 PRIMARY OPPORTUNITY:")
            print(f"Event: {primary.event_name}")
            print(f"Sport: {primary.sport.value.title()}")
            print(f"Market: {primary.market_type}")
            print(f"Profit Margin: {primary.profit_margin:.2%}")
            print(f"Risk Tier: {primary.risk_tier.value.upper()}")
            
            # Display comparisons
            print(f"\n📈 COMPARISON WITH OTHER OPPORTUNITIES:")
            for i, opp_id in enumerate(comparison.recommended_ranks[:5], 1):
                opp = next((o for o in comparison.secondary_opportunities if o.id == opp_id), None)
                if opp and opp.id in comparison.metrics:
                    metric = comparison.metrics[opp.id]
                    print(f"{i}. {opp.event_name[:40]}...")
                    print(f"   Profit: {metric.profit_margin:.2%} | Success: {metric.historical_success_rate:.1%} | Quality: {metric.quality_score:.1%}")
            
            print("=" * 80)
            
        except Exception as e:
            logger.error(f"Error displaying comparison: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown console presenter."""
        try:
            print("\n🔴 Console presenter shutting down...")
            
        except Exception as e:
            logger.error(f"Error shutting down console presenter: {e}")


class WebPresenter(OpportunityPresenterInterface):
    """Web-based opportunity presenter using WebSockets."""
    
    def __init__(self, host: str = "localhost", port: int = 8765, max_clients: int = 50):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.server = None
        self.clients: set = set()
        self._lock = threading.RLock()
        self._running = False
    
    async def initialize(self) -> None:
        """Initialize web presenter."""
        try:
            logger.info(f"Initializing web presenter on {self.host}:{self.port}")
            
            # Start WebSocket server
            self._running = True
            self.server = await websockets.serve(
                self._handle_client,
                self.host,
                self.port,
                max_connections=self.max_clients
            )
            
            logger.info(f"Web presenter server started on ws://{self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Error initializing web presenter: {e}")
            raise
    
    async def _handle_client(self, websocket, path):
        """Handle WebSocket client connection."""
        try:
            async with websocket:
                logger.info(f"New client connected: {websocket.remote_address}")
                
                # Send welcome message
                welcome_message = {
                    "type": "welcome",
                    "message": "Connected to ARBitech HITL Opportunity Presenter",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send(json.dumps(welcome_message))
                
                self.clients.add(websocket)
                
                # Keep connection alive and handle messages
                async for message in websocket:
                    try:
                        # Echo messages back for now
                        response = {
                            "type": "echo",
                            "message": f"Received: {message}",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await websocket.send(json.dumps(response))
                        
                    except websockets.exceptions.ConnectionClosed:
                        break
                        
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client disconnected: {websocket.remote_address}")
    
    async def _broadcast_message(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        try:
            if not self.clients:
                return
            
            # Create JSON message
            json_message = json.dumps(message, default=str)
            
            # Send to all clients
            disconnected_clients = set()
            for client in self.clients.copy():
                try:
                    await client.send(json_message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected_clients.add(client)
                except Exception as e:
                    logger.error(f"Error sending to client: {e}")
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self.clients -= disconnected_clients
            
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
    
    async def display_opportunities(
        self, 
        opportunities: List[ArbitrageOpportunity],
        metrics: Dict[UUID, OpportunityMetrics]
    ) -> None:
        """Display opportunities via WebSocket."""
        try:
            message = {
                "type": "opportunities_update",
                "data": {
                    "opportunities": [asdict(self._serialize_opportunity(opp)) for opp in opportunities],
                    "metrics": {str(k): asdict(v) for k, v in metrics.items()},
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await self._broadcast_message(message)
            
        except Exception as e:
            logger.error(f"Error displaying opportunities: {e}")
    
    def _serialize_opportunity(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Serialize opportunity for JSON transmission."""
        try:
            serialized = asdict(opportunity)
            # Convert Decimal objects to float for JSON serialization
            serialized = self._convert_decimals(serialized)
            return serialized
            
        except Exception as e:
            logger.error(f"Error serializing opportunity: {e}")
            return {}
    
    def _convert_decimals(self, obj: Any) -> Any:
        """Convert Decimal objects to float for JSON serialization."""
        try:
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: self._convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [self._convert_decimals(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, UUID):
                return str(obj)
            else:
                return obj
                
        except Exception as e:
            logger.error(f"Error converting decimals: {e}")
            return obj
    
    async def update_opportunity(self, opportunity: ArbitrageOpportunity, metrics: OpportunityMetrics) -> None:
        """Update single opportunity via WebSocket."""
        try:
            message = {
                "type": "opportunity_update",
                "data": {
                    "opportunity": self._serialize_opportunity(opportunity),
                    "metrics": asdict(metrics),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await self._broadcast_message(message)
            
        except Exception as e:
            logger.error(f"Error updating opportunity: {e}")
    
    async def remove_opportunity(self, opportunity_id: UUID) -> None:
        """Remove opportunity via WebSocket."""
        try:
            message = {
                "type": "opportunity_removed",
                "data": {
                    "opportunity_id": str(opportunity_id),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await self._broadcast_message(message)
            
        except Exception as e:
            logger.error(f"Error removing opportunity: {e}")
    
    async def display_comparison(self, comparison: ComparisonData) -> None:
        """Display opportunity comparison via WebSocket."""
        try:
            message = {
                "type": "opportunity_comparison",
                "data": {
                    "primary_opportunity": self._serialize_opportunity(comparison.primary_opportunity),
                    "secondary_opportunities": [self._serialize_opportunity(opp) for opp in comparison.secondary_opportunities],
                    "metrics": {str(k): asdict(v) for k, v in comparison.metrics.items()},
                    "recommended_ranks": [str(uid) for uid in comparison.recommended_ranks],
                    "comparative_analysis": comparison.comparative_analysis,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            await self._broadcast_message(message)
            
        except Exception as e:
            logger.error(f"Error displaying comparison: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown web presenter."""
        try:
            logger.info("Shutting down web presenter")
            self._running = False
            
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            
            # Close all client connections
            for client in self.clients.copy():
                try:
                    await client.close()
                except Exception:
                    pass
            
            logger.info("Web presenter shutdown complete")
            
        except Exception as e:
            logger.error(f"Error shutting down web presenter: {e}")


class GUIPresenter(OpportunityPresenterInterface):
    """GUI-based opportunity presenter (placeholder for future implementation)."""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize GUI presenter."""
        try:
            logger.info("Initializing GUI presenter")
            # Placeholder for GUI implementation
            self._initialized = True
            logger.info("GUI presenter initialized (placeholder)")
            
        except Exception as e:
            logger.error(f"Error initializing GUI presenter: {e}")
            raise
    
    async def display_opportunities(
        self, 
        opportunities: List[ArbitrageOpportunity],
        metrics: Dict[UUID, OpportunityMetrics]
    ) -> None:
        """Display opportunities in GUI."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Placeholder for GUI implementation
            logger.info(f"GUI: Displaying {len(opportunities)} opportunities")
            
        except Exception as e:
            logger.error(f"Error displaying opportunities in GUI: {e}")
    
    async def update_opportunity(self, opportunity: ArbitrageOpportunity, metrics: OpportunityMetrics) -> None:
        """Update opportunity in GUI."""
        try:
            # Placeholder for GUI implementation
            logger.info(f"GUI: Updating opportunity {opportunity.id}")
            
        except Exception as e:
            logger.error(f"Error updating opportunity in GUI: {e}")
    
    async def remove_opportunity(self, opportunity_id: UUID) -> None:
        """Remove opportunity from GUI."""
        try:
            # Placeholder for GUI implementation
            logger.info(f"GUI: Removing opportunity {opportunity_id}")
            
        except Exception as e:
            logger.error(f"Error removing opportunity from GUI: {e}")
    
    async def display_comparison(self, comparison: ComparisonData) -> None:
        """Display opportunity comparison in GUI."""
        try:
            # Placeholder for GUI implementation
            logger.info("GUI: Displaying opportunity comparison")
            
        except Exception as e:
            logger.error(f"Error displaying comparison in GUI: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown GUI presenter."""
        try:
            logger.info("GUI presenter shutting down")
            self._initialized = False
            
        except Exception as e:
            logger.error(f"Error shutting down GUI presenter: {e}")


class OpportunityRanker:
    """Advanced opportunity ranking and comparison system."""
    
    def __init__(self):
        self.weight_config = {
            'profit_margin': 0.25,
            'kelly_fraction': 0.20,
            'historical_success': 0.20,
            'risk_score': 0.15,
            'liquidity_score': 0.10,
            'freshness_score': 0.10
        }
        self._lock = threading.RLock()
    
    def calculate_priority_score(self, opportunity: ArbitrageOpportunity, metrics: OpportunityMetrics) -> Decimal:
        """Calculate comprehensive priority score for an opportunity."""
        try:
            with self._lock:
                score = Decimal('0')
                
                # Profit margin score (0-1, normalized)
                profit_score = min(Decimal('1.0'), metrics.profit_margin / Decimal('0.1'))  # Normalize to 10%
                score += profit_score * self.weight_config['profit_margin']
                
                # Kelly fraction score (prefer moderate Kelly)
                kelly_score = min(
                    Decimal('1.0'),
                    metrics.kelly_fraction / Decimal('0.25')
                )
                if metrics.kelly_fraction > Decimal('0.5'):  # Penalize over-aggressive Kelly
                    kelly_score *= Decimal('0.5')
                score += kelly_score * self.weight_config['kelly_fraction']
                
                # Historical success rate score
                score += metrics.historical_success_rate * self.weight_config['historical_success']
                
                # Risk score (inverse - lower risk is better)
                risk_score = Decimal('1.0') - metrics.risk_score
                score += risk_score * self.weight_config['risk_score']
                
                # Liquidity score
                score += metrics.liquidity_score * self.weight_config['liquidity_score']
                
                # Freshness score (inverse of age)
                freshness_score = Decimal('1.0') - (metrics.freshness_score)
                score += freshness_score * self.weight_config['freshness_score']
                
                return min(Decimal('1.0'), score)
                
        except Exception as e:
            logger.error(f"Error calculating priority score: {e}")
            return Decimal('0.5')
    
    def rank_opportunities(
        self, 
        opportunities: List[ArbitrageOpportunity],
        metrics: Dict[UUID, OpportunityMetrics]
    ) -> List[Tuple[ArbitrageOpportunity, OpportunityMetrics, Decimal]]:
        """Rank opportunities by priority score."""
        try:
            with self._lock:
                ranked = []
                
                for opportunity in opportunities:
                    if opportunity.id not in metrics:
                        continue
                    
                    metrics_obj = metrics[opportunity.id]
                    priority_score = self.calculate_priority_score(opportunity, metrics_obj)
                    ranked.append((opportunity, metrics_obj, priority_score))
                
                # Sort by priority score descending
                ranked.sort(key=lambda x: x[2], reverse=True)
                
                return ranked
                
        except Exception as e:
            logger.error(f"Error ranking opportunities: {e}")
            return []
    
    def compare_opportunities(
        self,
        primary_opportunity: ArbitrageOpportunity,
        secondary_opportunities: List[ArbitrageOpportunity],
        metrics: Dict[UUID, OpportunityMetrics]
    ) -> ComparisonData:
        """Compare opportunities and provide recommendations."""
        try:
            # Calculate metrics for all opportunities
            all_metrics = {}
            for opp in [primary_opportunity] + secondary_opportunities:
                if opp.id in metrics:
                    all_metrics[opp.id] = metrics[opp.id]
            
            # Rank all opportunities
            ranked_list = self.rank_opportunities([primary_opportunity] + secondary_opportunities, all_metrics)
            
            # Get recommended ranks
            recommended_ranks = [opp.id for opp, _, _ in ranked_list]
            
            # Perform comparative analysis
            comparative_analysis = self._perform_comparative_analysis(
                primary_opportunity, secondary_opportunities, all_metrics
            )
            
            return ComparisonData(
                primary_opportunity=primary_opportunity,
                secondary_opportunities=secondary_opportunities,
                metrics=all_metrics,
                recommended_ranks=recommended_ranks,
                comparative_analysis=comparative_analysis
            )
            
        except Exception as e:
            logger.error(f"Error comparing opportunities: {e}")
            return ComparisonData(
                primary_opportunity=primary_opportunity,
                secondary_opportunities=secondary_opportunities,
                metrics=metrics,
                recommended_ranks=[],
                comparative_analysis={}
            )
    
    def _perform_comparative_analysis(
        self,
        primary_opportunity: ArbitrageOpportunity,
        secondary_opportunities: List[ArbitrageOpportunity],
        metrics: Dict[UUID, OpportunityMetrics]
    ) -> Dict[str, Any]:
        """Perform detailed comparative analysis."""
        try:
            analysis = {
                'total_opportunities': len(secondary_opportunities) + 1,
                'avg_profit_margin': Decimal('0'),
                'best_profit_opportunity': None,
                'lowest_risk_opportunity': None,
                'highest_success_rate': None,
                'risk_distribution': {'tier_a': 0, 'tier_b': 0, 'tier_c': 0, 'tier_d': 0},
                'sport_distribution': {},
                'recommendations': []
            }
            
            # Analyze profit margins
            profit_margins = []
            best_profit = Decimal('0')
            best_profit_opp = None
            
            # Analyze risk tiers
            risk_counts = {'tier_a': 0, 'tier_b': 0, 'tier_c': 0, 'tier_d': 0}
            
            # Analyze sports distribution
            sport_counts = {}
            
            all_opportunities = [primary_opportunity] + secondary_opportunities
            for opp in all_opportunities:
                if opp.id in metrics:
                    metric = metrics[opp.id]
                    
                    # Profit analysis
                    profit_margins.append(metric.profit_margin)
                    if metric.profit_margin > best_profit:
                        best_profit = metric.profit_margin
                        best_profit_opp = opp
                    
                    # Risk tier analysis
                    risk_counts[opp.risk_tier.value] += 1
                    
                    # Sport analysis
                    sport = opp.sport.value
                    sport_counts[sport] = sport_counts.get(sport, 0) + 1
            
            # Calculate averages
            if profit_margins:
                analysis['avg_profit_margin'] = sum(profit_margins) / len(profit_margins)
            
            analysis['best_profit_opportunity'] = best_profit_opp.id if best_profit_opp else None
            analysis['risk_distribution'] = risk_counts
            analysis['sport_distribution'] = sport_counts
            
            # Generate recommendations
            recommendations = []
            
            if best_profit_opp:
                recommendations.append({
                    'type': 'highest_profit',
                    'opportunity_id': best_profit_opp.id,
                    'message': f"Highest profit margin: {best_profit:.2%}"
                })
            
            # Find lowest risk opportunity
            lowest_risk_score = Decimal('1.0')
            lowest_risk_opp = None
            for opp in all_opportunities:
                if opp.id in metrics and metrics[opp.id].risk_score < lowest_risk_score:
                    lowest_risk_score = metrics[opp.id].risk_score
                    lowest_risk_opp = opp
            
            if lowest_risk_opp:
                analysis['lowest_risk_opportunity'] = lowest_risk_opp.id
                recommendations.append({
                    'type': 'lowest_risk',
                    'opportunity_id': lowest_risk_opp.id,
                    'message': f"Lowest risk score: {lowest_risk_score:.2%}"
                })
            
            analysis['recommendations'] = recommendations
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error performing comparative analysis: {e}")
            return {}


class OpportunityPresenterSystem:
    """
    Main opportunity presentation system for HITL mode.
    
    Coordinates multiple presenters, real-time updates, and comprehensive
    opportunity analysis and presentation.
    """
    
    def __init__(
        self,
        display_formats: List[DisplayFormat] = None,
        max_opportunities: int = 50,
        update_interval: float = 5.0,
        historical_store_size: int = 10000
    ):
        """Initialize the opportunity presentation system."""
        try:
            # Configuration
            self.display_formats = display_formats or [DisplayFormat.CONSOLE]
            self.max_opportunities = max_opportunities
            self.update_interval = update_interval
            self.running = False
            
            # Core components
            self.presenters: Dict[DisplayFormat, OpportunityPresenterInterface] = {}
            self.ranker = OpportunityRanker()
            self.historical_store = HistoricalDataStore(historical_store_size)
            
            # State tracking
            self._opportunities: Dict[UUID, ArbitrageOpportunity] = {}
            self._metrics: Dict[UUID, OpportunityMetrics] = {}
            self._events: deque = deque(maxlen=1000)
            self._lock = threading.RLock()
            
            # Integration components
            self.scanner: Optional[OpportunityScanner] = None
            self.kelly_calculator: Optional[KellyCalculator] = None
            self.risk_analyzer: Optional[RiskAnalyzer] = None
            self.audit_logger: Optional[AuditLogger] = None
            
            # Event handlers
            self.event_handlers: Dict[PresentationEventType, List[Callable]] = {
                event_type: [] for event_type in PresentationEventType
            }
            
            logger.info(f"OpportunityPresenterSystem initialized with formats: {[f.value for f in self.display_formats]}")
            
        except Exception as e:
            logger.error(f"Error initializing OpportunityPresenterSystem: {e}")
            raise
    
    def integrate_scanner(self, scanner: OpportunityScanner) -> None:
        """Integrate with opportunity scanner for real-time updates."""
        try:
            self.scanner = scanner
            scanner.add_event_handler(self._handle_scanner_event)
            logger.info("Scanner integration established")
            
        except Exception as e:
            logger.error(f"Error integrating scanner: {e}")
    
    def integrate_kelly_calculator(self, kelly_calculator: KellyCalculator) -> None:
        """Integrate with Kelly calculator for stake calculations."""
        try:
            self.kelly_calculator = kelly_calculator
            logger.info("Kelly calculator integration established")
            
        except Exception as e:
            logger.error(f"Error integrating Kelly calculator: {e}")
    
    def integrate_risk_analyzer(self, risk_analyzer: RiskAnalyzer) -> None:
        """Integrate with risk analyzer for risk assessment."""
        try:
            self.risk_analyzer = risk_analyzer
            logger.info("Risk analyzer integration established")
            
        except Exception as e:
            logger.error(f"Error integrating risk analyzer: {e}")
    
    def integrate_audit_logger(self, audit_logger: AuditLogger) -> None:
        """Integrate with audit logger for comprehensive logging."""
        try:
            self.audit_logger = audit_logger
            logger.info("Audit logger integration established")
            
        except Exception as e:
            logger.error(f"Error integrating audit logger: {e}")
    
    async def initialize_presenters(self) -> None:
        """Initialize all configured presenters."""
        try:
            logger.info("Initializing presenters...")
            
            for format_type in self.display_formats:
                try:
                    if format_type == DisplayFormat.CONSOLE:
                        presenter = ConsolePresenter(self.max_opportunities)
                    elif format_type == DisplayFormat.WEB:
                        presenter = WebPresenter()
                    elif format_type == DisplayFormat.GUI:
                        presenter = GUIPresenter()
                    elif format_type == DisplayFormat.JSON:
                        presenter = ConsolePresenter(self.max_opportunities)  # Reuse console for JSON output
                    else:
                        logger.warning(f"Unknown display format: {format_type}")
                        continue
                    
                    await presenter.initialize()
                    self.presenters[format_type] = presenter
                    logger.info(f"Initialized {format_type.value} presenter")
                    
                except Exception as e:
                    logger.error(f"Error initializing {format_type.value} presenter: {e}")
                    # Continue with other presenters
            
            logger.info(f"Successfully initialized {len(self.presenters)} presenters")
            
        except Exception as e:
            logger.error(f"Error initializing presenters: {e}")
            raise
    
    async def add_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> None:
        """Add new opportunities to the presentation system."""
        try:
            with self._lock:
                new_opportunities = []
                
                for opportunity in opportunities:
                    # Skip if opportunity already exists
                    if opportunity.id in self._opportunities:
                        continue
                    
                    # Calculate metrics
                    metrics = await self._calculate_opportunity_metrics(opportunity)
                    if metrics:
                        self._opportunities[opportunity.id] = opportunity
                        self._metrics[opportunity.id] = metrics
                        new_opportunities.append(opportunity)
                        
                        # Log event
                        await self._log_event(
                            PresentationEventType.OPPORTUNITY_ADDED,
                            {"opportunity_id": str(opportunity.id), "event_name": opportunity.event_name}
                        )
                
                # Update displays
                if new_opportunities:
                    await self._update_displays()
                    
                logger.info(f"Added {len(new_opportunities)} new opportunities")
                
        except Exception as e:
            logger.error(f"Error adding opportunities: {e}")
            logger.error(traceback.format_exc())
    
    async def update_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> None:
        """Update existing opportunities."""
        try:
            with self._lock:
                updated_count = 0
                
                for opportunity in opportunities:
                    if opportunity.id not in self._opportunities:
                        continue
                    
                    # Recalculate metrics
                    metrics = await self._calculate_opportunity_metrics(opportunity)
                    if metrics:
                        self._opportunities[opportunity.id] = opportunity
                        self._metrics[opportunity.id] = metrics
                        updated_count += 1
                        
                        # Log event
                        await self._log_event(
                            PresentationEventType.OPPORTUNITY_UPDATED,
                            {"opportunity_id": str(opportunity.id), "event_name": opportunity.event_name}
                        )
                
                # Update displays
                if updated_count > 0:
                    await self._update_displays()
                    
                logger.info(f"Updated {updated_count} opportunities")
                
        except Exception as e:
            logger.error(f"Error updating opportunities: {e}")
            logger.error(traceback.format_exc())
    
    async def remove_opportunities(self, opportunity_ids: List[UUID]) -> None:
        """Remove opportunities from the presentation system."""
        try:
            with self._lock:
                removed_count = 0
                
                for opp_id in opportunity_ids:
                    if opp_id in self._opportunities:
                        del self._opportunities[opp_id]
                        del self._metrics[opp_id]
                        removed_count += 1
                        
                        # Update displays
                        for presenter in self.presenters.values():
                            await presenter.remove_opportunity(opp_id)
                        
                        # Log event
                        await self._log_event(
                            PresentationEventType.OPPORTUNITY_REMOVED,
                            {"opportunity_id": str(opp_id)}
                        )
                
                logger.info(f"Removed {removed_count} opportunities")
                
        except Exception as e:
            logger.error(f"Error removing opportunities: {e}")
            logger.error(traceback.format_exc())
    
    async def _calculate_opportunity_metrics(self, opportunity: ArbitrageOpportunity) -> Optional[OpportunityMetrics]:
        """Calculate comprehensive metrics for an opportunity."""
        try:
            # Basic metrics
            metrics = OpportunityMetrics(
                opportunity_id=opportunity.id,
                profit_margin=opportunity.profit_margin,
                profit_amount=opportunity.profit_amount,
                kelly_fraction=Decimal('0'),  # To be calculated
                kelly_stake=Decimal('0'),      # To be calculated
                risk_score=Decimal('0.5'),     # Default risk score
                liquidity_score=Decimal('0.5'), # Default liquidity score
                freshness_score=Decimal('0.5'), # Default freshness score
                historical_success_rate=Decimal('0'), # To be calculated
                quality_score=Decimal('0'),    # To be calculated
                priority_score=Decimal('0'),   # To be calculated
                estimated_execution_time=0,    # To be estimated
                confidence_level=Decimal('0.8') # Default confidence
            )
            
            # Calculate Kelly stakes if Kelly calculator is available
            if self.kelly_calculator:
                try:
                    kelly_config = KellyConfig(mode=KellyMode.FRACTIONAL, fractional_factor=Decimal('0.25'))
                    
                    # Calculate Kelly fraction for each leg
                    kelly_fractions = []
                    for leg in opportunity.legs:
                        kelly_result = await self.kelly_calculator.calculate_kelly(
                            odds=leg.odds,
                            estimated_probability=leg.implied_probability,
                            config=kelly_config
                        )
                        if kelly_result:
                            kelly_fractions.append(kelly_result.fraction)
                    
                    if kelly_fractions:
                        # Use average Kelly fraction
                        metrics.kelly_fraction = sum(kelly_fractions) / len(kelly_fractions)
                        metrics.kelly_stake = opportunity.total_stake * metrics.kelly_fraction
                        
                except Exception as e:
                    logger.warning(f"Error calculating Kelly stakes for {opportunity.id}: {e}")
            
            # Calculate risk score if risk analyzer is available
            if self.risk_analyzer:
                try:
                    risk_analysis = await self.risk_analyzer.analyze_opportunity(opportunity)
                    if risk_analysis:
                        metrics.risk_score = risk_analysis.overall_risk_score
                        
                except Exception as e:
                    logger.warning(f"Error calculating risk score for {opportunity.id}: {e}")
            
            # Calculate freshness score based on odds age
            try:
                age_minutes = (datetime.utcnow() - opportunity.odds_freshness).total_seconds() / 60
                metrics.freshness_score = max(Decimal('0'), Decimal('1') - (age_minutes / Decimal('60')))  # Decay over 1 hour
                
            except Exception as e:
                logger.warning(f"Error calculating freshness score for {opportunity.id}: {e}")
            
            # Get historical performance data
            try:
                historical_data = self.historical_store.get_historical_performance(
                    opportunity.sport,
                    opportunity.market_type,
                    opportunity.risk_tier,
                    opportunity.profit_margin
                )
                
                if historical_data:
                    metrics.historical_success_rate = historical_data.success_rate
                    metrics.confidence_level = min(Decimal('1.0'), historical_data.performance_score + Decimal('0.1'))
                    
            except Exception as e:
                logger.warning(f"Error getting historical data for {opportunity.id}: {e}")
            
            # Calculate quality score
            try:
                quality_factors = [
                    metrics.profit_margin / Decimal('0.05'),  # Normalize to 5%
                    Decimal('1.0') - metrics.risk_score,     # Inverse of risk
                    metrics.historical_success_rate,         # Historical success
                    metrics.freshness_score,                 # Data freshness
                    min(Decimal('1.0'), metrics.confidence_level)  # Confidence level
                ]
                
                metrics.quality_score = sum(quality_factors) / len(quality_factors)
                
            except Exception as e:
                logger.warning(f"Error calculating quality score for {opportunity.id}: {e}")
            
            # Calculate priority score using ranker
            try:
                metrics.priority_score = self.ranker.calculate_priority_score(opportunity, metrics)
                
            except Exception as e:
                logger.warning(f"Error calculating priority score for {opportunity.id}: {e}")
            
            # Estimate execution time
            try:
                # Base execution time + risk-based adjustment
                base_time = 30000  # 30 seconds base
                risk_adjustment = int(metrics.risk_score * 30000)  # Up to 30s additional
                metrics.estimated_execution_time = base_time + risk_adjustment
                
            except Exception as e:
                logger.warning(f"Error estimating execution time for {opportunity.id}: {e}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating opportunity metrics: {e}")
            logger.error(traceback.format_exc())
            return None
    
    async def _update_displays(self) -> None:
        """Update all displays with current opportunities."""
        try:
            if not self.presenters:
                return
            
            opportunities = list(self._opportunities.values())
            metrics = self._metrics.copy()
            
            # Update all presenters
            for presenter in self.presenters.values():
                try:
                    await presenter.display_opportunities(opportunities, metrics)
                except Exception as e:
                    logger.error(f"Error updating presenter: {e}")
            
            # Log display update
            await self._log_event(
                PresentationEventType.DISPLAY_UPDATED,
                {
                    "opportunity_count": len(opportunities),
                    "presenter_count": len(self.presenters)
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating displays: {e}")
    
    async def _handle_scanner_event(self, event_type: ScannerEventType, data: Dict[str, Any]) -> None:
        """Handle events from the opportunity scanner."""
        try:
            logger.debug(f"Handling scanner event: {event_type}")
            
            if event_type == ScannerEventType.OPPORTUNITY_FOUND:
                # Convert scanner event data to opportunities
                opportunities_data = data.get('opportunities', [])
                opportunities = self._convert_scanner_data_to_opportunities(opportunities_data)
                
                if opportunities:
                    await self.add_opportunities(opportunities)
            
            elif event_type == ScannerEventType.SCAN_FAILED:
                # Log scan failure
                await self._log_event(
                    PresentationEventType.ERROR_OCCURRED,
                    {"error_type": "scan_failed", "error_data": data}
                )
            
        except Exception as e:
            logger.error(f"Error handling scanner event: {e}")
    
    def _convert_scanner_data_to_opportunities(self, scanner_data: List[Dict[str, Any]]) -> List[ArbitrageOpportunity]:
        """Convert scanner event data to ArbitrageOpportunity objects."""
        try:
            opportunities = []
            
            for data in scanner_data:
                # This is a placeholder - implement actual conversion logic
                # based on scanner output format
                logger.debug(f"Converting scanner data: {data}")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error converting scanner data: {e}")
            return []
    
    async def add_performance_data(self, trade: Trade) -> None:
        """Add performance data from completed trades."""
        try:
            self.historical_store.add_performance_data(trade)
            
            # Update quality scores of similar opportunities
            opportunity = trade.opportunity
            if opportunity.id in self._opportunities:
                # Recalculate metrics for this opportunity
                new_metrics = await self._calculate_opportunity_metrics(opportunity)
                if new_metrics:
                    self._metrics[opportunity.id] = new_metrics
                    await self._update_displays()
            
            logger.info(f"Added performance data from trade {trade.id}")
            
        except Exception as e:
            logger.error(f"Error adding performance data: {e}")
    
    async def compare_opportunities(
        self,
        primary_opportunity_id: UUID,
        secondary_opportunity_ids: List[UUID] = None
    ) -> Optional[ComparisonData]:
        """Compare opportunities and provide analysis."""
        try:
            with self._lock:
                if primary_opportunity_id not in self._opportunities:
                    logger.warning(f"Primary opportunity {primary_opportunity_id} not found")
                    return None
                
                primary_opportunity = self._opportunities[primary_opportunity_id]
                secondary_opportunities = []
                
                # Get secondary opportunities
                if secondary_opportunity_ids:
                    for opp_id in secondary_opportunity_ids:
                        if opp_id in self._opportunities and opp_id != primary_opportunity_id:
                            secondary_opportunities.append(self._opportunities[opp_id])
                else:
                    # Auto-select top 5 secondary opportunities
                    secondary_opportunities = [
                        opp for opp_id, opp in self._opportunities.items()
                        if opp_id != primary_opportunity_id
                    ][:5]
                
                # Perform comparison
                comparison = self.ranker.compare_opportunities(
                    primary_opportunity,
                    secondary_opportunities,
                    self._metrics
                )
                
                # Display comparison on all presenters
                for presenter in self.presenters.values():
                    await presenter.display_comparison(comparison)
                
                # Log comparison
                await self._log_event(
                    PresentationEventType.OPPORTUNITY_RANKED,
                    {
                        "primary_opportunity_id": str(primary_opportunity_id),
                        "secondary_opportunity_count": len(secondary_opportunities)
                    }
                )
                
                return comparison
                
        except Exception as e:
            logger.error(f"Error comparing opportunities: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def add_event_handler(self, event_type: PresentationEventType, handler: Callable) -> None:
        """Add event handler for presentation events."""
        try:
            if event_type in self.event_handlers:
                self.event_handlers[event_type].append(handler)
                logger.info(f"Added event handler for {event_type}")
            else:
                logger.warning(f"Unknown event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error adding event handler: {e}")
    
    async def _log_event(self, event_type: PresentationEventType, data: Dict[str, Any]) -> None:
        """Log presentation events."""
        try:
            event = PresentationEvent(
                type=event_type,
                timestamp=datetime.utcnow(),
                data=data,
                source="opportunity_presenter"
            )
            
            self._events.append(event)
            
            # Log to audit logger if available
            if self.audit_logger:
                try:
                    await self.audit_logger.log_event(
                        event_type=f"opportunity_presenter_{event_type.value}",
                        data=asdict(event),
                        level="INFO"
                    )
                except Exception as e:
                    logger.warning(f"Error logging to audit logger: {e}")
            
            # Notify event handlers
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler: {e}")
            
        except Exception as e:
            logger.error(f"Error logging event: {e}")
    
    async def start(self) -> None:
        """Start the opportunity presentation system."""
        try:
            if self.running:
                logger.warning("Presentation system already running")
                return
            
            self.running = True
            logger.info("Starting opportunity presentation system")
            
            # Initialize presenters
            await self.initialize_presenters()
            
            logger.info("Opportunity presentation system started successfully")
            
        except Exception as e:
            logger.error(f"Error starting presentation system: {e}")
            self.running = False
            raise
    
    async def stop(self) -> None:
        """Stop the opportunity presentation system."""
        try:
            if not self.running:
                logger.warning("Presentation system not running")
                return
            
            self.running = False
            logger.info("Stopping opportunity presentation system")
            
            # Shutdown all presenters
            for format_type, presenter in self.presenters.items():
                try:
                    await presenter.shutdown()
                    logger.info(f"Shut down {format_type.value} presenter")
                except Exception as e:
                    logger.error(f"Error shutting down {format_type.value} presenter: {e}")
            
            self.presenters.clear()
            
            logger.info("Opportunity presentation system stopped")
            
        except Exception as e:
            logger.error(f"Error stopping presentation system: {e}")
    
    def get_opportunities(self) -> Dict[UUID, ArbitrageOpportunity]:
        """Get current opportunities."""
        with self._lock:
            return self._opportunities.copy()
    
    def get_metrics(self) -> Dict[UUID, OpportunityMetrics]:
        """Get current metrics."""
        with self._lock:
            return self._metrics.copy()
    
    def get_events(self, limit: int = 100) -> List[PresentationEvent]:
        """Get recent presentation events."""
        with self._lock:
            return list(self._events)[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            with self._lock:
                return {
                    'total_opportunities': len(self._opportunities),
                    'active_presenters': len(self.presenters),
                    'event_count': len(self._events),
                    'historical_entries': len(self.historical_store.data),
                    'aggregated_stats': len(self.historical_store.aggregated_stats),
                    'running': self.running,
                    'last_update': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


# Utility functions for easy integration

async def create_hitl_presenter(
    display_formats: List[DisplayFormat] = None,
    scanner: Optional[OpportunityScanner] = None,
    kelly_calculator: Optional[KellyCalculator] = None,
    risk_analyzer: Optional[RiskAnalyzer] = None,
    audit_logger: Optional[AuditLogger] = None,
    **kwargs
) -> OpportunityPresenterSystem:
    """Create and configure HITL opportunity presenter system."""
    try:
        presenter_system = OpportunityPresenterSystem(
            display_formats=display_formats,
            **kwargs
        )
        
        # Integrate components if provided
        if scanner:
            presenter_system.integrate_scanner(scanner)
        if kelly_calculator:
            presenter_system.integrate_kelly_calculator(kelly_calculator)
        if risk_analyzer:
            presenter_system.integrate_risk_analyzer(risk_analyzer)
        if audit_logger:
            presenter_system.integrate_audit_logger(audit_logger)
        
        logger.info("HITL opportunity presenter system created")
        return presenter_system
        
    except Exception as e:
        logger.error(f"Error creating HITL presenter: {e}")
        raise


# Example usage and testing

async def demo_hitl_presenter():
    """Demonstration of HITL opportunity presenter system."""
    try:
        logger.info("Starting HITL presenter demonstration")
        
        # Create presenter system with console and web formats
        presenter_system = await create_hitl_presenter(
            display_formats=[DisplayFormat.CONSOLE, DisplayFormat.WEB],
            max_opportunities=10,
            update_interval=5.0
        )
        
        # Start the system
        await presenter_system.start()
        
        # Add some demo opportunities (placeholder data)
        demo_opportunities = [
            ArbitrageOpportunity(
                sport=Sport.FOOTBALL,
                event_name="Manchester United vs Liverpool",
                event_date=datetime.utcnow(),
                market_type="match_winner",
                legs=[
                    ArbitrageLeg(
                        bookmaker="Bet365",
                        event_outcome="Manchester United Win",
                        odds=Decimal('2.10'),
                        implied_probability=Decimal('0.476'),
                        stake_percentage=Decimal('0.475'),
                        actual_stake=Decimal('95.00'),
                        potential_payout=Decimal('199.50')
                    ),
                    ArbitrageLeg(
                        bookmaker="Pinnacle",
                        event_outcome="Liverpool Win",
                        odds=Decimal('2.05'),
                        implied_probability=Decimal('0.488'),
                        stake_percentage=Decimal('0.525'),
                        actual_stake=Decimal('105.00'),
                        potential_payout=Decimal('215.25')
                    )
                ],
                total_stake=Decimal('200.00'),
                profit_margin=Decimal('0.047'),
                profit_amount=Decimal('15.75'),
                risk_tier=RiskTier.TIER_A,
                source_scanner="demo_scanner"
            )
        ]
        
        # Add opportunities
        await presenter_system.add_opportunities(demo_opportunities)
        
        # Keep running for demonstration
        logger.info("HITL presenter running... Press Ctrl+C to stop")
        await asyncio.sleep(60)
        
        # Stop the system
        await presenter_system.stop()
        logger.info("Demo completed")
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo error: {e}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demo_hitl_presenter())