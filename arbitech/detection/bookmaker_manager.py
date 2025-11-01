"""
Bookmaker Manager - Central management system for multiple bookmaker APIs and data sources.

This module provides a comprehensive system for managing different bookmaker integrations,
including health monitoring, failover capabilities, and data collection orchestration.
"""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Callable, Tuple
from dataclasses import dataclass, field
from uuid import uuid4
import logging
import traceback
from abc import ABC, abstractmethod

try:
    # Try relative imports first (when used as part of arbitech package)
    from ..core.config_manager import ConfigManager
    from ..utils.logger import get_logger
except ImportError:
    # Fall back to absolute imports (when used standalone)
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir.parent.parent))  # Add workspace root
    
    try:
        from core.config_manager import ConfigManager
    except ImportError:
        class ConfigManager:
            def get(self, key, default=None):
                return default
    
    try:
        from utils.logger import get_logger
    except ImportError:
        import logging
        def get_logger(name):
            return logging.getLogger(name)


logger = get_logger(__name__)


class BookmakerStatus(str, Enum):
    """Bookmaker connectivity and health status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    SUSPENDED = "suspended"
    UNKNOWN = "unknown"


class DataSourceType(str, Enum):
    """Types of data sources supported."""
    API_REST = "api_rest"
    API_GRAPHQL = "api_graphql"
    WEBSOCKET = "websocket"
    SCREEN_SCRAPING = "screen_scraping"
    VLM_EXTRACTION = "vlm_extraction"
    FILE_FEED = "file_feed"


class PriorityLevel(str, Enum):
    """Priority levels for data collection."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class HealthMetrics:
    """Health monitoring metrics for bookmaker connections."""
    bookmaker_name: str
    status: BookmakerStatus
    last_successful_call: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    avg_response_time_ms: float = 0.0
    last_response_time_ms: float = 0.0
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[datetime] = None
    uptime_percentage: float = 100.0
    reliability_score: float = 100.0
    data_freshness_score: float = 100.0


@dataclass
class DataSource:
    """Configuration for a specific data source."""
    name: str
    bookmaker_name: str
    source_type: DataSourceType
    priority: PriorityLevel
    endpoint_url: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None
    rate_limit_per_minute: int = 60
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    health_check_interval_seconds: int = 300
    enabled: bool = True
    weight: float = 1.0
    custom_headers: Optional[Dict[str, str]] = None
    custom_parameters: Optional[Dict[str, Any]] = None
    
    # Health monitoring
    health_metrics: Optional[HealthMetrics] = None
    last_health_check: Optional[datetime] = None
    
    # Data collection
    last_data_collection: Optional[datetime] = None
    data_quality_score: float = 100.0
    
    def __post_init__(self):
        if not self.health_metrics:
            self.health_metrics = HealthMetrics(
                bookmaker_name=self.bookmaker_name,
                status=BookmakerStatus.UNKNOWN
            )


@dataclass
class BookmakerIntegration:
    """Complete bookmaker integration configuration."""
    bookmaker_name: str
    display_name: str
    base_url: str
    region: str
    currency: str
    supported_sports: List[str]
    data_sources: List[DataSource] = field(default_factory=list)
    failover_sources: List[str] = field(default_factory=list)
    
    # Health and performance
    overall_health: BookmakerStatus = BookmakerStatus.UNKNOWN
    data_collection_active: bool = False
    last_sync_time: Optional[datetime] = None
    
    # Configuration
    max_concurrent_requests: int = 5
    connection_pool_size: int = 10
    connection_timeout: int = 30
    read_timeout: int = 60
    
    # VLM integration
    vlm_enabled: bool = False
    vlm_screenshots_enabled: bool = False
    vlm_extraction_template: Optional[str] = None
    vlm_quality_threshold: float = 0.8


