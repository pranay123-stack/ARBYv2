# Intelligent Opportunity Ranking and Filtering System

A comprehensive, high-performance system for ranking, filtering, and managing arbitrage opportunities in the ARBitech framework. The system provides intelligent prioritization and quality assessment to optimize arbitrage trading decisions.

## Overview

The system consists of four main components:

1. **OpportunityRanker** - Advanced ranking with configurable scoring algorithms
2. **FilteringEngine** - Multi-dimensional filtering with complex rule support  
3. **PriorityQueue** - High-performance queue management with multiple strategies
4. **QualityScorer** - Comprehensive quality assessment across multiple dimensions

## Key Features

### 🎯 Intelligent Ranking
- **Configurable Scoring Algorithms** with weighted dimensions (profit, risk, liquidity, time, execution)
- **Multiple Ranking Strategies** (profit-first, risk-first, speed-first, balanced, liquidity-first, time-sensitive)
- **Real-time Ranking Updates** as market conditions change
- **Detailed Scoring Explanations** for each opportunity
- **Opportunity Aging** with time decay support
- **Batch Processing** for large opportunity sets
- **Performance Optimization** with caching and parallel processing

### 🔍 Advanced Filtering
- **Multi-dimensional Filtering** for profit margins, bookmakers, markets, sports, and risk levels
- **Complex Filter Combinations** with AND/OR logic
- **Rule-based Filtering** with flexible operators (=, >, <, in, regex, etc.)
- **Custom Filter Support** for user-defined logic
- **High-performance Processing** optimized for high-frequency operations
- **Filter Group Management** for complex filter configurations

### 📊 Priority Queue Management
- **Multiple Priority Strategies** (FIFO, LIFO, highest score, lowest risk, most profitable, urgent-first)
- **Real-time Priority Updates** with efficient heap operations
- **Batch Processing** for improved throughput
- **Thread-safe Operations** with concurrent access support
- **Automatic Eviction** of expired entries
- **Performance Metrics** and monitoring
- **Queue Management** (pause, resume, drain, clear)

### ⭐ Quality Assessment
- **Multi-dimensional Quality Scoring** (reliability, profit stability, execution complexity, market conditions, historical performance)
- **Quality Level Classification** (excellent, very good, good, fair, poor, very poor)
- **Detailed Quality Explanations** with confidence levels
- **Performance Recommendations** based on quality analysis
- **Historical Performance Tracking** with success rate analysis
- **Parallel Batch Assessment** for multiple opportunities

## Quick Start

### Basic Usage

```python
from detection import (
    OpportunityRanker, FilteringEngine, PriorityQueue, QualityScorer,
    RankingStrategy, create_profit_filter, create_risk_filter
)
from storage.models import ArbitrageOpportunity

# Create components
ranker = OpportunityRanker()
filter_engine = FilteringEngine()
queue = PriorityQueue()
quality_scorer = QualityScorer()

# Add filters
filter_engine.add_filter(create_profit_filter(min_margin=Decimal("0.02")))
filter_engine.add_filter(create_risk_filter([RiskTier.TIER_A, RiskTier.TIER_B]))

# Filter opportunities
filtered_ops = filter_engine.filter_opportunities(opportunities)

# Rank opportunities
ranked_ops = ranker.rank_opportunities(filtered_ops, strategy=RankingStrategy.PROFIT_FIRST)

# Assess quality
assessments = [quality_scorer.assess_quality(opp) for opp in ranked_ops]

# Add to priority queue
for score in ranked_ops:
    if score.overall_score > 70:  # Only high-scoring opportunities
        queue.enqueue(opportunity, priority_score=score.overall_score)

# Process queue
while True:
    result = queue.dequeue(timeout_seconds=5.0)
    if not result:
        break
    
    opp_id, metadata = result
    # Process opportunity...
```

### Advanced Configuration

