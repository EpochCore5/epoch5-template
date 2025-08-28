#!/usr/bin/env python3
"""
EPOCH5 Agent Security Controller

This module integrates the EPOCH5 Audit System with the Agent Monitoring System,
providing ceiling enforcement, secure audit logging, and verification mechanisms.
Derived from Alpha Ceiling, GBTEpoch, and Phone Audit Scroll concepts.
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import EPOCH5 components
try:
    from agent_monitor import AgentMonitor, AgentMessage
    from epoch_audit import EpochAudit
except ImportError:
    print("Error: Required EPOCH5 components not found.")
    print("Make sure you are running this script from the EPOCH5 directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("epoch_security.log")
    ]
)

logger = logging.getLogger("AgentSecurity")


class AgentSecurityController:
    """
    Security controller for EPOCH5 agents with ceiling enforcement,
    audit logging, and verification mechanisms.
    """
    
    def __init__(self, base_dir: str = "./archive/EPOCH5"):
        """
        Initialize the security controller
        
        Args:
            base_dir: Base directory for EPOCH5 systems
        """
        self.base_dir = Path(base_dir)
        
        # Initialize audit system
        self.audit = EpochAudit(base_dir=base_dir)
        
        # Initialize agent monitor
        self.monitor = AgentMonitor(base_dir=base_dir)
        
        # Define security policies
        self.security_policies = {
            "max_task_priority": 100,
            "max_resource_allocation": 100,
            "max_message_rate": 20,  # per minute
            "max_concurrent_tasks": 10,
            "required_heartbeat_interval": 300,  # seconds
            "max_execution_time": 600,  # seconds
            "max_agent_restart_attempts": 5,
            "daily_resource_quota": 1000
        }
        
        # Rate limiting tracking
        self.rate_limits = {}
        
        # Initialize the emoji seal command
        self.init_emoji_command()
        
        logger.info("Agent Security Controller initialized")
    
    def init_emoji_command(self):
        """Initialize emoji command for audit scroll"""
        # Create bash script wrapper for the Phone Audit Scroll
        script_path = self.base_dir / "scripts"
        script_path.mkdir(exist_ok=True)
        
        audit_script = script_path / "emoji_audit_scroll.sh"
        
        script_content = f"""#!/bin/bash
# EPOCH5 Audit Scroll Script
# Access with emoji: 🧙🦿🤖

python3 -m epoch_audit scroll --output {self.base_dir}/audit/scrolls/audit_$(date +%Y%m%d_%H%M%S).txt
echo "📜 Audit scroll generated at {self.base_dir}/audit/scrolls/"
"""
        
        # Create the script file
        with open(audit_script, "w") as f:
            f.write(script_content)
        
        # Make it executable
        os.chmod(audit_script, 0o755)
        
        # Create alias file
        alias_file = self.base_dir / "scripts" / "emoji_alias.sh"
        
        alias_content = f"""#!/bin/bash
# EPOCH5 Emoji aliases
# Source this file to use emoji commands

