# EPOCH5 Template - Core Ledger System

One-shot Bash capsule for EPOCH 5 — sealed payloads, manifest logging, and Unity Seal.

## Overview

The EPOCH5 Template provides a focused system for:

- **Core EPOCH5 System**: Triple-pass capsule processing with hash-chained provenance
- **Manifest Logging**: Automated manifest generation with timestamped records
- **Unity Seal**: Final sealing and archiving for complete provenance chains
- **Data Integrity**: Capsule storage with Merkle tree proofs and hash verification
- **System State Capture**: Meta-capsules for comprehensive system snapshots

## Components

### 1. Core EPOCH5 System (`epoch5.sh`)
The foundational Bash script providing triple-pass capsule processing:

```bash
# Run EPOCH5 with custom delays (default: 6 hours between passes)
DELAY_HOURS_P1_P2=0 DELAY_HOURS_P2_P3=0 ./epoch5.sh

# Use custom payload content
P1_PAYLOAD="Your Pass 1 content" P2_PAYLOAD="Your Pass 2 content" P3_PAYLOAD="Your Pass 3 content" ./epoch5.sh
```

**Features:**
- **Triple-Pass Processing**: Anchor → Amplify → Crown structure
- **Hash-Chained Provenance**: Each pass builds on the previous hash
- **Manifest Generation**: Automated manifest files with metadata
- **Unity Seal Creation**: Final seal with completion status
- **Configurable Delays**: Customizable timing between passes

**Generated Files:**
- `./archive/EPOCH5/manifests/E5-P1_manifest.txt` - Pass 1 manifest
- `./archive/EPOCH5/manifests/E5-P2_manifest.txt` - Pass 2 manifest
- `./archive/EPOCH5/manifests/E5-P3_manifest.txt` - Pass 3 manifest
- `./archive/EPOCH5/ledger.log` - Complete provenance ledger
- `./archive/EPOCH5/unity_seal.txt` - Final unity seal
- `./archive/EPOCH5/heartbeat.log` - System heartbeat log

### 2. Capsule & Metadata Management (`capsule_metadata.py`)
Data integrity and archiving with Merkle tree proofs:

```bash
# Create data capsule with integrity protection
echo "Important data content" > data.txt
python3 capsule_metadata.py create-capsule "data_v1" data.txt --metadata '{"version": "1.0", "type": "dataset"}'

# Verify data integrity
python3 capsule_metadata.py verify "data_v1"

# Create metadata linking capsules
python3 capsule_metadata.py create-metadata "batch_metadata" "data_v1" "processed_v1" --metadata '{"batch_id": "2024001"}'

# Create archive with multiple capsules
python3 capsule_metadata.py create-archive "release_archive" "data_v1" "processed_v1"

# List all capsules and archives
python3 capsule_metadata.py list-capsules
python3 capsule_metadata.py list-archives
```

**Features:**
- **Merkle Tree Integrity**: Cryptographic proofs for data blocks
- **Content Hash Verification**: SHA256 hashing for tamper detection
- **Metadata Relationships**: Link capsules with structured metadata
- **ZIP Archive Creation**: Secure packaging with integrity hashes
- **Block-Level Proofs**: Verify individual data blocks within capsules

### 3. Meta-Capsule System (`meta_capsule.py`)
Comprehensive system state capture and archiving:

```bash
# Create complete system snapshot
python3 meta_capsule.py create "system_state_2024_001" --description "Quarterly system snapshot"

# Verify meta-capsule integrity
python3 meta_capsule.py verify "system_state_2024_001"

# View current system state
python3 meta_capsule.py state

# List all meta-capsules
python3 meta_capsule.py list
```

**Features:**
- **Complete System State**: Captures ledger, manifests, capsules, and Unity Seal
- **Provenance Chain Building**: Links all system operations in chronological order
- **System Archive Creation**: ZIP packaging of entire system state
- **Integrity Verification**: Multi-level validation of captured data
- **Ledger Integration**: Updates main ledger with meta-capsule records

## Architecture

The system is built around core EPOCH5 principles:

1. **Hash Chaining**: Every operation creates hash-chained entries in the ledger
2. **Timestamping**: Consistent ISO timestamp format across all components
3. **Provenance**: Complete audit trail from initial capsule through Unity Seal
4. **Modularity**: Each component operates independently while maintaining integration
5. **Integrity**: Cryptographic verification at every level

## Security Features

