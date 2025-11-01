"""
Utils package for Arbitech arbitrage betting framework.

This package provides core mathematical utilities and validation functions
for arbitrage calculations, input validation, and data sanitization.
"""

from .math_helpers import (
    calculate_implied_probabilities,
    calculate_profit_margin,
    calculate_kelly_stakes,
    validate_arbitrage_opportunity,
    calculate_lay_bet_requirements,
    stake_optimization,
    calculate_arbitrage_metrics,
    calculate_combined_odds,
    calculate_expected_value,
    ArbitrageOpportunity,
    BettingLeg
)

from .validation import (
    validate_odds_format,
    validate_bet_amount,
    validate_bookmaker_name,
    validate_outcome_name,
    validate_url,
    validate_api_key,
    sanitize_list_input,
    validate_bankroll_data,
    validate_arbitrage_legs,
    validate_datetime_input,
    validate_percentage,
    create_validation_pipeline,
    sanitize_user_input,
    validate_transaction_amount,
    ValidationError,
    SanitizationError
)

__version__ = "1.0.0"
__all__ = [
    # Math helpers
    "calculate_implied_probabilities",
    "calculate_profit_margin", 
    "calculate_kelly_stakes",
    "validate_arbitrage_opportunity",
    "calculate_lay_bet_requirements",
    "stake_optimization",
    "calculate_arbitrage_metrics",
    "calculate_combined_odds",
    "calculate_expected_value",
    "ArbitrageOpportunity",
    "BettingLeg",
    
    # Validation
    "validate_odds_format",
    "validate_bet_amount",
    "validate_bookmaker_name",
    "validate_outcome_name", 
    "validate_url",
    "validate_api_key",
    "sanitize_list_input",
    "validate_bankroll_data",
    "validate_arbitrage_legs",
    "validate_datetime_input",
    "validate_percentage",
    "create_validation_pipeline",
    "sanitize_user_input",
    "validate_transaction_amount",
    "ValidationError",
    "SanitizationError"
]