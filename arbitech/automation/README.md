# Enhanced Playwright Setup for Arbitrage Workflows

## Overview

This enhanced browser automation system provides comprehensive functionality for arbitrage trading workflows with enterprise-grade security, stealth capabilities, and advanced session management. The system integrates with the existing Playwright setup and extends it with arbitrage-specific features.

## Architecture

The system consists of four main components:

1. **EnhancedBrowser** (`enhanced_browser.py`) - Core enhanced browser automation
2. **ArbitrageBrowser** (`arbitrage_browser.py`) - Specialized arbitrage trading browser
3. **BrowserSessionPool** (`browser_manager.py`) - Advanced session management
4. **BrowserSecurity** (`browser_security.py`) - Security and anti-detection

## Features

### Enhanced Browser Automation

- **Integration with existing setup**: Works with Chrome port 9222 and AVO Tabs extension
- **Risk management integration**: Validates opportunities through RiskAnalyzer
- **Multi-bookmaker support**: Concurrent operations across multiple bookmakers
- **Automatic recovery**: Self-healing sessions with error detection
- **Performance monitoring**: Comprehensive metrics and health checks
- **Headless/Headed modes**: Flexible operation modes

### Arbitrage Trading Browser

- **Multi-bookmaker interface management**: Handles different bookmaker layouts
- **Automated form filling**: Smart form detection and completion
- **Trade execution**: Automated bet placement with confirmation
- **Real-time monitoring**: Live odds tracking and change detection
- **Batch operations**: Multiple bet placement support
- **Error recovery**: Intelligent retry mechanisms

### Session Pool Management

- **Load balancing**: Multiple strategies (round-robin, least connections, performance-based)
- **Health monitoring**: Continuous session health assessment
- **Auto-scaling**: Dynamic session pool sizing
- **Resource optimization**: Memory and CPU usage tracking
- **Failover handling**: Automatic session replacement
- **Performance analytics**: Detailed operation metrics

### Security & Stealth

- **User agent rotation**: Dynamic user agent management
- **Proxy rotation**: Support for proxy chains
- **Request throttling**: Adaptive rate limiting
- **Fingerprint randomization**: Anti-detection techniques
- **Session partitioning**: Isolated browsing contexts
- **Network obfuscation**: Traffic pattern masking
- **Resource blocking**: Fingerprinting surface reduction

## Installation & Setup

### Prerequisites

- Python 3.8+
- Playwright installed
- Chrome browser with remote debugging enabled (port 9222)
- AVO Tabs Chrome extension (optional but recommended)

### Configuration

The system integrates with the existing configuration in `/workspace/arbitech/config/config.yaml`:

```yaml
# Browser configuration
browser:
  # Pool settings
  pool:
    max_sessions: 10
    min_sessions: 2
    session_timeout: 1800
    health_check_interval: 60
    auto_scaling: true
    load_balancing_strategy: "round_robin"
  
  # Security settings
  security:
    stealth_level: "standard"
    user_agent_rotation: true
    proxy_rotation: false
    request_throttling: "adaptive"
    cookie_encryption: true
    session_partitioning: true
    fingerprint_randomization: true
  
  # Performance settings
  timeout: 30000
  retry_attempts: 3
  max_concurrent_bets: 5
```

## Usage Examples

### Basic Enhanced Browser Usage

```python
import asyncio
from arbitech.automation import EnhancedBrowser, BrowserConfig

async def main():
    # Initialize enhanced browser
    browser = EnhancedBrowser()
    await browser.initialize()
    
    # Create session
    config = BrowserConfig(
        name="main_session",
        headless=True,
        enable_stealth=True
    )
    
    session = await browser.create_session(config)
    
    # Navigate to bookmaker
    await browser.navigate_to_bookmaker(session, "bet365")
    
    # Get status
    status = await browser.get_session_status()
    print(f"Browser status: {status}")
    
    await browser.shutdown()

asyncio.run(main())
```

### Arbitrage Browser Usage

```python
import asyncio
from arbitech.automation import ArbitrageBrowser

async def main():
    # Create arbitrage browser
    arbitrage_browser = ArbitrageBrowser()
    
    # Attach to page
    from playwright.async_api import async_playwright
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    
    await arbitrage_browser.attach_to_page(page)
    
    # Place bets
    bet = await arbitrage_browser.place_bet(
        bookmaker_name="bet365",
        selection="Team A",
        odds=2.5,
        stake=10.0
    )
    
    print(f"Bet status: {bet.status}")

asyncio.run(main())
```

### Session Pool Usage

```python
import asyncio
from arbitech.automation import BrowserSessionPool

async def main():
    # Initialize pool
    pool = BrowserSessionPool()
    await pool.start()
    
    # Get session from pool
    session = await pool.get_session()
    
    if session:
        # Use session...
        
        # Release back to pool
        await pool.release_session(session)
    
    # Get pool statistics
    stats = pool.get_pool_stats()
    print(f"Pool stats: {stats}")
    
    await pool.stop()

asyncio.run(main())
```

### Security Features

