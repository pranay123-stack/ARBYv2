#!/usr/bin/env python3
"""
Opportunity Scanner Example - Comprehensive Usage Demonstration

This script demonstrates how to use the complete opportunity scanner system
with VLM integration for arbitrage opportunity detection.

Features Demonstrated:
- Setting up the main OpportunityScanner
- Configuring scanner engine with multi-threading
- Using market monitor for real-time odds tracking
- Implementing advanced scheduling with scan scheduler
- Event handling and monitoring
- Performance metrics and health checks
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any
import json

# Add the project root to Python path
sys.path.append('/workspace')

from arbitech.detection import (
    OpportunityScanner,
    ScannerEngine,
    MarketMonitor,
    ScanScheduler,
    create_scanner,
    create_market_monitor,
    create_scheduler,
    ScannerEventType,
    MarketEventType,
    ScanPriority,
    ScheduleType,
    Sport,
    RiskTier
)
from arbitech.core.config_manager import get_config
from arbitech.storage.models import ArbitrageOpportunity


# ============================================================================
# EXAMPLE EVENT HANDLERS
# ============================================================================

class ScannerEventHandler:
    """Example event handler for scanner events."""
    
    def __init__(self):
        self.opportunity_count = 0
        self.error_count = 0
        
    async def handle_scanner_event(self, event):
        """Handle scanner events."""
        if event.event_type == ScannerEventType.OPPORTUNITY_FOUND:
            self.opportunity_count += 1
            print(f"🎯 NEW OPPORTUNITY! Total found: {self.opportunity_count}")
            if event.opportunity_id:
                print(f"   Opportunity ID: {event.opportunity_id}")
            if event.bookmaker:
                print(f"   Bookmaker: {event.bookmaker}")
            if event.sport:
                print(f"   Sport: {event.sport.value}")
                
        elif event.event_type == ScannerEventType.VLM_ERROR:
            self.error_count += 1
            print(f"⚠️ VLM Error ({self.error_count}): {event.error_message}")
            if event.bookmaker:
                print(f"   Bookmaker: {event.bookmaker}")
                
        elif event.event_type == ScannerEventType.SCAN_FAILED:
            print(f"❌ Scan failed: {event.error_message}")
            if event.bookmaker:
                print(f"   Bookmaker: {event.bookmaker}")
        
        print("-" * 50)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get event handler summary."""
        return {
            'opportunities_found': self.opportunity_count,
            'errors_encountered': self.error_count
        }


class MarketEventHandler:
    """Example event handler for market events."""
    
    def __init__(self):
        self.odds_updates = 0
        self.arbitrage_detected = 0
        
    async def handle_market_event(self, event):
        """Handle market events."""
        if event.event_type == MarketEventType.ODDS_UPDATED:
            self.odds_updates += 1
            if self.odds_updates % 10 == 0:  # Log every 10th update
                print(f"📊 Odds updates: {self.odds_updates}")
                if event.bookmaker:
                    print(f"   Latest from: {event.bookmaker}")
                    
        elif event.event_type == MarketEventType.ARBITRAGE_DETECTED:
            self.arbitrage_detected += 1
            print(f"💰 Arbitrage opportunity #{self.arbitrage_detected} detected!")
            if event.data and 'profit_margin' in event.data:
                margin = event.data['profit_margin'] * 100
                print(f"   Profit margin: {margin:.2f}%")
        
        print("-" * 30)


# ============================================================================
# EXAMPLE SCANNER SETUP
# ============================================================================

async def setup_basic_scanner():
    """Set up a basic opportunity scanner."""
    print("🚀 Setting up Basic Opportunity Scanner...")
    
    # Create scanner with minimal configuration
    scanner = await create_scanner()
    
    # Add event handlers
    scanner_handler = ScannerEventHandler()
    scanner.add_event_handler(scanner_handler.handle_scanner_event)
    
    print("✅ Basic scanner created successfully")
    return scanner, scanner_handler


