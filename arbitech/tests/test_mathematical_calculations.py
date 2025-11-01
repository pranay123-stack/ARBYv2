"""
Mathematical Accuracy Testing Framework

This module provides comprehensive testing for mathematical calculations
used in arbitrage detection, including edge cases, boundary conditions,
and precision validation.

Key Features:
- Decimal precision testing with various bit sizes
- Edge cases for probability calculations
- Rounding and precision boundary testing
- Large number arithmetic validation
- Integration testing with detection algorithms
- Performance testing for mathematical operations
"""

import json
import time
from decimal import Decimal, ROUND_HALF_UP, getcontext, localcontext
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import math
import statistics
import logging
import sys

import pytest


class MathematicalArbitrageCalculator:
    """Mathematical calculator for arbitrage operations with configurable precision."""
    
    def __init__(self, precision: int = 28):
        """Initialize calculator with specified precision."""
        self.precision = precision
        getcontext().prec = precision
    
    @staticmethod
    def decimal_to_implied_probability(decimal_odds: Decimal) -> Decimal:
        """Convert decimal odds to implied probability."""
        if decimal_odds <= Decimal("1"):
            raise ValueError("Decimal odds must be greater than 1")
        return Decimal("1") / decimal_odds
    
    @staticmethod
    def implied_probability_to_decimal(probability: Decimal) -> Decimal:
        """Convert implied probability to decimal odds."""
        if probability <= Decimal("0") or probability >= Decimal("1"):
            raise ValueError("Probability must be between 0 and 1 (exclusive)")
        return Decimal("1") / probability
    
    @staticmethod
    def calculate_market_overround(odds: List[Decimal]) -> Decimal:
        """Calculate market overround (sum of implied probabilities)."""
        if not odds:
            return Decimal("0")
        
        total_implied_prob = sum(
            MathematicalArbitrageCalculator.decimal_to_implied_probability(odd) 
            for odd in odds
        )
        return total_implied_prob
    
    @staticmethod
    def calculate_arbitrage_profit(odds: List[Decimal], total_stake: Decimal = Decimal("1000")) -> Dict[str, Any]:
        """Calculate arbitrage profit with optimal stakes."""
        if len(odds) < 2:
            raise ValueError("At least 2 odds required for arbitrage calculation")
        
        # Calculate implied probabilities
        implied_probs = [MathematicalArbitrageCalculator.decimal_to_implied_probability(odd) for odd in odds]
        total_implied_prob = sum(implied_probs)
        
        # Check if arbitrage exists
        arbitrage_exists = total_implied_prob < Decimal("1")
        
        if not arbitrage_exists:
            return {
                "arbitrage_exists": False,
                "market_overround": float(total_implied_prob),
                "bookmaker_margin": float((total_implied_prob - Decimal("1")) * 100)
            }
        
        # Calculate optimal stakes
        optimal_stakes = []
        for i, odd in enumerate(odds):
            stake_percentage = implied_probs[i] / total_implied_prob
            actual_stake = total_stake * stake_percentage
            optimal_stakes.append(actual_stake)
        
        # Calculate guaranteed profit
        best_payout = min(odd * stake for odd, stake in zip(odds, optimal_stakes))
        guaranteed_profit = best_payout - total_stake
        profit_margin = (guaranteed_profit / total_stake) * 100
        
        return {
            "arbitrage_exists": True,
            "optimal_stakes": [float(stake) for stake in optimal_stakes],
            "guaranteed_profit": float(guaranteed_profit),
            "profit_margin": float(profit_margin),
            "market_overround": float(total_implied_prob),
            "total_stake": float(total_stake),
            "best_payout": float(best_payout)
        }
    
    @staticmethod
    def calculate_breakeven_odds(target_implied_prob: Decimal, num_outcomes: int) -> List[Decimal]:
        """Calculate breakeven odds for a given implied probability and number of outcomes."""
        breakeven_odds = []
        for _ in range(num_outcomes):
            breakeven_odds.append(MathematicalArbitrageCalculator.implied_probability_to_decimal(target_implied_prob))
        return breakeven_odds
    
    @staticmethod
    def validate_odds_consistency(odds: List[Decimal]) -> Dict[str, Any]:
        """Validate odds for mathematical consistency."""
        issues = []
        
        if not odds:
            issues.append("No odds provided")
            return {"is_valid": False, "issues": issues}
        
        if len(odds) < 2:
            issues.append("At least 2 odds required")
        
        # Check for invalid odds
        for i, odd in enumerate(odds):
            if odd <= Decimal("1"):
                issues.append(f"Invalid odds {odd} at index {i} (must be > 1)")
            elif odd > Decimal("1000"):
                issues.append(f"Unusually high odds {odd} at index {i}")
        
        # Calculate market overround
        market_overround = MathematicalArbitrageCalculator.calculate_market_overround(odds)
        
        # Check for potential issues
        if market_overround > Decimal("2.0"):  # 200% overround
            issues.append(f"Very high market overround: {market_overround}")
        elif market_overround < Decimal("0.5"):  # 50% - potential data error
            issues.append(f"Very low market overround: {market_overround}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "market_overround": float(market_overround),
            "num_outcomes": len(odds)
        }


