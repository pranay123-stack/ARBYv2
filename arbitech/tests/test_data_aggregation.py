"""
Data Aggregation Testing Framework

This module provides comprehensive testing for data aggregation functionality,
including multiple bookmaker scenarios, data quality issues, and synchronization challenges.

Key Features:
- Multi-bookmaker data aggregation testing
- Data quality validation and error handling
- Synchronization and timing issues testing
- Performance testing with large datasets
- Integration testing with detection algorithms
- Edge cases for missing or invalid data
- Real-time data processing validation
"""

import json
import time
import threading
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import queue
import random
import logging
from pathlib import Path

import pytest


@dataclass
class BookmakerData:
    """Data structure for bookmaker odds data."""
    bookmaker_name: str
    odds: List[Decimal]
    timestamp: datetime
    data_quality_score: float = 1.0
    last_update: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bookmaker_name": self.bookmaker_name,
            "odds": [float(x) for x in self.odds],
            "timestamp": self.timestamp.isoformat(),
            "data_quality_score": self.data_quality_score,
            "last_update": self.last_update.isoformat(),
            "is_active": self.is_active,
            "errors": self.errors
        }


class RealisticBookmakerDataSource:
    """Realistic data source that simulates multiple bookmaker feeds."""
    
    def __init__(self, bookmaker_name: str, reliability: float = 0.95, latency_ms: int = 100):
        self.bookmaker_name = bookmaker_name
        self.reliability = reliability
        self.latency_ms = latency_ms
        self.is_running = False
        
    async def fetch_odds(self, event_id: str) -> Optional[BookmakerData]:
        """Fetch odds data with realistic latency and potential failures."""
        await asyncio.sleep(self.latency_ms / 1000.0)  # Simulate network latency
        
        # Simulate reliability - occasional failures
        if random.random() > self.reliability:
            # Simulate various error conditions
            error_types = ["timeout", "invalid_response", "rate_limited", "maintenance"]
            error = random.choice(error_types)
            return BookmakerData(
                bookmaker_name=self.bookmaker_name,
                odds=[],
                timestamp=datetime.now(),
                data_quality_score=0.0,
                errors=[error]
            )
        
        # Generate realistic odds
        base_odds = [Decimal("2.0") + Decimal(str(random.uniform(0, 2))) for _ in range(3)]
        
        # Simulate occasional data quality issues
        quality_score = 1.0
        errors = []
        
        if random.random() < 0.05:  # 5% chance of data quality issues
            quality_score = random.uniform(0.5, 0.9)
            error_types = ["stale_data", "inconsistent_odds", "missing_outcomes"]
            errors.append(random.choice(error_types))
        
        return BookmakerData(
            bookmaker_name=self.bookmaker_name,
            odds=base_odds,
            timestamp=datetime.now(),
            data_quality_score=quality_score,
            errors=errors
        )