```python
# Custom ranking weights
custom_weights = RankingWeights(
    profit_score=0.4,     # 40% weight on profit
    risk_score=0.3,       # 30% weight on risk
    liquidity_score=0.15, # 15% weight on liquidity
    time_score=0.1,       # 10% weight on time
    execution_score=0.05  # 5% weight on execution
)

ranker = OpportunityRanker(weights=custom_weights, strategy=RankingStrategy.PROFIT_FIRST)

# Custom filtering rules
from detection.filtering_engine import FilterRule, FilterOperator, FilterGroup

# Create complex filter group
stake_rule = FilterRule(
    field="total_stake",
    operator=FilterOperator.BETWEEN,
    value=[Decimal("100"), Decimal("1000")]
)

sport_rule = FilterRule(
    field="sport",
    operator=FilterOperator.IN,
    value=[Sport.FOOTBALL, Sport.BASKETBALL],
    negate=True  # Exclude these sports
)

filter_group = FilterGroup(
    rules=[stake_rule, sport_rule],
    logic_operator="AND"
)

filter_engine.add_filter_group(filter_group)

# Batch processing
results = queue.batch_process(
    processor_func=process_opportunity,
    batch_size=50,
    timeout_seconds=30.0
)

print(f"Processed {results.processed_count} opportunities in {results.processing_time_ms:.2f}ms")
```

## Component Details

### OpportunityRanker

The core ranking system that scores opportunities based on multiple dimensions:

#### Scoring Dimensions:
- **Profit Score** (35% default): Based on profit margin, amount, ROI, and stability
- **Risk Score** (25% default): Based on risk tier, liquidity verification, odds freshness
- **Liquidity Score** (15% default): Based on liquidity ratios, stake size, leg complexity  
- **Time Score** (15% default): Based on discovery age, event urgency, expiration time
- **Execution Score** (10% default): Based on complexity, market type, stake distribution

#### Ranking Strategies:
- `PROFIT_FIRST`: Emphasizes highest profit opportunities
- `RISK_FIRST`: Prioritizes lowest risk opportunities
- `SPEED_FIRST`: Focuses on time-sensitive opportunities
- `LIQUIDITY_FIRST`: Prioritizes highly liquid opportunities
- `TIME_SENSITIVE`: Optimizes for immediate execution
- `BALANCED`: Equal weight across all dimensions

### FilteringEngine

Flexible filtering system supporting multiple filter types:

#### Built-in Filters:
- `ProfitMarginFilter`: Filter by profit margin ranges
- `RiskTierFilter`: Filter by risk assessment tiers
- `SportFilter`: Filter by sport types
- `BookmakerFilter`: Filter by bookmaker combinations
- `MarketTypeFilter`: Filter by market types with pattern matching
- `StakeAmountFilter`: Filter by stake amount ranges
- `TimeFilter`: Filter by time-based criteria
- `LiquidityFilter`: Filter by liquidity verification status
- `CustomFilter`: User-defined filtering logic

#### Filter Operators:
- Comparison: `=`, `!=`, `>`, `>=`, `<`, `<=`
- Collection: `in`, `not_in`
- Text: `contains`, `not_contains`, `starts_with`, `ends_with`, `regex`
- Range: `between`

### PriorityQueue

High-performance priority queue with multiple strategies:

#### Queue Strategies:
- `HIGHEST_SCORE`: Process highest priority scores first
- `LOWEST_RISK`: Prioritize lowest risk opportunities
- `MOST_PROFITABLE`: Focus on profit potential
- `URGENT_FIRST`: Handle time-sensitive opportunities first
- `FIFO`/`LIFO`: Traditional queue order
- `CUSTOM`: User-defined priority logic

#### Features:
- Thread-safe operations with locks
- Automatic eviction of expired entries
- Batch processing for improved performance
- Comprehensive metrics and monitoring
- Callback support for custom processing

### QualityScorer

Comprehensive quality assessment across five dimensions:

#### Quality Dimensions:
1. **Reliability Score**: Bookmaker trust, risk tier, liquidity verification
2. **Profit Stability Score**: Margin consistency, distribution balance, risk-adjusted returns
3. **Execution Complexity Score**: Leg count, market type, stake size, time pressure
4. **Market Conditions Score**: Sport popularity, market liquidity, competition level
5. **Historical Performance Score**: Sport, bookmaker, market type, and risk tier history

#### Quality Levels:
- `EXCELLENT` (85+): Top-tier opportunities with minimal risk
- `VERY_GOOD` (75-84): High-quality opportunities with good fundamentals
- `GOOD` (65-74): Solid opportunities with acceptable risk levels
- `FAIR` (50-64): Average opportunities with some concerns
- `POOR` (35-49): Below-average opportunities with elevated risk
- `VERY_POOR` (<35): Poor quality opportunities requiring caution

## Performance Optimization

