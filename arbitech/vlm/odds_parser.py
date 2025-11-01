"""
VLM Response Parsing and Validation System

This module provides sophisticated parsing and validation capabilities for VLM responses
and extracted odds data. It integrates with the existing Pydantic models from core/models.py
and provides comprehensive validation against mathematical constraints.

Features:
- Response parsing with confidence scoring
- Odds format normalization (decimal, fractional, American)
- Mathematical validation of odds
- Integration with ArbitrageOpportunity model
- Detailed parsing metadata for debugging
"""

import re
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from typing import Dict, List, Optional, Union, Tuple, Any, Set
from enum import Enum
from uuid import uuid4, UUID

from pydantic import BaseModel, Field, validator, root_validator

from ..storage.models import ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier


# ============================================================================
# ODDS FORMAT ENUMS AND MODELS
# ============================================================================

class OddsFormat(str, Enum):
    """Supported odds formats."""
    DECIMAL = "decimal"          # 2.50, 1.85, etc.
    FRACTIONAL = "fractional"    # 3/2, 4/5, etc.
    AMERICAN = "american"        # +150, -200, etc.
    HONGKONG = "hongkong"        # 0.75, 1.25, etc.
    INDONESIAN = "indonesian"    # 0.75, -2.0, etc.
    MALAYSIAN = "malaysian"      # 0.75, -0.5, etc.


class ParsingStatus(str, Enum):
    """Status of parsing operation."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    VALIDATION_ERROR = "validation_error"
    FORMAT_ERROR = "format_error"


class OddsNormalization(BaseModel):
    """Normalized odds data with format information."""
    
    original_odds: Union[str, Decimal] = Field(..., description="Original odds representation")
    normalized_decimal: Decimal = Field(..., description="Decimal odds (1.0+)")
    
    # Format information
    detected_format: OddsFormat = Field(..., description="Detected original format")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Format detection confidence")
    
    # Conversion details
    conversion_steps: List[str] = Field(default_factory=list, description="Steps taken to normalize")
    conversion_errors: List[str] = Field(default_factory=list, description="Any conversion errors")
    
    # Validation
    is_valid: bool = Field(default=True, description="Whether odds are mathematically valid")
    implied_probability: Decimal = Field(..., ge=0.0, le=1.0, description="Implied probability")


class ParsedOdds(BaseModel):
    """Parsed and normalized odds data."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique parsing result ID")
    
    # Basic odds data
    outcome: str = Field(..., min_length=1, max_length=200, description="Betting outcome")
    sport: Sport = Field(..., description="Sport type")
    market_type: str = Field(..., min_length=1, max_length=100, description="Market type")
    
    # Normalized odds
    decimal_odds: Decimal = Field(..., gt=Decimal('1.0'), description="Decimal odds")
    implied_probability: Decimal = Field(..., ge=Decimal('0.0'), le=Decimal('1.0'), 
                                         description="Implied probability")
    
    # Original data
    original_representation: str = Field(..., description="Original odds representation")
    original_format: OddsFormat = Field(..., description="Original odds format")
    
    # Parsing confidence and quality
    parsing_confidence: float = Field(..., ge=0.0, le=1.0, description="Parsing confidence score")
    format_confidence: float = Field(..., ge=0.0, le=1.0, description="Format detection confidence")
    
    # Market context
    bookmaker: str = Field(..., description="Source bookmaker")
    event_name: str = Field(..., description="Associated event name")
    event_date: Optional[datetime] = Field(None, description="Event date if available")
    
    # Additional data
    is_live_odds: bool = Field(default=False, description="Whether these are live odds")
    stake_range: Optional[Tuple[Decimal, Decimal]] = Field(
        None, description="Available stake range (min, max)"
    )
    
    # Validation status
    validation_status: ParsingStatus = Field(..., description="Validation status")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    
    # Timestamps
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('decimal_odds')
    def validate_decimal_odds(cls, v):
        """Validate decimal odds."""
        if v <= Decimal('1.0'):
            raise ValueError("Decimal odds must be greater than 1.0")
        return v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @validator('implied_probability')
    def validate_implied_probability(cls, v):
        """Validate implied probability."""
        if v <= Decimal('0.0') or v >= Decimal('1.0'):
            raise ValueError("Implied probability must be between 0 and 1 (exclusive)")
        return v.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)


