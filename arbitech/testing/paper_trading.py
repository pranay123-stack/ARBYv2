"""
Sophisticated Paper Trading System

A comprehensive paper trading environment for arbitrage betting that simulates:
- Virtual trading environment with realistic market data simulation
- Virtual bankroll management with realistic constraints
- Simulated execution with realistic slippage and delays
- Backtesting with historical opportunity data
- Virtual bookmaker accounts with simulated responses
- Performance tracking and analytics
- Mode switching between paper and live trading

Integrates with phases 3-9 for complete simulation:
- Phase 3: Arbitrage Detection Engine
- Phase 4: Risk Management System
- Phase 5: Human-in-the-Loop Approval
- Phase 6: Browser Automation
- Phase 7: Autonomous Decision Making
- Phase 8: Trading Automation
- Phase 9: Notification System

Author: ARBitech Framework
Date: 2025-11-02
Version: 1.0.0
"""

import asyncio
import json
import logging
import math
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP, getcontext
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable, Set
from uuid import UUID, uuid4
import numpy as np
import pandas as pd
from pydantic import ValidationError

# Import existing ARBitech components
try:
    from arbitech.storage.models import (
        ArbitrageOpportunity, ArbitrageLeg, Sport, TradeStatus, ExecutionMode,
        RiskTier, Trade, TradeTimestamps, StakeData, BankrollConfig,
        User, NotificationType, NotificationPriority
    )
    from arbitech.detection.opportunity_scanner import OpportunityScanner, ScanMetrics
    from arbitech.risk.bankroll_manager import BankrollManager, BankrollStrategy, DrawdownPhase
    from arbitech.automation.arbitrage_executor import ArbitrageExecutor
    from arbitech.autonomous.decision_engine import DecisionEngine
    from arbitech.notifications.telegram_bot import TelegramBot
except ImportError as e:
    # Fallback imports for standalone usage
    print(f"Warning: Could not import ARBitech components: {e}")
    print("Running in standalone mode with mock implementations.")
    
    # Create minimal mock implementations
    from enum import Enum
    from datetime import datetime
    from decimal import Decimal
    from typing import Dict, List, Optional, Any
    from uuid import UUID, uuid4
    
    class Sport(str, Enum):
        FOOTBALL = "football"
        BASKETBALL = "basketball"
        TENNIS = "tennis"
        BASEBALL = "baseball"
    
    class RiskTier(str, Enum):
        TIER_A = "tier_a"
        TIER_B = "tier_b"
        TIER_C = "tier_c"
        TIER_D = "tier_d"
    
    class TradeStatus(str, Enum):
        PENDING = "pending"
        FILLED = "filled"
        FAILED = "failed"
    
    class ExecutionMode(str, Enum):
        MANUAL = "manual"
        AUTO_FULL = "auto_full"
        AUTO_STEALTH = "auto_stealth"
        DELAYED = "delayed"
        SIMULATED = "simulated"
    
    class NotificationType(str, Enum):
        SYSTEM_ERROR = "system_error"
        PROFIT_REALIZED = "profit_realized"
        ACCOUNT_UPDATE = "account_update"
    
    class NotificationPriority(str, Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    class ArbitrageLeg:
        def __init__(self, id=None, sport=None, event_id=None, bookmaker=None, 
                     odds=None, suggested_stake=None, risk_tier=None):
            self.id = id or uuid4()
            self.sport = sport
            self.event_id = event_id
            self.bookmaker = bookmaker
            self.odds = odds
            self.suggested_stake = suggested_stake
            self.risk_tier = risk_tier
    
    class ArbitrageOpportunity:
        def __init__(self, id=None, sport=None, event_id=None, profit_margin=None,
                     legs=None, risk_tier=None, detection_timestamp=None, quality_score=None):
            self.id = id or uuid4()
            self.sport = sport
            self.event_id = event_id
            self.profit_margin = profit_margin or Decimal('0.02')
            self.legs = legs or []
            self.risk_tier = risk_tier or RiskTier.TIER_A
            self.detection_timestamp = detection_timestamp or datetime.now()
            self.quality_score = quality_score or Decimal('0.8')
    
    # Mock classes for missing components
    class OpportunityScanner:
        pass
    
    class BankrollManager:
        pass
    
    class ArbitrageExecutor:
        pass
    
    class DecisionEngine:
        pass
    
    class TelegramBot:
        async def send_notification(self, *args, **kwargs):
            pass
    
    # Import what we can
    ArbitrageOpportunity, ArbitrageLeg, Sport, TradeStatus, ExecutionMode, RiskTier
    NotificationType, NotificationPriority

# Configure decimal precision for financial calculations
getcontext().prec = 50


# ============================================================================
# ENUMS AND DATA MODELS
# ============================================================================

class TradingMode(str, Enum):
    """Trading execution modes."""
    PAPER = "paper"
    LIVE = "live"
    BACKTEST = "backtest"
    HYBRID = "hybrid"


class PaperTradeStatus(str, Enum):
    """Paper trading status codes."""
    PENDING = "pending"
    PLACING_BETS = "placing_bets"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    HEDGING = "hedging"
    SETTLED = "settled"
    BACKTESTED = "backtested"


class MarketCondition(str, Enum):
    """Market condition simulation."""
    STABLE = "stable"
    VOLATILE = "volatile"
    TRENDING = "trending"
    HIGH_LIQUIDITY = "high_liquidity"
    LOW_LIQUIDITY = "low_liquidity"
    CHANGING_RAPIDLY = "changing_rapidly"


class ExecutionDelayType(str, Enum):
    """Types of execution delays."""
    NETWORK_LATENCY = "network_latency"
    BOOKMAKER_PROCESSING = "bookmaker_processing"
    LIQUIDITY_DELAY = "liquidity_delay"
    MANUAL_APPROVAL = "manual_approval"
    TECHNICAL_ERROR = "technical_error"


@dataclass
class VirtualMarketData:
    """Simulated market data for paper trading."""
    sport: Sport
    event_id: str
    bookmaker: str
    odds: Decimal
    timestamp: datetime
    confidence: float = 0.95
    market_liquidity: Decimal = Decimal('1000.00')
    volatility: float = 0.02
    change_probability: float = 0.15
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sport": self.sport,
            "event_id": self.event_id,
            "bookmaker": self.bookmaker,
            "odds": float(self.odds),
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "market_liquidity": float(self.market_liquidity),
            "volatility": self.volatility,
            "change_probability": self.change_probability
        }


@dataclass
class SimulatedExecution:
    """Simulated trade execution details."""
    bet_id: str
    bookmaker: str
    sport: Sport
    event_id: str
    odds: Decimal
    stake: Decimal
    expected_return: Decimal
    slippage: Decimal = Decimal('0.00')
    delay_ms: int = 0
    execution_cost: Decimal = Decimal('0.00')
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bet_id": self.bet_id,
            "bookmaker": self.bookmaker,
            "sport": self.sport,
            "event_id": self.event_id,
            "odds": float(self.odds),
            "stake": float(self.stake),
            "expected_return": float(self.expected_return),
            "slippage": float(self.slippage),
            "delay_ms": self.delay_ms,
            "execution_cost": float(self.execution_cost),
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class VirtualBankrollAccount:
    """Virtual bookmaker account for paper trading."""
    bookmaker: str
    balance: Decimal = Decimal('10000.00')
    reserved_balance: Decimal = Decimal('0.00')
    daily_limit: Decimal = Decimal('5000.00')
    weekly_limit: Decimal = Decimal('25000.00')
    monthly_limit: Decimal = Decimal('100000.00')
    daily_volume: Decimal = Decimal('0.00')
    weekly_volume: Decimal = Decimal('0.00')
    monthly_volume: Decimal = Decimal('0.00')
    last_reset_date: datetime = field(default_factory=datetime.now)
    status: str = "active"
    risk_tier: RiskTier = RiskTier.TIER_A
    transaction_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def get_available_balance(self) -> Decimal:
        """Get available balance for new bets."""
        return self.balance - self.reserved_balance
    
    def can_place_bet(self, amount: Decimal) -> Tuple[bool, str]:
        """Check if a bet can be placed."""
        if self.status != "active":
            return False, f"Account status: {self.status}"
        
        if amount > self.get_available_balance():
            return False, "Insufficient balance"
        
        if amount > self.daily_limit:
            return False, "Daily limit exceeded"
        
        if amount > self.weekly_limit:
            return False, "Weekly limit exceeded"
        
        if amount > self.monthly_limit:
            return False, "Monthly limit exceeded"
        
        return True, "OK"
    
    def reserve_balance(self, amount: Decimal) -> bool:
        """Reserve balance for pending bet."""
        if amount <= self.get_available_balance():
            self.reserved_balance += amount
            return True
        return False
    
    def release_reservation(self, amount: Decimal) -> None:
        """Release reserved balance."""
        self.reserved_balance = max(self.reserved_balance - amount, Decimal('0.00'))
    
    def execute_bet(self, amount: Decimal, odds: Decimal, expected_return: Decimal) -> Dict[str, Any]:
        """Execute a virtual bet."""
        success = self.reserve_balance(amount)
        if success:
            # Simulate transaction record
            transaction = {
                "id": str(uuid4()),
                "type": "bet",
                "amount": float(amount),
                "odds": float(odds),
                "expected_return": float(expected_return),
                "timestamp": datetime.now().isoformat(),
                "status": "placed"
            }
            self.transaction_history.append(transaction)
            self.daily_volume += amount
            self.weekly_volume += amount
            self.monthly_volume += amount
            
        return {"success": success, "transaction": transaction if success else None}


