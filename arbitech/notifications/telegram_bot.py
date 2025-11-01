"""
Comprehensive Telegram Bot Integration for ARBitech System

This module provides a complete Telegram bot integration for the ARBitech arbitrage trading platform.
It supports real-time notifications, interactive approval workflows, and comprehensive trading management.

Features:
- Telegram Bot API integration with complete command suite
- Real-time arbitrage opportunity notifications
- Interactive buttons for quick trade approval/rejection
- Conversation states for complex workflows
- Multimedia notifications with charts and screenshots
- Multi-user authentication and authorization
- Integration with ARBitech Phases 3-8
- Comprehensive error handling and rate limiting
- System monitoring and health checks

Author: ARBitech Development Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import time
import traceback
import io
import base64
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable, Any, Union
from uuid import UUID, uuid4
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import threading

# Telegram Bot
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand, Bot, InputFile
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler,
    CallbackContext
)
from telegram.constants import ParseMode
from telegram.error import TelegramError, RetryAfter, TimedOut, NetworkError

# ARBitech System Integration
from storage.supabase_layer import SupabaseDataLayer
from storage.models import (
    ArbitrageOpportunity, ArbitrageLeg, Trade, TradeStatus,
    RiskTier, Sport, NotificationType, NotificationPriority,
    NotificationChannel
)
from hitl.approval_workflow import ApprovalWorkflow, ApprovalStatus, ApprovalMode
from detection.opportunity_scanner import OpportunityScanner
from risk.risk_analyzer import RiskAnalyzer
from storage.audit_logger import AuditLogger

# Data and Analysis
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import numpy as np


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Enums for bot functionality
class UserRole(Enum):
    """User roles in the bot system"""
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"
    APPROVER = "approver"


class BotState(Enum):
    """Conversation states for the bot"""
    AUTHENTICATING = 1
    MENU = 2
    VIEWING_OPPORTUNITIES = 3
    APPROVING_TRADE = 4
    VIEWING_PERFORMANCE = 5
    SETTINGS = 6
    CONFIGURING_ALERTS = 7


class MessageType(Enum):
    """Types of bot messages"""
    NOTIFICATION = "notification"
    UPDATE = "update"
    ERROR = "error"
    COMMAND_RESPONSE = "command_response"
    APPROVAL_REQUEST = "approval_request"


@dataclass
class UserSession:
    """Bot user session data"""
    user_id: str
    telegram_id: int
    username: str
    role: UserRole
    authorized: bool = False
    preferences: Dict[str, Any] = None
    current_opportunity_id: Optional[str] = None
    state: BotState = BotState.AUTHENTICATING
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()
        if self.preferences is None:
            self.preferences = {}


@dataclass
class RateLimitEntry:
    """Rate limiting entry for users"""
    user_id: int
    command: str
    count: int
    window_start: float
    reset_time: float


@dataclass
class BotNotification:
    """Notification data structure"""
    notification_id: str
    user_id: str
    type: MessageType
    title: str
    content: str
    data: Dict[str, Any]
    priority: NotificationPriority
    timestamp: datetime
    read: bool = False
    buttons: List[Dict[str, str]] = None


class ARBITechTelegramBot:
    """
    Comprehensive Telegram bot for ARBitech arbitrage trading system.
    
    Features:
    - Real-time opportunity notifications
    - Interactive trade approval workflows
    - Performance analytics and reporting
    - Multi-user management
    - Rate limiting and error handling
    - Integration with all ARBitech phases
    """
    
    # Command definitions
    COMMANDS = {
        'start': 'Initialize the bot and authentication',
        'help': 'Show available commands and usage',
        'menu': 'Open main menu',
        'opportunities': 'View recent arbitrage opportunities',
        'approve': 'Approve a pending trade',
        'reject': 'Reject a pending trade',
        'performance': 'View trading performance metrics',
        'status': 'Check system status',
        'settings': 'Configure user preferences',
        'alerts': 'Manage notification alerts',
        'logout': 'Log out from the bot'
    }
    
    # Rate limiting configuration
    RATE_LIMIT_COMMANDS = {
        'opportunities': (5, 60),  # 5 commands per minute
        'approve': (10, 60),       # 10 approvals per minute
        'performance': (3, 60),    # 3 reports per minute
        'status': (10, 60)         # 10 status checks per minute
    }
    
    # Default user preferences
    DEFAULT_PREFERENCES = {
        'notifications_enabled': True,
        'opportunity_alerts': True,
        'trade_updates': True,
        'risk_warnings': True,
        'performance_reports': True,
        'min_profit_threshold': 1.0,  # 1% minimum profit
        'max_stake_limit': 10000.0,   # $10,000 max stake
        'risk_tier_filter': ['TIER_A', 'TIER_B'],
        'sports_filter': [],  # Empty means all sports
        'auto_approve_tier_a': False,
        'screenshot_notifications': True,
        'performance_update_frequency': 'daily'
    }
    
    def __init__(self, token: str, data_layer: SupabaseDataLayer):
        """
        Initialize the Telegram bot.
        
        Args:
            token: Telegram bot token
            data_layer: Supabase data layer instance
        """
        self.token = token
        self.data_layer = data_layer
        self.bot = Bot(token=token)
        
        # User management
        self.users: Dict[int, UserSession] = {}
        self.user_lock = threading.Lock()
        
        # Rate limiting
        self.rate_limits: Dict[str, List[RateLimitEntry]] = {}
        self.rate_limit_lock = threading.Lock()
        
        # Notification queue
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Integration components
        self.approval_workflow = ApprovalWorkflow()
        self.audit_logger = AuditLogger()
        self.risk_analyzer = RiskAnalyzer()
        
        # Application
        self.application: Optional[Application] = None
        
        # Status tracking
        self.start_time = datetime.utcnow()
        self.total_messages_sent = 0
        self.total_notifications_sent = 0
        self.error_count = 0
        
        logger.info("ARBitech Telegram Bot initialized")
    
    async def initialize(self) -> None:
        """Initialize the bot application and components"""
        try:
            # Create application
            self.application = (
                Application.builder()
                .token(self.token)
                .build()
            )
            
            # Add handlers
            self._add_handlers()
            
            # Start the application
            await self.application.initialize()
            await self.application.start()
            
            # Set bot commands
            await self._set_bot_commands()
            
            # Start background tasks
            asyncio.create_task(self._notification_worker())
            asyncio.create_task(self._cleanup_worker())
            
            logger.info("Telegram bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise
    
    def _add_handlers(self) -> None:
        """Add command and message handlers to the application"""
        app = self.application
        
        # Command handlers
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("help", self._cmd_help))
        app.add_handler(CommandHandler("menu", self._cmd_menu))
        app.add_handler(CommandHandler("opportunities", self._cmd_opportunities))
        app.add_handler(CommandHandler("approve", self._cmd_approve))
        app.add_handler(CommandHandler("reject", self._cmd_reject))
        app.add_handler(CommandHandler("performance", self._cmd_performance))
        app.add_handler(CommandHandler("status", self._cmd_status))
        app.add_handler(CommandHandler("settings", self._cmd_settings))
        app.add_handler(CommandHandler("alerts", self._cmd_alerts))
        app.add_handler(CommandHandler("logout", self._cmd_logout))
        
        # Callback query handlers
        app.add_handler(CallbackQueryHandler(self._handle_approval_callback, pattern="^approve:"))
        app.add_handler(CallbackQueryHandler(self._handle_rejection_callback, pattern="^reject:"))
        app.add_handler(CallbackQueryHandler(self._handle_menu_callback, pattern="^menu:"))
        app.add_handler(CallbackQueryHandler(self._handle_settings_callback, pattern="^settings:"))
        app.add_handler(CallbackQueryHandler(self._handle_alerts_callback, pattern="^alerts:"))
        
        # Conversation handler for complex workflows
        conversation_handler = ConversationHandler(
            entry_points=[CommandHandler("menu", self._cmd_menu)],
            states={
                BotState.AUTHENTICATING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_auth)
                ],
                BotState.MENU: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_menu_input)
                ],
                BotState.VIEWING_OPPORTUNITIES: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_opportunities_input)
                ],
                BotState.APPROVING_TRADE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_approval_input)
                ],
                BotState.SETTINGS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_settings_input)
                ],
                BotState.CONFIGURING_ALERTS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_alerts_input)
                ]
            },
            fallbacks=[CommandHandler("cancel", self._cmd_cancel)]
        )
        app.add_handler(conversation_handler)
        
        # Error handler
        app.add_error_handler(self._handle_error)
    
    async def _set_bot_commands(self) -> None:
        """Set bot commands in Telegram"""
        commands = [
            BotCommand(command, description)
            for command, description in self.COMMANDS.items()
        ]
        await self.bot.set_my_commands(commands)
    
    # Command Handlers
    
    async def _cmd_start(self, update: Update, context: CallbackContext) -> None:
        """Handle /start command"""
        user = update.effective_user
        
        # Create user session
        session = UserSession(
            user_id=str(uuid4()),
            telegram_id=user.id,
            username=user.username or user.first_name,
            role=UserRole.VIEWER  # Default role
        )
        
        with self.user_lock:
            self.users[user.id] = session
        
        # Send welcome message
        welcome_text = f"""
