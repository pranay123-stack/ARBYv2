"""
Professional Email Notification System for ARBitech Trading Platform

This comprehensive email notification system provides:
- SMTP integration with support for Gmail, Outlook, custom SMTP servers
- Rich HTML email templates for different notification types
- HTML and plain text formatting with responsive design
- Attachment support for screenshots, reports, and documents
- Email queue system with retry mechanisms and delivery confirmation
- Personalized notifications with user preferences
- Unsubscribe links and email preference management
- Integration with Supabase data layer
- Professional deliverability and spam prevention
"""

import os
import smtplib
import ssl
import time
import asyncio
import hashlib
import base64
import mimetypes
import logging
import threading
import queue
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from email.utils import formataddr, make_msgid
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import json
import re

# Import ARBitech models and Supabase layer
from storage.models import (
    Notification, NotificationType, NotificationPriority, 
    NotificationChannel, ArbitrageOpportunity, Trade, User,
    Sport, RiskTier, TradeStatus
)
from storage.supabase_layer import get_data_layer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailPriority(str, Enum):
    """Email priority levels for proper handling."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class EmailStatus(str, Enum):
    """Email delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    EXPIRED = "expired"
    BOUNCED = "bounced"


@dataclass
class SMTPConfig:
    """SMTP server configuration."""
    host: str
    port: int
    username: str
    password: str
    use_tls: bool = True
    use_ssl: bool = False
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5
    
    def __post_init__(self):
        """Validate SMTP configuration."""
        if not self.host:
            raise ValueError("SMTP host is required")
        if not self.username:
            raise ValueError("SMTP username is required")
        if not self.password:
            raise ValueError("SMTP password is required")
        if self.port not in [25, 587, 465, 2525]:
            logger.warning(f"Non-standard SMTP port: {self.port}")


@dataclass
class EmailTemplate:
    """Email template configuration."""
    subject_template: str
    html_template: str
    text_template: str
    preview_text: str = ""
    category: str = "general"
    requires_specific_data: List[str] = field(default_factory=list)


@dataclass
class EmailRecipient:
    """Email recipient information."""
    email: str
    name: Optional[str] = None
    user_id: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


@dataclass
class EmailAttachment:
    """Email attachment data."""
    filename: str
    content: Union[bytes, str]
    content_type: Optional[str] = None
    is_inline: bool = False
    content_id: Optional[str] = None


@dataclass
class EmailMessage:
    """Complete email message."""
    to: List[EmailRecipient]
    from_name: str = "ARBitech Trading"
    from_email: str = "noreply@arbitech.trading"
    reply_to: Optional[str] = None
    subject: str = ""
    html_body: str = ""
    text_body: str = ""
    priority: EmailPriority = EmailPriority.NORMAL
    template: Optional[EmailTemplate] = None
    attachments: List[EmailAttachment] = field(default_factory=list)
    tracking_pixel: bool = True
    unsubscribe_url: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class EmailQueueEntry:
    """Email queue entry for tracking and retries."""
    id: str
    message: EmailMessage
    status: EmailStatus = EmailStatus.PENDING
    attempt_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserEmailPreferences:
    """User email notification preferences."""
    user_id: str
    email: str
    name: Optional[str] = None
    
    # Notification type preferences
    opportunity_alerts: bool = True
    trade_updates: bool = True
    risk_warnings: bool = True
    profit_reports: bool = True
    system_alerts: bool = True
    weekly_reports: bool = False
    monthly_reports: bool = True
    
    # Delivery preferences
    frequency: str = "immediate"  # immediate, hourly, daily, weekly
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "08:00"
    timezone: str = "UTC"
    
    # Content preferences
    include_screenshots: bool = True
    include_charts: bool = True
    detailed_reports: bool = True
    
    # Email format preferences
    html_emails: bool = True
    text_emails: bool = False
    
    # Marketing preferences
    marketing_emails: bool = False
    newsletter: bool = False
    
    # Compliance
    unsubscribe_token: Optional[str] = None
    unsubscribed_at: Optional[datetime] = None


class EmailDeliverability:
    """Email deliverability and spam prevention utilities."""
    
    @staticmethod
    def validate_email_address(email: str) -> bool:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def check_spam_score(text: str, html: str = "") -> Dict[str, Any]:
        """Check potential spam score of email content."""
        issues = []
        score = 0
        
        # Common spam indicators
        spam_words = [
            "free", "urgent", "click here", "act now", "limited time",
            "guaranteed", "no risk", "make money fast", "congratulations"
        ]
        
        text_lower = text.lower()
        html_lower = html.lower() if html else ""
        
        for word in spam_words:
            if word in text_lower or word in html_lower:
                issues.append(f"Contains spam word: {word}")
                score += 1
        
        # Check excessive capitalization
        if len(text) > 50:
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.3:
                issues.append("Excessive capitalization")
                score += 2
        
        # Check for multiple exclamation marks
        if "!!!" in text or "!!!" in html:
            issues.append("Multiple exclamation marks")
            score += 1
        
        # Check for URL patterns
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        if len(re.findall(url_pattern, text + html)) > 3:
            issues.append("Too many URLs")
            score += 1
        
        return {
            "score": score,
            "issues": issues,
            "risk_level": "high" if score > 3 else "medium" if score > 1 else "low"
        }
    
    @staticmethod
    def generate_tracking_pixel(user_id: str, email_id: str) -> str:
        """Generate tracking pixel URL for email open tracking."""
        # In a real implementation, this would generate a unique tracking URL
        return f"https://tracking.arbitech.trading/pixel/{user_id}/{email_id}"
    
    @staticmethod
    def generate_click_tracking_url(original_url: str, user_id: str, email_id: str) -> str:
        """Generate click tracking URL."""
        # In a real implementation, this would generate a tracked URL
        encoded_url = base64.b64encode(original_url.encode()).decode()
        return f"https://tracking.arbitech.tracking/click/{encoded_url}/{user_id}/{email_id}"


