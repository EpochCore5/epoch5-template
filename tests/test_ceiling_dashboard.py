"""
Tests for ceiling dashboard functionality
"""

import pytest
import json
import tempfile
import threading
import time
import sys
import os
import http.client
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from ceiling_dashboard import CeilingDashboard, CeilingDashboardHandler
except ImportError as e:
    pytest.skip(f"Could not import ceiling_dashboard module: {e}", allow_module_level=True)


class MockHTTPRequest:
    """Mock HTTP request for testing handler"""
    def __init__(self, path="/"):
        self.path = path


class TestCeilingDashboardHandler:
    """Test cases for CeilingDashboardHandler class"""
    
    @pytest.fixture
    def mock_wfile(self):
        """Mock wfile with buffer to capture output"""
        class MockWFile:
            def __init__(self):
                self.buffer = bytearray()
                
            def write(self, data):
                self.buffer.extend(data)
                
        return MockWFile()
    
    @pytest.fixture
    def mock_ceiling_manager(self):
        """Create mock ceiling manager"""
        mock_cm = MagicMock()
        
        # Setup mock load_ceilings method
        mock_cm.load_ceilings.return_value = {
            "configurations": {
                "config1": {
                    "name": "Test Config",
                    "type": "BUDGET",
                    "limit": 1000
                }
            },
            "last_updated": "2024-01-01T00:00:00Z"
        }
        
        # Setup mock load_service_tiers method
        mock_cm.load_service_tiers.return_value = {
            "tiers": {
                "basic": {
                    "name": "Basic Tier",
                    "monthly_cost": 10,
                    "ceilings": {
                        "budget": 100,
                        "latency": 1.0,
                        "rate_limit": 100,
                        "success_rate": 0.95
                    }
                },
                "premium": {
                    "name": "Premium Tier",
                    "monthly_cost": 50,
                    "ceilings": {
                        "budget": 500,
                        "latency": 0.5,
                        "rate_limit": 500,
                        "success_rate": 0.99
                    }
                }
            }
        }
        
        # Setup mock ceiling_events_log
        events_log = tempfile.NamedTemporaryFile(delete=False, mode='w')
        event_data = {
            "timestamp": "2024-01-01T00:00:00Z",
            "event_type": "DYNAMIC_ADJUSTMENT",
            "data": {
                "config_id": "config1",
                "performance_score": 0.85,
                "adjustments": {"latency": 0.2}
            }
        }
        events_log.write(json.dumps(event_data) + "\n")
        events_log.close()
        
        mock_cm.ceiling_events_log = Path(events_log.name)
        
        # Mock audit system if needed for security
        mock_audit_system = MagicMock()
        mock_audit_system.verify_seals.return_value = {
            "status": "PASSED", 
            "valid_count": 10,
            "invalid_count": 0
        }
        mock_audit_system.generate_audit_scroll.return_value = [
            {
                "ts": "2024-01-01T00:00:00Z",
                "event": "ceiling_verification",
                "note": "Successful verification"
            }
        ]
        mock_cm.audit_system = mock_audit_system
        
        return mock_cm
    
    @pytest.fixture
    def mock_integration(self):
        """Create mock integration system"""
        mock_int = MagicMock()
        
        # Setup mock get_system_status method
        mock_int.get_system_status.return_value = {
            "timestamp": "2024-01-01T00:00:00Z",
            "components": {
                "agents": {
                    "active": 5,
                    "total": 10
                },
                "ceilings": {
                    "total_configurations": 3,
                    "average_performance_score": 0.87,
                    "dynamic_adjustments_active": 2
                },
                "policies": {
                    "active_policies": 8,
                    "total_grants": 25
                },
                "cycles": {
                    "completed": 15,
                    "total": 20
                }
            }
        }
        
        return mock_int
    
    @pytest.fixture
    def handler(self, mock_wfile, mock_ceiling_manager, mock_integration):
        """Create a dashboard handler for testing"""
        handler = CeilingDashboardHandler.__new__(CeilingDashboardHandler)
        handler.ceiling_manager = mock_ceiling_manager
        handler.integration = mock_integration
        handler.wfile = mock_wfile
        
        # Mock send_response and send_header methods
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        
        return handler
    
    def test_serve_dashboard(self, handler):
        """Test serving the main dashboard HTML"""
        handler.serve_dashboard()
        
        # Verify response setup
        handler.send_response.assert_called_once_with(200)
        handler.send_header.assert_called_once_with("Content-type", "text/html")
        handler.end_headers.assert_called_once()
        
        # Verify content
        html_content = handler.wfile.buffer.decode('utf-8')
        assert "<!DOCTYPE html>" in html_content
        assert "<title>EPOCH5 Ceiling Dashboard</title>" in html_content
        assert "Real-time Performance & Revenue Optimization" in html_content
    
    def test_serve_api_status(self, handler):
        """Test serving the status API endpoint"""
        handler.serve_api_status()
        
        # Verify response setup
        handler.send_response.assert_called_once_with(200)
        # Don't check exact call count because CeilingDashboardHandler sets multiple headers
        handler.send_header.assert_any_call("Content-type", "application/json")
        handler.end_headers.assert_called_once()
        
        # Verify content
        response_data = json.loads(handler.wfile.buffer.decode('utf-8'))
        assert "timestamp" in response_data
        assert "components" in response_data
        assert "agents" in response_data["components"]
        assert "ceilings" in response_data["components"]
        assert "policies" in response_data["components"]
    
    def test_serve_api_ceilings(self, handler):
        """Test serving the ceilings API endpoint"""
        handler.serve_api_ceilings()
        
        # Verify response setup
        handler.send_response.assert_called_once_with(200)
        # Don't check exact call count because CeilingDashboardHandler sets multiple headers
        handler.send_header.assert_any_call("Content-type", "application/json")
        handler.end_headers.assert_called_once()
        
        # Verify content
        response_data = json.loads(handler.wfile.buffer.decode('utf-8'))
        assert "configurations" in response_data
        assert "service_tiers" in response_data
        assert "last_updated" in response_data
        
        # Verify service tiers
        assert "basic" in response_data["service_tiers"]
        assert "premium" in response_data["service_tiers"]
        assert response_data["service_tiers"]["basic"]["monthly_cost"] == 10
    
    def test_serve_api_performance(self, handler):
        """Test serving the performance API endpoint"""
        handler.serve_api_performance()
        
        # Verify response setup
        handler.send_response.assert_called_once_with(200)
        # Don't check exact call count because CeilingDashboardHandler sets multiple headers
        handler.send_header.assert_any_call("Content-type", "application/json")
        handler.end_headers.assert_called_once()
        
        # Verify content
        response_data = json.loads(handler.wfile.buffer.decode('utf-8'))
        assert isinstance(response_data, list)
        assert len(response_data) > 0
        assert "timestamp" in response_data[0]
        assert "performance_score" in response_data[0]
        assert "config_id" in response_data[0]
        assert "adjustments" in response_data[0]
    
    def test_serve_api_security(self, handler):
        """Test serving the security API endpoint"""
        handler.serve_api_security()
        
        # Verify response setup
        handler.send_response.assert_called_once_with(200)
        # Don't check exact call count because CeilingDashboardHandler sets multiple headers
        handler.send_header.assert_any_call("Content-type", "application/json")
        handler.end_headers.assert_called_once()
        
        # Verify content
        response_data = json.loads(handler.wfile.buffer.decode('utf-8'))
        assert "status" in response_data
        assert "verification" in response_data
        assert "recent_events" in response_data
        assert response_data["verification"]["status"] == "PASSED"
    
    def test_send_json_response(self, handler):
        """Test JSON response formatting"""
        test_data = {"test": "data", "nested": {"value": 123}}
        handler.send_json_response(test_data)
        
        # Verify response setup
        handler.send_response.assert_called_once_with(200)
        # Don't check exact call count because CeilingDashboardHandler sets multiple headers
        handler.send_header.assert_any_call("Content-type", "application/json")
        handler.end_headers.assert_called_once()
        
        # Verify content
        response_data = json.loads(handler.wfile.buffer.decode('utf-8'))
        assert response_data == test_data
    
    def test_do_get_dashboard(self, handler):
        """Test GET request routing for dashboard path"""
        handler.path = "/"
        
        # Mock serve_dashboard method
        original_serve_dashboard = handler.serve_dashboard
        handler.serve_dashboard = MagicMock()
        
        handler.do_GET()
        
        # Verify routing
        handler.serve_dashboard.assert_called_once()
        
        # Restore original method
        handler.serve_dashboard = original_serve_dashboard
    
    def test_do_get_api_status(self, handler):
        """Test GET request routing for API status path"""
        handler.path = "/api/status"
        
        # Mock serve_api_status method
        original_serve_api_status = handler.serve_api_status
        handler.serve_api_status = MagicMock()
        
        handler.do_GET()
        
        # Verify routing
        handler.serve_api_status.assert_called_once()
        
        # Restore original method
        handler.serve_api_status = original_serve_api_status
    
    def test_do_get_api_ceilings(self, handler):
        """Test GET request routing for API ceilings path"""
        handler.path = "/api/ceilings"
        
        # Mock serve_api_ceilings method
        original_serve_api_ceilings = handler.serve_api_ceilings
        handler.serve_api_ceilings = MagicMock()
        
        handler.do_GET()
        
        # Verify routing
        handler.serve_api_ceilings.assert_called_once()
        
        # Restore original method
        handler.serve_api_ceilings = original_serve_api_ceilings
    
    def test_do_get_api_performance(self, handler):
        """Test GET request routing for API performance path"""
        handler.path = "/api/performance"
        
        # Mock serve_api_performance method
        original_serve_api_performance = handler.serve_api_performance
        handler.serve_api_performance = MagicMock()
        
        handler.do_GET()
        
        # Verify routing
        handler.serve_api_performance.assert_called_once()
        
        # Restore original method
        handler.serve_api_performance = original_serve_api_performance
    
    def test_do_get_api_security(self, handler):
        """Test GET request routing for API security path"""
        handler.path = "/api/security"
        
        # Mock serve_api_security method
        original_serve_api_security = handler.serve_api_security
        handler.serve_api_security = MagicMock()
        
        handler.do_GET()
        
        # Verify routing
        handler.serve_api_security.assert_called_once()
        
        # Restore original method
        handler.serve_api_security = original_serve_api_security
    
    def test_do_get_not_found(self, handler):
        """Test GET request routing for unknown path"""
        handler.path = "/unknown/path"
        
        # Mock send_error method
        handler.send_error = MagicMock()
        
        handler.do_GET()
        
        # Verify error response
        handler.send_error.assert_called_once_with(404, "Endpoint not found")