async def setup_advanced_scanner():
    """Set up an advanced opportunity scanner with custom configuration."""
    print("🔧 Setting up Advanced Opportunity Scanner...")
    
    # Custom configuration
    config = {
        'scanner': {
            'max_concurrent_scans': 5,
            'min_profit_margin': 1.0,  # 1%
            'max_scan_age_seconds': 180,
            'retry_failed_scans': True,
            'max_retries': 2
        },
        'vlm': {
            'timeout': 20,
            'retry_attempts': 2,
            'rate_limit_per_minute': 30
        },
        'market_monitor': {
            'max_odds_age_seconds': 120,
            'min_confidence': 0.6,
            'opportunity_expiry_minutes': 10
        },
        'scheduler': {
            'max_concurrent_schedules': 50,
            'adaptive_scheduling': True,
            'resource_monitoring': True
        }
    }
    
    # Create scanner with custom config
    scanner = await create_scanner(config)
    
    # Add event handlers
    scanner_handler = ScannerEventHandler()
    scanner.add_event_handler(scanner_handler.handle_scanner_event)
    
    # Add market monitor handler
    market_handler = MarketEventHandler()
    scanner.market_monitor.add_event_handler(market_handler.handle_market_event)
    
    print("✅ Advanced scanner created successfully")
    return scanner, scanner_handler, market_handler


async def setup_scheduled_scanning(scanner):
    """Set up scheduled scanning patterns."""
    print("📅 Setting up Scheduled Scanning...")
    
    # Create a scheduler
    scheduler = scanner.scan_scheduler
    
    # Schedule 1: Quick scans every 30 seconds for Bet365
    from arbitech.detection.scan_scheduler import create_quick_scan_schedule
    
    quick_schedule = create_quick_scan_schedule(
        bookmaker="bet365",
        sport="football",
        interval_seconds=30,
        priority=ScanPriority.HIGH
    )
    
    quick_id = scheduler.create_schedule(quick_schedule)
    print(f"   Created quick scan schedule: {quick_id}")
    
    # Schedule 2: Comprehensive scans every 2 minutes
    from arbitech.detection.scan_scheduler import ScheduleConfig
    
    comprehensive_schedule = ScheduleConfig(
        name="Comprehensive Football Scans",
        description="Regular comprehensive scans for football markets",
        schedule_type=ScheduleType.INTERVAL,
        interval_seconds=120,
        bookmakers=["bet365", "william_hill", "ladbrokes"],
        sports=["football", "tennis"],
        market_types=["match_winner", "over_under"],
        priority=ScanPriority.NORMAL,
        max_concurrent=3
    )
    
    comprehensive_id = scheduler.create_schedule(comprehensive_schedule)
    print(f"   Created comprehensive schedule: {comprehensive_id}")
    
    # Schedule 3: Cron-based scans for specific times
    from arbitech.detection.scan_scheduler import create_cron_scan_schedule
    
    # Run every 15 minutes during business hours
    cron_schedule = create_cron_scan_schedule(
        name="Business Hours Scanning",
        bookmakers=["pinnacle", "betfair"],
        sports=["basketball"],
        cron_expression="*/15 9-17 * * *",  # Every 15 minutes, 9 AM to 5 PM
        priority=ScanPriority.NORMAL
    )
    
    cron_id = scheduler.create_schedule(cron_schedule)
    print(f"   Created cron schedule: {cron_id}")
    
    print("✅ Scheduling setup completed")
    return [quick_id, comprehensive_id, cron_id]


# ============================================================================
# SCAN SIMULATION
# ============================================================================

async def simulate_scans(scanner: OpportunityScanner, num_scans: int = 10):
    """Simulate scanning operations for demonstration."""
    print(f"🔍 Simulating {num_scans} scans...")
    
    # Sample bookmaker and sport combinations
    sample_data = [
        ("bet365", Sport.FOOTBALL, "https://example.com/bet365_football.png"),
        ("william_hill", Sport.TENNIS, "https://example.com/wh_tennis.png"),
        ("ladbrokes", Sport.BASKETBALL, "https://example.com/ladbrokes_basketball.png"),
        ("pinnacle", Sport.FOOTBALL, "https://example.com/pinnacle_football.png"),
        ("betfair", Sport.TENNIS, "https://example.com/betfair_tennis.png"),
    ]
    
    for i in range(num_scans):
        bookmaker, sport, image_data = sample_data[i % len(sample_data)]
        
        print(f"   Scan {i+1}/{num_scans}: {bookmaker} ({sport.value})")
        
        try:
            # Perform scan (this would normally use real image data)
            opportunity = await scanner.scan_bookmaker(
                bookmaker=bookmaker,
                sport=sport,
                image_data=image_data,
                market_type="match_winner",
                event_name=f"{sport.value.title()} Match"
            )
            
            if opportunity:
                print(f"   ✅ Found opportunity: {float(opportunity.profit_margin)*100:.2f}% margin")
            else:
                print(f"   ℹ️ No opportunity found")
                
        except Exception as e:
            print(f"   ❌ Scan failed: {str(e)}")
        
        # Small delay between scans
        await asyncio.sleep(0.5)
    
    print("✅ Scan simulation completed")


