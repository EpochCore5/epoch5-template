#!/usr/bin/env python3
"""
Basic performance benchmarking for EPOCH5 components
Demonstrates foundations for Priority 3 improvements
"""

import time
import sys
import os
import tempfile
import shutil
import subprocess
from pathlib import Path

def benchmark_function(func, name, runs=3):
    """Benchmark a function over multiple runs"""
    times = []
    for i in range(runs):
        start = time.time()
        try:
            func()
            end = time.time()
            times.append(end - start)
        except Exception as e:
            print(f"❌ {name} failed on run {i+1}: {e}")
            return None
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"⏱️  {name}: avg={avg_time:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s")
    return avg_time

def benchmark_integration_setup():
    """Benchmark integration demo setup"""
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        # Copy necessary files
        original_dir = os.getcwd()
        for file in ["integration.py", "agent_management.py", "policy_grants.py", 
                    "dag_management.py", "cycle_execution.py", "capsule_metadata.py", "meta_capsule.py"]:
            shutil.copy2(os.path.join(original_dir, file), temp_dir)
        
        subprocess.run([sys.executable, "integration.py", "setup-demo"], 
                      capture_output=True, check=True)

def benchmark_shell_script():
    """Benchmark epoch5.sh execution"""  
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        original_dir = "/home/runner/work/epoch5-template/epoch5-template"
        shutil.copy2(os.path.join(original_dir, "epoch5.sh"), temp_dir)
        os.chmod("epoch5.sh", 0o755)
        
        env = os.environ.copy()
        env["DELAY_HOURS_P1_P2"] = "0"
        env["DELAY_HOURS_P2_P3"] = "0"
        
        subprocess.run(["./epoch5.sh"], capture_output=True, check=True, env=env)

def benchmark_agent_operations():
    """Benchmark agent creation and operations"""
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        original_dir = "/home/runner/work/epoch5-template/epoch5-template"
        for file in ["integration.py", "agent_management.py", "policy_grants.py", 
                    "dag_management.py", "cycle_execution.py", "capsule_metadata.py", "meta_capsule.py"]:
            shutil.copy2(os.path.join(original_dir, file), temp_dir)
        
        # Setup first
        subprocess.run([sys.executable, "integration.py", "setup-demo"], 
                      capture_output=True, check=True)
        
        # Create 10 agents
        for i in range(10):
            subprocess.run([sys.executable, "integration.py", "agents", "create", 
                          f"skill{i}", f"capability{i}"], 
                          capture_output=True, check=True)

def main():
    """Run performance benchmarks"""
    print("🔬 EPOCH5 Performance Benchmarks")
    print("=" * 50)
    print("ℹ️  This demonstrates foundations for performance optimization")
    print()
    
    original_dir = os.getcwd()
    
    try:
        results = {}
        
        # Benchmark core operations
        results['Integration Setup'] = benchmark_function(benchmark_integration_setup, 
                                                        "Integration Demo Setup")
        results['Shell Script Execution'] = benchmark_function(benchmark_shell_script, 
                                                              "EPOCH5 Shell Script")  
        results['Agent Operations'] = benchmark_function(benchmark_agent_operations,
                                                        "Agent Creation (10 agents)")
        
        print()
        print("=" * 50)
        print("📊 Performance Summary")
        print("=" * 50)
        
        for operation, avg_time in results.items():
            if avg_time is not None:
                status = "✅ Good" if avg_time < 5.0 else "⚠️  Slow" if avg_time < 15.0 else "❌ Very Slow"
                print(f"{operation}: {avg_time:.3f}s - {status}")
        
        print()
        print("💡 Optimization Opportunities (Priority 3):")
        print("   • Parallel agent creation")
        print("   • Caching for repeated operations") 
        print("   • Database backend for large agent registries")
        print("   • Asynchronous I/O for file operations")
        
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    main()