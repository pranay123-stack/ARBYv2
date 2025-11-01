# Advanced Kelly Criterion & Risk Management System

A sophisticated stake calculation system using Kelly criterion and advanced optimization algorithms for optimal position sizing in arbitrage betting.

## Overview

This system provides a comprehensive framework for bankroll management and position sizing through:

- **Kelly Calculator**: Advanced Kelly criterion implementation with fractional Kelly, dynamic adjustment, and portfolio-based optimization
- **Stake Optimizer**: Multi-strategy optimization including fixed-fractional, optimal f, risk parity, and custom algorithms
- **Position Sizer**: Professional position sizing with maximum position limits, diversification requirements, and correlation adjustment
- **Bankroll Manager**: Complete bankroll management with growth modeling, drawdown protection, and performance tracking

## Key Features

### 🔢 Mathematical Rigor
- High-precision decimal calculations for financial accuracy
- Proper statistical analysis with confidence intervals
- Portfolio optimization with correlation adjustments
- Dynamic risk modeling and adjustment

### 🎯 Multiple Optimization Strategies
- **Kelly Criterion**: Classic and fractional Kelly optimization
- **Risk Parity**: Equal risk contribution allocation
- **Maximum Sharpe**: Optimizes risk-adjusted returns
- **Minimum Variance**: Focuses on risk minimization
- **Fixed Fractional**: Simple percentage-based staking
- **Optimal F**: Ralph Vince's fixed ratio method

### 🛡️ Risk Management
- Drawdown protection with multiple levels
- Capital preservation mechanisms
- Position size limits and diversification requirements
- Liquidity constraints and market impact analysis
- Correlation-based position adjustments

### 📊 Performance Tracking
- Real-time performance metrics
- Growth projections and Monte Carlo simulations
- Comprehensive backtesting capabilities
- Detailed reporting and export functionality

## Installation

The system is built on Python with the following dependencies:

```bash
pip install numpy scipy pandas python-decimal
```

## Quick Start

### Basic Kelly Calculator Usage

```python
from decimal import Decimal
from risk.kelly_calculator import KellyCalculator, KellyConfig, KellyMode

# Configure calculator
config = KellyConfig(
    mode=KellyMode.FRACTIONAL,
    fractional_factor=Decimal('0.25')  # Quarter Kelly
)

calculator = KellyCalculator(config)

# Calculate optimal position size
kelly_result = calculator.calculate_classic_kelly(
    win_probability=Decimal('0.55'),
    odds=Decimal('2.1'),
    bankroll=Decimal('10000')
)

print(f"Optimal Kelly Fraction: {kelly_result.optimal_fraction:.2%}")
print(f"Recommended Stake: ${kelly_result.optimal_fraction * 10000:.2f}")
```

### Stake Optimization

```python
from risk.stake_optimizer import StakeOptimizer, OptimizationStrategy

# Configure optimizer
optimizer = StakeOptimizer(
    OptimizationConfig(strategy=OptimizationStrategy.MAXIMUM_SHARPE)
)

# Define opportunities
opportunities = [
    {
        'id': 'match_1',
        'win_probability': Decimal('0.58'),
        'odds': Decimal('1.9'),
        'confidence': Decimal('0.8')
    },
    {
        'id': 'match_2', 
        'win_probability': Decimal('0.62'),
        'odds': Decimal('1.75'),
        'confidence': Decimal('0.9')
    }
]

# Optimize stakes
result = optimizer.optimize_stakes(
    opportunities=opportunities,
    bankroll=Decimal('10000')
)

for opp_id, stake in result.optimal_stakes.items():
    print(f"{opp_id}: ${stake:.2f}")
```

### Position Sizing

```python
from risk.position_sizer import PositionSizer, SizingMethod, RiskLevel

# Configure position sizer
sizer = PositionSizer(
    PositionConfig(
        method=SizingMethod.KELLY_OPTIMAL,
        risk_level=RiskLevel.MODERATE,
        max_position_size=Decimal('0.05')  # 5% max per position
    )
)

# Calculate position size
opportunity = {
    'id': 'premium_match',
    'win_probability': Decimal('0.60'),
    'odds': Decimal('1.85'),
    'confidence': Decimal('0.9')
}

position_size = sizer.calculate_position_size(
    opportunity=opportunity,
    bankroll=Decimal('10000')
)

print(f"Recommended Stake: ${position_size.recommended_stake:.2f}")
print(f"Risk Score: {position_size.risk_score:.2f}")
print(f"Reasoning: {position_size.reasoning}")
```

