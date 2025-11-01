#!/usr/bin/env python3
"""
ARBITech Interactive Onboarding Tutorial

This script provides a step-by-step interactive tutorial for new users.
Run this to get personalized onboarding based on your experience level.

Usage:
    python tutorial.py [--user-id USER_ID]
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import arbitech
sys.path.insert(0, str(Path(__file__).parent.parent))

from docs.onboarding import (
    OnboardingSystem, UserLevel, Component, UserProfile
)


class InteractiveTutorial:
    """Interactive tutorial class"""
    
    def __init__(self):
        self.onboarding = OnboardingSystem()
        self.current_user = None
    
    async def run(self):
        """Run the interactive tutorial"""
        print("=" * 60)
        print("🚀 ARBITECH INTERACTIVE TUTORIAL")
        print("=" * 60)
        print()
        
        # Step 1: Create or load user profile
        await self._setup_user_profile()
        
        # Step 2: Show personalized path
        await self._show_onboarding_path()
        
        # Step 3: Interactive tutorials
        await self._run_interactive_tutorials()
        
        # Step 4: Wrap up
        await self._wrap_up()
    
    async def _setup_user_profile(self):
        """Setup user profile"""
        print("Step 1: User Profile Setup")
        print("-" * 30)
        
        # Get user ID
        user_id = input("Enter your user ID (or press Enter for 'demo_user'): ").strip()
        if not user_id:
            user_id = "demo_user"
        
        # Check if user exists
        if user_id in self.onboarding.users:
            print(f"Welcome back, {self.onboarding.users[user_id].name}!")
            self.current_user = self.onboarding.users[user_id]
        else:
            # Create new profile
            name = input("Enter your name: ").strip() or "Demo User"
            
            print("\nWhat's your experience level?")
            print("1. Beginner - New to arbitrage trading")
            print("2. Intermediate - Some experience with trading systems")
            print("3. Advanced - Experienced with algorithmic trading")
            
            level_choice = input("Enter choice (1-3): ").strip()
            level_map = {
                "1": UserLevel.BEGINNER,
                "2": UserLevel.INTERMEDIATE,
                "3": UserLevel.ADVANCED
            }
            level = level_map.get(level_choice, UserLevel.BEGINNER)
            
            print("\nWhich components interest you most? (choose all that apply)")
            print("1. Detection & Scanning")
            print("2. Risk Management")
            print("3. Browser Automation")
            print("4. Human-in-the-Loop (HITL)")
            print("5. Autonomous Trading")
            print("6. Notifications")
            print("7. Data Storage & Analytics")
            
            interests_input = input("Enter numbers (comma-separated): ").strip()
            interest_map = {
                "1": Component.DETECTION,
                "2": Component.RISK_MANAGEMENT,
                "3": Component.BROWSER_AUTOMATION,
                "4": Component.HITL,
                "5": Component.AUTONOMOUS,
                "6": Component.NOTIFICATIONS,
                "7": Component.STORAGE
            }
            
            interests = []
            for num in interests_input.split(","):
                num = num.strip()
                if num in interest_map:
                    interests.append(interest_map[num])
            
            if not interests:
                interests = [Component.DETECTION]  # Default
            
            self.current_user = self.onboarding.create_user_profile(
                user_id, name, level, interests
            )
        
        print(f"\n✅ Profile setup complete!")
        print(f"Welcome, {self.current_user.name}!")
        print(f"Skill Level: {self.current_user.level.value.title()}")
        print(f"Interests: {', '.join([c.value.replace('_', ' ').title() for c in self.current_user.interests])}")
        print()
    
    async def _show_onboarding_path(self):
        """Show personalized onboarding path"""
        print("Step 2: Your Personalized Onboarding Path")
        print("-" * 45)
        
        path = self.onboarding.get_personalized_onboarding_path(self.current_user.user_id)
        
        print(f"Based on your profile, here's your recommended path ({len(path)} steps):\n")
        
        for i, step in enumerate(path, 1):
            status = "✅" if step.id in self.current_user.completed_steps else "📋"
            print(f"{i}. {status} {step.title}")
            print(f"   Component: {step.component.value.replace('_', ' ').title()}")
            print(f"   Duration: {step.estimated_time} minutes")
            print(f"   Level: {step.user_level.value.title()}")
            print(f"   Description: {step.description}")
            print()
        
        print("You can:")
        print("1. Start the first step")
        print("2. View a specific step in detail")
        print("3. Skip to the next tutorial section")
        choice = input("\nWhat would you like to do? (1-3): ").strip()
        
        if choice == "1" and path:
            await self._run_step(path[0])
        elif choice == "2":
            step_num = input(f"Enter step number (1-{len(path)}): ").strip()
            try:
                step_idx = int(step_num) - 1
                if 0 <= step_idx < len(path):
                    await self._run_step(path[step_idx])
                else:
                    print("Invalid step number")
            except ValueError:
                print("Invalid input")
        print()
    
    async def _run_step(self, step):
        """Run a specific onboarding step"""
        print(f"\n🔄 Running Step: {step.title}")
        print("=" * 50)
        print(f"Description: {step.description}")
        print(f"Estimated time: {step.estimated_time} minutes")
        print()
        
        # Show prerequisites
        if step.prerequisites:
            print("Prerequisites:")
            for prereq in step.prerequisites:
                print(f"  - {prereq}")
            print()
        
        # Show actions
        print("Actions to complete:")
        for i, action in enumerate(step.actions, 1):
            print(f"  {i}. {action}")
        print()
        
        # Show code examples
        if step.code_examples:
            print("Code Examples:")
            for example in step.code_examples:
                print(f"  ```python")
                print(f"  {example}")
                print(f"  ```")
            print()
        
        # Show troubleshooting tips
        if step.troubleshooting_tips:
            print("Troubleshooting Tips:")
            for tip in step.troubleshooting_tips:
                print(f"  • {tip}")
            print()
        
        # Simulate completion
        print("Press Enter when you've completed this step (or type 'skip' to skip):", end=" ")
        response = input()
        
        if response.lower() != 'skip':
            result = self.onboarding.simulate_onboarding_step(
                self.current_user.user_id, step.id
            )
            print(f"\n✅ Step marked as complete!")
            print(f"Progress: {result['completion_percentage']:.1f}%")
        
        print()
    
    async def _run_interactive_tutorials(self):
        """Run interactive component tutorials"""
        print("Step 3: Interactive Component Tutorials")
        print("-" * 40)
        
        tutorials = {
            "detection": self._tutorial_detection,
            "risk": self._tutorial_risk_management,
            "automation": self._tutorial_browser_automation,
            "notifications": self._tutorial_notifications
        }
        
        for component in self.current_user.interests:
            component_name = component.value
            if component_name in tutorials:
                print(f"\n📚 {component_name.replace('_', ' ').title()} Tutorial")
                print("-" * 40)
                
                await tutorials[component_name]()
    
    async def _tutorial_detection(self):
        """Interactive detection tutorial"""
        print("Welcome to the Detection Engine tutorial!")
        print()
        
        # Simulate code execution
        print("Let's create a simple opportunity scanner:")
        print()
        
        example_code = '''
from detection.opportunity_scanner import OpportunityScanner

# Initialize scanner
scanner = OpportunityScanner()

# Configure scanning parameters
scanner.set_bookmakers(["bet365", "william_hill"])
scanner.set_sports(["football", "basketball"])
scanner.set_min_profit(0.02)  # 2% minimum

# Run scan
opportunities = await scanner.scan_markets()

print(f"Found {len(opportunities)} opportunities")
        '''
        
        print("Example code:")
        print(example_code)
        
        # Simulate running the code
        print("Running scan simulation...")
        await asyncio.sleep(2)
        
        # Show simulated results
        print("\n✅ Simulated Results:")
        print("  • Found 3 opportunities")
        print("  • Average profit: 2.8%")
        print("  • Total potential profit: $47.50")
        print()
        
        print("Key concepts learned:")
        print("  ✓ How to initialize the scanner")
        print("  ✓ How to configure scan parameters")
        print("  ✓ How to interpret scan results")
        print()
        
        input("Press Enter to continue...")
    
    async def _tutorial_risk_management(self):
        """Interactive risk management tutorial"""
        print("Welcome to Risk Management tutorial!")
        print()
        
        print("Risk management is crucial for successful arbitrage trading.")
        print("Let's learn about Kelly Criterion and circuit breakers.\n")
        
        # Kelly Criterion example
        print("Kelly Criterion for Position Sizing:")
        kelly_example = '''
from risk.kelly_calculator import KellyCalculator

kelly = KellyCalculator()
stake = kelly.calculate_stake(
    bankroll=1000,    # Your total money
    edge=0.025,       # Your advantage (2.5%)
    odds=2.0          # Average odds
)

print(f"Recommended stake: ${stake:.2f}")
        '''
        
        print(kelly_example)
        print("Running calculation...")
        await asyncio.sleep(1)
        print("Recommended stake: $25.00")
        print()
        
        # Circuit breaker example
        print("Circuit Breaker Configuration:")
        circuit_example = '''
from risk.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker()
breaker.set_max_daily_loss(100)     # Stop if losing $100 in a day
breaker.set_max_drawdown(0.05)      # Stop if down 5%
breaker.set_max_concurrent_trades(3) # Max 3 trades at once
        '''
        
        print(circuit_example)
        print("\nKey concepts learned:")
        print("  ✓ Kelly Criterion calculation")
        print("  ✓ Circuit breaker setup")
        print("  ✓ Risk parameter configuration")
        print()
        
        input("Press Enter to continue...")
    
    async def _tutorial_browser_automation(self):
        """Interactive browser automation tutorial"""
        print("Welcome to Browser Automation tutorial!")
        print()
        
        print("Browser automation allows ARBITech to execute trades automatically.")
        print("Let's set up a basic execution workflow.\n")
        
        automation_example = '''
from automation.arbitrage_executor import ArbitrageExecutor
from automation.execution_tracker import ExecutionTracker

# Initialize executor
executor = ArbitrageExecutor()
tracker = ExecutionTracker()

# Execute opportunity (dry run for safety)
trade = await executor.execute_opportunity(
    opportunity=opportunity,
    dry_run=True  # Set to False for real trading
)

# Track execution
status = await tracker.get_trade_status(trade.id)
print(f"Trade status: {status}")
        '''
        
        print("Basic automation code:")
        print(automation_example)
        print("\nFeatures demonstrated:")
        print("  ✓ Automated trade execution")
        print("  ✓ Execution tracking")
        print("  ✓ Dry-run safety mode")
        print()
        
        print("Safety features:")
        print("  • Dry-run mode for testing")
        print("  • Automatic screenshot capture")
        print("  • Error recovery mechanisms")
        print("  • Execution time monitoring")
        print()
        
        input("Press Enter to continue...")
    
    async def _tutorial_notifications(self):
        """Interactive notifications tutorial"""
        print("Welcome to Notifications tutorial!")
        print()
        
        print("Stay informed with real-time alerts about opportunities and trades.")
        print("Let's set up multiple notification channels.\n")
        
        notifications_example = '''
from notifications.email_notifications import EmailNotifier
from notifications.telegram_bot import TelegramBot

# Email notifications
email = EmailNotifier()
await email.send_opportunity_alert(
    recipient="your@email.com",
    opportunity=opportunity
)

# Telegram bot
telegram = TelegramBot()
await telegram.send_trade_alert(
    chat_id="your_chat_id",
    message=f"New opportunity: {opp.profit_margin:.2%} profit!"
)
        '''
        
        print("Notification setup:")
        print(notifications_example)
        print("\nChannels available:")
        print("  ✓ Email notifications")
        print("  ✓ Telegram bot")
        print("  ✓ Dashboard alerts")
        print("  ✓ SMS (coming soon)")
        print()
        
        input("Press Enter to continue...")
    
    async def _wrap_up(self):
        """Wrap up the tutorial"""
        print("\n" + "=" * 60)
        print("🎉 TUTORIAL COMPLETE!")
        print("=" * 60)
        print()
        
        # Show statistics
        stats = self.onboarding.get_user_statistics(self.current_user.user_id)
        print("Your Progress Summary:")
        print(f"  • Steps completed: {stats['completed_steps']}/{stats['total_steps']}")
        print(f"  • Completion percentage: {stats['completion_percentage']:.1f}%")
        print(f"  • Time spent: {stats['estimated_time_spent']} minutes")
        print()
        
        # Show next steps
        print("Next Steps:")
        print("1. Configure your bookmaker accounts")
        print("2. Run your first scan")
        print("3. Set up risk management")
        print("4. Explore advanced features")
        print()
        
        # Offer to generate documentation
        print("Would you like me to generate your personalized documentation?")
        choice = input("Generate docs? (y/n): ").strip().lower()
        
        if choice == 'y':
            docs_dir = Path.home() / "arbitech_docs"
            docs_dir.mkdir(exist_ok=True)
            
            # Generate user manual
            manual_path = docs_dir / "user_manual.md"
            self.onboarding.generate_user_manual(
                self.current_user.user_id, str(manual_path)
            )
            print(f"✅ User manual generated: {manual_path}")
            
            # Generate API documentation
            api_path = docs_dir / "api_documentation.md"
            self.onboarding.generate_api_documentation(str(api_path))
            print(f"✅ API documentation generated: {api_path}")
            
            # Generate troubleshooting guide
            troubleshooting_path = docs_dir / "troubleshooting_guide.md"
            self.onboarding.generate_troubleshooting_guide(str(troubleshooting_path))
            print(f"✅ Troubleshooting guide generated: {troubleshooting_path}")
        
        print("\nThank you for using ARBITech! 🚀")
        print("Visit https://docs.arbitech.com for more resources.")


async def main():
    """Main entry point"""
    tutorial = InteractiveTutorial()
    await tutorial.run()


if __name__ == "__main__":
    asyncio.run(main())