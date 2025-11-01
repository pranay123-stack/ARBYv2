"""
Data Aggregator - Central data aggregation engine for consolidating odds and market data.

This module provides a comprehensive system for collecting, normalizing, and synchronizing
odds data from multiple bookmaker sources, including real-time streaming capabilities.
"""

import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging
import hashlib
from collections import defaultdict
import statistics

try:
    # Try relative imports first (when used as part of arbitech package)
    from .bookmaker_manager import (
        BookmakerManager, get_bookmaker_manager, BookmakerStatus, 
        PriorityLevel, DataSourceType
    )
    from ..utils.logger import get_logger
    from ..storage.models import Sport
except ImportError:
    # Fall back to absolute imports (when used standalone)
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    from bookmaker_manager import (
        BookmakerManager, get_bookmaker_manager, BookmakerStatus, 
        PriorityLevel, DataSourceType
    )
    
    try:
        from utils.logger import get_logger
    except ImportError:
        import logging
        def get_logger(name):
            return logging.getLogger(name)
    
    try:
        from storage.models import Sport
    except ImportError:
        # Mock Sport enum for standalone usage
        from enum import Enum
        class Sport(str, Enum):
            FOOTBALL = "football"
            TENNIS = "tennis"
            BASKETBALL = "basketball"
            BASEBALL = "baseball"
            HOCKEY = "hockey"


logger = get_logger(__name__)


class AggregationStrategy(str, Enum):
    """Data aggregation strategies."""
    PRIORITY_BASED = "priority_based"
    WEIGHTED_AVERAGE = "weighted_average"
    MOST_RECENT = "most_recent"
    CONSENSUS = "consensus"
    FAILOVER = "failover"


