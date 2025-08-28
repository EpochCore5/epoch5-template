"""
Extended test suite for StrategyDECKAgent
Focusing on ceiling and security integration
"""
import os
import time
import pytest
import logging
import sys
import json
from typing import Dict, Any
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta

# Mock the ceiling_manager and epoch_audit imports
sys.modules['ceiling_manager'] = MagicMock()
sys.modules['epoch_audit'] = MagicMock()

# Set the global flag before importing
import strategydeck_agent
strategydeck_agent.CEILING_SYSTEM_AVAILABLE = True

from strategydeck_agent import StrategyDECKAgent


@pytest.fixture
def agent():
    """Create a test agent instance with mocked ceiling and audit"""
    with patch('strategydeck_agent.CeilingManager') as mock_ceiling_manager, \
         patch('strategydeck_agent.EpochAudit') as mock_audit, \
         patch('strategydeck_agent.ServiceTier') as mock_service_tier:
        
        # Configure mock ceiling manager
        mock_cm_instance = mock_ceiling_manager.return_value
        mock_cm_instance.load_ceilings.return_value = {
            "configurations": {
                "agent_testagent": {
                    "service_tier": "professional",
                    "performance_score": 0.85,
                    "last_adjustment": "2025-08-28T09:00:00Z"
                }
            }
        }
        
        # Configure mock audit system
        mock_audit_instance = mock_audit.return_value
        
        # Service tier enum mock
        mock_service_tier.return_value = "professional"
        
        agent = StrategyDECKAgent(
            name="TestAgent", 
            log_level=logging.ERROR,
            service_tier="professional",
            config_id="agent_testagent"
        )
        
        # Set start time for predictable uptime
        agent.start_time = datetime.now() - timedelta(hours=1)
        
        yield agent


def test_get_ceiling_status(agent):
    """Test getting ceiling status information"""
    # Set up ceiling manager mock responses
    agent.ceiling_manager.load_ceilings.return_value = {
        "configurations": {
            "agent_testagent": {
                "service_tier": "professional",
                "performance_score": 0.85,
                "last_adjustment": "2025-08-28T09:00:00Z"
            }
        }
    }
    
    # Mock get_effective_ceiling
    agent.ceiling_manager.get_effective_ceiling.return_value = 100
    
    # Mock get_upgrade_recommendations
    agent.ceiling_manager.get_upgrade_recommendations.return_value = {
        "should_upgrade": True,
        "recommended_tier": "enterprise",
        "estimated_roi": 2.5
    }
    
    # Get ceiling status
    status = agent.get_ceiling_status()
    
    # Check status structure
    assert status["config_id"] == "agent_testagent"
    assert status["service_tier"] == "professional"
    assert status["performance_score"] == 0.85
    assert status["upgrade_recommended"] == True
    assert status["recommended_tier"] == "enterprise"


def test_get_ceiling_status_error(agent):
    """Test error handling in ceiling status"""
    # Make load_ceilings throw an exception
    agent.ceiling_manager.load_ceilings.side_effect = Exception("Mock error")
    
    # Get ceiling status
    status = agent.get_ceiling_status()
    
    # Should return error
    assert "error" in status
    assert "Failed to get ceiling status" in status["error"]


def test_get_ceiling_status_no_config(agent):
    """Test ceiling status when config is missing"""
    # Return empty configurations
    agent.ceiling_manager.load_ceilings.return_value = {
        "configurations": {}
    }
    
    # Get ceiling status
    status = agent.get_ceiling_status()
    
    # Should indicate no config found
    assert "error" in status
    assert "No ceiling configuration found" in status["error"]


def test_verify_security_success(agent):
    """Test security verification success case"""
    # Configure mock audit system response
    agent.audit_system.verify_seals.return_value = {
        "status": "PASSED",
        "verified_count": 10,
        "valid_count": 10,
        "invalid_count": 0,
        "invalid_events": []
    }
    
    # Get security verification
    security = agent.verify_security()
    
    # Check result
    assert security["status"] == "PASSED"
    assert security["verified_count"] == 10
    assert security["valid_count"] == 10
    assert security["invalid_count"] == 0
    assert "agent_name" in security
    assert "verification_time" in security
    
    # Verify log_event was called
    agent.audit_system.log_event.assert_called_with(
        "security_verification",
        f"Agent {agent.name} performed security verification",
        security
    )


def test_verify_security_error(agent):
    """Test security verification error case"""
    # Make verify_seals throw an exception
    agent.audit_system.verify_seals.side_effect = Exception("Mock security error")
    
    # Get security verification
    security = agent.verify_security()
    
    # Should return error
    assert "error" in security
    assert "Failed to verify security" in security["error"]


