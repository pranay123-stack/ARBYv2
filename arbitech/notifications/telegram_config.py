"""
Configuration module for ARBitech Telegram Bot

This module contains all configuration settings for the Telegram bot integration,
including bot settings, rate limiting, notification preferences, and integration options.

Author: ARBitech Development Team
Version: 1.0.0
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class BotMode(Enum):
    """Bot operation modes"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    
    # Bot Settings
    bot_token: str
    mode: BotMode = BotMode.PRODUCTION
    webhook_url: str = ""
    
    # API Settings
    api_timeout: int = 30
    api_retries: int = 3
    api_backoff_factor: float = 1.5
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    default_rate_limit: int = 10  # requests per minute
    burst_limit: int = 20  # burst requests
    
    # Notification Settings
    max_notifications_per_minute: int = 30
    notification_timeout: int = 10
    batch_notifications: bool = True
    batch_size: int = 5
    batch_timeout: float = 2.0
    
    # Security
    require_authentication: bool = True
    admin_codes: List[str] = None
    allowed_user_ids: List[int] = None
    blocked_user_ids: List[int] = None
    
    # Integration
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "/workspace/arbitech/logs/telegram_bot.log"
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    
    # Performance
    max_concurrent_notifications: int = 10
    notification_queue_size: int = 1000
    cleanup_interval: int = 3600  # seconds
    
    def __post_init__(self):
        if self.admin_codes is None:
            self.admin_codes = ["ADMIN2024", "TRADER2024", "VIEW2024"]
        if self.allowed_user_ids is None:
            self.allowed_user_ids = []
        if self.blocked_user_ids is None:
            self.blocked_user_ids = []


@dataclass
class NotificationConfig:
    """Notification delivery configuration"""
    
    # Enabled channels
    telegram_enabled: bool = True
    email_enabled: bool = False
    sms_enabled: bool = False
    slack_enabled: bool = False
    discord_enabled: bool = False
    
    # Telegram-specific settings
    telegram_parse_mode: str = "Markdown"
    telegram_disable_web_page_preview: bool = True
    telegram_disable_notification: bool = False
    
    # Message formatting
    use_emojis: bool = True
    compact_mode: bool = False
    include_timestamp: bool = True
    include_user_context: bool = True
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    
    # Filtering
    min_profit_threshold: float = 1.0
    max_stake_threshold: float = 10000.0
    allowed_risk_tiers: List[str] = None
    allowed_sports: List[str] = None
    
    def __post_init__(self):
        if self.allowed_risk_tiers is None:
            self.allowed_risk_tiers = ["TIER_A", "TIER_B"]
        if self.allowed_sports is None:
            self.allowed_sports = []


@dataclass
class FeatureConfig:
    """Feature toggles for the bot"""
    
    # Core features
    enable_opportunity_notifications: bool = True
    enable_trade_approvals: bool = True
    enable_performance_reports: bool = True
    enable_system_monitoring: bool = True
    
    # Interactive features
    enable_inline_keyboards: bool = True
    enable_conversation_handlers: bool = True
    enable_callback_queries: bool = True
    
    # Multimedia features
    enable_charts: bool = True
    enable_screenshots: bool = True
    enable_screenshots_notifications: bool = False  # Often too large
    
    # Advanced features
    enable_auto_approval: bool = False
    enable_batch_operations: bool = True
    enable_user_preferences: bool = True
    enable_multi_user_support: bool = True
    
    # Integration features
    enable_hitl_integration: bool = True
    enable_risk_monitoring: bool = True
    enable_audit_logging: bool = True
    enable_real_time_updates: bool = True
    
    # Debug features
    enable_debug_mode: bool = False
    enable_test_commands: bool = False
    enable_performance_metrics: bool = True


@dataclass
class IntegrationConfig:
    """External system integration configuration"""
    
    # Supabase integration
    supabase_enabled: bool = True
    supabase_realtime_enabled: bool = True
    supabase_sync_interval: int = 5  # seconds
    
    # HITL integration
    hitl_enabled: bool = True
    hitl_timeout: int = 300  # 5 minutes
    hitl_auto_approval: bool = False
    
    # Risk management integration
    risk_enabled: bool = True
    risk_check_interval: int = 30  # seconds
    risk_alert_threshold: float = 0.8
    
    # Scanner integration
    scanner_enabled: bool = True
    scanner_check_interval: int = 10  # seconds
    scanner_batch_size: int = 20
    
    # Performance monitoring
    performance_enabled: bool = True
    performance_interval: int = 60  # seconds
    performance_metrics: List[str] = None
    
    # Audit logging
    audit_enabled: bool = True
    audit_level: str = "INFO"
    audit_include_user_data: bool = True
    
    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = [
                "total_trades",
                "win_rate",
                "profit_loss",
                "average_stake",
                "execution_time"
            ]


