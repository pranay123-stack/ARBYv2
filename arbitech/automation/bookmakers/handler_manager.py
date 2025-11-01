"""
Bookmaker Handler Manager

Manages all bookmaker handlers with dynamic loading, health monitoring,
and configuration management.

Features:
- Dynamic handler loading and registration
- Health monitoring and automatic recovery
- Load balancing across handlers
- Configuration management
- Event coordination
- Performance metrics aggregation
- Fallback mechanisms
"""

import asyncio
import json
import logging
import time
import importlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Type, Union
from datetime import datetime, timedelta

from .handler_base import BaseBookmakerHandler, HandlerStatus, BetRequest, BetResponse, MarketData
from .betfair_handler import BetfairHandler
from .pinnacle_handler import PinnacleHandler
from .betdex_handler import BetDexHandler
from .average_handler import AverHandler


@dataclass
class HandlerMetrics:
    """Metrics for a specific handler"""
    bookmaker: str
    status: str
    response_time_avg: float = 0.0
    success_rate: float = 0.0
    request_count: int = 0
    error_count: int = 0
    last_health_check: float = 0.0
    uptime_percentage: float = 0.0
    balance: Optional[float] = None
    currency: Optional[str] = None
    last_error: Optional[str] = None


@dataclass
class ManagerConfig:
    """Configuration for the handler manager"""
    auto_recovery: bool = True
    health_check_interval: int = 30
    max_concurrent_requests: int = 10
    load_balancing_strategy: str = "round_robin"  # round_robin, least_loaded, fastest_response
    fallback_enabled: bool = True
    performance_monitoring: bool = True
    config_file: Optional[str] = None


