# EPOCH5 Template - Enhanced Integration System

A comprehensive tool for logging, agent management, policy enforcement, and secure execution of tasks with advanced provenance tracking.

## Overview

The EPOCH5 Template provides a complete ecosystem for:

- **Advanced Logging & Provenance**: Hash-chained ledger system with tamper-evident records
- **Agent Management**: Decentralized identifiers (DIDs), registry, and real-time monitoring  
- **Policy & Security**: Rule enforcement with quorum requirements and multi-signature approvals
- **DAG Management**: Directed Acyclic Graph execution with fault-tolerant mechanisms
- **Cycle Execution**: Budget control, latency tracking, and PBFT consensus
- **Data Integrity**: Capsule storage with Merkle tree proofs and ZIP archiving
- **Meta-Capsules**: Comprehensive system state capture and ledger integration

## Components

### 1. Core EPOCH5 System (`epoch5.sh`)
The foundational Bash script providing:
- Triple-pass capsule processing (Anchor → Amplify → Crown)
- Hash-chained provenance tracking
- Manifest generation and Unity Seal creation
- Configurable delays between passes

```bash
# Run EPOCH5 with custom delays
DELAY_HOURS_P1_P2=0 DELAY_HOURS_P2_P3=0 ./epoch5.sh
```

### 2. Enhanced Agent Management (`agent_management.py`)
**🔒 NEW: Cryptographic Identity & Security Features**

Advanced agent lifecycle management with robust security:

```python
# Create agent with cryptographic identity
python3 agent_management.py create --skills python cryptography security --type security-agent

# List active agents with enhanced formatting  
python3 agent_management.py list --active-only

# Verify agent integrity and cryptographic identity
python3 agent_management.py verify --did did:epoch5:agent:abc123

# Log anomalies with severity-based classification
python3 agent_management.py anomaly --did did:epoch5:agent:abc123 --type performance --severity high --details "High latency detected"

# Get comprehensive agent statistics
python3 agent_management.py stats --did did:epoch5:agent:abc123

# Update task statistics with history tracking
python3 agent_management.py update-stats --did did:epoch5:agent:abc123 --success --latency 2.5 --task-type security-scan

# Create provenance records for audit trails
python3 agent_management.py provenance --did did:epoch5:agent:abc123 --action "task_completed" --details '{"result": "success"}'
```

**Enhanced Security Features:**
- **RSA Cryptographic Identity**: Each agent gets 2048-bit RSA key pairs with secure storage
- **Message Signing & Verification**: Full cryptographic signing and verification capabilities  
- **Severity-Based Anomalies**: Four levels (low, medium, high, critical) with automatic deactivation
- **Thread Safety**: Mutex locks and atomic operations for concurrent access
- **Backup & Recovery**: Automatic registry backup with recovery mechanisms
- **Integrity Verification**: Hash validation and cryptographic identity verification
- **Provenance Tracking**: Signed audit trails for all agent actions
- **Task History**: Limited-buffer task tracking (1000 global, 100 per agent)

# Log heartbeat
python3 agent_management.py --heartbeat did:epoch5:agent:abc123

# Report anomaly
python3 agent_management.py --anomaly did:epoch5:agent:abc123 "timeout" "Task execution timeout"
```

**Features:**
- DID generation for agents
- Skill-based registry with reliability scoring
- Heartbeat monitoring and anomaly detection
- Performance metrics tracking

### 3. Policy & Grant System (`policy_grants.py`)
Enforces security through configurable policies:

```python
# Create quorum policy
python3 policy_grants.py create-policy "critical_ops" "quorum" '{"required_count": 3}'

# Create multi-signature policy  
python3 policy_grants.py create-policy "deploy" "multi_sig" '{"required_signatures": 2, "authorized_signers": ["signer1", "signer2", "signer3"]}'

# Create access grant
python3 policy_grants.py create-grant "data_access_1" "did:epoch5:agent:abc123" "database" "read" "write"

# Evaluate policy
python3 policy_grants.py evaluate "critical_ops" '{"approvers": ["user1", "user2", "user3"]}'
```

**Policy Types:**
- **Quorum**: Require N approvers
- **Multi-Signature**: Require M-of-N signatures
- **Rate Limiting**: Control request frequency
- **Skill Requirements**: Ensure agent capabilities
- **Trust Thresholds**: Minimum reliability scores

### 4. DAG Management (`dag_management.py`)
Creates and executes task graphs:

```python
# Create tasks definition file
cat > tasks.json <<EOF
{
  "description": "Data processing pipeline",
  "tasks": [
    {
      "task_id": "extract",
      "command": "extract_data --source db",
      "dependencies": [],
      "required_skills": ["database", "etl"]
    },
    {
      "task_id": "transform", 
      "command": "transform_data --input raw_data.csv",
      "dependencies": ["extract"],
      "required_skills": ["python", "data_processing"]
    },
    {
      "task_id": "load",
      "command": "load_data --target warehouse", 
      "dependencies": ["transform"],
      "required_skills": ["database", "etl"]
    }
  ]
}
EOF

