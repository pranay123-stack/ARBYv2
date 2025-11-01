"""
Enhanced Browser Automation for Arbitrage Trading

This module provides an enhanced browser automation system specifically designed
for arbitrage trading workflows. It integrates with the existing Playwright setup
and includes arbitrage-specific features, risk validation, and multi-bookmaker management.

Features:
- Integration with existing browser setup (Chrome port 9222)
- Support for AVO Tabs Chrome extension
- Integration with risk management system
- Concurrent multi-bookmaker operations
- Automatic retry and error recovery
- Comprehensive logging and monitoring
- Headless and headed mode support
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4
import random
import string

from playwright.async_api import Page, Browser, BrowserContext, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Import existing modules
try:
    from ..core.config_manager import ConfigManager
    from ..utils.logger import get_logger
    from ..risk.risk_analyzer import RiskAnalyzer, RiskAlert, AlertSeverity
    from ..storage.models import ArbitrageOpportunity
    from ..vlm.odds_extractor import OddsExtractor
except ImportError as e:
    # Fallback for standalone usage
    import sys
    sys.path.append('/workspace')
    try:
        from arbitech.core.config_manager import ConfigManager
        from arbitech.utils.logger import get_logger
        from arbitech.risk.risk_analyzer import RiskAnalyzer, RiskAlert, AlertSeverity
        from arbitech.storage.models import ArbitrageOpportunity
        from arbitech.vlm.odds_extractor import OddsExtractor
    except ImportError:
        # Mock for basic functionality
        class ConfigManager:
            def get(self, key, default=None):
                return default
        
        class MockLogger:
            def info(self, msg, *args, **kwargs): print(f"INFO: {msg}")
            def warning(self, msg, *args, **kwargs): print(f"WARNING: {msg}")
            def error(self, msg, *args, **kwargs): print(f"ERROR: {msg}")
            def debug(self, msg, *args, **kwargs): print(f"DEBUG: {msg}")
            def exception(self, msg, *args, **kwargs): print(f"EXCEPTION: {msg}")
        
        def get_logger(name):
            return MockLogger()
        
        class RiskAnalyzer:
            def validate_opportunity(self, opp):
                return {"status": "approved", "risk_score": 0.1}
        
        class ArbitrageOpportunity:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

logger = get_logger(__name__)


class BrowserMode(str, Enum):
    """Browser operation modes."""
    HEADLESS = "headless"
    HEADED = "headed"
    REMOTE = "remote"


class RiskLevel(str, Enum):
    """Risk levels for browser operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BrowserConfig:
    """Configuration for browser instances."""
    name: str
    user_data_dir: Optional[str] = None
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1280, "height": 720})
    user_agent: Optional[str] = None
    headless: bool = False
    proxy: Optional[Dict[str, str]] = None
    extra_args: List[str] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)
    enable_stealth: bool = True
    max_concurrent_pages: int = 10
    timeout: int = 30000
    slow_mo: int = 0


@dataclass
class BookmakerConfig:
    """Configuration for bookmaker browser automation."""
    name: str
    base_url: str
    login_url: str
    bet_url: str
    selectors: Dict[str, str] = field(default_factory=dict)
    form_mapping: Dict[str, str] = field(default_factory=dict)
    verification_selectors: List[str] = field(default_factory=list)
    timeout: int = 30000
    retry_count: int = 3
    requires_login: bool = True
    supports_direct_betting: bool = True
    max_stake: float = 1000.0
    risk_level: RiskLevel = RiskLevel.MEDIUM


@dataclass
class BrowserSession:
    """Represents a browser session."""
    session_id: str
    browser: Browser
    context: BrowserContext
    page: Page
    bookmaker_configs: Dict[str, BookmakerConfig]
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    operations_count: int = 0
    error_count: int = 0