class BookmakerAPIInterface(ABC):
    """Abstract interface for bookmaker API integrations."""
    
    def __init__(self, config: DataSource, bookmaker_config: BookmakerIntegration):
        self.config = config
        self.bookmaker_config = bookmaker_config
        self.logger = get_logger(f"{__name__}.{config.name}")
    
    @abstractmethod
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test connection to the data source. Returns (success, error_message)."""
        pass
    
    @abstractmethod
    async def collect_odds_data(self, 
                               sports: List[str], 
                               markets: Optional[List[str]] = None,
                               event_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Collect odds data from the source."""
        pass
    
    @abstractmethod
    async def collect_live_data(self, 
                               event_ids: List[str]) -> Dict[str, Any]:
        """Collect live odds data for active events."""
        pass
    
    @abstractmethod
    async def health_check(self) -> HealthMetrics:
        """Perform health check and return metrics."""
        pass


class RESTAPIClient(BookmakerAPIInterface):
    """REST API client implementation."""
    
    def __init__(self, config: DataSource, bookmaker_config: BookmakerIntegration):
        super().__init__(config, bookmaker_config)
        self.session = None
    
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test REST API connection."""
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Test basic endpoint connectivity
                test_url = f"{self.bookmaker_config.base_url}/health" if self.config.endpoint_url is None else self.config.endpoint_url
                
                async with session.get(test_url) as response:
                    if response.status == 200:
                        self.config.health_metrics.status = BookmakerStatus.ACTIVE
                        self.config.health_metrics.last_successful_call = datetime.utcnow()
                        return True, None
                    else:
                        error_msg = f"HTTP {response.status}"
                        self.config.health_metrics.status = BookmakerStatus.ERROR
                        self.config.health_metrics.last_error = error_msg
                        return False, error_msg
        
        except Exception as e:
            error_msg = str(e)
            self.config.health_metrics.status = BookmakerStatus.ERROR
            self.config.health_metrics.last_error = error_msg
            self.logger.error(f"Connection test failed: {error_msg}")
            return False, error_msg
    
    async def collect_odds_data(self, 
                               sports: List[str], 
                               markets: Optional[List[str]] = None,
                               event_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Collect odds data via REST API."""
        start_time = time.time()
        
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {
                    'Accept': 'application/json',
                    'User-Agent': 'Arbitech/1.0'
                }
                
                # Add custom headers
                if self.config.custom_headers:
                    headers.update(self.config.custom_headers)
                
                # Build request URL
                url = self.config.endpoint_url or f"{self.bookmaker_config.base_url}/odds"
                params = {'sports': ','.join(sports)}
                
                if markets:
                    params['markets'] = ','.join(markets)
                if event_ids:
                    params['event_ids'] = ','.join(event_ids)
                
                # Add custom parameters
                if self.config.custom_parameters:
                    params.update(self.config.custom_parameters)
                
                async with session.get(url, headers=headers, params=params) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    self.config.health_metrics.total_requests += 1
                    self.config.health_metrics.last_response_time_ms = response_time
                    
                    if response.status == 200:
                        data = await response.json()
                        self.config.health_metrics.successful_requests += 1
                        self.config.health_metrics.last_successful_call = datetime.utcnow()
                        self.config.health_metrics.status = BookmakerStatus.ACTIVE
                        
                        # Calculate rolling average response time
                        if self.config.health_metrics.avg_response_time_ms == 0:
                            self.config.health_metrics.avg_response_time_ms = response_time
                        else:
                            self.config.health_metrics.avg_response_time_ms = (
                                self.config.health_metrics.avg_response_time_ms * 0.8 + response_time * 0.2
                            )
                        
                        return {
                            'bookmaker': self.bookmaker_config.bookmaker_name,
                            'source': self.config.name,
                            'timestamp': datetime.utcnow().isoformat(),
                            'response_time_ms': response_time,
                            'data': data,
                            'status': 'success'
                        }
                    elif response.status == 429:
                        self.config.health_metrics.status = BookmakerStatus.RATE_LIMITED
                        self.config.health_metrics.last_error = f"Rate limited: {response.headers.get('X-RateLimit-Remaining', 'unknown')}"
                        return self._create_error_response("Rate limited", response_time)
                    else:
                        error_msg = f"HTTP {response.status}: {await response.text()}"
                        self.config.health_metrics.status = BookmakerStatus.ERROR
                        self.config.health_metrics.last_error = error_msg
                        return self._create_error_response(error_msg, response_time)
        
        except asyncio.TimeoutError:
            self.config.health_metrics.status = BookmakerStatus.ERROR
            self.config.health_metrics.last_error = "Request timeout"
            return self._create_error_response("Request timeout", (time.time() - start_time) * 1000)
        
        except Exception as e:
            error_msg = str(e)
            self.config.health_metrics.status = BookmakerStatus.ERROR
            self.config.health_metrics.last_error = error_msg
            self.logger.error(f"Data collection failed: {error_msg}")
            return self._create_error_response(error_msg, (time.time() - start_time) * 1000)
    
    async def collect_live_data(self, event_ids: List[str]) -> Dict[str, Any]:
        """Collect live odds data via REST API."""
        # Implementation similar to collect_odds_data but for live events
        return await self.collect_odds_data([], event_ids=event_ids)
    
    async def health_check(self) -> HealthMetrics:
        """Perform REST API health check."""
        success, error = await self.test_connection()
        
        # Update reliability score
        if self.config.health_metrics.total_requests > 0:
            success_rate = (self.config.health_metrics.successful_requests / 
                          self.config.health_metrics.total_requests)
            self.config.health_metrics.reliability_score = success_rate * 100
        
        # Calculate uptime percentage
        if self.config.health_metrics.last_successful_call:
            time_since_last_success = datetime.utcnow() - self.config.health_metrics.last_successful_call
            if time_since_last_success > timedelta(minutes=5):
                self.config.health_metrics.status = BookmakerStatus.INACTIVE
        
        self.config.health_metrics.last_health_check = datetime.utcnow()
        return self.config.health_metrics
    
    def _create_error_response(self, error_msg: str, response_time_ms: float) -> Dict[str, Any]:
        """Create standardized error response."""
        self.config.health_metrics.consecutive_failures += 1
        
        return {
            'bookmaker': self.bookmaker_config.bookmaker_name,
            'source': self.config.name,
            'timestamp': datetime.utcnow().isoformat(),
            'response_time_ms': response_time_ms,
            'status': 'error',
            'error': error_msg,
            'data': None
        }


