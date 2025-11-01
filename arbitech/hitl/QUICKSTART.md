# HITL Orchestrator Quick Start Guide

This guide will get you up and running with the HITL execution orchestrator in minutes.

## 🚀 Running the Demo

### Option 1: Complete Demo
```bash
cd /workspace/arbitech/hitl
python demo_orchestrator.py
```

This runs the complete demonstration showing all features:
- Orchestrator initialization
- Opportunity submission and processing
- User approval/rejection simulation
- Error handling and recovery
- Graceful shutdown
- State resume functionality

### Option 2: Specific Demo Types

```bash
# Basic workflow only (faster)
python demo_orchestrator.py --workflow

# User interactions simulation
python demo_orchestrator.py --interactions

# Error handling demonstration
python demo_orchestrator.py --errors

# Graceful shutdown demo
python demo_orchestrator.py --shutdown

# State resume demo
python demo_orchestrator.py --resume
```

## 📋 What You'll See

### Demo 1: Basic Workflow
1. **Initialization**: Orchestrator starts with configuration
2. **Submission**: Sample opportunities are submitted
3. **Processing**: Opportunities flow through states:
   - `DETECTED` → `PRESENTED` → `APPROVED` → `EXECUTING` → `COMPLETED`
4. **Monitoring**: Real-time state updates

### Demo 2: User Interactions
- **Approval Process**: Shows how users approve opportunities
- **Rejection Process**: Demonstrates rejection with reasons
- **Timeout Handling**: Shows what happens when users don't respond

### Demo 3: Error Handling
- **Retry Mechanisms**: Automatic retries for failures
- **Recovery**: System recovery from various error conditions
- **Logging**: Comprehensive error logging and tracking

### Demo 4: Graceful Shutdown
- **Clean Shutdown**: Graceful termination preserving state
- **State Saving**: Automatic state persistence
- **Resumption**: Resume from saved state after restart

## 🛠 Integration with Your System

### 1. Initialize the Orchestrator

```python
from arbitech.hitl import HITLOrchestrator, OrchestratorConfig
from arbitech.core.audit_logger import AuditLogger

# Create configuration
config = OrchestratorConfig(
    max_concurrent_opportunities=10,
    enable_recovery=True,
    processing_timeout=300,
    retry_attempts=3
)

# Initialize orchestrator
orchestrator = HITLOrchestrator(
    config=config,
    audit_logger=AuditLogger(),
    detection_scanner=your_scanner,      # Phase 3 component
    risk_validator=your_validator,       # Phase 4 component
    automation_executor=your_executor    # Phase 5 component
)
```

### 2. Start Processing

```python
await orchestrator.start()
```

### 3. Submit Opportunities

```python
from arbitech.storage.models import ArbitrageOpportunity, RiskTier

# Create opportunity
opportunity = ArbitrageOpportunity(
    id="unique_id_001",
    symbol="BTC/USD",
    expected_profit=25.0,
    risk_tier=RiskTier.LOW_RISK,
    # ... other fields
)

# Submit for processing
await orchestrator.submit_opportunity(opportunity)
```

### 4. Handle User Approvals

```python
# Approve opportunity
approval_data = {
    "user_id": "user_123",
    "comments": "Looks good",
    "timestamp": datetime.now().isoformat()
}
await orchestrator.approve_opportunity(opportunity.id, approval_data)

# Or reject with reason
rejection_data = {
    "user_id": "user_123",
    "rejection_reason": "insufficient_profit",
    "comments": "Profit margin too low"
}
await orchestrator.reject_opportunity(opportunity.id, rejection_data)
```

### 5. Monitor Processing

```python
# Get current states
states = await orchestrator.get_opportunity_states()
for state in states:
    print(f"{state.opportunity_id}: {state.state.value}")
```

### 6. Graceful Shutdown

```python
await orchestrator.shutdown(graceful=True)
```

## 🔧 Configuration Options

### Basic Configuration

```python
config = OrchestratorConfig(
    max_concurrent_opportunities=10,    # Max simultaneous opportunities
    processing_timeout=300,              # Overall timeout (5 minutes)
    retry_attempts=3,                   # Retry attempts on failure
    retry_delay=5,                      # Delay between retries (seconds)
    enable_recovery=True,               # Enable error recovery
    recovery_interval=30,               # Recovery check interval
    state_save_interval=60              # State save frequency
)
```

