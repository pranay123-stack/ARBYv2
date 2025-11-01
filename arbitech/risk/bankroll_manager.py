"""
Advanced Bankroll Management System

This module provides comprehensive bankroll management with growth modeling, drawdown protection,
capital preservation strategies, and detailed performance tracking for arbitrage betting operations.
"""

import math
from typing import List, Dict, Optional, Tuple, Union, Callable, NamedTuple
from decimal import Decimal, getcontext
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import json
import warnings
import logging

# Configure decimal precision for financial calculations
getcontext().prec = 50


class BankrollStrategy(Enum):
    """Types of bankroll management strategies."""
    FLAT_BETTING = "flat_betting"
    FIXED_FRACTION = "fixed_fraction"
    KELLY_CRITERION = "kelly_criterion"
    FRACTIONAL_KELLY = "fractional_kelly"
    DYNAMIC_KELLY = "dynamic_kelly"
    RISK_PARITY = "risk_parity"
    CONSTANT_RISK = "constant_risk"
    ANTI_MARTINGALE = "anti_martingale"
    PYRAMIDING = "pyramiding"
    CUSTOM = "custom"


class DrawdownPhase(Enum):
    """Drawdown protection phases."""
    NORMAL = "normal"
    CAUTION = "caution"
    DEFENSIVE = "defensive"
    CRISIS = "crisis"
    EMERGENCY = "emergency"
    RECOVERY = "recovery"


class CapitalPreservationMode(Enum):
    """Capital preservation modes."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    EMERGENCY = "emergency"


@dataclass
class BankrollConfig:
    """Configuration for bankroll management."""
    strategy: BankrollStrategy = BankrollStrategy.KELLY_CRITERION
    
    # Bankroll limits
    initial_bankroll: Decimal = '10000'
    minimum_bankroll: Decimal = '1000'
    maximum_bankroll: Decimal = '1000000'
    
    # Position sizing
    base_fraction: Decimal = '0.02'  # 2% base fraction
    kelly_fraction: Decimal = '0.25'  # Fractional Kelly multiplier
    max_position_fraction: Decimal = '0.05'  # 5% max position
    
    # Drawdown protection
    drawdown_levels: List[Decimal] = field(default_factory=lambda: [
        '0.05',  # 5% - Caution
        '0.10',  # 10% - Defensive
        '0.15',  # 15% - Crisis
        '0.20'   # 20% - Emergency
    ])
    protection_factors: List[Decimal] = field(default_factory=lambda: [
        '0.8',   # Reduce position sizes by 20%
        '0.6',   # Reduce position sizes by 40%
        '0.4',   # Reduce position sizes by 60%
        '0.2'    # Reduce position sizes by 80%
    ])
    
    # Performance thresholds
    win_rate_threshold: Decimal = '0.55'
    profit_factor_threshold: Decimal = '1.2'
    sharpe_ratio_threshold: Decimal = '1.0'
    
    # Rebalancing
    rebalancing_frequency: int = 10  # Rebalance every N trades
    performance_lookback: int = 50   # Performance calculation window
    
    # Capital preservation
    preservation_mode: CapitalPreservationMode = CapitalPreservationMode.MODERATE
    emergency_stop_loss: Decimal = '0.25'  # 25% stop loss
    capital_preservation_threshold: Decimal = '0.1'  # 10% drawdown
    
    # Advanced settings
    dynamic_adjustment: bool = True
    volatility_adjustment: bool = True
    correlation_adjustment: bool = True
    time_decay_factor: Decimal = '0.95'


@dataclass
class GrowthModel:
    """Bankroll growth model and projections."""
    current_bankroll: Decimal
    expected_growth_rate: Decimal
    volatility: Decimal
    projected_values: List[Decimal]
    confidence_intervals: List[Tuple[Decimal, Decimal]]
    doubling_time: Decimal
    risk_adjusted_return: Decimal
    maximum_drawdown_estimate: Decimal
    
    def get_projection(self, time_period: int) -> Decimal:
        """Get bankroll projection for specific time period."""
        if time_period < len(self.projected_values):
            return self.projected_values[time_period]
        
        # Extrapolate if beyond calculated range
        growth_rate = float(self.expected_growth_rate)
        current_value = float(self.current_bankroll)
        projected = current_value * (1 + growth_rate) ** time_period
        
        return str(projected)
    
    def get_confidence_bounds(self, time_period: int, confidence: Decimal = '0.95') -> Tuple[Decimal, Decimal]:
        """Get confidence bounds for projection."""
        if time_period < len(self.confidence_intervals):
            return self.confidence_intervals[time_period]
        
        # Extrapolate confidence bounds
        z_score = 1.96 if confidence >= '0.95' else 1.645
        growth_rate = float(self.expected_growth_rate)
        volatility = float(self.volatility)
        
        current_value = float(self.current_bankroll)
        mean_projection = current_value * (1 + growth_rate) ** time_period
        
        # Add volatility adjustment
        vol_adjustment = z_score * volatility * math.sqrt(time_period)
        lower_bound = mean_projection * (1 - vol_adjustment)
        upper_bound = mean_projection * (1 + vol_adjustment)
        
        return (
            str(max(0, lower_bound)),
            str(upper_bound)
        )


@dataclass
class DrawdownProtection:
    """Drawdown protection system."""
    current_phase: DrawdownPhase
    current_drawdown: Decimal
    peak_bankroll: Decimal
    protection_active: bool
    reduction_factor: Decimal
    recovery_progress: Decimal
    days_in_drawdown: int
    auto_recovery_enabled: bool
    
    def get_position_size_multiplier(self) -> Decimal:
        """Get multiplier for position sizes based on drawdown phase."""
        phase_multipliers = {
            DrawdownPhase.NORMAL: '1.0',
            DrawdownPhase.CAUTION: '0.8',
            DrawdownPhase.DEFENSIVE: '0.6',
            DrawdownPhase.CRISIS: '0.4',
            DrawdownPhase.EMERGENCY: '0.2'
        }
        
        return phase_multipliers.get(self.current_phase, '1.0')
    
    def should_activate_protection(self, current_drawdown: Decimal) -> bool:
        """Check if drawdown protection should be activated."""
        return current_drawdown > '0.05'  # 5% threshold
    
    def calculate_recovery_needed(self, current_bankroll: Decimal) -> Decimal:
        """Calculate recovery needed to exit drawdown."""
        if self.peak_bankroll <= 0:
            return '0'
        
        return self.peak_bankroll - current_bankroll


@dataclass
class PerformanceTracker:
    """Performance tracking and metrics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_profit_loss: Decimal
    win_rate: Decimal
    average_win: Decimal
    average_loss: Decimal
    profit_factor: Decimal
    largest_win: Decimal
    largest_loss: Decimal
    consecutive_wins: int
    consecutive_losses: int
    current_streak: int
    sharpe_ratio: Decimal
    sortino_ratio: Decimal
    calmar_ratio: Decimal
    maximum_drawdown: Decimal
    current_drawdown: Decimal
    recovery_factor: Decimal
    
    def update_with_trade(self, won: bool, profit_loss: Decimal):
        """Update metrics with new trade."""
        self.total_trades += 1
        
        if won:
            self.winning_trades += 1
            self.total_profit_loss += profit_loss
            self.consecutive_wins += 1
            self.consecutive_losses = 0
            self.current_streak = self.consecutive_wins
            
            if profit_loss > self.largest_win:
                self.largest_win = profit_loss
        else:
            self.losing_trades += 1
            self.total_profit_loss += profit_loss  # profit_loss is negative for losses
            self.consecutive_losses += 1
            self.consecutive_wins = 0
            self.current_streak = -self.consecutive_losses
            
            if profit_loss < self.largest_loss:  # More negative
                self.largest_loss = profit_loss
        
        # Recalculate metrics
        self._recalculate_metrics()
    
    def _recalculate_metrics(self):
        """Recalculate all performance metrics."""
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
        else:
            self.win_rate = '0'
        
        if self.winning_trades > 0:
            self.average_win = self.total_profit_loss / self.winning_trades if self.total_profit_loss > 0 else '0'
        else:
            self.average_win = '0'
        
        if self.losing_trades > 0:
            self.average_loss = self.total_profit_loss / self.losing_trades if self.total_profit_loss < 0 else '0'
        else:
            self.average_loss = '0'
        
        # Profit factor
        total_wins = sum(1 for _ in range(self.winning_trades))  # Simplified
        total_losses = sum(1 for _ in range(self.losing_trades))  # Simplified
        
        if total_losses > 0 and self.average_loss != 0:
            self.profit_factor = abs(self.average_win / self.average_loss)
        else:
            self.profit_factor = 'inf' if self.winning_trades > 0 else '0'
        
        # Recovery factor
        if self.maximum_drawdown > 0:
            self.recovery_factor = self.total_profit_loss / self.maximum_drawdown
        else:
            self.recovery_factor = '0'


