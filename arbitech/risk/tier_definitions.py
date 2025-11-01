"""
Risk Tier Definitions for Arbitrage Trading System

This module provides comprehensive risk tier definitions with detailed criteria,
mathematical thresholds, and validation rules for the A, B, C, D risk classification system.

Each risk tier represents a different level of acceptable risk with corresponding
thresholds for market volatility, bookmaker reliability, liquidity depth, 
execution difficulty, and timing sensitivity.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
import logging
import math


class RiskToleranceLevel(str, Enum):
    """User-defined risk tolerance levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    INSTITUTIONAL = "institutional"


class MarketCondition(str, Enum):
    """Market conditions affecting risk assessment."""
    CALM = "calm"  # Low volatility, stable odds
    NORMAL = "normal"  # Standard market conditions
    VOLATILE = "volatile"  # High volatility, changing odds
    STRESSED = "stressed"  # Extreme volatility, market disruption
    EMERGENCY = "emergency"  # Crisis conditions


class ConfidenceLevel(str, Enum):
    """Confidence levels for risk assessments."""
    LOW = "low"  # 60-70% confidence
    MEDIUM = "medium"  # 70-85% confidence
    HIGH = "high"  # 85-95% confidence
    VERY_HIGH = "very_high"  # 95%+ confidence


@dataclass
class RiskTierCriteria:
    """Detailed criteria for a specific risk tier."""
    tier_id: str
    name: str
    description: str
    
    # Mathematical thresholds
    min_profit_margin: Decimal
    max_profit_margin: Decimal
    min_liquidity_score: Decimal
    max_execution_time: timedelta
    max_odds_deviation: Decimal
    max_volatility_score: Decimal
    min_confidence_score: Decimal
    
    # Bookmaker requirements
    min_bookmaker_reliability: Decimal
    min_bookmaker_rating: Decimal
    required_bookmaker_count: int
    max_bookmaker_risk_weight: Decimal
    
    # Market conditions
    acceptable_market_conditions: List[MarketCondition]
    max_market_impact_factor: Decimal
    min_market_depth: Decimal
    
    # Execution requirements
    min_slippage_tolerance: Decimal
    max_cancellation_risk: Decimal
    min_fill_probability: Decimal
    
    # Timing constraints
    max_odds_age: timedelta
    min_time_to_event: timedelta
    max_processing_time: timedelta
    
    # Risk limits
    max_position_size: Decimal
    max_exposure_per_opportunity: Decimal
    max_daily_exposure: Decimal
    max_concurrent_opportunities: int
    
    # Quality metrics
    min_success_rate: Decimal
    max_drawdown_tolerance: Decimal
    min_sharpe_ratio: Decimal
    max_var_95: Decimal
    
    # Stress test requirements
    stress_test_pass_rate: Decimal
    monte_carlo_success_threshold: Decimal
    scenario_analysis_score: Decimal
    
    # Additional metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    is_active: bool = True


class TierDefinition(BaseModel):
    """Pydantic model for risk tier definitions."""
    criteria: RiskTierCriteria = Field(..., description="Risk tier criteria")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules")
    scoring_weights: Dict[str, Decimal] = Field(default_factory=dict, description="Scoring component weights")
    thresholds: Dict[str, Union[Decimal, int, timedelta]] = Field(default_factory=dict, description="Threshold values")
    
    class Config:
        use_enum_values = False
        arbitrary_types_allowed = True


# Define comprehensive risk tier criteria

