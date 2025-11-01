"""
ARBitech Notifications Module

Comprehensive notification system with intelligent filtering, multi-channel delivery orchestration,
intelligent routing, priority handling, failover mechanisms, analytics tracking, and now
Telegram bot integration for real-time trading notifications.

Components:
1. Telegram Bot Integration (telegram_bot.py):
   - Real-time arbitrage opportunity notifications
   - Interactive trade approval workflows
   - Performance analytics with charts
   - Multi-user authentication and role management
   - System monitoring and health checks
   - Rate limiting and error handling
   - Integration with ARBitech Phases 3-8

2. Multi-Channel Delivery System (multi_channel_delivery.py):
   - Multi-channel delivery (Telegram, Email, Dashboard, SMS, Webhook, Slack, Discord)
   - Intelligent channel selection based on urgency and user preferences
   - Delivery confirmation and retry mechanisms with exponential backoff
   - Failover between channels for critical notifications
   - Priority-based queue management with batch processing
   - Delivery analytics and performance tracking
   - Emergency notification escalation protocols

3. Notification Filtering System (notification_filters.py):
   - Multi-criteria filtering (profit thresholds, risk tiers, sports, bookmakers, times)
   - User-defined notification preferences with granular controls
   - Machine learning-based relevance scoring (TF-IDF)
   - Notification deduplication and grouping
   - Quiet hours and time-based filtering
   - Custom alert rules with complex logic
   - Notification history and analytics
   - Notification importance levels and escalation rules
   - Integration with Supabase user profiles and preferences

Classes:
Telegram Bot:
- ARBITechTelegramBot: Main bot implementation
- create_arbitech_bot: Factory function for bot creation
- BotNotification: Notification data structure
- UserSession: User session management
- config_manager: Configuration management

Delivery System:
- MultiChannelDeliveryOrchestrator: Main orchestrator for notification delivery
- ChannelSelector: Intelligent channel selection logic
- DeliveryQueue: Priority-based notification queue
- BatchProcessor: Batch delivery for non-urgent notifications
- AnalyticsTracker: Performance tracking and analytics
- NotificationRequest: Data structure for notification requests
- UserPreferences: User notification preferences
- DeliveryMetrics: Metrics for tracking delivery performance

Filtering System:
- NotificationFilterEngine: Core filtering and preferences engine
- UserPreferences (filtering): User notification preferences for filtering
- NotificationFilter: Composite notification filter with multiple conditions
- FilterCondition: Represents a single filter condition
- RelevanceScorer: Abstract base class for relevance scoring
- TfidfRelevanceScorer: TF-IDF based relevance scorer
- NotificationDeduplicator: Handles deduplication and grouping
- TimeFilter: Time-based filtering including quiet hours
- CustomRuleEngine: Custom alert rules evaluation
- EscalationManager: Notification escalation rules
- NotificationAnalytics: Analytics and performance tracking

Enums:
Telegram Bot:
- UserRole, BotState, MessageType: Bot-related enums
- NotificationType, NotificationPriority: Notification enums

Delivery System:
- DeliveryStatus, ChannelType, UrgencyLevel: Delivery system enums

Filtering System:
- FilterOperator: Supported filter operators

Integration:
The bot, filtering, and delivery systems work together - use the bot for real-time
Telegram interactions, the filtering system to process and filter notifications,
and the delivery system to send them through multiple channels.
"""

__version__ = "1.0.0"

# Import Telegram bot components
from .telegram_bot import (
    # Main bot class
    ARBITechTelegramBot,
    
    # Factory function
    create_arbitech_bot,
    
    # Data structures
    BotNotification,
    UserSession,
    RateLimitEntry,
    
    # Enums
    UserRole,
    BotState,
    MessageType,
    
    # Configuration
    config_manager,
    TelegramConfig,
    NotificationConfig,
    FeatureConfig,
    IntegrationConfig,
    
    # Helper functions
    DEFAULT_TELEGRAM_CONFIG,
    DEFAULT_NOTIFICATION_CONFIG,
    DEFAULT_FEATURE_CONFIG,
    DEFAULT_INTEGRATION_CONFIG,
)

