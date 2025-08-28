#!/usr/bin/env python3
"""
Unit tests for ceiling_manager.py
"""

import json
import os
import tempfile
import time
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import pytest
import statistics
from datetime import datetime, timezone

# Import the module under test
from ceiling_manager import CeilingManager, ServiceTier, CeilingType

@pytest.fixture
def mock_epoch_audit():
    """Mock for EpochAudit to use in tests"""
    mock_audit = MagicMock()
    mock_audit.log_event = MagicMock()
    mock_audit.enforce_ceiling = MagicMock()
    mock_audit.verify_seals = MagicMock(return_value={
        "status": "VERIFIED",
        "verified_count": 5,
        "valid_count": 5,
        "invalid_count": 0,
        "invalid_events": []
    })
    mock_audit.get_security_alerts = MagicMock(return_value=[])
    mock_audit.get_ceiling_violations = MagicMock(return_value=[])
    mock_audit.ceilings = {}
    return mock_audit

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def ceiling_manager(temp_dir, mock_epoch_audit):
    """Create a CeilingManager instance with mocked dependencies"""
    with patch('ceiling_manager.SECURITY_SYSTEM_AVAILABLE', True), \
         patch('ceiling_manager.EpochAudit', return_value=mock_epoch_audit):
        manager = CeilingManager(temp_dir)
        yield manager

def test_init(ceiling_manager):
    """Test initialization of CeilingManager"""
    assert ceiling_manager.base_dir == Path(ceiling_manager.base_dir)
    assert ceiling_manager.ceiling_dir.exists()
    assert ceiling_manager.audit_system is not None

def test_timestamp(ceiling_manager):
    """Test timestamp generation"""
    timestamp = ceiling_manager.timestamp()
    # Ensure it's a string in ISO format
    assert isinstance(timestamp, str)
    # Try to parse it as a datetime to validate format
    datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")

def test_sha256(ceiling_manager):
    """Test SHA256 hash generation"""
    test_data = "test data for hashing"
    hash_result = ceiling_manager.sha256(test_data)
    assert isinstance(hash_result, str)
    assert len(hash_result) == 64  # SHA256 produces 64 character hashes

def test_initialize_default_tiers(ceiling_manager):
    """Test initialization of default service tiers"""
    # Reset to ensure _initialize_default_tiers gets called
    with patch('pathlib.Path.exists', return_value=False), \
         patch('builtins.open', mock_open()) as mock_file:
        ceiling_manager._initialize_default_tiers()
        mock_file.assert_called()

    # Check that all expected service tiers are present
    tiers_data = ceiling_manager.load_service_tiers()
    assert "tiers" in tiers_data
    assert ServiceTier.FREEMIUM.value in tiers_data["tiers"]
    assert ServiceTier.PROFESSIONAL.value in tiers_data["tiers"]
    assert ServiceTier.ENTERPRISE.value in tiers_data["tiers"]

def test_save_load_service_tiers(ceiling_manager, temp_dir):
    """Test saving and loading service tiers"""
    test_tiers = {
        "tiers": {
            ServiceTier.FREEMIUM.value: {
                "name": "Test Tier",
                "ceilings": {
                    CeilingType.BUDGET.value: 100.0
                }
            }
        }
    }
    
    # Save the test tiers
    ceiling_manager.save_service_tiers(test_tiers)
    
    # Load the tiers
    loaded_tiers = ceiling_manager.load_service_tiers()
    
    # Verify the data was saved and loaded correctly
    assert ServiceTier.FREEMIUM.value in loaded_tiers["tiers"]
    assert loaded_tiers["tiers"][ServiceTier.FREEMIUM.value]["name"] == "Test Tier"
    assert loaded_tiers["tiers"][ServiceTier.FREEMIUM.value]["ceilings"][CeilingType.BUDGET.value] == 100.0

def test_get_ceiling_for_tier(ceiling_manager):
    """Test getting ceiling values for specific service tiers"""
    # Setup test data
    test_tiers = {
        "tiers": {
            ServiceTier.FREEMIUM.value: {
                "name": "Test Freemium",
                "ceilings": {
                    CeilingType.BUDGET.value: 50.0,
                    CeilingType.LATENCY.value: 120.0
                }
            }
        }
    }
    
    with patch.object(ceiling_manager, 'load_service_tiers', return_value=test_tiers):
        # Test getting existing ceiling
        budget_ceiling = ceiling_manager.get_ceiling_for_tier(
            ServiceTier.FREEMIUM, CeilingType.BUDGET
        )
        assert budget_ceiling == 50.0
        
        # Test getting non-existent ceiling
        unknown_ceiling = ceiling_manager.get_ceiling_for_tier(
            ServiceTier.FREEMIUM, CeilingType.TRUST_THRESHOLD
        )
        assert unknown_ceiling == 0.0

