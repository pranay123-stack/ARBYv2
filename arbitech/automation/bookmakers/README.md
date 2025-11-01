# Bookmaker-Specific Automation Handlers

A comprehensive automation framework for arbitrage betting across multiple bookmaker platforms. This system provides specialized handlers for different betting platforms, each optimized for their unique features and requirements.

## Overview

The bookmaker automation system consists of:

- **Base Handler** - Common functionality and interface abstraction
- **Betfair Handler** - Exchange trading and market making
- **Pinnacle Handler** - Asian handicaps and live betting
- **BetDex Handler** - Cryptocurrency integration and DeFi markets
- **Aver Handler** - Regional markets and local payment methods
- **Handler Manager** - Unified coordination and management

## Features

### Common Features (All Handlers)
- ✅ Consistent interface for cross-bookmaker operations
- ✅ Authentication and session management
- ✅ Rate limiting and request queuing
- ✅ Error handling and recovery mechanisms
- ✅ Performance monitoring and metrics
- ✅ Configuration management
- ✅ Health checking and auto-recovery
- ✅ Event-driven architecture

### Bookmaker-Specific Features

#### Betfair Handler
- 🔄 **Exchange Trading** - Back/Lay betting with market depth
- 📊 **Market Analysis** - Liquidity information and trading volume
- 💰 **Commission Calculation** - Automated exchange commission handling
- ⏸️ **Market Suspension** - Real-time suspension detection
- 🎯 **Asian Handicap** - Specialized handicap market support
- 🔴 **In-Play Trading** - Live betting capabilities

#### Pinnacle Handler
- 🎯 **Asian Handicap** - Native Asian handicap markets
- 🔴 **Live Betting** - Comprehensive in-play betting
- 💎 **High Stakes** - Large bet limit support
- 📉 **Low Margins** - Competitive odds with low bookmaker margin
- 🌍 **Multi-Currency** - Support for various currencies
- 🎮 **Esports** - Dedicated esports betting markets

#### BetDex Handler
- 🪙 **Cryptocurrency** - Full crypto payment and settlement support
- ⚡ **Smart Contracts** - Blockchain-based betting transactions
- 🌉 **Cross-Chain** - Multi-blockchain compatibility
- 🎨 **NFT Betting** - NFT price and volume predictions
- 🏦 **DeFi Integration** - Yield farming and liquidity mining markets
- 🗳️ **DAO Governance** - Governance token betting

#### Aver Handler
- 🌍 **Regional Focus** - Africa, Asia, Latin America markets
- 💳 **Local Payments** - Mobile money, local banking methods
- 📱 **Mobile-First** - Optimized for mobile betting
- 📺 **Live Streaming** - Integrated sports streaming
- 🏆 **Local Leagues** - Regional league coverage
- 🎭 **Cultural Adaptation** - Region-specific betting preferences

## Architecture

```python
arbitech/
└── automation/
    └── bookmakers/
        ├── __init__.py
        ├── handler_base.py          # Base class and common interfaces
        ├── handler_manager.py       # Manager for all handlers
        ├── betfair_handler.py       # Betfair exchange handler
        ├── pinnacle_handler.py      # Pinnacle sports handler
        ├── betdex_handler.py        # BetDex crypto handler
        ├── average_handler.py       # Aver regional handler
        ├── demo.py                  # Comprehensive demo
        └── README.md                # This file
```

## Installation

### Requirements

```python
# Core dependencies
aiohttp>=3.8.0
pyyaml>=6.0
web3>=6.0.0
python-dateutil>=2.8.0

# Optional dependencies for specific handlers
# For BetDex (crypto features)
# - Additional Web3 libraries as needed
# - Blockchain RPC access

# For Aver (regional features)
# - Local payment SDKs (if available)
# - Regional API access
```

### Setup

1. **Clone or copy the bookmaker handlers to your project**
2. **Install dependencies**:
   ```bash
   pip install aiohttp pyyaml web3 python-dateutil
   ```
3. **Configure authentication** for each bookmaker
4. **Initialize handlers** with appropriate configurations

## Quick Start

### Basic Usage