# Import delivery system components
from .multi_channel_delivery import (
    # Main orchestrator
    MultiChannelDeliveryOrchestrator,
    
    # Core classes
    ChannelSelector,
    DeliveryQueue,
    BatchProcessor,
    AnalyticsTracker,
    
    # Data structures
    NotificationRequest,
    UserPreferences as DeliveryUserPreferences,
    DeliveryMetrics,
    
    # Channels
    TelegramChannel,
    EmailChannel,
    DashboardChannel,
    SMSChannel,
    NotificationChannel,
    
    # Enums
    DeliveryStatus,
    ChannelType,
    UrgencyLevel,
    
    # Integration functions
    initialize_orchestrator,
    send_critical_notification,
    send_batch_notification,
    notify_arbitrage_opportunity,
    notify_risk_alert,
    process_notification_delivery,
)

# Import filtering system components
from .notification_filters import (
    # Core filtering engine
    NotificationFilterEngine,
    UserPreferences as FilterUserPreferences,
    NotificationFilter,
    FilterCondition,
    FilterOperator,
    
    # Scoring and filtering components
    RelevanceScorer,
    TfidfRelevanceScorer,
    NotificationDeduplicator,
    TimeFilter,
    CustomRuleEngine,
    
    # Management components
    EscalationManager,
    NotificationAnalytics,
    
    # Factory functions
    create_filter_engine,
    
    # Filter creation utilities
    create_profit_threshold_filter,
    create_sport_filter,
    create_bookmaker_filter,
    create_time_window_filter,
    
    # Integration helpers
    filter_opportunity_notifications,
)

# Import email notification system components
from .email_notifications import (
    # Core system
    EmailNotificationSystem,
    
    # Configuration
    SMTPConfig,
    EmailConfig,
    
    # Message structures
    EmailMessage,
    EmailRecipient,
    EmailAttachment,
    EmailQueueEntry,
    
    # Templates and rendering
    EmailTemplate,
    EmailTemplateManager,
    
    # Queue management
    EmailQueue,
    
    # User preferences
    UserEmailPreferences as EmailUserPreferences,
    UserEmailPreferencesManager,
    
    # SMTP management
    SMTPManager,
    
    # Utilities
    EmailDeliverability,
    
    # Enums
    EmailPriority,
    EmailStatus,
    
    # Predefined configurations
    SMTPConfigs,
    get_gmail_config,
    get_outlook_config,
    get_sendgrid_config,
    get_custom_config,
    
    # Demo function
    demo_email_system
)

# Import email configuration
from .email_config import (
    EmailConfig as ConfigEmailConfig,
    default_config,
    EMAIL_PROVIDER_CONFIGS
)

# Re-export storage models for convenience
from storage.models import (
    Notification,
    NotificationType,
    NotificationPriority,
    NotificationChannel as StorageNotificationChannel,
    NotificationChannelConfig,
    MessageData
)

