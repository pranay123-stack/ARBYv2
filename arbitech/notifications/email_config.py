"""
Email Notification Configuration for ARBitech Trading Platform

This file contains configuration settings for the email notification system.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class EmailConfig:
    """Email notification system configuration."""
    
    # SMTP Settings
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    smtp_use_ssl: bool = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    
    # Email Settings
    from_name: str = os.getenv("EMAIL_FROM_NAME", "ARBitech Trading")
    from_email: str = os.getenv("EMAIL_FROM_EMAIL", "noreply@arbitech.trading")
    reply_to: Optional[str] = os.getenv("EMAIL_REPLY_TO")
    
    # Domain and URLs
    base_url: str = os.getenv("BASE_URL", "https://app.arbitech.trading")
    tracking_domain: str = os.getenv("TRACKING_DOMAIN", "tracking.arbitech.trading")
    
    # Queue Settings
    max_queue_size: int = int(os.getenv("EMAIL_QUEUE_MAX_SIZE", "10000"))
    max_retries: int = int(os.getenv("EMAIL_MAX_RETRIES", "3"))
    retry_delay: int = int(os.getenv("EMAIL_RETRY_DELAY", "5"))
    
    # Rate Limiting
    max_emails_per_hour: int = int(os.getenv("MAX_EMAILS_PER_HOUR", "100"))
    max_emails_per_day: int = int(os.getenv("MAX_EMAILS_PER_DAY", "1000"))
    
    # Template Settings
    enable_tracking: bool = os.getenv("ENABLE_EMAIL_TRACKING", "true").lower() == "true"
    enable_click_tracking: bool = os.getenv("ENABLE_CLICK_TRACKING", "true").lower() == "true"
    default_html_format: bool = os.getenv("DEFAULT_HTML_FORMAT", "true").lower() == "true"
    
    # Notification Settings
    opportunity_alert_enabled: bool = os.getenv("ENABLE_OPPORTUNITY_ALERTS", "true").lower() == "true"
    trade_update_enabled: bool = os.getenv("ENABLE_TRADE_UPDATES", "true").lower() == "true"
    risk_warning_enabled: bool = os.getenv("ENABLE_RISK_WARNINGS", "true").lower() == "true"
    profit_report_enabled: bool = os.getenv("ENABLE_PROFIT_REPORTS", "true").lower() == "true"
    weekly_summary_enabled: bool = os.getenv("ENABLE_WEEKLY_SUMMARIES", "true").lower() == "true"
    
    # Attachments
    max_attachment_size_mb: int = int(os.getenv("MAX_ATTACHMENT_SIZE_MB", "10"))
    allowed_attachment_types: list = [
        "image/png", "image/jpeg", "image/gif",
        "application/pdf", "text/csv", "application/json"
    ]
    
    # Compliance
    enable_unsubscribe: bool = os.getenv("ENABLE_UNSUBSCRIBE", "true").lower() == "true"
    include_mailing_address: bool = os.getenv("INCLUDE_MAILING_ADDRESS", "true").lower() == "true"
    mailing_address: str = os.getenv(
        "MAILING_ADDRESS", 
        "ARBitech Trading\\n123 Trading St\\nFinancial District, NY 10001"
    )
    
    # Logging
    log_level: str = os.getenv("EMAIL_LOG_LEVEL", "INFO")
    enable_delivery_logging: bool = os.getenv("ENABLE_DELIVERY_LOGGING", "true").lower() == "true"
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        required_fields = ["smtp_host", "smtp_username", "smtp_password"]
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Required field missing: {field}")
        
        if self.smtp_port not in [25, 587, 465, 2525]:
            raise ValueError(f"Invalid SMTP port: {self.smtp_port}")
        
        if not self.from_email or "@" not in self.from_email:
            raise ValueError("Invalid from_email address")
        
        return True


# Default configuration instance
default_config = EmailConfig()

# Predefined configurations for common email providers
EMAIL_PROVIDER_CONFIGS = {
    "gmail": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_use_tls": True,
        "smtp_use_ssl": False
    },
    "outlook": {
        "smtp_host": "smtp-mail.outlook.com",
        "smtp_port": 587,
        "smtp_use_tls": True,
        "smtp_use_ssl": False
    },
    "yahoo": {
        "smtp_host": "smtp.mail.yahoo.com",
        "smtp_port": 587,
        "smtp_use_tls": True,
        "smtp_use_ssl": False
    },
    "sendgrid": {
        "smtp_host": "smtp.sendgrid.net",
        "smtp_port": 587,
        "smtp_use_tls": True,
        "smtp_use_ssl": False
    },
    "mailgun": {
        "smtp_host": "smtp.mailgun.org",
        "smtp_port": 587,
        "smtp_use_tls": True,
        "smtp_use_ssl": False
    }
}


def get_gmail_config(username: str, app_password: str, from_name: str = None) -> EmailConfig:
    """Get Gmail-specific configuration."""
    config = default_config
    config.smtp_host = "smtp.gmail.com"
    config.smtp_port = 587
    config.smtp_username = username
    config.smtp_password = app_password
    config.smtp_use_tls = True
    config.smtp_use_ssl = False
    
    if from_name:
        config.from_name = from_name
    
    return config


def get_outlook_config(username: str, password: str, from_name: str = None) -> EmailConfig:
    """Get Outlook-specific configuration."""
    config = default_config
    config.smtp_host = "smtp-mail.outlook.com"
    config.smtp_port = 587
    config.smtp_username = username
    config.smtp_password = password
    config.smtp_use_tls = True
    config.smtp_use_ssl = False
    
    if from_name:
        config.from_name = from_name
    
    return config


def get_sendgrid_config(api_key: str, from_email: str, from_name: str = None) -> EmailConfig:
    """Get SendGrid-specific configuration."""
    config = default_config
    config.smtp_host = "smtp.sendgrid.net"
    config.smtp_port = 587
    config.smtp_username = "apikey"
    config.smtp_password = api_key
    config.smtp_use_tls = True
    config.smtp_use_ssl = False
    config.from_email = from_email
    
    if from_name:
        config.from_name = from_name
    
    return config


def get_custom_config(
    host: str,
    port: int,
    username: str,
    password: str,
    use_tls: bool = True,
    use_ssl: bool = False,
    from_email: str = None,
    from_name: str = None
) -> EmailConfig:
    """Get custom SMTP configuration."""
    config = default_config
    config.smtp_host = host
    config.smtp_port = port
    config.smtp_username = username
    config.smtp_password = password
    config.smtp_use_tls = use_tls
    config.smtp_use_ssl = use_ssl
    
    if from_email:
        config.from_email = from_email
    if from_name:
        config.from_name = from_name
    
    return config