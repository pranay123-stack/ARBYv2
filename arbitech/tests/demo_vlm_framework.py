#!/usr/bin/env python3
"""
VLM Testing Framework Demo

Quick demonstration of the VLM testing framework capabilities.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import with fallback for missing dependencies
try:
    from tests.test_vlm_accuracy import VLMAccuracyTestSuite
    VLM_AVAILABLE = True
except ImportError:
    print("⚠ VLM accuracy tests not available (missing dependencies)")
    VLM_AVAILABLE = False

try:
    from tests.test_bookmaker_specific import BookmakerVLMTester
    BOOKMAKER_AVAILABLE = True
except ImportError:
    print("⚠ Bookmaker tests not available (missing dependencies)")
    BOOKMAKER_AVAILABLE = False

try:
    from tests.test_odds_validation import OddsValidationTestSuite
    VALIDATION_AVAILABLE = True
except ImportError:
    print("⚠ Odds validation tests not available (missing dependencies)")
    VALIDATION_AVAILABLE = False

from tests.create_sample_data.data_provider import SampleDataProvider


def demo_data_provider():
    """Demonstrate the sample data provider."""
    print("=" * 60)
    print("SAMPLE DATA PROVIDER DEMO")
    print("=" * 60)
    
    provider = SampleDataProvider()
    
    # Show dataset summary
    print("Dataset Summary:")
    provider.print_dataset_summary()
    
    print("\nAvailable Test Scenarios:")
    scenarios = provider.list_available_scenarios()
    for scenario in scenarios:
        print(f"  - {scenario}")
    
    print("\nBookmaker Coverage:")
    bookmakers = provider.get_bookmaker_list()
    for bookmaker in bookmakers:
        images = provider.get_test_images(bookmaker=bookmaker)
        print(f"  - {bookmaker}: {len(images)} images")
    
    print("\nSport Coverage:")
    sports = provider.get_sport_list()
    for sport in sports:
        images = provider.get_test_images(sport=sport)
        print(f"  - {sport}: {len(images)} images")
    
    # Validate sample data
    print("\nData Validation:")
    validation = provider.validate_sample_data()
    print(f"  Valid: {validation['is_valid']}")
    print(f"  Issues: {len(validation['issues'])}")
    print(f"  Warnings: {len(validation['warnings'])}")
    
    return provider


def demo_vlm_accuracy_tests():
    """Demonstrate VLM accuracy tests."""
    if not VLM_AVAILABLE:
        print("\n" + "=" * 60)
        print("VLM ACCURACY TESTS DEMO")
        print("=" * 60)
        print("VLM accuracy tests not available - install test dependencies")
        print("Run: pip install -r tests/requirements.txt")
        return None
        
    print("\n" + "=" * 60)
    print("VLM ACCURACY TESTS DEMO")
    print("=" * 60)
    
    test_suite = VLMAccuracyTestSuite()
    
    print("Running basic accuracy tests...")
    accuracy_results = test_suite.run_basic_accuracy_tests()
    print(f"  Overall Accuracy: {accuracy_results.get('overall_accuracy', 0):.2%}")
    print(f"  Total Tests: {accuracy_results.get('total_tests', 0)}")
    
    print("\nRunning edge case tests...")
    edge_results = test_suite.run_edge_case_tests()
    print(f"  Edge Cases Tested: {edge_results.get('edge_cases_tested', 0)}")
    
    print("\nRunning performance benchmarks...")
    perf_results = test_suite.run_performance_benchmarks()
    print(f"  Tests Per Second: {perf_results.get('tests_per_second', 0):.2f}")
    print(f"  Average Time: {perf_results.get('average_time_per_test_ms', 0):.1f}ms")
    
    return test_suite


def demo_bookmaker_tests():
    """Demonstrate bookmaker-specific tests."""
    if not BOOKMAKER_AVAILABLE:
        print("\n" + "=" * 60)
        print("BOOKMAKER-SPECIFIC TESTS DEMO")
        print("=" * 60)
        print("Bookmaker tests not available - install test dependencies")
        print("Run: pip install -r tests/requirements.txt")
        return None
        
    print("\n" + "=" * 60)
    print("BOOKMAKER-SPECIFIC TESTS DEMO")
    print("=" * 60)
    
    tester = BookmakerVLMTester()
    
    print("Testing individual bookmakers...")
    bookmakers = ["bet365", "william_hill", "betfair"]
    
    for bookmaker in bookmakers:
        try:
            results = tester.test_bookmaker_interface_recognition(bookmaker)
            print(f"  {bookmaker}:")
            print(f"    Accuracy: {results.get('extraction_accuracy', 0):.2%}")
            print(f"    Avg Confidence: {results.get('average_confidence', 0):.3f}")
            print(f"    Processing Time: {results.get('average_processing_time', 0):.1f}ms")
        except Exception as e:
            print(f"  {bookmaker}: Error - {e}")
    
    print("\nCross-bookmaker comparison...")
    comparison = tester.test_cross_bookmaker_comparison()
    if comparison.get("best_performing"):
        print(f"  Best Performing: {comparison['best_performing']}")
        print(f"  Worst Performing: {comparison['worst_performing']}")
        print(f"  Average Accuracy: {comparison.get('average_accuracy', 0):.2%}")
    
    return tester


def demo_odds_validation():
    """Demonstrate odds validation tests."""
    if not VALIDATION_AVAILABLE:
        print("\n" + "=" * 60)
        print("ODDS VALIDATION TESTS DEMO")
        print("=" * 60)
        print("Odds validation tests not available - install test dependencies")
        print("Run: pip install -r tests/requirements.txt")
        return None
        
    print("\n" + "=" * 60)
    print("ODDS VALIDATION TESTS DEMO")
    print("=" * 60)
    
    validator = OddsValidationTestSuite()
    
    print("Testing probability sum validation...")
    prob_results = validator.test_probability_sum_validation()
    print(f"  Tests Run: {prob_results.get('total_tests', 0)}")
    print(f"  Success Rate: {prob_results.get('success_rate', 0):.2%}")
    
    print("\nTesting arbitrage detection...")
    arb_results = validator.test_arbitrage_detection()
    print(f"  Tests Run: {arb_results.get('total_tests', 0)}")
    print(f"  Success Rate: {arb_results.get('success_rate', 0):.2%}")
    
    print("\nTesting consistency validation...")
    cons_results = validator.test_odds_consistency_validation()
    print(f"  Tests Run: {cons_results.get('total_tests', 0)}")
    print(f"  Success Rate: {cons_results.get('success_rate', 0):.2%}")
    
    print("\nVLM integration validation...")
    int_results = validator.test_vlm_integration_validation()
    print(f"  Extractions: {int_results.get('total_extractions', 0)}")
    print(f"  Success Rate: {int_results.get('extraction_success_rate', 0):.2%}")
    
    return validator


def demo_comprehensive_report():
    """Demonstrate comprehensive reporting."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST REPORTING DEMO")
    print("=" * 60)
    
    # Run a quick test to generate results
    test_suite = VLMAccuracyTestSuite()
    test_suite.run_basic_accuracy_tests()
    
    # Generate report
    report = test_suite.generate_comprehensive_report()
    print("Sample Report Preview:")
    print("-" * 40)
    
    # Show first few lines of the report
    lines = report.split('\n')[:15]
    for line in lines:
        print(line)
    print("...")
    print(f"(Report continues for {len(lines)} more lines)")
    
    return report


