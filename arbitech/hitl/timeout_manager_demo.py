"""
Comprehensive Demo and Testing for Timeout Manager

This module provides a complete demonstration of the timeout management system,
including all features, performance testing, and integration examples.
"""

import asyncio
import logging
import time
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.models import (
    ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier,
    NotificationType, NotificationPriority
)
from hitl.timeout_manager import (
    TimeoutManager, TimeoutRule, TimeoutEvent,
    TimeoutStatus, EscalationAction
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TimeoutManagerDemo:
    """Comprehensive demo of the timeout manager."""
    
    def __init__(self):
        self.timeout_manager = TimeoutManager(
            check_interval_ms=100,
            enable_performance_monitoring=True
        )
        self.test_opportunities = []
    
    def create_sample_opportunities(self) -> List[ArbitrageOpportunity]:
        """Create sample arbitrage opportunities for testing."""
        opportunities = []
        
        # High-profit, low-risk opportunity
        high_profit_opp = ArbitrageOpportunity(
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
                    stake_percentage=Decimal("0.5"),
                    actual_stake=Decimal("50.00"),
                    potential_payout=Decimal("105.00")
                ),
                ArbitrageLeg(
                    bookmaker="william_hill",
                    event_outcome="Liverpool wins",
                    odds=Decimal("1.90"),
                    implied_probability=Decimal("0.526"),
                    stake_percentage=Decimal("0.5"),
                    actual_stake=Decimal("50.00"),
                    potential_payout=Decimal("95.00")
                )
            ],
            total_stake=Decimal("100.00"),
            profit_margin=Decimal("0.08"),  # 8% profit margin
            profit_amount=Decimal("8.00"),
            risk_tier=RiskTier.TIER_A
        )
        opportunities.append(high_profit_opp)
        
        # Medium-profit, medium-risk opportunity
        medium_profit_opp = ArbitrageOpportunity(
            sport=Sport.TENNIS,
            event_name="Djokovic vs Nadal",
            event_date=datetime.utcnow() + timedelta(hours=1),
            market_type="match_winner",
            legs=[
                ArbitrageLeg(
                    bookmaker="pinnacle",
                    event_outcome="Djokovic wins",
                    odds=Decimal("1.85"),
                    implied_probability=Decimal("0.541"),
                    stake_percentage=Decimal("0.52"),
                    actual_stake=Decimal("52.00"),
                    potential_payout=Decimal("96.20")
                ),
                ArbitrageLeg(
                    bookmaker="betway",
                    event_outcome="Nadal wins",
                    odds=Decimal("2.05"),
                    implied_probability=Decimal("0.488"),
                    stake_percentage=Decimal("0.48"),
                    actual_stake=Decimal("48.00"),
                    potential_payout=Decimal("98.40")
                )
            ],
            total_stake=Decimal("100.00"),
            profit_margin=Decimal("0.044"),  # 4.4% profit margin
            profit_amount=Decimal("4.40"),
            risk_tier=RiskTier.TIER_B
        )
        opportunities.append(medium_profit_opp)
        
        # Low-profit, high-risk opportunity
        low_profit_opp = ArbitrageOpportunity(
            sport=Sport.ESPORTS,
            event_name="Team A vs Team B",
            event_date=datetime.utcnow() + timedelta(minutes=30),
            market_type="match_winner",
            legs=[
                ArbitrageLeg(
                    bookmaker="draftkings",
                    event_outcome="Team A wins",
                    odds=Decimal("1.75"),
                    implied_probability=Decimal("0.571"),
                    stake_percentage=Decimal("0.55"),
                    actual_stake=Decimal("55.00"),
                    potential_payout=Decimal("96.25")
                ),
                ArbitrageLeg(
                    bookmaker="fanduel",
                    event_outcome="Team B wins",
                    odds=Decimal("2.15"),
                    implied_probability=Decimal("0.465"),
                    stake_percentage=Decimal("0.45"),
                    actual_stake=Decimal("45.00"),
                    potential_payout=Decimal("96.75")
                )
            ],
            total_stake=Decimal("100.00"),
            profit_margin=Decimal("0.025"),  # 2.5% profit margin
            profit_amount=Decimal("2.50"),
            risk_tier=RiskTier.TIER_D
        )
        opportunities.append(low_profit_opp)
        
        # Basketball opportunity with different market type
        basketball_opp = ArbitrageOpportunity(
            sport=Sport.BASKETBALL,
            event_name="Lakers vs Celtics",
            event_date=datetime.utcnow() + timedelta(hours=3),
            market_type="over_under",
            legs=[
                ArbitrageLeg(
                    bookmaker="bet365",
                    event_outcome="Over 210.5",
                    odds=Decimal("1.91"),
                    implied_probability=Decimal("0.524"),
                    stake_percentage=Decimal("0.51"),
                    actual_stake=Decimal("51.00"),
                    potential_payout=Decimal("97.41")
                ),
                ArbitrageLeg(
                    bookmaker="william_hill",
                    event_outcome="Under 210.5",
                    odds=Decimal("1.95"),
                    implied_probability=Decimal("0.513"),
                    stake_percentage=Decimal("0.49"),
                    actual_stake=Decimal("49.00"),
                    potential_payout=Decimal("95.55")
                )
            ],
            total_stake=Decimal("100.00"),
            profit_margin=Decimal("0.039"),  # 3.9% profit margin
            profit_amount=Decimal("3.90"),
            risk_tier=RiskTier.TIER_C
        )
        opportunities.append(basketball_opp)
        
        return opportunities
    
    def setup_custom_rules(self):
        """Setup custom timeout rules for testing."""
        
        # High-frequency trading rule
        hf_rule = TimeoutRule(
            name="High-Frequency Trading",
            description="Very short timeouts for high-frequency opportunities",
            sport=Sport.ESPORTS,
            base_timeout_seconds=15,
            min_timeout_seconds=5,
            max_timeout_seconds=30,
            urgency_multiplier=Decimal('0.6'),
            enable_escalation=True,
            escalation_threshold_seconds=8,
            max_escalations=2,
            escalation_actions=[
                EscalationAction.NOTIFY_USER,
                EscalationAction.AUTO_REJECT
            ]
        )
        self.timeout_manager.add_rule(hf_rule)
        
        # Premium user rule
        premium_rule = TimeoutRule(
            name="Premium User Extended",
            description="Extended timeouts for premium users",
            base_timeout_seconds=90,
            min_timeout_seconds=30,
            max_timeout_seconds=180,
            profit_margin_multiplier=Decimal('2.0'),
            liquidity_factor=Decimal('1.5'),
            enable_escalation=False  # Premium users get full time
        )
        self.timeout_manager.add_rule(premium_rule)
        
        # Football-specific rule
        football_rule = TimeoutRule(
            name="Football Extended",
            description="Extended timeouts for football markets",
            sport=Sport.FOOTBALL,
            base_timeout_seconds=60,
            liquidity_factor=Decimal('1.3'),
            max_escalations=4,
            escalation_actions=[
                EscalationAction.EXTEND_TIMEOUT,
                EscalationAction.NOTIFY_USER
            ]
        )
        self.timeout_manager.add_rule(football_rule)
        
        logger.info("Custom rules setup complete")
    
    def register_demo_callbacks(self):
        """Register demonstration callbacks."""
        
        def on_timeout_created(data):
            logger.info(f"🚨 TIMEOUT CREATED: {data['opportunity_id']} - {data['timeout_seconds']:.1f}s")
        
        def on_timeout_expired(data):
            logger.warning(f"⏰ TIMEOUT EXPIRED: {data['opportunity_id']}")
        
        def on_timeout_extended(data):
            logger.info(f"⏳ TIMEOUT EXTENDED: {data['opportunity_id']} +{data['additional_seconds']:.1f}s")
        
        def on_timeout_escalated(data):
            logger.warning(f"🚨 ESCALATION: {data['opportunity_id']} - {data['time_remaining']:.1f}s remaining")
        
        def on_opportunity_auto_rejected(data):
            logger.error(f"❌ AUTO-REJECTED: {data['opportunity_id']} - {data['reason']}")
        
        # Register callbacks
        self.timeout_manager.register_timeout_callback('timeout_created', on_timeout_created)
        self.timeout_manager.register_timeout_callback('timeout_expired', on_timeout_expired)
        self.timeout_manager.register_timeout_callback('timeout_extended', on_timeout_extended)
        self.timeout_manager.register_timeout_callback('timeout_escalated', on_timeout_escalated)
        self.timeout_manager.register_timeout_callback('opportunity_auto_rejected', on_opportunity_auto_rejected)
        
        logger.info("Demo callbacks registered")
    
    async def run_basic_demo(self):
        """Run basic timeout management demonstration."""
        logger.info("=" * 60)
        logger.info("BASIC TIMEOUT MANAGEMENT DEMO")
        logger.info("=" * 60)
        
        # Setup
        self.setup_custom_rules()
        self.register_demo_callbacks()
        
        # Create opportunities
        opportunities = self.create_sample_opportunities()
        
        # Create timeouts for each opportunity
        created_timeouts = []
        for i, opp in enumerate(opportunities):
            logger.info(f"\nCreating timeout for opportunity {i+1}: {opp.event_name}")
            logger.info(f"  Sport: {opp.sport.value}")
            logger.info(f"  Profit Margin: {opp.profit_margin:.1%}")
            logger.info(f"  Risk Tier: {opp.risk_tier.value}")
            
            timeout_id, expiration_time = self.timeout_manager.create_timeout(opp)
            created_timeouts.append((opp.id, timeout_id, expiration_time))
            
            remaining = self.timeout_manager.get_timeout_remaining(opp.id)
            status = self.timeout_manager.get_timeout_status(opp.id)
            logger.info(f"  Timeout: {remaining:.1f}s remaining, status: {status.value}")
        
        # Monitor timeouts for a few seconds
        logger.info("\nMonitoring timeouts...")
        for check_round in range(5):
            await asyncio.sleep(3)
            
            logger.info(f"\n--- Check Round {check_round + 1} ---")
            for opp_id, timeout_id, expiration_time in created_timeouts:
                remaining = self.timeout_manager.get_timeout_remaining(opp_id)
                status = self.timeout_manager.get_timeout_status(opp_id)
                if remaining is not None:
                    logger.info(f"  {opp_id}: {remaining:.1f}s remaining, status: {status.value}")
        
        # Test extension
        logger.info("\nTesting timeout extension...")
        if opportunities:
            first_opp = opportunities[0]
            extended = self.timeout_manager.extend_timeout(
                first_opp.id, 
                30.0, 
                "demo_extension"
            )
            if extended:
                remaining = self.timeout_manager.get_timeout_remaining(first_opp.id)
                logger.info(f"Extended timeout for {first_opp.event_name}, now {remaining:.1f}s remaining")
    
    async def run_performance_demo(self):
        """Run performance and stress testing demo."""
        logger.info("=" * 60)
        logger.info("PERFORMANCE AND STRESS TEST DEMO")
        logger.info("=" * 60)
        
        # Create many opportunities for stress testing
        stress_opportunities = []
        for i in range(50):  # Create 50 opportunities
            opp = ArbitrageOpportunity(
                sport=Sport.FOOTBALL if i % 3 == 0 else Sport.BASKETBALL if i % 3 == 1 else Sport.TENNIS,
                event_name=f"Stress Test Match {i+1}",
                event_date=datetime.utcnow() + timedelta(minutes=i),
                market_type="match_winner",
                legs=[
                    ArbitrageLeg(
                        bookmaker=f"bookmaker_{i % 5}",
                        event_outcome="Team A wins",
                        odds=Decimal(f"{1.8 + (i % 10) * 0.05}"),
                        implied_probability=Decimal("0.55"),
                        stake_percentage=Decimal("0.5"),
                        actual_stake=Decimal("50.00"),
                        potential_payout=Decimal("90.00")
                    ),
                    ArbitrageLeg(
                        bookmaker=f"bookmaker_{(i+1) % 5}",
                        event_outcome="Team B wins",
                        odds=Decimal(f"{2.0 + (i % 10) * 0.05}"),
                        implied_probability=Decimal("0.45"),
                        stake_percentage=Decimal("0.5"),
                        actual_stake=Decimal("50.00"),
                        potential_payout=Decimal("100.00")
                    )
                ],
                total_stake=Decimal("100.00"),
                profit_margin=Decimal(f"{0.02 + (i % 10) * 0.01}"),
                profit_amount=Decimal(f"{2.0 + i}"),
                risk_tier=[RiskTier.TIER_A, RiskTier.TIER_B, RiskTier.TIER_C, RiskTier.TIER_D][i % 4]
            )
            stress_opportunities.append(opp)
        
        # Create timeouts for all opportunities
        logger.info(f"Creating {len(stress_opportunities)} timeouts...")
        start_time = time.time()
        
        for i, opp in enumerate(stress_opportunities):
            self.timeout_manager.create_timeout(opp, custom_timeout_seconds=20.0 + i % 10)
        
        creation_time = time.time() - start_time
        logger.info(f"Created {len(stress_opportunities)} timeouts in {creation_time:.2f}s")
        
        # Monitor performance
        logger.info("Monitoring performance...")
        for check_round in range(10):
            await asyncio.sleep(1)
            
            metrics = self.timeout_manager.get_metrics()
            near_timeout = self.timeout_manager.get_opportunities_near_timeout(
                threshold_seconds=5.0, 
                limit=10
            )
            
            if check_round % 2 == 0:  # Log every other check
                logger.info(
                    f"Round {check_round + 1}: "
                    f"{metrics.active_opportunities} active, "
                    f"{len(near_timeout)} near timeout, "
                    f"{metrics.average_check_time_ms:.2f}ms avg check time"
                )
        
        # Final metrics
        final_metrics = self.timeout_manager.get_metrics()
        logger.info("\nFinal Performance Metrics:")
        logger.info(f"  Total opportunities: {final_metrics.total_opportunities}")
        logger.info(f"  Active opportunities: {final_metrics.active_opportunities}")
        logger.info(f"  Expired opportunities: {final_metrics.expired_opportunities}")
        logger.info(f"  Extended opportunities: {final_metrics.extended_opportunities}")
        logger.info(f"  Escalated opportunities: {final_metrics.escalated_opportunities}")
        logger.info(f"  Total escalations: {final_metrics.total_escalations}")
        logger.info(f"  Average check time: {final_metrics.average_check_time_ms:.2f}ms")
        logger.info(f"  Max check time: {final_metrics.max_check_time_ms:.2f}ms")
        logger.info(f"  Check frequency: {final_metrics.check_frequency_hz:.1f} Hz")
    
    async def run_integration_demo(self):
        """Run integration testing demo."""
        logger.info("=" * 60)
        logger.info("INTEGRATION DEMO")
        logger.info("=" * 60)
        
        # Demonstrate integration with other components
        from hitl.timeout_manager import integrate_with_opportunity_scanner, integrate_with_arbitrage_executor
        
        # Mock scanner class
        class MockScanner:
            def __init__(self):
                self.callbacks = {}
            
            def register_callback(self, event_type, callback):
                self.callbacks[event_type] = callback
            
            def simulate_opportunity_found(self, opportunity):
                if 'opportunity_found' in self.callbacks:
                    self.callbacks['opportunity_found']({'opportunity': opportunity})
        
        # Mock executor class
        class MockExecutor:
            def __init__(self):
                self.callbacks = {}
            
            def register_callback(self, event_type, callback):
                self.callbacks[event_type] = callback
            
            def simulate_execution_start(self, opportunity_id):
                if 'execution_started' in self.callbacks:
                    self.callbacks['execution_started']({'opportunity_id': opportunity_id})
        
        # Create mock components
        mock_scanner = MockScanner()
        mock_executor = MockExecutor()
        
        # Integrate
        integrate_with_opportunity_scanner(self.timeout_manager, mock_scanner)
        integrate_with_arbitrage_executor(self.timeout_manager, mock_executor)
        
        logger.info("Integrated with mock scanner and executor")
        
        # Test integration
        opportunities = self.create_sample_opportunities()
        
        for opp in opportunities[:2]:  # Test with first 2 opportunities
            # Simulate opportunity being found
            mock_scanner.simulate_opportunity_found(opp)
            
            # Wait a bit
            await asyncio.sleep(0.5)
            
            # Check timeout was created
            status = self.timeout_manager.get_timeout_status(opp.id)
            logger.info(f"Status after scanner integration: {status.value}")
            
            # Simulate execution start
            mock_executor.simulate_execution_start(opp.id)
            
            # Check timeout was removed
            status = self.timeout_manager.get_timeout_status(opp.id)
            logger.info(f"Status after executor integration: {status.value}")
    
    async def run_cleanup_demo(self):
        """Run cleanup and maintenance demo."""
        logger.info("=" * 60)
        logger.info("CLEANUP AND MAINTENANCE DEMO")
        logger.info("=" * 60)
        
        # Create some old entries by manipulating timestamps
        # (This is a simplified demo - in real usage, you'd have actual old entries)
        
        # Show export functionality
        export_data = self.timeout_manager.export_timeout_data()
        logger.info("Exported timeout data:")
        logger.info(f"  Active timeouts: {export_data['active_timeouts']}")
        logger.info(f"  Total rules: {export_data['total_rules']}")
        
        # Show metrics
        metrics = self.timeout_manager.get_metrics()
        logger.info("\nCurrent metrics:")
        logger.info(f"  Memory usage: {metrics.memory_usage_mb:.1f} MB")
        logger.info(f"  CPU usage: {metrics.cpu_usage_percent:.1f}%")
        
        # Cleanup (would clean up old entries in real usage)
        self.timeout_manager.cleanup_expired_entries(max_age_hours=1)
        logger.info("Cleanup completed")
    
    async def run_comprehensive_demo(self):
        """Run comprehensive demonstration of all features."""
        logger.info("🚀 STARTING COMPREHENSIVE TIMEOUT MANAGER DEMO")
        logger.info("=" * 80)
        
        # Start monitoring
        self.timeout_manager.start_monitoring()
        logger.info("✅ Timeout monitoring started")
        
        try:
            # Run all demos
            await self.run_basic_demo()
            await asyncio.sleep(2)  # Brief pause between demos
            
            await self.run_performance_demo()
            await asyncio.sleep(2)
            
            await self.run_integration_demo()
            await asyncio.sleep(2)
            
            await self.run_cleanup_demo()
            
            # Final summary
            logger.info("=" * 80)
            logger.info("🎉 COMPREHENSIVE DEMO COMPLETED")
            logger.info("=" * 80)
            
            final_metrics = self.timeout_manager.get_metrics()
            logger.info("\nFinal Summary:")
            logger.info(f"  📊 Total opportunities processed: {final_metrics.total_opportunities}")
            logger.info(f"  ⏰ Active timeouts: {final_metrics.active_opportunities}")
            logger.info(f"  ❌ Expired timeouts: {final_metrics.expired_opportunities}")
            logger.info(f"  🔄 Extended timeouts: {final_metrics.extended_opportunities}")
            logger.info(f"  🚨 Escalated timeouts: {final_metrics.escalated_opportunities}")
            logger.info(f"  📈 Total escalations: {final_metrics.total_escalations}")
            logger.info(f"  ⚡ Average check time: {final_metrics.average_check_time_ms:.2f}ms")
            logger.info(f"  🚀 Peak check frequency: {final_metrics.check_frequency_hz:.1f} Hz")
            
            if final_metrics.escalations_by_type:
                logger.info("\nEscalations by type:")
                for action, count in final_metrics.escalations_by_type.items():
                    logger.info(f"  {action.value}: {count}")
            
        finally:
            # Stop monitoring
            self.timeout_manager.stop_monitoring()
            logger.info("⏹️ Timeout monitoring stopped")


async def main():
    """Main demo function."""
    demo = TimeoutManagerDemo()
    await demo.run_comprehensive_demo()


if __name__ == "__main__":
    print("🚀 Starting Timeout Manager Comprehensive Demo")
    print("This demo showcases all features of the timeout management system:")
    print("  • Dynamic timeout calculation")
    print("  • Escalation and notification") 
    print("  • Performance optimization")
    print("  • Integration capabilities")
    print("  • Custom rules per user/bookmaker/sport")
    print("  • High-frequency monitoring")
    print("=" * 80)
    
    # Run the demo
    asyncio.run(main())
    
    print("\n✅ Demo completed successfully!")
    print("The timeout manager is ready for production use.")