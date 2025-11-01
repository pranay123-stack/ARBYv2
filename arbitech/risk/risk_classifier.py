"""
Risk Classifier for Arbitrage Trading System

This module provides the main risk classification engine with multi-dimensional risk analysis
including market volatility assessment, bookmaker reliability scoring, liquidity depth analysis,
execution difficulty assessment, timing sensitivity analysis, confidence scoring, and
uncertainty quantification.

The classifier integrates with the ArbitrageOpportunity model from Phase 1 and uses
mathematical models from Phase 3 to provide sophisticated risk tier classification.
"""

import math
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from typing import List, Dict, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import deque, defaultdict
import json
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN

# Configure decimal precision
getcontext().prec = 50

from storage.models import ArbitrageOpportunity, ArbitrageLeg
from tier_definitions import (
    TierDefinition, RiskTierCriteria, MarketCondition, ConfidenceLevel,
    get_tier_definition, get_all_tier_definitions, calculate_composite_risk_score
)
from risk_calculator import RiskCalculator, VolatilityModel


class RiskComponent(str, Enum):
    """Risk assessment components."""
    MARKET_VOLATILITY = "market_volatility"
    BOOKMAKER_RELIABILITY = "bookmaker_reliability"
    LIQUIDITY_DEPTH = "liquidity_depth"
    EXECUTION_DIFFICULTY = "execution_difficulty"
    TIMING_SENSITIVITY = "timing_sensitivity"
    ODDS_STABILITY = "odds_stability"
    DIVERSIFICATION = "diversification"
    CORRELATION_RISK = "correlation_risk"


class RiskFactor(str, Enum):
    """Individual risk factors."""
    PROFIT_MARGIN = "profit_margin"
    LIQUIDITY_SCORE = "liquidity_score"
    BOOKMAKER_RATING = "bookmaker_rating"
    EXECUTION_TIME = "execution_time"
    ODDS_DEVIATION = "odds_deviation"
    VOLATILITY_SCORE = "volatility_score"
    CONFIDENCE_LEVEL = "confidence_level"
    MARKET_IMPACT = "market_impact"
    CORRELATION_COEF = "correlation_coefficient"
    TIME_TO_EVENT = "time_to_event"


@dataclass
class RiskComponentScore:
    """Individual risk component score."""
    component: RiskComponent
    score: Decimal  # 0.0 (high risk) to 1.0 (low risk)
    weight: Decimal
    confidence: Decimal
    factors: Dict[RiskFactor, Decimal]
    explanation: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RiskFactorAnalysis:
    """Detailed analysis of individual risk factors."""
    factor: RiskFactor
    value: Decimal
    normalized_score: Decimal
    percentile_rank: Decimal
    trend_direction: str  # "increasing", "decreasing", "stable"
    volatility: Decimal
    confidence_interval: Tuple[Decimal, Decimal]
    benchmark_comparison: Optional[Decimal] = None


@dataclass
class RiskClassificationResult:
    """Comprehensive risk classification result."""
    # Core classification
    opportunity_id: str
    assigned_tier: str  # tier_a, tier_b, tier_c, tier_d
    composite_risk_score: Decimal  # 0.0 to 1.0 (higher = more risky)
    confidence_score: Decimal  # 0.0 to 1.0
    
    # Component breakdown
    component_scores: List[RiskComponentScore]
    risk_factor_analysis: Dict[RiskFactor, RiskFactorAnalysis]
    
    # Detailed metrics
    profitability_analysis: Dict[str, Decimal]
    liquidity_analysis: Dict[str, Decimal]
    execution_analysis: Dict[str, Decimal]
    timing_analysis: Dict[str, Decimal]
    market_analysis: Dict[str, Decimal]
    
    # Tier validation
    tier_criteria_met: Dict[str, bool]
    tier_violations: List[str]
    recommendations: List[str]
    
    # Uncertainty quantification
    model_uncertainty: Decimal
    data_uncertainty: Decimal
    market_uncertainty: Decimal
    total_uncertainty: Decimal
    
    # Additional metadata
    classification_timestamp: datetime = field(default_factory=datetime.utcnow)
    classification_version: str = "1.0.0"
    calculation_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketVolatilityMetrics:
    """Market volatility assessment metrics."""
    historical_volatility: Decimal
    implied_volatility: Decimal
    volatility_rank: Decimal
    volatility_trend: str
    regime_classification: MarketCondition
    volatility_percentile: Decimal
    correlation_volatility: Decimal
    tail_risk_indicator: Decimal


@dataclass
class BookmakerReliabilityMetrics:
    """Bookmaker reliability assessment metrics."""
    reliability_score: Decimal
    rating_score: Decimal
    execution_success_rate: Decimal
    cancellation_rate: Decimal
    settlement_accuracy: Decimal
    support_quality: Decimal
    regulatory_compliance: Decimal
    financial_stability: Decimal


@dataclass
class LiquidityDepthMetrics:
    """Liquidity depth assessment metrics."""
    market_depth: Decimal
    bid_ask_spread: Decimal
    market_impact_factor: Decimal
    fill_probability: Decimal
    slippage_estimate: Decimal
    market_concentration: Decimal
    liquidity_regime: str


class MarketVolatilityAnalyzer:
    """Advanced market volatility analysis engine."""
    
    def __init__(self, risk_calculator: RiskCalculator):
        self.risk_calculator = risk_calculator
        self.logger = logging.getLogger(__name__)
        self.volatility_cache = {}
        self.regime_classifier = None
        
    def analyze_market_volatility(
        self,
        returns: List[Decimal],
        market_data: Optional[Dict[str, Any]] = None,
        time_horizon: timedelta = timedelta(days=30)
    ) -> MarketVolatilityMetrics:
        """
        Perform comprehensive market volatility analysis.
        
        Args:
            returns: Historical market returns
            market_data: Additional market context data
            time_horizon: Analysis time horizon
            
        Returns:
            MarketVolatilityMetrics with comprehensive volatility assessment
        """
        if len(returns) < 30:
            raise ValueError("Insufficient data for volatility analysis")
        
        # Calculate historical volatility using multiple models
        volatility_models = [VolatilityModel.HISTORICAL, VolatilityModel.EWMA, VolatilityModel.GARCH]
        volatilities = {}
        
        for model in volatility_models:
            try:
                forecast = self.risk_calculator.calculate_volatility(returns, model=model)
                volatilities[model] = forecast.forecasted_volatility
            except Exception as e:
                self.logger.warning(f"Failed to calculate volatility for {model}: {e}")
                volatilities[model] = '0.2'  # Default assumption
        
        # Use historical volatility as primary metric
        historical_vol = volatilities.get(VolatilityModel.HISTORICAL, '0.2')
        
        # Implied volatility (if market data available)
        implied_vol = self._estimate_implied_volatility(market_data, historical_vol)
        
        # Volatility ranking and trend analysis
        volatility_rank = self._calculate_volatility_rank(returns)
        volatility_trend = self._analyze_volatility_trend(returns)
        
        # Market regime classification
        regime_classification = self._classify_volatility_regime(returns, historical_vol)
        
        # Volatility percentile calculation
        volatility_percentile = self._calculate_volatility_percentile(returns)
        
        # Correlation volatility (volatility of volatility)
        correlation_vol = self._calculate_volatility_of_volatility(returns)
        
        # Tail risk indicator
        tail_risk_indicator = self._calculate_tail_risk_indicator(returns)
        
        return MarketVolatilityMetrics(
            historical_volatility=historical_vol,
            implied_volatility=implied_vol,
            volatility_rank=volatility_rank,
            volatility_trend=volatility_trend,
            regime_classification=regime_classification,
            volatility_percentile=volatility_percentile,
            correlation_volatility=correlation_vol,
            tail_risk_indicator=tail_risk_indicator
        )
    
    def _estimate_implied_volatility(
        self, 
        market_data: Optional[Dict[str, Any]], 
        historical_vol: Decimal
    ) -> Decimal:
        """Estimate implied volatility from market data."""
        if not market_data:
            # Fallback to historical vol adjusted for current conditions
            return historical_vol * '1.1'  # Slight upward adjustment
        
        # Extract implied vol indicators from market data
        bid_ask_spread = market_data.get('bid_ask_spread', '0.01')
        order_book_depth = market_data.get('order_book_depth', '1000')
        recent_price_moves = market_data.get('recent_price_moves', [])
        
        # Adjust based on market stress indicators
        stress_multiplier = '1.0'
        
        if bid_ask_spread > '0.02':  # Wide spreads indicate stress
            stress_multiplier *= '1.2'
        
        if order_book_depth < '500':  # Shallow order books
            stress_multiplier *= '1.15'
        
        if len(recent_price_moves) > 0:
            recent_volatility = np.std([float(x) for x in recent_price_moves[-10:]])
            if recent_volatility > float(historical_vol) * 1.5:
                stress_multiplier *= '1.25'
        
        return historical_vol * stress_multiplier
    
    def _calculate_volatility_rank(self, returns: List[Decimal]) -> Decimal:
        """Calculate volatility rank relative to historical periods."""
        returns_array = np.array([float(r) for r in returns])
        
        # Calculate rolling volatilities
        rolling_vol = []
        window = 21  # 3 weeks
        for i in range(window, len(returns_array)):
            vol = np.std(returns_array[i-window:i], ddof=1)
            rolling_vol.append(vol)
        
        if not rolling_vol:
            return '0.5'
        
        current_vol = rolling_vol[-1]
        volatility_percentile = stats.percentileofscore(rolling_vol, current_vol)
        
        return str(volatility_percentile / 100.0)
    
    def _analyze_volatility_trend(self, returns: List[Decimal]) -> str:
        """Analyze volatility trend direction."""
        if len(returns) < 42:  # Need at least 6 weeks of data
            return "stable"
        
        returns_array = np.array([float(r) for r in returns])
        
        # Calculate recent vs historical volatility
        recent_vol = np.std(returns_array[-21:], ddof=1)
        historical_vol = np.std(returns_array[:-21], ddof=1)
        
        ratio = recent_vol / historical_vol if historical_vol > 0 else 1.0
        
        if ratio > 1.3:
            return "increasing"
        elif ratio < 0.7:
            return "decreasing"
        else:
            return "stable"
    
    def _classify_volatility_regime(
        self, 
        returns: List[Decimal], 
        current_vol: Decimal
    ) -> MarketCondition:
        """Classify current market volatility regime."""
        # Calculate regime thresholds based on historical data
        returns_array = np.array([float(r) for r in returns])
        historical_vol_percentiles = []
        
        # Calculate percentiles for different vol levels
        window = 21
        for i in range(window, len(returns_array)):
            vol = np.std(returns_array[i-window:i], ddof=1)
            historical_vol_percentiles.append(vol)
        
        if not historical_vol_percentiles:
            return MarketCondition.NORMAL
        
        # Define regime thresholds
        p25 = np.percentile(historical_vol_percentiles, 25)
        p50 = np.percentile(historical_vol_percentiles, 50)
        p75 = np.percentile(historical_vol_percentiles, 75)
        p90 = np.percentile(historical_vol_percentiles, 90)
        
        current_vol_float = float(current_vol)
        
        if current_vol_float <= p25:
            return MarketCondition.CALM
        elif current_vol_float <= p50:
            return MarketCondition.NORMAL
        elif current_vol_float <= p75:
            return MarketCondition.VOLATILE
        elif current_vol_float <= p90:
            return MarketCondition.STRESSED
        else:
            return MarketCondition.EMERGENCY
    
    def _calculate_volatility_percentile(self, returns: List[Decimal]) -> Decimal:
        """Calculate current volatility percentile."""
        returns_array = np.array([float(r) for r in returns])
        
        # Calculate rolling volatilities
        rolling_vol = []
        window = 21
        for i in range(window, len(returns_array)):
            vol = np.std(returns_array[i-window:i], ddof=1)
            rolling_vol.append(vol)
        
        if not rolling_vol:
            return '0.5'
        
        current_vol = rolling_vol[-1]
        percentile = stats.percentileofscore(rolling_vol, current_vol)
        
        return str(percentile / 100.0)
    
    def _calculate_volatility_of_volatility(self, returns: List[Decimal]) -> Decimal:
        """Calculate volatility of volatility."""
        returns_array = np.array([float(r) for r in returns])
        
        # Calculate rolling volatilities
        rolling_vol = []
        window = 21
        for i in range(window, len(returns_array)):
            vol = np.std(returns_array[i-window:i], ddof=1)
            rolling_vol.append(vol)
        
        if len(rolling_vol) < 10:
            return '0.1'  # Default assumption
        
        vol_of_vol = np.std(rolling_vol, ddof=1)
        return str(vol_of_vol)
    
    def _calculate_tail_risk_indicator(self, returns: List[Decimal]) -> Decimal:
        """Calculate tail risk indicator based on extreme observations."""
        returns_array = np.array([float(r) for r in returns])
        
        # Calculate various tail risk metrics
        sorted_returns = np.sort(returns_array)
        n = len(sorted_returns)
        
        # Worst 5% average loss
        tail_size = max(5, int(0.05 * n))
        worst_tail_avg = np.mean(sorted_returns[:tail_size])
        
        # Worst single day loss
        worst_day = sorted_returns[0]
        
        # Extreme Value Theory approximation
        # Fit exponential distribution to tail
        tail_returns = sorted_returns[:tail_size]
        lambda_param = 1.0 / abs(np.mean(tail_returns)) if np.mean(tail_returns) < 0 else 1.0
        
        # Calculate tail risk score (0-1, higher = more risky)
        tail_risk_score = min(1.0, abs(worst_day) * 2 + abs(worst_tail_avg))
        
        return str(tail_risk_score)


