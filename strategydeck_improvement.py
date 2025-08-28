"""
Continuous Improvement System for StrategyDECK
Enables autonomous learning, optimization, and self-improvement
"""

import os
import json
import time
import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import threading
import random
from collections import defaultdict


class ContinuousImprovementSystem:
    """
    Autonomous system for continuous improvement of the StrategyDECK agent.
    
    Features:
    - Performance tracking and analysis
    - Strategy pattern optimization
    - Automated learning from execution history
    - Self-tuning of parameters
    - Periodic improvement cycles
    """
    
    def __init__(self, 
                base_dir: str = "./archive/EPOCH5",
                config_path: Optional[str] = None,
                log_level: int = logging.INFO):
        """
        Initialize the continuous improvement system.
        
        Args:
            base_dir: Base directory for data storage
            config_path: Path to configuration file (optional)
            log_level: Logging level
        """
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "improvement_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance history storage
        self.execution_history_file = self.data_dir / "execution_history.json"
        self.optimization_history_file = self.data_dir / "optimization_history.json"
        self.learned_patterns_file = self.data_dir / "learned_patterns.json"
        
        # Initialize logger
        self.logger = logging.getLogger("ContinuousImprovement")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # Add file handler
            log_file = self.data_dir / f"improvement_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Learning parameters
        self.learning_rate = self.config.get("learning_rate", 0.05)
        self.exploration_rate = self.config.get("exploration_rate", 0.2)
        self.improvement_cycle_hours = self.config.get("improvement_cycle_hours", 24)
        self.min_samples_for_learning = self.config.get("min_samples_for_learning", 10)
        
        # Performance metrics
        self.performance_metrics = defaultdict(list)
        self.strategy_patterns = {}
        self.parameter_recommendations = {}
        
        # Load historical data
        self._load_historical_data()
        
        self.logger.info(f"Continuous Improvement System initialized with learning rate {self.learning_rate}")
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "learning_rate": 0.05,
            "exploration_rate": 0.2,
            "improvement_cycle_hours": 24,
            "min_samples_for_learning": 10,
            "metrics_to_track": ["execution_time", "success_rate", "resource_usage"],
            "optimization_goals": {
                "execution_time": "minimize",
                "success_rate": "maximize",
                "resource_usage": "minimize"
            },
            "parameter_ranges": {
                "timeout": {"min": 5.0, "max": 120.0, "step": 5.0},
                "retries": {"min": 0, "max": 5, "step": 1},
                "max_workers": {"min": 1, "max": 8, "step": 1}
            },
            "auto_apply_improvements": True
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    merged_config = {**default_config, **loaded_config}
                    self.logger.info(f"Configuration loaded from {config_path}")
                    return merged_config
            except Exception as e:
                self.logger.error(f"Error loading configuration: {str(e)}")
                
        self.logger.info("Using default configuration")
        return default_config
    
    def _load_historical_data(self) -> None:
        """Load historical execution and optimization data"""
        # Load execution history
        if self.execution_history_file.exists():
            try:
                with open(self.execution_history_file, 'r') as f:
                    history = json.load(f)
                    self.logger.info(f"Loaded {len(history['executions'])} historical executions")
                    
                    # Process historical data for initial learning
                    for execution in history.get('executions', []):
                        strategy_type = execution.get('strategy_type', 'default')
                        for metric, value in execution.get('metrics', {}).items():
                            self.performance_metrics[f"{strategy_type}_{metric}"].append(value)
            except Exception as e:
                self.logger.error(f"Error loading execution history: {str(e)}")
        
        # Load learned patterns
        if self.learned_patterns_file.exists():
            try:
                with open(self.learned_patterns_file, 'r') as f:
                    patterns = json.load(f)
                    self.strategy_patterns = patterns.get('patterns', {})
                    self.parameter_recommendations = patterns.get('recommendations', {})
                    self.logger.info(f"Loaded {len(self.strategy_patterns)} learned patterns")
            except Exception as e:
                self.logger.error(f"Error loading learned patterns: {str(e)}")
    
    def record_execution(self, 
                        strategy_data: Dict[str, Any], 
                        result: Dict[str, Any]) -> None:
        """
        Record execution results for learning and improvement.
        
        Args:
            strategy_data: The input strategy data
            result: The execution result with metrics
        """
        strategy_type = strategy_data.get('goal', '').split()[0].lower()
        if not strategy_type:
            strategy_type = 'default'
            
        # Extract key metrics
        metrics = {
            "execution_time": result.get('execution_time', 0.0),
            "success": result.get('status') == 'success',
            "timestamp": datetime.now().isoformat()
        }
        
        # Add resource usage if available
        if 'resources' in strategy_data:
            metrics["resource_usage"] = sum(
                float(amount) for amount in strategy_data['resources'].values()
            )
        
        # Add constraints count if available
        if 'constraints' in strategy_data:
            metrics["constraints_count"] = len(strategy_data['constraints'])
            
        # Add priority weight
        priority_weights = {'high': 3, 'medium': 2, 'low': 1}
        metrics["priority_weight"] = priority_weights.get(
            strategy_data.get('priority', 'medium').lower(), 2
        )
        
        # Update performance metrics
        for metric, value in metrics.items():
            if metric != 'timestamp':  # Don't store timestamp in performance metrics
                self.performance_metrics[f"{strategy_type}_{metric}"].append(value)
        
        # Store execution record
        execution_record = {
            "strategy_type": strategy_type,
            "strategy_data": strategy_data,
            "metrics": metrics,
            "steps_completed": result.get('steps_completed', []),
            "result_status": result.get('status', 'unknown')
        }
        
        # Save to history file
        self._append_to_history(execution_record)
        self.logger.debug(f"Recorded execution of {strategy_type} strategy")
        
        # Trigger learning if we have enough samples
        metric_key = f"{strategy_type}_execution_time"
        if len(self.performance_metrics.get(metric_key, [])) >= self.min_samples_for_learning:
            self._learn_from_execution(strategy_type)
    
    def _append_to_history(self, execution_record: Dict[str, Any]) -> None:
        """Append execution record to history file"""
        history = {"executions": []}
        
        if self.execution_history_file.exists():
            try:
                with open(self.execution_history_file, 'r') as f:
                    history = json.load(f)
            except Exception as e:
                self.logger.error(f"Error reading history file: {str(e)}")
        
        history["executions"].append(execution_record)
        history["last_updated"] = datetime.now().isoformat()
        
        # Keep history size manageable (limit to last 1000 executions)
        if len(history["executions"]) > 1000:
            history["executions"] = history["executions"][-1000:]
        
        try:
            with open(self.execution_history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error writing to history file: {str(e)}")
    
    def _learn_from_execution(self, strategy_type: str) -> None:
        """
        Learn patterns and optimal parameters from execution history.
        
        Args:
            strategy_type: Type of strategy to learn from
        """
        self.logger.info(f"Learning from execution history for {strategy_type} strategies")
        
        # Get relevant metrics
        execution_times = self.performance_metrics.get(f"{strategy_type}_execution_time", [])
        success_rates = self.performance_metrics.get(f"{strategy_type}_success", [])
        
        if len(execution_times) < self.min_samples_for_learning:
            self.logger.debug(f"Not enough samples to learn from for {strategy_type}")
            return
        
        # Calculate key statistics
        avg_execution_time = sum(execution_times) / len(execution_times)
        success_rate = sum(1 for s in success_rates if s) / len(success_rates) if success_rates else 0
        
        # Identify patterns from historical data
        pattern = {
            "avg_execution_time": avg_execution_time,
            "success_rate": success_rate,
            "sample_size": len(execution_times),
            "optimal_parameters": self._determine_optimal_parameters(strategy_type)
        }
        
        # Store learned pattern
        self.strategy_patterns[strategy_type] = pattern
        
        # Update learned patterns file
        self._save_learned_patterns()
        
        self.logger.info(f"Updated learned patterns for {strategy_type}: " +
                        f"success rate={success_rate:.2f}, avg time={avg_execution_time:.2f}s")
    
    def _determine_optimal_parameters(self, strategy_type: str) -> Dict[str, Any]:
        """
        Determine optimal parameters for a strategy type based on historical performance.
        
        Args:
            strategy_type: The type of strategy
            
        Returns:
            Dictionary of recommended parameter values
        """
        # Get history data
        history = {"executions": []}
        if self.execution_history_file.exists():
            try:
                with open(self.execution_history_file, 'r') as f:
                    history = json.load(f)
            except Exception:
                pass
        
        # Filter relevant executions
        relevant_executions = [
            exe for exe in history.get("executions", []) 
            if exe.get("strategy_type") == strategy_type and 
               exe.get("result_status") == "success"
        ]
        
        if not relevant_executions:
            return {}
        
        # Extract parameter combinations and their performance
        param_performance = []
        for exe in relevant_executions:
            strategy_data = exe.get("strategy_data", {})
            metrics = exe.get("metrics", {})
            
            # Calculate a performance score (lower is better)
            # Weight execution time and inverse success rate
            score = metrics.get("execution_time", 999.0)
            if metrics.get("success", False) is False:
                score *= 2  # Penalize failures
                
            # Extract key parameters
            params = {
                "priority": strategy_data.get("priority", "medium"),
                "constraints_count": len(strategy_data.get("constraints", [])),
                "has_resources": "resources" in strategy_data,
            }
            
            param_performance.append((params, score))
        
        # Find the best performing parameter combinations
        param_performance.sort(key=lambda x: x[1])  # Sort by score (lower is better)
        best_params = param_performance[0][0] if param_performance else {}
        
        # Add recommendations
        recommendations = {
            "recommended_priority": best_params.get("priority", "medium"),
            "optimal_constraints_count": best_params.get("constraints_count", 0),
            "should_include_resources": best_params.get("has_resources", False),
            "confidence": min(1.0, len(relevant_executions) / 20.0)  # Confidence based on sample size
        }
        
        # Store in recommendations
        self.parameter_recommendations[strategy_type] = recommendations
        
        return recommendations
    
    def _save_learned_patterns(self) -> None:
        """Save learned patterns to file"""
        patterns_data = {
            "patterns": self.strategy_patterns,
            "recommendations": self.parameter_recommendations,
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open(self.learned_patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving learned patterns: {str(e)}")
    
    def get_strategy_recommendations(self, 
                                   goal: str,
                                   existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get recommendations for optimizing a strategy based on learned patterns.
        
        Args:
            goal: The strategy goal
            existing_data: Existing strategy data to enhance (optional)
            
        Returns:
            Enhanced strategy data with recommendations
        """
        strategy_type = goal.split()[0].lower()
        
        # Start with existing data or empty dict
        strategy_data = existing_data.copy() if existing_data else {}
        strategy_data["goal"] = goal
        
        # Apply recommendations if we have learned patterns
        if strategy_type in self.parameter_recommendations:
            recommendations = self.parameter_recommendations[strategy_type]
            confidence = recommendations.get("confidence", 0.0)
            
            # Only apply if we have reasonable confidence
            if confidence > 0.5:
                # Apply recommendations with some exploration
                if "priority" not in strategy_data and random.random() > self.exploration_rate:
                    strategy_data["priority"] = recommendations.get("recommended_priority", "medium")
                
                # Suggest constraints if not already provided
                if "constraints" not in strategy_data:
                    optimal_count = recommendations.get("optimal_constraints_count", 0)
                    if optimal_count > 0:
                        # Just a placeholder - in a real system, you'd have domain-specific constraints
                        strategy_data["constraints"] = [
                            f"auto_constraint_{i+1}" for i in range(optimal_count)
                        ]
                
                # Add resources if beneficial
                if "resources" not in strategy_data and recommendations.get("should_include_resources", False):
                    # Placeholder resources - in a real system, these would be meaningful
                    strategy_data["resources"] = {"compute": 10, "memory": 4}
            
            self.logger.info(f"Applied strategy recommendations for {strategy_type} with {confidence:.2f} confidence")
        
        return strategy_data
    
    def get_execution_parameters(self, 
                               strategy_type: str) -> Dict[str, Any]:
        """
        Get recommended execution parameters (timeout, retries, etc.)
        
        Args:
            strategy_type: Type of strategy
            
        Returns:
            Dictionary of execution parameters
        """
        # Default parameters
        params = {
            "timeout": 30.0,
            "retries": 2,
            "retry_delay": 1.0
        }
        
        # Apply learned parameters if available
        if strategy_type in self.strategy_patterns:
            pattern = self.strategy_patterns[strategy_type]
            avg_time = pattern.get("avg_execution_time", 10.0)
            success_rate = pattern.get("success_rate", 0.9)
            
            # Adjust timeout based on historical execution time
            # Add buffer of 50% above average
            params["timeout"] = avg_time * 1.5
            
            # Adjust retries based on success rate
            # Lower success rate means more retries
            if success_rate < 0.7:
                params["retries"] = 3
            elif success_rate < 0.9:
                params["retries"] = 2
            else:
                params["retries"] = 1
                
            # Add small random variation for exploration
            if random.random() < self.exploration_rate:
                params["timeout"] += random.uniform(-5.0, 10.0)
                params["timeout"] = max(5.0, params["timeout"])  # Ensure minimum timeout
                params["retries"] += random.choice([-1, 0, 1])
                params["retries"] = max(0, params["retries"])  # Ensure non-negative
        
        return params
    
    def start_improvement_cycle(self) -> None:
        """
        Start the continuous improvement cycle in a background thread.
        This periodically analyzes performance and updates recommendations.
        """
        def improvement_thread():
            self.logger.info(f"Starting continuous improvement cycle (every {self.improvement_cycle_hours} hours)")
            
            while True:
                try:
                    # Sleep until next cycle
                    time.sleep(self.improvement_cycle_hours * 3600)
                    
                    # Run improvement cycle
                    self.run_improvement_cycle()
                    
                except Exception as e:
                    self.logger.error(f"Error in improvement cycle: {str(e)}")
        
        # Start the improvement thread as a daemon
        thread = threading.Thread(target=improvement_thread, daemon=True)
        thread.start()
        self.logger.info("Improvement cycle thread started")
    
    def run_improvement_cycle(self) -> Dict[str, Any]:
        """
        Run a complete improvement cycle to optimize system performance.
        
        Returns:
            Dictionary with improvement results
        """
        self.logger.info("Running improvement cycle")
        start_time = time.time()
        
        # 1. Analyze historical performance
        strategy_types = set()
        for key in self.performance_metrics.keys():
            parts = key.split('_')
            if len(parts) > 1:
                strategy_types.add(parts[0])
        
        # 2. Learn from each strategy type
        for strategy_type in strategy_types:
            self._learn_from_execution(strategy_type)
        
        # 3. Identify global optimization opportunities
        optimization_results = self._identify_optimization_opportunities()
        
        # 4. Update configurations if auto-apply is enabled
        if self.config.get("auto_apply_improvements", True):
            self._apply_optimizations(optimization_results)
        
        duration = time.time() - start_time
        self.logger.info(f"Improvement cycle completed in {duration:.2f}s")
        
        # Record the improvement cycle
        cycle_record = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "strategies_analyzed": len(strategy_types),
            "optimizations": optimization_results,
        }
        
        # Save to optimization history
        self._append_to_optimization_history(cycle_record)
        
        return cycle_record
    
    def _identify_optimization_opportunities(self) -> Dict[str, Any]:
        """
        Identify opportunities for global optimization.
        
        Returns:
            Dictionary of optimization opportunities
        """
        optimizations = {
            "parameter_adjustments": {},
            "workflow_improvements": [],
            "resource_allocation": {}
        }
        
        # Analyze execution times across strategy types
        execution_times = {}
        for key, values in self.performance_metrics.items():
            if key.endswith('_execution_time'):
                strategy_type = key.split('_')[0]
                execution_times[strategy_type] = sum(values) / len(values) if values else 0
        
        # Identify slowest strategy types
        if execution_times:
            sorted_times = sorted(execution_times.items(), key=lambda x: x[1], reverse=True)
            slowest_strategies = sorted_times[:3]
            
            optimizations["workflow_improvements"].append({
                "type": "execution_time_optimization",
                "targets": slowest_strategies,
                "recommendation": "Optimize execution parameters for these slower strategy types"
            })
        
        # Analyze success rates
        success_rates = {}
        for key, values in self.performance_metrics.items():
            if key.endswith('_success'):
                strategy_type = key.split('_')[0]
                success_rates[strategy_type] = sum(values) / len(values) if values else 0
        
        # Identify least successful strategy types
        if success_rates:
            sorted_rates = sorted(success_rates.items(), key=lambda x: x[1])
            least_successful = sorted_rates[:3]
            
            optimizations["workflow_improvements"].append({
                "type": "reliability_optimization",
                "targets": least_successful,
                "recommendation": "Increase retry counts for these less reliable strategy types"
            })
        
        # Calculate optimal global parameters
        global_retry_adjustment = 0
        global_timeout_adjustment = 0.0
        
        # If overall success rate is low, increase retries
        avg_success = sum(success_rates.values()) / len(success_rates) if success_rates else 0.9
        if avg_success < 0.8:
            global_retry_adjustment = 1
        
        # If overall execution times are high, increase timeouts
        avg_execution_time = sum(execution_times.values()) / len(execution_times) if execution_times else 10.0
        if avg_execution_time > 20.0:
            global_timeout_adjustment = avg_execution_time * 0.2  # 20% increase
        
        optimizations["parameter_adjustments"] = {
            "global_retry_adjustment": global_retry_adjustment,
            "global_timeout_adjustment": global_timeout_adjustment
        }
        
        return optimizations
    
    def _apply_optimizations(self, optimizations: Dict[str, Any]) -> None:
        """
        Apply optimizations to the system configuration.
        
        Args:
            optimizations: Optimization opportunities to apply
        """
        # In a real system, this would update config files or databases
        # Here we'll just log what would be applied
        adjustments = optimizations.get("parameter_adjustments", {})
        
        if adjustments.get("global_retry_adjustment", 0) != 0:
            self.logger.info(f"Would apply global retry adjustment: {adjustments['global_retry_adjustment']}")
        
        if adjustments.get("global_timeout_adjustment", 0.0) != 0.0:
            self.logger.info(f"Would apply global timeout adjustment: {adjustments['global_timeout_adjustment']:.2f}s")
        
        # Log workflow improvements
        for improvement in optimizations.get("workflow_improvements", []):
            self.logger.info(f"Workflow improvement: {improvement['type']}")
            for target, value in improvement.get("targets", []):
                self.logger.info(f"  Target: {target} ({value:.2f})")
            self.logger.info(f"  Recommendation: {improvement['recommendation']}")
    
    def _append_to_optimization_history(self, cycle_record: Dict[str, Any]) -> None:
        """Append optimization cycle record to history file"""
        history = {"cycles": []}
        
        if self.optimization_history_file.exists():
            try:
                with open(self.optimization_history_file, 'r') as f:
                    history = json.load(f)
            except Exception as e:
                self.logger.error(f"Error reading optimization history: {str(e)}")
        
        history["cycles"].append(cycle_record)
        history["last_updated"] = datetime.now().isoformat()
        
        # Keep history manageable
        if len(history["cycles"]) > 100:
            history["cycles"] = history["cycles"][-100:]
        
        try:
            with open(self.optimization_history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error writing optimization history: {str(e)}")
    
    def get_improvement_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the improvement system's performance.
        
        Returns:
            Dictionary with improvement system statistics
        """
        stats = {
            "learning_rate": self.learning_rate,
            "exploration_rate": self.exploration_rate,
            "tracked_strategy_types": [],
            "learned_patterns_count": len(self.strategy_patterns),
            "recommendations_count": len(self.parameter_recommendations),
            "metrics_tracked": {}
        }
        
        # Get strategy types
        strategy_types = set()
        for key in self.performance_metrics.keys():
            parts = key.split('_')
            if len(parts) > 1:
                strategy_types.add(parts[0])
        
        stats["tracked_strategy_types"] = list(strategy_types)
        
        # Get metric counts
        for key, values in self.performance_metrics.items():
            stats["metrics_tracked"][key] = len(values)
        
        # Get improvement cycle stats
        if self.optimization_history_file.exists():
            try:
                with open(self.optimization_history_file, 'r') as f:
                    history = json.load(f)
                    stats["improvement_cycles_run"] = len(history.get("cycles", []))
                    if history.get("cycles"):
                        stats["last_improvement_cycle"] = history["cycles"][-1]["timestamp"]
            except Exception:
                stats["improvement_cycles_run"] = 0
        else:
            stats["improvement_cycles_run"] = 0
        
        return stats


# Example usage when run directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="StrategyDECK Continuous Improvement System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    subparsers.add_parser("status", help="Show improvement system status")
    
    # Run cycle command
    subparsers.add_parser("run-cycle", help="Run an improvement cycle")
    
    # Get recommendations command
    recommend_parser = subparsers.add_parser("recommend", help="Get strategy recommendations")
    recommend_parser.add_argument("--goal", required=True, help="Strategy goal")
    
    args = parser.parse_args()
    
    # Create improvement system
    cis = ContinuousImprovementSystem()
    
    if args.command == "status":
        stats = cis.get_improvement_stats()
        print(json.dumps(stats, indent=2))
        
    elif args.command == "run-cycle":
        results = cis.run_improvement_cycle()
        print(json.dumps(results, indent=2))
        
    elif args.command == "recommend":
        recommendations = cis.get_strategy_recommendations(args.goal)
        print(json.dumps(recommendations, indent=2))
        
    else:
        # Demo mode - simulate some executions and learning
        print("Running demo mode with simulated executions")
        
        # Simulate recording some executions
        for i in range(20):
            strategy_type = random.choice(["optimize", "analyze", "transform"])
            goal = f"{strategy_type} workflow"
            priority = random.choice(["high", "medium", "low"])
            
            constraints = []
            if random.random() > 0.5:
                num_constraints = random.randint(1, 5)
                constraints = [f"constraint_{j}" for j in range(num_constraints)]
            
            resources = {}
            if random.random() > 0.6:
                resources = {"compute": random.randint(5, 20), "memory": random.randint(2, 8)}
            
            strategy_data = {
                "goal": goal,
                "priority": priority
            }
            
            if constraints:
                strategy_data["constraints"] = constraints
            
            if resources:
                strategy_data["resources"] = resources
            
            # Simulate execution result
            success = random.random() > 0.2  # 80% success rate
            execution_time = random.uniform(1.0, 30.0)
            
            result = {
                "status": "success" if success else "error",
                "execution_time": execution_time,
                "steps_completed": [f"step_{j}" for j in range(random.randint(2, 8))] if success else []
            }
            
            # Record the execution
            cis.record_execution(strategy_data, result)
            
            print(f"Recorded {strategy_type} execution: {'✓' if success else '✗'} in {execution_time:.2f}s")
        
        # Run an improvement cycle
        print("\nRunning improvement cycle...")
        cycle_results = cis.run_improvement_cycle()
        
        # Get recommendations
        print("\nGetting recommendations for 'optimize resources'...")
        recommendations = cis.get_strategy_recommendations("optimize resources")
        
        print("\nGetting execution parameters for 'optimize'...")
        params = cis.get_execution_parameters("optimize")
        
        print("\nImprovement system status:")
        stats = cis.get_improvement_stats()
        print(json.dumps(stats, indent=2))