# Create and execute DAG
python3 dag_management.py create "etl_pipeline" tasks.json
python3 dag_management.py execute "etl_pipeline"
python3 dag_management.py status "etl_pipeline"
```

**Features:**
- Cycle detection and DAG validation
- Mesh connectivity for fault tolerance
- Task dependency resolution
- Execution monitoring and logging

### 5. Cycle Execution (`cycle_execution.py`)
Manages execution cycles with SLA enforcement:

```python
# Create task assignments
cat > assignments.json <<EOF
{
  "assignments": [
    {"task_id": "process_batch_1", "agent_did": "did:epoch5:agent:worker1", "estimated_cost": 25.0},
    {"task_id": "process_batch_2", "agent_did": "did:epoch5:agent:worker2", "estimated_cost": 30.0}
  ],
  "sla_requirements": {
    "min_success_rate": 0.95,
    "max_failure_rate": 0.05,
    "max_retry_count": 3
  }
}
EOF

# Create and execute cycle
python3 cycle_execution.py create "batch_process_cycle" 100.0 300.0 assignments.json
python3 cycle_execution.py execute "batch_process_cycle" --validators validator1 validator2 validator3
python3 cycle_execution.py sla "batch_process_cycle"
```

**Features:**
- Budget and latency constraints
- PBFT consensus for decisions
- SLA monitoring and violation detection
- Resource usage tracking

### 6. Capsule & Metadata Management (`capsule_metadata.py`)
Provides data integrity and archiving:

```python
# Create data capsule
echo "Important data content" > data.txt
python3 capsule_metadata.py create-capsule "data_v1" data.txt --metadata '{"version": "1.0", "type": "dataset"}'

# Verify integrity
python3 capsule_metadata.py verify "data_v1"

# Create metadata linking capsules
python3 capsule_metadata.py create-metadata "batch_metadata" "data_v1" "processed_v1" --metadata '{"batch_id": "2024001"}'

# Create archive
python3 capsule_metadata.py create-archive "release_archive" "data_v1" "processed_v1"
```

**Features:**
- Merkle tree integrity proofs
- Content hash verification
- Metadata relationship tracking
- ZIP archive creation with hashing

### 7. Meta-Capsule System (`meta_capsule.py`)
Captures comprehensive system state:

```python
# Create meta-capsule of entire system
python3 meta_capsule.py create "system_state_2024_001" --description "Quarterly system snapshot"

# Verify meta-capsule
python3 meta_capsule.py verify "system_state_2024_001"

# View current system state
python3 meta_capsule.py state

# List all meta-capsules
python3 meta_capsule.py list
```

**Features:**
- Full system state capture
- Multi-system integration
- Provenance chain building
- Comprehensive archiving

### 8. Integration System (`integration.py`)
Unified orchestration interface:

```python
# Set up complete demo environment
python3 integration.py setup-demo

# Run integrated workflow
python3 integration.py run-workflow

# Check system status
python3 integration.py status

# Validate system integrity
python3 integration.py validate

# Quick operations (one-liners)
python3 integration.py oneliner system-snapshot
python3 integration.py oneliner quick-agent --params '{"skills": ["devops", "monitoring"]}'
```

## One-Liner Examples

The system is designed for both complex workflows and simple one-liner operations:

```bash
# Quick agent creation
python3 agent_management.py --create security audit compliance

# Instant policy check  
python3 policy_grants.py evaluate "trust_policy" '{"agent_reliability": 0.95}'

# Fast integrity verification
python3 capsule_metadata.py verify important_data

# System snapshot
python3 integration.py oneliner system-snapshot