# Default configurations
DEFAULT_TELEGRAM_CONFIG = TelegramConfig(
    bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
    mode=BotMode.PRODUCTION
)

DEFAULT_NOTIFICATION_CONFIG = NotificationConfig()

DEFAULT_FEATURE_CONFIG = FeatureConfig()

DEFAULT_INTEGRATION_CONFIG = IntegrationConfig()


# Configuration loader
class ConfigLoader:
    """Load configuration from environment variables and files"""
    
    @staticmethod
    def load_from_env() -> TelegramConfig:
        """Load configuration from environment variables"""
        config = TelegramConfig(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            mode=BotMode(os.getenv("BOT_MODE", "production")),
            webhook_url=os.getenv("TELEGRAM_WEBHOOK_URL", ""),
            api_timeout=int(os.getenv("API_TIMEOUT", "30")),
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
            supabase_service_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "/workspace/arbitech/logs/telegram_bot.log")
        )
        
        # Load admin codes
        admin_codes = os.getenv("ADMIN_CODES", "ADMIN2024,TRADER2024,VIEW2024")
        config.admin_codes = [code.strip() for code in admin_codes.split(",")]
        
        # Load allowed/blocked user IDs
        allowed_users = os.getenv("ALLOWED_USER_IDS", "")
        if allowed_users:
            config.allowed_user_ids = [int(uid) for uid in allowed_users.split(",")]
        
        blocked_users = os.getenv("BLOCKED_USER_IDS", "")
        if blocked_users:
            config.blocked_user_ids = [int(uid) for uid in blocked_users.split(",")]
        
        return config
    
    @staticmethod
    def load_notification_config() -> NotificationConfig:
        """Load notification configuration from environment"""
        config = NotificationConfig(
            telegram_enabled=os.getenv("TELEGRAM_ENABLED", "true").lower() == "true",
            email_enabled=os.getenv("EMAIL_ENABLED", "false").lower() == "true",
            sms_enabled=os.getenv("SMS_ENABLED", "false").lower() == "true",
            slack_enabled=os.getenv("SLACK_ENABLED", "false").lower() == "true",
            discord_enabled=os.getenv("DISCORD_ENABLED", "false").lower() == "true",
            max_notifications_per_minute=int(os.getenv("MAX_NOTIFICATIONS_PER_MINUTE", "30")),
            min_profit_threshold=float(os.getenv("MIN_PROFIT_THRESHOLD", "1.0")),
            max_stake_threshold=float(os.getenv("MAX_STAKE_THRESHOLD", "10000.0")),
            enable_charts=os.getenv("ENABLE_CHARTS", "true").lower() == "true"
        )
        
        # Load risk tiers
        risk_tiers = os.getenv("ALLOWED_RISK_TIERS", "TIER_A,TIER_B")
        config.allowed_risk_tiers = [tier.strip() for tier in risk_tiers.split(",")]
        
        # Load sports
        sports = os.getenv("ALLOWED_SPORTS", "")
        if sports:
            config.allowed_sports = [sport.strip() for sport in sports.split(",")]
        
        return config
    
    @staticmethod
    def load_feature_config() -> FeatureConfig:
        """Load feature configuration from environment"""
        return FeatureConfig(
            enable_opportunity_notifications=os.getenv("ENABLE_OPPORTUNITY_NOTIFICATIONS", "true").lower() == "true",
            enable_trade_approvals=os.getenv("ENABLE_TRADE_APPROVALS", "true").lower() == "true",
            enable_performance_reports=os.getenv("ENABLE_PERFORMANCE_REPORTS", "true").lower() == "true",
            enable_system_monitoring=os.getenv("ENABLE_SYSTEM_MONITORING", "true").lower() == "true",
            enable_inline_keyboards=os.getenv("ENABLE_INLINE_KEYBOARDS", "true").lower() == "true",
            enable_conversation_handlers=os.getenv("ENABLE_CONVERSATION_HANDLERS", "true").lower() == "true",
            enable_charts=os.getenv("ENABLE_CHARTS", "true").lower() == "true",
            enable_screenshots=os.getenv("ENABLE_SCREENSHOTS", "true").lower() == "true",
            enable_auto_approval=os.getenv("ENABLE_AUTO_APPROVAL", "false").lower() == "true",
            enable_hitl_integration=os.getenv("ENABLE_HITL_INTEGRATION", "true").lower() == "true",
            enable_risk_monitoring=os.getenv("ENABLE_RISK_MONITORING", "true").lower() == "true",
            enable_debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
            enable_test_commands=os.getenv("ENABLE_TEST_COMMANDS", "false").lower() == "true"
        )
    
    @staticmethod
    def load_integration_config() -> IntegrationConfig:
        """Load integration configuration from environment"""
        return IntegrationConfig(
            supabase_enabled=os.getenv("SUPABASE_ENABLED", "true").lower() == "true",
            supabase_realtime_enabled=os.getenv("SUPABASE_REALTIME_ENABLED", "true").lower() == "true",
            supabase_sync_interval=int(os.getenv("SUPABASE_SYNC_INTERVAL", "5")),
            hitl_enabled=os.getenv("HITL_ENABLED", "true").lower() == "true",
            hitl_timeout=int(os.getenv("HITL_TIMEOUT", "300")),
            risk_enabled=os.getenv("RISK_ENABLED", "true").lower() == "true",
            risk_check_interval=int(os.getenv("RISK_CHECK_INTERVAL", "30")),
            scanner_enabled=os.getenv("SCANNER_ENABLED", "true").lower() == "true",
            performance_enabled=os.getenv("PERFORMANCE_ENABLED", "true").lower() == "true",
            audit_enabled=os.getenv("AUDIT_ENABLED", "true").lower() == "true"
        )