### Thread Safety
All components are thread-safe and support concurrent access patterns using appropriate locking mechanisms.

### Caching
The ranking system includes intelligent caching to avoid recomputing scores for identical opportunities.

### Batch Processing
Efficient batch operations for processing large numbers of opportunities in parallel.

### Memory Management
Automatic cleanup of expired entries and memory-efficient data structures.

### Monitoring
Comprehensive performance metrics and monitoring for all components.

## Integration with Existing Models

The system integrates seamlessly with the existing `ArbitrageOpportunity` model from `storage.models`:

```python
from storage.models import ArbitrageOpportunity, ArbitrageLeg, RiskTier, Sport

# All components work with the standard ArbitrageOpportunity model
opportunity = ArbitrageOpportunity(
    sport=Sport.FOOTBALL,
    event_name="Team A vs Team B",
    event_date=datetime.utcnow() + timedelta(hours=2),
    market_type="match_winner",
    legs=[...],  # List of ArbitrageLeg objects
    total_stake=Decimal("1000.00"),
    profit_margin=Decimal("0.025"),
    profit_amount=Decimal("25.00"),
    risk_tier=RiskTier.TIER_A,
    # ... other fields
)

# Components can directly process these opportunities
ranked_opportunities = ranker.rank_opportunities([opportunity])
quality_assessment = quality_scorer.assess_quality(opportunity)
```

## Example Workflow

```python
def comprehensive_opportunity_processing(opportunities: List[ArbitrageOpportunity]):
    \"\"\"Complete workflow for processing opportunities through all systems.\"\"\"
    
    # 1. Filter opportunities
    filter_engine = FilteringEngine()
    filter_engine.add_filter(create_profit_filter(min_margin=Decimal("0.015")))
    filter_engine.add_filter(create_risk_filter([RiskTier.TIER_A, RiskTier.TIER_B]))
    filter_engine.add_filter(create_liquidity_filter(must_be_checked=True))
    
    filtered_ops = filter_engine.filter_opportunities(opportunities)
    
    # 2. Rank opportunities
    ranker = OpportunityRanker(strategy=RankingStrategy.BALANCED)
    ranked_ops = ranker.rank_opportunities(filtered_ops)
    
    # 3. Assess quality
    quality_scorer = QualityScorer()
    quality_results = []
    
    for score in ranked_ops:
        opp = find_opportunity_by_id(score.opportunity_id)
        assessment = quality_scorer.assess_quality(opp)
        quality_results.append(assessment)
    
    # 4. Add high-quality opportunities to queue
    queue = PriorityQueue()
    for score in ranked_ops:
        assessment = quality_results_by_id[score.opportunity_id]
        if assessment.quality_level in [QualityLevel.EXCELLENT, QualityLevel.VERY_GOOD]:
            opp = find_opportunity_by_id(score.opportunity_id)
            queue.enqueue(opp, priority_score=score.overall_score)
    
    # 5. Process queue
    processed_count = 0
    while True:
        result = queue.dequeue(timeout_seconds=10.0)
        if not result:
            break
        
        opp_id, metadata = result
        process_opportunity(opp_id)
        processed_count += 1
    
    return {
        'filtered_count': len(filtered_ops),
        'ranked_count': len(ranked_ops),
        'processed_count': processed_count,
        'average_quality': sum(a.overall_quality_score for a in quality_results) / len(quality_results)
    }
```

## Testing and Demo

Run the comprehensive demo to see all components in action:

```bash
python -m detection.demo_ranking_system
```

The demo showcases:
- Opportunity ranking with different strategies
- Multi-dimensional filtering
- Priority queue operations with various strategies  
- Quality assessment across all dimensions
- Integrated system workflow

## Performance Considerations

### For High-Frequency Trading:
1. Use batch processing for large opportunity sets
2. Enable caching in the ranker
3. Set appropriate queue sizes and eviction policies
4. Use parallel processing for quality assessment
5. Monitor performance metrics regularly

### Memory Usage:
- Queue size limits prevent memory overflow
- Automatic cleanup of expired entries
- Efficient data structures minimize memory footprint
- Cache management prevents unbounded growth

### Scalability:
- Thread-safe operations support multiple concurrent users
- Batch processing improves throughput for large datasets
- Caching reduces computational overhead
- Efficient algorithms scale with data size

## Future Enhancements

Potential improvements and extensions:

