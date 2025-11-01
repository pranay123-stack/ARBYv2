"""
Simple Test Script for Notification Filtering System

This script validates the core functionality of the notification filtering system
without requiring external dependencies like Supabase.
"""

import asyncio
import sys
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

# Import the filtering system
sys.path.append('/workspace')

from notifications import (
    NotificationFilterEngine,
    NotificationFilter,
    FilterCondition,
    FilterOperator,
    FilterUserPreferences,
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationChannel,
    MessageData,
    create_filter_engine,
    create_profit_threshold_filter,
    RiskTier,
    Sport
)


async def test_basic_filtering():
    """Test basic notification filtering functionality."""
    print("\n=== Testing Basic Filtering ===")
    
    # Create filter engine
    filter_engine = create_filter_engine()
    print("✓ Created filter engine")
    
    # Create user preferences
    user_id = uuid4()
    preferences = filter_engine.create_default_preferences()
    
    # Configure profit thresholds
    preferences.profit_thresholds = {
        RiskTier.TIER_A: Decimal('0.05'),
        RiskTier.TIER_B: Decimal('0.08'),
        RiskTier.TIER_C: Decimal('0.12')
    }
    
    # Set sport preferences
    preferences.sport_preferences = {
        Sport.FOOTBALL,
        Sport.BASKETBALL
    }
    
    # Add custom filter
    high_profit_filter = create_profit_threshold_filter(
        threshold=Decimal('0.10'),
        risk_tier=RiskTier.TIER_A
    )
    preferences.custom_filters = [high_profit_filter]
    
    # Save preferences
    await filter_engine.save_user_preferences(user_id, preferences)
    print("✓ Created and saved user preferences")
    
    # Create test notifications
    notifications = [
        # High profit, should pass
        Notification(
            user_id=user_id,
            type=NotificationType.OPPORTUNITY_ALERT,
            priority=NotificationPriority.HIGH,
            message=MessageData(
                title="High Profit Football Opportunity",
                body="15% profit margin",
                data={
                    'opportunity': {
                        'sport': 'football',
                        'profit_margin': 0.15,
                        'risk_tier': 'tier_a',
                        'bookmakers': ['bet365', 'william_hill']
                    }
                }
            ),
            channels=[NotificationChannel.PUSH]
        ),
        
        # Medium profit, should pass
        Notification(
            user_id=user_id,
            type=NotificationType.OPPORTUNITY_ALERT,
            priority=NotificationPriority.MEDIUM,
            message=MessageData(
                title="Basketball Opportunity",
                body="8% profit margin",
                data={
                    'opportunity': {
                        'sport': 'basketball',
                        'profit_margin': 0.08,
                        'risk_tier': 'tier_b',
                        'bookmakers': ['ladbrokes', 'pinnacle']
                    }
                }
            ),
            channels=[NotificationChannel.EMAIL]
        ),
        
        # Low profit, should be filtered out
        Notification(
            user_id=user_id,
            type=NotificationType.OPPORTUNITY_ALERT,
            priority=NotificationPriority.LOW,
            message=MessageData(
                title="Tennis Opportunity",
                body="3% profit margin",
                data={
                    'opportunity': {
                        'sport': 'tennis',  # Not in preferences
                        'profit_margin': 0.03,  # Below threshold
                        'risk_tier': 'tier_c',
                        'bookmakers': ['betfair', 'unreliable']
                    }
                }
            ),
            channels=[NotificationChannel.PUSH]
        )
    ]
    
    print(f"✓ Created {len(notifications)} test notifications")
    
    # Filter notifications
    filtered_notifications, metadata = await filter_engine.filter_notifications(
        notifications, user_id
    )
    
    print(f"✓ Filtered notifications: {len(filtered_notifications)} out of {len(notifications)}")
    print(f"  - Metadata: {metadata}")
    
    # Validate results
    assert len(filtered_notifications) == 2, f"Expected 2 notifications, got {len(filtered_notifications)}"
    print("✓ Basic filtering test passed!")
    
    return True