```python
import asyncio
from arbitech.automation import BrowserSecurity, StealthLevel

async def main():
    # Initialize security manager
    security = BrowserSecurity()
    
    # Set stealth level
    security.set_stealth_level(StealthLevel.HIGH)
    
    # Get current user agent
    current_ua = security.get_current_user_agent()
    print(f"User agent: {current_ua.user_agent}")
    
    # Apply to page
    from playwright.async_api import async_playwright
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await browser.new_page()
    
    await security.apply_stealth_features(page, context)

asyncio.run(main())
```

## Integration with Existing System

### Risk Management Integration

The system integrates with the existing risk management system:

```python
from arbitech.risk.risk_analyzer import RiskAnalyzer

# The enhanced browser automatically validates opportunities
validation_result = risk_analyzer.validate_opportunity(opportunity)
```

### Bookmaker Configuration

Bookmaker configurations are loaded from the existing config:

```yaml
bookmakers:
  bet365:
    enabled: true
    base_url: "https://www.bet365.com"
    max_stake_per_bet: 500.0
  william_hill:
    enabled: true
    base_url: "https://www.williamhill.com"
    max_stake_per_bet: 300.0
```

### VLM Integration

Supports Vision Language Model integration for complex interface handling:

```python
from arbitech.vlm.odds_extractor import OddsExtractor

# Odds extraction and processing
extractor = OddsExtractor()
odds_data = await extractor.extract_odds(page)
```

## Running the Demo

Execute the comprehensive demo:

```bash
cd /workspace
python automation_demo.py
```

The demo showcases:
- Browser pool management
- Security features
- Multi-bookmaker operations
- Risk integration
- Performance monitoring
- Concurrent operations

## Security Considerations

### Stealth Levels

- **Minimal**: Basic stealth for low-risk operations
- **Standard**: Balanced stealth and performance
- **High**: Strong stealth for sensitive operations
- **Maximum**: Maximum stealth with reduced performance

### Anti-Detection Features

- User agent rotation
- Request throttling
- Canvas fingerprint randomization
- WebGL noise injection
- Plugin mocking
- WebDriver hiding
- Console API hiding

### Proxy Support

- HTTP/HTTPS/SOCKS4/SOCKS5 proxies
- Automatic rotation
- Health monitoring
- Response time tracking

## Performance Optimization

### Session Pool Configuration

```python
PoolConfig(
    max_sessions=10,
    min_sessions=2,
    session_timeout_seconds=1800,
    health_check_interval_seconds=60,
    auto_scaling_enabled=True,
    load_balancing_strategy=LoadBalancingStrategy.LEAST_CONNECTIONS
)
```

### Resource Management

- Automatic memory cleanup
- Session timeout handling
- Error rate monitoring
- Performance score calculation

## Monitoring & Analytics

### Metrics Collected

- Operation success/failure rates
- Response times
- Memory usage
- CPU utilization
- Error patterns
- Session health scores

### Health Checks

- Page responsiveness
- Memory usage thresholds
- Error rate monitoring
- Session age tracking

## Error Handling & Recovery

### Automatic Recovery

- Session recycling on errors
- Health check failures
- Memory limit exceeded
- Timeout handling

### Retry Mechanisms

- Configurable retry attempts
- Exponential backoff
- Operation-specific retries
- Circuit breaker patterns

## Best Practices

### Security

1. Use appropriate stealth level for your risk tolerance
2. Enable user agent rotation for production
3. Monitor detection attempts
4. Use proxy rotation for sensitive operations
5. Regularly update user agent profiles

### Performance

1. Configure appropriate pool sizes
2. Monitor memory usage
3. Use load balancing effectively
4. Implement proper timeouts
5. Regular health checks

### Reliability

1. Enable auto-scaling
2. Monitor error rates
3. Implement circuit breakers
4. Use comprehensive logging
5. Regular testing

## Troubleshooting

### Common Issues

1. **Sessions not created**: Check Chrome remote debugging port
2. **Detection by bookmakers**: Increase stealth level
3. **High memory usage**: Reduce pool size or increase cleanup frequency
4. **Slow performance**: Adjust throttling settings
5. **Connection timeouts**: Check network and proxy settings

### Debugging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check security events:

```python
security_events = security.get_security_events()
for event in security_events:
    print(f"{event.timestamp}: {event.description}")
```

Monitor pool statistics:

```python
stats = pool.get_pool_stats()
print(f"Pool health: {stats.pool_health_score}")
```

## Contributing

When extending the system:

1. Follow the existing architecture patterns
2. Maintain backward compatibility
3. Add comprehensive error handling
4. Include proper logging
5. Write unit tests
6. Update documentation

## License

This enhanced browser automation system is part of the ARBitech framework and follows the same licensing terms.

## Support

For issues and questions:
- Check the logs for detailed error information
- Review the security event logs
- Monitor pool health statistics
- Test with the provided demo script

---

*This enhanced browser automation system provides enterprise-grade functionality for arbitrage trading workflows with comprehensive security, performance optimization, and reliability features.*
