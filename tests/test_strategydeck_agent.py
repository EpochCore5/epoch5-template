"""
Test suite for the StrategyDECKAgent
"""
import os
import time
import pytest
import logging
import sys
from typing import Dict, Any
from unittest.mock import patch, MagicMock

# Mock the ceiling_manager and epoch_audit imports before importing StrategyDECKAgent
sys.modules['ceiling_manager'] = MagicMock()
sys.modules['epoch_audit'] = MagicMock()

# Set the global flag before importing
import strategydeck_agent
strategydeck_agent.CEILING_SYSTEM_AVAILABLE = True

from strategydeck_agent import StrategyDECKAgent


@pytest.fixture
def agent():
    """Create a test agent instance"""
    with patch('strategydeck_agent.CeilingManager') as mock_ceiling_manager, \
         patch('strategydeck_agent.EpochAudit') as mock_audit:
        
        # Configure mock ceiling manager
        mock_cm_instance = mock_ceiling_manager.return_value
        mock_cm_instance.load_ceilings.return_value = {"configurations": {}}
        
        agent = StrategyDECKAgent(name="TestAgent", log_level=logging.ERROR)
        yield agent


def test_agent_initialization():
    """Test that agent initializes correctly with different parameters"""
    # Set up mocks
    with patch('strategydeck_agent.CeilingManager') as mock_ceiling_manager, \
         patch('strategydeck_agent.EpochAudit') as mock_audit:
        
        # Configure mock ceiling manager
        mock_cm_instance = mock_ceiling_manager.return_value
        mock_cm_instance.load_ceilings.return_value = {"configurations": {}}
        
        # Basic initialization
        agent1 = StrategyDECKAgent()
        assert agent1.name == "StrategyDECKAgent"
        assert agent1.max_workers == 4
        
        # Custom initialization
        agent2 = StrategyDECKAgent(name="CustomAgent", max_workers=8, log_level=logging.DEBUG)
        assert agent2.name == "CustomAgent"
        assert agent2.max_workers == 8
        
        # Check metrics initialization
        assert agent1.metrics["tasks_completed"] == 0
        assert agent1.metrics["tasks_failed"] == 0


def test_run_task_success(agent):
    """Test successful task execution"""
    def sample_task(x, y):
        return x + y
    
    result = agent.run_task(sample_task, 5, 7)
    assert result == 12
    assert agent.metrics["tasks_completed"] == 1
    assert agent.metrics["tasks_failed"] == 0


def test_run_task_failure(agent):
    """Test failed task execution"""
    def failing_task():
        raise ValueError("Test error")
    
    result = agent.run_task(failing_task)
    assert result is None
    assert agent.metrics["tasks_completed"] == 0
    assert agent.metrics["tasks_failed"] == 1


def test_run_task_with_retries(agent):
    """Test task execution with retries"""
    # Create a task that fails twice then succeeds
    counter = {"attempts": 0}
    
    def flaky_task():
        counter["attempts"] += 1
        if counter["attempts"] < 3:
            raise ConnectionError("Simulated connection error")
        return "success"
    
    # Should fail without enough retries
    result1 = agent.run_task(flaky_task, retries=1)
    assert result1 is None
    
    # Reset counter
    counter["attempts"] = 0
    
    # Should succeed with enough retries
    result2 = agent.run_task(flaky_task, retries=3)
    assert result2 == "success"


def test_run_task_with_timeout(agent):
    """Test task execution with timeout"""
    def slow_task():
        time.sleep(2)
        return "completed"
    
    # Test with timeout - we need to mock the ThreadPoolExecutor
    with patch('concurrent.futures.ThreadPoolExecutor.submit') as mock_submit:
        # Setup the mock for timeout failure
        mock_future = MagicMock()
        mock_future.result.side_effect = TimeoutError("Task timed out")
        mock_submit.return_value = mock_future
        
        # Should fail with short timeout
        result1 = agent.run_task(slow_task, timeout=0.1)
        assert result1 is None
        
        # Change mock for success
        mock_future.result.side_effect = None
        mock_future.result.return_value = "completed"
        
        # Should succeed with sufficient timeout
        result2 = agent.run_task(slow_task, timeout=3)
        assert result2 == "completed"


def test_automate_strategy_validation(agent):
    """Test strategy data validation"""
    # Test invalid input type
    with pytest.raises(ValueError) as exc_info:
        agent.automate_strategy("not-a-dict")
    assert "must be a dictionary" in str(exc_info.value)
    
    # Test missing required field
    with pytest.raises(ValueError) as exc_info:
        agent.automate_strategy({})
    assert "Required field 'goal'" in str(exc_info.value)
    
    # Test invalid priority normalization
    result = agent.automate_strategy({"goal": "Test goal", "priority": "INVALID"})
    assert result["priority"] == "medium"  # Should normalize to default


def test_automate_strategy_success(agent):
    """Test successful strategy automation"""
    strategy_data = {
        "goal": "Optimize workflow",
        "priority": "high",
        "constraints": ["time-sensitive"],
        "resources": {"compute": 10}
    }
    
    result = agent.automate_strategy(strategy_data)
    
    # Check result structure
    assert result["status"] == "success"
    assert result["goal_processed"] == "Optimize workflow"
    assert result["priority"] == "high"
    assert isinstance(result["execution_time"], float)
    assert "time-sensitive" in result["constraints_applied"]
    assert len(result["steps_completed"]) >= 3  # Should have multiple steps


