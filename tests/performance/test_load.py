#!/usr/bin/env python3
"""
Performance and load testing for EPOCH5 system
"""

import time
import concurrent.futures
import statistics
from pathlib import Path
import pytest
import sys
import os
import threading

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integration import EPOCH5Integration
from agent_management import AgentManager
from dag_management import DAGManager

class TestPerformance:
    """Performance and load tests for EPOCH5 system"""
    
    def test_agent_registration_performance(self, temp_workspace):
        """Test agent registration performance under load"""
        agent_manager = AgentManager(str(temp_workspace))
        
        # Measure single agent registration
        start_time = time.time()
        agent = agent_manager.register_agent(["performance_test"])
        single_time = time.time() - start_time
        
        # Measure batch agent registration
        num_agents = 100
        start_time = time.time()
        
        agents = []
        for i in range(num_agents):
            agent = agent_manager.register_agent([f"skill_{i}"])
            agents.append(agent)
        
        batch_time = time.time() - start_time
        avg_time_per_agent = batch_time / num_agents
        
        # Performance assertions
        assert single_time < 1.0  # Single registration should be fast
        assert avg_time_per_agent < 0.1  # Average should be under 100ms
        assert len(agents) == num_agents
        
        print(f"Single agent registration: {single_time:.3f}s")
        print(f"Batch registration ({num_agents} agents): {batch_time:.3f}s") 
        print(f"Average per agent: {avg_time_per_agent:.3f}s")
    
    def test_concurrent_heartbeat_performance(self, temp_workspace):
        """Test concurrent heartbeat logging performance"""
        agent_manager = AgentManager(str(temp_workspace))
        
        # Register agents for testing
        num_agents = 50
        agents = []
        for i in range(num_agents):
            agent = agent_manager.register_agent([f"heartbeat_skill_{i}"])
            agents.append(agent)
        
        def log_heartbeats(agent_batch):
            """Log heartbeats for a batch of agents"""
            times = []
            for agent in agent_batch:
                start = time.time()
                agent_manager.log_heartbeat(agent["did"])
                times.append(time.time() - start)
            return times
        
        # Test concurrent heartbeat logging
        start_time = time.time()
        
        # Split agents into batches for concurrent processing
        batch_size = 10
        batches = [agents[i:i+batch_size] for i in range(0, len(agents), batch_size)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(log_heartbeats, batch) for batch in batches]
            all_times = []
            for future in concurrent.futures.as_completed(futures):
                all_times.extend(future.result())
        
        total_time = time.time() - start_time
        
        # Performance analysis
        avg_heartbeat_time = statistics.mean(all_times)
        max_heartbeat_time = max(all_times)
        
        # Assertions
        assert total_time < 5.0  # Should complete within 5 seconds
        assert avg_heartbeat_time < 0.05  # Average heartbeat under 50ms
        assert max_heartbeat_time < 0.2  # Max heartbeat under 200ms
        
        print(f"Concurrent heartbeats ({num_agents} agents): {total_time:.3f}s")
        print(f"Average heartbeat time: {avg_heartbeat_time:.3f}s")
        print(f"Max heartbeat time: {max_heartbeat_time:.3f}s")
    
    def test_dag_execution_scalability(self, temp_workspace):
        """Test DAG execution scalability with increasing task counts"""
        dag_manager = DAGManager(str(temp_workspace))
        
        # Test different DAG sizes
        task_counts = [5, 10, 25, 50]
        execution_times = []
        
        for num_tasks in task_counts:
            # Create linear DAG (each task depends on previous)
            tasks = [{"task_id": f"task_0", "dependencies": []}]
            for i in range(1, num_tasks):
                tasks.append({
                    "task_id": f"task_{i}",
                    "dependencies": [f"task_{i-1}"]
                })
            
            dag_id = f"scalability_test_{num_tasks}"
            dag_manager.create_dag(dag_id, tasks)
            
            # Measure execution time
            start_time = time.time()
            result = dag_manager.execute_dag(dag_id, simulation=True)
            execution_time = time.time() - start_time
            
            execution_times.append(execution_time)
            
            # Verify successful completion
            assert result["final_status"] == "completed"
            assert len(result["completed_tasks"]) == num_tasks
            
            print(f"DAG with {num_tasks} tasks: {execution_time:.3f}s")
        
        # Performance should scale reasonably
        for i, time_taken in enumerate(execution_times):
            assert time_taken < (task_counts[i] * 0.1)  # Linear scaling assumption
    
    def test_memory_usage_under_load(self, temp_workspace):
        """Test memory usage stability under sustained load"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        agent_manager = AgentManager(str(temp_workspace))
        dag_manager = DAGManager(str(temp_workspace))
        
        # Sustained operations
        for iteration in range(10):
            # Register agents
            agents = []
            for i in range(20):
                agent = agent_manager.register_agent([f"memory_test_{iteration}_{i}"])
                agents.append(agent)
            
            # Create and execute DAGs
            for i in range(5):
                tasks = [
                    {"task_id": f"mem_task_{iteration}_{i}_1", "dependencies": []},
                    {"task_id": f"mem_task_{iteration}_{i}_2", "dependencies": [f"mem_task_{iteration}_{i}_1"]}
                ]
                dag_id = f"memory_test_dag_{iteration}_{i}"
                dag_manager.create_dag(dag_id, tasks)
                dag_manager.execute_dag(dag_id, simulation=True)
            
            # Log heartbeats
            for agent in agents:
                agent_manager.log_heartbeat(agent["did"])
            
            # Force garbage collection
            gc.collect()
            
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory
            
            print(f"Iteration {iteration}: Memory usage {current_memory:.1f} MB (+{memory_increase:.1f} MB)")
            
            # Memory should not grow excessively
            assert memory_increase < 100  # Less than 100MB increase
    
    def test_file_io_performance(self, temp_workspace):
        """Test file I/O performance for ledgers and registries"""
        agent_manager = AgentManager(str(temp_workspace))
        
        # Measure registry write performance
        write_times = []
        for i in range(100):
            start_time = time.time()
            agent_manager.register_agent([f"io_test_{i}"])
            write_times.append(time.time() - start_time)
        
        # Measure registry read performance
        read_times = []
        for i in range(100):
            start_time = time.time()
            agent_manager.load_registry()
            read_times.append(time.time() - start_time)
        
        avg_write_time = statistics.mean(write_times)
        avg_read_time = statistics.mean(read_times)
        
        # Performance assertions
        assert avg_write_time < 0.1  # Average write under 100ms
        assert avg_read_time < 0.05  # Average read under 50ms
        
        print(f"Average registry write time: {avg_write_time:.4f}s")
        print(f"Average registry read time: {avg_read_time:.4f}s")
    
    def test_system_latency_under_load(self, temp_workspace):
        """Test system response latency under varying load conditions"""
        integration = EPOCH5Integration(str(temp_workspace))
        integration.setup_demo_environment()
        
        # Baseline latency measurement
        start_time = time.time()
        status = integration.get_system_status()
        baseline_latency = time.time() - start_time
        
        # Load system with background operations
        def background_load():
            """Generate background load"""
            for i in range(50):
                agent = integration.agent_manager.register_agent([f"load_agent_{i}"])
                integration.agent_manager.log_heartbeat(agent["did"])
        
        # Start background load
        load_thread = threading.Thread(target=background_load)
        load_thread.start()
        
        # Measure latency under load
        latency_samples = []
        for i in range(10):
            start_time = time.time()
            status = integration.get_system_status()
            latency = time.time() - start_time
            latency_samples.append(latency)
            time.sleep(0.1)  # Small delay between samples
        
        load_thread.join()
        
        avg_latency_under_load = statistics.mean(latency_samples)
        max_latency = max(latency_samples)
        
        # Performance assertions
        assert avg_latency_under_load < baseline_latency * 5  # Should not be more than 5x slower
        assert max_latency < 1.0  # Max latency should be under 1 second
        
        print(f"Baseline latency: {baseline_latency:.3f}s")
        print(f"Average latency under load: {avg_latency_under_load:.3f}s")
        print(f"Maximum latency: {max_latency:.3f}s")
    
    def test_throughput_measurement(self, temp_workspace):
        """Test system throughput for various operations"""
        agent_manager = AgentManager(str(temp_workspace))
        dag_manager = DAGManager(str(temp_workspace))
        
        # Agent registration throughput
        start_time = time.time()
        num_operations = 200
        
        for i in range(num_operations):
            agent_manager.register_agent([f"throughput_test_{i}"])
        
        duration = time.time() - start_time
        agent_throughput = num_operations / duration
        
        # DAG creation throughput
        start_time = time.time()
        num_dags = 50
        
        for i in range(num_dags):
            tasks = [{"task_id": f"throughput_task_{i}", "dependencies": []}]
            dag_manager.create_dag(f"throughput_dag_{i}", tasks)
        
        duration = time.time() - start_time
        dag_throughput = num_dags / duration
        
        # Throughput assertions
        assert agent_throughput > 50  # At least 50 agent registrations per second
        assert dag_throughput > 10   # At least 10 DAG creations per second
        
        print(f"Agent registration throughput: {agent_throughput:.1f} ops/sec")
        print(f"DAG creation throughput: {dag_throughput:.1f} ops/sec")