```python
import asyncio
from automation.bookmakers import BookmakerHandlerManager, ManagerConfig
from automation.bookmakers.handler_base import BetRequest

async def main():
    # Initialize manager
    config = ManagerConfig(
        auto_recovery=True,
        health_check_interval=30,
        max_concurrent_requests=10
    )
    manager = BookmakerHandlerManager(config)
    
    # Register handlers
    handler_configs = {
        'betfair': {'api_key': '...', 'username': '...', 'password': '...'},
        'pinnacle': {'username': '...', 'password': '...', 'client_id': '...'},
        'betdex': {'private_key': '...', 'wallet_address': '...'},
        'aver': {'username': '..., 'password': '...', 'region': 'africa'}
    }
    
    results = await manager.register_default_handlers(handler_configs)
    
    # Place a bet
    bet_request = BetRequest(
        market_id="12345",
        selection_id="67890", 
        selection_name="Team A",
        odds=2.5,
        stake=100.0,
        bet_type="back",
        market_type="match_odds"
    )
    
    response = await manager.place_bet(bet_request)
    print(f"Bet placed: {response.success}")
    
    # Get markets from all bookmakers
    markets = await manager.get_markets({'sport': 'football'})
    for bookmaker, market_list in markets.items():
        print(f"{bookmaker}: {len(market_list)} markets")
    
    # Cleanup
    await manager.close()

asyncio.run(main())
```

### Individual Handler Usage

```python
import asyncio
from automation.bookmakers.betfair_handler import BetfairHandler

async def betfair_example():
    config = {
        'api_key': 'your_api_key',
        'username': 'your_username', 
        'password': 'your_password',
        'exchange_app_key': 'your_app_key'
    }
    
    async with BetfairHandler(config) as handler:
        # Check status
        print(f"Status: {handler.status.value}")
        
        # Get markets
        markets = await handler.get_markets({'sport': 'football'})
        print(f"Found {len(markets)} markets")
        
        # Place a bet
        bet_response = await handler.place_bet(bet_request)
        
        # Get balance
        balance = await handler.get_balance()
        print(f"Balance: {balance}")

asyncio.run(betfair_example())
```

### Configuration Examples

#### Betfair Configuration
```python
betfair_config = {
    'api_base_url': 'https://api.betfair.com/exchange/betting/rest/v1',
    'login_url': 'https://identitysso.betfair.com/api/login',
    'api_key': 'your_betfair_api_key',
    'username': 'your_betfair_username',
    'password': 'your_betfair_password',
    'exchange_app_key': 'lwapV6BgqzeNDTJ5',
    'commission_rate': 0.02,
    'timeout': 15,
    'max_retries': 3
}
```

#### Pinnacle Configuration
```python
pinnacle_config = {
    'api_base_url': 'https://api.pinnacle.com',
    'username': 'your_pinnacle_username',
    'password': 'your_pinnacle_password',
    'client_id': 'your_pinnacle_client_id',
    'client_secret': 'your_pinnacle_client_secret',
    'default_currency': 'USD',
    'live_betting_enabled': True,
    'timeout': 10
}
```

#### BetDex Configuration
```python
betdex_config = {
    'api_base_url': 'https://api.betdex.com',
    'web3_rpc_url': 'https://mainnet.infura.io/v3/YOUR_KEY',
    'private_key': 'your_wallet_private_key',
    'wallet_address': 'your_wallet_address',
    'chain_id': 1,
    'default_currency': 'USDC',
    'betting_contract_address': '0x...',
    'timeout': 20
}
```

#### Aver Configuration
```python
aver_config = {
    'api_base_url': 'https://api.aver.com',
    'region': 'africa',  # africa, asia, latam
    'language': 'en',
    'timezone': 'Africa/Johannesburg',
    'username': 'your_aver_username',
    'password': 'your_aver_password',
    'default_currency': 'GHS',
    'live_stream_enabled': True,
    'mobile_optimized': True
}
```

## Advanced Features

### Load Balancing

The manager supports multiple load balancing strategies:

```python
config = ManagerConfig(
    load_balancing_strategy="round_robin"  # or "least_loaded", "fastest_response"
)
```

### Health Monitoring

```python
# Start automatic health monitoring
await manager.start_health_monitoring()

# Manual health check
health_reports = await manager.health_check_all_handlers()
for bookmaker, report in health_reports.items():
    print(f"{bookmaker}: {'Healthy' if report['healthy'] else 'Unhealthy'}")
```

### Event Handling

```python
# Register event handlers
def on_error(error):
    print(f"Error occurred: {error}")

def on_handler_registered(bookmaker):
    print(f"Handler registered: {bookmaker}")

manager.on('error_occurred', on_error)
manager.on('handler_registered', on_handler_registered)
```

