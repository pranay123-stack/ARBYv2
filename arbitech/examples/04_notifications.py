#!/usr/bin/env python3
"""
ARBITech Example 4: Notifications System

This example demonstrates:
1. How to set up multi-channel notification systems
2. How to configure email notifications for opportunities
3. How to implement Telegram bot alerts
4. How to create dashboard notifications
5. How to filter and prioritize notifications

Stay informed about your arbitrage opportunities and trades!
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from examples_util import ArbitrageOpportunity, BettingLeg, Sport, RiskTier, Trade

# Mock notification classes for demonstration
class NotificationChannel:
    """Base class for notification channels"""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.delivery_stats = {"sent": 0, "failed": 0}
    
    async def send(self, **kwargs) -> Dict[str, Any]:
        """Send notification - to be implemented by subclasses"""
        raise NotImplementedError
    
    def get_status(self) -> Dict[str, Any]:
        """Get channel status and statistics"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "stats": self.delivery_stats.copy()
        }


class EmailNotifier(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587):
        super().__init__("Email")
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.credentials = {}
    
    def configure(self, username: str, password: str, from_email: str):
        """Configure email credentials"""
        self.credentials = {
            "username": username,
            "password": password,
            "from_email": from_email
        }
        print(f"📧 Email configured for {username}")
    
    async def send_opportunity_alert(self, recipient: str, opportunity: ArbitrageOpportunity):
        """Send opportunity alert via email"""
        print(f"📧 Sending opportunity alert to {recipient}...")
        await asyncio.sleep(0.5)
        
        # Simulate email sending
        self.delivery_stats["sent"] += 1
        print("✅ Email sent successfully")
        
        return {
            "channel": "email",
            "recipient": recipient,
            "type": "opportunity_alert",
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }
    
    async def send_trade_update(self, recipient: str, trade: Trade, status: str):
        """Send trade status update via email"""
        print(f"📧 Sending trade update to {recipient}...")
        await asyncio.sleep(0.3)
        
        self.delivery_stats["sent"] += 1
        print("✅ Trade update email sent")
        
        return {
            "channel": "email",
            "recipient": recipient,
            "type": "trade_update",
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }
    
    async def send(self, **kwargs) -> Dict[str, Any]:
        """Generic send method"""
        notification_type = kwargs.get("type", "generic")
        
        if notification_type == "opportunity":
            return await self.send_opportunity_alert(
                kwargs["recipient"], kwargs["opportunity"]
            )
        elif notification_type == "trade":
            return await self.send_trade_update(
                kwargs["recipient"], kwargs["trade"], kwargs.get("status", "unknown")
            )
        else:
            print("📧 Sending generic notification...")
            self.delivery_stats["sent"] += 1
            return {"status": "sent"}


class TelegramBot(NotificationChannel):
    """Telegram bot notification channel"""
    
    def __init__(self):
        super().__init__("Telegram")
        self.bot_token = None
        self.chat_ids = []
    
    def configure(self, bot_token: str):
        """Configure bot token"""
        self.bot_token = bot_token
        print(f"🤖 Telegram bot configured")
    
    def add_chat(self, chat_id: str):
        """Add chat to notification list"""
        self.chat_ids.append(chat_id)
        print(f"📱 Added chat {chat_id} to notifications")
    
    async def send_opportunity_alert(self, chat_id: str, opportunity: ArbitrageOpportunity):
        """Send opportunity alert via Telegram"""
        message = f"""
🎯 New Arbitrage Opportunity!

📊 Details:
• Event: {opportunity.event}
• Profit: {opportunity.profit_margin:.2%}
• Stake: ${opportunity.required_stake:.2f}
• Return: ${opportunity.expected_return:.2f}
• Risk: {opportunity.risk_tier}

🚀 Action: Execute now!
        """
        
        print(f"🤖 Sending Telegram alert to {chat_id}...")
        await asyncio.sleep(0.4)
        
        self.delivery_stats["sent"] += 1
        print("✅ Telegram message sent")
        
        return {
            "channel": "telegram",
            "chat_id": chat_id,
            "type": "opportunity_alert",
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }
    
    async def send_trade_alert(self, chat_id: str, trade: Trade):
        """Send trade alert via Telegram"""
        status_emoji = {
            "pending": "⏳",
            "filled": "✅",
            "failed": "❌",
            "settled": "💰"
        }
        
        emoji = status_emoji.get(trade.status.value, "📊")
        
        message = f"""
{emoji} Trade Update: {trade.id}

📈 Status: {trade.status.value.upper()}
💰 Stake: ${trade.total_stake:.2f}
📊 Expected: ${trade.expected_return:.2f}
💵 P&L: ${trade.profit_loss:.2f}

Event: {trade.opportunity.event}
        """
        
        print(f"🤖 Sending trade alert to {chat_id}...")
        await asyncio.sleep(0.3)
        
        self.delivery_stats["sent"] += 1
        print("✅ Trade alert sent")
        
        return {
            "channel": "telegram",
            "chat_id": chat_id,
            "type": "trade_alert",
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }
    
    async def send(self, **kwargs) -> Dict[str, Any]:
        """Generic send method"""
        notification_type = kwargs.get("type", "generic")
        
        if notification_type == "opportunity":
            return await self.send_opportunity_alert(
                kwargs["chat_id"], kwargs["opportunity"]
            )
        elif notification_type == "trade":
            return await self.send_trade_alert(
                kwargs["chat_id"], kwargs["trade"]
            )
        else:
            print("🤖 Sending generic Telegram message...")
            self.delivery_stats["sent"] += 1
            return {"status": "sent"}


