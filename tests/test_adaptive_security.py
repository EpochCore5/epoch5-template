#!/usr/bin/env python3
"""
Tests for EPOCH5 Adaptive Security Learning System
"""

import pytest
import json
import sys
import os
import tempfile
import time
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from adaptive_security import (
        AdaptiveSecurityEngine, 
        SecurityViolation, 
        ResponseAction
    )
except ImportError as e:
    pytest.skip(f"Could not import adaptive_security module: {e}", allow_module_level=True)


class TestSecurityViolation:
    """Test cases for SecurityViolation class"""
    
    def test_initialization(self):
        """Test that SecurityViolation initializes correctly"""
        violation = SecurityViolation(
            violation_type="brute_force",
            severity="high",
            timestamp="2023-08-01T12:30:00Z",
            details={"ip_address": "192.168.1.100", "attempts": 50},
            source="api_gateway"
        )
        
        assert violation.violation_type == "brute_force"
        assert violation.severity == "high"
        assert violation.timestamp == "2023-08-01T12:30:00Z"
        assert violation.details == {"ip_address": "192.168.1.100", "attempts": 50}
        assert violation.source == "api_gateway"
        assert violation.response_actions == []
        assert violation.outcome is None
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        violation = SecurityViolation(
            violation_type="api_abuse",
            severity="medium",
            timestamp="2023-08-01T12:30:00Z",
            details={"endpoint": "/api/v1/users", "rate": 500},
            source="api_gateway"
        )
        
        violation_dict = violation.to_dict()
        assert violation_dict["violation_type"] == "api_abuse"
        assert violation_dict["severity"] == "medium"
        assert violation_dict["timestamp"] == "2023-08-01T12:30:00Z"
        assert violation_dict["details"] == {"endpoint": "/api/v1/users", "rate": 500}
        assert violation_dict["source"] == "api_gateway"
        assert violation_dict["response_actions"] == []
        assert violation_dict["outcome"] is None
    
    def test_add_response(self):
        """Test adding response actions"""
        violation = SecurityViolation(
            violation_type="data_exfiltration",
            severity="critical",
            timestamp="2023-08-01T12:30:00Z",
            details={"data_type": "user_data", "volume_mb": 250},
            source="data_access"
        )
        
        result = {"status": "success", "message": "Blocked connection"}
        violation.add_response("block_ip", result)
        
        assert len(violation.response_actions) == 1
        assert violation.response_actions[0]["action"] == "block_ip"
        assert violation.response_actions[0]["result"] == result
        assert "timestamp" in violation.response_actions[0]
    
    def test_set_outcome(self):
        """Test setting outcome"""
        violation = SecurityViolation(
            violation_type="ceiling_violation",
            severity="high",
            timestamp="2023-08-01T12:30:00Z",
            details={"ceiling_type": "rate_limit", "attempted_value": 800},
            source="ceiling_manager"
        )
        
        violation.set_outcome(
            outcome="mitigated",
            effectiveness=0.85,
            details={"action_taken": "reduce_ceiling"}
        )
        
        assert violation.outcome["status"] == "mitigated"
        assert violation.outcome["effectiveness"] == 0.85
        assert violation.outcome["details"] == {"action_taken": "reduce_ceiling"}
        assert "timestamp" in violation.outcome


