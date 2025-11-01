"""
Comprehensive Test Suite for ARBITech System

This is the main comprehensive test suite for the entire ARBITech arbitrage trading
system, covering all 9 phases from foundation to notifications.

Features:
- Unit tests for all core components (Phases 1-9)
- Integration tests for cross-phase workflows
- Performance tests with load testing capabilities
- End-to-end tests covering complete arbitrage workflows
- Mock data generation for testing without real money
- Test coverage reporting and CI/CD integration
- Automated regression testing
- Stress testing for high-frequency scenarios

Usage:
    pytest testing/test_suite.py -v
    pytest testing/test_suite.py --e2e
    pytest testing/test_suite.py --performance
    pytest testing/test_suite.py --stress
    pytest testing/test_suite.py --coverage
"""

import pytest
import asyncio
import sys
import os
import time
import json
import random
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal, getcontext

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Set high precision for financial calculations
getcontext().prec = 50

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TEST CONFIGURATION AND FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Global test configuration."""
    return {
        "precision": 10,
        "min_odds": Decimal("1.01"),
        "max_odds": Decimal("100.0"),
        "test_timeout": 30,
        "performance_threshold": 0.1,  # seconds
        "stress_test_iterations": 1000,
        "load_test_concurrent": 50,
    }


@pytest.fixture
def temp_dir():
    """Create temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_bookmaker_data():
    """Generate mock bookmaker data for testing."""
    def _generate_data(num_bookmakers=5, num_events=10):
        data = {}
        for bookmaker in range(1, num_bookmakers + 1):
            data[f"bookmaker_{bookmaker}"] = []
            for event in range(1, num_events + 1):
                # Generate random odds
                home_odds = Decimal(str(random.uniform(1.1, 5.0))).quantize(Decimal("0.01"))
                draw_odds = Decimal(str(random.uniform(2.5, 8.0))).quantize(Decimal("0.01"))
                away_odds = Decimal(str(random.uniform(1.1, 5.0))).quantize(Decimal("0.01"))
                
                data[f"bookmaker_{bookmaker}"].append({
                    "event_id": f"event_{event}",
                    "event_name": f"Team {event}A vs Team {event}B",
                    "sport": "Football",
                    "market_type": "match_winner",
                    "odds": {
                        "home": home_odds,
                        "draw": draw_odds,
                        "away": away_odds,
                    },
                    "timestamp": datetime.now().isoformat(),
                    "status": "active"
                })
        return data
    
    return _generate_data


@pytest.fixture
def arbitrage_opportunity():
    """Create a sample arbitrage opportunity."""
    return {
        "event_id": "test_event_1",
        "event_name": "Team A vs Team B",
        "sport": "Football",
        "market_type": "match_winner",
        "bookmaker_combinations": [
            {
                "bookmaker_1": "bookmaker_1",
                "bookmaker_2": "bookmaker_2",
                "selection_1": "home",
                "selection_2": "away",
                "odds_1": Decimal("2.10"),
                "odds_2": Decimal("2.05"),
                "profit_margin": Decimal("0.0251"),
                "expected_profit": Decimal("25.10")
            }
        ],
        "timestamp": datetime.now(),
        "confidence": Decimal("0.95"),
        "status": "detected"
    }


# ============================================================================
# PHASE 1: FOUNDATION & INFRASTRUCTURE TESTS
# ============================================================================

