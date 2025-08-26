#!/usr/bin/env python3
"""
Unit tests for agent management functionality
"""

import json
import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_management import AgentManager
from tests.conftest import TestHelpers

class TestAgentManager:
    """Test cases for AgentManager class"""
    
    def test_agent_manager_initialization(self, temp_workspace):
        """Test AgentManager initializes correctly"""
        manager = AgentManager(str(temp_workspace))
        assert str(manager.base_dir) == str(temp_workspace)
        assert Path(manager.registry_file).parent.exists()
    
    def test_generate_did(self, temp_workspace):
        """Test DID generation"""
        manager = AgentManager(str(temp_workspace))
        
        did = manager.generate_did("test_agent")
        assert did.startswith("did:epoch5:test_agent:")
        assert len(did.split(":")) == 4
        
        # Generate another DID and ensure uniqueness
        did2 = manager.generate_did("test_agent")
        assert did != did2
    
    def test_register_agent(self, temp_workspace, sample_agent_data):
        """Test agent registration"""
        manager = AgentManager(str(temp_workspace))
        
        result = manager.register_agent(
            sample_agent_data["skills"],
            agent_type="test_agent"
        )
        
        assert "did" in result
        assert "created_at" in result
        assert result["skills"] == sample_agent_data["skills"]
        assert result["status"] == "active"
        
        # Verify agent is in registry
        registry = manager.load_registry()
        assert result["did"] in registry["agents"]
    
    def test_update_reliability_score(self, temp_workspace, sample_agent_data):
        """Test reliability score updates"""
        manager = AgentManager(str(temp_workspace))
        
        # Register agent first
        agent = manager.register_agent(sample_agent_data["skills"])
        did = agent["did"]
        
        # Update reliability score
        manager.update_reliability_score(did, 0.85)
        
        registry = manager.load_registry()
        assert registry["agents"][did]["reliability_score"] == 0.85
    
    def test_log_heartbeat(self, temp_workspace):
        """Test heartbeat logging"""
        manager = AgentManager(str(temp_workspace))
        
        # Register agent
        agent = manager.register_agent(["test_skill"])
        did = agent["did"]
        
        # Log heartbeat
        manager.log_heartbeat(did)
        
        # Verify heartbeat file exists and contains entry
        assert Path(manager.heartbeat_file).exists()
        heartbeat_content = Path(manager.heartbeat_file).read_text()
        assert did in heartbeat_content
        assert "HEARTBEAT" in heartbeat_content
    
    def test_detect_anomaly(self, temp_workspace):
        """Test anomaly detection logging"""
        manager = AgentManager(str(temp_workspace))
        
        # Register agent
        agent = manager.register_agent(["test_skill"])
        did = agent["did"]
        
        # Log anomaly
        anomaly = manager.detect_anomaly(
            did, 
            "performance_degradation", 
            "Response time exceeded threshold"
        )
        
        assert anomaly["did"] == did
        assert anomaly["type"] == "performance_degradation"
        assert "hash" in anomaly
        
        # Verify anomaly file exists
        assert Path(manager.anomalies_file).exists()
    
    def test_get_active_agents(self, temp_workspace):
        """Test getting active agents"""
        manager = AgentManager(str(temp_workspace))
        
        # Register multiple agents
        agent1 = manager.register_agent(["skill1"])
        agent2 = manager.register_agent(["skill2"])
        
        active_agents = manager.get_active_agents()
        
        assert len(active_agents) == 2
        dids = [agent["did"] for agent in active_agents]
        assert agent1["did"] in dids
        assert agent2["did"] in dids
    
    def test_registry_persistence(self, temp_workspace):
        """Test registry data persistence"""
        manager = AgentManager(str(temp_workspace))
        
        # Register agent
        agent = manager.register_agent(["persistent_skill"])
        
        # Create new manager instance (simulates restart)
        manager2 = AgentManager(str(temp_workspace))
        registry = manager2.load_registry()
        
        # Verify agent persisted
        assert agent["did"] in registry["agents"]
        assert registry["agents"][agent["did"]]["skills"] == ["persistent_skill"]
    
    def test_agent_validation(self, temp_workspace):
        """Test agent data validation"""
        manager = AgentManager(str(temp_workspace))
        
        # Test with invalid skills (empty list)
        with pytest.raises((ValueError, TypeError)):
            manager.register_agent([])
        
        # Test with invalid agent type
        agent = manager.register_agent(["valid_skill"], agent_type="")
        # Should still work but use default type
        assert "did:epoch5:agent:" in agent["did"]
    
    def test_concurrent_operations(self, temp_workspace):
        """Test thread safety of concurrent operations"""
        manager = AgentManager(str(temp_workspace))
        
        # Simulate concurrent registrations
        agents = []
        for i in range(5):
            agent = manager.register_agent([f"skill_{i}"])
            agents.append(agent)
        
        # Verify all agents registered correctly
        registry = manager.load_registry()
        assert len(registry["agents"]) == 5
        
        for agent in agents:
            assert agent["did"] in registry["agents"]