🚀 *ARBitech Trading Bot*

Welcome to the ARBitech arbitrage trading platform!

Your Telegram ID: `{user.id}`
Session ID: `{session.user_id}`

Please authenticate to access trading features.

*Available Commands:*
• /help - Show all commands
• /menu - Open main menu
• /status - Check system status

Initializing...
        """
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Log the connection
        await self.audit_logger.log_event(
            event_type="bot_connection",
            user_id=session.user_id,
            data={"telegram_id": user.id, "username": session.username}
        )
        
        # Start authentication process
        await self._start_authentication(update, context)
    
    async def _cmd_help(self, update: Update, context: CallbackContext) -> None:
        """Handle /help command"""
        user = self._get_user_session(update.effective_user.id)
        if not user:
            await update.message.reply_text("Please start with /start first.")
            return
        
        help_text = f"""
📚 *ARBitech Bot Commands*

*Trading Commands:*
/opportunities - View recent arbitrage opportunities
/approve <trade_id> - Approve a pending trade
/reject <trade_id> - Reject a pending trade
/performance - View trading performance

*System Commands:*
/menu - Open interactive menu
/status - Check system health and status
/settings - Configure your preferences
/alerts - Manage notification alerts
/logout - Log out safely

*Your Current Status:*
Role: {user.role.value.title()}
Authorized: {'✅' if user.authorized else '❌'}
Notifications: {'✅' if user.preferences.get('notifications_enabled', True) else '❌'}

