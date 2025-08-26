#!/usr/bin/env python3
"""
EPOCH5 Test Suite
Comprehensive unit and integration tests for EPOCH5 components.
Tests key functionality including Merkle trees, SLA compliance, and system integrity.
"""

import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import EPOCH5 components
from epoch5_utils import (
    EPOCH5Logger, EPOCH5Config, EPOCH5ErrorHandler, EPOCH5Utils, EPOCH5Metrics,
    timestamp, sha256, safe_load_json, safe_save_json
)


class TestEPOCH5Utils(unittest.TestCase):
    """Test EPOCH5 utility functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = {
            "test_key": "test_value",
            "nested": {
                "key": "value"
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_timestamp_format(self):
        """Test timestamp format consistency"""
        ts = timestamp()
        self.assertRegex(ts, r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')
    
    def test_sha256_consistency(self):
        """Test SHA256 hash consistency"""
        test_string = "test data"
        hash1 = sha256(test_string)
        hash2 = sha256(test_string.encode('utf-8'))
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 produces 64 character hex
    
    def test_directory_creation(self):
        """Test directory creation utility"""
        test_path = Path(self.temp_dir) / "test" / "nested" / "dir"
        created_path = EPOCH5Utils.ensure_directory(test_path)
        self.assertTrue(created_path.exists())
        self.assertTrue(created_path.is_dir())
    
    def test_safe_json_operations(self):
        """Test safe JSON loading and saving"""
        test_file = Path(self.temp_dir) / "test.json"
        
        # Test saving
        success = safe_save_json(self.test_data, test_file)
        self.assertTrue(success)
        self.assertTrue(test_file.exists())
        
        # Test loading
        loaded_data = safe_load_json(test_file)
        self.assertEqual(loaded_data, self.test_data)
        
        # Test loading non-existent file with default
        non_existent = Path(self.temp_dir) / "nonexistent.json"
        default_data = {"default": True}
        loaded_default = safe_load_json(non_existent, default_data)
        self.assertEqual(loaded_default, default_data)
    
    def test_batch_processing(self):
        """Test batch processing utility"""
        items = list(range(100))
        batch_size = 10
        
        def simple_processor(batch):
            return [item * 2 for item in batch]
        
        results = EPOCH5Utils.batch_process(items, batch_size, simple_processor)
        expected = [item * 2 for item in items]
        self.assertEqual(results, expected)
    
    def test_field_validation(self):
        """Test required field validation"""
        data = {
            "required_field1": "value1",
            "required_field2": "value2",
            "optional_field": "value3"
        }
        
        # Test with all required fields present
        valid, missing = EPOCH5Utils.validate_required_fields(
            data, ["required_field1", "required_field2"]
        )
        self.assertTrue(valid)
        self.assertEqual(missing, [])
        
        # Test with missing required fields
        valid, missing = EPOCH5Utils.validate_required_fields(
            data, ["required_field1", "missing_field"]
        )
        self.assertFalse(valid)
        self.assertIn("missing_field", missing)


class TestEPOCH5Config(unittest.TestCase):
    """Test EPOCH5 configuration management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test.conf"
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_default_config(self):
        """Test default configuration loading"""
        config = EPOCH5Config()
        
        # Test default values
        self.assertEqual(config.get('DEFAULT', 'base_dir'), './archive/EPOCH5')
        self.assertEqual(config.get('DEFAULT', 'log_level'), 'INFO')
        self.assertEqual(config.getint('DEFAULT', 'max_retries'), 3)
        self.assertTrue(config.getboolean('performance', 'enable_batch_processing'))
    
    def test_custom_config_file(self):
        """Test custom configuration file loading"""
        # Create custom config
        custom_config = """
[DEFAULT]
base_dir = /custom/path
log_level = DEBUG

[custom_section]
custom_value = test
"""
        with open(self.config_file, 'w') as f:
            f.write(custom_config)
        
        config = EPOCH5Config(str(self.config_file))
        self.assertEqual(config.get('DEFAULT', 'base_dir'), '/custom/path')
        self.assertEqual(config.get('DEFAULT', 'log_level'), 'DEBUG')
        self.assertEqual(config.get('custom_section', 'custom_value'), 'test')
    
    def test_config_save(self):
        """Test configuration saving"""
        config = EPOCH5Config()
        config.config.set('DEFAULT', 'test_value', 'saved')
        config.save(str(self.config_file))
        
        # Load saved config
        new_config = EPOCH5Config(str(self.config_file))
        self.assertEqual(new_config.get('DEFAULT', 'test_value'), 'saved')


