# ARBitech Supabase Integration

Complete data storage and integration system for the ARBitech autonomous arbitrage trading platform.

## Overview

This integration provides comprehensive data persistence, real-time monitoring, and automated workflows for ARBitech's trading operations. It seamlessly integrates with all existing phases (1-7) of the ARBitech system.

## Quick Start

### 1. Set Environment Variables

```bash
export SUPABASE_URL="https://apailklayaphzswnxgya.supabase.co"
export SUPABASE_ANON_KEY="your_anon_key"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"
```

### 2. Install Dependencies

```bash
pip install supabase-py
```

### 3. Use the Data Layer

```python
from storage.supabase_layer import get_data_layer

# Initialize
data_layer = get_data_layer()

# Save an opportunity
await data_layer.save_opportunity(opportunity)

# Create a trade
await data_layer.create_trade(trade)

# Log a decision
await data_layer.log_hitl_decision(
    opportunity_id=opp_id,
    user_id=user_id,
    decision='approved'
)
```

### 4. Run the Demo

```bash
cd /workspace/arbitech
python examples/supabase_integration_demo.py
```

## What's Included

### Database (16 Tables)
- **Trading**: opportunities, legs, trades, bookmaker accounts
- **Risk**: configs, alerts, circuit breaker events
- **Decisions**: HITL decisions, autonomous decisions
- **Operations**: scanner sessions, execution logs, notifications
- **Analytics**: performance metrics, market snapshots
- **Compliance**: audit trail, profiles

### Data Persistence Layer
- **File**: `storage/supabase_layer.py`
- **Class**: `SupabaseDataLayer`
- **Methods**: 40+ methods for all database operations
- **Features**: Async operations, real-time subscriptions, storage management

### Edge Functions (4)
1. **process-opportunity**: Risk analysis and validation
2. **generate-report**: Performance metrics and reporting
3. **monitor-system**: Health monitoring and alerting (cron)
4. **send-notification**: Multi-channel notifications

### Storage Buckets (3)
- `arbitech-screenshots`: Trade screenshots (10MB)
- `arbitech-logs`: System logs (50MB)
- `arbitech-documents`: Trade documents (10MB)

## Documentation

### Complete Guides
1. **[Integration Guide](docs/SUPABASE_INTEGRATION_GUIDE.md)** - Complete walkthrough with examples
2. **[API Reference](docs/SUPABASE_API_REFERENCE.md)** - Quick reference for all methods
3. **[System Overview](docs/SYSTEM_OVERVIEW.md)** - Architecture and design

### Example Code
- **[Demo Script](examples/supabase_integration_demo.py)** - End-to-end working example

### Database
- **[Schema Migration](supabase/migrations/01_initial_schema.sql)** - Complete database schema

## Key Features

### Type-Safe Integration
Uses Pydantic models from `storage/models.py` for type safety and validation.

### Real-Time Updates
Subscribe to live updates for opportunities and trades:
```python
data_layer.subscribe_to_opportunities(callback)
data_layer.subscribe_to_trade_status(user_id, callback)
```

### Automated Workflows
Edge functions handle complex processing:
- Risk analysis and validation
- Performance reporting
- System health monitoring
- Notification delivery

### Comprehensive Logging
Track every step of trade execution:
```python
await data_layer.add_execution_log(
    trade_id=trade_id,
    log_level='info',
    message='Bet placed successfully',
    screenshot_url=screenshot_url
)
```

### Multi-Tenant Security
Row-level security policies ensure data isolation between users.

## Integration with ARBitech Phases

### Phase 3: Detection
```python
# Save discovered opportunities
opportunities = await scanner.scan_markets()
for opp in opportunities:
    await data_layer.save_opportunity(opp)
```

### Phase 4: Risk Management
```python
# Create risk alerts
await data_layer.create_risk_alert(
    alert_type='high_risk',
    severity='high',
    title='High Risk Detected'
)
```

### Phase 5: Browser Automation
```python
# Track trade execution
await data_layer.create_trade(trade)
await data_layer.add_execution_log(trade_id, 'info', 'Bet placed')
```

### Phase 6: HITL
```python
# Log human decisions
await data_layer.log_hitl_decision(
    opportunity_id=opp_id,
    user_id=user_id,
    decision='approved'
)
```

### Phase 7: Autonomous Trading
```python
# Log AI decisions
await data_layer.log_autonomous_decision(
    opportunity_id=opp_id,
    decision='execute',
    confidence_score=0.95
)
```

## Edge Function Endpoints

Base URL: `https://apailklayaphzswnxgya.supabase.co/functions/v1`

### Process Opportunity
```bash
curl -X POST https://apailklayaphzswnxgya.supabase.co/functions/v1/process-opportunity \
  -H "Content-Type: application/json" \
  -d '{"opportunity_id": "uuid", "processing_type": "risk_analysis"}'
```

### Generate Report
```bash
curl -X POST https://apailklayaphzswnxgya.supabase.co/functions/v1/generate-report \
  -H "Content-Type: application/json" \
  -d '{"user_id": "uuid", "period_days": 7}'
```

### Monitor System
```bash
curl -X POST https://apailklayaphzswnxgya.supabase.co/functions/v1/monitor-system \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Send Notification
```bash
curl -X POST https://apailklayaphzswnxgya.supabase.co/functions/v1/send-notification \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid",
    "notification_type": "opportunity_alert",
    "priority": "high",
    "title": "New Opportunity",
    "body": "High-profit opportunity detected"
  }'
