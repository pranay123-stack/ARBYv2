"""
Standalone Examples: Advanced Arbitrage Mathematical Calculation Engine

This file demonstrates how to use the sophisticated mathematical calculations
for arbitrage detection, profit analysis, market efficiency assessment, and risk modeling.
Direct module imports to avoid dependency issues.
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict
import numpy as np

# Add the project path for imports
sys.path.append('/workspace/arbitech')

# Direct imports from specific modules without going through __init__.py
from arbitrage_math import (
    AdvancedArbitrageMath,
    ArbitrageOpportunity,
    MarketLeg,
    StakeAllocation,
    ArbitrageStrategy,
    MarketType,
    create_arbitrage_math_engine
)

from profit_calculator import (
    AdvancedProfitCalculator,
    ProfitCalculation,
    CommissionStructure,
    FeeStructureConfig,
    ExchangeRate,
    TimeValueParameters,
    create_profit_calculator
)

from market_analysis import (
    AdvancedMarketAnalysis,
    MarketDataPoint,
    LiquidityAnalysis,
    MarketEfficiencyAnalysis,
    PriceMovementPrediction,
    MarketMicrostructure,
    MarketEfficiency,
    LiquidityLevel,
    PriceMovementType,
    create_market_analyzer
)

from mathematical_models import (
    AdvancedMathematicalModels,
    RiskMetrics,
    PerformanceMetrics,
    ExpectedUtilityResult,
    PortfolioOptimizationResult,
    RiskMetric,
    OptimizationObjective,
    create_mathematical_models
)

# Add utils path for basic functions
sys.path.append('/workspace/arbitech/utils')


def example_1_basic_arbitrage_detection():
    """Example 1: Basic arbitrage opportunity detection."""
    print("=" * 60)
    print("Example 1: Basic Arbitrage Detection")
    print("=" * 60)
    
    # Create arbitrage math engine
    arbitrage_engine = create_arbitrage_math_engine(risk_tolerance=Decimal('0.1'))
    
    # Sample betting legs for a tennis match
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


def example_2_profit_calculations():
    """Example 2: Profit calculations with fees."""
    print("=" * 60)
    print("Example 2: Advanced Profit Calculations")
    print("=" * 60)
    
    # Create profit calculator
    profit_calc = create_profit_calculator(base_currency='USD')
    
    # Add sample exchange rates
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
    market_analyzer = create_market_analyzer(analysis_window=timedelta(hours=24))
    
    # Generate sample market data
    np.random.seed(42)  # For reproducible results
    
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


def example_4_risk_metrics():
    """Example 4: Risk metrics and mathematical models."""
    print("=" * 60)
    print("Example 4: Risk Metrics and Mathematical Models")
    print("=" * 60)
    
    # Create mathematical models engine
    models = create_mathematical_models(risk_free_rate=Decimal('0.02'))
    
    # Set seed for reproducible results
    np.random.seed(42)
    
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
    
    print()


def example_5_complete_workflow():
    """Example 5: Complete arbitrage analysis workflow."""
    print("=" * 60)
    print("Example 5: Complete Arbitrage Analysis Workflow")
    print("=" * 60)
    
    # Create all engines
    arbitrage_engine = create_arbitrage_math_engine()
    profit_calc = create_profit_calculator()
    market_analyzer = create_market_analyzer()
    models = create_mathematical_models()
    
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
        np.random.seed(123)
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
    
    # Quick arbitrage check using basic math_helpers
    try:
        from math_helpers import calculate_profit_margin
        print("🔍 Quick Arbitrage Check:")
        odds_list = [2.10, 1.95]
        bookmakers = ['bet365', 'pinnacle']
        
        profit_margin = calculate_profit_margin(odds_list)
        is_arbitrage = profit_margin > 0.5
        
        print(f"   Odds: {odds_list}")
        print(f"   Arbitrage: {is_arbitrage}")
        print(f"   Profit Margin: {profit_margin:.2f}%")
        
    except ImportError:
        print("⚠️  Basic math helpers not available")
    
    # Quick Kelly calculation
    print(f"\n🎯 Quick Kelly Calculation:")
    models = create_mathematical_models()
    kelly_result = models.calculate_kelly_criterion(
        odds=Decimal('2.50'),
        win_probability=Decimal('0.45'),
        bankroll=Decimal('1000')
    )
    
    print(f"   Full Kelly Stake: ${kelly_result['optimal_stake']:.2f}")
    print(f"   Half Kelly Stake: ${kelly_result['optimal_stake'] * Decimal('0.5'):.2f}")
    print(f"   Expected Growth: {kelly_result['expected_growth_rate']:.4f}")
    
    print()


def main():
    """Run all examples."""
    print("🚀 Advanced Arbitrage Mathematical Calculation Engine")
    print("=" * 60)
    print("Demonstrating sophisticated financial mathematics for arbitrage betting")
    print()
    
    try:
        # Run all examples
        example_1_basic_arbitrage_detection()
        example_2_profit_calculations()
        example_3_market_analysis()
        example_4_risk_metrics()
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
        
    except Exception as e:
        print(f"❌ Error running examples: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()