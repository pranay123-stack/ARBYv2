# Quick Reference Guide - Enhanced Browser Automation

## Quick Start

### 1. Basic Browser Setup
```python
from arbitech.automation import EnhancedBrowser, BrowserConfig

# Initialize
browser = EnhancedBrowser()
await browser.initialize()

# Create session
config = BrowserConfig(
    name="main_session",
    headless=True,  # Set to False for headed mode
    enable_stealth=True
)
session = await browser.create_session(config)

# Use session
await browser.navigate_to_bookmaker(session, "bet365")

# Cleanup
await browser.shutdown()
```

### 2. Session Pool Management
```python
from arbitech.automation import BrowserSessionPool

# Initialize pool
pool = BrowserSessionPool()
await pool.start()

# Get session
session = await pool.get_session()

if session:
    # Use session
    await pool.release_session(session)

# Get statistics
stats = pool.get_pool_stats()
print(f"Pool health: {stats.pool_health_score}%")
```

### 3. Security Configuration
```python
from arbitech.automation import BrowserSecurity, StealthLevel

# Initialize security
security = BrowserSecurity()

# Set stealth level
security.set_stealth_level(StealthLevel.HIGH)  # minimal, standard, high, maximum

# Apply to page
await security.apply_stealth_features(page, context)

# Get current user agent
current_ua = security.get_current_user_agent()
print(f"User agent: {current_ua.browser_name} {current_ua.browser_version}")
```

### 4. Arbitrage Operations
```python
from arbitech.automation import ArbitrageBrowser

# Create arbitrage browser
arbitrage_browser = ArbitrageBrowser()
await arbitrage_browser.attach_to_page(page)

# Load bookmaker interface
await arbitrage_browser.load_bookmaker_interface("bet365")

# Place bet
bet = await arbitrage_browser.place_bet(
    bookmaker_name="bet365",
    selection="Team A",
    odds=2.5,
    stake=10.0
)

print(f"Bet status: {bet.status}")
```

## Configuration Options

### BrowserConfig
```python
BrowserConfig(
    name="session_name",
    user_data_dir="/path/to/user/data",  # Optional
    viewport={"width": 1920, "height": 1080},
    user_agent="custom_user_agent",      # Optional
    headless=True,
    proxy={"server": "http://proxy:port"},  # Optional
    extra_args=["--arg1", "--arg2"],     # Additional Chrome args
    extensions=["/path/to/extension"],   # Load extensions
    enable_stealth=True,
    max_concurrent_pages=10,
    timeout=30000,
    slow_mo=0  # Delay between actions in ms
)
```

### PoolConfig
```python
PoolConfig(
    max_sessions=10,
    min_sessions=2,
    session_timeout_seconds=1800,
    health_check_interval_seconds=60,
    max_operations_per_session=100,
    auto_scaling_enabled=True,
    load_balancing_strategy=LoadBalancingStrategy.ROUND_ROBIN,
    max_memory_usage_mb=512,
    max_cpu_usage_percent=80.0,
    recovery_attempts=3,
    graceful_shutdown_timeout=30
)
```

### SecurityProfile
```python
SecurityProfile(
    stealth_level=StealthLevel.STANDARD,
    user_agent_rotation_enabled=True,
    proxy_rotation_enabled=False,
    request_throttling=RequestThrottlingMode.ADAPTIVE,
    cookie_encryption=True,
    session_partitioning=True,
    fingerprint_randomization=True,
    network_obfuscation=False,
    resource_blocking=["fingerprint", "analytics"]
)
```

## Common Operations

### Execute Arbitrage Opportunity
```python
# Create opportunity
opportunity = ArbitrageOpportunity(
    id="opp_001",
    sport="soccer",
    event="Team A vs Team B",
    profit_margin=2.5,
    legs=[
        BetLeg(
            bookmaker="bet365",
            selection="Team A",
            odds=2.1,
            stake=100.0
        ),
        BetLeg(
            bookmaker="william_hill",
            selection="Team B",
            odds=2.0,
            stake=105.0
        )
    ]
)

# Execute
result = await browser.execute_arbitrage_opportunity(session, opportunity)

if result["success"]:
    print(f"Opportunity executed successfully")
    print(f"Operation ID: {result['operation_id']}")
else:
    print(f"Failed: {result['reason']}")
```

### Monitor Odds Changes
```python
# Start odds monitoring
task = await arbitrage_browser.monitor_odds_changes(
    bookmaker_name="bet365",
    selectors=["[data-odds]", ".odds-value"],
    callback=lambda odds: print(f"Odds changed: {odds}"),
    interval=5
)

# Later, cancel monitoring
task.cancel()
```

### Batch Bet Placement
```python
bets = [
    {
        "bookmaker": "bet365",
        "selection": "Team A",
        "odds": 2.5,
        "stake": 10.0,
        "bet_type": "single"
    },
    {
        "bookmaker": "william_hill",
        "selection": "Team B",
        "odds": 2.3,
        "stake": 9.0,
        "bet_type": "single"
    }
]

results = await arbitrage_browser.batch_place_bets(bets)
print(f"Placed {len(results)} bets successfully")
```

## Security Best Practices

