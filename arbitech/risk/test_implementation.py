"""
Simple test to validate the bankroll and limit validation system implementation.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta

# Import the risk management components
try:
    from risk import BankrollValidator, LimitManager, ExposureTracker, ValidationEngine
    from storage.models import (
        ArbitrageOpportunity, Trade, Sport, RiskTier, TradeStatus, 
        RiskConfig, TierASettings, TierBSettings, GlobalLimits, Failsafes,
        StakeData, ArbitrageLeg, ArbitrageLeg
    )
    print("✓ All imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


async def test_basic_functionality():
    """Test basic functionality of the risk management system."""
    print("\n" + "="*60)
    print("TESTING BASIC FUNCTIONALITY")
    print("="*60)
    
    try:
        # Create basic risk config
        risk_config = RiskConfig(
            user_id=uuid4(),
            name="Test Configuration",
            tier_a_settings=TierASettings(
                max_stake_per_trade='100',
                max_daily_exposure='500',
                min_profit_margin='0.02'
            ),
            global_limits=GlobalLimits(
                max_total_exposure='1000',
                system_min_profit_margin='0.01'
            ),
            failsafes=Failsafes(
                emergency_stop_loss='200',
                max_loss_per_hour='100'
            )
        )
        print("✓ Risk configuration created")
        
        # Test Bankroll Validator
        bankroll_validator = BankrollValidator(risk_config)
        validation_result = await bankroll_validator.validate_bankroll()
        print(f"✓ Bankroll validator initialized (valid: {validation_result.is_valid})")
        
        # Test Limit Manager
        limit_manager = LimitManager(risk_config)
        print(f"✓ Limit manager initialized ({len(limit_manager.rules)} rules)")
        
        # Test Exposure Tracker
        exposure_tracker = ExposureTracker()
        print("✓ Exposure tracker initialized")
        
        # Test Validation Engine
        validation_engine = ValidationEngine(risk_config)
        print(f"✓ Validation engine initialized ({len(validation_engine.rules)} rules)")
        
        print("\n✅ All basic components initialized successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_validation_pipeline():
    """Test the validation pipeline with a sample opportunity."""
    print("\n" + "="*60)
    print("TESTING VALIDATION PIPELINE")
    print("="*60)
    
    try:
        # Create risk config
        risk_config = RiskConfig(
            user_id=uuid4(),
            name="Test Validation",
            tier_a_settings=TierASettings(
                max_stake_per_trade='100',
                max_daily_exposure='500'
            ),
            global_limits=GlobalLimits(
                max_total_exposure='1000'
            )
        )
        
        # Create validation engine
        validation_engine = ValidationEngine(risk_config)
        
        # Create sample opportunity
        leg1 = ArbitrageLeg(
            bookmaker="bet365",
            event_outcome="Team A wins",
            odds='2.0',
            implied_probability='0.5',
            stake_percentage='0.5',
            actual_stake='50',
            potential_payout='100'
        )
        
        leg2 = ArbitrageLeg(
            bookmaker="william_hill",
            event_outcome="Team B wins or draw",
            odds='2.0',
            implied_probability='0.5',
            stake_percentage='0.5',
            actual_stake='50',
            potential_payout='100'
        )
        
        opportunity = ArbitrageOpportunity(
            sport=Sport.FOOTBALL,
            event_name="Team A vs Team B",
            event_date=datetime.utcnow() + timedelta(hours=2),
            market_type="match_winner",
            legs=[leg1, leg2],
            total_stake='100',
            profit_margin='0.02',
            profit_amount='2',
            guaranteed_profit=True,
            risk_tier=RiskTier.TIER_A
        )
        
        # Test validation
        user_id = uuid4()
        validation_report = await validation_engine.validate_trade(
            opportunity,
            opportunity.total_stake,
            user_id
        )
        
        print(f"✓ Validation completed")
        print(f"  Score: {validation_report.overall_score:.3f}")
        print(f"  Risk: {validation_report.risk_assessment.value}")
        print(f"  Rules: {validation_report.passed_rules}/{validation_report.total_rules}")
        
        print("\n✅ Validation pipeline test passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Validation pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """Test component integration."""
    print("\n" + "="*60)
    print("TESTING COMPONENT INTEGRATION")
    print("="*60)
    
    try:
        # Create risk config
        risk_config = RiskConfig(
            user_id=uuid4(),
            name="Integration Test",
            tier_a_settings=TierASettings(
                max_stake_per_trade='100',
                max_daily_exposure='500'
            ),
            global_limits=GlobalLimits(
                max_total_exposure='1000'
            )
        )
        
        # Initialize all components
        bankroll_validator = BankrollValidator(risk_config)
        limit_manager = LimitManager(risk_config)
        exposure_tracker = ExposureTracker()
        validation_engine = ValidationEngine(risk_config)
        
        # Start monitoring
        await asyncio.gather(
            bankroll_validator.start_monitoring(),
            exposure_tracker.start_monitoring(),
            validation_engine.start_monitoring()
        )
        print("✓ All monitoring started")
        
        # Create sample trade
        leg1 = ArbitrageLeg(
            bookmaker="bet365",
            event_outcome="Outcome 1",
            odds='2.0',
            implied_probability='0.5',
            stake_percentage='0.5',
            actual_stake='50',
            potential_payout='100'
        )
        
        leg2 = ArbitrageLeg(
            bookmaker="william_hill",
            event_outcome="Outcome 2",
            odds='2.0',
            implied_probability='0.5',
            stake_percentage='0.5',
            actual_stake='50',
            potential_payout='100'
        )
        
        opportunity = ArbitrageOpportunity(
            sport=Sport.FOOTBALL,
            event_name="Test Event",
            event_date=datetime.utcnow() + timedelta(hours=1),
            market_type="test",
            legs=[leg1, leg2],
            total_stake='100',
            profit_margin='0.02',
            profit_amount='2',
            guaranteed_profit=True,
            risk_tier=RiskTier.TIER_A
        )
        
        trade = Trade(
            user_id=uuid4(),
            opportunity=opportunity,
            status=TradeStatus.PENDING,
            stake_data=StakeData(
                total_stake='100',
                currency="USD",
                leg_allocations={"bet365": '50', "william_hill": '50'},
                fees_included='0',
                net_stake='100'
            ),
            expected_profit='2'
        )
        
        # Test integration
        print("Testing trade processing...")
        
        # Add to bankroll validator
        success = await bankroll_validator.add_trade(trade)
        print(f"✓ Trade added to bankroll validator: {success}")
        
        # Add to exposure tracker
        positions = await exposure_tracker.add_position(trade)
        print(f"✓ Positions added to exposure tracker: {len(positions)}")
        
        # Record in limit manager
        await limit_manager.record_trade_execution(trade)
        print("✓ Trade recorded in limit manager")
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Get metrics
        bankroll_metrics = await bankroll_validator.get_bankroll_metrics()
        print(f"✓ Bankroll metrics: ${bankroll_metrics['total_balance']}")
        
        exposure_summary = await exposure_tracker.get_exposure_summary()
        print(f"✓ Exposure summary: ${exposure_summary['total_exposure']}")
        
        limit_summary = await limit_manager.get_limit_summary()
        print(f"✓ Limit summary: {limit_summary['active_rules']} active rules")
        
        # Stop monitoring
        await asyncio.gather(
            bankroll_validator.stop_monitoring(),
            exposure_tracker.stop_monitoring(),
            validation_engine.stop_monitoring()
        )
        print("✓ All monitoring stopped")
        
        print("\n✅ Component integration test passed")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("="*60)
    print("RISK MANAGEMENT SYSTEM - VALIDATION TESTS")
    print("="*60)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Validation Pipeline", test_validation_pipeline),
        ("Component Integration", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! The risk management system is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed} tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)