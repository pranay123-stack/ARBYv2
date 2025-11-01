# ARBitech Supabase API Quick Reference

## Table of Contents
- [Data Layer Methods](#data-layer-methods)
- [Edge Function Endpoints](#edge-function-endpoints)
- [Database Tables](#database-tables)
- [Enums and Types](#enums-and-types)

## Data Layer Methods

### Initialization

```python
from storage.supabase_layer import get_data_layer

data_layer = get_data_layer()
```

### Opportunities

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `save_opportunity()` | `opportunity: ArbitrageOpportunity` | `Dict[str, Any]` | Save opportunity with legs |
| `get_opportunities()` | `sport, risk_tier, min_profit_margin, limit` | `List[Dict]` | Retrieve opportunities |
| `get_opportunity_legs()` | `opportunity_id: str` | `List[Dict]` | Get legs for opportunity |

### Trades

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `create_trade()` | `trade: Trade` | `Dict[str, Any]` | Create new trade |
| `update_trade_status()` | `trade_id, status, additional_data` | `Dict[str, Any]` | Update trade status |
| `get_user_trades()` | `user_id, status, limit` | `List[Dict]` | Get user's trades |

### Decisions

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `log_hitl_decision()` | `opportunity_id, user_id, decision, ...` | `Dict[str, Any]` | Log HITL decision |
| `log_autonomous_decision()` | `opportunity_id, decision, confidence_score, ...` | `Dict[str, Any]` | Log AI decision |

### Risk Management

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `create_risk_alert()` | `alert_type, severity, title, description, ...` | `Dict[str, Any]` | Create risk alert |
| `get_unresolved_alerts()` | `user_id, min_severity` | `List[Dict]` | Get unresolved alerts |
| `log_circuit_breaker_event()` | `breaker_type, trigger_value, ...` | `Dict[str, Any]` | Log circuit breaker |

### Logging

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `add_execution_log()` | `trade_id, log_level, message, ...` | `Dict[str, Any]` | Add execution log |

### Performance

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `save_performance_metrics()` | `user_id, period_start, period_end, metrics` | `Dict[str, Any]` | Save metrics |

### Storage

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `upload_screenshot()` | `file_path, screenshot_name, bucket` | `str` | Upload screenshot, returns URL |
| `upload_log_file()` | `file_path, log_name, bucket` | `str` | Upload log file, returns URL |

### Real-time

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `subscribe_to_opportunities()` | `callback` | `None` | Subscribe to opportunity updates |
| `subscribe_to_trade_status()` | `user_id, callback` | `None` | Subscribe to trade updates |
| `unsubscribe_all()` | None | `None` | Unsubscribe from all |

## Edge Function Endpoints

Base URL: `https://apailklayaphzswnxgya.supabase.co/functions/v1`

### 1. Process Opportunity

**POST** `/process-opportunity`

Process and analyze arbitrage opportunities.

**Request Body**:
```json
{
  "opportunity_id": "string (uuid)",
  "user_id": "string (uuid, optional)",
  "processing_type": "string (risk_analysis|validation)"
}
```

**Response** (200 OK):
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

**Processing Types**:
- `risk_analysis`: Calculate risk score and create alerts if needed
- `validation`: Validate opportunity data and update errors

### 2. Generate Report

**POST** `/generate-report`

Generate performance reports and save metrics.

**Request Body**:
```json
{
  "user_id": "string (uuid, optional, null for system-wide)",
  "period_days": 7
}
```

**Response** (200 OK):
```json
{
  "data": {
    "metrics": {
      "total_trades": 45,
      "successful_trades": 38,
      "failed_trades": 7,
      "total_profit": 1250.50,
      "total_loss": 125.00,
      "net_profit": 1125.50,
      "win_rate": 0.844,
      "avg_profit_per_trade": 25.01,
      "avg_execution_time_ms": 1500,
      "sharpe_ratio": 1.85,
      "max_drawdown": 125.00,
      "volatility": 15.5
    },
    "saved": true,
    "trades_analyzed": 45,
    "report_generated_at": "2025-11-01T20:00:00Z"
  }
}
```

### 3. Monitor System

**POST** `/monitor-system` (also cron-triggered)

Monitor system health, circuit breakers, and alerts.

**Request Body**: `{}` (empty for manual trigger)

**Response** (200 OK):
```json
{
  "data": {
    "status": "healthy",
    "timestamp": "2025-11-01T20:00:00Z",
    "circuit_breakers_active": 0,
    "critical_alerts": 0,
    "recent_trades": 15,
    "recent_losses": 3,
    "total_hourly_loss": 45.00,
    "loss_rate": 0.2,
    "consecutive_losses": 2,
    "issues": []
  }
}
```

**Status Values**:
- `healthy`: No issues
- `warning`: Some issues detected
- `critical`: Critical issues requiring attention

**Issue Object**:
```json
{
  "type": "circuit_breaker_active",
  "severity": "critical",
  "count": 1,
  "message": "1 circuit breaker(s) active"
}
```

### 4. Send Notification

**POST** `/send-notification`

Send notifications to users.

**Request Body**:
```json
{
  "user_id": "string (uuid)",
  "notification_type": "string (see types below)",
  "priority": "string (low|medium|high|critical)",
  "title": "string",
  "body": "string",
  "data": {},
  "action_url": "string (optional)"
}
```

**Response** (200 OK):
```json
{
  "data": {
    "notification": {
      "id": "uuid",
      "sent_at": "2025-11-01T20:00:00Z"
    },
    "delivery": {
      "delivered": true,
      "channels_delivered": ["email", "push"],
      "delivery_timestamp": "2025-11-01T20:00:00Z"
    }
  }
}
```

**Notification Types**:
- `opportunity_alert`
- `trade_update`
- `risk_warning`
- `account_update`
- `system_error`
- `profit_realized`
- `limit_hit`
- `maintenance`

## Database Tables

### arbitrage_opportunities

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| sport | sport_type | Sport category |
| event_name | TEXT | Event name |
| event_date | TIMESTAMPTZ | Event date/time |
| market_type | TEXT | Market type |
| total_stake | NUMERIC(18,8) | Total stake amount |
| profit_margin | NUMERIC(18,8) | Profit margin |
| profit_amount | NUMERIC(18,8) | Expected profit |
| risk_tier | risk_tier | Risk tier (A-D) |
| discovered_at | TIMESTAMPTZ | Discovery time |
| expires_at | TIMESTAMPTZ | Expiration time |

### arbitrage_legs

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| opportunity_id | UUID | Opportunity reference |
| bookmaker | TEXT | Bookmaker name |
| event_outcome | TEXT | Bet outcome |
| odds | NUMERIC(18,8) | Decimal odds |
| implied_probability | NUMERIC(18,8) | Implied probability |
| stake_percentage | NUMERIC(18,8) | Stake percentage |
| actual_stake | NUMERIC(18,8) | Actual stake amount |
| potential_payout | NUMERIC(18,8) | Potential payout |

### trades

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | User reference |
| opportunity_id | UUID | Opportunity reference |
| status | trade_status | Trade status |
| execution_mode | execution_mode | Execution mode |
| total_stake | NUMERIC(18,8) | Total stake |
| expected_profit | NUMERIC(18,8) | Expected profit |
| actual_profit | NUMERIC(18,8) | Actual profit |
| created_at | TIMESTAMPTZ | Creation time |
| completed_at | TIMESTAMPTZ | Completion time |

### hitl_decisions

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| opportunity_id | UUID | Opportunity reference |
| user_id | UUID | User reference |
| decision | TEXT | Decision (approved/rejected/modified) |
| decision_reason | TEXT | Reason for decision |
| presented_at | TIMESTAMPTZ | Presentation time |
| decided_at | TIMESTAMPTZ | Decision time |
| response_time_ms | INTEGER | Response time |
| risk_summary | JSONB | Risk summary data |

### autonomous_decisions

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| opportunity_id | UUID | Opportunity reference |
| decision | TEXT | Decision (execute/skip/queue) |
| confidence_score | NUMERIC(18,8) | Confidence level |
| reasoning | JSONB | Decision reasoning |
| risk_score | NUMERIC(18,8) | Risk score |
| risk_factors | JSONB | Risk factors |
| executed | BOOLEAN | Execution status |

### risk_alerts

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | User reference (optional) |
| opportunity_id | UUID | Opportunity reference |
| alert_type | TEXT | Alert type |
| severity | alert_severity | Severity level |
| title | TEXT | Alert title |
| description | TEXT | Alert description |
| risk_metrics | JSONB | Risk metrics data |
| resolved | BOOLEAN | Resolution status |

### circuit_breaker_events

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| breaker_type | TEXT | Breaker type |
| trigger_value | NUMERIC(18,8) | Trigger value |
| threshold_value | NUMERIC(18,8) | Threshold value |
| description | TEXT | Event description |
| affected_operations | JSONB | Affected operations |
| resolved | BOOLEAN | Resolution status |
| triggered_at | TIMESTAMPTZ | Trigger time |

### execution_logs

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| trade_id | UUID | Trade reference |
| log_level | TEXT | Log level |
| message | TEXT | Log message |
| details | JSONB | Additional details |
| screenshot_url | TEXT | Screenshot URL |
| bookmaker | TEXT | Bookmaker name |
| step_name | TEXT | Execution step |

### performance_metrics

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | User reference (optional) |
| period_start | TIMESTAMPTZ | Period start |
| period_end | TIMESTAMPTZ | Period end |
| total_trades | INTEGER | Total trades |
| successful_trades | INTEGER | Successful trades |
| total_profit | NUMERIC(18,8) | Total profit |
| win_rate | NUMERIC(18,8) | Win rate |
| sharpe_ratio | NUMERIC(18,8) | Sharpe ratio |
| max_drawdown | NUMERIC(18,8) | Max drawdown |

## Enums and Types

### sport_type
```
football, basketball, tennis, baseball, hockey, mma,
cricket, rugby, volleyball, golf, boxing, esports,
politics, entertainment
```

### trade_status
```
pending, placing_bets, partial_filled, filled, failed,
cancelled, expired, hedging, settled
```

### execution_mode
```
manual, auto_full, auto_stealth, delayed, simulated
```

### risk_tier
```
tier_a, tier_b, tier_c, tier_d
```

### account_status
```
active, suspended, limited, banned, closed, under_review
```

### scanner_status
```
idle, scanning, paused, error, stopped
```

### notification_type
```
opportunity_alert, trade_update, risk_warning, account_update,
system_error, profit_realized, limit_hit, maintenance
```

### notification_priority
```
low, medium, high, critical
```

### alert_severity
```
low, medium, high, critical
```

## Python Usage Examples

### Quick Start

```python
from storage.supabase_layer import get_data_layer
from storage.models import Sport, RiskTier, TradeStatus

# Initialize
data_layer = get_data_layer()

# Save opportunity
await data_layer.save_opportunity(opportunity)

# Get opportunities
opportunities = data_layer.get_opportunities(
    sport=Sport.FOOTBALL,
    risk_tier=RiskTier.TIER_A,
    min_profit_margin=0.02,
    limit=50
)

# Create trade
await data_layer.create_trade(trade)

# Update trade status
await data_layer.update_trade_status(
    trade_id,
    TradeStatus.FILLED,
    {'actual_profit': 15.50}
)

# Log HITL decision
await data_layer.log_hitl_decision(
    opportunity_id=opp_id,
    user_id=user_id,
    decision='approved',
    decision_reason='Good opportunity'
)

# Create risk alert
await data_layer.create_risk_alert(
    alert_type='market_volatility_spike',
    severity='high',
    title='High Volatility',
    description='Market volatility exceeded threshold'
)

# Upload screenshot
url = await data_layer.upload_screenshot(
    file_path='/path/to/screenshot.png',
    screenshot_name='trade_123_bet365.png'
)
```

### Edge Function Invocation

```python
import requests

# Process opportunity
response = requests.post(
    'https://apailklayaphzswnxgya.supabase.co/functions/v1/process-opportunity',
    json={
        'opportunity_id': opp_id,
        'processing_type': 'risk_analysis'
    }
)
result = response.json()

# Generate report
response = requests.post(
    'https://apailklayaphzswnxgya.supabase.co/functions/v1/generate-report',
    json={'user_id': user_id, 'period_days': 7}
)
metrics = response.json()['data']['metrics']

# Send notification
response = requests.post(
    'https://apailklayaphzswnxgya.supabase.co/functions/v1/send-notification',
    json={
        'user_id': user_id,
        'notification_type': 'opportunity_alert',
        'priority': 'high',
        'title': 'New Opportunity',
        'body': 'High-profit opportunity detected'
    }
)
```

### Real-time Subscriptions

```python
# Subscribe to opportunities
def on_new_opportunity(payload):
    print(f"New opportunity: {payload}")

data_layer.subscribe_to_opportunities(on_new_opportunity)

# Subscribe to trade updates
def on_trade_update(payload):
    print(f"Trade updated: {payload}")

data_layer.subscribe_to_trade_status(user_id, on_trade_update)

# Clean up
data_layer.unsubscribe_all()
```

## Storage Buckets

| Bucket | Purpose | Size Limit | Allowed Types |
|--------|---------|------------|---------------|
| `arbitech-screenshots` | Trade screenshots | 10MB | PNG, JPEG |
| `arbitech-logs` | System logs | 50MB | JSON, TXT, CSV |
| `arbitech-documents` | Trade documents | 10MB | PDF, JSON |

## Error Handling

### Common Errors

**RLS Policy Violation**:
```python
try:
    await data_layer.save_opportunity(opportunity)
except Exception as e:
    if 'row-level security' in str(e):
        # RLS policy issue
        logger.error("RLS policy violation")
```

**Storage Upload Error**:
```python
try:
    url = await data_layer.upload_screenshot(path, name)
except Exception as e:
    if 'InvalidKey' in str(e):
        # Non-ASCII characters in path
        logger.error("Invalid file path")
```

**Edge Function Error**:
```python
response = requests.post(endpoint, json=data)
if response.status_code != 200:
    error = response.json()
    logger.error(f"Edge function error: {error['error']['message']}")
```

## Performance Tips

1. **Batch operations**: Group multiple inserts when possible
2. **Use indexes**: Query indexed fields (sport, risk_tier, created_at)
3. **Limit results**: Always specify a reasonable limit
4. **Cache frequently accessed data**: Store in memory when appropriate
5. **Async operations**: Use async methods for better concurrency

## Security Notes

1. **Never expose service role key** in frontend code
2. **Use RLS policies** to enforce data access
3. **Validate all input** before saving to database
4. **Encrypt sensitive data** (credentials, personal info)
5. **Audit trail**: All operations are logged in `audit_trail` table