### Bankroll Management

```python
from risk.bankroll_manager import BankrollManager, BankrollStrategy

# Configure bankroll manager
manager = BankrollManager(
    BankrollConfig(strategy=BankrollStrategy.KELLY_CRITERION)
)

# Calculate position size
opportunity = {'id': 'bet_1', 'win_probability': Decimal('0.58'), 'odds': Decimal('1.9')}
position_size = manager.calculate_position_size(opportunity)

# Simulate trade outcome
trade_result = {
    'opportunity_id': 'bet_1',
    'won': True,  # or False
    'profit_loss': position_size * (Decimal('1.9') - Decimal('1')),
    'timestamp': datetime.now()
}

# Update bankroll
manager.update_bankroll(trade_result)

# Generate performance report
report = manager.generate_performance_report()
print(f"Current Bankroll: ${report['summary']['current_bankroll']:,.2f}")
print(f"Total Return: {report['summary']['total_return']:+.1%}")
```

## Core Components

### KellyCalculator

**Purpose**: Calculate optimal Kelly fractions with advanced features

**Key Methods**:
- `calculate_classic_kelly()`: Standard Kelly calculation
- `calculate_fractional_kelly()`: Fractional Kelly with risk adjustment
- `calculate_multi_outcome_kelly()`: Multi-outcome scenarios
- `calculate_dynamic_kelly()`: Market condition adjustments
- `calculate_portfolio_kelly()`: Portfolio optimization
- `backtest_kelly_strategy()`: Historical backtesting

**Features**:
- Volatility adjustment
- Drawdown protection
- Correlation analysis
- Confidence intervals
- Transaction cost modeling

### StakeOptimizer

**Purpose**: Optimize stakes using multiple strategies

**Key Methods**:
- `optimize_stakes()`: Single strategy optimization
- `compare_strategies()`: Multi-strategy comparison
- Backtesting and validation

**Supported Strategies**:
- Fixed Fractional
- Optimal F (Ralph Vince)
- Risk Parity
- Kelly Criterion
- Maximum Sharpe Ratio
- Minimum Variance
- Maximum Utility

**Features**:
- Constraint handling
- Risk budgeting
- Portfolio optimization
- Strategy comparison

### PositionSizer

**Purpose**: Professional position sizing with risk controls

**Key Methods**:
- `calculate_position_size()`: Single position sizing
- `calculate_portfolio_sizes()`: Portfolio sizing
- `rebalance_positions()`: Portfolio rebalancing
- `assess_portfolio_risk()`: Risk assessment

**Features**:
- Maximum position limits
- Diversification requirements
- Liquidity constraints
- Correlation adjustments
- Real-time risk monitoring

### BankrollManager

**Purpose**: Complete bankroll management system

**Key Methods**:
- `calculate_position_size()`: Strategy-based sizing
- `update_bankroll()`: Trade tracking
- `generate_performance_report()`: Performance analysis
- `simulate_growth_scenarios()`: Monte Carlo simulation

**Features**:
- Multiple bankroll strategies
- Growth modeling
- Drawdown protection
- Capital preservation
- Performance tracking

## Configuration Options

### Kelly Configuration

```python
kelly_config = KellyConfig(
    mode=KellyMode.FRACTIONAL,           # Calculation mode
    fractional_factor=Decimal('0.25'),   # Fractional multiplier
    max_kelly_fraction=Decimal('0.5'),   # Maximum Kelly fraction
    volatility_adjustment=True,          # Volatility-based adjustment
    drawdown_threshold=Decimal('0.2'),   # Drawdown protection threshold
    confidence_level=Decimal('0.95')     # Confidence for intervals
)
```

### Optimization Configuration

```python
opt_config = OptimizationConfig(
    strategy=OptimizationStrategy.KELLY_CRITERION,  # Optimization strategy
    max_iterations=1000,                           # Optimization iterations
    tolerance=Decimal('1e-6'),                     # Convergence tolerance
    transaction_cost_rate=Decimal('0.005'),        # Transaction costs
    max_correlation=Decimal('0.7'),                # Correlation threshold
    risk_free_rate=Decimal('0.02')                 # Risk-free rate
)
```

### Position Sizing Configuration

