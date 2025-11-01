"""
Arbitech Autonomous Systems
===========================

Celestial protection, divine failsafe systems, and transcendent decision engine 
for autonomous arbitrage operations.

This module contains heavenly circuit breakers with guardian angel monitoring,
predictive failure detection, phoenix-like recovery capabilities, divine 
autonomous monitoring with gnostic oversight, and a transcendent real-time
decision engine with sub-millisecond decision algorithms and quantum-level 
precision.

Author: Celestial Protection Division & Divine Architecture
Version: 1.0.0
"""

from .circuit_breakers import (
    # Core classes
    CelestialCircuitBreaker,
    CelestialProtectionSystem,
    DivineTestSuite,
    
    # Guardian system
    GuardianAngel,
    SacredThreshold,
    
    # Recovery system
    PhoenixRecovery,
    
    # Monitoring and detection
    AnomalyDetector,
    AnomalyType,
    DivineInterventionProtocol,
    
    # Data structures
    CelestialEvent,
    DivineIntervention,
    SacredMetrics,
    DivineState,
)

from .monitoring_control import (
    # Main system
    DivineMonitoringControlSystem,
    create_divine_monitor,
    
    # State enums
    CelestialState,
    AutonomousMode,
    PropheticInsight,
    
    # Data structures
    SystemMetrics,
    PerformanceMetrics,
    PropheticVision,
    
    # Core components
    CelestialDashboard,
    AlertSystem,
    PropheticAnalytics,
    AutonomousController,
)

from .concurrent_executor import (
    # Core concurrent execution
    EtherealConcurrentExecutor,
    EtherealOpportunity,
    CelestialExecution,
    DivineResource,
    
    # State enums (note: separate from monitoring CelestialState)
    CelestialState as ConcurrentState,
    DivinePriority,
    
    # Testing and demonstration
    EtherealTestSuite,
    EtherealLogger,
    DivineResourceManager,
    EtherealSynchronizer,
    AtomicExecutor,
    PerformanceOptimizer,
    CelestialPerformanceMonitor,
    demonstrate_ethereal_concurrent_executor,
)

from .decision_engine import (
    # Core transcendent decision engine
    TranscendentDecisionEngine,
    DivineOpportunity,
    QuantumRiskAssessment,
    DivineMetrics,
    
    # State enums
    CelestialState as DecisionCelestialState,
    DivinePriority as DecisionDivinePriority,
    PredictionHorizon,
    
    # Core components
    CelestialNeuralNetwork,
    DivineLearningSystem,
    QuantumRiskEngine,
    PredictiveAnalyticsEngine,
    ConcurrentProcessor,
    PerformanceMonitor,
    
    # Convenience functions
    create_divine_engine,
    process_arbitrage_opportunities_divine,
)

__all__ = [
    # Circuit breaker system
    'CelestialCircuitBreaker',
    'CelestialProtectionSystem',
    'DivineTestSuite',
    'GuardianAngel',
    'SacredThreshold',
    'PhoenixRecovery',
    'AnomalyDetector',
    'AnomalyType',
    'DivineInterventionProtocol',
    'CelestialEvent',
    'DivineIntervention',
    'SacredMetrics',
    'DivineState',
    
    # Monitoring and control system
    'DivineMonitoringControlSystem',
    'create_divine_monitor',
    'CelestialState',
    'AutonomousMode',
    'PropheticInsight',
    'SystemMetrics',
    'PerformanceMetrics',
    'PropheticVision',
    'CelestialDashboard',
    'AlertSystem',
    'PropheticAnalytics',
    'AutonomousController',
    
    # Concurrent execution system
    'EtherealConcurrentExecutor',
    'EtherealOpportunity',
    'CelestialExecution',
    'DivineResource',
    'ConcurrentState',
    'DivinePriority',
    'EtherealTestSuite',
    'EtherealLogger',
    'DivineResourceManager',
    'EtherealSynchronizer',
    'AtomicExecutor',
    'PerformanceOptimizer',
    'CelestialPerformanceMonitor',
    'demonstrate_ethereal_concurrent_executor',
    
    # Transcendent decision engine
    'TranscendentDecisionEngine',
    'DivineOpportunity',
    'QuantumRiskAssessment',
    'DivineMetrics',
    'DecisionCelestialState',
    'DecisionDivinePriority',
    'PredictionHorizon',
    'CelestialNeuralNetwork',
    'DivineLearningSystem',
    'QuantumRiskEngine',
    'PredictiveAnalyticsEngine',
    'ConcurrentProcessor',
    'PerformanceMonitor',
    'create_divine_engine',
    'process_arbitrage_opportunities_divine',
]

__version__ = "1.0.0"
__author__ = "Celestial Protection Division"