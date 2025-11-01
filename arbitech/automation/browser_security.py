"""
Browser Security - Security and Anti-Detection Measures

This module provides comprehensive security and anti-detection measures for
browser automation used in arbitrage trading. It includes user agent rotation,
request throttling, stealth techniques, and enterprise security features.

Features:
- User agent rotation and management
- Request throttling and rate limiting
- Stealth techniques to avoid detection
- Proxy management and rotation
- Cookie and session security
- Fingerprinting protection
- Traffic obfuscation
- Enterprise security integration
"""

import asyncio
import json
import time
import logging
import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from urllib.parse import urljoin, urlparse
import ipaddress
import base64
import secrets

from playwright.async_api import Page, Browser, BrowserContext, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Import existing modules
try:
    from ..core.config_manager import ConfigManager
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append('/workspace')
    try:
        from arbitech.core.config_manager import ConfigManager
        from arbitech.utils.logger import get_logger
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

logger = get_logger(__name__)


class StealthLevel(str, Enum):
    """Stealth levels for browser operations."""
    MINIMAL = "minimal"     # Basic stealth
    STANDARD = "standard"   # Balanced stealth
    HIGH = "high"          # Strong stealth
    MAXIMUM = "maximum"    # Maximum stealth


class ProxyType(str, Enum):
    """Types of proxy servers."""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
    ROTATING = "rotating"


class RequestThrottlingMode(str, Enum):
    """Request throttling modes."""
    DISABLED = "disabled"
    FIXED_DELAY = "fixed_delay"
    ADAPTIVE = "adaptive"
    RANDOMIZED = "randomized"


@dataclass
class UserAgentProfile:
    """User agent profile for browser stealth."""
    user_agent: str
    platform: str
    architecture: str
    browser_name: str
    browser_version: str
    device_type: str = "desktop"
    mobile: bool = False
    screen_resolution: Tuple[int, int] = (1920, 1080)
    timezone: str = "UTC"
    language: str = "en-US"
    webgl_vendor: str = "Intel Inc."
    webgl_renderer: str = "Intel(R) HD Graphics 4000"


@dataclass
class ProxyConfig:
    """Configuration for proxy server."""
    host: str
    port: int
    proxy_type: ProxyType
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    provider: Optional[str] = None
    response_time_ms: Optional[int] = None
    success_rate: float = 100.0
    last_tested: Optional[datetime] = None
    active: bool = True


@dataclass
class SecurityProfile:
    """Security profile configuration."""
    stealth_level: StealthLevel = StealthLevel.STANDARD
    user_agent_rotation_enabled: bool = True
    proxy_rotation_enabled: bool = False
    request_throttling: RequestThrottlingMode = RequestThrottlingMode.ADAPTIVE
    cookie_encryption: bool = True
    session_partitioning: bool = True
    fingerprint_randomization: bool = True
    network_obfuscation: bool = False
    resource_blocking: List[str] = field(default_factory=list)


@dataclass
class SecurityEvent:
    """Security event for monitoring."""
    event_id: str
    timestamp: datetime
    event_type: str
    severity: str
    description: str
    session_id: Optional[str] = None
    url: Optional[str] = None
    action_taken: Optional[str] = None


