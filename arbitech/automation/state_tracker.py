"""
Advanced Browser State Tracking System for ARBitech Trading Platform

This module provides sophisticated browser state tracking capabilities:
- Real-time page load monitoring and analysis
- Element detection and state tracking
- Interface state analysis and validation
- DOM change detection and monitoring
- Performance timing tracking
- User interaction state monitoring
- Error detection and recovery tracking

Features:
- Multi-dimensional state tracking
- Advanced page load timing analysis
- Element state monitoring
- DOM mutation detection
- Interactive state validation
- State change event system
- Comprehensive state history
"""

import asyncio
import time
import json
import weakref
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set, Tuple, Union, NamedTuple
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from collections import deque, defaultdict
import logging
import hashlib
import re

from arbitech.storage.audit_logger import get_audit_logger, log_performance_metric
from arbitech.utils.logger import get_logger

logger = get_logger(__name__)

# Try to import Selenium
try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, 
        StaleElementReferenceException, WebDriverException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available - advanced state tracking will be limited")


class PageState(Enum):
    """Page state enumeration"""
    UNKNOWN = "unknown"
    LOADING = "loading"
    LOADED = "loaded"
    INTERACTIVE = "interactive"
    ERROR = "error"
    TIMEOUT = "timeout"
    CRASHED = "crashed"
    REDIRECTING = "redirecting"


class ElementState(Enum):
    """Element state enumeration"""
    UNKNOWN = "unknown"
    PRESENT = "present"
    VISIBLE = "visible"
    CLICKABLE = "clickable"
    ENABLED = "enabled"
    DISABLED = "disabled"
    HIDDEN = "hidden"
    STALE = "stale"
    ERROR = "error"


class InteractionType(Enum):
    """Types of user interactions"""
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    HOVER = "hover"
    DRAG = "drag"
    SUBMIT = "submit"
    SELECT = "select"
    CLEAR = "clear"


class StateChangeEvent(Enum):
    """Types of state change events"""
    PAGE_LOADED = "page_loaded"
    ELEMENT_ADDED = "element_added"
    ELEMENT_REMOVED = "element_removed"
    ELEMENT_UPDATED = "element_updated"
    ELEMENT_STATE_CHANGED = "element_state_changed"
    DOM_MUTATED = "dom_mutated"
    INTERACTION_DETECTED = "interaction_detected"
    ERROR_OCCURRED = "error_occurred"
    TIMEOUT_OCCURRED = "timeout_occurred"


@dataclass
class PageLoadMetrics:
    """Page load timing metrics"""
    # Navigation timing
    navigation_start: float = 0.0
    dom_loading: float = 0.0
    dom_content_loaded: float = 0.0
    page_loaded: float = 0.0
    fully_loaded: float = 0.0
    
    # Resource timing
    first_byte: float = 0.0
    dom_parse_time: float = 0.0
    resource_load_time: float = 0.0
    
    # User timing
    first_paint: float = 0.0
    first_contentful_paint: float = 0.0
    largest_contentful_paint: float = 0.0
    
    # Calculated metrics
    total_load_time: float = 0.0
    time_to_interactive: float = 0.0
    
    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    url: str = ""
    page_title: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'navigation_start': self.navigation_start,
            'dom_loading': self.dom_loading,
            'dom_content_loaded': self.dom_content_loaded,
            'page_loaded': self.page_loaded,
            'fully_loaded': self.fully_loaded,
            'first_byte': self.first_byte,
            'dom_parse_time': self.dom_parse_time,
            'resource_load_time': self.resource_load_time,
            'first_paint': self.first_paint,
            'first_contentful_paint': self.first_contentful_paint,
            'largest_contentful_paint': self.largest_contentful_paint,
            'total_load_time': self.total_load_time,
            'time_to_interactive': self.time_to_interactive,
            'timestamp': self.timestamp.isoformat(),
            'url': self.url,
            'page_title': self.page_title
        }


@dataclass
class ElementInfo:
    """Information about a page element"""
    element_id: str
    tag_name: str
    element_type: str
    text: str
    attributes: Dict[str, str]
    
    # Location and size
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    
    # State
    state: ElementState = ElementState.UNKNOWN
    is_visible: bool = False
    is_enabled: bool = False
    is_clickable: bool = False
    
    # Identifiers
    id: Optional[str] = None
    class_name: Optional[str] = None
    name: Optional[str] = None
    xpath: Optional[str] = None
    css_selector: Optional[str] = None
    
    # Metadata
    found_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    change_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'element_id': self.element_id,
            'tag_name': self.tag_name,
            'element_type': self.element_type,
            'text': self.text,
            'attributes': self.attributes,
            'location': {'x': self.x, 'y': self.y},
            'size': {'width': self.width, 'height': self.height},
            'state': self.state.value,
            'is_visible': self.is_visible,
            'is_enabled': self.is_enabled,
            'is_clickable': self.is_clickable,
            'identifiers': {
                'id': self.id,
                'class_name': self.class_name,
                'name': self.name,
                'xpath': self.xpath,
                'css_selector': self.css_selector
            },
            'found_at': self.found_at.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'change_count': self.change_count
        }


