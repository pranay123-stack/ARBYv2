"""
Multi-Dimensional Filtering Engine

Advanced filtering system for arbitrage opportunities with configurable filters
for profit margins, bookmaker combinations, market types, sports, and risk levels.
Supports complex filter combinations and real-time filter updates.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Union, Any, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
import re

from ..storage.models import ArbitrageOpportunity, ArbitrageLeg, RiskTier, Sport


logger = logging.getLogger(__name__)


class FilterOperator(str, Enum):
    """Available filter operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"
    BETWEEN = "between"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


@dataclass
class FilterRule:
    """Individual filter rule."""
    field: str
    operator: FilterOperator
    value: Any
    negate: bool = False
    case_sensitive: bool = True
    weight: float = 1.0


@dataclass
class FilterGroup:
    """Group of related filter rules."""
    rules: List[FilterRule]
    logic_operator: str = "AND"  # AND, OR
    weight: float = 1.0
    
    def validate(self) -> bool:
        """Validate filter group configuration."""
        if not self.rules:
            return False
        if self.logic_operator not in ["AND", "OR"]:
            return False
        return True


class BaseFilter(ABC):
    """Abstract base class for filters."""
    
    @abstractmethod
    def apply(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """Apply filter to opportunities list."""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of filter."""
        pass


class ProfitMarginFilter(BaseFilter):
    """Filter opportunities by profit margin."""
    
    def __init__(self, 
                 min_profit: Optional[Decimal] = None,
                 max_profit: Optional[Decimal] = None,
                 operator: FilterOperator = FilterOperator.GREATER_THAN_OR_EQUAL):
        self.min_profit = min_profit
        self.max_profit = max_profit
        self.operator = operator
    
    def apply(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        filtered = []
        for opp in opportunities:
            if self._matches_profit_margin(opp.profit_margin):
                filtered.append(opp)
        return filtered
    
    def _matches_profit_margin(self, profit_margin: Decimal) -> bool:
        """Check if profit margin matches filter criteria."""
        if self.operator == FilterOperator.BETWEEN:
            return (self.min_profit or Decimal('0')) <= profit_margin <= (self.max_profit or Decimal('inf'))
        elif self.operator == FilterOperator.GREATER_THAN:
            return profit_margin > (self.min_profit or Decimal('0'))
        elif self.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return profit_margin >= (self.min_profit or Decimal('0'))
        elif self.operator == FilterOperator.LESS_THAN:
            return profit_margin < (self.max_profit or Decimal('inf'))
        elif self.operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return profit_margin <= (self.max_profit or Decimal('inf'))
        else:
            return True
    
    def get_description(self) -> str:
        desc = f"Profit margin filter: {self.operator.value}"
        if self.min_profit is not None:
            desc += f" min: {self.min_profit:.2%}"
        if self.max_profit is not None:
            desc += f" max: {self.max_profit:.2%}"
        return desc


class RiskTierFilter(BaseFilter):
    """Filter opportunities by risk tier."""
    
    def __init__(self, 
                 allowed_tiers: Optional[List[RiskTier]] = None,
                 excluded_tiers: Optional[List[RiskTier]] = None,
                 operator: FilterOperator = FilterOperator.IN):
        self.allowed_tiers = set(allowed_tiers or [])
        self.excluded_tiers = set(excluded_tiers or [])
        self.operator = operator
    
    def apply(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        filtered = []
        for opp in opportunities:
            if self._matches_risk_tier(opp.risk_tier):
                filtered.append(opp)
        return filtered
    
    def _matches_risk_tier(self, risk_tier: RiskTier) -> bool:
        """Check if risk tier matches filter criteria."""
        if self.allowed_tiers and self.operator == FilterOperator.IN:
            return risk_tier in self.allowed_tiers
        elif self.excluded_tiers and self.operator == FilterOperator.NOT_IN:
            return risk_tier not in self.excluded_tiers
        return True
    
    def get_description(self) -> str:
        if self.allowed_tiers:
            tiers = [t.value for t in self.allowed_tiers]
            return f"Risk tier filter: allowed tiers {tiers}"
        elif self.excluded_tiers:
            tiers = [t.value for t in self.excluded_tiers]
            return f"Risk tier filter: excluded tiers {tiers}"
        return "Risk tier filter: no restrictions"


class SportFilter(BaseFilter):
    """Filter opportunities by sport."""
    
    def __init__(self, 
                 allowed_sports: Optional[List[Sport]] = None,
                 excluded_sports: Optional[List[Sport]] = None,
                 operator: FilterOperator = FilterOperator.IN):
        self.allowed_sports = set(allowed_sports or [])
        self.excluded_sports = set(excluded_sports or [])
        self.operator = operator
    
    def apply(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        filtered = []
        for opp in opportunities:
            if self._matches_sport(opp.sport):
                filtered.append(opp)
        return filtered
    
    def _matches_sport(self, sport: Sport) -> bool:
        """Check if sport matches filter criteria."""
        if self.allowed_sports and self.operator == FilterOperator.IN:
            return sport in self.allowed_sports
        elif self.excluded_sports and self.operator == FilterOperator.NOT_IN:
            return sport not in self.excluded_sports
        return True
    
    def get_description(self) -> str:
        if self.allowed_sports:
            sports = [s.value for s in self.allowed_sports]
            return f"Sport filter: allowed sports {sports}"
        elif self.excluded_sports:
            sports = [s.value for s in self.excluded_sports]
            return f"Sport filter: excluded sports {sports}"
        return "Sport filter: no restrictions"


class BookmakerFilter(BaseFilter):
    """Filter opportunities by bookmaker combinations."""
    
    def __init__(self, 
                 required_bookmakers: Optional[List[str]] = None,
                 excluded_bookmakers: Optional[List[str]] = None,
                 min_bookmakers: Optional[int] = None,
                 max_bookmakers: Optional[int] = None,
                 must_include_all: bool = False):
        self.required_bookmakers = set(required_bookmakers or [])
        self.excluded_bookmakers = set(excluded_bookmakers or [])
        self.min_bookmakers = min_bookmakers
        self.max_bookmakers = max_bookmakers
        self.must_include_all = must_include_all
    
    def apply(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        filtered = []
        for opp in opportunities:
            if self._matches_bookmaker_criteria(opp):
                filtered.append(opp)
        return filtered
    
    def _matches_bookmaker_criteria(self, opportunity: ArbitrageOpportunity) -> bool:
        """Check if opportunity matches bookmaker criteria."""
        bookmakers = {leg.bookmaker for leg in opportunity.legs}
        
        # Check excluded bookmakers
        if self.excluded_bookmakers.intersection(bookmakers):
            return False
        
        # Check required bookmakers
        if self.required_bookmakers:
            if self.must_include_all:
                if not self.required_bookmakers.issubset(bookmakers):
                    return False
            else:
                if not self.required_bookmakers.intersection(bookmakers):
                    return False
        
        # Check bookmaker count constraints
        bookmaker_count = len(bookmakers)
        if self.min_bookmakers is not None and bookmaker_count < self.min_bookmakers:
            return False
        if self.max_bookmakers is not None and bookmaker_count > self.max_bookmakers:
            return False
        
        return True
    
    def get_description(self) -> str:
        desc = "Bookmaker filter: "
        if self.required_bookmakers:
            desc += f"required: {list(self.required_bookmakers)}, "
        if self.excluded_bookmakers:
            desc += f"excluded: {list(self.excluded_bookmakers)}, "
        if self.min_bookmakers is not None:
            desc += f"min bookmakers: {self.min_bookmakers}, "
        if self.max_bookmakers is not None:
            desc += f"max bookmakers: {self.max_bookmakers}, "
        return desc.rstrip(", ")


class MarketTypeFilter(BaseFilter):
    """Filter opportunities by market type."""
    
    def __init__(self, 
                 allowed_markets: Optional[List[str]] = None,
                 excluded_markets: Optional[List[str]] = None,
                 pattern: Optional[str] = None,
                 case_sensitive: bool = False):
        self.allowed_markets = set(allowed_markets or [])
        self.excluded_markets = set(excluded_markets or [])
        self.pattern = pattern
        self.case_sensitive = case_sensitive
    
    def apply(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        filtered = []
        for opp in opportunities:
            if self._matches_market_type(opp.market_type):
                filtered.append(opp)
        return filtered
    
    def _matches_market_type(self, market_type: str) -> bool:
        """Check if market type matches filter criteria."""
        # Direct match against allowed/excluded lists
        if self.allowed_markets and market_type not in self.allowed_markets:
            return False
        if self.excluded_markets and market_type in self.excluded_markets:
            return False
        
        # Pattern matching
        if self.pattern:
            if self.case_sensitive:
                return bool(re.search(self.pattern, market_type))
            else:
                return bool(re.search(self.pattern, market_type, re.IGNORECASE))
        
        return True
    
    def get_description(self) -> str:
        desc = "Market type filter: "
        if self.allowed_markets:
            desc += f"allowed: {list(self.allowed_markets)}, "
        if self.excluded_markets:
            desc += f"excluded: {list(self.excluded_markets)}, "
        if self.pattern:
            desc += f"pattern: {self.pattern}, "
        return desc.rstrip(", ")


class StakeAmountFilter(BaseFilter):
    """Filter opportunities by stake amount."""
    
    def __init__(self, 
                 min_stake: Optional[Decimal] = None,
                 max_stake: Optional[Decimal] = None,
                 operator: FilterOperator = FilterOperator.BETWEEN):
        self.min_stake = min_stake
        self.max_stake = max_stake
        self.operator = operator
    
    def apply(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        filtered = []
        for opp in opportunities:
            if self._matches_stake_amount(opp.total_stake):
                filtered.append(opp)
        return filtered
    
    def _matches_stake_amount(self, stake: Decimal) -> bool:
        """Check if stake amount matches filter criteria."""
        if self.operator == FilterOperator.BETWEEN:
            return (self.min_stake or Decimal('0')) <= stake <= (self.max_stake or Decimal('inf'))
        elif self.operator == FilterOperator.GREATER_THAN:
            return stake > (self.min_stake or Decimal('0'))
        elif self.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return stake >= (self.min_stake or Decimal('0'))
        elif self.operator == FilterOperator.LESS_THAN:
            return stake < (self.max_stake or Decimal('inf'))
        elif self.operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return stake <= (self.max_stake or Decimal('inf'))
        return True
    
    def get_description(self) -> str:
        desc = f"Stake amount filter: {self.operator.value}"
        if self.min_stake is not None:
            desc += f" min: ${self.min_stake}"
        if self.max_stake is not None:
            desc += f" max: ${self.max_stake}"
        return desc


class TimeFilter(BaseFilter):
    """Filter opportunities by time-related criteria."""
    
    def __init__(self, 
                 max_age_minutes: Optional[int] = None,
                 min_event_urgency_minutes: Optional[int] = None,
                 max_event_urgency_minutes: Optional[int] = None,
                 must_have_expiry: bool = False):
        self.max_age_minutes = max_age_minutes
        self.min_event_urgency_minutes = min_event_urgency_minutes
        self.max_event_urgency_minutes = max_event_urgency_minutes
        self.must_have_expiry = must_have_expiry
    
    def apply(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        filtered = []
        for opp in opportunities:
            if self._matches_time_criteria(opp):
                filtered.append(opp)
        return filtered
    
    def _matches_time_criteria(self, opportunity: ArbitrageOpportunity) -> bool:
        """Check if opportunity matches time criteria."""
        now = datetime.utcnow()
        
        # Check discovery age
        if self.max_age_minutes is not None:
            age_minutes = (now - opportunity.discovered_at).total_seconds() / 60
            if age_minutes > self.max_age_minutes:
                return False
        
        # Check event urgency
        if self.min_event_urgency_minutes is not None or self.max_event_urgency_minutes is not None:
            event_minutes = (opportunity.event_date - now).total_seconds() / 60
            
            if self.min_event_urgency_minutes is not None:
                if event_minutes < self.min_event_urgency_minutes:
                    return False
            
            if self.max_event_urgency_minutes is not None:
                if event_minutes > self.max_event_urgency_minutes:
                    return False
        
        # Check expiry requirement
        if self.must_have_expiry and opportunity.expires_at is None:
            return False
        
        return True
    
    def get_description(self) -> str:
        desc = "Time filter: "
        if self.max_age_minutes is not None:
            desc += f"max age: {self.max_age_minutes}min, "
        if self.min_event_urgency_minutes is not None:
            desc += f"min urgency: {self.min_event_urgency_minutes}min, "
        if self.max_event_urgency_minutes is not None:
            desc += f"max urgency: {self.max_event_urgency_minutes}min, "
        if self.must_have_expiry:
            desc += "must have expiry, "
        return desc.rstrip(", ")


class LiquidityFilter(BaseFilter):
    """Filter opportunities by liquidity criteria."""
    
    def __init__(self, 
                 must_be_checked: bool = False,
                 max_odds_age_minutes: Optional[int] = None,
                 liquidity_ratio_threshold: Optional[float] = None):
        self.must_be_checked = must_be_checked
        self.max_odds_age_minutes = max_odds_age_minutes
        self.liquidity_ratio_threshold = liquidity_ratio_threshold
    
    def apply(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        filtered = []
        for opp in opportunities:
            if self._matches_liquidity_criteria(opp):
                filtered.append(opp)
        return filtered
    
    def _matches_liquidity_criteria(self, opportunity: ArbitrageOpportunity) -> bool:
        """Check if opportunity matches liquidity criteria."""
        # Check liquidity verification
        if self.must_be_checked and not opportunity.liquidity_checked:
            return False
        
        # Check odds freshness
        if self.max_odds_age_minutes is not None:
            age_minutes = (datetime.utcnow() - opportunity.odds_freshness).total_seconds() / 60
            if age_minutes > self.max_odds_age_minutes:
                return False
        
        # Check liquidity ratio (placeholder implementation)
        if self.liquidity_ratio_threshold is not None:
            total_stake = float(opportunity.total_stake)
            # Assume liquidity is 10x stake for now
            liquidity_ratio = (total_stake * 10) / total_stake
            if liquidity_ratio < self.liquidity_ratio_threshold:
                return False
        
        return True
    
    def get_description(self) -> str:
        desc = "Liquidity filter: "
        if self.must_be_checked:
            desc += "must be checked, "
        if self.max_odds_age_minutes is not None:
            desc += f"max odds age: {self.max_odds_age_minutes}min, "
        if self.liquidity_ratio_threshold is not None:
            desc += f"min liquidity ratio: {self.liquidity_ratio_threshold}, "
        return desc.rstrip(", ")


class CustomFilter(BaseFilter):
    """Custom filter with user-defined logic."""
    
    def __init__(self, 
                 filter_func: Callable[[ArbitrageOpportunity], bool],
                 description: str):
        self.filter_func = filter_func
        self.description = description
    
    def apply(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        return [opp for opp in opportunities if self.filter_func(opp)]
    
    def get_description(self) -> str:
        return f"Custom filter: {self.description}"


class FilteringEngine:
    """
    Multi-dimensional filtering engine for arbitrage opportunities.
    """
    
    def __init__(self):
        """Initialize the filtering engine."""
        self.filters: List[BaseFilter] = []
        self.filter_groups: List[FilterGroup] = []
        self.active_filters: Set[str] = set()
        
        # Performance tracking
        self.filter_stats = {
            'total_filtered': 0,
            'total_processed': 0,
            'average_filter_time_ms': 0.0,
            'filter_counts': {}
        }
    
    def add_filter(self, filter_obj: BaseFilter, filter_id: Optional[str] = None) -> str:
        """
        Add a filter to the engine.
        
        Args:
            filter_obj: Filter object to add
            filter_id: Optional custom ID for the filter
            
        Returns:
            Filter ID
        """
        filter_id = filter_id or f"filter_{len(self.filters)}"
        
        self.filters.append(filter_obj)
        self.active_filters.add(filter_id)
        
        logger.info(f"Added filter {filter_id}: {filter_obj.get_description()}")
        return filter_id
    
    def remove_filter(self, filter_id: str) -> bool:
        """
        Remove a filter by ID.
        
        Args:
            filter_id: ID of filter to remove
            
        Returns:
            True if filter was removed, False if not found
        """
        # Find filter index (filters are stored in order)
        for i, filter_obj in enumerate(self.filters):
            if f"filter_{i}" == filter_id:
                del self.filters[i]
                self.active_filters.discard(filter_id)
                logger.info(f"Removed filter {filter_id}")
                return True
        return False
    
    def clear_filters(self):
        """Clear all filters."""
        self.filters.clear()
        self.active_filters.clear()
        logger.info("Cleared all filters")
    
    def add_filter_group(self, group: FilterGroup) -> str:
        """
        Add a group of related filter rules.
        
        Args:
            group: Filter group to add
            
        Returns:
            Group ID
        """
        group_id = f"group_{len(self.filter_groups)}"
        
        if not group.validate():
            raise ValueError("Invalid filter group configuration")
        
        self.filter_groups.append(group)
        logger.info(f"Added filter group {group_id} with {len(group.rules)} rules")
        return group_id
    
    def filter_opportunities(self, 
                           opportunities: List[ArbitrageOpportunity],
                           use_groups: bool = False,
                           group_logic: str = "AND") -> List[ArbitrageOpportunity]:
        """
        Filter opportunities using all configured filters.
        
        Args:
            opportunities: List of opportunities to filter
            use_groups: Whether to use filter groups instead of individual filters
            group_logic: Logic for combining groups (AND, OR)
            
        Returns:
            Filtered list of opportunities
        """
        start_time = datetime.utcnow()
        
        if use_groups and self.filter_groups:
            filtered = self._apply_filter_groups(opportunities, group_logic)
        else:
            filtered = self._apply_individual_filters(opportunities)
        
        # Update statistics
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        self._update_filter_stats(len(opportunities), len(filtered), processing_time)
        
        logger.info(f"Filtered {len(opportunities)} opportunities to {len(filtered)} in {processing_time:.2f}ms")
        return filtered
    
    def _apply_individual_filters(self, opportunities: List[ArbitrageOpportunity]) -> List[ArbitrageOpportunity]:
        """Apply individual filters in sequence."""
        filtered = opportunities.copy()
        
        for filter_obj in self.filters:
            try:
                filtered = filter_obj.apply(filtered)
                # Track individual filter performance
                filter_name = filter_obj.__class__.__name__
                self.filter_stats['filter_counts'][filter_name] = \
                    self.filter_stats['filter_counts'].get(filter_name, 0) + 1
            except Exception as e:
                logger.error(f"Error applying filter {filter_obj.__class__.__name__}: {e}")
                continue
        
        return filtered
    
    def _apply_filter_groups(self, opportunities: List[ArbitrageOpportunity], group_logic: str) -> List[ArbitrageOpportunity]:
        """Apply filter groups with complex logic."""
        results = []
        
        for opportunity in opportunities:
            group_scores = []
            
            for group in self.filter_groups:
                score = self._evaluate_filter_group(opportunity, group)
                group_scores.append(score)
            
            # Combine group scores based on logic
            if group_logic.upper() == "AND":
                passes = all(group_scores)
            else:  # OR
                passes = any(group_scores)
            
            if passes:
                results.append(opportunity)
        
        return results
    
    def _evaluate_filter_group(self, opportunity: ArbitrageOpportunity, group: FilterGroup) -> bool:
        """Evaluate a single filter group against an opportunity."""
        rule_results = []
        
        for rule in group.rules:
            result = self._evaluate_rule(opportunity, rule)
            rule_results.append(result)
        
        # Combine rule results
        if group.logic_operator.upper() == "AND":
            return all(rule_results)
        else:  # OR
            return any(rule_results)
    
    def _evaluate_rule(self, opportunity: ArbitrageOpportunity, rule: FilterRule) -> bool:
        """Evaluate a single filter rule against an opportunity."""
        try:
            # Get field value from opportunity
            field_value = self._get_field_value(opportunity, rule.field)
            if field_value is None:
                return False
            
            # Apply operator
            result = self._apply_operator(field_value, rule.value, rule.operator, rule.case_sensitive)
            
            # Apply negation if needed
            if rule.negate:
                result = not result
            
            return result
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.field} {rule.operator}: {e}")
            return False
    
    def _get_field_value(self, opportunity: ArbitrageOpportunity, field: str) -> Any:
        """Get field value from opportunity using dot notation."""
        fields = field.split('.')
        value = opportunity
        
        for field_name in fields:
            if hasattr(value, field_name):
                value = getattr(value, field_name)
            elif isinstance(value, dict) and field_name in value:
                value = value[field_name]
            else:
                return None
        
        return value
    
    def _apply_operator(self, field_value: Any, rule_value: Any, operator: FilterOperator, case_sensitive: bool) -> bool:
        """Apply operator to field value."""
        # Handle string comparison with case sensitivity
        if isinstance(field_value, str) and isinstance(rule_value, str):
            if not case_sensitive:
                field_value = field_value.lower()
                rule_value = rule_value.lower()
        
        # Apply operator
        if operator == FilterOperator.EQUALS:
            return field_value == rule_value
        elif operator == FilterOperator.NOT_EQUALS:
            return field_value != rule_value
        elif operator == FilterOperator.GREATER_THAN:
            return field_value > rule_value
        elif operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return field_value >= rule_value
        elif operator == FilterOperator.LESS_THAN:
            return field_value < rule_value
        elif operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return field_value <= rule_value
        elif operator == FilterOperator.IN:
            return field_value in rule_value
        elif operator == FilterOperator.NOT_IN:
            return field_value not in rule_value
        elif operator == FilterOperator.CONTAINS:
            return rule_value in field_value
        elif operator == FilterOperator.NOT_CONTAINS:
            return rule_value not in field_value
        elif operator == FilterOperator.REGEX:
            pattern = re.compile(rule_value, 0 if case_sensitive else re.IGNORECASE)
            return bool(pattern.search(str(field_value)))
        elif operator == FilterOperator.BETWEEN:
            return rule_value[0] <= field_value <= rule_value[1]
        elif operator == FilterOperator.STARTS_WITH:
            return str(field_value).startswith(str(rule_value))
        elif operator == FilterOperator.ENDS_WITH:
            return str(field_value).endswith(str(rule_value))
        
        return False
    
    def _update_filter_stats(self, total_processed: int, total_filtered: int, processing_time_ms: float):
        """Update filtering performance statistics."""
        self.filter_stats['total_processed'] += total_processed
        self.filter_stats['total_filtered'] += total_filtered
        
        # Update average processing time
        total_ops = self.filter_stats['total_processed']
        current_avg = self.filter_stats['average_filter_time_ms']
        new_avg = ((current_avg * (total_ops - total_processed)) + processing_time_ms) / total_ops
        self.filter_stats['average_filter_time_ms'] = new_avg
    
    def get_filter_info(self) -> Dict[str, Any]:
        """Get information about current filters."""
        return {
            'individual_filters': [
                {
                    'id': f"filter_{i}",
                    'type': filter_obj.__class__.__name__,
                    'description': filter_obj.get_description(),
                    'active': f"filter_{i}" in self.active_filters
                }
                for i, filter_obj in enumerate(self.filters)
            ],
            'filter_groups': [
                {
                    'id': f"group_{i}",
                    'rules_count': len(group.rules),
                    'logic_operator': group.logic_operator,
                    'weight': group.weight
                }
                for i, group in enumerate(self.filter_groups)
            ],
            'performance_stats': self.filter_stats.copy(),
            'active_filter_count': len(self.active_filters),
            'total_filter_groups': len(self.filter_groups)
        }
    
    def reset_stats(self):
        """Reset performance statistics."""
        self.filter_stats = {
            'total_filtered': 0,
            'total_processed': 0,
            'average_filter_time_ms': 0.0,
            'filter_counts': {}
        }
        logger.info("Reset filter statistics")


# Convenience functions for common filter combinations
def create_profit_filter(min_margin: Decimal = Decimal('0.01'), max_margin: Optional[Decimal] = None) -> ProfitMarginFilter:
    """Create a profit margin filter."""
    return ProfitMarginFilter(min_profit=min_margin, max_profit=max_margin)


def create_risk_filter(allowed_tiers: List[RiskTier]) -> RiskTierFilter:
    """Create a risk tier filter."""
    return RiskTierFilter(allowed_tiers=allowed_tiers)


def create_sport_filter(allowed_sports: List[Sport]) -> SportFilter:
    """Create a sport filter."""
    return SportFilter(allowed_sports=allowed_sports)


def create_bookmaker_filter(required_bookmakers: List[str], excluded_bookmakers: Optional[List[str]] = None) -> BookmakerFilter:
    """Create a bookmaker filter."""
    return BookmakerFilter(required_bookmakers=required_bookmakers, excluded_bookmakers=excluded_bookmakers)


def create_time_filter(max_age_minutes: int = 30) -> TimeFilter:
    """Create a time-based filter."""
    return TimeFilter(max_age_minutes=max_age_minutes)


def create_liquidity_filter(must_be_checked: bool = True, max_odds_age: int = 15) -> LiquidityFilter:
    """Create a liquidity filter."""
    return LiquidityFilter(must_be_checked=must_be_checked, max_odds_age_minutes=max_odds_age)