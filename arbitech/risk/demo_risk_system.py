"""
Comprehensive example demonstrating the Bankroll and Limit Validation System
for safe trading operations with real-time monitoring and enforcement.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any
from uuid import uuid4, UUID

# Import the risk management components
from arbitech.risk import BankrollValidator, LimitManager, ExposureTracker, ValidationEngine
from arbitech.storage.models import (
    ArbitrageOpportunity, Trade, Sport, RiskTier, TradeStatus, ExecutionMode,
    RiskConfig, TierASettings, TierBSettings, GlobalLimits, Failsafes,
    StakeData, ArbitrageLeg, AccountBalance, BookmakerAccount, AccountStatus
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_sample_risk_config() -> RiskConfig:
    """Create a sample risk configuration for demonstration."""
    return RiskConfig(
        user_id=uuid4(),
        name="Conservative Trading Strategy",
        description="Low-risk arbitrage trading with strict limits",
        
        tier_a_settings=TierASettings(
            max_stake_per_trade='100',
            max_daily_trades=25,
            max_daily_exposure='500',
            min_profit_margin='0.02',
            max_execution_time_ms=30000,
            allow_stealth_mode=True,
            max_concurrent_opportunities=3
        ),
        
        tier_b_settings=TierBSettings(
            max_stake_per_trade='250',
            max_daily_trades=50,
            max_daily_exposure='1000',
            min_profit_margin='0.015',
            max_execution_time_ms=45000,
            allow_stealth_mode=True,
            max_concurrent_opportunities=5
        ),
        
        global_limits=GlobalLimits(
            max_total_exposure='2000',
            max_concurrent_users=50,
            system_min_profit_margin='0.01',
            max_slippage_tolerance='0.05',
            max_odds_age_minutes=30
        ),
        
        failsafes=Failsafes(
            emergency_stop_loss='200',
            max_loss_per_hour='100',
            max_consecutive_losses=3,
            automatic_pause_threshold='0.1',
            cool_down_minutes=15,
            notification_on_trigger=True
        )
    )


async def create_sample_opportunities() -> List[ArbitrageOpportunity]:
    """Create sample arbitrage opportunities for testing."""
    opportunities = []
    
    # Tier A opportunity - Football match
    football_legs = [
        ArbitrageLeg(
            bookmaker="bet365",
            event_outcome="Manchester United wins",
            odds='2.10',
            implied_probability='0.4762',
            stake_percentage='0.5',
            actual_stake='50.00',
            potential_payout='105.00'
        ),
        ArbitrageLeg(
            bookmaker="william_hill",
            event_outcome="Draw or Liverpool wins",
            odds='1.85',
            implied_probability='0.5405',
            stake_percentage='0.5',
            actual_stake='50.00',
            potential_payout='92.50'
        )
    ]
    
    football_opportunity = ArbitrageOpportunity(
        sport=Sport.FOOTBALL,
        event_name="Manchester United vs Liverpool",
        event_date=datetime.utcnow() + timedelta(hours=3),
        market_type="match_winner",
        legs=football_legs,
        total_stake='100.00',
        profit_margin='0.025',
        profit_amount='2.50',
        guaranteed_profit=True,
        risk_tier=RiskTier.TIER_A,
        liquidity_checked=True,
        source_scanner="football_scanner_v2",
        discovered_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    opportunities.append(football_opportunity)
    
    # Tier B opportunity - Tennis match
    tennis_legs = [
        ArbitrageLeg(
            bookmaker="ladbrokes",
            event_outcome="Novak Djokovic wins",
            odds='1.75',
            implied_probability='0.5714',
            stake_percentage='0.6',
            actual_stake='120.00',
            potential_payout='210.00'
        ),
        ArbitrageLeg(
            bookmaker="pinnacle",
            event_outcome="Rafael Nadal wins",
            odds='2.50',
            implied_probability='0.4',
            stake_percentage='0.4',
            actual_stake='80.00',
            potential_payout='200.00'
        )
    ]
    
    tennis_opportunity = ArbitrageOpportunity(
        sport=Sport.TENNIS,
        event_name="Djokovic vs Nadal - Finals",
        event_date=datetime.utcnow() + timedelta(hours=6),
        market_type="match_winner",
        legs=tennis_legs,
        total_stake='200.00',
        profit_margin='0.048',
        profit_amount='10.00',
        guaranteed_profit=True,
        risk_tier=RiskTier.TIER_B,
        liquidity_checked=True,
        source_scanner="tennis_scanner_v1",
        discovered_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    opportunities.append(tennis_opportunity)
    
    # Tier C opportunity - Basketball game
    basketball_legs = [
        ArbitrageLeg(
            bookmaker="draftkings",
            event_outcome="Lakers win by 5+ points",
            odds='1.90',
            implied_probability='0.5263',
            stake_percentage='0.7',
            actual_stake='175.00',
            potential_payout='332.50'
        ),
        ArbitrageLeg(
            bookmaker="betfair",
            event_outcome="Warriors win or lose by 4 or less",
            odds='2.20',
            implied_probability='0.4545',
            stake_percentage='0.3',
            actual_stake='75.00',
            potential_payout='165.00'
        )
    ]
    
    basketball_opportunity = ArbitrageOpportunity(
        sport=Sport.BASKETBALL,
        event_name="Lakers vs Warriors",
        event_date=datetime.utcnow() + timedelta(hours=8),
        market_type="handicap",
        legs=basketball_legs,
        total_stake='250.00',
        profit_margin='0.0375',
        profit_amount='9.38',
        guaranteed_profit=True,
        risk_tier=RiskTier.TIER_C,
        liquidity_checked=False,  # Mark as not checked for testing
        source_scanner="basketball_scanner_v3",
        discovered_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=20),
        validation_errors=["Liquidity not verified"]  # Add validation error
    )
    opportunities.append(basketball_opportunity)
    
    return opportunities


async def create_sample_trade(opportunity: ArbitrageOpportunity, user_id: UUID) -> Trade:
    """Create a sample trade from an opportunity."""
    return Trade(
        user_id=user_id,
        opportunity=opportunity,
        status=TradeStatus.PENDING,
        execution_mode=ExecutionMode.AUTO_FULL,
        stake_data=StakeData(
            total_stake=opportunity.total_stake,
            currency="USD",
            leg_allocations={
                leg.bookmaker: leg.actual_stake for leg in opportunity.legs
            },
            fees_included='0',
            net_stake=opportunity.total_stake
        ),
        expected_profit=opportunity.profit_amount,
        timestamps={
            "created_at": datetime.utcnow()
        },
        placed_bets=[],
        failed_bets=[],
        hedge_trades=[],
        error_messages=[],
        retry_count=0
    )


async def create_sample_bookmaker_accounts(user_id: UUID) -> List[BookmakerAccount]:
    """Create sample bookmaker accounts with balances."""
    accounts = []
    
    # Bet365 account
    bet365_account = BookmakerAccount(
        user_id=user_id,
        bookmaker_name="bet365",
        credentials={
            "username_encrypted": "encrypted_username_123",
            "password_encrypted": "encrypted_password_456"
        },
        status=AccountStatus.ACTIVE,
        balance=AccountBalance(
            available_balance='1000.00',
            total_balance='1000.00',
            currency="USD",
            last_updated=datetime.utcnow()
        ),
        daily_bet_limit='500',
        single_bet_limit='200',
        success_rate='0.95',
        total_bets_placed=150,
        risk_score='0.2'
    )
    accounts.append(bet365_account)
    
    # William Hill account
    william_hill_account = BookmakerAccount(
        user_id=user_id,
        bookmaker_name="william_hill",
        credentials={
            "username_encrypted": "encrypted_username_789",
            "password_encrypted": "encrypted_password_012"
        },
        status=AccountStatus.ACTIVE,
        balance=AccountBalance(
            available_balance='750.00',
            total_balance='750.00',
            currency="USD",
            last_updated=datetime.utcnow()
        ),
        daily_bet_limit='300',
        single_bet_limit='150',
        success_rate='0.92',
        total_bets_placed=89,
        risk_score='0.3'
    )
    accounts.append(william_hill_account)
    
    # Ladbrokes account
    ladbrokes_account = BookmakerAccount(
        user_id=user_id,
        bookmaker_name="ladbrokes",
        credentials={
            "username_encrypted": "encrypted_username_345",
            "password_encrypted": "encrypted_password_678"
        },
        status=AccountStatus.ACTIVE,
        balance=AccountBalance(
            available_balance='600.00',
            total_balance='600.00',
            currency="USD",
            last_updated=datetime.utcnow()
        ),
        daily_bet_limit='400',
        single_bet_limit='180',
        success_rate='0.88',
        total_bets_placed=67,
        risk_score='0.25'
    )
    accounts.append(ladbrokes_account)
    
    return accounts


async def demo_bankroll_validation():
    """Demonstrate bankroll validation functionality."""
    print("\\n" + "="*80)
    print("DEMO: Bankroll Validation System")
    print("="*80)
    
    # Create risk configuration
    risk_config = await create_sample_risk_config()
    user_id = uuid4()
    
    # Initialize bankroll validator
    bankroll_validator = BankrollValidator(risk_config)
    
    # Create sample bookmaker accounts
    accounts = await create_sample_bookmaker_accounts(user_id)
    
    # Start monitoring
    await bankroll_validator.start_monitoring()
    
    print("✓ Bankroll validator initialized and monitoring started")
    
    # Update account balances
    for account in accounts:
        await bankroll_validator.update_balance(
            account.bookmaker_name,
            account.id,
            account.balance.available_balance
        )
    
    print(f"✓ Updated balances for {len(accounts)} bookmaker accounts")
    
    # Validate current bankroll state
    validation_result = await bankroll_validator.validate_bankroll()
    print(f"\\nBankroll Validation Results:")
    print(f"  Valid: {validation_result.is_valid}")
    print(f"  Current Exposure: ${validation_result.current_exposure}")
    print(f"  Remaining Capacity: ${validation_result.remaining_capacity}")
    print(f"  Violations: {validation_result.violations}")
    print(f"  Warnings: {validation_result.warnings}")
    
    # Get bankroll metrics
    metrics = await bankroll_validator.get_bankroll_metrics()
    print(f"\\nBankroll Metrics:")
    print(f"  Total Balance: ${metrics['total_balance']}")
    print(f"  Available Balance: ${metrics['available_balance']}")
    print(f"  Active Positions: {metrics['active_positions']}")
    print(f"  Limit Utilization: {metrics['limit_utilization']:.1%}")
    
    # Stop monitoring
    await bankroll_validator.stop_monitoring()
    print("\\n✓ Bankroll validation demo completed")


async def demo_limit_management():
    """Demonstrate limit management functionality."""
    print("\\n" + "="*80)
    print("DEMO: Limit Management System")
    print("="*80)
    
    # Create risk configuration
    risk_config = await create_sample_risk_config()
    user_id = uuid4()
    
    # Initialize limit manager
    limit_manager = LimitManager(risk_config)
    
    # Create sample opportunities
    opportunities = await create_sample_opportunities()
    
    print(f"✓ Limit manager initialized with {len(limit_manager.rules)} rules")
    
    # Test trade validation with different opportunities
    for i, opportunity in enumerate(opportunities, 1):
        print(f"\\n--- Testing Opportunity {i}: {opportunity.sport.value} ({opportunity.risk_tier.value}) ---")
        
        # Validate trade limits
        validation_result = await limit_manager.check_trade_limits(
            opportunity,
            opportunity.total_stake,
            user_id
        )
        
        print(f"  Valid: {validation_result['is_valid']}")
        print(f"  Violations: {len(validation_result['violations'])}")
        print(f"  Warnings: {len(validation_result['warnings'])}")
        print(f"  Applicable Rules: {validation_result['applicable_rules']}")
        print(f"  Check Time: {validation_result['check_time_ms']:.1f}ms")
        
        if validation_result['violations']:
            for violation in validation_result['violations']:
                print(f"    ⚠️  {violation['rule_name']}: {violation['message']}")
        
        if validation_result['warnings']:
            for warning in validation_result['warnings']:
                print(f"    ⚡ {warning['rule_name']}: {warning['message']}")
        
        # Record trade execution if valid
        if validation_result['is_valid']:
            trade = await create_sample_trade(opportunity, user_id)
            await limit_manager.record_trade_execution(trade)
            print(f"  ✓ Trade recorded for execution tracking")
    
    # Get limit summary
    summary = await limit_manager.get_limit_summary()
    print(f"\\nLimit Management Summary:")
    print(f"  Total Rules: {summary['total_rules']}")
    print(f"  Active Rules: {summary['active_rules']}")
    print(f"  Breached Limits: {summary['breached_limits']}")
    print(f"  Alerts Sent: {summary['alerts_sent']}")
    print(f"  Rule Evaluations: {summary['rule_evaluations']}")
    
    # Get detailed usage report
    usage_report = await limit_manager.get_detailed_usage_report()
    print(f"\\nUsage Report Details:")
    print(f"  Tracked Rules: {len(usage_report['usage_by_rule'])}")
    print(f"  Scope Categories: {len(usage_report['usage_by_scope'])}")
    
    print("\\n✓ Limit management demo completed")


async def demo_exposure_tracking():
    """Demonstrate exposure tracking functionality."""
    print("\\n" + "="*80)
    print("DEMO: Exposure Tracking System")
    print("="*80)
    
    # Initialize exposure tracker
    exposure_tracker = ExposureTracker()
    
    # Start monitoring
    await exposure_tracker.start_monitoring()
    
    print("✓ Exposure tracker initialized and monitoring started")
    
    # Create sample opportunities and trades
    user_id = uuid4()
    opportunities = await create_sample_opportunities()
    
    # Simulate active trades
    active_trades = []
    for i, opportunity in enumerate(opportunities[:2]):  # Use first 2 opportunities
        trade = await create_sample_trade(opportunity, user_id)
        active_trades.append(trade)
        
        # Add positions to tracking
        positions = await exposure_tracker.add_position(trade)
        print(f"✓ Added {len(positions)} positions for {opportunity.sport.value} trade")
    
    # Wait for monitoring to process
    await asyncio.sleep(2)
    
    # Get exposure summary
    summary = await exposure_tracker.get_exposure_summary()
    print(f"\\nExposure Summary:")
    print(f"  Total Exposure: ${summary['total_exposure']}")
    print(f"  Active Positions: {summary['active_positions']}")
    print(f"  Concentration Alerts: {summary['concentration_alerts']}")
    
    print(f"\\nExposure by Type:")
    for exp_type, amount in summary['exposure_by_type'].items():
        print(f"  {exp_type}: ${amount}")
    
    print(f"\\nTop Concentrations:")
    for conc in summary['top_concentrations'][:3]:
        print(f"  {conc['source']}: ${conc['exposure']:.2f} ({conc['concentration']:.1%})")
    
    # Get correlation analysis
    correlation_matrix = await exposure_tracker.get_correlation_matrix()
    print(f"\\nCorrelation Analysis:")
    print(f"  Sources tracked: {len(correlation_matrix['sources'])}")
    print(f"  Significant correlations: {len(correlation_matrix['significant_correlations'])}")
    
    # Get concentration analysis
    concentration_analysis = await exposure_tracker.get_concentration_analysis()
    print(f"\\nConcentration Analysis:")
    print(f"  Total exposure tracked: ${concentration_analysis['total_exposure']}")
    print(f"  Recommendations: {len(concentration_analysis['recommendations'])}")
    
    for rec in concentration_analysis['recommendations']:
        print(f"    • {rec}")
    
    # Calculate position sizing
    if opportunities:
        opportunity = opportunities[0]
        leg = opportunity.legs[0]
        
        sizing_result = await exposure_tracker.calculate_position_sizing(
            '50.00',
            "bookmaker",
            leg.bookmaker
        )
        
        print(f"\\nPosition Sizing Recommendation:")
        print(f"  Original exposure: ${sizing_result['original_exposure']}")
        print(f"  Recommended exposure: ${sizing_result['recommended_exposure']}")
        print(f"  Sizing efficiency: {sizing_result['sizing_efficiency']:.1%}")
        
        for reason in sizing_result['adjustment_reason']:
            print(f"    • {reason}")
    
    # Stop monitoring
    await exposure_tracker.stop_monitoring()
    print("\\n✓ Exposure tracking demo completed")


async def demo_validation_engine():
    """Demonstrate the comprehensive validation engine."""
    print("\\n" + "="*80)
    print("DEMO: Comprehensive Validation Engine")
    print("="*80)
    
    # Create risk configuration
    risk_config = await create_sample_risk_config()
    user_id = uuid4()
    
    # Initialize validation engine
    validation_engine = ValidationEngine(risk_config)
    
    # Start monitoring
    await validation_engine.start_monitoring()
    
    print("✓ Validation engine initialized and monitoring started")
    
    # Create sample opportunities
    opportunities = await create_sample_opportunities()
    
    # Test validation at different levels
    validation_levels = ["basic", "standard", "strict"]
    
    for level in validation_levels:
        print(f"\\n--- Validation Level: {level.upper()} ---")
        
        for i, opportunity in enumerate(opportunities, 1):
            print(f"\\nValidating Opportunity {i}: {opportunity.sport.value}")
            
            # Run comprehensive validation
            from arbitech.risk.validation_engine import ValidationLevel
            validation_level = ValidationLevel(level)
            
            validation_report = await validation_engine.validate_trade(
                opportunity,
                opportunity.total_stake,
                user_id,
                validation_level
            )
            
            print(f"  Overall Score: {validation_report.overall_score:.3f}")
            print(f"  Risk Assessment: {validation_report.risk_assessment.value.upper()}")
            print(f"  Rules Checked: {validation_report.passed_rules}/{validation_report.total_rules}")
            print(f"  Execution Time: {validation_report.total_execution_time_ms:.1f}ms")
            
            if validation_report.critical_issues:
                print(f"  Critical Issues:")
                for issue in validation_report.critical_issues:
                    print(f"    ❌ {issue}")
            
            if validation_report.warnings:
                print(f"  Warnings:")
                for warning in validation_report.warnings:
                    print(f"    ⚠️  {warning}")
            
            if validation_report.recommendations:
                print(f"  Recommendations:")
                for rec in validation_report.recommendations:
                    print(f"    💡 {rec}")
            
            # Show slowest/fastest rules
            if validation_report.slowest_rule:
                print(f"  Slowest Rule: {validation_report.slowest_rule}")
            if validation_report.fastest_rule:
                print(f"  Fastest Rule: {validation_report.fastest_rule}")
            
            # Break early for strict level to save time
            if level == "strict" and i >= 1:
                break
    
    # Get validation summary
    summary = await validation_engine.get_validation_summary()
    print(f"\\nValidation Engine Summary:")
    print(f"  Total Validations: {summary['performance_metrics']['total_validations']}")
    print(f"  Success Rate: {summary['performance_metrics']['success_rate']:.1%}")
    print(f"  Average Time: {summary['performance_metrics']['average_validation_time_ms']:.1f}ms")
    print(f"  Peak Concurrent: {summary['performance_metrics']['peak_concurrent_validations']}")
    
    print(f"\\nRule Statistics:")
    print(f"  Total Rules: {summary['rule_statistics']['total_rules']}")
    print(f"  Active Rules: {summary['rule_statistics']['active_rules']}")
    
    print(f"\\nRules by Stage:")
    for stage, count in summary['rule_statistics']['rules_by_stage'].items():
        print(f"  {stage}: {count}")
    
    print(f"\\nCircuit Breaker Status:")
    cb_status = summary['circuit_breaker']
    print(f"  Active: {cb_status['is_active']}")
    print(f"  Activations: {cb_status['activations_count']}")
    print(f"  Emergency Stop: {cb_status['emergency_stop_active']}")
    
    # Stop monitoring
    await validation_engine.stop_monitoring()
    print("\\n✓ Validation engine demo completed")


async def demo_integration_workflow():
    """Demonstrate full integration workflow."""
    print("\\n" + "="*80)
    print("DEMO: Full Integration Workflow")
    print("="*80)
    
    # Create risk configuration
    risk_config = await create_sample_risk_config()
    user_id = uuid4()
    
    # Initialize all components
    bankroll_validator = BankrollValidator(risk_config)
    limit_manager = LimitManager(risk_config)
    exposure_tracker = ExposureTracker()
    validation_engine = ValidationEngine(risk_config)
    
    # Start all monitoring
    await asyncio.gather(
        bankroll_validator.start_monitoring(),
        exposure_tracker.start_monitoring(),
        validation_engine.start_monitoring()
    )
    
    print("✓ All risk management components initialized and monitoring started")
    
    # Create bookmaker accounts and update balances
    accounts = await create_sample_bookmaker_accounts(user_id)
    for account in accounts:
        await bankroll_validator.update_balance(
            account.bookmaker_name,
            account.id,
            account.balance.available_balance
        )
    
    print(f"✓ Updated {len(accounts)} bookmaker account balances")
    
    # Create opportunities
    opportunities = await create_sample_opportunities()
    
    # Process each opportunity through the full pipeline
    processed_trades = []
    for i, opportunity in enumerate(opportunities, 1):
        print(f"\\n--- Processing Opportunity {i}: {opportunity.sport.value} ---")
        
        # Step 1: Run comprehensive validation
        validation_report = await validation_engine.validate_trade(
            opportunity,
            opportunity.total_stake,
            user_id
        )
        
        print(f"  Validation Score: {validation_report.overall_score:.3f}")
        print(f"  Risk Level: {validation_report.risk_assessment.value}")
        
        # Step 2: Check if validation passed
        if validation_report.overall_score >= '0.5':
            print(f"  ✓ Validation passed - proceeding with trade")
            
            # Step 3: Create and add trade
            trade = await create_sample_trade(opportunity, user_id)
            
            # Add to bankroll validator
            bankroll_success = await bankroll_validator.add_trade(trade)
            if bankroll_success:
                print(f"  ✓ Trade added to bankroll tracking")
                
                # Record in limit manager
                await limit_manager.record_trade_execution(trade)
                print(f"  ✓ Trade recorded in limit manager")
                
                # Add positions to exposure tracker
                positions = await exposure_tracker.add_position(trade)
                print(f"  ✓ {len(positions)} positions added to exposure tracking")
                
                processed_trades.append(trade)
            else:
                print(f"  ❌ Trade rejected by bankroll validator")
        else:
            print(f"  ❌ Validation failed - trade rejected")
            print(f"  Critical Issues: {validation_report.critical_issues}")
    
    # Wait for real-time updates to process
    await asyncio.sleep(3)
    
    # Get comprehensive metrics from all components
    print(f"\\n--- System Status Report ---")
    
    # Bankroll status
    bankroll_metrics = await bankroll_validator.get_bankroll_metrics()
    print(f"\\nBankroll Status:")
    print(f"  Total Balance: ${bankroll_metrics['total_balance']}")
    print(f"  Current Exposure: ${bankroll_metrics['current_exposure']}")
    print(f"  Active Positions: {bankroll_metrics['active_positions']}")
    print(f"  Limit Utilization: {bankroll_metrics['limit_utilization']:.1%}")
    
    # Limit status
    limit_summary = await limit_manager.get_limit_summary()
    print(f"\\nLimit Status:")
    print(f"  Active Rules: {limit_summary['active_rules']}")
    print(f"  Breached Limits: {limit_summary['breached_limits']}")
    print(f"  Alerts Sent: {limit_summary['alerts_sent']}")
    
    # Exposure status
    exposure_summary = await exposure_tracker.get_exposure_summary()
    print(f"\\nExposure Status:")
    print(f"  Total Exposure: ${exposure_summary['total_exposure']}")
    print(f"  Active Positions: {exposure_summary['active_positions']}")
    print(f"  Concentration Alerts: {exposure_summary['concentration_alerts']}")
    
    # Validation status
    validation_summary = await validation_engine.get_validation_summary()
    print(f"\\nValidation Status:")
    print(f"  Total Validations: {validation_summary['performance_metrics']['total_validations']}")
    print(f"  Success Rate: {validation_summary['performance_metrics']['success_rate']:.1%}")
    print(f"  Circuit Breaker: {validation_summary['circuit_breaker']['is_active']}")
    
    # Test circuit breaker (simulate emergency)
    print(f"\\n--- Testing Circuit Breaker ---")
    await validation_engine.activate_emergency_stop()
    print("🚨 Emergency stop activated - trading suspended")
    
    # Try to validate another trade (should be rejected)
    test_opportunity = opportunities[0]
    test_report = await validation_engine.validate_trade(
        test_opportunity,
        test_opportunity.total_stake,
        user_id
    )
    
    print(f"\\nValidation during emergency stop:")
    print(f"  Score: {test_report.overall_score:.3f}")
    print(f"  Critical Issues: {test_report.critical_issues}")
    
    # Reset circuit breaker
    await validation_engine.reset_circuit_breaker()
    print("\\n✅ Circuit breaker reset - trading resumed")
    
    # Export system data
    print(f"\\n--- Data Export ---")
    validation_data = await validation_engine.export_validation_data()
    exposure_data = await exposure_tracker.export_exposure_data()
    limit_data = await limit_manager.export_rules()
    
    print(f"  Validation data: {len(validation_data['validation_rules'])} rules, "
          f"{len(validation_data['validation_history'])} history records")
    print(f"  Exposure data: {len(exposure_data['active_positions'])} positions, "
          f"{len(exposure_data['correlation_cache'])} correlations")
    print(f"  Limit data: {len(limit_data['rules'])} rules, "
          f"{len(limit_data['usage'])} usage records")
    
    # Stop all monitoring
    await asyncio.gather(
        bankroll_validator.stop_monitoring(),
        exposure_tracker.stop_monitoring(),
        validation_engine.stop_monitoring()
    )
    
    print("\\n✅ Full integration workflow demo completed")


async def main():
    """Main demonstration function."""
    print("="*80)
    print("ARBITECH RISK MANAGEMENT SYSTEM - COMPREHENSIVE DEMONSTRATION")
    print("="*80)
    print("This demonstration shows the complete bankroll and limit validation system")
    print("with real-time monitoring and enforcement capabilities.")
    
    try:
        # Run individual component demos
        await demo_bankroll_validation()
        await demo_limit_management()
        await demo_exposure_tracking()
        await demo_validation_engine()
        
        # Run full integration workflow
        await demo_integration_workflow()
        
        print("\\n" + "="*80)
        print("DEMONSTRATION COMPLETED SUCCESSFULLY")
        print("="*80)
        print("The risk management system has demonstrated:")
        print("✓ Real-time bankroll validation and balance tracking")
        print("✓ Advanced limit management with configurable rules")
        print("✓ Comprehensive exposure tracking and correlation analysis")
        print("✓ Multi-stage validation pipeline with circuit breakers")
        print("✓ Integration with ArbitrageOpportunity and Trade models")
        print("✓ Fault-tolerant operation with recovery mechanisms")
        print("✓ Detailed analytics and reporting capabilities")
        print("✓ Emergency controls and compliance features")
        
    except Exception as e:
        print(f"\\n❌ Demo failed with error: {e}")
        logger.exception("Demo failed")
        raise


if __name__ == "__main__":
    # Run the comprehensive demonstration
    asyncio.run(main())