"""
Configuration Examples for Multi-Channel Delivery Orchestrator

This file provides example configurations for setting up the multi-channel
delivery orchestrator with different channels and settings.
"""

from typing import Dict, Any
from notifications import ChannelType, DEFAULT_CHANNELS, DEFAULT_CONFIG

# Example 1: Basic Development Setup
BASIC_CONFIG = {
    "channels": {
        "telegram": {
            "bot_token": "your_telegram_bot_token_here",
            "max_retries": 2,
            "retry_base_delay": 1.0
        },
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "your_email@gmail.com",
            "password": "your_app_password",
            "from_email": "notifications@yourdomain.com",
            "max_retries": 2,
            "retry_base_delay": 2.0
        }
    },
    "worker_threads": 2,
    "batch_size": 20,
    "batch_interval": 180,
    "max_queue_size": 5000,
    "enable_analytics": True,
    "analytics_db_path": "/workspace/arbitech/logs/delivery_analytics.db"
}

# Example 2: Production Setup with All Channels
PRODUCTION_CONFIG = {
    "channels": {
        "telegram": {
            "bot_token": "1234567890:ABCdefGHIjklMNOpqrSTUVwxyz",
            "max_retries": 3,
            "retry_base_delay": 1.0,
            "parse_mode": "Markdown"
        },
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "notifications@arbitech.com",
            "password": "secure_app_password",
            "from_email": "ARBitech Notifications <notifications@arbitech.com>",
            "max_retries": 2,
            "retry_base_delay": 3.0,
            "use_tls": True
        },
        "dashboard": {
            "api_endpoint": "https://dashboard.arbitech.com/api/notifications",
            "api_key": "your_dashboard_api_key",
            "max_retries": 1,
            "retry_base_delay": 0.5,
            "timeout": 15
        },
        "sms": {
            "provider": "twilio",
            "account_sid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "auth_token": "your_twilio_auth_token",
            "from_number": "+1234567890",
            "max_retries": 2,
            "retry_base_delay": 10.0,
            "timeout": 30
        },
        "webhook": {
            "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
            "timeout": 10,
            "max_retries": 3,
            "retry_base_delay": 2.0,
            "headers": {"Content-Type": "application/json"}
        }
    },
    "worker_threads": 6,
    "batch_size": 100,
    "batch_interval": 600,  # 10 minutes
    "max_queue_size": 50000,
    "enable_analytics": True,
    "analytics_db_path": "/workspace/arbitech/logs/production_analytics.db",
    "emergency_escalation": {
        "enabled": True,
        "min_criticality_score": 10.0,
        "max_parallel_channels": 3,
        "timeout_per_channel": 60
    }
}

# Example 3: High-Frequency Trading Setup (Ultra-responsive)
HFT_CONFIG = {
    "channels": {
        "telegram": {
            "bot_token": "your_hft_telegram_bot_token",
            "max_retries": 5,
            "retry_base_delay": 0.5,  # Fast retry for urgent opportunities
            "priority_queue": True
        },
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "hft@arbitech.com",
            "password": "hft_secure_password",
            "from_email": "HFT Alerts <hft@arbitech.com>",
            "max_retries": 3,
            "retry_base_delay": 1.0
        },
        "sms": {
            "provider": "twilio",
            "account_sid": "AC_ultra_secure_hft",
            "auth_token": "hft_sms_token",
            "from_number": "+1888777666",
            "max_retries": 1,  # Quick failover for SMS
            "retry_delay": 2.0
        }
    },
    "worker_threads": 12,  # More workers for high frequency
    "batch_size": 10,  # Small batches for quick processing
    "batch_interval": 30,  # Frequent batch processing
    "max_queue_size": 100000,
    "enable_analytics": True,
    "analytics_db_path": "/workspace/arbitech/logs/hft_analytics.db",
    "priority_handling": {
        "critical_queue_size": 1000,
        "high_queue_size": 5000,
        "medium_queue_size": 20000,
        "low_queue_size": 50000,
        "batch_queue_size": 10000
    },
    "performance_optimizations": {
        "async_batch_size": 50,
        "connection_pooling": True,
        "cache_user_preferences": True,
        "preload_channel_configs": True
    }
}

# Example 4: Test/Development Setup with Mock Channels
TEST_CONFIG = {
    "channels": {
        "telegram": {
            "bot_token": "test_token",
            "mock_mode": True,
            "max_retries": 1,
            "retry_base_delay": 0.1
        },
        "email": {
            "smtp_server": "localhost",
            "smtp_port": 1025,
            "username": "test",
            "password": "test",
            "from_email": "test@arbitech.com",
            "mock_mode": True,
            "max_retries": 1
        },
        "dashboard": {
            "api_endpoint": "http://localhost:3000/api/notifications",
            "mock_mode": True,
            "max_retries": 1,
            "retry_base_delay": 0.1
        },
        "sms": {
            "provider": "mock",
            "mock_mode": True,
            "max_retries": 1,
            "retry_base_delay": 0.1
        }
    },
    "worker_threads": 1,
    "batch_size": 5,
    "batch_interval": 10,
    "max_queue_size": 1000,
    "enable_analytics": True,
    "analytics_db_path": "/tmp/test_analytics.db",
    "test_mode": True,
    "log_level": "DEBUG"
}

