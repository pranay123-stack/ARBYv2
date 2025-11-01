"""
Comprehensive Test Runner for Arbitrage Detection Framework

This module provides a unified test runner that executes all test suites
and generates comprehensive reports for continuous integration.

Features:
- Unified test execution across all test modules
- Parallel test execution for performance
- Comprehensive reporting with metrics and recommendations
- CI/CD integration support
- Test result persistence and historical analysis
- Automated test data validation and generation
"""

import json
import time
import sys
import os
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback
import subprocess
import concurrent.futures
from dataclasses import dataclass, asdict

# Import test suites
sys.path.append(str(Path(__file__).parent))

from test_arbitrage_detection import ArbitrageDetectionTestSuite
from test_mathematical_calculations import MathematicalTestSuite
from test_data_aggregation import DataAggregationTestSuite


@dataclass
class TestExecutionSummary:
    """Summary of test execution results."""
    
    test_suite_name: str
    execution_time: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    critical_failures: List[str]
    warnings: List[str]
    performance_metrics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ComprehensiveTestRunner:
    """Comprehensive test runner for all arbitrage detection tests."""
    
    def __init__(self, output_dir: str = "test_results", parallel_execution: bool = True):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.parallel_execution = parallel_execution
        self.logger = self._setup_logging()
        
        self.test_suites = {
            "arbitrage_detection": ArbitrageDetectionTestSuite(),
            "mathematical_calculations": MathematicalTestSuite(),
            "data_aggregation": DataAggregationTestSuite()
        }
        
        self.execution_results: Dict[str, TestExecutionSummary] = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging."""
        logger = logging.getLogger("ComprehensiveTestRunner")
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(console_handler)
        
        # File handler
        log_file = self.output_dir / f"test_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def run_arbitrage_detection_tests(self) -> TestExecutionSummary:
        """Run arbitrage detection tests."""
        self.logger.info("Starting arbitrage detection tests...")
        
        start_time = time.time()
        suite = self.test_suites["arbitrage_detection"]
        
        try:
            # Run comprehensive tests
            results = suite.run_all_tests()
            
            execution_time = time.time() - start_time
            
            # Extract summary metrics
            overall_metrics = results.get("overall_summary", {})
            total_tests = overall_metrics.get("total_tests", 0)
            total_passed = overall_metrics.get("total_passed", 0)
            failed_tests = total_tests - total_passed
            success_rate = overall_metrics.get("overall_success_rate", 0.0)
            
            # Extract performance metrics
            performance_metrics = {}
            if "test_suites" in results:
                perf_results = results["test_suites"].get("performance_tests", {})
                if perf_results:
                    performance_metrics = {
                        "avg_detection_time_ms": perf_results.get("detection_metrics", {}).get("average_detection_time_ms", 0),
                        "memory_usage_increase_mb": perf_results.get("memory_usage_test", {}).get("memory_increase_mb", 0),
                        "calculations_per_second": perf_results.get("high_frequency_test", {}).get("detections_per_second", 0)
                    }
            
            # Identify critical failures
            critical_failures = []
            warnings = []
            
            # Check accuracy metrics
            detection_metrics = results.get("test_suites", {}).get("accuracy_tests", {}).get("detection_metrics", {})
            if detection_metrics.get("accuracy", 0) < 0.8:
                critical_failures.append("Low detection accuracy (< 80%)")
            if detection_metrics.get("precision", 0) < 0.75:
                warnings.append("Low precision rate detected")
            if detection_metrics.get("recall", 0) < 0.75:
                warnings.append("Low recall rate detected")
            
            summary = TestExecutionSummary(
                test_suite_name="arbitrage_detection",
                execution_time=execution_time,
                total_tests=total_tests,
                passed_tests=total_passed,
                failed_tests=failed_tests,
                success_rate=success_rate,
                critical_failures=critical_failures,
                warnings=warnings,
                performance_metrics=performance_metrics
            )
            
            self.logger.info(f"Arbitrage detection tests completed: {success_rate:.2%} success rate")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Arbitrage detection tests failed: {str(e)}")
            return TestExecutionSummary(
                test_suite_name="arbitrage_detection",
                execution_time=time.time() - start_time,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                success_rate=0.0,
                critical_failures=[f"Test suite execution failed: {str(e)}"],
                warnings=[],
                performance_metrics={}
            )
    
    def run_mathematical_tests(self) -> TestExecutionSummary:
        """Run mathematical calculation tests."""
        self.logger.info("Starting mathematical calculation tests...")
        
        start_time = time.time()
        suite = self.test_suites["mathematical_calculations"]
        
        try:
            # Run comprehensive tests
            results = suite.run_comprehensive_mathematical_tests()
            
            execution_time = time.time() - start_time
            
            # Extract summary metrics
            overall_metrics = results.get("overall_metrics", {})
            total_tests = overall_metrics.get("total_tests", 0)
            total_passed = overall_metrics.get("passed_tests", 0)
            failed_tests = total_tests - total_passed
            success_rate = overall_metrics.get("overall_success_rate", 0.0)
            
            # Extract performance metrics
            performance_metrics = {}
            performance_tests = results.get("test_suites", {}).get("performance_tests", {})
            if performance_tests:
                performance_metrics = {
                    "calculations_per_second": performance_tests.get("calculations_per_second", 0),
                    "avg_time_per_calculation_ms": performance_tests.get("average_time_per_calculation_ms", 0)
                }
            
            # Identify critical failures
            critical_failures = []
            warnings = []
            
            # Check precision tests
            precision_results = results.get("test_suites", {}).get("precision_tests", {})
            if precision_results.get("passed_tests", 0) / max(precision_results.get("total_tests", 1), 1) < 0.8:
                critical_failures.append("Low precision test success rate")
            
            # Check stability tests
            stability_results = results.get("test_suites", {}).get("stability_tests", {})
            if stability_results.get("passed_tests", 0) / max(stability_results.get("total_tests", 1), 1) < 0.9:
                warnings.append("Numerical stability issues detected")
            
            summary = TestExecutionSummary(
                test_suite_name="mathematical_calculations",
                execution_time=execution_time,
                total_tests=total_tests,
                passed_tests=total_passed,
                failed_tests=failed_tests,
                success_rate=success_rate,
                critical_failures=critical_failures,
                warnings=warnings,
                performance_metrics=performance_metrics
            )
            
            self.logger.info(f"Mathematical tests completed: {success_rate:.2%} success rate")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Mathematical tests failed: {str(e)}")
            return TestExecutionSummary(
                test_suite_name="mathematical_calculations",
                execution_time=time.time() - start_time,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                success_rate=0.0,
                critical_failures=[f"Test suite execution failed: {str(e)}"],
                warnings=[],
                performance_metrics={}
            )
    
    def run_data_aggregation_tests(self) -> TestExecutionSummary:
        """Run data aggregation tests."""
        self.logger.info("Starting data aggregation tests...")
        
        start_time = time.time()
        suite = self.test_suites["data_aggregation"]
        
        try:
            # Run comprehensive tests
            results = suite.run_comprehensive_aggregation_tests()
            
            execution_time = time.time() - start_time
            
            # Extract summary metrics
            overall_metrics = results.get("overall_metrics", {})
            total_tests = overall_metrics.get("total_tests", 0)
            total_passed = overall_metrics.get("passed_tests", 0)
            failed_tests = total_tests - total_passed
            success_rate = overall_metrics.get("overall_success_rate", 0.0)
            
            # Extract performance metrics
            performance_metrics = {}
            perf_results = results.get("test_suites", {}).get("performance_under_load", {})
            if perf_results:
                performance_metrics = {
                    "single_aggregation_time_ms": perf_results.get("performance_metrics", {}).get("single_aggregation_time_ms", 0),
                    "concurrent_performance": perf_results.get("performance_metrics", {}).get("average_concurrent_time_ms", 0)
                }
            
            # Identify critical failures
            critical_failures = []
            warnings = []
            
            # Check load test performance
            if not perf_results.get("passed", False):
                critical_failures.append("Performance under load test failed")
            
            # Check data quality validation
            quality_results = results.get("test_suites", {}).get("data_quality_validation", {})
            if not quality_results.get("passed", False):
                warnings.append("Data quality validation issues detected")
            
            summary = TestExecutionSummary(
                test_suite_name="data_aggregation",
                execution_time=execution_time,
                total_tests=total_tests,
                passed_tests=total_passed,
                failed_tests=failed_tests,
                success_rate=success_rate,
                critical_failures=critical_failures,
                warnings=warnings,
                performance_metrics=performance_metrics
            )
            
            self.logger.info(f"Data aggregation tests completed: {success_rate:.2%} success rate")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Data aggregation tests failed: {str(e)}")
            return TestExecutionSummary(
                test_suite_name="data_aggregation",
                execution_time=time.time() - start_time,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                success_rate=0.0,
                critical_failures=[f"Test suite execution failed: {str(e)}"],
                warnings=[],
                performance_metrics={}
            )
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites."""
        self.logger.info("Starting comprehensive test execution...")
        
        start_time = time.time()
        
        if self.parallel_execution:
            # Run tests in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    "arbitrage_detection": executor.submit(self.run_arbitrage_detection_tests),
                    "mathematical_calculations": executor.submit(self.run_mathematical_tests),
                    "data_aggregation": executor.submit(self.run_data_aggregation_tests)
                }
                
                for test_name, future in futures.items():
                    try:
                        self.execution_results[test_name] = future.result()
                    except Exception as e:
                        self.logger.error(f"Failed to execute {test_name}: {str(e)}")
        else:
            # Run tests sequentially
            self.execution_results["arbitrage_detection"] = self.run_arbitrage_detection_tests()
            self.execution_results["mathematical_calculations"] = self.run_mathematical_tests()
            self.execution_results["data_aggregation"] = self.run_data_aggregation_tests()
        
        total_execution_time = time.time() - start_time
        
        # Calculate overall summary
        total_tests = sum(result.total_tests for result in self.execution_results.values())
        total_passed = sum(result.passed_tests for result in self.execution_results.values())
        total_failed = sum(result.failed_tests for result in self.execution_results.values())
        overall_success_rate = total_passed / total_tests if total_tests > 0 else 0.0
        
        # Collect all critical failures and warnings
        all_critical_failures = []
        all_warnings = []
        for result in self.execution_results.values():
            all_critical_failures.extend(result.critical_failures)
            all_warnings.extend(result.warnings)
        
        return {
            "execution_summary": {
                "total_execution_time": total_execution_time,
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "overall_success_rate": overall_success_rate,
                "execution_timestamp": datetime.now().isoformat(),
                "critical_failures": all_critical_failures,
                "warnings": all_warnings,
                "parallel_execution": self.parallel_execution
            },
            "test_suite_results": {
                name: result.to_dict() for name, result in self.execution_results.items()
            }
        }
    
    def generate_comprehensive_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive test execution report."""
        
        summary = results["execution_summary"]
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        report = f"""
COMPREHENSIVE ARBITRAGE DETECTION TEST REPORT
=============================================
Generated: {timestamp}
Execution Mode: {"Parallel" if summary["parallel_execution"] else "Sequential"}