class MathematicalPrecisionTester:
    """Tester for mathematical precision and edge cases."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.precision_tests = []
        self.edge_case_tests = []
        self.performance_tests = []
    
    def test_decimal_precision(self) -> Dict[str, Any]:
        """Test decimal precision with various configurations."""
        self.logger.info("Testing decimal precision...")
        
        precision_tests = [
            {"precision": 28, "test_value": "1.1234567890123456789012345678"},
            {"precision": 50, "test_value": "1.1234567890123456789012345678901234567890123456789012345678"},
            {"precision": 10, "test_value": "1.1234567890"}
        ]
        
        results = []
        
        for test in precision_tests:
            precision = test["precision"]
            test_value = Decimal(test["test_value"])
            
            with localcontext() as ctx:
                ctx.prec = precision
                
                # Test basic arithmetic
                addition_result = test_value + Decimal("0.1")
                multiplication_result = test_value * Decimal("2")
                division_result = test_value / Decimal("3")
                
                # Test precision preservation
                precision_preserved = len(str(addition_result).split('.')[-1]) <= precision
                
                results.append({
                    "precision": precision,
                    "original_value": test["test_value"],
                    "addition_result": str(addition_result),
                    "multiplication_result": str(multiplication_result),
                    "division_result": str(division_result),
                    "precision_preserved": precision_preserved
                })
        
        return {
            "test_name": "decimal_precision",
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r["precision_preserved"]),
            "results": results
        }
    
    def test_probability_calculations(self) -> Dict[str, Any]:
        """Test probability calculation edge cases."""
        self.logger.info("Testing probability calculations...")
        
        test_cases = [
            {
                "name": "Very low odds",
                "odds": [Decimal("1.001"), Decimal("1000.0")],
                "expected_behavior": "high_implied_prob"
            },
            {
                "name": "Very high odds", 
                "odds": [Decimal("1000.0"), Decimal("1.001")],
                "expected_behavior": "high_implied_prob"
            },
            {
                "name": "Boundary - exactly 1.0",
                "odds": [Decimal("1.0")],
                "expected_behavior": "should_fail"
            },
            {
                "name": "Normal range",
                "odds": [Decimal("2.0"), Decimal("3.0"), Decimal("6.0")],
                "expected_behavior": "valid"
            },
            {
                "name": "Many outcomes",
                "odds": [Decimal("1.5") + Decimal(str(i)) for i in range(10)],
                "expected_behavior": "valid"
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                odds = test_case["odds"]
                
                # Test conversion functions
                implied_probs = []
                for odd in odds:
                    try:
                        implied_prob = MathematicalArbitrageCalculator.decimal_to_implied_probability(odd)
                        implied_probs.append(implied_prob)
                    except ValueError as e:
                        implied_probs.append(None)
                
                # Test market overround calculation
                market_overround = MathematicalArbitrageCalculator.calculate_market_overround(odds)
                
                # Validate results based on expected behavior
                behavior_valid = True
                
                if test_case["expected_behavior"] == "should_fail":
                    behavior_valid = any(p is None for p in implied_probs)
                elif test_case["expected_behavior"] == "high_implied_prob":
                    behavior_valid = any(p is not None and p > Decimal("0.5") for p in implied_probs if p is not None)
                elif test_case["expected_behavior"] == "valid":
                    behavior_valid = all(p is not None for p in implied_probs)
                
                results.append({
                    "test_name": test_case["name"],
                    "odds": [str(odd) for odd in odds],
                    "implied_probs": [str(p) if p is not None else "FAILED" for p in implied_probs],
                    "market_overround": str(market_overround),
                    "behavior_valid": behavior_valid,
                    "success": True
                })
                
            except Exception as e:
                results.append({
                    "test_name": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "test_name": "probability_calculations",
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.get("success", False) and r.get("behavior_valid", False)),
            "results": results
        }
    
    def test_arbitrage_calculations(self) -> Dict[str, Any]:
        """Test arbitrage profit calculation edge cases."""
        self.logger.info("Testing arbitrage calculations...")
        
        test_cases = [
            {
                "name": "Clear arbitrage",
                "odds": [Decimal("2.1"), Decimal("1.9"), Decimal("3.2")],
                "total_stake": Decimal("1000"),
                "expected_profit_positive": True
            },
            {
                "name": "No arbitrage",
                "odds": [Decimal("1.8"), Decimal("1.9"), Decimal("2.1")],
                "total_stake": Decimal("1000"),
                "expected_profit_positive": False
            },
            {
                "name": "Very small arbitrage margin",
                "odds": [Decimal("1.999"), Decimal("2.001")],
                "total_stake": Decimal("10000"),
                "expected_profit_positive": True
            },
            {
                "name": "Large stakes",
                "odds": [Decimal("2.0"), Decimal("3.0"), Decimal("6.0")],
                "total_stake": Decimal("1000000"),
                "expected_profit_positive": True
            },
            {
                "name": "Extreme odds",
                "odds": [Decimal("1.01"), Decimal("100.0")],
                "total_stake": Decimal("100"),
                "expected_profit_positive": True
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                odds = test_case["odds"]
                total_stake = test_case["total_stake"]
                
                calculation_result = MathematicalArbitrageCalculator.calculate_arbitrage_profit(
                    odds, total_stake
                )
                
                # Check if profit calculation is positive as expected
                has_profit = calculation_result.get("arbitrage_exists", False)
                expected_profit = test_case["expected_profit_positive"]
                
                # Additional validation checks
                profit_valid = True
                if has_profit:
                    profit = Decimal(str(calculation_result.get("guaranteed_profit", 0)))
                    profit_valid = profit > Decimal("0")
                    
                    # Check stake calculation sums to total
                    stakes = calculation_result.get("optimal_stakes", [])
                    total_allocated = sum(Decimal(str(stake)) for stake in stakes)
                    stake_valid = abs(total_allocated - total_stake) < Decimal("0.01")
                    profit_valid = profit_valid and stake_valid
                
                results.append({
                    "test_name": test_case["name"],
                    "odds": [str(odd) for odd in odds],
                    "total_stake": str(total_stake),
                    "arbitrage_exists": calculation_result.get("arbitrage_exists", False),
                    "profit_margin": calculation_result.get("profit_margin", 0),
                    "guaranteed_profit": calculation_result.get("guaranteed_profit", 0),
                    "expected_profit_positive": expected_profit,
                    "has_profit": has_profit,
                    "profit_valid": profit_valid,
                    "success": True
                })
                
            except Exception as e:
                results.append({
                    "test_name": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "test_name": "arbitrage_calculations",
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.get("success", False) and r.get("profit_valid", False)),
            "results": results
        }
    
    def test_rounding_behavior(self) -> Dict[str, Any]:
        """Test various rounding modes and precision behaviors."""
        self.logger.info("Testing rounding behavior...")
        
        test_values = [
            Decimal("1.23456789"),
            Decimal("2.99999999"),
            Decimal("0.00000001"),
            Decimal("999999.999999")
        ]
        
        rounding_modes = [
            ROUND_HALF_UP,
            ROUND_DOWN,
            ROUND_UP,
            ROUND_FLOOR,
            ROUND_CEILING
        ]
        
        results = []
        
        for value in test_values:
            for rounding_mode in rounding_modes:
                try:
                    # Test different precision levels
                    rounded_values = []
                    for precision in [2, 4, 8, 16]:
                        with localcontext() as ctx:
                            ctx.prec = precision
                            rounded = value.quantize(Decimal("0." + "0" * precision + "1"), rounding=rounding_mode)
                            rounded_values.append((precision, str(rounded)))
                    
                    results.append({
                        "original_value": str(value),
                        "rounding_mode": str(rounding_mode),
                        "rounded_values": rounded_values,
                        "success": True
                    })
                    
                except Exception as e:
                    results.append({
                        "original_value": str(value),
                        "rounding_mode": str(rounding_mode),
                        "success": False,
                        "error": str(e)
                    })
        
        return {
            "test_name": "rounding_behavior",
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.get("success", False)),
            "results": results
        }
    
    def test_boundary_conditions(self) -> Dict[str, Any]:
        """Test mathematical boundary conditions."""
        self.logger.info("Testing boundary conditions...")
        
        boundary_tests = [
            {
                "name": "Maximum decimal precision",
                "test_function": lambda: self._test_max_precision(),
                "expected_success": True
            },
            {
                "name": "Minimum positive odds",
                "test_function": lambda: MathematicalArbitrageCalculator.decimal_to_implied_probability(Decimal("1.0000001")),
                "expected_success": True
            },
            {
                "name": "Maximum reasonable odds",
                "test_function": lambda: MathematicalArbitrageCalculator.decimal_to_implied_probability(Decimal("1000000")),
                "expected_success": True
            },
            {
                "name": "Zero probability boundary",
                "test_function": lambda: MathematicalArbitrageCalculator.implied_probability_to_decimal(Decimal("0.0000001")),
                "expected_success": True
            },
            {
                "name": "One probability boundary",
                "test_function": lambda: MathematicalArbitrageCalculator.implied_probability_to_decimal(Decimal("0.9999999")),
                "expected_success": True
            }
        ]
        
        results = []
        
        for test in boundary_tests:
            try:
                start_time = time.time()
                result = test["test_function"]()
                execution_time = (time.time() - start_time) * 1000
                
                results.append({
                    "test_name": test["name"],
                    "result": str(result),
                    "execution_time_ms": execution_time,
                    "success": True,
                    "expected_success": test["expected_success"]
                })
                
            except Exception as e:
                results.append({
                    "test_name": test["name"],
                    "success": False,
                    "error": str(e),
                    "expected_success": test["expected_success"]
                })
        
        return {
            "test_name": "boundary_conditions",
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.get("success", False) == r.get("expected_success", True)),
            "results": results
        }
    
    def _test_max_precision(self) -> str:
        """Test maximum decimal precision operations."""
        # Create very precise numbers
        high_precision_values = [
            Decimal("1.123456789012345678901234567890123456789"),
            Decimal("0.000000000000000000000000000000000000001")
        ]
        
        result = high_precision_values[0] * high_precision_values[1]
        return str(result)
    
    def test_performance_mathematical_operations(self) -> Dict[str, Any]:
        """Test performance of mathematical operations."""
        self.logger.info("Testing mathematical operation performance...")
        
        # Test large number of calculations
        num_calculations = 10000
        
        start_time = time.time()
        
        # Perform many arbitrage calculations
        for i in range(num_calculations):
            odds = [
                Decimal("1.5") + Decimal(str(i % 10) + ".001"),
                Decimal("2.0") + Decimal(str(i % 8) + ".002"),
                Decimal("3.0") + Decimal(str(i % 6) + ".003")
            ]
            
            MathematicalArbitrageCalculator.calculate_arbitrage_profit(
                odds, Decimal("1000")
            )
        
        total_time = time.time() - start_time
        
        return {
            "test_name": "performance_operations",
            "num_calculations": num_calculations,
            "total_time_seconds": total_time,
            "calculations_per_second": num_calculations / total_time,
            "average_time_per_calculation_ms": (total_time * 1000) / num_calculations
        }
    
    def test_numerical_stability(self) -> Dict[str, Any]:
        """Test numerical stability with extreme values."""
        self.logger.info("Testing numerical stability...")
        
        stability_tests = [
            {
                "name": "Very small probability differences",
                "odds": [
                    Decimal("1.9999999"),
                    Decimal("2.0000001"),
                    Decimal("2.0000000")
                ]
            },
            {
                "name": "Large probability differences",
                "odds": [
                    Decimal("1.01"),
                    Decimal("100.0"),
                    Decimal("1000.0")
                ]
            },
            {
                "name": "Identical odds",
                "odds": [
                    Decimal("2.0"),
                    Decimal("2.0"),
                    Decimal("2.0")
                ]
            }
        ]
        
        results = []
        
        for test in stability_tests:
            try:
                # Run calculation multiple times to check consistency
                calculation_results = []
                for _ in range(100):
                    result = MathematicalArbitrageCalculator.calculate_arbitrage_profit(
                        test["odds"], Decimal("10000")
                    )
                    calculation_results.append(result)
                
                # Check consistency of results
                profit_margins = [r.get("profit_margin", 0) for r in calculation_results]
                profit_values = [r.get("guaranteed_profit", 0) for r in calculation_results]
                
                margin_consistent = len(set(profit_margins)) == 1
                profit_consistent = len(set(profit_values)) == 1
                
                results.append({
                    "test_name": test["name"],
                    "odds": [str(odd) for odd in test["odds"]],
                    "margin_consistent": margin_consistent,
                    "profit_consistent": profit_consistent,
                    "num_calculations": len(calculation_results),
                    "unique_margins": len(set(profit_margins)),
                    "unique_profits": len(set(profit_values)),
                    "success": margin_consistent and profit_consistent
                })
                
            except Exception as e:
                results.append({
                    "test_name": test["name"],
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "test_name": "numerical_stability",
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.get("success", False)),
            "results": results
        }


class MathematicalTestSuite:
    """Comprehensive mathematical testing suite."""
    
    def __init__(self):
        self.calculator = MathematicalArbitrageCalculator()
        self.tester = MathematicalPrecisionTester()
        self.logger = logging.getLogger(__name__)
        
    def run_comprehensive_mathematical_tests(self) -> Dict[str, Any]:
        """Run all mathematical tests and compile results."""
        self.logger.info("Running comprehensive mathematical tests...")
        
        all_results = {
            "timestamp": datetime.now().isoformat(),
            "test_suites": {}
        }
        
        # Run all test categories
        all_results["test_suites"]["precision_tests"] = self.tester.test_decimal_precision()
        all_results["test_suites"]["probability_tests"] = self.tester.test_probability_calculations()
        all_results["test_suites"]["arbitrage_tests"] = self.tester.test_arbitrage_calculations()
        all_results["test_suites"]["rounding_tests"] = self.tester.test_rounding_behavior()
        all_results["test_suites"]["boundary_tests"] = self.tester.test_boundary_conditions()
        all_results["test_suites"]["stability_tests"] = self.tester.test_numerical_stability()
        all_results["test_suites"]["performance_tests"] = self.tester.test_performance_mathematical_operations()
        
        # Calculate overall metrics
        total_tests = sum(
            result.get("total_tests", 0) 
            for result in all_results["test_suites"].values()
        )
        
        total_passed = sum(
            result.get("passed_tests", 0) 
            for result in all_results["test_suites"].values()
        )
        
        all_results["overall_metrics"] = {
            "total_tests": total_tests,
            "passed_tests": total_passed,
            "overall_success_rate": total_passed / total_tests if total_tests > 0 else 0,
            "test_completion_time": datetime.now().isoformat()
        }
        
        return all_results
    
    def generate_mathematical_report(self) -> str:
        """Generate comprehensive mathematical test report."""
        results = self.run_comprehensive_mathematical_tests()
        
        report = f"""
