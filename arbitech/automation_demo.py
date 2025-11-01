"""
Enhanced Playwright Setup Demo for Arbitrage Workflows

This script demonstrates the comprehensive usage of the enhanced browser automation
system for arbitrage trading workflows. It shows integration with the existing setup,
multi-bookmaker operations, security features, and risk management.

Usage:
    python automation_demo.py

This demo includes:
- Browser pool management with load balancing
- Multi-bookmaker navigation and automation
- Risk validation integration
- Security and stealth features
- Performance monitoring
- Automatic error recovery
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import automation components
from arbitech.automation import (
    EnhancedBrowser,
    ArbitrageBrowser,
    BrowserSessionPool,
    BrowserSecurity,
    BrowserConfig,
    PoolConfig,
    SecurityProfile,
    StealthLevel,
    RiskLevel
)

# Import core components
try:
    from arbitech.core.config_manager import ConfigManager
    from arbitech.utils.logger import get_logger
    from arbitech.storage.models import ArbitrageOpportunity, BetLeg
    from arbitech.risk.risk_analyzer import RiskAnalyzer
except ImportError as e:
    print(f"Warning: Could not import some components: {e}")
    # Mock for basic functionality
    class ConfigManager:
        def get(self, key, default=None):
            return default
    
    class ArbitrageOpportunity:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class BetLeg:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    def get_logger(name):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(name)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = get_logger(__name__)


class ArbitrageWorkflowDemo:
    """
    Comprehensive demo of the enhanced browser automation system for arbitrage workflows.
    """
    
    def __init__(self):
        """Initialize the demo."""
        self.config_manager = ConfigManager()
        self.enhanced_browser = None
        self.session_pool = None
        self.security_manager = None
        self.risk_analyzer = None
        
        logger.info("ArbitrageWorkflowDemo initialized")
    
    async def setup_components(self):
        """Set up all automation components."""
        try:
            logger.info("Setting up automation components...")
            
            # Initialize Enhanced Browser
            self.enhanced_browser = EnhancedBrowser(self.config_manager)
            await self.enhanced_browser.initialize()
            
            # Initialize Browser Pool
            self.session_pool = BrowserSessionPool(self.config_manager)
            await self.session_pool.start()
            
            # Initialize Security Manager
            self.security_manager = BrowserSecurity(self.config_manager)
            
            # Initialize Risk Analyzer if available
            try:
                self.risk_analyzer = RiskAnalyzer()
                logger.info("Risk analyzer initialized")
            except Exception as e:
                logger.warning(f"Risk analyzer not available: {e}")
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup components: {e}")
            raise
    
    async def demo_browser_pool_management(self):
        """Demonstrate browser pool management."""
        logger.info("\n=== Browser Pool Management Demo ===")
        
        try:
            # Get pool statistics
            stats = self.session_pool.get_pool_stats()
            logger.info(f"Pool statistics: {stats}")
            
            # Get sessions from pool
            session = await self.session_pool.get_session()
            if session:
                logger.info(f"Got session: {session.session_id}")
                
                # Release session back to pool
                await self.session_pool.release_session(session)
                logger.info("Released session back to pool")
            
            # Get session metrics
            metrics = self.session_pool.get_all_session_metrics()
            logger.info(f"Session metrics: {len(metrics)} sessions tracked")
            
        except Exception as e:
            logger.error(f"Error in pool management demo: {e}")
    
    async def demo_security_features(self):
        """Demonstrate security and stealth features."""
        logger.info("\n=== Security Features Demo ===")
        
        try:
            # Show current security profile
            stealth_level = self.security_manager.get_stealth_level()
            logger.info(f"Current stealth level: {stealth_level}")
            
            # Show user agent rotation status
            ua_rotation = self.security_manager.is_user_agent_rotation_enabled()
            logger.info(f"User agent rotation enabled: {ua_rotation}")
            
            # Get current user agent
            current_ua = self.security_manager.get_current_user_agent()
            if current_ua:
                logger.info(f"Current user agent: {current_ua.browser_name} {current_ua.browser_version}")
            
            # Show detection statistics
            detection_stats = self.security_manager.get_detection_stats()
            logger.info(f"Detection statistics: {json.dumps(detection_stats, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error in security features demo: {e}")
    
    async def demo_multi_bookmaker_operations(self):
        """Demonstrate multi-bookmaker operations."""
        logger.info("\n=== Multi-Bookmaker Operations Demo ===")
        
        try:
            # Get browser status
            browser_status = await self.enhanced_browser.get_session_status()
            logger.info(f"Browser status: {json.dumps(browser_status, indent=2)}")
            
            # Get bookmaker configurations
            bookmaker_configs = self.enhanced_browser.get_bookmaker_configs()
            logger.info(f"Available bookmakers: {list(bookmaker_configs.keys())}")
            
            # Create a session for operations
            config = BrowserConfig(
                name="demo_session",
                headless=True,
                enable_stealth=True
            )
            
            session = await self.enhanced_browser.create_session(config)
            logger.info(f"Created demo session: {session.session_id}")
            
            # Test navigation to bookmaker (simulation)
            logger.info("Testing navigation to bookmaker (simulated)...")
            # await self.enhanced_browser.navigate_to_bookmaker(session, "bet365")
            
            # Clean up session
            await self.enhanced_browser._close_session(session.session_id)
            
        except Exception as e:
            logger.error(f"Error in multi-bookmaker operations demo: {e}")
    
    async def demo_risk_integration(self):
        """Demonstrate risk management integration."""
        logger.info("\n=== Risk Management Integration Demo ===")
        
        try:
            if self.risk_analyzer:
                # Create a sample arbitrage opportunity
                opportunity = ArbitrageOpportunity(
                    id="demo_opp_001",
                    sport="soccer",
                    event="Team A vs Team B",
                    profit_margin=2.5,
                    timestamp=datetime.now(),
                    legs=[
                        BetLeg(
                            bookmaker="bet365",
                            selection="Team A",
                            odds=2.1,
                            stake=100.0,
                            expected_return=210.0
                        ),
                        BetLeg(
                            bookmaker="william_hill",
                            selection="Team B", 
                            odds=2.0,
                            stake=105.0,
                            expected_return=210.0
                        )
                    ]
                )
                
                # Validate opportunity through risk analyzer
                validation_result = self.risk_analyzer.validate_opportunity(opportunity)
                logger.info(f"Risk validation result: {json.dumps(validation_result, indent=2)}")
                
            else:
                logger.info("Risk analyzer not available for demo")
            
        except Exception as e:
            logger.error(f"Error in risk integration demo: {e}")
    
    async def demo_arbitrage_browser(self):
        """Demonstrate arbitrage browser functionality."""
        logger.info("\n=== Arbitrage Browser Demo ===")
        
        try:
            # Create browser instance
            arbitrage_browser = ArbitrageBrowser(self.config_manager)
            
            # Create page for testing
            from playwright.async_api import async_playwright
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Attach arbitrage browser to page
            await arbitrage_browser.attach_to_page(page)
            
            # Load bookmaker interface
            await arbitrage_browser.load_bookmaker_interface("bet365")
            logger.info("Loaded bookmaker interface")
            
            # Simulate bet placement (without actual navigation)
            logger.info("Simulating bet placement...")
            # bet = await arbitrage_browser.place_bet(
            #     bookmaker_name="bet365",
            #     selection="Team A",
            #     odds=2.5,
            #     stake=10.0
            # )
            # logger.info(f"Bet placement status: {bet.status}")
            
            # Get recent bets
            recent_bets = arbitrage_browser.get_recent_bets()
            logger.info(f"Recent bets: {len(recent_bets)}")
            
            # Clean up
            await browser.close()
            await playwright.stop()
            
        except Exception as e:
            logger.error(f"Error in arbitrage browser demo: {e}")
    
    async def demo_performance_monitoring(self):
        """Demonstrate performance monitoring."""
        logger.info("\n=== Performance Monitoring Demo ===")
        
        try:
            # Wait a bit for monitoring data to accumulate
            await asyncio.sleep(5)
            
            # Get updated pool statistics
            stats = self.session_pool.get_pool_stats()
            logger.info(f"Updated pool stats: {json.dumps(stats, indent=2)}")
            
            # Get session metrics
            all_metrics = self.session_pool.get_all_session_metrics()
            for session_id, metrics in all_metrics.items():
                logger.info(f"Session {session_id} metrics: {metrics}")
            
            # Record a test operation
            if all_metrics:
                session_id = list(all_metrics.keys())[0]
                self.session_pool.record_operation(
                    session_id=session_id,
                    operation_type="test_navigation",
                    success=True,
                    response_time_ms=150.0
                )
                logger.info("Recorded test operation")
            
        except Exception as e:
            logger.error(f"Error in performance monitoring demo: {e}")
    
    async def demo_concurrent_operations(self):
        """Demonstrate concurrent operations."""
        logger.info("\n=== Concurrent Operations Demo ===")
        
        try:
            # Start multiple concurrent tasks
            tasks = []
            
            # Task 1: Get pool stats
            async def get_stats():
                await asyncio.sleep(1)
                stats = self.session_pool.get_pool_stats()
                return f"Pool has {stats.total_sessions} sessions"
            
            # Task 2: Get security events
            async def get_security():
                await asyncio.sleep(1)
                events = self.security_manager.get_security_events()
                return f"Security events: {len(events)}"
            
            # Task 3: Check browser status
            async def get_browser_status():
                await asyncio.sleep(1)
                status = await self.enhanced_browser.get_session_status()
                return f"Browser sessions: {status['total_sessions']}"
            
            tasks = [
                get_stats(),
                get_security(), 
                get_browser_status()
            ]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info("Concurrent operations results:")
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Task {i+1} failed: {result}")
                else:
                    logger.info(f"Task {i+1}: {result}")
            
        except Exception as e:
            logger.error(f"Error in concurrent operations demo: {e}")
    
    async def run_comprehensive_demo(self):
        """Run the complete comprehensive demo."""
        logger.info("Starting Comprehensive Arbitrage Browser Automation Demo")
        logger.info("=" * 60)
        
        try:
            # Setup components
            await self.setup_components()
            
            # Run individual demos
            await self.demo_browser_pool_management()
            await self.demo_security_features()
            await self.demo_multi_bookmaker_operations()
            await self.demo_risk_integration()
            await self.demo_arbitrage_browser()
            await self.demo_performance_monitoring()
            await self.demo_concurrent_operations()
            
            logger.info("\n" + "=" * 60)
            logger.info("Demo completed successfully!")
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up all components."""
        logger.info("Cleaning up components...")
        
        try:
            if self.session_pool:
                await self.session_pool.stop()
            
            if self.enhanced_browser:
                await self.enhanced_browser.shutdown()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """Main demo function."""
    demo = ArbitrageWorkflowDemo()
    
    try:
        await demo.run_comprehensive_demo()
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
    
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    print("""
    ================================================================
    ARBitech Enhanced Browser Automation Demo
    
    This demo showcases the comprehensive browser automation system
    for arbitrage trading workflows with:
    
    ✓ Enhanced browser automation with arbitrage-specific features
    ✓ Multi-bookmaker interface management
    ✓ Advanced session pool with load balancing
    ✓ Enterprise security and stealth capabilities
    ✓ Risk management integration
    ✓ Performance monitoring and analytics
    ✓ Automatic error recovery
    ✓ Concurrent operations support
    
    ================================================================
    """)
    
    # Run the demo
    asyncio.run(main())
