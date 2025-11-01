# HITL (Human-in-the-Loop) Module - Complete Execution System

## Overview

The HITL module provides comprehensive human oversight and intervention capabilities for the ARBitech arbitrage trading system. The system orchestrates the complete workflow from Phase 3 detection through Phase 5 execution with sophisticated timeout management, opportunity presentation, user approval processing, and automated trade execution.

## 🚀 New: Complete HITL Execution Orchestrator

The HITL module now includes a complete execution orchestrator that coordinates the entire human-in-the-loop workflow:

- **Execution Orchestrator**: Main coordinator for the complete HITL workflow
- **Opportunity Presenter**: User-facing opportunity display and ranking
- **Approval Handler**: User approval/rejection processing with validation
- **Timeout Management**: Sophisticated timeout handling for opportunities
- **Result Logging**: Trade outcome logging and performance analytics

### Quick Demo

Run the complete HITL orchestrator demonstration:

```bash
cd /workspace/arbitech/hitl
python demo_orchestrator.py
```

The demo shows:
1. **Initialization**: Setting up the orchestrator with configuration
2. **Workflow**: Submit → Approve → Execute workflow demonstration
3. **User Interactions**: Simulated approvals and rejections
4. **Error Handling**: Recovery mechanisms and error handling
5. **Graceful Shutdown**: Clean shutdown with state preservation
6. **State Resume**: Resume from saved state after restart

For specific demos:
```bash
# Basic workflow only
python demo_orchestrator.py --workflow

# User interactions only
python demo_orchestrator.py --interactions

# Error handling only
python demo_orchestrator.py --errors

# Graceful shutdown only
python demo_orchestrator.py --shutdown

# State resume only
python demo_orchestrator.py --resume

# Use custom configuration
python demo_orchestrator.py --config /path/to/config.yaml
```

### Basic Usage Example

```python
import asyncio
from arbitech.hitl import HITLOrchestrator, WorkflowState, OrchestratorConfig
from arbitech.core.audit_logger import AuditLogger
from arbitech.storage.models import ArbitrageOpportunity, RiskTier

async def main():
    # Create configuration
    config = OrchestratorConfig(
        max_concurrent_opportunities=10,
        enable_recovery=True,
        processing_timeout=300
    )
    
    # Initialize orchestrator
    audit_logger = AuditLogger()
    orchestrator = HITLOrchestrator(
        config=config,
        audit_logger=audit_logger,
        detection_scanner=scanner,      # Your Phase 3 scanner
        risk_validator=validator,       # Your Phase 4 validator
        automation_executor=executor    # Your Phase 5 executor
    )
    
    # Start orchestrator
    await orchestrator.start()
    
    try:
        # Submit opportunity for processing
        opportunity = ArbitrageOpportunity(
            id="demo_opportunity_001",
            symbol="BTC/USD",
            exchange_buy="Binance",
            exchange_sell="Coinbase",
            expected_profit=25.0,
            risk_tier=RiskTier.LOW_RISK
        )
        
        await orchestrator.submit_opportunity(opportunity)
        
        # Monitor processing
        while True:
            states = await orchestrator.get_opportunity_states()
            active_opportunities = [
                state for state in states 
                if state.state in [WorkflowState.PRESENTED, WorkflowState.EXECUTING]
            ]
            
            if active_opportunities:
                for state in active_opportunities:
                    print(f"Opportunity {state.opportunity_id}: {state.state.value}")
            else:
                break
                
            await asyncio.sleep(2)
    
    finally:
        # Graceful shutdown
        await orchestrator.shutdown(graceful=True)

# Run the example
asyncio.run(main())
```

## Components

### 1. Timeout Management 🚀
- **TimeoutManager**: Sophisticated timeout handling for opportunities with dynamic calculation
- **TimeoutRule**: Configurable timeout rules based on opportunity characteristics and custom factors
- **TimeoutEvent**: Event tracking for timeout-related actions with comprehensive logging
- **TimeoutMetrics**: Performance metrics for timeout management and optimization
- **High-Frequency Support**: Optimized for processing thousands of timeouts with minimal latency
- **Intelligent Escalation**: Multi-level escalation system with custom actions and triggers
- **Integration Ready**: Seamless integration with scanners, executors, and risk management systems

### 2. Result Logging
- **ResultLogger**: Comprehensive logging of human decisions and trade results
- **HumanDecision**: Models for tracking human intervention decisions
- **TradeResult**: Models for tracking trade outcomes and performance
- **PerformanceAnalytics**: Tools for analyzing human trader performance

### 3. Opportunity Presentation System 🎯
- **OpportunityPresenterSystem**: Main system for presenting opportunities
- **ConsolePresenter**: Console-based rich display for terminal environments
- **WebPresenter**: Web-based presentation using WebSockets for real-time updates
- **GUIPresenter**: GUI-based presentation (placeholder for future implementation)
- **OpportunityRanker**: Advanced ranking and comparison algorithms
- **HistoricalDataStore**: Management of historical performance data

## Features

### 🕐 Timeout Management Features

#### Dynamic Timeout Calculation
- **Profit-Based Timeouts**: Longer timeouts for higher profit opportunities
- **Risk-Adjusted Timing**: Shorter timeouts for higher-risk opportunities  
- **Sport-Specific Rules**: Optimized timeouts for different sports and markets
- **Bookmaker-Specific Factors**: Adjusted based on bookmaker stability and response times
- **Market Type Optimization**: Different timeouts for match_winner, over_under, handicaps, etc.
- **User-Specific Customization**: Premium users get extended timeouts

#### High-Performance Monitoring
- **Low-Latency Checking**: Sub-millisecond timeout validation
- **Optimized Data Structures**: Heap-based priority queue for efficient expiration tracking
- **Concurrent Processing**: Support for thousands of concurrent timeouts
- **Memory Efficient**: Weak references and garbage collection optimization
- **Batch Processing**: Grouped operations for better cache performance
- **Lock-Free Reading**: Read-heavy operations without locks

#### Intelligent Escalation System
- **Multi-Level Escalation**: Progressive escalation based on time remaining
- **Action Triggers**: Auto-reject, extend timeout, notify user, increase priority
- **Custom Escalation Rules**: Per user, bookmaker, sport, or risk tier
- **Emergency Stop**: Automatic intervention for critical situations
- **Escalation Analytics**: Comprehensive tracking of escalation patterns
- **Performance Monitoring**: Real-time metrics and performance optimization

#### Advanced Integration
- **Event-Driven Architecture**: Callback system for real-time notifications
- **Async Support**: Full asynchronous operation support
- **Scanner Integration**: Automatic timeout creation for new opportunities
- **Executor Integration**: Timeout removal on execution start/completion
- **Risk Management Integration**: Emergency stop capabilities
- **Plugin Architecture**: Extensible with custom timeout calculators

