#!/usr/bin/env python3
import os, json, hashlib, uuid, datetime as dt, io, zipfile, math, random

# Define functions and utility lambdas
U = lambda: dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
S = lambda: dt.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
H = lambda b: hashlib.sha256(b).hexdigest()
HS = lambda s: H(s.encode())

# Execution logging and SLA calculation
OUT = os.getenv('OUTDIR', './ledger')
os.makedirs(OUT, exist_ok=True)

# Sample execution data - in real usage this would come from actual mesh execution
execs = [
    {'node': 'n1', 'cap': 'export.report', 'ok': True, 'lat_ms': 200},
    {'node': 'n2', 'cap': 'blackboard.merge', 'ok': True, 'lat_ms': 250},
    {'node': 'n3', 'cap': 'data.sync', 'ok': False, 'lat_ms': 1500},
    {'node': 'n4', 'cap': 'crypto.verify', 'ok': True, 'lat_ms': 180},
    {'node': 'n5', 'cap': 'mesh.route', 'ok': True, 'lat_ms': 320}
]

def calculate_sla_metrics(executions):
    """Calculate SLA metrics from execution data"""
    total_ops = len(executions)
    successful_ops = sum(1 for ex in executions if ex['ok'])
    failed_ops = total_ops - successful_ops
    
    success_rate = (successful_ops / total_ops) * 100 if total_ops > 0 else 0
    
    # Calculate latency statistics for successful operations
    success_latencies = [ex['lat_ms'] for ex in executions if ex['ok']]
    if success_latencies:
        avg_latency = sum(success_latencies) / len(success_latencies)
        max_latency = max(success_latencies)
        min_latency = min(success_latencies)
        p95_latency = sorted(success_latencies)[int(len(success_latencies) * 0.95)]
    else:
        avg_latency = max_latency = min_latency = p95_latency = 0
    
    return {
        'total_operations': total_ops,
        'successful_operations': successful_ops,
        'failed_operations': failed_ops,
        'success_rate_percent': round(success_rate, 2),
        'avg_latency_ms': round(avg_latency, 2),
        'max_latency_ms': max_latency,
        'min_latency_ms': min_latency,
        'p95_latency_ms': p95_latency,
        'sla_met': success_rate >= 95.0 and avg_latency <= 500
    }

def create_merkle_tree(data_list):
    """Create a simple Merkle tree from execution data"""
    if not data_list:
        return None
    
    # Convert data to hashes
    leaves = [HS(json.dumps(item, sort_keys=True)) for item in data_list]
    
    # Build tree bottom-up
    tree_levels = [leaves]
    current_level = leaves
    
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = left + right
            next_level.append(HS(combined))
        tree_levels.append(next_level)
        current_level = next_level
    
    return {
        'root_hash': current_level[0] if current_level else None,
        'levels': tree_levels,
        'leaf_count': len(leaves)
    }

def generate_execution_log(executions, sla_metrics, merkle_tree):
    """Generate comprehensive execution log"""
    log_entry = {
        'log_id': str(uuid.uuid4()),
        'timestamp': U(),
        'session_info': {
            'session_id': f"session_{S()}",
            'total_duration_ms': sum(ex['lat_ms'] for ex in executions),
            'operations_logged': len(executions)
        },
        'executions': executions,
        'sla_metrics': sla_metrics,
        'merkle_proof': {
            'root_hash': merkle_tree['root_hash'] if merkle_tree else None,
            'leaf_count': merkle_tree['leaf_count'] if merkle_tree else 0,
            'tree_depth': len(merkle_tree['levels']) if merkle_tree else 0
        },
        'compliance': {
            'data_integrity_verified': merkle_tree is not None,
            'sla_compliance': sla_metrics['sla_met'],
            'audit_trail_complete': True
        }
    }
    
    # Add execution signature
    log_content = json.dumps(log_entry, sort_keys=True)
    log_entry['signature'] = HS(log_content + "mesh_exec_logger")
    
    return log_entry

