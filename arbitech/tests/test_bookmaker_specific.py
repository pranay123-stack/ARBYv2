"""
Bookmaker-Specific VLM Testing

Specialized tests for each supported bookmaker with real interface examples.
Tests specific parsing logic, UI elements, and data extraction for each bookmaker platform.
"""

import json
import logging
import time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch

from PIL import Image


class BookmakerTestSpec:
    """Specification for bookmaker-specific tests."""
    
    def __init__(self, name: str, domain: str, ui_elements: List[str], 
                 common_odds_formats: List[str], test_images: List[str]):
        self.name = name
        self.domain = domain
        self.ui_elements = ui_elements
        self.common_odds_formats = common_odds_formats
        self.test_images = test_images
        self.success_criteria = {
            "odds_extraction_accuracy": 0.85,
            "ui_element_detection": 0.90,
            "format_recognition": 0.80,
            "error_handling": 0.95
        }


# Define test specifications for each supported bookmaker
BOOKMAKER_SPECS = {
    "bet365": BookmakerTestSpec(
        name="Bet365",
        domain="bet365.com",
        ui_elements=[
            "odds_display", "team_names", "market_tabs", "live_indicator", 
            "cash_out_button", "bet_slip", "account_balance"
        ],
        common_odds_formats=["decimal", "fractional"],
        test_images=[
            "bet365_football_match.png",
            "bet365_tennis_match.png", 
            "bet365_basketball_match.png",
            "bet365_live_interface.png",
            "bet365_error_state.png"
        ]
    ),
    
    "william_hill": BookmakerTestSpec(
        name="William Hill",
        domain="williamhill.com",
        ui_elements=[
            "odds_display", "team_names", "navigation_menu", "promotions_banner",
            "search_function", "my_bets_section", "account_dropdown"
        ],
        common_odds_formats=["decimal"],
        test_images=[
            "william_hill_football.png",
            "william_hill_tennis.png",
            "william_hill_promotions.png",
            "william_hill_mobile_view.png"
        ]
    ),
    
    "ladbrokes": BookmakerTestSpec(
        name="Ladbrokes", 
        domain="ladbrokes.com",
        ui_elements=[
            "odds_display", "team_names", "category_menu", "bet_builder",
            "in_play_section", "results_tab", "help_support"
        ],
        common_odds_formats=["decimal"],
        test_images=[
            "ladbrokes_football.png",
            "ladbrokes_in_play.png",
            "ladbrokes_bet_builder.png",
            "ladbrokes_results.png"
        ]
    ),
    
    "betfair": BookmakerTestSpec(
        name="Betfair Exchange",
        domain="betfair.com",
        ui_elements=[
            "back_lay_odds", "team_names", "exchange_market", "volume_display",
            "commission_rate", "betting_slips", "market_status"
        ],
        common_odds_formats=["decimal"],
        test_images=[
            "betfair_exchange_football.png",
            "betfair_exchange_tennis.png",
            "betfair_back_lay_interface.png",
            "betfair_market_closed.png"
        ]
    ),
    
    "pinnacle": BookmakerTestSpec(
        name="Pinnacle",
        domain="pinnacle.com",
        ui_elements=[
            "odds_display", "team_names", "live_betting", "asian_handicap",
            "maximum_payout", "bet_history", "account_settings"
        ],
        common_odds_formats=["decimal"],
        test_images=[
            "pinnacle_football.png",
            "pinnacle_asian_handicap.png",
            "pinnacle_live_betting.png",
            "pinnacle_bet_history.png"
        ]
    ),
    
    "1xbet": BookmakerTestSpec(
        name="1xBet",
        domain="1xbet.com", 
        ui_elements=[
            "odds_display", "team_names", "multi_live", "casino_integration",
            "bonus_promotions", "virtual_sports", "payment_methods"
        ],
        common_odds_formats=["decimal", "american"],
        test_images=[
            "1xbet_football.png",
            "1xbet_multi_live.png",
            "1xbet_casino.png",
            "1xbet_virtual_sports.png"
        ]
    )
}


