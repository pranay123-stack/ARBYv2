"""
Odds Validation Testing Framework

Tests for mathematical validation of extracted odds including:
- Sum of probabilities validation
- Arbitrage detection and calculation
- Market efficiency testing
- Odds consistency checks
"""

import json
import logging
import math
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock

import pytest


class OddsValidator:
    """Validator for extracted betting odds."""
    
    @staticmethod
    def decimal_to_implied_probability(decimal_odds: Decimal) -> Decimal:
        """Convert decimal odds to implied probability."""
        if decimal_odds <= 1:
            raise ValueError("Decimal odds must be greater than 1")
        return Decimal("1.0") / decimal_odds
        
    @staticmethod
    def implied_probability_to_decimal(probability: Decimal) -> Decimal:
        """Convert implied probability to decimal odds."""
        if probability <= 0 or probability >= 1:
            raise ValueError("Probability must be between 0 and 1")
        return Decimal("1.0") / probability
        
    @staticmethod
    def calculate_market_overround(odds: List[Decimal]) -> Decimal:
        """Calculate market overround (sum of implied probabilities)."""
        if not odds:
            return Decimal("0")
            
        total_implied_prob = sum(OddsValidator.decimal_to_implied_probability(odd) for odd in odds)
        return total_implied_prob
        
    @staticmethod
    def detect_arbitrage(odds_by_bookmaker: Dict[str, List[Decimal]]) -> Dict[str, Any]:
        """Detect arbitrage opportunities across bookmakers."""
        if not odds_by_bookmaker:
            return {"arbitrage_exists": False}
            
        # Find best odds for each outcome across all bookmakers
        best_odds = {}
        for bookmaker, odds in odds_by_bookmaker.items():
            for i, odd in enumerate(odds):
                if i not in best_odds or odd > best_odds[i][0]:
                    best_odds[i] = (odd, bookmaker)
                    
        # Calculate if arbitrage exists
        if not best_odds:
            return {"arbitrage_exists": False}
            
        best_odds_values = [odd for odd, _ in best_odds.values()]
        market_overround = OddsValidator.calculate_market_overround(best_odds_values)
        
        arbitrage_exists = market_overround < Decimal("1.0")
        
        if arbitrage_exists:
            # Calculate optimal stakes
            total_stake = Decimal("1000.0")  # Example stake
            optimal_stakes = []
            total_implied_prob = market_overround
            
            for odd, _ in best_odds.values():
                implied_prob = OddsValidator.decimal_to_implied_probability(odd)
                stake_percentage = implied_prob / total_implied_prob
                actual_stake = total_stake * stake_percentage
                optimal_stakes.append(actual_stake)
                
            # Calculate guaranteed profit
            best_payout = min(odd * stake for odd, stake in zip(best_odds_values, optimal_stakes))
            guaranteed_profit = best_payout - total_stake
            profit_margin = (guaranteed_profit / total_stake) * 100
            
            return {
                "arbitrage_exists": True,
                "profit_margin": profit_margin,
                "guaranteed_profit": guaranteed_profit,
                "best_odds": dict(zip(range(len(best_odds_values)), best_odds_values)),
                "best_bookmakers": dict(zip(range(len(best_odds_values)), [bm for _, bm in best_odds.values()])),
                "optimal_stakes": optimal_stakes,
                "market_overround": market_overround
            }
        else:
            return {
                "arbitrage_exists": False,
                "market_overround": market_overround,
                "bookmaker_edge": (market_overround - Decimal("1.0")) * 100
            }
            
    @staticmethod
    def validate_odds_consistency(odds_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate consistency of extracted odds data."""
        issues = []
        warnings = []
        
        # Check required fields
        required_fields = ["bookmaker", "sport", "event_name", "market_type", "odds"]
        for field in required_fields:
            if field not in odds_data or not odds_data[field]:
                issues.append(f"Missing required field: {field}")
                
        # Validate odds format and values
        if "odds" in odds_data:
            odds_list = odds_data["odds"]
            
            if not isinstance(odds_list, list) or len(odds_list) < 2:
                issues.append("Odds must be a list with at least 2 entries")
            else:
                decimal_odds = []
                for i, odds_entry in enumerate(odds_list):
                    if not isinstance(odds_entry, dict):
                        issues.append(f"Odds entry {i} must be a dictionary")
                        continue
                        
                    if "decimal_odds" not in odds_entry:
                        issues.append(f"Missing decimal_odds in entry {i}")
                        continue
                        
                    try:
                        odd = Decimal(str(odds_entry["decimal_odds"]))
                        if odd <= 1:
                            issues.append(f"Invalid odds value {odd} in entry {i} (must be > 1)")
                        elif odd > 1000:
                            warnings.append(f"Unusually high odds {odd} in entry {i}")
                        else:
                            decimal_odds.append(odd)
                    except (ValueError, TypeError):
                        issues.append(f"Invalid decimal_odds format in entry {i}")
                        
                # Check for reasonable market totals
                if decimal_odds:
                    market_overround = OddsValidator.calculate_market_overround(decimal_odds)
                    
                    if market_overround > Decimal("1.5"):  # 150% overround
                        warnings.append(f"Very high market overround: {market_overround:.3f}")
                    elif market_overround < Decimal("0.8"):  # 80% - potential arbitrage
                        warnings.append(f"Low market overround detected: {market_overround:.3f} (potential arbitrage)")
                        
        # Check for duplicate outcomes
        if "odds" in odds_data:
            outcomes = [odds.get("outcome", "") for odds in odds_data["odds"]]
            if len(outcomes) != len(set(outcomes)):
                issues.append("Duplicate outcomes detected in odds list")
                
        # Validate sport and market type consistency
        sport = odds_data.get("sport", "").lower()
        market_type = odds_data.get("market_type", "").lower()
        
        if "over" in market_type or "under" in market_type:
            if sport not in ["football", "basketball", "baseball"]:
                warnings.append(f"Over/Under market type {market_type} may not be suitable for {sport}")
                
        if "handicap" in market_type:
            if sport not in ["football", "basketball", "tennis"]:
                warnings.append(f"Handicap market type {market_type} may not be suitable for {sport}")
                
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "validation_timestamp": datetime.now().isoformat()
        }


class MockVLMOddsExtractor:
    """Mock VLM extractor that generates realistic odds data for testing."""
    
    def __init__(self, error_rate: float = 0.15):
        self.error_rate = error_rate
        
    def extract_odds_with_validation(self, image_path: str) -> Dict[str, Any]:
        """Extract odds and include validation results."""
        import random
        random.seed(hash(image_path) % 1000)
        
        # Simulate extraction success/failure
        if random.random() < self.error_rate:
            return {
                "success": False,
                "error": "extraction_failed",
                "confidence": random.uniform(0.1, 0.4),
                "validation": {
                    "is_valid": False,
                    "issues": ["extraction_failed"],
                    "warnings": []
                }
            }
            
        # Generate realistic odds data
        bookmakers = ["Bet365", "William Hill", "Ladbrokes", "Betfair", "Pinnacle", "1xBet"]
        sports = ["Football", "Tennis", "Basketball", "Baseball"]
        market_types = ["match_winner", "total_points", "handicap", "over_under"]
        
        bookmaker = random.choice(bookmakers)
        sport = random.choice(sports)
        market_type = random.choice(market_types)
        
        # Generate outcomes based on market type
        if market_type == "match_winner":
            outcomes = ["Home Win", "Draw", "Away Win"] if sport == "Football" else ["Player A", "Player B"]
        elif market_type == "total_points":
            outcomes = ["Over 150.5", "Under 150.5"]
        elif market_type == "handicap":
            outcomes = ["Home -2.5", "Away +2.5"]
        else:
            outcomes = ["Yes", "No"]
            
        # Generate realistic odds
        odds = []
        for outcome in outcomes:
            base_odd = random.uniform(1.5, 4.0)
            
            # Introduce some realistic inconsistencies
            if random.random() < 0.1:  # 10% chance of bad odds
                if random.random() < 0.5:
                    base_odd = random.uniform(0.5, 1.2)  # Too low
                else:
                    base_odd = random.uniform(15.0, 50.0)  # Too high
                    
            odds.append({
                "outcome": outcome,
                "decimal_odds": round(base_odd, 2)
            })
            
        result = {
            "success": True,
            "bookmaker": bookmaker,
            "sport": sport,
            "event_name": f"{random.choice(['Team A', 'Player X'])} vs {random.choice(['Team B', 'Player Y'])}",
            "market_type": market_type,
            "odds": odds,
            "confidence": random.uniform(0.65, 0.95),
            "processing_time_ms": random.uniform(80, 250)
        }
        
        # Add validation
        result["validation"] = OddsValidator.validate_odds_consistency(result)
        
        return result


class OddsValidationTestSuite:
    """Comprehensive test suite for odds validation."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mock_extractor = MockVLMOddsExtractor()
        self.validation_results = []
        
    def test_probability_sum_validation(self) -> Dict[str, Any]:
        """Test that extracted odds have valid probability sums."""
        self.logger.info("Testing probability sum validation...")
        
        test_cases = [
            # Valid market (normal overround)
            {"odds": [Decimal("2.0"), Decimal("3.5"), Decimal("4.0")], "expected_valid": True},
            # Perfect market (exactly 100%)
            {"odds": [Decimal("2.0"), Decimal("3.0"), Decimal("6.0")], "expected_valid": True},
            # Arbitrage opportunity
            {"odds": [Decimal("1.8"), Decimal("1.9"), Decimal("2.2")], "expected_valid": True},
            # Invalid market (over 150% overround)
            {"odds": [Decimal("1.2"), Decimal("1.3"), Decimal("1.4")], "expected_valid": False},
            # Edge cases
            {"odds": [Decimal("1.01")], "expected_valid": False},  # Single odds
            {"odds": [], "expected_valid": False},  # Empty odds
        ]
        
        results = {
            "total_tests": len(test_cases),
            "passed_tests": 0,
            "failed_tests": 0,
            "validation_details": []
        }
        
        for i, test_case in enumerate(test_cases):
            try:
                odds = test_case["odds"]
                expected_valid = test_case["expected_valid"]
                
                if not odds:
                    results["failed_tests"] += 1
                    results["validation_details"].append({
                        "test_case": i,
                        "status": "failed",
                        "reason": "empty_odds"
                    })
                    continue
                    
                market_overround = OddsValidator.calculate_market_overround(odds)
                
                # Consider valid if overround is between 80% and 150%
                is_valid = Decimal("0.8") <= market_overround <= Decimal("1.5")
                
                if is_valid == expected_valid:
                    results["passed_tests"] += 1
                    status = "passed"
                else:
                    results["failed_tests"] += 1
                    status = "failed"
                    
                results["validation_details"].append({
                    "test_case": i,
                    "status": status,
                    "odds": [float(odd) for odd in odds],
                    "market_overround": float(market_overround),
                    "expected_valid": expected_valid,
                    "actual_valid": is_valid
                })
                
            except Exception as e:
                results["failed_tests"] += 1
                results["validation_details"].append({
                    "test_case": i,
                    "status": "failed",
                    "reason": str(e)
                })
                
        results["success_rate"] = results["passed_tests"] / results["total_tests"]
        return results
        
    def test_arbitrage_detection(self) -> Dict[str, Any]:
        """Test arbitrage detection across multiple bookmakers."""
        self.logger.info("Testing arbitrage detection...")
        
        # Test cases with different arbitrage scenarios
        test_scenarios = [
            {
                "name": "Clear Arbitrage Opportunity",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("2.1"), Decimal("1.9"), Decimal("3.2")],
                    "Bookmaker_B": [Decimal("1.9"), Decimal("2.2"), Decimal("2.8")],
                    "Bookmaker_C": [Decimal("2.0"), Decimal("1.8"), Decimal("3.5")]
                },
                "expected_arbitrage": True
            },
            {
                "name": "No Arbitrage",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("1.8"), Decimal("1.9"), Decimal("2.1")],
                    "Bookmaker_B": [Decimal("1.85"), Decimal("1.95"), Decimal("2.05")],
                    "Bookmaker_C": [Decimal("1.9"), Decimal("1.85"), Decimal("2.15")]
                },
                "expected_arbitrage": False
            },
            {
                "name": "Marginal Arbitrage",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("1.95"), Decimal("1.95"), Decimal("2.15")],
                    "Bookmaker_B": [Decimal("1.98"), Decimal("1.93"), Decimal("2.10")]
                },
                "expected_arbitrage": False  # Very close to break-even
            },
            {
                "name": "Two-Outcome Arbitrage",
                "odds_by_bookmaker": {
                    "Bookmaker_A": [Decimal("1.8"), Decimal("2.3")],
                    "Bookmaker_B": [Decimal("2.1"), Decimal("1.9")]
                },
                "expected_arbitrage": True
            }
        ]
        
        results = {
            "total_tests": len(test_scenarios),
            "passed_tests": 0,
            "failed_tests": 0,
            "arbitrage_details": []
        }
        
        for scenario in test_scenarios:
            try:
                detection_result = OddsValidator.detect_arbitrage(scenario["odds_by_bookmaker"])
                
                actual_arbitrage = detection_result.get("arbitrage_exists", False)
                expected_arbitrage = scenario["expected_arbitrage"]
                
                if actual_arbitrage == expected_arbitrage:
                    results["passed_tests"] += 1
                    status = "passed"
                else:
                    results["failed_tests"] += 1
                    status = "failed"
                    
                # Add detailed results
                scenario_result = {
                    "scenario_name": scenario["name"],
                    "status": status,
                    "expected_arbitrage": expected_arbitrage,
                    "actual_arbitrage": actual_arbitrage,
                    "detection_result": {
                        k: float(v) if isinstance(v, Decimal) else v 
                        for k, v in detection_result.items()
                    }
                }
                
                results["arbitrage_details"].append(scenario_result)
                
            except Exception as e:
                results["failed_tests"] += 1
                results["arbitrage_details"].append({
                    "scenario_name": scenario["name"],
                    "status": "failed",
                    "reason": str(e)
                })
                
        results["success_rate"] = results["passed_tests"] / results["total_tests"]
        return results
        
    def test_odds_consistency_validation(self) -> Dict[str, Any]:
        """Test validation of odds data consistency."""
        self.logger.info("Testing odds consistency validation...")
        
        test_cases = [
            {
                "name": "Valid Football Match",
                "data": {
                    "bookmaker": "Bet365",
                    "sport": "Football",
                    "event_name": "Manchester United vs Liverpool",
                    "market_type": "match_winner",
                    "odds": [
                        {"outcome": "Home Win", "decimal_odds": 2.1},
                        {"outcome": "Draw", "decimal_odds": 3.2},
                        {"outcome": "Away Win", "decimal_odds": 3.8}
                    ]
                },
                "expected_valid": True
            },
            {
                "name": "Invalid Low Odds",
                "data": {
                    "bookmaker": "Pinnacle",
                    "sport": "Tennis",
                    "event_name": "Djokovic vs Nadal",
                    "market_type": "match_winner",
                    "odds": [
                        {"outcome": "Djokovic", "decimal_odds": 0.8},
                        {"outcome": "Nadal", "decimal_odds": 1.3}
                    ]
                },
                "expected_valid": False
            },
            {
                "name": "Missing Required Fields",
                "data": {
                    "bookmaker": "William Hill",
                    "sport": "Basketball",
                    "odds": [
                        {"outcome": "Over 150.5", "decimal_odds": 1.9},
                        {"outcome": "Under 150.5", "decimal_odds": 1.9}
                    ]
                },
                "expected_valid": False
            },
            {
                "name": "High Overround Warning",
                "data": {
                    "bookmaker": "1xBet",
                    "sport": "Football",
                    "event_name": "Arsenal vs Chelsea",
                    "market_type": "match_winner",
                    "odds": [
                        {"outcome": "Home Win", "decimal_odds": 1.1},
                        {"outcome": "Draw", "decimal_odds": 1.2},
                        {"outcome": "Away Win", "decimal_odds": 1.3}
                    ]
                },
                "expected_valid": True,  # Valid but with warnings
                "expected_warnings": True
            }
        ]
        
        results = {
            "total_tests": len(test_cases),
            "passed_tests": 0,
            "failed_tests": 0,
            "validation_details": []
        }
        
        for test_case in test_cases:
            try:
                validation_result = OddsValidator.validate_odds_consistency(test_case["data"])
                
                is_valid = validation_result["is_valid"]
                expected_valid = test_case["expected_valid"]
                has_warnings = len(validation_result.get("warnings", [])) > 0
                expected_warnings = test_case.get("expected_warnings", False)
                
                # Test passes if validity matches expectation and warnings match expectation
                validity_match = is_valid == expected_valid
                warnings_match = has_warnings == expected_warnings or not expected_warnings
                
                if validity_match and warnings_match:
                    results["passed_tests"] += 1
                    status = "passed"
                else:
                    results["failed_tests"] += 1
                    status = "failed"
                    
                results["validation_details"].append({
                    "test_name": test_case["name"],
                    "status": status,
                    "expected_valid": expected_valid,
                    "actual_valid": is_valid,
                    "expected_warnings": expected_warnings,
                    "has_warnings": has_warnings,
                    "issues": validation_result["issues"],
                    "warnings": validation_result["warnings"]
                })
                
            except Exception as e:
                results["failed_tests"] += 1
                results["validation_details"].append({
                    "test_name": test_case["name"],
                    "status": "failed",
                    "reason": str(e)
                })
                
        results["success_rate"] = results["passed_tests"] / results["total_tests"]
        return results
        
    def test_vlm_integration_validation(self) -> Dict[str, Any]:
        """Test validation integration with VLM extraction."""
        self.logger.info("Testing VLM integration validation...")
        
        # Test with mock VLM extractions
        test_images = [
            "integration_test_1.png",
            "integration_test_2.png",
            "integration_test_3.png",
            "integration_test_4.png",
            "integration_test_5.png"
        ]
        
        results = {
            "total_extractions": len(test_images),
            "successful_extractions": 0,
            "valid_extractions": 0,
            "invalid_extractions": 0,
            "validation_issues": {},
            "performance_metrics": {
                "average_validation_time_ms": 0.0,
                "validation_accuracy": 0.0
            }
        }
        
        import time
        validation_times = []
        
        for image in test_images:
            try:
                # Extract odds using mock VLM
                extraction_start = time.time()
                extraction_result = self.mock_extractor.extract_odds_with_validation(image)
                extraction_time = (time.time() - extraction_start) * 1000
                
                # Validate extraction
                validation_start = time.time()
                if extraction_result["success"]:
                    results["successful_extractions"] += 1
                    
                    validation_result = extraction_result.get("validation", {})
                    is_valid = validation_result.get("is_valid", False)
                    
                    if is_valid:
                        results["valid_extractions"] += 1
                    else:
                        results["invalid_extractions"] += 1
                        
                    # Track validation issues
                    issues = validation_result.get("issues", [])
                    for issue in issues:
                        results["validation_issues"][issue] = results["validation_issues"].get(issue, 0) + 1
                        
                validation_time = (time.time() - validation_start) * 1000
                validation_times.append(validation_time)
                
            except Exception as e:
                self.logger.error(f"Integration test failed for {image}: {e}")
                results["invalid_extractions"] += 1
                results["validation_issues"]["extraction_exception"] = results["validation_issues"].get("extraction_exception", 0) + 1
                
        # Calculate performance metrics
        results["performance_metrics"]["average_validation_time_ms"] = sum(validation_times) / len(validation_times) if validation_times else 0
        results["performance_metrics"]["validation_accuracy"] = results["valid_extractions"] / max(results["successful_extractions"], 1)
        results["extraction_success_rate"] = results["successful_extractions"] / results["total_extractions"]
        
        return results
        
    def test_market_efficiency_analysis(self) -> Dict[str, Any]:
        """Test analysis of market efficiency and bookmaker margins."""
        self.logger.info("Testing market efficiency analysis...")
        
        # Test different market scenarios
        market_scenarios = [
            {
                "name": "Efficient Market",
                "odds": [Decimal("1.91"), Decimal("1.91"), Decimal("1.91")],  # ~105% overround
                "expected_efficiency": "efficient"
            },
            {
                "name": "Inefficient Market (High Margin)",
                "odds": [Decimal("1.80"), Decimal("1.80"), Decimal("1.80")],  # ~167% overround
                "expected_efficiency": "inefficient"
            },
            {
                "name": "Potentially Arbitragable",
                "odds": [Decimal("2.10"), Decimal("2.00"), Decimal("1.95")],  # ~147% overround
                "expected_efficiency": "monitor"
            }
        ]
        
        results = {
            "total_markets": len(market_scenarios),
            "efficiency_analysis": [],
            "margin_statistics": {
                "average_margin": 0.0,
                "min_margin": float('inf'),
                "max_margin": 0.0,
                "efficient_markets": 0
            }
        }
        
        margins = []
        
        for scenario in market_scenarios:
            odds = scenario["odds"]
            market_overround = OddsValidator.calculate_market_overround(odds)
            bookmaker_margin = (market_overround - Decimal("1.0")) * 100
            
            margins.append(float(bookmaker_margin))
            
            # Classify market efficiency
            if bookmaker_margin <= Decimal("6.0"):
                efficiency = "efficient"
                results["margin_statistics"]["efficient_markets"] += 1
            elif bookmaker_margin >= Decimal("15.0"):
                efficiency = "inefficient"
            else:
                efficiency = "monitor"
                
            results["efficiency_analysis"].append({
                "scenario_name": scenario["name"],
                "odds": [float(odd) for odd in odds],
                "market_overround": float(market_overround),
                "bookmaker_margin": float(bookmaker_margin),
                "efficiency_classification": efficiency,
                "expected_efficiency": scenario["expected_efficiency"]
            })
            
        # Calculate margin statistics
        if margins:
            results["margin_statistics"]["average_margin"] = sum(margins) / len(margins)
            results["margin_statistics"]["min_margin"] = min(margins)
            results["margin_statistics"]["max_margin"] = max(margins)
            
        return results
        
    def run_comprehensive_validation_tests(self) -> Dict[str, Any]:
        """Run all validation tests and compile results."""
        self.logger.info("Running comprehensive validation tests...")
        
        all_results = {
            "timestamp": datetime.now().isoformat(),
            "test_suites": {}
        }
        
        # Run all test suites
        all_results["test_suites"]["probability_validation"] = self.test_probability_sum_validation()
        all_results["test_suites"]["arbitrage_detection"] = self.test_arbitrage_detection()
        all_results["test_suites"]["consistency_validation"] = self.test_odds_consistency_validation()
        all_results["test_suites"]["vlm_integration"] = self.test_vlm_integration_validation()
        all_results["test_suites"]["market_efficiency"] = self.test_market_efficiency_analysis()
        
        # Calculate overall metrics
        total_tests = sum(result.get("total_tests", 0) for result in all_results["test_suites"].values())
        total_passed = sum(result.get("passed_tests", 0) for result in all_results["test_suites"].values())
        
        all_results["overall_metrics"] = {
            "total_tests": total_tests,
            "passed_tests": total_passed,
            "overall_success_rate": total_passed / total_tests if total_tests > 0 else 0,
            "test_completion_time": datetime.now().isoformat()
        }
        
        return all_results
        
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation test report."""
        results = self.run_comprehensive_validation_tests()
        
        report = f"""
