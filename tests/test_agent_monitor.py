"""
Tests for agent monitoring functionality
"""

import pytest
import json
import sys
import os
import time
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from agent_monitor import AgentMonitor, AgentMessage
except ImportError as e:
    pytest.skip(
        f"Could not import agent_monitor module: {e}", allow_module_level=True
    )


class TestAgentMessage:
    """Test cases for AgentMessage class"""
    
    def test_initialization(self):
        """Test that AgentMessage initializes correctly"""
        message = AgentMessage(
            message_type="TEST",
            content="Test message content",
            sender="test_agent",
            priority=1
        )
        
        assert message.message_type == "TEST"
        assert message.content == "Test message content"
        assert message.sender == "test_agent"
        assert message.priority == 1
        assert message.message_id is not None
        assert message.timestamp is not None
        assert message.expires_at is not None
        
    def test_to_dict(self):
        """Test conversion to dictionary"""
        message = AgentMessage(
            message_type="TEST",
            content="Test message content",
            sender="test_agent",
            priority=1
        )
        
        message_dict = message.to_dict()
        
        assert isinstance(message_dict, dict)
        assert message_dict["message_type"] == "TEST"
        assert message_dict["content"] == "Test message content"
        assert message_dict["sender"] == "test_agent"
        assert message_dict["priority"] == 1
        assert message_dict["message_id"] == message.message_id
        assert message_dict["timestamp"] == message.timestamp
        assert message_dict["expires_at"] == message.expires_at
        
    def test_from_dict(self):
        """Test creation from dictionary"""
        original = AgentMessage(
            message_type="TEST",
            content="Test message content",
            sender="test_agent",
            priority=1
        )
        
        message_dict = original.to_dict()
        recreated = AgentMessage.from_dict(message_dict)
        
        assert recreated.message_type == original.message_type
        assert recreated.content == original.content
        assert recreated.sender == original.sender
        assert recreated.priority == original.priority
        assert recreated.message_id == original.message_id
        assert recreated.timestamp == original.timestamp
        assert recreated.expires_at == original.expires_at
        
    def test_is_expired(self):
        """Test expiration check"""
        # Create a message that's not expired
        future_message = AgentMessage(
            message_type="TEST",
            content="Test message content",
            sender="test_agent",
            priority=1,
            ttl=3600  # 1 hour TTL
        )
        
        assert future_message.is_expired() is False
        
        # Create a message that's expired
        past_message = AgentMessage(
            message_type="TEST",
            content="Test message content",
            sender="test_agent",
            priority=1,
            ttl=-10  # Negative TTL to ensure it's expired
        )
        
        assert past_message.is_expired() is True