1. **Machine Learning Integration**: Use ML models for more sophisticated scoring
2. **Real-time Market Data**: Integrate live market feeds for dynamic scoring
3. **Advanced Risk Modeling**: Enhanced risk assessment using historical data
4. **Custom Scoring Plugins**: Support for user-defined scoring algorithms
5. **Distributed Processing**: Scale across multiple machines for very large datasets
6. **Performance Optimization**: Further optimizations for ultra-high-frequency scenarios
7. **Advanced Analytics**: Deeper insights and reporting capabilities
8. **A/B Testing Framework**: Test different ranking strategies in production

# Opportunity Scanner - VLM-Powered Arbitrage Detection System

A sophisticated, production-ready opportunity scanner that uses Vision Language Model (VLM) infrastructure to continuously scan betting interfaces for arbitrage opportunities in real-time.

## Overview

The Opportunity Scanner extends the detection system with comprehensive scanning capabilities:

1. **OpportunityScanner** - Main coordinator class that orchestrates all scanning operations
2. **ScannerEngine** - Multi-threaded core engine with priority-based scanning
3. **MarketMonitor** - Real-time market state tracking and arbitrage detection
4. **ScanScheduler** - Advanced scheduling system with multiple scheduling patterns

## Key Features

### 🚀 Real-time Scanning
- **Continuous Monitoring** of multiple bookmaker interfaces using VLM
- **Concurrent Scanning** with configurable thread pools and priority queues
- **Priority-based Scheduling** with automatic escalation and resource management
- **Automatic Retry Logic** with exponential backoff and error recovery

### 🎯 Arbitrage Detection
- **Real-time Odds Comparison** across multiple bookmakers
- **Automated Profit Calculation** with configurable thresholds
- **Risk Assessment** with tier-based filtering
- **Opportunity Validation** with confidence scoring

### 📅 Advanced Scheduling
- **Interval-based**: Fixed time intervals between scans
- **Cron-based**: Flexible cron expression scheduling
- **Priority-based**: Resource-aware priority scheduling  
- **Adaptive**: Dynamic adjustment based on market conditions

### 🔍 Comprehensive Monitoring
- **Performance Metrics** collection and analysis
- **Health Checks** for all system components
- **Event-driven Logging** and notifications
- **Real-time Status** monitoring and reporting

## Quick Start

### Basic Usage

```python
import asyncio
from arbitech.detection import create_scanner, Sport

async def basic_scanner_example():
    # Create scanner
    scanner = await create_scanner()
    
    # Add event handlers
    def handle_opportunity(event):
        print(f"Found opportunity: {event.opportunity_id}")
    
    scanner.add_event_handler(handle_opportunity)
    
    # Start scanning
    await scanner.start_scanning([
        Sport.FOOTBALL,
        Sport.TENNIS,
        Sport.BASKETBALL
    ])
    
    # Monitor for opportunities
    opportunities = scanner.get_opportunities(limit=10)
    for opp in opportunities:
        print(f"Opportunity: {float(opp.profit_margin)*100:.2f}% margin")
    
    # Stop scanning
    await scanner.stop_scanning()

# Run example
asyncio.run(basic_scanner_example())
```

### Advanced Configuration

```python
import asyncio
from arbitech.detection import create_scanner, Sport, ScanPriority
from decimal import Decimal

async def advanced_scanner_example():
    # Custom configuration
    config = {
        'scanner': {
            'max_concurrent_scans': 10,
            'min_profit_margin': 1.5,  # 1.5%
            'retry_failed_scans': True,
            'max_retries': 3
        },
        'vlm': {
            'timeout': 30,
            'rate_limit_per_minute': 60
        },
        'market_monitor': {
            'max_odds_age_seconds': 180,
            'opportunity_expiry_minutes': 15
        }
    }
    
    # Create scanner with custom config
    scanner = await create_scanner(config)
    
    # Add comprehensive event handlers
    class ScannerEventHandler:
        def __init__(self):
            self.opportunity_count = 0
            self.error_count = 0
        
        async def handle_scanner_event(self, event):
            if event.event_type == ScannerEventType.OPPORTUNITY_FOUND:
                self.opportunity_count += 1
                print(f"🎯 New opportunity #{self.opportunity_count}")
            elif event.event_type == ScannerEventType.VLM_ERROR:
                self.error_count += 1
                print(f"⚠️ VLM Error: {event.error_message}")
    
    handler = ScannerEventHandler()
    scanner.add_event_handler(handler.handle_scanner_event)
    
    # Start scanning
    await scanner.start_scanning()
    
    return scanner

# Use the scanner
scanner = asyncio.run(advanced_scanner_example())
```

