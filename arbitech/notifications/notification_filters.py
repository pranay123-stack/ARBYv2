"""
Advanced Notification Filtering and Preferences System

This module provides intelligent notification filtering, user preferences management,
and smart notification delivery for the ARBitech arbitrage trading platform.

Features:
- Multi-criteria filtering (profit thresholds, risk tiers, sports, bookmakers, times)
- User-defined notification preferences with granular controls
- Machine learning-based relevance scoring
- Notification deduplication and grouping
- Quiet hours and time-based filtering
- Custom alert rules with complex logic
- Notification history and analytics
- Notification importance levels and escalation rules
- Integration with Supabase user profiles and preferences
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import (
    List, Dict, Optional, Any, Union, Set, Callable, Tuple, Literal,
    Protocol
)
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum
import pickle
import gzip
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from storage.models import (
    Notification, NotificationType, NotificationPriority, NotificationChannel,
    ArbitrageOpportunity, RiskTier, Sport, MessageData
)
from storage.supabase_layer import SupabaseDataLayer
from detection.mathematical_models import ArbitrageOpportunity as MathOpportunity


logger = logging.getLogger(__name__)


class FilterOperator(Enum):
    """Supported filter operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_EQUAL = "greater_equal"
    LESS_THAN = "less_than"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    REGEX = "regex"


@dataclass
class FilterCondition:
    """Represents a single filter condition."""
    field: str
    operator: FilterOperator
    value: Any
    description: Optional[str] = None


@dataclass
class NotificationFilter:
    """Composite notification filter with multiple conditions."""
    name: str
    conditions: List[FilterCondition] = field(default_factory=list)
    logic_operator: Literal["AND", "OR"] = "AND"
    enabled: bool = True
    priority_boost: float = 0.0
    description: Optional[str] = None


class RelevanceScorer(ABC):
    """Abstract base class for relevance scoring algorithms."""
    
    @abstractmethod
    def calculate_score(self, notification: Notification, user_preferences: Dict[str, Any]) -> float:
        """Calculate relevance score for a notification."""
        pass