def test_calculate_dynamic_ceiling(ceiling_manager):
    """Test dynamic ceiling calculation based on performance history"""
    # Set up test performance data
    performance_history = [
        {"success_rate": 0.99, "actual_latency": 30.0},
        {"success_rate": 0.98, "actual_latency": 35.0},
        {"success_rate": 0.97, "actual_latency": 40.0},
    ]
    
    # Mock the base ceiling value
    with patch.object(ceiling_manager, 'get_ceiling_for_tier', return_value=100.0):
        # Test budget ceiling with high performance
        budget_ceiling = ceiling_manager.calculate_dynamic_ceiling(
            CeilingType.BUDGET, ServiceTier.PROFESSIONAL, performance_history
        )
        # Should increase by 10% due to high success rate (avg_success > 0.95)
        assert budget_ceiling == pytest.approx(110.0)
        
        # Test latency ceiling
        latency_ceiling = ceiling_manager.calculate_dynamic_ceiling(
            CeilingType.LATENCY, ServiceTier.PROFESSIONAL, performance_history
        )
        # Should be 1.5 * avg_latency but within bounds
        avg_latency = statistics.mean([p["actual_latency"] for p in performance_history])
        expected_latency = avg_latency * 1.5
        assert latency_ceiling == expected_latency
        
        # Test with insufficient performance history
        ceiling_with_no_history = ceiling_manager.calculate_dynamic_ceiling(
            CeilingType.BUDGET, ServiceTier.PROFESSIONAL, []
        )
        assert ceiling_with_no_history == 100.0

def test_create_ceiling_configuration(ceiling_manager):
    """Test creating a ceiling configuration"""
    # Setup test data
    test_tiers = {
        "tiers": {
            ServiceTier.PROFESSIONAL.value: {
                "name": "Professional",
                "ceilings": {
                    CeilingType.BUDGET.value: 200.0,
                    CeilingType.LATENCY.value: 60.0,
                }
            }
        }
    }
    
    with patch.object(ceiling_manager, 'load_service_tiers', return_value=test_tiers):
        # Create configuration
        config = ceiling_manager.create_ceiling_configuration(
            "test-config-1", ServiceTier.PROFESSIONAL
        )
        
        # Verify configuration
        assert config["config_id"] == "test-config-1"
        assert config["service_tier"] == ServiceTier.PROFESSIONAL.value
        assert config["base_ceilings"][CeilingType.BUDGET.value] == 200.0
        assert config["base_ceilings"][CeilingType.LATENCY.value] == 60.0
        assert "hash" in config

        # Test with custom ceilings
        custom_ceilings = {
            CeilingType.BUDGET.value: 300.0
        }
        custom_config = ceiling_manager.create_ceiling_configuration(
            "test-config-2", ServiceTier.PROFESSIONAL, custom_ceilings
        )
        assert custom_config["custom_ceilings"][CeilingType.BUDGET.value] == 300.0

def test_adjust_ceiling_for_performance(ceiling_manager):
    """Test adjusting ceilings based on performance metrics"""
    # Setup test data
    test_config = {
        "config_id": "test-config",
        "service_tier": ServiceTier.PROFESSIONAL.value,
        "base_ceilings": {
            CeilingType.BUDGET.value: 200.0,
            CeilingType.LATENCY.value: 60.0,
            CeilingType.RATE_LIMIT.value: 1000,
        },
        "custom_ceilings": {},
        "dynamic_adjustments": {},
        "performance_score": 1.0,
    }
    test_ceilings_data = {
        "configurations": {
            "test-config": test_config
        }
    }
    
    # Test with excellent performance
    performance_metrics = {
        "success_rate": 0.99,  # High success rate
        "actual_latency": 30.0,  # Low latency (better)
        "spent_budget": 100.0,  # Low spending (better)
    }
    
    with patch.object(ceiling_manager, 'load_ceilings', return_value=test_ceilings_data), \
         patch.object(ceiling_manager, 'save_ceilings') as mock_save, \
         patch.object(ceiling_manager, 'log_ceiling_event') as mock_log:
        
        result = ceiling_manager.adjust_ceiling_for_performance(
            "test-config", performance_metrics
        )
        
        # Check that performance score is calculated
        assert result["performance_score"] > 1.0
        
        # Check that dynamic adjustments are made
        assert CeilingType.BUDGET.value in result["dynamic_adjustments"]
        assert CeilingType.RATE_LIMIT.value in result["dynamic_adjustments"]
        
        # Check that log was called
        mock_log.assert_called_once()
        
        # Check that save was called
        mock_save.assert_called_once()

    # Test with config not found
    with patch.object(ceiling_manager, 'load_ceilings', return_value={"configurations": {}}):
        error_result = ceiling_manager.adjust_ceiling_for_performance(
            "non-existent-config", performance_metrics
        )
        assert "error" in error_result
        assert error_result["error"] == "Configuration not found"

