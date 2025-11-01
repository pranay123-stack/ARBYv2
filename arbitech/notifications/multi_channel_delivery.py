"""
Multi-Channel Delivery Orchestrator for ARBitech System
Comprehensive notification delivery system with intelligent routing,
priority handling, failover mechanisms, and analytics tracking.
"""

import asyncio
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
import uuid
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import os
import sys

# Add the parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.audit_logger import AuditLogger
from storage.models import NotificationChannel, NotificationPriority, NotificationType
from risk.safety_pipeline import SafetyPipeline


class DeliveryStatus(Enum):
    """Status of notification delivery attempts."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    EXPIRED = "expired"
    FAILED_PERMANENTLY = "failed_permanently"


class ChannelType(Enum):
    """Available notification channels."""
    TELEGRAM = "telegram"
    EMAIL = "email"
    DASHBOARD = "dashboard"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"


class UrgencyLevel(Enum):
    """Notification urgency levels for intelligent routing."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BATCH = 5


@dataclass
class UserPreferences:
    """User notification preferences."""
    user_id: str
    preferred_channels: List[ChannelType]
    backup_channels: List[ChannelType]
    quiet_hours_start: Optional[str] = None  # HH:MM format
    quiet_hours_end: Optional[str] = None    # HH:MM format
    timezone: str = "UTC"
    language: str = "en"
    emergency_override: bool = False


@dataclass
class DeliveryMetrics:
    """Metrics for tracking delivery performance."""
    notification_id: str
    channel_type: ChannelType
    attempt_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: DeliveryStatus = DeliveryStatus.PENDING
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    retry_delay_seconds: Optional[float] = None


@dataclass
class NotificationRequest:
    """Request for notification delivery."""
    id: str
    user_id: str
    title: str
    message: str
    notification_type: NotificationType
    priority: UrgencyLevel
    channels: List[ChannelType]
    user_preferences: UserPreferences
    created_at: datetime
    expires_at: Optional[datetime] = None
    retry_config: Optional[Dict] = None
    metadata: Optional[Dict] = None
    criticality_score: float = 0.0  # For emergency escalation


class NotificationChannel:
    """Base class for all notification channels."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"notification.{self.__class__.__name__.lower()}")
        self.metrics: List[DeliveryMetrics] = []
        self.lock = threading.Lock()

    async def send(self, request: NotificationRequest, metrics: DeliveryMetrics) -> bool:
        """Send notification through this channel. Override in subclasses."""
        raise NotImplementedError

    def is_available(self) -> bool:
        """Check if channel is available for delivery."""
        return True

    def get_max_retries(self) -> int:
        """Get maximum retry attempts for this channel."""
        return self.config.get('max_retries', 3)

    def get_retry_delay(self, attempt: int) -> float:
        """Get retry delay in seconds using exponential backoff."""
        base_delay = self.config.get('retry_base_delay', 1.0)
        return base_delay * (2 ** attempt)

    def record_metrics(self, metrics: DeliveryMetrics):
        """Record delivery metrics."""
        with self.lock:
            self.metrics.append(metrics)


class TelegramChannel(NotificationChannel):
    """Telegram notification channel."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_token = config.get('bot_token')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def send(self, request: NotificationRequest, metrics: DeliveryMetrics) -> bool:
        """Send notification via Telegram."""
        try:
            payload = {
                'chat_id': request.user_id,
                'text': f"*{request.title}*\n\n{request.message}",
                'parse_mode': 'Markdown'
            }

            async with asyncio.timeout(30):
                response = requests.post(self.api_url, json=payload, timeout=10)
                
            metrics.end_time = datetime.now()
            metrics.status = DeliveryStatus.DELIVERED if response.status_code == 200 else DeliveryStatus.FAILED
            metrics.latency_ms = (metrics.end_time - metrics.start_time).total_seconds() * 1000
            
            if response.status_code != 200:
                metrics.error_message = f"Telegram API error: {response.status_code}"
                
            return response.status_code == 200
            
        except Exception as e:
            metrics.end_time = datetime.now()
            metrics.status = DeliveryStatus.FAILED
            metrics.error_message = str(e)
            self.logger.error(f"Telegram delivery failed for {request.id}: {e}")
            return False