def test_health_check_full(agent):
    """Test comprehensive health check with ceiling and security"""
    # Set metrics
    agent.metrics["tasks_completed"] = 5
    agent.metrics["tasks_failed"] = 1
    agent.metrics["avg_task_duration"] = 0.75
    
    # Mock ceiling status and security verification
    with patch.object(agent, 'get_ceiling_status') as mock_ceiling_status, \
         patch.object(agent, 'verify_security') as mock_verify_security:
        
        # Configure mocks
        mock_ceiling_status.return_value = {
            "config_id": "agent_testagent",
            "service_tier": "professional",
            "performance_score": 0.85
        }
        
        mock_verify_security.return_value = {
            "status": "PASSED",
            "valid_count": 10,
            "invalid_count": 0
        }
        
        # Get health check
        health = agent.health_check()
        
        # Check health status
        assert health["status"] == "healthy"
        assert health["agent_name"] == "TestAgent"
        assert isinstance(health["uptime_seconds"], float)
        assert health["tasks_completed"] == 5
        assert health["tasks_failed"] == 1
        assert health["ceiling_status"]["config_id"] == "agent_testagent"
        assert health["security"]["status"] == "PASSED"


def test_health_check_degraded(agent):
    """Test health check with degraded status"""
    # Set metrics
    agent.metrics["tasks_completed"] = 5
    agent.metrics["tasks_failed"] = 2
    
    # Mock ceiling status and security verification
    with patch.object(agent, 'get_ceiling_status') as mock_ceiling_status, \
         patch.object(agent, 'verify_security') as mock_verify_security:
        
        # Configure mocks with issues
        mock_ceiling_status.return_value = {
            "error": "Ceiling system unavailable"
        }
        
        mock_verify_security.return_value = {
            "status": "FAILED",
            "valid_count": 8,
            "invalid_count": 2
        }
        
        # Get health check
        health = agent.health_check()
        
        # Should report degraded status
        assert health["status"] == "degraded"
        assert "warning" in health


def test_health_check_security_degraded(agent):
    """Test health check with security issues"""
    # Mock ceiling status and security verification
    with patch.object(agent, 'get_ceiling_status') as mock_ceiling_status, \
         patch.object(agent, 'verify_security') as mock_verify_security:
        
        # Configure mocks with security issues
        mock_ceiling_status.return_value = {
            "config_id": "agent_testagent"
        }
        
        mock_verify_security.return_value = {
            "status": "FAILED",
            "valid_count": 8,
            "invalid_count": 2
        }
        
        # Get health check
        health = agent.health_check()
        
        # Should report degraded status due to security
        assert health["status"] == "degraded"
        assert "security" in health
        assert health["security"]["invalid_seals"] == 2


def test_cli_run_command():
    """Test the CLI run command"""
    with patch('argparse.ArgumentParser') as mock_parser, \
         patch('strategydeck_agent.StrategyDECKAgent') as mock_agent_class:
        
        # Configure mock parser
        mock_args = mock_parser.return_value.parse_args.return_value
        mock_args.command = "run"
        mock_args.goal = "Test goal"
        mock_args.priority = "high"
        mock_args.constraints = ["constraint1", "constraint2"]
        mock_args.resource = [("compute", "10"), ("memory", "8")]
        
        # Configure mock agent
        mock_agent = mock_agent_class.return_value
        mock_agent.run_task.return_value = {
            "status": "success",
            "goal_processed": "Test goal",
            "steps_completed": ["step1", "step2"]
        }
        
        # Run the CLI code
        with patch('sys.argv', ['strategydeck_agent.py', 'run', 
                              '--goal', 'Test goal', 
                              '--priority', 'high',
                              '--constraints', 'constraint1', 'constraint2',
                              '--resource', 'compute', '10',
                              '--resource', 'memory', '8']), \
             patch('builtins.print') as mock_print:
            
            # Import to trigger __main__
            import importlib
            import strategydeck_agent
            importlib.reload(strategydeck_agent)
            
            # Check that the agent was initialized correctly
            mock_agent_class.assert_called_once()
            
            # Check that run_task was called with the right strategy data
            call_args = mock_agent.run_task.call_args[0]
            assert call_args[0] == mock_agent.automate_strategy
            assert call_args[1]["goal"] == "Test goal"
            assert call_args[1]["priority"] == "high"
            assert "constraint1" in call_args[1]["constraints"]
            assert call_args[1]["resources"]["compute"] == 10.0
            assert call_args[1]["resources"]["memory"] == 8.0


