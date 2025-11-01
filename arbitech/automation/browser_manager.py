"""
Browser Manager - Advanced Browser Session Management

This module provides advanced browser session management with pool management,
health monitoring, and automatic recovery for arbitrage trading workflows.

Features:
- Browser pool management with load balancing
- Session health monitoring and metrics
- Automatic recovery and failover
- Resource optimization and cleanup
- Performance tracking and analytics
- Concurrent session management
- Load balancing and distribution
"""

import asyncio
import json
import time
import logging
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from uuid import uuid4
import random
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref

from playwright.async_api import Page, Browser, BrowserContext, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Import existing modules
try:
    from ..core.config_manager import ConfigManager
    from ..utils.logger import get_logger
    from .enhanced_browser import EnhancedBrowser, BrowserConfig, BrowserSession
except ImportError:
    # Fallback for standalone usage
    import sys
    sys.path.append('/workspace')
    try:
        from arbitech.core.config_manager import ConfigManager
        from arbitech.utils.logger import get_logger
        from arbitech.automation.enhanced_browser import EnhancedBrowser, BrowserConfig, BrowserSession
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
        
        class BrowserConfig:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        class BrowserSession:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

logger = get_logger(__name__)


class SessionStatus(str, Enum):
    """Status of browser sessions."""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    RECOVERING = "recovering"
    CLOSED = "closed"
    SUSPENDED = "suspended"


class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies for browser sessions."""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    PERFORMANCE_BASED = "performance_based"


class HealthStatus(str, Enum):
    """Health status of browser sessions."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class SessionMetrics:
    """Metrics for browser sessions."""
    session_id: str
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    avg_response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    page_load_time_ms: float = 0.0
    network_requests_count: int = 0
    error_rate: float = 0.0
    last_health_check: Optional[datetime] = None
    uptime_seconds: float = 0.0
    throughput_ops_per_min: float = 0.0


@dataclass
class PoolConfig:
    """Configuration for browser session pool."""
    max_sessions: int = 10
    min_sessions: int = 2
    session_timeout_seconds: int = 1800  # 30 minutes
    health_check_interval_seconds: int = 60
    max_operations_per_session: int = 100
    auto_scaling_enabled: bool = True
    load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    max_memory_usage_mb: int = 512
    max_cpu_usage_percent: float = 80.0
    recovery_attempts: int = 3
    graceful_shutdown_timeout: int = 30


@dataclass
class PoolStats:
    """Statistics for browser session pool."""
    total_sessions: int = 0
    active_sessions: int = 0
    idle_sessions: int = 0
    busy_sessions: int = 0
    error_sessions: int = 0
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    avg_response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    pool_health_score: float = 100.0
    uptime_seconds: float = 0.0
    last_scaling_action: Optional[datetime] = None


