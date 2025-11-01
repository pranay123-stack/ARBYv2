# Bankroll and Limit Validation System

A comprehensive risk management system for safe arbitrage trading operations with real-time monitoring and enforcement.

## Overview

The Bankroll and Limit Validation System provides enterprise-grade risk management capabilities including:

- **Real-time bankroll validation** with balance tracking and exposure monitoring
- **Advanced limit management** with configurable rules per bookmaker, sport, market type, and risk tier
- **Exposure tracking** with correlation analysis and concentration monitoring  
- **Comprehensive validation pipeline** with pre-trade checks, real-time monitoring, and post-trade analysis
- **Circuit breakers** and emergency controls for risk protection
- **Detailed audit trails** for regulatory compliance

## Architecture

The system consists of four main components working together:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Validation     │    │  Bankroll       │    │  Limit          │    │  Exposure       │
│  Engine         │◄──►│  Validator      │◄──►│  Manager        │◄──►│  Tracker        │
│                 │    │                 │    │                 │    │                 │
│ Orchestrates    │    │ Real-time       │    │ Configurable    │    │ Correlation &   │
│ all validation  │    │ balance checks  │    │ rule engine     │    │ concentration   │
│ stages          │    │ & enforcement   │    │ & monitoring    │    │ analysis        │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Components

### 1. Bankroll Validator (`bankroll_validator.py`)

Real-time bankroll validation system with:

- **Current balance tracking** across all bookmaker accounts
- **Exposure monitoring** with automatic position sizing adjustments
- **Limit enforcement** across all active positions
- **Real-time reconciliation** of expected vs actual balances
- **Fault-tolerant operation** with automatic recovery mechanisms

#### Key Features:

- Thread-safe real-time monitoring
- Automatic balance update processing
- Position sizing adjustments to respect limits
- Balance discrepancy detection and alerting
- Performance metrics and reporting

#### Usage Example:

```python
from arbitech.risk import BankrollValidator
from arbitech.storage.models import RiskConfig

# Initialize validator
bankroll_validator = BankrollValidator(risk_config)

# Start monitoring
await bankroll_validator.start_monitoring()

# Validate bankroll state
validation_result = await bankroll_validator.validate_bankroll()
print(f"Bankroll valid: {validation_result.is_valid}")
print(f"Remaining capacity: ${validation_result.remaining_capacity}")

# Add trade to tracking
await bankroll_validator.add_trade(trade)

# Get comprehensive metrics
metrics = await bankroll_validator.get_bankroll_metrics()
```

### 2. Limit Manager (`limit_manager.py`)

Advanced limit management system with:

- **Configurable limit rules** per bookmaker, sport, market type, risk tier
- **Real-time usage tracking** with alert thresholds
- **Complex limit hierarchies** and dependencies
- **Custom rule engine** for business logic
- **Automatic position sizing** adjustments

#### Key Features:

- Rule-based limit engine with weights and conditions
- Real-time usage monitoring and alerting
- Support for time-based and rolling window limits
- Import/export functionality for rule management
- Comprehensive usage analytics and reporting

#### Usage Example:

```python
from arbitech.risk import LimitManager

# Initialize manager
limit_manager = LimitManager(risk_config)

# Check trade against limits
validation_result = await limit_manager.check_trade_limits(
    opportunity, proposed_stake, user_id
)

if validation_result["is_valid"]:
    # Record successful trade execution
    await limit_manager.record_trade_execution(trade)

# Add custom rule
custom_rule = LimitRule(
    name="Maximum Daily Tennis",
    limit_type=LimitType.MAX_DAILY_EXPOSURE,
    scope=LimitScope.SPORT,
    scope_value="tennis",
    value=Decimal('500')
)
limit_manager.add_custom_rule(custom_rule)

# Get usage report
report = await limit_manager.get_detailed_usage_report()
```

### 3. Exposure Tracker (`exposure_tracker.py`)

Real-time exposure tracking with:

- **Correlation analysis** between different exposure sources
- **Concentration monitoring** with risk-based alerts
- **Portfolio-level risk assessment** with VaR calculations
- **Position sizing recommendations** based on risk metrics
- **Historical trend analysis** for risk patterns

#### Key Features:

- Multi-dimensional exposure tracking (bookmaker, sport, market type)
- Real-time correlation calculations
- Concentration risk assessment with thresholds
- Value at Risk (VaR) and maximum drawdown calculations
- Diversification ratio and risk metrics

#### Usage Example:

