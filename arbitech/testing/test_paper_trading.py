"""
Comprehensive Test Suite for Paper Trading System

This module contains comprehensive tests for all paper trading functionality
including unit tests, integration tests, and performance benchmarks.

Usage:
    python test_paper_trading.py [test_suite]

Test suites:
    - unit: Unit tests for individual components
    - integration: Integration tests for complete workflows
    - performance: Performance and stress tests
    - all: Run all test suites
"""

import asyncio
import json
import logging
import pytest
import random
import tempfile
import time
from decimal import Decimal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from uuid import uuid4
import pandas as pd

# Import the paper trading system and utilities
from paper_trading import (
    PaperTradingSystem, TradingMode, MarketCondition, Sport, RiskTier,
    PaperTradeStatus, VirtualBankrollAccount, SimulatedExecution,
    create_paper_trading_system, load_sample_opportunities,
    ArbitrageOpportunity, ArbitrageLeg
)

# Configure test logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise during tests
logger = logging.getLogger(__name__)


class TestPaperTradingSystem:
    """Test suite for PaperTradingSystem class."""
    
    @pytest.fixture
    def system(self):
        """Create a test system instance."""
        return create_paper_trading_system(
            mode=TradingMode.PAPER,
            initial_bankroll=Decimal('50000.00')
        )
    
    @pytest.fixture
    def sample_opportunity(self):
        """Create a sample arbitrage opportunity."""
        legs = [
            ArbitrageLeg(
                id=uuid4(),
                sport=Sport.FOOTBALL,
                event_id="test_event_1",
                bookmaker="Pinnacle",
                odds=Decimal('2.10'),
                suggested_stake=Decimal('500.00'),
                risk_tier=RiskTier.TIER_A
            ),
            ArbitrageLeg(
                id=uuid4(),
                sport=Sport.FOOTBALL,
                event_id="test_event_1",
                bookmaker="Bet365",
                odds=Decimal('1.95'),
                suggested_stake=Decimal('500.00'),
                risk_tier=RiskTier.TIER_A
            )
        ]
        
        return ArbitrageOpportunity(
            id=uuid4(),
            sport=Sport.FOOTBALL,
            event_id="test_event_1",
            profit_margin=Decimal('0.025'),
            legs=legs,
            risk_tier=RiskTier.TIER_A,
            detection_timestamp=datetime.now(),
            quality_score=Decimal('0.8')
        )
    
    # ========================================================================
    # UNIT TESTS
    # ========================================================================
    
    def test_system_initialization(self, system):
        """Test system initialization."""
        assert system.mode == TradingMode.PAPER
        assert system.initial_bankroll == Decimal('50000.00')
        assert system.is_running == False
        assert len(system.virtual_accounts) > 0
        assert system.performance_metrics.total_trades == 0
    
    def test_virtual_account_creation(self, system):
        """Test virtual account creation and functionality."""
        account = system.virtual_accounts.get('Pinnacle')
        assert account is not None
        assert account.balance == Decimal('10000.00')
        assert account.get_available_balance() == Decimal('10000.00')
        
        # Test balance reservation
        can_bet, reason = account.can_place_bet(Decimal('1000.00'))
        assert can_bet == True
        assert reason == "OK"
        
        success = account.reserve_balance(Decimal('1000.00'))
        assert success == True
        assert account.get_available_balance() == Decimal('9000.00')
        
        account.release_reservation(Decimal('500.00'))
        assert account.get_available_balance() == Decimal('9500.00')
    
    def test_account_limits(self, system):
        """Test account limit enforcement."""
        account = system.virtual_accounts.get('Pinnacle')
        
        # Test daily limit
        can_bet, reason = account.can_place_bet(Decimal('6000.00'))
        assert can_bet == False
        assert "Daily limit" in reason
    
    def test_market_simulation(self, system):
        """Test market data simulation."""
        initial_odds = Decimal('2.00')
        new_odds = system.market_simulator.simulate_odds_movement(
            initial_odds, 'Pinnacle', Sport.FOOTBALL
        )
        
        assert isinstance(new_odds, Decimal)
        assert new_odds >= Decimal('1.01')
        assert new_odds <= Decimal('100.00')
    
    def test_execution_simulation(self, system):
        """Test execution delay and slippage simulation."""
        # Test execution delay
        delay = system.execution_simulator.simulate_execution_delay(
            TradingMode.PAPER, MarketCondition.STABLE
        )
        assert isinstance(delay, int)
        assert delay > 0
        
        # Test slippage calculation
        slippage = system.execution_simulator.simulate_slippage(
            Decimal('2.00'), Decimal('1000.00'), MarketCondition.STABLE
        )
        assert isinstance(slippage, Decimal)
        assert slippage >= Decimal('0.00')
        assert slippage <= Decimal('0.15')
    
    def test_performance_metrics_initialization(self, system):
        """Test performance metrics initialization."""
        metrics = system.performance_metrics
        assert metrics.total_trades == 0
        assert metrics.successful_trades == 0
        assert metrics.failed_trades == 0
        assert metrics.total_profit == Decimal('0.00')
        assert metrics.net_profit == Decimal('0.00')
    
    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_opportunity_processing(self, system, sample_opportunity):
        """Test complete opportunity processing workflow."""
        user_id = uuid4()
        
        # Process opportunity
        trade = await system.process_opportunity(sample_opportunity, user_id)
        
        assert trade.id is not None
        assert trade.opportunity.id == sample_opportunity.id
        assert trade.status in [PaperTradeStatus.FILLED, PaperTradeStatus.PARTIAL_FILLED, PaperTradeStatus.FAILED]
        assert len(trade.placed_bets) + len(trade.failed_bets) == len(sample_opportunity.legs)
    
    @pytest.mark.asyncio
    async def test_multiple_opportunities(self, system):
        """Test processing multiple opportunities."""
        opportunities = load_sample_opportunities(5)
        user_id = uuid4()
        
        for opportunity in opportunities:
            trade = await system.process_opportunity(opportunity, user_id)
            assert trade.id is not None
        
        # Check that metrics are updated
        assert system.performance_metrics.total_trades == 5
    
    @pytest.mark.asyncio
    async def test_start_stop_simulation(self, system):
        """Test starting and stopping the simulation."""
        assert system.is_running == False
        
        await system.start_paper_trading()
        assert system.is_running == True
        
        await asyncio.sleep(0.1)  # Let it run briefly
        
        await system.stop_paper_trading()
        assert system.is_running == False
    
    @pytest.mark.asyncio
    async def test_mode_switching(self, system):
        """Test switching between trading modes."""
        assert system.mode == TradingMode.PAPER
        
        system.switch_mode(TradingMode.BACKTEST)
        assert system.mode == TradingMode.BACKTEST
        
        system.switch_mode(TradingMode.HYBRID)
        assert system.mode == TradingMode.HYBRID
        
        system.switch_mode(TradingMode.PAPER)
        assert system.mode == TradingMode.PAPER
    
    # ========================================================================
    # PERFORMANCE TESTS
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_processing_speed(self, system):
        """Test processing speed with multiple opportunities."""
        opportunities = load_sample_opportunities(10)
        user_id = uuid4()
        
        start_time = time.time()
        
        for opportunity in opportunities:
            trade = await system.process_opportunity(opportunity, user_id)
            assert trade.id is not None
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 10 opportunities in reasonable time (less than 30 seconds)
        assert processing_time < 30.0
        
        # Calculate processing rate
        processing_rate = len(opportunities) / processing_time
        assert processing_rate > 0.5  # At least 0.5 opportunities per second
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, system):
        """Test memory usage with large number of trades."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process many opportunities
        opportunities = load_sample_opportunities(50)
        user_id = uuid4()
        
        for opportunity in opportunities:
            trade = await system.process_opportunity(opportunity, user_id)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB
    
    # ========================================================================
    # BACKTEST TESTS
    # ========================================================================
    
    def test_backtest_data_loading(self, system):
        """Test loading backtest data."""
        # Create test data
        test_data = pd.DataFrame({
            'sport': ['football', 'basketball'],
            'event_id': ['event1', 'event2'],
            'bookmaker': ['Pinnacle', 'Bet365'],
            'odds': [2.0, 1.8],
            'timestamp': [datetime.now(), datetime.now()]
        })
        
        system.load_backtest_data(test_data)
        assert system.backtest_data is not None
        assert len(system.backtest_data) == 2
    
    @pytest.mark.asyncio
    async def test_backtest_execution(self, system):
        """Test backtest execution."""
        # Create minimal backtest data
        backtest_data = pd.DataFrame({
            'sport': ['football', 'football', 'basketball', 'basketball'],
            'event_id': ['event1', 'event1', 'event2', 'event2'],
            'bookmaker': ['Pinnacle', 'Bet365', 'Unibet', 'William Hill'],
            'odds': [2.1, 1.9, 2.3, 1.7],
            'timestamp': pd.date_range('2024-01-01', periods=4, freq='H')
        })
        
        system.load_backtest_data(backtest_data)
        results = await system.run_backtest()
        
        assert 'total_trades' in results
        assert 'total_profit' in results
        assert 'roi' in results
        assert isinstance(results['total_trades'], int)
        assert isinstance(results['total_profit'], (int, float))
    
    # ========================================================================
    # EXPORT AND REPORTING TESTS
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_trade_history_export(self, system):
        """Test trade history export functionality."""
        # Process a trade first
        opportunity = load_sample_opportunities(1)[0]
        user_id = uuid4()
        trade = await system.process_opportunity(opportunity, user_id)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            system.export_trade_history(temp_path, format="json")
            
            # Verify file was created and has content
            assert Path(temp_path).exists()
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert 'metadata' in data
            assert 'trades' in data
            assert len(data['trades']) > 0
            
        finally:
            # Clean up
            Path(temp_path).unlink(missing_ok=True)
    
    def test_performance_report_generation(self, system):
        """Test performance report generation."""
        report = system.get_performance_report()
        
        assert 'trading_mode' in report
        assert 'performance_metrics' in report
        assert 'virtual_accounts' in report
        assert 'trade_summary' in report
        
        metrics = report['performance_metrics']
        assert 'total_trades' in metrics
        assert 'net_profit' in metrics
        assert 'win_rate' in metrics
    
    def test_account_summary(self, system):
        """Test account summary generation."""
        summary = system.get_account_summary()
        
        assert 'total_accounts' in summary
        assert 'total_balance' in summary
        assert 'total_available_balance' in summary
        assert 'accounts' in summary
        
        assert summary['total_accounts'] == len(system.virtual_accounts)
    
    # ========================================================================
    # ERROR HANDLING TESTS
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_invalid_opportunity_handling(self, system):
        """Test handling of invalid opportunities."""
        # Create invalid opportunity with inconsistent odds
        legs = [
            ArbitrageLeg(
                id=uuid4(),
                sport=Sport.FOOTBALL,
                event_id="invalid_event",
                bookmaker="Pinnacle",
                odds=Decimal('2.10'),
                suggested_stake=Decimal('1000.00'),  # Too large
                risk_tier=RiskTier.TIER_A
            )
        ]
        
        invalid_opportunity = ArbitrageOpportunity(
            id=uuid4(),
            sport=Sport.FOOTBALL,
            event_id="invalid_event",
            profit_margin=Decimal('-0.05'),  # Negative profit
            legs=legs,
            risk_tier=RiskTier.TIER_A,
            detection_timestamp=datetime.now(),
            quality_score=Decimal('0.8')
        )
        
        user_id = uuid4()
        
        # Should handle gracefully
        trade = await system.process_opportunity(invalid_opportunity, user_id)
        assert trade.id is not None
        assert trade.status in [PaperTradeStatus.FAILED, PaperTradeStatus.CANCELLED]
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, system):
        """Test concurrent opportunity processing."""
        opportunities = load_sample_opportunities(5)
        user_id = uuid4()
        
        # Process opportunities concurrently
        tasks = [
            system.process_opportunity(opp, user_id)
            for opp in opportunities
        ]
        
        trades = await asyncio.gather(*tasks)
        
        assert len(trades) == len(opportunities)
        assert all(trade.id is not None for trade in trades)
    
    # ========================================================================
    # STRESS TESTS
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_high_volume_processing(self, system):
        """Test high-volume opportunity processing."""
        # Generate large number of opportunities
        opportunities = load_sample_opportunities(100)
        user_id = uuid4()
        
        start_time = time.time()
        
        # Process all opportunities
        for opportunity in opportunities:
            trade = await system.process_opportunity(opportunity, user_id)
            assert trade.id is not None
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should handle 100 opportunities reasonably quickly
        assert processing_time < 60.0  # Less than 1 minute
        
        # Verify all trades were recorded
        assert system.performance_metrics.total_trades == 100
    
    # ========================================================================
    # CONFIGURATION TESTS
    # ========================================================================
    
    def test_custom_configuration(self):
        """Test system with custom configuration."""
        # Create temporary config file
        config = {
            "virtual_bookmakers": ["Pinnacle", "Bet365"],
            "initial_account_balances": {"default": 5000.00}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            config_path = f.name
        
        try:
            system = create_paper_trading_system(
                mode=TradingMode.PAPER,
                config_path=config_path
            )
            
            # Verify custom config was loaded
            assert len(system.virtual_accounts) == 2
            assert "Pinnacle" in system.virtual_accounts
            assert system.virtual_accounts["Pinnacle"].balance == Decimal('5000.00')
            
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    # ========================================================================
    # SCENARIO TESTS
    # ========================================================================
    
    @pytest.mark.asyncio
    async def test_volatile_market_scenario(self, system):
        """Test system behavior in volatile market conditions."""
        system.simulate_market_event(MarketCondition.VOLATILE, 1)
        
        # Process opportunities in volatile market
        opportunities = load_sample_opportunities(5)
        user_id = uuid4()
        
        for opportunity in opportunities:
            trade = await system.process_opportunity(opportunity, user_id)
            
            # Volatile markets should have higher slippage and more failures
            # This is tested implicitly by the simulation
        
        # System should handle volatile conditions gracefully
        assert system.performance_metrics.total_trades == 5
    
    @pytest.mark.asyncio
    async def test_account_reset_functionality(self, system):
        """Test account reset functionality."""
        # Process some trades first
        opportunities = load_sample_opportunities(3)
        user_id = uuid4()
        
        for opportunity in opportunities:
            await system.process_opportunity(opportunity, user_id)
        
        # Verify accounts have activity
        total_volume = sum(acc.daily_volume for acc in system.virtual_accounts.values())
        assert total_volume > 0
        
        # Reset accounts
        system.reset_virtual_accounts()
        
        # Verify reset
        total_volume_after_reset = sum(acc.daily_volume for acc in system.virtual_accounts.values())
        assert total_volume_after_reset == 0
        
        # Verify performance metrics were reset
        assert system.performance_metrics.total_trades == 0


def run_test_suite(test_type: str = "all"):
    """Run specific test suite or all tests."""
    
    if test_type == "unit":
        print("🧪 Running unit tests...")
        pytest.main([__file__, "-v", "-m", "not integration and not performance and not stress", __file__])
    
    elif test_type == "integration":
        print("🔗 Running integration tests...")
        pytest.main([__file__, "-v", "-m", "integration", __file__])
    
    elif test_type == "performance":
        print("⚡ Running performance tests...")
        pytest.main([__file__, "-v", "-m", "performance or stress", __file__])
    
    elif test_type == "all":
        print("🚀 Running all tests...")
        pytest.main([__file__, "-v", __file__])
    
    else:
        print(f"❌ Unknown test type: {test_type}")
        print("Available: unit, integration, performance, all")


if __name__ == "__main__":
    import sys
    
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    run_test_suite(test_type)