#!/usr/bin/env python3
"""
Capsule and Metadata Management System
Stores capsules, metadata, and Merkle tree proofs for data integrity
Archives data into ZIP files for secure storage and transport
Integrates with EPOCH5 provenance tracking system
"""

import json
import hashlib
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional


class MerkleTree:
    """Simple Merkle tree implementation for data integrity proofs"""

    def __init__(self, data_blocks: List[str]):
        self.data_blocks = data_blocks
        self.tree_levels = []
        self.root_hash = self.build_tree()

    def sha256(self, data: str) -> str:
        """SHA256 hash function"""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def build_tree(self) -> str:
        """Build the Merkle tree and return root hash"""
        if not self.data_blocks:
            return self.sha256("")

        # Start with leaf hashes
        current_level = [self.sha256(block) for block in self.data_blocks]
        self.tree_levels.append(current_level[:])

        # Build tree levels
        while len(current_level) > 1:
            next_level = []

            # Process pairs of hashes
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined_hash = self.sha256(left + right)
                next_level.append(combined_hash)

            self.tree_levels.append(next_level[:])
            current_level = next_level

        return current_level[0] if current_level else self.sha256("")

    def get_proof(self, block_index: int) -> List[Dict[str, Any]]:
        """Get Merkle proof for a specific data block"""
        if block_index >= len(self.data_blocks):
            return []

        proof = []
        current_index = block_index

        for level in self.tree_levels[:-1]:  # Exclude root level
            # Find sibling
            if current_index % 2 == 0:  # Left child
                sibling_index = current_index + 1
                position = "right"
            else:  # Right child
                sibling_index = current_index - 1
                position = "left"

            if sibling_index < len(level):
                sibling_hash = level[sibling_index]
            else:
                sibling_hash = level[current_index]  # Self if no sibling

            proof.append({"hash": sibling_hash, "position": position})

            current_index = current_index // 2

        return proof

    def verify_proof(
        self, block_data: str, block_index: int, proof: List[Dict[str, Any]]
    ) -> bool:
        """Verify a Merkle proof"""
        current_hash = self.sha256(block_data)

        for proof_element in proof:
            sibling_hash = proof_element["hash"]
            position = proof_element["position"]

            if position == "left":
                current_hash = self.sha256(sibling_hash + current_hash)
            else:
                current_hash = self.sha256(current_hash + sibling_hash)

        return current_hash == self.root_hash