```python
from arbitech.risk import ExposureTracker

# Initialize tracker
exposure_tracker = ExposureTracker()

# Add positions from trade
positions = await exposure_tracker.add_position(trade)

# Get exposure summary
summary = await exposure_tracker.get_exposure_summary()
print(f"Total exposure: ${summary['total_exposure']}")
print(f"Active positions: {summary['active_positions']}")

# Get correlation matrix
correlations = await exposure_tracker.get_correlation_matrix()
significant_corrs = correlations["significant_correlations"]

# Calculate position sizing
sizing = await exposure_tracker.calculate_position_sizing(
    proposed_exposure, ExposureType.BOOKMAKER, "bet365"
)
print(f"Recommended size: ${sizing['recommended_exposure']}")
```

### 4. Validation Engine (`validation_engine.py`)

Comprehensive validation pipeline orchestrating:

- **Pre-trade validation** with multi-stage checks
- **Real-time monitoring** with continuous validation
- **Post-trade analysis** for performance tracking
- **Circuit breaker activation** for emergency stops
- **Compliance validation** for regulatory requirements

#### Key Features:

- Multi-stage validation pipeline (Pre-trade, Real-time, Post-trade, Circuit breaker, Compliance)
- Configurable validation levels (Basic, Standard, Strict, Emergency)
- Rule-based validation with weighted scoring
- Real-time monitoring with event processing
- Emergency controls and circuit breakers

#### Usage Example:

```python
from arbitech.risk import ValidationEngine
from arbitech.risk.validation_engine import ValidationLevel

# Initialize engine
validation_engine = ValidationEngine(risk_config)

# Start monitoring
await validation_engine.start_monitoring()

# Comprehensive validation
validation_report = await validation_engine.validate_trade(
    opportunity, proposed_stake, user_id, ValidationLevel.STRICT
)

print(f"Overall score: {validation_report.overall_score}")
print(f"Risk assessment: {validation_report.risk_assessment.value}")
print(f"Rules passed: {validation_report.passed_rules}/{validation_report.total_rules}")

if validation_report.overall_score >= Decimal('0.5'):
    # Trade is acceptable
    execute_trade()
else:
    # Trade rejected
    print(f"Issues: {validation_report.critical_issues}")

# Emergency controls
await validation_engine.activate_emergency_stop()  # Halt all trading
await validation_engine.reset_circuit_breaker()   # Resume trading
```

## Integration with Existing Models

The system integrates seamlessly with the existing `ArbitrageOpportunity` and `Trade` models from Phase 1:

```python
# Uses existing models directly
from arbitech.storage.models import ArbitrageOpportunity, Trade, RiskConfig

# Risk configuration extends existing models
risk_config = RiskConfig(
    tier_a_settings=TierASettings(...),
    tier_b_settings=TierBSettings(...),
    global_limits=GlobalLimits(...),
    failsafes=Failsafes(...)
)

# Validation works with existing opportunity structure
validation_report = await validation_engine.validate_trade(
    opportunity,  # ArbitrageOpportunity instance
    proposed_stake,
    user_id
)

# Trade tracking uses existing Trade model
await bankroll_validator.add_trade(trade)  # Trade instance
```

## Configuration

### Risk Configuration

Configure risk parameters through the `RiskConfig` model:

```python
risk_config = RiskConfig(
    user_id=user_id,
    name="Conservative Strategy",
    description="Low-risk arbitrage with strict limits",
    
    # Tier-specific settings
    tier_a_settings=TierASettings(
        max_stake_per_trade=Decimal('100'),
        max_daily_exposure=Decimal('500'),
        min_profit_margin=Decimal('0.02'),
        max_concurrent_opportunities=3
    ),
    
    tier_b_settings=TierBSettings(
        max_stake_per_trade=Decimal('250'),
        max_daily_exposure=Decimal('1000'),
        min_profit_margin=Decimal('0.015'),
        max_concurrent_opportunities=5
    ),
    
    # Global constraints
    global_limits=GlobalLimits(
        max_total_exposure=Decimal('2000'),
        system_min_profit_margin=Decimal('0.01'),
        max_odds_age_minutes=30
    ),
    
    # Emergency failsafes
    failsafes=Failsafes(
        emergency_stop_loss=Decimal('200'),
        max_loss_per_hour=Decimal('100'),
        max_consecutive_losses=3,
        automatic_pause_threshold=Decimal('0.1')
    )
)
```

### Custom Limit Rules