class TfidfRelevanceScorer(RelevanceScorer):
    """TF-IDF based relevance scorer for notification content."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.user_profiles = {}
        self._load_or_initialize()
    
    def _load_or_initialize(self):
        """Load existing model or initialize new one."""
        if self.model_path and Path(self.model_path).exists():
            try:
                with gzip.open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.vectorizer = data['vectorizer']
                    self.user_profiles = data['user_profiles']
                logger.info(f"Loaded relevance model from {self.model_path}")
            except Exception as e:
                logger.warning(f"Could not load relevance model: {e}")
    
    def save_model(self):
        """Save the trained model."""
        if self.model_path:
            try:
                data = {
                    'vectorizer': self.vectorizer,
                    'user_profiles': self.user_profiles
                }
                with gzip.open(self.model_path, 'wb') as f:
                    pickle.dump(data, f)
                logger.info(f"Saved relevance model to {self.model_path}")
            except Exception as e:
                logger.error(f"Failed to save relevance model: {e}")
    
    def calculate_score(self, notification: Notification, user_preferences: Dict[str, Any]) -> float:
        """Calculate relevance score using TF-IDF similarity."""
        try:
            # Extract text content
            content = f"{notification.message.title} {notification.message.body}"
            user_keywords = user_preferences.get('keywords', [])
            
            if not user_keywords:
                return 0.5  # Default neutral score
            
            # Create user profile vector
            user_text = ' '.join(user_keywords)
            user_vector = self.vectorizer.transform([user_text])
            content_vector = self.vectorizer.transform([content])
            
            # Calculate similarity
            similarity = cosine_similarity(user_vector, content_vector)[0][0]
            
            # Apply preference weights
            priority_weight = {
                NotificationPriority.LOW: 0.8,
                NotificationPriority.MEDIUM: 1.0,
                NotificationPriority.HIGH: 1.2,
                NotificationPriority.CRITICAL: 1.5
            }.get(notification.priority, 1.0)
            
            final_score = similarity * priority_weight
            return min(1.0, max(0.0, final_score))
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.5  # Return neutral score on error


class UserPreferences:
    """User notification preferences and settings."""
    
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        self.profit_thresholds: Dict[RiskTier, Decimal] = {}
        self.sport_preferences: Set[Sport] = set()
        self.bookmaker_preferences: Set[str] = set()
        self.time_filters: Dict[str, Any] = {}
        self.channel_settings: Dict[NotificationChannel, Dict[str, Any]] = {}
        self.quiet_hours: Dict[str, str] = {}
        self.custom_filters: List[NotificationFilter] = []
        self.dedup_settings: Dict[str, Any] = {}
        self.importance_weights: Dict[str, float] = {}
        self.escalation_rules: Dict[str, Any] = {}
        self.keywords: List[str] = []
        self.notification_frequency: Dict[str, int] = {}
        self.last_updated = datetime.utcnow()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], user_id: UUID) -> 'UserPreferences':
        """Create UserPreferences from dictionary."""
        prefs = cls(user_id)
        
        # Parse profit thresholds
        for tier_str, amount in data.get('profit_thresholds', {}).items():
            try:
                tier = RiskTier(tier_str)
                prefs.profit_thresholds[tier] = Decimal(str(amount))
            except (ValueError, TypeError):
                logger.warning(f"Invalid risk tier: {tier_str}")
        
        # Parse sport preferences
        for sport_str in data.get('sport_preferences', []):
            try:
                prefs.sport_preferences.add(Sport(sport_str))
            except ValueError:
                logger.warning(f"Invalid sport: {sport_str}")
        
        # Parse other settings
        prefs.bookmaker_preferences = set(data.get('bookmaker_preferences', []))
        prefs.time_filters = data.get('time_filters', {})
        prefs.channel_settings = data.get('channel_settings', {})
        prefs.quiet_hours = data.get('quiet_hours', {})
        prefs.dedup_settings = data.get('dedup_settings', {})
        prefs.importance_weights = data.get('importance_weights', {})
        prefs.escalation_rules = data.get('escalation_rules', {})
        prefs.keywords = data.get('keywords', [])
        prefs.notification_frequency = data.get('notification_frequency', {})
        
        # Parse custom filters
        for filter_data in data.get('custom_filters', []):
            filter_obj = NotificationFilter(
                name=filter_data['name'],
                logic_operator=filter_data.get('logic_operator', 'AND'),
                enabled=filter_data.get('enabled', True),
                priority_boost=filter_data.get('priority_boost', 0.0),
                description=filter_data.get('description')
            )
            
            for condition_data in filter_data.get('conditions', []):
                condition = FilterCondition(
                    field=condition_data['field'],
                    operator=FilterOperator(condition_data['operator']),
                    value=condition_data['value'],
                    description=condition_data.get('description')
                )
                filter_obj.conditions.append(condition)
            
            prefs.custom_filters.append(filter_obj)
        
        prefs.last_updated = datetime.utcnow()
        return prefs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert UserPreferences to dictionary."""
        return {
            'profit_thresholds': {tier.value: float(amount) for tier, amount in self.profit_thresholds.items()},
            'sport_preferences': [sport.value for sport in self.sport_preferences],
            'bookmaker_preferences': list(self.bookmaker_preferences),
            'time_filters': self.time_filters,
            'channel_settings': self.channel_settings,
            'quiet_hours': self.quiet_hours,
            'custom_filters': [
                {
                    'name': filter.name,
                    'logic_operator': filter.logic_operator,
                    'enabled': filter.enabled,
                    'priority_boost': filter.priority_boost,
                    'description': filter.description,
                    'conditions': [
                        {
                            'field': condition.field,
                            'operator': condition.operator.value,
                            'value': condition.value,
                            'description': condition.description
                        }
                        for condition in filter.conditions
                    ]
                }
                for filter in self.custom_filters
            ],
            'dedup_settings': self.dedup_settings,
            'importance_weights': self.importance_weights,
            'escalation_rules': self.escalation_rules,
            'keywords': self.keywords,
            'notification_frequency': self.notification_frequency,
            'last_updated': self.last_updated.isoformat()
        }