class EmailTemplateManager:
    """Manages email templates for different notification types."""
    
    def __init__(self):
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, EmailTemplate]:
        """Load email templates."""
        templates = {}
        
        # Opportunity Alert Template
        templates["opportunity_alert"] = EmailTemplate(
            subject_template="🎯 New Arbitrage Opportunity: {event_name} - {profit_margin:.1f}% Profit",
            html_template=self._get_opportunity_alert_html(),
            text_template=self._get_opportunity_alert_text(),
            preview_text="New arbitrage opportunity found with {profit_margin:.1f}% profit margin",
            category="opportunity",
            requires_specific_data=["event_name", "profit_margin", "sport", "legs"]
        )
        
        # Trade Update Template
        templates["trade_update"] = EmailTemplate(
            subject_template="📈 Trade Update: {trade_status} - {expected_profit:.2f} Expected Profit",
            html_template=self._get_trade_update_html(),
            text_template=self._get_trade_update_text(),
            preview_text="Your arbitrage trade has been updated",
            category="trading",
            requires_specific_data=["trade_status", "expected_profit", "opportunity"]
        )
        
        # Risk Warning Template
        templates["risk_warning"] = EmailTemplate(
            subject_template="⚠️ Risk Alert: {alert_title}",
            html_template=self._get_risk_warning_html(),
            text_template=self._get_risk_warning_text(),
            preview_text="Important risk alert requiring your attention",
            category="risk",
            requires_specific_data=["alert_title", "severity", "description", "risk_metrics"]
        )
        
        # Profit Report Template
        templates["profit_report"] = EmailTemplate(
            subject_template="💰 Profit Report: {period} - {total_profit:.2f} Total Profit",
            html_template=self._get_profit_report_html(),
            text_template=self._get_profit_report_text(),
            preview_text="Your trading performance report",
            category="reports",
            requires_specific_data=["period", "total_profit", "trade_summary", "performance_metrics"]
        )
        
        # Weekly Summary Template
        templates["weekly_summary"] = EmailTemplate(
            subject_template="📊 Weekly Trading Summary - {week_range}",
            html_template=self._get_weekly_summary_html(),
            text_template=self._get_weekly_summary_text(),
            preview_text="Your weekly trading performance summary",
            category="reports",
            requires_specific_data=["week_range", "trades_count", "total_profit", "top_sports"]
        )
        
        # System Alert Template
        templates["system_alert"] = EmailTemplate(
            subject_template="🔧 System Alert: {alert_type}",
            html_template=self._get_system_alert_html(),
            text_template=self._get_system_alert_text(),
            preview_text="Important system notification",
            category="system",
            requires_specific_data=["alert_type", "description", "impact", "action_required"]
        )
        
        return templates
    
    def get_template(self, template_name: str) -> Optional[EmailTemplate]:
        """Get template by name."""
        return self.templates.get(template_name)
    
    def render_template(self, template: EmailTemplate, data: Dict[str, Any]) -> Tuple[str, str]:
        """Render template with data."""
        try:
            # Render subject
            subject = template.subject_template.format(**data)
            
            # Render HTML body
            html_body = template.html_template.format(**data)
            
            # Render text body
            text_body = template.text_template.format(**data)
            
            return subject, html_body, text_body
            
        except KeyError as e:
            logger.error(f"Missing data for template rendering: {e}")
            raise ValueError(f"Missing required data for template: {e}")
    
    def _get_opportunity_alert_html(self) -> str:
        """HTML template for opportunity alerts."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Arbitrage Opportunity</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background-color: #f8f9fa; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; text-align: center; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; font-weight: 700; }}
        .header .subtitle {{ font-size: 16px; opacity: 0.9; }}
        .content {{ padding: 30px 20px; }}
        .opportunity-card {{ background: #f8f9ff; border: 2px solid #e3f2fd; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .profit-highlight {{ background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); color: white; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; }}
        .profit-amount {{ font-size: 32px; font-weight: bold; }}
        .legs-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .legs-table th, .legs-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .legs-table th {{ background-color: #f5f5f5; font-weight: 600; }}
        .bookmaker {{ font-weight: 600; color: #667eea; }}
        .odds {{ font-weight: 700; color: #4caf50; }}
        .action-buttons {{ text-align: center; margin: 30px 0; }}
        .btn {{ display: inline-block; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 0 10px; }}
        .btn-primary {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        .btn-secondary {{ background: #f8f9fa; color: #667eea; border: 2px solid #667eea; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
        .footer a {{ color: #667eea; text-decoration: none; }}
        @media (max-width: 600px) {{
            .container {{ width: 100% !important; }}
            .content {{ padding: 20px 15px !important; }}
            .legs-table {{ font-size: 14px; }}
            .profit-amount {{ font-size: 24px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 New Arbitrage Opportunity</h1>
            <div class="subtitle">High-profit betting opportunity detected</div>
        </div>
        
        <div class="content">
            <div class="opportunity-card">
                <h2 style="color: #667eea; margin-bottom: 15px;">{event_name}</h2>
                <p style="color: #666; margin-bottom: 10px;"><strong>Sport:</strong> {sport} | <strong>Market:</strong> {market_type}</p>
                <p style="color: #666; margin-bottom: 15px;"><strong>Event Date:</strong> {event_date}</p>
                
                <div class="profit-highlight">
                    <div>Expected Profit</div>
                    <div class="profit-amount">{profit_amount:.2f} {currency}</div>
                    <div style="font-size: 14px; margin-top: 5px;">{profit_margin:.1f}% Profit Margin</div>
                </div>
                
                <table class="legs-table">
                    <thead>
                        <tr>
                            <th>Bookmaker</th>
                            <th>Outcome</th>
                            <th>Odds</th>
                            <th>Stake %</th>
                        </tr>
                    </thead>
                    <tbody>
                        {legs_html}
                    </tbody>
                </table>
                
                {risk_info}
            </div>
            
            <div class="action-buttons">
                <a href="{dashboard_url}" class="btn btn-primary">View Opportunity</a>
                <a href="{unsubscribe_url}" class="btn btn-secondary">Manage Preferences</a>
            </div>
        </div>
        
        <div class="footer">
            <p>This opportunity was detected by ARBitech's advanced scanning system.</p>
            <p><a href="{dashboard_url}">Visit Dashboard</a> | <a href="{unsubscribe_url}">Unsubscribe</a></p>
            <p style="margin-top: 10px; font-size: 12px;">© 2024 ARBitech Trading Platform. All rights reserved.</p>
        </div>
    </div>
    
    {tracking_pixel}
</body>
</html>
        """
    
    def _get_opportunity_alert_text(self) -> str:
        """Text template for opportunity alerts."""
        return """
🎯 NEW ARBITRAGE OPPORTUNITY

{event_name}
Sport: {sport} | Market: {market_type}
Event Date: {event_date}

PROFIT SUMMARY:
Expected Profit: {profit_amount:.2f} {currency}
Profit Margin: {profit_margin:.1f}%

BETTING LEGS:
{legs_text}

RISK ASSESSMENT:
{risk_info}

---
Visit your dashboard to view this opportunity: {dashboard_url}

Manage your notification preferences: {unsubscribe_url}

© 2024 ARBitech Trading Platform
        """
    
    def _get_trade_update_html(self) -> str:
        """HTML template for trade updates."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trade Update</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background-color: #f8f9fa; }}
        .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; }}
        .header {{ background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); color: white; padding: 30px 20px; text-align: center; }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; font-weight: 700; }}
        .status-badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: 600; }}
        .status-filled {{ background-color: #4caf50; }}
        .status-pending {{ background-color: #ff9800; }}
        .status-failed {{ background-color: #f44336; }}
        .content {{ padding: 30px 20px; }}
        .trade-details {{ background: #f8f9ff; border: 2px solid #e3f2fd; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .profit-box {{ background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }}
        .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Trade Update</h1>
            <div class="status-badge status-{status_class}">{trade_status}</div>
        </div>
        
        <div class="content">
            <div class="trade-details">
                <h2 style="color: #4caf50; margin-bottom: 15px;">{opportunity_name}</h2>
                
                <div class="profit-box">
                    <div>Expected Profit</div>
                    <div style="font-size: 24px; font-weight: bold;">{expected_profit:.2f} {currency}</div>
                    <div>Total Stake: {total_stake:.2f} {currency}</div>
                </div>
                
                <p><strong>Execution Mode:</strong> {execution_mode}</p>
                <p><strong>Execution Time:</strong> {execution_time}ms</p>
                {actual_profit_info}
            </div>
        </div>
        
        <div class="footer">
            <p><a href="{dashboard_url}">Visit Dashboard</a> | <a href="{unsubscribe_url}">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_trade_update_text(self) -> str:
        """Text template for trade updates."""
        return """