Add custom validation rules:

```python
# Sport-specific limit
sport_rule = LimitRule(
    name="Maximum Tennis Daily",
    limit_type=LimitType.MAX_DAILY_EXPOSURE,
    scope=LimitScope.SPORT,
    scope_value="tennis",
    value=Decimal('500'),
    unit="currency",
    time_window=86400,  # 24 hours
    conditions={"sport": "tennis"}
)

# Bookmaker concentration limit
concentration_rule = LimitRule(
    name="Bookmaker Concentration",
    limit_type=LimitType.MAX_CONCENTRATION_RATIO,
    scope=LimitScope.GLOBAL,
    value=Decimal('0.3'),  # 30% maximum concentration
    unit="percentage",
    conditions={"max_ratio": Decimal('0.3')}
)

limit_manager.add_custom_rule(sport_rule)
limit_manager.add_custom_rule(concentration_rule)
```

## Real-time Monitoring

The system provides comprehensive real-time monitoring capabilities:

### Bankroll Monitoring

```python
# Start real-time monitoring
await bankroll_validator.start_monitoring()

# Monitor balance updates automatically
await bankroll_validator.update_balance("bet365", account_id, new_balance)

# Get current exposure breakdown
breakdown = await bankroll_validator.get_exposure_breakdown()
print(f"By bookmaker: {breakdown['by_bookmaker']}")
print(f"By sport: {breakdown['by_sport']}")
```

### Limit Monitoring

```python
# Real-time limit usage tracking
await limit_manager.check_trade_limits(opportunity, stake, user_id)

# Monitor limit alerts
alerts = limit_manager.get_recent_alerts()
for alert in alerts:
    if alert.severity == AlertSeverity.CRITICAL:
        handle_critical_alert(alert)

# Get limit usage summary
summary = await limit_manager.get_limit_summary()
print(f"Breached limits: {summary['breached_limits']}")
print(f"Active rules: {summary['active_rules']}")
```

### Exposure Monitoring

```python
# Real-time exposure tracking
await exposure_tracker.start_monitoring()

# Monitor concentration risks
concentration = await exposure_tracker.get_concentration_analysis()
for recommendation in concentration['recommendations']:
    if "CRITICAL" in recommendation:
        handle_concentration_risk(recommendation)

# Monitor correlations
correlations = await exposure_tracker.get_correlation_matrix()
high_correlations = [c for c in correlations["significant_correlations"] 
                    if abs(c["correlation"]) > 0.7]
```

### Validation Monitoring

```python
# Real-time validation pipeline
await validation_engine.start_monitoring()

# Monitor validation performance
summary = await validation_engine.get_validation_summary()
print(f"Validation success rate: {summary['performance_metrics']['success_rate']:.1%}")
print(f"Circuit breaker active: {summary['circuit_breaker']['is_active']}")

# Monitor recent validations
recent = summary['recent_validations'][-5:]
for validation in recent:
    if validation['risk_assessment'] in ['high', 'critical']:
        handle_high_risk_validation(validation)
```

## Circuit Breakers and Emergency Controls

The system includes comprehensive circuit breaker functionality:

### Automatic Circuit Breakers

```python
# Automatic triggers based on:
# - Multiple bankroll violations
# - Failsafe condition breaches
# - Excessive losses
# - System errors

# Circuit breaker activation
if len(bankroll_violations) >= 3:
    await validation_engine._trigger_circuit_breaker(
        "Multiple bankroll violations detected"
    )
```

### Manual Emergency Controls

```python
# Emergency stop (manual)
await validation_engine.activate_emergency_stop()
# Halts all trading immediately

# Reset circuit breaker
await validation_engine.reset_circuit_breaker()
# Allows trading to resume after cooldown
```

### Failsafe Conditions

```python
# Emergency stop loss
if daily_pnl <= -emergency_stop_loss:
    activate_circuit_breaker("Emergency stop loss breached")

# Maximum hourly loss
if hourly_loss <= -max_loss_per_hour:
    activate_circuit_breaker("Hourly loss limit exceeded")

# Consecutive losses
if consecutive_losses >= max_consecutive_losses:
    activate_circuit_breaker("Too many consecutive losses")
```

## Analytics and Reporting

The system provides comprehensive analytics:

### Performance Metrics

