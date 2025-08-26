#!/usr/bin/env python3
"""
SVG Ledger Visualization System for EdgeCapsule Cloud Mesh
Converts mesh_links.dot files and DAG mesh data into SVG graphs for visual audits
Integrates with EPOCH5 DAG management and mesh connectivity systems
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set

class SVGLedgerVisualizer:
    def __init__(self, base_dir: str = "./archive/EPOCH5"):
        self.base_dir = Path(base_dir)
        self.dags_dir = self.base_dir / "dags"
        self.visualizations_dir = self.base_dir / "visualizations"
        self.visualizations_dir.mkdir(parents=True, exist_ok=True)
        
    def timestamp(self) -> str:
        """Generate ISO timestamp consistent with EPOCH5"""
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def check_graphviz_installed(self) -> bool:
        """Check if Graphviz dot command is available"""
        try:
            result = subprocess.run(['dot', '-V'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def load_dag_data(self, dag_id: str = None) -> Dict[str, Any]:
        """Load DAG data from JSON file"""
        dags_file = self.dags_dir / "dags.json"
        
        if not dags_file.exists():
            return {}
        
        try:
            with open(dags_file, 'r') as f:
                dags_data = json.load(f)
            
            if dag_id:
                return dags_data.get("dags", {}).get(dag_id, {})
            else:
                return dags_data.get("dags", {})
                
        except Exception as e:
            print(f"Error loading DAG data: {e}")
            return {}
    
    def generate_mesh_dot_content(self, dag_data: Dict[str, Any]) -> str:
        """Generate Graphviz DOT content from DAG mesh data"""
        dag_id = dag_data.get("dag_id", "unknown")
        mesh_nodes = dag_data.get("mesh_nodes", {})
        tasks = dag_data.get("tasks", {})
        
        # Start DOT content
        dot_lines = [
            f'digraph "{dag_id}_mesh" {{',
            '  rankdir=TB;',
            '  node [shape=box, style=filled];',
            '  edge [fontsize=10];',
            '',
            '  // Node definitions with fault tolerance levels'
        ]
        
        # Add nodes with styling based on fault tolerance
        for task_id, mesh_info in mesh_nodes.items():
            task_info = tasks.get(task_id, {})
            fault_level = mesh_info.get("fault_tolerance_level", 1)
            
            # Color nodes based on fault tolerance level
            if fault_level >= 3:
                color = "lightgreen"
                style = "filled,bold"
            elif fault_level == 2:
                color = "lightblue"
                style = "filled"
            else:
                color = "lightyellow"
                style = "filled"
            
            # Create node label with information
            label = f"{task_id}\\nFT: {fault_level}"
            if task_info.get("status"):
                label += f"\\nStatus: {task_info['status']}"
            
            dot_lines.append(f'  "{task_id}" [label="{label}", fillcolor="{color}", style="{style}"];')
        
        dot_lines.extend(['', '  // Primary connections (dependencies)'])
        
        # Add primary connections (direct dependencies)
        for task_id, mesh_info in mesh_nodes.items():
            primary_connections = mesh_info.get("primary_connections", [])
            for dep in primary_connections:
                dot_lines.append(f'  "{dep}" -> "{task_id}" [style=bold, color=blue, label="primary"];')
        
        dot_lines.extend(['', '  // Secondary connections (fault tolerance)'])
        
        # Add secondary connections (fault tolerance mesh)
        for task_id, mesh_info in mesh_nodes.items():
            secondary_connections = mesh_info.get("secondary_connections", [])
            for sec_conn in secondary_connections:
                dot_lines.append(f'  "{sec_conn}" -> "{task_id}" [style=dashed, color=gray, label="mesh"];')
        
        # Add legend
        dot_lines.extend([
            '',
            '  // Legend',
            '  subgraph cluster_legend {',
            '    label="EdgeCapsule Cloud Mesh Legend";',
            '    style=filled;',
            '    fillcolor=lightgray;',
            '    node [shape=plaintext];',
            '    legend [label=<<TABLE BORDER="0">',
            '      <TR><TD ALIGN="LEFT"><B>Fault Tolerance Levels:</B></TD></TR>',
            '      <TR><TD ALIGN="LEFT">• High (3+): Green - Multiple backup paths</TD></TR>',
            '      <TR><TD ALIGN="LEFT">• Medium (2): Blue - Some redundancy</TD></TR>',
            '      <TR><TD ALIGN="LEFT">• Low (1): Yellow - Limited backup</TD></TR>',
            '      <TR><TD ALIGN="LEFT"><B>Connection Types:</B></TD></TR>',
            '      <TR><TD ALIGN="LEFT">• Blue solid: Primary dependencies</TD></TR>',
            '      <TR><TD ALIGN="LEFT">• Gray dashed: Mesh fault tolerance</TD></TR>',
            '    </TABLE>>];',
            '  }',
            '}'
        ])
        
        return "\n".join(dot_lines)
    
    def create_mesh_dot_file(self, dag_id: str) -> Optional[Path]:
        """Create mesh_links.dot file for a specific DAG"""
        dag_data = self.load_dag_data(dag_id)
        
        if not dag_data:
            print(f"No DAG data found for: {dag_id}")
            return None
        
        dot_content = self.generate_mesh_dot_content(dag_data)
        dot_file = self.dags_dir / f"{dag_id}_mesh_links.dot"
        
        try:
            with open(dot_file, 'w') as f:
                f.write(dot_content)
            
            print(f"✅ Generated DOT file: {dot_file}")
            return dot_file
            
        except Exception as e:
            print(f"Error creating DOT file: {e}")
            return None
    
    def dot_to_svg(self, dot_file: Path, output_file: Path = None) -> Optional[Path]:
        """Convert DOT file to SVG using Graphviz"""
        if not self.check_graphviz_installed():
            print("❌ Graphviz not installed. Please install graphviz to generate SVG files.")
            print("   Ubuntu/Debian: sudo apt install graphviz")
            print("   macOS: brew install graphviz")
            print("   Windows: Download from https://graphviz.org/download/")
            return None
        
        if not dot_file.exists():
            print(f"DOT file not found: {dot_file}")
            return None
        
        # Determine output file
        if output_file is None:
            output_file = self.visualizations_dir / f"{dot_file.stem}.svg"
        
        try:
            # Run Graphviz dot command
            result = subprocess.run([
                'dot', '-Tsvg', str(dot_file), '-o', str(output_file)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ Generated SVG: {output_file}")
                return output_file
            else:
                print(f"❌ Graphviz error: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Graphviz command timed out")
            return None
        except Exception as e:
            print(f"❌ Error running Graphviz: {e}")
            return None
    
    def generate_ledger_visualization(self, dag_id: str) -> Dict[str, Any]:
        """Generate complete visualization package for a DAG"""
        result = {
            "dag_id": dag_id,
            "timestamp": self.timestamp(),
            "dot_file": None,
            "svg_file": None,
            "status": "failed",
            "error": None
        }
        
        try:
            # Load DAG data
            dag_data = self.load_dag_data(dag_id)
            if not dag_data:
                result["error"] = f"DAG '{dag_id}' not found"
                return result
            
            # Create DOT file
            dot_file = self.create_mesh_dot_file(dag_id)
            if not dot_file:
                result["error"] = "Failed to create DOT file"
                return result
            
            result["dot_file"] = str(dot_file)
            
            # Generate SVG
            svg_file = self.dot_to_svg(dot_file)
            if svg_file:
                result["svg_file"] = str(svg_file)
                result["status"] = "success"
            else:
                result["status"] = "partial"
                result["error"] = "SVG generation failed (DOT file created)"
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def create_ledger_overview_dot(self) -> str:
        """Create a DOT visualization of the entire ledger system"""
        ledger_file = self.base_dir / "ledger.log"
        meta_ledger = self.base_dir / "meta_capsules" / "meta_ledger.log"
        
        dot_lines = [
            'digraph "ledger_overview" {',
            '  rankdir=TB;',
            '  node [shape=box, style=filled];',
            '  edge [fontsize=10];',
            '',
            '  // System components'
        ]
        
        # Add main components
        components = [
            ('ledger', 'Main Ledger\\nHash Chain', 'lightblue'),
            ('meta_ledger', 'Meta-Capsule\\nLedger', 'lightgreen'),
            ('capsules', 'Capsule\\nStorage', 'lightyellow'),
            ('agents', 'Agent\\nRegistry', 'lightcoral'),
            ('dags', 'DAG\\nExecution', 'lightpink')
        ]
        
        for comp_id, label, color in components:
            dot_lines.append(f'  "{comp_id}" [label="{label}", fillcolor="{color}"];')
        
        # Add relationships
        dot_lines.extend([
            '',
            '  // System relationships',
            '  "meta_ledger" -> "ledger" [label="updates"];',
            '  "capsules" -> "ledger" [label="records"];',
            '  "agents" -> "ledger" [label="logs"];',
            '  "dags" -> "ledger" [label="execution\\ntraces"];',
            '  "dags" -> "agents" [label="assigns\\ntasks"];',
            '}'
        ])
        
        return "\n".join(dot_lines)
    
    def generate_system_overview_svg(self) -> Optional[Path]:
        """Generate SVG overview of the entire EPOCH5 system"""
        dot_content = self.create_ledger_overview_dot()
        
        # Create temporary DOT file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
            f.write(dot_content)
            dot_file = Path(f.name)
        
        try:
            svg_file = self.visualizations_dir / "epoch5_system_overview.svg"
            result = self.dot_to_svg(dot_file, svg_file)
            
            # Cleanup temporary file
            os.unlink(dot_file)
            
            return result
            
        except Exception as e:
            print(f"Error generating system overview: {e}")
            os.unlink(dot_file)  # Cleanup on error
            return None
    
    def list_available_dags(self) -> List[str]:
        """List all available DAGs for visualization"""
        dags_data = self.load_dag_data()
        return list(dags_data.keys())
    
    def generate_all_visualizations(self) -> Dict[str, Any]:
        """Generate visualizations for all available DAGs"""
        results = {
            "timestamp": self.timestamp(),
            "system_overview": None,
            "dag_visualizations": {},
            "summary": {
                "total_dags": 0,
                "successful": 0,
                "failed": 0
            }
        }
        
        # Generate system overview
        print("🎨 Generating system overview...")
        system_svg = self.generate_system_overview_svg()
        if system_svg:
            results["system_overview"] = str(system_svg)
        
        # Generate DAG visualizations
        available_dags = self.list_available_dags()
        results["summary"]["total_dags"] = len(available_dags)
        
        for dag_id in available_dags:
            print(f"🎨 Generating visualization for DAG: {dag_id}")
            dag_result = self.generate_ledger_visualization(dag_id)
            results["dag_visualizations"][dag_id] = dag_result
            
            if dag_result["status"] == "success":
                results["summary"]["successful"] += 1
            else:
                results["summary"]["failed"] += 1
        
        return results

# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EdgeCapsule Cloud SVG Ledger Visualizer")
    parser.add_argument("--base-dir", default="./archive/EPOCH5",
                       help="Base directory for EPOCH5 archive")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate visualization for specific DAG")
    generate_parser.add_argument("dag_id", help="DAG identifier")
    
    # List command  
    list_parser = subparsers.add_parser("list", help="List available DAGs")
    
    # All command
    all_parser = subparsers.add_parser("all", help="Generate visualizations for all DAGs")
    
    # Overview command
    overview_parser = subparsers.add_parser("overview", help="Generate system overview")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check if Graphviz is installed")
    
    args = parser.parse_args()
    visualizer = SVGLedgerVisualizer(args.base_dir)
    
    if args.command == "generate":
        result = visualizer.generate_ledger_visualization(args.dag_id)
        print(f"\nVisualization Result:")
        print(f"  Status: {result['status']}")
        if result.get("dot_file"):
            print(f"  DOT file: {result['dot_file']}")
        if result.get("svg_file"):
            print(f"  SVG file: {result['svg_file']}")
        if result.get("error"):
            print(f"  Error: {result['error']}")
    
    elif args.command == "list":
        dags = visualizer.list_available_dags()
        print(f"Available DAGs ({len(dags)}):")
        for dag_id in dags:
            print(f"  - {dag_id}")
    
    elif args.command == "all":
        results = visualizer.generate_all_visualizations()
        print(f"\nGenerated visualizations:")
        print(f"  Total DAGs: {results['summary']['total_dags']}")
        print(f"  Successful: {results['summary']['successful']}")
        print(f"  Failed: {results['summary']['failed']}")
        
        if results.get("system_overview"):
            print(f"  System overview: {results['system_overview']}")
    
    elif args.command == "overview":
        result = visualizer.generate_system_overview_svg()
        if result:
            print(f"System overview generated: {result}")
        else:
            print("Failed to generate system overview")
    
    elif args.command == "check":
        if visualizer.check_graphviz_installed():
            print("✅ Graphviz is installed and available")
        else:
            print("❌ Graphviz is not installed")
            print("Install with:")
            print("  Ubuntu/Debian: sudo apt install graphviz")
            print("  macOS: brew install graphviz") 
            print("  Windows: Download from https://graphviz.org/download/")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()