MATHEMATICAL ACCURACY TEST REPORT
=================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY
----------------
Total Mathematical Tests: {results['overall_metrics']['total_tests']}
Passed Tests: {results['overall_metrics']['passed_tests']}
Overall Success Rate: {results['overall_metrics']['overall_success_rate']:.2%}

TEST CATEGORY BREAKDOWN
----------------------
"""
        
        for category, result in results["test_suites"].items():
            category_name = category.replace("_tests", "").replace("_", " ").title()
            report += f"{category_name}:\n"
            report += f"  Total Tests: {result.get('total_tests', 0)}\n"
            report += f"  Passed Tests: {result.get('passed_tests', 0)}\n"
            if result.get('total_tests', 0) > 0:
                success_rate = result.get('passed_tests', 0) / result.get('total_tests', 1)
                report += f"  Success Rate: {success_rate:.2%}\n"
            report += "\n"
        
        # Add performance summary
        performance_result = results["test_suites"].get("performance_tests", {})
        if performance_result:
            report += "PERFORMANCE SUMMARY\n"
            report += "------------------\n"
            report += f"Calculations per Second: {performance_result.get('calculations_per_second', 0):.0f}\n"
            report += f"Average Time per Calculation: {performance_result.get('average_time_per_calculation_ms', 0):.2f}ms\n"
        
        return report
    
    def save_mathematical_results(self, filepath: str):
        """Save mathematical test results to JSON file."""
        results = self.run_comprehensive_mathematical_tests()
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"Mathematical test results saved to {filepath}")


# Pytest test classes
class TestMathematicalPrecision:
    """Pytest tests for mathematical precision."""
    
    @pytest.fixture
    def calculator(self):
        return MathematicalArbitrageCalculator()
    
    @pytest.fixture
    def tester(self):
        return MathematicalPrecisionTester()
    
    def test_decimal_conversions(self, calculator):
        """Test decimal odds to probability conversions."""
        # Test valid conversions
        assert calculator.decimal_to_implied_probability(Decimal("2.0")) == Decimal("0.5")
        assert calculator.decimal_to_implied_probability(Decimal("1.5")) == Decimal("0.6666666666666666666666666667")
        
        # Test invalid conversions
        with pytest.raises(ValueError):
            calculator.decimal_to_implied_probability(Decimal("1.0"))
        
        with pytest.raises(ValueError):
            calculator.decimal_to_implied_probability(Decimal("0.5"))
    
    def test_probability_conversions(self, calculator):
        """Test probability to decimal odds conversions."""
        # Test valid conversions
        assert calculator.implied_probability_to_decimal(Decimal("0.5")) == Decimal("2.0")
        assert calculator.implied_probability_to_decimal(Decimal("0.6666666666666666666666666667")) == Decimal("1.5")
        
        # Test invalid conversions
        with pytest.raises(ValueError):
            calculator.implied_probability_to_decimal(Decimal("0.0"))
        
        with pytest.raises(ValueError):
            calculator.implied_probability_to_decimal(Decimal("1.0"))
    
    def test_precision_consistency(self, tester):
        """Test precision consistency across operations."""
        results = tester.test_decimal_precision()
        
        assert results["passed_tests"] >= results["total_tests"] * 0.8  # At least 80% should preserve precision


class TestArbitrageCalculations:
    """Pytest tests for arbitrage calculations."""
    
    @pytest.fixture
    def calculator(self):
        return MathematicalArbitrageCalculator()
    
    def test_arbitrage_detection(self, calculator):
        """Test arbitrage detection accuracy."""
        # Clear arbitrage case
        odds = [Decimal("2.1"), Decimal("1.9"), Decimal("3.2")]
        result = calculator.calculate_arbitrage_profit(odds)
        
        assert result["arbitrage_exists"] == True
        assert result["profit_margin"] > 0
        assert result["guaranteed_profit"] > 0
    
    def test_no_arbitrage_case(self, calculator):
        """Test no arbitrage case."""
        # No arbitrage case
        odds = [Decimal("1.8"), Decimal("1.9"), Decimal("2.1")]
        result = calculator.calculate_arbitrage_profit(odds)
        
        assert result["arbitrage_exists"] == False
    
    def test_profit_calculation_accuracy(self, calculator):
        """Test profit calculation accuracy."""
        odds = [Decimal("2.0"), Decimal("3.0"), Decimal("6.0")]
        result = calculator.calculate_arbitrage_profit(odds, Decimal("1000"))
        
        # Verify stake calculation accuracy
        stakes = [Decimal(str(stake)) for stake in result["optimal_stakes"]]
        total_staked = sum(stakes)
        
        assert abs(total_staked - Decimal("1000")) < Decimal("0.01")
    
    def test_boundary_odds(self, calculator):
        """Test boundary odds conditions."""
        # Very high odds
        high_odds = [Decimal("1000.0"), Decimal("1.001")]
        result = calculator.calculate_arbitrage_profit(high_odds, Decimal("1000"))
        
        assert "arbitrage_exists" in result
        assert isinstance(result["profit_margin"], float)


class TestMathematicalStability:
    """Pytest tests for mathematical stability."""
    
    @pytest.fixture
    def tester(self):
        return MathematicalPrecisionTester()
    
    def test_numerical_stability(self, tester):
        """Test numerical stability."""
        results = tester.test_numerical_stability()
        
        assert results["passed_tests"] >= results["total_tests"] * 0.9  # At least 90% stability
    
    def test_performance_requirements(self, tester):
        """Test performance meets requirements."""
        results = tester.test_performance_mathematical_operations()
        
        # Should handle at least 100 calculations per second
        assert results["calculations_per_second"] >= 100
        
        # Should be fast enough
        assert results["average_time_per_calculation_ms"] <= 10


if __name__ == "__main__":
    # Run comprehensive mathematical tests when script is executed
    test_suite = MathematicalTestSuite()
    
    print("Running Comprehensive Mathematical Accuracy Tests...")
    print("=" * 60)
    
    # Run all test categories
    all_results = test_suite.run_comprehensive_mathematical_tests()
    
    # Generate and print comprehensive report
    report = test_suite.generate_mathematical_report()
    print(report)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"mathematical_accuracy_test_results_{timestamp}.json"
    test_suite.save_mathematical_results(results_file)
    
    print(f"\nDetailed results saved to: {results_file}")
    print(f"Overall success rate: {all_results['overall_metrics']['overall_success_rate']:.2%}")