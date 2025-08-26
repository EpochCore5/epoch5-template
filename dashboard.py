#!/usr/bin/env python3
"""
Real-time monitoring dashboard for EPOCH5 system
Web-based dashboard for visualizing metrics and system health
"""

import json
import time
import asyncio
import websockets
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

from monitoring import get_metrics_collector

class DashboardServer:
    """Web-based monitoring dashboard server"""
    
    def __init__(self, port: int = 8080, ws_port: int = 8081, base_dir: str = "./archive/EPOCH5"):
        self.port = port
        self.ws_port = ws_port
        self.base_dir = base_dir
        self.metrics_collector = get_metrics_collector(base_dir)
        self.running = False
        self.connected_clients = set()
        
        # Start system monitoring
        self.metrics_collector.start_system_monitoring(interval=5)
        
    def create_dashboard_html(self) -> str:
        """Generate HTML for the dashboard"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EPOCH5 Monitoring Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .status-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .status-card:hover {{
            transform: translateY(-5px);
        }}
        .status-card h3 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-unit {{
            font-size: 0.8em;
            color: #666;
        }}
        .health-good {{ color: #28a745; }}
        .health-warning {{ color: #ffc107; }}
        .health-critical {{ color: #dc3545; }}
        .metrics-table {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .metrics-table h3 {{
            margin: 0;
            padding: 20px;
            background: #667eea;
            color: white;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .status-online {{ background: #28a745; }}
        .status-offline {{ background: #dc3545; }}
        .refresh-time {{
            text-align: center;
            color: white;
            margin-top: 20px;
            opacity: 0.8;
        }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .progress-fill {{
            height: 100%;
            transition: width 0.3s ease;
        }}
        .charts-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 30px;
        }}
        .chart-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .log-container {{
            background: #1a1a1a;
            color: #00ff00;
            border-radius: 10px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            max-height: 300px;
            overflow-y: auto;
            margin-top: 20px;
        }}
        .log-entry {{
            margin-bottom: 5px;
            padding: 2px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ EPOCH5 Monitoring Dashboard</h1>
            <p>Real-time system monitoring and metrics visualization</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>📊 System Health</h3>
                <div>CPU: <span id="cpu-usage" class="metric-value">--</span><span class="metric-unit">%</span></div>
                <div class="progress-bar">
                    <div id="cpu-bar" class="progress-fill" style="background: #28a745; width: 0%"></div>
                </div>
                <div>Memory: <span id="memory-usage" class="metric-value">--</span><span class="metric-unit">%</span></div>
                <div class="progress-bar">
                    <div id="memory-bar" class="progress-fill" style="background: #17a2b8; width: 0%"></div>
                </div>
            </div>
            
            <div class="status-card">
                <h3>🗂️ EPOCH5 Archive</h3>
                <div>Manifests: <span id="manifest-count" class="metric-value">--</span></div>
                <div>Ledger Entries: <span id="ledger-entries" class="metric-value">--</span></div>
                <div>Archive Size: <span id="archive-size" class="metric-value">--</span><span class="metric-unit">MB</span></div>
            </div>
            
            <div class="status-card">
                <h3>🔧 System Status</h3>
                <div><span class="status-indicator" id="system-indicator"></span>System: <span id="system-status">--</span></div>
                <div><span class="status-indicator" id="monitoring-indicator"></span>Monitoring: <span id="monitoring-status">--</span></div>
                <div><span class="status-indicator" id="metrics-indicator"></span>Metrics: <span id="metrics-status">--</span></div>
            </div>
            
            <div class="status-card">
                <h3>⚡ Performance</h3>
                <div>Metrics/sec: <span id="metrics-rate" class="metric-value">--</span></div>
                <div>Uptime: <span id="uptime" class="metric-value">--</span></div>
                <div>Last Update: <span id="last-update">--</span></div>
            </div>
        </div>
        
        <div class="metrics-table">
            <h3>📈 Recent Metrics</h3>
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Unit</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="metrics-tbody">
                    <tr><td colspan="4">Loading metrics...</td></tr>
                </tbody>
            </table>
        </div>
        
        <div class="log-container">
            <div style="color: white; margin-bottom: 10px;">📋 System Log</div>
            <div id="log-output">
                <div class="log-entry">System starting up...</div>
            </div>
        </div>
        
        <div class="refresh-time">
            Last refreshed: <span id="refresh-time">--</span>
        </div>
    </div>
    
    <script>
        class Dashboard {{
            constructor() {{
                this.ws = null;
                this.startTime = Date.now();
                this.metricsReceived = 0;
                this.setupWebSocket();
                this.updateUptime();
                setInterval(() => this.updateUptime(), 1000);
            }}
            
            setupWebSocket() {{
                try {{
                    this.ws = new WebSocket('ws://localhost:{self.ws_port}');
                    
                    this.ws.onopen = () => {{
                        console.log('Connected to monitoring server');
                        this.updateConnectionStatus(true);
                        this.addLogEntry('📡 Connected to monitoring server');
                    }};
                    
                    this.ws.onmessage = (event) => {{
                        const data = JSON.parse(event.data);
                        this.updateDashboard(data);
                        this.metricsReceived++;
                    }};
                    
                    this.ws.onclose = () => {{
                        console.log('Disconnected from monitoring server');
                        this.updateConnectionStatus(false);
                        this.addLogEntry('❌ Disconnected from monitoring server');
                        // Attempt to reconnect
                        setTimeout(() => this.setupWebSocket(), 5000);
                    }};
                    
                    this.ws.onerror = (error) => {{
                        console.error('WebSocket error:', error);
                        this.addLogEntry('⚠️ WebSocket connection error');
                    }};
                    
                }} catch (error) {{
                    console.error('Failed to setup WebSocket:', error);
                    this.updateConnectionStatus(false);
                }}
            }}
            
            updateConnectionStatus(connected) {{
                const systemIndicator = document.getElementById('system-indicator');
                const systemStatus = document.getElementById('system-status');
                const monitoringIndicator = document.getElementById('monitoring-indicator');
                const monitoringStatus = document.getElementById('monitoring-status');
                
                if (connected) {{
                    systemIndicator.className = 'status-indicator status-online';
                    systemStatus.textContent = 'Online';
                    monitoringIndicator.className = 'status-indicator status-online';
                    monitoringStatus.textContent = 'Active';
                }} else {{
                    systemIndicator.className = 'status-indicator status-offline';
                    systemStatus.textContent = 'Offline';
                    monitoringIndicator.className = 'status-indicator status-offline';
                    monitoringStatus.textContent = 'Disconnected';
                }}
            }}
            
            updateDashboard(data) {{
                // Update system health
                const cpuUsage = data.system_health.cpu_percent.toFixed(1);
                const memoryUsage = data.system_health.memory_percent.toFixed(1);
                
                document.getElementById('cpu-usage').textContent = cpuUsage;
                document.getElementById('memory-usage').textContent = memoryUsage;
                document.getElementById('cpu-bar').style.width = cpuUsage + '%';
                document.getElementById('memory-bar').style.width = memoryUsage + '%';
                
                // Color code based on usage
                document.getElementById('cpu-bar').style.background = this.getHealthColor(cpuUsage);
                document.getElementById('memory-bar').style.background = this.getHealthColor(memoryUsage);
                
                // Update EPOCH5 stats
                document.getElementById('manifest-count').textContent = data.epoch5_stats.manifest_count;
                document.getElementById('ledger-entries').textContent = data.epoch5_stats.ledger_entries;
                document.getElementById('archive-size').textContent = data.epoch5_stats.archive_size_mb.toFixed(1);
                
                // Update metrics status
                const metricsIndicator = document.getElementById('metrics-indicator');
                const metricsStatus = document.getElementById('metrics-status');
                metricsIndicator.className = 'status-indicator status-online';
                metricsStatus.textContent = `${{data.recent_metrics}} active`;
                
                // Update metrics rate
                const metricsRate = (this.metricsReceived / ((Date.now() - this.startTime) / 1000)).toFixed(1);
                document.getElementById('metrics-rate').textContent = metricsRate;
                
                // Update last update time
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                document.getElementById('refresh-time').textContent = new Date().toLocaleString();
                
                // Update metrics table
                this.updateMetricsTable(data);
                
                // Add log entry for significant events
                if (cpuUsage > 80 || memoryUsage > 80) {{
                    this.addLogEntry(`⚠️ High resource usage: CPU ${{cpuUsage}}%, Memory ${{memoryUsage}}%`);
                }}
            }}
            
            updateMetricsTable(data) {{
                const tbody = document.getElementById('metrics-tbody');
                tbody.innerHTML = '';
                
                const metrics = [
                    {{ name: 'CPU Usage', value: data.system_health.cpu_percent.toFixed(1), unit: '%', status: this.getHealthStatus(data.system_health.cpu_percent) }},
                    {{ name: 'Memory Usage', value: data.system_health.memory_percent.toFixed(1), unit: '%', status: this.getHealthStatus(data.system_health.memory_percent) }},
                    {{ name: 'Disk Usage', value: data.system_health.disk_percent.toFixed(1), unit: '%', status: this.getHealthStatus(data.system_health.disk_percent) }},
                    {{ name: 'Manifest Count', value: data.epoch5_stats.manifest_count, unit: 'files', status: 'good' }},
                    {{ name: 'Ledger Entries', value: data.epoch5_stats.ledger_entries, unit: 'entries', status: 'good' }},
                    {{ name: 'Archive Size', value: data.epoch5_stats.archive_size_mb.toFixed(1), unit: 'MB', status: 'good' }}
                ];
                
                metrics.forEach(metric => {{
                    const row = tbody.insertRow();
                    row.innerHTML = `
                        <td>${{metric.name}}</td>
                        <td>${{metric.value}}</td>
                        <td>${{metric.unit}}</td>
                        <td class="health-${{metric.status}}">${{metric.status.toUpperCase()}}</td>
                    `;
                }});
            }}
            
            getHealthColor(value) {{
                if (value < 50) return '#28a745';
                if (value < 80) return '#ffc107';
                return '#dc3545';
            }}
            
            getHealthStatus(value) {{
                if (value < 50) return 'good';
                if (value < 80) return 'warning';
                return 'critical';
            }}
            
            updateUptime() {{
                const uptime = Math.floor((Date.now() - this.startTime) / 1000);
                const hours = Math.floor(uptime / 3600);
                const minutes = Math.floor((uptime % 3600) / 60);
                const seconds = uptime % 60;
                
                document.getElementById('uptime').textContent = 
                    `${{hours.toString().padStart(2, '0')}}:${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
            }}
            
            addLogEntry(message) {{
                const logOutput = document.getElementById('log-output');
                const timestamp = new Date().toLocaleTimeString();
                const entry = document.createElement('div');
                entry.className = 'log-entry';
                entry.textContent = `[${{timestamp}}] ${{message}}`;
                
                logOutput.appendChild(entry);
                
                // Keep only last 50 log entries
                while (logOutput.children.length > 50) {{
                    logOutput.removeChild(logOutput.firstChild);
                }}
                
                // Scroll to bottom
                logOutput.scrollTop = logOutput.scrollHeight;
            }}
        }}
        
        // Start dashboard when page loads
        document.addEventListener('DOMContentLoaded', () => {{
            new Dashboard();
        }});
    </script>
</body>
</html>
        """
    
    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections"""
        self.connected_clients.add(websocket)
        print(f"Client connected: {websocket.remote_address}")
        
        try:
            while True:
                # Get dashboard data
                dashboard_data = self.metrics_collector.get_dashboard_data()
                
                # Send to client
                await websocket.send(json.dumps(dashboard_data))
                
                # Wait before next update
                await asyncio.sleep(2)
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.remove(websocket)
            print(f"Client disconnected: {websocket.remote_address}")
    
    async def start_websocket_server(self):
        """Start WebSocket server for real-time updates"""
        print(f"🔌 Starting WebSocket server on port {self.ws_port}")
        server = await websockets.serve(self.websocket_handler, "localhost", self.ws_port)
        return server
    
    def start_http_server(self):
        """Start HTTP server for dashboard"""
        # Create dashboard HTML file
        dashboard_html = self.create_dashboard_html()
        dashboard_file = Path("dashboard.html")
        dashboard_file.write_text(dashboard_html)
        
        class DashboardHandler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/" or self.path == "/dashboard":
                    self.path = "/dashboard.html"
                return super().do_GET()
        
        # Start HTTP server
        with socketserver.TCPServer(("", self.port), DashboardHandler) as httpd:
            print(f"🌐 Dashboard server running on http://localhost:{self.port}")
            print(f"📊 Opening dashboard in browser...")
            
            # Open browser
            webbrowser.open(f"http://localhost:{self.port}")
            
            httpd.serve_forever()
    
    async def run_async(self):
        """Run both servers asynchronously"""
        self.running = True
        
        # Start WebSocket server
        ws_server = await self.start_websocket_server()
        
        # Start HTTP server in thread
        http_thread = threading.Thread(target=self.start_http_server, daemon=True)
        http_thread.start()
        
        print("✅ Dashboard started successfully!")
        print(f"📊 Dashboard: http://localhost:{self.port}")
        print(f"🔌 WebSocket: ws://localhost:{self.ws_port}")
        print("Press Ctrl+C to stop...")
        
        try:
            # Keep running
            await ws_server.wait_closed()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down dashboard...")
            self.metrics_collector.stop_system_monitoring()
    
    def run(self):
        """Run the dashboard server"""
        asyncio.run(self.run_async())

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EPOCH5 Monitoring Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="HTTP server port")
    parser.add_argument("--ws-port", type=int, default=8081, help="WebSocket server port")
    parser.add_argument("--base-dir", default="./archive/EPOCH5", help="Base directory for metrics")
    
    args = parser.parse_args()
    
    dashboard = DashboardServer(args.port, args.ws_port, args.base_dir)
    dashboard.run()

if __name__ == "__main__":
    main()