alias 🧙🦿🤖="{audit_script}"
echo "EPOCH5 emoji commands available: 🧙🦿🤖 (audit scroll)"
"""
        
        # Create the alias file
        with open(alias_file, "w") as f:
            f.write(alias_content)
        
        # Make it executable
        os.chmod(alias_file, 0o755)
        
        logger.info(f"Emoji command initialized: 🧙🦿🤖")
    
    def enforce_task_priority(self, task_data: Dict[str, Any], agent_did: Optional[str] = None) -> Dict[str, Any]:
        """
        Enforce ceiling on task priority
        
        Args:
            task_data: Task data with priority field
            agent_did: Optional agent DID
            
        Returns:
            Task data with enforced priority
        """
        if "priority" in task_data:
            try:
                priority = float(task_data["priority"])
                result = self.audit.enforce_ceiling("task_priority", priority, agent_did)
                
                if result["capped"]:
                    logger.warning(f"Task priority capped: {result['original_value']} → {result['final_value']}")
                    task_data["priority"] = result["final_value"]
                    
                    # Add ceiling enforcement note to task
                    if "notes" not in task_data:
                        task_data["notes"] = []
                    
                    task_data["notes"].append(f"Priority capped from {result['original_value']} to {result['final_value']} due to ceiling enforcement")
            except (ValueError, TypeError):
                logger.warning(f"Invalid task priority: {task_data.get('priority')}")
        
        return task_data
    
    def enforce_resource_allocation(self, resource_data: Dict[str, Any], agent_did: Optional[str] = None) -> Dict[str, Any]:
        """
        Enforce ceiling on resource allocation
        
        Args:
            resource_data: Resource allocation data
            agent_did: Optional agent DID
            
        Returns:
            Resource data with enforced allocations
        """
        if "allocation" in resource_data:
            try:
                allocation = float(resource_data["allocation"])
                result = self.audit.enforce_ceiling("resource_allocation", allocation, agent_did)
                
                if result["capped"]:
                    logger.warning(f"Resource allocation capped: {result['original_value']} → {result['final_value']}")
                    resource_data["allocation"] = result["final_value"]
                    resource_data["capped"] = True
                    resource_data["original_allocation"] = result["original_value"]
            except (ValueError, TypeError):
                logger.warning(f"Invalid resource allocation: {resource_data.get('allocation')}")
        
        return resource_data
    
    def check_rate_limit(self, agent_did: str, action_type: str) -> bool:
        """
        Check if an action exceeds the rate limit
        
        Args:
            agent_did: Agent DID
            action_type: Type of action
            
        Returns:
            True if within rate limit, False if exceeded
        """
        current_time = time.time()
        
        # Initialize rate limit tracking for this agent if not already done
        if agent_did not in self.rate_limits:
            self.rate_limits[agent_did] = {}
        
        if action_type not in self.rate_limits[agent_did]:
            self.rate_limits[agent_did][action_type] = []
        
        # Remove expired timestamps (older than 1 minute)
        self.rate_limits[agent_did][action_type] = [
            ts for ts in self.rate_limits[agent_did][action_type] 
            if current_time - ts < 60
        ]
        
        # Check if rate limit exceeded
        if action_type == "message":
            max_rate = self.security_policies["max_message_rate"]
            if len(self.rate_limits[agent_did][action_type]) >= max_rate:
                # Log rate limit violation
                self.audit.log_event("rate_limit_exceeded", f"Message rate limit exceeded for agent {agent_did}", {
                    "agent_did": agent_did,
                    "action_type": action_type,
                    "current_rate": len(self.rate_limits[agent_did][action_type]),
                    "max_rate": max_rate
                })
                
                return False
        
        # Add current timestamp to rate limit tracking
        self.rate_limits[agent_did][action_type].append(current_time)
        
        return True
    
    def verify_agent_integrity(self, agent_did: str) -> Dict[str, Any]:
        """
        Verify the integrity of an agent
        
        Args:
            agent_did: Agent DID
            
        Returns:
            Verification results
        """
        # Get agent status
        agent = self.monitor.get_agent_status(agent_did)
        
        if not agent:
            return {
                "status": "error",
                "message": f"Agent {agent_did} not found"
            }
        
        agent_data = agent["agent_data"]
        
        # Check heartbeat age
        last_heartbeat = agent.get("heartbeat_age", float('inf'))
        required_interval = self.security_policies["required_heartbeat_interval"]
        
        heartbeat_status = "ok" if last_heartbeat < required_interval else "expired"
        
        # Verify agent's performance
        reliability = agent_data.get("reliability_score", 0)
        reliability_status = "ok" if reliability >= 0.7 else ("warning" if reliability >= 0.5 else "critical")
        
        # Check task history if available
        if "query_responses" in agent:
            task_history = next((r for r in agent["query_responses"] if r.get("query_type") == "task_history"), None)
            if task_history:
                recent_failures = sum(1 for t in task_history.get("response", {}).get("tasks", [])
                                    if t.get("status") == "failed")
                
                failure_status = "ok" if recent_failures <= 2 else ("warning" if recent_failures <= 5 else "critical")
            else:
                failure_status = "unknown"
                recent_failures = 0
        else:
            failure_status = "unknown"
            recent_failures = 0
        
        # Prepare verification result
        verification = {
            "agent_did": agent_did,
            "status": "verified" if heartbeat_status == "ok" and reliability_status in ["ok", "warning"] else "compromised",
            "checks": {
                "heartbeat": {
                    "status": heartbeat_status,
                    "age": last_heartbeat,
                    "required_interval": required_interval
                },
                "reliability": {
                    "status": reliability_status,
                    "score": reliability
                },
                "task_failures": {
                    "status": failure_status,
                    "recent_failures": recent_failures
                }
            }
        }
        
        # Log verification
        self.audit.log_event("agent_verification", 
                           f"Agent {agent_did} verification: {verification['status']}", 
                           verification)
        
        return verification
    
    def secure_command(self, agent_did: str, command: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a command to an agent with security checks
        
        Args:
            agent_did: Agent DID
            command: Command to send
            parameters: Command parameters
            
        Returns:
            Command result with security details
        """
        # Verify agent integrity first
        verification = self.verify_agent_integrity(agent_did)
        if verification["status"] == "compromised":
            return {
                "status": "error",
                "message": f"Agent {agent_did} failed integrity check",
                "verification": verification
            }
        
        # Check rate limit
        if not self.check_rate_limit(agent_did, "command"):
            return {
                "status": "error",
                "message": f"Rate limit exceeded for agent {agent_did}"
            }
        
        # Apply ceiling enforcement to parameters if needed
        if command == "execute_strategy" and "priority" in parameters:
            parameters = self.enforce_task_priority(parameters, agent_did)
        
        if command in ["allocate_resources", "set_resources"] and "allocation" in parameters:
            parameters = self.enforce_resource_allocation(parameters, agent_did)
        
        # Log command
        self.audit.log_event("secure_command", f"Sending command {command} to agent {agent_did}", {
            "agent_did": agent_did,
            "command": command,
            "parameters": parameters
        })
        
        # Send command
        message_id = self.monitor.send_command(agent_did, command, parameters)
        
        if not message_id:
            return {
                "status": "error",
                "message": f"Failed to send command to agent {agent_did}"
            }
        
        return {
            "status": "success",
            "message_id": message_id,
            "command": command,
            "parameters": parameters,
            "verification": verification
        }
    
    def generate_security_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a security report for all agents
        
        Args:
            output_file: Optional file to write the report to
            
        Returns:
            Security report data
        """
        # Get all agents
        agents = self.monitor.get_all_agent_statuses()
        
        # Generate GBTEpoch timestamp
        epoch_time = int(time.time())
        
        # Initialize report
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "epoch": epoch_time,
            "agent_count": len(agents),
            "online_agents": sum(1 for a in agents.values() if a["is_online"]),
            "offline_agents": sum(1 for a in agents.values() if not a["is_online"]),
            "agents": [],
            "security_policies": self.security_policies,
            "seal": ""
        }
        
        # Add agent data
        for did, agent in agents.items():
            agent_data = agent["agent_data"]
            
            # Verify agent integrity
            verification = self.verify_agent_integrity(did)
            
            # Add to report
            report["agents"].append({
                "did": did,
                "type": agent_data.get("type", "unknown"),
                "status": "online" if agent["is_online"] else "offline",
                "integrity": verification["status"],
                "reliability": agent_data.get("reliability_score", 0),
                "heartbeat_age": agent.get("heartbeat_age", None),
                "verification": verification["checks"]
            })
        
        # Generate seal for report
        report_payload = f"security_report_{report['timestamp']}_{report['agent_count']}"
        report["seal"] = hashlib.sha256(report_payload.encode()).hexdigest()
        
        # Log report generation
        self.audit.log_event("security_report", f"Generated security report: {report['agent_count']} agents", {
            "agent_count": report["agent_count"],
            "online_agents": report["online_agents"],
            "offline_agents": report["offline_agents"],
            "seal": report["seal"]
        })
        
        # Write to output file if specified
        if output_file:
            output_path = Path(output_file)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)
        
        return report
    
    def run_audit_scroll(self, output_file: Optional[str] = None) -> str:
        """
        Run the Phone Audit Scroll (generate and display audit log)
        
        Args:
            output_file: Optional file to write the scroll to
            
        Returns:
            Path to the generated audit scroll
        """
        # Generate timestamp for file name
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Set default output file if not specified
        if not output_file:
            scrolls_dir = self.base_dir / "audit" / "scrolls"
            scrolls_dir.mkdir(parents=True, exist_ok=True)
            output_file = str(scrolls_dir / f"audit_scroll_{timestamp}.txt")
        
        # Generate audit scroll
        self.audit.generate_audit_scroll(output_file)
        
        # Log scroll generation
        self.audit.log_event("audit_scroll", f"Generated audit scroll: {output_file}")
        
        return output_file
    
    def shutdown(self):
        """Shut down the security controller"""
        self.monitor.shutdown()
        
        # Log shutdown
        self.audit.log_event("security_controller_shutdown", "Security controller shutdown")


# CLI interface
def main():
    """Main entry point for security controller"""
    parser = argparse.ArgumentParser(description="EPOCH5 Agent Security Controller")
    parser.add_argument("--base-dir", default="./archive/EPOCH5", help="Base directory for EPOCH5 systems")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Verify agent integrity command
    verify_parser = subparsers.add_parser("verify", help="Verify agent integrity")
    verify_parser.add_argument("did", help="Agent DID")
    
    # Secure command command
    secure_parser = subparsers.add_parser("secure-command", help="Send a secure command to an agent")
    secure_parser.add_argument("did", help="Agent DID")
    secure_parser.add_argument("command", help="Command to send")
    secure_parser.add_argument("--parameters", help="Command parameters (JSON)")
    
    # Generate security report command
    report_parser = subparsers.add_parser("report", help="Generate security report")
    report_parser.add_argument("--output", help="Output file")
    
    # Run audit scroll command
    scroll_parser = subparsers.add_parser("scroll", help="Run audit scroll")
    scroll_parser.add_argument("--output", help="Output file")
    
    # Emoji command
    emoji_parser = subparsers.add_parser("emoji", help="Run emoji command")
    
    args = parser.parse_args()
    
    # Create security controller
    controller = AgentSecurityController(base_dir=args.base_dir)
    
    try:
        if args.command == "verify":
            # Verify agent integrity
            verification = controller.verify_agent_integrity(args.did)
            
            print(f"Agent {args.did} verification status: {verification['status']}")
            print("\nCheck details:")
            
            for check, details in verification["checks"].items():
                print(f"  {check}: {details['status']}")
            
        elif args.command == "secure-command":
            # Parse parameters
            parameters = {}
            if args.parameters:
                try:
                    parameters = json.loads(args.parameters)
                except json.JSONDecodeError:
                    print("Error: Parameters must be valid JSON")
                    exit(1)
            
            # Send secure command
            result = controller.secure_command(args.did, args.command, parameters)
            
            if result["status"] == "success":
                print(f"Command sent to agent {args.did}")
                print(f"Message ID: {result['message_id']}")
                print(f"Command: {result['command']}")
                print(f"Parameters: {result['parameters']}")
            else:
                print(f"Error: {result['message']}")
            
        elif args.command == "report":
            # Generate security report
            report = controller.generate_security_report(args.output)
            
            if args.output:
                print(f"Security report written to {args.output}")
            else:
                print(f"Security Report ({report['timestamp']}):")
                print(f"Total Agents: {report['agent_count']}")
                print(f"Online: {report['online_agents']}, Offline: {report['offline_agents']}")
                print("\nAgent status:")
                
                for agent in report["agents"]:
                    status_color = "green" if agent["status"] == "online" else "red"
                    integrity_color = "green" if agent["integrity"] == "verified" else "red"
                    
                    print(f"  {agent['did']}: {agent['status']} ({agent['integrity']})")
            
        elif args.command == "scroll":
            # Run audit scroll
            scroll_file = controller.run_audit_scroll(args.output)
            
            print(f"Audit scroll generated: {scroll_file}")
            
            # Display scroll contents
            try:
                with open(scroll_file, "r") as f:
                    print("\n" + f.read())
            except Exception as e:
                print(f"Error displaying scroll: {str(e)}")
            
        elif args.command == "emoji":
            # Run emoji command (audit scroll)
            scroll_file = controller.run_audit_scroll()
            
            print(f"🧙🦿🤖 Audit scroll generated: {scroll_file}")
            
            # Display instructions
            print("\nTo use emoji commands in your shell:")
            print(f"  source {controller.base_dir}/scripts/emoji_alias.sh")
            
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        controller.shutdown()


if __name__ == "__main__":
    # Add import for hashlib
    import hashlib
    main()
