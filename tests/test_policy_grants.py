"""
Tests for policy and grants functionality
"""

import pytest
import json
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

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
        resource = "data/resource123"
        actions = ["read", "execute"]
        conditions = {"valid_until": "2024-12-31T23:59:59Z"}

        grant = policy_manager.create_grant(
            grant_id, 
            grantee_did, 
            resource, 
            actions, 
            conditions
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
        grant_id = "register_test"
        grantee_did = "grantee"
        resource = "resource/test"
        actions = ["access"]
        
        grant = policy_manager.create_grant(
            grant_id,
            grantee_did,
            resource,
            actions
        )

        result = policy_manager.add_grant(grant)
        assert result is True

        # Verify grant is registered
        grants = policy_manager.load_grants()
        assert grant["grant_id"] in grants["grants"]

    def test_check_grant(self, policy_manager):
        """Test grant verification"""
        grant_id = "verify_test"
        grantee_did = "grantee"
        resource = "resource/test"
        actions = ["read", "write"]
        
        grant = policy_manager.create_grant(
            grant_id,
            grantee_did,
            resource,
            actions
        )
        
        policy_manager.add_grant(grant)

        # Test verification
        result = policy_manager.check_grant(grant_id, grantee_did, resource, "read")
        assert isinstance(result, bool)

    def test_policy_evaluation(self, policy_manager):
        """Test policy evaluation"""
        policy = policy_manager.create_policy(
            "eval_test",
            PolicyType.TRUST_THRESHOLD,
            {"min_reliability": 0.8},  # Changed to min_reliability to match implementation
            "Evaluation test",
        )
        policy_manager.add_policy(policy)

        # Passing case
        context = {"agent_reliability": 0.9}
        result = policy_manager.evaluate_policy(policy["policy_id"], context)
        assert result is True

        # Failing case
        context = {"agent_reliability": 0.7}
        result = policy_manager.evaluate_policy(policy["policy_id"], context)
        assert result is False
    
    def test_quorum_policy(self, policy_manager):
        """Test quorum policy evaluation"""
        policy = policy_manager.create_policy(
            "quorum_test",
            PolicyType.QUORUM,
            {"required_count": 3},
            "Quorum test policy"
        )
        policy_manager.add_policy(policy)
        
        # Passing case
        context = {"approvers": ["user1", "user2", "user3", "user4"]}
        result = policy_manager.evaluate_policy(policy["policy_id"], context)
        assert result is True
        
        # Failing case
        context = {"approvers": ["user1", "user2"]}
        result = policy_manager.evaluate_policy(policy["policy_id"], context)
        assert result is False
    
    def test_multi_sig_policy(self, policy_manager):
        """Test multi signature policy evaluation"""
        policy = policy_manager.create_policy(
            "multisig_test",
            PolicyType.MULTI_SIG,
            {
                "required_signatures": 2,
                "authorized_signers": ["signer1", "signer2", "signer3"]
            },
            "Multi-signature test policy"
        )
        policy_manager.add_policy(policy)
        
        # Passing case
        context = {"signatures": ["signer1", "signer2"]}
        result = policy_manager.evaluate_policy(policy["policy_id"], context)
        assert result is True
        
        # Failing case - not enough authorized signers
        context = {"signatures": ["signer1", "unauthorized"]}
        result = policy_manager.evaluate_policy(policy["policy_id"], context)
        assert result is False
    
    def test_rate_limit_policy(self, policy_manager):
        """Test rate limit policy evaluation"""
        policy = policy_manager.create_policy(
            "rate_limit_test",
            PolicyType.RATE_LIMIT,
            {"max_requests_per_hour": 100},
            "Rate limit test policy"
        )
        policy_manager.add_policy(policy)
        
        # Passing case
        context = {"did": "test_user", "current_requests": 50}
        result = policy_manager.evaluate_policy(policy["policy_id"], context)
        assert result is True
        
        # Failing case
        context = {"did": "test_user", "current_requests": 150}
        result = policy_manager.evaluate_policy(policy["policy_id"], context)
        assert result is False
    
    def test_skill_required_policy(self, policy_manager):
        """Test skill required policy evaluation"""
        policy = policy_manager.create_policy(
            "skill_test",
            PolicyType.SKILL_REQUIRED,
            {"required_skills": ["python", "data_analysis"]},
            "Skill requirement test policy"
        )
        policy_manager.add_policy(policy)
        
        # Passing case - has all required skills
        context = {"agent_skills": ["python", "data_analysis", "machine_learning"]}
        result = policy_manager.evaluate_policy(policy["policy_id"], context)
        assert result is True
        
        # Failing case - missing required skills
        context = {"agent_skills": ["python", "machine_learning"]}
        result = policy_manager.evaluate_policy(policy["policy_id"], context)
        assert result is False
    
    def test_expired_grants(self, policy_manager):
        """Test handling of expired grants"""
        # Create a grant that's already expired
        past_date = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        grant = policy_manager.create_grant(
            "expired_grant",
            "test_did",
            "resource/test",
            ["read"],
            None,
            past_date  # Set an expired date
        )
        
        policy_manager.add_grant(grant)
        
        # Verify the expired grant fails
        result = policy_manager.check_grant("expired_grant", "test_did", "resource/test", "read")
        assert result is False
        
        # Verify the grant is now marked inactive
        grants = policy_manager.load_grants()
        assert grants["grants"]["expired_grant"]["active"] is False
    
    def test_grant_validity(self, policy_manager):
        """Test grant validity checks"""
        grant = policy_manager.create_grant(
            "validity_test_grant",
            "test_did",
            "resource/test",
            ["read", "write"]
        )
        policy_manager.add_grant(grant)
        
        # Valid check
        assert policy_manager.check_grant("validity_test_grant", "test_did", "resource/test", "read") is True
        
        # Invalid DID
        assert policy_manager.check_grant("validity_test_grant", "wrong_did", "resource/test", "read") is False
        
        # Invalid resource
        assert policy_manager.check_grant("validity_test_grant", "test_did", "wrong_resource", "read") is False
        
        # Invalid action
        assert policy_manager.check_grant("validity_test_grant", "test_did", "resource/test", "delete") is False
        
        # Non-existent grant
        assert policy_manager.check_grant("nonexistent_grant", "test_did", "resource/test", "read") is False
        
        # Test inactive grant
        # First, let's make the grant inactive
        grants = policy_manager.load_grants()
        grants["grants"]["validity_test_grant"]["active"] = False
        policy_manager.save_grants(grants)
        
        # Now check it - should return false
        assert policy_manager.check_grant("validity_test_grant", "test_did", "resource/test", "read") is False
    
    def test_log_violation(self, policy_manager):
        """Test policy violation logging"""
        policy_id = "violation_test_policy"
        context = {"user": "test_user", "action": "unauthorized_access"}
        
        # Use a context manager to mock the file operation
        with patch('builtins.open', MagicMock()) as mock_open:
            policy_manager.log_violation(policy_id, context)
            mock_open.assert_called_once()
    
    def test_get_valid_grants(self, policy_manager):
        """Test retrieving valid grants for a DID"""
        did = "test_user_did"
        
        # Create multiple grants, some expired, some for other DIDs
        # Current grant for target DID
        grant1 = policy_manager.create_grant(
            "valid_grant_1",
            did,
            "resource/1",
            ["read"]
        )
        policy_manager.add_grant(grant1)
        
        # Expired grant for target DID
        past_date = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        grant2 = policy_manager.create_grant(
            "expired_grant",
            did,
            "resource/2",
            ["read"],
            None,
            past_date
        )
        policy_manager.add_grant(grant2)
        
        # Valid grant for different DID
        grant3 = policy_manager.create_grant(
            "other_did_grant",
            "other_did",
            "resource/3",
            ["read"]
        )
        policy_manager.add_grant(grant3)
        
        # Get valid grants and verify
        valid_grants = policy_manager.get_valid_grants(did)
        
        # Should only return grant1
        assert len(valid_grants) == 1
        assert valid_grants[0]["grant_id"] == "valid_grant_1"
    
    def test_policy_evaluation_error(self, policy_manager):
        """Test policy evaluation with errors"""
        # Create a policy
        policy = policy_manager.create_policy(
            "error_test_policy",
            PolicyType.TRUST_THRESHOLD,
            {"min_reliability": 0.8},
            "Error test policy"
        )
        policy_manager.add_policy(policy)
        
        # Force an error by providing invalid context
        with patch.object(policy_manager, 'check_trust_threshold_policy', side_effect=Exception("Test error")):
            with patch.object(policy_manager, 'log_violation') as mock_log:
                result = policy_manager.evaluate_policy("error_test_policy", {})
                assert result is False
                mock_log.assert_called_once()
    
    def test_policy_evaluation_unknown_type(self, policy_manager):
        """Test policy evaluation with unknown policy type"""
        # Create a policy with a type that doesn't match any case
        # We'll need to patch to create this situation
        with patch.object(PolicyType, '__eq__', return_value=False):
            # Make a policy that won't match any type
            policy = policy_manager.create_policy(
                "unknown_type_policy",
                PolicyType.TRUST_THRESHOLD,  # Will be treated as unknown due to patch
                {"min_reliability": 0.8},
                "Unknown type policy"
            )
            policy_manager.add_policy(policy)
            
            # Evaluate the policy - should return False due to unknown type
            result = policy_manager.evaluate_policy("unknown_type_policy", {})
            assert result is False
                
    def test_policy_nonexistent(self, policy_manager):
        """Test evaluation of non-existent policy"""
        result = policy_manager.evaluate_policy("nonexistent_policy", {})
        assert result is False

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

def test_main_function():
    """Test the CLI interface main function"""
    with patch('argparse.ArgumentParser') as mock_parser, \
         patch('policy_grants.PolicyManager') as mock_manager:
        
        # Setup mock policy manager
        manager_instance = mock_manager.return_value
        manager_instance.create_policy.return_value = {"policy_id": "test_policy", "hash": "abc123"}
        manager_instance.add_policy.return_value = True
        manager_instance.create_grant.return_value = {"grant_id": "test_grant", "hash": "def456"}
        manager_instance.add_grant.return_value = True
        manager_instance.evaluate_policy.return_value = True
        manager_instance.get_active_policies.return_value = [
            {"policy_id": "policy1", "type": "trust_threshold", "enforced_count": 5, "violation_count": 1}
        ]
        manager_instance.load_grants.return_value = {
            "grants": {
                "grant1": {"grant_id": "grant1", "grantee_did": "did1", "resource": "res1", "active": True}
            }
        }
        
        # Setup argparse mock for different commands
        def setup_args(command):
            mock_args = MagicMock()
            mock_args.command = command
            mock_parser.return_value.parse_args.return_value = mock_args
            return mock_args
        
        # Test create-policy command
        args = setup_args('create-policy')
        args.policy_id = 'test_policy'
        args.policy_type = 'trust_threshold'
        args.parameters = '{"min_reliability": 0.8}'
        
        from policy_grants import main
        main()
        manager_instance.create_policy.assert_called_once()
        manager_instance.add_policy.assert_called_once()
        
        # Test create-grant command
        manager_instance.create_policy.reset_mock()
        manager_instance.add_policy.reset_mock()
        
        args = setup_args('create-grant')
        args.grant_id = 'test_grant'
        args.grantee_did = 'test_did'
        args.resource = 'test_resource'
        args.actions = ['read', 'write']
        
        main()
        manager_instance.create_grant.assert_called_once()
        manager_instance.add_grant.assert_called_once()
        
        # Test evaluate command
        manager_instance.create_grant.reset_mock()
        manager_instance.add_grant.reset_mock()
        
        args = setup_args('evaluate')
        args.policy_id = 'test_policy'
        args.context = '{"agent_reliability": 0.9}'
        
        main()
        manager_instance.evaluate_policy.assert_called_once()
        
        # Test list-policies command
        manager_instance.evaluate_policy.reset_mock()
        
        args = setup_args('list-policies')
        main()
        manager_instance.get_active_policies.assert_called_once()
        
        # Test list-grants command
        manager_instance.get_active_policies.reset_mock()
        
        args = setup_args('list-grants')
        main()
        manager_instance.load_grants.assert_called_once()
        
        # Test help/no command
        manager_instance.load_grants.reset_mock()
        
        args = setup_args(None)
        main()
        mock_parser.return_value.print_help.assert_called_once()