@dataclass
class CapitalPreservation:
    """Capital preservation system."""
    mode: CapitalPreservationMode
    emergency_fund_ratio: Decimal
    stop_loss_active: bool
    preservation_threshold: Decimal
    capital_at_risk: Decimal
    emergency_bankroll: Decimal
    
    def should_preserve_capital(self, drawdown: Decimal, win_rate: Decimal) -> bool:
        """Determine if capital preservation should be activated."""
        if self.mode == CapitalPreservationMode.EMERGENCY:
            return drawdown > self.preservation_threshold
        
        elif self.mode == CapitalPreservationMode.CONSERVATIVE:
            return drawdown > self.preservation_threshold * '0.5' or win_rate < '0.5'
        
        elif self.mode == CapitalPreservationMode.MODERATE:
            return drawdown > self.preservation_threshold or win_rate < '0.45'
        
        else:  # AGGRESSIVE
            return drawdown > self.preservation_threshold * '1.5'
    
    def get_preservation_ratio(self) -> Decimal:
        """Get ratio of bankroll to preserve based on mode."""
        ratios = {
            CapitalPreservationMode.CONSERVATIVE: '0.8',  # Preserve 80%
            CapitalPreservationMode.MODERATE: '0.6',     # Preserve 60%
            CapitalPreservationMode.AGGRESSIVE: '0.4',   # Preserve 40%
            CapitalPreservationMode.EMERGENCY: '0.9'     # Preserve 90%
        }
        
        return ratios.get(self.mode, '0.6')


