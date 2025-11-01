"""
VLM Odds Extraction Parser - Usage Examples

This script demonstrates how to use the VLM Odds Extraction and Parsing System
for extracting and validating betting odds from bookmaker interface images.
"""

import asyncio
import logging
from decimal import Decimal
from datetime import datetime, timezone

from vlm import (
    OddsExtractor, 
    OddsParser, 
    TemplateManager,
    OddsValidator,
    ExtractionRequest,
    Sport,
    cross_validate_odds,
    validate_arbitrage_constraints
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def demo_odds_extraction():
    """Demonstrate odds extraction from VLM."""
    logger.info("=== Demo: Odds Extraction ===")
    
    # Initialize extractor
    extractor = OddsExtractor()
    
    # Example extraction request (using placeholder image data)
    request = ExtractionRequest(
        image_data="placeholder_image_data",  # Would be actual image data
        bookmaker="Betfair",
        sport=Sport.FOOTBALL,
        market_type="match_winner",
        event_name="Manchester United vs Liverpool",
        min_confidence=0.7
    )
    
    logger.info(f"Created extraction request for {request.bookmaker} - {request.event_name}")
    
    # In a real scenario, this would call the VLM service
    # For demo, we'll skip the actual extraction
    logger.info("Extraction request prepared (VLM call would happen here)")


async def demo_odds_parsing():
    """Demonstrate odds parsing and normalization."""
    logger.info("\n=== Demo: Odds Parsing ===")
    
    parser = OddsParser()
    
    # Example VLM response data
    raw_response = '''
    {
        "outcomes": ["Home Win", "Away Win", "Draw"],
        "odds": {
            "Home Win": "2.50",
            "Away Win": "3.20", 
            "Draw": "3.00"
        }
    }
    '''
    
    # Parse the response
    result = await parser.parse_vlm_response(
        raw_response=raw_response,
        bookmaker="Pinnacle",
        sport=Sport.FOOTBALL,
        market_type="match_winner",
        event_name="Chelsea vs Arsenal"
    )
    
    logger.info(f"Parsed {len(result.parsed_odds)} odds for {result.bookmaker}")
    logger.info(f"Parsing status: {result.parsing_status.value}")
    logger.info(f"Overall confidence: {result.overall_confidence:.3f}")
    
    # Show parsed odds
    for odd in result.parsed_odds:
        logger.info(f"  {odd.outcome}: {odd.decimal_odds} (implied prob: {odd.implied_probability:.4f})")


async def demo_bookmaker_templates():
    """Demonstrate bookmaker template system."""
    logger.info("\n=== Demo: Bookmaker Templates ===")
    
    template_manager = TemplateManager()
    
    # List available templates
    templates = template_manager.list_templates()
    logger.info(f"Available templates: {len(templates)}")
    
    for template in templates:
        logger.info(f"  {template.name} v{template.version} for {template.bookmaker}")
    
    # Get a specific template
    betfair_template = template_manager.get_template("Betfair", Sport.FOOTBALL)
    if betfair_template:
        logger.info(f"\nGot Betfair template: {betfair_template.name}")
        
        # Generate extraction prompt
        prompt = betfair_template.get_extraction_prompt(Sport.FOOTBALL, "match_winner")
        logger.info("Extraction prompt generated for Betfair")
    
    # Validate template compatibility
    compatibility = template_manager.validate_template_compatibility(
        "Pinnacle", Sport.FOOTBALL, "over_under"
    )
    logger.info(f"Template compatibility: {compatibility}")


async def demo_odds_validation():
    """Demonstrate odds validation."""
    logger.info("\n=== Demo: Odds Validation ===")
    
    # Create sample parsed odds
    from vlm.odds_parser import ParsedOdds, OddsFormat, MarketParseResult, ParsingMetadata
    
    sample_odds = [
        ParsedOdds(
            outcome="Home Win",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('2.50'),
            implied_probability=Decimal('0.40'),
            original_representation="2.50",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.85,
            format_confidence=0.90,
            bookmaker="Pinnacle",
            event_name="Test Match",
            validation_status="success"
        ),
        ParsedOdds(
            outcome="Away Win",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('3.20'),
            implied_probability=Decimal('0.3125'),
            original_representation="3.20",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.80,
            format_confidence=0.85,
            bookmaker="Pinnacle",
            event_name="Test Match",
            validation_status="success"
        ),
        ParsedOdds(
            outcome="Draw",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('3.00'),
            implied_probability=Decimal('0.3333'),
            original_representation="3.00",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.75,
            format_confidence=0.80,
            bookmaker="Pinnacle",
            event_name="Test Match",
            validation_status="success"
        )
    ]
    
    # Create market result
    market_result = MarketParseResult(
        sport=Sport.FOOTBALL,
        market_type="match_winner",
        event_name="Test Match",
        parsed_odds=sample_odds,
        bookmaker="Pinnacle",
        parsing_status="success",
        total_outcomes=3,
        successful_odds=3,
        failed_odds=0,
        overall_confidence=0.80,
        data_completeness=1.0,
        parsing_metadata=ParsingMetadata(
            source_type="demo",
            raw_response="demo_response",
            parsing_time_ms=100,
            data_quality_score=0.80
        )
    )
    
    # Validate the odds
    validator = OddsValidator()
    validation_result = await validator.validate_market_odds(market_result)
    
    logger.info(f"Validation result: {'PASS' if validation_result.is_valid else 'FAIL'}")
    logger.info(f"Quality score: {validation_result.quality_score:.3f}")
    logger.info(f"Issues found: {len(validation_result.issues)}")
    
    for issue in validation_result.issues:
        logger.info(f"  [{issue.severity.value}] {issue.message}")


async def demo_cross_validation():
    """Demonstrate cross-bookmaker validation."""
    logger.info("\n=== Demo: Cross-Bookmaker Validation ===")
    
    # Create sample market results from different bookmakers
    from vlm.odds_parser import ParsedOdds, OddsFormat, MarketParseResult, ParsingMetadata
    
    market_results = []
    
    # Betfair odds
    betfair_odds = [
        ParsedOdds(
            outcome="Home Win",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('2.45'),
            implied_probability=Decimal('0.4082'),
            original_representation="2.45",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.90,
            format_confidence=0.95,
            bookmaker="Betfair",
            event_name="Demo Match",
            validation_status="success"
        ),
        ParsedOdds(
            outcome="Away Win",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('3.25'),
            implied_probability=Decimal('0.3077'),
            original_representation="3.25",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.88,
            format_confidence=0.92,
            bookmaker="Betfair",
            event_name="Demo Match",
            validation_status="success"
        ),
        ParsedOdds(
            outcome="Draw",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('3.10'),
            implied_probability=Decimal('0.3226'),
            original_representation="3.10",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.85,
            format_confidence=0.88,
            bookmaker="Betfair",
            event_name="Demo Match",
            validation_status="success"
        )
    ]
    
    betfair_result = MarketParseResult(
        sport=Sport.FOOTBALL,
        market_type="match_winner",
        event_name="Demo Match",
        parsed_odds=betfair_odds,
        bookmaker="Betfair",
        parsing_status="success",
        total_outcomes=3,
        successful_odds=3,
        failed_odds=0,
        overall_confidence=0.88,
        data_completeness=1.0,
        parsing_metadata=ParsingMetadata(
            source_type="demo",
            raw_response="demo_betfair_response",
            parsing_time_ms=200,
            data_quality_score=0.88
        )
    )
    market_results.append(betfair_result)
    
    # Pinnacle odds (slightly different)
    pinnacle_odds = [
        ParsedOdds(
            outcome="Home Win",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('2.48'),
            implied_probability=Decimal('0.4032'),
            original_representation="2.48",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.92,
            format_confidence=0.94,
            bookmaker="Pinnacle",
            event_name="Demo Match",
            validation_status="success"
        ),
        ParsedOdds(
            outcome="Away Win",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('3.22'),
            implied_probability=Decimal('0.3106'),
            original_representation="3.22",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.89,
            format_confidence=0.91,
            bookmaker="Pinnacle",
            event_name="Demo Match",
            validation_status="success"
        ),
        ParsedOdds(
            outcome="Draw",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('3.05'),
            implied_probability=Decimal('0.3279'),
            original_representation="3.05",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.86,
            format_confidence=0.89,
            bookmaker="Pinnacle",
            event_name="Demo Match",
            validation_status="success"
        )
    ]
    
    pinnacle_result = MarketParseResult(
        sport=Sport.FOOTBALL,
        market_type="match_winner",
        event_name="Demo Match",
        parsed_odds=pinnacle_odds,
        bookmaker="Pinnacle",
        parsing_status="success",
        total_outcomes=3,
        successful_odds=3,
        failed_odds=0,
        overall_confidence=0.89,
        data_completeness=1.0,
        parsing_metadata=ParsingMetadata(
            source_type="demo",
            raw_response="demo_pinnacle_response",
            parsing_time_ms=180,
            data_quality_score=0.89
        )
    )
    market_results.append(pinnacle_result)
    
    # Cross-validate
    cross_validation_results = await cross_validate_odds(market_results)
    
    logger.info("Cross-validation results:")
    for bookmaker, validation_result in cross_validation_results.items():
        logger.info(f"  {bookmaker}: {'PASS' if validation_result.is_valid else 'FAIL'} (quality: {validation_result.quality_score:.3f})")
        for issue in validation_result.issues:
            logger.info(f"    [{issue.severity.value}] {issue.message}")
    
    # Check for arbitrage opportunities
    arbitrage_validation = await validate_arbitrage_constraints(market_results, min_profit_margin=1.0)
    logger.info(f"Arbitrage validation: {'FOUND' if arbitrage_validation.issues else 'NOT FOUND'}")
    for issue in arbitrage_validation.issues:
        logger.info(f"  {issue.message}")


async def demo_arbitrage_creation():
    """Demonstrate creating arbitrage opportunities."""
    logger.info("\n=== Demo: Arbitrage Opportunity Creation ===")
    
    from vlm.odds_parser import create_arbitrage_opportunity
    
    # Use the market results from the previous demo
    # (In a real scenario, these would come from actual VLM extraction)
    
    # For demo, we'll create an obvious arbitrage opportunity
    from vlm.odds_parser import ParsedOdds, OddsFormat, MarketParseResult, ParsingMetadata
    
    # Market with actual arbitrage opportunity
    market_results = []
    
    # Bookmaker A with high odds on Home Win
    bookmaker_a_odds = [
        ParsedOdds(
            outcome="Home Win",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('3.50'),
            implied_probability=Decimal('0.2857'),
            original_representation="3.50",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.90,
            format_confidence=0.95,
            bookmaker="Bookmaker A",
            event_name="Arbitrage Demo",
            validation_status="success"
        ),
        ParsedOdds(
            outcome="Away Win",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('1.40'),
            implied_probability=Decimal('0.7143'),
            original_representation="1.40",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.88,
            format_confidence=0.92,
            bookmaker="Bookmaker A",
            event_name="Arbitrage Demo",
            validation_status="success"
        )
    ]
    
    bookmaker_a_result = MarketParseResult(
        sport=Sport.FOOTBALL,
        market_type="match_winner",
        event_name="Arbitrage Demo",
        parsed_odds=bookmaker_a_odds,
        bookmaker="Bookmaker A",
        parsing_status="success",
        total_outcomes=2,
        successful_odds=2,
        failed_odds=0,
        overall_confidence=0.89,
        data_completeness=1.0,
        parsing_metadata=ParsingMetadata(
            source_type="demo",
            raw_response="demo_bookmaker_a",
            parsing_time_ms=150,
            data_quality_score=0.89
        )
    )
    market_results.append(bookmaker_a_result)
    
    # Bookmaker B with high odds on Away Win
    bookmaker_b_odds = [
        ParsedOdds(
            outcome="Home Win",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('1.20'),
            implied_probability=Decimal('0.8333'),
            original_representation="1.20",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.92,
            format_confidence=0.96,
            bookmaker="Bookmaker B",
            event_name="Arbitrage Demo",
            validation_status="success"
        ),
        ParsedOdds(
            outcome="Away Win",
            sport=Sport.FOOTBALL,
            market_type="match_winner",
            decimal_odds=Decimal('5.00'),
            implied_probability=Decimal('0.2000'),
            original_representation="5.00",
            original_format=OddsFormat.DECIMAL,
            parsing_confidence=0.87,
            format_confidence=0.91,
            bookmaker="Bookmaker B",
            event_name="Arbitrage Demo",
            validation_status="success"
        )
    ]
    
    bookmaker_b_result = MarketParseResult(
        sport=Sport.FOOTBALL,
        market_type="match_winner",
        event_name="Arbitrage Demo",
        parsed_odds=bookmaker_b_odds,
        bookmaker="Bookmaker B",
        parsing_status="success",
        total_outcomes=2,
        successful_odds=2,
        failed_odds=0,
        overall_confidence=0.895,
        data_completeness=1.0,
        parsing_metadata=ParsingMetadata(
            source_type="demo",
            raw_response="demo_bookmaker_b",
            parsing_time_ms=160,
            data_quality_score=0.895
        )
    )
    market_results.append(bookmaker_b_result)
    
    # Try to create arbitrage opportunity
    opportunity = await create_arbitrage_opportunity(market_results, min_profit_margin=1.0)
    
    if opportunity:
        logger.info("Arbitrage opportunity created!")
        logger.info(f"  Sport: {opportunity.sport.value}")
        logger.info(f"  Event: {opportunity.event_name}")
        logger.info(f"  Market: {opportunity.market_type}")
        logger.info(f"  Total Stake: ${opportunity.total_stake}")
        logger.info(f"  Profit Margin: {opportunity.profit_margin:.4f}%")
        logger.info(f"  Profit Amount: ${opportunity.profit_amount}")
        logger.info(f"  Risk Tier: {opportunity.risk_tier.value}")
        logger.info(f"  Number of Legs: {len(opportunity.legs)}")
        
        # Show the legs
        for i, leg in enumerate(opportunity.legs):
            logger.info(f"  Leg {i+1}: {leg.bookmaker} - {leg.event_outcome}")
            logger.info(f"    Odds: {leg.odds}")
            logger.info(f"    Implied Probability: {leg.implied_probability:.4f}")
            logger.info(f"    Stake Percentage: {leg.stake_percentage:.4f}")
            logger.info(f"    Potential Payout: ${leg.potential_payout}")
    else:
        logger.info("No arbitrage opportunity found (as expected in most cases)")


async def main():
    """Run all demos."""
    logger.info("VLM Odds Extraction Parser System - Demo")
    logger.info("=" * 50)
    
    await demo_odds_extraction()
    await demo_odds_parsing()
    await demo_bookmaker_templates()
    await demo_odds_validation()
    await demo_cross_validation()
    await demo_arbitrage_creation()
    
    logger.info("\n" + "=" * 50)
    logger.info("Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())