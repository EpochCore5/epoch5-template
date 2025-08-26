#!/usr/bin/env python3
"""
Unit tests for DAG management functionality
"""

import json
from pathlib import Path
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dag_management import DAGManager, TaskStatus

class TestDAGManager:
    """Test cases for DAGManager class"""
    
    def test_dag_manager_initialization(self, temp_workspace):
        """Test DAGManager initializes correctly"""
        manager = DAGManager(str(temp_workspace))
        assert manager.base_dir == str(temp_workspace)
        assert Path(manager.dags_file).parent.exists()
    
    def test_validate_dag_simple(self, temp_workspace):
        """Test DAG validation with simple valid DAG"""
        manager = DAGManager(str(temp_workspace))
        
        tasks = [
            {"task_id": "task1", "dependencies": []},
            {"task_id": "task2", "dependencies": ["task1"]},
            {"task_id": "task3", "dependencies": ["task1", "task2"]}
        ]
        
        assert manager.validate_dag(tasks) == True
    
    def test_validate_dag_with_cycle(self, temp_workspace):
        """Test DAG validation detects cycles"""
        manager = DAGManager(str(temp_workspace))
        
        # Create circular dependency
        tasks = [
            {"task_id": "task1", "dependencies": ["task2"]},
            {"task_id": "task2", "dependencies": ["task1"]}
        ]
        
        assert manager.validate_dag(tasks) == False
    
    def test_validate_dag_missing_dependency(self, temp_workspace):
        """Test DAG validation detects missing dependencies"""
        manager = DAGManager(str(temp_workspace))
        
        tasks = [
            {"task_id": "task1", "dependencies": ["missing_task"]},
        ]
        
        assert manager.validate_dag(tasks) == False
    
    def test_create_dag(self, temp_workspace, sample_dag_data):
        """Test DAG creation"""
        manager = DAGManager(str(temp_workspace))
        
        tasks = list(sample_dag_data["tasks"].values())
        result = manager.create_dag(sample_dag_data["dag_id"], tasks)
        
        assert result["success"] == True
        assert result["dag_id"] == sample_dag_data["dag_id"]
        
        # Verify DAG was saved
        dags = manager.load_dags()
        assert sample_dag_data["dag_id"] in dags["dags"]
    
    def test_get_ready_tasks(self, temp_workspace):
        """Test getting ready tasks for execution"""
        manager = DAGManager(str(temp_workspace))
        
        # Create DAG with mixed task statuses
        tasks = [
            {"task_id": "task1", "dependencies": []},
            {"task_id": "task2", "dependencies": ["task1"]},
            {"task_id": "task3", "dependencies": ["task1"]}
        ]
        
        dag_id = "test_ready_tasks"
        manager.create_dag(dag_id, tasks)
        
        # Initially, only task1 should be ready
        ready_tasks = manager.get_ready_tasks(dag_id)
        assert len(ready_tasks) == 1
        assert ready_tasks[0]["task_id"] == "task1"
        
        # Complete task1
        manager.complete_task(dag_id, "task1")
        
        # Now task2 and task3 should be ready
        ready_tasks = manager.get_ready_tasks(dag_id)
        ready_task_ids = [task["task_id"] for task in ready_tasks]
        assert "task2" in ready_task_ids
        assert "task3" in ready_task_ids
    
    def test_assign_task(self, temp_workspace):
        """Test task assignment to agents"""
        manager = DAGManager(str(temp_workspace))
        
        tasks = [{"task_id": "task1", "dependencies": []}]
        dag_id = "test_assign"
        manager.create_dag(dag_id, tasks)
        
        agent_did = "did:epoch5:agent:test123"
        result = manager.assign_task(dag_id, "task1", agent_did)
        
        assert result == True
        
        # Verify task status changed
        dags = manager.load_dags()
        task = dags["dags"][dag_id]["tasks"]["task1"]
        assert task["status"] == TaskStatus.RUNNING.value
        assert task["assigned_agent"] == agent_did
    
    def test_complete_task(self, temp_workspace):
        """Test task completion"""
        manager = DAGManager(str(temp_workspace))
        
        tasks = [{"task_id": "task1", "dependencies": []}]
        dag_id = "test_complete"
        manager.create_dag(dag_id, tasks)
        
        # Assign and complete task
        agent_did = "did:epoch5:agent:test123"
        manager.assign_task(dag_id, "task1", agent_did)
        result = manager.complete_task(dag_id, "task1", "Task output", True)
        
        assert result == True
        
        # Verify task status
        dags = manager.load_dags()
        task = dags["dags"][dag_id]["tasks"]["task1"]
        assert task["status"] == TaskStatus.COMPLETED.value
        assert task["output"] == "Task output"
    
    def test_execute_dag_simulation(self, temp_workspace):
        """Test DAG execution in simulation mode"""
        manager = DAGManager(str(temp_workspace))
        
        tasks = [
            {"task_id": "task1", "dependencies": []},
            {"task_id": "task2", "dependencies": ["task1"]},
            {"task_id": "task3", "dependencies": ["task1", "task2"]}
        ]
        
        dag_id = "test_execution"
        manager.create_dag(dag_id, tasks)
        
        result = manager.execute_dag(dag_id, simulation=True)
        
        assert result["final_status"] == "completed"
        assert len(result["completed_tasks"]) == 3
        assert len(result["failed_tasks"]) == 0
    
    def test_dag_persistence(self, temp_workspace):
        """Test DAG data persistence"""
        manager = DAGManager(str(temp_workspace))
        
        tasks = [{"task_id": "persist_task", "dependencies": []}]
        dag_id = "persist_dag"
        manager.create_dag(dag_id, tasks)
        
        # Create new manager instance
        manager2 = DAGManager(str(temp_workspace))
        dags = manager2.load_dags()
        
        # Verify DAG persisted
        assert dag_id in dags["dags"]
        assert "persist_task" in dags["dags"][dag_id]["tasks"]
    
    def test_complex_dag_validation(self, temp_workspace):
        """Test validation of complex DAG structures"""
        manager = DAGManager(str(temp_workspace))
        
        # Complex but valid DAG
        tasks = [
            {"task_id": "start", "dependencies": []},
            {"task_id": "process_a", "dependencies": ["start"]},
            {"task_id": "process_b", "dependencies": ["start"]},
            {"task_id": "merge", "dependencies": ["process_a", "process_b"]},
            {"task_id": "finalize", "dependencies": ["merge"]}
        ]
        
        assert manager.validate_dag(tasks) == True
        
        # Create and validate the DAG
        result = manager.create_dag("complex_dag", tasks)
        assert result["success"] == True
    
    def test_task_status_transitions(self, temp_workspace):
        """Test valid task status transitions"""
        manager = DAGManager(str(temp_workspace))
        
        tasks = [{"task_id": "status_task", "dependencies": []}]
        dag_id = "status_test"
        manager.create_dag(dag_id, tasks)
        
        agent_did = "did:epoch5:agent:test123"
        
        # Test valid transitions: pending -> running -> completed
        manager.assign_task(dag_id, "status_task", agent_did)
        dags = manager.load_dags()
        assert dags["dags"][dag_id]["tasks"]["status_task"]["status"] == TaskStatus.RUNNING.value
        
        manager.complete_task(dag_id, "status_task", "Success", True)
        dags = manager.load_dags()
        assert dags["dags"][dag_id]["tasks"]["status_task"]["status"] == TaskStatus.COMPLETED.value
    
    def test_dag_with_failed_task(self, temp_workspace):
        """Test DAG handling with failed tasks"""
        manager = DAGManager(str(temp_workspace))
        
        tasks = [
            {"task_id": "task1", "dependencies": []},
            {"task_id": "task2", "dependencies": ["task1"]}
        ]
        
        dag_id = "fail_test"
        manager.create_dag(dag_id, tasks)
        
        agent_did = "did:epoch5:agent:test123"
        
        # Fail task1
        manager.assign_task(dag_id, "task1", agent_did)
        manager.complete_task(dag_id, "task1", "Failed", False)
        
        # task2 should not be ready since task1 failed
        ready_tasks = manager.get_ready_tasks(dag_id)
        task_ids = [task["task_id"] for task in ready_tasks]
        assert "task2" not in task_ids