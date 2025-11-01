# ARBitech Supabase Integration Guide

Complete data storage and integration system for the ARBitech autonomous arbitrage trading platform.

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup and Configuration](#setup-and-configuration)
4. [Data Persistence Layer](#data-persistence-layer)
5. [Edge Functions](#edge-functions)
6. [Real-time Subscriptions](#real-time-subscriptions)
7. [Storage Buckets](#storage-buckets)
8. [Usage Examples](#usage-examples)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Overview

The ARBitech Supabase integration provides:

- **Comprehensive Database Schema**: 16+ tables covering opportunities, trades, risk configs, HITL decisions, autonomous decisions, circuit breakers, and more
- **Data Persistence Layer**: Python module (`supabase_layer.py`) for seamless integration with existing ARBitech infrastructure
- **Edge Functions**: 4 serverless functions for automated workflows (opportunity processing, reporting, monitoring, notifications)
- **Storage Buckets**: 3 buckets for screenshots, logs, and documents
- **Real-time Subscriptions**: Live dashboard updates for opportunities and trade status
- **Row-Level Security**: Multi-tenant architecture with user isolation

## Architecture

### Database Schema

```
├── User Management
│   └── profiles - User profiles and preferences
├── Trading Core
│   ├── arbitrage_opportunities - Discovered opportunities
│   ├── arbitrage_legs - Betting legs for each opportunity
│   ├── trades - Trade execution records
│   ├── bookmaker_accounts - User bookmaker credentials
│   └── market_data_snapshots - Historical market data
├── Risk Management
│   ├── risk_configs - User/system risk configurations
│   ├── risk_alerts - Risk monitoring alerts
│   └── circuit_breaker_events - Emergency stop events
├── Decision Tracking
│   ├── hitl_decisions - Human-in-the-loop decisions
│   └── autonomous_decisions - AI system decisions
├── Operations
│   ├── scanner_sessions - Discovery session tracking
│   ├── execution_logs - Trade execution logs
│   ├── notifications - User notifications
│   └── performance_metrics - Performance analytics
└── Audit
    └── audit_trail - Complete audit log
```

### Edge Functions

1. **process-opportunity**: Analyzes opportunities with risk scoring and validation
2. **generate-report**: Creates performance reports and metrics
3. **monitor-system**: Monitors system health and circuit breakers (cron)
4. **send-notification**: Delivers notifications via multiple channels

### Storage Buckets

- `arbitech-screenshots`: Trading screenshots (10MB limit, PNG/JPEG)
- `arbitech-logs`: System logs (50MB limit, JSON/TXT/CSV)
- `arbitech-documents`: Trade documents (10MB limit, PDF/JSON)

## Setup and Configuration

### 1. Environment Variables

Set the following environment variables:

```bash
export SUPABASE_URL="https://apailklayaphzswnxgya.supabase.co"
export SUPABASE_ANON_KEY="your_anon_key_here"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key_here"
```

### 2. Install Python Dependencies

```bash
cd /workspace/arbitech
pip install supabase-py
```

### 3. Initialize Data Layer

```python
from storage.supabase_layer import get_data_layer

# Initialize the data layer
data_layer = get_data_layer()
```

## Data Persistence Layer

The `SupabaseDataLayer` class in `storage/supabase_layer.py` provides a comprehensive interface for all database operations.

### Key Features

- Asynchronous operations for better performance
- Type-safe integration with Pydantic models
- Automatic error handling and logging
- Real-time subscription management
- Storage operations for files

### Core Methods

#### Opportunities

```python
# Save an opportunity
await data_layer.save_opportunity(opportunity)

# Retrieve opportunities with filters
opportunities = data_layer.get_opportunities(
    sport=Sport.FOOTBALL,
    risk_tier=RiskTier.TIER_A,
    min_profit_margin=0.02,
    limit=50
)

# Get legs for an opportunity
legs = data_layer.get_opportunity_legs(opportunity_id)
```

#### Trades

```python
# Create a trade
await data_layer.create_trade(trade)

# Update trade status
await data_layer.update_trade_status(
    trade_id,
    TradeStatus.FILLED,
    additional_data={'actual_profit': 15.50}
)

# Get user trades
trades = data_layer.get_user_trades(
    user_id,
    status=TradeStatus.FILLED,
    limit=100
)
```

#### HITL Decisions

```python
# Log a human decision
await data_layer.log_hitl_decision(
    opportunity_id=opp_id,
    user_id=user_id,
    decision='approved',
    decision_reason='High confidence, low risk',
    risk_summary={'risk_score': 0.15},
    opportunity_snapshot=opp_data
)
```

#### Autonomous Decisions

```python
# Log an AI decision
await data_layer.log_autonomous_decision(
    opportunity_id=opp_id,
    decision='execute',
    confidence_score=0.95,
    reasoning={'factors': ['high_profit', 'low_risk']},
    risk_score=0.12,
    risk_factors=['market_volatility']
)
```

#### Risk Alerts

```python
# Create a risk alert
await data_layer.create_risk_alert(
    alert_type='market_volatility_spike',
    severity='high',
    title='High Volatility Detected',
    description='Market volatility exceeded threshold',
    user_id=user_id,
    risk_metrics={'volatility': 0.15},
    recommended_action='Review open positions'
)

# Get unresolved alerts
alerts = data_layer.get_unresolved_alerts(
    user_id=user_id,
    min_severity='medium'
)
```

#### Circuit Breakers

```python
# Log circuit breaker event
await data_layer.log_circuit_breaker_event(
    breaker_type='max_loss_per_hour',
    trigger_value=250.0,
    threshold_value=200.0,
    description='Hourly loss limit exceeded',
    affected_operations=['trading', 'autonomous_execution']
)
```

#### Execution Logs

```python
# Add execution log
await data_layer.add_execution_log(
    trade_id=trade_id,
    log_level='info',
    message='Bet placed successfully',
    details={'bookmaker': 'Bet365', 'amount': 100.0},
    screenshot_url=screenshot_url,
    bookmaker='Bet365',
    step_name='place_bet'
)
```

#### Storage Operations

```python
# Upload screenshot
screenshot_url = await data_layer.upload_screenshot(
    file_path='/path/to/screenshot.png',
    screenshot_name='trade_12345_bet365.png'
)

# Upload log file
log_url = await data_layer.upload_log_file(
    file_path='/path/to/log.json',
    log_name='execution_log_20251101.json'
)
```

## Edge Functions

### 1. Process Opportunity

**Endpoint**: `https://apailklayaphzswnxgya.supabase.co/functions/v1/process-opportunity`

Analyzes opportunities with risk scoring and validation.

**Request**:
```json
{
  "opportunity_id": "uuid",
  "user_id": "uuid",
  "processing_type": "risk_analysis" // or "validation"
}
```

**Response**:
```json
{
  "data": {
    "opportunity_id": "uuid",
    "risk_score": 2.5,
    "total_implied_probability": 1.025,
    "arbitrage_margin": -0.025,
    "num_bookmakers": 3,
    "timestamp": "2025-11-01T20:00:00Z"
  }
}
```

### 2. Generate Report

**Endpoint**: `https://apailklayaphzswnxgya.supabase.co/functions/v1/generate-report`

Generates performance reports and saves metrics.

**Request**:
```json
{
  "user_id": "uuid", // optional, null for system-wide
  "period_days": 7
}
```

**Response**:
```json
{
  "data": {
    "metrics": {
      "total_trades": 45,
      "successful_trades": 38,
      "failed_trades": 7,
      "total_profit": 1250.50,
      "win_rate": 0.844,
      "sharpe_ratio": 1.85,
      "max_drawdown": 125.00
    },
    "saved": true,
    "trades_analyzed": 45,
    "report_generated_at": "2025-11-01T20:00:00Z"
  }
}
```

### 3. Monitor System (Cron)

**Endpoint**: `https://apailklayaphzswnxgya.supabase.co/functions/v1/monitor-system`

Monitors system health, circuit breakers, and risk alerts. Runs automatically via cron.

**Request**: None (cron-triggered)

**Response**:
```json
{
  "data": {
    "status": "healthy", // or "warning", "critical"
    "circuit_breakers_active": 0,
    "critical_alerts": 0,
    "recent_trades": 15,
    "total_hourly_loss": 45.00,
    "loss_rate": 0.2,
    "consecutive_losses": 2,
    "issues": []
  }
}
```

### 4. Send Notification

**Endpoint**: `https://apailklayaphzswnxgya.supabase.co/functions/v1/send-notification`

Sends notifications to users.

**Request**:
```json
{
  "user_id": "uuid",
  "notification_type": "opportunity_alert",
  "priority": "high",
  "title": "High-Profit Opportunity",
  "body": "A tier-A opportunity with 3.5% profit margin",
  "data": {"opportunity_id": "uuid"},
  "action_url": "/opportunities/uuid"
}
```

**Response**:
```json
{
  "data": {
    "notification": {
      "id": "uuid",
      "sent_at": "2025-11-01T20:00:00Z"
    },
    "delivery": {
      "delivered": true,
      "channels_delivered": ["email", "push"]
    }
  }
}
```

## Real-time Subscriptions

### Subscribe to Opportunities

```python
def on_opportunity_update(payload):
    print(f"New opportunity: {payload}")

data_layer.subscribe_to_opportunities(on_opportunity_update)
```

### Subscribe to Trade Status

```python
def on_trade_update(payload):
    print(f"Trade updated: {payload}")

data_layer.subscribe_to_trade_status(user_id, on_trade_update)
```

### Unsubscribe

```python
data_layer.unsubscribe_all()
```

## Usage Examples

### Complete Integration Example

```python
import asyncio
from storage.supabase_layer import get_data_layer
from storage.models import ArbitrageOpportunity, ArbitrageLeg, Trade
from datetime import datetime, timedelta

async def main():
    # Initialize
    data_layer = get_data_layer()
    
    # 1. Save an opportunity discovered by scanner
    opportunity = ArbitrageOpportunity(
        sport=Sport.FOOTBALL,
        event_name="Team A vs Team B",
        event_date=datetime.utcnow() + timedelta(hours=24),
        market_type="match_winner",
        legs=[
            ArbitrageLeg(
                bookmaker="Bet365",
                event_outcome="Team A Win",
                odds=2.10,
                implied_probability=0.476,
                stake_percentage=0.476,
                actual_stake=47.60,
                potential_payout=100.0
            ),
            ArbitrageLeg(
                bookmaker="Pinnacle",
                event_outcome="Team B Win",
                odds=2.20,
                implied_probability=0.454,
                stake_percentage=0.454,
                actual_stake=45.40,
                potential_payout=100.0
            )
        ],
        total_stake=93.0,
        profit_margin=0.07,
        profit_amount=7.0,
        risk_tier=RiskTier.TIER_A
    )
    
    saved_opp = await data_layer.save_opportunity(opportunity)
    print(f"Saved opportunity: {saved_opp['id']}")
    
    # 2. Process opportunity with edge function
    import requests
    process_response = requests.post(
        'https://apailklayaphzswnxgya.supabase.co/functions/v1/process-opportunity',
        json={
            'opportunity_id': saved_opp['id'],
            'processing_type': 'risk_analysis'
        }
    )
    risk_data = process_response.json()['data']
    print(f"Risk score: {risk_data['risk_score']}")
    
    # 3. Log HITL decision
    await data_layer.log_hitl_decision(
        opportunity_id=saved_opp['id'],
        user_id=user_id,
        decision='approved',
        decision_reason='Acceptable risk, good profit',
        risk_summary=risk_data
    )
    
    # 4. Create and track trade
    trade = Trade(
        user_id=user_id,
        opportunity=opportunity,
        execution_mode=ExecutionMode.AUTO_FULL,
        stake_data=StakeData(
            total_stake=93.0,
            currency='USD',
            leg_allocations={'Bet365': 47.60, 'Pinnacle': 45.40},
            net_stake=93.0
        ),
        expected_profit=7.0
    )
    
    saved_trade = await data_layer.create_trade(trade)
    print(f"Created trade: {saved_trade['id']}")
    
    # 5. Update trade status during execution
    await data_layer.update_trade_status(
        saved_trade['id'],
        TradeStatus.PLACING_BETS
    )
    
    # 6. Log execution steps
    await data_layer.add_execution_log(
        trade_id=saved_trade['id'],
        log_level='info',
        message='Placing bet on Bet365',
        bookmaker='Bet365',
        step_name='place_bet_1'
    )
    
    # 7. Upload screenshot
    screenshot_url = await data_layer.upload_screenshot(
        file_path='/path/to/screenshot.png',
        screenshot_name=f'trade_{saved_trade["id"]}_bet365.png'
    )
    
    # 8. Complete trade
    await data_layer.update_trade_status(
        saved_trade['id'],
        TradeStatus.FILLED,
        additional_data={'actual_profit': 6.95}
    )
    
    # 9. Generate performance report
    report_response = requests.post(
        'https://apailklayaphzswnxgya.supabase.co/functions/v1/generate-report',
        json={'user_id': user_id, 'period_days': 7}
    )
    metrics = report_response.json()['data']['metrics']
    print(f"Performance: Win rate {metrics['win_rate']:.2%}, Net profit ${metrics['net_profit']:.2f}")

if __name__ == '__main__':
    asyncio.run(main())
```

### Integration with Existing Phases

#### Phase 3: Detection Integration

```python
from detection.opportunity_scanner import OpportunityScanner
from storage.supabase_layer import get_data_layer

async def scan_and_persist():
    scanner = OpportunityScanner()
    data_layer = get_data_layer()
    
    # Scan for opportunities
    opportunities = await scanner.scan_markets()
    
    # Save to database
    for opp in opportunities:
        saved = await data_layer.save_opportunity(opp)
        print(f"Persisted opportunity {saved['id']}")
```

#### Phase 4: Risk Management Integration

```python
from risk.risk_analyzer import RiskAnalyzer
from storage.supabase_layer import get_data_layer

async def analyze_and_alert():
    analyzer = RiskAnalyzer()
    data_layer = get_data_layer()
    
    # Get opportunities from database
    opportunities = data_layer.get_opportunities(limit=50)
    
    for opp in opportunities:
        # Analyze risk
        risk_result = analyzer.analyze_opportunity(opp)
        
        # Create alert if high risk
        if risk_result.severity == 'high':
            await data_layer.create_risk_alert(
                alert_type='high_risk_opportunity',
                severity='high',
                title=f'High risk in {opp["event_name"]}',
                description=risk_result.description,
                opportunity_id=opp['id'],
                risk_metrics=risk_result.metrics
            )
```

#### Phase 6: HITL Integration

```python
from hitl.approval_workflow import ApprovalWorkflow
from storage.supabase_layer import get_data_layer

async def hitl_with_persistence():
    workflow = ApprovalWorkflow()
    data_layer = get_data_layer()
    
    # Get opportunity
    opportunity = data_layer.get_opportunities(limit=1)[0]
    
    # Present to user and get decision
    decision = await workflow.present_opportunity(opportunity)
    
    # Log decision to database
    await data_layer.log_hitl_decision(
        opportunity_id=opportunity['id'],
        user_id=user_id,
        decision=decision.decision,
        decision_reason=decision.reason,
        presented_at=decision.presented_at,
        decided_at=decision.decided_at
    )
```

#### Phase 7: Autonomous Mode Integration

```python
from autonomous.decision_engine import DecisionEngine
from storage.supabase_layer import get_data_layer

async def autonomous_with_persistence():
    engine = DecisionEngine()
    data_layer = get_data_layer()
    
    # Get opportunity
    opportunity = data_layer.get_opportunities(limit=1)[0]
    
    # Make autonomous decision
    decision = engine.decide(opportunity)
    
    # Log decision
    await data_layer.log_autonomous_decision(
        opportunity_id=opportunity['id'],
        decision=decision.action,
        confidence_score=decision.confidence,
        reasoning=decision.reasoning,
        risk_score=decision.risk_score,
        risk_factors=decision.risk_factors
    )
    
    # Execute if approved
    if decision.action == 'execute':
        # Execute trade and log
        trade = await execute_trade(opportunity)
        await data_layer.create_trade(trade)
```

## Best Practices

### 1. Error Handling

Always wrap database operations in try-except blocks:

```python
try:
    await data_layer.save_opportunity(opportunity)
except Exception as e:
    logger.error(f"Failed to save opportunity: {str(e)}")
    # Handle error appropriately
```

### 2. Batch Operations

For high-volume operations, batch your writes:

```python
# Instead of saving one by one
for opp in opportunities:
    await data_layer.save_opportunity(opp)  # Multiple round trips

# Batch insert (implement custom method if needed)
await data_layer.batch_save_opportunities(opportunities)  # Single round trip
```

### 3. Connection Management

Reuse the data layer instance:

```python
# Good - reuse singleton
data_layer = get_data_layer()

# Avoid - creating multiple instances
data_layer1 = SupabaseDataLayer()
data_layer2 = SupabaseDataLayer()
```

### 4. Real-time Subscriptions

Unsubscribe when done to prevent memory leaks:

```python
try:
    data_layer.subscribe_to_opportunities(callback)
    # Do work
finally:
    data_layer.unsubscribe_all()
```

### 5. Data Validation

Validate data before saving:

```python
# Pydantic models handle validation
try:
    opportunity = ArbitrageOpportunity(**data)
    await data_layer.save_opportunity(opportunity)
except ValidationError as e:
    logger.error(f"Invalid opportunity data: {e}")
```

## Troubleshooting

### Issue: "new row violates row-level security policy"

**Cause**: RLS policies not allowing the operation.

**Solution**: Verify RLS policies include both `anon` and `service_role` roles.

### Issue: Connection timeout

**Cause**: Network issues or Supabase overload.

**Solution**: Implement retry logic with exponential backoff.

```python
import time

max_retries = 3
for attempt in range(max_retries):
    try:
        await data_layer.save_opportunity(opportunity)
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        time.sleep(2 ** attempt)
```

### Issue: Storage upload fails

**Cause**: File size exceeds bucket limits.

**Solution**: Check file size before upload and compress if needed.

```python
import os

file_size = os.path.getsize(file_path)
if file_size > 10 * 1024 * 1024:  # 10MB
    # Compress or resize
    compressed_path = compress_image(file_path)
    await data_layer.upload_screenshot(compressed_path, name)
```

### Issue: Edge function returns 500

**Cause**: Code error or missing environment variables.

**Solution**: Check function logs using `get_logs` tool.

```python
from supabase_tools import get_logs

logs = get_logs(service='edge-function')
print(logs)
```

## Additional Resources

- **Database Schema**: `/workspace/arbitech/supabase/migrations/01_initial_schema.sql`
- **Data Layer**: `/workspace/arbitech/storage/supabase_layer.py`
- **Edge Functions**: `/workspace/arbitech/supabase/functions/`
- **Supabase Dashboard**: https://supabase.com/dashboard/project/apailklayaphzswnxgya

## Support

For issues or questions:
1. Check logs: `get_logs(service='api')` or `get_logs(service='edge-function')`
2. Review database records in Supabase dashboard
3. Test edge functions with `test_edge_function` tool
4. Verify environment variables are set correctly

## Next Steps

1. **Set up authentication**: Implement user signup/login with Supabase Auth
2. **Build dashboard**: Create real-time dashboard with subscriptions
3. **Deploy to production**: Move from development to production environment
4. **Monitor performance**: Set up alerts and monitoring for system health
5. **Scale**: Optimize queries and implement caching as needed