## Component Details

### OpportunityScanner

The main coordinator that manages the entire scanning process.

#### Key Methods:
- `start_scanning(sports=None, custom_schedule=None)` - Start scanning operations
- `stop_scanning()` - Gracefully stop all scanning
- `scan_bookmaker(bookmaker, sport, image_data, ...)` - Scan specific bookmaker
- `get_status()` - Get comprehensive scanner status
- `get_opportunities(filters)` - Get discovered arbitrage opportunities
- `add_event_handler(handler)` - Add custom event handlers

#### Usage Example:
```python
# Get current scanner status
status = scanner.get_status()
print(f"Status: {status['status']}")
print(f"Active scans: {status['active_scans']}")
print(f"Opportunities found: {status['metrics']['opportunities_found']}")

# Get high-quality opportunities
opportunities = scanner.get_opportunities(
    min_profit_margin=Decimal('2.0'),
    sport=Sport.FOOTBALL,
    risk_tier=RiskTier.TIER_A,
    limit=10
)

for opp in opportunities:
    print(f"{opp.event_name}: {float(opp.profit_margin)*100:.2f}% margin")
```

### ScannerEngine

Multi-threaded engine that handles scan execution with fault tolerance.

#### Features:
- **Priority-based Queue** with configurable thread pools
- **Circuit Breaker Pattern** for fault tolerance
- **Automatic Retry Logic** with exponential backoff
- **Performance Metrics** and monitoring
- **Resource Management** with load balancing

#### Usage Example:
```python
from arbitech.detection import ScannerEngine, ScanType, ScanPriority

# Create engine with custom settings
engine = ScannerEngine({
    'max_concurrent_scans': 5,
    'retry_failed_scans': True,
    'max_retries': 2
})

await engine.start()

# Add scan task
task_id = engine.add_scan_task(
    scan_type=ScanType.BOOKMAKER_SCAN,
    bookmaker="bet365",
    sport=Sport.FOOTBALL,
    image_data="https://example.com/bet365_football.png",
    priority=ScanPriority.HIGH
)

# Monitor engine performance
metrics = engine.get_engine_metrics()
print(f"Success rate: {metrics['success_rate']:.2%}")
print(f"Throughput: {metrics['throughput_scans_per_minute']:.1f} scans/min")

await engine.stop()
```

### MarketMonitor

Real-time market state tracking and arbitrage detection system.

#### Features:
- **Real-time Odds Tracking** across multiple bookmakers
- **Automated Arbitrage Detection** with configurable algorithms
- **Market State Persistence** with expiration handling
- **Event-driven Updates** for immediate opportunity detection
- **Performance Optimization** for large-scale markets

#### Usage Example:
```python
from arbitech.detection import MarketMonitor, create_market_monitor

# Create monitor
monitor = await create_market_monitor({
    'max_odds_age_seconds': 120,
    'min_confidence': 0.7
})

await monitor.start()

# Update market odds
odds_data = {
    'bookmaker': 'bet365',
    'sport': Sport.FOOTBALL,
    'market_type': 'match_winner',
    'odds': {'home': Decimal('2.1'), 'away': Decimal('1.8')},
    'confidence': 0.9
}

await monitor.update_market_odds(odds_data)

# Find arbitrage opportunities
opportunities = await monitor.find_arbitrage_opportunities(
    min_profit_margin=Decimal('1.0')
)

# Get market state summary
summary = monitor.get_state_summary()
print(f"Active markets: {summary['total_markets']}")
print(f"Average confidence: {summary['average_confidence']:.2%}")

await monitor.stop()
```

### ScanScheduler

Advanced scheduling system with multiple scheduling patterns and adaptive behavior.

#### Scheduling Types:
- **Interval-based**: Fixed time intervals between scans
- **Cron-based**: Flexible cron expression scheduling
- **Event-driven**: Triggered by external events
- **Priority-based**: Resource-aware priority scheduling
- **Adaptive**: Dynamic adjustment based on market conditions

