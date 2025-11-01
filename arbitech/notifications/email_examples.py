#!/usr/bin/env python3
"""
Email Notification System Example

This script demonstrates how to use the ARBitech email notification system
with different email providers and notification types.
"""

import asyncio
import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

# Import ARBitech components
from storage.models import (
    ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier, 
    Trade, TradeStatus, ExecutionMode, StakeData
)

# Import email notification system
from notifications import (
    EmailNotificationSystem,
    get_gmail_config,
    get_outlook_config,
    get_sendgrid_config,
    UserEmailPreferences,
    EmailPriority,
    demo_email_system
)


async def example_gmail_setup():
    """Example: Setting up Gmail email notifications."""
    print("=== Gmail Email System Example ===")
    
    # Gmail configuration (requires app password)
    # Get these from environment variables for security
    username = os.getenv("GMAIL_USERNAME", "your-email@gmail.com")
    app_password = os.getenv("GMAIL_APP_PASSWORD", "your-16-char-app-password")
    
    if username == "your-email@gmail.com" or app_password == "your-16-char-app-password":
        print("⚠️  Please set GMAIL_USERNAME and GMAIL_APP_PASSWORD environment variables")
        print("   Get app password from: https://myaccount.google.com/apppasswords")
        return None
    
    try:
        # Create email system
        config = get_gmail_config(username, app_password, "ARBitech Trading")
        email_system = EmailNotificationSystem(config)
        
        print(f"✅ Email system initialized for {username}")
        return email_system
        
    except Exception as e:
        print(f"❌ Failed to initialize Gmail system: {e}")
        return None


async def example_send_opportunity_alert(email_system: EmailNotificationSystem):
    """Example: Sending an opportunity alert."""
    print("\n=== Sending Opportunity Alert ===")
    
    if not email_system:
        print("❌ Email system not available")
        return
    
    try:
        # Create sample arbitrage opportunity
        opportunity = ArbitrageOpportunity(
            sport=Sport.FOOTBALL,
            event_name="Manchester United vs Liverpool",
            event_date=datetime.utcnow() + timedelta(days=1),
            market_type="Match Winner",
            legs=[
                ArbitrageLeg(
                    bookmaker="Bet365",
                    event_outcome="Manchester United Win",
                    odds=Decimal("2.10"),
                    implied_probability=Decimal("0.476"),
                    stake_percentage=Decimal("0.487"),
                    actual_stake=Decimal("48.70"),
                    potential_payout=Decimal("102.27")
                ),
                ArbitrageLeg(
                    bookmaker="William Hill",
                    event_outcome="Liverpool Win",
                    odds=Decimal("1.95"),
                    implied_probability=Decimal("0.513"),
                    stake_percentage=Decimal("0.513"),
                    actual_stake=Decimal("51.30"),
                    potential_payout=Decimal("100.04")
                )
            ],
            total_stake=Decimal("100.00"),
            profit_margin=Decimal("0.0223"),
            profit_amount=Decimal("2.23"),
            risk_tier=RiskTier.TIER_A
        )
        
        # Send opportunity alert
        user_id = str(uuid4())
        success = await email_system.send_opportunity_alert(
            user_id=user_id,
            opportunity=opportunity,
            custom_message="High confidence opportunity based on historical data!",
            include_screenshot=True
        )
        
        if success:
            print(f"✅ Opportunity alert queued for user {user_id}")
            print(f"   Event: {opportunity.event_name}")
            print(f"   Profit: {opportunity.profit_amount:.2f} ({opportunity.profit_margin*100:.1f}%)")
        else:
            print("❌ Failed to queue opportunity alert")
            
    except Exception as e:
        print(f"❌ Error sending opportunity alert: {e}")


