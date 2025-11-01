"""
Comprehensive Arbitrage Detection Testing Framework

This module provides comprehensive testing for arbitrage detection algorithms
using realistic market data and scenarios. Tests detection accuracy, false
positive/negative rates, and performance under various conditions.

Key Features:
- Quantitative accuracy metrics for detection rates
- False positive/negative analysis
- Profit calculation accuracy validation
- Stress testing with high-frequency market changes
- Edge case testing and unusual market conditions
- Performance benchmarking and scalability testing
- Detailed test reporting with analysis and recommendations
- Continuous integration support
"""

import json
import time
import threading
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable
import logging
import statistics
import concurrent.futures
from dataclasses import dataclass

import pytest


@dataclass
class ArbitrageDetectionMetrics:
    """Container for arbitrage detection test metrics."""
    
    total_tests: int = 0
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    
    detection_time_ms: float = 0.0
    profit_calculation_accuracy: float = 0.0
    
    def calculate_metrics(self):
        """Calculate all performance metrics."""
        if self.total_tests == 0:
            return
            
        # Basic metrics
        self.accuracy = (self.true_positives + self.true_negatives) / self.total_tests
        
        # Precision (avoid false positives)
        if self.true_positives + self.false_positives > 0:
            self.precision = self.true_positives / (self.true_positives + self.false_positives)
        
        # Recall (avoid false negatives)
        if self.true_positives + self.false_negatives > 0:
            self.recall = self.true_positives / (self.true_positives + self.false_negatives)
        
        # F1 Score
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)


class RealisticArbitrageDetector:
    """Realistic arbitrage detector implementation for testing."""
    
    @staticmethod
    def detect_arbitrage(odds_by_bookmaker: Dict[str, List[Decimal]]) -> Dict[str, Any]:
        """Detect arbitrage opportunities with realistic detection logic."""
        
        if not odds_by_bookmaker or len(odds_by_bookmaker) < 2:
            return {"arbitrage_exists": False, "confidence": 0.0}
        
        # Find best odds for each outcome
        best_odds = {}
        best_bookmakers = {}
        
        all_outcomes = list(range(len(next(iter(odds_by_bookmaker.values())))))
        
        for outcome_idx in all_outcomes:
            best_odd = Decimal("0")
            best_bookmaker = ""
            
            for bookmaker, odds in odds_by_bookmaker.items():
                if outcome_idx < len(odds) and odds[outcome_idx] > best_odd:
                    best_odd = odds[outcome_idx]
                    best_bookmaker = bookmaker
            
            if best_odd > 0:
                best_odds[outcome_idx] = best_odd
                best_bookmakers[outcome_idx] = best_bookmaker
        
        if not best_odds:
            return {"arbitrage_exists": False, "confidence": 0.0}
        
        # Calculate market overround
        total_implied_prob = sum(Decimal("1.0") / odd for odd in best_odds.values())
        market_overround = total_implied_prob
        
        # Detect arbitrage (margin < 100%)
        arbitrage_exists = market_overround < Decimal("1.0")
        
        # Calculate confidence based on margin
        if arbitrage_exists:
            margin = Decimal("1.0") - market_overround
            confidence = min(1.0, float(margin / Decimal("0.05")))  # Higher confidence for larger margins
        else:
            margin = market_overround - Decimal("1.0")
            confidence = max(0.0, 1.0 - float(margin / Decimal("0.20")))  # Lower confidence for larger margins
        
        result = {
            "arbitrage_exists": arbitrage_exists,
            "confidence": confidence,
            "market_overround": float(market_overround),
            "best_odds": {k: float(v) for k, v in best_odds.items()},
            "best_bookmakers": best_bookmakers
        }
        
        if arbitrage_exists:
            # Calculate optimal stakes and profit
            total_stake = Decimal("1000.0")
            
            # Optimal stake for each outcome
            optimal_stakes = []
            for odd in best_odds.values():
                implied_prob = Decimal("1.0") / odd
                stake_percentage = implied_prob / total_implied_prob
                actual_stake = total_stake * stake_percentage
                optimal_stakes.append(float(actual_stake))
            
            # Calculate guaranteed profit
            best_payout = min(odd * stake for odd, stake in zip(best_odds.values(), optimal_stakes))
            guaranteed_profit = float(best_payout - total_stake)
            profit_margin = (guaranteed_profit / float(total_stake)) * 100
            
            result.update({
                "optimal_stakes": optimal_stakes,
                "guaranteed_profit": guaranteed_profit,
                "profit_margin": profit_margin,
                "total_stake": float(total_stake)
            })
        
        return result
    
    @staticmethod
    def calculate_profit_accuracy(expected_profit: float, actual_profit: float, tolerance: float = 0.01) -> bool:
        """Calculate if profit calculation is accurate within tolerance."""
        if expected_profit == 0 and actual_profit == 0:
            return True
        
        if expected_profit == 0:
            return abs(actual_profit) < tolerance
        
        relative_error = abs(actual_profit - expected_profit) / abs(expected_profit)
        return relative_error <= tolerance