class VLMExtractionClient(BookmakerAPIInterface):
    """VLM (Vision Language Model) extraction client."""
    
    def __init__(self, config: DataSource, bookmaker_config: BookmakerIntegration):
        super().__init__(config, bookmaker_config)
        self.vlm_client = None  # Will be initialized with VLM client
    
    async def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Test VLM extraction capability."""
        try:
            # Test VLM service availability
            # This would integrate with the VLM extraction system
            success = True
            error_msg = None if success else "VLM service unavailable"
            
            self.config.health_metrics.status = BookmakerStatus.ACTIVE if success else BookmakerStatus.ERROR
            self.config.health_metrics.last_successful_call = datetime.utcnow() if success else None
            
            return success, error_msg
        
        except Exception as e:
            error_msg = str(e)
            self.config.health_metrics.status = BookmakerStatus.ERROR
            self.config.health_metrics.last_error = error_msg
            return False, error_msg
    
    async def collect_odds_data(self, 
                               sports: List[str], 
                               markets: Optional[List[str]] = None,
                               event_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Collect odds data via VLM extraction from screenshots/images."""
        start_time = time.time()
        
        try:
            # This would integrate with the VLM extraction system
            # to analyze screenshots and extract odds data
            
            # Mock implementation for now
            await asyncio.sleep(1)  # Simulate VLM processing
            
            response_time = (time.time() - start_time) * 1000
            
            self.config.health_metrics.total_requests += 1
            self.config.health_metrics.last_response_time_ms = response_time
            self.config.health_metrics.successful_requests += 1
            self.config.health_metrics.last_successful_call = datetime.utcnow()
            self.config.health_metrics.status = BookmakerStatus.ACTIVE
            
            return {
                'bookmaker': self.bookmaker_config.bookmaker_name,
                'source': self.config.name,
                'timestamp': datetime.utcnow().isoformat(),
                'response_time_ms': response_time,
                'extraction_method': 'vlm',
                'data': {
                    'sports': sports,
                    'markets': markets or [],
                    'extracted_odds': []  # Would contain VLM extracted data
                },
                'status': 'success'
            }
        
        except Exception as e:
            error_msg = str(e)
            self.config.health_metrics.status = BookmakerStatus.ERROR
            self.config.health_metrics.last_error = error_msg
            return self._create_error_response(error_msg, (time.time() - start_time) * 1000)
    
    async def collect_live_data(self, event_ids: List[str]) -> Dict[str, Any]:
        """Collect live data via VLM extraction."""
        return await self.collect_odds_data([], event_ids=event_ids)
    
    async def health_check(self) -> HealthMetrics:
        """Perform VLM service health check."""
        success, error = await self.test_connection()
        
        if self.config.health_metrics.total_requests > 0:
            success_rate = (self.config.health_metrics.successful_requests / 
                          self.config.health_metrics.total_requests)
            self.config.health_metrics.reliability_score = success_rate * 100
        
        self.config.health_metrics.last_health_check = datetime.utcnow()
        return self.config.health_metrics
    
    def _create_error_response(self, error_msg: str, response_time_ms: float) -> Dict[str, Any]:
        """Create standardized error response."""
        self.config.health_metrics.consecutive_failures += 1
        
        return {
            'bookmaker': self.bookmaker_config.bookmaker_name,
            'source': self.config.name,
            'timestamp': datetime.utcnow().isoformat(),
            'response_time_ms': response_time_ms,
            'status': 'error',
            'error': error_msg,
            'data': None
        }