class EmailChannel(NotificationChannel):
    """Email notification channel."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.from_email = config.get('from_email')

    async def send(self, request: NotificationRequest, metrics: DeliveryMetrics) -> bool:
        """Send notification via email."""
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = request.user_id
            msg['Subject'] = request.title
            
            # HTML body
            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                        .content {{ margin: 20px 0; line-height: 1.6; }}
                        .priority-{request.priority.name.lower()} {{ color: red; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h2>{request.title}</h2>
                        <p class="priority-{request.priority.name.lower()}">
                            Priority: {request.priority.name}
                        </p>
                        <p>Notification ID: {request.id}</p>
                    </div>
                    <div class="content">
                        {request.message.replace(chr(10), '<br>')}
                    </div>
                    <hr>
                    <small>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            metrics.end_time = datetime.now()
            metrics.status = DeliveryStatus.DELIVERED
            metrics.latency_ms = (metrics.end_time - metrics.start_time).total_seconds() * 1000
            return True
            
        except Exception as e:
            metrics.end_time = datetime.now()
            metrics.status = DeliveryStatus.FAILED
            metrics.error_message = str(e)
            self.logger.error(f"Email delivery failed for {request.id}: {e}")
            return False


class DashboardChannel(NotificationChannel):
    """Dashboard notification channel."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_endpoint = config.get('api_endpoint', '/api/notifications')

    async def send(self, request: NotificationRequest, metrics: DeliveryMetrics) -> bool:
        """Send notification to dashboard."""
        try:
            payload = {
                'user_id': request.user_id,
                'title': request.title,
                'message': request.message,
                'type': request.notification_type.value,
                'priority': request.priority.value,
                'timestamp': datetime.now().isoformat(),
                'id': request.id
            }

            # Simulate dashboard API call (replace with actual implementation)
            async with asyncio.timeout(10):
                await asyncio.sleep(0.1)  # Simulated delay
                
            metrics.end_time = datetime.now()
            metrics.status = DeliveryStatus.DELIVERED
            metrics.latency_ms = (metrics.end_time - metrics.start_time).total_seconds() * 1000
            return True
            
        except Exception as e:
            metrics.end_time = datetime.now()
            metrics.status = DeliveryStatus.FAILED
            metrics.error_message = str(e)
            self.logger.error(f"Dashboard delivery failed for {request.id}: {e}")
            return False


