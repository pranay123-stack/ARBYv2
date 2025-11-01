"""
Example Usage: Advanced Arbitrage Mathematical Calculation Engine

This file demonstrates how to use the sophisticated mathematical calculations
for arbitrage detection, profit analysis, market efficiency assessment, and risk modeling.
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict

# Add the project path for imports
sys.path.append('/workspace/arbitech')

# Import the mathematical calculation engines
from detection import (
    create_complete_arbitrage_engine,
    quick_arbitrage_check,
    calculate_kelly_stakes,
    ArbitrageStrategy,
    MarketType,
    AdvancedArbitrageMath,
    AdvancedProfitCalculator,
    AdvancedMarketAnalysis,
    AdvancedMathematicalModels
)


def example_1_basic_arbitrage_detection():
    """Example 1: Basic arbitrage opportunity detection."""
    print("=" * 60)
    print("Example 1: Basic Arbitrage Detection")
    print("=" * 60)
    
    # Create arbitrage math engine
    arbitrage_engine = AdvancedArbitrageMath(risk_tolerance=Decimal('0.1'))
    
    # Sample betting legs for a tennis match
    from detection.arbitrage_math import MarketLeg
    
    legs = [
        MarketLeg(
            bookmaker="bet365",
            market_type=MarketType.MATCH_WINNER,
            selection="Player A",
            odds=Decimal('2.10'),
            implied_probability=Decimal('1') / Decimal('2.10'),
            commission_rate=Decimal('0.05')
        ),
        MarketLeg(
            bookmaker="pinnacle", 
            market_type=MarketType.MATCH_WINNER,
            selection="Player B",
            odds=Decimal('1.95'),
            implied_probability=Decimal('1') / Decimal('1.95'),
            commission_rate=Decimal('0.02')
        )
    ]
    
    # Detect arbitrage opportunity
    opportunity = arbitrage_engine.detect_arbitrage_opportunity(
        legs=legs,
        strategy=ArbitrageStrategy.TWO_WAY,
        minimum_profit_margin=Decimal('0.5')
    )
    
    if opportunity:
        print(f"✅ Arbitrage opportunity found!")
        print(f"   Opportunity ID: {opportunity.opportunity_id}")
        print(f"   Profit Margin: {opportunity.profit_margin:.2f}%")
        print(f"   ROI: {opportunity.roi_percentage:.2f}%")
        print(f"   Confidence Level: {opportunity.confidence_level:.2f}")
        print(f"   Risk Score: {opportunity.risk_score:.2f}")
        
        # Calculate optimal stake allocation
        stake_allocation = arbitrage_engine.calculate_optimal_stake_allocation(
            opportunity=opportunity,
            total_bankroll=Decimal('1000'),
            allocation_strategy='kelly_conservative'
        )
        
        print(f"\n📊 Optimal Stake Allocation:")
        print(f"   Total Stake: ${stake_allocation.total_stake:.2f}")
        print(f"   Expected Profit: ${stake_allocation.optimal_profit:.2f}")
        print(f"   Kelly Percentage: {stake_allocation.kelly_percentage:.2f}%")
        
        for leg_idx, leg in enumerate(opportunity.legs):
            leg_key = f"leg_{leg_idx}_{leg.bookmaker}"
            if leg_key in stake_allocation.individual_stakes:
                stake = stake_allocation.individual_stakes[leg_key]
                print(f"   {leg.bookmaker} ({leg.selection}): ${stake:.2f}")
    
    else:
        print("❌ No arbitrage opportunity detected")
    
    print()


def example_2_profit_calculations_with_fees():
    """Example 2: Profit calculations with fees and commissions."""
    print("=" * 60)
    print("Example 2: Advanced Profit Calculations")
    print("=" * 60)
    
    # Create profit calculator
    profit_calc = AdvancedProfitCalculator(base_currency='USD')
    
    # Add sample exchange rates
    from detection.profit_calculator import ExchangeRate
    profit_calc.add_exchange_rate(ExchangeRate(
        from_currency='USD',
        to_currency='EUR', 
        rate=Decimal('0.85'),
        timestamp=datetime.now(),
        source='ECB'
    ))
    
    # Calculate profit with various fees
    result = profit_calc.calculate_profit_with_fees(
        stake=Decimal('100'),
        odds=Decimal('2.50'),
        commission_rate=Decimal('0.05'),
        platform_fees={
            'processing_fee': Decimal('0.50'),
            'withdrawal_fee': Decimal('2.00')
        }
    )
    
    print("💰 Profit Calculation Results:")
    print(f"   Stake: ${result['stake']}")
    print(f"   Gross Return: ${result['gross_return']}")
    print(f"   Commission: ${result['commission']}")
    print(f"   Platform Fees: ${result['platform_fees']}")
    print(f"   Net Return: ${result['net_return']}")
    print(f"   Net Profit: ${result['net_profit']}")
    print(f"   ROI: {result['roi_percentage']:.2f}%")
    print(f"   Effective Odds: {result['effective_odds']:.3f}")
    
    # Calculate arbitrage profit with multiple legs
    from detection.profit_calculator import ProfitCalculation
    
    arbitrage_legs = [
        {
            'bookmaker': 'bet365',
            'stake': Decimal('400'),
            'odds': Decimal('2.10'),
            'selection': 'Player A'
        },
        {
            'bookmaker': 'pinnacle',
            'stake': Decimal('545'),
            'odds': Decimal('1.55'),
            'selection': 'Player B'
        }
    ]
    
    commission_rates = {
        'bet365': Decimal('0.05'),
        'pinnacle': Decimal('0.02')
    }
    
    profit_result = profit_calc.calculate_arbitrage_profit_with_fees(
        legs=arbitrage_legs,
        total_stake=Decimal('945'),
        commission_rates=commission_rates
    )
    
    print(f"\n🏆 Arbitrage Profit Analysis:")
    print(f"   Calculation ID: {profit_result.calculation_id}")
    print(f"   Gross Profit: ${profit_result.gross_profit}")
    print(f"   Net Profit: ${profit_result.net_profit}")
    print(f"   Total Fees: ${profit_result.total_fees}")
    print(f"   ROI: {profit_result.roi_percentage:.2f}%")
    
    print()


def example_3_market_analysis():
    """Example 3: Market efficiency and liquidity analysis."""
    print("=" * 60)
    print("Example 3: Market Analysis")
    print("=" * 60)
    
    # Create market analyzer
    market_analyzer = AdvancedMarketAnalysis(analysis_window=timedelta(hours=24))
    
    # Generate sample market data
    from detection.market_analysis import MarketDataPoint
    import numpy as np
    
    # Simulate odds movement over time
    base_odds = Decimal('2.00')
    market_data = []
    
    for i in range(50):  # 50 data points
        # Add some random variation to simulate market movement
        random_factor = np.random.normal(1.0, 0.02)  # 2% volatility
        odds = base_odds * Decimal(str(random_factor))
        implied_prob = Decimal('1') / odds
        
        data_point = MarketDataPoint(
            timestamp=datetime.now() - timedelta(minutes=i*30),
            odds=odds,
            implied_probability=implied_prob,
            liquidity=Decimal(str(np.random.uniform(500, 5000))),
            volume=Decimal(str(np.random.uniform(100, 1000)))
        )
        market_data.append(data_point)
    
    # Analyze market efficiency
    efficiency_analysis = market_analyzer.analyze_market_efficiency(
        market_id="tennis_match_example",
        odds_history=market_data
    )
    
    print("📈 Market Efficiency Analysis:")
    print(f"   Efficiency Level: {efficiency_analysis.efficiency_level.value}")
    print(f"   Efficiency Score: {efficiency_analysis.efficiency_score:.2f}/100")
    print(f"   Arbitrage Frequency: {efficiency_analysis.arbitrage_frequency:.3f}/hour")
    print(f"   Profit Margin Volatility: {efficiency_analysis.profit_margin_volatility:.4f}")
    print(f"   Market Impact Cost: {efficiency_analysis.market_impact_cost:.2f}%")
    print(f"   Information Ratio: {efficiency_analysis.information_ratio:.3f}")
    
    # Analyze liquidity
    liquidity_analysis = market_analyzer.analyze_liquidity(
        market_id="tennis_match_example",
        liquidity_data=market_data
    )
    
    print(f"\n💧 Liquidity Analysis:")
    print(f"   Liquidity Level: {liquidity_analysis.liquidity_level.value}")
    print(f"   Total Liquidity: ${liquidity_analysis.total_liquidity:.0f}")
    print(f"   Average Liquidity: ${liquidity_analysis.average_liquidity:.0f}")
    print(f"   Liquidity Score: {liquidity_analysis.liquidity_score:.1f}/100")
    print(f"   Concentration Ratio: {liquidity_analysis.concentration_ratio:.2f}")
    
    # Predict price movement
    prediction = market_analyzer.predict_price_movement(
        odds_history=market_data,
        prediction_horizon=timedelta(hours=1)
    )
    
    print(f"\n🔮 Price Movement Prediction:")
    print(f"   Movement Type: {prediction.movement_type.value}")
    print(f"   Confidence Level: {prediction.confidence_level:.2f}")
    print(f"   Expected Change: {prediction.expected_change:.4f}")
    print(f"   Volatility Forecast: {prediction.volatility_forecast:.4f}")
    
    print()


def example_4_risk_metrics_and_models():
    """Example 4: Advanced risk metrics and mathematical models."""
    print("=" * 60)
    print("Example 4: Risk Metrics and Mathematical Models")
    print("=" * 60)
    
    # Create mathematical models engine
    models = AdvancedMathematicalModels(risk_free_rate=Decimal('0.02'))
    
    # Simulate return series
    import numpy as np
    np.random.seed(42)  # For reproducible results
    
    # Generate sample returns (daily returns over 1 year)
    daily_returns = []
    for _ in range(252):  # Trading days in a year
        # Simulate betting returns with some volatility
        daily_return = np.random.normal(0.001, 0.02)  # 0.1% mean, 2% daily volatility
        daily_returns.append(Decimal(str(daily_return)))
    
    # Calculate comprehensive risk metrics
    risk_metrics = models.calculate_comprehensive_risk_metrics(daily_returns)
    
    print("⚠️  Risk Metrics:")
    print(f"   Volatility: {risk_metrics.volatility:.4f}")
    print(f"   VaR (95%): {risk_metrics.var_95:.4f}")
    print(f"   VaR (99%): {risk_metrics.var_99:.4f}")
    print(f"   CVaR (95%): {risk_metrics.cvar_95:.4f}")
    print(f"   CVaR (99%): {risk_metrics.cvar_99:.4f}")
    print(f"   Maximum Drawdown: {risk_metrics.maximum_drawdown:.4f}")
    print(f"   Beta Coefficient: {risk_metrics.beta_coefficient:.3f}")
    print(f"   Information Ratio: {risk_metrics.information_ratio:.3f}")
    
    # Calculate performance metrics
    performance_metrics = models.calculate_comprehensive_performance_metrics(daily_returns)
    
    print(f"\n📊 Performance Metrics:")
    print(f"   Sharpe Ratio: {performance_metrics.sharpe_ratio:.2f}")
    print(f"   Sortino Ratio: {performance_metrics.sortino_ratio:.2f}")
    print(f"   Calmar Ratio: {performance_metrics.calmar_ratio:.2f}")
    print(f"   Omega Ratio: {performance_metrics.omega_ratio:.2f}")
    print(f"   Treynor Ratio: {performance_metrics.treynor_ratio:.2f}")
    
    # Calculate Kelly criterion
    kelly_result = models.calculate_kelly_criterion(
        odds=Decimal('2.50'),
        win_probability=Decimal('0.45'),
        bankroll=Decimal('1000')
    )
    
    print(f"\n🎯 Kelly Criterion Analysis:")
    print(f"   Kelly Fraction: {kelly_result['kelly_fraction']:.4f}")
    print(f"   Half Kelly Fraction: {kelly_result['half_kelly_fraction']:.4f}")
    print(f"   Optimal Stake: ${kelly_result['optimal_stake']:.2f}")
    print(f"   Expected Growth Rate: {kelly_result['expected_growth_rate']:.4f}")
    print(f"   Edge: {kelly_result['edge']:.4f}")
    
    # Monte Carlo simulation
    mc_result = models.monte_carlo_simulation(
        returns_distribution={
            'mean': Decimal('0.001'),
            'std': Decimal('0.02'),
            'type': 'normal'
        },
        initial_value=Decimal('1000'),
        time_horizon=timedelta(days=30),
        simulations=1000
    )
    
    print(f"\n🎲 Monte Carlo Simulation (30 days):")
    print(f"   Expected Final Value: ${mc_result['expected_final_value']:.0f}")
    print(f"   Expected Return: {mc_result['expected_return_percentage']:.2f}%")
    print(f"   Probability of Loss: {mc_result['probability_of_loss']:.3f}")
    print(f"   VaR (95%): ${mc_result['var_95']:.0f}")
    print(f"   Best Case: ${mc_result['best_case']:.0f}")
    print(f"   Worst Case: ${mc_result['worst_case']:.0f}")
    
    print()


def example_5_complete_workflow():
    """Example 5: Complete arbitrage analysis workflow."""
    print("=" * 60)
    print("Example 5: Complete Arbitrage Analysis Workflow")
    print("=" * 60)
    
    # Create complete arbitrage engine
    engines = create_complete_arbitrage_engine(
        risk_tolerance=0.1,
        base_currency='USD',
        risk_free_rate=0.02,
        analysis_window_hours=24
    )
    
    arbitrage_engine = engines['arbitrage_math']
    profit_calc = engines['profit_calculator']
    market_analyzer = engines['market_analysis']
    models = engines['mathematical_models']
    
    # Step 1: Create sample arbitrage opportunity
    legs = [
        MarketLeg(
            bookmaker="bet365",
            market_type=MarketType.MATCH_WINNER,
            selection="Team A",
            odds=Decimal('2.20'),
            implied_probability=Decimal('1') / Decimal('2.20'),
            commission_rate=Decimal('0.05')
        ),
        MarketLeg(
            bookmaker="pinnacle",
            market_type=MarketType.MATCH_WINNER,
            selection="Team B", 
            odds=Decimal('1.75'),
            implied_probability=Decimal('1') / Decimal('1.75'),
            commission_rate=Decimal('0.02')
        )
    ]
    
    # Step 2: Detect opportunity
    opportunity = arbitrage_engine.detect_arbitrage_opportunity(
        legs=legs,
        strategy=ArbitrageStrategy.TWO_WAY,
        minimum_profit_margin=Decimal('0.5')
    )
    
    if opportunity:
        print("✅ Workflow: Arbitrage Opportunity Detected")
        
        # Step 3: Calculate optimal stakes
        stake_allocation = arbitrage_engine.calculate_optimal_stake_allocation(
            opportunity=opportunity,
            total_bankroll=Decimal('2000'),
            allocation_strategy='kelly_conservative'
        )
        
        print(f"   💰 Optimal Stakes: ${stake_allocation.total_stake:.2f}")
        print(f"   📈 Expected Profit: ${stake_allocation.optimal_profit:.2f}")
        
        # Step 4: Calculate detailed profit with fees
        profit_result = profit_calc.calculate_arbitrage_profit_with_fees(
            legs=[
                {'bookmaker': 'bet365', 'stake': Decimal('800'), 'odds': Decimal('2.20')},
                {'bookmaker': 'pinnacle', 'stake': Decimal('1000'), 'odds': Decimal('1.75')}
            ],
            total_stake=Decimal('1800'),
            commission_rates={'bet365': Decimal('0.05'), 'pinnacle': Decimal('0.02')}
        )
        
        print(f"   🔍 Net Profit (after fees): ${profit_result.net_profit:.2f}")
        print(f"   📊 ROI: {profit_result.roi_percentage:.2f}%")
        
        # Step 5: Risk assessment
        # Simulate returns for risk calculation
        simulated_returns = [Decimal(str(np.random.normal(0.02, 0.1))) for _ in range(30)]
        risk_metrics = models.calculate_comprehensive_risk_metrics(simulated_returns)
        
        print(f"   ⚠️  Risk Score: {risk_metrics.volatility:.4f}")
        print(f"   📉 Max Drawdown Risk: {risk_metrics.maximum_drawdown:.4f}")
        
        # Step 6: Portfolio optimization
        opportunities = [
            {'odds': Decimal('2.20'), 'win_probability': Decimal('0.45')},
            {'odds': Decimal('1.75'), 'win_probability': Decimal('0.57')}
        ]
        
        portfolio_result = models.optimize_portfolio_kelly(
            opportunities=opportunities,
            bankroll=Decimal('2000')
        )
        
        print(f"   🎯 Portfolio Optimization:")
        print(f"      Expected Return: {portfolio_result.expected_return:.4f}")
        print(f"      Portfolio Sharpe: {portfolio_result.sharpe_ratio:.2f}")
        
        # Step 7: Final recommendation
        print(f"\n🎉 Final Recommendation:")
        if profit_result.net_profit > 0 and risk_metrics.volatility < Decimal('0.5'):
            print("   ✅ RECOMMENDED: High profit, acceptable risk")
        elif profit_result.net_profit > 0:
            print("   ⚠️  CAUTION: Profitable but high risk")
        else:
            print("   ❌ NOT RECOMMENDED: Low profit or high risk")
    
    else:
        print("❌ Workflow: No arbitrage opportunity found")
    
    print()


def example_6_quick_utilities():
    """Example 6: Quick utility functions."""
    print("=" * 60)
    print("Example 6: Quick Utility Functions")
    print("=" * 60)
    
    # Quick arbitrage check
    print("🔍 Quick Arbitrage Check:")
    odds_list = [2.10, 1.95]
    bookmakers = ['bet365', 'pinnacle']
    
    result = quick_arbitrage_check(odds_list, bookmakers, minimum_margin=0.5)
    print(f"   Odds: {odds_list}")
    print(f"   Arbitrage: {result['is_arbitrage']}")
    print(f"   Profit Margin: {result['profit_margin']:.2f}%")
    
    # Quick Kelly calculation
    print(f"\n🎯 Quick Kelly Calculation:")
    kelly_result = calculate_kelly_stakes(
        bankroll=1000,
        odds=2.50,
        win_probability=0.45,
        conservative_factor=0.5
    )
    print(f"   Full Kelly Stake: ${kelly_result['full_kelly_stake']:.2f}")
    print(f"   Conservative Stake: ${kelly_result['conservative_stake']:.2f}")
    print(f"   Expected Growth: {kelly_result['expected_growth_rate']:.4f}")
    
    print()


def main():
    """Run all examples."""
    print("🚀 Advanced Arbitrage Mathematical Calculation Engine")
    print("=" * 60)
    print("Demonstrating sophisticated financial mathematics for arbitrage betting")
    print()
    
    # Run all examples
    example_1_basic_arbitrage_detection()
    example_2_profit_calculations_with_fees()
    example_3_market_analysis()
    example_4_risk_metrics_and_models()
    example_5_complete_workflow()
    example_6_quick_utilities()
    
    print("🎉 All examples completed successfully!")
    print("\n💡 Key Features Demonstrated:")
    print("   ✅ Advanced arbitrage opportunity detection")
    print("   ✅ Sophisticated profit calculations with fees")
    print("   ✅ Market efficiency and liquidity analysis")
    print("   ✅ Comprehensive risk metrics and models")
    print("   ✅ Portfolio optimization using Kelly criterion")
    print("   ✅ Monte Carlo simulations for risk assessment")
    print("   ✅ Quick utility functions for common calculations")


if __name__ == "__main__":
    main()