# Complete workflow execution
python3 integration.py run-workflow
```

## File Structure

```
epoch5-template/
├── epoch5.sh                 # Core EPOCH5 Bash script
├── agent_management.py       # Enhanced Agent DID and registry system 🔒
├── policy_grants.py          # Policy enforcement and grants
├── dag_management.py         # DAG creation and execution
├── cycle_execution.py        # Cycle management with PBFT consensus
├── capsule_metadata.py       # Data capsules with Merkle proofs
├── meta_capsule.py          # System state meta-capsules
├── integration.py           # Unified orchestration system
├── README.md               # This documentation
└── archive/               # Runtime data directory
    └── EPOCH5/           # System data storage
        ├── agents/       # Enhanced agent registry and logs 🔒
        │   ├── keys/     # RSA key storage (secure permissions) 🔒
        │   ├── backups/  # Automatic registry backups 🔒
        │   ├── registry.json         # Agent registry with integrity hashes
        │   ├── anomalies.log         # Severity-based anomaly log
        │   ├── integrity.log         # Identity verification log 🔒
        │   ├── agent_management.log  # Enhanced system logging
        │   └── *_provenance.log      # Per-agent provenance trails 🔒
        ├── policies/     # Policy and grant definitions
        ├── dags/         # DAG definitions and execution logs
        ├── cycles/       # Cycle execution data
        ├── capsules/     # Data capsules and content
        ├── metadata/     # Metadata entries and relationships
        ├── archives/     # ZIP archives
        ├── meta_capsules/# Meta-capsule storage
        ├── manifests/    # EPOCH5 manifests
        ├── ledger.log    # Main provenance ledger
        └── heartbeat.log # System heartbeat log
```
🔒 = New enhanced security features

## Architecture Integration

All components integrate through the EPOCH5 foundation:

1. **Hash Chaining**: Every operation creates hash-chained entries in the ledger
2. **Timestamping**: Consistent ISO timestamp format across all components
3. **Provenance**: Complete audit trail from agents through meta-capsules
4. **Modularity**: Each component can run independently or as part of workflows
5. **Extensibility**: New components can easily integrate with existing patterns

## Security Features

**🔒 Enhanced Security (NEW):**
- **RSA Cryptographic Identity** for all agents with 2048-bit key pairs
- **Message Signing & Verification** with PSS padding and SHA-256
- **Severity-Based Anomaly Detection** with automatic deactivation
- **Thread-Safe Operations** with mutex locks and atomic writes
- **Backup & Recovery** with automatic file backup before critical operations
- **Provenance Tracking** with cryptographically signed audit trails
- **Integrity Verification** with hash validation and identity verification

**Existing Security Features:**
- **Multi-signature approval** for critical operations
- **Quorum requirements** for consensus decisions
- **Rate limiting** to prevent abuse
- **Skill-based access control** ensuring qualified agents
- **Trust thresholds** based on reliability scoring
- **Merkle tree proofs** for data integrity
- **PBFT consensus** for distributed agreement
- **Hash chain verification** for tamper detection

## Use Cases

### DevOps Pipeline
```bash
# Set up agents with different skills
python3 agent_management.py --create ci_cd docker kubernetes
python3 agent_management.py --create security audit compliance
python3 agent_management.py --create monitoring logging alerting

# Create deployment policy
python3 policy_grants.py create-policy "prod_deploy" "multi_sig" '{"required_signatures": 2, "authorized_signers": ["lead_dev", "devops_lead", "security_lead"]}'

# Execute deployment DAG with approval workflow
python3 dag_management.py create "prod_deployment" deployment_tasks.json
python3 dag_management.py execute "prod_deployment"
```

### Data Processing Workflow  
```bash
# Create data processing cycle
python3 cycle_execution.py create "monthly_etl" 500.0 1800.0 etl_assignments.json

# Execute with validation
python3 cycle_execution.py execute "monthly_etl" --validators node1 node2 node3

# Archive results with integrity proofs
python3 capsule_metadata.py create-capsule "monthly_data" processed_data.json
python3 capsule_metadata.py create-archive "monthly_archive" "monthly_data"
```

### Compliance & Audit
```bash
# Create comprehensive system snapshot
python3 meta_capsule.py create "compliance_snapshot_q1" --description "Q1 compliance audit snapshot"

# Validate all system components
python3 integration.py validate

# Generate audit trail
python3 integration.py status > audit_report.json
```

## Requirements

- **Python 3.7+** for all Python components
- **Bash 4.0+** for epoch5.sh
- **openssl** or **shasum** for hashing (usually pre-installed)
- **cryptography** library for RSA operations (`pip install cryptography`) 🔒
- **Optional**: NetworkX for advanced DAG validation (`pip install networkx`)

**🔒 New**: The enhanced agent management system requires the `cryptography` library for RSA key generation, signing, and verification capabilities.

## Getting Started

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd epoch5-template
   chmod +x epoch5.sh
   ```

2. **Initialize with demo data**:
   ```bash
   python3 integration.py setup-demo
   ```

3. **Run your first workflow**:
   ```bash
   python3 integration.py run-workflow
   ```

4. **Create system snapshot**:
   ```bash
   python3 integration.py oneliner system-snapshot
   ```

5. **Validate everything**:
   ```bash
   python3 integration.py validate
   ```

The EPOCH5 Template provides a complete foundation for secure, auditable, and scalable task execution with comprehensive provenance tracking.