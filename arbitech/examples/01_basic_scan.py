#!/usr/bin/env python3
"""
ARBITech Example 1: Basic Opportunity Scanning

This example demonstrates:
1. How to initialize the opportunity scanner
2. How to configure scanning parameters
3. How to run a scan for arbitrage opportunities
4. How to interpret and display results

Perfect for beginners who want to understand the core detection functionality.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Simulated data structures for demonstration
class Sport:
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    TENNIS = "tennis"

class RiskTier:
    TIER_A = "TIER_A"  # Safest
    TIER_B = "TIER_B"  # Moderate risk
    TIER_C = "TIER_C"  # Higher risk

class ArbitrageOpportunity:
    def __init__(self, sport, event, profit_margin, risk_tier, required_stake, expected_return, legs):
        self.sport = sport
        self.event = event
        self.profit_margin = profit_margin
        self.risk_tier = risk_tier
        self.required_stake = required_stake
        self.expected_return = expected_return
        self.legs = legs
        self.timestamp = datetime.now()

class BettingLeg:
    def __init__(self, bookmaker, outcome, odds, stake):
        self.bookmaker = bookmaker
        self.outcome = outcome
        self.odds = odds
        self.stake = stake

class MockOpportunityScanner:
    """Mock scanner for demonstration purposes"""
    
    def __init__(self):
        self.bookmakers = []
        self.sports = []
        self.min_profit = 0.02
    
    def set_bookmakers(self, bookmakers):
        self.bookmakers = bookmakers
    
    def set_sports(self, sports):
        self.sports = sports
    
    def set_min_profit(self, min_profit):
        self.min_profit = min_profit
    
    async def scan_markets(self):
        """Simulate scanning for opportunities"""
        print("🔍 Scanning markets...")
        await asyncio.sleep(2)  # Simulate API calls
        
        # Generate mock opportunities
        opportunities = [
            ArbitrageOpportunity(
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
            ),
            ArbitrageOpportunity(
                sport=Sport.BASKETBALL,
                event="Lakers vs Warriors",
                profit_margin=0.031,
                risk_tier=RiskTier.TIER_A,
                required_stake=150.00,
                expected_return=154.65,
                legs=[
                    BettingLeg("bet365", "Lakers", 2.05, 73.17),
                    BettingLeg("pinnacle", "Warriors", 1.98, 76.83)
                ]
            ),
            ArbitrageOpportunity(
                sport=Sport.TENNIS,
                event="Djokovic vs Nadal",
                profit_margin=0.018,
                risk_tier=RiskTier.TIER_B,
                required_stake=200.00,
                expected_return=203.60,
                legs=[
                    BettingLeg("bet365", "Djokovic", 2.00, 101.80),
                    BettingLeg("william_hill", "Nadal", 2.02, 98.20)
                ]
            )
        ]
        
        # Filter by minimum profit
        filtered = [opp for opp in opportunities if opp.profit_margin >= self.min_profit]
        
        return filtered

async def main():
    """Main demonstration function"""
    
    print("=" * 70)
    print("📊 ARBITECH EXAMPLE 1: BASIC OPPORTUNITY SCANNING")
    print("=" * 70)
    print()
    
    # Step 1: Introduction
    print("📚 LEARNING OBJECTIVES:")
    print("  • Understand how opportunity scanning works")
    print("  • Learn to configure scan parameters")
    print("  • Practice interpreting scan results")
    print("  • Understand profit calculations")
    print()
    
    # Step 2: Initialize Scanner
    print("1️⃣ INITIALIZING SCANNER")
    print("-" * 30)
    print("Creating opportunity scanner...")
    scanner = MockOpportunityScanner()
    print("✅ Scanner initialized successfully!")
    print()
    
    # Step 3: Configure Parameters
    print("2️⃣ CONFIGURING SCAN PARAMETERS")
    print("-" * 35)
    
    print("Setting bookmakers to scan:")
    bookmakers = ["bet365", "william_hill", "pinnacle"]
    for bookmaker in bookmakers:
        print(f"  • {bookmaker}")
    scanner.set_bookmakers(bookmakers)
    print()
    
    print("Setting sports to scan:")
    sports = [Sport.FOOTBALL, Sport.BASKETBALL, Sport.TENNIS]
    for sport in sports:
        print(f"  • {sport.title()}")
    scanner.set_sports(sports)
    print()
    
    print("Setting minimum profit margin: 2.5%")
    scanner.set_min_profit(0.025)
    print()
    
    # Step 4: Run Scan
    print("3️⃣ RUNNING OPPORTUNITY SCAN")
    print("-" * 30)
    print("This may take a few seconds as we query multiple bookmakers...")
    
    try:
        opportunities = await scanner.scan_markets()
        print(f"✅ Scan completed! Found {len(opportunities)} opportunities.")
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        print("💡 Check your internet connection and API credentials.")
        return
    print()
    
    # Step 5: Display Results
    print("4️⃣ SCAN RESULTS")
    print("-" * 20)
    
    if not opportunities:
        print("❌ No opportunities found matching your criteria.")
        print()
        print("💡 Suggestions:")
        print("  • Lower the minimum profit threshold")
        print("  • Add more bookmakers to scan")
        print("  • Check if bookmaker APIs are accessible")
        print("  • Try scanning at different times")
    else:
        print(f"🎯 FOUND {len(opportunities)} ARBITRAGE OPPORTUNITIES")
        print()
        
        for i, opp in enumerate(opportunities, 1):
            print(f"--- OPPORTUNITY #{i} ---")
            print(f"Sport: {opp.sport.title()}")
            print(f"Event: {opp.event}")
            print(f"Profit Margin: {opp.profit_margin:.2%}")
            print(f"Risk Tier: {opp.risk_tier}")
            print(f"Required Stake: ${opp.required_stake:.2f}")
            print(f"Expected Return: ${opp.expected_return:.2f}")
            print(f"Expected Profit: ${opp.expected_return - opp.required_stake:.2f}")
            print()
            print("Betting Strategy:")
            for leg in opp.legs:
                print(f"  • {leg.bookmaker}: ${leg.stake:.2f} on {leg.outcome} (Odds: {leg.odds})")
            print()
    
    # Step 6: Explain Results
    print("5️⃣ UNDERSTANDING THE RESULTS")
    print("-" * 30)
    print("Key metrics explained:")
    print()
    print("📊 Profit Margin:")
    print("  The percentage profit you can make if the arbitrage succeeds.")
    print("  Formula: (1/Odds1 + 1/Odds2) - 1")
    print()
    print("🎯 Risk Tier:")
    print("  TIER_A: Lowest risk, most conservative")
    print("  TIER_B: Moderate risk, balanced approach")
    print("  TIER_C: Higher risk, maximum profit potential")
    print()
    print("💰 Required Stake:")
    print("  Total amount you need to bet across all bookmakers")
    print()
    print("📈 Expected Return:")
    print("  Total amount you'll receive if all bets win")
    print()
    
    # Step 7: Calculate Example
    print("6️⃣ PROFIT CALCULATION EXAMPLE")
    print("-" * 35)
    print("Let's trace through a profit calculation:")
    print()
    
    if opportunities:
        opp = opportunities[0]  # Use first opportunity
        print(f"Example: {opp.event}")
        print(f"Total stake: ${opp.required_stake:.2f}")
        print()
        print("If Manchester United wins:")
        print(f"  Return from bet365: ${opp.legs[0].stake * opp.legs[0].odds:.2f}")
        print(f"  Loss from william_hill: ${opp.legs[1].stake:.2f}")
        print(f"  Net profit: ${(opp.legs[0].stake * opp.legs[0].odds) - opp.required_stake:.2f}")
        print()
        print("If Liverpool wins:")
        print(f"  Return from william_hill: ${opp.legs[1].stake * opp.legs[1].odds:.2f}")
        print(f"  Loss from bet365: ${opp.legs[0].stake:.2f}")
        print(f"  Net profit: ${(opp.legs[1].stake * opp.legs[1].odds) - opp.required_stake:.2f}")
        print()
        print("Either way, you profit!")
        print()
    
    # Step 8: Next Steps
    print("7️⃣ NEXT STEPS")
    print("-" * 15)
    print("✅ Congratulations! You've completed the basic scanning tutorial.")
    print()
    print("What you've learned:")
    print("  ✓ How to initialize the scanner")
    print("  ✓ How to configure scan parameters")
    print("  ✓ How to interpret scan results")
    print("  ✓ Understanding profit calculations")
    print()
    print("Recommended next steps:")
    print("  1. Run Example 2: Risk Management")
    print("  2. Learn about Kelly Criterion for position sizing")
    print("  3. Configure your bookmaker accounts")
    print("  4. Set up risk management rules")
    print()
    print("To continue, run:")
    print("  python examples/02_risk_management.py")
    print()
    print("=" * 70)
    print("Example 1 completed! 🎉")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Tutorial cancelled by user. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("Please check the error message and try again.")