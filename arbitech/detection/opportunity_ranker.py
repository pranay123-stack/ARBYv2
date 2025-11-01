"""
Advanced Opportunity Ranking System

Intelligent ranking system that scores arbitrage opportunities based on multiple
dimensions including profit potential, risk level, liquidity, time sensitivity,
and execution difficulty. Supports configurable scoring algorithms and weights.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass
import math
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

from ..storage.models import ArbitrageOpportunity, ArbitrageLeg, RiskTier, Sport


logger = logging.getLogger(__name__)


class RankingStrategy(str, Enum):
    """Available ranking strategies."""
    PROFIT_FIRST = "profit_first"
    RISK_FIRST = "risk_first"
    SPEED_FIRST = "speed_first"
    BALANCED = "balanced"
    LIQUIDITY_FIRST = "liquidity_first"
    TIME_SENSITIVE = "time_sensitive"


@dataclass
class RankingWeights:
    """Configurable weights for different scoring dimensions."""
    profit_score: float = 0.35
    risk_score: float = 0.25
    liquidity_score: float = 0.15
    time_score: float = 0.15
    execution_score: float = 0.10
    
    def validate(self) -> bool:
        """Validate that weights sum to approximately 1.0."""
        total = sum(self.profit_score, self.risk_score, self.liquidity_score, 
                   self.time_score, self.execution_score)
        return abs(total - 1.0) < 0.01


@dataclass
class OpportunityScore:
    """Detailed scoring result for an opportunity."""
    opportunity_id: str
    overall_score: float
    rank: int
    ranking_strategy: RankingStrategy
    
    # Individual dimension scores
    profit_score: float
    risk_score: float
    liquidity_score: float
    time_score: float
    execution_score: float
    
    # Score explanations
    profit_details: Dict[str, Any]
    risk_details: Dict[str, Any]
    liquidity_details: Dict[str, Any]
    time_details: Dict[str, Any]
    execution_details: Dict[str, Any]
    
    # Timing and metadata
    scored_at: datetime
    score_version: str = "1.0"


class ProfitScoreCalculator:
    """Calculates profit-based scores for opportunities."""
    
    @staticmethod
    def calculate_profit_score(opportunity: ArbitrageOpportunity) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate profit-based score (0-100).
        
        Args:
            opportunity: The arbitrage opportunity to score
            
        Returns:
            Tuple of (score, details_dict)
        """
        details = {}
        
        # Base profit margin score (0-40 points)
        profit_margin = float(opportunity.profit_margin)
        if profit_margin >= 0.05:  # 5%+
            base_score = 40.0
        elif profit_margin >= 0.03:  # 3-5%
            base_score = 30.0 + (profit_margin - 0.03) * 500  # Up to 40 points
        elif profit_margin >= 0.01:  # 1-3%
            base_score = 10.0 + (profit_margin - 0.01) * 1000  # Up to 30 points
        else:  # <1%
            base_score = max(0.0, profit_margin * 1000)  # Up to 10 points
        
        details['profit_margin_score'] = base_score
        details['profit_margin'] = profit_margin
        
        # Profit amount score (0-25 points)
        profit_amount = float(opportunity.profit_amount)
        if profit_amount >= 100:  # $100+
            profit_amount_score = 25.0
        elif profit_amount >= 50:  # $50-100
            profit_amount_score = 15.0 + (profit_amount - 50) * 0.2
        elif profit_amount >= 10:  # $10-50
            profit_amount_score = 5.0 + (profit_amount - 10) * 0.25
        else:  # <$10
            profit_amount_score = max(0.0, profit_amount * 0.5)
        
        details['profit_amount_score'] = profit_amount_score
        details['profit_amount'] = profit_amount
        
        # Stake efficiency score (0-20 points)
        total_stake = float(opportunity.total_stake)
        roi = profit_amount / total_stake if total_stake > 0 else 0
        if roi >= 0.05:  # 5% ROI
            stake_efficiency_score = 20.0
        elif roi >= 0.03:  # 3-5% ROI
            stake_efficiency_score = 15.0 + (roi - 0.03) * 250
        elif roi >= 0.01:  # 1-3% ROI
            stake_efficiency_score = 5.0 + (roi - 0.01) * 500
        else:  # <1% ROI
            stake_efficiency_score = max(0.0, roi * 500)
        
        details['stake_efficiency_score'] = stake_efficiency_score
        details['roi'] = roi
        
        # Profit stability score (0-15 points)
        stability_score = ProfitScoreCalculator._calculate_stability_score(opportunity)
        details['stability_score'] = stability_score
        
        total_score = min(100.0, base_score + profit_amount_score + stake_efficiency_score + stability_score)
        
        return total_score, details
    
    @staticmethod
    def _calculate_stability_score(opportunity: ArbitrageOpportunity) -> float:
        """Calculate profit stability based on arbitrage structure."""
        # Higher stability for opportunities with more legs (diversification)
        leg_count = len(opportunity.legs)
        if leg_count >= 4:
            stability_bonus = 15.0
        elif leg_count == 3:
            stability_bonus = 10.0
        else:  # 2 legs
            stability_bonus = 5.0
        
        # Bonus for balanced odds (less variance in stake percentages)
        stake_percentages = [float(leg.stake_percentage) for leg in opportunity.legs]
        stake_variance = sum((p - 1.0/len(stake_percentages))**2 for p in stake_percentages) / len(stake_percentages)
        balance_penalty = min(5.0, stake_variance * 100)  # Penalty for imbalanced stakes
        
        return max(0.0, stability_bonus - balance_penalty)