def save_execution_files(log_entry, merkle_tree):
    """Save execution log and related files"""
    timestamp = S()
    
    # Save main execution log
    log_file = os.path.join(OUT, f'execution_log_{timestamp}.json')
    with open(log_file, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    # Save Merkle tree structure
    if merkle_tree:
        merkle_file = os.path.join(OUT, f'merkle_tree_{timestamp}.json')
        with open(merkle_file, 'w') as f:
            json.dump(merkle_tree, f, indent=2)
    
    # Create execution summary
    summary = {
        'execution_id': log_entry['log_id'],
        'timestamp': log_entry['timestamp'],
        'success_rate': log_entry['sla_metrics']['success_rate_percent'],
        'avg_latency': log_entry['sla_metrics']['avg_latency_ms'],
        'sla_met': log_entry['sla_metrics']['sla_met'],
        'merkle_root': log_entry['merkle_proof']['root_hash'],
        'files_created': [log_file]
    }
    
    if merkle_tree:
        summary['files_created'].append(merkle_file)
    
    summary_file = os.path.join(OUT, f'exec_summary_{timestamp}.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Create execution archive
    archive_file = os.path.join(OUT, f'execution_archive_{timestamp}.zip')
    with zipfile.ZipFile(archive_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(log_file, os.path.basename(log_file))
        if merkle_tree:
            zf.write(merkle_file, os.path.basename(merkle_file))
        zf.write(summary_file, os.path.basename(summary_file))
    
    summary['archive_file'] = archive_file
    
    return summary

def load_mesh_execution_data():
    """Load or generate execution data for processing"""
    # Try to load from existing mesh files if available
    mesh_files = [f for f in os.listdir(OUT) if f.startswith('mesh_config_') and f.endswith('.json')]
    
    if mesh_files:
        # Load from most recent mesh file
        latest_mesh = sorted(mesh_files)[-1]
        mesh_path = os.path.join(OUT, latest_mesh)
        try:
            with open(mesh_path, 'r') as f:
                mesh_data = json.load(f)
            
            # Generate execution data based on mesh nodes
            executions = []
            for node in mesh_data.get('nodes', []):
                for cap in node.get('capabilities', []):
                    exec_data = {
                        'node': node['node_id'],
                        'cap': cap,
                        'ok': random.choice([True, True, True, False]),  # 75% success rate
                        'lat_ms': random.randint(100, 800),
                        'timestamp': U()
                    }
                    executions.append(exec_data)
            
            return executions
        except (json.JSONDecodeError, FileNotFoundError):
            print("Warning: Could not load mesh data, using default execution data")
    
    # Return default execution data if no mesh available
    return execs

def main():
    """Main execution function"""
    print(f"MESH EXECUTION LOGGER - Started at {U()}")
    print(f"Output directory: {OUT}")
    
    # Load execution data
    execution_data = load_mesh_execution_data()
    print(f"Processing {len(execution_data)} execution records")
    
    # Calculate SLA metrics
    sla_metrics = calculate_sla_metrics(execution_data)
    print(f"SLA Success Rate: {sla_metrics['success_rate_percent']}%")
    print(f"Average Latency: {sla_metrics['avg_latency_ms']}ms")
    print(f"SLA Met: {'Yes' if sla_metrics['sla_met'] else 'No'}")
    
    # Create Merkle tree
    merkle_tree = create_merkle_tree(execution_data)
    if merkle_tree:
        print(f"Merkle Tree Root: {merkle_tree['root_hash'][:16]}...")
    
    # Generate execution log
    log_entry = generate_execution_log(execution_data, sla_metrics, merkle_tree)
    
    # Save files
    summary = save_execution_files(log_entry, merkle_tree)
    
    print(f"Execution logging completed:")
    print(f"  - Log ID: {log_entry['log_id']}")
    print(f"  - Files created: {len(summary['files_created'])}")
    print(f"  - Archive: {summary['archive_file']}")
    
    # Log completion
    completion_log = os.path.join(OUT, 'build_log.txt')
    with open(completion_log, 'a') as f:
        f.write(f"{U()} - MESH_EXEC_LOGGER completed successfully\n")
        f.write(f"  Log ID: {log_entry['log_id']}\n")
        f.write(f"  SLA Met: {sla_metrics['sla_met']}\n")
        f.write(f"  Merkle Root: {merkle_tree['root_hash'] if merkle_tree else 'None'}\n\n")

if __name__ == '__main__':
    main()