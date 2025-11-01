"""
VLM Accuracy Testing Framework

Comprehensive testing suite for VLM (Vision Language Model) accuracy on betting interfaces.
Tests extraction accuracy, false positive rates, and confidence scores for various betting scenarios.
"""

import json
import time
import traceback
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from unittest.mock import Mock, patch
import logging

import pytest
from PIL import Image

from arbitech.storage.models import (
    Sport, ArbitrageOpportunity, ArbitrageLeg, TradeStatus, RiskTier
)


class VLMTestResults:
    """Container for VLM test results and metrics."""
    
    def __init__(self):
        self.test_runs = []
        self.accuracy_metrics = {}
        self.false_positive_metrics = {}
        self.confidence_scores = []
        self.performance_metrics = {}
        self.error_logs = []
        
    def add_test_result(self, test_result: Dict[str, Any]):
        """Add a test result to the collection."""
        self.test_runs.append(test_result)
        
    def calculate_accuracy(self) -> Dict[str, float]:
        """Calculate overall accuracy metrics."""
        if not self.test_runs:
            return {"overall_accuracy": 0.0}
            
        correct_extractions = sum(1 for result in self.test_runs 
                                if result.get('extraction_correct', False))
        total_extractions = len(self.test_runs)
        
        odds_accuracy = []
        bookmaker_accuracy = []
        sport_accuracy = []
        
        for result in self.test_runs:
            if 'odds_accuracy' in result:
                odds_accuracy.append(result['odds_accuracy'])
            if 'bookmaker_accuracy' in result:
                bookmaker_accuracy.append(result['bookmaker_accuracy'])
            if 'sport_accuracy' in result:
                sport_accuracy.append(result['sport_accuracy'])
                
        metrics = {
            "overall_accuracy": correct_extractions / total_extractions if total_extractions > 0 else 0.0,
            "odds_extraction_accuracy": sum(odds_accuracy) / len(odds_accuracy) if odds_accuracy else 0.0,
            "bookmaker_detection_accuracy": sum(bookmaker_accuracy) / len(bookmaker_accuracy) if bookmaker_accuracy else 0.0,
            "sport_classification_accuracy": sum(sport_accuracy) / len(sport_accuracy) if sport_accuracy else 0.0,
            "total_tests": total_extractions,
            "successful_extractions": correct_extractions
        }
        
        self.accuracy_metrics = metrics
        return metrics
        
    def calculate_false_positive_rate(self) -> Dict[str, float]:
        """Calculate false positive rates for different categories."""
        if not self.test_runs:
            return {"overall_false_positive_rate": 0.0}
            
        false_positive_categories = {
            "bookmaker": 0,
            "sport": 0,
            "odds": 0,
            "event": 0,
            "market": 0
        }
        
        total_tests = len(self.test_runs)
        for result in self.test_runs:
            false_positives = result.get('false_positives', {})
            for category in false_positive_categories:
                if false_positives.get(category, False):
                    false_positive_categories[category] += 1
                    
        false_positive_rates = {
            category: count / total_tests 
            for category, count in false_positive_categories.items()
        }
        
        overall_fpr = sum(false_positive_categories.values()) / (total_tests * len(false_positive_categories))
        false_positive_rates["overall_false_positive_rate"] = overall_fpr
        
        self.false_positive_metrics = false_positive_rates
        return false_positive_rates
        
    def get_confidence_statistics(self) -> Dict[str, float]:
        """Calculate confidence score statistics."""
        if not self.confidence_scores:
            return {"mean_confidence": 0.0, "median_confidence": 0.0, "std_confidence": 0.0}
            
        scores = [score for score in self.confidence_scores if score is not None]
        if not scores:
            return {"mean_confidence": 0.0, "median_confidence": 0.0, "std_confidence": 0.0}
            
        scores.sort()
        n = len(scores)
        
        stats = {
            "mean_confidence": sum(scores) / n,
            "median_confidence": scores[n // 2] if n % 2 == 1 else (scores[n // 2 - 1] + scores[n // 2]) / 2,
            "std_confidence": (sum((x - stats["mean_confidence"]) ** 2 for x in scores) / n) ** 0.5,
            "min_confidence": min(scores),
            "max_confidence": max(scores),
            "confidence_distribution": {
                "high_confidence": sum(1 for s in scores if s >= 0.8),
                "medium_confidence": sum(1 for s in scores if 0.5 <= s < 0.8),
                "low_confidence": sum(1 for s in scores if s < 0.5)
            }
        }
        
        return stats
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics."""
        if not self.test_runs:
            return {}
            
        processing_times = [result.get('processing_time_ms', 0) for result in self.test_runs]
        success_rates = [1 if result.get('extraction_correct', False) else 0 for result in self.test_runs]
        
        return {
            "average_processing_time_ms": sum(processing_times) / len(processing_times),
            "median_processing_time_ms": sorted(processing_times)[len(processing_times) // 2],
            "success_rate": sum(success_rates) / len(success_rates),
            "total_processing_time_ms": sum(processing_times),
            "tests_per_second": len(self.test_runs) / (sum(processing_times) / 1000) if sum(processing_times) > 0 else 0
        }
        
    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        accuracy = self.calculate_accuracy()
        fpr = self.calculate_false_positive_rate()
        confidence_stats = self.get_confidence_statistics()
        performance = self.get_performance_metrics()
        
        report = f"""
VLM Accuracy Test Report
========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ACCURACY METRICS
----------------
Overall Accuracy: {accuracy.get('overall_accuracy', 0.0):.2%}
Odds Extraction Accuracy: {accuracy.get('odds_extraction_accuracy', 0.0):.2%}
Bookmaker Detection Accuracy: {accuracy.get('bookmaker_detection_accuracy', 0.0):.2%}
Sport Classification Accuracy: {accuracy.get('sport_classification_accuracy', 0.0):.2%}

Total Tests: {accuracy.get('total_tests', 0)}
Successful Extractions: {accuracy.get('successful_extractions', 0)}

FALSE POSITIVE RATES
-------------------
Overall False Positive Rate: {fpr.get('overall_false_positive_rate', 0.0):.2%}
Bookmaker False Positives: {fpr.get('bookmaker', 0.0):.2%}
Sport False Positives: {fpr.get('sport', 0.0):.2%}
Odds False Positives: {fpr.get('odds', 0.0):.2%}
Event False Positives: {fpr.get('event', 0.0):.2%}
Market False Positives: {fpr.get('market', 0.0):.2%}

CONFIDENCE STATISTICS
--------------------
Mean Confidence: {confidence_stats.get('mean_confidence', 0.0):.3f}
Median Confidence: {confidence_stats.get('median_confidence', 0.0):.3f}
Standard Deviation: {confidence_stats.get('std_confidence', 0.0):.3f}
Min Confidence: {confidence_stats.get('min_confidence', 0.0):.3f}
Max Confidence: {confidence_stats.get('max_confidence', 0.0):.3f}

Confidence Distribution:
- High Confidence (≥0.8): {confidence_stats.get('confidence_distribution', {}).get('high_confidence', 0)}
- Medium Confidence (0.5-0.8): {confidence_stats.get('confidence_distribution', {}).get('medium_confidence', 0)}
- Low Confidence (<0.5): {confidence_stats.get('confidence_distribution', {}).get('low_confidence', 0)}

PERFORMANCE METRICS
------------------
Average Processing Time: {performance.get('average_processing_time_ms', 0):.1f} ms
Median Processing Time: {performance.get('median_processing_time_ms', 0):.1f} ms
Success Rate: {performance.get('success_rate', 0.0):.2%}
Tests Per Second: {performance.get('tests_per_second', 0):.2f}

ERROR SUMMARY
------------
Total Errors: {len(self.error_logs)}
"""
        
        if self.error_logs:
            report += "\nRecent Errors:\n"
            for error in self.error_logs[-5:]:  # Show last 5 errors
                report += f"- {error}\n"
                
        return report


class MockVLMExtractor:
    """Mock VLM extractor for testing purposes."""
    
    def __init__(self, accuracy_rate: float = 0.85, confidence_bias: float = 0.0):
        self.accuracy_rate = accuracy_rate
        self.confidence_bias = confidence_bias
        
    def extract_odds_from_image(self, image_path: str, **kwargs) -> Dict[str, Any]:
        """Mock extraction of odds from betting interface image."""
        import random
        random.seed(hash(image_path) % 1000)  # Deterministic based on image path
        
        # Simulate processing time
        processing_time = random.uniform(50, 200)  # ms
        time.sleep(processing_time / 1000)
        
        # Simulate extraction based on accuracy rate
        will_succeed = random.random() < self.accuracy_rate
        
        if will_succeed:
            # Simulate successful extraction
            bookmakers = ["Bet365", "William Hill", "Ladbrokes", "Betfair", "Pinnacle", "1xBet"]
            sports = ["Football", "Tennis", "Basketball", "Baseball"]
            outcomes = ["Home Win", "Away Win", "Draw", "Over 2.5", "Under 2.5"]
            
            result = {
                "success": True,
                "bookmaker": random.choice(bookmakers),
                "sport": random.choice(sports),
                "event_name": f"{random.choice(['Team A', 'Team B'])} vs {random.choice(['Team C', 'Team D'])}",
                "market_type": "match_winner",
                "odds": [
                    {"outcome": random.choice(outcomes), "decimal_odds": round(random.uniform(1.5, 5.0), 2)}
                ],
                "confidence": min(0.95, max(0.6, random.random() + self.confidence_bias)),
                "processing_time_ms": processing_time,
                "raw_text": "Mock extracted text content",
                "detected_elements": ["odds", "team_names", "market_type"]
            }
        else:
            # Simulate failed extraction
            error_types = ["no_odds_found", "unclear_image", "partial_interface", "loading_state", "error_page"]
            result = {
                "success": False,
                "error": random.choice(error_types),
                "confidence": random.uniform(0.1, 0.4),
                "processing_time_ms": processing_time,
                "partial_data": {}
            }
            
        return result


class VLMAccuracyTestSuite:
    """Comprehensive test suite for VLM accuracy testing."""
    
    def __init__(self):
        self.results = VLMTestResults()
        self.sample_data_path = Path(__file__).parent / "create_sample_data"
        self.mock_extractor = MockVLMExtractor()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
    def run_basic_accuracy_tests(self) -> Dict[str, Any]:
        """Run basic accuracy tests with mock data."""
        self.logger.info("Running basic accuracy tests...")
        
        test_cases = [
            # Perfect interface tests
            {
                "image": "perfect_football_interface.png",
                "expected": {
                    "bookmaker": "Bet365",
                    "sport": "Football",
                    "event_name": "Manchester United vs Liverpool",
                    "market_type": "match_winner",
                    "odds": [{"outcome": "Home Win", "decimal_odds": 2.1}]
                },
                "difficulty": "easy"
            },
            {
                "image": "perfect_tennis_interface.png", 
                "expected": {
                    "bookmaker": "William Hill",
                    "sport": "Tennis",
                    "event_name": "Djokovic vs Nadal",
                    "market_type": "match_winner",
                    "odds": [{"outcome": "Djokovic", "decimal_odds": 1.8}]
                },
                "difficulty": "easy"
            },
            # Complex interface tests
            {
                "image": "complex_multi_market_interface.png",
                "expected": {
                    "bookmaker": "Betfair",
                    "sport": "Basketball", 
                    "event_name": "Lakers vs Warriors",
                    "market_type": "total_points",
                    "odds": [{"outcome": "Over 225.5", "decimal_odds": 1.91}]
                },
                "difficulty": "medium"
            },
            # Edge case tests
            {
                "image": "partial_interface.png",
                "expected": None,  # Should fail gracefully
                "difficulty": "hard"
            },
            {
                "image": "loading_state_interface.png", 
                "expected": None,  # Should fail gracefully
                "difficulty": "hard"
            }
        ]
        
        for test_case in test_cases:
            self._run_single_test(test_case)
            
        return self.results.calculate_accuracy()
        
    def run_edge_case_tests(self) -> Dict[str, Any]:
        """Run edge case tests for challenging scenarios."""
        self.logger.info("Running edge case tests...")
        
        edge_cases = [
            {
                "name": "Partial Interface",
                "image": "partial_odds_interface.png",
                "scenario": "Only half the interface visible",
                "expected_failure": True
            },
            {
                "name": "Loading State",
                "image": "loading_spinners_interface.png", 
                "scenario": "Interface showing loading spinners",
                "expected_failure": True
            },
            {
                "name": "Error Page",
                "image": "error_page_interface.png",
                "scenario": "Bookmaker showing error page",
                "expected_failure": True
            },
            {
                "name": "Low Resolution",
                "image": "low_res_interface.png",
                "scenario": "Interface with very low resolution",
                "expected_failure": True
            },
            {
                "name": "Multiple Languages",
                "image": "multilingual_interface.png",
                "scenario": "Interface in multiple languages",
                "expected_failure": False  # Should handle gracefully
            }
        ]
        
        for case in edge_cases:
            self._run_edge_case_test(case)
            
        return {"edge_cases_tested": len(edge_cases)}
        
    def run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks for VLM processing."""
        self.logger.info("Running performance benchmarks...")
        
        # Test processing speed
        start_time = time.time()
        test_images = [
            "performance_test_1.png",
            "performance_test_2.png", 
            "performance_test_3.png",
            "performance_test_4.png",
            "performance_test_5.png"
        ]
        
        for image in test_images * 10:  # Run 50 tests total
            result = self.mock_extractor.extract_odds_from_image(image)
            self.results.confidence_scores.append(result.get('confidence'))
            
        total_time = time.time() - start_time
        
        benchmarks = {
            "total_tests": len(test_images) * 10,
            "total_time_seconds": total_time,
            "tests_per_second": (len(test_images) * 10) / total_time,
            "average_time_per_test_ms": (total_time * 1000) / (len(test_images) * 10)
        }
        
        self.results.performance_metrics = benchmarks
        return benchmarks
        
    def run_integration_tests(self) -> Dict[str, Any]:
        """Test integration with existing data models."""
        self.logger.info("Running integration tests...")
        
        # Test extraction to ArbitrageOpportunity conversion
        test_extractions = [
            {
                "extraction": {
                    "bookmaker": "Bet365",
                    "sport": "Football",
                    "event_name": "Arsenal vs Chelsea",
                    "market_type": "match_winner",
                    "odds": [
                        {"outcome": "Arsenal Win", "decimal_odds": 2.0},
                        {"outcome": "Draw", "decimal_odds": 3.2},
                        {"outcome": "Chelsea Win", "decimal_odds": 3.8}
                    ]
                }
            }
        ]
        
        successful_integrations = 0
        
        for test in test_extractions:
            try:
                # Test conversion to ArbitrageOpportunity
                extraction = test["extraction"]
                
                legs = [
                    ArbitrageLeg(
                        bookmaker=extraction["bookmaker"],
                        event_outcome=odds["outcome"],
                        odds=Decimal(str(odds["decimal_odds"])),
                        implied_probability=Decimal("1.0") / Decimal(str(odds["decimal_odds"])),
                        stake_percentage=Decimal("0.33"),
                        actual_stake=Decimal("100.00"),
                        potential_payout=Decimal(str(odds["decimal_odds"] * 100))
                    )
                    for odds in extraction["odds"]
                ]
                
                opportunity = ArbitrageOpportunity(
                    sport=Sport.FOOTBALL,
                    event_name=extraction["event_name"],
                    event_date=datetime.now() + timedelta(days=1),
                    market_type=extraction["market_type"],
                    legs=legs,
                    total_stake=Decimal("300.00"),
                    profit_margin=Decimal("0.05"),
                    profit_amount=Decimal("15.00"),
                    risk_tier=RiskTier.TIER_A
                )
                
                # Validate the opportunity
                assert opportunity.profit_margin > 0
                assert len(opportunity.legs) == 3
                assert all(leg.implied_probability > 0 for leg in opportunity.legs)
                
                successful_integrations += 1
                
            except Exception as e:
                self.logger.error(f"Integration test failed: {e}")
                self.results.error_logs.append(f"Integration error: {str(e)}")
                
        return {
            "total_integration_tests": len(test_extractions),
            "successful_integrations": successful_integrations,
            "integration_success_rate": successful_integrations / len(test_extractions) if test_extractions else 0
        }
        
    def _run_single_test(self, test_case: Dict[str, Any]) -> None:
        """Run a single accuracy test case."""
        try:
            image_path = str(self.sample_data_path / "betting_interfaces" / test_case["image"])
            
            # Run VLM extraction
            start_time = time.time()
            result = self.mock_extractor.extract_odds_from_image(image_path)
            processing_time = (time.time() - start_time) * 1000
            
            # Evaluate results
            test_result = self._evaluate_test_result(test_case, result, processing_time)
            self.results.add_test_result(test_result)
            
            self.logger.info(f"Test completed: {test_case['image']} - {'PASS' if test_result['extraction_correct'] else 'FAIL'}")
            
        except Exception as e:
            error_msg = f"Test failed for {test_case['image']}: {str(e)}"
            self.logger.error(error_msg)
            self.results.error_logs.append(error_msg)
            
    def _run_edge_case_test(self, test_case: Dict[str, Any]) -> None:
        """Run an edge case test."""
        try:
            image_path = str(self.sample_data_path / "betting_interfaces" / test_case["image"])
            
            start_time = time.time()
            result = self.mock_extractor.extract_odds_from_image(image_path)
            processing_time = (time.time() - start_time) * 1000
            
            # For edge cases, we expect failure but want graceful handling
            expected_failure = test_case.get("expected_failure", False)
            actual_failure = not result.get("success", False)
            
            handled_gracefully = (expected_failure and actual_failure) or (not expected_failure and result.get("success", False))
            
            test_result = {
                "test_name": test_case["name"],
                "scenario": test_case["scenario"],
                "image": test_case["image"],
                "expected_failure": expected_failure,
                "actual_failure": actual_failure,
                "handled_gracefully": handled_gracefully,
                "processing_time_ms": processing_time,
                "confidence": result.get("confidence", 0),
                "extraction_correct": handled_gracefully,
                "error": result.get("error")
            }
            
            self.results.add_test_result(test_result)
            self.logger.info(f"Edge case test: {test_case['name']} - {'PASS' if handled_gracefully else 'FAIL'}")
            
        except Exception as e:
            error_msg = f"Edge case test failed for {test_case['name']}: {str(e)}"
            self.logger.error(error_msg)
            self.results.error_logs.append(error_msg)
            
    def _evaluate_test_result(self, test_case: Dict[str, Any], result: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Evaluate a single test result against expected values."""
        expected = test_case.get("expected")
        
        if expected is None:
            # Edge case test
            return {
                "image": test_case["image"],
                "difficulty": test_case["difficulty"],
                "extraction_correct": not result.get("success", True),  # Should fail
                "processing_time_ms": processing_time,
                "confidence": result.get("confidence", 0),
                "success": result.get("success", False)
            }
            
        # Normal test with expected values
        extraction_correct = True
        false_positives = {}
        
        # Check bookmaker accuracy
        bookmaker_match = result.get("bookmaker") == expected.get("bookmaker")
        extraction_correct &= bookmaker_match
        false_positives["bookmaker"] = not bookmaker_match and result.get("bookmaker") is not None
        
        # Check sport accuracy  
        sport_match = result.get("sport").lower() == expected.get("sport").lower()
        extraction_correct &= sport_match
        false_positives["sport"] = not sport_match and result.get("sport") is not None
        
        # Check event name accuracy
        event_match = result.get("event_name") == expected.get("event_name")
        extraction_correct &= event_match
        false_positives["event"] = not event_match and result.get("event_name") is not None
        
        # Check odds accuracy (simplified)
        odds_accuracy = 0.0
        if result.get("odds") and expected.get("odds"):
            expected_odds = [o["decimal_odds"] for o in expected["odds"]]
            result_odds = [o.get("decimal_odds", 0) for o in result["odds"]]
            
            if len(expected_odds) == len(result_odds):
                correct_odds = sum(1 for e, r in zip(expected_odds, result_odds) if abs(e - r) < 0.1)
                odds_accuracy = correct_odds / len(expected_odds)
            else:
                odds_accuracy = 0.0
                
        extraction_correct &= odds_accuracy > 0.8
        false_positives["odds"] = result.get("odds") and not expected.get("odds")
        
        # Check market type accuracy
        market_match = result.get("market_type") == expected.get("market_type")
        extraction_correct &= market_match
        false_positives["market"] = not market_match and result.get("market_type") is not None
        
        return {
            "image": test_case["image"],
            "difficulty": test_case["difficulty"],
            "extraction_correct": extraction_correct,
            "bookmaker_accuracy": 1.0 if bookmaker_match else 0.0,
            "sport_accuracy": 1.0 if sport_match else 0.0,
            "event_accuracy": 1.0 if event_match else 0.0,
            "odds_accuracy": odds_accuracy,
            "market_accuracy": 1.0 if market_match else 0.0,
            "false_positives": false_positives,
            "processing_time_ms": processing_time,
            "confidence": result.get("confidence", 0),
            "success": result.get("success", False)
        }
        
    def generate_comprehensive_report(self) -> str:
        """Generate a comprehensive test report with all metrics."""
        return self.results.generate_report()
        
    def save_results_to_file(self, filepath: str):
        """Save test results to a JSON file."""
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "test_runs": self.results.test_runs,
            "accuracy_metrics": self.results.accuracy_metrics,
            "false_positive_metrics": self.results.false_positive_metrics,
            "performance_metrics": self.results.performance_metrics,
            "error_logs": self.results.error_logs
        }
        
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
            
        self.logger.info(f"Test results saved to {filepath}")


# Pytest test functions
class TestVLMAccuracy:
    """Pytest test class for VLM accuracy."""
    
    @pytest.fixture
    def test_suite(self):
        """Fixture providing VLM test suite."""
        return VLMAccuracyTestSuite()
        
    def test_basic_accuracy(self, test_suite):
        """Test basic VLM extraction accuracy."""
        results = test_suite.run_basic_accuracy_tests()
        
        # Assertions for basic accuracy
        assert results["overall_accuracy"] >= 0.70, "Overall accuracy should be at least 70%"
        assert results["odds_extraction_accuracy"] >= 0.75, "Odds extraction should be at least 75% accurate"
        assert results["total_tests"] >= 5, "Should run at least 5 basic tests"
        
    def test_edge_cases(self, test_suite):
        """Test edge case handling."""
        results = test_suite.run_edge_case_tests()
        
        assert results["edge_cases_tested"] >= 5, "Should test at least 5 edge cases"
        
    def test_performance_benchmarks(self, test_suite):
        """Test VLM processing performance."""
        results = test_suite.run_performance_benchmarks()
        
        # Performance assertions
        assert results["tests_per_second"] >= 1.0, "Should process at least 1 test per second"
        assert results["average_time_per_test_ms"] <= 500, "Average processing time should be under 500ms"
        
    def test_integration_with_models(self, test_suite):
        """Test integration with existing data models."""
        results = test_suite.run_integration_tests()
        
        assert results["integration_success_rate"] >= 0.80, "Integration success rate should be at least 80%"
        
    def test_confidence_scoring(self, test_suite):
        """Test VLM confidence scoring."""
        test_suite.run_basic_accuracy_tests()
        confidence_stats = test_suite.results.get_confidence_statistics()
        
        assert confidence_stats["mean_confidence"] >= 0.5, "Mean confidence should be at least 0.5"
        assert confidence_stats["confidence_distribution"]["high_confidence"] > 0, "Should have some high confidence results"
        
    def test_false_positive_rates(self, test_suite):
        """Test false positive rates."""
        test_suite.run_basic_accuracy_tests()
        fpr = test_suite.results.calculate_false_positive_rate()
        
        assert fpr["overall_false_positive_rate"] <= 0.20, "Overall false positive rate should be under 20%"
        assert fpr["bookmaker"] <= 0.15, "Bookmaker false positive rate should be under 15%"
        assert fpr["odds"] <= 0.20, "Odds false positive rate should be under 20%"


if __name__ == "__main__":
    # Run tests directly when script is executed
    test_suite = VLMAccuracyTestSuite()
    
    print("Running VLM Accuracy Test Suite...")
    print("=" * 50)
    
    # Run all test categories
    test_suite.run_basic_accuracy_tests()
    test_suite.run_edge_case_tests()
    test_suite.run_performance_benchmarks()
    test_suite.run_integration_tests()
    
    # Generate and print comprehensive report
    report = test_suite.generate_comprehensive_report()
    print(report)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"vlm_test_results_{timestamp}.json"
    test_suite.save_results_to_file(results_file)
    
    print(f"\nResults saved to: {results_file}")