class TestResponseAction:
    """Test cases for ResponseAction class"""
    
    def test_initialization(self):
        """Test that ResponseAction initializes correctly"""
        action = ResponseAction(
            name="block_ip",
            action_type="block",
            description="Block offending IP address",
            effectiveness={"brute_force": 0.9, "api_abuse": 0.7},
            impact=0.8
        )
        
        assert action.name == "block_ip"
        assert action.action_type == "block"
        assert action.description == "Block offending IP address"
        assert action.effectiveness == {"brute_force": 0.9, "api_abuse": 0.7}
        assert action.impact == 0.8
        assert action.usage_count == 0
        assert action.success_count == 0
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        action = ResponseAction(
            name="rate_limit",
            action_type="throttle",
            description="Apply rate limiting",
            effectiveness={"api_abuse": 0.9},
            impact=0.5
        )
        
        action_dict = action.to_dict()
        assert action_dict["name"] == "rate_limit"
        assert action_dict["action_type"] == "throttle"
        assert action_dict["description"] == "Apply rate limiting"
        assert action_dict["effectiveness"] == {"api_abuse": 0.9}
        assert action_dict["impact"] == 0.5
        assert action_dict["usage_count"] == 0
        assert action_dict["success_count"] == 0
        assert action_dict["success_rate"] == 0.0
    
    def test_success_rate(self):
        """Test success rate calculation"""
        action = ResponseAction(
            name="encrypt_data",
            action_type="protection",
            description="Encrypt data",
            effectiveness={"data_exfiltration": 0.8},
            impact=0.3
        )
        
        # No uses yet
        assert action.success_rate == 0.0
        
        # Update counts
        action.usage_count = 10
        action.success_count = 7
        
        assert action.success_rate == 0.7


