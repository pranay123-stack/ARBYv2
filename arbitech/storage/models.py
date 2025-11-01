"""
Comprehensive Pydantic data models for arbitrage trading system.
Contains all core entities for opportunities, trades, risk management, and notifications.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Dict, Optional, Union, Literal, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator, root_validator, model_validator


# Enums for type safety
class Sport(str, Enum):
    """Supported sports for arbitrage opportunities."""
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    TENNIS = "tennis"
    BASEBALL = "baseball"
    HOCKEY = "hockey"
    MMA = "mma"
    CRICKET = "cricket"
    RUGBY = "rugby"
    VOLLEYBALL = "volleyball"
    GOLF = "golf"
    BOXING = "boxing"
    ESPORTS = "esports"
    POLITICS = "politics"
    ENTERTAINMENT = "entertainment"


class TradeStatus(str, Enum):
    """Trade execution status."""
    PENDING = "pending"
    PLACING_BETS = "placing_bets"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    HEDGING = "hedging"
    SETTLED = "settled"


class ExecutionMode(str, Enum):
    """Trade execution modes."""
    MANUAL = "manual"
    AUTO_FULL = "auto_full"
    AUTO_STEALTH = "auto_stealth"
    DELAYED = "delayed"
    SIMULATED = "simulated"


class RiskTier(str, Enum):
    """Risk assessment tiers."""
    TIER_A = "tier_a"
    TIER_B = "tier_b"
    TIER_C = "tier_c"
    TIER_D = "tier_d"


class NotificationType(str, Enum):
    """Types of notifications."""
    OPPORTUNITY_ALERT = "opportunity_alert"
    TRADE_UPDATE = "trade_update"
    RISK_WARNING = "risk_warning"
    ACCOUNT_UPDATE = "account_update"
    SYSTEM_ERROR = "system_error"
    PROFIT_REALIZED = "profit_realized"
    LIMIT_HIT = "limit_hit"
    MAINTENANCE = "maintenance"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    DISCORD = "discord"
    SLACK = "slack"
    TELEGRAM = "telegram"


class AccountStatus(str, Enum):
    """Bookmaker account status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LIMITED = "limited"
    BANNED = "banned"
    CLOSED = "closed"
    UNDER_REVIEW = "under_review"


class ScannerStatus(str, Enum):
    """Scanner session status."""
    IDLE = "idle"
    SCANNING = "scanning"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


