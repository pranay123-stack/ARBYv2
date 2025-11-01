# ARBITech Quick Start Guide

Get up and running with ARBITech arbitrage trading system in minutes!

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Basic Configuration](#basic-configuration)
4. [First Scan](#first-scan)
5. [Understanding Results](#understanding-results)
6. [Next Steps](#next-steps)

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8 or higher**
- **Git** (for cloning the repository)
- **Internet connection** (for API calls and data fetching)
- **Basic Python knowledge** (for customization)

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/arbitech.git
cd arbitech
```

### Step 2: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
python -c "import arbitech; print('ARBITech installed successfully!')"
```

## Basic Configuration

### Step 1: Create Configuration File

```bash
cp config/config.yaml.example config/config.yaml
```

### Step 2: Configure Bookmaker Accounts

Edit `config/config.yaml`:

```yaml
bookmakers:
  bet365:
    enabled: true
    api_key: "your_api_key_here"
    username: "your_username"
    password: "your_password"
    rate_limit: 10  # requests per minute
  
  william_hill:
    enabled: true
    api_key: "your_api_key_here"
    username: "your_username"
    password: "your_password"
    rate_limit: 5

detection:
  min_profit_margin: 0.02  # 2% minimum profit
  max_risk_tier: "TIER_A"  # Only safe trades
  scan_interval: 300       # 5 minutes
```

### Step 3: Test Configuration

```python
from core.config_manager import ConfigManager
config = ConfigManager()
if config.validate():
    print("Configuration is valid!")
else:
    print("Configuration errors found!")
```

## First Scan

### Simple Scan Example

```python
#!/usr/bin/env python3
"""
Your first ARBITech scan!
"""

import asyncio
from detection.opportunity_scanner import OpportunityScanner
from storage.supabase_layer import get_data_layer

async def main():
    print("🚀 Starting ARBITech...")
    
    # Initialize scanner
    scanner = OpportunityScanner()
    
    # Run scan
    print("🔍 Scanning for opportunities...")
    opportunities = await scanner.scan_markets(
        bookmakers=["bet365", "william_hill"],
        sports=["football", "basketball"],
        min_profit=0.02
    )
    
    # Display results
    print(f"\n✅ Found {len(opportunities)} opportunities:")
    
    for i, opp in enumerate(opportunities[:5], 1):  # Show first 5
        print(f"\n{i}. {opp.sport} - {opp.event}")
        print(f"   Profit: {opp.profit_margin:.2%}")
        print(f"   Risk: {opp.risk_tier}")
        print(f"   Stake: ${opp.required_stake:.2f}")
        print(f"   Expected Return: ${opp.expected_return:.2f}")
    
    if len(opportunities) > 5:
        print(f"\n... and {len(opportunities) - 5} more opportunities")

if __name__ == "__main__":
    asyncio.run(main())
```

### Run Your First Scan

```bash
python examples/first_scan.py
```

Expected output:
```
🚀 Starting ARBITech...
🔍 Scanning for opportunities...
✅ Found 3 opportunities:

1. Football - Manchester United vs Liverpool
   Profit: 2.5%
   Risk: TIER_A
   Stake: $100.00
   Expected Return: $102.50

2. Basketball - Lakers vs Warriors
   Profit: 3.1%
   Risk: TIER_A
   Stake: $150.00
   Expected Return: $154.65

3. Tennis - Djokovic vs Nadal
   Profit: 1.8%
   Risk: TIER_B
   Stake: $200.00
   Expected Return: $203.60

... and 0 more opportunities
```

## Understanding Results

### Opportunity Components

Each opportunity contains:

- **Sport & Event**: What sport and specific match/event
- **Profit Margin**: Expected profit percentage (e.g., 2.5%)
- **Risk Tier**: Safety level (TIER_A = safest, TIER_C = riskier)
- **Required Stake**: Total amount needed across all bookmakers
- **Expected Return**: Total amount you'll receive if successful

### Risk Tiers Explained

| Tier | Description | Max Risk Level |
|------|-------------|----------------|
| **TIER_A** | Lowest risk, highest confidence | Conservative limit |
| **TIER_B** | Moderate risk, good opportunities | Medium limit |
| **TIER_C** | Higher risk, maximum profit potential | Aggressive limit |

### Profit Calculation

```
Profit = (Sum of 1/Odds - 1) × 100

Example:
- Bookmaker A: Odds = 2.10 → 1/2.10 = 0.476
- Bookmaker B: Odds = 1.95 → 1/1.95 = 0.513
- Total: 0.476 + 0.513 = 0.989
- Profit: (0.989 - 1) × 100 = -1.1% (loss)

Better example:
- Bookmaker A: Odds = 2.05 → 1/2.05 = 0.488
- Bookmaker B: Odds = 2.00 → 1/2.00 = 0.500
- Total: 0.488 + 0.500 = 0.988
- Profit: (0.988 - 1) × 100 = -1.2% (still loss - need better odds!)
```

## Next Steps

### 1. Explore the Onboarding System

```bash
python docs/onboarding.py tutorial
```

This interactive tutorial will guide you through:
- System overview
- Component-specific features
- Best practices
- Troubleshooting

### 2. Configure Risk Management

```python
from risk.kelly_calculator import KellyCalculator
from risk.circuit_breaker import CircuitBreaker

# Set up Kelly Criterion for position sizing
kelly = KellyCalculator()
stake = kelly.calculate_stake(
    bankroll=1000,    # Your total bankroll
    edge=0.025,       # Your edge (2.5%)
    odds=2.0          # Average odds
)

# Set up circuit breakers
breaker = CircuitBreaker(
    max_daily_loss=100,
    max_drawdown=0.05,  # 5%
    max_concurrent_trades=3
)
```

### 3. Set Up Notifications

```python
from notifications.email_notifications import EmailNotifier
from notifications.telegram_bot import TelegramBot

# Email alerts
email_notifier = EmailNotifier()
await email_notifier.send_opportunity_alert(
    recipient="your@email.com",
    opportunity=opportunity
)

# Telegram bot alerts
telegram_bot = TelegramBot()
await telegram_bot.send_trade_alert(
    chat_id="your_chat_id",
    message=f"New opportunity: {opp.profit_margin:.2%} profit!"
)
```

### 4. Try Browser Automation

```python
from automation.arbitrage_executor import ArbitrageExecutor

# Execute trades automatically
executor = ArbitrageExecutor()
trade = await executor.execute_opportunity(
    opportunity=opportunity,
    dry_run=True  # Set to False for real trading
)

print(f"Trade executed: {trade.status}")
```

### 5. View Interactive Demos

Run these demos to explore features:

```bash
# Detection engine demo
python detection/demo_opportunity_scanner.py

# Risk management demo
python risk/demo_risk_system.py

# Browser automation demo
python automation/demo_arbitrage_executor.py

# Notifications demo
python notifications/demo_notifications.py
```

## Common Issues and Solutions

### Issue: "No opportunities found"

**Possible causes:**
- API credentials incorrect
- Rate limits exceeded
- Filter settings too strict

**Solutions:**
1. Check API credentials in config
2. Increase scan interval
3. Lower minimum profit threshold

### Issue: "Connection timeout"

**Possible causes:**
- Slow internet connection
- API server overloaded
- Network firewall blocking

**Solutions:**
1. Increase timeout values in config
2. Try again later
3. Check network settings

### Issue: "Invalid odds data"

**Possible causes:**
- Bookmaker API changes
- Data format mismatch
- Corrupted responses

**Solutions:**
1. Update bookmaker configurations
2. Check API documentation
3. Enable data validation

## Getting Help

### Documentation
- **Full User Manual**: `docs/onboarding.py` (interactive)
- **API Reference**: `docs/SUPABASE_API_REFERENCE.md`
- **Troubleshooting Guide**: `docs/TROUBLESHOOTING_GUIDE.md`

### Community
- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Ask questions and share tips
- **Discord**: Real-time chat with other users

### Support
- **Email**: support@arbitech.com
- **Documentation**: https://docs.arbitech.com
- **Status Page**: https://status.arbitech.com

## Congratulations! 🎉

You've successfully completed the ARBITech quick start guide. You now know how to:

- ✅ Install and configure ARBITech
- ✅ Run your first opportunity scan
- ✅ Understand scan results and risk tiers
- ✅ Set up basic risk management
- ✅ Configure notifications
- ✅ Troubleshoot common issues

### Next: Dive Deeper

Continue your journey with the interactive onboarding system:

```bash
python docs/onboarding.py tutorial --user-id your_username
```

Or explore specific components:

- **Detection**: Learn advanced scanning techniques
- **Risk Management**: Master Kelly Criterion and circuit breakers
- **Automation**: Set up fully automated trading
- **Analytics**: Build custom reporting and dashboards

Happy arbitrage trading! 📈