class TestAdaptiveSecurityEngine:
    """Test cases for AdaptiveSecurityEngine class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests"""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname
    
    @pytest.fixture
    def engine(self, temp_dir):
        """Create an AdaptiveSecurityEngine instance for testing"""
        return AdaptiveSecurityEngine(base_dir=temp_dir)
    
    def test_initialization(self, engine, temp_dir):
        """Test that AdaptiveSecurityEngine initializes correctly"""
        assert engine.base_dir == Path(temp_dir)
        assert engine.security_dir == Path(temp_dir) / "adaptive_security"
        assert engine.violations_file == engine.security_dir / "violations_history.json"
        assert engine.actions_file == engine.security_dir / "response_actions.json"
        assert engine.learning_file == engine.security_dir / "learning_model.json"
        assert engine.config_file == engine.security_dir / "adaptive_config.json"
        assert engine.available_actions is not None
        assert engine.is_monitoring is False
        assert engine.is_learning is False
    
    def test_timestamp(self, engine):
        """Test timestamp generation"""
        timestamp = engine.timestamp()
        assert isinstance(timestamp, str)
        assert len(timestamp) > 0
    
    def test_sha256(self, engine):
        """Test SHA256 hash generation"""
        data = "Test data for hashing"
        hash_value = engine.sha256(data)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 produces 64 character hex string
    
    def test_initialize_config(self, engine):
        """Test configuration initialization"""
        # Config should have been initialized in the fixture
        assert engine.config is not None
        assert "monitoring_interval" in engine.config
        assert "learning_interval" in engine.config
        assert "auto_response" in engine.config
        assert "learning_parameters" in engine.config
        assert "response_thresholds" in engine.config
        assert "pattern_detection" in engine.config
    
    def test_load_or_init_actions(self, engine):
        """Test loading or initializing response actions"""
        actions = engine.available_actions
        assert isinstance(actions, dict)
        assert len(actions) > 0
        
        # Check for expected default actions
        expected_actions = ["block_ip", "rate_limit", "step_up_auth", "alert_admin", 
                          "encrypt_data", "reduce_ceiling", "terminate_session", "log_forensics"]
        
        for action_name in expected_actions:
            assert action_name in actions
            assert isinstance(actions[action_name], ResponseAction)
    
    def test_save_actions(self, engine):
        """Test saving response actions"""
        with patch("builtins.open", mock_open()) as mock_file:
            engine._save_actions(engine.available_actions)
            mock_file.assert_called_once_with(engine.actions_file, "w")
    
    def test_save_violations_history(self, engine):
        """Test saving violations history"""
        # Create a test violation
        violation = SecurityViolation(
            violation_type="brute_force",
            severity="high",
            timestamp=engine.timestamp(),
            details={"ip_address": "192.168.1.100"},
            source="api_gateway"
        )
        
        # Add to history
        engine.violations_history.append(violation)
        
        with patch("builtins.open", mock_open()) as mock_file:
            engine._save_violations_history()
            mock_file.assert_called_once_with(engine.violations_file, "w")
    
    def test_save_learning_state(self, engine):
        """Test saving learning state"""
        with patch("builtins.open", mock_open()) as mock_file:
            engine._save_learning_state()
            mock_file.assert_called_once_with(engine.learning_file, "w")
    
    def test_get_state_key(self, engine):
        """Test creation of state key for Q-learning"""
        violation = SecurityViolation(
            violation_type="api_abuse",
            severity="medium",
            timestamp=engine.timestamp(),
            details={},
            source="api_gateway"
        )
        
        state_key = engine._get_state_key(violation)
        assert state_key == "api_abuse:medium:api_gateway"
    
    def test_select_response_action(self, engine):
        """Test selecting the best response action"""
        violation = SecurityViolation(
            violation_type="brute_force",
            severity="high",
            timestamp=engine.timestamp(),
            details={},
            source="user_auth"
        )
        
        # Force exploitation (no exploration)
        with patch.dict(engine.config["learning_parameters"], {"exploration_rate": 0}):
            action = engine._select_response_action(violation)
            assert isinstance(action, str)
            assert action in engine.available_actions
    
    def test_update_action_reward(self, engine):
        """Test updating Q-value for state-action pair"""
        state_key = "brute_force:high:user_auth"
        action = "block_ip"
        reward = 0.8
        
        # Initial update
        engine._update_action_reward(state_key, action, reward)
        
        assert state_key in engine.state_action_rewards
        assert action in engine.state_action_rewards[state_key]
        
        initial_value = engine.state_action_rewards[state_key][action]
        
        # Second update
        engine._update_action_reward(state_key, action, 0.9)
        
        # Value should have changed
        assert engine.state_action_rewards[state_key][action] != initial_value
    
    def test_execute_response(self, engine):
        """Test executing a response action"""
        violation = SecurityViolation(
            violation_type="api_abuse",
            severity="medium",
            timestamp=engine.timestamp(),
            details={},
            source="api_gateway"
        )
        
        action_name = "rate_limit"
        initial_count = engine.available_actions[action_name].usage_count
        
        result = engine._execute_response(violation, action_name)
        
        assert "status" in result
        assert result["status"] in ["success", "failure"]
        assert "message" in result
        assert "details" in result
        
        # Usage count should be incremented
        assert engine.available_actions[action_name].usage_count == initial_count + 1
    
    def test_process_violation(self, engine):
        """Test processing a security violation"""
        violation = SecurityViolation(
            violation_type="data_exfiltration",
            severity="critical",
            timestamp=engine.timestamp(),
            details={"data_type": "credentials", "volume_mb": 50},
            source="data_access"
        )
        
        initial_count = engine.stats["violations_detected"]
        
        # Process with auto-response disabled
        with patch.dict(engine.config, {"auto_response": False}):
            result = engine.process_violation(violation)
            
            assert result is violation
            assert engine.stats["violations_detected"] == initial_count + 1
            assert not violation.response_actions
        
        # Process with auto-response enabled
        with patch.dict(engine.config, {"auto_response": True}), \
             patch.object(engine, "_select_response_action", return_value="encrypt_data"), \
             patch.object(engine, "_execute_response", return_value={"status": "success", "message": "Encrypted data"}), \
             patch.object(engine, "_save_violations_history"), \
             patch.object(engine, "_save_learning_state"):
            
            result = engine.process_violation(violation)
            
            assert result is violation
            assert len(violation.response_actions) == 1
            assert violation.response_actions[0]["action"] == "encrypt_data"
            assert violation.outcome is not None
    
    def test_calculate_reward(self, engine):
        """Test calculating reward for reinforcement learning"""
        violation = SecurityViolation(
            violation_type="ceiling_violation",
            severity="high",
            timestamp=engine.timestamp(),
            details={},
            source="ceiling_manager"
        )
        
        action_name = "reduce_ceiling"
        effectiveness = 0.9
        outcome = "mitigated"
        
        reward = engine._calculate_reward(violation, action_name, effectiveness, outcome)
        
        assert -1.0 <= reward <= 1.0
        
        # Test false positive penalty
        reward_fp = engine._calculate_reward(violation, action_name, effectiveness, "false_positive")
        assert reward_fp == -1.0
    
    def test_simulate_violation(self, engine):
        """Test simulating a security violation"""
        violation = engine._simulate_violation()
        
        assert isinstance(violation, SecurityViolation)
        assert violation.violation_type in ["brute_force", "api_abuse", "data_exfiltration", "ceiling_violation"]
        assert violation.severity in ["low", "medium", "high", "critical"]
        assert isinstance(violation.details, dict)
    
    def test_simulate_specific_violation(self, engine):
        """Test simulating a specific security violation"""
        violation_type = "api_abuse"
        source = "api_gateway"
        
        violation = engine._simulate_specific_violation(violation_type, source)
        
        assert isinstance(violation, SecurityViolation)
        assert violation.violation_type == violation_type
        assert violation.source == source
        assert isinstance(violation.details, dict)
    
    def test_start_stop_monitoring(self, engine):
        """Test starting and stopping monitoring"""
        # Since the actual monitoring happens in threads, we need to directly test
        # the status setting and response behavior
        
        # Directly set monitoring flag for testing
        engine.is_monitoring = True
        engine.monitor_thread = MagicMock()
        engine.is_learning = True
        engine.learning_thread = MagicMock()
        
        # Test stop_monitoring when it's running
        result = engine.stop_monitoring()
        assert result["status"] == "stopped"
        assert engine.is_monitoring is False
        assert engine.is_learning is False
        
        # Test start_monitoring 
        with patch("threading.Thread") as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            
            # Reset flags since we manually set them
            engine.is_monitoring = False
            engine.is_learning = False
            
            result = engine.start_monitoring()
            assert result["status"] == "started"
            assert mock_thread.call_count >= 1
            assert mock_thread_instance.start.call_count >= 1
            
        # Test stop_monitoring when it's not running
        engine.is_monitoring = False
        result = engine.stop_monitoring()
        assert result["status"] == "not_running"
    
    def test_get_effectiveness_report(self, engine):
        """Test generating effectiveness report"""
        # Add some test data
        engine.stats["violations_detected"] = 50
        engine.stats["successful_mitigations"] = 35
        engine.stats["failed_mitigations"] = 10
        engine.stats["false_positives"] = 5
        engine.stats["model_accuracy"] = 0.8
        
        # Add a pattern
        engine.violation_patterns["brute_force:api_gateway:5"] = {
            "count": 3,
            "first_seen": engine.timestamp(),
            "last_seen": engine.timestamp()
        }
        
        report = engine.get_effectiveness_report()
        
        assert "timestamp" in report
        assert "actions_effectiveness" in report
        assert "performance_metrics" in report
        assert "pattern_insights" in report
        assert "learning_progress" in report
        
        metrics = report["performance_metrics"]
        assert metrics["violations_detected"] == 50
        assert metrics["successful_mitigations"] == 35
        assert metrics["failed_mitigations"] == 10
        assert metrics["false_positives"] == 5
        assert metrics["accuracy"] == 0.8
    
    def test_get_recommendation_for_pattern(self, engine):
        """Test getting recommendation for a pattern"""
        pattern_key = "brute_force:api_gateway:5"
        
        # No learned recommendations yet
        recommendation = engine._get_recommendation_for_pattern(pattern_key)
        assert isinstance(recommendation, str)
        assert len(recommendation) > 0
        
        # Add a learned recommendation
        state_key = "brute_force:high:api_gateway"
        engine.state_action_rewards[state_key] = {"block_ip": 0.9, "rate_limit": 0.7}
        
        recommendation = engine._get_recommendation_for_pattern(pattern_key)
        assert "block_ip" in recommendation
    
    def test_update_violation_patterns(self, engine):
        """Test updating violation patterns"""
        # Add some violations to history
        for i in range(5):
            violation = SecurityViolation(
                violation_type="brute_force",
                severity="high",
                timestamp=engine.timestamp(),  # Current time
                details={"ip_address": f"192.168.1.{i+1}"},
                source="api_gateway"
            )
            engine.violations_history.append(violation)
        
        # Set a very large time window to include all violations
        with patch.dict(engine.config["pattern_detection"], {"time_window": 86400, "min_occurrences": 3}):
            engine._update_violation_patterns()
            
            # Should have detected at least one pattern
            assert len(engine.violation_patterns) > 0
    
    def test_update_action_effectiveness(self, engine):
        """Test updating action effectiveness based on outcomes"""
        # Create a violation with response and outcome
        violation = SecurityViolation(
            violation_type="api_abuse",
            severity="medium",
            timestamp=engine.timestamp(),
            details={},
            source="api_gateway"
        )
        
        # Add response and outcome
        violation.add_response("rate_limit", {"status": "success", "message": "Applied rate limit"})
        violation.set_outcome("mitigated", 0.8, {})
        
        # Add to history
        engine.violations_history.append(violation)
        
        # Initial effectiveness
        initial_effectiveness = engine.available_actions["rate_limit"].effectiveness.get("api_abuse", 0)
        
        # Update effectiveness
        with patch.object(engine, "_save_actions"):
            engine._update_action_effectiveness()
            
            # Check if effectiveness was updated in action_effectiveness dict
            key = "rate_limit:api_abuse"
            assert key in engine.action_effectiveness
            
            # Check if effectiveness was updated in the action itself
            new_effectiveness = engine.available_actions["rate_limit"].effectiveness.get("api_abuse", 0)
            assert new_effectiveness != initial_effectiveness
    
    def test_run_training_simulations(self, engine):
        """Test running training simulations"""
        # Mock necessary methods to isolate the test
        with patch.object(engine, "_simulate_violation") as mock_simulate, \
             patch.object(engine, "_execute_response") as mock_execute, \
             patch.object(engine, "_calculate_reward") as mock_calculate, \
             patch.object(engine, "_update_action_reward") as mock_update:
            
            # Configure mocks
            mock_simulate.return_value = SecurityViolation(
                violation_type="brute_force",
                severity="high",
                timestamp=engine.timestamp(),
                details={},
                source="user_auth"
            )
            mock_execute.return_value = {"status": "success", "message": "Test"}
            mock_calculate.return_value = 0.8
            
            # Run simulations
            engine._run_training_simulations()
            
            # Check if methods were called
            assert mock_simulate.call_count > 0
            assert mock_execute.call_count > 0
            assert mock_calculate.call_count > 0
            assert mock_update.call_count > 0
            
            # Check if model accuracy was updated
            assert "model_accuracy" in engine.stats

    def test_main_function(self):
        """Test the main CLI function"""
        with patch("argparse.ArgumentParser.parse_args") as mock_args, \
             patch("adaptive_security.AdaptiveSecurityEngine") as MockEngine, \
             patch("builtins.print"):
            
            # Mock engine instance
            mock_instance = MagicMock()
            MockEngine.return_value = mock_instance
            mock_instance.start_monitoring.return_value = {
                "status": "started", 
                "timestamp": "2023-08-01T12:30:00Z"
            }
            
            # Test start command
            mock_args.return_value.command = "start"
            
            from adaptive_security import main
            main()
            
            # Verify the method was called
            mock_instance.start_monitoring.assert_called_once()
            
            # Test report command
            mock_args.return_value.command = "report"
            mock_instance.get_effectiveness_report.return_value = {
                "timestamp": "2023-08-01T12:30:00Z",
                "performance_metrics": {
                    "violations_detected": 50,
                    "successful_mitigations": 35,
                    "failed_mitigations": 10,
                    "false_positives": 5,
                    "mitigation_rate": 70.0,
                    "accuracy": 0.8,
                    "training_cycles": 10
                },
                "actions_effectiveness": {},
                "pattern_insights": [],
                "learning_progress": {
                    "state_action_pairs": 20,
                    "unique_patterns": 5,
                    "last_updated": "2023-08-01T12:30:00Z"
                }
            }
            
            main()
            mock_instance.get_effectiveness_report.assert_called_once()
