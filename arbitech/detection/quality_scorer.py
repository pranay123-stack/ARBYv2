"""
Comprehensive Quality Scoring System

Advanced quality assessment system that evaluates arbitrage opportunities across
multiple dimensions including reliability, profit stability, execution complexity,
market conditions, and historical performance metrics.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
import statistics
import math
from collections import defaultdict, deque

from ..storage.models import ArbitrageOpportunity, ArbitrageLeg, RiskTier, Sport


logger = logging.getLogger(__name__)


class QualityLevel(str, Enum):
    """Quality level classifications."""
    EXCELLENT = "excellent"
    VERY_GOOD = "very_good"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    VERY_POOR = "very_poor"


class ReliabilityScore(str, Enum):
    """Reliability score categories."""
    HIGHLY_RELIABLE = "highly_reliable"
    RELIABLE = "reliable"
    MODERATELY_RELIABLE = "moderately_reliable"
    UNRELIABLE = "unreliable"
    VERY_UNRELIABLE = "very_unreliable"


@dataclass
class QualityDimension:
    """Individual quality dimension score."""
    name: str
    score: float
    weight: float
    max_score: float = 100.0
    explanation: str = ""
    confidence: float = 1.0
    
    @property
    def normalized_score(self) -> float:
        """Get score normalized to 0-1 range."""
        return self.score / self.max_score if self.max_score > 0 else 0.0
    
    @property
    def weighted_score(self) -> float:
        """Get weighted contribution to overall quality."""
        return self.normalized_score * self.weight


@dataclass
class QualityAssessment:
    """Complete quality assessment for an opportunity."""
    opportunity_id: str
    overall_quality_score: float
    quality_level: QualityLevel
    
    # Dimension scores
    reliability_score: QualityDimension
    profit_stability_score: QualityDimension
    execution_complexity_score: QualityDimension
    market_conditions_score: QualityDimension
    historical_performance_score: QualityDimension
    
    # Aggregated scores
    weighted_dimensions: List[QualityDimension]
    unweighted_average: float
    
    # Assessment metadata
    assessed_at: datetime
    assessment_version: str = "1.0"
    confidence_level: float = 1.0
    
    # Detailed explanations
    summary: str = ""
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []


class BaseQualityScorer(ABC):
    """Abstract base class for quality scorers."""
    
    @abstractmethod
    def calculate_score(self, opportunity: ArbitrageOpportunity, context: Optional[Dict[str, Any]] = None) -> QualityDimension:
        """Calculate quality score for a dimension."""
        pass
    
    @abstractmethod
    def get_explanation(self, score: float, opportunity: ArbitrageOpportunity) -> str:
        """Generate explanation for the score."""
        pass


class ReliabilityScorer(BaseQualityScorer):
    """Scores the reliability of an arbitrage opportunity."""
    
    def __init__(self):
        self.bookmaker_reliability_cache: Dict[str, float] = {}
    
    def calculate_score(self, opportunity: ArbitrageOpportunity, context: Optional[Dict[str, Any]] = None) -> QualityDimension:
        """Calculate reliability score (0-100)."""
        details = {}
        
        # Bookmaker reliability score (0-40 points)
        bookmaker_scores = []
        for leg in opportunity.legs:
            reliability = self._get_bookmaker_reliability(leg.bookmaker)
            bookmaker_scores.append(reliability)
        
        avg_bookmaker_reliability = statistics.mean(bookmaker_scores) if bookmaker_scores else 0.0
        details['avg_bookmaker_reliability'] = avg_bookmaker_reliability
        
        # Risk tier reliability (0-30 points)
        tier_reliability = {
            RiskTier.TIER_A: 30.0,
            RiskTier.TIER_B: 22.5,
            RiskTier.TIER_C: 15.0,
            RiskTier.TIER_D: 7.5
        }
        tier_score = tier_reliability.get(opportunity.risk_tier, 0.0)
        details['tier_score'] = tier_score
        details['risk_tier'] = opportunity.risk_tier.value
        
        # Liquidity verification score (0-20 points)
        liquidity_score = 20.0 if opportunity.liquidity_checked else 5.0
        details['liquidity_verified'] = opportunity.liquidity_checked
        
        # Odds freshness score (0-10 points)
        freshness_score = self._calculate_freshness_score(opportunity)
        details['freshness_score'] = freshness_score
        
        total_score = min(100.0, avg_bookmaker_reliability * 0.4 + tier_score + liquidity_score + freshness_score)
        
        explanation = self.get_explanation(total_score, opportunity)
        
        return QualityDimension(
            name="reliability",
            score=total_score,
            weight=0.25,
            explanation=explanation,
            confidence=self._calculate_confidence(opportunity, details)
        )
    
    def _get_bookmaker_reliability(self, bookmaker: str) -> float:
        """Get reliability score for a bookmaker (0-100)."""
        # This would typically come from a database of historical performance
        # For now, using placeholder logic
        if bookmaker in self.bookmaker_reliability_cache:
            return self.bookmaker_reliability_cache[bookmaker]
        
        # Simulate reliability based on bookmaker characteristics
        reliability_map = {
            'bet365': 95.0,
            'william_hill': 90.0,
            'pinnacle': 95.0,
            'betfair': 92.0,
            'draftkings': 88.0,
            'fanduel': 85.0,
            'unibet': 82.0,
            'betway': 78.0
        }
        
        base_reliability = reliability_map.get(bookmaker.lower(), 75.0)
        
        # Add some randomization to simulate real-world variation
        import random
        reliability = max(0.0, min(100.0, base_reliability + random.uniform(-10, 10)))
        
        self.bookmaker_reliability_cache[bookmaker] = reliability
        return reliability
    
    def _calculate_freshness_score(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate score based on odds freshness."""
        age_minutes = (datetime.utcnow() - opportunity.odds_freshness).total_seconds() / 60
        
        if age_minutes <= 2:
            return 10.0
        elif age_minutes <= 5:
            return 8.0
        elif age_minutes <= 10:
            return 6.0
        elif age_minutes <= 30:
            return 4.0
        else:
            return 2.0
    
    def _calculate_confidence(self, opportunity: ArbitrageOpportunity, details: Dict[str, Any]) -> float:
        """Calculate confidence in the reliability assessment."""
        confidence_factors = []
        
        # Liquidity check increases confidence
        if details.get('liquidity_verified', False):
            confidence_factors.append(1.0)
        
        # Multiple bookmakers increase confidence
        unique_bookmakers = set(leg.bookmaker for leg in opportunity.legs)
        if len(unique_bookmakers) >= 3:
            confidence_factors.append(0.9)
        
        # Fresh odds increase confidence
        if details.get('freshness_score', 0) >= 8.0:
            confidence_factors.append(0.95)
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.5
    
    def get_explanation(self, score: float, opportunity: ArbitrageOpportunity) -> str:
        """Generate explanation for reliability score."""
        if score >= 85:
            return f"Highly reliable opportunity with trusted bookmakers and verified liquidity"
        elif score >= 70:
            return f"Good reliability with established bookmakers and appropriate risk level"
        elif score >= 55:
            return f"Moderate reliability - some uncertainty in bookmaker performance"
        else:
            return f"Low reliability - high risk tier or unverified liquidity"