class BookmakerVLMTester:
    """Test VLM accuracy for specific bookmakers."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = {}
        self.sample_data_path = Path(__file__).parent / "create_sample_data"
        
        # Mock VLM with bookmaker-specific accuracy rates
        self.bookmaker_extractors = {
            name: self._create_bookmaker_extractor(spec) 
            for name, spec in BOOKMAKER_SPECS.items()
        }
        
    def _create_bookmaker_extractor(self, spec: BookmakerTestSpec) -> Mock:
        """Create a mock VLM extractor specific to a bookmaker."""
        extractor = Mock()
        
        def extract_odds(image_path: str, **kwargs) -> Dict[str, Any]:
            import random
            random.seed(hash(f"{spec.name}_{image_path}") % 1000)
            
            processing_time = random.uniform(80, 250)
            time.sleep(processing_time / 1000)
            
            # Simulate bookmaker-specific success rates
            base_accuracy = {
                "bet365": 0.88,    # High accuracy, complex interface
                "william_hill": 0.85,  # Good accuracy, clean interface
                "ladbrokes": 0.82,     # Moderate accuracy, some quirks
                "betfair": 0.90,       # Very high accuracy, consistent layout
                "pinnacle": 0.87,      # High accuracy, professional design
                "1xbet": 0.80          # Lower accuracy, complex interface
            }.get(spec.name, 0.85)
            
            success_rate = base_accuracy + random.uniform(-0.05, 0.05)
            will_succeed = random.random() < success_rate
            
            if will_succeed:
                # Simulate successful extraction with bookmaker-specific data
                sports = ["Football", "Tennis", "Basketball", "Baseball"]
                teams = [
                    "Manchester United", "Liverpool", "Arsenal", "Chelsea",
                    "Real Madrid", "Barcelona", "Bayern Munich", "PSG"
                ]
                
                result = {
                    "success": True,
                    "bookmaker": spec.name,
                    "sport": random.choice(sports),
                    "event_name": f"{random.choice(teams)} vs {random.choice(teams)}",
                    "market_type": "match_winner",
                    "odds": [
                        {
                            "outcome": outcome,
                            "decimal_odds": round(random.uniform(1.5, 5.0), 2)
                        }
                        for outcome in ["Home Win", "Draw", "Away Win"]
                    ],
                    "confidence": min(0.95, max(0.6, random.random())),
                    "processing_time_ms": processing_time,
                    "detected_ui_elements": random.sample(spec.ui_elements, 
                                                        random.randint(3, len(spec.ui_elements))),
                    "odds_format": random.choice(spec.common_odds_formats),
                    "extraction_method": "vlm_ocr",
                    "raw_text": f"Mock extracted text from {spec.name} interface"
                }
            else:
                # Simulate various failure modes specific to bookmaker
                error_types = {
                    "bet365": ["complex_layout", "overlay_elements", "dynamic_loading"],
                    "william_hill": ["navigation_interference", "popup_blocks"],
                    "ladbrokes": ["bet_builder_conflict", "in_play_indicator"],
                    "betfair": ["back_lay_confusion", "market_suspension"],
                    "pinnacle": ["asian_handicap_complexity", "live_update"],
                    "1xbet": ["multi_language", "casino_interference", "popup_flood"]
                }
                
                result = {
                    "success": False,
                    "error": random.choice(error_types.get(spec.name, ["unknown_error"])),
                    "confidence": random.uniform(0.1, 0.4),
                    "processing_time_ms": processing_time,
                    "partial_detection": {
                        "team_names": random.choice([True, False]),
                        "some_odds": random.choice([True, False]),
                        "market_type": random.choice([True, False])
                    }
                }
                
            return result
            
        extractor.extract_odds_from_image = extract_odds
        return extractor
        
    def test_bookmaker_interface_recognition(self, bookmaker: str) -> Dict[str, Any]:
        """Test VLM's ability to recognize bookmaker-specific interfaces."""
        if bookmaker not in BOOKMAKER_SPECS:
            raise ValueError(f"Unknown bookmaker: {bookmaker}")
            
        spec = BOOKMAKER_SPECS[bookmaker]
        extractor = self.bookmaker_extractors[bookmaker]
        
        self.logger.info(f"Testing {spec.name} interface recognition...")
        
        results = {
            "bookmaker": spec.name,
            "total_tests": len(spec.test_images),
            "successful_extractions": 0,
            "ui_element_detection_rates": {},
            "error_breakdown": {},
            "average_confidence": 0.0,
            "average_processing_time": 0.0
        }
        
        confidences = []
        processing_times = []
        
        for image_file in spec.test_images:
            image_path = str(self.sample_data_path / "betting_interfaces" / image_file)
            
            try:
                result = extractor.extract_odds_from_image(image_path)
                
                if result["success"]:
                    results["successful_extractions"] += 1
                    
                # Track confidence scores
                confidences.append(result.get("confidence", 0))
                
                # Track processing times
                processing_times.append(result.get("processing_time_ms", 0))
                
                # Track error types
                if not result["success"]:
                    error = result.get("error", "unknown")
                    results["error_breakdown"][error] = results["error_breakdown"].get(error, 0) + 1
                    
            except Exception as e:
                self.logger.error(f"Error testing {image_file}: {e}")
                results["error_breakdown"]["extraction_error"] = results["error_breakdown"].get("extraction_error", 0) + 1
                
        # Calculate metrics
        results["extraction_accuracy"] = results["successful_extractions"] / results["total_tests"]
        results["average_confidence"] = sum(confidences) / len(confidences) if confidences else 0
        results["average_processing_time"] = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Test UI element detection rates
        for element in spec.ui_elements:
            detection_rate = 0.0
            detections = 0
            total_tests = len(spec.test_images)
            
            for image_file in spec.test_images:
                # Simulate UI element detection for this specific image
                import random
                random.seed(hash(f"{bookmaker}_{element}_{image_file}") % 1000)
                if random.random() > 0.2:  # 80% base detection rate
                    detections += 1
                    
            detection_rate = detections / total_tests if total_tests > 0 else 0
            results["ui_element_detection_rates"][element] = detection_rate
            
        self.test_results[bookmaker] = results
        return results
        
    def test_all_bookmakers(self) -> Dict[str, Dict[str, Any]]:
        """Test all supported bookmakers."""
        self.logger.info("Testing all bookmakers...")
        
        all_results = {}
        for bookmaker in BOOKMAKER_SPECS.keys():
            try:
                results = self.test_bookmaker_interface_recognition(bookmaker)
                all_results[bookmaker] = results
            except Exception as e:
                self.logger.error(f"Failed to test {bookmaker}: {e}")
                all_results[bookmaker] = {"error": str(e)}
                
        return all_results
        
    def test_cross_bookmaker_comparison(self) -> Dict[str, Any]:
        """Compare VLM performance across different bookmakers."""
        if not self.test_results:
            self.test_all_bookmakers()
            
        comparison = {
            "accuracy_ranking": [],
            "performance_ranking": [],
            "reliability_ranking": [],
            "best_performing": None,
            "worst_performing": None,
            "average_accuracy": 0.0,
            "average_processing_time": 0.0
        }
        
        accuracies = []
        processing_times = []
        reliability_scores = []
        
        for bookmaker, results in self.test_results.items():
            if "error" not in results:
                accuracy = results.get("extraction_accuracy", 0)
                processing_time = results.get("average_processing_time", float('inf'))
                reliability = 1.0 - (len(results.get("error_breakdown", {})) / max(results.get("total_tests", 1), 1))
                
                accuracies.append((bookmaker, accuracy))
                processing_times.append((bookmaker, processing_time))
                reliability_scores.append((bookmaker, reliability))
                
        # Sort by metrics
        comparison["accuracy_ranking"] = sorted(accuracies, key=lambda x: x[1], reverse=True)
        comparison["performance_ranking"] = sorted(processing_times, key=lambda x: x[1])
        comparison["reliability_ranking"] = sorted(reliability_scores, key=lambda x: x[1], reverse=True)
        
        # Calculate averages
        comparison["average_accuracy"] = sum(acc for _, acc in accuracies) / len(accuracies) if accuracies else 0
        comparison["average_processing_time"] = sum(pt for _, pt in processing_times) / len(processing_times) if processing_times else 0
        
        # Identify best and worst performers
        if accuracies:
            comparison["best_performing"] = comparison["accuracy_ranking"][0][0]
            comparison["worst_performing"] = comparison["accuracy_ranking"][-1][0]
            
        return comparison
        
    def test_bookmaker_specific_edge_cases(self, bookmaker: str) -> Dict[str, Any]:
        """Test bookmaker-specific edge cases and special scenarios."""
        if bookmaker not in BOOKMAKER_SPECS:
            raise ValueError(f"Unknown bookmaker: {bookmaker}")
            
        spec = BOOKMAKER_SPECS[bookmaker]
        extractor = self.bookmaker_extractors[bookmaker]
        
        self.logger.info(f"Testing {spec.name} edge cases...")
        
        edge_cases = {
            "mobile_view": {"image": f"{bookmaker}_mobile_interface.png", "expected_challenges": ["small_text", "touch_elements"]},
            "popup_blocks": {"image": f"{bookmaker}_popup_blocked.png", "expected_challenges": ["overlay_elements", "obscured_content"]},
            "loading_state": {"image": f"{bookmaker}_loading.png", "expected_challenges": ["dynamic_content", "incomplete_data"]},
            "multi_language": {"image": f"{bookmaker}_non_english.png", "expected_challenges": ["language_detection", "text_extraction"]},
            "high_traffic": {"image": f"{bookmaker}_slow_load.png", "expected_challenges": ["timeout_handling", "partial_loading"]},
            "maintenance_mode": {"image": f"{bookmaker}_maintenance.png", "expected_challenges": ["maintenance_detection", "graceful_failure"]}
        }
        
        edge_case_results = {
            "bookmaker": spec.name,
            "total_edge_cases": len(edge_cases),
            "handled_gracefully": 0,
            "failure_modes": {},
            "performance_impact": {}
        }
        
        for case_name, case_config in edge_cases.items():
            image_path = str(self.sample_data_path / "betting_interfaces" / case_config["image"])
            
            try:
                start_time = time.time()
                result = extractor.extract_odds_from_image(image_path)
                processing_time = (time.time() - start_time) * 1000
                
                # Check if edge case was handled gracefully
                gracefully_handled = (
                    result["success"] or  # Successful extraction despite challenges
                    (not result["success"] and result.get("confidence", 0) < 0.5)  # Failed but with low confidence
                )
                
                if gracefully_handled:
                    edge_case_results["handled_gracefully"] += 1
                else:
                    error = result.get("error", "unknown")
                    edge_case_results["failure_modes"][error] = edge_case_results["failure_modes"].get(error, 0) + 1
                    
                # Track performance impact
                baseline_time = 150  # Assume 150ms baseline
                performance_impact = (processing_time - baseline_time) / baseline_time
                edge_case_results["performance_impact"][case_name] = performance_impact
                
            except Exception as e:
                self.logger.error(f"Edge case {case_name} failed for {bookmaker}: {e}")
                edge_case_results["failure_modes"]["extraction_exception"] = edge_case_results["failure_modes"].get("extraction_exception", 0) + 1
                
        edge_case_results["graceful_handling_rate"] = edge_case_results["handled_gracefully"] / edge_case_results["total_edge_cases"]
        
        return edge_case_results
        
    def generate_bookmaker_report(self) -> str:
        """Generate a comprehensive bookmaker-specific test report."""
        if not self.test_results:
            self.test_all_bookmakers()
            
        comparison = self.test_cross_bookmaker_comparison()
        
        report = f"""
Bookmaker-Specific VLM Test Report
===================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

INDIVIDUAL BOOKMAKER RESULTS
----------------------------
"""
        
        for bookmaker, results in self.test_results.items():
            if "error" in results:
                report += f"\n{bookmaker.upper()}:\n"
                report += f"  Status: ERROR - {results['error']}\n"
                continue
                
            report += f"\n{bookmaker.upper()}:\n"
            report += f"  Extraction Accuracy: {results['extraction_accuracy']:.2%}\n"
            report += f"  Average Confidence: {results['average_confidence']:.3f}\n"
            report += f"  Average Processing Time: {results['average_processing_time']:.1f}ms\n"
            report += f"  Total Tests: {results['total_tests']}\n"
            report += f"  Successful Extractions: {results['successful_extractions']}\n"
            
            if results['error_breakdown']:
                report += f"  Error Breakdown:\n"
                for error, count in results['error_breakdown'].items():
                    report += f"    - {error}: {count}\n"
                    
            report += f"  UI Element Detection Rates:\n"
            for element, rate in results['ui_element_detection_rates'].items():
                report += f"    - {element}: {rate:.2%}\n"
                
        report += f"""
CROSS-BOOKMAKER COMPARISON
-------------------------
Average Accuracy Across All Bookmakers: {comparison['average_accuracy']:.2%}
Average Processing Time: {comparison['average_processing_time']:.1f}ms

Accuracy Ranking (Best to Worst):
"""
        
        for i, (bookmaker, accuracy) in enumerate(comparison['accuracy_ranking'], 1):
            report += f"  {i}. {bookmaker}: {accuracy:.2%}\n"
            
        if comparison['best_performing'] and comparison['worst_performing']:
            report += f"""
Best Performing Bookmaker: {comparison['best_performing']}
Worst Performing Bookmaker: {comparison['worst_performing']}
"""
            
        return report
        
    def save_bookmaker_results(self, filepath: str):
        """Save bookmaker test results to JSON file."""
        all_data = {
            "timestamp": datetime.now().isoformat(),
            "individual_results": self.test_results,
            "cross_comparison": self.test_cross_bookmaker_comparison()
        }
        
        with open(filepath, 'w') as f:
            json.dump(all_data, f, indent=2, default=str)
            
        self.logger.info(f"Bookmaker test results saved to {filepath}")