class MarketParseResult(BaseModel):
    """Result of parsing a complete betting market."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique market result ID")
    
    # Market identification
    sport: Sport = Field(..., description="Sport type")
    market_type: str = Field(..., description="Market type")
    event_name: str = Field(..., description="Event name")
    event_date: Optional[datetime] = Field(None, description="Event date")
    
    # Parsed odds
    parsed_odds: List[ParsedOdds] = Field(default_factory=list, description="All parsed odds in market")
    
    # Bookmaker information
    bookmaker: str = Field(..., description="Source bookmaker")
    bookmaker_odds: Dict[str, ParsedOdds] = Field(
        default_factory=dict, description="Odds mapped by outcome"
    )
    
    # Parsing summary
    parsing_status: ParsingStatus = Field(..., description="Overall parsing status")
    total_outcomes: int = Field(..., ge=0, description="Total number of outcomes")
    successful_odds: int = Field(..., ge=0, description="Successfully parsed odds")
    failed_odds: int = Field(..., ge=0, description="Failed odds")
    
    # Quality metrics
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall parsing confidence")
    data_completeness: float = Field(..., ge=0.0, le=1.0, description="Data completeness score")
    
    # Arbitrage potential
    arbitrage_potential: Optional[Dict[str, Any]] = Field(
        None, description="Arbitrage calculation results"
    )
    
    # Metadata
    parsing_metadata: 'ParsingMetadata' = Field(..., description="Detailed parsing metadata")
    
    # Timestamps
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @root_validator
    def validate_market_consistency(cls, values):
        """Validate market data consistency."""
        parsed_odds = values.get('parsed_odds', [])
        
        # Check that we have odds for all detected outcomes
        outcomes = set(odd.outcome for odd in parsed_odds)
        if len(outcomes) < 2:
            raise ValueError("Market must have at least 2 outcomes")
        
        return values


class ParsingMetadata(BaseModel):
    """Detailed metadata for parsing process."""
    
    # Source information
    source_type: str = Field(..., description="Type of source (VLM, API, etc.)")
    raw_response: str = Field(..., description="Raw parsing input")
    
    # Processing details
    parsing_time_ms: int = Field(..., ge=0, description="Parsing time in milliseconds")
    format_detection_attempts: int = Field(default=0, ge=0, description="Format detection attempts")
    normalization_steps: List[str] = Field(default_factory=list, description="Normalization steps taken")
    
    # Quality indicators
    data_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall data quality")
    text_clarity_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Text clarity score")
    layout_complexity_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Layout complexity")
    
    # Error tracking
    parsing_errors: List[str] = Field(default_factory=list, description="Parsing errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Parsing warnings")
    skipped_elements: List[str] = Field(default_factory=list, description="Elements that were skipped")
    
    # Validation metrics
    mathematical_validation_passed: bool = Field(default=True, description="Mathematical validation status")
    constraint_violations: List[str] = Field(default_factory=list, description="Constraint violations")
    
    # Additional context
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Additional context data")
    
    # Template information
    template_used: Optional[str] = Field(None, description="Parsing template used")
    template_version: Optional[str] = Field(None, description="Template version")


# ============================================================================
# MAIN ODDS PARSER ENGINE
# ============================================================================

class OddsParser:
    """
    Sophisticated odds parsing and validation engine.
    
    This class provides comprehensive parsing capabilities for various odds formats
    with mathematical validation and integration with the ArbitrageOpportunity model.
    """
    
    def __init__(self):
        """Initialize the odds parser."""
        self.logger = logging.getLogger(__name__)
        
        # Format patterns for detection
        self.odds_patterns = {
            OddsFormat.DECIMAL: re.compile(r'^\d+\.?\d*$'),
            OddsFormat.FRACTIONAL: re.compile(r'^(\d+)/(\d+)$'),
            OddsFormat.AMERICAN: re.compile(r'^([+-]?\d+)$'),
            OddsFormat.HONGKONG: re.compile(r'^\d+\.?\d*$'),
            OddsFormat.INDONESIAN: re.compile(r'^([+-]?\d+\.?\d*)$'),
            OddsFormat.MALAYSIAN: re.compile(r'^([+-]?\d+\.?\d*)$')
        }
        
        # Market type keywords for detection
        self.market_keywords = {
            'match_winner': ['winner', 'win', 'victory', 'victor', 'outcome'],
            'over_under': ['over', 'under', 'total', 'goals', 'points'],
            'handicap': ['handicap', 'spread', 'line', 'advantage'],
            'both_teams_score': ['both teams', 'btts', 'both to score'],
            'first_half': ['first half', '1h', 'ht'],
            'second_half': ['second half', '2h', 'second'],
            'corner_kicks': ['corners', 'corner'],
            'cards': ['cards', 'yellow', 'red'],
            'player_props': ['player', 'goalscorer', 'scorer'],
            'specials': ['special', 'misc', 'other']
        }
    
    async def parse_vlm_response(
        self,
        raw_response: str,
        bookmaker: str,
        sport: Sport,
        market_type: str,
        event_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> MarketParseResult:
        """
        Parse a VLM response containing odds data.
        
        Args:
            raw_response: Raw VLM response text
            bookmaker: Source bookmaker name
            sport: Sport type
            market_type: Market type
            event_name: Event name
            context: Additional parsing context
            
        Returns:
            MarketParseResult with parsed odds and metadata
        """
        start_time = datetime.now()
        context = context or {}
        
        try:
            self.logger.info("Parsing VLM response for %s - %s", bookmaker, event_name)
            
            # Extract structured data from response
            parsed_data = self._extract_structured_data(raw_response)
            
            # Parse individual odds
            parsed_odds_list = []
            parsing_errors = []
            
            for outcome, odds_text in parsed_data.get('odds', {}).items():
                try:
                    parsed_odd = await self._parse_single_odd(
                        outcome=outcome,
                        odds_text=str(odds_text),
                        bookmaker=bookmaker,
                        sport=sport,
                        market_type=market_type,
                        event_name=event_name,
                        context=context
                    )
                    
                    if parsed_odd:
                        parsed_odds_list.append(parsed_odd)
                    
                except Exception as e:
                    error_msg = f"Failed to parse odds for {outcome}: {str(e)}"
                    self.logger.warning(error_msg)
                    parsing_errors.append(error_msg)
            
            # Create odds mapping
            odds_mapping = {odd.outcome: odd for odd in parsed_odds_list}
            
            # Calculate quality metrics
            overall_confidence = self._calculate_overall_confidence(parsed_odds_list)
            data_completeness = self._calculate_data_completeness(parsed_odds_list, len(parsed_data.get('outcomes', [])))
            
            # Determine parsing status
            parsing_status = self._determine_parsing_status(parsed_odds_list, parsing_errors)
            
            # Calculate parsing time
            parsing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Create metadata
            metadata = ParsingMetadata(
                source_type="VLM",
                raw_response=raw_response,
                parsing_time_ms=parsing_time,
                data_quality_score=(overall_confidence + data_completeness) / 2,
                parsing_errors=parsing_errors,
                template_used=context.get('template_used'),
                template_version=context.get('template_version')
            )
            
            # Check for arbitrage potential
            arbitrage_potential = self._calculate_arbitrage_potential(parsed_odds_list) if len(parsed_odds_list) >= 2 else None
            
            result = MarketParseResult(
                sport=sport,
                market_type=market_type,
                event_name=event_name,
                parsed_odds=parsed_odds_list,
                bookmaker=bookmaker,
                bookmaker_odds=odds_mapping,
                parsing_status=parsing_status,
                total_outcomes=len(parsed_data.get('outcomes', [])),
                successful_odds=len(parsed_odds_list),
                failed_odds=len(parsing_errors),
                overall_confidence=overall_confidence,
                data_completeness=data_completeness,
                arbitrage_potential=arbitrage_potential,
                parsing_metadata=metadata
            )
            
            self.logger.info("Successfully parsed %d odds for %s", len(parsed_odds_list), bookmaker)
            return result
            
        except Exception as e:
            self.logger.error("Failed to parse VLM response: %s", str(e))
            
            # Return error result
            parsing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            metadata = ParsingMetadata(
                source_type="VLM",
                raw_response=raw_response,
                parsing_time_ms=parsing_time,
                data_quality_score=0.0,
                parsing_errors=[str(e)]
            )
            
            return MarketParseResult(
                sport=sport,
                market_type=market_type,
                event_name=event_name,
                parsed_odds=[],
                bookmaker=bookmaker,
                parsing_status=ParsingStatus.FAILED,
                total_outcomes=0,
                successful_odds=0,
                failed_odds=1,
                overall_confidence=0.0,
                data_completeness=0.0,
                parsing_metadata=metadata
            )
    
    async def _parse_single_odd(
        self,
        outcome: str,
        odds_text: str,
        bookmaker: str,
        sport: Sport,
        market_type: str,
        event_name: str,
        context: Dict[str, Any]
    ) -> Optional[ParsedOdds]:
        """
        Parse a single odds entry.
        
        Args:
            outcome: Betting outcome
            odds_text: Odds representation
            bookmaker: Source bookmaker
            sport: Sport type
            market_type: Market type
            event_name: Event name
            context: Parsing context
            
        Returns:
            ParsedOdds object or None if parsing fails
        """
        try:
            # Normalize the odds
            normalized = await self._normalize_odds(odds_text)
            
            if not normalized.is_valid:
                raise ValueError(f"Invalid odds: {normalized.conversion_errors}")
            
            # Create ParsedOdds object
            parsed_odd = ParsedOdds(
                outcome=outcome,
                sport=sport,
                market_type=market_type,
                decimal_odds=normalized.normalized_decimal,
                implied_probability=normalized.implied_probability,
                original_representation=odds_text,
                original_format=normalized.detected_format,
                parsing_confidence=normalized.confidence,
                format_confidence=normalized.confidence,
                bookmaker=bookmaker,
                event_name=event_name,
                validation_status=ParsingStatus.SUCCESS if normalized.is_valid else ParsingStatus.VALIDATION_ERROR,
                validation_errors=normalized.conversion_errors
            )
            
            return parsed_odd
            
        except Exception as e:
            self.logger.warning("Failed to parse single odd for %s: %s", outcome, str(e))
            return None
    
    async def _normalize_odds(self, odds_text: str) -> OddsNormalization:
        """
        Normalize odds text to decimal format.
        
        Args:
            odds_text: Raw odds text
            
        Returns:
            OddsNormalization with normalized data
        """
        conversion_steps = []
        conversion_errors = []
        
        # Detect format
        detected_format, format_confidence = self._detect_odds_format(odds_text)
        
        try:
            # Normalize based on detected format
            if detected_format == OddsFormat.DECIMAL:
                normalized, steps = self._normalize_decimal(odds_text)
            elif detected_format == OddsFormat.FRACTIONAL:
                normalized, steps = self._normalize_fractional(odds_text)
            elif detected_format == OddsFormat.AMERICAN:
                normalized, steps = self._normalize_american(odds_text)
            elif detected_format == OddsFormat.HONGKONG:
                normalized, steps = self._normalize_hongkong(odds_text)
            elif detected_format == OddsFormat.INDONESIAN:
                normalized, steps = self._normalize_indonesian(odds_text)
            elif detected_format == OddsFormat.MALAYSIAN:
                normalized, steps = self._normalize_malaysian(odds_text)
            else:
                raise ValueError(f"Unsupported odds format: {detected_format}")
            
            conversion_steps.extend(steps)
            
            # Validate normalized odds
            is_valid = normalized > Decimal('1.0')
            implied_probability = Decimal('1.0') / normalized
            
            return OddsNormalization(
                original_odds=odds_text,
                normalized_decimal=normalized,
                detected_format=detected_format,
                confidence=format_confidence,
                conversion_steps=conversion_steps,
                conversion_errors=conversion_errors,
                is_valid=is_valid,
                implied_probability=implied_probability
            )
            
        except Exception as e:
            conversion_errors.append(str(e))
            return OddsNormalization(
                original_odds=odds_text,
                normalized_decimal=Decimal('0.0'),
                detected_format=detected_format,
                confidence=0.0,
                conversion_steps=conversion_steps,
                conversion_errors=conversion_errors,
                is_valid=False,
                implied_probability=Decimal('0.0')
            )
    
    def _detect_odds_format(self, odds_text: str) -> Tuple[OddsFormat, float]:
        """
        Detect the format of odds text.
        
        Args:
            odds_text: Odds representation
            
        Returns:
            Tuple of (detected_format, confidence)
        """
        odds_text = odds_text.strip()
        
        # Try each pattern
        for format_type, pattern in self.odds_patterns.items():
            if pattern.match(odds_text):
                return format_type, 0.9
        
        # Fallback: try to determine by value ranges
        try:
            # Try decimal first
            decimal_value = float(odds_text)
            if 1.0 < decimal_value <= 1000.0:
                return OddsFormat.DECIMAL, 0.7
        except ValueError:
            pass
        
        # If we can't determine, assume decimal with low confidence
        return OddsFormat.DECIMAL, 0.3
    
    def _normalize_decimal(self, odds_text: str) -> Tuple[Decimal, List[str]]:
        """Normalize decimal odds."""
        try:
            decimal_value = Decimal(odds_text)
            return decimal_value, ["Converted to decimal"]
        except ValueError as e:
            raise ValueError(f"Invalid decimal odds: {odds_text}") from e
    
    def _normalize_fractional(self, odds_text: str) -> Tuple[Decimal, List[str]]:
        """Normalize fractional odds to decimal."""
        match = re.match(r'^(\d+)/(\d+)$', odds_text)
        if not match:
            raise ValueError(f"Invalid fractional format: {odds_text}")
        
        numerator = int(match.group(1))
        denominator = int(match.group(2))
        
        if denominator == 0:
            raise ValueError(f"Invalid fractional odds (division by zero): {odds_text}")
        
        decimal_value = Decimal(numerator) / Decimal(denominator) + Decimal('1.0')
        steps = [f"Converted {numerator}/{denominator} to decimal"]
        return decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), steps
    
    def _normalize_american(self, odds_text: str) -> Tuple[Decimal, List[str]]:
        """Normalize American odds to decimal."""
        try:
            american_odds = int(odds_text)
            
            if american_odds > 0:
                decimal_value = (Decimal(american_odds) / Decimal('100')) + Decimal('1.0')
            elif american_odds < 0:
                decimal_value = (Decimal('100') / Decimal(abs(american_odds))) + Decimal('1.0')
            else:
                raise ValueError("Invalid American odds: 0")
            
            return decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), [
                f"Converted American {american_odds} to decimal"
            ]
            
        except ValueError as e:
            raise ValueError(f"Invalid American odds: {odds_text}") from e
    
    def _normalize_hongkong(self, odds_text: str) -> Tuple[Decimal, List[str]]:
        """Normalize Hong Kong odds to decimal."""
        try:
            hk_value = Decimal(odds_text)
            decimal_value = hk_value + Decimal('1.0')
            return decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), [
                f"Converted Hong Kong {hk_value} to decimal"
            ]
        except ValueError as e:
            raise ValueError(f"Invalid Hong Kong odds: {odds_text}") from e
    
    def _normalize_indonesian(self, odds_text: str) -> Tuple[Decimal, List[str]]:
        """Normalize Indonesian odds to decimal."""
        try:
            indo_value = Decimal(odds_text)
            
            if indo_value >= 0:
                decimal_value = indo_value + Decimal('1.0')
            else:
                # Negative Indonesian odds: 1 + (1/abs(value))
                decimal_value = Decimal('1.0') + (Decimal('1.0') / abs(indo_value))
            
            return decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), [
                f"Converted Indonesian {indo_value} to decimal"
            ]
        except ValueError as e:
            raise ValueError(f"Invalid Indonesian odds: {odds_text}") from e
    
    def _normalize_malaysian(self, odds_text: str) -> Tuple[Decimal, List[str]]:
        """Normalize Malaysian odds to decimal."""
        try:
            malay_value = Decimal(odds_text)
            
            if malay_value >= 0:
                # Positive Malaysian odds: same as Hong Kong
                decimal_value = malay_value + Decimal('1.0')
            else:
                # Negative Malaysian odds: different formula
                decimal_value = Decimal('1.0') - malay_value
            
            return decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), [
                f"Converted Malaysian {malay_value} to decimal"
            ]
        except ValueError as e:
            raise ValueError(f"Invalid Malaysian odds: {odds_text}") from e
    
    def _extract_structured_data(self, raw_response: str) -> Dict[str, Any]:
        """
        Extract structured data from raw VLM response.
        
        Args:
            raw_response: Raw response text
            
        Returns:
            Dictionary with extracted data
        """
        import json
        import re
        
        # Try to extract JSON
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        
        if json_match:
            try:
                json_str = json_match.group(0)
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to parse key-value pairs
        data = {"outcomes": [], "odds": {}}
        
        # Look for patterns like "outcome: odds"
        lines = raw_response.split('\n')
        for line in lines:
            line = line.strip()
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    outcome = parts[0].strip()
                    odds_value = parts[1].strip()
                    
                    if outcome and odds_value:
                        data["outcomes"].append(outcome)
                        data["odds"][outcome] = odds_value
        
        return data
    
    def _calculate_overall_confidence(self, parsed_odds: List[ParsedOdds]) -> float:
        """Calculate overall confidence score."""
        if not parsed_odds:
            return 0.0
        
        total_confidence = sum(odd.parsing_confidence for odd in parsed_odds)
        return total_confidence / len(parsed_odds)
    
    def _calculate_data_completeness(self, parsed_odds: List[ParsedOdds], total_expected: int) -> float:
        """Calculate data completeness score."""
        if total_expected == 0:
            return 1.0 if not parsed_odds else 0.0
        
        return min(len(parsed_odds) / total_expected, 1.0)
    
    def _determine_parsing_status(self, parsed_odds: List[ParsedOdds], errors: List[str]) -> ParsingStatus:
        """Determine overall parsing status."""
        if not parsed_odds and not errors:
            return ParsingStatus.FAILED
        elif not parsed_odds:
            return ParsingStatus.FAILED
        elif errors:
            return ParsingStatus.PARTIAL_SUCCESS
        else:
            return ParsingStatus.SUCCESS
    
    def _calculate_arbitrage_potential(self, parsed_odds: List[ParsedOdds]) -> Optional[Dict[str, Any]]:
        """Calculate arbitrage potential for the market."""
        if len(parsed_odds) < 2:
            return None
        
        try:
            # Calculate combined implied probability
            total_implied_probability = sum(odd.implied_probability for odd in parsed_odds)
            
            if total_implied_probability < Decimal('1.0'):
                # Arbitrage opportunity exists
                profit_margin = (Decimal('1.0') / total_implied_probability - Decimal('1.0')) * Decimal('100')
                
                # Calculate optimal stakes (equal profit on all outcomes)
                stakes = []
                for odd in parsed_odds:
                    # Stake = total_potential_return / odds
                    # For equal profit: stake = 1 / odds
                    stakes.append(Decimal('1.0') / odd.decimal_odds)
                
                # Normalize stakes to sum to 1.0
                total_stake = sum(stakes)
                normalized_stakes = [stake / total_stake for stake in stakes]
                
                return {
                    "arbitrage_exists": True,
                    "profit_margin_percent": float(profit_margin.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                    "combined_implied_probability": float(total_implied_probability.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)),
                    "optimal_stakes": {
                        odd.outcome: float(stake.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))
                        for odd, stake in zip(parsed_odds, normalized_stakes)
                    },
                    "expected_return_percent": float(((Decimal('1.0') / total_implied_probability) * Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                }
            else:
                return {
                    "arbitrage_exists": False,
                    "combined_implied_probability": float(total_implied_probability.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))
                }
                
        except Exception as e:
            self.logger.warning("Failed to calculate arbitrage potential: %s", str(e))
            return None
    
    def validate_odds_constraints(self, odds: List[ParsedOdds]) -> Tuple[bool, List[str]]:
        """
        Validate odds against mathematical constraints.
        
        Args:
            odds: List of parsed odds to validate
            
        Returns:
            Tuple of (is_valid, violation_messages)
        """
        violations = []
        
        if len(odds) < 2:
            violations.append("Insufficient odds for validation (need at least 2)")
            return False, violations
        
        # Check for reasonable odds ranges
        for odd in odds:
            if odd.decimal_odds < Decimal('1.01'):
                violations.append(f"Odds too low for {odd.outcome}: {odd.decimal_odds}")
            elif odd.decimal_odds > Decimal('1000.0'):
                violations.append(f"Odds too high for {odd.outcome}: {odd.decimal_odds}")
        
        # Check implied probabilities sum reasonably
        total_implied = sum(odd.implied_probability for odd in odds)
        
        if total_implied > Decimal('2.0'):
            violations.append(f"Total implied probability too high: {total_implied}")
        elif total_implied < Decimal('0.1'):
            violations.append(f"Total implied probability too low: {total_implied}")
        
        # Check for duplicate outcomes
        outcomes = [odd.outcome for odd in odds]
        if len(outcomes) != len(set(outcomes)):
            violations.append("Duplicate outcomes detected")
        
        return len(violations) == 0, violations


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def parse_odds_string(
    odds_text: str,
    outcome: str,
    bookmaker: str,
    sport: Sport,
    market_type: str,
    event_name: str
) -> ParsedOdds:
    """
    Convenience function to parse a single odds string.
    
    Args:
        odds_text: Odds representation
        outcome: Betting outcome
        bookmaker: Source bookmaker
        sport: Sport type
        market_type: Market type
        event_name: Event name
        
    Returns:
        ParsedOdds object
    """
    parser = OddsParser()
    
    # Use a simple market result structure
    result = await parser.parse_vlm_response(
        raw_response=f"{outcome}: {odds_text}",
        bookmaker=bookmaker,
        sport=sport,
        market_type=market_type,
        event_name=event_name
    )
    
    if result.parsed_odds:
        return result.parsed_odds[0]
    else:
        raise ValueError(f"Failed to parse odds: {odds_text}")


async def create_arbitrage_opportunity(
    market_results: List[MarketParseResult],
    min_profit_margin: float = 2.0
) -> Optional[ArbitrageOpportunity]:
    """
    Create an ArbitrageOpportunity from multiple market parse results.
    
    Args:
        market_results: List of market parse results from different bookmakers
        min_profit_margin: Minimum profit margin to consider
        
    Returns:
        ArbitrageOpportunity or None if no arbitrage exists
    """
    if len(market_results) < 2:
        return None
    
    # Find common market across bookmakers
    sport = market_results[0].sport
    market_type = market_results[0].market_type
    event_name = market_results[0].event_name
    event_date = market_results[0].event_date
    
    # Verify all markets are the same
    for result in market_results:
        if (result.sport != sport or 
            result.market_type != market_type or 
            result.event_name != event_name):
            return None
    
    # Collect odds by outcome across bookmakers
    outcome_odds = {}
    for result in market_results:
        for outcome, odd in result.bookmaker_odds.items():
            if outcome not in outcome_odds:
                outcome_odds[outcome] = []
            outcome_odds[outcome].append((result.bookmaker, odd))
    
    # Find arbitrage opportunities
    arbitrage_legs = []
    for outcome, odds_list in outcome_odds.items():
        # Use the best odds for each outcome
        best_bookmaker, best_odd = max(odds_list, key=lambda x: x[1].decimal_odds)
        
        arbitrage_legs.append(ArbitrageLeg(
            bookmaker=best_bookmaker,
            event_outcome=outcome,
            odds=best_odd.decimal_odds,
            implied_probability=best_odd.implied_probability,
            stake_percentage=Decimal('0.0'),  # Will be calculated later
            actual_stake=Decimal('0.0'),     # Will be calculated later
            potential_payout=Decimal('0.0')  # Will be calculated later
        ))
    
    if len(arbitrage_legs) < 2:
        return None
    
    # Calculate arbitrage calculations
    total_implied_probability = sum(leg.implied_probability for leg in arbitrage_legs)
    
    if total_implied_probability >= Decimal('1.0'):
        return None  # No arbitrage opportunity
    
    # Calculate profit margin
    profit_margin = (Decimal('1.0') / total_implied_probability - Decimal('1.0')) * Decimal('100')
    
    if profit_margin < Decimal(str(min_profit_margin)):
        return None  # Below minimum profit margin
    
    # Calculate optimal stakes
    total_stake = Decimal('100.0')  # Assume $100 total stake for calculation
    
    for leg in arbitrage_legs:
        leg.stake_percentage = (Decimal('1.0') / leg.decimal_odds) / total_implied_probability
        leg.actual_stake = total_stake * leg.stake_percentage
        leg.potential_payout = leg.actual_stake * leg.odds
    
    profit_amount = (total_stake / total_implied_probability) - total_stake
    
    return ArbitrageOpportunity(
        sport=sport,
        event_name=event_name,
        event_date=event_date or datetime.now(),
        market_type=market_type,
        legs=arbitrage_legs,
        total_stake=total_stake,
        profit_margin=profit_margin,
        profit_amount=profit_amount,
        risk_tier=RiskTier.TIER_A,  # Default tier
        source_scanner="VLM_OddsParser"
    )


# Update forward references
MarketParseResult.update_forward_refs()
ParsingMetadata.update_forward_refs()