async def example_send_trade_update(email_system: EmailNotificationSystem):
    """Example: Sending a trade update."""
    print("\n=== Sending Trade Update ===")
    
    if not email_system:
        print("❌ Email system not available")
        return
    
    try:
        # Create sample trade
        stake_data = StakeData(
            total_stake=Decimal("200.00"),
            currency="USD",
            leg_allocations={"Bet365": Decimal("100.00"), "William Hill": Decimal("100.00")},
            fees_included=Decimal("2.00"),
            net_stake=Decimal("198.00")
        )
        
        trade = Trade(
            user_id=uuid4(),
            opportunity=ArbitrageOpportunity(
                sport=Sport.FOOTBALL,
                event_name="Arsenal vs Chelsea",
                event_date=datetime.utcnow() + timedelta(days=2),
                market_type="Match Winner",
                legs=[
                    ArbitrageLeg(
                        bookmaker="Bet365",
                        event_outcome="Arsenal Win",
                        odds=Decimal("1.90"),
                        implied_probability=Decimal("0.526"),
                        stake_percentage=Decimal("0.5"),
                        actual_stake=Decimal("100.00"),
                        potential_payout=Decimal("190.00")
                    ),
                    ArbitrageLeg(
                        bookmaker="William Hill",
                        event_outcome="Chelsea Win",
                        odds=Decimal("2.20"),
                        implied_probability=Decimal("0.455"),
                        stake_percentage=Decimal("0.5"),
                        actual_stake=Decimal("100.00"),
                        potential_payout=Decimal("220.00")
                    )
                ],
                total_stake=Decimal("200.00"),
                profit_margin=Decimal("0.047"),
                profit_amount=Decimal("9.00"),
                risk_tier=RiskTier.TIER_A
            ),
            execution_mode=ExecutionMode.AUTO_STEALTH,
            stake_data=stake_data,
            expected_profit=Decimal("9.00"),
            execution_time_ms=4500,
            status=TradeStatus.FILLED
        )
        
        # Send trade update
        user_id = str(trade.user_id)
        success = await email_system.send_trade_update(
            user_id=user_id,
            trade=trade,
            include_screenshot=True
        )
        
        if success:
            print(f"✅ Trade update queued for user {user_id}")
            print(f"   Status: {trade.status.value}")
            print(f"   Expected Profit: {trade.expected_profit:.2f} {trade.stake_data.currency}")
            print(f"   Execution Time: {trade.execution_time_ms}ms")
        else:
            print("❌ Failed to queue trade update")
            
    except Exception as e:
        print(f"❌ Error sending trade update: {e}")


async def example_send_risk_warning(email_system: EmailNotificationSystem):
    """Example: Sending a risk warning."""
    print("\n=== Sending Risk Warning ===")
    
    if not email_system:
        print("❌ Email system not available")
        return
    
    try:
        # Send risk warning
        user_id = str(uuid4())
        success = await email_system.send_risk_warning(
            user_id=user_id,
            alert_type="position_limit",
            severity="high",
            title="Position Limit Approaching",
            description="Your current position size is approaching the configured limit. Consider reducing exposure.",
            risk_metrics={
                "Current Exposure": "$1,850.00",
                "Position Limit": "$2,000.00",
                "Utilization": "92.5%",
                "Risk Score": "Medium"
            },
            recommended_action="Reduce position size or increase limit in risk settings."
        )
        
        if success:
            print(f"✅ Risk warning queued for user {user_id}")
            print("   Alert: Position Limit Approaching")
            print("   Severity: High")
            print("   Utilization: 92.5%")
        else:
            print("❌ Failed to queue risk warning")
            
    except Exception as e:
        print(f"❌ Error sending risk warning: {e}")


async def example_send_profit_report(email_system: EmailNotificationSystem):
    """Example: sending a profit report."""
    print("\n=== Sending Profit Report ===")
    
    if not email_system:
        print("❌ Email system not available")
        return
    
    try:
        # Send profit report
        user_id = str(uuid4())
        success = await email_system.send_profit_report(
            user_id=user_id,
            period="Week of December 2-8, 2024",
            total_profit=Decimal("247.85"),
            trades_count=12,
            success_rate=85.7,
            performance_metrics={
                "avg_profit_per_trade": 20.65,
                "best_trade": 45.30,
                "worst_trade": -8.50,
                "total_trades": 12
            },
            include_charts=True
        )
        
        if success:
            print(f"✅ Profit report queued for user {user_id}")
            print("   Period: Week of December 2-8, 2024")
            print("   Total Profit: $247.85")
            print("   Trades: 12 (85.7% success rate)")
        else:
            print("❌ Failed to queue profit report")
            
    except Exception as e:
        print(f"❌ Error sending profit report: {e}")