### 🎯 Opportunity Presentation Features

### Multi-Format Presentation
- **Console**: Rich terminal interface with colored formatting and tables
- **Web**: Real-time WebSocket-based presentation for web interfaces
- **GUI**: Graphical user interface (future implementation)
- **JSON**: Machine-readable output for integration with other systems

### Real-Time Features
- Live opportunity updates
- Instant ranking recalculation
- Historical performance integration
- Kelly criterion stake calculations
- Risk assessment visualization

### Advanced Analytics
- Intelligent opportunity ranking
- Comparative analysis
- Historical performance tracking
- Quality scoring algorithms
- Priority-based presentation

## Quick Start

### Basic Usage

```python
import asyncio
from arbitech.hitl import create_hitl_presenter, DisplayFormat
from arbitech.detection import OpportunityScanner
from arbitech.risk import KellyCalculator, RiskAnalyzer

async def main():
    # Create presenter system
    presenter = await create_hitl_presenter(
        display_formats=[DisplayFormat.CONSOLE, DisplayFormat.WEB],
        max_opportunities=50,
        update_interval=5.0
    )
    
    # Start the system
    await presenter.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await presenter.stop()

# Run the example
asyncio.run(main())
```

### 🕐 Timeout Management Quick Start

```python
from arbitech.hitl import TimeoutManager, TimeoutRule, EscalationAction
from arbitech.storage.models import ArbitrageOpportunity, Sport, RiskTier
from decimal import Decimal
from datetime import datetime
import asyncio

async def timeout_management_example():
    # Create timeout manager
    timeout_manager = TimeoutManager(
        check_interval_ms=100,  # Check every 100ms
        enable_performance_monitoring=True
    )
    
    # Start monitoring
    timeout_manager.start_monitoring()
    
    try:
        # Create custom timeout rule
        custom_rule = TimeoutRule(
            name="High-Frequency Trading",
            description="Very short timeouts for volatile markets",
            sport=Sport.ESPORTS,
            base_timeout_seconds=15,
            min_timeout_seconds=5,
            max_timeout_seconds=30,
            urgency_multiplier=Decimal('0.7'),
            enable_escalation=True,
            escalation_threshold_seconds=8,
            max_escalations=2,
            escalation_actions=[
                EscalationAction.NOTIFY_USER,
                EscalationAction.AUTO_REJECT
            ]
        )
        
        # Add rule to manager
        rule_id = timeout_manager.add_rule(custom_rule)
        
        # Create sample opportunity
        opportunity = ArbitrageOpportunity(
            sport=Sport.FOOTBALL,
            event_name="Manchester United vs Liverpool",
            event_date=datetime.utcnow() + timedelta(hours=2),
            market_type="match_winner",
            legs=[
                ArbitrageLeg(
                    bookmaker="bet365",
                    event_outcome="Manchester United wins",
                    odds=Decimal("2.10"),
                    implied_probability=Decimal("0.476"),
                    stake_percentage=Decimal("0.5"),
                    actual_stake=Decimal("50.00"),
                    potential_payout=Decimal("105.00")
                ),
                ArbitrageLeg(
                    bookmaker="william_hill",
                    event_outcome="Liverpool wins",
                    odds=Decimal("1.90"),
                    implied_probability=Decimal("0.526"),
                    stake_percentage=Decimal("0.5"),
                    actual_stake=Decimal("50.00"),
                    potential_payout=Decimal("95.00")
                )
            ],
            total_stake=Decimal("100.00"),
            profit_margin=Decimal("0.08"),  # 8% profit margin
            profit_amount=Decimal("8.00"),
            risk_tier=RiskTier.TIER_A
        )
        
        # Create timeout for opportunity
        timeout_id, expiration_time = timeout_manager.create_timeout(
            opportunity, 
            rule_id=rule_id
        )
        
        print(f"Created timeout {timeout_id}, expires at {expiration_time}")
        
        # Monitor timeout for a few seconds
        for i in range(5):
            await asyncio.sleep(2)
            remaining = timeout_manager.get_timeout_remaining(opportunity.id)
            status = timeout_manager.get_timeout_status(opportunity.id)
            print(f"Check {i+1}: {remaining:.1f}s remaining, status: {status.value}")
        
        # Extend timeout if needed
        extended = timeout_manager.extend_timeout(
            opportunity.id, 
            additional_seconds=30.0, 
            reason="demo_extension"
        )
        
        if extended:
            remaining = timeout_manager.get_timeout_remaining(opportunity.id)
            print(f"Extended timeout, now {remaining:.1f}s remaining")
        
        # Get performance metrics
        metrics = timeout_manager.get_metrics()
        print(f"Average check time: {metrics.average_check_time_ms:.2f}ms")
        print(f"Active opportunities: {metrics.active_opportunities}")
        
    finally:
        # Stop monitoring
        timeout_manager.stop_monitoring()

# Run timeout management example
asyncio.run(timeout_management_example())
```

### Performance Testing Demo

```python
import time
from arbitech.hitl import TimeoutManager

async def performance_test():
    timeout_manager = TimeoutManager(enable_performance_monitoring=True)
    timeout_manager.start_monitoring()
    
    try:
        # Create many opportunities for stress testing
        stress_opportunities = []
        for i in range(100):  # Create 100 opportunities
            # Create test opportunities (simplified)
            stress_opportunities.append(create_test_opportunity(i))
        
        # Create timeouts for all opportunities
        print(f"Creating {len(stress_opportunities)} timeouts...")
        start_time = time.time()
        
        for opp in stress_opportunities:
            timeout_manager.create_timeout(opp, custom_timeout_seconds=20.0 + i % 10)
        
        creation_time = time.time() - start_time
        print(f"Created {len(stress_opportunities)} timeouts in {creation_time:.2f}s")
        
        # Monitor performance
        for check_round in range(10):
            await asyncio.sleep(1)
            
            metrics = timeout_manager.get_metrics()
            near_timeout = timeout_manager.get_opportunities_near_timeout(
                threshold_seconds=5.0, 
                limit=10
            )
            
            print(
                f"Round {check_round + 1}: "
                f"{metrics.active_opportunities} active, "
                f"{len(near_timeout)} near timeout, "
                f"{metrics.average_check_time_ms:.2f}ms avg check time"
            )
        
    finally:
        timeout_manager.stop_monitoring()

asyncio.run(performance_test())
```

### Integration with Existing Components

