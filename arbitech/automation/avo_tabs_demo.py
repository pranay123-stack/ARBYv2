"""
AVO Tabs Integration Demo - Comprehensive demonstration of the complete system
Shows how all components work together for seamless tab management and coordination.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Import AVO Tabs components
from avo_tabs_interface import (
    AVOTabManager, TabType, TabState
)
from avo_validator import (
    AVOValidator, ValidationSeverity, ValidationResult
)
from tab_coordinator import (
    TabCoordinator, BookmakerProfile, TabPriority, CoordinationStrategy
)
from avo_extension_handler import (
    AVOExtensionHandler, ExtensionConfiguration
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AVOTabsDemo:
    """Comprehensive demo of AVO Tabs system integration"""
    
    def __init__(self):
        # Initialize components
        self.tab_manager = AVOTabManager(max_tabs=20, sync_interval=0.5)
        self.validator = AVOValidator(self.tab_manager)
        self.coordinator = TabCoordinator(self.tab_manager, CoordinationStrategy.HEALTH_AWARE)
        
        # Initialize extension handler with demo configuration
        extension_config = ExtensionConfiguration(
            extension_id="demo_avo_extension",
            extension_name="AVO Tabs Demo Extension",
            version="1.0",
            websocket_url="ws://localhost:8765",  # Demo WebSocket URL
            api_endpoint="http://localhost:8765",
            authentication_token=None,
            enabled_features=[
                "tab_management",
                "demo_functionality", 
                "performance_monitoring"
            ],
            permissions=["tabs", "scripting"]
        )
        
        self.extension_handler = AVOExtensionHandler(extension_config)
        
        # Register event handlers
        self._register_event_handlers()
        
        logger.info("AVO Tabs Demo initialized")
    
    def _register_event_handlers(self):
        """Register comprehensive event handlers"""
        
        # Tab manager events
        self.tab_manager.register_event_handler('tab_created', self._handle_tab_created)
        self.tab_manager.register_event_handler('tab_closed', self._handle_tab_closed)
        self.tab_manager.register_event_handler('tab_state_changed', self._handle_tab_state_changed)
        self.tab_manager.register_event_handler('tab_error', self._handle_tab_error)
        self.tab_manager.register_event_handler('tab_health_changed', self._handle_tab_health_changed)
        
        # Coordinator events
        self.coordinator.register_event_handler('TAB_ASSIGNED', self._handle_tab_assigned)
        self.coordinator.register_event_handler('TAB_RELEASED', self._handle_tab_released)
        self.coordinator.register_event_handler('LOAD_BALANCED', self._handle_load_balanced)
        self.coordinator.register_event_handler('HEALTH_CHECK', self._handle_health_check)
        
        # Extension handler events
        self.extension_handler.register_event_handler('tab_event', self._handle_extension_tab_event)
        self.extension_handler.register_event_handler('error_event', self._handle_extension_error)
        
        logger.info("Event handlers registered")
    
    # Event handlers
    async def _handle_tab_created(self, event_data: Dict[str, Any]):
        """Handle tab created event"""
        tab_info = event_data.get('tab_info', {})
        logger.info(f"📋 Tab created: ID {tab_info.get('tab_id')} - {tab_info.get('tab_type')} - {tab_info.get('url')}")
    
    async def _handle_tab_closed(self, event_data: Dict[str, Any]):
        """Handle tab closed event"""
        tab_id = event_data.get('tab_id')
        logger.info(f"🔒 Tab closed: ID {tab_id}")
    
    async def _handle_tab_state_changed(self, event_data: Dict[str, Any]):
        """Handle tab state change event"""
        tab_id = event_data.get('tab_id')
        old_state = event_data.get('old_state')
        new_state = event_data.get('new_state')
        logger.debug(f"⚡ Tab {tab_id} state: {old_state} → {new_state}")
    
    async def _handle_tab_error(self, event_data: Dict[str, Any]):
        """Handle tab error event"""
        tab_id = event_data.get('tab_id')
        error_info = event_data.get('error_info', {})
        logger.error(f"❌ Tab {tab_id} error: {error_info}")
    
    async def _handle_tab_health_changed(self, event_data: Dict[str, Any]):
        """Handle tab health change event"""
        tab_id = event_data.get('tab_id')
        old_health = event_data.get('old_health')
        new_health = event_data.get('new_health')
        if abs(new_health - old_health) > 0.1:  # Only log significant changes
            logger.info(f"💚 Tab {tab_id} health: {old_health:.2f} → {new_health:.2f}")
    
    async def _handle_tab_assigned(self, event_data: Dict[str, Any]):
        """Handle tab assignment event"""
        assignment_info = (
            f"Tab {event_data.get('tab_id')} assigned to {event_data.get('bookmaker_id')}"
            f" for {event_data.get('task_type')}"
        )
        logger.info(f"🎯 {assignment_info}")
    
    async def _handle_tab_released(self, event_data: Dict[str, Any]):
        """Handle tab release event"""
        success = event_data.get('success')
        response_time = event_data.get('response_time', 0)
        status = "✅ Success" if success else "❌ Failed"
        logger.info(f"🔄 Tab {event_data.get('tab_id')} released: {status} ({response_time:.2f}s)")
    
    async def _handle_load_balanced(self, event_data: Dict[str, Any]):
        """Handle load balancing event"""
        from_bookmaker = event_data.get('from_bookmaker')
        to_bookmaker = event_data.get('to_bookmaker')
        logger.info(f"⚖️ Load balanced: {from_bookmaker} → {to_bookmaker}")
    
    async def _handle_health_check(self, event_data: Dict[str, Any]):
        """Handle health check event"""
        action = event_data.get('action')
        bookmaker_id = event_data.get('bookmaker_id')
        logger.debug(f"🏥 Health check: {bookmaker_id} - {action}")
    
    async def _handle_extension_tab_event(self, event_data: Dict[str, Any]):
        """Handle extension tab event"""
        event_type = event_data.get('event_type')
        logger.debug(f"🔌 Extension event: {event_type}")
    
    async def _handle_extension_error(self, event_data: Dict[str, Any]):
        """Handle extension error event"""
        error_type = event_data.get('error_type')
        error_message = event_data.get('error_message')
        logger.warning(f"⚠️ Extension error ({error_type}): {error_message}")
    
    async def run_comprehensive_demo(self):
        """Run the complete AVO Tabs system demo"""
        try:
            logger.info("🚀 Starting comprehensive AVO Tabs demo...")
            
            # Phase 1: Initialize system
            await self._demo_initialization()
            
            # Phase 2: Tab management operations
            await self._demo_tab_management()
            
            # Phase 3: Validation system
            await self._demo_validation_system()
            
            # Phase 4: Coordination system
            await self._demo_coordination_system()
            
            # Phase 5: Extension integration
            await self._demo_extension_integration()
            
            # Phase 6: System monitoring
            await self._demo_system_monitoring()
            
            # Phase 7: Error handling and recovery
            await self._demo_error_handling()
            
            logger.info("🎉 AVO Tabs demo completed successfully!")
            
        except Exception as e:
            logger.error(f"💥 Demo failed: {e}")
            raise
    
    async def _demo_initialization(self):
        """Phase 1: System initialization"""
        logger.info("\n" + "="*60)
        logger.info("📋 PHASE 1: SYSTEM INITIALIZATION")
        logger.info("="*60)
        
        # Start background services
        self.tab_manager.start_sync_processing()
        self.tab_manager.start_health_monitoring()
        self.coordinator.start_coordination()
        
        # Note: Extension handler requires actual extension to be running
        logger.info("✅ Tab manager started (sync + health monitoring)")
        logger.info("✅ Tab coordinator started")
        logger.info("⚠️ Extension handler requires WebSocket connection to extension")
        
        await asyncio.sleep(2)
    
    async def _demo_tab_management(self):
        """Phase 2: Tab management operations"""
        logger.info("\n" + "="*60)
        logger.info("🔧 PHASE 2: TAB MANAGEMENT OPERATIONS")
        logger.info("="*60)
        
        # Create various types of tabs
        demo_urls = [
            ("https://example-bet365.com", TabType.BOOKMAKER_PRIMARY, "bet365"),
            ("https://example-williamhill.com", TabType.BOOKMAKER_SECONDARY, "william_hill"),
            ("https://example-ladbrokes.com", TabType.BOOKMAKER_BACKUP, "ladbrokes"),
            ("https://example-oddschecker.com", TabType.ARBITRAGE_MONITOR, None),
            ("https://example-trading.com", TabType.TRADING_DASHBOARD, None)
        ]
        
        created_tabs = []
        
        for url, tab_type, bookmaker_id in demo_urls:
            try:
                tab_id = self.tab_manager.create_tab(
                    url=url,
                    tab_type=tab_type,
                    bookmaker_id=bookmaker_id,
                    metadata={"demo": True, "created_at": datetime.now().isoformat()}
                )
                
                if tab_id:
                    created_tabs.append((tab_id, url, tab_type, bookmaker_id))
                    # Update tab state to active (simulating successful loading)
                    self.tab_manager.update_tab_state(tab_id, TabState.ACTIVE)
                else:
                    logger.warning(f"Failed to create tab for {url}")
                    
            except Exception as e:
                logger.error(f"Error creating tab for {url}: {e}")
        
        logger.info(f"✅ Created {len(created_tabs)} tabs")
        
        # Demonstrate tab queries
        await self._demonstrate_tab_queries(created_tabs)
        
        # Demonstrate tab synchronization
        await self._demonstrate_tab_synchronization(created_tabs)
        
        await asyncio.sleep(3)
    
    async def _demonstrate_tab_queries(self, created_tabs: List):
        """Demonstrate various tab queries"""
        logger.info("\n🔍 Tab Queries Demo:")
        
        # Get all tabs by type
        bookmaker_tabs = self.tab_manager.get_tabs_by_type(TabType.BOOKMAKER_PRIMARY)
        logger.info(f"📊 Primary bookmaker tabs: {len(bookmaker_tabs)}")
        
        # Get tabs by bookmaker
        bet365_tabs = self.tab_manager.get_tabs_by_bookmaker("bet365")
        logger.info(f"🏆 Bet365 tabs: {len(bet365_tabs)}")
        
        # Get system status
        system_status = self.tab_manager.get_system_status()
        logger.info(f"📈 System status: {system_status['system_status']}")
        logger.info(f"📊 Tab stats: {system_status['tab_statistics']}")
    
    async def _demonstrate_tab_synchronization(self, created_tabs: List):
        """Demonstrate tab synchronization"""
        logger.info("\n🔄 Tab Synchronization Demo:")
        
        if len(created_tabs) < 2:
            logger.info("Not enough tabs for synchronization demo")
            return
        
        tab_id_1, url_1, _, _ = created_tabs[0]
        tab_id_2, url_2, _, _ = created_tabs[1]
        
        # Send synchronization messages
        message_id_1 = self.tab_manager.send_sync_message(
            source_tab_id=tab_id_1,
            target_tab_id=tab_id_2,
            message_type="state_sync",
            payload={"status": "active", "odds_data": {"home": 2.1, "away": 1.8}},
            priority=3
        )
        
        message_id_2 = self.tab_manager.send_sync_message(
            source_tab_id=tab_id_2,
            target_tab_id=tab_id_1,
            message_type="heartbeat",
            payload={"timestamp": datetime.now().isoformat()},
            priority=5
        )
        
        logger.info(f"📨 Sent sync messages: {message_id_1[:8]}, {message_id_2[:8]}")
        
        # Wait for message processing
        await asyncio.sleep(1)
    
    async def _demo_validation_system(self):
        """Phase 3: Validation system demonstration"""
        logger.info("\n" + "="*60)
        logger.info("✅ PHASE 3: VALIDATION SYSTEM")
        logger.info("="*60)
        
        # Run comprehensive validation
        logger.info("🔍 Running comprehensive validation...")
        validation_report = await self.validator.run_comprehensive_validation("full")
        
        # Display validation results
        logger.info(f"📊 Validation completed: {validation_report.overall_result.value}")
        logger.info(f"📈 Summary: {validation_report.summary}")
        
        # Show recommendations
        if validation_report.recommendations:
            logger.info("💡 Recommendations:")
            for rec in validation_report.recommendations[:5]:  # Show first 5
                logger.info(f"  • {rec}")
        
        # Test individual validation rules
        await self._demo_individual_validations()
        
        # Show validation statistics
        stats = self.validator.get_validation_statistics()
        logger.info(f"📊 Validation stats: {stats}")
        
        await asyncio.sleep(2)
    
    async def _demo_individual_validations(self):
        """Demonstrate individual validation checks"""
        logger.info("\n🔬 Individual Validation Checks:")
        
        # Test connection validation (simulated)
        try:
            connection_check = await self.validator.run_validation_check("tab_connection", tab_id=1, expected_url="https://example.com")
            logger.info(f"🔗 Connection check: {connection_check.result.value} - {connection_check.message}")
        except Exception as e:
            logger.warning(f"Connection validation skipped: {e}")
        
        # Test sync consistency
        sync_check = await self.validator.run_validation_check("sync_consistency")
        logger.info(f"🔄 Sync consistency: {sync_check.result.value} - {sync_check.message}")
        
        # Test system health
        health_check = await self.validator.run_validation_check("system_health")
        logger.info(f"💚 System health: {health_check.result.value} - {health_check.message}")
        
        # Test resource usage
        resource_check = await self.validator.run_validation_check("resource_usage")
        logger.info(f"📊 Resource usage: {resource_check.result.value} - {resource_check.message}")
    
    async def _demo_coordination_system(self):
        """Phase 4: Coordination system demonstration"""
        logger.info("\n" + "="*60)
        logger.info("🎯 PHASE 4: COORDINATION SYSTEM")
        logger.info("="*60)
        
        # Register demo bookmakers
        await self._register_demo_bookmakers()
        
        # Demonstrate tab assignments
        await self._demo_tab_assignments()
        
        # Demonstrate load balancing
        await self._demo_load_balancing()
        
        # Show coordination status
        coord_status = self.coordinator.get_coordination_status()
        logger.info(f"⚡ Coordination status: Active={coord_status['active']}")
        logger.info(f"📊 Active assignments: {coord_status['active_assignments']}")
        logger.info(f"👥 Total bookmakers: {coord_status['total_bookmakers']}")
        
        await asyncio.sleep(3)
    
    async def _register_demo_bookmakers(self):
        """Register demo bookmakers for coordination"""
        logger.info("📝 Registering demo bookmakers...")
        
        bookmakers = [
            BookmakerProfile(
                bookmaker_id="bet365",
                name="Bet365",
                base_url="https://example-bet365.com",
                supported_markets=["football", "tennis", "basketball"],
                max_concurrent_tabs=5,
                priority_weight=1.5,
                health_threshold=0.8,
                retry_policy={"max_retries": 3, "backoff_factor": 2.0},
                characteristics={"response_time": 0.5, "reliability": 0.95},
                created_at=datetime.now(),
                last_activity=datetime.now(),
                total_requests=100,
                successful_requests=95,
                failed_requests=5,
                average_response_time=0.8
            ),
            BookmakerProfile(
                bookmaker_id="william_hill", 
                name="William Hill",
                base_url="https://example-williamhill.com",
                supported_markets=["football", "tennis"],
                max_concurrent_tabs=3,
                priority_weight=1.2,
                health_threshold=0.75,
                retry_policy={"max_retries": 2, "backoff_factor": 1.5},
                characteristics={"response_time": 0.7, "reliability": 0.90},
                created_at=datetime.now(),
                last_activity=datetime.now(),
                total_requests=80,
                successful_requests=72,
                failed_requests=8,
                average_response_time=1.1
            ),
            BookmakerProfile(
                bookmaker_id="ladbrokes",
                name="Ladbrokes", 
                base_url="https://example-ladbrokes.com",
                supported_markets=["football", "tennis", "basketball"],
                max_concurrent_tabs=4,
                priority_weight=1.0,
                health_threshold=0.7,
                retry_policy={"max_retries": 3, "backoff_factor": 2.0},
                characteristics={"response_time": 0.9, "reliability": 0.88},
                created_at=datetime.now(),
                last_activity=datetime.now(),
                total_requests=60,
                successful_requests=53,
                failed_requests=7,
                average_response_time=1.3
            )
        ]
        
        for bookmaker in bookmakers:
            success = self.coordinator.register_bookmaker(bookmaker)
            if success:
                logger.info(f"✅ Registered {bookmaker.name} ({bookmaker.bookmaker_id})")
            else:
                logger.warning(f"❌ Failed to register {bookmaker.name}")
    
    async def _demo_tab_assignments(self):
        """Demonstrate tab assignments with different priorities"""
        logger.info("\n🎯 Tab Assignments Demo:")
        
        # Create assignments with different priorities
        assignments = [
            ("market_scan", TabPriority.HIGH, {"required_markets": ["football"]}),
            ("odds_comparison", TabPriority.NORMAL, {"required_markets": ["tennis"]}),
            ("arbitrage_check", TabPriority.LOW, {"estimated_duration": 30.0}),
            ("monitoring", TabPriority.BACKGROUND, {"continuous": True}),
            ("trading", TabPriority.CRITICAL, {"high_value": True})
        ]
        
        assignment_ids = []
        for task_type, priority, requirements in assignments:
            assignment_id = self.coordinator.assign_tab(task_type, priority, requirements)
            if assignment_id:
                assignment_ids.append(assignment_id)
                logger.info(f"📋 Assigned {task_type} ({priority.value}) - ID: {assignment_id[:8]}")
                
                # Simulate assignment completion after delay
                asyncio.create_task(self._simulate_assignment_completion(assignment_id))
            else:
                logger.warning(f"❌ Failed to assign {task_type}")
        
        # Wait for some assignments to complete
        await asyncio.sleep(5)
        
        return assignment_ids
    
    async def _simulate_assignment_completion(self, assignment_id: str):
        """Simulate assignment completion"""
        await asyncio.sleep(2)  # Simulate work time
        
        # Random success/failure for demo
        import random
        success = random.random() > 0.2  # 80% success rate
        response_time = random.uniform(0.5, 3.0)
        
        self.coordinator.release_tab(assignment_id, success, response_time)
    
    async def _demo_load_balancing(self):
        """Demonstrate load balancing capabilities"""
        logger.info("\n⚖️ Load Balancing Demo:")
        
        # Get current load distribution
        coord_status = self.coordinator.get_coordination_status()
        load_distribution = coord_status.get('load_distribution', {})
        
        for bookmaker_id, load in load_distribution.items():
            logger.info(f"📊 {bookmaker_id}: {load:.1f} active tabs")
        
        # Show performance scores
        performance_scores = coord_status.get('performance_scores', {})
        for bookmaker_id, score in performance_scores.items():
            logger.info(f"⭐ {bookmaker_id}: {score:.2f} performance score")
    
    async def _demo_extension_integration(self):
        """Phase 5: Extension integration demonstration"""
        logger.info("\n" + "="*60)
        logger.info("🔌 PHASE 5: EXTENSION INTEGRATION")
        logger.info("="*60)
        
        # Note: This requires actual extension WebSocket server
        logger.info("⚠️ Extension handler requires WebSocket connection to extension")
        logger.info("📋 Extension handler capabilities:")
        
        # Show extension configuration
        config = self.extension_handler.config
        logger.info(f"🔧 Extension ID: {config.extension_id}")
        logger.info(f"🔧 Extension Name: {config.extension_name}")
        logger.info(f"🔧 WebSocket URL: {config.websocket_url}")
        logger.info(f"🔧 Enabled Features: {config.enabled_features}")
        
        # Show connection status (will show disconnected in demo)
        conn_status = self.extension_handler.get_connection_status()
        logger.info(f"📡 Connection Status: {conn_status.get('connection_status', 'unknown')}")
        
        # Demonstrate what extension operations would look like
        logger.info("\n📝 Extension Operations Demo (simulated):")
        
        # These would require actual extension connection
        logger.info("  • create_tab() - Would create tab through extension")
        logger.info("  • close_tab() - Would close tab through extension") 
        logger.info("  • get_tab_info() - Would get tab info from extension")
        logger.info("  • send_message_to_tab() - Would send message to tab")
        
        # Health check
        health = self.extension_handler.perform_health_check()
        logger.info(f"💚 Extension health: {health.get('healthy', False)}")
        
        await asyncio.sleep(2)
    
    async def _demo_system_monitoring(self):
        """Phase 6: System monitoring demonstration"""
        logger.info("\n" + "="*60)
        logger.info("📊 PHASE 6: SYSTEM MONITORING")
        logger.info("="*60)
        
        # Get comprehensive system status
        logger.info("🔍 Comprehensive System Status:")
        
        # Tab manager status
        tab_status = self.tab_manager.get_system_status()
        logger.info(f"📊 Tab Manager: {tab_status['system_status']}")
        logger.info(f"  • Total tabs: {tab_status['tab_statistics']['total_tabs']}")
        logger.info(f"  • Active tabs: {tab_status['tab_statistics']['active_tabs']}")
        logger.info(f"  • Average health: {tab_status['metrics']['average_health_score']:.2f}")
        
        # Validator status
        validator_stats = self.validator.get_validation_statistics()
        logger.info(f"📊 Validator: {validator_stats.get('active_rules', 0)} active rules")
        logger.info(f"  • Success rate: {validator_stats.get('recent_success_rate', 0):.2%}")
        logger.info(f"  • Average execution time: {validator_stats.get('average_execution_time', 0):.2f}s")
        
        # Coordinator status
        coord_status = self.coordinator.get_coordination_status()
        logger.info(f"📊 Coordinator: {coord_status['active']}")
        logger.info(f"  • Active assignments: {coord_status['active_assignments']}")
        logger.info(f"  • Bookmakers: {coord_status['total_bookmakers']}")
        logger.info(f"  • Health score: {coord_status['metrics']['health_score']:.2f}")
        
        # Export configurations for backup
        await self._demo_configuration_export()
        
        await asyncio.sleep(2)
    
    async def _demo_configuration_export(self):
        """Demonstrate configuration export and import"""
        logger.info("\n💾 Configuration Export/Import Demo:")
        
        # Export tab manager configuration
        tab_config = self.tab_manager.export_tab_configuration()
        logger.info(f"✅ Exported tab config: {len(tab_config.get('tabs', {}))} tabs")
        
        # Export validator configuration (mock)
        logger.info("✅ Validator config export available")
        
        # Export extension configuration
        ext_config = self.extension_handler.export_configuration()
        logger.info("✅ Extension config exported")
        
        # Show validation report export
        if self.validator.validation_history:
            latest_report = self.validator.validation_history[-1]
            report_json = self.validator.export_validation_report(latest_report)
            logger.info(f"✅ Validation report exported: {len(report_json)} characters")
    
    async def _demo_error_handling(self):
        """Phase 7: Error handling and recovery demonstration"""
        logger.info("\n" + "="*60)
        logger.info("🛡️ PHASE 7: ERROR HANDLING & RECOVERY")
        logger.info("="*60)
        
        # Simulate various error conditions
        logger.info("🔥 Simulating error conditions...")
        
        # Simulate tab errors
        tab_errors = await self._simulate_tab_errors()
        
        # Demonstrate recovery procedures
        logger.info("\n🔄 Recovery Procedures Demo:")
        
        # Tab coordinator emergency recovery
        recovery_report = self.coordinator.emergency_recovery()
        logger.info(f"🚨 Emergency recovery actions: {len(recovery_report.get('actions_taken', []))}")
        
        # Health monitoring demonstration
        self.tab_manager.perform_health_check()
        logger.info("✅ Health check performed")
        
        # Validation retry demonstration
        if self.validator.validation_history:
            latest_report = self.validator.validation_history[-1]
            failed_checks = [check for check in latest_report.checks 
                           if check.result == ValidationResult.FAILED]
            if failed_checks:
                logger.info(f"🔄 Found {len(failed_checks)} failed validations for retry")
        
        logger.info("✅ Error handling demonstration completed")
        
        await asyncio.sleep(2)
    
    async def _simulate_tab_errors(self):
        """Simulate various tab errors for testing"""
        if not self.tab_manager.tabs:
            logger.info("No tabs available for error simulation")
            return
        
        # Get first tab and simulate error
        first_tab_id = next(iter(self.tab_manager.tabs.keys()))
        
        # Update tab state to error
        self.tab_manager.update_tab_state(first_tab_id, TabState.ERROR, error_count=3)
        
        # Simulate sync message error
        self.tab_manager.send_sync_message(
            source_tab_id=first_tab_id,
            target_tab_id=None,  # Broadcast
            message_type="error_alert",
            payload={"error_type": "simulated_error", "error_message": "Demo error"},
            priority=1  # High priority
        )
        
        logger.info(f"❌ Simulated error on tab {first_tab_id}")
    
    async def cleanup(self):
        """Cleanup demo resources"""
        logger.info("\n🧹 Cleaning up demo resources...")
        
        # Stop all services
        self.tab_manager.stop_sync_processing()
        self.tab_manager.stop_health_monitoring()
        self.coordinator.stop_coordination()
        
        if self.extension_handler.is_running:
            await self.extension_handler.stop()
        
        # Close all tabs
        tabs_to_close = list(self.tab_manager.tabs.keys())
        for tab_id in tabs_to_close:
            self.tab_manager.close_tab(tab_id)
        
        logger.info("✅ Cleanup completed")
    
    def get_demo_summary(self) -> Dict[str, Any]:
        """Get comprehensive demo summary"""
        try:
            return {
                "demo_timestamp": datetime.now().isoformat(),
                "components_initialized": {
                    "tab_manager": True,
                    "validator": True, 
                    "coordinator": True,
                    "extension_handler": True
                },
                "current_status": {
                    "tab_manager": {
                        "total_tabs": len(self.tab_manager.tabs),
                        "sync_active": self.tab_manager.running,
                        "health_monitoring": self.tab_manager.health_monitor_active
                    },
                    "validator": {
                        "validation_rules": len(self.validator.validation_rules),
                        "validation_history": len(self.validator.validation_history)
                    },
                    "coordinator": {
                        "bookmakers": len(self.coordinator.bookmakers),
                        "active_assignments": len(self.coordinator.active_assignments),
                        "coordination_active": self.coordinator.monitoring_active
                    },
                    "extension_handler": {
                        "is_running": self.extension_handler.is_running,
                        "connection_status": self.extension_handler.connection_status.value
                    }
                },
                "capabilities_demonstrated": [
                    "Tab creation and management",
                    "Tab synchronization and messaging",
                    "Comprehensive validation system",
                    "Load balancing and coordination",
                    "Health monitoring and recovery",
                    "Error handling and resilience",
                    "Configuration export and import",
                    "Real-time event handling"
                ]
            }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}


async def main():
    """Main demo entry point"""
    demo = AVOTabsDemo()
    
    try:
        await demo.run_comprehensive_demo()
        
        # Print comprehensive summary
        summary = demo.get_demo_summary()
        print("\n" + "="*60)
        print("🎉 AVO TABS DEMO SUMMARY")
        print("="*60)
        print(json.dumps(summary, indent=2, default=str))
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
    finally:
        await demo.cleanup()


if __name__ == "__main__":
    # Run the comprehensive demo
    asyncio.run(main())