class NotificationDeduplicator:
    """Handles notification deduplication and grouping."""
    
    def __init__(self, dedup_window: timedelta = timedelta(minutes=5)):
        self.dedup_window = dedup_window
        self.notification_groups: Dict[str, List[Notification]] = defaultdict(list)
        self.last_seen: Dict[str, datetime] = {}
    
    def should_deduplicate(self, notification: Notification) -> bool:
        """Check if notification should be deduplicated."""
        key = self._generate_dedup_key(notification)
        now = datetime.utcnow()
        
        if key in self.last_seen:
            time_diff = now - self.last_seen[key]
            return time_diff < self.dedup_window
        
        return False
    
    def _generate_dedup_key(self, notification: Notification) -> str:
        """Generate deduplication key for notification."""
        # Create key based on opportunity characteristics
        data = notification.message.data
        if 'opportunity' in data:
            opp = data['opportunity']
            return f"{opp.get('sport', '')}:{opp.get('profit_margin', 0)}:{sorted(opp.get('bookmakers', []))}"
        
        # Fallback to notification type and priority
        return f"{notification.type.value}:{notification.priority.value}"
    
    def group_notifications(self, notifications: List[Notification]) -> Dict[str, List[Notification]]:
        """Group similar notifications together."""
        groups = defaultdict(list)
        
        for notification in notifications:
            key = self._generate_dedup_key(notification)
            groups[key].append(notification)
        
        return dict(groups)


class TimeFilter:
    """Handles time-based filtering including quiet hours."""
    
    def __init__(self):
        self.quiet_hours_config: Dict[str, Dict[str, str]] = {}
    
    def is_quiet_time(self, user_preferences: UserPreferences, current_time: Optional[datetime] = None) -> bool:
        """Check if current time falls within user's quiet hours."""
        if current_time is None:
            current_time = datetime.utcnow()
        
        quiet_hours = user_preferences.quiet_hours
        if not quiet_hours:
            return False
        
        # Parse quiet hours configuration
        for day_range, time_range in quiet_hours.items():
            try:
                start_str, end_str = time_range.split('-')
                start_hour, start_min = map(int, start_str.split(':'))
                end_hour, end_min = map(int, end_str.split(':'))
                
                current_hour = current_time.hour
                current_min = current_time.minute
                current_time_minutes = current_hour * 60 + current_min
                start_minutes = start_hour * 60 + start_min
                end_minutes = end_hour * 60 + end_min
                
                # Handle overnight quiet hours (e.g., 22:00-06:00)
                if start_minutes > end_minutes:
                    if current_time_minutes >= start_minutes or current_time_minutes <= end_minutes:
                        return True
                else:
                    if start_minutes <= current_time_minutes <= end_minutes:
                        return True
                        
            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid quiet hours configuration: {quiet_hours} - {e}")
        
        return False
    
    def filter_by_time(self, notifications: List[Notification], user_preferences: UserPreferences) -> List[Notification]:
        """Filter notifications based on time preferences."""
        current_time = datetime.utcnow()
        
        # Check quiet hours
        if self.is_quiet_time(user_preferences, current_time):
            # During quiet hours, only allow critical notifications
            return [n for n in notifications if n.priority == NotificationPriority.CRITICAL]
        
        return notifications