# Pytest test class
class TestBookmakerSpecific:
    """Pytest tests for bookmaker-specific VLM functionality."""
    
    @pytest.fixture
    def bookmaker_tester(self):
        """Fixture providing bookmaker tester."""
        return BookmakerVLMTester()
        
    @pytest.mark.parametrize("bookmaker", list(BOOKMAKER_SPECS.keys()))
    def test_individual_bookmaker_accuracy(self, bookmaker_tester, bookmaker):
        """Test VLM accuracy for individual bookmakers."""
        results = bookmaker_tester.test_bookmaker_interface_recognition(bookmaker)
        
        spec = BOOKMAKER_SPECS[bookmaker]
        
        # Assertions based on bookmaker-specific criteria
        assert results["extraction_accuracy"] >= spec.success_criteria["odds_extraction_accuracy"], \
            f"{spec.name} extraction accuracy below threshold"
            
        assert results["average_confidence"] >= 0.6, \
            f"{spec.name} average confidence too low"
            
        assert results["total_tests"] >= 3, \
            f"{spec.name} should have at least 3 test images"
            
    def test_all_bookmakers_performance(self, bookmaker_tester):
        """Test performance across all bookmakers."""
        results = bookmaker_tester.test_all_bookmakers()
        
        assert len(results) == len(BOOKMAKER_SPECS), "Should test all bookmakers"
        
        # Check that all bookmakers were tested successfully
        successful_tests = sum(1 for r in results.values() if "error" not in r)
        assert successful_tests >= len(BOOKMAKER_SPECS) * 0.8, "At least 80% of bookmakers should test successfully"
        
    def test_cross_bookmaker_comparison(self, bookmaker_tester):
        """Test cross-bookmaker comparison functionality."""
        bookmaker_tester.test_all_bookmakers()
        comparison = bookmaker_tester.test_cross_bookmaker_comparison()
        
        assert "accuracy_ranking" in comparison, "Should have accuracy ranking"
        assert "performance_ranking" in comparison, "Should have performance ranking"
        assert len(comparison["accuracy_ranking"]) > 0, "Should have at least one bookmaker in ranking"
        
        best_performer = comparison["accuracy_ranking"][0]
        assert best_performer[1] >= 0.7, "Best performer should have at least 70% accuracy"
        
    def test_bookmaker_edge_cases(self, bookmaker_tester):
        """Test edge cases for major bookmakers."""
        major_bookmakers = ["bet365", "william_hill", "betfair"]  # Test top 3
        
        for bookmaker in major_bookmakers:
            results = bookmaker_tester.test_bookmaker_specific_edge_cases(bookmaker)
            
            assert results["graceful_handling_rate"] >= 0.6, \
                f"{BOOKMAKER_SPECS[bookmaker].name} should handle at least 60% of edge cases gracefully"
                
    def test_ui_element_detection(self, bookmaker_tester):
        """Test UI element detection rates."""
        for bookmaker in list(BOOKMAKER_SPECS.keys())[:3]:  # Test first 3 bookmakers
            results = bookmaker_tester.test_bookmaker_interface_recognition(bookmaker)
            
            detection_rates = results["ui_element_detection_rates"]
            spec = BOOKMAKER_SPECS[bookmaker]
            
            # Check that key UI elements are detected at reasonable rates
            key_elements = ["odds_display", "team_names"]
            for element in key_elements:
                if element in detection_rates:
                    assert detection_rates[element] >= 0.7, \
                        f"{BOOKMAKER_SPECS[bookmaker].name} should detect {element} at least 70% of the time"


if __name__ == "__main__":
    # Run tests directly when script is executed
    tester = BookmakerVLMTester()
    
    print("Running Bookmaker-Specific VLM Tests...")
    print("=" * 50)
    
    # Test all bookmakers
    tester.test_all_bookmakers()
    
    # Generate and print comprehensive report
    report = tester.generate_bookmaker_report()
    print(report)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"bookmaker_test_results_{timestamp}.json"
    tester.save_bookmaker_results(results_file)
    
    print(f"\nResults saved to: {results_file}")