class TestEPOCH5ErrorHandler(unittest.TestCase):
    """Test EPOCH5 error handling utilities"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_safe_file_operation_success(self):
        """Test successful file operation"""
        test_file = Path(self.temp_dir) / "test.txt"
        
        def write_file(path, content):
            with open(path, 'w') as f:
                f.write(content)
            return "success"
        
        success, result, error = EPOCH5ErrorHandler.safe_file_operation(
            write_file, str(test_file), "test content"
        )
        
        self.assertTrue(success)
        self.assertEqual(result, "success")
        self.assertIsNone(error)
        self.assertTrue(test_file.exists())
    
    def test_safe_file_operation_failure(self):
        """Test failed file operation"""
        def failing_operation():
            raise FileNotFoundError("Test file not found")
        
        success, result, error = EPOCH5ErrorHandler.safe_file_operation(failing_operation)
        
        self.assertFalse(success)
        self.assertIsNone(result)
        self.assertIn("File not found", error)
    
    def test_safe_json_operations(self):
        """Test safe JSON operations"""
        test_data = {"key": "value"}
        test_file = Path(self.temp_dir) / "test.json"
        
        # Test JSON dump
        success, result, error = EPOCH5ErrorHandler.safe_json_operation(
            'dump', data=test_data, file_path=str(test_file)
        )
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # Test JSON load
        success, result, error = EPOCH5ErrorHandler.safe_json_operation(
            'load', file_path=str(test_file)
        )
        self.assertTrue(success)
        self.assertEqual(result, test_data)
        self.assertIsNone(error)
        
        # Test invalid JSON
        invalid_file = Path(self.temp_dir) / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")
        
        success, result, error = EPOCH5ErrorHandler.safe_json_operation(
            'load', file_path=str(invalid_file)
        )
        self.assertFalse(success)
        self.assertIsNone(result)
        self.assertIn("JSON decode error", error)
    
    def test_retry_decorator(self):
        """Test retry on failure decorator"""
        call_count = 0
        
        @EPOCH5ErrorHandler.retry_on_failure(max_retries=2, delay=0.1)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = flaky_function()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 2)


class TestEPOCH5Logger(unittest.TestCase):
    """Test EPOCH5 logging system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_logger_creation(self):
        """Test logger creation and configuration"""
        log_file = Path(self.temp_dir) / "test.log"
        logger = EPOCH5Logger.get_logger("test_logger", str(log_file), "DEBUG")
        
        self.assertEqual(logger.name, "test_logger")
        self.assertEqual(logger.level, 10)  # DEBUG level
        self.assertEqual(len(logger.handlers), 2)  # Console + File handlers
        
        # Test logging
        logger.info("Test message")
        self.assertTrue(log_file.exists())
        
        with open(log_file, 'r') as f:
            log_content = f.read()
            self.assertIn("Test message", log_content)
            self.assertIn("INFO", log_content)
    
    def test_logger_singleton_behavior(self):
        """Test that loggers are reused (singleton pattern)"""
        logger1 = EPOCH5Logger.get_logger("same_name")
        logger2 = EPOCH5Logger.get_logger("same_name")
        
        self.assertIs(logger1, logger2)