class SMSChannel(NotificationChannel):
    """SMS notification channel (backup)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.sms_provider = config.get('provider', 'twilio')

    async def send(self, request: NotificationRequest, metrics: DeliveryMetrics) -> bool:
        """Send notification via SMS."""
        try:
            # SMS providers implementation would go here
            # For now, simulate SMS delivery
            if not self.is_available():
                raise Exception("SMS provider unavailable")
                
            message = f"{request.title}: {request.message[:160]}"  # SMS length limit
            
            # Simulate SMS API call
            async with asyncio.timeout(15):
                await asyncio.sleep(0.1)
                
            metrics.end_time = datetime.now()
            metrics.status = DeliveryStatus.DELIVERED
            metrics.latency_ms = (metrics.end_time - metrics.start_time).total_seconds() * 1000
            return True
            
        except Exception as e:
            metrics.end_time = datetime.now()
            metrics.status = DeliveryStatus.FAILED
            metrics.error_message = str(e)
            self.logger.error(f"SMS delivery failed for {request.id}: {e}")
            return False


class ChannelSelector:
    """Intelligent channel selection based on urgency and preferences."""

    @staticmethod
    def select_primary_channel(request: NotificationRequest, available_channels: List[ChannelType]) -> Optional[ChannelType]:
        """Select the primary channel for delivery."""
        # Priority-based channel selection
        if request.priority == UrgencyLevel.CRITICAL:
            # Critical: Use multiple channels for redundancy
            if ChannelType.SMS in available_channels:
                return ChannelType.SMS
            elif ChannelType.TELEGRAM in available_channels:
                return ChannelType.TELEGRAM
            elif ChannelType.EMAIL in available_channels:
                return ChannelType.EMAIL
        
        elif request.priority == UrgencyLevel.HIGH:
            if ChannelType.TELEGRAM in available_channels:
                return ChannelType.TELEGRAM
            elif ChannelType.EMAIL in available_channels:
                return ChannelType.EMAIL
        
        elif request.priority == UrgencyLevel.MEDIUM:
            if ChannelType.EMAIL in available_channels:
                return ChannelType.EMAIL
            elif ChannelType.DASHBOARD in available_channels:
                return ChannelType.DASHBOARD
        
        elif request.priority == UrgencyLevel.LOW:
            if ChannelType.DASHBOARD in available_channels:
                return ChannelType.DASHBOARD
            elif ChannelType.EMAIL in available_channels:
                return ChannelType.EMAIL
        
        elif request.priority == UrgencyLevel.BATCH:
            return ChannelType.DASHBOARD
        
        # Fallback: first available channel
        return available_channels[0] if available_channels else None

    @staticmethod
    def get_failover_channels(primary_channel: ChannelType, available_channels: List[ChannelType]) -> List[ChannelType]:
        """Get failover channels for redundancy."""
        failover_order = {
            ChannelType.SMS: [ChannelType.TELEGRAM, ChannelType.EMAIL],
            ChannelType.TELEGRAM: [ChannelType.EMAIL, ChannelType.SMS],
            ChannelType.EMAIL: [ChannelType.DASHBOARD, ChannelType.TELEGRAM],
            ChannelType.DASHBOARD: [ChannelType.EMAIL],
        }
        
        primary_failovers = failover_order.get(primary_channel, [])
        return [ch for ch in primary_failovers if ch in available_channels]


class DeliveryQueue:
    """Priority-based notification queue with smart scheduling."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.queues = {
            UrgencyLevel.CRITICAL: asyncio.Queue(maxsize=max_size),
            UrgencyLevel.HIGH: asyncio.Queue(maxsize=max_size),
            UrgencyLevel.MEDIUM: asyncio.Queue(maxsize=max_size),
            UrgencyLevel.LOW: asyncio.Queue(maxsize=max_size),
            UrgencyLevel.BATCH: asyncio.Queue(maxsize=max_size),
        }
        self.processing = set()
        self.lock = asyncio.Lock()

    async def enqueue(self, request: NotificationRequest) -> bool:
        """Add notification to appropriate queue."""
        try:
            await self.queues[request.priority].put(request)
            return True
        except asyncio.QueueFull:
            return False

    async def dequeue(self) -> Optional[NotificationRequest]:
        """Get highest priority notification (critical first)."""
        for priority in UrgencyLevel:
            if not self.queues[priority].empty():
                return await self.queues[priority].get()
        return None

    async def size(self) -> Dict[UrgencyLevel, int]:
        """Get queue sizes."""
        return {priority: q.qsize() for priority, q in self.queues.items()}

    async def processing_ids(self) -> set:
        """Get IDs of notifications currently being processed."""
        async with self.lock:
            return self.processing.copy()

    async def add_processing(self, notification_id: str):
        """Mark notification as being processed."""
        async with self.lock:
            self.processing.add(notification_id)

    async def remove_processing(self, notification_id: str):
        """Remove notification from processing set."""
        async with self.lock:
            self.processing.discard(notification_id)


