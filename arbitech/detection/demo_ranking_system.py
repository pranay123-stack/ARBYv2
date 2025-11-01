"""
Intelligent Opportunity Ranking and Filtering System - Demo

Comprehensive demonstration of the arbitrage opportunity ranking, filtering,
priority queuing, and quality assessment systems working together.
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
import logging

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detection import (
    OpportunityRanker,
    FilteringEngine,
    PriorityQueue,
    QualityScorer,
    RankingStrategy,
    RankingWeights,
    QualityLevel,
    PriorityStrategy as PQStrategy,
    create_profit_filter,
    create_risk_filter,
    create_sport_filter,
    create_liquidity_filter
)

from storage.models import (
    ArbitrageOpportunity,
    ArbitrageLeg,
    RiskTier,
    Sport
)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_opportunities() -> List[ArbitrageOpportunity]:
    """Create sample arbitrage opportunities for demonstration."""
    opportunities = []
    
    # Sample 1: High-profit, low-risk opportunity
    opp1 = ArbitrageOpportunity(
        sport=Sport.FOOTBALL,
        event_name="Manchester United vs Liverpool",
        event_date=datetime.utcnow() + timedelta(hours=2),
        market_type="match_winner",
        legs=[
            ArbitrageLeg(
                bookmaker="bet365",
                event_outcome="Manchester United wins",
                odds=Decimal("2.10"),
                implied_probability=Decimal("0.476"),
                stake_percentage=Decimal("0.476"),
                actual_stake=Decimal("476.00"),
                potential_payout=Decimal("1000.00")
            ),
            ArbitrageLeg(
                bookmaker="pinnacle",
                event_outcome="Draw",
                odds=Decimal("3.50"),
                implied_probability=Decimal("0.286"),
                stake_percentage=Decimal("0.286"),
                actual_stake=Decimal("286.00"),
                potential_payout=Decimal("1000.00")
            ),
            ArbitrageLeg(
                bookmaker="william_hill",
                event_outcome="Liverpool wins",
                odds=Decimal("4.20"),
                implied_probability=Decimal("0.238"),
                stake_percentage=Decimal("0.238"),
                actual_stake=Decimal("238.00"),
                potential_payout=Decimal("1000.00")
            )
        ],
        total_stake=Decimal("1000.00"),
        profit_margin=Decimal("0.025"),
        profit_amount=Decimal("25.00"),
        guaranteed_profit=True,
        risk_tier=RiskTier.TIER_A,
        liquidity_checked=True,
        source_scanner="demo_scanner_1",
        discovered_at=datetime.utcnow() - timedelta(minutes=5)
    )
    opportunities.append(opp1)
    
    # Sample 2: Medium-profit, moderate-risk opportunity
    opp2 = ArbitrageOpportunity(
        sport=Sport.BASKETBALL,
        event_name="Lakers vs Warriors",
        event_date=datetime.utcnow() + timedelta(hours=1),
        market_type="over_under",
        legs=[
            ArbitrageLeg(
                bookmaker="draftkings",
                event_outcome="Over 220.5",
                odds=Decimal("1.91"),
                implied_probability=Decimal("0.524"),
                stake_percentage=Decimal("0.524"),
                actual_stake=Decimal("524.00"),
                potential_payout=Decimal("1000.00")
            ),
            ArbitrageLeg(
                bookmaker="fanduel",
                event_outcome="Under 220.5",
                odds=Decimal("1.91"),
                implied_probability=Decimal("0.524"),
                stake_percentage=Decimal("0.476"),
                actual_stake=Decimal("476.00"),
                potential_payout=Decimal("1000.00")
            )
        ],
        total_stake=Decimal("1000.00"),
        profit_margin=Decimal("0.018"),
        profit_amount=Decimal("18.00"),
        guaranteed_profit=True,
        risk_tier=RiskTier.TIER_B,
        liquidity_checked=True,
        source_scanner="demo_scanner_2",
        discovered_at=datetime.utcnow() - timedelta(minutes=10)
    )
    opportunities.append(opp2)
    
    # Sample 3: Low-profit, high-risk opportunity
    opp3 = ArbitrageOpportunity(
        sport=Sport.ESPORTS,
        event_name="Team A vs Team B",
        event_date=datetime.utcnow() + timedelta(minutes=30),
        market_type="match_winner",
        legs=[
            ArbitrageLeg(
                bookmaker="betway",
                event_outcome="Team A wins",
                odds=Decimal("1.85"),
                implied_probability=Decimal("0.541"),
                stake_percentage=Decimal("0.541"),
                actual_stake=Decimal("541.00"),
                potential_payout=Decimal("1000.00")
            ),
            ArbitrageLeg(
                bookmaker="unibet",
                event_outcome="Team B wins",
                odds=Decimal("1.95"),
                implied_probability=Decimal("0.513"),
                stake_percentage=Decimal("0.459"),
                actual_stake=Decimal("459.00"),
                potential_payout=Decimal("1000.00")
            )
        ],
        total_stake=Decimal("1000.00"),
        profit_margin=Decimal("0.008"),
        profit_amount=Decimal("8.00"),
        guaranteed_profit=True,
        risk_tier=RiskTier.TIER_D,
        liquidity_checked=False,
        source_scanner="demo_scanner_3",
        discovered_at=datetime.utcnow() - timedelta(minutes=25)
    )
    opportunities.append(opp3)
    
    # Sample 4: High-profit, time-sensitive opportunity
    opp4 = ArbitrageOpportunity(
        sport=Sport.TENNIS,
        event_name="Djokovic vs Nadal",
        event_date=datetime.utcnow() + timedelta(minutes=45),
        market_type="handicap",
        legs=[
            ArbitrageLeg(
                bookmaker="pinnacle",
                event_outcome="Djokovic -2.5 games",
                odds=Decimal("2.05"),
                implied_probability=Decimal("0.488"),
                stake_percentage=Decimal("0.488"),
                actual_stake=Decimal("488.00"),
                potential_payout=Decimal("1000.00")
            ),
            ArbitrageLeg(
                bookmaker="betfair",
                event_outcome="Nadal +2.5 games",
                odds=Decimal("2.05"),
                implied_probability=Decimal("0.488"),
                stake_percentage=Decimal("0.512"),
                actual_stake=Decimal("512.00"),
                potential_payout=Decimal("1000.00")
            )
        ],
        total_stake=Decimal("1000.00"),
        profit_margin=Decimal("0.032"),
        profit_amount=Decimal("32.00"),
        guaranteed_profit=True,
        risk_tier=RiskTier.TIER_B,
        liquidity_checked=True,
        source_scanner="demo_scanner_4",
        discovered_at=datetime.utcnow() - timedelta(minutes=2)
    )
    opportunities.append(opp4)
    
    # Sample 5: Large stake, complex opportunity
    opp5 = ArbitrageOpportunity(
        sport=Sport.FOOTBALL,
        event_name="Real Madrid vs Barcelona",
        event_date=datetime.utcnow() + timedelta(days=1),
        market_type="correct_score",
        legs=[
            ArbitrageLeg(
                bookmaker="bet365",
                event_outcome="1-0",
                odds=Decimal("8.50"),
                implied_probability=Decimal("0.118"),
                stake_percentage=Decimal("0.118"),
                actual_stake=Decimal("118.00"),
                potential_payout=Decimal("1000.00")
            ),
            ArbitrageLeg(
                bookmaker="william_hill",
                event_outcome="0-0",
                odds=Decimal("12.00"),
                implied_probability=Decimal("0.083"),
                stake_percentage=Decimal("0.083"),
                actual_stake=Decimal("83.00"),
                potential_payout=Decimal("1000.00")
            ),
            ArbitrageLeg(
                bookmaker="pinnacle",
                event_outcome="2-1",
                odds=Decimal("9.00"),
                implied_probability=Decimal("0.111"),
                stake_percentage=Decimal("0.111"),
                actual_stake=Decimal("111.00"),
                potential_payout=Decimal("1000.00")
            ),
            ArbitrageLeg(
                bookmaker="unibet",
                event_outcome="1-1",
                odds=Decimal("7.50"),
                implied_probability=Decimal("0.133"),
                stake_percentage=Decimal("0.133"),
                actual_stake=Decimal("133.00"),
                potential_payout=Decimal("1000.00")
            ),
            ArbitrageLeg(
                bookmaker="betway",
                event_outcome="0-1",
                odds=Decimal("11.00"),
                implied_probability=Decimal("0.091"),
                stake_percentage=Decimal("0.091"),
                actual_stake=Decimal("91.00"),
                potential_payout=Decimal("1000.00")
            ),
            ArbitrageLeg(
                bookmaker="draftkings",
                event_outcome="Other scores",
                odds=Decimal("3.20"),
                implied_probability=Decimal("0.313"),
                stake_percentage=Decimal("0.313"),
                actual_stake=Decimal("313.00"),
                potential_payout=Decimal("1000.00")
            ),
            ArbitrageLeg(
                bookmaker="fanduel",
                event_outcome="2-0",
                odds=Decimal("15.00"),
                implied_probability=Decimal("0.067"),
                stake_percentage=Decimal("0.067"),
                actual_stake=Decimal("67.00"),
                potential_payout=Decimal("1000.00")
            )
        ],
        total_stake=Decimal("1000.00"),
        profit_margin=Decimal("0.045"),
        profit_amount=Decimal("45.00"),
        guaranteed_profit=True,
        risk_tier=RiskTier.TIER_C,
        liquidity_checked=True,
        source_scanner="demo_scanner_5",
        discovered_at=datetime.utcnow() - timedelta(minutes=15),
        expires_at=datetime.utcnow() + timedelta(hours=2)
    )
    opportunities.append(opp5)
    
    return opportunities


def demo_opportunity_ranking():
    """Demonstrate the opportunity ranking system."""
    logger.info("=== Opportunity Ranking Demo ===")
    
    opportunities = create_sample_opportunities()
    ranker = OpportunityRanker()
    
    # Test different ranking strategies
    strategies_to_test = [
        RankingStrategy.BALANCED,
        RankingStrategy.PROFIT_FIRST,
        RankingStrategy.RISK_FIRST,
        RankingStrategy.SPEED_FIRST,
        RankingStrategy.LIQUIDITY_FIRST
    ]
    
    for strategy in strategies_to_test:
        logger.info(f"\n--- Ranking with {strategy.value} strategy ---")
        
        ranked_opportunities = ranker.rank_opportunities(
            opportunities, 
            strategy=strategy
        )
        
        for score in ranked_opportunities[:3]:  # Show top 3
            logger.info(f"Rank {score.rank}: Opportunity {score.opportunity_id[:8]}")
            logger.info(f"  Overall Score: {score.overall_score:.1f}")
            logger.info(f"  Profit Score: {score.profit_score:.1f}")
            logger.info(f"  Risk Score: {score.risk_score:.1f}")
            logger.info(f"  Liquidity Score: {score.liquidity_score:.1f}")
            logger.info(f"  Time Score: {score.time_score:.1f}")
            logger.info(f"  Execution Score: {score.execution_score:.1f}")
            logger.info(f"  Explanation: {score.profit_details}")
    
    # Show performance statistics
    stats = ranker.get_performance_stats()
    logger.info(f"\nRanking Performance: {stats}")


def demo_filtering_engine():
    """Demonstrate the filtering engine."""
    logger.info("\n=== Filtering Engine Demo ===")
    
    opportunities = create_sample_opportunities()
    filter_engine = FilteringEngine()
    
    # Add various filters
    filter_engine.add_filter(create_profit_filter(min_margin=Decimal("0.015")))
    filter_engine.add_filter(create_risk_filter([RiskTier.TIER_A, RiskTier.TIER_B]))
    filter_engine.add_filter(create_sport_filter([Sport.FOOTBALL, Sport.BASKETBALL]))
    filter_engine.add_filter(create_liquidity_filter(must_be_checked=True))
    
    # Apply filters
    filtered_opportunities = filter_engine.filter_opportunities(opportunities)
    
    logger.info(f"Original opportunities: {len(opportunities)}")
    logger.info(f"Filtered opportunities: {len(filtered_opportunities)}")
    
    # Show filtered results
    for opp in filtered_opportunities:
        logger.info(f"  {opp.sport.value}: {opp.event_name} - {opp.profit_margin:.2%} profit")
    
    # Show filter information
    filter_info = filter_engine.get_filter_info()
    logger.info(f"\nFilter Configuration: {filter_info}")


def demo_priority_queue():
    """Demonstrate the priority queue system."""
    logger.info("\n=== Priority Queue Demo ===")
    
    opportunities = create_sample_opportunities()
    queue = PriorityQueue(max_size=100, default_strategy=PQStrategy.HIGHEST_SCORE)
    
    # Enqueue opportunities
    logger.info("Enqueuing opportunities...")
    for i, opp in enumerate(opportunities):
        success = queue.enqueue(opp, custom_metadata={'demo_index': i})
        logger.info(f"Enqueued {i+1}: {'Success' if success else 'Failed'}")
    
    # Show queue info
    queue_info = queue.get_queue_info()
    logger.info(f"Queue Info: {queue_info['current_size']} items, Status: {queue_info['status']}")
    
    # Test different deque strategies
    strategies = [PQStrategy.HIGHEST_SCORE, PQStrategy.FIFO, PQStrategy.URGENT_FIRST]
    
    for strategy in strategies:
        logger.info(f"\n--- Dequeuing with {strategy.value} strategy ---")
        
        # Reset queue for fair comparison
        queue.clear()
        for opp in opportunities:
            queue.enqueue(opp)
        
        # Dequeue top 3 opportunities
        for i in range(3):
            result = queue.dequeue(timeout_seconds=1.0, strategy=strategy)
            if result:
                opp_id, metadata = result
                logger.info(f"Dequeued {i+1}: {str(opp_id)[:8]} with metadata: {metadata}")
            else:
                logger.info(f"Dequeued {i+1}: No opportunity available")
    
    # Test batch processing
    logger.info("\n--- Batch Processing Demo ---")
    batch_result = queue.batch_process(
        lambda opp_id, metadata: logger.info(f"Processed {str(opp_id)[:8]}"),
        batch_size=2
    )
    logger.info(f"Batch processing result: {batch_result}")


def demo_quality_scorer():
    """Demonstrate the quality scoring system."""
    logger.info("\n=== Quality Scoring Demo ===")
    
    opportunities = create_sample_opportunities()
    quality_scorer = QualityScorer()
    
    # Assess quality of each opportunity
    quality_results = []
    for opp in opportunities:
        assessment = quality_scorer.assess_quality(opp)
        quality_results.append(assessment)
        
        logger.info(f"\n--- Quality Assessment for {opp.event_name} ---")
        logger.info(f"Overall Quality Score: {assessment.overall_quality_score:.1f}")
        logger.info(f"Quality Level: {assessment.quality_level.value}")
        logger.info(f"Confidence Level: {assessment.confidence_level:.1%}")
        logger.info(f"Summary: {assessment.summary}")
        
        # Show dimension breakdown
        logger.info("Dimension Scores:")
        for dim in assessment.weighted_dimensions:
            logger.info(f"  {dim.name}: {dim.score:.1f}/100 (weight: {dim.weight:.1%})")
            logger.info(f"    {dim.explanation}")
        
        # Show recommendations
        if assessment.recommendations:
            logger.info("Recommendations:")
            for rec in assessment.recommendations:
                logger.info(f"  • {rec}")
    
    # Batch assessment
    logger.info("\n--- Batch Quality Assessment ---")
    batch_results = quality_scorer.batch_assess_quality(opportunities)
    logger.info(f"Batch assessment completed for {len(batch_results)} opportunities")
    
    # Show quality distribution
    distribution = quality_scorer.get_quality_distribution()
    logger.info(f"Quality Distribution: {distribution}")
    
    # Show scorer information
    scorer_info = quality_scorer.get_scorer_info()
    logger.info(f"Scorer Info: {scorer_info['supported_dimensions']}")


def demo_integrated_system():
    """Demonstrate the integrated system working together."""
    logger.info("\n=== Integrated System Demo ===")
    
    opportunities = create_sample_opportunities()
    
    # Create components
    ranker = OpportunityRanker()
    filter_engine = FilteringEngine()
    queue = PriorityQueue()
    quality_scorer = QualityScorer()
    
    # Step 1: Apply filters
    logger.info("Step 1: Filtering opportunities...")
    filter_engine.add_filter(create_profit_filter(min_margin=Decimal("0.010")))
    filter_engine.add_filter(create_risk_filter([RiskTier.TIER_A, RiskTier.TIER_B, RiskTier.TIER_C]))
    filtered_opportunities = filter_engine.filter_opportunities(opportunities)
    logger.info(f"Filtered {len(opportunities)} to {len(filtered_opportunities)} opportunities")
    
    # Step 2: Rank opportunities
    logger.info("Step 2: Ranking opportunities...")
    ranked_opportunities = ranker.rank_opportunities(
        filtered_opportunities,
        strategy=RankingStrategy.BALANCED
    )
    
    # Step 3: Assess quality
    logger.info("Step 3: Assessing quality...")
    quality_assessments = {}
    for score in ranked_opportunities:
        opp = next(o for o in opportunities if str(o.id) == score.opportunity_id)
        assessment = quality_scorer.assess_quality(opp)
        quality_assessments[score.opportunity_id] = assessment
    
    # Step 4: Add to priority queue (only high-quality opportunities)
    logger.info("Step 4: Adding high-quality opportunities to queue...")
    for score in ranked_opportunities:
        assessment = quality_assessments[score.opportunity_id]
        
        # Only add opportunities with good quality scores
        if assessment.quality_level in [QualityLevel.EXCELLENT, QualityLevel.VERY_GOOD, QualityLevel.GOOD]:
            opp = next(o for o in opportunities if str(o.id) == score.opportunity_id)
            queue.enqueue(opp, priority_score=assessment.overall_quality_score)
    
    # Step 5: Process queue
    logger.info("Step 5: Processing priority queue...")
    processed_count = 0
    while True:
        result = queue.dequeue(timeout_seconds=1.0)
        if not result:
            break
        
        opp_id, metadata = result
        processed_count += 1
        
        # Get quality assessment for processed opportunity
        assessment = quality_assessments[opp_id]
        logger.info(f"Processed {processed_count}: Quality {assessment.quality_level.value} ({assessment.overall_quality_score:.1f})")
        
        if processed_count >= 5:  # Limit for demo
            break
    
    # Final summary
    logger.info("\n=== System Integration Summary ===")
    logger.info(f"• Processed {processed_count} high-quality opportunities")
    logger.info(f"• Average quality score: {sum(a.overall_quality_score for a in quality_assessments.values()) / len(quality_assessments):.1f}")
    
    # Show performance metrics
    queue_info = queue.get_queue_info()
    ranking_stats = ranker.get_performance_stats()
    filter_info = filter_engine.get_filter_info()
    
    logger.info(f"• Queue throughput: {queue_info['metrics']['throughput_per_second']:.2f} ops/sec")
    logger.info(f"• Ranking performance: {ranking_stats['average_scoring_time_ms']:.2f}ms per opportunity")
    logger.info(f"• Filter processing: {filter_info['performance_stats']['average_filter_time_ms']:.2f}ms")


def main():
    """Run all demonstrations."""
    logger.info("Starting Intelligent Opportunity Ranking and Filtering System Demo")
    logger.info("=" * 70)
    
    try:
        # Run individual demos
        demo_opportunity_ranking()
        demo_filtering_engine()
        demo_priority_queue()
        demo_quality_scorer()
        
        # Run integrated demo
        demo_integrated_system()
        
        logger.info("\n" + "=" * 70)
        logger.info("Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}", exc_info=True)


if __name__ == "__main__":
    main()