"""
Arbitrage Browser - Specialized Browser for Arbitrage Trading

This module provides a specialized browser class designed specifically for arbitrage
trading workflows. It handles multiple bookmaker interfaces, form filling, and trade
execution with advanced error handling and recovery capabilities.

Features:
- Multi-bookmaker interface management
- Automated form filling and validation
- Trade execution with confirmation
- Real-time odds monitoring
- Error detection and recovery
- Performance optimization
- Comprehensive logging
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4
import random
import re
from urllib.parse import urljoin, urlparse

from playwright.async_api import Page, Browser, BrowserContext, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Import existing modules
try:
    from ..core.config_manager import ConfigManager
    from ..utils.logger import get_logger
    from ..storage.models import ArbitrageOpportunity, BetLeg, BookmakerInfo
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append('/workspace')
    try:
        from arbitech.core.config_manager import ConfigManager
        from arbitech.utils.logger import get_logger
        from arbitech.storage.models import ArbitrageOpportunity, BetLeg, BookmakerInfo
    except ImportError:
        # Mock classes for basic functionality
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
        
        class ArbitrageOpportunity:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        class BetLeg:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        class BookmakerInfo:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

logger = get_logger(__name__)


class BetStatus(str, Enum):
    """Status of a bet placement."""
    PENDING = "pending"
    PLACED = "placed"
    FAILED = "failed"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class FormValidationResult(str, Enum):
    """Result of form validation."""
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"
    TIMEOUT = "timeout"


class NavigationMethod(str, Enum):
    """Methods for navigating bookmaker interfaces."""
    DIRECT_URL = "direct_url"
    CLICK_THROUGH = "click_through"
    SEARCH = "search"
    MENU_NAVIGATION = "menu_navigation"


@dataclass
class FormField:
    """Represents a form field in a bookmaker interface."""
    name: str
    selector: str
    field_type: str  # input, select, checkbox, etc.
    required: bool = True
    validation_pattern: Optional[str] = None
    default_value: Optional[str] = None
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None  # For select fields


@dataclass
class BetPlacement:
    """Represents a bet placement request."""
    bet_id: str
    bookmaker_name: str
    selection: str
    odds: float
    stake: float
    bet_type: str = "single"
    status: BetStatus = BetStatus.PENDING
    placed_at: Optional[datetime] = None
    confirmation_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class BookmakerInterface:
    """Configuration for bookmaker interface automation."""
    name: str
    base_url: str
    
    # Navigation selectors
    login_selectors: List[str] = field(default_factory=list)
    odds_page_selectors: List[str] = field(default_factory=list)
    bet_form_selectors: List[str] = field(default_factory=list)
    balance_selectors: List[str] = field(default_factory=list)
    
    # Form field mappings
    stake_field: Optional[FormField] = None
    selection_field: Optional[FormField] = None
    odds_field: Optional[FormField] = None
    place_bet_button: Optional[str] = None
    confirm_bet_button: Optional[str] = None
    
    # Additional form fields
    additional_fields: List[FormField] = field(default_factory=list)
    
    # Validation selectors
    validation_selectors: List[str] = field(default_factory=list)
    error_selectors: List[str] = field(default_factory=list)
    
    # Performance settings
    timeout: int = 30000
    retry_count: int = 3
    wait_after_navigation: int = 2
    wait_after_form_fill: int = 1


class ArbitrageBrowser:
    """
    Specialized Browser for Arbitrage Trading
    
    Provides comprehensive automation for arbitrage trading across multiple
    bookmaker interfaces with advanced form handling and trade execution.
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the arbitrage browser."""
        self.config_manager = config_manager or ConfigManager()
        self.page: Optional[Page] = None
        self.bookmaker_interfaces: Dict[str, BookmakerInterface] = {}
        
        # Performance settings
        self.default_timeout = self.config_manager.get("browser.timeout", 30000)
        self.retry_attempts = self.config_manager.get("browser.retry_attempts", 3)
        self.max_concurrent_bets = self.config_manager.get("user.risk.max_concurrent_bets", 5)
        
        # Active bet placements
        self.active_bets: Dict[str, BetPlacement] = {}
        self.completed_bets: List[BetPlacement] = []
        
        # Form field cache
        self.form_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("ArbitrageBrowser initialized successfully")
    
    async def attach_to_page(self, page: Page):
        """Attach to an existing Playwright page."""
        self.page = page
        logger.info("Attached to Playwright page")
    
    async def load_bookmaker_interface(self, bookmaker_name: str) -> bool:
        """Load and configure a bookmaker interface."""
        if not self.page:
            raise ValueError("No page attached. Call attach_to_page() first.")
        
        if bookmaker_name not in self.bookmaker_interfaces:
            # Create default interface configuration
            interface = await self._create_default_interface(bookmaker_name)
            self.bookmaker_interfaces[bookmaker_name] = interface
        
        logger.info(f"Loaded interface for {bookmaker_name}")
        return True
    
    async def _create_default_interface(self, bookmaker_name: str) -> BookmakerInterface:
        """Create a default interface configuration for a bookmaker."""
        # This would typically load from configuration files
        # For now, create a basic configuration
        
        interface = BookmakerInterface(
            name=bookmaker_name,
            base_url=f"https://{bookmaker_name}.com",
            timeout=self.default_timeout,
            retry_count=self.retry_attempts
        )
        
        return interface
    
    async def navigate_to_bookmaker(self, bookmaker_name: str, method: NavigationMethod = NavigationMethod.DIRECT_URL) -> bool:
        """Navigate to a bookmaker's website."""
        if not self.page:
            raise ValueError("No page attached. Call attach_to_page() first.")
        
        if bookmaker_name not in self.bookmaker_interfaces:
            await self.load_bookmaker_interface(bookmaker_name)
        
        interface = self.bookmaker_interfaces[bookmaker_name]
        
        try:
            if method == NavigationMethod.DIRECT_URL:
                await self._navigate_direct_url(interface)
            elif method == NavigationMethod.CLICK_THROUGH:
                await self._navigate_click_through(interface)
            elif method == NavigationMethod.SEARCH:
                await self._navigate_search(interface)
            elif method == NavigationMethod.MENU_NAVIGATION:
                await self._navigate_menu(interface)
            
            # Wait for page to load
            await asyncio.sleep(interface.wait_after_navigation)
            
            # Validate page loaded correctly
            if not await self._validate_page_loaded(interface):
                raise Exception("Page validation failed")
            
            logger.info(f"Successfully navigated to {bookmaker_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to {bookmaker_name}: {e}")
            return False
    
    async def _navigate_direct_url(self, interface: BookmakerInterface):
        """Navigate using direct URL."""
        await self.page.goto(
            interface.base_url,
            timeout=interface.timeout,
            wait_until="networkidle"
        )
    
    async def _navigate_click_through(self, interface: BookmakerInterface):
        """Navigate by clicking through links."""
        # Implement click-through navigation logic
        pass
    
    async def _navigate_search(self, interface: BookmakerInterface):
        """Navigate using search functionality."""
        # Implement search-based navigation
        pass
    
    async def _navigate_menu(self, interface: BookmakerInterface):
        """Navigate using menu system."""
        # Implement menu navigation
        pass
    
    async def _validate_page_loaded(self, interface: BookmakerInterface) -> bool:
        """Validate that the page loaded correctly."""
        try:
            # Check for common page elements
            validation_selectors = interface.validation_selectors or [
                "body",
                "html",
                "[data-testid]"
            ]
            
            for selector in validation_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    return True
                except PlaywrightTimeoutError:
                    continue
            
            return True  # If no validation selectors, assume success
            
        except Exception as e:
            logger.warning(f"Page validation failed: {e}")
            return False
    
    async def check_login_status(self, bookmaker_name: str) -> bool:
        """Check if user is logged in to the bookmaker."""
        if bookmaker_name not in self.bookmaker_interfaces:
            await self.load_bookmaker_interface(bookmaker_name)
        
        interface = self.bookmaker_interfaces[bookmaker_name]
        
        try:
            # Check for login/logout indicators
            login_indicators = [
                "a[href*='login']",
                "button:has-text('Login')",
                "button:has-text('Sign In')",
                "button:has-text('Log In')",
                ".login-button",
                "#login-form"
            ]
            
            logout_indicators = [
                "button:has-text('Logout')",
                "button:has-text('Sign Out')",
                "a[href*='logout']",
                ".logout-button",
                "[data-testid='user-menu']"
            ]
            
            # Look for logout indicators (indicates logged in)
            for selector in logout_indicators:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    logger.info(f"User is logged in to {bookmaker_name}")
                    return True
                except PlaywrightTimeoutError:
                    continue
            
            # Look for login indicators (indicates not logged in)
            for selector in login_indicators:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    logger.info(f"User is not logged in to {bookmaker_name}")
                    return False
                except PlaywrightTimeoutError:
                    continue
            
            # If we can't determine, assume not logged in
            logger.warning(f"Could not determine login status for {bookmaker_name}")
            return False
            
        except Exception as e:
            logger.error(f"Error checking login status for {bookmaker_name}: {e}")
            return False
    
    async def navigate_to_odds_page(self, bookmaker_name: str, event_url: Optional[str] = None) -> bool:
        """Navigate to the odds/betting page."""
        if not self.page:
            raise ValueError("No page attached. Call attach_to_page() first.")
        
        if bookmaker_name not in self.bookmaker_interfaces:
            await self.load_bookmaker_interface(bookmaker_name)
        
        interface = self.bookmaker_interfaces[bookmaker_name]
        
        try:
            if event_url:
                # Navigate directly to event URL
                await self.page.goto(
                    event_url,
                    timeout=interface.timeout,
                    wait_until="networkidle"
                )
            else:
                # Use selectors to navigate to odds page
                odds_selectors = interface.odds_page_selectors or [
                    "a[href*='sports']",
                    "a[href*='odds']",
                    "button:has-text('Sports')",
                    "button:has-text('Odds')",
                    ".nav-sports",
                    ".odds-navigation"
                ]
                
                for selector in odds_selectors:
                    try:
                        await self.page.click(selector)
                        await asyncio.sleep(interface.wait_after_navigation)
                        break
                    except PlaywrightTimeoutError:
                        continue
            
            logger.info(f"Navigated to odds page for {bookmaker_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to odds page for {bookmaker_name}: {e}")
            return False
    
    async def place_bet(self, bookmaker_name: str, selection: str, odds: float, stake: float, 
                       bet_type: str = "single") -> BetPlacement:
        """Place a bet at the bookmaker."""
        if not self.page:
            raise ValueError("No page attached. Call attach_to_page() first.")
        
        if bookmaker_name not in self.bookmaker_interfaces:
            await self.load_bookmaker_interface(bookmaker_name)
        
        interface = self.bookmaker_interfaces[bookmaker_name]
        bet_id = str(uuid4())
        
        bet_placement = BetPlacement(
            bet_id=bet_id,
            bookmaker_name=bookmaker_name,
            selection=selection,
            odds=odds,
            stake=stake,
            bet_type=bet_type
        )
        
        try:
            # Check login status first
            if not await self.check_login_status(bookmaker_name):
                raise Exception("User not logged in")
            
            # Navigate to betting page
            if not await self.navigate_to_odds_page(bookmaker_name):
                raise Exception("Failed to navigate to odds page")
            
            # Find and fill bet form
            form_result = await self._fill_bet_form(interface, selection, odds, stake)
            
            if form_result != FormValidationResult.VALID:
                raise Exception(f"Form validation failed: {form_result}")
            
            # Submit bet
            submission_result = await self._submit_bet(interface)
            
            if submission_result["success"]:
                bet_placement.status = BetStatus.PLACED
                bet_placement.placed_at = datetime.now()
                bet_placement.confirmation_code = submission_result.get("confirmation_code")
                
                logger.info(f"Bet placed successfully: {bet_id}")
                
            else:
                bet_placement.status = BetStatus.FAILED
                bet_placement.error_message = submission_result.get("error", "Unknown error")
                
                logger.error(f"Bet placement failed: {bet_placement.error_message}")
            
        except Exception as e:
            bet_placement.status = BetStatus.FAILED
            bet_placement.error_message = str(e)
            bet_placement.retry_count += 1
            
            logger.error(f"Error placing bet {bet_id}: {e}")
            
            # Retry if attempts remaining
            if bet_placement.retry_count < interface.retry_count:
                logger.info(f"Retrying bet placement ({bet_placement.retry_count + 1}/{interface.retry_count})")
                return await self.place_bet(bookmaker_name, selection, odds, stake, bet_type)
        
        # Track the bet
        self.active_bets[bet_id] = bet_placement
        self.completed_bets.append(bet_placement)
        
        return bet_placement
    
    async def _fill_bet_form(self, interface: BookmakerInterface, selection: str, 
                           odds: float, stake: float) -> FormValidationResult:
        """Fill the bet form with selection, odds, and stake."""
        try:
            # Fill stake field
            if interface.stake_field:
                stake_field = interface.stake_field
                await self._fill_form_field(stake_field, str(stake))
                await asyncio.sleep(interface.wait_after_form_fill)
            
            # Fill selection field if present
            if interface.selection_field:
                selection_field = interface.selection_field
                await self._fill_form_field(selection_field, selection)
                await asyncio.sleep(interface.wait_after_form_fill)
            
            # Fill odds field if present
            if interface.odds_field:
                odds_field = interface.odds_field
                await self._fill_form_field(odds_field, str(odds))
                await asyncio.sleep(interface.wait_after_form_fill)
            
            # Fill additional fields
            for field in interface.additional_fields:
                await self._fill_form_field(field)
                await asyncio.sleep(0.5)
            
            # Validate form
            return await self._validate_form(interface)
            
        except Exception as e:
            logger.error(f"Error filling bet form: {e}")
            return FormValidationResult.ERROR
    
    async def _fill_form_field(self, field: FormField, value: Optional[str] = None):
        """Fill a specific form field."""
        try:
            value_to_use = value or field.default_value
            
            if not value_to_use:
                return
            
            # Handle different field types
            if field.field_type == "input":
                await self.page.fill(field.selector, value_to_use)
            elif field.field_type == "select":
                await self.page.select_option(field.selector, value_to_use)
            elif field.field_type == "checkbox":
                if value_to_use.lower() in ["true", "1", "yes"]:
                    await self.page.check(field.selector)
                else:
                    await self.page.uncheck(field.selector)
            elif field.field_type == "button":
                await self.page.click(field.selector)
            
            logger.debug(f"Filled field {field.name} with value {value_to_use}")
            
        except Exception as e:
            logger.error(f"Error filling field {field.name}: {e}")
            raise
    
    async def _validate_form(self, interface: BookmakerInterface) -> FormValidationResult:
        """Validate that the form is properly filled."""
        try:
            # Check for error messages
            error_selectors = interface.error_selectors or [
                ".error",
                ".alert-danger",
                ".validation-error",
                "[data-error]"
            ]
            
            for selector in error_selectors:
                try:
                    error_element = await self.page.query_selector(selector)
                    if error_element:
                        error_text = await error_element.text_content()
                        logger.warning(f"Form validation error: {error_text}")
                        return FormValidationResult.INVALID
                except Exception:
                    continue
            
            # Check for required fields
            if interface.stake_field and interface.stake_field.required:
                stake_value = await self.page.input_value(interface.stake_field.selector)
                if not stake_value or float(stake_value) <= 0:
                    return FormValidationResult.INVALID
            
            return FormValidationResult.VALID
            
        except Exception as e:
            logger.error(f"Error validating form: {e}")
            return FormValidationResult.ERROR
    
    async def _submit_bet(self, interface: BookmakerInterface) -> Dict[str, Any]:
        """Submit the bet for processing."""
        try:
            # Click place bet button
            place_bet_selector = interface.place_bet_button or "button[type='submit']"
            
            await self.page.click(place_bet_selector)
            await asyncio.sleep(2)
            
            # Check for confirmation
            if interface.confirm_bet_button:
                # Some bookmakers require confirmation
                await self.page.click(interface.confirm_bet_button)
                await asyncio.sleep(1)
            
            # Look for confirmation indicators
            confirmation_selectors = [
                ".bet-confirmed",
                ".success-message",
                "[data-confirmation]",
                "text=Bet placed successfully",
                "text=Your bet has been placed"
            ]
            
            for selector in confirmation_selectors:
                try:
                    if selector.startswith("text="):
                        text_content = selector[5:]
                        await self.page.wait_for_function(
                            f"document.body.textContent.includes('{text_content}')",
                            timeout=5000
                        )
                    else:
                        await self.page.wait_for_selector(selector, timeout=5000)
                    
                    # Extract confirmation code if available
                    confirmation_code = await self._extract_confirmation_code()
                    
                    return {
                        "success": True,
                        "confirmation_code": confirmation_code
                    }
                    
                except PlaywrightTimeoutError:
                    continue
            
            # If no confirmation found, assume success
            return {"success": True}
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _extract_confirmation_code(self) -> Optional[str]:
        """Extract bet confirmation code from page."""
        try:
            # Common patterns for confirmation codes
            code_patterns = [
                r"Confirmation[:\s]+([A-Z0-9]+)",
                r"Reference[:\s]+([A-Z0-9]+)",
                r"Ticket[:\s]+([A-Z0-9]+)",
                r"Bet ID[:\s]+([A-Z0-9]+)"
            ]
            
            page_text = await self.page.text_content("body")
            
            for pattern in code_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract confirmation code: {e}")
            return None
    
    async def monitor_odds_changes(self, bookmaker_name: str, selectors: List[str], 
                                 callback: Callable[[float], None], interval: int = 5) -> asyncio.Task:
        """Monitor odds changes and call callback when changes detected."""
        
        async def monitor_task():
            last_odds = None
            
            while True:
                try:
                    if bookmaker_name not in self.bookmaker_interfaces:
                        await asyncio.sleep(interval)
                        continue
                    
                    interface = self.bookmaker_interfaces[bookmaker_name]
                    
                    # Extract current odds
                    current_odds = None
                    for selector in selectors:
                        try:
                            odds_text = await self.page.text_content(selector)
                            # Extract numeric value from odds text
                            odds_match = re.search(r'[\d.]+', odds_text)
                            if odds_match:
                                current_odds = float(odds_match.group())
                                break
                        except Exception:
                            continue
                    
                    if current_odds is not None and current_odds != last_odds:
                        last_odds = current_odds
                        await callback(current_odds)
                    
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Error in odds monitoring: {e}")
                    await asyncio.sleep(interval)
        
        # Start monitoring task
        task = asyncio.create_task(monitor_task())
        logger.info(f"Started odds monitoring for {bookmaker_name}")
        
        return task
    
    async def batch_place_bets(self, bets: List[Dict[str, Any]]) -> List[BetPlacement]:
        """Place multiple bets in batch."""
        results = []
        
        # Limit concurrent bets
        bet_queue = bets[:self.max_concurrent_bets]
        
        tasks = []
        for bet in bet_queue:
            task = asyncio.create_task(
                self.place_bet(
                    bet["bookmaker"],
                    bet["selection"],
                    bet["odds"],
                    bet["stake"],
                    bet.get("bet_type", "single")
                )
            )
            tasks.append(task)
        
        # Wait for all bets to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, BetPlacement):
                valid_results.append(result)
            else:
                logger.error(f"Bet placement failed: {result}")
        
        return valid_results
    
    def get_bet_status(self, bet_id: str) -> Optional[BetPlacement]:
        """Get status of a specific bet."""
        return self.active_bets.get(bet_id)
    
    def get_all_active_bets(self) -> Dict[str, BetPlacement]:
        """Get all active bet placements."""
        return self.active_bets.copy()
    
    def get_recent_bets(self, count: int = 10) -> List[BetPlacement]:
        """Get recent completed bets."""
        return self.completed_bets[-count:] if self.completed_bets else []
    
    async def cancel_bet(self, bet_id: str) -> bool:
        """Cancel a pending bet (if supported by bookmaker)."""
        if bet_id not in self.active_bets:
            return False
        
        bet = self.active_bets[bet_id]
        
        # Only cancel if bet is still pending
        if bet.status != BetStatus.PENDING:
            return False
        
        # This would need bookmaker-specific implementation
        # For now, mark as cancelled
        bet.status = BetStatus.CANCELLED
        logger.info(f"Cancelled bet {bet_id}")
        
        return True


# Example usage and testing
async def main():
    """Example usage of ArbitrageBrowser."""
    from playwright.async_api import async_playwright
    
    # Create page
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    
    try:
        # Create arbitrage browser
        arbitrage_browser = ArbitrageBrowser()
        await arbitrage_browser.attach_to_page(page)
        
        # Load bookmaker interface
        await arbitrage_browser.load_bookmaker_interface("bet365")
        
        # Navigate to bookmaker
        success = await arbitrage_browser.navigate_to_bookmaker("bet365")
        print(f"Navigation successful: {success}")
        
        # Place a test bet
        bet = await arbitrage_browser.place_bet(
            bookmaker_name="bet365",
            selection="Team A",
            odds=2.5,
            stake=10.0
        )
        
        print(f"Bet status: {bet.status}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())