# Configuration validation
class ConfigValidator:
    """Validate configuration settings"""
    
    @staticmethod
    def validate_telegram_config(config: TelegramConfig) -> List[str]:
        """Validate Telegram configuration and return list of errors"""
        errors = []
        
        if not config.bot_token:
            errors.append("Bot token is required")
        
        if not config.bot_token.startswith(('1', '2')):
            errors.append("Bot token appears invalid (should start with 1 or 2)")
        
        if config.mode not in BotMode:
            errors.append(f"Invalid bot mode: {config.mode}")
        
        if not 1 <= config.api_timeout <= 120:
            errors.append("API timeout must be between 1 and 120 seconds")
        
        if not 0 < config.rate_limit_enabled or config.default_rate_limit > 100:
            errors.append("Default rate limit must be positive and reasonable (< 100)")
        
        return errors
    
    @staticmethod
    def validate_notification_config(config: NotificationConfig) -> List[str]:
        """Validate notification configuration"""
        errors = []
        
        if config.min_profit_threshold < 0:
            errors.append("Minimum profit threshold cannot be negative")
        
        if config.max_stake_threshold <= 0:
            errors.append("Maximum stake threshold must be positive")
        
        if config.max_notifications_per_minute <= 0:
            errors.append("Max notifications per minute must be positive")
        
        valid_risk_tiers = ["TIER_A", "TIER_B", "TIER_C", "TIER_D"]
        for tier in config.allowed_risk_tiers:
            if tier not in valid_risk_tiers:
                errors.append(f"Invalid risk tier: {tier}")
        
        return errors
    
    @staticmethod
    def validate_all_configs(
        telegram_config: TelegramConfig,
        notification_config: NotificationConfig,
        feature_config: FeatureConfig,
        integration_config: IntegrationConfig
    ) -> Dict[str, List[str]]:
        """Validate all configuration objects"""
        return {
            "telegram": ConfigValidator.validate_telegram_config(telegram_config),
            "notification": ConfigValidator.validate_notification_config(notification_config),
            "feature": [],  # Feature config validation would go here
            "integration": []  # Integration config validation would go here
        }


