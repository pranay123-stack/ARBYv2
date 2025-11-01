#!/usr/bin/env python3
"""
Example usage of the Arbitech Configuration Management System

This script demonstrates how to use the configuration system in a real
arbitrage trading application.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import init_config, get_config, get_active_bookmakers, is_bookmaker_enabled


def setup_logging():
    """Setup logging based on configuration."""
    from core.config_manager import get_config_manager
    
    manager = get_config_manager()
    if manager:
        manager.configure_logging()
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
    return logger


def check_risk_limits(opportunity):
    """
    Check if an arbitrage opportunity meets risk criteria.
    
    Args:
        opportunity: Dictionary containing opportunity details
        
    Returns:
        bool: True if opportunity meets risk criteria
    """
    # Get risk limits from configuration
    max_stake = get_config('user.risk.max_stake', 1000.0)
    risk_percentage = get_config('user.risk.risk_percentage', 2.0)
    min_odds = get_config('user.risk.min_odds', 1.5)
    max_odds = get_config('user.risk.max_odds', 10.0)
    min_profit_margin = get_config('user.risk.min_profit_margin', 1.0)
    
    # Extract opportunity details
    stake = opportunity.get('stake', 0)
    profit_margin = opportunity.get('profit_margin', 0)
    odds = opportunity.get('odds', {})
    
    # Check risk criteria
    if stake > max_stake:
        logging.warning(f"Opportunity rejected: Stake {stake} exceeds max stake {max_stake}")
        return False
    
    if profit_margin < min_profit_margin:
        logging.warning(f"Opportunity rejected: Profit margin {profit_margin}% below minimum {min_profit_margin}%")
        return False
    
    # Check if any odds are outside acceptable range
    for bookmaker, odds_value in odds.items():
        if odds_value < min_odds or odds_value > max_odds:
            logging.warning(f"Opportunity rejected: Odds {odds_value} for {bookmaker} outside range [{min_odds}, {max_odds}]")
            return False
    
    return True


def scan_bookmakers():
    """
    Simulate scanning active bookmakers for opportunities.
    """
    active_bookmakers = get_active_bookmakers()
    logging.info(f"Scanning active bookmakers: {', '.join(active_bookmakers)}")
    
    # Get scan intervals from configuration
    general_scan_interval = get_config('system.scan_intervals.general_scan', 60)
    live_odds_interval = get_config('system.scan_intervals.live_odds', 5)
    
    logging.info(f"Using scan intervals - General: {general_scan_interval}s, Live: {live_odds_interval}s")
    
    # Simulate finding an opportunity
    sample_opportunity = {
        'stake': 250.0,
        'profit_margin': 2.5,
        'odds': {
            'bet365': 2.1,
            'william_hill': 2.05,
            'ladbrokes': 2.08
        },
        'bookmakers': ['bet365', 'william_hill', 'ladbrokes']
    }
    
    return sample_opportunity


def execute_arbitrage(opportunity):
    """
    Simulate executing an arbitrage trade.
    """
    # Get bookmaker-specific configurations
    for bookmaker in opportunity['bookmakers']:
        if is_bookmaker_enabled(bookmaker):
            max_stake = get_config(f'bookmakers.{bookmaker}.max_stake_per_bet', 500.0)
            currency = get_config(f'bookmakers.{bookmaker}.currency', 'USD')
            rate_limit = get_config(f'bookmakers.{bookmaker}.rate_limit_per_minute', 30)
            
            logging.info(f"Bookmaker {bookmaker}:")
            logging.info(f"  - Max stake: {max_stake} {currency}")
            logging.info(f"  - Rate limit: {rate_limit}/minute")
            
            # Check if bookmaker can handle the stake
            if opportunity['stake'] > max_stake:
                logging.warning(f"Stake {opportunity['stake']} exceeds {bookmaker} limit {max_stake}")
                return False
    
    logging.info("All bookmakers can handle the stake")
    return True


def send_notification(opportunity):
    """
    Send notification about arbitrage opportunity.
    """
    # Get notification configuration
    notifications_enabled = get_config('notifications.triggers.enable_opportunity_alerts', True)
    min_profit_margin = get_config('notifications.triggers.min_profit_margin', 2.0)
    
    if not notifications_enabled:
        logging.info("Opportunity notifications are disabled")
        return
    
    if opportunity['profit_margin'] < min_profit_margin:
        logging.info(f"Profit margin {opportunity['profit_margin']}% below notification threshold {min_profit_margin}%")
        return
    
    # Check notification channels
    email_enabled = get_config('notifications.email.enabled', False)
    discord_enabled = get_config('notifications.discord.enabled', False)
    telegram_enabled = get_config('notifications.telegram.enabled', False)
    
    if email_enabled:
        to_addresses = get_config('notifications.email.to_addresses', [])
        logging.info(f"Would send email notification to: {to_addresses}")
    
    if discord_enabled:
        webhook_url = get_config('notifications.discord.webhook_url')
        logging.info(f"Would send Discord notification to: {webhook_url}")
    
    if telegram_enabled:
        chat_id = get_config('notifications.telegram.chat_id')
        logging.info(f"Would send Telegram notification to chat: {chat_id}")
    
    # Always log the opportunity
    logging.info(f"🎯 Arbitrage Opportunity Found!")
    logging.info(f"  - Profit Margin: {opportunity['profit_margin']}%")
    logging.info(f"  - Stake: {opportunity['stake']}")
    logging.info(f"  - Bookmakers: {', '.join(opportunity['bookmakers'])}")


def run_arbitrage_scanner():
    """
    Main arbitrage scanner loop.
    """
    logger = setup_logging()
    logger.info("Starting Arbitech Arbitrage Scanner")
    
    # Get system configuration
    max_concurrent_scans = get_config('system.performance.max_concurrent_scans', 10)
    logger.info(f"Max concurrent scans: {max_concurrent_scans}")
    
    # Check VLM configuration
    vlm_enabled = get_config('system.vlm.enabled', False)
    if vlm_enabled:
        vlm_endpoint = get_config('system.vlm.endpoint')
        logger.info(f"VLM integration enabled: {vlm_endpoint}")
    
    # Main scanning loop
    scan_count = 0
    try:
        while scan_count < 3:  # Run for 3 scans only in this example
            scan_count += 1
            logger.info(f"Starting scan #{scan_count}")
            
            # Scan for opportunities
            opportunity = scan_bookmakers()
            
            # Check if opportunity meets risk criteria
            if check_risk_limits(opportunity):
                logger.info("Opportunity passed risk checks")
                
                # Execute arbitrage
                if execute_arbitrage(opportunity):
                    logger.info("Arbitrage execution approved")
                    
                    # Send notification
                    send_notification(opportunity)
                else:
                    logger.warning("Arbitrage execution failed - stake limits exceeded")
            else:
                logger.warning("Opportunity failed risk checks")
            
            # Wait before next scan
            scan_interval = get_config('system.scan_intervals.general_scan', 60)
            logger.info(f"Waiting {scan_interval} seconds before next scan...")
            time.sleep(min(scan_interval, 5))  # Use shorter delay for demo
    
    except KeyboardInterrupt:
        logger.info("Scanner stopped by user")
    except Exception as e:
        logger.error(f"Scanner error: {e}", exc_info=True)
    
    logger.info("Arbitech Arbitrage Scanner stopped")


def main():
    """Main entry point."""
    print("="*60)
    print("Arbitech Configuration System Example")
    print("="*60)
    
    try:
        # Initialize configuration
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        print(f"\nLoading configuration from: {config_path}")
        
        init_config(config_path=config_path)
        print("✓ Configuration loaded successfully")
        
        # Display configuration summary
        print("\nConfiguration Summary:")
        print("-" * 40)
        
        # User risk settings
        max_stake = get_config('user.risk.max_stake')
        risk_pct = get_config('user.risk.risk_percentage')
        print(f"User Risk Settings:")
        print(f"  Max Stake: {max_stake}")
        print(f"  Risk Percentage: {risk_pct}%")
        
        # Active bookmakers
        active_bookmakers = get_active_bookmakers()
        print(f"\nActive Bookmakers ({len(active_bookmakers)}):")
        for bookmaker in active_bookmakers:
            currency = get_config(f'bookmakers.{bookmaker}.currency', 'USD')
            max_stake = get_config(f'bookmakers.{bookmaker}.max_stake_per_bet', 500.0)
            print(f"  - {bookmaker}: {currency} (max: {max_stake})")
        
        # System settings
        scan_interval = get_config('system.scan_intervals.general_scan')
        max_scans = get_config('system.performance.max_concurrent_scans')
        print(f"\nSystem Settings:")
        print(f"  Scan Interval: {scan_interval}s")
        print(f"  Max Concurrent Scans: {max_scans}")
        
        # Notification settings
        notifications_enabled = get_config('notifications.triggers.enable_opportunity_alerts')
        email_enabled = get_config('notifications.email.enabled')
        print(f"\nNotification Settings:")
        print(f"  Opportunity Alerts: {notifications_enabled}")
        print(f"  Email Notifications: {email_enabled}")
        
        # Run the arbitrage scanner example
        print("\n" + "="*60)
        print("Running Arbitrage Scanner Example")
        print("="*60)
        
        run_arbitrage_scanner()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
