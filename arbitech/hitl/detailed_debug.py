#!/usr/bin/env python3
"""
Detailed debug script for the Approval Workflow System
"""

import sys
sys.path.append('/workspace/arbitech/hitl')

from approval_workflow import (
    ApprovalWorkflowSystem,
    User,
    ApprovalPriority,
    ApprovalMode,
    ApprovalTier,
    ApprovalStatus
)

def detailed_debug():
    """Detailed debug of request creation and approval flow"""
    print("Detailed Debug of Request Creation and Approval Flow...")
    print("=" * 60)
    
    # Initialize system
    system = ApprovalWorkflowSystem()
    
    # Create test user with admin role
    admin_user = User(
        user_id="debug_admin",
        username="debug_admin",
        email="admin@test.com",
        roles={"admin", "approver"},
        permissions={"approve_all", "emergency_override"},
        can_emergency_override=True
    )
    
    system.create_user(admin_user)
    print(f"✓ Created user: {admin_user.user_id}")
    
    # Check all users
    print(f"\nAll users in system:")
    for user_id, user in system.users.items():
        print(f"  {user_id}: {user.roles}")
    
    # Create approval request
    print(f"\n--- Creating Request ---")
    request_id = system.create_approval_request(
        title="Debug Purchase Order",
        description="Debugging approval workflow system",
        requester_id="debug_admin",
        request_type="purchase_order",
        amount=5000.0,
        priority=ApprovalPriority.MEDIUM,
        mode=ApprovalMode.MANUAL
    )
    
    if request_id:
        request = system.get_request(request_id)
        print(f"✓ Created request: {request_id}")
        print(f"Request Details:")
        print(f"  Title: {request.title}")
        print(f"  Amount: ${request.amount}")
        print(f"  Tier: {request.tier}")
        print(f"  Mode: {request.mode.value}")
        print(f"  Status: {request.status.value}")
        print(f"  Priority: {request.priority.name}")
        print(f"  Steps: {len(request.steps)}")
        
        if request.steps:
            for i, step in enumerate(request.steps):
                print(f"    Step {i+1}:")
                print(f"      Approver: {step.approver_id}")
                print(f"      Status: {step.status.value}")
                print(f"      Role: {step.role}")
                print(f"      Assigned: {step.assigned_at}")
        else:
            print("  No steps created!")
        
        # Check if request is auto-approved
        print(f"\nAuto-approval check:")
        print(f"  Status: {request.status.value}")
        if request.status == ApprovalStatus.AUTO_APPROVED:
            print(f"  ✓ Request was auto-approved")
        elif request.status == ApprovalStatus.PENDING:
            print(f"  ✓ Request is pending manual approval")
        
        # Check pending requests for admin
        print(f"\n--- Checking Pending Requests ---")
        pending_admin = system.get_pending_requests("debug_admin")
        print(f"Pending requests for debug_admin: {len(pending_admin)}")
        for req in pending_admin:
            print(f"  - {req.title} (${req.amount})")
        
        # Also check all pending requests regardless of assignees
        print(f"\nAll pending requests in system:")
        for req_id, req in system.requests.items():
            if req.status == ApprovalStatus.PENDING:
                print(f"  {req_id}: {req.title} - {req.status.value}")
                if req.steps:
                    current_step = req.steps[req.current_step_index] if req.current_step_index < len(req.steps) else None
                    if current_step:
                        print(f"    Current step assigned to: {current_step.approver_id}")
        
        # Try to approve the request manually
        print(f"\n--- Manual Approval Test ---")
        success, message = system.approve_request(
            request_id,
            "debug_admin", 
            "Manual approval test"
        )
        print(f"Manual approval result: {success} - {message}")
        
        # Check status after approval
        updated_request = system.get_request(request_id)
        print(f"Status after approval: {updated_request.status.value}")
        
    else:
        print("❌ Failed to create request")

if __name__ == "__main__":
    detailed_debug()