"""
HITL Approval Handler

Component responsible for managing human approval requests and responses.
Handles request creation, routing, notification, timeout management, and 
response processing with comprehensive audit trails.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Union, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID

from ..storage.models import ArbitrageOpportunity, RiskTier
from ..storage.audit_logger import get_audit_logger, EventType, LogLevel
from ..utils.logger import get_logger


class ApprovalChannel(str, Enum):
    """Channels through which approval requests can be sent."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    DISCORD = "discord"
    SLACK = "slack"
    TELEGRAM = "telegram"
    IN_APP = "in_app"
    API = "api"
    CONSOLE = "console"


class ApprovalAction(str, Enum):
    """Actions that can be taken on approval requests."""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_MORE_INFO = "request_more_info"
    DELEGATE = "delegate"
    ESCALATE = "escalate"
    EXPIRE = "expire"


class ApprovalPriority(str, Enum):
    """Priority levels for approval requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class ApprovalRule:
    """Rules for automatic approval/rejection."""
    rule_id: UUID = field(default_factory=uuid.uuid4)
    name: str = ""
    description: str = ""
    
    # Conditions
    risk_tiers: Set[RiskTier] = field(default_factory=set)
    min_profit_margin: Optional[float] = None
    max_profit_margin: Optional[float] = None
    min_stake: Optional[float] = None
    max_stake: Optional[float] = None
    bookmakers: Set[str] = field(default_factory=set)
    sports: Set[str] = field(default_factory=set)
    
    # Action
    action: ApprovalAction = ApprovalAction.REQUEST_MORE_INFO
    auto_approve: bool = False
    auto_reject: bool = False
    
    # Metadata
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None


@dataclass
class ApprovalRequest:
    """Represents a human approval request."""
    # Core identifiers
    request_id: UUID = field(default_factory=uuid.uuid4)
    workflow_id: UUID = field(default_factory=uuid.uuid4)
    opportunity_id: UUID = field(default_factory=uuid.uuid4)
    
    # Request details
    title: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    priority: ApprovalPriority = ApprovalPriority.MEDIUM
    
    # Opportunity context
    opportunity_summary: Dict[str, Any] = field(default_factory=dict)
    risk_tier: Optional[RiskTier] = None
    expected_profit: Optional[float] = None
    total_stake: Optional[float] = None
    bookmakers: List[str] = field(default_factory=list)
    sport: Optional[str] = None
    
    # Routing
    primary_reviewer: Optional[str] = None
    backup_reviewers: List[str] = field(default_factory=list)
    approval_channels: List[ApprovalChannel] = field(default_factory=lambda: [ApprovalChannel.IN_APP])
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=5))
    last_reminder_at: Optional[datetime] = None
    
    # Status tracking
    status: str = "pending"  # pending, approved, rejected, expired, delegated, escalated
    responded_at: Optional[datetime] = None
    response: Optional[str] = None
    reviewer: Optional[str] = None
    
    # Escalation
    escalation_level: int = 0
    max_escalation_level: int = 3
    escalated_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)


@dataclass
class ApprovalResponse:
    """Represents a response to an approval request."""
    response_id: UUID = field(default_factory=uuid.uuid4)
    request_id: UUID = field(default_factory=uuid.uuid4)
    
    # Response details
    action: ApprovalAction = ApprovalAction.APPROVE
    decision: bool = True  # True for approve, False for reject
    message: str = ""
    reasoning: str = ""
    
    # Reviewer information
    reviewer_id: str = ""
    reviewer_name: str = ""
    reviewer_role: str = ""
    
    # Timing
    responded_at: datetime = field(default_factory=datetime.utcnow)
    processing_time: Optional[float] = None
    
    # Metadata
    source_channel: ApprovalChannel = ApprovalChannel.IN_APP
    metadata: Dict[str, Any] = field(default_factory=dict)


class HITLApprovalHandler:
    """
    HITL Approval Handler - manages approval requests and responses
    with comprehensive routing, notification, and timeout handling.
    """
    
    def __init__(self, audit_logger=None, logger: Optional[logging.Logger] = None):
        """Initialize the HITL approval handler."""
        self.audit_logger = audit_logger or get_audit_logger()
        self.logger = logger or get_logger('hitl_approval')
        
        # Approval requests storage
        self._pending_requests: Dict[UUID, ApprovalRequest] = {}
        self._completed_requests: Dict[UUID, ApprovalRequest] = {}
        self._approval_responses: Dict[UUID, ApprovalResponse] = {}
        
        # Approval rules
        self._approval_rules: Dict[UUID, ApprovalRule] = {}
        self._default_rules_initialized = False
        
        # Reviewer management
        self._reviewers: Dict[str, Dict[str, Any]] = {}
        self._reviewer_availability: Dict[str, bool] = {}
        
        # Statistics and metrics
        self._stats = {
            'requests_created': 0,
            'requests_approved': 0,
            'requests_rejected': 0,
            'requests_expired': 0,
            'requests_delegated': 0,
            'requests_escalated': 0,
            'avg_response_time': 0.0,
            'total_response_time': 0.0,
            'auto_actions': 0,
            'channel_usage': {},
            'priority_distribution': {}
        }
        
        # Background tasks
        self._monitoring_active = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Notification handlers
        self._notification_handlers: Dict[ApprovalChannel, Callable] = {}
        self._initialize_notification_handlers()
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """Initialize default approval rules."""
        if self._default_rules_initialized:
            return
        
        # Rule 1: Auto-approve low-risk, low-stake opportunities
        rule1 = ApprovalRule(
            name="Auto-approve Tier A low-stake",
            description="Automatically approve Tier A opportunities under $100",
            risk_tiers={RiskTier.TIER_A},
            max_stake=100.0,
            action=ApprovalAction.APPROVE,
            auto_approve=True
        )
        self._approval_rules[rule1.rule_id] = rule1
        
        # Rule 2: Auto-reject very high-risk opportunities
        rule2 = ApprovalRule(
            name="Auto-reject Tier D",
            description="Automatically reject Tier D opportunities",
            risk_tiers={RiskTier.TIER_D},
            action=ApprovalAction.REJECT,
            auto_reject=True
        )
        self._approval_rules[rule2.rule_id] = rule2
        
        # Rule 3: Auto-reject very high profit margin (suspicious)
        rule3 = ApprovalRule(
            name="Auto-reject suspicious high margin",
            description="Auto-reject opportunities with >20% profit margin",
            min_profit_margin=0.20,
            action=ApprovalAction.REJECT,
            auto_reject=True
        )
        self._approval_rules[rule3.rule_id] = rule3
        
        self._default_rules_initialized = True
        self.logger.debug("Default approval rules initialized")
    
    def _initialize_notification_handlers(self) -> None:
        """Initialize notification handlers for different channels."""
        self._notification_handlers = {
            ApprovalChannel.EMAIL: self._send_email_notification,
            ApprovalChannel.SMS: self._send_sms_notification,
            ApprovalChannel.WEBHOOK: self._send_webhook_notification,
            ApprovalChannel.DISCORD: self._send_discord_notification,
            ApprovalChannel.SLACK: self._send_slack_notification,
            ApprovalChannel.TELEGRAM: self._send_telegram_notification,
            ApprovalChannel.IN_APP: self._send_in_app_notification,
            ApprovalChannel.API: self._send_api_notification,
            ApprovalChannel.CONSOLE: self._send_console_notification
        }
    
    async def create_approval_request(
        self,
        workflow_id: UUID,
        opportunity: ArbitrageOpportunity,
        primary_reviewer: str,
        backup_reviewers: Optional[List[str]] = None,
        approval_channels: Optional[List[ApprovalChannel]] = None,
        custom_message: Optional[str] = None,
        priority: ApprovalPriority = ApprovalPriority.MEDIUM,
        **kwargs
    ) -> ApprovalRequest:
        """
        Create a new approval request.
        
        Args:
            workflow_id: Associated workflow ID
            opportunity: The arbitrage opportunity
            primary_reviewer: Primary reviewer username/ID
            backup_reviewers: List of backup reviewers
            approval_channels: Channels to send the request through
            custom_message: Custom message for the request
            priority: Priority level of the request
            **kwargs: Additional request parameters
        
        Returns:
            ApprovalRequest object
        """
        # Check automatic rules first
        auto_action = self._check_approval_rules(opportunity)
        if auto_action:
            self.logger.info(
                "Auto-action applied based on rules",
                opportunity_id=str(opportunity.id),
                action=auto_action.action.value
            )
            # Create a virtual request/response for audit trail
            virtual_request = self._create_virtual_request(workflow_id, opportunity, auto_action)
            return virtual_request
        
        # Create actual approval request
        request = ApprovalRequest(
            workflow_id=workflow_id,
            opportunity_id=opportunity.id,
            title=f"Arbitrage Approval: {opportunity.event_name}",
            message=custom_message or f"Approval needed for arbitrage opportunity: {opportunity.event_name}",
            priority=priority,
            opportunity_summary=self._create_opportunity_summary(opportunity),
            risk_tier=opportunity.risk_tier,
            expected_profit=float(opportunity.profit_amount),
            total_stake=float(opportunity.total_stake),
            bookmakers=[leg.bookmaker for leg in opportunity.legs],
            sport=opportunity.sport.value,
            primary_reviewer=primary_reviewer,
            backup_reviewers=backup_reviewers or [],
            approval_channels=approval_channels or [ApprovalChannel.IN_APP],
            expires_at=datetime.utcnow() + timedelta(minutes=kwargs.get('timeout_minutes', 5)),
            metadata=kwargs
        )
        
        # Add to tracking
        self._pending_requests[request.request_id] = request
        self._stats['requests_created'] += 1
        self._stats['channel_usage'][request.approval_channels[0].value] = \
            self._stats['channel_usage'].get(request.approval_channels[0].value, 0) + 1
        self._stats['priority_distribution'][priority.value] = \
            self._stats['priority_distribution'].get(priority.value, 0) + 1
        
        # Start monitoring if not already active
        if not self._monitoring_active:
            await self._start_monitoring()
        
        # Send notifications
        await self._send_approval_notifications(request)
        
        # Log request creation
        await self._log_approval_event(
            request.request_id, "approval_request_created",
            {
                'workflow_id': str(workflow_id),
                'opportunity_id': str(opportunity.id),
                'primary_reviewer': primary_reviewer,
                'priority': priority.value,
                'channels': [ch.value for ch in request.approval_channels]
            }
        )
        
        self.logger.info(
            "Approval request created",
            request_id=str(request.request_id),
            workflow_id=str(workflow_id),
            primary_reviewer=primary_reviewer,
            priority=priority.value
        )
        
        return request
    
    def _check_approval_rules(self, opportunity: ArbitrageOpportunity) -> Optional[ApprovalRule]:
        """Check if any approval rules apply to this opportunity."""
        for rule in self._approval_rules.values():
            if not rule.enabled:
                continue
            
            # Check risk tier
            if rule.risk_tiers and opportunity.risk_tier not in rule.risk_tiers:
                continue
            
            # Check profit margin
            profit_margin = float(opportunity.profit_margin)
            if rule.min_profit_margin is not None and profit_margin < rule.min_profit_margin:
                continue
            if rule.max_profit_margin is not None and profit_margin > rule.max_profit_margin:
                continue
            
            # Check stake
            stake = float(opportunity.total_stake)
            if rule.min_stake is not None and stake < rule.min_stake:
                continue
            if rule.max_stake is not None and stake > rule.max_stake:
                continue
            
            # Check bookmakers
            opportunity_bookmakers = set(leg.bookmaker for leg in opportunity.legs)
            if rule.bookmakers and not opportunity_bookmakers.intersection(rule.bookmakers):
                continue
            
            # Check sports
            if rule.sports and opportunity.sport.value not in rule.sports:
                continue
            
            # Rule matches
            rule.last_used = datetime.utcnow()
            
            if rule.auto_approve:
                return rule
            elif rule.auto_reject:
                return rule
        
        return None
    
    def _create_virtual_request(self, workflow_id: UUID, opportunity: ArbitrageOpportunity, rule: ApprovalRule) -> ApprovalRequest:
        """Create a virtual request/response for auto-actions."""
        request = ApprovalRequest(
            request_id=uuid.uuid4(),
            workflow_id=workflow_id,
            opportunity_id=opportunity.id,
            title=f"Auto-{rule.action.value.title()}: {opportunity.event_name}",
            message=f"Automatically {rule.action.value} based on rule: {rule.name}",
            status="completed" if rule.auto_approve or rule.auto_reject else "pending",
            created_at=datetime.utcnow(),
            responded_at=datetime.utcnow(),
            reviewer="system",
            metadata={'auto_action': True, 'rule_id': str(rule.rule_id)}
        )
        
        # Update stats
        self._stats['auto_actions'] += 1
        if rule.action == ApprovalAction.APPROVE:
            self._stats['requests_approved'] += 1
        elif rule.action == ApprovalAction.REJECT:
            self._stats['requests_rejected'] += 1
        
        return request
    
    def _create_opportunity_summary(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Create a summary of the opportunity for the approval request."""
        return {
            'id': str(opportunity.id),
            'sport': opportunity.sport.value,
            'event_name': opportunity.event_name,
            'event_date': opportunity.event_date.isoformat(),
            'market_type': opportunity.market_type,
            'total_stake': float(opportunity.total_stake),
            'profit_amount': float(opportunity.profit_amount),
            'profit_margin': float(opportunity.profit_margin),
            'risk_tier': opportunity.risk_tier.value,
            'bookmakers': [leg.bookmaker for leg in opportunity.legs],
            'legs_count': len(opportunity.legs)
        }
    
    async def _send_approval_notifications(self, request: ApprovalRequest) -> None:
        """Send approval notifications through configured channels."""
        notification_tasks = []
        
        for channel in request.approval_channels:
            handler = self._notification_handlers.get(channel)
            if handler:
                task = asyncio.create_task(handler(request))
                notification_tasks.append(task)
        
        # Wait for notifications to be sent (don't wait for delivery)
        if notification_tasks:
            await asyncio.gather(*notification_tasks, return_exceptions=True)
    
    async def _send_email_notification(self, request: ApprovalRequest) -> None:
        """Send email notification (placeholder implementation)."""
        self.logger.info(
            "Email notification sent",
            request_id=str(request.request_id),
            to=request.primary_reviewer
        )
        # Implementation would integrate with email service
        await asyncio.sleep(0.1)  # Simulate sending time
    
    async def _send_sms_notification(self, request: ApprovalRequest) -> None:
        """Send SMS notification (placeholder implementation)."""
        self.logger.info(
            "SMS notification sent",
            request_id=str(request.request_id),
            to=request.primary_reviewer
        )
        await asyncio.sleep(0.1)
    
    async def _send_webhook_notification(self, request: ApprovalRequest) -> None:
        """Send webhook notification (placeholder implementation)."""
        self.logger.info(
            "Webhook notification sent",
            request_id=str(request.request_id)
        )
        await asyncio.sleep(0.1)
    
    async def _send_discord_notification(self, request: ApprovalRequest) -> None:
        """Send Discord notification (placeholder implementation)."""
        self.logger.info(
            "Discord notification sent",
            request_id=str(request.request_id),
            channel=request.primary_reviewer
        )
        await asyncio.sleep(0.1)
    
    async def _send_slack_notification(self, request: ApprovalRequest) -> None:
        """Send Slack notification (placeholder implementation)."""
        self.logger.info(
            "Slack notification sent",
            request_id=str(request.request_id),
            channel=request.primary_reviewer
        )
        await asyncio.sleep(0.1)
    
    async def _send_telegram_notification(self, request: ApprovalRequest) -> None:
        """Send Telegram notification (placeholder implementation)."""
        self.logger.info(
            "Telegram notification sent",
            request_id=str(request.request_id),
            chat_id=request.primary_reviewer
        )
        await asyncio.sleep(0.1)
    
    async def _send_in_app_notification(self, request: ApprovalRequest) -> None:
        """Send in-app notification."""
        self.logger.info(
            "In-app notification created",
            request_id=str(request.request_id),
            user=request.primary_reviewer
        )
        # Store in user's notification queue
        await asyncio.sleep(0.05)
    
    async def _send_api_notification(self, request: ApprovalRequest) -> None:
        """Send API notification."""
        self.logger.info(
            "API notification sent",
            request_id=str(request.request_id)
        )
        # Call webhook or API endpoint
        await asyncio.sleep(0.1)
    
    async def _send_console_notification(self, request: ApprovalRequest) -> None:
        """Send console notification."""
        print(f"\n🔔 APPROVAL REQUEST: {request.title}")
        print(f"Reviewer: {request.primary_reviewer}")
        print(f"Priority: {request.priority.value}")
        print(f"Message: {request.message}")
        print(f"Expires: {request.expires_at}\n")
        await asyncio.sleep(0.05)
    
    async def respond_to_approval(
        self,
        request_id: UUID,
        action: ApprovalAction,
        reviewer_id: str,
        message: str = "",
        reasoning: str = "",
        **kwargs
    ) -> ApprovalResponse:
        """
        Respond to an approval request.
        
        Args:
            request_id: The request ID to respond to
            action: The action taken
            reviewer_id: ID of the reviewer
            message: Response message
            reasoning: Reasoning for the decision
            **kwargs: Additional response metadata
        
        Returns:
            ApprovalResponse object
        """
        # Find the request
        request = self._pending_requests.get(request_id)
        if not request:
            raise ValueError(f"Approval request not found: {request_id}")
        
        # Check if request has expired
        if datetime.utcnow() > request.expires_at:
            await self._expire_request(request_id)
            raise ValueError(f"Approval request has expired: {request_id}")
        
        # Create response
        response = ApprovalResponse(
            request_id=request_id,
            action=action,
            decision=action in [ApprovalAction.APPROVE, ApprovalAction.REJECT],
            message=message,
            reasoning=reasoning,
            reviewer_id=reviewer_id,
            reviewer_name=kwargs.get('reviewer_name', reviewer_id),
            reviewer_role=kwargs.get('reviewer_role', 'user'),
            source_channel=kwargs.get('source_channel', ApprovalChannel.IN_APP),
            metadata=kwargs
        )
        
        # Update request
        request.status = action.value
        request.responded_at = datetime.utcnow()
        request.response = message
        request.reviewer = reviewer_id
        
        # Calculate processing time
        response.processing_time = (request.responded_at - request.created_at).total_seconds()
        
        # Store response
        self._approval_responses[response.response_id] = response
        
        # Move request to completed
        self._completed_requests[request_id] = request
        del self._pending_requests[request_id]
        
        # Update statistics
        if action == ApprovalAction.APPROVE:
            self._stats['requests_approved'] += 1
        elif action == ApprovalAction.REJECT:
            self._stats['requests_rejected'] += 1
        elif action == ApprovalAction.DELEGATE:
            self._stats['requests_delegated'] += 1
        elif action == ApprovalAction.ESCALATE:
            self._stats['requests_escalated'] += 1
        
        # Update response time stats
        self._stats['total_response_time'] += response.processing_time
        self._stats['avg_response_time'] = (
            self._stats['total_response_time'] / 
            (self._stats['requests_approved'] + self._stats['requests_rejected'])
        )
        
        # Log response
        await self._log_approval_event(
            request_id, "approval_response_received",
            {
                'action': action.value,
                'reviewer_id': reviewer_id,
                'processing_time': response.processing_time,
                'source_channel': response.source_channel.value
            }
        )
        
        self.logger.info(
            "Approval response received",
            request_id=str(request_id),
            action=action.value,
            reviewer_id=reviewer_id,
            processing_time=response.processing_time
        )
        
        return response
    
    async def _expire_request(self, request_id: UUID) -> None:
        """Mark a request as expired."""
        request = self._pending_requests.get(request_id)
        if not request:
            return
        
        request.status = "expired"
        request.responded_at = datetime.utcnow()
        request.response = "Request expired due to timeout"
        
        # Move to completed
        self._completed_requests[request_id] = request
        del self._pending_requests[request_id]
        
        # Update stats
        self._stats['requests_expired'] += 1
        
        # Log expiration
        await self._log_approval_event(
            request_id, "approval_request_expired",
            {'expired_at': request.responded_at.isoformat()}
        )
        
        self.logger.warning(
            "Approval request expired",
            request_id=str(request_id)
        )
    
    async def _start_monitoring(self) -> None:
        """Start background monitoring of approval requests."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitor_task = asyncio.create_task(self._monitor_requests())
    
    async def _monitor_requests(self) -> None:
        """Background task to monitor approval requests."""
        while self._monitoring_active:
            try:
                current_time = datetime.utcnow()
                expired_requests = []
                
                # Check for expired requests
                for request_id, request in self._pending_requests.items():
                    if current_time > request.expires_at:
                        expired_requests.append(request_id)
                
                # Expire requests
                for request_id in expired_requests:
                    await self._expire_request(request_id)
                
                # Send reminders for requests approaching expiry
                reminder_threshold = timedelta(minutes=1)
                for request_id, request in self._pending_requests.items():
                    time_to_expiry = request.expires_at - current_time
                    if (time_to_expiry <= reminder_threshold and 
                        time_to_expiry > timedelta(0) and
                        request.last_reminder_at is None):
                        
                        # Send reminder
                        await self._send_reminder(request)
                        request.last_reminder_at = current_time
                
                # Sleep for a short period
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error("Error in approval monitoring", error=str(e))
                await asyncio.sleep(60)  # Back off on error
    
    async def _send_reminder(self, request: ApprovalRequest) -> None:
        """Send a reminder for an approval request."""
        self.logger.info(
            "Sending approval reminder",
            request_id=str(request.request_id),
            time_remaining=str(request.expires_at - datetime.utcnow())
        )
        
        # Send reminder through primary channel
        await self._send_approval_notifications(request)
        
        # Log reminder
        await self._log_approval_event(
            request.request_id, "approval_reminder_sent",
            {'reminder_type': 'expiry_warning'}
        )
    
    async def _log_approval_event(self, request_id: UUID, event_type: str, details: Dict[str, Any]) -> None:
        """Log approval events to audit trail."""
        try:
            await self.audit_logger.log_user_action(
                action=f"hitl_approval_{event_type}",
                resource=f"approval:{request_id}",
                details={
                    'request_id': str(request_id),
                    'event_type': event_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    **details
                }
            )
        except Exception as e:
            self.logger.error("Failed to log approval event", error=str(e))
    
    # Public API methods
    def get_pending_requests(self, reviewer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending approval requests."""
        requests = []
        
        for request in self._pending_requests.values():
            if reviewer_id is None or request.primary_reviewer == reviewer_id:
                requests.append(self._serialize_request(request))
        
        # Sort by priority and creation time
        priority_order = {
            ApprovalPriority.EMERGENCY: 0,
            ApprovalPriority.CRITICAL: 1,
            ApprovalPriority.HIGH: 2,
            ApprovalPriority.MEDIUM: 3,
            ApprovalPriority.LOW: 4
        }
        
        requests.sort(key=lambda x: (
            priority_order.get(ApprovalPriority(x['priority']), 5),
            x['created_at']
        ))
        
        return requests
    
    def get_request_details(self, request_id: UUID) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific request."""
        request = self._pending_requests.get(request_id) or self._completed_requests.get(request_id)
        if request:
            return self._serialize_request(request, include_response=True)
        return None
    
    def _serialize_request(self, request: ApprovalRequest, include_response: bool = False) -> Dict[str, Any]:
        """Serialize request for API responses."""
        data = {
            'request_id': str(request.request_id),
            'workflow_id': str(request.workflow_id),
            'opportunity_id': str(request.opportunity_id),
            'title': request.title,
            'message': request.message,
            'priority': request.priority.value,
            'opportunity_summary': request.opportunity_summary,
            'risk_tier': request.risk_tier.value if request.risk_tier else None,
            'expected_profit': request.expected_profit,
            'total_stake': request.total_stake,
            'bookmakers': request.bookmakers,
            'sport': request.sport,
            'primary_reviewer': request.primary_reviewer,
            'backup_reviewers': request.backup_reviewers,
            'approval_channels': [ch.value for ch in request.approval_channels],
            'created_at': request.created_at.isoformat(),
            'expires_at': request.expires_at.isoformat(),
            'status': request.status,
            'escalation_level': request.escalation_level,
            'tags': list(request.tags)
        }
        
        if include_response and request.responded_at:
            data.update({
                'responded_at': request.responded_at.isoformat(),
                'response': request.response,
                'reviewer': request.reviewer
            })
        
        return data
    
    def add_reviewer(self, reviewer_id: str, name: str, role: str = "user", **kwargs) -> None:
        """Add a reviewer to the system."""
        self._reviewers[reviewer_id] = {
            'id': reviewer_id,
            'name': name,
            'role': role,
            'created_at': datetime.utcnow().isoformat(),
            **kwargs
        }
        self._reviewer_availability[reviewer_id] = True
        
        self.logger.info("Reviewer added", reviewer_id=reviewer_id, name=name, role=role)
    
    def set_reviewer_availability(self, reviewer_id: str, available: bool) -> None:
        """Set reviewer availability status."""
        self._reviewer_availability[reviewer_id] = available
        self.logger.debug(
            "Reviewer availability updated",
            reviewer_id=reviewer_id,
            available=available
        )
    
    def get_reviewers(self, available_only: bool = False) -> List[Dict[str, Any]]:
        """Get list of reviewers."""
        reviewers = []
        
        for reviewer_id, info in self._reviewers.items():
            if not available_only or self._reviewer_availability.get(reviewer_id, True):
                reviewers.append({
                    **info,
                    'available': self._reviewer_availability.get(reviewer_id, True)
                })
        
        return reviewers
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get approval handler statistics."""
        return {
            **self._stats,
            'pending_requests': len(self._pending_requests),
            'completed_requests': len(self._completed_requests),
            'active_reviewers': len([r for r in self._reviewer_availability.values() if r]),
            'approval_rules': len(self._approval_rules)
        }
    
    async def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._monitor_task


