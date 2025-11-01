"""
Tab Coordinator - Advanced tab coordination system for managing multiple bookmaker tabs
with load balancing and health monitoring for seamless AVO Tabs operation.
"""

import asyncio
import json
import logging
import threading
import time
import random
import uuid
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import heapq
import weakref

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoordinationStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    PERFORMANCE_BASED = "performance_based"
    HEALTH_AWARE = "health_aware"


class TabPriority(Enum):
    """Tab priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class CoordinationEvent(Enum):
    """Coordination event types"""
    TAB_ASSIGNED = "tab_assigned"
    TAB_RELEASED = "tab_released"
    TAB_FAILED = "tab_failed"
    TAB_RECOVERED = "tab_recovered"
    LOAD_BALANCED = "load_balanced"
    HEALTH_CHECK = "health_check"
    PRIORITY_CHANGED = "priority_changed"


@dataclass
class BookmakerProfile:
    """Bookmaker configuration and profile"""
    bookmaker_id: str
    name: str
    base_url: str
    supported_markets: List[str]
    max_concurrent_tabs: int
    priority_weight: float
    health_threshold: float
    retry_policy: Dict[str, Any]
    characteristics: Dict[str, Any]
    created_at: datetime
    last_activity: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float


@dataclass
class TabAssignment:
    """Tab assignment information"""
    assignment_id: str
    tab_id: int
    bookmaker_id: str
    task_type: str
    priority: TabPriority
    assigned_at: datetime
    estimated_duration: Optional[float]
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    status: str
    load_balancer_score: float
    retry_count: int
    metadata: Dict[str, Any]


@dataclass
class CoordinationMetrics:
    """Coordination performance metrics"""
    total_assignments: int
    successful_assignments: int
    failed_assignments: int
    average_assignment_time: float
    load_distribution_variance: float
    bookmaker_utilization: Dict[str, float]
    priority_distribution: Dict[str, int]
    health_score: float
    last_updated: datetime


class LoadBalancer:
    """Advanced load balancer for tab assignments"""
    
    def __init__(self, strategy: CoordinationStrategy = CoordinationStrategy.HEALTH_AWARE):
        self.strategy = strategy
        self.assignment_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.bookmaker_loads: Dict[str, float] = defaultdict(float)
        self.performance_scores: Dict[str, float] = defaultdict(lambda: 1.0)
        self.lock = threading.RLock()
    
    def select_bookmaker(self, available_bookmakers: List[BookmakerProfile], 
                        task_requirements: Dict[str, Any]) -> Optional[BookmakerProfile]:
        """Select best bookmaker based on strategy and current load"""
        if not available_bookmakers:
            return None
        
        with self.lock:
            if self.strategy == CoordinationStrategy.ROUND_ROBIN:
                return self._round_robin_select(available_bookmakers)
            elif self.strategy == CoordinationStrategy.LEAST_CONNECTIONS:
                return self._least_connections_select(available_bookmakers)
            elif self.strategy == CoordinationStrategy.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_select(available_bookmakers)
            elif self.strategy == CoordinationStrategy.RANDOM:
                return random.choice(available_bookmakers)
            elif self.strategy == CoordinationStrategy.PERFORMANCE_BASED:
                return self._performance_based_select(available_bookmakers)
            elif self.strategy == CoordinationStrategy.HEALTH_AWARE:
                return self._health_aware_select(available_bookmakers)
            else:
                return available_bookmakers[0]  # Fallback
    
    def _round_robin_select(self, bookmakers: List[BookmakerProfile]) -> BookmakerProfile:
        """Round-robin selection"""
        bookmaker_id = bookmakers[0].bookmaker_id
        history = self.assignment_history[bookmaker_id]
        
        if history:
            last_assigned = history[-1]
            # Find next in sequence
            current_index = next(
                (i for i, bm in enumerate(bookmakers) if bm.bookmaker_id == last_assigned),
                -1
            )
            next_index = (current_index + 1) % len(bookmakers)
            return bookmakers[next_index]
        
        return bookmakers[0]
    
    def _least_connections_select(self, bookmakers: List[BookmakerProfile]) -> BookmakerProfile:
        """Select bookmaker with least current connections"""
        return min(bookmakers, key=lambda bm: self.bookmaker_loads.get(bm.bookmaker_id, 0))
    
    def _weighted_round_robin_select(self, bookmakers: List[BookmakerProfile]) -> BookmakerProfile:
        """Weighted round-robin selection"""
        weights = [(bm.priority_weight, bm) for bm in bookmakers]
        total_weight = sum(weight for weight, _ in weights)
        
        if total_weight == 0:
            return bookmakers[0]
        
        r = random.uniform(0, total_weight)
        weight_sum = 0
        
        for weight, bookmaker in sorted(weights, reverse=True):
            weight_sum += weight
            if r <= weight_sum:
                return bookmaker
        
        return bookmakers[0]
    
    def _performance_based_select(self, bookmakers: List[BookmakerProfile]) -> BookmakerProfile:
        """Select based on historical performance"""
        return max(bookmakers, key=lambda bm: self.performance_scores.get(bm.bookmaker_id, 0))
    
    def _health_aware_select(self, bookmakers: List[BookmakerProfile]) -> BookmakerProfile:
        """Health-aware selection combining multiple factors"""
        scored_bookmakers = []
        
        for bm in bookmakers:
            health_score = self._calculate_bookmaker_health_score(bm)
            load_factor = 1.0 / (1.0 + self.bookmaker_loads.get(bm.bookmaker_id, 0))
            performance_factor = self.performance_scores.get(bm.bookmaker_id, 0)
            
            combined_score = (health_score * 0.4 + load_factor * 0.3 + performance_factor * 0.3)
            scored_bookmakers.append((combined_score, bm))
        
        return max(scored_bookmakers, key=lambda x: x[0])[1]
    
    def _calculate_bookmaker_health_score(self, bookmaker: BookmakerProfile) -> float:
        """Calculate health score for a bookmaker"""
        # Success rate
        total_requests = bookmaker.total_requests
        if total_requests == 0:
            return 1.0
        
        success_rate = bookmaker.successful_requests / total_requests
        
        # Response time factor (normalized)
        avg_response_time = bookmaker.average_response_time
        response_time_score = max(0, 1.0 - (avg_response_time / 10.0))  # Normalize to 10s max
        
        # Recent activity factor
        time_since_activity = (datetime.now() - bookmaker.last_activity).total_seconds()
        activity_score = max(0, 1.0 - (time_since_activity / 3600))  # Penalty for inactivity
        
        # Combine factors
        health_score = (success_rate * 0.5 + response_time_score * 0.3 + activity_score * 0.2)
        return max(0, min(1, health_score))
    
    def update_bookmaker_load(self, bookmaker_id: str, delta: float):
        """Update bookmaker load"""
        with self.lock:
            self.bookmaker_loads[bookmaker_id] += delta
            if self.bookmaker_loads[bookmaker_id] < 0:
                self.bookmaker_loads[bookmaker_id] = 0
    
    def update_performance_score(self, bookmaker_id: str, success: bool, response_time: float):
        """Update performance score based on assignment results"""
        with self.lock:
            current_score = self.performance_scores[bookmaker_id]
            
            if success:
                # Positive feedback with response time consideration
                performance_bonus = max(0.1, 1.0 - (response_time / 5.0))  # Bonus for fast responses
                new_score = min(1.0, current_score + performance_bonus * 0.1)
            else:
                # Negative feedback
                new_score = max(0.1, current_score - 0.2)
            
            self.performance_scores[bookmaker_id] = new_score
    
    def record_assignment(self, bookmaker_id: str, assignment_result: str):
        """Record assignment result for history"""
        with self.lock:
            self.assignment_history[bookmaker_id].append({
                'timestamp': datetime.now(),
                'result': assignment_result
            })


class HealthMonitor:
    """Advanced health monitoring for bookmaker tabs"""
    
    def __init__(self, check_interval: float = 30.0, failure_threshold: int = 3):
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.bookmaker_health: Dict[str, Dict[str, Any]] = {}
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()
        
    def start_monitoring(self):
        """Start health monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        logger.info("Health monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                self._perform_health_checks()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(5.0)
    
    def _perform_health_checks(self):
        """Perform health checks on all monitored bookmakers"""
        with self.lock:
            bookmakers_to_check = list(self.bookmaker_health.keys())
        
        for bookmaker_id in bookmakers_to_check:
            try:
                self._check_bookmaker_health(bookmaker_id)
            except Exception as e:
                logger.error(f"Health check failed for {bookmaker_id}: {e}")
    
    def _check_bookmaker_health(self, bookmaker_id: str):
        """Check health of a specific bookmaker"""
        health_data = self.bookmaker_health.get(bookmaker_id, {})
        
        # Simulate health check
        # In real implementation, this would perform actual health checks
        is_healthy = self._simulate_health_check(bookmaker_id)
        
        with self.lock:
            if bookmaker_id not in self.bookmaker_health:
                self.bookmaker_health[bookmaker_id] = {
                    'failure_count': 0,
                    'last_check': datetime.now(),
                    'consecutive_failures': 0,
                    'last_success': datetime.now(),
                    'status': 'unknown'
                }
            
            bookmaker_health = self.bookmaker_health[bookmaker_id]
            bookmaker_health['last_check'] = datetime.now()
            
            if is_healthy:
                bookmaker_health['consecutive_failures'] = 0
                bookmaker_health['last_success'] = datetime.now()
                bookmaker_health['status'] = 'healthy'
            else:
                bookmaker_health['consecutive_failures'] += 1
                if bookmaker_health['consecutive_failures'] >= self.failure_threshold:
                    bookmaker_health['status'] = 'unhealthy'
    
    def _simulate_health_check(self, bookmaker_id: str) -> bool:
        """Simulate health check (replace with real implementation)"""
        # This would perform actual connectivity and response tests
        return random.random() > 0.1  # 90% success rate simulation
    
    def register_bookmaker(self, bookmaker: BookmakerProfile):
        """Register bookmaker for health monitoring"""
        with self.lock:
            self.bookmaker_health[bookmaker.bookmaker_id] = {
                'failure_count': 0,
                'last_check': datetime.now(),
                'consecutive_failures': 0,
                'last_success': datetime.now(),
                'status': 'unknown',
                'bookmaker': bookmaker
            }
        logger.info(f"Registered {bookmaker.bookmaker_id} for health monitoring")
    
    def unregister_bookmaker(self, bookmaker_id: str):
        """Unregister bookmaker from health monitoring"""
        with self.lock:
            if bookmaker_id in self.bookmaker_health:
                del self.bookmaker_health[bookmaker_id]
        logger.info(f"Unregistered {bookmaker_id} from health monitoring")
    
    def get_bookmaker_health(self, bookmaker_id: str) -> Optional[Dict[str, Any]]:
        """Get health status of a bookmaker"""
        with self.lock:
            return self.bookmaker_health.get(bookmaker_id)
    
    def get_all_bookmaker_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all bookmakers"""
        with self.lock:
            return self.bookmaker_health.copy()
    
    def mark_failure(self, bookmaker_id: str):
        """Mark a failure for a bookmaker"""
        with self.lock:
            if bookmaker_id in self.bookmaker_health:
                self.bookmaker_health[bookmaker_id]['failure_count'] += 1
                self.bookmaker_health[bookmaker_id]['consecutive_failures'] += 1
    
    def mark_success(self, bookmaker_id: str):
        """Mark a success for a bookmaker"""
        with self.lock:
            if bookmaker_id in self.bookmaker_health:
                self.bookmaker_health[bookmaker_id]['consecutive_failures'] = 0
                self.bookmaker_health[bookmaker_id]['last_success'] = datetime.now()
                self.bookmaker_health[bookmaker_id]['status'] = 'healthy'


class TabCoordinator:
    """Advanced tab coordination system"""
    
    def __init__(self, tab_manager, strategy: CoordinationStrategy = CoordinationStrategy.HEALTH_AWARE):
        self.tab_manager = tab_manager
        self.strategy = strategy
        self.load_balancer = LoadBalancer(strategy)
        self.health_monitor = HealthMonitor()
        
        # Bookmaker registry
        self.bookmakers: Dict[str, BookmakerProfile] = {}
        
        # Tab assignments
        self.active_assignments: Dict[str, TabAssignment] = {}
        self.assignment_history: deque = deque(maxlen=1000)
        
        # Coordination metrics
        self.metrics = CoordinationMetrics(
            total_assignments=0,
            successful_assignments=0,
            failed_assignments=0,
            average_assignment_time=0.0,
            load_distribution_variance=0.0,
            bookmaker_utilization={},
            priority_distribution={},
            health_score=1.0,
            last_updated=datetime.now()
        )
        
        # Event handling
        self.event_handlers: Dict[CoordinationEvent, List[Callable]] = defaultdict(list)
        self.coordination_lock = threading.RLock()
        
        # Background tasks
        self.monitoring_active = False
        self.rebalance_active = False
        
        logger.info("Tab Coordinator initialized")
    
    def register_event_handler(self, event_type: CoordinationEvent, handler: Callable):
        """Register event handler for coordination events"""
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler for {event_type.value}")
    
    def _emit_event(self, event_type: CoordinationEvent, data: Dict[str, Any]):
        """Emit coordination event"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Event handler error for {event_type.value}: {e}")
    
    def register_bookmaker(self, bookmaker: BookmakerProfile) -> bool:
        """Register a bookmaker for coordination"""
        try:
            with self.coordination_lock:
                self.bookmakers[bookmaker.bookmaker_id] = bookmaker
                self.health_monitor.register_bookmaker(bookmaker)
                self._update_metrics()
                
                self._emit_event(CoordinationEvent.HEALTH_CHECK, {
                    'bookmaker_id': bookmaker.bookmaker_id,
                    'action': 'registered',
                    'bookmaker': asdict(bookmaker)
                })
                
                logger.info(f"Registered bookmaker: {bookmaker.bookmaker_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error registering bookmaker {bookmaker.bookmaker_id}: {e}")
            return False
    
    def unregister_bookmaker(self, bookmaker_id: str) -> bool:
        """Unregister a bookmaker from coordination"""
        try:
            with self.coordination_lock:
                if bookmaker_id in self.bookmakers:
                    del self.bookmakers[bookmaker_id]
                    self.health_monitor.unregister_bookmaker(bookmaker_id)
                    self._update_metrics()
                    
                    self._emit_event(CoordinationEvent.HEALTH_CHECK, {
                        'bookmaker_id': bookmaker_id,
                        'action': 'unregistered'
                    })
                    
                    logger.info(f"Unregistered bookmaker: {bookmaker_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error unregistering bookmaker {bookmaker_id}: {e}")
            return False
    
    def assign_tab(self, task_type: str, priority: TabPriority, 
                   requirements: Dict[str, Any] = None) -> Optional[str]:
        """Assign a tab to handle a task"""
        try:
            if not requirements:
                requirements = {}
            
            with self.coordination_lock:
                # Filter available bookmakers
                available_bookmakers = self._get_available_bookmakers(requirements)
                
                if not available_bookmakers:
                    logger.warning("No available bookmakers for assignment")
                    return None
                
                # Select best bookmaker using load balancer
                selected_bookmaker = self.load_balancer.select_bookmaker(
                    available_bookmakers, requirements
                )
                
                if not selected_bookmaker:
                    logger.warning("Load balancer could not select bookmaker")
                    return None
                
                # Create assignment
                assignment_id = str(uuid.uuid4())
                assignment = TabAssignment(
                    assignment_id=assignment_id,
                    tab_id=0,  # Will be assigned by tab manager
                    bookmaker_id=selected_bookmaker.bookmaker_id,
                    task_type=task_type,
                    priority=priority,
                    assigned_at=datetime.now(),
                    estimated_duration=requirements.get('estimated_duration'),
                    actual_start_time=None,
                    actual_end_time=None,
                    status='pending',
                    load_balancer_score=0.0,
                    retry_count=0,
                    metadata=requirements.copy()
                )
                
                # Request tab from tab manager
                tab_id = self._request_tab_from_manager(
                    selected_bookmaker, task_type, requirements
                )
                
                if not tab_id:
                    logger.error(f"Failed to get tab for {selected_bookmaker.bookmaker_id}")
                    return None
                
                assignment.tab_id = tab_id
                assignment.load_balancer_score = self._calculate_assignment_score(assignment)
                
                # Store assignment
                self.active_assignments[assignment_id] = assignment
                self.metrics.total_assignments += 1
                
                # Update bookmaker activity
                selected_bookmaker.last_activity = datetime.now()
                selected_bookmaker.total_requests += 1
                
                # Update load balancer
                self.load_balancer.update_bookmaker_load(selected_bookmaker.bookmaker_id, 1.0)
                
                # Emit event
                self._emit_event(CoordinationEvent.TAB_ASSIGNED, {
                    'assignment_id': assignment_id,
                    'tab_id': tab_id,
                    'bookmaker_id': selected_bookmaker.bookmaker_id,
                    'task_type': task_type,
                    'priority': priority.value
                })
                
                logger.info(f"Assigned tab {tab_id} to {selected_bookmaker.bookmaker_id} for {task_type}")
                return assignment_id
                
        except Exception as e:
            logger.error(f"Error assigning tab: {e}")
            return None
    
    def release_tab(self, assignment_id: str, success: bool = True, 
                   response_time: Optional[float] = None) -> bool:
        """Release a tab assignment"""
        try:
            with self.coordination_lock:
                if assignment_id not in self.active_assignments:
                    logger.warning(f"Assignment {assignment_id} not found")
                    return False
                
                assignment = self.active_assignments[assignment_id]
                assignment.status = 'completed' if success else 'failed'
                assignment.actual_end_time = datetime.now()
                
                # Update metrics
                if success:
                    self.metrics.successful_assignments += 1
                else:
                    self.metrics.failed_assignments += 1
                
                # Update load balancer performance
                self.load_balancer.update_performance_score(
                    assignment.bookmaker_id, success, response_time or 0.0
                )
                self.load_balancer.record_assignment(assignment.bookmaker_id, 'success' if success else 'failure')
                
                # Release tab back to pool
                self._release_tab_to_manager(assignment.tab_id)
                self.load_balancer.update_bookmaker_load(assignment.bookmaker_id, -1.0)
                
                # Update bookmaker stats
                if assignment.bookmaker_id in self.bookmakers:
                    bookmaker = self.bookmakers[assignment.bookmaker_id]
                    if success:
                        bookmaker.successful_requests += 1
                    else:
                        bookmaker.failed_requests += 1
                    if response_time:
                        # Update average response time
                        bookmaker.average_response_time = (
                            (bookmaker.average_response_time * 0.9) + (response_time * 0.1)
                        )
                
                # Move to history
                self.assignment_history.append(assignment)
                del self.active_assignments[assignment_id]
                
                # Emit event
                self._emit_event(CoordinationEvent.TAB_RELEASED, {
                    'assignment_id': assignment_id,
                    'tab_id': assignment.tab_id,
                    'bookmaker_id': assignment.bookmaker_id,
                    'success': success,
                    'response_time': response_time
                })
                
                self._update_metrics()
                
                logger.info(f"Released assignment {assignment_id} - Success: {success}")
                return True
                
        except Exception as e:
            logger.error(f"Error releasing tab assignment {assignment_id}: {e}")
            return False
    
    def retry_assignment(self, assignment_id: str) -> bool:
        """Retry a failed assignment"""
        try:
            with self.coordination_lock:
                if assignment_id not in self.active_assignments:
                    logger.warning(f"Assignment {assignment_id} not found for retry")
                    return False
                
                assignment = self.active_assignments[assignment_id]
                
                if assignment.retry_count >= 3:  # Max 3 retries
                    logger.warning(f"Assignment {assignment_id} exceeded retry limit")
                    return False
                
                assignment.retry_count += 1
                assignment.status = 'retrying'
                assignment.assigned_at = datetime.now()
                assignment.actual_start_time = None
                assignment.actual_end_time = None
                
                # Get new tab for retry
                bookmaker = self.bookmakers.get(assignment.bookmaker_id)
                if not bookmaker:
                    return False
                
                new_tab_id = self._request_tab_from_manager(
                    bookmaker, assignment.task_type, assignment.metadata
                )
                
                if new_tab_id:
                    assignment.tab_id = new_tab_id
                    assignment.load_balancer_score = self._calculate_assignment_score(assignment)
                    
                    self._emit_event(CoordinationEvent.TAB_ASSIGNED, {
                        'assignment_id': assignment_id,
                        'tab_id': new_tab_id,
                        'bookmaker_id': assignment.bookmaker_id,
                        'retry_count': assignment.retry_count
                    })
                    
                    logger.info(f"Retrying assignment {assignment_id} (attempt {assignment.retry_count})")
                    return True
                else:
                    logger.error(f"Failed to get tab for retry of {assignment_id}")
                    return False
                
        except Exception as e:
            logger.error(f"Error retrying assignment {assignment_id}: {e}")
            return False
    
    def _get_available_bookmakers(self, requirements: Dict[str, Any]) -> List[BookmakerProfile]:
        """Get list of available bookmakers based on requirements"""
        available = []
        
        for bookmaker in self.bookmakers.values():
            # Check capacity
            current_load = self.load_balancer.bookmaker_loads.get(bookmaker.bookmaker_id, 0)
            if current_load >= bookmaker.max_concurrent_tabs:
                continue
            
            # Check health status
            health_status = self.health_monitor.get_bookmaker_health(bookmaker.bookmaker_id)
            if health_status and health_status.get('status') == 'unhealthy':
                continue
            
            # Check requirements
            if self._meets_requirements(bookmaker, requirements):
                available.append(bookmaker)
        
        return available
    
    def _meets_requirements(self, bookmaker: BookmakerProfile, requirements: Dict[str, Any]) -> bool:
        """Check if bookmaker meets task requirements"""
        # Check supported markets
        if 'required_markets' in requirements:
            required_markets = requirements['required_markets']
            if not any(market in bookmaker.supported_markets for market in required_markets):
                return False
        
        # Check minimum health score
        if 'min_health_score' in requirements:
            health_data = self.health_monitor.get_bookmaker_health(bookmaker.bookmaker_id)
            if not health_data:
                return False
            
            # This would calculate actual health score
            # For now, use a simplified check
            if health_data.get('status') != 'healthy':
                return False
        
        return True
    
    def _request_tab_from_manager(self, bookmaker: BookmakerProfile, task_type: str, 
                                requirements: Dict[str, Any]) -> Optional[int]:
        """Request tab from tab manager"""
        try:
            # Create appropriate URL for bookmaker
            base_url = requirements.get('specific_url') or bookmaker.base_url
            
            # Map task types to tab types
            tab_type_mapping = {
                'market_scan': 'bookmaker_primary',
                'odds_comparison': 'bookmaker_secondary',
                'arbitrage_check': 'bookmaker_backup',
                'monitoring': 'arbitrage_monitor',
                'trading': 'trading_dashboard'
            }
            
            tab_type_str = tab_type_mapping.get(task_type, 'bookmaker_primary')
            
            # Request tab through tab manager
            tab_id = self.tab_manager.create_tab(
                url=base_url,
                tab_type=tab_type_str,
                bookmaker_id=bookmaker.bookmaker_id,
                metadata={
                    'task_type': task_type,
                    'requirements': requirements,
                    'coordinator_id': str(uuid.uuid4())
                }
            )
            
            return tab_id
            
        except Exception as e:
            logger.error(f"Error requesting tab from manager: {e}")
            return None
    
    def _release_tab_to_manager(self, tab_id: int):
        """Release tab back to tab manager"""
        try:
            self.tab_manager.close_tab(tab_id)
        except Exception as e:
            logger.error(f"Error releasing tab to manager: {e}")
    
    def _calculate_assignment_score(self, assignment: TabAssignment) -> float:
        """Calculate load balancer score for assignment"""
        try:
            bookmaker = self.bookmakers.get(assignment.bookmaker_id)
            if not bookmaker:
                return 0.0
            
            # Base score from bookmaker weight
            base_score = bookmaker.priority_weight
            
            # Adjust for current load
            current_load = self.load_balancer.bookmaker_loads.get(assignment.bookmaker_id, 0)
            load_factor = 1.0 / (1.0 + current_load)
            
            # Adjust for priority
            priority_factor = {
                TabPriority.CRITICAL: 1.5,
                TabPriority.HIGH: 1.2,
                TabPriority.NORMAL: 1.0,
                TabPriority.LOW: 0.8,
                TabPriority.BACKGROUND: 0.6
            }.get(assignment.priority, 1.0)
            
            # Adjust for historical performance
            performance_score = self.load_balancer.performance_scores.get(assignment.bookmaker_id, 1.0)
            
            final_score = base_score * load_factor * priority_factor * performance_score
            return max(0.0, min(2.0, final_score))  # Clamp between 0 and 2
            
        except Exception as e:
            logger.error(f"Error calculating assignment score: {e}")
            return 1.0
    
    def _update_metrics(self):
        """Update coordination metrics"""
        try:
            with self.coordination_lock:
                # Update bookmaker utilization
                utilization = {}
                for bookmaker_id, bookmaker in self.bookmakers.items():
                    current_load = self.load_balancer.bookmaker_loads.get(bookmaker_id, 0)
                    utilization[bookmaker_id] = current_load / bookmaker.max_concurrent_tabs
                
                self.metrics.bookmaker_utilization = utilization
                
                # Update priority distribution
                priority_dist = defaultdict(int)
                for assignment in self.active_assignments.values():
                    priority_dist[assignment.priority.value] += 1
                
                self.metrics.priority_distribution = dict(priority_dist)
                
                # Calculate overall health score
                total_bookmakers = len(self.bookmakers)
                if total_bookmakers > 0:
                    healthy_bookmakers = 0
                    for health_data in self.health_monitor.get_all_bookmaker_health().values():
                        if health_data.get('status') == 'healthy':
                            healthy_bookmakers += 1
                    
                    self.metrics.health_score = healthy_bookmakers / total_bookmakers
                
                self.metrics.last_updated = datetime.now()
                
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def start_coordination(self):
        """Start coordination system"""
        try:
            if not self.monitoring_active:
                self.monitoring_active = True
                self.health_monitor.start_monitoring()
                
                # Start rebalancing thread
                rebalance_thread = threading.Thread(target=self._rebalancing_loop, daemon=True)
                rebalance_thread.start()
                
                logger.info("Tab coordination started")
        except Exception as e:
            logger.error(f"Error starting coordination: {e}")
    
    def stop_coordination(self):
        """Stop coordination system"""
        try:
            self.monitoring_active = False
            self.rebalance_active = False
            self.health_monitor.stop_monitoring()
            
            logger.info("Tab coordination stopped")
        except Exception as e:
            logger.error(f"Error stopping coordination: {e}")
    
    def _rebalancing_loop(self):
        """Background rebalancing loop"""
        while self.monitoring_active:
            try:
                self._perform_load_rebalancing()
                time.sleep(60.0)  # Rebalance every minute
            except Exception as e:
                logger.error(f"Rebalancing error: {e}")
                time.sleep(10.0)
    
    def _perform_load_rebalancing(self):
        """Perform load rebalancing across bookmakers"""
        try:
            # Identify overloaded bookmakers
            overloaded = []
            underloaded = []
            
            for bookmaker_id, bookmaker in self.bookmakers.items():
                current_load = self.load_balancer.bookmaker_loads.get(bookmaker_id, 0)
                load_ratio = current_load / bookmaker.max_concurrent_tabs
                
                if load_ratio > 0.8:  # Overloaded
                    overloaded.append((bookmaker_id, load_ratio))
                elif load_ratio < 0.3:  # Underloaded
                    underloaded.append((bookmaker_id, load_ratio))
            
            # Attempt rebalancing
            if overloaded and underloaded:
                self._rebalance_load(overloaded, underloaded)
                
        except Exception as e:
            logger.error(f"Error performing load rebalancing: {e}")
    
    def _rebalance_load(self, overloaded: List[Tuple[str, float]], 
                       underloaded: List[Tuple[str, float]]):
        """Rebalance load between overloaded and underloaded bookmakers"""
        try:
            for overloaded_id, _ in overloaded:
                # Find assignments that can be moved
                movable_assignments = [
                    assignment for assignment in self.active_assignments.values()
                    if assignment.bookmaker_id == overloaded_id and assignment.priority in [TabPriority.LOW, TabPriority.BACKGROUND]
                ]
                
                for assignment in movable_assignments[:2]:  # Move max 2 assignments
                    # Try to reassign to underloaded bookmaker
                    available_bookmakers = self._get_available_bookmakers(assignment.metadata)
                    underloaded_bookmakers = [
                        bm for bm in available_bookmakers 
                        if bm.bookmaker_id in [uid for uid, _ in underloaded]
                    ]
                    
                    if underloaded_bookmakers:
                        target_bookmaker = random.choice(underloaded_bookmakers)
                        
                        # Release from current bookmaker
                        self.load_balancer.update_bookmaker_load(overloaded_id, -1.0)
                        
                        # Assign to target bookmaker
                        new_tab_id = self._request_tab_from_manager(
                            target_bookmaker, assignment.task_type, assignment.metadata
                        )
                        
                        if new_tab_id:
                            assignment.bookmaker_id = target_bookmaker.bookmaker_id
                            assignment.tab_id = new_tab_id
                            assignment.load_balancer_score = self._calculate_assignment_score(assignment)
                            
                            self.load_balancer.update_bookmaker_load(target_bookmaker.bookmaker_id, 1.0)
                            
                            self._emit_event(CoordinationEvent.LOAD_BALANCED, {
                                'assignment_id': assignment.assignment_id,
                                'from_bookmaker': overloaded_id,
                                'to_bookmaker': target_bookmaker.bookmaker_id
                            })
                            
                            logger.debug(f"Rebalanced assignment {assignment.assignment_id} from {overloaded_id} to {target_bookmaker.bookmaker_id}")
                            
        except Exception as e:
            logger.error(f"Error rebalancing load: {e}")
    
    def get_coordination_status(self) -> Dict[str, Any]:
        """Get comprehensive coordination status"""
        try:
            with self.coordination_lock:
                health_status = self.health_monitor.get_all_bookmaker_health()
                
                return {
                    'active': self.monitoring_active,
                    'strategy': self.strategy.value,
                    'total_bookmakers': len(self.bookmakers),
                    'active_assignments': len(self.active_assignments),
                    'completed_assignments': len(self.assignment_history),
                    'metrics': asdict(self.metrics),
                    'bookmaker_health': health_status,
                    'load_distribution': dict(self.load_balancer.bookmaker_loads),
                    'performance_scores': dict(self.load_balancer.performance_scores),
                    'bookmakers': {
                        bid: asdict(bookmaker) for bid, bookmaker in self.bookmakers.items()
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting coordination status: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def get_bookmaker_profile(self, bookmaker_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed bookmaker profile"""
        try:
            bookmaker = self.bookmakers.get(bookmaker_id)
            if bookmaker:
                health_data = self.health_monitor.get_bookmaker_health(bookmaker_id)
                load_info = {
                    'current_load': self.load_balancer.bookmaker_loads.get(bookmaker_id, 0),
                    'performance_score': self.load_balancer.performance_scores.get(bookmaker_id, 0)
                }
                
                return {
                    'profile': asdict(bookmaker),
                    'health': health_data,
                    'load': load_info,
                    'recent_assignments': [
                        asdict(assignment) for assignment in self.assignment_history
                        if assignment.bookmaker_id == bookmaker_id
                    ][-10:]  # Last 10 assignments
                }
            return None
        except Exception as e:
            logger.error(f"Error getting bookmaker profile: {e}")
            return None
    
    def update_bookmaker_priority(self, bookmaker_id: str, new_priority: float):
        """Update bookmaker priority weight"""
        try:
            if bookmaker_id in self.bookmakers:
                old_priority = self.bookmakers[bookmaker_id].priority_weight
                self.bookmakers[bookmaker_id].priority_weight = new_priority
                
                self._emit_event(CoordinationEvent.PRIORITY_CHANGED, {
                    'bookmaker_id': bookmaker_id,
                    'old_priority': old_priority,
                    'new_priority': new_priority
                })
                
                logger.info(f"Updated {bookmaker_id} priority from {old_priority} to {new_priority}")
        except Exception as e:
            logger.error(f"Error updating bookmaker priority: {e}")
    
    def emergency_recovery(self) -> Dict[str, Any]:
        """Perform emergency recovery procedures"""
        recovery_report = {
            'timestamp': datetime.now().isoformat(),
            'actions_taken': [],
            'bookmakers_affected': [],
            'assignments_recovered': 0
        }
        
        try:
            # Reset failed bookmakers
            for bookmaker_id, health_data in self.health_monitor.get_all_bookmaker_health().items():
                if health_data.get('status') == 'unhealthy':
                    # Reset failure count
                    health_data['consecutive_failures'] = 0
                    health_data['status'] = 'unknown'
                    recovery_report['bookmakers_affected'].append(bookmaker_id)
                    recovery_report['actions_taken'].append(f"Reset health status for {bookmaker_id}")
            
            # Retry failed assignments
            failed_assignments = [
                assignment for assignment in self.active_assignments.values()
                if assignment.status == 'failed'
            ]
            
            for assignment in failed_assignments:
                if self.retry_assignment(assignment.assignment_id):
                    recovery_report['assignments_recovered'] += 1
                    recovery_report['actions_taken'].append(f"Retried assignment {assignment.assignment_id}")
            
            # Reset performance scores for unhealthy bookmakers
            for bookmaker_id in recovery_report['bookmakers_affected']:
                self.load_balancer.performance_scores[bookmaker_id] = 0.5  # Reset to neutral
            
            # Force garbage collection of old assignments
            old_assignments = [
                aid for aid, assignment in self.active_assignments.items()
                if (datetime.now() - assignment.assigned_at).total_seconds() > 3600  # 1 hour
            ]
            
            for assignment_id in old_assignments:
                self.release_tab(assignment_id, success=False)
                recovery_report['actions_taken'].append(f"Cleaned up stale assignment {assignment_id}")
            
            self._update_metrics()
            
            logger.info(f"Emergency recovery completed: {recovery_report}")
            return recovery_report
            
        except Exception as e:
            error_report = {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'partial_recovery': recovery_report
            }
            logger.error(f"Emergency recovery failed: {e}")
            return error_report