# Base models
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UUIDMixin(BaseModel):
    """Mixin for UUID fields."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier")


# Arbitrage Opportunity Models
class ArbitrageLeg(BaseModel):
    """Individual leg of an arbitrage opportunity."""
    bookmaker: str = Field(..., min_length=1, max_length=100, description="Bookmaker name")
    event_outcome: str = Field(..., min_length=1, max_length=200, description="Specific outcome/bet type")
    odds: Decimal = Field(..., gt=1.0, description="Decimal odds value")
    implied_probability: Decimal = Field(..., ge=0.0, le=1.0, description="Implied probability (0-1)")
    stake_percentage: Decimal = Field(..., gt=0.0, le=1.0, description="Percentage of total stake")
    actual_stake: Decimal = Field(..., gt=0.0, description="Actual stake amount in currency")
    potential_payout: Decimal = Field(..., gt=0.0, description="Potential payout amount")


class ArbitrageOpportunity(UUIDMixin, TimestampMixin):
    """
    Represents an arbitrage opportunity with all necessary details.
    Contains sport, event information, betting legs, profit margins, and risk assessment.
    """
    sport: Sport = Field(..., description="Sport type")
    event_name: str = Field(..., min_length=1, max_length=500, description="Event name/title")
    event_date: datetime = Field(..., description="Event scheduled date/time")
    market_type: str = Field(..., min_length=1, max_length=100, description="Market type (e.g., match_winner, over_under)")
    
    # Arbitrage calculation fields
    legs: List[ArbitrageLeg] = Field(..., min_items=2, description="Betting legs for arbitrage")
    total_stake: Decimal = Field(..., gt=0.0, description="Total stake amount")
    profit_margin: Decimal = Field(..., ge=0.0, description="Profit margin as percentage")
    profit_amount: Decimal = Field(..., ge=0.0, description="Expected profit amount")
    guaranteed_profit: bool = Field(default=True, description="Whether profit is guaranteed")
    
    # Risk and validation
    risk_tier: RiskTier = Field(..., description="Risk assessment tier")
    liquidity_checked: bool = Field(default=False, description="Whether liquidity was verified")
    odds_freshness: datetime = Field(default_factory=datetime.utcnow, description="When odds were last updated")
    validation_errors: List[str] = Field(default_factory=list, description="Validation issues if any")
    
    # Metadata
    source_scanner: str = Field(default="unknown", description="Source scanner name")
    discovered_at: datetime = Field(default_factory=datetime.utcnow, description="When opportunity was discovered")
    expires_at: Optional[datetime] = Field(None, description="When opportunity expires")
    
    @validator('legs')
    def validate_legs(cls, v):
        """Ensure legs percentages sum to 1.0."""
        total_percentage = sum(leg.stake_percentage for leg in v)
        if abs(total_percentage - Decimal('1.0')) > Decimal('0.01'):  # Allow small rounding errors
            raise ValueError("Leg stake percentages must sum to 1.0")
        return v
    
    @validator('profit_margin')
    def validate_profit_margin(cls, v):
        """Ensure profit margin is reasonable."""
        if v > 0.5:  # 50% margin seems unrealistic
            raise ValueError("Profit margin seems unrealistic (>50%)")
        return v


# Trade Models
class StakeData(BaseModel):
    """Detailed stake allocation data."""
    total_stake: Decimal = Field(..., gt=0.0, description="Total amount to stake")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")
    leg_allocations: Dict[str, Decimal] = Field(..., description="Stake per bookmaker/leg")
    fees_included: Decimal = Field(default=0.0, ge=0.0, description="Total fees")
    net_stake: Decimal = Field(..., gt=0.0, description="Net stake after fees")


class TradeTimestamps(BaseModel):
    """Timing information for trade lifecycle."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None


class Trade(UUIDMixin, TimestampMixin):
    """
    Represents an arbitrage trade execution.
    Links users to opportunities and tracks execution details.
    """
    user_id: UUID = Field(..., description="User who initiated the trade")
    opportunity: ArbitrageOpportunity = Field(..., description="Associated arbitrage opportunity")
    
    # Execution details
    status: TradeStatus = Field(default=TradeStatus.PENDING, description="Current trade status")
    execution_mode: ExecutionMode = Field(..., description="How the trade was executed")
    
    # Financial data
    stake_data: StakeData = Field(..., description="Stake allocation and amounts")
    expected_profit: Decimal = Field(..., ge=0.0, description="Expected profit amount")
    actual_profit: Optional[Decimal] = Field(None, description="Actual profit after settlement")
    
    # Timing
    timestamps: TradeTimestamps = Field(default_factory=TradeTimestamps, description="Trade lifecycle timestamps")
    
    # Execution tracking
    placed_bets: List[Dict[str, Any]] = Field(default_factory=list, description="Successfully placed bets")
    failed_bets: List[Dict[str, Any]] = Field(default_factory=list, description="Failed bet attempts")
    hedge_trades: List[Dict[str, Any]] = Field(default_factory=list, description="Hedge transactions")
    
    # Error handling
    error_messages: List[str] = Field(default_factory=list, description="Any error messages")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    
    # Performance metrics
    execution_time_ms: Optional[int] = Field(None, ge=0, description="Execution time in milliseconds")
    slippage: Optional[Decimal] = Field(None, ge=0.0, description="Price slippage experienced")
    
    @model_validator(mode='before')
    @classmethod
    def validate_profit_consistency(cls, values):
        """Ensure profit calculations are consistent."""
        if isinstance(values, dict):
            stake_data = values.get('stake_data')
            expected_profit = values.get('expected_profit')
            
            if stake_data and expected_profit is not None:
                total_potential_return = sum(stake_data.leg_allocations.values())
                if expected_profit > total_potential_return * Decimal('0.1'):  # Max 10% profit margin
                    raise ValueError("Expected profit seems unrealistic")
        
        return values