```python
from arbitech.hitl import OpportunityPresenterSystem
from arbitech.detection import OpportunityScanner
from arbitech.risk import KellyCalculator, RiskAnalyzer
from arbitech.storage import AuditLogger

async def setup_full_system():
    # Create all components
    presenter_system = OpportunityPresenterSystem(
        display_formats=[DisplayFormat.CONSOLE, DisplayFormat.WEB]
    )
    
    scanner = OpportunityScanner()
    kelly_calculator = KellyCalculator()
    risk_analyzer = RiskAnalyzer()
    audit_logger = AuditLogger()
    
    # Integrate components
    presenter_system.integrate_scanner(scanner)
    presenter_system.integrate_kelly_calculator(kelly_calculator)
    presenter_system.integrate_risk_analyzer(risk_analyzer)
    presenter_system.integrate_audit_logger(audit_logger)
    
    # Start the system
    await presenter_system.start()
    
    return presenter_system
```

### Console Presentation Features

The console presenter provides:
- **Rich Tables**: Formatted opportunity displays
- **Color Coding**: Visual indicators for risk levels and profit margins
- **Real-Time Updates**: Live refresh of opportunity data
- **Detailed Leg Information**: Expandable opportunity details
- **Priority Ranking**: Smart sorting by calculated priority scores

### Web Presentation Features

The web presenter provides:
- **WebSocket Communication**: Real-time bidirectional communication
- **JSON Serialization**: Structured data format for web applications
- **Multiple Client Support**: Simultaneous connections from multiple users
- **Scalable Architecture**: Efficient broadcasting to multiple clients

## Configuration

### Display Formats

```python
from arbitech.hitl import DisplayFormat

# Available formats
formats = [
    DisplayFormat.CONSOLE,  # Terminal interface
    DisplayFormat.WEB,      # WebSocket interface  
    DisplayFormat.GUI,      # Graphical interface (future)
    DisplayFormat.JSON      # Machine-readable output
]
```

### System Configuration

```python
presenter_config = {
    'max_opportunities': 50,        # Maximum opportunities to display
    'update_interval': 5.0,         # Update frequency in seconds
    'historical_store_size': 10000, # Historical data store size
    'ranking_weights': {            # Custom ranking weights
        'profit_margin': 0.25,
        'kelly_fraction': 0.20,
        'historical_success': 0.20,
        'risk_score': 0.15,
        'liquidity_score': 0.10,
        'freshness_score': 0.10
    }
}
```

## 🕐 Timeout Management Configuration

### Basic Configuration

```python
timeout_manager = TimeoutManager(
    check_interval_ms=100,           # Check frequency (default: 100ms)
    enable_performance_monitoring=True,  # Collect metrics (default: True)
    max_concurrent_checks=1000       # Concurrent check limit (default: 1000)
)
```

### Custom Rule Configuration

```python
# High-profit, low-risk rule
high_profit_rule = TimeoutRule(
    name="High Profit Low Risk",
    description="Extended timeouts for high-profit, low-risk opportunities",
    risk_tier=RiskTier.TIER_A,
    base_timeout_seconds=60,
    profit_margin_multiplier=Decimal('1.5'),
    escalation_threshold_seconds=30,
    max_escalations=2
)

# High-frequency trading rule
hf_rule = TimeoutRule(
    name="High-Frequency Trading",
    description="Very short timeouts for volatile markets",
    sport=Sport.ESPORTS,
    base_timeout_seconds=15,
    min_timeout_seconds=5,
    max_timeout_seconds=30,
    urgency_multiplier=Decimal('0.7'),
    enable_escalation=True,
    escalation_threshold_seconds=8,
    max_escalations=2,
    escalation_actions=[
        EscalationAction.NOTIFY_USER,
        EscalationAction.AUTO_REJECT
    ]
)

# Sport-specific rules
football_rule = TimeoutRule(
    name="Football Extended",
    description="Extended timeouts for football markets",
    sport=Sport.FOOTBALL,
    base_timeout_seconds=60,
    liquidity_factor=Decimal('1.3'),
    max_escalations=4,
    escalation_actions=[
        EscalationAction.EXTEND_TIMEOUT,
        EscalationAction.NOTIFY_USER
    ]
)
```

### Timeout Calculation Factors

The timeout manager uses sophisticated algorithms to calculate optimal timeouts:

#### Profit Margin Impact
```python
profit_factor = 1.0 + (profit_margin * profit_multiplier * 0.5)
```
- Higher profit margins receive longer timeouts
- Configurable multiplier allows fine-tuning
- Exponential scaling for extreme cases

#### Risk Tier Adjustment
```python
risk_multipliers = {
    RiskTier.TIER_A: 1.2,  # Low risk gets more time
    RiskTier.TIER_B: 1.0,  # Standard time
    RiskTier.TIER_C: 0.8,  # Higher risk gets less time
    RiskTier.TIER_D: 0.6   # Highest risk gets least time
}
```

#### Sport-Specific Factors
```python
sport_multipliers = {
    Sport.FOOTBALL: 1.3,   # Complex markets, more time
    Sport.BASKETBALL: 1.1,
    Sport.TENNIS: 0.9,     # Faster markets, less time
    Sport.ESPORTS: 0.8,    # Very fast-moving, least time
}
```

#### Bookmaker Adjustments
```python
bookmaker_factors = {
    'pinnacle': 1.3,   # Very stable odds
    'bet365': 1.2,     # Stable platform
    'draftkings': 0.9, # Faster execution
    'fanduel': 0.9,    # Faster execution
}
```

### Escalation Configuration

```python
escalation_rule = TimeoutRule(
    name="Standard Escalation",
    enable_escalation=True,
    escalation_threshold_seconds=15,  # Escalate when 15s remaining
    max_escalations=3,                # Maximum 3 escalations
    escalation_actions=[
        EscalationAction.NOTIFY_USER,     # First: Notify user
        EscalationAction.EXTEND_TIMEOUT,  # Second: Extend timeout
        EscalationAction.AUTO_REJECT      # Final: Auto-reject
    ]
)
```

### Performance Optimization Settings

```python
# High-performance configuration
perf_config = TimeoutManager(
    check_interval_ms=50,              # Faster checking
    enable_performance_monitoring=True, # Detailed metrics
    max_concurrent_checks=5000         # Support more timeouts
)

# Memory-efficient configuration  
mem_config = TimeoutManager(
    check_interval_ms=200,             # Slower checking, less overhead
    enable_performance_monitoring=False, # Disable metrics collection
    max_concurrent_checks=500          # Lower concurrent limit
)
```

### Environment Configuration

```bash
# Timeout manager configuration
TIMEOUT_CHECK_INTERVAL_MS=100
TIMEOUT_MAX_CONCURRENT=1000
TIMEOUT_ENABLE_METRICS=true

# Escalation settings
TIMEOUT_ESCALATION_ENABLED=true
TIMEOUT_ESCALATION_THRESHOLD=15
TIMEOUT_MAX_ESCALATIONS=3

# Performance tuning
TIMEOUT_HEAP_SIZE_LIMIT=10000
TIMEOUT_CLEANUP_INTERVAL_HOURS=24
```

## 🕐 Timeout Management Integration Examples

### Scanner Integration

