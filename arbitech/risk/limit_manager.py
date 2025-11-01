"""
Advanced limit management system with configurable limits per bookmaker,
sport, market type, risk tier, and user-defined criteria.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from uuid import UUID, uuid4
import json
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor

from arbitech.storage.models import (
    ArbitrageOpportunity, Trade, Sport, RiskTier, 
    BookmakerAccount, TradeStatus, RiskConfig,
    TierASettings, TierBSettings, GlobalLimits, Failsafes
)


logger = logging.getLogger(__name__)


class LimitType(str, Enum):
    """Types of limits that can be applied."""
    MAX_STAKE_PER_TRADE = "max_stake_per_trade"
    MAX_DAILY_EXPOSURE = "max_daily_exposure"
    MAX_CONCURRENT_POSITIONS = "max_concurrent_positions"
    MIN_PROFIT_MARGIN = "min_profit_margin"
    MAX_PROFIT_PER_TRADE = "max_profit_per_trade"
    MAX_CONCENTRATION_RATIO = "max_concentration_ratio"
    MAX_BOOKMAKER_EXPOSURE = "max_bookmaker_exposure"
    MAX_SPORT_EXPOSURE = "max_sport_exposure"
    MAX_MARKET_TYPE_EXPOSURE = "max_market_type_exposure"
    MAX_USER_DEFINED = "max_user_defined"


class LimitScope(str, Enum):
    """Scope of limit application."""
    GLOBAL = "global"
    BOOKMAKER = "bookmaker"
    SPORT = "sport"
    MARKET_TYPE = "market_type"
    RISK_TIER = "risk_tier"
    USER_DEFINED = "user_defined"
    TIME_BASED = "time_based"


class AlertSeverity(str, Enum):
    """Severity levels for limit alerts."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class LimitRule:
    """Individual limit rule definition."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    limit_type: LimitType = LimitType.MAX_STAKE_PER_TRADE
    scope: LimitScope = LimitScope.GLOBAL
    scope_value: str = ""  # bookmaker name, sport, market type, etc.
    value: Decimal = '0'
    unit: str = "currency"  # "currency", "percentage", "count"
    
    # Time-based constraints
    time_window: Optional[int] = None  # seconds
    rolling_window: bool = True
    
    # Conditions
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # State
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # Performance tracking
    hit_count: int = 0
    last_hit: Optional[datetime] = None


@dataclass
class LimitUsage:
    """Current usage of a specific limit."""
    limit_id: UUID
    current_usage: Decimal = '0'
    percentage_used: Decimal = '0'
    remaining_capacity: Decimal = '0'
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    hit_count: int = 0
    is_breached: bool = False
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LimitAlert:
    """Alert triggered when limits are approached or breached."""
    id: UUID = field(default_factory=uuid4)
    alert_type: str = ""  # "approach", "breach", "emergency"
    severity: AlertSeverity = AlertSeverity.WARNING
    limit_id: UUID = None
    limit_name: str = ""
    current_usage: Decimal = '0'
    limit_value: Decimal = '0'
    usage_percentage: Decimal = '0'
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved_at: Optional[datetime] = None


class LimitManager:
    """
    Advanced limit management system with comprehensive rule engine
    and real-time usage tracking across multiple dimensions.
    """
    
    def __init__(self, risk_config: RiskConfig):
        """
        Initialize the limit manager.
        
        Args:
            risk_config: Risk management configuration
        """
        self.risk_config = risk_config
        self.rules: Dict[UUID, LimitRule] = {}
        self.usage_tracker: Dict[str, LimitUsage] = {}  # key -> usage
        self.alerts: deque = deque(maxlen=1000)
        self.usage_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Thread-safe operations
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Rule engine
        self._rule_cache: Dict[str, List[LimitRule]] = {}
        self._last_cache_update = datetime.min
        
        # Performance metrics
        self.rule_evaluations = 0
        self.total_limit_checks = 0
        self.alerts_sent = 0
        self.average_check_time_ms = '0'
        
        # Initialize default rules
        self._initialize_default_rules()
        
        logger.info("Limit manager initialized")
    
    def _initialize_default_rules(self):
        """Initialize default limit rules from risk configuration."""
        now = datetime.utcnow()
        
        # Global exposure limit
        global_exposure_rule = LimitRule(
            name="Global Exposure Limit",
            description="Maximum total exposure across all positions",
            limit_type=LimitType.MAX_DAILY_EXPOSURE,
            scope=LimitScope.GLOBAL,
            value=self.risk_config.global_limits.max_total_exposure,
            unit="currency",
            created_at=now,
            last_updated=now
        )
        self.rules[global_exposure_rule.id] = global_exposure_rule
        
        # Profit margin requirement
        profit_margin_rule = LimitRule(
            name="Minimum Profit Margin",
            description="Minimum profit margin for all trades",
            limit_type=LimitType.MIN_PROFIT_MARGIN,
            scope=LimitScope.GLOBAL,
            value=self.risk_config.global_limits.system_min_profit_margin,
            unit="percentage",
            created_at=now,
            last_updated=now
        )
        self.rules[profit_margin_rule.id] = profit_margin_rule
        
        # Bookmaker-specific exposure limits
        bookmaker_concentration_rule = LimitRule(
            name="Bookmaker Concentration Limit",
            description="Maximum exposure concentration per bookmaker",
            limit_type=LimitType.MAX_CONCENTRATION_RATIO,
            scope=LimitScope.GLOBAL,
            value='0.3',  # 30% concentration limit
            unit="percentage",
            conditions={"max_ratio": '0.3'},
            created_at=now,
            last_updated=now
        )
        self.rules[bookmaker_concentration_rule.id] = bookmaker_concentration_rule
        
        # Risk tier specific rules
        tier_a_max_stake = LimitRule(
            name="Tier A Max Stake",
            description="Maximum stake per trade for Tier A opportunities",
            limit_type=LimitType.MAX_STAKE_PER_TRADE,
            scope=LimitScope.RISK_TIER,
            scope_value="tier_a",
            value=self.risk_config.tier_a_settings.max_stake_per_trade,
            unit="currency",
            conditions={"risk_tier": RiskTier.TIER_A},
            created_at=now,
            last_updated=now
        )
        self.rules[tier_a_max_stake.id] = tier_a_max_stake
        
        tier_b_max_stake = LimitRule(
            name="Tier B Max Stake",
            description="Maximum stake per trade for Tier B opportunities",
            limit_type=LimitType.MAX_STAKE_PER_TRADE,
            scope=LimitScope.RISK_TIER,
            scope_value="tier_b",
            value=self.risk_config.tier_b_settings.max_stake_per_trade,
            unit="currency",
            conditions={"risk_tier": RiskTier.TIER_B},
            created_at=now,
            last_updated=now
        )
        self.rules[tier_b_max_stake.id] = tier_b_max_stake
        
        # Daily exposure limits by risk tier
        tier_a_daily = LimitRule(
            name="Tier A Daily Exposure",
            description="Maximum daily exposure for Tier A trades",
            limit_type=LimitType.MAX_DAILY_EXPOSURE,
            scope=LimitScope.RISK_TIER,
            scope_value="tier_a",
            value=self.risk_config.tier_a_settings.max_daily_exposure,
            unit="currency",
            time_window=86400,  # 24 hours
            conditions={"risk_tier": RiskTier.TIER_A},
            created_at=now,
            last_updated=now
        )
        self.rules[tier_a_daily.id] = tier_a_daily
        
        tier_b_daily = LimitRule(
            name="Tier B Daily Exposure",
            description="Maximum daily exposure for Tier B trades",
            limit_type=LimitType.MAX_DAILY_EXPOSURE,
            scope=LimitScope.RISK_TIER,
            scope_value="tier_b",
            value=self.risk_config.tier_b_settings.max_daily_exposure,
            unit="currency",
            time_window=86400,  # 24 hours
            conditions={"risk_tier": RiskTier.TIER_B},
            created_at=now,
            last_updated=now
        )
        self.rules[tier_b_daily.id] = tier_b_daily
        
        logger.info(f"Initialized {len(self.rules)} default limit rules")
    
    async def check_trade_limits(self, opportunity: ArbitrageOpportunity, 
                                proposed_stake: Decimal, user_id: UUID) -> Dict[str, Any]:
        """
        Check if a trade proposal respects all applicable limits.
        
        Args:
            opportunity: Arbitrage opportunity
            proposed_stake: Proposed stake amount
            user_id: User ID
            
        Returns:
            Dict containing validation results and recommendations
        """
        start_time = datetime.utcnow()
        violations = []
        warnings = []
        recommendations = []
        applicable_rules = []
        
        # Get applicable rules
        applicable_rules = self._get_applicable_rules(
            scope_value=opportunity.sport.value,
            market_type=opportunity.market_type,
            risk_tier=opportunity.risk_tier
        )
        
        # Evaluate each applicable rule
        for rule in applicable_rules:
            result = await self._evaluate_rule(rule, opportunity, proposed_stake, user_id)
            
            if result["is_violated"]:
                violations.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "message": result["message"],
                    "current_usage": result["current_usage"],
                    "limit_value": result["limit_value"]
                })
            elif result["is_warning"]:
                warnings.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "message": result["message"],
                    "usage_percentage": result["usage_percentage"]
                })
            
            # Update usage tracking
            await self._update_usage(rule, result["current_usage"])
            
            # Generate recommendations
            if result["is_violated"]:
                recommendations.extend(result["recommendations"])
        
        # Calculate execution time
        check_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.total_limit_checks += 1
        self.average_check_time_ms = (
            self.average_check_time_ms * (self.total_limit_checks - 1) + str(check_time)
        ) / self.total_limit_checks
        
        return {
            "is_valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "recommendations": recommendations,
            "applicable_rules": len(applicable_rules),
            "check_time_ms": check_time,
            "remaining_capacity": self._calculate_remaining_capacity(opportunity, proposed_stake),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def record_trade_execution(self, trade: Trade):
        """Record trade execution and update limit usage."""
        with self._lock:
            # Update usage for all applicable rules
            applicable_rules = self._get_applicable_rules(
                scope_value=trade.opportunity.sport.value,
                market_type=trade.opportunity.market_type,
                risk_tier=trade.opportunity.risk_tier
            )
            
            for rule in applicable_rules:
                if rule.limit_type == LimitType.MAX_STAKE_PER_TRADE:
                    usage_increment = trade.stake_data.total_stake
                elif rule.limit_type == LimitType.MAX_DAILY_EXPOSURE:
                    usage_increment = trade.stake_data.total_stake
                elif rule.limit_type == LimitType.MAX_PROFIT_PER_TRADE:
                    usage_increment = trade.expected_profit
                else:
                    usage_increment = '1'  # Count-based limits
                
                await self._increment_usage(rule, usage_increment)
            
            logger.info(f"Recorded trade execution for limits tracking")
    
    def add_custom_rule(self, rule: LimitRule) -> UUID:
        """
        Add a custom limit rule.
        
        Args:
            rule: Limit rule to add
            
        Returns:
            UUID of added rule
        """
        with self._lock:
            rule.created_at = datetime.utcnow()
            rule.last_updated = datetime.utcnow()
            self.rules[rule.id] = rule
            
            # Clear cache
            self._rule_cache.clear()
            
            logger.info(f"Added custom limit rule: {rule.name}")
            return rule.id
    
    def remove_rule(self, rule_id: UUID) -> bool:
        """
        Remove a limit rule.
        
        Args:
            rule_id: ID of rule to remove
            
        Returns:
            bool: True if rule was removed
        """
        with self._lock:
            if rule_id in self.rules:
                rule_name = self.rules[rule_id].name
                del self.rules[rule_id]
                
                # Clear usage tracking for this rule
                key = f"rule_{rule_id}"
                if key in self.usage_tracker:
                    del self.usage_tracker[key]
                
                # Clear cache
                self._rule_cache.clear()
                
                logger.info(f"Removed limit rule: {rule_name}")
                return True
            
            return False
    
    def update_rule(self, rule_id: UUID, updates: Dict[str, Any]) -> bool:
        """
        Update an existing limit rule.
        
        Args:
            rule_id: ID of rule to update
            updates: Dictionary of updates
            
        Returns:
            bool: True if rule was updated
        """
        with self._lock:
            if rule_id not in self.rules:
                return False
            
            rule = self.rules[rule_id]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            rule.last_updated = datetime.utcnow()
            
            # Clear cache
            self._rule_cache.clear()
            
            logger.info(f"Updated limit rule: {rule.name}")
            return True
    
    def _get_applicable_rules(self, scope_value: str = "", 
                             market_type: str = "", 
                             risk_tier: Optional[RiskTier] = None) -> List[LimitRule]:
        """
        Get all rules applicable to a given context.
        
        Args:
            scope_value: Bookmaker, sport, or other scope value
            market_type: Market type
            risk_tier: Risk tier
            
        Returns:
            List of applicable rules
        """
        # Check cache validity
        cache_key = f"{scope_value}_{market_type}_{risk_tier.value if risk_tier else 'none'}"
        if cache_key in self._rule_cache:
            cache_time = self._rule_cache.get("_cache_time")
            if cache_time and (datetime.utcnow() - cache_time).total_seconds() < 60:
                return self._rule_cache[cache_key]
        
        applicable_rules = []
        
        for rule in self.rules.values():
            if not rule.is_active:
                continue
            
            # Check scope applicability
            if rule.scope == LimitScope.GLOBAL:
                applicable_rules.append(rule)
            elif rule.scope == LimitScope.BOOKMAKER and rule.scope_value == scope_value:
                applicable_rules.append(rule)
            elif rule.scope == LimitScope.SPORT and rule.scope_value == scope_value:
                applicable_rules.append(rule)
            elif rule.scope == LimitScope.MARKET_TYPE and rule.scope_value == market_type:
                applicable_rules.append(rule)
            elif rule.scope == LimitScope.RISK_TIER and rule.scope_value == risk_tier.value:
                applicable_rules.append(rule)
        
        # Cache results
        self._rule_cache[cache_key] = applicable_rules
        self._rule_cache["_cache_time"] = datetime.utcnow()
        
        return applicable_rules
    
    async def _evaluate_rule(self, rule: LimitRule, opportunity: ArbitrageOpportunity,
                           proposed_stake: Decimal, user_id: UUID) -> Dict[str, Any]:
        """
        Evaluate a single limit rule.
        
        Args:
            rule: Rule to evaluate
            opportunity: Arbitrage opportunity
            proposed_stake: Proposed stake
            user_id: User ID
            
        Returns:
            Evaluation results
        """
        # Get current usage for this rule
        usage_key = f"{rule.scope.value}_{rule.scope_value}_{rule.limit_type.value}"
        usage = self.usage_tracker.get(usage_key)
        
        if not usage:
            usage = LimitUsage(
                limit_id=rule.id,
                current_usage='0',
                percentage_used='0',
                remaining_capacity=rule.value,
                window_start=datetime.utcnow() if rule.time_window else None,
                window_end=datetime.utcnow() + timedelta(seconds=rule.time_window) if rule.time_window else None
            )
            self.usage_tracker[usage_key] = usage
        
        # Calculate projected usage
        if rule.limit_type == LimitType.MAX_STAKE_PER_TRADE:
            # Check individual stake
            projected_usage = proposed_stake
        elif rule.limit_type == LimitType.MAX_DAILY_EXPOSURE:
            # Check daily exposure
            projected_usage = usage.current_usage + proposed_stake
        elif rule.limit_type == LimitType.MIN_PROFIT_MARGIN:
            # Check profit margin
            projected_usage = opportunity.profit_margin
        elif rule.limit_type == LimitType.MAX_CONCENTRATION_RATIO:
            # Check concentration ratio
            projected_usage = '0'  # Would calculate based on bookmaker exposure
        else:
            projected_usage = usage.current_usage
        
        # Evaluate violation
        is_violated = False
        is_warning = False
        message = ""
        
        if rule.limit_type == LimitType.MIN_PROFIT_MARGIN:
            if projected_usage < rule.value:
                is_violated = True
                message = f"Profit margin {projected_usage:.2%} below minimum {rule.value:.2%}"
        else:
            # For limits where higher is worse
            if projected_usage > rule.value:
                is_violated = True
                message = f"Usage {projected_usage} exceeds limit {rule.value}"
            elif projected_usage > rule.value * '0.8':  # 80% threshold for warnings
                is_warning = True
                message = f"Usage approaching limit: {projected_usage:.1%} of {rule.value}"
        
        # Calculate usage percentage
        usage_percentage = '0'
        if rule.value > 0:
            usage_percentage = (projected_usage / rule.value * 100).quantize('0.01')
        
        # Generate recommendations
        recommendations = []
        if is_violated:
            if rule.limit_type == LimitType.MIN_PROFIT_MARGIN:
                recommendations.append("Seek opportunities with higher profit margins")
            else:
                recommendations.append("Reduce stake size to respect limits")
        
        return {
            "is_violated": is_violated,
            "is_warning": is_warning,
            "message": message,
            "current_usage": projected_usage,
            "limit_value": rule.value,
            "usage_percentage": usage_percentage,
            "recommendations": recommendations
        }
    
    async def _update_usage(self, rule: LimitRule, current_usage: Decimal):
        """Update usage tracking for a rule."""
        usage_key = f"{rule.scope.value}_{rule.scope_value}_{rule.limit_type.value}"
        usage = self.usage_tracker.get(usage_key)
        
        if usage:
            usage.current_usage = current_usage
            usage.percentage_used = (current_usage / rule.value * 100).quantize('0.01')
            usage.remaining_capacity = max(rule.value - current_usage, '0')
            usage.last_updated = datetime.utcnow()
            
            # Check for alerts
            await self._check_alert_thresholds(usage, rule)
    
    async def _increment_usage(self, rule: LimitRule, increment: Decimal):
        """Increment usage for a rule."""
        usage_key = f"{rule.scope.value}_{rule.scope_value}_{rule.limit_type.value}"
        usage = self.usage_tracker.get(usage_key)
        
        if not usage:
            usage = LimitUsage(
                limit_id=rule.id,
                current_usage='0',
                percentage_used='0',
                remaining_capacity=rule.value
            )
            self.usage_tracker[usage_key] = usage
        
        # Check if we're crossing into a violation
        was_breached = usage.is_breached
        usage.current_usage += increment
        usage.percentage_used = (usage.current_usage / rule.value * 100).quantize('0.01')
        usage.remaining_capacity = max(rule.value - usage.current_usage, '0')
        usage.hit_count += 1
        usage.last_updated = datetime.utcnow()
        
        # Update breach status
        usage.is_breached = usage.current_usage >= rule.value
        
        # Record history
        self._record_usage_history(usage_key, usage.current_usage)
        
        # Trigger alerts if newly breached
        if not was_breached and usage.is_breached:
            await self._trigger_limit_breach_alert(rule, usage)
        
        # Update rule hit count
        rule.hit_count += 1
        rule.last_hit = datetime.utcnow()
    
    async def _check_alert_thresholds(self, usage: LimitUsage, rule: LimitRule):
        """Check if usage crosses alert thresholds."""
        if usage.percentage_used >= 100:
            await self._trigger_breach_alert(rule, usage)
        elif usage.percentage_used >= 80:
            await self._trigger_warning_alert(rule, usage, "approaching_limit")
        elif usage.percentage_used >= 60:
            await self._trigger_info_alert(rule, usage, "moderate_usage")
    
    async def _trigger_breach_alert(self, rule: LimitRule, usage: LimitUsage):
        """Trigger a limit breach alert."""
        alert = LimitAlert(
            alert_type="breach",
            severity=AlertSeverity.CRITICAL,
            limit_id=rule.id,
            limit_name=rule.name,
            current_usage=usage.current_usage,
            limit_value=rule.value,
            usage_percentage=usage.percentage_used,
            message=f"LIMIT BREACH: {rule.name} exceeded - {usage.current_usage}/{rule.value}"
        )
        
        self.alerts.append(alert)
        self.alerts_sent += 1
        
        logger.critical(f"LIMIT BREACH: {rule.name} - {usage.current_usage} >= {rule.value}")
    
    async def _trigger_warning_alert(self, rule: LimitRule, usage: LimitUsage, alert_type: str):
        """Trigger a warning alert."""
        alert = LimitAlert(
            alert_type=alert_type,
            severity=AlertSeverity.WARNING,
            limit_id=rule.id,
            limit_name=rule.name,
            current_usage=usage.current_usage,
            limit_value=rule.value,
            usage_percentage=usage.percentage_used,
            message=f"WARNING: {rule.name} at {usage.percentage_used:.1f}% of limit"
        )
        
        self.alerts.append(alert)
        self.alerts_sent += 1
        
        logger.warning(f"Limit warning: {rule.name} - {usage.percentage_used:.1f}% used")
    
    async def _trigger_info_alert(self, rule: LimitRule, usage: LimitUsage, alert_type: str):
        """Trigger an info alert."""
        alert = LimitAlert(
            alert_type=alert_type,
            severity=AlertSeverity.INFO,
            limit_id=rule.id,
            limit_name=rule.name,
            current_usage=usage.current_usage,
            limit_value=rule.value,
            usage_percentage=usage.percentage_used,
            message=f"INFO: {rule.name} usage at {usage.percentage_used:.1f}%"
        )
        
        self.alerts.append(alert)
        self.alerts_sent += 1
        
        logger.info(f"Limit info: {rule.name} - {usage.percentage_used:.1f}% used")
    
    async def _trigger_limit_breach_alert(self, rule: LimitRule, usage: LimitUsage):
        """Trigger alert for newly breached limit."""
        alert = LimitAlert(
            alert_type="breach",
            severity=AlertSeverity.EMERGENCY,
            limit_id=rule.id,
            limit_name=rule.name,
            current_usage=usage.current_usage,
            limit_value=rule.value,
            usage_percentage='100',
            message=f"EMERGENCY: {rule.name} just breached - {usage.current_usage} >= {rule.value}"
        )
        
        self.alerts.append(alert)
        self.alerts_sent += 1
        
        # This is critical - would trigger circuit breaker
        logger.critical(f"LIMIT BREACH: {rule.name} - IMMEDIATE ACTION REQUIRED")
    
    def _calculate_remaining_capacity(self, opportunity: ArbitrageOpportunity, 
                                    proposed_stake: Decimal) -> Dict[str, Decimal]:
        """Calculate remaining capacity across different limit types."""
        capacity = {
            "global_exposure": '0',
            "stake_limit": '0',
            "daily_exposure": '0',
            "profit_margin": '0'
        }
        
        # Get applicable rules
        applicable_rules = self._get_applicable_rules(
            scope_value=opportunity.sport.value,
            market_type=opportunity.market_type,
            risk_tier=opportunity.risk_tier
        )
        
        for rule in applicable_rules:
            usage_key = f"{rule.scope.value}_{rule.scope_value}_{rule.limit_type.value}"
            usage = self.usage_tracker.get(usage_key)
            
            if usage:
                if rule.limit_type == LimitType.MAX_DAILY_EXPOSURE:
                    capacity["daily_exposure"] = usage.remaining_capacity
                elif rule.limit_type == LimitType.MAX_STAKE_PER_TRADE:
                    capacity["stake_limit"] = min(capacity["stake_limit"], rule.value)
                elif rule.limit_type == LimitType.MIN_PROFIT_MARGIN:
                    capacity["profit_margin"] = rule.value
        
        # Global exposure capacity
        global_key = f"global_{LimitType.MAX_DAILY_EXPOSURE.value}"
        global_usage = self.usage_tracker.get(global_key)
        if global_usage:
            capacity["global_exposure"] = global_usage.remaining_capacity
        
        return capacity
    
    def _record_usage_history(self, usage_key: str, usage_value: Decimal):
        """Record usage history for trend analysis."""
        if usage_key not in self.usage_history:
            self.usage_history[usage_key] = deque(maxlen=100)
        
        self.usage_history[usage_key].append({
            "timestamp": datetime.utcnow().isoformat(),
            "usage": usage_value
        })
    
    async def get_limit_summary(self) -> Dict[str, Any]:
        """Get comprehensive limit management summary."""
        with self._lock:
            # Calculate overall metrics
            total_rules = len(self.rules)
            active_rules = sum(1 for rule in self.rules.values() if rule.is_active)
            
            breached_limits = sum(1 for usage in self.usage_tracker.values() if usage.is_breached)
            approaching_limits = sum(1 for usage in self.usage_tracker.values() 
                                   if '80' <= usage.percentage_used < '100')
            
            # Get recent alerts
            recent_alerts = [
                {
                    "type": alert.alert_type,
                    "severity": alert.severity.value,
                    "limit_name": alert.limit_name,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in list(self.alerts)[-10:]  # Last 10 alerts
            ]
            
            # Calculate most hit rules
            most_hit_rules = sorted(
                [(rule.name, rule.hit_count) for rule in self.rules.values()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                "total_rules": total_rules,
                "active_rules": active_rules,
                "breached_limits": breached_limits,
                "approaching_limits": approaching_limits,
                "alerts_sent": self.alerts_sent,
                "rule_evaluations": self.rule_evaluations,
                "total_limit_checks": self.total_limit_checks,
                "average_check_time_ms": float(self.average_check_time_ms),
                "recent_alerts": recent_alerts,
                "most_hit_rules": most_hit_rules,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_detailed_usage_report(self) -> Dict[str, Any]:
        """Get detailed usage report for all limits."""
        with self._lock:
            usage_report = {
                "usage_by_rule": {},
                "usage_by_scope": defaultdict(lambda: {
                    "total_usage": '0',
                    "active_rules": 0,
                    "breached_count": 0
                }),
                "historical_trends": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Detailed usage by rule
            for usage_key, usage in self.usage_tracker.items():
                rule_id, scope_type = usage_key.split("_", 1)
                rule = self.rules.get(UUID(rule_id))
                
                if rule:
                    usage_report["usage_by_rule"][rule.name] = {
                        "current_usage": float(usage.current_usage),
                        "limit_value": float(rule.value),
                        "percentage_used": float(usage.percentage_used),
                        "remaining_capacity": float(usage.remaining_capacity),
                        "scope": rule.scope.value,
                        "scope_value": rule.scope_value,
                        "is_breached": usage.is_breached,
                        "hit_count": usage.hit_count,
                        "last_updated": usage.last_updated.isoformat()
                    }
                    
                    # Aggregate by scope
                    scope_data = usage_report["usage_by_scope"][rule.scope.value]
                    scope_data["total_usage"] += usage.current_usage
                    scope_data["active_rules"] += 1
                    if usage.is_breached:
                        scope_data["breached_count"] += 1
            
            # Historical trends
            for usage_key, history in self.usage_history.items():
                usage_report["historical_trends"][usage_key] = list(history)
            
            return usage_report
    
    async def reset_limit_usage(self, rule_id: UUID) -> bool:
        """
        Reset usage tracking for a specific rule.
        
        Args:
            rule_id: ID of rule to reset
            
        Returns:
            bool: True if reset was successful
        """
        with self._lock:
            if rule_id not in self.rules:
                return False
            
            rule = self.rules[rule_id]
            usage_key = f"{rule.scope.value}_{rule.scope_value}_{rule.limit_type.value}"
            
            if usage_key in self.usage_tracker:
                del self.usage_tracker[usage_key]
                
                if usage_key in self.usage_history:
                    del self.usage_history[usage_key]
                
                logger.info(f"Reset usage tracking for rule: {rule.name}")
                return True
            
            return False
    
    def acknowledge_alert(self, alert_id: UUID) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: ID of alert to acknowledge
            
        Returns:
            bool: True if alert was acknowledged
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.resolved_at = datetime.utcnow()
                logger.info(f"Alert acknowledged: {alert.limit_name}")
                return True
        
        return False
    
    async def export_rules(self) -> Dict[str, Any]:
        """Export all rules and current usage state."""
        with self._lock:
            return {
                "rules": [
                    {
                        "id": str(rule.id),
                        "name": rule.name,
                        "description": rule.description,
                        "limit_type": rule.limit_type.value,
                        "scope": rule.scope.value,
                        "scope_value": rule.scope_value,
                        "value": str(rule.value),
                        "unit": rule.unit,
                        "time_window": rule.time_window,
                        "conditions": rule.conditions,
                        "is_active": rule.is_active,
                        "created_at": rule.created_at.isoformat(),
                        "last_updated": rule.last_updated.isoformat(),
                        "hit_count": rule.hit_count,
                        "last_hit": rule.last_hit.isoformat() if rule.last_hit else None
                    }
                    for rule in self.rules.values()
                ],
                "usage": {
                    key: {
                        "current_usage": str(usage.current_usage),
                        "percentage_used": str(usage.percentage_used),
                        "remaining_capacity": str(usage.remaining_capacity),
                        "is_breached": usage.is_breached,
                        "hit_count": usage.hit_count,
                        "last_updated": usage.last_updated.isoformat()
                    }
                    for key, usage in self.usage_tracker.items()
                },
                "export_timestamp": datetime.utcnow().isoformat()
            }
    
    async def import_rules(self, rules_data: Dict[str, Any]) -> int:
        """
        Import rules and usage state.
        
        Args:
            rules_data: Exported rules data
            
        Returns:
            int: Number of rules imported
        """
        imported_count = 0
        
        for rule_data in rules_data.get("rules", []):
            try:
                rule = LimitRule(
                    id=UUID(rule_data["id"]),
                    name=rule_data["name"],
                    description=rule_data["description"],
                    limit_type=LimitType(rule_data["limit_type"]),
                    scope=LimitScope(rule_data["scope"]),
                    scope_value=rule_data["scope_value"],
                    value=rule_data["value"],
                    unit=rule_data["unit"],
                    time_window=rule_data.get("time_window"),
                    conditions=rule_data.get("conditions", {}),
                    is_active=rule_data.get("is_active", True),
                    created_at=datetime.fromisoformat(rule_data["created_at"]),
                    last_updated=datetime.fromisoformat(rule_data["last_updated"]),
                    hit_count=rule_data.get("hit_count", 0)
                )
                
                if rule_data.get("last_hit"):
                    rule.last_hit = datetime.fromisoformat(rule_data["last_hit"])
                
                self.rules[rule.id] = rule
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Failed to import rule {rule_data.get('name', 'unknown')}: {e}")
        
        # Clear cache after import
        self._rule_cache.clear()
        
        logger.info(f"Imported {imported_count} limit rules")
        return imported_count