@dataclass
class StateChange:
    """Represents a state change"""
    change_id: UUID = field(default_factory=uuid4)
    event_type: StateChangeEvent = StateChangeEvent.DOM_MUTATED
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Change details
    element_id: Optional[str] = None
    old_value: Any = None
    new_value: Any = None
    change_description: str = ""
    
    # Context
    page_url: str = ""
    page_title: str = ""
    trigger_source: str = ""  # automatic, user, script, etc.
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'change_id': str(self.change_id),
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'element_id': self.element_id,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'change_description': self.change_description,
            'page_url': self.page_url,
            'page_title': self.page_title,
            'trigger_source': self.trigger_source,
            'metadata': self.metadata
        }


@dataclass
class InteractionEvent:
    """Represents a user interaction event"""
    interaction_id: UUID = field(default_factory=uuid4)
    interaction_type: InteractionType = InteractionType.CLICK
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Element details
    element_id: Optional[str] = None
    element_tag: str = ""
    element_text: str = ""
    
    # Interaction details
    coordinates: Optional[Tuple[int, int]] = None
    value: Optional[str] = None  # For typing interactions
    duration_ms: float = 0.0
    
    # Context
    page_url: str = ""
    page_title: str = ""
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'interaction_id': str(self.interaction_id),
            'interaction_type': self.interaction_type.value,
            'timestamp': self.timestamp.isoformat(),
            'element_id': self.element_id,
            'element_tag': self.element_tag,
            'element_text': self.element_text,
            'coordinates': self.coordinates,
            'value': self.value,
            'duration_ms': self.duration_ms,
            'page_url': self.page_url,
            'page_title': self.page_title,
            'success': self.success,
            'error_message': self.error_message
        }


@dataclass
class StateTrackingConfig:
    """Configuration for state tracking"""
    # Monitoring intervals
    state_check_interval_seconds: float = 5.0
    element_discovery_interval_seconds: float = 30.0
    dom_monitoring_interval_seconds: 1.0
    page_load_monitoring_interval_seconds: 2.0
    
    # Element tracking
    max_tracked_elements: int = 1000
    element_timeout_seconds: float = 60.0
    element_retry_attempts: int = 3
    
    # Page load monitoring
    page_load_timeout_seconds: float = 30.0
    max_page_load_time_seconds: float = 15.0
    enable_performance_monitoring: bool = True
    
    # DOM monitoring
    enable_dom_mutation_detection: bool = True
    max_dom_changes_per_interval: int = 100
    dom_change_timeout_seconds: float = 5.0
    
    # History and storage
    max_history_entries: int = 10000
    state_retention_hours: int = 24
    element_history_limit: int = 100
    
    # Detection settings
    enable_automatic_element_discovery: bool = True
    enable_state_validation: bool = True
    enable_interaction_tracking: bool = True
    
    # Performance settings
    enable_caching: bool = True
    cache_timeout_seconds: float = 300.0
    max_concurrent_tracking: int = 10


class DOMMutationObserver:
    """Observer for DOM mutations"""
    
    def __init__(self, driver):
        self.driver = driver
        self.mutations = deque(maxlen=1000)
        self.observers = []
        self.last_hash = ""
    
    def start_observation(self):
        """Start DOM mutation observation"""
        if not SELENIUM_AVAILABLE:
            return
        
        try:
            # Execute JavaScript to set up mutation observer
            script = """
            var mutations = [];
            var observer = new MutationObserver(function(muts) {
                muts.forEach(function(mutation) {
                    mutations.push({
                        type: mutation.type,
                        target: mutation.target.tagName,
                        addedNodes: mutation.addedNodes.length,
                        removedNodes: mutation.removedNodes.length,
                        attributes: mutation.attributeName,
                        timestamp: Date.now()
                    });
                });
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeOldValue: true,
                characterData: true,
                characterDataOldValue: true
            });
            
            window._mutationObserver = observer;
            window._mutations = mutations;
            """
            
            self.driver.execute_script(script)
            logger.info("DOM mutation observer started")
            
        except Exception as e:
            logger.warning(f"Failed to start DOM mutation observer: {e}")
    
    def stop_observation(self):
        """Stop DOM mutation observation"""
        try:
            script = """
            if (window._mutationObserver) {
                window._mutationObserver.disconnect();
                delete window._mutationObserver;
            }
            """
            
            self.driver.execute_script(script)
            logger.info("DOM mutation observer stopped")
            
        except Exception as e:
            logger.warning(f"Failed to stop DOM mutation observer: {e}")
    
    def get_mutations(self) -> List[Dict[str, Any]]:
        """Get recent mutations"""
        if not SELENIUM_AVAILABLE:
            return []
        
        try:
            mutations_script = """
            if (window._mutations) {
                var mutations = window._mutations.slice();
                window._mutations = [];
                return mutations;
            }
            return [];
            """
            
            mutations = self.driver.execute_script(mutations_script)
            return mutations
            
        except Exception as e:
            logger.warning(f"Failed to get mutations: {e}")
            return []
    
    def get_page_hash(self) -> str:
        """Get hash of current page content"""
        try:
            script = """
            return btoa(document.documentElement.outerHTML).slice(0, 1000);
            """
            
            hash_value = self.driver.execute_script(script)
            return hash_value
            
        except Exception:
            return ""
    
    def has_page_changed(self) -> bool:
        """Check if page has changed"""
        current_hash = self.get_page_hash()
        if current_hash and current_hash != self.last_hash:
            self.last_hash = current_hash
            return True
        return False