### 1. Use Appropriate Stealth Level
```python
# For low-risk operations
security.set_stealth_level(StealthLevel.MINIMAL)

# For standard operations
security.set_stealth_level(StealthLevel.STANDARD)

# For high-risk operations
security.set_stealth_level(StealthLevel.HIGH)

# For maximum stealth
security.set_stealth_level(StealthLevel.MAXIMUM)
```

### 2. Monitor Security Events
```python
# Get recent security events
events = security.get_security_events(since=datetime.now() - timedelta(hours=1))

for event in events:
    if event.severity in ["warning", "critical"]:
        print(f"{event.timestamp}: {event.description}")
```

### 3. Enable User Agent Rotation
```python
# Ensure rotation is enabled
assert security.is_user_agent_rotation_enabled() == True

# Get current user agent
current_ua = security.get_current_user_agent()
print(f"Using: {current_ua.user_agent}")
```

## Performance Optimization

### 1. Configure Pool Size
```python
# For small operations
pool_config = PoolConfig(max_sessions=3, min_sessions=1)

# For medium operations  
pool_config = PoolConfig(max_sessions=10, min_sessions=2)

# For large operations
pool_config = PoolConfig(max_sessions=20, min_sessions=5)
```

### 2. Monitor Pool Health
```python
stats = pool.get_pool_stats()
print(f"Pool health: {stats.pool_health_score}%")
print(f"Memory usage: {stats.memory_usage_mb}MB")
print(f"CPU usage: {stats.cpu_usage_percent}%")
```

### 3. Enable Auto-Scaling
```python
pool_config = PoolConfig(
    auto_scaling_enabled=True,
    # Will automatically scale between min_sessions and max_sessions
)
```

## Error Handling

### 1. Session Recovery
```python
# Sessions automatically recover from errors
# Monitor recovery events
session = await pool.get_session()
if session.status == SessionStatus.ERROR:
    # Session will be automatically recycled
    pass
```

### 2. Retry Mechanisms
```python
# Built-in retry for bet placement
bet = await arbitrage_browser.place_bet(
    bookmaker_name="bet365",
    selection="Team A", 
    odds=2.5,
    stake=10.0
)

# Will automatically retry up to configured limit
print(f"Retry count: {bet.retry_count}")
```

### 3. Health Checks
```python
# Manual health check
metrics = pool.get_session_metrics(session_id)
if metrics.last_health_check:
    health_age = datetime.now() - metrics.last_health_check
    if health_age > timedelta(minutes=5):
        print("Session health check overdue")
```

## Monitoring & Analytics

### 1. Performance Metrics
```python
# Get all session metrics
all_metrics = pool.get_all_session_metrics()

for session_id, metrics in all_metrics.items():
    print(f"Session {session_id}:")
    print(f"  Operations: {metrics.total_operations}")
    print(f"  Success rate: {metrics.successful_operations / max(1, metrics.total_operations) * 100:.1f}%")
    print(f"  Avg response time: {metrics.avg_response_time_ms:.1f}ms")
    print(f"  Memory usage: {metrics.memory_usage_mb:.1f}MB")
```

### 2. Security Monitoring
```python
# Get detection statistics
detection_stats = security.get_detection_stats()
print(f"Detection attempts: {detection_stats['total_detection_attempts']}")
print(f"Blocked resources: {detection_stats['blocked_resources']}")
print(f"Recent detection rate: {detection_stats['recent_detection_rate']}/hour")
```

### 3. Operation History
```python
# Record custom operation
pool.record_operation(
    session_id=session.session_id,
    operation_type="custom_operation",
    success=True,
    response_time_ms=150.0
)
```

## Cleanup

### 1. Graceful Shutdown
```python
# For browser
await browser.shutdown()

# For pool
await pool.stop()

# For individual session
await browser._close_session(session.session_id)
```

### 2. Context Manager Pattern
```python
async with BrowserSessionPool() as pool:
    session = await pool.get_session()
    try:
        # Use session
        pass
    finally:
        await pool.release_session(session)
```

## Troubleshooting

### Common Issues

**Issue**: Sessions not being created
- **Solution**: Check Chrome remote debugging port (9222) is available

**Issue**: High memory usage  
- **Solution**: Reduce pool size or increase cleanup frequency

**Issue**: Detection by bookmakers
- **Solution**: Increase stealth level or enable proxy rotation

**Issue**: Slow performance
- **Solution**: Adjust throttling settings or use performance-based load balancing

### Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Check security events
events = security.get_security_events()
for event in events[-10:]:  # Last 10 events
    print(f"{event.timestamp}: {event.description}")

# Monitor pool statistics  
stats = pool.get_pool_stats()
print(f"Pool health: {stats.pool_health_score}")
```

## Integration with Existing System

The enhanced browser automation integrates with:

- ✅ **Risk Management**: Validates opportunities through RiskAnalyzer
- ✅ **Bookmaker Config**: Uses existing config.yaml settings
- ✅ **VLM System**: Compatible with Vision Language Model
- ✅ **Storage System**: Integrates with ArbitrageOpportunity models
- ✅ **Existing Setup**: Works with current Playwright configuration

---

For more detailed information, see the full documentation in `/workspace/arbitech/automation/README.md`