class DataQualityLevel(str, Enum):
    """Data quality assessment levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INVALID = "invalid"


class UpdateFrequency(str, Enum):
    """Data update frequency recommendations."""
    REAL_TIME = "real_time"
    HIGH = "high"      # Every 30 seconds
    MEDIUM = "medium"  # Every 2 minutes
    LOW = "low"        # Every 5 minutes
    BATCH = "batch"    # Every 15+ minutes


@dataclass
class MarketOdds:
    """Individual market odds data point."""
    bookmaker: str
    outcome: str
    odds: float
    odds_format: str = "decimal"  # decimal, american, fractional
    implied_probability: float = 0.0
    stake_limit: Optional[float] = None
    liquidity: Optional[float] = None
    last_updated: Optional[datetime] = None
    source_reliability: float = 100.0
    data_quality: DataQualityLevel = DataQualityLevel.GOOD
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class MarketData:
    """Market-level data container."""
    sport: Sport
    event_name: str
    event_id: str
    market_type: str  # match_winner, over_under, etc.
    market_id: str
    start_time: datetime
    participants: List[str]  # team/player names
    
    # Odds data
    odds: List[MarketOdds] = field(default_factory=list)
    
    # Market metadata
    league: Optional[str] = None
    venue: Optional[str] = None
    status: str = "open"  # open, suspended, closed, settled
    last_update: datetime = field(default_factory=datetime.utcnow)
    
    # Quality and reliability
    aggregation_strategy: AggregationStrategy = AggregationStrategy.PRIORITY_BASED
    consensus_odds: Optional[Dict[str, float]] = None
    confidence_score: float = 0.0
    data_freshness_minutes: float = 0.0
    source_count: int = 0
    conflicting_sources: int = 0
    
    # Aggregation metadata
    aggregation_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1


@dataclass
class AggregatedEvent:
    """Complete event data with multiple markets."""
    event_id: str
    event_name: str
    sport: Sport
    start_time: datetime
    participants: List[str]
    
    # Markets
    markets: Dict[str, MarketData] = field(default_factory=dict)
    
    # Event metadata
    league: Optional[str] = None
    venue: Optional[str] = None
    event_status: str = "scheduled"
    
    # Quality metrics
    overall_quality_score: float = 0.0
    data_completeness: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    source_coverage: float = 0.0
    
    # Performance metrics
    aggregation_latency_ms: float = 0.0
    processing_time_ms: float = 0.0
    source_count: int = 0


@dataclass
class AggregationStats:
    """Performance and quality statistics."""
    total_events_processed: int = 0
    total_markets_processed: int = 0
    total_odds_collected: int = 0
    successful_aggregations: int = 0
    failed_aggregations: int = 0
    average_latency_ms: float = 0.0
    data_quality_distribution: Dict[str, int] = field(default_factory=dict)
    source_reliability_scores: Dict[str, float] = field(default_factory=dict)
    last_stats_update: datetime = field(default_factory=datetime.utcnow)


class OddsNormalizer:
    """Normalizes odds from different formats and bookmakers."""
    
    @staticmethod
    def normalize_odds(odds_value: Union[str, float], source_format: str) -> Tuple[float, str]:
        """Normalize odds to decimal format."""
        try:
            if isinstance(odds_value, str):
                odds_value = float(odds_value.strip())
            
            if source_format.lower() == "decimal":
                return odds_value, "decimal"
            
            elif source_format.lower() == "american":
                if odds_value > 0:
                    decimal_odds = 1 + (odds_value / 100)
                else:
                    decimal_odds = 1 + (100 / abs(odds_value))
                return decimal_odds, "decimal"
            
            elif source_format.lower() in ["fractional", "fraction"]:
                # Parse fractional odds like "5/2" or "3/1"
                if "/" in str(odds_value):
                    numerator, denominator = str(odds_value).split("/")
                    decimal_odds = float(numerator) / float(denominator) + 1
                else:
                    decimal_odds = float(odds_value) + 1
                return decimal_odds, "decimal"
            
            else:
                # Assume already decimal
                return float(odds_value), "decimal"
        
        except Exception as e:
            logger.warning(f"Failed to normalize odds {odds_value} from {source_format}: {e}")
            return 0.0, "invalid"
    
    @staticmethod
    def calculate_implied_probability(decimal_odds: float) -> float:
        """Calculate implied probability from decimal odds."""
        if decimal_odds <= 0:
            return 0.0
        return 1.0 / decimal_odds


class DataQualityAssessor:
    """Assesses and scores data quality from various sources."""
    
    def __init__(self):
        self.quality_thresholds = {
            DataQualityLevel.EXCELLENT: 0.95,
            DataQualityLevel.GOOD: 0.85,
            DataQualityLevel.FAIR: 0.70,
            DataQualityLevel.POOR: 0.50
        }
    
    def assess_odds_quality(self, 
                           odds_list: List[MarketOdds], 
                           expected_outcomes: Set[str]) -> Dict[str, DataQualityLevel]:
        """Assess quality of odds data."""
        quality_scores = {}
        
        for outcome in expected_outcomes:
            outcome_odds = [o for o in odds_list if o.outcome.lower() == outcome.lower()]
            
            if not outcome_odds:
                quality_scores[outcome] = DataQualityLevel.INVALID
                continue
            
            # Check for consistency across sources
            odds_values = [o.odds for o in outcome_odds if o.odds > 0]
            
            if not odds_values:
                quality_scores[outcome] = DataQualityLevel.INVALID
                continue
            
            # Calculate coefficient of variation
            if len(odds_values) > 1:
                mean_odds = statistics.mean(odds_values)
                std_odds = statistics.stdev(odds_values)
                cv = std_odds / mean_odds if mean_odds > 0 else float('inf')
                
                # Lower CV indicates higher consistency
                consistency_score = max(0, 1 - (cv / 0.5))  # Normalize CV
            else:
                consistency_score = 1.0
            
            # Check data freshness
            now = datetime.utcnow()
            freshness_scores = []
            
            for odds in outcome_odds:
                if odds.last_updated:
                    age_minutes = (now - odds.last_updated).total_seconds() / 60
                    if age_minutes < 1:
                        freshness_score = 1.0
                    elif age_minutes < 5:
                        freshness_score = 0.9
                    elif age_minutes < 15:
                        freshness_score = 0.7
                    else:
                        freshness_score = 0.3
                    freshness_scores.append(freshness_score)
            
            avg_freshness = statistics.mean(freshness_scores) if freshness_scores else 0.0
            
            # Source reliability weighting
            weighted_reliability = 0
            total_weight = 0
            
            for odds in outcome_odds:
                weight = odds.source_reliability / 100.0
                weighted_reliability += odds.data_quality.value * weight
                total_weight += weight
            
            source_quality = weighted_reliability / total_weight if total_weight > 0 else 0.5
            
            # Overall quality score
            overall_score = (
                consistency_score * 0.4 +
                avg_freshness * 0.3 +
                source_quality * 0.3
            )
            
            # Determine quality level
            if overall_score >= self.quality_thresholds[DataQualityLevel.EXCELLENT]:
                quality_scores[outcome] = DataQualityLevel.EXCELLENT
            elif overall_score >= self.quality_thresholds[DataQualityLevel.GOOD]:
                quality_scores[outcome] = DataQualityLevel.GOOD
            elif overall_score >= self.quality_thresholds[DataQualityLevel.FAIR]:
                quality_scores[outcome] = DataQualityLevel.FAIR
            elif overall_score >= self.quality_thresholds[DataQualityLevel.POOR]:
                quality_scores[outcome] = DataQualityLevel.POOR
            else:
                quality_scores[outcome] = DataQualityLevel.POOR
        
        return quality_scores
    
    def detect_conflicts(self, odds_list: List[MarketOdds], threshold: float = 0.1) -> int:
        """Detect conflicting odds data."""
        conflicts = 0
        
        # Group odds by outcome
        outcome_groups = defaultdict(list)
        for odds in odds_list:
            outcome_groups[odds.outcome.lower()].append(odds)
        
        for outcome, outcome_odds in outcome_groups.items():
            if len(outcome_odds) < 2:
                continue
            
            # Check for significant odds discrepancies
            odds_values = [o.odds for o in outcome_odds if o.odds > 0]
            
            if len(odds_values) > 1:
                max_odds = max(odds_values)
                min_odds = min(odds_values)
                spread = (max_odds - min_odds) / min_odds
                
                if spread > threshold:  # 10% spread threshold
                    conflicts += 1
        
        return conflicts


class DataAggregator:
    """Central data aggregation engine."""
    
    def __init__(self, bookmaker_manager: Optional[BookmakerManager] = None):
        self.bookmaker_manager = bookmaker_manager or BookmakerManager()
        self.logger = get_logger(__name__)
        
        # Normalization and quality assessment
        self.normalizer = OddsNormalizer()
        self.quality_assessor = DataQualityAssessor()
        
        # Aggregation state
        self.active_aggregations: Dict[str, AggregatedEvent] = {}
        self.aggregation_stats = AggregationStats()
        
        # Processing configuration
        self.max_concurrent_aggregations = 20
        self.aggregation_timeout = 30  # seconds
        self.data_freshness_threshold = 15  # minutes
        
        # Event callbacks
        self.aggregation_complete_callbacks: List[Callable] = []
        self.quality_threshold_callbacks: List[Callable] = []
        
        # Streaming and real-time updates
        self.streaming_enabled = True
        self.update_frequency: Dict[str, UpdateFrequency] = {}
        self.last_update_times: Dict[str, datetime] = {}
        
        # Concurrency control
        self.aggregation_semaphore = asyncio.Semaphore(self.max_concurrent_aggregations)
        
        # Performance tracking
        self.processing_times: List[float] = []
        self.quality_history: List[Dict[str, float]] = []
    
    async def initialize(self):
        """Initialize the data aggregator."""
        try:
            await self.bookmaker_manager.initialize()
            self.logger.info("Data aggregator initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize data aggregator: {e}")
            raise
    
    async def aggregate_sports_data(self, 
                                   sports: List[Sport],
                                   markets: Optional[List[str]] = None,
                                   aggregation_strategy: AggregationStrategy = AggregationStrategy.PRIORITY_BASED,
                                   timeout_seconds: Optional[int] = None) -> Dict[str, AggregatedEvent]:
        """Aggregate data for multiple sports concurrently."""
        timeout = timeout_seconds or self.aggregation_timeout
        
        tasks = []
        for sport in sports:
            task = asyncio.create_task(
                self.aggregate_sport_data(sport, markets, aggregation_strategy)
            )
            tasks.append(task)
        
        results = {}
        for task in asyncio.as_completed(tasks, timeout=timeout):
            try:
                sport_events = await task
                results.update(sport_events)
            except asyncio.TimeoutError:
                self.logger.warning(f"Aggregation timeout for sports batch: {sports}")
            except Exception as e:
                self.logger.error(f"Aggregation error in sports batch: {e}")
        
        return results
    
    async def aggregate_sport_data(self, 
                                  sport: Sport,
                                  markets: Optional[List[str]] = None,
                                  aggregation_strategy: AggregationStrategy = AggregationStrategy.PRIORITY_BASED) -> Dict[str, AggregatedEvent]:
        """Aggregate data for a specific sport."""
        start_time = time.time()
        
        try:
            # Collect data from all bookmakers
            bookmaker_data = await self.bookmaker_manager.collect_data_concurrent(
                sports=[sport.value], markets=markets
            )
            
            # Process and normalize data
            normalized_data = await self._normalize_bookmaker_data(bookmaker_data, sport)
            
            # Aggregate by events
            aggregated_events = await self._aggregate_events(normalized_data, aggregation_strategy)
            
            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            self.processing_times.append(processing_time)
            
            self.aggregation_stats.total_events_processed += len(aggregated_events)
            self.aggregation_stats.total_markets_processed += sum(len(event.markets) for event in aggregated_events.values())
            
            for event in aggregated_events.values():
                self.aggregation_stats.total_odds_collected += sum(len(market.odds) for market in event.markets.values())
                event.processing_time_ms = processing_time / len(aggregated_events)
            
            return aggregated_events
        
        except Exception as e:
            self.logger.error(f"Sport aggregation failed for {sport.value}: {e}")
            self.aggregation_stats.failed_aggregations += 1
            return {}
    
    async def _normalize_bookmaker_data(self, 
                                       bookmaker_data: Dict[str, Any], 
                                       sport: Sport) -> List[MarketData]:
        """Normalize raw bookmaker data into MarketData objects."""
        normalized_markets = []
        
        for bookmaker_name, data in bookmaker_data.items():
            if data.get('status') != 'success':
                continue
            
            try:
                bookmaker_markets = self._extract_markets_from_data(data['data'], bookmaker_name, sport)
                normalized_markets.extend(bookmaker_markets)
            
            except Exception as e:
                self.logger.warning(f"Failed to normalize data from {bookmaker_name}: {e}")
        
        return normalized_markets
    
    def _extract_markets_from_data(self, 
                                  raw_data: Any, 
                                  bookmaker_name: str, 
                                  sport: Sport) -> List[MarketData]:
        """Extract market information from raw bookmaker data."""
        markets = []
        
        try:
            # Handle different data structures
            if isinstance(raw_data, dict):
                if 'events' in raw_data:
                    events = raw_data['events']
                elif 'markets' in raw_data:
                    events = [{'markets': raw_data['markets']}]
                else:
                    events = [raw_data]
            elif isinstance(raw_data, list):
                events = raw_data
            else:
                return markets
            
            for event_data in events:
                if not isinstance(event_data, dict):
                    continue
                
                # Extract event information
                event_name = event_data.get('name', event_data.get('event_name', 'Unknown Event'))
                event_id = self._generate_event_id(event_name, sport.value)
                start_time = self._parse_event_time(event_data.get('start_time'))
                participants = self._extract_participants(event_data)
                league = event_data.get('league', event_data.get('competition'))
                
                # Process markets
                event_markets = event_data.get('markets', event_data.get('bets', []))
                
                if isinstance(event_markets, dict):
                    for market_type, market_odds in event_markets.items():
                        market_data = self._create_market_data(
                            event_id, event_name, sport, market_type, 
                            market_odds, bookmaker_name, start_time, participants
                        )
                        if market_data:
                            markets.append(market_data)
                
                elif isinstance(event_markets, list):
                    for market in event_markets:
                        market_type = market.get('name', market.get('type', 'unknown'))
                        market_odds = market.get('odds', market.get('outcomes', []))
                        
                        market_data = self._create_market_data(
                            event_id, event_name, sport, market_type, 
                            market_odds, bookmaker_name, start_time, participants
                        )
                        if market_data:
                            markets.append(market_data)
        
        except Exception as e:
            self.logger.warning(f"Market extraction failed: {e}")
        
        return markets
    
    def _create_market_data(self, 
                           event_id: str, 
                           event_name: str, 
                           sport: Sport, 
                           market_type: str,
                           market_odds: Any, 
                           bookmaker_name: str, 
                           start_time: datetime, 
                           participants: List[str]) -> Optional[MarketData]:
        """Create MarketData object from extracted data."""
        try:
            market_id = self._generate_market_id(event_id, market_type)
            odds_list = []
            
            # Process odds data
            if isinstance(market_odds, dict):
                for outcome, odds_data in market_odds.items():
                    if isinstance(odds_data, dict):
                        odds_value = odds_data.get('odds', odds_data.get('price', odds_data.get('value')))
                        odds_format = odds_data.get('format', 'decimal')
                    else:
                        odds_value = odds_data
                        odds_format = 'decimal'
                    
                    if odds_value is not None:
                        normalized_odds, _ = self.normalizer.normalize_odds(odds_value, odds_format)
                        implied_prob = self.normalizer.calculate_implied_probability(normalized_odds)
                        
                        market_odds_obj = MarketOdds(
                            bookmaker=bookmaker_name,
                            outcome=outcome,
                            odds=normalized_odds,
                            odds_format="decimal",
                            implied_probability=implied_prob,
                            last_updated=datetime.utcnow(),
                            source_reliability=self._get_bookmaker_reliability(bookmaker_name)
                        )
                        odds_list.append(market_odds_obj)
            
            elif isinstance(market_odds, list):
                for odds_data in market_odds:
                    if isinstance(odds_data, dict):
                        outcome = odds_data.get('outcome', odds_data.get('name', 'unknown'))
                        odds_value = odds_data.get('odds', odds_data.get('price', odds_data.get('value')))
                        odds_format = odds_data.get('format', 'decimal')
                        
                        if odds_value is not None:
                            normalized_odds, _ = self.normalizer.normalize_odds(odds_value, odds_format)
                            implied_prob = self.normalizer.calculate_implied_probability(normalized_odds)
                            
                            market_odds_obj = MarketOdds(
                                bookmaker=bookmaker_name,
                                outcome=outcome,
                                odds=normalized_odds,
                                odds_format="decimal",
                                implied_probability=implied_prob,
                                last_updated=datetime.utcnow(),
                                source_reliability=self._get_bookmaker_reliability(bookmaker_name)
                            )
                            odds_list.append(market_odds_obj)
            
            if not odds_list:
                return None
            
            return MarketData(
                sport=sport,
                event_name=event_name,
                event_id=event_id,
                market_type=market_type,
                market_id=market_id,
                start_time=start_time,
                participants=participants,
                odds=odds_list,
                league=None,  # Will be set during aggregation
                last_update=datetime.utcnow(),
                source_count=1
            )
        
        except Exception as e:
            self.logger.warning(f"Market data creation failed: {e}")
            return None
    
    async def _aggregate_events(self, 
                               market_data_list: List[MarketData], 
                               strategy: AggregationStrategy) -> Dict[str, AggregatedEvent]:
        """Aggregate market data into events using specified strategy."""
        # Group market data by event
        event_groups = defaultdict(list)
        
        for market_data in market_data_list:
            event_groups[market_data.event_id].append(market_data)
        
        aggregated_events = {}
        
        for event_id, event_markets in event_groups.items():
            try:
                aggregated_event = await self._create_aggregated_event(event_id, event_markets, strategy)
                if aggregated_event:
                    aggregated_events[event_id] = aggregated_event
                    
                    # Store in active aggregations
                    self.active_aggregations[event_id] = aggregated_event
            
            except Exception as e:
                self.logger.error(f"Event aggregation failed for {event_id}: {e}")
        
        return aggregated_events
    
    async def _create_aggregated_event(self, 
                                     event_id: str, 
                                     market_data_list: List[MarketData], 
                                     strategy: AggregationStrategy) -> Optional[AggregatedEvent]:
        """Create aggregated event from market data."""
        try:
            # Get first market for event-level data
            first_market = market_data_list[0]
            
            aggregated_markets = {}
            
            # Group markets by type
            market_groups = defaultdict(list)
            for market_data in market_data_list:
                market_groups[market_data.market_type].append(market_data)
            
            # Aggregate each market type
            for market_type, markets in market_groups.items():
                aggregated_market = await self._aggregate_market_data(markets, strategy)
                if aggregated_market:
                    aggregated_markets[market_type] = aggregated_market
            
            if not aggregated_markets:
                return None
            
            # Create aggregated event
            event = AggregatedEvent(
                event_id=event_id,
                event_name=first_market.event_name,
                sport=first_market.sport,
                start_time=first_market.start_time,
                participants=first_market.participants,
                markets=aggregated_markets,
                league=first_market.league,
                overall_quality_score=self._calculate_overall_quality(aggregated_markets),
                data_completeness=self._calculate_completeness(aggregated_markets),
                source_coverage=self._calculate_source_coverage(market_data_list),
                source_count=len(set(m.bookmaker for m in market_data_list))
            )
            
            return event
        
        except Exception as e:
            self.logger.error(f"Aggregated event creation failed for {event_id}: {e}")
            return None
    
    async def _aggregate_market_data(self, 
                                   market_data_list: List[MarketData], 
                                   strategy: AggregationStrategy) -> Optional[MarketData]:
        """Aggregate multiple market data objects."""
        if not market_data_list:
            return None
        
        try:
            # Start with first market as base
            base_market = market_data_list[0]
            aggregated_odds = []
            
            # Collect all odds for each outcome
            outcome_odds = defaultdict(list)
            
            for market_data in market_data_list:
                for odds in market_data.odds:
                    outcome_odds[odds.outcome.lower()].append(odds)
            
            # Apply aggregation strategy for each outcome
            for outcome, odds_list in outcome_odds.items():
                aggregated_odds.append(await self._aggregate_outcome_odds(odds_list, strategy))
            
            # Calculate consensus odds and confidence
            consensus_odds = {}
            confidence_scores = []
            
            for outcome_odds_obj in aggregated_odds:
                consensus_odds[outcome_odds_obj.outcome] = outcome_odds_obj.odds
                confidence_scores.append(outcome_odds_obj.source_reliability)
            
            avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
            
            # Assess data quality
            expected_outcomes = set(o.outcome for o in aggregated_odds)
            quality_assessment = self.quality_assessor.assess_odds_quality(aggregated_odds, expected_outcomes)
            conflicts = self.quality_assessor.detect_conflicts(aggregated_odds)
            
            # Create aggregated market
            aggregated_market = MarketData(
                sport=base_market.sport,
                event_name=base_market.event_name,
                event_id=base_market.event_id,
                market_type=base_market.market_type,
                market_id=base_market.market_id,
                start_time=base_market.start_time,
                participants=base_market.participants,
                odds=aggregated_odds,
                consensus_odds=consensus_odds,
                confidence_score=avg_confidence,
                data_freshness_minutes=0.0,  # Will be calculated
                source_count=len(market_data_list),
                conflicting_sources=conflicts,
                aggregation_strategy=strategy,
                league=base_market.league
            )
            
            # Calculate data freshness
            now = datetime.utcnow()
            freshness_scores = []
            for odds in aggregated_odds:
                if odds.last_updated:
                    age_minutes = (now - odds.last_updated).total_seconds() / 60
                    freshness_scores.append(max(0, 1 - (age_minutes / 60)))  # Decay over 1 hour
            aggregated_market.data_freshness_minutes = statistics.mean(freshness_scores) * 60 if freshness_scores else 60
            
            return aggregated_market
        
        except Exception as e:
            self.logger.error(f"Market aggregation failed: {e}")
            return None
    
    async def _aggregate_outcome_odds(self, 
                                    odds_list: List[MarketOdds], 
                                    strategy: AggregationStrategy) -> MarketOdds:
        """Aggregate odds for a specific outcome using strategy."""
        if not odds_list:
            raise ValueError("Cannot aggregate empty odds list")
        
        if len(odds_list) == 1:
            return odds_list[0]
        
        if strategy == AggregationStrategy.PRIORITY_BASED:
            # Use highest priority source (highest reliability)
            return max(odds_list, key=lambda x: x.source_reliability)
        
        elif strategy == AggregationStrategy.WEIGHTED_AVERAGE:
            # Calculate weighted average by source reliability
            total_weight = sum(odds.source_reliability for odds in odds_list)
            if total_weight > 0:
                weighted_odds = sum(odds.odds * odds.source_reliability for odds in odds_list) / total_weight
                avg_reliability = total_weight / len(odds_list)
                
                return MarketOdds(
                    bookmaker="aggregated",
                    outcome=odds_list[0].outcome,
                    odds=weighted_odds,
                    implied_probability=self.normalizer.calculate_implied_probability(weighted_odds),
                    source_reliability=avg_reliability,
                    data_quality=DataQualityLevel.GOOD
                )
        
        elif strategy == AggregationStrategy.MOST_RECENT:
            # Use most recent data
            return max(odds_list, key=lambda x: x.last_updated or datetime.min)
        
        elif strategy == AggregationStrategy.CONSENSUS:
            # Use median to reduce outlier impact
            odds_values = [odds.odds for odds in odds_list if odds.odds > 0]
            if odds_values:
                median_odds = statistics.median(odds_values)
                avg_reliability = statistics.mean([odds.source_reliability for odds in odds_list])
                
                return MarketOdds(
                    bookmaker="consensus",
                    outcome=odds_list[0].outcome,
                    odds=median_odds,
                    implied_probability=self.normalizer.calculate_implied_probability(median_odds),
                    source_reliability=avg_reliability,
                    data_quality=DataQualityLevel.GOOD
                )
        
        # Default to first odds (should not reach here)
        return odds_list[0]
    
    def _calculate_overall_quality(self, markets: Dict[str, MarketData]) -> float:
        """Calculate overall quality score for event."""
        if not markets:
            return 0.0
        
        quality_scores = [market.confidence_score for market in markets.values()]
        return statistics.mean(quality_scores) / 100.0  # Normalize to 0-1
    
    def _calculate_completeness(self, markets: Dict[str, MarketData]) -> float:
        """Calculate data completeness percentage."""
        if not markets:
            return 0.0
        
        completeness_scores = []
        for market in markets.values():
            # Check if market has odds for all major outcomes
            expected_outcomes = len(set(odds.outcome for odds in market.odds))
            actual_outcomes = len(market.odds)
            completeness = min(1.0, actual_outcomes / max(1, expected_outcomes))
            completeness_scores.append(completeness)
        
        return statistics.mean(completeness_scores)
    
    def _calculate_source_coverage(self, market_data_list: List[MarketData]) -> float:
        """Calculate source coverage percentage."""
        if not market_data_list:
            return 0.0
        
        # Count unique sources
        sources = set(market.bookmaker for market in market_data_list)
        total_possible_sources = len(set(m.bookmaker for m in market_data_list))  # In real implementation, this would be total configured sources
        
        return min(1.0, len(sources) / max(1, total_possible_sources))
    
    def _get_bookmaker_reliability(self, bookmaker_name: str) -> float:
        """Get reliability score for bookmaker (would integrate with health monitoring)."""
        # Mock implementation - would integrate with bookmaker manager health metrics
        return 85.0
    
    def _generate_event_id(self, event_name: str, sport: str) -> str:
        """Generate unique event ID from name and sport."""
        content = f"{event_name}_{sport}_{datetime.utcnow().strftime('%Y%m%d')}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _generate_market_id(self, event_id: str, market_type: str) -> str:
        """Generate unique market ID."""
        content = f"{event_id}_{market_type}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _parse_event_time(self, time_data: Any) -> datetime:
        """Parse event time from various formats."""
        if isinstance(time_data, datetime):
            return time_data
        elif isinstance(time_data, str):
            try:
                # Try various datetime formats
                formats = [
                    '%Y-%m-%dT%H:%M:%SZ',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S',
                    '%Y-%m-%d'
                ]
                for fmt in formats:
                    try:
                        return datetime.strptime(time_data, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # Default to current time if parsing fails
        return datetime.utcnow()
    
    def _extract_participants(self, event_data: Dict[str, Any]) -> List[str]:
        """Extract participant names from event data."""
        participants = []
        
        # Common field names for participants
        participant_fields = ['participants', 'teams', 'players', 'competitors']
        
        for field in participant_fields:
            if field in event_data:
                data = event_data[field]
                if isinstance(data, list):
                    participants.extend(str(item) for item in data)
                elif isinstance(data, dict):
                    participants.extend(str(item) for item in data.values())
        
        # If no participants found, try to extract from event name
        if not participants:
            event_name = event_data.get('name', event_data.get('event_name', ''))
            # Simple extraction: split by common separators
            if ' vs ' in event_name:
                participants = event_name.split(' vs ')
            elif ' v ' in event_name:
                participants = event_name.split(' v ')
            elif ' - ' in event_name:
                participants = event_name.split(' - ')
        
        return participants[:2]  # Return max 2 participants
    
    async def get_event_data(self, event_id: str) -> Optional[AggregatedEvent]:
        """Get cached event data."""
        return self.active_aggregations.get(event_id)
    
    async def get_sport_events(self, sport: Sport) -> Dict[str, AggregatedEvent]:
        """Get all active events for a sport."""
        return {event_id: event for event_id, event in self.active_aggregations.items() 
                if event.sport == sport}
    
    def get_aggregation_statistics(self) -> AggregationStats:
        """Get current aggregation statistics."""
        return self.aggregation_stats
    
    def add_aggregation_complete_callback(self, callback):
        """Add callback for when aggregation completes."""
        self.aggregation_complete_callbacks.append(callback)
    
    async def shutdown(self):
        """Shutdown the data aggregator."""
        self.logger.info("Data aggregator shutdown initiated")
        # Cancel any ongoing aggregations
        self.active_aggregations.clear()
        self.logger.info("Data aggregator shutdown complete")


# Global instance
_data_aggregator: Optional[DataAggregator] = None


async def get_data_aggregator() -> DataAggregator:
    """Get global data aggregator instance."""
    global _data_aggregator
    
    if _data_aggregator is None:
        bookmaker_manager = await get_bookmaker_manager()
        _data_aggregator = DataAggregator(bookmaker_manager)
        await _data_aggregator.initialize()
    
    return _data_aggregator


async def shutdown_data_aggregator():
    """Shutdown global data aggregator."""
    global _data_aggregator
    
    if _data_aggregator:
        await _data_aggregator.shutdown()
        _data_aggregator = None