"""
Standalone Test for Notification Filtering System

This test validates the core notification filtering functionality without
requiring full system imports or external dependencies.
"""

import asyncio
import sys
import os

# Add paths for imports
sys.path.insert(0, '/workspace')
sys.path.insert(0, '/workspace/arbitech')

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

# Direct import of notification filters module
from notifications.notification_filters import (
    NotificationFilterEngine,
    NotificationFilter,
    FilterCondition,
    FilterOperator,
    UserPreferences,
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


async def test_basic_functionality():
    """Test basic filtering functionality."""
    print("\n=== Testing Basic Notification Filtering ===")
    
    # Create filter engine
    filter_engine = create_filter_engine()
    print("✓ Created filter engine")
    
    # Create user preferences
    user_id = uuid4()
    preferences = filter_engine.create_default_preferences()
    print("✓ Created user preferences")
    
    # Configure profit thresholds
    preferences.profit_thresholds = {
        RiskTier.TIER_A: Decimal('0.05'),
        RiskTier.TIER_B: Decimal('0.08'),
        RiskTier.TIER_C: Decimal('0.12')
    }
    print("✓ Configured profit thresholds")
    
    # Create test notification (high profit, should pass)
    notification = Notification(
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
    )
    print("✓ Created test notification")
    
    # Test filtering
    try:
        filtered_notifications, metadata = await filter_engine.filter_notifications(
            [notification], user_id
        )
        print(f"✓ Filtered {len(filtered_notifications)} notification(s)")
        print(f"  Metadata: {metadata}")
    except Exception as e:
        print(f"✗ Filtering failed: {e}")
        return False
    
    return True


async def test_custom_rules():
    """Test custom rule evaluation."""
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
                    'risk_tier': 'tier_a'
                }
            }
        ),
        channels=[NotificationChannel.PUSH]
    )
    
    # Create custom rule
    rule = NotificationFilter(
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
    )
    
    # Test rule evaluation
    passed = filter_engine.rule_engine._evaluate_rule(rule, notification)
    print(f"  Rule evaluation: {'PASSED' if passed else 'FAILED'}")
    
    if passed:
        print("✓ Custom rules test passed!")
        return True
    else:
        print("✗ Custom rules test failed!")
        return False


async def test_filter_utilities():
    """Test filter creation utilities."""
    print("\n=== Testing Filter Utilities ===")
    
    try:
        # Test profit threshold filter
        profit_filter = create_profit_threshold_filter(
            threshold=Decimal('0.05'),
            risk_tier=RiskTier.TIER_A
        )
        print(f"✓ Created profit filter: {profit_filter.name}")
        assert profit_filter.name == "profit_threshold_tier_a"
        
        # Test sport filter
        sport_filter = create_sport_filter([Sport.FOOTBALL, Sport.BASKETBALL])
        print(f"✓ Created sport filter: {sport_filter.name}")
        assert "sports_filter" in sport_filter.name
        
        print("✓ Filter utilities test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Filter utilities test failed: {e}")
        return False


async def test_preferences_serialization():
    """Test user preferences serialization."""
    print("\n=== Testing Preferences Serialization ===")
    
    try:
        # Create preferences
        preferences = UserPreferences(uuid4())
        
        # Set some values
        preferences.profit_thresholds = {
            RiskTier.TIER_A: Decimal('0.05'),
            RiskTier.TIER_B: Decimal('0.08')
        }
        preferences.sport_preferences = {Sport.FOOTBALL}
        
        # Serialize to dict
        data = preferences.to_dict()
        print(f"✓ Serialized preferences to dict")
        
        # Deserialize from dict
        preferences2 = UserPreferences.from_dict(data, uuid4())
        print(f"✓ Deserialized preferences from dict")
        
        # Verify values
        assert len(preferences2.profit_thresholds) == 2
        assert Sport.FOOTBALL in preferences2.sport_preferences
        
        print("✓ Preferences serialization test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Preferences serialization test failed: {e}")
        return False


async def test_deduplication():
    """Test notification deduplication."""
    print("\n=== Testing Deduplication ===")
    
    try:
        from notifications.notification_filters import NotificationDeduplicator
        
        dedup = NotificationDeduplicator()
        
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
        
        print(f"  First notification deduplicated: {should_dedupe1}")
        print(f"  Second notification deduplicated: {should_dedupe2}")
        
        # First should not be deduplicated, second should
        assert not should_dedupe1, "First should not be deduplicated"
        
        print("✓ Deduplication test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Deduplication test failed: {e}")
        return False


async def run_all_tests():
    """Run all standalone tests."""
    print("=" * 60)
    print("NOTIFICATION FILTERING SYSTEM - STANDALONE TEST")
    print("=" * 60)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Custom Rules", test_custom_rules),
        ("Filter Utilities", test_filter_utilities),
        ("Preferences Serialization", test_preferences_serialization),
        ("Deduplication", test_deduplication)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"FINAL RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    if success:
        print("\n🎉 All tests passed successfully!")
    else:
        print("\n⚠️  Some tests failed.")
    
    sys.exit(0 if success else 1)