# User Preference Examples
USER_PREFERENCES_EXAMPLES = {
    "power_trader": {
        "preferred_channels": [ChannelType.TELEGRAM, ChannelType.SMS],
        "backup_channels": [ChannelType.EMAIL, ChannelType.DASHBOARD],
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "06:00",
        "timezone": "America/New_York",
        "language": "en",
        "emergency_override": True
    },
    "casual_investor": {
        "preferred_channels": [ChannelType.EMAIL, ChannelType.DASHBOARD],
        "backup_channels": [ChannelType.TELEGRAM],
        "quiet_hours_start": "20:00",
        "quiet_hours_end": "08:00",
        "timezone": "America/Los_Angeles",
        "language": "en",
        "emergency_override": False
    },
    "high_frequency_trader": {
        "preferred_channels": [ChannelType.SMS, ChannelType.TELEGRAM, ChannelType.WEBHOOK],
        "backup_channels": [ChannelType.EMAIL],
        "quiet_hours_start": None,  # No quiet hours
        "quiet_hours_end": None,
        "timezone": "UTC",
        "language": "en",
        "emergency_override": True
    },
    "conservative_user": {
        "preferred_channels": [ChannelType.EMAIL],
        "backup_channels": [ChannelType.DASHBOARD],
        "quiet_hours_start": "21:00",
        "quiet_hours_end": "07:00",
        "timezone": "Europe/London",
        "language": "en",
        "emergency_override": False
    }
}

# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    "development": TEST_CONFIG,
    "staging": BASIC_CONFIG,
    "production": PRODUCTION_CONFIG,
    "hft": HFT_CONFIG
}

# Configuration validation rules
CONFIG_VALIDATION_RULES = {
    "required_fields": [
        "channels",
        "worker_threads",
        "batch_size",
        "batch_interval",
        "max_queue_size"
    ],
    "channel_specific": {
        "telegram": ["bot_token"],
        "email": ["smtp_server", "username", "password", "from_email"],
        "sms": ["provider"],
        "dashboard": ["api_endpoint"],
        "webhook": ["url"]
    },
    "value_constraints": {
        "worker_threads": {"min": 1, "max": 20},
        "batch_size": {"min": 1, "max": 1000},
        "batch_interval": {"min": 1, "max": 3600},
        "max_queue_size": {"min": 100, "max": 1000000}
    }
}

def validate_config(config: Dict[str, Any]) -> tuple[bool, list]:
    """
    Validate notification configuration.
    
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields
    for field in CONFIG_VALIDATION_RULES["required_fields"]:
        if field not in config:
            errors.append(f"Missing required field: {field}")
    
    # Check channel-specific requirements
    for channel_name, channel_config in config.get("channels", {}).items():
        if channel_name in CONFIG_VALIDATION_RULES["channel_specific"]:
            for required_field in CONFIG_VALIDATION_RULES["channel_specific"][channel_name]:
                if required_field not in channel_config:
                    errors.append(f"Channel {channel_name} missing required field: {required_field}")
    
    # Check value constraints
    constraints = CONFIG_VALIDATION_RULES["value_constraints"]
    for field, constraint in constraints.items():
        if field in config:
            value = config[field]
            if "min" in constraint and value < constraint["min"]:
                errors.append(f"Field {field} value {value} below minimum {constraint['min']}")
            if "max" in constraint and value > constraint["max"]:
                errors.append(f"Field {field} value {value} above maximum {constraint['max']}")
    
    return len(errors) == 0, errors

def get_config_for_environment(env: str) -> Dict[str, Any]:
    """Get configuration for specific environment."""
    if env not in ENVIRONMENT_CONFIGS:
        raise ValueError(f"Unknown environment: {env}. Available: {list(ENVIRONMENT_CONFIGS.keys())}")
    
    config = ENVIRONMENT_CONFIGS[env].copy()
    
    # Validate configuration
    is_valid, errors = validate_config(config)
    if not is_valid:
        raise ValueError(f"Configuration validation failed: {errors}")
    
    return config

def get_user_preferences(profile: str) -> Dict[str, Any]:
    """Get user preferences for specific profile."""
    if profile not in USER_PREFERENCES_EXAMPLES:
        raise ValueError(f"Unknown user profile: {profile}. Available: {list(USER_PREFERENCES_EXAMPLES.keys())}")
    
    return USER_PREFERENCES_EXAMPLES[profile]