```python
# Bankroll metrics
metrics = await bankroll_validator.get_bankroll_metrics()
# - Total/exposed/available balance
# - Active positions count
# - Limit utilization
# - Validation performance

# Limit usage analytics
usage_report = await limit_manager.get_detailed_usage_report()
# - Usage by rule
# - Historical trends
# - Most hit rules
# - Alert frequency

# Exposure analytics
exposure_summary = await exposure_tracker.get_exposure_summary()
# - Concentration analysis
# - Correlation matrix
# - Risk metrics (VaR, Sharpe ratio)
# - Diversification ratio

# Validation analytics
validation_summary = await validation_engine.get_validation_summary()
# - Success rates
# - Rule performance
# - Processing times
# - Circuit breaker status
```

### Export Functionality

```python
# Export all system data for analysis
validation_data = await validation_engine.export_validation_data()
exposure_data = await exposure_tracker.export_exposure_data()
limit_data = await limit_manager.export_rules()

# Data includes:
# - Complete rule configurations
# - Historical validation results
# - Exposure tracking data
# - Correlation analysis
# - Performance metrics
# - Audit trails
```

## Fault Tolerance and Recovery

The system is designed for fault-tolerant operation:

### Automatic Recovery

- **Thread-safe operations** with proper locking mechanisms
- **Exception handling** with graceful degradation
- **Resource cleanup** on shutdown
- **State persistence** for critical data
- **Monitoring loop recovery** from errors

### Error Handling

```python
# Example error handling in validation
try:
    result = await validation_engine.validate_trade(opportunity, stake, user_id)
except Exception as e:
    # Log error
    logger.error(f"Validation failed: {e}")
    
    # Return safe default (reject trade)
    return ValidationReport(
        overall_score=Decimal('0'),
        risk_assessment=RiskAssessment.UNACCEPTABLE,
        critical_issues=[f"Validation system error: {str(e)}"]
    )
```

### Health Monitoring

```python
# System health checks
async def check_system_health():
    # Check component status
    bankroll_healthy = bankroll_validator._monitoring_active
    exposure_healthy = exposure_tracker._monitoring_active
    validation_healthy = validation_engine.monitoring_active
    
    # Check performance metrics
    avg_validation_time = validation_engine.average_validation_time_ms
    error_rate = validation_engine.failed_validations / max(validation_engine.total_validations, 1)
    
    return {
        "overall_healthy": bankroll_healthy and exposure_healthy and validation_healthy,
        "performance": {
            "avg_validation_time_ms": float(avg_validation_time),
            "error_rate": float(error_rate)
        }
    }
```

## Demonstration

Run the comprehensive demonstration:

```bash
cd /workspace/arbitech/risk
python demo_risk_system.py
```

The demo includes:
- Individual component testing
- Integration workflow demonstration
- Emergency control testing
- Data export examples
- Performance benchmarking

## Best Practices

### Configuration

1. **Conservative initial settings** - Start with strict limits and adjust based on performance
2. **Tier-based strategies** - Use different settings for different risk tiers
3. **Regular review** - Analyze performance and adjust limits periodically
4. **Backup configurations** - Maintain multiple config versions for different market conditions

### Monitoring

1. **Real-time alerts** - Set up notifications for critical events
2. **Regular health checks** - Monitor system performance and error rates
3. **Historical analysis** - Track patterns in limit breaches and violations
4. **Correlation tracking** - Monitor exposure correlations for diversification

### Emergency Procedures

1. **Circuit breaker testing** - Regularly test emergency stop functionality
2. **Recovery procedures** - Document steps for system recovery
3. **Communication protocols** - Establish notification procedures for emergencies
4. **Regular drills** - Practice emergency response procedures

## Integration Notes

### Dependencies

- Requires Phase 1 models from `arbitech.storage.models`
- Uses existing configuration system
- Integrates with logging and notification systems
- Compatible with async/await patterns

### Thread Safety

- All components are thread-safe with proper locking
- ThreadPoolExecutor used for CPU-intensive operations
- Async operations for I/O-bound tasks
- Proper resource cleanup on shutdown

### Performance

- Designed for high-frequency trading scenarios
- Sub-second validation times
- Efficient memory usage with bounded queues
- Scalable to multiple concurrent users

## Future Enhancements

- Machine learning-based risk assessment
- Advanced portfolio optimization
- Real-time market correlation analysis
- Automated limit adjustment based on performance
- Integration with external risk management systems
- Advanced scenario modeling and stress testing

---

This comprehensive risk management system provides enterprise-grade protection for arbitrage trading operations while maintaining the flexibility to adapt to changing market conditions and business requirements.