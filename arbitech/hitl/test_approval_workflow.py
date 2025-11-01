#!/usr/bin/env python3
"""
Test script for the Approval Workflow System
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

def test_basic_functionality():
    """Test basic approval workflow functionality"""
    print("Testing Basic Approval Workflow System...")
    print("=" * 50)
    
    # Initialize system
    system = ApprovalWorkflowSystem()
    
    # Create test users
    admin_user = User(
        user_id="test_admin",
        username="test_admin",
        email="admin@test.com",
        roles={"admin", "approver"},
        permissions={"approve_all", "emergency_override"},
        can_emergency_override=True
    )
    
    manager_user = User(
        user_id="test_manager",
        username="test_manager", 
        email="manager@test.com",
        roles={"manager", "approver"},
        permissions={"approve"},
        approval_limits={
            ApprovalTier.TIER_1: 10000.0,
            ApprovalTier.TIER_2: 50000.0
        }
    )
    
    # Add users
    system.create_user(admin_user)
    system.create_user(manager_user)
    print(f"✓ Created users: {admin_user.user_id}, {manager_user.user_id}")
    
    # Test 1: Create approval request
    request_id = system.create_approval_request(
        title="Test Purchase Order",
        description="Testing approval workflow system",
        requester_id="test_admin",
        request_type="purchase_order",
        amount=5000.0,
        priority=ApprovalPriority.MEDIUM
    )
    print(f"✓ Created approval request: {request_id}")
    
    # Test 2: Check request exists
    request = system.get_request(request_id)
    assert request is not None, "Request should exist"
    assert request.title == "Test Purchase Order", "Request title should match"
    print(f"✓ Retrieved request: {request.title}")
    
    # Test 3: Get pending requests (assigned to admin by default for tier 2)
    pending = system.get_pending_requests("admin")
    assert len(pending) > 0, "Should have pending requests"
    print(f"✓ Found {len(pending)} pending requests for admin")
    
    # Test 4: Approve request
    success, message = system.approve_request(
        request_id,
        "admin", 
        "Approved for testing"
    )
    assert success, f"Approval should succeed: {message}"
    print(f"✓ Approved request: {message}")
    
    # Test 5: Check approved status
    updated_request = system.get_request(request_id)
    assert updated_request.status == ApprovalStatus.APPROVED, "Status should be approved"
    print(f"✓ Request status updated to: {updated_request.status.value}")
    
    # Test 6: Get history
    history = system.get_request_history(request_id)
    assert len(history) > 0, "Should have history entries"
    print(f"✓ Found {len(history)} history entries")
    
    # Test 7: Emergency override (admin function)
    emergency_id = system.create_approval_request(
        title="Emergency Purchase",
        description="Urgent emergency purchase",
        requester_id="test_admin",
        request_type="emergency",
        amount=1000.0,
        priority=ApprovalPriority.URGENT
    )
    
    success, message = system.emergency_override(
        emergency_id,
        "test_admin",
        "Emergency override for testing"
    )
    assert success, f"Emergency override should succeed: {message}"
    print(f"✓ Emergency override successful: {message}")
    
    # Test 8: System status
    status = system.get_queue_status()
    assert "total_requests" in status, "Status should include total_requests"
    print(f"✓ System status retrieved: {status['total_requests']} total requests")
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Approval workflow system is working correctly.")
    return True

def test_batch_processing():
    """Test batch processing functionality"""
    print("\nTesting Batch Processing...")
    print("=" * 30)
    
    system = ApprovalWorkflowSystem()
    
    # Create batch approver
    batch_approver = User(
        user_id="batch_approver",
        username="batch_approver",
        email="batch@test.com",
        roles={"approver"},
        permissions={"approve"},
        can_batch_approve=True
    )
    
    system.create_user(batch_approver)
    
    # Create batch
    batch_id = "test_batch_001"
    success = system.create_batch(batch_id, "batch_approver")
    assert success, "Batch creation should succeed"
    print(f"✓ Created batch: {batch_id}")
    
    # Create multiple requests and add to batch
    request_ids = []
    for i in range(3):
        req_id = system.create_approval_request(
            title=f"Batch Item {i+1}",
            description=f"Testing batch processing item {i+1}",
            requester_id="batch_approver",
            request_type="batch_test",
            amount=100.0 * (i+1),
            priority=ApprovalPriority.LOW
        )
        
        if req_id:
            system.add_to_batch(batch_id, req_id)
            request_ids.append(req_id)
    
    print(f"✓ Added {len(request_ids)} requests to batch")
    
    # Get batch requests
    batch_requests = system.get_batch_requests(batch_id)
    assert len(batch_requests) == len(request_ids), "All requests should be in batch"
    print(f"✓ Batch contains {len(batch_requests)} requests")
    
    # Batch approve
    success, results = system.approve_batch(
        batch_id,
        "batch_approver",
        "Batch approval test"
    )
    assert success, "Batch approval should succeed"
    assert "approved" in results, "Results should include approved count"
    print(f"✓ Batch approval completed: {results['approved']} approved")
    
    return True

def test_delegation():
    """Test approval delegation"""
    print("\nTesting Delegation...")
    print("=" * 20)
    
    system = ApprovalWorkflowSystem()
    
    # Create delegator and delegate
    delegator = User(
        user_id="delegator",
        username="delegator",
        email="delegator@test.com",
        roles={"approver"},
        permissions={"approve"},
        can_delegate=True
    )
    
    delegate = User(
        user_id="delegate",
        username="delegate", 
        email="delegate@test.com",
        roles={"approver"},
        permissions={"approve"}
    )
    
    system.create_user(delegator)
    system.create_user(delegate)
    
    # Create request
    request_id = system.create_approval_request(
        title="Delegation Test",
        description="Testing delegation functionality",
        requester_id="delegator",
        request_type="delegation_test",
        amount=50000.0,  # Higher amount to get assigned to delegator
        priority=ApprovalPriority.MEDIUM
    )
    
    # Delegate approval
    success, message = system.delegate_approval(
        request_id,
        "delegator",
        "delegate",
        "Delegating for review"
    )
    
    assert success, f"Delegation should succeed: {message}"
    print(f"✓ Delegation successful: {message}")
    
    # Check delegated requests
    delegated = system.get_delegated_requests("delegate")
    assert len(delegated) > 0, "Should have delegated requests"
    print(f"✓ Found {len(delegated)} delegated requests")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Approval Workflow System Tests\n")
    
    try:
        # Run tests
        test_basic_functionality()
        test_batch_processing()
        test_delegation()
        
        print("\n" + "🎉" * 20)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("The approval workflow system is fully functional.")
        print("🎉" * 20)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)