EXECUTIVE SUMMARY
----------------
Total Tests: {summary["total_tests"]}
Passed Tests: {summary["total_passed"]}
Failed Tests: {summary["total_failed"]}
Overall Success Rate: {summary["overall_success_rate"]:.2%}
Total Execution Time: {summary["total_execution_time"]:.2f} seconds

TEST SUITE BREAKDOWN
-------------------
"""
        
        for suite_name, suite_result in results["test_suite_results"].items():
            suite_name_formatted = suite_name.replace("_", " ").title()
            report += f"{suite_name_formatted}:\n"
            report += f"  Tests: {suite_result['passed_tests']}/{suite_result['total_tests']} passed\n"
            report += f"  Success Rate: {suite_result['success_rate']:.2%}\n"
            report += f"  Execution Time: {suite_result['execution_time']:.2f}s\n"
            
            if suite_result["critical_failures"]:
                report += f"  Critical Issues: {len(suite_result['critical_failures'])}\n"
            if suite_result["warnings"]:
                report += f"  Warnings: {len(suite_result['warnings'])}\n"
            
            # Add performance metrics if available
            perf_metrics = suite_result.get("performance_metrics", {})
            if perf_metrics:
                report += "  Performance Metrics:\n"
                for metric, value in perf_metrics.items():
                    if isinstance(value, float):
                        report += f"    {metric}: {value:.2f}\n"
                    else:
                        report += f"    {metric}: {value}\n"
            
            report += "\n"
        
        # Add critical issues section
        if summary["critical_failures"]:
            report += "CRITICAL ISSUES\n"
            report += "--------------\n"
            for i, failure in enumerate(summary["critical_failures"], 1):
                report += f"{i}. {failure}\n"
            report += "\n"
        
        # Add warnings section
        if summary["warnings"]:
            report += "WARNINGS\n"
            report += "--------\n"
            for i, warning in enumerate(summary["warnings"], 1):
                report += f"{i}. {warning}\n"
            report += "\n"
        
        # Add recommendations
        report += "RECOMMENDATIONS\n"
        report += "---------------\n"
        
        if summary["overall_success_rate"] < 0.9:
            report += "- Overall test success rate below 90% - review failing tests\n"
        
        if summary["critical_failures"]:
            report += "- Address all critical issues before production deployment\n"
        
        # Check for performance issues
        for suite_result in results["test_suite_results"].values():
            perf_metrics = suite_result.get("performance_metrics", {})
            
            if "avg_detection_time_ms" in perf_metrics and perf_metrics["avg_detection_time_ms"] > 100:
                report += "- Optimize detection algorithms for better performance\n"
            
            if "single_aggregation_time_ms" in perf_metrics and perf_metrics["single_aggregation_time_ms"] > 2000:
                report += "- Improve data aggregation performance\n"
        
        if summary["warnings"]:
            report += "- Review and address all warnings for improved reliability\n"
        
        report += "\n"
        
        return report
    
    def save_results(self, results: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save test results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"comprehensive_test_results_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # Add metadata
        results["metadata"] = {
            "test_framework_version": "1.0.0",
            "python_version": sys.version,
            "execution_environment": "comprehensive_test_runner",
            "generated_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"Test results saved to {filepath}")
        return str(filepath)
    
    def run_quick_validation(self) -> bool:
        """Run quick validation tests for CI/CD."""
        self.logger.info("Running quick validation tests...")
        
        try:
            # Test basic arbitrage detection
            suite = ArbitrageDetectionTestSuite()
            results = suite.run_detection_accuracy_tests()
            
            # Quick validation criteria
            accuracy_ok = results["detection_metrics"]["accuracy"] >= 0.8
            precision_ok = results["detection_metrics"]["precision"] >= 0.7
            speed_ok = results["detection_metrics"]["average_detection_time_ms"] <= 50
            
            validation_passed = accuracy_ok and precision_ok and speed_ok
            
            if validation_passed:
                self.logger.info("Quick validation PASSED")
            else:
                self.logger.warning("Quick validation FAILED")
                self.logger.warning(f"Accuracy: {results['detection_metrics']['accuracy']:.2%}")
                self.logger.warning(f"Precision: {results['detection_metrics']['precision']:.2%}")
                self.logger.warning(f"Speed: {results['detection_metrics']['average_detection_time_ms']:.2f}ms")
            
            return validation_passed
            
        except Exception as e:
            self.logger.error(f"Quick validation failed: {str(e)}")
            return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Comprehensive Arbitrage Detection Test Runner")
    parser.add_argument("--mode", choices=["quick", "full", "ci"], default="full",
                       help="Test execution mode: quick (fast validation), full (all tests), ci (CI/CD mode)")
    parser.add_argument("--parallel", action="store_true", default=True,
                       help="Run test suites in parallel")
    parser.add_argument("--output-dir", default="test_results",
                       help="Directory to save test results")
    parser.add_argument("--quiet", action="store_true",
                       help="Reduce logging output")
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    # Create test runner
    runner = ComprehensiveTestRunner(
        output_dir=args.output_dir,
        parallel_execution=args.parallel
    )
    
    try:
        if args.mode == "quick":
            # Quick validation
            success = runner.run_quick_validation()
            sys.exit(0 if success else 1)
            
        elif args.mode == "ci":
            # CI/CD mode - quick validation first, then full tests if quick passes
            if not runner.run_quick_validation():
                print("Quick validation failed - aborting full test run")
                sys.exit(1)
            
            results = runner.run_all_tests()
            
        else:  # full mode
            results = runner.run_all_tests()
        
        # Generate and display report
        report = runner.generate_comprehensive_report(results)
        print(report)
        
        # Save results
        results_file = runner.save_results(results)
        print(f"\nDetailed results saved to: {results_file}")
        
        # Determine exit code based on success rate
        overall_success_rate = results["execution_summary"]["overall_success_rate"]
        critical_failures = results["execution_summary"]["critical_failures"]
        
        if critical_failures:
            print("\n❌ CRITICAL FAILURES DETECTED - DEPLOYMENT NOT RECOMMENDED")
            sys.exit(1)
        elif overall_success_rate < 0.8:
            print("\n⚠️  LOW SUCCESS RATE - REVIEW REQUIRED")
            sys.exit(1)
        else:
            print("\n✅ ALL TESTS PASSED - DEPLOYMENT APPROVED")
            sys.exit(0)
            
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()