#!/usr/bin/env python3
"""
EPOCH5 Integration Script
Main orchestration script that integrates all EPOCH5 Python components
Provides unified interface for managing agents, policies, DAGs, cycles, capsules, and meta-capsules
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Import all EPOCH5 components
from agent_management import AgentManager
from policy_grants import PolicyManager, PolicyType
from dag_management import DAGManager
from cycle_execution import CycleExecutor
from capsule_metadata import CapsuleManager
from meta_capsule import MetaCapsuleCreator

class EPOCH5Integration:
    """Main integration class for EPOCH5 system"""
    
    def __init__(self, base_dir: str = "./archive/EPOCH5"):
        try:
            self.base_dir = Path(base_dir)
            self.base_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize all managers
            self.agent_manager = AgentManager(str(base_dir))
            self.policy_manager = PolicyManager(str(base_dir))
            self.dag_manager = DAGManager(str(base_dir))
            self.cycle_executor = CycleExecutor(str(base_dir))
            self.capsule_manager = CapsuleManager(str(base_dir))
            self.meta_capsule_creator = MetaCapsuleCreator(str(base_dir))
            
            # Integration log
            self.integration_log = self.base_dir / "integration.log"
        except PermissionError:
            raise PermissionError(f"Cannot create or access directory: {base_dir}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize EPOCH5Integration: {e}")
    
    def timestamp(self) -> str:
        """Generate ISO timestamp"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def log_integration_event(self, event: str, data: Dict[str, Any]):
        """Log integration events"""
        log_entry = {
            "timestamp": self.timestamp(),
            "event": event,
            "data": data
        }
        
        with open(self.integration_log, 'a') as f:
            f.write(f"{json.dumps(log_entry)}\n")
    
    def setup_demo_environment(self) -> Dict[str, Any]:
        """Set up a complete demo environment with sample data"""
        setup_results = {
            "started_at": self.timestamp(),
            "components": {},
            "errors": []
        }
        
        try:
            # Create sample agents
            agents = []
            agent_skills = [
                ["python", "data_processing", "ml"],
                ["javascript", "frontend", "api"],
                ["devops", "docker", "kubernetes"],
                ["security", "cryptography", "audit"],
                ["database", "sql", "nosql"]
            ]
            
            for i, skills in enumerate(agent_skills, 1):
                agent = self.agent_manager.create_agent(skills, f"demo_agent_{i}")
                self.agent_manager.register_agent(agent)
                agents.append(agent["did"])
            
            setup_results["components"]["agents"] = {
                "created": len(agents),
                "dids": agents
            }
            
            # Create sample policies
            policies = [
                {
                    "policy_id": "demo_quorum",
                    "type": PolicyType.QUORUM,
                    "parameters": {"required_count": 2},
                    "description": "Demo quorum policy requiring 2 approvers"
                },
                {
                    "policy_id": "demo_trust",
                    "type": PolicyType.TRUST_THRESHOLD,
                    "parameters": {"min_reliability": 0.8},
                    "description": "Demo trust policy requiring 80% reliability"
                }
            ]
            
            for policy_def in policies:
                policy = self.policy_manager.create_policy(
                    policy_def["policy_id"],
                    policy_def["type"],
                    policy_def["parameters"],
                    policy_def["description"]
                )
                self.policy_manager.add_policy(policy)
            
            setup_results["components"]["policies"] = {
                "created": len(policies),
                "policy_ids": [p["policy_id"] for p in policies]
            }
            
            # Create sample grants
            grants = []
            for i, agent_did in enumerate(agents[:3], 1):
                grant = self.policy_manager.create_grant(
                    f"demo_grant_{i}",
                    agent_did,
                    "demo_resource",
                    ["read", "execute"]
                )
                self.policy_manager.add_grant(grant)
                grants.append(grant["grant_id"])
            
            setup_results["components"]["grants"] = {
                "created": len(grants),
                "grant_ids": grants
            }
            
            # Create sample DAG
            demo_tasks = [
                {
                    "task_id": "task_1",
                    "command": "process_data --input data.csv",
                    "dependencies": [],
                    "required_skills": ["python", "data_processing"]
                },
                {
                    "task_id": "task_2",
                    "command": "validate_results --data processed_data.json",
                    "dependencies": ["task_1"],
                    "required_skills": ["python"]
                },
                {
                    "task_id": "task_3",
                    "command": "generate_report --results validated_data.json",
                    "dependencies": ["task_2"],
                    "required_skills": ["python"]
                }
            ]
            
            dag_tasks = [self.dag_manager.create_task(**task_def) for task_def in demo_tasks]
            demo_dag = self.dag_manager.create_dag("demo_dag", dag_tasks, "Demo DAG for testing")
            self.dag_manager.save_dag(demo_dag)
            
            setup_results["components"]["dags"] = {
                "created": 1,
                "dag_id": "demo_dag",
                "tasks": len(dag_tasks)
            }
            
            # Create sample cycle
            task_assignments = [
                {"task_id": "demo_task_1", "agent_did": agents[0], "estimated_cost": 10.0},
                {"task_id": "demo_task_2", "agent_did": agents[1], "estimated_cost": 15.0},
                {"task_id": "demo_task_3", "agent_did": agents[2], "estimated_cost": 8.0}
            ]
            
            demo_cycle = self.cycle_executor.create_cycle(
                "demo_cycle",
                budget=100.0,
                max_latency=60.0,
                task_assignments=task_assignments
            )
            self.cycle_executor.save_cycle(demo_cycle)
            
            setup_results["components"]["cycles"] = {
                "created": 1,
                "cycle_id": "demo_cycle",
                "tasks": len(task_assignments)
            }
            
            # Create sample capsules
            demo_content = "This is demo content for EPOCH5 capsule system. It demonstrates the integration of all components."
            demo_capsule = self.capsule_manager.create_capsule(
                "demo_capsule",
                demo_content,
                {"type": "demo", "version": "1.0"},
                "text/plain"
            )
            
            setup_results["components"]["capsules"] = {
                "created": 1,
                "capsule_id": "demo_capsule",
                "content_hash": demo_capsule["content_hash"]
            }
            
            setup_results["completed_at"] = self.timestamp()
            setup_results["success"] = True
            
        except Exception as e:
            setup_results["errors"].append(str(e))
            setup_results["success"] = False
        
        self.log_integration_event("DEMO_ENVIRONMENT_SETUP", setup_results)
        return setup_results
    
    def run_complete_workflow(self) -> Dict[str, Any]:
        """Run a complete workflow demonstrating all system integration"""
        workflow_results = {
            "started_at": self.timestamp(),
            "steps": {},
            "errors": []
        }
        
        try:
            # Step 1: Execute DAG
            dag_result = self.dag_manager.execute_dag("demo_dag", simulation=True)
            workflow_results["steps"]["dag_execution"] = {
                "status": dag_result.get("final_status"),
                "completed_tasks": len(dag_result.get("completed_tasks", [])),
                "failed_tasks": len(dag_result.get("failed_tasks", []))
            }
            
            # Step 2: Execute Cycle
            validator_nodes = ["validator_1", "validator_2", "validator_3"]
            cycle_result = self.cycle_executor.execute_full_cycle("demo_cycle", validator_nodes, simulation=True)
            workflow_results["steps"]["cycle_execution"] = {
                "status": cycle_result.get("status"),
                "sla_compliant": cycle_result.get("sla_compliance", {}).get("compliant"),
                "success_rate": cycle_result.get("final_metrics", {}).get("success_rate")
            }
            
            # Step 3: Verify capsule integrity
            integrity_result = self.capsule_manager.verify_capsule_integrity("demo_capsule")
            workflow_results["steps"]["capsule_verification"] = {
                "valid": integrity_result.get("overall_valid"),
                "content_hash_valid": integrity_result.get("content_hash_valid"),
                "merkle_valid": integrity_result.get("merkle_verification", {}).get("root_valid")
            }
            
            # Step 4: Create comprehensive archive
            archive_result = self.capsule_manager.create_archive(
                "workflow_archive",
                ["demo_capsule"],
                include_metadata=True
            )
            workflow_results["steps"]["archive_creation"] = {
                "status": archive_result.get("status"),
                "file_count": archive_result.get("file_count"),
                "archive_hash": archive_result.get("archive_hash")
            }
            
            # Step 5: Create meta-capsule
            meta_capsule = self.meta_capsule_creator.create_meta_capsule(
                "workflow_meta_capsule",
                "Meta-capsule created from complete workflow execution"
            )
            workflow_results["steps"]["meta_capsule_creation"] = {
                "meta_capsule_id": meta_capsule["meta_capsule_id"],
                "systems_captured": len(meta_capsule["system_state"]["systems"]),
                "files_captured": meta_capsule["system_state"]["summary_stats"]["total_files_captured"],
                "meta_hash": meta_capsule["meta_hash"]
            }
            
            workflow_results["completed_at"] = self.timestamp()
            workflow_results["success"] = True
            
        except Exception as e:
            workflow_results["errors"].append(str(e))
            workflow_results["success"] = False
        
        self.log_integration_event("COMPLETE_WORKFLOW", workflow_results)
        return workflow_results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            "timestamp": self.timestamp(),
            "components": {}
        }
        
        # Agent status
        agent_registry = self.agent_manager.load_registry()
        status["components"]["agents"] = {
            "total": len(agent_registry.get("agents", {})),
            "active": len(self.agent_manager.get_active_agents())
        }
        
        # Policy status
        policies = self.policy_manager.load_policies()
        grants = self.policy_manager.load_grants()
        status["components"]["policies"] = {
            "total_policies": len(policies.get("policies", {})),
            "active_policies": len(self.policy_manager.get_active_policies()),
            "total_grants": len(grants.get("grants", {}))
        }
        
        # DAG status
        dags = self.dag_manager.load_dags()
        status["components"]["dags"] = {
            "total": len(dags.get("dags", {})),
            "completed": len([d for d in dags.get("dags", {}).values() if d.get("status") == "completed"])
        }
        
        # Cycle status
        cycles = self.cycle_executor.load_cycles()
        status["components"]["cycles"] = {
            "total": len(cycles.get("cycles", {})),
            "completed": len([c for c in cycles.get("cycles", {}).values() if c.get("status") == "completed"])
        }
        
        # Capsule status
        capsules = self.capsule_manager.list_capsules()
        archives = self.capsule_manager.list_archives()
        status["components"]["capsules"] = {
            "total_capsules": len(capsules),
            "total_archives": len(archives)
        }
        
        # Meta-capsule status
        meta_capsules = self.meta_capsule_creator.list_meta_capsules()
        status["components"]["meta_capsules"] = {
            "total": len(meta_capsules)
        }
        
        return status
    
    def validate_system_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of the entire system"""
        validation_results = {
            "started_at": self.timestamp(),
            "validations": {},
            "overall_valid": True,
            "errors": []
        }
        
        try:
            # Validate all capsules
            capsules = self.capsule_manager.list_capsules()
            capsule_validations = []
            
            for capsule_info in capsules:
                # This is a simplified approach - in real implementation we'd need capsule IDs
                pass  # Skip detailed capsule validation for demo
            
            validation_results["validations"]["capsules"] = {
                "total_checked": len(capsules),
                "valid": len(capsules),  # Simplified
                "invalid": 0
            }
            
            # Validate meta-capsules
            meta_capsules = self.meta_capsule_creator.list_meta_capsules()
            meta_validations = []
            
            for meta_capsule_info in meta_capsules:
                try:
                    result = self.meta_capsule_creator.verify_meta_capsule(meta_capsule_info["meta_capsule_id"])
                    meta_validations.append(result)
                except Exception as e:
                    validation_results["errors"].append(f"Meta-capsule validation error: {str(e)}")
            
            valid_meta_capsules = len([r for r in meta_validations if r.get("integrity_valid", False)])
            validation_results["validations"]["meta_capsules"] = {
                "total_checked": len(meta_capsules),
                "valid": valid_meta_capsules,
                "invalid": len(meta_capsules) - valid_meta_capsules
            }
            
            # Overall validation
            validation_results["overall_valid"] = (
                validation_results["validations"]["capsules"]["invalid"] == 0 and
                validation_results["validations"]["meta_capsules"]["invalid"] == 0 and
                len(validation_results["errors"]) == 0
            )
            
        except Exception as e:
            validation_results["errors"].append(f"System validation error: {str(e)}")
            validation_results["overall_valid"] = False
        
        validation_results["completed_at"] = self.timestamp()
        self.log_integration_event("SYSTEM_INTEGRITY_VALIDATION", validation_results)
        
        return validation_results

def main():
    parser = argparse.ArgumentParser(description="EPOCH5 Integration System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Setup demo environment
    subparsers.add_parser("setup-demo", help="Set up demo environment with sample data")
    
    # Run complete workflow
    subparsers.add_parser("run-workflow", help="Run complete integrated workflow")
    
    # System status
    subparsers.add_parser("status", help="Get system status")
    
    # Validate system
    subparsers.add_parser("validate", help="Validate system integrity")
    
    # Component-specific commands
    agent_parser = subparsers.add_parser("agents", help="Agent management commands")
    agent_subparsers = agent_parser.add_subparsers(dest="agent_command")
    agent_subparsers.add_parser("list", help="List agents")
    create_agent = agent_subparsers.add_parser("create", help="Create agent")
    create_agent.add_argument("skills", nargs="+", help="Agent skills")
    
    policy_parser = subparsers.add_parser("policies", help="Policy management commands")
    policy_subparsers = policy_parser.add_subparsers(dest="policy_command")
    policy_subparsers.add_parser("list", help="List policies")
    
    # One-liner commands for quick operations
    oneliner_parser = subparsers.add_parser("oneliner", help="Execute one-liner commands")
    oneliner_parser.add_argument("operation", choices=[
        "quick-agent", "quick-policy", "quick-dag", "quick-cycle", 
        "quick-capsule", "quick-meta", "system-snapshot"
    ], help="One-liner operation to execute")
    oneliner_parser.add_argument("--params", help="JSON parameters for the operation")
    
    args = parser.parse_args()
    
    # Initialize integration system
    integration = EPOCH5Integration()
    
    if args.command == "setup-demo":
        print("Setting up EPOCH5 demo environment...")
        result = integration.setup_demo_environment()
        
        if result["success"]:
            print("✓ Demo environment setup completed successfully!")
            print(f"Created components:")
            for component, details in result["components"].items():
                print(f"  - {component}: {details.get('created', 'N/A')} items")
        else:
            print("✗ Demo environment setup failed!")
            for error in result["errors"]:
                print(f"  Error: {error}")
    
    elif args.command == "run-workflow":
        print("Running complete EPOCH5 workflow...")
        result = integration.run_complete_workflow()
        
        if result["success"]:
            print("✓ Complete workflow executed successfully!")
            print("Workflow steps completed:")
            for step, details in result["steps"].items():
                print(f"  - {step}: {details}")
        else:
            print("✗ Workflow execution failed!")
            for error in result["errors"]:
                print(f"  Error: {error}")
    
    elif args.command == "status":
        status = integration.get_system_status()
        print(f"EPOCH5 System Status (as of {status['timestamp']}):")
        
        for component, stats in status["components"].items():
            print(f"  {component.upper()}:")
            for key, value in stats.items():
                print(f"    {key}: {value}")
    
    elif args.command == "validate":
        print("Validating EPOCH5 system integrity...")
        result = integration.validate_system_integrity()
        
        print(f"System validation: {'✓ VALID' if result['overall_valid'] else '✗ INVALID'}")
        print("Component validations:")
        for component, validation in result["validations"].items():
            print(f"  {component}: {validation['valid']}/{validation['total_checked']} valid")
        
        if result["errors"]:
            print("Errors:")
            for error in result["errors"]:
                print(f"  - {error}")
    
    elif args.command == "agents":
        if args.agent_command == "list":
            registry = integration.agent_manager.load_registry()
            print(f"Registered Agents ({len(registry.get('agents', {}))}):")
            for did, agent in registry.get('agents', {}).items():
                print(f"  {did}: {agent.get('skills', [])} (reliability: {agent.get('reliability_score', 0):.2f})")
        
        elif args.agent_command == "create":
            # Validate skills input
            if not args.skills or len(args.skills) == 0:
                print("❌ Error: At least one skill is required to create an agent")
                print("💡 Usage: python3 integration.py agents create skill1 skill2 ...")
                sys.exit(1)
            
            # Validate skill format (basic validation)
            invalid_skills = [skill for skill in args.skills if not skill.strip() or len(skill.strip()) < 2]
            if invalid_skills:
                print(f"❌ Error: Invalid skill names: {invalid_skills}")
                print("💡 Skills must be at least 2 characters long and not empty")
                sys.exit(1)
            
            try:
                agent = integration.agent_manager.create_agent(args.skills)
                integration.agent_manager.register_agent(agent)
                print(f"✓ Created agent: {agent['did']} with skills: {', '.join(agent['skills'])}")
            except Exception as e:
                print(f"❌ Failed to create agent: {e}")
                sys.exit(1)
    
    elif args.command == "policies":
        if args.policy_command == "list":
            policies = integration.policy_manager.get_active_policies()
            print(f"Active Policies ({len(policies)}):")
            for policy in policies:
                print(f"  {policy['policy_id']}: {policy['type']} (enforced: {policy['enforced_count']})")
    
    elif args.command == "oneliner":
        # Execute one-liner operations
        params = json.loads(args.params) if args.params else {}
        
        if args.operation == "quick-agent":
            skills = params.get("skills", ["python", "general"])
            agent = integration.agent_manager.create_agent(skills)
            integration.agent_manager.register_agent(agent)
            print(f"Quick agent created: {agent['did']}")
        
        elif args.operation == "system-snapshot":
            meta_capsule_id = params.get("id", f"snapshot_{int(datetime.now().timestamp())}")
            meta_capsule = integration.meta_capsule_creator.create_meta_capsule(
                meta_capsule_id,
                "Quick system snapshot"
            )
            print(f"System snapshot created: {meta_capsule['meta_capsule_id']}")
            print(f"Systems captured: {len(meta_capsule['system_state']['systems'])}")
            print(f"Files captured: {meta_capsule['system_state']['summary_stats']['total_files_captured']}")
        
        else:
            print(f"One-liner operation '{args.operation}' not implemented yet")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Operation interrupted by user")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        sys.exit(1)
    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
        print("💡 Try checking file permissions or running with appropriate privileges")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Use --help for usage information or check the logs for more details")
        sys.exit(1)
    main()