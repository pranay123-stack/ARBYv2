"""
Integration Example: Notification Filtering and Delivery System

This example demonstrates how to use both the notification filtering system
and the multi-channel delivery system together to provide end-to-end
notification processing from detection to delivery.

The integration flow:
1. Configure user preferences for filtering
2. Filter arbitrage opportunities through intelligent filters
3. Use the delivery orchestrator to send filtered notifications
4. Track analytics and performance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from typing import List, Dict, Any

# Import both systems
from notifications import (
    # Filtering system
    NotificationFilterEngine,
    FilterUserPreferences,
    NotificationFilter,
    FilterCondition,
    FilterOperator,
    NotificationPriority,
    NotificationType,
    NotificationChannel,
    create_filter_engine,
    create_profit_threshold_filter,
    create_sport_filter,
    create_bookmaker_filter,
    
    # Delivery system
    MultiChannelDeliveryOrchestrator,
    DeliveryUserPreferences,
    initialize_orchestrator,
    notify_arbitrage_opportunity,
    
    # Models
    Notification,
    MessageData,
    RiskTier,
    Sport
)

# Import mathematical models from detection
from detection.mathematical_models import ArbitrageOpportunity as MathOpportunity, ArbitrageLeg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_user_preferences(filter_engine: NotificationFilterEngine) -> FilterUserPreferences:
    """Set up comprehensive user preferences for filtering."""
    
    # Create user preferences
    user_id = uuid4()
    preferences = filter_engine.create_default_preferences()
    
    # Configure profit thresholds by risk tier
    preferences.profit_thresholds = {
        RiskTier.TIER_A: Decimal('0.03'),  # 3% minimum for tier A
        RiskTier.TIER_B: Decimal('0.06'),  # 6% minimum for tier B
        RiskTier.TIER_C: Decimal('0.10'),  # 10% minimum for tier C
        RiskTier.TIER_D: Decimal('0.15')   # 15% minimum for tier D
    }
    
    # Set sport preferences
    preferences.sport_preferences = {
        Sport.FOOTBALL,
        Sport.BASKETBALL,
        Sport.TENNIS,
        Sport.HOCKEY
    }
    
    # Set bookmaker preferences (whitelist trusted bookmakers)
    preferences.bookmaker_preferences = {
        'bet365',
        'william_hill',
        'ladbrokes',
        'pinnacle',
        'betfair'
    }
    
    # Configure channel settings for delivery
    preferences.channel_settings = {
        NotificationChannel.PUSH: {
            'enabled': True,
            'rate_limit_per_hour': 50,
            'quiet_hours_override': True  # Allow push notifications even during quiet hours
        },
        NotificationChannel.EMAIL: {
            'enabled': True,
            'rate_limit_per_hour': 100,
            'priority_filter': ['high', 'critical']
        },
        NotificationChannel.SMS: {
            'enabled': False,  # Disabled by default
            'rate_limit_per_hour': 10,
            'priority_filter': ['critical']
        }
    }
    
    # Set quiet hours
    preferences.quiet_hours = {
        'weekdays': '22:00-06:00',
        'weekends': '23:00-07:00'
    }
    
    # Add custom filters
    custom_filters = [
        # High-value opportunities filter
        NotificationFilter(
            name="high_value_opportunities",
            conditions=[
                FilterCondition(
                    field="message.data.opportunity.profit_margin",
                    operator=FilterOperator.GREATER_THAN,
                    value=0.12,  # > 12% profit
                    description="High profit margin"
                ),
                FilterCondition(
                    field="message.data.opportunity.risk_tier",
                    operator=FilterOperator.IN,
                    value=['tier_a', 'tier_b'],
                    description="Low to medium risk"
                )
            ],
            logic_operator="AND",
            priority_boost=2.0,
            description="Boost high-value, low-risk opportunities"
        ),
        
        # Football-specific filter
        create_sport_filter([Sport.FOOTBALL]),
        
        # Bookmaker filter for trusted operators
        create_bookmaker_filter(['bet365', 'pinnacle'], include=True)
    ]
    
    preferences.custom_filters = custom_filters
    
    # Set importance weights for relevance scoring
    preferences.importance_weights = {
        'profit_margin': 2.0,
        'risk_tier': 1.5,
        'bookmaker_reliability': 1.0,
        'sport_popularity': 0.8
    }
    
    # Configure escalation rules
    preferences.escalation_rules = {
        'priority_rules': {
            'critical': {
                'channels': ['push', 'sms'],
                'force_delivery': True,
                'retry_attempts': 5
            },
            'high': {
                'channels': ['push', 'email'],
                'retry_attempts': 3
            }
        },
        'frequency_rules': {
            'max_same_opportunity_per_hour': 3,
            'escalate_after_failures': 2
        }
    }
    
    # Set user keywords for relevance scoring
    preferences.keywords = [
        'football', 'basketball', 'tennis',
        'premier league', 'championship',
        'big odds', 'surebet',
        'high profit', 'low risk'
    ]
    
    # Configure notification frequency limits
    preferences.notification_frequency = {
        'opportunity_alert': 30,  # Max 1 per 30 seconds
        'risk_warning': 300,      # Max 1 per 5 minutes
        'system_error': 60        # Max 1 per minute
    }
    
    # Configure deduplication settings
    preferences.dedup_settings = {
        'window_minutes': 5,
        'group_similar': True,
        'aggregate_profits': True
    }
    
    return preferences, user_id


async def create_sample_opportunities() -> List[MathOpportunity]:
    """Create sample arbitrage opportunities for testing."""
    
    opportunities = []
    
    # Sample Opportunity 1: Football match (High value)
    leg1 = ArbitrageLeg(
        bookmaker='bet365',
        odds=Decimal('2.10'),
        stake=Decimal('476.19'),
        event_outcome='Home Win'
    )
    leg2 = ArbitrageLeg(
        bookmaker='william_hill',
        odds=Decimal('1.95'),
        stake=Decimal('512.82'),
        event_outcome='Away Win'
    )
    
    opp1 = MathOpportunity(
        legs=[leg1, leg2],
        sport=Sport.FOOTBALL,
        event_name='Liverpool vs Arsenal',
        profit_margin=Decimal('0.125'),  # 12.5%
        expected_profit=Decimal('125.00'),
        risk_tier=RiskTier.TIER_A
    )
    opportunities.append(opp1)
    
    # Sample Opportunity 2: Basketball game (Medium value)
    leg3 = ArbitrageLeg(
        bookmaker='ladbrokes',
        odds=Decimal('1.85'),
        stake=Decimal('540.54'),
        event_outcome='Over 215.5'
    )
    leg4 = ArbitrageLeg(
        bookmaker='pinnacle',
        odds=Decimal('2.05'),
        stake=Decimal('487.80'),
        event_outcome='Under 215.5'
    )
    
    opp2 = MathOpportunity(
        legs=[leg3, leg4],
        sport=Sport.BASKETBALL,
        event_name='Lakers vs Celtics',
        profit_margin=Decimal('0.075'),  # 7.5%
        expected_profit=Decimal('75.00'),
        risk_tier=RiskTier.TIER_B
    )
    opportunities.append(opp2)
    
    # Sample Opportunity 3: Tennis match (Low value, should be filtered)
    leg5 = ArbitrageLeg(
        bookmaker='betfair',
        odds=Decimal('1.75'),
        stake=Decimal('571.43'),
        event_outcome='Player 1 Wins'
    )
    leg6 = ArbitraryLeg(
        bookmaker='unknown_bookmaker',  # Not in whitelist
        odds=Decimal('2.40'),
        stake=Decimal('416.67'),
        event_outcome='Player 2 Wins'
    )
    
    opp3 = MathOpportunity(
        legs=[leg5, leg6],
        sport=Sport.TENNIS,
        event_name='Djokovic vs Nadal',
        profit_margin=Decimal('0.025'),  # 2.5% - below threshold
        expected_profit=Decimal('25.00'),
        risk_tier=RiskTier.TIER_C
    )
    opportunities.append(opp3)
    
    # Sample Opportunity 4: High risk, high reward (Should be escalated)
    leg7 = ArbitrageLeg(
        bookmaker='bet365',
        odds=Decimal('3.50'),
        stake=Decimal('285.71'),
        event_outcome='Draw'
    )
    leg8 = ArbitrageLeg(
        bookmaker='unreliable_bookmaker',  # Not in whitelist
        odds=Decimal('1.45'),
        stake=Decimal('689.66'),
        event_outcome='No Draw'
    )
    
    opp4 = MathOpportunity(
        legs=[leg7, leg8],
        sport=Sport.FOOTBALL,
        event_name='Manchester United vs Chelsea',
        profit_margin=Decimal('0.18'),  # 18% but high risk
        expected_profit=Decimal('180.00'),
        risk_tier=RiskTier.TIER_D
    )
    opportunities.append(opp4)
    
    return opportunities


async def filter_and_deliver_notifications(
    opportunities: List[MathOpportunity],
    user_id: uuid4,
    filter_engine: NotificationFilterEngine,
    delivery_orchestrator: MultiChannelDeliveryOrchestrator
):
    """Complete pipeline: filter opportunities and deliver notifications."""
    
    logger.info(f"Processing {len(opportunities)} opportunities for user {user_id}")
    
    # Step 1: Convert opportunities to notifications
    from notifications.notification_filters import filter_opportunity_notifications
    notifications = await filter_opportunity_notifications(
        opportunities, user_id, filter_engine
    )
    
    logger.info(f"Generated {len(notifications)} notifications")
    
    # Step 2: Apply additional filtering based on user preferences
    filtered_notifications, metadata = await filter_engine.filter_notifications(
        notifications, user_id
    )
    
    logger.info(f"After filtering: {len(filtered_notifications)} notifications")
    logger.info(f"Filter metadata: {metadata}")
    
    # Step 3: Deliver notifications through orchestrator
    delivery_results = []
    
    for notification in filtered_notifications:
        try:
            # Use delivery orchestrator to send notification
            result = await delivery_orchestrator.send_notification(notification)
            delivery_results.append(result)
            
            logger.info(
                f"Delivered notification: {notification.type.value} "
                f"via {list(notification.channels)} channels"
            )
            
        except Exception as e:
            logger.error(f"Failed to deliver notification: {e}")
    
    return delivery_results


async def demonstrate_analytics(filter_engine: NotificationFilterEngine):
    """Demonstrate analytics and reporting features."""
    
    logger.info("=== Notification Analytics ===")
    
    # Get filter analytics
    filter_analytics = filter_engine.get_filter_analytics()
    
    logger.info(f"Filter Engine Analytics:")
    logger.info(f"  - User preferences loaded: {filter_analytics['user_preferences_loaded']}")
    logger.info(f"  - Total notifications processed: {filter_analytics['analytics']['total_notifications']}")
    logger.info(f"  - Cache size: {filter_analytics['cache_size']}")
    logger.info(f"  - Performance mode: {filter_analytics['performance_mode']}")
    
    # Display priority distribution
    priority_dist = filter_analytics['analytics']['priority_distribution']
    logger.info(f"Priority Distribution:")
    for priority, count in priority_dist.items():
        logger.info(f"  - {priority}: {count}")
    
    # Display type distribution
    type_dist = filter_analytics['analytics']['type_distribution']
    logger.info(f"Type Distribution:")
    for type_name, count in type_dist.items():
        logger.info(f"  - {type_name}: {count}")


async def main():
    """Main demonstration of integrated filtering and delivery system."""
    
    logger.info("Starting Notification Filtering and Delivery Integration Demo")
    
    # Step 1: Initialize systems
    logger.info("Initializing filter engine and delivery orchestrator...")
    
    # Create filter engine (without Supabase for demo)
    filter_engine = create_filter_engine()
    
    # Initialize delivery orchestrator
    delivery_orchestrator = initialize_orchestrator()
    
    # Step 2: Set up user preferences
    logger.info("Setting up user preferences...")
    preferences, user_id = await setup_user_preferences(filter_engine)
    await filter_engine.save_user_preferences(user_id, preferences)
    
    logger.info(f"Created preferences for user {user_id}")
    
    # Step 3: Create sample opportunities
    logger.info("Creating sample arbitrage opportunities...")
    opportunities = await create_sample_opportunities()
    
    logger.info(f"Created {len(opportunities)} opportunities:")
    for i, opp in enumerate(opportunities, 1):
        logger.info(
            f"  {i}. {opp.sport} - {opp.event_name}: "
            f"{opp.profit_margin:.1%} profit ({opp.risk_tier.value})"
        )
    
    # Step 4: Filter and deliver notifications
    logger.info("Filtering opportunities and delivering notifications...")
    delivery_results = await filter_and_deliver_notifications(
        opportunities, user_id, filter_engine, delivery_orchestrator
    )
    
    logger.info(f"Delivery results: {len(delivery_results)} notifications sent")
    
    # Step 5: Demonstrate analytics
    await demonstrate_analytics(filter_engine)
    
    # Step 6: Demonstrate advanced filtering features
    logger.info("=== Advanced Filtering Features Demo ===")
    
    # Test custom rule evaluation
    rule_engine = filter_engine.rule_engine
    
    # Create a test notification for rule evaluation
    test_notification = Notification(
        user_id=user_id,
        type=NotificationType.OPPORTUNITY_ALERT,
        priority=NotificationPriority.HIGH,
        message=MessageData(
            title="Test High-Value Football Opportunity",
            body="Manchester United vs Liverpool - 15% profit margin",
            data={
                'opportunity': {
                    'sport': 'football',
                    'profit_margin': 0.15,
                    'risk_tier': 'tier_a',
                    'bookmakers': ['bet365', 'pinnacle']
                }
            }
        ),
        channels=[NotificationChannel.PUSH, NotificationChannel.EMAIL]
    )
    
    # Evaluate custom rules
    rule_score = rule_engine.evaluate_notification(test_notification)
    logger.info(f"Custom rule evaluation score: {rule_score}")
    
    # Test time-based filtering
    time_filter = filter_engine.time_filter
    is_quiet_time = time_filter.is_quiet_time(preferences)
    logger.info(f"Current time is quiet hours: {is_quiet_time}")
    
    # Test deduplication
    dedup = filter_engine.deduplicator
    
    # Create duplicate notifications
    notification1 = Notification(
        user_id=user_id,
        type=NotificationType.OPPORTUNITY_ALERT,
        priority=NotificationPriority.MEDIUM,
        message=MessageData(
            title="Football Opportunity",
            body="Liverpool vs Arsenal",
            data={
                'opportunity': {
                    'sport': 'football',
                    'profit_margin': 0.085,
                    'risk_tier': 'tier_a',
                    'bookmakers': ['bet365', 'william_hill']
                }
            }
        ),
        channels=[NotificationChannel.PUSH]
    )
    
    notification2 = Notification(
        user_id=user_id,
        type=NotificationType.OPPORTUNITY_ALERT,
        priority=NotificationPriority.MEDIUM,
        message=MessageData(
            title="Football Opportunity",
            body="Liverpool vs Arsenal",
            data={
                'opportunity': {
                    'sport': 'football',
                    'profit_margin': 0.085,
                    'risk_tier': 'tier_a',
                    'bookmakers': ['bet365', 'william_hill']
                }
            }
        ),
        channels=[NotificationChannel.PUSH]
    )
    
    should_dedupe = dedup.should_deduplicate(notification2)
    logger.info(f"Duplicate notification detected: {should_dedupe}")
    
    logger.info("=== Demo Completed Successfully ===")
    
    # Save relevance model
    filter_engine.relevance_scorer.save_model()
    logger.info("Saved relevance scoring model")


# Add missing import
from detection.mathematical_models import ArbitrageLeg as ArbitraryLeg


if __name__ == "__main__":
    # Run the integrated demo
    asyncio.run(main())
