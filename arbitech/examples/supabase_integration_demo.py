"""
Complete Integration Example: ARBitech + Supabase

This script demonstrates a full end-to-end integration between ARBitech's
trading system and the Supabase data persistence layer.

Features demonstrated:
1. Opportunity discovery and persistence
2. Risk analysis with edge functions
3. HITL decision logging
4. Trade execution tracking
5. Performance reporting
6. Real-time monitoring
"""

import asyncio
import os
import sys
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4
import logging

# Add arbitech to path
sys.path.insert(0, '/workspace/arbitech')

from storage.supabase_layer import get_data_layer
from storage.models import (
    ArbitrageOpportunity, ArbitrageLeg, Trade, StakeData, TradeTimestamps,
    Sport, RiskTier, TradeStatus, ExecutionMode
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_sample_opportunity():
    """Create a sample arbitrage opportunity."""
    logger.info("Creating sample opportunity...")
    
    opportunity = ArbitrageOpportunity(
        id=uuid4(),
        sport=Sport.FOOTBALL,
        event_name="Manchester United vs Liverpool",
        event_date=datetime.utcnow() + timedelta(hours=48),
        market_type="match_winner",
        legs=[
            ArbitrageLeg(
                bookmaker="Bet365",
                event_outcome="Manchester United Win",
                odds=Decimal('2.10'),
                implied_probability=Decimal('0.476'),
                stake_percentage=Decimal('0.476'),
                actual_stake=Decimal('47.60'),
                potential_payout=Decimal('100.00')
            ),
            ArbitrageLeg(
                bookmaker="Pinnacle",
                event_outcome="Liverpool Win",
                odds=Decimal('2.20'),
                implied_probability=Decimal('0.454'),
                stake_percentage=Decimal('0.454'),
                actual_stake=Decimal('45.40'),
                potential_payout=Decimal('100.00')
            ),
            ArbitrageLeg(
                bookmaker="Betfair",
                event_outcome="Draw",
                odds=Decimal('14.50'),
                implied_probability=Decimal('0.070'),
                stake_percentage=Decimal('0.070'),
                actual_stake=Decimal('7.00'),
                potential_payout=Decimal('100.00')
            )
        ],
        total_stake=Decimal('100.0'),
        profit_margin=Decimal('0.070'),
        profit_amount=Decimal('7.0'),
        guaranteed_profit=True,
        risk_tier=RiskTier.TIER_A,
        liquidity_checked=True,
        source_scanner="opportunity_scanner_v2",
        discovered_at=datetime.utcnow()
    )
    
    return opportunity


async def demonstrate_opportunity_workflow():
    """Demonstrate complete opportunity discovery and processing workflow."""
    logger.info("=== Opportunity Workflow Demo ===")
    
    data_layer = get_data_layer()
    
    # Step 1: Create and save opportunity
    logger.info("Step 1: Creating opportunity...")
    opportunity = await create_sample_opportunity()
    saved_opp = await data_layer.save_opportunity(opportunity)
    logger.info(f"Opportunity saved with ID: {saved_opp['id']}")
    
    # Step 2: Process opportunity with edge function (risk analysis)
    logger.info("Step 2: Processing opportunity with edge function...")
    import requests
    
    try:
        response = requests.post(
            'https://apailklayaphzswnxgya.supabase.co/functions/v1/process-opportunity',
            json={
                'opportunity_id': saved_opp['id'],
                'processing_type': 'risk_analysis'
            }
        )
        
        if response.status_code == 200:
            risk_data = response.json()['data']
            logger.info(f"Risk analysis complete:")
            logger.info(f"  - Risk score: {risk_data['risk_score']}")
            logger.info(f"  - Total implied probability: {risk_data['total_implied_probability']}")
            logger.info(f"  - Arbitrage margin: {risk_data['arbitrage_margin']}")
        else:
            logger.error(f"Edge function error: {response.text}")
            risk_data = {}
    except Exception as e:
        logger.error(f"Failed to call edge function: {e}")
        risk_data = {}
    
    # Step 3: Retrieve opportunity from database
    logger.info("Step 3: Retrieving opportunity from database...")
    opportunities = data_layer.get_opportunities(
        sport=Sport.FOOTBALL,
        risk_tier=RiskTier.TIER_A,
        limit=1
    )
    logger.info(f"Retrieved {len(opportunities)} opportunity(ies)")
    
    # Step 4: Get opportunity legs
    legs = data_layer.get_opportunity_legs(saved_opp['id'])
    logger.info(f"Retrieved {len(legs)} legs for opportunity")
    for leg in legs:
        logger.info(f"  - {leg['bookmaker']}: {leg['event_outcome']} @ {leg['odds']}")
    
    return saved_opp, risk_data


async def demonstrate_hitl_workflow(opportunity_id: str, risk_data: dict):
    """Demonstrate HITL decision logging."""
    logger.info("\n=== HITL Workflow Demo ===")
    
    data_layer = get_data_layer()
    
    # Simulate user review and decision
    user_id = str(uuid4())  # In production, get from authentication
    
    presented_at = datetime.utcnow()
    await asyncio.sleep(2)  # Simulate user review time
    decided_at = datetime.utcnow()
    
    # Log HITL decision
    logger.info("Logging HITL decision...")
    decision = await data_layer.log_hitl_decision(
        opportunity_id=opportunity_id,
        user_id=user_id,
        decision='approved',
        decision_reason='Acceptable risk, good profit margin, verified liquidity',
        risk_summary=risk_data,
        opportunity_snapshot={'profit_margin': 0.07, 'total_stake': 100.0},
        presented_at=presented_at,
        decided_at=decided_at
    )
    
    logger.info(f"HITL decision logged:")
    logger.info(f"  - Decision: approved")
    logger.info(f"  - Response time: {decision.get('response_time_ms', 0)}ms")
    
    return user_id


async def demonstrate_trade_workflow(opportunity: dict, user_id: str):
    """Demonstrate trade creation and tracking."""
    logger.info("\n=== Trade Workflow Demo ===")
    
    data_layer = get_data_layer()
    
    # Step 1: Create trade
    logger.info("Step 1: Creating trade...")
    
    # Reconstruct opportunity object for trade
    opp_obj = ArbitrageOpportunity(
        id=opportunity['id'],
        sport=Sport(opportunity['sport']),
        event_name=opportunity['event_name'],
        event_date=datetime.fromisoformat(opportunity['event_date']),
        market_type=opportunity['market_type'],
        legs=[],  # Simplified for demo
        total_stake=Decimal(str(opportunity['total_stake'])),
        profit_margin=Decimal(str(opportunity['profit_margin'])),
        profit_amount=Decimal(str(opportunity['profit_amount'])),
        guaranteed_profit=opportunity['guaranteed_profit'],
        risk_tier=RiskTier(opportunity['risk_tier'])
    )
    
    trade = Trade(
        id=uuid4(),
        user_id=uuid4() if not user_id else uuid4(),  # Use provided user_id
        opportunity=opp_obj,
        status=TradeStatus.PENDING,
        execution_mode=ExecutionMode.AUTO_FULL,
        stake_data=StakeData(
            total_stake=Decimal('100.0'),
            currency='USD',
            leg_allocations={
                'Bet365': Decimal('47.60'),
                'Pinnacle': Decimal('45.40'),
                'Betfair': Decimal('7.00')
            },
            fees_included=Decimal('0.0'),
            net_stake=Decimal('100.0')
        ),
        expected_profit=Decimal('7.0'),
        timestamps=TradeTimestamps()
    )
    
    saved_trade = await data_layer.create_trade(trade)
    trade_id = saved_trade['id']
    logger.info(f"Trade created with ID: {trade_id}")
    
    # Step 2: Update to placing bets
    logger.info("Step 2: Updating trade status to PLACING_BETS...")
    await data_layer.update_trade_status(
        trade_id,
        TradeStatus.PLACING_BETS
    )
    
    # Step 3: Log execution steps
    logger.info("Step 3: Logging execution steps...")
    
    await data_layer.add_execution_log(
        trade_id=trade_id,
        log_level='info',
        message='Starting bet placement on Bet365',
        details={'stake': 47.60, 'odds': 2.10},
        bookmaker='Bet365',
        step_name='place_bet_1'
    )
    
    await asyncio.sleep(1)  # Simulate execution time
    
    await data_layer.add_execution_log(
        trade_id=trade_id,
        log_level='info',
        message='Bet placed successfully on Bet365',
        details={'bet_id': 'BET123456', 'confirmation_time': datetime.utcnow().isoformat()},
        bookmaker='Bet365',
        step_name='bet_confirmed_1'
    )
    
    # Similar for other bookmakers...
    await data_layer.add_execution_log(
        trade_id=trade_id,
        log_level='info',
        message='All bets placed successfully',
        details={'total_bets': 3, 'total_stake': 100.0}
    )
    
    # Step 4: Update to filled
    logger.info("Step 4: Updating trade status to FILLED...")
    await data_layer.update_trade_status(
        trade_id,
        TradeStatus.FILLED,
        additional_data={'actual_profit': 6.95}  # Slight slippage
    )
    
    logger.info(f"Trade {trade_id} completed successfully")
    
    return trade_id


async def demonstrate_autonomous_workflow(opportunity_id: str):
    """Demonstrate autonomous decision logging."""
    logger.info("\n=== Autonomous Decision Workflow Demo ===")
    
    data_layer = get_data_layer()
    
    # Simulate AI decision
    logger.info("Logging autonomous decision...")
    
    decision = await data_layer.log_autonomous_decision(
        opportunity_id=opportunity_id,
        decision='execute',
        confidence_score=0.92,
        reasoning={
            'positive_factors': [
                'High profit margin (7%)',
                'Tier A risk classification',
                'Liquidity verified',
                'Event in 48 hours (good timing)'
            ],
            'negative_factors': [
                'Slight odds movement detected'
            ],
            'final_assessment': 'Execute with confidence'
        },
        risk_score=0.15,
        risk_factors=['odds_volatility']
    )
    
    logger.info(f"Autonomous decision logged:")
    logger.info(f"  - Decision: execute")
    logger.info(f"  - Confidence: 92%")
    logger.info(f"  - Risk score: 0.15")


async def demonstrate_risk_monitoring():
    """Demonstrate risk monitoring and alerts."""
    logger.info("\n=== Risk Monitoring Demo ===")
    
    data_layer = get_data_layer()
    
    # Create sample risk alert
    logger.info("Creating risk alert...")
    
    alert = await data_layer.create_risk_alert(
        alert_type='market_volatility_spike',
        severity='medium',
        title='Increased Market Volatility',
        description='Odds volatility increased by 25% in last 15 minutes',
        risk_metrics={
            'current_volatility': 0.15,
            'threshold': 0.12,
            'spike_percentage': 0.25,
            'affected_markets': ['match_winner', 'over_under']
        },
        recommended_action='Review open positions and consider hedging'
    )
    
    logger.info(f"Risk alert created: {alert['id']}")
    
    # Get unresolved alerts
    alerts = data_layer.get_unresolved_alerts(min_severity='medium')
    logger.info(f"Found {len(alerts)} unresolved alert(s)")
    
    # Simulate circuit breaker event
    logger.info("Simulating circuit breaker event...")
    
    event = await data_layer.log_circuit_breaker_event(
        breaker_type='max_loss_per_hour',
        trigger_value=225.0,
        threshold_value=200.0,
        description='Hourly loss limit exceeded: $225 > $200 threshold',
        affected_operations=['trading', 'autonomous_execution']
    )
    
    logger.info(f"Circuit breaker event logged: {event['id']}")


async def demonstrate_reporting():
    """Demonstrate performance reporting."""
    logger.info("\n=== Performance Reporting Demo ===")
    
    import requests
    
    # Generate report via edge function
    logger.info("Generating performance report...")
    
    try:
        response = requests.post(
            'https://apailklayaphzswnxgya.supabase.co/functions/v1/generate-report',
            json={'period_days': 7}
        )
        
        if response.status_code == 200:
            result = response.json()['data']
            metrics = result['metrics']
            
            logger.info("Performance Report Generated:")
            logger.info(f"  - Total trades: {metrics['total_trades']}")
            logger.info(f"  - Successful trades: {metrics['successful_trades']}")
            logger.info(f"  - Win rate: {metrics['win_rate']:.2%}")
            logger.info(f"  - Net profit: ${metrics['net_profit']:.2f}")
            logger.info(f"  - Avg profit/trade: ${metrics['avg_profit_per_trade']:.2f}")
            logger.info(f"  - Sharpe ratio: {metrics.get('sharpe_ratio', 'N/A')}")
            logger.info(f"  - Report saved: {result['saved']}")
        else:
            logger.error(f"Report generation failed: {response.text}")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")


async def demonstrate_system_monitoring():
    """Demonstrate system health monitoring."""
    logger.info("\n=== System Monitoring Demo ===")
    
    import requests
    
    # Trigger system monitoring
    logger.info("Running system health check...")
    
    try:
        response = requests.post(
            'https://apailklayaphzswnxgya.supabase.co/functions/v1/monitor-system',
            json={}
        )
        
        if response.status_code == 200:
            status = response.json()['data']
            
            logger.info("System Health Status:")
            logger.info(f"  - Status: {status['status']}")
            logger.info(f"  - Circuit breakers active: {status['circuit_breakers_active']}")
            logger.info(f"  - Critical alerts: {status['critical_alerts']}")
            logger.info(f"  - Recent trades: {status['recent_trades']}")
            logger.info(f"  - Loss rate: {status['loss_rate']:.2%}")
            logger.info(f"  - Consecutive losses: {status['consecutive_losses']}")
            
            if status['issues']:
                logger.warning(f"  - Issues detected: {len(status['issues'])}")
                for issue in status['issues']:
                    logger.warning(f"    * {issue['message']} [{issue['severity']}]")
        else:
            logger.error(f"System monitoring failed: {response.text}")
    except Exception as e:
        logger.error(f"Failed to monitor system: {e}")


async def main():
    """Run complete integration demonstration."""
    logger.info("=" * 60)
    logger.info("ARBitech + Supabase Integration Demo")
    logger.info("=" * 60)
    
    try:
        # 1. Opportunity workflow
        opportunity, risk_data = await demonstrate_opportunity_workflow()
        
        # 2. HITL workflow
        user_id = await demonstrate_hitl_workflow(opportunity['id'], risk_data)
        
        # 3. Trade workflow
        trade_id = await demonstrate_trade_workflow(opportunity, user_id)
        
        # 4. Autonomous decision
        await demonstrate_autonomous_workflow(opportunity['id'])
        
        # 5. Risk monitoring
        await demonstrate_risk_monitoring()
        
        # 6. Performance reporting
        await demonstrate_reporting()
        
        # 7. System monitoring
        await demonstrate_system_monitoring()
        
        logger.info("\n" + "=" * 60)
        logger.info("Integration Demo Complete!")
        logger.info("=" * 60)
        logger.info("\nKey Resources:")
        logger.info("  - Documentation: /workspace/arbitech/docs/SUPABASE_INTEGRATION_GUIDE.md")
        logger.info("  - API Reference: /workspace/arbitech/docs/SUPABASE_API_REFERENCE.md")
        logger.info("  - Data Layer: /workspace/arbitech/storage/supabase_layer.py")
        logger.info("  - Edge Functions: /workspace/arbitech/supabase/functions/")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    asyncio.run(main())
