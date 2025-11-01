"""
Pytest configuration and shared fixtures for ARBITech testing.

This file contains global pytest configuration, fixtures, and utilities
used across all test modules in the ARBITech system.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, MagicMock
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "stress: mark test as stress test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add unit marker to tests in test_*.py files
        if "test_" in item.fspath and "/unit/" in item.fspath:
            item.add_marker(pytest.mark.unit)
        
        # Add integration marker to integration tests
        if "integration" in item.name.lower() or "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that take longer
        if any(keyword in item.name.lower() for keyword in ['stress', 'performance', 'load']):
            item.add_marker(pytest.mark.slow)


# ============================================================================
# GLOBAL TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Global test configuration with all necessary settings."""
    return {
        # Precision settings
        "precision": 10,
        "decimal_precision": 50,
        
        # Odds ranges
        "min_odds": Decimal("1.01"),
        "max_odds": Decimal("1000.0"),
        
        # Test timeouts
        "test_timeout": 30,
        "slow_test_timeout": 120,
        
        # Performance thresholds
        "detection_threshold": 0.1,  # seconds
        "processing_threshold": 1.0,  # seconds
        "memory_threshold_mb": 100,
        
        # Load test settings
        "stress_test_iterations": 1000,
        "load_test_concurrent": 50,
        "load_test_duration": 30,  # seconds
        
        # Quality thresholds
        "min_profit_margin": Decimal("0.01"),
        "min_confidence_score": Decimal("0.8"),
        "max_false_positive_rate": 0.05,
        "min_accuracy_rate": 0.95,
        
        # Mock data settings
        "num_bookmakers": 10,
        "num_events": 50,
        "num_test_scenarios": 20,
        
        # Integration test settings
        "integration_timeout": 60,
        "e2e_timeout": 120,
    }


@pytest.fixture(scope="session")
def test_data_dir():
    """Create and provide test data directory."""
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    return test_data_dir


@pytest.fixture(scope="function")
def temp_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def clean_environment():
    """Ensure clean test environment."""
    # Save current environment
    original_env = os.environ.copy()
    
    # Set test-specific environment variables
    os.environ["ARBITECH_TEST_MODE"] = "true"
    os.environ["ARBITECH_LOG_LEVEL"] = "WARNING"  # Reduce log noise during tests
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# DATA GENERATION FIXTURES
# ============================================================================

