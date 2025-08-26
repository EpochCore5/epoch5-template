#!/usr/bin/env python3
"""
Agent Management System - Decentralized identifiers, registry, and monitoring
Integrates with EPOCH5 logging, hashing, and provenance tracking

This module provides comprehensive agent lifecycle management including:
- Decentralized identifier (DID) generation and validation
- Agent registry with skill-based categorization
- Performance metrics and reliability scoring
- Heartbeat monitoring and anomaly detection
- Batch processing for large-scale agent operations

Examples:
    Basic agent creation:
        manager = AgentManager()
        agent = manager.create_agent(["python", "data_processing"])
        manager.register_agent(agent)
    
    Monitoring and metrics:
        manager.log_heartbeat(agent["did"])
        manager.update_agent_stats(agent["did"], success=True, latency=0.5)
        manager.detect_anomaly(agent["did"], "timeout", "Task timeout occurred")
"""

import json
import uuid
import time
import hashlib
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import EPOCH5 utilities for enhanced functionality
from epoch5_utils import (
    get_logger, timestamp, sha256, ensure_directory, safe_load_json, safe_save_json,
    EPOCH5Config, EPOCH5ErrorHandler, EPOCH5Utils, EPOCH5Metrics
)

class AgentManager:
    """
    Manages agent lifecycle with enhanced error handling and logging
    
    This class provides comprehensive agent management capabilities including:
    - DID generation and validation
    - Registry operations with atomic updates
    - Performance monitoring and metrics collection
    - Batch processing for large-scale operations
    - Configurable behavior through EPOCH5Config
    
    Attributes:
        base_dir (Path): Base directory for agent data storage
        config (EPOCH5Config): Configuration manager instance
        logger (Logger): Logger instance for this component
        metrics (EPOCH5Metrics): Metrics collector for performance monitoring
    """
    
    def __init__(self, base_dir: str = "./archive/EPOCH5", config: Optional[EPOCH5Config] = None):
        """
        Initialize agent manager with enhanced configuration and logging
        
        Args:
            base_dir (str): Base directory for EPOCH5 data storage
            config (EPOCH5Config, optional): Configuration instance. Creates default if None.
            
        Raises:
            RuntimeError: If directory creation fails or permissions are insufficient
        """
        self.base_dir = ensure_directory(base_dir)
        self.config = config or EPOCH5Config()
        self.metrics = EPOCH5Metrics()
        
        # Setup logging with configuration
        log_level = self.config.get('agent_management', 'log_level', 'INFO')
        log_file = self.base_dir / "agents" / "agent_management.log"
        self.logger = get_logger('AgentManager', str(log_file), log_level)
        
        # Initialize directories with error handling
        try:
            self.agents_dir = ensure_directory(self.base_dir / "agents")
            self.registry_file = self.agents_dir / "registry.json"
            self.anomalies_file = self.agents_dir / "anomalies.log"
            self.heartbeat_file = self.agents_dir / "agent_heartbeats.log"
            
            self.logger.info(f"AgentManager initialized with base_dir: {base_dir}")
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentManager: {str(e)}")
            raise RuntimeError(f"AgentManager initialization failed: {str(e)}")
        
        # Load configuration defaults
        self.default_reliability_score = float(self.config.get(
            'agent_management', 'default_reliability_score', '1.0'
        ))
        self.batch_size = self.config.getint('DEFAULT', 'batch_size', 100)
        
    def timestamp(self) -> str:
        """Generate ISO timestamp consistent with EPOCH5"""
        return timestamp()
    
    def sha256(self, data: str) -> str:
        """Generate SHA256 hash consistent with EPOCH5"""
        return sha256(data)
    
    def generate_did(self, agent_type: str = "agent") -> str:
        """
        Generate decentralized identifier for agent with validation
        
        Args:
            agent_type (str): Type of agent (default: "agent")
            
        Returns:
            str: Generated DID in format "did:epoch5:{type}:{hash}"
            
        Raises:
            ValueError: If agent_type is invalid or empty
        """
        if not agent_type or not agent_type.strip():
            raise ValueError("Agent type cannot be empty")
            
        # Sanitize agent type
        agent_type = agent_type.strip().lower()
        
        unique_id = str(uuid.uuid4())
        timestamp_val = self.timestamp()
        did_data = f"{agent_type}|{unique_id}|{timestamp_val}"
        did_hash = self.sha256(did_data)[:16]
        
        did = f"did:epoch5:{agent_type}:{did_hash}"
        self.logger.debug(f"Generated DID: {did} for agent_type: {agent_type}")
        
        return did
    
    def create_agent(self, skills: List[str], agent_type: str = "agent") -> Dict[str, Any]:
        """
        Create new agent with DID and initial properties with validation
        
        Args:
            skills (List[str]): List of agent skills/capabilities
            agent_type (str): Type of agent (default: "agent")
            
        Returns:
            Dict[str, Any]: Agent data structure with all required fields
            
        Raises:
            ValueError: If skills list is empty or contains invalid values
        """
        self.metrics.start_operation('create_agent')
        
        try:
            # Validate inputs
            if not skills or not isinstance(skills, list):
                raise ValueError("Skills must be a non-empty list")
            
            # Clean and validate skills
            cleaned_skills = [skill.strip().lower() for skill in skills if skill.strip()]
            if not cleaned_skills:
                raise ValueError("No valid skills provided")
            
            did = self.generate_did(agent_type)
            agent = {
                "did": did,
                "type": agent_type,
                "created_at": self.timestamp(),
                "skills": cleaned_skills,
                "reliability_score": self.default_reliability_score,
                "average_latency": 0.0,
                "total_tasks": 0,
                "successful_tasks": 0,
                "last_heartbeat": self.timestamp(),
                "status": "active",
                "metadata": {
                    "creation_hash": self.sha256(f"{did}|{cleaned_skills}|{self.timestamp()}")
                }
            }
            
            self.log_heartbeat(did, "AGENT_CREATED")
            self.logger.info(f"Created agent {did} with skills: {cleaned_skills}")
            self.metrics.end_operation('create_agent', success=True)
            
            return agent
            
        except Exception as e:
            self.logger.error(f"Failed to create agent: {str(e)}")
            self.metrics.end_operation('create_agent', success=False)
            raise
    
    def load_registry(self) -> Dict[str, Any]:
        """
        Load agent registry from file with enhanced error handling
        
        Returns:
            Dict[str, Any]: Registry data with agents and metadata
            
        Note:
            Returns empty registry structure if file doesn't exist or is corrupted
        """
        default_registry = {"agents": {}, "last_updated": self.timestamp()}
        
        if not self.registry_file.exists():
            self.logger.debug(f"Registry file does not exist: {self.registry_file}")
            return default_registry
        
        try:
            registry = safe_load_json(self.registry_file, default_registry)
            self.logger.debug(f"Loaded registry with {len(registry.get('agents', {}))} agents")
            return registry
        except Exception as e:
            self.logger.error(f"Failed to load registry, using default: {str(e)}")
            return default_registry
    
    def save_registry(self, registry: Dict[str, Any]) -> bool:
        """
        Save agent registry to file with enhanced error handling
        
        Args:
            registry (Dict[str, Any]): Registry data to save
            
        Returns:
            bool: True if save successful, False otherwise
        """
        self.metrics.start_operation('save_registry')
        
        try:
            # Update timestamp
            registry["last_updated"] = self.timestamp()
            
            # Validate registry structure
            if "agents" not in registry:
                registry["agents"] = {}
            
            # Save with error handling
            success = safe_save_json(registry, self.registry_file)
            
            if success:
                self.logger.debug(f"Saved registry with {len(registry['agents'])} agents")
                self.metrics.end_operation('save_registry', success=True)
            else:
                self.logger.error("Failed to save registry")
                self.metrics.end_operation('save_registry', success=False)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Registry save error: {str(e)}")
            self.metrics.end_operation('save_registry', success=False)
            return False
    
    def register_agent(self, agent: Dict[str, Any]) -> bool:
        """Register agent in the registry"""
        registry = self.load_registry()
        registry["agents"][agent["did"]] = agent
        self.save_registry(registry)
        return True
    
    def get_agent(self, did: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent by DID"""
        registry = self.load_registry()
        return registry["agents"].get(did)
    
    def update_agent_stats(self, did: str, success: bool, latency: float):
        """Update agent performance statistics"""
        registry = self.load_registry()
        if did in registry["agents"]:
            agent = registry["agents"][did]
            agent["total_tasks"] += 1
            if success:
                agent["successful_tasks"] += 1
            
            # Update reliability score (weighted average)
            agent["reliability_score"] = agent["successful_tasks"] / agent["total_tasks"]
            
            # Update average latency (exponential moving average)
            alpha = 0.1
            agent["average_latency"] = (alpha * latency) + ((1 - alpha) * agent["average_latency"])
            
            self.save_registry(registry)
            return True
        return False
    
    def log_heartbeat(self, did: str, status: str = "HEARTBEAT"):
        """Log agent heartbeat with EPOCH5 compatible format"""
        timestamp = self.timestamp()
        with open(self.heartbeat_file, 'a') as f:
            f.write(f"{timestamp} | DID={did} | {status}\n")
        
        # Update last heartbeat in registry
        registry = self.load_registry()
        if did in registry["agents"]:
            registry["agents"][did]["last_heartbeat"] = timestamp
            self.save_registry(registry)
    
    def detect_anomaly(self, did: str, anomaly_type: str, details: str):
        """Log agent anomaly for monitoring"""
        timestamp = self.timestamp()
        anomaly = {
            "timestamp": timestamp,
            "did": did,
            "type": anomaly_type,
            "details": details,
            "hash": self.sha256(f"{timestamp}|{did}|{anomaly_type}|{details}")
        }
        
        with open(self.anomalies_file, 'a') as f:
            f.write(f"{json.dumps(anomaly)}\n")
        
        return anomaly
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get list of active agents"""
        registry = self.load_registry()
        return [agent for agent in registry["agents"].values() if agent["status"] == "active"]
    
    def get_agents_by_skill(self, skill: str) -> List[Dict[str, Any]]:
        """Get agents that have a specific skill"""
        registry = self.load_registry()
        return [agent for agent in registry["agents"].values() 
                if skill in agent["skills"] and agent["status"] == "active"]

# CLI interface for agent management
def main():
    """Enhanced CLI interface with configuration support and comprehensive options"""
    parser = EPOCH5Utils.create_cli_parser("EPOCH5 Agent Management System")
    
    # Agent operations
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create agent
    create_parser = subparsers.add_parser("create", help="Create new agent")
    create_parser.add_argument("skills", nargs="+", help="Agent skills")
    create_parser.add_argument("--type", default="agent", help="Agent type")
    
    # List agents
    list_parser = subparsers.add_parser("list", help="List agents")
    list_parser.add_argument("--skill", help="Filter by skill")
    list_parser.add_argument("--active-only", action="store_true", help="Show only active agents")
    
    # Agent monitoring
    heartbeat_parser = subparsers.add_parser("heartbeat", help="Log agent heartbeat")
    heartbeat_parser.add_argument("did", help="Agent DID")
    heartbeat_parser.add_argument("--status", default="HEARTBEAT", help="Status message")
    
    # Anomaly reporting
    anomaly_parser = subparsers.add_parser("anomaly", help="Report agent anomaly")
    anomaly_parser.add_argument("did", help="Agent DID")
    anomaly_parser.add_argument("type", help="Anomaly type")
    anomaly_parser.add_argument("details", help="Anomaly details")
    
    # Statistics
    stats_parser = subparsers.add_parser("stats", help="Update agent statistics")
    stats_parser.add_argument("did", help="Agent DID")
    stats_parser.add_argument("--success", type=bool, default=True, help="Task success")
    stats_parser.add_argument("--latency", type=float, required=True, help="Task latency")
    
    # Bulk operations
    bulk_parser = subparsers.add_parser("bulk", help="Bulk operations")
    bulk_parser.add_argument("--create-from-file", help="Create agents from JSON file")
    bulk_parser.add_argument("--export", help="Export registry to file")
    
    args = parser.parse_args()
    
    # Initialize configuration and manager
    config = EPOCH5Config(args.config) if args.config else None
    manager = AgentManager(args.base_dir, config)
    
    if args.command == "create":
        try:
            agent = manager.create_agent(args.skills, args.type)
            manager.register_agent(agent)
            print(f"✓ Created agent: {agent['did']}")
            print(f"  Type: {agent['type']}")
            print(f"  Skills: {', '.join(agent['skills'])}")
            print(f"  Reliability: {agent['reliability_score']:.2f}")
        except Exception as e:
            print(f"✗ Failed to create agent: {str(e)}", file=sys.stderr)
            return 1
    
    elif args.command == "list":
        try:
            registry = manager.load_registry()
            agents = registry.get('agents', {})
            
            # Apply filters
            if args.skill:
                agents = {did: agent for did, agent in agents.items() 
                         if args.skill.lower() in [s.lower() for s in agent.get('skills', [])]}
            
            if args.active_only:
                agents = {did: agent for did, agent in agents.items() 
                         if agent.get('status') == 'active'}
            
            print(f"Agent Registry ({len(agents)} agents):")
            if not agents:
                print("  No agents found matching criteria")
            else:
                for did, agent in agents.items():
                    status_indicator = "🟢" if agent.get('status') == 'active' else "🔴"
                    print(f"  {status_indicator} {did}")
                    print(f"    Skills: {', '.join(agent.get('skills', []))}")
                    print(f"    Reliability: {agent.get('reliability_score', 0):.2f}")
                    print(f"    Tasks: {agent.get('successful_tasks', 0)}/{agent.get('total_tasks', 0)}")
                    print()
        except Exception as e:
            print(f"✗ Failed to list agents: {str(e)}", file=sys.stderr)
            return 1
    
    elif args.command == "heartbeat":
        try:
            manager.log_heartbeat(args.did, args.status)
            print(f"✓ Heartbeat logged for {args.did}")
        except Exception as e:
            print(f"✗ Failed to log heartbeat: {str(e)}", file=sys.stderr)
            return 1
    
    elif args.command == "anomaly":
        try:
            anomaly = manager.detect_anomaly(args.did, args.type, args.details)
            print(f"✓ Anomaly logged: {anomaly['hash']}")
            print(f"  DID: {args.did}")
            print(f"  Type: {args.type}")
            print(f"  Details: {args.details}")
        except Exception as e:
            print(f"✗ Failed to log anomaly: {str(e)}", file=sys.stderr)
            return 1
    
    elif args.command == "stats":
        try:
            success = manager.update_agent_stats(args.did, args.success, args.latency)
            if success:
                print(f"✓ Updated statistics for {args.did}")
                agent = manager.get_agent(args.did)
                if agent:
                    print(f"  Reliability: {agent['reliability_score']:.2f}")
                    print(f"  Avg Latency: {agent['average_latency']:.2f}s")
            else:
                print(f"✗ Agent {args.did} not found")
                return 1
        except Exception as e:
            print(f"✗ Failed to update statistics: {str(e)}", file=sys.stderr)
            return 1
    
    elif args.command == "bulk":
        if args.create_from_file:
            try:
                with open(args.create_from_file, 'r') as f:
                    agents_data = json.load(f)
                
                created_count = 0
                for agent_data in agents_data:
                    agent = manager.create_agent(
                        agent_data['skills'], 
                        agent_data.get('type', 'agent')
                    )
                    manager.register_agent(agent)
                    created_count += 1
                
                print(f"✓ Created {created_count} agents from {args.create_from_file}")
            except Exception as e:
                print(f"✗ Failed to create agents from file: {str(e)}", file=sys.stderr)
                return 1
        
        elif args.export:
            try:
                registry = manager.load_registry()
                with open(args.export, 'w') as f:
                    json.dump(registry, f, indent=2)
                print(f"✓ Exported registry to {args.export}")
            except Exception as e:
                print(f"✗ Failed to export registry: {str(e)}", file=sys.stderr)
                return 1
    
    else:
        parser.print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())