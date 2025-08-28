#!/usr/bin/env python3
"""
EPOCH5 Autonomous System Test Data Generator
Generates synthetic test data for evaluating autonomous system components
"""

import os
import sys
import time
import json
import random
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("test_data_generator.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TestDataGenerator:
    """Generates test data for EPOCH5 autonomous system evaluation"""
    
    def __init__(self):
        """Initialize the test data generator"""
        self.data_dir = Path("./test_data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Components that can experience issues
        self.components = [
            "agent_manager", "dag_executor", "policy_engine", 
            "capsule_loader", "ceiling_enforcer", "integration_service"
        ]
        
        # Types of anomalies
        self.anomaly_types = [
            "resource_exhaustion", "memory_leak", "deadlock",
            "performance_degradation", "connection_failure", "data_corruption"
        ]
        
        # Types of security events
        self.security_event_types = [
            "ceiling_violation", "policy_breach", "unauthorized_access",
            "data_exfiltration", "injection_attempt", "unusual_activity_pattern"
        ]
        
        # Security severities
        self.security_severities = ["low", "medium", "high", "critical"]
        
    def generate_component_metrics(self, days=7, anomaly_probability=0.05):
        """Generate synthetic component health metrics with occasional anomalies"""
        logger.info(f"Generating component metrics for {days} days")
        
        metrics_data = []
        now = datetime.now()
        
        # Generate data points at 5-minute intervals
        for day in range(days):
            for hour in range(24):
                for minute in range(0, 60, 5):
                    timestamp = now - timedelta(days=days-day, hours=23-hour, minutes=60-minute)
                    
                    # For each component
                    for component in self.components:
                        # Normal metrics with some random variation
                        cpu_usage = random.uniform(10, 30)
                        memory_usage = random.uniform(100, 300)
                        response_time = random.uniform(50, 150)
                        error_rate = random.uniform(0, 0.5)
                        
                        # Introduce anomaly with specified probability
                        is_anomaly = random.random() < anomaly_probability
                        anomaly_type = None
                        
                        if is_anomaly:
                            anomaly_type = random.choice(self.anomaly_types)
                            
                            # Modify metrics based on anomaly type
                            if anomaly_type == "resource_exhaustion":
                                cpu_usage = random.uniform(85, 100)
                                memory_usage = random.uniform(800, 1000)
                            elif anomaly_type == "memory_leak":
                                memory_usage = random.uniform(700, 1000)
                            elif anomaly_type == "deadlock":
                                response_time = random.uniform(2000, 5000)
                            elif anomaly_type == "performance_degradation":
                                response_time = random.uniform(500, 1500)
                                cpu_usage = random.uniform(60, 80)
                            elif anomaly_type == "connection_failure":
                                error_rate = random.uniform(5, 10)
                            elif anomaly_type == "data_corruption":
                                error_rate = random.uniform(1, 3)
                        
                        # Create metric record
                        metric = {
                            "timestamp": timestamp.isoformat(),
                            "component": component,
                            "metrics": {
                                "cpu_usage": round(cpu_usage, 2),
                                "memory_usage": round(memory_usage, 2),
                                "response_time_ms": round(response_time, 2),
                                "error_rate": round(error_rate, 2)
                            },
                            "is_anomaly": is_anomaly
                        }
                        
                        if anomaly_type:
                            metric["anomaly_type"] = anomaly_type
                        
                        metrics_data.append(metric)
        
        # Write metrics to file
        metrics_file = self.data_dir / "component_metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f, indent=2)
            
        logger.info(f"Generated {len(metrics_data)} component metric records")
        logger.info(f"Data written to {metrics_file}")
        
        return metrics_data
    
    def generate_security_events(self, days=7, event_frequency=10):
        """Generate synthetic security events"""
        logger.info(f"Generating security events for {days} days")
        
        security_events = []
        now = datetime.now()
        
        # Generate a specified number of events per day
        for day in range(days):
            for _ in range(event_frequency):
                # Random timestamp within the day
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                timestamp = now - timedelta(days=days-day, hours=23-hour, minutes=59-minute, seconds=59-second)
                
                # Select event properties
                event_type = random.choice(self.security_event_types)
                severity = random.choice(self.security_severities)
                source_component = random.choice(self.components)
                
                # Create event record
                event = {
                    "timestamp": timestamp.isoformat(),
                    "event_id": f"SEC-{random.randint(10000, 99999)}",
                    "event_type": event_type,
                    "severity": severity,
                    "source_component": source_component,
                    "description": f"{severity.capitalize()} {event_type} detected in {source_component}",
                    "details": {
                        "user_agent": f"Mozilla/5.0 (compatible; Bot/{random.randint(1, 100)})" if random.random() < 0.3 else "EPOCH5-Client/1.0",
                        "source_ip": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
                        "target_resource": f"/{random.choice(['api', 'data', 'admin', 'service'])}/{random.choice(['v1', 'v2'])}/{random.choice(['users', 'configs', 'agents', 'tasks'])}",
                        "request_method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                        "request_size": random.randint(100, 10000)
                    },
                    "auto_mitigated": random.random() < 0.7  # 70% of events are auto-mitigated
                }
                
                security_events.append(event)
        
        # Sort events by timestamp
        security_events.sort(key=lambda x: x["timestamp"])
        
        # Write events to file
        events_file = self.data_dir / "security_events.json"
        with open(events_file, 'w') as f:
            json.dump(security_events, f, indent=2)
            
        logger.info(f"Generated {len(security_events)} security events")
        logger.info(f"Data written to {events_file}")
        
        return security_events
    
    def generate_system_decisions(self, days=7, decisions_per_day=20):
        """Generate synthetic autonomous system decisions"""
        logger.info(f"Generating system decisions for {days} days")
        
        decisions = []
        now = datetime.now()
        
        # Decision types and outcomes
        decision_types = [
            "resource_allocation", "component_restart", "security_policy_update",
            "performance_optimization", "failover_activation", "ceiling_adjustment"
        ]
        
        outcomes = ["success", "partial_success", "failed"]
        outcome_weights = [0.85, 0.1, 0.05]  # 85% success, 10% partial, 5% failure
        
        # Generate a specified number of decisions per day
        for day in range(days):
            for _ in range(decisions_per_day):
                # Random timestamp within the day
                hour = random.randint(0, 23)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                timestamp = now - timedelta(days=days-day, hours=23-hour, minutes=59-minute, seconds=59-second)
                
                # Select decision properties
                decision_type = random.choice(decision_types)
                target_component = random.choice(self.components + ["system"])
                outcome = random.choices(outcomes, weights=outcome_weights)[0]
                
                # Generate decision description
                description = ""
                if decision_type == "resource_allocation":
                    resource = random.choice(["CPU", "memory", "disk", "network"])
                    amount = random.randint(10, 500)
                    description = f"Allocated {amount} units of {resource} to {target_component}"
                elif decision_type == "component_restart":
                    description = f"Restarted {target_component} due to {random.choice(self.anomaly_types)}"
                elif decision_type == "security_policy_update":
                    description = f"Updated security policy for {target_component} to mitigate {random.choice(self.security_event_types)}"
                elif decision_type == "performance_optimization":
                    description = f"Optimized {target_component} configuration for improved performance"
                elif decision_type == "failover_activation":
                    description = f"Activated failover for {target_component} due to primary instance failure"
                elif decision_type == "ceiling_adjustment":
                    ceiling_type = random.choice(["budget", "tokens", "requests", "time"])
                    direction = random.choice(["increased", "decreased"])
                    amount = random.randint(5, 20)
                    description = f"{direction.capitalize()} {ceiling_type} ceiling by {amount}% based on usage patterns"
                
                # Create decision record
                decision = {
                    "timestamp": timestamp.isoformat(),
                    "decision_id": f"DEC-{random.randint(10000, 99999)}",
                    "decision_type": decision_type,
                    "target_component": target_component,
                    "description": description,
                    "reasoning": f"Decision made based on analysis of {random.randint(5, 50)} data points and {random.randint(2, 10)} historical patterns",
                    "confidence": round(random.uniform(0.7, 1.0), 2),
                    "outcome": outcome,
                    "execution_time_ms": random.randint(50, 2000)
                }
                
                # Add failure reason if applicable
                if outcome == "failed":
                    decision["failure_reason"] = random.choice([
                        "Insufficient permissions",
                        "Resource unavailable",
                        "Component locked",
                        "System in inconsistent state",
                        "Timeout during execution"
                    ])
                elif outcome == "partial_success":
                    decision["partial_reason"] = random.choice([
                        "Some subcomponents unreachable",
                        "Partial resource allocation succeeded",
                        "Operation completed with warnings",
                        "Secondary actions failed"
                    ])
                
                decisions.append(decision)
        
        # Sort decisions by timestamp
        decisions.sort(key=lambda x: x["timestamp"])
        
        # Write decisions to file
        decisions_file = self.data_dir / "system_decisions.json"
        with open(decisions_file, 'w') as f:
            json.dump(decisions, f, indent=2)
            
        logger.info(f"Generated {len(decisions)} system decisions")
        logger.info(f"Data written to {decisions_file}")
        
        return decisions
    
    def generate_all(self):
        """Generate all test data types"""
        self.generate_component_metrics()
        self.generate_security_events()
        self.generate_system_decisions()
        
        logger.info("All test data generated successfully")


def main():
    """Main function to parse arguments and generate test data"""
    parser = argparse.ArgumentParser(description='Generate test data for EPOCH5 autonomous system evaluation')
    parser.add_argument('--days', type=int, default=7, help='Number of days of data to generate')
    parser.add_argument('--anomaly-probability', type=float, default=0.05, help='Probability of generating anomalies')
    parser.add_argument('--security-events-per-day', type=int, default=10, help='Number of security events per day')
    parser.add_argument('--decisions-per-day', type=int, default=20, help='Number of system decisions per day')
    parser.add_argument('--type', choices=['all', 'metrics', 'security', 'decisions'], default='all', 
                        help='Type of data to generate')
    
    args = parser.parse_args()
    
    generator = TestDataGenerator()
    
    if args.type == 'all':
        generator.generate_component_metrics(days=args.days, anomaly_probability=args.anomaly_probability)
        generator.generate_security_events(days=args.days, event_frequency=args.security_events_per_day)
        generator.generate_system_decisions(days=args.days, decisions_per_day=args.decisions_per_day)
    elif args.type == 'metrics':
        generator.generate_component_metrics(days=args.days, anomaly_probability=args.anomaly_probability)
    elif args.type == 'security':
        generator.generate_security_events(days=args.days, event_frequency=args.security_events_per_day)
    elif args.type == 'decisions':
        generator.generate_system_decisions(days=args.days, decisions_per_day=args.decisions_per_day)


if __name__ == "__main__":
    main()