class TestAgentMonitor:
    """Test cases for AgentMonitor class"""
    
    @pytest.fixture
    def agent_monitor(self, tmp_path):
        """Create an AgentMonitor instance for testing"""
        # Mock the AgentManager
        with patch('agent_monitor.AgentManager') as mock_agent_manager:
            # Configure the mock
            monitor = AgentMonitor(base_dir=str(tmp_path))
            yield monitor
    
    def test_initialization(self, agent_monitor):
        """Test that AgentMonitor initializes correctly"""
        assert agent_monitor is not None
        assert isinstance(agent_monitor.base_dir, Path)
        assert agent_monitor.messages_dir.exists()
        assert agent_monitor.dashboard_data_dir.exists()
        assert agent_monitor.outbox_path.exists()
        assert agent_monitor.inbox_path.exists()
        assert isinstance(agent_monitor.active_agents, dict)
        assert isinstance(agent_monitor.performance_history, dict)
        
    def test_register_agent(self, agent_monitor):
        """Test agent registration"""
        with patch.object(agent_monitor.agent_manager, 'register_agent', return_value=True):
            result = agent_monitor.register_agent(
                agent_did="did:epoch5:test1",
                agent_type="test_agent",
                endpoint="http://localhost:8080",
                skills=["test"]
            )
            
            assert result is True
            assert "did:epoch5:test1" in agent_monitor.active_agents
            assert agent_monitor.active_agents["did:epoch5:test1"]["agent_type"] == "test_agent"
            assert agent_monitor.active_agents["did:epoch5:test1"]["endpoint"] == "http://localhost:8080"
            assert "test" in agent_monitor.active_agents["did:epoch5:test1"]["skills"]
            
    def test_unregister_agent(self, agent_monitor):
        """Test agent unregistration"""
        # First register an agent
        agent_monitor.active_agents["did:epoch5:test1"] = {
            "agent_type": "test_agent",
            "endpoint": "http://localhost:8080",
            "skills": ["test"],
            "status": "active",
            "last_seen": datetime.now().isoformat()
        }
        
        # Then unregister it
        result = agent_monitor.unregister_agent("did:epoch5:test1")
        
        assert result is True
        assert "did:epoch5:test1" not in agent_monitor.active_agents
        
    def test_send_message(self, agent_monitor):
        """Test sending messages to agents"""
        with patch('pathlib.Path.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump:
            
            message = AgentMessage(
                message_type="TEST",
                content="Test message content",
                sender="monitor",
                priority=1
            )
            
            result = agent_monitor.send_message("did:epoch5:test1", message)
            
            assert result is True
            mock_file.assert_called_once()
            mock_json_dump.assert_called_once()
            
    def test_broadcast_message(self, agent_monitor):
        """Test broadcasting messages to multiple agents"""
        with patch.object(agent_monitor, 'send_message', return_value=True) as mock_send:
            # Register some agents
            agent_monitor.active_agents = {
                "did:epoch5:test1": {"status": "active"},
                "did:epoch5:test2": {"status": "active"},
                "did:epoch5:test3": {"status": "inactive"}
            }
            
            message = AgentMessage(
                message_type="BROADCAST",
                content="Broadcast test",
                sender="monitor",
                priority=2
            )
            
            results = agent_monitor.broadcast_message(message)
            
            # Should be sent to 2 active agents
            assert len(results) == 2
            assert all(results.values())
            assert mock_send.call_count == 2
    
    def test_process_incoming_messages(self, agent_monitor):
        """Test processing incoming messages"""
        # Create mock message files
        mock_files = {
            "msg1.json": json.dumps({
                "message_type": "STATUS",
                "content": "Status report",
                "sender": "did:epoch5:test1",
                "priority": 1,
                "message_id": "test_id_1",
                "timestamp": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
            }),
            "msg2.json": json.dumps({
                "message_type": "ALERT",
                "content": "Alert message",
                "sender": "did:epoch5:test2",
                "priority": 3,
                "message_id": "test_id_2",
                "timestamp": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat()
            })
        }
        
        with patch('os.listdir', return_value=list(mock_files.keys())), \
             patch('pathlib.Path.open', side_effect=lambda *args, **kwargs: mock_open(read_data=mock_files[args[0].name]).return_value):
            
            messages = agent_monitor.process_incoming_messages()
            
            assert len(messages) == 2
            assert messages[0].message_type == "STATUS"
            assert messages[1].message_type == "ALERT"
    
    def test_update_agent_status(self, agent_monitor):
        """Test updating agent status"""
        # First register an agent
        agent_monitor.active_agents["did:epoch5:test1"] = {
            "agent_type": "test_agent",
            "endpoint": "http://localhost:8080",
            "skills": ["test"],
            "status": "active",
            "last_seen": (datetime.now() - timedelta(minutes=5)).isoformat()
        }
        
        # Update its status
        agent_monitor.update_agent_status("did:epoch5:test1", "busy")
        
        assert agent_monitor.active_agents["did:epoch5:test1"]["status"] == "busy"
        assert datetime.fromisoformat(agent_monitor.active_agents["did:epoch5:test1"]["last_seen"]) > datetime.now() - timedelta(minutes=1)
        
    def test_check_agent_health(self, agent_monitor):
        """Test checking agent health"""
        # Setup agents with different last_seen times
        now = datetime.now()
        agent_monitor.active_agents = {
            # Active and recently seen
            "did:epoch5:active": {
                "status": "active",
                "last_seen": now.isoformat()
            },
            # Active but not seen recently
            "did:epoch5:stale": {
                "status": "active",
                "last_seen": (now - timedelta(minutes=10)).isoformat()
            },
            # Inactive and not seen recently
            "did:epoch5:inactive": {
                "status": "inactive",
                "last_seen": (now - timedelta(hours=1)).isoformat()
            }
        }
        
        with patch.object(agent_monitor, 'ping_agent', side_effect=lambda did: did == "did:epoch5:active"):
            health_report = agent_monitor.check_agent_health()
            
            assert health_report["total"] == 3
            assert health_report["active"] == 1
            assert health_report["stale"] == 1
            assert health_report["inactive"] == 1
            
            # The stale agent should now be marked inactive
            assert agent_monitor.active_agents["did:epoch5:stale"]["status"] == "inactive"
    
    def test_record_performance_metric(self, agent_monitor):
        """Test recording performance metrics"""
        agent_monitor.record_performance_metric(
            "did:epoch5:test1",
            metric_type="latency",
            value=0.5
        )
        
        assert "did:epoch5:test1" in agent_monitor.performance_history
        assert len(agent_monitor.performance_history["did:epoch5:test1"]) == 1
        assert agent_monitor.performance_history["did:epoch5:test1"][0]["metric_type"] == "latency"
        assert agent_monitor.performance_history["did:epoch5:test1"][0]["value"] == 0.5
        
    def test_get_agent_metrics(self, agent_monitor):
        """Test retrieving agent metrics"""
        # Record some metrics
        agent_monitor.record_performance_metric("did:epoch5:test1", "latency", 0.5)
        agent_monitor.record_performance_metric("did:epoch5:test1", "cpu", 30)
        agent_monitor.record_performance_metric("did:epoch5:test1", "latency", 0.7)
        
        metrics = agent_monitor.get_agent_metrics("did:epoch5:test1")
        
        assert len(metrics) == 3
        assert metrics[0]["metric_type"] == "latency"
        assert metrics[0]["value"] == 0.5
        
        # Test filtering by metric type
        latency_metrics = agent_monitor.get_agent_metrics("did:epoch5:test1", metric_type="latency")
        assert len(latency_metrics) == 2
        assert all(m["metric_type"] == "latency" for m in latency_metrics)
        
    def test_save_and_load_monitoring_data(self, agent_monitor):
        """Test saving and loading monitoring data"""
        # Setup some data
        agent_monitor.active_agents = {
            "did:epoch5:test1": {"status": "active"}
        }
        agent_monitor.performance_history = {
            "did:epoch5:test1": [{"metric_type": "latency", "value": 0.5}]
        }
        
        with patch('pathlib.Path.open', mock_open()) as mock_file, \
             patch('json.dump') as mock_json_dump, \
             patch('json.load', return_value={
                 "active_agents": {"did:epoch5:test1": {"status": "active"}},
                 "performance_history": {"did:epoch5:test1": [{"metric_type": "latency", "value": 0.5}]}
             }):
            
            # Save data
            agent_monitor.save_monitoring_data()
            mock_file.assert_called()
            mock_json_dump.assert_called_once()
            
            # Reset and load data
            agent_monitor.active_agents = {}
            agent_monitor.performance_history = {}
            
            agent_monitor.load_monitoring_data()
            
            assert "did:epoch5:test1" in agent_monitor.active_agents
            assert "did:epoch5:test1" in agent_monitor.performance_history


# Test the main function and CLI functionality
def test_main_function():
    """Test the main CLI function"""
    
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('agent_monitor.AgentMonitor') as MockMonitor:
        
        # Mock instance
        mock_instance = MockMonitor.return_value
        
        # Test status command
        mock_args.return_value.command = "status"
        mock_instance.check_agent_health.return_value = {
            "total": 3, "active": 2, "stale": 0, "inactive": 1
        }
        
        with patch('builtins.print') as mock_print:
            from agent_monitor import main
            main()
            
            mock_instance.check_agent_health.assert_called_once()
            mock_print.assert_called()
            
        # Test broadcast command
        mock_args.return_value.command = "broadcast"
        mock_args.return_value.message = "Test broadcast"
        mock_args.return_value.priority = 2
        mock_instance.broadcast_message.return_value = {"did:epoch5:test1": True}
        
        with patch('builtins.print') as mock_print:
            main()
            
            mock_instance.broadcast_message.assert_called_once()
            mock_print.assert_called()