class TestCeilingDashboard:
    """Test cases for CeilingDashboard class"""
    
    @pytest.fixture
    def mock_http_server(self):
        """Mock HTTPServer for testing"""
        with patch('ceiling_dashboard.HTTPServer') as mock_server:
            # Setup mock instance
            mock_instance = MagicMock()
            mock_server.return_value = mock_instance
            yield mock_server
    
    def test_initialization(self, temp_dir):
        """Test dashboard initialization"""
        with patch('ceiling_dashboard.CeilingManager') as mock_cm, \
             patch('ceiling_dashboard.EPOCH5Integration') as mock_integration:
            
            # Force CEILING_AVAILABLE to True for testing
            with patch('ceiling_dashboard.CEILING_AVAILABLE', True):
                dashboard = CeilingDashboard(base_dir=temp_dir)
                
                assert dashboard is not None
                assert dashboard.base_dir == temp_dir
                assert dashboard.port == 8080  # Default port
                
                # Verify managers are initialized
                mock_cm.assert_called_once_with(temp_dir)
                mock_integration.assert_called_once_with(temp_dir)
    
    def test_initialization_no_ceiling(self, temp_dir):
        """Test dashboard initialization when ceiling is not available"""
        with patch('ceiling_dashboard.CEILING_AVAILABLE', False):
            dashboard = CeilingDashboard(base_dir=temp_dir)
            
            assert dashboard is not None
            assert dashboard.base_dir == temp_dir
            assert dashboard.ceiling_manager is None
            assert dashboard.integration is None
    
    def test_start_server(self, mock_http_server, temp_dir):
        """Test starting the dashboard server"""
        with patch('ceiling_dashboard.CeilingManager'), \
             patch('ceiling_dashboard.EPOCH5Integration'), \
             patch('ceiling_dashboard.CEILING_AVAILABLE', True), \
             patch('builtins.print') as mock_print:
            
            dashboard = CeilingDashboard(base_dir=temp_dir, port=9000)
            
            # Mock serve_forever to simulate CTRL+C
            mock_instance = mock_http_server.return_value
            mock_instance.serve_forever.side_effect = KeyboardInterrupt()
            
            # Call start_server
            dashboard.start_server()
            
            # Verify server creation
            mock_http_server.assert_called_once_with(("localhost", 9000), mock_http_server.call_args[0][1])
            
            # Verify serve_forever called
            mock_instance.serve_forever.assert_called_once()
            
            # Verify server_close called on KeyboardInterrupt
            mock_instance.server_close.assert_called_once()
            
            # Verify print messages
            assert mock_print.call_count >= 4  # At least 4 print statements
            mock_print.assert_any_call("\n🛑 Dashboard server stopped")