class RiskScoreCalculator:
    """Calculates risk-based scores for opportunities."""
    
    @staticmethod
    def calculate_risk_score(opportunity: ArbitrageOpportunity) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate risk-based score (0-100, higher = lower risk).
        
        Args:
            opportunity: The arbitrage opportunity to score
            
        Returns:
            Tuple of (score, details_dict)
        """
        details = {}
        
        # Base risk tier score (0-40 points)
        tier_scores = {
            RiskTier.TIER_A: 40.0,
            RiskTier.TIER_B: 30.0,
            RiskTier.TIER_C: 20.0,
            RiskTier.TIER_D: 10.0
        }
        base_score = tier_scores.get(opportunity.risk_tier, 0.0)
        details['risk_tier_score'] = base_score
        details['risk_tier'] = opportunity.risk_tier.value
        
        # Liquidity score (0-25 points)
        if opportunity.liquidity_checked:
            liquidity_score = 25.0
        else:
            liquidity_score = 10.0  # Penalty for not checked
        details['liquidity_score'] = liquidity_score
        
        # Odds freshness score (0-20 points)
        freshness_score = RiskScoreCalculator._calculate_freshness_score(opportunity)
        details['freshness_score'] = freshness_score
        
        # Bookmaker diversity score (0-15 points)
        diversity_score = RiskScoreCalculator._calculate_diversity_score(opportunity)
        details['diversity_score'] = diversity_score
        
        total_score = min(100.0, base_score + liquidity_score + freshness_score + diversity_score)
        
        return total_score, details
    
    @staticmethod
    def _calculate_freshness_score(opportunity: ArbitrageOpportunity) -> float:
        """Calculate score based on odds freshness."""
        age_minutes = (datetime.utcnow() - opportunity.odds_freshness).total_seconds() / 60
        if age_minutes <= 5:
            return 20.0
        elif age_minutes <= 15:
            return 15.0
        elif age_minutes <= 30:
            return 10.0
        elif age_minutes <= 60:
            return 5.0
        else:
            return 0.0
    
    @staticmethod
    def _calculate_diversity_score(opportunity: ArbitrageOpportunity) -> float:
        """Calculate score based on bookmaker diversity."""
        unique_bookmakers = set(leg.bookmaker for leg in opportunity.legs)
        diversity_score = min(15.0, len(unique_bookmakers) * 5.0)
        return diversity_score


class LiquidityScoreCalculator:
    """Calculates liquidity-based scores for opportunities."""
    
    @staticmethod
    def calculate_liquidity_score(opportunity: ArbitrageOpportunity) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate liquidity score (0-100).
        
        Args:
            opportunity: The arbitrage opportunity to score
            
        Returns:
            Tuple of (score, details_dict)
        """
        details = {}
        
        # Stakes vs potential liquidity analysis
        total_stake = float(opportunity.total_stake)
        
        # Assume average bookmaker liquidity is 10x the total stake for calculation
        assumed_liquidity = total_stake * 10
        
        # Liquidity ratio score (0-40 points)
        liquidity_ratio = assumed_liquidity / total_stake if total_stake > 0 else 0
        if liquidity_ratio >= 20:
            liquidity_ratio_score = 40.0
        elif liquidity_ratio >= 10:
            liquidity_ratio_score = 30.0 + (liquidity_ratio - 10) * 1.0
        elif liquidity_ratio >= 5:
            liquidity_ratio_score = 15.0 + (liquidity_ratio - 5) * 3.0
        else:
            liquidity_ratio_score = max(0.0, liquidity_ratio * 3.0)
        
        details['liquidity_ratio_score'] = liquidity_ratio_score
        details['liquidity_ratio'] = liquidity_ratio
        
        # Stake size score (0-30 points) - smaller stakes are easier to place
        if total_stake <= 50:
            stake_size_score = 30.0
        elif total_stake <= 100:
            stake_size_score = 25.0
        elif total_stake <= 250:
            stake_size_score = 20.0
        elif total_stake <= 500:
            stake_size_score = 15.0
        elif total_stake <= 1000:
            stake_size_score = 10.0
        else:
            stake_size_score = 5.0
        
        details['stake_size_score'] = stake_size_score
        details['total_stake'] = total_stake
        
        # Leg count score (0-30 points) - more legs = more complex execution
        leg_count = len(opportunity.legs)
        if leg_count == 2:
            leg_count_score = 30.0
        elif leg_count == 3:
            leg_count_score = 20.0
        else:  # 4+ legs
            leg_count_score = max(0.0, 20.0 - (leg_count - 3) * 5.0)
        
        details['leg_count_score'] = leg_count_score
        details['leg_count'] = leg_count
        
        total_score = min(100.0, liquidity_ratio_score + stake_size_score + leg_count_score)
        
        return total_score, details