# Risk Management Models
class TierASettings(BaseModel):
    """Tier A (lowest risk) configuration settings."""
    max_stake_per_trade: Decimal = Field(default=100.0, gt=0.0, description="Maximum stake per trade")
    max_daily_trades: int = Field(default=50, gt=0, description="Maximum trades per day")
    max_daily_exposure: Decimal = Field(default=1000.0, gt=0.0, description="Maximum daily exposure")
    min_profit_margin: Decimal = Field(default=0.02, gt=0.0, description="Minimum profit margin required")
    max_execution_time_ms: int = Field(default=30000, gt=0, description="Maximum execution time")
    allow_stealth_mode: bool = Field(default=True, description="Allow stealth execution")
    max_concurrent_opportunities: int = Field(default=5, gt=0, description="Max concurrent opportunities")


class TierBSettings(BaseModel):
    """Tier B (moderate risk) configuration settings."""
    max_stake_per_trade: Decimal = Field(default=250.0, gt=0.0, description="Maximum stake per trade")
    max_daily_trades: int = Field(default=100, gt=0, description="Maximum trades per day")
    max_daily_exposure: Decimal = Field(default=2500.0, gt=0.0, description="Maximum daily exposure")
    min_profit_margin: Decimal = Field(default=0.015, gt=0.0, description="Minimum profit margin required")
    max_execution_time_ms: int = Field(default=45000, gt=0, description="Maximum execution time")
    allow_stealth_mode: bool = Field(default=True, description="Allow stealth execution")
    max_concurrent_opportunities: int = Field(default=10, gt=0, description="Max concurrent opportunities")


class GlobalLimits(BaseModel):
    """Global system limits and constraints."""
    max_total_exposure: Decimal = Field(default=10000.0, gt=0.0, description="Maximum total exposure")
    max_concurrent_users: int = Field(default=100, gt=0, description="Maximum concurrent users")
    system_min_profit_margin: Decimal = Field(default=0.01, gt=0.0, description="System minimum profit margin")
    max_slippage_tolerance: Decimal = Field(default=0.05, gt=0.0, description="Maximum allowed slippage")
    max_odds_age_minutes: int = Field(default=60, gt=0, description="Maximum age of odds data")


class Failsafes(BaseModel):
    """Emergency failsafe and circuit breaker settings."""
    emergency_stop_loss: Decimal = Field(default=500.0, gt=0.0, description="Emergency stop loss amount")
    max_loss_per_hour: Decimal = Field(default=200.0, gt=0.0, description="Maximum loss per hour")
    max_consecutive_losses: int = Field(default=5, ge=0, description="Max consecutive losses before pause")
    automatic_pause_threshold: Decimal = Field(default=0.1, gt=0.0, description="Pause trading if loss ratio exceeds this")
    cool_down_minutes: int = Field(default=30, ge=0, description="Cool down period after failsafe trigger")
    notification_on_trigger: bool = Field(default=True, description="Send notifications on failsafe triggers")


class RiskConfig(UUIDMixin, TimestampMixin):
    """
    Comprehensive risk management configuration.
    Defines all risk parameters, limits, and failsafe mechanisms.
    """
    user_id: Optional[UUID] = Field(None, description="User-specific config if applicable")
    name: str = Field(..., min_length=1, max_length=100, description="Configuration name")
    description: Optional[str] = Field(None, max_length=500, description="Configuration description")
    
    # Risk tier settings
    tier_a_settings: TierASettings = Field(default_factory=TierASettings, description="Tier A risk settings")
    tier_b_settings: TierBSettings = Field(default_factory=TierBSettings, description="Tier B risk settings")
    
    # Global constraints
    global_limits: GlobalLimits = Field(default_factory=GlobalLimits, description="Global risk limits")
    failsafes: Failsafes = Field(default_factory=Failsafes, description="Emergency failsafes")
    
    # Configuration metadata
    is_active: bool = Field(default=True, description="Whether this config is currently active")
    version: str = Field(default="1.0.0", description="Configuration version")
    last_validated: datetime = Field(default_factory=datetime.utcnow, description="Last validation timestamp")