```python
from arbitech.hitl import integrate_with_opportunity_scanner

def on_opportunity_found(opportunity_data):
    """Handle new opportunity from scanner."""
    opportunity = opportunity_data['opportunity']
    
    # Create timeout automatically
    timeout_manager.create_timeout(opportunity)
    
    logger.info(f"Created timeout for opportunity {opportunity.id}")

# Integrate with scanner
integrate_with_opportunity_scanner(timeout_manager, scanner)
```

### Executor Integration

```python
from arbitech.hitl import integrate_with_arbitrage_executor

def on_execution_start(execution_data):
    """Handle execution start."""
    opportunity_id = execution_data.get('opportunity_id')
    
    # Remove timeout when execution starts
    timeout_manager.remove_timeout(
        opportunity_id, 
        "execution_started"
    )

def on_execution_timeout(execution_data):
    """Handle execution timeout."""
    opportunity_id = execution_data.get('opportunity_id')
    
    # Mark as execution timeout
    timeout_manager.remove_timeout(
        opportunity_id, 
        "execution_timeout"
    )

# Integrate with executor
integrate_with_arbitrage_executor(timeout_manager, executor)
```

### Risk Management Integration

```python
def on_emergency_stop(data):
    """Handle emergency stop signal."""
    opportunity_id = data.get('opportunity_id')
    
    # Immediate timeout removal
    timeout_manager.remove_timeout(
        opportunity_id,
        "emergency_stop"
    )
    
    # Notify risk management system
    risk_manager.handle_emergency_stop(opportunity_id)

# Register emergency callback
timeout_manager.register_timeout_callback(
    'emergency_stop_triggered', 
    on_emergency_stop
)
```

### Custom Callback Registration

```python
def on_timeout_created(data):
    logger.info(f"🚨 TIMEOUT CREATED: {data['opportunity_id']} - {data['timeout_seconds']:.1f}s")

def on_timeout_expired(data):
    logger.warning(f"⏰ TIMEOUT EXPIRED: {data['opportunity_id']}")

def on_timeout_extended(data):
    logger.info(f"⏳ TIMEOUT EXTENDED: {data['opportunity_id']} +{data['additional_seconds']:.1f}s")

def on_timeout_escalated(data):
    logger.warning(f"🚨 ESCALATION: {data['opportunity_id']} - {data['time_remaining']:.1f}s remaining")

def on_opportunity_auto_rejected(data):
    logger.error(f"❌ AUTO-REJECTED: {data['opportunity_id']} - {data['reason']}")

# Register all callbacks
timeout_manager.register_timeout_callback('timeout_created', on_timeout_created)
timeout_manager.register_timeout_callback('timeout_expired', on_timeout_expired)
timeout_manager.register_timeout_callback('timeout_extended', on_timeout_extended)
timeout_manager.register_timeout_callback('timeout_escalated', on_timeout_escalated)
timeout_manager.register_timeout_callback('opportunity_auto_rejected', on_opportunity_auto_rejected)
```

### Real-Time Monitoring

```python
async def monitor_timeouts():
    while True:
        # Get opportunities near timeout
        near_timeout = timeout_manager.get_opportunities_near_timeout(
            threshold_seconds=30.0,
            limit=50
        )
        
        for opp in near_timeout:
            logger.warning(
                f"🚨 URGENT: Opportunity {opp['opportunity_id']} has "
                f"{opp['time_remaining']:.1f}s remaining (status: {opp['status']})"
            )
        
        # Get performance metrics
        metrics = timeout_manager.get_metrics()
        if metrics.active_opportunities > 0:
            logger.info(
                f"📊 Active: {metrics.active_opportunities}, "
                f"Check Time: {metrics.average_check_time_ms:.2f}ms, "
                f"Frequency: {metrics.check_frequency_hz:.1f}Hz"
            )
        
        await asyncio.sleep(5)  # Check every 5 seconds

# Start monitoring
asyncio.create_task(monitor_timeouts())
```

## Opportunity Metrics

The system calculates comprehensive metrics for each opportunity:

### Core Metrics
- **Profit Margin**: Expected profit percentage
- **Profit Amount**: Expected profit in currency
- **Kelly Fraction**: Calculated Kelly criterion fraction
- **Kelly Stake**: Recommended stake amount
- **Risk Score**: Comprehensive risk assessment
- **Liquidity Score**: Market liquidity indicator
- **Freshness Score**: Data age and reliability

### Advanced Metrics
- **Historical Success Rate**: Past performance for similar opportunities
- **Quality Score**: Overall quality assessment
- **Priority Score**: Comprehensive ranking score
- **Estimated Execution Time**: Expected time to execute
- **Confidence Level**: Confidence in the opportunity

## Ranking Algorithm

The opportunity ranker uses a sophisticated algorithm:

### Weighted Scoring
1. **Profit Margin (25%)**: Higher margins score higher
2. **Kelly Fraction (20%)**: Moderate Kelly fractions preferred
3. **Historical Success (20%)**: Past performance indicator
4. **Risk Score (15%)**: Lower risk scores preferred
5. **Liquidity Score (10%)**: Higher liquidity preferred
6. **Freshness Score (10%)**: Recent data preferred

### Penalty Factors
- Over-aggressive Kelly fractions (>50%)
- Outdated odds data (>60 minutes)
- High risk scores (>70%)
- Low historical success rates

## Historical Performance Analysis

The system maintains historical performance data:

### Data Collection
- Trade outcomes and timing
- Profit/loss results
- Execution characteristics
- Risk factors and performance

### Analysis Features
- Success rate calculation
- Average profit tracking
- Sample size aggregation
- Performance trend analysis
- Similar opportunity identification

## Real-Time Updates

The system supports real-time updates through:

### Scanner Integration
- Direct integration with opportunity scanners
- Event-based update notifications
- Automatic opportunity refresh
- Live metric recalculation

### WebSocket Broadcasting
- Real-time updates to web clients
- Concurrent client support
- Event-driven architecture
- Scalable notification system

## Error Handling

Comprehensive error handling includes:

### Logging
- Detailed error logging
- Event tracking
- Performance monitoring
- Audit trail maintenance

### Recovery
- Graceful degradation
- Component isolation
- Automatic retry mechanisms
- Fallback presentation modes

## API Reference

### 🕐 Timeout Management API

#### TimeoutManager Class