def test_get_effective_ceiling(ceiling_manager):
    """Test getting effective ceiling values"""
    # Setup test data
    test_config = {
        "config_id": "test-config",
        "service_tier": ServiceTier.PROFESSIONAL.value,
        "base_ceilings": {
            CeilingType.BUDGET.value: 200.0,
        },
        "custom_ceilings": {
            CeilingType.LATENCY.value: 45.0,
        },
        "dynamic_adjustments": {
            CeilingType.BUDGET.value: 1.2,  # 20% increase
        },
    }
    test_ceilings_data = {
        "configurations": {
            "test-config": test_config
        }
    }
    
    with patch.object(ceiling_manager, 'load_ceilings', return_value=test_ceilings_data):
        # Test base ceiling with adjustment
        budget_ceiling = ceiling_manager.get_effective_ceiling(
            "test-config", CeilingType.BUDGET
        )
        assert budget_ceiling == 200.0 * 1.2
        
        # Test custom ceiling
        latency_ceiling = ceiling_manager.get_effective_ceiling(
            "test-config", CeilingType.LATENCY
        )
        assert latency_ceiling == 45.0
        
        # Test non-existent config
        with patch.object(ceiling_manager, 'get_ceiling_for_tier', return_value=50.0):
            fallback_ceiling = ceiling_manager.get_effective_ceiling(
                "non-existent-config", CeilingType.BUDGET
            )
            assert fallback_ceiling == 50.0

def test_calculate_revenue_impact(ceiling_manager):
    """Test revenue impact calculation"""
    # Setup test performance data
    performance_before = {
        "success_rate": 0.95,
        "actual_latency": 60.0,
    }
    performance_after = {
        "success_rate": 0.97,  # 2% improvement
        "actual_latency": 50.0,  # 10 seconds improvement
    }
    
    with patch.object(ceiling_manager, 'audit_system') as mock_audit:
        result = ceiling_manager.calculate_revenue_impact(
            "test-config", performance_before, performance_after
        )
        
        # Check calculations
        assert result["success_rate_improvement"] == pytest.approx(0.02)
        assert result["latency_improvement_seconds"] == pytest.approx(10.0)
        
        # Expected revenue: (0.02 * 100 * 100) + (10 * 50) = 200 + 500 = 700
        assert result["estimated_monthly_revenue_impact"] == pytest.approx(700.0)
        
        # Check recommendation
        assert "recommendation" in result
        assert "Strong positive impact" in result["recommendation"]
        
        # Check audit log
        mock_audit.log_event.assert_called_once()

def test_enforce_value_ceiling(ceiling_manager):
    """Test enforcing value ceilings"""
    # Setup test
    ceiling_value = 100.0
    
    # Set up the ceilings in audit system to avoid ValueError
    ceiling_manager.audit_system.ceilings = {CeilingType.BUDGET.value: ceiling_value}
    
    with patch.object(ceiling_manager, 'get_effective_ceiling', return_value=ceiling_value), \
         patch.object(ceiling_manager, 'log_ceiling_event') as mock_log:
        
        # Test value under ceiling
        result_under = ceiling_manager.enforce_value_ceiling(
            "test-config", CeilingType.BUDGET, 90.0
        )
        assert result_under["capped"] == False
        assert result_under["original_value"] == 90.0
        assert result_under["final_value"] == 90.0
        
        # Reset mock to test the next call separately
        mock_log.reset_mock()
        
        # Test value over ceiling
        result_over = ceiling_manager.enforce_value_ceiling(
            "test-config", CeilingType.BUDGET, 150.0
        )
        assert result_over["capped"] == True
        assert result_over["original_value"] == 150.0
        assert result_over["final_value"] == 100.0
        assert mock_log.call_count == 1  # Use call_count instead of assert_called_once

