#!/usr/bin/env python3
"""
HITL Execution Orchestrator - Standalone Demo

This is a simplified standalone demo that demonstrates the core HITL concepts
without depending on external imports. It shows the complete workflow and
can be run directly.

Usage:
    python demo_standalone.py
"""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
import json
import os


# =============================================================================
# Mock Classes for Standalone Demo
# =============================================================================

class WorkflowState(Enum):
    """States in the HITL workflow."""
    DETECTED = "detected"
    PRESENTED = "presented"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OpportunityState:
    """Represents the state of an opportunity in the workflow."""
    opportunity_id: str
    state: WorkflowState
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_state(self, new_state: WorkflowState):
        """Update the opportunity state."""
        self.state = new_state
        self.last_updated = datetime.now()


@dataclass
class OrchestratorConfig:
    """Configuration for the HITL orchestrator."""
    max_concurrent_opportunities: int = 10
    processing_timeout: int = 300
    retry_attempts: int = 3
    retry_delay: int = 5
    enable_recovery: bool = True
    recovery_interval: int = 30
    state_save_interval: int = 60


@dataclass
class ArbitrageOpportunity:
    """Mock arbitrage opportunity for demo purposes."""
    id: str
    symbol: str
    exchange_buy: str
    exchange_sell: str
    buy_price: float
    sell_price: float
    quantity: float
    expected_profit: float
    confidence_score: float
    detected_at: datetime
    expires_at: datetime
    risk_tier: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class HitlError(Exception):
    """Base exception for HITL operations."""
    pass


class OrchestratorError(HitlError):
    """Orchestrator-specific error."""
    pass


class TimeoutError(HitlError):
    """Timeout-related error."""
    pass


class ApprovalError(HitlError):
    """Approval-related error."""
    pass


class ExecutionError(HitlError):
    """Execution-related error."""
    pass


# =============================================================================
# Mock Components
# =============================================================================

class MockAuditLogger:
    """Mock audit logger for demo purposes."""
    
    def __init__(self):
        self.logs = []
    
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log an audit event."""
        self.logs.append({
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        })
        print(f"[AUDIT] {event_type}: {data}")
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """Get all logged events."""
        return self.logs


class MockDetectionScanner:
    """Mock detection scanner for demo purposes."""
    
    async def scan_for_opportunities(self) -> List[ArbitrageOpportunity]:
        """Mock scanning that returns sample opportunities."""
        await asyncio.sleep(0.5)  # Simulate scanning time
        return []  # Scanner integration would return real opportunities
    
    async def get_opportunity_details(self, opportunity_id: str) -> Optional[ArbitrageOpportunity]:
        """Mock getting opportunity details."""
        await asyncio.sleep(0.2)
        return None


class MockRiskValidator:
    """Mock risk validator for demo purposes."""
    
    async def validate_opportunity(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Mock validation that always passes."""
        await asyncio.sleep(0.3)  # Simulate validation time
        return {
            "valid": True,
            "risk_score": 0.3,
            "risk_tier": opportunity.risk_tier,
            "validation_details": "Mock validation passed"
        }


