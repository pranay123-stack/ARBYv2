#!/usr/bin/env python3
"""
Test and Demo Script for Opportunity Presenter System

This script demonstrates and tests the comprehensive opportunity presentation system
for HITL mode, including console and web presenters.

Usage:
    python test_opportunity_presenter.py [console|web|both]

Default: both
"""

import asyncio
import sys
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID

# Import ARBitech models and components
try:
    # Try relative imports first
    from ..storage.models import ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier
    from ..hitl import (
        create_hitl_presenter, 
        DisplayFormat, 
        OpportunityPresenterSystem,
        demo_hitl_presenter
    )
    from ..utils.logger import get_logger
except ImportError:
    # Fall back to absolute imports
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from storage.models import ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier
    from hitl import (
        create_hitl_presenter, 
        DisplayFormat, 
        OpportunityPresenterSystem,
        demo_hitl_presenter
    )
    from utils.logger import get_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)


async def create_demo_opportunities() -> list[ArbitrageOpportunity]:
    """Create demo arbitrage opportunities for testing."""
    try:
        logger.info("Creating demo opportunities...")
        
        opportunities = []
        
        # Football opportunity
        football_opp = ArbitrageOpportunity(
            id=uuid4(),
            sport=Sport.FOOTBALL,
            event_name="Manchester United vs Liverpool - Premier League",
            event_date=datetime.utcnow() + timedelta(hours=2),
            market_type="match_winner",
            legs=[
                ArbitrageLeg(
                    bookmaker="Bet365",
                    event_outcome="Manchester United Win",
                    odds=Decimal('2.10'),
                    implied_probability=Decimal('0.476'),
                    stake_percentage=Decimal('0.475'),
                    actual_stake=Decimal('95.00'),
                    potential_payout=Decimal('199.50')
                ),
                ArbitrageLeg(
                    bookmaker="Pinnacle",
                    event_outcome="Liverpool Win",
                    odds=Decimal('2.05'),
                    implied_probability=Decimal('0.488'),
                    stake_percentage=Decimal('0.525'),
                    actual_stake=Decimal('105.00'),
                    potential_payout=Decimal('215.25')
                )
            ],
            total_stake=Decimal('200.00'),
            profit_margin=Decimal('0.047'),
            profit_amount=Decimal('15.75'),
            risk_tier=RiskTier.TIER_A,
            source_scanner="demo_scanner_1",
            discovered_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )
        opportunities.append(football_opp)
        
        # Basketball opportunity
        basketball_opp = ArbitrageOpportunity(
            id=uuid4(),
            sport=Sport.BASKETBALL,
            event_name="Los Angeles Lakers vs Boston Celtics",
            event_date=datetime.utcnow() + timedelta(hours=4),
            market_type="moneyline",
            legs=[
                ArbitrageLeg(
                    bookmaker="DraftKings",
                    event_outcome="Los Angeles Lakers Win",
                    odds=Decimal('1.85'),
                    implied_probability=Decimal('0.541'),
                    stake_percentage=Decimal('0.541'),
                    actual_stake=Decimal('108.11'),
                    potential_payout=Decimal('200.00')
                ),
                ArbitrageLeg(
                    bookmaker="FanDuel",
                    event_outcome="Boston Celtics Win",
                    odds=Decimal('2.25'),
                    implied_probability=Decimal('0.444'),
                    stake_percentage=Decimal('0.444'),
                    actual_stake=Decimal('88.89'),
                    potential_payout=Decimal('200.00')
                )
            ],
            total_stake=Decimal('197.00'),
            profit_margin=Decimal('0.015'),
            profit_amount=Decimal('3.00'),
            risk_tier=RiskTier.TIER_B,
            source_scanner="demo_scanner_2",
            discovered_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=45)
        )
        opportunities.append(basketball_opp)
        
        # Tennis opportunity - Higher profit
        tennis_opp = ArbitrageOpportunity(
            id=uuid4(),
            sport=Sport.TENNIS,
            event_name="Novak Djokovic vs Rafael Nadal",
            event_date=datetime.utcnow() + timedelta(hours=6),
            market_type="match_winner",
            legs=[
                ArbitrageLeg(
                    bookmaker="William Hill",
                    event_outcome="Novak Djokovic Win",
                    odds=Decimal('1.75'),
                    implied_probability=Decimal('0.571'),
                    stake_percentage=Decimal('0.571'),
                    actual_stake=Decimal('114.29'),
                    potential_payout=Decimal('200.00')
                ),
                ArbitrageLeg(
                    bookmaker="Betfair",
                    event_outcome="Rafael Nadal Win",
                    odds=Decimal('2.50'),
                    implied_probability=Decimal('0.400'),
                    stake_percentage=Decimal('0.400'),
                    actual_stake=Decimal('80.00'),
                    potential_payout=Decimal('200.00')
                )
            ],
            total_stake=Decimal('194.29'),
            profit_margin=Decimal('0.029'),
            profit_amount=Decimal('5.71'),
            risk_tier=RiskTier.TIER_A,
            source_scanner="demo_scanner_3",
            discovered_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        opportunities.append(tennis_opp)
        
        # Hockey opportunity - Higher risk
        hockey_opp = ArbitrageOpportunity(
            id=uuid4(),
            sport=Sport.HOCKEY,
            event_name="New York Rangers vs Boston Bruins",
            event_date=datetime.utcnow() + timedelta(hours=8),
            market_type="total_goals_over_under",
            legs=[
                ArbitrageLeg(
                    bookmaker="Caesars",
                    event_outcome="Over 5.5 Goals",
                    odds=Decimal('1.95'),
                    implied_probability=Decimal('0.513'),
                    stake_percentage=Decimal('0.513'),
                    actual_stake=Decimal('102.56'),
                    potential_payout=Decimal('200.00')
                ),
                ArbitrageLeg(
                    bookmaker="PointsBet",
                    event_outcome="Under 5.5 Goals",
                    odds=Decimal('2.15'),
                    implied_probability=Decimal('0.465'),
                    stake_percentage=Decimal('0.465'),
                    actual_stake=Decimal('93.02'),
                    potential_payout=Decimal('200.00')
                )
            ],
            total_stake=Decimal('195.58'),
            profit_margin=Decimal('0.022'),
            profit_amount=Decimal('4.42'),
            risk_tier=RiskTier.TIER_C,
            source_scanner="demo_scanner_4",
            discovered_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=20)
        )
        opportunities.append(hockey_opp)
        
        # Baseball opportunity - Small profit, low risk
        baseball_opp = ArbitrageOpportunity(
            id=uuid4(),
            sport=Sport.BASEBALL,
            event_name="New York Yankees vs Boston Red Sox",
            event_date=datetime.utcnow() + timedelta(hours=10),
            market_type="run_line",
            legs=[
                ArbitrageLeg(
                    bookmaker="DraftKings",
                    event_outcome="Yankees -1.5",
                    odds=Decimal('1.90'),
                    implied_probability=Decimal('0.526'),
                    stake_percentage=Decimal('0.526'),
                    actual_stake=Decimal('105.26'),
                    potential_payout=Decimal('200.00')
                ),
                ArbitrageLeg(
                    bookmaker="FanDuel",
                    event_outcome="Red Sox +1.5",
                    odds=Decimal('2.20'),
                    implied_probability=Decimal('0.455'),
                    stake_percentage=Decimal('0.455'),
                    actual_stake=Decimal('91.00'),
                    potential_payout=Decimal('200.20')
                )
            ],
            total_stake=Decimal('196.26'),
            profit_margin=Decimal('0.019'),
            profit_amount=Decimal('3.94'),
            risk_tier=RiskTier.TIER_A,
            source_scanner="demo_scanner_5",
            discovered_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=90)
        )
        opportunities.append(baseball_opp)
        
        logger.info(f"Created {len(opportunities)} demo opportunities")
        return opportunities
        
    except Exception as e:
        logger.error(f"Error creating demo opportunities: {e}")
        logger.error(f"Error details: {e.__class__.__name__}: {e}")
        raise


