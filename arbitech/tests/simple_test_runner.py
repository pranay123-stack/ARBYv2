"""
Simple test runner for mathematical calculations without pytest dependency
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_mathematical_calculations import MathematicalTestSuite

def run_simple_tests():
    print("Running Simple Mathematical Tests...")
    print("=" * 50)
    
    suite = MathematicalTestSuite()
    
    # Test basic functionality without pytest
    print("1. Testing basic probability calculations...")
    try:
        from test_mathematical_calculations import MathematicalArbitrageCalculator
        calculator = MathematicalArbitrageCalculator()
        
        # Test decimal to probability conversion
        odd = calculator.decimal_to_implied_probability(2.0)
        expected = 0.5
        assert abs(float(odd) - expected) < 0.001, f"Expected {expected}, got {float(odd)}"
        print("   ✓ Decimal to probability conversion works")
        
        # Test arbitrage calculation
        odds = [2.1, 1.9, 3.2]
        result = calculator.calculate_arbitrage_profit(odds)
        assert result["arbitrage_exists"] == True, "Should detect arbitrage"
        assert result["profit_margin"] > 0, "Should have positive profit"
        print("   ✓ Arbitrage detection works")
        
        print("Basic mathematical tests PASSED ✓")
        
    except Exception as e:
        print(f"Basic mathematical tests FAILED: {e}")
        return False
    
    print("\n2. Running comprehensive mathematical tests...")
    try:
        results = suite.run_comprehensive_mathematical_tests()
        
        total_tests = results["overall_metrics"]["total_tests"]
        passed_tests = results["overall_metrics"]["passed_tests"]
        success_rate = results["overall_metrics"]["overall_success_rate"]
        
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed Tests: {passed_tests}")
        print(f"   Success Rate: {success_rate:.2%}")
        
        if success_rate >= 0.8:
            print("Comprehensive mathematical tests PASSED ✓")
            return True
        else:
            print(f"Comprehensive mathematical tests FAILED: Low success rate {success_rate:.2%}")
            return False
            
    except Exception as e:
        print(f"Comprehensive mathematical tests FAILED: {e}")
        return False

if __name__ == "__main__":
    success = run_simple_tests()
    
    if success:
        print("\n🎉 All mathematical tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some mathematical tests failed!")
        sys.exit(1)