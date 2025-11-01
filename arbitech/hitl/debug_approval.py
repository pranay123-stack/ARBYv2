#!/usr/bin/env python3
"""
Debug script for the Approval Workflow System
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

def debug_request_creation():
    """Debug request creation process"""
    print("Debugging Request Creation Process...")
    print("=" * 50)
    
    # Initialize system
    system = ApprovalWorkflowSystem()
    
    # Create test user
    manager_user = User(
        user_id="debug_manager",
        username="debug_manager", 
        email="manager@test.com",
        roles={"manager", "approver"},
        permissions={"approve"},
        approval_limits={
            ApprovalTier.TIER_1: 10000.0,
            ApprovalTier.TIER_2: 50000.0
        }
    )
    
    system.create_user(manager_user)
    print(f"✓ Created user: {manager_user.user_id}")
    
    # Create approval request
    request_id = system.create_approval_request(
        title="Debug Purchase Order",
        description="Debugging approval workflow system",
        requester_id="debug_manager",
        request_type="purchase_order",
        amount=5000.0,
        priority=ApprovalPriority.MEDIUM,
        mode=ApprovalMode.MANUAL  # Force manual mode
    )
    
    if request_id:
        request = system.get_request(request_id)
        print(f"\n=== Request Details ===")
        print(f"ID: {request.request_id}")
        print(f"Title: {request.title}")
        print(f"Amount: ${request.amount}")
        print(f"Tier: {request.tier}")
        print(f"Mode: {request.mode.value}")
        print(f"Status: {request.status.value}")
        print(f"Priority: {request.priority.name}")
        print(f"Steps: {len(request.steps)}")
        
        if request.steps:
            for i, step in enumerate(request.steps):
                print(f"  Step {i+1}: {step.approver_id} ({step.status.value})")
        else:
            print("  No steps created")
        
        # Check rules
        applicable_rules = system.get_applicable_rules(request)
        print(f"\nApplicable Rules: {len(applicable_rules)}")
        for rule in applicable_rules:
            print(f"  - {rule.name}: auto_approve={rule.auto_approve}")
        
        # Check thresholds
        print(f"\nAuto-approve thresholds:")
        for tier, threshold in system.config["auto_approve_thresholds"].items():
            print(f"  {tier.value}: ${threshold}")
        
        print(f"\nThreshold for TIER_2: ${system.config['auto_approve_thresholds'].get(ApprovalTier.TIER_2)}")
        
        # Check pending requests
        pending = system.get_pending_requests("debug_manager")
        print(f"\nPending requests for debug_manager: {len(pending)}")
        for req in pending:
            print(f"  - {req.title} (${req.amount}, {req.status.value})")
        
        # Check all requests status
        print(f"\nAll requests in system:")
        for req_id, req in system.requests.items():
            print(f"  {req_id}: {req.title} - {req.status.value}")
    
    else:
        print("❌ Failed to create request")

if __name__ == "__main__":
    debug_request_creation()