async def test_console_presenter():
    """Test console presenter functionality."""
    try:
        logger.info("Testing console presenter...")
        
        # Create presenter system with console format only
        presenter_system = await create_hitl_presenter(
            display_formats=[DisplayFormat.CONSOLE],
            max_opportunities=10,
            update_interval=2.0
        )
        
        # Start the system
        await presenter_system.start()
        logger.info("Console presenter started successfully")
        
        # Add demo opportunities
        opportunities = await create_demo_opportunities()
        await presenter_system.add_opportunities(opportunities)
        logger.info("Added demo opportunities to console presenter")
        
        # Run for a few seconds to show updates
        logger.info("Running console presenter for 10 seconds...")
        await asyncio.sleep(10)
        
        # Show statistics
        stats = presenter_system.get_statistics()
        logger.info(f"Presenter statistics: {stats}")
        
        # Test opportunity comparison
        if len(opportunities) >= 2:
            logger.info("Testing opportunity comparison...")
            comparison = await presenter_system.compare_opportunities(
                opportunities[0].id,
                [opp.id for opp in opportunities[1:3]]
            )
            if comparison:
                logger.info("Comparison completed successfully")
        
        # Stop the system
        await presenter_system.stop()
        logger.info("Console presenter test completed")
        
    except Exception as e:
        logger.error(f"Console presenter test failed: {e}")
        logger.error(f"Error details: {e.__class__.__name__}: {e}")
        raise


