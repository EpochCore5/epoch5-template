"""
Tests for meta_capsule functionality
"""

import pytest
import json
import tempfile
import zipfile
import hashlib
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
import os
from datetime import datetime, timezone

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from meta_capsule import MetaCapsuleCreator, main
except ImportError as e:
    pytest.skip(f"Could not import meta_capsule module: {e}", allow_module_level=True)


class TestMetaCapsuleCreator:
    """Test cases for MetaCapsuleCreator class"""
    
    @pytest.fixture
    def meta_capsule_instance(self, temp_dir):
        """Create a MetaCapsuleCreator instance for testing"""
        # Create necessary directory structure
        meta_dir = Path(temp_dir) / "meta_capsules"
        meta_dir.mkdir(parents=True, exist_ok=True)
        
        (Path(temp_dir) / "meta_capsules" / "state_snapshots").mkdir(parents=True, exist_ok=True)
        
        # Mock the dependent modules
        with patch('meta_capsule.AgentManager', MagicMock()), \
             patch('meta_capsule.PolicyManager', MagicMock()), \
             patch('meta_capsule.DAGManager', MagicMock()), \
             patch('meta_capsule.CycleExecutor', MagicMock()), \
             patch('meta_capsule.CapsuleManager', MagicMock()):
            
            instance = MetaCapsuleCreator(base_dir=temp_dir)
            
            # Setup mock manager behavior
            if instance.agent_manager:
                instance.agent_manager.load_registry.return_value = {"agents": {"agent1": {}, "agent2": {}}}
                instance.agent_manager.get_active_agents.return_value = ["agent1", "agent2"]
            
            if instance.policy_manager:
                instance.policy_manager.load_policies.return_value = {"policies": {"policy1": {}, "policy2": {}}}
                instance.policy_manager.load_grants.return_value = {"grants": {"grant1": {}, "grant2": {}}}
                instance.policy_manager.get_active_policies.return_value = ["policy1"]
            
            if instance.dag_manager:
                instance.dag_manager.load_dags.return_value = {"dags": {"dag1": {"status": "completed"}, "dag2": {"status": "in_progress"}}}
            
            if instance.cycle_executor:
                instance.cycle_executor.load_cycles.return_value = {"cycles": {"cycle1": {"status": "completed"}, "cycle2": {"status": "in_progress"}}}
            
            if instance.capsule_manager:
                instance.capsule_manager.list_capsules.return_value = ["capsule1", "capsule2"]
                instance.capsule_manager.list_archives.return_value = ["archive1"]
            
            return instance
    
    @pytest.fixture
    def ledger_file(self, temp_dir):
        """Create a test ledger file"""
        ledger_file = Path(temp_dir) / "ledger.log"
        with open(ledger_file, "w") as f:
            f.write("TIMESTAMP=2024-01-01T00:00:00Z|TYPE=RECORD|ID=test1|RECORD_HASH=1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef\n")
            f.write("TIMESTAMP=2024-01-02T00:00:00Z|TYPE=RECORD|ID=test2|RECORD_HASH=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890\n")
        return ledger_file
    
    @pytest.fixture
    def sample_meta_capsule(self):
        """Sample meta capsule data for testing"""
        return {
            "meta_capsule_id": "test_meta_001",
            "created_at": "2024-01-01T00:00:00Z",
            "description": "Test meta-capsule",
            "version": "1.0",
            "type": "EPOCH5_META_CAPSULE",
            "system_state": {
                "captured_at": "2024-01-01T00:00:00Z",
                "systems": {"test": {"data": "test"}},
                "file_hashes": {"test.json": "hash123"},
                "summary_stats": {
                    "total_files_captured": 1,
                    "systems_captured": 1,
                    "capture_timestamp": "2024-01-01T00:00:00Z",
                    "state_hash": "statehash123"
                }
            },
            "provenance_chain": [],
            "integrity_verification": {},
            "meta_hash": "metahash123",
            "archive_info": {
                "archive_id": "test_meta_001_system_archive",
                "created_at": "2024-01-01T00:00:00Z",
                "archive_file": "/tmp/test_meta_001_system_archive.zip",
                "status": "completed",
                "file_count": 5,
                "total_size": 1024,
                "archive_hash": "archivehash123"
            },
            "ledger_update": {
                "main_ledger_updated": True,
                "meta_ledger_updated": True,
                "ledger_entry_hash": "ledgerhash123",
                "prev_hash": "prevhash123",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    
    def test_initialization(self, meta_capsule_instance):
        """Test that MetaCapsuleCreator initializes correctly"""
        assert meta_capsule_instance is not None
        assert isinstance(meta_capsule_instance.base_dir, Path)
        assert isinstance(meta_capsule_instance.meta_dir, Path)
        assert meta_capsule_instance.meta_dir.exists()
        assert meta_capsule_instance.state_snapshots.exists()
        
        # Check that manager instances were initialized
        if hasattr(meta_capsule_instance, 'agent_manager'):
            assert meta_capsule_instance.agent_manager is not None
        if hasattr(meta_capsule_instance, 'policy_manager'):
            assert meta_capsule_instance.policy_manager is not None
        if hasattr(meta_capsule_instance, 'dag_manager'):
            assert meta_capsule_instance.dag_manager is not None
        if hasattr(meta_capsule_instance, 'cycle_executor'):
            assert meta_capsule_instance.cycle_executor is not None
        if hasattr(meta_capsule_instance, 'capsule_manager'):
            assert meta_capsule_instance.capsule_manager is not None

    def test_timestamp(self, meta_capsule_instance):
        """Test timestamp functionality"""
        timestamp = meta_capsule_instance.timestamp()
        assert isinstance(timestamp, str)
        assert 'T' in timestamp  # ISO format contains T between date and time
        assert 'Z' in timestamp  # UTC timezone ends with Z
        
        # Verify format by attempting to parse it
        try:
            datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
            is_valid_format = True
        except ValueError:
            is_valid_format = False
        
        assert is_valid_format

    def test_sha256(self, meta_capsule_instance):
        """Test sha256 functionality"""
        test_data = "test data for hashing"
        hash_result = meta_capsule_instance.sha256(test_data)
        
        # Verify the hash is correct
        expected_hash = hashlib.sha256(test_data.encode("utf-8")).hexdigest()
        assert hash_result == expected_hash
        
        # Verify hash properties
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 produces a 64-character hex string
        assert all(c in "0123456789abcdef" for c in hash_result)  # Only hex characters

    def test_capture_system_state(self, meta_capsule_instance):
        """Test capture_system_state functionality"""
        # Set up mock file structure
        agents_dir = Path(meta_capsule_instance.base_dir) / "agents"
        agents_dir.mkdir(exist_ok=True)
        with open(agents_dir / "agent1.json", "w") as f:
            f.write('{"id": "agent1", "status": "active"}')
        
        # Mock system-specific methods
        with patch('pathlib.Path.glob') as mock_glob, \
             patch('builtins.open', mock_open(read_data='{"test": "data"}')):
            
            # Simulate file discovery via glob
            mock_glob.return_value = [agents_dir / "agent1.json"]
            
            # Capture system state
            state = meta_capsule_instance.capture_system_state()
            
            # Verify state structure
            assert isinstance(state, dict)
            assert "captured_at" in state
            assert "systems" in state
            assert "file_hashes" in state
            assert "summary_stats" in state
            
            # Verify summary stats
            assert "total_files_captured" in state["summary_stats"]
            assert "systems_captured" in state["summary_stats"]
            assert "capture_timestamp" in state["summary_stats"]
            assert "state_hash" in state["summary_stats"]
            
            # If agent manager is mocked properly, verify agent data
            if meta_capsule_instance.agent_manager and "agents" in state["systems"]:
                assert "registry" in state["systems"]["agents"]
                assert "active_agents" in state["systems"]["agents"]
                assert "total_agents" in state["systems"]["agents"]

    def test_capture_epoch5_base_state(self, meta_capsule_instance, ledger_file):
        """Test capture_epoch5_base_state functionality"""
        # Create sample base files for testing
        base_dir = meta_capsule_instance.base_dir
        
        # Create heartbeat file
        with open(base_dir / "heartbeat.log", "w") as f:
            f.write("HEARTBEAT|2024-01-01T00:00:00Z\n")
            f.write("HEARTBEAT|2024-01-01T00:01:00Z\n")
        
        # Create manifests directory and file
        manifests_dir = base_dir / "manifests"
        manifests_dir.mkdir(exist_ok=True)
        with open(manifests_dir / "manifest1.txt", "w") as f:
            f.write("MANIFEST CONTENT")
        
        # Create unity seal
        with open(base_dir / "unity_seal.txt", "w") as f:
            f.write("UNITY SEAL CONTENT")
        
        # Capture base state
        base_state = meta_capsule_instance.capture_epoch5_base_state()
        
        # Verify state structure
        assert isinstance(base_state, dict)
        assert "ledger" in base_state
        assert "heartbeat" in base_state
        assert "manifests" in base_state
        assert "unity_seal" in base_state
        
        # Verify ledger state
        assert base_state["ledger"]["exists"] is True
        assert base_state["ledger"]["entries"] == 2
        assert base_state["ledger"]["hash"] is not None
        
        # Verify heartbeat state
        assert base_state["heartbeat"]["exists"] is True
        assert base_state["heartbeat"]["entries"] == 2
        
        # Verify manifests state
        assert base_state["manifests"]["count"] == 1
        assert "manifest1.txt" in base_state["manifests"]["files"]
        
        # Verify unity seal state
        assert base_state["unity_seal"]["exists"] is True
        assert base_state["unity_seal"]["hash"] is not None

    def test_create_meta_capsule(self, meta_capsule_instance):
        """Test create_meta_capsule functionality"""
        # Mock methods that are called during meta capsule creation
        with patch.object(meta_capsule_instance, 'capture_system_state') as mock_capture, \
             patch.object(meta_capsule_instance, 'build_provenance_chain') as mock_provenance, \
             patch.object(meta_capsule_instance, 'create_integrity_verification') as mock_integrity, \
             patch.object(meta_capsule_instance, 'create_system_archive') as mock_archive, \
             patch.object(meta_capsule_instance, 'update_ledger_with_meta_capsule') as mock_update, \
             patch.object(meta_capsule_instance, 'log_meta_event') as mock_log, \
             patch('builtins.open', mock_open()) as mock_file:
            
            # Setup mock returns
            mock_capture.return_value = {
                "captured_at": "2024-01-01T00:00:00Z",
                "systems": {"test": {}},
                "file_hashes": {"test.json": "hash123"},
                "summary_stats": {
                    "total_files_captured": 1,
                    "systems_captured": 1,
                    "capture_timestamp": "2024-01-01T00:00:00Z",
                    "state_hash": "statehash123"
                }
            }
            mock_provenance.return_value = []
            mock_integrity.return_value = {"combined_hash": "integrity123"}
            mock_archive.return_value = {
                "archive_id": "test_meta_001_system_archive",
                "created_at": "2024-01-01T00:00:00Z",
                "status": "completed",
                "file_count": 5,
                "archive_hash": "archivehash123"
            }
            
            # Create meta capsule
            meta_capsule = meta_capsule_instance.create_meta_capsule("test_meta_001", "Test meta-capsule")
            
            # Verify meta capsule structure
            assert meta_capsule is not None
            assert meta_capsule["meta_capsule_id"] == "test_meta_001"
            assert "created_at" in meta_capsule
            assert meta_capsule["description"] == "Test meta-capsule"
            assert meta_capsule["version"] == "1.0"
            assert meta_capsule["type"] == "EPOCH5_META_CAPSULE"
            assert "system_state" in meta_capsule
            assert "provenance_chain" in meta_capsule
            assert "integrity_verification" in meta_capsule
            assert "meta_hash" in meta_capsule
            assert "archive_info" in meta_capsule
            
            # Verify method calls
            mock_capture.assert_called_once()
            mock_provenance.assert_called_once()
            mock_integrity.assert_called_once()
            mock_archive.assert_called_once_with("test_meta_001")
            mock_update.assert_called_once()
            mock_log.assert_called_once()
            
            # Verify file operations
            meta_file_calls = [call for call in mock_file.mock_calls if "test_meta_001.json" in str(call)]
            assert len(meta_file_calls) > 0
            
            snapshot_file_calls = [call for call in mock_file.mock_calls if "test_meta_001_snapshot.json" in str(call)]
            assert len(snapshot_file_calls) > 0

    def test_build_provenance_chain(self, meta_capsule_instance, ledger_file):
        """Test build_provenance_chain functionality"""
        # Build provenance chain from test ledger
        provenance = meta_capsule_instance.build_provenance_chain()
        
        # Verify provenance structure
        assert isinstance(provenance, list)
        assert len(provenance) == 2  # Two entries in test ledger
        
        # Verify provenance content
        assert provenance[0]["line_number"] == 1
        assert "raw_entry" in provenance[0]
        assert "record_hash" in provenance[0]
        assert provenance[0]["record_hash"] == "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        
        assert provenance[1]["line_number"] == 2
        assert "raw_entry" in provenance[1]
        assert "record_hash" in provenance[1]
        assert provenance[1]["record_hash"] == "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"

    def test_create_integrity_verification(self, meta_capsule_instance, sample_meta_capsule):
        """Test create_integrity_verification functionality"""
        # Create integrity verification
        verification = meta_capsule_instance.create_integrity_verification(sample_meta_capsule)
        
        # Verify structure
        assert isinstance(verification, dict)
        assert "created_at" in verification
        assert "verification_method" in verification
        assert verification["verification_method"] == "SHA256_CHAIN_MERKLE"
        assert "system_hashes" in verification
        assert "provenance_hash" in verification
        assert "combined_hash" in verification
        
        # Verify hash is a valid SHA-256 hash
        assert isinstance(verification["combined_hash"], str)
        assert len(verification["combined_hash"]) == 64
        assert all(c in "0123456789abcdef" for c in verification["combined_hash"])

    def test_create_system_archive(self, meta_capsule_instance):
        """Test create_system_archive functionality"""
        # Setup mock directories and files
        for dir_name in ["agents", "policies", "dags", "cycles", "capsules", "metadata", "archives", "manifests"]:
            dir_path = meta_capsule_instance.base_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            with open(dir_path / f"test_{dir_name}.json", "w") as f:
                f.write(f'{{"{dir_name}": "test"}}')
        
        # Create base files
        for file_name in ["ledger.log", "heartbeat.log", "incoming_tide.log", "unity_seal.txt"]:
            with open(meta_capsule_instance.base_dir / file_name, "w") as f:
                f.write(f"{file_name} content")
        
        # Mock Path.is_file to return True for our test files
        with patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.rglob') as mock_rglob, \
             patch('zipfile.ZipFile') as mock_zipfile:
            
            # Setup mock zipfile instance
            mock_zip_instance = MagicMock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            
            # Setup rglob to return some test files
            mock_file1 = MagicMock()
            mock_file1.is_file.return_value = True
            mock_file1.name = "test_file1.json"
            
            mock_file2 = MagicMock()
            mock_file2.is_file.return_value = True
            mock_file2.name = "test_file2.json"
            
            mock_rglob.return_value = [mock_file1, mock_file2]
            
            # Mock Path.stat to return file size
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value = MagicMock(st_size=1024)
                
                # Mock file reading for hash calculation
                with patch('builtins.open', mock_open(read_data=b'test archive content')):
                    
                    # Create system archive
                    archive_info = meta_capsule_instance.create_system_archive("test_meta_001")
                    
                    # Verify archive info structure
                    assert isinstance(archive_info, dict)
                    assert archive_info["archive_id"] == "test_meta_001_system_archive"
                    assert "created_at" in archive_info
                    assert "archive_file" in archive_info
                    assert "included_directories" in archive_info
                    assert "file_count" in archive_info
                    assert "total_size" in archive_info
                    assert "archive_hash" in archive_info
                    assert "status" in archive_info
                    
                    # Verify zipfile operations
                    assert mock_zipfile.called

    def test_update_ledger_with_meta_capsule(self, meta_capsule_instance, sample_meta_capsule):
        """Test update_ledger_with_meta_capsule functionality"""
        # Mock get_previous_hash method
        with patch.object(meta_capsule_instance, 'get_previous_hash') as mock_prev_hash, \
             patch('builtins.open', mock_open()) as mock_file:
            
            mock_prev_hash.return_value = "prev_hash_123"
            
            # Update ledger with meta capsule
            meta_capsule_instance.update_ledger_with_meta_capsule(sample_meta_capsule)
            
            # Verify get_previous_hash was called
            mock_prev_hash.assert_called_once()
            
            # Verify file operations
            # Should have two open calls - one for main ledger, one for meta ledger
            ledger_write_calls = [call for call in mock_file.mock_calls if 'write' in str(call)]
            assert len(ledger_write_calls) >= 2
            
            # Check the main ledger entry has required fields - we'll only check for PREV_HASH in the main ledger entry
            main_ledger_entry = None
            meta_ledger_entry = None
            
            for call in ledger_write_calls:
                call_args = call[1][0]
                assert isinstance(call_args, str)
                
                if "TYPE=META_CAPSULE" in call_args:
                    main_ledger_entry = call_args
                elif "META_CAPSULE_ID" in call_args:
                    meta_ledger_entry = call_args
            
            # Verify main ledger entry format
            if main_ledger_entry:
                assert "TIMESTAMP=" in main_ledger_entry
                assert "META_CAPSULE" in main_ledger_entry
                assert "META_HASH=" in main_ledger_entry
                assert "PREV_HASH=" in main_ledger_entry
                assert "RECORD_HASH=" in main_ledger_entry
            
            # Verify meta ledger entry format
            if meta_ledger_entry:
                assert "TIMESTAMP=" in meta_ledger_entry
                assert "META_CAPSULE_ID=" in meta_ledger_entry
                assert "META_HASH=" in meta_ledger_entry
                assert "SYSTEMS_COUNT=" in meta_ledger_entry
                assert "RECORD_HASH=" in meta_ledger_entry

    def test_get_previous_hash(self, meta_capsule_instance, ledger_file):
        """Test get_previous_hash functionality"""
        # Get previous hash from ledger
        prev_hash = meta_capsule_instance.get_previous_hash()
        
        # Verify it's the hash from the last ledger entry
        assert prev_hash == "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        
        # Test with non-existent ledger
        with patch.object(meta_capsule_instance, 'ledger_file', Path('/nonexistent/path')):
            genesis_hash = meta_capsule_instance.get_previous_hash()
            assert genesis_hash == "0" * 64  # Genesis hash for new ledger

    def test_verify_meta_capsule(self, meta_capsule_instance, sample_meta_capsule):
        """Test verify_meta_capsule functionality"""
        meta_id = sample_meta_capsule["meta_capsule_id"]
        
        # Mock file operations and verification methods
        with patch('pathlib.Path.exists') as mock_exists, \
             patch('builtins.open', mock_open(read_data=json.dumps(sample_meta_capsule))), \
             patch.object(meta_capsule_instance, 'verify_ledger_entry') as mock_verify_ledger, \
             patch('hashlib.sha256') as mock_sha256:
            
            # Setup mock hashlib.sha256 to avoid TypeError with string encoding
            mock_hash = MagicMock()
            mock_hash.hexdigest.return_value = "calculated_hash_123"
            mock_sha256.return_value = mock_hash
            
            mock_exists.return_value = True
            mock_verify_ledger.return_value = True
            
            # Verify meta capsule
            result = meta_capsule_instance.verify_meta_capsule(meta_id)
            
            # Verify result structure
            assert isinstance(result, dict)
            assert result["meta_capsule_id"] == meta_id
            assert "verified_at" in result
            assert "integrity_valid" in result
            assert "archive_valid" in result
            assert "ledger_consistent" in result
            assert "details" in result
            
            # Test with non-existent meta capsule
            mock_exists.return_value = False
            not_found_result = meta_capsule_instance.verify_meta_capsule("nonexistent")
            assert "error" in not_found_result
            assert not_found_result["error"] == "Meta-capsule not found"

    def test_verify_ledger_entry(self, meta_capsule_instance, sample_meta_capsule, ledger_file):
        """Test verify_ledger_entry functionality"""
        # Create a ledger entry for the sample meta capsule
        meta_id = sample_meta_capsule["meta_capsule_id"]
        meta_hash = sample_meta_capsule["meta_hash"]
        
        with open(ledger_file, "a") as f:
            f.write(f"TIMESTAMP=2024-01-03T00:00:00Z|TYPE=META_CAPSULE|META_ID={meta_id}|META_HASH={meta_hash}|PREV_HASH=prevhash|RECORD_HASH=recordhash\n")
        
        # Verify ledger entry
        result = meta_capsule_instance.verify_ledger_entry(sample_meta_capsule)
        assert result is True
        
        # Test with meta capsule not in ledger
        sample_meta_capsule["meta_hash"] = "different_hash"
        result = meta_capsule_instance.verify_ledger_entry(sample_meta_capsule)
        assert result is False
        
        # Test with non-existent ledger
        with patch.object(meta_capsule_instance, 'ledger_file', Path('/nonexistent/path')):
            result = meta_capsule_instance.verify_ledger_entry(sample_meta_capsule)
            assert result is False

    def test_log_meta_event(self, meta_capsule_instance):
        """Test log_meta_event functionality"""
        # Mock file operations
        with patch('builtins.open', mock_open()) as mock_file:
            # Log meta event
            meta_capsule_instance.log_meta_event(
                "test_meta_001", 
                "TEST_EVENT", 
                {"test": "data"}
            )
            
            # Verify file operations
            mock_file.assert_called_once()
            write_calls = [call for call in mock_file.mock_calls if 'write' in str(call)]
            assert len(write_calls) == 1
            
            # Verify log entry format
            log_entry = write_calls[0][1][0]
            assert isinstance(log_entry, str)
            
            # Parse the JSON to verify structure
            entry_data = json.loads(log_entry)
            assert "timestamp" in entry_data
            assert entry_data["meta_capsule_id"] == "test_meta_001"
            assert entry_data["event"] == "TEST_EVENT"
            assert entry_data["data"] == {"test": "data"}
            assert "hash" in entry_data

    def test_list_meta_capsules(self, meta_capsule_instance, sample_meta_capsule):
        """Test list_meta_capsules functionality"""
        # Create sample meta capsule files
        meta_dir = meta_capsule_instance.meta_dir
        
        # Mock glob and file operations
        with patch('pathlib.Path.glob') as mock_glob, \
             patch('builtins.open', mock_open(read_data=json.dumps(sample_meta_capsule))):
            
            # Setup mock glob to return sample files
            mock_glob.return_value = [
                meta_dir / "test_meta_001.json",
                meta_dir / "test_meta_002.json"
            ]
            
            # List meta capsules
            meta_capsules = meta_capsule_instance.list_meta_capsules()
            
            # Verify result
            assert isinstance(meta_capsules, list)
            assert len(meta_capsules) == 2
            
            # Verify each meta capsule entry
            for mc in meta_capsules:
                assert "meta_capsule_id" in mc
                assert "created_at" in mc
                assert "systems_captured" in mc
                assert "files_captured" in mc
                assert "meta_hash" in mc
            
            # Test with invalid file
            with patch('builtins.open', mock_open()) as mock_file:
                mock_file.side_effect = Exception("Error reading file")
                empty_list = meta_capsule_instance.list_meta_capsules()
                assert isinstance(empty_list, list)
                assert len(empty_list) == 0


def test_main():
    """Test main functionality"""
    # Test create command
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('meta_capsule.MetaCapsuleCreator') as MockCreator, \
         patch('builtins.print') as mock_print:
        
        # Setup mock args for create command
        mock_args.return_value.command = 'create'
        mock_args.return_value.meta_capsule_id = 'test_meta_001'
        mock_args.return_value.description = 'Test description'
        
        # Setup mock creator
        mock_instance = MockCreator.return_value
        mock_instance.create_meta_capsule.return_value = {
            'meta_capsule_id': 'test_meta_001',
            'meta_hash': 'hash123',
            'system_state': {
                'systems': {'test': {}},
                'summary_stats': {'total_files_captured': 10}
            },
            'archive_info': {
                'status': 'completed',
                'file_count': 5,
                'total_size': 1024
            }
        }
        
        # Run main function
        main()
        
        # Verify MetaCapsuleCreator was instantiated
        MockCreator.assert_called_once()
        
        # Verify create_meta_capsule was called
        mock_instance.create_meta_capsule.assert_called_once_with('test_meta_001', 'Test description')
        
        # Verify print was called
        assert mock_print.called
    
    # Test verify command
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('meta_capsule.MetaCapsuleCreator') as MockCreator, \
         patch('builtins.print') as mock_print:
        
        # Setup mock args for verify command
        mock_args.return_value.command = 'verify'
        mock_args.return_value.meta_capsule_id = 'test_meta_001'
        
        # Setup mock creator
        mock_instance = MockCreator.return_value
        mock_instance.verify_meta_capsule.return_value = {
            'meta_capsule_id': 'test_meta_001',
            'integrity_valid': True,
            'archive_valid': True,
            'ledger_consistent': True
        }
        
        # Run main function
        main()
        
        # Verify verify_meta_capsule was called
        mock_instance.verify_meta_capsule.assert_called_once_with('test_meta_001')
        
        # Verify print was called
        assert mock_print.called
    
    # Test list command
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('meta_capsule.MetaCapsuleCreator') as MockCreator, \
         patch('builtins.print') as mock_print:
        
        # Setup mock args for list command
        mock_args.return_value.command = 'list'
        
        # Setup mock creator
        mock_instance = MockCreator.return_value
        mock_instance.list_meta_capsules.return_value = [
            {
                'meta_capsule_id': 'test_meta_001',
                'created_at': '2024-01-01T00:00:00Z',
                'systems_captured': 5,
                'files_captured': 10,
                'meta_hash': 'hash123'
            },
            {
                'meta_capsule_id': 'test_meta_002',
                'created_at': '2024-01-02T00:00:00Z',
                'systems_captured': 6,
                'files_captured': 12,
                'meta_hash': 'hash456'
            }
        ]
        
        # Run main function
        main()
        
        # Verify list_meta_capsules was called
        mock_instance.list_meta_capsules.assert_called_once()
        
        # Verify print was called
        assert mock_print.called
    
    # Test state command
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('meta_capsule.MetaCapsuleCreator') as MockCreator, \
         patch('builtins.print') as mock_print:
        
        # Setup mock args for state command
        mock_args.return_value.command = 'state'
        
        # Setup mock creator
        mock_instance = MockCreator.return_value
        mock_instance.capture_system_state.return_value = {
            'captured_at': '2024-01-01T00:00:00Z',
            'systems': {'test1': {}, 'test2': {}},
            'file_hashes': {'file1.json': 'hash1', 'file2.json': 'hash2'},
            'summary_stats': {
                'state_hash': 'statehash123'
            }
        }
        
        # Run main function
        main()
        
        # Verify capture_system_state was called
        mock_instance.capture_system_state.assert_called_once()
        
        # Verify print was called
        assert mock_print.called
        
    # Test unknown command
    with patch('argparse.ArgumentParser.parse_args') as mock_args, \
         patch('meta_capsule.MetaCapsuleCreator') as MockCreator, \
         patch('argparse.ArgumentParser.print_help') as mock_help:
        
        # Setup mock args for unknown command
        mock_args.return_value.command = None
        
        # Run main function
        main()
        
        # Verify print_help was called
        mock_help.assert_called_once()