__all__ = [
    # ===== Telegram Bot Components =====
    # Main bot
    "ARBITechTelegramBot",
    
    # Factory function
    "create_arbitech_bot",
    
    # Data structures
    "BotNotification",
    "UserSession",
    "RateLimitEntry",
    
    # Enums
    "UserRole",
    "BotState",
    "MessageType",
    
    # Configuration
    "config_manager",
    "TelegramConfig",
    "NotificationConfig",
    "FeatureConfig",
    "IntegrationConfig",
    
    # ===== Delivery System Components =====
    # Main components
    "MultiChannelDeliveryOrchestrator",
    
    # Core classes
    "ChannelSelector",
    "DeliveryQueue", 
    "BatchProcessor",
    "AnalyticsTracker",
    
    # Data structures
    "NotificationRequest",
    "DeliveryUserPreferences",
    "DeliveryMetrics",
    
    # Channels
    "NotificationChannel",
    "TelegramChannel",
    "EmailChannel", 
    "DashboardChannel",
    "SMSChannel",
    
    # Enums
    "DeliveryStatus",
    "ChannelType",
    "UrgencyLevel",
    
    # Integration functions
    "initialize_orchestrator",
    "send_critical_notification",
    "send_batch_notification", 
    "notify_arbitrage_opportunity",
    "notify_risk_alert",
    "process_notification_delivery",
    
    # ===== Filtering System Components =====
    # Core filtering engine
    "NotificationFilterEngine",
    "FilterUserPreferences",
    "NotificationFilter",
    "FilterCondition",
    "FilterOperator",
    
    # Scoring and filtering
    "RelevanceScorer",
    "TfidfRelevanceScorer",
    "NotificationDeduplicator",
    "TimeFilter",
    "CustomRuleEngine",
    
    # Management components
    "EscalationManager",
    "NotificationAnalytics",
    
    # Factory functions
    "create_filter_engine",
    
    # Filter creation utilities
    "create_profit_threshold_filter",
    "create_sport_filter",
    "create_bookmaker_filter",
    "create_time_window_filter",
    
    # Integration helpers
    "filter_opportunity_notifications",
    
    # Re-exported storage models
    "Notification",
    "NotificationType",
    "NotificationPriority",
    "StorageNotificationChannel",
    "NotificationChannelConfig",
    "MessageData",
    
    # ===== Email Notification System Components =====
    # Core system
    "EmailNotificationSystem",
    
    # Configuration
    "SMTPConfig",
    "EmailConfig",
    
    # Message structures
    "EmailMessage",
    "EmailRecipient",
    "EmailAttachment", 
    "EmailQueueEntry",
    
    # Templates and rendering
    "EmailTemplate",
    "EmailTemplateManager",
    
    # Queue management
    "EmailQueue",
    
    # User preferences
    "EmailUserPreferences",
    "UserEmailPreferencesManager",
    
    # SMTP management
    "SMTPManager",
    
    # Utilities
    "EmailDeliverability",
    
    # Enums
    "EmailPriority",
    "EmailStatus",
    
    # Predefined configurations
    "SMTPConfigs",
    "get_gmail_config",
    "get_outlook_config",
    "get_sendgrid_config",
    "get_custom_config",
    
    # Demo function
    "demo_email_system",
    
    # Configuration
    "ConfigEmailConfig",
    "default_config",
    "EMAIL_PROVIDER_CONFIGS"
]

# Quick start constants for easy configuration
DEFAULT_CHANNELS = {
    "telegram": {
        "max_retries": 3,
        "retry_base_delay": 1.0
    },
    "email": {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "max_retries": 2,
        "retry_base_delay": 2.0
    },
    "dashboard": {
        "api_endpoint": "/api/notifications",
        "max_retries": 1,
        "retry_base_delay": 0.5
    },
    "sms": {
        "provider": "twilio",
        "max_retries": 2,
        "retry_base_delay": 5.0
    },
    "webhook": {
        "timeout": 10,
        "max_retries": 3,
        "retry_base_delay": 1.0
    }
}

DEFAULT_CONFIG = {
    "channels": DEFAULT_CHANNELS,
    "worker_threads": 4,
    "batch_size": 50,
    "batch_interval": 300,
    "max_queue_size": 10000,
    "enable_analytics": True,
    "analytics_db_path": "delivery_analytics.db"
}

# ===== Telegram Bot Convenience Functions =====

async def create_telegram_bot(token: str, data_layer=None) -> ARBITechTelegramBot:
    """
    Quick start function to create and initialize Telegram bot.
    
    Args:
        token: Telegram bot token
        data_layer: Optional SupabaseDataLayer instance
        
    Returns:
        Configured ARBITechTelegramBot instance
    """
    if data_layer is None:
        from storage.supabase_layer import SupabaseDataLayer
        data_layer = SupabaseDataLayer()
    
    return create_arbitech_bot(token, data_layer)


async def run_telegram_bot_demo(token: str) -> None:
    """
    Run the complete Telegram bot demonstration.
    
    Args:
        token: Telegram bot token
    """
    from .telegram_bot_example import main as demo_main
    os.environ["TELEGRAM_BOT_TOKEN"] = token
    await demo_main()


def get_bot_config_summary() -> str:
    """
    Get configuration summary for the Telegram bot.
    
    Returns:
        Formatted configuration summary string
    """
    return config_manager.get_config_summary()