class BankrollManager:
    """
    Advanced Bankroll Management System
    
    Provides comprehensive bankroll management with:
    - Multiple bankroll strategies
    - Dynamic growth modeling
    - Sophisticated drawdown protection
    - Capital preservation mechanisms
    - Real-time performance tracking
    - Risk-adjusted position sizing
    """
    
    def __init__(self, config: BankrollConfig = None):
        """Initialize bankroll manager with configuration."""
        self.config = config or BankrollConfig()
        self.logger = self._setup_logger()
        
        # Current state
        self.current_bankroll = self.config.initial_bankroll
        self.peak_bankroll = self.config.initial_bankroll
        self.trade_history = []
        self.bankroll_history = [self.config.initial_bankroll]
        
        # Components
        self.drawdown_protection = self._initialize_drawdown_protection()
        self.performance_tracker = self._initialize_performance_tracker()
        self.capital_preservation = self._initialize_capital_preservation()
        self.growth_model = None
        
        # Tracking
        self._last_rebalance = 0
        self._drawdown_start_date = None
        
    def calculate_position_size(
        self,
        opportunity: Dict[str, Union[str, Decimal, Decimal, Decimal]],
        market_conditions: Dict[str, Decimal] = None
    ) -> Decimal:
        """
        Calculate position size based on current bankroll and strategy.
        
        Args:
            opportunity: Betting opportunity details
            market_conditions: Current market conditions
            
        Returns:
            Recommended position size
        """
        market_conditions = market_conditions or {}
        
        # Validate inputs
        self._validate_opportunity(opportunity)
        
        # Calculate base size using strategy
        if self.config.strategy == BankrollStrategy.FLAT_BETTING:
            size = self._calculate_flat_betting_size(opportunity)
        elif self.config.strategy == BankrollStrategy.FIXED_FRACTION:
            size = self._calculate_fixed_fraction_size(opportunity)
        elif self.config.strategy == BankrollStrategy.KELLY_CRITERION:
            size = self._calculate_kelly_size(opportunity)
        elif self.config.strategy == BankrollStrategy.FRACTIONAL_KELLY:
            size = self._calculate_fractional_kelly_size(opportunity)
        elif self.config.strategy == BankrollStrategy.DYNAMIC_KELLY:
            size = self._calculate_dynamic_kelly_size(opportunity, market_conditions)
        elif self.config.strategy == BankrollStrategy.RISK_PARITY:
            size = self._calculate_risk_parity_size(opportunity)
        elif self.config.strategy == BankrollStrategy.CONSTANT_RISK:
            size = self._calculate_constant_risk_size(opportunity)
        elif self.config.strategy == BankrollStrategy.ANTI_MARTINGALE:
            size = self._calculate_anti_martingale_size(opportunity)
        elif self.config.strategy == BankrollStrategy.PYRAMIDING:
            size = self._calculate_pyramiding_size(opportunity)
        else:
            size = self._calculate_fixed_fraction_size(opportunity)
        
        # Apply drawdown protection
        size = self._apply_drawdown_protection(size)
        
        # Apply capital preservation
        size = self._apply_capital_preservation(size)
        
        # Apply volatility adjustments
        if self.config.volatility_adjustment:
            size = self._apply_volatility_adjustment(size, opportunity, market_conditions)
        
        # Apply correlation adjustments
        if self.config.correlation_adjustment:
            size = self._apply_correlation_adjustment(size, opportunity)
        
        # Ensure size is within bounds
        size = self._validate_position_size(size)
        
        return size
    
    def update_bankroll(self, trade_result: Dict[str, Union[bool, Decimal, datetime]]):
        """
        Update bankroll after completing a trade.
        
        Args:
            trade_result: Trade result with outcome and profit/loss
        """
        # Extract trade information
        won = trade_result.get('won', False)
        profit_loss = str(trade_result.get('profit_loss', '0'))
        timestamp = trade_result.get('timestamp', datetime.now())
        opportunity_id = trade_result.get('opportunity_id', 'unknown')
        
        # Update bankroll
        old_bankroll = self.current_bankroll
        self.current_bankroll += profit_loss
        
        # Update peak bankroll
        if self.current_bankroll > self.peak_bankroll:
            self.peak_bankroll = self.current_bankroll
        
        # Update history
        self.bankroll_history.append(self.current_bankroll)
        self.trade_history.append({
            'timestamp': timestamp,
            'opportunity_id': opportunity_id,
            'won': won,
            'profit_loss': profit_loss,
            'bankroll_before': old_bankroll,
            'bankroll_after': self.current_bankroll
        })
        
        # Update drawdown protection
        self._update_drawdown_protection()
        
        # Update performance tracker
        self.performance_tracker.update_with_trade(won, profit_loss)
        
        # Update capital preservation
        self._update_capital_preservation()
        
        # Update growth model
        self._update_growth_model()
        
        # Check for emergency stop loss
        self._check_emergency_stop_loss()
        
        # Log update
        self.logger.info(f"Trade completed: {opportunity_id}, Won: {won}, P&L: {profit_loss:.4f}, "
                        f"Bankroll: {self.current_bankroll:.4f}")
    
    def generate_performance_report(self) -> Dict[str, Union[str, Decimal, List, Dict]]:
        """
        Generate comprehensive performance report.
        
        Returns:
            Dictionary with detailed performance metrics
        """
        current_drawdown = self._calculate_current_drawdown()
        days_active = (datetime.now() - self.trade_history[0]['timestamp']).days if self.trade_history else 0
        
        report = {
            'summary': {
                'current_bankroll': self.current_bankroll,
                'initial_bankroll': self.config.initial_bankroll,
                'total_return': (self.current_bankroll - self.config.initial_bankroll) / self.config.initial_bankroll,
                'total_trades': self.performance_tracker.total_trades,
                'days_active': days_active
            },
            'performance_metrics': {
                'win_rate': self.performance_tracker.win_rate,
                'profit_factor': self.performance_tracker.profit_factor,
                'sharpe_ratio': self.performance_tracker.sharpe_ratio,
                'sortino_ratio': self.performance_tracker.sortino_ratio,
                'calmar_ratio': self.performance_tracker.calmar_ratio,
                'largest_win': self.performance_tracker.largest_win,
                'largest_loss': self.performance_tracker.largest_loss,
                'average_win': self.performance_tracker.average_win,
                'average_loss': self.performance_tracker.average_loss
            },
            'risk_metrics': {
                'current_drawdown': current_drawdown,
                'maximum_drawdown': self.performance_tracker.maximum_drawdown,
                'recovery_factor': self.performance_tracker.recovery_factor,
                'volatility': self._calculate_volatility(),
                'var_95': self._calculate_var('0.95')
            },
            'drawdown_analysis': {
                'current_phase': self.drawdown_protection.current_phase.value,
                'protection_active': self.drawdown_protection.protection_active,
                'days_in_drawdown': self.drawdown_protection.days_in_drawdown,
                'recovery_progress': self.drawdown_protection.recovery_progress
            },
            'capital_preservation': {
                'mode': self.capital_preservation.mode.value,
                'stop_loss_active': self.capital_preservation.stop_loss_active,
                'emergency_fund_ratio': self.capital_preservation.emergency_fund_ratio,
                'capital_at_risk': self.capital_preservation.capital_at_risk
            },
            'growth_projections': {
                'expected_growth_rate': self.growth_model.expected_growth_rate if self.growth_model else '0',
                'doubling_time': self.growth_model.doubling_time if self.growth_model else '0',
                'projected_30_days': self.growth_model.get_projection(30) if self.growth_model else self.current_bankroll,
                'projected_90_days': self.growth_model.get_projection(90) if self.growth_model else self.current_bankroll,
                'projected_365_days': self.growth_model.get_projection(365) if self.growth_model else self.current_bankroll
            },
            'strategy_status': {
                'current_strategy': self.config.strategy.value,
                'performance_vs_threshold': self._evaluate_strategy_performance(),
                'rebalancing_due': self._is_rebalancing_due(),
                'next_rebalance': self._get_next_rebalance_date()
            }
        }
        
        return report
    
    def simulate_growth_scenarios(
        self,
        scenarios: List[Dict[str, Union[str, Decimal]]],
        time_horizon: int = 365
    ) -> Dict[str, List[Decimal]]:
        """
        Simulate bankroll growth under different scenarios.
        
        Args:
            scenarios: List of scenarios with probability, win_rate, avg_odds
            time_horizon: Number of days to simulate
            
        Returns:
            Dictionary with simulation results for each scenario
        """
        simulation_results = {}
        
        for scenario in scenarios:
            scenario_name = scenario.get('name', 'unknown')
            scenario_prob = str(scenario.get('probability', '0'))
            scenario_win_rate = str(scenario.get('win_rate', '0.5'))
            scenario_avg_odds = str(scenario.get('avg_odds', '2.0'))
            
            # Run Monte Carlo simulation
            bankroll_path = self._run_growth_simulation(
                scenario_prob, scenario_win_rate, scenario_avg_odds, time_horizon
            )
            
            simulation_results[scenario_name] = bankroll_path
        
        return simulation_results
    
    def get_rebalancing_recommendations(self) -> Dict[str, Union[str, List, Decimal]]:
        """
        Get recommendations for bankroll rebalancing.
        
        Returns:
            Dictionary with rebalancing recommendations
        """
        recommendations = {
            'rebalancing_due': self._is_rebalancing_due(),
            'current_strategy_performance': self._evaluate_strategy_performance(),
            'recommended_adjustments': [],
            'risk_warnings': [],
            'optimization_suggestions': []
        }
        
        # Check if rebalancing is needed
        if recommendations['rebalancing_due']:
            recommendations['recommended_adjustments'].append(
                "Rebalance bankroll allocation based on recent performance"
            )
        
        # Performance-based recommendations
        if self.performance_tracker.win_rate < self.config.win_rate_threshold:
            recommendations['risk_warnings'].append(
                f"Win rate {self.performance_tracker.win_rate:.1%} below threshold {self.config.win_rate_threshold:.1%}"
            )
        
        if self.performance_tracker.profit_factor < self.config.profit_factor_threshold:
            recommendations['risk_warnings'].append(
                f"Profit factor {self.performance_tracker.profit_factor:.2f} below threshold {self.config.profit_factor_threshold:.2f}"
            )
        
        # Strategy optimization suggestions
        if self.config.strategy == BankrollStrategy.KELLY_CRITERION:
            if self.drawdown_protection.current_phase != DrawdownPhase.NORMAL:
                recommendations['optimization_suggestions'].append(
                    "Consider switching to fractional Kelly during drawdown periods"
                )
        
        # Drawdown-specific recommendations
        if self.drawdown_protection.current_drawdown > '0.1':  # 10%
            recommendations['optimization_suggestions'].append(
                "Reduce position sizes and focus on higher confidence opportunities"
            )
        
        recommendations['next_rebalance'] = self._get_next_rebalance_date()
        
        return recommendations
    
    def export_performance_data(self, file_path: str = None) -> str:
        """
        Export detailed performance data to JSON file.
        
        Args:
            file_path: Path to save the file (optional)
            
        Returns:
            JSON string with performance data
        """
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'version': '1.0',
                'configuration': {
                    'strategy': self.config.strategy.value,
                    'initial_bankroll': str(self.config.initial_bankroll),
                    'kelly_fraction': str(self.config.kelly_fraction),
                    'drawdown_levels': [str(level) for level in self.config.drawdown_levels]
                }
            },
            'bankroll_history': [str(bankroll) for bankroll in self.bankroll_history],
            'trade_history': [
                {
                    'timestamp': trade['timestamp'].isoformat(),
                    'opportunity_id': trade['opportunity_id'],
                    'won': trade['won'],
                    'profit_loss': str(trade['profit_loss']),
                    'bankroll_before': str(trade['bankroll_before']),
                    'bankroll_after': str(trade['bankroll_after'])
                }
                for trade in self.trade_history
            ],
            'performance_report': self.generate_performance_report(),
            'current_state': {
                'current_bankroll': str(self.current_bankroll),
                'peak_bankroll': str(self.peak_bankroll),
                'drawdown_phase': self.drawdown_protection.current_phase.value,
                'protection_active': self.drawdown_protection.protection_active
            }
        }
        
        json_data = json.dumps(export_data, indent=2, default=str)
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(json_data)
        
        return json_data
    
    # Private helper methods
    
    def _setup_logger(self):
        """Setup logging for the bankroll manager."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        return logger
    
    def _initialize_drawdown_protection(self) -> DrawdownProtection:
        """Initialize drawdown protection system."""
        return DrawdownProtection(
            current_phase=DrawdownPhase.NORMAL,
            current_drawdown='0',
            peak_bankroll=self.config.initial_bankroll,
            protection_active=False,
            reduction_factor='1',
            recovery_progress='0',
            days_in_drawdown=0,
            auto_recovery_enabled=True
        )
    
    def _initialize_performance_tracker(self) -> PerformanceTracker:
        """Initialize performance tracker."""
        return PerformanceTracker(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            total_profit_loss='0',
            win_rate='0',
            average_win='0',
            average_loss='0',
            profit_factor='0',
            largest_win='0',
            largest_loss='0',
            consecutive_wins=0,
            consecutive_losses=0,
            current_streak=0,
            sharpe_ratio='0',
            sortino_ratio='0',
            calmar_ratio='0',
            maximum_drawdown='0',
            current_drawdown='0',
            recovery_factor='0'
        )
    
    def _initialize_capital_preservation(self) -> CapitalPreservation:
        """Initialize capital preservation system."""
        emergency_fund_ratio = '0.1'  # 10% emergency fund
        
        return CapitalPreservation(
            mode=self.config.preservation_mode,
            emergency_fund_ratio=emergency_fund_ratio,
            stop_loss_active=False,
            preservation_threshold=self.config.capital_preservation_threshold,
            capital_at_risk='0',
            emergency_bankroll=self.config.initial_bankroll * emergency_fund_ratio
        )
    
    def _validate_opportunity(self, opportunity: Dict):
        """Validate opportunity data."""
        required_keys = ['win_probability', 'odds']
        if not all(key in opportunity for key in required_keys):
            raise ValueError("Opportunity must have win_probability and odds")
    
    def _calculate_flat_betting_size(self, opportunity: Dict) -> Decimal:
        """Calculate flat betting size."""
        return self.current_bankroll * self.config.base_fraction
    
    def _calculate_fixed_fraction_size(self, opportunity: Dict) -> Decimal:
        """Calculate fixed fraction size."""
        return self.current_bankroll * self.config.base_fraction
    
    def _calculate_kelly_size(self, opportunity: Dict) -> Decimal:
        """Calculate Kelly optimal size."""
        win_prob = str(opportunity['win_probability'])
        odds = str(opportunity['odds'])
        
        if odds <= '1':
            return '0'
        
        b = odds - '1'
        kelly_fraction = (b * win_prob - ('1' - win_prob)) / b
        kelly_fraction = max(kelly_fraction, '0')
        
        return self.current_bankroll * min(kelly_fraction, self.config.max_position_fraction)
    
    def _calculate_fractional_kelly_size(self, opportunity: Dict) -> Decimal:
        """Calculate fractional Kelly size."""
        kelly_size = self._calculate_kelly_size(opportunity)
        return kelly_size * self.config.kelly_fraction
    
    def _calculate_dynamic_kelly_size(self, opportunity: Dict, market_conditions: Dict) -> Decimal:
        """Calculate dynamic Kelly size with adjustments."""
        base_kelly = self._calculate_fractional_kelly_size(opportunity)
        
        # Apply market condition adjustments
        adjustments = []
        
        # Volatility adjustment
        if 'market_volatility' in market_conditions:
            vol_adj = '1' / ('1' + market_conditions['market_volatility'])
            adjustments.append(('volatility', vol_adj))
            base_kelly *= vol_adj
        
        # Liquidity adjustment
        if 'liquidity' in market_conditions:
            liq_adj = min(market_conditions['liquidity'], '1')
            adjustments.append(('liquidity', liq_adj))
            base_kelly *= liq_adj
        
        # Confidence adjustment
        confidence = str(opportunity.get('confidence', '1'))
        base_kelly *= confidence
        
        return base_kelly
    
    def _calculate_risk_parity_size(self, opportunity: Dict) -> Decimal:
        """Calculate risk parity size."""
        # Simplified risk parity - equal risk contribution
        win_prob = str(opportunity['win_probability'])
        odds = str(opportunity['odds'])
        
        # Calculate risk (variance)
        variance = win_prob * (odds - 1) ** 2 + (1 - win_prob)
        risk = math.sqrt(float(variance))
        
        # Inverse relationship with risk
        base_allocation = self.current_bankroll * self.config.max_position_fraction
        risk_adjusted = base_allocation / str(max(risk, 0.1))
        
        return min(risk_adjusted, self.current_bankroll * self.config.max_position_fraction)
    
    def _calculate_constant_risk_size(self, opportunity: Dict) -> Decimal:
        """Calculate constant risk size."""
        # Maintain constant risk amount regardless of odds
        target_risk = self.current_bankroll * self.config.base_fraction
        
        win_prob = str(opportunity['win_probability'])
        odds = str(opportunity['odds'])
        
        # Calculate position size to maintain constant risk
        expected_loss = ('1' - win_prob)
        size = target_risk / expected_loss
        
        return min(size, self.current_bankroll * self.config.max_position_fraction)
    
    def _calculate_anti_martingale_size(self, opportunity: Dict) -> Decimal:
        """Calculate anti-martingale position size."""
        # Increase size after wins, decrease after losses
        base_size = self.current_bankroll * self.config.base_fraction
        
        # Adjust based on current streak
        streak_multiplier = '1'
        if self.performance_tracker.current_streak > 0:
            # Winning streak - increase size
            streak_multiplier = '1' + (str(self.performance_tracker.current_streak) * '0.1')
        elif self.performance_tracker.current_streak < 0:
            # Losing streak - decrease size
            streak_multiplier = '1' - (str(abs(self.performance_tracker.current_streak)) * '0.05')
        
        return base_size * min(streak_multiplier, '2')  # Cap at 2x
    
    def _calculate_pyramiding_size(self, opportunity: Dict) -> Decimal:
        """Calculate pyramiding position size."""
        # Increase size as bankroll grows
        growth_factor = self.current_bankroll / self.config.initial_bankroll
        base_size = self.current_bankroll * self.config.base_fraction
        
        # Scale with growth but with diminishing returns
        pyramid_multiplier = '1' + math.log(float(growth_factor)) * '0.5'
        
        return base_size * min(pyramid_multiplier, '3')  # Cap at 3x
    
    def _apply_drawdown_protection(self, size: Decimal) -> Decimal:
        """Apply drawdown protection to position size."""
        multiplier = self.drawdown_protection.get_position_size_multiplier()
        protected_size = size * multiplier
        
        # Update protection status
        if self.drawdown_protection.should_activate_protection(self.drawdown_protection.current_drawdown):
            self.drawdown_protection.protection_active = True
        else:
            self.drawdown_protection.protection_active = False
        
        return protected_size
    
    def _apply_capital_preservation(self, size: Decimal) -> Decimal:
        """Apply capital preservation constraints."""
        # Check if capital preservation should be active
        should_preserve = self.capital_preservation.should_preserve_capital(
            self.drawdown_protection.current_drawdown,
            self.performance_tracker.win_rate
        )
        
        if should_preserve:
            # Reduce available bankroll for betting
            preservation_ratio = self.capital_preservation.get_preservation_ratio()
            available_bankroll = self.current_bankroll * ('1' - preservation_ratio)
            preserved_size = min(size, available_bankroll * self.config.base_fraction)
            
            self.capital_preservation.capital_at_risk = preserved_size
            return preserved_size
        
        return size
    
    def _apply_volatility_adjustment(
        self,
        size: Decimal,
        opportunity: Dict,
        market_conditions: Dict
    ) -> Decimal:
        """Apply volatility adjustment to position size."""
        # Calculate implied volatility from opportunity
        win_prob = str(opportunity['win_probability'])
        odds = str(opportunity['odds'])
        
        variance = win_prob * (odds - 1) ** 2 + (1 - win_prob)
        volatility = math.sqrt(float(variance))
        
        # Volatility adjustment (inverse relationship)
        vol_adjustment = '1' / ('1' + volatility)
        
        # Market volatility adjustment
        if 'market_volatility' in market_conditions:
            market_vol_adj = '1' / ('1' + market_conditions['market_volatility'])
            vol_adjustment *= market_vol_adj
        
        return size * vol_adjustment
    
    def _apply_correlation_adjustment(self, size: Decimal, opportunity: Dict) -> Decimal:
        """Apply correlation adjustment to position size."""
        # Simplified correlation adjustment
        # In practice, would calculate correlation with existing positions
        
        correlation_penalty = '0'  # Placeholder
        
        # Check for market concentration
        current_positions = len([t for t in self.trade_history if t['timestamp'].date() == datetime.now().date()])
        if current_positions > 5:  # More than 5 positions today
            correlation_penalty = '0.1'
        
        return size * ('1' - correlation_penalty)
    
    def _validate_position_size(self, size: Decimal) -> Decimal:
        """Validate final position size."""
        # Ensure size is positive
        if size <= 0:
            return '0'
        
        # Ensure size doesn't exceed bankroll
        if size > self.current_bankroll:
            return self.current_bankroll * self.config.max_position_fraction
        
        # Ensure size doesn't exceed maximum position fraction
        max_size = self.current_bankroll * self.config.max_position_fraction
        if size > max_size:
            return max_size
        
        # Ensure size doesn't go below minimum
        min_size = self.current_bankroll * '0.001'  # 0.1%
        if size < min_size:
            return '0'
        
        return size
    
    def _update_drawdown_protection(self):
        """Update drawdown protection system."""
        current_drawdown = self._calculate_current_drawdown()
        
        self.drawdown_protection.current_drawdown = current_drawdown
        
        # Determine drawdown phase
        if current_drawdown <= self.config.drawdown_levels[0]:
            phase = DrawdownPhase.NORMAL
        elif current_drawdown <= self.config.drawdown_levels[1]:
            phase = DrawdownPhase.CAUTION
        elif current_drawdown <= self.config.drawdown_levels[2]:
            phase = DrawdownPhase.DEFENSIVE
        elif current_drawdown <= self.config.drawdown_levels[3]:
            phase = DrawdownPhase.CRISIS
        else:
            phase = DrawdownPhase.EMERGENCY
        
        self.drawdown_protection.current_phase = phase
        
        # Update protection factors
        if phase != DrawdownPhase.NORMAL:
            level_index = min(int(current_drawdown / '0.05'), len(self.config.protection_factors) - 1)
            self.drawdown_protection.reduction_factor = self.config.protection_factors[level_index]
        
        # Update drawdown tracking
        if current_drawdown > '0.01':  # 1% threshold
            if self._drawdown_start_date is None:
                self._drawdown_start_date = datetime.now()
            self.drawdown_protection.days_in_drawdown = (datetime.now() - self._drawdown_start_date).days
        
        # Calculate recovery progress
        if self.peak_bankroll > self.current_bankroll:
            recovery_needed = self.peak_bankroll - self.current_bankroll
            recovery_progress = (self.peak_bankroll - self.current_bankroll) / self.peak_bankroll
            self.drawdown_protection.recovery_progress = '1' - recovery_progress
    
    def _update_capital_preservation(self):
        """Update capital preservation system."""
        current_drawdown = self.drawdown_protection.current_drawdown
        
        # Update capital at risk
        total_risk = sum(
            abs(trade['profit_loss']) for trade in self.trade_history[-10:] if trade['profit_loss'] < 0
        )
        self.capital_preservation.capital_at_risk = total_risk
        
        # Check for emergency stop loss
        if current_drawdown >= self.config.emergency_stop_loss:
            self.capital_preservation.stop_loss_active = True
        else:
            self.capital_preservation.stop_loss_active = False
    
    def _update_growth_model(self):
        """Update growth model with current data."""
        if len(self.bankroll_history) < 2:
            return
        
        # Calculate recent returns
        recent_returns = []
        for i in range(1, min(len(self.bankroll_history), 21)):  # Last 20 returns
            prev_bankroll = self.bankroll_history[-i-1]
            curr_bankroll = self.bankroll_history[-i]
            
            if prev_bankroll > 0:
                return_rate = (curr_bankroll - prev_bankroll) / prev_bankroll
                recent_returns.append(float(return_rate))
        
        if not recent_returns:
            return
        
        # Calculate growth metrics
        mean_return = np.mean(recent_returns)
        volatility = np.std(recent_returns)
        
        # Estimate growth rate (annualized)
        if len(self.bankroll_history) > 365:
            # Use full history
            total_return = float((self.current_bankroll - self.config.initial_bankroll) / self.config.initial_bankroll)
            days_active = (datetime.now() - self.trade_history[0]['timestamp']).days
            annual_growth = (1 + total_return) ** (365 / max(days_active, 1)) - 1
        else:
            # Use recent performance
            annual_growth = mean_return * 252  # Assuming daily data
        
        # Create growth model
        self.growth_model = GrowthModel(
            current_bankroll=self.current_bankroll,
            expected_growth_rate=str(annual_growth),
            volatility=str(volatility),
            projected_values=self._generate_projections(),
            confidence_intervals=self._generate_confidence_intervals(),
            doubling_time=str(math.log(2 / max(annual_growth, 0.001))),
            risk_adjusted_return=str(mean_return / max(volatility, 0.001)),
            maximum_drawdown_estimate=self._estimate_max_drawdown()
        )
    
    def _check_emergency_stop_loss(self):
        """Check if emergency stop loss should be triggered."""
        current_drawdown = self.drawdown_protection.current_drawdown
        
        if current_drawdown >= self.config.emergency_stop_loss:
            self.logger.critical(
                f"EMERGENCY STOP LOSS TRIGGERED: Drawdown {current_drawdown:.1%} exceeds "
                f"threshold {self.config.emergency_stop_loss:.1%}"
            )
            
            # Force conservative position sizing
            self.config.strategy = BankrollStrategy.FLAT_BETTING
            self.config.base_fraction = '0.005'  # Very small positions
            self.config.preservation_mode = CapitalPreservationMode.EMERGENCY
    
    def _calculate_current_drawdown(self) -> Decimal:
        """Calculate current drawdown from peak."""
        if self.peak_bankroll <= 0:
            return '0'
        
        return (self.peak_bankroll - self.current_bankroll) / self.peak_bankroll
    
    def _calculate_volatility(self) -> Decimal:
        """Calculate bankroll volatility."""
        if len(self.bankroll_history) < 2:
            return '0'
        
        returns = []
        for i in range(1, len(self.bankroll_history)):
            prev_bankroll = self.bankroll_history[i-1]
            curr_bankroll = self.bankroll_history[i]
            
            if prev_bankroll > 0:
                return_rate = float((curr_bankroll - prev_bankroll) / prev_bankroll)
                returns.append(return_rate)
        
        if not returns:
            return '0'
        
        return str(np.std(returns))
    
    def _calculate_var(self, confidence: Decimal) -> Decimal:
        """Calculate Value at Risk."""
        volatility = self._calculate_volatility()
        
        # Use normal distribution approximation
        if confidence == '0.95':
            z_score = 1.645
        elif confidence == '0.99':
            z_score = 2.33
        else:
            z_score = 1.96  # Default for 95%
        
        return z_score * volatility * self.current_bankroll
    
    def _evaluate_strategy_performance(self) -> str:
        """Evaluate current strategy performance."""
        if self.performance_tracker.win_rate >= self.config.win_rate_threshold and \
           self.performance_tracker.profit_factor >= self.config.profit_factor_threshold:
            return "excellent"
        elif self.performance_tracker.win_rate >= self.config.win_rate_threshold * '0.9':
            return "good"
        elif self.performance_tracker.win_rate >= self.config.win_rate_threshold * '0.8':
            return "acceptable"
        else:
            return "poor"
    
    def _is_rebalancing_due(self) -> bool:
        """Check if rebalancing is due."""
        return (self.performance_tracker.total_trades - self._last_rebalance) >= self.config.rebalancing_frequency
    
    def _get_next_rebalance_date(self) -> datetime:
        """Get next rebalancing date."""
        trades_since_rebalance = self.performance_tracker.total_trades - self._last_rebalance
        trades_needed = self.config.rebalancing_frequency - trades_since_rebalance
        
        # Estimate trades per day (simplified)
        if self.trade_history:
            days_active = (datetime.now() - self.trade_history[0]['timestamp']).days
            trades_per_day = self.performance_tracker.total_trades / max(days_active, 1)
            days_to_rebalance = trades_needed / max(trades_per_day, 1)
        else:
            days_to_rebalance = self.config.rebalancing_frequency / 10  # Default assumption
        
        return datetime.now() + timedelta(days=days_to_rebalance)
    
    def _generate_projections(self) -> List[Decimal]:
        """Generate bankroll projections."""
        projections = []
        current_value = float(self.current_bankroll)
        
        for days in [7, 14, 30, 60, 90, 180, 365]:
            if self.growth_model:
                growth_rate = float(self.growth_model.expected_growth_rate)
                projected = current_value * (1 + growth_rate) ** (days / 365)
            else:
                projected = current_value
            
            projections.append(str(projected))
        
        return projections
    
    def _generate_confidence_intervals(self) -> List[Tuple[Decimal, Decimal]]:
        """Generate confidence intervals for projections."""
        if not self.growth_model:
            return []
        
        intervals = []
        volatility = float(self.growth_model.volatility)
        growth_rate = float(self.growth_model.expected_growth_rate)
        
        for days in [7, 14, 30, 60, 90, 180, 365]:
            z_score = 1.96  # 95% confidence
            current_value = float(self.current_bankroll)
            
            mean_projection = current_value * (1 + growth_rate) ** (days / 365)
            vol_adjustment = z_score * volatility * math.sqrt(days / 365)
            
            lower = mean_projection * (1 - vol_adjustment)
            upper = mean_projection * (1 + vol_adjustment)
            
            intervals.append((
                str(max(0, lower)),
                str(upper)
            ))
        
        return intervals
    
    def _estimate_max_drawdown(self) -> Decimal:
        """Estimate maximum drawdown based on volatility."""
        volatility = self._calculate_volatility()
        
        # Conservative estimate: 3x volatility
        estimated_max_dd = volatility * '3'
        
        return min(estimated_max_dd, '0.5')  # Cap at 50%
    
    def _run_growth_simulation(
        self,
        probability: Decimal,
        win_rate: Decimal,
        avg_odds: Decimal,
        time_horizon: int
    ) -> List[Decimal]:
        """Run Monte Carlo growth simulation."""
        bankroll_path = [float(self.current_bankroll)]
        current_bankroll = float(self.current_bankroll)
        
        for day in range(time_horizon):
            # Simulate daily trades (assume 5 trades per day average)
            daily_trades = 5
            daily_pnl = 0
            
            for trade in range(daily_trades):
                # Determine if trade wins
                won = np.random.random() < float(win_rate)
                
                # Calculate trade result
                if won:
                    # Calculate Kelly-optimal stake
                    b = float(avg_odds) - 1
                    kelly_f = (b * float(probability) - (1 - float(probability))) / b
                    kelly_f = max(0, kelly_f)  # Ensure non-negative
                    
                    stake = current_bankroll * kelly_f * 0.25  # Fractional Kelly
                    pnl = stake * (float(avg_odds) - 1)
                else:
                    stake = current_bankroll * 0.02  # Fixed fraction
                    pnl = -stake
                
                daily_pnl += pnl
            
            current_bankroll += daily_pnl
            bankroll_path.append(current_bankroll)
        
        return [str(value) for value in bankroll_path]
    
    def reset_bankroll(self, new_bankroll: Decimal = None):
        """Reset bankroll to initial state."""
        if new_bankroll is None:
            new_bankroll = self.config.initial_bankroll
        
        self.current_bankroll = new_bankroll
        self.peak_bankroll = new_bankroll
        self.trade_history.clear()
        self.bankroll_history = [new_bankroll]
        
        # Reset components
        self.drawdown_protection = self._initialize_drawdown_protection()
        self.performance_tracker = self._initialize_performance_tracker()
        self.capital_preservation = self._initialize_capital_preservation()
        self.growth_model = None
        
        self._last_rebalance = 0
        self._drawdown_start_date = None
        
        self.logger.info(f"Bankroll reset to {new_bankroll}")
    
    def get_current_state(self) -> Dict[str, Union[str, Decimal, bool]]:
        """Get current bankroll management state."""
        return {
            'current_bankroll': self.current_bankroll,
            'peak_bankroll': self.peak_bankroll,
            'strategy': self.config.strategy.value,
            'drawdown_phase': self.drawdown_protection.current_phase.value,
            'drawdown_percentage': self.drawdown_protection.current_drawdown,
            'protection_active': self.drawdown_protection.protection_active,
            'total_trades': self.performance_tracker.total_trades,
            'win_rate': self.performance_tracker.win_rate,
            'profit_factor': self.performance_tracker.profit_factor,
            'emergency_stop': self.capital_preservation.stop_loss_active
        }