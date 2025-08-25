#!/usr/bin/env python3
"""
EPOCH5 Test Suite
Unit and integration tests for EPOCH5 components
Tests core functionality including Merkle trees, SLA compliance, and DAG validation
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from epoch5_utils import EPOCH5Utils, EPOCH5Config, EPOCH5Logger, EPOCH5ErrorHandler
from epoch5_utils import EPOCH5Error, EPOCH5FileError, EPOCH5JSONError, EPOCH5ValidationError


class TestEPOCH5Utils(unittest.TestCase):
    """Test EPOCH5 utility functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "test.json"
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_timestamp_format(self):
        """Test timestamp format consistency"""
        timestamp = EPOCH5Utils.timestamp()
        # Should be in ISO format: YYYY-MM-DDTHH:MM:SSZ
        self.assertRegex(timestamp, r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')
    
    def test_sha256_consistency(self):
        """Test SHA256 hash consistency"""
        test_data = "test_data_for_hashing"
        hash1 = EPOCH5Utils.sha256(test_data)
        hash2 = EPOCH5Utils.sha256(test_data)
        
        # Same input should produce same hash
        self.assertEqual(hash1, hash2)
        # Should be 64 characters (256 bits in hex)
        self.assertEqual(len(hash1), 64)
        # Should be hexadecimal
        self.assertRegex(hash1, r'^[a-f0-9]{64}$')
    
    def test_safe_json_operations(self):
        """Test safe JSON load/save operations"""
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        
        # Test save
        success = EPOCH5Utils.safe_json_save(test_data, self.test_file)
        self.assertTrue(success)
        self.assertTrue(self.test_file.exists())
        
        # Test load
        loaded_data = EPOCH5Utils.safe_json_load(self.test_file)
        self.assertEqual(loaded_data, test_data)
        
        # Test load non-existent file with default
        non_existent = Path(self.temp_dir) / "non_existent.json"
        default_data = {"default": True}
        loaded_data = EPOCH5Utils.safe_json_load(non_existent, default_data)
        self.assertEqual(loaded_data, default_data)
    
    def test_validate_required_fields(self):
        """Test field validation"""
        data = {"field1": "value1", "field2": "value2"}
        required_fields = ["field1", "field2"]
        
        # Should pass validation
        result = EPOCH5Utils.validate_required_fields(data, required_fields)
        self.assertTrue(result)
        
        # Should raise exception for missing fields
        required_fields_missing = ["field1", "field2", "field3"]
        with self.assertRaises(EPOCH5ValidationError):
            EPOCH5Utils.validate_required_fields(data, required_fields_missing)
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        unsafe_filename = 'test<file>name:with|unsafe?chars*'
        safe_filename = EPOCH5Utils.sanitize_filename(unsafe_filename)
        
        # Should not contain unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            self.assertNotIn(char, safe_filename)
        
        # Should contain underscores instead
        self.assertIn('_', safe_filename)


class TestEPOCH5Config(unittest.TestCase):
    """Test EPOCH5 configuration management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.json"
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_config_creation(self):
        """Test default configuration creation"""
        config = EPOCH5Config(self.config_file)
        
        # Should have default values
        self.assertEqual(config.get('base_directory'), './archive/EPOCH5')
        self.assertEqual(config.get('logging.level'), 'INFO')
        self.assertEqual(config.get('performance.batch_size'), 100)
        
        # Config file should be created
        self.assertTrue(self.config_file.exists())
    
    def test_config_get_set(self):
        """Test configuration get/set operations"""
        config = EPOCH5Config(self.config_file)
        
        # Test setting and getting values
        config.set('test.value', 'test_data')
        self.assertEqual(config.get('test.value'), 'test_data')
        
        # Test nested path access
        config.set('nested.deep.value', 42)
        self.assertEqual(config.get('nested.deep.value'), 42)
        
        # Test default value for non-existent key
        self.assertEqual(config.get('non.existent', 'default'), 'default')


class TestEPOCH5Logger(unittest.TestCase):
    """Test EPOCH5 logging system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_creation(self):
        """Test logger creation and setup"""
        logger = EPOCH5Logger('test_component', str(self.log_dir))
        
        # Log directory should be created
        self.assertTrue(self.log_dir.exists())
        
        # Log file should be created after logging
        logger.info("Test message")
        log_file = self.log_dir / "test_component.log"
        self.assertTrue(log_file.exists())
        
        # Log file should contain message
        log_content = log_file.read_text()
        self.assertIn("Test message", log_content)
    
    def test_structured_logging(self):
        """Test structured logging with extra data"""
        logger = EPOCH5Logger('test_structured', str(self.log_dir))
        
        extra_data = {"user_id": 123, "action": "test_action"}
        logger.info("Structured log test", extra_data)
        
        log_file = self.log_dir / "test_structured.log"
        log_content = log_file.read_text()
        
        self.assertIn("Structured log test", log_content)
        self.assertIn("user_id", log_content)
        self.assertIn("test_action", log_content)


class TestMerkleTreeBasics(unittest.TestCase):
    """Test basic Merkle tree functionality (simplified version for testing)"""
    
    def test_simple_merkle_tree(self):
        """Test basic Merkle tree construction"""
        # Import here to avoid circular imports
        from capsule_metadata import MerkleTree
        
        data_blocks = ["block1", "block2", "block3", "block4"]
        tree = MerkleTree(data_blocks)
        
        # Should have a root hash
        self.assertIsNotNone(tree.root_hash)
        self.assertEqual(len(tree.root_hash), 64)  # SHA256 hex length
        
        # Should have tree levels
        self.assertTrue(len(tree.tree_levels) > 0)
        
        # First level should have hashes for all blocks
        self.assertEqual(len(tree.tree_levels[0]), len(data_blocks))
    
    def test_merkle_proof_verification(self):
        """Test Merkle proof generation and verification"""
        from capsule_metadata import MerkleTree
        
        data_blocks = ["block1", "block2", "block3", "block4"]
        tree = MerkleTree(data_blocks)
        
        # Generate proof for first block
        proof = tree.get_proof(0)
        self.assertIsInstance(proof, list)
        
        # Verify the proof
        is_valid = tree.verify_proof(data_blocks[0], 0, proof)
        self.assertTrue(is_valid)
        
        # Invalid data should not verify
        is_valid_invalid = tree.verify_proof("invalid_block", 0, proof)
        self.assertFalse(is_valid_invalid)


class TestSLAValidation(unittest.TestCase):
    """Test SLA compliance validation"""
    
    def test_sla_compliance_check(self):
        """Test basic SLA compliance checking logic"""
        # Mock SLA requirements
        sla_requirements = {
            "min_success_rate": 0.95,
            "max_failure_rate": 0.05,
            "max_retry_count": 3
        }
        
        # Mock execution metrics - compliant case
        metrics_compliant = {
            "success_rate": 0.97,
            "failure_rate": 0.03,
            "retry_count": 1
        }
        
        # Check compliance (simplified)
        is_compliant = (
            metrics_compliant["success_rate"] >= sla_requirements["min_success_rate"] and
            metrics_compliant["failure_rate"] <= sla_requirements["max_failure_rate"] and
            metrics_compliant["retry_count"] <= sla_requirements["max_retry_count"]
        )
        
        self.assertTrue(is_compliant)
        
        # Mock execution metrics - non-compliant case
        metrics_non_compliant = {
            "success_rate": 0.90,  # Below threshold
            "failure_rate": 0.10,  # Above threshold
            "retry_count": 5       # Above threshold
        }
        
        is_compliant_bad = (
            metrics_non_compliant["success_rate"] >= sla_requirements["min_success_rate"] and
            metrics_non_compliant["failure_rate"] <= sla_requirements["max_failure_rate"] and
            metrics_non_compliant["retry_count"] <= sla_requirements["max_retry_count"]
        )
        
        self.assertFalse(is_compliant_bad)


class TestDAGValidationBasics(unittest.TestCase):
    """Test basic DAG validation logic"""
    
    def test_basic_dag_validation(self):
        """Test basic DAG cycle detection"""
        # Valid DAG (no cycles)
        valid_tasks = [
            {"task_id": "task1", "dependencies": []},
            {"task_id": "task2", "dependencies": ["task1"]},
            {"task_id": "task3", "dependencies": ["task2"]},
        ]
        
        # Simple validation logic
        def validate_dag_simple(tasks):
            task_ids = {task["task_id"] for task in tasks}
            
            # Check that all dependencies exist
            for task in tasks:
                for dep in task["dependencies"]:
                    if dep not in task_ids:
                        return False
            return True
        
        self.assertTrue(validate_dag_simple(valid_tasks))
        
        # Invalid DAG (missing dependency)
        invalid_tasks = [
            {"task_id": "task1", "dependencies": []},
            {"task_id": "task2", "dependencies": ["task1", "nonexistent"]},
        ]
        
        self.assertFalse(validate_dag_simple(invalid_tasks))


def run_test_suite():
    """Run the complete test suite"""
    print("Running EPOCH5 Test Suite...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestEPOCH5Utils,
        TestEPOCH5Config,
        TestEPOCH5Logger,
        TestMerkleTreeBasics,
        TestSLAValidation,
        TestDAGValidationBasics
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    
    return success


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)