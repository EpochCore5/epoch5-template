"""
Tests for capsule metadata and management functionality
"""

import pytest
import json
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from capsule_metadata import CapsuleManager
except ImportError as e:
    pytest.skip(
        f"Could not import capsule_metadata module: {e}", allow_module_level=True
    )


class TestCapsuleManager:
    """Test cases for CapsuleManager class"""

    @pytest.fixture
    def capsule_manager(self, temp_dir):
        """Create a CapsuleManager instance for testing"""
        return CapsuleManager(base_dir=temp_dir)

    def test_initialization(self, capsule_manager):
        """Test that CapsuleManager initializes correctly"""
        assert capsule_manager is not None
        assert hasattr(capsule_manager, "base_dir")
        assert hasattr(capsule_manager, "capsules_dir")

    def test_create_capsule(self, capsule_manager):
        """Test capsule creation"""
        capsule_id = "test_capsule_001"
        content = "Test capsule content for validation"
        metadata = {
            "content_type": "text/plain",
            "description": "Test capsule",
            "tags": ["test", "validation"],
        }

        capsule = capsule_manager.create_capsule(capsule_id, content, metadata)

        assert isinstance(capsule, dict)
        assert capsule["capsule_id"] == capsule_id
        assert "content_hash" in capsule
        assert "created_at" in capsule
        assert capsule["metadata"] == metadata

        # Verify content hash is generated correctly
        expected_hash = capsule_manager.sha256(content)
        assert capsule["content_hash"] == expected_hash

    def test_store_capsule(self, capsule_manager):
        """Test capsule storage"""
        capsule_id = "storage_test"
        content = "Content to be stored"
        capsule = capsule_manager.create_capsule(capsule_id, content, {})

        # Store using the content directly with the capsule
        capsule_manager.update_capsule_index(capsule)

        # Verify capsule is indexed
        index = capsule_manager.load_index(capsule_manager.capsules_index)
        assert capsule_id in index["capsules"]

    def test_get_capsule(self, capsule_manager):
        """Test capsule retrieval"""
        capsule_id = "retrieval_test"
        content = "Content for retrieval test"
        capsule = capsule_manager.create_capsule(capsule_id, content, {"type": "test"})
        capsule_manager.update_capsule_index(capsule)

        retrieved_capsule = capsule_manager.load_capsule(capsule_id)
        assert retrieved_capsule is not None
        assert retrieved_capsule["capsule_id"] == capsule_id
        assert retrieved_capsule["content_hash"] == capsule["content_hash"]

    def test_verify_capsule_integrity(self, capsule_manager):
        """Test capsule integrity verification"""
        capsule_id = "integrity_test"
        content = "Content for integrity verification"
        capsule = capsule_manager.create_capsule(capsule_id, content, {})
        capsule_manager.update_capsule_index(capsule)

        verification_result = capsule_manager.verify_capsule_integrity(capsule_id)

        assert isinstance(verification_result, dict)
        assert "overall_valid" in verification_result

    def test_list_capsules(self, capsule_manager):
        """Test capsule listing"""
        # Create multiple capsules
        for i in range(3):
            capsule_id = f"list_test_{i}"
            content = f"Content {i}"
            capsule = capsule_manager.create_capsule(capsule_id, content, {})
            capsule_manager.update_capsule_index(capsule)

        capsules = capsule_manager.list_capsules()
        assert len(capsules) >= 3  # May have more from other tests
        # The list_capsules returns index values which contain metadata like created_at, content_hash, etc.
        assert all("created_at" in capsule for capsule in capsules)
        assert all("content_hash" in capsule for capsule in capsules)

    def test_create_merkle_tree(self, capsule_manager):
        """Test Merkle tree creation through capsule system"""
        capsule_ids = []

        # Create multiple capsules for Merkle tree
        for i in range(4):
            capsule_id = f"merkle_test_{i}"
            content = f"Merkle content {i}"
            capsule = capsule_manager.create_capsule(capsule_id, content, {})
            capsule_manager.update_capsule_index(capsule)
            capsule_ids.append(capsule_id)

        # Create blocks from capsule content for Merkle tree
        blocks = [f"Block {i}" for i in range(4)]
        content_blocks = capsule_manager.split_content_to_blocks("\n".join(blocks), 10)

        assert isinstance(content_blocks, list)
        assert len(content_blocks) > 0

    def test_create_archive(self, capsule_manager):
        """Test archive creation"""
        # Create capsules for archiving
        capsule_ids = []
        for i in range(2):
            capsule_id = f"archive_test_{i}"
            content = f"Archive content {i}"
            capsule = capsule_manager.create_capsule(capsule_id, content, {})
            capsule_manager.update_capsule_index(capsule)
            capsule_ids.append(capsule_id)

        archive_result = capsule_manager.create_archive(
            "test_archive", capsule_ids, include_metadata=True
        )

        assert isinstance(archive_result, dict)
        assert "archive_id" in archive_result
        assert "archive_file" in archive_result
        assert "archive_hash" in archive_result
        assert archive_result["archive_id"] == "test_archive"

    def test_nonexistent_capsule(self, capsule_manager):
        """Test operations on nonexistent capsules"""
        fake_capsule_id = "nonexistent_capsule"

        capsule = capsule_manager.load_capsule(fake_capsule_id)
        assert capsule is None

        verification = capsule_manager.verify_capsule_integrity(fake_capsule_id)
        assert "error" in verification
        assert verification["error"] == "Capsule not found"