TIER_A_DEFINITION = TierDefinition(
    criteria=RiskTierCriteria(
        tier_id="tier_a",
        name="Low Risk",
        description="Conservative arbitrage opportunities with minimal risk profile. Suitable for institutional and risk-averse strategies.",
        
        # Mathematical thresholds (most restrictive)
        min_profit_margin='0.03',  # Minimum 3% profit margin
        max_profit_margin='0.15',  # Maximum 15% (unrealistic higher margins avoided)
        min_liquidity_score='0.90',  # Very high liquidity required
        max_execution_time=timedelta(seconds=30),  # Very fast execution required
        max_odds_deviation='0.005',  # Maximum 0.5% odds deviation
        max_volatility_score='0.10',  # Very low volatility tolerance
        min_confidence_score='0.90',  # Very high confidence required
        
        # Bookmaker requirements (most strict)
        min_bookmaker_reliability='0.95',  # 95% minimum reliability
        min_bookmaker_rating='8.5',  # 8.5/10 minimum rating
        required_bookmaker_count=3,  # Minimum 3 bookmakers
        max_bookmaker_risk_weight='0.25',  # Max 25% risk weight per bookmaker
        
        # Market conditions (most restrictive)
        acceptable_market_conditions=[MarketCondition.CALM, MarketCondition.NORMAL],
        max_market_impact_factor='0.02',  # Max 2% market impact
        min_market_depth='10000',  # Minimum $10K market depth
        
        # Execution requirements (highest standards)
        min_slippage_tolerance='0.01',  # Max 1% slippage
        max_cancellation_risk='0.01',  # Max 1% cancellation risk
        min_fill_probability='0.95',  # Min 95% fill probability
        
        # Timing constraints (most restrictive)
        max_odds_age=timedelta(minutes=5),  # Odds must be <5 min old
        min_time_to_event=timedelta(hours=24),  # Min 24 hours to event
        max_processing_time=timedelta(seconds=60),  # Max 60 sec total processing
        
        # Risk limits (most conservative)
        max_position_size='1000',  # Max $1K position
        max_exposure_per_opportunity='0.05',  # Max 5% of bankroll per opportunity
        max_daily_exposure='0.20',  # Max 20% of bankroll daily
        max_concurrent_opportunities=3,  # Max 3 concurrent opportunities
        
        # Quality metrics (highest standards)
        min_success_rate='0.92',  # Min 92% success rate
        max_drawdown_tolerance='0.03',  # Max 3% drawdown
        min_sharpe_ratio='2.0',  # Min Sharpe ratio of 2.0
        max_var_95='0.02',  # Max 2% VaR at 95% confidence
        
        # Stress test requirements (highest standards)
        stress_test_pass_rate='0.90',  # Min 90% stress test pass rate
        monte_carlo_success_threshold='0.85',  # Min 85% Monte Carlo success
        scenario_analysis_score='8.0'  # Min 8/10 scenario analysis score
    ),
    validation_rules={
        'minimum_opportunities_per_day': 5,
        'maximum_consecutive_failures': 2,
        'required_data_points': 100,
        'minimum_backtest_period_days': 90,
        'maximum_correlation_threshold': '0.3',
        'required_volatility_regime_stability': True
    },
    scoring_weights={
        'profit_margin': '0.25',
        'liquidity': '0.20',
        'bookmaker_reliability': '0.20',
        'execution_speed': '0.15',
        'odds_stability': '0.10',
        'timing': '0.10'
    },
    thresholds={
        'minimum_sharpe_ratio': '2.0',
        'maximum_beta': '0.5',
        'minimum_information_ratio': '1.5',
        'maximum_tracking_error': '0.02',
        'minimum_calmar_ratio': '3.0'
    }
)


