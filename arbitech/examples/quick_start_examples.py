#!/usr/bin/env python3
"""
ARBITech Quick Start Examples

This directory contains example scripts to help you get started with ARBITech.
Run these in order to learn the system progressively.

Files:
    01_basic_scan.py      - Simple opportunity scanning
    02_risk_management.py - Risk analysis and Kelly Criterion
    03_browser_automation.py - Automated trade execution
    04_notifications.py   - Alert and notification system
    05_hitl_workflow.py   - Human-in-the-loop approvals
    06_autonomous_trading.py - AI-powered trading
    07_full_workflow.py   - Complete end-to-end example
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 70)
print("🚀 ARBITECH QUICK START EXAMPLES")
print("=" * 70)
print()
print("Welcome to ARBITech! These examples will guide you through the system.")
print()
print("Available examples:")
print()
print("1. BASIC SCAN")
print("   File: 01_basic_scan.py")
print("   Description: Learn to scan for arbitrage opportunities")
print("   Time: 5 minutes")
print("   Level: Beginner")
print()
print("2. RISK MANAGEMENT")
print("   File: 02_risk_management.py")
print("   Description: Understand risk analysis and position sizing")
print("   Time: 10 minutes")
print("   Level: Beginner")
print()
print("3. BROWSER AUTOMATION")
print("   File: 03_browser_automation.py")
print("   Description: Set up automated trade execution")
print("   Time: 15 minutes")
print("   Level: Intermediate")
print()
print("4. NOTIFICATIONS")
print("   File: 04_notifications.py")
print("   Description: Configure alert and notification systems")
print("   Time: 10 minutes")
print("   Level: Beginner")
print()
print("5. HITL WORKFLOW")
print("   File: 05_hitl_workflow.py")
print("   Description: Implement human-in-the-loop approval process")
print("   Time: 15 minutes")
print("   Level: Intermediate")
print()
print("6. AUTONOMOUS TRADING")
print("   File: 06_autonomous_trading.py")
print("   Description: Configure AI-powered autonomous trading")
print("   Time: 20 minutes")
print("   Level: Advanced")
print()
print("7. FULL WORKFLOW")
print("   File: 07_full_workflow.py")
print("   Description: Complete end-to-end arbitrage trading workflow")
print("   Time: 30 minutes")
print("   Level: Advanced")
print()
print("=" * 70)
print()

while True:
    choice = input("Which example would you like to run? (1-7) or 'q' to quit: ").strip()
    
    examples = {
        "1": "01_basic_scan.py",
        "2": "02_risk_management.py",
        "3": "03_browser_automation.py",
        "4": "04_notifications.py",
        "5": "05_hitl_workflow.py",
        "6": "06_autonomous_trading.py",
        "7": "07_full_workflow.py"
    }
    
    if choice.lower() == 'q':
        print("\nThank you for exploring ARBITech! 🚀")
        print("Visit https://docs.arbitech.com for more resources.")
        break
    
    if choice in examples:
        example_file = examples[choice]
        print(f"\n🚀 Running {example_file}...")
        print("=" * 70)
        
        # Import and run the example
        try:
            example_path = Path(__file__).parent / example_file
            if example_path.exists():
                # Execute the example file
                import subprocess
                result = subprocess.run([sys.executable, str(example_path)], 
                                      capture_output=False, text=True)
                if result.returncode == 0:
                    print(f"\n✅ {example_file} completed successfully!")
                else:
                    print(f"\n❌ {example_file} failed with exit code {result.returncode}")
            else:
                print(f"❌ Example file {example_file} not found!")
        except Exception as e:
            print(f"❌ Error running {example_file}: {e}")
        
        print("\n" + "=" * 70)
        print()
    else:
        print("Invalid choice. Please enter 1-7 or 'q' to quit.")
        print()