class BatchProcessor:
    """Handles batch delivery for non-urgent notifications."""

    def __init__(self, batch_size: int = 50, batch_interval: int = 300):
        self.batch_size = batch_size
        self.batch_interval = batch_interval  # seconds
        self.batch_buffer: List[NotificationRequest] = []
        self.last_batch_time = time.time()

    async def add_to_batch(self, request: NotificationRequest) -> bool:
        """Add notification to batch (only for non-urgent)."""
        if request.priority in [UrgencyLevel.LOW, UrgencyLevel.BATCH]:
            self.batch_buffer.append(request)
            
            if len(self.batch_buffer) >= self.batch_size or \
               (time.time() - self.last_batch_time) >= self.batch_interval:
                await self.process_batch()
            
            return True
        return False

    async def process_batch(self):
        """Process all buffered notifications."""
        if not self.batch_buffer:
            return

        batch = self.batch_buffer.copy()
        self.batch_buffer.clear()
        self.last_batch_time = time.time()

        # Process batch in parallel
        tasks = []
        for request in batch:
            task = asyncio.create_task(
                process_notification_delivery(request)
            )
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)


class AnalyticsTracker:
    """Tracks delivery performance and analytics."""

    def __init__(self, db_path: str = "delivery_analytics.db"):
        self.db_path = db_path
        self.init_database()
        self.channel_performance: Dict[ChannelType, List[float]] = defaultdict(list)
        self.delivery_times: List[float] = []
        self.success_rates: Dict[ChannelType, float] = {}

    def init_database(self):
        """Initialize analytics database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS delivery_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_id TEXT,
                    channel_type TEXT,
                    priority TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    latency_ms REAL,
                    status TEXT,
                    attempt_number INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def record_delivery(self, metrics: DeliveryMetrics):
        """Record delivery metrics."""
        # Update in-memory stats
        if metrics.latency_ms:
            self.channel_performance[metrics.channel_type].append(metrics.latency_ms)
            self.delivery_times.append(metrics.latency_ms)

        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO delivery_analytics 
                (notification_id, channel_type, priority, start_time, end_time, 
                 latency_ms, status, attempt_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.notification_id,
                metrics.channel_type.value,
                "",  # Priority would be stored separately
                metrics.start_time,
                metrics.end_time,
                metrics.latency_ms,
                metrics.status.value,
                metrics.attempt_number
            ))

    def get_channel_performance(self, channel: ChannelType, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for a channel."""
        latencies = self.channel_performance.get(channel, [])
        
        if not latencies:
            return {
                "count": 0,
                "avg_latency": 0,
                "min_latency": 0,
                "max_latency": 0,
                "success_rate": 0
            }

        return {
            "count": len(latencies),
            "avg_latency": sum(latencies) / len(latencies),
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "success_rate": self.success_rates.get(channel, 0.0)
        }

    def get_overall_analytics(self) -> Dict[str, Any]:
        """Get overall delivery analytics."""
        total_deliveries = len(self.delivery_times)
        avg_latency = sum(self.delivery_times) / total_deliveries if total_deliveries else 0
        
        return {
            "total_deliveries": total_deliveries,
            "avg_latency_ms": avg_latency,
            "total_channels": len(self.channel_performance),
            "success_rates": dict(self.success_rates)
        }


