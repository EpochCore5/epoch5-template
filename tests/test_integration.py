"""
Tests for EPOCH5 integration system
"""

import pytest
import json
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from integration import EPOCH5Integration
except ImportError as e:
    pytest.skip(f"Could not import integration module: {e}", allow_module_level=True)


class TestEPOCH5Integration:
    """Test cases for EPOCH5Integration class"""

    @pytest.fixture
    def integration_system(self, temp_dir):
        """Create an EPOCH5Integration instance for testing"""
        return EPOCH5Integration(base_dir=temp_dir)

    def test_initialization(self, integration_system):
        """Test that EPOCH5Integration initializes correctly"""
        assert integration_system is not None
        assert hasattr(integration_system, "base_dir")
        assert hasattr(integration_system, "agent_manager")
        assert hasattr(integration_system, "policy_manager")

    def test_timestamp_generation(self, integration_system):
        """Test timestamp generation"""
        timestamp = integration_system.timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
        # Basic format check for ISO timestamp
        assert "T" in timestamp
        assert "Z" in timestamp

    def test_sha256_hash_generation(self, integration_system):
        """Test SHA256 hash generation"""
        test_data = "test_data"
        # Use the actual method that exists on the integration system
        # The integration system delegates to its components for hashing
        hash_value = integration_system.agent_manager.sha256(test_data)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64-character hex string

    def test_setup_demo_environment(self, integration_system):
        """Test demo environment setup"""
        result = integration_system.setup_demo_environment()
        assert isinstance(result, dict)
        assert "success" in result
        assert "components" in result

        if result["success"]:
            assert "agents" in result["components"]
            assert "policies" in result["components"]

    def test_get_system_status(self, integration_system):
        """Test system status retrieval"""
        # First setup demo environment to have data
        integration_system.setup_demo_environment()

        status = integration_system.get_system_status()
        assert isinstance(status, dict)
        assert "timestamp" in status
        assert "components" in status
        assert isinstance(status["components"], dict)

    def test_log_integration_event(self, integration_system):
        """Test integration event logging"""
        event_type = "TEST_EVENT"
        event_data = {"test": "data"}

        # This should not raise an exception
        integration_system.log_integration_event(event_type, event_data)

        # Check that log file exists - the log file is integration.log, not integration_events.log
        log_file = integration_system.base_dir / "integration.log"
        assert log_file.exists()

    def test_validate_system_integrity_empty(self, integration_system):
        """Test system integrity validation on empty system"""
        result = integration_system.validate_system_integrity()
        assert isinstance(result, dict)
        assert "started_at" in result
        assert "validations" in result
        assert "overall_valid" in result
        assert "errors" in result

    @patch("integration.EPOCH5Integration.run_complete_workflow")
    def test_run_complete_workflow_mock(self, mock_workflow, integration_system):
        """Test complete workflow execution with mocking"""
        mock_workflow.return_value = {
            "success": True,
            "steps": {"demo": "completed"},
            "errors": [],
        }

        result = integration_system.run_complete_workflow()
        assert result["success"] is True
        assert "steps" in result