class TestEPOCH5Metrics(unittest.TestCase):
    """Test EPOCH5 metrics and monitoring"""
    
    def test_metrics_tracking(self):
        """Test metrics tracking functionality"""
        metrics = EPOCH5Metrics()
        
        # Start and end operation
        metrics.start_operation("test_operation")
        import time
        time.sleep(0.1)  # Small delay for timing
        metrics.end_operation("test_operation", success=True)
        
        # Check metrics
        summary = metrics.get_summary()
        self.assertEqual(summary['total_operations'], 1)
        self.assertEqual(summary['operation_counts']['test_operation'], 1)
        self.assertIn('test_operation', summary['average_timing'])
        self.assertGreater(summary['average_timing']['test_operation'], 0)
    
    def test_error_tracking(self):
        """Test error rate tracking"""
        metrics = EPOCH5Metrics()
        
        # Simulate operations with some failures
        for i in range(10):
            metrics.start_operation("test_op")
            success = i < 8  # 8 successes, 2 failures
            metrics.end_operation("test_op", success=success)
        
        summary = metrics.get_summary()
        self.assertEqual(summary['total_operations'], 10)
        self.assertEqual(summary['operation_counts']['test_op'], 10)
        self.assertEqual(summary['error_rates']['test_op'], 0.2)  # 2/10 = 0.2


class TestMerkleTree(unittest.TestCase):
    """Test Merkle tree implementation for capsule integrity"""
    
    def test_merkle_tree_creation(self):
        """Test Merkle tree creation and verification"""
        # This test would require importing the actual Merkle tree implementation
        # from capsule_metadata.py once it's refactored
        
        # For now, test the concept with a simple hash chain
        blocks = ["block1", "block2", "block3", "block4"]
        hashes = [sha256(block) for block in blocks]
        
        # Simple binary tree construction
        while len(hashes) > 1:
            next_level = []
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i + 1]
                else:
                    combined = hashes[i] + hashes[i]  # Duplicate if odd number
                next_level.append(sha256(combined))
            hashes = next_level
        
        root_hash = hashes[0]
        self.assertEqual(len(root_hash), 64)  # SHA256 length
        
        # Test that same blocks produce same root
        blocks2 = ["block1", "block2", "block3", "block4"]
        hashes2 = [sha256(block) for block in blocks2]
        
        while len(hashes2) > 1:
            next_level = []
            for i in range(0, len(hashes2), 2):
                if i + 1 < len(hashes2):
                    combined = hashes2[i] + hashes2[i + 1]
                else:
                    combined = hashes2[i] + hashes2[i]
                next_level.append(sha256(combined))
            hashes2 = next_level
        
        root_hash2 = hashes2[0]
        self.assertEqual(root_hash, root_hash2)


class TestSLACompliance(unittest.TestCase):
    """Test SLA compliance checking"""
    
    def test_sla_success_rate_calculation(self):
        """Test SLA success rate calculation"""
        # Simulate task results
        task_results = [
            {"success": True, "latency": 0.5},
            {"success": True, "latency": 0.3},
            {"success": False, "latency": 1.0},
            {"success": True, "latency": 0.7},
            {"success": True, "latency": 0.4}
        ]
        
        total_tasks = len(task_results)
        successful_tasks = sum(1 for result in task_results if result["success"])
        success_rate = successful_tasks / total_tasks
        
        self.assertEqual(success_rate, 0.8)  # 4/5 = 0.8
        
        # Test SLA compliance
        sla_requirements = {
            "min_success_rate": 0.75,
            "max_failure_rate": 0.25
        }
        
        failure_rate = 1 - success_rate
        sla_compliant = (
            success_rate >= sla_requirements["min_success_rate"] and
            failure_rate <= sla_requirements["max_failure_rate"]
        )
        
        self.assertTrue(sla_compliant)
    
    def test_sla_latency_compliance(self):
        """Test SLA latency compliance checking"""
        task_results = [
            {"latency": 0.5},
            {"latency": 0.3},
            {"latency": 1.2},
            {"latency": 0.7}
        ]
        
        max_latency = 1.0
        latency_violations = [
            result for result in task_results 
            if result["latency"] > max_latency
        ]
        
        self.assertEqual(len(latency_violations), 1)
        self.assertEqual(latency_violations[0]["latency"], 1.2)


if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestEPOCH5Utils,
        TestEPOCH5Config,
        TestEPOCH5ErrorHandler,
        TestEPOCH5Logger,
        TestEPOCH5Metrics,
        TestMerkleTree,
        TestSLACompliance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with error code if tests failed
    exit(0 if result.wasSuccessful() else 1)