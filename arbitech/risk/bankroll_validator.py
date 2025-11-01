"""
Real-time bankroll validation system with current balance tracking,
exposure monitoring, and limit enforcement across all active positions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple, Any
from uuid import UUID
import json
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import PriorityQueue

from arbitech.storage.models import (
    ArbitrageOpportunity, Trade, TradeStatus, RiskTier, 
    BookmakerAccount, AccountBalance, GlobalLimits, 
    Failsafes, RiskConfig, StakeData
)


logger = logging.getLogger(__name__)


@dataclass
class BankrollSnapshot:
    """Current state of bankroll and positions."""
    timestamp: datetime
    available_balance: Decimal
    total_balance: Decimal
    locked_balance: Decimal  # In pending trades
    unrealized_pnl: Decimal
    daily_pnl: Decimal
    active_positions_count: int
    max_exposure: Decimal
    current_exposure: Decimal


@dataclass
class BalanceUpdate:
    """Balance update event."""
    bookmaker: str
    account_id: UUID
    new_balance: Decimal
    previous_balance: Decimal
    change_amount: Decimal
    timestamp: datetime
    source: str  # API, manual, etc.
    is_estimated: bool


@dataclass
class ValidationResult:
    """Result of bankroll validation."""
    is_valid: bool
    current_exposure: Decimal
    remaining_capacity: Decimal
    violations: List[str]
    warnings: List[str]
    recommendations: List[str]
    timestamp: datetime


class BankrollValidator:
    """
    Real-time bankroll validation system with comprehensive tracking
    and automatic limit enforcement across all bookmaker accounts.
    """
    
    def __init__(self, risk_config: RiskConfig):
        """
        Initialize the bankroll validator.
        
        Args:
            risk_config: Risk management configuration
        """
        self.risk_config = risk_config
        self.current_exposure: Decimal = '0'
        self.daily_pnl: Decimal = '0'
        self.active_trades: Dict[UUID, Trade] = {}
        self.bookmaker_balances: Dict[str, AccountBalance] = {}
        self.position_tracker: Dict[str, Decimal] = {}  # bookmaker -> exposure
        self.limit_violations: List[Dict[str, Any]] = []
        
        # Thread-safe tracking
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Balance update queue for processing
        self._update_queue: PriorityQueue = PriorityQueue()
        
        # Real-time monitoring
        self._monitoring_active = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Performance metrics
        self.validation_count = 0
        self.total_violations = 0
        self.average_validation_time_ms = '0'
        
        # Balance reconciliation tracking
        self.last_reconciliation: Optional[datetime] = None
        self.reconciliation_discrepancies: List[Dict[str, Any]] = []
        
        logger.info("Bankroll validator initialized")
    
    async def start_monitoring(self):
        """Start real-time bankroll monitoring."""
        if self._monitoring_active:
            return
            
        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Bankroll monitoring started")
    
    async def stop_monitoring(self):
        """Stop real-time bankroll monitoring."""
        self._monitoring_active = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Bankroll monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop for real-time updates."""
        while self._monitoring_active:
            try:
                # Process pending balance updates
                await self._process_balance_updates()
                
                # Validate current bankroll state
                validation_result = await self.validate_bankroll()
                if not validation_result.is_valid:
                    await self._handle_validation_failure(validation_result)
                
                # Reconcile balances periodically
                await self._reconcile_balances()
                
                # Clean up old violations
                self._cleanup_old_violations()
                
                # Sleep before next iteration
                await asyncio.sleep(1)  # 1 second monitoring interval
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Back off on error
    
    async def add_trade(self, trade: Trade) -> bool:
        """
        Add a trade to active positions and update bankroll state.
        
        Args:
            trade: Trade to add
            
        Returns:
            bool: True if trade was added successfully
        """
        with self._lock:
            # Check if trade is valid for bankroll
            validation_result = await self._validate_trade_impact(trade)
            
            if not validation_result.is_valid:
                logger.warning(f"Trade rejected due to bankroll violations: {validation_result.violations}")
                self._record_violation("trade_rejection", validation_result.violations)
                return False
            
            # Add to active trades
            self.active_trades[trade.id] = trade
            self.current_exposure += trade.stake_data.total_stake
            
            # Update position tracking
            for leg in trade.opportunity.legs:
                if leg.bookmaker in self.position_tracker:
                    self.position_tracker[leg.bookmaker] += leg.actual_stake
                else:
                    self.position_tracker[leg.bookmaker] = leg.actual_stake
            
            logger.info(f"Added trade {trade.id} to bankroll, exposure: {self.current_exposure}")
            return True
    
    async def remove_trade(self, trade_id: UUID) -> Optional[Trade]:
        """
        Remove a trade from active positions and update bankroll state.
        
        Args:
            trade_id: ID of trade to remove
            
        Returns:
            Trade: Removed trade or None if not found
        """
        with self._lock:
            trade = self.active_trades.pop(trade_id, None)
            if trade:
                self.current_exposure -= trade.stake_data.total_stake
                
                # Update position tracking
                for leg in trade.opportunity.legs:
                    if leg.bookmaker in self.position_tracker:
                        self.position_tracker[leg.bookmaker] -= leg.actual_stake
                        if self.position_tracker[leg.bookmaker] <= 0:
                            del self.position_tracker[leg.bookmaker]
                
                logger.info(f"Removed trade {trade.id} from bankroll, exposure: {self.current_exposure}")
            
            return trade
    
    async def update_balance(self, bookmaker: str, account_id: UUID, 
                           new_balance: Decimal, source: str = "api") -> bool:
        """
        Update account balance and process reconciliation.
        
        Args:
            bookmaker: Bookmaker name
            account_id: Account ID
            new_balance: New balance amount
            source: Source of balance update
            
        Returns:
            bool: True if update was processed
        """
        # Get previous balance
        key = f"{bookmaker}_{account_id}"
        previous_balance = self.bookmaker_balances.get(key)
        
        # Create balance update event
        update = BalanceUpdate(
            bookmaker=bookmaker,
            account_id=account_id,
            new_balance=new_balance,
            previous_balance=previous_balance.available_balance if previous_balance else '0',
            change_amount=new_balance - (previous_balance.available_balance if previous_balance else '0'),
            timestamp=datetime.utcnow(),
            source=source,
            is_estimated=False
        )
        
        # Add to update queue
        priority = -update.timestamp.timestamp()  # Higher priority for newer updates
        self._update_queue.put((priority, update))
        
        logger.debug(f"Balance update queued for {bookmaker}: {new_balance}")
        return True
    
    async def validate_bankroll(self) -> ValidationResult:
        """
        Comprehensive bankroll validation.
        
        Returns:
            ValidationResult: Complete validation results
        """
        start_time = datetime.utcnow()
        violations = []
        warnings = []
        recommendations = []
        
        # Get current bankroll snapshot
        snapshot = await self._get_bankroll_snapshot()
        
        # Check global exposure limit
        if snapshot.current_exposure > self.risk_config.global_limits.max_total_exposure:
            violation = f"Global exposure {snapshot.current_exposure} exceeds limit {self.risk_config.global_limits.max_total_exposure}"
            violations.append(violation)
        
        # Check bookmaker-specific limits
        for bookmaker, exposure in self.position_tracker.items():
            if exposure > self.risk_config.global_limits.max_total_exposure * '0.3':  # 30% max per bookmaker
                violation = f"Bookmaker {bookmaker} exposure {exposure} exceeds limit"
                violations.append(violation)
        
        # Check daily PnL limits
        if abs(snapshot.daily_pnl) > self.risk_config.failsafes.max_loss_per_hour * 12:  # 12 hours = 1 day approx
            warning = f"Daily PnL {snapshot.daily_pnl} approaching daily limits"
            warnings.append(warning)
        
        # Check for concentration risk
        total_exposure = snapshot.current_exposure
        if total_exposure > 0:
            max_bookmaker_exposure = max(self.position_tracker.values(), default='0')
            concentration_ratio = max_bookmaker_exposure / total_exposure
            
            if concentration_ratio > '0.4':  # 40% concentration limit
                warning = f"High concentration risk: {concentration_ratio:.1%} in single bookmaker"
                warnings.append(warning)
        
        # Calculate remaining capacity
        remaining_capacity = self._calculate_remaining_capacity(snapshot)
        
        # Generate recommendations
        if remaining_capacity < snapshot.total_balance * '0.1':  # Less than 10% capacity
            recommendations.append("Consider reducing position sizes to maintain adequate reserves")
        
        # Update performance metrics
        self.validation_count += 1
        validation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.average_validation_time_ms = (self.average_validation_time_ms * (self.validation_count - 1) + 
                                         str(validation_time)) / self.validation_count
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            current_exposure=snapshot.current_exposure,
            remaining_capacity=remaining_capacity,
            violations=violations,
            warnings=warnings,
            recommendations=recommendations,
            timestamp=datetime.utcnow()
        )
    
    async def _get_bankroll_snapshot(self) -> BankrollSnapshot:
        """Get current bankroll snapshot."""
        total_balance = '0'
        available_balance = '0'
        locked_balance = '0'
        
        # Aggregate bookmaker balances
        for balance in self.bookmaker_balances.values():
            total_balance += balance.total_balance
            available_balance += balance.available_balance
        
        # Calculate locked balance from active trades
        for trade in self.active_trades.values():
            if trade.status in [TradeStatus.PENDING, TradeStatus.PLACING_BETS]:
                locked_balance += trade.stake_data.total_stake
        
        available_for_new_positions = available_balance - locked_balance
        
        return BankrollSnapshot(
            timestamp=datetime.utcnow(),
            available_balance=available_for_new_positions,
            total_balance=total_balance,
            locked_balance=locked_balance,
            unrealized_pnl='0',  # Would be calculated from pending outcomes
            daily_pnl=self.daily_pnl,
            active_positions_count=len(self.active_trades),
            max_exposure=self.risk_config.global_limits.max_total_exposure,
            current_exposure=self.current_exposure
        )
    
    async def _validate_trade_impact(self, trade: Trade) -> ValidationResult:
        """Validate impact of a new trade on bankroll."""
        new_exposure = self.current_exposure + trade.stake_data.total_stake
        violations = []
        warnings = []
        
        # Check if this would exceed global limits
        if new_exposure > self.risk_config.global_limits.max_total_exposure:
            violations.append(f"Trade would exceed global exposure limit")
        
        # Check bookmaker-specific limits
        trade_bookmaker_exposures = {}
        for leg in trade.opportunity.legs:
            current_exposure = self.position_tracker.get(leg.bookmaker, '0')
            new_exposure_per_bookmaker = current_exposure + leg.actual_stake
            
            if new_exposure_per_bookmaker > self.risk_config.global_limits.max_total_exposure * '0.3':
                violations.append(f"Trade would exceed {leg.bookmaker} bookmaker limit")
            
            trade_bookmaker_exposures[leg.bookmaker] = new_exposure_per_bookmaker
        
        # Check profit margin requirements
        if trade.opportunity.profit_margin < self.risk_config.global_limits.system_min_profit_margin:
            violations.append(f"Trade profit margin {trade.opportunity.profit_margin} below minimum")
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            current_exposure=new_exposure,
            remaining_capacity=self.risk_config.global_limits.max_total_exposure - new_exposure,
            violations=violations,
            warnings=warnings,
            recommendations=[],
            timestamp=datetime.utcnow()
        )
    
    async def _process_balance_updates(self):
        """Process pending balance updates."""
        processed_count = 0
        max_processes = 10  # Limit processing per cycle
        
        while not self._update_queue.empty() and processed_count < max_processes:
            try:
                _, update = self._update_queue.get_nowait()
                
                # Update stored balance
                key = f"{update.bookmaker}_{update.account_id}"
                self.bookmaker_balances[key] = AccountBalance(
                    available_balance=update.new_balance,
                    total_balance=update.new_balance,  # Simplified - would calculate properly
                    currency="USD",  # Would get from bookmaker config
                    last_updated=update.timestamp,
                    is_estimated=update.is_estimated
                )
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing balance update: {e}")
                break
    
    async def _reconcile_balances(self):
        """Reconcile bookmaker balances with expected values."""
        # Only reconcile every 5 minutes
        if self.last_reconciliation and (datetime.utcnow() - self.last_reconciliation).total_seconds() < 300:
            return
        
        try:
            # Would implement actual reconciliation logic here
            # For now, just update timestamp
            self.last_reconciliation = datetime.utcnow()
            
            # Check for significant discrepancies
            expected_total = sum(
                trade.stake_data.total_stake 
                for trade in self.active_trades.values()
            )
            
            actual_locked = self.current_exposure
            
            if abs(expected_total - actual_locked) > expected_total * '0.01':  # 1% tolerance
                discrepancy = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "expected_locked": expected_total,
                    "actual_locked": actual_locked,
                    "difference": abs(expected_total - actual_locked)
                }
                self.reconciliation_discrepancies.append(discrepancy)
                logger.warning(f"Balance reconciliation discrepancy: {discrepancy}")
                
        except Exception as e:
            logger.error(f"Error during balance reconciliation: {e}")
    
    async def _handle_validation_failure(self, validation_result: ValidationResult):
        """Handle validation failures."""
        # Log violations
        for violation in validation_result.violations:
            logger.error(f"Bankroll validation failure: {violation}")
            self._record_violation("validation_failure", [violation])
        
        # Trigger alerts based on severity
        if len(validation_result.violations) > 0:
            await self._trigger_circuit_breaker()
    
    def _record_violation(self, violation_type: str, details: List[str]):
        """Record a limit violation."""
        violation = {
            "type": violation_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "exposure": self.current_exposure,
            "balance": sum(b.available_balance for b in self.bookmaker_balances.values())
        }
        
        self.limit_violations.append(violation)
        self.total_violations += 1
        
        # Keep only last 1000 violations
        if len(self.limit_violations) > 1000:
            self.limit_violations = self.limit_violations[-1000:]
    
    async def _trigger_circuit_breaker(self):
        """Trigger circuit breaker for severe violations."""
        logger.critical("CRITICAL: Circuit breaker triggered due to bankroll violations")
        
        # Would implement circuit breaker logic here
        # - Stop new trades
        # - Alert users
        # - Activate failsafes
        
        self._record_violation("circuit_breaker", ["Critical bankroll violations detected"])
    
    def _cleanup_old_violations(self):
        """Remove violations older than 24 hours."""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.limit_violations = [
            v for v in self.limit_violations 
            if datetime.fromisoformat(v["timestamp"]) > cutoff
        ]
    
    def _calculate_remaining_capacity(self, snapshot: BankrollSnapshot) -> Decimal:
        """Calculate remaining bankroll capacity for new positions."""
        available_for_positions = snapshot.available_balance - snapshot.locked_balance
        max_new_exposure = self.risk_config.global_limits.max_total_exposure - snapshot.current_exposure
        
        return min(available_for_positions, max_new_exposure)
    
    async def get_exposure_breakdown(self) -> Dict[str, Any]:
        """Get detailed exposure breakdown by bookmaker and sport."""
        with self._lock:
            breakdown = {
                "total_exposure": self.current_exposure,
                "by_bookmaker": dict(self.position_tracker),
                "by_sport": {},
                "active_trades_count": len(self.active_trades),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Calculate exposure by sport
            sport_exposures = {}
            for trade in self.active_trades.values():
                sport = trade.opportunity.sport
                if sport in sport_exposures:
                    sport_exposures[sport] += trade.stake_data.total_stake
                else:
                    sport_exposures[sport] = trade.stake_data.total_stake
            
            breakdown["by_sport"] = sport_exposures
            
            return breakdown
    
    async def get_bankroll_metrics(self) -> Dict[str, Any]:
        """Get comprehensive bankroll metrics."""
        snapshot = await self._get_bankroll_snapshot()
        
        return {
            "current_exposure": float(self.current_exposure),
            "total_balance": float(snapshot.total_balance),
            "available_balance": float(snapshot.available_balance),
            "locked_balance": float(snapshot.locked_balance),
            "daily_pnl": float(self.daily_pnl),
            "active_positions": len(self.active_trades),
            "limit_utilization": float(self.current_exposure / self.risk_config.global_limits.max_total_exposure),
            "bookmaker_count": len(self.bookmaker_balances),
            "validation_count": self.validation_count,
            "total_violations": self.total_violations,
            "average_validation_time_ms": float(self.average_validation_time_ms),
            "last_update": datetime.utcnow().isoformat()
        }
    
    def get_position_sizing_adjustment(self, proposed_stake: Decimal, bookmaker: str) -> Decimal:
        """
        Calculate adjusted stake size to respect limits.
        
        Args:
            proposed_stake: Originally proposed stake
            bookmaker: Bookmaker name
            
        Returns:
            Adjusted stake amount
        """
        with self._lock:
            # Get current exposure for bookmaker
            current_exposure = self.position_tracker.get(bookmaker, '0')
            
            # Calculate maximum allowed exposure for this bookmaker
            max_bookmaker_exposure = self.risk_config.global_limits.max_total_exposure * '0.3'
            
            # Calculate remaining capacity
            remaining_capacity = max_bookmaker_exposure - current_exposure
            
            # Also check global remaining capacity
            global_remaining = self.risk_config.global_limits.max_total_exposure - self.current_exposure
            
            # Use the more restrictive limit
            final_remaining = min(remaining_capacity, global_remaining)
            
            # Adjust proposed stake if needed
            if proposed_stake > final_remaining:
                adjusted_stake = final_remaining * '0.9'  # 90% of remaining for safety
                logger.info(f"Adjusted stake from {proposed_stake} to {adjusted_stake} for {bookmaker}")
                return max(adjusted_stake, '0')
            
            return proposed_stake
    
    async def shutdown(self):
        """Gracefully shutdown the validator."""
        logger.info("Shutting down bankroll validator...")
        
        # Stop monitoring
        await self.stop_monitoring()
        
        # Shutdown thread pool
        self._executor.shutdown(wait=True)
        
        # Log final metrics
        metrics = await self.get_bankroll_metrics()
        logger.info(f"Final bankroll metrics: {json.dumps(metrics, default=str)}")
        
        logger.info("Bankroll validator shutdown complete")