# Scanner Session Models
class SessionStats(BaseModel):
    """Scanner session performance statistics."""
    opportunities_found: int = Field(default=0, ge=0, description="Total opportunities discovered")
    opportunities_traded: int = Field(default=0, ge=0, description="Opportunities converted to trades")
    total_profit: Decimal = Field(default=0.0, ge=0.0, description="Total profit generated")
    success_rate: Decimal = Field(default=0.0, ge=0.0, le=1.0, description="Success rate (0-1)")
    average_execution_time_ms: int = Field(default=0, ge=0, description="Average execution time")
    errors_encountered: int = Field(default=0, ge=0, description="Number of errors encountered")
    uptime_minutes: Decimal = Field(default=0.0, ge=0.0, description="Session uptime in minutes")


class ScanConfig(BaseModel):
    """Scanner configuration parameters."""
    sports: List[Sport] = Field(..., min_items=1, description="Sports to scan")
    min_profit_margin: Decimal = Field(default=0.02, gt=0.0, description="Minimum profit margin")
    max_stake_per_trade: Decimal = Field(default=100.0, gt=0.0, description="Maximum stake per trade")
    bookmaker_whitelist: List[str] = Field(default_factory=list, description="Allowed bookmakers")
    bookmaker_blacklist: List[str] = Field(default_factory=list, description="Blocked bookmakers")
    max_odds_age_minutes: int = Field(default=30, gt=0, description="Maximum age of odds data")
    scan_interval_seconds: int = Field(default=60, gt=0, description="Time between scans")
    risk_tier_preference: RiskTier = Field(default=RiskTier.TIER_A, description="Preferred risk tier")


class ScannerSession(UUIDMixin, TimestampMixin):
    """
    Represents an active scanner session for discovering arbitrage opportunities.
    Tracks performance, configuration, and status.
    """
    user_id: UUID = Field(..., description="User who owns this scanner session")
    name: str = Field(..., min_length=1, max_length=100, description="Session name")
    
    # Status and configuration
    status: ScannerStatus = Field(default=ScannerStatus.IDLE, description="Current session status")
    scan_config: ScanConfig = Field(..., description="Scanner configuration")
    
    # Performance tracking
    session_stats: SessionStats = Field(default_factory=SessionStats, description="Session statistics")
    
    # Session lifecycle
    started_at: Optional[datetime] = Field(None, description="When session started")
    stopped_at: Optional[datetime] = Field(None, description="When session stopped")
    last_scan_at: Optional[datetime] = Field(None, description="Last scan timestamp")
    
    # Error handling
    current_errors: List[str] = Field(default_factory=list, description="Current session errors")
    last_error_at: Optional[datetime] = Field(None, description="When last error occurred")
    
    # Performance optimization
    average_scan_time_ms: Optional[int] = Field(None, ge=0, description="Average scan duration")
    memory_usage_mb: Optional[float] = Field(None, ge=0.0, description="Memory usage in MB")


# Bookmaker Account Models
class EncryptedCredentials(BaseModel):
    """Encrypted bookmaker account credentials."""
    username_encrypted: str = Field(..., description="Encrypted username")
    password_encrypted: str = Field(..., description="Encrypted password")
    api_key_encrypted: Optional[str] = Field(None, description="Encrypted API key if applicable")
    additional_data: Dict[str, str] = Field(default_factory=dict, description="Additional encrypted data")


class AccountBalance(BaseModel):
    """Account balance information."""
    available_balance: Decimal = Field(..., ge=0.0, description="Available balance for betting")
    total_balance: Decimal = Field(..., ge=0.0, description="Total account balance")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Balance update timestamp")
    is_estimated: bool = Field(default=False, description="Whether balance is estimated")