#### Usage Example:
```python
from arbitech.detection import (
    ScanScheduler, ScheduleConfig, ScheduleType, ScanPriority,
    create_quick_scan_schedule, create_cron_scan_schedule
)

# Create scheduler
scheduler = await create_scheduler({
    'adaptive_scheduling': True,
    'resource_monitoring': True
})

await scheduler.start()

# Create interval-based schedule
schedule = ScheduleConfig(
    name="Regular Football Scans",
    schedule_type=ScheduleType.INTERVAL,
    interval_seconds=60,
    bookmakers=["bet365", "william_hill"],
    sports=["football"],
    priority=ScanPriority.NORMAL
)

schedule_id = scheduler.create_schedule(schedule)

# Create quick scan for high-priority bookmaker
quick_schedule = create_quick_scan_schedule(
    bookmaker="pinnacle",
    sport="tennis",
    interval_seconds=30,
    priority=ScanPriority.HIGH
)

quick_id = scheduler.create_schedule(quick_schedule)

# Create cron-based schedule for business hours
cron_schedule = create_cron_scan_schedule(
    name="Business Hours Scanning",
    bookmakers=["bet365", "william_hill"],
    sports=["basketball"],
    cron_expression="*/15 9-17 * * *",  # Every 15 minutes, 9 AM to 5 PM
    priority=ScanPriority.NORMAL
)

cron_id = scheduler.create_schedule(cron_schedule)

# Monitor scheduler performance
metrics = scheduler.get_scheduler_metrics()
print(f"Active schedules: {metrics['active_schedules']}")
print(f"Resource adjustments: {metrics['resource_adjustments']}")

await scheduler.stop()
```

## Event Handling

Comprehensive event system for monitoring and integration:

```python
from arbitech.detection import ScannerEventType, MarketEventType

class ComprehensiveEventHandler:
    async def handle_scanner_event(self, event):
        if event.event_type == ScannerEventType.OPPORTUNITY_FOUND:
            print(f"🎯 New opportunity: {event.opportunity_id}")
            # Handle new opportunity discovery
            
        elif event.event_type == ScannerEventType.VLM_ERROR:
            print(f"⚠️ VLM Error: {event.error_message}")
            # Handle VLM extraction errors
            
        elif event.event_type == ScannerEventType.BOOKMAKER_UNAVAILABLE:
            print(f"❌ Bookmaker unavailable: {event.bookmaker}")
            # Handle bookmaker connectivity issues
    
    async def handle_market_event(self, event):
        if event.event_type == MarketEventType.ARBITRAGE_DETECTED:
            profit_margin = event.data.get('profit_margin', 0)
            print(f"💰 Arbitrage detected: {profit_margin:.2%} margin")
            # Handle arbitrage opportunity detection
            
        elif event.event_type == MarketEventType.OPPORTUNITY_EXPIRED:
            print(f"⏰ Opportunity expired: {event.opportunity_id}")
            # Handle opportunity expiration

# Register handlers
handler = ComprehensiveEventHandler()
scanner.add_event_handler(handler.handle_scanner_event)
monitor.add_event_handler(handler.handle_market_event)
```

## Performance Monitoring

### Comprehensive Metrics

```python
# Scanner metrics
scanner_metrics = scanner.get_status()['metrics']
print(f"Total scans: {scanner_metrics['total_scans']}")
print(f"Success rate: {scanner_metrics['success_rate']:.2%}")
print(f"VLM API calls: {scanner_metrics['vlm_api_calls']}")
print(f"Opportunities found: {scanner_metrics['opportunities_found']}")

# Engine metrics
engine_metrics = scanner.scanner_engine.get_engine_metrics()
print(f"Throughput: {engine_metrics['throughput_scans_per_minute']:.1f} scans/min")
print(f"Queue utilization: {engine_metrics['utilization']:.2%}")

# Market metrics
market_metrics = scanner.market_monitor.get_state_summary()
print(f"Active bookmakers: {market_metrics['active_bookmakers']}")
print(f"Average confidence: {market_metrics['average_confidence']:.2%}")

# Scheduler metrics
scheduler_metrics = scanner.scan_scheduler.get_scheduler_metrics()
print(f"Scheduled scans: {scheduler_metrics['total_scheduled_scans']}")
print(f"Resource adjustments: {scheduler_metrics['resource_adjustments']}")
```

### Health Checks

