# Arbitech Configuration Management - Quick Reference

## Quick Start

```python
from arbitech.core.config_manager import init_config, get_config, set_config

# Initialize (loads config.yaml)
init_config()

# Get values
max_stake = get_config('user.risk.max_stake')
active_bookmakers = get_config('bookmakers', {})

# Modify and save
set_config('user.risk.max_stake', 1500.0)
```

## Environment Variables

```bash
# Format: ARBITECH_<SECTION>__<KEY>

# User settings
export ARBITECH_USER__RISK__MAX_STAKE=2000.0
export ARBITECH_USER__RISK__RISK_PERCENTAGE=1.5

# System settings
export ARBITECH_SYSTEM__VLM__ENABLED=true
export ARBITECH_SYSTEM__PERFORMANCE__MAX_CONCURRENT_SCANS=20

# Bookmaker credentials
export ARBITECH_BOOKMAKERS__BET365__API_KEY=your_key
export ARBITECH_BOOKMAKERS__BET365__USERNAME=your_user

# Notifications
export ARBITECH_NOTIFICATIONS__EMAIL__ENABLED=true
export ARBITECH_NOTIFICATIONS__DISCORD__WEBHOOK_URL=https://...
```

## Common Configuration Paths

### User Risk Settings
```
user.risk.max_stake                    # Maximum stake per bet
user.risk.risk_percentage             # % of bankroll per bet
user.risk.min_odds                    # Minimum odds to consider
user.risk.max_odds                    # Maximum odds to consider
user.risk.max_concurrent_bets         # Concurrent bet limit
user.risk.min_profit_margin           # Minimum profit %
user.risk.max_exposure_per_bookmaker  # Exposure limit
```

### System Settings
```
system.vlm.enabled                    # Enable VLM integration
system.vlm.endpoint                   # VLM API endpoint
system.vlm.timeout                    # VLM request timeout
system.scan_intervals.general_scan    # Opportunity scan interval
system.scan_intervals.live_odds       # Live odds check interval
system.scan_intervals.balance_check   # Balance check interval
system.performance.max_concurrent_scans # Max concurrent scans
system.performance.thread_pool_size   # Thread pool size
```

### Bookmaker Settings
```
bookmakers.<name>.enabled             # Enable/disable bookmaker
bookmakers.<name>.type                # api, exchange, etc.
bookmakers.<name>.api_key             # API credentials
bookmakers.<name>.username            # Login credentials
bookmakers.<name>.rate_limit_per_minute # API rate limit
bookmakers.<name>.max_stake_per_bet   # Stake limit
bookmakers.<name>.currency            # Trading currency
bookmakers.<name>.sports              # Supported sports list
```

### Notifications
```
notifications.email.enabled           # Enable email notifications
notifications.email.smtp_server       # SMTP server
notifications.email.to_addresses      # Recipient list
notifications.discord.enabled         # Enable Discord
notifications.discord.webhook_url     # Discord webhook
notifications.telegram.enabled        # Enable Telegram
notifications.telegram.bot_token      # Bot token
notifications.triggers.min_profit_margin # Alert threshold
```

### Logging
```
logging.level                         # DEBUG, INFO, WARNING, ERROR
logging.file                          # Log file path
logging.format                        # Log format string
logging.max_file_size                 # Max log file size
logging.backup_count                  # Backup files to keep
```

## Convenience Functions

```python
from arbitech.core.config_manager import (
    get_user_config, get_system_config, get_bookmaker_configs,
    get_risk_limits, get_scan_intervals, get_active_bookmakers,
    is_bookmaker_enabled
)

# Get configuration sections
user_config = get_user_config()          # Returns: {'risk': {...}}
system_config = get_system_config()      # Returns: {'vlm': {...}, ...}
bookmakers = get_bookmaker_configs()     # Returns: {'bet365': {...}, ...}

# Get specific settings
risk_limits = get_risk_limits()          # Returns risk configuration
scan_intervals = get_scan_intervals()    # Returns scan intervals
active_bookmakers = get_active_bookmakers()  # Returns list of enabled bookmakers

# Check specific settings
if is_bookmaker_enabled('bet365'):
    print("Bet365 is active")
```

## Configuration File Structure

```yaml
# config/config.yaml
user:
  risk:
    max_stake: 1000.0
    risk_percentage: 2.0
    min_odds: 1.5
    max_odds: 10.0

system:
  vlm:
    enabled: true
    endpoint: "http://localhost:8080/vlm"
  scan_intervals:
    general_scan: 60
    live_odds: 5
  performance:
    max_concurrent_scans: 10

bookmakers:
  bet365:
    enabled: true
    type: "api"
    api_key: null
    currency: "GBP"
    max_stake_per_bet: 500.0

notifications:
  email:
    enabled: false
    smtp_server: "smtp.gmail.com"
  triggers:
    min_profit_margin: 2.0
    enable_opportunity_alerts: true

logging:
  level: "INFO"
  file: "logs/arbitech.log"
  console: true
```

## Hot-Reload

```python
from arbitech.core.config_manager import get_config_manager, reload_config

# Get manager and register callback
manager = get_config_manager()

def on_config_change(old_config, new_config):
    print("Configuration changed!")

manager.register_callback(on_config_change)

# Manual reload
reload_config()

# File watching (automatic)
# Configuration reloads automatically when file changes
```

## Validation

```python
from arbitech.core.config_manager import init_config, ConfigError

try:
    init_config(config_path="config/config.yaml")
    print("✓ Configuration valid")
except ConfigError as e:
    print(f"❌ Configuration error: {e}")
```

## Common Patterns

### Risk Checking
```python
def check_opportunity_risk(stake, profit_margin):
    max_stake = get_config('user.risk.max_stake')
    min_profit = get_config('user.risk.min_profit_margin')
    
    return (stake <= max_stake and 
            profit_margin >= min_profit)
```

### Bookmaker Iteration
```python
active_bookmakers = get_active_bookmakers()

for bookmaker in active_bookmakers:
    if is_bookmaker_enabled(bookmaker):
        config = get_config(f'bookmakers.{bookmaker}')
        # Process bookmaker...
```

### Notification Setup
```python
def setup_notifications():
    email_enabled = get_config('notifications.email.enabled')
    discord_enabled = get_config('notifications.discord.enabled')
    
    if email_enabled:
        smtp_config = get_config('notifications.email')
        # Setup email...
    
    if discord_enabled:
        webhook_url = get_config('notifications.discord.webhook_url')
        # Setup Discord...
```

## Troubleshooting

### Configuration Not Loading
- Check file path: `config/config.yaml`
- Verify YAML syntax
- Check file permissions
- Ensure required sections exist

### Environment Variables Not Working
- Verify prefix: `ARBITECH_`
- Check double underscores for nested keys
- Restart application after setting
- Verify variable names match exactly

### Validation Errors
- Check data types (numbers, booleans, strings)
- Verify ranges (odds between 1.0-100.0, percentages 0-100)
- Ensure required fields present
- Check logical constraints (min < max)

### Hot-Reload Not Working
- Enable file watching: `watch_for_changes=True`
- Check file modification detection
- Verify callback registration
- Ensure write permissions

## Files Reference

| File | Description |
|------|-------------|
| `/workspace/arbitech/core/config_manager.py` | Main implementation |
| `/workspace/arbitech/config/config.yaml` | Sample configuration |
| `/workspace/arbitech/test_config.py` | Test suite |
| `/workspace/arbitech/example_usage.py` | Usage example |
| `/workspace/arbitech/core/README_config.md` | Full documentation |
| `/workspace/arbitech/IMPLEMENTATION_SUMMARY.md` | Implementation details |