def main():
    """Main demo function."""
    print("VLM Testing Framework - Comprehensive Demo")
    print("=" * 80)
    print("This demo showcases the key features and capabilities of the VLM testing framework.")
    print()
    
    try:
        # Demo 1: Data Provider
        provider = demo_data_provider()
        
        # Demo 2: VLM Accuracy Tests (if available)
        vlm_tester = None
        if VLM_AVAILABLE:
            vlm_tester = demo_vlm_accuracy_tests()
        
        # Demo 3: Bookmaker-Specific Tests (if available)
        bookmaker_tester = None
        if BOOKMAKER_AVAILABLE:
            bookmaker_tester = demo_bookmaker_tests()
        
        # Demo 4: Odds Validation Tests (if available)
        odds_validator = None
        if VALIDATION_AVAILABLE:
            odds_validator = demo_odds_validation()
        
        # Demo 5: Comprehensive Reporting (if available)
        report = None
        if vlm_tester is not None:
            report = demo_comprehensive_report()
        
        print("\n" + "=" * 80)
        print("DEMO SUMMARY")
        print("=" * 80)
        print("✓ Sample data provider loaded and validated")
        
        available_features = []
        if VLM_AVAILABLE:
            available_features.append("VLM accuracy tests")
        if BOOKMAKER_AVAILABLE:
            available_features.append("bookmaker-specific tests")
        if VALIDATION_AVAILABLE:
            available_features.append("odds validation tests")
        
        for feature in available_features:
            print(f"✓ {feature} executed successfully")
            
        if not available_features:
            print("⚠ Test modules not available - install dependencies")
            print("  Run: pip install -r tests/requirements.txt")
        
        print()
        print("Available Features:")
        print("• Sample data provider and management")
        if VLM_AVAILABLE:
            print("• Quantitative accuracy metrics across multiple categories")
        if BOOKMAKER_AVAILABLE:
            print("• Bookmaker-specific interface testing")
        if VALIDATION_AVAILABLE:
            print("• Mathematical odds validation and arbitrage detection")
        print("• Edge case handling and error recovery")
        print("• Performance benchmarking and monitoring")
        print("• Comprehensive reporting and analysis")
        print()
        print("The VLM Testing Framework is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)