class MultiChannelDeliveryOrchestrator:
    """
    Main orchestrator for multi-channel notification delivery.
    Handles intelligent routing, failover, retry logic, and monitoring.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.channel_selector = ChannelSelector()
        self.delivery_queue = DeliveryQueue()
        self.batch_processor = BatchProcessor()
        self.analytics = AnalyticsTracker()
        self.audit_logger = AuditLogger()
        
        # Initialize channels
        self.channels: Dict[ChannelType, NotificationChannel] = {}
        self._initialize_channels()
        
        # Running state
        self.running = False
        self.worker_tasks: List[asyncio.Task] = []
        self.delivery_lock = asyncio.Lock()

    def _initialize_channels(self):
        """Initialize notification channels."""
        channel_configs = self.config.get('channels', {})
        
        if 'telegram' in channel_configs:
            self.channels[ChannelType.TELEGRAM] = TelegramChannel(channel_configs['telegram'])
        
        if 'email' in channel_configs:
            self.channels[ChannelType.EMAIL] = EmailChannel(channel_configs['email'])
        
        if 'dashboard' in channel_configs:
            self.channels[ChannelType.DASHBOARD] = DashboardChannel(channel_configs['dashboard'])
        
        if 'sms' in channel_configs:
            self.channels[ChannelType.SMS] = SMSChannel(channel_configs['sms'])

    async def start(self):
        """Start the delivery orchestrator."""
        self.logger.info("Starting Multi-Channel Delivery Orchestrator")
        self.running = True
        
        # Start worker tasks
        for i in range(self.config.get('worker_threads', 4)):
            task = asyncio.create_task(self._delivery_worker(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        # Start batch processor
        batch_task = asyncio.create_task(self._batch_processor_worker())
        self.worker_tasks.append(batch_task)
        
        self.logger.info(f"Started {len(self.worker_tasks)} worker threads")

    async def stop(self):
        """Stop the delivery orchestrator."""
        self.logger.info("Stopping Multi-Channel Delivery Orchestrator")
        self.running = False
        
        # Cancel all worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()

    async def send_notification(self, request: NotificationRequest) -> str:
        """Send notification through appropriate channels."""
        # Log the notification request
        await self.audit_logger.log_event(
            "notification.request",
            {"request": asdict(request)}
        )
        
        # Check if it's batchable
        if await self.batch_processor.add_to_batch(request):
            return f"batch:{request.id}"
        
        # Add to delivery queue
        await self.delivery_queue.enqueue(request)
        return request.id

    async def _delivery_worker(self, worker_name: str):
        """Worker thread for processing delivery queue."""
        self.logger.info(f"Starting delivery worker: {worker_name}")
        
        while self.running:
            try:
                # Get next notification from queue
                request = await self.delivery_queue.dequeue()
                if not request:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process notification
                await self._process_notification(request, worker_name)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)

    async def _batch_processor_worker(self):
        """Worker for processing batch notifications."""
        while self.running:
            try:
                # Process any pending batch
                await self.batch_processor.process_batch()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Batch processor error: {e}")
                await asyncio.sleep(5)

    async def _process_notification(self, request: NotificationRequest, worker_name: str):
        """Process a single notification with failover and retry logic."""
        notification_id = request.id
        
        try:
            # Mark as processing
            await self.delivery_queue.add_processing(notification_id)
            
            # Get available channels
            available_channels = [ch for ch, instance in self.channels.items() 
                                if instance.is_available()]
            
            if not available_channels:
                self.logger.error(f"No channels available for notification {notification_id}")
                return
            
            # Select primary and failover channels
            primary_channel = self.channel_selector.select_primary_channel(request, available_channels)
            failover_channels = self.channel_selector.get_failover_channels(
                primary_channel, available_channels
            )
            
            if not primary_channel:
                self.logger.error(f"Could not select channel for notification {notification_id}")
                return
            
            # Attempt delivery with retry logic
            success = await self._deliver_with_failover(request, primary_channel, failover_channels)
            
            if success:
                self.logger.info(f"Successfully delivered notification {notification_id}")
            else:
                self.logger.error(f"Failed to deliver notification {notification_id}")
                
        finally:
            await self.delivery_queue.remove_processing(notification_id)

    async def _deliver_with_failover(self, request: NotificationRequest, 
                                   primary: ChannelType, 
                                   failover_channels: List[ChannelType]) -> bool:
        """Attempt delivery with failover mechanism."""
        attempt = 0
        max_attempts = sum([self.channels[ch].get_max_retries() for ch in [primary] + failover_channels])
        
        channels_to_try = [primary] + failover_channels
        
        while attempt < max_attempts:
            current_channel = channels_to_try[attempt % len(channels_to_try)]
            channel_instance = self.channels[current_channel]
            
            # Create metrics
            metrics = DeliveryMetrics(
                notification_id=request.id,
                channel_type=current_channel,
                attempt_number=attempt + 1,
                start_time=datetime.now(),
                status=DeliveryStatus.IN_PROGRESS
            )
            
            # Attempt delivery
            success = await channel_instance.send(request, metrics)
            
            # Record metrics
            self.analytics.record_delivery(metrics)
            channel_instance.record_metrics(metrics)
            
            if success:
                await self.audit_logger.log_event(
                    "notification.delivered",
                    {
                        "notification_id": request.id,
                        "channel": current_channel.value,
                        "attempts": attempt + 1,
                        "metrics": asdict(metrics)
                    }
                )
                return True
            
            # Calculate retry delay
            if attempt < max_attempts - 1:
                delay = channel_instance.get_retry_delay(attempt)
                await asyncio.sleep(delay)
                metrics.status = DeliveryStatus.RETRYING
                metrics.retry_delay_seconds = delay
            
            attempt += 1
        
        # All attempts failed
        await self.audit_logger.log_event(
            "notification.failed",
            {
                "notification_id": request.id,
                "channels_attempted": [ch.value for ch in channels_to_try],
                "total_attempts": max_attempts
            }
        )
        
        return False

    async def get_delivery_status(self, notification_id: str) -> Dict[str, Any]:
        """Get delivery status for a notification."""
        # Check analytics database
        with sqlite3.connect(self.analytics.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM delivery_analytics WHERE notification_id = ?",
                (notification_id,)
            )
            rows = cursor.fetchall()
            
        status = {
            "notification_id": notification_id,
            "attempts": len(rows),
            "delivered": False,
            "channels_attempted": [],
            "total_latency_ms": 0,
            "latest_status": "pending"
        }
        
        for row in rows:
            status["channels_attempted"].append(row[2])
            if row[7] == "delivered":
                status["delivered"] = True
            status["total_latency_ms"] += row[6] or 0
            status["latest_status"] = row[7]
        
        return status

    async def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive delivery analytics."""
        overall = self.analytics.get_overall_analytics()
        
        channel_stats = {}
        for channel_type in ChannelType:
            if channel_type in self.channels:
                channel_stats[channel_type.value] = self.analytics.get_channel_performance(channel_type)
        
        queue_sizes = await self.delivery_queue.size()
        processing_ids = await self.delivery_queue.processing_ids()
        
        return {
            "overall": overall,
            "channels": channel_stats,
            "queue_sizes": {k.value: v for k, v in queue_sizes.items()},
            "currently_processing": len(processing_ids),
            "system_status": "running" if self.running else "stopped"
        }

    async def emergency_escalation(self, request: NotificationRequest):
        """Emergency escalation protocol for critical notifications."""
        self.logger.warning(f"EMERGENCY ESCALATION for notification {request.id}")
        
        # Bypass normal queue processing
        emergency_channel_list = [ChannelType.SMS, ChannelType.TELEGRAM, ChannelType.EMAIL]
        available_emergency = [ch for ch in emergency_channel_list if ch in self.channels]
        
        # Send through ALL available channels simultaneously
        tasks = []
        for channel_type in available_emergency:
            channel_instance = self.channels[channel_type]
            
            metrics = DeliveryMetrics(
                notification_id=request.id,
                channel_type=channel_type,
                attempt_number=1,
                start_time=datetime.now(),
                status=DeliveryStatus.IN_PROGRESS
            )
            
            task = asyncio.create_task(
                self._emergency_delivery(request, channel_instance, metrics)
            )
            tasks.append(task)
        
        # Wait for all emergency deliveries
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_deliveries = sum(1 for result in results if result is True)
        
        await self.audit_logger.log_event(
            "notification.emergency_escalation",
            {
                "notification_id": request.id,
                "channels_activated": len(available_emergency),
                "successful_deliveries": successful_deliveries,
                "criticality_score": request.criticality_score
            }
        )
        
        return successful_deliveries > 0

    async def _emergency_delivery(self, request: NotificationRequest, 
                                channel: NotificationChannel, 
                                metrics: DeliveryMetrics) -> bool:
        """Emergency delivery with no retry limits."""
        try:
            success = await asyncio.wait_for(
                channel.send(request, metrics),
                timeout=60  # 1 minute timeout for emergency
            )
            
            self.analytics.record_delivery(metrics)
            return success
        except Exception as e:
            self.logger.error(f"Emergency delivery failed for {channel}: {e}")
            metrics.status = DeliveryStatus.FAILED
            metrics.error_message = str(e)
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check health of the delivery system."""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "channels": {},
            "queue": {},
            "issues": []
        }
        
        # Check channels
        for channel_type, channel_instance in self.channels.items():
            if not channel_instance.is_available():
                health_status["issues"].append(f"{channel_type.value} unavailable")
                health_status["status"] = "degraded"
            
            health_status["channels"][channel_type.value] = {
                "available": channel_instance.is_available(),
                "total_attempts": len(channel_instance.metrics),
                "recent_failures": sum(1 for m in channel_instance.metrics 
                                     if m.status == DeliveryStatus.FAILED and 
                                     m.start_time > datetime.now() - timedelta(hours=1))
            }
        
        # Check queue
        queue_sizes = await self.delivery_queue.size()
        total_queue_size = sum(queue_sizes.values())
        
        if total_queue_size > 1000:
            health_status["issues"].append("Queue size critical")
            health_status["status"] = "degraded"
        
        health_status["queue"] = {
            "total_size": total_queue_size,
            "sizes": {k.value: v for k, v in queue_sizes.items()},
            "processing": len(await self.delivery_queue.processing_ids())
        }
        
        return health_status


# Global instance
orchestrator: Optional[MultiChannelDeliveryOrchestrator] = None


async def initialize_orchestrator(config: Dict[str, Any]) -> MultiChannelDeliveryOrchestrator:
    """Initialize the global orchestrator instance."""
    global orchestrator
    orchestrator = MultiChannelDeliveryOrchestrator(config)
    await orchestrator.start()
    return orchestrator


async def process_notification_delivery(request: NotificationRequest) -> bool:
    """Process notification delivery through the orchestrator."""
    if not orchestrator:
        raise RuntimeError("Orchestrator not initialized")
    
    return await orchestrator._process_notification(request, "direct")


async def send_critical_notification(user_id: str, title: str, message: str, 
                                   user_preferences: UserPreferences,
                                   criticality_score: float = 10.0) -> str:
    """Send critical notification with emergency escalation."""
    request = NotificationRequest(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title,
        message=message,
        notification_type=NotificationType.ALERT,
        priority=UrgencyLevel.CRITICAL,
        channels=user_preferences.preferred_channels,
        user_preferences=user_preferences,
        created_at=datetime.now(),
        criticality_score=criticality_score
    )
    
    if criticality_score >= 10.0:
        # Immediate emergency escalation
        await orchestrator.emergency_escalation(request)
        return f"emergency:{request.id}"
    
    return await orchestrator.send_notification(request)


async def send_batch_notification(requests: List[NotificationRequest]) -> List[str]:
    """Send multiple notifications in batch."""
    if not orchestrator:
        raise RuntimeError("Orchestrator not initialized")
    
    results = []
    for request in requests:
        notification_id = await orchestrator.send_notification(request)
        results.append(notification_id)
    
    return results


# Integration with ARBitech phases
async def notify_arbitrage_opportunity(user_id: str, opportunity_data: Dict[str, Any], 
                                     user_preferences: UserPreferences):
    """Notify user of arbitrage opportunity."""
    title = f"Arbitrage Opportunity: {opportunity_data['bookmaker_1']} vs {opportunity_data['bookmaker_2']}"
    message = f"""
    Profitable opportunity detected:
    - Bookmaker 1: {opportunity_data['bookmaker_1']} @ {opportunity_data['odds_1']}
    - Bookmaker 2: {opportunity_data['bookmaker_2']} @ {opportunity_data['odds_2']}
    - Expected Profit: {opportunity_data['profit']:.2f}
    - Stake Required: {opportunity_data['stake']:.2f}
    - Confidence: {opportunity_data['confidence']:.1%}
    """
    
    priority = UrgencyLevel.HIGH if opportunity_data['confidence'] > 0.8 else UrgencyLevel.MEDIUM
    
    request = NotificationRequest(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title,
        message=message,
        notification_type=NotificationType.OPPORTUNITY,
        priority=priority,
        channels=user_preferences.preferred_channels,
        user_preferences=user_preferences,
        created_at=datetime.now(),
        metadata=opportunity_data
    )
    
    return await orchestrator.send_notification(request)


async def notify_risk_alert(user_id: str, alert_data: Dict[str, Any], 
                          user_preferences: UserPreferences):
    """Notify user of risk alert."""
    severity = alert_data.get('severity', 'medium')
    
    if severity == 'critical':
        priority = UrgencyLevel.CRITICAL
        criticality_score = 15.0
    elif severity == 'high':
        priority = UrgencyLevel.HIGH
        criticality_score = 8.0
    else:
        priority = UrgencyLevel.MEDIUM
        criticality_score = 5.0
    
    title = f"Risk Alert: {alert_data.get('alert_type', 'Unknown')}"
    message = f"""
    Risk Alert Detected:
    - Type: {alert_data.get('alert_type')}
    - Severity: {severity.upper()}
    - Description: {alert_data.get('description', 'No description')}
    - Recommended Action: {alert_data.get('action', 'Review immediately')}
    - Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    request = NotificationRequest(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title,
        message=message,
        notification_type=NotificationType.ALERT,
        priority=priority,
        channels=user_preferences.preferred_channels,
        user_preferences=user_preferences,
        created_at=datetime.now(),
        criticality_score=criticality_score,
        metadata=alert_data
    )
    
    return await orchestrator.send_notification(request)


