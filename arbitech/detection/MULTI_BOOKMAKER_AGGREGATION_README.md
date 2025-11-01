# Multi-Bookmaker Data Aggregation System

## Overview

The Multi-Bookmaker Data Aggregation System is a comprehensive solution for collecting, normalizing, synchronizing, and storing odds and market data from multiple bookmaker sources. It provides real-time data processing with fault tolerance, automatic failover, and high-performance storage capabilities.

## System Architecture

### Core Components

1. **BookmakerManager** - Central management for multiple bookmaker APIs and data sources
2. **DataAggregator** - Central data aggregation engine for consolidating odds data
3. **DataSynchronizer** - Real-time data synchronization system with conflict resolution
4. **MarketDataStore** - High-performance storage system with caching and compression

### Integration Points

- **VLM Extraction**: Integrates with the Vision Language Model extraction system
- **Configuration**: Uses the centralized configuration management system
- **Logging**: Comprehensive logging and monitoring throughout the pipeline
- **Storage Models**: Compatible with existing Pydantic data models

## Detailed Component Documentation

### 1. BookmakerManager

**Purpose**: Central management system for multiple bookmaker integrations with health monitoring and failover capabilities.

**Key Features**:
- Multi-source data collection (REST APIs, VLM extraction, WebSocket streams)
- Health monitoring with automatic failover
- Rate limiting and connection pooling
- Source priority management
- Real-time health status tracking

**Key Classes**:
- `BookmakerManager` - Main orchestration class
- `DataSource` - Individual data source configuration
- `BookmakerIntegration` - Complete bookmaker configuration
- `HealthMetrics` - Health monitoring metrics
- `RESTAPIClient` / `VLMExtractionClient` - API client implementations

**Usage Example**:
```python
# Initialize bookmaker manager
bookmaker_manager = await get_bookmaker_manager()

# Get health status
health_status = bookmaker_manager.get_all_health_status()

# Collect data from specific bookmaker
result = await bookmaker_manager.collect_data_from_bookmaker(
    bookmaker_name="bet365",
    sports=["football", "tennis"],
    markets=["match_winner"]
)

# Collect data from multiple bookmakers concurrently
results = await bookmaker_manager.collect_data_concurrent(
    bookmaker_names=["bet365", "william_hill", "pinnacle"],
    sports=["football"]
)
```

### 2. DataAggregator

**Purpose**: Central data aggregation engine that collects, normalizes, and consolidates odds data from multiple sources.

**Key Features**:
- Concurrent data collection from multiple sources
- Odds format normalization (decimal, american, fractional)
- Data quality assessment and scoring
- Multiple aggregation strategies (priority-based, weighted average, consensus)
- Conflict detection and resolution

**Key Classes**:
- `DataAggregator` - Main aggregation orchestration
- `MarketData` - Individual market data container
- `MarketOdds` - Individual odds data point
- `AggregatedEvent` - Complete event with multiple markets
- `OddsNormalizer` - Format normalization utilities
- `DataQualityAssessor` - Quality assessment and scoring

**Usage Example**:
```python
# Initialize data aggregator
data_aggregator = await get_data_aggregator()

# Aggregate data for multiple sports
aggregated_events = await data_aggregator.aggregate_sports_data(
    sports=[Sport.FOOTBALL, Sport.TENNIS],
    markets=["match_winner", "over_under"],
    aggregation_strategy=AggregationStrategy.CONSENSUS
)

# Get specific event data
event = await data_aggregator.get_event_data("event_id_123")

# Get events for a specific sport
football_events = await data_aggregator.get_sport_events(Sport.FOOTBALL)
```

### 3. DataSynchronizer

**Purpose**: Real-time data synchronization system that maintains consistency across bookmaker data sources.

**Key Features**:
- Real-time synchronization with priority queue processing
- Conflict detection and resolution with multiple strategies
- Stream processing for live data updates
- Health monitoring and automatic recovery
- Event-driven architecture with callbacks

**Key Classes**:
- `DataSynchronizer` - Main synchronization orchestration
- `SyncEvent` - Synchronization event representation
- `SyncState` - Current synchronization state
- `ConflictDetector` - Conflict detection algorithms
- `ConflictResolver` - Conflict resolution strategies
- `StreamProcessor` - Real-time stream processing