class BookmakerReliabilityScorer:
    """Advanced bookmaker reliability scoring engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bookmaker_cache = {}
        self.reliability_model = None
        
    def score_bookmaker_reliability(
        self,
        bookmaker_name: str,
        historical_data: Optional[Dict[str, Any]] = None,
        account_data: Optional[Dict[str, Any]] = None
    ) -> BookmakerReliabilityMetrics:
        """
        Score bookmaker reliability based on multiple factors.
        
        Args:
            bookmaker_name: Name of the bookmaker
            historical_data: Historical performance data
            account_data: Account-specific data
            
        Returns:
            BookmakerReliabilityMetrics with comprehensive reliability assessment
        """
        # Get base reliability score
        base_reliability = self._calculate_base_reliability(bookmaker_name)
        
        # Calculate execution success rate
        execution_success_rate = self._calculate_execution_success_rate(
            bookmaker_name, historical_data
        )
        
        # Calculate cancellation rate
        cancellation_rate = self._calculate_cancellation_rate(
            bookmaker_name, historical_data
        )
        
        # Calculate settlement accuracy
        settlement_accuracy = self._calculate_settlement_accuracy(
            bookmaker_name, historical_data
        )
        
        # Calculate support quality score
        support_quality = self._calculate_support_quality(bookmaker_name)
        
        # Regulatory compliance score
        regulatory_compliance = self._assess_regulatory_compliance(bookmaker_name)
        
        # Financial stability score
        financial_stability = self._assess_financial_stability(bookmaker_name, account_data)
        
        # Calculate composite rating score
        rating_score = self._calculate_composite_rating(
            base_reliability, execution_success_rate, settlement_accuracy,
            support_quality, regulatory_compliance, financial_stability
        )
        
        return BookmakerReliabilityMetrics(
            reliability_score=base_reliability,
            rating_score=rating_score,
            execution_success_rate=execution_success_rate,
            cancellation_rate=cancellation_rate,
            settlement_accuracy=settlement_accuracy,
            support_quality=support_quality,
            regulatory_compliance=regulatory_compliance,
            financial_stability=financial_stability
        )
    
    def _calculate_base_reliability(self, bookmaker_name: str) -> Decimal:
        """Calculate base reliability score for bookmaker."""
        # This would typically integrate with a bookmaker database
        # For now, using predefined scores based on market knowledge
        
        known_bookmakers = {
            'pinnacle': '0.95',
            'betfair': '0.92',
            'william_hill': '0.88',
            'ladbrokes': '0.85',
            'bet365': '0.90',
            'unibet': '0.87',
            'betway': '0.83',
            '888sport': '0.82'
        }
        
        # Convert to lowercase for matching
        name_lower = bookmaker_name.lower().replace(' ', '_')
        
        # Return known score or default
        return known_bookmakers.get(name_lower, '0.75')
    
    def _calculate_execution_success_rate(
        self,
        bookmaker_name: str,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Calculate execution success rate."""
        if not historical_data:
            # Use base reliability as proxy
            return self._calculate_base_reliability(bookmaker_name)
        
        # Extract execution data
        total_bets = historical_data.get('total_bets', 0)
        successful_bets = historical_data.get('successful_bets', 0)
        
        if total_bets == 0:
            return self._calculate_base_reliability(bookmaker_name)
        
        success_rate = str(successful_bets / total_bets)
        return min(success_rate, '1.0')
    
    def _calculate_cancellation_rate(
        self,
        bookmaker_name: str,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Calculate bet cancellation rate."""
        if not historical_data:
            # Assume low cancellation rate for reputable bookmakers
            return '0.05'
        
        total_bets = historical_data.get('total_bets', 0)
        cancelled_bets = historical_data.get('cancelled_bets', 0)
        
        if total_bets == 0:
            return '0.05'
        
        cancellation_rate = str(cancelled_bets / total_bets)
        return min(cancellation_rate, '0.5')  # Cap at 50%
    
    def _calculate_settlement_accuracy(
        self,
        bookmaker_name: str,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Calculate settlement accuracy."""
        if not historical_data:
            # High accuracy for major bookmakers
            return '0.98'
        
        total_settlements = historical_data.get('total_settlements', 0)
        accurate_settlements = historical_data.get('accurate_settlements', 0)
        
        if total_settlements == 0:
            return '0.98'
        
        accuracy_rate = str(accurate_settlements / total_settlements)
        return min(accuracy_rate, '1.0')
    
    def _calculate_support_quality(self, bookmaker_name: str) -> Decimal:
        """Calculate support quality score."""
        # This would typically involve analyzing support ticket data,
        # response times, resolution rates, etc.
        
        # For now, using predefined scores
        support_scores = {
            'pinnacle': '0.90',
            'betfair': '0.88',
            'william_hill': '0.85',
            'ladbrokes': '0.82',
            'bet365': '0.87',
            'unibet': '0.83',
            'betway': '0.80',
            '888sport': '0.78'
        }
        
        name_lower = bookmaker_name.lower().replace(' ', '_')
        return support_scores.get(name_lower, '0.75')
    
    def _assess_regulatory_compliance(self, bookmaker_name: str) -> Decimal:
        """Assess regulatory compliance score."""
        # This would check licensing status, regulatory history, etc.
        
        # Major licensed bookmakers get high scores
        licensed_bookmakers = {
            'pinnacle': '1.0',
            'betfair': '1.0',
            'william_hill': '0.95',
            'ladbrokes': '0.95',
            'bet365': '0.98',
            'unibet': '0.96',
            'betway': '0.92',
            '888sport': '0.91'
        }
        
        name_lower = bookmaker_name.lower().replace(' ', '_')
        return licensed_bookmakers.get(name_lower, '0.70')
    
    def _assess_financial_stability(
        self,
        bookmaker_name: str,
        account_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Assess financial stability of bookmaker."""
        # This would involve checking financial statements, credit ratings, etc.
        
        # Major established bookmakers get high scores
        stability_scores = {
            'pinnacle': '0.95',
            'betfair': '0.93',
            'william_hill': '0.90',
            'ladbrokes': '0.88',
            'bet365': '0.92',
            'unibet': '0.87',
            'betway': '0.85',
            '888sport': '0.84'
        }
        
        name_lower = bookmaker_name.lower().replace(' ', '_')
        base_score = stability_scores.get(name_lower, '0.75')
        
        # Adjust based on account-specific factors
        if account_data:
            # Adjust for account status, limits, etc.
            account_status = account_data.get('status', 'active')
            if account_status != 'active':
                base_score *= '0.9'  # Reduced score for non-active accounts
            
            # Check for recent restrictions
            recent_restrictions = account_data.get('recent_restrictions', 0)
            if recent_restrictions > 0:
                base_score *= '0.95' ** recent_restrictions
        
        return min(base_score, '1.0')
    
    def _calculate_composite_rating(
        self,
        reliability: Decimal,
        execution_success: Decimal,
        settlement_accuracy: Decimal,
        support_quality: Decimal,
        regulatory_compliance: Decimal,
        financial_stability: Decimal
    ) -> Decimal:
        """Calculate composite reliability rating."""
        # Weighted average of all components
        weights = {
            'reliability': '0.25',
            'execution': '0.20',
            'settlement': '0.20',
            'support': '0.15',
            'regulatory': '0.10',
            'financial': '0.10'
        }
        
        composite_score = (
            reliability * weights['reliability'] +
            execution_success * weights['execution'] +
            settlement_accuracy * weights['settlement'] +
            support_quality * weights['support'] +
            regulatory_compliance * weights['regulatory'] +
            financial_stability * weights['financial']
        )
        
        return min(composite_score, '1.0')


class LiquidityDepthAnalyzer:
    """Advanced liquidity depth analysis engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.liquidity_cache = {}
        
    def analyze_liquidity_depth(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None
    ) -> LiquidityDepthMetrics:
        """
        Analyze liquidity depth for arbitrage opportunity.
        
        Args:
            opportunity: Arbitrage opportunity to analyze
            market_data: Market depth and order book data
            
        Returns:
            LiquidityDepthMetrics with comprehensive liquidity assessment
        """
        # Calculate market depth
        market_depth = self._calculate_market_depth(opportunity, market_data)
        
        # Estimate bid-ask spread
        bid_ask_spread = self._estimate_bid_ask_spread(opportunity, market_data)
        
        # Calculate market impact factor
        market_impact_factor = self._calculate_market_impact(opportunity, market_depth)
        
        # Estimate fill probability
        fill_probability = self._estimate_fill_probability(opportunity, market_depth, bid_ask_spread)
        
        # Estimate slippage
        slippage_estimate = self._estimate_slippage(opportunity, bid_ask_spread, market_impact_factor)
        
        # Assess market concentration
        market_concentration = self._assess_market_concentration(opportunity, market_data)
        
        # Classify liquidity regime
        liquidity_regime = self._classify_liquidity_regime(market_depth, bid_ask_spread)
        
        return LiquidityDepthMetrics(
            market_depth=market_depth,
            bid_ask_spread=bid_ask_spread,
            market_impact_factor=market_impact_factor,
            fill_probability=fill_probability,
            slippage_estimate=slippage_estimate,
            market_concentration=market_concentration,
            liquidity_regime=liquidity_regime
        )
    
    def _calculate_market_depth(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Calculate available market depth."""
        if market_data and 'market_depth' in market_data:
            return market_data['market_depth']
        
        # Estimate based on profit margin and bookmaker quality
        base_depth = '5000'  # Base assumption
        
        # Adjust for profit margin
        margin_multiplier = opportunity.profit_margin / '0.02'  # Normalize to 2%
        margin_adjustment = min(margin_multiplier, '2.0')  # Cap adjustment
        
        # Adjust for bookmaker quality
        bookmaker_quality_multiplier = self._estimate_bookmaker_quality(opportunity)
        
        estimated_depth = base_depth * margin_adjustment * bookmaker_quality_multiplier
        
        return min(estimated_depth, '50000')  # Cap at reasonable level
    
    def _estimate_bookmaker_quality(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Estimate bookmaker quality multiplier."""
        reliability_scores = []
        
        for leg in opportunity.legs:
            # Use predefined scores (would integrate with bookmaker database)
            bookmaker_scores = {
                'pinnacle': '0.95',
                'betfair': '0.92',
                'william_hill': '0.88',
                'ladbrokes': '0.85',
                'bet365': '0.90',
                'unibet': '0.87',
                'betway': '0.83',
                '888sport': '0.82'
            }
            
            name_lower = leg.bookmaker.lower().replace(' ', '_')
            score = bookmaker_scores.get(name_lower, '0.75')
            reliability_scores.append(score)
        
        # Average reliability score
        avg_reliability = sum(reliability_scores) / len(reliability_scores)
        
        # Convert to multiplier (higher reliability = higher depth multiplier)
        return '0.5' + avg_reliability * '0.5'
    
    def _estimate_bid_ask_spread(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Estimate bid-ask spread."""
        if market_data and 'bid_ask_spread' in market_data:
            return market_data['bid_ask_spread']
        
        # Base spread assumptions by profit margin
        if opportunity.profit_margin > '0.10':
            base_spread = '0.005'  # 0.5% for high-margin opportunities
        elif opportunity.profit_margin > '0.05':
            base_spread = '0.008'  # 0.8% for medium-margin opportunities
        else:
            base_spread = '0.015'  # 1.5% for low-margin opportunities
        
        # Adjust for market volatility (simplified)
        volatility_adjustment = '1.2'  # Would be calculated from actual volatility data
        
        return base_spread * volatility_adjustment
    
    def _calculate_market_impact(
        self,
        opportunity: ArbitrageOpportunity,
        market_depth: Decimal
    ) -> Decimal:
        """Calculate estimated market impact factor."""
        # Market impact based on position size relative to market depth
        position_size_ratio = opportunity.total_stake / market_depth
        
        # Square root impact model (simplified)
        if position_size_ratio <= '0.01':
            # Minimal impact for small positions
            impact = position_size_ratio * '0.1'
        elif position_size_ratio <= '0.05':
            # Linear impact for medium positions
            impact = '0.001' + (position_size_ratio - '0.01') * '0.02'
        else:
            # Square root impact for large positions
            impact = '0.002' + np.sqrt(position_size_ratio - '0.05') * '0.05'
        
        return min(impact, '0.20')  # Cap at 20% impact
    
    def _estimate_fill_probability(
        self,
        opportunity: ArbitrageOpportunity,
        market_depth: Decimal,
        bid_ask_spread: Decimal
    ) -> Decimal:
        """Estimate probability of successful fill."""
        # Base fill probability
        base_prob = '0.90'
        
        # Adjust for market depth (deeper markets = higher fill probability)
        depth_factor = min(market_depth / '10000', '1.5')  # Max 50% boost
        depth_adjustment = '1.0' + (depth_factor - '1.0') * '0.1'
        
        # Adjust for bid-ask spread (wider spreads = lower fill probability)
        spread_factor = max('0.5', '1.0' - bid_ask_spread * '10')
        
        # Adjust for position size (larger positions = lower fill probability)
        size_factor = max('0.5', '1.0' - opportunity.total_stake / '5000')
        
        fill_probability = base_prob * depth_adjustment * spread_factor * size_factor
        
        return min(fill_probability, '0.99')  # Cap at 99%
    
    def _estimate_slippage(
        self,
        opportunity: ArbitrageOpportunity,
        bid_ask_spread: Decimal,
        market_impact: Decimal
    ) -> Decimal:
        """Estimate potential slippage."""
        # Slippage is combination of spread and market impact
        total_slippage = bid_ask_spread + market_impact
        
        # Add execution risk component
        execution_risk = '0.001'  # 0.1% execution risk
        total_slippage += execution_risk
        
        return min(total_slippage, '0.50')  # Cap at 50%
    
    def _assess_market_concentration(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Assess market concentration risk."""
        # Count unique bookmakers
        unique_bookmakers = len(set(leg.bookmaker for leg in opportunity.legs))
        
        # Concentration score (lower = more concentrated, higher = more diversified)
        if unique_bookmakers >= 4:
            concentration = '0.2'  # Low concentration
        elif unique_bookmakers == 3:
            concentration = '0.5'  # Medium concentration
        elif unique_bookmakers == 2:
            concentration = '0.8'  # High concentration
        else:
            concentration = '1.0'  # Very high concentration
        
        # Adjust for market data if available
        if market_data and 'market_concentration' in market_data:
            return market_data['market_concentration']
        
        return concentration
    
    def _classify_liquidity_regime(
        self,
        market_depth: Decimal,
        bid_ask_spread: Decimal
    ) -> str:
        """Classify current liquidity regime."""
        # Define regime thresholds
        deep_market_threshold = '20000'  # $20K+
        moderate_market_threshold = '5000'  # $5K+
        
        tight_spread_threshold = '0.01'  # 1%
        moderate_spread_threshold = '0.02'  # 2%
        
        if market_depth >= deep_market_threshold and bid_ask_spread <= tight_spread_threshold:
            return "deep_liquid"
        elif market_depth >= moderate_market_threshold and bid_ask_spread <= moderate_spread_threshold:
            return "moderate_liquid"
        elif market_depth >= '2000' and bid_ask_spread <= '0.03':
            return "shallow_liquid"
        else:
            return "illiquid"


class ExecutionDifficultyAssessor:
    """Advanced execution difficulty assessment engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def assess_execution_difficulty(
        self,
        opportunity: ArbitrageOpportunity,
        market_conditions: MarketCondition = MarketCondition.NORMAL
    ) -> Dict[str, Decimal]:
        """
        Assess execution difficulty for arbitrage opportunity.
        
        Args:
            opportunity: Arbitrage opportunity to assess
            market_conditions: Current market conditions
            
        Returns:
            Dictionary of execution difficulty metrics
        """
        # Calculate base execution time
        base_execution_time = self._estimate_execution_time(opportunity)
        
        # Calculate coordination complexity
        coordination_complexity = self._assess_coordination_complexity(opportunity)
        
        # Calculate technical execution risk
        technical_risk = self._assess_technical_execution_risk(opportunity)
        
        # Calculate timing sensitivity
        timing_sensitivity = self._assess_timing_sensitivity(opportunity, market_conditions)
        
        # Calculate manual intervention probability
        intervention_probability = self._assess_intervention_probability(opportunity)
        
        # Calculate total execution difficulty score
        difficulty_score = self._calculate_execution_difficulty_score(
            base_execution_time, coordination_complexity, technical_risk,
            timing_sensitivity, intervention_probability, market_conditions
        )
        
        return {
            'base_execution_time': base_execution_time,
            'coordination_complexity': coordination_complexity,
            'technical_risk': technical_risk,
            'timing_sensitivity': timing_sensitivity,
            'intervention_probability': intervention_probability,
            'total_difficulty_score': difficulty_score
        }
    
    def _estimate_execution_time(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Estimate time required for execution."""
        # Base time per leg
        base_time_per_leg = '5'  # 5 seconds per leg
        
        # Add coordination overhead
        coordination_overhead = '10'  # 10 seconds coordination
        
        # Add complexity factor based on number of legs
        complexity_factor = len(opportunity.legs) * '2'  # 2 seconds per additional leg
        
        # Add market condition adjustment
        market_adjustment = self._get_market_time_adjustment(opportunity)
        
        total_time = (base_time_per_leg * len(opportunity.legs) + 
                     coordination_overhead + complexity_factor) * market_adjustment
        
        return min(total_time, '300')  # Cap at 5 minutes
    
    def _get_market_time_adjustment(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Get time adjustment factor based on market conditions."""
        # Faster execution in calm markets, slower in volatile markets
        market_speeds = {
            MarketCondition.CALM: '0.8',
            MarketCondition.NORMAL: '1.0',
            MarketCondition.VOLATILE: '1.5',
            MarketCondition.STRESSED: '2.0',
            MarketCondition.EMERGENCY: '3.0'
        }
        
        # Would determine actual market condition from real data
        return market_speeds.get(MarketCondition.NORMAL, '1.0')
    
    def _assess_coordination_complexity(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Assess coordination complexity between bookmakers."""
        # More legs = higher complexity
        leg_complexity = len(opportunity.legs) * '0.2'
        
        # Different bookmakers = higher complexity
        unique_bookmakers = len(set(leg.bookmaker for leg in opportunity.legs))
        bookmaker_complexity = unique_bookmakers * '0.15'
        
        # Time synchronization requirement
        sync_complexity = '0.3' if len(opportunity.legs) > 2 else '0.1'
        
        total_complexity = min(
            leg_complexity + bookmaker_complexity + sync_complexity,
            '1.0'
        )
        
        return total_complexity
    
    def _assess_technical_execution_risk(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Assess technical execution risk."""
        # API availability risk
        api_risk = '0.1'  # Base API risk
        
        # Login/credential risk for each bookmaker
        login_risk = len(opportunity.legs) * '0.05'
        
        # Bet placement risk
        placement_risk = len(opportunity.legs) * '0.1'
        
        # Confirmation risk
        confirmation_risk = len(opportunity.legs) * '0.05'
        
        total_technical_risk = api_risk + login_risk + placement_risk + confirmation_risk
        
        return min(total_technical_risk, '1.0')
    
    def _assess_timing_sensitivity(
        self,
        opportunity: ArbitrageOpportunity,
        market_conditions: MarketCondition
    ) -> Decimal:
        """Assess timing sensitivity of opportunity."""
        # Base timing sensitivity
        base_sensitivity = '0.3'
        
        # Adjust for market volatility
        volatility_multipliers = {
            MarketCondition.CALM: '0.8',
            MarketCondition.NORMAL: '1.0',
            MarketCondition.VOLATILE: '1.5',
            MarketCondition.STRESSED: '2.0',
            MarketCondition.EMERGENCY: '3.0'
        }
        
        volatility_multiplier = volatility_multipliers.get(market_conditions, '1.0')
        
        # Adjust for profit margin (higher margins = more time-sensitive)
        margin_factor = min(opportunity.profit_margin / '0.02', '2.0')
        
        timing_sensitivity = base_sensitivity * volatility_multiplier * margin_factor
        
        return min(timing_sensitivity, '1.0')
    
    def _assess_intervention_probability(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Assess probability of manual intervention required."""
        # Base intervention probability
        base_prob = '0.1'
        
        # Adjust for complexity factors
        leg_factor = len(opportunity.legs) * '0.05'
        bookmaker_factor = len(set(leg.bookmaker for leg in opportunity.legs)) * '0.03'
        
        # Adjust for stake size (larger stakes = more monitoring)
        size_factor = min(opportunity.total_stake / '1000', '0.2')
        
        intervention_probability = base_prob + leg_factor + bookmaker_factor + size_factor
        
        return min(intervention_probability, '0.8')  # Cap at 80%
    
    def _calculate_execution_difficulty_score(
        self,
        execution_time: Decimal,
        coordination_complexity: Decimal,
        technical_risk: Decimal,
        timing_sensitivity: Decimal,
        intervention_probability: Decimal,
        market_conditions: MarketCondition
    ) -> Decimal:
        """Calculate overall execution difficulty score."""
        # Normalize execution time to 0-1 scale
        normalized_time = min(execution_time / '60', '1.0')  # Max 1 minute
        
        # Weighted combination of all factors
        weights = {
            'time': '0.25',
            'coordination': '0.25',
            'technical': '0.20',
            'timing': '0.15',
            'intervention': '0.15'
        }
        
        difficulty_score = (
            normalized_time * weights['time'] +
            coordination_complexity * weights['coordination'] +
            technical_risk * weights['technical'] +
            timing_sensitivity * weights['timing'] +
            intervention_probability * weights['intervention']
        )
        
        return min(difficulty_score, '1.0')


class TimingSensitivityAnalyzer:
    """Advanced timing sensitivity analysis engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_timing_sensitivity(
        self,
        opportunity: ArbitrageOpportunity,
        market_conditions: MarketCondition = MarketCondition.NORMAL,
        odds_history: Optional[List[Decimal]] = None
    ) -> Dict[str, Decimal]:
        """
        Analyze timing sensitivity for arbitrage opportunity.
        
        Args:
            opportunity: Arbitrage opportunity to analyze
            market_conditions: Current market conditions
            odds_history: Historical odds data for analysis
            
        Returns:
            Dictionary of timing sensitivity metrics
        """
        # Calculate time decay rate
        time_decay_rate = self._calculate_time_decay_rate(opportunity, odds_history)
        
        # Assess urgency level
        urgency_level = self._assess_urgency_level(opportunity, market_conditions)
        
        # Calculate odds volatility
        odds_volatility = self._calculate_odds_volatility(opportunity, odds_history)
        
        # Assess deadline pressure
        deadline_pressure = self._assess_deadline_pressure(opportunity)
        
        # Calculate optimal execution window
        optimal_window = self._calculate_optimal_execution_window(opportunity, market_conditions)
        
        # Calculate timing risk score
        timing_risk_score = self._calculate_timing_risk_score(
            time_decay_rate, urgency_level, odds_volatility, 
            deadline_pressure, optimal_window, market_conditions
        )
        
        return {
            'time_decay_rate': time_decay_rate,
            'urgency_level': urgency_level,
            'odds_volatility': odds_volatility,
            'deadline_pressure': deadline_pressure,
            'optimal_execution_window': optimal_window,
            'timing_risk_score': timing_risk_score
        }
    
    def _calculate_time_decay_rate(
        self,
        opportunity: ArbitrageOpportunity,
        odds_history: Optional[List[Decimal]] = None
    ) -> Decimal:
        """Calculate rate at which arbitrage opportunity decays over time."""
        if not odds_history or len(odds_history) < 10:
            # Use default decay rate based on profit margin
            base_decay = '0.1'  # 10% per hour base rate
            
            # Higher margins decay faster
            margin_factor = opportunity.profit_margin / '0.02'
            
            return base_decay * margin_factor
        
        # Calculate actual decay rate from odds history
        if len(odds_history) >= 2:
            initial_odds = odds_history[0]
            current_odds = odds_history[-1]
            
            # Calculate implied probability change
            initial_prob = '1' / initial_odds
            current_prob = '1' / current_odds
            
            prob_change_rate = abs(current_prob - initial_prob) / len(odds_history)
            
            # Convert to decay rate (simplified)
            decay_rate = prob_change_rate * '10'  # Scale factor
            
            return min(decay_rate, '1.0')  # Cap at 100% per time unit
        
        return '0.1'  # Default
    
    def _assess_urgency_level(
        self,
        opportunity: ArbitrageOpportunity,
        market_conditions: MarketCondition
    ) -> Decimal:
        """Assess urgency level for opportunity execution."""
        # Base urgency
        base_urgency = '0.5'
        
        # Time to event factor
        time_to_event = opportunity.event_date - datetime.utcnow()
        if time_to_event.total_seconds() <= 3600:  # Less than 1 hour
            urgency_multiplier = '2.0'
        elif time_to_event.total_seconds() <= 86400:  # Less than 1 day
            urgency_multiplier = '1.5'
        else:
            urgency_multiplier = '1.0'
        
        # Market condition factor
        condition_factors = {
            MarketCondition.CALM: '0.8',
            MarketCondition.NORMAL: '1.0',
            MarketCondition.VOLATILE: '1.8',
            MarketCondition.STRESSED: '2.5',
            MarketCondition.EMERGENCY: '3.0'
        }
        
        condition_factor = condition_factors.get(market_conditions, '1.0')
        
        # Profit margin factor (higher margin = more urgent)
        margin_factor = opportunity.profit_margin / '0.02'
        
        urgency_level = base_urgency * urgency_multiplier * condition_factor * margin_factor
        
        return min(urgency_level, '1.0')
    
    def _calculate_odds_volatility(
        self,
        opportunity: ArbitrageOpportunity,
        odds_history: Optional[List[Decimal]] = None
    ) -> Decimal:
        """Calculate volatility of odds."""
        if not odds_history or len(odds_history) < 2:
            # Estimate volatility based on market conditions
            return '0.02'  # 2% default volatility
        
        odds_array = np.array([float(o) for o in odds_history])
        volatility = np.std(odds_array, ddof=1)
        
        return str(volatility)
    
    def _assess_deadline_pressure(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Assess deadline pressure for opportunity."""
        time_to_event = opportunity.event_date - datetime.utcnow()
        total_seconds = time_to_event.total_seconds()
        
        # Convert to hours
        hours_to_event = str(total_seconds / 3600)
        
        # Calculate pressure based on time remaining
        if hours_to_event <= '1':
            pressure = '1.0'  # Maximum pressure
        elif hours_to_event <= '6':
            pressure = '0.8'  # High pressure
        elif hours_to_event <= '24':
            pressure = '0.6'  # Medium pressure
        else:
            pressure = '0.3'  # Low pressure
        
        return pressure
    
    def _calculate_optimal_execution_window(
        self,
        opportunity: ArbitrageOpportunity,
        market_conditions: MarketCondition
    ) -> Decimal:
        """Calculate optimal execution window (in minutes)."""
        # Base window
        base_window = '30'  # 30 minutes
        
        # Adjust for market conditions
        condition_multipliers = {
            MarketCondition.CALM: '2.0',    # Longer window in calm markets
            MarketCondition.NORMAL: '1.0',  # Standard window
            MarketCondition.VOLATILE: '0.5', # Shorter window in volatile markets
            MarketCondition.STRESSED: '0.25', # Very short window
            MarketCondition.EMERGENCY: '0.1'  # Minimal window
        }
        
        multiplier = condition_multipliers.get(market_conditions, '1.0')
        
        # Adjust for profit margin (higher margin = shorter window)
        margin_factor = max('0.5', '1.0' - opportunity.profit_margin / '0.10')
        
        optimal_window = base_window * multiplier * margin_factor
        
        return max(optimal_window, '5')  # Minimum 5 minutes
    
    def _calculate_timing_risk_score(
        self,
        time_decay_rate: Decimal,
        urgency_level: Decimal,
        odds_volatility: Decimal,
        deadline_pressure: Decimal,
        optimal_window: Decimal,
        market_conditions: MarketCondition
    ) -> Decimal:
        """Calculate overall timing risk score."""
        # Normalize components to 0-1 scale
        normalized_decay = min(time_decay_rate * '5', '1.0')
        normalized_volatility = min(odds_volatility / '0.1', '1.0')
        normalized_window = max('1.0' - optimal_window / '60', '0.0')
        
        # Weighted combination
        weights = {
            'decay': '0.3',
            'urgency': '0.25',
            'volatility': '0.2',
            'pressure': '0.15',
            'window': '0.1'
        }
        
        timing_risk_score = (
            normalized_decay * weights['decay'] +
            urgency_level * weights['urgency'] +
            normalized_volatility * weights['volatility'] +
            deadline_pressure * weights['pressure'] +
            normalized_window * weights['window']
        )
        
        return min(timing_risk_score, '1.0')


class ConfidenceScorer:
    """Advanced confidence scoring engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def calculate_confidence_score(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None,
        historical_performance: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Decimal]:
        """
        Calculate comprehensive confidence score for opportunity.
        
        Args:
            opportunity: Arbitrage opportunity
            market_data: Market context data
            historical_performance: Historical performance data
            
        Returns:
            Dictionary of confidence metrics
        """
        # Data quality confidence
        data_confidence = self._assess_data_confidence(opportunity, market_data)
        
        # Model confidence
        model_confidence = self._assess_model_confidence(opportunity, historical_performance)
        
        # Execution confidence
        execution_confidence = self._assess_execution_confidence(opportunity)
        
        # Market confidence
        market_confidence = self._assess_market_confidence(opportunity, market_data)
        
        # Overall confidence score
        overall_confidence = self._calculate_overall_confidence(
            data_confidence, model_confidence, execution_confidence, market_confidence
        )
        
        return {
            'data_confidence': data_confidence,
            'model_confidence': model_confidence,
            'execution_confidence': execution_confidence,
            'market_confidence': market_confidence,
            'overall_confidence': overall_confidence,
            'confidence_interval': self._calculate_confidence_interval(overall_confidence)
        }
    
    def _assess_data_confidence(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Assess confidence in data quality."""
        # Base data confidence
        base_confidence = '0.8'
        
        # Adjust for data freshness
        time_since_update = datetime.utcnow() - opportunity.odds_freshness
        if time_since_update.total_seconds() < 300:  # Less than 5 minutes
            freshness_bonus = '0.1'
        elif time_since_update.total_seconds() < 1800:  # Less than 30 minutes
            freshness_bonus = '0.05'
        else:
            freshness_bonus = '0.0'
        
        # Adjust for data source quality
        source_quality = self._assess_data_source_quality(opportunity)
        
        # Adjust for cross-validation
        cross_validation_confidence = self._assess_cross_validation(opportunity, market_data)
        
        data_confidence = base_confidence + freshness_bonus + source_quality + cross_validation_confidence
        
        return min(data_confidence, '1.0')
    
    def _assess_data_source_quality(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Assess quality of data sources."""
        # Higher quality for reputable bookmakers
        quality_scores = []
        
        for leg in opportunity.legs:
            # Predefined quality scores
            bookmaker_quality = {
                'pinnacle': '0.95',
                'betfair': '0.92',
                'william_hill': '0.88',
                'ladbrokes': '0.85',
                'bet365': '0.90',
                'unibet': '0.87',
                'betway': '0.83',
                '888sport': '0.82'
            }
            
            name_lower = leg.bookmaker.lower().replace(' ', '_')
            quality = bookmaker_quality.get(name_lower, '0.75')
            quality_scores.append(quality)
        
        # Average quality score
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        # Convert to confidence adjustment (0.0 to 0.15)
        confidence_adjustment = (avg_quality - '0.75') * '0.6'
        
        return max(confidence_adjustment, '0.0')
    
    def _assess_cross_validation(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Assess cross-validation confidence."""
        if not market_data:
            return '0.0'
        
        # Check for multiple data sources
        data_sources = market_data.get('data_sources', [])
        cross_validation_bonus = min(len(data_sources) * '0.02', '0.1')
        
        # Check for consistency between sources
        consistency_score = market_data.get('consistency_score', '0.5')
        consistency_bonus = consistency_score * '0.05'
        
        return cross_validation_bonus + consistency_bonus
    
    def _assess_model_confidence(
        self,
        opportunity: ArbitrageOpportunity,
        historical_performance: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Assess confidence in model predictions."""
        # Base model confidence
        base_confidence = '0.7'
        
        if not historical_performance:
            return base_confidence
        
        # Adjust for historical accuracy
        accuracy_rate = historical_performance.get('accuracy_rate', '0.7')
        accuracy_bonus = (accuracy_rate - '0.7') * '0.3'
        
        # Adjust for sample size
        sample_size = historical_performance.get('sample_size', 0)
        if sample_size >= 1000:
            sample_bonus = '0.1'
        elif sample_size >= 500:
            sample_bonus = '0.05'
        else:
            sample_bonus = '0.0'
        
        model_confidence = base_confidence + accuracy_bonus + sample_bonus
        
        return min(model_confidence, '1.0')
    
    def _assess_execution_confidence(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Assess confidence in execution ability."""
        # Base execution confidence
        base_confidence = '0.8'
        
        # Adjust for account status (assume active for simplicity)
        account_bonus = '0.1'  # Bonus for active accounts
        
        # Adjust for bookmaker relationships
        relationship_bonus = self._assess_bookmaker_relationships(opportunity)
        
        # Adjust for execution complexity
        complexity_penalty = min(len(opportunity.legs) * '0.02', '0.1')
        
        execution_confidence = base_confidence + account_bonus + relationship_bonus - complexity_penalty
        
        return max(execution_confidence, '0.5')
    
    def _assess_bookmaker_relationships(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Assess strength of bookmaker relationships."""
        # Stronger relationships = higher confidence
        relationship_strengths = {
            'pinnacle': '0.1',
            'betfair': '0.08',
            'william_hill': '0.06',
            'ladbrokes': '0.05',
            'bet365': '0.07',
            'unibet': '0.05',
            'betway': '0.04',
            '888sport': '0.03'
        }
        
        total_bonus = '0.0'
        for leg in opportunity.legs:
            name_lower = leg.bookmaker.lower().replace(' ', '_')
            bonus = relationship_strengths.get(name_lower, '0.02')
            total_bonus += bonus
        
        return min(total_bonus, '0.15')
    
    def _assess_market_confidence(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Assess confidence in market conditions."""
        # Base market confidence
        base_confidence = '0.75'
        
        if not market_data:
            return base_confidence
        
        # Adjust for market stability
        market_stability = market_data.get('market_stability', '0.5')
        stability_bonus = market_stability * '0.1'
        
        # Adjust for liquidity
        liquidity_score = market_data.get('liquidity_score', '0.5')
        liquidity_bonus = liquidity_score * '0.1'
        
        # Adjust for volatility
        volatility_score = market_data.get('volatility_score', '0.5')
        volatility_penalty = ('1.0' - volatility_score) * '0.05'
        
        market_confidence = base_confidence + stability_bonus + liquidity_bonus - volatility_penalty
        
        return min(market_confidence, '1.0')
    
    def _calculate_overall_confidence(
        self,
        data_confidence: Decimal,
        model_confidence: Decimal,
        execution_confidence: Decimal,
        market_confidence: Decimal
    ) -> Decimal:
        """Calculate overall confidence score."""
        # Weighted combination
        weights = {
            'data': '0.3',
            'model': '0.25',
            'execution': '0.25',
            'market': '0.2'
        }
        
        overall_confidence = (
            data_confidence * weights['data'] +
            model_confidence * weights['model'] +
            execution_confidence * weights['execution'] +
            market_confidence * weights['market']
        )
        
        return min(overall_confidence, '1.0')
    
    def _calculate_confidence_interval(self, confidence_score: Decimal) -> Tuple[Decimal, Decimal]:
        """Calculate confidence interval for the confidence score."""
        # Calculate uncertainty based on confidence score
        uncertainty = '1.0' - confidence_score
        
        # Lower bound
        lower_bound = max(confidence_score - uncertainty * '0.5', '0.0')
        
        # Upper bound
        upper_bound = min(confidence_score + uncertainty * '0.3', '1.0')
        
        return (lower_bound, upper_bound)


class UncertaintyQuantifier:
    """Advanced uncertainty quantification engine."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def quantify_uncertainty(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None,
        model_predictions: Optional[Dict[str, Decimal]] = None
    ) -> Dict[str, Decimal]:
        """
        Quantify different types of uncertainty for the opportunity.
        
        Args:
            opportunity: Arbitrage opportunity
            market_data: Market context data
            model_predictions: Model prediction confidence
            
        Returns:
            Dictionary of uncertainty metrics
        """
        # Model uncertainty
        model_uncertainty = self._quantify_model_uncertainty(model_predictions)
        
        # Data uncertainty
        data_uncertainty = self._quantify_data_uncertainty(opportunity, market_data)
        
        # Market uncertainty
        market_uncertainty = self._quantify_market_uncertainty(opportunity, market_data)
        
        # Execution uncertainty
        execution_uncertainty = self._quantify_execution_uncertainty(opportunity)
        
        # Temporal uncertainty
        temporal_uncertainty = self._quantify_temporal_uncertainty(opportunity)
        
        # Total uncertainty
        total_uncertainty = self._calculate_total_uncertainty(
            model_uncertainty, data_uncertainty, market_uncertainty,
            execution_uncertainty, temporal_uncertainty
        )
        
        return {
            'model_uncertainty': model_uncertainty,
            'data_uncertainty': data_uncertainty,
            'market_uncertainty': market_uncertainty,
            'execution_uncertainty': execution_uncertainty,
            'temporal_uncertainty': temporal_uncertainty,
            'total_uncertainty': total_uncertainty,
            'uncertainty_breakdown': self._generate_uncertainty_breakdown(
                model_uncertainty, data_uncertainty, market_uncertainty,
                execution_uncertainty, temporal_uncertainty
            )
        }
    
    def _quantify_model_uncertainty(self, model_predictions: Optional[Dict[str, Decimal]]) -> Decimal:
        """Quantify uncertainty in model predictions."""
        if not model_predictions:
            return '0.3'  # Default uncertainty
        
        # Extract prediction confidences
        confidences = list(model_predictions.values())
        
        if not confidences:
            return '0.3'
        
        # Calculate variance in predictions
        mean_confidence = sum(confidences) / len(confidences)
        variance = sum((c - mean_confidence) ** 2 for c in confidences) / len(confidences)
        
        # Uncertainty is proportional to variance and distance from perfect confidence
        base_uncertainty = str(variance)
        confidence_penalty = ('1.0' - mean_confidence) * '0.5'
        
        return min(base_uncertainty + confidence_penalty, '1.0')
    
    def _quantify_data_uncertainty(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Quantify uncertainty in input data."""
        # Base data uncertainty
        base_uncertainty = '0.2'
        
        # Adjust for data freshness
        time_since_update = datetime.utcnow() - opportunity.odds_freshness
        if time_since_update.total_seconds() > 3600:  # More than 1 hour
            freshness_uncertainty = '0.2'
        elif time_since_update.total_seconds() > 900:  # More than 15 minutes
            freshness_uncertainty = '0.1'
        else:
            freshness_uncertainty = '0.0'
        
        # Adjust for data source quality
        source_uncertainty = self._assess_data_source_uncertainty(opportunity)
        
        # Adjust for cross-validation
        validation_uncertainty = '0.1' if not market_data else '0.0'
        
        total_uncertainty = base_uncertainty + freshness_uncertainty + source_uncertainty + validation_uncertainty
        
        return min(total_uncertainty, '1.0')
    
    def _assess_data_source_uncertainty(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Assess uncertainty from data sources."""
        # Higher uncertainty for lower quality sources
        uncertainty_scores = []
        
        for leg in opportunity.legs:
            # Uncertainty inversely proportional to quality
            bookmaker_quality = {
                'pinnacle': '0.02',
                'betfair': '0.03',
                'william_hill': '0.05',
                'ladbrokes': '0.06',
                'bet365': '0.04',
                'unibet': '0.05',
                'betway': '0.07',
                '888sport': '0.08'
            }
            
            name_lower = leg.bookmaker.lower().replace(' ', '_')
            uncertainty = bookmaker_quality.get(name_lower, '0.1')
            uncertainty_scores.append(uncertainty)
        
        # Average uncertainty
        avg_uncertainty = sum(uncertainty_scores) / len(uncertainty_scores)
        return avg_uncertainty
    
    def _quantify_market_uncertainty(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Quantify uncertainty from market conditions."""
        # Base market uncertainty
        base_uncertainty = '0.15'
        
        if not market_data:
            return base_uncertainty
        
        # Adjust for market volatility
        volatility = market_data.get('volatility', '0.1')
        volatility_uncertainty = volatility * '0.5'
        
        # Adjust for liquidity
        liquidity = market_data.get('liquidity', '0.5')
        liquidity_uncertainty = ('1.0' - liquidity) * '0.2'
        
        # Adjust for market depth
        market_depth = market_data.get('market_depth', '5000')
        depth_uncertainty = max('0.0', ('10000' - market_depth) / '10000' * '0.3')
        
        total_uncertainty = base_uncertainty + volatility_uncertainty + liquidity_uncertainty + depth_uncertainty
        
        return min(total_uncertainty, '1.0')
    
    def _quantify_execution_uncertainty(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Quantify execution-related uncertainty."""
        # Base execution uncertainty
        base_uncertainty = '0.1'
        
        # Adjust for complexity (more legs = more uncertainty)
        complexity_uncertainty = len(opportunity.legs) * '0.02'
        
        # Adjust for stake size (larger stakes = more execution risk)
        size_uncertainty = min(opportunity.total_stake / '5000', '0.2')
        
        # Adjust for bookmaker diversity
        unique_bookmakers = len(set(leg.bookmaker for leg in opportunity.legs))
        diversity_uncertainty = unique_bookmakers * '0.01'
        
        total_uncertainty = base_uncertainty + complexity_uncertainty + size_uncertainty + diversity_uncertainty
        
        return min(total_uncertainty, '0.8')
    
    def _quantify_temporal_uncertainty(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Quantify temporal uncertainty."""
        # Time to event uncertainty
        time_to_event = opportunity.event_date - datetime.utcnow()
        hours_to_event = time_to_event.total_seconds() / 3600
        
        if hours_to_event < 1:
            temporal_uncertainty = '0.3'  # High uncertainty for immediate events
        elif hours_to_event < 24:
            temporal_uncertainty = '0.15'  # Medium uncertainty
        else:
            temporal_uncertainty = '0.05'  # Low uncertainty
        
        # Adjust for odds age
        odds_age = (datetime.utcnow() - opportunity.odds_freshness).total_seconds() / 3600
        if odds_age > 1:
            temporal_uncertainty += '0.1'
        
        return min(temporal_uncertainty, '0.5')
    
    def _calculate_total_uncertainty(
        self,
        model_uncertainty: Decimal,
        data_uncertainty: Decimal,
        market_uncertainty: Decimal,
        execution_uncertainty: Decimal,
        temporal_uncertainty: Decimal
    ) -> Decimal:
        """Calculate total combined uncertainty."""
        # Use formula for combining uncertainties: sqrt(sum of squares) for independent uncertainties
        squared_uncertainties = [
            model_uncertainty ** 2,
            data_uncertainty ** 2,
            market_uncertainty ** 2,
            execution_uncertainty ** 2,
            temporal_uncertainty ** 2
        ]
        
        total_variance = sum(squared_uncertainties)
        total_uncertainty = math.sqrt(float(total_variance))
        
        return min(str(total_uncertainty), '1.0')
    
    def _generate_uncertainty_breakdown(
        self,
        model_uncertainty: Decimal,
        data_uncertainty: Decimal,
        market_uncertainty: Decimal,
        execution_uncertainty: Decimal,
        temporal_uncertainty: Decimal
    ) -> Dict[str, Decimal]:
        """Generate detailed uncertainty breakdown."""
        return {
            'model_uncertainty': model_uncertainty,
            'data_uncertainty': data_uncertainty,
            'market_uncertainty': market_uncertainty,
            'execution_uncertainty': execution_uncertainty,
            'temporal_uncertainty': temporal_uncertainty,
            'dominant_uncertainty': self._identify_dominant_uncertainty(
                model_uncertainty, data_uncertainty, market_uncertainty,
                execution_uncertainty, temporal_uncertainty
            )
        }
    
    def _identify_dominant_uncertainty(
        self,
        model_uncertainty: Decimal,
        data_uncertainty: Decimal,
        market_uncertainty: Decimal,
        execution_uncertainty: Decimal,
        temporal_uncertainty: Decimal
    ) -> str:
        """Identify the dominant source of uncertainty."""
        uncertainties = {
            'model': model_uncertainty,
            'data': data_uncertainty,
            'market': market_uncertainty,
            'execution': execution_uncertainty,
            'temporal': temporal_uncertainty
        }
        
        return max(uncertainties, key=uncertainties.get)


class RiskClassifier:
    """
    Main risk classification engine for arbitrage opportunities.
    
    Provides comprehensive multi-dimensional risk analysis including market volatility,
    bookmaker reliability, liquidity depth, execution difficulty, timing sensitivity,
    confidence scoring, and uncertainty quantification.
    """
    
    def __init__(self):
        """Initialize the risk classifier."""
        self.logger = logging.getLogger(__name__)
        self.risk_calculator = RiskCalculator()
        
        # Initialize component analyzers
        self.volatility_analyzer = MarketVolatilityAnalyzer(self.risk_calculator)
        self.reliability_scorer = BookmakerReliabilityScorer()
        self.liquidity_analyzer = LiquidityDepthAnalyzer()
        self.execution_assessor = ExecutionDifficultyAssessor()
        self.timing_analyzer = TimingSensitivityAnalyzer()
        self.confidence_scorer = ConfidenceScorer()
        self.uncertainty_quantifier = UncertaintyQuantifier()
        
        # Cache for performance
        self.classification_cache = {}
        self.max_cache_size = 1000
        
        # Risk thresholds
        self.risk_thresholds = {
            'tier_a_max_risk_score': '0.25',
            'tier_b_max_risk_score': '0.50',
            'tier_c_max_risk_score': '0.75',
            'minimum_confidence_threshold': '0.60'
        }
    
    def classify_arbitrage_risk(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None,
        historical_data: Optional[Dict[str, Any]] = None,
        user_risk_tolerance: Optional[str] = None
    ) -> RiskClassificationResult:
        """
        Perform comprehensive risk classification for arbitrage opportunity.
        
        Args:
            opportunity: Arbitrage opportunity to classify
            market_data: Market context data
            historical_data: Historical performance data
            user_risk_tolerance: User's risk tolerance preference
            
        Returns:
            RiskClassificationResult with comprehensive risk assessment
        """
        self.logger.info(f"Classifying risk for opportunity: {opportunity.id}")
        
        # Check cache first
        cache_key = self._generate_cache_key(opportunity, market_data)
        if cache_key in self.classification_cache:
            self.logger.info("Returning cached classification result")
            return self.classification_cache[cache_key]
        
        try:
            # Perform comprehensive analysis
            component_scores = self._analyze_risk_components(
                opportunity, market_data, historical_data
            )
            
            # Calculate risk factor analysis
            risk_factor_analysis = self._analyze_risk_factors(
                opportunity, market_data, historical_data
            )
            
            # Perform detailed analysis
            profitability_analysis = self._analyze_profitability(opportunity, market_data)
            liquidity_analysis = self._analyze_liquidity(opportunity, market_data)
            execution_analysis = self._analyze_execution(opportunity, market_data)
            timing_analysis = self._analyze_timing(opportunity, market_data)
            market_analysis = self._analyze_market_conditions(opportunity, market_data)
            
            # Calculate composite risk score
            composite_risk_score = self._calculate_composite_risk_score(
                component_scores, opportunity
            )
            
            # Determine appropriate tier
            assigned_tier = self._determine_risk_tier(
                composite_risk_score, user_risk_tolerance
            )
            
            # Validate tier criteria
            tier_criteria_met, tier_violations = self._validate_tier_criteria(
                opportunity, assigned_tier
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                component_scores, composite_risk_score, assigned_tier, opportunity
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_overall_confidence(
                opportunity, component_scores, market_data, historical_data
            )
            
            # Quantify uncertainty
            uncertainty_metrics = self.uncertainty_quantifier.quantify_uncertainty(
                opportunity, market_data
            )
            
            # Create comprehensive result
            result = RiskClassificationResult(
                opportunity_id=str(opportunity.id),
                assigned_tier=assigned_tier,
                composite_risk_score=composite_risk_score,
                confidence_score=confidence_score,
                component_scores=component_scores,
                risk_factor_analysis=risk_factor_analysis,
                profitability_analysis=profitability_analysis,
                liquidity_analysis=liquidity_analysis,
                execution_analysis=execution_analysis,
                timing_analysis=timing_analysis,
                market_analysis=market_analysis,
                tier_criteria_met=tier_criteria_met,
                tier_violations=tier_violations,
                recommendations=recommendations,
                model_uncertainty=uncertainty_metrics['model_uncertainty'],
                data_uncertainty=uncertainty_metrics['data_uncertainty'],
                market_uncertainty=uncertainty_metrics['market_uncertainty'],
                total_uncertainty=uncertainty_metrics['total_uncertainty'],
                calculation_details={
                    'analysis_timestamp': datetime.utcnow(),
                    'market_data_available': market_data is not None,
                    'historical_data_available': historical_data is not None,
                    'user_risk_tolerance': user_risk_tolerance
                }
            )
            
            # Cache result
            self._cache_classification_result(cache_key, result)
            
            self.logger.info(f"Risk classification completed. Tier: {assigned_tier}, Score: {composite_risk_score}")
            return result
            
        except Exception as e:
            self.logger.error(f"Risk classification failed: {e}")
            raise
    
    def _analyze_risk_components(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> List[RiskComponentScore]:
        """Analyze all risk components."""
        component_scores = []
        
        # 1. Market volatility analysis
        try:
            if market_data and 'returns' in market_data:
                volatility_metrics = self.volatility_analyzer.analyze_market_volatility(
                    market_data['returns'], market_data
                )
            else:
                # Use default assumptions
                volatility_metrics = MarketVolatilityMetrics(
                    historical_volatility='0.2',
                    implied_volatility='0.22',
                    volatility_rank='0.5',
                    volatility_trend="stable",
                    regime_classification=MarketCondition.NORMAL,
                    volatility_percentile='0.5',
                    correlation_volatility='0.1',
                    tail_risk_indicator='0.3'
                )
            
            volatility_score = self._calculate_volatility_score(volatility_metrics)
            component_scores.append(RiskComponentScore(
                component=RiskComponent.MARKET_VOLATILITY,
                score=volatility_score,
                weight='0.20',
                confidence='0.8',
                factors={RiskFactor.VOLATILITY_SCORE: volatility_score},
                explanation=f"Market volatility score: {volatility_score:.3f}"
            ))
        except Exception as e:
            self.logger.warning(f"Volatility analysis failed: {e}")
        
        # 2. Bookmaker reliability analysis
        try:
            reliability_scores = []
            for leg in opportunity.legs:
                metrics = self.reliability_scorer.score_bookmaker_reliability(
                    leg.bookmaker, historical_data
                )
                reliability_scores.append(metrics.rating_score)
            
            avg_reliability = sum(reliability_scores) / len(reliability_scores)
            component_scores.append(RiskComponentScore(
                component=RiskComponent.BOOKMAKER_RELIABILITY,
                score=avg_reliability,
                weight='0.20',
                confidence='0.9',
                factors={RiskFactor.BOOKMAKER_RATING: avg_reliability},
                explanation=f"Average bookmaker reliability: {avg_reliability:.3f}"
            ))
        except Exception as e:
            self.logger.warning(f"Reliability analysis failed: {e}")
        
        # 3. Liquidity depth analysis
        try:
            liquidity_metrics = self.liquidity_analyzer.analyze_liquidity_depth(
                opportunity, market_data
            )
            liquidity_score = self._calculate_liquidity_score(liquidity_metrics)
            component_scores.append(RiskComponentScore(
                component=RiskComponent.LIQUIDITY_DEPTH,
                score=liquidity_score,
                weight='0.20',
                confidence='0.75',
                factors={
                    RiskFactor.LIQUIDITY_SCORE: liquidity_score,
                    'market_depth': liquidity_metrics.market_depth,
                    'fill_probability': liquidity_metrics.fill_probability
                },
                explanation=f"Liquidity depth score: {liquidity_score:.3f}"
            ))
        except Exception as e:
            self.logger.warning(f"Liquidity analysis failed: {e}")
        
        # 4. Execution difficulty assessment
        try:
            execution_metrics = self.execution_assessor.assess_execution_difficulty(
                opportunity
            )
            execution_difficulty = execution_metrics['total_difficulty_score']
            execution_score = '1.0' - execution_difficulty  # Convert difficulty to reliability
            component_scores.append(RiskComponentScore(
                component=RiskComponent.EXECUTION_DIFFICULTY,
                score=execution_score,
                weight='0.15',
                confidence='0.7',
                factors={
                    RiskFactor.EXECUTION_TIME: execution_metrics['base_execution_time'],
                    'coordination_complexity': execution_metrics['coordination_complexity'],
                    'timing_sensitivity': execution_metrics['timing_sensitivity']
                },
                explanation=f"Execution feasibility score: {execution_score:.3f}"
            ))
        except Exception as e:
            self.logger.warning(f"Execution assessment failed: {e}")
        
        # 5. Timing sensitivity analysis
        try:
            timing_metrics = self.timing_analyzer.analyze_timing_sensitivity(
                opportunity
            )
            timing_score = '1.0' - timing_metrics['timing_risk_score']
            component_scores.append(RiskComponentScore(
                component=RiskComponent.TIMING_SENSITIVITY,
                score=timing_score,
                weight='0.10',
                confidence='0.6',
                factors={
                    RiskFactor.TIME_TO_EVENT: self._calculate_time_to_event(opportunity),
                    'urgency_level': timing_metrics['urgency_level'],
                    'deadline_pressure': timing_metrics['deadline_pressure']
                },
                explanation=f"Timing reliability score: {timing_score:.3f}"
            ))
        except Exception as e:
            self.logger.warning(f"Timing analysis failed: {e}")
        
        # 6. Odds stability analysis
        try:
            odds_score = self._analyze_odds_stability(opportunity, market_data)
            component_scores.append(RiskComponentScore(
                component=RiskComponent.ODDS_STABILITY,
                score=odds_score,
                weight='0.10',
                confidence='0.8',
                factors={
                    RiskFactor.ODDS_DEVIATION: self._calculate_odds_deviation(opportunity),
                    'odds_freshness': self._calculate_odds_freshness_score(opportunity)
                },
                explanation=f"Odds stability score: {odds_score:.3f}"
            ))
        except Exception as e:
            self.logger.warning(f"Odds stability analysis failed: {e}")
        
        # 7. Diversification analysis
        try:
            diversification_score = self._analyze_diversification(opportunity)
            component_scores.append(RiskComponentScore(
                component=RiskComponent.DIVERSIFICATION,
                score=diversification_score,
                weight='0.03',
                confidence='0.9',
                factors={'bookmaker_diversity': diversification_score},
                explanation=f"Portfolio diversification score: {diversification_score:.3f}"
            ))
        except Exception as e:
            self.logger.warning(f"Diversification analysis failed: {e}")
        
        # 8. Correlation risk analysis
        try:
            correlation_score = self._analyze_correlation_risk(opportunity, market_data)
            component_scores.append(RiskComponentScore(
                component=RiskComponent.CORRELATION_RISK,
                score=correlation_score,
                weight='0.02',
                confidence='0.7',
                factors={'correlation_coefficient': correlation_score},
                explanation=f"Correlation risk score: {correlation_score:.3f}"
            ))
        except Exception as e:
            self.logger.warning(f"Correlation analysis failed: {e}")
        
        return component_scores
    
    def _analyze_risk_factors(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[RiskFactor, RiskFactorAnalysis]:
        """Perform detailed risk factor analysis."""
        risk_factors = {}
        
        # Profit margin factor
        profit_margin_score = min(opportunity.profit_margin / '0.05', '1.0')
        risk_factors[RiskFactor.PROFIT_MARGIN] = RiskFactorAnalysis(
            factor=RiskFactor.PROFIT_MARGIN,
            value=opportunity.profit_margin,
            normalized_score=profit_margin_score,
            percentile_rank='0.7',  # Would be calculated from historical data
            trend_direction="stable",
            volatility='0.02',
            confidence_interval=(opportunity.profit_margin - '0.01', opportunity.profit_margin + '0.01')
        )
        
        # Liquidity score factor
        liquidity_score = self._estimate_liquidity_score(opportunity, market_data)
        risk_factors[RiskFactor.LIQUIDITY_SCORE] = RiskFactorAnalysis(
            factor=RiskFactor.LIQUIDITY_SCORE,
            value=liquidity_score,
            normalized_score=liquidity_score,
            percentile_rank='0.6',
            trend_direction="stable",
            volatility='0.1',
            confidence_interval=(liquidity_score - '0.1', liquidity_score + '0.1')
        )
        
        # Bookmaker rating factor
        avg_rating = self._calculate_average_bookmaker_rating(opportunity)
        risk_factors[RiskFactor.BOOKMAKER_RATING] = RiskFactorAnalysis(
            factor=RiskFactor.BOOKMAKER_RATING,
            value=avg_rating,
            normalized_score=avg_rating / '10',  # Normalize to 0-1
            percentile_rank='0.8',
            trend_direction="stable",
            volatility='0.2',
            confidence_interval=(avg_rating - '1.0', avg_rating + '1.0')
        )
        
        # Execution time factor
        execution_time = self._estimate_execution_time(opportunity)
        risk_factors[RiskFactor.EXECUTION_TIME] = RiskFactorAnalysis(
            factor=RiskFactor.EXECUTION_TIME,
            value=execution_time,
            normalized_score=max('0.0', '1.0' - execution_time / '120'),  # 2 min max
            percentile_rank='0.5',
            trend_direction="stable",
            volatility='0.2',
            confidence_interval=(execution_time - '30', execution_time + '30')
        )
        
        # Odds deviation factor
        odds_deviation = self._calculate_odds_deviation(opportunity)
        risk_factors[RiskFactor.ODDS_DEVIATION] = RiskFactorAnalysis(
            factor=RiskFactor.ODDS_DEVIATION,
            value=odds_deviation,
            normalized_score=max('0.0', '1.0' - odds_deviation / '0.05'),
            percentile_rank='0.4',
            trend_direction="stable",
            volatility='0.01',
            confidence_interval=(odds_deviation - '0.005', odds_deviation + '0.005')
        )
        
        # Volatility score factor
        volatility_score = self._estimate_volatility_score(opportunity, market_data)
        risk_factors[RiskFactor.VOLATILITY_SCORE] = RiskFactorAnalysis(
            factor=RiskFactor.VOLATILITY_SCORE,
            value=volatility_score,
            normalized_score=volatility_score,
            percentile_rank='0.5',
            trend_direction="stable",
            volatility='0.05',
            confidence_interval=(volatility_score - '0.05', volatility_score + '0.05')
        )
        
        # Confidence level factor
        confidence_metrics = self.confidence_scorer.calculate_confidence_score(opportunity, market_data)
        confidence_level = confidence_metrics['overall_confidence']
        risk_factors[RiskFactor.CONFIDENCE_LEVEL] = RiskFactorAnalysis(
            factor=RiskFactor.CONFIDENCE_LEVEL,
            value=confidence_level,
            normalized_score=confidence_level,
            percentile_rank='0.7',
            trend_direction="stable",
            volatility='0.1',
            confidence_interval=confidence_metrics['confidence_interval']
        )
        
        return risk_factors
    
    def _calculate_composite_risk_score(
        self,
        component_scores: List[RiskComponentScore],
        opportunity: ArbitrageOpportunity
    ) -> Decimal:
        """Calculate composite risk score from components."""
        if not component_scores:
            return '0.5'  # Default moderate risk
        
        # Calculate weighted average (lower scores = higher risk, so we invert)
        total_weight = sum(score.weight for score in component_scores)
        weighted_score = sum(
            ('1.0' - score.score) * score.weight * score.confidence
            for score in component_scores
        )
        
        # Normalize by total weight
        composite_score = weighted_score / total_weight
        
        return min(composite_score, '1.0')
    
    def _determine_risk_tier(
        self,
        composite_risk_score: Decimal,
        user_risk_tolerance: Optional[str] = None
    ) -> str:
        """Determine appropriate risk tier based on score and user preference."""
        # Use user preference if provided
        if user_risk_tolerance:
            tolerance_mapping = {
                'conservative': 'tier_a',
                'moderate': 'tier_b',
                'aggressive': 'tier_c',
                'institutional': 'tier_a'
            }
            preferred_tier = tolerance_mapping.get(user_risk_tolerance.lower(), 'tier_b')
            
            # Check if user's preferred tier is appropriate
            tier_scores = {
                'tier_a': self.risk_thresholds['tier_a_max_risk_score'],
                'tier_b': self.risk_thresholds['tier_b_max_risk_score'],
                'tier_c': self.risk_thresholds['tier_c_max_risk_score']
            }
            
            max_allowed_score = tier_scores.get(preferred_tier, '0.5')
            if composite_risk_score <= max_allowed_score:
                return preferred_tier
        
        # Default tier determination based on score
        if composite_risk_score <= self.risk_thresholds['tier_a_max_risk_score']:
            return 'tier_a'
        elif composite_risk_score <= self.risk_thresholds['tier_b_max_risk_score']:
            return 'tier_b'
        elif composite_risk_score <= self.risk_thresholds['tier_c_max_risk_score']:
            return 'tier_c'
        else:
            return 'tier_d'
    
    def _validate_tier_criteria(
        self,
        opportunity: ArbitrageOpportunity,
        assigned_tier: str
    ) -> Tuple[Dict[str, bool], List[str]]:
        """Validate that opportunity meets assigned tier criteria."""
        tier_definition = get_tier_definition(assigned_tier)
        if not tier_definition:
            return {}, ["Invalid tier assignment"]
        
        criteria = tier_definition.criteria
        met_criteria = {}
        violations = []
        
        # Validate profit margin
        if opportunity.profit_margin >= criteria.min_profit_margin:
            met_criteria['profit_margin'] = True
        else:
            met_criteria['profit_margin'] = False
            violations.append(f"Profit margin {opportunity.profit_margin:.3f} below minimum {criteria.min_profit_margin:.3f}")
        
        # Validate number of bookmakers
        unique_bookmakers = len(set(leg.bookmaker for leg in opportunity.legs))
        if unique_bookmakers >= criteria.required_bookmaker_count:
            met_criteria['bookmaker_count'] = True
        else:
            met_criteria['bookmaker_count'] = False
            violations.append(f"Only {unique_bookmakers} bookmakers, minimum required: {criteria.required_bookmaker_count}")
        
        # Validate time to event
        time_to_event = opportunity.event_date - datetime.utcnow()
        if time_to_event >= criteria.min_time_to_event:
            met_criteria['time_to_event'] = True
        else:
            met_criteria['time_to_event'] = False
            violations.append(f"Time to event {time_to_event} below minimum {criteria.min_time_to_event}")
        
        # Validate position size (simplified check)
        if opportunity.total_stake <= criteria.max_position_size:
            met_criteria['position_size'] = True
        else:
            met_criteria['position_size'] = False
            violations.append(f"Position size {opportunity.total_stake} exceeds maximum {criteria.max_position_size}")
        
        return met_criteria, violations
    
    def _generate_recommendations(
        self,
        component_scores: List[RiskComponentScore],
        composite_risk_score: Decimal,
        assigned_tier: str,
        opportunity: ArbitrageOpportunity
    ) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # General recommendations based on tier
        if assigned_tier == 'tier_d':
            recommendations.append("Consider reducing position size due to high risk profile")
            recommendations.append("Implement additional monitoring and risk controls")
        
        # Component-specific recommendations
        for score in component_scores:
            if score.score < '0.6':  # Poor performance
                if score.component == RiskComponent.MARKET_VOLATILITY:
                    recommendations.append("Monitor market volatility closely; consider hedging")
                elif score.component == RiskComponent.BOOKMAKER_RELIABILITY:
                    recommendations.append("Verify bookmaker reliability before execution")
                elif score.component == RiskComponent.LIQUIDITY_DEPTH:
                    recommendations.append("Ensure adequate market depth before placing large orders")
                elif score.component == RiskComponent.EXECUTION_DIFFICULTY:
                    recommendations.append("Prepare for potential execution challenges")
        
        # Profit margin recommendations
        if opportunity.profit_margin < '0.02':  # Less than 2%
            recommendations.append("Low profit margin - ensure efficient execution to maintain profitability")
        
        # Time-sensitive recommendations
        time_to_event = opportunity.event_date - datetime.utcnow()
        if time_to_event.total_seconds() < 3600:  # Less than 1 hour
            recommendations.append("High urgency - execute promptly")
        
        return recommendations
    
    def _calculate_overall_confidence(
        self,
        opportunity: ArbitrageOpportunity,
        component_scores: List[RiskComponentScore],
        market_data: Optional[Dict[str, Any]] = None,
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Decimal:
        """Calculate overall confidence score."""
        # Use confidence scorer for comprehensive confidence calculation
        confidence_metrics = self.confidence_scorer.calculate_confidence_score(
            opportunity, market_data, historical_data
        )
        return confidence_metrics['overall_confidence']
    
    def _generate_cache_key(
        self,
        opportunity: ArbitrageOpportunity,
        market_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate cache key for classification result."""
        # Use opportunity ID and data hash
        base_key = str(opportunity.id)
        
        if market_data:
            # Create hash of market data (simplified)
            data_str = str(sorted(market_data.items()))
            data_hash = hash(data_str) % 1000000
            return f"{base_key}_{data_hash}"
        
        return base_key
    
    def _cache_classification_result(self, cache_key: str, result: RiskClassificationResult):
        """Cache classification result for performance."""
        if len(self.classification_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.classification_cache))
            del self.classification_cache[oldest_key]
        
        self.classification_cache[cache_key] = result
    
    def clear_cache(self):
        """Clear the classification cache."""
        self.classification_cache.clear()
        self.logger.info("Risk classification cache cleared")
    
    # Helper methods for component analysis
    
    def _calculate_volatility_score(self, metrics: MarketVolatilityMetrics) -> Decimal:
        """Calculate volatility score (higher = less risky)."""
        # Invert volatility score (lower volatility = higher score)
        vol_score = '1.0' - min(metrics.historical_volatility / '0.5', '1.0')
        
        # Adjust for regime
        regime_multipliers = {
            MarketCondition.CALM: '1.2',
            MarketCondition.NORMAL: '1.0',
            MarketCondition.VOLATILE: '0.7',
            MarketCondition.STRESSED: '0.4',
            MarketCondition.EMERGENCY: '0.2'
        }
        
        multiplier = regime_multipliers.get(metrics.regime_classification, '1.0')
        return min(vol_score * multiplier, '1.0')
    
    def _calculate_liquidity_score(self, metrics: LiquidityDepthMetrics) -> Decimal:
        """Calculate liquidity score."""
        # Base score from fill probability
        fill_score = metrics.fill_probability
        
        # Adjust for market depth (normalized)
        depth_score = min(metrics.market_depth / '20000', '1.0')
        
        # Adjust for spread (inverted - tighter spreads = higher score)
        spread_score = max('0.0', '1.0' - metrics.bid_ask_spread / '0.05')
        
        # Weighted average
        liquidity_score = (
            fill_score * '0.5' +
            depth_score * '0.3' +
            spread_score * '0.2'
        )
        
        return min(liquidity_score, '1.0')
    
    def _analyze_odds_stability(self, opportunity: ArbitrageOpportunity, market_data: Optional[Dict[str, Any]]) -> Decimal:
        """Analyze odds stability."""
        # Base stability score
        base_stability = '0.8'
        
        # Adjust for odds freshness
        time_since_update = datetime.utcnow() - opportunity.odds_freshness
        if time_since_update.total_seconds() < 300:  # Less than 5 minutes
            freshness_bonus = '0.1'
        elif time_since_update.total_seconds() < 1800:  # Less than 30 minutes
            freshness_bonus = '0.05'
        else:
            freshness_bonus = '0.0'
        
        return min(base_stability + freshness_bonus, '1.0')
    
    def _analyze_diversification(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Analyze diversification score."""
        unique_bookmakers = len(set(leg.bookmaker for leg in opportunity.legs))
        total_legs = len(opportunity.legs)
        
        if total_legs == 0:
            return '0.0'
        
        diversity_ratio = unique_bookmakers / total_legs
        return min(diversity_ratio, '1.0')
    
    def _analyze_correlation_risk(self, opportunity: ArbitrageOpportunity, market_data: Optional[Dict[str, Any]]) -> Decimal:
        """Analyze correlation risk (simplified)."""
        # Assume low correlation risk for different bookmakers
        unique_bookmakers = len(set(leg.bookmaker for leg in opportunity.legs))
        
        if unique_bookmakers <= 2:
            return '0.3'  # Higher correlation risk
        elif unique_bookmakers <= 3:
            return '0.6'  # Medium correlation risk
        else:
            return '0.9'  # Low correlation risk
    
    def _analyze_profitability(self, opportunity: ArbitrageOpportunity, market_data: Optional[Dict[str, Any]]) -> Dict[str, Decimal]:
        """Analyze profitability aspects."""
        return {
            'profit_margin': opportunity.profit_margin,
            'profit_amount': opportunity.profit_amount,
            'guaranteed_profit': '1.0' if opportunity.guaranteed_profit else '0.0',
            'margin_quality_score': min(opportunity.profit_margin / '0.05', '1.0')
        }
    
    def _analyze_liquidity(self, opportunity: ArbitrageOpportunity, market_data: Optional[Dict[str, Any]]) -> Dict[str, Decimal]:
        """Analyze liquidity aspects."""
        return {
            'market_depth_estimate': self._estimate_market_depth(opportunity),
            'position_size_ratio': opportunity.total_stake / '10000',
            'liquidity_score': self._estimate_liquidity_score(opportunity, market_data),
            'slippage_risk': self._estimate_slippage_risk(opportunity)
        }
    
    def _analyze_execution(self, opportunity: ArbitrageOpportunity, market_data: Optional[Dict[str, Any]]) -> Dict[str, Decimal]:
        """Analyze execution aspects."""
        execution_metrics = self.execution_assessor.assess_execution_difficulty(opportunity)
        return {
            'execution_time_estimate': execution_metrics['base_execution_time'],
            'coordination_complexity': execution_metrics['coordination_complexity'],
            'technical_risk': execution_metrics['technical_risk'],
            'execution_feasibility': '1.0' - execution_metrics['total_difficulty_score']
        }
    
    def _analyze_timing(self, opportunity: ArbitrageOpportunity, market_data: Optional[Dict[str, Any]]) -> Dict[str, Decimal]:
        """Analyze timing aspects."""
        timing_metrics = self.timing_analyzer.analyze_timing_sensitivity(opportunity)
        return {
            'time_to_event': self._calculate_time_to_event(opportunity),
            'urgency_level': timing_metrics['urgency_level'],
            'timing_risk': timing_metrics['timing_risk_score'],
            'execution_window': timing_metrics['optimal_execution_window']
        }
    
    def _analyze_market_conditions(self, opportunity: ArbitrageOpportunity, market_data: Optional[Dict[str, Any]]) -> Dict[str, Decimal]:
        """Analyze market conditions."""
        return {
            'volatility_estimate': self._estimate_volatility_score(opportunity, market_data),
            'market_stress_level': self._estimate_market_stress(opportunity, market_data),
            'liquidity_regime': '0.7',  # Default
            'correlation_environment': '0.5'  # Default
        }
    
    # Additional helper methods
    def _calculate_time_to_event(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Calculate time to event in hours."""
        time_to_event = opportunity.event_date - datetime.utcnow()
        return str(max(0, time_to_event.total_seconds() / 3600))
    
    def _calculate_odds_deviation(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Calculate estimated odds deviation."""
        # Simplified calculation based on profit margin
        return opportunity.profit_margin * Decimal('0.1')  # Assume 10% of margin as deviation
    
    def _calculate_odds_freshness_score(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Calculate odds freshness score."""
        time_since_update = datetime.utcnow() - opportunity.odds_freshness
        minutes_old = time_since_update.total_seconds() / 60
        
        if minutes_old <= 5:
            return '1.0'
        elif minutes_old <= 30:
            return '0.8'
        elif minutes_old <= 120:
            return '0.6'
        else:
            return '0.4'
    
    def _calculate_average_bookmaker_rating(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Calculate average bookmaker rating."""
        ratings = []
        for leg in opportunity.legs:
            bookmaker_ratings = {
                'pinnacle': '8.5',
                'betfair': '8.2',
                'william_hill': '7.8',
                'ladbrokes': '7.5',
                'bet365': '8.0',
                'unibet': '7.6',
                'betway': '7.3',
                '888sport': '7.2'
            }
            
            name_lower = leg.bookmaker.lower().replace(' ', '_')
            rating = bookmaker_ratings.get(name_lower, '7.0')
            ratings.append(rating)
        
        return sum(ratings) / len(ratings) if ratings else '7.0'
    
    def _estimate_execution_time(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Estimate execution time in seconds."""
        base_time = len(opportunity.legs) * '5'  # 5 seconds per leg
        coordination_overhead = '10'  # 10 seconds coordination
        return base_time + coordination_overhead
    
    def _estimate_liquidity_score(self, opportunity: ArbitrageOpportunity, market_data: Optional[Dict[str, Any]]) -> Decimal:
        """Estimate liquidity score."""
        if market_data and 'liquidity_score' in market_data:
            return market_data['liquidity_score']
        
        # Base assumption
        return '0.7'
    
    def _estimate_volatility_score(self, opportunity: ArbitrageOpportunity, market_data: Optional[Dict[str, Any]]) -> Decimal:
        """Estimate volatility score."""
        if market_data and 'volatility' in market_data:
            return market_data['volatility']
        
        # Base assumption
        return '0.2'
    
    def _estimate_market_depth(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Estimate market depth."""
        base_depth = '5000'
        margin_adjustment = opportunity.profit_margin / '0.02'
        return base_depth * margin_adjustment
    
    def _estimate_slippage_risk(self, opportunity: ArbitrageOpportunity) -> Decimal:
        """Estimate slippage risk."""
        return min(opportunity.profit_margin * '0.1', '0.05')
    
    def _estimate_market_stress(self, opportunity: ArbitrageOpportunity, market_data: Optional[Dict[str, Any]]) -> Decimal:
        """Estimate market stress level."""
        if market_data and 'market_stress' in market_data:
            return market_data['market_stress']
        
        # Base assumption
        return '0.3'


# Create logger instance
logger = logging.getLogger(__name__)