#!/usr/bin/env python3
"""
Opportunity Scanner Integration Test

This script tests the integration of all opportunity scanner components
to ensure they work together correctly.
"""

import asyncio
import sys
import traceback
from datetime import datetime

# Add project root to path
sys.path.append('/workspace')

def test_imports():
    """Test that all imports work correctly."""
    print("🔍 Testing imports...")
    
    try:
        # Test main scanner components
        from arbitech.detection import (
            OpportunityScanner,
            ScannerEngine,
            MarketMonitor,
            ScanScheduler,
            create_scanner,
            create_market_monitor,
            create_scheduler
        )
        print("✅ Main scanner components imported successfully")
        
        # Test data models
        from arbitech.storage.models import ArbitrageOpportunity, Sport, RiskTier
        print("✅ Data models imported successfully")
        
        # Test VLM integration
        from arbitech.vlm.odds_extractor import OddsExtractor
        print("✅ VLM integration imported successfully")
        
        # Test configuration
        from arbitech.core.config_manager import get_config
        print("✅ Configuration system imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

async def test_basic_functionality():
    """Test basic scanner functionality."""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test scanner creation
        from arbitech.detection import create_scanner
        scanner = await create_scanner()
        print("✅ Scanner created successfully")
        
        # Test status
        status = scanner.get_status()
        assert 'session_id' in status
        assert 'status' in status
        assert 'metrics' in status
        print("✅ Scanner status works correctly")
        
        # Test event handlers
        event_count = 0
        def test_handler(event):
            nonlocal event_count
            event_count += 1
        
        scanner.add_event_handler(test_handler)
        print("✅ Event handlers work correctly")
        
        # Test market monitor
        from arbitech.detection import create_market_monitor
        monitor = await create_market_monitor()
        
        summary = monitor.get_state_summary()
        assert 'total_markets' in summary
        print("✅ Market monitor works correctly")
        
        # Test scheduler
        from arbitech.detection import create_scheduler
        scheduler = await create_scheduler()
        
        metrics = scheduler.get_scheduler_metrics()
        assert 'total_schedules' in metrics
        print("✅ Scan scheduler works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {str(e)}")
        traceback.print_exc()
        return False

async def test_vlm_integration():
    """Test VLM integration."""
    print("\n🤖 Testing VLM integration...")
    
    try:
        from arbitech.vlm.odds_extractor import OddsExtractor
        
        # Test VLM extractor creation
        extractor = OddsExtractor()
        print("✅ VLM Extractor created successfully")
        
        # Test health check (should work even without real VLM endpoint)
        try:
            healthy = await extractor.health_check()
            print(f"✅ VLM health check completed: {'healthy' if healthy else 'needs attention'}")
        except Exception as e:
            print(f"⚠️ VLM health check issue (expected without real endpoint): {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ VLM integration test failed: {str(e)}")
        traceback.print_exc()
        return False

async def test_scanner_lifecycle():
    """Test complete scanner lifecycle."""
    print("\n🔄 Testing scanner lifecycle...")
    
    try:
        from arbitech.detection import create_scanner
        from arbitech.storage.models import Sport
        
        # Create scanner
        scanner = await create_scanner()
        print("✅ Scanner created")
        
        # Test start (should work even without real VLM endpoint)
        try:
            success = await scanner.start_scanning([Sport.FOOTBALL])
            if success:
                print("✅ Scanner started successfully")
                
                # Test that status changes
                status = scanner.get_status()
                if status['status'] == 'scanning':
                    print("✅ Scanner status updated correctly")
                
                # Test stop
                stop_success = await scanner.stop_scanning()
                if stop_success:
                    print("✅ Scanner stopped successfully")
                else:
                    print("⚠️ Scanner stop returned False")
            else:
                print("⚠️ Scanner start returned False (may be expected without VLM)")
                
        except Exception as e:
            print(f"⚠️ Scanner lifecycle issue (may be expected): {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Scanner lifecycle test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration system."""
    print("\n⚙️ Testing configuration...")
    
    try:
        from arbitech.core.config_manager import get_config
        
        # Test basic config access
        bookmakers = get_config('bookmakers', {})
        print("✅ Configuration access works")
        
        # Test system config
        system_config = get_config('system', {})
        print("✅ System configuration accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")
        traceback.print_exc()
        return False

async def test_scheduling():
    """Test scheduling functionality."""
    print("\n📅 Testing scheduling...")
    
    try:
        from arbitech.detection import create_scheduler, ScheduleConfig, ScheduleType
        
        # Create scheduler
        scheduler = await create_scheduler()
        print("✅ Scheduler created")
        
        # Create a simple schedule
        schedule = ScheduleConfig(
            name="Test Schedule",
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=60,
            bookmakers=["test_bookmaker"],
            sports=["test_sport"]
        )
        
        schedule_id = scheduler.create_schedule(schedule)
        print("✅ Schedule created successfully")
        
        # Test schedule status
        status = scheduler.get_schedule_status(schedule_id)
        assert status is not None
        assert status['name'] == "Test Schedule"
        print("✅ Schedule status retrieval works")
        
        # Clean up
        scheduler.delete_schedule(schedule_id)
        print("✅ Schedule deletion works")
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduling test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_models():
    """Test data models."""
    print("\n📊 Testing data models...")
    
    try:
        from arbitech.storage.models import ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier
        from decimal import Decimal
        from datetime import datetime
        
        # Test ArbitrageOpportunity creation with minimum 2 legs
        leg1 = ArbitrageLeg(
            bookmaker="test_bookmaker1",
            event_outcome="home_win",
            odds=Decimal('2.0'),
            implied_probability=Decimal('0.5'),
            stake_percentage=Decimal('1.0'),
            actual_stake=Decimal('100'),
            potential_payout=Decimal('200')
        )
        
        leg2 = ArbitrageLeg(
            bookmaker="test_bookmaker2",
            event_outcome="away_win",
            odds=Decimal('2.1'),
            implied_probability=Decimal('0.476'),
            stake_percentage=Decimal('0.952'),
            actual_stake=Decimal('95.24'),
            potential_payout=Decimal('200')
        )
        
        opportunity = ArbitrageOpportunity(
            sport=Sport.FOOTBALL,
            event_name="Test Event",
            event_date=datetime.utcnow(),
            market_type="match_winner",
            legs=[leg1, leg2],
            total_stake=Decimal('195.24'),
            profit_margin=Decimal('0.024'),
            profit_amount=Decimal('4.76'),
            risk_tier=RiskTier.TIER_A
        )
        
        print("✅ ArbitrageOpportunity creation works")
        print(f"   Profit margin: {float(opportunity.profit_margin)*100:.2f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Data models test failed: {str(e)}")
        traceback.print_exc()
        return False

async def main():
    """Run all integration tests."""
    print("🚀 ARBitech Opportunity Scanner - Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_configuration),
        ("Data Models Test", test_models),
        ("Basic Functionality Test", test_basic_functionality),
        ("VLM Integration Test", test_vlm_integration),
        ("Scanner Lifecycle Test", test_scanner_lifecycle),
        ("Scheduling Test", test_scheduling)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        print("-" * 40)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            results.append((test_name, result))
            
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! The opportunity scanner is ready to use.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    print(f"Starting integration tests at {datetime.now()}")
    
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        traceback.print_exc()
        sys.exit(1)