class TimeScoreCalculator:
    """Calculates time-based scores for opportunities."""
    
    @staticmethod
    def calculate_time_score(opportunity: ArbitrageOpportunity) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate time-based score (0-100).
        
        Args:
            opportunity: The arbitrage opportunity to score
            
        Returns:
            Tuple of (score, details_dict)
        """
        details = {}
        
        # Discovery age score (0-40 points)
        discovery_age_minutes = (datetime.utcnow() - opportunity.discovered_at).total_seconds() / 60
        if discovery_age_minutes <= 2:
            discovery_score = 40.0
        elif discovery_age_minutes <= 5:
            discovery_score = 35.0
        elif discovery_age_minutes <= 10:
            discovery_score = 25.0
        elif discovery_age_minutes <= 30:
            discovery_score = 15.0
        else:
            discovery_score = max(0.0, 40.0 - discovery_age_minutes * 0.5)
        
        details['discovery_age_score'] = discovery_score
        details['discovery_age_minutes'] = discovery_age_minutes
        
        # Event urgency score (0-35 points) - closer events get priority
        event_time_minutes = (opportunity.event_date - datetime.utcnow()).total_seconds() / 60
        if event_time_minutes <= 60:  # Within 1 hour
            urgency_score = 35.0
        elif event_time_minutes <= 180:  # Within 3 hours
            urgency_score = 25.0
        elif event_time_minutes <= 720:  # Within 12 hours
            urgency_score = 20.0
        elif event_time_minutes <= 1440:  # Within 1 day
            urgency_score = 10.0
        else:
            urgency_score = 5.0
        
        details['event_urgency_score'] = urgency_score
        details['event_time_minutes'] = event_time_minutes
        
        # Expiration score (0-25 points)
        if opportunity.expires_at:
            expiration_minutes = (opportunity.expires_at - datetime.utcnow()).total_seconds() / 60
            if expiration_minutes <= 5:
                expiration_score = 25.0
            elif expiration_minutes <= 15:
                expiration_score = 20.0
            elif expiration_minutes <= 60:
                expiration_score = 15.0
            elif expiration_minutes <= 300:
                expiration_score = 10.0
            else:
                expiration_score = 5.0
        else:
            expiration_score = 15.0  # Default for non-expiring opportunities
        
        details['expiration_score'] = expiration_score
        
        total_score = min(100.0, discovery_score + urgency_score + expiration_score)
        
        return total_score, details


class ExecutionScoreCalculator:
    """Calculates execution complexity scores for opportunities."""
    
    @staticmethod
    def calculate_execution_score(opportunity: ArbitrageOpportunity) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate execution complexity score (0-100, higher = easier).
        
        Args:
            opportunity: The arbitrage opportunity to score
            
        Returns:
            Tuple of (score, details_dict)
        """
        details = {}
        
        # Complexity score based on number of legs (0-40 points)
        leg_count = len(opportunity.legs)
        if leg_count == 2:
            complexity_score = 40.0
        elif leg_count == 3:
            complexity_score = 30.0
        else:  # 4+ legs
            complexity_score = max(0.0, 30.0 - (leg_count - 3) * 5.0)
        
        details['complexity_score'] = complexity_score
        details['leg_count'] = leg_count
        
        # Market type score (0-30 points)
        market_complexity = {
            'match_winner': 30.0,
            'over_under': 25.0,
            'handicap': 20.0,
            'correct_score': 15.0,
            'first_goal': 20.0,
            'half_time': 15.0,
            'other': 10.0
        }
        market_score = market_complexity.get(opportunity.market_type.lower(), 15.0)
        details['market_score'] = market_score
        details['market_type'] = opportunity.market_type
        
        # Stake distribution score (0-30 points) - more balanced is easier
        stake_percentages = [float(leg.stake_percentage) for leg in opportunity.legs]
        target_percentage = 1.0 / len(stake_percentages)
        distribution_variance = sum((p - target_percentage)**2 for p in stake_percentages) / len(stake_percentages)
        
        # Lower variance = higher score
        if distribution_variance <= 0.001:
            distribution_score = 30.0
        elif distribution_variance <= 0.01:
            distribution_score = 25.0
        elif distribution_variance <= 0.05:
            distribution_score = 20.0
        elif distribution_variance <= 0.1:
            distribution_score = 15.0
        else:
            distribution_score = 10.0
        
        details['distribution_score'] = distribution_score
        details['distribution_variance'] = distribution_variance
        
        total_score = min(100.0, complexity_score + market_score + distribution_score)
        
        return total_score, details


