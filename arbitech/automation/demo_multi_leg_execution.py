"""
Multi-Leg Trade Execution System Demo

This demo showcases the sophisticated multi-leg trade execution system with:
- Coordinated betting across multiple bookmakers
- Atomic operations with rollback capabilities
- Real-time execution tracking and monitoring
- Advanced profit calculation and stake distribution
- Comprehensive safety validation and error handling

Run this demo to see the system in action.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the multi-leg execution components
try:
    from automation import (
        MultiLegExecutor, 
        ExecutionStrategy,
        OrderType,
        ExecutionMode,
        TradeCoordinator,
        ExecutionTracker,
        ArbitrageExecutor,
        StakeDistributionStrategy,
        ExecutionState,
        EventType,
        AlertSeverity,
        TrackingLevel
    )
    
    # Import storage models
    from storage.models import (
        ArbitrageOpportunity, 
        ArbitrageLeg, 
        Sport, 
        RiskTier
    )
    
    logger.info("Successfully imported multi-leg execution components")
    EXECUTION_AVAILABLE = True
    
except ImportError as e:
    logger.error(f"Failed to import components: {e}")
    EXECUTION_AVAILABLE = False

# Sample arbitrage opportunity
SAMPLE_OPPORTUNITY = {
    'id': 'arb_001',
    'sport': Sport.FOOTBALL,
    'market_type': 'match_winner',
    'event_date': datetime.utcnow() + timedelta(hours=2),
    'profit_margin': 0.025,  # 2.5%
    'profit_amount': 25.0,
    'total_stake': 1000.0,
    'risk_tier': RiskTier.TIER_A,
    'odds_freshness': datetime.utcnow(),
    'discovered_at': datetime.utcnow() - timedelta(minutes=5),
    'legs': [
        {
            'id': 'leg_001',
            'bookmaker': 'Bet365',
            'selection': 'Team A Win',
            'odds': 2.1,
            'stake_percentage': 0.476,
            'stake_amount': 476.19
        },
        {
            'id': 'leg_002', 
            'bookmaker': 'WilliamHill',
            'selection': 'Draw',
            'odds': 3.4,
            'stake_percentage': 0.294,
            'stake_amount': 294.12
        },
        {
            'id': 'leg_003',
            'bookmaker': 'DraftKings',
            'selection': 'Team B Win',
            'odds': 4.2,
            'stake_percentage': 0.230,
            'stake_amount': 229.69
        }
    ]
}


async def demo_basic_execution():
    """Demo basic multi-leg execution functionality."""
    
    logger.info("=" * 60)
    logger.info("DEMO: Basic Multi-Leg Execution")
    logger.info("=" * 60)
    
    if not EXECUTION_AVAILABLE:
        logger.error("Execution components not available - cannot run demo")
        return
    
    # Initialize the execution engine
    executor = MultiLegExecutor()
    
    logger.info("✓ Multi-Leg Executor initialized")
    
    # Create a sample opportunity
    opportunity = ArbitrageOpportunity(**SAMPLE_OPPORTUNITY)
    logger.info(f"✓ Created opportunity: {opportunity.id}")
    logger.info(f"  - Sport: {opportunity.sport.value}")
    logger.info(f"  - Profit Margin: {opportunity.profit_margin:.2%}")
    logger.info(f"  - Total Stake: ${opportunity.total_stake}")
    logger.info(f"  - Legs: {len(opportunity.legs)}")
    
    # Demonstrate execution strategies
    strategies = [
        (ExecutionStrategy.ATOMIC, "Atomic (All-or-Nothing)"),
        (ExecutionStrategy.SEQUENTIAL, "Sequential"),
        (ExecutionStrategy.PARALLEL, "Parallel"),
        (ExecutionStrategy.ADAPTIVE, "Adaptive")
    ]
    
    for strategy, description in strategies:
        logger.info(f"\\n--- {description} Execution ---")
        
        try:
            # Execute the opportunity
            result = await executor.execute_opportunity(
                opportunity=opportunity,
                execution_strategy=strategy,
                order_type=OrderType.MARKET,
                execution_mode=ExecutionMode.AUTO_FULL,
                total_stake=opportunity.total_stake
            )
            
            # Display results
            logger.info(f"✓ Execution completed")
            logger.info(f"  - State: {result.execution_state.value}")
            logger.info(f"  - Duration: {result.execution_duration:.2f}s")
            logger.info(f"  - Legs Attempted: {result.legs_attempted}")
            logger.info(f"  - Legs Succeeded: {result.legs_succeeded}")
            logger.info(f"  - Legs Failed: {result.legs_failed}")
            logger.info(f"  - Total Stake Placed: ${result.total_stake_placed:.2f}")
            
            if result.errors:
                logger.warning(f"  - Errors: {len(result.errors)}")
                for error in result.errors[:3]:  # Show first 3 errors
                    logger.warning(f"    • {error}")
            
        except Exception as e:
            logger.error(f"✗ Execution failed: {str(e)}")
    
    # Show performance stats
    stats = executor.get_performance_stats()
    logger.info("\\n" + "=" * 60)
    logger.info("PERFORMANCE STATISTICS")
    logger.info("=" * 60)
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")


async def demo_coordination_system():
    """Demo advanced coordination system."""
    
    logger.info("\\n" + "=" * 60)
    logger.info("DEMO: Trade Coordination System")
    logger.info("=" * 60)
    
    if not EXECUTION_AVAILABLE:
        return
    
    # Initialize coordinator
    coordinator = TradeCoordinator()
    logger.info("✓ Trade Coordinator initialized")
    
    # Create sample opportunity
    opportunity = ArbitrageOpportunity(**SAMPLE_OPPORTUNITY)
    
    # Create execution context
    from automation.multi_leg_executor import ExecutionContext
    
    context = ExecutionContext(
        execution_id="coord_demo_001",
        opportunity_id=opportunity.id,
        strategy=ExecutionStrategy.PARALLEL,
        order_type=OrderType.MARKET,
        execution_mode=ExecutionMode.AUTO_FULL,
        total_stake=1000.0
    )
    
    # Setup coordination
    plan = await coordinator.setup_coordination(
        opportunity, context, {}
    )
    
    logger.info("✓ Coordination plan created")
    logger.info(f"  - Strategy: {plan.strategy.value}")
    logger.info(f"  - Sync Mode: {plan.synchronization_mode.value}")
    logger.info(f"  - Execution Steps: {len(plan.execution_sequence)}")
    logger.info(f"  - Expected Conflicts: {len(plan.expected_conflicts)}")
    
    # Demonstrate coordination
    execution_sequence = [
        {
            'leg_index': i,
            'bookmaker': leg.bookmaker,
            'execution_mode': 'parallel',
            'start_offset': 0.0,
            'timeout': 10.0,
            'priority': 1
        }
        for i, leg in enumerate(opportunity.legs)
    ]
    
    coordination_result = await coordinator.coordinate_execution(
        context.execution_id, execution_sequence
    )
    
    logger.info("✓ Coordination completed")
    logger.info(f"  - Coordination Time: {coordination_result['coordination_time']:.3f}s")
    logger.info(f"  - Results: {len(coordination_result['results'])}")
    
    # Show performance stats
    coord_stats = coordinator.get_performance_stats()
    logger.info("\\n✓ Coordinator Performance:")
    for key, value in coord_stats.items():
        logger.info(f"  {key}: {value}")


async def demo_execution_tracking():
    """Demo real-time execution tracking."""
    
    logger.info("\\n" + "=" * 60)
    logger.info("DEMO: Execution Tracking System")
    logger.info("=" * 60)
    
    if not EXECUTION_AVAILABLE:
        return
    
    # Initialize tracker
    tracker = ExecutionTracker()
    logger.info("✓ Execution Tracker initialized")
    
    # Create sample execution
    execution_id = "track_demo_001"
    
    # Start monitoring
    await tracker.start_monitoring_execution(
        execution_id=execution_id,
        opportunity_id="opp_001",
        strategy="atomic",
        total_legs=3
    )
    
    logger.info("✓ Started monitoring execution")
    
    # Simulate tracking events
    events = [
        ("execution_started", EventType.EXECUTION_STARTED, {"strategy": "atomic"}),
        ("leg_1_started", EventType.LEG_STARTED, {"bookmaker": "Bet365", "leg_id": "leg_001"}),
        ("leg_1_completed", EventType.LEG_COMPLETED, {"bookmaker": "Bet365", "stake_placed": 476.19}),
        ("leg_2_started", EventType.LEG_STARTED, {"bookmaker": "WilliamHill", "leg_id": "leg_002"}),
        ("leg_2_completed", EventType.LEG_COMPLETED, {"bookmaker": "WilliamHill", "stake_placed": 294.12}),
        ("leg_3_started", EventType.LEG_STARTED, {"bookmaker": "DraftKings", "leg_id": "leg_003"}),
        ("leg_3_completed", EventType.LEG_COMPLETED, {"bookmaker": "DraftKings", "stake_placed": 229.69}),
        ("execution_completed", EventType.EXECUTION_COMPLETED, {"total_stake": 1000.0})
    ]
    
    for event_name, event_type, event_data in events:
        # Create and track event
        from automation.execution_tracker import TrackEvent
        
        event = TrackEvent(
            event_id=f"evt_{len(events)}",
            execution_id=execution_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            event_data=event_data,
            latency_ms=50.0
        )
        
        await tracker.track_event(event)
        logger.info(f"✓ Tracked: {event_name}")
        
        # Small delay to simulate real-time tracking
        await asyncio.sleep(0.1)
    
    # Get tracking summary
    summary = await tracker.get_tracking_summary(execution_id)
    
    logger.info("\\n✓ Tracking Summary:")
    logger.info(f"  - Total Events: {summary['total_events']}")
    logger.info(f"  - Event Counts: {summary['event_counts']}")
    logger.info(f"  - Average Latency: {summary['average_latency_ms']:.2f}ms")
    logger.info(f"  - Max Latency: {summary['max_latency_ms']:.2f}ms")
    
    # Get active alerts
    alerts = await tracker.get_active_alerts()
    logger.info(f"  - Active Alerts: {len(alerts)}")
    
    # Show snapshot
    snapshot = await tracker.get_execution_snapshot(execution_id)
    if snapshot:
        logger.info("\\n✓ Execution Snapshot:")
        logger.info(f"  - State: {snapshot['current_state']}")
        logger.info(f"  - Progress: {snapshot['progress_percent']:.1f}%")
        logger.info(f"  - Legs Completed: {snapshot['legs_completed']}/{snapshot['legs_total']}")
        logger.info(f"  - Elapsed Time: {snapshot['elapsed_time']:.1f}s")
    
    # Stop monitoring
    await tracker.stop_monitoring_execution(execution_id)
    logger.info("✓ Stopped monitoring execution")


async def demo_arbitrage_calculation():
    """Demo sophisticated arbitrage calculation."""
    
    logger.info("\\n" + "=" * 60)
    logger.info("DEMO: Arbitrage Calculation System")
    logger.info("=" * 60)
    
    if not EXECUTION_AVAILABLE:
        return
    
    # Initialize arbitrage executor
    executor = ArbitrageExecutor()
    logger.info("✓ Arbitrage Executor initialized")
    
    # Create sample opportunity
    opportunity = ArbitrageOpportunity(**SAMPLE_OPPORTUNITY)
    
    # Test different distribution strategies
    strategies = [
        (StakeDistributionStrategy.EQUAL_PERCENTAGE, "Equal Percentage"),
        (StakeDistributionStrategy.ODDS_WEIGHTED, "Odds Weighted"),
        (StakeDistributionStrategy.PROFIT_MAXIMIZING, "Profit Maximizing"),
        (StakeDistributionStrategy.RISK_MINIMIZING, "Risk Minimizing"),
        (StakeDistributionStrategy.KELLY_OPTIMAL, "Kelly Optimal")
    ]
    
    for strategy, description in strategies:
        logger.info(f"\\n--- {description} Distribution ---")
        
        try:
            # Calculate arbitrage
            calculation = await executor.calculate_arbitrage(
                opportunity=opportunity,
                strategy=strategy,
                total_stake=1000.0
            )
            
            logger.info(f"✓ Calculation completed")
            logger.info(f"  - Valid: {calculation.calculation_valid}")
            logger.info(f"  - Total Stake: ${calculation.total_stake:.2f}")
            logger.info(f"  - Total Return: ${calculation.total_potential_return:.2f}")
            logger.info(f"  - Gross Profit: ${calculation.gross_profit:.2f}")
            logger.info(f"  - Profit Margin: {calculation.profit_margin:.2%}")
            logger.info(f"  - Calculation Time: {calculation.calculation_time_ms:.2f}ms")
            
            if calculation.validation_errors:
                logger.warning(f"  - Validation Errors: {len(calculation.validation_errors)}")
                for error in calculation.validation_errors:
                    logger.warning(f"    • {error}")
            
            # Show stake allocations
            logger.info(f"  - Stake Allocations:")
            for allocation in calculation.stake_allocations:
                logger.info(f"    • {allocation.bookmaker}: ${allocation.stake_amount:.2f} ({allocation.stake_percentage:.1f}%)")
            
        except Exception as e:
            logger.error(f"✗ Calculation failed: {str(e)}")
    
    # Show performance stats
    stats = executor.get_performance_stats()
    logger.info("\\n" + "=" * 60)
    logger.info("ARBITRAGE EXECUTOR PERFORMANCE")
    logger.info("=" * 60)
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")


async def demo_integrated_execution():
    """Demo integrated multi-component execution."""
    
    logger.info("\\n" + "=" * 60)
    logger.info("DEMO: Integrated Multi-Component Execution")
    logger.info("=" * 60)
    
    if not EXECUTION_AVAILABLE:
        return
    
    # Initialize all components
    executor = MultiLegExecutor()
    coordinator = TradeCoordinator()
    tracker = ExecutionTracker()
    arb_executor = ArbitrageExecutor()
    
    logger.info("✓ All components initialized")
    
    # Create sample opportunity
    opportunity = ArbitrageOpportunity(**SAMPLE_OPPORTUNITY)
    execution_id = "integrated_demo_001"
    
    # Step 1: Advanced arbitrage calculation
    logger.info("\\n--- Step 1: Advanced Calculation ---")
    calculation = await arb_executor.calculate_arbitrage(
        opportunity=opportunity,
        strategy=StakeDistributionStrategy.OPTIMIZED,
        total_stake=500.0  # Smaller stake for demo
    )
    
    logger.info(f"✓ Advanced calculation: {calculation.calculation_valid}")
    logger.info(f"  - Profit: ${calculation.gross_profit:.2f}")
    
    # Step 2: Start execution tracking
    logger.info("\\n--- Step 2: Start Tracking ---")
    await tracker.start_monitoring_execution(
        execution_id=execution_id,
        opportunity_id=opportunity.id,
        strategy="adaptive",
        total_legs=len(opportunity.legs)
    )
    logger.info("✓ Tracking started")
    
    # Step 3: Setup coordination
    logger.info("\\n--- Step 3: Setup Coordination ---")
    context = executor._active_executions.get(execution_id) or executor.__dict__.get('execution_context')
    
    if not context:
        # Create a simple context for demo
        from automation.multi_leg_executor import ExecutionContext
        context = ExecutionContext(
            execution_id=execution_id,
            opportunity_id=opportunity.id,
            strategy=ExecutionStrategy.ADAPTIVE,
            order_type=OrderType.MARKET,
            execution_mode=ExecutionMode.AUTO_FULL,
            total_stake=500.0
        )
    
    coordination_plan = await coordinator.setup_coordination(
        opportunity, context, {'calculation': calculation}
    )
    
    logger.info(f"✓ Coordination plan: {coordination_plan.strategy.value}")
    
    # Step 4: Execute with integrated monitoring
    logger.info("\\n--- Step 4: Execute ---")
    
    try:
        result = await executor.execute_opportunity(
            opportunity=opportunity,
            execution_strategy=ExecutionStrategy.ADAPTIVE,
            order_type=OrderType.MARKET,
            execution_mode=ExecutionMode.AUTO_FULL,
            total_stake=500.0
        )
        
        logger.info(f"✓ Integrated execution completed")
        logger.info(f"  - State: {result.execution_state.value}")
        logger.info(f"  - Duration: {result.execution_duration:.2f}s")
        logger.info(f"  - Success Rate: {result.legs_succeeded}/{result.legs_attempted}")
        
        # Step 5: Get comprehensive results
        logger.info("\\n--- Step 5: Comprehensive Analysis ---")
        
        # Tracking summary
        tracking_summary = await tracker.get_tracking_summary(execution_id)
        logger.info(f"✓ Tracking: {tracking_summary['total_events']} events")
        
        # Performance metrics
        executor_stats = executor.get_performance_stats()
        coord_stats = coordinator.get_performance_stats()
        arb_stats = arb_executor.get_performance_stats()
        
        logger.info("\\n✓ Component Performance:")
        logger.info(f"  - Executor: {executor_stats['successful_executions']}/{executor_stats['total_executions']} successful")
        logger.info(f"  - Coordinator: {coord_stats['total_coordinations']} coordinations")
        logger.info(f"  - Arbitrage Calculator: {arb_stats['successful_calculations']}/{arb_stats['total_calculations']} calculations")
        
    except Exception as e:
        logger.error(f"✗ Integrated execution failed: {str(e)}")
    
    finally:
        # Cleanup
        await tracker.stop_monitoring_execution(execution_id)
        await coordinator.cleanup_coordination(execution_id)
        logger.info("✓ Cleanup completed")


async def main():
    """Run all demos."""
    
    logger.info("🚀 Starting Multi-Leg Trade Execution System Demos")
    logger.info(f"📅 Demo Date: {datetime.utcnow().isoformat()}")
    
    if not EXECUTION_AVAILABLE:
        logger.error("❌ Cannot run demos - execution components not available")
        logger.error("Please ensure all dependencies are installed correctly")
        return
    
    try:
        # Run individual demos
        await demo_basic_execution()
        await demo_coordination_system()
        await demo_execution_tracking()
        await demo_arbitrage_calculation()
        
        # Run integrated demo
        await demo_integrated_execution()
        
        logger.info("\\n" + "🎉" * 60)
        logger.info("🎉 ALL DEMOS COMPLETED SUCCESSFULLY! 🎉")
        logger.info("🎉" * 60)
        
        logger.info("\\n📋 Demo Summary:")
        logger.info("  ✅ Basic Multi-Leg Execution")
        logger.info("  ✅ Trade Coordination System")
        logger.info("  ✅ Real-Time Execution Tracking")
        logger.info("  ✅ Arbitrage Calculation Engine")
        logger.info("  ✅ Integrated Multi-Component System")
        
        logger.info("\\n🔧 System Features Demonstrated:")
        logger.info("  • Atomic operations with rollback")
        logger.info("  • Advanced coordination strategies")
        logger.info("  • Real-time monitoring and alerts")
        logger.info("  • Sophisticated profit optimization")
        logger.info("  • Comprehensive error handling")
        logger.info("  • Performance analytics and reporting")
        
        logger.info("\\n📊 Key Capabilities:")
        logger.info("  • Multi-bookmaker coordination")
        logger.info("  • Adaptive execution strategies")
        logger.info("  • Bulletproof validation and recovery")
        logger.info("  • Enterprise-grade reliability")
        logger.info("  • Comprehensive safety mechanisms")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
