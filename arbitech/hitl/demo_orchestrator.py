#!/usr/bin/env python3
"""
HITL Execution Orchestrator - Comprehensive Demo

This demo file demonstrates the complete usage of the HITL execution orchestrator,
showing how to integrate with all system components and handle the full workflow
from opportunity detection through execution.

Key Integration Points:
1. ConfigManager - Configuration loading and management
2. AuditLogger - Structured logging and audit trails  
3. Detection Scanner - Phase 3 opportunity detection
4. Risk Validator - Phase 4 risk assessment and validation
5. Automation Executor - Phase 5 trade execution
6. Timeout Manager - HITL timeout handling
7. Opportunity Presenter - User-facing opportunity presentation
8. Approval Handler - User approval/rejection processing
9. Result Logger - Trade outcome logging and persistence

Author: Arbitech Trading System
Created: 2025-11-02
"""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import os

# Import HITL orchestrator and components
try:
    # Try relative imports first (when imported as module)
    from .execution_orchestrator import (
        HITLOrchestrator,
        WorkflowState,
        OpportunityState,
        OrchestratorConfig,
        HitlError
    )
except ImportError:
    try:
        # Try absolute imports (when running as script)
        from arbitech.hitl.execution_orchestrator import (
            HITLOrchestrator,
            WorkflowState,
            OpportunityState,
            OrchestratorConfig,
            HitlError
        )
    except ImportError:
        # Create mock classes for standalone demo
        logging.warning("Could not import execution_orchestrator, using mock classes")
        
        from enum import Enum
        from dataclasses import dataclass
        from datetime import datetime
        
        class WorkflowState(Enum):
            DETECTED = "detected"
            PRESENTED = "presented"
            APPROVED = "approved"
            EXECUTING = "executing"
            COMPLETED = "completed"
            FAILED = "failed"
            CANCELLED = "cancelled"
        
        @dataclass
        class OpportunityState:
            opportunity_id: str
            state: WorkflowState
            created_at: datetime
            last_updated: datetime
        
        @dataclass
        class OrchestratorConfig:
            max_concurrent_opportunities: int = 10
            processing_timeout: int = 300
            retry_attempts: int = 3
            retry_delay: int = 5
            enable_recovery: bool = True
            recovery_interval: int = 30
            state_save_interval: int = 60
        
        class HitlError(Exception):
            pass
        
        class HITLOrchestrator:
            def __init__(self, config, audit_logger=None, detection_scanner=None, 
                         risk_validator=None, automation_executor=None):
                self.config = config
                logging.info("Using mock HITLOrchestrator for demo")
                
            async def submit_opportunity(self, opportunity):
                logging.info(f"Mock: Submitted opportunity {opportunity.id}")
                
            async def start(self):
                logging.info("Mock: Started orchestrator")
                
            async def shutdown(self, graceful=True):
                logging.info("Mock: Shutdown orchestrator")
                
            async def get_opportunity_states(self):
                return []
                
            async def approve_opportunity(self, opportunity_id, approval_data):
                logging.info(f"Mock: Approved opportunity {opportunity_id}")
                
            async def reject_opportunity(self, opportunity_id, rejection_data):
                logging.info(f"Mock: Rejected opportunity {opportunity_id}")
                
            async def resume_from_state(self):
                return {"resumed": False}

# Import system integration components
try:
    from arbitech.core.config_manager import ConfigManager
    from arbitech.core.audit_logger import AuditLogger
    from arbitech.storage.models import (
        ArbitrageOpportunity, 
        Trade, 
        ArbitrageLeg,
        TradeStatus,
        RiskTier,
        OpportunityStatus
    )
    from arbitech.core.detection.scanner import DetectionScanner
    from arbitech.core.risk.validator import RiskValidator
    from arbitech.core.automation.executor import AutomationExecutor