@pytest.mark.skip("Integration test requiring actual server")
class TestCeilingDashboardIntegration:
    """Integration tests for CeilingDashboard with actual server"""
    
    @pytest.fixture
    def dashboard_server(self, temp_dir):
        """Start a real dashboard server for testing"""
        with patch('ceiling_dashboard.CeilingManager') as mock_cm, \
             patch('ceiling_dashboard.EPOCH5Integration') as mock_integration, \
             patch('ceiling_dashboard.CEILING_AVAILABLE', True):
            
            # Initialize dashboard with test port
            dashboard = CeilingDashboard(base_dir=temp_dir, port=8888)
            
            # Setup mock methods
            dashboard.ceiling_manager = mock_cm.return_value
            dashboard.integration = mock_integration.return_value
            
            # Start server in a separate thread
            server_thread = threading.Thread(target=dashboard.start_server)
            server_thread.daemon = True
            server_thread.start()
            
            # Wait for server to start
            time.sleep(0.5)
            
            yield dashboard
            
            # No need to clean up as daemon thread will be terminated
    
    def test_live_server(self, dashboard_server):
        """Test connection to live server"""
        # Connect to the server
        conn = http.client.HTTPConnection("localhost", 8888)
        conn.request("GET", "/")
        
        # Get response
        response = conn.getresponse()
        data = response.read().decode()
        
        # Verify response
        assert response.status == 200
        assert "EPOCH5 Ceiling Dashboard" in data
        
        conn.close()