class BookmakerAccount(UUIDMixin, TimestampMixin):
    """
    Represents a bookmaker account with encrypted credentials and status.
    Contains balance information and account health metrics.
    """
    user_id: UUID = Field(..., description="User who owns this account")
    bookmaker_name: str = Field(..., min_length=1, max_length=100, description="Bookmaker name")
    
    # Account credentials and status
    credentials: EncryptedCredentials = Field(..., description="Encrypted login credentials")
    status: AccountStatus = Field(default=AccountStatus.ACTIVE, description="Account status")
    
    # Financial information
    balance: AccountBalance = Field(..., description="Account balance information")
    daily_bet_limit: Optional[Decimal] = Field(None, ge=0.0, description="Daily betting limit")
    single_bet_limit: Optional[Decimal] = Field(None, ge=0.0, description="Single bet limit")
    
    # Account health and performance
    success_rate: Decimal = Field(default=1.0, ge=0.0, le=1.0, description="Bet success rate")
    total_bets_placed: int = Field(default=0, ge=0, description="Total bets placed")
    last_bet_at: Optional[datetime] = Field(None, description="Last bet placement time")
    
    # Risk assessment
    risk_score: Decimal = Field(default=0.0, ge=0.0, le=1.0, description="Account risk score")
    flagged_for_review: bool = Field(default=False, description="Whether account needs review")
    restriction_notes: List[str] = Field(default_factory=list, description="Any restriction notes")
    
    # API integration
    api_endpoint: Optional[str] = Field(None, description="API endpoint URL")
    rate_limit_per_minute: Optional[int] = Field(None, gt=0, description="API rate limit")
    last_api_call: Optional[datetime] = Field(None, description="Last API call timestamp")


# Notification Models
class MessageData(BaseModel):
    """Structured message data for notifications."""
    title: str = Field(..., min_length=1, max_length=200, description="Message title")
    body: str = Field(..., min_length=1, max_length=1000, description="Message body")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional structured data")
    action_url: Optional[str] = Field(None, description="Optional action URL")
    image_url: Optional[str] = Field(None, description="Optional image URL")


class NotificationChannelConfig(BaseModel):
    """Configuration for specific notification channels."""
    enabled: bool = Field(default=True, description="Whether this channel is enabled")
    rate_limit_per_hour: int = Field(default=100, ge=0, description="Rate limit per hour")
    priority_filter: List[NotificationPriority] = Field(
        default_factory=lambda: [NotificationPriority.HIGH, NotificationPriority.CRITICAL],
        description="Priority levels for this channel"
    )
    quiet_hours: Optional[Dict[str, str]] = Field(None, description="Quiet hours configuration")


class Notification(UUIDMixin, TimestampMixin):
    """
    Represents a notification to be sent to users.
    Supports multiple channels and delivery tracking.
    """
    user_id: UUID = Field(..., description="User to notify")
    type: NotificationType = Field(..., description="Type of notification")
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM, description="Priority level")
    
    # Message content
    message: MessageData = Field(..., description="Message content and data")
    
    # Delivery channels
    channels: List[NotificationChannel] = Field(..., min_items=1, description="Channels to deliver via")
    channel_configs: Dict[NotificationChannel, NotificationChannelConfig] = Field(
        default_factory=dict, description="Per-channel configuration"
    )
    
    # Delivery tracking
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    delivered_channels: List[NotificationChannel] = Field(default_factory=list, description="Successfully delivered channels")
    failed_channels: List[NotificationChannel] = Field(default_factory=list, description="Failed delivery channels")
    
    # Expiration and retry
    expires_at: Optional[datetime] = Field(None, description="When notification expires")
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    
    # Response tracking
    acknowledged_at: Optional[datetime] = Field(None, description="When user acknowledged the notification")
    clicked_at: Optional[datetime] = Field(None, description="When user clicked action link")
    
    @validator('channels', pre=True)
    def validate_channels(cls, v):
        """Ensure channels is always a list."""
        if isinstance(v, set):
            return list(v)
        return v