# Configuration manager
class ConfigManager:
    """Manager for all bot configurations"""
    
    def __init__(self):
        self.telegram_config = DEFAULT_TELEGRAM_CONFIG
        self.notification_config = DEFAULT_NOTIFICATION_CONFIG
        self.feature_config = DEFAULT_FEATURE_CONFIG
        self.integration_config = DEFAULT_INTEGRATION_CONFIG
    
    def load_from_environment(self) -> None:
        """Load all configurations from environment variables"""
        self.telegram_config = ConfigLoader.load_from_env()
        self.notification_config = ConfigLoader.load_notification_config()
        self.feature_config = ConfigLoader.load_feature_config()
        self.integration_config = ConfigLoader.load_integration_config()
        
        # Validate all configs
        validation_errors = ConfigValidator.validate_all_configs(
            self.telegram_config,
            self.notification_config,
            self.feature_config,
            self.integration_config
        )
        
        # Log validation errors
        for config_type, errors in validation_errors.items():
            for error in errors:
                if config_type == "telegram":
                    # Only log telegram config errors as critical
                    raise ValueError(f"Invalid {config_type} config: {error}")
    
    def save_to_file(self, filepath: str) -> None:
        """Save configuration to file"""
        import json
        from dataclasses import asdict
        
        config_data = {
            "telegram": asdict(self.telegram_config),
            "notification": asdict(self.notification_config),
            "feature": asdict(self.feature_config),
            "integration": asdict(self.integration_config)
        }
        
        # Convert enum values to strings for JSON serialization
        config_data = self._convert_enums_to_strings(config_data)
        
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_from_file(self, filepath: str) -> None:
        """Load configuration from file"""
        import json
        
        with open(filepath, 'r') as f:
            config_data = json.load(f)
        
        # Convert strings back to enums
        config_data = self._convert_strings_to_enums(config_data)
        
        # Update configs
        for config_type, config_dict in config_data.items():
            if config_type == "telegram":
                self.telegram_config = TelegramConfig(**config_dict)
            elif config_type == "notification":
                self.notification_config = NotificationConfig(**config_dict)
            elif config_type == "feature":
                self.feature_config = FeatureConfig(**config_dict)
            elif config_type == "integration":
                self.integration_config = IntegrationConfig(**config_dict)
    
    def _convert_enums_to_strings(self, data: Any) -> Any:
        """Convert enum values to strings for JSON serialization"""
        if hasattr(data, '__dict__'):
            data_dict = {}
            for key, value in data.items():
                if hasattr(value, 'value'):  # It's an enum
                    data_dict[key] = value.value
                else:
                    data_dict[key] = self._convert_enums_to_strings(value)
            return data_dict
        elif isinstance(data, list):
            return [self._convert_enums_to_strings(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._convert_enums_to_strings(value) for key, value in data.items()}
        else:
            return data
    
    def _convert_strings_to_enums(self, data: Any) -> Any:
        """Convert strings back to enums"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key == "mode" and isinstance(value, str):
                    result[key] = BotMode(value)
                else:
                    result[key] = self._convert_strings_to_enums(value)
            return result
        elif isinstance(data, list):
            return [self._convert_strings_to_enums(item) for item in data]
        else:
            return data
    
    def get_config_summary(self) -> str:
        """Get a summary of current configuration"""
        return f"""
📋 ARBitech Telegram Bot Configuration

🔧 Telegram Settings:
• Mode: {self.telegram_config.mode.value}
• Token: {"✅ Set" if self.telegram_config.bot_token else "❌ Missing"}
• Rate Limiting: {"✅ Enabled" if self.telegram_config.rate_limit_enabled else "❌ Disabled"}

📱 Notification Settings:
• Telegram: {"✅ Enabled" if self.notification_config.telegram_enabled else "❌ Disabled"}
• Max/minute: {self.notification_config.max_notifications_per_minute}
• Min profit: {self.notification_config.min_profit_threshold}%
• Max stake: ${self.notification_config.max_stake_threshold:,.2f}

🎛️ Features:
• Opportunity Notifications: {"✅" if self.feature_config.enable_opportunity_notifications else "❌"}
• Trade Approvals: {"✅" if self.feature_config.enable_trade_approvals else "❌"}
• Performance Reports: {"✅" if self.feature_config.enable_performance_reports else "❌"}
• Auto-approval: {"✅" if self.feature_config.enable_auto_approval else "❌"}

🔗 Integration:
• Supabase: {"✅ Enabled" if self.integration_config.supabase_enabled else "❌ Disabled"}
• HITL: {"✅ Enabled" if self.integration_config.hitl_enabled else "❌ Disabled"}
• Risk Monitoring: {"✅ Enabled" if self.integration_config.risk_enabled else "❌ Disabled"}
• Audit Logging: {"✅ Enabled" if self.integration_config.audit_enabled else "❌ Disabled"}
        """


# Global configuration manager instance
config_manager = ConfigManager()
