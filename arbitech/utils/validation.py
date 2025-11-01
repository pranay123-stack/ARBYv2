"""
Input validation, data sanitization, and safety checks for financial data.

This module provides comprehensive validation utilities for arbitrage betting
including input sanitization, data type validation, and financial safety checks.
"""

import re
import math
from typing import Any, List, Dict, Optional, Union, Callable
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from urllib.parse import urlparse


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class SanitizationError(Exception):
    """Custom exception for sanitization errors."""
    pass


def validate_odds_format(odds: Any, allow_formats: List[str] = None) -> Decimal:
    """
    Validate and convert odds to standard decimal format.
    
    Args:
        odds: Input odds (string, float, or int)
        allow_formats: List of allowed formats ('decimal', 'american', 'fractional')
        
    Returns:
        Decimal representation of odds
        
    Raises:
        ValidationError: If odds format is invalid
    """
    if allow_formats is None:
        allow_formats = ['decimal']
    
    if odds is None:
        raise ValidationError("Odds cannot be None")
    
    try:
        # Convert to string for processing
        odds_str = str(odds).strip()
        
        # Remove common formatting characters
        odds_str = re.sub(r'[^\d.+/-]', '', odds_str)
        
        # Handle different odds formats
        if '+' in odds_str and 'american' in allow_formats:
            # American odds
            american_odds = int(odds_str.replace('+', ''))
            decimal_odds = Decimal(american_odds) / Decimal('100') + Decimal('1')
        elif '-' in odds_str and 'american' in allow_formats:
            # Negative American odds
            american_odds = int(odds_str.replace('-', ''))
            decimal_odds = Decimal('100') / Decimal(abs(american_odds)) + Decimal('1')
        elif '/' in odds_str and 'fractional' in allow_formats:
            # Fractional odds
            parts = odds_str.split('/')
            if len(parts) != 2:
                raise ValidationError("Invalid fractional odds format")
            numerator, denominator = map(int, parts)
            if denominator == 0:
                raise ValidationError("Denominator cannot be zero")
            decimal_odds = Decimal(numerator) / Decimal(denominator) + Decimal('1')
        else:
            # Decimal odds
            decimal_odds = Decimal(odds_str)
        
        # Validate decimal odds range
        if decimal_odds <= Decimal('0'):
            raise ValidationError(f"Odds must be positive, got: {decimal_odds}")
        
        if decimal_odds < Decimal('1.01'):
            raise ValidationError(f"Odds too low, minimum is 1.01: {decimal_odds}")
        
        if decimal_odds > Decimal('10000'):
            raise ValidationError(f"Odds too high, maximum is 10000: {decimal_odds}")
        
        return decimal_odds.quantize(Decimal('0.0001'))
        
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValidationError(f"Invalid odds format: {odds}. Error: {str(e)}")


def validate_bet_amount(amount: Union[str, float, int, Decimal], 
                       min_amount: Union[str, float] = '0.01',
                       max_amount: Union[str, float] = None,
                       currency: str = 'USD') -> Decimal:
    """
    Validate bet amounts for financial safety.
    
    Args:
        amount: Bet amount to validate
        min_amount: Minimum allowed bet amount
        max_amount: Maximum allowed bet amount
        currency: Currency code for formatting
        
    Returns:
        Decimal representation of validated amount
        
    Raises:
        ValidationError: If amount is invalid or outside limits
    """
    try:
        amount_decimal = Decimal(str(amount))
        
        if amount_decimal <= 0:
            raise ValidationError(f"Bet amount must be positive, got: {amount_decimal}")
        
        if amount_decimal < Decimal(str(min_amount)):
            raise ValidationError(
                f"Bet amount too low. Minimum: {min_amount} {currency}, got: {amount_decimal}"
            )
        
        if max_amount is not None:
            max_decimal = Decimal(str(max_amount))
            if amount_decimal > max_decimal:
                raise ValidationError(
                    f"Bet amount too high. Maximum: {max_amount} {currency}, got: {amount_decimal}"
                )
        
        # Check for reasonable precision (max 2 decimal places for most currencies)
        if amount_decimal.as_tuple().exponent < -4:
            raise ValidationError(
                f"Too many decimal places in bet amount. Maximum 4 decimal places: {amount_decimal}"
            )
        
        return amount_decimal.quantize(Decimal('0.01'))
        
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValidationError(f"Invalid bet amount: {amount}. Error: {str(e)}")


