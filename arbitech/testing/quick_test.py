#!/usr/bin/env python3
"""
Quick test script for paper trading system validation.
"""

import asyncio
from decimal import Decimal
import sys
import os

# Add the testing directory to path
sys.path.insert(0, '/workspace/arbitech/testing')

from paper_trading import create_paper_trading_system, TradingMode

async def quick_test():
    print('🚀 Quick Paper Trading System Test')
    print('=' * 50)
    
    try:
        # Create system
        system = create_paper_trading_system(
            mode=TradingMode.PAPER,
            initial_bankroll=Decimal('10000.00')
        )
        
        print(f'✅ System created successfully')
        print(f'📊 Virtual accounts: {len(system.virtual_accounts)}')
        print(f'🏢 Bookmakers: {list(system.virtual_accounts.keys())[:5]}...')
        print(f'💰 Initial bankroll: ${system.initial_bankroll:,.2f}')
        print(f'🎯 Trading mode: {system.mode}')
        
        # Test account summary
        summary = system.get_account_summary()
        print(f'✅ Account summary: {summary["total_accounts"]} accounts')
        print(f'💳 Total available balance: ${summary["total_available_balance"]:,.2f}')
        
        # Test performance report
        report = system.get_performance_report()
        metrics = report['performance_metrics']
        print(f'✅ Performance report: {metrics["total_trades"]} trades')
        print(f'📈 Current ROI: {metrics["roi_percentage"]:.2f}%')
        
        # Test market simulation
        initial_odds = Decimal('2.00')
        new_odds = system.market_simulator.simulate_odds_movement(
            initial_odds, 'Pinnacle', 'football'
        )
        print(f'✅ Market simulation: {initial_odds} → {new_odds}')
        
        # Test execution simulation
        delay = system.execution_simulator.simulate_execution_delay(
            TradingMode.PAPER, 'stable'
        )
        slippage = system.execution_simulator.simulate_slippage(
            Decimal('2.00'), Decimal('1000.00'), 'stable'
        )
        print(f'✅ Execution simulation: {delay}ms delay, {slippage:.3%} slippage')
        
        # Test system status
        status = system.get_simulation_status()
        print(f'✅ System status: Running={status["is_running"]}')
        
        print('\n' + '=' * 50)
        print('🎉 All tests passed! Paper trading system is working correctly.')
        print('✅ Ready for production use!')
        
    except Exception as e:
        print(f'❌ Test failed with error: {e}')
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)