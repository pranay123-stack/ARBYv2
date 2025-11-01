#!/usr/bin/env python3
"""
Integration Example for Opportunity Presenter System

This script demonstrates how to integrate the opportunity presenter system
with existing ARBitech components including scanner, risk management, and logging.

This is a comprehensive example showing real-world usage patterns.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from typing import List

# Import ARBitech models and components
try:
    # Try relative imports first (when used as part of arbitech package)
    from ..storage.models import ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier, Trade, TradeStatus
    from ..detection.opportunity_scanner import OpportunityScanner, ScannerEventType
    from ..risk.kelly_calculator import KellyCalculator, KellyConfig, KellyMode
    from ..risk.risk_analyzer import RiskAnalyzer
    from ..storage.audit_logger import AuditLogger
    from ..utils.logger import get_logger
    
    # Import HITL components
    from . import create_hitl_presenter, DisplayFormat
except ImportError:
    # Fall back to absolute imports (when used standalone or in tests)
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from storage.models import ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier, Trade, TradeStatus
    from detection.opportunity_scanner import OpportunityScanner, ScannerEventType
    from risk.kelly_calculator import KellyCalculator, KellyConfig, KellyMode
    from risk.risk_analyzer import RiskAnalyzer
    from storage.audit_logger import AuditLogger
    from utils.logger import get_logger
    
    # Import HITL components
    from hitl import create_hitl_presenter, DisplayFormat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)


class MockOpportunityScanner:
    """Mock opportunity scanner for demonstration purposes."""
    
    def __init__(self):
        self._handlers = []
        self._running = False
    
    def add_event_handler(self, handler):
        """Add event handler for scanner events."""
        self._handlers.append(handler)
        logger.info(f"Added event handler to scanner: {handler}")
    
    async def simulate_opportunities(self):
        """Simulate finding opportunities."""
        try:
            logger.info("Starting opportunity simulation...")
            
            # Simulate finding opportunities periodically
            opportunity_count = 0
            
            while self._running:
                # Create a new opportunity
                opportunity = self._create_simulated_opportunity(opportunity_count)
                opportunity_count += 1
                
                # Notify handlers
                from detection.opportunity_scanner import ScannerEventType
                event_data = {
                    'opportunities': [opportunity],
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                for handler in self._handlers:
                    try:
                        await handler(ScannerEventType.OPPORTUNITY_FOUND, event_data)
                    except Exception as e:
                        logger.error(f"Error in scanner event handler: {e}")
                
                # Wait before next opportunity (random interval)
                import random
                await asyncio.sleep(random.uniform(2, 5))
                
        except Exception as e:
            logger.error(f"Error in opportunity simulation: {e}")
    
    def _create_simulated_opportunity(self, count: int) -> dict:
        """Create a simulated opportunity for testing."""
        sports = [Sport.FOOTBALL, Sport.BASKETBALL, Sport.TENNIS, Sport.BASEBALL]
        bookmakers = [
            ("Bet365", "William Hill"),
            ("Pinnacle", "DraftKings"),
            ("FanDuel", "PointsBet"),
            ("Caesars", "Betfair")
        ]
        
        sport = sports[count % len(sports)]
        bookmaker1, bookmaker2 = bookmakers[count % len(bookmakers)]
        
        # Generate realistic odds for arbitrage
        base_odds = Decimal(str(1.8 + (count % 10) * 0.05))  # Vary base odds
        inverse_odds = base_odds * Decimal('1.05')  # Create arbitrage
        
        event_names = {
            Sport.FOOTBALL: "Premier League Match",
            Sport.BASKETBALL: "NBA Game", 
            Sport.TENNIS: "Grand Slam Match",
            Sport.BASEBALL: "MLB Game"
        }
        
        return {
            'id': str(uuid4()),
            'sport': sport.value,
            'event_name': f"{event_names[sport]} #{count + 1}",
            'event_date': (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            'market_type': 'match_winner',
            'legs': [
                {
                    'bookmaker': bookmaker1,
                    'event_outcome': 'Team A Win',
                    'odds': base_odds,
                    'implied_probability': Decimal('1') / base_odds,
                    'stake_percentage': Decimal('0.5'),
                    'actual_stake': Decimal('100.00'),
                    'potential_payout': base_odds * Decimal('100')
                },
                {
                    'bookmaker': bookmaker2,
                    'event_outcome': 'Team B Win',
                    'odds': inverse_odds,
                    'implied_probability': Decimal('1') / inverse_odds,
                    'stake_percentage': Decimal('0.5'),
                    'actual_stake': Decimal('100.00'),
                    'potential_payout': inverse_odds * Decimal('100')
                }
            ],
            'total_stake': Decimal('200.00'),
            'profit_margin': ((base_odds * Decimal('100')) - Decimal('200')) / Decimal('200'),
            'profit_amount': (base_odds * Decimal('100')) - Decimal('200'),
            'risk_tier': RiskTier.TIER_A.value,
            'source_scanner': 'mock_scanner',
            'discovered_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        }
    
    async def start(self):
        """Start the mock scanner."""
        self._running = True
        asyncio.create_task(self.simulate_opportunities())
        logger.info("Mock opportunity scanner started")
    
    async def stop(self):
        """Stop the mock scanner."""
        self._running = False
        logger.info("Mock opportunity scanner stopped")


class MockKellyCalculator:
    """Mock Kelly calculator for demonstration purposes."""
    
    def __init__(self):
        logger.info("Mock Kelly calculator initialized")
    
    async def calculate_kelly(self, odds: Decimal, estimated_probability: Decimal, config: KellyConfig):
        """Calculate Kelly fraction (mock implementation)."""
        try:
            # Simple Kelly calculation
            b = odds - Decimal('1')  # Net odds received
            p = estimated_probability  # Probability of winning
            q = Decimal('1') - p  # Probability of losing
            
            # Kelly formula: (bp - q) / b
            kelly_fraction = (b * p - q) / b
            
            # Apply fractional Kelly if configured
            if config.mode == KellyMode.FRACTIONAL:
                kelly_fraction *= config.fractional_factor
            
            # Ensure Kelly fraction is reasonable
            kelly_fraction = max(Decimal('0.01'), min(Decimal('0.25'), kelly_fraction))
            
            # Mock result object
            class KellyResult:
                def __init__(self, fraction, stake):
                    self.fraction = fraction
                    self.stake = stake
                    self.expected_value = fraction * odds * stake - stake
                    self.confidence = min(Decimal('0.9'), p + Decimal('0.1'))
            
            return KellyResult(kelly_fraction, kelly_fraction)
            
        except Exception as e:
            logger.error(f"Error calculating Kelly: {e}")
            return None


class MockRiskAnalyzer:
    """Mock risk analyzer for demonstration purposes."""
    
    def __init__(self):
        logger.info("Mock risk analyzer initialized")
    
    async def analyze_opportunity(self, opportunity: ArbitrageOpportunity):
        """Analyze opportunity risk (mock implementation)."""
        try:
            # Mock risk analysis
            import random
            
            class RiskAnalysis:
                def __init__(self, risk_score, factors):
                    self.overall_risk_score = risk_score
                    self.risk_factors = factors
                    self.recommended_action = "proceed" if risk_score < 0.6 else "caution"
            
            # Generate risk based on opportunity characteristics
            base_risk = Decimal('0.3')  # Base risk
            
            # Adjust for profit margin (higher profit = higher risk)
            profit_risk = min(Decimal('0.2'), opportunity.profit_margin)
            
            # Adjust for risk tier
            tier_adjustments = {
                RiskTier.TIER_A: Decimal('0.0'),
                RiskTier.TIER_B: Decimal('0.1'),
                RiskTier.TIER_C: Decimal('0.2'),
                RiskTier.TIER_D: Decimal('0.3')
            }
            tier_risk = tier_adjustments.get(opportunity.risk_tier, Decimal('0.2'))
            
            # Add some randomness
            random_factor = Decimal(str(random.uniform(0, 0.1)))
            
            total_risk = base_risk + profit_risk + tier_risk + random_factor
            total_risk = min(Decimal('0.9'), total_risk)
            
            risk_factors = {
                'profit_margin': float(opportunity.profit_margin),
                'risk_tier': opportunity.risk_tier.value,
                'leg_count': len(opportunity.legs),
                'total_stake': float(opportunity.total_stake),
                'liquidity_indicators': 'medium'
            }
            
            return RiskAnalysis(total_risk, risk_factors)
            
        except Exception as e:
            logger.error(f"Error analyzing risk: {e}")
            return None


class MockAuditLogger:
    """Mock audit logger for demonstration purposes."""
    
    def __init__(self):
        logger.info("Mock audit logger initialized")
    
    async def log_event(self, event_type: str, data: dict, level: str = "INFO"):
        """Log audit event (mock implementation)."""
        try:
            logger.info(f"AUDIT: [{event_type}] {data} (level: {level})")
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")


async def simulate_trade_outcome(presenter_system, opportunity: ArbitrageOpportunity):
    """Simulate a trade outcome and add performance data."""
    try:
        # Create a mock trade
        trade = Trade(
            id=uuid4(),
            user_id=uuid4(),  # Mock user ID
            opportunity=opportunity,
            status=TradeStatus.SETTLED,
            execution_mode="manual",
            stake_data={
                'total_stake': float(opportunity.total_stake),
                'currency': 'USD',
                'leg_allocations': {
                    leg.bookmaker: float(leg.actual_stake) 
                    for leg in opportunity.legs
                },
                'fees_included': 0.0,
                'net_stake': float(opportunity.total_stake)
            },
            expected_profit=float(opportunity.profit_amount),
            actual_profit=float(opportunity.profit_amount * Decimal('0.95')),  # 95% of expected (simulate slippage)
            timestamps={
                'created_at': datetime.utcnow(),
                'submitted_at': datetime.utcnow(),
                'started_at': datetime.utcnow(),
                'completed_at': datetime.utcnow(),
                'settled_at': datetime.utcnow()
            }
        )
        
        # Add performance data to the presenter system
        await presenter_system.add_performance_data(trade)
        logger.info(f"Added performance data for trade {trade.id}")
        
    except Exception as e:
        logger.error(f"Error simulating trade outcome: {e}")


async def full_integration_example():
    """Comprehensive integration example."""
    try:
        logger.info("="*80)
        logger.info("STARTING COMPREHENSIVE INTEGRATION EXAMPLE")
        logger.info("="*80)
        
        # Step 1: Create mock components
        logger.info("Step 1: Creating mock components...")
        mock_scanner = MockOpportunityScanner()
        mock_kelly = MockKellyCalculator()
        mock_risk = MockRiskAnalyzer()
        mock_audit = MockAuditLogger()
        
        # Step 2: Create presenter system with full integration
        logger.info("Step 2: Creating opportunity presenter system...")
        presenter_system = await create_hitl_presenter(
            display_formats=[DisplayFormat.CONSOLE, DisplayFormat.WEB],
            max_opportunities=15,
            update_interval=3.0
        )
        
        # Step 3: Integrate all components
        logger.info("Step 3: Integrating components...")
        presenter_system.integrate_scanner(mock_scanner)
        presenter_system.integrate_kelly_calculator(mock_kelly)
        presenter_system.integrate_risk_analyzer(mock_risk)
        presenter_system.integrate_audit_logger(mock_audit)
        
        # Step 4: Start the system
        logger.info("Step 4: Starting integrated system...")
        await presenter_system.start()
        
        # Step 5: Start the mock scanner
        await mock_scanner.start()
        
        # Step 6: Add event handlers for logging
        async def log_events(event):
            logger.info(f"PRESENTATION EVENT: {event.type.value} - {event.data}")
        
        from hitl import PresentationEventType
        presenter_system.add_event_handler(PresentationEventType.OPPORTUNITY_ADDED, log_events)
        presenter_system.add_event_handler(PresentationEventType.OPPORTUNITY_RANKED, log_events)
        
        logger.info("System running with integrated components!")
        logger.info("Watch the console for opportunity presentations...")
        
        # Step 7: Run the system for demonstration
        run_duration = 30  # Run for 30 seconds
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < run_duration:
            await asyncio.sleep(1)
            
            # Occasionally simulate a trade outcome
            if (datetime.utcnow() - start_time).total_seconds() % 10 == 0:
                opportunities = list(presenter_system.get_opportunities().values())
                if opportunities:
                    await simulate_trade_outcome(presenter_system, opportunities[0])
        
        # Step 8: Show final statistics
        logger.info("="*80)
        logger.info("FINAL SYSTEM STATISTICS")
        logger.info("="*80)
        
        stats = presenter_system.get_statistics()
        for key, value in stats.items():
            logger.info(f"{key}: {value}")
        
        # Step 9: Test opportunity comparison
        opportunities = list(presenter_system.get_opportunities().values())
        if len(opportunities) >= 2:
            logger.info("Testing opportunity comparison...")
            comparison = await presenter_system.compare_opportunities(
                opportunities[0].id,
                [opp.id for opp in opportunities[1:4]]
            )
            if comparison:
                logger.info(f"Comparison completed: Primary={comparison.primary_opportunity.event_name}")
                logger.info(f"Recommended ranks: {len(comparison.recommended_ranks)} opportunities ranked")
        
        # Step 10: Show recent events
        events = presenter_system.get_events(10)
        logger.info(f"Recent events captured: {len(events)}")
        
        # Step 11: Stop all components
        logger.info("Stopping system components...")
        await mock_scanner.stop()
        await presenter_system.stop()
        
        logger.info("="*80)
        logger.info("INTEGRATION EXAMPLE COMPLETED SUCCESSFULLY!")
        logger.info("="*80)
        
        logger.info("Summary:")
        logger.info("- Console presenter: Real-time terminal interface")
        logger.info("- Web presenter: WebSocket-based real-time updates")
        logger.info("- Scanner integration: Live opportunity detection")
        logger.info("- Kelly calculator: Dynamic stake calculations")
        logger.info("- Risk analyzer: Comprehensive risk assessment")
        logger.info("- Audit logger: Complete event tracking")
        logger.info("- Historical analysis: Performance tracking")
        logger.info("- Smart ranking: Intelligent opportunity prioritization")
        
        logger.info("The system is now ready for production use!")
        
    except Exception as e:
        logger.error(f"Integration example failed: {e}")
        logger.error(f"Error details: {e.__class__.__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise


async def quick_demo():
    """Quick demonstration of key features."""
    try:
        logger.info("="*60)
        logger.info("QUICK DEMO: OPPORTUNITY PRESENTER HIGHLIGHTS")
        logger.info("="*60)
        
        # Create simple presenter
        presenter_system = await create_hitl_presenter(
            display_formats=[DisplayFormat.CONSOLE],
            max_opportunities=5
        )
        
        await presenter_system.start()
        
        # Add a few manual opportunities
        from storage.models import ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier
        
        quick_opportunities = [
            ArbitrageOpportunity(
                id=uuid4(),
                sport=Sport.FOOTBALL,
                event_name="Quick Demo Match",
                event_date=datetime.utcnow() + timedelta(hours=1),
                market_type="match_winner",
                legs=[
                    ArbitrageLeg(
                        bookmaker="DemoBook",
                        event_outcome="Team A Win",
                        odds=Decimal('2.0'),
                        implied_probability=Decimal('0.5'),
                        stake_percentage=Decimal('0.5'),
                        actual_stake=Decimal('100.00'),
                        potential_payout=Decimal('200.00')
                    ),
                    ArbitrageLeg(
                        bookmaker="DemoBook2",
                        event_outcome="Team B Win",
                        odds=Decimal('2.0'),
                        implied_probability=Decimal('0.5'),
                        stake_percentage=Decimal('0.5'),
                        actual_stake=Decimal('100.00'),
                        potential_payout=Decimal('200.00')
                    )
                ],
                total_stake=Decimal('200.00'),
                profit_margin=Decimal('0.0'),
                profit_amount=Decimal('0.00'),
                risk_tier=RiskTier.TIER_A
            )
        ]
        
        await presenter_system.add_opportunities(quick_opportunities)
        
        # Show for a few seconds
        logger.info("Displaying quick demo opportunities...")
        await asyncio.sleep(5)
        
        # Show stats
        stats = presenter_system.get_statistics()
        logger.info(f"Demo statistics: {stats}")
        
        await presenter_system.stop()
        logger.info("Quick demo completed!")
        
    except Exception as e:
        logger.error(f"Quick demo failed: {e}")
        raise


async def main():
    """Main function with demo selection."""
    import sys
    
    logger.info("OPPORTUNITY PRESENTER INTEGRATION EXAMPLES")
    logger.info("Choose demonstration type:")
    logger.info("1. Full Integration Demo (30 seconds)")
    logger.info("2. Quick Demo (10 seconds)")
    
    try:
        choice = input("Enter choice (1 or 2, default=1): ").strip()
        if not choice or choice == "1":
            await full_integration_example()
        elif choice == "2":
            await quick_demo()
        else:
            logger.info("Invalid choice, running full demo...")
            await full_integration_example()
            
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())