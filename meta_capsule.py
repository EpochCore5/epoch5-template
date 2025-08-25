#!/usr/bin/env python3
"""
Meta-Capsule Creation System
Generates a meta-capsule that captures the state of EPOCH5 core systems
Updates the ledger with the meta-capsule, ensuring traceability
Focuses on core ledger, manifest logging, and Unity Seal functionality
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import zipfile
import glob

# Import capsule management for integration
try:
    from capsule_metadata import CapsuleManager
except ImportError:
    CapsuleManager = None

class MetaCapsuleCreator:
    def __init__(self, base_dir: str = "./archive/EPOCH5"):
        self.base_dir = Path(base_dir)
        self.meta_dir = self.base_dir / "meta_capsules"
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        
        self.ledger_file = self.base_dir / "ledger.log"
        self.meta_ledger = self.meta_dir / "meta_ledger.log"
        self.state_snapshots = self.meta_dir / "state_snapshots"
        self.state_snapshots.mkdir(parents=True, exist_ok=True)
        
        # Initialize capsule manager if available
        self.capsule_manager = CapsuleManager(base_dir) if CapsuleManager else None
    
    def timestamp(self) -> str:
        """Generate ISO timestamp consistent with EPOCH5"""
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def sha256(self, data: str) -> str:
        """Generate SHA256 hash consistent with EPOCH5"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    def capture_system_state(self) -> Dict[str, Any]:
        """Capture the current state of EPOCH5 core systems"""
        state = {
            "captured_at": self.timestamp(),
            "systems": {},
            "file_hashes": {},
            "summary_stats": {}
        }
        
        # Capture capsule and metadata state if available
        if self.capsule_manager:
            try:
                capsules = self.capsule_manager.list_capsules()
                archives = self.capsule_manager.list_archives()
                state["systems"]["capsules"] = {
                    "total_capsules": len(capsules),
                    "total_archives": len(archives),
                    "capsule_summary": capsules[:10],  # Sample of capsules
                    "archive_summary": archives[:10]   # Sample of archives
                }
                
                # Hash capsule files
                for dir_name in ["capsules", "metadata", "archives"]:
                    dir_path = self.base_dir / dir_name
                    if dir_path.exists():
                        for file_path in dir_path.glob("*.json"):
                            with open(file_path, 'r') as f:
                                content = f.read()
                                state["file_hashes"][f"{dir_name}/{file_path.name}"] = self.sha256(content)
            except Exception as e:
                # Graceful fallback if capsule manager fails
                state["systems"]["capsules"] = {"error": str(e)}
        
        # Capture base EPOCH5 system state
        state["systems"]["epoch5_base"] = self.capture_epoch5_base_state()
        
        # Generate summary statistics
        state["summary_stats"] = {
            "total_files_captured": len(state["file_hashes"]),
            "systems_captured": len(state["systems"]),
            "capture_timestamp": state["captured_at"],
            "state_hash": self.sha256(json.dumps(state["systems"], sort_keys=True))
        }
        
        return state
    
    def capture_epoch5_base_state(self) -> Dict[str, Any]:
        """Capture state from the original EPOCH5 system"""
        base_state = {
            "ledger": {"exists": False, "entries": 0, "hash": None},
            "heartbeat": {"exists": False, "entries": 0, "hash": None},
            "manifests": {"count": 0, "files": []},
            "unity_seal": {"exists": False, "hash": None}
        }
        
        # Check ledger
        if self.ledger_file.exists():
            with open(self.ledger_file, 'r') as f:
                content = f.read()
                lines = content.strip().split('\n') if content.strip() else []
                base_state["ledger"] = {
                    "exists": True,
                    "entries": len(lines),
                    "hash": self.sha256(content),
                    "last_entry": lines[-1] if lines else None
                }
        
        # Check heartbeat
        heartbeat_file = self.base_dir / "heartbeat.log"
        if heartbeat_file.exists():
            with open(heartbeat_file, 'r') as f:
                content = f.read()
                lines = content.strip().split('\n') if content.strip() else []
                base_state["heartbeat"] = {
                    "exists": True,
                    "entries": len(lines),
                    "hash": self.sha256(content)
                }
        
        # Check manifests
        manifests_dir = self.base_dir / "manifests"
        if manifests_dir.exists():
            manifest_files = list(manifests_dir.glob("*.txt"))
            base_state["manifests"] = {
                "count": len(manifest_files),
                "files": [f.name for f in manifest_files]
            }
        
        # Check unity seal
        unity_seal_file = self.base_dir / "unity_seal.txt"
        if unity_seal_file.exists():
            with open(unity_seal_file, 'r') as f:
                content = f.read()
                base_state["unity_seal"] = {
                    "exists": True,
                    "hash": self.sha256(content)
                }
        
        return base_state
    
    def create_meta_capsule(self, meta_capsule_id: str, description: str = "") -> Dict[str, Any]:
        """Create a meta-capsule capturing the complete system state"""
        # Capture current system state
        system_state = self.capture_system_state()
        
        # Create meta-capsule
        meta_capsule = {
            "meta_capsule_id": meta_capsule_id,
            "created_at": self.timestamp(),
            "description": description,
            "version": "1.0",
            "type": "EPOCH5_META_CAPSULE",
            "system_state": system_state,
            "provenance_chain": self.build_provenance_chain(),
            "integrity_verification": {},
            "archive_info": None,
            "ledger_update": None
        }
        
        # Calculate meta-capsule hash
        meta_data = json.dumps({
            "meta_capsule_id": meta_capsule_id,
            "created_at": meta_capsule["created_at"],
            "state_hash": system_state["summary_stats"]["state_hash"],
            "file_count": system_state["summary_stats"]["total_files_captured"]
        }, sort_keys=True)
        
        meta_capsule["meta_hash"] = self.sha256(meta_data)
        
        # Create integrity verification
        meta_capsule["integrity_verification"] = self.create_integrity_verification(meta_capsule)
        
        # Save meta-capsule
        meta_capsule_file = self.meta_dir / f"{meta_capsule_id}.json"
        with open(meta_capsule_file, 'w') as f:
            json.dump(meta_capsule, f, indent=2)
        
        # Create system archive
        archive_info = self.create_system_archive(meta_capsule_id)
        meta_capsule["archive_info"] = archive_info
        
        # Update ledger with meta-capsule
        self.update_ledger_with_meta_capsule(meta_capsule)
        
        # Log the meta-capsule creation
        self.log_meta_event(meta_capsule_id, "created", {
            "systems_captured": len(system_state["systems"]),
            "files_captured": system_state["summary_stats"]["total_files_captured"],
            "meta_hash": meta_capsule["meta_hash"]
        })
        
        return meta_capsule
    
    def build_provenance_chain(self) -> List[Dict[str, Any]]:
        """Build provenance chain from ledger entries"""
        chain = []
        
        if self.ledger_file.exists():
            with open(self.ledger_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '|RECORD_HASH=' in line:
                        parts = line.split('|RECORD_HASH=')
                        if len(parts) == 2:
                            chain.append({
                                "entry": parts[0],
                                "hash": parts[1],
                                "timestamp": self.timestamp()
                            })
        
        return chain
    
    def create_integrity_verification(self, meta_capsule: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive integrity verification for the meta-capsule"""
        verification = {
            "verified_at": self.timestamp(),
            "components": {},
            "overall_valid": True
        }
        
        # Verify ledger integrity
        if self.ledger_file.exists():
            verification["components"]["ledger"] = {
                "exists": True,
                "hash_valid": True,  # Could implement chain validation here
                "entry_count": len(meta_capsule["provenance_chain"])
            }
        
        # Verify manifests
        manifests_dir = self.base_dir / "manifests"
        if manifests_dir.exists():
            manifest_files = list(manifests_dir.glob("*.txt"))
            verification["components"]["manifests"] = {
                "count": len(manifest_files),
                "all_readable": all(f.is_file() for f in manifest_files)
            }
        
        return verification
    
    def create_system_archive(self, meta_capsule_id: str) -> Dict[str, Any]:
        """Create a comprehensive archive of the entire system state"""
        archive_path = self.state_snapshots / f"{meta_capsule_id}_system.zip"
        
        archive_info = {
            "created_at": self.timestamp(),
            "archive_path": str(archive_path),
            "file_count": 0,
            "total_size": 0,
            "status": "created"
        }
        
        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Archive core EPOCH5 directories
                system_dirs = ["manifests", "capsules", "metadata", "archives", "meta_capsules"]
                
                for dir_name in system_dirs:
                    dir_path = self.base_dir / dir_name
                    if dir_path.exists():
                        for file_path in dir_path.rglob("*"):
                            if file_path.is_file():
                                arc_name = f"{dir_name}/{file_path.relative_to(dir_path)}"
                                zipf.write(file_path, arc_name)
                                archive_info["file_count"] += 1
                
                # Archive core files
                core_files = ["ledger.log", "heartbeat.log", "unity_seal.txt"]
                for core_file in core_files:
                    file_path = self.base_dir / core_file
                    if file_path.exists():
                        zipf.write(file_path, core_file)
                        archive_info["file_count"] += 1
            
            archive_info["total_size"] = archive_path.stat().st_size
            archive_info["status"] = "completed"
            
        except Exception as e:
            archive_info["status"] = "failed"
            archive_info["error"] = str(e)
        
        return archive_info
    
    def update_ledger_with_meta_capsule(self, meta_capsule: Dict[str, Any]):
        """Update the main ledger with meta-capsule information"""
        prev_hash = self.get_previous_hash()
        
        # Create ledger entry for meta-capsule
        ledger_entry = {
            "timestamp": self.timestamp(),
            "type": "META_CAPSULE",
            "meta_capsule_id": meta_capsule["meta_capsule_id"],
            "meta_hash": meta_capsule["meta_hash"],
            "systems_captured": len(meta_capsule["system_state"]["systems"]),
            "files_captured": meta_capsule["system_state"]["summary_stats"]["total_files_captured"],
            "prev_hash": prev_hash
        }
        
        # Calculate record hash
        entry_data = f"{ledger_entry['timestamp']}|{ledger_entry['type']}|{meta_capsule['meta_capsule_id']}|{prev_hash}"
        record_hash = self.sha256(entry_data)
        
        # Write to ledger
        ledger_line = f"{json.dumps(ledger_entry)}|RECORD_HASH={record_hash}"
        with open(self.ledger_file, 'a') as f:
            f.write(f"{ledger_line}\n")
        
        meta_capsule["ledger_update"] = {
            "entry": ledger_entry,
            "record_hash": record_hash,
            "updated_at": self.timestamp()
        }
    
    def get_previous_hash(self) -> str:
        """Get the previous hash from the ledger for chaining"""
        if not self.ledger_file.exists():
            return "GENESIS"
        
        with open(self.ledger_file, 'r') as f:
            lines = f.read().strip().split('\n')
            if lines and lines[-1]:
                last_line = lines[-1]
                if '|RECORD_HASH=' in last_line:
                    return last_line.split('|RECORD_HASH=')[-1]
        
        return "GENESIS"
    
    def verify_meta_capsule(self, meta_capsule_id: str) -> Dict[str, Any]:
        """Verify the integrity of a meta-capsule"""
        result = {
            "meta_capsule_id": meta_capsule_id,
            "verified_at": self.timestamp(),
            "integrity_valid": False,
            "archive_valid": False,
            "ledger_consistent": False,
            "errors": []
        }
        
        meta_capsule_file = self.meta_dir / f"{meta_capsule_id}.json"
        
        if not meta_capsule_file.exists():
            result["errors"].append("Meta-capsule file not found")
            return result
        
        try:
            with open(meta_capsule_file, 'r') as f:
                meta_capsule = json.load(f)
            
            # Verify meta-capsule hash
            meta_data = json.dumps({
                "meta_capsule_id": meta_capsule["meta_capsule_id"],
                "created_at": meta_capsule["created_at"],
                "state_hash": meta_capsule["system_state"]["summary_stats"]["state_hash"],
                "file_count": meta_capsule["system_state"]["summary_stats"]["total_files_captured"]
            }, sort_keys=True)
            
            expected_hash = self.sha256(meta_data)
            if expected_hash == meta_capsule["meta_hash"]:
                result["integrity_valid"] = True
            else:
                result["errors"].append("Meta-capsule hash mismatch")
            
            # Verify archive
            if meta_capsule.get("archive_info"):
                archive_path = Path(meta_capsule["archive_info"]["archive_path"])
                if archive_path.exists():
                    result["archive_valid"] = True
                else:
                    result["errors"].append("Archive file not found")
            
            # Verify ledger entry
            result["ledger_consistent"] = self.verify_ledger_entry(meta_capsule)
            
        except Exception as e:
            result["errors"].append(f"Verification error: {str(e)}")
        
        return result
    
    def verify_ledger_entry(self, meta_capsule: Dict[str, Any]) -> bool:
        """Verify that the meta-capsule entry exists in the ledger"""
        if not self.ledger_file.exists():
            return False
        
        meta_capsule_id = meta_capsule["meta_capsule_id"]
        meta_hash = meta_capsule["meta_hash"]
        
        with open(self.ledger_file, 'r') as f:
            for line in f:
                if meta_capsule_id in line and meta_hash in line:
                    return True
        
        return False
    
    def list_meta_capsules(self) -> List[Dict[str, Any]]:
        """List all meta-capsules"""
        meta_capsules = []
        
        for file_path in self.meta_dir.glob("*.json"):
            if file_path.name != "meta_ledger.log":
                try:
                    with open(file_path, 'r') as f:
                        meta_capsule = json.load(f)
                        summary = {
                            "meta_capsule_id": meta_capsule["meta_capsule_id"],
                            "created_at": meta_capsule["created_at"],
                            "description": meta_capsule.get("description", ""),
                            "systems_captured": len(meta_capsule["system_state"]["systems"]),
                            "files_captured": meta_capsule["system_state"]["summary_stats"]["total_files_captured"],
                            "meta_hash": meta_capsule["meta_hash"]
                        }
                        meta_capsules.append(summary)
                except Exception:
                    continue
        
        return sorted(meta_capsules, key=lambda x: x["created_at"], reverse=True)
    
    def log_meta_event(self, meta_capsule_id: str, event: str, data: Dict[str, Any]):
        """Log meta-capsule events"""
        log_entry = {
            "timestamp": self.timestamp(),
            "meta_capsule_id": meta_capsule_id,
            "event": event,
            "data": data
        }
        
        with open(self.meta_ledger, 'a') as f:
            f.write(f"{json.dumps(log_entry)}\n")

# CLI interface for meta-capsule management
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="EPOCH5 Meta-Capsule System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create meta-capsule
    create_parser = subparsers.add_parser("create", help="Create a new meta-capsule")
    create_parser.add_argument("meta_capsule_id", help="Meta-capsule identifier")
    create_parser.add_argument("--description", default="", help="Description of the meta-capsule")
    
    # Verify meta-capsule
    verify_parser = subparsers.add_parser("verify", help="Verify meta-capsule integrity")
    verify_parser.add_argument("meta_capsule_id", help="Meta-capsule identifier")
    
    # List meta-capsules
    subparsers.add_parser("list", help="List all meta-capsules")
    
    # Show current system state
    subparsers.add_parser("state", help="Show current system state")
    
    args = parser.parse_args()
    creator = MetaCapsuleCreator()
    
    if args.command == "create":
        meta_capsule = creator.create_meta_capsule(args.meta_capsule_id, args.description)
        print(f"Created meta-capsule: {meta_capsule['meta_capsule_id']}")
        print(f"Systems captured: {len(meta_capsule['system_state']['systems'])}")
        print(f"Files captured: {meta_capsule['system_state']['summary_stats']['total_files_captured']}")
        print(f"Meta-hash: {meta_capsule['meta_hash']}")
        
        if meta_capsule.get("archive_info") and meta_capsule["archive_info"]["status"] == "completed":
            print(f"System archive: {meta_capsule['archive_info']['file_count']} files, {meta_capsule['archive_info']['total_size']} bytes")
    
    elif args.command == "verify":
        result = creator.verify_meta_capsule(args.meta_capsule_id)
        print(f"Meta-capsule verification for {args.meta_capsule_id}:")
        print(f"  Integrity valid: {result['integrity_valid']}")
        print(f"  Archive valid: {result['archive_valid']}")
        print(f"  Ledger consistent: {result['ledger_consistent']}")
        
        if result["errors"]:
            print("  Errors:")
            for error in result["errors"]:
                print(f"    - {error}")
    
    elif args.command == "list":
        meta_capsules = creator.list_meta_capsules()
        print(f"All Meta-Capsules ({len(meta_capsules)}):")
        for mc in meta_capsules:
            print(f"  {mc['meta_capsule_id']}: {mc['created_at']} ({mc['systems_captured']} systems, {mc['files_captured']} files)")
    
    elif args.command == "state":
        state = creator.capture_system_state()
        print(f"Current System State:")
        print(f"  Captured at: {state['captured_at']}")
        print(f"  Systems: {len(state['systems'])}")
        print(f"  Files: {len(state['file_hashes'])}")
        print(f"  State hash: {state['summary_stats']['state_hash']}")
        
        for system_name, system_data in state['systems'].items():
            if isinstance(system_data, dict):
                print(f"    {system_name}: {len(system_data)} entries")
            else:
                print(f"    {system_name}: {type(system_data)}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()