if __name__ == "__main__":
    # Example usage
    async def main():
        # Configuration
        config = {
            "channels": {
                "telegram": {
                    "bot_token": "YOUR_BOT_TOKEN",
                    "max_retries": 3,
                    "retry_base_delay": 1.0
                },
                "email": {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "your_email@gmail.com",
                    "password": "your_password",
                    "from_email": "your_email@gmail.com"
                },
                "dashboard": {
                    "api_endpoint": "/api/notifications"
                },
                "sms": {
                    "provider": "twilio",
                    "api_key": "YOUR_SMS_API_KEY"
                }
            },
            "worker_threads": 4
        }
        
        # Initialize orchestrator
        orch = await initialize_orchestrator(config)
        
        # Example user preferences
        preferences = UserPreferences(
            user_id="user123",
            preferred_channels=[ChannelType.TELEGRAM, ChannelType.EMAIL],
            backup_channels=[ChannelType.SMS]
        )
        
        # Send a notification
        notification_id = await send_critical_notification(
            user_id="user123",
            title="System Alert",
            message="Critical system issue detected!",
            user_preferences=preferences,
            criticality_score=12.0
        )
        
        print(f"Notification sent: {notification_id}")
        
        # Get analytics
        analytics = await orch.get_analytics()
        print(f"Analytics: {json.dumps(analytics, indent=2, default=str)}")
        
        # Health check
        health = await orch.health_check()
        print(f"Health: {json.dumps(health, indent=2, default=str)}")
        
        await orch.stop()
    
    # Run example
    asyncio.run(main())