class DashboardNotifier(NotificationChannel):
    """Dashboard notification channel"""
    
    def __init__(self):
        super().__init__("Dashboard")
        self.notifications = []
        self.websocket_connections = []
    
    async def send_opportunity_alert(self, opportunity: ArbitrageOpportunity):
        """Send opportunity alert to dashboard"""
        alert = {
            "type": "opportunity",
            "priority": "high" if opportunity.profit_margin > 0.03 else "medium",
            "title": f"New Opportunity: {opportunity.event}",
            "message": f"Profit: {opportunity.profit_margin:.2%} | Stake: ${opportunity.required_stake:.2f}",
            "timestamp": datetime.now().isoformat(),
            "data": opportunity.__dict__
        }
        
        self.notifications.append(alert)
        print(f"📊 Dashboard notification added")
        
        # Broadcast to connected websockets
        for connection in self.websocket_connections:
            await self._broadcast_to_websocket(connection, alert)
        
        return {
            "channel": "dashboard",
            "type": "opportunity_alert",
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }
    
    async def send_trade_update(self, trade: Trade):
        """Send trade update to dashboard"""
        alert = {
            "type": "trade",
            "priority": "high" if trade.status.value in ["failed", "settled"] else "medium",
            "title": f"Trade {trade.id} - {trade.status.value.upper()}",
            "message": f"P&L: ${trade.profit_loss:.2f} | Stake: ${trade.total_stake:.2f}",
            "timestamp": datetime.now().isoformat(),
            "data": trade.__dict__
        }
        
        self.notifications.append(alert)
        print(f"📊 Trade update added to dashboard")
        
        # Broadcast to websockets
        for connection in self.websocket_connections:
            await self._broadcast_to_websocket(connection, alert)
        
        return {
            "channel": "dashboard",
            "type": "trade_update",
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _broadcast_to_websocket(self, connection, data):
        """Broadcast data to websocket connection"""
        print(f"📡 Broadcasting to websocket {connection}")
        await asyncio.sleep(0.1)
    
    def add_websocket_connection(self, connection_id: str):
        """Add websocket connection for real-time updates"""
        self.websocket_connections.append(connection_id)
        print(f"🔗 Websocket {connection_id} connected")
    
    def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notification history"""
        return self.notifications[-limit:]
    
    async def send(self, **kwargs) -> Dict[str, Any]:
        """Generic send method"""
        notification_type = kwargs.get("type", "generic")
        
        if notification_type == "opportunity":
            return await self.send_opportunity_alert(kwargs["opportunity"])
        elif notification_type == "trade":
            return await self.send_trade_update(kwargs["trade"])
        else:
            print("📊 Sending generic dashboard notification...")
            return {"status": "sent"}


class NotificationFilters:
    """Filters for notification content and recipients"""
    
    def __init__(self):
        self.rules = []
    
    def add_profit_filter(self, min_profit: float, channels: List[str]):
        """Only notify for opportunities with minimum profit"""
        self.rules.append({
            "type": "profit_filter",
            "min_profit": min_profit,
            "channels": channels
        })
    
    def add_risk_filter(self, max_risk: str, channels: List[str]):
        """Only notify for opportunities up to certain risk tier"""
        self.rules.append({
            "type": "risk_filter",
            "max_risk": max_risk,
            "channels": channels
        })
    
    def add_stake_filter(self, max_stake: float, channels: List[str]):
        """Only notify for opportunities below maximum stake"""
        self.rules.append({
            "type": "stake_filter",
            "max_stake": max_stake,
            "channels": channels
        })
    
    def should_notify(self, opportunity: ArbitrageOpportunity, channel: str) -> bool:
        """Check if notification should be sent based on filters"""
        for rule in self.rules:
            if channel not in rule.get("channels", []):
                continue
            
            if rule["type"] == "profit_filter":
                if opportunity.profit_margin < rule["min_profit"]:
                    return False
            
            elif rule["type"] == "risk_filter":
                risk_tiers = {"TIER_A": 1, "TIER_B": 2, "TIER_C": 3}
                if risk_tiers.get(opportunity.risk_tier, 3) > risk_tiers.get(rule["max_risk"], 3):
                    return False
            
            elif rule["type"] == "stake_filter":
                if opportunity.required_stake > rule["max_stake"]:
                    return False
        
        return True


class NotificationManager:
    """Central notification manager"""
    
    def __init__(self):
        self.channels = {}
        self.filters = NotificationFilters()
        self.delivery_stats = {"total_sent": 0, "total_failed": 0}
    
    def add_channel(self, channel: NotificationChannel):
        """Add notification channel"""
        self.channels[channel.name.lower()] = channel
        print(f"📢 Added {channel.name} channel")
    
    async def send_opportunity_alert(self, opportunity: ArbitrageOpportunity, 
                                   recipients: Dict[str, Any]):
        """Send opportunity alert to configured channels"""
        
        print(f"\n🔔 Sending opportunity alerts...")
        print(f"   Event: {opportunity.event}")
        print(f"   Profit: {opportunity.profit_margin:.2%}")
        print()
        
        results = []
        
        # Email notifications
        if "email" in recipients and "email" in self.channels:
            email_channel = self.channels["email"]
            if self.filters.should_notify(opportunity, "email"):
                result = await email_channel.send_opportunity_alert(
                    recipients["email"], opportunity
                )
                results.append(result)
        
        # Telegram notifications
        if "telegram" in recipients and "telegram" in self.channels:
            telegram_channel = self.channels["telegram"]
            if self.filters.should_notify(opportunity, "telegram"):
                result = await telegram_channel.send_opportunity_alert(
                    recipients["telegram"], opportunity
                )
                results.append(result)
        
        # Dashboard notifications (always)
        if "dashboard" in self.channels:
            dashboard_channel = self.channels["dashboard"]
            result = await dashboard_channel.send_opportunity_alert(opportunity)
            results.append(result)
        
        # Update statistics
        for result in results:
            if result["status"] == "sent":
                self.delivery_stats["total_sent"] += 1
            else:
                self.delivery_stats["total_failed"] += 1
        
        return results
    
    async def send_trade_update(self, trade: Trade, recipients: Dict[str, Any]):
        """Send trade update notification"""
        
        print(f"\n🔔 Sending trade update...")
        print(f"   Trade: {trade.id}")
        print(f"   Status: {trade.status.value}")
        print(f"   P&L: ${trade.profit_loss:.2f}")
        print()
        
        results = []
        
        # Email notifications
        if "email" in recipients and "email" in self.channels:
            email_channel = self.channels["email"]
            result = await email_channel.send_trade_update(
                recipients["email"], trade, trade.status.value
            )
            results.append(result)
        
        # Telegram notifications
        if "telegram" in recipients and "telegram" in self.channels:
            telegram_channel = self.channels["telegram"]
            result = await telegram_channel.send_trade_alert(
                recipients["telegram"], trade
            )
            results.append(result)
        
        # Dashboard notifications
        if "dashboard" in self.channels:
            dashboard_channel = self.channels["dashboard"]
            result = await dashboard_channel.send_trade_update(trade)
            results.append(result)
        
        return results
    
    def configure_filters(self, config: Dict[str, Any]):
        """Configure notification filters"""
        
        if "min_profit" in config:
            self.filters.add_profit_filter(
                config["min_profit"], 
                config.get("profit_channels", ["email", "telegram"])
            )
        
        if "max_risk" in config:
            self.filters.add_risk_filter(
                config["max_risk"],
                config.get("risk_channels", ["email"])
            )
        
        if "max_stake" in config:
            self.filters.add_stake_filter(
                config["max_stake"],
                config.get("stake_channels", ["telegram"])
            )
        
        print("🔍 Notification filters configured")
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get delivery statistics"""
        return {
            "total_sent": self.delivery_stats["total_sent"],
            "total_failed": self.delivery_stats["total_failed"],
            "channels": {name: channel.get_status() for name, channel in self.channels.items()}
        }


async def demonstrate_notifications():
    """Demonstrate notification system"""
    
    print("=" * 70)
    print("🔔 NOTIFICATION SYSTEM DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Initialize notification manager
    manager = NotificationManager()
    
    # Add channels
    email = EmailNotifier()
    telegram = TelegramBot()
    dashboard = DashboardNotifier()
    
    manager.add_channel(email)
    manager.add_channel(telegram)
    manager.add_channel(dashboard)
    
    # Configure channels
    email.configure("your_email@gmail.com", "app_password", "your_email@gmail.com")
    telegram.configure("your_bot_token")
    telegram.add_chat("123456789")
    dashboard.add_websocket_connection("dashboard_1")
    
    print()
    
    # Configure filters
    manager.configure_filters({
        "min_profit": 0.02,  # 2% minimum
        "max_risk": "TIER_B",  # Only TIER_A and TIER_B
        "max_stake": 500.0,   # Maximum $500 stake
        "profit_channels": ["email", "telegram"],
        "risk_channels": ["email"],
        "stake_channels": ["telegram"]
    })
    
    print()
    
    # Create sample opportunity
    opportunity = ArbitrageOpportunity(
        sport=Sport.FOOTBALL.value,
        event="Arsenal vs Chelsea",
        profit_margin=0.028,
        risk_tier=RiskTier.TIER_A.value,
        required_stake=200.00,
        expected_return=205.60,
        legs=[
            BettingLeg("bet365", "Arsenal", 2.08, 98.08),
            BettingLeg("william_hill", "Chelsea", 1.98, 101.92)
        ]
    )
    
    # Send opportunity alert
    recipients = {
        "email": "trader@email.com",
        "telegram": "123456789"
    }
    
    await manager.send_opportunity_alert(opportunity, recipients)
    
    # Create sample trade
    from examples_util import TradeStatus
    trade = Trade(
        id="TRADE_001",
        opportunity=opportunity,
        status=TradeStatus.FILLED,
        total_stake=200.00,
        expected_return=205.60,
        actual_return=204.80,
        profit_loss=4.80
    )
    
    # Send trade update
    await manager.send_trade_update(trade, recipients)
    
    # Show statistics
    print("\n📊 DELIVERY STATISTICS")
    print("-" * 25)
    stats = manager.get_delivery_stats()
    print(f"Total Sent: {stats['total_sent']}")
    print(f"Total Failed: {stats['total_failed']}")
    print(f"Success Rate: {(stats['total_sent'] / (stats['total_sent'] + stats['total_failed'])) * 100:.1f}%")
    
    print("\nChannel Status:")
    for name, status in stats["channels"].items():
        print(f"  {name}: {status['stats']['sent']} sent, {status['stats']['failed']} failed")
    
    return manager


async def main():
    """Main demonstration function"""
    
    print("=" * 70)
    print("📱 ARBITECH EXAMPLE 4: NOTIFICATIONS SYSTEM")
    print("=" * 70)
    print()
    
    # Step 1: Introduction
    print("📚 LEARNING OBJECTIVES:")
    print("  • Understand multi-channel notification systems")
    print("  • Learn to configure email and Telegram notifications")
    print("  • Practice implementing notification filters")
    print("  • Understand real-time dashboard updates")
    print("  • Learn notification prioritization and delivery")
    print()
    
    # Step 2: Notification Channels
    print("1️⃣ NOTIFICATION CHANNELS")
    print("-" * 25)
    
    print("Supported channels:")
    print("  📧 Email - Detailed alerts with full information")
    print("  📱 Telegram - Quick mobile-friendly notifications")
    print("  📊 Dashboard - Real-time web interface updates")
    print("  📞 SMS - Critical alerts via text message (coming soon)")
    print()
    
    print("Channel features:")
    print("  • Delivery confirmation")
    print("  • Retry logic for failed deliveries")
    print("  • Rate limiting to avoid spam")
    print("  • Rich formatting with emojis and structure")
    print()
    
    # Step 3: Configuration
    print("2️⃣ CHANNEL CONFIGURATION")
    print("-" * 25)
    
    print("Email setup:")
    print("  • SMTP server configuration")
    print("  • Authentication with app passwords")
    print("  • From/Reply-to address")
    print("  • HTML and plain text support")
    print()
    
    print("Telegram setup:")
    print("  • Bot token from BotFather")
    print("  • Chat ID configuration")
    print("  • Rich message formatting")
    print("  • Inline keyboards for quick actions")
    print()
    
    print("Dashboard setup:")
    print("  • Websocket connections for real-time updates")
    print("  • Notification history")
    print("  • Interactive notifications")
    print("  • Mobile-responsive design")
    print()
    
    # Step 4: Filters
    print("3️⃣ NOTIFICATION FILTERS")
    print("-" * 25)
    
    print("Available filters:")
    print("  💰 Minimum profit filter - Only high-value opportunities")
    print("  🎯 Risk tier filter - Limit by safety level")
    print("  💸 Stake size filter - Control maximum exposure")
    print("  ⏰ Time-based filters - Avoid off-hours notifications")
    print("  📍 Bookmaker filter - Filter by specific bookmakers")
    print()
    
    print("Filter benefits:")
    print("  • Reduce notification noise")
    print("  • Focus on relevant opportunities")
    print("  • Customize per channel")
    print("  • Improve signal-to-noise ratio")
    print()
    
    # Step 5: Demonstration
    print("4️⃣ NOTIFICATION DEMONSTRATION")
    print("-" * 35)
    
    await demonstrate_notifications()
    
    print()
    
    # Step 6: Notification Types
    print("5️⃣ NOTIFICATION TYPES")
    print("-" * 25)
    
    print("Opportunity alerts:")
    print("  • New arbitrage opportunities")
    print("  • High-profit opportunities")
    print("  • Time-sensitive opportunities")
    print("  • Bookmaker-specific alerts")
    print()
    
    print("Trade updates:")
    print("  • Trade execution status")
    print("  • Profit/loss notifications")
    print("  • Error and failure alerts")
    print("  • Settlement confirmations")
    print()
    
    print("System notifications:")
    print("  • Risk alerts and circuit breakers")
    print("  • System health monitoring")
    print("  • Maintenance notifications")
    print("  • Performance summaries")
    print()
    
    # Step 7: Best Practices
    print("6️⃣ NOTIFICATION BEST PRACTICES")
    print("-" * 40)
    
    print("✅ DO:")
    print("  • Use appropriate channels for different alert types")
    print("  • Set up filters to reduce noise")
    print("  • Test notification delivery regularly")
    print("  • Use rich formatting for better readability")
    print("  • Include actionable information")
    print("  • Monitor delivery statistics")
    print()
    
    print("❌ DON'T:")
    print("  • Over-notify (will be ignored)")
    print("  • Use the same channel for all notifications")
    print("  • Send sensitive information without encryption")
    print("  • Ignore failed delivery notifications")
    print("  • Set minimum profit too high (miss opportunities)")
    print("  • Forget to test emergency notifications")
    print()
    
    # Step 8: Security
    print("7️⃣ SECURITY CONSIDERATIONS")
    print("-" * 30)
    
    print("🔒 Security best practices:")
    print("  • Use app passwords, not main account passwords")
    print("  • Enable 2FA on notification accounts")
    print("  • Store credentials securely (environment variables)")
    print("  • Limit notification access to necessary channels")
    print("  • Monitor for unauthorized access")
    print("  • Use VPN for additional privacy")
    print()
    
    # Step 9: Integration
    print("8️⃣ INTEGRATION WITH OTHER SYSTEMS")
    print("-" * 40)
    
    print("Notification integration:")
    print("  • Risk management system alerts")
    print("  • Browser automation status updates")
    print("  • Performance monitoring notifications")
    print("  • Error tracking and alerting")
    print("  • Audit trail notifications")
    print("  • Compliance reporting alerts")
    print()
    
    # Step 10: Next Steps
    print("9️⃣ NEXT STEPS")
    print("-" * 15)
    print("✅ Congratulations! You've completed the notifications tutorial.")
    print()
    print("What you've learned:")
    print("  ✓ Multi-channel notification setup")
    print("  ✓ Email and Telegram configuration")
    print("  ✓ Notification filtering and prioritization")
    print("  ✓ Real-time dashboard updates")
    print("  ✓ Security considerations")
    print("  ✓ Integration with other systems")
    print()
    print("Recommended next steps:")
    print("  1. Run Example 5: HITL Workflow")
    print("  2. Configure your notification channels")
    print("  3. Set up filtering rules")
    print("  4. Test delivery mechanisms")
    print("  5. Integrate with your trading workflow")
    print()
    print("To continue, run:")
    print("  python examples/05_hitl_workflow.py")
    print()
    print("=" * 70)
    print("Example 4 completed! 🎉")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Tutorial cancelled by user. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("Please check the error message and try again.")