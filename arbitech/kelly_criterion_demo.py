"""
Comprehensive Kelly Criterion and Advanced Risk Management Demo

This script demonstrates the complete sophisticated stake calculation system using Kelly criterion
and advanced optimization algorithms for optimal position sizing in arbitrage betting.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
from datetime import datetime, timedelta
import json

# Import all risk management components
from risk.kelly_calculator import (
    KellyCalculator, KellyConfig, KellyMode, KellyFraction,
    MultiOutcomeKellyResult, DynamicKellyResult, PortfolioKellyResult
)
from risk.stake_optimizer import (
    StakeOptimizer, OptimizationConfig, OptimizationStrategy, 
    OptimizationResult, ConstraintSet, MultiStrategyResult
)
from risk.position_sizer import (
    PositionSizer, PositionConfig, PositionSize, SizingMethod, RiskLevel,
    LiquidityConstraint, DiversificationConstraint
)
from risk.bankroll_manager import (
    BankrollManager, BankrollConfig, BankrollStrategy, CapitalPreservationMode
)

def demo_kelly_calculator():
    """Demonstrate Kelly Criterion Calculator functionality."""
    print("\n" + "="*60)
    print("KELLY CRITERION CALCULATOR DEMO")
    print("="*60)
    
    # Configure Kelly calculator
    config = KellyConfig(
        mode=KellyMode.FRACTIONAL,
        fractional_factor=Decimal('0.25'),
        volatility_adjustment=True,
        drawdown_threshold=Decimal('0.15')
    )
    
    calculator = KellyCalculator(config)
    
    # Test classic Kelly
    print("\n1. Classic Kelly Calculation:")
    win_prob = Decimal('0.55')
    odds = Decimal('2.1')
    bankroll = Decimal('10000')
    
    kelly_result = calculator.calculate_classic_kelly(win_prob, odds, bankroll)
    print(f"   Win Probability: {win_prob:.1%}")
    print(f"   Odds: {odds:.2f}")
    print(f"   Bankroll: ${bankroll:,.2f}")
    print(f"   Optimal Kelly Fraction: {kelly_result.optimal_fraction:.3%}")
    print(f"   Expected Growth Rate: {kelly_result.expected_growth_rate:.4f}")
    print(f"   Utility Score: {kelly_result.utility_score:.4f}")
    
    # Test fractional Kelly
    print("\n2. Fractional Kelly Calculation:")
    fractional_result = calculator.calculate_fractional_kelly(win_prob, odds, bankroll)
    print(f"   Fractional Factor: {config.fractional_factor:.1%}")
    print(f"   Fractional Kelly Fraction: {fractional_result.optimal_fraction:.3%}")
    print(f"   Risk-Adjusted Return: {fractional_result.expected_growth_rate:.4f}")
    
    # Test multi-outcome Kelly
    print("\n3. Multi-Outcome Kelly Calculation:")
    outcomes = {
        'Team A Win': (Decimal('0.45'), Decimal('2.2')),
        'Team B Win': (Decimal('0.35'), Decimal('2.8')),
        'Draw': (Decimal('0.20'), Decimal('3.5'))
    }
    
    multi_outcome_result = calculator.calculate_multi_outcome_kelly(outcomes, bankroll)
    print(f"   Total Fraction: {multi_outcome_result.total_fraction:.3%}")
    print(f"   Expected Return: {multi_outcome_result.expected_return:.4f}")
    print(f"   Portfolio Variance: {multi_outcome_result.portfolio_variance:.4f}")
    print(f"   Diversification Ratio: {multi_outcome_result.diversification_ratio:.3f}")
    
    # Test portfolio Kelly
    print("\n4. Portfolio Kelly Calculation:")
    opportunities = [
        {
            'id': 'match_1_team_a',
            'probability': Decimal('0.55'),
            'odds': Decimal('2.1'),
            'correlation': Decimal('0.2')
        },
        {
            'id': 'match_2_over',
            'probability': Decimal('0.60'),
            'odds': Decimal('1.8'),
            'correlation': Decimal('0.1')
        },
        {
            'id': 'match_3_handicap',
            'probability': Decimal('0.52'),
            'odds': Decimal('1.95'),
            'correlation': Decimal('0.3')
        }
    ]
    
    portfolio_result = calculator.calculate_portfolio_kelly(opportunities, bankroll)
    print(f"   Total Kelly Fraction: {portfolio_result.total_kelly_fraction:.3%}")
    print(f"   Expected Portfolio Return: {portfolio_result.expected_portfolio_return:.4f}")
    print(f"   Portfolio Volatility: {portfolio_result.portfolio_volatility:.4f}")
    print(f"   Sharpe Ratio: {portfolio_result.sharpe_ratio:.3f}")
    
    # Show optimal weights
    print("   Optimal Weights:")
    for opp_id, weight in portfolio_result.portfolio_weights.items():
        print(f"     {opp_id}: {weight:.3%}")
    
    return True

def demo_stake_optimizer():
    """Demonstrate Stake Optimizer functionality."""
    print("\n" + "="*60)
    print("STAKE OPTIMIZER DEMO")
    print("="*60)
    
    # Configure optimizer
    config = OptimizationConfig(
        strategy=OptimizationStrategy.MAXIMUM_SHARPE,
        max_iterations=100,
        transaction_cost_rate=Decimal('0.005')
    )
    
    optimizer = StakeOptimizer(config)
    
    # Test opportunities
    opportunities = [
        {
            'id': 'football_match_1',
            'win_probability': Decimal('0.58'),
            'odds': Decimal('1.9'),
            'confidence': Decimal('0.8')
        },
        {
            'id': 'basketball_over',
            'win_probability': Decimal('0.62'),
            'odds': Decimal('1.75'),
            'confidence': Decimal('0.9')
        },
        {
            'id': 'tennis_handicap',
            'win_probability': Decimal('0.55'),
            'odds': Decimal('2.05'),
            'confidence': Decimal('0.7')
        }
    ]
    
    bankroll = Decimal('10000')
    
    # Test single strategy optimization
    print("\n1. Single Strategy Optimization (Maximum Sharpe):")
    result = optimizer.optimize_stakes(opportunities, bankroll)
    print(f"   Strategy Used: {config.strategy.value}")
    print(f"   Total Stake: ${result.total_stake:,.2f}")
    print(f"   Expected Return: {result.expected_return:.4f}")
    print(f"   Expected Variance: {result.expected_variance:.6f}")
    print(f"   Sharpe Ratio: {result.expected_sharpe_ratio:.3f}")
    print(f"   Optimization Status: {result.optimization_status}")
    
    print("   Optimal Stakes:")
    for opp_id, stake in result.optimal_stakes.items():
        percentage = (stake / bankroll) * 100
        print(f"     {opp_id}: ${stake:,.2f} ({percentage:.1f}%)")
    
    # Test multi-strategy comparison
    print("\n2. Multi-Strategy Comparison:")
    strategies_to_compare = [
        OptimizationStrategy.KELLY_CRITERION,
        OptimizationStrategy.RISK_PARITY,
        OptimizationStrategy.MINIMUM_VAR,
        OptimizationStrategy.FIXED_FRACTIONAL
    ]
    
    comparison_result = optimizer.compare_strategies(
        opportunities, bankroll, strategies_to_compare
    )
    
    print(f"   Best Strategy: {comparison_result.best_strategy.value}")
    print(f"   Best Objective Value: {comparison_result.best_objective_value:.4f}")
    print(f"   Strategies Compared: {len(comparison_result.strategy_results)}")
    
    print("\n   Strategy Rankings:")
    for i, (strategy, score) in enumerate(comparison_result.risk_adjusted_ranking[:3], 1):
        result = comparison_result.strategy_results[strategy]
        print(f"     {i}. {strategy.value}: Score {score:.3f}, "
              f"Sharpe {result.expected_sharpe_ratio:.3f}")
    
    return True

def demo_position_sizer():
    """Demonstrate Position Sizer functionality."""
    print("\n" + "="*60)
    print("POSITION SIZER DEMO")
    print("="*60)
    
    # Configure position sizer
    config = PositionConfig(
        method=SizingMethod.KELLY_OPTIMAL,
        risk_level=RiskLevel.MODERATE,
        max_position_size=Decimal('0.05'),  # 5% max
        max_total_exposure=Decimal('0.8'),  # 80% max
        volatility_adjustment=True,
        correlation_adjustment=True
    )
    
    sizer = PositionSizer(config)
    
    # Test single position sizing
    opportunity = {
        'id': 'premium_match',
        'win_probability': Decimal('0.60'),
        'odds': Decimal('1.85'),
        'confidence': Decimal('0.9'),
        'market': 'football',
        'sport': 'soccer'
    }
    
    bankroll = Decimal('10000')
    existing_positions = {'existing_1': Decimal('200'), 'existing_2': Decimal('300')}
    
    print("\n1. Single Position Sizing:")
    position_size = sizer.calculate_position_size(opportunity, bankroll, existing_positions)
    
    print(f"   Opportunity: {position_size.opportunity_id}")
    print(f"   Recommended Stake: ${position_size.recommended_stake:,.2f}")
    print(f"   Risk Score: {position_size.risk_score:.3f}")
    print(f"   Confidence Score: {position_size.confidence_score:.3f}")
    print(f"   Expected Return: ${position_size.expected_return:,.2f}")
    print(f"   VaR (95%): ${position_size.var_95:,.2f}")
    print(f"   Sizing Method: {position_size.sizing_method.value}")
    print(f"   Reasoning: {position_size.reasoning}")
    
    if position_size.warnings:
        print("   Warnings:")
        for warning in position_size.warnings:
            print(f"     - {warning}")
    
    # Test portfolio sizing
    print("\n2. Portfolio Position Sizing:")
    opportunities = [
        {
            'id': 'match_1',
            'win_probability': Decimal('0.58'),
            'odds': Decimal('1.9'),
            'confidence': Decimal('0.8')
        },
        {
            'id': 'match_2',
            'win_probability': Decimal('0.62'),
            'odds': Decimal('1.75'),
            'confidence': Decimal('0.9')
        },
        {
            'id': 'over_under',
            'win_probability': Decimal('0.55'),
            'odds': Decimal('2.05'),
            'confidence': Decimal('0.7')
        }
    ]
    
    portfolio_sizes = sizer.calculate_portfolio_sizes(opportunities, bankroll)
    
    print(f"   Total Opportunities: {len(portfolio_sizes)}")
    total_allocation = sum(size.recommended_stake for size in portfolio_sizes.values())
    print(f"   Total Allocation: ${total_allocation:,.2f}")
    print(f"   Allocation Percentage: {(total_allocation/bankroll)*100:.1f}%")
    
    print("   Individual Position Sizes:")
    for opp_id, pos_size in portfolio_sizes.items():
        percentage = (pos_size.recommended_stake / bankroll) * 100
        print(f"     {opp_id}: ${pos_size.recommended_stake:,.2f} ({percentage:.1f}%) - "
              f"Risk {pos_size.risk_score:.2f}")
    
    # Test portfolio risk assessment
    print("\n3. Portfolio Risk Assessment:")
    positions = {opp_id: size.recommended_stake for opp_id, size in portfolio_sizes.items()}
    risk_metrics = sizer.assess_portfolio_risk(positions, opportunities)
    
    print(f"   Total Exposure: ${risk_metrics['total_exposure']:,.2f}")
    print(f"   Concentration Risk: {risk_metrics['concentration_risk']:.3f}")
    print(f"   Diversification Ratio: {risk_metrics['diversification_ratio']:.3f}")
    print(f"   Portfolio VaR (95%): ${risk_metrics['portfolio_var_95']:,.2f}")
    print(f"   Correlation Risk: {risk_metrics['correlation_risk']:.3f}")
    print(f"   Number of Positions: {risk_metrics['num_positions']}")
    print(f"   Largest Position: {risk_metrics['largest_position']:.1%}")
    
    return True

def demo_bankroll_manager():
    """Demonstrate Bankroll Manager functionality."""
    print("\n" + "="*60)
    print("BANKROLL MANAGER DEMO")
    print("="*60)
    
    # Configure bankroll manager
    config = BankrollConfig(
        strategy=BankrollStrategy.KELLY_CRITERION,
        initial_bankroll=Decimal('10000'),
        kelly_fraction=Decimal('0.25'),
        drawdown_levels=[Decimal('0.05'), Decimal('0.10'), Decimal('0.15'), Decimal('0.20')],
        preservation_mode=CapitalPreservationMode.MODERATE
    )
    
    manager = BankrollManager(config)
    
    # Simulate some trades
    print("\n1. Simulating Trades:")
    opportunities = [
        {'id': 'trade_1', 'win_probability': Decimal('0.58'), 'odds': Decimal('1.9')},
        {'id': 'trade_2', 'win_probability': Decimal('0.62'), 'odds': Decimal('1.75')},
        {'id': 'trade_3', 'win_probability': Decimal('0.55'), 'odds': Decimal('2.05')},
        {'id': 'trade_4', 'win_probability': Decimal('0.60'), 'odds': Decimal('1.85')},
        {'id': 'trade_5', 'win_probability': Decimal('0.52'), 'odds': Decimal('2.15')}
    ]
    
    # Simulate trade outcomes (random for demo)
    import random
    random.seed(42)  # For reproducible results
    
    for i, opp in enumerate(opportunities):
        # Calculate position size
        position_size = manager.calculate_position_size(opp)
        
        # Simulate outcome (simplified)
        win_prob = float(opp['win_probability'])
        won = random.random() < win_prob
        
        if won:
            profit = position_size * (Decimal(str(opp['odds'])) - Decimal('1'))
        else:
            profit = -position_size
        
        # Update bankroll
        trade_result = {
            'opportunity_id': opp['id'],
            'won': won,
            'profit_loss': profit,
            'timestamp': datetime.now() + timedelta(minutes=i*10)
        }
        
        manager.update_bankroll(trade_result)
        
        print(f"   Trade {i+1}: {opp['id']} - "
              f"Size ${position_size:,.2f} - "
              f"{'WIN' if won else 'LOSS'} ${profit:+,.2f} - "
              f"Bankroll ${manager.current_bankroll:,.2f}")
    
    # Generate performance report
    print("\n2. Performance Report:")
    report = manager.generate_performance_report()
    
    print(f"   Current Bankroll: ${report['summary']['current_bankroll']:,.2f}")
    print(f"   Total Return: {report['summary']['total_return']:+.1%}")
    print(f"   Total Trades: {report['summary']['total_trades']}")
    print(f"   Win Rate: {report['performance_metrics']['win_rate']:.1%}")
    print(f"   Profit Factor: {report['performance_metrics']['profit_factor']:.2f}")
    print(f"   Sharpe Ratio: {report['performance_metrics']['sharpe_ratio']:.3f}")
    print(f"   Current Drawdown: {report['risk_metrics']['current_drawdown']:.1%}")
    print(f"   Maximum Drawdown: {report['risk_metrics']['maximum_drawdown']:.1%}")
    
    # Show growth projections
    print("\n3. Growth Projections:")
    projections = report['growth_projections']
    print(f"   Expected Growth Rate: {projections['expected_growth_rate']:.1%}")
    print(f"   Doubling Time: {projections['doubling_time']:.1f} days")
    print(f"   30-day Projection: ${projections['projected_30_days']:,.2f}")
    print(f"   90-day Projection: ${projections['projected_90_days']:,.2f}")
    print(f"   1-year Projection: ${projections['projected_365_days']:,.2f}")
    
    # Show drawdown protection status
    drawdown = report['drawdown_analysis']
    print("\n4. Drawdown Protection:")
    print(f"   Current Phase: {drawdown['current_phase']}")
    print(f"   Protection Active: {drawdown['protection_active']}")
    print(f"   Days in Drawdown: {drawdown['days_in_drawdown']}")
    print(f"   Recovery Progress: {drawdown['recovery_progress']:.1%}")
    
    # Get rebalancing recommendations
    print("\n5. Rebalancing Recommendations:")
    recommendations = manager.get_rebalancing_recommendations()
    print(f"   Rebalancing Due: {recommendations['rebalancing_due']}")
    print(f"   Performance vs Threshold: {recommendations['current_strategy_performance']}")
    
    if recommendations['recommended_adjustments']:
        print("   Recommended Adjustments:")
        for adj in recommendations['recommended_adjustments']:
            print(f"     - {adj}")
    
    if recommendations['risk_warnings']:
        print("   Risk Warnings:")
        for warning in recommendations['risk_warnings']:
            print(f"     - {warning}")
    
    # Export performance data
    print("\n6. Performance Data Export:")
    json_data = manager.export_performance_data()
    print(f"   Performance data exported ({len(json_data)} characters)")
    
    return True

def demo_integration():
    """Demonstrate full system integration."""
    print("\n" + "="*60)
    print("INTEGRATED SYSTEM DEMO")
    print("="*60)
    
    # Create comprehensive betting scenario
    opportunities = [
        {
            'id': 'premium_football',
            'win_probability': Decimal('0.62'),
            'odds': Decimal('1.8'),
            'confidence': Decimal('0.9'),
            'market': 'football',
            'liquidity': Decimal('50000')
        },
        {
            'id': 'basketball_total',
            'win_probability': Decimal('0.58'),
            'odds': Decimal('1.95'),
            'confidence': Decimal('0.8'),
            'market': 'basketball',
            'liquidity': Decimal('30000')
        },
        {
            'id': 'tennis_match',
            'win_probability': Decimal('0.55'),
            'odds': Decimal('2.1'),
            'confidence': Decimal('0.7'),
            'market': 'tennis',
            'liquidity': Decimal('20000')
        },
        {
            'id': 'hockey_handicap',
            'win_probability': Decimal('0.60'),
            'odds': Decimal('1.85'),
            'confidence': Decimal('0.85'),
            'market': 'hockey',
            'liquidity': Decimal('25000')
        }
    ]
    
    bankroll = Decimal('25000')
    
    print(f"\n1. System Setup:")
    print(f"   Bankroll: ${bankroll:,.2f}")
    print(f"   Opportunities: {len(opportunities)}")
    
    # Initialize all components
    kelly_config = KellyConfig(mode=KellyMode.DYNAMIC)
    kelly_calc = KellyCalculator(kelly_config)
    
    optimizer_config = OptimizationConfig(strategy=OptimizationStrategy.MAXIMUM_UTILITY)
    optimizer = StakeOptimizer(optimizer_config)
    
    position_config = PositionConfig(method=SizingMethod.CORRELATION_ADJUSTED)
    position_sizer = PositionSizer(position_config)
    
    bankroll_config = BankrollConfig(strategy=BankrollStrategy.FRACTIONAL_KELLY)
    bankroll_mgr = BankrollManager(bankroll_config)
    
    print("\n2. Comprehensive Analysis:")
    
    # Kelly analysis
    portfolio_kelly = kelly_calc.calculate_portfolio_kelly(opportunities, bankroll)
    print(f"   Kelly Portfolio Analysis:")
    print(f"     Total Kelly Fraction: {portfolio_kelly.total_kelly_fraction:.2%}")
    print(f"     Expected Return: {portfolio_kelly.expected_portfolio_return:.3f}")
    print(f"     Sharpe Ratio: {portfolio_kelly.sharpe_ratio:.3f}")
    
    # Stake optimization
    optimization_result = optimizer.optimize_stakes(opportunities, bankroll)
    print(f"   Stake Optimization:")
    print(f"     Strategy: {optimization_result.optimization_status}")
    print(f"     Total Allocation: ${optimization_result.total_stake:,.2f}")
    print(f"     Expected Sharpe: {optimization_result.expected_sharpe_ratio:.3f}")
    
    # Position sizing
    portfolio_sizes = position_sizer.calculate_portfolio_sizes(opportunities, bankroll)
    total_position_size = sum(size.recommended_stake for size in portfolio_sizes.values())
    print(f"   Position Sizing:")
    print(f"     Total Recommended: ${total_position_size:,.2f}")
    print(f"     Average Risk Score: {sum(size.risk_score for size in portfolio_sizes.values()) / len(portfolio_sizes):.2f}")
    
    # Bankroll management
    bankroll_recommendations = bankroll_mgr.get_rebalancing_recommendations()
    print(f"   Bankroll Management:")
    print(f"     Strategy Performance: {bankroll_recommendations['current_strategy_performance']}")
    print(f"     Risk Warnings: {len(bankroll_recommendations['risk_warnings'])}")
    
    print("\n3. Final Recommendations:")
    
    # Find consensus recommendations
    high_confidence_opps = [opp for opp in opportunities if Decimal(str(opp['confidence'])) >= Decimal('0.8')]
    medium_confidence_opps = [opp for opp in opportunities if Decimal(str(opp['confidence'])) >= Decimal('0.6')]
    
    print(f"   High Confidence Opportunities: {len(high_confidence_opps)}")
    print(f"   Medium+ Confidence Opportunities: {len(medium_confidence_opps)}")
    
    # Calculate recommended allocation
    total_bankroll_utilization = min(
        float(portfolio_kelly.total_kelly_fraction),
        float(optimization_result.total_stake / bankroll),
        float(total_position_size / bankroll)
    )
    
    print(f"   Recommended Bankroll Utilization: {total_bankroll_utilization:.1%}")
    
    if total_bankroll_utilization > 0.5:
        print("   ⚠️  High utilization - consider diversifying risk")
    elif total_bankroll_utilization < 0.2:
        print("   📈 Conservative allocation - may be underutilizing opportunities")
    else:
        print("   ✅ Balanced allocation strategy")
    
    # Risk assessment
    portfolio_risk = position_sizer.assess_portfolio_risk(
        {opp_id: size.recommended_stake for opp_id, size in portfolio_sizes.items()},
        opportunities
    )
    
    print(f"   Portfolio Risk Metrics:")
    print(f"     Diversification Ratio: {portfolio_risk['diversification_ratio']:.3f}")
    print(f"     Concentration Risk: {portfolio_risk['concentration_risk']:.3f}")
    print(f"     Portfolio VaR (95%): ${portfolio_risk['portfolio_var_95']:,.2f}")
    
    if portfolio_risk['diversification_ratio'] < 0.3:
        print("   ⚠️  Low diversification - consider more opportunities")
    if portfolio_risk['concentration_risk'] > 0.5:
        print("   ⚠️  High concentration risk - reduce position sizes")
    
    return True

def main():
    """Run all demonstrations."""
    print("ADVANCED KELLY CRITERION & RISK MANAGEMENT SYSTEM")
    print("=" * 80)
    print("Comprehensive demonstration of sophisticated stake calculation system")
    print("using Kelly criterion and advanced optimization algorithms")
    print("=" * 80)
    
    success_count = 0
    total_demos = 5
    
    # Run individual component demos
    try:
        if demo_kelly_calculator():
            success_count += 1
            print("\n✅ Kelly Calculator Demo: SUCCESS")
        else:
            print("\n❌ Kelly Calculator Demo: FAILED")
    except Exception as e:
        print(f"\n❌ Kelly Calculator Demo: ERROR - {str(e)}")
    
    try:
        if demo_stake_optimizer():
            success_count += 1
            print("\n✅ Stake Optimizer Demo: SUCCESS")
        else:
            print("\n❌ Stake Optimizer Demo: FAILED")
    except Exception as e:
        print(f"\n❌ Stake Optimizer Demo: ERROR - {str(e)}")
    
    try:
        if demo_position_sizer():
            success_count += 1
            print("\n✅ Position Sizer Demo: SUCCESS")
        else:
            print("\n❌ Position Sizer Demo: FAILED")
    except Exception as e:
        print(f"\n❌ Position Sizer Demo: ERROR - {str(e)}")
    
    try:
        if demo_bankroll_manager():
            success_count += 1
            print("\n✅ Bankroll Manager Demo: SUCCESS")
        else:
            print("\n❌ Bankroll Manager Demo: FAILED")
    except Exception as e:
        print(f"\n❌ Bankroll Manager Demo: ERROR - {str(e)}")
    
    try:
        if demo_integration():
            success_count += 1
            print("\n✅ Integration Demo: SUCCESS")
        else:
            print("\n❌ Integration Demo: FAILED")
    except Exception as e:
        print(f"\n❌ Integration Demo: ERROR - {str(e)}")
    
    # Final summary
    print("\n" + "="*80)
    print("DEMO SUMMARY")
    print("="*80)
    print(f"Successful Demos: {success_count}/{total_demos}")
    print(f"Success Rate: {(success_count/total_demos)*100:.1f}%")
    
    if success_count == total_demos:
        print("\n🎉 ALL DEMOS PASSED - System is fully functional!")
        print("\nThe sophisticated stake calculation system is ready for use with:")
        print("• Advanced Kelly criterion implementation")
        print("• Multi-strategy stake optimization")
        print("• Professional position sizing")
        print("• Comprehensive bankroll management")
        print("• Real-time risk monitoring")
        print("• Portfolio-based optimization")
    else:
        print(f"\n⚠️  {total_demos - success_count} demo(s) failed - please check error messages")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()