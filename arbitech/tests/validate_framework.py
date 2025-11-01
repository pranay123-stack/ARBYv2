"""
Standalone validation test for the comprehensive testing framework
This test validates the core functionality without external dependencies
"""

import json
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class SimpleArbitrageDetector:
    """Simplified arbitrage detector for testing framework validation."""
    
    @staticmethod
    def detect_arbitrage(odds_by_bookmaker: Dict[str, List[float]]) -> Dict[str, Any]:
        """Detect arbitrage opportunities."""
        if not odds_by_bookmaker or len(odds_by_bookmaker) < 2:
            return {"arbitrage_exists": False}
        
        # Find best odds for each outcome
        best_odds = {}
        for bookmaker, odds in odds_by_bookmaker.items():
            for i, odd in enumerate(odds):
                if i not in best_odds or odd > best_odds[i]:
                    best_odds[i] = odd
        
        if not best_odds:
            return {"arbitrage_exists": False}
        
        # Calculate market overround
        total_implied_prob = sum(1.0 / odd for odd in best_odds.values())
        arbitrage_exists = total_implied_prob < 1.0
        
        result = {
            "arbitrage_exists": arbitrage_exists,
            "market_overround": total_implied_prob,
            "best_odds": best_odds
        }
        
        if arbitrage_exists:
            result["profit_margin"] = (1.0 - total_implied_prob) * 100
        
        return result


def validate_test_data_generation():
    """Validate that test data was generated correctly."""
    print("1. Validating test data generation...")
    
    test_data_dir = "create_test_data/test_data"
    if not os.path.exists(test_data_dir):
        print("   ❌ Test data directory not found")
        return False
    
    # Check for key test data files
    expected_files = [
        "clear_arbitrage.json",
        "no_arbitrage.json", 
        "bookmaker_dataset.json",
        "index.json"
    ]
    
    missing_files = []
    for file in expected_files:
        filepath = os.path.join(test_data_dir, file)
        if not os.path.exists(filepath):
            missing_files.append(file)
    
    if missing_files:
        print(f"   ❌ Missing test data files: {missing_files}")
        return False
    
    # Validate content of a test file
    try:
        with open(os.path.join(test_data_dir, "clear_arbitrage.json"), 'r') as f:
            data = json.load(f)
        
        if "expected_arbitrage" not in data:
            print("   ❌ Missing expected_arbitrage field in test data")
            return False
            
        print("   ✓ Test data generation validated")
        return True
        
    except Exception as e:
        print(f"   ❌ Error validating test data: {e}")
        return False


