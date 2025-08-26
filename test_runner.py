#!/usr/bin/env python3
"""
Comprehensive test runner for EPOCH5 Template
Provides orchestrated testing including unit, integration, performance, and end-to-end tests
"""

import os
import sys
import time
import subprocess
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any
import concurrent.futures

class TestRunner:
    """Orchestrates comprehensive testing of EPOCH5 system"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.getcwd())
        self.test_results = {}
        self.start_time = time.time()
        
    def run_command(self, command: List[str], timeout: int = 300, env: Dict[str, str] = None) -> Dict[str, Any]:
        """Run a command and capture results"""
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
            
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=full_env,
                cwd=self.base_dir
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(command)
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "command": " ".join(command)
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(command)
            }
    
    def check_dependencies(self) -> bool:
        """Check if all test dependencies are available"""
        print("🔍 Checking test dependencies...")
        
        dependencies = [
            (["python3", "--version"], "Python 3"),
            (["pytest", "--version"], "pytest"),
            (["black", "--version"], "black"),
            (["flake8", "--version"], "flake8"),
        ]
        
        missing_deps = []
        for cmd, name in dependencies:
            result = self.run_command(cmd, timeout=10)
            if not result["success"]:
                missing_deps.append(name)
                print(f"❌ {name} not available")
            else:
                print(f"✅ {name} available")
        
        if missing_deps:
            print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
            print("Please install missing dependencies and try again.")
            return False
        
        return True
    
    def install_test_dependencies(self) -> bool:
        """Install test dependencies"""
        print("📦 Installing test dependencies...")
        
        result = self.run_command([
            "python3", "-m", "pip", "install", 
            "-r", "requirements-test.txt"
        ], timeout=120)
        
        if result["success"]:
            print("✅ Test dependencies installed successfully")
            return True
        else:
            print("❌ Failed to install test dependencies")
            print(result["stderr"])
            return False
    
    def run_linting(self) -> Dict[str, Any]:
        """Run code linting checks"""
        print("🔍 Running linting checks...")
        
        linting_results = {
            "started_at": time.time(),
            "checks": {},
            "overall_success": True
        }
        
        # Black formatting check
        print("  Running black format check...")
        result = self.run_command(["black", "--check", "--diff", "."])
        linting_results["checks"]["black"] = result
        if not result["success"]:
            linting_results["overall_success"] = False
            print("    ❌ Black formatting issues found")
        else:
            print("    ✅ Black formatting OK")
        
        # Flake8 style check
        print("  Running flake8 style check...")
        result = self.run_command(["flake8", ".", "--max-line-length=100"])
        linting_results["checks"]["flake8"] = result
        if not result["success"]:
            linting_results["overall_success"] = False
            print("    ❌ Flake8 style issues found")
        else:
            print("    ✅ Flake8 style check OK")
        
        # ShellCheck for bash scripts
        print("  Running shellcheck on bash scripts...")
        bash_scripts = list(Path(".").glob("*.sh"))
        if bash_scripts:
            for script in bash_scripts:
                result = self.run_command(["shellcheck", str(script)])
                linting_results["checks"][f"shellcheck_{script.name}"] = result
                if not result["success"]:
                    linting_results["overall_success"] = False
                    print(f"    ❌ ShellCheck issues in {script.name}")
                else:
                    print(f"    ✅ ShellCheck OK for {script.name}")
        
        linting_results["completed_at"] = time.time()
        linting_results["duration"] = linting_results["completed_at"] - linting_results["started_at"]
        
        return linting_results
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests"""
        print("🧪 Running unit tests...")
        
        if not (self.base_dir / "tests" / "unit").exists():
            print("  ⚠️  No unit tests directory found")
            return {"success": True, "skipped": True}
        
        result = self.run_command([
            "pytest", "tests/unit/", "-v", "--tb=short",
            "--cov=.", "--cov-report=term-missing",
            "--cov-report=xml:coverage-unit.xml"
        ])
        
        if result["success"]:
            print("✅ Unit tests passed")
        else:
            print("❌ Unit tests failed")
            print(result["stderr"])
        
        return result
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests"""
        print("🔗 Running integration tests...")
        
        if not (self.base_dir / "tests" / "integration").exists():
            print("  ⚠️  No integration tests directory found")
            return {"success": True, "skipped": True}
        
        result = self.run_command([
            "pytest", "tests/integration/", "-v", "--tb=short",
            "--cov=.", "--cov-append", 
            "--cov-report=xml:coverage-integration.xml"
        ])
        
        if result["success"]:
            print("✅ Integration tests passed")
        else:
            print("❌ Integration tests failed")
            print(result["stderr"])
        
        return result
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        print("⚡ Running performance tests...")
        
        if not (self.base_dir / "tests" / "performance").exists():
            print("  ⚠️  No performance tests directory found")
            return {"success": True, "skipped": True}
        
        result = self.run_command([
            "pytest", "tests/performance/", "-v", "--tb=short",
            "--benchmark-only", "--benchmark-json=benchmark-results.json"
        ])
        
        if result["success"]:
            print("✅ Performance tests passed")
        else:
            print("❌ Performance tests failed")
            print(result["stderr"])
        
        return result
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests"""
        print("🔒 Running security tests...")
        
        security_results = {
            "started_at": time.time(),
            "checks": {},
            "overall_success": True
        }
        
        # Bandit security scan
        print("  Running bandit security scan...")
        result = self.run_command(["bandit", "-r", ".", "-f", "json", "-o", "bandit-results.json"])
        security_results["checks"]["bandit"] = result
        # Bandit may return non-zero for issues found, but that's expected
        print(f"    ✅ Bandit scan completed")
        
        # Safety check for known vulnerabilities
        print("  Running safety vulnerability check...")
        result = self.run_command(["safety", "check", "--json", "--output", "safety-results.json"])
        security_results["checks"]["safety"] = result
        if result["success"]:
            print("    ✅ No known vulnerabilities found")
        else:
            print("    ⚠️  Potential vulnerabilities detected")
            security_results["overall_success"] = False
        
        security_results["completed_at"] = time.time()
        security_results["duration"] = security_results["completed_at"] - security_results["started_at"]
        
        return security_results
    
    def run_end_to_end_tests(self) -> Dict[str, Any]:
        """Run end-to-end tests"""
        print("🎯 Running end-to-end tests...")
        
        e2e_results = {
            "started_at": time.time(),
            "tests": {},
            "overall_success": True
        }
        
        # Test main EPOCH5 script
        print("  Testing epoch5.sh script...")
        env = {
            "DELAY_HOURS_P1_P2": "0",
            "DELAY_HOURS_P2_P3": "0",
            "ARC_ID": "E2E-TEST"
        }
        
        # Make script executable
        self.run_command(["chmod", "+x", "epoch5.sh"])
        
        result = self.run_command(["./epoch5.sh"], timeout=60, env=env)
        e2e_results["tests"]["epoch5_script"] = result
        
        if result["success"]:
            print("    ✅ EPOCH5 script executed successfully")
            
            # Verify artifacts were created
            archive_dir = self.base_dir / "archive" / "EPOCH5"
            if archive_dir.exists():
                print("    ✅ Archive directory created")
                if (archive_dir / "ledger.txt").exists():
                    print("    ✅ Ledger file created")
                if (archive_dir / "unity_seal.txt").exists():
                    print("    ✅ Unity seal created")
                if (archive_dir / "manifests").exists():
                    manifest_count = len(list((archive_dir / "manifests").glob("*_manifest.txt")))
                    print(f"    ✅ {manifest_count} manifests created")
            else:
                print("    ❌ Archive directory not created")
                e2e_results["overall_success"] = False
                
        else:
            print("    ❌ EPOCH5 script failed")
            e2e_results["overall_success"] = False
        
        # Test Python integration
        print("  Testing Python integration...")
        result = self.run_command(["python3", "integration.py", "setup-demo"])
        e2e_results["tests"]["python_setup"] = result
        
        if result["success"]:
            print("    ✅ Python integration setup successful")
            
            # Test workflow execution
            result = self.run_command(["python3", "integration.py", "run-workflow"])
            e2e_results["tests"]["python_workflow"] = result
            
            if result["success"]:
                print("    ✅ Python workflow execution successful")
            else:
                print("    ❌ Python workflow execution failed")
                e2e_results["overall_success"] = False
        else:
            print("    ❌ Python integration setup failed")
            e2e_results["overall_success"] = False
        
        e2e_results["completed_at"] = time.time()
        e2e_results["duration"] = e2e_results["completed_at"] - e2e_results["started_at"]
        
        return e2e_results
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time
        
        report = {
            "timestamp": time.time(),
            "total_duration": total_duration,
            "results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "passed": sum(1 for result in self.test_results.values() 
                             if result.get("success", False) or result.get("overall_success", False)),
                "failed": sum(1 for result in self.test_results.values() 
                             if not (result.get("success", False) or result.get("overall_success", False))),
                "skipped": sum(1 for result in self.test_results.values() 
                              if result.get("skipped", False))
            }
        }
        
        report["summary"]["success_rate"] = (
            report["summary"]["passed"] / report["summary"]["total_tests"] * 100
            if report["summary"]["total_tests"] > 0 else 0
        )
        
        return report
    
    def run_all_tests(self, include_security: bool = True, include_performance: bool = True, 
                     include_e2e: bool = True) -> Dict[str, Any]:
        """Run all test suites"""
        print("🚀 Starting comprehensive test suite for EPOCH5 Template")
        print("=" * 60)
        
        # Check dependencies
        if not self.check_dependencies():
            # Try to install missing dependencies
            if not self.install_test_dependencies():
                return {"success": False, "error": "Failed to install dependencies"}
        
        # Run test suites
        test_suites = [
            ("linting", self.run_linting),
            ("unit_tests", self.run_unit_tests),
            ("integration_tests", self.run_integration_tests),
        ]
        
        if include_performance:
            test_suites.append(("performance_tests", self.run_performance_tests))
        
        if include_security:
            test_suites.append(("security_tests", self.run_security_tests))
        
        if include_e2e:
            test_suites.append(("end_to_end_tests", self.run_end_to_end_tests))
        
        # Execute test suites
        for suite_name, suite_func in test_suites:
            print(f"\n{'='*20} {suite_name.upper()} {'='*20}")
            start_time = time.time()
            result = suite_func()
            result["duration"] = time.time() - start_time
            self.test_results[suite_name] = result
        
        # Generate report
        print("\n" + "="*60)
        print("📊 GENERATING TEST REPORT")
        print("="*60)
        
        report = self.generate_test_report()
        
        # Save report
        report_file = self.base_dir / "test-report.json"
        with report_file.open("w") as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        summary = report["summary"]
        print(f"📈 Test Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Skipped: {summary['skipped']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Total Duration: {report['total_duration']:.2f}s")
        print(f"📄 Full report saved to: {report_file}")
        
        overall_success = summary["failed"] == 0
        if overall_success:
            print("\n🎉 All tests passed successfully!")
        else:
            print(f"\n❌ {summary['failed']} test suite(s) failed")
            
        return {
            "success": overall_success,
            "report": report,
            "report_file": str(report_file)
        }