class CapsuleManager:
    def __init__(self, base_dir: str = "./archive/EPOCH5"):
        self.base_dir = Path(base_dir)
        self.capsules_dir = self.base_dir / "capsules"
        self.metadata_dir = self.base_dir / "metadata"
        self.archives_dir = self.base_dir / "archives"

        # Create directories
        for directory in [self.capsules_dir, self.metadata_dir, self.archives_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        self.capsules_index = self.capsules_dir / "index.json"
        self.metadata_index = self.metadata_dir / "index.json"
        self.integrity_log = self.base_dir / "integrity.log"

    def timestamp(self) -> str:
        """Generate ISO timestamp consistent with EPOCH5"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def sha256(self, data: str) -> str:
        """Generate SHA256 hash consistent with EPOCH5"""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def create_capsule(
        self,
        capsule_id: str,
        content: str,
        metadata: Dict[str, Any] = None,
        content_type: str = "text/plain",
    ) -> Dict[str, Any]:
        """Create a new data capsule with integrity protection"""
        capsule = {
            "capsule_id": capsule_id,
            "created_at": self.timestamp(),
            "content_type": content_type,
            "content_hash": self.sha256(content),
            "content_size": len(content.encode("utf-8")),
            "metadata": metadata or {},
            "merkle_root": None,
            "merkle_proofs": {},
            "integrity_verified": True,
            "version": 1,
            "status": "active",
        }

        # Create Merkle tree for content integrity
        content_blocks = self.split_content_to_blocks(content, block_size=1024)
        merkle_tree = MerkleTree(content_blocks)

        capsule["merkle_root"] = merkle_tree.root_hash
        capsule["content_blocks_count"] = len(content_blocks)

        # Generate proofs for each block
        for i, block in enumerate(content_blocks):
            proof = merkle_tree.get_proof(i)
            capsule["merkle_proofs"][f"block_{i}"] = {
                "block_hash": merkle_tree.sha256(block),
                "proof": proof,
                "block_index": i,
            }

        # Save capsule content
        capsule_file = self.capsules_dir / f"{capsule_id}.json"
        content_file = self.capsules_dir / f"{capsule_id}_content.dat"

        with open(content_file, "w", encoding="utf-8") as f:
            f.write(content)

        capsule["content_file"] = str(content_file)
        capsule["capsule_file"] = str(capsule_file)

        # Save capsule metadata
        with open(capsule_file, "w") as f:
            json.dump(capsule, f, indent=2)

        # Update index
        self.update_capsule_index(capsule)

        # Log integrity creation
        self.log_integrity_event(
            capsule_id,
            "CAPSULE_CREATED",
            {
                "merkle_root": capsule["merkle_root"],
                "blocks_count": capsule["content_blocks_count"],
                "content_hash": capsule["content_hash"],
            },
        )

        return capsule

    def split_content_to_blocks(
        self, content: str, block_size: int = 1024
    ) -> List[str]:
        """Split content into blocks for Merkle tree"""
        content_bytes = content.encode("utf-8")
        blocks = []

        for i in range(0, len(content_bytes), block_size):
            block = content_bytes[i : i + block_size]
            blocks.append(block.decode("utf-8", errors="ignore"))

        return blocks if blocks else [""]

    def load_capsule(self, capsule_id: str) -> Optional[Dict[str, Any]]:
        """Load a capsule from storage"""
        capsule_file = self.capsules_dir / f"{capsule_id}.json"

        if not capsule_file.exists():
            return None

        try:
            with open(capsule_file, "r") as f:
                return json.load(f)
        except Exception as e:
            self.log_integrity_event(
                capsule_id, "CAPSULE_LOAD_ERROR", {"error": str(e)}
            )
            return None

    def get_capsule_content(self, capsule_id: str) -> Optional[str]:
        """Get the content of a capsule"""
        capsule = self.load_capsule(capsule_id)
        if not capsule:
            return None

        content_file = Path(capsule.get("content_file", ""))
        if not content_file.exists():
            return None

        try:
            with open(content_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Verify content integrity
            if self.sha256(content) != capsule["content_hash"]:
                self.log_integrity_event(
                    capsule_id,
                    "CONTENT_INTEGRITY_VIOLATION",
                    {
                        "expected_hash": capsule["content_hash"],
                        "actual_hash": self.sha256(content),
                    },
                )
                return None

            return content

        except Exception as e:
            self.log_integrity_event(
                capsule_id, "CONTENT_READ_ERROR", {"error": str(e)}
            )
            return None

    def verify_capsule_integrity(self, capsule_id: str) -> Dict[str, Any]:
        """Verify the integrity of a capsule using Merkle proofs"""
        capsule = self.load_capsule(capsule_id)
        if not capsule:
            return {"error": "Capsule not found"}

        content = self.get_capsule_content(capsule_id)
        if content is None:
            return {"error": "Could not read capsule content"}

        verification_result = {
            "capsule_id": capsule_id,
            "verified_at": self.timestamp(),
            "content_hash_valid": False,
            "merkle_verification": {
                "root_valid": False,
                "blocks_verified": 0,
                "blocks_failed": 0,
                "total_blocks": capsule["content_blocks_count"],
            },
            "overall_valid": False,
        }

        # Verify content hash
        actual_content_hash = self.sha256(content)
        verification_result["content_hash_valid"] = (
            actual_content_hash == capsule["content_hash"]
        )

        # Verify Merkle tree
        content_blocks = self.split_content_to_blocks(content, block_size=1024)
        merkle_tree = MerkleTree(content_blocks)

        # Check if root hash matches
        verification_result["merkle_verification"]["root_valid"] = (
            merkle_tree.root_hash == capsule["merkle_root"]
        )

        # Verify individual blocks with their proofs
        for block_key, proof_data in capsule["merkle_proofs"].items():
            block_index = proof_data["block_index"]
            if block_index < len(content_blocks):
                block_data = content_blocks[block_index]
                proof = proof_data["proof"]

                if merkle_tree.verify_proof(block_data, block_index, proof):
                    verification_result["merkle_verification"]["blocks_verified"] += 1
                else:
                    verification_result["merkle_verification"]["blocks_failed"] += 1

        # Overall validation
        verification_result["overall_valid"] = (
            verification_result["content_hash_valid"]
            and verification_result["merkle_verification"]["root_valid"]
            and verification_result["merkle_verification"]["blocks_failed"] == 0
        )

        # Log verification result
        self.log_integrity_event(
            capsule_id, "INTEGRITY_VERIFICATION", verification_result
        )

        return verification_result

    def create_metadata_entry(
        self, entry_id: str, capsule_refs: List[str], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a metadata entry linking multiple capsules"""
        entry = {
            "entry_id": entry_id,
            "created_at": self.timestamp(),
            "capsule_references": capsule_refs,
            "metadata": metadata,
            "entry_hash": None,
            "dependency_hashes": {},
            "status": "active",
        }

        # Calculate dependency hashes
        for capsule_id in capsule_refs:
            capsule = self.load_capsule(capsule_id)
            if capsule:
                entry["dependency_hashes"][capsule_id] = capsule["content_hash"]

        # Calculate entry hash
        entry_data = f"{entry_id}|{','.join(capsule_refs)}|{json.dumps(metadata, sort_keys=True)}"
        entry["entry_hash"] = self.sha256(entry_data)

        # Save metadata entry
        metadata_file = self.metadata_dir / f"{entry_id}.json"
        with open(metadata_file, "w") as f:
            json.dump(entry, f, indent=2)

        # Update metadata index
        self.update_metadata_index(entry)

        return entry

    def create_archive(
        self, archive_id: str, capsule_ids: List[str], include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Create a ZIP archive containing capsules and metadata"""
        archive_info = {
            "archive_id": archive_id,
            "created_at": self.timestamp(),
            "included_capsules": capsule_ids,
            "include_metadata": include_metadata,
            "archive_hash": None,
            "file_count": 0,
            "total_size": 0,
        }

        archive_file = self.archives_dir / f"{archive_id}.zip"

        try:
            with zipfile.ZipFile(archive_file, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add capsules
                for capsule_id in capsule_ids:
                    capsule = self.load_capsule(capsule_id)
                    if not capsule:
                        continue

                    # Add capsule metadata
                    capsule_file = self.capsules_dir / f"{capsule_id}.json"
                    if capsule_file.exists():
                        zipf.write(capsule_file, f"capsules/{capsule_id}.json")
                        archive_info["file_count"] += 1

                    # Add capsule content
                    content_file = Path(capsule.get("content_file", ""))
                    if content_file.exists():
                        zipf.write(content_file, f"capsules/{capsule_id}_content.dat")
                        archive_info["file_count"] += 1

                # Add metadata entries if requested
                if include_metadata:
                    for metadata_file in self.metadata_dir.glob("*.json"):
                        zipf.write(metadata_file, f"metadata/{metadata_file.name}")
                        archive_info["file_count"] += 1

                # Add integrity log
                if self.integrity_log.exists():
                    zipf.write(self.integrity_log, "integrity.log")
                    archive_info["file_count"] += 1

            # Calculate archive properties
            archive_info["total_size"] = archive_file.stat().st_size

            # Calculate archive hash
            with open(archive_file, "rb") as f:
                archive_content = f.read()
                archive_info["archive_hash"] = hashlib.sha256(
                    archive_content
                ).hexdigest()

            archive_info["archive_file"] = str(archive_file)
            archive_info["status"] = "completed"

            # Save archive metadata
            archive_metadata_file = self.archives_dir / f"{archive_id}_metadata.json"
            with open(archive_metadata_file, "w") as f:
                json.dump(archive_info, f, indent=2)

            self.log_integrity_event(
                archive_id,
                "ARCHIVE_CREATED",
                {
                    "file_count": archive_info["file_count"],
                    "total_size": archive_info["total_size"],
                    "archive_hash": archive_info["archive_hash"],
                },
            )

            return archive_info

        except Exception as e:
            archive_info["status"] = "failed"
            archive_info["error"] = str(e)
            self.log_integrity_event(
                archive_id, "ARCHIVE_CREATION_FAILED", {"error": str(e)}
            )
            return archive_info

    def update_capsule_index(self, capsule: Dict[str, Any]):
        """Update the capsule index"""
        index = self.load_index(self.capsules_index)
        index["capsules"][capsule["capsule_id"]] = {
            "created_at": capsule["created_at"],
            "content_hash": capsule["content_hash"],
            "merkle_root": capsule["merkle_root"],
            "status": capsule["status"],
        }
        self.save_index(self.capsules_index, index)

    def update_metadata_index(self, entry: Dict[str, Any]):
        """Update the metadata index"""
        index = self.load_index(self.metadata_index)
        index["entries"][entry["entry_id"]] = {
            "created_at": entry["created_at"],
            "entry_hash": entry["entry_hash"],
            "capsule_count": len(entry["capsule_references"]),
            "status": entry["status"],
        }
        self.save_index(self.metadata_index, index)

    def load_index(self, index_file: Path) -> Dict[str, Any]:
        """Load an index file"""
        if index_file.exists():
            with open(index_file, "r") as f:
                return json.load(f)

        return {
            "capsules" if "capsules" in str(index_file) else "entries": {},
            "last_updated": self.timestamp(),
        }

    def save_index(self, index_file: Path, index: Dict[str, Any]):
        """Save an index file"""
        index["last_updated"] = self.timestamp()
        with open(index_file, "w") as f:
            json.dump(index, f, indent=2)

    def log_integrity_event(self, object_id: str, event: str, data: Dict[str, Any]):
        """Log integrity-related events"""
        log_entry = {
            "timestamp": self.timestamp(),
            "object_id": object_id,
            "event": event,
            "data": data,
            "hash": self.sha256(f"{self.timestamp()}|{object_id}|{event}"),
        }

        with open(self.integrity_log, "a") as f:
            f.write(f"{json.dumps(log_entry)}\n")

    def list_capsules(self) -> List[Dict[str, Any]]:
        """List all capsules"""
        index = self.load_index(self.capsules_index)
        capsules = []
        for capsule_id, metadata in index["capsules"].items():
            capsule_info = {"capsule_id": capsule_id}
            capsule_info.update(metadata)
            capsules.append(capsule_info)
        return capsules

    def list_archives(self) -> List[Dict[str, Any]]:
        """List all archives"""
        archives = []
        for metadata_file in self.archives_dir.glob("*_metadata.json"):
            with open(metadata_file, "r") as f:
                archives.append(json.load(f))
        return archives


# CLI interface for capsule management
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="EPOCH5 Capsule and Metadata Management"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create capsule
    create_parser = subparsers.add_parser("create-capsule", help="Create a new capsule")
    create_parser.add_argument("capsule_id", help="Capsule identifier")
    create_parser.add_argument("content_file", help="File containing content")
    create_parser.add_argument("--metadata", help="JSON metadata")

    # Verify capsule
    verify_parser = subparsers.add_parser("verify", help="Verify capsule integrity")
    verify_parser.add_argument("capsule_id", help="Capsule identifier")

    # Create metadata
    metadata_parser = subparsers.add_parser(
        "create-metadata", help="Create metadata entry"
    )
    metadata_parser.add_argument("entry_id", help="Metadata entry identifier")
    metadata_parser.add_argument(
        "capsule_ids", nargs="+", help="Referenced capsule IDs"
    )
    metadata_parser.add_argument("--metadata", help="JSON metadata")

    # Create archive
    archive_parser = subparsers.add_parser("create-archive", help="Create ZIP archive")
    archive_parser.add_argument("archive_id", help="Archive identifier")
    archive_parser.add_argument("capsule_ids", nargs="+", help="Capsule IDs to include")
    archive_parser.add_argument(
        "--no-metadata", action="store_true", help="Exclude metadata"
    )

    # List commands
    subparsers.add_parser("list-capsules", help="List all capsules")
    subparsers.add_parser("list-archives", help="List all archives")

    args = parser.parse_args()
    manager = CapsuleManager()

    if args.command == "create-capsule":
        with open(args.content_file, "r", encoding="utf-8") as f:
            content = f.read()

        metadata = json.loads(args.metadata) if args.metadata else {}
        capsule = manager.create_capsule(args.capsule_id, content, metadata)
        print(f"Created capsule: {capsule['capsule_id']}")
        print(f"Content hash: {capsule['content_hash']}")
        print(f"Merkle root: {capsule['merkle_root']}")

    elif args.command == "verify":
        result = manager.verify_capsule_integrity(args.capsule_id)
        print(
            f"Integrity verification for {args.capsule_id}: {'VALID' if result['overall_valid'] else 'INVALID'}"
        )
        if not result["overall_valid"]:
            print(f"Content hash valid: {result['content_hash_valid']}")
            print(f"Merkle root valid: {result['merkle_verification']['root_valid']}")
            print(
                f"Blocks verified: {result['merkle_verification']['blocks_verified']}"
            )
            print(f"Blocks failed: {result['merkle_verification']['blocks_failed']}")

    elif args.command == "create-metadata":
        metadata = json.loads(args.metadata) if args.metadata else {}
        entry = manager.create_metadata_entry(args.entry_id, args.capsule_ids, metadata)
        print(f"Created metadata entry: {entry['entry_id']}")
        print(f"Entry hash: {entry['entry_hash']}")

    elif args.command == "create-archive":
        archive = manager.create_archive(
            args.archive_id, args.capsule_ids, not args.no_metadata
        )
        print(f"Created archive: {archive['archive_id']}")
        print(f"Status: {archive['status']}")
        if archive["status"] == "completed":
            print(
                f"Files: {archive['file_count']}, Size: {archive['total_size']} bytes"
            )
            print(f"Archive hash: {archive['archive_hash']}")

    elif args.command == "list-capsules":
        capsules = manager.list_capsules()
        print(f"All Capsules ({len(capsules)}):")
        for capsule in capsules:
            print(f"  {capsule}")

    elif args.command == "list-archives":
        archives = manager.list_archives()
        print(f"All Archives ({len(archives)}):")
        for archive in archives:
            print(
                f"  {archive['archive_id']}: {archive['status']} ({archive['file_count']} files)"
            )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