TIER_B_DEFINITION = TierDefinition(
    criteria=RiskTierCriteria(
        tier_id="tier_b",
        name="Moderate Risk",
        description="Balanced arbitrage opportunities with moderate risk profile. Good for most trading strategies.",
        
        # Mathematical thresholds (moderately restrictive)
        min_profit_margin='0.02',  # Minimum 2% profit margin
        max_profit_margin='0.20',  # Maximum 20%
        min_liquidity_score='0.75',  # Good liquidity required
        max_execution_time=timedelta(seconds=60),  # 60 second execution window
        max_odds_deviation='0.01',  # Maximum 1% odds deviation
        max_volatility_score='0.25',  # Moderate volatility tolerance
        min_confidence_score='0.75',  # Good confidence required
        
        # Bookmaker requirements (moderate)
        min_bookmaker_reliability='0.85',  # 85% minimum reliability
        min_bookmaker_rating='7.0',  # 7.0/10 minimum rating
        required_bookmaker_count=2,  # Minimum 2 bookmakers
        max_bookmaker_risk_weight='0.40',  # Max 40% risk weight per bookmaker
        
        # Market conditions (moderate)
        acceptable_market_conditions=[MarketCondition.CALM, MarketCondition.NORMAL, MarketCondition.VOLATILE],
        max_market_impact_factor='0.05',  # Max 5% market impact
        min_market_depth='5000',  # Minimum $5K market depth
        
        # Execution requirements (standard)
        min_slippage_tolerance='0.025',  # Max 2.5% slippage
        max_cancellation_risk='0.05',  # Max 5% cancellation risk
        min_fill_probability='0.80',  # Min 80% fill probability
        
        # Timing constraints (standard)
        max_odds_age=timedelta(minutes=15),  # Odds must be <15 min old
        min_time_to_event=timedelta(hours=6),  # Min 6 hours to event
        max_processing_time=timedelta(seconds=120),  # Max 2 min total processing
        
        # Risk limits (moderate)
        max_position_size='2500',  # Max $2.5K position
        max_exposure_per_opportunity='0.10',  # Max 10% of bankroll per opportunity
        max_daily_exposure='0.35',  # Max 35% of bankroll daily
        max_concurrent_opportunities=5,  # Max 5 concurrent opportunities
        
        # Quality metrics (good standards)
        min_success_rate='0.85',  # Min 85% success rate
        max_drawdown_tolerance='0.05',  # Max 5% drawdown
        min_sharpe_ratio='1.5',  # Min Sharpe ratio of 1.5
        max_var_95='0.05',  # Max 5% VaR at 95% confidence
        
        # Stress test requirements (good standards)
        stress_test_pass_rate='0.75',  # Min 75% stress test pass rate
        monte_carlo_success_threshold='0.70',  # Min 70% Monte Carlo success
        scenario_analysis_score='6.5'  # Min 6.5/10 scenario analysis score
    ),
    validation_rules={
        'minimum_opportunities_per_day': 3,
        'maximum_consecutive_failures': 3,
        'required_data_points': 50,
        'minimum_backtest_period_days': 60,
        'maximum_correlation_threshold': '0.5',
        'required_volatility_regime_stability': False
    },
    scoring_weights={
        'profit_margin': '0.25',
        'liquidity': '0.20',
        'bookmaker_reliability': '0.20',
        'execution_speed': '0.15',
        'odds_stability': '0.10',
        'timing': '0.10'
    },
    thresholds={
        'minimum_sharpe_ratio': '1.5',
        'maximum_beta': '0.8',
        'minimum_information_ratio': '1.0',
        'maximum_tracking_error': '0.05',
        'minimum_calmar_ratio': '2.0'
    }
)


