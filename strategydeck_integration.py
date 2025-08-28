"""
Integration module connecting StrategyDECKAgent with EPOCH5 Agent Management system.
This enables the StrategyDECKAgent to be registered, monitored, and managed within
the EPOCH5 ecosystem.

Features:
- Agent registration with EPOCH5 Agent Management
- Heartbeat monitoring for agent health tracking
- Continuous improvement system integration
- Agent messaging and command handling (via agent_monitor.py)
- Performance tracking and reporting
- Security features including audit logging and ceiling enforcement
"""

import os
import time
import json
import uuid
import logging
import threading
import traceback
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
from pathlib import Path

# Import EPOCH5 components
from agent_management import AgentManager
from strategydeck_agent import StrategyDECKAgent
from strategydeck_improvement import ContinuousImprovementSystem

# Try to import agent_monitor for messaging capabilities
try:
    from agent_monitor import AgentMessage
    AGENT_MONITOR_AVAILABLE = True
except ImportError:
    AGENT_MONITOR_AVAILABLE = False

# Try to import security components
try:
    from epoch_audit import EpochAudit
    from agent_security import AgentSecurityController
    SECURITY_SYSTEM_AVAILABLE = True
except ImportError:
    SECURITY_SYSTEM_AVAILABLE = False


class StrategyDECKAgentIntegration:
    """
    Integration layer between StrategyDECKAgent and EPOCH5 Agent Management.
    Provides registration, heartbeat monitoring, and performance tracking.
    """
    
    def __init__(self, 
                base_dir: str = "./archive/EPOCH5",
                agent_name: Optional[str] = None,
                log_level: int = logging.INFO,
                max_workers: int = 4,
                enable_continuous_improvement: bool = True,
                enable_security: bool = True):
        """
        Initialize the integration layer.
        
        Args:
            base_dir: Base directory for EPOCH5 systems
            agent_name: Optional custom name for the agent (default: auto-generated)
            log_level: Logging level
            max_workers: Maximum number of concurrent workers
            enable_continuous_improvement: Whether to enable the continuous improvement system
            enable_security: Whether to enable security features
        """
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs" / "strategydeck"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logger
        self.logger = logging.getLogger("StrategyDECKIntegration")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Add file handler
            file_handler = logging.FileHandler(
                self.logs_dir / f"integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Initialize EPOCH5 Agent Manager
        self.agent_manager = AgentManager(base_dir)
        
        # Generate a unique name if not provided
        self.agent_name = agent_name or f"StrategyDECK_{uuid.uuid4().hex[:8]}"
        
        # Initialize StrategyDECKAgent
        self.agent = StrategyDECKAgent(
            name=self.agent_name,
            log_dir=str(self.logs_dir),
            log_level=log_level,
            max_workers=max_workers
        )
        
        # Initialize Continuous Improvement System if enabled
        self.improvement_system = None
        if enable_continuous_improvement:
            self.improvement_system = ContinuousImprovementSystem(
                base_dir=base_dir,
                log_level=log_level
            )
            # Start the continuous improvement cycle
            self.improvement_system.start_improvement_cycle()
            self.logger.info("Continuous Improvement System enabled and started")
        
        # Initialize Security System if enabled and available
        self.security_system = None
        self.audit_system = None
        if enable_security and SECURITY_SYSTEM_AVAILABLE:
            self.audit_system = EpochAudit(base_dir)
            self.security_system = AgentSecurityController(base_dir)
            self.logger.info("Security System enabled and initialized")
            
            # Log initialization in audit system
            self.audit_system.log_event(
                "strategydeck_init", 
                f"StrategyDECK Integration initialized for agent '{self.agent_name}'",
                {"agent_name": self.agent_name, "max_workers": max_workers}
            )
        
        # Store agent DID after registration
        self.agent_did = None
        
        # Setup messaging system if available
        self.message_handler_thread = None
        self.running = True
        self.inbox_path = self.base_dir / "messages" / "inbox"
        self.outbox_path = self.base_dir / "messages" / "outbox"
        
        # Create message directories if they don't exist
        if AGENT_MONITOR_AVAILABLE:
            self.inbox_path.parent.mkdir(parents=True, exist_ok=True)
            self.inbox_path.mkdir(exist_ok=True)
            self.outbox_path.mkdir(exist_ok=True)
            
            # Register command handlers
            self.command_handlers = {
                "status": self._handle_status_command,
                "execute_strategy": self._handle_execute_strategy_command,
                "pause": self._handle_pause_command,
                "resume": self._handle_resume_command,
                "shutdown": self._handle_shutdown_command,
                "health_check": self._handle_health_check_command,
                "run_improvement_cycle": self._handle_run_improvement_cycle_command,
                # Add security-related command handlers
                "security_status": self._handle_security_status_command,
                "verify_integrity": self._handle_verify_integrity_command,
                "run_audit": self._handle_run_audit_command,
            }
        
        self.logger.info(f"StrategyDECK Integration initialized with agent '{self.agent_name}'")
    
    def register_agent(self) -> str:
        """
        Register the StrategyDECKAgent with EPOCH5 Agent Management.
        
        Returns:
            The agent's DID (Decentralized Identifier)
        """
        # Define agent skills
        skills = ["strategy_automation", "workflow_optimization", "resource_management"]
        
        # Create agent in EPOCH5 registry
        agent_record = self.agent_manager.create_agent(
            skills=skills,
            agent_type="strategydeck"
        )
        
        # Register agent
        self.agent_manager.register_agent(agent_record)
        self.agent_did = agent_record["did"]
        
        self.logger.info(f"Agent registered with DID: {self.agent_did}")
        self.logger.info(f"Agent skills: {', '.join(skills)}")
        
        # Log registration in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "agent_registration", 
                f"StrategyDECK Agent registered with DID: {self.agent_did}",
                {"agent_did": self.agent_did, "skills": skills}
            )
        
        # Start heartbeat and message handler
        self.start_heartbeat_monitoring()
        self.start_message_handler()
        
        return self.agent_did
    
    def start_message_handler(self):
        """
        Start the message handling thread to process incoming messages
        """
        if not AGENT_MONITOR_AVAILABLE:
            self.logger.warning("Agent monitor module not available, messaging disabled")
            return False
        
        if not self.agent_did:
            self.logger.warning("Agent not registered, cannot start message handler")
            return False
        
        # Start message handler thread
        self.message_handler_thread = threading.Thread(target=self._message_handler_loop)
        self.message_handler_thread.daemon = True
        self.message_handler_thread.start()
        
        self.logger.info("Message handler started")
        
        # Log in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "message_handler_start", 
                f"Message handler started for agent {self.agent_did}"
            )
        
        return True
    
    def _message_handler_loop(self):
        """Background thread for processing incoming messages"""
        try:
            while self.running:
                try:
                    # Check for messages addressed to this agent
                    self._process_messages()
                    
                    # Sleep to avoid high CPU usage
                    time.sleep(2)
                    
                except Exception as e:
                    self.logger.error(f"Error in message handler: {str(e)}")
                    self.logger.debug(traceback.format_exc())
                    
                    # Log error in audit system
                    if self.audit_system:
                        self.audit_system.log_event(
                            "message_handler_error", 
                            f"Error in message handler: {str(e)}",
                            {"error": str(e), "traceback": traceback.format_exc()}
                        )
        
        except Exception as e:
            self.logger.error(f"Fatal error in message handler thread: {str(e)}")
            self.logger.error(traceback.format_exc())
            
            # Log fatal error in audit system
            if self.audit_system:
                self.audit_system.log_event(
                    "message_handler_fatal", 
                    f"Fatal error in message handler: {str(e)}",
                    {"error": str(e), "traceback": traceback.format_exc()}
                )
    
    def _process_messages(self):
        """Process incoming messages from the outbox directory"""
        if not self.agent_did:
            return
        
        # Look for messages addressed to this agent
        for file_path in self.outbox_path.glob(f"{self.agent_did}_*.json"):
            try:
                with open(file_path, "r") as f:
                    message_data = json.load(f)
                
                # Log message received in audit system
                if self.audit_system:
                    message_type = message_data.get("message_type", "unknown")
                    message_id = message_data.get("message_id", "unknown")
                    self.audit_system.log_event(
                        "message_received", 
                        f"Received {message_type} message (ID: {message_id})",
                        {"message_id": message_id, "message_type": message_type}
                    )
                
                # Apply rate limiting if security system is available
                if self.security_system and self.agent_did:
                    if not self.security_system.check_rate_limit(self.agent_did, "message"):
                        self.logger.warning(f"Message rate limit exceeded, skipping message")
                        continue
                
                # Process message
                self._handle_message(message_data)
                
                # Archive or delete message after processing
                file_path.unlink()
                
            except Exception as e:
                self.logger.error(f"Error processing message {file_path}: {str(e)}")
                
                # Log error in audit system
                if self.audit_system:
                    self.audit_system.log_event(
                        "message_processing_error", 
                        f"Error processing message {file_path}: {str(e)}",
                        {"error": str(e), "file_path": str(file_path)}
                    )
    
    def _handle_message(self, message_data: Dict[str, Any]):
        """Handle an incoming message"""
        if "message_type" not in message_data or "content" not in message_data:
            self.logger.warning(f"Invalid message format: {message_data}")
            return
        
        message_type = message_data["message_type"]
        content = message_data["content"]
        message_id = message_data.get("message_id", "unknown")
        
        self.logger.info(f"Received {message_type} message (ID: {message_id})")
        
        # Handle different message types
        if message_type == "command":
            self._handle_command(message_id, content)
        elif message_type == "task":
            self._handle_task(message_id, content)
        elif message_type == "query":
            self._handle_query(message_id, content)
        elif message_type == "notification":
            self.logger.info(f"Notification: {content.get('message', 'No message')}")
        else:
            self.logger.warning(f"Unknown message type: {message_type}")
            
            # Log unknown message type in audit system
            if self.audit_system:
                self.audit_system.log_event(
                    "unknown_message_type", 
                    f"Unknown message type: {message_type}",
                    {"message_id": message_id, "message_type": message_type}
                )
    
    def _handle_command(self, message_id: str, content: Dict[str, Any]):
        """Handle a command message"""
        command = content.get("command", "")
        parameters = content.get("parameters", {})
        
        self.logger.info(f"Executing command: {command}")
        
        # Log command in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "command_received", 
                f"Executing command: {command}",
                {"message_id": message_id, "command": command, "parameters": parameters}
            )
        
        # Apply security checks and ceiling enforcement if security system is available
        if self.security_system and command == "execute_strategy" and "priority" in parameters:
            # Enforce ceiling on task priority
            parameters = self.security_system.enforce_task_priority(parameters, self.agent_did)
        
        # Execute command if handler exists
        if command in self.command_handlers:
            try:
                result = self.command_handlers[command](parameters)
                
                # Log command success in audit system
                if self.audit_system:
                    self.audit_system.log_event(
                        "command_success", 
                        f"Command {command} executed successfully",
                        {"message_id": message_id, "command": command, "status": "success"}
                    )
                
                self._send_response(message_id, "command_result", {
                    "command": command,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                self.logger.error(f"Error executing command {command}: {str(e)}")
                
                # Log command error in audit system
                if self.audit_system:
                    self.audit_system.log_event(
                        "command_error", 
                        f"Error executing command {command}: {str(e)}",
                        {"message_id": message_id, "command": command, "error": str(e)}
                    )
                
                self._send_response(message_id, "command_result", {
                    "command": command,
                    "status": "error",
                    "error_message": str(e)
                })
        else:
            self.logger.warning(f"Unknown command: {command}")
            
            # Log unknown command in audit system
            if self.audit_system:
                self.audit_system.log_event(
                    "unknown_command", 
                    f"Unknown command: {command}",
                    {"message_id": message_id, "command": command}
                )
            
            self._send_response(message_id, "command_result", {
                "command": command,
                "status": "error",
                "error_message": f"Unknown command: {command}"
            })
    
    def _handle_task(self, message_id: str, content: Dict[str, Any]):
        """Handle a task message"""
        self.logger.info(f"Received task: {content}")
        
        # Log task in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "task_received", 
                f"Received task: {content.get('goal', 'Unknown')}",
                {"message_id": message_id, "task": content}
            )
        
        # Apply ceiling enforcement to task parameters if security system is available
        if self.security_system:
            if "priority" in content:
                content = self.security_system.enforce_task_priority(content, self.agent_did)
            
            if "resources" in content:
                content["resources"] = self.security_system.enforce_resource_allocation(
                    content["resources"], self.agent_did
                )
        
        # Execute strategy based on task content
        try:
            result = self.execute_strategy(content)
            
            # Log task success in audit system
            if self.audit_system:
                task_status = result.get("status", "error")
                self.audit_system.log_event(
                    "task_completed", 
                    f"Task completed with status: {task_status}",
                    {"message_id": message_id, "status": task_status}
                )
            
            # Send result back
            self._send_response(message_id, "task_result", {
                "task_id": message_id,
                "status": result.get("status", "error"),
                "result": result
            })
            
        except Exception as e:
            self.logger.error(f"Error executing task: {str(e)}")
            
            # Log task error in audit system
            if self.audit_system:
                self.audit_system.log_event(
                    "task_error", 
                    f"Error executing task: {str(e)}",
                    {"message_id": message_id, "error": str(e)}
                )
            
            self._send_response(message_id, "task_result", {
                "task_id": message_id,
                "status": "error",
                "error_message": str(e)
            })
    
    def _handle_query(self, message_id: str, content: Dict[str, Any]):
        """Handle a query message"""
        query_id = content.get("query_id", "unknown")
        query_type = content.get("query_type", "")
        parameters = content.get("parameters", {})
        
        self.logger.info(f"Received query: {query_type} (ID: {query_id})")
        
        # Log query in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "query_received", 
                f"Received query: {query_type} (ID: {query_id})",
                {"message_id": message_id, "query_type": query_type, "query_id": query_id}
            )
        
        # Process different query types
        response = {"query_id": query_id, "query_type": query_type}
        
        if query_type == "status":
            response["response"] = self.get_agent_status()
        elif query_type == "capabilities":
            response["response"] = self._get_agent_capabilities()
        elif query_type == "improvement_stats":
            if self.improvement_system:
                response["response"] = self.improvement_system.get_improvement_stats()
            else:
                response["response"] = {"error": "Improvement system not enabled"}
        elif query_type == "task_history":
            response["response"] = self.agent.get_task_history()
        elif query_type == "security_status" and self.security_system:
            # New query type for security status
            response["response"] = self.get_security_status()
        elif query_type == "audit_events" and self.audit_system:
            # New query type for audit events
            event_types = parameters.get("event_types", None)
            limit = parameters.get("limit", 50)
            response["response"] = {
                "events": self.audit_system.generate_audit_scroll(
                    event_types=event_types,
                    limit=limit
                )
            }
        else:
            response["response"] = {"error": f"Unknown query type: {query_type}"}
            
            # Log unknown query type in audit system
            if self.audit_system:
                self.audit_system.log_event(
                    "unknown_query_type", 
                    f"Unknown query type: {query_type}",
                    {"message_id": message_id, "query_type": query_type}
                )
        
        # Send response
        self._send_response(message_id, "query_response", response)
    
    def _send_response(self, original_message_id: str, response_type: str, content: Dict[str, Any]):
        """Send a response message"""
        if not AGENT_MONITOR_AVAILABLE or not self.agent_did:
            return
        
        # Create response message
        message = AgentMessage(
            message_type=response_type,
            content=content,
            sender=self.agent_did
        )
        
        # Save to inbox
        message_file = self.inbox_path / f"response_{original_message_id}_{message.message_id}.json"
        with open(message_file, "w") as f:
            json.dump(message.to_dict(), f, indent=2)
        
        self.logger.debug(f"Sent {response_type} response for message {original_message_id}")
        
        # Log response in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "response_sent", 
                f"Sent {response_type} response for message {original_message_id}",
                {"original_message_id": original_message_id, "response_type": response_type, "message_id": message.message_id}
            )
    
    def get_security_status(self) -> Dict[str, Any]:
        """
        Get the current security status for the agent
        
        Returns:
            Security status information
        """
        if not self.security_system or not self.audit_system:
            return {"status": "unavailable", "message": "Security system not enabled"}
        
        # Get verification status if agent is registered
        verification = None
        if self.agent_did:
            verification = self.security_system.verify_agent_integrity(self.agent_did)
        
        # Check seal verification
        seal_verification = self.audit_system.verify_seals(max_events=50)
        
        # Generate hash of agent's current state for integrity check
        agent_state = {
            "agent_name": self.agent_name,
            "agent_did": self.agent_did,
            "running": self.running,
            "metrics": self.agent.health_check()["metrics"]
        }
        
        state_hash = hashlib.sha256(json.dumps(agent_state, sort_keys=True).encode()).hexdigest()
        
        # Create comprehensive security status
        security_status = {
            "status": verification["status"] if verification else "unverified",
            "agent_integrity": verification if verification else {"status": "unverified"},
            "audit_integrity": {
                "status": seal_verification["status"],
                "verified_count": seal_verification["verified_count"],
                "valid_count": seal_verification["valid_count"],
                "invalid_count": seal_verification["invalid_count"]
            },
            "agent_state_hash": state_hash,
            "security_features": {
                "audit_logging": True,
                "ceiling_enforcement": True,
                "integrity_verification": True,
                "rate_limiting": True
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return security_status
        
    def send_status_update(self):
        """Send a status update message to the monitoring system"""
        if not AGENT_MONITOR_AVAILABLE or not self.agent_did:
            return
        
        # Create status update message
        status = self.get_agent_status()
        message = AgentMessage(
            message_type="status_update",
            content=status,
            sender=self.agent_did
        )
        
        # Save to inbox
        message_file = self.inbox_path / f"status_{self.agent_did}_{int(time.time())}.json"
        with open(message_file, "w") as f:
            json.dump(message.to_dict(), f, indent=2)
        
        self.logger.debug("Sent status update")
    
    def _get_agent_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities"""
        capabilities = {
            "commands": list(self.command_handlers.keys()),
            "skills": [],
            "features": {
                "continuous_improvement": self.improvement_system is not None,
                "security_features": self.security_system is not None,
                "audit_logging": self.audit_system is not None,
                "concurrent_execution": True,
                "task_retry": True,
                "timeout_control": True
            }
        }
        
        # Get skills from registry
        if self.agent_did:
            agent_record = self.agent_manager.get_agent(self.agent_did)
            if agent_record:
                capabilities["skills"] = agent_record.get("skills", [])
        
        return capabilities
    
    # Command handlers
    def _handle_status_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status command"""
        detailed = parameters.get("detailed", False)
        
        if detailed:
            return self.get_agent_status()
        else:
            return {
                "status": "running" if self.running else "stopped",
                "agent_did": self.agent_did,
                "agent_name": self.agent_name
            }
    
    def _handle_execute_strategy_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execute_strategy command"""
        # Apply ceiling enforcement to parameters if security system is available
        if self.security_system and "priority" in parameters:
            parameters = self.security_system.enforce_task_priority(parameters, self.agent_did)
        
        # Execute strategy
        result = self.execute_strategy(parameters)
        return result
    
    def _handle_pause_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pause command"""
        timeout = parameters.get("timeout", 0)
        
        self.agent.pause()
        
        # Log pause in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "agent_paused", 
                f"Agent {self.agent_did} paused" + (f" with {timeout}s timeout" if timeout > 0 else ""),
                {"agent_did": self.agent_did, "timeout": timeout}
            )
        
        if timeout > 0:
            # Start a timer to resume after timeout
            def resume_after_timeout():
                time.sleep(timeout)
                self.agent.resume()
                self.logger.info(f"Agent resumed after {timeout}s timeout")
                
                # Log resume in audit system
                if self.audit_system:
                    self.audit_system.log_event(
                        "agent_resumed", 
                        f"Agent {self.agent_did} automatically resumed after timeout",
                        {"agent_did": self.agent_did, "timeout": timeout}
                    )
            
            threading.Thread(target=resume_after_timeout, daemon=True).start()
            return {"status": "paused", "auto_resume_after": timeout}
        
        return {"status": "paused"}
    
    def _handle_resume_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resume command"""
        self.agent.resume()
        
        # Log resume in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "agent_resumed", 
                f"Agent {self.agent_did} resumed",
                {"agent_did": self.agent_did}
            )
        
        return {"status": "resumed"}
    
    def _handle_shutdown_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shutdown command"""
        force = parameters.get("force", False)
        timeout = parameters.get("timeout", 0)
        
        if force:
            # Log shutdown in audit system
            if self.audit_system:
                self.audit_system.log_event(
                    "agent_shutdown_initiated", 
                    f"Agent {self.agent_did} shutdown initiated" + (f" with {timeout}s timeout" if timeout > 0 else ""),
                    {"agent_did": self.agent_did, "force": force, "timeout": timeout}
                )
            
            # Schedule shutdown
            def delayed_shutdown():
                time.sleep(max(0, timeout))
                self.running = False
                self.shutdown()
            
            threading.Thread(target=delayed_shutdown, daemon=True).start()
            return {"status": "shutdown_initiated", "force": True, "timeout": timeout}
        else:
            return {"status": "shutdown_requested", "message": "Use force=True to confirm shutdown"}
    
    def _handle_health_check_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health_check command"""
        health_data = self.agent.health_check()
        
        # Log health check in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "health_check", 
                f"Health check performed for agent {self.agent_did}",
                {"agent_did": self.agent_did, "health": health_data}
            )
        
        return health_data
    
    def _handle_run_improvement_cycle_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle run_improvement_cycle command"""
        if not self.improvement_system:
            return {"status": "error", "message": "Improvement system not enabled"}
        
        # Log improvement cycle in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "improvement_cycle", 
                f"Improvement cycle initiated for agent {self.agent_did}",
                {"agent_did": self.agent_did}
            )
        
        return self.improvement_system.run_improvement_cycle()
    
    # Security-related command handlers
    def _handle_security_status_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle security_status command"""
        return self.get_security_status()
    
    def _handle_verify_integrity_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle verify_integrity command"""
        if not self.security_system:
            return {"status": "error", "message": "Security system not enabled"}
        
        verification = self.security_system.verify_agent_integrity(self.agent_did)
        
        # Log verification in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "integrity_verification", 
                f"Integrity verification performed for agent {self.agent_did}: {verification['status']}",
                {"agent_did": self.agent_did, "verification_status": verification["status"]}
            )
        
        return verification
    
    def _handle_run_audit_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle run_audit command"""
        if not self.audit_system:
            return {"status": "error", "message": "Audit system not enabled"}
        
        event_types = parameters.get("event_types", None)
        limit = parameters.get("limit", 100)
        
        # Generate audit scroll
        events = self.audit_system.generate_audit_scroll(
            event_types=event_types,
            limit=limit
        )
        
        # Log audit generation in audit system
        self.audit_system.log_event(
            "audit_generation", 
            f"Audit scroll generated with {len(events)} events",
            {"event_count": len(events)}
        )
        
        return {
            "status": "success",
            "event_count": len(events),
            "events": events
        }
    
    def execute_strategy(self, strategy_data: Dict[str, Any], 
                        track_performance: bool = True) -> Dict[str, Any]:
        """
        Execute a strategy and track performance in EPOCH5.
        
        Args:
            strategy_data: Strategy data to process
            track_performance: Whether to track performance in EPOCH5
            
        Returns:
            The strategy execution result
        """
        if not self.agent_did:
            self.logger.warning("Agent not registered with EPOCH5. Registering now...")
            self.register_agent()
        
        start_time = time.time()
        success = False
        
        # Log strategy execution start in audit system
        if self.audit_system:
            goal = strategy_data.get('goal', 'unknown')
            self.audit_system.log_event(
                "strategy_execution_start", 
                f"Starting strategy execution: {goal}",
                {"agent_did": self.agent_did, "goal": goal}
            )
            
            # Apply ceiling enforcement to strategy priority if available
            if "priority" in strategy_data and self.security_system:
                strategy_data = self.security_system.enforce_task_priority(strategy_data, self.agent_did)
        
        # Apply continuous improvement recommendations if available
        if self.improvement_system:
            goal = strategy_data.get('goal', 'unknown')
            strategy_type = goal.split()[0].lower() if goal else 'default'
            
            # Get recommended strategy enhancements
            enhanced_data = self.improvement_system.get_strategy_recommendations(goal, strategy_data)
            
            # Get execution parameters (timeout, retries)
            execution_params = self.improvement_system.get_execution_parameters(strategy_type)
            
            self.logger.info(f"Applied continuous improvement recommendations for {strategy_type}")
            
            # Use the enhanced strategy data
            strategy_data = enhanced_data
        else:
            # Default execution parameters if improvement system is not available
            execution_params = {"timeout": 30.0, "retries": 2}
        
        try:
            # Execute strategy with recommended parameters
            result = self.agent.run_task(
                self.agent.automate_strategy, 
                strategy_data,
                **execution_params
            )
            
            if result and result.get("status") == "success":
                success = True
                self.logger.info(f"Strategy executed successfully: {result['goal_processed']}")
                
                # Record successful execution for continuous improvement
                if self.improvement_system:
                    self.improvement_system.record_execution(strategy_data, result)
                    
                # Log successful execution in audit system
                if self.audit_system:
                    self.audit_system.log_event(
                        "strategy_execution_success", 
                        f"Strategy executed successfully: {result['goal_processed']}",
                        {
                            "agent_did": self.agent_did, 
                            "goal": strategy_data.get('goal', 'unknown'),
                            "execution_time": time.time() - start_time
                        }
                    )
            else:
                self.logger.error("Strategy execution failed")
                
                # Record failed execution for continuous improvement
                if self.improvement_system and result:
                    result["status"] = "error"
                    self.improvement_system.record_execution(strategy_data, result)
                
                # Log failed execution in audit system
                if self.audit_system:
                    self.audit_system.log_event(
                        "strategy_execution_failure", 
                        f"Strategy execution failed: {strategy_data.get('goal', 'unknown')}",
                        {
                            "agent_did": self.agent_did, 
                            "goal": strategy_data.get('goal', 'unknown'),
                            "execution_time": time.time() - start_time,
                            "error": result.get("error", "Unknown error") if result else "No result"
                        }
                    )
                
            # Record performance in EPOCH5 if requested
            if track_performance and self.agent_did:
                latency = time.time() - start_time
                
                # Apply ceiling enforcement to latency if security system is available
                if self.audit_system:
                    latency_result = self.audit_system.enforce_ceiling(
                        "execution_time", latency, self.agent_did
                    )
                    if latency_result["capped"]:
                        self.logger.warning(f"Execution time capped: {latency_result['original_value']} → {latency_result['final_value']}")
                        latency = latency_result["final_value"]
                
                self.agent_manager.update_agent_stats(
                    self.agent_did,
                    success=success,
                    latency=latency
                )
                
                if not success:
                    # Log anomaly for failed execution
                    self.agent_manager.detect_anomaly(
                        self.agent_did,
                        "STRATEGY_FAILURE",
                        f"Failed to execute strategy: {strategy_data.get('goal', 'Unknown')}"
                    )
            
            return result if result else {"status": "error", "message": "Execution failed"}
            
        except Exception as e:
            self.logger.error(f"Error executing strategy: {str(e)}")
            
            # Log exception in audit system
            if self.audit_system:
                self.audit_system.log_event(
                    "strategy_execution_error", 
                    f"Error executing strategy: {str(e)}",
                    {
                        "agent_did": self.agent_did, 
                        "goal": strategy_data.get('goal', 'unknown'),
                        "execution_time": time.time() - start_time,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                )
            
            # Record failure in EPOCH5
            if track_performance and self.agent_did:
                latency = time.time() - start_time
                self.agent_manager.update_agent_stats(
                    self.agent_did,
                    success=False,
                    latency=latency
                )
                
                # Log anomaly for exception
                self.agent_manager.detect_anomaly(
                    self.agent_did,
                    "EXECUTION_ERROR",
                    f"Exception during strategy execution: {str(e)}"
                )
            
            return {"status": "error", "message": str(e)}
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get combined status from both StrategyDECKAgent and EPOCH5 registry.
        
        Returns:
            Combined status information
        """
        status = {
            "agent_health": self.agent.health_check(),
            "epoch5_integration": {
                "registered": self.agent_did is not None,
                "agent_did": self.agent_did
            }
        }
        
        # Add EPOCH5 registry information if available
        if self.agent_did:
            agent_record = self.agent_manager.get_agent(self.agent_did)
            if agent_record:
                status["epoch5_integration"]["registry_data"] = {
                    "reliability_score": agent_record["reliability_score"],
                    "average_latency": agent_record["average_latency"],
                    "total_tasks": agent_record["total_tasks"],
                    "successful_tasks": agent_record["successful_tasks"],
                    "last_heartbeat": agent_record["last_heartbeat"],
                    "status": agent_record["status"]
                }
        
        # Add continuous improvement status if enabled
        if self.improvement_system:
            status["continuous_improvement"] = self.improvement_system.get_improvement_stats()
        
        # Add security status if enabled
        if self.security_system:
            status["security"] = {
                "enabled": True,
                "audit_enabled": self.audit_system is not None
            }
            
            # Add integrity verification if agent is registered
            if self.agent_did:
                verification = self.security_system.verify_agent_integrity(self.agent_did)
                status["security"]["integrity"] = verification["status"]
        
        return status
    
    def run_improvement_cycle(self) -> Dict[str, Any]:
        """
        Manually trigger a continuous improvement cycle.
        
        Returns:
            Results of the improvement cycle
        """
        if not self.improvement_system:
            self.logger.error("Continuous improvement system is not enabled")
            return {"error": "Continuous improvement system is not enabled"}
        
        self.logger.info("Manually triggering improvement cycle")
        return self.improvement_system.run_improvement_cycle()
    
    def start_heartbeat_monitoring(self, interval_seconds: int = 60) -> None:
        """
        Start heartbeat monitoring in a separate thread.
        
        Args:
            interval_seconds: Interval between heartbeats
        """
        def heartbeat_thread():
            self.logger.info(f"Heartbeat monitoring started (interval: {interval_seconds}s)")
            
            # Log heartbeat start in audit system
            if self.audit_system:
                self.audit_system.log_event(
                    "heartbeat_monitoring_start", 
                    f"Heartbeat monitoring started for agent {self.agent_did} (interval: {interval_seconds}s)",
                    {"agent_did": self.agent_did, "interval": interval_seconds}
                )
            
            while self.running:
                try:
                    if self.agent_did:
                        # Log heartbeat in agent manager
                        self.agent_manager.log_heartbeat(self.agent_did)
                        
                        # Update agent stats based on current metrics
                        metrics = self.agent.health_check()["metrics"]
                        total_tasks = metrics["tasks_completed"] + metrics["tasks_failed"]
                        if total_tasks > 0:
                            success_rate = metrics["tasks_completed"] / total_tasks
                            
                            # Apply ceiling enforcement to latency if security system is available
                            latency = metrics["avg_task_duration"]
                            if self.audit_system:
                                latency_result = self.audit_system.enforce_ceiling(
                                    "execution_time", latency, self.agent_did
                                )
                                if latency_result["capped"]:
                                    self.logger.warning(f"Average task duration capped: {latency_result['original_value']} → {latency_result['final_value']}")
                                    latency = latency_result["final_value"]
                            
                            self.agent_manager.update_agent_stats(
                                self.agent_did,
                                success=True,  # Just logging a heartbeat, not a task result
                                latency=latency
                            )
                        
                        # Log heartbeat in audit system
                        if self.audit_system and random.random() < 0.2:  # Only log ~20% of heartbeats to avoid flooding
                            self.audit_system.log_event(
                                "agent_heartbeat", 
                                f"Heartbeat sent for agent {self.agent_did}",
                                {"agent_did": self.agent_did}
                            )
                            
                        self.logger.debug(f"Heartbeat sent for {self.agent_did}")
                        
                        # Send status update to monitoring system
                        if AGENT_MONITOR_AVAILABLE:
                            self.send_status_update()
                except Exception as e:
                    self.logger.error(f"Error in heartbeat: {str(e)}")
                    
                    # Log heartbeat error in audit system
                    if self.audit_system:
                        self.audit_system.log_event(
                            "heartbeat_error", 
                            f"Error in heartbeat for agent {self.agent_did}: {str(e)}",
                            {"agent_did": self.agent_did, "error": str(e)}
                        )
                
                # Sleep for the specified interval
                time.sleep(interval_seconds)
        
        # Start the heartbeat thread as a daemon (will exit when main program exits)
        thread = threading.Thread(target=heartbeat_thread, daemon=True)
        thread.start()
    
    def shutdown(self) -> None:
        """
        Gracefully shut down the integration and agent.
        """
        self.logger.info("Shutting down StrategyDECK integration")
        
        # Log shutdown in audit system
        if self.audit_system:
            self.audit_system.log_event(
                "integration_shutdown", 
                f"Shutting down StrategyDECK integration for agent {self.agent_did}",
                {"agent_did": self.agent_did}
            )
        
        # Send final heartbeat if registered
        if self.agent_did:
            try:
                self.agent_manager.log_heartbeat(self.agent_did, "AGENT_SHUTDOWN")
            except Exception as e:
                self.logger.error(f"Error sending final heartbeat: {str(e)}")
        
        # Shut down the agent
        self.agent.shutdown()
        self.logger.info("Integration shutdown complete")


