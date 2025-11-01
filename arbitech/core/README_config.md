# Arbitech Configuration Management System

## Overview

The Arbitech configuration management system provides a flexible, YAML-based configuration framework with support for environment variable overrides, validation, and hot-reload capabilities. This system is designed to handle complex arbitrage trading configurations while maintaining simplicity and reliability.

## Features

- ✅ **YAML-based configuration**: Human-readable configuration files
- ✅ **Environment variable overrides**: Override any configuration value via environment variables
- ✅ **Validation**: Automatic validation of configuration values and structure
- ✅ **Hot-reload**: Automatic reloading of configuration when file changes
- ✅ **Type conversion**: Automatic conversion of environment variables to appropriate types
- ✅ **Nested configuration access**: Use dot notation to access nested configuration values
- ✅ **Runtime modification**: Modify configuration values at runtime
- ✅ **Callback system**: Register callbacks for configuration changes
- ✅ **Thread-safe**: Safe for concurrent access

## Configuration Structure

### User Risk Configuration

```yaml
user:
  risk:
    max_stake: 1000.0          # Maximum stake amount per bet
    risk_percentage: 2.0       # Risk percentage of bankroll per bet (0-100)
    min_odds: 1.5             # Minimum odds to consider
    max_odds: 10.0            # Maximum odds to consider
    max_concurrent_bets: 5     # Maximum concurrent bets
    stop_loss_percentage: 10.0 # Stop loss percentage (null to disable)
    take_profit_percentage: 20.0 # Take profit percentage (null to disable)
    min_profit_margin: 1.0     # Minimum profit margin percentage
    max_exposure_per_bookmaker: 500.0 # Maximum exposure per bookmaker
```

### System Configuration

```yaml
system:
  vlm:
    endpoint: "http://localhost:8080/vlm"
    api_key: null
    timeout: 30
    retry_attempts: 3
    enabled: true
  
  scan_intervals:
    general_scan: 60           # General opportunity scan interval (seconds)
    live_odds: 5              # Live odds check interval (seconds)
    bookmaker_update: 30       # Bookmaker data update interval (seconds)
    balance_check: 300         # Balance check interval (seconds)
    health_check: 120          # Health check interval (seconds)
  
  performance:
    max_concurrent_scans: 10    # Maximum concurrent scans
    thread_pool_size: 20       # Thread pool size
    memory_limit: 1024         # Memory limit in MB
    cache_expiration: 300      # Cache expiration time in seconds
```

### Bookmaker Integrations

```yaml
bookmakers:
  bet365:
    enabled: true
    type: "api"
    api_key: null              # Set via environment variable
    username: null             # Set via environment variable
    base_url: "https://api.bet365.com"
    rate_limit_per_minute: 30
    sports:
      - "soccer"
      - "tennis"
      - "basketball"
    currency: "GBP"
    max_stake_per_bet: 500.0
```

### Notification Preferences

```yaml
notifications:
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    username: null             # Set via environment variable
    password: null             # Set via environment variable
    to_addresses:
      - "user@example.com"
  
  discord:
    enabled: false
    webhook_url: null          # Set via environment variable
  
  triggers:
    min_profit_margin: 2.0      # Minimum profit margin for notifications
    max_opportunities_per_hour: 10
    enable_opportunity_alerts: true
    enable_error_alerts: true
```

### Logging Configuration

```yaml
logging:
  level: "INFO"                # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/arbitech.log"
  max_file_size: 10485760      # 10MB
  backup_count: 5
  console: true
```

## Environment Variable Overrides

You can override any configuration value using environment variables. The format is:

```
ARBITECH_<SECTION>__<KEY>
```

Where:
- `<SECTION>` is the configuration section (e.g., `USER`, `SYSTEM`, `BOOKMAKERS`)
- `<KEY>` is the configuration key (use double underscores `__` for nested keys)

### Examples

