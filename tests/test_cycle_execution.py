"""
Tests for cycle_execution functionality
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from cycle_execution import CycleExecutor, CycleStatus, PBFTPhase, main
except ImportError as e:
    pytest.skip(f"Could not import cycle_execution module: {e}", allow_module_level=True)


class TestCycleExecutor:
    """Test cases for CycleExecutor class"""
    
    @pytest.fixture
    def cycle_executor_instance(self, temp_dir):
        """Create a CycleExecutor instance for testing"""
        # Create necessary directory structure
        cycles_dir = Path(temp_dir) / "cycles"
        cycles_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the ceiling manager
        with patch('cycle_execution.CeilingManager', MagicMock()), \
             patch('cycle_execution.CEILING_MANAGER_AVAILABLE', True):
            
            instance = CycleExecutor(base_dir=temp_dir)
            
            # Setup ceiling manager behavior
            if instance.ceiling_manager:
                instance.ceiling_manager.get_effective_ceiling.return_value = 100.0
                instance.ceiling_manager.adjust_ceiling_for_performance.return_value = True
                instance.ceiling_manager.get_upgrade_recommendations.return_value = {
                    "recommended_tier": "premium",
                    "reason": "Better performance"
                }
            
            return instance
    
    @pytest.fixture
    def sample_task_assignments(self):
        """Sample task assignments for testing"""
        return [
            {
                "task_id": "task_001",
                "agent_did": "did:example:agent1",
                "input": {"data": "test input 1"},
                "priority": "high"
            },
            {
                "task_id": "task_002",
                "agent_did": "did:example:agent2",
                "input": {"data": "test input 2"},
                "priority": "medium"
            }
        ]
    
    @pytest.fixture
    def sample_cycle(self, cycle_executor_instance, sample_task_assignments):
        """Create a sample cycle for testing"""
        cycle = cycle_executor_instance.create_cycle(
            "test_cycle_001",
            100.0,
            30.0,
            sample_task_assignments,
            {"min_success_rate": 0.95, "max_failure_rate": 0.05, "max_retry_count": 3},
            "premium",
            "ceiling_config_001"
        )
        cycle_executor_instance.save_cycle(cycle)
        return cycle
    
    @pytest.fixture
    def sample_validator_nodes(self):
        """Sample validator nodes for testing"""
        return ["validator1", "validator2", "validator3", "validator4"]
    
    def test_initialization(self, cycle_executor_instance):
        """Test that CycleExecutor initializes correctly"""
        assert cycle_executor_instance is not None
        assert isinstance(cycle_executor_instance.base_dir, Path)
        assert isinstance(cycle_executor_instance.cycles_dir, Path)
        assert cycle_executor_instance.cycles_dir.exists()
        
        # Check that ceiling manager was initialized if available
        if hasattr(cycle_executor_instance, 'ceiling_manager'):
            assert cycle_executor_instance.ceiling_manager is not None
    
    def test_timestamp(self, cycle_executor_instance):
        """Test timestamp functionality"""
        timestamp = cycle_executor_instance.timestamp()
        assert timestamp is not None
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format has T between date and time
        assert "Z" in timestamp  # UTC timezone marker
    
    def test_sha256(self, cycle_executor_instance):
        """Test SHA256 hash generation"""
        test_data = "test data for hashing"
        hash_value = cycle_executor_instance.sha256(test_data)
        
        # Verify hash properties
        assert hash_value is not None
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 is 64 hex characters
        assert all(c in "0123456789abcdef" for c in hash_value)  # Only hex characters
    
    def test_create_cycle(self, cycle_executor_instance, sample_task_assignments):
        """Test create_cycle functionality"""
        # Create cycle with ceiling configuration
        cycle = cycle_executor_instance.create_cycle(
            "test_cycle_001",
            100.0,
            30.0,
            sample_task_assignments,
            {"min_success_rate": 0.95, "max_failure_rate": 0.05, "max_retry_count": 3},
            "premium",
            "ceiling_config_001"
        )
        
        # Verify cycle structure
        assert cycle is not None
        assert isinstance(cycle, dict)
        assert cycle["cycle_id"] == "test_cycle_001"
        assert cycle["budget"] == 100.0
        assert cycle["max_latency"] == 30.0
        assert cycle["task_assignments"] == sample_task_assignments
        assert cycle["service_tier"] == "premium"
        assert cycle["ceiling_config_id"] == "ceiling_config_001"
        assert cycle["status"] == CycleStatus.PLANNED.value
        assert cycle["consensus_state"]["phase"] is None
        assert cycle["execution_metrics"]["total_tasks"] == len(sample_task_assignments)
        assert "hash" in cycle
        
        # Create cycle without ceiling configuration
        cycle_no_ceiling = cycle_executor_instance.create_cycle(
            "test_cycle_002",
            50.0,
            15.0,
            sample_task_assignments
        )
        assert cycle_no_ceiling["cycle_id"] == "test_cycle_002"
        assert cycle_no_ceiling["budget"] == 50.0
        assert cycle_no_ceiling["ceiling_config_id"] is None
    
    def test_save_and_load_cycles(self, cycle_executor_instance, sample_cycle):
        """Test save_cycle and load_cycles functionality"""
        # Save sample cycle
        result = cycle_executor_instance.save_cycle(sample_cycle)
        assert result is True
        
        # Load cycles
        cycles = cycle_executor_instance.load_cycles()
        assert isinstance(cycles, dict)
        assert "cycles" in cycles
        assert "last_updated" in cycles
        assert sample_cycle["cycle_id"] in cycles["cycles"]
        assert cycles["cycles"][sample_cycle["cycle_id"]] == sample_cycle
        
        # Test loading when cycles file doesn't exist
        with patch.object(cycle_executor_instance, 'cycles_file', Path('/nonexistent/file.json')):
            empty_cycles = cycle_executor_instance.load_cycles()
            assert empty_cycles["cycles"] == {}
    
    def test_start_cycle(self, cycle_executor_instance, sample_cycle, sample_validator_nodes):
        """Test start_cycle functionality"""
        # Start cycle
        with patch.object(cycle_executor_instance, 'initiate_pbft_consensus') as mock_consensus:
            result = cycle_executor_instance.start_cycle(sample_cycle["cycle_id"], sample_validator_nodes)
            assert result is True
            
            # Verify cycle status was updated
            cycles = cycle_executor_instance.load_cycles()
            started_cycle = cycles["cycles"][sample_cycle["cycle_id"]]
            assert started_cycle["status"] == CycleStatus.EXECUTING.value
            assert started_cycle["started_at"] is not None
            assert started_cycle["consensus_state"]["validator_nodes"] == sample_validator_nodes
            assert started_cycle["consensus_state"]["phase"] == PBFTPhase.PRE_PREPARE.value
            
            # Verify consensus was initiated
            mock_consensus.assert_called_once()
            
            # Test starting a non-existent cycle
            result = cycle_executor_instance.start_cycle("nonexistent_cycle", sample_validator_nodes)
            assert result is False
            
            # Test starting a cycle that's not in PLANNED state
            cycle_copy = started_cycle.copy()
            cycle_copy["status"] = CycleStatus.COMPLETED.value
            cycle_executor_instance.save_cycle(cycle_copy)
            
            result = cycle_executor_instance.start_cycle(sample_cycle["cycle_id"], sample_validator_nodes)
            assert result is False
    
    def test_execute_task_assignment(self, cycle_executor_instance, sample_cycle):
        """Test execute_task_assignment functionality"""
        # Start cycle
        with patch.object(cycle_executor_instance, 'initiate_pbft_consensus'):
            cycle_executor_instance.start_cycle(sample_cycle["cycle_id"], ["validator1", "validator2"])
        
        # Execute task with simulation
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = cycle_executor_instance.execute_task_assignment(sample_cycle["cycle_id"], 0, simulation=True)
            
            # Verify result structure
            assert isinstance(result, dict)
            assert "assignment_index" in result
            assert "task_id" in result
            assert "started_at" in result
            assert "completed_at" in result
            assert "success" in result
            assert "latency" in result
            assert "cost" in result
            
            # Verify cycle was updated
            cycles = cycle_executor_instance.load_cycles()
            updated_cycle = cycles["cycles"][sample_cycle["cycle_id"]]
            assert updated_cycle["spent_budget"] > 0
            assert updated_cycle["actual_latency"] > 0
            assert updated_cycle["execution_metrics"]["tasks_completed"] + updated_cycle["execution_metrics"]["tasks_failed"] == 1
            
            # Test executing non-existent cycle
            error_result = cycle_executor_instance.execute_task_assignment("nonexistent_cycle", 0)
            assert "error" in error_result
            assert error_result["error"] == "Cycle not found"
            
            # Test invalid assignment index
            error_result = cycle_executor_instance.execute_task_assignment(sample_cycle["cycle_id"], 999)
            assert "error" in error_result
            assert error_result["error"] == "Invalid assignment index"
    
    def test_check_sla_compliance(self, cycle_executor_instance, sample_cycle):
        """Test check_sla_compliance functionality"""
        # Start cycle and execute tasks
        with patch.object(cycle_executor_instance, 'initiate_pbft_consensus'), \
             patch('time.sleep'):
                
            cycle_executor_instance.start_cycle(sample_cycle["cycle_id"], ["validator1", "validator2"])
            cycle_executor_instance.execute_task_assignment(sample_cycle["cycle_id"], 0)
            cycle_executor_instance.execute_task_assignment(sample_cycle["cycle_id"], 1)
        
        # Check SLA compliance
        with patch.object(cycle_executor_instance, 'save_sla_metrics'):
            sla_status = cycle_executor_instance.check_sla_compliance(sample_cycle["cycle_id"])
            
            # Verify SLA status structure
            assert isinstance(sla_status, dict)
            assert "cycle_id" in sla_status
            assert "checked_at" in sla_status
            assert "compliant" in sla_status
            assert "violations" in sla_status
            assert "metrics" in sla_status
            
            # Verify metrics
            assert "success_rate" in sla_status["metrics"]
            assert "budget_usage" in sla_status["metrics"]
            assert "latency_usage" in sla_status["metrics"]
            
            # Test non-existent cycle
            error_status = cycle_executor_instance.check_sla_compliance("nonexistent_cycle")
            assert "error" in error_status
            assert error_status["error"] == "Cycle not found"
    
    def test_initiate_pbft_consensus(self, cycle_executor_instance, sample_cycle, sample_validator_nodes):
        """Test initiate_pbft_consensus functionality"""
        # Start cycle to add validators
        cycle_copy = sample_cycle.copy()
        cycle_copy["consensus_state"]["validator_nodes"] = sample_validator_nodes
        cycle_executor_instance.save_cycle(cycle_copy)
        
        # Initiate consensus
        with patch.object(cycle_executor_instance, 'simulate_pbft_voting'), \
             patch.object(cycle_executor_instance, 'log_consensus'):
                
            consensus_request = cycle_executor_instance.initiate_pbft_consensus(
                sample_cycle["cycle_id"],
                "test_decision",
                {"action": "test_action"}
            )
            
            # Verify consensus request structure
            assert isinstance(consensus_request, dict)
            assert consensus_request["cycle_id"] == sample_cycle["cycle_id"]
            assert consensus_request["decision_type"] == "test_decision"
            assert consensus_request["proposal"]["action"] == "test_action"
            assert consensus_request["phase"] == PBFTPhase.PRE_PREPARE.value
            assert "sequence_number" in consensus_request
            assert "votes" in consensus_request
            assert "hash" in consensus_request
            
            # Test non-existent cycle - using a different approach than raising KeyError
            with patch.object(cycle_executor_instance, 'load_cycles') as mock_load:
                mock_load.return_value = {"cycles": {}}  # Empty cycles dict
                
                # This should return an error dict, not raise KeyError
                error_result = cycle_executor_instance.initiate_pbft_consensus("nonexistent_cycle", "test", {})
                assert isinstance(error_result, dict)
                assert "error" in error_result
    
    def test_simulate_pbft_voting(self, cycle_executor_instance, sample_validator_nodes):
        """Test simulate_pbft_voting functionality"""
        # Create consensus request
        consensus_request = {
            "cycle_id": "test_cycle_001",
            "decision_type": "test_decision",
            "proposal": {"action": "test_action"},
            "initiated_at": cycle_executor_instance.timestamp(),
            "phase": PBFTPhase.PRE_PREPARE.value,
            "sequence_number": 1,
            "votes": {"pre_prepare": {}, "prepare": {}, "commit": {}},
            "required_votes": (2 * len(sample_validator_nodes)) // 3 + 1,
            "hash": cycle_executor_instance.sha256("test_hash"),
        }
        
        # Simulate voting
        cycle_executor_instance.simulate_pbft_voting(consensus_request, sample_validator_nodes)
        
        # Verify voting results
        assert len(consensus_request["votes"]["pre_prepare"]) > 0
        
        # If pre-prepare passed, prepare should have votes
        if consensus_request["phase"] == PBFTPhase.PREPARE.value:
            assert len(consensus_request["votes"]["prepare"]) > 0
        
        # If prepare passed, commit should have votes
        if consensus_request["phase"] == PBFTPhase.COMMIT.value:
            assert len(consensus_request["votes"]["commit"]) > 0
            
        # If committed is True, all phases must have passed
        if consensus_request.get("committed", False):
            assert consensus_request["phase"] == PBFTPhase.COMMIT.value
            assert len(consensus_request["votes"]["pre_prepare"]) >= consensus_request["required_votes"]
            assert len(consensus_request["votes"]["prepare"]) >= consensus_request["required_votes"]
            assert len(consensus_request["votes"]["commit"]) >= consensus_request["required_votes"]
    
    def test_complete_cycle(self, cycle_executor_instance, sample_cycle, sample_validator_nodes):
        """Test complete_cycle functionality"""
        # Start cycle and execute tasks
        with patch.object(cycle_executor_instance, 'initiate_pbft_consensus'), \
             patch('time.sleep'):
                
            cycle_executor_instance.start_cycle(sample_cycle["cycle_id"], sample_validator_nodes)
            cycle_executor_instance.execute_task_assignment(sample_cycle["cycle_id"], 0)
            cycle_executor_instance.execute_task_assignment(sample_cycle["cycle_id"], 1)
        
        # Complete cycle
        with patch.object(cycle_executor_instance, 'check_sla_compliance') as mock_sla, \
             patch.object(cycle_executor_instance, 'initiate_pbft_consensus') as mock_consensus:
                
            mock_sla.return_value = {"compliant": True, "violations": []}
            mock_consensus.return_value = {"committed": True}
            
            result = cycle_executor_instance.complete_cycle(sample_cycle["cycle_id"])
            assert result is True
            
            # Verify cycle was updated
            cycles = cycle_executor_instance.load_cycles()
            completed_cycle = cycles["cycles"][sample_cycle["cycle_id"]]
            assert completed_cycle["status"] == CycleStatus.COMPLETED.value
            assert completed_cycle["completed_at"] is not None
            
            # Test completing non-existent cycle
            result = cycle_executor_instance.complete_cycle("nonexistent_cycle")
            assert result is False
            
            # Test completing cycle with wrong status
            cycle_copy = completed_cycle.copy()
            cycle_copy["status"] = CycleStatus.PLANNED.value
            cycle_executor_instance.save_cycle(cycle_copy)
            
            result = cycle_executor_instance.complete_cycle(sample_cycle["cycle_id"])
            assert result is False
            
            # Test force complete
            result = cycle_executor_instance.complete_cycle(sample_cycle["cycle_id"], force=True)
            assert result is True
    
    def test_execute_full_cycle(self, cycle_executor_instance, sample_cycle, sample_validator_nodes):
        """Test execute_full_cycle functionality"""
        # Mock all component methods to isolate test
        with patch.object(cycle_executor_instance, 'start_cycle') as mock_start, \
             patch.object(cycle_executor_instance, 'execute_task_assignment') as mock_execute, \
             patch.object(cycle_executor_instance, 'complete_cycle') as mock_complete, \
             patch.object(cycle_executor_instance, 'check_sla_compliance') as mock_sla, \
             patch.object(cycle_executor_instance, 'load_cycles') as mock_load:
                
            # Setup mocks
            mock_start.return_value = True
            mock_execute.return_value = {"success": True, "latency": 1.0, "cost": 10.0}
            mock_complete.return_value = True
            mock_sla.return_value = {"compliant": True}
            
            # Mock cycle data for various load_cycles calls
            cycles_data = {
                "cycles": {
                    sample_cycle["cycle_id"]: {
                        "task_assignments": sample_cycle["task_assignments"],
                        "spent_budget": 20.0,
                        "budget": 100.0,
                        "actual_latency": 2.0,
                        "max_latency": 30.0,
                        "status": CycleStatus.COMPLETED.value,
                        "execution_metrics": {"tasks_completed": 2, "total_tasks": 2},
                        "resource_usage": {"cpu_time": 1.0}
                    }
                }
            }
            mock_load.return_value = cycles_data
            
            # Execute full cycle
            result = cycle_executor_instance.execute_full_cycle(
                sample_cycle["cycle_id"],
                sample_validator_nodes,
                simulation=True
            )
            
            # Verify result structure
            assert isinstance(result, dict)
            assert result["cycle_id"] == sample_cycle["cycle_id"]
            assert "status" in result
            assert "execution_results" in result
            assert "final_metrics" in result
            assert "sla_compliance" in result
            assert "resource_usage" in result
            
            # Verify method calls
            mock_start.assert_called_once_with(sample_cycle["cycle_id"], sample_validator_nodes)
            assert mock_execute.call_count == 2  # Once for each task
            mock_complete.assert_called_once_with(sample_cycle["cycle_id"])
            mock_sla.assert_called_once_with(sample_cycle["cycle_id"])
            
            # Test failure to start cycle
            mock_start.reset_mock()
            mock_start.return_value = False
            
            error_result = cycle_executor_instance.execute_full_cycle(
                "error_cycle",
                sample_validator_nodes
            )
            assert "error" in error_result
            assert error_result["error"] == "Failed to start cycle"
    
    def test_log_execution(self, cycle_executor_instance):
        """Test log_execution functionality"""
        with patch('builtins.open', mock_open()) as mock_file:
            cycle_executor_instance.log_execution(
                "test_cycle_001",
                "TEST_EVENT",
                {"test_data": "test value"}
            )
            
            # Verify file was opened for appending
            mock_file.assert_called_once_with(cycle_executor_instance.execution_log, "a")
            
            # Verify write was called
            mock_file.return_value.write.assert_called_once()
            
            # Verify log entry format
            log_entry = mock_file.return_value.write.call_args[0][0]
            assert "timestamp" in log_entry
            assert "test_cycle_001" in log_entry
            assert "TEST_EVENT" in log_entry
            assert "test_data" in log_entry
            assert "hash" in log_entry
    
    def test_log_consensus(self, cycle_executor_instance):
        """Test log_consensus functionality"""
        consensus_request = {
            "cycle_id": "test_cycle_001",
            "decision_type": "test_decision",
            "proposal": {"action": "test_action"},
            "hash": "testhash123",
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            cycle_executor_instance.log_consensus(consensus_request)
            
            # Verify file was opened for appending
            mock_file.assert_called_once_with(cycle_executor_instance.consensus_log, "a")
            
            # Verify write was called
            mock_file.return_value.write.assert_called_once()
            
            # Verify log entry format
            log_entry = mock_file.return_value.write.call_args[0][0]
            assert "timestamp" in log_entry
            assert "consensus_request" in log_entry
            assert "test_cycle_001" in log_entry
            assert "hash" in log_entry
    
    def test_save_sla_metrics(self, cycle_executor_instance):
        """Test save_sla_metrics functionality"""
        sla_status = {
            "cycle_id": "test_cycle_001",
            "checked_at": cycle_executor_instance.timestamp(),
            "compliant": True,
            "violations": [],
            "metrics": {"success_rate": 1.0}
        }
        
        # Test with existing metrics file
        mock_file = mock_open(read_data='{"sla_reports": [], "last_updated": "2024-01-01T00:00:00Z"}')
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_file):
                
            cycle_executor_instance.save_sla_metrics(sla_status)
            
            # Verify write was called
            write_calls = [call for call in mock_file().mock_calls if 'write' in str(call)]
            assert len(write_calls) > 0
        
        # Test with non-existent metrics file
        mock_file = mock_open()
        with patch('pathlib.Path.exists', return_value=False), \
             patch('builtins.open', mock_file):
                
            cycle_executor_instance.save_sla_metrics(sla_status)
            
            # Verify write was called
            write_calls = [call for call in mock_file().mock_calls if 'write' in str(call)]
            assert len(write_calls) > 0


# Test main CLI function
def test_main():
    """Test the main CLI function"""
    # Test create command
    with patch('sys.argv', ['cycle_execution.py', 'create', 'test_cycle_001', '100.0', '30.0', 'assignments.json']), \
         patch('builtins.open', mock_open(read_data='{"assignments": [{"task_id": "task1"}], "sla_requirements": {"min_success_rate": 0.95}}')), \
         patch('cycle_execution.CycleExecutor') as mock_executor, \
         patch('builtins.print'):
            
        mock_instance = MagicMock()
        mock_executor.return_value = mock_instance
        mock_instance.create_cycle.return_value = {
            "cycle_id": "test_cycle_001",
            "task_assignments": [{"task_id": "task1"}]
        }
        
        main()
        
        # Verify methods were called
        mock_executor.assert_called_once()
        mock_instance.create_cycle.assert_called_once()
        mock_instance.save_cycle.assert_called_once()
    
    # Test execute command
    with patch('sys.argv', ['cycle_execution.py', 'execute', 'test_cycle_001', '--validators', 'v1', 'v2']), \
         patch('cycle_execution.CycleExecutor') as mock_executor, \
         patch('builtins.print'):
            
        mock_instance = MagicMock()
        mock_executor.return_value = mock_instance
        mock_instance.execute_full_cycle.return_value = {
            "status": "completed",
            "sla_compliance": {"compliant": True},
            "final_metrics": {"success_rate": 1.0}
        }
        
        main()
        
        # Verify methods were called
        mock_executor.assert_called_once()
        mock_instance.execute_full_cycle.assert_called_once_with(
            'test_cycle_001', ['v1', 'v2'], simulation=True
        )
    
    # Test status command
    with patch('sys.argv', ['cycle_execution.py', 'status', 'test_cycle_001']), \
         patch('cycle_execution.CycleExecutor') as mock_executor, \
         patch('builtins.print'):
            
        mock_instance = MagicMock()
        mock_executor.return_value = mock_instance
        mock_instance.load_cycles.return_value = {
            "cycles": {
                "test_cycle_001": {
                    "status": "completed",
                    "spent_budget": 50.0,
                    "budget": 100.0,
                    "execution_metrics": {
                        "tasks_completed": 2,
                        "total_tasks": 2
                    }
                }
            }
        }
        
        main()
        
        # Verify methods were called
        mock_executor.assert_called_once()
        mock_instance.load_cycles.assert_called_once()
    
    # Test sla command
    with patch('sys.argv', ['cycle_execution.py', 'sla', 'test_cycle_001']), \
         patch('cycle_execution.CycleExecutor') as mock_executor, \
         patch('builtins.print'):
            
        mock_instance = MagicMock()
        mock_executor.return_value = mock_instance
        mock_instance.check_sla_compliance.return_value = {
            "compliant": True,
            "violations": []
        }
        
        main()
        
        # Verify methods were called
        mock_executor.assert_called_once()
        mock_instance.check_sla_compliance.assert_called_once_with('test_cycle_001')
    
    # Test list command
    with patch('sys.argv', ['cycle_execution.py', 'list']), \
         patch('cycle_execution.CycleExecutor') as mock_executor, \
         patch('builtins.print'):
            
        mock_instance = MagicMock()
        mock_executor.return_value = mock_instance
        mock_instance.load_cycles.return_value = {
            "cycles": {
                "test_cycle_001": {
                    "status": "completed",
                    "spent_budget": 50.0,
                    "budget": 100.0
                },
                "test_cycle_002": {
                    "status": "executing",
                    "spent_budget": 20.0,
                    "budget": 100.0
                }
            }
        }
        
        main()
        
        # Verify methods were called
        mock_executor.assert_called_once()
        mock_instance.load_cycles.assert_called_once()
    
    # Test help/no command
    with patch('sys.argv', ['cycle_execution.py']), \
         patch('cycle_execution.CycleExecutor') as mock_executor, \
         patch('argparse.ArgumentParser.print_help') as mock_print_help:
            
        main()
        
        # Verify help was printed
        mock_print_help.assert_called_once()