async def test_web_presenter():
    """Test web presenter functionality."""
    try:
        logger.info("Testing web presenter...")
        
        # Create presenter system with web format only
        presenter_system = await create_hitl_presenter(
            display_formats=[DisplayFormat.WEB],
            max_opportunities=10,
            update_interval=2.0
        )
        
        # Start the system
        await presenter_system.start()
        logger.info("Web presenter started successfully on ws://localhost:8765")
        
        # Add demo opportunities
        opportunities = await create_demo_opportunities()
        await presenter_system.add_opportunities(opportunities)
        logger.info("Added demo opportunities to web presenter")
        
        # Run for a few seconds
        logger.info("Running web presenter for 10 seconds...")
        await asyncio.sleep(10)
        
        # Show statistics
        stats = presenter_system.get_statistics()
        logger.info(f"Web presenter statistics: {stats}")
        
        # Stop the system
        await presenter_system.stop()
        logger.info("Web presenter test completed")
        
    except Exception as e:
        logger.error(f"Web presenter test failed: {e}")
        logger.error(f"Error details: {e.__class__.__name__}: {e}")
        raise


async def test_combined_presenters():
    """Test both console and web presenters together."""
    try:
        logger.info("Testing combined presenters (console + web)...")
        
        # Create presenter system with both formats
        presenter_system = await create_hitl_presenter(
            display_formats=[DisplayFormat.CONSOLE, DisplayFormat.WEB],
            max_opportunities=10,
            update_interval=2.0
        )
        
        # Start the system
        await presenter_system.start()
        logger.info("Combined presenters started successfully")
        
        # Add demo opportunities
        opportunities = await create_demo_opportunities()
        await presenter_system.add_opportunities(opportunities)
        logger.info("Added demo opportunities to both presenters")
        
        # Simulate some updates
        logger.info("Simulating opportunity updates...")
        await asyncio.sleep(3)
        
        # Update one opportunity (modify profit margin)
        if opportunities:
            updated_opp = opportunities[0].copy(deep=True)
            updated_opp.profit_margin = Decimal('0.060')  # Increase profit margin
            updated_opp.profit_amount = updated_opp.total_stake * updated_opp.profit_margin
            await presenter_system.update_opportunities([updated_opp])
            logger.info("Updated opportunity profit margin")
        
        # Remove one opportunity
        if len(opportunities) > 1:
            await presenter_system.remove_opportunities([opportunities[-1].id])
            logger.info("Removed last opportunity")
        
        # Add new opportunity
        new_opportunities = await create_demo_opportunities()
        await presenter_system.add_opportunities([new_opportunities[0]])  # Add just one more
        
        # Run for more time to show updates
        logger.info("Running combined presenters for 15 seconds...")
        await asyncio.sleep(15)
        
        # Show final statistics
        stats = presenter_system.get_statistics()
        logger.info(f"Final statistics: {stats}")
        
        # Test opportunity comparison
        logger.info("Testing opportunity comparison...")
        comparison = await presenter_system.compare_opportunities(
            opportunities[0].id,
            [opp.id for opp in opportunities[1:3]]
        )
        if comparison:
            logger.info("Comparison completed successfully")
            logger.info(f"Primary opportunity: {comparison.primary_opportunity.event_name}")
            logger.info(f"Comparison recommended {len(comparison.recommended_ranks)} ranks")
        
        # Show recent events
        events = presenter_system.get_events(5)
        logger.info(f"Recent events: {len(events)} events captured")
        for event in events[-3:]:  # Show last 3 events
            logger.info(f"  - {event.type}: {event.data}")
        
        # Stop the system
        await presenter_system.stop()
        logger.info("Combined presenters test completed successfully")
        
    except Exception as e:
        logger.error(f"Combined presenters test failed: {e}")
        logger.error(f"Error details: {e.__class__.__name__}: {e}")
        raise


async def main():
    """Main test function."""
    try:
        logger.info("="*60)
        logger.info("OPPORTUNITY PRESENTER SYSTEM TEST")
        logger.info("="*60)
        
        # Parse command line arguments
        test_mode = "both"
        if len(sys.argv) > 1:
            test_mode = sys.argv[1].lower()
        
        logger.info(f"Test mode: {test_mode}")
        
        # Run tests based on mode
        if test_mode == "console":
            await test_console_presenter()
        elif test_mode == "web":
            await test_web_presenter()
        elif test_mode == "both":
            await test_combined_presenters()
        elif test_mode == "demo":
            await demo_hitl_presenter()
        else:
            logger.error(f"Unknown test mode: {test_mode}")
            logger.info("Available modes: console, web, both, demo")
            return 1
        
        logger.info("="*60)
        logger.info("ALL TESTS COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        logger.error(f"Error details: {e.__class__.__name__}: {e}")
        logger.error("Full traceback:")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)