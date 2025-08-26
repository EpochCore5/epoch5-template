#!/usr/bin/env python3
"""
Test configuration and utilities for EPOCH5 Template
"""

import os
import tempfile
import shutil
import pytest
from pathlib import Path
from typing import Generator, Dict, Any

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "data"
TEMP_DIR = Path(tempfile.gettempdir()) / "epoch5_tests"

@pytest.fixture(scope="session")
def test_data_dir():
    """Provide path to test data directory"""
    return TEST_DATA_DIR

@pytest.fixture(scope="function")
def temp_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace for each test"""
    workspace = TEMP_DIR / f"test_{os.getpid()}"
    workspace.mkdir(parents=True, exist_ok=True)
    
    # Change to temp directory for test
    original_cwd = os.getcwd()
    os.chdir(workspace)
    
    try:
        yield workspace
    finally:
        os.chdir(original_cwd)
        if workspace.exists():
            shutil.rmtree(workspace, ignore_errors=True)

@pytest.fixture(scope="function")
def mock_archive_structure(temp_workspace: Path) -> Path:
    """Create mock archive directory structure"""
    archive_dir = temp_workspace / "archive" / "EPOCH5"
    manifests_dir = archive_dir / "manifests"
    
    manifests_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock files
    (archive_dir / "ledger.txt").touch()
    (archive_dir / "heartbeat.log").touch()
    (archive_dir / "unity_seal.txt").touch()
    
    return archive_dir

@pytest.fixture(scope="function") 
def sample_agent_data() -> Dict[str, Any]:
    """Provide sample agent data for testing"""
    return {
        "did": "did:epoch5:agent:test123",
        "skills": ["data_processing", "validation"],
        "status": "active",
        "reliability_score": 0.95,
        "created_at": "2024-01-01T00:00:00Z",
        "last_heartbeat": "2024-01-01T12:00:00Z"
    }

@pytest.fixture(scope="function")
def sample_dag_data() -> Dict[str, Any]:
    """Provide sample DAG data for testing"""
    return {
        "dag_id": "test_dag",
        "tasks": {
            "task1": {
                "task_id": "task1",
                "dependencies": [],
                "status": "pending",
                "assigned_agent": None
            },
            "task2": {
                "task_id": "task2", 
                "dependencies": ["task1"],
                "status": "pending",
                "assigned_agent": None
            }
        },
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z"
    }

class TestHelpers:
    """Test utility functions"""
    
    @staticmethod
    def create_test_manifest(workspace: Path, pass_id: str, content: str) -> Path:
        """Create a test manifest file"""
        manifests_dir = workspace / "archive" / "EPOCH5" / "manifests"
        manifests_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_file = manifests_dir / f"{pass_id}_manifest.txt"
        manifest_file.write_text(f"""EPOCH 5 MANIFEST
================
ARC_ID: TEST-ARC
PASS_ID: {pass_id}
TIMESTAMP: 2024-01-01T00:00:00Z
TITLE: Test Pass
CONTENT_HASH: test_hash
PREV_HASH: prev_test_hash
RECORD_HASH: record_test_hash

PAYLOAD:
{content}

FOUNDER_NOTE:
Test manifest for automated testing
""")
        return manifest_file
    
    @staticmethod
    def create_test_ledger(workspace: Path, entries: list) -> Path:
        """Create a test ledger file"""
        archive_dir = workspace / "archive" / "EPOCH5"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        ledger_file = archive_dir / "ledger.txt"
        with ledger_file.open('w') as f:
            for entry in entries:
                f.write(f"{entry}\n")
        
        return ledger_file
    
    @staticmethod
    def verify_hash_chain(ledger_path: Path) -> bool:
        """Verify hash chain integrity in ledger"""
        if not ledger_path.exists():
            return False
            
        entries = ledger_path.read_text().strip().split('\n')
        if not entries:
            return True
            
        # Simplified hash chain verification
        for i, entry in enumerate(entries):
            if '|RECORD_HASH=' not in entry:
                return False
                
        return True