"""
Paper Trading Demo and Testing Script

This script demonstrates the complete paper trading system functionality
including real-time simulation, backtesting, and performance analytics.

Usage:
    python demo_paper_trading.py [demo_type]

Demo types:
    - full: Complete paper trading demonstration
    - backtest: Backtesting demonstration
    - hybrid: Hybrid mode demonstration
    - performance: Performance analytics demonstration
"""

import asyncio
import json
import logging
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

# Import the paper trading system
from paper_trading import (
    PaperTradingSystem, TradingMode, MarketCondition, Sport, RiskTier,
    create_paper_trading_system, load_sample_opportunities,
    demo_paper_trading, demo_backtest
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def full_paper_trading_demo() -> None:
    """Complete paper trading demonstration with all features."""
    print("=" * 80)
    print("🚀 COMPREHENSIVE PAPER TRADING DEMONSTRATION")
    print("=" * 80)
    
    # Create system
    system = create_paper_trading_system(
        mode=TradingMode.PAPER,
        initial_bankroll=Decimal('100000.00')
    )
    
    print(f"\n📊 System Initialized:")
    print(f"   Mode: {system.mode}")
    print(f"   Initial Bankroll: ${system.initial_bankroll:,.2f}")
    print(f"   Virtual Accounts: {len(system.virtual_accounts)}")
    
    # Start simulation
    await system.start_paper_trading()
    
    print(f"\n⏱️ Simulation Started at {system.simulation_start_time}")
    
    # Load and process opportunities
    opportunities = load_sample_opportunities(15)
    
    print(f"\n🎯 Processing {len(opportunities)} Opportunities...")
    
    user_id = uuid4()
    processed_count = 0
    successful_trades = 0
    
    for i, opportunity in enumerate(opportunities):
        print(f"\n--- Opportunity {i+1}/{len(opportunities)} ---")
        print(f"Sport: {opportunity.sport.value.title()}")
        print(f"Event ID: {opportunity.event_id}")
        print(f"Profit Margin: {opportunity.profit_margin:.2%}")
        print(f"Risk Tier: {opportunity.risk_tier.value.upper()}")
        print(f"Legs: {len(opportunity.legs)}")
        
        # Process opportunity
        trade = await system.process_opportunity(opportunity, user_id)
        processed_count += 1
        
        print(f"Status: {trade.status}")
        if trade.actual_profit:
            print(f"Profit: ${trade.actual_profit:.2f}")
            if trade.actual_profit > 0:
                successful_trades += 1
        
        print(f"Execution Time: {trade.execution_time_ms}ms")
        print(f"Total Slippage: {trade.total_slippage:.3%}")
        
        if trade.error_messages:
            print(f"Errors: {', '.join(trade.error_messages)}")
        
        # Simulate market changes
        if i % 3 == 0:
            system.simulate_market_event(MarketCondition.VOLATILE, 2)
            print("📈 Market condition changed to VOLATILE")
        
        await asyncio.sleep(0.5)  # Small delay
    
    # Generate comprehensive report
    print("\n" + "=" * 80)
    print("📈 PERFORMANCE REPORT")
    print("=" * 80)
    
    report = system.get_performance_report()
    metrics = report["performance_metrics"]
    
    print(f"\n💰 Financial Performance:")
    print(f"   Total Trades: {metrics['total_trades']}")
    print(f"   Successful Trades: {metrics['successful_trades']}")
    print(f"   Failed Trades: {metrics['failed_trades']}")
    print(f"   Win Rate: {metrics['win_rate']:.1f}%")
    print(f"   Net Profit: ${metrics['net_profit']:,.2f}")
    print(f"   ROI: {metrics['roi_percentage']:.2f}%")
    print(f"   Average Profit per Trade: ${metrics['average_profit_per_trade']:.2f}")
    
    print(f"\n⚡ Execution Performance:")
    print(f"   Average Execution Time: {metrics['average_execution_time_ms']}ms")
    print(f"   Total Slippage: {metrics['total_slippage']:.3f}")
    print(f"   Average Slippage: {metrics['average_slippage']:.4f}")
    
    print(f"\n🏆 Best/Worst Trades:")
    print(f"   Best Trade: ${metrics['best_trade']:.2f}")
    print(f"   Worst Trade: ${metrics['worst_trade']:.2f}")
    
    print(f"\n🥇 Performance by Sport:")
    for sport, profit in metrics['profit_by_sport'].items():
        print(f"   {sport.value.title()}: ${profit:.2f}")
    
    print(f"\n🏢 Performance by Bookmaker:")
    for bookmaker, profit in list(metrics['profit_by_bookmaker'].items())[:5]:
        print(f"   {bookmaker}: ${profit:.2f}")
    
    print(f"\n⚠️ Performance by Risk Tier:")
    for tier, profit in metrics['profit_by_risk_tier'].items():
        print(f"   {tier.value.upper()}: ${profit:.2f}")
    
    # Account summary
    print(f"\n💳 Virtual Account Status:")
    account_summary = system.get_account_summary()
    print(f"   Total Accounts: {account_summary['total_accounts']}")
    print(f"   Total Balance: ${account_summary['total_balance']:,.2f}")
    print(f"   Available Balance: ${account_summary['total_available_balance']:,.2f}")
    print(f"   Reserved Balance: ${account_summary['total_reserved_balance']:,.2f}")
    
    # Show some individual account details
    print(f"\n   Account Details (Top 3 by balance):")
    sorted_accounts = sorted(
        [(name, acc) for name, acc in system.virtual_accounts.items()],
        key=lambda x: x[1].balance,
        reverse=True
    )[:3]
    
    for bookmaker, account in sorted_accounts:
        print(f"   {bookmaker}:")
        print(f"      Balance: ${account.balance:,.2f}")
        print(f"      Available: ${account.get_available_balance():,.2f}")
        print(f"      Status: {account.status}")
    
    # Export results
    export_path = f"/workspace/arbitech/testing/paper_trade_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    system.export_trade_history(export_path, format="json")
    print(f"\n💾 Trade history exported to: {export_path}")
    
    # Stop simulation
    await system.stop_paper_trading()
    
    print(f"\n✅ Full paper trading demonstration completed!")
    print(f"📊 Success Rate: {successful_trades}/{processed_count} ({successful_trades/processed_count*100:.1f}%)")


async def backtest_demo() -> None:
    """Demonstrate backtesting functionality with realistic data."""
    print("=" * 80)
    print("🔍 BACKTESTING DEMONSTRATION")
    print("=" * 80)
    
    # Create backtesting system
    system = create_paper_trading_system(
        mode=TradingMode.BACKTEST,
        initial_bankroll=Decimal('50000.00')
    )
    
    print(f"\n📊 Backtest System Initialized:")
    print(f"   Initial Bankroll: ${system.initial_bankroll:,.2f}")
    
    # Generate realistic backtest data
    print(f"\n📈 Generating synthetic backtest data...")
    
    start_date = datetime.now() - timedelta(days=30)
    sports = [Sport.FOOTBALL, Sport.BASKETBALL, Sport.TENNIS]
    bookmakers = ["Pinnacle", "Bet365", "William Hill", "Unibet", "Betfair"]
    
    data_records = []
    
    # Generate 500 events over 30 days
    for day in range(30):
        current_date = start_date + timedelta(days=day)
        
        # 15-25 events per day
        daily_events = 15 + (day % 10)
        
        for event_idx in range(daily_events):
            sport = sports[event_idx % len(sports)]
            event_id = f"backtest_{day}_{event_idx}"
            
            # Generate odds for multiple bookmakers
            base_odds = 2.0 + (sport.value == 'tennis') * 0.3  # Tennis typically higher odds
            
            for bookmaker in bookmakers:
                # Simulate bookmaker-specific odds with realistic variance
                volatility = 0.15 if bookmaker == "Bet365" else 0.08
                odds_variation = 1.0 + (event_idx % 3 - 1) * 0.05  # Trend component
                random_variation = 1.0 + (hash(f"{bookmaker}_{event_id}") % 100 - 50) * 0.001
                
                odds = Decimal(str(round(base_odds * odds_variation * random_variation, 2)))
                odds = max(Decimal('1.2'), min(odds, Decimal('10.0')))  # Realistic bounds
                
                data_records.append({
                    'sport': sport.value,
                    'event_id': event_id,
                    'bookmaker': bookmaker,
                    'odds': float(odds),
                    'timestamp': current_date + timedelta(hours=event_idx)
                })
    
    # Create DataFrame
    backtest_data = pd.DataFrame(data_records)
    
    print(f"Generated {len(backtest_data)} data points")
    print(f"Date range: {backtest_data['timestamp'].min()} to {backtest_data['timestamp'].max()}")
    print(f"Unique events: {backtest_data['event_id'].nunique()}")
    print(f"Sports: {', '.join(backtest_data['sport'].unique())}")
    print(f"Bookmakers: {', '.join(backtest_data['bookmaker'].unique())}")
    
    # Load data and run backtest
    system.load_backtest_data(backtest_data)
    
    print(f"\n🔍 Running backtest analysis...")
    print(f"Minimum profit margin threshold: 2.0%")
    
    results = await system.run_backtest(
        min_profit_margin=Decimal('0.02')
    )
    
    # Display results
    print("\n" + "=" * 80)
    print("📊 BACKTEST RESULTS")
    print("=" * 80)
    
    print(f"\n📈 Financial Performance:")
    print(f"   Initial Bankroll: ${results['initial_bankroll']:,.2f}")
    print(f"   Final Bankroll: ${results['final_bankroll']:,.2f}")
    print(f"   Total Profit: ${results['total_profit']:,.2f}")
    print(f"   ROI: {results['roi']:.2f}%")
    
    print(f"\n📊 Trade Statistics:")
    print(f"   Total Opportunities: {results['total_trades']}")
    print(f"   Profitable Trades: {results['profitable_trades']}")
    print(f"   Losing Trades: {results['losing_trades']}")
    print(f"   Win Rate: {results['win_rate']:.1f}%")
    print(f"   Average Profit per Trade: ${results['average_profit_per_trade']:.2f}")
    
    print(f"\n🏆 Trade Extremes:")
    print(f"   Best Trade: ${results['best_trade']:.2f}")
    print(f"   Worst Trade: ${results['worst_trade']:.2f}")
    
    print(f"\n⚡ Execution Quality:")
    print(f"   Total Slippage: {results['total_slippage']:.4f}")
    print(f"   Average Slippage: {results['average_slippage']:.4f}")
    print(f"   Avg Execution Time: {results['execution_time_stats']['average_ms']:.1f}ms")
    
    print(f"\n🥇 Performance by Sport:")
    for sport, profit in results['profit_by_sport'].items():
        print(f"   {sport.title()}: ${profit:.2f}")
    
    # Performance analysis
    if results['total_trades'] > 0:
        profitable_pct = results['profitable_trades'] / results['total_trades'] * 100
        avg_trade_size = results['total_profit'] / results['total_trades'] if results['total_trades'] > 0 else 0
        
        print(f"\n📋 Analysis:")
        if profitable_pct > 60:
            print(f"   ✅ Excellent win rate: {profitable_pct:.1f}%")
        elif profitable_pct > 45:
            print(f"   ✅ Good win rate: {profitable_pct:.1f}%")
        else:
            print(f"   ⚠️  Low win rate: {profitable_pct:.1f}%")
        
        if avg_trade_size > 10:
            print(f"   ✅ High average profit per trade: ${avg_trade_size:.2f}")
        elif avg_trade_size > 5:
            print(f"   ✅ Moderate average profit per trade: ${avg_trade_size:.2f}")
        else:
            print(f"   ⚠️  Low average profit per trade: ${avg_trade_size:.2f}")
        
        if results['average_slippage'] < 0.01:
            print(f"   ✅ Low slippage impact: {results['average_slippage']:.3%}")
        else:
            print(f"   ⚠️  High slippage impact: {results['average_slippage']:.3%}")
    
    print(f"\n✅ Backtest demonstration completed!")


async def hybrid_mode_demo() -> None:
    """Demonstrate hybrid paper/live trading mode."""
    print("=" * 80)
    print("🔄 HYBRID MODE DEMONSTRATION")
    print("=" * 80)
    
    # Create hybrid system
    system = create_paper_trading_system(
        mode=TradingMode.HYBRID,
        initial_bankroll=Decimal('75000.00')
    )
    
    print(f"\n📊 Hybrid System Initialized:")
    print(f"   Mode: {system.mode}")
    print(f"   Initial Bankroll: ${system.initial_bankroll:,.2f}")
    
    # Start hybrid mode
    await system.start_paper_trading()
    
    print(f"\n🔄 Hybrid mode allows combination of paper and live trading")
    print(f"   - Paper trades for testing new strategies")
    print(f"   - Live trades for proven opportunities")
    print(f"   - Risk-based mode switching")
    
    # Simulate hybrid workflow
    opportunities = load_sample_opportunities(8)
    
    print(f"\n🎯 Processing opportunities with hybrid logic...")
    
    user_id = uuid4()
    paper_trades = 0
    live_trades = 0
    
    for i, opportunity in enumerate(opportunities):
        print(f"\n--- Opportunity {i+1} ---")
        print(f"Profit Margin: {opportunity.profit_margin:.2%}")
        print(f"Risk Tier: {opportunity.risk_tier.value.upper()}")
        
        # Hybrid decision logic
        if opportunity.risk_tier == RiskTier.TIER_A and opportunity.profit_margin > Decimal('0.03'):
            # High-confidence, high-profit -> Live trading
            print(f"🎯 Decision: LIVE TRADING (Tier A + High Profit)")
            live_trades += 1
            # In real implementation, this would trigger live execution
        else:
            # Everything else -> Paper trading for testing
            print(f"🧪 Decision: PAPER TRADING (Testing)")
            trade = await system.process_opportunity(opportunity, user_id)
            paper_trades += 1
            
            print(f"   Status: {trade.status}")
            if trade.actual_profit:
                print(f"   Paper Profit: ${trade.actual_profit:.2f}")
        
        await asyncio.sleep(0.3)
    
    print(f"\n📊 Hybrid Mode Summary:")
    print(f"   Paper Trades: {paper_trades}")
    print(f"   Live Trades: {live_trades}")
    print(f"   Total Opportunities: {len(opportunities)}")
    
    await system.stop_paper_trading()
    
    print(f"\n✅ Hybrid mode demonstration completed!")


async def performance_analytics_demo() -> None:
    """Demonstrate advanced performance analytics."""
    print("=" * 80)
    print("📊 PERFORMANCE ANALYTICS DEMONSTRATION")
    print("=" * 80)
    
    # Create high-volume trading system
    system = create_paper_trading_system(
        mode=TradingMode.PAPER,
        initial_bankroll=Decimal('200000.00')
    )
    
    print(f"\n📊 High-volume system initialized:")
    print(f"   Initial Bankroll: ${system.initial_bankroll:,.2f}")
    
    # Generate larger dataset
    opportunities = load_sample_opportunities(50)
    
    print(f"\n🎯 Processing {len(opportunities)} opportunities for analytics...")
    
    user_id = uuid4()
    
    # Start simulation
    await system.start_paper_trading()
    
    # Process opportunities with different market conditions
    market_conditions = [
        MarketCondition.STABLE,
        MarketCondition.VOLATILE,
        MarketCondition.LOW_LIQUIDITY,
        MarketCondition.HIGH_LIQUIDITY
    ]
    
    for i, opportunity in enumerate(opportunities):
        # Change market condition every 10 trades
        if i % 10 == 0 and i > 0:
            condition = market_conditions[(i // 10) % len(market_conditions)]
            system.simulate_market_event(condition, 5)
            print(f"📈 Market condition: {condition.value}")
        
        trade = await system.process_opportunity(opportunity, user_id)
        
        if i % 10 == 0:  # Progress update every 10 trades
            report = system.get_performance_report()
            metrics = report["performance_metrics"]
            print(f"   Progress: {i+1}/{len(opportunities)} trades")
            print(f"   Current Win Rate: {metrics['win_rate']:.1f}%")
            print(f"   Current ROI: {metrics['roi_percentage']:.2f}%")
        
        await asyncio.sleep(0.1)
    
    # Generate detailed analytics
    print(f"\n" + "=" * 80)
    print("📊 ADVANCED PERFORMANCE ANALYTICS")
    print("=" * 80)
    
    report = system.get_performance_report()
    metrics = report["performance_metrics"]
    
    # Time-based analysis
    print(f"\n⏰ Time-based Analysis:")
    print(f"   Simulation Duration: {report['simulation_duration']}")
    trades_by_hour = metrics['trades_by_hour']
    peak_hour = max(trades_by_hour, key=trades_by_hour.get)
    print(f"   Peak Trading Hour: {peak_hour}:00 ({trades_by_hour[peak_hour]} trades)")
    print(f"   Average Trades per Hour: {sum(trades_by_hour.values()) / 24:.1f}")
    
    # Risk-adjusted returns
    print(f"\n⚖️ Risk Analysis:")
    tier_performance = metrics['profit_by_risk_tier']
    if tier_performance:
        best_tier = max(tier_performance, key=tier_performance.get)
        worst_tier = min(tier_performance, key=tier_performance.get)
        print(f"   Best Performing Tier: {best_tier.value.upper()} (${tier_performance[best_tier]:.2f})")
        print(f"   Worst Performing Tier: {worst_tier.value.upper()} (${tier_performance[worst_tier]:.2f})")
    
    # Bookmaker analysis
    print(f"\n🏢 Bookmaker Performance:")
    bookmaker_performance = metrics['profit_by_bookmaker']
    if bookmaker_performance:
        best_bookmaker = max(bookmaker_performance, key=bookmaker_performance.get)
        worst_bookmaker = min(bookmaker_performance, key=bookmaker_performance.get)
        print(f"   Best Bookmaker: {best_bookmaker} (${bookmaker_performance[best_bookmaker]:.2f})")
        print(f"   Worst Bookmaker: {worst_bookmaker} (${bookmaker_performance[worst_bookmaker]:.2f})")
    
    # Execution quality metrics
    print(f"\n⚡ Execution Quality:")
    exec_stats = report.get('execution_stats', {})
    if exec_stats:
        print(f"   Average Slippage: {metrics['average_slippage']:.4f}")
        print(f"   Execution Efficiency: {(1 - min(metrics['average_slippage'], 0.1) / 0.1) * 100:.1f}%")
    
    # Efficiency ratios
    if metrics['total_trades'] > 0:
        profit_per_trade = metrics['net_profit'] / metrics['total_trades']
        cost_per_trade = abs(metrics['total_slippage']) / metrics['total_trades']
        efficiency_ratio = profit_per_trade / max(cost_per_trade, 0.01)
        
        print(f"\n📈 Efficiency Metrics:")
        print(f"   Profit per Trade: ${profit_per_trade:.2f}")
        print(f"   Cost per Trade: ${cost_per_trade:.4f}")
        print(f"   Efficiency Ratio: {efficiency_ratio:.2f}")
        
        if efficiency_ratio > 10:
            print(f"   ✅ Excellent efficiency")
        elif efficiency_ratio > 5:
            print(f"   ✅ Good efficiency")
        else:
            print(f"   ⚠️  Low efficiency - review strategy")
    
    # Account utilization
    print(f"\n💳 Account Utilization:")
    account_summary = system.get_account_summary()
    utilization = (account_summary['total_reserved_balance'] / 
                  max(account_summary['total_balance'], 1)) * 100
    print(f"   Total Utilization: {utilization:.1f}%")
    print(f"   Active Accounts: {len([a for a in system.virtual_accounts.values() if a.status == 'active'])}")
    
    # Export detailed analytics
    export_path = f"/workspace/arbitech/testing/performance_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Add additional analytics to report
    extended_report = report.copy()
    extended_report['analytics'] = {
        'efficiency_ratio': float(efficiency_ratio) if 'efficiency_ratio' in locals() else 0.0,
        'account_utilization': float(utilization),
        'peak_trading_hour': int(peak_hour) if 'peak_hour' in locals() else 0,
        'market_condition_distribution': {
            'stable': 25,  # Simulated distribution
            'volatile': 25,
            'low_liquidity': 25,
            'high_liquidity': 25
        }
    }
    
    with open(export_path, 'w') as f:
        json.dump(extended_report, f, indent=2)
    
    print(f"\n💾 Detailed analytics exported to: {export_path}")
    
    await system.stop_paper_trading()
    
    print(f"\n✅ Performance analytics demonstration completed!")


async def main():
    """Main demonstration runner."""
    import sys
    
    demo_type = sys.argv[1] if len(sys.argv) > 1 else "full"
    
    print(f"🎮 Starting Paper Trading Demo: {demo_type.upper()}")
    
    try:
        if demo_type == "full":
            await full_paper_trading_demo()
        elif demo_type == "backtest":
            await backtest_demo()
        elif demo_type == "hybrid":
            await hybrid_mode_demo()
        elif demo_type == "performance":
            await performance_analytics_demo()
        elif demo_type == "quick":
            # Quick demo with fewer trades
            await full_paper_trading_demo()
        else:
            print(f"❌ Unknown demo type: {demo_type}")
            print(f"Available demos: full, backtest, hybrid, performance, quick")
            return
        
        print(f"\n🎉 Demo '{demo_type}' completed successfully!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logger.exception("Demo execution failed")


if __name__ == "__main__":
    asyncio.run(main())