async def example_user_preferences():
    """Example: Setting up user email preferences."""
    print("\n=== User Email Preferences ===")
    
    try:
        # Create user preferences
        preferences = UserEmailPreferences(
            user_id=str(uuid4()),
            email="user@example.com",
            name="Demo User",
            opportunity_alerts=True,
            trade_updates=True,
            risk_warnings=True,
            profit_reports=True,
            weekly_reports=False,
            monthly_reports=True,
            frequency="immediate",
            quiet_hours_start="22:00",  # 10 PM
            quiet_hours_end="08:00",    # 8 AM
            timezone="America/New_York",
            include_screenshots=True,
            include_charts=True,
            detailed_reports=True,
            html_emails=True,
            text_emails=False
        )
        
        print(f"✅ Created preferences for user {preferences.user_id}")
        print(f"   Email: {preferences.email}")
        print(f"   Opportunity Alerts: {preferences.opportunity_alerts}")
        print(f"   Trade Updates: {preferences.trade_updates}")
        print(f"   Risk Warnings: {preferences.risk_warnings}")
        print(f"   Quiet Hours: {preferences.quiet_hours_start} - {preferences.quiet_hours_end}")
        
        return preferences
        
    except Exception as e:
        print(f"❌ Error creating user preferences: {e}")
        return None


async def example_system_monitoring(email_system: EmailNotificationSystem):
    """Example: Monitoring email system status."""
    print("\n=== Email System Status ===")
    
    if not email_system:
        print("❌ Email system not available")
        return
    
    try:
        # Get system stats
        stats = email_system.get_queue_stats()
        
        print(f"📊 Email Queue Statistics:")
        print(f"   Queue Size: {stats['queue_size']}")
        print(f"   Sent Emails: {stats['sent_count']}")
        print(f"   Failed Emails: {stats['failed_count']}")
        print(f"   Processing Active: {stats['processing_active']}")
        
        # Calculate success rate
        if stats['sent_count'] + stats['failed_count'] > 0:
            success_rate = (stats['sent_count'] / (stats['sent_count'] + stats['failed_count'])) * 100
            print(f"   Success Rate: {success_rate:.1f}%")
        
        # System health
        if stats['failed_count'] > 10:
            print("⚠️  System Status: DEGRADED (high failure rate)")
        else:
            print("✅ System Status: HEALTHY")
            
    except Exception as e:
        print(f"❌ Error getting system status: {e}")


async def main():
    """Main example function."""
    print("🚀 ARBitech Email Notification System Examples")
    print("=" * 50)
    
    # Example 1: Setup Gmail
    email_system = await example_gmail_setup()
    
    # Example 2: User preferences
    user_prefs = await example_user_preferences()
    
    # Example 3: Send notifications
    await example_send_opportunity_alert(email_system)
    await example_send_trade_update(email_system)
    await example_send_risk_warning(email_system)
    await example_send_profit_report(email_system)
    
    # Example 4: System monitoring
    await example_system_monitoring(email_system)
    
    # Wait a moment for processing
    print("\n⏳ Waiting for email processing...")
    await asyncio.sleep(2)
    
    # Final status check
    await example_system_monitoring(email_system)
    
    print("\n🎉 Examples completed!")
    print("\n📚 Next steps:")
    print("1. Set your Gmail credentials in environment variables")
    print("2. Run: export GMAIL_USERNAME='your-email@gmail.com'")
    print("3. Run: export GMAIL_APP_PASSWORD='your-16-char-password'")
    print("4. Update the user email addresses in the examples")
    print("5. Integrate with your ARBitech trading system")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())