- **SHA256 Hashing**: Cryptographic integrity for all data and metadata
- **Merkle Tree Proofs**: Mathematical verification of data integrity
- **Hash Chain Verification**: Tamper-evident provenance tracking
- **Unity Seal**: Final cryptographic seal ensuring completeness
- **Archive Integrity**: ZIP-level checksums and verification

## File Structure

```
epoch5-template/
├── epoch5.sh                 # Core EPOCH5 triple-pass system
├── capsule_metadata.py       # Data capsules with Merkle tree proofs
├── meta_capsule.py          # System state meta-capsules and archiving
├── README.md               # This documentation
└── archive/               # Runtime data directory
    └── EPOCH5/           # System data storage
        ├── manifests/    # Pass manifests (E5-P1, E5-P2, E5-P3)
        ├── capsules/     # Data capsules and content
        ├── metadata/     # Metadata entries and relationships
        ├── archives/     # ZIP archives with integrity proofs
        ├── meta_capsules/# System state meta-capsules
        ├── ledger.log    # Main provenance ledger with hash chains
        ├── heartbeat.log # System heartbeat and timing log
        └── unity_seal.txt# Final unity seal with completion status
```

## Use Cases

### Document Archiving with Provenance
```bash
# Create timestamped document capsule
echo "Important contract document" > contract.txt
python3 capsule_metadata.py create-capsule "contract_v1" contract.txt --metadata '{"type": "legal", "classification": "confidential"}'

# Run EPOCH5 to create provenance chain
./epoch5.sh

# Create system snapshot
python3 meta_capsule.py create "contract_archive_$(date +%Y%m%d)" --description "Contract archive with full provenance"

# Verify everything
python3 capsule_metadata.py verify "contract_v1"
python3 meta_capsule.py verify "contract_archive_$(date +%Y%m%d)"
```

### Data Pipeline with Integrity Checking
```bash
# Create data processing pipeline
echo "Raw data batch 1" > raw_data.csv
python3 capsule_metadata.py create-capsule "raw_batch_1" raw_data.csv

# Process data (external processing step)
echo "Processed data batch 1" > processed_data.json
python3 capsule_metadata.py create-capsule "processed_batch_1" processed_data.json

# Link with metadata
python3 capsule_metadata.py create-metadata "pipeline_batch_1" "raw_batch_1" "processed_batch_1" --metadata '{"pipeline": "data_processing_v2", "batch_id": "20240825_001"}'

# Create final archive
python3 capsule_metadata.py create-archive "pipeline_complete" "raw_batch_1" "processed_batch_1"

# Generate system state with EPOCH5
DELAY_HOURS_P1_P2=0 DELAY_HOURS_P2_P3=0 ./epoch5.sh
python3 meta_capsule.py create "pipeline_$(date +%Y%m%d_%H%M%S)"
```

### Compliance and Audit Trail
```bash
# Create comprehensive audit snapshot
python3 meta_capsule.py create "audit_$(date +%Y%m%d)" --description "Monthly compliance audit snapshot"

# Verify all system components
python3 meta_capsule.py state
python3 capsule_metadata.py list-capsules
python3 capsule_metadata.py list-archives

# Generate audit report
echo "=== EPOCH5 Audit Report ===" > audit_report.txt
echo "Generated: $(date)" >> audit_report.txt
python3 meta_capsule.py list >> audit_report.txt
python3 capsule_metadata.py list-capsules >> audit_report.txt
```

## Requirements

- **Bash 4.0+** for epoch5.sh
- **Python 3.7+** for Python components
- **openssl** or **shasum** for hashing (usually pre-installed)
- Standard library modules only (no external dependencies)

## Getting Started

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd epoch5-template
   chmod +x epoch5.sh
   ```

2. **Run your first EPOCH5 capsule**:
   ```bash
   # Quick test with no delays
   DELAY_HOURS_P1_P2=0 DELAY_HOURS_P2_P3=0 ./epoch5.sh
   ```

3. **Create and verify a data capsule**:
   ```bash
   echo "Test data" > test.txt
   python3 capsule_metadata.py create-capsule "test_1" test.txt
   python3 capsule_metadata.py verify "test_1"
   ```

4. **Create system snapshot**:
   ```bash
   python3 meta_capsule.py create "first_snapshot" --description "Initial system state"
   ```

5. **View system status**:
   ```bash
   python3 meta_capsule.py state
   python3 meta_capsule.py list
   ```

The EPOCH5 Template provides a complete foundation for secure, auditable data processing with comprehensive provenance tracking and cryptographic integrity verification.