"""
Odds Validation and Cross-Validation System

This module provides comprehensive validation of extracted odds against mathematical
constraints and arbitrage opportunities. It ensures data quality and identifies
potentially profitable arbitrage scenarios.

Features:
- Mathematical constraint validation
- Arbitrage opportunity detection
- Odds consistency checking
- Market comparison validation
- Comprehensive validation reporting
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Union, Tuple, Set, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import math

from ..storage.models import (
    ArbitrageOpportunity, ArbitrageLeg, Sport, Market, 
    MarketType, Bet, BetStatus, RiskTier
)


class ValidationLevel(Enum):
    """Validation levels for different use cases."""
    BASIC = "basic"
    STANDARD = "standard" 
    STRICT = "strict"
    RESEARCH = "research"


class ValidationResult(Enum):
    """Results of validation checks."""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    ERROR = "error"


@dataclass
class ValidationCheck:
    """Individual validation check result."""
    name: str
    result: ValidationResult
    message: str
    confidence: float
    details: Optional[Dict[str, Any]] = None


@dataclass
class ArbitrageCheck:
    """Arbitrage opportunity analysis result."""
    is_arbitrage: bool
    profit_margin: Decimal
    confidence: float
    required_stakes: Optional[Dict[str, Decimal]] = None
    potential_profit: Optional[Decimal] = None
    details: Optional[Dict[str, Any]] = None


class OddsValidator:
    """
    Comprehensive odds validation system with mathematical constraint checking
    and arbitrage opportunity detection.
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """
        Initialize the odds validator.
        
        Args:
            validation_level: Level of validation strictness to apply
        """
        self.validation_level = validation_level
        self.logger = logging.getLogger(__name__)
        
        # Validation thresholds based on level
        self.thresholds = {
            ValidationLevel.BASIC: {
                'min_odds': Decimal('1.01'),
                'max_odds': Decimal('1000.00'),
                'max_implied_probability': Decimal('0.999'),
                'min_implied_probability': Decimal('0.001')
            },
            ValidationLevel.STANDARD: {
                'min_odds': Decimal('1.05'),
                'max_odds': Decimal('500.00'), 
                'max_implied_probability': Decimal('0.95'),
                'min_implied_probability': Decimal('0.02')
            },
            ValidationLevel.STRICT: {
                'min_odds': Decimal('1.10'),
                'max_odds': Decimal('100.00'),
                'max_implied_probability': Decimal('0.90'),
                'min_implied_probability': Decimal('0.05')
            },
            ValidationLevel.RESEARCH: {
                'min_odds': Decimal('1.01'),
                'max_odds': Decimal('10000.00'),
                'max_implied_probability': Decimal('0.999'),
                'min_implied_probability': Decimal('0.001')
            }
        }
    
    def validate_odds(self, odds: Union[str, float, int, Decimal]) -> List[ValidationCheck]:
        """
        Validate individual odds value.
        
        Args:
            odds: The odds value to validate
            
        Returns:
            List of validation check results
        """
        checks = []
        
        try:
            # Convert to Decimal for precise calculations
            if isinstance(odds, str):
                decimal_odds = Decimal(odds.strip())
            elif isinstance(odds, (int, float)):
                decimal_odds = Decimal(str(odds))
            else:
                decimal_odds = odds
                
        except (InvalidOperation, ValueError, TypeError) as e:
            return [ValidationCheck(
                name="numeric_format",
                result=ValidationResult.FAIL,
                message=f"Invalid numeric format: {odds}",
                confidence=1.0,
                details={"error": str(e)}
            )]
        
        # Range validation
        threshold = self.thresholds[self.validation_level]
        if decimal_odds < threshold['min_odds']:
            checks.append(ValidationCheck(
                name="odds_range_min",
                result=ValidationResult.WARNING if self.validation_level == ValidationLevel.RESEARCH else ValidationResult.FAIL,
                message=f"Odds {decimal_odds} below minimum threshold {threshold['min_odds']}",
                confidence=0.9,
                details={"odds": float(decimal_odds), "threshold": float(threshold['min_odds'])}
            ))
        
        if decimal_odds > threshold['max_odds']:
            checks.append(ValidationCheck(
                name="odds_range_max", 
                result=ValidationResult.WARNING if self.validation_level == ValidationLevel.RESEARCH else ValidationResult.FAIL,
                message=f"Odds {decimal_odds} above maximum threshold {threshold['max_odds']}",
                confidence=0.9,
                details={"odds": float(decimal_odds), "threshold": float(threshold['max_odds'])}
            ))
        
        # Implied probability validation
        try:
            implied_prob = Decimal('1') / decimal_odds
            if implied_prob > threshold['max_implied_probability']:
                checks.append(ValidationCheck(
                    name="implied_probability_max",
                    result=ValidationResult.WARNING,
                    message=f"Implied probability {implied_prob:.3f} above threshold {threshold['max_implied_probability']:.3f}",
                    confidence=0.8,
                    details={"implied_probability": float(implied_prob)}
                ))
                
            if implied_prob < threshold['min_implied_probability']:
                checks.append(ValidationCheck(
                    name="implied_probability_min",
                    result=ValidationResult.WARNING,
                    message=f"Implied probability {implied_prob:.3f} below threshold {threshold['min_implied_probability']:.3f}",
                    confidence=0.8,
                    details={"implied_probability": float(implied_prob)}
                ))
        except (InvalidOperation, ZeroDivisionError):
            checks.append(ValidationCheck(
                name="implied_probability_calculation",
                result=ValidationResult.FAIL,
                message="Cannot calculate implied probability from odds",
                confidence=1.0
            ))
        
        # Special value checks
        if decimal_odds == Decimal('0'):
            checks.append(ValidationCheck(
                name="zero_odds",
                result=ValidationResult.FAIL,
                message="Odds cannot be zero",
                confidence=1.0
            ))
        
        # Consistency checks for common decimal patterns
        str_odds = str(decimal_odds)
        if '.' in str_odds:
            decimal_places = len(str_odds.split('.')[1])
            if decimal_places > 4:
                checks.append(ValidationCheck(
                    name="excessive_decimal_places",
                    result=ValidationResult.WARNING,
                    message=f"Odds has {decimal_places} decimal places, may indicate processing error",
                    confidence=0.7,
                    details={"decimal_places": decimal_places}
                ))
        
        return checks
    
    def validate_arbitrage_opportunity(self, legs: List[ArbitrageLeg]) -> ArbitrageCheck:
        """
        Check if a set of arbitrage legs represents a valid arbitrage opportunity.
        
        Args:
            legs: List of arbitrage legs to check
            
        Returns:
            Arbitrage check result
        """
        if len(legs) < 2:
            return ArbitrageCheck(
                is_arbitrage=False,
                profit_margin=Decimal('0'),
                confidence=1.0,
                details={"error": "Need at least 2 legs for arbitrage check"}
            )
        
        try:
            # Calculate total implied probability
            total_implied_prob = Decimal('0')
            bookmaker_odds = {}
            
            for leg in legs:
                if not leg.odds or leg.odds <= Decimal('0'):
                    return ArbitrageCheck(
                        is_arbitrage=False,
                        profit_margin=Decimal('0'),
                        confidence=0.5,
                        details={"error": f"Invalid odds in leg: {leg}"}
                    )
                
                implied_prob = Decimal('1') / leg.odds
                total_implied_prob += implied_prob
                
                if leg.bookmaker not in bookmaker_odds:
                    bookmaker_odds[leg.bookmaker] = []
                bookmaker_odds[leg.bookmaker].append(leg.odds)
            
            # Arbitrage condition: total implied probability < 1
            is_arbitrage = total_implied_prob < Decimal('1')
            profit_margin = Decimal('1') - total_implied_prob
            
            # Calculate required stakes for equal profit
            if is_arbitrage:
                required_stakes = {}
                total_investment = Decimal('1000')  # Example stake
                
                for leg in legs:
                    stake = (total_investment * (Decimal('1') / leg.odds)) / total_implied_prob
                    required_stakes[f"{leg.bookmaker}_{leg.selection}"] = stake
                
                potential_profit = total_investment * profit_margin
            else:
                required_stakes = None
                potential_profit = None
            
            # Confidence scoring
            confidence = self._calculate_arbitrage_confidence(legs, total_implied_prob)
            
            return ArbitrageCheck(
                is_arbitrage=is_arbitrage,
                profit_margin=profit_margin,
                confidence=confidence,
                required_stakes=required_stakes,
                potential_profit=potential_profit,
                details={
                    "total_implied_probability": float(total_implied_prob),
                    "number_of_legs": len(legs),
                    "bookmakers": list(bookmaker_odds.keys())
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error validating arbitrage opportunity: {e}")
            return ArbitrageCheck(
                is_arbitrage=False,
                profit_margin=Decimal('0'),
                confidence=0.0,
                details={"error": str(e)}
            )
    
    def validate_market_consistency(self, market: Market) -> List[ValidationCheck]:
        """
        Validate consistency of odds within a market.
        
        Args:
            market: Market object to validate
            
        Returns:
            List of validation check results
        """
        checks = []
        
        if not market.bets:
            checks.append(ValidationCheck(
                name="market_empty",
                result=ValidationResult.WARNING,
                message="Market contains no bets",
                confidence=1.0
            ))
            return checks
        
        # Check for duplicate selections
        selections = [bet.selection for bet in market.bets]
        if len(selections) != len(set(selections)):
            checks.append(ValidationCheck(
                name="duplicate_selections",
                result=ValidationResult.FAIL,
                message="Market contains duplicate selections",
                confidence=1.0,
                details={"selections": selections}
            ))
        
        # Validate individual odds
        for bet in market.bets:
            odds_checks = self.validate_odds(bet.odds)
            for check in odds_checks:
                check.name = f"bet_odds_{bet.selection}_{check.name}"
                checks.append(check)
        
        # Check for market-specific inconsistencies
        if market.market_type == MarketType.OVER_UNDER:
            checks.extend(self._validate_over_under_market(market))
        elif market.market_type == MarketType.MONEYLINE:
            checks.extend(self._validate_moneyline_market(market))
        elif market.market_type == MarketType.SPREAD:
            checks.extend(self._validate_spread_market(market))
        
        return checks
    
    def _validate_over_under_market(self, market: Market) -> List[ValidationCheck]:
        """Validate over/under market-specific constraints."""
        checks = []
        
        # Over/under markets should have exactly 2 selections
        if len(market.bets) != 2:
            checks.append(ValidationCheck(
                name="over_under_selection_count",
                result=ValidationResult.FAIL,
                message=f"Over/under market should have 2 selections, got {len(market.bets)}",
                confidence=1.0
            ))
        
        # Check if selections are over/under
        selections = [bet.selection for bet in market.bets]
        if len(selections) == 2:
            over_found = any('over' in sel.lower() for sel in selections)
            under_found = any('under' in sel.lower() for sel in selections)
            
            if not (over_found and under_found):
                checks.append(ValidationCheck(
                    name="over_under_selection_format",
                    result=ValidationResult.WARNING,
                    message="Over/under market selections should include 'Over' and 'Under'",
                    confidence=0.8,
                    details={"selections": selections}
                ))
        
        return checks
    
    def _validate_moneyline_market(self, market: Market) -> List[ValidationCheck]:
        """Validate moneyline market-specific constraints."""
        checks = []
        
        # Moneyline markets typically have 2-3 selections (home/away/draw)
        if len(market.bets) < 2 or len(market.bets) > 3:
            checks.append(ValidationCheck(
                name="moneyline_selection_count",
                result=ValidationResult.WARNING,
                message=f"Moneyline market typically has 2-3 selections, got {len(market.bets)}",
                confidence=0.7
            ))
        
        return checks
    
    def _validate_spread_market(self, market: Market) -> List[ValidationCheck]:
        """Validate spread market-specific constraints."""
        checks = []
        
        # Spread markets should have exactly 2 selections
        if len(market.bets) != 2:
            checks.append(ValidationCheck(
                name="spread_selection_count",
                result=ValidationResult.FAIL,
                message=f"Spread market should have 2 selections, got {len(market.bets)}",
                confidence=1.0
            ))
        
        return checks
    
    def validate_arbitrage_opportunity_object(self, opportunity: ArbitrageOpportunity) -> List[ValidationCheck]:
        """
        Validate a complete ArbitrageOpportunity object.
        
        Args:
            opportunity: ArbitrageOpportunity to validate
            
        Returns:
            List of validation check results
        """
        checks = []
        
        # Basic structure validation
        if not opportunity.legs:
            checks.append(ValidationCheck(
                name="opportunity_empty_legs",
                result=ValidationResult.FAIL,
                message="Arbitrage opportunity has no legs",
                confidence=1.0
            ))
            return checks
        
        if len(opportunity.legs) < 2:
            checks.append(ValidationCheck(
                name="opportunity_insufficient_legs",
                result=ValidationResult.FAIL,
                message="Arbitrage opportunity needs at least 2 legs",
                confidence=1.0,
                details={"leg_count": len(opportunity.legs)}
            ))
        
        # Validate each leg
        for i, leg in enumerate(opportunity.legs):
            try:
                leg_checks = self.validate_arbitrage_leg(leg)
                for check in leg_checks:
                    check.name = f"leg_{i}_{check.name}"
                    checks.append(check)
            except Exception as e:
                checks.append(ValidationCheck(
                    name=f"leg_{i}_validation_error",
                    result=ValidationResult.ERROR,
                    message=f"Error validating leg {i}: {e}",
                    confidence=1.0
                ))
        
        # Cross-leg validation
        if len(opportunity.legs) >= 2:
            checks.extend(self._validate_leg_consistency(opportunity.legs))
            checks.extend(self._validate_bookmaker_diversity(opportunity.legs))
            checks.extend(self._validate_market_consistency_cross_leg(opportunity.legs))
        
        return checks
    
    def validate_arbitrage_leg(self, leg: ArbitrageLeg) -> List[ValidationCheck]:
        """Validate individual arbitrage leg."""
        checks = []
        
        # Required field validation
        if not leg.bookmaker:
            checks.append(ValidationCheck(
                name="leg_missing_bookmaker",
                result=ValidationResult.FAIL,
                message="Arbitrage leg missing bookmaker",
                confidence=1.0
            ))
        
        if not leg.selection:
            checks.append(ValidationCheck(
                name="leg_missing_selection",
                result=ValidationResult.FAIL,
                message="Arbitrage leg missing selection",
                confidence=1.0
            ))
        
        if not leg.odds or leg.odds <= Decimal('0'):
            checks.append(ValidationCheck(
                name="leg_invalid_odds",
                result=ValidationResult.FAIL,
                message="Arbitrage leg has invalid odds",
                confidence=1.0,
                details={"odds": str(leg.odds) if leg.odds else "None"}
            ))
        
        # Odds validation
        if leg.odds:
            checks.extend(self.validate_odds(leg.odds))
        
        return checks
    
    def _validate_leg_consistency(self, legs: List[ArbitrageLeg]) -> List[ValidationCheck]:
        """Validate consistency across arbitrage legs."""
        checks = []
        
        # Check if all legs are for the same sport/event
        sports = set()
        events = set()
        
        for leg in legs:
            if hasattr(leg, 'sport') and leg.sport:
                sports.add(leg.sport)
            if hasattr(leg, 'event') and leg.event:
                events.add(leg.event)
        
        if len(sports) > 1:
            checks.append(ValidationCheck(
                name="cross_leg_sport_mismatch",
                result=ValidationResult.FAIL,
                message="Arbitrage legs from different sports",
                confidence=1.0,
                details={"sports": list(sports)}
            ))
        
        if len(events) > 1:
            checks.append(ValidationCheck(
                name="cross_leg_event_mismatch", 
                result=ValidationResult.FAIL,
                message="Arbitrage legs from different events",
                confidence=1.0,
                details={"events": list(events)}
            ))
        
        # Check odds ratio consistency
        if len(legs) == 2:
            odds_ratio = legs[0].odds / legs[1].odds
            if odds_ratio > Decimal('10') or odds_ratio < Decimal('0.1'):
                checks.append(ValidationCheck(
                    name="extreme_odds_ratio",
                    result=ValidationResult.WARNING,
                    message=f"Unusual odds ratio between legs: {odds_ratio:.2f}",
                    confidence=0.6,
                    details={"ratio": float(odds_ratio)}
                ))
        
        return checks
    
    def _validate_bookmaker_diversity(self, legs: List[ArbitrageLeg]) -> List[ValidationCheck]:
        """Validate bookmaker diversity in arbitrage legs."""
        checks = []
        
        bookmakers = [leg.bookmaker for leg in legs if leg.bookmaker]
        unique_bookmakers = set(bookmakers)
        
        if len(unique_bookmakers) == 1:
            checks.append(ValidationCheck(
                name="bookmaker_diversity",
                result=ValidationResult.FAIL,
                message="Arbitrage opportunity uses only one bookmaker",
                confidence=1.0,
                details={"bookmaker": list(unique_bookmakers)[0]}
            ))
        elif len(unique_bookmakers) < len(legs) / 2:
            checks.append(ValidationCheck(
                name="limited_bookmaker_diversity",
                result=ValidationResult.WARNING,
                message="Limited bookmaker diversity in arbitrage opportunity",
                confidence=0.7,
                details={"bookmakers": list(unique_bookmakers), "leg_count": len(legs)}
            ))
        
        return checks
    
    def _validate_market_consistency_cross_leg(self, legs: List[ArbitrageLeg]) -> List[ValidationCheck]:
        """Validate market consistency across legs."""
        checks = []
        
        # Check if selections represent the same market
        selections = [leg.selection.lower() for leg in legs if leg.selection]
        
        # Simple keyword matching for market consistency
        market_keywords = {
            'win': ['win', 'winner', 'victory', 'beat'],
            'over_under': ['over', 'under', 'total'],
            'spread': ['spread', 'handicap', 'line'],
            'draw': ['draw', 'tie', 'equal']
        }
        
        detected_markets = []
        for market_type, keywords in market_keywords.items():
            if any(keyword in ' '.join(selections) for keyword in keywords):
                detected_markets.append(market_type)
        
        if len(detected_markets) > 1:
            checks.append(ValidationCheck(
                name="mixed_market_types",
                result=ValidationResult.WARNING,
                message="Legs appear to be from different market types",
                confidence=0.6,
                details={"detected_markets": detected_markets, "selections": selections}
            ))
        
        return checks
    
    def _calculate_arbitrage_confidence(self, legs: List[ArbitrageLeg], total_implied_prob: Decimal) -> float:
        """
        Calculate confidence score for arbitrage detection.
        
        Args:
            legs: List of arbitrage legs
            total_implied_prob: Total implied probability of all legs
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 1.0
        
        # Reduce confidence for unusual odds values
        for leg in legs:
            if leg.odds and (leg.odds < Decimal('1.1') or leg.odds > Decimal('100')):
                confidence -= 0.1
        
        # Reduce confidence for insufficient bookmaker diversity
        bookmakers = set(leg.bookmaker for leg in legs if leg.bookmaker)
        if len(bookmakers) < 3:
            confidence -= 0.1
        
        # Reduce confidence for poor profit margins (too small to be practical)
        profit_margin = Decimal('1') - total_implied_prob
        if profit_margin < Decimal('0.01'):  # Less than 1%
            confidence -= 0.3
        elif profit_margin > Decimal('0.2'):  # More than 20% (suspicious)
            confidence -= 0.2
        
        # Ensure confidence is within bounds
        return max(0.0, min(1.0, float(confidence)))
    
    def batch_validate_opportunities(self, opportunities: List[ArbitrageOpportunity]) -> Dict[str, Any]:
        """
        Validate multiple arbitrage opportunities in batch.
        
        Args:
            opportunities: List of ArbitrageOpportunity objects
            
        Returns:
            Validation summary with statistics
        """
        total_opportunities = len(opportunities)
        valid_opportunities = 0
        invalid_opportunities = 0
        warning_opportunities = 0
        
        all_checks = []
        arbitrage_opportunities = 0
        total_profit_margins = []
        
        for i, opportunity in enumerate(opportunities):
            checks = self.validate_arbitrage_opportunity_object(opportunity)
            all_checks.extend(checks)
            
            # Categorize opportunity
            has_failures = any(check.result == ValidationResult.FAIL for check in checks)
            has_warnings = any(check.result == ValidationResult.WARNING for check in checks)
            
            if has_failures:
                invalid_opportunities += 1
            elif has_warnings:
                warning_opportunities += 1
            else:
                valid_opportunities += 1
            
            # Check for actual arbitrage
            arbitrage_check = self.validate_arbitrage_opportunity(opportunity.legs)
            if arbitrage_check.is_arbitrage:
                arbitrage_opportunities += 1
                total_profit_margins.append(arbitrage_check.profit_margin)
        
        # Calculate summary statistics
        avg_profit_margin = sum(total_profit_margins, Decimal('0')) / len(total_profit_margins) if total_profit_margins else Decimal('0')
        
        return {
            "total_opportunities": total_opportunities,
            "valid_opportunities": valid_opportunities,
            "invalid_opportunities": invalid_opportunities,
            "warning_opportunities": warning_opportunities,
            "arbitrage_opportunities": arbitrage_opportunities,
            "arbitrage_rate": arbitrage_opportunities / total_opportunities if total_opportunities > 0 else 0,
            "average_profit_margin": float(avg_profit_margin),
            "total_validation_checks": len(all_checks),
            "checks_by_result": {
                "pass": len([c for c in all_checks if c.result == ValidationResult.PASS]),
                "warning": len([c for c in all_checks if c.result == ValidationResult.WARNING]),
                "fail": len([c for c in all_checks if c.result == ValidationResult.FAIL]),
                "error": len([c for c in all_checks if c.result == ValidationResult.ERROR])
            }
        }


def create_sample_opportunity() -> ArbitrageOpportunity:
    """Create a sample arbitrage opportunity for testing."""
    from uuid import uuid4
    
    legs = [
        ArbitrageLeg(
            id=uuid4(),
            bookmaker="BookmakerA",
            selection="Team 1",
            odds=Decimal('2.10'),
            stake=Decimal('476.19'),
            sport=Sport.FOOTBALL,
            market_type=MarketType.MONEYLINE
        ),
        ArbitrageLeg(
            id=uuid4(),
            bookmaker="BookmakerB", 
            selection="Team 2",
            odds=Decimal('2.00'),
            stake=Decimal('500.00'),
            sport=Sport.FOOTBALL,
            market_type=MarketType.MONEYLINE
        )
    ]
    
    return ArbitrageOpportunity(
        id=uuid4(),
        sport=Sport.FOOTBALL,
        event="Test Match",
        market_type=MarketType.MONEYLINE,
        legs=legs,
        created_at=datetime.now(timezone.utc),
        risk_tier=RiskTier.LOW
    )