# Example usage
if __name__ == "__main__":
    import asyncio
    from decimal import Decimal
    
    async def main():
        """Example usage of HITL Approval Handler."""
        
        handler = HITLApprovalHandler()
        
        # Add a reviewer
        handler.add_reviewer("user123", "John Doe", role="trader")
        
        # Create sample opportunity
        from ..storage.models import Sport, ArbitrageLeg
        
        opportunity = ArbitrageOpportunity(
            sport=Sport.FOOTBALL,
            event_name="Liverpool vs Manchester United",
            event_date=datetime.utcnow() + timedelta(days=1),
            market_type="match_winner",
            legs=[
                ArbitrageLeg(
                    bookmaker="bet365",
                    event_outcome="Liverpool",
                    odds=Decimal("2.10"),
                    implied_probability=Decimal("0.4762"),
                    stake_percentage=Decimal("0.5"),
                    actual_stake=Decimal("100.00"),
                    potential_payout=Decimal("210.00")
                ),
                ArbitrageLeg(
                    bookmaker="william_hill",
                    event_outcome="Manchester United",
                    odds=Decimal("2.05"),
                    implied_probability=Decimal("0.4878"),
                    stake_percentage=Decimal("0.5"),
                    actual_stake=Decimal("100.00"),
                    potential_payout=Decimal("205.00")
                )
            ],
            total_stake=Decimal("200.00"),
            profit_margin=Decimal("0.025"),
            profit_amount=Decimal("5.00"),
            risk_tier=RiskTier.TIER_A,
            source_scanner="test_scanner"
        )
        
        # Create approval request
        request = await handler.create_approval_request(
            workflow_id=uuid.uuid4(),
            opportunity=opportunity,
            primary_reviewer="user123",
            approval_channels=[ApprovalChannel.CONSOLE, ApprovalChannel.IN_APP]
        )
        
        print(f"Created approval request: {request.request_id}")
        print(f"Pending requests: {len(handler.get_pending_requests())}")
        
        # Simulate approval response
        response = await handler.respond_to_approval(
            request_id=request.request_id,
            action=ApprovalAction.APPROVE,
            reviewer_id="user123",
            message="Looks good, approving",
            reasoning="Low risk Tier A opportunity"
        )
        
        print(f"Response recorded: {response.response_id}")
        
        # Get statistics
        stats = handler.get_statistics()
        print(f"Statistics: {stats}")
        
        await handler.stop_monitoring()
    
    asyncio.run(main())