```bash
# Override max stake
export ARBITECH_USER__RISK__MAX_STAKE=2000.0

# Enable VLM
export ARBITECH_SYSTEM__VLM__ENABLED=true

# Set bookmaker API key
export ARBITECH_BOOKMAKERS__BET365__API_KEY=your_api_key

# Enable email notifications
export ARBITECH_NOTIFICATIONS__EMAIL__ENABLED=true

# Set email SMTP credentials
export ARBITECH_NOTIFICATIONS__EMAIL__SMTP_SERVER=smtp.gmail.com
export ARBITECH_NOTIFICATIONS__EMAIL__USERNAME=your_email@gmail.com
export ARBITECH_NOTIFICATIONS__EMAIL__PASSWORD=your_app_password
```

### Supported Value Types

The configuration manager automatically converts environment variables to appropriate Python types:

- **Booleans**: `true`, `false`, `True`, `False`
- **Integers**: Whole numbers (e.g., `10`, `100`)
- **Floats**: Decimal numbers (e.g., `1.5`, `10.25`)
- **JSON**: Complex data structures (e.g., `{"key": "value"}`)
- **Strings**: Everything else

## Usage

### Basic Usage

```python
from arbitech.core.config_manager import init_config, get_config, set_config

# Initialize configuration
init_config(config_path="config/config.yaml")

# Get configuration values
max_stake = get_config('user.risk.max_stake')
vlm_enabled = get_config('system.vlm.enabled', False)  # With default value

# Set configuration values
set_config('user.risk.max_stake', 1500.0)

# Reload configuration from file
reload_config()
```

### Advanced Usage

```python
from arbitech.core.config_manager import (
    init_config, get_config_manager, get_user_config,
    get_system_config, get_bookmaker_configs,
    get_notification_config, get_logging_config,
    get_risk_limits, get_scan_intervals, get_active_bookmakers
)

# Initialize configuration
manager = init_config(config_path="config/config.yaml")

# Access configuration sections
user_config = get_user_config()
system_config = get_system_config()
bookmaker_configs = get_bookmaker_configs()
notification_config = get_notification_config()
logging_config = get_logging_config()

# Get risk limits
risk_limits = get_risk_limits()
print(f"Max stake: {risk_limits['max_stake']}")

# Get scan intervals
scan_intervals = get_scan_intervals()
print(f"General scan interval: {scan_intervals['general_scan']}")

# Get active bookmakers
active_bookmakers = get_active_bookmakers()
print(f"Active bookmakers: {active_bookmakers}")
```

### Bookmaker-Specific Access

```python
# Get all bookmaker configurations
all_bookmakers = get_config('bookmakers', {})

# Get specific bookmaker configuration
bet365_config = get_config('bookmakers.bet365', {})
print(f"Bet365 enabled: {bet365_config.get('enabled')}")

# Check if bookmaker is enabled
from arbitech.core.config_manager import is_bookmaker_enabled

if is_bookmaker_enabled('bet365'):
    print("Bet365 is enabled")
    
    # Get bet365-specific settings
    bet365_sports = get_config('bookmakers.bet365.sports', [])
    bet365_currency = get_config('bookmakers.bet365.currency', 'USD')
```

### Configuration Change Callbacks

```python
from arbitech.core.config_manager import get_config_manager

def on_config_change(old_config, new_config):
    """Called when configuration is reloaded."""
    old_max_stake = old_config.get('user', {}).get('risk', {}).get('max_stake')
    new_max_stake = new_config.get('user', {}).get('risk', {}).get('max_stake')
    
    if old_max_stake != new_max_stake:
        print(f"Max stake changed from {old_max_stake} to {new_max_stake}")

# Register callback
manager = get_config_manager()
manager.register_callback(on_config_change)

# Configuration changes will now trigger the callback
```

### Configuration Validation

The configuration system automatically validates your configuration when loading:

- **Type validation**: Ensures values are of the correct type
- **Range validation**: Ensures numerical values are within reasonable ranges
- **Required field validation**: Ensures all required fields are present
- **Logical validation**: Ensures values make logical sense (e.g., min < max)

```python
from arbitech.core.config_manager import init_config, ConfigError

try:
    init_config(config_path="config/config.yaml")
    print("Configuration loaded and validated successfully")
except ConfigError as e:
    print(f"Configuration error: {e}")
```

## Configuration File Management

### Saving Configuration

