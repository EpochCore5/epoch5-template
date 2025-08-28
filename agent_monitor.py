"""
Agent Monitor and Communication Dashboard

This module provides a comprehensive dashboard for monitoring and communicating with all agents 
in the EPOCH5 ecosystem, including StrategyDECK agents.

Features:
- Real-time agent status monitoring
- Agent health metrics visualization
- Command broadcasting to multiple agents
- Detailed agent performance analytics
- Task assignment and management
- Integration with EPOCH5 Agent Management
"""

import os
import json
import time
import threading
import argparse
import logging
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import copy
import csv
import signal
import sys

# Import EPOCH5 components
from agent_management import AgentManager
from strategydeck_agent import StrategyDECKAgent
from strategydeck_integration import StrategyDECKAgentIntegration

try:
    import dash
    from dash import dcc, html, dash_table
    import dash_bootstrap_components as dbc
    from dash.dependencies import Input, Output, State
    import plotly.graph_objs as go
    import plotly.express as px
    import pandas as pd
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent_monitor.log")
    ]
)
logger = logging.getLogger("AgentMonitor")


class AgentMessage:
    """Represents a message that can be sent to agents"""
    
    def __init__(self, 
                message_type: str, 
                content: Dict[str, Any], 
                sender: str = "AgentMonitor",
                priority: str = "normal",
                expires_at: Optional[datetime] = None):
        """
        Initialize a new agent message
        
        Args:
            message_type: Type of message (command, notification, query)
            content: Message content/payload
            sender: Sender identifier
            priority: Message priority (low, normal, high, critical)
            expires_at: Expiration timestamp (optional)
        """
        self.message_id = str(uuid.uuid4())
        self.message_type = message_type
        self.content = content
        self.sender = sender
        self.timestamp = datetime.now().isoformat()
        self.priority = priority
        self.expires_at = expires_at.isoformat() if expires_at else None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "content": self.content,
            "sender": self.sender,
            "timestamp": self.timestamp,
            "priority": self.priority,
            "expires_at": self.expires_at
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        msg = cls(
            message_type=data["message_type"],
            content=data["content"],
            sender=data["sender"],
            priority=data["priority"]
        )
        msg.message_id = data["message_id"]
        msg.timestamp = data["timestamp"]
        msg.expires_at = data["expires_at"]
        return msg