```python
pos_config = PositionConfig(
    method=SizingMethod.KELLY_OPTIMAL,          # Sizing method
    risk_level=RiskLevel.MODERATE,              # Risk tolerance
    max_position_size=Decimal('0.1'),           # Max position % of bankroll
    min_position_size=Decimal('0.001'),         # Min position % of bankroll
    max_total_exposure=Decimal('0.8'),          # Max total exposure
    correlation_threshold=Decimal('0.7'),       # Correlation limit
    max_liquidity_utilization=Decimal('0.1')    # Liquidity utilization
)
```

### Bankroll Management Configuration

```python
bankroll_config = BankrollConfig(
    strategy=BankrollStrategy.KELLY_CRITERION,   # Bankroll strategy
    initial_bankroll=Decimal('10000'),           # Starting bankroll
    kelly_fraction=Decimal('0.25'),              # Fractional Kelly factor
    drawdown_levels=[                           # Drawdown protection levels
        Decimal('0.05'), Decimal('0.10'), 
        Decimal('0.15'), Decimal('0.20')
    ],
    preservation_mode=CapitalPreservationMode.MODERATE,
    emergency_stop_loss=Decimal('0.25')          # Emergency stop loss
)
```

## Advanced Features

### Portfolio Optimization

The system can optimize across multiple opportunities considering:

- **Correlation Analysis**: Adjusts positions based on opportunity correlations
- **Risk Parity**: Equalizes risk contributions across positions
- **Diversification**: Ensures adequate portfolio diversification
- **Constraint Handling**: Respects position limits and exposure caps

### Dynamic Adjustments

Real-time adjustments based on:

- **Market Volatility**: Adjusts position sizes for volatile markets
- **Performance History**: Modifies strategy based on recent performance
- **Drawdown Protection**: Reduces sizes during losing streaks
- **Liquidity Conditions**: Considers market liquidity in sizing

### Risk Modeling

Comprehensive risk assessment:

- **Value at Risk (VaR)**: 95% and 99% VaR calculations
- **Maximum Drawdown**: Historical and projected drawdown analysis
- **Sharpe Ratio**: Risk-adjusted return metrics
- **Correlation Risk**: Portfolio correlation analysis

### Monte Carlo Simulation

Growth projections using Monte Carlo methods:

```python
scenarios = [
    {
        'name': 'optimistic',
        'probability': Decimal('0.3'),
        'win_rate': Decimal('0.65'),
        'avg_odds': Decimal('2.0')
    },
    {
        'name': 'realistic', 
        'probability': Decimal('0.5'),
        'win_rate': Decimal('0.55'),
        'avg_odds': Decimal('1.9')
    },
    {
        'name': 'conservative',
        'probability': Decimal('0.2'),
        'win_rate': Decimal('0.50'),
        'avg_odds': Decimal('1.8')
    }
]

results = manager.simulate_growth_scenarios(scenarios, time_horizon=365)

for scenario, path in results.items():
    final_value = path[-1]
    print(f"{scenario}: ${final_value:,.2f}")
```

## Performance Metrics

The system tracks comprehensive performance metrics:

### Return Metrics
- Total return
- Annualized return
- Risk-adjusted return (Sharpe, Sortino, Calmar ratios)

### Risk Metrics
- Maximum drawdown
- Value at Risk (VaR)
- Volatility
- Correlation metrics

### Trading Metrics
- Win rate
- Profit factor
- Average win/loss
- Consecutive wins/losses

### Portfolio Metrics
- Diversification ratio
- Concentration risk
- Portfolio VaR
- Asset allocation efficiency

## Best Practices

### Risk Management
1. **Start Conservative**: Use fractional Kelly (0.25-0.5x) initially
2. **Monitor Drawdowns**: Activate protection at 5-10% drawdown
3. **Diversify Positions**: Avoid concentration in single opportunities
4. **Track Performance**: Regular performance review and strategy adjustment

### Position Sizing
1. **Respect Limits**: Never exceed maximum position size constraints
2. **Consider Liquidity**: Account for market liquidity in position sizing
3. **Correlation Awareness**: Reduce positions in highly correlated opportunities
4. **Rebalance Regularly**: Rebalance portfolio every 10-20 trades

### Bankroll Management
1. **Emergency Stops**: Set emergency stop loss at 20-25% drawdown
2. **Performance Review**: Regular review of strategy performance
3. **Growth Projections**: Use Monte Carlo for realistic expectations
4. **Capital Preservation**: Prioritize capital preservation during downturns

## Integration with Detection Engine

The system integrates seamlessly with the arbitrage detection engine:

```python
# Get opportunities from detection engine
opportunities = detection_engine.find_opportunities()

# Optimize stakes using Kelly criterion
kelly_calc = KellyCalculator()
portfolio_result = kelly_calc.calculate_portfolio_kelly(
    opportunities, bankroll
)

# Apply position sizing with constraints
sizer = PositionSizer()
position_sizes = sizer.calculate_portfolio_sizes(
    opportunities, bankroll, 
    market_data=detection_engine.get_market_data()
)

# Manage bankroll with tracking
manager = BankrollManager()
for opp_id, size in position_sizes.items():
    # Execute bet...
    manager.update_bankroll(trade_result)
```

## Example Usage Scenarios

### Conservative Approach
```python
# Low-risk configuration
config = KellyConfig(
    mode=KellyMode.FRACTIONAL,
    fractional_factor=Decimal('0.125'),  # Eighth Kelly
    max_kelly_fraction=Decimal('0.25')   # Cap at 25%
)

manager = BankrollManager(BankrollConfig(
    strategy=BankrollStrategy.FIXED_FRACTION,
    base_fraction=Decimal('0.01'),       # 1% fixed
    preservation_mode=CapitalPreservationMode.CONSERVATIVE
))
```

### Aggressive Approach
```python
# Higher-risk configuration
config = KellyConfig(
    mode=KellyMode.DYNAMIC,
    fractional_factor=Decimal('0.5'),    # Half Kelly
    volatility_adjustment=True
)

manager = BankrollManager(BankrollConfig(
    strategy=BankrollStrategy.KELLY_CRITERION,
    kelly_fraction=Decimal('0.5'),
    preservation_mode=CapitalPreservationMode.AGGRESSIVE
))
```

### Portfolio Approach
```python
# Multi-opportunity optimization
optimizer = StakeOptimizer(OptimizationConfig(
    strategy=OptimizationStrategy.MAXIMUM_SHARPE,
    objective_weights={
        'return': Decimal('0.4'),
        'risk': Decimal('0.3'),
        'diversification': Decimal('0.2'),
        'liquidity': Decimal('0.1')
    }
))

result = optimizer.optimize_stakes(opportunities, bankroll)
```

## Mathematical Foundation

### Kelly Criterion Formula

For a single opportunity:
```
f* = (bp - q) / b

Where:
f* = Kelly fraction
b = odds - 1
p = win probability
q = 1 - p = lose probability
```

### Fractional Kelly

```
f_frac = f* × α

Where α is the fractional multiplier (typically 0.25-0.5)
```

### Portfolio Kelly

For multiple opportunities with correlations:
```
Maximize: Σᵢ fᵢ × (pᵢ × bᵢ - (1 - pᵢ))
Subject to: Σᵢ fᵢ ≤ 1, correlation constraints
```

### Risk Metrics

**Value at Risk (VaR)**: 
```
VaR₉₅ = z₀.₉₅ × σ × √t
```

**Sharpe Ratio**:
```
Sharpe = (Rₚ - Rբ) / σₚ

Where:
Rₚ = portfolio return
Rբ = risk-free rate  
σₚ = portfolio volatility
```

## Testing and Validation

Run the comprehensive demo to test all components:

```bash
python kelly_criterion_demo.py
```

The demo includes:
- Individual component testing
- Integration scenarios
- Performance validation
- Risk assessment
- Export functionality

## Error Handling

The system includes robust error handling:

- Input validation for all mathematical operations
- Graceful fallback for optimization failures
- Comprehensive logging and monitoring
- Emergency stop mechanisms

## Performance Considerations

- Decimal precision: 50 decimal places for financial accuracy
- Efficient algorithms: Optimized for real-time calculation
- Memory management: Minimal memory footprint
- Scalability: Handles large opportunity portfolios

## Limitations

- Assumes independence for simplified calculations (correlation adjustments available)
- Historical performance may not predict future results
- Market liquidity constraints are simplified
- Transaction costs are approximated

## Future Enhancements

- Machine learning integration for dynamic parameter adjustment
- Real-time market data integration
- Advanced correlation modeling
- Options-based hedging strategies
- Multi-timeframe analysis

## Support and Documentation

- Comprehensive docstrings in all modules
- Example usage in demo script
- Mathematical derivations in comments
- Configuration validation

## License

This system is part of the Arbitech arbitrage betting platform.

---

**Disclaimer**: This system is for educational and research purposes. Always practice proper risk management and never bet more than you can afford to lose. Past performance does not guarantee future results.