class ProfitStabilityScorer(BaseQualityScorer):
    """Scores the stability and consistency of profit expectations."""
    
    def calculate_score(self, opportunity: ArbitrageOpportunity, context: Optional[Dict[str, Any]] = None) -> QualityDimension:
        """Calculate profit stability score (0-100)."""
        details = {}
        
        # Profit margin consistency (0-30 points)
        profit_consistency = self._calculate_profit_consistency(opportunity)
        details['profit_consistency'] = profit_consistency
        
        # Stake distribution balance (0-25 points)
        distribution_balance = self._calculate_distribution_balance(opportunity)
        details['distribution_balance'] = distribution_balance
        
        # Risk-adjusted return (0-25 points)
        risk_adjusted_return = self._calculate_risk_adjusted_return(opportunity)
        details['risk_adjusted_return'] = risk_adjusted_return
        
        # Market efficiency score (0-20 points)
        market_efficiency = self._calculate_market_efficiency(opportunity)
        details['market_efficiency'] = market_efficiency
        
        total_score = min(100.0, profit_consistency + distribution_balance + risk_adjusted_return + market_efficiency)
        
        explanation = self.get_explanation(total_score, opportunity)
        
        return QualityDimension(
            name="profit_stability",
            score=total_score,
            weight=0.25,
            explanation=explanation,
            confidence=self._calculate_stability_confidence(opportunity, details)
        )
    
    def _calculate_profit_consistency(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate profit consistency based on arbitrage structure."""
        profit_margin = float(opportunity.profit_margin)
        
        # Higher margins are generally less stable (more likely to attract competition)
        if profit_margin >= 0.08:  # 8%+
            return 15.0
        elif profit_margin >= 0.05:  # 5-8%
            return 25.0
        elif profit_margin >= 0.03:  # 3-5%
            return 30.0
        elif profit_margin >= 0.015:  # 1.5-3%
            return 28.0
        else:  # <1.5%
            return 20.0
    
    def _calculate_distribution_balance(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate how balanced the stake distribution is."""
        stake_percentages = [float(leg.stake_percentage) for leg in opportunity.legs]
        n_legs = len(stake_percentages)
        target_percentage = 1.0 / n_legs
        
        # Calculate variance from perfect balance
        variances = [(p - target_percentage)**2 for p in stake_percentages]
        avg_variance = statistics.mean(variances)
        
        # Convert variance to score (lower variance = higher score)
        max_variance = target_percentage**2  # Worst case scenario
        balance_score = max(0.0, 25.0 * (1.0 - (avg_variance / max_variance)))
        
        return balance_score
    
    def _calculate_risk_adjusted_return(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate risk-adjusted return score."""
        profit_margin = float(opportunity.profit_margin)
        
        # Risk-adjusted return varies by risk tier
        tier_adjustments = {
            RiskTier.TIER_A: 1.0,
            RiskTier.TIER_B: 0.9,
            RiskTier.TIER_C: 0.7,
            RiskTier.TIER_D: 0.5
        }
        
        adjustment = tier_adjustments.get(opportunity.risk_tier, 0.5)
        adjusted_return = profit_margin * adjustment
        
        # Score based on adjusted return
        if adjusted_return >= 0.04:
            return 25.0
        elif adjusted_return >= 0.025:
            return 20.0
        elif adjusted_return >= 0.015:
            return 15.0
        elif adjusted_return >= 0.01:
            return 10.0
        else:
            return 5.0
    
    def _calculate_market_efficiency(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate market efficiency score."""
        # More legs generally indicate more efficient markets
        leg_count = len(opportunity.legs)
        
        if leg_count >= 5:
            return 20.0
        elif leg_count == 4:
            return 18.0
        elif leg_count == 3:
            return 15.0
        else:  # 2 legs
            return 10.0
    
    def _calculate_stability_confidence(self, opportunity: ArbitrageOpportunity, details: Dict[str, Any]) -> float:
        """Calculate confidence in stability assessment."""
        confidence = 0.8  # Base confidence
        
        # Higher confidence for well-distributed opportunities
        if details.get('distribution_balance', 0) > 20.0:
            confidence += 0.1
        
        # Higher confidence for reasonable profit margins
        if 0.015 <= float(opportunity.profit_margin) <= 0.05:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def get_explanation(self, score: float, opportunity: ArbitrageOpportunity) -> str:
        """Generate explanation for profit stability score."""
        if score >= 80:
            return f"Highly stable profit with balanced distribution and optimal risk-reward"
        elif score >= 65:
            return f"Good profit stability with reasonable risk profile"
        elif score >= 50:
            return f"Moderate profit stability - some imbalance in distribution"
        else:
            return f"Low profit stability - high risk or poor distribution balance"


class ExecutionComplexityScorer(BaseQualityScorer):
    """Scores the complexity of executing the arbitrage opportunity."""
    
    def calculate_score(self, opportunity: ArbitrageOpportunity, context: Optional[Dict[str, Any]] = None) -> QualityDimension:
        """Calculate execution complexity score (0-100, higher = less complex)."""
        details = {}
        
        # Leg count complexity (0-40 points)
        leg_count = len(opportunity.legs)
        if leg_count == 2:
            leg_complexity_score = 40.0
        elif leg_count == 3:
            leg_complexity_score = 30.0
        else:  # 4+ legs
            leg_complexity_score = max(10.0, 40.0 - (leg_count - 3) * 5.0)
        
        details['leg_count_complexity'] = leg_complexity_score
        details['leg_count'] = leg_count
        
        # Market type complexity (0-25 points)
        market_complexity = {
            'match_winner': 25.0,
            'over_under': 20.0,
            'handicap': 18.0,
            'correct_score': 10.0,
            'first_goal': 15.0,
            'half_time': 12.0,
            'other': 8.0
        }
        market_score = market_complexity.get(opportunity.market_type.lower(), 10.0)
        details['market_complexity'] = market_score
        details['market_type'] = opportunity.market_type
        
        # Stake size complexity (0-20 points) - smaller stakes are easier
        total_stake = float(opportunity.total_stake)
        if total_stake <= 50:
            stake_complexity = 20.0
        elif total_stake <= 100:
            stake_complexity = 17.0
        elif total_stake <= 250:
            stake_complexity = 15.0
        elif total_stake <= 500:
            stake_complexity = 12.0
        elif total_stake <= 1000:
            stake_complexity = 8.0
        else:
            stake_complexity = 5.0
        
        details['stake_complexity'] = stake_complexity
        details['total_stake'] = total_stake
        
        # Time sensitivity complexity (0-15 points) - more time is less complex
        time_to_event = (opportunity.event_date - datetime.utcnow()).total_seconds() / 60
        if time_to_event >= 1440:  # 24+ hours
            time_complexity = 15.0
        elif time_to_event >= 180:  # 3+ hours
            time_complexity = 12.0
        elif time_to_event >= 60:  # 1+ hour
            time_complexity = 10.0
        elif time_to_event >= 30:  # 30+ minutes
            time_complexity = 7.0
        else:  # <30 minutes
            time_complexity = 3.0
        
        details['time_complexity'] = time_complexity
        details['time_to_event_minutes'] = time_to_event
        
        total_score = min(100.0, leg_complexity_score + market_score + stake_complexity + time_complexity)
        
        explanation = self.get_explanation(total_score, opportunity)
        
        return QualityDimension(
            name="execution_complexity",
            score=total_score,
            weight=0.20,
            explanation=explanation,
            confidence=self._calculate_execution_confidence(opportunity, details)
        )
    
    def _calculate_execution_confidence(self, opportunity: ArbitrageOpportunity, details: Dict[str, Any]) -> float:
        """Calculate confidence in execution complexity assessment."""
        confidence = 0.9  # Base confidence for execution complexity
        
        # Lower confidence for very complex scenarios
        if details.get('leg_count', 2) > 4:
            confidence -= 0.1
        
        # Lower confidence for very large stakes
        if details.get('total_stake', 0) > 1000:
            confidence -= 0.1
        
        return max(0.5, confidence)
    
    def get_explanation(self, score: float, opportunity: ArbitrageOpportunity) -> str:
        """Generate explanation for execution complexity score."""
        if score >= 80:
            return f"Simple execution with few legs and reasonable stake size"
        elif score >= 65:
            return f"Moderate complexity - manageable execution requirements"
        elif score >= 50:
            return f"Complex execution with multiple legs or large stakes"
        else:
            return f"Very complex execution - many legs and high stakes required"


class MarketConditionsScorer(BaseQualityScorer):
    """Scores the current market conditions affecting the opportunity."""
    
    def calculate_score(self, opportunity: ArbitrageOpportunity, context: Optional[Dict[str, Any]] = None) -> QualityDimension:
        """Calculate market conditions score (0-100)."""
        details = {}
        
        # Sport popularity score (0-25 points)
        sport_popularity = {
            Sport.FOOTBALL: 25.0,
            Sport.BASKETBALL: 22.0,
            Sport.TENNIS: 20.0,
            Sport.BASEBALL: 18.0,
            Sport.HOCKEY: 16.0,
            Sport.MMA: 15.0,
            Sport.CRICKET: 14.0,
            Sport.RUGBY: 12.0,
            Sport.GOLF: 10.0,
            Sport.BOXING: 8.0,
            Sport.ESPORTS: 12.0,
            Sport.POLITICS: 5.0,
            Sport.ENTERTAINMENT: 3.0
        }
        sport_score = sport_popularity.get(opportunity.sport, 10.0)
        details['sport_score'] = sport_score
        details['sport'] = opportunity.sport.value
        
        # Market liquidity score (0-25 points) - larger markets are more liquid
        market_liquidity = self._estimate_market_liquidity(opportunity)
        details['market_liquidity'] = market_liquidity
        
        # Competition level score (0-25 points) - less competition = better
        competition_level = self._estimate_competition_level(opportunity)
        competition_score = max(0.0, 25.0 - competition_level)
        details['competition_score'] = competition_score
        details['competition_level'] = competition_level
        
        # Market volatility score (0-25 points) - less volatility = better
        volatility_score = self._calculate_volatility_score(opportunity)
        details['volatility_score'] = volatility_score
        
        total_score = min(100.0, sport_score + market_liquidity + competition_score + volatility_score)
        
        explanation = self.get_explanation(total_score, opportunity)
        
        return QualityDimension(
            name="market_conditions",
            score=total_score,
            weight=0.15,
            explanation=explanation,
            confidence=self._calculate_market_confidence(opportunity, details)
        )
    
    def _estimate_market_liquidity(self, opportunity: ArbitrageOpportunity) -> float:
        """Estimate market liquidity score."""
        # Simulate liquidity based on market characteristics
        total_stake = float(opportunity.total_stake)
        leg_count = len(opportunity.legs)
        
        # Assume larger stakes indicate higher liquidity potential
        if total_stake >= 500:
            liquidity_score = 25.0
        elif total_stake >= 200:
            liquidity_score = 20.0
        elif total_stake >= 100:
            liquidity_score = 15.0
        elif total_stake >= 50:
            liquidity_score = 10.0
        else:
            liquidity_score = 5.0
        
        # Bonus for more bookmakers (indicates active market)
        if leg_count >= 4:
            liquidity_score += 3.0
        
        return min(25.0, liquidity_score)
    
    def _estimate_competition_level(self, opportunity: ArbitrageOpportunity) -> float:
        """Estimate competition level (0-25, higher = more competition)."""
        # Higher profit margins typically indicate less competition
        profit_margin = float(opportunity.profit_margin)
        
        if profit_margin >= 0.08:  # 8%+
            return 2.0  # Low competition
        elif profit_margin >= 0.05:  # 5-8%
            return 5.0
        elif profit_margin >= 0.03:  # 3-5%
            return 10.0
        elif profit_margin >= 0.015:  # 1.5-3%
            return 15.0
        else:  # <1.5%
            return 20.0  # High competition
    
    def _calculate_volatility_score(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate market volatility score."""
        # Time to event affects volatility
        time_to_event = (opportunity.event_date - datetime.utcnow()).total_seconds() / 60
        
        if time_to_event >= 1440:  # 24+ hours
            return 20.0  # Low volatility
        elif time_to_event >= 180:  # 3+ hours
            return 15.0
        elif time_to_event >= 60:  # 1+ hour
            return 12.0
        elif time_to_event >= 30:  # 30+ minutes
            return 8.0
        else:  # <30 minutes
            return 3.0  # High volatility
    
    def _calculate_market_confidence(self, opportunity: ArbitrageOpportunity, details: Dict[str, Any]) -> float:
        """Calculate confidence in market conditions assessment."""
        confidence = 0.7  # Base confidence for market conditions
        
        # Higher confidence for popular sports
        if opportunity.sport in [Sport.FOOTBALL, Sport.BASKETBALL, Sport.TENNIS]:
            confidence += 0.1
        
        # Lower confidence for very volatile situations
        if details.get('volatility_score', 0) < 10.0:
            confidence -= 0.1
        
        return max(0.4, confidence)
    
    def get_explanation(self, score: float, opportunity: ArbitrageOpportunity) -> str:
        """Generate explanation for market conditions score."""
        if score >= 80:
            return f"Excellent market conditions with high liquidity and low competition"
        elif score >= 65:
            return f"Good market conditions with favorable competitive landscape"
        elif score >= 50:
            return f"Moderate market conditions with average liquidity"
        else:
            return f"Challenging market conditions with high volatility or competition"


class HistoricalPerformanceScorer(BaseQualityScorer):
    """Scores opportunities based on historical performance data."""
    
    def __init__(self):
        self.performance_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
    
    def calculate_score(self, opportunity: ArbitrageOpportunity, context: Optional[Dict[str, Any]] = None) -> QualityDimension:
        """Calculate historical performance score (0-100)."""
        details = {}
        
        # Sport historical performance (0-30 points)
        sport_performance = self._get_sport_performance(opportunity.sport)
        details['sport_performance'] = sport_performance
        
        # Bookmaker historical success rate (0-30 points)
        bookmaker_performance = self._calculate_bookmaker_performance(opportunity.legs)
        details['bookmaker_performance'] = bookmaker_performance
        
        # Market type historical accuracy (0-25 points)
        market_performance = self._get_market_performance(opportunity.market_type)
        details['market_performance'] = market_performance
        
        # Risk tier historical outcomes (0-15 points)
        risk_performance = self._get_risk_performance(opportunity.risk_tier)
        details['risk_performance'] = risk_performance
        
        total_score = min(100.0, sport_performance + bookmaker_performance + market_performance + risk_performance)
        
        explanation = self.get_explanation(total_score, opportunity)
        
        return QualityDimension(
            name="historical_performance",
            score=total_score,
            weight=0.15,
            explanation=explanation,
            confidence=self._calculate_historical_confidence(opportunity, details)
        )
    
    def _get_sport_performance(self, sport: Sport) -> float:
        """Get historical performance score for sport."""
        # Historical success rates by sport (simulated)
        performance_data = {
            Sport.FOOTBALL: 85.0,
            Sport.BASKETBALL: 82.0,
            Sport.TENNIS: 78.0,
            Sport.BASEBALL: 75.0,
            Sport.HOCKEY: 72.0,
            Sport.MMA: 68.0,
            Sport.CRICKET: 70.0,
            Sport.RUGBY: 65.0,
            Sport.GOLF: 60.0,
            Sport.BOXING: 58.0,
            Sport.ESPORTS: 62.0,
            Sport.POLITICS: 45.0,
            Sport.ENTERTAINMENT: 40.0
        }
        
        return performance_data.get(sport, 60.0)
    
    def _calculate_bookmaker_performance(self, legs: List[ArbitrageLeg]) -> float:
        """Calculate historical performance based on bookmakers involved."""
        bookmaker_scores = []
        
        for leg in legs:
            # Simulate historical success rate for each bookmaker
            success_rate = self._get_bookmaker_success_rate(leg.bookmaker)
            bookmaker_scores.append(success_rate)
        
        return statistics.mean(bookmaker_scores) if bookmaker_scores else 50.0
    
    def _get_bookmaker_success_rate(self, bookmaker: str) -> float:
        """Get simulated historical success rate for a bookmaker."""
        # Base success rates by bookmaker (simulated)
        success_rates = {
            'bet365': 88.0,
            'william_hill': 85.0,
            'pinnacle': 90.0,
            'betfair': 87.0,
            'draftkings': 82.0,
            'fanduel': 80.0,
            'unibet': 78.0,
            'betway': 75.0
        }
        
        base_rate = success_rates.get(bookmaker.lower(), 70.0)
        
        # Add some variation based on cache
        cache_key = f"{bookmaker}_performance"
        if cache_key not in self.performance_cache:
            # Initialize with base rate
            recent_scores = [base_rate + (hash(f"{bookmaker}_{i}") % 20 - 10) for i in range(10)]
            self.performance_cache[cache_key].extend(recent_scores)
        
        return statistics.mean(self.performance_cache[cache_key])
    
    def _get_market_performance(self, market_type: str) -> float:
        """Get historical performance score for market type."""
        # Historical success rates by market type
        market_performance = {
            'match_winner': 82.0,
            'over_under': 78.0,
            'handicap': 75.0,
            'correct_score': 65.0,
            'first_goal': 72.0,
            'half_time': 68.0,
            'other': 60.0
        }
        
        return market_performance.get(market_type.lower(), 65.0)
    
    def _get_risk_performance(self, risk_tier: RiskTier) -> float:
        """Get historical performance score for risk tier."""
        performance_map = {
            RiskTier.TIER_A: 90.0,
            RiskTier.TIER_B: 80.0,
            RiskTier.TIER_C: 70.0,
            RiskTier.TIER_D: 60.0
        }
        
        return performance_map.get(risk_tier, 60.0)
    
    def _calculate_historical_confidence(self, opportunity: ArbitrageOpportunity, details: Dict[str, Any]) -> float:
        """Calculate confidence in historical performance assessment."""
        confidence = 0.8  # Base confidence
        
        # More data increases confidence
        sport_perf = details.get('sport_performance', 0)
        if sport_perf > 80:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def get_explanation(self, score: float, opportunity: ArbitrageOpportunity) -> str:
        """Generate explanation for historical performance score."""
        if score >= 85:
            return f"Excellent historical performance with high success rates across all dimensions"
        elif score >= 70:
            return f"Good historical performance with reliable track record"
        elif score >= 55:
            return f"Average historical performance with mixed results"
        else:
            return f"Poor historical performance - high risk of execution issues"


class QualityScorer:
    """
    Comprehensive quality scoring system that combines multiple dimensions.
    """
    
    def __init__(self):
        """Initialize the quality scorer with all dimension scorers."""
        self.scorers = {
            'reliability': ReliabilityScorer(),
            'profit_stability': ProfitStabilityScorer(),
            'execution_complexity': ExecutionComplexityScorer(),
            'market_conditions': MarketConditionsScorer(),
            'historical_performance': HistoricalPerformanceScorer()
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            QualityLevel.EXCELLENT: 85.0,
            QualityLevel.VERY_GOOD: 75.0,
            QualityLevel.GOOD: 65.0,
            QualityLevel.FAIR: 50.0,
            QualityLevel.POOR: 35.0,
            QualityLevel.VERY_POOR: 0.0
        }
        
        # Performance tracking
        self.scoring_stats = {
            'total_assessments': 0,
            'average_quality_score': 0.0,
            'quality_distribution': defaultdict(int),
            'assessment_time_ms': 0.0
        }
    
    def assess_quality(self, 
                      opportunity: ArbitrageOpportunity, 
                      context: Optional[Dict[str, Any]] = None) -> QualityAssessment:
        """
        Perform comprehensive quality assessment of an opportunity.
        
        Args:
            opportunity: Arbitrage opportunity to assess
            context: Additional context for assessment
            
        Returns:
            Complete QualityAssessment
        """
        start_time = datetime.utcnow()
        
        try:
            # Calculate individual dimension scores
            dimensions = {}
            dimension_objects = {}
            
            for dimension_name, scorer in self.scorers.items():
                try:
                    dimension = scorer.calculate_score(opportunity, context)
                    dimensions[dimension_name] = dimension.score
                    dimension_objects[dimension_name] = dimension
                except Exception as e:
                    logger.error(f"Error calculating {dimension_name} score: {e}")
                    # Use default score for failed calculations
                    dimensions[dimension_name] = 50.0
                    dimension_objects[dimension_name] = QualityDimension(
                        name=dimension_name,
                        score=50.0,
                        weight=0.20,
                        explanation=f"Error calculating {dimension_name} score"
                    )
            
            # Calculate weighted overall score
            weighted_score = sum(
                dimension.normalized_score * dimension.weight 
                for dimension in dimension_objects.values()
            ) * 100
            
            # Calculate unweighted average
            unweighted_average = statistics.mean(dimensions.values())
            
            # Determine quality level
            quality_level = self._determine_quality_level(weighted_score)
            
            # Generate summary and recommendations
            summary, recommendations = self._generate_summary_and_recommendations(
                weighted_score, dimension_objects, opportunity
            )
            
            # Calculate overall confidence
            confidence_level = statistics.mean(
                dimension.confidence for dimension in dimension_objects.values()
            )
            
            assessment = QualityAssessment(
                opportunity_id=str(opportunity.id),
                overall_quality_score=weighted_score,
                quality_level=quality_level,
                reliability_score=dimension_objects['reliability'],
                profit_stability_score=dimension_objects['profit_stability'],
                execution_complexity_score=dimension_objects['execution_complexity'],
                market_conditions_score=dimension_objects['market_conditions'],
                historical_performance_score=dimension_objects['historical_performance'],
                weighted_dimensions=list(dimension_objects.values()),
                unweighted_average=unweighted_average,
                assessed_at=datetime.utcnow(),
                confidence_level=confidence_level,
                summary=summary,
                recommendations=recommendations
            )
            
            # Update statistics
            self._update_stats(weighted_score, assessment)
            
            logger.debug(f"Assessed quality for opportunity {opportunity.id}: {weighted_score:.1f} ({quality_level.value})")
            return assessment
            
        except Exception as e:
            logger.error(f"Error in quality assessment for {opportunity.id}: {e}")
            # Return fallback assessment
            return self._create_fallback_assessment(opportunity)
    
    def batch_assess_quality(self, 
                           opportunities: List[ArbitrageOpportunity],
                           context: Optional[Dict[str, Any]] = None,
                           max_workers: int = 4) -> List[QualityAssessment]:
        """
        Perform quality assessment on multiple opportunities in parallel.
        
        Args:
            opportunities: List of opportunities to assess
            context: Additional context for assessment
            max_workers: Maximum number of parallel workers
            
        Returns:
            List of QualityAssessment objects
        """
        from concurrent.futures import ThreadPoolExecutor
        
        assessments = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.assess_quality, opportunity, context)
                for opportunity in opportunities
            ]
            
            for future in futures:
                try:
                    assessment = future.result()
                    assessments.append(assessment)
                except Exception as e:
                    logger.error(f"Error in batch assessment: {e}")
                    # Continue with other assessments
        
        logger.info(f"Completed batch quality assessment for {len(assessments)} opportunities")
        return assessments
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """Determine quality level based on score."""
        for level, threshold in self.quality_thresholds.items():
            if score >= threshold:
                return level
        return QualityLevel.VERY_POOR
    
    def _generate_summary_and_recommendations(self, 
                                            score: float,
                                            dimensions: Dict[str, QualityDimension],
                                            opportunity: ArbitrageOpportunity) -> Tuple[str, List[str]]:
        """Generate summary and recommendations based on assessment."""
        summary = f"Quality score: {score:.1f}/100 - "
        
        # Quality summary
        if score >= 85:
            summary += "Excellent opportunity with high reliability and stability"
        elif score >= 75:
            summary += "Very good opportunity with strong fundamentals"
        elif score >= 65:
            summary += "Good opportunity with some concerns to monitor"
        elif score >= 50:
            summary += "Fair opportunity with moderate risk factors"
        else:
            summary += "Poor opportunity with significant quality issues"
        
        recommendations = []
        
        # Reliability recommendations
        if dimensions['reliability'].score < 70:
            recommendations.append("Verify bookmaker reliability and liquidity before execution")
        
        # Profit stability recommendations
        if dimensions['profit_stability'].score < 70:
            recommendations.append("Review profit margin sustainability and distribution balance")
        
        # Execution complexity recommendations
        if dimensions['execution_complexity'].score < 60:
            recommendations.append("Consider simplifying execution with fewer legs or smaller stakes")
        
        # Market conditions recommendations
        if dimensions['market_conditions'].score < 60:
            recommendations.append("Monitor market volatility and competitive landscape")
        
        # Time-based recommendations
        time_to_event = (opportunity.event_date - datetime.utcnow()).total_seconds() / 60
        if time_to_event < 60:
            recommendations.append("Execute quickly due to time-sensitive nature")
        
        # Risk-based recommendations
        if opportunity.risk_tier in [RiskTier.TIER_C, RiskTier.TIER_D]:
            recommendations.append("Consider reducing stake size due to higher risk tier")
        
        return summary, recommendations
    
    def _update_stats(self, score: float, assessment: QualityAssessment):
        """Update performance statistics."""
        self.scoring_stats['total_assessments'] += 1
        
        # Update average score
        total = self.scoring_stats['total_assessments']
        current_avg = self.scoring_stats['average_quality_score']
        new_avg = ((current_avg * (total - 1)) + score) / total
        self.scoring_stats['average_quality_score'] = new_avg
        
        # Update quality distribution
        self.scoring_stats['quality_distribution'][assessment.quality_level.value] += 1
    
    def _create_fallback_assessment(self, opportunity: ArbitrageOpportunity) -> QualityAssessment:
        """Create a fallback assessment when scoring fails."""
        return QualityAssessment(
            opportunity_id=str(opportunity.id),
            overall_quality_score=50.0,
            quality_level=QualityLevel.FAIR,
            reliability_score=QualityDimension("reliability", 50.0, 0.25),
            profit_stability_score=QualityDimension("profit_stability", 50.0, 0.25),
            execution_complexity_score=QualityDimension("execution_complexity", 50.0, 0.20),
            market_conditions_score=QualityDimension("market_conditions", 50.0, 0.15),
            historical_performance_score=QualityDimension("historical_performance", 50.0, 0.15),
            weighted_dimensions=[],
            unweighted_average=50.0,
            assessed_at=datetime.utcnow(),
            confidence_level=0.5,
            summary="Fallback assessment due to scoring error",
            recommendations=["Manual review required due to assessment error"]
        )
    
    def get_scorer_info(self) -> Dict[str, Any]:
        """Get information about the quality scoring system."""
        return {
            'scorers': {
                name: scorer.__class__.__name__ 
                for name, scorer in self.scorers.items()
            },
            'quality_thresholds': {level.value: threshold for level, threshold in self.quality_thresholds.items()},
            'performance_stats': dict(self.scoring_stats),
            'supported_dimensions': list(self.scorers.keys())
        }
    
    def get_quality_distribution(self) -> Dict[str, int]:
        """Get distribution of quality levels across all assessments."""
        return dict(self.scoring_stats['quality_distribution'])


# Convenience functions
def create_quality_assessment(opportunity: ArbitrageOpportunity) -> QualityAssessment:
    """Create a quick quality assessment using default scorer."""
    scorer = QualityScorer()
    return scorer.assess_quality(opportunity)


def batch_quality_assessment(opportunities: List[ArbitrageOpportunity]) -> List[QualityAssessment]:
    """Perform quality assessment on multiple opportunities."""
    scorer = QualityScorer()
    return scorer.batch_assess_quality(opportunities)