```python
from arbitech.core.config_manager import get_config_manager

# Get the configuration manager
manager = get_config_manager()

# Save current configuration to file
manager.save_to_file("custom_config.yaml")

# Or save to the default location
manager.save_to_file()
```

### Hot-Reload Configuration

```python
import time
from arbitech.core.config_manager import get_config_manager, get_config

# Initialize configuration
init_config(config_path="config/config.yaml")

# Modify configuration in another process or thread
manager = get_config_manager()
manager.set('user.risk.max_stake', 2000.0)
manager.save_to_file()

# Wait a moment for file system events
time.sleep(1)

# Reload configuration (this will be automatic if watching is enabled)
reload_config()

# Verify the change
new_max_stake = get_config('user.risk.max_stake')
print(f"New max stake: {new_max_stake}")
```

## Thread Safety

The configuration manager is thread-safe and can be accessed from multiple threads simultaneously:

```python
import threading
from arbitech.core.config_manager import get_config

def worker_thread(thread_id):
    """Worker thread that reads configuration."""
    for i in range(10):
        max_stake = get_config('user.risk.max_stake')
        print(f"Thread {thread_id}: Max stake is {max_stake}")
        time.sleep(0.1)

# Start multiple worker threads
threads = []
for i in range(5):
    thread = threading.Thread(target=worker_thread, args=(i,))
    thread.start()
    threads.append(thread)

# Wait for all threads to complete
for thread in threads:
    thread.join()
```

## Error Handling

The configuration system provides clear error messages for common issues:

```python
from arbitech.core.config_manager import (
    init_config, ConfigError, get_config
)

try:
    # Try to initialize configuration
    init_config(config_path="config/config.yaml")
    
    # Try to access a non-existent value
    value = get_config('non.existent.path', 'default_value')
    
except ConfigError as e:
    print(f"Configuration error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

1. **Use environment variables for sensitive data**: Store API keys, passwords, and other sensitive information in environment variables rather than in configuration files.

2. **Validate your configuration**: Always validate your configuration during initialization to catch errors early.

3. **Use appropriate log levels**: Configure logging levels appropriately for different environments (DEBUG for development, INFO for production).

4. **Monitor configuration changes**: Register callbacks to be notified when configuration changes, especially for critical settings like risk parameters.

5. **Backup your configuration**: Keep backups of your configuration files, especially when running in production.

6. **Document your changes**: When modifying configuration values, document what changed and why.

7. **Use type hints**: When accessing configuration values in your code, use appropriate type checking to catch errors early.

## Example Production Setup

```python
# production.py - Production configuration setup

import os
from arbitech.core.config_manager import init_config, get_config_manager

def setup_production_config():
    """Set up configuration for production environment."""
    
    # Set environment variables for production
    os.environ.update({
        'ARBITECH_USER__RISK__MAX_STAKE': '5000.0',
        'ARBITECH_USER__RISK__RISK_PERCENTAGE': '1.0',
        'ARBITECH_SYSTEM__PERFORMANCE__MAX_CONCURRENT_SCANS': '20',
        'ARBITECH_BOOKMAKERS__BET365__API_KEY': os.getenv('BET365_API_KEY'),
        'ARBITECH_NOTIFICATIONS__EMAIL__ENABLED': 'true',
        'ARBITECH_NOTIFICATIONS__EMAIL__SMTP_SERVER': 'smtp.gmail.com',
        'ARBITECH_NOTIFICATIONS__EMAIL__USERNAME': os.getenv('SMTP_USERNAME'),
        'ARBITECH_NOTIFICATIONS__EMAIL__PASSWORD': os.getenv('SMTP_PASSWORD'),
        'ARBITECH_LOGGING__LEVEL': 'INFO',
        'ARBITECH_LOGGING__FILE': '/var/log/arbitech/arbitech.log'
    })
    
    # Initialize configuration
    init_config(
        config_path='/etc/arbitech/config.yaml',
        watch_for_changes=True
    )
    
    # Configure logging
    manager = get_config_manager()
    manager.configure_logging()
    
    print("Production configuration loaded successfully")

if __name__ == '__main__':
    setup_production_config()
```

This configuration management system provides a robust, flexible, and user-friendly way to manage all aspects of the Arbitech arbitrage trading system.