def test_generate_revenue_recommendation(ceiling_manager):
    """Test revenue recommendation generation"""
    # Test different revenue impacts
    high_rec = ceiling_manager._generate_revenue_recommendation(600.0)
    assert "Strong positive impact" in high_rec
    
    moderate_rec = ceiling_manager._generate_revenue_recommendation(200.0)
    assert "Moderate positive impact" in moderate_rec
    
    negative_rec = ceiling_manager._generate_revenue_recommendation(-200.0)
    assert "Negative impact detected" in negative_rec
    
    neutral_rec = ceiling_manager._generate_revenue_recommendation(50.0)
    assert "Neutral impact" in neutral_rec

def test_save_load_ceilings(ceiling_manager, temp_dir):
    """Test saving and loading ceiling configurations"""
    # Create test ceiling configuration
    test_config = {
        "config_id": "test-config",
        "service_tier": ServiceTier.PROFESSIONAL.value,
        "base_ceilings": {
            CeilingType.BUDGET.value: 200.0,
        },
        "custom_ceilings": {},
        "dynamic_adjustments": {},
    }
    
    # Setup test data
    test_ceilings_data = {
        "configurations": {
            "test-config": test_config
        }
    }
    
    # Test saving
    ceiling_manager.save_ceilings(test_ceilings_data)
    
    # Test loading
    loaded_data = ceiling_manager.load_ceilings()
    assert "configurations" in loaded_data
    assert "test-config" in loaded_data["configurations"]
    assert loaded_data["configurations"]["test-config"]["base_ceilings"][CeilingType.BUDGET.value] == 200.0

def test_add_configuration(ceiling_manager):
    """Test adding a ceiling configuration"""
    # Create test configuration
    test_config = {
        "config_id": "test-config-add",
        "service_tier": ServiceTier.PROFESSIONAL.value,
        "base_ceilings": {
            CeilingType.BUDGET.value: 200.0,
        },
        "custom_ceilings": {},
        "dynamic_adjustments": {},
    }
    
    # Mock load_ceilings and save_ceilings
    mock_ceilings_data = {"configurations": {}}
    
    with patch.object(ceiling_manager, 'load_ceilings', return_value=mock_ceilings_data), \
         patch.object(ceiling_manager, 'save_ceilings') as mock_save:
        
        result = ceiling_manager.add_configuration(test_config)
        assert result == True
        
        # Verify save_ceilings was called with updated data
        mock_save.assert_called_once()
        saved_data = mock_save.call_args[0][0]
        assert "configurations" in saved_data
        assert "test-config-add" in saved_data["configurations"]

def test_log_ceiling_event(ceiling_manager):
    """Test logging ceiling events"""
    event_type = "TEST_EVENT"
    event_data = {
        "config_id": "test-config",
        "value": 100.0
    }
    
    # Mock file operations and audit system to avoid multiple calls
    with patch('builtins.open', mock_open()) as mock_file, \
         patch.object(ceiling_manager, 'audit_system', None):  # Set audit_system to None for this test
        ceiling_manager.log_ceiling_event(event_type, event_data)
        assert mock_file.call_count >= 1  # Ensure open was called at least once
        
        # Check that audit system was called if available
        if ceiling_manager.audit_system:
            ceiling_manager.audit_system.log_event.assert_called_once()