class CustomRuleEngine:
    """Engine for evaluating custom alert rules."""
    
    def __init__(self):
        self.custom_rules: Dict[str, NotificationFilter] = {}
    
    def add_rule(self, rule: NotificationFilter):
        """Add a custom rule."""
        self.custom_rules[rule.name] = rule
    
    def evaluate_notification(self, notification: Notification) -> float:
        """Evaluate notification against all custom rules."""
        score = 0.0
        
        for rule in self.custom_rules.values():
            if not rule.enabled:
                continue
            
            if self._evaluate_rule(rule, notification):
                score += rule.priority_boost
        
        return score
    
    def _evaluate_rule(self, rule: NotificationFilter, notification: Notification) -> bool:
        """Evaluate a single rule against notification."""
        results = []
        
        for condition in rule.conditions:
            result = self._evaluate_condition(condition, notification)
            results.append(result)
        
        if rule.logic_operator == "AND":
            return all(results)
        else:
            return any(results)
    
    def _evaluate_condition(self, condition: FilterCondition, notification: Notification) -> bool:
        """Evaluate a single condition."""
        try:
            # Get field value
            value = self._get_field_value(notification, condition.field)
            
            # Apply operator
            return self._apply_operator(value, condition.operator, condition.value)
            
        except Exception as e:
            logger.error(f"Error evaluating condition {condition.field}: {e}")
            return False
    
    def _get_field_value(self, notification: Notification, field: str) -> Any:
        """Get value of a field from notification."""
        # Handle nested fields
        if '.' in field:
            parts = field.split('.')
            value = notification
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif part in value.message.data:
                    value = value.message.data[part]
                else:
                    return None
            return value
        
        # Handle direct attributes
        if hasattr(notification, field):
            return getattr(notification, field)
        elif field in notification.message.data:
            return notification.message.data[field]
        
        return None
    
    def _apply_operator(self, value: Any, operator: FilterOperator, target: Any) -> bool:
        """Apply operator to compare value with target."""
        if value is None:
            return operator == FilterOperator.NOT_EQUALS
        
        try:
            if operator == FilterOperator.EQUALS:
                return value == target
            elif operator == FilterOperator.NOT_EQUALS:
                return value != target
            elif operator == FilterOperator.GREATER_THAN:
                return float(value) > float(target)
            elif operator == FilterOperator.GREATER_EQUAL:
                return float(value) >= float(target)
            elif operator == FilterOperator.LESS_THAN:
                return float(value) < float(target)
            elif operator == FilterOperator.LESS_EQUAL:
                return float(value) <= float(target)
            elif operator == FilterOperator.CONTAINS:
                return str(target).lower() in str(value).lower()
            elif operator == FilterOperator.NOT_CONTAINS:
                return str(target).lower() not in str(value).lower()
            elif operator == FilterOperator.IN:
                return value in target if isinstance(target, (list, set, tuple)) else False
            elif operator == FilterOperator.NOT_IN:
                return value not in target if isinstance(target, (list, set, tuple)) else True
            elif operator == FilterOperator.BETWEEN:
                if isinstance(target, (list, tuple)) and len(target) == 2:
                    return float(target[0]) <= float(value) <= float(target[1])
                return False
            elif operator == FilterOperator.REGEX:
                import re
                return bool(re.search(str(target), str(value)))
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error applying operator {operator.value}: {e}")
        
        return False


class EscalationManager:
    """Manages notification escalation rules."""
    
    def __init__(self):
        self.escalation_rules: Dict[str, Dict[str, Any]] = {}
    
    def should_escalate(self, notification: Notification, user_preferences: UserPreferences) -> Tuple[bool, Dict[str, Any]]:
        """Check if notification should be escalated."""
        escalation_config = user_preferences.escalation_rules
        
        # Check priority-based escalation
        priority_rules = escalation_config.get('priority_rules', {})
        if notification.priority.value in priority_rules:
            return True, priority_rules[notification.priority.value]
        
        # Check frequency-based escalation
        frequency_rules = escalation_config.get('frequency_rules', {})
        if self._check_frequency_escalation(notification, frequency_rules):
            return True, frequency_rules
        
        return False, {}
    
    def _check_frequency_escalation(self, notification: Notification, rules: Dict[str, Any]) -> bool:
        """Check if notification frequency triggers escalation."""
        # This would check notification history for frequency patterns
        # Implementation depends on storage layer
        return False


