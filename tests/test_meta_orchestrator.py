"""
Tests for meta orchestrator functionality
"""

import pytest
import json
import sys
import os
import time
import threading
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from meta_orchestrator import MetaOrchestrator, DecisionEngine, OrchestratorAction
except ImportError as e:
    pytest.skip(
        f"Could not import meta_orchestrator module: {e}", allow_module_level=True
    )


class TestDecisionEngine:
    """Test cases for DecisionEngine class"""
    
    def test_initialization(self):
        """Test that DecisionEngine initializes correctly"""
        engine = DecisionEngine()
        
        assert engine.decision_history == []
        assert isinstance(engine.decision_outcomes, dict)
    
    def test_evaluate_decision(self):
        """Test decision evaluation"""
        engine = DecisionEngine()
        
        # Create a simple context for decision making
        context = {
            "system_state": {
                "load": 0.7,
                "error_rate": 0.05,
                "available_agents": 5
            },
            "priority": "performance"
        }
        
        decisions = [
            {"action": "scale_up", "confidence": 0.8},
            {"action": "optimize", "confidence": 0.6},
            {"action": "no_action", "confidence": 0.3}
        ]
        
        # Test with performance priority
        result = engine.evaluate_decision(decisions, context)
        assert result is not None
        assert "action" in result
        assert result["action"] == "scale_up"  # Highest confidence
        
        # Test with different priority
        context["priority"] = "stability"
        with patch.object(engine, '_apply_decision_rules', return_value={"action": "optimize", "confidence": 0.9}):
            result = engine.evaluate_decision(decisions, context)
            assert result["action"] == "optimize"
    
    def test_record_decision(self):
        """Test recording decision history"""
        engine = DecisionEngine()
        
        decision = {"action": "scale_up", "confidence": 0.8}
        context = {"system_state": {"load": 0.7}}
        
        engine.record_decision(decision, context)
        
        assert len(engine.decision_history) == 1
        assert engine.decision_history[0]["decision"] == decision
        assert engine.decision_history[0]["context"] == context
        assert "timestamp" in engine.decision_history[0]
    
    def test_record_outcome(self):
        """Test recording decision outcomes"""
        engine = DecisionEngine()
        
        # Test success outcome
        engine.record_outcome("scale_up", {"status": "success", "details": "Scaled successfully"})
        assert "scale_up" in engine.decision_outcomes
        assert engine.decision_outcomes["scale_up"]["successes"] == 1
        assert engine.decision_outcomes["scale_up"]["failures"] == 0
        
        # Test failure outcome
        engine.record_outcome("scale_up", {"status": "failure", "details": "Failed to scale"})
        assert engine.decision_outcomes["scale_up"]["successes"] == 1
        assert engine.decision_outcomes["scale_up"]["failures"] == 1
        
        # Test another action
        engine.record_outcome("optimize", {"status": "success"})
        assert "optimize" in engine.decision_outcomes
        assert engine.decision_outcomes["optimize"]["successes"] == 1
    
    def test_learn_from_history(self):
        """Test learning from history"""
        engine = DecisionEngine()
        
        # Record some outcomes
        engine.record_outcome("action1", {"status": "success"})
        engine.record_outcome("action1", {"status": "success"})
        engine.record_outcome("action1", {"status": "failure"})
        engine.record_outcome("action2", {"status": "failure"})
        
        # Should not raise exceptions
        engine.learn_from_history()
        
        # Verify the stats are correct
        assert engine.decision_outcomes["action1"]["total"] == 3
        assert engine.decision_outcomes["action1"]["successes"] == 2
        assert engine.decision_outcomes["action2"]["total"] == 1
        assert engine.decision_outcomes["action2"]["failures"] == 1


