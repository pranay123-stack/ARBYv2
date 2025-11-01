#!/usr/bin/env python3
"""
Simple delegation test
"""

import sys
sys.path.append('/workspace/arbitech/hitl')

from approval_workflow import (
    ApprovalWorkflowSystem,
    User,
    ApprovalPriority,
    ApprovalTier,
    ApprovalStatus
)

def simple_delegation_test():
    """Simple delegation test"""
    print("Simple Delegation Test...")
    print("=" * 30)
    
    system = ApprovalWorkflowSystem()
    
    # Create a user with admin privileges so they get assigned the request
    admin_user = User(
        user_id="test_delegator",
        username="test_delegator",
        email="delegator@test.com",
        roles={"admin", "approver"},
        permissions={"approve"},
        can_delegate=True
    )
    
    delegate_user = User(
        user_id="test_delegate",
        username="test_delegate", 
        email="delegate@test.com",
        roles={"approver"},
        permissions={"approve"}
    )
    
    system.create_user(admin_user)
    system.create_user(delegate_user)
    
    # Create a request that should be assigned to the admin user
    request_id = system.create_approval_request(
        title="Delegation Test Request",
        description="Testing delegation",
        requester_id="test_delegator",
        request_type="test",
        amount=100000.0,  # High amount to ensure admin gets it
        priority=ApprovalPriority.MEDIUM
    )
    
    if request_id:
        request = system.get_request(request_id)
        print(f"Created request: {request_id}")
        print(f"Status: {request.status.value}")
        print(f"Steps: {len(request.steps)}")
        
        if request.steps:
            current_step = request.steps[request.current_step_index]
            print(f"Current step assigned to: {current_step.approver_id}")
            actual_approver = current_step.approver_id
        
        # Try to delegate from the actual approver
        print(f"\nAttempting delegation from {actual_approver} to test_delegate...")
        success, message = system.delegate_approval(
            request_id,
            actual_approver,  # Delegate from the actual approver
            "test_delegate",
            "Delegating for testing"
        )
        
        print(f"Delegation result: {success} - {message}")
        
        if success:
            # Check updated request
            updated_request = system.get_request(request_id)
            print(f"\nAfter delegation:")
            print(f"Status: {updated_request.status.value}")
            print(f"Steps: {len(updated_request.steps)}")
            
            if updated_request.steps:
                for i, step in enumerate(updated_request.steps):
                    print(f"  Step {i+1}: {step.approver_id} ({step.status.value})")
            
            # Check delegated requests
            print(f"\nDebug: checking for delegated requests for test_delegate")
            print(f"Request delegated_from: {updated_request.delegated_from}")
            print(f"Request status: {updated_request.status.value}")
            if updated_request.steps:
                current_step = updated_request.steps[updated_request.current_step_index]
                print(f"Current step approver: {current_step.approver_id}")
            
            delegated = system.get_delegated_requests("test_delegate")
            print(f"\nDelegated requests for test_delegate: {len(delegated)}")
            for req in delegated:
                print(f"  - {req.title}")
        else:
            print("❌ Delegation failed")

if __name__ == "__main__":
    simple_delegation_test()