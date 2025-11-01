# Paper Trading System Documentation

A sophisticated paper trading environment for arbitrage betting that provides realistic simulation of all trading aspects without risking real money.

## 🎯 Features

### Core Capabilities
- **Virtual Trading Environment**: Realistic market data simulation with configurable volatility
- **Virtual Bankroll Management**: Multi-bookmaker accounts with realistic constraints
- **Simulated Execution**: Realistic slippage, delays, and execution failures
- **Backtesting Engine**: Historical data analysis with performance metrics
- **Virtual Bookmaker Accounts**: Complete simulation of account management
- **Performance Analytics**: Comprehensive tracking and reporting
- **Mode Switching**: Paper, Live, Backtest, and Hybrid modes
- **Phase Integration**: Seamless integration with ARBitech phases 3-9

### Advanced Features
- **Risk Tier Simulation**: Realistic risk-based constraints
- **Market Condition Modeling**: Stable, volatile, high/low liquidity scenarios
- **Execution Quality Metrics**: Slippage, latency, and success rate tracking
- **Multi-Sport Support**: Football, Basketball, Tennis, Baseball, and more
- **Concurrent Processing**: High-volume opportunity processing
- **Export Capabilities**: JSON, CSV, and Excel export formats
- **Comprehensive Logging**: Detailed audit trails and error tracking

## 📁 File Structure

```
/workspace/arbitech/testing/
├── paper_trading.py              # Main paper trading system
├── demo_paper_trading.py         # Comprehensive demonstrations
├── test_paper_trading.py         # Test suite
├── paper_trading_config.json     # Configuration file
└── README_paper_trading.md       # This documentation
```

## 🚀 Quick Start

### Basic Usage

```python
from paper_trading import create_paper_trading_system, load_sample_opportunities
import asyncio

async def main():
    # Create paper trading system
    system = create_paper_trading_system(
        mode=TradingMode.PAPER,
        initial_bankroll=Decimal('100000.00')
    )
    
    # Start simulation
    await system.start_paper_trading()
    
    # Load sample opportunities
    opportunities = load_sample_opportunities(10)
    
    # Process opportunities
    for opportunity in opportunities:
        trade = await system.process_opportunity(
            opportunity, 
            user_id=uuid4()
        )
        print(f"Trade {trade.status}: ${trade.actual_profit or 0}")
    
    # Generate report
    report = system.get_performance_report()
    print(f"Win Rate: {report['performance_metrics']['win_rate']:.1f}%")
    
    # Stop simulation
    await system.stop_paper_trading()

asyncio.run(main())
```

### Running Demonstrations

```bash
# Full paper trading demonstration
python demo_paper_trading.py full

# Backtesting demonstration
python demo_paper_trading.py backtest

# Hybrid mode demonstration
python demo_paper_trading.py hybrid

# Performance analytics demonstration
python demo_paper_trading.py performance
```

### Running Tests

```bash
# Run all tests
python test_paper_trading.py all

# Run specific test suite
python test_paper_trading.py unit
python test_paper_trading.py integration
python test_paper_trading.py performance
```

## 📊 Trading Modes

### Paper Trading Mode
- **Purpose**: Safe testing and strategy validation
- **Features**: Real-time simulation, no real money risk
- **Use Case**: New strategy testing, parameter optimization

### Live Trading Mode
- **Purpose**: Real money trading with paper safety net
- **Features**: Real execution with simulated backup
- **Use Case**: Gradual transition to live trading

### Backtest Mode
- **Purpose**: Historical performance analysis
- **Features**: Historical data replay, performance metrics
- **Use Case**: Strategy validation, parameter tuning

### Hybrid Mode
- **Purpose**: Combination of paper and live trading
- **Features**: Dynamic mode switching based on performance
- **Use Case**: Risk-managed transition to live trading

## 🏢 Virtual Bookmaker Accounts

### Supported Bookmakers
- **Premium**: Pinnacle, Betfair
- **Standard**: William Hill, Bet365, Unibet, 888Sport
- **US Market**: DraftKings, FanDuel
- **European**: Betway, Casumo, LeoVegas, MrGreen