### Timeout Configuration by Risk Tier

```python
timeout_config = {
    "LOW_RISK": {
        "approval_timeout": 120,    # 2 minutes
        "execution_timeout": 60,     # 1 minute
        "auto_approve": True
    },
    "MEDIUM_RISK": {
        "approval_timeout": 300,    # 5 minutes
        "execution_timeout": 180,    # 3 minutes
        "auto_approve": False
    },
    "HIGH_RISK": {
        "approval_timeout": 600,    # 10 minutes
        "execution_timeout": 300,    # 5 minutes
        "auto_approve": False
    }
}
```

## 📊 Understanding Workflow States

### WorkflowState Enum
- `DETECTED`: Opportunity detected by Phase 3 scanner
- `PRESENTED`: Opportunity presented to user for approval
- `APPROVED`: User approved the opportunity
- `EXECUTING`: Trade execution in progress (Phase 5)
- `COMPLETED`: Trade executed successfully
- `FAILED`: Trade execution failed
- `CANCELLED`: User cancelled or timeout occurred

### State Transitions
```
DETECTED → PRESENTED → APPROVED → EXECUTING → COMPLETED
                     ↓
                   REJECTED → FAILED
                     ↓
                   TIMEOUT → FAILED
```

## 🔍 Monitoring and Debugging

### Get Orchestrator Statistics

```python
# Get opportunity statistics
stats = await orchestrator.get_statistics()
print(f"Total processed: {stats['total_processed']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Average processing time: {stats['avg_processing_time']:.2f}s")
```

### Error Handling

```python
try:
    await orchestrator.submit_opportunity(opportunity)
except HitlError as e:
    print(f"HITL Error: {e}")
except OrchestratorError as e:
    print(f"Orchestrator Error: {e}")
except TimeoutError as e:
    print(f"Timeout Error: {e}")
except ApprovalError as e:
    print(f"Approval Error: {e}")
except ExecutionError as e:
    print(f"Execution Error: {e}")
```

## 📁 File Structure

After running the demo, you'll see these files created:

```
/workspace/arbitech/hitl/
├── demo_orchestrator.py           # Main demo script
├── logs/
│   └── hitl_demo.log             # Demo execution logs
├── state/
│   └── orchestrator_state.json   # Saved state (after shutdown)
├── data/
│   └── (temporary data files)
└── QUICKSTART.md                 # This file
```

## 🚨 Common Issues and Solutions

### 1. "Orchestrator not initialized"
**Solution**: Call `await orchestrator.start()` before submitting opportunities

### 2. "Component not configured"
**Solution**: Ensure all required components (scanner, validator, executor) are provided

### 3. Import errors
**Solution**: Make sure you're running from the correct directory:
```bash
cd /workspace/arbitech/hitl
python demo_orchestrator.py
```

### 4. Permission errors
**Solution**: Ensure write permissions for log and state directories

## 🎯 Next Steps

1. **Run the Demo**: Start with `python demo_orchestrator.py`
2. **Integrate Components**: Connect your Phase 3, 4, and 5 components
3. **Custom Configuration**: Adjust timeouts and settings for your use case
4. **Production Setup**: Configure logging, monitoring, and alerting
5. **Performance Tuning**: Optimize for your expected load

## 📚 Additional Resources

- **Complete Documentation**: See [README.md](README.md) for detailed API reference
- **Demo Script**: See [demo_orchestrator.py](demo_orchestrator.py) for complete examples
- **Component Examples**: Each HITL component has its own demo script
- **API Reference**: Full API documentation in the main README

## 🆘 Getting Help

1. **Check Logs**: Look in `/workspace/arbitech/logs/hitl_demo.log`
2. **Run Diagnostics**: Use `--workflow` for focused testing
3. **Review State**: Check saved state in `/workspace/arbitech/hitl/state/`
4. **Enable Debug**: Add `logging.basicConfig(level=logging.DEBUG)`

Happy trading! 🚀