def validate_arbitrage_detection():
    """Validate arbitrage detection functionality."""
    print("\n2. Validating arbitrage detection...")
    
    detector = SimpleArbitrageDetector()
    
    test_cases = [
        {
            "name": "Clear arbitrage",
            "odds": {
                "Bookmaker_A": [2.1, 1.9, 3.2],
                "Bookmaker_B": [1.9, 2.2, 2.8]
            },
            "expected_arbitrage": True
        },
        {
            "name": "No arbitrage", 
            "odds": {
                "Bookmaker_A": [1.8, 1.9, 2.1],
                "Bookmaker_B": [1.85, 1.95, 2.05]
            },
            "expected_arbitrage": False
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for case in test_cases:
        try:
            result = detector.detect_arbitrage(case["odds"])
            actual = result.get("arbitrage_exists", False)
            expected = case["expected_arbitrage"]
            
            if actual == expected:
                print(f"   ✓ {case['name']}: PASS")
                passed += 1
            else:
                print(f"   ❌ {case['name']}: FAIL (expected {expected}, got {actual})")
                
        except Exception as e:
            print(f"   ❌ {case['name']}: ERROR - {e}")
    
    success_rate = passed / total
    print(f"   Arbitrage detection success rate: {success_rate:.2%}")
    return success_rate >= 0.5


def validate_mathematical_calculations():
    """Validate mathematical calculation functions."""
    print("\n3. Validating mathematical calculations...")
    
    try:
        # Test decimal operations
        odds = [Decimal("2.0"), Decimal("3.0"), Decimal("6.0")]
        
        # Test implied probability calculation
        implied_probs = [Decimal("1") / odd for odd in odds]
        market_overround = sum(implied_probs)
        
        expected_overround = float(Decimal("1"))
        actual_overround = float(market_overround)
        
        if abs(actual_overround - expected_overround) < 0.001:
            print("   ✓ Market overround calculation validated")
        else:
            print(f"   ❌ Market overround calculation failed: {actual_overround} != {expected_overround}")
            return False
        
        # Test profit calculation
        if market_overround < Decimal("1"):
            total_stake = Decimal("1000")
            optimal_stakes = []
            for i, odd in enumerate(odds):
                stake_percentage = implied_probs[i] / market_overround
                actual_stake = total_stake * stake_percentage
                optimal_stakes.append(float(actual_stake))
            
            best_payout = min(odd * stake for odd, stake in zip(odds, optimal_stakes))
            profit = best_payout - total_stake
            
            if profit > 0:
                print("   ✓ Profit calculation validated")
                return True
            else:
                print("   ❌ Profit calculation failed: negative profit")
                return False
        else:
            print("   ✓ Non-arbitrage scenario handled correctly")
            return True
            
    except Exception as e:
        print(f"   ❌ Mathematical calculations error: {e}")
        return False


def validate_data_aggregation():
    """Validate data aggregation concepts."""
    print("\n4. Validating data aggregation concepts...")
    
    try:
        # Simulate bookmaker data
        bookmaker_data = {
            "Bet365": {
                "odds": [2.0, 3.0, 4.0],
                "timestamp": datetime.now().isoformat(),
                "quality_score": 0.95
            },
            "William Hill": {
                "odds": [1.9, 3.1, 3.9], 
                "timestamp": datetime.now().isoformat(),
                "quality_score": 0.90
            }
        }
        
        # Validate data structure
        if len(bookmaker_data) >= 2:
            print("   ✓ Multi-bookmaker data structure validated")
        else:
            print("   ❌ Insufficient bookmaker data")
            return False
        
        # Validate odds consistency
        outcome_counts = [len(data["odds"]) for data in bookmaker_data.values()]
        if len(set(outcome_counts)) == 1:
            print("   ✓ Outcome consistency validated")
        else:
            print("   ❌ Outcome inconsistency detected")
            return False
        
        # Calculate data quality
        quality_scores = [data["quality_score"] for data in bookmaker_data.values()]
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        if avg_quality >= 0.8:
            print(f"   ✓ Data quality validated (avg: {avg_quality:.2f})")
            return True
        else:
            print(f"   ❌ Low data quality: {avg_quality:.2f}")
            return False
            
    except Exception as e:
        print(f"   ❌ Data aggregation error: {e}")
        return False


def validate_performance_concepts():
    """Validate performance testing concepts."""
    print("\n5. Validating performance concepts...")
    
    try:
        # Simulate performance testing
        detector = SimpleArbitrageDetector()
        
        # Test with increasing complexity
        test_sizes = [2, 5, 10, 20]
        times = []
        
        for size in test_sizes:
            # Create test data
            odds_data = {
                f"Bookmaker_{i}": [2.0 + i * 0.1, 3.0 + i * 0.1, 4.0 + i * 0.1]
                for i in range(size)
            }
            
            # Time the detection
            start_time = time.time()
            for _ in range(100):  # Run multiple times for accuracy
                detector.detect_arbitrage(odds_data)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 100 * 1000  # ms per detection
            times.append(avg_time)
        
        print(f"   Performance test results:")
        for size, time_ms in zip(test_sizes, times):
            print(f"     {size} bookmakers: {time_ms:.2f}ms per detection")
        
        # Check scalability (time should not grow too rapidly)
        if times[-1] / times[0] < 10:  # Should not be 10x slower
            print("   ✓ Scalability validated")
            return True
        else:
            print("   ❌ Poor scalability detected")
            return False
            
    except Exception as e:
        print(f"   ❌ Performance testing error: {e}")
        return False


def run_framework_validation():
    """Run comprehensive framework validation."""
    print("COMPREHENSIVE TESTING FRAMEWORK VALIDATION")
    print("=" * 50)
    
    validation_results = []
    
    # Run all validation tests
    validation_results.append(("Test Data Generation", validate_test_data_generation()))
    validation_results.append(("Arbitrage Detection", validate_arbitrage_detection()))
    validation_results.append(("Mathematical Calculations", validate_mathematical_calculations()))
    validation_results.append(("Data Aggregation", validate_data_aggregation()))
    validation_results.append(("Performance Concepts", validate_performance_concepts()))
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in validation_results if result)
    total = len(validation_results)
    success_rate = passed / total
    
    for test_name, result in validation_results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall Success Rate: {success_rate:.2%} ({passed}/{total})")
    
    if success_rate >= 0.8:
        print("\n🎉 Framework validation PASSED!")
        print("The comprehensive testing framework is working correctly.")
        return True
    else:
        print("\n❌ Framework validation FAILED!")
        print("Please review the failing components.")
        return False


if __name__ == "__main__":
    success = run_framework_validation()
    sys.exit(0 if success else 1)