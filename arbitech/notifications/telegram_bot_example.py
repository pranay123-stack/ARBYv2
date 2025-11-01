"""
Example usage script for ARBitech Telegram Bot

This script demonstrates how to integrate and use the ARBitech Telegram bot
with the complete arbitrage trading system. It includes examples for:

1. Bot initialization and configuration
2. Real-time opportunity notifications
3. Trade approval workflows
4. Performance monitoring
5. Integration with ARBitech Phases 3-8
6. Error handling and monitoring

Author: ARBitech Development Team
Version: 1.0.0
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

# Add ARBitech path for imports
sys.path.append('/workspace/arbitech')

from notifications.telegram_bot import (
    ARBITechTelegramBot, create_arbitech_bot,
    BotNotification, MessageType
)
from notifications.telegram_config import config_manager

from storage.supabase_layer import SupabaseDataLayer
from storage.models import (
    ArbitrageOpportunity, ArbitrageLeg, Trade, TradeStatus,
    Sport, RiskTier
)
from detection.opportunity_scanner import OpportunityScanner
from hitl.approval_workflow import ApprovalWorkflow
from risk.risk_analyzer import RiskAnalyzer
from storage.audit_logger import AuditLogger


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ARBITechBotDemo:
    """
    Demonstration class showing ARBitech Telegram bot integration
    """
    
    def __init__(self, bot_token: str):
        """
        Initialize the demo with bot token
        
        Args:
            bot_token: Telegram bot token
        """
        self.bot_token = bot_token
        
        # Initialize components
        self.data_layer = SupabaseDataLayer()
        self.scanner = OpportunityScanner()
        self.approval_workflow = ApprovalWorkflow()
        self.risk_analyzer = RiskAnalyzer()
        self.audit_logger = AuditLogger()
        
        # Create bot
        self.bot = create_arbitech_bot(bot_token)
        
        # Demo data
        self.demo_opportunities: List[ArbitrageOpportunity] = []
        self.demo_trades: List[Trade] = []
        
        logger.info("ARBitech Bot Demo initialized")
    
    async def setup_demo_data(self) -> None:
        """Set up demo data for testing"""
        logger.info("Setting up demo data...")
        
        # Create demo arbitrage opportunities
        opportunities = [
            self._create_demo_opportunity(
                sport=Sport.FOOTBALL,
                event_name="Liverpool vs Manchester United",
                profit_margin=2.5,
                total_stake=1000.0,
                risk_tier=RiskTier.TIER_A
            ),
            self._create_demo_opportunity(
                sport=Sport.BASKETBALL,
                event_name="Lakers vs Warriors",
                profit_margin=1.8,
                total_stake=2500.0,
                risk_tier=RiskTier.TIER_B
            ),
            self._create_demo_opportunity(
                sport=Sport.TENNIS,
                event_name="Djokovic vs Nadal",
                profit_margin=3.2,
                total_stake=500.0,
                risk_tier=RiskTier.TIER_A
            ),
            self._create_demo_opportunity(
                sport=Sport.MMA,
                event_name="Conor McGregor vs Dustin Poirier",
                profit_margin=2.1,
                total_stake=1500.0,
                risk_tier=RiskTier.TIER_C
            )
        ]
        
        self.demo_opportunities = opportunities
        
        # Create demo trades
        trades = [
            self._create_demo_trade(
                opportunity=opportunities[0],
                status=TradeStatus.PENDING
            ),
            self._create_demo_trade(
                opportunity=opportunities[1],
                status=TradeStatus.FILLED
            ),
            self._create_demo_trade(
                opportunity=opportunities[2],
                status=TradeStatus.SETTLED
            )
        ]
        
        self.demo_trades = trades
        
        logger.info(f"Created {len(opportunities)} opportunities and {len(trades)} trades")
    
    def _create_demo_opportunity(
        self,
        sport: Sport,
        event_name: str,
        profit_margin: float,
        total_stake: float,
        risk_tier: RiskTier
    ) -> ArbitrageOpportunity:
        """Create a demo arbitrage opportunity"""
        
        # Create legs based on sport
        if sport == Sport.FOOTBALL:
            legs = [
                ArbitrageLeg(
                    bookmaker="Bet365",
                    event_outcome="Liverpool Win",
                    odds=Decimal("2.10"),
                    implied_probability=Decimal("0.476"),
                    stake_percentage=Decimal("0.476"),
                    actual_stake=Decimal(str(total_stake * 0.476)),
                    potential_payout=Decimal(str(total_stake * 0.476 * 2.10))
                ),
                ArbitrageLeg(
                    bookmaker="William Hill",
                    event_outcome="Draw",
                    odds=Decimal("3.80"),
                    implied_probability=Decimal("0.263"),
                    stake_percentage=Decimal("0.263"),
                    actual_stake=Decimal(str(total_stake * 0.263)),
                    potential_payout=Decimal(str(total_stake * 0.263 * 3.80))
                ),
                ArbitrageLeg(
                    bookmaker="Pinnacle",
                    event_outcome="Manchester United Win",
                    odds=Decimal("4.20"),
                    implied_probability=Decimal("0.238"),
                    stake_percentage=Decimal("0.238"),
                    actual_stake=Decimal(str(total_stake * 0.238)),
                    potential_payout=Decimal(str(total_stake * 0.238 * 4.20))
                )
            ]
        elif sport == Sport.BASKETBALL:
            legs = [
                ArbitrageLeg(
                    bookmaker="Bet365",
                    event_outcome="Lakers Win",
                    odds=Decimal("1.85"),
                    implied_probability=Decimal("0.541"),
                    stake_percentage=Decimal("0.541"),
                    actual_stake=Decimal(str(total_stake * 0.541)),
                    potential_payout=Decimal(str(total_stake * 0.541 * 1.85))
                ),
                ArbitrageLeg(
                    bookmaker="Pinnacle",
                    event_outcome="Warriors Win",
                    odds=Decimal("2.05"),
                    implied_probability=Decimal("0.488"),
                    stake_percentage=Decimal("0.488"),
                    actual_stake=Decimal(str(total_stake * 0.488)),
                    potential_payout=Decimal(str(total_stake * 0.488 * 2.05))
                )
            ]
        else:
            # Generic legs for other sports
            legs = [
                ArbitrageLeg(
                    bookmaker="Bet365",
                    event_outcome=f"{event_name} - Option 1",
                    odds=Decimal("2.00"),
                    implied_probability=Decimal("0.500"),
                    stake_percentage=Decimal("0.500"),
                    actual_stake=Decimal(str(total_stake * 0.500)),
                    potential_payout=Decimal(str(total_stake * 0.500 * 2.00))
                ),
                ArbitrageLeg(
                    bookmaker="Pinnacle",
                    event_outcome=f"{event_name} - Option 2",
                    odds=Decimal("2.00"),
                    implied_probability=Decimal("0.500"),
                    stake_percentage=Decimal("0.500"),
                    actual_stake=Decimal(str(total_stake * 0.500)),
                    potential_payout=Decimal(str(total_stake * 0.500 * 2.00))
                )
            ]
        
        # Calculate expected profit
        max_payout = max(leg.potential_payout for leg in legs)
        expected_profit = max_payout - Decimal(str(total_stake))
        
        return ArbitrageOpportunity(
            sport=sport,
            event_name=event_name,
            event_date=datetime.utcnow() + timedelta(hours=2),
            market_type="match_winner",
            legs=legs,
            total_stake=Decimal(str(total_stake)),
            profit_margin=Decimal(str(profit_margin)),
            expected_profit=expected_profit,
            risk_tier=risk_tier,
            quality_score=Decimal("0.85"),
            confidence_level=Decimal("0.92")
        )
    
    def _create_demo_trade(self, opportunity: ArbitrageOpportunity, status: TradeStatus) -> Trade:
        """Create a demo trade"""
        
        # Calculate profit based on status
        if status == TradeStatus.SETTLED:
            actual_profit = opportunity.expected_profit * Decimal("1.0")  # Full profit
        elif status == TradeStatus.FILLED:
            actual_profit = None  # Not yet settled
        else:
            actual_profit = None  # Pending
        
        return Trade(
            opportunity_id=opportunity.id,
            user_id="demo_user_123",  # Demo user
            status=status,
            execution_mode="manual",
            legs=[
                {
                    "bookmaker": leg.bookmaker,
                    "event_outcome": leg.event_outcome,
                    "odds": float(leg.odds),
                    "stake": float(leg.actual_stake),
                    "status": "filled" if status in [TradeStatus.FILLED, TradeStatus.SETTLED] else "pending"
                }
                for leg in opportunity.legs
            ],
            total_stake=opportunity.total_stake,
            expected_profit=opportunity.expected_profit,
            actual_profit=actual_profit,
            execution_time=datetime.utcnow() - timedelta(minutes=30) if status != TradeStatus.PENDING else None
        )
    
    async def simulate_opportunity_detection(self) -> None:
        """Simulate real-time opportunity detection and notification"""
        logger.info("Simulating opportunity detection...")
        
        # Send notifications for each opportunity
        for i, opportunity in enumerate(self.demo_opportunities):
            logger.info(f"Sending opportunity {i+1}: {opportunity.event_name}")
            
            # Simulate delay for realistic detection
            await asyncio.sleep(2)
            
            # Send opportunity alert through bot
            await self.bot.send_opportunity_alert(opportunity)
            
            logger.info(f"✅ Opportunity {opportunity.id} notification sent")
    
    async def simulate_trade_updates(self) -> None:
        """Simulate trade status updates"""
        logger.info("Simulating trade updates...")
        
        for i, trade in enumerate(self.demo_trades):
            if trade.status == TradeStatus.PENDING:
                # Simulate approval and execution
                await asyncio.sleep(3)
                
                # Update trade to FILLED
                trade.status = TradeStatus.FILLED
                await self.bot.send_trade_update(trade, "Trade Filled")
                
                logger.info(f"✅ Trade {trade.id} filled notification sent")
                
                # Simulate settlement after a delay
                await asyncio.sleep(5)
                trade.status = TradeStatus.SETTLED
                trade.actual_profit = trade.expected_profit * Decimal("1.0")
                
                await self.bot.send_trade_update(trade, "Trade Settled")
                logger.info(f"✅ Trade {trade.id} settled notification sent")
    
    async def simulate_risk_alerts(self) -> None:
        """Simulate risk alerts"""
        logger.info("Simulating risk alerts...")
        
        # Create risk alert data
        risk_alert = {
            "alert_type": "high_exposure",
            "severity": "high",
            "description": "High exposure detected in Football markets",
            "details": {
                "market": "Football",
                "exposure_amount": 15000.0,
                "recommended_action": "reduce_position_sizes"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await asyncio.sleep(5)
        await self.bot.send_risk_alert(risk_alert)
        
        logger.info("✅ Risk alert notification sent")
    
    async def demonstrate_performance_reporting(self) -> None:
        """Demonstrate performance report generation"""
        logger.info("Demonstrating performance reporting...")
        
        # Simulate performance data collection
        await asyncio.sleep(2)
        
        # This would normally be triggered by /performance command
        # For demo purposes, we'll show the method
        logger.info("📊 Performance report functionality ready")
        logger.info("Users can request reports using /performance command")
    
    async def run_demo_scenarios(self) -> None:
        """Run all demonstration scenarios"""
        logger.info("🚀 Starting ARBitech Telegram Bot Demo")
        logger.info("=" * 60)
        
        try:
            # Setup demo data
            await self.setup_demo_data()
            
            # Initialize bot (but don't run polling in demo)
            await self.bot.initialize()
            
            # Run demonstration scenarios
            await self.simulate_opportunity_detection()
            await self.simulate_trade_updates()
            await self.simulate_risk_alerts()
            await self.demonstrate_performance_reporting()
            
            logger.info("=" * 60)
            logger.info("✅ Demo completed successfully!")
            logger.info("📱 Bot is ready to receive commands")
            logger.info("💡 Use /start in Telegram to interact with the bot")
            
            # Keep bot running for interaction
            logger.info("🔄 Bot will continue running for 5 minutes for testing...")
            await asyncio.sleep(300)  # Run for 5 minutes
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            raise
        finally:
            await self.bot.shutdown()


async def interactive_bot_session(bot_token: str) -> None:
    """Run an interactive bot session for testing"""
    logger.info("🤖 Starting Interactive Bot Session")
    
    try:
        # Create and initialize bot
        bot = create_arbitech_bot(bot_token)
        await bot.initialize()
        
        logger.info("✅ Bot initialized successfully")
        logger.info("📱 Send /start to your bot on Telegram")
        logger.info("💡 Demo commands:")
        logger.info("   • /start - Initialize and authenticate")
        logger.info("   • /menu - Open main menu")
        logger.info("   • /opportunities - View opportunities")
        logger.info("   • /performance - View performance")
        logger.info("   • /status - Check system status")
        logger.info("   • /settings - Configure preferences")
        logger.info("   • Use authentication code: VIEW, TRADER, or ADMIN2024")
        
        # Run the bot (this is blocking)
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Bot session interrupted by user")
    except Exception as e:
        logger.error(f"Bot session failed: {e}")
        raise


async def integration_test() -> None:
    """Test bot integration with ARBitech system components"""
    logger.info("🔧 Testing ARBitech Integration")
    
    try:
        # Test data layer connection
        data_layer = SupabaseDataLayer()
        health_check = await data_layer.health_check()
        logger.info(f"📊 Database connection: {'✅' if health_check else '❌'}")
        
        # Test opportunity scanner
        scanner = OpportunityScanner()
        logger.info("🔍 Opportunity scanner: ✅ Ready")
        
        # Test risk analyzer
        risk_analyzer = RiskAnalyzer()
        logger.info("⚠️ Risk analyzer: ✅ Ready")
        
        # Test approval workflow
        approval_workflow = ApprovalWorkflow()
        logger.info("✅ Approval workflow: ✅ Ready")
        
        # Test audit logger
        audit_logger = AuditLogger()
        logger.info("📝 Audit logger: ✅ Ready")
        
        logger.info("✅ All ARBitech components are ready for integration")
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        raise


async def load_configuration_demo() -> None:
    """Demonstrate configuration loading"""
    logger.info("⚙️ Loading Bot Configuration")
    
    try:
        # Load configuration from environment
        config_manager.load_from_environment()
        
        # Display configuration summary
        logger.info(config_manager.get_config_summary())
        
        # Validate configuration
        logger.info("🔍 Validating configuration...")
        
        errors = config_manager.validate_all_configs(
            config_manager.telegram_config,
            config_manager.notification_config,
            config_manager.feature_config,
            config_manager.integration_config
        )
        
        for config_type, config_errors in errors.items():
            if config_errors:
                logger.error(f"❌ {config_type} config errors:")
                for error in config_errors:
                    logger.error(f"   • {error}")
            else:
                logger.info(f"✅ {config_type} config is valid")
        
        logger.info("✅ Configuration loading complete")
        
    except Exception as e:
        logger.error(f"Configuration loading failed: {e}")
        raise


async def main():
    """Main demo function"""
    
    # Get bot token from environment or prompt
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("🤖 ARBitech Telegram Bot Demo")
        print("=" * 40)
        print("Please provide your Telegram bot token:")
        print("1. Create a bot with @BotFather on Telegram")
        print("2. Get your bot token")
        print("3. Set environment variable: export TELEGRAM_BOT_TOKEN=your_token")
        print("4. Run this demo again")
        print()
        
        # For demo purposes, we can still run integration tests
        bot_token = "DEMO_TOKEN"
    
    print(f"🚀 Starting ARBitech Telegram Bot Demo")
    print(f"Token: {'✅ Configured' if bot_token != 'DEMO_TOKEN' else '❌ Demo Mode'}")
    
    try:
        # Load configuration
        await load_configuration_demo()
        
        # Run integration tests
        await integration_test()
        
        if bot_token != "DEMO_TOKEN":
            # Run full demo with actual bot
            demo = ARBITechBotDemo(bot_token)
            await demo.run_demo_scenarios()
            
            # Optionally run interactive session
            print("\n🤖 Run interactive bot session? (y/N): ", end="")
            if input().lower().startswith('y'):
                await interactive_bot_session(bot_token)
        else:
            # Run demo without actual bot (demo mode)
            demo = ARBITechBotDemo("DEMO_TOKEN")
            await demo.run_demo_scenarios()
    
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)
        exit(1)
    
    print("\n✅ Demo completed!")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