class NotificationAnalytics:
    """Tracks notification analytics and performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            'total_notifications': 0,
            'delivered_notifications': 0,
            'failed_notifications': 0,
            'acknowledged_notifications': 0,
            'clicked_notifications': 0,
            'channel_performance': defaultdict(int),
            'priority_distribution': defaultdict(int),
            'type_distribution': defaultdict(int),
            'user_engagement': defaultdict(float),
            'processing_times': [],
            'filter_effectiveness': defaultdict(int)
        }
    
    def record_notification(self, notification: Notification, status: str):
        """Record notification metrics."""
        self.metrics['total_notifications'] += 1
        
        if status == 'delivered':
            self.metrics['delivered_notifications'] += 1
        elif status == 'failed':
            self.metrics['failed_notifications'] += 1
        elif status == 'acknowledged':
            self.metrics['acknowledged_notifications'] += 1
        elif status == 'clicked':
            self.metrics['clicked_notifications'] += 1
        
        # Record distributions
        self.metrics['priority_distribution'][notification.priority.value] += 1
        self.metrics['type_distribution'][notification.type.value] += 1
        
        for channel in notification.channels:
            self.metrics['channel_performance'][channel.value] += 1
    
    def record_filter_result(self, filter_name: str, passed: bool):
        """Record filter effectiveness."""
        self.metrics['filter_effectiveness'][filter_name] += 1 if passed else 0
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get current analytics data."""
        return dict(self.metrics)