class TestPhase1Foundation:
    """Test Phase 1: Foundation & Infrastructure Setup."""
    
    def test_config_manager_loading(self, test_config):
        """Test configuration management system."""
        from core.config_manager import ConfigManager
        
        # Test loading default configuration
        config_manager = ConfigManager()
        
        # Verify core sections exist
        assert "system" in config_manager.config
        assert "logging" in config_manager.config
        assert "database" in config_manager.config
        
        # Test configuration validation
        assert config_manager.validate_config()
        
        # Test configuration updates
        config_manager.update_config({"test": "value"})
        assert config_manager.config["test"] == "value"
    
    def test_math_helpers_accuracy(self, test_config):
        """Test mathematical utility functions."""
        from utils.math_helpers import (
            calculate_implied_probability,
            calculate_arbitrage_profit,
            find_arbitrage_opportunities
        )
        
        # Test implied probability calculation
        odds = Decimal("2.00")
        prob = calculate_implied_probability(odds)
        assert abs(prob - Decimal("0.5")) < Decimal("0.001")
        
        # Test arbitrage profit calculation
        stake = Decimal("100")
        odds1 = Decimal("2.10")
        odds2 = Decimal("2.05")
        
        profit, total_stake = calculate_arbitrage_profit(stake, odds1, odds2)
        assert profit > 0
        assert total_stake > 0
        
        # Test finding arbitrage opportunities
        markets = {
            "bookmaker1": {"home": Decimal("2.10"), "away": Decimal("1.95")},
            "bookmaker2": {"home": Decimal("1.90"), "away": Decimal("2.15")}
        }
        
        opportunities = find_arbitrage_opportunities(markets)
        assert len(opportunities) > 0
    
    def test_input_validation(self):
        """Test input validation utilities."""
        from utils.validation import (
            validate_odds,
            validate_stake_amount,
            validate_event_data
        )
        
        # Test odds validation
        assert validate_odds(Decimal("2.00")) == True
        assert validate_odds(Decimal("1.01")) == True
        assert validate_odds(Decimal("1000")) == True
        assert validate_odds(Decimal("0.99")) == False
        assert validate_odds(Decimal("0")) == False
        
        # Test stake validation
        assert validate_stake_amount(Decimal("100")) == True
        assert validate_stake_amount(Decimal("0")) == False
        assert validate_stake_amount(Decimal("-100")) == False
        
        # Test event data validation
        event_data = {
            "event_id": "test",
            "event_name": "Test Event",
            "sport": "Football",
            "market_type": "match_winner"
        }
        assert validate_event_data(event_data) == True
    
    def test_logging_system(self):
        """Test centralized logging system."""
        from utils.logger import setup_logging
        
        # Test logging setup
        logger = setup_logging("test", level="DEBUG")
        assert logger is not None
        
        # Test logging functionality
        logger.info("Test log message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        # Verify log levels work
        assert logger.level == logging.DEBUG


# ============================================================================
# PHASE 2: VISION LANGUAGE MODEL TESTS
# ============================================================================

class TestPhase2VLM:
    """Test Phase 2: Vision Language Model Integration."""
    
    def test_odds_extraction_mock(self):
        """Test VLM odds extraction with mock interface."""
        from vlm.odds_extractor import OddsExtractor
        
        extractor = OddsExtractor()
        
        # Mock interface data
        mock_interface = {
            "html_content": """
            <div class="odds-container">
                <span class="home-odds">2.10</span>
                <span class="draw-odds">3.20</span>
                <span class="away-odds">3.50</span>
            </div>
            """,
            "image_screenshot": b"mock_image_data"
        }
        
        # Test extraction
        odds_data = extractor.extract_odds(mock_interface)
        
        assert odds_data is not None
        assert "home" in odds_data
        assert "draw" in odds_data
        assert "away" in odds_data
        
        # Verify odds values
        assert odds_data["home"] == Decimal("2.10")
        assert odds_data["draw"] == Decimal("3.20")
        assert odds_data["away"] == Decimal("3.50")
    
    def test_qwen_vl_client_mock(self):
        """Test Qwen VLM client with mocked responses."""
        from vlm.qwen_vl_client import QwenVLClient
        
        client = QwenVLClient()
        
        # Mock API response
        mock_response = {
            "text": "2.10, 3.20, 3.50",
            "confidence": 0.95
        }
        
        with patch.object(client, 'analyze_image') as mock_analyze:
            mock_analyze.return_value = mock_response
            
            result = client.analyze_image(b"mock_image")
            
            assert result is not None
            assert "text" in result
            assert result["confidence"] > 0.8
    
    def test_error_recovery_mechanism(self):
        """Test VLM error recovery and retry logic."""
        from vlm.error_recovery import ErrorRecovery
        
        recovery = ErrorRecovery(max_retries=3, backoff_factor=0.5)
        
        # Test retry mechanism
        call_count = 0
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = recovery.retry_with_backoff(failing_function)
        assert result == "success"
        assert call_count == 3
    
    def test_retry_logic(self):
        """Test retry logic for VLM operations."""
        from vlm.retry_logic import RetryLogic
        
        retry_logic = RetryLogic(max_attempts=3, delay=0.1)
        
        # Test successful operation
        result = retry_logic.execute(lambda: "success")
        assert result == "success"
        
        # Test with failures
        attempts = []
        def failing_operation():
            attempts.append(1)
            if len(attempts) < 3:
                raise Exception("Failed")
            return "eventual_success"
        
        result = retry_logic.execute(failing_operation)
        assert result == "eventual_success"
        assert len(attempts) == 3


# ============================================================================
# PHASE 3: ARBITRAGE DETECTION ENGINE TESTS
# ============================================================================

class TestPhase3ArbitrageDetection:
    """Test Phase 3: Arbitrage Detection Engine."""
    
    def test_opportunity_scanner(self, mock_bookmaker_data):
        """Test arbitrage opportunity scanner."""
        from detection.opportunity_scanner import OpportunityScanner
        
        scanner = OpportunityScanner(min_profit_margin=Decimal("0.01"))
        
        # Generate test data
        test_data = mock_bookmaker_data(num_bookmakers=3, num_events=5)
        
        # Scan for opportunities
        opportunities = scanner.scan_opportunities(test_data)
        
        assert isinstance(opportunities, list)
        # Should find some opportunities with the test data
        
    def test_mathematical_engine(self):
        """Test mathematical calculations engine."""
        from detection.arbitrage_math import (
            calculate_implied_probabilities,
            check_arbitrage_condition,
            calculate_optimal_stakes
        )
        
        # Test probability calculation
        odds = [Decimal("2.10"), Decimal("3.20"), Decimal("3.50")]
        probabilities = calculate_implied_probabilities(odds)
        
        assert len(probabilities) == 3
        assert all(0 < p <= 1 for p in probabilities)
        
        # Test arbitrage condition check
        has_arbitrage = check_arbitrage_condition(probabilities)
        assert isinstance(has_arbitrage, bool)
        
        # Test optimal stake calculation
        if has_arbitrage:
            stakes = calculate_optimal_stakes(odds)
            assert len(stakes) == 3
            assert all(s > 0 for s in stakes)
    
    def test_market_data_store(self):
        """Test market data storage and retrieval."""
        from detection.market_data_store import MarketDataStore
        
        store = MarketDataStore()
        
        # Test data storage
        test_data = {
            "event_id": "test_event",
            "odds": {"home": Decimal("2.10"), "away": Decimal("1.95")},
            "timestamp": datetime.now()
        }
        
        store.store_odds_data("bookmaker1", test_data)
        
        # Test data retrieval
        retrieved_data = store.get_odds_data("bookmaker1", "test_event")
        assert retrieved_data is not None
        
        # Test data aggregation
        all_data = store.get_all_data()
        assert "bookmaker1" in all_data
    
    def test_scanner_engine(self):
        """Test main scanner engine."""
        from detection.scanner_engine import ScannerEngine
        
        engine = ScannerEngine()
        
        # Test configuration
        assert engine.min_profit_margin > 0
        assert engine.max_response_time > 0
        
        # Test scanning capabilities
        assert hasattr(engine, 'scan_markets')
        assert hasattr(engine, 'filter_opportunities')
        
    def test_profit_calculator(self):
        """Test profit calculation functionality."""
        from detection.profit_calculator import ProfitCalculator
        
        calculator = ProfitCalculator()
        
        # Test basic profit calculation
        odds = [Decimal("2.10"), Decimal("2.05")]
        total_stake = Decimal("100")
        
        profit, breakdown = calculator.calculate_arbitrage_profit(
            odds, total_stake
        )
        
        assert profit > 0
        assert len(breakdown) == 2
        assert all(s > 0 for s in breakdown.values())
    
    def test_quality_scorer(self):
        """Test opportunity quality scoring."""
        from detection.quality_scorer import QualityScorer
        
        scorer = QualityScorer()
        
        # Create test opportunity
        opportunity = {
            "profit_margin": Decimal("0.05"),
            "confidence": Decimal("0.9"),
            "bookmaker_reliability": Decimal("0.95"),
            "data_freshness": 30  # seconds
        }
        
        score = scorer.calculate_quality_score(opportunity)
        assert 0 <= score <= 1


# ============================================================================
# PHASE 4: RISK MANAGEMENT SYSTEM TESTS
# ============================================================================

class TestPhase4RiskManagement:
    """Test Phase 4: Risk Management System."""
    
    def test_bankroll_manager(self):
        """Test bankroll management functionality."""
        from risk.bankroll_manager import BankrollManager
        
        manager = BankrollManager(initial_bankroll=Decimal("1000"))
        
        # Test bankroll initialization
        assert manager.get_current_bankroll() == Decimal("1000")
        
        # Test stake calculation
        stake = manager.calculate_stake(
            bankroll_percentage=Decimal("0.02"),
            odds=Decimal("2.0")
        )
        assert stake == Decimal("20")
        
        # Test bankroll updates
        manager.update_bankroll(Decimal("-50"))  # Loss
        assert manager.get_current_bankroll() == Decimal("950")
        
        manager.update_bankroll(Decimal("100"))  # Win
        assert manager.get_current_bankroll() == Decimal("1050")
    
    def test_kelly_calculator(self):
        """Test Kelly Criterion calculations."""
        from risk.kelly_calculator import KellyCalculator
        
        calculator = KellyCalculator()
        
        # Test Kelly calculation
        win_probability = Decimal("0.55")
        odds = Decimal("2.0")
        
        kelly_fraction = calculator.calculate_kelly_fraction(
            win_probability, odds
        )
        
        assert 0 <= kelly_fraction <= 1
        
        # Test conservative Kelly
        conservative_kelly = calculator.calculate_conservative_kelly(
            win_probability, odds, risk_factor=Decimal("0.5")
        )
        
        assert conservative_kelly <= kelly_fraction
    
    def test_loss_limiter(self):
        """Test loss limiting functionality."""
        from risk.loss_limiter import LossLimiter
        
        limiter = LossLimiter(max_daily_loss=Decimal("100"), max_loss_percentage=0.05)
        
        # Test daily loss tracking
        assert not limiter.should_stop_trading()  # No losses yet
        
        # Add losses
        limiter.record_loss(Decimal("50"))
        assert not limiter.should_stop_trading()
        
        limiter.record_loss(Decimal("60"))  # Total 110 > 100
        assert limiter.should_stop_trading()
    
    def test_position_sizer(self):
        """Test position sizing calculations."""
        from risk.position_sizer import PositionSizer
        
        sizer = PositionSizer()
        
        # Test position sizing
        bankroll = Decimal("1000")
        risk_per_trade = Decimal("0.02")
        odds = Decimal("2.0")
        
        position_size = sizer.calculate_position_size(
            bankroll, risk_per_trade, odds
        )
        
        assert position_size > 0
        assert position_size <= bankroll * risk_per_trade
    
    def test_safety_monitor(self):
        """Test safety monitoring system."""
        from risk.safety_monitor import SafetyMonitor
        
        monitor = SafetyMonitor()
        
        # Test risk assessment
        opportunity = {
            "profit_margin": Decimal("0.05"),
            "stake_amount": Decimal("100"),
            "bookmaker_risk": Decimal("0.1")
        }
        
        risk_level = monitor.assess_risk_level(opportunity)
        assert risk_level in ["low", "medium", "high"]
        
        # Test safety checks
        safety_passed = monitor.check_safety_conditions(opportunity)
        assert isinstance(safety_passed, bool)
    
    def test_risk_analyzer(self):
        """Test comprehensive risk analysis."""
        from risk.risk_analyzer import RiskAnalyzer
        
        analyzer = RiskAnalyzer()
        
        # Test portfolio risk analysis
        opportunities = [
            {
                "stake_amount": Decimal("100"),
                "profit_margin": Decimal("0.03"),
                "correlation": Decimal("0.5")
            },
            {
                "stake_amount": Decimal("50"),
                "profit_margin": Decimal("0.02"),
                "correlation": Decimal("0.3")
            }
        ]
        
        risk_metrics = analyzer.analyze_portfolio_risk(opportunities)
        
        assert "total_exposure" in risk_metrics
        assert "diversification_score" in risk_metrics
        assert "risk_score" in risk_metrics


# ============================================================================
# PHASE 5: BROWSER AUTOMATION TESTS
# ============================================================================

class TestPhase5BrowserAutomation:
    """Test Phase 5: Browser Automation & AVO Integration."""
    
    def test_enhanced_browser_mock(self):
        """Test enhanced browser functionality with mocks."""
        from automation.enhanced_browser import EnhancedBrowser
        
        browser = EnhancedBrowser(headless=True)
        
        # Test browser initialization
        assert browser is not None
        
        # Mock navigation
        with patch.object(browser, 'navigate') as mock_navigate:
            browser.navigate("https://example.com")
            mock_navigate.assert_called_once_with("https://example.com")
        
        # Mock screenshot
        with patch.object(browser, 'take_screenshot') as mock_screenshot:
            mock_screenshot.return_value = b"mock_screenshot"
            screenshot = browser.take_screenshot()
            assert screenshot == b"mock_screenshot"
    
    def test_tab_coordinator(self):
        """Test tab coordination functionality."""
        from automation.tab_coordinator import TabCoordinator
        
        coordinator = TabCoordinator()
        
        # Test tab management
        tab_id = coordinator.create_tab("https://example1.com")
        assert tab_id is not None
        
        # Test tab switching
        coordinator.switch_to_tab(tab_id)
        
        # Test tab closure
        coordinator.close_tab(tab_id)
    
    def test_trade_coordinator(self):
        """Test trade coordination functionality."""
        from automation.trade_coordinator import TradeCoordinator
        
        coordinator = TradeCoordinator()
        
        # Test trade preparation
        trade_data = {
            "bookmaker": "test_bookmaker",
            "selection": "home",
            "stake": Decimal("100"),
            "odds": Decimal("2.10")
        }
        
        preparation = coordinator.prepare_trade(trade_data)
        assert preparation["status"] in ["ready", "needs_confirmation"]
        
        # Test trade execution (mock)
        with patch.object(coordinator, 'execute_trade') as mock_execute:
            mock_execute.return_value = {"success": True, "confirmation_id": "test_123"}
            
            result = coordinator.execute_trade(trade_data)
            assert result["success"] is True
    
    def test_execution_tracker(self):
        """Test trade execution tracking."""
        from automation.execution_tracker import ExecutionTracker
        
        tracker = ExecutionTracker()
        
        # Test trade tracking
        trade_id = tracker.start_tracking({
            "stake": Decimal("100"),
            "expected_profit": Decimal("5")
        })
        
        assert trade_id is not None
        
        # Test status updates
        tracker.update_status(trade_id, "placed")
        status = tracker.get_status(trade_id)
        assert status["status"] == "placed"
    
    def test_browser_security(self):
        """Test browser security features."""
        from automation.browser_security import BrowserSecurity
        
        security = BrowserSecurity()
        
        # Test security checks
        result = security.perform_security_scan()
        assert result["status"] in ["safe", "warning", "blocked"]
        
        # Test blocked content detection
        blocked = security.is_content_blocked("malicious_script.js")
        assert isinstance(blocked, bool)


# ============================================================================
# PHASE 6: HITL MODE TESTS
# ============================================================================

class TestPhase6HITL:
    """Test Phase 6: Human-In-The-Loop Mode."""
    
    def test_approval_workflow(self):
        """Test approval workflow functionality."""
        from hitl.approval_workflow import ApprovalWorkflow
        
        workflow = ApprovalWorkflow()
        
        # Create approval request
        request = {
            "opportunity_id": "test_123",
            "profit_margin": Decimal("0.05"),
            "stake_amount": Decimal("100"),
            "bookmaker": "test_bookmaker"
        }
        
        approval_id = workflow.create_approval_request(request)
        assert approval_id is not None
        
        # Test approval
        result = workflow.process_approval(approval_id, approve=True)
        assert result["status"] in ["approved", "rejected"]
    
    def test_opportunity_presenter(self):
        """Test opportunity presentation system."""
        from hitl.opportunity_presenter import OpportunityPresenter
        
        presenter = OpportunityPresenter()
        
        # Test opportunity formatting
        opportunity = {
            "event_name": "Team A vs Team B",
            "profit_margin": Decimal("0.05"),
            "expected_profit": Decimal("5"),
            "bookmaker_combinations": []
        }
        
        formatted = presenter.format_opportunity(opportunity)
        assert "event_name" in formatted
        assert "profit_margin" in formatted
        assert formatted["profit_margin"] == Decimal("0.05")
    
    def test_timeout_manager(self):
        """Test timeout management for approvals."""
        from hitl.timeout_manager import TimeoutManager
        
        manager = TimeoutManager(default_timeout=30)
        
        # Test timeout setting
        timeout_id = manager.set_timeout("test_approval", 30)
        assert timeout_id is not None
        
        # Test timeout checking
        is_expired = manager.is_expired(timeout_id)
        assert isinstance(is_expired, bool)
        
        # Test timeout cancellation
        manager.cancel_timeout(timeout_id)
    
    def test_execution_orchestrator(self):
        """Test execution orchestration."""
        from hitl.execution_orchestrator import ExecutionOrchestrator
        
        orchestrator = ExecutionOrchestrator()
        
        # Test execution planning
        plan = orchestrator.create_execution_plan({
            "opportunity_id": "test_123",
            "legs": [
                {"bookmaker": "bm1", "selection": "home", "stake": Decimal("50")},
                {"bookmaker": "bm2", "selection": "away", "stake": Decimal("50")}
            ]
        })
        
        assert "execution_order" in plan
        assert len(plan["execution_order"]) == 2


# ============================================================================
# PHASE 7: AUTONOMOUS MODE TESTS
# ============================================================================

class TestPhase7Autonomous:
    """Test Phase 7: Autonomous Mode & Safety."""
    
    def test_decision_engine(self):
        """Test autonomous decision making engine."""
        from autonomous.decision_engine import DecisionEngine
        
        engine = DecisionEngine()
        
        # Test opportunity evaluation
        opportunity = {
            "profit_margin": Decimal("0.05"),
            "confidence": Decimal("0.9"),
            "stake_amount": Decimal("100"),
            "bookmaker_risk": Decimal("0.1")
        }
        
        decision = engine.evaluate_opportunity(opportunity)
        assert decision["action"] in ["execute", "reject", "review"]
        assert "confidence" in decision
        assert "reasoning" in decision
    
    def test_circuit_breaker(self):
        """Test circuit breaker for safety."""
        from autonomous.circuit_breakers import CircuitBreaker
        
        circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        
        # Test normal operation
        assert circuit_breaker.state == "closed"
        
        # Test failure tracking
        for i in range(5):
            circuit_breaker.record_failure()
        
        assert circuit_breaker.state == "open"
        
        # Test recovery (mock time)
        with patch('time.time', return_value=time.time() + 100):
            circuit_breaker.check_state()
            assert circuit_breaker.state == "half_open"
    
    def test_monitoring_control(self):
        """Test monitoring and control systems."""
        from autonomous.monitoring_control import MonitoringControl
        
        control = MonitoringControl()
        
        # Test system health check
        health_status = control.check_system_health()
        assert "status" in health_status
        assert health_status["status"] in ["healthy", "warning", "critical"]
        
        # Test emergency stop
        emergency_stopped = control.trigger_emergency_stop("Test emergency")
        assert isinstance(emergency_stopped, bool)
    
    def test_concurrent_executor(self):
        """Test concurrent execution capabilities."""
        from autonomous.concurrent_executor import ConcurrentExecutor
        
        executor = ConcurrentExecutor(max_workers=4)
        
        # Test task execution
        def test_task(x):
            return x * 2
        
        # Submit multiple tasks
        futures = []
        for i in range(10):
            future = executor.submit_task(test_task, i)
            futures.append(future)
        
        # Wait for completion
        results = executor.wait_for_completion(futures, timeout=5)
        assert len(results) == 10
        assert all(result == i * 2 for i, result in enumerate(results))
    
    def test_tier_a_executor(self):
        """Test Tier A execution system."""
        from autonomous.tier_a_executor import TierAExecutor
        
        executor = TierAExecutor()
        
        # Test execution criteria
        opportunity = {
            "profit_margin": Decimal("0.03"),
            "confidence": Decimal("0.95"),
            "bookmaker_reliability": Decimal("0.98")
        }
        
        can_execute = executor.can_execute_tier_a(opportunity)
        assert isinstance(can_execute, bool)


# ============================================================================
# PHASE 8: DATA STORAGE TESTS
# ============================================================================

class TestPhase8DataStorage:
    """Test Phase 8: Data Storage & Supabase Integration."""
    
    @pytest.mark.skipif(not os.getenv("SUPABASE_URL"), reason="Supabase credentials not available")
    def test_supabase_connection(self):
        """Test Supabase database connection."""
        from storage.supabase_layer import SupabaseLayer
        
        layer = SupabaseLayer()
        
        # Test connection
        assert layer.client is not None
        
        # Test basic query
        result = layer.test_connection()
        assert isinstance(result, bool)
    
    def test_audit_logger(self):
        """Test audit logging functionality."""
        from storage.audit_logger import AuditLogger
        
        logger = AuditLogger()
        
        # Test logging trade
        trade_log = {
            "trade_id": "test_123",
            "action": "execute",
            "details": {"stake": "100", "profit": "5"}
        }
        
        log_id = logger.log_trade(trade_log)
        assert log_id is not None
        
        # Test logging system event
        event_log = {
            "event_type": "system_start",
            "severity": "info",
            "message": "System started successfully"
        }
        
        log_id = logger.log_system_event(event_log)
        assert log_id is not None
    
    def test_data_models(self):
        """Test data model structures."""
        from storage.models import (
            ArbitrageOpportunity,
            TradeExecution,
            SystemEvent,
            AuditLog
        )
        
        # Test ArbitrageOpportunity model
        opportunity = ArbitrageOpportunity(
            event_id="test_123",
            profit_margin=Decimal("0.05"),
            expected_profit=Decimal("5.00")
        )
        
        assert opportunity.event_id == "test_123"
        assert opportunity.profit_margin == Decimal("0.05")
        
        # Test TradeExecution model
        trade = TradeExecution(
            trade_id="trade_123",
            opportunity_id="op_123",
            status="executed"
        )
        
        assert trade.trade_id == "trade_123"
        assert trade.status == "executed"


# ============================================================================
# PHASE 9: NOTIFICATION SYSTEM TESTS
# ============================================================================

class TestPhase9Notifications:
    """Test Phase 9: Notification System."""
    
    def test_email_notifications(self):
        """Test email notification system."""
        from notifications.email_notifications import EmailNotification
        
        notifier = EmailNotification()
        
        # Test email composition
        email_data = {
            "to": "test@example.com",
            "subject": "Test Notification",
            "body": "This is a test notification"
        }
        
        email_id = notifier.send_notification(email_data)
        assert email_id is not None
    
    def test_telegram_bot(self):
        """Test Telegram bot functionality."""
        from notifications.telegram_bot import TelegramBot
        
        bot = TelegramBot()
        
        # Test message sending
        message = {
            "chat_id": "test_chat",
            "text": "Test message from bot"
        }
        
        message_id = bot.send_message(message)
        assert message_id is not None
    
    def test_notification_filters(self):
        """Test notification filtering."""
        from notifications.notification_filters import NotificationFilter
        
        filter_system = NotificationFilter()
        
        # Test filter application
        notification = {
            "type": "opportunity",
            "profit_margin": Decimal("0.05"),
            "priority": "high"
        }
        
        should_send = filter_system.should_send_notification(notification)
        assert isinstance(should_send, bool)
    
    def test_multi_channel_delivery(self):
        """Test multi-channel notification delivery."""
        from notifications.multi_channel_delivery import MultiChannelDelivery
        
        delivery = MultiChannelDelivery()
        
        # Test channel selection
        notification = {
            "type": "urgent_alert",
            "channels": ["email", "telegram"]
        }
        
        selected_channels = delivery.select_channels(notification)
        assert len(selected_channels) > 0
        assert all(ch in ["email", "telegram", "dashboard"] for ch in selected_channels)
    
    def test_dashboard_updates(self):
        """Test dashboard update functionality."""
        from notifications.dashboard_updates import DashboardUpdates
        
        updater = DashboardUpdates()
        
        # Test dashboard notification
        update_data = {
            "type": "opportunity_detected",
            "data": {"profit_margin": "5%", "event": "Team A vs B"}
        }
        
        update_id = updater.push_update(update_data)
        assert update_id is not None


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegrationCrossPhase:
    """Integration tests for cross-phase workflows."""
    
    def test_detection_to_risk_workflow(self, mock_bookmaker_data):
        """Test integration from detection to risk management."""
        from detection.opportunity_scanner import OpportunityScanner
        from risk.risk_analyzer import RiskAnalyzer
        
        # Generate test data
        test_data = mock_bookmaker_data(num_bookmakers=3, num_events=5)
        
        # Scan for opportunities
        scanner = OpportunityScanner(min_profit_margin=Decimal("0.01"))
        opportunities = scanner.scan_opportunities(test_data)
        
        if opportunities:
            # Analyze risk
            analyzer = RiskAnalyzer()
            risk_metrics = analyzer.analyze_portfolio_risk(opportunities)
            
            assert "total_exposure" in risk_metrics
            assert "risk_score" in risk_metrics
    
    def test_vlm_to_detection_workflow(self):
        """Test integration from VLM to detection."""
        from vlm.odds_extractor import OddsExtractor
        from detection.opportunity_scanner import OpportunityScanner
        
        # Mock VLM extracted data
        vlm_data = {
            "bookmaker1": {
                "event_1": {"home": Decimal("2.10"), "away": Decimal("1.95")}
            },
            "bookmaker2": {
                "event_1": {"home": Decimal("1.90"), "away": Decimal("2.15")}
            }
        }
        
        # Detect opportunities
        scanner = OpportunityScanner(min_profit_margin=Decimal("0.01"))
        opportunities = scanner.scan_opportunities(vlm_data)
        
        assert isinstance(opportunities, list)
    
    def test_hitl_to_automation_workflow(self, arbitrage_opportunity):
        """Test integration from HITL to automation."""
        from hitl.approval_workflow import ApprovalWorkflow
        from automation.trade_coordinator import TradeCoordinator
        
        # Create approval request
        workflow = ApprovalWorkflow()
        approval_id = workflow.create_approval_request(arbitrage_opportunity)
        
        # Simulate approval
        approval_result = workflow.process_approval(approval_id, approve=True)
        
        if approval_result["status"] == "approved":
            # Prepare for automation
            coordinator = TradeCoordinator()
            trade_data = {
                "bookmaker": "test_bookmaker",
                "selection": "home",
                "stake": Decimal("100"),
                "odds": Decimal("2.10")
            }
            
            preparation = coordinator.prepare_trade(trade_data)
            assert preparation["status"] in ["ready", "needs_confirmation"]
    
    def test_autonomous_to_storage_workflow(self, arbitrage_opportunity):
        """Test integration from autonomous to storage."""
        from autonomous.decision_engine import DecisionEngine
        from storage.audit_logger import AuditLogger
        
        # Make autonomous decision
        engine = DecisionEngine()
        decision = engine.evaluate_opportunity(arbitrage_opportunity)
        
        if decision["action"] == "execute":
            # Log the decision
            logger = AuditLogger()
            log_entry = {
                "event_type": "autonomous_execution",
                "decision": decision,
                "opportunity": arbitrage_opportunity
            }
            
            log_id = logger.log_system_event(log_entry)
            assert log_id is not None
    
    def test_notification_workflow(self, arbitrage_opportunity):
        """Test notification system integration."""
        from notifications.multi_channel_delivery import MultiChannelDelivery
        from notifications.notification_filters import NotificationFilter
        
        # Apply notification filters
        filter_system = NotificationFilter()
        should_notify = filter_system.should_send_notification({
            "type": "opportunity",
            "profit_margin": arbitrage_opportunity["bookmaker_combinations"][0]["profit_margin"],
            "priority": "high"
        })
        
        if should_notify:
            # Deliver notifications
            delivery = MultiChannelDelivery()
            channels = delivery.select_channels({
                "type": "opportunity",
                "priority": "high"
            })
            
            assert len(channels) > 0


# ============================================================================
# END-TO-END TESTS
# ============================================================================

class TestEndToEndWorkflows:
    """End-to-end tests for complete arbitrage workflows."""
    
    @pytest.mark.e2e
    def test_complete_arbitrage_workflow(self, mock_bookmaker_data):
        """Test complete arbitrage detection to execution workflow."""
        # This test simulates a complete workflow without actual betting
        from detection.opportunity_scanner import OpportunityScanner
        from risk.risk_analyzer import RiskAnalyzer
        from autonomous.decision_engine import DecisionEngine
        from notifications.multi_channel_delivery import MultiChannelDelivery
        
        # Step 1: Generate market data
        market_data = mock_bookmaker_data(num_bookmakers=5, num_events=10)
        
        # Step 2: Detect opportunities
        scanner = OpportunityScanner(min_profit_margin=Decimal("0.01"))
        opportunities = scanner.scan_opportunities(market_data)
        
        if opportunities:
            # Step 3: Analyze risk
            analyzer = RiskAnalyzer()
            risk_metrics = analyzer.analyze_portfolio_risk(opportunities)
            
            # Step 4: Make autonomous decision
            engine = DecisionEngine()
            decision = engine.evaluate_opportunity(opportunities[0])
            
            # Step 5: Send notification if approved
            if decision["action"] == "execute":
                delivery = MultiChannelDelivery()
                channels = delivery.select_channels({
                    "type": "execution_approved",
                    "opportunity": opportunities[0]
                })
                
                assert len(channels) > 0
    
    @pytest.mark.e2e
    def test_hitl_complete_workflow(self, arbitrage_opportunity):
        """Test complete HITL workflow from detection to execution."""
        from hitl.approval_workflow import ApprovalWorkflow
        from automation.trade_coordinator import TradeCoordinator
        from storage.audit_logger import AuditLogger
        
        # Step 1: Create approval request
        workflow = ApprovalWorkflow()
        approval_id = workflow.create_approval_request(arbitrage_opportunity)
        
        # Step 2: Process approval (simulate user approval)
        approval_result = workflow.process_approval(approval_id, approve=True)
        
        if approval_result["status"] == "approved":
            # Step 3: Coordinate trades
            coordinator = TradeCoordinator()
            
            for leg in arbitrage_opportunity["bookmaker_combinations"]:
                trade_data = {
                    "bookmaker": leg["bookmaker_1"],
                    "selection": leg["selection_1"],
                    "stake": Decimal("100"),
                    "odds": leg["odds_1"]
                }
                
                preparation = coordinator.prepare_trade(trade_data)
                assert preparation["status"] in ["ready", "needs_confirmation"]
            
            # Step 4: Log the workflow
            logger = AuditLogger()
            log_entry = {
                "event_type": "hitl_workflow_complete",
                "approval_id": approval_id,
                "opportunity": arbitrage_opportunity
            }
            
            log_id = logger.log_system_event(log_entry)
            assert log_id is not None
    
    @pytest.mark.e2e
    def test_system_monitoring_workflow(self):
        """Test complete system monitoring workflow."""
        from autonomous.monitoring_control import MonitoringControl
        from storage.audit_logger import AuditLogger
        from notifications.email_notifications import EmailNotification
        
        # Step 1: Monitor system health
        monitor = MonitoringControl()
        health_status = monitor.check_system_health()
        
        # Step 2: Log health status
        logger = AuditLogger()
        log_entry = {
            "event_type": "health_check",
            "status": health_status
        }
        
        log_id = logger.log_system_event(log_entry)
        assert log_id is not None
        
        # Step 3: Send alert if unhealthy
        if health_status["status"] in ["warning", "critical"]:
            notifier = EmailNotification()
            alert_data = {
                "to": "admin@example.com",
                "subject": f"System Health Alert: {health_status['status']}",
                "body": f"System health check failed: {health_status}"
            }
            
            alert_id = notifier.send_notification(alert_data)
            assert alert_id is not None


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance and load testing."""
    
    def test_detection_performance(self, test_config):
        """Test arbitrage detection performance."""
        from detection.opportunity_scanner import OpportunityScanner
        import time
        
        scanner = OpportunityScanner(min_profit_margin=Decimal("0.01"))
        
        # Generate large dataset
        large_dataset = {}
        for bookmaker_id in range(1, 51):  # 50 bookmakers
            large_dataset[f"bookmaker_{bookmaker_id}"] = []
            for event_id in range(1, 101):  # 100 events per bookmaker
                large_dataset[f"bookmaker_{bookmaker_id}"].append({
                    "event_id": f"event_{event_id}",
                    "event_name": f"Event {event_id}",
                    "sport": "Football",
                    "market_type": "match_winner",
                    "odds": {
                        "home": Decimal(str(random.uniform(1.1, 5.0))).quantize(Decimal("0.01")),
                        "draw": Decimal(str(random.uniform(2.5, 8.0))).quantize(Decimal("0.01")),
                        "away": Decimal(str(random.uniform(1.1, 5.0))).quantize(Decimal("0.01")),
                    },
                    "timestamp": datetime.now().isoformat(),
                    "status": "active"
                })
        
        # Measure detection time
        start_time = time.time()
        opportunities = scanner.scan_opportunities(large_dataset)
        end_time = time.time()
        
        detection_time = end_time - start_time
        
        # Performance assertions
        assert detection_time < test_config["performance_threshold"]
        assert isinstance(opportunities, list)
        
        print(f"Detection time: {detection_time:.3f}s")
        print(f"Opportunities found: {len(opportunities)}")
    
    def test_concurrent_processing_performance(self, test_config):
        """Test concurrent opportunity processing."""
        from concurrent_executor import ConcurrentExecutor
        import time
        
        executor = ConcurrentExecutor(max_workers=10)
        
        def process_opportunity(opportunity_id):
            # Simulate processing time
            time.sleep(0.01)
            return f"processed_{opportunity_id}"
        
        # Process 100 opportunities concurrently
        start_time = time.time()
        futures = []
        for i in range(100):
            future = executor.submit_task(process_opportunity, i)
            futures.append(future)
        
        results = executor.wait_for_completion(futures, timeout=10)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        assert len(results) == 100
        assert processing_time < 2.0  # Should complete in under 2 seconds
        
        print(f"Concurrent processing time: {processing_time:.3f}s")
    
    def test_memory_usage(self, test_config):
        """Test memory usage during processing."""
        from detection.market_data_store import MarketDataStore
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Store large amount of data
        store = MarketDataStore()
        for bookmaker_id in range(1, 101):  # 100 bookmakers
            for event_id in range(1, 101):  # 100 events per bookmaker
                test_data = {
                    "event_id": f"event_{event_id}",
                    "odds": {
                        "home": Decimal("2.10"),
                        "away": Decimal("1.95")
                    },
                    "timestamp": datetime.now()
                }
                store.store_odds_data(f"bookmaker_{bookmaker_id}", test_data)
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Memory should not increase by more than 100MB
        assert memory_increase < 100
        
        print(f"Memory increase: {memory_increase:.2f}MB")


# ============================================================================
# STRESS TESTS
# ============================================================================

class TestStress:
    """Stress testing for high-frequency scenarios."""
    
    @pytest.mark.stress
    def test_high_frequency_detection(self, test_config):
        """Test detection under high frequency updates."""
        from detection.scanner_engine import ScannerEngine
        import time
        
        engine = ScannerEngine()
        
        # Simulate rapid market updates
        num_updates = test_config["stress_test_iterations"]
        start_time = time.time()
        
        for i in range(num_updates):
            # Generate rapid update
            update_data = {
                "bookmaker_1": {
                    "event_1": {
                        "odds": {
                            "home": Decimal(str(random.uniform(1.1, 5.0))).quantize(Decimal("0.01")),
                            "away": Decimal(str(random.uniform(1.1, 5.0))).quantize(Decimal("0.01"))
                        }
                    }
                }
            }
            
            # Process update
            opportunities = engine.process_market_update(update_data)
            
            if i % 100 == 0:
                logger.info(f"Processed {i}/{num_updates} updates")
        
        end_time = time.time()
        total_time = end_time - start_time
        updates_per_second = num_updates / total_time
        
        print(f"High-frequency test: {updates_per_second:.1f} updates/second")
        
        # Should handle at least 100 updates per second
        assert updates_per_second > 100
    
    @pytest.mark.stress
    def test_concurrent_stress_test(self, test_config):
        """Test system under concurrent stress."""
        import asyncio
        import aiohttp
        
        async def simulate_api_call(session, bookmaker_id):
            """Simulate API call to bookmaker."""
            # Mock API call
            await asyncio.sleep(0.01)  # Simulate network delay
            
            return {
                "bookmaker_id": bookmaker_id,
                "status": "success",
                "data": {
                    "odds": {
                        "home": Decimal("2.10"),
                        "away": Decimal("1.95")
                    }
                }
            }
        
        async def stress_test():
            """Run concurrent stress test."""
            async with aiohttp.ClientSession() as session:
                # Create many concurrent tasks
                tasks = []
                for i in range(test_config["load_test_concurrent"]):
                    task = simulate_api_call(session, i)
                    tasks.append(task)
                
                start_time = time.time()
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                
                return len(results), end_time - start_time
        
        # Run stress test
        num_results, execution_time = asyncio.run(stress_test())
        
        assert num_results == test_config["load_test_concurrent"]
        assert execution_time < 5.0  # Should complete in under 5 seconds
        
        print(f"Concurrent stress test: {num_results} requests in {execution_time:.2f}s")
    
    @pytest.mark.stress
    def test_system_stability_under_load(self, test_config):
        """Test system stability under sustained load."""
        from autonomous.monitoring_control import MonitoringControl
        from storage.audit_logger import AuditLogger
        import time
        
        monitor = MonitoringControl()
        logger = AuditLogger()
        
        # Run sustained load
        load_duration = 30  # 30 seconds
        operations_per_second = 50
        start_time = time.time()
        
        operations_completed = 0
        errors_encountered = 0
        
        while time.time() - start_time < load_duration:
            try:
                # Simulate various operations
                health_status = monitor.check_system_health()
                
                log_entry = {
                    "event_type": "load_test_operation",
                    "timestamp": datetime.now().isoformat(),
                    "health_status": health_status["status"]
                }
                logger.log_system_event(log_entry)
                
                operations_completed += 1
                
                # Maintain target operations per second
                time.sleep(1.0 / operations_per_second)
                
            except Exception as e:
                errors_encountered += 1
                logger.warning(f"Load test error: {str(e)}")
        
        # Calculate metrics
        actual_duration = time.time() - start_time
        actual_ops_per_second = operations_completed / actual_duration
        error_rate = errors_encountered / operations_completed if operations_completed > 0 else 0
        
        print(f"Stability test results:")
        print(f"  Duration: {actual_duration:.1f}s")
        print(f"  Operations: {operations_completed}")
        print(f"  Ops/second: {actual_ops_per_second:.1f}")
        print(f"  Error rate: {error_rate:.2%}")
        
        # Assertions
        assert error_rate < 0.05  # Less than 5% error rate
        assert actual_ops_per_second > operations_per_second * 0.8  # At least 80% of target


# ============================================================================
# REGRESSION TESTS
# ============================================================================

class TestRegression:
    """Automated regression testing."""
    
    @pytest.fixture
    def baseline_metrics(self):
        """Baseline performance metrics for regression testing."""
        return {
            "detection_time_threshold": 0.1,  # seconds
            "opportunity_detection_rate": 0.8,  # 80% of opportunities found
            "false_positive_rate": 0.05,  # Less than 5% false positives
            "system_availability": 0.99,  # 99% availability
        }
    
    def test_performance_regression(self, baseline_metrics, test_config):
        """Test for performance regressions."""
        from detection.opportunity_scanner import OpportunityScanner
        import time
        
        # Test current performance
        scanner = OpportunityScanner(min_profit_margin=Decimal("0.01"))
        
        # Generate test data
        test_data = {}
        for i in range(10):
            test_data[f"bookmaker_{i+1}"] = [{
                "event_1": {
                    "odds": {
                        "home": Decimal("2.10"),
                        "away": Decimal("1.95")
                    }
                }
            }]
        
        # Measure detection time
        start_time = time.time()
        opportunities = scanner.scan_opportunities(test_data)
        detection_time = time.time() - start_time
        
        # Check against baseline
        assert detection_time < baseline_metrics["detection_time_threshold"], \
            f"Performance regression detected: {detection_time:.3f}s > {baseline_metrics['detection_time_threshold']}s"
    
    def test_accuracy_regression(self, baseline_metrics):
        """Test for accuracy regressions."""
        from detection.opportunity_scanner import OpportunityScanner
        from utils.math_helpers import find_arbitrage_opportunities
        
        # Test known arbitrage case
        markets = {
            "bookmaker1": {"home": Decimal("2.10"), "away": Decimal("1.90")},
            "bookmaker2": {"home": Decimal("1.95"), "away": Decimal("2.05")}
        }
        
        opportunities = find_arbitrage_opportunities(markets)
        
        # Should detect the arbitrage opportunity
        assert len(opportunities) > 0, "Accuracy regression: No arbitrage opportunity detected"
        
        # Check false positive rate with non-arbitrage case
        non_arbitrage_markets = {
            "bookmaker1": {"home": Decimal("2.00"), "away": Decimal("1.90")},
            "bookmaker2": {"home": Decimal("1.95"), "away": Decimal("1.85")}
        }
        
        false_positives = find_arbitrage_opportunities(non_arbitrage_markets)
        
        # Should not detect arbitrage in non-arbitrage case
        if false_positives:
            false_positive_rate = len(false_positives) / 2  # Assume 2 markets
            assert false_positive_rate < baseline_metrics["false_positive_rate"], \
                f"False positive regression: {false_positive_rate:.2%} > {baseline_metrics['false_positive_rate']:.2%}"
    
    def test_integration_regression(self):
        """Test for integration regressions."""
        # Test key integration points
        try:
            from detection.opportunity_scanner import OpportunityScanner
            from risk.risk_analyzer import RiskAnalyzer
            from autonomous.decision_engine import DecisionEngine
            
            # Test that all modules can be imported and instantiated
            scanner = OpportunityScanner()
            analyzer = RiskAnalyzer()
            engine = DecisionEngine()
            
            # Test basic functionality
            assert scanner.min_profit_margin > 0
            assert hasattr(analyzer, 'analyze_portfolio_risk')
            assert hasattr(engine, 'evaluate_opportunity')
            
        except ImportError as e:
            pytest.fail(f"Integration regression: Cannot import required modules: {e}")
    
    def test_mathematical_regression(self):
        """Test for mathematical calculation regressions."""
        from utils.math_helpers import (
            calculate_implied_probability,
            calculate_arbitrage_profit
        )
        
        # Test known values
        odds = Decimal("2.00")
        probability = calculate_implied_probability(odds)
        expected_probability = Decimal("0.5")
        
        # Should be very close to expected
        assert abs(probability - expected_probability) < Decimal("0.001"), \
            f"Mathematical regression: {probability} != {expected_probability}"
        
        # Test arbitrage profit calculation with known values
        stake = Decimal("100")
        odds1 = Decimal("2.10")
        odds2 = Decimal("2.05")
        
        profit, total_stake = calculate_arbitrage_profit(stake, odds1, odds2)
        
        # Profit should be positive
        assert profit > 0, "Mathematical regression: Non-positive profit calculated"
        
        # Total stake should equal input stake
        assert abs(total_stake - stake) < Decimal("0.01"), \
            f"Mathematical regression: Stake mismatch {total_stake} != {stake}"


# ============================================================================
# TEST RUNNER AND MAIN
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--strict-markers",
        "--disable-warnings",
    ])