def validate_bookmaker_name(name: str) -> str:
    """
    Validate and sanitize bookmaker names.
    
    Args:
        name: Bookmaker name to validate
        
    Returns:
        Sanitized bookmaker name
        
    Raises:
        ValidationError: If name is invalid
    """
    if not name:
        raise ValidationError("Bookmaker name cannot be empty")
    
    if len(name) > 100:
        raise ValidationError("Bookmaker name too long (max 100 characters)")
    
    # Remove leading/trailing whitespace
    sanitized = name.strip()
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'[^a-zA-Z0-9\s\-_&.]',  # Allow alphanumeric, spaces, hyphens, underscores, ampersands, periods
        r'http[s]?://',
        r'\b(logo|image|logo\.png|logo\.jpg)\b',
        r'javascript:',
        r'<script>',
        r'eval\(',
        r'document\.',
        r'window\.'
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            raise ValidationError(f"Bookmaker name contains invalid content: {name}")
    
    return sanitized


def validate_outcome_name(outcome: str, allowed_outcomes: List[str] = None) -> str:
    """
    Validate outcome names (e.g., team names, player names).
    
    Args:
        outcome: Outcome name to validate
        allowed_outcomes: List of allowed outcomes (whitelist approach)
        
    Returns:
        Sanitized outcome name
        
    Raises:
        ValidationError: If outcome is invalid
    """
    if not outcome:
        raise ValidationError("Outcome name cannot be empty")
    
    if len(outcome) > 200:
        raise ValidationError("Outcome name too long (max 200 characters)")
    
    # Remove leading/trailing whitespace
    sanitized = outcome.strip()
    
    # Check for malicious content
    if re.search(r'[<>"\'`&]', sanitized):
        raise ValidationError("Outcome name contains invalid special characters")
    
    # If whitelist provided, check against it
    if allowed_outcomes and sanitized.lower() not in [o.lower() for o in allowed_outcomes]:
        raise ValidationError(f"Outcome '{sanitized}' not in allowed list")
    
    return sanitized


def validate_url(url: str, allowed_domains: List[str] = None) -> str:
    """
    Validate URLs for safety.
    
    Args:
        url: URL to validate
        allowed_domains: List of allowed domains
        
    Returns:
        Sanitized URL
        
    Raises:
        ValidationError: If URL is invalid
    """
    if not url:
        raise ValidationError("URL cannot be empty")
    
    try:
        parsed = urlparse(url)
        
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError("Invalid URL format")
        
        # Only allow safe schemes
        if parsed.scheme not in ['http', 'https']:
            raise ValidationError(f"Unsafe URL scheme: {parsed.scheme}")
        
        # Check against allowed domains if provided
        if allowed_domains and parsed.netloc.lower() not in [d.lower() for d in allowed_domains]:
            raise ValidationError(f"Domain not allowed: {parsed.netloc}")
        
        # Additional security checks
        if any(char in url for char in ['<', '>', '"', "'", '(', ')', ';']):
            raise ValidationError("URL contains suspicious characters")
        
        return url.strip()
        
    except Exception as e:
        raise ValidationError(f"Invalid URL: {url}. Error: {str(e)}")


