# epoch5-template
One-shot Bash capsule for EPOCH 5 — sealed payloads, manifest logging, and Unity Seal for Eli's archive

## Python Scripts
This repository includes two Python scripts to enhance the automation process:

1. `mesh_builder.py`: Generates the mesh structure, agents, and associated files.
2. `mesh_exec_logger.py`: Logs execution data, calculates SLA, and creates a Merkle tree.

## Features

### mesh_builder.py
- Generates configurable mesh networks with nodes and connections
- Creates individual agent configurations with capabilities
- Supports environment-based configuration (COUNT, SEED, FOUNDER_NOTE, OUTDIR, MESH_SECRET)
- Outputs JSON files for mesh configuration, connections, and agent details
- Provides cryptographic signatures and content hashing

### mesh_exec_logger.py  
- Processes execution data from mesh operations
- Calculates SLA metrics including success rates and latency statistics
- Creates Merkle trees for data integrity verification
- Generates comprehensive execution logs and archives
- Provides compliance reporting and audit trails

## Configuration

The scripts can be configured using environment variables:

- `COUNT`: Number of nodes to generate (default: 100)
- `SEED`: Seed for reproducible mesh generation (default: 'TrueNorth')
- `FOUNDER_NOTE`: Note to include in generated files (default: 'Ledger first. For Eli.')
- `OUTDIR`: Output directory for generated files (default: './ledger')
- `MESH_SECRET`: Secret key for mesh signatures (default: 'default_mesh_secret')

## Usage

### Running the Scripts Individually

```bash
# Run mesh builder
python3 mesh_builder.py

# Run execution logger
python3 mesh_exec_logger.py
```

### Running the Complete Workflow

Run the entire workflow with the Bash script:

```bash
./epoch5.sh
```

This will execute both Python scripts in sequence and provide a unified output.

### Example with Custom Configuration

```bash
# Set environment variables
export COUNT=50
export SEED=CustomSeed
export FOUNDER_NOTE="Custom mesh build"
export OUTDIR=./custom_output

# Run the workflow
./epoch5.sh
```

## Output Files

The scripts generate several types of files in the output directory:

- `mesh_config_*.json`: Main mesh configuration
- `connections_*.json`: Node connection mappings  
- `agents/`: Directory containing individual agent configurations
- `execution_log_*.json`: Execution data and SLA metrics
- `merkle_tree_*.json`: Merkle tree structure for data integrity
- `execution_archive_*.zip`: Compressed archive of execution files
- `mesh_summary_*.json`: Summary of mesh build process
- `exec_summary_*.json`: Summary of execution logging
- `build_log.txt`: Combined build and execution log

## Requirements

- Python 3.6+
- Bash shell
- Standard Unix utilities (date, mkdir, etc.)

## Architecture

The mesh builder creates a network of interconnected nodes with various capabilities:
- Each node has 1-3 capabilities from: export.report, blackboard.merge, data.sync, crypto.verify, mesh.route
- Nodes are connected in a web pattern for redundancy
- All data is cryptographically signed and hashed for integrity
- Execution logger processes the mesh operations and provides compliance reporting