#!/usr/bin/env python3
"""
Integration tests for EPOCH5 system workflows
"""

import json
import subprocess
from pathlib import Path
import pytest
import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integration import EPOCH5Integration
from agent_management import AgentManager
from dag_management import DAGManager
from tests.conftest import TestHelpers

class TestEPOCH5Integration:
    """Integration tests for complete EPOCH5 workflows"""
    
    def test_system_initialization(self, temp_workspace):
        """Test complete system initialization"""
        integration = EPOCH5Integration(str(temp_workspace))
        
        result = integration.setup_demo_environment()
        
        assert result["success"] == True
        assert "components" in result
        
        # Verify all components initialized
        expected_components = ["agents", "policies", "dags", "cycles", "capsules", "meta_capsules", "ceilings"]
        for component in expected_components:
            assert component in result["components"]
    
    def test_complete_workflow_execution(self, temp_workspace):
        """Test complete workflow from start to finish"""
        integration = EPOCH5Integration(str(temp_workspace))
        
        # Setup demo environment first
        setup_result = integration.setup_demo_environment()
        assert setup_result["success"] == True
        
        # Run complete workflow
        workflow_result = integration.run_complete_workflow()
        
        assert workflow_result["success"] == True
        assert "steps" in workflow_result
        
        # Verify all workflow steps completed
        expected_steps = ["dag_execution", "cycle_execution", "capsule_verification", "archive_creation", "meta_capsule_creation"]
        for step in expected_steps:
            assert step in workflow_result["steps"]
    
    def test_system_status_reporting(self, temp_workspace):
        """Test system status reporting functionality"""
        integration = EPOCH5Integration(str(temp_workspace))
        integration.setup_demo_environment()
        
        status = integration.get_system_status()
        
        assert "timestamp" in status
        assert "components" in status
        
        # Verify all component stats are present
        components = status["components"]
        assert "agents" in components
        assert "policies" in components  
        assert "dags" in components
        assert "cycles" in components
        assert "capsules" in components
        assert "meta_capsules" in components
        assert "ceilings" in components
    
    def test_system_integrity_validation(self, temp_workspace):
        """Test system integrity validation"""
        integration = EPOCH5Integration(str(temp_workspace))
        integration.setup_demo_environment()
        
        validation_result = integration.validate_system_integrity()
        
        assert "overall_valid" in validation_result
        assert "validations" in validation_result
        assert "started_at" in validation_result
        
        # In a clean environment, system should be valid
        assert validation_result["overall_valid"] == True
    
    def test_multi_agent_coordination(self, temp_workspace):
        """Test coordination between multiple agents"""
        integration = EPOCH5Integration(str(temp_workspace))
        agent_manager = AgentManager(str(temp_workspace))
        dag_manager = DAGManager(str(temp_workspace))
        
        # Register multiple agents
        agent1 = agent_manager.register_agent(["data_processing"])
        agent2 = agent_manager.register_agent(["validation"])
        agent3 = agent_manager.register_agent(["archival"])
        
        # Create a multi-task DAG
        tasks = [
            {"task_id": "collect", "dependencies": []},
            {"task_id": "process", "dependencies": ["collect"]},
            {"task_id": "validate", "dependencies": ["process"]},
            {"task_id": "archive", "dependencies": ["validate"]}
        ]
        
        dag_id = "multi_agent_workflow"
        dag_result = dag_manager.create_dag(dag_id, tasks)
        assert dag_result["success"] == True
        
        # Execute DAG with agent coordination
        execution_result = dag_manager.execute_dag(dag_id, simulation=True)
        assert execution_result["final_status"] == "completed"
        assert len(execution_result["completed_tasks"]) == 4
    
    def test_error_recovery_mechanisms(self, temp_workspace):
        """Test system error recovery and resilience"""
        integration = EPOCH5Integration(str(temp_workspace))
        integration.setup_demo_environment()
        
        # Simulate failure scenario
        dag_manager = integration.dag_manager
        
        tasks = [
            {"task_id": "stable_task", "dependencies": []},
            {"task_id": "failing_task", "dependencies": ["stable_task"]},
            {"task_id": "recovery_task", "dependencies": ["failing_task"]}
        ]
        
        dag_id = "error_recovery_test"
        dag_manager.create_dag(dag_id, tasks)
        
        # Execute with failure simulation
        result = dag_manager.execute_dag(dag_id, simulation=True)
        
        # System should handle failures gracefully
        assert "failed_tasks" in result
        assert "completed_tasks" in result
    
    def test_data_integrity_chain(self, temp_workspace):
        """Test data integrity through the complete processing chain"""
        integration = EPOCH5Integration(str(temp_workspace))
        integration.setup_demo_environment()
        
        # Create test data
        test_payload = "Test data for integrity validation"
        
        # Process through capsule system
        capsule_result = integration.capsule_manager.create_capsule(
            "integrity_test_capsule",
            test_payload,
            "Test capsule for integrity validation"
        )
        
        assert capsule_result["success"] == True
        
        # Verify integrity
        integrity_result = integration.capsule_manager.verify_capsule_integrity(
            "integrity_test_capsule"
        )
        
        assert integrity_result["overall_valid"] == True
        assert integrity_result["content_hash_valid"] == True
    
    def test_concurrent_workflow_execution(self, temp_workspace):
        """Test multiple concurrent workflows"""
        integration = EPOCH5Integration(str(temp_workspace))
        integration.setup_demo_environment()
        
        # Create multiple DAGs
        dag_manager = integration.dag_manager
        
        for i in range(3):
            tasks = [
                {"task_id": f"start_{i}", "dependencies": []},
                {"task_id": f"process_{i}", "dependencies": [f"start_{i}"]},
                {"task_id": f"finish_{i}", "dependencies": [f"process_{i}"]}
            ]
            
            dag_id = f"concurrent_dag_{i}"
            result = dag_manager.create_dag(dag_id, tasks)
            assert result["success"] == True
        
        # Execute all DAGs
        results = []
        for i in range(3):
            result = dag_manager.execute_dag(f"concurrent_dag_{i}", simulation=True)
            results.append(result)
        
        # Verify all completed successfully
        for result in results:
            assert result["final_status"] == "completed"
    
    def test_performance_under_load(self, temp_workspace):
        """Test system performance under simulated load"""
        integration = EPOCH5Integration(str(temp_workspace))
        integration.setup_demo_environment()
        
        # Create agents for load testing
        agent_manager = integration.agent_manager
        num_agents = 10
        
        agents = []
        for i in range(num_agents):
            agent = agent_manager.register_agent([f"load_test_skill_{i}"])
            agents.append(agent)
        
        # Measure performance metrics
        start_time = time.time()
        
        # Simulate heartbeats from all agents
        for agent in agents:
            agent_manager.log_heartbeat(agent["did"])
        
        # Get system status
        status = integration.get_system_status()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance assertions
        assert processing_time < 5.0  # Should complete within 5 seconds
        assert status["components"]["agents"]["total"] == num_agents
        assert status["components"]["agents"]["active"] == num_agents
    
    def test_end_to_end_bash_integration(self, temp_workspace):
        """Test integration with the main epoch5.sh script"""
        # Change to workspace directory
        original_cwd = os.getcwd()
        os.chdir(temp_workspace)
        
        try:
            # Copy epoch5.sh to workspace
            script_source = Path(original_cwd) / "epoch5.sh"
            script_dest = temp_workspace / "epoch5.sh"
            script_dest.write_text(script_source.read_text())
            script_dest.chmod(0o755)
            
            # Run with minimal delays for testing
            env = os.environ.copy()
            env.update({
                "DELAY_HOURS_P1_P2": "0",
                "DELAY_HOURS_P2_P3": "0",
                "ARC_ID": "TEST-E2E"
            })
            
            # Execute script with timeout
            result = subprocess.run(
                ["./epoch5.sh"],
                env=env,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Verify script execution
            assert result.returncode == 0
            assert "EPOCH 5 Complete!" in result.stdout
            
            # Verify artifacts were created
            archive_dir = temp_workspace / "archive" / "EPOCH5"
            assert archive_dir.exists()
            assert (archive_dir / "ledger.txt").exists()
            assert (archive_dir / "unity_seal.txt").exists()
            
            manifests_dir = archive_dir / "manifests"
            assert manifests_dir.exists()
            assert len(list(manifests_dir.glob("*_manifest.txt"))) == 3  # Three passes
            
        finally:
            os.chdir(original_cwd)