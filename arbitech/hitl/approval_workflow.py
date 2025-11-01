"""
Sophisticated User Approval Workflow System

A comprehensive approval system supporting multiple approval modes, queue management,
delegation, audit trails, and integration with risk validation and execution phases.

Features:
- Multiple approval modes (manual, auto-approve by tier, batch, rule-based)
- Priority-based approval queues
- Approval delegation and multi-user scenarios
- Comprehensive audit trails and history
- Emergency override capabilities
- Timeout management
- Integration with Phase 4 risk validation and Phase 5 execution coordination
- Permission checking and confirmation workflows
"""

import json
import logging
import time
import uuid
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any, Tuple, Union
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
import threading
import queue
import copy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Approval status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELEGATED = "delegated"
    EXPIRED = "expired"
    EMERGENCY_OVERRIDE = "emergency_override"
    AUTO_APPROVED = "auto_approved"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


class ApprovalMode(Enum):
    """Approval mode enumeration"""
    MANUAL = "manual"
    AUTO_TIER = "auto_tier"
    BATCH = "batch"
    RULE_BASED = "rule_based"
    EMERGENCY = "emergency"
    DELEGATED = "delegated"


class ApprovalPriority(Enum):
    """Approval priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    URGENT = 5


class ApprovalTier(Enum):
    """Approval tier levels"""
    TIER_1 = "tier_1"      # Up to $1,000
    TIER_2 = "tier_2"      # Up to $10,000
    TIER_3 = "tier_3"      # Up to $100,000
    TIER_4 = "tier_4"      # Up to $1,000,000
    TIER_5 = "tier_5"      # Above $1,000,000


@dataclass
class ApprovalRule:
    """Rule-based approval configuration"""
    rule_id: str
    name: str
    condition: Callable[[Dict], bool]
    required_approvers: List[str]
    auto_approve: bool = False
    timeout_minutes: int = 60
    priority: ApprovalPriority = ApprovalPriority.MEDIUM
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ApprovalStep:
    """Individual approval step in workflow"""
    step_id: str
    approver_id: str
    role: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    assigned_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    comments: str = ""
    delegated_to: Optional[str] = None
    expires_at: Optional[datetime] = None


@dataclass
class ApprovalRequest:
    """Complete approval request"""
    request_id: str
    title: str
    description: str
    requester_id: str
    request_type: str
    amount: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: ApprovalStatus = ApprovalStatus.PENDING
    mode: ApprovalMode = ApprovalMode.MANUAL
    priority: ApprovalPriority = ApprovalPriority.MEDIUM
    tier: Optional[ApprovalTier] = None
    steps: List[ApprovalStep] = field(default_factory=list)
    current_step_index: int = 0
    timeout_minutes: int = 60
    expires_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    escalation_count: int = 0
    max_escalations: int = 3
    batch_id: Optional[str] = None
    delegated_from: Optional[str] = None
    override_reason: Optional[str] = None
    risk_score: Optional[float] = None
    phase_4_validated: bool = False
    phase_5_coord_id: Optional[str] = None


@dataclass
class ApprovalHistory:
    """Audit trail entry"""
    history_id: str
    request_id: str
    action: str
    user_id: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class User:
    """User representation with permissions"""
    user_id: str
    username: str
    email: str
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    is_active: bool = True
    approval_limits: Dict[ApprovalTier, float] = field(default_factory=dict)
    can_emergency_override: bool = False
    can_delegate: bool = True
    can_batch_approve: bool = False
    max_delegation_depth: int = 3
    last_login: Optional[datetime] = None


class ApprovalWorkflowSystem:
    """Main approval workflow system"""
    
    def __init__(self):
        """Initialize the approval workflow system"""
        self.requests: Dict[str, ApprovalRequest] = {}
        self.users: Dict[str, User] = {}
        self.rules: Dict[str, ApprovalRule] = {}
        self.history: Dict[str, List[ApprovalHistory]] = defaultdict(list)
        self.approval_queue = queue.PriorityQueue()
        self.delegation_tree: Dict[str, List[str]] = defaultdict(list)
        self.batch_queues: Dict[str, List[ApprovalRequest]] = defaultdict(list)
        self.lock = threading.RLock()
        self.observers: List[Callable] = []
        
        # Configuration
        self.config = {
            "max_concurrent_approvals": 50,
            "default_timeout_hours": 24,
            "escalation_interval_minutes": 30,
            "auto_approve_thresholds": {
                ApprovalTier.TIER_1: 100.0,
                ApprovalTier.TIER_2: 1000.0,
                ApprovalTier.TIER_3: 10000.0,
                ApprovalTier.TIER_4: 100000.0,
            },
            "priority_queue_weights": {
                ApprovalPriority.URGENT: 5,
                ApprovalPriority.CRITICAL: 4,
                ApprovalPriority.HIGH: 3,
                ApprovalPriority.MEDIUM: 2,
                ApprovalPriority.LOW: 1,
            }
        }
        
        # Initialize default users and rules
        self._initialize_defaults()
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info("Approval Workflow System initialized")
    
    def _initialize_defaults(self):
        """Initialize default users and rules"""
        # Create default admin user
        admin_user = User(
            user_id="admin",
            username="admin",
            email="admin@company.com",
            roles={"admin", "approver"},
            permissions={"approve_all", "emergency_override", "manage_users", "view_audit"},
            approval_limits={
                ApprovalTier.TIER_1: float('inf'),
                ApprovalTier.TIER_2: float('inf'),
                ApprovalTier.TIER_3: float('inf'),
                ApprovalTier.TIER_4: float('inf'),
                ApprovalTier.TIER_5: float('inf'),
            },
            can_emergency_override=True,
            can_batch_approve=True
        )
        self.users[admin_user.user_id] = admin_user
        
        # Create default approver
        approver_user = User(
            user_id="approver_1",
            username="approver",
            email="approver@company.com",
            roles={"approver"},
            permissions={"approve", "view_requests"},
            approval_limits={
                ApprovalTier.TIER_1: 1000.0,
                ApprovalTier.TIER_2: 5000.0,
                ApprovalTier.TIER_3: 50000.0,
            }
        )
        self.users[approver_user.user_id] = approver_user
        
        # Create default approval rules
        low_amount_rule = ApprovalRule(
            rule_id="low_amount_auto",
            name="Auto-approve low amounts",
            condition=lambda req: req.get("amount", 0) <= 100,
            required_approvers=[],
            auto_approve=True,
            timeout_minutes=30,
            priority=ApprovalPriority.LOW
        )
        self.rules[low_amount_rule.rule_id] = low_amount_rule
        
        high_amount_rule = ApprovalRule(
            rule_id="high_amount_multi",
            name="Multi-step approval for high amounts",
            condition=lambda req: req.get("amount", 0) > 100000,
            required_approvers=["approver_1", "admin"],
            auto_approve=False,
            timeout_minutes=120,
            priority=ApprovalPriority.HIGH
        )
        self.rules[high_amount_rule.rule_id] = high_amount_rule
    
    def _start_background_tasks(self):
        """Start background monitoring tasks"""
        def timeout_monitor():
            while True:
                try:
                    self._check_timeouts()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Timeout monitor error: {e}")
                    time.sleep(60)
        
        timeout_thread = threading.Thread(target=timeout_monitor, daemon=True)
        timeout_thread.start()
        
        def escalation_monitor():
            while True:
                try:
                    self._check_escalations()
                    time.sleep(self.config["escalation_interval_minutes"] * 60)
                except Exception as e:
                    logger.error(f"Escalation monitor error: {e}")
                    time.sleep(self.config["escalation_interval_minutes"] * 60)
        
        escalation_thread = threading.Thread(target=escalation_monitor, daemon=True)
        escalation_thread.start()
        
        logger.info("Background monitoring tasks started")
    
    # ==================== USER MANAGEMENT ====================
    
    def create_user(self, user: User) -> bool:
        """Create a new user"""
        with self.lock:
            if user.user_id in self.users:
                logger.warning(f"User {user.user_id} already exists")
                return False
            
            self.users[user.user_id] = user
            self._log_action(user.user_id, "user_created", user.user_id, {})
            logger.info(f"User {user.user_id} created")
            return True
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user information"""
        with self.lock:
            if user_id not in self.users:
                logger.error(f"User {user_id} not found")
                return False
            
            user = self.users[user_id]
            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            self._log_action(user_id, "user_updated", user_id, updates)
            logger.info(f"User {user_id} updated")
            return True
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def list_users(self, role: Optional[str] = None) -> List[User]:
        """List users, optionally filtered by role"""
        users = list(self.users.values())
        if role:
            users = [u for u in users if role in u.roles]
        return users
    
    # ==================== APPROVAL RULES ====================
    
    def create_rule(self, rule: ApprovalRule) -> bool:
        """Create a new approval rule"""
        with self.lock:
            if rule.rule_id in self.rules:
                logger.warning(f"Rule {rule.rule_id} already exists")
                return False
            
            self.rules[rule.rule_id] = rule
            self._log_action("system", "rule_created", rule.rule_id, asdict(rule))
            logger.info(f"Rule {rule.rule_id} created")
            return True
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing rule"""
        with self.lock:
            if rule_id not in self.rules:
                logger.error(f"Rule {rule_id} not found")
                return False
            
            rule = self.rules[rule_id]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            self._log_action("system", "rule_updated", rule_id, updates)
            logger.info(f"Rule {rule_id} updated")
            return True
    
    def get_applicable_rules(self, request: ApprovalRequest) -> List[ApprovalRule]:
        """Get rules applicable to a request"""
        applicable = []
        request_dict = asdict(request)
        
        for rule in self.rules.values():
            if rule.active and rule.condition(request_dict):
                applicable.append(rule)
        
        # Sort by priority (higher priority first)
        applicable.sort(key=lambda r: r.priority.value, reverse=True)
        return applicable
    
    # ==================== APPROVAL REQUEST CREATION ====================
    
    def create_approval_request(
        self,
        title: str,
        description: str,
        requester_id: str,
        request_type: str,
        amount: Optional[float] = None,
        priority: ApprovalPriority = ApprovalPriority.MEDIUM,
        mode: ApprovalMode = ApprovalMode.MANUAL,
        metadata: Optional[Dict[str, Any]] = None,
        timeout_minutes: Optional[int] = None,
        batch_id: Optional[str] = None
    ) -> Optional[str]:
        """Create a new approval request"""
        
        with self.lock:
            # Validate requester
            if requester_id not in self.users:
                logger.error(f"Requester {requester_id} not found")
                return None
            
            requester = self.users[requester_id]
            if not requester.is_active:
                logger.error(f"Requester {requester_id} is inactive")
                return None
            
            # Determine approval tier
            tier = self._determine_tier(amount) if amount else None
            
            # Calculate timeout
            default_timeout = timeout_minutes or self.config["default_timeout_hours"] * 60
            expires_at = datetime.now() + timedelta(minutes=default_timeout)
            
            # Create request
            request = ApprovalRequest(
                request_id=str(uuid.uuid4()),
                title=title,
                description=description,
                requester_id=requester_id,
                request_type=request_type,
                amount=amount,
                metadata=metadata or {},
                tier=tier,
                priority=priority,
                mode=mode,
                timeout_minutes=default_timeout,
                expires_at=expires_at,
                batch_id=batch_id
            )
            
            # Apply approval rules
            self._apply_approval_rules(request)
            
            # Add to queue
            self._add_to_queue(request)
            
            # Store request
            self.requests[request.request_id] = request
            
            # Log creation
            self._log_action(
                requester_id, 
                "request_created", 
                request.request_id, 
                asdict(request)
            )
            
            # Notify observers
            self._notify_observers("request_created", request)
            
            logger.info(f"Approval request {request.request_id} created")
            return request.request_id
    
    def _determine_tier(self, amount: Optional[float]) -> Optional[ApprovalTier]:
        """Determine approval tier based on amount"""
        if amount is None:
            return None
        
        if amount <= 1000:
            return ApprovalTier.TIER_1
        elif amount <= 10000:
            return ApprovalTier.TIER_2
        elif amount <= 100000:
            return ApprovalTier.TIER_3
        elif amount <= 1000000:
            return ApprovalTier.TIER_4
        else:
            return ApprovalTier.TIER_5
    
    def _apply_approval_rules(self, request: ApprovalRequest):
        """Apply applicable rules to request"""
        applicable_rules = self.get_applicable_rules(request)
        
        if applicable_rules:
            # Use first applicable rule (highest priority)
            rule = applicable_rules[0]
            request.mode = ApprovalMode.RULE_BASED
            request.timeout_minutes = rule.timeout_minutes
            
            if rule.auto_approve:
                self._auto_approve_request(request, rule)
            else:
                # Create approval steps based on rule
                for approver_id in rule.required_approvers:
                    if approver_id in self.users:
                        step = ApprovalStep(
                            step_id=str(uuid.uuid4()),
                            approver_id=approver_id,
                            role=next(iter(self.users[approver_id].roles)) if self.users[approver_id].roles else "approver",
                            expires_at=datetime.now() + timedelta(minutes=rule.timeout_minutes)
                        )
                        request.steps.append(step)
        
        # Auto-approve based on tier if amount is below threshold
        if request.tier and request.amount:
            threshold = self.config["auto_approve_thresholds"].get(request.tier)
            if threshold and request.amount <= threshold:
                request.mode = ApprovalMode.AUTO_TIER
                self._auto_approve_request(request, None)
                return
        
        # If no auto-approval and no rule-based steps, create default steps based on tier
        if not request.steps and request.status == ApprovalStatus.PENDING:
            self._create_default_approval_steps(request)
    
    def _auto_approve_request(self, request: ApprovalRequest, rule: Optional[ApprovalRule]):
        """Auto-approve a request"""
        request.status = ApprovalStatus.AUTO_APPROVED
        request.approved_at = datetime.now()
        
        self._log_action(
            "system", 
            "auto_approved", 
            request.request_id, 
            {"rule_id": rule.rule_id if rule else "tier_based"}
        )
    
    def _create_default_approval_steps(self, request: ApprovalRequest):
        """Create default approval steps based on tier and amount"""
        # Find approvers based on tier requirements
        approvers = []
        
        # For TIER_1 and TIER_2 requests, use regular approvers
        if request.tier in [ApprovalTier.TIER_1, ApprovalTier.TIER_2]:
            # Find approvers with sufficient limits
            for user in self.users.values():
                if ("approver" in user.roles or "manager" in user.roles) and user.is_active:
                    limit = user.approval_limits.get(request.tier, 0)
                    if request.amount and request.amount <= limit:
                        approvers.append(user.user_id)
                        break  # Single approval for lower tiers
        
        # For TIER_3 and higher, require multiple approvals
        elif request.tier in [ApprovalTier.TIER_3, ApprovalTier.TIER_4, ApprovalTier.TIER_5]:
            # Find manager approver
            manager_found = False
            for user in self.users.values():
                if ("manager" in user.roles or "director" in user.roles) and user.is_active:
                    limit = user.approval_limits.get(request.tier, 0)
                    if request.amount and request.amount <= limit:
                        approvers.append(user.user_id)
                        manager_found = True
                        break
            
            # Find admin approver for higher tiers
            if request.tier in [ApprovalTier.TIER_4, ApprovalTier.TIER_5] or manager_found:
                for user in self.users.values():
                    if "admin" in user.roles and user.is_active:
                        approvers.append(user.user_id)
                        break
        
        # Fallback: use any available approver
        if not approvers:
            for user in self.users.values():
                if "approver" in user.roles and user.is_active:
                    approvers.append(user.user_id)
                    break
        
        # Create steps for each approver
        for approver_id in approvers:
            user = self.users[approver_id]
            step = ApprovalStep(
                step_id=str(uuid.uuid4()),
                approver_id=approver_id,
                role=next(iter(user.roles)) if user.roles else "approver",
                status=ApprovalStatus.PENDING,
                assigned_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=request.timeout_minutes)
            )
            request.steps.append(step)
        
        # Mark first step as assigned
        if request.steps:
            request.steps[0].assigned_at = datetime.now()
    
    def _add_to_queue(self, request: ApprovalRequest):
        """Add request to priority queue"""
        priority_weight = self.config["priority_queue_weights"][request.priority]
        queue_priority = (priority_weight, request.created_at.timestamp())
        self.approval_queue.put((queue_priority, request.request_id))
    
    # ==================== APPROVAL ACTIONS ====================
    
    def approve_request(
        self, 
        request_id: str, 
        approver_id: str, 
        comments: str = ""
    ) -> Tuple[bool, str]:
        """Approve a request"""
        with self.lock:
            if request_id not in self.requests:
                return False, "Request not found"
            
            request = self.requests[request_id]
            approver = self.users.get(approver_id)
            
            if not approver or not approver.is_active:
                return False, "Invalid approver"
            
            # Check if request is in pending state
            if request.status not in [ApprovalStatus.PENDING, ApprovalStatus.DELEGATED]:
                return False, f"Request is {request.status.value} and cannot be approved"
            
            # Check current step
            if request.current_step_index >= len(request.steps):
                return False, "No pending steps"
            
            current_step = request.steps[request.current_step_index]
            
            # Verify approver permission
            if not self._can_approve(request, approver):
                return False, "Insufficient permissions"
            
            # Check if step is assigned to this approver
            if current_step.approver_id != approver_id and not approver.can_emergency_override:
                return False, "Not assigned to this approver"
            
            # Approve current step
            current_step.status = ApprovalStatus.APPROVED
            current_step.approved_at = datetime.now()
            current_step.comments = comments
            
            # Move to next step or complete request
            request.current_step_index += 1
            
            if request.current_step_index >= len(request.steps):
                request.status = ApprovalStatus.APPROVED
                request.approved_at = datetime.now()
                
                # Trigger Phase 5 execution coordination
                self._trigger_phase5_execution(request)
            else:
                # Update next step assignment
                next_step = request.steps[request.current_step_index]
                next_step.assigned_at = datetime.now()
            
            # Log approval
            self._log_action(
                approver_id, 
                "approved", 
                request_id, 
                {
                    "step_id": current_step.step_id,
                    "comments": comments
                }
            )
            
            # Notify observers
            self._notify_observers("approved", request)
            
            logger.info(f"Request {request_id} approved by {approver_id}")
            return True, "Request approved successfully"
    
    def reject_request(
        self, 
        request_id: str, 
        approver_id: str, 
        comments: str = ""
    ) -> Tuple[bool, str]:
        """Reject a request"""
        with self.lock:
            if request_id not in self.requests:
                return False, "Request not found"
            
            request = self.requests[request_id]
            approver = self.users.get(approver_id)
            
            if not approver or not approver.is_active:
                return False, "Invalid approver"
            
            # Check if request is in pending state
            if request.status not in [ApprovalStatus.PENDING, ApprovalStatus.DELEGATED]:
                return False, f"Request is {request.status.value} and cannot be rejected"
            
            # Check current step
            if request.current_step_index >= len(request.steps):
                return False, "No pending steps"
            
            current_step = request.steps[request.current_step_index]
            
            # Verify approver permission
            if not self._can_approve(request, approver):
                return False, "Insufficient permissions"
            
            # Check if step is assigned to this approver
            if current_step.approver_id != approver_id and not approver.can_emergency_override:
                return False, "Not assigned to this approver"
            
            # Reject request
            current_step.status = ApprovalStatus.REJECTED
            current_step.comments = comments
            request.status = ApprovalStatus.REJECTED
            request.rejected_at = datetime.now()
            
            # Log rejection
            self._log_action(
                approver_id, 
                "rejected", 
                request_id, 
                {
                    "step_id": current_step.step_id,
                    "comments": comments
                }
            )
            
            # Notify observers
            self._notify_observers("rejected", request)
            
            logger.info(f"Request {request_id} rejected by {approver_id}")
            return True, "Request rejected successfully"
    
    def delegate_approval(
        self, 
        request_id: str, 
        current_approver_id: str, 
        delegate_to_id: str,
        comments: str = ""
    ) -> Tuple[bool, str]:
        """Delegate approval to another user"""
        with self.lock:
            if request_id not in self.requests:
                return False, "Request not found"
            
            request = self.requests[request_id]
            
            if request.status not in [ApprovalStatus.PENDING, ApprovalStatus.DELEGATED]:
                return False, f"Request is {request.status.value} and cannot be delegated"
            
            current_approver = self.users.get(current_approver_id)
            delegate_to = self.users.get(delegate_to_id)
            
            if not current_approver or not delegate_to:
                return False, "Invalid user(s)"
            
            # Check delegation permissions
            if not current_approver.can_delegate:
                return False, "Current approver cannot delegate"
            
            if not delegate_to.is_active:
                return False, "Delegate target is inactive"
            
            # Check delegation depth
            if self._get_delegation_depth(current_approver_id) >= current_approver.max_delegation_depth:
                return False, "Maximum delegation depth exceeded"
            
            # Update current step
            if request.current_step_index < len(request.steps):
                current_step = request.steps[request.current_step_index]
                current_step.status = ApprovalStatus.DELEGATED
                current_step.delegated_to = delegate_to_id
                current_step.comments = comments
                
                # Create new step for delegate
                new_step = ApprovalStep(
                    step_id=str(uuid.uuid4()),
                    approver_id=delegate_to_id,
                    role=current_step.role,
                    status=ApprovalStatus.PENDING,
                    assigned_at=datetime.now(),
                    expires_at=current_step.expires_at
                )
                
                request.steps.insert(request.current_step_index + 1, new_step)
                request.current_step_index += 1  # Move to the new delegated step
                request.delegated_from = current_approver_id
            
            # Log delegation
            self._log_action(
                current_approver_id, 
                "delegated", 
                request_id, 
                {
                    "delegate_to": delegate_to_id,
                    "comments": comments
                }
            )
            
            # Track delegation chain
            self.delegation_tree[request_id].append(delegate_to_id)
            
            # Notify observers
            self._notify_observers("delegated", request)
            
            logger.info(f"Request {request_id} delegated from {current_approver_id} to {delegate_to_id}")
            return True, "Approval delegated successfully"
    
    def emergency_override(
        self, 
        request_id: str, 
        override_approver_id: str, 
        reason: str
    ) -> Tuple[bool, str]:
        """Emergency override of approval requirements"""
        with self.lock:
            if request_id not in self.requests:
                return False, "Request not found"
            
            request = self.requests[request_id]
            override_approver = self.users.get(override_approver_id)
            
            if not override_approver:
                return False, "Invalid override approver"
            
            if not override_approver.can_emergency_override:
                return False, "Insufficient permissions for emergency override"
            
            if not override_approver.is_active:
                return False, "Override approver is inactive"
            
            # Emergency override
            request.status = ApprovalStatus.EMERGENCY_OVERRIDE
            request.approved_at = datetime.now()
            request.override_reason = reason
            
            # Mark all pending steps as approved
            for step in request.steps:
                if step.status == ApprovalStatus.PENDING:
                    step.status = ApprovalStatus.EMERGENCY_OVERRIDE
            
            # Log emergency override
            self._log_action(
                override_approver_id, 
                "emergency_override", 
                request_id, 
                {"reason": reason}
            )
            
            # Notify observers
            self._notify_observers("emergency_override", request)
            
            # Trigger Phase 5 execution coordination
            self._trigger_phase5_execution(request)
            
            logger.info(f"Emergency override applied to request {request_id} by {override_approver_id}")
            return True, "Emergency override applied successfully"
    
    # ==================== BATCH PROCESSING ====================
    
    def create_batch(self, batch_id: str, requester_id: str) -> bool:
        """Create a new batch for batch processing"""
        with self.lock:
            if batch_id in self.batch_queues:
                return False
            
            self.batch_queues[batch_id] = []
            self._log_action(requester_id, "batch_created", batch_id, {})
            return True
    
    def add_to_batch(self, batch_id: str, request_id: str) -> bool:
        """Add request to batch"""
        with self.lock:
            if batch_id not in self.batch_queues:
                return False
            
            if request_id not in self.requests:
                return False
            
            request = self.requests[request_id]
            request.batch_id = batch_id
            self.batch_queues[batch_id].append(request)
            return True
    
    def approve_batch(
        self, 
        batch_id: str, 
        approver_id: str, 
        comments: str = ""
    ) -> Tuple[bool, Dict[str, str]]:
        """Approve all requests in a batch"""
        with self.lock:
            if batch_id not in self.batch_queues:
                return False, {"error": "Batch not found"}
            
            approver = self.users.get(approver_id)
            if not approver or not approver.can_batch_approve:
                return False, {"error": "Insufficient permissions for batch approval"}
            
            results = {}
            approved_count = 0
            failed_count = 0
            
            for request in self.batch_queues[batch_id]:
                if request.status == ApprovalStatus.PENDING:
                    success, message = self.approve_request(
                        request.request_id, 
                        approver_id, 
                        f"Batch approval: {comments}"
                    )
                    results[request.request_id] = message
                    if success:
                        approved_count += 1
                    else:
                        failed_count += 1
            
            # Log batch approval
            self._log_action(
                approver_id, 
                "batch_approved", 
                batch_id, 
                {
                    "total_requests": len(self.batch_queues[batch_id]),
                    "approved": approved_count,
                    "failed": failed_count,
                    "comments": comments
                }
            )
            
            return True, {
                "batch_id": batch_id,
                "total": len(self.batch_queues[batch_id]),
                "approved": approved_count,
                "failed": failed_count,
                "results": results
            }
    
    def reject_batch(
        self, 
        batch_id: str, 
        approver_id: str, 
        comments: str = ""
    ) -> Tuple[bool, Dict[str, str]]:
        """Reject all requests in a batch"""
        with self.lock:
            if batch_id not in self.batch_queues:
                return False, {"error": "Batch not found"}
            
            approver = self.users.get(approver_id)
            if not approver or not approver.can_batch_approve:
                return False, {"error": "Insufficient permissions for batch rejection"}
            
            results = {}
            rejected_count = 0
            failed_count = 0
            
            for request in self.batch_queues[batch_id]:
                if request.status == ApprovalStatus.PENDING:
                    success, message = self.reject_request(
                        request.request_id, 
                        approver_id, 
                        f"Batch rejection: {comments}"
                    )
                    results[request.request_id] = message
                    if success:
                        rejected_count += 1
                    else:
                        failed_count += 1
            
            # Log batch rejection
            self._log_action(
                approver_id, 
                "batch_rejected", 
                batch_id, 
                {
                    "total_requests": len(self.batch_queues[batch_id]),
                    "rejected": rejected_count,
                    "failed": failed_count,
                    "comments": comments
                }
            )
            
            return True, {
                "batch_id": batch_id,
                "total": len(self.batch_queues[batch_id]),
                "rejected": rejected_count,
                "failed": failed_count,
                "results": results
            }
    
    # ==================== QUERY METHODS ====================
    
    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get request by ID"""
        return self.requests.get(request_id)
    
    def get_pending_requests(self, approver_id: str) -> List[ApprovalRequest]:
        """Get pending requests for an approver"""
        pending = []
        
        for request in self.requests.values():
            if request.status == ApprovalStatus.PENDING:
                if (request.current_step_index < len(request.steps) and 
                    request.steps[request.current_step_index].approver_id == approver_id):
                    pending.append(request)
        
        # Sort by priority and creation time
        pending.sort(key=lambda r: (
            self.config["priority_queue_weights"][r.priority],
            r.created_at
        ), reverse=True)
        
        return pending
    
    def get_delegated_requests(self, delegate_id: str) -> List[ApprovalRequest]:
        """Get requests delegated to a user"""
        delegated = []
        
        for request in self.requests.values():
            if (request.status == ApprovalStatus.PENDING and
                request.delegated_from and
                request.current_step_index < len(request.steps)):
                
                # Check if the current step is assigned to this delegate
                current_step = request.steps[request.current_step_index]
                if current_step.approver_id == delegate_id:
                    delegated.append(request)
        
        return delegated
    
    def get_batch_requests(self, batch_id: str) -> List[ApprovalRequest]:
        """Get all requests in a batch"""
        return self.batch_queues.get(batch_id, [])
    
    def search_requests(
        self,
        status: Optional[ApprovalStatus] = None,
        requester_id: Optional[str] = None,
        priority: Optional[ApprovalPriority] = None,
        mode: Optional[ApprovalMode] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ApprovalRequest]:
        """Search requests with filters"""
        results = list(self.requests.values())
        
        if status:
            results = [r for r in results if r.status == status]
        
        if requester_id:
            results = [r for r in results if r.requester_id == requester_id]
        
        if priority:
            results = [r for r in results if r.priority == priority]
        
        if mode:
            results = [r for r in results if r.mode == mode]
        
        if date_from:
            results = [r for r in results if r.created_at >= date_from]
        
        if date_to:
            results = [r for r in results if r.created_at <= date_to]
        
        # Sort by creation time (newest first)
        results.sort(key=lambda r: r.created_at, reverse=True)
        
        return results[:limit]
    
    def get_request_history(self, request_id: str) -> List[ApprovalHistory]:
        """Get approval history for a request"""
        return self.history.get(request_id, [])
    
    def get_user_history(self, user_id: str, limit: int = 100) -> List[ApprovalHistory]:
        """Get approval history for a user"""
        user_history = []
        
        for request_history in self.history.values():
            for entry in request_history:
                if entry.user_id == user_id:
                    user_history.append(entry)
        
        # Sort by timestamp (newest first)
        user_history.sort(key=lambda h: h.timestamp, reverse=True)
        
        return user_history[:limit]
    
    # ==================== VALIDATION & INTEGRATION ====================
    
    def integrate_phase4_risk_validation(self, request_id: str, risk_score: float, validation_details: Dict[str, Any]) -> bool:
        """Integrate with Phase 4 risk validation"""
        with self.lock:
            if request_id not in self.requests:
                return False
            
            request = self.requests[request_id]
            request.risk_score = risk_score
            request.phase_4_validated = True
            
            # Store validation details in metadata
            request.metadata["phase4_validation"] = validation_details
            request.metadata["phase4_validated_at"] = datetime.now().isoformat()
            
            # Log integration
            self._log_action(
                "phase4_system", 
                "risk_validation", 
                request_id, 
                {
                    "risk_score": risk_score,
                    "validation_details": validation_details
                }
            )
            
            # Trigger risk-based actions
            if risk_score > 0.8:
                # High risk - escalate priority
                request.priority = ApprovalPriority.CRITICAL
                logger.warning(f"High risk score {risk_score} for request {request_id} - escalated to critical")
            
            return True
    
    def _trigger_phase5_execution(self, request: ApprovalRequest):
        """Trigger Phase 5 execution coordination"""
        try:
            # Create execution coordination ID
            coord_id = f"exec_{request.request_id}_{int(time.time())}"
            request.phase_5_coord_id = coord_id
            
            # Prepare execution payload
            execution_payload = {
                "coordination_id": coord_id,
                "request_id": request.request_id,
                "approved_at": request.approved_at.isoformat(),
                "approver_id": request.steps[-1].approver_id if request.steps else None,
                "request_details": asdict(request),
                "phase4_validated": request.phase_4_validated,
                "risk_score": request.risk_score
            }
            
            # Log Phase 5 trigger
            self._log_action(
                "system", 
                "phase5_execution_triggered", 
                request.request_id, 
                {
                    "coordination_id": coord_id,
                    "payload": execution_payload
                }
            )
            
            # Notify Phase 5 system (external integration point)
            self._notify_observers("phase5_execution", {
                "coordination_id": coord_id,
                "request_id": request.request_id,
                "payload": execution_payload
            })
            
            logger.info(f"Phase 5 execution triggered for request {request.request_id} with coordination ID {coord_id}")
            
        except Exception as e:
            logger.error(f"Error triggering Phase 5 execution for {request.request_id}: {e}")
    
    # ==================== HELPER METHODS ====================
    
    def _can_approve(self, request: ApprovalRequest, approver: User) -> bool:
        """Check if user can approve the request"""
        # Emergency override permission
        if approver.can_emergency_override:
            return True
        
        # Role-based permission
        if "approve_all" in approver.permissions:
            return True
        
        # Check approval limits
        if request.tier and request.amount:
            limit = approver.approval_limits.get(request.tier, 0)
            if request.amount <= limit:
                return True
        
        # Check specific role requirement
        if request.current_step_index < len(request.steps):
            current_step = request.steps[request.current_step_index]
            if current_step.role in approver.roles:
                return True
        
        return False
    
    def _get_delegation_depth(self, user_id: str) -> int:
        """Get delegation depth for a user"""
        depth = 0
        for chain in self.delegation_tree.values():
            if user_id in chain:
                position = chain.index(user_id)
                depth = max(depth, position + 1)
        return depth
    
    def _check_timeouts(self):
        """Check for timed out requests"""
        current_time = datetime.now()
        
        for request in self.requests.values():
            if request.status == ApprovalStatus.PENDING:
                # Check overall timeout
                if request.expires_at and current_time > request.expires_at:
                    request.status = ApprovalStatus.EXPIRED
                    self._log_action("system", "request_expired", request.request_id, {})
                    self._notify_observers("expired", request)
                
                # Check step timeout
                elif (request.current_step_index < len(request.steps) and
                      request.steps[request.current_step_index].expires_at and
                      current_time > request.steps[request.current_step_index].expires_at):
                    
                    # Auto-reject or escalate
                    if request.escalation_count < request.max_escalations:
                        self._escalate_request(request)
                    else:
                        request.status = ApprovalStatus.EXPIRED
                        self._log_action("system", "request_expired", request.request_id, {})
                        self._notify_observers("expired", request)
    
    def _check_escalations(self):
        """Check for requests that need escalation"""
        current_time = datetime.now()
        
        for request in self.requests.values():
            if request.status == ApprovalStatus.PENDING:
                # Check if step has been pending for too long
                if (request.current_step_index < len(request.steps) and
                    request.steps[request.current_step_index].assigned_at):
                    
                    assigned_time = request.steps[request.current_step_index].assigned_at
                    time_since_assignment = current_time - assigned_time
                    escalation_threshold = timedelta(minutes=self.config["escalation_interval_minutes"])
                    
                    if time_since_assignment > escalation_threshold:
                        self._escalate_request(request)
    
    def _escalate_request(self, request: ApprovalRequest):
        """Escalate a request to higher authority"""
        request.escalation_count += 1
        current_step = request.steps[request.current_step_index]
        
        # Find alternative approver (admin or senior role)
        alternative_approver = None
        for user in self.users.values():
            if ("admin" in user.roles or "senior_approver" in user.roles) and user.is_active:
                alternative_approver = user
                break
        
        if alternative_approver:
            # Update current step
            current_step.status = ApprovalStatus.ESCALATED
            
            # Create new step for alternative approver
            new_step = ApprovalStep(
                step_id=str(uuid.uuid4()),
                approver_id=alternative_approver.user_id,
                role=current_step.role,
                status=ApprovalStatus.PENDING,
                assigned_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=2)
            )
            
            request.steps.insert(request.current_step_index + 1, new_step)
            
            # Increase priority
            if request.priority.value < ApprovalPriority.URGENT.value:
                request.priority = ApprovalPriority( min(request.priority.value + 1, ApprovalPriority.URGENT.value))
            
            # Log escalation
            self._log_action(
                "system", 
                "request_escalated", 
                request.request_id, 
                {
                    "escalation_count": request.escalation_count,
                    "escalated_to": alternative_approver.user_id
                }
            )
            
            # Notify observers
            self._notify_observers("escalated", request)
            
            logger.info(f"Request {request.request_id} escalated to {alternative_approver.user_id}")
    
    def _log_action(self, user_id: str, action: str, target_id: str, details: Dict[str, Any]):
        """Log an action to audit trail"""
        history_entry = ApprovalHistory(
            history_id=str(uuid.uuid4()),
            request_id=target_id if action in ["approved", "rejected", "delegated", "emergency_override", "phase5_execution_triggered"] else "",
            action=action,
            user_id=user_id,
            timestamp=datetime.now(),
            details=details
        )
        
        if history_entry.request_id:
            self.history[history_entry.request_id].append(history_entry)
        else:
            # Log system actions to a special key
            self.history[f"system_{target_id}"].append(history_entry)
    
    def _notify_observers(self, event_type: str, data: Any):
        """Notify registered observers"""
        for observer in self.observers:
            try:
                observer(event_type, data)
            except Exception as e:
                logger.error(f"Observer notification error: {e}")
    
    def register_observer(self, observer: Callable[[str, Any], None]):
        """Register an observer for system events"""
        self.observers.append(observer)
    
    def unregister_observer(self, observer: Callable[[str, Any], None]):
        """Unregister an observer"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    # ==================== UTILITY METHODS ====================
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        queue_size = self.approval_queue.qsize()
        
        # Count requests by status
        status_counts = defaultdict(int)
        for request in self.requests.values():
            status_counts[request.status.value] += 1
        
        # Count requests by priority
        priority_counts = defaultdict(int)
        for request in self.requests.values():
            if request.status in [ApprovalStatus.PENDING, ApprovalStatus.DELEGATED]:
                priority_counts[request.priority.name] += 1
        
        return {
            "queue_size": queue_size,
            "total_requests": len(self.requests),
            "status_counts": dict(status_counts),
            "pending_by_priority": dict(priority_counts),
            "batch_queues": len(self.batch_queues),
            "active_users": len([u for u in self.users.values() if u.is_active]),
            "rules_active": len([r for r in self.rules.values() if r.active])
        }
    
    def get_approver_workload(self) -> Dict[str, Dict[str, Any]]:
        """Get workload statistics for approvers"""
        workload = {}
        
        for user in self.users.values():
            if "approver" in user.roles or "admin" in user.roles:
                pending_count = len(self.get_pending_requests(user.user_id))
                delegated_count = len(self.get_delegated_requests(user.user_id))
                
                # Get approval statistics from history
                history = self.get_user_history(user.user_id, limit=1000)
                approved_count = len([h for h in history if h.action == "approved"])
                rejected_count = len([h for h in history if h.action == "rejected"])
                delegated_count_history = len([h for h in history if h.action == "delegated"])
                
                workload[user.user_id] = {
                    "username": user.username,
                    "roles": list(user.roles),
                    "pending_requests": pending_count,
                    "delegated_requests": delegated_count,
                    "total_pending": pending_count + delegated_count,
                    "approved_count": approved_count,
                    "rejected_count": rejected_count,
                    "delegated_count": delegated_count_history,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                }
        
        return workload
    
    def export_audit_trail(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        format_type: str = "json"
    ) -> str:
        """Export audit trail for compliance"""
        all_history = []
        
        for request_history in self.history.values():
            for entry in request_history:
                if start_date <= entry.timestamp <= end_date:
                    all_history.append(asdict(entry))
        
        if format_type.lower() == "json":
            return json.dumps(all_history, indent=2, default=str)
        else:
            # Simple CSV format
            csv_lines = ["history_id,request_id,action,user_id,timestamp,details"]
            for entry in all_history:
                details_str = json.dumps(entry["details"]).replace('"', '""')
                csv_lines.append(
                    f'{entry["history_id"]},{entry["request_id"]},{entry["action"]},'
                    f'{entry["user_id"]},{entry["timestamp"]},"{details_str}"'
                )
            return "\n".join(csv_lines)
    
    def cleanup_expired_requests(self, days_old: int = 30) -> int:
        """Clean up old expired requests"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_count = 0
        
        with self.lock:
            expired_request_ids = []
            
            for request_id, request in self.requests.items():
                if (request.status in [ApprovalStatus.EXPIRED, ApprovalStatus.CANCELLED] and
                    (request.rejected_at or request.created_at) < cutoff_date):
                    expired_request_ids.append(request_id)
            
            for request_id in expired_request_ids:
                del self.requests[request_id]
                if request_id in self.history:
                    del self.history[request_id]
                cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} expired requests older than {days_old} days")
        return cleaned_count