except ImportError as e:
    logging.warning(f"Could not import some components: {e}")
    # Create mock classes for demo purposes
    ConfigManager = None
    AuditLogger = None
    DetectionScanner = None
    RiskValidator = None
    AutomationExecutor = None
    
    # Create mock ArbitrageOpportunity if not available
    try:
        from typing import TypedDict
        
        class RiskTier:
            LOW_RISK = "low_risk"
            MEDIUM_RISK = "medium_risk"  
            HIGH_RISK = "high_risk"
            
        class ArbitrageOpportunity:
            def __init__(self, id, symbol, exchange_buy, exchange_sell, 
                        buy_price, sell_price, quantity, expected_profit, 
                        confidence_score, detected_at, expires_at, risk_tier, metadata):
                self.id = id
                self.symbol = symbol
                self.exchange_buy = exchange_buy
                self.exchange_sell = exchange_sell
                self.buy_price = buy_price
                self.sell_price = sell_price
                self.quantity = quantity
                self.expected_profit = expected_profit
                self.confidence_score = confidence_score
                self.detected_at = detected_at
                self.expires_at = expires_at
                self.risk_tier = risk_tier
                self.metadata = metadata
    except:
        pass


class HITLDemo:
    """
    Comprehensive demonstration of the HITL execution orchestrator.
    
    This class provides a complete example of how to:
    1. Initialize and configure the orchestrator
    2. Submit opportunities for processing
    3. Simulate user interactions (approvals/rejections)
    4. Handle graceful shutdown and recovery
    5. Resume processing from saved state
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the demo environment.
        
        Args:
            config_path: Path to configuration file (YAML)
        """
        self.config_path = config_path
        self.orchestrator: Optional[HITLOrchestrator] = None
        self.demo_opportunities: List[ArbitrageOpportunity] = []
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
        # Demo configuration
        self.demo_config = self._create_demo_config()
    
    def _setup_logging(self):
        """Configure logging for the demo."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/workspace/arbitech/logs/hitl_demo.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("HITL Demo initialized with logging")
    
    def _create_demo_config(self) -> Dict[str, Any]:
        """
        Create demo configuration for the orchestrator.
        
        This demonstrates how to configure the HITL system with:
        - Timeout settings for different risk tiers
        - Approval requirements and workflows
        - Retry policies and failure handling
        - Concurrent processing limits
        - Notification settings
        
        Returns:
            Dict containing orchestrator configuration
        """
        return {
            # Core orchestrator settings
            "orchestrator": {
                "max_concurrent_opportunities": 10,
                "processing_timeout": 300,  # 5 minutes
                "retry_attempts": 3,
                "retry_delay": 5,
                "enable_recovery": True,
                "recovery_interval": 30,
                "state_save_interval": 60
            },
            
            # Timeout settings by risk tier
            "timeouts": {
                "LOW_RISK": {
                    "approval_timeout": 120,  # 2 minutes
                    "execution_timeout": 60,   # 1 minute
                    "auto_approve": True
                },
                "MEDIUM_RISK": {
                    "approval_timeout": 300,  # 5 minutes
                    "execution_timeout": 180,  # 3 minutes
                    "auto_approve": False
                },
                "HIGH_RISK": {
                    "approval_timeout": 600,  # 10 minutes
                    "execution_timeout": 300,  # 5 minutes
                    "auto_approve": False
                }
            },
            
            # Approval workflow settings
            "approval": {
                "require_dual_approval": False,
                "approval_callbacks": [
                    "email_notification",
                    "slack_notification"
                ],
                "rejection_reasons": [
                    "insufficient_profit",
                    "high_risk",
                    "market_conditions",
                    "user_cancelled"
                ]
            },
            
            # Recovery and error handling
            "recovery": {
                "enable_auto_recovery": True,
                "recovery_attempts": 3,
                "recovery_delay": 10,
                "save_failed_opportunities": True,
                "cleanup_failed_after": 3600  # 1 hour
            },
            
            # Integration settings
            "integrations": {
                "detection_scanner": {
                    "enabled": True,
                    "scan_interval": 30,
                    "min_profit_threshold": 100.0
                },
                "risk_validator": {
                    "enabled": True,
                    "max_position_size": 10000.0,
                    "max_exposure_per_market": 5000.0
                },
                "automation_executor": {
                    "enabled": True,
                    "max_concurrent_trades": 5,
                    "execution_delay": 2
                }
            }
        }
    
    async def initialize_orchestrator(self) -> bool:
        """
        Initialize the HITL orchestrator with configuration.
        
        This demonstrates:
        1. Loading configuration from file or creating demo config
        2. Initializing the orchestrator with all required components
        3. Setting up error handling and recovery mechanisms
        4. Configuring state persistence
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing HITL execution orchestrator...")
            
            # Initialize configuration manager
            if self.config_path and os.path.exists(self.config_path):
                config_manager = ConfigManager(self.config_path)
                config = config_manager.get_config()
                self.logger.info(f"Loaded configuration from {self.config_path}")
            else:
                # Use demo configuration
                config = self.demo_config
                self.logger.info("Using demo configuration")
            
            # Initialize audit logger for comprehensive logging
            audit_logger = AuditLogger() if AuditLogger else None
            if audit_logger:
                audit_logger.log_event("demo_start", {
                    "timestamp": datetime.now().isoformat(),
                    "action": "orchestrator_initialization",
                    "config_source": "demo" if not self.config_path else "file"
                })
            
            # Create orchestrator configuration
            orchestrator_config = OrchestratorConfig(
                max_concurrent_opportunities=config["orchestrator"]["max_concurrent_opportunities"],
                processing_timeout=config["orchestrator"]["processing_timeout"],
                retry_attempts=config["orchestrator"]["retry_attempts"],
                retry_delay=config["orchestrator"]["retry_delay"],
                enable_recovery=config["orchestrator"]["enable_recovery"],
                recovery_interval=config["orchestrator"]["recovery_interval"],
                state_save_interval=config["orchestrator"]["state_save_interval"]
            )
            
            # Initialize the orchestrator with all components
            self.orchestrator = HITLOrchestrator(
                config=orchestrator_config,
                audit_logger=audit_logger,
                detection_scanner=self._create_mock_scanner(),
                risk_validator=self._create_mock_validator(),
                automation_executor=self._create_mock_executor()
            )
            
            self.logger.info("HITL orchestrator initialized successfully")
            
            if audit_logger:
                audit_logger.log_event("orchestrator_ready", {
                    "timestamp": datetime.now().isoformat(),
                    "status": "initialized",
                    "components": ["detection_scanner", "risk_validator", "automation_executor"]
                })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize orchestrator: {e}")
            return False
    
    def _create_mock_scanner(self):
        """Create a mock detection scanner for demo purposes."""
        class MockScanner:
            def __init__(self):
                self.logger = logging.getLogger("MockScanner")
            
            async def scan_for_opportunities(self):
                """Mock scanning that returns sample opportunities."""
                await asyncio.sleep(1)  # Simulate scanning time
                return []
            
            async def get_opportunity_details(self, opportunity_id: str):
                """Mock getting opportunity details."""
                await asyncio.sleep(0.5)
                return None
        
        return MockScanner()
    
    def _create_mock_validator(self):
        """Create a mock risk validator for demo purposes."""
        class MockValidator:
            def __init__(self):
                self.logger = logging.getLogger("MockValidator")
            
            async def validate_opportunity(self, opportunity):
                """Mock validation that always passes."""
                await asyncio.sleep(0.5)  # Simulate validation time
                return {"valid": True, "risk_score": 0.3, "risk_tier": "LOW_RISK"}
            
            async def calculate_position_sizing(self, opportunity, account_balance):
                """Mock position sizing calculation."""
                return min(opportunity.expected_profit * 0.1, 1000.0)
        
        return MockValidator()
    
    def _create_mock_executor(self):
        """Create a mock automation executor for demo purposes."""
        class MockExecutor:
            def __init__(self):
                self.logger = logging.getLogger("MockExecutor")
            
            async def execute_trade(self, opportunity, approval_data):
                """Mock trade execution that simulates success/failure."""
                await asyncio.sleep(2)  # Simulate execution time
                
                # Simulate occasional failures for demo
                import random
                if random.random() < 0.1:  # 10% failure rate
                    return {
                        "success": False,
                        "error": "Market temporarily unavailable",
                        "execution_id": f"mock_exec_{random.randint(1000, 9999)}"
                    }
                
                return {
                    "success": True,
                    "execution_id": f"mock_exec_{random.randint(1000, 9999)}",
                    "executed_price": opportunity.expected_profit * 0.95,
                    "execution_time": datetime.now().isoformat()
                }
        
        return MockExecutor()
    
    def create_sample_opportunities(self) -> List[ArbitrageOpportunity]:
        """
        Create sample arbitrage opportunities for demo purposes.
        
        This demonstrates:
        1. How to create ArbitrageOpportunity objects
        2. Setting up ArbitrageLeg objects for buy/sell legs
        3. Configuring profit expectations and risk levels
        4. Adding metadata for tracking and reporting
        
        Returns:
            List of sample ArbitrageOpportunity objects
        """
        self.logger.info("Creating sample arbitrage opportunities...")
        
        # Sample opportunity 1: Low-risk crypto arbitrage
        opportunity1 = ArbitrageOpportunity(
            id="crypto_arbitrage_btc_usd_001",
            symbol="BTC/USD",
            exchange_buy="Binance",
            exchange_sell="Coinbase",
            buy_price=45000.0,
            sell_price=45250.0,
            quantity=0.1,
            expected_profit=25.0,
            confidence_score=0.85,
            detected_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=10),
            risk_tier=RiskTier.LOW_RISK,
            metadata={
                "strategy": "crypto_arbitrage",
                "market_hours": "24/7",
                "liquidity": "high",
                "notes": "Bitcoin arbitrage between major exchanges"
            }
        )
        
        # Sample opportunity 2: Medium-risk forex arbitrage
        opportunity2 = ArbitrageOpportunity(
            id="forex_arb_eur_usd_002",
            symbol="EUR/USD",
            exchange_buy="FXCM",
            exchange_sell="OANDA",
            buy_price=1.0950,
            sell_price=1.0955,
            quantity=10000,
            expected_profit=5.0,
            confidence_score=0.72,
            detected_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=5),
            risk_tier=RiskTier.MEDIUM_RISK,
            metadata={
                "strategy": "forex_arbitrage",
                "market_hours": "business_hours",
                "liquidity": "medium",
                "notes": "EUR/USD spread arbitrage during London session"
            }
        )
        
        # Sample opportunity 3: High-risk commodity arbitrage
        opportunity3 = ArbitrageOpportunity(
            id="commodity_arbitrage_gold_003",
            symbol="XAU/USD",
            exchange_buy="Interactive Brokers",
            exchange_sell="TD Ameritrade",
            buy_price=2050.0,
            sell_price=2055.0,
            quantity=1.0,
            expected_profit=5.0,
            confidence_score=0.68,
            detected_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=3),
            risk_tier=RiskTier.HIGH_RISK,
            metadata={
                "strategy": "commodity_arbitrage",
                "market_hours": "business_hours",
                "liquidity": "low",
                "notes": "Gold arbitrage with limited liquidity"
            }
        )
        
        self.demo_opportunities = [opportunity1, opportunity2, opportunity3]
        
        self.logger.info(f"Created {len(self.demo_opportunities)} sample opportunities:")
        for opp in self.demo_opportunities:
            self.logger.info(
                f"  - {opp.id}: {opp.symbol} | "
                f"Profit: ${opp.expected_profit:.2f} | "
                f"Risk: {opp.risk_tier.value} | "
                f"Confidence: {opp.confidence_score:.1%}"
            )
        
        return self.demo_opportunities
    
    async def demo_basic_workflow(self):
        """
        Demonstrate the basic HITL workflow: submit → approve → execute.
        
        This shows:
        1. How to submit opportunities to the orchestrator
        2. How opportunities flow through the state machine
        3. How user approvals are processed
        4. How execution results are handled
        """
        self.logger.info("=== Starting Basic HITL Workflow Demo ===")
        
        if not self.orchestrator:
            self.logger.error("Orchestrator not initialized")
            return
        
        try:
            # Submit opportunities to the orchestrator
            self.logger.info("Submitting opportunities to orchestrator...")
            for opportunity in self.demo_opportunities:
                # This would normally be called by the detection scanner
                await self.orchestrator.submit_opportunity(opportunity)
                self.logger.info(f"Submitted opportunity: {opportunity.id}")
                
                # Brief pause between submissions
                await asyncio.sleep(0.5)
            
            # Start the orchestrator to begin processing
            self.logger.info("Starting orchestrator processing...")
            await self.orchestrator.start()
            
            # Monitor processing for a limited time
            await self.monitor_processing(duration=60)
            
        except Exception as e:
            self.logger.error(f"Error in basic workflow demo: {e}")
    
    async def demo_user_interactions(self):
        """
        Demonstrate simulated user interactions (approvals/rejections).
        
        This shows:
        1. How to approve opportunities
        2. How to reject opportunities with reasons
        3. How to handle approval timeouts
        4. How to process batch approvals/rejections
        """
        self.logger.info("=== Starting User Interaction Demo ===")
        
        if not self.orchestrator:
            self.logger.error("Orchestrator not initialized")
            return
        
        try:
            # Submit a new opportunity for interaction demo
            opportunity = self.demo_opportunities[0]
            await self.orchestrator.submit_opportunity(opportunity)
            
            # Start processing
            await self.orchestrator.start()
            
            # Wait for opportunity to be presented
            await asyncio.sleep(2)
            
            # Get current opportunity states
            opportunity_states = await self.orchestrator.get_opportunity_states()
            presented_opportunities = [
                state for state in opportunity_states 
                if state.state == WorkflowState.PRESENTED
            ]
            
            if presented_opportunities:
                # Demonstrate approval
                state = presented_opportunities[0]
                self.logger.info(f"Simulating approval for opportunity: {state.opportunity_id}")
                
                approval_data = {
                    "user_id": "demo_user_001",
                    "approval_type": "manual",
                    "comments": "Looks good, approved for execution",
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.orchestrator.approve_opportunity(state.opportunity_id, approval_data)
                
                # Demonstrate rejection with reason
                if len(presented_opportunities) > 1:
                    state2 = presented_opportunities[1]
                    self.logger.info(f"Simulating rejection for opportunity: {state2.opportunity_id}")
                    
                    rejection_data = {
                        "user_id": "demo_user_001",
                        "rejection_reason": "insufficient_profit",
                        "comments": "Profit margin too low for the risk level",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await self.orchestrator.reject_opportunity(state2.opportunity_id, rejection_data)
            
            # Monitor processing
            await self.monitor_processing(duration=30)
            
        except Exception as e:
            self.logger.error(f"Error in user interaction demo: {e}")
    
    async def demo_graceful_shutdown(self):
        """
        Demonstrate graceful shutdown capabilities.
        
        This shows:
        1. How to initiate graceful shutdown
        2. How the orchestrator handles in-flight opportunities
        3. How state is preserved during shutdown
        4. How to resume after shutdown
        """
        self.logger.info("=== Starting Graceful Shutdown Demo ===")
        
        if not self.orchestrator:
            self.logger.error("Orchestrator not initialized")
            return
        
        try:
            # Submit opportunities and start processing
            self.logger.info("Submitting opportunities for shutdown demo...")
            for opportunity in self.demo_opportunities[:2]:
                await self.orchestrator.submit_opportunity(opportunity)
            
            # Start processing
            self.logger.info("Starting orchestrator...")
            await self.orchestrator.start()
            
            # Let it run for a bit
            await asyncio.sleep(5)
            
            # Demonstrate graceful shutdown
            self.logger.info("Initiating graceful shutdown...")
            await self.orchestrator.shutdown(graceful=True)
            
            self.logger.info("Orchestrator shutdown completed")
            
            # Check if state was saved
            if hasattr(self.orchestrator, '_state_manager'):
                state_file = "/workspace/arbitech/hitl/state/orchestrator_state.json"
                if os.path.exists(state_file):
                    self.logger.info(f"State saved to: {state_file}")
                    
                    # Show saved state
                    with open(state_file, 'r') as f:
                        saved_state = json.load(f)
                        self.logger.info(f"Saved state contains {len(saved_state.get('opportunities', []))} opportunities")
            
        except Exception as e:
            self.logger.error(f"Error in graceful shutdown demo: {e}")
    
    async def demo_state_resume(self):
        """
        Demonstrate state resume functionality.
        
        This shows:
        1. How to load saved state
        2. How to resume processing from saved state
        3. How opportunities are restored to their previous state
        4. How to handle partially completed workflows
        """
        self.logger.info("=== Starting State Resume Demo ===")
        
        if not self.orchestrator:
            self.logger.error("Orchestrator not initialized")
            return
        
        try:
            # Attempt to resume from saved state
            self.logger.info("Attempting to resume from saved state...")
            
            resume_result = await self.orchestrator.resume_from_state()
            
            if resume_result.get("resumed", False):
                self.logger.info("Successfully resumed from saved state")
                self.logger.info(f"Resumed {resume_result.get('resumed_count', 0)} opportunities")
                
                # Show the states of resumed opportunities
                opportunity_states = await self.orchestrator.get_opportunity_states()
                for state in opportunity_states:
                    self.logger.info(
                        f"  - {state.opportunity_id}: {state.state.value} "
                        f"(started: {state.created_at.strftime('%H:%M:%S')})"
                    )
            else:
                self.logger.info("No saved state found, starting fresh")
            
            # Start processing resumed opportunities
            await self.orchestrator.start()
            await self.monitor_processing(duration=30)
            
        except Exception as e:
            self.logger.error(f"Error in state resume demo: {e}")
    
    async def demo_error_handling(self):
        """
        Demonstrate error handling and recovery mechanisms.
        
        This shows:
        1. How errors are logged and tracked
        2. How retry mechanisms work
        3. How failed opportunities are handled
        4. How recovery mechanisms activate
        """
        self.logger.info("=== Starting Error Handling Demo ===")
        
        if not self.orchestrator:
            self.logger.error("Orchestrator not initialized")
            return
        
        try:
            # Submit opportunities and force some errors
            self.logger.info("Submitting opportunities for error handling demo...")
            
            for opportunity in self.demo_opportunities:
                await self.orchestrator.submit_opportunity(opportunity)
            
            # Start processing
            await self.orchestrator.start()
            
            # Monitor for errors and recovery
            await self.monitor_processing(duration=45)
            
            # Check error statistics
            if hasattr(self.orchestrator, 'get_error_stats'):
                error_stats = await self.orchestrator.get_error_stats()
                self.logger.info("Error handling statistics:")
                for error_type, count in error_stats.items():
                    self.logger.info(f"  - {error_type}: {count}")
            
        except Exception as e:
            self.logger.error(f"Error in error handling demo: {e}")
    
    async def monitor_processing(self, duration: int = 30):
        """
        Monitor orchestrator processing and display status updates.
        
        Args:
            duration: How long to monitor (seconds)
        """
        self.logger.info(f"Monitoring processing for {duration} seconds...")
        
        start_time = time.time()
        while time.time() - start_time < duration:
            try:
                # Get current opportunity states
                opportunity_states = await self.orchestrator.get_opportunity_states()
                
                # Count opportunities by state
                state_counts = {}
                for state in opportunity_states:
                    state_name = state.state.value
                    state_counts[state_name] = state_counts.get(state_name, 0) + 1
                
                # Display status
                self.logger.info(
                    f"Active opportunities: {len(opportunity_states)} | "
                    f"States: {state_counts}"
                )
                
                # Show detailed info for recent activities
                recent_states = [
                    state for state in opportunity_states
                    if state.last_updated > datetime.now() - timedelta(seconds=10)
                ]
                
                for state in recent_states:
                    self.logger.info(
                        f"  - {state.opportunity_id}: {state.state.value} "
                        f"(updated: {state.last_updated.strftime('%H:%M:%S')})"
                    )
                
                await asyncio.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error monitoring processing: {e}")
                break
        
        self.logger.info("Monitoring completed")
    
    async def run_complete_demo(self):
        """
        Run the complete demo sequence covering all aspects of the HITL orchestrator.
        
        Demo Flow:
        1. Initialize orchestrator
        2. Demonstrate basic workflow
        3. Show user interactions
        4. Demonstrate graceful shutdown
        5. Resume from state
        6. Show error handling
        """
        self.logger.info("=== Starting Complete HITL Orchestrator Demo ===")
        
        try:
            # Step 1: Initialize
            self.logger.info("\n=== Step 1: Initialize Orchestrator ===")
            if not await self.initialize_orchestrator():
                self.logger.error("Failed to initialize orchestrator")
                return
            
            # Step 2: Create sample opportunities
            self.logger.info("\n=== Step 2: Create Sample Opportunities ===")
            self.create_sample_opportunities()
            
            # Step 3: Basic workflow
            self.logger.info("\n=== Step 3: Basic Workflow ===")
            await self.demo_basic_workflow()
            
            # Brief pause between demos
            await asyncio.sleep(3)
            
            # Step 4: User interactions
            self.logger.info("\n=== Step 4: User Interactions ===")
            await self.demo_user_interactions()
            
            # Brief pause between demos
            await asyncio.sleep(3)
            
            # Step 5: Error handling
            self.logger.info("\n=== Step 5: Error Handling ===")
            await self.demo_error_handling()
            
            # Step 6: Graceful shutdown
            self.logger.info("\n=== Step 6: Graceful Shutdown ===")
            await self.demo_graceful_shutdown()
            
            # Brief pause before resume
            await asyncio.sleep(2)
            
            # Step 7: State resume
            self.logger.info("\n=== Step 7: State Resume ===")
            await self.demo_state_resume()
            
            self.logger.info("\n=== Complete HITL Demo Finished ===")
            
        except KeyboardInterrupt:
            self.logger.info("Demo interrupted by user")
        except Exception as e:
            self.logger.error(f"Demo failed: {e}")
            raise
        finally:
            if self.orchestrator:
                await self.orchestrator.shutdown(graceful=True)


async def main():
    """
    Main demo entry point with command line argument support.
    
    Usage:
    - python demo_orchestrator.py                    # Run complete demo
    - python demo_orchestrator.py --init-only        # Initialize only
    - python demo_orchestrator.py --workflow         # Workflow demo only
    - python demo_orchestrator.py --interactions     # User interactions only
    - python demo_orchestrator.py --shutdown         # Shutdown demo only
    - python demo_orchestrator.py --resume           # Resume demo only
    - python demo_orchestrator.py --errors           # Error handling only
    - python demo_orchestrator.py --config config.yaml  # Use custom config
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="HITL Orchestrator Demo")
    parser.add_argument(
        "--init-only", 
        action="store_true",
        help="Initialize orchestrator only"
    )
    parser.add_argument(
        "--workflow",
        action="store_true", 
        help="Run workflow demo only"
    )
    parser.add_argument(
        "--interactions",
        action="store_true",
        help="Run user interactions demo only"
    )
    parser.add_argument(
        "--shutdown",
        action="store_true",
        help="Run graceful shutdown demo only"
    )
    parser.add_argument(
        "--resume", 
        action="store_true",
        help="Run state resume demo only"
    )
    parser.add_argument(
        "--errors",
        action="store_true",
        help="Run error handling demo only"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Create demo instance
    demo = HITLDemo(config_path=args.config)
    
    try:
        if args.init_only:
            # Initialize only
            await demo.initialize_orchestrator()
            demo.create_sample_opportunities()
            print("Initialization complete. Use --workflow to start processing.")
            
        elif args.workflow:
            # Workflow demo only
            await demo.initialize_orchestrator()
            demo.create_sample_opportunities()
            await demo.demo_basic_workflow()
            
        elif args.interactions:
            # User interactions demo only
            await demo.initialize_orchestrator()
            demo.create_sample_opportunities()
            await demo.demo_user_interactions()
            
        elif args.shutdown:
            # Shutdown demo only
            await demo.initialize_orchestrator()
            demo.create_sample_opportunities()
            await demo.demo_graceful_shutdown()
            
        elif args.resume:
            # Resume demo only
            await demo.initialize_orchestrator()
            await demo.demo_state_resume()
            
        elif args.errors:
            # Error handling demo only
            await demo.initialize_orchestrator()
            demo.create_sample_opportunities()
            await demo.demo_error_handling()
            
        else:
            # Run complete demo
            await demo.run_complete_demo()
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo failed: {e}")
        raise
    finally:
        if demo.orchestrator:
            await demo.orchestrator.shutdown(graceful=True)


if __name__ == "__main__":
    """
    Entry point for the HITL orchestrator demo.
    
    This script demonstrates the complete integration of the HITL execution
    orchestrator with all system components:
    
    1. ConfigManager - Configuration loading and management
    2. AuditLogger - Comprehensive audit trails
    3. DetectionScanner - Phase 3 opportunity detection
    4. RiskValidator - Phase 4 risk assessment
    5. AutomationExecutor - Phase 5 trade execution
    6. TimeoutManager - HITL timeout handling
    7. OpportunityPresenter - User-facing presentations
    8. ApprovalHandler - User approval/rejection processing
    9. ResultLogger - Trade outcome logging
    
    To run the complete demo:
        python demo_orchestrator.py
    
    To run specific demos:
        python demo_orchestrator.py --workflow
        python demo_orchestrator.py --interactions
        python demo_orchestrator.py --errors
    
    To use a custom configuration:
        python demo_orchestrator.py --config /path/to/config.yaml
    
    For more information, see the HITL system documentation.
    """
    
    # Ensure required directories exist
    os.makedirs("/workspace/arbitech/logs", exist_ok=True)
    os.makedirs("/workspace/arbitech/hitl/state", exist_ok=True)
    os.makedirs("/workspace/arbitech/hitl/data", exist_ok=True)
    
    # Run the demo
    asyncio.run(main())