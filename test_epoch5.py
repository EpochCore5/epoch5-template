#!/usr/bin/env python3
"""
Basic integration tests for EPOCH5 Template
Tests core functionality of Python modules and shell scripts
"""

import os
import sys
import subprocess
import tempfile
import shutil
import json
from pathlib import Path

class EPOCH5Tests:
    def __init__(self):
        self.test_dir = None
        self.original_dir = os.getcwd()
        self.passed = 0
        self.failed = 0
        
    def setup_test_environment(self):
        """Create temporary directory for testing"""
        self.test_dir = tempfile.mkdtemp(prefix="epoch5_test_")
        os.chdir(self.test_dir)
        print(f"🧪 Test environment: {self.test_dir}")
        
        # Copy necessary files to test directory
        original_files = [
            "integration.py", "agent_management.py", "policy_grants.py", 
            "dag_management.py", "cycle_execution.py", "capsule_metadata.py",
            "meta_capsule.py", "epoch5.sh"
        ]
        
        for file in original_files:
            src_path = os.path.join(self.original_dir, file)
            if os.path.exists(src_path):
                shutil.copy2(src_path, self.test_dir)
                # Make epoch5.sh executable
                if file == "epoch5.sh":
                    os.chmod(file, 0o755)
    
    def cleanup_test_environment(self):
        """Clean up test environment"""
        os.chdir(self.original_dir)
        if self.test_dir:
            shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def run_test(self, test_name, test_func):
        """Run a single test and track results"""
        try:
            print(f"🔍 Running {test_name}...")
            test_func()
            print(f"✅ {test_name} PASSED")
            self.passed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED: {e}")
            self.failed += 1
    
    def test_python_compilation(self):
        """Test that all Python modules compile without errors"""
        python_files = ["integration.py", "agent_management.py", "policy_grants.py", 
                       "dag_management.py", "cycle_execution.py", "capsule_metadata.py", "meta_capsule.py"]
        
        for py_file in python_files:
            if os.path.exists(py_file):
                result = subprocess.run([sys.executable, "-m", "py_compile", py_file], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Compilation failed for {py_file}: {result.stderr}")
    
    def test_shell_script_syntax(self):
        """Test that shell script has valid syntax"""
        if os.path.exists("epoch5.sh"):
            result = subprocess.run(["bash", "-n", "epoch5.sh"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Shell script syntax error: {result.stderr}")
    
    def test_integration_help(self):
        """Test that integration.py help works"""
        result = subprocess.run([sys.executable, "integration.py", "--help"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Integration help failed: {result.stderr}")
        if "EPOCH5 Integration System" not in result.stdout:
            raise Exception("Help output doesn't contain expected text")
    
    def test_integration_demo_setup(self):
        """Test that demo setup works"""
        result = subprocess.run([sys.executable, "integration.py", "setup-demo"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise Exception(f"Demo setup failed: {result.stderr}")
        if "Demo environment setup completed" not in result.stdout:
            raise Exception("Demo setup didn't complete successfully")
    
    def test_integration_status(self):
        """Test that system status works"""
        # First run setup-demo
        subprocess.run([sys.executable, "integration.py", "setup-demo"], 
                      capture_output=True, text=True, timeout=30)
        
        result = subprocess.run([sys.executable, "integration.py", "status"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise Exception(f"Status check failed: {result.stderr}")
        if "System Status" not in result.stdout:
            raise Exception("Status output doesn't contain expected text")
    
    def test_agent_creation_validation(self):
        """Test agent creation input validation"""
        # Test invalid skills
        result = subprocess.run([sys.executable, "integration.py", "agents", "create", ""], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            raise Exception("Empty skill should have failed validation")
        if "Invalid skill names" not in result.stdout and "Invalid skill names" not in result.stderr:
            raise Exception("Expected validation error message not found")
    
    def test_epoch5_script_execution(self):
        """Test that epoch5.sh runs successfully"""
        env = os.environ.copy()
        env["DELAY_HOURS_P1_P2"] = "0"
        env["DELAY_HOURS_P2_P3"] = "0"
        
        result = subprocess.run(["./epoch5.sh"], 
                              capture_output=True, text=True, env=env, timeout=60)
        if result.returncode != 0:
            raise Exception(f"epoch5.sh failed: {result.stderr}")
        if "EPOCH 5 Complete" not in result.stdout:
            raise Exception("Script didn't complete successfully")
        
        # Check that files were created
        expected_files = [
            "./archive/EPOCH5/unity_seal.txt",
            "./archive/EPOCH5/ledger.log",
            "./archive/EPOCH5/manifests/E5-P1_manifest.txt",
            "./archive/EPOCH5/manifests/E5-P2_manifest.txt",
            "./archive/EPOCH5/manifests/E5-P3_manifest.txt"
        ]
        
        for file_path in expected_files:
            if not os.path.exists(file_path):
                raise Exception(f"Expected output file not created: {file_path}")
    
    def test_error_handling(self):
        """Test error handling in restricted directory"""
        # This test is more conceptual since we can't easily test permission errors
        # in a temporary directory. We'll test the validation logic instead.
        result = subprocess.run([sys.executable, "integration.py", "agents", "create", "x"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            raise Exception("Single character skill should have failed validation")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting EPOCH5 Template Tests")
        print("=" * 50)
        
        try:
            self.setup_test_environment()
            
            # Core functionality tests
            self.run_test("Python Module Compilation", self.test_python_compilation)
            self.run_test("Shell Script Syntax", self.test_shell_script_syntax)
            self.run_test("Integration Help", self.test_integration_help)
            self.run_test("Demo Environment Setup", self.test_integration_demo_setup)
            self.run_test("System Status", self.test_integration_status)
            self.run_test("Agent Creation Validation", self.test_agent_creation_validation)
            self.run_test("EPOCH5 Script Execution", self.test_epoch5_script_execution)
            self.run_test("Error Handling", self.test_error_handling)
            
        finally:
            self.cleanup_test_environment()
        
        # Report results
        print("=" * 50)
        print(f"📊 Test Results: {self.passed} passed, {self.failed} failed")
        
        if self.failed > 0:
            print("❌ Some tests failed!")
            return 1
        else:
            print("✅ All tests passed!")
            return 0

if __name__ == "__main__":
    tests = EPOCH5Tests()
    exit_code = tests.run_all_tests()
    sys.exit(exit_code)