### Performance Metrics

```python
# Get comprehensive metrics
metrics = await manager.get_comprehensive_metrics()
print(f"Active handlers: {metrics['manager']['active_handlers']}")
print(f"Total requests: {metrics['manager']['total_requests']}")

# Handler-specific metrics
for bookmaker, handler_metrics in metrics['handlers'].items():
    print(f"{bookmaker}:")
    print(f"  - Success rate: {handler_metrics['success_rate']:.2%}")
    print(f"  - Avg response time: {handler_metrics['response_time_avg']:.3f}s")
    print(f"  - Uptime: {handler_metrics['uptime_percentage']:.2%}")
```

## Bookmaker-Specific Examples

### Betfair Exchange Trading

```python
# Get market depth
market_data = await handler.update_market_data(market_id)
for selection in market_data.selections:
    exchange_data = selection.get('exchange', {})
    back_prices = exchange_data.get('back', [])
    lay_prices = exchange_data.get('lay', [])
    
    if back_prices:
        best_back = back_prices[0]  # Best back price
        print(f"Best back: {best_back['price']} for {best_back['size']}")
    
    if lay_prices:
        best_lay = lay_prices[0]  # Best lay price
        print(f"Best lay: {best_lay['price']} for {best_lay['size']}")

# Calculate potential arbitrage
back_odds = get_best_back_price(selection)
lay_odds = get_best_lay_price(selection)
if back_odds > lay_odds + commission_rate:
    print("Arbitrage opportunity!")
```

### Pinnacle Asian Handicap

```python
# Place Asian handicap bet
bet_request = BetRequest(
    market_id="handicap123",
    selection_id="home456",
    selection_name="Home Team -1.5",
    odds=1.95,
    stake=100.0,
    bet_type="back",
    market_type="asian_handicap",
    metadata={'handicap': -1.5}
)

# Calculate handicap outcome
outcome = handler.calculate_asian_handicap_outcome(
    home_score=2, away_score=0, handicap=-1.5, bet_type='home'
)
print(f"Handicap outcome: {outcome}")
```

### BetDex Cryptocurrency

```python
# Swap tokens before betting
swap_tx = await handler.swap_tokens('ETH', 'USDC', 1.0)
if swap_tx:
    print(f"Swap completed: {swap_tx}")

# Place crypto bet
bet_request = BetRequest(
    market_id="crypto123",
    selection_id="btc456",
    selection_name="Bitcoin Price > $50000",
    odds=2.0,
    stake=100.0,
    bet_type="back",
    market_type="crypto_prediction",
    metadata={'volatility': 0.25}
)

# Volatility-adjusted odds
adjusted_odds = handler.calculate_crypto_volatility_adjusted_odds(2.0, 0.25)
print(f"Volatility-adjusted odds: {adjusted_odds}")
```

### Aver Regional Betting

```python
# Get regional payment methods
payment_methods = await handler.get_local_payment_methods()
for method in payment_methods:
    print(f"{method['name']}: {method['description']}")

# Calculate regional betting limits
limits = handler.calculate_regional_betting_limits('match_odds', 8)
print(f"Min stake: ${limits['min']}, Max stake: ${limits['max']}")

# Get cultural preferences
preferences = handler.get_cultural_betting_preferences()
print(f"Popular markets: {preferences['popular_markets']}")
```

## Error Handling

### Common Error Patterns

```python
try:
    response = await manager.place_bet(bet_request)
    if not response.success:
        print(f"Bet failed: {response.error_message}")
        # Handle specific error types
        if "authentication" in response.error_message.lower():
            # Re-authenticate
            await handler.reauthenticate()
        elif "rate_limit" in response.error_message.lower():
            # Wait and retry
            await asyncio.sleep(10)
except Exception as e:
    print(f"Unexpected error: {e}")
    # Trigger recovery mechanisms
    await manager.health_check_all_handlers()
```

### Automatic Recovery

The system includes automatic recovery mechanisms:

- **Re-authentication** - Automatic token refresh
- **Connection retry** - Exponential backoff retry logic
- **Fallback handlers** - Switch to backup handlers
- **Circuit breaker** - Temporarily disable failing handlers
- **Health monitoring** - Continuous health checks

## Security Considerations

### Credential Management

```python
# Load credentials from environment variables
import os

config = {
    'api_key': os.getenv('BETFAIR_API_KEY'),
    'username': os.getenv('BETFAIR_USERNAME'),
    'password': os.getenv('BETFAIR_PASSWORD'),
    # Use environment variables for sensitive data
}

# Never hardcode credentials in source code
```