async def test_custom_rules():
    """Test custom rule engine functionality."""
    print("\n=== Testing Custom Rules ===")
    
    filter_engine = create_filter_engine()
    
    # Create test notification
    notification = Notification(
        user_id=uuid4(),
        type=NotificationType.OPPORTUNITY_ALERT,
        priority=NotificationPriority.HIGH,
        message=MessageData(
            title="Football Opportunity",
            body="Manchester United vs Liverpool",
            data={
                'opportunity': {
                    'sport': 'football',
                    'profit_margin': 0.12,
                    'risk_tier': 'tier_a',
                    'bookmakers': ['bet365', 'pinnacle']
                }
            }
        ),
        channels=[NotificationChannel.PUSH]
    )
    
    # Create custom rules
    rules = [
        NotificationFilter(
            name="high_profit_football",
            conditions=[
                FilterCondition(
                    field="message.data.opportunity.sport",
                    operator=FilterOperator.EQUALS,
                    value="football"
                ),
                FilterCondition(
                    field="message.data.opportunity.profit_margin",
                    operator=FilterOperator.GREATER_THAN,
                    value=0.10
                )
            ],
            logic_operator="AND",
            priority_boost=2.0
        ),
        
        NotificationFilter(
            name="trusted_bookmakers",
            conditions=[
                FilterCondition(
                    field="message.data.opportunity.bookmakers",
                    operator=FilterOperator.CONTAINS,
                    value="bet365"
                )
            ],
            priority_boost=1.0
        )
    ]
    
    # Test rule evaluation
    for rule in rules:
        passed = filter_engine.rule_engine._evaluate_rule(rule, notification)
        print(f"  Rule '{rule.name}': {'PASSED' if passed else 'FAILED'}")
        assert passed, f"Rule {rule.name} should have passed"
    
    # Test combined scoring
    total_score = filter_engine.rule_engine.evaluate_notification(notification)
    print(f"  Total rule score: {total_score}")
    assert total_score > 0, "Should have positive rule score"
    
    print("✓ Custom rules test passed!")
    return True


async def test_deduplication():
    """Test notification deduplication."""
    print("\n=== Testing Deduplication ===")
    
    filter_engine = create_filter_engine()
    dedup = filter_engine.deduplicator
    
    # Create similar notifications
    notification1 = Notification(
        user_id=uuid4(),
        type=NotificationType.OPPORTUNITY_ALERT,
        priority=NotificationPriority.MEDIUM,
        message=MessageData(
            title="Football Opportunity",
            body="Liverpool vs Arsenal",
            data={
                'opportunity': {
                    'sport': 'football',
                    'profit_margin': 0.08,
                    'risk_tier': 'tier_a',
                    'bookmakers': ['bet365', 'william_hill']
                }
            }
        ),
        channels=[NotificationChannel.PUSH]
    )
    
    notification2 = Notification(
        user_id=uuid4(),
        type=NotificationType.OPPORTUNITY_ALERT,
        priority=NotificationPriority.MEDIUM,
        message=MessageData(
            title="Football Opportunity",
            body="Liverpool vs Arsenal",
            data={
                'opportunity': {
                    'sport': 'football',
                    'profit_margin': 0.08,
                    'risk_tier': 'tier_a',
                    'bookmakers': ['bet365', 'william_hill']
                }
            }
        ),
        channels=[NotificationChannel.PUSH]
    )
    
    # Test deduplication
    should_dedupe1 = dedup.should_deduplicate(notification1)
    should_dedupe2 = dedup.should_deduplicate(notification2)
    
    print(f"  First notification should deduplicate: {should_dedupe1}")
    print(f"  Second notification should deduplicate: {should_dedupe2}")
    
    # First notification should not be deduplicated
    assert not should_dedupe1, "First notification should not be deduplicated"
    
    # Second notification should be deduplicated (within time window)
    assert should_dedupe2, "Second notification should be deduplicated"
    
    print("✓ Deduplication test passed!")
    return True


async def test_time_filtering():
    """Test time-based filtering."""
    print("\n=== Testing Time Filtering ===")
    
    filter_engine = create_filter_engine()
    time_filter = filter_engine.time_filter
    
    # Create user with quiet hours
    user_id = uuid4()
    preferences = filter_engine.create_default_preferences()
    preferences.quiet_hours = {
        'weekdays': '22:00-06:00'
    }
    
    await filter_engine.save_user_preferences(user_id, preferences)
    
    # Test notifications during quiet hours
    current_time = datetime(2025, 11, 2, 23, 0, 0)  # 11 PM on a weekday
    is_quiet = time_filter.is_quiet_time(preferences, current_time)
    
    print(f"  11 PM on weekday is quiet hours: {is_quiet}")
    assert is_quiet, "11 PM should be quiet hours"
    
    # Test notifications outside quiet hours
    current_time = datetime(2025, 11, 2, 14, 0, 0)  # 2 PM on a weekday
    is_quiet = time_filter.is_quiet_time(preferences, current_time)
    
    print(f"  2 PM on weekday is quiet hours: {is_quiet}")
    assert not is_quiet, "2 PM should not be quiet hours"
    
    # Test filtering during quiet hours
    notifications = [
        Notification(
            user_id=user_id,
            type=NotificationType.OPPORTUNITY_ALERT,
            priority=NotificationPriority.MEDIUM,
            message=MessageData(
                title="Medium Priority",
                body="Regular notification",
                data={}
            ),
            channels=[NotificationChannel.PUSH]
        ),
        Notification(
            user_id=user_id,
            type=NotificationType.OPPORTUNITY_ALERT,
            priority=NotificationPriority.CRITICAL,
            message=MessageData(
                title="Critical",
                body="Critical notification",
                data={}
            ),
            channels=[NotificationChannel.PUSH]
        )
    ]
    
    filtered = time_filter.filter_by_time(notifications, preferences)
    
    print(f"  Filtered {len(filtered)} out of {len(notifications)} during quiet hours")
    assert len(filtered) == 1, "Only critical notification should pass during quiet hours"
    assert filtered[0].priority == NotificationPriority.CRITICAL
    
    print("✓ Time filtering test passed!")
    return True