```python
async def comprehensive_health_check(scanner):
    checks = {
        'vlm_extractor': await scanner.vlm_extractor.health_check(),
        'scanner_engine': await scanner.scanner_engine.health_check(),
        'market_monitor': len(scanner.market_monitor.current_odds) >= 0
    }
    
    for component, healthy in checks.items():
        status = "✅ Healthy" if healthy else "❌ Unhealthy"
        print(f"{component}: {status}")
    
    overall_healthy = all(checks.values())
    print(f"System health: {'✅ Good' if overall_healthy else '⚠️ Issues detected'}")
    
    return overall_healthy

# Run health check
healthy = await comprehensive_health_check(scanner)
```

## Configuration

### Scanner Configuration
```yaml
scanner:
  max_concurrent_scans: 10          # Maximum concurrent scans
  min_profit_margin: 2.0            # Minimum profit margin (%)
  max_scan_age_seconds: 300         # Maximum age of scan data
  retry_failed_scans: true          # Enable retry for failed scans
  max_retries: 3                    # Maximum retry attempts
```

### VLM Integration
```yaml
vlm:
  timeout: 30                       # VLM API timeout (seconds)
  retry_attempts: 3                 # Retry attempts
  rate_limit_per_minute: 60         # API rate limit
  min_confidence: 0.7               # Minimum extraction confidence
```

### Market Monitor
```yaml
market_monitor:
  max_odds_age_seconds: 180         # Maximum age of odds data
  min_confidence: 0.7               # Minimum confidence threshold
  opportunity_expiry_minutes: 15    # Opportunity expiry time
```

### Scheduler
```yaml
scheduler:
  max_concurrent_schedules: 100     # Maximum concurrent schedules
  adaptive_scheduling: true         # Enable adaptive scheduling
  resource_monitoring: true         # Enable resource monitoring
  default_interval_seconds: 60      # Default scan interval
```

## Example Applications

### 1. Continuous Monitoring Service
```python
class ArbitrageMonitoringService:
    def __init__(self):
        self.scanner = None
        self.running = False
    
    async def start(self):
        self.scanner = await create_scanner()
        self.scanner.add_event_handler(self.handle_opportunity_event)
        
        await self.scanner.start_scanning()
        self.running = True
        
        # Run monitoring loop
        while self.running:
            await self.process_opportunities()
            await asyncio.sleep(60)  # Check every minute
    
    async def stop(self):
        self.running = False
        if self.scanner:
            await self.scanner.stop_scanning()
    
    async def handle_opportunity_event(self, event):
        if event.event_type == ScannerEventType.OPPORTUNITY_FOUND:
            # Process new opportunity
            await self.execute_arbitrage(event.opportunity_id)
    
    async def process_opportunities(self):
        # Get and process high-quality opportunities
        opportunities = self.scanner.get_opportunities(
            min_profit_margin=Decimal('2.0'),
            limit=10
        )
        
        for opp in opportunities:
            if opp.risk_tier == RiskTier.TIER_A:
                await self.execute_arbitrage(opp.id)

# Usage
service = ArbitrageMonitoringService()
await service.start()
```

### 2. Scheduled Scanning Service
```python
class ScheduledScanningService:
    def __init__(self):
        self.scheduler = None
    
    async def setup_comprehensive_schedules(self):
        self.scheduler = await create_scheduler()
        
        # High-frequency scans for popular sports
        football_schedule = create_quick_scan_schedule(
            bookmaker="bet365",
            sport="football",
            interval_seconds=30,
            priority=ScanPriority.HIGH
        )
        self.scheduler.create_schedule(football_schedule)
        
        # Comprehensive scans for all sports
        comprehensive_schedule = ScheduleConfig(
            name="Comprehensive All-Sports",
            schedule_type=ScheduleType.INTERVAL,
            interval_seconds=300,  # 5 minutes
            bookmakers=["bet365", "william_hill", "ladbrokes", "pinnacle"],
            sports=["football", "tennis", "basketball", "hockey"],
            market_types=["match_winner", "over_under"],
            priority=ScanPriority.NORMAL,
            max_concurrent=5
        )
        self.scheduler.create_schedule(comprehensive_schedule)
        
        # Business hours premium scanning
        business_schedule = create_cron_scan_schedule(
            name="Premium Business Hours",
            bookmakers=["pinnacle", "betfair"],  # Premium bookmakers
            sports=["football", "tennis", "basketball"],
            cron_expression="*/10 8-22 * * *",  # Every 10 minutes during active hours
            priority=ScanPriority.HIGH
        )
        self.scheduler.create_schedule(business_schedule)
        
        await self.scheduler.start()

# Usage
service = ScheduledScanningService()
await service.setup_comprehensive_schedules()
```