class AgentMonitor:
    """
    Comprehensive agent monitoring and communication system for EPOCH5.
    
    Provides real-time monitoring, messaging, and management for all agents
    in the EPOCH5 ecosystem, including StrategyDECK agents.
    """
    
    def __init__(self, base_dir: str = "./archive/EPOCH5"):
        """
        Initialize the agent monitor
        
        Args:
            base_dir: Base directory for EPOCH5 systems
        """
        self.base_dir = Path(base_dir)
        self.agent_manager = AgentManager(base_dir)
        
        # Create necessary directories
        self.messages_dir = self.base_dir / "messages"
        self.messages_dir.mkdir(parents=True, exist_ok=True)
        
        self.dashboard_data_dir = self.base_dir / "dashboard_data"
        self.dashboard_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Store active agent connections
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        
        # Performance metrics storage
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize the messaging system
        self.outbox_path = self.messages_dir / "outbox"
        self.inbox_path = self.messages_dir / "inbox"
        self.outbox_path.mkdir(exist_ok=True)
        self.inbox_path.mkdir(exist_ok=True)
        
        # Start monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Agent Monitor initialized")
    
    def _monitoring_loop(self):
        """Background thread for continuous agent monitoring"""
        try:
            while self.running:
                try:
                    # Refresh agent statuses from registry
                    self._refresh_agent_statuses()
                    
                    # Check for incoming messages
                    self._process_incoming_messages()
                    
                    # Update performance history
                    self._update_performance_history()
                    
                    # Save dashboard data
                    self._save_dashboard_data()
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    logger.debug(traceback.format_exc())
                
                # Sleep to avoid high CPU usage
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"Fatal error in monitoring thread: {e}")
            logger.error(traceback.format_exc())
    
    def _refresh_agent_statuses(self):
        """Refresh agent statuses from the registry"""
        registry = self.agent_manager.load_registry()
        
        # Update active agents list
        for did, agent_data in registry["agents"].items():
            # Skip inactive agents
            if agent_data["status"] != "active":
                continue
                
            # Calculate time since last heartbeat
            last_heartbeat = datetime.fromisoformat(agent_data["last_heartbeat"].replace("Z", "+00:00"))
            now = datetime.now().astimezone()
            heartbeat_age = (now - last_heartbeat).total_seconds()
            
            # Agent is considered online if heartbeat is recent (last 2 minutes)
            is_online = heartbeat_age < 120
            
            # Update agent status
            if did in self.active_agents:
                self.active_agents[did].update({
                    "agent_data": agent_data,
                    "is_online": is_online,
                    "heartbeat_age": heartbeat_age,
                    "last_checked": datetime.now().isoformat()
                })
            else:
                # Add new agent
                self.active_agents[did] = {
                    "agent_data": agent_data,
                    "is_online": is_online,
                    "heartbeat_age": heartbeat_age,
                    "last_checked": datetime.now().isoformat(),
                    "last_communication": None,
                    "pending_messages": []
                }
    
    def _process_incoming_messages(self):
        """Process incoming messages from agents"""
        for file_path in self.inbox_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    message_data = json.load(f)
                
                # Process message
                self._handle_incoming_message(message_data)
                
                # Archive or delete message after processing
                file_path.unlink()
                
            except Exception as e:
                logger.error(f"Error processing message {file_path}: {e}")
    
    def _handle_incoming_message(self, message_data: Dict[str, Any]):
        """Handle an incoming message from an agent"""
        if "sender" not in message_data or "message_type" not in message_data:
            logger.warning(f"Invalid message format: {message_data}")
            return
            
        sender = message_data["sender"]
        message_type = message_data["message_type"]
        
        # Update last communication timestamp
        if sender in self.active_agents:
            self.active_agents[sender]["last_communication"] = datetime.now().isoformat()
        
        # Handle different message types
        if message_type == "status_update":
            self._handle_status_update(sender, message_data["content"])
        elif message_type == "task_result":
            self._handle_task_result(sender, message_data["content"])
        elif message_type == "error_report":
            self._handle_error_report(sender, message_data["content"])
        elif message_type == "query_response":
            self._handle_query_response(sender, message_data["content"])
        else:
            logger.info(f"Received {message_type} message from {sender}")
    
    def _handle_status_update(self, sender: str, content: Dict[str, Any]):
        """Handle a status update message from an agent"""
        if sender in self.active_agents:
            self.active_agents[sender]["status"] = content
            logger.debug(f"Updated status for agent {sender}")
    
    def _handle_task_result(self, sender: str, content: Dict[str, Any]):
        """Handle a task result message from an agent"""
        logger.info(f"Received task result from {sender}: {content.get('status', 'unknown')}")
        
        # Update agent statistics
        if "execution_time" in content and "status" in content:
            self.agent_manager.update_agent_stats(
                sender,
                success=content["status"] == "success",
                latency=content["execution_time"]
            )
    
    def _handle_error_report(self, sender: str, content: Dict[str, Any]):
        """Handle an error report from an agent"""
        logger.warning(f"Error report from {sender}: {content.get('error_message', 'unknown error')}")
        
        # Log anomaly in agent management system
        self.agent_manager.detect_anomaly(
            sender,
            content.get("error_type", "UNKNOWN_ERROR"),
            content.get("error_message", "No details provided")
        )
    
    def _handle_query_response(self, sender: str, content: Dict[str, Any]):
        """Handle a query response from an agent"""
        logger.info(f"Received query response from {sender}")
        
        # Store query response for later retrieval
        if sender in self.active_agents:
            if "query_responses" not in self.active_agents[sender]:
                self.active_agents[sender]["query_responses"] = []
            
            self.active_agents[sender]["query_responses"].append({
                "timestamp": datetime.now().isoformat(),
                "query_id": content.get("query_id"),
                "response": content.get("response")
            })
    
    def _update_performance_history(self):
        """Update performance history for all active agents"""
        for did, agent in self.active_agents.items():
            if agent["is_online"]:
                # Initialize history for new agents
                if did not in self.performance_history:
                    self.performance_history[did] = []
                
                # Add current metrics to history
                agent_data = agent["agent_data"]
                
                # Only record if we have meaningful data
                if agent_data["total_tasks"] > 0:
                    self.performance_history[did].append({
                        "timestamp": datetime.now().isoformat(),
                        "reliability": agent_data["reliability_score"],
                        "latency": agent_data["average_latency"],
                        "total_tasks": agent_data["total_tasks"],
                        "successful_tasks": agent_data["successful_tasks"]
                    })
                    
                    # Limit history size to avoid memory growth
                    if len(self.performance_history[did]) > 1000:
                        self.performance_history[did] = self.performance_history[did][-1000:]
    
    def _save_dashboard_data(self):
        """Save current data for dashboard visualization"""
        # Save agent status snapshot
        status_data = {
            "timestamp": datetime.now().isoformat(),
            "agents": {}
        }
        
        for did, agent in self.active_agents.items():
            status_data["agents"][did] = {
                "name": agent["agent_data"].get("type", "unknown"),
                "is_online": agent["is_online"],
                "skills": agent["agent_data"].get("skills", []),
                "reliability": agent["agent_data"].get("reliability_score", 0),
                "total_tasks": agent["agent_data"].get("total_tasks", 0),
                "successful_tasks": agent["agent_data"].get("successful_tasks", 0),
                "last_heartbeat_age": agent["heartbeat_age"]
            }
        
        # Save to JSON file
        with open(self.dashboard_data_dir / "agent_status.json", "w") as f:
            json.dump(status_data, f, indent=2)
        
        # Save performance history snapshot (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        performance_data = {}
        
        for did, history in self.performance_history.items():
            # Filter for recent entries
            recent_entries = [
                entry for entry in history 
                if datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")) > cutoff_time
            ]
            
            if recent_entries:
                performance_data[did] = recent_entries
        
        # Save to JSON file
        with open(self.dashboard_data_dir / "performance_history.json", "w") as f:
            json.dump(performance_data, f, indent=2)
    
    def send_message_to_agent(self, did: str, message: AgentMessage) -> bool:
        """
        Send a message to a specific agent
        
        Args:
            did: Agent's decentralized identifier
            message: Message to send
            
        Returns:
            True if message was sent, False otherwise
        """
        if did not in self.active_agents:
            logger.warning(f"Cannot send message to unknown agent: {did}")
            return False
        
        # Convert message to dictionary
        message_dict = message.to_dict()
        
        # Save to outbox
        message_file = self.outbox_path / f"{did}_{message.message_id}.json"
        with open(message_file, "w") as f:
            json.dump(message_dict, f, indent=2)
        
        # Add to pending messages
        self.active_agents[did]["pending_messages"].append(message_dict)
        
        logger.info(f"Message sent to {did}: {message.message_type}")
        return True
    
    def broadcast_message(self, message: AgentMessage, agent_filter: Optional[Dict[str, Any]] = None) -> int:
        """
        Broadcast a message to multiple agents with optional filtering
        
        Args:
            message: Message to broadcast
            agent_filter: Optional filter to select agents (e.g., {"skills": ["strategy_automation"]})
            
        Returns:
            Number of agents the message was sent to
        """
        sent_count = 0
        
        for did, agent in self.active_agents.items():
            # Skip offline agents
            if not agent["is_online"]:
                continue
                
            # Apply filter if provided
            if agent_filter:
                if "skills" in agent_filter:
                    agent_skills = agent["agent_data"].get("skills", [])
                    if not any(skill in agent_skills for skill in agent_filter["skills"]):
                        continue
                
                if "agent_type" in agent_filter:
                    agent_type = agent["agent_data"].get("type", "")
                    if agent_type != agent_filter["agent_type"]:
                        continue
            
            # Send message
            if self.send_message_to_agent(did, message):
                sent_count += 1
        
        logger.info(f"Broadcast message to {sent_count} agents")
        return sent_count
    
    def send_command(self, did: str, command: str, parameters: Dict[str, Any] = None) -> str:
        """
        Send a command to a specific agent
        
        Args:
            did: Agent's decentralized identifier
            command: Command to execute
            parameters: Command parameters
            
        Returns:
            Message ID if command was sent, empty string otherwise
        """
        message = AgentMessage(
            message_type="command",
            content={
                "command": command,
                "parameters": parameters or {}
            },
            priority="high"
        )
        
        if self.send_message_to_agent(did, message):
            return message.message_id
        
        return ""
    
    def broadcast_command(self, command: str, parameters: Dict[str, Any] = None, 
                         agent_filter: Optional[Dict[str, Any]] = None) -> int:
        """
        Broadcast a command to multiple agents
        
        Args:
            command: Command to execute
            parameters: Command parameters
            agent_filter: Optional filter to select agents
            
        Returns:
            Number of agents the command was sent to
        """
        message = AgentMessage(
            message_type="command",
            content={
                "command": command,
                "parameters": parameters or {}
            },
            priority="high"
        )
        
        return self.broadcast_message(message, agent_filter)
    
    def get_agent_status(self, did: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed status for a specific agent
        
        Args:
            did: Agent's decentralized identifier
            
        Returns:
            Agent status or None if agent not found
        """
        if did not in self.active_agents:
            return None
        
        return copy.deepcopy(self.active_agents[did])
    
    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statuses for all agents
        
        Returns:
            Dictionary of agent statuses
        """
        return copy.deepcopy(self.active_agents)
    
    def get_agent_performance_history(self, did: str) -> List[Dict[str, Any]]:
        """
        Get performance history for a specific agent
        
        Args:
            did: Agent's decentralized identifier
            
        Returns:
            List of performance metrics over time
        """
        if did not in self.performance_history:
            return []
        
        return copy.deepcopy(self.performance_history[did])
    
    def assign_task(self, task_data: Dict[str, Any], agent_filter: Dict[str, Any] = None) -> Tuple[str, str]:
        """
        Assign a task to the most suitable agent
        
        Args:
            task_data: Task data/parameters
            agent_filter: Optional filter to select eligible agents
            
        Returns:
            Tuple of (agent DID, message ID) or ("", "") if no suitable agent found
        """
        eligible_agents = []
        
        for did, agent in self.active_agents.items():
            # Skip offline agents
            if not agent["is_online"]:
                continue
                
            # Apply filter if provided
            if agent_filter:
                if "skills" in agent_filter:
                    agent_skills = agent["agent_data"].get("skills", [])
                    if not any(skill in agent_skills for skill in agent_filter["skills"]):
                        continue
                
                if "agent_type" in agent_filter:
                    agent_type = agent["agent_data"].get("type", "")
                    if agent_type != agent_filter["agent_type"]:
                        continue
            
            # Add to eligible agents
            eligible_agents.append((did, agent))
        
        if not eligible_agents:
            logger.warning("No eligible agents found for task assignment")
            return ("", "")
        
        # Find the most reliable agent with capacity
        eligible_agents.sort(key=lambda x: x[1]["agent_data"].get("reliability_score", 0), reverse=True)
        selected_did, _ = eligible_agents[0]
        
        # Create and send task message
        message = AgentMessage(
            message_type="task",
            content=task_data,
            priority="normal"
        )
        
        if self.send_message_to_agent(selected_did, message):
            logger.info(f"Task assigned to agent {selected_did}")
            return (selected_did, message.message_id)
        
        return ("", "")
    
    def query_agent(self, did: str, query_type: str, query_parameters: Dict[str, Any] = None) -> str:
        """
        Send a query to a specific agent
        
        Args:
            did: Agent's decentralized identifier
            query_type: Type of query
            query_parameters: Query parameters
            
        Returns:
            Query ID if query was sent, empty string otherwise
        """
        query_id = str(uuid.uuid4())
        
        message = AgentMessage(
            message_type="query",
            content={
                "query_id": query_id,
                "query_type": query_type,
                "parameters": query_parameters or {}
            },
            priority="normal"
        )
        
        if self.send_message_to_agent(did, message):
            return query_id
        
        return ""
    
    def get_query_response(self, did: str, query_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a response to a previously sent query
        
        Args:
            did: Agent's decentralized identifier
            query_id: Query ID
            
        Returns:
            Query response or None if not found
        """
        if did not in self.active_agents:
            return None
            
        if "query_responses" not in self.active_agents[did]:
            return None
            
        for response in self.active_agents[did]["query_responses"]:
            if response.get("query_id") == query_id:
                return copy.deepcopy(response)
                
        return None
    
    def export_performance_data(self, output_file: str) -> bool:
        """
        Export performance data to CSV
        
        Args:
            output_file: Output file path
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            rows = []
            
            for did, history in self.performance_history.items():
                agent_type = "unknown"
                if did in self.active_agents:
                    agent_type = self.active_agents[did]["agent_data"].get("type", "unknown")
                
                for entry in history:
                    rows.append({
                        "agent_did": did,
                        "agent_type": agent_type,
                        "timestamp": entry["timestamp"],
                        "reliability": entry["reliability"],
                        "latency": entry["latency"],
                        "total_tasks": entry["total_tasks"],
                        "successful_tasks": entry["successful_tasks"]
                    })
            
            if not rows:
                logger.warning("No performance data to export")
                return False
                
            # Write to CSV
            with open(output_file, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
                
            logger.info(f"Exported performance data to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting performance data: {e}")
            return False
    
    def shutdown(self):
        """Gracefully shut down the agent monitor"""
        logger.info("Shutting down Agent Monitor")
        self.running = False
        
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
            
        logger.info("Agent Monitor shutdown complete")


class AgentDashboard:
    """
    Web-based dashboard for agent monitoring and management
    Built with Dash and Plotly for rich visualizations
    """
    
    def __init__(self, agent_monitor: AgentMonitor):
        """
        Initialize the agent dashboard
        
        Args:
            agent_monitor: AgentMonitor instance
        """
        if not DASH_AVAILABLE:
            logger.error("Dash is not installed. Cannot create dashboard.")
            raise ImportError("Dash and its dependencies must be installed to use the dashboard")
            
        self.agent_monitor = agent_monitor
        
        # Initialize Dash app
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )
        
        # Set up layout
        self._setup_layout()
        
        # Set up callbacks
        self._setup_callbacks()
        
        logger.info("Agent Dashboard initialized")
    
    def _setup_layout(self):
        """Set up the dashboard layout"""
        # Main layout with tabs
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("EPOCH5 Agent Monitor", className="display-4 mt-3 mb-4"),
                    html.P("Real-time monitoring and communication system for EPOCH5 agents", className="lead mb-4"),
                ], width=12)
            ]),
            
            dbc.Tabs([
                # Overview Tab
                dbc.Tab([
                    dbc.Row([
                        # Agent Status Cards
                        dbc.Col([
                            html.Div(id="agent-status-cards", className="mt-4"),
                            dcc.Interval(id="interval-status", interval=5000, n_intervals=0)
                        ], width=12)
                    ]),
                    
                    dbc.Row([
                        # Agent Type Distribution
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Agent Type Distribution"),
                                dbc.CardBody([
                                    dcc.Graph(id="agent-type-pie")
                                ])
                            ], className="mt-4")
                        ], width=6),
                        
                        # Reliability Distribution
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Agent Reliability Distribution"),
                                dbc.CardBody([
                                    dcc.Graph(id="reliability-histogram")
                                ])
                            ], className="mt-4")
                        ], width=6)
                    ]),
                    
                    dbc.Row([
                        # Recent Activity Feed
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Recent Activity"),
                                dbc.CardBody([
                                    html.Div(id="activity-feed")
                                ])
                            ], className="mt-4")
                        ], width=12)
                    ])
                ], label="Overview", tab_id="tab-overview"),
                
                # Agent Details Tab
                dbc.Tab([
                    dbc.Row([
                        # Agent Selector
                        dbc.Col([
                            html.Label("Select Agent:"),
                            dcc.Dropdown(id="agent-selector", className="mb-4"),
                            html.Div(id="agent-details")
                        ], width=12)
                    ])
                ], label="Agent Details", tab_id="tab-agent-details"),
                
                # Performance Tab
                dbc.Tab([
                    dbc.Row([
                        # Performance Metrics
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Agent Performance Metrics"),
                                dbc.CardBody([
                                    dcc.Graph(id="performance-timeline")
                                ])
                            ], className="mt-4")
                        ], width=12)
                    ]),
                    
                    dbc.Row([
                        # Performance Comparison
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Agent Performance Comparison"),
                                dbc.CardBody([
                                    dcc.Graph(id="performance-comparison")
                                ])
                            ], className="mt-4")
                        ], width=12)
                    ])
                ], label="Performance", tab_id="tab-performance"),
                
                # Communication Tab
                dbc.Tab([
                    dbc.Row([
                        # Command Broadcaster
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Send Command to Agents"),
                                dbc.CardBody([
                                    html.Label("Command:"),
                                    dcc.Input(id="command-input", type="text", className="form-control mb-2"),
                                    html.Label("Parameters (JSON):"),
                                    dcc.Textarea(id="parameters-input", className="form-control mb-2", style={"height": "100px"}),
                                    html.Label("Filter by Agent Type (optional):"),
                                    dcc.Input(id="agent-type-filter", type="text", className="form-control mb-2"),
                                    html.Label("Filter by Skills (comma-separated, optional):"),
                                    dcc.Input(id="skills-filter", type="text", className="form-control mb-2"),
                                    dbc.Button("Send Command", id="send-command-button", color="primary", className="mt-2")
                                ])
                            ], className="mt-4")
                        ], width=6),
                        
                        # Task Assignment
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Assign Task"),
                                dbc.CardBody([
                                    html.Label("Task Data (JSON):"),
                                    dcc.Textarea(id="task-data-input", className="form-control mb-2", style={"height": "200px"}),
                                    html.Label("Filter by Agent Type (optional):"),
                                    dcc.Input(id="task-agent-type-filter", type="text", className="form-control mb-2"),
                                    html.Label("Filter by Skills (comma-separated, optional):"),
                                    dcc.Input(id="task-skills-filter", type="text", className="form-control mb-2"),
                                    dbc.Button("Assign Task", id="assign-task-button", color="primary", className="mt-2")
                                ])
                            ], className="mt-4")
                        ], width=6)
                    ]),
                    
                    dbc.Row([
                        # Command Results
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader("Command Results"),
                                dbc.CardBody([
                                    html.Div(id="command-results")
                                ])
                            ], className="mt-4")
                        ], width=12)
                    ])
                ], label="Communication", tab_id="tab-communication")
            ], id="tabs", active_tab="tab-overview"),
            
            # Footer
            dbc.Row([
                dbc.Col([
                    html.Hr(),
                    html.P("EPOCH5 Agent Monitor Dashboard - © EpochCore5", className="text-muted")
                ], width=12)
            ])
        ], fluid=True)
    
    def _setup_callbacks(self):
        """Set up dashboard callbacks"""
        # Update agent status cards
        @self.app.callback(
            Output("agent-status-cards", "children"),
            Input("interval-status", "n_intervals")
        )
        def update_status_cards(n):
            agents = self.agent_monitor.get_all_agent_statuses()
            
            cards = []
            for did, agent in agents.items():
                agent_data = agent["agent_data"]
                agent_type = agent_data.get("type", "unknown")
                
                # Get status color
                status_color = "success" if agent["is_online"] else "danger"
                status_text = "Online" if agent["is_online"] else "Offline"
                
                # Create card
                card = dbc.Card([
                    dbc.CardHeader(f"Agent: {agent_type} ({did[:10]}...)"),
                    dbc.CardBody([
                        html.H5(f"Status: ", className="card-title"),
                        html.Span(status_text, className=f"badge bg-{status_color}"),
                        html.P(f"Reliability: {agent_data.get('reliability_score', 0):.2f}", className="card-text mt-2"),
                        html.P(f"Tasks: {agent_data.get('successful_tasks', 0)}/{agent_data.get('total_tasks', 0)}", className="card-text"),
                        html.P(f"Skills: {', '.join(agent_data.get('skills', []))}", className="card-text"),
                    ])
                ], className="mb-4", color=status_color, outline=True)
                
                cards.append(dbc.Col(card, width=3))
            
            if not cards:
                return html.Div("No agents registered", className="text-center py-4")
                
            return dbc.Row(cards)
        
        # Update agent type pie chart
        @self.app.callback(
            Output("agent-type-pie", "figure"),
            Input("interval-status", "n_intervals")
        )
        def update_agent_type_pie(n):
            agents = self.agent_monitor.get_all_agent_statuses()
            
            # Count agent types
            agent_types = {}
            for did, agent in agents.items():
                agent_type = agent["agent_data"].get("type", "unknown")
                agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
            
            if not agent_types:
                return go.Figure()
                
            # Create pie chart
            fig = px.pie(
                names=list(agent_types.keys()),
                values=list(agent_types.values()),
                title="Agent Types"
            )
            
            return fig
        
        # Update reliability histogram
        @self.app.callback(
            Output("reliability-histogram", "figure"),
            Input("interval-status", "n_intervals")
        )
        def update_reliability_histogram(n):
            agents = self.agent_monitor.get_all_agent_statuses()
            
            # Get reliability scores
            reliability_scores = []
            agent_names = []
            for did, agent in agents.items():
                reliability = agent["agent_data"].get("reliability_score", 0)
                agent_type = agent["agent_data"].get("type", "unknown")
                agent_name = f"{agent_type} ({did[:8]}...)"
                
                reliability_scores.append(reliability)
                agent_names.append(agent_name)
            
            if not reliability_scores:
                return go.Figure()
                
            # Create bar chart
            fig = px.bar(
                x=agent_names,
                y=reliability_scores,
                title="Agent Reliability Scores",
                labels={"x": "Agent", "y": "Reliability Score"}
            )
            
            fig.update_layout(yaxis_range=[0, 1])
            
            return fig
        
        # Update activity feed
        @self.app.callback(
            Output("activity-feed", "children"),
            Input("interval-status", "n_intervals")
        )
        def update_activity_feed(n):
            # Read recent heartbeats
            try:
                heartbeat_file = self.agent_monitor.agent_manager.heartbeat_file
                if not os.path.exists(heartbeat_file):
                    return html.P("No recent activity")
                    
                with open(heartbeat_file, "r") as f:
                    lines = f.readlines()
                
                # Get last 10 lines
                recent_lines = lines[-10:]
                
                # Create list items
                items = []
                for line in recent_lines:
                    items.append(html.Li(line.strip(), className="list-group-item"))
                
                return html.Ul(items, className="list-group")
                
            except Exception as e:
                logger.error(f"Error updating activity feed: {e}")
                return html.P(f"Error: {str(e)}")
        
        # Update agent selector
        @self.app.callback(
            Output("agent-selector", "options"),
            Input("interval-status", "n_intervals")
        )
        def update_agent_selector(n):
            agents = self.agent_monitor.get_all_agent_statuses()
            
            options = []
            for did, agent in agents.items():
                agent_type = agent["agent_data"].get("type", "unknown")
                label = f"{agent_type} ({did})"
                
                options.append({"label": label, "value": did})
            
            return options
        
        # Update agent details
        @self.app.callback(
            Output("agent-details", "children"),
            Input("agent-selector", "value")
        )
        def update_agent_details(did):
            if not did:
                return html.P("Select an agent to view details")
                
            agent = self.agent_monitor.get_agent_status(did)
            if not agent:
                return html.P(f"Agent {did} not found")
                
            agent_data = agent["agent_data"]
            
            # Create details table
            rows = [
                html.Tr([html.Td("Agent DID"), html.Td(did)]),
                html.Tr([html.Td("Agent Type"), html.Td(agent_data.get("type", "unknown"))]),
                html.Tr([html.Td("Status"), html.Td("Online" if agent["is_online"] else "Offline")]),
                html.Tr([html.Td("Created At"), html.Td(agent_data.get("created_at", "unknown"))]),
                html.Tr([html.Td("Last Heartbeat"), html.Td(agent_data.get("last_heartbeat", "unknown"))]),
                html.Tr([html.Td("Reliability Score"), html.Td(f"{agent_data.get('reliability_score', 0):.2f}")]),
                html.Tr([html.Td("Average Latency"), html.Td(f"{agent_data.get('average_latency', 0):.2f}s")]),
                html.Tr([html.Td("Total Tasks"), html.Td(agent_data.get("total_tasks", 0))]),
                html.Tr([html.Td("Successful Tasks"), html.Td(agent_data.get("successful_tasks", 0))]),
                html.Tr([html.Td("Skills"), html.Td(", ".join(agent_data.get("skills", [])))]),
            ]
            
            table = dbc.Table([html.Tbody(rows)], bordered=True)
            
            # Add query section
            query_section = dbc.Card([
                dbc.CardHeader("Query Agent"),
                dbc.CardBody([
                    html.Label("Query Type:"),
                    dcc.Input(id="query-type-input", type="text", className="form-control mb-2"),
                    html.Label("Parameters (JSON):"),
                    dcc.Textarea(id="query-parameters-input", className="form-control mb-2", style={"height": "100px"}),
                    dbc.Button("Send Query", id="send-query-button", color="primary", className="mt-2"),
                    html.Div(id="query-results", className="mt-3")
                ])
            ], className="mt-4")
            
            return html.Div([
                dbc.Card([
                    dbc.CardHeader("Agent Details"),
                    dbc.CardBody([table])
                ]),
                query_section
            ])
        
        # Update performance timeline
        @self.app.callback(
            Output("performance-timeline", "figure"),
            Input("interval-status", "n_intervals")
        )
        def update_performance_timeline(n):
            performance_data = {}
            
            # Get performance data for all agents
            agents = self.agent_monitor.get_all_agent_statuses()
            for did, agent in agents.items():
                history = self.agent_monitor.get_agent_performance_history(did)
                if history:
                    agent_type = agent["agent_data"].get("type", "unknown")
                    performance_data[f"{agent_type} ({did[:8]}...)"] = history
            
            if not performance_data:
                return go.Figure()
            
            # Create figure
            fig = go.Figure()
            
            for agent_name, history in performance_data.items():
                timestamps = [entry["timestamp"] for entry in history]
                reliability = [entry["reliability"] for entry in history]
                
                fig.add_trace(go.Scatter(
                    x=timestamps,
                    y=reliability,
                    mode="lines",
                    name=f"{agent_name} (Reliability)"
                ))
            
            fig.update_layout(
                title="Agent Reliability Over Time",
                xaxis_title="Time",
                yaxis_title="Reliability Score",
                yaxis_range=[0, 1]
            )
            
            return fig
        
        # Update performance comparison
        @self.app.callback(
            Output("performance-comparison", "figure"),
            Input("interval-status", "n_intervals")
        )
        def update_performance_comparison(n):
            agents = self.agent_monitor.get_all_agent_statuses()
            
            # Prepare data for comparison
            agent_names = []
            reliability_scores = []
            latencies = []
            success_rates = []
            
            for did, agent in agents.items():
                agent_data = agent["agent_data"]
                agent_type = agent_data.get("type", "unknown")
                agent_name = f"{agent_type} ({did[:8]}...)"
                
                reliability = agent_data.get("reliability_score", 0)
                latency = agent_data.get("average_latency", 0)
                
                total_tasks = agent_data.get("total_tasks", 0)
                successful_tasks = agent_data.get("successful_tasks", 0)
                success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0
                
                agent_names.append(agent_name)
                reliability_scores.append(reliability)
                latencies.append(latency)
                success_rates.append(success_rate)
            
            if not agent_names:
                return go.Figure()
            
            # Create figure with subplots
            fig = make_subplots(rows=3, cols=1, 
                               subplot_titles=("Reliability Scores", "Average Latency (s)", "Success Rate"))
            
            fig.add_trace(go.Bar(x=agent_names, y=reliability_scores, name="Reliability"), row=1, col=1)
            fig.add_trace(go.Bar(x=agent_names, y=latencies, name="Latency"), row=2, col=1)
            fig.add_trace(go.Bar(x=agent_names, y=success_rates, name="Success Rate"), row=3, col=1)
            
            fig.update_layout(height=800, title_text="Agent Performance Comparison")
            
            return fig
        
        # Send command
        @self.app.callback(
            Output("command-results", "children"),
            Input("send-command-button", "n_clicks"),
            State("command-input", "value"),
            State("parameters-input", "value"),
            State("agent-type-filter", "value"),
            State("skills-filter", "value"),
            prevent_initial_call=True
        )
        def send_command(n_clicks, command, parameters_json, agent_type_filter, skills_filter):
            if not command:
                return html.P("Please enter a command", className="text-danger")
            
            try:
                # Parse parameters JSON
                parameters = {}
                if parameters_json:
                    parameters = json.loads(parameters_json)
                
                # Create filter
                agent_filter = {}
                if agent_type_filter:
                    agent_filter["agent_type"] = agent_type_filter
                
                if skills_filter:
                    skills = [s.strip() for s in skills_filter.split(",")]
                    agent_filter["skills"] = skills
                
                # Send command
                sent_count = self.agent_monitor.broadcast_command(command, parameters, agent_filter)
                
                return html.Div([
                    html.P(f"Command sent to {sent_count} agents", className="text-success"),
                    html.P(f"Command: {command}"),
                    html.P(f"Parameters: {parameters}"),
                    html.P(f"Filter: {agent_filter}")
                ])
                
            except Exception as e:
                return html.P(f"Error: {str(e)}", className="text-danger")
        
        # Assign task
        @self.app.callback(
            Output("command-results", "children", allow_duplicate=True),
            Input("assign-task-button", "n_clicks"),
            State("task-data-input", "value"),
            State("task-agent-type-filter", "value"),
            State("task-skills-filter", "value"),
            prevent_initial_call=True
        )
        def assign_task(n_clicks, task_data_json, agent_type_filter, skills_filter):
            if not task_data_json:
                return html.P("Please enter task data", className="text-danger")
            
            try:
                # Parse task data JSON
                task_data = json.loads(task_data_json)
                
                # Create filter
                agent_filter = {}
                if agent_type_filter:
                    agent_filter["agent_type"] = agent_type_filter
                
                if skills_filter:
                    skills = [s.strip() for s in skills_filter.split(",")]
                    agent_filter["skills"] = skills
                
                # Assign task
                agent_did, message_id = self.agent_monitor.assign_task(task_data, agent_filter)
                
                if not agent_did:
                    return html.P("No suitable agent found for this task", className="text-warning")
                
                return html.Div([
                    html.P(f"Task assigned to agent {agent_did}", className="text-success"),
                    html.P(f"Message ID: {message_id}"),
                    html.P(f"Task Data: {task_data}"),
                    html.P(f"Filter: {agent_filter}")
                ])
                
            except Exception as e:
                return html.P(f"Error: {str(e)}", className="text-danger")
        
        # Send query
        @self.app.callback(
            Output("query-results", "children"),
            Input("send-query-button", "n_clicks"),
            State("agent-selector", "value"),
            State("query-type-input", "value"),
            State("query-parameters-input", "value"),
            prevent_initial_call=True
        )
        def send_query(n_clicks, did, query_type, parameters_json):
            if not did:
                return html.P("Please select an agent", className="text-danger")
                
            if not query_type:
                return html.P("Please enter a query type", className="text-danger")
            
            try:
                # Parse parameters JSON
                parameters = {}
                if parameters_json:
                    parameters = json.loads(parameters_json)
                
                # Send query
                query_id = self.agent_monitor.query_agent(did, query_type, parameters)
                
                if not query_id:
                    return html.P("Failed to send query", className="text-danger")
                
                return html.Div([
                    html.P(f"Query sent successfully", className="text-success"),
                    html.P(f"Query ID: {query_id}"),
                    html.P("The response will appear in the agent's query responses when available."),
                    dbc.Button("Check for Response", id="check-response-button", color="primary", className="mt-2"),
                    html.Div(id="query-response-result", className="mt-3")
                ])
                
            except Exception as e:
                return html.P(f"Error: {str(e)}", className="text-danger")
        
        # Check query response
        @self.app.callback(
            Output("query-response-result", "children"),
            Input("check-response-button", "n_clicks"),
            State("agent-selector", "value"),
            prevent_initial_call=True
        )
        def check_query_response(n_clicks, did):
            if not did:
                return html.P("Agent not selected", className="text-danger")
            
            agent = self.agent_monitor.get_agent_status(did)
            if not agent:
                return html.P(f"Agent {did} not found", className="text-danger")
            
            if "query_responses" not in agent:
                return html.P("No query responses available", className="text-warning")
            
            responses = agent["query_responses"]
            if not responses:
                return html.P("No query responses available", className="text-warning")
            
            # Show most recent responses
            recent_responses = responses[-5:]
            
            response_items = []
            for response in recent_responses:
                timestamp = response.get("timestamp", "unknown")
                query_id = response.get("query_id", "unknown")
                response_data = response.get("response", {})
                
                response_items.append(html.Div([
                    html.P(f"Query ID: {query_id}"),
                    html.P(f"Timestamp: {timestamp}"),
                    html.P("Response:"),
                    html.Pre(json.dumps(response_data, indent=2), className="bg-light p-2")
                ], className="border p-3 mb-3"))
            
            return html.Div([
                html.H5(f"Recent Query Responses ({len(recent_responses)})"),
                html.Div(response_items)
            ])
    
    def run(self, host: str = "0.0.0.0", port: int = 8050, debug: bool = False):
        """
        Run the dashboard
        
        Args:
            host: Host to run on
            port: Port to run on
            debug: Whether to run in debug mode
        """
        self.app.run_server(host=host, port=port, debug=debug)