class MockAutomationExecutor:
    """Mock automation executor for demo purposes."""
    
    async def execute_trade(self, opportunity: ArbitrageOpportunity, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock trade execution that simulates success/failure."""
        await asyncio.sleep(2)  # Simulate execution time
        
        # Simulate occasional failures for demo
        import random
        if random.random() < 0.15:  # 15% failure rate for demo
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


# =============================================================================
# Main HITL Orchestrator (Simplified for Demo)
# =============================================================================

class HITLOrchestrator:
    """
    Simplified HITL orchestrator for demonstration purposes.
    
    This is a mock version that demonstrates the core concepts without
    requiring the full implementation.
    """
    
    def __init__(self, config: OrchestratorConfig, audit_logger=None, 
                 detection_scanner=None, risk_validator=None, automation_executor=None):
        self.config = config
        self.audit_logger = audit_logger or MockAuditLogger()
        self.detection_scanner = detection_scanner or MockDetectionScanner()
        self.risk_validator = risk_validator or MockRiskValidator()
        self.automation_executor = automation_executor or MockAutomationExecutor()
        
        self.opportunities: Dict[str, OpportunityState] = {}
        self.running = False
        self.logger = logging.getLogger(__name__)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.logger.info("HITL Orchestrator initialized")
    
    async def start(self):
        """Start the orchestrator."""
        self.running = True
        self.audit_logger.log_event("orchestrator_started", {
            "config": self.config.__dict__
        })
        self.logger.info("HITL Orchestrator started")
    
    async def shutdown(self, graceful: bool = True):
        """Shutdown the orchestrator."""
        self.running = False
        self.audit_logger.log_event("orchestrator_shutdown", {
            "graceful": graceful
        })
        self.logger.info("HITL Orchestrator shutdown")
    
    async def submit_opportunity(self, opportunity: ArbitrageOpportunity):
        """Submit an opportunity for processing."""
        if not self.running:
            raise OrchestratorError("Orchestrator not running")
        
        # Create opportunity state
        state = OpportunityState(
            opportunity_id=opportunity.id,
            state=WorkflowState.DETECTED,
            metadata={"opportunity": opportunity.__dict__}
        )
        
        self.opportunities[opportunity.id] = state
        
        self.audit_logger.log_event("opportunity_submitted", {
            "opportunity_id": opportunity.id,
            "symbol": opportunity.symbol,
            "expected_profit": opportunity.expected_profit
        })
        
        # Simulate workflow progression
        asyncio.create_task(self._process_opportunity(opportunity.id))
        
        self.logger.info(f"Submitted opportunity: {opportunity.id}")
    
    async def _process_opportunity(self, opportunity_id: str):
        """Process an opportunity through the workflow."""
        try:
            state = self.opportunities.get(opportunity_id)
            if not state:
                return
            
            opportunity_data = state.metadata["opportunity"]
            
            # Simulate Phase 3-4 validation
            self.logger.info(f"Validating opportunity: {opportunity_id}")
            await asyncio.sleep(1)
            
            # Present to user (simulate approval delay)
            state.update_state(WorkflowState.PRESENTED)
            self.audit_logger.log_event("opportunity_presented", {
                "opportunity_id": opportunity_id
            })
            
            # Simulate user approval (auto-approve for demo)
            self.logger.info(f"Auto-approving opportunity: {opportunity_id}")
            approval_data = {
                "user_id": "demo_user",
                "approval_type": "automatic",
                "timestamp": datetime.now().isoformat(),
                "reason": "Demo auto-approval"
            }
            
            await self.approve_opportunity(opportunity_id, approval_data)
            
        except Exception as e:
            self.logger.error(f"Error processing opportunity {opportunity_id}: {e}")
            state.update_state(WorkflowState.FAILED)
    
    async def approve_opportunity(self, opportunity_id: str, approval_data: Dict[str, Any]):
        """Approve an opportunity for execution."""
        state = self.opportunities.get(opportunity_id)
        if not state:
            raise ApprovalError(f"Opportunity {opportunity_id} not found")
        
        if state.state != WorkflowState.PRESENTED:
            raise ApprovalError(f"Opportunity {opportunity_id} not in PRESENTED state")
        
        # Update state
        state.update_state(WorkflowState.APPROVED)
        
        self.audit_logger.log_event("opportunity_approved", {
            "opportunity_id": opportunity_id,
            "approval_data": approval_data
        })
        
        # Start execution
        asyncio.create_task(self._execute_opportunity(opportunity_id))
        
        self.logger.info(f"Approved opportunity: {opportunity_id}")
    
    async def reject_opportunity(self, opportunity_id: str, rejection_data: Dict[str, Any]):
        """Reject an opportunity."""
        state = self.opportunities.get(opportunity_id)
        if not state:
            raise ApprovalError(f"Opportunity {opportunity_id} not found")
        
        # Update state
        state.update_state(WorkflowState.FAILED)
        
        self.audit_logger.log_event("opportunity_rejected", {
            "opportunity_id": opportunity_id,
            "rejection_data": rejection_data
        })
        
        self.logger.info(f"Rejected opportunity: {opportunity_id}")
    
    async def _execute_opportunity(self, opportunity_id: str):
        """Execute an approved opportunity."""
        state = self.opportunities.get(opportunity_id)
        if not state:
            return
        
        # Update to executing
        state.update_state(WorkflowState.EXECUTING)
        
        self.audit_logger.log_event("execution_started", {
            "opportunity_id": opportunity_id
        })
        
        try:
            # Mock execution
            opportunity_dict = state.metadata["opportunity"]
            opportunity = ArbitrageOpportunity(**opportunity_dict)
            
            approval_data = {"user_id": "demo_user", "timestamp": datetime.now().isoformat()}
            result = await self.automation_executor.execute_trade(opportunity, approval_data)
            
            if result["success"]:
                state.update_state(WorkflowState.COMPLETED)
                self.audit_logger.log_event("execution_completed", {
                    "opportunity_id": opportunity_id,
                    "execution_result": result
                })
                self.logger.info(f"Successfully executed opportunity: {opportunity_id}")
            else:
                state.update_state(WorkflowState.FAILED)
                self.audit_logger.log_event("execution_failed", {
                    "opportunity_id": opportunity_id,
                    "execution_result": result
                })
                self.logger.error(f"Failed to execute opportunity: {opportunity_id}")
                
        except Exception as e:
            state.update_state(WorkflowState.FAILED)
            self.audit_logger.log_event("execution_error", {
                "opportunity_id": opportunity_id,
                "error": str(e)
            })
            self.logger.error(f"Execution error for opportunity {opportunity_id}: {e}")
    
    async def get_opportunity_states(self) -> List[OpportunityState]:
        """Get current opportunity states."""
        return list(self.opportunities.values())
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        states = list(self.opportunities.values())
        total = len(states)
        
        state_counts = {}
        for state in states:
            state_name = state.state.value
            state_counts[state_name] = state_counts.get(state_name, 0) + 1
        
        return {
            "total_opportunities": total,
            "state_counts": state_counts,
            "running": self.running
        }
    
    async def resume_from_state(self) -> Dict[str, Any]:
        """Resume from saved state (mock implementation)."""
        self.audit_logger.log_event("state_resume_attempted", {})
        return {"resumed": False, "message": "No saved state found"}


# =============================================================================
# Demo Implementation
# =============================================================================

class HITLStandaloneDemo:
    """Standalone demonstration of the HITL orchestrator."""
    
    def __init__(self):
        self.orchestrator: Optional[HITLOrchestrator] = None
        self.demo_opportunities: List[ArbitrageOpportunity] = []
        self.logger = logging.getLogger(__name__)
    
    def create_sample_opportunities(self) -> List[ArbitrageOpportunity]:
        """Create sample arbitrage opportunities for demo."""
        self.logger.info("Creating sample arbitrage opportunities...")
        
        now = datetime.now()
        
        # Low-risk crypto arbitrage
        opp1 = ArbitrageOpportunity(
            id="crypto_btc_usd_001",
            symbol="BTC/USD",
            exchange_buy="Binance",
            exchange_sell="Coinbase",
            buy_price=45000.0,
            sell_price=45250.0,
            quantity=0.1,
            expected_profit=25.0,
            confidence_score=0.85,
            detected_at=now,
            expires_at=now + timedelta(minutes=10),
            risk_tier="LOW_RISK",
            metadata={"strategy": "crypto_arbitrage"}
        )
        
        # Medium-risk forex arbitrage
        opp2 = ArbitrageOpportunity(
            id="forex_eur_usd_002",
            symbol="EUR/USD",
            exchange_buy="FXCM",
            exchange_sell="OANDA",
            buy_price=1.0950,
            sell_price=1.0955,
            quantity=10000,
            expected_profit=5.0,
            confidence_score=0.72,
            detected_at=now,
            expires_at=now + timedelta(minutes=5),
            risk_tier="MEDIUM_RISK",
            metadata={"strategy": "forex_arbitrage"}
        )
        
        # High-risk commodity arbitrage
        opp3 = ArbitrageOpportunity(
            id="commodity_gold_003",
            symbol="XAU/USD",
            exchange_buy="Interactive Brokers",
            exchange_sell="TD Ameritrade",
            buy_price=2050.0,
            sell_price=2055.0,
            quantity=1.0,
            expected_profit=5.0,
            confidence_score=0.68,
            detected_at=now,
            expires_at=now + timedelta(minutes=3),
            risk_tier="HIGH_RISK",
            metadata={"strategy": "commodity_arbitrage"}
        )
        
        self.demo_opportunities = [opp1, opp2, opp3]
        
        self.logger.info(f"Created {len(self.demo_opportunities)} sample opportunities:")
        for opp in self.demo_opportunities:
            self.logger.info(
                f"  - {opp.id}: {opp.symbol} | "
                f"Profit: ${opp.expected_profit:.2f} | "
                f"Risk: {opp.risk_tier} | "
                f"Confidence: {opp.confidence_score:.1%}"
            )
        
        return self.demo_opportunities
    
    async def demo_basic_workflow(self):
        """Demonstrate the basic HITL workflow."""
        self.logger.info("=== Starting Basic HITL Workflow Demo ===")
        
        # Create configuration
        config = OrchestratorConfig(
            max_concurrent_opportunities=10,
            enable_recovery=True,
            processing_timeout=300
        )
        
        # Initialize orchestrator
        self.orchestrator = HITLOrchestrator(config=config)
        
        # Start orchestrator
        await self.orchestrator.start()
        
        try:
            # Submit opportunities
            self.logger.info("Submitting opportunities to orchestrator...")
            for opportunity in self.demo_opportunities:
                await self.orchestrator.submit_opportunity(opportunity)
                await asyncio.sleep(0.5)  # Brief pause between submissions
            
            # Monitor processing
            await self.monitor_processing(duration=30)
            
        except Exception as e:
            self.logger.error(f"Error in basic workflow demo: {e}")
        finally:
            await self.orchestrator.shutdown(graceful=True)
    
    async def monitor_processing(self, duration: int = 30):
        """Monitor orchestrator processing."""
        self.logger.info(f"Monitoring processing for {duration} seconds...")
        
        start_time = time.time()
        while time.time() - start_time < duration and self.orchestrator.running:
            try:
                # Get statistics
                stats = await self.orchestrator.get_statistics()
                
                self.logger.info(
                    f"Active opportunities: {stats['total_opportunities']} | "
                    f"States: {stats['state_counts']}"
                )
                
                # Show detailed states for recent activities
                states = await self.orchestrator.get_opportunity_states()
                recent_states = [
                    state for state in states
                    if state.last_updated > datetime.now() - timedelta(seconds=10)
                ]
                
                for state in recent_states:
                    self.logger.info(
                        f"  - {state.opportunity_id}: {state.state.value} "
                        f"(updated: {state.last_updated.strftime('%H:%M:%S')})"
                    )
                
                await asyncio.sleep(3)
                
            except Exception as e:
                self.logger.error(f"Error monitoring processing: {e}")
                break
        
        self.logger.info("Monitoring completed")
    
    async def demo_user_interactions(self):
        """Demonstrate user interaction simulation."""
        self.logger.info("=== Starting User Interaction Demo ===")
        
        # Create configuration
        config = OrchestratorConfig(max_concurrent_opportunities=5)
        
        # Initialize orchestrator
        self.orchestrator = HITLOrchestrator(config=config)
        
        await self.orchestrator.start()
        
        try:
            # Submit one opportunity
            opportunity = self.demo_opportunities[0]
            await self.orchestrator.submit_opportunity(opportunity)
            
            # Wait for presentation
            await asyncio.sleep(2)
            
            # Get current states
            states = await self.orchestrator.get_opportunity_states()
            presented_opportunities = [
                state for state in states 
                if state.state == WorkflowState.PRESENTED
            ]
            
            if presented_opportunities:
                # Simulate approval
                state = presented_opportunities[0]
                self.logger.info(f"Simulating approval for: {state.opportunity_id}")
                
                approval_data = {
                    "user_id": "demo_user",
                    "approval_type": "manual",
                    "comments": "Looks good for demo",
                    "timestamp": datetime.now().isoformat()
                }
                
                await self.orchestrator.approve_opportunity(state.opportunity_id, approval_data)
            
            # Monitor processing
            await self.monitor_processing(duration=20)
            
        finally:
            await self.orchestrator.shutdown(graceful=True)
    
    async def run_complete_demo(self):
        """Run the complete demo sequence."""
        self.logger.info("=== Starting Complete HITL Standalone Demo ===")
        
        try:
            # Create sample opportunities
            self.logger.info("\n=== Creating Sample Opportunities ===")
            self.create_sample_opportunities()
            
            # Basic workflow demo
            self.logger.info("\n=== Basic Workflow Demo ===")
            await self.demo_basic_workflow()
            
            # Brief pause
            await asyncio.sleep(3)
            
            # User interactions demo
            self.logger.info("\n=== User Interactions Demo ===")
            await self.demo_user_interactions()
            
            self.logger.info("\n=== Complete Demo Finished ===")
            self.logger.info("This demo showed the core HITL workflow concepts:")
            self.logger.info("1. Opportunity submission and processing")
            self.logger.info("2. State management through workflow")
            self.logger.info("3. User approval simulation")
            self.logger.info("4. Trade execution")
            self.logger.info("5. Comprehensive logging and monitoring")
            
        except KeyboardInterrupt:
            self.logger.info("Demo interrupted by user")
        except Exception as e:
            self.logger.error(f"Demo failed: {e}")
            raise
        finally:
            if self.orchestrator:
                await self.orchestrator.shutdown(graceful=True)


async def main():
    """Main demo entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="HITL Orchestrator Standalone Demo")
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
        "--duration",
        type=int,
        default=30,
        help="Monitoring duration in seconds"
    )
    
    args = parser.parse_args()
    
    # Create demo instance
    demo = HITLStandaloneDemo()
    
    try:
        if args.workflow:
            # Workflow demo only
            demo.create_sample_opportunities()
            await demo.demo_basic_workflow()
            
        elif args.interactions:
            # User interactions demo only
            demo.create_sample_opportunities()
            await demo.demo_user_interactions()
            
        else:
            # Run complete demo
            await demo.run_complete_demo()
            
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    """
    Standalone HITL Orchestrator Demo
    
    This demo can be run directly without any dependencies on the existing
    arbitech codebase. It demonstrates the core concepts of the HITL system:
    
    1. **Workflow Orchestration**: How opportunities flow through states
    2. **State Management**: Tracking opportunities through the pipeline
    3. **User Interactions**: Approval and rejection processes
    4. **Error Handling**: Recovery and failure scenarios
    5. **Logging and Monitoring**: Comprehensive audit trails
    
    Usage:
        python demo_standalone.py              # Complete demo
        python demo_standalone.py --workflow  # Workflow only
        python demo_standalone.py --interactions  # User interactions only
    
    This demo is perfect for:
    - Understanding HITL concepts
    - Testing workflow logic
    - Demonstrating the system to stakeholders
    - Training and educational purposes
    """
    
    # Ensure required directories exist
    os.makedirs("logs", exist_ok=True)
    os.makedirs("state", exist_ok=True)
    
    # Setup logging to both file and console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/hitl_standalone_demo.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                    HITL Orchestrator Standalone Demo          ║
    ║             Human-in-the-Loop Trading System Demo             ║
    ║                                                               ║
    ║  This demo shows the complete HITL workflow without external  ║
    ║  dependencies. Perfect for understanding the system concepts. ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Run the demo
    asyncio.run(main())