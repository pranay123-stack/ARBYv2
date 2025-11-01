"""
Bookmaker Template System for VLM Odds Extraction

This module provides sophisticated templates for different bookmaker interfaces,
each with specific prompts and parsing rules optimized for VLM extraction.

Supported bookmakers:
- Betfair: Exchange-style interface
- Pinnacle: Clean, professional layout
- BetDex: Modern betting interface
- Aver: Regional bookmaker layout

Features:
- Customizable prompts for each bookmaker
- Interface-specific parsing rules
- Dynamic prompt generation
- Template versioning and updates
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from uuid import uuid4, UUID

from pydantic import BaseModel, Field

from ..storage.models import Sport


# ============================================================================
# BASE TEMPLATE SYSTEM
# ============================================================================

class BookmakerTemplate(ABC):
    """
    Abstract base class for bookmaker-specific extraction templates.
    
    Each template provides customized prompts and parsing rules optimized
    for the specific interface layout of a bookmaker.
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """
        Initialize bookmaker template.
        
        Args:
            name: Template name
            version: Template version
        """
        self.name = name
        self.version = version
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def get_extraction_prompt(self, sport: Sport, market_type: str) -> str:
        """
        Get the extraction prompt for this bookmaker.
        
        Args:
            sport: Sport type
            market_type: Market type
            
        Returns:
            Formatted extraction prompt
        """
        pass
    
    @abstractmethod
    def get_parsing_rules(self) -> Dict[str, Any]:
        """
        Get parsing rules specific to this bookmaker.
        
        Returns:
            Dictionary of parsing rules
        """
        pass
    
    @abstractmethod
    def get_odds_format_hints(self) -> Dict[str, str]:
        """
        Get odds format hints for this bookmaker.
        
        Returns:
            Dictionary mapping formats to regex patterns
        """
        pass
    
    def get_supported_sports(self) -> List[Sport]:
        """Get list of supported sports for this bookmaker."""
        return [
            Sport.FOOTBALL, Sport.BASKETBALL, Sport.TENNIS, 
            Sport.BASEBALL, Sport.HOCKEY, Sport.MMA
        ]
    
    def get_interface_keywords(self) -> Dict[str, List[str]]:
        """
        Get interface-specific keywords for outcome detection.
        
        Returns:
            Dictionary mapping outcomes to interface terms
        """
        return {
            "home_win": ["home", "home team", "team 1", "1"],
            "away_win": ["away", "away team", "team 2", "2"],
            "draw": ["draw", "tie", "x"],
            "over": ["over", "o"],
            "under": ["under", "u"],
            "both_teams_score": ["both teams", "btts", "gg"]
        }
    
    def validate_extraction_context(
        self, 
        sport: Sport, 
        market_type: str
    ) -> tuple[bool, List[str]]:
        """
        Validate if this template can handle the extraction context.
        
        Args:
            sport: Sport type
            market_type: Market type
            
        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings = []
        
        # Check if sport is supported
        if sport not in self.get_supported_sports():
            warnings.append(f"Sport {sport} may not be fully supported")
        
        # Check market type compatibility
        common_markets = ["match_winner", "over_under", "handicap"]
        if market_type not in common_markets:
            warnings.append(f"Market type '{market_type}' may require additional configuration")
        
        return len(warnings) <= 1, warnings  # Allow 1 warning, but not more


class TemplateMetadata(BaseModel):
    """Metadata for template information."""
    
    template_id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Template name")
    version: str = Field(..., description="Template version")
    bookmaker: str = Field(..., description="Bookmaker name")
    description: Optional[str] = Field(None, description="Template description")
    
    # Compatibility information
    supported_sports: List[Sport] = Field(..., description="Supported sports")
    supported_markets: List[str] = Field(..., description="Supported market types")
    
    # Performance characteristics
    average_accuracy: float = Field(default=0.85, ge=0.0, le=1.0, description="Average extraction accuracy")
    average_extraction_time_ms: int = Field(default=2500, ge=0, description="Average extraction time")
    
    # Update information
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_validation: Optional[datetime] = Field(None, description="Last template validation")
    
    # Quality metrics
    success_rate: float = Field(default=0.9, ge=0.0, le=1.0, description="Historical success rate")
    common_errors: List[str] = Field(default_factory=list, description="Common extraction errors")
    
    # Configuration
    is_active: bool = Field(default=True, description="Whether template is active")
    is_experimental: bool = Field(default=False, description="Whether template is experimental")


# ============================================================================
# CONCRETE BOOKMAKER TEMPLATES
# ============================================================================

class BetfairTemplate(BookmakerTemplate):
    """
    Betfair Exchange interface template.
    
    Betfair uses an exchange-style layout with back and lay betting options,
    unique decimal odds formatting, and commission-based model.
    """
    
    def __init__(self):
        super().__init__("betfair_exchange", "1.0.0")
        self.bookmaker_name = "Betfair"
    
    def get_extraction_prompt(self, sport: Sport, market_type: str) -> str:
        """Get Betfair-specific extraction prompt."""
        return f"""
        Extract betting odds from the Betfair Exchange interface for {sport.value} - {market_type}.
        
        Betfair Interface Notes:
        - Uses decimal odds with 2 decimal places (e.g., 2.50)
        - Shows both BACK and LAY odds for each outcome
        - Exchange commission (typically 5%) applies
        - Interface shows "Back" and "Lay" buttons/options
        
        Focus on:
        1. BACK odds (what you can BET ON at these odds)
        2. Match the outcome names to standard betting terms
        3. Look for the primary odds displayed prominently
        
        Key outcome mappings:
        - Home team/player = "Home Win"
        - Away team/player = "Away Win" 
        - Draw/Tie = "Draw"
        - Over 0.5/1.5/2.5/3.5 goals = "Over X.5"
        - Under 0.5/1.5/2.5/3.5 goals = "Under X.5"
        
        Ignore:
        - Very small odds (< 1.10) unless clearly visible
        - Lay odds unless specifically requested
        - Unusual market variants
        """
    
    def get_parsing_rules(self) -> Dict[str, Any]:
        """Get Betfair-specific parsing rules."""
        return {
            "odds_format": "decimal",
            "odds_decimal_places": 2,
            "primary_odds_field": "back_odds",
            "outcome_detection": {
                "home_team_keywords": ["home", "team 1", "1", "home team"],
                "away_team_keywords": ["away", "team 2", "2", "away team"],
                "draw_keywords": ["draw", "tie", "x", "the draw"],
                "over_under_keywords": {
                    "over": ["over", "o"],
                    "under": ["under", "u"]
                }
            },
            "confidence_indicators": {
                "high_confidence": ["prominently displayed", "large font", "highlighted"],
                "medium_confidence": ["normal display", "standard font"],
                "low_confidence": ["small text", "secondary position", "footnote"]
            },
            "commission_note": "Apply 5% commission to final calculations",
            "rate_limit_considerations": True,
            "exchange_specific": True
        }
    
    def get_odds_format_hints(self) -> Dict[str, str]:
        """Get Betfair odds format hints."""
        return {
            "decimal": r'^\d+\.\d{2}$',  # Always 2 decimal places
            "fractional": None,  # Not used by Betfair
            "american": None     # Not used by Betfair
        }
    
    def get_supported_sports(self) -> List[Sport]:
        """Get Betfair-supported sports."""
        return [
            Sport.FOOTBALL, Sport.TENNIS, Sport.BASKETBALL, 
            Sport.HORSE_RACING, Sport.CRICKET, Sport.GOLF
        ]


class PinnacleTemplate(BookmakerTemplate):
    """
    Pinnacle interface template.
    
    Pinnacle is known for clean, professional interface design with
    straightforward decimal odds and comprehensive market coverage.
    """
    
    def __init__(self):
        super().__init__("pinnacle_standard", "1.0.0")
        self.bookmaker_name = "Pinnacle"
    
    def get_extraction_prompt(self, sport: Sport, market_type: str) -> str:
        """Get Pinnacle-specific extraction prompt."""
        return f"""
        Extract betting odds from the Pinnacle interface for {sport.value} - {market_type}.
        
        Pinnacle Interface Notes:
        - Clean, minimalist design with clear typography
        - Uses decimal odds with 2-3 decimal places
        - No bonuses or promotional distractions
        - Professional layout with clear sections
        
        Focus on:
        1. Main odds displayed in the center column
        2. Team/player names on the left
        3. Standard betting terminology
        
        Key outcome mappings:
        - Team/Player names directly map to outcomes
        - Use explicit team/player names where possible
        - Standard over/under format: "Over X.5 Goals"
        
        Look for:
        - Clean white backgrounds
        - Clear, readable fonts
        - Logical left-to-right layout
        - Consistent spacing between elements
        """
    
    def get_parsing_rules(self) -> Dict[str, Any]:
        """Get Pinnacle-specific parsing rules."""
        return {
            "odds_format": "decimal",
            "odds_decimal_places": [2, 3],
            "layout_style": "clean_minimal",
            "outcome_detection": {
                "primary_source": "team_names",
                "mapping_strategy": "direct",
                "fallback_mapping": "standard_terms"
            },
            "confidence_indicators": {
                "high_confidence": ["clean display", "clear typography", "center column"],
                "medium_confidence": ["normal layout", "standard positioning"],
                "low_confidence": ["edge cases", "small markets"]
            },
            "quality_indicators": {
                "professional_layout": True,
                "clear_separation": True,
                "consistent_formatting": True
            },
            "rate_limit_considerations": False,
            "exchange_specific": False
        }
    
    def get_odds_format_hints(self) -> Dict[str, str]:
        """Get Pinnacle odds format hints."""
        return {
            "decimal": r'^\d+\.\d{2,3}$',  # 2-3 decimal places
            "fractional": None,
            "american": None
        }
    
    def get_supported_sports(self) -> List[Sport]:
        """Get Pinnacle-supported sports."""
        return [
            Sport.FOOTBALL, Sport.BASKETBALL, Sport.TENNIS,
            Sport.BASEBALL, Sport.HOCKEY, Sport.ESPORTS
        ]


class BetDexTemplate(BookmakerTemplate):
    """
    BetDex interface template.
    
    BetDex represents modern betting interfaces with dynamic content,
    real-time updates, and mobile-first design principles.
    """
    
    def __init__(self):
        super().__init__("betdex_modern", "1.0.0")
        self.bookmaker_name = "BetDex"
    
    def get_extraction_prompt(self, sport: Sport, market_type: str) -> str:
        """Get BetDex-specific extraction prompt."""
        return f"""
        Extract betting odds from the BetDex modern interface for {sport.value} - {market_type}.
        
        BetDex Interface Notes:
        - Modern, responsive design with dynamic content
        - May include promotional elements or "boosted" odds
        - Real-time odds updates with animated elements
        - Mobile-first design principles
        
        Focus on:
        1. Main betting odds in card-based layouts
        2. Avoid promotional or "boosted" odds unless clearly marked
        3. Look for standard market structure
        4. Consider both desktop and mobile layout variations
        
        Key outcome mappings:
        - Card-based layout with outcome names
        - May use abbreviations (H/A for Home/Away)
        - Standard market terminology with modern styling
        
        Be aware of:
        - Dynamic content loading
        - Potential promotional overlays
        - Real-time update animations
        - Responsive layout changes
        """
    
    def get_parsing_rules(self) -> Dict[str, Any]:
        """Get BetDex-specific parsing rules."""
        return {
            "odds_format": "decimal",
            "odds_decimal_places": [1, 2, 3],
            "layout_style": "modern_card_based",
            "outcome_detection": {
                "primary_source": "card_headers",
                "mapping_strategy": "flexible",
                "abbreviation_support": True
            },
            "confidence_indicators": {
                "high_confidence": ["main betting card", "standard layout", "clear headers"],
                "medium_confidence": ["secondary cards", "modified layout"],
                "low_confidence": ["promotional elements", "dynamic content", "mobile view"]
            },
            "quality_indicators": {
                "dynamic_content": True,
                "real_time_updates": True,
                "responsive_design": True
            },
            "promotional_awareness": True,
            "rate_limit_considerations": True,
            "exchange_specific": False
        }
    
    def get_odds_format_hints(self) -> Dict[str, str]:
        """Get BetDex odds format hints."""
        return {
            "decimal": r'^\d+\.?\d*$',  # Variable decimal places
            "fractional": r'^\d+/\d+$',
            "american": r'^[+-]?\d+$'
        }
    
    def get_interface_keywords(self) -> Dict[str, List[str]]:
        """Get BetDex-specific interface keywords."""
        return {
            "home_win": ["home", "h", "team 1", "1", "home team"],
            "away_win": ["away", "a", "team 2", "2", "away team"],
            "draw": ["draw", "tie", "x", "d"],
            "over": ["over", "o", "o/u"],
            "under": ["under", "u", "o/u"],
            "both_teams_score": ["both teams", "btts", "gg", "both to score"]
        }


class AverTemplate(BookmakerTemplate):
    """
    Aver interface template.
    
    Aver represents regional bookmaker interfaces with potentially
    diverse layouts, localized content, and varied betting styles.
    """
    
    def __init__(self):
        super().__init__("aver_regional", "1.0.0")
        self.bookmaker_name = "Aver"
    
    def get_extraction_prompt(self, sport: Sport, market_type: str) -> str:
        """Get Aver-specific extraction prompt."""
        return f"""
        Extract betting odds from the Aver interface for {sport.value} - {market_type}.
        
        Aver Interface Notes:
        - Regional bookmaker with potential localization
        - May include diverse betting styles and markets
        - Interface design may vary by region/sport
        - Could have mixed decimal/fractional odds
        
        Focus on:
        1. Core betting odds regardless of layout style
        2. Standard betting markets and terminology
        3. Main event odds (avoid special/exotic markets)
        
        Key outcome mappings:
        - Use both local and international terminology
        - Standard sports outcomes (Win/Loss/Draw, Over/Under)
        - Account for potential localization
        
        Be flexible with:
        - Layout variations
        - Mixed odds formats
        - Regional market variations
        - Localized team/player names
        """
    
    def get_parsing_rules(self) -> Dict[str, Any]:
        """Get Aver-specific parsing rules."""
        return {
            "odds_format": ["decimal", "fractional"],
            "odds_decimal_places": [1, 2, 3],
            "layout_style": "flexible_regional",
            "outcome_detection": {
                "primary_source": "outcomes",
                "mapping_strategy": "adaptive",
                "localization_support": True
            },
            "confidence_indicators": {
                "high_confidence": ["main odds section", "standard markets", "clear display"],
                "medium_confidence": ["secondary markets", "modified layout"],
                "low_confidence": ["exotic markets", "poor display quality"]
            },
            "quality_indicators": {
                "regional_variations": True,
                "localization": True,
                "mixed_formats": True
            },
            "localization_awareness": True,
            "rate_limit_considerations": False,
            "exchange_specific": False
        }
    
    def get_odds_format_hints(self) -> Dict[str, str]:
        """Get Aver odds format hints."""
        return {
            "decimal": r'^\d+\.?\d*$',
            "fractional": r'^\d+/\d+$',
            "american": r'^[+-]?\d+$',
            "hong_kong": r'^\d+\.?\d*$'
        }
    
    def get_interface_keywords(self) -> Dict[str, List[str]]:
        """Get Aver-specific interface keywords with localization support."""
        return {
            "home_win": ["home", "local", "team 1", "1", "home team", "vie"],
            "away_win": ["away", "visitor", "team 2", "2", "away team", "de"],
            "draw": ["draw", "tie", "x", "empate", "nul"],
            "over": ["over", "mas", "over x", "superior"],
            "under": ["under", "menos", "under x", "inferior"],
            "both_teams_score": ["both teams", "ambos anotan", "gg", "both score"]
        }


# ============================================================================
# TEMPLATE MANAGER
# ============================================================================

class TemplateManager:
    """
    Manages bookmaker templates for VLM odds extraction.
    
    Provides template discovery, versioning, and management capabilities.
    """
    
    def __init__(self):
        """Initialize the template manager."""
        self.logger = logging.getLogger(__name__)
        
        # Load all available templates
        self.templates: Dict[str, BookmakerTemplate] = {}
        self.template_metadata: Dict[str, TemplateMetadata] = {}
        
        # Initialize built-in templates
        self._initialize_builtin_templates()
    
    def _initialize_builtin_templates(self) -> None:
        """Initialize all built-in bookmaker templates."""
        builtin_templates = [
            BetfairTemplate(),
            PinnacleTemplate(),
            BetDexTemplate(),
            AverTemplate()
        ]
        
        for template in builtin_templates:
            self.register_template(template)
        
        self.logger.info("Initialized %d built-in templates", len(builtin_templates))
    
    def register_template(self, template: BookmakerTemplate) -> None:
        """
        Register a new bookmaker template.
        
        Args:
            template: Template to register
        """
        template_id = f"{template.name}_v{template.version}"
        
        # Create metadata
        metadata = TemplateMetadata(
            name=template.name,
            version=template.version,
            bookmaker=template.bookmaker_name if hasattr(template, 'bookmaker_name') else template.name,
            supported_sports=template.get_supported_sports(),
            supported_markets=self._get_default_markets_for_sport(template.get_supported_sports()[0] if template.get_supported_sports() else Sport.FOOTBALL)
        )
        
        self.templates[template_id] = template
        self.template_metadata[template_id] = metadata
        
        self.logger.info("Registered template: %s v%s", template.name, template.version)
    
    def get_template(
        self, 
        bookmaker: str, 
        sport: Sport, 
        version: Optional[str] = None
    ) -> Optional[BookmakerTemplate]:
        """
        Get template for specific bookmaker and sport.
        
        Args:
            bookmaker: Bookmaker name
            sport: Sport type
            version: Optional specific version
            
        Returns:
            Template or None if not found
        """
        # Try exact match first
        for template_id, template in self.templates.items():
            if self._template_matches(template, bookmaker, sport, version):
                self.logger.debug("Found template: %s", template_id)
                return template
        
        # Try fallback matching
        return self._find_fallback_template(bookmaker, sport)
    
    def _template_matches(
        self, 
        template: BookmakerTemplate, 
        bookmaker: str, 
        sport: Sport, 
        version: Optional[str]
    ) -> bool:
        """Check if template matches the criteria."""
        template_bookmaker = getattr(template, 'bookmaker_name', template.name)
        
        if template_bookmaker.lower() != bookmaker.lower():
            return False
        
        if version and template.version != version:
            return False
        
        if sport not in template.get_supported_sports():
            return False
        
        return True
    
    def _find_fallback_template(
        self, 
        bookmaker: str, 
        sport: Sport
    ) -> Optional[BookmakerTemplate]:
        """Find a fallback template when exact match isn't available."""
        bookmaker_lower = bookmaker.lower()
        
        # Look for templates that support the sport
        compatible_templates = []
        for template in self.templates.values():
            if sport in template.get_supported_sports():
                template_bookmaker = getattr(template, 'bookmaker_name', template.name)
                if (template_bookmaker.lower() == bookmaker_lower or
                    self._similar_bookmaker_names(template_bookmaker, bookmaker)):
                    compatible_templates.append(template)
        
        if compatible_templates:
            # Return the most recent version
            return max(compatible_templates, key=lambda t: t.version)
        
        # Final fallback: use Pinnacle as it's often well-structured
        for template in self.templates.values():
            if isinstance(template, PinnacleTemplate):
                self.logger.warning("Using fallback template for %s", bookmaker)
                return template
        
        return None
    
    def _similar_bookmaker_names(self, template_name: str, target_name: str) -> bool:
        """Check if bookmaker names are similar (for fallback matching)."""
        template_lower = template_name.lower().replace(' ', '').replace('-', '')
        target_lower = target_name.lower().replace(' ', '').replace('-', '')
        
        # Check for common abbreviations or variations
        variations = {
            'pinnacle': ['pinnacle', 'pin', 'pinn'],
            'betfair': ['betfair', 'bf', 'bet_fair'],
            'draftkings': ['draftkings', 'dk', 'draft_kings'],
            'williamhill': ['williamhill', 'wh', 'william_hill']
        }
        
        for standard, alternatives in variations.items():
            if (standard in template_lower and any(alt in target_lower for alt in alternatives)) or \
               (standard in target_lower and any(alt in template_lower for alt in alternatives)):
                return True
        
        return False
    
    def _get_default_markets_for_sport(self, sport: Sport) -> List[str]:
        """Get default supported markets for a sport."""
        market_mapping = {
            Sport.FOOTBALL: ["match_winner", "over_under", "both_teams_score", "handicap"],
            Sport.BASKETBALL: ["match_winner", "over_under", "handicap"],
            Sport.TENNIS: ["match_winner", "over_under", "handicap"],
            Sport.BASEBALL: ["match_winner", "over_under"],
            Sport.HOCKEY: ["match_winner", "over_under", "handicap"],
            Sport.ESPORTS: ["match_winner", "over_under"]
        }
        
        return market_mapping.get(sport, ["match_winner", "over_under"])
    
    def list_templates(self) -> List[TemplateMetadata]:
        """List all registered templates."""
        return list(self.template_metadata.values())
    
    def get_template_by_name(self, name: str) -> Optional[BookmakerTemplate]:
        """Get template by name (case-insensitive)."""
        name_lower = name.lower()
        
        for template in self.templates.values():
            template_name = getattr(template, 'bookmaker_name', template.name).lower()
            if template_name == name_lower or template.name.lower() == name_lower:
                return template
        
        return None
    
    def validate_template_compatibility(
        self, 
        bookmaker: str, 
        sport: Sport, 
        market_type: str
    ) -> Dict[str, Any]:
        """
        Validate template compatibility for extraction.
        
        Args:
            bookmaker: Bookmaker name
            sport: Sport type
            market_type: Market type
            
        Returns:
            Compatibility validation result
        """
        template = self.get_template(bookmaker, sport)
        
        if not template:
            return {
                "compatible": False,
                "warnings": ["No suitable template found"],
                "recommendations": ["Consider using a generic template", "Check template registration"]
            }
        
        is_valid, warnings = template.validate_extraction_context(sport, market_type)
        
        recommendations = []
        if warnings:
            recommendations.extend([
                "Consider using a different sport template",
                "Review template configuration",
                "Adjust parsing rules if necessary"
            ])
        
        return {
            "compatible": is_valid,
            "template_used": template.name,
            "template_version": template.version,
            "warnings": warnings,
            "recommendations": recommendations,
            "supported_sports": [s.value for s in template.get_supported_sports()]
        }
    
    def get_best_template_for_context(
        self, 
        bookmaker: str, 
        sport: Sport, 
        market_type: str
    ) -> Optional[BookmakerTemplate]:
        """
        Get the best template for a given context.
        
        Args:
            bookmaker: Bookmaker name
            sport: Sport type
            market_type: Market type
            
        Returns:
            Best matching template
        """
        template = self.get_template(bookmaker, sport)
        
        if template:
            is_valid, warnings = template.validate_extraction_context(sport, market_type)
            
            if not is_valid:
                self.logger.warning("Template validation failed for %s: %s", bookmaker, warnings)
                # Still return the template but log the issues
        
        return template or self._find_fallback_template(bookmaker, sport)