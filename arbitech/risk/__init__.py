"""
Advanced Risk Management System for Arbitech
Comprehensive bankroll management and sophisticated stake calculation using Kelly criterion,
advanced optimization algorithms, and professional position sizing strategies.
"""

# Try to import existing functionality (if available)
try:
    from .bankroll_validator import BankrollValidator
    from .limit_manager import LimitManager
    from .exposure_tracker import ExposureTracker
    from arbitech.risk.validation_engine import ValidationEngine
    EXISTING_MODULES_AVAILABLE = True
except ImportError:
    # Create dummy classes if modules don't exist
    class BankrollValidator:
        pass
    class LimitManager:
        pass
    class ExposureTracker:
        pass
    class ValidationEngine:
        pass
    EXISTING_MODULES_AVAILABLE = False

# Import Kelly Criterion and Advanced Stake Calculation System
from .kelly_calculator import (
    KellyCalculator,
    KellyConfig,
    KellyFraction,
    MultiOutcomeKellyResult,
    DynamicKellyResult,
    PortfolioKellyResult
)

from .stake_optimizer import (
    StakeOptimizer,
    OptimizationConfig,
    OptimizationStrategy,
    OptimizationResult,
    ConstraintSet,
    MultiStrategyResult
)

from .position_sizer import (
    PositionSizer,
    PositionConfig,
    PositionSize,
    PositionLimit,
    LiquidityConstraint,
    DiversificationConstraint,
    CorrelationAdjustment
)

from .bankroll_manager import (
    BankrollManager,
    BankrollConfig,
    GrowthModel,
    DrawdownProtection,
    PerformanceTracker,
    CapitalPreservation
)

__all__ = [
    # Existing functionality (if available)
    *(['BankrollValidator', 'LimitManager', 'ExposureTracker', 'ValidationEngine'] 
      if EXISTING_MODULES_AVAILABLE else []),
    
    # Kelly Calculator
    'KellyCalculator',
    'KellyConfig',
    'KellyFraction',
    'MultiOutcomeKellyResult',
    'DynamicKellyResult',
    'PortfolioKellyResult',
    
    # Stake Optimizer
    'StakeOptimizer',
    'OptimizationConfig',
    'OptimizationStrategy',
    'OptimizationResult',
    'ConstraintSet',
    'MultiStrategyResult',
    
    # Position Sizer
    'PositionSizer',
    'PositionConfig',
    'PositionSize',
    'PositionLimit',
    'LiquidityConstraint',
    'DiversificationConstraint',
    'CorrelationAdjustment',
    
    # Bankroll Manager
    'BankrollManager',
    'BankrollConfig',
    'GrowthModel',
    'DrawdownProtection',
    'PerformanceTracker',
    'CapitalPreservation',
    
    # System info
    'EXISTING_MODULES_AVAILABLE'
]

__version__ = "1.0.0"