Odds Validation Test Report
===========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERALL RESULTS
--------------
Total Tests: {results['overall_metrics']['total_tests']}
Passed Tests: {results['overall_metrics']['passed_tests']}
Success Rate: {results['overall_metrics']['overall_success_rate']:.2%}

PROBABILITY SUM VALIDATION
--------------------------
"""
        
        prob_results = results["test_suites"]["probability_validation"]
        report += f"Tests Run: {prob_results['total_tests']}\n"
        report += f"Success Rate: {prob_results['success_rate']:.2%}\n"
        report += f"Passed: {prob_results['passed_tests']}, Failed: {prob_results['failed_tests']}\n\n"
        
        report += "ARBITRAGE DETECTION\n-------------------\n"
        arb_results = results["test_suites"]["arbitrage_detection"]
        report += f"Tests Run: {arb_results['total_tests']}\n"
        report += f"Success Rate: {arb_results['success_rate']:.2%}\n"
        report += f"Passed: {arb_results['passed_tests']}, Failed: {arb_results['failed_tests']}\n\n"
        
        report += "ODDS CONSISTENCY VALIDATION\n---------------------------\n"
        cons_results = results["test_suites"]["consistency_validation"]
        report += f"Tests Run: {cons_results['total_tests']}\n"
        report += f"Success Rate: {cons_results['success_rate']:.2%}\n"
        report += f"Passed: {cons_results['passed_tests']}, Failed: {cons_results['failed_tests']}\n\n"
        
        report += "VLM INTEGRATION VALIDATION\n---------------------------\n"
        int_results = results["test_suites"]["vlm_integration"]
        report += f"Total Extractions: {int_results['total_extractions']}\n"
        report += f"Success Rate: {int_results['extraction_success_rate']:.2%}\n"
        report += f"Validation Accuracy: {int_results['performance_metrics']['validation_accuracy']:.2%}\n"
        report += f"Avg Validation Time: {int_results['performance_metrics']['average_validation_time_ms']:.1f}ms\n\n"
        
        report += "MARKET EFFICIENCY ANALYSIS\n---------------------------\n"
        eff_results = results["test_suites"]["market_efficiency"]
        report += f"Markets Analyzed: {eff_results['total_markets']}\n"
        report += f"Average Bookmaker Margin: {eff_results['margin_statistics']['average_margin']:.2f}%\n"
        report += f"Efficient Markets: {eff_results['margin_statistics']['efficient_markets']}\n"
        
        return report
        
    def save_validation_results(self, filepath: str):
        """Save validation test results to JSON file."""
        results = self.run_comprehensive_validation_tests()
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        self.logger.info(f"Validation results saved to {filepath}")


# Pytest test classes
class TestProbabilityValidation:
    """Test probability sum validation."""
    
    @pytest.fixture
    def validator(self):
        return OddsValidator()
        
    def test_decimal_to_probability_conversion(self, validator):
        """Test conversion from decimal odds to implied probability."""
        assert validator.decimal_to_implied_probability(Decimal("2.0")) == Decimal("0.5")
        assert validator.decimal_to_implied_probability(Decimal("1.5")) == Decimal("0.6666666666666666")
        
    def test_probability_to_decimal_conversion(self, validator):
        """Test conversion from implied probability to decimal odds."""
        assert validator.implied_probability_to_decimal(Decimal("0.5")) == Decimal("2.0")
        assert validator.implied_probability_to_decimal(Decimal("0.6666666666666666")) == Decimal("1.5")
        
    def test_market_overround_calculation(self, validator):
        """Test calculation of market overround."""
        odds = [Decimal("2.0"), Decimal("3.0"), Decimal("6.0")]
        overround = validator.calculate_market_overround(odds)
        assert abs(overround - Decimal("1.0")) < 0.001  # Should be exactly 100%
        
    def test_arbitrage_detection(self, validator):
        """Test arbitrage detection functionality."""
        odds_by_bookmaker = {
            "Bookmaker_A": [Decimal("2.1"), Decimal("1.9"), Decimal("3.2")],
            "Bookmaker_B": [Decimal("1.9"), Decimal("2.2"), Decimal("2.8")]
        }
        result = validator.detect_arbitrage(odds_by_bookmaker)
        assert result["arbitrage_exists"] == True


class TestOddsConsistency:
    """Test odds consistency validation."""
    
    @pytest.fixture
    def validator(self):
        return OddsValidator()
        
    def test_valid_odds_validation(self, validator):
        """Test validation of valid odds data."""
        valid_data = {
            "bookmaker": "Bet365",
            "sport": "Football",
            "event_name": "Man United vs Liverpool",
            "market_type": "match_winner",
            "odds": [
                {"outcome": "Home Win", "decimal_odds": 2.1},
                {"outcome": "Draw", "decimal_odds": 3.2},
                {"outcome": "Away Win", "decimal_odds": 3.8}
            ]
        }
        result = validator.validate_odds_consistency(valid_data)
        assert result["is_valid"] == True
        assert len(result["issues"]) == 0
        
    def test_invalid_odds_validation(self, validator):
        """Test validation of invalid odds data."""
        invalid_data = {
            "bookmaker": "Pinnacle",
            "odds": [
                {"outcome": "Over", "decimal_odds": 0.8},  # Invalid odds
                {"outcome": "Under", "decimal_odds": 1.3}
            ]
        }
        result = validator.validate_odds_consistency(invalid_data)
        assert result["is_valid"] == False
        assert len(result["issues"]) > 0


class TestVLMOddsIntegration:
    """Test VLM odds extraction integration."""
    
    @pytest.fixture
    def test_suite(self):
        return OddsValidationTestSuite()
        
    def test_validation_test_suite(self, test_suite):
        """Test that validation test suite runs successfully."""
        results = test_suite.test_probability_sum_validation()
        assert results["total_tests"] > 0
        assert "success_rate" in results
        
    def test_arbitrage_detection_suite(self, test_suite):
        """Test arbitrage detection suite."""
        results = test_suite.test_arbitrage_detection()
        assert results["total_tests"] > 0
        assert results["success_rate"] >= 0.5  # At least 50% success


if __name__ == "__main__":
    # Run tests directly when script is executed
    test_suite = OddsValidationTestSuite()
    
    print("Running Odds Validation Test Suite...")
    print("=" * 50)
    
    # Run comprehensive tests
    results = test_suite.run_comprehensive_validation_tests()
    
    # Generate and print comprehensive report
    report = test_suite.generate_validation_report()
    print(report)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"odds_validation_results_{timestamp}.json"
    test_suite.save_validation_results(results_file)
    
    print(f"\nResults saved to: {results_file}")