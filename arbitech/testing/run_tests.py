#!/usr/bin/env python3
"""
Comprehensive Test Runner for ARBITech System

This script provides a unified interface for running different types of tests
with various configurations and reporting options.

Usage:
    python run_tests.py --mode unit                    # Run unit tests
    python run_tests.py --mode integration             # Run integration tests
    python run_tests.py --mode e2e                     # Run end-to-end tests
    python run_tests.py --mode performance             # Run performance tests
    python run_tests.py --mode stress                  # Run stress tests
    python run_tests.py --mode regression              # Run regression tests
    python run_tests.py --mode full                    # Run all tests
    python run_tests.py --mode ci                      # Run tests for CI/CD
    python run_tests.py --coverage                     # Generate coverage report
    python run_tests.py --benchmark                    # Run benchmarking
"""

import argparse
import sys
import os
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class TestRunner:
    """Comprehensive test runner for ARBITech system."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.testing_dir = project_root / "testing"
        self.test_suite_path = self.testing_dir / "test_suite.py"
        
        # Output directories
        self.output_dir = self.testing_dir / "test_results"
        self.output_dir.mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        print(f"Running: {' '.join(cmd)}")
        start_time = time.time()
        
        result = subprocess.run(
            cmd,
            cwd=cwd or self.project_root,
            capture_output=True,
            text=True
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Command completed in {duration:.2f}s")
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        
        return result
    
    def run_unit_tests(self, 
                      verbose: bool = True,
                      parallel: bool = False,
                      coverage: bool = False) -> bool:
        """Run unit tests."""
        cmd = ["python", "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        
        if parallel:
            cmd.extend(["-n", "auto"])
        
        if coverage:
            cmd.extend([
                "--cov=arbitech",
                "--cov-report=term-missing",
                f"--cov-report=html:{self.output_dir}/htmlcov",
                f"--cov-report=xml:{self.output_dir}/coverage.xml",
                "--cov-fail-under=80"
            ])
        
        cmd.extend([
            str(self.test_suite_path),
            "-m", "unit",
            "--tb=short"
        ])
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_integration_tests(self,
                             verbose: bool = True,
                             coverage: bool = False) -> bool:
        """Run integration tests."""
        cmd = ["python", "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=arbitech",
                "--cov-report=term-missing",
                f"--cov-report=html:{self.output_dir}/htmlcov",
            ])
        
        cmd.extend([
            str(self.test_suite_path),
            "-m", "integration",
            "--tb=short",
            "--timeout=300"
        ])
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_e2e_tests(self, verbose: bool = True) -> bool:
        """Run end-to-end tests."""
        cmd = ["python", "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend([
            str(self.test_suite_path),
            "-m", "e2e",
            "--tb=short",
            "--timeout=600"
        ])
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_performance_tests(self, verbose: bool = True) -> bool:
        """Run performance tests."""
        cmd = ["python", "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend([
            str(self.test_suite_path),
            "-m", "performance",
            "--tb=short",
            "--benchmark-only",
            "--benchmark-sort=mean"
        ])
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_stress_tests(self, verbose: bool = True) -> bool:
        """Run stress tests."""
        cmd = ["python", "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend([
            str(self.test_suite_path),
            "-m", "stress",
            "--tb=short",
            "--timeout=1800",  # 30 minutes
            "-x"  # Stop on first failure
        ])
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_regression_tests(self,
                            baseline_file: Optional[Path] = None,
                            verbose: bool = True) -> bool:
        """Run regression tests."""
        cmd = ["python", "-m", "pytest"]
        
        if verbose:
            cmd.append("-v")
        
        cmd.extend([
            str(self.test_suite_path),
            "-m", "regression",
            "--tb=short",
            "--timeout=300"
        ])
        
        result = self.run_command(cmd)
        
        # Save regression test results
        if result.returncode == 0:
            self.save_regression_results(result.stdout)
        
        return result.returncode == 0
    
    def run_all_tests(self,
                     parallel: bool = True,
                     coverage: bool = True,
                     fail_fast: bool = False) -> bool:
        """Run all tests."""
        cmd = ["python", "-m", "pytest"]
        
        cmd.append("-v")
        
        if parallel:
            cmd.extend(["-n", "auto"])
        
        if coverage:
            cmd.extend([
                "--cov=arbitech",
                "--cov-report=term-missing",
                f"--cov-report=html:{self.output_dir}/htmlcov",
                f"--cov-report=xml:{self.output_dir}/coverage.xml",
                "--cov-fail-under=70"
            ])
        
        if fail_fast:
            cmd.append("-x")
        
        cmd.extend([
            str(self.test_suite_path),
            "--tb=short",
            "--durations=20"
        ])
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def run_ci_tests(self) -> bool:
        """Run tests optimized for CI/CD."""
        cmd = [
            "python", "-m", "pytest",
            "-v",
            "--tb=line",
            "--cov=arbitech",
            "--cov-report=term-missing",
            f"--cov-report=xml:{self.output_dir}/coverage.xml",
            "--cov-fail-under=75",
            "--maxfail=10",
            str(self.test_suite_path)
        ]
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def generate_coverage_report(self) -> bool:
        """Generate detailed coverage report."""
        # Run tests with coverage
        cmd = [
            "python", "-m", "pytest",
            str(self.test_suite_path),
            "--cov=arbitech",
            f"--cov-report=html:{self.output_dir}/htmlcov",
            f"--cov-report=xml:{self.output_dir}/coverage.xml",
            f"--cov-report=json:{self.output_dir}/coverage.json",
            "--cov-fail-under=70"
        ]
        
        result = self.run_command(cmd)
        
        if result.returncode == 0:
            print(f"\nCoverage reports generated:")
            print(f"  HTML: {self.output_dir}/htmlcov/index.html")
            print(f"  XML: {self.output_dir}/coverage.xml")
            print(f"  JSON: {self.output_dir}/coverage.json")
        
        return result.returncode == 0
    
    def run_benchmark(self) -> bool:
        """Run performance benchmarking."""
        cmd = [
            "python", "-m", "pytest",
            str(self.test_suite_path),
            "-m", "performance",
            "--benchmark-only",
            "--benchmark-sort=mean",
            f"--benchmark-json={self.output_dir}/benchmark_results.json",
            "--benchmark-legend=mean,stddev,min,max"
        ]
        
        result = self.run_command(cmd)
        
        if result.returncode == 0:
            print(f"\nBenchmark results saved to:")
            print(f"  JSON: {self.output_dir}/benchmark_results.json")
        
        return result.returncode == 0
    
    def save_regression_results(self, output: str):
        """Save regression test results for comparison."""
        results_file = self.output_dir / f"regression_results_{self.timestamp}.json"
        
        # Parse output and extract key metrics
        results = {
            "timestamp": self.timestamp,
            "output": output,
            "summary": self._parse_test_summary(output)
        }
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Regression results saved to: {results_file}")
    
    def _parse_test_summary(self, output: str) -> Dict[str, Any]:
        """Parse test summary from pytest output."""
        summary = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "duration": 0.0
        }
        
        # Simple parsing - could be enhanced
        lines = output.split('\n')
        for line in lines:
            if 'passed' in line and 'failed' in line:
                # Example: "5 passed, 2 failed in 10.5s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed' and i > 0:
                        summary["passed"] = int(parts[i-1])
                    elif part == 'failed' and i > 0:
                        summary["failed"] = int(parts[i-1])
                    elif part == 'skipped' and i > 0:
                        summary["skipped"] = int(parts[i-1])
        
        summary["total_tests"] = summary["passed"] + summary["failed"] + summary["skipped"]
        
        return summary
    
    def run_specific_test(self, test_pattern: str) -> bool:
        """Run specific test or test pattern."""
        cmd = [
            "python", "-m", "pytest",
            "-v",
            str(self.test_suite_path),
            "-k", test_pattern
        ]
        
        result = self.run_command(cmd)
        return result.returncode == 0
    
    def generate_test_report(self) -> bool:
        """Generate comprehensive test report."""
        report_file = self.output_dir / f"test_report_{self.timestamp}.html"
        
        cmd = [
            "python", "-m", "pytest",
            str(self.test_suite_path),
            "--html", str(report_file),
            "--self-contained-html",
            "--cov=arbitech",
            f"--cov-report=html:{self.output_dir}/htmlcov"
        ]
        
        result = self.run_command(cmd)
        
        if result.returncode == 0:
            print(f"HTML test report generated: {report_file}")
        
        return result.returncode == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Runner for ARBITech System"
    )
    
    parser.add_argument(
        "--mode",
        choices=["unit", "integration", "e2e", "performance", "stress", "regression", "full", "ci"],
        default="unit",
        help="Test mode to run"
    )
    
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmarking"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first failure"
    )
    
    parser.add_argument(
        "--test-pattern",
        help="Run specific test pattern"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Custom output directory"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Project root directory"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner(args.project_root)
    
    # Override output directory if specified
    if args.output_dir:
        runner.output_dir = args.output_dir
        runner.output_dir.mkdir(exist_ok=True)
    
    print(f"ARBITech Test Runner")
    print(f"Project Root: {args.project_root}")
    print(f"Testing Directory: {runner.testing_dir}")
    print(f"Output Directory: {runner.output_dir}")
    print(f"Test Suite: {runner.test_suite_path}")
    print("=" * 60)
    
    # Run selected test mode
    success = False
    
    try:
        if args.mode == "unit":
            success = runner.run_unit_tests(
                verbose=args.verbose,
                parallel=args.parallel,
                coverage=args.coverage
            )
        
        elif args.mode == "integration":
            success = runner.run_integration_tests(
                verbose=args.verbose,
                coverage=args.coverage
            )
        
        elif args.mode == "e2e":
            success = runner.run_e2e_tests(verbose=args.verbose)
        
        elif args.mode == "performance":
            if args.benchmark:
                success = runner.run_benchmark()
            else:
                success = runner.run_performance_tests(verbose=args.verbose)
        
        elif args.mode == "stress":
            success = runner.run_stress_tests(verbose=args.verbose)
        
        elif args.mode == "regression":
            success = runner.run_regression_tests(verbose=args.verbose)
        
        elif args.mode == "full":
            success = runner.run_all_tests(
                parallel=args.parallel,
                coverage=args.coverage,
                fail_fast=args.fail_fast
            )
        
        elif args.mode == "ci":
            success = runner.run_ci_tests()
        
        if args.test_pattern:
            success = runner.run_specific_test(args.test_pattern)
        
        if args.coverage and not args.benchmark:
            success = runner.generate_coverage_report() and success
        
        if not any([args.mode, args.benchmark, args.test_pattern]):
            # Generate report if no specific mode selected
            success = runner.generate_test_report()
    
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)
    
    # Print final summary
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
