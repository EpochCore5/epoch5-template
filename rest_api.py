#!/usr/bin/env python3
"""
REST API for EdgeCapsule Cloud Mesh Ledger
Flask-based API to serve capsule files, ledger lines, and audit reports programmatically
Integrates with EPOCH5 ledger system, capsule management, and audit scanner
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from functools import wraps

try:
    from flask import Flask, jsonify, request, send_file, abort
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Install with: pip install flask flask-cors")

# Import our custom modules
from audit_scanner import LedgerAuditScanner
from svg_visualizer import SVGLedgerVisualizer
from capsule_metadata import CapsuleManager
from meta_capsule import MetaCapsuleCreator

class EdgeCapsuleAPI:
    def __init__(self, base_dir: str = "./archive/EPOCH5"):
        self.base_dir = Path(base_dir)
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for web access
        
        # Initialize components
        self.audit_scanner = LedgerAuditScanner(str(self.base_dir))
        self.visualizer = SVGLedgerVisualizer(str(self.base_dir))
        self.capsule_manager = CapsuleManager(str(self.base_dir))
        self.meta_creator = MetaCapsuleCreator(str(self.base_dir))
        
        # Setup routes
        self.setup_routes()
        
    def timestamp(self) -> str:
        """Generate ISO timestamp consistent with EPOCH5"""
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def error_handler(self, f):
        """Decorator to handle API errors consistently"""
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except FileNotFoundError as e:
                return jsonify({"error": "Resource not found", "details": str(e)}), 404
            except ValueError as e:
                return jsonify({"error": "Invalid input", "details": str(e)}), 400
            except Exception as e:
                return jsonify({"error": "Internal server error", "details": str(e)}), 500
        return wrapper
    
    def setup_routes(self):
        """Setup all API routes"""
        
        # Root and health
        @self.app.route('/')
        def root():
            return jsonify({
                "service": "EdgeCapsule Cloud Mesh Ledger API",
                "version": "1.0.0",
                "timestamp": self.timestamp(),
                "endpoints": {
                    "health": "/health",
                    "ledger": "/api/ledger",
                    "capsules": "/api/capsules", 
                    "audit": "/api/audit",
                    "visualization": "/api/visualization",
                    "meta-capsules": "/api/meta-capsules"
                }
            })
        
        @self.app.route('/health')
        def health():
            return jsonify({
                "status": "healthy",
                "timestamp": self.timestamp(),
                "components": {
                    "audit_scanner": "available",
                    "visualizer": "available",
                    "capsule_manager": "available",
                    "meta_creator": "available"
                }
            })
        
        # Ledger endpoints
        @self.app.route('/api/ledger')
        @self.error_handler
        def get_ledger():
            """Get ledger entries"""
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            ledger_file = self.base_dir / "ledger.log"
            if not ledger_file.exists():
                return jsonify({"entries": [], "total": 0, "message": "No ledger found"})
            
            with open(ledger_file, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            total = len(lines)
            entries = []
            
            # Apply pagination
            start_idx = max(0, min(offset, total))
            end_idx = min(start_idx + limit, total)
            
            for i, line in enumerate(lines[start_idx:end_idx], start=start_idx):
                entry = self.parse_ledger_entry(line)
                entry["line_number"] = i + 1
                entries.append(entry)
            
            return jsonify({
                "entries": entries,
                "total": total,
                "offset": offset,
                "limit": limit,
                "timestamp": self.timestamp()
            })
        
        @self.app.route('/api/ledger/<int:line_number>')
        @self.error_handler
        def get_ledger_entry(line_number: int):
            """Get specific ledger entry by line number"""
            ledger_file = self.base_dir / "ledger.log"
            if not ledger_file.exists():
                abort(404)
            
            with open(ledger_file, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            if line_number < 1 or line_number > len(lines):
                abort(404)
            
            entry = self.parse_ledger_entry(lines[line_number - 1])
            entry["line_number"] = line_number
            
            return jsonify({
                "entry": entry,
                "timestamp": self.timestamp()
            })
        
        # Capsule endpoints
        @self.app.route('/api/capsules')
        @self.error_handler
        def list_capsules():
            """List all capsules"""
            capsules_dir = self.base_dir / "capsules"
            if not capsules_dir.exists():
                return jsonify({"capsules": [], "total": 0})
            
            capsules = []
            for capsule_file in capsules_dir.glob("*.json"):
                try:
                    with open(capsule_file, 'r') as f:
                        capsule_data = json.load(f)
                    
                    capsule_summary = {
                        "capsule_id": capsule_data.get("capsule_id"),
                        "created_at": capsule_data.get("created_at"),
                        "content_hash": capsule_data.get("content_hash"),
                        "file_path": str(capsule_file),
                        "size": capsule_file.stat().st_size
                    }
                    capsules.append(capsule_summary)
                except Exception:
                    continue
            
            return jsonify({
                "capsules": capsules,
                "total": len(capsules),
                "timestamp": self.timestamp()
            })
        
        @self.app.route('/api/capsules/<capsule_id>')
        @self.error_handler
        def get_capsule(capsule_id: str):
            """Get specific capsule data"""
            capsules_dir = self.base_dir / "capsules"
            capsule_file = capsules_dir / f"{capsule_id}.json"
            
            if not capsule_file.exists():
                abort(404)
            
            with open(capsule_file, 'r') as f:
                capsule_data = json.load(f)
            
            return jsonify({
                "capsule": capsule_data,
                "timestamp": self.timestamp()
            })
        
        @self.app.route('/api/capsules/<capsule_id>/verify')
        @self.error_handler
        def verify_capsule(capsule_id: str):
            """Verify capsule integrity"""
            try:
                result = self.capsule_manager.verify_capsule_integrity(capsule_id)
                return jsonify({
                    "verification": result,
                    "timestamp": self.timestamp()
                })
            except Exception as e:
                return jsonify({
                    "error": f"Verification failed: {str(e)}"
                }), 500
        
        @self.app.route('/api/capsules/<capsule_id>/download')
        @self.error_handler
        def download_capsule(capsule_id: str):
            """Download capsule file"""
            capsules_dir = self.base_dir / "capsules"
            capsule_file = capsules_dir / f"{capsule_id}.json"
            
            if not capsule_file.exists():
                abort(404)
            
            return send_file(
                capsule_file,
                as_attachment=True,
                download_name=f"{capsule_id}.json",
                mimetype='application/json'
            )
        
        # Audit endpoints
        @self.app.route('/api/audit/run')
        @self.error_handler
        def run_audit():
            """Run audit scan and return results"""
            anomalies, report = self.audit_scanner.run_audit()
            
            return jsonify({
                "audit_results": anomalies,
                "report_markdown": report,
                "timestamp": self.timestamp()
            })
        
        @self.app.route('/api/audit/reports')
        @self.error_handler
        def list_audit_reports():
            """List available audit reports"""
            audit_dir = self.base_dir / "audits"
            reports = []
            
            if audit_dir.exists():
                for report_file in audit_dir.glob("audit_report_*.md"):
                    try:
                        stat = report_file.stat()
                        reports.append({
                            "filename": report_file.name,
                            "path": str(report_file),
                            "size": stat.st_size,
                            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                    except Exception:
                        continue
            
            # Sort by creation time, newest first
            reports.sort(key=lambda x: x["created"], reverse=True)
            
            return jsonify({
                "reports": reports,
                "total": len(reports),
                "timestamp": self.timestamp()
            })
        
        @self.app.route('/api/audit/reports/<filename>')
        @self.error_handler
        def get_audit_report(filename: str):
            """Get specific audit report"""
            audit_dir = self.base_dir / "audits"
            report_file = audit_dir / filename
            
            if not report_file.exists() or not filename.startswith("audit_report_"):
                abort(404)
            
            with open(report_file, 'r') as f:
                report_content = f.read()
            
            return jsonify({
                "filename": filename,
                "content": report_content,
                "size": len(report_content),
                "timestamp": self.timestamp()
            })
        
        @self.app.route('/api/audit/reports/<filename>/download')
        @self.error_handler
        def download_audit_report(filename: str):
            """Download audit report file"""
            audit_dir = self.base_dir / "audits"
            report_file = audit_dir / filename
            
            if not report_file.exists() or not filename.startswith("audit_report_"):
                abort(404)
            
            return send_file(
                report_file,
                as_attachment=True,
                download_name=filename,
                mimetype='text/markdown'
            )
        
        # Visualization endpoints
        @self.app.route('/api/visualization/dags')
        @self.error_handler
        def list_visualizable_dags():
            """List DAGs available for visualization"""
            dags = self.visualizer.list_available_dags()
            return jsonify({
                "dags": dags,
                "total": len(dags),
                "timestamp": self.timestamp()
            })
        
        @self.app.route('/api/visualization/generate/<dag_id>')
        @self.error_handler
        def generate_visualization(dag_id: str):
            """Generate visualization for specific DAG"""
            result = self.visualizer.generate_ledger_visualization(dag_id)
            return jsonify({
                "visualization_result": result,
                "timestamp": self.timestamp()
            })
        
        @self.app.route('/api/visualization/svg/<dag_id>')
        @self.error_handler
        def get_dag_svg(dag_id: str):
            """Get SVG file for specific DAG"""
            svg_file = self.base_dir / "visualizations" / f"{dag_id}_mesh_links.svg"
            
            if not svg_file.exists():
                abort(404)
            
            return send_file(svg_file, mimetype='image/svg+xml')
        
        @self.app.route('/api/visualization/dot/<dag_id>')
        @self.error_handler
        def get_dag_dot(dag_id: str):
            """Get DOT file for specific DAG"""
            dot_file = self.base_dir / "dags" / f"{dag_id}_mesh_links.dot"
            
            if not dot_file.exists():
                abort(404)
            
            return send_file(dot_file, mimetype='text/plain')
        
        @self.app.route('/api/visualization/overview')
        @self.error_handler
        def get_system_overview():
            """Get system overview SVG"""
            svg_file = self.base_dir / "visualizations" / "epoch5_system_overview.svg"
            
            if not svg_file.exists():
                # Generate it if it doesn't exist
                result = self.visualizer.generate_system_overview_svg()
                if not result:
                    return jsonify({"error": "Failed to generate system overview"}), 500
            
            return send_file(svg_file, mimetype='image/svg+xml')
        
        # Meta-capsule endpoints
        @self.app.route('/api/meta-capsules')
        @self.error_handler
        def list_meta_capsules():
            """List all meta-capsules"""
            meta_capsules = self.meta_creator.list_meta_capsules()
            return jsonify({
                "meta_capsules": meta_capsules,
                "total": len(meta_capsules),
                "timestamp": self.timestamp()
            })
        
        @self.app.route('/api/meta-capsules/<meta_id>')
        @self.error_handler
        def get_meta_capsule(meta_id: str):
            """Get specific meta-capsule"""
            meta_dir = self.base_dir / "meta_capsules"
            meta_file = meta_dir / f"{meta_id}.json"
            
            if not meta_file.exists():
                abort(404)
            
            with open(meta_file, 'r') as f:
                meta_data = json.load(f)
            
            return jsonify({
                "meta_capsule": meta_data,
                "timestamp": self.timestamp()
            })
        
        @self.app.route('/api/meta-capsules/<meta_id>/verify')
        @self.error_handler
        def verify_meta_capsule(meta_id: str):
            """Verify meta-capsule integrity"""
            result = self.meta_creator.verify_meta_capsule(meta_id)
            return jsonify({
                "verification": result,
                "timestamp": self.timestamp()
            })
        
        # System status endpoint
        @self.app.route('/api/system/status')
        @self.error_handler
        def system_status():
            """Get comprehensive system status"""
            # Quick audit
            anomalies = self.audit_scanner.scan_for_anomalies()
            
            # Count resources
            ledger_file = self.base_dir / "ledger.log"
            ledger_entries = 0
            if ledger_file.exists():
                with open(ledger_file, 'r') as f:
                    ledger_entries = len([line for line in f if line.strip()])
            
            capsules_dir = self.base_dir / "capsules"
            capsule_count = len(list(capsules_dir.glob("*.json"))) if capsules_dir.exists() else 0
            
            meta_capsules_dir = self.base_dir / "meta_capsules"
            meta_count = len(list(meta_capsules_dir.glob("*.json"))) if meta_capsules_dir.exists() else 0
            
            dags = self.visualizer.list_available_dags()
            
            return jsonify({
                "status": "operational",
                "timestamp": self.timestamp(),
                "statistics": {
                    "ledger_entries": ledger_entries,
                    "capsules": capsule_count,
                    "meta_capsules": meta_count,
                    "dags": len(dags)
                },
                "health": anomalies.get("system_health", {}),
                "ledger_integrity": anomalies.get("ledger_integrity", {}).get("valid", False)
            })
    
    def parse_ledger_entry(self, line: str) -> Dict[str, str]:
        """Parse a ledger entry line into components"""
        entry = {}
        parts = line.strip().split("|")
        
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                entry[key.lower()] = value
        
        return entry
    
    def run(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        """Run the Flask API server"""
        if not FLASK_AVAILABLE:
            print("❌ Flask not available. Install with:")
            print("   pip install flask flask-cors")
            return
        
        print(f"🚀 Starting EdgeCapsule Cloud API server...")
        print(f"   URL: http://{host}:{port}")
        print(f"   Base directory: {self.base_dir}")
        print(f"   Debug mode: {debug}")
        print(f"   API Documentation: http://{host}:{port}/")
        
        self.app.run(host=host, port=port, debug=debug)

# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EdgeCapsule Cloud REST API Server")
    parser.add_argument("--base-dir", default="./archive/EPOCH5",
                       help="Base directory for EPOCH5 archive")
    parser.add_argument("--host", default="127.0.0.1", 
                       help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000,
                       help="Port to bind to")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug mode")
    
    args = parser.parse_args()
    
    if not FLASK_AVAILABLE:
        print("❌ Flask is required to run the REST API")
        print("Install with: pip install flask flask-cors")
        return
    
    api = EdgeCapsuleAPI(args.base_dir)
    api.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()