@pytest.fixture
def mock_bookmaker_data():
    """Generate realistic mock bookmaker data for testing."""
    def _generate_data(
        num_bookmakers: int = 5,
        num_events: int = 10,
        include_arbitrage: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate mock bookmaker data with optional arbitrage opportunities."""
        import random
        
        data = {}
        
        for bookmaker_id in range(1, num_bookmakers + 1):
            data[f"bookmaker_{bookmaker_id}"] = []
            
            for event_id in range(1, num_events + 1):
                # Generate realistic odds
                home_odds = Decimal(str(random.uniform(1.1, 5.0))).quantize(Decimal("0.01"))
                draw_odds = Decimal(str(random.uniform(2.5, 8.0))).quantize(Decimal("0.01"))
                away_odds = Decimal(str(random.uniform(1.1, 5.0))).quantize(Decimal("0.01"))
                
                # Optionally create arbitrage opportunity
                if include_arbitrage and event_id == 1 and bookmaker_id > 1:
                    # Create arbitrage by making odds slightly better
                    if bookmaker_id == 2:
                        away_odds = Decimal("2.20")  # Better than others
                    elif bookmaker_id == 3:
                        home_odds = Decimal("2.25")  # Better than others
                
                data[f"bookmaker_{bookmaker_id}"].append({
                    "event_id": f"event_{event_id}",
                    "event_name": f"Team {event_id}A vs Team {event_id}B",
                    "sport": random.choice(["Football", "Basketball", "Tennis", "Baseball"]),
                    "market_type": random.choice(["match_winner", "over_under", "handicap"]),
                    "odds": {
                        "home": home_odds,
                        "draw": draw_odds,
                        "away": away_odds,
                    },
                    "timestamp": datetime.now().isoformat(),
                    "status": "active",
                    "confidence": Decimal(str(random.uniform(0.8, 1.0))).quantize(Decimal("0.01")),
                    "last_updated": (datetime.now() - timedelta(seconds=random.randint(1, 300))).isoformat()
                })
        
        return data
    
    return _generate_data


@pytest.fixture
def arbitrage_opportunity():
    """Create a sample arbitrage opportunity for testing."""
    return {
        "event_id": "test_event_123",
        "event_name": "Manchester United vs Liverpool",
        "sport": "Football",
        "market_type": "match_winner",
        "bookmaker_combinations": [
            {
                "bookmaker_1": "bet365",
                "bookmaker_2": "william_hill",
                "selection_1": "home",
                "selection_2": "away",
                "odds_1": Decimal("2.10"),
                "odds_2": Decimal("2.05"),
                "profit_margin": Decimal("0.0251"),
                "expected_profit": Decimal("25.10"),
                "confidence": Decimal("0.95")
            },
            {
                "bookmaker_1": "ladbrokes",
                "bookmaker_2": "betfair",
                "selection_1": "draw",
                "selection_2": "home",
                "odds_1": Decimal("3.20"),
                "odds_2": Decimal("1.85"),
                "profit_margin": Decimal("0.0189"),
                "expected_profit": Decimal("18.90"),
                "confidence": Decimal("0.87")
            }
        ],
        "timestamp": datetime.now(),
        "status": "detected",
        "quality_score": Decimal("0.92"),
        "risk_level": "low",
        "total_stake_required": Decimal("1000.00"),
        "max_profit": Decimal("25.10"),
        "execution_window": 300,  # 5 minutes
        "data_freshness": 45  # seconds
    }


@pytest.fixture
def opportunity_with_risk():
    """Create a higher-risk arbitrage opportunity."""
    return {
        "event_id": "risky_event_456",
        "event_name": "Chelsea vs Arsenal",
        "sport": "Football",
        "market_type": "match_winner",
        "bookmaker_combinations": [
            {
                "bookmaker_1": "unreliable_book",
                "bookmaker_2": "slow_bookmaker",
                "selection_1": "home",
                "selection_2": "away",
                "odds_1": Decimal("2.15"),
                "odds_2": Decimal("2.00"),
                "profit_margin": Decimal("0.0325"),
                "expected_profit": Decimal("32.50"),
                "confidence": Decimal("0.65")  # Lower confidence
            }
        ],
        "timestamp": datetime.now(),
        "status": "detected",
        "quality_score": Decimal("0.65"),
        "risk_level": "high",
        "total_stake_required": Decimal("500.00"),
        "max_profit": Decimal("32.50"),
        "execution_window": 120,  # Shorter window
        "data_freshness": 180,  # Stale data
        "bookmaker_reliability": Decimal("0.70")
    }


@pytest.fixture
def market_data_scenarios():
    """Generate various market data scenarios for testing."""
    scenarios = {
        "clear_arbitrage": {
            "description": "Clear arbitrage opportunity with high profit margin",
            "data": {
                "bookmaker_1": {
                    "event_1": {
                        "odds": {"home": Decimal("2.20"), "away": Decimal("1.85")}
                    }
                },
                "bookmaker_2": {
                    "event_1": {
                        "odds": {"home": Decimal("1.90"), "away": Decimal("2.15")}
                    }
                }
            },
            "expected_opportunities": 1,
            "min_profit_margin": Decimal("0.05")
        },
        
        "marginal_arbitrage": {
            "description": "Marginal arbitrage with small profit margin",
            "data": {
                "bookmaker_1": {
                    "event_1": {
                        "odds": {"home": Decimal("2.01"), "away": Decimal("1.99")}
                    }
                },
                "bookmaker_2": {
                    "event_1": {
                        "odds": {"home": Decimal("1.98"), "away": Decimal("2.02")}
                    }
                }
            },
            "expected_opportunities": 1,
            "min_profit_margin": Decimal("0.001")
        },
        
        "no_arbitrage": {
            "description": "No arbitrage opportunity - standard market",
            "data": {
                "bookmaker_1": {
                    "event_1": {
                        "odds": {"home": Decimal("2.00"), "away": Decimal("1.90")}
                    }
                },
                "bookmaker_2": {
                    "event_1": {
                        "odds": {"home": Decimal("1.95"), "away": Decimal("1.95")}
                    }
                }
            },
            "expected_opportunities": 0,
            "min_profit_margin": Decimal("0.01")
        },
        
        "edge_case_high_odds": {
            "description": "Edge case with very high odds",
            "data": {
                "bookmaker_1": {
                    "event_1": {
                        "odds": {"home": Decimal("50.0"), "away": Decimal("1.02")}
                    }
                },
                "bookmaker_2": {
                    "event_1": {
                        "odds": {"home": Decimal("1.01"), "away": Decimal("55.0")}
                    }
                }
            },
            "expected_opportunities": 1,
            "min_profit_margin": Decimal("0.01")
        },
        
        "live_market": {
            "description": "Live market with rapid changes",
            "data": {
                "bookmaker_1": {
                    "event_1": {
                        "odds": {
                            "home": Decimal("2.10"),
                            "draw": Decimal("3.20"),
                            "away": Decimal("3.50")
                        },
                        "timestamp": datetime.now().isoformat(),
                        "status": "live"
                    }
                },
                "bookmaker_2": {
                    "event_1": {
                        "odds": {
                            "home": Decimal("2.05"),
                            "draw": Decimal("3.30"),
                            "away": Decimal("3.40")
                        },
                        "timestamp": datetime.now().isoformat(),
                        "status": "live"
                    }
                }
            },
            "expected_opportunities": 0,
            "min_profit_margin": Decimal("0.01")
        }
    }
    
    return scenarios


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_supabase_client():
    """Create mock Supabase client for testing."""
    client = Mock()
    client.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": 1, "event_id": "test_event", "odds": "2.10"}
    ]
    client.table.return_value.select.return_value.execute.return_value.data = [
        {"id": 1, "event_id": "test_event", "odds": "2.10"}
    ]
    return client


@pytest.fixture
def mock_vlm_client():
    """Create mock VLM client for testing."""
    client = Mock()
    client.analyze_image.return_value = {
        "text": "Home: 2.10, Draw: 3.20, Away: 3.50",
        "confidence": 0.95,
        "extracted_odds": {
            "home": Decimal("2.10"),
            "draw": Decimal("3.20"),
            "away": Decimal("3.50")
        }
    }
    client.extract_odds.return_value = {
        "home": Decimal("2.10"),
        "draw": Decimal("3.20"),
        "away": Decimal("3.50")
    }
    return client


@pytest.fixture
def mock_browser():
    """Create mock browser for testing."""
    browser = Mock()
    browser.navigate.return_value = None
    browser.take_screenshot.return_value = b"mock_screenshot_data"
    browser.get_page_source.return_value = "<html>mock page</html>"
    browser.find_element.return_value = Mock(text="2.10")
    browser.execute_script.return_value = "script executed"
    return browser


@pytest.fixture
def mock_notification_service():
    """Create mock notification service."""
    service = Mock()
    service.send_email.return_value = {"message_id": "email_123", "status": "sent"}
    service.send_telegram.return_value = {"message_id": "telegram_123", "status": "sent"}
    service.push_dashboard_update.return_value = {"update_id": "dashboard_123", "status": "pushed"}
    return service


# ============================================================================
# PERFORMANCE FIXTURES
# ============================================================================

@pytest.fixture
def performance_monitor():
    """Create performance monitor for benchmarking."""
    import time
    import psutil
    import os
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.checkpoints = []
        
        def start(self):
            """Start monitoring."""
            self.start_time = time.time()
            process = psutil.Process(os.getpid())
            self.start_memory = process.memory_info().rss
        
        def checkpoint(self, name: str):
            """Record a checkpoint."""
            if self.start_time is None:
                self.start()
            
            current_time = time.time()
            process = psutil.Process(os.getpid())
            current_memory = process.memory_info().rss
            
            checkpoint = {
                "name": name,
                "timestamp": current_time,
                "elapsed_time": current_time - self.start_time,
                "memory_usage_mb": (current_memory - self.start_memory) / 1024 / 1024
            }
            self.checkpoints.append(checkpoint)
            return checkpoint
        
        def get_report(self) -> Dict[str, Any]:
            """Get performance report."""
            if not self.checkpoints:
                return {"error": "No checkpoints recorded"}
            
            total_time = self.checkpoints[-1]["elapsed_time"]
            peak_memory = max(c["memory_usage_mb"] for c in self.checkpoints)
            
            return {
                "total_time_seconds": total_time,
                "peak_memory_mb": peak_memory,
                "checkpoints": self.checkpoints,
                "avg_time_per_checkpoint": total_time / len(self.checkpoints)
            }
    
    return PerformanceMonitor()


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def test_logger():
    """Create test-specific logger."""
    logger = logging.getLogger(f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    logger.setLevel(logging.DEBUG)
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    yield logger
    
    # Cleanup
    logger.handlers.clear()


@pytest.fixture
def decimal_precision():
    """Ensure consistent decimal precision for tests."""
    from decimal import getcontext
    
    # Save original precision
    original_precision = getcontext().prec
    
    # Set test precision
    getcontext().prec = 50
    
    yield getcontext().prec
    
    # Restore original precision
    getcontext().prec = original_precision


# ============================================================================
# TEST HELPERS
# ============================================================================

class TestHelpers:
    """Utility functions for tests."""
    
    @staticmethod
    def assert_decimal_almost_equal(actual: Decimal, expected: Decimal, tolerance: Decimal = Decimal("0.01")):
        """Assert two decimal values are almost equal."""
        assert abs(actual - expected) <= tolerance, \
            f"Expected {expected}, got {actual} (diff: {abs(actual - expected)})"
    
    @staticmethod
    def assert_valid_odds(odds: Dict[str, Decimal]):
        """Assert that odds values are valid."""
        for outcome, odd_value in odds.items():
            assert isinstance(odd_value, Decimal), f"Odds must be Decimal, got {type(odd_value)}"
            assert odd_value >= Decimal("1.01"), f"Odds must be >= 1.01, got {odd_value}"
            assert odd_value <= Decimal("1000.0"), f"Odds must be <= 1000.0, got {odd_value}"
    
    @staticmethod
    def assert_valid_arbitrage_opportunity(opportunity: Dict[str, Any]):
        """Assert that opportunity structure is valid."""
        required_fields = [
            "event_id", "event_name", "sport", "market_type",
            "bookmaker_combinations", "timestamp", "status"
        ]
        
        for field in required_fields:
            assert field in opportunity, f"Missing required field: {field}"
        
        assert len(opportunity["bookmaker_combinations"]) > 0, "Must have at least one bookmaker combination"
        
        for combination in opportunity["bookmaker_combinations"]:
            required_combo_fields = ["bookmaker_1", "bookmaker_2", "odds_1", "odds_2", "profit_margin"]
            for field in required_combo_fields:
                assert field in combination, f"Missing combination field: {field}"
            
            assert combination["odds_1"] >= Decimal("1.01"), "Invalid odds_1"
            assert combination["odds_2"] >= Decimal("1.01"), "Invalid odds_2"
            assert combination["profit_margin"] > 0, "Profit margin must be positive"


@pytest.fixture
def helpers():
    """Provide test helpers."""
    return TestHelpers()


# ============================================================================
# CLEANUP FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatically cleanup after each test."""
    # Setup
    yield
    
    # Cleanup
    # Close any mock connections
    # Clear test data
    # Reset global state if needed
    pass