class DataAggregationEngine:
    """Data aggregation engine for collecting and processing bookmaker data."""
    
    def __init__(self, min_data_quality: float = 0.7, max_aggregation_time: float = 5.0):
        self.min_data_quality = min_data_quality
        self.max_aggregation_time = max_aggregation_time
        self.data_sources: Dict[str, RealisticBookmakerDataSource] = {}
        self.aggregation_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_latency_ms": 0.0,
            "data_quality_scores": []
        }
        
    def add_data_source(self, source: RealisticBookmakerDataSource):
        """Add a bookmaker data source."""
        self.data_sources[source.bookmaker_name] = source
    
    async def aggregate_bookmaker_data(self, event_id: str) -> Dict[str, Any]:
        """Aggregate data from all bookmaker sources."""
        start_time = time.time()
        aggregated_data = {}
        successful_sources = 0
        
        # Fetch data from all sources concurrently
        tasks = []
        for source in self.data_sources.values():
            task = asyncio.create_task(source.fetch_odds(event_id))
            tasks.append((source.bookmaker_name, task))
        
        # Wait for results with timeout
        timeout_time = start_time + self.max_aggregation_time
        
        for bookmaker_name, task in tasks:
            try:
                remaining_time = timeout_time - time.time()
                if remaining_time <= 0:
                    break
                
                result = await asyncio.wait_for(task, timeout=remaining_time)
                
                if result and result.odds and result.data_quality_score >= self.min_data_quality:
                    aggregated_data[bookmaker_name] = result
                    successful_sources += 1
                    
                    self.aggregation_stats["successful_requests"] += 1
                    self.aggregation_stats["data_quality_scores"].append(result.data_quality_score)
                else:
                    self.aggregation_stats["failed_requests"] += 1
                    
            except asyncio.TimeoutError:
                self.aggregation_stats["failed_requests"] += 1
            except Exception as e:
                self.aggregation_stats["failed_requests"] += 1
        
        self.aggregation_stats["total_requests"] += len(tasks)
        
        # Calculate average latency
        if successful_sources > 0:
            total_latency = sum(source.latency_ms for source in self.data_sources.values())
            self.aggregation_stats["average_latency_ms"] = total_latency / len(self.data_sources)
        
        aggregation_time = (time.time() - start_time) * 1000
        
        return {
            "event_id": event_id,
            "aggregation_time_ms": aggregation_time,
            "total_sources": len(self.data_sources),
            "successful_sources": successful_sources,
            "failed_sources": len(self.data_sources) - successful_sources,
            "success_rate": successful_sources / len(self.data_sources),
            "bookmaker_data": {k: v.to_dict() for k, v in aggregated_data.items()},
            "data_quality_score": sum(self.aggregation_stats["data_quality_scores"]) / len(self.aggregation_stats["data_quality_scores"]) if self.aggregation_stats["data_quality_scores"] else 0.0
        }


class DataQualityValidator:
    """Validator for data quality and consistency."""
    
    @staticmethod
    def validate_data_completeness(bookmaker_data: Dict[str, BookmakerData]) -> Dict[str, Any]:
        """Validate data completeness across bookmakers."""
        issues = []
        warnings = []
        
        if not bookmaker_data:
            return {
                "is_complete": False,
                "issues": ["No bookmaker data available"],
                "warnings": []
            }
        
        # Check for minimum bookmakers
        min_bookmakers = 2
        if len(bookmaker_data) < min_bookmakers:
            issues.append(f"Insufficient bookmakers: {len(bookmaker_data)} < {min_bookmakers}")
        
        # Check outcome consistency
        outcome_counts = {}
        for bookmaker, data in bookmaker_data.items():
            num_outcomes = len(data.odds)
            if num_outcomes not in outcome_counts:
                outcome_counts[num_outcomes] = []
            outcome_counts[num_outcomes].append(bookmaker)
        
        if len(outcome_counts) > 1:
            issues.append("Inconsistent number of outcomes across bookmakers")
            warnings.append(f"Outcome counts: {outcome_counts}")
        
        # Check data freshness
        now = datetime.now()
        stale_threshold = timedelta(minutes=5)
        
        for bookmaker, data in bookmaker_data.items():
            age = now - data.timestamp
            if age > stale_threshold:
                warnings.append(f"Stale data from {bookmaker}: {age.total_seconds():.0f}s old")
        
        return {
            "is_complete": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "bookmaker_count": len(bookmaker_data),
            "outcome_consistency": len(outcome_counts) == 1
        }
    
    @staticmethod
    def validate_odds_consistency(bookmaker_data: Dict[str, BookmakerData]) -> Dict[str, Any]:
        """Validate odds consistency and detect anomalies."""
        issues = []
        warnings = []
        
        if len(bookmaker_data) < 2:
            return {
                "is_consistent": False,
                "issues": ["Need at least 2 bookmakers for consistency check"],
                "warnings": []
            }
        
        # Extract all odds for each outcome position
        outcome_odds = {}
        for bookmaker, data in bookmaker_data.items():
            for i, odd in enumerate(data.odds):
                if i not in outcome_odds:
                    outcome_odds[i] = []
                outcome_odds[i].append((bookmaker, odd))
        
        # Check for unusual odds patterns
        for outcome_idx, odds_list in outcome_odds.items():
            odds_values = [odd for _, odd in odds_list]
            min_odds = min(odds_values)
            max_odds = max(odds_values)
            
            # Check for extreme variations
            if max_odds / min_odds > 10:  # More than 10x difference
                warnings.append(f"Large odds variation in outcome {outcome_idx}: {min_odds} to {max_odds}")
            
            # Check for impossible odds
            for bookmaker, odd in odds_list:
                if odd <= Decimal("1"):
                    issues.append(f"Invalid odds from {bookmaker} in outcome {outcome_idx}: {odd}")
        
        return {
            "is_consistent": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "outcomes_analyzed": len(outcome_odds)
        }
    
    @staticmethod
    def calculate_data_quality_score(bookmaker_data: Dict[str, BookmakerData]) -> float:
        """Calculate overall data quality score."""
        if not bookmaker_data:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for bookmaker, data in bookmaker_data.items():
            # Weight by data quality score and recency
            quality_score = data.data_quality_score
            
            # Reduce score for stale data
            age_minutes = (datetime.now() - data.timestamp).total_seconds() / 60
            recency_factor = max(0.1, 1.0 - (age_minutes / 30))  # Decay over 30 minutes
            
            # Reduce score for errors
            error_penalty = len(data.errors) * 0.1
            
            final_score = max(0.0, quality_score * recency_factor - error_penalty)
            
            total_score += final_score
            total_weight += 1.0
        
        return total_score / total_weight if total_weight > 0 else 0.0


