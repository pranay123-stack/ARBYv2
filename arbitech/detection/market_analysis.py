"""
Advanced Market Analysis Module

This module provides sophisticated market analysis including market efficiency assessment,
liquidity analysis, price movement prediction, and market microstructure analysis
for arbitrage betting opportunities.
"""

import math
from typing import List, Dict, Optional, Tuple, Union, Any
from decimal import Decimal, getcontext
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import numpy as np
from collections import deque
import statistics

# Configure decimal precision for financial calculations
getcontext().prec = 50


class MarketEfficiency(Enum):
    """Market efficiency levels."""
    HIGHLY_EFFICIENT = "highly_efficient"
    EFFICIENT = "efficient"
    MODERATELY_EFFICIENT = "moderately_efficient"
    INEFFICIENT = "inefficient"
    HIGHLY_INEFFICIENT = "highly_inefficient"


class LiquidityLevel(Enum):
    """Liquidity levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    VERY_POOR = "very_poor"


class PriceMovementType(Enum):
    """Types of price movements."""
    STABLE = "stable"
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    VOLATILE = "volatile"
    REVERSAL = "reversal"
    BREAKOUT = "breakout"


@dataclass
class MarketDataPoint:
    """Represents a single market data point."""
    timestamp: datetime
    odds: Decimal
    volume: Optional[Decimal] = None
    liquidity: Optional[Decimal] = None
    implied_probability: Optional[Decimal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LiquidityAnalysis:
    """Liquidity analysis results."""
    total_liquidity: Decimal
    average_liquidity: Decimal
    liquidity_volatility: Decimal
    liquidity_level: LiquidityLevel
    spread_analysis: Dict[str, Decimal]
    depth_analysis: Dict[str, Decimal]
    concentration_ratio: Decimal
    liquidity_score: Decimal  # 0-100 scale


@dataclass
class MarketEfficiencyAnalysis:
    """Market efficiency analysis results."""
    efficiency_level: MarketEfficiency
    efficiency_score: Decimal  # 0-100 scale
    arbitrage_frequency: Decimal
    profit_margin_volatility: Decimal
    market_impact_cost: Decimal
    information_ratio: Decimal
    beta_coefficient: Decimal
    alpha_estimate: Decimal
    seasonal_patterns: Dict[str, Decimal]
    behavioral_biases: Dict[str, Decimal]


@dataclass
class PriceMovementPrediction:
    """Price movement prediction results."""
    movement_type: PriceMovementType
    confidence_level: Decimal
    expected_change: Decimal
    time_horizon: timedelta
    volatility_forecast: Decimal
    support_resistance_levels: List[Decimal]
    probability_distribution: Dict[str, Decimal]
    prediction_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketMicrostructure:
    """Market microstructure analysis."""
    bid_ask_spread: Decimal
    effective_spread: Decimal
    price_impact_coefficient: Decimal
    market_depth: Decimal
    order_book_imbalance: Decimal
    velocity_coefficient: Decimal
    resiliency_measure: Decimal


class AdvancedMarketAnalysis:
    """
    Advanced market analysis engine for arbitrage betting.
    
    This class provides sophisticated analysis of betting markets including:
    - Market efficiency assessment
    - Liquidity analysis and measurement
    - Price movement prediction
    - Market microstructure analysis
    - Behavioral pattern recognition
    """
    
    def __init__(self, analysis_window: timedelta = timedelta(hours=24)):
        """
        Initialize the market analysis engine.
        
        Args:
            analysis_window: Time window for market analysis
        """
        self.analysis_window = analysis_window
        self.logger = logging.getLogger(__name__)
        
        # Market data storage
        self._market_data: Dict[str, deque] = {}
        
        # Analysis parameters
        self.default_parameters = {
            'liquidity_threshold_excellent': Decimal('10000'),
            'liquidity_threshold_good': Decimal('5000'),
            'liquidity_threshold_fair': Decimal('1000'),
            'liquidity_threshold_poor': Decimal('100'),
            'efficiency_threshold_high': Decimal('0.95'),
            'efficiency_threshold_moderate': Decimal('0.85'),
            'efficiency_threshold_low': Decimal('0.70'),
            'volatility_threshold_high': Decimal('0.05'),
            'volatility_threshold_moderate': Decimal('0.02'),
            'min_data_points': 10,
            'confidence_intervals': [0.68, 0.95, 0.99]  # 1-sigma, 2-sigma, 3-sigma
        }

    def analyze_market_efficiency(
        self,
        market_id: str,
        odds_history: List[MarketDataPoint],
        arbitrage_opportunities: Optional[List[Dict]] = None
    ) -> MarketEfficiencyAnalysis:
        """
        Analyze market efficiency using multiple metrics.
        
        Args:
            market_id: Unique identifier for the market
            odds_history: Historical odds data
            arbitrage_opportunities: Historical arbitrage opportunities
            
        Returns:
            MarketEfficiencyAnalysis object
        """
        if len(odds_history) < self.default_parameters['min_data_points']:
            self.logger.warning(f"Insufficient data points for {market_id}: {len(odds_history)}")
        
        # Calculate efficiency score
        efficiency_score = self._calculate_efficiency_score(odds_history)
        
        # Determine efficiency level
        efficiency_level = self._determine_efficiency_level(efficiency_score)
        
        # Calculate arbitrage frequency
        arbitrage_frequency = self._calculate_arbitrage_frequency(arbitrage_opportunities, odds_history)
        
        # Calculate profit margin volatility
        profit_margin_volatility = self._calculate_profit_margin_volatility(odds_history)
        
        # Estimate market impact cost
        market_impact_cost = self._estimate_market_impact_cost(odds_history)
        
        # Calculate information ratio
        information_ratio = self._calculate_information_ratio(odds_history)
        
        # Calculate beta and alpha
        beta_coeff, alpha_est = self._calculate_beta_alpha(odds_history)
        
        # Analyze seasonal patterns
        seasonal_patterns = self._analyze_seasonal_patterns(odds_history)
        
        # Identify behavioral biases
        behavioral_biases = self._identify_behavioral_biases(odds_history)
        
        return MarketEfficiencyAnalysis(
            efficiency_level=efficiency_level,
            efficiency_score=efficiency_score,
            arbitrage_frequency=arbitrage_frequency,
            profit_margin_volatility=profit_margin_volatility,
            market_impact_cost=market_impact_cost,
            information_ratio=information_ratio,
            beta_coefficient=beta_coeff,
            alpha_estimate=alpha_est,
            seasonal_patterns=seasonal_patterns,
            behavioral_biases=behavioral_biases
        )

    def analyze_liquidity(
        self,
        market_id: str,
        liquidity_data: List[MarketDataPoint]
    ) -> LiquidityAnalysis:
        """
        Analyze market liquidity using multiple metrics.
        
        Args:
            market_id: Unique identifier for the market
            liquidity_data: Liquidity data over time
            
        Returns:
            LiquidityAnalysis object
        """
        if not liquidity_data:
            raise ValueError("Liquidity data cannot be empty")
        
        # Calculate basic liquidity metrics
        total_liquidity = sum(point.liquidity or Decimal('0') for point in liquidity_data)
        average_liquidity = total_liquidity / len(liquidity_data)
        
        # Calculate liquidity volatility
        liquidity_values = [float(point.liquidity or Decimal('0')) for point in liquidity_data]
        liquidity_volatility = Decimal(str(np.std(liquidity_values))) if len(liquidity_values) > 1 else Decimal('0')
        
        # Determine liquidity level
        liquidity_level = self._determine_liquidity_level(average_liquidity)
        
        # Analyze spread
        spread_analysis = self._analyze_spread(liquidity_data)
        
        # Analyze depth
        depth_analysis = self._analyze_depth(liquidity_data)
        
        # Calculate concentration ratio
        concentration_ratio = self._calculate_concentration_ratio(liquidity_data)
        
        # Calculate liquidity score (0-100)
        liquidity_score = self._calculate_liquidity_score(
            average_liquidity, liquidity_volatility, concentration_ratio
        )
        
        return LiquidityAnalysis(
            total_liquidity=total_liquidity,
            average_liquidity=average_liquidity,
            liquidity_volatility=liquidity_volatility,
            liquidity_level=liquidity_level,
            spread_analysis=spread_analysis,
            depth_analysis=depth_analysis,
            concentration_ratio=concentration_ratio,
            liquidity_score=liquidity_score
        )

    def predict_price_movement(
        self,
        odds_history: List[MarketDataPoint],
        prediction_horizon: timedelta = timedelta(hours=1)
    ) -> PriceMovementPrediction:
        """
        Predict price movements using technical analysis and statistical models.
        
        Args:
            odds_history: Historical odds data
            prediction_horizon: Time horizon for prediction
            
        Returns:
            PriceMovementPrediction object
        """
        if len(odds_history) < 5:
            raise ValueError("Insufficient data for price movement prediction")
        
        # Extract price series
        prices = [point.odds for point in odds_history]
        timestamps = [point.timestamp for point in odds_history]
        
        # Determine movement type
        movement_type = self._classify_price_movement(prices, timestamps)
        
        # Calculate confidence level
        confidence_level = self._calculate_prediction_confidence(odds_history, prediction_horizon)
        
        # Calculate expected change
        expected_change = self._calculate_expected_price_change(prices, timestamps, prediction_horizon)
        
        # Forecast volatility
        volatility_forecast = self._forecast_volatility(odds_history, prediction_horizon)
        
        # Identify support/resistance levels
        support_resistance_levels = self._identify_support_resistance_levels(prices)
        
        # Generate probability distribution
        probability_distribution = self._generate_probability_distribution(
            prices, movement_type, prediction_horizon
        )
        
        return PriceMovementPrediction(
            movement_type=movement_type,
            confidence_level=confidence_level,
            expected_change=expected_change,
            time_horizon=prediction_horizon,
            volatility_forecast=volatility_forecast,
            support_resistance_levels=support_resistance_levels,
            probability_distribution=probability_distribution,
            prediction_metadata={
                'model_type': 'statistical_ensemble',
                'data_points': len(odds_history),
                'prediction_timestamp': datetime.now(),
                'historical_range': {
                    'start': min(timestamps),
                    'end': max(timestamps)
                }
            }
        )

    def analyze_market_microstructure(
        self,
        order_book_data: List[Dict[str, Any]]
    ) -> MarketMicrostructure:
        """
        Analyze market microstructure from order book data.
        
        Args:
            order_book_data: Order book snapshots
            
        Returns:
            MarketMicrostructure object
        """
        if not order_book_data:
            raise ValueError("Order book data cannot be empty")
        
        # Calculate bid-ask spread
        bid_ask_spread = self._calculate_bid_ask_spread(order_book_data)
        
        # Calculate effective spread
        effective_spread = self._calculate_effective_spread(order_book_data)
        
        # Calculate price impact coefficient
        price_impact_coeff = self._calculate_price_impact_coefficient(order_book_data)
        
        # Calculate market depth
        market_depth = self._calculate_market_depth(order_book_data)
        
        # Calculate order book imbalance
        order_book_imbalance = self._calculate_order_book_imbalance(order_book_data)
        
        # Calculate velocity coefficient
        velocity_coeff = self._calculate_velocity_coefficient(order_book_data)
        
        # Calculate resiliency measure
        resiliency_measure = self._calculate_resiliency_measure(order_book_data)
        
        return MarketMicrostructure(
            bid_ask_spread=bid_ask_spread,
            effective_spread=effective_spread,
            price_impact_coefficient=price_impact_coeff,
            market_depth=market_depth,
            order_book_imbalance=order_book_imbalance,
            velocity_coefficient=velocity_coeff,
            resiliency_measure=resiliency_measure
        )

    def detect_market_anomalies(
        self,
        odds_history: List[MarketDataPoint],
        threshold_multiplier: Decimal = Decimal('3')
    ) -> List[Dict[str, Any]]:
        """
        Detect market anomalies using statistical methods.
        
        Args:
            odds_history: Historical odds data
            threshold_multiplier: Standard deviation multiplier for anomaly detection
            
        Returns:
            List of detected anomalies
        """
        if len(odds_history) < 10:
            return []
        
        anomalies = []
        
        # Extract price series
        prices = [float(point.odds) for point in odds_history]
        timestamps = [point.timestamp for point in odds_history]
        
        # Calculate statistics
        price_mean = statistics.mean(prices)
        price_std = statistics.stdev(prices) if len(prices) > 1 else 0
        
        # Detect price jumps (anomalies)
        for i, (price, timestamp) in enumerate(zip(prices, timestamps)):
            z_score = abs(price - price_mean) / price_std if price_std > 0 else 0
            
            if z_score > float(threshold_multiplier):
                anomaly = {
                    'timestamp': timestamp,
                    'type': 'price_jump',
                    'value': price,
                    'z_score': z_score,
                    'severity': 'high' if z_score > 5 else 'medium' if z_score > 3 else 'low',
                    'details': {
                        'mean': price_mean,
                        'std': price_std,
                        'deviation': abs(price - price_mean)
                    }
                }
                anomalies.append(anomaly)
        
        # Detect volume anomalies
        volumes = [float(point.volume or 0) for point in odds_history if point.volume]
        if volumes:
            volume_mean = statistics.mean(volumes)
            volume_std = statistics.stdev(volumes) if len(volumes) > 1 else 0
            
            for i, (volume, point) in enumerate(zip(volumes, odds_history)):
                if point.volume:
                    z_score = abs(volume - volume_mean) / volume_std if volume_std > 0 else 0
                    
                    if z_score > float(threshold_multiplier):
                        anomaly = {
                            'timestamp': point.timestamp,
                            'type': 'volume_spike',
                            'value': volume,
                            'z_score': z_score,
                            'severity': 'high' if z_score > 5 else 'medium' if z_score > 3 else 'low'
                        }
                        anomalies.append(anomaly)
        
        return sorted(anomalies, key=lambda x: x['timestamp'])

    def calculate_market_impact(
        self,
        trade_size: Decimal,
        market_data: List[MarketDataPoint],
        liquidity_data: List[MarketDataPoint]
    ) -> Dict[str, Decimal]:
        """
        Calculate expected market impact for a given trade size.
        
        Args:
            trade_size: Size of the trade
            market_data: Market price data
            liquidity_data: Liquidity data
            
        Returns:
            Dictionary containing market impact metrics
        """
        if not market_data or not liquidity_data:
            raise ValueError("Market data and liquidity data required")
        
        # Get current market state
        current_price = market_data[-1].odds
        current_liquidity = liquidity_data[-1].liquidity or Decimal('0')
        
        # Calculate relative trade size
        relative_size = trade_size / current_liquidity if current_liquidity > 0 else Decimal('1')
        
        # Calculate price impact using empirical models
        # Square root model: Impact ∝ √(Trade Size / Daily Volume)
        daily_volume = sum(point.liquidity or Decimal('0') for point in liquidity_data)
        relative_daily_volume = trade_size / daily_volume if daily_volume > 0 else Decimal('0')
        
        # Impact coefficients (typical values for betting markets)
        temporary_impact_coeff = Decimal('0.01')  # 1% per √(relative size)
        permanent_impact_coeff = Decimal('0.005')  # 0.5% per √(relative size)
        
        # Calculate temporary impact (price pressure)
        sqrt_relative_volume = relative_daily_volume.sqrt()
        temporary_impact = temporary_impact_coeff * sqrt_relative_volume
        
        # Calculate permanent impact (information effect)
        permanent_impact = permanent_impact_coeff * sqrt_relative_volume
        
        # Total expected impact
        total_impact = temporary_impact + permanent_impact
        
        # Calculate impact in price terms
        price_impact_absolute = current_price * total_impact
        
        # Calculate breakeven profit required to overcome impact
        breakeven_profit = trade_size * total_impact
        
        return {
            'trade_size': trade_size,
            'current_price': current_price,
            'current_liquidity': current_liquidity,
            'relative_trade_size': relative_size.quantize(Decimal('0.0001')),
            'temporary_impact': temporary_impact.quantize(Decimal('0.0001')),
            'permanent_impact': permanent_impact.quantize(Decimal('0.0001')),
            'total_impact': total_impact.quantize(Decimal('0.0001')),
            'price_impact_absolute': price_impact_absolute.quantize(Decimal('0.001')),
            'breakeven_profit_required': breakeven_profit.quantize(Decimal('0.01')),
            'impact_percentage': (total_impact * Decimal('100')).quantize(Decimal('0.01'))
        }

    def _calculate_efficiency_score(self, odds_history: List[MarketDataPoint]) -> Decimal:
        """Calculate market efficiency score using various metrics."""
        if len(odds_history) < 2:
            return Decimal('0')
        
        # Extract price series
        prices = [point.odds for point in odds_history]
        
        # Calculate return series
        returns = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(float(ret))
        
        if not returns:
            return Decimal('0')
        
        # Calculate metrics
        # 1. Mean reversion tendency (negative autocorrelation indicates efficiency)
        autocorr = self._calculate_autocorrelation(returns, lag=1)
        mean_reversion_score = max(0, Decimal('1') - abs(Decimal(str(autocorr))))
        
        # 2. Volatility clustering (high clustering indicates inefficiency)
        volatility_series = self._calculate_rolling_volatility(returns, window=5)
        volatility_clustering = np.std(volatility_series) if volatility_series else Decimal('0')
        volatility_score = max(0, Decimal('1') - Decimal(str(volatility_clustering)))
        
        # 3. Information integration speed (price adjustment to new information)
        price_adjustments = []
        for i in range(2, len(prices)):
            adjustment = abs(prices[i] - prices[i-2]) / prices[i-2]
            price_adjustments.append(float(adjustment))
        
        integration_speed = np.mean(price_adjustments) if price_adjustments else 0
        integration_score = min(1, Decimal(str(integration_speed * 10)))  # Normalized
        
        # Combine scores
        efficiency_score = (mean_reversion_score * Decimal('0.4') + 
                          volatility_score * Decimal('0.3') + 
                          integration_score * Decimal('0.3'))
        
        return efficiency_score.quantize(Decimal('0.01'))

    def _calculate_autocorrelation(self, series: List[float], lag: int) -> float:
        """Calculate autocorrelation of a time series."""
        if len(series) <= lag:
            return 0.0
        
        n = len(series) - lag
        if n <= 1:
            return 0.0
        
        mean_series = np.mean(series)
        numerator = sum((series[i] - mean_series) * (series[i + lag] - mean_series) 
                       for i in range(n))
        denominator = sum((x - mean_series) ** 2 for x in series[:n])
        
        return numerator / denominator if denominator != 0 else 0.0

    def _calculate_rolling_volatility(self, returns: List[float], window: int) -> List[float]:
        """Calculate rolling volatility of returns."""
        if len(returns) < window:
            return []
        
        volatilities = []
        for i in range(window - 1, len(returns)):
            window_returns = returns[i - window + 1:i + 1]
            volatility = np.std(window_returns)
            volatilities.append(volatility)
        
        return volatilities

    def _determine_efficiency_level(self, efficiency_score: Decimal) -> MarketEfficiency:
        """Determine market efficiency level from score."""
        if efficiency_score >= self.default_parameters['efficiency_threshold_high']:
            return MarketEfficiency.HIGHLY_EFFICIENT
        elif efficiency_score >= self.default_parameters['efficiency_threshold_moderate']:
            return MarketEfficiency.EFFICIENT
        elif efficiency_score >= self.default_parameters['efficiency_threshold_low']:
            return MarketEfficiency.MODERATELY_EFFICIENT
        elif efficiency_score >= Decimal('0.5'):
            return MarketEfficiency.INEFFICIENT
        else:
            return MarketEfficiency.HIGHLY_INEFFICIENT

    def _calculate_arbitrage_frequency(
        self,
        arbitrage_opportunities: Optional[List[Dict]],
        odds_history: List[MarketDataPoint]
    ) -> Decimal:
        """Calculate frequency of arbitrage opportunities."""
        if not arbitrage_opportunities:
            return Decimal('0')
        
        time_span = (max(point.timestamp for point in odds_history) - 
                    min(point.timestamp for point in odds_history)).total_seconds()
        
        if time_span <= 0:
            return Decimal('0')
        
        frequency_per_second = len(arbitrage_opportunities) / time_span
        frequency_per_hour = frequency_per_second * 3600
        
        return Decimal(str(frequency_per_hour)).quantize(Decimal('0.001'))

    def _calculate_profit_margin_volatility(self, odds_history: List[MarketDataPoint]) -> Decimal:
        """Calculate volatility of profit margins."""
        if len(odds_history) < 2:
            return Decimal('0')
        
        # Calculate implied probabilities
        implied_probs = [Decimal('1') / point.odds for point in odds_history]
        
        # Calculate total implied probabilities over time (assuming 2-way markets)
        total_implied = []
        for i in range(0, len(implied_probs), 2):
            if i + 1 < len(implied_probs):
                total = implied_probs[i] + implied_probs[i + 1]
                total_implied.append(float(total))
        
        if len(total_implied) < 2:
            return Decimal('0')
        
        # Calculate volatility (standard deviation)
        volatility = np.std(total_implied)
        
        return Decimal(str(volatility)).quantize(Decimal('0.0001'))

    def _estimate_market_impact_cost(self, odds_history: List[MarketDataPoint]) -> Decimal:
        """Estimate market impact cost from price movements."""
        if len(odds_history) < 2:
            return Decimal('0')
        
        # Calculate absolute price changes
        price_changes = []
        for i in range(1, len(odds_history)):
            change = abs(odds_history[i].odds - odds_history[i-1].odds)
            price_changes.append(float(change))
        
        if not price_changes:
            return Decimal('0')
        
        # Estimate impact as average absolute change
        avg_change = np.mean(price_changes)
        current_price = float(odds_history[-1].odds)
        
        # Convert to percentage
        impact_percentage = (avg_change / current_price) * 100
        
        return Decimal(str(impact_percentage)).quantize(Decimal('0.0001'))

    def _calculate_information_ratio(self, odds_history: List[MarketDataPoint]) -> Decimal:
        """Calculate information ratio (risk-adjusted return measure)."""
        if len(odds_history) < 2:
            return Decimal('0')
        
        # Calculate returns
        returns = []
        for i in range(1, len(odds_history)):
            ret = (odds_history[i].odds - odds_history[i-1].odds) / odds_history[i-1].odds
            returns.append(float(ret))
        
        if not returns:
            return Decimal('0')
        
        # Calculate mean return and volatility
        mean_return = np.mean(returns)
        volatility = np.std(returns)
        
        if volatility == 0:
            return Decimal('0')
        
        information_ratio = mean_return / volatility
        
        return Decimal(str(information_ratio)).quantize(Decimal('0.0001'))

    def _calculate_beta_alpha(self, odds_history: List[MarketDataPoint]) -> Tuple[Decimal, Decimal]:
        """Calculate beta and alpha coefficients (requires market benchmark)."""
        # Simplified calculation - in practice would need market benchmark
        # For now, use price momentum as proxy for beta
        if len(odds_history) < 2:
            return Decimal('0'), Decimal('0')
        
        # Calculate price momentum
        momentum = (odds_history[-1].odds - odds_history[0].odds) / odds_history[0].odds
        
        # Estimate beta from momentum (simplified)
        beta = Decimal('1') + momentum * Decimal('0.5')  # Conservative estimate
        
        # Alpha is typically small in betting markets
        alpha = momentum * Decimal('0.1')  # Small positive alpha
        
        return beta.quantize(Decimal('0.01')), alpha.quantize(Decimal('0.0001'))

    def _analyze_seasonal_patterns(self, odds_history: List[MarketDataPoint]) -> Dict[str, Decimal]:
        """Analyze seasonal patterns in the data."""
        patterns = {}
        
        if len(odds_history) < 10:
            return patterns
        
        # Group by hour of day
        hourly_prices = {}
        for point in odds_history:
            hour = point.timestamp.hour
            if hour not in hourly_prices:
                hourly_prices[hour] = []
            hourly_prices[hour].append(float(point.odds))
        
        # Calculate hourly averages
        for hour, prices in hourly_prices.items():
            if len(prices) >= 3:  # Minimum data points
                avg_price = np.mean(prices)
                patterns[f'hour_{hour}'] = Decimal(str(avg_price)).quantize(Decimal('0.001'))
        
        return patterns

    def _identify_behavioral_biases(self, odds_history: List[MarketDataPoint]) -> Dict[str, Decimal]:
        """Identify behavioral biases in market pricing."""
        biases = {}
        
        if len(odds_history) < 5:
            return biases
        
        prices = [float(point.odds) for point in odds_history]
        
        # Overreaction bias (excessive price movements)
        overreaction_score = self._calculate_overreaction_score(prices)
        biases['overreaction'] = overreaction_score
        
        # Momentum bias (trending behavior)
        momentum_score = self._calculate_momentum_score(prices)
        biases['momentum'] = momentum_score
        
        # Mean reversion bias (reversion to mean)
        mean_reversion_score = self._calculate_mean_reversion_score(prices)
        biases['mean_reversion'] = mean_reversion_score
        
        return biases

    def _calculate_overreaction_score(self, prices: List[float]) -> Decimal:
        """Calculate overreaction score."""
        if len(prices) < 3:
            return Decimal('0')
        
        # Calculate consecutive price changes
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Look for large consecutive changes in same direction
        overreactions = 0
        for i in range(len(changes) - 1):
            if abs(changes[i]) > 0.02 and abs(changes[i + 1]) > 0.02:  # 2% threshold
                if (changes[i] > 0 and changes[i + 1] > 0) or (changes[i] < 0 and changes[i + 1] < 0):
                    overreactions += 1
        
        score = overreactions / len(changes) if changes else 0
        return Decimal(str(score)).quantize(Decimal('0.01'))

    def _calculate_momentum_score(self, prices: List[float]) -> Decimal:
        """Calculate momentum score."""
        if len(prices) < 3:
            return Decimal('0')
        
        # Calculate directional consistency
        changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        positive_changes = sum(1 for change in changes if change > 0)
        total_changes = len(changes)
        
        momentum_score = abs(positive_changes / total_changes - 0.5) * 2  # 0 to 1 scale
        return Decimal(str(momentum_score)).quantize(Decimal('0.01'))

    def _calculate_mean_reversion_score(self, prices: List[float]) -> Decimal:
        """Calculate mean reversion score."""
        if len(prices) < 5:
            return Decimal('0')
        
        # Calculate autocorrelation with longer lag
        autocorr = self._calculate_autocorrelation(prices, lag=2)
        
        # Negative autocorrelation indicates mean reversion
        mean_reversion_score = max(0, -Decimal(str(autocorr)))
        
        return mean_reversion_score.quantize(Decimal('0.01'))

    # Liquidity analysis methods
    def _determine_liquidity_level(self, avg_liquidity: Decimal) -> LiquidityLevel:
        """Determine liquidity level from average liquidity."""
        if avg_liquidity >= self.default_parameters['liquidity_threshold_excellent']:
            return LiquidityLevel.EXCELLENT
        elif avg_liquidity >= self.default_parameters['liquidity_threshold_good']:
            return LiquidityLevel.GOOD
        elif avg_liquidity >= self.default_parameters['liquidity_threshold_fair']:
            return LiquidityLevel.FAIR
        elif avg_liquidity >= self.default_parameters['liquidity_threshold_poor']:
            return LiquidityLevel.POOR
        else:
            return LiquidityLevel.VERY_POOR

    def _analyze_spread(self, liquidity_data: List[MarketDataPoint]) -> Dict[str, Decimal]:
        """Analyze bid-ask spread characteristics."""
        spreads = []
        
        for point in liquidity_data:
            # Estimate spread from price volatility (proxy)
            if point.metadata.get('spread_estimate'):
                spreads.append(point.metadata['spread_estimate'])
        
        if not spreads:
            return {
                'average_spread': Decimal('0'),
                'spread_volatility': Decimal('0'),
                'spread_skew': Decimal('0')
            }
        
        avg_spread = np.mean(spreads)
        spread_volatility = np.std(spreads)
        
        # Calculate skew (simplified)
        spread_skew = np.mean([s - avg_spread for s in spreads]) / spread_volatility if spread_volatility > 0 else 0
        
        return {
            'average_spread': Decimal(str(avg_spread)).quantize(Decimal('0.0001')),
            'spread_volatility': Decimal(str(spread_volatility)).quantize(Decimal('0.0001')),
            'spread_skew': Decimal(str(spread_skew)).quantize(Decimal('0.01'))
        }

    def _analyze_depth(self, liquidity_data: List[MarketDataPoint]) -> Dict[str, Decimal]:
        """Analyze market depth characteristics."""
        liquidity_values = [float(point.liquidity or Decimal('0')) for point in liquidity_data]
        
        if not liquidity_values:
            return {
                'depth_at_best': Decimal('0'),
                'average_depth': Decimal('0'),
                'depth_volatility': Decimal('0')
            }
        
        avg_depth = np.mean(liquidity_values)
        depth_volatility = np.std(liquidity_values)
        depth_at_best = liquidity_values[-1] if liquidity_values else 0
        
        return {
            'depth_at_best': Decimal(str(depth_at_best)).quantize(Decimal('0.01')),
            'average_depth': Decimal(str(avg_depth)).quantize(Decimal('0.01')),
            'depth_volatility': Decimal(str(depth_volatility)).quantize(Decimal('0.01'))
        }

    def _calculate_concentration_ratio(self, liquidity_data: List[MarketDataPoint]) -> Decimal:
        """Calculate liquidity concentration ratio."""
        liquidity_values = [float(point.liquidity or Decimal('0')) for point in liquidity_data]
        
        if not liquidity_values:
            return Decimal('0')
        
        # Sort in descending order
        sorted_liquidity = sorted(liquidity_values, reverse=True)
        total_liquidity = sum(sorted_liquidity)
        
        if total_liquidity == 0:
            return Decimal('0')
        
        # Calculate concentration ratios for different tiers
        # CR4: Top 4 participants
        cr4 = sum(sorted_liquidity[:4]) / total_liquidity if len(sorted_liquidity) >= 4 else Decimal('1')
        
        return cr4.quantize(Decimal('0.01'))

    def _calculate_liquidity_score(
        self,
        avg_liquidity: Decimal,
        liquidity_volatility: Decimal,
        concentration_ratio: Decimal
    ) -> Decimal:
        """Calculate overall liquidity score (0-100)."""
        # Base score from average liquidity
        liquidity_score = min(100, float(avg_liquidity) / 100)  # Scale liquidity to 0-100
        
        # Adjust for volatility (lower volatility = higher score)
        volatility_penalty = float(liquidity_volatility) * 10  # Penalty factor
        volatility_score = max(0, 100 - volatility_penalty)
        
        # Adjust for concentration (higher concentration = lower score)
        concentration_score = 100 * (1 - float(concentration_ratio))
        
        # Weighted average
        final_score = (
            liquidity_score * 0.5 +
            volatility_score * 0.3 +
            concentration_score * 0.2
        )
        
        return Decimal(str(final_score)).quantize(Decimal('0.1'))

    # Price movement prediction methods
    def _classify_price_movement(self, prices: List[Decimal], timestamps: List[datetime]) -> PriceMovementType:
        """Classify the type of price movement."""
        if len(prices) < 3:
            return PriceMovementType.STABLE
        
        # Calculate price trends
        price_changes = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        # Calculate volatility
        volatility = np.std([float(change) for change in price_changes])
        
        # Classify based on characteristics
        if volatility > float(self.default_parameters['volatility_threshold_high']):
            return PriceMovementType.VOLATILE
        
        # Check for trends
        recent_changes = [float(change) for change in price_changes[-3:]]  # Last 3 changes
        avg_recent_change = np.mean(recent_changes)
        
        if abs(avg_recent_change) > 0.01:  # 1% threshold
            if avg_recent_change > 0:
                return PriceMovementType.TRENDING_UP
            else:
                return PriceMovementType.TRENDING_DOWN
        
        # Check for reversals
        if len(recent_changes) >= 3:
            if (recent_changes[0] > 0 and recent_changes[1] < 0) or (recent_changes[0] < 0 and recent_changes[1] > 0):
                return PriceMovementType.REVERSAL
        
        # Check for breakouts
        price_range = max(prices) - min(prices)
        recent_range = max(recent_changes) - min(recent_changes)
        if recent_range > price_range * 0.5:
            return PriceMovementType.BREAKOUT
        
        return PriceMovementType.STABLE

    def _calculate_prediction_confidence(
        self,
        odds_history: List[MarketDataPoint],
        prediction_horizon: timedelta
    ) -> Decimal:
        """Calculate confidence level for prediction."""
        # Base confidence from data quantity
        data_confidence = min(1.0, len(odds_history) / 50)  # 50 points = 100% confidence
        
        # Adjust for data recency
        time_diff = datetime.now() - odds_history[-1].timestamp
        recency_factor = max(0.5, 1.0 - float(time_diff.total_seconds()) / 86400)  # Decay over 24 hours
        
        # Adjust for prediction horizon (longer horizon = lower confidence)
        horizon_factor = max(0.3, 1.0 - float(prediction_horizon.total_seconds()) / 3600)  # Decay over 1 hour
        
        final_confidence = data_confidence * recency_factor * horizon_factor
        
        return Decimal(str(final_confidence)).quantize(Decimal('0.01'))

    def _calculate_expected_price_change(
        self,
        prices: List[Decimal],
        timestamps: List[datetime],
        prediction_horizon: timedelta
    ) -> Decimal:
        """Calculate expected price change over prediction horizon."""
        if len(prices) < 2:
            return Decimal('0')
        
        # Calculate historical rate of change
        time_diffs = []
        price_changes = []
        
        for i in range(1, len(prices)):
            time_diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600  # Hours
            price_change = (prices[i] - prices[i-1]) / prices[i-1]
            time_diffs.append(time_diff)
            price_changes.append(float(price_change))
        
        # Calculate average rate of change per hour
        rates = [change / diff if diff > 0 else 0 for change, diff in zip(price_changes, time_diffs)]
        avg_rate = np.mean(rates) if rates else 0
        
        # Project forward
        horizon_hours = prediction_horizon.total_seconds() / 3600
        expected_change = avg_rate * horizon_hours
        
        return Decimal(str(expected_change)).quantize(Decimal('0.0001'))

    def _forecast_volatility(
        self,
        odds_history: List[MarketDataPoint],
        prediction_horizon: timedelta
    ) -> Decimal:
        """Forecast volatility over prediction horizon."""
        if len(odds_history) < 2:
            return Decimal('0')
        
        # Calculate historical returns
        returns = []
        for i in range(1, len(odds_history)):
            ret = (odds_history[i].odds - odds_history[i-1].odds) / odds_history[i-1].odds
            returns.append(float(ret))
        
        # Calculate historical volatility
        historical_vol = np.std(returns) if len(returns) > 1 else 0
        
        # Adjust for prediction horizon
        horizon_hours = prediction_horizon.total_seconds() / 3600
        forecast_vol = historical_vol * math.sqrt(horizon_hours / 24)  # Daily to hourly scaling
        
        return Decimal(str(forecast_vol)).quantize(Decimal('0.0001'))

    def _identify_support_resistance_levels(self, prices: List[Decimal]) -> List[Decimal]:
        """Identify support and resistance levels."""
        if len(prices) < 5:
            return []
        
        # Find local minima and maxima
        support_levels = []
        resistance_levels = []
        
        for i in range(2, len(prices) - 2):
            # Check for local minimum (support)
            if (prices[i] < prices[i-1] and prices[i] < prices[i+1] and
                prices[i] < prices[i-2] and prices[i] < prices[i+2]):
                support_levels.append(prices[i])
            
            # Check for local maximum (resistance)
            elif (prices[i] > prices[i-1] and prices[i] > prices[i+1] and
                  prices[i] > prices[i-2] and prices[i] > prices[i+2]):
                resistance_levels.append(prices[i])
        
        # Combine and sort
        levels = support_levels + resistance_levels
        levels.sort()
        
        # Return unique levels (within tolerance)
        unique_levels = []
        tolerance = Decimal('0.01')
        
        for level in levels:
            if not any(abs(level - existing) < tolerance for existing in unique_levels):
                unique_levels.append(level)
        
        return unique_levels[:5]  # Return top 5 levels

    def _generate_probability_distribution(
        self,
        prices: List[Decimal],
        movement_type: PriceMovementType,
        prediction_horizon: timedelta
    ) -> Dict[str, Decimal]:
        """Generate probability distribution for price movements."""
        # Simplified probability distribution based on movement type
        distribution = {}
        
        base_probability = Decimal('0.25')  # Equal probability for 4 outcomes
        
        if movement_type == PriceMovementType.STABLE:
            distribution = {
                'significant_increase': Decimal('0.1'),
                'slight_increase': Decimal('0.2'),
                'no_change': Decimal('0.4'),
                'slight_decrease': Decimal('0.2'),
                'significant_decrease': Decimal('0.1')
            }
        elif movement_type == PriceMovementType.TRENDING_UP:
            distribution = {
                'significant_increase': Decimal('0.3'),
                'slight_increase': Decimal('0.4'),
                'no_change': Decimal('0.15'),
                'slight_decrease': Decimal('0.1'),
                'significant_decrease': Decimal('0.05')
            }
        elif movement_type == PriceMovementType.TRENDING_DOWN:
            distribution = {
                'significant_increase': Decimal('0.05'),
                'slight_increase': Decimal('0.1'),
                'no_change': Decimal('0.15'),
                'slight_decrease': Decimal('0.4'),
                'significant_decrease': Decimal('0.3')
            }
        elif movement_type == PriceMovementType.VOLATILE:
            distribution = {
                'significant_increase': Decimal('0.25'),
                'slight_increase': Decimal('0.25'),
                'no_change': Decimal('0.0'),
                'slight_decrease': Decimal('0.25'),
                'significant_decrease': Decimal('0.25')
            }
        else:
            distribution = {
                'significant_increase': base_probability,
                'slight_increase': base_probability,
                'no_change': base_probability,
                'slight_decrease': base_probability,
                'significant_decrease': base_probability
            }
        
        return distribution

    # Market microstructure methods
    def _calculate_bid_ask_spread(self, order_book_data: List[Dict[str, Any]]) -> Decimal:
        """Calculate average bid-ask spread."""
        spreads = []
        
        for snapshot in order_book_data:
            if 'bids' in snapshot and 'asks' in snapshot:
                best_bid = max(snapshot['bids'], key=lambda x: x['price'])['price']
                best_ask = min(snapshot['asks'], key=lambda x: x['price'])['price']
                spread = best_ask - best_bid
                spreads.append(float(spread))
        
        if not spreads:
            return Decimal('0')
        
        avg_spread = np.mean(spreads)
        return Decimal(str(avg_spread)).quantize(Decimal('0.0001'))

    def _calculate_effective_spread(self, order_book_data: List[Dict[str, Any]]) -> Decimal:
        """Calculate effective spread (transaction cost measure)."""
        # Simplified effective spread calculation
        bid_ask_spread = self._calculate_bid_ask_spread(order_book_data)
        mid_price = self._calculate_mid_price(order_book_data)
        
        if mid_price > 0:
            effective_spread = (bid_ask_spread / mid_price) * Decimal('2')
        else:
            effective_spread = bid_ask_spread
        
        return effective_spread.quantize(Decimal('0.0001'))

    def _calculate_mid_price(self, order_book_data: List[Dict[str, Any]]) -> Decimal:
        """Calculate mid price from order book."""
        mid_prices = []
        
        for snapshot in order_book_data:
            if 'bids' in snapshot and 'asks' in snapshot:
                best_bid = max(snapshot['bids'], key=lambda x: x['price'])['price']
                best_ask = min(snapshot['asks'], key=lambda x: x['price'])['price']
                mid_price = (best_bid + best_ask) / 2
                mid_prices.append(float(mid_price))
        
        if not mid_prices:
            return Decimal('0')
        
        avg_mid_price = np.mean(mid_prices)
        return Decimal(str(avg_mid_price)).quantize(Decimal('0.001'))

    def _calculate_price_impact_coefficient(self, order_book_data: List[Dict[str, Any]]) -> Decimal:
        """Calculate price impact coefficient."""
        # Simplified calculation based on order book depth
        depth_values = []
        
        for snapshot in order_book_data:
            if 'total_depth' in snapshot:
                depth_values.append(snapshot['total_depth'])
        
        if not depth_values:
            return Decimal('0.01')  # Default coefficient
        
        avg_depth = np.mean(depth_values)
        
        # Inverse relationship: higher depth = lower impact
        impact_coeff = Decimal('1') / Decimal(str(avg_depth + 1))
        
        return impact_coeff.quantize(Decimal('0.0001'))

    def _calculate_market_depth(self, order_book_data: List[Dict[str, Any]]) -> Decimal:
        """Calculate market depth."""
        depths = []
        
        for snapshot in order_book_data:
            if 'total_depth' in snapshot:
                depths.append(snapshot['total_depth'])
        
        if not depths:
            return Decimal('0')
        
        avg_depth = np.mean(depths)
        return Decimal(str(avg_depth)).quantize(Decimal('0.01'))

    def _calculate_order_book_imbalance(self, order_book_data: List[Dict[str, Any]]) -> Decimal:
        """Calculate order book imbalance."""
        imbalances = []
        
        for snapshot in order_book_data:
            if 'bids' in snapshot and 'asks' in snapshot:
                bid_volume = sum(bid['quantity'] for bid in snapshot['bids'])
                ask_volume = sum(ask['quantity'] for ask in snapshot['asks'])
                
                total_volume = bid_volume + ask_volume
                if total_volume > 0:
                    imbalance = abs(bid_volume - ask_volume) / total_volume
                    imbalances.append(imbalance)
        
        if not imbalances:
            return Decimal('0')
        
        avg_imbalance = np.mean(imbalances)
        return Decimal(str(avg_imbalance)).quantize(Decimal('0.01'))

    def _calculate_velocity_coefficient(self, order_book_data: List[Dict[str, Any]]) -> Decimal:
        """Calculate order book velocity coefficient."""
        # Simplified velocity calculation based on order book changes
        if len(order_book_data) < 2:
            return Decimal('0.1')
        
        velocity_measurements = []
        
        for i in range(1, len(order_book_data)):
            current_depth = order_book_data[i].get('total_depth', 0)
            previous_depth = order_book_data[i-1].get('total_depth', 0)
            
            if previous_depth > 0:
                velocity = abs(current_depth - previous_depth) / previous_depth
                velocity_measurements.append(velocity)
        
        if not velocity_measurements:
            return Decimal('0.1')
        
        avg_velocity = np.mean(velocity_measurements)
        return Decimal(str(avg_velocity)).quantize(Decimal('0.0001'))

    def _calculate_resiliency_measure(self, order_book_data: List[Dict[str, Any]]) -> Decimal:
        """Calculate market resiliency measure."""
        # Simplified resiliency as inverse of volatility in depth
        if len(order_book_data) < 3:
            return Decimal('0.5')
        
        depths = [snapshot.get('total_depth', 0) for snapshot in order_book_data]
        
        # Calculate depth volatility
        depth_volatility = np.std(depths) if len(depths) > 1 else 0
        avg_depth = np.mean(depths)
        
        if avg_depth > 0:
            # Higher relative volatility = lower resiliency
            resiliency = Decimal('1') / (Decimal('1') + Decimal(str(depth_volatility / avg_depth)))
        else:
            resiliency = Decimal('0')
        
        return resiliency.quantize(Decimal('0.01'))


def create_market_analyzer(analysis_window: timedelta = timedelta(hours=24)) -> AdvancedMarketAnalysis:
    """
    Factory function to create and configure a market analyzer.
    
    Args:
        analysis_window: Time window for analysis
        
    Returns:
        Configured AdvancedMarketAnalysis instance
    """
    return AdvancedMarketAnalysis(analysis_window=analysis_window)