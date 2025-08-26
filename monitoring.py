#!/usr/bin/env python3
"""
Monitoring and metrics collection system for EPOCH5
Provides structured logging, metrics tracking, and performance monitoring
"""

import json
import time
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
import psutil

@dataclass
class MetricPoint:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str]
    unit: str = ""

class MetricsCollector:
    """Collects and manages system metrics"""
    
    def __init__(self, base_dir: str = "./archive/EPOCH5"):
        self.base_dir = Path(base_dir)
        self.metrics_dir = self.base_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory metric storage for real-time access
        self.metrics_buffer = deque(maxlen=10000)  # Last 10k metrics
        self.metric_aggregates = defaultdict(list)
        
        # Performance counters
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.timers = defaultdict(list)
        
        # System monitoring
        self._monitoring_active = False
        self._monitor_thread = None
        
        # Setup structured logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup structured logging for metrics"""
        log_file = self.metrics_dir / "metrics.log"
        
        # Configure logger
        self.logger = logging.getLogger("epoch5.metrics")
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def timestamp(self) -> float:
        """Get current timestamp"""
        return datetime.now(timezone.utc).timestamp()
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = ""):
        """Record a metric data point"""
        if tags is None:
            tags = {}
            
        metric = MetricPoint(
            name=name,
            value=value,
            timestamp=self.timestamp(),
            tags=tags,
            unit=unit
        )
        
        # Add to buffer
        self.metrics_buffer.append(metric)
        
        # Add to aggregates for analysis
        self.metric_aggregates[name].append(value)
        
        # Log metric
        self.logger.info(f"METRIC | {name}={value}{unit} | tags={json.dumps(tags)}")
        
        # Persist to file periodically
        self._persist_metric(metric)
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        self.counters[name] += value
        self.record_metric(f"counter.{name}", self.counters[name], tags, "count")
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None, unit: str = ""):
        """Set a gauge metric"""
        self.gauges[name] = value
        self.record_metric(f"gauge.{name}", value, tags, unit)
    
    def record_timing(self, name: str, duration: float, tags: Dict[str, str] = None):
        """Record timing information"""
        self.timers[name].append(duration)
        # Keep only last 1000 timing samples
        if len(self.timers[name]) > 1000:
            self.timers[name] = self.timers[name][-1000:]
        
        self.record_metric(f"timer.{name}", duration, tags, "seconds")
    
    def timing_context(self, name: str, tags: Dict[str, str] = None):
        """Context manager for timing operations"""
        return TimingContext(self, name, tags)
    
    def get_metric_summary(self, name: str) -> Dict[str, Any]:
        """Get statistical summary of a metric"""
        if name not in self.metric_aggregates:
            return {}
            
        values = self.metric_aggregates[name]
        if not values:
            return {}
        
        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1] if values else 0
        }
    
    def get_timing_stats(self, name: str) -> Dict[str, float]:
        """Get timing statistics"""
        if name not in self.timers:
            return {}
            
        timings = self.timers[name]
        if not timings:
            return {}
        
        sorted_timings = sorted(timings)
        count = len(timings)
        
        return {
            "count": count,
            "avg": sum(timings) / count,
            "min": min(timings),
            "max": max(timings),
            "p50": sorted_timings[count // 2],
            "p95": sorted_timings[int(count * 0.95)] if count > 0 else 0,
            "p99": sorted_timings[int(count * 0.99)] if count > 0 else 0
        }
    
    def start_system_monitoring(self, interval: int = 30):
        """Start background system monitoring"""
        if self._monitoring_active:
            return
            
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._system_monitor_loop,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info(f"Started system monitoring with {interval}s interval")
    
    def stop_system_monitoring(self):
        """Stop background system monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("Stopped system monitoring")
    
    def _system_monitor_loop(self, interval: int):
        """Background system monitoring loop"""
        while self._monitoring_active:
            try:
                self._collect_system_metrics()
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in system monitoring: {e}")
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge("system.cpu_percent", cpu_percent, unit="%")
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.set_gauge("system.memory_used", memory.used, unit="bytes")
            self.set_gauge("system.memory_percent", memory.percent, unit="%")
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.set_gauge("system.disk_used", disk.used, unit="bytes")
            self.set_gauge("system.disk_percent", disk.percent, unit="%")
            
            # Process metrics for current process
            process = psutil.Process()
            self.set_gauge("process.memory_rss", process.memory_info().rss, unit="bytes")
            self.set_gauge("process.cpu_percent", process.cpu_percent(), unit="%")
            
            # Custom EPOCH5 metrics
            self._collect_epoch5_metrics()
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_epoch5_metrics(self):
        """Collect EPOCH5-specific metrics"""
        try:
            # Count files in archive
            if self.base_dir.exists():
                manifest_count = len(list((self.base_dir / "manifests").glob("*.txt"))) if (self.base_dir / "manifests").exists() else 0
                self.set_gauge("epoch5.manifest_count", manifest_count, unit="count")
                
                # Count ledger entries
                ledger_file = self.base_dir / "ledger.txt"
                if ledger_file.exists():
                    ledger_lines = len(ledger_file.read_text().strip().split('\n')) if ledger_file.stat().st_size > 0 else 0
                    self.set_gauge("epoch5.ledger_entries", ledger_lines, unit="count")
                
                # Archive size
                total_size = sum(f.stat().st_size for f in self.base_dir.rglob('*') if f.is_file())
                self.set_gauge("epoch5.archive_size", total_size, unit="bytes")
                
        except Exception as e:
            self.logger.error(f"Error collecting EPOCH5 metrics: {e}")
    
    def _persist_metric(self, metric: MetricPoint):
        """Persist metric to file storage"""
        try:
            metrics_file = self.metrics_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            metric_data = {
                "name": metric.name,
                "value": metric.value,
                "timestamp": metric.timestamp,
                "tags": metric.tags,
                "unit": metric.unit
            }
            
            with metrics_file.open('a') as f:
                f.write(json.dumps(metric_data) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error persisting metric: {e}")
    
    def export_metrics(self, format: str = "prometheus") -> str:
        """Export metrics in various formats"""
        if format == "prometheus":
            return self._export_prometheus()
        elif format == "json":
            return self._export_json()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Counters
        for name, value in self.counters.items():
            lines.append(f"# TYPE epoch5_counter_{name} counter")
            lines.append(f"epoch5_counter_{name} {value}")
        
        # Gauges
        for name, value in self.gauges.items():
            lines.append(f"# TYPE epoch5_gauge_{name} gauge")
            lines.append(f"epoch5_gauge_{name} {value}")
        
        return '\n'.join(lines)
    
    def _export_json(self) -> str:
        """Export metrics in JSON format"""
        return json.dumps({
            "timestamp": self.timestamp(),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "metrics_count": len(self.metrics_buffer)
        }, indent=2)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "system_health": {
                "cpu_percent": self.gauges.get("system.cpu_percent", 0),
                "memory_percent": self.gauges.get("system.memory_percent", 0),
                "disk_percent": self.gauges.get("system.disk_percent", 0)
            },
            "epoch5_stats": {
                "manifest_count": self.gauges.get("epoch5.manifest_count", 0),
                "ledger_entries": self.gauges.get("epoch5.ledger_entries", 0),
                "archive_size_mb": self.gauges.get("epoch5.archive_size", 0) / (1024 * 1024)
            },
            "recent_metrics": len(self.metrics_buffer)
        }

class TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: Dict[str, str] = None):
        self.collector = collector
        self.name = name
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.record_timing(self.name, duration, self.tags)

# Global metrics collector instance
_global_collector = None

def get_metrics_collector(base_dir: str = "./archive/EPOCH5") -> MetricsCollector:
    """Get global metrics collector instance"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector(base_dir)
    return _global_collector

def record_metric(name: str, value: float, tags: Dict[str, str] = None, unit: str = ""):
    """Convenience function to record metric"""
    collector = get_metrics_collector()
    collector.record_metric(name, value, tags, unit)

def increment_counter(name: str, value: int = 1, tags: Dict[str, str] = None):
    """Convenience function to increment counter"""
    collector = get_metrics_collector()
    collector.increment_counter(name, value, tags)

def set_gauge(name: str, value: float, tags: Dict[str, str] = None, unit: str = ""):
    """Convenience function to set gauge"""
    collector = get_metrics_collector()
    collector.set_gauge(name, value, tags, unit)

def timing_context(name: str, tags: Dict[str, str] = None):
    """Convenience function for timing context"""
    collector = get_metrics_collector()
    return collector.timing_context(name, tags)

# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EPOCH5 Metrics and Monitoring")
    parser.add_argument("command", choices=["start", "stop", "status", "export", "dashboard"])
    parser.add_argument("--format", choices=["prometheus", "json"], default="json", 
                       help="Export format for metrics")
    parser.add_argument("--interval", type=int, default=30,
                       help="Monitoring interval in seconds")
    parser.add_argument("--base-dir", default="./archive/EPOCH5",
                       help="Base directory for metrics storage")
    
    args = parser.parse_args()
    
    collector = MetricsCollector(args.base_dir)
    
    if args.command == "start":
        print("🔍 Starting EPOCH5 monitoring...")
        collector.start_system_monitoring(args.interval)
        print(f"✅ Monitoring started with {args.interval}s interval")
        print("Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            collector.stop_system_monitoring()
            print("\n🛑 Monitoring stopped")
    
    elif args.command == "status":
        dashboard_data = collector.get_dashboard_data()
        print("📊 EPOCH5 System Metrics:")
        print(json.dumps(dashboard_data, indent=2))
    
    elif args.command == "export":
        metrics_data = collector.export_metrics(args.format)
        print(metrics_data)
    
    elif args.command == "dashboard":
        dashboard_data = collector.get_dashboard_data()
        print("🖥️  EPOCH5 Dashboard Data:")
        print(f"System Health: CPU {dashboard_data['system_health']['cpu_percent']:.1f}%, "
              f"Memory {dashboard_data['system_health']['memory_percent']:.1f}%, "
              f"Disk {dashboard_data['system_health']['disk_percent']:.1f}%")
        print(f"EPOCH5 Stats: {dashboard_data['epoch5_stats']['manifest_count']} manifests, "
              f"{dashboard_data['epoch5_stats']['ledger_entries']} ledger entries, "
              f"{dashboard_data['epoch5_stats']['archive_size_mb']:.1f} MB archive")
        print(f"Active Metrics: {dashboard_data['recent_metrics']} data points")

if __name__ == "__main__":
    main()