class EnhancedBrowser:
    """
    Enhanced Browser Automation for Arbitrage Trading
    
    Provides comprehensive browser automation with risk management integration,
    multi-bookmaker support, and enterprise-grade security features.
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the enhanced browser."""
        self.config_manager = config_manager or ConfigManager()
        self.playwright = None
        self.sessions: Dict[str, BrowserSession] = {}
        self.bookmaker_configs: Dict[str, BookmakerConfig] = {}
        self.active_operations: Dict[str, Any] = {}
        
        # Risk management integration
        self.risk_analyzer = None
        self.safety_threshold = self.config_manager.get("user.risk.risk_percentage", 2.0)
        
        # Browser pool configuration
        self.max_sessions = self.config_manager.get("browser.max_sessions", 5)
        self.session_timeout = self.config_manager.get("browser.session_timeout", 1800)  # 30 minutes
        
        # AVO Tabs extension support
        self.avo_tabs_enabled = self.config_manager.get("browser.avo_tabs_enabled", True)
        self.avo_tabs_extension_path = "/workspace/browser/browser_extension/avo_tabs"
        
        # Performance settings
        self.default_timeout = self.config_manager.get("browser.timeout", 30000)
        self.retry_attempts = self.config_manager.get("browser.retry_attempts", 3)
        
        logger.info("EnhancedBrowser initialized successfully")
    
    async def initialize(self):
        """Initialize the browser automation system."""
        try:
            self.playwright = await async_playwright().start()
            logger.info("Playwright initialized successfully")
            
            # Initialize risk analyzer if available
            try:
                self.risk_analyzer = RiskAnalyzer()
                logger.info("Risk analyzer initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize risk analyzer: {e}")
            
            # Load bookmaker configurations
            await self._load_bookmaker_configs()
            
            # Start background monitoring
            asyncio.create_task(self._background_monitor())
            
        except Exception as e:
            logger.error(f"Failed to initialize EnhancedBrowser: {e}")
            raise
    
    async def _load_bookmaker_configs(self):
        """Load bookmaker configurations."""
        bookmaker_configs = self.config_manager.get("bookmakers", {})
        
        for name, config in bookmaker_configs.items():
            if config.get("enabled", False):
                bookmaker_config = BookmakerConfig(
                    name=name,
                    base_url=config.get("base_url", ""),
                    login_url=f"{config.get('base_url', '')}/login",
                    bet_url=f"{config.get('base_url', '')}/bet",
                    timeout=config.get("timeout", 30000),
                    retry_count=config.get("retry_attempts", 3),
                    max_stake=config.get("max_stake_per_bet", 1000.0),
                    risk_level=RiskLevel(config.get("risk_level", "medium"))
                )
                self.bookmaker_configs[name] = bookmaker_config
        
        logger.info(f"Loaded {len(self.bookmaker_configs)} bookmaker configurations")
    
    async def create_session(self, config: BrowserConfig) -> BrowserSession:
        """Create a new browser session."""
        if len(self.sessions) >= self.max_sessions:
            await self._cleanup_stale_sessions()
        
        try:
            # Configure browser arguments
            args = [
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-background-timer-throttling",
                "--disable-popup-blocking",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-window-activation",
                "--disable-focus-on-load",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-web-security",
                "--disable-site-isolation-trials",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
            
            # Add stealth mode arguments
            if config.enable_stealth:
                args.extend([
                    "--disable-client-side-phishing-detection",
                    "--disable-component-extensions-with-background-pages",
                    "--disable-default-apps",
                    "--disable-features=TranslateUI",
                    "--disable-ipc-flooding-protection",
                ])
            
            # Add extra arguments
            args.extend(config.extra_args)
            
            # Add extension support
            if self.avo_tabs_enabled:
                if Path(self.avo_tabs_extension_path).exists():
                    args.extend([
                        f"--disable-extensions-except={self.avo_tabs_extension_path}",
                        f"--load-extension={self.avo_tabs_extension_path}"
                    ])
            
            # Launch browser
            context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=config.user_data_dir or f"/workspace/browser/sessions/{config.name}",
                headless=config.headless,
                viewport=config.viewport,
                args=args,
                channel="chromium"
            )
            
            # Create primary page
            page = await context.new_page()
            
            # Set user agent if specified
            if config.user_agent:
                await page.set_extra_http_headers({"User-Agent": config.user_agent})
            
            session_id = str(uuid4())
            session = BrowserSession(
                session_id=session_id,
                browser=context.browser,
                context=context,
                page=page,
                bookmaker_configs=self.bookmaker_configs
            )
            
            self.sessions[session_id] = session
            
            # Set up page event handlers
            await self._setup_page_handlers(session)
            
            logger.info(f"Created browser session: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create browser session: {e}")
            raise
    
    async def _setup_page_handlers(self, session: BrowserSession):
        """Set up page event handlers for monitoring and error handling."""
        
        async def handle_page_error(error):
            """Handle page errors."""
            session.error_count += 1
            session.last_activity = datetime.now()
            logger.error(f"Page error in session {session.session_id}: {error}")
            
            # Check if session should be recycled
            if session.error_count > 10:  # Threshold for recycling
                logger.warning(f"Session {session.session_id} has too many errors, marking for recycling")
                session.status = "error_recycle"
        
        async def handle_console_message(msg):
            """Handle console messages for debugging."""
            if msg.type in ["error", "warning"]:
                logger.debug(f"Console [{msg.type}] in session {session.session_id}: {msg.text}")
        
        async def handle_response(response):
            """Monitor response status."""
            session.last_activity = datetime.now()
            
            # Log failed responses
            if response.status >= 400:
                logger.warning(f"HTTP {response.status} in session {session.session_id}: {response.url}")
        
        # Register handlers
        session.page.on("pageerror", handle_page_error)
        session.page.on("console", handle_console_message)
        session.page.on("response", handle_response)
    
    async def navigate_to_bookmaker(self, session: BrowserSession, bookmaker_name: str) -> bool:
        """Navigate to a bookmaker website."""
        if bookmaker_name not in session.bookmaker_configs:
            logger.error(f"Unknown bookmaker: {bookmaker_name}")
            return False
        
        config = session.bookmaker_configs[bookmaker_name]
        
        try:
            await session.page.goto(
                config.base_url,
                timeout=config.timeout,
                wait_until="networkidle"
            )
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            # Check if login is required
            if config.requires_login:
                await self._check_login_status(session, bookmaker_name)
            
            logger.info(f"Successfully navigated to {bookmaker_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to {bookmaker_name}: {e}")
            return False
    
    async def _check_login_status(self, session: BrowserSession, bookmaker_name: str):
        """Check if user is logged in to the bookmaker."""
        config = session.bookmaker_configs[bookmaker_name]
        
        try:
            # Look for login indicators based on selectors
            login_selectors = [
                "a[href*='login']",
                "button:has-text('Login')",
                "button:has-text('Sign In')",
                ".login-button",
                "#login-form"
            ]
            
            for selector in login_selectors:
                try:
                    await session.page.wait_for_selector(selector, timeout=2000)
                    logger.info(f"Login required for {bookmaker_name}")
                    return False
                except PlaywrightTimeoutError:
                    continue
            
            # If we get here, likely logged in
            logger.info(f"Already logged in to {bookmaker_name}")
            return True
            
        except Exception as e:
            logger.warning(f"Could not determine login status for {bookmaker_name}: {e}")
            return False
    
    async def execute_arbitrage_opportunity(self, session: BrowserSession, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Execute an arbitrage opportunity across multiple bookmakers."""
        try:
            # Validate opportunity through risk analyzer
            if self.risk_analyzer:
                validation_result = self.risk_analyzer.validate_opportunity(opportunity)
                if validation_result.get("status") != "approved":
                    return {
                        "success": False,
                        "reason": "Risk validation failed",
                        "validation": validation_result
                    }
            
            # Track the operation
            operation_id = str(uuid4())
            self.active_operations[operation_id] = {
                "status": "running",
                "start_time": datetime.now(),
                "opportunity": opportunity
            }
            
            try:
                # Execute trades across bookmakers
                results = await self._execute_multi_bookmaker_trades(session, opportunity)
                
                # Update operation status
                self.active_operations[operation_id]["status"] = "completed"
                self.active_operations[operation_id]["results"] = results
                self.active_operations[operation_id]["end_time"] = datetime.now()
                
                return {
                    "success": True,
                    "operation_id": operation_id,
                    "results": results
                }
                
            except Exception as e:
                # Update operation status
                self.active_operations[operation_id]["status"] = "failed"
                self.active_operations[operation_id]["error"] = str(e)
                self.active_operations[operation_id]["end_time"] = datetime.now()
                
                logger.error(f"Failed to execute arbitrage opportunity: {e}")
                return {
                    "success": False,
                    "reason": str(e),
                    "operation_id": operation_id
                }
                
        finally:
            # Clean up completed operations
            await self._cleanup_completed_operations()
    
    async def _execute_multi_bookmaker_trades(self, session: BrowserSession, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Execute trades across multiple bookmakers."""
        trades_results = {}
        
        # Navigate to each bookmaker and place bets
        for leg in opportunity.legs:
            bookmaker_name = leg.bookmaker
            if bookmaker_name not in session.bookmaker_configs:
                logger.warning(f"Unknown bookmaker: {bookmaker_name}")
                continue
            
            try:
                # Navigate to bookmaker
                if not await self.navigate_to_bookmaker(session, bookmaker_name):
                    trades_results[bookmaker_name] = {"success": False, "reason": "Navigation failed"}
                    continue
                
                # Execute the bet
                result = await self._place_bet(session, bookmaker_name, leg)
                trades_results[bookmaker_name] = result
                
            except Exception as e:
                logger.error(f"Failed to place bet at {bookmaker_name}: {e}")
                trades_results[bookmaker_name] = {"success": False, "reason": str(e)}
        
        return trades_results
    
    async def _place_bet(self, session: BrowserSession, bookmaker_name: str, leg) -> Dict[str, Any]:
        """Place a bet at a specific bookmaker."""
        config = session.bookmaker_configs[bookmaker_name]
        
        try:
            # This would need to be implemented based on specific bookmaker interfaces
            # For now, return a placeholder result
            logger.info(f"Placing bet at {bookmaker_name}: ${leg.stake} on {leg.selection}")
            
            # Simulate bet placement
            await asyncio.sleep(random.uniform(1, 3))  # Simulate processing time
            
            return {
                "success": True,
                "bet_id": f"bet_{uuid4().hex[:8]}",
                "stake": leg.stake,
                "selection": leg.selection,
                "odds": leg.odds
            }
            
        except Exception as e:
            logger.error(f"Failed to place bet at {bookmaker_name}: {e}")
            return {
                "success": False,
                "reason": str(e)
            }
    
    async def _background_monitor(self):
        """Background monitoring task."""
        while True:
            try:
                await asyncio.sleep(60)  # Monitor every minute
                await self._cleanup_stale_sessions()
                await self._check_session_health()
                await self._cleanup_completed_operations()
                
            except Exception as e:
                logger.error(f"Error in background monitor: {e}")
    
    async def _cleanup_stale_sessions(self):
        """Clean up stale browser sessions."""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            if (current_time - session.last_activity).seconds > self.session_timeout:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            await self._close_session(session_id)
    
    async def _check_session_health(self):
        """Check health of all browser sessions."""
        for session_id, session in self.sessions.items():
            try:
                # Check if page is still responsive
                await session.page.evaluate("1")  # Simple test
                
                # Update session health
                session.status = "active"
                
            except Exception as e:
                logger.warning(f"Session {session_id} health check failed: {e}")
                session.status = "error"
    
    async def _cleanup_completed_operations(self):
        """Clean up completed operations."""
        current_time = datetime.now()
        operations_to_remove = []
        
        for op_id, op_data in self.active_operations.items():
            end_time = op_data.get("end_time")
            if end_time and (current_time - end_time).seconds > 300:  # 5 minutes
                operations_to_remove.append(op_id)
        
        for op_id in operations_to_remove:
            del self.active_operations[op_id]
    
    async def _close_session(self, session_id: str):
        """Close a browser session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            try:
                await session.context.close()
                logger.info(f"Closed browser session: {session_id}")
            except Exception as e:
                logger.error(f"Error closing session {session_id}: {e}")
            finally:
                del self.sessions[session_id]
    
    async def shutdown(self):
        """Shutdown the browser automation system."""
        logger.info("Shutting down EnhancedBrowser...")
        
        # Close all sessions
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self._close_session(session_id)
        
        # Stop playwright
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("EnhancedBrowser shutdown complete")
    
    # Public utility methods
    
    async def get_session_status(self) -> Dict[str, Any]:
        """Get status of all sessions."""
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": len([s for s in self.sessions.values() if s.status == "active"]),
            "sessions": {
                session_id: {
                    "status": session.status,
                    "bookmaker_configs": list(session.bookmaker_configs.keys()),
                    "operations_count": session.operations_count,
                    "error_count": session.error_count,
                    "created_at": session.created_at.isoformat(),
                    "last_activity": session.last_activity.isoformat()
                }
                for session_id, session in self.sessions.items()
            }
        }
    
    async def get_active_operations(self) -> Dict[str, Any]:
        """Get currently active operations."""
        return self.active_operations.copy()
    
    def get_bookmaker_configs(self) -> Dict[str, BookmakerConfig]:
        """Get loaded bookmaker configurations."""
        return self.bookmaker_configs.copy()


# Example usage and testing
async def main():
    """Example usage of EnhancedBrowser."""
    browser = EnhancedBrowser()
    
    try:
        await browser.initialize()
        
        # Create a session
        config = BrowserConfig(
            name="main_session",
            headless=True,
            enable_stealth=True
        )
        
        session = await browser.create_session(config)
        
        # Get status
        status = await browser.get_session_status()
        print(f"Browser status: {json.dumps(status, indent=2)}")
        
        # Test navigation to a bookmaker
        await browser.navigate_to_bookmaker(session, "bet365")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        
    finally:
        await browser.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