```python
class TimeoutManager:
    def __init__(
        self,
        check_interval_ms: int = 100,
        enable_performance_monitoring: bool = True,
        max_concurrent_checks: int = 1000
    )
    
    # Core Methods
    def create_timeout(
        self,
        opportunity: ArbitrageOpportunity,
        custom_timeout_seconds: Optional[float] = None,
        rule_id: Optional[UUID] = None
    ) -> Tuple[UUID, float]
    
    def extend_timeout(
        self,
        opportunity_id: UUID,
        additional_seconds: float,
        reason: str = "manual_extension"
    ) -> bool
    
    def get_timeout_remaining(self, opportunity_id: UUID) -> Optional[float]
    def get_timeout_status(self, opportunity_id: UUID) -> TimeoutStatus
    def remove_timeout(
        self,
        opportunity_id: UUID,
        reason: str = "manual_removal"
    ) -> bool
    
    # Monitoring Methods
    def start_monitoring(self)
    def stop_monitoring(self)
    def get_opportunities_near_timeout(
        self,
        threshold_seconds: float = 30.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]
    def get_metrics(self) -> TimeoutMetrics
    
    # Rule Management
    def add_rule(self, rule: TimeoutRule) -> UUID
    def remove_rule(self, rule_id: UUID) -> bool
    def register_timeout_callback(self, event_type: str, callback: Callable)
    
    # Utility Methods
    def get_timeout_history(
        self,
        opportunity_id: UUID,
        limit: int = 10
    ) -> List[TimeoutEvent]
    def cleanup_expired_entries(self, max_age_hours: int = 24)
    def export_timeout_data(self) -> Dict[str, Any]
```

#### TimeoutRule Class

```python
@dataclass
class TimeoutRule:
    rule_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: Optional[str] = None
    
    # Rule Scope
    user_id: Optional[UUID] = None
    bookmaker: Optional[str] = None
    sport: Optional[Sport] = None
    market_type: Optional[str] = None
    risk_tier: Optional[RiskTier] = None
    
    # Timeout Parameters
    base_timeout_seconds: int = 30
    min_timeout_seconds: int = 10
    max_timeout_seconds: int = 300
    
    # Dynamic Factors
    profit_margin_multiplier: Decimal = Decimal('1.0')
    urgency_multiplier: Decimal = Decimal('1.0')
    liquidity_factor: Decimal = Decimal('1.0')
    
    # Escalation Settings
    enable_escalation: bool = True
    escalation_threshold_seconds: int = 20
    max_escalations: int = 3
    escalation_actions: List[EscalationAction] = field(default_factory=list)
    
    # Performance Settings
    check_interval_ms: int = 100
    enable_performance_monitoring: bool = True
    
    # Metadata
    is_active: bool = True
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
```

#### TimeoutEvent Class

```python
@dataclass
class TimeoutEvent:
    event_id: UUID = field(default_factory=uuid4)
    opportunity_id: UUID
    event_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Event Data
    original_timeout: Optional[float] = None
    new_timeout: Optional[float] = None
    time_remaining: Optional[float] = None
    action_taken: Optional[str] = None
    
    # Performance Metrics
    check_count: int = 0
    notification_sent: bool = False
    escalation_level: int = 0
```

#### TimeoutMetrics Class

```python
@dataclass
class TimeoutMetrics:
    # Timing Metrics
    average_check_time_ms: float = 0.0
    max_check_time_ms: float = 0.0
    min_check_time_ms: float = float('inf')
    
    # Opportunity Metrics
    total_opportunities: int = 0
    active_opportunities: int = 0
    expired_opportunities: int = 0
    extended_opportunities: int = 0
    escalated_opportunities: int = 0
    
    # Escalation Metrics
    total_escalations: int = 0
    escalations_by_type: Dict[EscalationAction, int] = field(default_factory=dict)
    
    # System Performance
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    check_frequency_hz: float = 0.0
    
    # Error Tracking
    timeout_errors: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
```

#### Enumerations

```python
class TimeoutStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EXTENDED = "extended"
    ESCALATED = "escalated"
    AUTO_REJECTED = "auto_rejected"
    EXECUTED = "executed"
    REMOVED = "removed"

class TimeoutSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EscalationAction(str, Enum):
    NOTIFY_USER = "notify_user"
    EXTEND_TIMEOUT = "extend_timeout"
    AUTO_REJECT = "auto_reject"
    INCREASE_PRIORITY = "increase_priority"
    TRIGGER_SCAN = "trigger_scan"
    EMERGENCY_STOP = "emergency_stop"
```

#### Utility Functions

```python
def create_timeout_manager_from_config(config: Dict[str, Any]) -> TimeoutManager
def integrate_with_opportunity_scanner(timeout_manager: TimeoutManager, scanner)
def integrate_with_arbitrage_executor(timeout_manager: TimeoutManager, executor)
```

### 🎯 Opportunity Presentation API

#### OpportunityPresenterSystem

```python
class OpportunityPresenterSystem:
    def __init__(self, display_formats, max_opportunities, update_interval)
    def integrate_scanner(self, scanner)
    def integrate_kelly_calculator(self, kelly_calculator)
    def integrate_risk_analyzer(self, risk_analyzer)
    def integrate_audit_logger(self, audit_logger)
    async def start(self)
    async def stop(self)
    async def add_opportunities(self, opportunities)
    async def update_opportunities(self, opportunities)
    async def remove_opportunities(self, opportunity_ids)
    async def compare_opportunities(self, primary_id, secondary_ids)
    def get_opportunities(self)
    def get_metrics(self)
    def get_statistics(self)
```

### Display Format Presenters

```python
class ConsolePresenter:
    async def initialize(self)
    async def display_opportunities(self, opportunities, metrics)
    async def update_opportunity(self, opportunity, metrics)
    async def remove_opportunity(self, opportunity_id)
    async def display_comparison(self, comparison)

class WebPresenter:
    async def initialize(self)
    async def display_opportunities(self, opportunities, metrics)
    async def update_opportunity(self, opportunity, metrics)
    async def remove_opportunity(self, opportunity_id)
    async def display_comparison(self, comparison)
    async def _broadcast_message(self, message)
```

## Examples

### Complete Integration Example

```python
import asyncio
from datetime import datetime
from decimal import Decimal
from arbitech.hitl import create_hitl_presenter, DisplayFormat
from arbitech.storage.models import ArbitrageOpportunity, ArbitrageLeg, Sport, RiskTier
from arbitech.detection import OpportunityScanner
from arbitech.risk import KellyCalculator, RiskAnalyzer

async def full_example():
    # Create presenter system
    presenter = await create_hitl_presenter(
        display_formats=[DisplayFormat.CONSOLE, DisplayFormat.WEB],
        max_opportunities=20,
        update_interval=3.0
    )
    
    # Start system
    await presenter.start()
    
    # Create demo opportunity
    opportunity = ArbitrageOpportunity(
        sport=Sport.FOOTBALL,
        event_name="Real Madrid vs Barcelona",
        event_date=datetime.utcnow(),
        market_type="match_winner",
        legs=[
            ArbitrageLeg(
                bookmaker="Bet365",
                event_outcome="Real Madrid Win",
                odds=Decimal('2.05'),
                implied_probability=Decimal('0.488'),
                stake_percentage=Decimal('0.488'),
                actual_stake=Decimal('100.00'),
                potential_payout=Decimal('205.00')
            ),
            ArbitrageLeg(
                bookmaker="Pinnacle", 
                event_outcome="Barcelona Win",
                odds=Decimal('2.10'),
                implied_probability=Decimal('0.476'),
                stake_percentage=Decimal('0.476'),
                actual_stake=Decimal('100.00'),
                potential_payout=Decimal('210.00')
            )
        ],
        total_stake=Decimal('200.00'),
        profit_margin=Decimal('0.025'),
        profit_amount=Decimal('5.00'),
        risk_tier=RiskTier.TIER_A
    )
    
    # Add opportunity
    await presenter.add_opportunities([opportunity])
    
    # Run for demonstration
    await asyncio.sleep(30)
    
    # Stop system
    await presenter.stop()

# Run example
asyncio.run(full_example())
```

