#!/usr/bin/env python3
"""
Tests for the ceiling management security features.
"""

import os
import sys
import unittest
import tempfile
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from ceiling_manager import CeilingManager, ServiceTier, CeilingType
    from epoch_audit import EpochAudit
    CEILING_SYSTEM_AVAILABLE = True
except ImportError:
    CEILING_SYSTEM_AVAILABLE = False

@unittest.skipIf(not CEILING_SYSTEM_AVAILABLE, "Ceiling management system not available")
class TestCeilingSecurityFeatures(unittest.TestCase):
    """Test suite for ceiling management security features."""
    
    def setUp(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.base_dir = Path(self.temp_dir) / "EPOCH5_TEST"
        
        # Initialize managers
        self.ceiling_manager = CeilingManager(self.base_dir)
        self.audit_system = EpochAudit(self.base_dir)
        
        # Create test configuration
        self.config_id = "test_security_config"
        config = self.ceiling_manager.create_ceiling_configuration(
            self.config_id, ServiceTier.PROFESSIONAL
        )
        self.ceiling_manager.add_configuration(config)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def test_ceiling_enforcement_with_audit(self):
        """Test that ceiling enforcement correctly logs to audit system."""
        # Get baseline event count
        before_events = len(self.audit_system.generate_audit_scroll())
        
        # Enforce ceiling and verify it was recorded
        result = self.ceiling_manager.enforce_value_ceiling(
            self.config_id, CeilingType.BUDGET, 1000.0
        )
        
        # Check that value was capped
        self.assertTrue(result["capped"])
        self.assertEqual(result["final_value"], result["ceiling"])
        self.assertLess(result["final_value"], result["original_value"])
        
        # Check that event was logged to audit system
        after_events = self.audit_system.generate_audit_scroll()
        self.assertGreater(len(after_events), before_events)
        
        # Verify the last event is a ceiling enforcement
        ceiling_events = [e for e in after_events if "ceiling_enforcement" in e["event"]]
        self.assertGreaterEqual(len(ceiling_events), 1)
    
    def test_audit_seal_verification(self):
        """Test verification of audit seals."""
        # Create multiple audit events
        for i in range(5):
            self.audit_system.log_event(
                f"test_event_{i}",
                f"Test event {i}",
                {"test_data": i}
            )
        
        # Verify the seals
        verification_result = self.audit_system.verify_seals()
        
        # Check verification status
        self.assertEqual(verification_result["status"], "PASSED")
        self.assertGreaterEqual(verification_result["valid_count"], 5)
        self.assertEqual(verification_result["invalid_count"], 0)
    
    def test_security_with_performance_adjustment(self):
        """Test security features when adjusting ceilings based on performance."""
        # Define performance metrics
        performance_metrics = {
            "success_rate": 0.98,
            "actual_latency": 45.0,
            "spent_budget": 80.0
        }
        
        # Get baseline event count
        before_events = len(self.audit_system.generate_audit_scroll())
        
        # Adjust ceiling based on performance
        adjusted_config = self.ceiling_manager.adjust_ceiling_for_performance(
            self.config_id, performance_metrics
        )
        
        # Verify adjustment was made
        self.assertGreater(adjusted_config["performance_score"], 1.0)
        self.assertIn("dynamic_adjustments", adjusted_config)
        
        # Check that audit events were created
        after_events = self.audit_system.generate_audit_scroll()
        self.assertGreater(len(after_events), before_events)
        
        # Verify security of the events
        verification_result = self.audit_system.verify_seals()
        self.assertEqual(verification_result["status"], "PASSED")
    
    def test_get_effective_ceiling_with_security(self):
        """Test getting effective ceiling values with security integration."""
        # Get effective ceiling
        budget_ceiling = self.ceiling_manager.get_effective_ceiling(
            self.config_id, CeilingType.BUDGET
        )
        
        # Verify ceiling value is valid
        self.assertGreater(budget_ceiling, 0.0)
        
        # Check that a verification event was logged
        events = self.audit_system.generate_audit_scroll()
        verification_events = [e for e in events if "ceiling_verification" in e["event"]]
        self.assertGreaterEqual(len(verification_events), 1)

if __name__ == "__main__":
    unittest.main()
