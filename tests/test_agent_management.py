"""
Tests for agent management functionality
"""

import pytest
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from agent_management import AgentManager
except ImportError as e:
    pytest.skip(
        f"Could not import agent_management module: {e}", allow_module_level=True
    )


class TestAgentManager:
    """Test cases for AgentManager class"""

    @pytest.fixture
    def agent_manager(self, temp_dir):
        """Create an AgentManager instance for testing"""
        return AgentManager(base_dir=temp_dir)

    def test_initialization(self, agent_manager):
        """Test that AgentManager initializes correctly"""
        assert agent_manager is not None
        assert hasattr(agent_manager, "base_dir")
        assert hasattr(agent_manager, "agents_dir")

    def test_create_agent(self, agent_manager):
        """Test agent creation"""
        skills = ["data_analysis", "encryption"]
        agent = agent_manager.create_agent(skills)

        assert isinstance(agent, dict)
        assert "did" in agent
        assert "skills" in agent
        assert agent["skills"] == skills
        assert "reliability_score" in agent
        assert "average_latency" in agent
        assert "created_at" in agent

        # Verify DID format
        assert agent["did"].startswith("did:epoch5:")

    def test_register_agent(self, agent_manager):
        """Test agent registration"""
        skills = ["monitoring", "validation"]
        agent = agent_manager.create_agent(skills)

        result = agent_manager.register_agent(agent)
        assert result is True

        # Verify agent is in registry
        registry = agent_manager.load_registry()
        assert agent["did"] in registry["agents"]

    def test_get_agent(self, agent_manager):
        """Test agent retrieval"""
        skills = ["testing"]
        agent = agent_manager.create_agent(skills)
        agent_manager.register_agent(agent)

        retrieved_agent = agent_manager.get_agent(agent["did"])
        assert retrieved_agent is not None
        assert retrieved_agent["did"] == agent["did"]
        assert retrieved_agent["skills"] == agent["skills"]

    def test_update_reliability_score(self, agent_manager):
        """Test agent stats updates"""
        skills = ["scoring"]
        agent = agent_manager.create_agent(skills)
        agent_manager.register_agent(agent)

        original_score = agent["reliability_score"]

        # Use the actual method available: update_agent_stats
        result = agent_manager.update_agent_stats(
            agent["did"], success=True, latency=50.0
        )
        assert result is True

        updated_agent = agent_manager.get_agent(agent["did"])
        # Reliability score should be 1.0 since we passed success=True and it's the first task
        assert updated_agent["reliability_score"] == 1.0
        assert updated_agent["total_tasks"] == 1
        assert updated_agent["successful_tasks"] == 1

    def test_list_agents(self, agent_manager):
        """Test agent listing"""
        # Create multiple agents
        for i in range(3):
            skills = [f"skill_{i}"]
            agent = agent_manager.create_agent(skills)
            agent_manager.register_agent(agent)

        # Use get_active_agents which is the available method
        agents = agent_manager.get_active_agents()
        assert len(agents) >= 3  # May have more from other tests
        assert all("did" in agent for agent in agents)

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

        # Test filtering
        data_analysts = agent_manager.get_agents_by_skill("data_analysis")
        assert len(data_analysts) == 2

        encryptors = agent_manager.get_agents_by_skill("encryption")
        assert len(encryptors) == 2

        validators = agent_manager.get_agents_by_skill("validation")
        assert len(validators) == 1

    def test_nonexistent_agent(self, agent_manager):
        """Test operations on nonexistent agents"""
        fake_did = "did:epoch5:nonexistent"

        agent = agent_manager.get_agent(fake_did)
        assert agent is None

        result = agent_manager.update_agent_stats(fake_did, success=False, latency=100.0)
        assert result is False