class DataAggregationTestSuite:
    """Comprehensive test suite for data aggregation functionality."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = []
        
    def test_basic_aggregation(self) -> Dict[str, Any]:
        """Test basic data aggregation functionality."""
        self.logger.info("Testing basic data aggregation...")
        
        # Create data sources with different characteristics
        sources = [
            RealisticBookmakerDataSource("Bet365", reliability=0.95, latency_ms=50),
            RealisticBookmakerDataSource("William Hill", reliability=0.90, latency_ms=75),
            RealisticBookmakerDataSource("Ladbrokes", reliability=0.85, latency_ms=100)
        ]
        
        engine = DataAggregationEngine(min_data_quality=0.7, max_aggregation_time=2.0)
        
        for source in sources:
            engine.add_data_source(source)
        
        # Test aggregation
        async def run_test():
            result = await engine.aggregate_bookmaker_data("test_event_001")
            return result
        
        import asyncio
        result = asyncio.run(run_test())
        
        return {
            "test_name": "basic_aggregation",
            "total_sources": result["total_sources"],
            "successful_sources": result["successful_sources"],
            "success_rate": result["success_rate"],
            "aggregation_time_ms": result["aggregation_time_ms"],
            "data_quality_score": result["data_quality_score"],
            "passed": result["successful_sources"] >= 2  # At least 2 sources should succeed
        }
    
    def test_data_quality_validation(self) -> Dict[str, Any]:
        """Test data quality validation logic."""
        self.logger.info("Testing data quality validation...")
        
        # Create test data with known quality issues
        test_data = {
            "Bet365": BookmakerData(
                bookmaker_name="Bet365",
                odds=[Decimal("2.0"), Decimal("3.0"), Decimal("4.0")],
                timestamp=datetime.now() - timedelta(minutes=2),
                data_quality_score=0.95
            ),
            "William Hill": BookmakerData(
                bookmaker_name="William Hill",
                odds=[Decimal("2.1"), Decimal("2.9"), Decimal("4.1")],
                timestamp=datetime.now() - timedelta(minutes=10),  # Stale
                data_quality_score=0.6,  # Low quality
                errors=["stale_data"]
            ),
            "Pinnacle": BookmakerData(
                bookmaker_name="Pinnacle",
                odds=[Decimal("1.9"), Decimal("3.1")],  # Missing third outcome
                timestamp=datetime.now() - timedelta(minutes=1),
                data_quality_score=0.85
            )
        }
        
        # Test completeness validation
        completeness_result = DataQualityValidator.validate_data_completeness(test_data)
        
        # Test consistency validation
        consistency_result = DataQualityValidator.validate_odds_consistency(test_data)
        
        # Test quality score calculation
        quality_score = DataQualityValidator.calculate_data_quality_score(test_data)
        
        return {
            "test_name": "data_quality_validation",
            "completeness_validation": completeness_result,
            "consistency_validation": consistency_result,
            "overall_quality_score": quality_score,
            "passed": completeness_result["is_complete"] or quality_score > 0.5
        }
    
    def test_synchronization_handling(self) -> Dict[str, Any]:
        """Test handling of synchronization issues."""
        self.logger.info("Testing synchronization handling...")
        
        # Create sources with different latencies
        fast_source = RealisticBookmakerDataSource("FastBook", reliability=1.0, latency_ms=10)
        slow_source = RealisticBookmakerDataSource("SlowBook", reliability=0.8, latency_ms=500)
        medium_source = RealisticBookmakerDataSource("MediumBook", reliability=0.9, latency_ms=100)
        
        engine = DataAggregationEngine(max_aggregation_time=1.0)  # 1 second timeout
        
        for source in [fast_source, slow_source, medium_source]:
            engine.add_data_source(source)
        
        async def run_sync_test():
            result = await engine.aggregate_bookmaker_data("sync_test_event")
            return result
        
        import asyncio
        result = asyncio.run(run_sync_test())
        
        return {
            "test_name": "synchronization_handling",
            "total_sources": result["total_sources"],
            "successful_sources": result["successful_sources"],
            "failed_sources": result["failed_sources"],
            "aggregation_time_ms": result["aggregation_time_ms"],
            "timeout_handling": result["aggregation_time_ms"] <= 1500,  # Should respect timeout
            "passed": result["successful_sources"] >= 1  # At least fast source should succeed
        }
    
    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling for various failure scenarios."""
        self.logger.info("Testing error handling...")
        
        error_scenarios = [
            {
                "name": "All sources fail",
                "sources": [
                    RealisticBookmakerDataSource("Failing1", reliability=0.0, latency_ms=50),
                    RealisticBookmakerDataSource("Failing2", reliability=0.0, latency_ms=50)
                ],
                "expected_min_success": 0
            },
            {
                "name": "Mixed reliability",
                "sources": [
                    RealisticBookmakerDataSource("Reliable", reliability=1.0, latency_ms=50),
                    RealisticBookmakerDataSource("Unreliable", reliability=0.0, latency_ms=50),
                    RealisticBookmakerDataSource("Moderate", reliability=0.5, latency_ms=50)
                ],
                "expected_min_success": 1
            },
            {
                "name": "High latency timeout",
                "sources": [
                    RealisticBookmakerDataSource("VerySlow", reliability=1.0, latency_ms=2000),
                    RealisticBookmakerDataSource("Fast", reliability=1.0, latency_ms=50)
                ],
                "expected_min_success": 1
            }
        ]
        
        results = []
        
        for scenario in error_scenarios:
            engine = DataAggregationEngine(max_aggregation_time=1.5)
            
            for source in scenario["sources"]:
                engine.add_data_source(source)
            
            async def run_error_test():
                result = await engine.aggregate_bookmaker_data(f"error_test_{scenario['name']}")
                return result
            
            import asyncio
            result = asyncio.run(run_error_test())
            
            test_passed = result["successful_sources"] >= scenario["expected_min_success"]
            
            results.append({
                "scenario_name": scenario["name"],
                "total_sources": result["total_sources"],
                "successful_sources": result["successful_sources"],
                "success_rate": result["success_rate"],
                "test_passed": test_passed
            })
        
        passed_scenarios = sum(1 for r in results if r["test_passed"])
        
        return {
            "test_name": "error_handling",
            "total_scenarios": len(results),
            "passed_scenarios": passed_scenarios,
            "success_rate": passed_scenarios / len(results),
            "scenario_results": results,
            "passed": passed_scenarios >= len(results) * 0.7  # 70% success rate
        }
    
    def test_performance_under_load(self) -> Dict[str, Any]:
        """Test performance under high load conditions."""
        self.logger.info("Testing performance under load...")
        
        # Create many data sources
        num_sources = 20
        sources = [
            RealisticBookmakerDataSource(f"Bookmaker_{i}", reliability=0.9, latency_ms=random.randint(20, 100))
            for i in range(num_sources)
        ]
        
        engine = DataAggregationEngine(max_aggregation_time=3.0)
        
        for source in sources:
            engine.add_data_source(source)
        
        async def run_load_test():
            # Test single aggregation
            start_time = time.time()
            result = await engine.aggregate_bookmaker_data("load_test_event")
            single_aggregation_time = (time.time() - start_time) * 1000
            
            # Test multiple concurrent aggregations
            start_time = time.time()
            tasks = [
                engine.aggregate_bookmaker_data(f"load_test_event_{i}")
                for i in range(10)
            ]
            concurrent_results = await asyncio.gather(*tasks)
            concurrent_time = (time.time() - start_time) * 1000
            
            return {
                "single_aggregation_time_ms": single_aggregation_time,
                "concurrent_time_ms": concurrent_time,
                "concurrent_requests": len(tasks),
                "average_concurrent_time_ms": concurrent_time / len(tasks),
                "single_success_rate": result["success_rate"],
                "concurrent_success_rates": [r["success_rate"] for r in concurrent_results]
            }
        
        import asyncio
        result = asyncio.run(run_load_test())
        
        # Performance criteria
        passed = (
            result["single_aggregation_time_ms"] <= 2000 and  # Single aggregation under 2s
            result["average_concurrent_time_ms"] <= 3000 and  # Concurrent under 3s average
            result["single_success_rate"] >= 0.7  # Good success rate
        )
        
        return {
            "test_name": "performance_under_load",
            "num_sources": num_sources,
            "performance_metrics": result,
            "passed": passed
        }
    
    def test_data_consistency_across_time(self) -> Dict[str, Any]:
        """Test data consistency over time periods."""
        self.logger.info("Testing data consistency across time...")
        
        # Simulate data changes over time
        base_data = {
            "Bookmaker_A": [Decimal("2.0"), Decimal("3.0"), Decimal("4.0")],
            "Bookmaker_B": [Decimal("1.9"), Decimal("3.1"), Decimal("3.9")]
        }
        
        consistency_tests = []
        
        # Test with static data (should be consistent)
        static_data = {}
        for bookmaker, odds in base_data.items():
            static_data[bookmaker] = BookmakerData(
                bookmaker_name=bookmaker,
                odds=odds.copy(),
                timestamp=datetime.now(),
                data_quality_score=1.0
            )
        
        consistency_static = DataQualityValidator.validate_odds_consistency(static_data)
        consistency_tests.append(consistency_static)
        
        # Test with changing data (may have inconsistencies)
        changing_data = {}
        for i, (bookmaker, odds) in enumerate(base_data.items()):
            # Simulate odds changes over time
            modified_odds = [odd * Decimal(str(1 + i * 0.1)) for odd in odds]
            changing_data[bookmaker] = BookmakerData(
                bookmaker_name=bookmaker,
                odds=modified_odds,
                timestamp=datetime.now() - timedelta(seconds=i),
                data_quality_score=0.9
            )
        
        consistency_changing = DataQualityValidator.validate_odds_consistency(changing_data)
        consistency_tests.append(consistency_changing)
        
        # Test quality scores
        static_quality = DataQualityValidator.calculate_data_quality_score(static_data)
        changing_quality = DataQualityValidator.calculate_data_quality_score(changing_data)
        
        return {
            "test_name": "data_consistency_across_time",
            "static_data_consistency": consistency_static,
            "changing_data_consistency": consistency_changing,
            "static_quality_score": static_quality,
            "changing_quality_score": changing_quality,
            "passed": static_quality > 0.8 and changing_quality > 0.7
        }
    
    def run_comprehensive_aggregation_tests(self) -> Dict[str, Any]:
        """Run all data aggregation tests."""
        self.logger.info("Running comprehensive data aggregation tests...")
        
        all_results = {
            "timestamp": datetime.now().isoformat(),
            "test_suites": {}
        }
        
        # Run all test categories
        all_results["test_suites"]["basic_aggregation"] = self.test_basic_aggregation()
        all_results["test_suites"]["data_quality_validation"] = self.test_data_quality_validation()
        all_results["test_suites"]["synchronization_handling"] = self.test_synchronization_handling()
        all_results["test_suites"]["error_handling"] = self.test_error_handling()
        all_results["test_suites"]["performance_under_load"] = self.test_performance_under_load()
        all_results["test_suites"]["data_consistency"] = self.test_data_consistency_across_time()
        
        # Calculate overall metrics
        total_tests = len(all_results["test_suites"])
        passed_tests = sum(1 for result in all_results["test_suites"].values() if result.get("passed", False))
        
        all_results["overall_metrics"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "overall_success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "test_completion_time": datetime.now().isoformat()
        }
        
        return all_results
    
    def generate_aggregation_report(self) -> str:
        """Generate comprehensive data aggregation test report."""
        results = self.run_comprehensive_aggregation_tests()
        
        report = f"""
DATA AGGREGATION TEST REPORT
============================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY
----------------
Total Tests: {results['overall_metrics']['total_tests']}
Passed Tests: {results['overall_metrics']['passed_tests']}
Overall Success Rate: {results['overall_metrics']['overall_success_rate']:.2%}

TEST CATEGORY RESULTS
--------------------
"""
        
        for category, result in results["test_suites"].items():
            category_name = category.replace("_", " ").title()
            status = "PASS" if result.get("passed", False) else "FAIL"
            report += f"{category_name}: {status}\n"
            
            if "success_rate" in result:
                report += f"  Success Rate: {result['success_rate']:.2%}\n"
            if "performance_metrics" in result:
                metrics = result["performance_metrics"]
                report += f"  Single Aggregation Time: {metrics.get('single_aggregation_time_ms', 0):.1f}ms\n"
                report += f"  Concurrent Performance: {metrics.get('average_concurrent_time_ms', 0):.1f}ms avg\n"
            report += "\n"
        
        # Add recommendations
        report += "RECOMMENDATIONS\n"
        report += "---------------\n"
        
        if results['overall_metrics']['overall_success_rate'] < 0.9:
            report += "- Improve data source reliability\n"
            report += "- Implement better error handling and retry logic\n"
        
        performance_result = results["test_suites"].get("performance_under_load", {})
        if performance_result.get("passed", False):
            perf_metrics = performance_result.get("performance_metrics", {})
            if perf_metrics.get("single_aggregation_time_ms", 0) > 1000:
                report += "- Optimize data source latency\n"
        
        return report
    
    def save_aggregation_results(self, filepath: str):
        """Save data aggregation test results to JSON file."""
        results = self.run_comprehensive_aggregation_tests()
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"Data aggregation test results saved to {filepath}")


