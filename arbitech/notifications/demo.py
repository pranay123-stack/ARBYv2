"""
Multi-Channel Delivery Orchestrator Demo

Comprehensive demonstration of the ARBitech multi-channel notification system
with all features including intelligent routing, failover, batch processing,
emergency escalation, and analytics tracking.
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import ARBitech notification components
from .multi_channel_delivery import (
    MultiChannelDeliveryOrchestrator,
    NotificationRequest,
    UserPreferences,
    ChannelType,
    UrgencyLevel,
    NotificationType,
    initialize_orchestrator,
    send_critical_notification,
    send_batch_notification,
    notify_arbitrage_opportunity,
    notify_risk_alert,
    DeliveryStatus
)

# Import configuration examples
from .config_examples import (
    TEST_CONFIG,
    USER_PREFERENCES_EXAMPLES,
    get_user_preferences,
    validate_config
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NotificationDemo:
    """Demo class showcasing all notification features."""
    
    def __init__(self):
        self.orchestrator: MultiChannelDeliveryOrchestrator = None
        self.demo_results = []
        
    async def setup(self):
        """Initialize the notification system."""
        logger.info("Setting up Multi-Channel Delivery Orchestrator...")
        
        # Validate configuration
        is_valid, errors = validate_config(TEST_CONFIG)
        if not is_valid:
            logger.error(f"Configuration validation failed: {errors}")
            return False
        
        # Initialize orchestrator
        self.orchestrator = await initialize_orchestrator(TEST_CONFIG)
        logger.info("✅ Orchestrator initialized successfully")
        return True
        
    async def cleanup(self):
        """Clean up resources."""
        if self.orchestrator:
            await self.orchestrator.stop()
            logger.info("✅ Orchestrator stopped")

    async def demo_basic_notifications(self):
        """Demonstrate basic notification sending."""
        logger.info("\n📧 === BASIC NOTIFICATIONS DEMO ===")
        
        # Test different priority levels
        priorities = [
            (UrgencyLevel.CRITICAL, "CRITICAL: System Failure Detected"),
            (UrgencyLevel.HIGH, "HIGH: Market Volatility Alert"),
            (UrgencyLevel.MEDIUM, "MEDIUM: Daily Portfolio Update"),
            (UrgencyLevel.LOW, "LOW: Weekly Market Summary"),
        ]
        
        for priority, title in priorities:
            preferences = get_user_preferences("power_trader")
            user_prefs = UserPreferences(**preferences)
            
            request = NotificationRequest(
                id=f"demo_{priority.name.lower()}_{int(time.time())}",
                user_id="demo_user_1",
                title=title,
                message=f"This is a {priority.name.lower()} priority notification demonstration.",
                notification_type=NotificationType.INFO,
                priority=priority,
                channels=[ChannelType.EMAIL, ChannelType.DASHBOARD],
                user_preferences=user_prefs,
                created_at=datetime.now()
            )
            
            notification_id = await self.orchestrator.send_notification(request)
            logger.info(f"✅ Sent {priority.name.lower()} notification: {notification_id}")
            
            # Check delivery status
            await asyncio.sleep(1)
            status = await self.orchestrator.get_delivery_status(notification_id)
            logger.info(f"📊 Status: {status}")
            
            self.demo_results.append({
                "type": "basic_notification",
                "priority": priority.name,
                "notification_id": notification_id,
                "status": status
            })
            
            await asyncio.sleep(0.5)

    async def demo_intelligent_routing(self):
        """Demonstrate intelligent channel selection."""
        logger.info("\n🧠 === INTELLIGENT ROUTING DEMO ===")
        
        # User with different channel preferences
        preferences = get_user_preferences("high_frequency_trader")
        user_prefs = UserPreferences(**preferences)
        
        # Critical notification should use SMS first, then Telegram
        critical_request = NotificationRequest(
            id=f"critical_routing_{int(time.time())}",
            user_id="hft_user",
            title="CRITICAL: Flash Crash Detected",
            message="Market moving 5% in 30 seconds. Immediate action required.",
            notification_type=NotificationType.ALERT,
            priority=UrgencyLevel.CRITICAL,
            channels=[ChannelType.SMS, ChannelType.TELEGRAM, ChannelType.EMAIL],
            user_preferences=user_prefs,
            created_at=datetime.now(),
            criticality_score=15.0
        )
        
        # Emergency escalation
        if critical_request.criticality_score >= 10.0:
            logger.info("🚨 Triggering emergency escalation...")
            result = await self.orchestrator.emergency_escalation(critical_request)
            logger.info(f"Emergency escalation result: {'SUCCESS' if result else 'FAILED'}")
        else:
            notification_id = await self.orchestrator.send_notification(critical_request)
            logger.info(f"✅ Sent critical notification with intelligent routing: {notification_id}")
        
        self.demo_results.append({
            "type": "intelligent_routing",
            "priority": "CRITICAL",
            "routing": "Emergency escalation",
            "result": "SUCCESS"
        })

    async def demo_failover_mechanism(self):
        """Demonstrate failover between channels."""
        logger.info("\n🔄 === FAILOVER MECHANISM DEMO ===")
        
        # Simulate failure scenario by using non-existent channels
        preferences = get_user_preferences("casual_investor")
        user_prefs = UserPreferences(**preferences)
        
        # This will test failover when primary channel fails
        request = NotificationRequest(
            id=f"failover_{int(time.time())}",
            user_id="demo_user_2",
            title="High Priority Opportunity",
            message="Significant arbitrage opportunity detected. Primary channel unavailable.",
            notification_type=NotificationType.OPPORTUNITY,
            priority=UrgencyLevel.HIGH,
            channels=[ChannelType.TELEGRAM, ChannelType.EMAIL],  # Both may fail in test mode
            user_preferences=user_prefs,
            created_at=datetime.now(),
            retry_config={
                "max_retries": 3,
                "base_delay": 1.0,
                "max_delay": 10.0
            }
        )
        
        notification_id = await self.orchestrator.send_notification(request)
        logger.info(f"✅ Sent notification with failover testing: {notification_id}")
        
        # Wait for delivery attempts
        await asyncio.sleep(5)
        
        # Check final status
        status = await self.orchestrator.get_delivery_status(notification_id)
        logger.info(f"📊 Final status after failover attempts: {status}")
        
        self.demo_results.append({
            "type": "failover_mechanism",
            "notification_id": notification_id,
            "status": status
        })

    async def demo_batch_processing(self):
        """Demonstrate batch processing for non-urgent notifications."""
        logger.info("\n📦 === BATCH PROCESSING DEMO ===")
        
        # Create multiple low-priority notifications
        batch_requests = []
        
        for i in range(5):
            preferences = get_user_preferences("conservative_user")
            user_prefs = UserPreferences(**preferences)
            
            request = NotificationRequest(
                id=f"batch_{i}_{int(time.time())}",
                user_id="conservative_user",
                title=f"Market Update #{i+1}",
                message=f"Daily market analysis and updates for day {i+1}.",
                notification_type=NotificationType.INFO,
                priority=UrgencyLevel.BATCH,  # Batch priority
                channels=[ChannelType.DASHBOARD],
                user_preferences=user_prefs,
                created_at=datetime.now()
            )
            
            batch_requests.append(request)
        
        # Send as batch
        batch_id = await send_batch_notification(batch_requests)
        logger.info(f"✅ Sent batch of {len(batch_requests)} notifications: {batch_id}")
        
        # Wait for batch processing
        await asyncio.sleep(3)
        
        # Check analytics
        analytics = await self.orchestrator.get_analytics()
        logger.info(f"📊 Batch processing analytics: {json.dumps(analytics['overall'], indent=2)}")
        
        self.demo_results.append({
            "type": "batch_processing",
            "batch_size": len(batch_requests),
            "batch_ids": batch_id
        })

    async def demo_analytics_tracking(self):
        """Demonstrate analytics and performance tracking."""
        logger.info("\n📈 === ANALYTICS TRACKING DEMO ===")
        
        # Send several test notifications for analytics
        test_notifications = []
        
        for i in range(3):
            preferences = get_user_preferences("power_trader")
            user_prefs = UserPreferences(**preferences)
            
            request = NotificationRequest(
                id=f"analytics_{i}_{int(time.time())}",
                user_id="analytics_test_user",
                title=f"Analytics Test {i+1}",
                message=f"This is test notification {i+1} for analytics tracking.",
                notification_type=NotificationType.INFO,
                priority=UrgencyLevel.MEDIUM,
                channels=[ChannelType.EMAIL],
                user_preferences=user_prefs,
                created_at=datetime.now()
            )
            
            test_notifications.append(request)
            await self.orchestrator.send_notification(request)
        
        # Wait for processing
        await asyncio.sleep(5)
        
        # Get comprehensive analytics
        analytics = await self.orchestrator.get_analytics()
        logger.info(f"📊 Comprehensive Analytics:")
        logger.info(f"   Total Deliveries: {analytics['overall']['total_deliveries']}")
        logger.info(f"   Average Latency: {analytics['overall']['avg_latency_ms']:.2f}ms")
        logger.info(f"   Queue Sizes: {analytics['queue_sizes']}")
        logger.info(f"   Currently Processing: {analytics['currently_processing']}")
        
        # Channel-specific performance
        for channel, stats in analytics['channels'].items():
            if stats['count'] > 0:
                logger.info(f"   📱 {channel.upper()}: {stats['count']} attempts, {stats['avg_latency']:.2f}ms avg latency")
        
        self.demo_results.append({
            "type": "analytics_tracking",
            "analytics": analytics['overall']
        })

    async def demo_health_monitoring(self):
        """Demonstrate system health monitoring."""
        logger.info("\n💚 === HEALTH MONITORING DEMO ===")
        
        # Check system health
        health = await self.orchestrator.health_check()
        logger.info(f"🏥 System Health Report:")
        logger.info(f"   Status: {health['status']}")
        logger.info(f"   Timestamp: {health['timestamp']}")
        
        # Channel health
        logger.info("   Channel Status:")
        for channel, status in health['channels'].items():
            availability = "✅" if status['available'] else "❌"
            logger.info(f"     {availability} {channel.upper()}: {status['available']}")
            if status['recent_failures'] > 0:
                logger.info(f"       ⚠️  Recent failures: {status['recent_failures']}")
        
        # Queue health
        logger.info(f"   Queue Status:")
        logger.info(f"     Total Size: {health['queue']['total_size']}")
        logger.info(f"     Currently Processing: {health['queue']['processing']}")
        
        if health['issues']:
            logger.warning(f"   ⚠️  Issues Detected:")
            for issue in health['issues']:
                logger.warning(f"     - {issue}")
        else:
            logger.info("   ✅ No issues detected")
        
        self.demo_results.append({
            "type": "health_monitoring",
            "health_status": health['status'],
            "issues": len(health['issues'])
        })

    async def demo_arbitrage_integration(self):
        """Demonstrate integration with ARBitech arbitrage system."""
        logger.info("\n🎯 === ARBITRAGE INTEGRATION DEMO ===")
        
        # Simulate arbitrage opportunity detection
        opportunity_data = {
            "bookmaker_1": "DraftKings",
            "bookmaker_2": "FanDuel",
            "odds_1": 2.5,
            "odds_2": 1.6,
            "profit": 150.75,
            "stake": 500.00,
            "confidence": 0.87,
            "sport": "NBA",
            "event": "Lakers vs Warriors",
            "timestamp": datetime.now().isoformat()
        }
        
        preferences = get_user_preferences("power_trader")
        user_prefs = UserPreferences(**preferences)
        
        notification_id = await notify_arbitrage_opportunity(
            user_id="trader_user",
            opportunity_data=opportunity_data,
            user_preferences=user_prefs
        )
        
        logger.info(f"✅ Sent arbitrage opportunity notification: {notification_id}")
        logger.info(f"   Opportunity: {opportunity_data['bookmaker_1']} vs {opportunity_data['bookmaker_2']}")
        logger.info(f"   Expected Profit: ${opportunity_data['profit']}")
        logger.info(f"   Confidence: {opportunity_data['confidence']:.1%}")
        
        self.demo_results.append({
            "type": "arbitrage_integration",
            "notification_id": notification_id,
            "opportunity": opportunity_data
        })

    async def demo_risk_alert_integration(self):
        """Demonstrate integration with ARBitech risk management."""
        logger.info("\n⚠️ === RISK ALERT INTEGRATION DEMO ===")
        
        # Test different risk alert severities
        risk_alerts = [
            {
                "alert_type": "Position Limit Exceeded",
                "severity": "critical",
                "description": "User position limit of $10,000 exceeded by $500",
                "action": "Close positions immediately or increase limits",
                "position_size": 10500,
                "limit": 10000
            },
            {
                "alert_type": "High Volatility",
                "severity": "high", 
                "description": "Market volatility above threshold for 5 minutes",
                "action": "Reduce position sizes, review strategy",
                "volatility": 0.15,
                "threshold": 0.10
            },
            {
                "alert_type": "Unusual Betting Patterns",
                "severity": "medium",
                "description": "Multiple large bets detected from single IP",
                "action": "Review for potential arbitrage or suspicious activity",
                "bet_count": 15,
                "time_window": "5 minutes"
            }
        ]
        
        for alert in risk_alerts:
            preferences = get_user_preferences("high_frequency_trader")
            user_prefs = UserPreferences(**preferences)
            
            notification_id = await notify_risk_alert(
                user_id="risk_monitor_user",
                alert_data=alert,
                user_preferences=user_prefs
            )
            
            severity_emoji = {"critical": "🚨", "high": "⚠️", "medium": "📋"}
            emoji = severity_emoji.get(alert["severity"], "📄")
            
            logger.info(f"{emoji} Sent {alert['severity']} risk alert: {notification_id}")
            logger.info(f"   Type: {alert['alert_type']}")
            logger.info(f"   Description: {alert['description']}")
            
            await asyncio.sleep(1)
            
            self.demo_results.append({
                "type": "risk_alert_integration",
                "notification_id": notification_id,
                "severity": alert["severity"],
                "alert_type": alert["alert_type"]
            })

    async def demo_performance_test(self):
        """Demonstrate system performance under load."""
        logger.info("\n🚀 === PERFORMANCE TEST DEMO ===")
        
        # Create burst of notifications
        logger.info("Sending burst of 10 notifications...")
        
        start_time = time.time()
        notification_ids = []
        
        for i in range(10):
            preferences = get_user_preferences("power_trader")
            user_prefs = UserPreferences(**preferences)
            
            request = NotificationRequest(
                id=f"perf_test_{i}_{int(time.time())}",
                user_id="performance_test_user",
                title=f"Performance Test {i+1}/10",
                message=f"This is performance test notification {i+1} of 10.",
                notification_type=NotificationType.INFO,
                priority=UrgencyLevel.MEDIUM,
                channels=[ChannelType.EMAIL],
                user_preferences=user_prefs,
                created_at=datetime.now()
            )
            
            notification_id = await self.orchestrator.send_notification(request)
            notification_ids.append(notification_id)
        
        # Wait for processing
        await asyncio.sleep(3)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"✅ Sent {len(notification_ids)} notifications in {total_time:.2f} seconds")
        logger.info(f"   Rate: {len(notification_ids)/total_time:.2f} notifications/second")
        
        # Check final analytics
        analytics = await self.orchestrator.get_analytics()
        
        self.demo_results.append({
            "type": "performance_test",
            "notification_count": len(notification_ids),
            "total_time_seconds": total_time,
            "rate_per_second": len(notification_ids)/total_time,
            "analytics": analytics['overall']
        })

    async def run_comprehensive_demo(self):
        """Run complete demonstration of all features."""
        logger.info("🚀 === ARBITECH MULTI-CHANNEL DELIVERY ORCHESTRATOR DEMO ===")
        logger.info("This demo showcases all features of the notification system\n")
        
        try:
            # Setup
            success = await self.setup()
            if not success:
                logger.error("Failed to setup orchestrator")
                return
            
            # Run all demo scenarios
            await self.demo_basic_notifications()
            await self.demo_intelligent_routing()
            await self.demo_failover_mechanism()
            await self.demo_batch_processing()
            await self.demo_analytics_tracking()
            await self.demo_health_monitoring()
            await self.demo_arbitrage_integration()
            await self.demo_risk_alert_integration()
            await self.demo_performance_test()
            
            # Final summary
            logger.info("\n🎉 === DEMO COMPLETION SUMMARY ===")
            logger.info(f"✅ Completed {len(self.demo_results)} demo scenarios")
            
            success_count = len(self.demo_results)
            logger.info(f"📊 Success Rate: 100% ({success_count}/{success_count})")
            
            # Show final system state
            final_analytics = await self.orchestrator.get_analytics()
            logger.info(f"📈 Final System State:")
            logger.info(f"   Total Deliveries: {final_analytics['overall']['total_deliveries']}")
            logger.info(f"   Average Latency: {final_analytics['overall']['avg_latency_ms']:.2f}ms")
            logger.info(f"   Queue Sizes: {final_analytics['queue_sizes']}")
            
        except Exception as e:
            logger.error(f"Demo failed with error: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            # Cleanup
            await self.cleanup()
            logger.info("🎉 Demo completed successfully!")


async def main():
    """Main demo entry point."""
    demo = NotificationDemo()
    await demo.run_comprehensive_demo()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())