class TestOrchestratorAction:
    """Test cases for OrchestratorAction class"""
    
    def test_initialization(self):
        """Test that OrchestratorAction initializes correctly"""
        action = OrchestratorAction(
            action_type="test",
            target="test_subsystem",
            parameters={"param1": "value1"}
        )
        
        assert action.action_type == "test"
        assert action.target == "test_subsystem"
        assert action.parameters == {"param1": "value1"}
        assert action.action_id is not None
        assert action.status == "pending"
        assert action.created_at is not None
        assert action.result is None
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        action = OrchestratorAction(
            action_type="test",
            target="test_subsystem",
            parameters={"param1": "value1"}
        )
        
        action_dict = action.to_dict()
        
        assert isinstance(action_dict, dict)
        assert action_dict["action_type"] == "test"
        assert action_dict["target"] == "test_subsystem"
        assert action_dict["parameters"] == {"param1": "value1"}
        assert action_dict["action_id"] == action.action_id
        assert action_dict["status"] == "pending"
        assert action_dict["created_at"] == action.created_at
    
    def test_from_dict(self):
        """Test creation from dictionary"""
        action_dict = {
            "action_type": "test",
            "target": "test_subsystem",
            "parameters": {"param1": "value1"},
            "action_id": "test_id_123",
            "status": "completed",
            "created_at": "2025-01-01T00:00:00",
            "result": {"success": True}
        }
        
        action = OrchestratorAction.from_dict(action_dict)
        
        assert action.action_type == "test"
        assert action.target == "test_subsystem"
        assert action.parameters == {"param1": "value1"}
        assert action.action_id == "test_id_123"
        assert action.status == "completed"
        assert action.created_at == "2025-01-01T00:00:00"
        assert action.result == {"success": True}
    
    def test_update_status(self):
        """Test updating status"""
        action = OrchestratorAction(
            action_type="test",
            target="test_subsystem"
        )
        
        action.update_status("in_progress")
        assert action.status == "in_progress"
        
        action.update_status("completed", {"success": True})
        assert action.status == "completed"
        assert action.result == {"success": True}