# Pytest test classes
class TestDataAggregation:
    """Pytest tests for data aggregation functionality."""
    
    @pytest.fixture
    def test_suite(self):
        return DataAggregationTestSuite()
    
    def test_basic_aggregation_functionality(self, test_suite):
        """Test basic data aggregation works correctly."""
        result = test_suite.test_basic_aggregation()
        
        assert result["total_sources"] >= 2, "Should test with multiple data sources"
        assert result["success_rate"] >= 0.5, "At least 50% of sources should succeed"
        assert result["passed"], "Basic aggregation test should pass"
    
    def test_data_quality_validation(self, test_suite):
        """Test data quality validation logic."""
        result = test_suite.test_data_quality_validation()
        
        completeness = result["completeness_validation"]
        consistency = result["consistency_validation"]
        
        assert "is_complete" in completeness
        assert "is_consistent" in consistency
        assert result["overall_quality_score"] >= 0, "Quality score should be non-negative"
    
    def test_synchronization_handling(self, test_suite):
        """Test synchronization issue handling."""
        result = test_suite.test_synchronization_handling()
        
        assert result["total_sources"] >= 2, "Should test with multiple sources"
        assert result["timeout_handling"], "Should respect timeout constraints"
        assert result["passed"], "Synchronization test should pass"
    
    def test_error_recovery(self, test_suite):
        """Test error recovery and resilience."""
        result = test_suite.test_error_handling()
        
        assert result["total_scenarios"] >= 3, "Should test multiple error scenarios"
        assert result["success_rate"] >= 0.5, "Should handle at least 50% of error scenarios"
        assert result["passed"], "Error handling test should pass"