TIER_C_DEFINITION = TierDefinition(
    criteria=RiskTierCriteria(
        tier_id="tier_c",
        name="Higher Risk",
        description="Higher risk arbitrage opportunities with increased potential returns. Suitable for experienced traders.",
        
        # Mathematical thresholds (less restrictive)
        min_profit_margin='0.015',  # Minimum 1.5% profit margin
        max_profit_margin='0.30',  # Maximum 30%
        min_liquidity_score='0.60',  # Moderate liquidity acceptable
        max_execution_time=timedelta(seconds=120),  # 2 minute execution window
        max_odds_deviation='0.02',  # Maximum 2% odds deviation
        max_volatility_score='0.40',  # Higher volatility tolerance
        min_confidence_score='0.60',  # Moderate confidence acceptable
        
        # Bookmaker requirements (relaxed)
        min_bookmaker_reliability='0.75',  # 75% minimum reliability
        min_bookmaker_rating='6.0',  # 6.0/10 minimum rating
        required_bookmaker_count=2,  # Minimum 2 bookmakers
        max_bookmaker_risk_weight='0.50',  # Max 50% risk weight per bookmaker
        
        # Market conditions (more flexible)
        acceptable_market_conditions=[MarketCondition.CALM, MarketCondition.NORMAL, MarketCondition.VOLATILE],
        max_market_impact_factor='0.10',  # Max 10% market impact
        min_market_depth='2000',  # Minimum $2K market depth
        
        # Execution requirements (flexible)
        min_slippage_tolerance='0.05',  # Max 5% slippage
        max_cancellation_risk='0.10',  # Max 10% cancellation risk
        min_fill_probability='0.70',  # Min 70% fill probability
        
        # Timing constraints (flexible)
        max_odds_age=timedelta(minutes=30),  # Odds must be <30 min old
        min_time_to_event=timedelta(hours=2),  # Min 2 hours to event
        max_processing_time=timedelta(seconds=300),  # Max 5 min total processing
        
        # Risk limits (higher)
        max_position_size='5000',  # Max $5K position
        max_exposure_per_opportunity='0.15',  # Max 15% of bankroll per opportunity
        max_daily_exposure='0.50',  # Max 50% of bankroll daily
        max_concurrent_opportunities=8,  # Max 8 concurrent opportunities
        
        # Quality metrics (acceptable standards)
        min_success_rate='0.75',  # Min 75% success rate
        max_drawdown_tolerance='0.08',  # Max 8% drawdown
        min_sharpe_ratio='1.0',  # Min Sharpe ratio of 1.0
        max_var_95='0.08',  # Max 8% VaR at 95% confidence
        
        # Stress test requirements (basic standards)
        stress_test_pass_rate='0.60',  # Min 60% stress test pass rate
        monte_carlo_success_threshold='0.55',  # Min 55% Monte Carlo success
        scenario_analysis_score='5.0'  # Min 5/10 scenario analysis score
    ),
    validation_rules={
        'minimum_opportunities_per_day': 2,
        'maximum_consecutive_failures': 4,
        'required_data_points': 25,
        'minimum_backtest_period_days': 30,
        'maximum_correlation_threshold': '0.7',
        'required_volatility_regime_stability': False
    },
    scoring_weights={
        'profit_margin': '0.25',
        'liquidity': '0.20',
        'bookmaker_reliability': '0.20',
        'execution_speed': '0.15',
        'odds_stability': '0.10',
        'timing': '0.10'
    },
    thresholds={
        'minimum_sharpe_ratio': '1.0',
        'maximum_beta': '1.2',
        'minimum_information_ratio': '0.5',
        'maximum_tracking_error': '0.10',
        'minimum_calmar_ratio': '1.0'
    }
)


TIER_D_DEFINITION = TierDefinition(
    criteria=RiskTierCriteria(
        tier_id="tier_d",
        name="Highest Risk",
        description="Highest risk arbitrage opportunities with maximum potential returns. Only for sophisticated traders with high risk tolerance.",
        
        # Mathematical thresholds (least restrictive)
        min_profit_margin='0.01',  # Minimum 1% profit margin
        max_profit_margin='0.50',  # Maximum 50%
        min_liquidity_score='0.40',  # Lower liquidity acceptable
        max_execution_time=timedelta(seconds=300),  # 5 minute execution window
        max_odds_deviation='0.05',  # Maximum 5% odds deviation
        max_volatility_score='0.60',  # High volatility tolerance
        min_confidence_score='0.50',  # Lower confidence acceptable
        
        # Bookmaker requirements (most relaxed)
        min_bookmaker_reliability='0.65',  # 65% minimum reliability
        min_bookmaker_rating='5.0',  # 5.0/10 minimum rating
        required_bookmaker_count=1,  # Minimum 1 bookmaker
        max_bookmaker_risk_weight='0.70',  # Max 70% risk weight per bookmaker
        
        # Market conditions (most flexible)
        acceptable_market_conditions=[MarketCondition.CALM, MarketCondition.NORMAL, MarketCondition.VOLATILE, MarketCondition.STRESSED],
        max_market_impact_factor='0.20',  # Max 20% market impact
        min_market_depth='500',  # Minimum $500 market depth
        
        # Execution requirements (most flexible)
        min_slippage_tolerance='0.10',  # Max 10% slippage
        max_cancellation_risk='0.20',  # Max 20% cancellation risk
        min_fill_probability='0.60',  # Min 60% fill probability
        
        # Timing constraints (most flexible)
        max_odds_age=timedelta(hours=2),  # Odds can be up to 2 hours old
        min_time_to_event=timedelta(minutes=30),  # Min 30 minutes to event
        max_processing_time=timedelta(seconds=600),  # Max 10 min total processing
        
        # Risk limits (highest)
        max_position_size='10000',  # Max $10K position
        max_exposure_per_opportunity='0.25',  # Max 25% of bankroll per opportunity
        max_daily_exposure='0.75',  # Max 75% of bankroll daily
        max_concurrent_opportunities=15,  # Max 15 concurrent opportunities
        
        # Quality metrics (basic standards)
        min_success_rate='0.65',  # Min 65% success rate
        max_drawdown_tolerance='0.12',  # Max 12% drawdown
        min_sharpe_ratio='0.5',  # Min Sharpe ratio of 0.5
        max_var_95='0.12',  # Max 12% VaR at 95% confidence
        
        # Stress test requirements (basic standards)
        stress_test_pass_rate='0.50',  # Min 50% stress test pass rate
        monte_carlo_success_threshold='0.45',  # Min 45% Monte Carlo success
        scenario_analysis_score='4.0'  # Min 4/10 scenario analysis score
    ),
    validation_rules={
        'minimum_opportunities_per_day': 1,
        'maximum_consecutive_failures': 5,
        'required_data_points': 10,
        'minimum_backtest_period_days': 14,
        'maximum_correlation_threshold': '0.9',
        'required_volatility_regime_stability': False
    },
    scoring_weights={
        'profit_margin': '0.30',
        'liquidity': '0.15',
        'bookmaker_reliability': '0.15',
        'execution_speed': '0.15',
        'odds_stability': '0.15',
        'timing': '0.10'
    },
    thresholds={
        'minimum_sharpe_ratio': '0.5',
        'maximum_beta': '1.5',
        'minimum_information_ratio': '0.2',
        'maximum_tracking_error': '0.20',
        'minimum_calmar_ratio': '0.5'
    }
)