### WebSocket Client Example

```python
import asyncio
import websockets
import json

async def web_client():
    uri = "ws://localhost:8765"
    
    async with websockets.connect(uri) as websocket:
        # Receive welcome message
        welcome = await websocket.recv()
        print(f"Server: {welcome}")
        
        # Listen for opportunities
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
            
            if data['type'] == 'opportunities_update':
                print(f"Found {len(data['data']['opportunities'])} opportunities")

asyncio.run(web_client())
```

## 🕐 Timeout Management Testing and Demo

### Comprehensive Demo

Run the complete timeout management demonstration:

```bash
cd /workspace/arbitech/hitl
python timeout_manager_demo.py
```

The demo includes:
- Basic timeout creation and management
- Performance testing with 50-100 concurrent opportunities  
- Integration testing with mock components
- Escalation scenario testing
- Cleanup and maintenance operations
- Real-time monitoring examples

### Unit Testing

```python
import pytest
from arbitech.hitl import TimeoutManager
from arbitech.storage.models import ArbitrageOpportunity, Sport, RiskTier

def test_timeout_creation():
    manager = TimeoutManager()
    opp = create_test_opportunity()
    
    timeout_id, expiration = manager.create_timeout(opp)
    
    assert timeout_id is not None
    assert expiration > time.time()
    assert manager.get_timeout_status(opp.id) == TimeoutStatus.ACTIVE

def test_timeout_expiration():
    manager = TimeoutManager()
    opp = create_test_opportunity()
    
    # Create very short timeout
    manager.create_timeout(opp, custom_timeout_seconds=0.1)
    
    time.sleep(0.2)  # Wait for expiration
    
    assert manager.get_timeout_status(opp.id) == TimeoutStatus.EXPIRED

def test_timeout_extension():
    manager = TimeoutManager()
    opp = create_test_opportunity()
    
    # Create timeout
    manager.create_timeout(opp, custom_timeout_seconds=10.0)
    initial_remaining = manager.get_timeout_remaining(opp.id)
    
    # Extend timeout
    extended = manager.extend_timeout(opp.id, 5.0, "test_extension")
    
    assert extended is True
    new_remaining = manager.get_timeout_remaining(opp.id)
    assert new_remaining > initial_remaining

def test_performance():
    manager = TimeoutManager()
    opportunities = create_test_opportunities(1000)
    
    start_time = time.time()
    
    for opp in opportunities:
        manager.create_timeout(opp)
    
    creation_time = time.time() - start_time
    print(f"Created 1000 timeouts in {creation_time:.3f}s")
    
    # Monitor check performance
    metrics = manager.get_metrics()
    assert metrics.average_check_time_ms < 10.0  # Less than 10ms average
```

### Integration Testing

```python
import asyncio
from arbitech.hitl import TimeoutManager, integrate_with_opportunity_scanner, integrate_with_arbitrage_executor

class MockScanner:
    def __init__(self):
        self.callbacks = {}
    
    def register_callback(self, event_type, callback):
        self.callbacks[event_type] = callback
    
    def simulate_opportunity_found(self, opportunity):
        if 'opportunity_found' in self.callbacks:
            self.callbacks['opportunity_found']({'opportunity': opportunity})

class MockExecutor:
    def __init__(self):
        self.callbacks = {}
    
    def register_callback(self, event_type, callback):
        self.callbacks[event_type] = callback
    
    def simulate_execution_start(self, opportunity_id):
        if 'execution_started' in self.callbacks:
            self.callbacks['execution_started']({'opportunity_id': opportunity_id})

async def integration_test():
    # Create components
    timeout_manager = TimeoutManager()
    mock_scanner = MockScanner()
    mock_executor = MockExecutor()
    
    # Integrate
    integrate_with_opportunity_scanner(timeout_manager, mock_scanner)
    integrate_with_arbitrage_executor(timeout_manager, mock_executor)
    
    # Start monitoring
    timeout_manager.start_monitoring()
    
    try:
        # Create test opportunity
        opp = create_test_opportunity()
        
        # Test scanner integration
        mock_scanner.simulate_opportunity_found(opp)
        await asyncio.sleep(0.1)
        
        # Check timeout was created
        status = timeout_manager.get_timeout_status(opp.id)
        assert status == TimeoutStatus.ACTIVE
        
        # Test executor integration
        mock_executor.simulate_execution_start(opp.id)
        await asyncio.sleep(0.1)
        
        # Check timeout was removed
        status = timeout_manager.get_timeout_status(opp.id)
        assert status == TimeoutStatus.REMOVED
        
        print("Integration test passed!")
        
    finally:
        timeout_manager.stop_monitoring()

# Run integration test
asyncio.run(integration_test())
```

### Performance Benchmarking

```python
import time
import statistics
from arbitech.hitl import TimeoutManager

def benchmark_timeout_performance():
    """Benchmark timeout manager performance."""
    
    test_sizes = [100, 500, 1000, 5000, 10000]
    results = []
    
    for size in test_sizes:
        print(f"\nBenchmarking {size} timeouts...")
        
        manager = TimeoutManager(enable_performance_monitoring=True)
        manager.start_monitoring()
        
        try:
            # Create opportunities and timeouts
            opportunities = create_test_opportunities(size)
            
            start_time = time.time()
            for opp in opportunities:
                manager.create_timeout(opp)
            creation_time = time.time() - start_time
            
            # Wait a bit for monitoring
            time.sleep(2)
            
            # Get metrics
            metrics = manager.get_metrics()
            
            results.append({
                'size': size,
                'creation_time': creation_time,
                'avg_check_time_ms': metrics.average_check_time_ms,
                'max_check_time_ms': metrics.max_check_time_ms,
                'memory_usage_mb': metrics.memory_usage_mb,
                'check_frequency_hz': metrics.check_frequency_hz
            })
            
            print(f"  Creation time: {creation_time:.3f}s")
            print(f"  Avg check time: {metrics.average_check_time_ms:.2f}ms")
            print(f"  Memory usage: {metrics.memory_usage_mb:.1f}MB")
            print(f"  Check frequency: {metrics.check_frequency_hz:.1f}Hz")
            
        finally:
            manager.stop_monitoring()
    
    # Print summary
    print("\n=== Performance Summary ===")
    for result in results:
        throughput = result['size'] / result['creation_time']
        print(f"{result['size']:>6} timeouts: {throughput:>8.1f} ops/sec, "
              f"{result['avg_check_time_ms']:>6.2f}ms check time")

# Run benchmark
benchmark_timeout_performance()
```