# CLI interface
if __name__ == "__main__":
    import argparse
    import sys
    import random
    import sys
    import random
    
    parser = argparse.ArgumentParser(description="StrategyDECK EPOCH5 Integration")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Register command
    register_parser = subparsers.add_parser("register", help="Register agent with EPOCH5")
    register_parser.add_argument("--name", help="Agent name (optional)")
    register_parser.add_argument("--no-improvement", action="store_true", 
                               help="Disable continuous improvement system")
    register_parser.add_argument("--no-security", action="store_true", 
                               help="Disable security system")
    
    # Execute command
    execute_parser = subparsers.add_parser("execute", help="Execute a strategy")
    execute_parser.add_argument("--goal", required=True, help="Strategy goal")
    execute_parser.add_argument("--priority", choices=["high", "medium", "low"], 
                             default="medium", help="Priority level")
    execute_parser.add_argument("--file", help="JSON file with complete strategy data")
    
    # Status command
    subparsers.add_parser("status", help="Show agent status")
    
    # Improvement commands
    improvement_parser = subparsers.add_parser("improvement", help="Continuous improvement commands")
    improvement_subparsers = improvement_parser.add_subparsers(dest="improvement_command")
    
    improvement_subparsers.add_parser("status", help="Show improvement system status")
    improvement_subparsers.add_parser("run-cycle", help="Run an improvement cycle")
    
    recommend_parser = improvement_subparsers.add_parser("recommend", help="Get strategy recommendations")
    recommend_parser.add_argument("--goal", required=True, help="Strategy goal")
    
    # Security commands
    security_parser = subparsers.add_parser("security", help="Security system commands")
    security_subparsers = security_parser.add_subparsers(dest="security_command")
    
    security_subparsers.add_parser("status", help="Show security system status")
    security_subparsers.add_parser("verify", help="Verify agent integrity")
    
    audit_parser = security_subparsers.add_parser("audit", help="Generate audit scroll")
    audit_parser.add_argument("--output", help="Output file")
    audit_parser.add_argument("--event-types", help="Event types to include (comma-separated)")
    audit_parser.add_argument("--limit", type=int, default=100, help="Maximum number of events")
    
    args = parser.parse_args()
    
    # Create integration
    enable_improvement = True
    if hasattr(args, 'no_improvement') and args.no_improvement:
        enable_improvement = False
        
    enable_security = True
    if hasattr(args, 'no_security') and args.no_security:
        enable_security = False
        
    integration = StrategyDECKAgentIntegration(
        agent_name=getattr(args, 'name', None),
        enable_continuous_improvement=enable_improvement,
        enable_security=enable_security
    )
    
    try:
        if args.command == "register":
            did = integration.register_agent()
            print(f"Agent registered with DID: {did}")
            
        elif args.command == "execute":
            # Register if not already registered
            if not integration.agent_did:
                integration.register_agent()
            
            # Prepare strategy data
            if hasattr(args, 'file') and args.file:
                with open(args.file, 'r') as f:
                    strategy_data = json.load(f)
            else:
                strategy_data = {
                    "goal": args.goal,
                    "priority": args.priority
                }
            
            # Execute strategy
            result = integration.execute_strategy(strategy_data)
            print(json.dumps(result, indent=2))
            
        elif args.command == "status":
            # Register if not already registered
            if not integration.agent_did:
                print("Agent not registered with EPOCH5")
            
            status = integration.get_agent_status()
            print(json.dumps(status, indent=2))
            
        elif args.command == "improvement":
            if not integration.improvement_system:
                print("Error: Continuous improvement system is not enabled")
                sys.exit(1)
                
            if args.improvement_command == "status":
                stats = integration.improvement_system.get_improvement_stats()
                print(json.dumps(stats, indent=2))
                
            elif args.improvement_command == "run-cycle":
                results = integration.run_improvement_cycle()
                print(json.dumps(results, indent=2))
                
            elif args.improvement_command == "recommend":
                recommendations = integration.improvement_system.get_strategy_recommendations(args.goal)
                print(json.dumps(recommendations, indent=2))
                
            else:
                improvement_parser.print_help()
                
        elif args.command == "security":
            if not integration.security_system:
                print("Error: Security system is not enabled")
                sys.exit(1)
                
            if args.security_command == "status":
                status = integration.get_security_status()
                print(json.dumps(status, indent=2))
                
            elif args.security_command == "verify":
                if not integration.agent_did:
                    print("Error: Agent not registered")
                    sys.exit(1)
                    
                verification = integration.security_system.verify_agent_integrity(integration.agent_did)
                print(json.dumps(verification, indent=2))
                
            elif args.security_command == "audit":
                # Parse event types if provided
                event_types = None
                if hasattr(args, 'event_types') and args.event_types:
                    event_types = [t.strip() for t in args.event_types.split(",")]
                
                # Generate audit scroll
                output = getattr(args, 'output', None)
                limit = getattr(args, 'limit', 100)
                
                events = integration.audit_system.generate_audit_scroll(output, event_types, limit)
                
                if output:
                    print(f"Audit scroll written to {output}")
                else:
                    print("===== EPOCH5 AUDIT SCROLL =====")
                    for event in events:
                        print(f"[{event['ts']}] {event['event']}: {event['note']}")
                
            else:
                security_parser.print_help()
            
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        integration.shutdown()