def test_run_concurrent_tasks(agent):
    """Test concurrent task execution"""
    tasks = [
        {
            "task_id": "task1",
            "callable": lambda x: x * 2,
            "args": [5]
        },
        {
            "task_id": "task2",
            "callable": lambda x, y: x + y,
            "kwargs": {"x": 3, "y": 7}
        },
        {
            "task_id": "task3",
            "callable": lambda: 1/0,  # Will cause error
        }
    ]
    
    # Mock run_task to simulate specific behavior for each task
    with patch.object(agent, 'run_task') as mock_run_task:
        def mock_run_task_impl(callable_func, *args, **kwargs):
            # Simulate task1
            if callable_func == tasks[0]['callable']:
                return 10
            # Simulate task2
            elif callable_func == tasks[1]['callable']:
                return 10
            # Simulate task3 (error case)
            elif callable_func == tasks[2]['callable']:
                return None
            return "Unexpected task"
            
        mock_run_task.side_effect = mock_run_task_impl
        
        # For the run_concurrent_tasks function, we also need to patch ThreadPoolExecutor
        with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
            # Set up mock results
            results = {
                "task1": {"status": "success", "result": 10},
                "task2": {"status": "success", "result": 10},
                "task3": {"status": "error", "error": "division by zero", "error_type": "ZeroDivisionError"}
            }
            
            # Create mock futures for each task
            mock_futures = {}
            for i, task in enumerate(tasks):
                task_id = task.get('task_id')
                mock_future = MagicMock()
                if task_id == "task1" or task_id == "task2":
                    mock_future.result.return_value = 10
                elif task_id == "task3":
                    mock_future.result.side_effect = Exception("Division by zero")
                mock_futures[task_id] = mock_future
            
            # Create a mock context manager for the executor
            mock_context = MagicMock()
            mock_context.__enter__.return_value = mock_context
            mock_executor.return_value = mock_context
            
            # Set up submit to return the appropriate future
            def mock_submit_side_effect(func, *args, **kwargs):
                if func == agent.run_task:
                    if args[0] == tasks[0]['callable']:
                        return mock_futures["task1"]
                    elif args[0] == tasks[1]['callable']:
                        return mock_futures["task2"]
                    elif args[0] == tasks[2]['callable']:
                        return mock_futures["task3"]
                return MagicMock()
            
            mock_context.submit.side_effect = mock_submit_side_effect
            
            # Configure as_completed to return our futures
            with patch('strategydeck_agent.as_completed') as mock_as_completed:
                mock_as_completed.return_value = list(mock_futures.values())
                
                # Run the actual method under test
                actual_results = agent.run_concurrent_tasks(tasks)
            
            assert len(actual_results) == 3
            assert "task1" in actual_results
            assert "task2" in actual_results
            assert "task3" in actual_results


def test_health_check(agent):
    """Test agent health check"""
    # Set metrics directly
    agent.metrics["tasks_completed"] = 1
    agent.metrics["tasks_failed"] = 1
    
    # Mock the methods that are causing issues
    with patch.object(agent, 'get_ceiling_status') as mock_ceiling_status, \
         patch.object(agent, 'verify_security') as mock_verify_security:
        
        # Set up mock returns
        mock_ceiling_status.return_value = {"config_id": "test_config"}
        mock_verify_security.return_value = {
            "status": "VERIFIED",
            "valid_count": 10,
            "invalid_count": 0
        }
        
        # Get health check
        health = agent.health_check()
        
        # Updated assertions based on actual health_check method
        assert health["status"] == "healthy"
        assert health["agent_name"] == "TestAgent"
        assert isinstance(health["uptime_seconds"], float)
        assert health["tasks_completed"] == 1
        assert health["tasks_failed"] == 1


def test_shutdown(agent):
    """Test agent shutdown"""
    with patch.object(agent.executor, 'shutdown') as mock_shutdown:
        agent.shutdown()
        mock_shutdown.assert_called_once_with(wait=True)
        
        agent.shutdown(wait=False)
        mock_shutdown.assert_called_with(wait=False)


def test_error_recovery_mechanism():
    """Test error context saving and recovery detection"""
    with patch('strategydeck_agent.CeilingManager') as mock_ceiling_manager, \
         patch('strategydeck_agent.EpochAudit') as mock_audit:
         
        # Configure mock ceiling manager
        mock_cm_instance = mock_ceiling_manager.return_value
        mock_cm_instance.load_ceilings.return_value = {"configurations": {}}
        
        agent = StrategyDECKAgent(name="RecoveryTest")
        
        # Test with recoverable error
        with patch.object(agent, '_save_error_context') as mock_save:
            def task_with_recoverable_error():
                raise ConnectionError("Network timeout")
            
            agent.run_task(task_with_recoverable_error)
            mock_save.assert_called_once()
        
        # Check error recovery detection
        assert agent._is_error_recoverable("ConnectionError") is True
        assert agent._is_error_recoverable("ValueError") is False
        assert agent._is_error_recoverable("ResourceUnavailable") is True


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