# Validation functions

def validate_tier_criteria(criteria: RiskTierCriteria) -> Tuple[bool, List[str]]:
    """
    Validate risk tier criteria for completeness and consistency.
    
    Args:
        criteria: Risk tier criteria to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Basic validation
    if criteria.min_profit_margin >= criteria.max_profit_margin:
        errors.append("Minimum profit margin must be less than maximum profit margin")
    
    if criteria.min_confidence_score > '1.0' or criteria.min_confidence_score < '0.0':
        errors.append("Confidence score must be between 0 and 1")
    
    if criteria.min_bookmaker_reliability > '1.0' or criteria.min_bookmaker_reliability < '0.0':
        errors.append("Bookmaker reliability must be between 0 and 1")
    
    # Timing validation
    if criteria.max_odds_age < timedelta(minutes=1):
        errors.append("Max odds age should be at least 1 minute")
    
    if criteria.min_time_to_event < timedelta(minutes=1):
        errors.append("Min time to event should be at least 1 minute")
    
    # Risk limit validation
    if criteria.max_exposure_per_opportunity > '0.50':
        errors.append("Max exposure per opportunity should not exceed 50% of bankroll")
    
    if criteria.max_daily_exposure > '1.0':
        errors.append("Max daily exposure cannot exceed 100% of bankroll")
    
    # Quality metric validation
    if criteria.min_success_rate > '1.0' or criteria.min_success_rate < '0.0':
        errors.append("Success rate must be between 0 and 1")
    
    if criteria.max_drawdown_tolerance > '0.50':
        errors.append("Drawdown tolerance should not exceed 50%")
    
    return len(errors) == 0, errors


def get_tier_by_score(score: Decimal) -> Optional[str]:
    """
    Get the appropriate risk tier based on a composite risk score.
    
    Args:
        score: Composite risk score (0.0 to 1.0, where 1.0 is highest risk)
        
    Returns:
        Risk tier string (tier_a, tier_b, tier_c, tier_d) or None if invalid
    """
    if score <= Decimal('0.25'):
        return 'tier_a'
    elif score <= Decimal('0.50'):
        return 'tier_b'
    elif score <= Decimal('0.75'):
        return 'tier_c'
    elif score <= Decimal('1.00'):
        return 'tier_d'
    else:
        return None


def get_tier_definition(tier_id: str) -> Optional[TierDefinition]:
    """
    Get tier definition by tier ID.
    
    Args:
        tier_id: Tier identifier (tier_a, tier_b, tier_c, tier_d)
        
    Returns:
        TierDefinition object or None if not found
    """
    tier_map = {
        'tier_a': TIER_A_DEFINITION,
        'tier_b': TIER_B_DEFINITION,
        'tier_c': TIER_C_DEFINITION,
        'tier_d': TIER_D_DEFINITION
    }
    return tier_map.get(tier_id)


def get_all_tier_definitions() -> List[Tuple[str, TierDefinition]]:
    """
    Get all defined risk tier definitions.
    
    Returns:
        List of (tier_id, tier_definition) tuples
    """
    return [
        ('tier_a', TIER_A_DEFINITION),
        ('tier_b', TIER_B_DEFINITION),
        ('tier_c', TIER_C_DEFINITION),
        ('tier_d', TIER_D_DEFINITION)
    ]


def get_tier_by_risk_tolerance(risk_tolerance: RiskToleranceLevel) -> str:
    """
    Get recommended risk tier based on user risk tolerance.
    
    Args:
        risk_tolerance: User's risk tolerance level
        
    Returns:
        Recommended tier ID
    """
    tolerance_to_tier = {
        RiskToleranceLevel.CONSERVATIVE: 'tier_a',
        RiskToleranceLevel.MODERATE: 'tier_b',
        RiskToleranceLevel.AGGRESSIVE: 'tier_c',
        RiskToleranceLevel.INSTITUTIONAL: 'tier_a'  # Institutions prefer low risk but with larger position sizes
    }
    return tolerance_to_tier.get(risk_tolerance, 'tier_b')  # Default to moderate


def get_acceptable_market_conditions(tier_id: str) -> List[MarketCondition]:
    """
    Get acceptable market conditions for a given tier.
    
    Args:
        tier_id: Tier identifier
        
    Returns:
        List of acceptable market conditions
    """
    tier_def = get_tier_definition(tier_id)
    if tier_def:
        return tier_def.criteria.acceptable_market_conditions
    return []


def calculate_composite_risk_score(
    profit_margin: Decimal,
    liquidity_score: Decimal,
    bookmaker_reliability: Decimal,
    execution_time: timedelta,
    odds_deviation: Decimal,
    volatility_score: Decimal,
    confidence_score: Decimal,
    tier_definition: TierDefinition
) -> Decimal:
    """
    Calculate composite risk score using tier-specific weights.
    
    Args:
        profit_margin: Profit margin score
        liquidity_score: Liquidity score
        bookmaker_reliability: Bookmaker reliability score
        execution_time: Execution time score
        odds_deviation: Odds deviation score
        volatility_score: Volatility score
        confidence_score: Confidence score
        tier_definition: Tier definition with scoring weights
        
    Returns:
        Composite risk score (0.0 to 1.0)
    """
    weights = tier_definition.scoring_weights
    
    # Calculate weighted score components
    score_components = {
        'profit_margin': profit_margin * weights.get('profit_margin', '0.0'),
        'liquidity': liquidity_score * weights.get('liquidity', '0.0'),
        'bookmaker_reliability': bookmaker_reliability * weights.get('bookmaker_reliability', '0.0'),
        'execution_speed': execution_time * weights.get('execution_speed', '0.0'),
        'odds_stability': odds_deviation * weights.get('odds_stability', '0.0'),
        'timing': confidence_score * weights.get('timing', '0.0')
    }
    
    # Sum all components
    total_score = sum(score_components.values())
    
    # Normalize to 0-1 range
    return min(max(total_score, Decimal('0.0')), Decimal('1.0'))


# Create logger instance
logger = logging.getLogger(__name__)


def initialize_risk_tiers():
    """Initialize and validate all risk tier definitions."""
    logger.info("Initializing risk tier definitions...")
    
    valid_tiers = 0
    total_tiers = 0
    
    for tier_id, tier_def in get_all_tier_definitions():
        total_tiers += 1
        is_valid, errors = validate_tier_criteria(tier_def.criteria)
        
        if is_valid:
            valid_tiers += 1
            logger.info(f"✓ Tier {tier_id} validated successfully")
        else:
            logger.error(f"✗ Tier {tier_id} validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
    
    logger.info(f"Risk tier validation complete: {valid_tiers}/{total_tiers} tiers valid")
    return valid_tiers == total_tiers


# Initialize on module load
if __name__ != "__main__":
    initialize_risk_tiers()