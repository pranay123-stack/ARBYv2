"""
Human-in-the-Loop (HITL) Module

This module provides human oversight and intervention capabilities for the arbitrage trading system,
including timeout management, manual override systems, and decision support interfaces.

Components:
- Execution Orchestrator: Main coordination component for HITL workflow
- Timeout Management: Sophisticated timeout handling for opportunities
- Manual Override: Human intervention capabilities  
- Decision Support: Tools to help humans make informed decisions
- Monitoring: Real-time oversight and alerting systems
- Opportunity Presentation: User-facing opportunity display
- Approval Processing: User approval/rejection handling
- Result Logging: Trade outcome logging and persistence

Integration Points:
- ConfigManager: Configuration loading and management
- AuditLogger: Comprehensive audit trails and logging
- DetectionScanner: Phase 3 opportunity detection
- RiskValidator: Phase 4 risk assessment and validation
- AutomationExecutor: Phase 5 trade execution

Usage:
    from arbitech.hitl import HITLOrchestrator, WorkflowState
    
    orchestrator = HITLOrchestrator(config, audit_logger, ...)
    await orchestrator.start()
    
For a complete example, see demo_orchestrator.py
"""

from .timeout_manager import (
    TimeoutManager,
    TimeoutRule,
    TimeoutEvent,
    TimeoutMetrics,
    TimeoutStatus,
    TimeoutSeverity,
    EscalationAction,
    create_timeout_manager_from_config,
    integrate_with_opportunity_scanner,
    integrate_with_arbitrage_executor
)

from .result_logger import (
    ResultLogger,
    HumanDecision,
    TradeResult,
    PerformanceMetrics,
    UserInteractionPattern,
    DecisionType,
    TradeOutcome,
    InteractionPattern,
    get_result_logger,
    log_human_decision,
    log_trade_result,
    get_performance_dashboard
)

from .execution_orchestrator import (
    HITLOrchestrator,
    WorkflowState,
    OpportunityState,
    OrchestratorConfig,
    HitlError,
    OrchestratorError,
    TimeoutError,
    ApprovalError,
    ExecutionError
)

from .presenter import (
    OpportunityPresenter,
    PresentationFormat,
    PresentationConfig
)

from .approval_handler import (
    ApprovalHandler,
    ApprovalData,
    RejectionData,
    ApprovalResult
)

from .opportunity_presenter import (
    # Main system classes
    OpportunityPresenterSystem,
    OpportunityPresenterInterface,
    
    # Presenter implementations
    ConsolePresenter,
    WebPresenter,
    GUIPresenter,
    
    # Supporting classes
    OpportunityRanker,
    HistoricalDataStore,
    OpportunityMetrics,
    ComparisonData,
    HistoricalPerformance,
    
    # Data structures and enums
    DisplayFormat,
    OpportunityPriority,
    PresentationEventType,
    PresentationEvent,
    
    # Utility functions
    create_hitl_presenter,
    demo_hitl_presenter
)

__all__ = [
    # Core Orchestrator
    'HITLOrchestrator',
    'WorkflowState',
    'OpportunityState',
    'OrchestratorConfig',
    'HitlError',
    'OrchestratorError',
    'TimeoutError',
    'ApprovalError',
    'ExecutionError',
    
    # Presentation
    'OpportunityPresenter',
    'PresentationFormat',
    'PresentationConfig',
    
    # Approval Processing
    'ApprovalHandler',
    'ApprovalData',
    'RejectionData',
    'ApprovalResult',
    
    # Timeout Management
    'TimeoutManager',
    'TimeoutRule', 
    'TimeoutEvent',
    'TimeoutMetrics',
    'TimeoutStatus',
    'TimeoutSeverity',
    'EscalationAction',
    'create_timeout_manager_from_config',
    'integrate_with_opportunity_scanner',
    'integrate_with_arbitrage_executor',
    
    # Result Logging
    'ResultLogger',
    'HumanDecision', 
    'TradeResult',
    'PerformanceMetrics',
    'UserInteractionPattern',
    'DecisionType',
    'TradeOutcome', 
    'InteractionPattern',
    'get_result_logger',
    'log_human_decision',
    'log_trade_result',
    'get_performance_dashboard',
    
    # Opportunity Presentation System
    'OpportunityPresenterSystem',
    'OpportunityPresenterInterface',
    'ConsolePresenter',
    'WebPresenter',
    'GUIPresenter',
    'OpportunityRanker',
    'HistoricalDataStore',
    'OpportunityMetrics',
    'ComparisonData',
    'HistoricalPerformance',
    'DisplayFormat',
    'OpportunityPriority',
    'PresentationEventType',
    'PresentationEvent',
    'create_hitl_presenter',
    'demo_hitl_presenter'
]

__version__ = "1.0.0"
__author__ = "Arbitech Trading System"


# Convenience functions for quick initialization
def create_orchestrator(
    config_path: str = None,
    max_concurrent: int = 10,
    enable_recovery: bool = True,
    **kwargs
) -> HITLOrchestrator:
    """
    Convenience function to create and initialize a HITL orchestrator.
    
    Args:
        config_path: Path to configuration file
        max_concurrent: Maximum concurrent opportunities to process
        enable_recovery: Whether to enable error recovery
        **kwargs: Additional configuration parameters
        
    Returns:
        Initialized HITLOrchestrator instance
        
    Example:
        orchestrator = create_orchestrator(
            config_path="config.yaml",
            max_concurrent=20,
            enable_recovery=True
        )
        await orchestrator.start()
    """
    # Create configuration
    orchestrator_config = OrchestratorConfig(
        max_concurrent_opportunities=max_concurrent,
        enable_recovery=enable_recovery,
        **kwargs
    )
    
    # Create orchestrator (components would be injected in real usage)
    orchestrator = HITLOrchestrator(config=orchestrator_config)
    
    return orchestrator


def quick_demo():
    """
    Run a quick demonstration of the HITL system.
    
    This function creates a simple demo showing basic HITL functionality
    without requiring external dependencies.
    """
    print_banner()
    print("Running quick HITL demo...")
    print("For full demo, run: python demo_orchestrator.py")
    
    # Create basic orchestrator
    config = OrchestratorConfig(
        max_concurrent_opportunities=5,
        enable_recovery=True
    )
    
    orchestrator = HITLOrchestrator(config=config)
    
    print(f"Created HITL orchestrator with config:")
    print(f"  - Max concurrent opportunities: {config.max_concurrent_opportunities}")
    print(f"  - Enable recovery: {config.enable_recovery}")
    print(f"  - Processing timeout: {config.processing_timeout}s")
    print("\nDemo completed. Use demo_orchestrator.py for full demonstration.")


def print_banner():
    """Print a welcome banner for the HITL system."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                     HITL Execution Orchestrator               ║
    ║              Human-in-the-Loop Trading System                ║
    ║                                                               ║
    ║  Version: {version:<47} ║
    ║  Author:  {author:<47} ║
    ║                                                               ║
    ║  Phase 3-5 Integration: Detection → Risk → Execution         ║
    ╚═══════════════════════════════════════════════════════════════╝
    """.format(version=__version__, author=__author__)
    print(banner)


def get_version() -> str:
    """Get the version of the HITL module."""
    return __version__