# ============================================================================
# MONITORING AND METRICS
# ============================================================================

async def display_scanner_status(scanner: OpportunityScanner):
    """Display current scanner status and metrics."""
    print("📊 Scanner Status Report")
    print("=" * 50)
    
    status = scanner.get_status()
    print(f"Session ID: {status['session_id']}")
    print(f"Status: {status['status']}")
    print(f"Active Scans: {status['active_scans']}")
    print(f"Active Bookmakers: {status['active_bookmakers']}")
    print(f"Uptime: {status['uptime_minutes']:.1f} minutes")
    
    metrics = status['metrics']
    print(f"\n📈 Performance Metrics:")
    print(f"Total Scans: {metrics['total_scans']}")
    print(f"Success Rate: {metrics['success_rate']:.2%}")
    print(f"VLM API Calls: {metrics['vlm_api_calls']}")
    print(f"VLM Success Rate: {metrics['vlm_success_rate']:.2%}")
    print(f"Opportunities Found: {metrics['opportunities_found']}")
    print(f"Average Scan Time: {metrics['average_scan_time']:.2f}s")
    
    if metrics['last_scan_at']:
        print(f"Last Scan: {metrics['last_scan_at']}")


async def display_market_state(monitor: MarketMonitor):
    """Display current market state."""
    print("\n🏪 Market State Report")
    print("=" * 50)
    
    summary = monitor.get_state_summary()
    print(f"Total Markets: {summary['total_markets']}")
    print(f"Active Bookmakers: {summary['active_bookmakers']}")
    print(f"Total Opportunities: {summary['total_opportunities']}")
    
    if summary['market_types']:
        print(f"\nMarket Types: {summary['market_types']}")
    
    if summary['sports_distribution']:
        print(f"Sports Distribution: {summary['sports_distribution']}")
    
    print(f"Average Confidence: {summary['average_confidence']:.2%}")


async def display_scheduler_status(scheduler: ScanScheduler):
    """Display scheduler status and metrics."""
    print("\n⏰ Scheduler Status Report")
    print("=" * 50)
    
    metrics = scheduler.get_scheduler_metrics()
    print(f"Total Schedules: {metrics['total_schedules']}")
    print(f"Active Schedules: {metrics['active_schedules']}")
    print(f"Total Scheduled Scans: {metrics['total_scheduled_scans']}")
    print(f"Success Rate: {metrics['success_rate']:.2%}")
    print(f"Resource Adjustments: {metrics['resource_adjustments']}")
    
    if metrics['schedule_types']:
        print(f"Schedule Types: {metrics['schedule_types']}")
    
    resource_usage = metrics['current_resource_usage']
    print(f"\nResource Usage:")
    print(f"CPU: {resource_usage.get('cpu_percent', 0):.1f}%")
    print(f"Memory: {resource_usage.get('memory_percent', 0):.1f}%")


async def display_opportunities(scanner: OpportunityScanner, limit: int = 5):
    """Display discovered arbitrage opportunities."""
    print(f"\n🎯 Top {limit} Arbitrage Opportunities")
    print("=" * 50)
    
    opportunities = scanner.get_opportunities(limit=limit)
    
    if not opportunities:
        print("No opportunities found yet.")
        return
    
    for i, opp in enumerate(opportunities, 1):
        print(f"\n{i}. {opp.event_name} ({opp.sport.value})")
        print(f"   Profit Margin: {float(opp.profit_margin)*100:.2f}%")
        print(f"   Expected Profit: ${float(opp.profit_amount):.2f}")
        print(f"   Risk Tier: {opp.risk_tier.value.upper()}")
        print(f"   Legs: {len(opp.legs)}")
        
        for leg in opp.legs:
            print(f"     - {leg.bookmaker}: {leg.event_outcome} @ {float(leg.odds):.2f}")


