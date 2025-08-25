#!/usr/bin/env python3
"""
Agent Management System - Decentralized identifiers, registry, and monitoring
Integrates with EPOCH5 logging, hashing, and provenance tracking
"""

import json
import uuid
import time
import hashlib
import random
import threading
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from collections import deque

# Cryptographic imports
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

class AnomalySeverity(Enum):
    """Severity levels for anomaly classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high" 
    CRITICAL = "critical"

class AgentManager:
    def __init__(self, base_dir: str = "./archive/EPOCH5"):
        self.base_dir = Path(base_dir)
        self.agents_dir = self.base_dir / "agents"
        self.keys_dir = self.agents_dir / "keys"  # Cryptographic keys storage
        self.backup_dir = self.agents_dir / "backups"  # Registry backups
        
        # Create directories
        for directory in [self.agents_dir, self.keys_dir, self.backup_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.registry_file = self.agents_dir / "registry.json"
        self.anomalies_file = self.agents_dir / "anomalies.log"
        self.heartbeat_file = self.agents_dir / "agent_heartbeats.log"
        self.integrity_log = self.agents_dir / "integrity.log"
        
        # Thread safety
        self._registry_lock = threading.Lock()
        self._file_lock = threading.Lock()
        
        # Task history buffer (limited size to prevent unbounded growth)
        self.max_task_history = 1000
        self.task_history = deque(maxlen=self.max_task_history)
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup enhanced logging capabilities"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.agents_dir / "agent_management.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _create_backup(self, file_path: Path) -> Path:
        """Create backup of a file before critical writes"""
        if file_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"{file_path.name}_{timestamp}.backup"
            shutil.copy2(file_path, backup_path)
            return backup_path
        return None
    
    def _validate_json_structure(self, data: Dict[str, Any], expected_keys: List[str]) -> bool:
        """Validate JSON structure against expected schema"""
        try:
            return all(key in data for key in expected_keys)
        except (TypeError, AttributeError):
            return False
    
    def generate_rsa_keypair(self) -> Tuple[bytes, bytes]:
        """Generate RSA key pair for agent"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    def sign_message(self, message: str, private_key_pem: bytes) -> bytes:
        """Sign a message with RSA private key"""
        private_key = load_pem_private_key(private_key_pem, password=None)
        signature = private_key.sign(
            message.encode('utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    def verify_signature(self, message: str, signature: bytes, public_key_pem: bytes) -> bool:
        """Verify message signature with RSA public key"""
        try:
            public_key = load_pem_public_key(public_key_pem)
            public_key.verify(
                signature,
                message.encode('utf-8'),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            self.logger.warning(f"Signature verification failed: {e}")
            return False
        
    def store_keys(self, did: str, private_key: bytes, public_key: bytes):
        """Securely store agent keys"""
        private_key_file = self.keys_dir / f"{did}_private.pem"
        public_key_file = self.keys_dir / f"{did}_public.pem"
        
        # Store with restricted permissions
        with open(private_key_file, 'wb') as f:
            f.write(private_key)
        private_key_file.chmod(0o600)  # Read/write for owner only
        
        with open(public_key_file, 'wb') as f:
            f.write(public_key)
        public_key_file.chmod(0o644)  # Read for all, write for owner
    
    def load_keys(self, did: str) -> Tuple[Optional[bytes], Optional[bytes]]:
        """Load agent keys"""
        private_key_file = self.keys_dir / f"{did}_private.pem"
        public_key_file = self.keys_dir / f"{did}_public.pem"
        
        private_key = None
        public_key = None
        
        try:
            if private_key_file.exists():
                with open(private_key_file, 'rb') as f:
                    private_key = f.read()
            
            if public_key_file.exists():
                with open(public_key_file, 'rb') as f:
                    public_key = f.read()
        except Exception as e:
            self.logger.error(f"Error loading keys for {did}: {e}")
        
        return private_key, public_key
        
    def timestamp(self) -> str:
        """Generate ISO timestamp consistent with EPOCH5"""
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def sha256(self, data: str) -> str:
        """Generate SHA256 hash consistent with EPOCH5"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def generate_did(self, agent_type: str = "agent") -> str:
        """Generate decentralized identifier for agent"""
        unique_id = str(uuid.uuid4())
        timestamp = self.timestamp()
        did_data = f"{agent_type}|{unique_id}|{timestamp}"
        did_hash = self.sha256(did_data)[:16]
        return f"did:epoch5:{agent_type}:{did_hash}"
    
    def create_agent(self, skills: List[str], agent_type: str = "agent") -> Dict[str, Any]:
        """Create new agent with DID, cryptographic identity, and initial properties"""
        did = self.generate_did(agent_type)
        
        # Generate cryptographic keys
        private_key, public_key = self.generate_rsa_keypair()
        
        # Create agent data
        agent = {
            "did": did,
            "type": agent_type,
            "created_at": self.timestamp(),
            "skills": skills,
            "reliability_score": 1.0,
            "average_latency": 0.0,
            "total_tasks": 0,
            "successful_tasks": 0,
            "last_heartbeat": self.timestamp(),
            "status": "active",
            "cryptographic_identity": {
                "public_key_hash": self.sha256(public_key.decode('utf-8')),
                "key_created_at": self.timestamp()
            },
            "metadata": {
                "creation_hash": self.sha256(f"{did}|{skills}|{self.timestamp()}")
            },
            "task_history": [],
            "anomaly_count": 0
        }
        
        # Store keys securely
        self.store_keys(did, private_key, public_key)
        
        # Create and verify agent identity signature
        identity_message = f"{did}|{agent['created_at']}|{agent['cryptographic_identity']['public_key_hash']}"
        signature = self.sign_message(identity_message, private_key)
        agent["cryptographic_identity"]["identity_signature"] = signature.hex()
        
        self.log_heartbeat(did, "AGENT_CREATED")
        self.logger.info(f"Created agent with cryptographic identity: {did}")
        
        return agent
    
    def load_registry(self) -> Dict[str, Any]:
        """Load agent registry from file with thread safety"""
        with self._registry_lock:
            if self.registry_file.exists():
                try:
                    with open(self.registry_file, 'r') as f:
                        registry = json.load(f)
                    
                    # Validate registry structure
                    expected_keys = ["agents", "last_updated"]
                    if not self._validate_json_structure(registry, expected_keys):
                        self.logger.warning("Invalid registry structure, creating new registry")
                        return {"agents": {}, "last_updated": self.timestamp(), "integrity_hash": ""}
                    
                    return registry
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.error(f"Error loading registry: {e}")
                    # Try to recover from backup
                    return self._recover_from_backup() or {"agents": {}, "last_updated": self.timestamp(), "integrity_hash": ""}
            
            return {"agents": {}, "last_updated": self.timestamp(), "integrity_hash": ""}
    
    def save_registry(self, registry: Dict[str, Any]):
        """Save agent registry to file with backup and thread safety"""
        with self._registry_lock:
            # Create backup before critical write
            self._create_backup(self.registry_file)
            
            # Update timestamp and integrity hash
            registry["last_updated"] = self.timestamp()
            registry_data = json.dumps(registry["agents"], sort_keys=True)
            registry["integrity_hash"] = self.sha256(registry_data)
            
            try:
                with open(self.registry_file, 'w') as f:
                    json.dump(registry, f, indent=2)
                self.logger.debug("Registry saved successfully")
            except IOError as e:
                self.logger.error(f"Error saving registry: {e}")
                raise
    
    def _recover_from_backup(self) -> Optional[Dict[str, Any]]:
        """Attempt to recover registry from most recent backup"""
        try:
            backup_files = list(self.backup_dir.glob("registry_*.backup"))
            if not backup_files:
                return None
            
            # Get most recent backup
            latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
            
            with open(latest_backup, 'r') as f:
                registry = json.load(f)
            
            self.logger.info(f"Recovered registry from backup: {latest_backup}")
            return registry
            
        except Exception as e:
            self.logger.error(f"Failed to recover from backup: {e}")
            return None
    
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
    
    def update_agent_stats(self, did: str, success: bool, latency: float, task_id: str = None, task_type: str = "generic"):
        """Update agent performance statistics with task history tracking"""
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
            
            # Update last activity timestamp
            agent["last_activity"] = self.timestamp()
            
            self.save_registry(registry)
            
            # Add to task history
            task_id = task_id or f"task_{uuid.uuid4().hex[:8]}"
            self.add_task_to_history(did, task_id, task_type, success, latency)
            
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
    
    def detect_anomaly(self, did: str, anomaly_type: str, details: str, 
                      severity: AnomalySeverity = AnomalySeverity.MEDIUM):
        """Log agent anomaly with severity-based classification and automatic deactivation"""
        timestamp = self.timestamp()
        anomaly = {
            "timestamp": timestamp,
            "did": did,
            "type": anomaly_type,
            "details": details,
            "severity": severity.value,
            "hash": self.sha256(f"{timestamp}|{did}|{anomaly_type}|{details}|{severity.value}")
        }
        
        with self._file_lock:
            with open(self.anomalies_file, 'a') as f:
                f.write(f"{json.dumps(anomaly)}\n")
        
        # Update agent anomaly count and check for automatic deactivation
        registry = self.load_registry()
        if did in registry["agents"]:
            agent = registry["agents"][did]
            agent["anomaly_count"] = agent.get("anomaly_count", 0) + 1
            
            # Automatic deactivation for critical issues
            if severity == AnomalySeverity.CRITICAL:
                agent["status"] = "deactivated"
                agent["deactivated_at"] = timestamp
                agent["deactivation_reason"] = f"Critical anomaly: {anomaly_type}"
                self.logger.warning(f"Agent {did} automatically deactivated due to critical anomaly")
            
            # Deactivate after multiple high-severity issues
            elif severity == AnomalySeverity.HIGH and agent["anomaly_count"] >= 3:
                agent["status"] = "deactivated" 
                agent["deactivated_at"] = timestamp
                agent["deactivation_reason"] = "Multiple high-severity anomalies"
                self.logger.warning(f"Agent {did} automatically deactivated due to repeated high-severity anomalies")
            
            self.save_registry(registry)
        
        self.logger.info(f"Anomaly logged for {did}: {anomaly_type} (severity: {severity.value})")
        return anomaly
    
    def verify_agent_identity(self, did: str) -> bool:
        """Verify agent's cryptographic identity"""
        agent = self.get_agent(did)
        if not agent or "cryptographic_identity" not in agent:
            return False
        
        # Load public key
        _, public_key_pem = self.load_keys(did)
        if not public_key_pem:
            return False
        
        # Verify public key hash
        expected_hash = self.sha256(public_key_pem.decode('utf-8'))
        if expected_hash != agent["cryptographic_identity"]["public_key_hash"]:
            return False
        
        # Verify identity signature
        try:
            identity_message = f"{did}|{agent['created_at']}|{agent['cryptographic_identity']['public_key_hash']}"
            signature = bytes.fromhex(agent["cryptographic_identity"]["identity_signature"])
            return self.verify_signature(identity_message, signature, public_key_pem)
        except Exception as e:
            self.logger.error(f"Identity verification failed for {did}: {e}")
            return False
    
    def validate_agent_data_integrity(self, did: str) -> Dict[str, Any]:
        """Validate integrity of agent data with hash verification"""
        agent = self.get_agent(did)
        if not agent:
            return {"valid": False, "error": "Agent not found"}
        
        # Validate creation hash
        expected_creation_hash = self.sha256(f"{did}|{agent['skills']}|{agent['created_at']}")
        creation_hash_valid = agent["metadata"]["creation_hash"] == expected_creation_hash
        
        # Verify cryptographic identity
        identity_valid = self.verify_agent_identity(did)
        
        # Create integrity record
        integrity_result = {
            "did": did,
            "verified_at": self.timestamp(),
            "creation_hash_valid": creation_hash_valid,
            "identity_valid": identity_valid,
            "overall_valid": creation_hash_valid and identity_valid
        }
        
        # Log integrity check
        with self._file_lock:
            with open(self.integrity_log, 'a') as f:
                f.write(f"{json.dumps(integrity_result)}\n")
        
        return integrity_result
    
    def add_task_to_history(self, did: str, task_id: str, task_type: str, success: bool, latency: float):
        """Add task to agent's history with limited buffer size"""
        task_record = {
            "task_id": task_id,
            "task_type": task_type,
            "timestamp": self.timestamp(),
            "success": success,
            "latency": latency,
            "did": did
        }
        
        # Add to global history buffer
        self.task_history.append(task_record)
        
        # Update agent's individual task history
        registry = self.load_registry()
        if did in registry["agents"]:
            agent = registry["agents"][did]
            if "task_history" not in agent:
                agent["task_history"] = []
            
            agent["task_history"].append(task_record)
            
            # Limit individual agent history size
            if len(agent["task_history"]) > 100:  # Keep last 100 tasks per agent
                agent["task_history"] = agent["task_history"][-100:]
            
            self.save_registry(registry)
    
    def get_active_agents(self) -> List[Dict[str, Any]]:
        """Get list of active agents"""
        registry = self.load_registry()
        return [agent for agent in registry["agents"].values() if agent["status"] == "active"]
    
    def get_agents_by_skill(self, skill: str) -> List[Dict[str, Any]]:
        """Get agents that have a specific skill"""
        registry = self.load_registry()
        return [agent for agent in registry["agents"].values() 
                if skill in agent["skills"] and agent["status"] == "active"]
    
    def reactivate_agent(self, did: str, reason: str = "Manual reactivation") -> bool:
        """Reactivate a deactivated agent"""
        registry = self.load_registry()
        if did in registry["agents"]:
            agent = registry["agents"][did]
            if agent["status"] == "deactivated":
                agent["status"] = "active"
                agent["reactivated_at"] = self.timestamp()
                agent["reactivation_reason"] = reason
                agent["anomaly_count"] = 0  # Reset anomaly count
                
                self.save_registry(registry)
                self.log_heartbeat(did, "AGENT_REACTIVATED")
                self.logger.info(f"Agent {did} reactivated: {reason}")
                return True
        return False
    
    def get_agent_statistics(self, did: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive statistics for an agent"""
        agent = self.get_agent(did)
        if not agent:
            return None
        
        # Calculate additional statistics
        from datetime import timezone
        now = datetime.now(timezone.utc)
        recent_tasks = [t for t in agent.get("task_history", []) 
                       if (now - datetime.fromisoformat(t["timestamp"].replace('Z', '+00:00'))).days < 7]
        
        stats = {
            "did": did,
            "basic_stats": {
                "total_tasks": agent["total_tasks"],
                "successful_tasks": agent["successful_tasks"],
                "reliability_score": agent["reliability_score"],
                "average_latency": agent["average_latency"]
            },
            "recent_activity": {
                "tasks_last_7_days": len(recent_tasks),
                "success_rate_last_7_days": sum(1 for t in recent_tasks if t["success"]) / len(recent_tasks) if recent_tasks else 0,
                "last_activity": agent.get("last_activity", agent["last_heartbeat"])
            },
            "security": {
                "identity_verified": self.verify_agent_identity(did),
                "anomaly_count": agent.get("anomaly_count", 0)
            },
            "status": {
                "current_status": agent["status"],
                "created_at": agent["created_at"],
                "last_heartbeat": agent["last_heartbeat"]
            }
        }
        
        return stats
    
    def create_provenance_record(self, did: str, action: str, details: Dict[str, Any]) -> str:
        """Create a provenance record for audit trails"""
        timestamp = self.timestamp()
        
        # Load private key for signing
        private_key_pem, _ = self.load_keys(did)
        
        provenance_record = {
            "did": did,
            "timestamp": timestamp,
            "action": action,
            "details": details,
            "record_hash": None,
            "signature": None
        }
        
        # Create record hash
        record_data = f"{did}|{timestamp}|{action}|{json.dumps(details, sort_keys=True)}"
        provenance_record["record_hash"] = self.sha256(record_data)
        
        # Sign the record if private key is available
        if private_key_pem:
            signature = self.sign_message(record_data, private_key_pem)
            provenance_record["signature"] = signature.hex()
        
        # Store provenance record
        provenance_file = self.agents_dir / f"{did}_provenance.log"
        with self._file_lock:
            with open(provenance_file, 'a') as f:
                f.write(f"{json.dumps(provenance_record)}\n")
        
        return provenance_record["record_hash"]

# Enhanced CLI interface with subcommands for agent management
def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced EPOCH5 Agent Management System with Cryptographic Identity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create --skills python ai --type worker
  %(prog)s list --active-only
  %(prog)s verify --did did:epoch5:agent:abc123
  %(prog)s anomaly --did did:epoch5:agent:abc123 --type performance --severity high --details "High latency detected"
  %(prog)s stats --did did:epoch5:agent:abc123
        """
    )
    
    # Add base directory option
    parser.add_argument("--base-dir", default="./archive/EPOCH5", 
                       help="Base directory for EPOCH5 data storage")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create agent subcommand
    create_parser = subparsers.add_parser("create", help="Create a new agent")
    create_parser.add_argument("--skills", nargs="+", required=True, 
                              help="Agent skills")
    create_parser.add_argument("--type", default="agent", 
                              help="Agent type (default: agent)")
    
    # List agents subcommand
    list_parser = subparsers.add_parser("list", help="List agents")
    list_parser.add_argument("--active-only", action="store_true",
                            help="Show only active agents")
    list_parser.add_argument("--skill", help="Filter by skill")
    list_parser.add_argument("--format", choices=["table", "json"], default="table",
                            help="Output format")
    
    # Heartbeat subcommand
    heartbeat_parser = subparsers.add_parser("heartbeat", help="Log agent heartbeat")
    heartbeat_parser.add_argument("--did", required=True, help="Agent DID")
    heartbeat_parser.add_argument("--status", default="HEARTBEAT", help="Status message")
    
    # Anomaly subcommand
    anomaly_parser = subparsers.add_parser("anomaly", help="Log agent anomaly")
    anomaly_parser.add_argument("--did", required=True, help="Agent DID")
    anomaly_parser.add_argument("--type", required=True, help="Anomaly type")
    anomaly_parser.add_argument("--details", required=True, help="Anomaly details")
    anomaly_parser.add_argument("--severity", choices=["low", "medium", "high", "critical"],
                               default="medium", help="Anomaly severity")
    
    # Verify subcommand
    verify_parser = subparsers.add_parser("verify", help="Verify agent identity and integrity")
    verify_parser.add_argument("--did", required=True, help="Agent DID")
    
    # Statistics subcommand
    stats_parser = subparsers.add_parser("stats", help="Get agent statistics")
    stats_parser.add_argument("--did", required=True, help="Agent DID")
    
    # Update stats subcommand
    update_parser = subparsers.add_parser("update-stats", help="Update agent task statistics")
    update_parser.add_argument("--did", required=True, help="Agent DID")
    update_parser.add_argument("--success", action="store_true", help="Task was successful")
    update_parser.add_argument("--latency", type=float, required=True, help="Task latency in seconds")
    update_parser.add_argument("--task-id", help="Task identifier")
    update_parser.add_argument("--task-type", default="generic", help="Task type")
    
    # Reactivate subcommand
    reactivate_parser = subparsers.add_parser("reactivate", help="Reactivate deactivated agent")
    reactivate_parser.add_argument("--did", required=True, help="Agent DID")
    reactivate_parser.add_argument("--reason", default="Manual reactivation", help="Reactivation reason")
    
    # Provenance subcommand
    provenance_parser = subparsers.add_parser("provenance", help="Create provenance record")
    provenance_parser.add_argument("--did", required=True, help="Agent DID")
    provenance_parser.add_argument("--action", required=True, help="Action performed")
    provenance_parser.add_argument("--details", required=True, help="Action details (JSON string)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        manager = AgentManager(args.base_dir)
        
        if args.command == "create":
            agent = manager.create_agent(args.skills, args.type)
            manager.register_agent(agent)
            print(f"✓ Created agent: {agent['did']}")
            print(f"  Type: {agent['type']}")
            print(f"  Skills: {', '.join(agent['skills'])}")
            print(f"  Cryptographic identity established")
            
        elif args.command == "list":
            registry = manager.load_registry()
            agents = list(registry['agents'].values())
            
            if args.active_only:
                agents = [a for a in agents if a['status'] == 'active']
            
            if args.skill:
                agents = [a for a in agents if args.skill in a['skills']]
            
            if args.format == "json":
                print(json.dumps(agents, indent=2))
            else:
                print(f"Agent Registry ({len(agents)} agents):")
                print("-" * 80)
                for agent in agents:
                    status_icon = "✓" if agent['status'] == 'active' else "✗"
                    print(f"{status_icon} {agent['did']}")
                    print(f"    Type: {agent['type']} | Skills: {', '.join(agent['skills'])}")
                    print(f"    Reliability: {agent['reliability_score']:.2f} | Tasks: {agent['total_tasks']}")
                    print(f"    Status: {agent['status']} | Anomalies: {agent.get('anomaly_count', 0)}")
                    print()
        
        elif args.command == "heartbeat":
            manager.log_heartbeat(args.did, args.status)
            print(f"✓ Heartbeat logged for {args.did}: {args.status}")
        
        elif args.command == "anomaly":
            severity = AnomalySeverity(args.severity)
            anomaly = manager.detect_anomaly(args.did, args.type, args.details, severity)
            print(f"✓ Anomaly logged: {anomaly['hash']}")
            print(f"  DID: {args.did}")
            print(f"  Type: {args.type}")
            print(f"  Severity: {args.severity}")
            if severity == AnomalySeverity.CRITICAL:
                print("  ⚠️  Agent automatically deactivated due to critical severity")
        
        elif args.command == "verify":
            integrity_result = manager.validate_agent_data_integrity(args.did)
            identity_valid = manager.verify_agent_identity(args.did)
            
            print(f"Agent Verification Report for {args.did}")
            print("-" * 50)
            print(f"Creation hash valid: {'✓' if integrity_result.get('creation_hash_valid', False) else '✗'}")
            print(f"Identity valid: {'✓' if identity_valid else '✗'}")
            print(f"Overall integrity: {'✓' if integrity_result.get('overall_valid', False) else '✗'}")
            print(f"Verified at: {integrity_result.get('verified_at', 'N/A')}")
        
        elif args.command == "stats":
            stats = manager.get_agent_statistics(args.did)
            if stats:
                print(f"Agent Statistics for {args.did}")
                print("-" * 50)
                print(f"Total tasks: {stats['basic_stats']['total_tasks']}")
                print(f"Successful tasks: {stats['basic_stats']['successful_tasks']}")
                print(f"Reliability score: {stats['basic_stats']['reliability_score']:.3f}")
                print(f"Average latency: {stats['basic_stats']['average_latency']:.3f}s")
                print(f"Tasks (last 7 days): {stats['recent_activity']['tasks_last_7_days']}")
                print(f"Success rate (last 7 days): {stats['recent_activity']['success_rate_last_7_days']:.3f}")
                print(f"Identity verified: {'✓' if stats['security']['identity_verified'] else '✗'}")
                print(f"Anomaly count: {stats['security']['anomaly_count']}")
                print(f"Current status: {stats['status']['current_status']}")
            else:
                print(f"✗ Agent not found: {args.did}")
        
        elif args.command == "update-stats":
            success = manager.update_agent_stats(
                args.did, args.success, args.latency, args.task_id, args.task_type
            )
            if success:
                print(f"✓ Updated statistics for {args.did}")
                print(f"  Task success: {args.success}")
                print(f"  Latency: {args.latency}s")
            else:
                print(f"✗ Failed to update statistics for {args.did}")
        
        elif args.command == "reactivate":
            success = manager.reactivate_agent(args.did, args.reason)
            if success:
                print(f"✓ Reactivated agent: {args.did}")
                print(f"  Reason: {args.reason}")
            else:
                print(f"✗ Failed to reactivate agent: {args.did}")
        
        elif args.command == "provenance":
            try:
                details = json.loads(args.details)
                record_hash = manager.create_provenance_record(args.did, args.action, details)
                print(f"✓ Provenance record created: {record_hash}")
                print(f"  DID: {args.did}")
                print(f"  Action: {args.action}")
            except json.JSONDecodeError:
                print(f"✗ Invalid JSON in details: {args.details}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()