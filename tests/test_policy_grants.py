"""
Tests for policy and grants functionality
"""

import pytest
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from policy_grants import PolicyManager, PolicyType
except ImportError as e:
    pytest.skip(f"Could not import policy_grants module: {e}", allow_module_level=True)


class TestPolicyManager:
    """Test cases for PolicyManager class"""

    @pytest.fixture
    def policy_manager(self, temp_dir):
        """Create a PolicyManager instance for testing"""
        return PolicyManager(base_dir=temp_dir)

    def test_initialization(self, policy_manager):
        """Test that PolicyManager initializes correctly"""
        assert policy_manager is not None
        assert hasattr(policy_manager, "base_dir")
        assert hasattr(policy_manager, "policy_dir")

    def test_create_policy(self, policy_manager):
        """Test policy creation"""
        policy_id = "test_budget_policy"
        policy_type = PolicyType.RATE_LIMIT
        parameters = {"max_requests": 100, "time_window": 3600}
        description = "Test rate limiting policy"

        policy = policy_manager.create_policy(
            policy_id, policy_type, parameters, description
        )

        assert isinstance(policy, dict)
        assert policy["policy_id"] == policy_id
        assert policy["type"] == policy_type.value
        assert policy["parameters"] == parameters
        assert policy["description"] == description
        assert "created_at" in policy
        assert "active" in policy
        assert policy["active"] is True

    def test_add_policy(self, policy_manager):
        """Test policy registration"""
        policy = policy_manager.create_policy(
            "test_policy", PolicyType.TRUST_THRESHOLD, {"min_trust": 0.8}, "Test policy"
        )

        result = policy_manager.add_policy(policy)
        assert result is True

        # Verify policy is registered
        policies = policy_manager.load_policies()
        assert policy["policy_id"] in policies["policies"]

    def test_get_active_policies(self, policy_manager):
        """Test listing active policies"""
        # Create multiple policies
        for i in range(3):
            policy = policy_manager.create_policy(
                f"active_policy_{i}",
                PolicyType.SKILL_REQUIRED,
                {"required_skills": [f"skill_{i}"]},
                f"Test policy {i}",
            )
            policy_manager.add_policy(policy)

        active_policies = policy_manager.get_active_policies()
        assert len(active_policies) >= 3  # May have more from other tests
        assert all(policy["active"] is True for policy in active_policies)

    def test_create_grant(self, policy_manager):
        """Test grant creation"""
        grant_id = "test_grant_001"
        grantee_did = "did:epoch5:user456"
        resource = "test_resource"
        actions = ["read", "execute"]
        conditions = {"valid_until": "2024-12-31T23:59:59Z"}

        grant = policy_manager.create_grant(
            grant_id, grantee_did, resource, actions, conditions
        )

        assert isinstance(grant, dict)
        assert grant["grant_id"] == grant_id
        assert grant["grantee_did"] == grantee_did
        assert grant["resource"] == resource
        assert grant["actions"] == actions
        assert "created_at" in grant
        assert "active" in grant

    def test_add_grant(self, policy_manager):
        """Test grant registration"""
        grantee_did = "did:epoch5:grantee"
        resource = "test_resource"
        actions = ["access"]
        conditions = {}

        grant = policy_manager.create_grant(
            "register_test", grantee_did, resource, actions, conditions
        )

        result = policy_manager.add_grant(grant)
        assert result is True

        # Verify grant is registered
        grants = policy_manager.load_grants()
        assert grant["grant_id"] in grants["grants"]

    def test_check_grant(self, policy_manager):
        """Test grant verification"""
        grantee_did = "did:epoch5:grantee"
        resource = "test_resource"
        actions = ["read", "write"]
        conditions = {}

        grant = policy_manager.create_grant(
            "verify_test", grantee_did, resource, actions, conditions
        )
        policy_manager.add_grant(grant)

        # Test verification - need to check the actual method signature for check_grant
        result = policy_manager.check_grant(
            "verify_test", grantee_did, resource, "read"
        )
        assert isinstance(result, bool)

    def test_policy_evaluation(self, policy_manager):
        """Test policy evaluation"""
        policy = policy_manager.create_policy(
            "eval_test",
            PolicyType.TRUST_THRESHOLD,
            {"min_reliability": 0.8},
            "Evaluation test",
        )
        policy_manager.add_policy(policy)

        context = {"agent_reliability": 0.9}
        result = policy_manager.evaluate_policy(policy["policy_id"], context)

        assert isinstance(result, bool)
        # Since agent_reliability (0.9) >= min_reliability (0.8), this should be True
        assert result is True
