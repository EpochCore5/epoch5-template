"""
Extended tests for capsule metadata functionality to improve coverage
"""

import pytest
import json
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from capsule_metadata import CapsuleManager, main
except ImportError as e:
    pytest.skip(
        f"Could not import capsule_metadata module: {e}", allow_module_level=True
    )


class TestCapsuleManagerExtended:
    """Extended test cases for CapsuleManager class"""

    @pytest.fixture
    def capsule_manager(self, temp_dir):
        """Create a CapsuleManager instance for testing"""
        return CapsuleManager(base_dir=temp_dir)

    def test_timestamp(self, capsule_manager):
        """Test timestamp generation"""
        timestamp = capsule_manager.timestamp()
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format includes T between date and time
        assert "Z" in timestamp  # UTC timezone ends with Z

    def test_sha256(self, capsule_manager):
        """Test SHA256 hash generation"""
        test_data = "test data for hashing"
        hash_result = capsule_manager.sha256(test_data)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 hash is 64 hex chars
        assert all(c in "0123456789abcdef" for c in hash_result)

    def test_create_capsule_with_empty_content(self, capsule_manager):
        """Test capsule creation with empty content"""
        capsule_id = "empty_capsule"
        content = ""
        metadata = {"content_type": "empty"}

        capsule = capsule_manager.create_capsule(capsule_id, content, metadata)

        assert capsule["capsule_id"] == capsule_id
        assert capsule["content_hash"] == capsule_manager.sha256(content)
        assert capsule["metadata"] == metadata

    def test_create_capsule_with_binary_content(self, capsule_manager):
        """Test capsule creation with binary content"""
        capsule_id = "binary_capsule"
        # Binary content as bytes
        content = b"Binary content \x00\x01\x02"
        content_str = str(content)
        metadata = {"content_type": "binary"}

        capsule = capsule_manager.create_capsule(capsule_id, content_str, metadata)

        assert capsule["capsule_id"] == capsule_id
        assert capsule["content_hash"] == capsule_manager.sha256(content_str)
        assert capsule["metadata"] == metadata

    def test_update_capsule_index_new_capsule(self, capsule_manager):
        """Test updating index with a new capsule"""
        capsule_id = "new_index_test"
        content = "New capsule for index test"
        capsule = capsule_manager.create_capsule(capsule_id, content, {})

        # Verify index doesn't have the capsule initially
        index_before = capsule_manager.load_index(capsule_manager.capsules_index)
        assert capsule_id not in index_before.get("capsules", {})

        # Update the index
        capsule_manager.update_capsule_index(capsule)

        # Verify capsule is indexed
        index_after = capsule_manager.load_index(capsule_manager.capsules_index)
        assert capsule_id in index_after["capsules"]
        assert "content_hash" in index_after["capsules"][capsule_id]
        assert "created_at" in index_after["capsules"][capsule_id]

    def test_update_capsule_index_existing_capsule(self, capsule_manager):
        """Test updating index with an existing capsule"""
        capsule_id = "existing_index_test"
        content1 = "Original capsule content"
        content2 = "Updated capsule content"
        
        # Create and index first version
        capsule1 = capsule_manager.create_capsule(capsule_id, content1, {})
        capsule_manager.update_capsule_index(capsule1)
        
        # Create and index second version
        capsule2 = capsule_manager.create_capsule(capsule_id, content2, {})
        capsule_manager.update_capsule_index(capsule2)
        
        # Verify index has the updated version
        index = capsule_manager.load_index(capsule_manager.capsules_index)
        assert capsule_id in index["capsules"]
        assert index["capsules"][capsule_id]["content_hash"] == capsule2["content_hash"]

    def test_store_capsule_content(self, capsule_manager):
        """Test storing capsule content"""
        capsule_id = "content_store_test"
        content = "Capsule content for storage test"
        capsule = capsule_manager.create_capsule(capsule_id, content, {})
        
        # Store the content
        result = capsule_manager.store_capsule_content(capsule_id, content)
        assert result is True
        
        # Verify the content file exists
        content_file = Path(capsule_manager.capsules_dir) / f"{capsule_id}.content"
        assert content_file.exists()
        
        # Verify the content is stored correctly
        with open(content_file, "r") as f:
            stored_content = f.read()
            assert stored_content == content

    def test_load_capsule_content(self, capsule_manager):
        """Test loading capsule content"""
        capsule_id = "content_load_test"
        content = "Capsule content for loading test"
        capsule = capsule_manager.create_capsule(capsule_id, content, {})
        capsule_manager.store_capsule_content(capsule_id, content)
        
        # Load the content
        loaded_content = capsule_manager.load_capsule_content(capsule_id)
        assert loaded_content == content
        
        # Test loading non-existent capsule
        non_existent_content = capsule_manager.load_capsule_content("non_existent")
        assert non_existent_content is None

    def test_split_content_to_blocks(self, capsule_manager):
        """Test splitting content into blocks"""
        content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        
        # Split into blocks of 10 bytes
        blocks = capsule_manager.split_content_to_blocks(content, 10)
        assert isinstance(blocks, list)
        assert len(blocks) > 1
        
        # Split with exact block size
        exact_blocks = capsule_manager.split_content_to_blocks("12345", 5)
        assert len(exact_blocks) == 1
        assert exact_blocks[0] == "12345"
        
        # Split empty content
        empty_blocks = capsule_manager.split_content_to_blocks("", 10)
        assert len(empty_blocks) == 0

    def test_create_merkle_tree_empty(self, capsule_manager):
        """Test creating a Merkle tree with empty block list"""
        blocks = []
        tree = capsule_manager.create_merkle_tree(blocks)
        assert tree == {"root_hash": "", "tree_depth": 0, "leaf_count": 0, "nodes": []}

    def test_create_merkle_tree_single_block(self, capsule_manager):
        """Test creating a Merkle tree with a single block"""
        blocks = ["Single block"]
        tree = capsule_manager.create_merkle_tree(blocks)
        
        assert isinstance(tree, dict)
        assert "root_hash" in tree
        assert "tree_depth" in tree
        assert "leaf_count" in tree
        assert "nodes" in tree
        assert tree["leaf_count"] == 1
        assert tree["tree_depth"] == 1
        assert len(tree["nodes"]) == 1

    def test_create_merkle_tree_multiple_blocks(self, capsule_manager):
        """Test creating a Merkle tree with multiple blocks"""
        blocks = ["Block 1", "Block 2", "Block 3", "Block 4"]
        tree = capsule_manager.create_merkle_tree(blocks)
        
        assert isinstance(tree, dict)
        assert "root_hash" in tree
        assert "tree_depth" in tree
        assert "leaf_count" in tree
        assert "nodes" in tree
        assert tree["leaf_count"] == 4
        assert tree["tree_depth"] > 1
        assert len(tree["nodes"]) > 4

    def test_create_archive_with_metadata(self, capsule_manager):
        """Test archive creation with metadata"""
        # Create capsules for archiving
        capsule_ids = []
        for i in range(3):
            capsule_id = f"archive_meta_test_{i}"
            content = f"Archive content with metadata {i}"
            metadata = {"test_key": f"value_{i}", "archive_test": True}
            capsule = capsule_manager.create_capsule(capsule_id, content, metadata)
            capsule_manager.update_capsule_index(capsule)
            capsule_manager.store_capsule_content(capsule_id, content)
            capsule_ids.append(capsule_id)

        # Create archive with metadata
        archive_result = capsule_manager.create_archive(
            "test_archive_with_meta", capsule_ids, include_metadata=True
        )
        
        assert isinstance(archive_result, dict)
        assert archive_result["status"] == "completed"
        assert "archive_file" in archive_result
        assert "archive_hash" in archive_result
        assert "metadata_included" in archive_result
        assert archive_result["metadata_included"] is True

    def test_create_archive_without_metadata(self, capsule_manager):
        """Test archive creation without metadata"""
        # Create capsules for archiving
        capsule_ids = []
        for i in range(2):
            capsule_id = f"archive_no_meta_test_{i}"
            content = f"Archive content without metadata {i}"
            metadata = {"test_key": f"value_{i}", "archive_test": True}
            capsule = capsule_manager.create_capsule(capsule_id, content, metadata)
            capsule_manager.update_capsule_index(capsule)
            capsule_manager.store_capsule_content(capsule_id, content)
            capsule_ids.append(capsule_id)

        # Create archive without metadata
        archive_result = capsule_manager.create_archive(
            "test_archive_without_meta", capsule_ids, include_metadata=False
        )
        
        assert isinstance(archive_result, dict)
        assert archive_result["status"] == "completed"
        assert "archive_file" in archive_result
        assert "archive_hash" in archive_result
        assert "metadata_included" in archive_result
        assert archive_result["metadata_included"] is False

    def test_create_archive_nonexistent_capsules(self, capsule_manager):
        """Test archive creation with nonexistent capsules"""
        archive_result = capsule_manager.create_archive(
            "test_nonexistent_archive", ["nonexistent1", "nonexistent2"]
        )
        
        assert isinstance(archive_result, dict)
        assert archive_result["status"] == "error"
        assert "message" in archive_result

    def test_verify_capsule_integrity_errors(self, capsule_manager):
        """Test capsule integrity verification with potential errors"""
        # Create a capsule
        capsule_id = "integrity_error_test"
        content = "Content for integrity error testing"
        capsule = capsule_manager.create_capsule(capsule_id, content, {})
        capsule_manager.update_capsule_index(capsule)
        capsule_manager.store_capsule_content(capsule_id, content)
        
        # Test with content mismatch
        with patch.object(capsule_manager, 'load_capsule_content', return_value="Tampered content"):
            verification = capsule_manager.verify_capsule_integrity(capsule_id)
            assert verification["overall_valid"] is False
            assert verification["content_hash_valid"] is False
        
        # Test with missing content file
        with patch.object(capsule_manager, 'load_capsule_content', return_value=None):
            verification = capsule_manager.verify_capsule_integrity(capsule_id)
            assert verification["overall_valid"] is False
            assert "content_missing" in verification

    def test_export_capsules(self, capsule_manager):
        """Test exporting capsules"""
        # Create capsules for export
        capsule_ids = []
        for i in range(2):
            capsule_id = f"export_test_{i}"
            content = f"Export content {i}"
            metadata = {"export_test": True}
            capsule = capsule_manager.create_capsule(capsule_id, content, metadata)
            capsule_manager.update_capsule_index(capsule)
            capsule_manager.store_capsule_content(capsule_id, content)
            capsule_ids.append(capsule_id)
        
        # Export capsules to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            export_path = tmp.name
            
        export_result = capsule_manager.export_capsules(capsule_ids, export_path)
        
        assert isinstance(export_result, dict)
        assert export_result["status"] == "completed"
        assert "export_file" in export_result
        assert export_result["export_file"] == export_path
        
        # Clean up
        os.unlink(export_path)

    def test_verify_archive_integrity(self, capsule_manager):
        """Test verifying archive integrity"""
        # Create capsules for archiving
        capsule_ids = []
        for i in range(2):
            capsule_id = f"verify_archive_test_{i}"
            content = f"Archive verification content {i}"
            capsule = capsule_manager.create_capsule(capsule_id, content, {})
            capsule_manager.update_capsule_index(capsule)
            capsule_manager.store_capsule_content(capsule_id, content)
            capsule_ids.append(capsule_id)

        # Create archive
        archive_result = capsule_manager.create_archive("verify_test_archive", capsule_ids)
        
        if archive_result["status"] == "completed":
            # Verify the archive
            verification = capsule_manager.verify_archive_integrity(archive_result["archive_file"])
            
            assert isinstance(verification, dict)
            assert "valid" in verification
            assert verification["valid"] is True
        
        # Test with nonexistent archive
        verification = capsule_manager.verify_archive_integrity("nonexistent_archive.zip")
        assert isinstance(verification, dict)
        assert "valid" in verification
        assert verification["valid"] is False
        assert "error" in verification