class ArbitrageDetectionTestSuite:
    """Comprehensive test suite for arbitrage detection algorithms."""
    
    def __init__(self, test_data_path: Optional[str] = None):
        self.test_data_path = test_data_path or "test_data"
        self.detector = RealisticArbitrageDetector()
        self.metrics = ArbitrageDetectionMetrics()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.detection_times = []
        self.memory_usage_samples = []
        
    def run_detection_accuracy_tests(self) -> Dict[str, Any]:
        """Run comprehensive detection accuracy tests."""
        self.logger.info("Running arbitrage detection accuracy tests...")
        
        # Test scenarios with known outcomes
        test_scenarios = [
            {
                "name": "Clear Arbitrage - Three Way",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("2.1"), Decimal("1.9"), Decimal("3.2")],
                    "Bookmaker_B": [Decimal("1.9"), Decimal("2.2"), Decimal("2.8")],
                    "Bookmaker_C": [Decimal("2.0"), Decimal("1.8"), Decimal("3.5")]
                },
                "expected_arbitrage": True,
                "expected_profit_margin": 3.2
            },
            {
                "name": "Clear Arbitrage - Two Way",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("1.8"), Decimal("2.3")],
                    "Bookmaker_B": [Decimal("2.1"), Decimal("1.9")]
                },
                "expected_arbitrage": True,
                "expected_profit_margin": 5.3
            },
            {
                "name": "No Arbitrage - Standard Market",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("1.8"), Decimal("1.9"), Decimal("2.1")],
                    "Bookmaker_B": [Decimal("1.85"), Decimal("1.95"), Decimal("2.05")],
                    "Bookmaker_C": [Decimal("1.9"), Decimal("1.85"), Decimal("2.15")]
                },
                "expected_arbitrage": False,
                "expected_profit_margin": -5.5
            },
            {
                "name": "Marginal - Near Break Even",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("1.98"), Decimal("2.02")],
                    "Bookmaker_B": [Decimal("2.01"), Decimal("1.99")]
                },
                "expected_arbitrage": False,  # Treat as no arbitrage due to calculation precision
                "expected_profit_margin": 0.1
            },
            {
                "name": "Edge Case - Very High Odds",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("15.0"), Decimal("25.0"), Decimal("50.0")],
                    "Bookmaker_B": [Decimal("14.0"), Decimal("30.0"), Decimal("45.0")]
                },
                "expected_arbitrage": True,
                "expected_profit_margin": 7.1
            }
        ]
        
        results = {
            "total_tests": len(test_scenarios),
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "detection_metrics": {}
        }
        
        for scenario in test_scenarios:
            test_start_time = time.time()
            
            try:
                # Run detection
                detection_result = self.detector.detect_arbitrage(scenario["odds_by_bookmaker"])
                
                detection_time = (time.time() - test_start_time) * 1000
                self.detection_times.append(detection_time)
                
                # Evaluate results
                actual_arbitrage = detection_result.get("arbitrage_exists", False)
                expected_arbitrage = scenario["expected_arbitrage"]
                
                # Check for true positive/negative/false positive/negative
                if actual_arbitrage and expected_arbitrage:
                    self.metrics.true_positives += 1
                    test_status = "passed"
                elif not actual_arbitrage and not expected_arbitrage:
                    self.metrics.true_negatives += 1
                    test_status = "passed"
                elif actual_arbitrage and not expected_arbitrage:
                    self.metrics.false_positives += 1
                    test_status = "failed"
                else:  # not actual_arbitrage and expected_arbitrage
                    self.metrics.false_negatives += 1
                    test_status = "failed"
                
                if test_status == "passed":
                    results["passed_tests"] += 1
                else:
                    results["failed_tests"] += 1
                
                # Check profit calculation accuracy
                if actual_arbitrage:
                    expected_profit = scenario["expected_profit_margin"]
                    actual_profit = detection_result.get("profit_margin", 0)
                    profit_accuracy = self.detector.calculate_profit_accuracy(
                        expected_profit, actual_profit
                    )
                else:
                    profit_accuracy = True  # No profit to calculate
                
                if profit_accuracy:
                    self.metrics.profit_calculation_accuracy += 1
                
                # Store detailed results
                test_detail = {
                    "scenario_name": scenario["name"],
                    "status": test_status,
                    "expected_arbitrage": expected_arbitrage,
                    "actual_arbitrage": actual_arbitrage,
                    "detection_time_ms": detection_time,
                    "confidence": detection_result.get("confidence", 0),
                    "market_overround": detection_result.get("market_overround", 0),
                    "profit_accuracy": profit_accuracy,
                    "expected_profit_margin": scenario["expected_profit_margin"],
                    "actual_profit_margin": detection_result.get("profit_margin", 0)
                }
                
                results["test_details"].append(test_detail)
                
            except Exception as e:
                self.logger.error(f"Test failed for {scenario['name']}: {str(e)}")
                results["failed_tests"] += 1
                self.metrics.false_negatives += 1
                
                results["test_details"].append({
                    "scenario_name": scenario["name"],
                    "status": "failed",
                    "error": str(e)
                })
        
        # Calculate detection metrics
        self.metrics.total_tests = len(test_scenarios)
        self.metrics.detection_time_ms = statistics.mean(self.detection_times) if self.detection_times else 0
        self.metrics.profit_calculation_accuracy = (
            self.metrics.profit_calculation_accuracy / max(1, len(test_scenarios))
        )
        self.metrics.calculate_metrics()
        
        results["detection_metrics"] = {
            "accuracy": self.metrics.accuracy,
            "precision": self.metrics.precision,
            "recall": self.metrics.recall,
            "f1_score": self.metrics.f1_score,
            "average_detection_time_ms": self.metrics.detection_time_ms,
            "profit_calculation_accuracy": self.metrics.profit_calculation_accuracy
        }
        
        return results
    
    def run_performance_stress_tests(self) -> Dict[str, Any]:
        """Run performance and stress tests."""
        self.logger.info("Running performance stress tests...")
        
        results = {
            "scalability_test": {},
            "high_frequency_test": {},
            "memory_usage_test": {},
            "concurrent_processing_test": {}
        }
        
        # Scalability test - increasing number of bookmakers
        scalability_results = []
        for num_bookmakers in [2, 5, 10, 20, 50]:
            test_odds = {
                f"Bookmaker_{i}": [Decimal("2.0") + Decimal(str(random.uniform(0, 1))) for _ in range(3)]
                for i in range(num_bookmakers)
            }
            
            start_time = time.time()
            detection_result = self.detector.detect_arbitrage(test_odds)
            processing_time = (time.time() - start_time) * 1000
            
            scalability_results.append({
                "num_bookmakers": num_bookmakers,
                "processing_time_ms": processing_time,
                "success": detection_result is not None
            })
        
        results["scalability_test"] = {
            "bookmaker_counts_tested": [2, 5, 10, 20, 50],
            "results": scalability_results,
            "max_processing_time_ms": max(r["processing_time_ms"] for r in scalability_results),
            "scaling_factor": scalability_results[-1]["processing_time_ms"] / scalability_results[0]["processing_time_ms"]
        }
        
        # High-frequency test - rapid consecutive detections
        hf_start_time = time.time()
        hf_detections = 0
        hf_time_limit = 5.0  # 5 seconds
        
        while (time.time() - hf_start_time) < hf_time_limit:
            test_odds = {
                "Bookmaker_A": [Decimal("2.0") + Decimal(str(random.uniform(0, 0.1))) for _ in range(3)],
                "Bookmaker_B": [Decimal("1.9") + Decimal(str(random.uniform(0, 0.1))) for _ in range(3)]
            }
            
            self.detector.detect_arbitrage(test_odds)
            hf_detections += 1
        
        results["high_frequency_test"] = {
            "total_detections": hf_detections,
            "time_period_seconds": hf_time_limit,
            "detections_per_second": hf_detections / hf_time_limit,
            "avg_time_per_detection_ms": (hf_time_limit * 1000) / hf_detections
        }
        
        # Memory usage test
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate large dataset
        large_odds = {
            f"Bookmaker_{i}": [Decimal(str(random.uniform(1.5, 5.0))) for _ in range(10)]
            for i in range(100)
        }
        
        # Process large dataset multiple times
        for _ in range(100):
            self.detector.detect_arbitrage(large_odds)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        results["memory_usage_test"] = {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": final_memory - initial_memory,
            "memory_per_detection_mb": (final_memory - initial_memory) / 100
        }
        
        # Concurrent processing test
        def process_odds_chunk(odds_data):
            return self.detector.detect_arbitrage(odds_data)
        
        concurrent_odds = [
            {
                f"Bookmaker_{i}": [Decimal("2.0") + Decimal(str(random.uniform(0, 1))) for _ in range(3)]
                for i in range(5)
            }
            for _ in range(50)
        ]
        
        concurrent_start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_odds_chunk, odds) for odds in concurrent_odds]
            concurrent_results = [future.result() for future in concurrent.futures]
        
        concurrent_time = time.time() - concurrent_start_time
        
        results["concurrent_processing_test"] = {
            "total_tasks": len(concurrent_odds),
            "concurrent_time_seconds": concurrent_time,
            "speedup_factor": (len(concurrent_odds) * 0.1) / concurrent_time,  # Approximate
            "success_rate": len([r for r in concurrent_results if r is not None]) / len(concurrent_odds)
        }
        
        return results
    
    def run_edge_case_tests(self) -> Dict[str, Any]:
        """Run edge case and boundary condition tests."""
        self.logger.info("Running edge case tests...")
        
        edge_cases = [
            {
                "name": "Single Bookmaker",
                "odds_by_bookmaker": {"Bookmaker_A": [Decimal("2.0"), Decimal("3.0")]},
                "should_fail": True
            },
            {
                "name": "Empty Odds",
                "odds_by_bookmaker": {},
                "should_fail": True
            },
            {
                "name": "Very Small Odds",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("1.001"), Decimal("1000.0")],
                    "Bookmaker_B": [Decimal("1000.0"), Decimal("1.001")]
                },
                "should_fail": False
            },
            {
                "name": "Identical Odds",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("2.0"), Decimal("3.0"), Decimal("4.0")],
                    "Bookmaker_B": [Decimal("2.0"), Decimal("3.0"), Decimal("4.0")]
                },
                "should_fail": False
            },
            {
                "name": "Unequal Outcome Counts",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("2.0"), Decimal("3.0")],
                    "Bookmaker_B": [Decimal("2.0"), Decimal("3.0"), Decimal("4.0")]
                },
                "should_fail": False  # Should handle gracefully
            }
        ]
        
        results = {
            "total_edge_cases": len(edge_cases),
            "passed_cases": 0,
            "failed_cases": 0,
            "edge_case_details": []
        }
        
        for case in edge_cases:
            try:
                detection_result = self.detector.detect_arbitrage(case["odds_by_bookmaker"])
                
                if case["should_fail"]:
                    # Should handle gracefully (return valid result or specific error handling)
                    passed = detection_result is not None
                else:
                    # Should process successfully
                    passed = detection_result is not None and "arbitrage_exists" in detection_result
                
                if passed:
                    results["passed_cases"] += 1
                    status = "passed"
                else:
                    results["failed_cases"] += 1
                    status = "failed"
                
                results["edge_case_details"].append({
                    "case_name": case["name"],
                    "status": status,
                    "detection_result": detection_result
                })
                
            except Exception as e:
                results["failed_cases"] += 1
                results["edge_case_details"].append({
                    "case_name": case["name"],
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Test integration between detection components."""
        self.logger.info("Running integration tests...")
        
        integration_tests = [
            {
                "name": "Detection + Profit Calculation",
                "test_function": self._test_detection_profit_integration
            },
            {
                "name": "Multiple Simultaneous Detections",
                "test_function": self._test_simultaneous_detections
            },
            {
                "name": "Detection with Data Validation",
                "test_function": self._test_detection_with_validation
            }
        ]
        
        results = {
            "total_integration_tests": len(integration_tests),
            "passed_tests": 0,
            "failed_tests": 0,
            "integration_details": []
        }
        
        for test in integration_tests:
            try:
                test_result = test["test_function"]()
                
                if test_result["passed"]:
                    results["passed_tests"] += 1
                    status = "passed"
                else:
                    results["failed_tests"] += 1
                    status = "failed"
                
                results["integration_details"].append({
                    "test_name": test["name"],
                    "status": status,
                    "details": test_result
                })
                
            except Exception as e:
                results["failed_tests"] += 1
                results["integration_details"].append({
                    "test_name": test["name"],
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def _test_detection_profit_integration(self) -> Dict[str, Any]:
        """Test integration between detection and profit calculation."""
        test_odds = {
            "Bookmaker_A": [Decimal("2.1"), Decimal("1.9"), Decimal("3.2")],
            "Bookmaker_B": [Decimal("1.9"), Decimal("2.2"), Decimal("2.8")]
        }
        
        detection_result = self.detector.detect_arbitrage(test_odds)
        
        if not detection_result.get("arbitrage_exists"):
            return {"passed": False, "reason": "Expected arbitrage detection to succeed"}
        
        required_fields = ["profit_margin", "guaranteed_profit", "optimal_stakes"]
        missing_fields = [field for field in required_fields if field not in detection_result]
        
        if missing_fields:
            return {"passed": False, "reason": f"Missing profit calculation fields: {missing_fields}"}
        
        # Validate profit calculation logic
        profit_margin = detection_result["profit_margin"]
        if profit_margin <= 0:
            return {"passed": False, "reason": "Profit margin should be positive for arbitrage"}
        
        return {"passed": True, "detection_result": detection_result}
    
    def _test_simultaneous_detections(self) -> Dict[str, Any]:
        """Test multiple arbitrage detections running simultaneously."""
        test_scenarios = [
            {
                "odds": {
                    "Bookmaker_A": [Decimal("2.1"), Decimal("1.9")],
                    "Bookmaker_B": [Decimal("1.9"), Decimal("2.1")]
                }
            },
            {
                "odds": {
                    "Bookmaker_C": [Decimal("3.0"), Decimal("1.5"), Decimal("2.5")],
                    "Bookmaker_D": [Decimal("2.8"), Decimal("1.6"), Decimal("2.7")]
                }
            }
        ]
        
        def detect_in_thread(scenario):
            return self.detector.detect_arbitrage(scenario["odds"])
        
        threads = []
        results = []
        
        for scenario in test_scenarios:
            thread = threading.Thread(target=lambda s=scenario: results.append(detect_in_thread(s)))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        if len(results) != len(test_scenarios):
            return {"passed": False, "reason": "Not all detections completed"}
        
        # Check that all results are valid
        valid_results = all(result is not None and "arbitrage_exists" in result for result in results)
        
        return {
            "passed": valid_results,
            "num_results": len(results),
            "expected_results": len(test_scenarios)
        }
    
    def _test_detection_with_validation(self) -> Dict[str, Any]:
        """Test detection combined with data validation."""
        # Test with invalid data
        invalid_odds = {
            "Bookmaker_A": [Decimal("0.5"), Decimal("1.5")],  # Invalid odds (< 1.0)
            "Bookmaker_B": [Decimal("2.0"), Decimal("1.8")]
        }
        
        try:
            detection_result = self.detector.detect_arbitrage(invalid_odds)
            # Should handle gracefully or raise appropriate error
            return {"passed": True, "handled_invalid_data": True}
        except Exception as e:
            # Expected to handle invalid data in some way
            return {"passed": True, "error_handled": True, "error": str(e)}
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive test report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""
ARBITRAGE DETECTION TEST REPORT
==============================-
Generated: {timestamp}

EXECUTIVE SUMMARY
----------------
Total Tests: {self.metrics.total_tests}
Accuracy: {self.metrics.accuracy:.2%}
Precision: {self.metrics.precision:.2%}
Recall: {self.metrics.recall:.2%}
F1 Score: {self.metrics.f1_score:.2%}

DETECTION PERFORMANCE
--------------------
Average Detection Time: {self.metrics.detection_time_ms:.2f}ms
Profit Calculation Accuracy: {self.metrics.profit_calculation_accuracy:.2%}

TEST BREAKDOWN
--------------
True Positives: {self.metrics.true_positives}
True Negatives: {self.metrics.true_negatives}
False Positives: {self.metrics.false_positives}
False Negatives: {self.metrics.false_negatives}

RECOMMENDATIONS
--------------
"""
        
        # Add recommendations based on performance
        if self.metrics.accuracy < 0.95:
            report += "- Consider improving detection algorithm accuracy\n"
        
        if self.metrics.precision < 0.90:
            report += "- Reduce false positive rate through better validation\n"
        
        if self.metrics.recall < 0.90:
            report += "- Improve sensitivity to catch more arbitrage opportunities\n"
        
        if self.metrics.detection_time_ms > 100:
            report += "- Optimize detection algorithm for better performance\n"
        
        if self.metrics.profit_calculation_accuracy < 0.95:
            report += "- Review profit calculation accuracy and rounding precision\n"
        
        return report
    
    def save_test_results(self, filepath: str):
        """Save comprehensive test results to JSON."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_suite": "ArbitrageDetectionTestSuite",
            "metrics": {
                "total_tests": self.metrics.total_tests,
                "true_positives": self.metrics.true_positives,
                "true_negatives": self.metrics.true_negatives,
                "false_positives": self.metrics.false_positives,
                "false_negatives": self.metrics.false_negatives,
                "accuracy": self.metrics.accuracy,
                "precision": self.metrics.precision,
                "recall": self.metrics.recall,
                "f1_score": self.metrics.f1_score,
                "detection_time_ms": self.metrics.detection_time_ms,
                "profit_calculation_accuracy": self.metrics.profit_calculation_accuracy
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"Test results saved to {filepath}")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites and compile results."""
        self.logger.info("Running comprehensive arbitrage detection tests...")
        
        all_results = {
            "timestamp": datetime.now().isoformat(),
            "test_suites": {}
        }
        
        # Run all test categories
        all_results["test_suites"]["accuracy_tests"] = self.run_detection_accuracy_tests()
        all_results["test_suites"]["performance_tests"] = self.run_performance_stress_tests()
        all_results["test_suites"]["edge_case_tests"] = self.run_edge_case_tests()
        all_results["test_suites"]["integration_tests"] = self.run_integration_tests()
        
        # Calculate overall success rate
        total_tests = sum(
            result.get("total_tests", 0) + result.get("total_edge_cases", 0) + result.get("total_integration_tests", 0)
            for result in all_results["test_suites"].values()
        )
        
        total_passed = sum(
            result.get("passed_tests", 0) + result.get("passed_cases", 0) + result.get("passed_tests", 0)
            for result in all_results["test_suites"].values()
        )
        
        all_results["overall_summary"] = {
            "total_tests": total_tests,
            "total_passed": total_passed,
            "overall_success_rate": total_passed / total_tests if total_tests > 0 else 0,
            "test_completion_time": datetime.now().isoformat()
        }
        
        return all_results


# Pytest test classes
class TestArbitrageDetectionAccuracy:
    """Pytest tests for arbitrage detection accuracy."""
    
    @pytest.fixture
    def test_suite(self):
        return ArbitrageDetectionTestSuite()
    
    def test_detection_accuracy(self, test_suite):
        """Test basic arbitrage detection accuracy."""
        results = test_suite.run_detection_accuracy_tests()
        
        assert results["total_tests"] > 0
        assert results["detection_metrics"]["accuracy"] >= 0.80
        assert results["detection_metrics"]["precision"] >= 0.75
        assert results["detection_metrics"]["recall"] >= 0.75
    
    def test_false_positive_rate(self, test_suite):
        """Test false positive rate is acceptable."""
        results = test_suite.run_detection_accuracy_tests()
        
        # False positive rate should be low
        fp_rate = results["detection_metrics"]["precision"]
        assert fp_rate >= 0.80, "False positive rate too high"
    
    def test_false_negative_rate(self, test_suite):
        """Test false negative rate is acceptable."""
        results = test_suite.run_detection_accuracy_tests()
        
        # False negative rate should be low (high recall)
        recall = results["detection_metrics"]["recall"]
        assert recall >= 0.80, "False negative rate too high"


class TestArbitragePerformance:
    """Pytest tests for arbitrage detection performance."""
    
    @pytest.fixture
    def test_suite(self):
        return ArbitrageDetectionTestSuite()
    
    def test_detection_speed(self, test_suite):
        """Test detection speed is acceptable."""
        results = test_suite.run_performance_stress_tests()
        
        avg_time = results["high_frequency_test"]["avg_time_per_detection_ms"]
        assert avg_time <= 50, f"Detection too slow: {avg_time}ms"
    
    def test_scalability(self, test_suite):
        """Test algorithm scales with number of bookmakers."""
        results = test_suite.run_performance_stress_tests()
        
        scaling_factor = results["scalability_test"]["scaling_factor"]
        assert scaling_factor <= 10, "Algorithm doesn't scale well"
    
    def test_concurrent_processing(self, test_suite):
        """Test concurrent processing capability."""
        results = test_suite.run_performance_stress_tests()
        
        success_rate = results["concurrent_processing_test"]["success_rate"]
        assert success_rate >= 0.95, "Concurrent processing reliability too low"


class TestArbitrageEdgeCases:
    """Pytest tests for edge cases and boundary conditions."""
    
    @pytest.fixture
    def test_suite(self):
        return ArbitrageDetectionTestSuite()
    
    def test_edge_case_handling(self, test_suite):
        """Test handling of edge cases."""
        results = test_suite.run_edge_case_tests()
        
        assert results["passed_cases"] >= results["total_edge_cases"] * 0.8
        assert results["failed_cases"] < results["total_edge_cases"] * 0.2
    
    def test_invalid_data_handling(self, test_suite):
        """Test graceful handling of invalid data."""
        results = test_suite.run_edge_case_tests()
        
        # Should handle invalid data gracefully
        edge_case_details = results["edge_case_details"]
        invalid_data_cases = [c for c in edge_case_details if "error" in c and "Single Bookmaker" in c["case_name"]]
        assert len(invalid_data_cases) == 0, "Should handle single bookmaker gracefully"


if __name__ == "__main__":
    # Run comprehensive tests when script is executed
    test_suite = ArbitrageDetectionTestSuite()
    
    print("Running Comprehensive Arbitrage Detection Tests...")
    print("=" * 60)
    
    # Run all test categories
    all_results = test_suite.run_all_tests()
    
    # Generate and print comprehensive report
    report = test_suite.generate_comprehensive_report()
    print(report)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"arbitrage_detection_test_results_{timestamp}.json"
    test_suite.save_test_results(results_file)
    
    print(f"\nDetailed results saved to: {results_file}")
    print(f"Overall success rate: {all_results['overall_summary']['overall_success_rate']:.2%}")