async def test_relevance_scoring():
    """Test relevance scoring functionality."""
    print("\n=== Testing Relevance Scoring ===")
    
    filter_engine = create_filter_engine()
    
    # Create user with keywords
    user_id = uuid4()
    preferences = filter_engine.create_default_preferences()
    preferences.keywords = ['football', 'liverpool', 'arsenal', 'high profit']
    await filter_engine.save_user_preferences(user_id, preferences)
    
    # Test notification with matching keywords
    matching_notification = Notification(
        user_id=user_id,
        type=NotificationType.OPPORTUNITY_ALERT,
        priority=NotificationPriority.HIGH,
        message=MessageData(
            title="Liverpool vs Arsenal High Profit Opportunity",
            body="Football match with great profit potential",
            data={}
        ),
        channels=[NotificationChannel.PUSH]
    )
    
    # Test notification without matching keywords
    non_matching_notification = Notification(
        user_id=user_id,
        type=NotificationType.OPPORTUNITY_ALERT,
        priority=NotificationPriority.LOW,
        message=MessageData(
            title="Tennis Match",
            body="Tennis tournament",
            data={}
        ),
        channels=[NotificationChannel.PUSH]
    )
    
    # Calculate relevance scores
    matching_score = filter_engine.relevance_scorer.calculate_score(
        matching_notification, preferences.to_dict()
    )
    non_matching_score = filter_engine.relevance_scorer.calculate_score(
        non_matching_notification, preferences.to_dict()
    )
    
    print(f"  Matching notification score: {matching_score:.3f}")
    print(f"  Non-matching notification score: {non_matching_score:.3f}")
    
    assert matching_score > non_matching_score, "Matching notification should have higher score"
    
    print("✓ Relevance scoring test passed!")
    return True


async def test_filter_utilities():
    """Test filter creation utilities."""
    print("\n=== Testing Filter Utilities ===")
    
    # Test profit threshold filter
    profit_filter = create_profit_threshold_filter(
        threshold=Decimal('0.05'),
        risk_tier=RiskTier.TIER_A
    )
    
    assert profit_filter.name == "profit_threshold_tier_a"
    assert len(profit_filter.conditions) == 2  # Profit margin + risk tier
    print("✓ Profit threshold filter created successfully")
    
    # Test sport filter
    sport_filter = create_sport_filter([Sport.FOOTBALL, Sport.BASKETBALL])
    
    assert sport_filter.name == "sports_filter_2_sports"
    assert len(sport_filter.conditions) == 1
    print("✓ Sport filter created successfully")
    
    # Test bookmaker filter
    bookmaker_filter = create_bookmaker_filter(
        ['bet365', 'william_hill'], 
        include=True
    )
    
    assert len(bookmaker_filter.conditions) == 1
    assert bookmaker_filter.conditions[0].operator == FilterOperator.IN
    print("✓ Bookmaker filter created successfully")
    
    print("✓ Filter utilities test passed!")
    return True


async def test_analytics():
    """Test analytics functionality."""
    print("\n=== Testing Analytics ===")
    
    filter_engine = create_filter_engine()
    analytics = filter_engine.analytics
    
    # Create test notification
    notification = Notification(
        user_id=uuid4(),
        type=NotificationType.OPPORTUNITY_ALERT,
        priority=NotificationPriority.HIGH,
        message=MessageData(
            title="Test Notification",
            body="Test body",
            data={}
        ),
        channels=[NotificationChannel.PUSH]
    )
    
    # Record notification
    analytics.record_notification(notification, 'delivered')
    
    # Get analytics
    metrics = analytics.get_analytics()
    
    assert metrics['total_notifications'] == 1
    assert metrics['delivered_notifications'] == 1
    assert metrics['priority_distribution']['high'] == 1
    assert metrics['type_distribution']['opportunity_alert'] == 1
    
    print(f"  Total notifications: {metrics['total_notifications']}")
    print(f"  Delivered: {metrics['delivered_notifications']}")
    print(f"  Priority distribution: {dict(metrics['priority_distribution'])}")
    
    print("✓ Analytics test passed!")
    return True


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("NOTIFICATION FILTERING SYSTEM - TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Basic Filtering", test_basic_filtering),
        ("Custom Rules", test_custom_rules),
        ("Deduplication", test_deduplication),
        ("Time Filtering", test_time_filtering),
        ("Relevance Scoring", test_relevance_scoring),
        ("Filter Utilities", test_filter_utilities),
        ("Analytics", test_analytics)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nRunning test: {test_name}")
            await test_func()
            passed += 1
            print(f"✅ {test_name} PASSED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