class BookmakerHandlerManager:
    """
    Manager for all bookmaker handlers.
    
    Provides unified interface to all handlers with:
    - Dynamic handler loading
    - Health monitoring and recovery
    - Load balancing
    - Configuration management
    - Performance metrics
    - Event coordination
    """
    
    def __init__(self, config: Union[Dict[str, Any], ManagerConfig] = None):
        """Initialize the handler manager"""
        if isinstance(config, dict):
            self.config = ManagerConfig(**config)
        else:
            self.config = config or ManagerConfig()
        
        self.logger = self._setup_logging()
        self.handlers: Dict[str, BaseBookmakerHandler] = {}
        self.handler_metrics: Dict[str, HandlerMetrics] = {}
        self.load_balancer = LoadBalancer(self.config.load_balancing_strategy)
        self.health_monitor = HealthMonitor(self)
        
        # Request tracking
        self.active_requests = 0
        self.request_semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)
        
        # Event handling
        self.event_handlers: Dict[str, List[Callable]] = {
            'handler_registered': [],
            'handler_unregistered': [],
            'health_check_failed': [],
            'balance_updated': [],
            'error_occurred': []
        }
        
        # Performance monitoring
        if self.config.performance_monitoring:
            self.executor = ThreadPoolExecutor(max_workers=4)
        else:
            self.executor = None
        
        # Configuration management
        self.config_path = self.config.config_file or '/workspace/arbitech/automation/bookmakers/manager_config.json'
        self._load_configuration()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the manager"""
        return logging.getLogger("arbitech.automation.bookmakers.manager")

    def _load_configuration(self) -> None:
        """Load configuration from file if available"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    saved_config = json.load(f)
                    self.logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            self.logger.warning(f"Could not load configuration: {e}")

    def save_configuration(self) -> None:
        """Save current configuration to file"""
        try:
            config_data = {
                'config': {
                    'auto_recovery': self.config.auto_recovery,
                    'health_check_interval': self.config.health_check_interval,
                    'max_concurrent_requests': self.config.max_concurrent_requests,
                    'load_balancing_strategy': self.config.load_balancing_strategy,
                    'fallback_enabled': self.config.fallback_enabled,
                    'performance_monitoring': self.config.performance_monitoring
                },
                'handlers': {
                    bookmaker: {
                        'status': metrics.status,
                        'balance': metrics.balance,
                        'currency': metrics.currency,
                        'last_health_check': metrics.last_health_check
                    }
                    for bookmaker, metrics in self.handler_metrics.items()
                },
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Could not save configuration: {e}")

    async def register_handler(
        self, 
        bookmaker: str, 
        handler_class: Type[BaseBookmakerHandler], 
        config: Dict[str, Any]
    ) -> bool:
        """Register a new bookmaker handler"""
        try:
            if bookmaker in self.handlers:
                self.logger.warning(f"Handler for {bookmaker} already registered")
                return False
            
            self.logger.info(f"Registering handler for {bookmaker}")
            
            # Initialize handler
            handler = handler_class(config)
            
            # Initialize and authenticate
            if await handler.initialize():
                self.handlers[bookmaker] = handler
                
                # Initialize metrics
                self.handler_metrics[bookmaker] = HandlerMetrics(
                    bookmaker=bookmaker,
                    status=handler.status.value
                )
                
                # Set up event handlers
                handler.on('on_error', self._handle_handler_error)
                handler.on('after_request', self._handle_request_complete)
                
                await self._emit_event('handler_registered', bookmaker)
                
                self.logger.info(f"Successfully registered handler for {bookmaker}")
                return True
            else:
                self.logger.error(f"Failed to initialize handler for {bookmaker}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error registering handler for {bookmaker}: {e}")
            return False

    async def unregister_handler(self, bookmaker: str) -> bool:
        """Unregister a bookmaker handler"""
        try:
            if bookmaker not in self.handlers:
                self.logger.warning(f"Handler for {bookmaker} not found")
                return False
            
            self.logger.info(f"Unregistering handler for {bookmaker}")
            
            # Close handler
            handler = self.handlers[bookmaker]
            await handler.close()
            
            # Remove from collections
            del self.handlers[bookmaker]
            if bookmaker in self.handler_metrics:
                del self.handler_metrics[bookmaker]
            
            await self._emit_event('handler_unregistered', bookmaker)
            
            self.logger.info(f"Successfully unregistered handler for {bookmaker}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unregistering handler for {bookmaker}: {e}")
            return False

    async def register_default_handlers(self, configs: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """Register all default handlers with their configurations"""
        handler_mapping = {
            'betfair': BetfairHandler,
            'pinnacle': PinnacleHandler,
            'betdex': BetDexHandler,
            'aver': AverHandler
        }
        
        results = {}
        for bookmaker, handler_class in handler_mapping.items():
            if bookmaker in configs:
                results[bookmaker] = await self.register_handler(
                    bookmaker, 
                    handler_class, 
                    configs[bookmaker]
                )
            else:
                self.logger.warning(f"No configuration provided for {bookmaker}")
                results[bookmaker] = False
        
        return results

    async def place_bet(self, bet_request: BetRequest, preferred_bookmaker: str = None) -> BetResponse:
        """Place a bet using the best available handler"""
        async with self.request_semaphore:
            try:
                # Select handler
                handler = await self._select_handler(bet_request, preferred_bookmaker)
                if not handler:
                    return BetResponse(
                        success=False,
                        error_message="No available handlers"
                    )
                
                # Place bet
                self.active_requests += 1
                start_time = time.time()
                
                response = await handler.place_bet(bet_request)
                
                # Update metrics
                response_time = time.time() - start_time
                await self._update_handler_metrics(handler.bookmaker_name, response_time, response.success)
                
                return response
                
            except Exception as e:
                self.logger.error(f"Error placing bet: {e}")
                return BetResponse(
                    success=False,
                    error_message=str(e)
                )
            finally:
                self.active_requests = max(0, self.active_requests - 1)

    async def _select_handler(
        self, 
        bet_request: BetRequest, 
        preferred_bookmaker: str = None
    ) -> Optional[BaseBookmakerHandler]:
        """Select the best handler for a bet"""
        # Check preferred handler first
        if preferred_bookmaker and preferred_bookmaker in self.handlers:
            preferred_handler = self.handlers[preferred_bookmaker]
            if preferred_handler.status == HandlerStatus.READY:
                return preferred_handler
        
        # Get available handlers
        available_handlers = [
            handler for handler in self.handlers.values()
            if handler.status == HandlerStatus.READY
        ]
        
        if not available_handlers:
            return None
        
        # Apply load balancing
        selected_handler = await self.load_balancer.select_handler(
            available_handlers, 
            bet_request
        )
        
        return selected_handler

    async def get_markets(
        self, 
        filters: Dict[str, Any] = None,
        bookmaker: str = None
    ) -> Dict[str, List[MarketData]]:
        """Get markets from all or specified bookmakers"""
        if not filters:
            filters = {}
        
        markets = {}
        
        if bookmaker:
            # Get markets from specific bookmaker
            if bookmaker in self.handlers:
                handler = self.handlers[bookmaker]
                if handler.status == HandlerStatus.READY:
                    markets[bookmaker] = await handler.get_markets(filters)
        else:
            # Get markets from all handlers
            tasks = []
            for name, handler in self.handlers.items():
                if handler.status == HandlerStatus.READY:
                    tasks.append((name, handler.get_markets(filters)))
            
            # Execute all tasks concurrently
            for name, task in tasks:
                try:
                    markets[name] = await task
                except Exception as e:
                    self.logger.error(f"Error getting markets from {name}: {e}")
                    markets[name] = []
        
        return markets

    async def get_balances(self) -> Dict[str, Dict[str, Any]]:
        """Get balances from all handlers"""
        balances = {}
        
        tasks = []
        for name, handler in self.handlers.items():
            if handler.status == HandlerStatus.READY:
                tasks.append((name, handler.get_balance()))
        
        # Execute all tasks concurrently
        for name, task in tasks:
            try:
                balance = await task
                if balance is not None:
                    balances[name] = {
                        'balance': balance,
                        'currency': self.handler_metrics[name].currency,
                        'status': 'available'
                    }
                else:
                    balances[name] = {'status': 'unavailable'}
            except Exception as e:
                self.logger.error(f"Error getting balance from {name}: {e}")
                balances[name] = {'status': 'error', 'error': str(e)}
        
        return balances

    async def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics for all handlers"""
        metrics = {
            'manager': {
                'total_handlers': len(self.handlers),
                'active_handlers': sum(1 for h in self.handlers.values() if h.status == HandlerStatus.READY),
                'active_requests': self.active_requests,
                'configuration': {
                    'auto_recovery': self.config.auto_recovery,
                    'health_check_interval': self.config.health_check_interval,
                    'load_balancing_strategy': self.config.load_balancing_strategy
                }
            },
            'handlers': {}
        }
        
        for bookmaker, handler_metrics in self.handler_metrics.items():
            # Get handler-specific metrics
            handler = self.handlers[bookmaker]
            handler_detailed_metrics = handler.get_metrics()
            
            metrics['handlers'][bookmaker] = {
                'status': handler_metrics.status,
                'response_time_avg': handler_metrics.response_time_avg,
                'success_rate': handler_metrics.success_rate,
                'request_count': handler_metrics.request_count,
                'error_count': handler_metrics.error_count,
                'uptime_percentage': handler_metrics.uptime_percentage,
                'balance': handler_metrics.balance,
                'currency': handler_metrics.currency,
                'last_error': handler_metrics.last_error,
                'detailed_metrics': handler_detailed_metrics
            }
        
        return metrics

    async def health_check_all_handlers(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all handlers"""
        health_reports = {}
        
        tasks = []
        for name, handler in self.handlers.items():
            tasks.append((name, handler.health_check()))
        
        # Execute all health checks concurrently
        for name, task in tasks:
            try:
                health_report = await task
                health_reports[name] = health_report
                
                # Update metrics
                metrics = self.handler_metrics[name]
                metrics.last_health_check = time.time()
                metrics.status = health_report.get('status', 'unknown')
                metrics.balance = health_report.get('session_info', {}).get('balance')
                metrics.currency = health_report.get('session_info', {}).get('currency')
                
                # Handle unhealthy handlers
                if not health_report.get('healthy', False):
                    await self._handle_unhealthy_handler(name, health_report)
                
            except Exception as e:
                self.logger.error(f"Health check failed for {name}: {e}")
                health_reports[name] = {
                    'bookmaker': name,
                    'healthy': False,
                    'error': str(e),
                    'timestamp': time.time()
                }
        
        return health_reports

    async def _handle_unhealthy_handler(self, bookmaker: str, health_report: Dict[str, Any]) -> None:
        """Handle unhealthy handler"""
        self.logger.warning(f"Handler {bookmaker} is unhealthy: {health_report}")
        
        # Emit event
        await self._emit_event('health_check_failed', bookmaker, health_report)
        
        # Auto-recovery if enabled
        if self.config.auto_recovery:
            self.logger.info(f"Attempting auto-recovery for {bookmaker}")
            await self._attempt_recovery(bookmaker)

    async def _attempt_recovery(self, bookmaker: str) -> bool:
        """Attempt to recover an unhealthy handler"""
        try:
            if bookmaker not in self.handlers:
                return False
            
            handler = self.handlers[bookmaker]
            
            # Re-authenticate
            if await handler.authenticate():
                self.logger.info(f"Successfully recovered handler {bookmaker}")
                return True
            else:
                self.logger.error(f"Failed to recover handler {bookmaker}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error attempting recovery for {bookmaker}: {e}")
            return False

    async def start_health_monitoring(self) -> None:
        """Start automatic health monitoring"""
        self.logger.info("Starting health monitoring")
        
        while True:
            try:
                await self.health_check_all_handlers()
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
                await asyncio.sleep(self.config.health_check_interval)

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

    async def _handle_handler_error(self, error: Exception) -> None:
        """Handle errors from handlers"""
        await self._emit_event('error_occurred', error)

    async def _handle_request_complete(self, response: BetResponse) -> None:
        """Handle completed requests"""
        if response.success and response.bet_id:
            await self._emit_event('balance_updated', response.bet_id)

    async def _update_handler_metrics(
        self, 
        bookmaker: str, 
        response_time: float, 
        success: bool
    ) -> None:
        """Update handler metrics"""
        if bookmaker not in self.handler_metrics:
            return
        
        metrics = self.handler_metrics[bookmaker]
        metrics.request_count += 1
        
        if success:
            # Update response time average
            metrics.response_time_avg = (
                (metrics.response_time_avg * (metrics.request_count - 1) + response_time) 
                / metrics.request_count
            )
        else:
            metrics.error_count += 1
        
        # Calculate success rate
        metrics.success_rate = (metrics.request_count - metrics.error_count) / metrics.request_count

    async def close(self) -> None:
        """Close all handlers and cleanup"""
        self.logger.info("Closing handler manager")
        
        # Stop health monitoring
        if hasattr(self, '_health_monitor_running'):
            self._health_monitor_running = False
        
        # Close all handlers
        close_tasks = []
        for bookmaker, handler in self.handlers.items():
            close_tasks.append(handler.close())
        
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
        
        # Save configuration
        self.save_configuration()
        
        # Cleanup resources
        if self.executor:
            self.executor.shutdown(wait=True)
        
        self.logger.info("Handler manager closed")

    # Configuration management methods
    def update_config(self, new_config: Union[Dict[str, Any], ManagerConfig]) -> None:
        """Update manager configuration"""
        if isinstance(new_config, dict):
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
        else:
            self.config = new_config
        
        self.logger.info("Manager configuration updated")
        self.save_configuration()

    def get_config(self) -> ManagerConfig:
        """Get current configuration"""
        return self.config

    # Utility methods
    def get_registered_bookmakers(self) -> List[str]:
        """Get list of registered bookmakers"""
        return list(self.handlers.keys())

    def get_handler(self, bookmaker: str) -> Optional[BaseBookmakerHandler]:
        """Get a specific handler"""
        return self.handlers.get(bookmaker)

    def is_handler_healthy(self, bookmaker: str) -> bool:
        """Check if a specific handler is healthy"""
        if bookmaker not in self.handler_metrics:
            return False
        
        metrics = self.handler_metrics[bookmaker]
        return (
            metrics.status in ['ready', 'authenticated'] and
            metrics.success_rate > 0.8 and
            time.time() - metrics.last_health_check < 300  # 5 minutes
        )


class LoadBalancer:
    """Load balancer for handler selection"""
    
    def __init__(self, strategy: str):
        self.strategy = strategy
        self.round_robin_counter = 0
    
    async def select_handler(
        self, 
        handlers: List[BaseBookmakerHandler], 
        bet_request: BetRequest
    ) -> BaseBookmakerHandler:
        """Select handler based on strategy"""
        if self.strategy == "round_robin":
            return self._round_robin_select(handlers)
        elif self.strategy == "least_loaded":
            return self._least_loaded_select(handlers)
        elif self.strategy == "fastest_response":
            return self._fastest_response_select(handlers)
        else:
            return handlers[0]  # Default to first handler

    def _round_robin_select(self, handlers: List[BaseBookmakerHandler]) -> BaseBookmakerHandler:
        """Round-robin selection"""
        handler = handlers[self.round_robin_counter % len(handlers)]
        self.round_robin_counter += 1
        return handler

    def _least_loaded_select(self, handlers: List[BaseBookmakerHandler]) -> BaseBookmakerHandler:
        """Select handler with least load"""
        # Placeholder implementation - would track request load
        return handlers[0]

    def _fastest_response_select(self, handlers: List[BaseBookmakerHandler]) -> BaseBookmakerHandler:
        """Select handler with fastest response time"""
        # Placeholder implementation - would track response times
        return handlers[0]


class HealthMonitor:
    """Health monitoring for handlers"""
    
    def __init__(self, manager: BookmakerHandlerManager):
        self.manager = manager
        self.logger = logging.getLogger("arbitech.automation.bookmakers.health_monitor")
