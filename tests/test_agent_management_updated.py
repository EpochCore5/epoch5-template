"""
Tests for agent management functionality
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from agent_management import AgentManager, main
except ImportError as e:
    pytest.skip(
        f"Could not import agent_management module: {e}", allow_module_level=True
    )


class TestAgentManager:
    """Test cases for AgentManager class"""

    @pytest.fixture
    def agent_manager(self, temp_dir):
        """Create an AgentManager instance for testing"""
        with patch('agent_management.SECURITY_SYSTEM_AVAILABLE', True), \
             patch('agent_management.EpochAudit', MagicMock()):
            manager = AgentManager(base_dir=temp_dir)
            if hasattr(manager, 'audit_system'):
                manager.audit_system.enforce_ceiling = MagicMock(
                    return_value={"capped": False, "final_value": 0.5}
                )
                manager.audit_system.log_event = MagicMock()
            return manager

    def test_initialization(self, agent_manager):
        """Test that AgentManager initializes correctly"""
        assert agent_manager is not None
        assert isinstance(agent_manager.base_dir, Path)
        assert agent_manager.agents_dir.exists()
        assert agent_manager.registry_file.exists() is False
        assert agent_manager.audit_system is not None

    def test_timestamp(self, agent_manager):
        """Test timestamp generation"""
        timestamp = agent_manager.timestamp()
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format includes T between date and time
        assert "Z" in timestamp  # UTC timezone ends with Z

    def test_sha256(self, agent_manager):
        """Test SHA256 hash generation"""
        test_data = "test data for hashing"
        hash_result = agent_manager.sha256(test_data)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 hash is 64 hex chars
        assert all(c in "0123456789abcdef" for c in hash_result)

    def test_generate_did(self, agent_manager):
        """Test DID generation"""
        did = agent_manager.generate_did("test_agent")
        
        assert isinstance(did, str)
        assert did.startswith("did:epoch5:test_agent:")
        assert len(did) > 20  # Reasonable length check

        # Test with default agent_type
        default_did = agent_manager.generate_did()
        assert default_did.startswith("did:epoch5:agent:")

    def test_create_agent(self, agent_manager):
        """Test agent creation"""
        skills = ["data_analysis", "encryption"]
        agent = agent_manager.create_agent(skills)

        assert isinstance(agent, dict)
        assert "did" in agent
        assert "skills" in agent
        assert agent["skills"] == skills
        assert agent["reliability_score"] == 1.0
        assert agent["average_latency"] == 0.0
        assert agent["total_tasks"] == 0
        assert agent["successful_tasks"] == 0
        assert "last_heartbeat" in agent
        assert agent["status"] == "active"
        assert "metadata" in agent
        assert "creation_hash" in agent["metadata"]

    def test_load_registry(self, agent_manager):
        """Test loading registry"""
        # Test with non-existent registry
        registry = agent_manager.load_registry()
        assert isinstance(registry, dict)
        assert "agents" in registry
        assert len(registry["agents"]) == 0
        assert "last_updated" in registry

        # Create registry file and test loading
        test_registry = {
            "agents": {
                "did:epoch5:test1": {"did": "did:epoch5:test1", "skills": ["test"]},
                "did:epoch5:test2": {"did": "did:epoch5:test2", "skills": ["test"]}
            },
            "last_updated": agent_manager.timestamp()
        }
        
        with open(agent_manager.registry_file, "w") as f:
            json.dump(test_registry, f)
            
        loaded_registry = agent_manager.load_registry()
        assert len(loaded_registry["agents"]) == 2
        assert "did:epoch5:test1" in loaded_registry["agents"]
        assert "did:epoch5:test2" in loaded_registry["agents"]

    def test_save_registry(self, agent_manager):
        """Test saving registry"""
        test_registry = {
            "agents": {
                "did:epoch5:test1": {"did": "did:epoch5:test1", "skills": ["test"]}
            }
        }
        
        agent_manager.save_registry(test_registry)
        
        # Verify file was created
        assert agent_manager.registry_file.exists()
        
        # Verify content
        with open(agent_manager.registry_file) as f:
            loaded_data = json.load(f)
            assert "agents" in loaded_data
            assert "did:epoch5:test1" in loaded_data["agents"]
            assert "last_updated" in loaded_data

    def test_register_agent(self, agent_manager):
        """Test agent registration"""
        skills = ["monitoring", "validation"]
        agent = agent_manager.create_agent(skills)

        result = agent_manager.register_agent(agent)
        assert result is True

        # Verify agent is in registry
        registry = agent_manager.load_registry()
        assert agent["did"] in registry["agents"]
        
        # Verify audit logging
        if agent_manager.audit_system:
            assert agent_manager.audit_system.log_event.called

    def test_get_agent(self, agent_manager):
        """Test agent retrieval"""
        skills = ["testing"]
        agent = agent_manager.create_agent(skills)
        agent_manager.register_agent(agent)

        retrieved_agent = agent_manager.get_agent(agent["did"])
        assert retrieved_agent is not None
        assert retrieved_agent["did"] == agent["did"]
        assert retrieved_agent["skills"] == agent["skills"]
        
        # Test non-existent agent
        assert agent_manager.get_agent("did:epoch5:nonexistent") is None

    def test_update_agent_stats(self, agent_manager):
        """Test updating agent stats"""
        skills = ["scoring"]
        agent = agent_manager.create_agent(skills)
        agent_manager.register_agent(agent)

        original_score = agent["reliability_score"]
        original_latency = agent["average_latency"]

        # Test successful task
        result = agent_manager.update_agent_stats(
            agent["did"], True, 0.5  # success=True, latency=0.5
        )
        assert result is True

        updated_agent = agent_manager.get_agent(agent["did"])
        assert updated_agent["total_tasks"] == 1
        assert updated_agent["successful_tasks"] == 1
        assert updated_agent["reliability_score"] == 1.0
        assert updated_agent["average_latency"] > original_latency
        
        # Test failed task
        agent_manager.update_agent_stats(agent["did"], False, 0.8)
        updated_agent = agent_manager.get_agent(agent["did"])
        assert updated_agent["total_tasks"] == 2
        assert updated_agent["successful_tasks"] == 1
        assert updated_agent["reliability_score"] == 0.5  # 1 success / 2 total
        
        # Test with security audit ceiling enforcement
        if agent_manager.audit_system:
            agent_manager.audit_system.enforce_ceiling.return_value = {
                "capped": True, "final_value": 0.3
            }
            
            agent_manager.update_agent_stats(agent["did"], True, 1.0)
            updated_agent = agent_manager.get_agent(agent["did"])
            # The latency would be capped at 0.3 and factor into the moving average
        
        # Test updating non-existent agent
        result = agent_manager.update_agent_stats("did:epoch5:nonexistent", True, 1.0)
        assert result is False

    def test_log_heartbeat(self, agent_manager):
        """Test logging heartbeat"""
        skills = ["heartbeat_test"]
        agent = agent_manager.create_agent(skills)
        agent_manager.register_agent(agent)
        
        original_heartbeat = agent["last_heartbeat"]
        
        # Wait briefly to ensure timestamp changes
        import time
        time.sleep(0.1)
        
        # Log heartbeat
        agent_manager.log_heartbeat(agent["did"], "TEST_STATUS")
        
        # Verify heartbeat file exists
        assert agent_manager.heartbeat_file.exists()
        
        # Verify last heartbeat was updated in registry
        updated_agent = agent_manager.get_agent(agent["did"])
        assert updated_agent["last_heartbeat"] != original_heartbeat

    def test_detect_anomaly(self, agent_manager):
        """Test anomaly detection"""
        skills = ["anomaly_test"]
        agent = agent_manager.create_agent(skills)
        
        # Detect anomaly
        anomaly = agent_manager.detect_anomaly(
            agent["did"], 
            "TEST_ANOMALY",
            "Test anomaly details"
        )
        
        # Verify anomaly structure
        assert isinstance(anomaly, dict)
        assert "timestamp" in anomaly
        assert "did" in anomaly
        assert anomaly["did"] == agent["did"]
        assert anomaly["type"] == "TEST_ANOMALY"
        assert anomaly["details"] == "Test anomaly details"
        assert "hash" in anomaly
        
        # Verify anomaly file exists
        assert agent_manager.anomalies_file.exists()
        
        # Verify audit logging if available
        if agent_manager.audit_system:
            audit_calls = agent_manager.audit_system.log_event.call_args_list
            anomaly_calls = [call for call in audit_calls if "agent_anomaly" in str(call)]
            assert len(anomaly_calls) > 0

    def test_get_active_agents(self, agent_manager):
        """Test getting active agents"""
        # Create active agents
        active_agents = []
        for i in range(3):
            agent = agent_manager.create_agent([f"skill_{i}"])
            agent_manager.register_agent(agent)
            active_agents.append(agent)
            
        # Create inactive agent
        inactive_agent = agent_manager.create_agent(["inactive_skill"])
        inactive_agent["status"] = "inactive"
        agent_manager.register_agent(inactive_agent)
        
        # Get active agents
        agents = agent_manager.get_active_agents()
        
        # Verify all active agents are included
        assert len(agents) == 3
        for agent in agents:
            assert agent["status"] == "active"
            
        # Verify inactive agent is not included
        inactive_dids = [a["did"] for a in agents if a["did"] == inactive_agent["did"]]
        assert len(inactive_dids) == 0

    def test_get_agents_by_skill(self, agent_manager):
        """Test filtering agents by skill"""
        # Create agents with different skills
        skills_sets = [
            ["data_analysis", "encryption"],
            ["data_analysis", "monitoring"],
            ["encryption", "validation"],
        ]

        for skills in skills_sets:
            agent = agent_manager.create_agent(skills)
            agent_manager.register_agent(agent)

        # Create inactive agent with target skill
        inactive_agent = agent_manager.create_agent(["data_analysis"])
        inactive_agent["status"] = "inactive"
        agent_manager.register_agent(inactive_agent)

        # Test filtering
        data_analysts = agent_manager.get_agents_by_skill("data_analysis")
        assert len(data_analysts) == 2  # Should exclude the inactive one

        encryptors = agent_manager.get_agents_by_skill("encryption")
        assert len(encryptors) == 2

        validators = agent_manager.get_agents_by_skill("validation")
        assert len(validators) == 1
        
        # Test non-existent skill
        nonexistent = agent_manager.get_agents_by_skill("nonexistent_skill")
        assert len(nonexistent) == 0


def test_main_function():
    """Test the main CLI function"""
    
    # Test create agent command
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('agent_management.AgentManager') as MockAgentManager, \
         patch('builtins.print') as mock_print:
        
        # Setup args for create
        mock_args.return_value.create = ["skill1", "skill2"]
        mock_args.return_value.list = False
        mock_args.return_value.heartbeat = None
        mock_args.return_value.anomaly = None
        
        # Setup mock manager
        mock_instance = MockAgentManager.return_value
        mock_instance.create_agent.return_value = {
            "did": "did:epoch5:test",
            "skills": ["skill1", "skill2"]
        }
        
        # Call main
        main()
        
        # Verify manager was created
        MockAgentManager.assert_called_once()
        
        # Verify agent was created and registered
        mock_instance.create_agent.assert_called_once_with(["skill1", "skill2"])
        mock_instance.register_agent.assert_called_once()
        
        # Verify output was printed
        assert mock_print.called
    
    # Test list agents command
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('agent_management.AgentManager') as MockAgentManager, \
         patch('builtins.print') as mock_print:
        
        # Setup args for list
        mock_args.return_value.create = None
        mock_args.return_value.list = True
        mock_args.return_value.heartbeat = None
        mock_args.return_value.anomaly = None
        
        # Setup mock manager
        mock_instance = MockAgentManager.return_value
        mock_instance.load_registry.return_value = {
            "agents": {
                "did:epoch5:test1": {
                    "did": "did:epoch5:test1",
                    "skills": ["skill1"],
                    "reliability_score": 0.95
                }
            }
        }
        
        # Call main
        main()
        
        # Verify registry was loaded
        mock_instance.load_registry.assert_called_once()
        
        # Verify output was printed
        assert mock_print.called
    
    # Test heartbeat command
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('agent_management.AgentManager') as MockAgentManager, \
         patch('builtins.print') as mock_print:
        
        # Setup args for heartbeat
        mock_args.return_value.create = None
        mock_args.return_value.list = False
        mock_args.return_value.heartbeat = "did:epoch5:test"
        mock_args.return_value.anomaly = None
        
        # Setup mock manager
        mock_instance = MockAgentManager.return_value
        
        # Call main
        main()
        
        # Verify heartbeat was logged
        mock_instance.log_heartbeat.assert_called_once_with("did:epoch5:test")
        
        # Verify output was printed
        assert mock_print.called
    
    # Test anomaly command
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('agent_management.AgentManager') as MockAgentManager, \
         patch('builtins.print') as mock_print:
        
        # Setup args for anomaly
        mock_args.return_value.create = None
        mock_args.return_value.list = False
        mock_args.return_value.heartbeat = None
        mock_args.return_value.anomaly = ["did:epoch5:test", "TEST_ANOMALY", "Test details"]
        
        # Setup mock manager
        mock_instance = MockAgentManager.return_value
        mock_instance.detect_anomaly.return_value = {
            "hash": "test_hash_value"
        }
        
        # Call main
        main()
        
        # Verify anomaly was detected
        mock_instance.detect_anomaly.assert_called_once_with(
            "did:epoch5:test", "TEST_ANOMALY", "Test details"
        )
        
        # Verify output was printed
        assert mock_print.called
    
    # Test no arguments/help
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('agent_management.AgentManager') as MockAgentManager, \
         patch('argparse.ArgumentParser.print_help') as mock_help:
        
        # Setup args for no command
        mock_args.return_value.create = None
        mock_args.return_value.list = False
        mock_args.return_value.heartbeat = None
        mock_args.return_value.anomaly = None
        
        # Call main
        main()
        
        # Verify help was printed
        mock_help.assert_called_once()