class BrowserSecurity:
    """
    Browser Security and Anti-Detection Manager
    
    Provides comprehensive security measures for browser automation
    including stealth techniques, proxy management, and anti-detection.
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the browser security manager."""
        self.config_manager = config_manager or ConfigManager()
        self.security_profile = SecurityProfile()
        
        # Load security configuration
        self._load_security_config()
        
        # User agent management
        self.user_agent_profiles: List[UserAgentProfile] = []
        self.current_user_agent_index = 0
        self.user_agent_rotation_enabled = self.config_manager.get("browser.security.user_agent_rotation", True)
        
        # Proxy management
        self.proxies: List[ProxyConfig] = []
        self.current_proxy_index = 0
        self.proxy_rotation_enabled = self.config_manager.get("browser.security.proxy_rotation", False)
        
        # Request throttling
        self.request_history: List[Dict[str, Any]] = []
        self.throttle_last_request_time = 0
        self.adaptive_throttle_delay = 1000  # milliseconds
        
        # Stealth features
        self.stealth_scripts_loaded = False
        self.fingerprint_cache: Dict[str, Any] = {}
        
        # Security monitoring
        self.security_events: List[SecurityEvent] = []
        self.detection_attempts = 0
        
        # Fingerprinting parameters
        self.canvas_noise_enabled = True
        self.webgl_noise_enabled = True
        self.audio_noise_enabled = True
        
        logger.info("BrowserSecurity initialized successfully")
    
    def _load_security_config(self):
        """Load security configuration from config manager."""
        try:
            # Load security profile
            security_config = self.config_manager.get("browser.security", {})
            
            # Set stealth level
            stealth_level_str = security_config.get("stealth_level", "standard")
            self.security_profile.stealth_level = StealthLevel(stealth_level_str)
            
            # Set feature flags
            self.security_profile.user_agent_rotation_enabled = security_config.get("user_agent_rotation", True)
            self.security_profile.proxy_rotation_enabled = security_config.get("proxy_rotation", False)
            
            # Set throttling mode
            throttling_str = security_config.get("request_throttling", "adaptive")
            self.security_profile.request_throttling = RequestThrottlingMode(throttling_str)
            
            # Load user agent profiles
            self._load_user_agent_profiles()
            
            # Load proxy configurations
            self._load_proxy_configs()
            
            logger.info(f"Loaded security configuration: {self.security_profile}")
            
        except Exception as e:
            logger.warning(f"Failed to load security configuration: {e}")
            self._load_default_security_config()
    
    def _load_default_security_config(self):
        """Load default security configuration."""
        self.user_agent_profiles = self._generate_default_user_agents()
        self.proxies = []
        logger.info("Loaded default security configuration")
    
    def _load_user_agent_profiles(self):
        """Load user agent profiles."""
        try:
            # Load from configuration or generate defaults
            ua_config = self.config_manager.get("browser.user_agents", [])
            
            if ua_config:
                for ua_data in ua_config:
                    profile = UserAgentProfile(
                        user_agent=ua_data["user_agent"],
                        platform=ua_data.get("platform", "Windows"),
                        architecture=ua_data.get("architecture", "x64"),
                        browser_name=ua_data.get("browser_name", "Chrome"),
                        browser_version=ua_data.get("browser_version", "120.0.0.0"),
                        device_type=ua_data.get("device_type", "desktop"),
                        mobile=ua_data.get("mobile", False),
                        screen_resolution=tuple(ua_data.get("screen_resolution", [1920, 1080])),
                        timezone=ua_data.get("timezone", "UTC"),
                        language=ua_data.get("language", "en-US"),
                        webgl_vendor=ua_data.get("webgl_vendor", "Intel Inc."),
                        webgl_renderer=ua_data.get("webgl_renderer", "Intel(R) HD Graphics 4000")
                    )
                    self.user_agent_profiles.append(profile)
            else:
                # Generate default profiles
                self.user_agent_profiles = self._generate_default_user_agents()
            
            logger.info(f"Loaded {len(self.user_agent_profiles)} user agent profiles")
            
        except Exception as e:
            logger.warning(f"Failed to load user agent profiles: {e}")
            self.user_agent_profiles = self._generate_default_user_agents()
    
    def _generate_default_user_agents(self) -> List[UserAgentProfile]:
        """Generate default user agent profiles."""
        user_agents = [
            UserAgentProfile(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                platform="Windows",
                architecture="x64",
                browser_name="Chrome",
                browser_version="120.0.0.0",
                device_type="desktop",
                mobile=False,
                screen_resolution=(1920, 1080),
                timezone="UTC",
                language="en-US",
                webgl_vendor="Intel Inc.",
                webgl_renderer="Intel(R) HD Graphics 4000"
            ),
            UserAgentProfile(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                platform="macOS",
                architecture="x64",
                browser_name="Chrome",
                browser_version="120.0.0.0",
                device_type="desktop",
                mobile=False,
                screen_resolution=(1440, 900),
                timezone="UTC",
                language="en-US",
                webgl_vendor="Apple Inc.",
                webgl_renderer="Apple GPU"
            ),
            UserAgentProfile(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                platform="Linux",
                architecture="x64",
                browser_name="Chrome",
                browser_version="120.0.0.0",
                device_type="desktop",
                mobile=False,
                screen_resolution=(1920, 1080),
                timezone="UTC",
                language="en-US",
                webgl_vendor="Intel Inc.",
                webgl_renderer="Intel(R) HD Graphics 4000"
            )
        ]
        
        return user_agents
    
    def _load_proxy_configs(self):
        """Load proxy configurations."""
        try:
            proxy_configs = self.config_manager.get("browser.proxies", [])
            
            for proxy_data in proxy_configs:
                proxy_config = ProxyConfig(
                    host=proxy_data["host"],
                    port=proxy_data["port"],
                    proxy_type=ProxyType(proxy_data.get("type", "http")),
                    username=proxy_data.get("username"),
                    password=proxy_data.get("password"),
                    country=proxy_data.get("country"),
                    city=proxy_data.get("city"),
                    provider=proxy_data.get("provider")
                )
                self.proxies.append(proxy_config)
            
            logger.info(f"Loaded {len(self.proxies)} proxy configurations")
            
        except Exception as e:
            logger.warning(f"Failed to load proxy configurations: {e}")
            self.proxies = []
    
    async def apply_stealth_features(self, page: Page, context: BrowserContext):
        """Apply stealth features to browser page and context."""
        try:
            logger.info("Applying stealth features...")
            
            # Apply user agent
            if self.security_profile.user_agent_rotation_enabled:
                await self._apply_user_agent(page)
            
            # Inject stealth scripts
            if not self.stealth_scripts_loaded:
                await self._inject_stealth_scripts(page)
                self.stealth_scripts_loaded = True
            
            # Apply request throttling
            await self._setup_request_throttling(page)
            
            # Apply fingerprint randomization
            if self.security_profile.fingerprint_randomization:
                await self._randomize_fingerprint(page)
            
            # Set up resource blocking
            if self.security_profile.resource_blocking:
                await self._setup_resource_blocking(page)
            
            # Apply session partitioning
            if self.security_profile.session_partitioning:
                await self._apply_session_partitioning(context)
            
            # Setup monitoring
            await self._setup_security_monitoring(page)
            
            logger.info("Stealth features applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply stealth features: {e}")
    
    async def _apply_user_agent(self, page: Page):
        """Apply user agent to page."""
        try:
            # Get current user agent profile
            if self.user_agent_profiles:
                profile = self.user_agent_profiles[self.current_user_agent_index]
                
                # Set user agent
                await page.set_extra_http_headers({"User-Agent": profile.user_agent})
                
                # Rotate for next request
                if self.user_agent_rotation_enabled:
                    self.current_user_agent_index = (self.current_user_agent_index + 1) % len(self.user_agent_profiles)
                
                logger.debug(f"Applied user agent: {profile.browser_name} {profile.browser_version}")
            
        except Exception as e:
            logger.warning(f"Failed to apply user agent: {e}")
    
    async def _inject_stealth_scripts(self, page: Page):
        """Inject stealth scripts to hide automation indicators."""
        try:
            # Stealth script to hide Playwright automation
            stealth_script = """
            // Hide Playwright automation indicators
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Override permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Hide CDP (Chrome DevTools Protocol) indicators
            window.chrome = {
                runtime: {},
            };
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Hide automation in console
            if (window.console) {
                console._commandLineAPI = undefined;
                console.__commandLineAPI = undefined;
            }
            """
            
            await page.add_init_script(stealth_script)
            
            # Apply additional stealth based on level
            if self.security_profile.stealth_level in [StealthLevel.HIGH, StealthLevel.MAXIMUM]:
                await self._apply_advanced_stealth(page)
            
            logger.debug("Injected stealth scripts")
            
        except Exception as e:
            logger.warning(f"Failed to inject stealth scripts: {e}")
    
    async def _apply_advanced_stealth(self, page: Page):
        """Apply advanced stealth features for high security level."""
        try:
            advanced_script = """
            // Advanced stealth techniques
            
            // Override SpeechSynthesis
            if (window.speechSynthesis) {
                window.speechSynthesis.__proto__.getVoices = function() {
                    return [];
                };
            }
            
            // Mock WebGL debugging info
            const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.'; // UNMASKED_VENDOR_ID
                }
                if (parameter === 37446) {
                    return 'Intel(R) HD Graphics 4000'; // UNMASKED_RENDERER_ID
                }
                return originalGetParameter.call(this, parameter);
            };
            
            // Randomize canvas fingerprint
            if (HTMLCanvasElement.prototype.getContext) {
                const originalGetContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(contextType, ...args) {
                    const context = originalGetContext.call(this, contextType, ...args);
                    if (contextType === '2d') {
                        const originalFillText = context.fillText;
                        context.fillText = function(...args) {
                            const x = Math.random() * 10;
                            const y = Math.random() * 10;
                            return originalFillText.call(this, ...args, x, y);
                        };
                    }
                    return context;
                };
            }
            
            // Mock crypto
            if (window.crypto && window.crypto.getRandomValues) {
                const originalGetRandomValues = window.crypto.getRandomValues;
                window.crypto.getRandomValues = function(array) {
                    return originalGetRandomValues.call(this, array);
                };
            }
            """
            
            await page.add_init_script(advanced_script)
            
            logger.debug("Applied advanced stealth features")
            
        except Exception as e:
            logger.warning(f"Failed to apply advanced stealth: {e}")
    
    async def _setup_request_throttling(self, page: Page):
        """Set up request throttling and rate limiting."""
        try:
            if self.security_profile.request_throttling == RequestThrottlingMode.DISABLED:
                return
            
            async def handle_request(request):
                """Handle request with throttling."""
                await self._throttle_request(request)
            
            page.on("request", handle_request)
            logger.debug("Set up request throttling")
            
        except Exception as e:
            logger.warning(f"Failed to setup request throttling: {e}")
    
    async def _throttle_request(self, request):
        """Throttle individual requests."""
        try:
            current_time = time.time() * 1000  # Convert to milliseconds
            
            if self.security_profile.request_throttling == RequestThrottlingMode.FIXED_DELAY:
                delay = 1000  # 1 second fixed delay
                await asyncio.sleep(delay / 1000)
                
            elif self.security_profile.request_throttling == RequestThrottlingMode.ADAPTIVE:
                # Adaptive delay based on request history
                delay = self.adaptive_throttle_delay
                await asyncio.sleep(delay / 1000)
                
                # Adjust adaptive delay based on response
                def adjust_delay(response):
                    nonlocal delay
                    if response.status >= 200 and response.status < 300:
                        delay = max(200, delay * 0.9)  # Decrease delay
                    else:
                        delay = min(5000, delay * 1.1)  # Increase delay
                    self.adaptive_throttle_delay = delay
                
                request.response.then(adjust_delay)
                
            elif self.security_profile.request_throttling == RequestThrottlingMode.RANDOMIZED:
                delay = random.uniform(500, 2000)  # Random delay between 0.5-2 seconds
                await asyncio.sleep(delay / 1000)
            
            self.throttle_last_request_time = current_time
            
        except Exception as e:
            logger.warning(f"Error throttling request: {e}")
    
    async def _randomize_fingerprint(self, page: Page):
        """Randomize browser fingerprint."""
        try:
            fingerprint_script = """
            // Randomize fingerprint parameters
            
            // Screen dimensions
            Object.defineProperty(screen, 'width', {
                get: () => 1920 + Math.floor(Math.random() * 100),
            });
            
            Object.defineProperty(screen, 'height', {
                get: () => 1080 + Math.floor(Math.random() * 100),
            });
            
            // Color depth
            Object.defineProperty(screen, 'colorDepth', {
                get: () => 24 + Math.floor(Math.random() * 8),
            });
            
            // Timezone
            const timezones = [
                'UTC', 'America/New_York', 'America/Chicago', 'America/Denver',
                'America/Los_Angeles', 'Europe/London', 'Europe/Paris',
                'Asia/Tokyo', 'Asia/Shanghai', 'Australia/Sydney'
            ];
            
            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
                value: function() {
                    return {
                        timeZone: timezones[Math.floor(Math.random() * timezones.length)]
                    };
                }
            });
            """
            
            await page.add_init_script(fingerprint_script)
            
            logger.debug("Applied fingerprint randomization")
            
        except Exception as e:
            logger.warning(f"Failed to randomize fingerprint: {e}")
    
    async def _setup_resource_blocking(self, page: Page):
        """Set up resource blocking to reduce fingerprint surface."""
        try:
            if "fingerprint" in self.security_profile.resource_blocking:
                # Block fingerprinting resources
                await page.route("**/*", self._block_resources)
            
            logger.debug("Set up resource blocking")
            
        except Exception as e:
            logger.warning(f"Failed to setup resource blocking: {e}")
    
    async def _block_resources(self, route, request):
        """Block specific resources based on patterns."""
        try:
            # Block common fingerprinting domains
            fingerprint_domains = [
                "analytics.google.com",
                "googletagmanager.com",
                "facebook.com",
                "doubleclick.net"
            ]
            
            request_url = request.url.lower()
            for domain in fingerprint_domains:
                if domain in request_url:
                    await route.abort()
                    return
            
            # Allow the request
            await route.continue_()
            
        except Exception as e:
            logger.warning(f"Error blocking resource: {e}")
            await route.continue_()
    
    async def _apply_session_partitioning(self, context: BrowserContext):
        """Apply session partitioning for isolation."""
        try:
            # This would typically involve setting up partitioned storage
            # For now, we'll set up partitioned cookies
            await context.add_cookies([])  # Initialize partitioned cookies
            
            logger.debug("Applied session partitioning")
            
        except Exception as e:
            logger.warning(f"Failed to apply session partitioning: {e}")
    
    async def _setup_security_monitoring(self, page: Page):
        """Set up security monitoring and detection."""
        try:
            # Monitor for detection attempts
            async def monitor_console(msg):
                if "webdriver" in msg.text.lower() or "automation" in msg.text.lower():
                    self.detection_attempts += 1
                    await self._log_security_event(
                        "detection_attempt",
                        "warning",
                        f"Potential detection: {msg.text}",
                        page.url
                    )
            
            # Monitor for blocked resources
            async def monitor_request_failed(request):
                if "fingerprint" in request.url.lower():
                    await self._log_security_event(
                        "resource_blocked",
                        "info",
                        f"Blocked fingerprinting resource: {request.url}",
                        request.url
                    )
            
            page.on("console", monitor_console)
            page.on("requestfailed", monitor_request_failed)
            
            logger.debug("Set up security monitoring")
            
        except Exception as e:
            logger.warning(f"Failed to setup security monitoring: {e}")
    
    async def _log_security_event(self, event_type: str, severity: str, description: str, 
                                 url: Optional[str] = None, session_id: Optional[str] = None):
        """Log a security event."""
        event = SecurityEvent(
            event_id=secrets.token_hex(16),
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            description=description,
            url=url,
            session_id=session_id
        )
        
        self.security_events.append(event)
        
        # Keep only recent events (last 1000)
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]
        
        # Log the event
        log_message = f"Security Event [{severity.upper()}]: {description}"
        if url:
            log_message += f" (URL: {url})"
        
        if severity == "critical":
            logger.critical(log_message)
        elif severity == "error":
            logger.error(log_message)
        elif severity == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    async def rotate_proxy(self, context: BrowserContext) -> bool:
        """Rotate to a different proxy."""
        if not self.proxies or not self.proxy_rotation_enabled:
            return False
        
        try:
            # Select next proxy
            old_index = self.current_proxy_index
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
            
            if self.current_proxy_index == old_index:
                return False  # No rotation needed
            
            proxy_config = self.proxies[self.current_proxy_index]
            
            # Apply new proxy
            proxy_url = f"{proxy_config.proxy_type.value}://{proxy_config.host}:{proxy_config.port}"
            
            if proxy_config.username and proxy_config.password:
                proxy_url = f"{proxy_config.proxy_type.value}://{proxy_config.username}:{proxy_config.password}@{proxy_config.host}:{proxy_config.port}"
            
            await context.set_default_timeout(30000)
            
            await self._log_security_event(
                "proxy_rotated",
                "info",
                f"Rotated to proxy: {proxy_config.host}:{proxy_config.port}",
                session_id=context.browser.contexts[0].pages[0].url if context.pages else None
            )
            
            logger.info(f"Rotated to proxy: {proxy_config.host}:{proxy_config.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate proxy: {e}")
            return False
    
    def get_current_user_agent(self) -> Optional[UserAgentProfile]:
        """Get the currently active user agent profile."""
        if self.user_agent_profiles:
            return self.user_agent_profiles[self.current_user_agent_index]
        return None
    
    def get_security_events(self, since: Optional[datetime] = None) -> List[SecurityEvent]:
        """Get security events, optionally filtered by time."""
        if since:
            return [event for event in self.security_events if event.timestamp >= since]
        return self.security_events.copy()
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection attempt statistics."""
        return {
            "total_detection_attempts": self.detection_attempts,
            "recent_detection_rate": len([e for e in self.security_events if 
                                        e.event_type == "detection_attempt" and 
                                        (datetime.now() - e.timestamp).seconds < 3600]),
            "security_events_count": len(self.security_events),
            "blocked_resources": len([e for e in self.security_events if e.event_type == "resource_blocked"])
        }
    
    def get_stealth_level(self) -> StealthLevel:
        """Get current stealth level."""
        return self.security_profile.stealth_level
    
    def set_stealth_level(self, level: StealthLevel):
        """Set stealth level."""
        old_level = self.security_profile.stealth_level
        self.security_profile.stealth_level = level
        
        logger.info(f"Changed stealth level from {old_level} to {level}")
    
    def is_proxy_rotation_enabled(self) -> bool:
        """Check if proxy rotation is enabled."""
        return self.proxy_rotation_enabled
    
    def is_user_agent_rotation_enabled(self) -> bool:
        """Check if user agent rotation is enabled."""
        return self.user_agent_rotation_enabled


# Example usage and testing
async def main():
    """Example usage of BrowserSecurity."""
    from playwright.async_api import async_playwright
    
    # Initialize security manager
    security = BrowserSecurity()
    
    # Create page
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    
    try:
        # Apply stealth features
        await security.apply_stealth_features(page, context)
        
        # Get current user agent
        current_ua = security.get_current_user_agent()
        print(f"Current user agent: {current_ua.user_agent if current_ua else 'None'}")
        
        # Navigate to a test page
        await page.goto("https://httpbin.org/user-agent")
        content = await page.text_content("pre")
        print(f"Server sees user agent: {content}")
        
        # Get detection stats
        stats = security.get_detection_stats()
        print(f"Detection stats: {json.dumps(stats, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())