# ============================================================================
# HEALTH CHECKS
# ============================================================================

async def perform_health_checks(scanner: OpportunityScanner):
    """Perform comprehensive health checks."""
    print("\n🏥 Health Check Report")
    print("=" * 50)
    
    # VLM Extractor health
    try:
        vlm_healthy = await scanner.vlm_extractor.health_check()
        print(f"VLM Extractor: {'✅ Healthy' if vlm_healthy else '❌ Unhealthy'}")
    except Exception as e:
        print(f"VLM Extractor: ❌ Error - {str(e)}")
    
    # Scanner Engine health
    try:
        engine_healthy = await scanner.scanner_engine.health_check()
        print(f"Scanner Engine: {'✅ Healthy' if engine_healthy else '❌ Unhealthy'}")
    except Exception as e:
        print(f"Scanner Engine: ❌ Error - {str(e)}")
    
    # Market Monitor health
    try:
        # Check market monitor internal state
        market_healthy = len(scanner.market_monitor.current_odds) >= 0
        print(f"Market Monitor: {'✅ Healthy' if market_healthy else '❌ Unhealthy'}")
    except Exception as e:
        print(f"Market Monitor: ❌ Error - {str(e)}")
    
    # Overall system health
    overall_healthy = (
        vlm_healthy if 'vlm_healthy' in locals() else False and
        engine_healthy if 'engine_healthy' in locals() else False
    )
    
    print(f"\nOverall System: {'✅ Healthy' if overall_healthy else '⚠️ Needs Attention'}")


# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

async def main():
    """Main demonstration function."""
    print("🚀 ARBitech Opportunity Scanner - Comprehensive Demo")
    print("=" * 60)
    
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 1. Set up advanced scanner
        scanner, scanner_handler, market_handler = await setup_advanced_scanner()
        
        # 2. Start scanning
        print("\n🎬 Starting Scanner...")
        success = await scanner.start_scanning()
        if not success:
            print("❌ Failed to start scanner")
            return
        
        # 3. Set up scheduled scanning
        schedule_ids = await setup_scheduled_scanning(scanner)
        
        # 4. Perform some simulated scans
        await simulate_scans(scanner, num_scans=15)
        
        # 5. Display status and metrics
        await display_scanner_status(scanner)
        await display_market_state(scanner.market_monitor)
        await display_scheduler_status(scanner.scan_scheduler)
        
        # 6. Display opportunities
        await display_opportunities(scanner, limit=3)
        
        # 7. Perform health checks
        await perform_health_checks(scanner)
        
        # 8. Show event handler summary
        print("\n📊 Event Handler Summary")
        print("=" * 50)
        scanner_summary = scanner_handler.get_summary()
        market_summary = market_handler.get_summary()
        
        print(f"Scanner Events:")
        print(f"  Opportunities Found: {scanner_summary['opportunities_found']}")
        print(f"  Errors Encountered: {scanner_summary['errors_encountered']}")
        
        print(f"Market Events:")
        print(f"  Odds Updates: {market_summary['odds_updates']}")
        print(f"  Arbitrage Detected: {market_summary['arbitrage_detected']}")
        
        # 9. Keep running for a bit to demonstrate real-time operation
        print("\n⏳ Running for 30 seconds to demonstrate real-time operation...")
        await asyncio.sleep(30)
        
        # 10. Final status
        await display_scanner_status(scanner)
        await display_opportunities(scanner, limit=5)
        
        # Cleanup
        print("\n🛑 Stopping Scanner...")
        await scanner.stop_scanning()
        
        print("\n✅ Demo completed successfully!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("Starting ARBitech Opportunity Scanner Demo...")
    print("Press Ctrl+C to stop the demo at any time.")
    print()
    
    # Run the demonstration
    asyncio.run(main())