# ==================== DEMO AND USAGE EXAMPLE ====================

def demo_approval_workflow():
    """Demonstrate the approval workflow system"""
    print("=== Approval Workflow System Demo ===\n")
    
    # Initialize system
    system = ApprovalWorkflowSystem()
    
    # Register event observer
    def event_observer(event_type: str, data: Any):
        print(f"Event: {event_type} - Request: {data.request_id if hasattr(data, 'request_id') else 'N/A'}")
    
    system.register_observer(event_observer)
    
    # Create additional users
    users_data = [
        User(
            user_id="manager_1",
            username="manager1",
            email="manager1@company.com",
            roles={"manager", "approver"},
            permissions={"approve", "view_requests"},
            approval_limits={
                ApprovalTier.TIER_1: 5000.0,
                ApprovalTier.TIER_2: 25000.0,
                ApprovalTier.TIER_3: 250000.0,
            }
        ),
        User(
            user_id="director_1",
            username="director1",
            email="director1@company.com",
            roles={"director", "approver"},
            permissions={"approve", "view_requests"},
            approval_limits={
                ApprovalTier.TIER_1: float('inf'),
                ApprovalTier.TIER_2: float('inf'),
                ApprovalTier.TIER_3: float('inf'),
                ApprovalTier.TIER_4: float('inf'),
            },
            can_batch_approve=True
        )
    ]
    
    for user in users_data:
        system.create_user(user)
    
    # Create approval requests
    print("1. Creating approval requests...")
    
    # Small amount request (should auto-approve)
    small_request_id = system.create_approval_request(
        title="Office Supplies Purchase",
        description="Purchase of office supplies for Q4",
        requester_id="admin",
        request_type="purchase",
        amount=50.0,
        priority=ApprovalPriority.LOW
    )
    
    # Medium amount request (manual approval)
    medium_request_id = system.create_approval_request(
        title="Software License Renewal",
        description="Annual renewal of project management software",
        requester_id="manager_1",
        request_type="license",
        amount=5000.0,
        priority=ApprovalPriority.MEDIUM
    )
    
    # Large amount request (multi-step approval)
    large_request_id = system.create_approval_request(
        title="Infrastructure Upgrade",
        description="Server and network equipment upgrade",
        requester_id="director_1",
        request_type="infrastructure",
        amount=250000.0,
        priority=ApprovalPriority.HIGH
    )
    
    print(f"Created requests: {small_request_id}, {medium_request_id}, {large_request_id}\n")
    
    # Check auto-approval
    print("2. Checking auto-approval...")
    small_request = system.get_request(small_request_id)
    print(f"Small request status: {small_request.status.value}")
    print(f"Large request status: {system.get_request(large_request_id).status.value}\n")
    
    # Get pending requests for approver
    print("3. Getting pending requests for approver_1...")
    pending = system.get_pending_requests("approver_1")
    print(f"Found {len(pending)} pending requests for approver_1")
    for req in pending:
        print(f"  - {req.title} (${req.amount}, Priority: {req.priority.name})")
    print()
    
    # Approve medium request
    print("4. Approving medium request...")
    success, message = system.approve_request(
        medium_request_id, 
        "approver_1", 
        "Approved after reviewing budget allocation"
    )
    print(f"Approval result: {success} - {message}\n")
    
    # Create batch for large requests
    print("5. Creating batch for large requests...")
    batch_id = "batch_001"
    system.create_batch(batch_id, "director_1")
    
    # Add large request to batch
    system.add_to_batch(batch_id, large_request_id)
    
    # Batch approve
    print("6. Batch approving...")
    success, results = system.approve_batch(
        batch_id, 
        "director_1", 
        "Approved as part of Q4 infrastructure initiative"
    )
    print(f"Batch approval result: {success}")
    print(f"Results: {results}\n")
    
    # Demonstrate delegation
    print("7. Demonstrating delegation...")
    if large_request_id:
        large_request = system.get_request(large_request_id)
        if large_request.status == ApprovalStatus.PENDING:
            success, message = system.delegate_approval(
                large_request_id,
                "approver_1",
                "manager_1",
                "Delegating to manager for detailed review"
            )
            print(f"Delegation result: {success} - {message}\n")
    
    # Show system status
    print("8. System status...")
    status = system.get_queue_status()
    print(f"Queue status: {json.dumps(status, indent=2)}\n")
    
    # Show approver workload
    print("9. Approver workload...")
    workload = system.get_approver_workload()
    print(f"Workload: {json.dumps(workload, indent=2)}\n")
    
    # Show approval history
    print("10. Recent approval history...")
    history = system.get_user_history("approver_1", limit=5)
    for entry in history:
        print(f"  {entry.timestamp}: {entry.action} - {entry.request_id}")
    print()
    
    print("=== Demo Complete ===")


if __name__ == "__main__":
    demo_approval_workflow()