### Account Features
- **Balance Management**: Starting balances, daily limits
- **Volume Tracking**: Daily, weekly, monthly volumes
- **Risk Tiers**: Tier A (lowest) to Tier D (highest risk)
- **Transaction History**: Complete audit trail
- **Limit Enforcement**: Realistic betting constraints

### Account Configuration

```python
# Create custom account
account = VirtualBankrollAccount(
    bookmaker="Custom Bookmaker",
    balance=Decimal('25000.00'),
    daily_limit=Decimal('10000.00'),
    weekly_limit=Decimal('50000.00'),
    monthly_limit=Decimal('200000.00'),
    risk_tier=RiskTier.TIER_B
)

# Check if bet can be placed
can_bet, reason = account.can_place_bet(Decimal('5000.00'))
if can_bet:
    account.reserve_balance(Decimal('5000.00'))
```

## 🎯 Opportunity Processing

### Arbitrage Opportunity Structure

```python
opportunity = ArbitrageOpportunity(
    id=uuid4(),
    sport=Sport.FOOTBALL,
    event_id="match_123",
    profit_margin=Decimal('0.025'),  # 2.5% profit
    legs=[
        ArbitrageLeg(
            id=uuid4(),
            sport=Sport.FOOTBALL,
            event_id="match_123",
            bookmaker="Pinnacle",
            odds=Decimal('2.10'),
            suggested_stake=Decimal('500.00'),
            risk_tier=RiskTier.TIER_A
        ),
        # More legs...
    ],
    risk_tier=RiskTier.TIER_A,
    detection_timestamp=datetime.now(),
    quality_score=Decimal('0.85')
)
```

### Processing Workflow

1. **Risk Validation**: Check bankroll, limits, constraints
2. **Decision Making**: AI/rule-based trading decisions
3. **HITL Approval**: Simulated human approval process
4. **Trade Execution**: Realistic execution simulation
5. **Settlement**: Profit/loss calculation
6. **Performance Tracking**: Metrics and analytics update

## 📈 Performance Analytics

### Key Metrics
- **Financial Performance**: ROI, Net Profit, Win Rate
- **Execution Quality**: Slippage, Latency, Success Rate
- **Risk Metrics**: Drawdown, Exposure, Risk-Adjusted Returns
- **Time Analysis**: Performance by hour, day, month
- **Sport Analysis**: Performance breakdown by sport
- **Bookmaker Analysis**: Performance by bookmaker

### Report Generation

```python
# Generate comprehensive report
report = system.get_performance_report()

print(f"Total Trades: {report['performance_metrics']['total_trades']}")
print(f"Win Rate: {report['performance_metrics']['win_rate']:.1f}%")
print(f"Net Profit: ${report['performance_metrics']['net_profit']:,.2f}")
print(f"ROI: {report['performance_metrics']['roi_percentage']:.2f}%")

# Export trade history
system.export_trade_history("trades.json", format="json")
system.export_trade_history("trades.csv", format="csv")
```

### Account Summary

```python
# Get detailed account summary
summary = system.get_account_summary()

print(f"Total Accounts: {summary['total_accounts']}")
print(f"Available Balance: ${summary['total_available_balance']:,.2f}")

for bookmaker, account_data in summary['accounts'].items():
    print(f"{bookmaker}: ${account_data['available']:,.2f} available")
```

## 🔄 Market Simulation

### Market Conditions
- **Stable**: Normal market conditions (2% volatility)
- **Volatile**: High price movement (5% volatility)
- **High Liquidity**: Large volume, tight spreads (0.7x delay multiplier)
- **Low Liquidity**: Small volume, wide spreads (3x delay multiplier)
- **Changing Rapidly**: Rapid price changes (4x delay multiplier)

### Simulation Parameters

```python
# Configure market simulation
system.market_simulator.volatility_level = 0.03  # 3% volatility
system.market_simulator.price_drift = Decimal('0.0002')  # Price drift
system.market_simulator.change_probability = 0.20  # 20% change probability

# Simulate market event
system.simulate_market_event(MarketCondition.VOLATILE, duration_minutes=30)
```