class TestMetaOrchestrator:
    """Test cases for MetaOrchestrator class"""
    
    @pytest.fixture
    def meta_orchestrator(self, tmp_path):
        """Create a MetaOrchestrator instance for testing"""
        with patch('meta_orchestrator.DecisionEngine'), \
             patch('json.load', return_value={}), \
             patch('pathlib.Path.open', mock_open()):
            orchestrator = MetaOrchestrator(base_dir=str(tmp_path))
            yield orchestrator
    
    def test_initialization(self, meta_orchestrator):
        """Test that MetaOrchestrator initializes correctly"""
        assert meta_orchestrator is not None
        assert isinstance(meta_orchestrator.base_dir, Path)
        assert meta_orchestrator.orchestration_dir.exists()
        assert meta_orchestrator.is_orchestrating is False
        assert meta_orchestrator.orchestration_thread is None
        assert isinstance(meta_orchestrator.subsystems, dict)
        assert isinstance(meta_orchestrator.metrics, dict)
    
    def test_initialize_config(self, meta_orchestrator):
        """Test config initialization"""
        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            
            meta_orchestrator._initialize_config()
            
            # Should create default config if it doesn't exist
            mock_file.assert_called_once()
            mock_json_dump.assert_called_once()
    
    def test_initialize_subsystems(self, meta_orchestrator):
        """Test subsystem initialization"""
        with patch('pathlib.Path.exists', return_value=False), \
             patch('pathlib.Path.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            
            subsystems = meta_orchestrator._initialize_subsystems()
            
            # Should create empty subsystems if file doesn't exist
            assert isinstance(subsystems, dict)
            mock_file.assert_called_once()
            mock_json_dump.assert_called_once()
    
    def test_register_subsystem(self, meta_orchestrator):
        """Test registering a subsystem"""
        with patch.object(meta_orchestrator, '_save_subsystems') as mock_save:
            result = meta_orchestrator.register_subsystem(
                name="test_system",
                endpoint="http://localhost:8080",
                capabilities=["test1", "test2"],
                metadata={"version": "1.0"}
            )
            
            assert result is True
            assert "test_system" in meta_orchestrator.subsystems
            assert meta_orchestrator.subsystems["test_system"]["endpoint"] == "http://localhost:8080"
            assert "test1" in meta_orchestrator.subsystems["test_system"]["capabilities"]
            assert meta_orchestrator.subsystems["test_system"]["metadata"]["version"] == "1.0"
            assert "registered_at" in meta_orchestrator.subsystems["test_system"]
            mock_save.assert_called_once()
    
    def test_unregister_subsystem(self, meta_orchestrator):
        """Test unregistering a subsystem"""
        # First register a subsystem
        meta_orchestrator.subsystems["test_system"] = {
            "endpoint": "http://localhost:8080",
            "capabilities": ["test1", "test2"],
            "status": "active"
        }
        
        with patch.object(meta_orchestrator, '_save_subsystems') as mock_save:
            result = meta_orchestrator.unregister_subsystem("test_system")
            
            assert result is True
            assert "test_system" not in meta_orchestrator.subsystems
            mock_save.assert_called_once()
    
    def test_get_subsystem(self, meta_orchestrator):
        """Test getting a subsystem"""
        # Register a subsystem
        meta_orchestrator.subsystems["test_system"] = {
            "endpoint": "http://localhost:8080",
            "capabilities": ["test1", "test2"],
            "status": "active"
        }
        
        # Get it
        subsystem = meta_orchestrator.get_subsystem("test_system")
        assert subsystem is not None
        assert subsystem["endpoint"] == "http://localhost:8080"
        
        # Test nonexistent subsystem
        assert meta_orchestrator.get_subsystem("nonexistent") is None
    
    def test_create_action(self, meta_orchestrator):
        """Test creating an action"""
        action = meta_orchestrator.create_action(
            action_type="test",
            target="test_system",
            parameters={"param1": "value1"}
        )
        
        assert action is not None
        assert action.action_type == "test"
        assert action.target == "test_system"
        assert action.parameters == {"param1": "value1"}
        assert action.status == "pending"
    
    def test_execute_action(self, meta_orchestrator):
        """Test executing an action"""
        # Register a test subsystem
        meta_orchestrator.subsystems["test_system"] = {
            "endpoint": "http://localhost:8080",
            "capabilities": ["test_action"],
            "status": "active"
        }
        
        # Create a test action
        action = OrchestratorAction(
            action_type="test_action",
            target="test_system"
        )
        
        # Mock the request
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}
            mock_post.return_value = mock_response
            
            result = meta_orchestrator._execute_action(action)
            
            assert result is True
            assert action.status == "completed"
            assert action.result["status"] == "success"
            mock_post.assert_called_once()
    
    def test_execute_action_failure(self, meta_orchestrator):
        """Test executing an action with failure"""
        # Register a test subsystem
        meta_orchestrator.subsystems["test_system"] = {
            "endpoint": "http://localhost:8080",
            "capabilities": ["test_action"],
            "status": "active"
        }
        
        # Create a test action
        action = OrchestratorAction(
            action_type="test_action",
            target="test_system"
        )
        
        # Mock request exception
        with patch('requests.post', side_effect=Exception("Test error")):
            result = meta_orchestrator._execute_action(action)
            
            assert result is False
            assert action.status == "failed"
            assert "error" in action.result
    
    def test_start_orchestration(self, meta_orchestrator):
        """Test starting orchestration"""
        with patch.object(meta_orchestrator, '_orchestration_loop') as mock_loop, \
             patch('threading.Thread') as mock_thread:
            
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            
            result = meta_orchestrator.start_orchestration()
            
            assert result is True
            assert meta_orchestrator.is_orchestrating is True
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
    
    def test_stop_orchestration(self, meta_orchestrator):
        """Test stopping orchestration"""
        # Setup orchestration state
        meta_orchestrator.is_orchestrating = True
        meta_orchestrator.orchestration_thread = MagicMock()
        
        result = meta_orchestrator.stop_orchestration()
        
        assert result is True
        assert meta_orchestrator.is_orchestrating is False
    
    def test_get_orchestration_state(self, meta_orchestrator):
        """Test getting orchestration state"""
        meta_orchestrator.is_orchestrating = True
        meta_orchestrator.metrics = {"decisions_made": 10}
        
        state = meta_orchestrator.get_orchestration_state()
        
        assert state["is_orchestrating"] is True
        assert state["metrics"]["decisions_made"] == 10
        assert "subsystems_count" in state
        assert "actions_count" in state
    
    def test_save_and_load_state(self, meta_orchestrator):
        """Test saving and loading state"""
        # Set some state
        meta_orchestrator.metrics = {"decisions_made": 10}
        
        with patch('pathlib.Path.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump, \
             patch('json.load', return_value={"metrics": {"decisions_made": 15}}):
            
            # Save state
            meta_orchestrator._save_state()
            mock_file.assert_called()
            mock_json_dump.assert_called_once()
            
            # Load state
            meta_orchestrator._load_state()
            assert meta_orchestrator.metrics["decisions_made"] == 15


def test_main_function():
    """Test the main CLI function"""
    
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('meta_orchestrator.MetaOrchestrator') as MockOrchestrator:
        
        # Setup mock orchestrator
        mock_instance = MockOrchestrator.return_value
        
        # Test start command
        mock_args.return_value.command = "start"
        mock_args.return_value.base_dir = "./test_dir"
        mock_instance.start_orchestration.return_value = True
        
        with patch('builtins.print') as mock_print:
            from meta_orchestrator import main
            main()
            
            MockOrchestrator.assert_called_with(base_dir="./test_dir")
            mock_instance.start_orchestration.assert_called_once()
            mock_print.assert_called()
        
        # Test status command
        mock_args.return_value.command = "status"
        mock_instance.get_orchestration_state.return_value = {
            "is_orchestrating": True,
            "metrics": {"decisions_made": 10}
        }
        
        with patch('builtins.print') as mock_print, \
             patch('json.dumps') as mock_json_dumps:
            main()
            
            mock_instance.get_orchestration_state.assert_called_once()
            mock_print.assert_called()
            mock_json_dumps.assert_called_once()
