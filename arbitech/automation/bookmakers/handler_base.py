"""
Base Bookmaker Handler

Provides common functionality and interface abstraction for all bookmaker-specific handlers.
This class defines the template methods and common utilities needed across different betting platforms.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
import aiohttp
import yaml
from pathlib import Path


class HandlerStatus(Enum):
    """Handler status enumeration"""
    INITIALIZING = "initializing"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    MAINTENANCE = "maintenance"


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class BetRequest:
    """Standardized bet request structure"""
    market_id: str
    selection_id: str
    selection_name: str
    odds: float
    stake: float
    bet_type: str = "back"  # back, lay
    market_type: str = "match_odds"
    event_id: Optional[str] = None
    event_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BetResponse:
    """Standardized bet response structure"""
    success: bool
    bet_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    odds: Optional[float] = None
    stake: Optional[float] = None
    remaining_stake: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketData:
    """Market data structure"""
    market_id: str
    event_id: str
    event_name: str
    market_type: str
    selections: List[Dict[str, Any]]
    last_updated: float = field(default_factory=time.time)
    suspended: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionInfo:
    """Session information structure"""
    authenticated: bool = False
    session_token: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
    last_activity: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseBookmakerHandler(ABC):
    """
    Base class for all bookmaker handlers.
    
    Provides common functionality including:
    - Session management
    - Request/response handling
    - Error handling and recovery
    - Logging and monitoring
    - Configuration management
    - Health checking
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize base handler with configuration"""
        self.config = config
        self.bookmaker_name = self._get_bookmaker_name()
        self.status = HandlerStatus.INITIALIZING
        self.session_info = SessionInfo()
        self.logger = self._setup_logging()
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = self._setup_rate_limiter()
        self.health_check_interval = config.get('health_check_interval', 30)
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 10)
        
        # Performance metrics
        self.metrics = {
            'requests_count': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'last_health_check': 0.0,
            'errors': []
        }
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {
            'before_request': [],
            'after_request': [],
            'on_error': [],
            'on_authentication': [],
            'on_disconnect': [],
            'on_market_update': []
        }

    def _get_bookmaker_name(self) -> str:
        """Get the bookmaker name for this handler"""
        return self.__class__.__name__.replace('_handler', '').lower()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for this handler"""
        logger = logging.getLogger(f"arbitech.automation.bookmakers.{self.bookmaker_name}")
        return logger

    def _setup_rate_limiter(self) -> Dict[str, Any]:
        """Setup rate limiting configuration"""
        return {
            'requests_per_minute': self.config.get('rate_limit_rpm', 100),
            'requests_per_hour': self.config.get('rate_limit_rph', 1000),
            'last_reset': time.time()
        }

    async def initialize(self) -> bool:
        """Initialize the handler"""
        try:
            self.logger.info(f"Initializing {self.bookmaker_name} handler")
            self.status = HandlerStatus.CONNECTED
            
            # Setup HTTP session
            await self._setup_http_session()
            
            # Authenticate
            if await self.authenticate():
                self.status = HandlerStatus.AUTHENTICATED
                await self._emit_event('on_authentication')
                
                # Final initialization
                if await self._finalize_initialization():
                    self.status = HandlerStatus.READY
                    self.logger.info(f"{self.bookmaker_name} handler initialized successfully")
                    return True
            
            self.status = HandlerStatus.ERROR
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.bookmaker_name} handler: {e}")
            self.status = HandlerStatus.ERROR
            return False

    async def _setup_http_session(self) -> None:
        """Setup HTTP session with appropriate headers and settings"""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        headers = {
            'User-Agent': self.config.get('user_agent', 'ARBitech/1.0'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Add bookmaker-specific headers
        headers.update(self._get_auth_headers())
        
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        self.http_session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers,
            connector=connector
        )

    @abstractmethod
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get bookmaker-specific authentication headers"""
        pass

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the bookmaker"""
        pass

    async def _finalize_initialization(self) -> bool:
        """Finalize initialization (override in subclasses if needed)"""
        return True

    async def place_bet(self, bet_request: BetRequest) -> BetResponse:
        """Place a bet using the standardized interface"""
        try:
            await self._emit_event('before_request', bet_request)
            self.status = HandlerStatus.BUSY
            
            # Validate bet request
            if not self._validate_bet_request(bet_request):
                return BetResponse(
                    success=False,
                    error_message="Invalid bet request"
                )
            
            # Check authentication
            if not self.session_info.authenticated:
                return BetResponse(
                    success=False,
                    error_message="Not authenticated"
                )
            
            # Execute bookmaker-specific bet placement
            response = await self._execute_bet(bet_request)
            
            # Update metrics
            self._update_metrics(response.success)
            
            await self._emit_event('after_request', response)
            return response
            
        except Exception as e:
            self.logger.error(f"Error placing bet: {e}")
            await self._emit_event('on_error', e)
            return BetResponse(
                success=False,
                error_message=str(e)
            )
        finally:
            if self.status == HandlerStatus.BUSY:
                self.status = HandlerStatus.READY

    @abstractmethod
    async def _execute_bet(self, bet_request: BetRequest) -> BetResponse:
        """Execute bet placement (bookmaker-specific implementation)"""
        pass

    async def get_markets(self, filters: Dict[str, Any] = None) -> List[MarketData]:
        """Get available markets"""
        try:
            self.logger.debug(f"Getting markets for {self.bookmaker_name}")
            return await self._fetch_markets(filters or {})
        except Exception as e:
            self.logger.error(f"Error getting markets: {e}")
            return []

    @abstractmethod
    async def _fetch_markets(self, filters: Dict[str, Any]) -> List[MarketData]:
        """Fetch markets (bookmaker-specific implementation)"""
        pass

    async def get_odds(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get odds for a specific market"""
        try:
            return await self._fetch_odds(market_id)
        except Exception as e:
            self.logger.error(f"Error getting odds for market {market_id}: {e}")
            return None

    @abstractmethod
    async def _fetch_odds(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Fetch odds (bookmaker-specific implementation)"""
        pass

    async def cancel_bet(self, bet_id: str) -> bool:
        """Cancel a bet"""
        try:
            return await self._execute_cancel(bet_id)
        except Exception as e:
            self.logger.error(f"Error cancelling bet {bet_id}: {e}")
            return False

    @abstractmethod
    async def _execute_cancel(self, bet_id: str) -> bool:
        """Execute bet cancellation (bookmaker-specific implementation)"""
        pass

    def _validate_bet_request(self, bet_request: BetRequest) -> bool:
        """Validate bet request before submission"""
        # Basic validation
        if not all([bet_request.market_id, bet_request.selection_id, bet_request.odds, bet_request.stake]):
            return False
        
        if bet_request.odds <= 0 or bet_request.stake <= 0:
            return False
        
        # Bookmaker-specific validation
        return self._validate_bet_request_bookmaker_specific(bet_request)

    def _validate_bet_request_bookmaker_specific(self, bet_request: BetRequest) -> bool:
        """Bookmaker-specific bet request validation (override in subclasses)"""
        return True

    def _validate_stake_limits(self, stake: float) -> bool:
        """Validate stake against bookmaker limits"""
        min_stake = self.config.get('min_stake', 0.1)
        max_stake = self.config.get('max_stake', 1000.0)
        return min_stake <= stake <= max_stake

    def _validate_odds_limits(self, odds: float) -> bool:
        """Validate odds against bookmaker limits"""
        min_odds = self.config.get('min_odds', 1.01)
        max_odds = self.config.get('max_odds', 1000.0)
        return min_odds <= odds <= max_odds

    async def _make_request(
        self,
        method: str,
        url: str,
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling and retries"""
        if not self.http_session:
            raise RuntimeError("HTTP session not initialized")
        
        # Rate limiting check
        if not self._check_rate_limit():
            raise RuntimeError("Rate limit exceeded")
        
        # Apply retry logic
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                async with self.http_session.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=headers,
                    params=params
                ) as response:
                    response_time = time.time() - start_time
                    
                    # Update metrics
                    self.metrics['requests_count'] += 1
                    self.metrics['average_response_time'] = (
                        (self.metrics['average_response_time'] * (self.metrics['requests_count'] - 1) + response_time) 
                        / self.metrics['requests_count']
                    )
                    
                    # Handle response
                    if response.status == 200:
                        self.metrics['successful_requests'] += 1
                        return await response.json()
                    elif response.status in [401, 403]:
                        # Authentication error
                        self.logger.warning(f"Authentication error: {response.status}")
                        await self.reauthenticate()
                        if attempt < self.max_retries:
                            continue
                    elif response.status == 429:
                        # Rate limit error
                        self.logger.warning(f"Rate limit error: {response.status}")
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        # Other errors
                        error_text = await response.text()
                        self.logger.error(f"HTTP error {response.status}: {error_text}")
                        if attempt < self.max_retries:
                            await asyncio.sleep(1)
                            continue
                    
                    self.metrics['failed_requests'] += 1
                    raise aiohttp.ClientError(f"HTTP {response.status}: {error_text}")
                    
            except Exception as e:
                if attempt == self.max_retries:
                    self.metrics['failed_requests'] += 1
                    raise e
                await asyncio.sleep(1)

    def _check_rate_limit(self) -> bool:
        """Check if current request is within rate limits"""
        current_time = time.time()
        
        # Reset hourly counter if needed
        if current_time - self.rate_limiter['last_reset'] > 3600:
            self.rate_limiter['hourly_count'] = 0
            self.rate_limiter['last_reset'] = current_time
        
        # Check limits
        rpm_limit = self.rate_limiter['requests_per_minute']
        rph_limit = self.rate_limiter['requests_per_hour']
        
        # Note: This is a simplified implementation
        # In production, you'd want more sophisticated rate limiting
        return True

    async def reauthenticate(self) -> bool:
        """Re-authenticate with the bookmaker"""
        self.logger.info(f"Re-authenticating with {self.bookmaker_name}")
        return await self.authenticate()

    def on(self, event: str, handler: Callable) -> None:
        """Register an event handler"""
        if event in self.event_handlers:
            self.event_handlers[event].append(handler)

    def off(self, event: str, handler: Callable) -> None:
        """Unregister an event handler"""
        if event in self.event_handlers:
            try:
                self.event_handlers[event].remove(handler)
            except ValueError:
                pass

    async def _emit_event(self, event: str, *args) -> None:
        """Emit an event to registered handlers"""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(*args)
                    else:
                        handler(*args)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event}: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_status = {
            'bookmaker': self.bookmaker_name,
            'status': self.status.value,
            'authenticated': self.session_info.authenticated,
            'last_activity': self.session_info.last_activity,
            'metrics': self.metrics.copy(),
            'timestamp': time.time()
        }
        
        try:
            # Basic connectivity check
            if self.http_session:
                # Test connection
                is_healthy = await self._perform_health_check()
                health_status['healthy'] = is_healthy
            else:
                health_status['healthy'] = False
                
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health_status['healthy'] = False
            health_status['error'] = str(e)
        
        self.metrics['last_health_check'] = time.time()
        return health_status

    async def _perform_health_check(self) -> bool:
        """Perform bookmaker-specific health check"""
        # Default implementation - override in subclasses
        return self.session_info.authenticated

    def get_metrics(self) -> Dict[str, Any]:
        """Get handler metrics"""
        return {
            'bookmaker': self.bookmaker_name,
            'status': self.status.value,
            'session_info': {
                'authenticated': self.session_info.authenticated,
                'last_activity': self.session_info.last_activity,
                'balance': self.session_info.balance,
                'currency': self.session_info.currency
            },
            'performance_metrics': self.metrics.copy(),
            'configuration': {
                'timeout': self.timeout,
                'max_retries': self.max_retries,
                'rate_limits': self.rate_limiter
            }
        }

    async def close(self) -> None:
        """Close the handler and cleanup resources"""
        try:
            self.status = HandlerStatus.DISCONNECTED
            self.logger.info(f"Closing {self.bookmaker_name} handler")
            
            if self.http_session:
                await self.http_session.close()
            
            await self._emit_event('on_disconnect')
            self.logger.info(f"{self.bookmaker_name} handler closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error closing handler: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    # Configuration management
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update handler configuration"""
        self.config.update(new_config)
        self.logger.info(f"Configuration updated for {self.bookmaker_name}")

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()

    def save_config(self, config_path: Union[str, Path]) -> None:
        """Save configuration to file"""
        with open(config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        self.logger.info(f"Configuration saved to {config_path}")

    @classmethod
    def load_config(cls, config_path: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    # Abstract methods for bookmaker-specific functionality
    @abstractmethod
    def get_supported_markets(self) -> List[str]:
        """Get list of supported market types"""
        pass

    @abstractmethod
    async def get_balance(self) -> Optional[float]:
        """Get current account balance"""
        pass

    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get detailed account information"""
        pass

    @abstractmethod
    async def get_bet_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get betting history"""
        pass

    @abstractmethod
    async def update_market_data(self, market_id: str) -> Optional[MarketData]:
        """Update market data for a specific market"""
        pass