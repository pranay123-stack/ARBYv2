"""
Real-time exposure tracking with correlation analysis, concentration monitoring,
and portfolio-level risk assessment.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from uuid import UUID
import json
import statistics
import numpy as np
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

from arbitech.storage.models import (
    ArbitrageOpportunity, Trade, Sport, RiskTier, 
    BookmakerAccount, TradeStatus, StakeData,
    ArbitrageLeg
)


logger = logging.getLogger(__name__)


class ExposureType(str, Enum):
    """Types of exposure being tracked."""
    BOOKMAKER = "bookmaker"
    SPORT = "sport"
    MARKET_TYPE = "market_type"
    EVENT = "event"
    CORRELATION_GROUP = "correlation_group"
    TEMPORAL = "temporal"
    PORTFOLIO = "portfolio"


class RiskMetric(str, Enum):
    """Types of risk metrics calculated."""
    VALUE_AT_RISK = "value_at_risk"
    MAXIMUM_DRAWDOWN = "maximum_drawdown"
    SHARPE_RATIO = "sharpe_ratio"
    CORRELATION_MATRIX = "correlation_matrix"
    CONCENTRATION_RATIO = "concentration_ratio"
    DIVERSIFICATION_RATIO = "diversification_ratio"
    VAR_BY_BOOKMAKER = "var_by_bookmaker"
    HEATMAP = "heatmap"


@dataclass
class ExposurePosition:
    """Individual exposure position."""
    id: UUID
    source_type: ExposureType
    source_value: str  # bookmaker name, sport, etc.
    trade_id: UUID
    opportunity_id: UUID
    stake: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal
    risk_weight: Decimal = '1'
    correlation_key: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExposureSnapshot:
    """Snapshot of portfolio exposure at a point in time."""
    timestamp: datetime
    total_exposure: Decimal
    exposure_by_type: Dict[ExposureType, Decimal]
    exposure_by_source: Dict[str, Decimal]
    concentration_metrics: Dict[str, Decimal]
    correlation_matrix: Dict[Tuple[str, str], Decimal]
    risk_metrics: Dict[RiskMetric, Decimal]
    active_positions: int
    top_exposures: List[Dict[str, Any]]


@dataclass
class RiskCorrelation:
    """Correlation between two exposure sources."""
    source_a: str
    source_b: str
    correlation_coefficient: Decimal
    confidence_level: Decimal
    sample_size: int
    last_updated: datetime
    is_significant: bool


@dataclass
class ConcentrationMetric:
    """Concentration risk metrics."""
    source_type: ExposureType
    source_value: str
    exposure_amount: Decimal
    concentration_ratio: Decimal
    percentile_rank: int
    is_concentrated: bool
    risk_level: str  # "low", "medium", "high", "critical"


class ExposureTracker:
    """
    Real-time exposure tracking with advanced correlation analysis
    and portfolio-level risk assessment.
    """
    
    def __init__(self):
        """Initialize the exposure tracker."""
        self.active_positions: Dict[UUID, ExposurePosition] = {}
        self.exposure_history: deque = deque(maxlen=1000)
        self.correlation_cache: Dict[Tuple[str, str], RiskCorrelation] = {}
        self.concentration_metrics: Dict[str, ConcentrationMetric] = {}
        
        # Thread-safe operations
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Real-time monitoring
        self._monitoring_active = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Analytics
        self._correlation_window = timedelta(days=30)  # 30 days for correlation analysis
        self._risk_window = timedelta(hours=24)  # 24 hours for risk metrics
        self._concentration_threshold = '0.3'  # 30% concentration threshold
        
        # Performance tracking
        self.total_calculations = 0
        self.correlation_updates = 0
        self.concentration_alerts = 0
        self.average_calculation_time_ms = '0'
        
        logger.info("Exposure tracker initialized")
    
    async def start_monitoring(self):
        """Start real-time exposure monitoring."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Exposure tracking monitoring started")
    
    async def stop_monitoring(self):
        """Stop real-time exposure monitoring."""
        self._monitoring_active = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Exposure tracking monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop for exposure tracking."""
        while self._monitoring_active:
            try:
                # Update all position values
                await self._update_position_values()
                
                # Calculate correlations
                await self._calculate_correlations()
                
                # Update concentration metrics
                await self._update_concentration_metrics()
                
                # Generate risk metrics
                await self._calculate_risk_metrics()
                
                # Take periodic snapshots
                await self._take_exposure_snapshot()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                await asyncio.sleep(5)  # 5 second monitoring interval
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in exposure monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def add_position(self, trade: Trade) -> List[ExposurePosition]:
        """
        Add positions from a trade to tracking.
        
        Args:
            trade: Trade to add positions from
            
        Returns:
            List of created exposure positions
        """
        positions = []
        
        for leg in trade.opportunity.legs:
            position = ExposurePosition(
                id=UUID(trade.id.hex + "_" + leg.bookmaker),
                source_type=ExposureType.BOOKMAKER,
                source_value=leg.bookmaker,
                trade_id=trade.id,
                opportunity_id=trade.opportunity.id,
                stake=leg.actual_stake,
                current_value=leg.actual_stake,
                unrealized_pnl='0',
                risk_weight=self._calculate_risk_weight(leg, trade),
                correlation_key=f"bookmaker_{leg.bookmaker}",
                timestamp=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            
            self.active_positions[position.id] = position
            positions.append(position)
        
        # Also add sport-level exposure
        sport_position = ExposurePosition(
            id=UUID(trade.id.hex + "_sport"),
            source_type=ExposureType.SPORT,
            source_value=trade.opportunity.sport.value,
            trade_id=trade.id,
            opportunity_id=trade.opportunity.id,
            stake=trade.stake_data.total_stake,
            current_value=trade.stake_data.total_stake,
            unrealized_pnl='0',
            risk_weight=self._calculate_sport_risk_weight(trade),
            correlation_key=f"sport_{trade.opportunity.sport.value}",
            timestamp=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )
        
        self.active_positions[sport_position.id] = sport_position
        positions.append(sport_position)
        
        logger.info(f"Added {len(positions)} exposure positions for trade {trade.id}")
        return positions
    
    async def remove_position(self, trade_id: UUID) -> List[ExposurePosition]:
        """
        Remove positions for a completed trade.
        
        Args:
            trade_id: ID of trade to remove positions for
            
        Returns:
            List of removed positions
        """
        removed_positions = []
        
        with self._lock:
            # Find all positions for this trade
            positions_to_remove = [
                pos for pos in self.active_positions.values()
                if pos.trade_id == trade_id
            ]
            
            # Remove them
            for position in positions_to_remove:
                removed_positions.append(position)
                del self.active_positions[position.id]
        
        logger.info(f"Removed {len(removed_positions)} exposure positions for trade {trade_id}")
        return removed_positions
    
    async def _update_position_values(self):
        """Update current values of all active positions."""
        with self._lock:
            for position in self.active_positions.values():
                # Get current exposure amount for this position
                current_exposure = await self._get_current_exposure(position)
                
                # Update value
                old_value = position.current_value
                position.current_value = current_exposure
                position.unrealized_pnl = current_exposure - position.stake
                position.last_updated = datetime.utcnow()
                
                # Log significant changes (>10% change)
                if abs(current_exposure - old_value) / max(old_value, '1') > '0.1':
                    logger.debug(f"Position {position.id} value updated: {old_value} -> {current_exposure}")
    
    def _calculate_risk_weight(self, leg: ArbitrageLeg, trade: Trade) -> Decimal:
        """Calculate risk weight for a bookmaker exposure."""
        # Base weight on bookmaker reliability and trade risk tier
        base_weight = '1'
        
        # Adjust for risk tier
        if trade.opportunity.risk_tier == RiskTier.TIER_A:
            base_weight *= '0.8'
        elif trade.opportunity.risk_tier == RiskTier.TIER_B:
            base_weight *= '1.0'
        elif trade.opportunity.risk_tier == RiskTier.TIER_C:
            base_weight *= '1.2'
        elif trade.opportunity.risk_tier == RiskTier.TIER_D:
            base_weight *= '1.5'
        
        # Adjust for profit margin (lower margin = higher risk)
        profit_margin_risk = max('1', '2' - trade.opportunity.profit_margin * 10)
        base_weight *= profit_margin_risk
        
        return base_weight.quantize('0.001')
    
    def _calculate_sport_risk_weight(self, trade: Trade) -> Decimal:
        """Calculate risk weight for sport exposure."""
        # Different sports have different risk profiles
        sport_risk_factors = {
            Sport.FOOTBALL: '1.0',
            Sport.BASKETBALL: '0.9',
            Sport.TENNIS: '0.8',
            Sport.BASEBALL: '1.1',
            Sport.HOCKEY: '1.0',
            Sport.MMA: '1.3',
            Sport.CRICKET: '0.7',
            Sport.RUGBY: '1.1',
            Sport.VOLLEYBALL: '0.8',
            Sport.GOLF: '1.2',
            Sport.BOXING: '1.3',
            Sport.ESPORTS: '1.4',
            Sport.POLITICS: '1.5',
            Sport.ENTERTAINMENT: '1.2'
        }
        
        base_weight = sport_risk_factors.get(trade.opportunity.sport, '1.0')
        
        # Adjust for market type risk
        if trade.opportunity.market_type in ['outright', 'winner']:
            base_weight *= '0.9'
        elif trade.opportunity.market_type in ['over_under', 'handicap']:
            base_weight *= '1.1'
        elif trade.opportunity.market_type in ['prop', 'special']:
            base_weight *= '1.3'
        
        return base_weight.quantize('0.001')
    
    async def _get_current_exposure(self, position: ExposurePosition) -> Decimal:
        """Get current exposure amount for a position."""
        # For bookmaker positions, get actual bookmaker exposure
        if position.source_type == ExposureType.BOOKMAKER:
            # Would implement actual bookmaker exposure calculation
            # For now, return the original stake
            return position.current_value
        
        # For sport positions, sum all bookmaker exposures for that sport
        elif position.source_type == ExposureType.SPORT:
            total_sport_exposure = '0'
            for pos in self.active_positions.values():
                if pos.source_type == ExposureType.BOOKMAKER and pos.source_value == position.source_value:
                    total_sport_exposure += pos.current_value
            return total_sport_exposure
        
        # Default fallback
        return position.current_value
    
    async def _calculate_correlations(self):
        """Calculate correlations between different exposure sources."""
        start_time = datetime.utcnow()
        
        # Group positions by correlation key
        position_groups = defaultdict(list)
        for position in self.active_positions.values():
            if position.correlation_key:
                position_groups[position.correlation_key].append(position)
        
        # Calculate correlations between groups
        correlation_pairs = []
        correlation_keys = list(position_groups.keys())
        
        for i, key_a in enumerate(correlation_keys):
            for key_b in correlation_keys[i+1:]:
                correlation_pairs.append((key_a, key_b))
        
        # Calculate each correlation
        for key_a, key_b in correlation_pairs:
            correlation = await self._calculate_pairwise_correlation(
                position_groups[key_a], position_groups[key_b]
            )
            
            if correlation is not None:
                self.correlation_cache[(key_a, key_b)] = correlation
                self.correlation_cache[(key_b, key_a)] = correlation
        
        # Update metrics
        calculation_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.total_calculations += 1
        self.correlation_updates += 1
        self.average_calculation_time_ms = (
            self.average_calculation_time_ms * (self.total_calculations - 1) + str(calculation_time)
        ) / self.total_calculations
    
    async def _calculate_pairwise_correlation(self, positions_a: List[ExposurePosition],
                                            positions_b: List[ExposurePosition]) -> Optional[RiskCorrelation]:
        """Calculate correlation between two groups of positions."""
        if not positions_a or not positions_b:
            return None
        
        # Get historical data for correlation calculation
        # This is simplified - would need proper time series data
        values_a = [float(pos.current_value) for pos in positions_a]
        values_b = [float(pos.current_value) for pos in positions_b]
        
        if len(values_a) < 2 or len(values_b) < 2:
            return None
        
        try:
            # Calculate Pearson correlation coefficient
            correlation = np.corrcoef(values_a, values_b)[0, 1]
            correlation = str(correlation) if not np.isnan(correlation) else '0'
            
            # Calculate confidence level (simplified)
            sample_size = min(len(values_a), len(values_b))
            confidence = str(min(0.95, sample_size / 20))  # Simplified confidence
            
            is_significant = abs(correlation) > '0.3' and confidence > '0.8'
            
            return RiskCorrelation(
                source_a=positions_a[0].correlation_key,
                source_b=positions_b[0].correlation_key,
                correlation_coefficient=correlation,
                confidence_level=confidence,
                sample_size=sample_size,
                last_updated=datetime.utcnow(),
                is_significant=is_significant
            )
            
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return None
    
    async def _update_concentration_metrics(self):
        """Update concentration metrics for all exposure sources."""
        with self._lock:
            # Calculate total portfolio exposure
            total_exposure = sum(pos.current_value for pos in self.active_positions.values())
            
            if total_exposure <= 0:
                return
            
            # Group exposures by type
            exposures_by_type = defaultdict(Decimal)
            exposures_by_source = defaultdict(Decimal)
            
            for position in self.active_positions.values():
                exposures_by_type[position.source_type] += position.current_value
                exposures_by_source[position.source_value] += position.current_value
            
            # Calculate concentration metrics
            for source_value, exposure in exposures_by_source.items():
                concentration_ratio = exposure / total_exposure
                
                # Determine risk level
                if concentration_ratio > '0.5':
                    risk_level = "critical"
                elif concentration_ratio > '0.3':
                    risk_level = "high"
                elif concentration_ratio > '0.2':
                    risk_level = "medium"
                else:
                    risk_level = "low"
                
                # Calculate percentile rank
                percentile_rank = int((concentration_ratio * 100).quantize('1'))
                
                # Create concentration metric
                metric = ConcentrationMetric(
                    source_type=next(
                        (t for t in ExposureType 
                         if any(pos.source_type == t and pos.source_value == source_value 
                               for pos in self.active_positions.values())),
                        ExposureType.BOOKMAKER
                    ),
                    source_value=source_value,
                    exposure_amount=exposure,
                    concentration_ratio=concentration_ratio,
                    percentile_rank=percentile_rank,
                    is_concentrated=concentration_ratio > self._concentration_threshold,
                    risk_level=risk_level
                )
                
                self.concentration_metrics[source_value] = metric
                
                # Trigger alerts for high concentration
                if concentration_ratio > self._concentration_threshold:
                    await self._trigger_concentration_alert(metric)
    
    async def _trigger_concentration_alert(self, metric: ConcentrationMetric):
        """Trigger alert for high concentration."""
        self.concentration_alerts += 1
        
        alert_message = (
            f"HIGH CONCENTRATION: {metric.source_value} has "
            f"{metric.concentration_ratio:.1%} portfolio concentration "
            f"({metric.risk_level.upper()} risk level)"
        )
        
        logger.warning(alert_message)
    
    async def _calculate_risk_metrics(self):
        """Calculate comprehensive risk metrics."""
        # Calculate Value at Risk (simplified)
        var_95 = await self._calculate_var()
        
        # Calculate maximum drawdown
        max_drawdown = await self._calculate_max_drawdown()
        
        # Calculate diversification ratio
        diversification_ratio = await self._calculate_diversification_ratio()
        
        # Store metrics for current snapshot
        self._current_risk_metrics = {
            RiskMetric.VALUE_AT_RISK: var_95,
            RiskMetric.MAXIMUM_DRAWDOWN: max_drawdown,
            RiskMetric.DIVERSIFICATION_RATIO: diversification_ratio
        }
    
    async def _calculate_var(self) -> Decimal:
        """Calculate Value at Risk at 95% confidence level."""
        # Simplified VaR calculation
        # In practice, would use proper historical simulation or Monte Carlo
        
        # Get historical exposure changes
        changes = []
        if len(self.exposure_history) >= 2:
            for i in range(1, len(self.exposure_history)):
                prev_exposure = self.exposure_history[i-1].total_exposure
                curr_exposure = self.exposure_history[i].total_exposure
                change = curr_exposure - prev_exposure
                changes.append(float(change))
        
        if not changes:
            return '0'
        
        # Calculate 95th percentile loss (VaR)
        sorted_changes = sorted(changes)
        var_index = int(len(sorted_changes) * 0.05)  # 5th percentile
        var_loss = abs(sorted_changes[var_index]) if var_index < len(sorted_changes) else '0'
        
        return str(var_loss).quantize('0.01')
    
    async def _calculate_max_drawdown(self) -> Decimal:
        """Calculate maximum drawdown from historical data."""
        if len(self.exposure_history) < 2:
            return '0'
        
        peak = '0'
        max_drawdown = '0'
        
        for snapshot in self.exposure_history:
            if snapshot.total_exposure > peak:
                peak = snapshot.total_exposure
            
            drawdown = peak - snapshot.total_exposure
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown.quantize('0.01')
    
    async def _calculate_diversification_ratio(self) -> Decimal:
        """Calculate diversification ratio based on concentration."""
        with self._lock:
            if not self.active_positions:
                return '1'
            
            # Calculate Herfindahl-Hirschman Index (HHI)
            total_exposure = sum(pos.current_value for pos in self.active_positions.values())
            
            if total_exposure <= 0:
                return '1'
            
            # Calculate HHI (sum of squared market shares)
            hhi = '0'
            for position in self.active_positions.values():
                market_share = position.current_value / total_exposure
                hhi += market_share * market_share
            
            # Normalize to get diversification ratio (1 - normalized HHI)
            normalized_hhi = hhi  # Already normalized between 0 and 1
            diversification_ratio = '1' - normalized_hhi
            
            return diversification_ratio.quantize('0.001')
    
    async def _take_exposure_snapshot(self):
        """Take a snapshot of current exposure state."""
        with self._lock:
            # Calculate aggregated exposures
            total_exposure = sum(pos.current_value for pos in self.active_positions.values())
            
            exposure_by_type = defaultdict(Decimal)
            exposure_by_source = defaultdict(Decimal)
            
            for position in self.active_positions.values():
                exposure_by_type[position.source_type] += position.current_value
                exposure_by_source[position.source_value] += position.current_value
            
            # Create correlation matrix
            correlation_matrix = {}
            for (source_a, source_b), correlation in self.correlation_cache.items():
                if correlation.is_significant:
                    correlation_matrix[(source_a, source_b)] = correlation.correlation_coefficient
            
            # Get top exposures
            top_exposures = sorted(
                [
                    {
                        "source_value": source,
                        "exposure": float(amount),
                        "concentration": float(amount / total_exposure) if total_exposure > 0 else 0
                    }
                    for source, amount in exposure_by_source.items()
                ],
                key=lambda x: x["exposure"],
                reverse=True
            )[:10]
            
            # Create snapshot
            snapshot = ExposureSnapshot(
                timestamp=datetime.utcnow(),
                total_exposure=total_exposure,
                exposure_by_type=dict(exposure_by_type),
                exposure_by_source=dict(exposure_by_source),
                concentration_metrics={
                    source: {
                        "concentration_ratio": float(metric.concentration_ratio),
                        "risk_level": metric.risk_level,
                        "is_concentrated": metric.is_concentrated
                    }
                    for source, metric in self.concentration_metrics.items()
                },
                correlation_matrix=correlation_matrix,
                risk_metrics=self._current_risk_metrics if hasattr(self, '_current_risk_metrics') else {},
                active_positions=len(self.active_positions),
                top_exposures=top_exposures
            )
            
            self.exposure_history.append(snapshot)
    
    async def _cleanup_old_data(self):
        """Clean up old data to maintain performance."""
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        
        # Remove old correlations
        expired_correlations = [
            key for key, correlation in self.correlation_cache.items()
            if correlation.last_updated < cutoff_time
        ]
        
        for key in expired_correlations:
            del self.correlation_cache[key]
        
        # Clean up concentration metrics for sources with no current exposure
        active_sources = {pos.source_value for pos in self.active_positions.values()}
        expired_metrics = [
            source for source in self.concentration_metrics.keys()
            if source not in active_sources
        ]
        
        for source in expired_metrics:
            del self.concentration_metrics[source]
    
    async def get_exposure_summary(self) -> Dict[str, Any]:
        """Get comprehensive exposure summary."""
        with self._lock:
            total_exposure = sum(pos.current_value for pos in self.active_positions.values())
            
            # Calculate exposure by type
            exposure_by_type = defaultdict(Decimal)
            exposure_by_bookmaker = defaultdict(Decimal)
            exposure_by_sport = defaultdict(Decimal)
            
            for position in self.active_positions.values():
                exposure_by_type[position.source_type.value] += position.current_value
                
                if position.source_type == ExposureType.BOOKMAKER:
                    exposure_by_bookmaker[position.source_value] += position.current_value
                elif position.source_type == ExposureType.SPORT:
                    exposure_by_sport[position.source_value] += position.current_value
            
            # Get top concentrations
            total_exposure_float = float(total_exposure) if total_exposure > 0 else 1
            concentrations = [
                {
                    "source": source,
                    "exposure": float(amount),
                    "concentration": float(amount / total_exposure_float),
                    "risk_level": self.concentration_metrics.get(source, {}).risk_level if source in self.concentration_metrics else "unknown"
                }
                for source, amount in sorted(exposure_by_bookmaker.items(), 
                                           key=lambda x: x[1], reverse=True)[:5]
            ]
            
            # Get risk metrics
            risk_metrics = {}
            if hasattr(self, '_current_risk_metrics'):
                risk_metrics = {
                    metric.value: float(value)
                    for metric, value in self._current_risk_metrics.items()
                }
            
            return {
                "total_exposure": float(total_exposure),
                "active_positions": len(self.active_positions),
                "exposure_by_type": {
                    k.value: float(v) for k, v in exposure_by_type.items()
                },
                "exposure_by_bookmaker": {
                    k: float(v) for k, v in exposure_by_bookmaker.items()
                },
                "exposure_by_sport": {
                    k: float(v) for k, v in exposure_by_sport.items()
                },
                "top_concentrations": concentrations,
                "risk_metrics": risk_metrics,
                "correlation_count": len(self.correlation_cache),
                "concentration_alerts": self.concentration_alerts,
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def get_correlation_matrix(self) -> Dict[str, Any]:
        """Get correlation matrix between different exposure sources."""
        with self._lock:
            # Get unique sources
            sources = set()
            for correlation in self.correlation_cache.values():
                sources.add(correlation.source_a)
                sources.add(correlation.source_b)
            
            sources = sorted(list(sources))
            
            # Build correlation matrix
            matrix = []
            for source_a in sources:
                row = [source_a]
                for source_b in sources:
                    if source_a == source_b:
                        correlation_value = '1.0'
                    else:
                        correlation = self.correlation_cache.get((source_a, source_b))
                        correlation_value = correlation.correlation_coefficient if correlation else '0'
                    
                    row.append(float(correlation_value))
                
                matrix.append(row)
            
            return {
                "sources": sources,
                "correlation_matrix": matrix,
                "significant_correlations": [
                    {
                        "source_a": corr.source_a,
                        "source_b": corr.source_b,
                        "correlation": float(corr.correlation_coefficient),
                        "confidence": float(corr.confidence_level),
                        "is_significant": corr.is_significant
                    }
                    for corr in self.correlation_cache.values()
                    if corr.is_significant
                ],
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def get_concentration_analysis(self) -> Dict[str, Any]:
        """Get detailed concentration analysis."""
        with self._lock:
            total_exposure = sum(pos.current_value for pos in self.active_positions.values())
            
            if total_exposure <= 0:
                return {
                    "total_exposure": 0,
                    "concentration_metrics": [],
                    "concentration_by_type": {},
                    "recommendations": []
                }
            
            # Group by concentration metric
            metrics_by_type = defaultdict(list)
            for source, metric in self.concentration_metrics.items():
                metrics_by_type[metric.source_type.value].append(metric)
            
            # Sort each group by concentration ratio
            sorted_metrics = {}
            for source_type, metrics in metrics_by_type.items():
                sorted_metrics[source_type] = sorted(
                    metrics,
                    key=lambda x: x.concentration_ratio,
                    reverse=True
                )
            
            # Generate recommendations
            recommendations = []
            for source, metric in self.concentration_metrics.items():
                if metric.is_concentrated:
                    if metric.concentration_ratio > '0.5':
                        recommendations.append(
                            f"CRITICAL: {source} has {metric.concentration_ratio:.1%} concentration. "
                            "Immediate diversification required."
                        )
                    elif metric.concentration_ratio > '0.3':
                        recommendations.append(
                            f"HIGH: {source} has {metric.concentration_ratio:.1%} concentration. "
                            "Consider reducing exposure."
                        )
            
            return {
                "total_exposure": float(total_exposure),
                "concentration_metrics": [
                    {
                        "source": metric.source_value,
                        "source_type": metric.source_type.value,
                        "exposure": float(metric.exposure_amount),
                        "concentration_ratio": float(metric.concentration_ratio),
                        "percentile_rank": metric.percentile_rank,
                        "risk_level": metric.risk_level,
                        "is_concentrated": metric.is_concentrated
                    }
                    for metric in sorted_metrics.get("bookmaker", [])
                ],
                "concentration_by_type": {
                    source_type: {
                        "total_exposure": float(sum(m.exposure_amount for m in metrics)),
                        "max_concentration": float(max(m.concentration_ratio for m in metrics)) if metrics else 0,
                        "avg_concentration": float(sum(m.concentration_ratio for m in metrics) / len(metrics)) if metrics else 0,
                        "concentrated_count": sum(1 for m in metrics if m.is_concentrated)
                    }
                    for source_type, metrics in sorted_metrics.items()
                },
                "recommendations": recommendations,
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def calculate_position_sizing(self, proposed_exposure: Decimal, 
                                      source_type: ExposureType, 
                                      source_value: str) -> Dict[str, Any]:
        """
        Calculate optimal position sizing based on risk metrics.
        
        Args:
            proposed_exposure: Proposed exposure amount
            source_type: Type of exposure
            source_value: Source value (bookmaker, sport, etc.)
            
        Returns:
            Dict with sizing recommendations
        """
        with self._lock:
            # Get current exposure for this source
            current_exposure = sum(
                pos.current_value 
                for pos in self.active_positions.values()
                if pos.source_type == source_type and pos.source_value == source_value
            )
            
            new_total_exposure = current_exposure + proposed_exposure
            total_portfolio_exposure = sum(pos.current_value for pos in self.active_positions.values())
            
            # Check concentration limits
            new_concentration = '0'
            if total_portfolio_exposure > 0:
                new_concentration = new_total_exposure / (total_portfolio_exposure + proposed_exposure)
            
            # Get correlation risk
            correlation_risk = '0'
            correlated_exposures = [
                pos.current_value 
                for pos in self.active_positions.values()
                if pos.source_type == source_type and pos.source_value != source_value
            ]
            
            if correlated_exposures:
                # Simplified correlation risk calculation
                correlation_risk = sum(correlated_exposures) / total_portfolio_exposure if total_portfolio_exposure > 0 else '0'
            
            # Calculate recommended sizing
            recommended_size = proposed_exposure
            reasons = []
            
            # Apply concentration limits
            if new_concentration > self._concentration_threshold:
                max_allowed_concentration = self._concentration_threshold
                max_allowed_exposure = (total_portfolio_exposure + proposed_exposure) * max_allowed_concentration
                recommended_size = max('0', max_allowed_exposure - current_exposure)
                reasons.append(f"Concentration limit: reduced from {proposed_exposure} to {recommended_size}")
            
            # Apply correlation limits
            if correlation_risk > '0.4':
                correlation_adjustment = '0.8'  # Reduce by 20%
                adjusted_size = proposed_exposure * correlation_adjustment
                if adjusted_size < recommended_size:
                    recommended_size = adjusted_size
                    reasons.append(f"Correlation risk: reduced by {correlation_adjustment:.1%}")
            
            # Calculate risk-adjusted returns
            if recommended_size > 0:
                risk_adjusted_return = ('0.02' / (correlation_risk + '0.1'))  # Simplified
            else:
                risk_adjusted_return = '0'
            
            return {
                "original_exposure": float(proposed_exposure),
                "recommended_exposure": float(recommended_size),
                "adjustment_reason": reasons,
                "current_exposure": float(current_exposure),
                "new_concentration": float(new_concentration),
                "correlation_risk": float(correlation_risk),
                "risk_adjusted_return": float(risk_adjusted_return),
                "sizing_efficiency": float(recommended_size / proposed_exposure) if proposed_exposure > 0 else 0,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def export_exposure_data(self) -> Dict[str, Any]:
        """Export all exposure tracking data."""
        with self._lock:
            return {
                "active_positions": [
                    {
                        "id": str(pos.id),
                        "source_type": pos.source_type.value,
                        "source_value": pos.source_value,
                        "trade_id": str(pos.trade_id),
                        "stake": str(pos.stake),
                        "current_value": str(pos.current_value),
                        "unrealized_pnl": str(pos.unrealized_pnl),
                        "risk_weight": str(pos.risk_weight),
                        "correlation_key": pos.correlation_key,
                        "timestamp": pos.timestamp.isoformat(),
                        "last_updated": pos.last_updated.isoformat()
                    }
                    for pos in self.active_positions.values()
                ],
                "correlation_cache": [
                    {
                        "source_a": corr.source_a,
                        "source_b": corr.source_b,
                        "correlation_coefficient": str(corr.correlation_coefficient),
                        "confidence_level": str(corr.confidence_level),
                        "sample_size": corr.sample_size,
                        "is_significant": corr.is_significant,
                        "last_updated": corr.last_updated.isoformat()
                    }
                    for corr in self.correlation_cache.values()
                ],
                "concentration_metrics": [
                    {
                        "source_value": metric.source_value,
                        "source_type": metric.source_type.value,
                        "exposure_amount": str(metric.exposure_amount),
                        "concentration_ratio": str(metric.concentration_ratio),
                        "risk_level": metric.risk_level,
                        "is_concentrated": metric.is_concentrated
                    }
                    for metric in self.concentration_metrics.values()
                ],
                "performance_metrics": {
                    "total_calculations": self.total_calculations,
                    "correlation_updates": self.correlation_updates,
                    "concentration_alerts": self.concentration_alerts,
                    "average_calculation_time_ms": float(self.average_calculation_time_ms)
                },
                "export_timestamp": datetime.utcnow().isoformat()
            }
    
    async def shutdown(self):
        """Gracefully shutdown the exposure tracker."""
        logger.info("Shutting down exposure tracker...")
        
        # Stop monitoring
        await self.stop_monitoring()
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        # Log final metrics
        summary = await self.get_exposure_summary()
        logger.info(f"Final exposure summary: {json.dumps(summary, default=str)}")
        
        logger.info("Exposure tracker shutdown complete")