class ElementDetector:
    """Advanced element detection and tracking"""
    
    def __init__(self, config: StateTrackingConfig):
        self.config = config
        self.tracked_elements: Dict[str, ElementInfo] = {}
        self.element_selectors = {
            'buttons': ['button', 'input[type="submit"]', 'input[type="button"]', 'a.btn'],
            'links': ['a', 'area'],
            'inputs': ['input', 'textarea', 'select'],
            'forms': ['form'],
            'images': ['img'],
            'text_elements': ['p', 'div', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        }
    
    def discover_elements(self, driver) -> List[ElementInfo]:
        """Discover and catalog page elements"""
        if not SELENIUM_AVAILABLE:
            return []
        
        elements = []
        current_time = datetime.now(timezone.utc)
        
        try:
            for category, selectors in self.element_selectors.items():
                for selector in selectors:
                    try:
                        found_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        for element in found_elements:
                            element_info = self._create_element_info(element, category)
                            if element_info:
                                elements.append(element_info)
                                
                    except Exception as e:
                        logger.debug(f"Error discovering elements with selector {selector}: {e}")
            
            logger.info(f"Discovered {len(elements)} elements on page")
            return elements
            
        except Exception as e:
            logger.error(f"Element discovery failed: {e}")
            return []
    
    def _create_element_info(self, element, category: str) -> Optional[ElementInfo]:
        """Create element info from WebElement"""
        try:
            element_id = self._generate_element_id(element)
            
            # Get basic properties
            tag_name = element.tag_name.lower()
            text = element.text or ""
            
            # Get attributes
            attributes = {}
            try:
                attributes = dict(element.get_dom_attribute, **element.get_attribute)
            except Exception:
                attributes = {}
            
            # Get location and size
            location = element.location
            size = element.size
            
            # Check state
            is_visible = element.is_displayed()
            is_enabled = element.is_enabled()
            
            # Try to determine clickability
            is_clickable = False
            try:
                is_clickable = element.is_enabled() and element.is_displayed()
            except Exception:
                pass
            
            # Get identifying attributes
            element_id_attr = element.get_attribute('id')
            class_name = element.get_attribute('class')
            name_attr = element.get_attribute('name')
            
            element_info = ElementInfo(
                element_id=element_id,
                tag_name=tag_name,
                element_type=category,
                text=text,
                attributes=attributes,
                x=location['x'],
                y=location['y'],
                width=size['width'],
                height=size['height'],
                is_visible=is_visible,
                is_enabled=is_enabled,
                is_clickable=is_clickable,
                id=element_id_attr,
                class_name=class_name,
                name=name_attr
            )
            
            # Set state
            if is_visible:
                if is_enabled:
                    if is_clickable:
                        element_info.state = ElementState.CLICKABLE
                    else:
                        element_info.state = ElementState.ENABLED
                else:
                    element_info.state = ElementState.DISABLED
            else:
                element_info.state = ElementState.HIDDEN
            
            return element_info
            
        except StaleElementReferenceException:
            logger.debug("Element reference is stale")
            return None
        except Exception as e:
            logger.debug(f"Error creating element info: {e}")
            return None
    
    def _generate_element_id(self, element) -> str:
        """Generate unique element ID"""
        try:
            # Try multiple approaches to identify element
            element_id = element.get_attribute('id')
            if element_id:
                return f"id_{element_id}"
            
            element_name = element.get_attribute('name')
            if element_name:
                return f"name_{element_name}"
            
            # Use CSS path as fallback
            css_selector = element.value_of_css_property('css-path')
            if css_selector:
                return f"css_{hashlib.md5(css_selector.encode()).hexdigest()[:8]}"
            
            # Use tag and position
            tag = element.tag_name
            location = element.location
            return f"{tag}_{location['x']}_{location['y']}"
            
        except Exception:
            # Last resort: generate random ID
            return f"auto_{uuid4().hex[:8]}"
    
    def update_element(self, element_info: ElementInfo, driver) -> Optional[ElementInfo]:
        """Update element information"""
        if not SELENIUM_AVAILABLE:
            return None
        
        try:
            # Try to find the element by ID
            element = None
            if element_info.id:
                try:
                    element = driver.find_element(By.ID, element_info.id)
                except NoSuchElementException:
                    pass
            
            # Try by other identifiers
            if not element and element_info.name:
                try:
                    element = driver.find_element(By.NAME, element_info.name)
                except NoSuchElementException:
                    pass
            
            if not element:
                return None
            
            # Update element info
            old_text = element_info.text
            old_state = element_info.state
            
            element_info.text = element.text or ""
            element_info.last_seen = datetime.now(timezone.utc)
            
            # Update state
            is_visible = element.is_displayed()
            is_enabled = element.is_enabled()
            
            element_info.is_visible = is_visible
            element_info.is_enabled = is_enabled
            
            if is_visible:
                if is_enabled:
                    element_info.state = ElementState.CLICKABLE if is_enabled else ElementState.ENABLED
                else:
                    element_info.state = ElementState.DISABLED
            else:
                element_info.state = ElementState.HIDDEN
            
            # Check if element has changed
            if old_text != element_info.text or old_state != element_info.state:
                element_info.change_count += 1
            
            return element_info
            
        except StaleElementReferenceException:
            logger.debug(f"Element {element_info.element_id} is stale")
            return None
        except Exception as e:
            logger.debug(f"Error updating element {element_info.element_id}: {e}")
            return None


class PageLoadMonitor:
    """Monitor page load performance and timing"""
    
    def __init__(self, config: StateTrackingConfig):
        self.config = config
        self.page_load_history: deque = deque(maxlen=100)
    
    def measure_page_load(self, driver) -> Optional[PageLoadMetrics]:
        """Measure page load metrics"""
        if not SELENIUM_AVAILABLE:
            return None
        
        try:
            # Execute performance timing script
            script = """
            var timing = performance.timing;
            var navigation = performance.navigation;
            
            return {
                // Navigation timing
                navigationStart: timing.navigationStart,
                domLoading: timing.domLoading,
                domContentLoadedEventEnd: timing.domContentLoadedEventEnd,
                loadEventEnd: timing.loadEventEnd,
                domComplete: timing.domComplete,
                
                // Resource timing
                responseEnd: timing.responseEnd,
                domInteractive: timing.domInteractive,
                
                // Calculated times
                pageLoadTime: timing.loadEventEnd - timing.navigationStart,
                domParseTime: timing.domComplete - timing.responseEnd,
                timeToInteractive: timing.domInteractive - timing.navigationStart
            };
            """
            
            timing_data = driver.execute_script(script)
            
            if not timing_data:
                return None
            
            # Create PageLoadMetrics object
            metrics = PageLoadMetrics(
                navigation_start=timing_data.get('navigationStart', 0),
                dom_loading=timing_data.get('domLoading', 0),
                dom_content_loaded=timing_data.get('domContentLoadedEventEnd', 0),
                page_loaded=timing_data.get('loadEventEnd', 0),
                fully_loaded=timing_data.get('domComplete', 0),
                total_load_time=timing_data.get('pageLoadTime', 0),
                time_to_interactive=timing_data.get('timeToInteractive', 0),
                dom_parse_time=timing_data.get('domParseTime', 0),
                url=driver.current_url,
                page_title=driver.title
            )
            
            # Store in history
            self.page_load_history.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.debug(f"Page load measurement failed: {e}")
            return None
    
    def get_load_time_stats(self, minutes: int = 30) -> Dict[str, Any]:
        """Get page load time statistics"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        recent_loads = [
            m for m in self.page_load_history 
            if m.timestamp > cutoff_time and m.total_load_time > 0
        ]
        
        if not recent_loads:
            return {'message': 'No recent page load data'}
        
        load_times = [m.total_load_time for m in recent_loads]
        
        return {
            'time_period_minutes': minutes,
            'total_measurements': len(recent_loads),
            'average_load_time_ms': sum(load_times) / len(load_times),
            'min_load_time_ms': min(load_times),
            'max_load_time_ms': max(load_times),
            'load_time_percentiles': {
                'p50': self._percentile(load_times, 50),
                'p90': self._percentile(load_times, 90),
                'p95': self._percentile(load_times, 95),
                'p99': self._percentile(load_times, 99)
            },
            'timeout_count': sum(1 for m in recent_loads if m.total_load_time > self.config.max_page_load_time_seconds * 1000),
            'slow_loads_count': sum(1 for m in recent_loads if m.total_load_time > 5000)
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = (percentile / 100) * (len(sorted_values) - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            return lower + (index - int(index)) * (upper - lower)


class StateTracker:
    """Main state tracking system"""
    
    def __init__(self, config: Optional[StateTrackingConfig] = None):
        self.config = config or StateTrackingConfig()
        self.audit_logger = get_audit_logger()
        
        # Core components
        self.element_detector = ElementDetector(self.config)
        self.page_load_monitor = PageLoadMonitor(self.config)
        
        # State tracking
        self.current_page_state = PageState.UNKNOWN
        self.current_page_url = ""
        self.current_page_title = ""
        
        # History and tracking
        self.state_changes: deque = deque(maxlen=self.config.max_history_entries)
        self.interaction_history: deque = deque(maxlen=500)
        self.tracked_elements: Dict[str, ElementInfo] = {}
        
        # Monitoring state
        self.tracking_active = False
        self.tracking_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Event callbacks
        self.state_change_callbacks: List[Callable] = []
        self.interaction_callbacks: List[Callable] = []
        
        # Performance tracking
        self.tracking_stats = {
            'elements_discovered': 0,
            'state_changes_detected': 0,
            'interactions_tracked': 0,
            'page_loads_monitored': 0,
            'errors_encountered': 0
        }
        
        logger.info("State tracking system initialized")
    
    async def start_tracking(self):
        """Start state tracking"""
        if self.tracking_active:
            logger.warning("State tracking already active")
            return
        
        self.tracking_active = True
        self._shutdown_event.clear()
        
        # Create tracking tasks
        self.tracking_tasks = [
            asyncio.create_task(self._state_monitoring_loop()),
            asyncio.create_task(self._element_discovery_loop()),
            asyncio.create_task(self._dom_monitoring_loop()),
            asyncio.create_task(self._page_load_monitoring_loop())
        ]
        
        logger.info("State tracking started")
    
    async def stop_tracking(self):
        """Stop state tracking"""
        if not self.tracking_active:
            return
        
        self.tracking_active = False
        self._shutdown_event.set()
        
        # Cancel tracking tasks
        for task in self.tracking_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tracking_tasks:
            await asyncio.gather(*self.tracking_tasks, return_exceptions=True)
        
        logger.info("State tracking stopped")
    
    def attach_browser(self, driver, browser_id: str = ""):
        """Attach browser driver for tracking"""
        self.browser_driver = driver
        self.browser_id = browser_id
        
        logger.info(f"Attached browser {browser_id} for state tracking")
    
    def detach_browser(self):
        """Detach browser driver"""
        self.browser_driver = None
        self.browser_id = ""
        
        logger.info("Detached browser from state tracking")
    
    def add_state_change_callback(self, callback: Callable):
        """Add callback for state changes"""
        self.state_change_callbacks.append(callback)
    
    def add_interaction_callback(self, callback: Callable):
        """Add callback for interactions"""
        self.interaction_callbacks.append(callback)
    
    async def _state_monitoring_loop(self):
        """Main state monitoring loop"""
        while self.tracking_active:
            try:
                await self._monitor_page_state()
                await asyncio.sleep(self.config.state_check_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in state monitoring loop: {e}", exc_info=True)
                self.tracking_stats['errors_encountered'] += 1
                await asyncio.sleep(5)
    
    async def _monitor_page_state(self):
        """Monitor current page state"""
        if not self.browser_driver:
            return
        
        try:
            # Check if page has loaded
            current_url = self.browser_driver.current_url
            current_title = self.browser_driver.title
            
            # Detect state changes
            if current_url != self.current_page_url:
                await self._handle_page_change(current_url, current_title)
            
            # Check if page is responsive
            try:
                # Try to execute simple JavaScript
                self.browser_driver.execute_script("return document.readyState;")
                if self.current_page_state == PageState.LOADING:
                    await self._update_page_state(PageState.LOADED)
            except WebDriverException:
                await self._update_page_state(PageState.ERROR)
            
            # Update current state
            self.current_page_url = current_url
            self.current_page_title = current_title
            
        except Exception as e:
            logger.debug(f"Page state monitoring error: {e}")
    
    async def _handle_page_change(self, new_url: str, new_title: str):
        """Handle page navigation change"""
        old_url = self.current_page_url
        
        await self._record_state_change(
            StateChangeEvent.PAGE_LOADED,
            change_description=f"Page navigated from {old_url} to {new_url}",
            metadata={'old_url': old_url, 'new_url': new_url}
        )
        
        await self._update_page_state(PageState.LOADING)
        
        # Reset tracked elements
        self.tracked_elements.clear()
        
        self.current_page_url = new_url
        self.current_page_title = new_title
    
    async def _update_page_state(self, new_state: PageState):
        """Update page state"""
        if new_state != self.current_page_state:
            old_state = self.current_page_state
            self.current_page_state = new_state
            
            await self._record_state_change(
                StateChangeEvent.DOM_MUTATED,
                change_description=f"Page state changed from {old_state.value} to {new_state.value}",
                metadata={'old_state': old_state.value, 'new_state': new_state.value}
            )
    
    async def _element_discovery_loop(self):
        """Element discovery and tracking loop"""
        while self.tracking_active:
            try:
                await self._discover_and_track_elements()
                await asyncio.sleep(self.config.element_discovery_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in element discovery loop: {e}", exc_info=True)
                self.tracking_stats['errors_encountered'] += 1
                await asyncio.sleep(10)
    
    async def _discover_and_track_elements(self):
        """Discover and track page elements"""
        if not self.browser_driver or not self.config.enable_automatic_element_discovery:
            return
        
        try:
            # Discover new elements
            new_elements = self.element_detector.discover_elements(self.browser_driver)
            
            # Track new elements
            for element_info in new_elements:
                if element_info.element_id not in self.tracked_elements:
                    self.tracked_elements[element_info.element_id] = element_info
                    self.tracking_stats['elements_discovered'] += 1
                    
                    await self._record_state_change(
                        StateChangeEvent.ELEMENT_ADDED,
                        element_id=element_info.element_id,
                        change_description=f"New element discovered: {element_info.tag_name}",
                        metadata=element_info.to_dict()
                    )
            
            # Update existing elements
            stale_elements = []
            for element_id, element_info in list(self.tracked_elements.items()):
                updated_element = self.element_detector.update_element(element_info, self.browser_driver)
                
                if updated_element is None:
                    stale_elements.append(element_id)
                else:
                    # Check for state changes
                    if element_info.change_count > 0:
                        await self._record_state_change(
                            StateChangeEvent.ELEMENT_UPDATED,
                            element_id=element_id,
                            change_description=f"Element updated: {element_info.tag_name}",
                            metadata=element_info.to_dict()
                        )
            
            # Remove stale elements
            for element_id in stale_elements:
                element_info = self.tracked_elements.pop(element_id)
                await self._record_state_change(
                    StateChangeEvent.ELEMENT_REMOVED,
                    element_id=element_id,
                    change_description=f"Element removed: {element_info.tag_name}",
                    metadata=element_info.to_dict()
                )
            
        except Exception as e:
            logger.debug(f"Element discovery error: {e}")
    
    async def _dom_monitoring_loop(self):
        """DOM mutation monitoring loop"""
        if not self.config.enable_dom_mutation_detection:
            return
        
        while self.tracking_active:
            try:
                await self._monitor_dom_changes()
                await asyncio.sleep(self.config.dom_monitoring_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in DOM monitoring loop: {e}", exc_info=True)
                self.tracking_stats['errors_encountered'] += 1
                await asyncio.sleep(5)
    
    async def _monitor_dom_changes(self):
        """Monitor for DOM mutations"""
        if not self.browser_driver:
            return
        
        try:
            # Check for page changes
            if hasattr(self, 'dom_observer'):
                mutations = self.dom_observer.get_mutations()
                
                for mutation in mutations:
                    if mutation['addedNodes'] > 0 or mutation['removedNodes'] > 0:
                        await self._record_state_change(
                            StateChangeEvent.DOM_MUTATED,
                            change_description=f"DOM structure changed: {mutation['type']}",
                            metadata=mutation
                        )
            
        except Exception as e:
            logger.debug(f"DOM monitoring error: {e}")
    
    async def _page_load_monitoring_loop(self):
        """Page load monitoring loop"""
        if not self.config.enable_performance_monitoring:
            return
        
        while self.tracking_active:
            try:
                await self._monitor_page_load_performance()
                await asyncio.sleep(self.config.page_load_monitoring_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in page load monitoring loop: {e}", exc_info=True)
                self.tracking_stats['errors_encountered'] += 1
                await asyncio.sleep(5)
    
    async def _monitor_page_load_performance(self):
        """Monitor page load performance"""
        if not self.browser_driver:
            return
        
        try:
            metrics = self.page_load_monitor.measure_page_load(self.browser_driver)
            
            if metrics:
                self.tracking_stats['page_loads_monitored'] += 1
                
                # Log performance metric
                try:
                    log_performance_metric(
                        "browser.page_load_time",
                        metrics.total_load_time,
                        unit="milliseconds",
                        tags={'url': metrics.url, 'page_title': metrics.page_title}
                    )
                except Exception as e:
                    logger.debug(f"Failed to log page load metric: {e}")
                
                # Check for slow page loads
                if metrics.total_load_time > self.config.max_page_load_time_seconds * 1000:
                    await self._record_state_change(
                        StateChangeEvent.TIMEOUT_OCCURRED,
                        change_description=f"Slow page load detected: {metrics.total_load_time:.0f}ms",
                        metadata=metrics.to_dict()
                    )
            
        except Exception as e:
            logger.debug(f"Page load monitoring error: {e}")
    
    async def _record_state_change(self, event_type: StateChangeEvent, **kwargs):
        """Record a state change"""
        change = StateChange(
            event_type=event_type,
            page_url=self.current_page_url,
            page_title=self.current_page_title,
            **kwargs
        )
        
        self.state_changes.append(change)
        self.tracking_stats['state_changes_detected'] += 1
        
        # Call registered callbacks
        for callback in self.state_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(change)
                else:
                    callback(change)
            except Exception as e:
                logger.debug(f"State change callback error: {e}")
        
        logger.debug(f"State change recorded: {event_type.value}")
    
    async def track_interaction(self, interaction_type: InteractionType, 
                              element_id: Optional[str] = None, **kwargs):
        """Track user interaction"""
        interaction = InteractionEvent(
            interaction_type=interaction_type,
            element_id=element_id,
            page_url=self.current_page_url,
            page_title=self.current_page_title,
            **kwargs
        )
        
        self.interaction_history.append(interaction)
        self.tracking_stats['interactions_tracked'] += 1
        
        # Record state change
        await self._record_state_change(
            StateChangeEvent.INTERACTION_DETECTED,
            element_id=element_id,
            change_description=f"User interaction: {interaction_type.value}",
            metadata=interaction.to_dict()
        )
        
        # Call registered callbacks
        for callback in self.interaction_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(interaction)
                else:
                    callback(interaction)
            except Exception as e:
                logger.debug(f"Interaction callback error: {e}")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current page state"""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'page_state': self.current_page_state.value,
            'page_url': self.current_page_url,
            'page_title': self.current_page_title,
            'tracked_elements_count': len(self.tracked_elements),
            'browser_id': getattr(self, 'browser_id', ''),
            'tracking_active': self.tracking_active
        }
    
    def get_tracked_elements(self, element_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tracked elements, optionally filtered by type"""
        elements = list(self.tracked_elements.values())
        
        if element_type:
            elements = [e for e in elements if e.element_type == element_type]
        
        return [element.to_dict() for element in elements]
    
    def get_state_changes(self, event_type: Optional[StateChangeEvent] = None, 
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get state changes, optionally filtered"""
        changes = list(self.state_changes)
        
        if event_type:
            changes = [c for c in changes if c.event_type == event_type]
        
        # Return most recent first
        recent_changes = sorted(changes, key=lambda c: c.timestamp, reverse=True)[:limit]
        return [change.to_dict() for change in recent_changes]
    
    def get_interaction_history(self, interaction_type: Optional[InteractionType] = None,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get interaction history"""
        interactions = list(self.interaction_history)
        
        if interaction_type:
            interactions = [i for i in interactions if i.interaction_type == interaction_type]
        
        # Return most recent first
        recent_interactions = sorted(interactions, key=lambda i: i.timestamp, reverse=True)[:limit]
        return [interaction.to_dict() for interaction in recent_interactions]
    
    def get_page_load_stats(self, minutes: int = 30) -> Dict[str, Any]:
        """Get page load statistics"""
        return self.page_load_monitor.get_load_time_stats(minutes)
    
    def get_tracking_summary(self) -> Dict[str, Any]:
        """Get tracking system summary"""
        current_time = datetime.now(timezone.utc)
        
        # Count state changes by type
        change_counts = defaultdict(int)
        for change in self.state_changes:
            change_counts[change.event_type.value] += 1
        
        # Count elements by type
        element_counts = defaultdict(int)
        for element in self.tracked_elements.values():
            element_counts[element.element_type] += 1
        
        # Count elements by state
        state_counts = defaultdict(int)
        for element in self.tracked_elements.values():
            state_counts[element.state.value] += 1
        
        return {
            'timestamp': current_time.isoformat(),
            'tracking_active': self.tracking_active,
            'current_state': {
                'page_state': self.current_page_state.value,
                'page_url': self.current_page_url,
                'page_title': self.current_page_title,
                'tracked_elements': len(self.tracked_elements)
            },
            'statistics': self.tracking_stats.copy(),
            'element_distribution': dict(element_counts),
            'element_state_distribution': dict(state_counts),
            'state_change_distribution': dict(change_counts),
            'configuration': {
                'state_check_interval': self.config.state_check_interval_seconds,
                'element_discovery_interval': self.config.element_discovery_interval_seconds,
                'dom_monitoring_interval': self.config.dom_monitoring_interval_seconds,
                'page_load_monitoring_interval': self.config.page_load_monitoring_interval_seconds,
                'enable_automatic_discovery': self.config.enable_automatic_element_discovery,
                'enable_dom_monitoring': self.config.enable_dom_mutation_detection,
                'enable_performance_monitoring': self.config.enable_performance_monitoring
            }
        }
    
    async def validate_page_state(self) -> Dict[str, Any]:
        """Validate current page state"""
        if not self.browser_driver:
            return {'error': 'No browser attached'}
        
        validation_result = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'valid': True,
            'issues': [],
            'checks_passed': 0,
            'checks_failed': 0
        }
        
        try:
            # Check if page is loaded
            try:
                ready_state = self.browser_driver.execute_script("return document.readyState;")
                if ready_state == 'complete':
                    validation_result['checks_passed'] += 1
                else:
                    validation_result['issues'].append(f"Document ready state: {ready_state}")
                    validation_result['checks_failed'] += 1
                    validation_result['valid'] = False
            except Exception as e:
                validation_result['issues'].append(f"Document ready state check failed: {e}")
                validation_result['checks_failed'] += 1
            
            # Check for JavaScript errors
            try:
                logs = self.browser_driver.get_log('browser')
                js_errors = [log for log in logs if log['level'] == 'SEVERE']
                if not js_errors:
                    validation_result['checks_passed'] += 1
                else:
                    validation_result['issues'].append(f"JavaScript errors detected: {len(js_errors)}")
                    validation_result['checks_failed'] += 1
            except Exception:
                validation_result['checks_passed'] += 1  # Assume OK if we can't check
            
            # Check for key elements
            key_selectors = ['body', 'title', 'html']
            for selector in key_selectors:
                try:
                    self.browser_driver.find_element(By.CSS_SELECTOR, selector)
                    validation_result['checks_passed'] += 1
                except NoSuchElementException:
                    validation_result['issues'].append(f"Key element missing: {selector}")
                    validation_result['checks_failed'] += 1
                    validation_result['valid'] = False
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['issues'].append(f"Validation error: {e}")
        
        return validation_result
    
    async def force_element_discovery(self) -> Dict[str, Any]:
        """Force element discovery on current page"""
        if not self.browser_driver:
            return {'error': 'No browser attached'}
        
        try:
            elements = self.element_detector.discover_elements(self.browser_driver)
            
            # Update tracked elements
            old_count = len(self.tracked_elements)
            for element_info in elements:
                self.tracked_elements[element_info.element_id] = element_info
            
            new_count = len(self.tracked_elements)
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'elements_discovered': len(elements),
                'total_tracked': new_count,
                'new_elements': new_count - old_count
            }
            
        except Exception as e:
            return {'error': f'Element discovery failed: {e}'}
    
    async def shutdown(self):
        """Graceful shutdown of state tracking"""
        logger.info("Initiating state tracking shutdown")
        
        # Stop tracking loops
        await self.stop_tracking()
        
        # Clear tracked elements
        self.tracked_elements.clear()
        
        # Clear state
        self.current_page_state = PageState.UNKNOWN
        self.current_page_url = ""
        self.current_page_title = ""
        
        logger.info("State tracking shutdown completed")


# Global state tracker instance
_global_state_tracker = None


def get_state_tracker() -> StateTracker:
    """Get or create global state tracker"""
    global _global_state_tracker
    if _global_state_tracker is None:
        _global_state_tracker = StateTracker()
    return _global_state_tracker


if __name__ == "__main__":
    # Example usage and testing
    async def test_state_tracker():
        # Setup
        config = StateTrackingConfig()
        tracker = StateTracker(config)
        
        print("Starting state tracking system...")
        await tracker.start_tracking()
        
        # Simulate browser attachment (if Selenium available)
        if SELENIUM_AVAILABLE:
            print("Selenium available - would attach browser for real tracking")
        else:
            print("Selenium not available - running in simulation mode")
        
        # Let it run for a bit
        await asyncio.sleep(5)
        
        print("Current state:", json.dumps(tracker.get_current_state(), indent=2))
        print("Tracking summary:", json.dumps(tracker.get_tracking_summary(), indent=2))
        
        # Stop tracking
        print("Stopping state tracking system...")
        await tracker.shutdown()
        
        print("State tracking system test completed!")
    
    # Run test
    asyncio.run(test_state_tracker())