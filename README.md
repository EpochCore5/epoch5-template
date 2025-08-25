# epoch5-template
One-shot Bash capsule for EPOCH 5 — sealed payloads, manifest logging, and Unity Seal for Eli's archive

## Advanced Logging and Provenance Tracking

This repository now includes `advanced_ledger.py`, a Python script that provides advanced security and functionality features:

### Features

1. **Ledger Management:**
   - Logs events in a ledger (`ledger_main.jsonl`) with timestamps, SHA-256 hashes, and provenance tracking
   - Ensures the integrity of ledger entries by validating the `line_sha` of previous records
   - Supports chain validation to detect tampering

2. **Content-Addressed Storage (CAS):**
   - Stores capsule data and associated files in a secure CAS directory
   - Computes and maintains a Merkle tree for all files, with the root hash stored in `mesh_merkle_tlsar.json`
   - Files are stored with their SHA-256 hash as part of the filename for integrity

3. **Capsule Archiving:**
   - Archives capsules into ZIP files atomically for secure transport or storage
   - Uses temporary files to ensure atomic operations

4. **Blackboard Reinjection:**
   - Updates a blackboard file (`mesh_blackboard.json`) with a Last-Write-Wins (LWW) and Observed-Removed (OR) set model
   - Tracks capsule reinjection state for distributed systems

5. **Output Summary:**
   - Prints a JSON summary of the operation, including timestamps, SHA-256 seals, Merkle root hashes, and archive paths

### Usage

#### Basic Usage
```bash
# Process a capsule with content
python3 advanced_ledger.py --capsule-id "CAPSULE-001" --title "My Capsule" --content "Capsule content here"

# Process a capsule with content from file
python3 advanced_ledger.py --capsule-id "CAPSULE-002" --title "File Capsule" --content-file "content.txt"

# Process a capsule with additional files
python3 advanced_ledger.py --capsule-id "CAPSULE-003" --title "Multi-file Capsule" \
  --content "Main content" --files config.json data.csv

# Include metadata
python3 advanced_ledger.py --capsule-id "CAPSULE-004" --title "Metadata Capsule" \
  --content "Content with metadata" --metadata '{"author": "user", "version": "1.0"}'
```

#### Advanced Options
```bash
# Use custom file paths
python3 advanced_ledger.py --capsule-id "CAPSULE-005" --title "Custom Paths" \
  --content "Content" --ledger "custom_ledger.jsonl" --cas-dir "custom_cas" \
  --blackboard "custom_blackboard.json" --merkle "custom_merkle.json"

# Validate ledger integrity
python3 advanced_ledger.py --validate-only

# Pretty-formatted output
python3 advanced_ledger.py --capsule-id "CAPSULE-006" --title "Pretty Output" \
  --content "Content" --output-format pretty
```

### Output Example

```json
{
  "timestamp": "2025-08-25T05:04:43.939252+00:00",
  "capsule_id": "TEST-003",
  "content_sha256": "ccfad09e69fcbd81cce66fe1286f8395c949041abfe28ce01878a1e447d0f2bd",
  "merkle_root": "c14e9fbebe01c0fa9439d4c25d98ad1d853bb704bb15618a4b3bfd48059d4610",
  "archive_path": "archives/TEST-003_20250825_050443.zip",
  "line_sha": "607e0ca3dcf962ab3375a137299ff18fa6f33b23ee67a8a35db44f04141f4512",
  "file_hashes": {
    "test_config.txt": "179dc40a17b998966b6b515bcd7f14292f631647eda112ba3beb6e1d5a69286c",
    "test_data.txt": "e7a80979a3e7de52943c2ea3fe41d0c58670fa118ea53380d0728b77c95878c2"
  },
  "status": "success"
}
```

### Integration with EPOCH5

The advanced ledger system is designed to complement the existing `epoch5.sh` script. You can use it alongside the bash script to provide enhanced security and provenance tracking for your capsule operations.

### Security Features

- **Cryptographic Integrity:** All data is secured with SHA-256 hashing
- **Provenance Tracking:** Complete audit trail of all operations
- **Atomic Operations:** ZIP archiving uses atomic file operations
- **Chain Validation:** Ledger entries form a cryptographically secure chain
- **Content Addressing:** Files are stored by their content hash for deduplication and integrity