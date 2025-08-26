#!/usr/bin/env python3
"""
EPOCH5 Merkle Tree and Capsule Tests
Comprehensive tests for the enhanced Merkle tree and capsule management functionality.
"""

import unittest
import tempfile
import shutil
from pathlib import Path

# Import the components we want to test
from capsule_metadata import MerkleTree, CapsuleManager
from epoch5_utils import sha256


class TestMerkleTreeEnhanced(unittest.TestCase):
    """Enhanced test cases for Merkle tree functionality"""
    
    def test_merkle_tree_creation(self):
        """Test basic Merkle tree creation"""
        blocks = ["block1", "block2", "block3", "block4"]
        tree = MerkleTree(blocks)
        
        # Check tree structure
        self.assertEqual(len(tree.data_blocks), 4)
        self.assertEqual(len(tree.tree_levels), 3)  # Leaf, intermediate, root
        self.assertIsInstance(tree.root_hash, str)
        self.assertEqual(len(tree.root_hash), 64)  # SHA256 produces 64 hex chars
    
    def test_merkle_tree_odd_blocks(self):
        """Test Merkle tree with odd number of blocks"""
        blocks = ["block1", "block2", "block3"]
        tree = MerkleTree(blocks)
        
        self.assertEqual(len(tree.data_blocks), 3)
        self.assertIsInstance(tree.root_hash, str)
        self.assertEqual(len(tree.root_hash), 64)
    
    def test_merkle_tree_single_block(self):
        """Test Merkle tree with single block"""
        blocks = ["single_block"]
        tree = MerkleTree(blocks)
        
        self.assertEqual(len(tree.data_blocks), 1)
        self.assertEqual(tree.root_hash, sha256("single_block"))
    
    def test_merkle_tree_empty_blocks(self):
        """Test Merkle tree with empty blocks raises error"""
        with self.assertRaises(ValueError):
            MerkleTree([])
        
        with self.assertRaises(ValueError):
            MerkleTree(None)
    
    def test_merkle_tree_consistency(self):
        """Test that same blocks produce same root hash"""
        blocks = ["block1", "block2", "block3", "block4"]
        
        tree1 = MerkleTree(blocks)
        tree2 = MerkleTree(blocks.copy())
        
        self.assertEqual(tree1.root_hash, tree2.root_hash)
    
    def test_merkle_tree_proof_generation(self):
        """Test proof generation for various blocks"""
        blocks = ["block1", "block2", "block3", "block4"]
        tree = MerkleTree(blocks)
        
        # Test proof generation for each block
        for i in range(len(blocks)):
            proof = tree.get_proof(i)
            self.assertIsInstance(proof, list)
            self.assertGreater(len(proof), 0)
            
            # Each proof element should have required fields
            for proof_element in proof:
                self.assertIn("hash", proof_element)
                self.assertIn("position", proof_element)
                self.assertIn("level", proof_element)
                self.assertIn(proof_element["position"], ["left", "right"])
    
    def test_merkle_tree_proof_verification(self):
        """Test proof verification for all blocks"""
        blocks = ["block1", "block2", "block3", "block4"]
        tree = MerkleTree(blocks)
        
        # Verify proof for each block
        for i, block in enumerate(blocks):
            proof = tree.get_proof(i)
            is_valid = tree.verify_proof(block, i, proof)
            self.assertTrue(is_valid, f"Proof verification failed for block {i}")
    
    def test_merkle_tree_invalid_proof(self):
        """Test that invalid proofs fail verification"""
        blocks = ["block1", "block2", "block3", "block4"]
        tree = MerkleTree(blocks)
        
        # Test with wrong block data
        proof = tree.get_proof(0)
        is_valid = tree.verify_proof("wrong_block", 0, proof)
        self.assertFalse(is_valid)
        
        # Test with corrupted proof
        corrupted_proof = proof.copy()
        if corrupted_proof:
            corrupted_proof[0]["hash"] = "corrupted_hash"
            is_valid = tree.verify_proof(blocks[0], 0, corrupted_proof)
            self.assertFalse(is_valid)
    
    def test_merkle_tree_invalid_index(self):
        """Test error handling for invalid block indices"""
        blocks = ["block1", "block2"]
        tree = MerkleTree(blocks)
        
        # Test invalid indices
        with self.assertRaises(ValueError):
            tree.get_proof(-1)
        
        with self.assertRaises(ValueError):
            tree.get_proof(10)
        
        with self.assertRaises(ValueError):
            tree.verify_proof("block1", -1, [])
        
        with self.assertRaises(ValueError):
            tree.verify_proof("block1", 10, [])
    
    def test_merkle_tree_large_dataset(self):
        """Test Merkle tree performance with larger dataset"""
        # Create 1000 blocks
        blocks = [f"block_{i:04d}" for i in range(1000)]
        tree = MerkleTree(blocks)
        
        self.assertEqual(len(tree.data_blocks), 1000)
        self.assertIsInstance(tree.root_hash, str)
        
        # Test proof generation and verification for a few blocks
        test_indices = [0, 100, 500, 999]
        for i in test_indices:
            proof = tree.get_proof(i)
            is_valid = tree.verify_proof(blocks[i], i, proof)
            self.assertTrue(is_valid, f"Proof verification failed for block {i}")
    
    def test_merkle_tree_invalid_block_types(self):
        """Test error handling for invalid block types"""
        with self.assertRaises(ValueError):
            tree = MerkleTree([1, 2, 3])  # Non-string blocks


class TestCapsuleManagerEnhanced(unittest.TestCase):
    """Enhanced test cases for CapsuleManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CapsuleManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_capsule_manager_initialization(self):
        """Test CapsuleManager initialization"""
        self.assertTrue(self.manager.capsules_dir.exists())
        self.assertTrue(self.manager.metadata_dir.exists())
        self.assertTrue(self.manager.archives_dir.exists())
        self.assertIsNotNone(self.manager.logger)
        self.assertIsNotNone(self.manager.metrics)
    
    def test_capsule_manager_directories(self):
        """Test that all required directories are created"""
        required_dirs = [
            self.manager.capsules_dir,
            self.manager.metadata_dir,
            self.manager.archives_dir
        ]
        
        for directory in required_dirs:
            self.assertTrue(directory.exists())
            self.assertTrue(directory.is_dir())


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)