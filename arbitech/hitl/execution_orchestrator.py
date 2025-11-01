"""
Human-in-the-Loop (HITL) Execution Orchestrator

Main orchestration component for managing the complete HITL workflow from Phase 3 
detection through Phase 5 execution. Provides enterprise-grade coordination with:
- Complete workflow orchestration
- State management across pipeline
- Concurrent opportunity processing
- Comprehensive error handling and recovery
- Graceful shutdown and resumption
- Integration with configuration and logging systems
"""

import asyncio
import logging
import time
import threading
from typing import Dict, List, Optional, Any, Tuple, Union, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from contextlib import asynccontextmanager, suppress
from collections import defaultdict, deque
import json
import signal
import weakref

# Core imports
from ..core.config_manager import ConfigManager, get_config_manager
from ..storage.models import (
    ArbitrageOpportunity, Trade, TradeStatus, RiskTier,
    ArbitrageLeg, TimestampMixin, UUIDMixin
)
from ..storage.audit_logger import get_audit_logger, EventType, LogLevel
from ..utils.logger import get_logger, LoggerUtils
from ..risk.risk_classifier import RiskClassifier
from ..risk.stake_optimizer import StakeOptimizer
from ..risk.safety_pipeline import SafetyPipeline
from ..risk.emergency_stops import EmergencyStopManager
from ..automation.arbitrage_browser import ArbitrageBrowser
from ..automation.avo_tabs_interface import AVOTabsInterface


# Exception classes for HITL workflow
class HITLWorkflowError(Exception):
    """Base exception for HITL workflow errors."""
    pass


class ApprovalTimeoutError(HITLWorkflowError):
    """Raised when human approval times out."""
    pass


class EmergencyStopTriggered(HITLWorkflowError):
    """Raised when emergency stop is triggered during execution."""
    pass


class StateCorruptionError(HITLWorkflowError):
    """Raised when workflow state is corrupted."""
    pass


class ConcurrentExecutionError(HITLWorkflowError):
    """Raised when concurrent execution conflict detected."""
    pass