class OpportunityRanker:
    """
    Main opportunity ranking system with configurable scoring algorithms.
    """
    
    def __init__(self, weights: Optional[RankingWeights] = None, strategy: RankingStrategy = RankingStrategy.BALANCED):
        """
        Initialize the opportunity ranker.
        
        Args:
            weights: Custom scoring weights
            strategy: Default ranking strategy
        """
        self.weights = weights or RankingWeights()
        self.strategy = strategy
        self.score_calculators = {
            'profit': ProfitScoreCalculator(),
            'risk': RiskScoreCalculator(),
            'liquidity': LiquidityScoreCalculator(),
            'time': TimeScoreCalculator(),
            'execution': ExecutionScoreCalculator()
        }
        
        # Thread-safe scoring cache
        self._score_cache = {}
        self._cache_lock = threading.RLock()
        
        # Performance tracking
        self.scoring_stats = {
            'opportunities_scored': 0,
            'total_scoring_time_ms': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def rank_opportunities(self, 
                          opportunities: List[ArbitrageOpportunity],
                          strategy: Optional[RankingStrategy] = None,
                          weights: Optional[RankingWeights] = None,
                          batch_size: int = 1000) -> List[OpportunityScore]:
        """
        Rank a list of opportunities with performance optimization.
        
        Args:
            opportunities: List of opportunities to rank
            strategy: Ranking strategy to use
            weights: Custom weights for this ranking
            batch_size: Batch size for processing large lists
            
        Returns:
            List of ranked opportunity scores
        """
        start_time = datetime.utcnow()
        effective_strategy = strategy or self.strategy
        effective_weights = weights or self.weights
        
        # Apply strategy-specific weight adjustments
        strategy_weights = self._apply_strategy_weights(effective_weights, effective_strategy)
        
        if len(opportunities) <= batch_size:
            # Process smaller lists directly
            scored_opportunities = self._score_opportunities_batch(opportunities, strategy_weights)
        else:
            # Process larger lists in batches
            scored_opportunities = []
            for i in range(0, len(opportunities), batch_size):
                batch = opportunities[i:i + batch_size]
                batch_scored = self._score_opportunities_batch(batch, strategy_weights)
                scored_opportunities.extend(batch_scored)
        
        # Sort by overall score (descending)
        scored_opportunities.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Assign ranks
        for rank, score in enumerate(scored_opportunities, 1):
            score.rank = rank
        
        # Update statistics
        scoring_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.scoring_stats['opportunities_scored'] += len(opportunities)
        self.scoring_stats['total_scoring_time_ms'] += scoring_time
        
        logger.info(f"Ranked {len(opportunities)} opportunities in {scoring_time:.2f}ms")
        
        return scored_opportunities
    
    def _score_opportunities_batch(self, 
                                   opportunities: List[ArbitrageOpportunity],
                                   weights: RankingWeights) -> List[OpportunityScore]:
        """Score a batch of opportunities using parallel processing."""
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self._score_single_opportunity, opp, weights) 
                      for opp in opportunities]
            return [future.result() for future in futures]
    
    def _score_single_opportunity(self, 
                                 opportunity: ArbitrageOpportunity, 
                                 weights: RankingWeights) -> OpportunityScore:
        """Score a single opportunity with caching."""
        
        # Check cache first
        cache_key = self._get_cache_key(opportunity, weights)
        with self._cache_lock:
            if cache_key in self._score_cache:
                self.scoring_stats['cache_hits'] += 1
                return self._score_cache[cache_key]
            self.scoring_stats['cache_misses'] += 1
        
        # Calculate individual scores
        profit_score, profit_details = self.score_calculators['profit'].calculate_profit_score(opportunity)
        risk_score, risk_details = self.score_calculators['risk'].calculate_risk_score(opportunity)
        liquidity_score, liquidity_details = self.score_calculators['liquidity'].calculate_liquidity_score(opportunity)
        time_score, time_details = self.score_calculators['time'].calculate_time_score(opportunity)
        execution_score, execution_details = self.score_calculators['execution'].calculate_execution_score(opportunity)
        
        # Calculate weighted overall score
        overall_score = (
            profit_score * weights.profit_score +
            risk_score * weights.risk_score +
            liquidity_score * weights.liquidity_score +
            time_score * weights.time_score +
            execution_score * weights.execution_score
        )
        
        # Create score object
        score = OpportunityScore(
            opportunity_id=str(opportunity.id),
            overall_score=overall_score,
            rank=0,  # Will be assigned later
            ranking_strategy=self.strategy,
            profit_score=profit_score,
            risk_score=risk_score,
            liquidity_score=liquidity_score,
            time_score=time_score,
            execution_score=execution_score,
            profit_details=profit_details,
            risk_details=risk_details,
            liquidity_details=liquidity_details,
            time_details=time_details,
            execution_details=execution_details,
            scored_at=datetime.utcnow()
        )
        
        # Cache the result
        with self._cache_lock:
            self._score_cache[cache_key] = score
        
        return score
    
    def _get_cache_key(self, opportunity: ArbitrageOpportunity, weights: RankingWeights) -> str:
        """Generate cache key for opportunity scoring."""
        # Include key opportunity characteristics and weights in cache key
        key_components = [
            str(opportunity.id),
            f"{opportunity.profit_margin:.4f}",
            f"{opportunity.profit_amount:.2f}",
            opportunity.risk_tier.value,
            str(len(opportunity.legs)),
            f"{weights.profit_score:.2f}",
            f"{weights.risk_score:.2f}",
            f"{weights.liquidity_score:.2f}",
            f"{weights.time_score:.2f}",
            f"{weights.execution_score:.2f}"
        ]
        return "|".join(key_components)
    
    def _apply_strategy_weights(self, base_weights: RankingWeights, strategy: RankingStrategy) -> RankingWeights:
        """Apply strategy-specific weight adjustments."""
        if strategy == RankingStrategy.PROFIT_FIRST:
            return RankingWeights(
                profit_score=0.50,
                risk_score=0.20,
                liquidity_score=0.15,
                time_score=0.10,
                execution_score=0.05
            )
        elif strategy == RankingStrategy.RISK_FIRST:
            return RankingWeights(
                profit_score=0.25,
                risk_score=0.40,
                liquidity_score=0.20,
                time_score=0.10,
                execution_score=0.05
            )
        elif strategy == RankingStrategy.SPEED_FIRST:
            return RankingWeights(
                profit_score=0.30,
                risk_score=0.15,
                liquidity_score=0.15,
                time_score=0.30,
                execution_score=0.10
            )
        elif strategy == RankingStrategy.LIQUIDITY_FIRST:
            return RankingWeights(
                profit_score=0.25,
                risk_score=0.20,
                liquidity_score=0.35,
                time_score=0.10,
                execution_score=0.10
            )
        elif strategy == RankingStrategy.TIME_SENSITIVE:
            return RankingWeights(
                profit_score=0.20,
                risk_score=0.15,
                liquidity_score=0.15,
                time_score=0.40,
                execution_score=0.10
            )
        else:  # BALANCED
            return base_weights
    
    def update_ranking_weights(self, new_weights: RankingWeights):
        """Update scoring weights and clear cache."""
        if not new_weights.validate():
            raise ValueError("Invalid weights: must sum to approximately 1.0")
        
        self.weights = new_weights
        with self._cache_lock:
            self._score_cache.clear()
        logger.info("Updated ranking weights and cleared cache")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the ranker."""
        return {
            **self.scoring_stats,
            'cache_hit_rate': (
                self.scoring_stats['cache_hits'] / 
                max(1, self.scoring_stats['cache_hits'] + self.scoring_stats['cache_misses'])
            ),
            'average_scoring_time_ms': (
                self.scoring_stats['total_scoring_time_ms'] / 
                max(1, self.scoring_stats['opportunities_scored'])
            )
        }
    
    def clear_cache(self):
        """Clear the scoring cache."""
        with self._cache_lock:
            self._score_cache.clear()
        logger.info("Cleared opportunity score cache")