## ⚡ Execution Simulation

### Slippage Modeling
- **Base Slippage**: 0.5% base rate
- **Odds Factor**: Lower odds = higher slippage risk
- **Stake Factor**: Larger stakes = higher slippage
- **Market Condition**: Volatile markets = higher slippage
- **Bookmaker Factor**: Individual bookmaker characteristics

### Delay Simulation
- **Base Latency**: 50ms base delay
- **Mode Multipliers**: Manual (5x), Auto (1x), Simulated (0.1x)
- **Condition Multipliers**: Stable (1x), Volatile (2x), Low Liquidity (3x)
- **Random Variance**: ±20% random variation

### Failure Simulation
- **Base Failure Rate**: 2% execution failure rate
- **Market Conditions**: Volatile markets increase failure rate
- **Risk Tiers**: Higher tiers have higher failure rates
- **Account Limits**: Limit violations cause failures

## 🔍 Backtesting

### Data Requirements
- **Required Columns**: sport, event_id, bookmaker, odds, timestamp
- **Supported Formats**: CSV, JSON, DataFrame
- **Time Range**: Configurable start/end dates
- **Data Quality**: Validation and cleaning

### Backtest Execution

```python
# Load historical data
system.load_backtest_data("historical_data.csv")

# Run backtest
results = await system.run_backtest(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 12, 31),
    min_profit_margin=Decimal('0.02')
)

print(f"Total Trades: {results['total_trades']}")
print(f"ROI: {results['roi']:.2f}%")
print(f"Win Rate: {results['win_rate']:.1f}%")
```

### Backtest Results
- **Trade Statistics**: Total, profitable, losing trades
- **Financial Metrics**: ROI, total profit, average profit per trade
- **Risk Metrics**: Best/worst trade, drawdown analysis
- **Execution Quality**: Slippage impact, execution time statistics

## 🔧 Configuration

### Configuration File
```json
{
  "virtual_bookmakers": ["Pinnacle", "Bet365", "William Hill"],
  "initial_account_balances": {
    "default": 10000.00,
    "premium": 25000.00
  },
  "execution_settings": {
    "enable_slippage": true,
    "enable_delays": true,
    "enable_failures": true,
    "max_concurrent_trades": 10
  },
  "performance_tracking": {
    "save_trade_history": true,
    "export_metrics": true,
    "generate_reports": true
  }
}
```

### Custom Configuration Usage
```python
system = PaperTradingSystem(
    mode=TradingMode.PAPER,
    initial_bankroll=Decimal('100000.00'),
    config_path="custom_config.json"
)
```

## 🧪 Testing

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Workflow and system integration
- **Performance Tests**: Speed and memory usage
- **Stress Tests**: High-volume processing
- **Error Handling**: Edge case and error scenarios

### Running Tests
```bash
# All tests
python test_paper_trading.py all

# Specific categories
python test_paper_trading.py unit
python test_paper_trading.py integration
python test_paper_trading.py performance
```

### Test Coverage
- System initialization and configuration
- Virtual account management
- Market and execution simulation
- Opportunity processing workflow
- Performance metrics calculation
- Data export and reporting
- Error handling and edge cases
- Concurrent processing
- Memory and performance optimization

## 🔌 Integration with ARBitech Phases

### Phase 3: Arbitrage Detection Engine
```python
# Integrate with opportunity scanner
system.integrate_opportunity_scanner(scanner)
opportunities = await scanner.scan_for_opportunities()
```

### Phase 4: Risk Management System
```python
# Integrate with bankroll manager
system.integrate_bankroll_manager(manager)
risk_validated = await manager.validate_trade(opportunity)
```

### Phase 5: Human-in-the-Loop
```python
# Simulated approval process
approved = await system._simulate_hitl_approval(opportunity)
```

### Phase 6: Browser Automation
```python
# Simulated browser execution
execution = await system._execute_single_leg(leg, trade)
```