def main():
    parser = argparse.ArgumentParser(description="EPOCH5 Comprehensive Test Runner")
    parser.add_argument("--no-security", action="store_true", help="Skip security tests")
    parser.add_argument("--no-performance", action="store_true", help="Skip performance tests")  
    parser.add_argument("--no-e2e", action="store_true", help="Skip end-to-end tests")
    parser.add_argument("--suite", choices=["linting", "unit", "integration", "performance", "security", "e2e"],
                       help="Run specific test suite only")
    parser.add_argument("--base-dir", help="Base directory for tests")
    
    args = parser.parse_args()
    
    runner = TestRunner(args.base_dir)
    
    if args.suite:
        # Run specific suite
        suite_map = {
            "linting": runner.run_linting,
            "unit": runner.run_unit_tests,
            "integration": runner.run_integration_tests,
            "performance": runner.run_performance_tests,
            "security": runner.run_security_tests,
            "e2e": runner.run_end_to_end_tests
        }
        
        if args.suite in suite_map:
            result = suite_map[args.suite]()
            success = result.get("success", False) or result.get("overall_success", False)
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown test suite: {args.suite}")
            sys.exit(1)
    else:
        # Run all tests
        result = runner.run_all_tests(
            include_security=not args.no_security,
            include_performance=not args.no_performance,
            include_e2e=not args.no_e2e
        )
        
        sys.exit(0 if result["success"] else 1)

if __name__ == "__main__":
    main()