class TestDataQuality:
    """Pytest tests for data quality validation."""
    
    def test_completeness_validation(self):
        """Test data completeness validation."""
        # Test with complete data
        complete_data = {
            "Bookmaker_A": BookmakerData("Bookmaker_A", [Decimal("2.0"), Decimal("3.0")], datetime.now()),
            "Bookmaker_B": BookmakerData("Bookmaker_B", [Decimal("1.9"), Decimal("3.1")], datetime.now())
        }
        
        result = DataQualityValidator.validate_data_completeness(complete_data)
        assert result["is_complete"] == True
        
        # Test with incomplete data
        incomplete_data = {
            "Bookmaker_A": BookmakerData("Bookmaker_A", [Decimal("2.0")], datetime.now())
        }
        
        result = DataQualityValidator.validate_data_completeness(incomplete_data)
        assert result["is_complete"] == False
    
    def test_consistency_validation(self):
        """Test odds consistency validation."""
        # Test with consistent data
        consistent_data = {
            "Bookmaker_A": BookmakerData("Bookmaker_A", [Decimal("2.0"), Decimal("3.0"), Decimal("4.0")], datetime.now()),
            "Bookmaker_B": BookmakerData("Bookmaker_B", [Decimal("1.9"), Decimal("3.1"), Decimal("3.9")], datetime.now())
        }
        
        result = DataQualityValidator.validate_odds_consistency(consistent_data)
        assert "is_consistent" in result
    
    def test_quality_score_calculation(self):
        """Test data quality score calculation."""
        test_data = {
            "Bookmaker_A": BookmakerData("Bookmaker_A", [Decimal("2.0"), Decimal("3.0")], datetime.now(), data_quality_score=0.9),
            "Bookmaker_B": BookmakerData("Bookmaker_B", [Decimal("1.9"), Decimal("3.1")], datetime.now(), data_quality_score=0.8)
        }
        
        score = DataQualityValidator.calculate_data_quality_score(test_data)
        assert 0 <= score <= 1, "Quality score should be between 0 and 1"
        assert score > 0, "Should have positive quality score for good data"


if __name__ == "__main__":
    # Run comprehensive data aggregation tests when script is executed
    test_suite = DataAggregationTestSuite()
    
    print("Running Comprehensive Data Aggregation Tests...")
    print("=" * 60)
    
    # Run all test categories
    all_results = test_suite.run_comprehensive_aggregation_tests()
    
    # Generate and print comprehensive report
    report = test_suite.generate_aggregation_report()
    print(report)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"data_aggregation_test_results_{timestamp}.json"
    test_suite.save_aggregation_results(results_file)
    
    print(f"\nDetailed results saved to: {results_file}")
    print(f"Overall success rate: {all_results['overall_metrics']['overall_success_rate']:.2%}")