### Phase 7: Decision Engine
```python
# Integrate with AI decision making
system.integrate_decision_engine(engine)
decision = await engine.should_trade(opportunity)
```

### Phase 8: Automation
```python
# Automated execution simulation
await system._execute_arbitrage_trade(paper_trade)
```

### Phase 9: Notification System
```python
# Integrate with Telegram bot
system.integrate_telegram_bot(bot)
await bot.send_trade_notification(trade)
```

## 🎛️ Advanced Usage

### Custom Market Simulation
```python
class CustomMarketSimulator(MarketSimulator):
    def __init__(self):
        super().__init__()
        self.custom_volatility = 0.04
        
    def simulate_odds_movement(self, odds, bookmaker, sport):
        # Custom logic here
        return super().simulate_odds_movement(odds, bookmaker, sport)

# Replace default simulator
system.market_simulator = CustomMarketSimulator()
```

### Custom Execution Simulation
```python
class CustomExecutionSimulator(ExecutionSimulator):
    def should_fail_execution(self, market_condition, risk_tier):
        # Custom failure logic
        base_rate = 0.01  # 1% base failure rate
        return random.random() < base_rate

# Replace default simulator
system.execution_simulator = CustomExecutionSimulator()
```

### Performance Monitoring
```python
# Add custom performance tracking
class CustomMetrics(PerformanceMetrics):
    def __init__(self):
        super().__init__()
        self.custom_metric = Decimal('0.00')
    
    def update_custom_metric(self, value):
        self.custom_metric = value

# Replace default metrics
system.performance_metrics = CustomMetrics()
```

## 📊 Logging and Monitoring

### Logging Configuration
```python
import logging

# Set up custom logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('paper_trading.log'),
        logging.StreamHandler()
    ]
)

# Get system logger
logger = system.logger
logger.info("Custom log message")
```

### Status Monitoring
```python
# Get real-time status
status = system.get_simulation_status()

print(f"Running: {status['is_running']}")
print(f"Mode: {status['mode']}")
print(f"Total Trades: {status['total_trades']}")
print(f"Current ROI: {status['performance_summary']['roi']:.2f}%")
```

## 🚨 Error Handling

### Common Error Scenarios
- **Insufficient Balance**: Account balance too low
- **Limit Exceeded**: Daily/weekly/monthly limits hit
- **Invalid Opportunity**: Malformed arbitrage opportunity
- **Network Errors**: Simulated connection issues
- **Execution Failures**: Bookmaker rejection or timeout

### Error Recovery
```python
try:
    trade = await system.process_opportunity(opportunity, user_id)
except Exception as e:
    logger.error(f"Processing failed: {e}")
    # Implement fallback logic
```

### Retry Logic
```python
async def process_with_retry(system, opportunity, user_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            trade = await system.process_opportunity(opportunity, user_id)
            if trade.status != PaperTradeStatus.FAILED:
                return trade
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
    
    return None
```

## 🔒 Security and Best Practices

### Data Protection
- No real financial data stored
- Virtual accounts with no real money
- Complete audit trails for transparency
- Secure configuration file handling

### Performance Optimization
- Async/await for concurrent processing
- Memory-efficient trade storage
- Configurable data retention policies
- Export old data to prevent memory bloat

### Code Quality
- Comprehensive type hints
- Extensive docstring documentation
- Unit and integration test coverage
- Error handling and logging

## 🤝 Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `python test_paper_trading.py all`
4. Run demos: `python demo_paper_trading.py full`

### Code Standards
- Follow PEP 8 style guidelines
- Add comprehensive docstrings
- Include unit tests for new features
- Update documentation for changes

### Testing Guidelines
- Unit tests for all public methods
- Integration tests for workflows
- Performance tests for optimization
- Error handling test coverage

## 📝 License

This paper trading system is part of the ARBitech Framework and follows the same licensing terms.

## 🆘 Support

For questions, issues, or contributions:
1. Check the test suite for usage examples
2. Review the demo scripts for complete workflows
3. Examine the configuration file for customization options
4. Run tests to validate system functionality

---

**Happy Paper Trading! 🎯📈**