# ===== Email Notification System Convenience Functions =====

def create_email_system_gmail(username: str, app_password: str, from_name: str = "ARBitech Trading"):
    """
    Quick start function to create email system with Gmail configuration.
    
    Args:
        username: Gmail username/email
        app_password: 16-character Gmail app password
        from_name: Display name for emails
        
    Returns:
        Configured EmailNotificationSystem instance
    """
    return get_gmail_config(username, app_password, from_name)


def create_email_system_outlook(username: str, password: str, from_name: str = "ARBitech Trading"):
    """
    Quick start function to create email system with Outlook configuration.
    
    Args:
        username: Outlook email
        password: Outlook password
        from_name: Display name for emails
        
    Returns:
        Configured EmailNotificationSystem instance
    """
    return get_outlook_config(username, password, from_name)


def create_email_system_sendgrid(api_key: str, from_email: str, from_name: str = "ARBitech Trading"):
    """
    Quick start function to create email system with SendGrid configuration.
    
    Args:
        api_key: SendGrid API key
        from_email: From email address
        from_name: Display name for emails
        
    Returns:
        Configured EmailNotificationSystem instance
    """
    return get_sendgrid_config(api_key, from_email, from_name)


async def send_test_email(system: EmailNotificationSystem, test_email: str) -> bool:
    """
    Send a test email to verify system configuration.
    
    Args:
        system: EmailNotificationSystem instance
        test_email: Email address to send test to
        
    Returns:
        True if sent successfully, False otherwise
    """
    test_recipient = EmailRecipient(email=test_email, name="Test User")
    test_message = EmailMessage(
        to=[test_recipient],
        subject="ARBitech Email System Test",
        html_body="""
        <h2>Email System Test</h2>
        <p>This is a test email from the ARBitech notification system.</p>
        <p>If you receive this, your email configuration is working correctly!</p>
        """,
        text_body="This is a test email from the ARBitech notification system.\n\nIf you receive this, your email configuration is working correctly!",
        priority=EmailPriority.NORMAL
    )
    
    entry = EmailQueueEntry(
        id=f"test_email_{int(time.time())}",
        message=test_message,
        metadata={'type': 'test_email'}
    )
    
    return system.queue.add_email(entry)


def get_email_system_status(system: EmailNotificationSystem) -> dict:
    """
    Get comprehensive email system status and health information.
    
    Args:
        system: EmailNotificationSystem instance
        
    Returns:
        Dictionary with system status information
    """
    stats = system.get_queue_stats()
    
    return {
        'system_status': 'healthy' if stats['failed_count'] < 10 else 'degraded',
        'queue_stats': stats,
        'smtp_connected': system.smtp_manager._connection is not None,
        'templates_loaded': len(system.template_manager.templates),
        'processing_active': stats['processing_active']
    }


# Integration helpers for ARBitech platform
async def notify_opportunity_found(
    system: EmailNotificationSystem,
    user_id: str,
    opportunity,
    custom_message: str = None,
    include_screenshot: bool = True
) -> bool:
    """
    Convenience function to notify users of new arbitrage opportunities.
    
    Args:
        system: EmailNotificationSystem instance
        user_id: User ID to notify
        opportunity: ArbitrageOpportunity instance
        custom_message: Optional custom message
        include_screenshot: Whether to include screenshots
        
    Returns:
        True if notification queued successfully
    """
    return await system.send_opportunity_alert(
        user_id=user_id,
        opportunity=opportunity,
        custom_message=custom_message,
        include_screenshot=include_screenshot
    )


async def notify_trade_update(
    system: EmailNotificationSystem,
    user_id: str,
    trade,
    include_screenshot: bool = True
) -> bool:
    """
    Convenience function to notify users of trade status updates.
    
    Args:
        system: EmailNotificationSystem instance
        user_id: User ID to notify
        trade: Trade instance
        include_screenshot: Whether to include screenshots
        
    Returns:
        True if notification queued successfully
    """
    return await system.send_trade_update(
        user_id=user_id,
        trade=trade,
        include_screenshot=include_screenshot
    )


# Add imports needed for the convenience functions
import os