**Usage Example**:
```python
# Initialize data synchronizer
data_synchronizer = await get_data_synchronizer()

# Start synchronization for events
results = await data_synchronizer.start_synchronization(
    event_ids=["event_1", "event_2", "event_3"],
    sync_mode="continuous"
)

# Get synchronization status
status = data_synchronizer.get_sync_status("event_1")

# Subscribe to synchronization events
data_synchronizer.subscribe_to_events("event_1", my_callback)

# Pause/resume synchronization
await data_synchronizer.pause_synchronization(["event_1"])
await data_synchronizer.resume_synchronization(["event_1"])
```

### 4. MarketDataStore

**Purpose**: High-performance storage system for market data with caching, compression, and efficient retrieval.

**Key Features**:
- Multi-tier storage (memory cache + persistent storage)
- Configurable caching strategies (LRU, TTL, LFU)
- Data compression and deduplication
- Advanced search and query capabilities
- Performance monitoring and metrics
- Background maintenance tasks

**Key Classes**:
- `MarketDataStore` - Main storage orchestration
- `DataRecord` - Individual storage record
- `StorageMetrics` - Performance and usage metrics
- `LRUCache` / `TTLCache` - Cache implementations
- `SQLiteStorage` - Persistent storage backend

**Usage Example**:
```python
# Initialize market data store
data_store = await get_market_data_store()

# Store event data
success = await data_store.store_event_data(aggregated_event)

# Retrieve event data
event = await data_store.retrieve_event_data("event_id_123")

# Search events by criteria
events = await data_store.search_events(
    sport="football",
    start_time_range=(start_time, end_time),
    min_quality_score=0.8,
    limit=50
)

# Get recent events
recent_events = await data_store.get_recent_events(hours=24)

# Get performance statistics
stats = data_store.get_performance_stats()
```

## Data Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Bookmakers    │───▶│  BookmakerManager│───▶│ DataAggregator  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  VLM Extraction │───▶│ DataSynchronizer │───▶│ MarketDataStore │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

1. **Data Collection**: BookmakerManager collects raw data from various sources
2. **Data Normalization**: DataAggregator normalizes and validates the data
3. **Data Synchronization**: DataSynchronizer maintains real-time consistency
4. **Data Storage**: MarketDataStore provides persistent storage and caching

## Configuration

The system uses the existing configuration management system. Key configuration sections:

### Bookmaker Configuration
```yaml
bookmakers:
  bet365:
    enabled: true
    type: "api"
    api_key: null  # Via environment variable
    base_url: "https://api.bet365.com"
    rate_limit_per_minute: 30
    timeout: 15
    sports: ["soccer", "tennis", "basketball"]
    vlm_enabled: false
```

### Storage Configuration
```yaml
storage:
  type: "sqlite"  # or "memory"
  cache_strategy: "lru"  # or "ttl", "lfu"
  max_cache_size: 10000
  compression: "gzip"
  db_path: "data/market_data.db"
```

## Error Handling and Fault Tolerance

### Automatic Failover
- Primary data source failure triggers automatic failover to secondary sources
- Health monitoring continuously checks source availability
- Reconnection attempts with exponential backoff

### Data Validation
- Input data validation at each processing stage
- Data integrity checks with checksums
- Quality scoring to identify unreliable data

### Error Recovery
- Graceful degradation when components fail
- Automatic retry mechanisms with configurable limits
- Circuit breaker patterns to prevent cascade failures

## Performance Optimizations

### Concurrency
- Async/await throughout the entire pipeline
- Concurrent data collection from multiple sources
- Parallel processing of market data

### Caching
- Multi-level caching (memory, persistent)
- Configurable cache strategies (LRU, TTL, LFU)
- Cache warming for frequently accessed data

### Compression
- GZIP compression for stored data
- Automatic compression optimization
- Configurable compression levels

### Database Optimization
- Indexed queries for fast retrieval
- Connection pooling for database access
- Batch operations for bulk inserts/updates

## Monitoring and Metrics

### Health Monitoring
- Real-time health status for all components
- Automatic alerting for health degradation
- Performance threshold monitoring

### Metrics Collection
- Operation counts and timing
- Cache hit/miss ratios
- Data quality scores
- Source reliability metrics

### Logging
- Structured logging throughout the pipeline
- Performance logging for optimization
- Error tracking and alerting