@dataclass
class PaperTrade:
    """Complete paper trade record."""
    id: UUID
    opportunity: ArbitrageOpportunity
    user_id: UUID
    mode: TradingMode
    status: PaperTradeStatus
    created_at: datetime
    placed_bets: List[SimulatedExecution] = field(default_factory=list)
    failed_bets: List[SimulatedExecution] = field(default_factory=list)
    hedge_trades: List[SimulatedExecution] = field(default_factory=list)
    expected_profit: Decimal = Decimal('0.00')
    actual_profit: Optional[Decimal] = None
    execution_time_ms: int = 0
    slippage: Decimal = Decimal('0.00')
    total_slippage: Decimal = Decimal('0.00')
    error_messages: List[str] = field(default_factory=list)
    retry_count: int = 0
    settlement_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "opportunity": {
                "sport": self.opportunity.sport,
                "event_id": self.opportunity.event_id,
                "profit_margin": float(self.opportunity.profit_margin),
                "legs": [leg.to_dict() for leg in self.opportunity.legs]
            },
            "user_id": str(self.user_id),
            "mode": self.mode,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "placed_bets": [bet.to_dict() for bet in self.placed_bets],
            "failed_bets": [bet.to_dict() for bet in self.failed_bets],
            "hedge_trades": [trade.to_dict() for trade in self.hedge_trades],
            "expected_profit": float(self.expected_profit),
            "actual_profit": float(self.actual_profit) if self.actual_profit else None,
            "execution_time_ms": self.execution_time_ms,
            "slippage": float(self.slippage),
            "total_slippage": float(self.total_slippage),
            "error_messages": self.error_messages,
            "retry_count": self.retry_count,
            "settlement_data": self.settlement_data
        }


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics for paper trading."""
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    pending_trades: int = 0
    total_profit: Decimal = Decimal('0.00')
    total_losses: Decimal = Decimal('0.00')
    net_profit: Decimal = Decimal('0.00')
    roi_percentage: Decimal = Decimal('0.00')
    win_rate: Decimal = Decimal('0.00')
    average_profit_per_trade: Decimal = Decimal('0.00')
    best_trade: Decimal = Decimal('0.00')
    worst_trade: Decimal = Decimal('0.00')
    average_execution_time_ms: int = 0
    total_slippage: Decimal = Decimal('0.00')
    average_slippage: Decimal = Decimal('0.00')
    profit_by_sport: Dict[Sport, Decimal] = field(default_factory=dict)
    profit_by_bookmaker: Dict[str, Decimal] = field(default_factory=dict)
    trades_by_hour: Dict[int, int] = field(default_factory=lambda: {i: 0 for i in range(24)})
    profit_by_risk_tier: Dict[RiskTier, Decimal] = field(default_factory=dict)
    
    def calculate_metrics(self) -> None:
        """Calculate performance metrics."""
        if self.total_trades > 0:
            self.win_rate = (Decimal(self.successful_trades) / Decimal(self.total_trades)) * 100
            self.average_profit_per_trade = self.net_profit / Decimal(self.total_trades)
            self.average_slippage = self.total_slippage / Decimal(self.total_trades)
            
            if self.total_trades > 0:
                total_stakes = sum(bet.stake for trade in self.get_all_trades() for bet in trade.placed_bets)
                if total_stakes > 0:
                    self.roi_percentage = (self.net_profit / Decimal(total_stakes)) * 100
    
    def get_all_trades(self) -> List[PaperTrade]:
        """Get all trades (this should be populated by the PaperTradingSystem)."""
        # This will be implemented in the main class
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "failed_trades": self.failed_trades,
            "pending_trades": self.pending_trades,
            "total_profit": float(self.total_profit),
            "total_losses": float(self.total_losses),
            "net_profit": float(self.net_profit),
            "roi_percentage": float(self.roi_percentage),
            "win_rate": float(self.win_rate),
            "average_profit_per_trade": float(self.average_profit_per_trade),
            "best_trade": float(self.best_trade),
            "worst_trade": float(self.worst_trade),
            "average_execution_time_ms": self.average_execution_time_ms,
            "total_slippage": float(self.total_slippage),
            "average_slippage": float(self.average_slippage),
            "profit_by_sport": {k: float(v) for k, v in self.profit_by_sport.items()},
            "profit_by_bookmaker": {k: float(v) for k, v in self.profit_by_bookmaker.items()},
            "trades_by_hour": self.trades_by_hour,
            "profit_by_risk_tier": {k: float(v) for k, v in self.profit_by_risk_tier.items()}
        }


# ============================================================================
# MARKET SIMULATION COMPONENTS
# ============================================================================

class MarketSimulator:
    """Simulates realistic market conditions and odds movements."""
    
    def __init__(self, volatility_level: float = 0.02):
        self.volatility_level = volatility_level
        self.active_markets: Dict[str, VirtualMarketData] = {}
        self.condition = MarketCondition.STABLE
        self.price_drift = Decimal('0.0001')  # Small random drift
        self.momentum = Decimal('0.0')  # Momentum effect
        
    def update_market_condition(self, condition: MarketCondition) -> None:
        """Update simulated market condition."""
        self.condition = condition
        if condition == MarketCondition.VOLATILE:
            self.volatility_level = 0.05
            self.price_drift = Decimal('0.001')
        elif condition == MarketCondition.STABLE:
            self.volatility_level = 0.02
            self.price_drift = Decimal('0.0001')
        elif condition == MarketCondition.LOW_LIQUIDITY:
            self.volatility_level = 0.03
            self.price_drift = Decimal('0.0005')
    
    def simulate_odds_movement(self, current_odds: Decimal, bookmaker: str, 
                             sport: Sport) -> Decimal:
        """Simulate realistic odds movement."""
        # Base random movement
        random_factor = Decimal(str(random.gauss(0, self.volatility_level)))
        
        # Momentum effect (trend continuation)
        momentum_factor = self.momentum * Decimal('0.1')
        
        # Bookmaker-specific behavior
        bookmaker_factor = self._get_bookmaker_behavior_factor(bookmaker)
        
        # Apply movement
        total_change = random_factor + momentum_factor + bookmaker_factor
        new_odds = current_odds * (Decimal('1.0') + total_change)
        
        # Ensure odds stay within reasonable bounds
        new_odds = max(Decimal('1.01'), min(new_odds, Decimal('100.0')))
        
        # Round to 2 decimal places for display
        new_odds = new_odds.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return new_odds
    
    def _get_bookmaker_behavior_factor(self, bookmaker: str) -> Decimal:
        """Get bookmaker-specific behavior factor."""
        # Simulate different bookmaker behaviors
        bookmaker_behaviors = {
            "Pinnacle": Decimal('0.0'),  # Most stable
            "Betfair": Decimal('-0.001'),  # Slightly conservative
            "William Hill": Decimal('0.001'),  # Slightly aggressive
            "Bet365": Decimal('0.002'),  # More volatile
            "Unibet": Decimal('0.001'),  # Moderate
        }
        return bookmaker_behaviors.get(bookmaker, Decimal('0.001'))
    
    def add_market_data(self, market_data: VirtualMarketData) -> None:
        """Add market data to simulation."""
        key = f"{market_data.event_id}_{market_data.bookmaker}"
        self.active_markets[key] = market_data
    
    def get_current_odds(self, event_id: str, bookmaker: str) -> Optional[Decimal]:
        """Get current simulated odds for an event/bookmaker."""
        key = f"{event_id}_{bookmaker}"
        if key in self.active_markets:
            return self.active_markets[key].odds
        return None
    
    def simulate_odds_changes(self) -> List[Dict[str, Any]]:
        """Simulate periodic odds changes and return changed events."""
        changed_events = []
        
        for key, market_data in list(self.active_markets.items()):
            # Check if odds should change based on probability
            if random.random() < market_data.change_probability:
                old_odds = market_data.odds
                new_odds = self.simulate_odds_movement(market_data.odds, 
                                                     market_data.bookmaker, 
                                                     market_data.sport)
                
                if abs(new_odds - old_odds) > Decimal('0.01'):  # Significant change
                    market_data.odds = new_odds
                    market_data.timestamp = datetime.now()
                    
                    changed_events.append({
                        "event_id": market_data.event_id,
                        "bookmaker": market_data.bookmaker,
                        "old_odds": float(old_odds),
                        "new_odds": float(new_odds),
                        "change_percent": float((new_odds - old_odds) / old_odds * 100)
                    })
        
        return changed_events


# ============================================================================
# EXECUTION SIMULATOR
# ============================================================================

class ExecutionSimulator:
    """Simulates trade execution with realistic delays and slippage."""
    
    def __init__(self):
        self.base_latency_ms = 50
        self.slippage_base = Decimal('0.005')  # 0.5% base slippage
        self.execution_failures = Decimal('0.02')  # 2% base failure rate
        
    def simulate_execution_delay(self, execution_mode: ExecutionMode, 
                               market_condition: MarketCondition) -> int:
        """Simulate execution delay based on mode and market conditions."""
        base_delay = self.base_latency_ms
        
        # Mode-specific adjustments
        mode_multipliers = {
            ExecutionMode.MANUAL: 5.0,  # Much slower
            ExecutionMode.AUTO_FULL: 1.0,
            ExecutionMode.AUTO_STEALTH: 1.5,
            ExecutionMode.DELAYED: 2.0,
            ExecutionMode.SIMULATED: 0.1  # Instant for paper trading
        }
        
        # Market condition adjustments
        condition_multipliers = {
            MarketCondition.STABLE: 1.0,
            MarketCondition.VOLATILE: 2.0,
            MarketCondition.HIGH_LIQUIDITY: 0.8,
            MarketCondition.LOW_LIQUIDITY: 3.0,
            MarketCondition.CHANGING_RAPIDLY: 4.0
        }
        
        mode_mult = mode_multipliers.get(execution_mode, 1.0)
        condition_mult = condition_multipliers.get(market_condition, 1.0)
        
        total_delay = int(base_delay * mode_mult * condition_mult)
        
        # Add random variance (±20%)
        variance = random.uniform(0.8, 1.2)
        total_delay = int(total_delay * variance)
        
        return max(total_delay, 1)  # Minimum 1ms
    
    def simulate_slippage(self, odds: Decimal, stake: Decimal, 
                         market_condition: MarketCondition) -> Decimal:
        """Simulate price slippage during execution."""
        base_slippage = self.slippage_base
        
        # Odds-dependent slippage (lower odds = higher slippage risk)
        odds_factor = max(Decimal('0.5'), Decimal('2.0') / odds)
        
        # Stake-dependent slippage (larger stakes = higher slippage)
        stake_factor = min(Decimal('2.0'), stake / Decimal('1000'))
        
        # Market condition adjustment
        condition_factors = {
            MarketCondition.STABLE: Decimal('1.0'),
            MarketCondition.VOLATILE: Decimal('2.5'),
            MarketCondition.HIGH_LIQUIDITY: Decimal('0.7'),
            MarketCondition.LOW_LIQUIDITY: Decimal('3.0'),
            MarketCondition.CHANGING_RAPIDLY: Decimal('4.0')
        }
        condition_factor = condition_factors.get(market_condition, Decimal('1.0'))
        
        total_slippage = base_slippage * odds_factor * stake_factor * condition_factor
        
        # Add random variation
        random_factor = Decimal(str(random.gauss(1.0, 0.3)))
        total_slippage *= max(random_factor, Decimal('0.1'))
        
        # Ensure slippage doesn't exceed reasonable bounds
        total_slippage = min(total_slippage, Decimal('0.15'))  # Max 15%
        
        return total_slippage
    
    def should_fail_execution(self, market_condition: MarketCondition, 
                            risk_tier: RiskTier) -> bool:
        """Determine if execution should fail."""
        base_failure_rate = self.execution_failures
        
        # Market condition adjustments
        condition_factors = {
            MarketCondition.STABLE: Decimal('0.5'),
            MarketCondition.VOLATILE: Decimal('3.0'),
            MarketCondition.HIGH_LIQUIDITY: Decimal('0.8'),
            MarketCondition.LOW_LIQUIDITY: Decimal('4.0'),
            MarketCondition.CHANGING_RAPIDLY: Decimal('5.0')
        }
        condition_factor = condition_factors.get(market_condition, Decimal('1.0'))
        
        # Risk tier adjustments (higher risk = higher failure rate)
        tier_factors = {
            RiskTier.TIER_A: Decimal('0.5'),
            RiskTier.TIER_B: Decimal('1.0'),
            RiskTier.TIER_C: Decimal('2.0'),
            RiskTier.TIER_D: Decimal('3.0')
        }
        tier_factor = tier_factors.get(risk_tier, Decimal('1.0'))
        
        adjusted_failure_rate = base_failure_rate * condition_factor * tier_factor
        
        # Random failure based on adjusted rate
        return random.random() < float(adjusted_failure_rate)


# ============================================================================
# PAPER TRADING SYSTEM MAIN CLASS
# ============================================================================

class PaperTradingSystem:
    """
    Comprehensive paper trading system that simulates all aspects of arbitrage trading.
    
    Integrates with:
    - Phase 3: Arbitrage Detection (real opportunities)
    - Phase 4: Risk Management (virtual constraints)
    - Phase 5: HITL Approval (simulated approvals)
    - Phase 6: Browser Automation (virtual execution)
    - Phase 7: Decision Engine (paper-only decisions)
    - Phase 8: Automation (simulated automation)
    - Phase 9: Notifications (virtual alerts)
    """
    
    def __init__(self, initial_bankroll: Decimal = Decimal('100000.00'),
                 mode: TradingMode = TradingMode.PAPER,
                 config_path: Optional[str] = None):
        self.initial_bankroll = initial_bankroll
        self.mode = mode
        self.config_path = config_path
        self.logger = self._setup_logging()
        
        # Core simulation components
        self.market_simulator = MarketSimulator()
        self.execution_simulator = ExecutionSimulator()
        
        # Virtual accounts and state
        self.virtual_accounts: Dict[str, VirtualBankrollAccount] = {}
        self.paper_trades: Dict[UUID, PaperTrade] = {}
        self.performance_metrics = PerformanceMetrics()
        
        # Integration with existing phases
        self.opportunity_scanner: Optional[OpportunityScanner] = None
        self.bankroll_manager: Optional[BankrollManager] = None
        self.decision_engine: Optional[DecisionEngine] = None
        self.telegram_bot: Optional[TelegramBot] = None
        
        # Simulation state
        self.is_running = False
        self.simulation_start_time = datetime.now()
        self.current_market_condition = MarketCondition.STABLE
        self.backtest_data: Optional[pd.DataFrame] = None
        
        # Configuration
        self.config = self._load_config()
        self._initialize_virtual_accounts()
        
        # Performance tracking
        self.trade_history: List[PaperTrade] = []
        self.execution_times: List[int] = []
        self.slippage_history: List[Decimal] = []
        
        self.logger.info(f"PaperTradingSystem initialized in {mode} mode with ${initial_bankroll} bankroll")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for paper trading system."""
        logger = logging.getLogger(f"paper_trading.{self.mode}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_config(self) -> Dict[str, Any]:
        """Load paper trading configuration."""
        default_config = {
            "virtual_bookmakers": [
                "Pinnacle", "Betfair", "William Hill", "Bet365", "Unibet",
                "888Sport", "Betway", "Casumo", "LeoVegas", "MrGreen"
            ],
            "initial_account_balances": {
                "default": Decimal('10000.00'),
                "premium": Decimal('25000.00'),
                "vip": Decimal('50000.00')
            },
            "execution_settings": {
                "enable_slippage": True,
                "enable_delays": True,
                "enable_failures": True,
                "max_concurrent_trades": 10,
                "trade_timeout_seconds": 30
            },
            "backtest_settings": {
                "default_period_days": 30,
                "include_slippage": True,
                "include_delays": True
            },
            "performance_tracking": {
                "save_trade_history": True,
                "export_metrics": True,
                "generate_reports": True
            }
        }
        
        if self.config_path and Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                default_config.update(loaded_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config from {self.config_path}: {e}")
        
        return default_config
    
    def _initialize_virtual_accounts(self) -> None:
        """Initialize virtual bookmaker accounts."""
        bookmakers = self.config["virtual_bookmakers"]
        
        for bookmaker in bookmakers:
            account = VirtualBankrollAccount(
                bookmaker=bookmaker,
                balance=Decimal(str(self.config["initial_account_balances"]["default"])),
                daily_limit=Decimal('5000.00'),
                weekly_limit=Decimal('25000.00'),
                monthly_limit=Decimal('100000.00'),
                risk_tier=RiskTier.TIER_A
            )
            self.virtual_accounts[bookmaker] = account
        
        self.logger.info(f"Initialized {len(bookmakers)} virtual accounts")
    
    # ============================================================================
    # INTEGRATION WITH EXISTING PHASES
    # ============================================================================
    
    def integrate_opportunity_scanner(self, scanner: OpportunityScanner) -> None:
        """Integrate with Phase 3: Arbitrage Detection Engine."""
        self.opportunity_scanner = scanner
        self.logger.info("Integrated with Opportunity Scanner (Phase 3)")
    
    def integrate_bankroll_manager(self, manager: BankrollManager) -> None:
        """Integrate with Phase 4: Risk Management System."""
        self.bankroll_manager = manager
        self.logger.info("Integrated with Bankroll Manager (Phase 4)")
    
    def integrate_decision_engine(self, engine: DecisionEngine) -> None:
        """Integrate with Phase 7: Autonomous Decision Making."""
        self.decision_engine = engine
        self.logger.info("Integrated with Decision Engine (Phase 7)")
    
    def integrate_telegram_bot(self, bot: TelegramBot) -> None:
        """Integrate with Phase 9: Notification System."""
        self.telegram_bot = bot
        self.logger.info("Integrated with Telegram Bot (Phase 9)")
    
    # ============================================================================
    # CORE PAPER TRADING FUNCTIONALITY
    # ============================================================================
    
    async def start_paper_trading(self) -> None:
        """Start the paper trading simulation."""
        if self.is_running:
            self.logger.warning("Paper trading is already running")
            return
        
        self.is_running = True
        self.simulation_start_time = datetime.now()
        self.logger.info("Starting paper trading simulation...")
        
        # Send notification if integrated
        if self.telegram_bot:
            await self.telegram_bot.send_notification(
                message=f"🚀 Paper Trading Started\nMode: {self.mode}\nInitial Bankroll: ${self.initial_bankroll}",
                notification_type=NotificationType.SYSTEM_ERROR,
                priority=NotificationPriority.MEDIUM
            )
        
        # Start background tasks
        if self.mode == TradingMode.PAPER:
            asyncio.create_task(self._paper_trading_loop())
        elif self.mode == TradingMode.BACKTEST:
            asyncio.create_task(self._backtest_loop())
        elif self.mode == TradingMode.HYBRID:
            asyncio.create_task(self._hybrid_trading_loop())
        
        self.logger.info("Paper trading simulation started successfully")
    
    async def stop_paper_trading(self) -> None:
        """Stop the paper trading simulation."""
        if not self.is_running:
            self.logger.warning("Paper trading is not running")
            return
        
        self.is_running = False
        self.logger.info("Stopping paper trading simulation...")
        
        # Send notification
        if self.telegram_bot:
            await self.telegram_bot.send_notification(
                message="⏹️ Paper Trading Stopped",
                notification_type=NotificationType.SYSTEM_ERROR,
                priority=NotificationPriority.MEDIUM
            )
        
        self.logger.info("Paper trading simulation stopped")
    
    async def _paper_trading_loop(self) -> None:
        """Main paper trading loop for live simulation."""
        while self.is_running:
            try:
                # Simulate market changes
                changed_events = self.market_simulator.simulate_odds_changes()
                
                # Process any opportunities from real scanner
                if self.opportunity_scanner:
                    await self._process_real_opportunities()
                
                # Update performance metrics
                self._update_performance_metrics()
                
                # Wait before next iteration
                await asyncio.sleep(5)  # 5 second intervals
                
            except Exception as e:
                self.logger.error(f"Error in paper trading loop: {e}")
                await asyncio.sleep(10)
    
    async def _process_real_opportunities(self) -> None:
        """Process real opportunities from integrated scanner."""
        # This would integrate with real-time opportunity detection
        # For now, we'll simulate the process
        self.logger.debug("Processing real-time opportunities...")
    
    def switch_mode(self, new_mode: TradingMode) -> None:
        """Switch between trading modes."""
        if new_mode == self.mode:
            self.logger.info(f"Already in {new_mode} mode")
            return
        
        old_mode = self.mode
        self.mode = new_mode
        
        self.logger.info(f"Switched from {old_mode} to {new_mode} mode")
        
        # Notify about mode switch
        if self.telegram_bot:
            asyncio.create_task(self.telegram_bot.send_notification(
                message=f"🔄 Mode Switch: {old_mode} → {new_mode}",
                notification_type=NotificationType.ACCOUNT_UPDATE,
                priority=NotificationPriority.MEDIUM
            ))
    
    # ============================================================================
    # OPPORTUNITY PROCESSING
    # ============================================================================
    
    async def process_opportunity(self, opportunity: ArbitrageOpportunity, 
                                user_id: UUID,
                                execution_mode: ExecutionMode = ExecutionMode.SIMULATED) -> PaperTrade:
        """
        Process an arbitrage opportunity in paper trading mode.
        
        This method simulates the complete execution pipeline including:
        1. Risk validation (Phase 4)
        2. Decision making (Phase 7)
        3. HITL approval (Phase 5) - simulated
        4. Trade execution (Phase 6/8) - simulated
        5. Notification (Phase 9) - simulated
        """
        trade_id = uuid4()
        start_time = datetime.now()
        
        paper_trade = PaperTrade(
            id=trade_id,
            opportunity=opportunity,
            user_id=user_id,
            mode=self.mode,
            status=PaperTradeStatus.PENDING,
            created_at=start_time
        )
        
        self.logger.info(f"Processing opportunity {opportunity.id} - Trade ID: {trade_id}")
        
        try:
            # Phase 4: Risk validation
            if not await self._validate_risk(opportunity, execution_mode):
                paper_trade.status = PaperTradeStatus.FAILED
                paper_trade.error_messages.append("Risk validation failed")
                return paper_trade
            
            # Phase 7: Decision making (if integrated)
            if self.decision_engine:
                decision = await self.decision_engine.should_trade(opportunity)
                if not decision.should_trade:
                    paper_trade.status = PaperTradeStatus.CANCELLED
                    paper_trade.error_messages.append(decision.reason)
                    return paper_trade
            
            paper_trade.status = PaperTradeStatus.PLACING_BETS
            
            # Phase 5: HITL approval simulation
            if execution_mode == ExecutionMode.MANUAL:
                approved = await self._simulate_hitl_approval(opportunity)
                if not approved:
                    paper_trade.status = PaperTradeStatus.CANCELLED
                    paper_trade.error_messages.append("HITL approval denied")
                    return paper_trade
            
            # Execute the arbitrage trade
            execution_start = datetime.now()
            await self._execute_arbitrage_trade(paper_trade)
            execution_end = datetime.now()
            
            paper_trade.execution_time_ms = int((execution_end - execution_start).total_seconds() * 1000)
            self.execution_times.append(paper_trade.execution_time_ms)
            
            # Calculate final results
            await self._settle_trade(paper_trade)
            
            # Update performance metrics
            self._record_trade_result(paper_trade)
            
            # Send success notification
            if self.telegram_bot and paper_trade.status == PaperTradeStatus.FILLED:
                await self.telegram_bot.send_notification(
                    message=f"✅ Paper Trade Filled\nProfit: ${paper_trade.actual_profit:.2f}\n"
                           f"Slippage: {paper_trade.total_slippage:.3%}",
                    notification_type=NotificationType.PROFIT_REALIZED,
                    priority=NotificationPriority.HIGH
                )
            
        except Exception as e:
            paper_trade.status = PaperTradeStatus.FAILED
            paper_trade.error_messages.append(str(e))
            self.logger.error(f"Error processing opportunity {opportunity.id}: {e}")
        
        finally:
            self.paper_trades[trade_id] = paper_trade
            self.trade_history.append(paper_trade)
        
        return paper_trade
    
    async def _validate_risk(self, opportunity: ArbitrageOpportunity, 
                           execution_mode: ExecutionMode) -> bool:
        """Phase 4: Validate risk constraints."""
        # Check if we have enough virtual balance
        total_stake_needed = Decimal('0.00')
        for leg in opportunity.legs:
            total_stake_needed += leg.suggested_stake
        
        if total_stake_needed > self.initial_bankroll:
            self.logger.warning(f"Insufficient bankroll: need {total_stake_needed}, have {self.initial_bankroll}")
            return False
        
        # Use integrated bankroll manager if available
        if self.bankroll_manager:
            return await self.bankroll_manager.can_place_bet(opportunity)
        
        return True
    
    async def _simulate_hitl_approval(self, opportunity: ArbitrageOpportunity) -> bool:
        """Phase 5: Simulate HITL approval process."""
        # In a real implementation, this would trigger approval workflow
        # For paper trading, we simulate approval with some probability
        
        approval_probability = 0.85  # 85% approval rate
        
        # Adjust probability based on opportunity characteristics
        if opportunity.profit_margin > Decimal('0.05'):  # High profit
            approval_probability += 0.1
        elif opportunity.profit_margin < Decimal('0.02'):  # Low profit
            approval_probability -= 0.1
        
        if opportunity.risk_tier == RiskTier.TIER_A:
            approval_probability += 0.05
        elif opportunity.risk_tier == RiskTier.TIER_D:
            approval_probability -= 0.1
        
        return random.random() < approval_probability
    
    async def _execute_arbitrage_trade(self, paper_trade: PaperTrade) -> None:
        """Execute arbitrage trade legs with simulated execution."""
        opportunity = paper_trade.opportunity
        
        for leg in opportunity.legs:
            # Simulate each leg execution
            execution = await self._execute_single_leg(leg, paper_trade)
            
            if execution.success:
                paper_trade.placed_bets.append(execution)
            else:
                paper_trade.failed_bets.append(execution)
                paper_trade.error_messages.append(execution.error_message or "Unknown error")
        
        # Check if all legs were successful
        if len(paper_trade.failed_bets) > 0:
            if len(paper_trade.placed_bets) == len(opportunity.legs):
                paper_trade.status = PaperTradeStatus.PARTIAL_FILLED
            else:
                paper_trade.status = PaperTradeStatus.FAILED
        else:
            paper_trade.status = PaperTradeStatus.FILLED
    
    async def _execute_single_leg(self, leg: ArbitrageLeg, 
                                paper_trade: PaperTrade) -> SimulatedExecution:
        """Execute a single arbitrage leg with realistic simulation."""
        bookmaker = leg.bookmaker
        odds = leg.odds
        stake = leg.suggested_stake
        
        # Get virtual account
        account = self.virtual_accounts.get(bookmaker)
        if not account:
            return SimulatedExecution(
                bet_id=str(uuid4()),
                bookmaker=bookmaker,
                sport=leg.sport,
                event_id=leg.event_id,
                odds=odds,
                stake=stake,
                expected_return=stake * odds,
                success=False,
                error_message="Virtual account not found"
            )
        
        # Check account constraints
        can_bet, reason = account.can_place_bet(stake)
        if not can_bet:
            return SimulatedExecution(
                bet_id=str(uuid4()),
                bookmaker=bookmaker,
                sport=leg.sport,
                event_id=leg.event_id,
                odds=odds,
                stake=stake,
                expected_return=stake * odds,
                success=False,
                error_message=f"Account constraint: {reason}"
            )
        
        # Simulate execution delay
        delay_ms = self.execution_simulator.simulate_execution_delay(
            ExecutionMode.SIMULATED, self.current_market_condition
        )
        
        await asyncio.sleep(delay_ms / 1000)  # Convert to seconds
        
        # Simulate execution failure
        if self.execution_simulator.should_fail_execution(
            self.current_market_condition, leg.risk_tier
        ):
            return SimulatedExecution(
                bet_id=str(uuid4()),
                bookmaker=bookmaker,
                sport=leg.sport,
                event_id=leg.event_id,
                odds=odds,
                stake=stake,
                expected_return=stake * odds,
                success=False,
                error_message="Simulated execution failure",
                delay_ms=delay_ms
            )
        
        # Calculate slippage if enabled
        slippage = Decimal('0.00')
        if self.config["execution_settings"]["enable_slippage"]:
            slippage = self.execution_simulator.simulate_slippage(
                odds, stake, self.current_market_condition
            )
            paper_trade.total_slippage += slippage
        
        # Simulate odds movement during execution
        if slippage > Decimal('0.00'):
            executed_odds = odds * (Decimal('1.0') - slippage)
        else:
            executed_odds = odds
        
        # Reserve balance and record transaction
        account.reserve_balance(stake)
        transaction = account.execute_bet(stake, executed_odds, stake * executed_odds)
        
        return SimulatedExecution(
            bet_id=str(uuid4()),
            bookmaker=bookmaker,
            sport=leg.sport,
            event_id=leg.event_id,
            odds=executed_odds,
            stake=stake,
            expected_return=stake * executed_odds,
            slippage=slippage,
            delay_ms=delay_ms,
            success=transaction["success"],
            error_message=transaction.get("transaction", {}).get("error_message") if not transaction["success"] else None
        )
    
    async def _settle_trade(self, paper_trade: PaperTrade) -> None:
        """Settle the paper trade and calculate actual profit/loss."""
        opportunity = paper_trade.opportunity
        
        # For paper trading, we'll simulate settlement
        if paper_trade.status == PaperTradeStatus.FILLED:
            # Calculate actual profit based on executed odds
            total_return = sum(bet.expected_return for bet in paper_trade.placed_bets)
            total_stake = sum(bet.stake for bet in paper_trade.placed_bets)
            paper_trade.actual_profit = total_return - total_stake
            
            # Simulate occasional settlement issues
            if random.random() < 0.02:  # 2% chance of settlement delay/issue
                paper_trade.status = PaperTradeStatus.HEDGING
                paper_trade.actual_profit *= Decimal(str(random.uniform(0.8, 1.2)))
        elif paper_trade.status == PaperTradeStatus.PARTIAL_FILLED:
            # Handle partial fills - calculate partial profit/loss
            successful_stakes = [bet.stake for bet in paper_trade.placed_bets]
            if successful_stakes:
                paper_trade.actual_profit = sum(successful_stakes) * Decimal('-0.1')  # Loss for partial fills
        else:
            paper_trade.actual_profit = Decimal('0.00')
        
        paper_trade.status = PaperTradeStatus.SETTLED
        self.slippage_history.append(paper_trade.total_slippage)
    
    def _record_trade_result(self, paper_trade: PaperTrade) -> None:
        """Record trade result in performance metrics."""
        self.performance_metrics.total_trades += 1
        
        if paper_trade.status == PaperTradeStatus.FILLED:
            self.performance_metrics.successful_trades += 1
            
            if paper_trade.actual_profit and paper_trade.actual_profit > 0:
                self.performance_metrics.total_profit += paper_trade.actual_profit
            elif paper_trade.actual_profit and paper_trade.actual_profit < 0:
                self.performance_metrics.total_losses += abs(paper_trade.actual_profit)
            
            # Track by sport
            sport = paper_trade.opportunity.sport
            if sport not in self.performance_metrics.profit_by_sport:
                self.performance_metrics.profit_by_sport[sport] = Decimal('0.00')
            
            if paper_trade.actual_profit:
                self.performance_metrics.profit_by_sport[sport] += paper_trade.actual_profit
            
            # Track by bookmaker
            for bet in paper_trade.placed_bets:
                if bet.bookmaker not in self.performance_metrics.profit_by_bookmaker:
                    self.performance_metrics.profit_by_bookmaker[bet.bookmaker] = Decimal('0.00')
                
                if paper_trade.actual_profit:
                    self.performance_metrics.profit_by_bookmaker[bet.bookmaker] += paper_trade.actual_profit / len(paper_trade.placed_bets)
        
        elif paper_trade.status in [PaperTradeStatus.FAILED, PaperTradeStatus.CANCELLED]:
            self.performance_metrics.failed_trades += 1
        
        # Update time-based statistics
        hour = paper_trade.created_at.hour
        self.performance_metrics.trades_by_hour[hour] += 1
        
        # Update risk tier statistics
        risk_tier = paper_trade.opportunity.risk_tier
        if risk_tier not in self.performance_metrics.profit_by_risk_tier:
            self.performance_metrics.profit_by_risk_tier[risk_tier] = Decimal('0.00')
        
        if paper_trade.actual_profit:
            self.performance_metrics.profit_by_risk_tier[risk_tier] += paper_trade.actual_profit
        
        # Recalculate metrics
        self.performance_metrics.calculate_metrics()
    
    def _update_performance_metrics(self) -> None:
        """Update real-time performance metrics."""
        # Calculate net profit
        self.performance_metrics.net_profit = (
            self.performance_metrics.total_profit - self.performance_metrics.total_losses
        )
        
        # Update average execution time
        if self.execution_times:
            self.performance_metrics.average_execution_time_ms = sum(self.execution_times) // len(self.execution_times)
        
        # Update total slippage
        if self.slippage_history:
            self.performance_metrics.total_slippage = sum(self.slippage_history)
        
        # Update best/worst trades
        profits = [t.actual_profit for t in self.trade_history if t.actual_profit is not None]
        if profits:
            self.performance_metrics.best_trade = max(profits)
            self.performance_metrics.worst_trade = min(profits)
    
    # ============================================================================
    # BACKTESTING FUNCTIONALITY
    # ============================================================================
    
    def load_backtest_data(self, data_source: Union[str, pd.DataFrame]) -> None:
        """Load historical data for backtesting."""
        if isinstance(data_source, str):
            if data_source.endswith('.csv'):
                self.backtest_data = pd.read_csv(data_source)
            elif data_source.endswith('.json'):
                with open(data_source, 'r') as f:
                    self.backtest_data = pd.DataFrame(json.load(f))
            else:
                raise ValueError("Unsupported file format. Use CSV or JSON.")
        elif isinstance(data_source, pd.DataFrame):
            self.backtest_data = data_source.copy()
        else:
            raise ValueError("Data source must be file path or DataFrame")
        
        # Ensure required columns exist
        required_columns = ['sport', 'event_id', 'bookmaker', 'odds', 'timestamp']
        missing_columns = [col for col in required_columns if col not in self.backtest_data.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        self.logger.info(f"Loaded backtest data with {len(self.backtest_data)} records")
    
    async def run_backtest(self, start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          min_profit_margin: Decimal = Decimal('0.02')) -> Dict[str, Any]:
        """Run backtest on historical data."""
        if self.backtest_data is None:
            raise ValueError("No backtest data loaded. Call load_backtest_data() first.")
        
        self.logger.info("Starting backtest...")
        
        # Filter data by date range
        if start_date or end_date:
            mask = pd.Series([True] * len(self.backtest_data))
            if start_date:
                mask &= pd.to_datetime(self.backtest_data['timestamp']) >= start_date
            if end_date:
                mask &= pd.to_datetime(self.backtest_data['timestamp']) <= end_date
            
            backtest_data = self.backtest_data[mask].copy()
        else:
            backtest_data = self.backtest_data.copy()
        
        backtest_trades = []
        current_bankroll = self.initial_bankroll
        
        # Group by event to find arbitrage opportunities
        events = backtest_data.groupby('event_id')
        
        for event_id, event_data in events:
            # Find arbitrage opportunities in this event
            opportunities = self._find_arbitrage_opportunities_in_data(event_data)
            
            for opportunity in opportunities:
                if opportunity.profit_margin >= min_profit_margin:
                    # Create paper trade for backtesting
                    trade_id = uuid4()
                    backtest_trade = PaperTrade(
                        id=trade_id,
                        opportunity=opportunity,
                        user_id=uuid4(),  # Dummy user ID for backtest
                        mode=TradingMode.BACKTEST,
                        status=PaperTradeStatus.BACKTESTED,
                        created_at=pd.to_datetime(opportunity.detection_timestamp)
                    )
                    
                    # Simulate execution in backtest mode
                    await self._execute_backtest_trade(backtest_trade, backtest_data)
                    
                    backtest_trades.append(backtest_trade)
                    
                    # Update virtual bankroll
                    if backtest_trade.actual_profit:
                        current_bankroll += backtest_trade.actual_profit
        
        # Generate backtest results
        results = self._generate_backtest_report(backtest_trades, current_bankroll)
        
        self.logger.info(f"Backtest completed: {len(backtest_trades)} trades analyzed")
        return results
    
    def _find_arbitrage_opportunities_in_data(self, event_data: pd.DataFrame) -> List[ArbitrageOpportunity]:
        """Find arbitrage opportunities in backtest data."""
        opportunities = []
        
        # Get unique sports and outcomes
        sports = event_data['sport'].unique()
        
        for sport in sports:
            sport_data = event_data[event_data['sport'] == sport]
            
            # Group by event_id
            events = sport_data.groupby('event_id')
            
            for event_id, event_odds in events:
                # Look for arbitrage opportunities across bookmakers
                bookmaker_odds = {}
                
                for _, row in event_odds.iterrows():
                    bookmaker = row['bookmaker']
                    odds = Decimal(str(row['odds']))
                    bookmaker_odds[bookmaker] = odds
                
                # Find best odds for each potential outcome
                # For simplicity, assume binary outcomes (Home/Away)
                home_odds = max(bookmaker_odds.values())
                away_odds = max(bookmaker_odds.values())
                
                # Check for arbitrage opportunity
                implied_prob_home = Decimal('1.0') / home_odds
                implied_prob_away = Decimal('1.0') / away_odds
                total_implied_prob = implied_prob_home + implied_prob_away
                
                if total_implied_prob < Decimal('1.0'):  # Arbitrage exists
                    profit_margin = Decimal('1.0') - total_implied_prob
                    
                    # Calculate optimal stakes
                    stake_total = Decimal('1000.00')  # Fixed stake for backtest
                    stake_home = stake_total * implied_prob_home / (total_implied_prob * home_odds)
                    stake_away = stake_total * implied_prob_away / (total_implied_prob * away_odds)
                    
                    # Create legs
                    legs = [
                        ArbitrageLeg(
                            id=uuid4(),
                            sport=Sport(sport),
                            event_id=event_id,
                            bookmaker=max(bookmaker_odds, key=bookmaker_odds.get),
                            odds=home_odds,
                            suggested_stake=stake_home,
                            risk_tier=RiskTier.TIER_A
                        ),
                        ArbitrageLeg(
                            id=uuid4(),
                            sport=Sport(sport),
                            event_id=event_id,
                            bookmaker=min(bookmaker_odds, key=bookmaker_odds.get),
                            odds=away_odds,
                            suggested_stake=stake_away,
                            risk_tier=RiskTier.TIER_A
                        )
                    ]
                    
                    # Create opportunity
                    opportunity = ArbitrageOpportunity(
                        id=uuid4(),
                        sport=Sport(sport),
                        event_id=event_id,
                        profit_margin=profit_margin,
                        legs=legs,
                        risk_tier=RiskTier.TIER_A,
                        detection_timestamp=event_odds.iloc[0]['timestamp'],
                        quality_score=Decimal('0.8')
                    )
                    
                    opportunities.append(opportunity)
        
        return opportunities
    
    async def _execute_backtest_trade(self, paper_trade: PaperTrade, 
                                     backtest_data: pd.DataFrame) -> None:
        """Execute trade in backtest mode with historical realism."""
        opportunity = paper_trade.opportunity
        
        # Simulate execution with historical slippage patterns
        total_slippage = Decimal('0.00')
        
        for leg in opportunity.legs:
            # Get historical odds at execution time
            execution_time = pd.to_datetime(paper_trade.created_at)
            historical_data = backtest_data[
                (backtest_data['event_id'] == leg.event_id) &
                (backtest_data['bookmaker'] == leg.bookmaker) &
                (pd.to_datetime(backtest_data['timestamp']) <= execution_time)
            ].sort_values('timestamp', ascending=False)
            
            if not historical_data.empty:
                historical_odds = Decimal(str(historical_data.iloc[0]['odds']))
                current_odds = leg.odds
                
                # Calculate slippage based on historical movement
                slippage = abs(current_odds - historical_odds) / historical_odds
                total_slippage += slippage
                
                # Simulate execution
                execution = SimulatedExecution(
                    bet_id=str(uuid4()),
                    bookmaker=leg.bookmaker,
                    sport=leg.sport,
                    event_id=leg.event_id,
                    odds=current_odds * (Decimal('1.0') - slippage),
                    stake=leg.suggested_stake,
                    expected_return=leg.suggested_stake * current_odds * (Decimal('1.0') - slippage),
                    slippage=slippage,
                    success=True,
                    timestamp=execution_time
                )
                
                paper_trade.placed_bets.append(execution)
            else:
                # No historical data, use simulated execution
                execution = await self._execute_single_leg(leg, paper_trade)
                paper_trade.placed_bets.append(execution)
        
        paper_trade.total_slippage = total_slippage
        
        # Calculate profit/loss
        if paper_trade.placed_bets:
            total_return = sum(bet.expected_return for bet in paper_trade.placed_bets)
            total_stake = sum(bet.stake for bet in paper_trade.placed_bets)
            paper_trade.actual_profit = total_return - total_stake
    
    def _generate_backtest_report(self, trades: List[PaperTrade], 
                                final_bankroll: Decimal) -> Dict[str, Any]:
        """Generate comprehensive backtest report."""
        if not trades:
            return {
                "total_trades": 0,
                "total_profit": 0.0,
                "roi": 0.0,
                "win_rate": 0.0,
                "message": "No trades found in backtest period"
            }
        
        profitable_trades = [t for t in trades if t.actual_profit and t.actual_profit > 0]
        losing_trades = [t for t in trades if t.actual_profit and t.actual_profit < 0]
        
        total_profit = sum(t.actual_profit for t in trades if t.actual_profit)
        roi = (final_bankroll - self.initial_bankroll) / self.initial_bankroll * 100
        
        win_rate = len(profitable_trades) / len(trades) * 100
        
        return {
            "total_trades": len(trades),
            "profitable_trades": len(profitable_trades),
            "losing_trades": len(losing_trades),
            "total_profit": float(total_profit),
            "final_bankroll": float(final_bankroll),
            "initial_bankroll": float(self.initial_bankroll),
            "roi": float(roi),
            "win_rate": float(win_rate),
            "average_profit_per_trade": float(total_profit / len(trades)),
            "best_trade": float(max(t.actual_profit for t in trades if t.actual_profit)),
            "worst_trade": float(min(t.actual_profit for t in trades if t.actual_profit)),
            "total_slippage": float(sum(t.total_slippage for t in trades)),
            "average_slippage": float(sum(t.total_slippage for t in trades) / len(trades)),
            "profit_by_sport": {
                str(t.opportunity.sport): float(sum(s.actual_profit for s in trades if s.opportunity.sport == t.opportunity.sport and s.actual_profit))
                for t in trades
            },
            "execution_time_stats": {
                "average_ms": float(sum(t.execution_time_ms for t in trades) / len(trades)) if trades else 0,
                "min_ms": min(t.execution_time_ms for t in trades) if trades else 0,
                "max_ms": max(t.execution_time_ms for t in trades) if trades else 0
            }
        }
    
    # ============================================================================
    # ANALYTICS AND REPORTING
    # ============================================================================
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "trading_mode": self.mode,
            "simulation_duration": str(datetime.now() - self.simulation_start_time),
            "performance_metrics": self.performance_metrics.to_dict(),
            "virtual_accounts": {
                bookmaker: {
                    "balance": float(account.balance),
                    "reserved_balance": float(account.reserved_balance),
                    "available_balance": float(account.get_available_balance()),
                    "daily_volume": float(account.daily_volume),
                    "status": account.status
                }
                for bookmaker, account in self.virtual_accounts.items()
            },
            "trade_summary": {
                "total_trades": len(self.paper_trades),
                "recent_trades": [
                    trade.to_dict() for trade in list(self.paper_trades.values())[-10:]
                ],
                "pending_trades": len([t for t in self.paper_trades.values() 
                                     if t.status in [PaperTradeStatus.PENDING, PaperTradeStatus.PLACING_BETS]]),
                "successful_trades": len([t for t in self.paper_trades.values() 
                                        if t.status == PaperTradeStatus.FILLED]),
                "failed_trades": len([t for t in self.paper_trades.values() 
                                    if t.status == PaperTradeStatus.FAILED])
            }
        }
        
        return report
    
    def export_trade_history(self, filepath: str, format: str = "json") -> None:
        """Export complete trade history to file."""
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "trading_mode": self.mode,
                "initial_bankroll": float(self.initial_bankroll),
                "total_trades": len(self.trade_history)
            },
            "trades": [trade.to_dict() for trade in self.trade_history],
            "performance_metrics": self.performance_metrics.to_dict()
        }
        
        if format.lower() == "json":
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
        elif format.lower() == "csv":
            # Convert to DataFrame for CSV export
            trades_data = []
            for trade in self.trade_history:
                trade_dict = trade.to_dict()
                trade_dict['execution_time'] = trade.created_at.isoformat()
                trades_data.append(trade_dict)
            
            df = pd.DataFrame(trades_data)
            df.to_csv(filepath, index=False)
        else:
            raise ValueError("Format must be 'json' or 'csv'")
        
        self.logger.info(f"Exported {len(self.trade_history)} trades to {filepath}")
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get summary of all virtual accounts."""
        total_balance = sum(account.balance for account in self.virtual_accounts.values())
        total_reserved = sum(account.reserved_balance for account in self.virtual_accounts.values())
        total_available = sum(account.get_available_balance() for account in self.virtual_accounts.values())
        
        return {
            "total_accounts": len(self.virtual_accounts),
            "total_balance": float(total_balance),
            "total_reserved_balance": float(total_reserved),
            "total_available_balance": float(total_available),
            "accounts": {
                bookmaker: {
                    "balance": float(account.balance),
                    "available": float(account.get_available_balance()),
                    "reserved": float(account.reserved_balance),
                    "daily_volume": float(account.daily_volume),
                    "status": account.status,
                    "risk_tier": account.risk_tier,
                    "transaction_count": len(account.transaction_history)
                }
                for bookmaker, account in self.virtual_accounts.items()
            }
        }
    
    def reset_virtual_accounts(self, preserve_history: bool = True) -> None:
        """Reset virtual accounts to initial state."""
        if preserve_history:
            self.logger.info("Resetting account balances (preserving history)")
        else:
            self.logger.info("Resetting all account data")
        
        for bookmaker, account in self.virtual_accounts.items():
            if preserve_history:
                # Keep transaction history but reset balances
                account.balance = Decimal(str(self.config["initial_account_balances"]["default"]))
                account.reserved_balance = Decimal('0.00')
                account.daily_volume = Decimal('0.00')
            else:
                # Complete reset
                account.balance = Decimal(str(self.config["initial_account_balances"]["default"]))
                account.reserved_balance = Decimal('0.00')
                account.daily_volume = Decimal('0.00')
                account.weekly_volume = Decimal('0.00')
                account.monthly_volume = Decimal('0.00')
                account.transaction_history.clear()
        
        # Reset performance metrics
        self.performance_metrics = PerformanceMetrics()
        
        self.logger.info("Virtual accounts reset completed")
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    async def _backtest_loop(self) -> None:
        """Backtest execution loop."""
        self.logger.info("Starting backtest mode...")
        # Backtest is executed synchronously via run_backtest()
    
    async def _hybrid_trading_loop(self) -> None:
        """Hybrid mode combining paper and live trading."""
        self.logger.info("Starting hybrid mode...")
        # Implement hybrid logic as needed
        
    def simulate_market_event(self, event_type: MarketCondition, 
                            duration_minutes: int = 30) -> None:
        """Simulate specific market conditions for testing."""
        self.current_market_condition = event_type
        self.market_simulator.update_market_condition(event_type)
        
        self.logger.info(f"Simulated market event: {event_type} for {duration_minutes} minutes")
        
        # Auto-revert to stable after duration
        def revert_condition():
            time.sleep(duration_minutes * 60)
            self.current_market_condition = MarketCondition.STABLE
            self.market_simulator.update_market_condition(MarketCondition.STABLE)
            self.logger.info("Market condition reverted to STABLE")
        
        import threading
        threading.Thread(target=revert_condition, daemon=True).start()
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        return {
            "is_running": self.is_running,
            "mode": self.mode,
            "start_time": self.simulation_start_time.isoformat(),
            "current_market_condition": self.current_market_condition,
            "total_trades": len(self.paper_trades),
            "active_accounts": len([acc for acc in self.virtual_accounts.values() if acc.status == "active"]),
            "performance_summary": {
                "net_profit": float(self.performance_metrics.net_profit),
                "win_rate": float(self.performance_metrics.win_rate),
                "roi": float(self.performance_metrics.roi_percentage)
            }
        }


# ============================================================================
# FACTORY AND UTILITY FUNCTIONS
# ============================================================================

def create_paper_trading_system(mode: TradingMode = TradingMode.PAPER,
                               initial_bankroll: Decimal = Decimal('100000.00'),
                               config_path: Optional[str] = None) -> PaperTradingSystem:
    """
    Factory function to create a paper trading system with optimal configuration.
    
    Args:
        mode: Trading mode (PAPER, BACKTEST, HYBRID)
        initial_bankroll: Starting virtual bankroll
        config_path: Path to configuration file
    
    Returns:
        Configured PaperTradingSystem instance
    """
    system = PaperTradingSystem(
        initial_bankroll=initial_bankroll,
        mode=mode,
        config_path=config_path
    )
    
    # Set up realistic market simulation based on mode
    if mode == TradingMode.PAPER:
        system.current_market_condition = MarketCondition.STABLE
        system.market_simulator.update_market_condition(MarketCondition.STABLE)
    elif mode == TradingMode.BACKTEST:
        # Backtest with historical volatility patterns
        system.current_market_condition = MarketCondition.VOLATILE
        system.market_simulator.update_market_condition(MarketCondition.VOLATILE)
    
    return system


def load_sample_opportunities(num_opportunities: int = 10) -> List[ArbitrageOpportunity]:
    """Generate sample arbitrage opportunities for testing."""
    opportunities = []
    
    sports = [Sport.FOOTBALL, Sport.BASKETBALL, Sport.TENNIS, Sport.BASEBALL]
    bookmakers = ["Pinnacle", "Bet365", "William Hill", "Unibet", "Betfair"]
    
    for i in range(num_opportunities):
        sport = random.choice(sports)
        event_id = f"event_{uuid4().hex[:8]}"
        profit_margin = Decimal(str(random.uniform(0.015, 0.08)))  # 1.5% to 8%
        
        # Generate legs for the opportunity
        legs = []
        for j in range(2):  # Binary arbitrage
            bookmaker = random.choice(bookmakers)
            odds = Decimal(str(random.uniform(1.5, 4.0)))
            stake = Decimal(str(random.uniform(50, 500)))
            
            leg = ArbitrageLeg(
                id=uuid4(),
                sport=sport,
                event_id=event_id,
                bookmaker=bookmaker,
                odds=odds,
                suggested_stake=stake,
                risk_tier=random.choice([RiskTier.TIER_A, RiskTier.TIER_B])
            )
            legs.append(leg)
        
        # Calculate actual profit margin from legs
        total_implied_prob = sum(Decimal('1.0') / leg.odds for leg in legs)
        actual_profit_margin = Decimal('1.0') - total_implied_prob
        
        opportunity = ArbitrageOpportunity(
            id=uuid4(),
            sport=sport,
            event_id=event_id,
            profit_margin=actual_profit_margin,
            legs=legs,
            risk_tier=random.choice([RiskTier.TIER_A, RiskTier.TIER_B, RiskTier.TIER_C]),
            detection_timestamp=datetime.now(),
            quality_score=Decimal(str(random.uniform(0.6, 0.95)))
        )
        
        opportunities.append(opportunity)
    
    return opportunities


# ============================================================================
# DEMO AND TESTING FUNCTIONS
# ============================================================================

async def demo_paper_trading() -> None:
    """Demonstrate paper trading functionality."""
    print("🚀 Starting Paper Trading Demo...")
    
    # Create paper trading system
    system = create_paper_trading_system(
        mode=TradingMode.PAPER,
        initial_bankroll=Decimal('50000.00')
    )
    
    # Load sample opportunities
    opportunities = load_sample_opportunities(20)
    print(f"📊 Loaded {len(opportunities)} sample opportunities")
    
    # Start paper trading
    await system.start_paper_trading()
    
    # Process some opportunities
    user_id = uuid4()
    
    for i, opportunity in enumerate(opportunities[:5]):
        print(f"\n🎯 Processing opportunity {i+1}: {opportunity.sport} - {opportunity.event_id}")
        print(f"   Profit margin: {opportunity.profit_margin:.2%}")
        
        # Execute opportunity
        trade = await system.process_opportunity(opportunity, user_id)
        
        print(f"   Status: {trade.status}")
        if trade.actual_profit:
            print(f"   Actual profit: ${trade.actual_profit:.2f}")
        if trade.total_slippage > 0:
            print(f"   Total slippage: {trade.total_slippage:.3%}")
        
        # Small delay between trades
        await asyncio.sleep(1)
    
    # Generate report
    print("\n📈 Performance Report:")
    report = system.get_performance_report()
    
    metrics = report["performance_metrics"]
    print(f"Total trades: {metrics['total_trades']}")
    print(f"Win rate: {metrics['win_rate']:.1f}%")
    print(f"Net profit: ${metrics['net_profit']:.2f}")
    print(f"ROI: {metrics['roi_percentage']:.2f}%")
    
    # Account summary
    print("\n💰 Account Summary:")
    account_summary = system.get_account_summary()
    print(f"Total available balance: ${account_summary['total_available_balance']:.2f}")
    
    # Stop paper trading
    await system.stop_paper_trading()
    print("\n✅ Paper trading demo completed!")


async def demo_backtest() -> None:
    """Demonstrate backtesting functionality."""
    print("🔍 Starting Backtest Demo...")
    
    # Create backtesting system
    system = create_paper_trading_system(
        mode=TradingMode.BACKTEST,
        initial_bankroll=Decimal('100000.00')
    )
    
    # Create synthetic backtest data
    backtest_data = pd.DataFrame({
        'sport': ['football'] * 100,
        'event_id': [f'event_{i}' for i in range(100)],
        'bookmaker': ['Pinnacle', 'Bet365', 'William Hill'] * 33 + ['Pinnacle'],
        'odds': [random.uniform(1.5, 3.5) for _ in range(100)],
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='H')
    })
    
    # Load data and run backtest
    system.load_backtest_data(backtest_data)
    results = await system.run_backtest()
    
    print("\n📊 Backtest Results:")
    print(f"Total trades analyzed: {results['total_trades']}")
    print(f"Total profit: ${results['total_profit']:.2f}")
    print(f"ROI: {results['roi']:.2f}%")
    print(f"Win rate: {results['win_rate']:.1f}%")
    print(f"Average profit per trade: ${results['average_profit_per_trade']:.2f}")
    
    print("\n✅ Backtest demo completed!")


if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_paper_trading())