def main():
    """Main entry point for agent monitor"""
    parser = argparse.ArgumentParser(description="EPOCH5 Agent Monitor and Communication System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start agent monitoring")
    monitor_parser.add_argument("--base-dir", default="./archive/EPOCH5", help="Base directory for EPOCH5 systems")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start web dashboard")
    dashboard_parser.add_argument("--host", default="0.0.0.0", help="Dashboard host")
    dashboard_parser.add_argument("--port", type=int, default=8050, help="Dashboard port")
    dashboard_parser.add_argument("--base-dir", default="./archive/EPOCH5", help="Base directory for EPOCH5 systems")
    dashboard_parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    # Broadcast command
    broadcast_parser = subparsers.add_parser("broadcast", help="Broadcast a command to agents")
    broadcast_parser.add_argument("--command", required=True, help="Command to broadcast")
    broadcast_parser.add_argument("--parameters", help="Command parameters (JSON)")
    broadcast_parser.add_argument("--agent-type", help="Filter by agent type")
    broadcast_parser.add_argument("--skills", help="Filter by skills (comma-separated)")
    broadcast_parser.add_argument("--base-dir", default="./archive/EPOCH5", help="Base directory for EPOCH5 systems")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show agent status")
    status_parser.add_argument("--did", help="Agent DID (show all if not specified)")
    status_parser.add_argument("--base-dir", default="./archive/EPOCH5", help="Base directory for EPOCH5 systems")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export performance data")
    export_parser.add_argument("--output", required=True, help="Output file path")
    export_parser.add_argument("--base-dir", default="./archive/EPOCH5", help="Base directory for EPOCH5 systems")
    
    args = parser.parse_args()
    
    # Create agent monitor
    monitor = AgentMonitor(base_dir=args.base_dir if hasattr(args, 'base_dir') else "./archive/EPOCH5")
    
    try:
        if args.command == "monitor":
            logger.info("Starting agent monitor...")
            
            # Set up signal handlers
            def signal_handler(sig, frame):
                logger.info("Shutting down agent monitor...")
                monitor.shutdown()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Run indefinitely
            logger.info("Press Ctrl+C to stop")
            signal.pause()
            
        elif args.command == "dashboard":
            logger.info(f"Starting agent dashboard on {args.host}:{args.port}...")
            
            if not DASH_AVAILABLE:
                logger.error("Dash is not installed. Cannot start dashboard.")
                logger.error("Install with: pip install dash dash-bootstrap-components plotly pandas")
                sys.exit(1)
            
            # Create and run dashboard
            dashboard = AgentDashboard(monitor)
            dashboard.run(host=args.host, port=args.port, debug=args.debug)
            
        elif args.command == "broadcast":
            # Parse parameters
            parameters = {}
            if args.parameters:
                parameters = json.loads(args.parameters)
            
            # Create filter
            agent_filter = {}
            if args.agent_type:
                agent_filter["agent_type"] = args.agent_type
            
            if args.skills:
                skills = [s.strip() for s in args.skills.split(",")]
                agent_filter["skills"] = skills
            
            # Broadcast command
            sent_count = monitor.broadcast_command(args.command, parameters, agent_filter)
            
            print(f"Command sent to {sent_count} agents")
            
        elif args.command == "status":
            if args.did:
                # Show status for specific agent
                status = monitor.get_agent_status(args.did)
                if not status:
                    print(f"Agent {args.did} not found")
                    sys.exit(1)
                
                print(f"Status for agent {args.did}:")
                print(json.dumps(status, indent=2))
            else:
                # Show status for all agents
                statuses = monitor.get_all_agent_statuses()
                
                print(f"Agent Statuses ({len(statuses)} agents):")
                for did, status in statuses.items():
                    agent_data = status["agent_data"]
                    agent_type = agent_data.get("type", "unknown")
                    is_online = status["is_online"]
                    reliability = agent_data.get("reliability_score", 0)
                    
                    status_text = "Online" if is_online else "Offline"
                    print(f"  {did} ({agent_type}): {status_text}, Reliability: {reliability:.2f}")
                
        elif args.command == "export":
            # Export performance data
            success = monitor.export_performance_data(args.output)
            
            if success:
                print(f"Performance data exported to {args.output}")
            else:
                print("Failed to export performance data")
                sys.exit(1)
                
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
    finally:
        monitor.shutdown()


if __name__ == "__main__":
    main()