## Troubleshooting

### Common Issues

#### 🕐 Timeout Management Issues

1. **High Memory Usage**
   - **Symptoms**: Memory usage grows unbounded over time
   - **Causes**: Too many timeout entries without cleanup, missing weak reference implementation, event history not being pruned
   - **Solutions**:
     ```python
     # Enable regular cleanup
     manager.cleanup_expired_entries(max_age_hours=24)
     
     # Monitor memory usage
     metrics = manager.get_metrics()
     print(f"Memory usage: {metrics.memory_usage_mb:.1f}MB")
     ```

2. **Slow Check Performance**
   - **Symptoms**: High average check times, system lag
   - **Causes**: Too many active timeouts, check interval too frequent, expensive callback operations
   - **Solutions**:
     ```python
     # Increase check interval
     manager.check_interval_ms = 200
     
     # Use async callbacks for expensive operations
     async def expensive_callback(data):
         # Async operation here
         pass
     
     manager.register_timeout_callback('timeout_expired', expensive_callback)
     ```

3. **Escalation Loops**
   - **Symptoms**: Opportunities constantly being escalated
   - **Causes**: Escalation threshold too high, extension duration too short, missing maximum escalation limits
   - **Solutions**:
     ```python
     # Set reasonable escalation limits
     rule.max_escalations = 3
     rule.escalation_threshold_seconds = 10
     rule.base_timeout_seconds = 30
     ```

4. **Timeout Creation Failures**
   - **Symptoms**: Timeouts not being created for new opportunities
   - **Causes**: Invalid opportunity data, missing required fields, rule configuration errors
   - **Solutions**:
     ```python
     # Validate opportunity before timeout creation
     try:
         timeout_id, expiration = manager.create_timeout(opportunity)
     except Exception as e:
         logger.error(f"Timeout creation failed: {e}")
         # Check opportunity validation
     ```

5. **Performance Degradation Under Load**
   - **Symptoms**: System slows down with many concurrent timeouts
   - **Causes**: Inefficient data structures, blocking operations, memory allocation overhead
   - **Solutions**:
     ```python
     # Use optimized configuration
     manager = TimeoutManager(
         check_interval_ms=50,
         max_concurrent_checks=5000,
         enable_performance_monitoring=False  # Disable for maximum performance
     )
     ```

#### 🎯 Presentation System Issues

6. **WebSocket Connection Failures**
   - **Symptoms**: Web interface not connecting, connection timeouts
   - **Causes**: Port 8765 not available, firewall blocking, web presenter not initialized
   - **Solutions**:
     ```bash
     # Check if port is available
     netstat -an | grep 8765
     
     # Check firewall
     sudo ufw status
     ```

7. **Console Display Issues**
   - **Symptoms**: Garbled output, missing formatting, display errors
   - **Causes**: Terminal doesn't support ANSI codes, terminal too small, Python version incompatibility
   - **Solutions**:
     ```python
     # Check terminal compatibility
     import os
     print(f"Terminal: {os.environ.get('TERM', 'unknown')}")
     print(f"Size: {os.get_terminal_size()}")
     
     # Use simpler display mode if needed
     presenter = ConsolePresenter(use_unicode=False)
     ```

8. **Performance Issues**
   - **Symptoms**: Slow updates, high CPU usage, memory leaks
   - **Causes**: Too many opportunities, update frequency too high, inefficient rendering
   - **Solutions**:
     ```python
     # Reduce opportunities and update frequency
     presenter = OpportunityPresenterSystem(
         max_opportunities=20,      # Reduce from default 50
         update_interval=10.0       # Increase from default 5.0
     )
     ```

### Debugging

#### 🕐 Timeout Management Debugging

Enable comprehensive timeout management debugging:

```python
import logging

# Enable debug logging for timeout manager
logging.getLogger('arbitech.hitl.timeout_manager').setLevel(logging.DEBUG)

# Enable performance monitoring
timeout_manager = TimeoutManager(enable_performance_monitoring=True)

# Start monitoring
timeout_manager.start_monitoring()

# The system will now output detailed debug information
```

Debug timeout creation and management:

```python
# Enable callback debugging
def debug_callback(event_type, data):
    logger.debug(f"Timeout event: {event_type} - {data}")

timeout_manager.register_timeout_callback('timeout_created', debug_callback)
timeout_manager.register_timeout_callback('timeout_expired', debug_callback)
timeout_manager.register_timeout_callback('timeout_extended', debug_callback)
timeout_manager.register_timeout_callback('timeout_escalated', debug_callback)
```

Check timeout manager statistics and metrics:

```python
# Get comprehensive metrics
metrics = timeout_manager.get_metrics()
print(f"Average check time: {metrics.average_check_time_ms:.2f}ms")
print(f"Max check time: {metrics.max_check_time_ms:.2f}ms")
print(f"Memory usage: {metrics.memory_usage_mb:.1f}MB")
print(f"Active opportunities: {metrics.active_opportunities}")
print(f"Total escalations: {metrics.total_escalations}")

# Export debug data
debug_data = timeout_manager.export_timeout_data()
print(json.dumps(debug_data, indent=2, default=str))

# Get near-timeout opportunities for debugging
near_timeout = timeout_manager.get_opportunities_near_timeout(threshold_seconds=10.0)
for opp in near_timeout:
    print(f"Near timeout: {opp['opportunity_id']} - {opp['time_remaining']:.1f}s remaining")
```

Check timeout history for specific opportunities:

```python
# Get timeout events for debugging
events = timeout_manager.get_timeout_history(opportunity_id, limit=20)
for event in events:
    print(f"{event.timestamp}: {event.event_type} - {event.action_taken or 'no action'}")
```

Performance profiling:

```python
import cProfile
import pstats

def profile_timeout_operations():
    """Profile timeout operations for performance analysis."""
    
    def run_test():
        manager = TimeoutManager(enable_performance_monitoring=True)
        manager.start_monitoring()
        
        # Create test opportunities
        opportunities = create_test_opportunities(1000)
        
        # Time timeout creation
        start_time = time.time()
        for opp in opportunities:
            manager.create_timeout(opp)
        creation_time = time.time() - start_time
        
        print(f"Created 1000 timeouts in {creation_time:.3f}s")
        
        # Monitor for a few seconds
        time.sleep(5)
        
        manager.stop_monitoring()
    
    # Profile the operations
    cProfile.run('run_test()', 'timeout_profile.stats')
    
    # Analyze results
    stats = pstats.Stats('timeout_profile.stats')
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions

# Run profiling
profile_timeout_operations()
```