## Error Handling & Recovery

The system includes comprehensive error handling and automatic recovery:

### Circuit Breakers
- **VLM API Protection**: Prevents overwhelming the VLM service
- **Engine Failure Tracking**: Monitors and responds to systematic failures
- **Automatic Recovery**: Self-healing capabilities with gradual restoration

### Retry Logic
- **Exponential Backoff**: Smart retry timing based on error type
- **Configurable Limits**: Adjustable retry attempts per component
- **Error Classification**: Different retry strategies for different error types

### Error Recovery Example
```python
class RobustScanner:
    async def scanning_with_recovery(self):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Perform scan operation
                result = await self.scanner.scan_bookmaker(...)
                return result
                
            except Exception as e:
                if attempt == max_attempts - 1:
                    # Final attempt failed
                    await self.handle_final_failure(e)
                    raise
                
                # Calculate backoff delay
                delay = 2 ** attempt
                print(f"Scan failed, retrying in {delay}s (attempt {attempt + 1}/{max_attempts})")
                await asyncio.sleep(delay)
```

## Performance Optimization

### Resource Management
```python
import psutil

async def resource_aware_scanning(scanner):
    while True:
        # Check resource usage
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 80 or memory_percent > 80:
            print("⚠️ High resource usage detected")
            # Reduce scan frequency
            await scanner.scan_scheduler.scale_down_scheduling()
        
        await asyncio.sleep(30)  # Check every 30 seconds
```

### Event-driven Processing
```python
# Use async event handlers for non-blocking processing
async def handle_opportunity_async(event):
    # Non-blocking opportunity processing
    asyncio.create_task(process_opportunity_background(event))

scanner.add_event_handler(handle_opportunity_async)
```

### Batch Operations
```python
# Process opportunities in batches for better performance
opportunities = scanner.get_opportunities(limit=100)
for batch in chunk_opportunities(opportunities, batch_size=10):
    await process_opportunity_batch(batch)
```

## Demo and Examples

Run the comprehensive demonstration:

```bash
cd /workspace/arbitech/detection
python example_opportunity_scanner.py
```

The demo showcases:
- Complete scanner setup and configuration
- Real-time scanning with multiple bookmakers
- Advanced scheduling patterns
- Event handling and monitoring
- Performance metrics and health checks
- Production-ready error handling

## Integration with Existing Systems

The Opportunity Scanner integrates seamlessly with:

### VLM Infrastructure
- Uses existing `OddsExtractor` for image processing
- Leverages VLM error recovery and circuit breakers
- Integrates with VLM quality assessment systems

### Storage Models
- Works with `ArbitrageOpportunity` from Phase 1
- Compatible with all existing arbitrage models
- Supports the complete opportunity lifecycle

### Configuration Management
- Uses existing config system with environment overrides
- Supports hot-reloading of configuration
- Maintains backward compatibility

### Logging & Monitoring
- Comprehensive logging with structured events
- Performance metrics collection
- Health check integration
- Audit trail support

## Troubleshooting

### Common Issues and Solutions

1. **VLM API Errors**
   ```python
   # Check VLM health
   healthy = await scanner.vlm_extractor.health_check()
   if not healthy:
       print("VLM service unavailable")
   ```

2. **High Memory Usage**
   ```python
   # Monitor and adjust concurrency
   if psutil.virtual_memory().percent > 80:
       scanner.max_concurrent_scans = max(1, scanner.max_concurrent_scans // 2)
   ```

3. **Poor Detection Accuracy**
   ```python
   # Increase minimum confidence
   scanner.min_confidence = 0.8
   ```

4. **Performance Issues**
   ```python
   # Enable adaptive scheduling
   scanner.scan_scheduler.adaptive_scheduling = True
   ```

### Debug Mode
```python
import logging

# Enable comprehensive debug logging
logging.basicConfig(level=logging.DEBUG)

# Component-specific debug logging
logging.getLogger('arbitech.detection.scanner_engine').setLevel(logging.DEBUG)
logging.getLogger('arbitech.detection.market_monitor').setLevel(logging.DEBUG)
```

## License

This system is part of the ARBitech framework and follows the same licensing terms.