class BookmakerManager:
    """Central manager for all bookmaker integrations and data sources."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.logger = get_logger(__name__)
        
        # Bookmaker configurations
        self.bookmakers: Dict[str, BookmakerIntegration] = {}
        self.active_data_sources: Dict[str, DataSource] = {}
        self.source_clients: Dict[str, BookmakerAPIInterface] = {}
        
        # Health monitoring
        self.health_check_interval = 300  # 5 minutes
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.monitoring_enabled = True
        
        # Performance tracking
        self.collection_stats: Dict[str, Dict[str, Any]] = {}
        self.last_collection_times: Dict[str, datetime] = {}
        
        # Event callbacks
        self.health_change_callbacks: List[Callable[[str, BookmakerStatus], None]] = []
        self.data_quality_callbacks: List[Callable[[str, float], None]] = []
        
        # Concurrency control
        self.max_concurrent_collections = 10
        self.collection_semaphore = asyncio.Semaphore(self.max_concurrent_collections)
        
        # Failover management
        self.failover_enabled = True
        self.failover_threshold = 3  # consecutive failures before failover
    
    async def initialize(self):
        """Initialize the bookmaker manager with configurations."""
        try:
            await self._load_bookmaker_configurations()
            await self._initialize_data_sources()
            await self._setup_health_monitoring()
            
            self.logger.info(f"Bookmaker manager initialized with {len(self.bookmakers)} bookmakers")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bookmaker manager: {e}")
            raise
    
    async def _load_bookmaker_configurations(self):
        """Load bookmaker configurations from config manager."""
        try:
            # Load bookmaker configurations from config file
            bookmaker_configs = self.config_manager.get('bookmakers', {})
            
            for bookmaker_name, config in bookmaker_configs.items():
                if not config.get('enabled', False):
                    continue
                
                bookmaker = BookmakerIntegration(
                    bookmaker_name=bookmaker_name,
                    display_name=config.get('display_name', bookmaker_name),
                    base_url=config['base_url'],
                    region=','.join(config.get('regions', ['GLOBAL'])),
                    currency=config.get('currency', 'USD'),
                    supported_sports=config.get('sports', []),
                    max_concurrent_requests=config.get('max_concurrent_requests', 5),
                    connection_pool_size=config.get('connection_pool_size', 10),
                    vlm_enabled=config.get('vlm_enabled', False),
                    vlm_screenshots_enabled=config.get('vlm_screenshots_enabled', False),
                    vlm_extraction_template=config.get('vlm_extraction_template'),
                )
                
                self.bookmakers[bookmaker_name] = bookmaker
                
                # Create data sources based on bookmaker type
                if config.get('type') == 'api':
                    # REST API data source
                    api_source = DataSource(
                        name=f"{bookmaker_name}_api",
                        bookmaker_name=bookmaker_name,
                        source_type=DataSourceType.API_REST,
                        priority=PriorityLevel.HIGH,
                        endpoint_url=config.get('api_endpoint'),
                        rate_limit_per_minute=config.get('rate_limit_per_minute', 60),
                        timeout_seconds=config.get('timeout', 30),
                        retry_attempts=config.get('retry_attempts', 3),
                        custom_headers=config.get('headers', {}),
                        custom_parameters=config.get('parameters', {})
                    )
                    bookmaker.data_sources.append(api_source)
                    self.active_data_sources[api_source.name] = api_source
                
                elif config.get('type') == 'exchange':
                    # Betfair-style exchange API
                    exchange_source = DataSource(
                        name=f"{bookmaker_name}_exchange",
                        bookmaker_name=bookmaker_name,
                        source_type=DataSourceType.API_REST,
                        priority=PriorityLevel.HIGH,
                        endpoint_url=config.get('api_endpoint'),
                        rate_limit_per_minute=config.get('rate_limit_per_minute', 10),
                        timeout_seconds=config.get('timeout', 10),
                        retry_attempts=config.get('retry_attempts', 3)
                    )
                    bookmaker.data_sources.append(exchange_source)
                    self.active_data_sources[exchange_source.name] = exchange_source
                
                # Add VLM extraction source if enabled
                if bookmaker.vlm_enabled:
                    vlm_source = DataSource(
                        name=f"{bookmaker_name}_vlm",
                        bookmaker_name=bookmaker_name,
                        source_type=DataSourceType.VLM_EXTRACTION,
                        priority=PriorityLevel.MEDIUM,
                        rate_limit_per_minute=10,  # VLM processing is slower
                        timeout_seconds=120,  # Longer timeout for VLM processing
                        retry_attempts=2
                    )
                    bookmaker.data_sources.append(vlm_source)
                    self.active_data_sources[vlm_source.name] = vlm_source
            
            self.logger.info(f"Loaded {len(self.bookmakers)} bookmaker configurations")
            
        except Exception as e:
            self.logger.error(f"Failed to load bookmaker configurations: {e}")
            raise
    
    async def _initialize_data_sources(self):
        """Initialize API clients for each data source."""
        for bookmaker in self.bookmakers.values():
            for source in bookmaker.data_sources:
                try:
                    if source.source_type == DataSourceType.API_REST:
                        client = RESTAPIClient(source, bookmaker)
                    elif source.source_type == DataSourceType.VLM_EXTRACTION:
                        client = VLMExtractionClient(source, bookmaker)
                    else:
                        self.logger.warning(f"Unsupported data source type: {source.source_type}")
                        continue
                    
                    self.source_clients[source.name] = client
                    
                    # Test connection
                    success, error = await client.test_connection()
                    if success:
                        self.logger.info(f"Data source {source.name} initialized successfully")
                    else:
                        self.logger.warning(f"Data source {source.name} connection test failed: {error}")
                
                except Exception as e:
                    self.logger.error(f"Failed to initialize data source {source.name}: {e}")
    
    async def _setup_health_monitoring(self):
        """Setup continuous health monitoring."""
        if not self.monitoring_enabled:
            return
        
        self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
        self.logger.info("Health monitoring started")
    
    async def _health_monitor_loop(self):
        """Continuous health monitoring loop."""
        while self.monitoring_enabled:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _perform_health_checks(self):
        """Perform health checks on all active data sources."""
        for source_name, client in self.source_clients.items():
            try:
                metrics = await client.health_check()
                
                # Check for status changes
                if (source_name not in self.collection_stats or 
                    self.collection_stats[source_name].get('status') != metrics.status):
                    
                    self.collection_stats[source_name] = {
                        'status': metrics.status,
                        'last_check': datetime.utcnow().isoformat(),
                        'reliability_score': metrics.reliability_score,
                        'data_freshness_score': metrics.data_freshness_score
                    }
                    
                    # Notify callbacks
                    await self._notify_health_change(source_name, metrics.status)
                
                # Update failover if needed
                if metrics.consecutive_failures >= self.failover_threshold:
                    await self._handle_failover(source_name)
                
            except Exception as e:
                self.logger.error(f"Health check failed for {source_name}: {e}")
    
    async def _notify_health_change(self, source_name: str, status: BookmakerStatus):
        """Notify callbacks of health status changes."""
        for callback in self.health_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(source_name, status)
                else:
                    callback(source_name, status)
            except Exception as e:
                self.logger.error(f"Health change callback failed: {e}")
    
    async def _handle_failover(self, failed_source_name: str):
        """Handle failover to backup data sources."""
        if not self.failover_enabled:
            return
        
        failed_source = self.active_data_sources.get(failed_source_name)
        if not failed_source:
            return
        
        bookmaker = next((b for b in self.bookmakers.values() 
                         if failed_source_name in [s.name for s in b.data_sources]), None)
        
        if not bookmaker:
            return
        
        # Find available failover sources
        for failover_source_name in bookmaker.failover_sources:
            failover_source = self.active_data_sources.get(failover_source_name)
            failover_client = self.source_clients.get(failover_source_name)
            
            if failover_source and failover_client:
                # Test failover source
                success, error = await failover_client.test_connection()
                if success:
                    self.logger.warning(f"Failover activated: {failed_source_name} -> {failover_source_name}")
                    return
        
        self.logger.error(f"No failover available for {failed_source_name}")
    
    async def collect_data_from_bookmaker(self, 
                                         bookmaker_name: str,
                                         sports: List[str],
                                         markets: Optional[List[str]] = None,
                                         use_failover: bool = True) -> Dict[str, Any]:
        """Collect data from a specific bookmaker using available sources."""
        bookmaker = self.bookmakers.get(bookmaker_name)
        if not bookmaker:
            return {
                'bookmaker': bookmaker_name,
                'status': 'error',
                'error': 'Bookmaker not configured'
            }
        
        # Sort sources by priority and reliability
        sources = sorted(bookmaker.data_sources, 
                        key=lambda s: (s.priority.value, -s.health_metrics.reliability_score),
                        reverse=True)
        
        for source in sources:
            if not source.enabled:
                continue
            
            client = self.source_clients.get(source.name)
            if not client:
                continue
            
            try:
                async with self.collection_semaphore:
                    result = await client.collect_odds_data(sports, markets)
                    
                if result['status'] == 'success':
                    # Update collection stats
                    self.last_collection_times[bookmaker_name] = datetime.utcnow()
                    return result
                else:
                    self.logger.warning(f"Data collection failed from {source.name}: {result.get('error')}")
                    if not use_failover:
                        break
            
            except Exception as e:
                self.logger.error(f"Data collection error from {source.name}: {e}")
                continue
        
        return {
            'bookmaker': bookmaker_name,
            'status': 'error',
            'error': 'All data sources failed'
        }
    
    async def collect_data_concurrent(self, 
                                     bookmaker_names: Optional[List[str]] = None,
                                     sports: List[str] = [],
                                     markets: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """Collect data from multiple bookmakers concurrently."""
        if bookmaker_names is None:
            bookmaker_names = list(self.bookmakers.keys())
        
        tasks = []
        for bookmaker_name in bookmaker_names:
            task = asyncio.create_task(
                self.collect_data_from_bookmaker(bookmaker_name, sports, markets)
            )
            tasks.append((bookmaker_name, task))
        
        results = {}
        for bookmaker_name, task in tasks:
            try:
                result = await task
                results[bookmaker_name] = result
            except Exception as e:
                self.logger.error(f"Concurrent collection failed for {bookmaker_name}: {e}")
                results[bookmaker_name] = {
                    'bookmaker': bookmaker_name,
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    def get_bookmaker_health(self, bookmaker_name: str) -> Optional[Dict[str, Any]]:
        """Get health status for a specific bookmaker."""
        bookmaker = self.bookmakers.get(bookmaker_name)
        if not bookmaker:
            return None
        
        health_data = {
            'bookmaker': bookmaker_name,
            'status': bookmaker.overall_health,
            'data_sources': [],
            'last_sync': bookmaker.last_sync_time.isoformat() if bookmaker.last_sync_time else None,
            'data_collection_active': bookmaker.data_collection_active
        }
        
        for source in bookmaker.data_sources:
            metrics = source.health_metrics
            health_data['data_sources'].append({
                'name': source.name,
                'status': metrics.status,
                'reliability_score': metrics.reliability_score,
                'last_successful_call': metrics.last_successful_call.isoformat() if metrics.last_successful_call else None,
                'consecutive_failures': metrics.consecutive_failures,
                'avg_response_time_ms': metrics.avg_response_time_ms
            })
        
        return health_data
    
    def get_all_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all bookmakers."""
        return {name: self.get_bookmaker_health(name) 
                for name in self.bookmakers.keys()}
    
    def add_health_change_callback(self, callback: Callable[[str, BookmakerStatus], None]):
        """Add callback for health status changes."""
        self.health_change_callbacks.append(callback)
    
    def add_data_quality_callback(self, callback: Callable[[str, float], None]):
        """Add callback for data quality changes."""
        self.data_quality_callbacks.append(callback)
    
    async def shutdown(self):
        """Shutdown the bookmaker manager."""
        self.monitoring_enabled = False
        
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Bookmaker manager shutdown complete")


# Factory function to create appropriate API client
def create_api_client(config: DataSource, 
                     bookmaker_config: BookmakerIntegration) -> Optional[BookmakerAPIInterface]:
    """Factory function to create appropriate API client."""
    if config.source_type == DataSourceType.API_REST:
        return RESTAPIClient(config, bookmaker_config)
    elif config.source_type == DataSourceType.VLM_EXTRACTION:
        return VLMExtractionClient(config, bookmaker_config)
    else:
        logger.warning(f"Unsupported data source type: {config.source_type}")
        return None


# Global instance for easy access
_bookmaker_manager: Optional[BookmakerManager] = None


async def get_bookmaker_manager() -> BookmakerManager:
    """Get global bookmaker manager instance."""
    global _bookmaker_manager
    
    if _bookmaker_manager is None:
        _bookmaker_manager = BookmakerManager()
        await _bookmaker_manager.initialize()
    
    return _bookmaker_manager


async def shutdown_bookmaker_manager():
    """Shutdown global bookmaker manager."""
    global _bookmaker_manager
    
    if _bookmaker_manager:
        await _bookmaker_manager.shutdown()
        _bookmaker_manager = None