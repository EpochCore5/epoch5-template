#!/usr/bin/env python3
"""
Advanced Logging, Hashing, and Provenance Tracking Script

This script provides advanced security and functionality features including:
- Ledger management with JSONL format and integrity validation
- Content-Addressed Storage (CAS) with Merkle tree computation
- Capsule archiving with atomic ZIP operations
- Blackboard reinjection with LWW and OR set models
- JSON output summaries
"""

import json
import hashlib
import os
import sys
import zipfile
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import tempfile
import shutil


class AdvancedLedger:
    """Advanced ledger system with provenance tracking and integrity validation."""
    
    def __init__(self, ledger_path: str = "ledger_main.jsonl", cas_dir: str = "cas", 
                 blackboard_path: str = "mesh_blackboard.json", 
                 merkle_path: str = "mesh_merkle_tlsar.json"):
        self.ledger_path = Path(ledger_path)
        self.cas_dir = Path(cas_dir)
        self.blackboard_path = Path(blackboard_path)
        self.merkle_path = Path(merkle_path)
        
        # Ensure directories exist
        self.cas_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.blackboard_path.parent.mkdir(parents=True, exist_ok=True)
        self.merkle_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _compute_sha256(self, data: str) -> str:
        """Compute SHA-256 hash of string data."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file contents."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _get_timestamp(self) -> str:
        """Get ISO 8601 UTC timestamp."""
        return datetime.now(timezone.utc).isoformat()
    
    def _get_previous_hash(self) -> str:
        """Get the line_sha of the last record in the ledger."""
        if not self.ledger_path.exists():
            return "0" * 64  # Genesis hash
        
        try:
            with open(self.ledger_path, 'r') as f:
                lines = f.readlines()
                if not lines:
                    return "0" * 64
                
                last_line = lines[-1].strip()
                if last_line:
                    record = json.loads(last_line)
                    return record.get('line_sha', "0" * 64)
                return "0" * 64
        except (json.JSONDecodeError, FileNotFoundError):
            return "0" * 64
    
    def log_event(self, event_type: str, data: Dict[str, Any], 
                  provenance: Optional[Dict[str, Any]] = None) -> str:
        """Log an event to the ledger with integrity validation."""
        timestamp = self._get_timestamp()
        prev_hash = self._get_previous_hash()
        
        # Create the record
        record = {
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data,
            "provenance": provenance or {},
            "prev_hash": prev_hash
        }
        
        # Compute the line hash for this record
        record_json = json.dumps(record, sort_keys=True, separators=(',', ':'))
        line_sha = self._compute_sha256(record_json)
        record["line_sha"] = line_sha
        
        # Write to ledger
        with open(self.ledger_path, 'a') as f:
            f.write(json.dumps(record, separators=(',', ':')) + '\n')
        
        return line_sha
    
    def validate_ledger_integrity(self) -> bool:
        """Validate the integrity of the entire ledger."""
        if not self.ledger_path.exists():
            return True
        
        prev_expected = "0" * 64
        
        with open(self.ledger_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    
                    # Check if prev_hash matches expected
                    if record.get('prev_hash') != prev_expected:
                        print(f"Integrity violation at line {line_num}: prev_hash mismatch")
                        return False
                    
                    # Recompute line_sha
                    line_sha = record.pop('line_sha', None)
                    record_json = json.dumps(record, sort_keys=True, separators=(',', ':'))
                    computed_sha = self._compute_sha256(record_json)
                    
                    if line_sha != computed_sha:
                        print(f"Integrity violation at line {line_num}: line_sha mismatch")
                        return False
                    
                    prev_expected = line_sha
                    
                except json.JSONDecodeError:
                    print(f"Invalid JSON at line {line_num}")
                    return False
        
        return True
    
    def store_in_cas(self, content: bytes, filename: str) -> str:
        """Store content in Content-Addressed Storage and return hash."""
        content_hash = hashlib.sha256(content).hexdigest()
        cas_file = self.cas_dir / f"{content_hash}_{filename}"
        
        with open(cas_file, 'wb') as f:
            f.write(content)
        
        return content_hash
    
    def compute_merkle_tree(self) -> str:
        """Compute Merkle tree for all files in CAS and store root hash."""
        if not self.cas_dir.exists():
            root_hash = "0" * 64
        else:
            # Get all files and their hashes
            file_hashes = []
            for file_path in sorted(self.cas_dir.glob("*")):
                if file_path.is_file():
                    file_hash = self._compute_file_hash(file_path)
                    file_hashes.append(file_hash)
            
            # Compute Merkle root
            if not file_hashes:
                root_hash = "0" * 64
            else:
                # Simple Merkle tree implementation
                level = file_hashes[:]
                while len(level) > 1:
                    next_level = []
                    for i in range(0, len(level), 2):
                        if i + 1 < len(level):
                            combined = level[i] + level[i + 1]
                        else:
                            combined = level[i] + level[i]  # Duplicate if odd number
                        next_level.append(self._compute_sha256(combined))
                    level = next_level
                root_hash = level[0] if level else "0" * 64
        
        # Store Merkle tree info
        merkle_data = {
            "timestamp": self._get_timestamp(),
            "root_hash": root_hash,
            "file_count": len(list(self.cas_dir.glob("*"))) if self.cas_dir.exists() else 0
        }
        
        with open(self.merkle_path, 'w') as f:
            json.dump(merkle_data, f, indent=2)
        
        return root_hash
    
    def archive_capsule(self, capsule_id: str, files: List[str], 
                       archive_dir: str = "archives") -> str:
        """Archive capsule files into a ZIP atomically."""
        archive_dir_path = Path(archive_dir)
        archive_dir_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        archive_name = f"{capsule_id}_{timestamp}.zip"
        archive_path = archive_dir_path / archive_name
        temp_path = archive_path.with_suffix('.zip.tmp')
        
        try:
            # Create archive atomically using temporary file
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in files:
                    file_path = Path(file_path)
                    if file_path.exists():
                        zf.write(file_path, file_path.name)
            
            # Atomic move
            temp_path.rename(archive_path)
            
            # Log the archiving event
            self.log_event("capsule_archived", {
                "capsule_id": capsule_id,
                "archive_path": str(archive_path),
                "file_count": len(files),
                "archive_hash": self._compute_file_hash(archive_path)
            })
            
            return str(archive_path)
            
        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise e
    
    def update_blackboard(self, capsule_id: str, operation: str, 
                         data: Dict[str, Any]) -> None:
        """Update blackboard with LWW and OR set model."""
        timestamp = self._get_timestamp()
        
        # Load existing blackboard
        if self.blackboard_path.exists():
            with open(self.blackboard_path, 'r') as f:
                blackboard = json.load(f)
        else:
            blackboard = {
                "lww_register": {},  # Last-Write-Wins register
                "or_set": {          # Observed-Removed set
                    "added": {},
                    "removed": {}
                }
            }
        
        # Update LWW register
        if capsule_id not in blackboard["lww_register"]:
            blackboard["lww_register"][capsule_id] = {}
        
        blackboard["lww_register"][capsule_id] = {
            "timestamp": timestamp,
            "operation": operation,
            "data": data
        }
        
        # Update OR set based on operation
        if operation == "add":
            blackboard["or_set"]["added"][capsule_id] = {
                "timestamp": timestamp,
                "data": data
            }
            # Remove from removed set if present
            blackboard["or_set"]["removed"].pop(capsule_id, None)
        elif operation == "remove":
            blackboard["or_set"]["removed"][capsule_id] = {
                "timestamp": timestamp,
                "data": data
            }
        
        # Write back atomically
        temp_path = self.blackboard_path.with_suffix('.json.tmp')
        with open(temp_path, 'w') as f:
            json.dump(blackboard, f, indent=2)
        temp_path.rename(self.blackboard_path)
    
    def process_capsule(self, capsule_id: str, title: str, content: str,
                       metadata: Optional[Dict[str, Any]] = None,
                       files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Process a complete capsule with all operations."""
        start_time = self._get_timestamp()
        
        # Store content in CAS
        content_hash = self.store_in_cas(content.encode('utf-8'), f"{capsule_id}.txt")
        
        # Store additional files in CAS if provided
        file_hashes = {}
        if files:
            for file_path in files:
                file_path = Path(file_path)
                if file_path.exists():
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    file_hash = self.store_in_cas(file_content, file_path.name)
                    file_hashes[str(file_path)] = file_hash
        
        # Compute Merkle tree
        merkle_root = self.compute_merkle_tree()
        
        # Create archive
        cas_files = list(self.cas_dir.glob(f"{content_hash}_*"))
        if files:
            cas_files.extend([self.cas_dir / f"{h}_{Path(f).name}" 
                            for f, h in file_hashes.items()])
        
        archive_path = self.archive_capsule(capsule_id, [str(f) for f in cas_files])
        
        # Update blackboard
        capsule_data = {
            "title": title,
            "content_hash": content_hash,
            "file_hashes": file_hashes,
            "metadata": metadata or {}
        }
        self.update_blackboard(capsule_id, "add", capsule_data)
        
        # Log to ledger
        ledger_data = {
            "capsule_id": capsule_id,
            "title": title,
            "content_hash": content_hash,
            "file_hashes": file_hashes,
            "merkle_root": merkle_root,
            "archive_path": archive_path,
            "metadata": metadata or {}
        }
        
        provenance = {
            "script": "advanced_ledger.py",
            "version": "1.0.0",
            "operation": "process_capsule"
        }
        
        line_sha = self.log_event("capsule_processed", ledger_data, provenance)
        
        # Return summary
        return {
            "timestamp": start_time,
            "capsule_id": capsule_id,
            "content_sha256": content_hash,
            "merkle_root": merkle_root,
            "archive_path": archive_path,
            "line_sha": line_sha,
            "file_hashes": file_hashes,
            "status": "success"
        }


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Advanced ledger and provenance tracking system"
    )
    parser.add_argument("--capsule-id", 
                       help="Unique identifier for the capsule")
    parser.add_argument("--title",
                       help="Title for the capsule")
    parser.add_argument("--content", 
                       help="Content to store (or use --content-file)")
    parser.add_argument("--content-file",
                       help="File containing content to store")
    parser.add_argument("--files", nargs="*", default=[],
                       help="Additional files to include in the capsule")
    parser.add_argument("--metadata",
                       help="JSON metadata for the capsule")
    parser.add_argument("--ledger", default="ledger_main.jsonl",
                       help="Path to the ledger file")
    parser.add_argument("--cas-dir", default="cas",
                       help="Content-Addressed Storage directory")
    parser.add_argument("--blackboard", default="mesh_blackboard.json",
                       help="Blackboard file path")
    parser.add_argument("--merkle", default="mesh_merkle_tlsar.json",
                       help="Merkle tree file path")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate ledger integrity")
    parser.add_argument("--output-format", choices=["json", "pretty"], default="json",
                       help="Output format")
    
    args = parser.parse_args()
    
    # Initialize ledger system
    ledger = AdvancedLedger(
        ledger_path=args.ledger,
        cas_dir=args.cas_dir,
        blackboard_path=args.blackboard,
        merkle_path=args.merkle
    )
    
    # Handle validation-only mode
    if args.validate_only:
        is_valid = ledger.validate_ledger_integrity()
        result = {
            "validation": "passed" if is_valid else "failed",
            "timestamp": ledger._get_timestamp()
        }
        print(json.dumps(result, indent=2 if args.output_format == "pretty" else None))
        sys.exit(0 if is_valid else 1)
    
    # Validate required arguments for capsule processing
    if not args.capsule_id:
        print("Error: --capsule-id is required for capsule processing", file=sys.stderr)
        sys.exit(1)
    if not args.title:
        print("Error: --title is required for capsule processing", file=sys.stderr)
        sys.exit(1)
    
    # Get content
    if args.content:
        content = args.content
    elif args.content_file:
        try:
            with open(args.content_file, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: Content file '{args.content_file}' not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading content file '{args.content_file}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: Either --content or --content-file must be provided", file=sys.stderr)
        sys.exit(1)
    
    # Parse metadata if provided
    metadata = None
    if args.metadata:
        try:
            metadata = json.loads(args.metadata)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in --metadata", file=sys.stderr)
            sys.exit(1)
    
    try:
        # Process the capsule
        result = ledger.process_capsule(
            capsule_id=args.capsule_id,
            title=args.title,
            content=content,
            metadata=metadata,
            files=args.files
        )
        
        # Output result
        if args.output_format == "pretty":
            print(json.dumps(result, indent=2))
        else:
            print(json.dumps(result))
            
    except Exception as e:
        error_result = {
            "timestamp": ledger._get_timestamp(),
            "status": "error",
            "error": str(e)
        }
        print(json.dumps(error_result, indent=2 if args.output_format == "pretty" else None))
        sys.exit(1)


if __name__ == "__main__":
    main()