### Rate Limiting Compliance

```python
# Respect bookmaker rate limits
config = {
    'rate_limit_rpm': 20,    # Betfair: 20 requests/minute
    'rate_limit_rph': 1000,  # Adjust per bookmaker
    'timeout': 15,
    'max_retries': 3
}
```

### Regional Compliance

```python
# Respect regional regulations
config = {
    'region': 'africa',
    'language': 'en',
    'timezone': 'Africa/Johannesburg',
    'compliance_mode': 'strict'  # Enable strict compliance checks
}
```

## Performance Optimization

### Connection Management

- **Connection pooling** - Reuse HTTP connections
- **Keep-alive** - Maintain persistent connections
- **Concurrent requests** - Parallel API calls

### Caching Strategies

```python
# Enable caching for frequently accessed data
config = {
    'cache_markets': True,
    'cache_ttl': 300,  # 5 minutes
    'cache_odds': True,
    'cache_odds_ttl': 30  # 30 seconds
}
```

### Monitoring and Alerting

```python
# Set up performance monitoring
manager.on('health_check_failed', handle_health_failure)
manager.on('balance_updated', update_balance_alerts)

async def handle_health_failure(bookmaker, health_report):
    # Alert or take corrective action
    if not health_report['healthy']:
        # Send alert, switch to fallback, etc.
        pass
```

## Testing

### Unit Testing

```python
import pytest
import asyncio
from automation.bookmakers.betfair_handler import BetfairHandler

@pytest.mark.asyncio
async def test_betfair_handler_initialization():
    config = {'username': 'test', 'password': 'test'}
    handler = BetfairHandler(config)
    
    # Mock the HTTP responses for testing
    # ... setup mocks ...
    
    result = await handler.initialize()
    assert result == True
    assert handler.status == HandlerStatus.READY
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_manager_coordination():
    manager = BookmakerHandlerManager()
    
    # Test handler registration
    success = await manager.register_handler(
        'betfair', BetfairHandler, test_config
    )
    assert success == True
    
    # Test bet placement
    bet_request = create_test_bet_request()
    response = await manager.place_bet(bet_request)
    # ... verify response ...
```

## Deployment

### Production Configuration

```python
# Production config with security hardening
prod_config = ManagerConfig(
    auto_recovery=True,
    health_check_interval=60,
    max_concurrent_requests=5,
    load_balancing_strategy="fastest_response",
    performance_monitoring=True,
    config_file="/secure/path/manager_config.json"
)

# Secure credential storage
secure_configs = {
    'betfair': load_secure_config('betfair.yaml'),
    'pinnacle': load_secure_config('pinnacle.yaml'),
    # Load from secure secret management system
}
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY automation/ ./automation/

CMD ["python", "-m", "automation.bookmakers.demo"]
```

## Support and Contributing

### Getting Help

1. **Documentation** - Check this README and inline documentation
2. **Demo** - Run the comprehensive demo to understand features
3. **Logs** - Enable debug logging for troubleshooting
4. **Health checks** - Use health monitoring for issue detection

### Contributing

The system is designed to be extensible. To add a new bookmaker handler:

1. **Extend BaseBookmakerHandler** - Inherit from the base class
2. **Implement abstract methods** - Override required methods
3. **Add bookmaker-specific features** - Implement unique capabilities
4. **Register with manager** - Update handler mapping
5. **Add tests** - Create comprehensive test coverage

### License

This bookmaker automation system is designed for educational and legitimate arbitrage betting purposes. Ensure compliance with:

- Bookmaker terms of service
- Regional gambling regulations
- Local laws and regulations
- Responsible gambling practices

## Changelog

### Version 1.0.0
- ✅ Initial release with all bookmaker handlers
- ✅ Base handler framework
- ✅ Betfair exchange trading support
- ✅ Pinnacle Asian handicap support
- ✅ BetDex cryptocurrency integration
- ✅ Aver regional market support
- ✅ Handler manager with load balancing
- ✅ Comprehensive error handling and recovery
- ✅ Performance monitoring and metrics
- ✅ Security and compliance features

---

**Disclaimer**: This software is provided for educational purposes. Users are responsible for compliance with all applicable laws and bookmaker terms of service. The authors are not responsible for any losses incurred through the use of this software.