#### 🎯 Presentation System Debugging

Enable presentation system debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# The presentation system will now output detailed debug information
```

Check presentation system statistics:

```python
stats = presenter_system.get_statistics()
print(f"Active opportunities: {stats['total_opportunities']}")
print(f"Event count: {stats['event_count']}")
print(f"Historical entries: {stats['historical_entries']}")
print(f"WebSocket connections: {stats['websocket_connections']}")
print(f"Update frequency: {stats['update_frequency']:.2f}Hz")
```

Debug WebSocket connections:

```python
# Check WebSocket server status
if hasattr(presenter_system, 'web_presenter'):
    ws_stats = presenter_system.web_presenter.get_connection_stats()
    print(f"Active connections: {ws_stats['active_connections']}")
    print(f"Messages sent: {ws_stats['messages_sent']}")
    print(f"Messages received: {ws_stats['messages_received']}")
```

Debug console display:

```python
# Check console presenter status
if hasattr(presenter_system, 'console_presenter'):
    console_stats = presenter_system.console_presenter.get_display_stats()
    print(f"Display updates: {console_stats['updates']}")
    print(f"Characters rendered: {console_stats['characters_rendered']}")
    print(f"Table refreshes: {console_stats['table_refreshes']}")
```

## Future Enhancements

### 🕐 Timeout Management Planned Features
- **Machine Learning Optimization**: AI-driven timeout optimization based on historical performance
- **Real-Time Adaptation**: Dynamic rule adjustment based on market conditions and system performance
- **Advanced Analytics Dashboard**: Web-based dashboard for timeout metrics and performance analysis
- **Distributed Timeout Management**: Multi-node timeout coordination for high-availability systems
- **Predictive Timeout Calculation**: Machine learning models to predict optimal timeout durations
- **Integration with Market Data**: Real-time volatility and liquidity-based timeout adjustments
- **Custom Escalation Workflows**: Visual workflow designer for complex escalation scenarios
- **Timeout A/B Testing Framework**: Built-in testing system for comparing different timeout strategies
- **Mobile App Integration**: Mobile notifications and timeout management
- **Voice-Activated Timeout Control**: Voice commands for timeout management and emergency actions

### 🎯 Presentation System Planned Features
- **GUI Implementation**: Full graphical user interface
- **Mobile Support**: Mobile-optimized web interface
- **Advanced Analytics**: Machine learning-based ranking
- **Voice Integration**: Voice-activated opportunity review
- **Alert System**: Intelligent alert generation

### Integration Roadmap
- **Trading Platform Integration**: Direct execution capabilities
- **Portfolio Management**: Multi-account management
- **Risk Dashboard**: Comprehensive risk visualization
- **Performance Analytics**: Advanced performance metrics
- **Market Data Integration**: Real-time market condition awareness
- **Compliance Reporting**: Automated compliance and audit reporting
- **Multi-Asset Support**: Expansion beyond sports betting to financial markets
- **Social Trading**: Community features for sharing strategies and performance

## Contributing

When contributing to the HITL module:

### General Guidelines
1. Follow the existing code structure and patterns
2. Add comprehensive error handling and logging
3. Include unit tests for new functionality
4. Update documentation for API changes
5. Ensure backward compatibility where possible

### 🕐 Timeout Management Contributions
1. **Performance Considerations**: Always consider performance impact when modifying timeout logic
2. **Thread Safety**: Ensure all timeout operations are thread-safe
3. **Memory Management**: Use weak references and proper cleanup to prevent memory leaks
4. **Test Coverage**: Include performance benchmarks for timeout operations
5. **Documentation**: Update timeout calculation algorithms and rule examples
6. **Integration Testing**: Test integration with scanner, executor, and risk management systems
7. **Escalation Testing**: Test all escalation scenarios and edge cases
8. **Metrics Documentation**: Document new metrics and their interpretation

### Code Style for Timeout Management
```python
# Use type hints for all parameters
def create_timeout(self, opportunity: ArbitrageOpportunity, custom_timeout_seconds: Optional[float] = None) -> Tuple[UUID, float]

# Use dataclasses for configuration
@dataclass
class TimeoutRule:
    base_timeout_seconds: int = 30
    enable_escalation: bool = True

# Document complex algorithms
def _calculate_timeout(self, opportunity: ArbitrageOpportunity, rule_id: Optional[UUID] = None) -> float:
    """
    Calculate optimal timeout duration using multi-factor algorithm.
    
    Args:
        opportunity: Arbitrage opportunity to calculate timeout for
        rule_id: Optional specific rule to use for calculation
        
    Returns:
        Timeout duration in seconds
        
    Algorithm factors:
    - Base timeout from applicable rule
    - Profit margin multiplier (higher profit = more time)
    - Risk tier adjustment (higher risk = less time)
    - Sport-specific factors (football gets more time than esports)
    - Bookmaker stability factors
    - Market type adjustments
    """
```

### Testing Requirements for Timeout Management
```python
def test_timeout_calculation_accuracy():
    """Test timeout calculation with known expected values."""
    manager = TimeoutManager()
    rule = create_test_rule()
    
    # High profit, low risk should get longer timeout
    high_profit_opp = create_high_profit_low_risk_opportunity()
    long_timeout = manager._calculate_timeout(high_profit_opp, rule.rule_id)
    
    # Low profit, high risk should get shorter timeout  
    low_profit_opp = create_low_profit_high_risk_opportunity()
    short_timeout = manager._calculate_timeout(low_profit_opp, rule.rule_id)
    
    assert long_timeout > short_timeout

def test_performance_under_load():
    """Test timeout manager performance with many concurrent timeouts."""
    manager = TimeoutManager()
    opportunities = create_test_opportunities(5000)
    
    start_time = time.time()
    for opp in opportunities:
        manager.create_timeout(opp)
    creation_time = time.time() - start_time
    
    # Should create 5000 timeouts in under 1 second
    assert creation_time < 1.0
    
    # Monitor performance for a few seconds
    manager.start_monitoring()
    time.sleep(5)
    
    metrics = manager.get_metrics()
    assert metrics.average_check_time_ms < 10.0  # Check time under 10ms
    assert metrics.active_opportunities == 5000
```

### Performance Benchmarking Requirements
When contributing performance improvements:
1. Include before/after benchmarks
2. Test with various load levels (100, 1K, 10K, 50K timeouts)
3. Measure memory usage impact
4. Document optimization techniques used
5. Include thread safety considerations

## License

Part of the ARBitech Framework - see main project license.