#!/usr/bin/env python3
"""
Test script for the Arbitech Configuration Management System

This script demonstrates the functionality of the config manager including:
- Loading configuration from YAML file
- Accessing configuration values
- Environment variable overrides
- Configuration validation
- Hot-reload functionality
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.config_manager import (
    init_config, get_config, set_config, reload_config,
    get_user_config, get_system_config, get_bookmaker_configs,
    get_notification_config, get_logging_config,
    get_risk_limits, get_scan_intervals, get_active_bookmakers,
    is_bookmaker_enabled, ConfigError
)


def setup_logging():
    """Setup basic logging for the test script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_basic_config_access():
    """Test basic configuration access methods."""
    print("\n" + "="*60)
    print("TESTING BASIC CONFIGURATION ACCESS")
    print("="*60)
    
    # Test getting user configuration
    user_config = get_user_config()
    print(f"\nUser configuration: {user_config}")
    
    # Test getting system configuration
    system_config = get_system_config()
    print(f"\nSystem configuration keys: {list(system_config.keys())}")
    
    # Test accessing nested values
    max_stake = get_config('user.risk.max_stake')
    print(f"\nMax stake: {max_stake}")
    
    vlm_enabled = get_config('system.vlm.enabled', False)
    print(f"VLM enabled: {vlm_enabled}")
    
    # Test getting bookmaker configurations
    bookmaker_configs = get_bookmaker_configs()
    print(f"\nConfigured bookmakers: {list(bookmaker_configs.keys())}")
    
    # Test active bookmakers
    active_bookmakers = get_active_bookmakers()
    print(f"Active bookmakers: {active_bookmakers}")


def test_bookmaker_config():
    """Test bookmaker-specific configuration access."""
    print("\n" + "="*60)
    print("TESTING BOOKMAKER CONFIGURATION")
    print("="*60)
    
    # Test if specific bookmakers are enabled
    bet365_enabled = is_bookmaker_enabled('bet365')
    print(f"Bet365 enabled: {bet365_enabled}")
    
    # Get specific bookmaker configuration
    bet365_config = get_config('bookmakers.bet365', {})
    print(f"\nBet365 configuration:")
    print(f"  - Type: {bet365_config.get('type')}")
    print(f"  - Sports: {bet365_config.get('sports', [])}")
    print(f"  - Currency: {bet365_config.get('currency')}")
    print(f"  - Max stake: {bet365_config.get('max_stake_per_bet')}")


def test_risk_configuration():
    """Test risk-related configuration access."""
    print("\n" + "="*60)
    print("TESTING RISK CONFIGURATION")
    print("="*60)
    
    risk_config = get_risk_limits()
    print(f"Risk configuration: {risk_config}")
    
    # Test accessing specific risk parameters
    max_stake = get_config('user.risk.max_stake')
    risk_percentage = get_config('user.risk.risk_percentage')
    min_odds = get_config('user.risk.min_odds')
    max_odds = get_config('user.risk.max_odds')
    
    print(f"\nRisk Parameters:")
    print(f"  - Max stake: {max_stake}")
    print(f"  - Risk percentage: {risk_percentage}%")
    print(f"  - Min odds: {min_odds}")
    print(f"  - Max odds: {max_odds}")


def test_system_configuration():
    """Test system configuration access."""
    print("\n" + "="*60)
    print("TESTING SYSTEM CONFIGURATION")
    print("="*60)
    
    # Test scan intervals
    scan_intervals = get_scan_intervals()
    print(f"Scan intervals: {scan_intervals}")
    
    # Test VLM configuration
    vlm_config = get_config('system.vlm')
    print(f"\nVLM Configuration:")
    print(f"  - Enabled: {vlm_config.get('enabled')}")
    print(f"  - Endpoint: {vlm_config.get('endpoint')}")
    print(f"  - Timeout: {vlm_config.get('timeout')} seconds")
    
    # Test performance settings
    performance_config = get_config('system.performance')
    max_scans = performance_config.get('max_concurrent_scans')
    print(f"\nPerformance Settings:")
    print(f"  - Max concurrent scans: {max_scans}")
    print(f"  - Thread pool size: {performance_config.get('thread_pool_size')}")


def test_notification_configuration():
    """Test notification configuration access."""
    print("\n" + "="*60)
    print("TESTING NOTIFICATION CONFIGURATION")
    print("="*60)
    
    notification_config = get_notification_config()
    print(f"Notification channels configured: {list(notification_config.keys())}")
    
    # Test email configuration
    email_config = get_config('notifications.email')
    print(f"\nEmail notifications:")
    print(f"  - Enabled: {email_config.get('enabled')}")
    print(f"  - SMTP server: {email_config.get('smtp_server')}")
    print(f"  - SMTP port: {email_config.get('smtp_port')}")
    
    # Test notification triggers
    triggers = get_config('notifications.triggers')
    print(f"\nNotification triggers:")
    print(f"  - Min profit margin: {triggers.get('min_profit_margin')}")
    print(f"  - Max opportunities per hour: {triggers.get('max_opportunities_per_hour')}")
    print(f"  - Enable opportunity alerts: {triggers.get('enable_opportunity_alerts')}")


def test_logging_configuration():
    """Test logging configuration access."""
    print("\n" + "="*60)
    print("TESTING LOGGING CONFIGURATION")
    print("="*60)
    
    logging_config = get_logging_config()
    print(f"Logging configuration:")
    print(f"  - Level: {logging_config.get('level')}")
    print(f"  - Log file: {logging_config.get('file')}")
    print(f"  - Console logging: {logging_config.get('console')}")
    print(f"  - Max file size: {logging_config.get('max_file_size')} bytes")
    print(f"  - Backup count: {logging_config.get('backup_count')}")


