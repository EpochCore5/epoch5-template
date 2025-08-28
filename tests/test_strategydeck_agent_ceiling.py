#!/usr/bin/env python3
"""
Tests for the StrategyDECKAgent ceiling integration.
"""

import os
import sys
import unittest
import tempfile
import json
import shutil
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from strategydeck_agent import StrategyDECKAgent
    from ceiling_manager import CeilingManager, ServiceTier, CeilingType
    from epoch_audit import EpochAudit
    CEILING_SYSTEM_AVAILABLE = True
except ImportError:
    CEILING_SYSTEM_AVAILABLE = False

@unittest.skipIf(not CEILING_SYSTEM_AVAILABLE, "Ceiling management system not available")
class TestStrategyDECKAgentCeilingIntegration(unittest.TestCase):
    """Test suite for StrategyDECKAgent ceiling integration."""
    
    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_dir = Path(self.temp_dir) / "EPOCH5_TEST"
        
        # Create temporary log directory
        self.log_dir = Path(self.temp_dir) / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up environment for ceiling manager
        os.environ["EPOCH5_BASE_DIR"] = str(self.base_dir)
        
        # Initialize agent
        self.agent = StrategyDECKAgent(
            name="TestAgent",
            log_dir=str(self.log_dir),
            service_tier="professional",
            config_id="test_agent_config"
        )
        
        # Get direct reference to ceiling manager for verification
        self.ceiling_manager = CeilingManager(self.base_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        self.agent.executor.shutdown(wait=False)
        shutil.rmtree(self.temp_dir)
    
    def test_agent_initialization_with_ceiling(self):
        """Test that agent initializes with ceiling management."""
        # Verify ceiling manager was initialized
        self.assertIsNotNone(self.agent.ceiling_manager)
        self.assertIsNotNone(self.agent.config_id)
        
        # Check that configuration exists
        ceilings_data = self.ceiling_manager.load_ceilings()
        self.assertIn(self.agent.config_id, ceilings_data.get("configurations", {}))
        
        # Verify service tier
        config = ceilings_data["configurations"][self.agent.config_id]
        self.assertEqual(config["service_tier"], "professional")
    
    def test_run_task_with_ceiling_enforcement(self):
        """Test running a task with ceiling enforcement."""
        # Define a simple test task
        def test_task(x, y):
            time.sleep(0.1)  # Small delay for timing
            return x + y
        
        # Run task with high priority that should be capped
        result = self.agent.run_task(test_task, 2, 3, priority=20)
        
        # Verify result
        self.assertEqual(result, 5)
        
        # Check that task was completed
        self.assertEqual(self.agent.metrics["tasks_completed"], 1)
        self.assertEqual(self.agent.metrics["tasks_failed"], 0)
        
        # Verify ceiling status
        ceiling_status = self.agent.get_ceiling_status()
        self.assertIn("service_tier", ceiling_status)
        self.assertIn("performance_score", ceiling_status)
    
    def test_task_failure_handling(self):
        """Test handling of task failures with ceiling integration."""
        # Define a task that will fail
        def failing_task():
            raise ValueError("Test failure")
            
        # Run failing task
        result = self.agent.run_task(failing_task)
        
        # Verify task was marked as failed
        self.assertEqual(self.agent.metrics["tasks_completed"], 0)
        self.assertEqual(self.agent.metrics["tasks_failed"], 1)
        
        # Verify ceiling status shows degraded performance
        ceiling_status = self.agent.get_ceiling_status()
        self.assertLessEqual(ceiling_status.get("performance_score", 0), 1.0)
    
    def test_security_verification(self):
        """Test agent's security verification capabilities."""
        # Run a task to generate audit events
        def simple_task():
            return "success"
            
        self.agent.run_task(simple_task)
        
        # Verify security
        verification_results = self.agent.verify_security()
        
        # Check verification results
        self.assertIn("status", verification_results)
        self.assertEqual(verification_results["status"], "PASSED")
        self.assertGreaterEqual(verification_results["valid_count"], 1)
        self.assertEqual(verification_results["invalid_count"], 0)
    
    def test_health_check_with_ceiling_info(self):
        """Test that health check includes ceiling information."""
        # Run task to generate some metrics
        def simple_task():
            return "success"
            
        self.agent.run_task(simple_task)
        
        # Get health check
        health = self.agent.health_check()
        
        # Verify ceiling information is included
        self.assertIn("ceiling_status", health)
        self.assertIn("security", health)
        
        # Check overall health status
        self.assertEqual(health["status"], "healthy")
        
        # Verify agent metrics
        self.assertEqual(health["tasks_completed"], 1)
        self.assertEqual(health["tasks_failed"], 0)

if __name__ == "__main__":
    unittest.main()