## Integration with VLM System

The system seamlessly integrates with the VLM extraction system:

```python
# VLM extraction as a data source
vlm_source = DataSource(
    name="bet365_vlm",
    bookmaker_name="bet365",
    source_type=DataSourceType.VLM_EXTRACTION,
    priority=PriorityLevel.MEDIUM,
    timeout_seconds=120
)

# Process VLM extracted data
async def handle_vlm_extraction(image_data, extracted_odds):
    market_data = parse_vlm_odds(extracted_odds)
    await data_synchronizer.process_stream_data(event_id, market_data, "vlm")
```

## Usage Examples

### Complete Workflow Example
```python
async def complete_aggregation_workflow():
    # Initialize all components
    bookmaker_manager = await get_bookmaker_manager()
    data_aggregator = await get_data_aggregator()
    data_synchronizer = await get_data_synchronizer()
    data_store = await get_market_data_store()
    
    # Aggregate data from multiple sports
    events = await data_aggregator.aggregate_sports_data([
        Sport.FOOTBALL, Sport.TENNIS, Sport.BASKETBALL
    ])
    
    # Store aggregated events
    for event_id, event in events.items():
        await data_store.store_event_data(event)
        
        # Start real-time synchronization
        await data_synchronizer.start_synchronization([event_id])
    
    # Wait for synchronization
    await asyncio.sleep(30)
    
    # Retrieve and analyze data
    for event_id in list(events.keys())[:5]:
        event = await data_store.retrieve_event_data(event_id)
        sync_status = data_synchronizer.get_sync_status(event_id)
        
        print(f"Event: {event.event_name}")
        print(f"Quality: {event.overall_quality_score:.2f}")
        print(f"Sync Status: {sync_status['sync_status']}")
    
    # Cleanup
    await shutdown_data_synchronizer()
    await shutdown_data_aggregator()
    await shutdown_bookmaker_manager()
    await shutdown_market_data_store()
```

### Performance Monitoring Example
```python
async def monitor_performance():
    data_store = await get_market_data_store()
    data_synchronizer = await get_data_synchronizer()
    
    # Get real-time metrics
    storage_stats = data_store.get_performance_stats()
    sync_stats = data_synchronizer.get_performance_stats()
    
    print(f"Cache Hit Ratio: {storage_stats['storage_metrics']['cache_hit_ratio']:.2f}")
    print(f"Avg Read Time: {storage_stats['performance']['avg_read_time_ms']:.2f}ms")
    print(f"Active Syncs: {sync_stats['active_syncs']}")
    print(f"Sync Success Rate: {sync_stats.get('success_rate', 0):.1f}%")
```

## Testing

Run the comprehensive test suite:

```bash
cd /workspace/arbitech/detection
python test_multi_bookmaker_aggregation.py
```

The test suite includes:
- Integration tests for the complete workflow
- Performance benchmarks
- Error handling tests
- Data quality validation tests

## Best Practices

1. **Resource Management**: Always properly initialize and shutdown components
2. **Error Handling**: Implement comprehensive error handling and logging
3. **Monitoring**: Monitor health metrics and performance regularly
4. **Configuration**: Use appropriate configuration for your use case
5. **Testing**: Regularly run tests to ensure system integrity

## Troubleshooting

### Common Issues

1. **Connection Failures**: Check network connectivity and API credentials
2. **High Latency**: Review cache configuration and consider increasing cache size
3. **Memory Usage**: Monitor memory usage and adjust cache limits as needed
4. **Data Quality Issues**: Review quality scoring parameters and source reliability

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Profiling

Use the built-in metrics to identify performance bottlenecks:

```python
# Get detailed performance metrics
storage_perf = data_store.get_performance_stats()
sync_perf = data_synchronizer.get_performance_stats()
agg_stats = data_aggregator.get_aggregation_statistics()
```

## Future Enhancements

- Support for additional data source types (WebSocket streams, file feeds)
- Machine learning-based data quality assessment
- Distributed storage options (Redis, MongoDB)
- Advanced conflict resolution algorithms
- Real-time analytics and reporting
- GraphQL API for data access

---

This comprehensive multi-bookmaker data aggregation system provides a robust foundation for arbitrage detection and market analysis in the ARBitech framework.