```

## Data Layer Methods

### Opportunities
```python
await data_layer.save_opportunity(opportunity)
opportunities = data_layer.get_opportunities(sport=Sport.FOOTBALL, risk_tier=RiskTier.TIER_A)
legs = data_layer.get_opportunity_legs(opportunity_id)
```

### Trades
```python
await data_layer.create_trade(trade)
await data_layer.update_trade_status(trade_id, TradeStatus.FILLED, {'actual_profit': 15.50})
trades = data_layer.get_user_trades(user_id, status=TradeStatus.FILLED)
```

### Decisions
```python
await data_layer.log_hitl_decision(opportunity_id, user_id, 'approved')
await data_layer.log_autonomous_decision(opportunity_id, 'execute', 0.95, reasoning, risk_score, risk_factors)
```

### Risk Management
```python
await data_layer.create_risk_alert('market_volatility', 'high', 'High Volatility', 'Description')
alerts = data_layer.get_unresolved_alerts(user_id=user_id)
await data_layer.log_circuit_breaker_event('max_loss', 250.0, 200.0, 'Description', ['trading'])
```

### Logging
```python
await data_layer.add_execution_log(trade_id, 'info', 'Message', details, screenshot_url)
```

### Storage
```python
screenshot_url = await data_layer.upload_screenshot('/path/to/file.png', 'trade_123.png')
log_url = await data_layer.upload_log_file('/path/to/log.json', 'execution.json')
```

### Real-Time
```python
data_layer.subscribe_to_opportunities(callback)
data_layer.subscribe_to_trade_status(user_id, callback)
data_layer.unsubscribe_all()
```

## Database Tables

| Table | Description |
|-------|-------------|
| `arbitrage_opportunities` | Discovered arbitrage opportunities |
| `arbitrage_legs` | Betting legs for each opportunity |
| `trades` | Trade execution records |
| `hitl_decisions` | Human-in-the-loop decisions |
| `autonomous_decisions` | AI system decisions |
| `risk_configs` | Risk management configurations |
| `risk_alerts` | Risk monitoring alerts |
| `circuit_breaker_events` | Emergency stop events |
| `scanner_sessions` | Discovery session tracking |
| `bookmaker_accounts` | User bookmaker credentials |
| `execution_logs` | Trade execution logs |
| `notifications` | User notifications |
| `performance_metrics` | Performance analytics |
| `market_data_snapshots` | Historical market data |
| `profiles` | User profiles |
| `audit_trail` | Complete audit log |

## Directory Structure

```
/workspace/arbitech/
├── docs/
│   ├── SUPABASE_INTEGRATION_GUIDE.md  # Complete guide
│   ├── SUPABASE_API_REFERENCE.md      # API reference
│   └── SYSTEM_OVERVIEW.md             # Architecture overview
├── examples/
│   └── supabase_integration_demo.py   # Working demo
├── storage/
│   ├── models.py                       # Pydantic models
│   └── supabase_layer.py              # Data persistence layer
└── supabase/
    ├── functions/                      # Edge functions
    │   ├── process-opportunity/
    │   ├── generate-report/
    │   ├── monitor-system/
    │   └── send-notification/
    └── migrations/                     # Database schema
        └── 01_initial_schema.sql
```

## Performance Tips

1. **Batch Operations**: Group multiple inserts when possible
2. **Use Indexes**: Query indexed fields (sport, risk_tier, created_at)
3. **Limit Results**: Always specify reasonable limits
4. **Cache Data**: Store frequently accessed data in memory
5. **Async Operations**: Use async methods for better concurrency

## Security

- **RLS Policies**: Multi-tenant data isolation
- **Encrypted Credentials**: Sensitive data encrypted at application layer
- **HTTPS Only**: All communication over secure connections
- **Audit Trail**: Complete logging of all operations
- **Service Role Protection**: Service role key never exposed to frontend

## Troubleshooting

### RLS Policy Violation
```python
# Error: "new row violates row-level security policy"
# Solution: Verify RLS policies include both 'anon' and 'service_role' roles
```

### Connection Timeout
```python
# Implement retry logic with exponential backoff
max_retries = 3
for attempt in range(max_retries):
    try:
        await data_layer.save_opportunity(opp)
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        time.sleep(2 ** attempt)
```

### Storage Upload Fails
```python
# Check file size before upload
import os
file_size = os.path.getsize(file_path)
if file_size > 10 * 1024 * 1024:  # 10MB
    # Compress or resize
    compressed = compress_file(file_path)
    await data_layer.upload_screenshot(compressed, name)
```

## Next Steps

1. **Run Demo**: `python examples/supabase_integration_demo.py`
2. **Review Docs**: Read the integration guide and API reference
3. **Integrate**: Add Supabase persistence to your ARBitech workflows
4. **Build Dashboard**: Create real-time dashboard with subscriptions
5. **Deploy**: Move to production with proper monitoring

## Resources

- **Supabase Dashboard**: https://supabase.com/dashboard/project/apailklayaphzswnxgya
- **Documentation**: `/workspace/arbitech/docs/`
- **Source Code**: `/workspace/arbitech/storage/` and `/workspace/arbitech/supabase/`
- **Demo Script**: `/workspace/arbitech/examples/supabase_integration_demo.py`

## Support

For issues or questions:
1. Check documentation in `docs/` directory
2. Review example script in `examples/` directory
3. Examine source code in `storage/` and `supabase/` directories
4. Test edge functions with provided endpoints

## Status

**Production Ready** ✓

- Database schema deployed and tested
- Data persistence layer implemented
- Edge functions deployed and operational
- Storage buckets configured
- Complete documentation provided
- Working demo script included
- RLS security implemented
- Audit trail configured

The system is ready for integration with the ARBitech trading platform.

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-01  
**Status**: Production Ready