class WorkflowPhase(str, Enum):
    """HITL workflow phases."""
    DETECTION = "detection"
    VALIDATION = "validation"
    RISK_ASSESSMENT = "risk_assessment"
    STAKE_CALCULATION = "stake_calculation"
    PRESENTATION = "presentation"
    APPROVAL = "approval"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    SETTLEMENT = "settlement"
    COMPLETION = "completion"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApprovalStatus(str, Enum):
    """Approval request status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    EXPIRED = "expired"


class ExecutionState(str, Enum):
    """Workflow execution state."""
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


@dataclass
class HITLWorkflowContext:
    """Context for HITL workflow execution."""
    workflow_id: UUID = field(default_factory=uuid4)
    opportunity_id: UUID = field(default_factory=uuid4)
    opportunity: Optional[ArbitrageOpportunity] = None
    current_phase: WorkflowPhase = WorkflowPhase.DETECTION
    state: ExecutionState = ExecutionState.IDLE
    
    # Timing information
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    phase_started_at: Optional[datetime] = None
    
    # Approval information
    approval_requested: bool = False
    approval_status: Optional[ApprovalStatus] = None
    approval_requested_at: Optional[datetime] = None
    approval_expires_at: Optional[datetime] = None
    
    # Execution information
    trade_id: Optional[UUID] = None
    execution_mode: str = "manual"  # manual, auto_approved, auto_rejected
    requires_human_approval: bool = True
    
    # Error handling
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    
    # Performance metrics
    phase_durations: Dict[str, float] = field(default_factory=dict)
    total_duration: Optional[float] = None
    
    # Dependencies
    stakeholders: Set[str] = field(default_factory=set)
    locks_held: Set[str] = field(default_factory=set)


@dataclass
class ApprovalRequest:
    """Represents a human approval request."""
    request_id: UUID = field(default_factory=uuid4)
    workflow_id: UUID = field(default_factory=uuid4)
    opportunity_id: UUID = field(default_factory=uuid4)
    
    # Request details
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    priority: str = "medium"  # low, medium, high, critical
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))
    
    # Status
    status: ApprovalStatus = ApprovalStatus.PENDING
    responded_at: Optional[datetime] = None
    response: Optional[str] = None
    
    # Context
    risk_tier: Optional[RiskTier] = None
    expected_profit: Optional[float] = None
    total_stake: Optional[float] = None
    bookmakers: List[str] = field(default_factory=list)
    human_reviewer: Optional[str] = None


class HITLExecutionOrchestrator:
    """
    Main HITL execution orchestrator that coordinates the complete workflow
    from opportunity detection through execution and settlement.
    """
    
    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        audit_logger=None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the HITL execution orchestrator."""
        self.config_manager = config_manager or get_config_manager()
        self.audit_logger = audit_logger or get_audit_logger()
        self.logger = logger or get_logger('hitl_orchestrator')
        self.logger_utils = LoggerUtils()
        
        # Configuration
        self._load_configuration()
        
        # Component references
        self.risk_classifier = RiskClassifier()
        self.stake_optimizer = StakeOptimizer()
        self.safety_pipeline = SafetyPipeline()
        self.emergency_stop_manager = EmergencyStopManager()
        self.arbitrage_browser = None  # Will be initialized when needed
        self.avo_tabs_interface = None  # Will be initialized when needed
        
        # State management
        self._workflows: Dict[UUID, HITLWorkflowContext] = {}
        self._approval_requests: Dict[UUID, ApprovalRequest] = {}
        self._workflow_locks: Dict[str, asyncio.Lock] = {}
        self._active_workflows: Set[UUID] = set()
        
        # Concurrency control
        self._execution_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()
        self._background_tasks: Set[asyncio.Task] = set()
        
        # Performance monitoring
        self._metrics = {
            'workflows_processed': 0,
            'workflows_completed': 0,
            'workflows_failed': 0,
            'approval_timeout_count': 0,
            'avg_workflow_duration': 0.0,
            'concurrent_workflows': 0,
            'peak_concurrent_workflows': 0
        }
        
        # Background monitoring
        self._monitoring_active = False
        
        # Signal handling for graceful shutdown
        self._setup_signal_handlers()
        
        self.logger.info("HITL Execution Orchestrator initialized")
    
    def _load_configuration(self) -> None:
        """Load HITL-specific configuration."""
        try:
            # Default configuration
            default_config = {
                'hitl': {
                    'max_concurrent_workflows': 5,
                    'approval_timeout_minutes': 5,
                    'auto_approve_tier_a': True,
                    'auto_reject_tier_d': True,
                    'enable_presentation': True,
                    'enable_monitoring': True,
                    'retry_failed_workflows': True,
                    'max_retries': 3,
                    'graceful_shutdown_timeout': 30
                }
            }
            
            # Load from config manager
            config = self.config_manager.get_config('hitl', default_config)
            self.config = config
            self.logger.debug("HITL configuration loaded", extra={'config': config})
            
        except Exception as e:
            self.logger.error("Failed to load HITL configuration", error=str(e))
            # Use defaults
            self.config = {
                'hitl': {
                    'max_concurrent_workflows': 5,
                    'approval_timeout_minutes': 5,
                    'auto_approve_tier_a': True,
                    'auto_reject_tier_d': True,
                    'enable_presentation': True,
                    'enable_monitoring': True,
                    'retry_failed_workflows': True,
                    'max_retries': 3,
                    'graceful_shutdown_timeout': 30
                }
            }
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(self.graceful_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start(self) -> None:
        """Start the HITL orchestrator and background services."""
        self.logger.info("Starting HITL Execution Orchestrator")
        
        # Start background monitoring
        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitor_workflows())
        self._background_tasks.add(self._monitor_task)
        
        # Initialize dependent components
        await self._initialize_components()
        
        self.logger.info("HITL Execution Orchestrator started successfully")
    
    async def stop(self) -> None:
        """Stop the HITL orchestrator and cleanup resources."""
        await self.graceful_shutdown()
    
    async def graceful_shutdown(self, timeout: Optional[int] = None) -> None:
        """Perform graceful shutdown of the orchestrator."""
        shutdown_timeout = timeout or self.config['hitl']['graceful_shutdown_timeout']
        
        self.logger.info("Initiating graceful shutdown", 
                        timeout_seconds=shutdown_timeout,
                        active_workflows=len(self._active_workflows))
        
        # Set shutdown flag
        self._shutdown_event.set()
        
        # Stop monitoring
        self._monitoring_active = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for background tasks to complete
        if self._background_tasks:
            await asyncio.wait_for(
                asyncio.gather(*self._background_tasks, return_exceptions=True),
                timeout=shutdown_timeout / 2
            )
        
        # Complete active workflows
        if self._active_workflows:
            self.logger.info(f"Completing {len(self._active_workflows)} active workflows")
            await self._complete_active_workflows(timeout=shutdown_timeout / 2)
        
        # Cleanup components
        await self._cleanup_components()
        
        self.logger.info("Graceful shutdown completed")
    
    async def _initialize_components(self) -> None:
        """Initialize dependent components."""
        try:
            # Initialize arbitrage browser if needed
            if self.config['hitl'].get('enable_automation', False):
                self.arbitrage_browser = ArbitrageBrowser()
                await self.arbitrage_browser.initialize()
            
            # Initialize AVO tabs interface if needed
            if self.config['hitl'].get('enable_avo_tabs', False):
                self.avo_tabs_interface = AVOTabsInterface()
                await self.avo_tabs_interface.initialize()
            
            self.logger.debug("HITL components initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize HITL components", error=str(e))
            raise
    
    async def _cleanup_components(self) -> None:
        """Cleanup dependent components."""
        try:
            if self.arbitrage_browser:
                await self.arbitrage_browser.cleanup()
            
            if self.avo_tabs_interface:
                await self.avo_tabs_interface.cleanup()
            
            self.logger.debug("HITL components cleaned up successfully")
            
        except Exception as e:
            self.logger.error("Error during component cleanup", error=str(e))
    
    async def process_opportunity(
        self, 
        opportunity: ArbitrageOpportunity,
        execution_mode: str = "manual"
    ) -> Tuple[bool, Optional[UUID], str]:
        """
        Process an arbitrage opportunity through the complete HITL workflow.
        
        Args:
            opportunity: The arbitrage opportunity to process
            execution_mode: Execution mode (manual, auto_approved, auto_rejected)
        
        Returns:
            Tuple of (success, workflow_id, message)
        """
        workflow_id = uuid4()
        
        try:
            # Create workflow context
            context = HITLWorkflowContext(
                workflow_id=workflow_id,
                opportunity_id=opportunity.id,
                opportunity=opportunity,
                execution_mode=execution_mode,
                requires_human_approval=True
            )
            
            # Add to tracking
            self._workflows[workflow_id] = context
            self._active_workflows.add(workflow_id)
            
            self.logger.info(
                "Starting HITL workflow for opportunity",
                workflow_id=str(workflow_id),
                opportunity_id=str(opportunity.id),
                risk_tier=opportunity.risk_tier,
                execution_mode=execution_mode
            )
            
            # Log workflow start
            await self._log_workflow_event(
                workflow_id, "workflow_started", 
                {"opportunity_id": str(opportunity.id), "execution_mode": execution_mode}
            )
            
            # Execute workflow
            success = await self._execute_workflow(context)
            
            if success:
                self._metrics['workflows_completed'] += 1
                message = "Workflow completed successfully"
                self.logger.info(
                    "HITL workflow completed successfully",
                    workflow_id=str(workflow_id),
                    opportunity_id=str(opportunity.id)
                )
            else:
                self._metrics['workflows_failed'] += 1
                message = "Workflow failed"
                self.logger.warning(
                    "HITL workflow failed",
                    workflow_id=str(workflow_id),
                    opportunity_id=str(opportunity.id)
                )
            
            return success, workflow_id, message
            
        except Exception as e:
            self.logger.error(
                "Error processing opportunity",
                workflow_id=str(workflow_id),
                opportunity_id=str(opportunity.id),
                error=str(e)
            )
            return False, workflow_id, f"Error: {str(e)}"
        
        finally:
            # Cleanup
            self._active_workflows.discard(workflow_id)
    
    async def _execute_workflow(self, context: HITLWorkflowContext) -> bool:
        """Execute the complete HITL workflow for a context."""
        phases = [
            WorkflowPhase.VALIDATION,
            WorkflowPhase.RISK_ASSESSMENT,
            WorkflowPhase.STAKE_CALCULATION,
            WorkflowPhase.PRESENTATION,
            WorkflowPhase.APPROVAL,
            WorkflowPhase.EXECUTION,
            WorkflowPhase.MONITORING,
            WorkflowPhase.SETTLEMENT,
            WorkflowPhase.COMPLETION
        ]
        
        for phase in phases:
            # Check if shutdown requested
            if self._shutdown_event.is_set():
                self.logger.warning("Shutdown requested during workflow execution")
                context.state = ExecutionState.STOPPED
                return False
            
            # Update phase
            context.current_phase = phase
            context.phase_started_at = datetime.utcnow()
            
            try:
                # Execute phase
                success = await self._execute_phase(context, phase)
                
                if not success:
                    self.logger.warning(
                        f"Phase {phase.value} failed",
                        workflow_id=str(context.workflow_id),
                        opportunity_id=str(context.opportunity_id)
                    )
                    context.current_phase = WorkflowPhase.FAILED
                    return False
                
                # Record phase duration
                if context.phase_started_at:
                    duration = (datetime.utcnow() - context.phase_started_at).total_seconds()
                    context.phase_durations[phase.value] = duration
                
            except Exception as e:
                self.logger.error(
                    f"Error executing phase {phase.value}",
                    workflow_id=str(context.workflow_id),
                    phase=phase.value,
                    error=str(e)
                )
                context.errors.append(f"Phase {phase.value} error: {str(e)}")
                context.current_phase = WorkflowPhase.FAILED
                return False
        
        # Mark as completed
        context.state = ExecutionState.IDLE
        context.total_duration = (datetime.utcnow() - context.started_at).total_seconds()
        
        self.logger.info(
            "Workflow completed successfully",
            workflow_id=str(context.workflow_id),
            total_duration=context.total_duration,
            phase_durations=context.phase_durations
        )
        
        return True
    
    async def _execute_phase(self, context: HITLWorkflowContext, phase: WorkflowPhase) -> bool:
        """Execute a specific workflow phase."""
        self.logger.debug(
            f"Executing phase {phase.value}",
            workflow_id=str(context.workflow_id),
            opportunity_id=str(context.opportunity_id)
        )
        
        with self.logger_utils.measure_performance(f"phase_{phase.value}"):
            if phase == WorkflowPhase.VALIDATION:
                return await self._phase_validation(context)
            elif phase == WorkflowPhase.RISK_ASSESSMENT:
                return await self._phase_risk_assessment(context)
            elif phase == WorkflowPhase.STAKE_CALCULATION:
                return await self._phase_stake_calculation(context)
            elif phase == WorkflowPhase.PRESENTATION:
                return await self._phase_presentation(context)
            elif phase == WorkflowPhase.APPROVAL:
                return await self._phase_approval(context)
            elif phase == WorkflowPhase.EXECUTION:
                return await self._phase_execution(context)
            elif phase == WorkflowPhase.MONITORING:
                return await self._phase_monitoring(context)
            elif phase == WorkflowPhase.SETTLEMENT:
                return await self._phase_settlement(context)
            elif phase == WorkflowPhase.COMPLETION:
                return await self._phase_completion(context)
            else:
                self.logger.error(f"Unknown phase: {phase}")
                return False
    
    async def _phase_validation(self, context: HITLWorkflowContext) -> bool:
        """Phase 1: Validate opportunity."""
        try:
            opportunity = context.opportunity
            
            # Check if emergency stop is active
            if self.emergency_stop_manager.is_emergency_stop_active():
                raise EmergencyStopTriggered("Emergency stop is active")
            
            # Validate opportunity data
            if not opportunity.legs or len(opportunity.legs) < 2:
                context.errors.append("Invalid opportunity: insufficient legs")
                return False
            
            # Check opportunity freshness
            if opportunity.expires_at and datetime.utcnow() > opportunity.expires_at:
                context.errors.append("Opportunity has expired")
                return False
            
            # Run safety validation pipeline
            validation_result = await self.safety_pipeline.validate_opportunity(opportunity)
            if not validation_result.is_valid:
                context.errors.extend(validation_result.errors)
                return False
            
            self.logger.debug(
                "Opportunity validation passed",
                workflow_id=str(context.workflow_id),
                opportunity_id=str(context.opportunity_id)
            )
            
            return True
            
        except Exception as e:
            context.errors.append(f"Validation error: {str(e)}")
            return False
    
    async def _phase_risk_assessment(self, context: HITLWorkflowContext) -> bool:
        """Phase 2: Assess risk of opportunity."""
        try:
            opportunity = context.opportunity
            
            # Classify risk tier
            risk_analysis = await self.risk_classifier.classify_risk(opportunity)
            opportunity.risk_tier = risk_analysis.tier
            
            # Check if automatic actions based on tier
            if opportunity.risk_tier == RiskTier.TIER_D and self.config['hitl']['auto_reject_tier_d']:
                context.errors.append("Opportunity rejected due to high risk (Tier D)")
                return False
            
            self.logger.debug(
                "Risk assessment completed",
                workflow_id=str(context.workflow_id),
                risk_tier=opportunity.risk_tier.value
            )
            
            return True
            
        except Exception as e:
            context.errors.append(f"Risk assessment error: {str(e)}")
            return False
    
    async def _phase_stake_calculation(self, context: HITLWorkflowContext) -> bool:
        """Phase 3: Calculate optimal stakes."""
        try:
            opportunity = context.opportunity
            
            # Calculate optimal stakes
            stake_result = await self.stake_optimizer.calculate_stakes(opportunity)
            
            if not stake_result.is_valid:
                context.errors.extend(stake_result.errors)
                return False
            
            # Update opportunity with calculated stakes
            for leg, allocation in zip(opportunity.legs, stake_result.leg_allocations):
                leg.actual_stake = allocation.amount
            
            opportunity.total_stake = stake_result.total_stake
            
            self.logger.debug(
                "Stake calculation completed",
                workflow_id=str(context.workflow_id),
                total_stake=str(opportunity.total_stake)
            )
            
            return True
            
        except Exception as e:
            context.errors.append(f"Stake calculation error: {str(e)}")
            return False
    
    async def _phase_presentation(self, context: HITLWorkflowContext) -> bool:
        """Phase 4: Present opportunity to user."""
        if not self.config['hitl']['enable_presentation']:
            return True
        
        try:
            opportunity = context.opportunity
            
            # Create presentation data
            presentation_data = {
                'workflow_id': str(context.workflow_id),
                'opportunity_id': str(opportunity.id),
                'event_name': opportunity.event_name,
                'sport': opportunity.sport.value,
                'risk_tier': opportunity.risk_tier.value,
                'profit_margin': str(opportunity.profit_margin),
                'expected_profit': str(opportunity.profit_amount),
                'total_stake': str(opportunity.total_stake),
                'legs': [
                    {
                        'bookmaker': leg.bookmaker,
                        'outcome': leg.event_outcome,
                        'odds': str(leg.odds),
                        'stake': str(leg.actual_stake)
                    }
                    for leg in opportunity.legs
                ],
                'created_at': opportunity.created_at.isoformat()
            }
            
            # Log presentation event
            await self._log_workflow_event(
                context.workflow_id, "opportunity_presented", presentation_data
            )
            
            self.logger.info(
                "Opportunity presented to user",
                workflow_id=str(context.workflow_id),
                opportunity_id=str(opportunity.id)
            )
            
            return True
            
        except Exception as e:
            context.errors.append(f"Presentation error: {str(e)}")
            return False
    
    async def _phase_approval(self, context: HITLWorkflowContext) -> bool:
        """Phase 5: Request and handle human approval."""
        opportunity = context.opportunity
        
        # Check automatic approval based on tier
        if opportunity.risk_tier == RiskTier.TIER_A and self.config['hitl']['auto_approve_tier_a']:
            context.approval_status = ApprovalStatus.APPROVED
            context.approval_requested = False
            self.logger.debug(
                "Auto-approved Tier A opportunity",
                workflow_id=str(context.workflow_id)
            )
            return True
        
        # Create approval request
        approval_request = ApprovalRequest(
            workflow_id=context.workflow_id,
            opportunity_id=context.opportunity_id,
            message=f"Approval needed for arbitrage opportunity: {opportunity.event_name}",
            details={
                'risk_tier': opportunity.risk_tier.value,
                'expected_profit': str(opportunity.profit_amount),
                'total_stake': str(opportunity.total_stake),
                'profit_margin': str(opportunity.profit_margin)
            },
            risk_tier=opportunity.risk_tier,
            expected_profit=float(opportunity.profit_amount),
            total_stake=float(opportunity.total_stake),
            bookmakers=[leg.bookmaker for leg in opportunity.legs]
        )
        
        # Add to tracking
        self._approval_requests[approval_request.request_id] = approval_request
        context.approval_requested = True
        context.approval_status = ApprovalStatus.PENDING
        context.approval_requested_at = datetime.utcnow()
        context.approval_expires_at = approval_request.expires_at
        
        # Log approval request
        await self._log_workflow_event(
            context.workflow_id, "approval_requested",
            {
                'request_id': str(approval_request.request_id),
                'expires_at': approval_request.expires_at.isoformat()
            }
        )
        
        self.logger.info(
            "Approval request created",
            workflow_id=str(context.workflow_id),
            request_id=str(approval_request.request_id),
            expires_at=approval_request.expires_at.isoformat()
        )
        
        # Wait for approval with timeout
        try:
            approval_result = await self._wait_for_approval(
                context.workflow_id,
                timeout_seconds=self.config['hitl']['approval_timeout_minutes'] * 60
            )
            
            return approval_result
            
        except ApprovalTimeoutError:
            context.approval_status = ApprovalStatus.TIMEOUT
            self._metrics['approval_timeout_count'] += 1
            context.errors.append("Approval request timed out")
            return False
    
    async def _phase_execution(self, context: HITLWorkflowContext) -> bool:
        """Phase 6: Execute the trades."""
        try:
            opportunity = context.opportunity
            
            # Check if automation is enabled
            if not self.arbitrage_browser:
                self.logger.warning("Arbitrage browser not available, marking for manual execution")
                return True
            
            # Execute trades using arbitrage browser
            execution_result = await self.arbitrage_browser.execute_arbitrage_opportunity(
                opportunity
            )
            
            if execution_result.success:
                context.trade_id = execution_result.trade_id
                self.logger.info(
                    "Trades executed successfully",
                    workflow_id=str(context.workflow_id),
                    trade_id=str(execution_result.trade_id)
                )
                return True
            else:
                context.errors.extend(execution_result.errors)
                return False
            
        except Exception as e:
            context.errors.append(f"Execution error: {str(e)}")
            return False
    
    async def _phase_monitoring(self, context: HITLWorkflowContext) -> bool:
        """Phase 7: Monitor execution progress."""
        if not self.config['hitl']['enable_monitoring']:
            return True
        
        try:
            opportunity = context.opportunity
            
            # Monitor execution if we have a trade
            if context.trade_id and self.arbitrage_browser:
                monitoring_result = await self.arbitrage_browser.monitor_trade_progress(
                    context.trade_id
                )
                
                if monitoring_result.is_complete:
                    self.logger.info(
                        "Trade monitoring completed",
                        workflow_id=str(context.workflow_id),
                        trade_id=str(context.trade_id)
                    )
                    return True
                else:
                    # Continue monitoring
                    await asyncio.sleep(1)
                    return await self._phase_monitoring(context)
            else:
                # No trade to monitor
                return True
            
        except Exception as e:
            context.errors.append(f"Monitoring error: {str(e)}")
            return False
    
    async def _phase_settlement(self, context: HITLWorkflowContext) -> bool:
        """Phase 8: Handle trade settlement."""
        try:
            # This would typically wait for bets to settle
            # For now, we'll mark as complete
            
            if context.trade_id and self.arbitrage_browser:
                settlement_result = await self.arbitrage_browser.check_trade_settlement(
                    context.trade_id
                )
                
                if settlement_result.is_settled:
                    self.logger.info(
                        "Trade settled successfully",
                        workflow_id=str(context.workflow_id),
                        trade_id=str(context.trade_id)
                    )
                    return True
                else:
                    # Settlement pending, wait and retry
                    await asyncio.sleep(5)
                    return await self._phase_settlement(context)
            else:
                # No trade to settle
                return True
            
        except Exception as e:
            context.errors.append(f"Settlement error: {str(e)}")
            return False
    
    async def _phase_completion(self, context: HITLWorkflowContext) -> bool:
        """Phase 9: Complete workflow and cleanup."""
        try:
            # Log completion
            await self._log_workflow_event(
                context.workflow_id, "workflow_completed",
                {
                    'total_duration': context.total_duration,
                    'phase_durations': context.phase_durations
                }
            )
            
            # Update metrics
            self._metrics['workflows_processed'] += 1
            
            # Cleanup approval requests
            for request_id, request in list(self._approval_requests.items()):
                if request.workflow_id == context.workflow_id:
                    del self._approval_requests[request_id]
            
            self.logger.info(
                "Workflow completion phase finished",
                workflow_id=str(context.workflow_id),
                total_duration=context.total_duration
            )
            
            return True
            
        except Exception as e:
            context.errors.append(f"Completion error: {str(e)}")
            return False
    
    async def _wait_for_approval(self, workflow_id: UUID, timeout_seconds: int) -> bool:
        """Wait for human approval with timeout."""
        context = self._workflows[workflow_id]
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            # Check shutdown event
            if self._shutdown_event.is_set():
                return False
            
            # Check approval status
            if context.approval_status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
                return context.approval_status == ApprovalStatus.APPROVED
            
            # Sleep briefly
            await asyncio.sleep(0.1)
        
        # Timeout
        raise ApprovalTimeoutError(f"Approval timeout after {timeout_seconds} seconds")
    
    async def approve_opportunity(self, workflow_id: UUID, approved: bool, reviewer: str = "system") -> bool:
        """Approve or reject a workflow opportunity."""
        if workflow_id not in self._workflows:
            self.logger.error(f"Workflow not found: {workflow_id}")
            return False
        
        context = self._workflows[workflow_id]
        
        if not context.approval_requested:
            self.logger.warning(f"No approval requested for workflow: {workflow_id}")
            return False
        
        # Update approval status
        if approved:
            context.approval_status = ApprovalStatus.APPROVED
        else:
            context.approval_status = ApprovalStatus.REJECTED
        
        context.approval_requested_at = datetime.utcnow()
        context.stakeholders.add(reviewer)
        
        # Find and update corresponding approval request
        for request in self._approval_requests.values():
            if request.workflow_id == workflow_id:
                request.status = context.approval_status
                request.responded_at = datetime.utcnow()
                request.human_reviewer = reviewer
                break
        
        # Log approval event
        await self._log_workflow_event(
            workflow_id, "approval_response",
            {
                'approved': approved,
                'reviewer': reviewer,
                'status': context.approval_status.value
            }
        )
        
        self.logger.info(
            f"Workflow {'approved' if approved else 'rejected'}",
            workflow_id=str(workflow_id),
            approved=approved,
            reviewer=reviewer
        )
        
        return True
    
    async def _monitor_workflows(self) -> None:
        """Background task to monitor workflows and handle timeouts."""
        while self._monitoring_active:
            try:
                current_time = datetime.utcnow()
                
                # Check for expired approval requests
                expired_requests = []
                for request_id, request in self._approval_requests.items():
                    if (request.status == ApprovalStatus.PENDING and 
                        current_time > request.expires_at):
                        expired_requests.append(request_id)
                
                # Handle expired requests
                for request_id in expired_requests:
                    request = self._approval_requests[request_id]
                    context = self._workflows.get(request.workflow_id)
                    
                    if context:
                        context.approval_status = ApprovalStatus.EXPIRED
                        request.status = ApprovalStatus.EXPIRED
                        
                        # Log expiration
                        await self._log_workflow_event(
                            request.workflow_id, "approval_expired",
                            {'request_id': str(request_id)}
                        )
                        
                        self.logger.warning(
                            "Approval request expired",
                            workflow_id=str(request.workflow_id),
                            request_id=str(request_id)
                        )
                
                # Clean up expired requests
                for request_id in expired_requests:
                    del self._approval_requests[request_id]
                
                # Update metrics
                self._metrics['concurrent_workflows'] = len(self._active_workflows)
                self._metrics['peak_concurrent_workflows'] = max(
                    self._metrics['peak_concurrent_workflows'],
                    len(self._active_workflows)
                )
                
                # Sleep
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error("Error in workflow monitoring", error=str(e))
                await asyncio.sleep(5)
    
    async def _complete_active_workflows(self, timeout: float) -> None:
        """Complete all active workflows during shutdown."""
        start_time = time.time()
        
        # Complete workflows concurrently
        tasks = []
        for workflow_id in list(self._active_workflows):
            context = self._workflows.get(workflow_id)
            if context and context.state == ExecutionState.ACTIVE:
                task = asyncio.create_task(self._complete_workflow_safely(workflow_id))
                tasks.append(task)
        
        if tasks:
            # Wait for completion with timeout
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
        
        elapsed = time.time() - start_time
        self.logger.info(f"Completed {len(tasks)} workflows in {elapsed:.2f} seconds")
    
    async def _complete_workflow_safely(self, workflow_id: UUID) -> None:
        """Safely complete a workflow during shutdown."""
        try:
            context = self._workflows.get(workflow_id)
            if not context:
                return
            
            context.state = ExecutionState.STOPPED
            self._active_workflows.discard(workflow_id)
            
            self.logger.debug(
                "Workflow completed during shutdown",
                workflow_id=str(workflow_id)
            )
            
        except Exception as e:
            self.logger.error(
                "Error completing workflow during shutdown",
                workflow_id=str(workflow_id),
                error=str(e)
            )
    
    async def _log_workflow_event(self, workflow_id: UUID, event_type: str, details: Dict[str, Any]) -> None:
        """Log workflow events to audit trail."""
        try:
            await self.audit_logger.log_user_action(
                action=f"hitl_workflow_{event_type}",
                resource=f"workflow:{workflow_id}",
                details={
                    'workflow_id': str(workflow_id),
                    'event_type': event_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    **details
                }
            )
        except Exception as e:
            self.logger.error("Failed to log workflow event", error=str(e))
    
    # Public API methods
    def get_workflow_status(self, workflow_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the current status of a workflow."""
        context = self._workflows.get(workflow_id)
        if not context:
            return None
        
        return {
            'workflow_id': str(context.workflow_id),
            'opportunity_id': str(context.opportunity_id),
            'current_phase': context.current_phase.value,
            'state': context.state.value,
            'approval_status': context.approval_status.value if context.approval_status else None,
            'started_at': context.started_at.isoformat(),
            'phase_started_at': context.phase_started_at.isoformat() if context.phase_started_at else None,
            'errors': context.errors,
            'retry_count': context.retry_count,
            'phase_durations': context.phase_durations
        }
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows."""
        return [
            self.get_workflow_status(workflow_id)
            for workflow_id in self._active_workflows
            if self.get_workflow_status(workflow_id)
        ]
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests."""
        return [
            {
                'request_id': str(req.request_id),
                'workflow_id': str(req.workflow_id),
                'opportunity_id': str(req.opportunity_id),
                'message': req.message,
                'priority': req.priority,
                'created_at': req.created_at.isoformat(),
                'expires_at': req.expires_at.isoformat(),
                'risk_tier': req.risk_tier.value if req.risk_tier else None,
                'expected_profit': req.expected_profit,
                'total_stake': req.total_stake,
                'bookmakers': req.bookmakers
            }
            for req in self._approval_requests.values()
            if req.status == ApprovalStatus.PENDING
        ]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance metrics."""
        # Calculate average workflow duration
        completed_durations = []
        for context in self._workflows.values():
            if context.total_duration:
                completed_durations.append(context.total_duration)
        
        if completed_durations:
            self._metrics['avg_workflow_duration'] = sum(completed_durations) / len(completed_durations)
        
        return self._metrics.copy()
    
    def cancel_workflow(self, workflow_id: UUID) -> bool:
        """Cancel an active workflow."""
        if workflow_id not in self._workflows:
            return False
        
        context = self._workflows[workflow_id]
        context.current_phase = WorkflowPhase.CANCELLED
        context.state = ExecutionState.STOPPED
        self._active_workflows.discard(workflow_id)
        
        self.logger.info(
            "Workflow cancelled",
            workflow_id=str(workflow_id)
        )
        
        return True
    
    def pause_workflow(self, workflow_id: UUID) -> bool:
        """Pause an active workflow."""
        if workflow_id not in self._workflows:
            return False
        
        context = self._workflows[workflow_id]
        if context.state == ExecutionState.ACTIVE:
            context.state = ExecutionState.PAUSED
            self.logger.info(
                "Workflow paused",
                workflow_id=str(workflow_id)
            )
            return True
        
        return False
    
    def resume_workflow(self, workflow_id: UUID) -> bool:
        """Resume a paused workflow."""
        if workflow_id not in self._workflows:
            return False
        
        context = self._workflows[workflow_id]
        if context.state == ExecutionState.PAUSED:
            context.state = ExecutionState.ACTIVE
            self.logger.info(
                "Workflow resumed",
                workflow_id=str(workflow_id)
            )
            return True
        
        return False


# Global orchestrator instance
_orchestrator_instance: Optional[HITLExecutionOrchestrator] = None
_instance_lock = asyncio.Lock()


async def get_hitl_orchestrator() -> HITLExecutionOrchestrator:
    """Get or create the global HITL orchestrator instance."""
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        async with _instance_lock:
            if _orchestrator_instance is None:
                _orchestrator_instance = HITLExecutionOrchestrator()
                await _orchestrator_instance.start()
    
    return _orchestrator_instance


def get_hitl_orchestrator_sync() -> HITLExecutionOrchestrator:
    """Synchronous version to get the HITL orchestrator."""
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        raise RuntimeError("HITL orchestrator not initialized. Call get_hitl_orchestrator() first.")
    
    return _orchestrator_instance


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def main():
        """Example usage of the HITL Execution Orchestrator."""
        
        # Initialize orchestrator
        orchestrator = HITLExecutionOrchestrator()
        await orchestrator.start()
        
        try:
            # Create a sample arbitrage opportunity
            opportunity = ArbitrageOpportunity(
                sport=Sport.FOOTBALL,
                event_name="Liverpool vs Manchester United",
                event_date=datetime.utcnow() + timedelta(days=1),
                market_type="match_winner",
                legs=[
                    ArbitrageLeg(
                        bookmaker="bet365",
                        event_outcome="Liverpool",
                        odds=Decimal("2.10"),
                        implied_probability=Decimal("0.4762"),
                        stake_percentage=Decimal("0.5"),
                        actual_stake=Decimal("100.00"),
                        potential_payout=Decimal("210.00")
                    ),
                    ArbitrageLeg(
                        bookmaker="william_hill",
                        event_outcome="Manchester United",
                        odds=Decimal("2.05"),
                        implied_probability=Decimal("0.4878"),
                        stake_percentage=Decimal("0.5"),
                        actual_stake=Decimal("100.00"),
                        potential_payout=Decimal("205.00")
                    )
                ],
                total_stake=Decimal("200.00"),
                profit_margin=Decimal("0.025"),
                profit_amount=Decimal("5.00"),
                risk_tier=RiskTier.TIER_A,
                source_scanner="test_scanner"
            )
            
            # Process opportunity
            success, workflow_id, message = await orchestrator.process_opportunity(
                opportunity,
                execution_mode="manual"
            )
            
            print(f"Workflow {'succeeded' if success else 'failed'}: {message}")
            print(f"Workflow ID: {workflow_id}")
            
            # Get status
            status = orchestrator.get_workflow_status(workflow_id)
            print(f"Workflow status: {status}")
            
            # Get pending approvals
            pending = orchestrator.get_pending_approvals()
            print(f"Pending approvals: {pending}")
            
            # Simulate approval
            if pending:
                approval_request = pending[0]
                await orchestrator.approve_opportunity(
                    UUID(approval_request['workflow_id']),
                    approved=True,
                    reviewer="test_user"
                )
            
            # Get metrics
            metrics = orchestrator.get_metrics()
            print(f"Metrics: {metrics}")
            
        finally:
            await orchestrator.stop()
    
    # Run example
    asyncio.run(main())
