#!/usr/bin/env python3
"""
ARBITech Example 2: Risk Management

This example demonstrates:
1. Kelly Criterion calculation for optimal position sizing
2. Circuit breaker configuration and monitoring
3. Risk analysis of arbitrage opportunities
4. Portfolio risk management
5. Real-time risk monitoring

Essential for responsible arbitrage trading.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Simulated data structures for demonstration
class RiskLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RiskAlert:
    def __init__(self, alert_type, severity, message, timestamp):
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.timestamp = timestamp

class KellyCalculator:
    """Mock Kelly Criterion calculator"""
    
    @staticmethod
    def calculate_stake(bankroll, edge, odds):
        """
        Calculate optimal stake using Kelly Criterion
        
        Formula: f = (bp - q) / b
        Where:
        f = fraction of bankroll to bet
        b = odds received on the wager
        p = probability of winning
        q = probability of losing (1-p)
        """
        
        # Convert to decimals for calculation
        bankroll = Decimal(str(bankroll))
        odds = Decimal(str(odds))
        
        # Estimate probability from edge
        # Edge is the advantage we have
        # Assuming edge = p - q (difference between win and loss probability)
        
        # For simplicity, assume we have a 2.5% edge
        # This means our win probability is higher by 2.5%
        
        # Calculate Kelly fraction
        if odds > 1:
            kelly_fraction = (edge * odds - (1 - edge)) / (odds - 1)
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
        else:
            kelly_fraction = 0
        
        # Calculate stake
        stake = bankroll * kelly_fraction
        
        return float(stake)
    
    @staticmethod
    def calculate_expected_value(bankroll, edge, odds, stake):
        """Calculate expected value of a bet"""
        p_win = 0.5 + edge / 2  # Simplified assumption
        p_loss = 1 - p_win
        
        expected_return = (p_win * stake * odds) + (p_loss * 0)
        expected_value = expected_return - stake
        
        return expected_value

class CircuitBreaker:
    """Mock circuit breaker for risk management"""
    
    def __init__(self, max_daily_loss=100, max_drawdown=0.05, max_concurrent_trades=3):
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.max_concurrent_trades = max_concurrent_trades
        
        self.daily_loss = 0.0
        self.peak_bankroll = 1000.0  # Starting bankroll
        self.current_bankroll = 1000.0
        self.active_trades = 0
        self.alerts = []
    
    def check_trade_approval(self, stake):
        """Check if a trade should be approved"""
        alerts = []
        
        # Check daily loss limit
        if self.daily_loss + stake > self.max_daily_loss:
            alerts.append(RiskAlert(
                "daily_loss_limit",
                "high",
                f"Trade would exceed daily loss limit: ${self.daily_loss + stake:.2f} > ${self.max_daily_loss:.2f}",
                datetime.now()
            ))
        
        # Check drawdown
        if self.current_bankroll < self.peak_bankroll * (1 - self.max_drawdown):
            alerts.append(RiskAlert(
                "drawdown_limit",
                "medium",
                f"Drawdown exceeds limit: {((self.peak_bankroll - self.current_bankroll) / self.peak_bankroll):.1%}",
                datetime.now()
            ))
        
        # Check concurrent trades
        if self.active_trades >= self.max_concurrent_trades:
            alerts.append(RiskAlert(
                "concurrent_trades",
                "low",
                f"Maximum concurrent trades reached: {self.active_trades}/{self.max_concurrent_trades}",
                datetime.now()
            ))
        
        return alerts
    
    def execute_trade(self, stake, profit=0):
        """Execute a trade and update risk metrics"""
        self.active_trades += 1
        self.current_bankroll -= stake
        self.daily_loss -= profit  # Profit reduces loss
        
        # Update peak bankroll
        if self.current_bankroll > self.peak_bankroll:
            self.peak_bankroll = self.current_bankroll
    
    def complete_trade(self, stake, actual_profit):
        """Complete a trade"""
        self.active_trades -= 1
        self.current_bankroll += stake + actual_profit
        
        # Update peak bankroll
        if self.current_bankroll > self.peak_bankroll:
            self.peak_bankroll = self.current_bankroll
        
        # Update daily loss
        if actual_profit < 0:
            self.daily_loss += abs(actual_profit)

class RiskAnalyzer:
    """Mock risk analyzer"""
    
    @staticmethod
    def analyze_opportunity(opportunity):
        """Analyze risk of an opportunity"""
        risk_score = 0
        risk_factors = []
        
        # Profit margin risk
        if opportunity.profit_margin < 0.02:
            risk_score += 30
            risk_factors.append("Low profit margin")
        elif opportunity.profit_margin > 0.05:
            risk_score += 20
            risk_factors.append("High profit margin (potential data error)")
        
        # Risk tier assessment
        if opportunity.risk_tier == "TIER_C":
            risk_score += 25
            risk_factors.append("Higher risk tier")
        
        # Stake size relative to bankroll
        if opportunity.required_stake > 500:
            risk_score += 15
            risk_factors.append("Large stake requirement")
        
        # Determine overall risk level
        if risk_score < 30:
            risk_level = RiskLevel.LOW
        elif risk_score < 60:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.HIGH
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommended": risk_score < 50
        }

# Reuse opportunity class from previous example
from examples.examples_util import ArbitrageOpportunity, BettingLeg, Sport, RiskTier

async def main():
    """Main demonstration function"""
    
    print("=" * 70)
    print("🛡️ ARBITECH EXAMPLE 2: RISK MANAGEMENT")
    print("=" * 70)
    print()
    
    # Step 1: Introduction
    print("📚 LEARNING OBJECTIVES:")
    print("  • Understand Kelly Criterion for position sizing")
    print("  • Learn to configure circuit breakers")
    print("  • Practice risk analysis of opportunities")
    print("  • Implement portfolio risk monitoring")
    print()
    
    # Step 2: Kelly Criterion
    print("1️⃣ KELLY CRITERION CALCULATION")
    print("-" * 35)
    print("Kelly Criterion helps determine optimal position size.")
    print("Formula: f = (bp - q) / b")
    print("Where f = fraction of bankroll to bet")
    print()
    
    bankroll = 1000.0
    edge = 0.025  # 2.5% edge
    odds = 2.0
    
    stake = KellyCalculator.calculate_stake(bankroll, edge, odds)
    expected_value = KellyCalculator.calculate_expected_value(bankroll, edge, odds, stake)
    
    print(f"Example Calculation:")
    print(f"  Bankroll: ${bankroll:.2f}")
    print(f"  Edge: {edge:.1%}")
    print(f"  Odds: {odds:.2f}")
    print(f"  Kelly Stake: ${stake:.2f} ({stake/bankroll:.1%} of bankroll)")
    print(f"  Expected Value: ${expected_value:.2f}")
    print()
    
    print("💡 Key Insights:")
    print("  • Higher edge = larger optimal stake")
    print("  • Lower odds = smaller optimal stake")
    print("  • Never bet more than Kelly recommends")
    print("  • Conservative approach: use 0.5x or 0.25x Kelly")
    print()
    
    # Step 3: Different Scenarios
    print("2️⃣ KELLY STAKE CALCULATIONS")
    print("-" * 30)
    
    scenarios = [
        {"bankroll": 500, "edge": 0.02, "odds": 1.9, "description": "Small bankroll, low edge"},
        {"bankroll": 2000, "edge": 0.03, "odds": 2.1, "description": "Large bankroll, good edge"},
        {"bankroll": 1000, "edge": 0.05, "odds": 2.5, "description": "High edge opportunity"},
    ]
    
    for scenario in scenarios:
        stake = KellyCalculator.calculate_stake(
            scenario["bankroll"], scenario["edge"], scenario["odds"]
        )
        percentage = (stake / scenario["bankroll"]) * 100
        
        print(f"\n{scenario['description']}:")
        print(f"  Bankroll: ${scenario['bankroll']:.2f}")
        print(f"  Edge: {scenario['edge']:.1%}")
        print(f"  Odds: {scenario['odds']:.2f}")
        print(f"  Recommended stake: ${stake:.2f} ({percentage:.1f}%)")
    print()
    
    # Step 4: Circuit Breakers
    print("3️⃣ CIRCUIT BREAKER CONFIGURATION")
    print("-" * 40)
    
    circuit_breaker = CircuitBreaker(
        max_daily_loss=100,
        max_drawdown=0.05,
        max_concurrent_trades=3
    )
    
    print("Circuit Breaker Settings:")
    print(f"  Max Daily Loss: ${circuit_breaker.max_daily_loss:.2f}")
    print(f"  Max Drawdown: {circuit_breaker.max_drawdown:.1%}")
    print(f"  Max Concurrent Trades: {circuit_breaker.max_concurrent_trades}")
    print()
    
    print("Current Status:")
    print(f"  Current Bankroll: ${circuit_breaker.current_bankroll:.2f}")
    print(f"  Daily Loss: ${circuit_breaker.daily_loss:.2f}")
    print(f"  Active Trades: {circuit_breaker.active_trades}")
    print()
    
    # Step 5: Risk Analysis
    print("4️⃣ OPPORTUNITY RISK ANALYSIS")
    print("-" * 35)
    
    # Create sample opportunity
    opportunity = ArbitrageOpportunity(
        sport=Sport.FOOTBALL,
        event="Manchester United vs Liverpool",
        profit_margin=0.025,
        risk_tier=RiskTier.TIER_A,
        required_stake=100.00,
        expected_return=102.50,
        legs=[
            BettingLeg("bet365", "Man United", 2.10, 48.81),
            BettingLeg("william_hill", "Liverpool", 1.95, 51.19)
        ]
    )
    
    risk_analysis = RiskAnalyzer.analyze_opportunity(opportunity)
    
    print(f"Analyzing: {opportunity.event}")
    print(f"  Profit Margin: {opportunity.profit_margin:.2%}")
    print(f"  Required Stake: ${opportunity.required_stake:.2f}")
    print(f"  Risk Score: {risk_analysis['risk_score']}/100")
    print(f"  Risk Level: {risk_analysis['risk_level'].upper()}")
    print(f"  Recommended: {'✅ YES' if risk_analysis['recommended'] else '❌ NO'}")
    print()
    
    if risk_analysis['risk_factors']:
        print("Risk Factors:")
        for factor in risk_analysis['risk_factors']:
            print(f"  • {factor}")
    print()
    
    # Step 6: Trade Approval
    print("5️⃣ TRADE APPROVAL PROCESS")
    print("-" * 30)
    
    # Check if trade should be approved
    stake = 50.0  # Proposed stake
    alerts = circuit_breaker.check_trade_approval(stake)
    
    print(f"Checking trade approval for stake: ${stake:.2f}")
    print()
    
    if not alerts:
        print("✅ Trade approved! No risk alerts.")
    else:
        print("⚠️ Risk alerts detected:")
        for alert in alerts:
            severity_icon = {"low": "🟡", "medium": "🟠", "high": "🔴"}
            print(f"  {severity_icon[alert.severity]} {alert.severity.upper()}: {alert.message}")
    print()
    
    # Step 7: Live Monitoring
    print("6️⃣ RISK MONITORING SIMULATION")
    print("-" * 35)
    
    print("Simulating trades with risk monitoring...")
    print()
    
    trades = [
        {"stake": 50, "profit": 2.50, "description": "Small winning trade"},
        {"stake": 75, "profit": -3.20, "description": "Losing trade"},
        {"stake": 100, "profit": 5.75, "description": "Medium winning trade"},
        {"stake": 80, "profit": 1.20, "description": "Small winning trade"},
    ]
    
    for i, trade in enumerate(trades, 1):
        # Check approval
        alerts = circuit_breaker.check_trade_approval(trade["stake"])
        
        if not alerts:
            print(f"Trade {i}: ✅ APPROVED")
            print(f"  ${trade['stake']:.2f} stake, ${trade['profit']:.2f} profit")
            
            # Update circuit breaker
            circuit_breaker.execute_trade(trade["stake"], trade["profit"])
            circuit_breaker.complete_trade(trade["stake"], trade["profit"])
            
            print(f"  Bankroll: ${circuit_breaker.current_bankroll:.2f}")
            print(f"  Daily Loss: ${circuit_breaker.daily_loss:.2f}")
            print(f"  Drawdown: {((circuit_breaker.peak_bankroll - circuit_breaker.current_bankroll) / circuit_breaker.peak_bankroll):.1%}")
        else:
            print(f"Trade {i}: ❌ BLOCKED")
            print(f"  ${trade['stake']:.2f} stake would trigger alerts")
            for alert in alerts:
                print(f"    ⚠️ {alert.message}")
        
        print()
    
    # Step 8: Risk Metrics Summary
    print("7️⃣ RISK METRICS SUMMARY")
    print("-" * 25)
    
    current_drawdown = (circuit_breaker.peak_bankroll - circuit_breaker.current_bankroll) / circuit_breaker.peak_bankroll
    
    print("Portfolio Risk Status:")
    print(f"  Peak Bankroll: ${circuit_breaker.peak_bankroll:.2f}")
    print(f"  Current Bankroll: ${circuit_breaker.current_bankroll:.2f}")
    print(f"  Total Drawdown: {current_drawdown:.1%}")
    print(f"  Daily Loss: ${circuit_breaker.daily_loss:.2f}")
    print(f"  Active Trades: {circuit_breaker.active_trades}")
    print()
    
    if circuit_breaker.daily_loss > circuit_breaker.max_daily_loss * 0.8:
        print("⚠️ WARNING: Approaching daily loss limit!")
    if current_drawdown > circuit_breaker.max_drawdown * 0.8:
        print("⚠️ WARNING: Approaching drawdown limit!")
    
    print()
    
    # Step 9: Best Practices
    print("8️⃣ RISK MANAGEMENT BEST PRACTICES")
    print("-" * 40)
    
    print("✅ DO:")
    print("  • Use Kelly Criterion for position sizing")
    print("  • Set conservative circuit breaker limits")
    print("  • Monitor risk metrics in real-time")
    print("  • Diversify across multiple opportunities")
    print("  • Keep detailed trading records")
    print()
    print("❌ DON'T:")
    print("  • Bet more than Kelly recommends")
    print("  • Ignore risk alerts")
    print("  • Chase losses with larger bets")
    print("  • Trade without risk limits")
    print("  • Take unnecessary risks")
    print()
    
    # Step 10: Next Steps
    print("9️⃣ NEXT STEPS")
    print("-" * 15)
    print("✅ Congratulations! You've completed the risk management tutorial.")
    print()
    print("What you've learned:")
    print("  ✓ Kelly Criterion calculation")
    print("  ✓ Circuit breaker configuration")
    print("  ✓ Risk analysis techniques")
    print("  ✓ Real-time risk monitoring")
    print("  ✓ Portfolio risk management")
    print()
    print("Recommended next steps:")
    print("  1. Run Example 3: Browser Automation")
    print("  2. Configure your own risk parameters")
    print("  3. Set up circuit breakers in production")
    print("  4. Practice with paper trading first")
    print()
    print("To continue, run:")
    print("  python examples/03_browser_automation.py")
    print()
    print("=" * 70)
    print("Example 2 completed! 🎉")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Tutorial cancelled by user. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("Please check the error message and try again.")