📈 TRADE UPDATE

Status: {trade_status}
Opportunity: {opportunity_name}

Expected Profit: {expected_profit:.2f} {currency}
Total Stake: {total_stake:.2f} {currency}
Execution Mode: {execution_mode}
Execution Time: {execution_time}ms
{actual_profit_info}

---
Visit your dashboard: {dashboard_url}
Unsubscribe: {unsubscribe_url}
        """
    
    def _get_risk_warning_html(self) -> str:
        """HTML template for risk warnings."""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Risk Alert</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f44336; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: white; padding: 20px; border: 1px solid #ddd; }}
        .risk-high {{ background: #ffebee; border-left: 4px solid #f44336; }}
        .risk-medium {{ background: #fff3e0; border-left: 4px solid #ff9800; }}
        .risk-low {{ background: #e8f5e8; border-left: 4px solid #4caf50; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Risk Alert</h1>
            <p>{alert_title}</p>
        </div>
        <div class="content risk-{severity_class}">
            <p>{description}</p>
            {risk_metrics}
            {recommended_action}
        </div>
    </div>
</body>
</html>
        """
    
    def _get_risk_warning_text(self) -> str:
        """Text template for risk warnings."""
        return """
⚠️ RISK ALERT

{alert_title}

Description: {description}

Severity: {severity}
{risk_metrics}

{recommended_action}

Dashboard: {dashboard_url}
Unsubscribe: {unsubscribe_url}
        """
    
    def _get_profit_report_html(self) -> str:
        """HTML template for profit reports."""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Profit Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .header {{ background: #4caf50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .metric {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 Profit Report</h1>
            <p>{period}</p>
        </div>
        <div class="content">
            <div class="metric">
                <h3>Total Profit: {total_profit:.2f} {currency}</h3>
            </div>
            <div class="metric">
                <h3>Trades Completed: {trades_count}</h3>
                <p>Success Rate: {success_rate:.1f}%</p>
            </div>
            {performance_details}
        </div>
    </div>
</body>
</html>
        """
    
    def _get_profit_report_text(self) -> str:
        """Text template for profit reports."""
        return """
💰 PROFIT REPORT

Period: {period}

Total Profit: {total_profit:.2f} {currency}
Trades Completed: {trades_count}
Success Rate: {success_rate:.1f}%

{performance_details}

Dashboard: {dashboard_url}
Unsubscribe: {unsubscribe_url}
        """
    
    def _get_weekly_summary_html(self) -> str:
        """HTML template for weekly summaries."""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Weekly Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .summary-box {{ background: #e3f2fd; padding: 20px; margin: 20px 0; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Weekly Trading Summary</h1>
        <div class="summary-box">
            <h2>{week_range}</h2>
            <p>Total Trades: {trades_count}</p>
            <p>Total Profit: {total_profit:.2f} {currency}</p>
            <p>Best Sport: {top_sports}</p>
        </div>
    </div>
</body>
</html>
        """
    
    def _get_weekly_summary_text(self) -> str:
        """Text template for weekly summaries."""
        return """
📊 WEEKLY TRADING SUMMARY

Period: {week_range}

Total Trades: {trades_count}
Total Profit: {total_profit:.2f} {currency}
Best Performing Sport: {top_sports}

Dashboard: {dashboard_url}
Unsubscribe: {unsubscribe_url}
        """
    
    def _get_system_alert_html(self) -> str:
        """HTML template for system alerts."""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>System Alert</title>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; margin: 20px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 System Alert</h1>
        <div class="alert">
            <h2>{alert_type}</h2>
            <p>{description}</p>
            <p>Impact: {impact}</p>
            {action_required}
        </div>
    </div>
</body>
</html>
        """
    
    def _get_system_alert_text(self) -> str:
        """Text template for system alerts."""
        return """
🔧 SYSTEM ALERT

{alert_type}

Description: {description}
Impact: {impact}
{action_required}

Dashboard: {dashboard_url}
Unsubscribe: {unsubscribe_url}
        """


class SMTPManager:
    """Manages SMTP connections and email sending."""
    
    def __init__(self, config: SMTPConfig):
        self.config = config
        self._connection = None
        self._last_used = None
    
    def connect(self) -> bool:
        """Establish SMTP connection."""
        try:
            if self.config.use_ssl:
                context = ssl.create_default_context()
                self._connection = smtplib.SMTP_SSL(
                    self.config.host, 
                    self.config.port, 
                    timeout=self.config.timeout,
                    context=context
                )
            else:
                self._connection = smtplib.SMTP(
                    self.config.host, 
                    self.config.port, 
                    timeout=self.config.timeout
                )
                
                if self.config.use_tls:
                    self._connection.starttls()
            
            self._connection.login(self.config.username, self.config.password)
            self._last_used = datetime.utcnow()
            logger.info(f"SMTP connection established to {self.config.host}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to SMTP server: {e}")
            return False
    
    def send_email(self, message: EmailMessage) -> bool:
        """Send email message."""
        if not self._connection or not self._is_connection_valid():
            if not self.connect():
                return False
        
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(message.subject, 'utf-8')
            msg['From'] = formataddr((message.from_name, message.from_email))
            msg['To'] = ', '.join([formataddr((r.name or "", r.email)) for r in message.to])
            
            if message.reply_to:
                msg['Reply-To'] = message.reply_to
            
            # Add custom headers
            for header, value in message.custom_headers.items():
                msg[header] = Header(value, 'utf-8')
            
            # Add priority headers
            if message.priority != EmailPriority.NORMAL:
                msg['X-Priority'] = message.priority.value
                msg['X-MSMail-Priority'] = message.priority.value
            
            # Add tracking headers
            if message.to:
                msg['X-User-ID'] = message.to[0].user_id or ""
            
            # Add text and HTML bodies
            text_part = MIMEText(message.text_body, 'plain', 'utf-8')
            html_part = MIMEText(message.html_body, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add attachments
            for attachment in message.attachments:
                self._add_attachment(msg, attachment)
            
            # Send email
            recipients = [r.email for r in message.to]
            self._connection.send_message(msg)
            
            logger.info(f"Email sent successfully to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            self._connection = None  # Reset connection
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: EmailAttachment):
        """Add attachment to email message."""
        try:
            if attachment.is_inline:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.content if isinstance(attachment.content, bytes) else attachment.content.encode())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'inline; filename="{attachment.filename}"')
                if attachment.content_id:
                    part.add_header('Content-ID', f'<{attachment.content_id}>')
                msg.attach(part)
            else:
                with open(attachment.content, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename="{attachment.filename}"')
                    msg.attach(part)
        except Exception as e:
            logger.error(f"Failed to add attachment {attachment.filename}: {e}")
    
    def _is_connection_valid(self) -> bool:
        """Check if SMTP connection is still valid."""
        if not self._connection or not self._last_used:
            return False
        
        # Check if connection is older than 5 minutes
        age = datetime.utcnow() - self._last_used
        return age.total_seconds() < 300
    
    def disconnect(self):
        """Close SMTP connection."""
        if self._connection:
            try:
                self._connection.quit()
            except:
                pass
            finally:
                self._connection = None


class EmailQueue:
    """Manages email queue with retry mechanisms."""
    
    def __init__(self, max_size: int = 10000):
        self.queue = queue.PriorityQueue(maxsize=max_size)
        self.sent_emails = {}
        self.failed_emails = {}
        self._processing = False
        self._lock = threading.Lock()
    
    def add_email(self, entry: EmailQueueEntry, priority: int = 5) -> bool:
        """Add email to queue with priority."""
        try:
            self.queue.put((priority, entry.created_at.timestamp(), entry))
            logger.info(f"Email added to queue: {entry.id}")
            return True
        except queue.Full:
            logger.error("Email queue is full")
            return False
    
    def get_next_email(self) -> Optional[EmailQueueEntry]:
        """Get next email from queue."""
        try:
            if self.queue.empty():
                return None
            
            priority, timestamp, entry = self.queue.get_nowait()
            return entry
            
        except queue.Empty:
            return None
    
    def mark_sent(self, entry_id: str):
        """Mark email as sent."""
        with self._lock:
            self.sent_emails[entry_id] = datetime.utcnow()
    
    def mark_failed(self, entry_id: str, error: str):
        """Mark email as failed."""
        with self._lock:
            self.failed_emails[entry_id] = {
                'error': error,
                'timestamp': datetime.utcnow()
            }
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self.queue.qsize()
    
    def cleanup_old_entries(self, hours: int = 24):
        """Clean up old email entries."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        with self._lock:
            # Clean sent emails
            self.sent_emails = {
                k: v for k, v in self.sent_emails.items() 
                if v > cutoff
            }
            
            # Clean failed emails
            self.failed_emails = {
                k: v for k, v in self.failed_emails.items() 
                if v['timestamp'] > cutoff
            }


class UserEmailPreferencesManager:
    """Manages user email preferences and unsubscribes."""
    
    def __init__(self, supabase_layer):
        self.supabase = supabase_layer
    
    async def get_user_preferences(self, user_id: str) -> Optional[UserEmailPreferences]:
        """Get user email preferences."""
        try:
            result = self.supabase.client.table('user_email_preferences').select('*').eq(
                'user_id', user_id
            ).execute()
            
            if result.data:
                data = result.data[0]
                return UserEmailPreferences(
                    user_id=data['user_id'],
                    email=data['email'],
                    name=data.get('name'),
                    opportunity_alerts=data.get('opportunity_alerts', True),
                    trade_updates=data.get('trade_updates', True),
                    risk_warnings=data.get('risk_warnings', True),
                    profit_reports=data.get('profit_reports', True),
                    system_alerts=data.get('system_alerts', True),
                    weekly_reports=data.get('weekly_reports', False),
                    monthly_reports=data.get('monthly_reports', True),
                    frequency=data.get('frequency', 'immediate'),
                    quiet_hours_start=data.get('quiet_hours_start'),
                    quiet_hours_end=data.get('quiet_hours_end'),
                    timezone=data.get('timezone', 'UTC'),
                    include_screenshots=data.get('include_screenshots', True),
                    include_charts=data.get('include_charts', True),
                    detailed_reports=data.get('detailed_reports', True),
                    html_emails=data.get('html_emails', True),
                    text_emails=data.get('text_emails', False),
                    marketing_emails=data.get('marketing_emails', False),
                    newsletter=data.get('newsletter', False),
                    unsubscribe_token=data.get('unsubscribe_token'),
                    unsubscribed_at=datetime.fromisoformat(data['unsubscribed_at']) if data.get('unsubscribed_at') else None
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving user preferences: {e}")
            return None
    
    async def save_user_preferences(self, preferences: UserEmailPreferences) -> bool:
        """Save user email preferences."""
        try:
            data = {
                'user_id': preferences.user_id,
                'email': preferences.email,
                'name': preferences.name,
                'opportunity_alerts': preferences.opportunity_alerts,
                'trade_updates': preferences.trade_updates,
                'risk_warnings': preferences.risk_warnings,
                'profit_reports': preferences.profit_reports,
                'system_alerts': preferences.system_alerts,
                'weekly_reports': preferences.weekly_reports,
                'monthly_reports': preferences.monthly_reports,
                'frequency': preferences.frequency,
                'quiet_hours_start': preferences.quiet_hours_start,
                'quiet_hours_end': preferences.quite_hours_end,
                'timezone': preferences.timezone,
                'include_screenshots': preferences.include_screenshots,
                'include_charts': preferences.include_charts,
                'detailed_reports': preferences.detailed_reports,
                'html_emails': preferences.html_emails,
                'text_emails': preferences.text_emails,
                'marketing_emails': preferences.marketing_emails,
                'newsletter': preferences.newsletter,
                'unsubscribe_token': preferences.unsubscribe_token,
                'unsubscribed_at': preferences.unsubscribed_at.isoformat() if preferences.unsubscribed_at else None,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Check if preferences exist
            existing = self.supabase.client.table('user_email_preferences').select('id').eq(
                'user_id', preferences.user_id
            ).execute()
            
            if existing.data:
                # Update existing
                result = self.supabase.client.table('user_email_preferences').update(data).eq(
                    'user_id', preferences.user_id
                ).execute()
            else:
                # Create new
                data['created_at'] = datetime.utcnow().isoformat()
                result = self.supabase.client.table('user_email_preferences').insert(data).execute()
            
            logger.info(f"Saved email preferences for user {preferences.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user preferences: {e}")
            return False
    
    def generate_unsubscribe_token(self, user_id: str, email: str) -> str:
        """Generate unsubscribe token."""
        data = f"{user_id}:{email}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def is_user_subscribed(self, preferences: UserEmailPreferences) -> bool:
        """Check if user is subscribed to emails."""
        return preferences.unsubscribed_at is None


class EmailNotificationSystem:
    """Main email notification system."""
    
    def __init__(self, smtp_config: SMTPConfig, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize email notification system."""
        self.smtp_config = smtp_config
        self.smtp_manager = SMTPManager(smtp_config)
        self.template_manager = EmailTemplateManager()
        self.queue = EmailQueue()
        self.deliverability = EmailDeliverability()
        
        # Initialize Supabase layer
        try:
            self.supabase = get_data_layer()
        except Exception as e:
            logger.warning(f"Could not initialize Supabase layer: {e}")
            self.supabase = None
        
        # Initialize preferences manager
        if self.supabase:
            self.preferences_manager = UserEmailPreferencesManager(self.supabase)
        else:
            self.preferences_manager = None
        
        # Start background processing
        self._processing_thread = None
        self._start_processing()
    
    def _start_processing(self):
        """Start background email processing thread."""
        if self._processing_thread is None or not self._processing_thread.is_alive():
            self._processing_thread = threading.Thread(target=self._process_queue, daemon=True)
            self._processing_thread.start()
    
    def _process_queue(self):
        """Process email queue in background."""
        while True:
            try:
                entry = self.queue.get_next_email()
                if entry:
                    self._send_queued_email(entry)
                else:
                    time.sleep(1)  # Wait if queue is empty
                    
            except Exception as e:
                logger.error(f"Error processing email queue: {e}")
                time.sleep(5)
    
    def _send_queued_email(self, entry: EmailQueueEntry):
        """Send queued email with retry logic."""
        try:
            entry.status = EmailStatus.SENDING
            entry.last_attempt_at = datetime.utcnow()
            entry.attempt_count += 1
            
            if self.smtp_manager.send_email(entry.message):
                entry.status = EmailStatus.SENT
                self.queue.mark_sent(entry.id)
                logger.info(f"Email sent successfully: {entry.id}")
                
                # Log to Supabase if available
                if self.supabase:
                    self._log_email_delivery(entry, "sent")
                
            else:
                entry.status = EmailStatus.FAILED
                entry.last_error = "SMTP send failed"
                
                # Retry if under max attempts
                if entry.attempt_count < self.smtp_config.max_retries:
                    entry.status = EmailStatus.RETRYING
                    # Re-add to queue with delay
                    delay = self.smtp_config.retry_delay * (2 ** (entry.attempt_count - 1))
                    entry.scheduled_at = datetime.utcnow() + timedelta(seconds=delay)
                    self.queue.add_email(entry, priority=entry.attempt_count)
                else:
                    self.queue.mark_failed(entry.id, entry.last_error)
                    logger.error(f"Email failed after {entry.attempt_count} attempts: {entry.id}")
                
                # Log to Supabase if available
                if self.supabase:
                    self._log_email_delivery(entry, "failed")
                    
        except Exception as e:
            logger.error(f"Error sending queued email {entry.id}: {e}")
            entry.last_error = str(e)
            entry.status = EmailStatus.FAILED
            self.queue.mark_failed(entry.id, str(e))
    
    def _log_email_delivery(self, entry: EmailQueueEntry, status: str):
        """Log email delivery to Supabase."""
        try:
            if not self.supabase:
                return
            
            log_data = {
                'id': entry.id,
                'status': status,
                'attempt_count': entry.attempt_count,
                'recipients': [r.email for r in entry.message.to],
                'subject': entry.message.subject,
                'created_at': entry.created_at.isoformat(),
                'sent_at': datetime.utcnow().isoformat(),
                'error_message': entry.last_error,
                'metadata': entry.metadata
            }
            
            self.supabase.client.table('email_delivery_logs').insert(log_data).execute()
            
        except Exception as e:
            logger.error(f"Error logging email delivery: {e}")
    
    async def send_opportunity_alert(
        self,
        user_id: str,
        opportunity: ArbitrageOpportunity,
        custom_message: Optional[str] = None,
        include_screenshot: bool = False
    ) -> bool:
        """Send opportunity alert email."""
        try:
            # Get user preferences
            preferences = await self.preferences_manager.get_user_preferences(user_id) if self.preferences_manager else None
            
            # Check if user wants opportunity alerts
            if preferences and not preferences.opportunity_alerts:
                logger.info(f"User {user_id} has disabled opportunity alerts")
                return False
            
            # Create recipient
            recipient = EmailRecipient(
                email=preferences.email if preferences else "user@example.com",
                name=preferences.name if preferences else None,
                user_id=user_id,
                preferences=preferences.__dict__ if preferences else None
            )
            
            # Prepare template data
            legs_html = ""
            legs_text = ""
            for i, leg in enumerate(opportunity.legs):
                legs_html += f"""
                <tr>
                    <td class="bookmaker">{leg.bookmaker}</td>
                    <td>{leg.event_outcome}</td>
                    <td class="odds">{leg.odds:.2f}</td>
                    <td>{leg.stake_percentage * 100:.1f}%</td>
                </tr>
                """
                legs_text += f"{leg.bookmaker}: {leg.event_outcome} @ {leg.odds:.2f} ({leg.stake_percentage * 100:.1f}% stake)\n"
            
            # Risk info
            risk_info = f"Risk Tier: {opportunity.risk_tier.value.upper()}"
            if not opportunity.liquidity_checked:
                risk_info += " | ⚠️ Liquidity not verified"
            
            # Generate unsubscribe URL
            unsubscribe_url = self._generate_unsubscribe_url(user_id)
            dashboard_url = f"https://app.arbitech.trading/opportunities/{opportunity.id}"
            
            # Prepare template data
            template_data = {
                'event_name': opportunity.event_name,
                'sport': opportunity.sport.value.title(),
                'market_type': opportunity.market_type,
                'event_date': opportunity.event_date.strftime('%Y-%m-%d %H:%M UTC'),
                'profit_amount': float(opportunity.profit_amount),
                'profit_margin': float(opportunity.profit_margin * 100),
                'currency': 'USD',  # This should come from user settings
                'legs_html': legs_html,
                'legs_text': legs_text,
                'risk_info': risk_info,
                'unsubscribe_url': unsubscribe_url,
                'dashboard_url': dashboard_url
            }
            
            # Get template
            template = self.template_manager.get_template('opportunity_alert')
            if not template:
                raise ValueError("Opportunity alert template not found")
            
            # Render template
            subject, html_body, text_body = self.template_manager.render_template(template, template_data)
            
            # Create email message
            message = EmailMessage(
                to=[recipient],
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                priority=EmailPriority.HIGH
            )
            
            # Add custom message if provided
            if custom_message:
                message.html_body += f"\n\n<div style='padding: 15px; background: #f0f0f0; border-radius: 5px; margin: 20px 0;'><strong>Additional Message:</strong><br>{custom_message}</div>"
                message.text_body += f"\n\nAdditional Message:\n{custom_message}"
            
            # Add tracking pixel
            if recipient.user_id:
                tracking_pixel_url = f"https://tracking.arbitech.trading/pixel/{recipient.user_id}/{opportunity.id}"
                message.html_body += f'<img src="{tracking_pixel_url}" width="1" height="1" style="display: none;" />'
            
            # Add screenshot if requested
            if include_screenshot and preferences and preferences.include_screenshots:
                # This would integrate with the screenshot storage system
                pass
            
            # Queue email
            entry = EmailQueueEntry(
                id=f"opportunity_{user_id}_{opportunity.id}_{int(time.time())}",
                message=message,
                metadata={
                    'type': 'opportunity_alert',
                    'user_id': user_id,
                    'opportunity_id': str(opportunity.id),
                    'profit_margin': float(opportunity.profit_margin)
                }
            )
            
            return self.queue.add_email(entry, priority=1)  # High priority
            
        except Exception as e:
            logger.error(f"Error sending opportunity alert: {e}")
            return False
    
    async def send_trade_update(
        self,
        user_id: str,
        trade: Trade,
        include_screenshot: bool = False
    ) -> bool:
        """Send trade update email."""
        try:
            # Get user preferences
            preferences = await self.preferences_manager.get_user_preferences(user_id) if self.preferences_manager else None
            
            # Check if user wants trade updates
            if preferences and not preferences.trade_updates:
                return False
            
            # Create recipient
            recipient = EmailRecipient(
                email=preferences.email if preferences else "user@example.com",
                name=preferences.name if preferences else None,
                user_id=user_id,
                preferences=preferences.__dict__ if preferences else None
            )
            
            # Prepare template data
            status_class = {
                TradeStatus.FILLED: 'filled',
                TradeStatus.PENDING: 'pending',
                TradeStatus.FAILED: 'failed'
            }.get(trade.status, 'pending')
            
            opportunity_name = trade.opportunity.event_name
            currency = trade.stake_data.currency
            
            # Actual profit info
            actual_profit_info = ""
            if trade.actual_profit is not None:
                actual_profit_info = f"<p><strong>Actual Profit:</strong> {trade.actual_profit:.2f} {currency}</p>"
            else:
                actual_profit_info = "<p><strong>Actual Profit:</strong> Pending settlement</p>"
            
            unsubscribe_url = self._generate_unsubscribe_url(user_id)
            dashboard_url = f"https://app.arbitech.trading/trades/{trade.id}"
            
            template_data = {
                'trade_status': trade.status.value.title(),
                'status_class': status_class,
                'opportunity_name': opportunity_name,
                'expected_profit': float(trade.expected_profit),
                'actual_profit_info': actual_profit_info,
                'total_stake': float(trade.stake_data.total_stake),
                'currency': currency,
                'execution_mode': trade.execution_mode.value,
                'execution_time': trade.execution_time_ms or 'N/A',
                'unsubscribe_url': unsubscribe_url,
                'dashboard_url': dashboard_url
            }
            
            # Get template
            template = self.template_manager.get_template('trade_update')
            if not template:
                raise ValueError("Trade update template not found")
            
            # Render template
            subject, html_body, text_body = self.template_manager.render_template(template, template_data)
            
            # Create email message
            message = EmailMessage(
                to=[recipient],
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                priority=EmailPriority.NORMAL if trade.status in [TradeStatus.PENDING, TradeStatus.FILLED] else EmailPriority.HIGH
            )
            
            # Queue email
            entry = EmailQueueEntry(
                id=f"trade_update_{user_id}_{trade.id}_{int(time.time())}",
                message=message,
                metadata={
                    'type': 'trade_update',
                    'user_id': user_id,
                    'trade_id': str(trade.id),
                    'trade_status': trade.status.value
                }
            )
            
            return self.queue.add_email(entry)
            
        except Exception as e:
            logger.error(f"Error sending trade update: {e}")
            return False
    
    async def send_risk_warning(
        self,
        user_id: str,
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        risk_metrics: Optional[Dict[str, Any]] = None,
        recommended_action: Optional[str] = None
    ) -> bool:
        """Send risk warning email."""
        try:
            # Get user preferences
            preferences = await self.preferences_manager.get_user_preferences(user_id) if self.preferences_manager else None
            
            # Check if user wants risk warnings
            if preferences and not preferences.risk_warnings:
                return False
            
            # Create recipient
            recipient = EmailRecipient(
                email=preferences.email if preferences else "user@example.com",
                name=preferences.name if preferences else None,
                user_id=user_id,
                preferences=preferences.__dict__ if preferences else None
            )
            
            # Risk severity mapping
            severity_class = {'critical': 'high', 'high': 'high', 'medium': 'medium', 'low': 'low'}.get(severity, 'medium')
            
            # Format risk metrics
            risk_metrics_html = ""
            risk_metrics_text = ""
            if risk_metrics:
                risk_metrics_html = "<h3>Risk Metrics:</h3><ul>"
                risk_metrics_text = "Risk Metrics:\n"
                for key, value in risk_metrics.items():
                    risk_metrics_html += f"<li><strong>{key}:</strong> {value}</li>"
                    risk_metrics_text += f"- {key}: {value}\n"
                risk_metrics_html += "</ul>"
            
            # Format recommended action
            action_html = ""
            action_text = ""
            if recommended_action:
                action_html = f"<h3>Recommended Action:</h3><p>{recommended_action}</p>"
                action_text = f"Recommended Action: {recommended_action}\n"
            
            unsubscribe_url = self._generate_unsubscribe_url(user_id)
            dashboard_url = "https://app.arbitech.trading/risk"
            
            template_data = {
                'alert_title': title,
                'severity': severity.title(),
                'severity_class': severity_class,
                'description': description,
                'risk_metrics': risk_metrics_html,
                'risk_metrics_text': risk_metrics_text,
                'recommended_action': action_html,
                'recommended_action_text': action_text,
                'unsubscribe_url': unsubscribe_url,
                'dashboard_url': dashboard_url
            }
            
            # Get template
            template = self.template_manager.get_template('risk_warning')
            if not template:
                raise ValueError("Risk warning template not found")
            
            # Render template
            subject, html_body, text_body = self.template_manager.render_template(template, template_data)
            
            # Create email message
            priority = EmailPriority.CRITICAL if severity == 'critical' else EmailPriority.HIGH
            message = EmailMessage(
                to=[recipient],
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                priority=priority
            )
            
            # Queue email
            entry = EmailQueueEntry(
                id=f"risk_warning_{user_id}_{int(time.time())}",
                message=message,
                metadata={
                    'type': 'risk_warning',
                    'user_id': user_id,
                    'alert_type': alert_type,
                    'severity': severity
                }
            )
            
            return self.queue.add_email(entry, priority=1)  # High priority for risk warnings
            
        except Exception as e:
            logger.error(f"Error sending risk warning: {e}")
            return False
    
    async def send_profit_report(
        self,
        user_id: str,
        period: str,
        total_profit: Decimal,
        trades_count: int,
        success_rate: float,
        performance_metrics: Dict[str, Any],
        include_charts: bool = True
    ) -> bool:
        """Send profit report email."""
        try:
            # Get user preferences
            preferences = await self.preferences_manager.get_user_preferences(user_id) if self.preferences_manager else None
            
            # Check if user wants profit reports
            if preferences and not preferences.profit_reports:
                return False
            
            # Create recipient
            recipient = EmailRecipient(
                email=preferences.email if preferences else "user@example.com",
                name=preferences.name if preferences else None,
                user_id=user_id,
                preferences=preferences.__dict__ if preferences else None
            )
            
            # Format performance details
            performance_details = ""
            if performance_metrics:
                if preferences and preferences.detailed_reports:
                    performance_details = f"""
                    <p><strong>Average Profit per Trade:</strong> {performance_metrics.get('avg_profit_per_trade', 0):.2f}</p>
                    <p><strong>Best Trade:</strong> {performance_metrics.get('best_trade', 0):.2f}</p>
                    <p><strong>Worst Trade:</strong> {performance_metrics.get('worst_trade', 0):.2f}</p>
                    <p><strong>Total Trades:</strong> {performance_metrics.get('total_trades', trades_count)}</p>
                    """
                else:
                    performance_details = f"<p>Completed {trades_count} trades with {success_rate:.1f}% success rate.</p>"
            
            unsubscribe_url = self._generate_unsubscribe_url(user_id)
            dashboard_url = "https://app.arbitech.trading/reports"
            
            template_data = {
                'period': period,
                'total_profit': float(total_profit),
                'currency': 'USD',
                'trades_count': trades_count,
                'success_rate': success_rate,
                'performance_details': performance_details,
                'unsubscribe_url': unsubscribe_url,
                'dashboard_url': dashboard_url
            }
            
            # Get template
            template = self.template_manager.get_template('profit_report')
            if not template:
                raise ValueError("Profit report template not found")
            
            # Render template
            subject, html_body, text_body = self.template_manager.render_template(template, template_data)
            
            # Create email message
            message = EmailMessage(
                to=[recipient],
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                priority=EmailPriority.NORMAL
            )
            
            # Queue email
            entry = EmailQueueEntry(
                id=f"profit_report_{user_id}_{int(time.time())}",
                message=message,
                metadata={
                    'type': 'profit_report',
                    'user_id': user_id,
                    'period': period,
                    'total_profit': float(total_profit)
                }
            )
            
            return self.queue.add_email(entry)
            
        except Exception as e:
            logger.error(f"Error sending profit report: {e}")
            return False
    
    async def send_weekly_summary(
        self,
        user_id: str,
        week_range: str,
        trades_count: int,
        total_profit: Decimal,
        top_sports: List[str]
    ) -> bool:
        """Send weekly summary email."""
        try:
            # Get user preferences
            preferences = await self.preferences_manager.get_user_preferences(user_id) if self.preferences_manager else None
            
            # Check if user wants weekly reports
            if preferences and not preferences.weekly_reports:
                return False
            
            # Create recipient
            recipient = EmailRecipient(
                email=preferences.email if preferences else "user@example.com",
                name=preferences.name if preferences else None,
                user_id=user_id,
                preferences=preferences.__dict__ if preferences else None
            )
            
            unsubscribe_url = self._generate_unsubscribe_url(user_id)
            dashboard_url = "https://app.arbitech.trading/reports/weekly"
            
            template_data = {
                'week_range': week_range,
                'trades_count': trades_count,
                'total_profit': float(total_profit),
                'currency': 'USD',
                'top_sports': ', '.join(top_sports[:3]),  # Top 3 sports
                'unsubscribe_url': unsubscribe_url,
                'dashboard_url': dashboard_url
            }
            
            # Get template
            template = self.template_manager.get_template('weekly_summary')
            if not template:
                raise ValueError("Weekly summary template not found")
            
            # Render template
            subject, html_body, text_body = self.template_manager.render_template(template, template_data)
            
            # Create email message
            message = EmailMessage(
                to=[recipient],
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                priority=EmailPriority.LOW
            )
            
            # Queue email
            entry = EmailQueueEntry(
                id=f"weekly_summary_{user_id}_{int(time.time())}",
                message=message,
                metadata={
                    'type': 'weekly_summary',
                    'user_id': user_id,
                    'week_range': week_range
                }
            )
            
            return self.queue.add_email(entry, priority=10)  # Low priority
            
        except Exception as e:
            logger.error(f"Error sending weekly summary: {e}")
            return False
    
    async def handle_unsubscribe(self, user_id: str, token: str) -> bool:
        """Handle unsubscribe request."""
        try:
            if not self.preferences_manager:
                return False
            
            preferences = await self.preferences_manager.get_user_preferences(user_id)
            if not preferences:
                return False
            
            # Validate token
            expected_token = self.preferences_manager.generate_unsubscribe_token(user_id, preferences.email)
            if token != expected_token:
                logger.warning(f"Invalid unsubscribe token for user {user_id}")
                return False
            
            # Unsubscribe user
            preferences.unsubscribed_at = datetime.utcnow()
            preferences.opportunity_alerts = False
            preferences.trade_updates = False
            preferences.risk_warnings = False
            preferences.profit_reports = False
            preferences.weekly_reports = False
            preferences.monthly_reports = False
            preferences.marketing_emails = False
            preferences.newsletter = False
            
            success = await self.preferences_manager.save_user_preferences(preferences)
            
            if success:
                logger.info(f"User {user_id} unsubscribed from emails")
            
            return success
            
        except Exception as e:
            logger.error(f"Error handling unsubscribe: {e}")
            return False
    
    def _generate_unsubscribe_url(self, user_id: str) -> str:
        """Generate unsubscribe URL for user."""
        # This would use the actual domain and token generation
        if self.preferences_manager:
            # In practice, you'd get the user's email from preferences
            email = "user@example.com"  # This should come from user data
            token = self.preferences_manager.generate_unsubscribe_token(user_id, email)
            return f"https://app.arbitech.trading/unsubscribe/{user_id}/{token}"
        return "https://app.arbitech.trading/account/email-preferences"
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get email queue statistics."""
        return {
            'queue_size': self.queue.get_queue_size(),
            'sent_count': len(self.queue.sent_emails),
            'failed_count': len(self.queue.failed_emails),
            'processing_active': self._processing_thread.is_alive() if self._processing_thread else False
        }
    
    def cleanup(self):
        """Cleanup resources."""
        self.smtp_manager.disconnect()
        self.queue.cleanup_old_entries()


# Predefined SMTP configurations for popular providers
class SMTPConfigs:
    """Predefined SMTP configurations."""
    
    @staticmethod
    def gmail(username: str, password: str, app_password: bool = True) -> SMTPConfig:
        """Gmail SMTP configuration."""
        return SMTPConfig(
            host="smtp.gmail.com",
            port=587,
            username=username,
            password=password,
            use_tls=True,
            use_ssl=False
        )
    
    @staticmethod
    def outlook(username: str, password: str) -> SMTPConfig:
        """Outlook/Hotmail SMTP configuration."""
        return SMTPConfig(
            host="smtp-mail.outlook.com",
            port=587,
            username=username,
            password=password,
            use_tls=True,
            use_ssl=False
        )
    
    @staticmethod
    def custom(
        host: str,
        port: int,
        username: str,
        password: str,
        use_tls: bool = True,
        use_ssl: bool = False
    ) -> SMTPConfig:
        """Custom SMTP configuration."""
        return SMTPConfig(
            host=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_tls,
            use_ssl=use_ssl
        )


# Example usage and testing functions
async def demo_email_system():
    """Demonstrate email notification system."""
    
    # Gmail configuration (use app password)
    smtp_config = SMTPConfigs.gmail(
        username="your-email@gmail.com",
        password="your-app-password"
    )
    
    # Initialize system
    email_system = EmailNotificationSystem(smtp_config)
    
    # Create sample opportunity
    from storage.models import ArbitrageLeg
    opportunity = ArbitrageOpportunity(
        sport=Sport.FOOTBALL,
        event_name="Manchester United vs Liverpool",
        event_date=datetime.utcnow() + timedelta(days=1),
        market_type="Match Winner",
        legs=[
            ArbitrageLeg(
                bookmaker="Bet365",
                event_outcome="Manchester United Win",
                odds=Decimal("2.10"),
                implied_probability=Decimal("0.476"),
                stake_percentage=Decimal("0.487"),
                actual_stake=Decimal("48.70"),
                potential_payout=Decimal("102.27")
            ),
            ArbitrageLeg(
                bookmaker="William Hill",
                event_outcome="Liverpool Win",
                odds=Decimal("1.95"),
                implied_probability=Decimal("0.513"),
                stake_percentage=Decimal("0.513"),
                actual_stake=Decimal("51.30"),
                potential_payout=Decimal("100.04")
            )
        ],
        total_stake=Decimal("100.00"),
        profit_margin=Decimal("0.0223"),
        profit_amount=Decimal("2.23"),
        risk_tier=RiskTier.TIER_A
    )
    
    # Send opportunity alert
    await email_system.send_opportunity_alert(
        user_id="demo-user-123",
        opportunity=opportunity,
        custom_message="This opportunity looks very promising based on historical data!"
    )
    
    # Print queue stats
    stats = email_system.get_queue_stats()
    print(f"Email queue stats: {stats}")


if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_email_system())