def test_cli_status_command():
    """Test the CLI status command"""
    with patch('argparse.ArgumentParser') as mock_parser, \
         patch('strategydeck_agent.StrategyDECKAgent') as mock_agent_class:
        
        # Configure mock parser
        mock_args = mock_parser.return_value.parse_args.return_value
        mock_args.command = "status"
        
        # Configure mock agent
        mock_agent = mock_agent_class.return_value
        mock_agent.health_check.return_value = {
            "status": "healthy",
            "agent_name": "StrategyDECKAgent",
            "uptime_seconds": 3600
        }
        
        # Run the CLI code
        with patch('sys.argv', ['strategydeck_agent.py', 'status']), \
             patch('builtins.print') as mock_print, \
             patch('json.dumps') as mock_dumps:
            
            # Import to trigger __main__
            import importlib
            import strategydeck_agent
            importlib.reload(strategydeck_agent)
            
            # Check that the agent was initialized correctly
            mock_agent_class.assert_called_once()
            
            # Check that health_check was called
            mock_agent.health_check.assert_called_once()
            
            # Check that results were printed
            mock_dumps.assert_called_once()


def test_cli_demo_mode():
    """Test the CLI demo mode (default)"""
    with patch('argparse.ArgumentParser') as mock_parser, \
         patch('strategydeck_agent.StrategyDECKAgent') as mock_agent_class:
        
        # Configure mock parser
        mock_args = mock_parser.return_value.parse_args.return_value
        mock_args.command = None
        
        # Configure mock agent
        mock_agent = mock_agent_class.return_value
        mock_agent.run_task.return_value = {
            "status": "success", 
            "goal_processed": "Demo goal"
        }
        mock_agent.run_concurrent_tasks.return_value = {
            "strategy1": {"status": "success"},
            "strategy2": {"status": "success"}
        }
        mock_agent.health_check.return_value = {"status": "healthy"}
        
        # Run the CLI code
        with patch('sys.argv', ['strategydeck_agent.py']), \
             patch('builtins.print') as mock_print:
            
            # Import to trigger __main__
            import importlib
            import strategydeck_agent
            importlib.reload(strategydeck_agent)
            
            # Check that the agent was initialized correctly
            mock_agent_class.assert_called_once()
            
            # Check that demo functions were called
            mock_agent.run_task.assert_called_once()
            mock_agent.run_concurrent_tasks.assert_called_once()
            mock_agent.health_check.assert_called_once()


def test_error_handling_in_cli():
    """Test error handling in the CLI"""
    with patch('argparse.ArgumentParser') as mock_parser, \
         patch('strategydeck_agent.StrategyDECKAgent') as mock_agent_class:
        
        # Configure mock parser
        mock_args = mock_parser.return_value.parse_args.return_value
        mock_args.command = "run"
        mock_args.goal = "Test goal"
        mock_args.priority = "high"
        mock_args.constraints = None
        mock_args.resource = None
        
        # Configure mock agent to raise an exception
        mock_agent = mock_agent_class.return_value
        mock_agent.run_task.side_effect = Exception("Test exception")
        
        # Run the CLI code
        with patch('sys.argv', ['strategydeck_agent.py', 'run', '--goal', 'Test goal']), \
             patch('builtins.print') as mock_print, \
             patch('traceback.print_exc') as mock_traceback:
            
            # Import to trigger __main__
            import importlib
            import strategydeck_agent
            importlib.reload(strategydeck_agent)
            
            # Check that exception was handled
            mock_print.assert_any_call("Error: Test exception")
            mock_traceback.assert_called_once()
            
            # Check that shutdown was called
            mock_agent.shutdown.assert_called_once()


def test_keyboard_interrupt_handling():
    """Test keyboard interrupt handling in the CLI"""
    with patch('argparse.ArgumentParser') as mock_parser, \
         patch('strategydeck_agent.StrategyDECKAgent') as mock_agent_class:
        
        # Configure mock parser
        mock_args = mock_parser.return_value.parse_args.return_value
        mock_args.command = "run"
        mock_args.goal = "Test goal"
        mock_args.priority = "high"
        mock_args.constraints = None
        mock_args.resource = None
        
        # Configure mock agent to raise KeyboardInterrupt
        mock_agent = mock_agent_class.return_value
        mock_agent.run_task.side_effect = KeyboardInterrupt()
        
        # Run the CLI code
        with patch('sys.argv', ['strategydeck_agent.py', 'run', '--goal', 'Test goal']), \
             patch('builtins.print') as mock_print:
            
            # Import to trigger __main__
            import importlib
            import strategydeck_agent
            importlib.reload(strategydeck_agent)
            
            # Check that interrupt was handled
            mock_print.assert_any_call("\nOperation interrupted by user")
            
            # Check that shutdown was called
            mock_agent.shutdown.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
