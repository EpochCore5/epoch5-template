#!/usr/bin/env python3
import os, json, hashlib, hmac, uuid, datetime as dt, io, base64, random

# Define functions and utility lambdas
U = lambda: dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
S = lambda: dt.datetime.utcnow().strftime('%Y%m%d_%H%M%S')
H = lambda b: hashlib.sha256(b).hexdigest()
HS = lambda s: H(s.encode())

# Load configuration from environment variables
CFG = {k: os.getenv(k) for k in ['COUNT', 'SEED', 'FOUNDER_NOTE', 'OUTDIR', 'MESH_SECRET']}
COUNT = int(CFG['COUNT'] or 100)
SEED = CFG['SEED'] or 'TrueNorth'
NOTE = CFG['FOUNDER_NOTE'] or 'Ledger first. For Eli.'
OUT = CFG['OUTDIR'] or './ledger'
SECRET = CFG['MESH_SECRET'] or 'default_mesh_secret'

os.makedirs(OUT, exist_ok=True)

# Mesh logic and outputs
def generate_node_id(index, seed):
    """Generate a unique node ID based on index and seed"""
    combined = f"{seed}_{index}"
    return f"node_{HS(combined)[:8]}"

def generate_agent_config(node_id, capabilities):
    """Generate agent configuration for a node"""
    return {
        'node_id': node_id,
        'capabilities': capabilities,
        'created_at': U(),
        'status': 'active',
        'metadata': {
            'seed': SEED,
            'founder_note': NOTE
        }
    }

def create_mesh_structure():
    """Create the mesh structure with nodes and connections"""
    print(f"Building mesh with {COUNT} nodes using seed '{SEED}'")
    
    # Use a local Random instance for reproducible builds
    rng = random.Random(SEED)
    
    mesh_data = {
        'mesh_id': f"mesh_{HS(SEED + str(COUNT))[:12]}",
        'created_at': U(),
        'node_count': COUNT,
        'seed': SEED,
        'founder_note': NOTE,
        'nodes': [],
        'connections': []
    }
    
    # Generate nodes
    capabilities_pool = ['export.report', 'blackboard.merge', 'data.sync', 'crypto.verify', 'mesh.route']
    
    for i in range(COUNT):
        node_id = generate_node_id(i, SEED)
        # Assign 1-3 random capabilities per node
        node_caps = random.sample(capabilities_pool, random.randint(1, 3))
        
        agent_config = generate_agent_config(node_id, node_caps)
        mesh_data['nodes'].append(agent_config)
        
        # Create connections to other nodes (each node connects to 2-4 others)
        if i > 0:  # Don't connect the first node to itself
            num_connections = min(random.randint(2, 4), i)
            connected_indices = random.sample(range(i), num_connections)
            
            for conn_idx in connected_indices:
                connection = {
                    'from_node': node_id,
                    'to_node': generate_node_id(conn_idx, SEED),
                    'weight': random.uniform(0.1, 1.0),
                    'established_at': U()
                }
                mesh_data['connections'].append(connection)
    
    # Generate mesh signature
    mesh_content = json.dumps(mesh_data, sort_keys=True)
    mesh_hash = HS(mesh_content)
    signature = hmac.new(SECRET.encode(), mesh_hash.encode(), hashlib.sha256).hexdigest()
    
    mesh_data['signature'] = signature
    mesh_data['content_hash'] = mesh_hash
    
    return mesh_data

def save_mesh_files(mesh_data):
    """Save mesh data to various output files"""
    timestamp = S()
    
    # Save main mesh configuration
    mesh_file = os.path.join(OUT, f'mesh_config_{timestamp}.json')
    with open(mesh_file, 'w') as f:
        json.dump(mesh_data, f, indent=2)
    
    # Save individual agent configs
    agents_dir = os.path.join(OUT, 'agents')
    os.makedirs(agents_dir, exist_ok=True)
    
    for node in mesh_data['nodes']:
        agent_file = os.path.join(agents_dir, f"{node['node_id']}.json")
        with open(agent_file, 'w') as f:
            json.dump(node, f, indent=2)
    
    # Save connections map
    connections_file = os.path.join(OUT, f'connections_{timestamp}.json')
    with open(connections_file, 'w') as f:
        json.dump(mesh_data['connections'], f, indent=2)
    
    # Save summary report
    summary = {
        'mesh_id': mesh_data['mesh_id'],
        'build_timestamp': U(),
        'node_count': len(mesh_data['nodes']),
        'connection_count': len(mesh_data['connections']),
        'capabilities_used': list(set([cap for node in mesh_data['nodes'] for cap in node['capabilities']])),
        'content_hash': mesh_data['content_hash'],
        'signature': mesh_data['signature'],
        'files_generated': {
            'mesh_config': mesh_file,
            'connections': connections_file,
            'agents_dir': agents_dir
        }
    }
    
    summary_file = os.path.join(OUT, f'mesh_summary_{timestamp}.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary

def main():
    """Main execution function"""
    print(f"MESH BUILDER - Started at {U()}")
    print(f"Configuration: COUNT={COUNT}, SEED={SEED}, OUT={OUT}")
    
    # Create mesh structure
    mesh_data = create_mesh_structure()
    
    # Save all files
    summary = save_mesh_files(mesh_data)
    
    print(f"Mesh built successfully:")
    print(f"  - Mesh ID: {mesh_data['mesh_id']}")
    print(f"  - Nodes: {len(mesh_data['nodes'])}")
    print(f"  - Connections: {len(mesh_data['connections'])}")
    print(f"  - Output directory: {OUT}")
    print(f"  - Summary saved to: {summary['files_generated']}")
    
    # Log completion
    log_file = os.path.join(OUT, 'build_log.txt')
    with open(log_file, 'a') as f:
        f.write(f"{U()} - MESH_BUILDER completed successfully\n")
        f.write(f"  Mesh ID: {mesh_data['mesh_id']}\n")
        f.write(f"  Hash: {mesh_data['content_hash']}\n\n")

if __name__ == '__main__':
    main()