class BrowserSessionPool:
    """
    Advanced Browser Session Pool Manager
    
    Manages a pool of browser sessions with health monitoring,
    load balancing, and automatic recovery capabilities.
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the browser session pool."""
        self.config_manager = config_manager or ConfigManager()
        self.pool_config = PoolConfig(
            max_sessions=self.config_manager.get("browser.pool.max_sessions", 10),
            min_sessions=self.config_manager.get("browser.pool.min_sessions", 2),
            session_timeout_seconds=self.config_manager.get("browser.pool.session_timeout", 1800),
            health_check_interval_seconds=self.config_manager.get("browser.pool.health_check_interval", 60),
            auto_scaling_enabled=self.config_manager.get("browser.pool.auto_scaling", True),
            load_balancing_strategy=LoadBalancingStrategy(
                self.config_manager.get("browser.pool.load_balancing_strategy", "round_robin")
            )
        )
        
        # Session management
        self.sessions: Dict[str, BrowserSession] = {}
        self.session_metrics: Dict[str, SessionMetrics] = {}
        self.pool_stats = PoolStats()
        
        # Load balancing
        self.round_robin_index = 0
        self.performance_scores: Dict[str, float] = {}
        
        # Health monitoring
        self.health_monitor_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.scaling_task: Optional[asyncio.Task] = None
        
        # Thread safety
        self._lock = asyncio.Lock()
        
        # Performance tracking
        self.operation_history: List[Dict[str, Any]] = []
        self.recent_operations_window = 100
        
        logger.info("BrowserSessionPool initialized successfully")
    
    async def start(self):
        """Start the browser session pool."""
        logger.info("Starting BrowserSessionPool...")
        
        # Initialize minimum sessions
        await self._initialize_sessions()
        
        # Start monitoring tasks
        self.health_monitor_task = asyncio.create_task(self._health_monitor())
        self.cleanup_task = asyncio.create_task(self._cleanup_worker())
        
        if self.pool_config.auto_scaling_enabled:
            self.scaling_task = asyncio.create_task(self._auto_scaling_worker())
        
        logger.info("BrowserSessionPool started successfully")
    
    async def stop(self):
        """Stop the browser session pool."""
        logger.info("Stopping BrowserSessionPool...")
        
        # Stop monitoring tasks
        for task in [self.health_monitor_task, self.cleanup_task, self.scaling_task]:
            if task:
                task.cancel()
        
        # Close all sessions
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self._close_session(session_id)
        
        logger.info("BrowserSessionPool stopped successfully")
    
    async def _initialize_sessions(self):
        """Initialize minimum number of sessions."""
        logger.info(f"Initializing {self.pool_config.min_sessions} sessions...")
        
        for i in range(self.pool_config.min_sessions):
            try:
                config = BrowserConfig(
                    name=f"pool_session_{i}",
                    headless=True,
                    enable_stealth=True
                )
                
                session = await self._create_session(config)
                logger.info(f"Created initial session: {session.session_id}")
                
            except Exception as e:
                logger.error(f"Failed to create initial session {i}: {e}")
        
        logger.info(f"Initialized {len(self.sessions)} sessions")
    
    async def get_session(self, preferred_bookmaker: Optional[str] = None) -> Optional[BrowserSession]:
        """Get an available browser session using load balancing."""
        async with self._lock:
            # Find available sessions
            available_sessions = []
            
            for session_id, session in self.sessions.items():
                if session.status == SessionStatus.ACTIVE or session.status == SessionStatus.IDLE:
                    if not preferred_bookmaker or preferred_bookmaker in session.bookmaker_configs:
                        available_sessions.append((session_id, session))
            
            if not available_sessions:
                logger.warning("No available sessions found")
                return None
            
            # Apply load balancing strategy
            selected_session = self._select_session(available_sessions)
            
            if selected_session:
                # Update session status
                self.sessions[selected_session.session_id].status = SessionStatus.BUSY
                self.sessions[selected_session.session_id].last_activity = datetime.now()
                
                # Update metrics
                if selected_session.session_id in self.session_metrics:
                    self.session_metrics[selected_session.session_id].total_operations += 1
                
                logger.info(f"Selected session: {selected_session.session_id}")
                return selected_session
        
        return None
    
    def _select_session(self, available_sessions: List[Tuple[str, BrowserSession]]) -> Optional[BrowserSession]:
        """Select session using load balancing strategy."""
        if not available_sessions:
            return None
        
        strategy = self.pool_config.load_balancing_strategy
        
        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            index = self.round_robin_index % len(available_sessions)
            self.round_robin_index += 1
            return available_sessions[index][1]
        
        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            # Select session with least operations
            session = min(available_sessions, key=lambda x: x[1].operations_count)[1]
            return session
        
        elif strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            # Implement weighted round robin based on performance
            weights = []
            for session_id, session in available_sessions:
                weight = self.performance_scores.get(session_id, 1.0)
                weights.append(weight)
            
            # Select based on weights
            total_weight = sum(weights)
            if total_weight > 0:
                rand = random.uniform(0, total_weight)
                cumulative = 0
                for i, (session_id, session) in enumerate(available_sessions):
                    cumulative += weights[i]
                    if rand <= cumulative:
                        return session
            
            # Fallback to first session
            return available_sessions[0][1]
        
        elif strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(available_sessions)[1]
        
        elif strategy == LoadBalancingStrategy.PERFORMANCE_BASED:
            # Select session with best performance score
            best_session = None
            best_score = 0
            
            for session_id, session in available_sessions:
                score = self.performance_scores.get(session_id, 0)
                if score > best_score:
                    best_score = score
                    best_session = session
            
            return best_session or available_sessions[0][1]
        
        else:
            return available_sessions[0][1]
    
    async def release_session(self, session: BrowserSession):
        """Release a browser session back to the pool."""
        async with self._lock:
            if session.session_id in self.sessions:
                session.status = SessionStatus.IDLE
                session.last_activity = datetime.now()
                logger.info(f"Released session: {session.session_id}")
    
    async def _create_session(self, config: BrowserConfig) -> BrowserSession:
        """Create a new browser session."""
        try:
            enhanced_browser = EnhancedBrowser(self.config_manager)
            session = await enhanced_browser.create_session(config)
            
            # Register in pool
            self.sessions[session.session_id] = session
            
            # Initialize metrics
            self.session_metrics[session.session_id] = SessionMetrics(
                session_id=session.session_id,
                last_health_check=datetime.now()
            )
            
            # Calculate initial performance score
            self.performance_scores[session.session_id] = 100.0
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def _close_session(self, session_id: str):
        """Close a browser session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            try:
                # Graceful shutdown
                await session.context.close()
                
                # Clean up
                del self.sessions[session_id]
                if session_id in self.session_metrics:
                    del self.session_metrics[session_id]
                if session_id in self.performance_scores:
                    del self.performance_scores[session_id]
                
                logger.info(f"Closed session: {session_id}")
                
            except Exception as e:
                logger.error(f"Error closing session {session_id}: {e}")
    
    async def _health_monitor(self):
        """Monitor health of all sessions."""
        while True:
            try:
                await asyncio.sleep(self.pool_config.health_check_interval_seconds)
                await self._perform_health_checks()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
    
    async def _perform_health_checks(self):
        """Perform health checks on all sessions."""
        unhealthy_sessions = []
        
        for session_id, session in self.sessions.items():
            try:
                health_status = await self._check_session_health(session)
                
                if health_status == HealthStatus.UNHEALTHY:
                    unhealthy_sessions.append(session_id)
                
                # Update metrics
                if session_id in self.session_metrics:
                    metrics = self.session_metrics[session_id]
                    metrics.last_health_check = datetime.now()
                    metrics.uptime_seconds = (datetime.now() - session.created_at).total_seconds()
                    
                    # Update performance score
                    self.performance_scores[session_id] = self._calculate_performance_score(metrics)
                
            except Exception as e:
                logger.error(f"Health check failed for session {session_id}: {e}")
                unhealthy_sessions.append(session_id)
        
        # Handle unhealthy sessions
        for session_id in unhealthy_sessions:
            await self._handle_unhealthy_session(session_id)
        
        # Update pool statistics
        await self._update_pool_stats()
    
    async def _check_session_health(self, session: BrowserSession) -> HealthStatus:
        """Check health of a single session."""
        try:
            # Check if session is responsive
            await session.page.evaluate("1")  # Simple test
            
            # Check memory usage
            memory_info = await self._get_session_memory_usage(session)
            if memory_info > self.pool_config.max_memory_usage_mb:
                return HealthStatus.DEGRADED
            
            # Check error rate
            if session.error_count > 10:
                return HealthStatus.DEGRADED
            
            # Check session age
            age = (datetime.now() - session.created_at).total_seconds()
            if age > self.pool_config.session_timeout_seconds:
                return HealthStatus.DEGRADED
            
            return HealthStatus.HEALTHY
            
        except Exception as e:
            logger.error(f"Session health check failed: {e}")
            return HealthStatus.UNHEALTHY
    
    async def _get_session_memory_usage(self, session: BrowserSession) -> float:
        """Get memory usage of a browser session in MB."""
        try:
            # This is a simplified implementation
            # In practice, you'd need to get actual browser process memory
            return random.uniform(50, 200)  # Placeholder
            
        except Exception:
            return 0.0
    
    def _calculate_performance_score(self, metrics: SessionMetrics) -> float:
        """Calculate performance score for a session."""
        try:
            # Base score
            score = 100.0
            
            # Adjust based on success rate
            if metrics.total_operations > 0:
                success_rate = metrics.successful_operations / metrics.total_operations
                score *= success_rate
            
            # Adjust based on response time
            if metrics.avg_response_time_ms > 0:
                response_time_penalty = min(metrics.avg_response_time_ms / 1000.0, 50.0)  # Max 50 point penalty
                score -= response_time_penalty
            
            # Adjust based on error rate
            score *= (1.0 - metrics.error_rate)
            
            # Ensure score is between 0 and 100
            return max(0.0, min(100.0, score))
            
        except Exception:
            return 50.0  # Default score
    
    async def _handle_unhealthy_session(self, session_id: str):
        """Handle an unhealthy session."""
        if session_id not in self.sessions:
            return
        
        session = self.sessions[session_id]
        logger.warning(f"Handling unhealthy session: {session_id}")
        
        try:
            # Try to recover the session
            recovery_success = await self._recover_session(session)
            
            if not recovery_success:
                # Close and replace the session
                logger.error(f"Failed to recover session {session_id}, replacing...")
                await self._close_session(session_id)
                
                # Create a new session if below minimum
                if len(self.sessions) < self.pool_config.min_sessions:
                    config = BrowserConfig(
                        name=f"recovery_session_{uuid4().hex[:8]}",
                        headless=True,
                        enable_stealth=True
                    )
                    await self._create_session(config)
        
        except Exception as e:
            logger.error(f"Error handling unhealthy session {session_id}: {e}")
    
    async def _recover_session(self, session: BrowserSession) -> bool:
        """Attempt to recover an unhealthy session."""
        try:
            # Mark as recovering
            session.status = SessionStatus.RECOVERING
            
            # Refresh page
            await session.page.reload()
            
            # Wait for page to stabilize
            await asyncio.sleep(5)
            
            # Test session
            await session.page.evaluate("1")
            
            # Reset error count
            session.error_count = 0
            
            # Mark as active
            session.status = SessionStatus.ACTIVE
            
            logger.info(f"Successfully recovered session: {session.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to recover session {session.session_id}: {e}")
            session.status = SessionStatus.ERROR
            return False
    
    async def _cleanup_worker(self):
        """Clean up expired and inactive sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                await self._cleanup_expired_sessions()
                await self._cleanup_operation_history()
                gc.collect()  # Force garbage collection
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = datetime.now()
        sessions_to_close = []
        
        for session_id, session in self.sessions.items():
            # Check if session is expired
            age = (current_time - session.created_at).total_seconds()
            idle_time = (current_time - session.last_activity).total_seconds()
            
            if age > self.pool_config.session_timeout_seconds or idle_time > 600:  # 10 minutes idle
                sessions_to_close.append(session_id)
        
        # Close expired sessions if above minimum
        for session_id in sessions_to_close:
            if len(self.sessions) > self.pool_config.min_sessions:
                await self._close_session(session_id)
    
    async def _cleanup_operation_history(self):
        """Clean up old operation history."""
        if len(self.operation_history) > self.recent_operations_window * 2:
            # Keep only the most recent operations
            self.operation_history = self.operation_history[-self.recent_operations_window:]
    
    async def _auto_scaling_worker(self):
        """Handle automatic scaling of the session pool."""
        while True:
            try:
                await asyncio.sleep(120)  # Check every 2 minutes
                await self._perform_auto_scaling()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto scaling worker: {e}")
    
    async def _perform_auto_scaling(self):
        """Perform automatic scaling based on load."""
        try:
            # Calculate load metrics
            total_sessions = len(self.sessions)
            busy_sessions = len([s for s in self.sessions.values() if s.status == SessionStatus.BUSY])
            utilization = busy_sessions / total_sessions if total_sessions > 0 else 0
            
            # Scale up if utilization is high
            if utilization > 0.8 and total_sessions < self.pool_config.max_sessions:
                await self._scale_up()
            
            # Scale down if utilization is low
            elif utilization < 0.2 and total_sessions > self.pool_config.min_sessions:
                await self._scale_down()
            
        except Exception as e:
            logger.error(f"Error in auto scaling: {e}")
    
    async def _scale_up(self):
        """Scale up the session pool."""
        try:
            logger.info("Scaling up browser session pool...")
            
            for i in range(min(2, self.pool_config.max_sessions - len(self.sessions))):
                config = BrowserConfig(
                    name=f"scaled_session_{uuid4().hex[:8]}",
                    headless=True,
                    enable_stealth=True
                )
                await self._create_session(config)
            
            self.pool_stats.last_scaling_action = datetime.now()
            logger.info("Scaled up browser session pool")
            
        except Exception as e:
            logger.error(f"Error scaling up: {e}")
    
    async def _scale_down(self):
        """Scale down the session pool."""
        try:
            logger.info("Scaling down browser session pool...")
            
            # Find idle sessions to close
            idle_sessions = [
                (session_id, session) for session_id, session in self.sessions.items()
                if session.status == SessionStatus.IDLE
            ]
            
            # Close extra idle sessions
            sessions_to_close = idle_sessions[:min(2, len(idle_sessions))]
            
            for session_id, _ in sessions_to_close:
                if len(self.sessions) > self.pool_config.min_sessions:
                    await self._close_session(session_id)
            
            self.pool_stats.last_scaling_action = datetime.now()
            logger.info("Scaled down browser session pool")
            
        except Exception as e:
            logger.error(f"Error scaling down: {e}")
    
    async def _update_pool_stats(self):
        """Update pool statistics."""
        self.pool_stats.total_sessions = len(self.sessions)
        self.pool_stats.active_sessions = len([s for s in self.sessions.values() if s.status == SessionStatus.ACTIVE])
        self.pool_stats.idle_sessions = len([s for s in self.sessions.values() if s.status == SessionStatus.IDLE])
        self.pool_stats.busy_sessions = len([s for s in self.sessions.values() if s.status == SessionStatus.BUSY])
        self.pool_stats.error_sessions = len([s for s in self.sessions.values() if s.status == SessionStatus.ERROR])
        
        # Calculate aggregate metrics
        if self.session_metrics:
            total_ops = sum(m.total_operations for m in self.session_metrics.values())
            successful_ops = sum(m.successful_operations for m in self.session_metrics.values())
            failed_ops = sum(m.failed_operations for m in self.session_metrics.values())
            
            self.pool_stats.total_operations = total_ops
            self.pool_stats.successful_operations = successful_ops
            self.pool_stats.failed_operations = failed_ops
            
            if total_ops > 0:
                self.pool_stats.avg_response_time_ms = sum(m.avg_response_time_ms for m in self.session_metrics.values()) / len(self.session_metrics)
                self.pool_stats.error_rate = failed_ops / total_ops
        
        # Calculate pool health score
        healthy_sessions = len([s for s in self.sessions.values() if s.status in [SessionStatus.ACTIVE, SessionStatus.IDLE]])
        self.pool_stats.pool_health_score = (healthy_sessions / self.pool_stats.total_sessions * 100) if self.pool_stats.total_sessions > 0 else 0.0
    
    def get_pool_stats(self) -> PoolStats:
        """Get current pool statistics."""
        return self.pool_stats
    
    def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """Get metrics for a specific session."""
        return self.session_metrics.get(session_id)
    
    def get_all_session_metrics(self) -> Dict[str, SessionMetrics]:
        """Get metrics for all sessions."""
        return self.session_metrics.copy()
    
    def record_operation(self, session_id: str, operation_type: str, success: bool, 
                        response_time_ms: float, error_message: Optional[str] = None):
        """Record an operation for tracking and analytics."""
        operation = {
            "session_id": session_id,
            "operation_type": operation_type,
            "success": success,
            "response_time_ms": response_time_ms,
            "error_message": error_message,
            "timestamp": datetime.now()
        }
        
        self.operation_history.append(operation)
        
        # Update session metrics if available
        if session_id in self.session_metrics:
            metrics = self.session_metrics[session_id]
            if success:
                metrics.successful_operations += 1
            else:
                metrics.failed_operations += 1
            
            # Update average response time
            if metrics.total_operations > 0:
                metrics.avg_response_time_ms = (
                    (metrics.avg_response_time_ms * (metrics.total_operations - 1) + response_time_ms) /
                    metrics.total_operations
                )


# Example usage and testing
async def main():
    """Example usage of BrowserSessionPool."""
    pool = BrowserSessionPool()
    
    try:
        await pool.start()
        
        # Get a session
        session = await pool.get_session()
        print(f"Got session: {session.session_id if session else 'None'}")
        
        # Release session
        if session:
            await pool.release_session(session)
        
        # Get pool stats
        stats = pool.get_pool_stats()
        print(f"Pool stats: {stats}")
        
        # Wait a bit for health checks
        await asyncio.sleep(5)
        
        # Get updated stats
        stats = pool.get_pool_stats()
        print(f"Updated pool stats: {stats}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        
    finally:
        await pool.stop()


if __name__ == "__main__":
    asyncio.run(main())