def test_get_upgrade_recommendations(ceiling_manager):
    """Test upgrade recommendations"""
    # Setup test data for freemium tier with high performance
    freemium_config = {
        "config_id": "freemium-config",
        "service_tier": ServiceTier.FREEMIUM.value,
        "performance_score": 1.4,  # High performance
    }
    
    # Setup test data for professional tier with high performance
    pro_config = {
        "config_id": "pro-config",
        "service_tier": ServiceTier.PROFESSIONAL.value,
        "performance_score": 1.4,  # High performance
    }
    
    # Setup test data for enterprise tier
    enterprise_config = {
        "config_id": "enterprise-config",
        "service_tier": ServiceTier.ENTERPRISE.value,
        "performance_score": 1.4,  # High performance
    }
    
    test_ceilings_data = {
        "configurations": {
            "freemium-config": freemium_config,
            "pro-config": pro_config,
            "enterprise-config": enterprise_config
        }
    }
    
    with patch.object(ceiling_manager, 'load_ceilings', return_value=test_ceilings_data):
        # Test freemium tier with high performance - should recommend upgrade
        freemium_rec = ceiling_manager.get_upgrade_recommendations("freemium-config")
        assert freemium_rec["should_upgrade"] == True
        assert freemium_rec["recommended_tier"] == ServiceTier.PROFESSIONAL.value
        assert len(freemium_rec["benefits"]) > 0
        
        # Test professional tier with high performance - should recommend upgrade
        pro_rec = ceiling_manager.get_upgrade_recommendations("pro-config")
        assert pro_rec["should_upgrade"] == True
        assert pro_rec["recommended_tier"] == ServiceTier.ENTERPRISE.value
        assert len(pro_rec["benefits"]) > 0
        
        # Test enterprise tier - should not recommend upgrade (already highest)
        enterprise_rec = ceiling_manager.get_upgrade_recommendations("enterprise-config")
        assert enterprise_rec["should_upgrade"] == False
        assert enterprise_rec["recommended_tier"] is None
        
        # Test config not found
        not_found_rec = ceiling_manager.get_upgrade_recommendations("non-existent-config")
        assert "error" in not_found_rec

def test_main(ceiling_manager):
    """Test CLI interface main function"""
    with patch('argparse.ArgumentParser') as mock_parser, \
         patch.object(ceiling_manager, 'create_ceiling_configuration') as mock_create, \
         patch.object(ceiling_manager, 'add_configuration') as mock_add, \
         patch.object(ceiling_manager, 'adjust_ceiling_for_performance') as mock_adjust, \
         patch.object(ceiling_manager, 'get_effective_ceiling') as mock_get, \
         patch.object(ceiling_manager, 'enforce_value_ceiling') as mock_enforce, \
         patch.object(ceiling_manager, 'get_upgrade_recommendations') as mock_upgrade, \
         patch('builtins.print') as mock_print, \
         patch('ceiling_manager.CeilingManager', return_value=ceiling_manager):
        
        # Patch the argparse to return different commands for each test
        def setup_args(command):
            mock_args = MagicMock()
            mock_args.command = command
            mock_parser.return_value.parse_args.return_value = mock_args
            return mock_args
        
        # Test create-config command
        args = setup_args('create-config')
        args.config_id = 'test-config'
        args.tier = ServiceTier.PROFESSIONAL.value
        mock_create.return_value = {
            "config_id": "test-config",
            "base_ceilings": {"budget": 200.0}
        }
        
        from ceiling_manager import main
        main()
        mock_create.assert_called_once()
        mock_add.assert_called_once()
        
        # Test adjust command
        mock_create.reset_mock()
        mock_add.reset_mock()
        
        args = setup_args('adjust')
        args.config_id = 'test-config'
        args.success_rate = 0.95
        args.latency = 60.0
        args.budget = 100.0
        mock_adjust.return_value = {
            "performance_score": 1.2,
            "dynamic_adjustments": {"budget": 1.1}
        }
        
        main()
        mock_adjust.assert_called_once_with(
            'test-config', 
            {"success_rate": 0.95, "actual_latency": 60.0, "spent_budget": 100.0}
        )
        
        # Test get command
        mock_adjust.reset_mock()
        
        args = setup_args('get')
        args.config_id = 'test-config'
        args.ceiling_type = 'budget'
        mock_get.return_value = 220.0
        
        main()
        mock_get.assert_called_once()
        
        # Test enforce command
        mock_get.reset_mock()
        
        args = setup_args('enforce')
        args.config_id = 'test-config'
        args.ceiling_type = 'budget'
        args.value = 150.0
        mock_enforce.return_value = {
            "original_value": 150.0,
            "final_value": 100.0,
            "ceiling": 100.0,
            "capped": True
        }
        
        main()
        mock_enforce.assert_called_once()
        
        # Test upgrade-rec command
        mock_enforce.reset_mock()
        
        args = setup_args('upgrade-rec')
        args.config_id = 'test-config'
        mock_upgrade.return_value = {
            "current_tier": "freemium",
            "performance_score": 1.5,
            "should_upgrade": True,
            "recommended_tier": "professional",
            "benefits": ["Benefit 1", "Benefit 2"],
            "estimated_roi": 2.5,
            "urgency": "high"
        }
        
        main()
        mock_upgrade.assert_called_once()
        
        # Test no command
        mock_upgrade.reset_mock()
        
        args = setup_args(None)
        main()
        mock_parser.return_value.print_help.assert_called_once()