class NotificationFilterEngine:
    """Main notification filtering and preferences engine."""
    
    def __init__(self, supabase_client: Optional[SupabaseDataLayer] = None):
        self.supabase = supabase_client
        self.user_preferences: Dict[UUID, UserPreferences] = {}
        self.relevance_scorer = TfidfRelevanceScorer(model_path="models/relevance_model.pkl.gz")
        self.deduplicator = NotificationDeduplicator()
        self.time_filter = TimeFilter()
        self.rule_engine = CustomRuleEngine()
        self.escalation_manager = EscalationManager()
        self.analytics = NotificationAnalytics()
        self.filter_cache: Dict[str, Any] = {}
        self._performance_mode = False
    
    async def load_user_preferences(self, user_id: UUID) -> UserPreferences:
        """Load user preferences from Supabase."""
        if user_id in self.user_preferences:
            return self.user_preferences[user_id]
        
        try:
            if self.supabase:
                # Fetch user preferences from Supabase
                prefs_data = await self._fetch_preferences_from_supabase(user_id)
                if prefs_data:
                    preferences = UserPreferences.from_dict(prefs_data, user_id)
                    self.user_preferences[user_id] = preferences
                    return preferences
            
            # Create default preferences if not found
            preferences = UserPreferences(user_id)
            self.user_preferences[user_id] = preferences
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to load user preferences for {user_id}: {e}")
            preferences = UserPreferences(user_id)
            self.user_preferences[user_id] = preferences
            return preferences
    
    async def _fetch_preferences_from_supabase(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Fetch user preferences from Supabase."""
        try:
            # This would fetch from a user_preferences table
            # Implementation depends on actual Supabase schema
            result = self.supabase.client.table('user_preferences').select('*').eq('user_id', str(user_id)).execute()
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching preferences from Supabase: {e}")
            return None
    
    async def save_user_preferences(self, user_id: UUID, preferences: UserPreferences):
        """Save user preferences to Supabase."""
        try:
            preferences.last_updated = datetime.utcnow()
            
            if self.supabase:
                await self._save_preferences_to_supabase(user_id, preferences)
            
            # Update cache
            self.user_preferences[user_id] = preferences
            
        except Exception as e:
            logger.error(f"Failed to save user preferences for {user_id}: {e}")
    
    async def _save_preferences_to_supabase(self, user_id: UUID, preferences: UserPreferences):
        """Save preferences to Supabase."""
        try:
            data = preferences.to_dict()
            data['user_id'] = str(user_id)
            
            # Upsert preferences
            self.supabase.client.table('user_preferences').upsert(data).execute()
            
        except Exception as e:
            logger.error(f"Error saving preferences to Supabase: {e}")
    
    async def filter_notifications(
        self,
        notifications: List[Notification],
        user_id: UUID,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Notification], Dict[str, Any]]:
        """Filter and process notifications for a user."""
        if context is None:
            context = {}
        
        # Load user preferences
        preferences = await self.load_user_preferences(user_id)
        
        # Apply various filters
        filtered_notifications = notifications.copy()
        
        # 1. Time-based filtering (quiet hours)
        filtered_notifications = self.time_filter.filter_by_time(filtered_notifications, preferences)
        
        # 2. Deduplication
        unique_notifications = []
        for notification in filtered_notifications:
            if not self.deduplicator.should_deduplicate(notification):
                unique_notifications.append(notification)
        filtered_notifications = unique_notifications
        
        # 3. Custom rules
        scored_notifications = []
        for notification in filtered_notifications:
            rule_score = self.rule_engine.evaluate_notification(notification)
            relevance_score = self.relevance_scorer.calculate_score(notification, preferences.to_dict())
            
            # Combine scores
            total_score = rule_score + relevance_score
            notification.message.data['filter_score'] = total_score
            scored_notifications.append(notification)
        
        # 4. Apply user preferences filters
        filtered_notifications = self._apply_preference_filters(scored_notifications, preferences)
        
        # 5. Sort by score and priority
        filtered_notifications.sort(
            key=lambda n: (
                n.priority.value,
                n.message.data.get('filter_score', 0)
            ),
            reverse=True
        )
        
        # 6. Check for escalation
        for notification in filtered_notifications:
            should_escalate, escalation_data = self.escalation_manager.should_escalate(
                notification, preferences
            )
            if should_escalate:
                notification.message.data['escalation'] = escalation_data
        
        # 7. Analytics
        self.analytics.record_notification_batch(filtered_notifications)
        
        metadata = {
            'total_input': len(notifications),
            'filtered_output': len(filtered_notifications),
            'filter_applied': 'multi_criteria',
            'user_id': str(user_id),
            'processing_time': context.get('processing_time', 0)
        }
        
        return filtered_notifications, metadata
    
    def _apply_preference_filters(self, notifications: List[Notification], preferences: UserPreferences) -> List[Notification]:
        """Apply user preference filters to notifications."""
        filtered = []
        
        for notification in notifications:
            if self._passes_preference_filters(notification, preferences):
                filtered.append(notification)
        
        return filtered
    
    def _passes_preference_filters(self, notification: Notification, preferences: UserPreferences) -> bool:
        """Check if notification passes user's preference filters."""
        data = notification.message.data
        
        # Check profit thresholds
        if 'opportunity' in data:
            opp = data['opportunity']
            risk_tier = opp.get('risk_tier')
            profit_margin = opp.get('profit_margin', 0)
            
            if risk_tier and risk_tier in preferences.profit_thresholds:
                threshold = preferences.profit_thresholds[RiskTier(risk_tier)]
                if profit_margin < float(threshold):
                    return False
        
        # Check sport preferences
        if 'opportunity' in data and 'sport' in data['opportunity']:
            sport = data['opportunity']['sport']
            if preferences.sport_preferences and Sport(sport) not in preferences.sport_preferences:
                return False
        
        # Check bookmaker preferences
        if 'opportunity' in data and 'bookmakers' in data['opportunity']:
            bookmakers = data['opportunity']['bookmakers']
            if preferences.bookmaker_preferences:
                # If user has specific preferences, only show those
                if not any(book in preferences.bookmaker_preferences for book in bookmakers):
                    return False
        
        return True
    
    def add_custom_filter(self, user_id: UUID, filter_obj: NotificationFilter):
        """Add custom filter for a user."""
        # This would be part of the preferences update
        pass
    
    def set_performance_mode(self, enabled: bool):
        """Enable/disable performance mode for high-volume streams."""
        self._performance_mode = enabled
        if enabled:
            logger.info("Performance mode enabled - skipping advanced analytics")
        else:
            logger.info("Performance mode disabled - full analytics enabled")
    
    def get_filter_analytics(self) -> Dict[str, Any]:
        """Get analytics about filter performance."""
        return {
            'user_preferences_loaded': len(self.user_preferences),
            'analytics': self.analytics.get_analytics(),
            'cache_size': len(self.filter_cache),
            'performance_mode': self._performance_mode
        }
    
    def create_default_preferences(self) -> UserPreferences:
        """Create default user preferences."""
        prefs = UserPreferences(uuid4())
        
        # Set default profit thresholds
        prefs.profit_thresholds = {
            RiskTier.TIER_A: Decimal('0.02'),  # 2%
            RiskTier.TIER_B: Decimal('0.05'),  # 5%
            RiskTier.TIER_C: Decimal('0.10'),  # 10%
            RiskTier.TIER_D: Decimal('0.15')   # 15%
        }
        
        # Set default sport preferences
        prefs.sport_preferences = {
            Sport.FOOTBALL,
            Sport.BASKETBALL,
            Sport.TENNIS
        }
        
        # Set default channel settings
        for channel in NotificationChannel:
            prefs.channel_settings[channel] = {
                'enabled': True,
                'rate_limit_per_hour': 100
            }
        
        # Set quiet hours
        prefs.quiet_hours = {
            'weekdays': '22:00-06:00',
            'weekends': '00:00-08:00'
        }
        
        # Set default importance weights
        prefs.importance_weights = {
            'profit_margin': 1.0,
            'risk_tier': 0.8,
            'bookmaker_reliability': 0.6
        }
        
        # Set default escalation rules
        prefs.escalation_rules = {
            'priority_rules': {
                'critical': {
                    'channels': ['push', 'sms'],
                    'force_delivery': True
                },
                'high': {
                    'channels': ['push', 'email']
                }
            }
        }
        
        return prefs


# Factory function for creating filter engine
def create_filter_engine(supabase_url: Optional[str] = None, supabase_key: Optional[str] = None) -> NotificationFilterEngine:
    """Create a notification filter engine with Supabase integration."""
    supabase_client = None
    if supabase_url and supabase_key:
        supabase_client = SupabaseDataLayer(supabase_url, supabase_key)
    
    return NotificationFilterEngine(supabase_client)


# Utility functions
def create_profit_threshold_filter(threshold: Decimal, risk_tier: RiskTier) -> NotificationFilter:
    """Create a filter for profit threshold by risk tier."""
    return NotificationFilter(
        name=f"profit_threshold_{risk_tier.value}",
        conditions=[
            FilterCondition(
                field="message.data.opportunity.risk_tier",
                operator=FilterOperator.EQUALS,
                value=risk_tier.value
            ),
            FilterCondition(
                field="message.data.opportunity.profit_margin",
                operator=FilterOperator.GREATER_EQUAL,
                value=float(threshold)
            )
        ],
        description=f"Filter opportunities with profit >= {threshold}% for {risk_tier.value}"
    )


def create_sport_filter(sports: List[Sport]) -> NotificationFilter:
    """Create a filter for specific sports."""
    return NotificationFilter(
        name=f"sports_filter_{len(sports)}_sports",
        conditions=[
            FilterCondition(
                field="message.data.opportunity.sport",
                operator=FilterOperator.IN,
                value=[sport.value for sport in sports]
            )
        ],
        description=f"Filter notifications for sports: {', '.join(s.value for s in sports)}"
    )


def create_bookmaker_filter(bookmakers: List[str], include: bool = True) -> NotificationFilter:
    """Create a filter for specific bookmakers."""
    operator = FilterOperator.IN if include else FilterOperator.NOT_IN
    
    return NotificationFilter(
        name=f"bookmaker_filter_{len(bookmakers)}_books",
        conditions=[
            FilterCondition(
                field="message.data.opportunity.bookmakers",
                operator=operator,
                value=bookmakers
            )
        ],
        description=f"{'Include' if include else 'Exclude'} notifications from: {', '.join(bookmakers)}"
    )


def create_time_window_filter(start_time: str, end_time: str, timezone: str = "UTC") -> NotificationFilter:
    """Create a filter for specific time windows."""
    return NotificationFilter(
        name=f"time_window_{start_time}-{end_time}",
        conditions=[
            FilterCondition(
                field="created_at",
                operator=FilterOperator.BETWEEN,
                value=[start_time, end_time]
            )
        ],
        description=f"Filter notifications between {start_time} and {end_time} ({timezone})"
    )


# Integration helpers for existing ARBitech components
async def filter_opportunity_notifications(
    opportunities: List[MathOpportunity],
    user_id: UUID,
    filter_engine: NotificationFilterEngine
) -> List[Notification]:
    """Convert arbitrage opportunities to filtered notifications."""
    notifications = []
    
    for opportunity in opportunities:
        # Create notification from opportunity
        notification = Notification(
            user_id=user_id,
            type=NotificationType.OPPORTUNITY_ALERT,
            priority=_determine_priority_from_opportunity(opportunity),
            message=MessageData(
                title=f"Arbitrage Opportunity: {opportunity.sport}",
                body=f"Profit margin: {opportunity.profit_margin:.2%}",
                data={
                    'opportunity': {
                        'sport': opportunity.sport,
                        'profit_margin': float(opportunity.profit_margin),
                        'risk_tier': opportunity.risk_tier,
                        'bookmakers': [leg.bookmaker for leg in opportunity.legs],
                        'expected_profit': float(opportunity.expected_profit)
                    }
                }
            ),
            channels=[NotificationChannel.PUSH, NotificationChannel.EMAIL]
        )
        
        notifications.append(notification)
    
    # Filter notifications
    filtered_notifications, _ = await filter_engine.filter_notifications(notifications, user_id)
    
    return filtered_notifications


def _determine_priority_from_opportunity(opportunity: MathOpportunity) -> NotificationPriority:
    """Determine notification priority based on opportunity characteristics."""
    if opportunity.profit_margin > Decimal('0.15'):  # > 15%
        return NotificationPriority.CRITICAL
    elif opportunity.profit_margin > Decimal('0.08'):  # > 8%
        return NotificationPriority.HIGH
    elif opportunity.profit_margin > Decimal('0.03'):  # > 3%
        return NotificationPriority.MEDIUM
    else:
        return NotificationPriority.LOW


# Enhancement to analytics class
def record_notification_batch(self, notifications: List[Notification]):
    """Record analytics for a batch of notifications."""
    for notification in notifications:
        self.record_notification(notification, 'processed')


# Monkey patch the analytics class
NotificationAnalytics.record_notification_batch = record_notification_batch


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def demo():
        # Create filter engine
        filter_engine = create_filter_engine()
        
        # Create user preferences
        preferences = filter_engine.create_default_preferences()
        user_id = uuid4()
        
        # Add custom filters
        profit_filter = create_profit_threshold_filter(Decimal('0.05'), RiskTier.TIER_A)
        sport_filter = create_sport_filter([Sport.FOOTBALL, Sport.BASKETBALL])
        
        # Convert to preference format
        preferences.custom_filters = [profit_filter, sport_filter]
        
        # Save preferences
        await filter_engine.save_user_preferences(user_id, preferences)
        
        # Create sample notifications
        notifications = [
            Notification(
                user_id=user_id,
                type=NotificationType.OPPORTUNITY_ALERT,
                priority=NotificationPriority.HIGH,
                message=MessageData(
                    title="Football Arbitrage Opportunity",
                    body="Liverpool vs Arsenal - 8.5% profit",
                    data={
                        'opportunity': {
                            'sport': 'football',
                            'profit_margin': 0.085,
                            'risk_tier': 'tier_a',
                            'bookmakers': ['bet365', 'william_hill']
                        }
                    }
                ),
                channels=[NotificationChannel.PUSH]
            )
        ]
        
        # Filter notifications
        filtered_notifications, metadata = await filter_engine.filter_notifications(
            notifications, user_id
        )
        
        print(f"Input: {len(notifications)} notifications")
        print(f"Output: {len(filtered_notifications)} notifications")
        print(f"Metadata: {metadata}")
        print(f"Analytics: {filter_engine.get_filter_analytics()}")
    
    # Run demo
    asyncio.run(demo())