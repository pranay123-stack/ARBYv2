#!/usr/bin/env python3
"""
VLM Testing Framework Runner

Comprehensive runner for all VLM accuracy tests with detailed reporting and analysis.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from arbitech.tests.test_vlm_accuracy import VLMAccuracyTestSuite
from arbitech.tests.test_bookmaker_specific import BookmakerVLMTester
from arbitech.tests.test_odds_validation import OddsValidationTestSuite
from arbitech.tests.create_sample_data.data_provider import SampleDataProvider


class VLMTestRunner:
    """Comprehensive test runner for all VLM testing components."""
    
    def __init__(self, output_dir: Path = None):
        """Initialize the test runner.
        
        Args:
            output_dir: Directory to save test results and reports
        """
        self.output_dir = output_dir or Path("vlm_test_results")
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up logging
        self.logger = self._setup_logging()
        
        # Initialize test suites
        self.vlm_test_suite = VLMAccuracyTestSuite()
        self.bookmaker_tester = BookmakerVLMTester()
        self.odds_validator = OddsValidationTestSuite()
        self.data_provider = SampleDataProvider()
        
        # Results storage
        self.all_results = {}
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the test runner."""
        logger = logging.getLogger("VLMTestRunner")
        logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file = self.output_dir / "test_runner.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def run_all_tests(self, 
                     include_performance: bool = True,
                     include_bookmaker_specific: bool = True,
                     include_odds_validation: bool = True) -> Dict[str, Any]:
        """Run all VLM tests comprehensively.
        
        Args:
            include_performance: Whether to include performance benchmarks
            include_bookmaker_specific: Whether to run bookmaker-specific tests
            include_odds_validation: Whether to run odds validation tests
            
        Returns:
            Dictionary containing all test results
        """
        self.logger.info("Starting comprehensive VLM test suite")
        start_time = datetime.now()
        
        # Initialize results structure
        results = {
            "test_run_info": {
                "start_time": start_time.isoformat(),
                "test_configuration": {
                    "include_performance": include_performance,
                    "include_bookmaker_specific": include_bookmaker_specific,
                    "include_odds_validation": include_odds_validation
                }
            },
            "data_validation": {},
            "vlm_accuracy_results": {},
            "bookmaker_specific_results": {},
            "odds_validation_results": {},
            "performance_results": {},
            "overall_summary": {}
        }
        
        try:
            # 1. Validate sample data
            self.logger.info("Validating sample data...")
            data_validation = self.data_provider.validate_sample_data()
            results["data_validation"] = data_validation
            
            if not data_validation["is_valid"]:
                self.logger.error("Sample data validation failed")
                for issue in data_validation["issues"]:
                    self.logger.error(f"Data issue: {issue}")
                    
            # 2. Run VLM accuracy tests
            self.logger.info("Running VLM accuracy tests...")
            results["vlm_accuracy_results"] = self._run_vlm_accuracy_tests()
            
            # 3. Run bookmaker-specific tests if enabled
            if include_bookmaker_specific:
                self.logger.info("Running bookmaker-specific tests...")
                results["bookmaker_specific_results"] = self._run_bookmaker_specific_tests()
            else:
                self.logger.info("Skipping bookmaker-specific tests")
                
            # 4. Run odds validation tests if enabled
            if include_odds_validation:
                self.logger.info("Running odds validation tests...")
                results["odds_validation_results"] = self._run_odds_validation_tests()
            else:
                self.logger.info("Skipping odds validation tests")
                
            # 5. Run performance tests if enabled
            if include_performance:
                self.logger.info("Running performance benchmarks...")
                results["performance_results"] = self._run_performance_benchmarks()
            else:
                self.logger.info("Skipping performance benchmarks")
                
            # 6. Generate overall summary
            end_time = datetime.now()
            results["test_run_info"]["end_time"] = end_time.isoformat()
            results["test_run_info"]["duration_seconds"] = (end_time - start_time).total_seconds()
            
            results["overall_summary"] = self._generate_overall_summary(results)
            
            self.logger.info(f"Test suite completed in {results['test_run_info']['duration_seconds']:.1f} seconds")
            
        except Exception as e:
            self.logger.error(f"Error running test suite: {e}")
            results["error"] = str(e)
            results["test_run_info"]["end_time"] = datetime.now().isoformat()
            
        return results
        
    def _run_vlm_accuracy_tests(self) -> Dict[str, Any]:
        """Run VLM accuracy tests."""
        try:
            # Run basic accuracy tests
            accuracy_results = self.vlm_test_suite.run_basic_accuracy_tests()
            
            # Run edge case tests
            edge_case_results = self.vlm_test_suite.run_edge_case_tests()
            
            # Run integration tests
            integration_results = self.vlm_test_suite.run_integration_tests()
            
            return {
                "accuracy_tests": accuracy_results,
                "edge_case_tests": edge_case_results,
                "integration_tests": integration_results,
                "test_completed": True
            }
            
        except Exception as e:
            self.logger.error(f"Error in VLM accuracy tests: {e}")
            return {
                "error": str(e),
                "test_completed": False
            }
            
    def _run_bookmaker_specific_tests(self) -> Dict[str, Any]:
        """Run bookmaker-specific tests."""
        try:
            # Test all bookmakers
            bookmaker_results = self.bookmaker_tester.test_all_bookmakers()
            
            # Run cross-bookmaker comparison
            comparison_results = self.bookmaker_tester.test_cross_bookmaker_comparison()
            
            return {
                "individual_bookmaker_results": bookmaker_results,
                "cross_bookmaker_comparison": comparison_results,
                "test_completed": True
            }
            
        except Exception as e:
            self.logger.error(f"Error in bookmaker-specific tests: {e}")
            return {
                "error": str(e),
                "test_completed": False
            }
            
    def _run_odds_validation_tests(self) -> Dict[str, Any]:
        """Run odds validation tests."""
        try:
            # Run comprehensive validation tests
            validation_results = self.odds_validator.run_comprehensive_validation_tests()
            
            return {
                "validation_results": validation_results,
                "test_completed": True
            }
            
        except Exception as e:
            self.logger.error(f"Error in odds validation tests: {e}")
            return {
                "error": str(e),
                "test_completed": False
            }
            
    def _run_performance_benchmarks(self) -> Dict[str, Any]:
        """Run performance benchmarks."""
        try:
            # Run VLM performance tests
            vlm_performance = self.vlm_test_suite.run_performance_benchmarks()
            
            # Calculate additional performance metrics
            performance_metrics = {
                "vlm_processing_performance": vlm_performance,
                "test_efficiency": {
                    "tests_per_second": vlm_performance.get("tests_per_second", 0),
                    "average_test_time_ms": vlm_performance.get("average_time_per_test_ms", 0)
                }
            }
            
            return {
                "performance_metrics": performance_metrics,
                "test_completed": True
            }
            
        except Exception as e:
            self.logger.error(f"Error in performance benchmarks: {e}")
            return {
                "error": str(e),
                "test_completed": False
            }
            
    def _generate_overall_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall test summary."""
        summary = {
            "test_success_rate": 0.0,
            "key_metrics": {},
            "recommendations": [],
            "critical_issues": []
        }
        
        # Count successful test suites
        successful_suites = 0
        total_suites = 4  # data validation, vlm accuracy, bookmaker specific, odds validation
        
        # Check data validation
        if results["data_validation"].get("is_valid", False):
            successful_suites += 1
        else:
            summary["critical_issues"].append("Sample data validation failed")
            
        # Check VLM accuracy tests
        if results["vlm_accuracy_results"].get("test_completed", False):
            successful_suites += 1
            accuracy = results["vlm_accuracy_results"]["accuracy_tests"].get("overall_accuracy", 0)
            summary["key_metrics"]["vlm_accuracy"] = accuracy
            if accuracy < 0.8:
                summary["recommendations"].append("VLM accuracy below 80% - consider model retraining")
        else:
            summary["critical_issues"].append("VLM accuracy tests failed")
            
        # Check bookmaker-specific tests
        if results["bookmaker_specific_results"].get("test_completed", False):
            successful_suites += 1
        else:
            summary["recommendations"].append("Bookmaker-specific tests failed - check test setup")
            
        # Check odds validation tests
        if results["odds_validation_results"].get("test_completed", False):
            successful_suites += 1
            validation_success = results["odds_validation_results"]["validation_results"]["overall_metrics"]["overall_success_rate"]
            summary["key_metrics"]["validation_success_rate"] = validation_success
            if validation_success < 0.9:
                summary["recommendations"].append("Validation tests show issues - check odds extraction logic")
        else:
            summary["critical_issues"].append("Odds validation tests failed")
            
        # Calculate overall success rate
        summary["test_success_rate"] = successful_suites / total_suites
        
        # Add performance metrics if available
        if results.get("performance_results", {}).get("test_completed", False):
            perf = results["performance_results"]["performance_metrics"]["test_efficiency"]
            summary["key_metrics"]["test_throughput"] = perf.get("tests_per_second", 0)
            
        # Generate recommendations based on results
        if not summary["critical_issues"]:
            summary["recommendations"].append("All tests passed successfully - VLM testing framework is working correctly")
            
        if summary["key_metrics"].get("vlm_accuracy", 1.0) > 0.9:
            summary["recommendations"].append("Excellent VLM performance - consider deploying to production")
            
        return summary
        
    def generate_comprehensive_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive test report."""
        report = f"""
VLM Testing Framework - Comprehensive Test Report
================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

TEST RUN INFORMATION
-------------------
Start Time: {results['test_run_info']['start_time']}
End Time: {results['test_run_info']['end_time']}
Duration: {results['test_run_info']['duration_seconds']:.1f} seconds

Configuration:
- Performance Tests: {results['test_run_info']['test_configuration']['include_performance']}
- Bookmaker-Specific Tests: {results['test_run_info']['test_configuration']['include_bookmaker_specific']}
- Odds Validation Tests: {results['test_run_info']['test_configuration']['include_odds_validation']}

DATA VALIDATION RESULTS
----------------------
Status: {'PASS' if results['data_validation'].get('is_valid', False) else 'FAIL'}
Total Images: {results['data_validation']['statistics'].get('total_images', 0)}
Ground Truth Coverage: {results['data_validation']['statistics']['ground_truth_coverage'].get('coverage_rate', 0):.2%}

"""
        
        # VLM Accuracy Results
        if results["vlm_accuracy_results"].get("test_completed", False):
            vlm_acc = results["vlm_accuracy_results"]["accuracy_tests"]
            report += f"""VLM ACCURACY TEST RESULTS
-----------------------
Overall Accuracy: {vlm_acc.get('overall_accuracy', 0):.2%}
Odds Extraction Accuracy: {vlm_acc.get('odds_extraction_accuracy', 0):.2%}
Bookmaker Detection Accuracy: {vlm_acc.get('bookmaker_detection_accuracy', 0):.2%}
Total Tests: {vlm_acc.get('total_tests', 0)}

"""
        else:
            report += "VLM ACCURACY TEST RESULTS: FAILED\n\n"
            
        # Bookmaker-Specific Results
        if results["bookmaker_specific_results"].get("test_completed", False):
            comp = results["bookmaker_specific_results"]["cross_bookmaker_comparison"]
            report += f"""BOOKMAKER-SPECIFIC TEST RESULTS
-----------------------------
Average Accuracy: {comp.get('average_accuracy', 0):.2%}
Best Performing: {comp.get('best_performing', 'N/A')}
Worst Performing: {comp.get('worst_performing', 'N/A')}

Accuracy Ranking:
"""
            for i, (bookmaker, accuracy) in enumerate(comp.get("accuracy_ranking", []), 1):
                report += f"  {i}. {bookmaker}: {accuracy:.2%}\n"
            report += "\n"
        else:
            report += "BOOKMAKER-SPECIFIC TEST RESULTS: FAILED\n\n"
            
        # Odds Validation Results
        if results["odds_validation_results"].get("test_completed", False):
            val = results["odds_validation_results"]["validation_results"]["overall_metrics"]
            report += f"""ODDS VALIDATION TEST RESULTS
---------------------------
Total Tests: {val.get('total_tests', 0)}
Passed Tests: {val.get('passed_tests', 0)}
Success Rate: {val.get('overall_success_rate', 0):.2%}

"""
        else:
            report += "ODDS VALIDATION TEST RESULTS: FAILED\n\n"
            
        # Performance Results
        if results.get("performance_results", {}).get("test_completed", False):
            perf = results["performance_results"]["performance_metrics"]["test_efficiency"]
            report += f"""PERFORMANCE BENCHMARK RESULTS
---------------------------
Tests Per Second: {perf.get('tests_per_second', 0):.2f}
Average Test Time: {perf.get('average_test_time_ms', 0):.1f}ms

"""
        else:
            report += "PERFORMANCE BENCHMARK RESULTS: SKIPPED/FAILED\n\n"
            
        # Overall Summary
        summary = results["overall_summary"]
        report += f"""OVERALL SUMMARY
--------------
Test Success Rate: {summary.get('test_success_rate', 0):.2%}

Key Metrics:
"""
        for metric, value in summary.get("key_metrics", {}).items():
            if isinstance(value, float):
                if metric in ["vlm_accuracy", "validation_success_rate"]:
                    report += f"  {metric.replace('_', ' ').title()}: {value:.2%}\n"
                else:
                    report += f"  {metric.replace('_', ' ').title()}: {value:.2f}\n"
            else:
                report += f"  {metric.replace('_', ' ').title()}: {value}\n"
                
        if summary.get("critical_issues"):
            report += "\nCritical Issues:\n"
            for issue in summary["critical_issues"]:
                report += f"  - {issue}\n"
                
        if summary.get("recommendations"):
            report += "\nRecommendations:\n"
            for rec in summary["recommendations"]:
                report += f"  - {rec}\n"
                
        return report
        
    def save_results(self, results: Dict[str, Any], prefix: str = "comprehensive_test"):
        """Save test results to files.
        
        Args:
            results: Test results dictionary
            prefix: Prefix for output files
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON results
        json_file = self.output_dir / f"{prefix}_{timestamp}.json"
        import json
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        self.logger.info(f"JSON results saved to: {json_file}")
        
        # Save text report
        report = self.generate_comprehensive_report(results)
        report_file = self.output_dir / f"{prefix}_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
            
        self.logger.info(f"Text report saved to: {report_file}")
        
        # Also save individual test results
        try:
            self.vlm_test_suite.save_results_to_file(
                str(self.output_dir / f"vlm_accuracy_{timestamp}.json")
            )
            self.bookmaker_tester.save_bookmaker_results(
                str(self.output_dir / f"bookmaker_results_{timestamp}.json")
            )
            self.odds_validator.save_validation_results(
                str(self.output_dir / f"validation_results_{timestamp}.json")
            )
        except Exception as e:
            self.logger.warning(f"Error saving individual results: {e}")
            
        return json_file, report_file


def main():
    """Main function to run the test suite."""
    parser = argparse.ArgumentParser(description="VLM Testing Framework Runner")
    parser.add_argument("--output-dir", type=Path, default=None,
                       help="Directory to save test results")
    parser.add_argument("--skip-performance", action="store_true",
                       help="Skip performance benchmarks")
    parser.add_argument("--skip-bookmaker", action="store_true",
                       help="Skip bookmaker-specific tests")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip odds validation tests")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick test suite (skip performance benchmarks)")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Create test runner
    runner = VLMTestRunner(args.output_dir)
    
    # Configure test options
    include_performance = not (args.skip_performance or args.quick)
    include_bookmaker_specific = not args.skip_bookmaker
    include_odds_validation = not args.skip_validation
    
    print("VLM Testing Framework - Comprehensive Test Runner")
    print("=" * 55)
    print(f"Output Directory: {runner.output_dir}")
    print(f"Include Performance Tests: {include_performance}")
    print(f"Include Bookmaker-Specific Tests: {include_bookmaker_specific}")
    print(f"Include Odds Validation Tests: {include_odds_validation}")
    print()
    
    # Run all tests
    results = runner.run_all_tests(
        include_performance=include_performance,
        include_bookmaker_specific=include_bookmaker_specific,
        include_odds_validation=include_odds_validation
    )
    
    # Generate and display report
    report = runner.generate_comprehensive_report(results)
    print(report)
    
    # Save results
    json_file, report_file = runner.save_results(results)
    
    print(f"\nResults saved:")
    print(f"  JSON: {json_file}")
    print(f"  Report: {report_file}")
    
    # Exit with appropriate code
    summary = results.get("overall_summary", {})
    if summary.get("test_success_rate", 0) >= 0.75 and not summary.get("critical_issues"):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    main()