def validate_api_key(api_key: str, min_length: int = 16) -> bool:
    """
    Validate API keys for format and security.
    
    Args:
        api_key: API key to validate
        min_length: Minimum length requirement
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key:
        raise ValidationError("API key cannot be empty")
    
    if len(api_key) < min_length:
        raise ValidationError(f"API key too short (min {min_length} characters)")
    
    if len(api_key) > 200:
        raise ValidationError("API key too long")
    
    # Check for suspicious patterns
    if re.search(r'[^a-zA-Z0-9_\-]', api_key):
        raise ValidationError("API key contains invalid characters")
    
    # Check for obvious dummy keys
    dummy_patterns = [
        r'^test$', r'^dummy$', r'^changeme$', r'^123456$',
        r'^your_api_key_here$', r'^sk_test_.*$', r'^sk_live_.*$'
    ]
    
    for pattern in dummy_patterns:
        if re.search(pattern, api_key, re.IGNORECASE):
            raise ValidationError("API key appears to be a placeholder or dummy key")
    
    return True


def sanitize_list_input(data: Any, max_length: int = 1000) -> List:
    """
    Sanitize and validate list input.
    
    Args:
        data: Data to sanitize
        max_length: Maximum list length
        
    Returns:
        Sanitized list
        
    Raises:
        ValidationError: If data is invalid
    """
    if not isinstance(data, (list, tuple)):
        raise ValidationError(f"Expected list or tuple, got: {type(data).__name__}")
    
    if len(data) > max_length:
        raise ValidationError(f"List too long (max {max_length} items)")
    
    if len(data) == 0:
        raise ValidationError("List cannot be empty")
    
    return list(data)


def validate_bankroll_data(bankroll: Union[str, float, int, Decimal],
                          currency: str = 'USD') -> Dict[str, Any]:
    """
    Comprehensive bankroll validation with safety checks.
    
    Args:
        bankroll: Bankroll amount
        currency: Currency code
        
    Returns:
        Dictionary with validation results and metadata
    """
    bankroll_decimal = validate_bet_amount(bankroll, min_amount='0.01')
    
    # Additional bankroll-specific validations
    if bankroll_decimal > Decimal('1000000'):  # $1M limit
        raise ValidationError("Bankroll exceeds maximum limit ($1,000,000)")
    
    # Check for round numbers that might indicate testing
    if bankroll_decimal % Decimal('100') == 0:
        # Round number might indicate testing - add warning
        warning = "Bankroll is a round number - verify this is intentional"
    else:
        warning = None
    
    return {
        'bankroll': bankroll_decimal,
        'currency': currency.upper(),
        'is_valid': True,
        'warning': warning,
        'validation_time': datetime.now(timezone.utc).isoformat()
    }


def validate_arbitrage_legs(legs: List[Dict]) -> Dict[str, Any]:
    """
    Validate arbitrage opportunity legs comprehensively.
    
    Args:
        legs: List of betting legs
        
    Returns:
        Dictionary with validation results
    """
    if not legs:
        raise ValidationError("No legs provided for arbitrage opportunity")
    
    if len(legs) < 2:
        raise ValidationError("Arbitrage opportunity must have at least 2 legs")
    
    if len(legs) > 20:  # Reasonable upper limit
        raise ValidationError("Too many legs (max 20 allowed)")
    
    validated_legs = []
    outcomes = set()
    
    for i, leg in enumerate(legs):
        try:
            # Validate required fields
            if not isinstance(leg, dict):
                raise ValidationError(f"Leg {i} is not a dictionary")
            
            required_fields = ['bookmaker', 'outcome', 'odds']
            for field in required_fields:
                if field not in leg:
                    raise ValidationError(f"Leg {i} missing required field: {field}")
            
            # Validate and sanitize each field
            bookmaker = validate_bookmaker_name(leg['bookmaker'])
            outcome = validate_outcome_name(leg['outcome'])
            odds = validate_odds_format(leg['odds'])
            
            # Check for duplicate outcomes
            if outcome in outcomes:
                raise ValidationError(f"Duplicate outcome '{outcome}' in legs")
            outcomes.add(outcome)
            
            validated_legs.append({
                'bookmaker': bookmaker,
                'outcome': outcome,
                'odds': odds,
                'implied_probability': float(Decimal('1') / odds),
                'index': i
            })
            
        except Exception as e:
            raise ValidationError(f"Error validating leg {i}: {str(e)}")
    
    return {
        'legs': validated_legs,
        'num_legs': len(validated_legs),
        'unique_outcomes': len(outcomes),
        'is_valid': True,
        'validation_time': datetime.now(timezone.utc).isoformat()
    }


def validate_datetime_input(datetime_input: str, 
                          allow_future: bool = True,
                          min_ago_days: int = None) -> datetime:
    """
    Validate datetime inputs for safety and reasonableness.
    
    Args:
        datetime_input: Datetime string to validate
        allow_future: Whether to allow future datetimes
        min_ago_days: Minimum days ago required
        
    Returns:
        Validated datetime object
        
    Raises:
        ValidationError: If datetime is invalid
    """
    try:
        # Parse the datetime
        if isinstance(datetime_input, str):
            parsed_dt = datetime.fromisoformat(datetime_input.replace('Z', '+00:00'))
        elif isinstance(datetime_input, datetime):
            parsed_dt = datetime_input
        else:
            raise ValidationError("Invalid datetime format")
        
        now = datetime.now(timezone.utc)
        
        # Check if future dates are allowed
        if not allow_future and parsed_dt > now:
            raise ValidationError("Future datetime not allowed")
        
        # Check minimum age if specified
        if min_ago_days is not None:
            min_age = now.replace(hour=0, minute=0, second=0, microsecond=0) - \
                     timedelta(days=min_ago_days)
            if parsed_dt < min_age:
                raise ValidationError(f"Date too old (min {min_ago_days} days ago)")
        
        return parsed_dt
        
    except ValueError as e:
        raise ValidationError(f"Invalid datetime format: {datetime_input}. Error: {str(e)}")


def validate_percentage(value: Union[str, float, int], 
                       min_value: float = 0.0,
                       max_value: float = 100.0) -> Decimal:
    """
    Validate percentage values.
    
    Args:
        value: Percentage value to validate
        min_value: Minimum percentage value
        max_value: Maximum percentage value
        
    Returns:
        Decimal representation of percentage
        
    Raises:
        ValidationError: If percentage is invalid
    """
    try:
        decimal_value = Decimal(str(value))
        
        if decimal_value < Decimal(str(min_value)):
            raise ValidationError(f"Percentage too low (min {min_value}%): {decimal_value}%")
        
        if decimal_value > Decimal(str(max_value)):
            raise ValidationError(f"Percentage too high (max {max_value}%): {decimal_value}%")
        
        return decimal_value.quantize(Decimal('0.01'))
        
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValidationError(f"Invalid percentage value: {value}. Error: {str(e)}")


def create_validation_pipeline(*validators: Callable) -> Callable:
    """
    Create a validation pipeline that applies multiple validators in sequence.
    
    Args:
        *validators: List of validator functions
        
    Returns:
        Pipeline function that applies all validators
    """
    def pipeline(data):
        result = data
        for validator in validators:
            result = validator(result)
        return result
    
    return pipeline


def sanitize_user_input(text: str, max_length: int = 5000) -> str:
    """
    Sanitize user input text for security.
    
    Args:
        text: Text to sanitize
        max_length: Maximum text length
        
    Returns:
        Sanitized text
        
    Raises:
        SanitizationError: If sanitization fails
    """
    if not isinstance(text, str):
        raise SanitizationError(f"Expected string, got: {type(text).__name__}")
    
    if len(text) > max_length:
        raise SanitizationError(f"Text too long (max {max_length} characters)")
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove control characters except common ones
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Strip whitespace
    text = text.strip()
    
    if not text:
        raise SanitizationError("Text cannot be empty after sanitization")
    
    return text


def validate_transaction_amount(amount: Union[str, float, int, Decimal],
                               transaction_type: str = 'deposit',
                               daily_limit: Decimal = Decimal('10000'),
                               monthly_limit: Decimal = Decimal('100000')) -> Dict[str, Any]:
    """
    Validate transaction amounts with daily/monthly limits.
    
    Args:
        amount: Transaction amount
        transaction_type: Type of transaction ('deposit', 'withdrawal', 'bet')
        daily_limit: Daily transaction limit
        monthly_limit: Monthly transaction limit
        
    Returns:
        Dictionary with validation results
    """
    validated_amount = validate_bet_amount(amount)
    
    # Type-specific validations
    if transaction_type == 'withdrawal':
        if validated_amount < Decimal('10'):
            raise ValidationError("Minimum withdrawal amount is $10")
    
    elif transaction_type == 'deposit':
        if validated_amount > monthly_limit:
            raise ValidationError(f"Deposit exceeds monthly limit: ${monthly_limit}")
    
    elif transaction_type == 'bet':
        if validated_amount > daily_limit:
            raise ValidationError(f"Bet amount exceeds daily limit: ${daily_limit}")
    
    else:
        raise ValidationError(f"Unknown transaction type: {transaction_type}")
    
    return {
        'amount': validated_amount,
        'transaction_type': transaction_type,
        'is_valid': True,
        'daily_limit': daily_limit,
        'monthly_limit': monthly_limit,
        'validation_time': datetime.now(timezone.utc).isoformat()
    }