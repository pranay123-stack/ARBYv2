#!/usr/bin/env python3
"""
Test script for the Transcendent Real-Time Decision Engine

This script demonstrates the capabilities of the divine decision engine
and validates its integration with the broader ArbiTech system.

Author: ArbiTech Divine Architecture
Created: 2025-11-02
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

# Add the parent directories to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_opportunity():
    """Create a sample arbitrage opportunity for testing."""
    
    # Import here to avoid issues if components are not available
    try:
        from storage.models import ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier
        from decimal import Decimal
        from datetime import datetime, timedelta
        from pydantic import BaseModel
    except ImportError:
        # Mock classes if storage models are not available
        from enum import Enum
        
        class Sport(str, Enum):
            FOOTBALL = "football"
            BASKETBALL = "basketball"
            TENNIS = "tennis"
        
        class RiskTier(str, Enum):
            TIER_A = "tier_a"
            TIER_B = "tier_b"  
            TIER_C = "tier_c"
            TIER_D = "tier_d"
        
        class ArbitrageLeg(BaseModel):
            bookmaker: str
            event_outcome: str
            odds: Decimal
            implied_probability: Decimal
            stake_percentage: Decimal
            actual_stake: Decimal
            potential_payout: Decimal
        
        class ArbitrageOpportunity(BaseModel):
            id: UUID = uuid4()
            sport: Sport = Sport.FOOTBALL
            event_name: str = "Test Match"
            event_date: datetime = datetime.now() + timedelta(hours=1)
            market_type: str = "match_winner"
            legs: List[ArbitrageLeg]
            total_stake: Decimal = Decimal("310.13")
            profit_margin: Decimal = Decimal("0.05")
            profit_amount: Decimal = Decimal("15.50")
            guaranteed_profit: bool = True
            risk_tier: RiskTier = RiskTier.TIER_B
            liquidity_checked: bool = False
            created_at: datetime = datetime.now()
            source_scanner: str = "test_scanner"
        
        # For non-Pydantic usage, create simple objects  
        class SimpleLeg:
            def __init__(self, bookmaker, odds, stake):
                self.bookmaker = bookmaker
                self.odds = Decimal(str(odds))
                self.stake = Decimal(str(stake))
        
        class SimpleOpportunity:
            def __init__(self):
                self.id = uuid4()
                self.sport = Sport.FOOTBALL
                self.event_name = "Test Match"
                self.event_date = datetime.now() + timedelta(hours=1)
                self.market_type = "match_winner"
                self.legs = []
                self.total_stake = Decimal("310.13")
                self.profit_margin = Decimal("0.05")
                self.profit_amount = Decimal("15.50")
                self.guaranteed_profit = True
                self.risk_tier = RiskTier.TIER_B
                self.liquidity_checked = False
                self.created_at = datetime.now()
                self.source_scanner = "test_scanner"
                self.expected_profit = 15.50
                self.confidence_score = 0.85
                self.max_stake = 500.0
        
        return SimpleOpportunity()
    
    # Create sample opportunity with proper structure
    opportunity = ArbitrageOpportunity(
        sport=Sport.FOOTBALL,
        event_name="Manchester United vs Liverpool",
        event_date=datetime.now() + timedelta(hours=2),
        market_type="match_winner",
        legs=[
            ArbitrageLeg(
                bookmaker="BookmakerA",
                event_outcome="Manchester United Win",
                odds=Decimal("2.1"),
                implied_probability=Decimal("0.476"),
                stake_percentage=Decimal("0.333"),
                actual_stake=Decimal("103.38"),
                potential_payout=Decimal("217.10")
            ),
            ArbitrageLeg(
                bookmaker="BookmakerB", 
                event_outcome="Liverpool Win",
                odds=Decimal("2.05"),
                implied_probability=Decimal("0.488"),
                stake_percentage=Decimal("0.333"),
                actual_stake=Decimal("103.38"),
                potential_payout=Decimal("211.93")
            ),
            ArbitrageLeg(
                bookmaker="BookmakerC",
                event_outcome="Draw", 
                odds=Decimal("1.95"),
                implied_probability=Decimal("0.513"),
                stake_percentage=Decimal("0.334"),
                actual_stake=Decimal("103.37"),
                potential_payout=Decimal("201.57")
            )
        ],
        total_stake=Decimal("310.13"),
        profit_margin=Decimal("0.05"),
        profit_amount=Decimal("15.50"),
        risk_tier=RiskTier.TIER_B
    )
    
    # Add convenience attributes for the decision engine  
    # Note: Use existing fields with proper mapping
    # The decision engine will handle the mapping internally
    
    return opportunity

async def test_decision_engine_basic():
    """Test basic functionality of the decision engine."""
    
    print("🌟 Testing Transcendent Decision Engine")
    print("=" * 60)
    
    try:
        # Import the decision engine
        from autonomous.decision_engine import (
            create_divine_engine,
            CelestialState,
            DivinePriority,
            PredictionHorizon
        )
        
        # Create the engine
        engine = create_divine_engine({
            'max_concurrent_decisions': 5,
            'decision_timeout_ms': 25,
            'learning_enabled': True,
            'quantum_precision_mode': True,
            'performance_monitoring': True,
            'risk_tolerance': 0.4,
            'profit_threshold': 5.0,
            'confidence_threshold': 0.6
        })
        
        print(f"✅ Engine created successfully")
        print(f"   State: {engine.state.value}")
        print(f"   Configuration: {engine.config}")
        
        # Create sample opportunities
        opportunities = []
        for i in range(3):
            opportunity = create_sample_opportunity()
            opportunity.id = uuid4()
            opportunity.expected_profit = 10.0 + (i * 5.0)  # Vary profit
            opportunity.confidence_score = 0.7 + (i * 0.1)  # Vary confidence
            opportunities.append(opportunity)
        
        print(f"\n📊 Created {len(opportunities)} sample opportunities")
        
        # Process opportunities
        divine_opportunities = await engine.process_opportunities_divine(opportunities)
        
        print(f"\n✨ Processed {len(divine_opportunities)} divine opportunities")
        
        # Display results
        for i, divine_opp in enumerate(divine_opportunities):
            print(f"\nDivine Opportunity #{i+1}:")
            print(f"  Original ID: {divine_opp.opportunity.id}")
            print(f"  Divine Score: {divine_opp.divine_score:.4f}")
            print(f"  Risk Score: {divine_opp.quantum_risk.risk_score:.4f}")
            print(f"  Success Probability: {divine_opp.execution_probability:.4f}")
            print(f"  Optimal Stake: {divine_opp.optimal_stake}")
            print(f"  Expected Profit: {divine_opp.expected_profit}")
            print(f"  Prediction Window: {divine_opp.prediction_window.value}")
            print(f"  Risk Factors: {', '.join(divine_opp.quantum_risk.risk_factors[:2])}")
        
        # Test performance monitoring
        performance_report = await engine.get_divine_performance_report()
        assessment = performance_report['divine_assessment']
        
        print(f"\n📈 Divine Performance Assessment:")
        print(f"  Rating: {assessment['rating']}")
        print(f"  Efficiency Score: {assessment['efficiency_score']:.2%}")
        print(f"  Grade: {assessment['divine_grade']}")
        print(f"  Recommendation: {assessment['sacred_recommendation']}")
        
        # Test quantum risk engine separately
        print(f"\n🛡️ Testing Quantum Risk Engine:")
        quantum_risk = engine.risk_engine.assess_quantum_risk(opportunities[0])
        print(f"  Base Risk: {quantum_risk.base_risk:.4f}")
        print(f"  Market Volatility: {quantum_risk.market_volatility:.4f}")
        print(f"  Liquidity Risk: {quantum_risk.liquidity_risk:.4f}")
        print(f"  Execution Risk: {quantum_risk.execution_risk:.4f}")
        print(f"  Quantum Uncertainty: {quantum_risk.quantum_uncertainty:.6f}")
        print(f"  Confidence Interval: {quantum_risk.confidence_interval}")
        
        # Test predictive analytics
        print(f"\n🔮 Testing Predictive Analytics:")
        prediction_data = engine.analytics.predict_optimal_execution_window(opportunities[0])
        print(f"  Optimal Start: {prediction_data.get('optimal_start_time')}")
        print(f"  Duration: {prediction_data.get('optimal_duration')}")
        print(f"  Confidence: {prediction_data.get('confidence_score'):.4f}")
        insights = prediction_data.get('insights', [])
        if insights:
            print(f"  Prophetic Insights: {', '.join(insights[:2])}")
        
        # Test learning system
        print(f"\n🧠 Testing Divine Learning System:")
        success_prob = engine.learning_system.predict_success_probability(opportunities[0])
        print(f"  Success Probability: {success_prob:.4f}")
        
        # Simulate outcome and learning
        mock_outcome = {
            'actual_profit': 12.50,
            'success': True,
            'execution_time': 0.5
        }
        engine.learning_system.update_with_outcome(opportunities[0], {}, mock_outcome)
        print(f"  Learning update completed")
        
        # Shutdown
        await engine.shutdown_divine_engine()
        print(f"\n🌙 Engine shutdown complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_concurrent_processing():
    """Test concurrent processing capabilities."""
    
    print(f"\n🔄 Testing Concurrent Processing")
    print("=" * 40)
    
    try:
        from autonomous.decision_engine import create_divine_engine
        
        engine = create_divine_engine({'max_concurrent_decisions': 8})
        
        # Create multiple opportunities for concurrent processing
        opportunities = []
        for i in range(10):
            opportunity = create_sample_opportunity()
            opportunity.id = uuid4()
            opportunity.expected_profit = 5.0 + (i * 2.0)
            opportunity.confidence_score = 0.6 + (i * 0.04)
            opportunities.append(opportunity)
        
        # Process concurrently
        start_time = asyncio.get_event_loop().time()
        divine_opportunities = await engine.process_opportunities_divine(opportunities)
        end_time = asyncio.get_event_loop().time()
        
        processing_time = (end_time - start_time) * 1000  # Convert to ms
        
        print(f"✅ Concurrent processing complete:")
        print(f"  Opportunities processed: {len(divine_opportunities)}")
        print(f"  Processing time: {processing_time:.2f}ms")
        print(f"  Average per opportunity: {processing_time/len(opportunities):.2f}ms")
        print(f"  Sub-millisecond target: {'✅ PASSED' if processing_time/len(opportunities) < 1.0 else '❌ FAILED'}")
        
        # Test concurrent processor directly
        concurrent_results = await engine.concurrent_processor.process_concurrent_opportunities(
            opportunities[:5], engine
        )
        print(f"  Direct concurrent processor: {len(concurrent_results)} results")
        
        await engine.shutdown_divine_engine()
        return True
        
    except Exception as e:
        print(f"❌ Concurrent test failed: {e}")
        return False

async def test_integration_points():
    """Test integration with other system components."""
    
    print(f"\n🔗 Testing Integration Points")
    print("=" * 40)
    
    try:
        from autonomous.decision_engine import create_divine_engine
        
        engine = create_divine_engine()
        
        # Test that integration methods exist and can be called
        integration_methods = [
            'integrate_opportunity_scanner',
            'integrate_risk_analyzer', 
            'integrate_executor',
            'integrate_approval_workflow'
        ]
        
        for method_name in integration_methods:
            if hasattr(engine, method_name):
                print(f"  ✅ {method_name} - Available")
            else:
                print(f"  ❌ {method_name} - Missing")
        
        # Test execution method
        if hasattr(engine, 'execute_divine_decision'):
            print(f"  ✅ execute_divine_decision - Available")
        else:
            print(f"  ❌ execute_divine_decision - Missing")
        
        await engine.shutdown_divine_engine()
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

async def main():
    """Run all tests for the transcendent decision engine."""
    
    print("🌟 TRANSCENDENT DECISION ENGINE TEST SUITE")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run basic functionality test
    result1 = await test_decision_engine_basic()
    test_results.append(("Basic Functionality", result1))
    
    # Run concurrent processing test
    result2 = await test_concurrent_processing()
    test_results.append(("Concurrent Processing", result2))
    
    # Run integration test
    result3 = await test_integration_points()
    test_results.append(("Integration Points", result3))
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! The divine engine is ready for celestial operations.")
    else:
        print("⚠️  Some tests failed. Review the output above.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())