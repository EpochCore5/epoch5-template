#!/usr/bin/env python3
"""
EPOCH5 Health Check Server
Simple HTTP server for health checks and basic metrics
"""

import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from integration import EPOCH5Integration


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health checks and metrics"""
    
    def __init__(self, *args, integration_instance=None, **kwargs):
        self.integration = integration_instance or EPOCH5Integration()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/health':
            self.handle_health()
        elif path == '/metrics':
            self.handle_metrics()
        elif path == '/status':
            self.handle_status()
        else:
            self.send_error(404, "Not Found")
    
    def handle_health(self):
        """Handle health check endpoint"""
        try:
            # Basic health check
            status = self.integration.get_system_status()
            
            # Simple health check - if we can get status, we're healthy
            health_data = {
                "status": "healthy" if status else "unhealthy",
                "timestamp": self.integration.timestamp(),
                "version": "1.0.0"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(health_data).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_data = {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": self.integration.timestamp()
            }
            self.wfile.write(json.dumps(error_data).encode())
    
    def handle_metrics(self):
        """Handle Prometheus-style metrics endpoint"""
        try:
            status = self.integration.get_system_status()
            
            # Generate Prometheus-style metrics
            metrics = []
            metrics.append("# HELP epoch5_agents_total Total number of agents")
            metrics.append("# TYPE epoch5_agents_total counter")
            metrics.append(f"epoch5_agents_total {status.get('agents', {}).get('total', 0)}")
            
            metrics.append("# HELP epoch5_agents_active Number of active agents")
            metrics.append("# TYPE epoch5_agents_active gauge")
            metrics.append(f"epoch5_agents_active {status.get('agents', {}).get('active', 0)}")
            
            metrics.append("# HELP epoch5_policies_total Total number of policies")
            metrics.append("# TYPE epoch5_policies_total counter")
            metrics.append(f"epoch5_policies_total {status.get('policies', {}).get('total_policies', 0)}")
            
            metrics.append("# HELP epoch5_capsules_total Total number of capsules")
            metrics.append("# TYPE epoch5_capsules_total counter")
            metrics.append(f"epoch5_capsules_total {status.get('capsules', {}).get('total_capsules', 0)}")
            
            metrics.append("# HELP epoch5_up Service availability")
            metrics.append("# TYPE epoch5_up gauge")
            metrics.append("epoch5_up 1")
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('\n'.join(metrics).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"# Error getting metrics: {str(e)}\n".encode())
    
    def handle_status(self):
        """Handle detailed status endpoint"""
        try:
            status = self.integration.get_system_status()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status, indent=2).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_data = {
                "error": str(e),
                "timestamp": self.integration.timestamp()
            }
            self.wfile.write(json.dumps(error_data).encode())
    
    def log_message(self, format, *args):
        """Override to reduce logging verbosity"""
        return  # Silent logging


def create_handler_class(integration_instance):
    """Create handler class with integration instance"""
    return lambda *args, **kwargs: HealthCheckHandler(*args, integration_instance=integration_instance, **kwargs)


def start_health_server(port=8080):
    """Start the health check server"""
    integration = EPOCH5Integration()
    handler_class = create_handler_class(integration)
    
    server = HTTPServer(('0.0.0.0', port), handler_class)
    print(f"Health check server starting on port {port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"Metrics: http://localhost:{port}/metrics")
    print(f"Status: http://localhost:{port}/status")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down health check server...")
        server.shutdown()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='EPOCH5 Health Check Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on (default: 8080)')
    
    args = parser.parse_args()
    start_health_server(args.port)