*Need Help?*
Contact an administrator for role upgrades.
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _cmd_menu(self, update: Update, context: CallbackContext) -> None:
        """Handle /menu command - show main menu"""
        user = self._get_user_session(update.effective_user.id)
        if not user or not user.authorized:
            await update.message.reply_text("❌ Please authenticate first with /start")
            return
        
        # Update user state
        user.state = BotState.MENU
        
        keyboard = [
            [InlineKeyboardButton("🔍 View Opportunities", callback_data="menu:opportunities")],
            [InlineKeyboardButton("✅ Approve Trades", callback_data="menu:approve")],
            [InlineKeyboardButton("📊 Performance", callback_data="menu:performance")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="menu:settings")],
            [InlineKeyboardButton("🔔 Alert Settings", callback_data="menu:alerts")],
            [InlineKeyboardButton("📈 System Status", callback_data="menu:status")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = f"""
🎯 *ARBitech Main Menu*

*Welcome, {user.username}!*

Role: {user.role.value.title()}
Active Opportunities: {len(await self._get_active_opportunities(user))}
Pending Approvals: {len(await self._get_pending_approvals(user))}

Select an option below:
        """
        
        await update.message.reply_text(
            menu_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _cmd_opportunities(self, update: Update, context: CallbackContext) -> None:
        """Handle /opportunities command"""
        if not self._check_rate_limit(update.effective_user.id, "opportunities"):
            await update.message.reply_text("⚠️ Rate limit exceeded. Please wait before requesting again.")
            return
        
        user = self._get_user_session(update.effective_user.id)
        if not user or not user.authorized:
            await update.message.reply_text("❌ Please authenticate first.")
            return
        
        # Get opportunities from data layer
        opportunities = await self._get_active_opportunities(user)
        
        if not opportunities:
            await update.message.reply_text("📭 No active arbitrage opportunities found.")
            return
        
        # Send opportunities with inline keyboards
        for i, opp in enumerate(opportunities[:5]):  # Limit to 5
            await self._send_opportunity_card(update, user, opp, i + 1)
        
        logger.info(f"Sent {len(opportunities)} opportunities to user {user.telegram_id}")
    
    async def _cmd_performance(self, update: Update, context: CallbackContext) -> None:
        """Handle /performance command"""
        if not self._check_rate_limit(update.effective_user.id, "performance"):
            await update.message.reply_text("⚠️ Rate limit exceeded. Please wait before requesting again.")
            return
        
        user = self._get_user_session(update.effective_user.id)
        if not user or not user.authorized:
            await update.message.reply_text("❌ Please authenticate first.")
            return
        
        # Generate performance report
        performance_data = await self._get_performance_data(user)
        
        if not performance_data:
            await update.message.reply_text("📊 No performance data available yet.")
            return
        
        # Create performance chart
        chart_buffer = await self._create_performance_chart(performance_data)
        
        # Create performance message
        performance_text = self._format_performance_text(performance_data)
        
        # Send performance report with chart
        await update.message.reply_photo(
            photo=chart_buffer,
            caption=performance_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        self.total_messages_sent += 1
    
    async def _cmd_status(self, update: Update, context: CallbackContext) -> None:
        """Handle /status command"""
        if not self._check_rate_limit(update.effective_user.id, "status"):
            await update.message.reply_text("⚠️ Rate limit exceeded. Please wait before requesting again.")
            return
        
        # Get system status
        status_data = await self._get_system_status()
        
        status_text = f"""
📊 *System Status*

*Bot Health:*
Uptime: {self._format_uptime()}
Messages Sent: {self.total_messages_sent}
Notifications: {self.total_notifications_sent}
Errors: {self.error_count}

*Trading System:*
Active Opportunities: {status_data.get('active_opportunities', 0)}
Pending Trades: {status_data.get('pending_trades', 0)}
Running Scanners: {status_data.get('running_scanners', 0)}
Active Users: {len([u for u in self.users.values() if u.authorized])}

*Database:*
Connection: {'✅' if status_data.get('db_connected', False) else '❌'}
Last Sync: {status_data.get('last_sync', 'N/A')}

*Risk Management:*
Active Alerts: {status_data.get('risk_alerts', 0)}
Circuit Breakers: {status_data.get('circuit_breakers', 0)}
        """
        
        await update.message.reply_text(
            status_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        self.total_messages_sent += 1
    
    async def _cmd_settings(self, update: Update, context: CallbackContext) -> None:
        """Handle /settings command"""
        user = self._get_user_session(update.effective_user.id)
        if not user or not user.authorized:
            await update.message.reply_text("❌ Please authenticate first.")
            return
        
        user.state = BotState.SETTINGS
        
        keyboard = [
            [InlineKeyboardButton("🔔 Notifications", callback_data="settings:notifications")],
            [InlineKeyboardButton("💰 Profit Thresholds", callback_data="settings:thresholds")],
            [InlineKeyboardButton("⚠️ Risk Settings", callback_data="settings:risk")],
            [InlineKeyboardButton("🏆 Sports Filter", callback_data="settings:sports")],
            [InlineKeyboardButton("🤖 Auto-Approve", callback_data="settings:auto_approve")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu:back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = """
⚙️ *User Settings*

Configure your trading preferences and notification settings.

*Current Status:*
• Notifications: {'✅' if user.preferences.get('notifications_enabled') else '❌'}
• Min Profit: {min_profit}%
• Max Stake: ${max_stake:,.2f}
• Auto-approve Tier A: {'✅' if user.preferences.get('auto_approve_tier_a') else '❌'}
        """
        
        await update.message.reply_text(
            settings_text.format(
                min_profit=user.preferences.get('min_profit_threshold', 1.0),
                max_stake=user.preferences.get('max_stake_limit', 10000.0)
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _cmd_alerts(self, update: Update, context: CallbackContext) -> None:
        """Handle /alerts command"""
        user = self._get_user_session(update.effective_user.id)
        if not user or not user.authorized:
            await update.message.reply_text("❌ Please authenticate first.")
            return
        
        user.state = BotState.CONFIGURING_ALERTS
        
        keyboard = [
            [InlineKeyboardButton("🔔 Enable All", callback_data="alerts:enable_all")],
            [InlineKeyboardButton("🔕 Disable All", callback_data="alerts:disable_all")],
            [InlineKeyboardButton("💡 Opportunity Alerts", callback_data="alerts:opportunities")],
            [InlineKeyboardButton("📈 Trade Updates", callback_data="alerts:trades")],
            [InlineKeyboardButton("⚠️ Risk Warnings", callback_data="alerts:risk")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu:back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        alerts_text = """
🔔 *Alert Configuration*

Manage which notifications you receive in real-time.

*Current Alerts:*
• Opportunities: {'✅' if user.preferences.get('opportunity_alerts') else '❌'}
• Trade Updates: {'✅' if user.preferences.get('trade_updates') else '❌'}
• Risk Warnings: {'✅' if user.preferences.get('risk_warnings') else '❌'}
• Performance: {'✅' if user.preferences.get('performance_reports') else '❌'}

Choose an option below:
        """
        
        await update.message.reply_text(
            alerts_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _cmd_approve(self, update: Update, context: CallbackContext) -> None:
        """Handle /approve command"""
        if not self._check_rate_limit(update.effective_user.id, "approve"):
            await update.message.reply_text("⚠️ Rate limit exceeded. Please wait before requesting again.")
            return
        
        user = self._get_user_session(update.effective_user.id)
        if not user or not user.authorized:
            await update.message.reply_text("❌ Please authenticate first.")
            return
        
        # Check if user has approval privileges
        if user.role not in [UserRole.ADMIN, UserRole.APPROVER, UserRole.TRADER]:
            await update.message.reply_text("❌ You don't have permission to approve trades.")
            return
        
        # Get trade ID from command arguments
        args = context.args
        if not args:
            await update.message.reply_text("❌ Please specify a trade ID. Usage: /approve <trade_id>")
            return
        
        trade_id = args[0]
        
        # Process approval
        success = await self._process_trade_approval(user, trade_id, approved=True)
        
        if success:
            await update.message.reply_text(f"✅ Trade {trade_id} has been approved.")
        else:
            await update.message.reply_text(f"❌ Failed to approve trade {trade_id}.")
    
    async def _cmd_reject(self, update: Update, context: CallbackContext) -> None:
        """Handle /reject command"""
        if not self._check_rate_limit(update.effective_user.id, "approve"):
            await update.message.reply_text("⚠️ Rate limit exceeded. Please wait before requesting again.")
            return
        
        user = self._get_user_session(update.effective_user.id)
        if not user or not user.authorized:
            await update.message.reply_text("❌ Please authenticate first.")
            return
        
        # Check if user has approval privileges
        if user.role not in [UserRole.ADMIN, UserRole.APPROVER, UserRole.TRADER]:
            await update.message.reply_text("❌ You don't have permission to reject trades.")
            return
        
        # Get trade ID from command arguments
        args = context.args
        if not args:
            await update.message.reply_text("❌ Please specify a trade ID. Usage: /reject <trade_id>")
            return
        
        trade_id = args[0]
        
        # Process rejection
        success = await self._process_trade_approval(user, trade_id, approved=False)
        
        if success:
            await update.message.reply_text(f"❌ Trade {trade_id} has been rejected.")
        else:
            await update.message.reply_text(f"⚠️ Failed to reject trade {trade_id}.")
    
    async def _cmd_logout(self, update: Update, context: CallbackContext) -> None:
        """Handle /logout command"""
        user = self._get_user_session(update.effective_user.id)
        if not user:
            await update.message.reply_text("❌ No active session found.")
            return
        
        # Clean up user session
        with self.user_lock:
            self.users.pop(update.effective_user.id, None)
        
        # Log logout
        await self.audit_logger.log_event(
            event_type="bot_logout",
            user_id=user.user_id,
            data={"telegram_id": user.telegram_id}
        )
        
        await update.message.reply_text("👋 You have been logged out successfully.")
    
    async def _cmd_cancel(self, update: Update, context: CallbackContext) -> int:
        """Handle conversation cancellation"""
        await update.message.reply_text("❌ Operation cancelled. Use /menu to return to main menu.")
        return ConversationHandler.END
    
    # Callback Query Handlers
    
    async def _handle_approval_callback(self, update: Update, context: CallbackContext) -> None:
        """Handle inline keyboard callbacks for trade approval"""
        query = update.callback_query
        await query.answer()
        
        # Extract data from callback data
        data = query.data.split(":")
        action = data[1]  # approve/reject
        trade_id = data[2]
        
        user = self._get_user_session(query.from_user.id)
        if not user or not user.authorized:
            await query.edit_message_text("❌ Session expired. Please /start again.")
            return
        
        # Process the approval/rejection
        if action == "approve":
            success = await self._process_trade_approval(user, trade_id, approved=True)
            message = f"✅ Trade {trade_id} approved successfully!"
        else:
            success = await self._process_trade_approval(user, trade_id, approved=False)
            message = f"❌ Trade {trade_id} rejected."
        
        # Update the message
        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Log the action
        await self.audit_logger.log_event(
            event_type="trade_approval",
            user_id=user.user_id,
            data={"trade_id": trade_id, "action": action, "success": success}
        )
    
    async def _handle_menu_callback(self, update: Update, context: CallbackContext) -> None:
        """Handle menu callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split(":")[1]
        
        if data == "opportunities":
            await self._cmd_opportunities(update, context)
        elif data == "approve":
            await self._show_pending_approvals(update, context)
        elif data == "performance":
            await self._cmd_performance(update, context)
        elif data == "settings":
            await self._cmd_settings(update, context)
        elif data == "alerts":
            await self._cmd_alerts(update, context)
        elif data == "status":
            await self._cmd_status(update, context)
        elif data == "back":
            await self._cmd_menu(update, context)
    
    async def _handle_settings_callback(self, update: Update, context: CallbackContext) -> None:
        """Handle settings callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split(":")[1]
        
        if data == "notifications":
            await self._toggle_notifications(update, context)
        elif data == "thresholds":
            await self._show_threshold_settings(update, context)
        elif data == "risk":
            await self._show_risk_settings(update, context)
        elif data == "sports":
            await self._show_sports_settings(update, context)
        elif data == "auto_approve":
            await self._toggle_auto_approve(update, context)
    
    async def _handle_alerts_callback(self, update: Update, context: CallbackContext) -> None:
        """Handle alerts callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data.split(":")[1]
        user = self._get_user_session(query.from_user.id)
        
        if data == "enable_all":
            await self._enable_all_alerts(user)
            await query.edit_message_text("🔔 All alerts have been enabled!")
        elif data == "disable_all":
            await self._disable_all_alerts(user)
            await query.edit_message_text("🔕 All alerts have been disabled!")
        elif data == "opportunities":
            await self._toggle_alert_type(user, "opportunity_alerts")
            await self._cmd_alerts(update, context)
        elif data == "trades":
            await self._toggle_alert_type(user, "trade_updates")
            await self._cmd_alerts(update, context)
        elif data == "risk":
            await self._toggle_alert_type(user, "risk_warnings")
            await self._cmd_alerts(update, context)
    
    # Authentication and User Management
    
    async def _start_authentication(self, update: Update, context: CallbackContext) -> None:
        """Start the authentication process"""
        auth_text = """
🔐 *Authentication Required*

To access ARBitech trading features, please provide one of:

1. **Admin Code** - Full access to all features
2. **API Key** - Your personal API key
3. **User ID** - Your registered user ID

*Default Access:*
• New users get VIEWER role
• VIEWER can view opportunities and performance
• TRADER can approve trades and view all data
• ADMIN has full control

Send your authentication code:
        """
        
        await update.message.reply_text(
            auth_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_auth(self, update: Update, context: CallbackContext) -> None:
        """Handle authentication input"""
        user = self._get_user_session(update.effective_user.id)
        if not user or user.state != BotState.AUTHENTICATING:
            return
        
        auth_code = update.message.text.strip()
        
        # Simple authentication logic (in production, this would be more secure)
        if auth_code == "ADMIN2024":
            user.role = UserRole.ADMIN
            user.authorized = True
            auth_message = "✅ Authentication successful! Welcome, ADMIN."
        elif auth_code.startswith("USER_"):
            user.role = UserRole.TRADER
            user.authorized = True
            auth_message = "✅ Authentication successful! Welcome, TRADER."
        elif auth_code == "VIEW":
            user.role = UserRole.VIEWER
            user.authorized = True
            auth_message = "✅ Authentication successful! Welcome, VIEWER."
        else:
            auth_message = "❌ Invalid authentication code. Please try again."
            return
        
        # Set default preferences
        user.preferences = self.DEFAULT_PREFERENCES.copy()
        user.state = BotState.MENU
        
        await update.message.reply_text(auth_message)
        
        # Log successful authentication
        await self.audit_logger.log_event(
            event_type="bot_authentication",
            user_id=user.user_id,
            data={
                "telegram_id": user.telegram_id,
                "role": user.role.value,
                "auth_code": auth_code[:4] + "****"  # Log partial code for security
            }
        )
        
        # Show menu
        await self._cmd_menu(update, context)
    
    # Helper Methods
    
    def _get_user_session(self, telegram_id: int) -> Optional[UserSession]:
        """Get user session by Telegram ID"""
        with self.user_lock:
            return self.users.get(telegram_id)
    
    def _check_rate_limit(self, user_id: int, command: str) -> bool:
        """Check if user is within rate limits"""
        if command not in self.RATE_LIMIT_COMMANDS:
            return True
        
        limit, window = self.RATE_LIMIT_COMMANDS[command]
        current_time = time.time()
        
        with self.rate_limit_lock:
            # Clean old entries
            key = f"{user_id}:{command}"
            if key not in self.rate_limits:
                self.rate_limits[key] = []
            
            entries = self.rate_limits[key]
            
            # Remove entries outside the window
            self.rate_limits[key] = [
                entry for entry in entries 
                if current_time - entry.window_start < window
            ]
            
            # Check if under limit
            if len(self.rate_limits[key]) >= limit:
                return False
            
            # Add new entry
            self.rate_limits[key].append(
                RateLimitEntry(
                    user_id=user_id,
                    command=command,
                    count=len(self.rate_limits[key]) + 1,
                    window_start=current_time,
                    reset_time=current_time + window
                )
            )
            
            return True
    
    async def _get_active_opportunities(self, user: UserSession) -> List[ArbitrageOpportunity]:
        """Get active arbitrage opportunities for user"""
        try:
            # Get opportunities from data layer
            opportunities = await self.data_layer.get_opportunities(
                limit=10,
                risk_tier_filter=user.preferences.get('risk_tier_filter', ['TIER_A', 'TIER_B'])
            )
            
            # Filter by user preferences
            filtered_opportunities = []
            for opp in opportunities:
                # Check profit threshold
                profit_margin = float(opp.profit_margin)
                if profit_margin < user.preferences.get('min_profit_threshold', 1.0):
                    continue
                
                # Check stake limit
                total_stake = float(opp.total_stake)
                if total_stake > user.preferences.get('max_stake_limit', 10000.0):
                    continue
                
                # Check sports filter
                sports_filter = user.preferences.get('sports_filter', [])
                if sports_filter and opp.sport not in sports_filter:
                    continue
                
                filtered_opportunities.append(opp)
            
            return filtered_opportunities
            
        except Exception as e:
            logger.error(f"Error getting opportunities: {e}")
            return []
    
    async def _get_pending_approvals(self, user: UserSession) -> List[Trade]:
        """Get pending trades for approval"""
        try:
            # Get pending trades
            trades = await self.data_layer.get_user_trades(
                user_id=user.user_id,
                status_filter=[TradeStatus.PENDING]
            )
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting pending approvals: {e}")
            return []
    
    async def _send_opportunity_card(self, update: Update, user: UserSession, 
                                   opportunity: ArbitrageOpportunity, index: int) -> None:
        """Send opportunity details as a formatted card"""
        
        # Create opportunity text
        opportunity_text = f"""
🔍 *Opportunity #{index}*

*Event:* {opportunity.event_name}
*Sport:* {opportunity.sport.title()}
*Market:* {opportunity.market_type}
*Date:* {opportunity.event_date.strftime('%Y-%m-%d %H:%M UTC')}

💰 *Profit Details:*
• Profit Margin: {opportunity.profit_margin:.2f}%
• Total Stake: ${opportunity.total_stake:,.2f}
• Expected Profit: ${opportunity.expected_profit:,.2f}
• Risk Tier: {opportunity.risk_tier.title()}

📊 *Betting Legs:*
        """
        
        # Add leg details
        for i, leg in enumerate(opportunity.legs):
            opportunity_text += f"""
{i+1}. {leg.bookmaker}
   Outcome: {leg.event_outcome}
   Odds: {leg.odds:.2f}
   Stake: ${leg.actual_stake:,.2f}
   Payout: ${leg.potential_payout:,.2f}"""
        
        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{opportunity.id}:approve"),
                InlineKeyboardButton("❌ Reject", callback_data=f"approve:{opportunity.id}:reject")
            ],
            [InlineKeyboardButton("📊 Details", callback_data=f"opportunity:{opportunity.id}:details")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send the opportunity card
        await update.message.reply_text(
            opportunity_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _show_pending_approvals(self, update: Update, context: CallbackContext) -> None:
        """Show pending approvals to user"""
        user = self._get_user_session(update.effective_user.id)
        if not user:
            return
        
        pending_trades = await self._get_pending_approvals(user)
        
        if not pending_trades:
            await update.callback_query.edit_message_text(
                "📭 No pending trades for approval.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Send each pending trade
        for i, trade in enumerate(pending_trades[:5]):  # Limit to 5
            await self._send_pending_trade_card(update, user, trade, i + 1)
    
    async def _send_pending_trade_card(self, update: Update, user: UserSession,
                                     trade: Trade, index: int) -> None:
        """Send pending trade details as a card"""
        
        # Calculate profit if available
        profit_text = "N/A"
        if hasattr(trade, 'actual_profit') and trade.actual_profit:
            profit_text = f"${trade.actual_profit:,.2f}"
        
        trade_text = f"""
⏳ *Pending Trade #{index}*

*Trade ID:* `{trade.id}`
*Status:* {trade.status.value.title()}
*Total Stake:* ${trade.total_stake:,.2f}
*Expected Profit:* ${trade.expected_profit:,.2f}
*Actual Profit:* {profit_text}

*Created:* {trade.created_at.strftime('%Y-%m-%d %H:%M UTC')}
*Updated:* {trade.updated_at.strftime('%Y-%m-%d %H:%M UTC')}

Ready for your approval.
        """
        
        # Create action buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve:{trade.id}:approve"),
                InlineKeyboardButton("❌ Reject", callback_data=f"approve:{trade.id}:reject")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            trade_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _process_trade_approval(self, user: UserSession, trade_id: str, 
                                    approved: bool) -> bool:
        """Process trade approval or rejection"""
        try:
            # Log the decision in HITL system
            decision_data = {
                'opportunity_id': trade_id,
                'user_id': user.user_id,
                'decision': 'approved' if approved else 'rejected',
                'decision_reason': 'User approved via Telegram bot',
                'timestamp': datetime.utcnow()
            }
            
            await self.data_layer.log_hitl_decision(**decision_data)
            
            # Update trade status
            new_status = TradeStatus.FILLED if approved else TradeStatus.CANCELLED
            await self.data_layer.update_trade_status(
                trade_id=trade_id,
                status=new_status
            )
            
            # Log to audit trail
            await self.audit_logger.log_event(
                event_type="trade_decision",
                user_id=user.user_id,
                data={
                    "trade_id": trade_id,
                    "decision": "approved" if approved else "rejected",
                    "bot_source": "telegram"
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing trade approval: {e}")
            return False
    
    async def _get_performance_data(self, user: UserSession) -> Dict[str, Any]:
        """Get trading performance data for user"""
        try:
            # Get user's trades
            trades = await self.data_layer.get_user_trades(
                user_id=user.user_id,
                limit=100
            )
            
            if not trades:
                return {}
            
            # Calculate metrics
            total_trades = len(trades)
            filled_trades = [t for t in trades if t.status == TradeStatus.SETTLED]
            won_trades = [t for t in filled_trades if hasattr(t, 'actual_profit') and t.actual_profit > 0]
            
            win_rate = (len(won_trades) / len(filled_trades) * 100) if filled_trades else 0
            
            total_profit = sum(
                float(t.actual_profit or 0) for t in filled_trades
                if hasattr(t, 'actual_profit')
            )
            
            # Daily performance (last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            recent_trades = [
                t for t in filled_trades 
                if t.created_at >= cutoff_date
            ]
            
            return {
                'total_trades': total_trades,
                'filled_trades': len(filled_trades),
                'won_trades': len(won_trades),
                'win_rate': win_rate,
                'total_profit': total_profit,
                'recent_trades': recent_trades,
                'average_profit_per_trade': total_profit / len(filled_trades) if filled_trades else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting performance data: {e}")
            return {}
    
    async def _create_performance_chart(self, performance_data: Dict[str, Any]) -> io.BytesIO:
        """Create performance chart image"""
        try:
            # Create figure
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            fig.suptitle('Trading Performance Report', fontsize=16, fontweight='bold')
            
            # Chart 1: Win Rate and Profit
            categories = ['Won Trades', 'Lost Trades']
            won_trades = performance_data.get('won_trades', 0)
            lost_trades = performance_data.get('filled_trades', 0) - won_trades
            
            ax1.pie([won_trades, lost_trades], labels=categories, autopct='%1.1f%%',
                   colors=['#00C851', '#FF4444'], startangle=90)
            ax1.set_title('Trade Results Distribution')
            
            # Chart 2: Performance Metrics
            metrics = ['Total Trades', 'Win Rate (%)', 'Avg Profit ($)']
            values = [
                performance_data.get('total_trades', 0),
                performance_data.get('win_rate', 0),
                performance_data.get('average_profit_per_trade', 0)
            ]
            
            bars = ax2.bar(metrics, values, color=['#4285F4', '#34A853', '#FBBC04'])
            ax2.set_title('Key Performance Metrics')
            ax2.set_ylabel('Value')
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.1f}', ha='center', va='bottom')
            
            plt.tight_layout()
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            plt.close(fig)
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error creating performance chart: {e}")
            return io.BytesIO()
    
    def _format_performance_text(self, performance_data: Dict[str, Any]) -> str:
        """Format performance data as text"""
        return f"""
📊 *Performance Report*

*Trading Overview:*
• Total Trades: {performance_data.get('total_trades', 0)}
• Filled Trades: {performance_data.get('filled_trades', 0)}
• Winning Trades: {performance_data.get('won_trades', 0)}
• Win Rate: {performance_data.get('win_rate', 0):.1f}%

*Profitability:*
• Total Profit: ${performance_data.get('total_profit', 0):,.2f}
• Average Profit per Trade: ${performance_data.get('average_profit_per_trade', 0):,.2f}

*Performance Rating:* {'🌟 Excellent' if performance_data.get('win_rate', 0) > 70 else '✅ Good' if performance_data.get('win_rate', 0) > 50 else '⚠️ Needs Improvement'}
        """
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get system status information"""
        try:
            # Get database status
            db_connected = await self.data_layer.health_check()
            
            # Get opportunity counts
            active_opportunities = len(await self.data_layer.get_opportunities(limit=1))
            
            # Get pending trades
            pending_trades = len(await self.data_layer.get_user_trades(
                status_filter=[TradeStatus.PENDING]
            ))
            
            # Get risk alerts
            risk_alerts = await self.data_layer.get_risk_alerts(
                limit=1,  # Just check if any exist
                active_only=True
            )
            
            return {
                'db_connected': db_connected,
                'active_opportunities': active_opportunities,
                'pending_trades': pending_trades,
                'running_scanners': 3,  # This would come from scanner status
                'last_sync': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'risk_alerts': len(risk_alerts),
                'circuit_breakers': 0  # This would come from circuit breaker status
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'db_connected': False}
    
    def _format_uptime(self) -> str:
        """Format bot uptime"""
        uptime = datetime.utcnow() - self.start_time
        days, remainder = divmod(int(uptime.total_seconds()), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    # Settings Methods
    
    async def _toggle_notifications(self, update: Update, context: CallbackContext) -> None:
        """Toggle notifications on/off"""
        query = update.callback_query
        user = self._get_user_session(query.from_user.id)
        
        if not user:
            return
        
        current = user.preferences.get('notifications_enabled', True)
        user.preferences['notifications_enabled'] = not current
        
        status = "enabled" if user.preferences['notifications_enabled'] else "disabled"
        
        await query.edit_message_text(f"🔔 Notifications {status}!")
    
    async def _show_threshold_settings(self, update: Update, context: CallbackContext) -> None:
        """Show profit threshold settings"""
        query = update.callback_query
        user = self._get_user_session(query.from_user.id)
        
        if not user:
            return
        
        threshold_text = f"""
💰 *Profit Threshold Settings*

Current minimum profit: {user.preferences.get('min_profit_threshold', 1.0)}%
Current maximum stake: ${user.preferences.get('max_stake_limit', 10000):,.2f}

Commands to adjust:
• Set minimum profit: Send percentage (e.g., "2.5")
• Set maximum stake: Send amount (e.g., "5000")
        """
        
        await query.edit_message_text(
            threshold_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_risk_settings(self, update: Update, context: CallbackContext) -> None:
        """Show risk settings"""
        query = update.callback_query
        user = self._get_user_session(query.from_user.id)
        
        if not user:
            return
        
        risk_tiers = user.preferences.get('risk_tier_filter', ['TIER_A', 'TIER_B'])
        
        risk_text = f"""
⚠️ *Risk Settings*

Current risk tiers: {', '.join(risk_tiers)}

Available tiers:
• TIER_A - Lowest risk, highest confidence
• TIER_B - Low risk
• TIER_C - Medium risk
• TIER_D - High risk

Send tier names to toggle (e.g., "TIER_C TIER_D")
        """
        
        await query.edit_message_text(
            risk_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _show_sports_settings(self, update: Update, context: CallbackContext) -> None:
        """Show sports filter settings"""
        query = update.callback_query
        user = self._get_user_session(query.from_user.id)
        
        if not user:
            return
        
        sports_filter = user.preferences.get('sports_filter', [])
        sports_text = "All sports" if not sports_filter else ', '.join(sports_filter)
        
        sports_list = list(Sport)
        
        sports_text_block = f"""
🏆 *Sports Filter Settings*

Currently filtered: {sports_text}

Available sports:
{', '.join([s.title() for s in sports_list])}

Send sport names to filter (e.g., "football basketball")
Send "all" to include all sports
        """
        
        await query.edit_message_text(
            sports_text_block,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _toggle_auto_approve(self, update: Update, context: CallbackContext) -> None:
        """Toggle auto-approve for Tier A opportunities"""
        query = update.callback_query
        user = self._get_user_session(query.from_user.id)
        
        if not user:
            return
        
        current = user.preferences.get('auto_approve_tier_a', False)
        user.preferences['auto_approve_tier_a'] = not current
        
        status = "enabled" if user.preferences['auto_approve_tier_a'] else "disabled"
        
        await query.edit_message_text(f"🤖 Auto-approve Tier A {status}!")
    
    async def _toggle_alert_type(self, user: UserSession, alert_type: str) -> None:
        """Toggle specific alert type"""
        current = user.preferences.get(alert_type, True)
        user.preferences[alert_type] = not current
    
    async def _enable_all_alerts(self, user: UserSession) -> None:
        """Enable all alert types"""
        for alert_type in ['opportunity_alerts', 'trade_updates', 'risk_warnings', 'performance_reports']:
            user.preferences[alert_type] = True
    
    async def _disable_all_alerts(self, user: UserSession) -> None:
        """Disable all alert types"""
        for alert_type in ['opportunity_alerts', 'trade_updates', 'risk_warnings', 'performance_reports']:
            user.preferences[alert_type] = False
    
    # Menu Input Handlers
    
    async def _handle_menu_input(self, update: Update, context: CallbackContext) -> None:
        """Handle text input in menu state"""
        # For now, just acknowledge the input
        await update.message.reply_text("Please use the menu buttons for navigation.")
    
    async def _handle_opportunities_input(self, update: Update, context: CallbackContext) -> None:
        """Handle input while viewing opportunities"""
        # Implementation for opportunity filtering/searching
        pass
    
    async def _handle_approval_input(self, update: Update, context: CallbackContext) -> None:
        """Handle input during approval process"""
        # Implementation for approval workflows
        pass
    
    async def _handle_settings_input(self, update: Update, context: CallbackContext) -> None:
        """Handle settings configuration input"""
        user = self._get_user_session(update.effective_user.id)
        if not user:
            return
        
        text = update.message.text.strip()
        
        # Parse setting changes
        if text.replace('.', '').replace('-', '').isdigit():
            # Likely a numeric setting
            value = float(text)
            if value <= 10:  # Assume profit percentage
                user.preferences['min_profit_threshold'] = value
                await update.message.reply_text(f"✅ Minimum profit threshold set to {value}%")
            else:  # Assume stake amount
                user.preferences['max_stake_limit'] = value
                await update.message.reply_text(f"✅ Maximum stake limit set to ${value:,.2f}")
        else:
            # Handle risk tier changes
            tiers = text.upper().split()
            valid_tiers = [t for t in tiers if t in ['TIER_A', 'TIER_B', 'TIER_C', 'TIER_D']]
            if valid_tiers:
                user.preferences['risk_tier_filter'] = valid_tiers
                await update.message.reply_text(f"✅ Risk tiers set to: {', '.join(valid_tiers)}")
    
    async def _handle_alerts_input(self, update: Update, context: CallbackContext) -> None:
        """Handle alert configuration input"""
        # Implementation for detailed alert configuration
        pass
    
    # Background Workers
    
    async def _notification_worker(self) -> None:
        """Background worker for sending notifications"""
        while True:
            try:
                # Get notification from queue
                notification = await self.notification_queue.get()
                
                # Send notification to users
                await self._send_notification(notification)
                
                # Mark task as done
                self.notification_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in notification worker: {e}")
                await asyncio.sleep(1)
    
    async def _send_notification(self, notification: BotNotification) -> None:
        """Send notification to user"""
        try:
            user = self._get_user_session(int(notification.user_id))
            if not user or not user.authorized:
                return
            
            # Check user preferences
            if not user.preferences.get('notifications_enabled', True):
                return
            
            # Format message
            message_text = f"*{notification.title}*\n\n{notification.content}"
            
            # Add buttons if provided
            reply_markup = None
            if notification.buttons:
                keyboard = [
                    [InlineKeyboardButton(btn['text'], callback_data=btn['callback_data'])]
                    for btn in notification.buttons
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send message
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            
            self.total_notifications_sent += 1
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            self.error_count += 1
    
    async def _cleanup_worker(self) -> None:
        """Background worker for cleanup tasks"""
        while True:
            try:
                # Clean up expired user sessions (24 hours inactive)
                cutoff = datetime.utcnow() - timedelta(hours=24)
                
                with self.user_lock:
                    expired_users = [
                        uid for uid, session in self.users.items()
                        if session.last_activity < cutoff
                    ]
                    
                    for uid in expired_users:
                        del self.users[uid]
                        logger.info(f"Cleaned up expired session for user {uid}")
                
                # Clean up rate limit entries
                current_time = time.time()
                with self.rate_limit_lock:
                    for key in list(self.rate_limits.keys()):
                        self.rate_limits[key] = [
                            entry for entry in self.rate_limits[key]
                            if current_time < entry.reset_time
                        ]
                        
                        # Remove empty entries
                        if not self.rate_limits[key]:
                            del self.rate_limits[key]
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                await asyncio.sleep(300)
    
    # Public Interface Methods
    
    async def send_opportunity_alert(self, opportunity: ArbitrageOpportunity) -> None:
        """Send opportunity alert to authorized users"""
        notification = BotNotification(
            notification_id=str(uuid4()),
            user_id="broadcast",  # Special broadcast user
            type=MessageType.NOTIFICATION,
            title=f"🚨 New {opportunity.sport.title()} Opportunity!",
            content=f"""
💰 Profit: {opportunity.profit_margin:.2f}%
💵 Stake: ${opportunity.total_stake:,.2f}
🎯 Expected: ${opportunity.expected_profit:,.2f}
⚠️ Risk: {opportunity.risk_tier.title()}

Event: {opportunity.event_name}
Market: {opportunity.market_type}
            """,
            data={'opportunity_id': str(opportunity.id)},
            priority=NotificationPriority.HIGH,
            timestamp=datetime.utcnow(),
            buttons=[
                {'text': '✅ Approve Now', 'callback_data': f"approve:{opportunity.id}:approve"},
                {'text': '❌ Reject', 'callback_data': f"approve:{opportunity.id}:reject"}
            ]
        )
        
        # Queue notification
        await self.notification_queue.put(notification)
    
    async def send_trade_update(self, trade: Trade, update_type: str) -> None:
        """Send trade status update"""
        user_id = trade.user_id  # Get user ID from trade
        
        notification = BotNotification(
            notification_id=str(uuid4()),
            user_id=user_id,
            type=MessageType.UPDATE,
            title=f"📊 Trade Update: {update_type}",
            content=f"""
Trade ID: {trade.id}
Status: {trade.status.value.title()}
Total Stake: ${trade.total_stake:,.2f}
Expected Profit: ${trade.expected_profit:,.2f}

Updated: {trade.updated_at.strftime('%H:%M:%S UTC')}
            """,
            data={'trade_id': str(trade.id), 'status': trade.status.value},
            priority=NotificationPriority.MEDIUM,
            timestamp=datetime.utcnow()
        )
        
        await self.notification_queue.put(notification)
    
    async def send_risk_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send risk alert to relevant users"""
        # Get users who want risk warnings
        risk_users = [
            session for session in self.users.values()
            if session.authorized and session.preferences.get('risk_warnings', True)
        ]
        
        for user in risk_users:
            notification = BotNotification(
                notification_id=str(uuid4()),
                user_id=user.user_id,
                type=MessageType.NOTIFICATION,
                title="⚠️ Risk Alert",
                content=alert_data.get('description', 'Risk threshold exceeded'),
                data=alert_data,
                priority=NotificationPriority.CRITICAL,
                timestamp=datetime.utcnow()
            )
            
            await self.notification_queue.put(notification)
    
    async def run(self) -> None:
        """Run the bot (blocking call)"""
        if not self.application:
            await self.initialize()
        
        logger.info("Starting ARBitech Telegram Bot...")
        await self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    
    # Error Handling
    
    async def _handle_error(self, update: Update, context: CallbackContext) -> None:
        """Handle errors in the bot"""
        logger.error(f"Update {update} caused error {context.error}")
        
        self.error_count += 1
        
        # Log detailed error information
        error_data = {
            'error_type': type(context.error).__name__,
            'error_message': str(context.error),
            'traceback': traceback.format_exc(),
            'update_data': update.to_dict() if update else None
        }
        
        # Send error notification to admin users
        admin_users = [
            session for session in self.users.values()
            if session.role == UserRole.ADMIN and session.authorized
        ]
        
        for user in admin_users:
            try:
                await self.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"🚨 *Bot Error*\n\nError: {error_data['error_message']}\n\nCheck logs for details.",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"Failed to send error notification: {e}")
    
    # Health Check
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform bot health check"""
        return {
            'status': 'healthy' if self.error_count < 10 else 'degraded',
            'uptime': self._format_uptime(),
            'active_users': len([u for u in self.users.values() if u.authorized]),
            'total_messages_sent': self.total_messages_sent,
            'total_notifications_sent': self.total_notifications_sent,
            'error_count': self.error_count,
            'queue_size': self.notification_queue.qsize(),
            'last_activity': datetime.utcnow().isoformat()
        }
    
    async def shutdown(self) -> None:
        """Shutdown the bot gracefully"""
        logger.info("Shutting down ARBitech Telegram Bot...")
        
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        self.executor.shutdown(wait=True)
        
        # Log shutdown
        await self.audit_logger.log_event(
            event_type="bot_shutdown",
            user_id="system",
            data={
                "uptime": self._format_uptime(),
                "messages_sent": self.total_messages_sent,
                "notifications_sent": self.total_notifications_sent,
                "errors": self.error_count
            }
        )
        
        logger.info("Bot shutdown complete")


# Factory function for easy initialization
def create_arbitech_bot(token: str) -> ARBITechTelegramBot:
    """
    Create and configure ARBitech Telegram bot.
    
    Args:
        token: Telegram bot token
        
    Returns:
        Configured ARBITechTelegramBot instance
    """
    # Initialize data layer (this would use environment variables in production)
    data_layer = SupabaseDataLayer()
    
    # Create bot
    bot = ARBITechTelegramBot(token=token, data_layer=data_layer)
    
    return bot


# Main entry point for standalone execution
if __name__ == "__main__":
    import os
    
    # Get bot token from environment or config
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
        print("Please set your Telegram bot token: export TELEGRAM_BOT_TOKEN=your_token")
        exit(1)
    
    # Create and run bot
    bot = create_arbitech_bot(BOT_TOKEN)
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n👋 Shutting down bot...")
        asyncio.run(bot.shutdown())
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        exit(1)