def test_environment_variable_overrides():
    """Test environment variable overrides."""
    print("\n" + "="*60)
    print("TESTING ENVIRONMENT VARIABLE OVERRIDES")
    print("="*60)
    
    # Set some environment variables
    os.environ['ARBITECH_USER__RISK__MAX_STAKE'] = '2000.0'
    os.environ['ARBITECH_SYSTEM__PERFORMANCE__MAX_CONCURRENT_SCANS'] = '15'
    os.environ['ARBITECH_NOTIFICATIONS__EMAIL__ENABLED'] = 'true'
    
    # Reload configuration to apply environment overrides
    reload_config()
    
    # Check if overrides were applied
    max_stake = get_config('user.risk.max_stake')
    max_scans = get_config('system.performance.max_concurrent_scans')
    email_enabled = get_config('notifications.email.enabled')
    
    print(f"\nEnvironment variable overrides applied:")
    print(f"  - Max stake (from env): {max_stake}")
    print(f"  - Max concurrent scans (from env): {max_scans}")
    print(f"  - Email enabled (from env): {email_enabled}")
    
    # Clean up
    del os.environ['ARBITECH_USER__RISK__MAX_STAKE']
    del os.environ['ARBITECH_SYSTEM__PERFORMANCE__MAX_CONCURRENT_SCANS']
    del os.environ['ARBITECH_NOTIFICATIONS__EMAIL__ENABLED']


def test_configuration_modification():
    """Test runtime configuration modification."""
    print("\n" + "="*60)
    print("TESTING RUNTIME CONFIGURATION MODIFICATION")
    print("="*60)
    
    # Get current value
    original_max_stake = get_config('user.risk.max_stake')
    print(f"Original max stake: {original_max_stake}")
    
    # Modify configuration
    new_max_stake = 1500.0
    set_config('user.risk.max_stake', new_max_stake)
    
    # Verify change
    updated_max_stake = get_config('user.risk.max_stake')
    print(f"Updated max stake: {updated_max_stake}")
    
    # Restore original value
    set_config('user.risk.max_stake', original_max_stake)
    restored_max_stake = get_config('user.risk.max_stake')
    print(f"Restored max stake: {restored_max_stake}")


def test_callback_registration():
    """Test configuration change callbacks."""
    print("\n" + "="*60)
    print("TESTING CONFIGURATION CHANGE CALLBACKS")
    print("="*60)
    
    # Global variable to track callback invocations
    callback_count = 0
    
    def config_change_callback(old_config, new_config):
        nonlocal callback_count
        callback_count += 1
        old_max_stake = old_config.get('user', {}).get('risk', {}).get('max_stake')
        new_max_stake = new_config.get('user', {}).get('risk', {}).get('max_stake')
        print(f"\nCallback #{callback_count}: Max stake changed from {old_max_stake} to {new_max_stake}")
    
    # Register callback
    from core.config_manager import get_config_manager
    manager = get_config_manager()
    manager.register_callback(config_change_callback)
    
    # Make some configuration changes
    set_config('user.risk.max_stake', 1234.0)
    set_config('user.risk.risk_percentage', 3.5)
    
    print(f"Total callbacks triggered: {callback_count}")
    
    # Unregister callback
    manager.unregister_callback(config_change_callback)


def test_configuration_validation():
    """Test configuration validation."""
    print("\n" + "="*60)
    print("TESTING CONFIGURATION VALIDATION")
    print("="*60)
    
    try:
        # Test valid configuration
        valid_config = {
            'user': {'risk': {'max_stake': 1000, 'risk_percentage': 2.0}},
            'system': {'scan_intervals': {'general_scan': 60}},
            'bookmakers': {'test_bookmaker': {'enabled': True, 'api_key': 'test'}},
            'notifications': {'email': {'enabled': False}},
            'logging': {'level': 'INFO'}
        }
        
        from core.config_manager import ConfigManager
        manager = ConfigManager(config_path="test_config.yaml")
        manager._config = valid_config
        manager._validate_config()
        print("✓ Valid configuration passed validation")
        
        # Test invalid configuration
        invalid_config = {
            'user': {'risk': {'max_stake': -100}},  # Invalid: negative stake
            'system': {},
            'bookmakers': {},
            'notifications': {},
            'logging': {'level': 'INVALID'}
        }
        
        manager._config = invalid_config
        try:
            manager._validate_config()
            print("✗ Invalid configuration should have failed validation")
        except ConfigError as e:
            print(f"✓ Invalid configuration correctly failed validation: {e}")
    
    except Exception as e:
        print(f"Configuration validation test failed: {e}")


def main():
    """Run all configuration tests."""
    print("Arbitech Configuration Management System Test")
    print("=" * 60)
    
    setup_logging()
    
    try:
        # Initialize configuration
        print("\nInitializing configuration...")
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        init_config(config_path=config_path)
        print(f"✓ Configuration loaded from: {config_path}")
        
        # Run tests
        test_basic_config_access()
        test_bookmaker_config()
        test_risk_configuration()
        test_system_configuration()
        test_notification_configuration()
        test_logging_configuration()
        test_environment_variable_overrides()
        test_configuration_modification()
        test_callback_registration()
        test_configuration_validation()
        
        print("\n" + "="*60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except ConfigError as e:
        print(f"\n❌ Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
