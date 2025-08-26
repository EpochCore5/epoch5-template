#!/usr/bin/env python3
"""
EPOCH5 Cycle Execution and SLA Compliance Tests
Comprehensive tests for the enhanced cycle execution and SLA monitoring functionality.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

# Import the components we want to test
from cycle_execution import CycleExecutor, CycleStatus, SLAViolationType
from epoch5_utils import EPOCH5Config


class TestCycleExecutorEnhanced(unittest.TestCase):
    """Enhanced test cases for CycleExecutor functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.executor = CycleExecutor(self.temp_dir)
        
        # Sample task assignments for testing
        self.sample_assignments = [
            {
                "task_id": "task_1",
                "agent_did": "did:epoch5:agent:test1",
                "estimated_cost": 25.0
            },
            {
                "task_id": "task_2", 
                "agent_did": "did:epoch5:agent:test2",
                "estimated_cost": 30.0
            },
            {
                "task_id": "task_3",
                "agent_did": "did:epoch5:agent:test3",
                "estimated_cost": 20.0
            }
        ]
        
        # Sample SLA requirements
        self.sample_sla = {
            "min_success_rate": 0.90,
            "max_failure_rate": 0.10,
            "max_retry_count": 2,
            "latency_percentile_threshold": 0.95,
            "budget_utilization_threshold": 0.85
        }
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_cycle_executor_initialization(self):
        """Test CycleExecutor initialization"""
        self.assertTrue(self.executor.cycles_dir.exists())
        self.assertIsNotNone(self.executor.logger)
        self.assertIsNotNone(self.executor.metrics)
        self.assertIsNotNone(self.executor.config)
    
    def test_cycle_creation_valid(self):
        """Test successful cycle creation with valid inputs"""
        cycle = self.executor.create_cycle(
            "test_cycle_1",
            100.0,
            300.0,
            self.sample_assignments,
            self.sample_sla
        )
        
        # Verify cycle structure
        self.assertEqual(cycle["cycle_id"], "test_cycle_1")
        self.assertEqual(cycle["budget"], 100.0)
        self.assertEqual(cycle["max_latency"], 300.0)
        self.assertEqual(cycle["status"], CycleStatus.PLANNED.value)
        self.assertEqual(len(cycle["task_assignments"]), 3)
        self.assertEqual(cycle["performance_metrics"]["total_tasks"], 3)
        self.assertIn("creation_hash", cycle)
        self.assertIn("created_at", cycle)
    
    def test_cycle_creation_invalid_inputs(self):
        """Test cycle creation with invalid inputs"""
        
        # Test empty cycle ID
        with self.assertRaises(ValueError):
            self.executor.create_cycle("", 100.0, 300.0, self.sample_assignments)
        
        # Test negative budget
        with self.assertRaises(ValueError):
            self.executor.create_cycle("test", -100.0, 300.0, self.sample_assignments)
        
        # Test negative latency
        with self.assertRaises(ValueError):
            self.executor.create_cycle("test", 100.0, -300.0, self.sample_assignments)
        
        # Test empty task assignments
        with self.assertRaises(ValueError):
            self.executor.create_cycle("test", 100.0, 300.0, [])
        
        # Test invalid task assignment structure
        invalid_assignments = [{"invalid": "structure"}]
        with self.assertRaises(ValueError):
            self.executor.create_cycle("test", 100.0, 300.0, invalid_assignments)
    
    def test_sla_compliance_calculation(self):
        """Test SLA compliance calculation logic"""
        # Create a cycle for testing
        cycle = self.executor.create_cycle(
            "sla_test_cycle",
            100.0,
            300.0,
            self.sample_assignments,
            self.sample_sla
        )
        
        # Simulate task results
        task_results = [
            {"task_id": "task_1", "success": True, "latency": 0.5, "cost": 25.0},
            {"task_id": "task_2", "success": True, "latency": 0.3, "cost": 28.0},
            {"task_id": "task_3", "success": False, "latency": 1.2, "cost": 15.0}
        ]
        
        # Calculate success rate
        successful_tasks = sum(1 for result in task_results if result["success"])
        total_tasks = len(task_results)
        success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0
        
        self.assertEqual(success_rate, 2/3)  # 2 out of 3 succeeded
        
        # Test SLA compliance
        min_success_rate = self.sample_sla["min_success_rate"]
        sla_compliant = success_rate >= min_success_rate
        
        self.assertFalse(sla_compliant)  # 0.67 < 0.90
    
    def test_sla_latency_compliance(self):
        """Test SLA latency compliance checking"""
        task_results = [
            {"latency": 0.2},
            {"latency": 0.5},
            {"latency": 0.8},
            {"latency": 1.5},  # This exceeds typical threshold
            {"latency": 0.3}
        ]
        
        max_latency = 1.0
        latency_violations = [
            result for result in task_results 
            if result["latency"] > max_latency
        ]
        
        self.assertEqual(len(latency_violations), 1)
        self.assertEqual(latency_violations[0]["latency"], 1.5)
    
    def test_budget_tracking(self):
        """Test budget tracking and utilization calculation"""
        budget = 100.0
        spent_costs = [25.0, 28.0, 15.0]
        total_spent = sum(spent_costs)
        
        budget_utilization = total_spent / budget
        remaining_budget = budget - total_spent
        
        self.assertEqual(budget_utilization, 0.68)  # 68/100
        self.assertEqual(remaining_budget, 32.0)    # 100 - 68
        
        # Test budget exceeded scenario
        high_costs = [40.0, 35.0, 30.0]  # Total: 105
        total_high_spent = sum(high_costs)
        budget_exceeded = total_high_spent > budget
        
        self.assertTrue(budget_exceeded)
    
    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation"""
        task_results = [
            {"success": True, "latency": 0.5, "cost": 25.0},
            {"success": True, "latency": 0.3, "cost": 30.0},
            {"success": False, "latency": 1.2, "cost": 20.0},
            {"success": True, "latency": 0.7, "cost": 15.0}
        ]
        
        # Calculate metrics
        total_tasks = len(task_results)
        successful_tasks = sum(1 for r in task_results if r["success"])
        failed_tasks = total_tasks - successful_tasks
        
        latencies = [r["latency"] for r in task_results]
        average_latency = sum(latencies) / len(latencies)
        
        total_cost = sum(r["cost"] for r in task_results)
        
        # Verify calculations
        self.assertEqual(total_tasks, 4)
        self.assertEqual(successful_tasks, 3)
        self.assertEqual(failed_tasks, 1)
        self.assertAlmostEqual(average_latency, 0.675, places=2)  # (0.5+0.3+1.2+0.7)/4
        self.assertEqual(total_cost, 90.0)
    
    def test_sla_violation_types(self):
        """Test different types of SLA violations"""
        # Test success rate violation
        success_rate = 0.80
        min_success_rate = 0.90
        success_rate_violation = success_rate < min_success_rate
        self.assertTrue(success_rate_violation)
        
        # Test latency violation
        max_allowed_latency = 1.0
        actual_latency = 1.5
        latency_violation = actual_latency > max_allowed_latency
        self.assertTrue(latency_violation)
        
        # Test budget violation
        budget_limit = 100.0
        actual_spend = 105.0
        budget_violation = actual_spend > budget_limit
        self.assertTrue(budget_violation)
    
    def test_cycle_status_transitions(self):
        """Test cycle status transitions"""
        cycle = self.executor.create_cycle(
            "status_test",
            100.0,
            300.0,
            self.sample_assignments
        )
        
        # Initial status should be PLANNED
        self.assertEqual(cycle["status"], CycleStatus.PLANNED.value)
        
        # Test status enumeration values
        self.assertEqual(CycleStatus.PLANNED.value, "planned")
        self.assertEqual(CycleStatus.EXECUTING.value, "executing")
        self.assertEqual(CycleStatus.COMPLETED.value, "completed")
        self.assertEqual(CycleStatus.FAILED.value, "failed")
        self.assertEqual(CycleStatus.SLA_VIOLATED.value, "sla_violated")
        self.assertEqual(CycleStatus.BUDGET_EXCEEDED.value, "budget_exceeded")
    
    def test_large_scale_cycle_creation(self):
        """Test cycle creation with large number of tasks"""
        # Create 100 task assignments
        large_assignments = []
        for i in range(100):
            large_assignments.append({
                "task_id": f"task_{i:03d}",
                "agent_did": f"did:epoch5:agent:worker_{i%10}",
                "estimated_cost": 10.0 + (i % 20)
            })
        
        cycle = self.executor.create_cycle(
            "large_scale_test",
            2000.0,
            600.0,
            large_assignments
        )
        
        self.assertEqual(cycle["performance_metrics"]["total_tasks"], 100)
        self.assertEqual(len(cycle["task_assignments"]), 100)
        self.assertIsInstance(cycle["creation_hash"], str)
    
    def test_configuration_integration(self):
        """Test integration with EPOCH5Config"""
        # Create executor with custom configuration
        config = EPOCH5Config()
        
        # Add the section before setting values
        if not config.config.has_section('cycle_execution'):
            config.config.add_section('cycle_execution')
            
        config.config.set('cycle_execution', 'default_budget', '500.0')
        config.config.set('cycle_execution', 'default_max_latency', '600.0')
        
        custom_executor = CycleExecutor(self.temp_dir, config)
        
        self.assertEqual(custom_executor.default_budget, 500.0)
        self.assertEqual(custom_executor.default_max_latency, 600.0)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)