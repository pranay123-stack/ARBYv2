"""
ARBitech Automation Module

This module contains advanced browser automation functionality for the ARBitech framework,
specifically designed for arbitrage trading workflows with enterprise security and stealth features.

Main Components:
- EnhancedBrowser: Enhanced browser automation with arbitrage-specific features
- ArbitrageBrowser: Specialized browser for arbitrage trading workflows
- BrowserSessionPool: Advanced browser session management with pooling
- BrowserSecurity: Security and anti-detection measures
- MultiLegExecutor: Main execution engine for coordinated multi-bookmaker trades with atomic operations
- TradeCoordinator: Advanced coordination system for managing simultaneous bets across bookmakers
- ExecutionTracker: Real-time execution tracking with status monitoring and performance analysis
- ArbitrageExecutor: Specialized executor for arbitrage trades with profit calculation and stake distribution

Features:
- Integration with existing Playwright setup (Chrome port 9222)
- Support for AVO Tabs Chrome extension
- Risk management system integration
- Multi-bookmaker concurrent operations
- Multi-leg trade execution with atomic operations and rollback
- Automatic retry and error recovery
- Comprehensive logging and monitoring
- Headless and headed mode support
- Enterprise-grade security and stealth capabilities
- Real-time execution tracking and performance analytics
- Sophisticated coordination strategies for simultaneous betting
- Kelly Criterion integration for optimal stake distribution
"""

__version__ = "1.0.0"

# Import main classes
from .enhanced_browser import EnhancedBrowser, BrowserConfig, BrowserSession, BrowserMode, RiskLevel
from .arbitrage_browser import ArbitrageBrowser, BetPlacement, BookmakerInterface, FormField
from .browser_manager import BrowserSessionPool, PoolConfig, SessionMetrics, PoolStats, SessionStatus
from .browser_security import BrowserSecurity, SecurityProfile, UserAgentProfile, ProxyConfig, StealthLevel

# Import multi-leg execution components
from .multi_leg_executor import MultiLegExecutor, ExecutionConfig, ExecutionStrategy, CompensationAction
from .trade_coordinator import TradeCoordinator, CoordinationStrategy, TimingController, CoordinationResult
from .execution_tracker import ExecutionTracker, LegStatus, PerformanceAnalyzer, TrackingSession
from .arbitrage_executor import ArbitrageExecutor, StakeOptimizer, ProfitCalculator, ArbitrageResult

__all__ = [
    # Enhanced Browser
    "EnhancedBrowser",
    "BrowserConfig", 
    "BrowserSession",
    "BrowserMode",
    "RiskLevel",
    
    # Arbitrage Browser
    "ArbitrageBrowser",
    "BetPlacement",
    "BookmakerInterface",
    "FormField",
    
    # Browser Manager
    "BrowserSessionPool",
    "PoolConfig",
    "SessionMetrics",
    "PoolStats",
    "SessionStatus",
    
    # Browser Security
    "BrowserSecurity",
    "SecurityProfile",
    "UserAgentProfile", 
    "ProxyConfig",
    "StealthLevel",
    
    # Multi-Leg Execution
    "MultiLegExecutor",
    "ExecutionConfig",
    "ExecutionStrategy",
    "CompensationAction",
    
    # Trade Coordination
    "TradeCoordinator",
    "CoordinationStrategy",
    "TimingController",
    "CoordinationResult",
    
    # Execution Tracking
    "ExecutionTracker",
    "LegStatus",
    "PerformanceAnalyzer",
    "TrackingSession",
    
    # Arbitrage Execution
    "ArbitrageExecutor",
    "StakeOptimizer",
    "ProfitCalculator",
    "ArbitrageResult",
]

# Initialize logging
import logging

logger = logging.getLogger(__name__)
logger.info(f"ARBitech Automation Module v{__version__} loaded")
logger.info("Browser automation components: EnhancedBrowser, ArbitrageBrowser, BrowserSessionPool, BrowserSecurity")
logger.info("Multi-leg execution components: MultiLegExecutor, TradeCoordinator, ExecutionTracker, ArbitrageExecutor")