def test_main_function():
    """Test the main CLI function"""
    
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('capsule_metadata.CapsuleManager') as MockManager, \
         patch('builtins.print') as mock_print, \
         patch('json.dumps', return_value="{}"):
        
        # Test create command
        mock_args.return_value.create = True
        mock_args.return_value.capsule_id = "test_capsule"
        mock_args.return_value.content = "Test content"
        mock_args.return_value.metadata = '{"test": true}'
        mock_args.return_value.list = False
        mock_args.return_value.verify = None
        mock_args.return_value.archive = None
        
        mock_instance = MockManager.return_value
        mock_instance.create_capsule.return_value = {
            "capsule_id": "test_capsule",
            "content_hash": "hash",
            "created_at": "time"
        }
        
        main()
        
        mock_instance.create_capsule.assert_called_once()
        mock_instance.update_capsule_index.assert_called_once()
        mock_instance.store_capsule_content.assert_called_once()
        assert mock_print.called
        
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('capsule_metadata.CapsuleManager') as MockManager, \
         patch('builtins.print') as mock_print, \
         patch('json.dumps', return_value="{}"):
        
        # Test list command
        mock_args.return_value.create = False
        mock_args.return_value.list = True
        mock_args.return_value.verify = None
        mock_args.return_value.archive = None
        
        mock_instance = MockManager.return_value
        mock_instance.list_capsules.return_value = [
            {"capsule_id": "test1", "content_hash": "hash1"},
            {"capsule_id": "test2", "content_hash": "hash2"}
        ]
        
        main()
        
        mock_instance.list_capsules.assert_called_once()
        assert mock_print.called
        
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('capsule_metadata.CapsuleManager') as MockManager, \
         patch('builtins.print') as mock_print, \
         patch('json.dumps', return_value="{}"):
        
        # Test verify command
        mock_args.return_value.create = False
        mock_args.return_value.list = False
        mock_args.return_value.verify = "test_capsule"
        mock_args.return_value.archive = None
        
        mock_instance = MockManager.return_value
        mock_instance.verify_capsule_integrity.return_value = {
            "overall_valid": True,
            "content_hash_valid": True
        }
        
        main()
        
        mock_instance.verify_capsule_integrity.assert_called_once_with("test_capsule")
        assert mock_print.called
        
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('capsule_metadata.CapsuleManager') as MockManager, \
         patch('builtins.print') as mock_print, \
         patch('json.dumps', return_value="{}"):
        
        # Test archive command
        mock_args.return_value.create = False
        mock_args.return_value.list = False
        mock_args.return_value.verify = None
        mock_args.return_value.archive = True
        mock_args.return_value.archive_name = "test_archive"
        mock_args.return_value.capsule_ids = ["test1", "test2"]
        
        mock_instance = MockManager.return_value
        mock_instance.create_archive.return_value = {
            "status": "completed",
            "archive_file": "test_archive.zip",
            "archive_hash": "hash"
        }
        
        main()
        
        mock_instance.create_archive.assert_called_once_with(
            "test_archive", ["test1", "test2"], include_metadata=False
        )
        assert mock_print.called
