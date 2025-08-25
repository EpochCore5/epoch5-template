#!/usr/bin/env python3
"""
EPOCH5 Utilities Module
Provides common functionality for error handling, logging, hashing, and configuration
Designed to reduce code duplication and improve maintainability across EPOCH5 components
"""

import json
import hashlib
import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from functools import wraps
import os


class EPOCH5Logger:
    """Enhanced logging system for EPOCH5 components"""
    
    def __init__(self, name: str, log_dir: str = "./archive/EPOCH5/logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger with file and console handlers"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # File handler
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str, extra_data: Dict[str, Any] = None):
        """Log info message with optional structured data"""
        if extra_data:
            message = f"{message} | Data: {json.dumps(extra_data)}"
        self.logger.info(message)
    
    def error(self, message: str, exception: Exception = None, extra_data: Dict[str, Any] = None):
        """Log error message with exception details"""
        if exception:
            message = f"{message} | Exception: {str(exception)}"
        if extra_data:
            message = f"{message} | Data: {json.dumps(extra_data)}"
        self.logger.error(message)
        
        # Log stack trace if exception provided
        if exception:
            self.logger.debug(traceback.format_exc())
    
    def warning(self, message: str, extra_data: Dict[str, Any] = None):
        """Log warning message"""
        if extra_data:
            message = f"{message} | Data: {json.dumps(extra_data)}"
        self.logger.warning(message)
    
    def debug(self, message: str, extra_data: Dict[str, Any] = None):
        """Log debug message"""
        if extra_data:
            message = f"{message} | Data: {json.dumps(extra_data)}"
        self.logger.debug(message)


class EPOCH5ErrorHandler:
    """Centralized error handling for EPOCH5 operations"""
    
    def __init__(self, logger: EPOCH5Logger):
        self.logger = logger
    
    def handle_file_operation(self, operation_name: str, file_path: Union[str, Path]):
        """Decorator for safe file operations"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except FileNotFoundError as e:
                    self.logger.error(f"File not found during {operation_name}", e, 
                                    {"file_path": str(file_path)})
                    raise EPOCH5FileError(f"File not found: {file_path}") from e
                except PermissionError as e:
                    self.logger.error(f"Permission denied during {operation_name}", e,
                                    {"file_path": str(file_path)})
                    raise EPOCH5FileError(f"Permission denied: {file_path}") from e
                except Exception as e:
                    self.logger.error(f"Unexpected error during {operation_name}", e,
                                    {"file_path": str(file_path)})
                    raise EPOCH5Error(f"File operation failed: {operation_name}") from e
            return wrapper
        return decorator
    
    def handle_json_operation(self, operation_name: str):
        """Decorator for safe JSON operations"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON decode error during {operation_name}", e)
                    raise EPOCH5JSONError(f"Invalid JSON format: {operation_name}") from e
                except Exception as e:
                    self.logger.error(f"JSON operation error during {operation_name}", e)
                    raise EPOCH5Error(f"JSON operation failed: {operation_name}") from e
            return wrapper
        return decorator


class EPOCH5Error(Exception):
    """Base exception for EPOCH5 operations"""
    pass


class EPOCH5FileError(EPOCH5Error):
    """File operation specific exception"""
    pass


class EPOCH5JSONError(EPOCH5Error):
    """JSON operation specific exception"""
    pass


class EPOCH5ValidationError(EPOCH5Error):
    """Validation specific exception"""
    pass


class EPOCH5Utils:
    """Common utilities for EPOCH5 components"""
    
    @staticmethod
    def timestamp() -> str:
        """Generate ISO timestamp consistent with EPOCH5"""
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    @staticmethod
    def sha256(data: str) -> str:
        """Generate SHA256 hash consistent with EPOCH5"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def safe_json_load(file_path: Union[str, Path], default: Dict[str, Any] = None) -> Dict[str, Any]:
        """Safely load JSON file with error handling"""
        file_path = Path(file_path)
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                return default or {}
        except json.JSONDecodeError:
            # Return default on corrupt JSON
            return default or {}
        except Exception:
            # Return default on any other error
            return default or {}
    
    @staticmethod
    def safe_json_save(data: Dict[str, Any], file_path: Union[str, Path], 
                      backup: bool = True) -> bool:
        """Safely save JSON file with optional backup"""
        file_path = Path(file_path)
        
        try:
            # Create backup if file exists and backup is requested
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                file_path.replace(backup_path)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write data atomically
            temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename
            temp_path.replace(file_path)
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def create_directory_structure(base_dir: Union[str, Path], 
                                 subdirs: List[str] = None) -> Path:
        """Create directory structure for EPOCH5 components"""
        base_path = Path(base_dir)
        base_path.mkdir(parents=True, exist_ok=True)
        
        if subdirs:
            for subdir in subdirs:
                (base_path / subdir).mkdir(parents=True, exist_ok=True)
        
        return base_path
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that required fields are present in data"""
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise EPOCH5ValidationError(f"Missing required fields: {missing_fields}")
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file operations"""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        return filename.strip()


class EPOCH5Config:
    """Configuration management for EPOCH5 components"""
    
    def __init__(self, config_file: Union[str, Path] = None):
        self.config_file = Path(config_file) if config_file else Path("./epoch5_config.json")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        default_config = {
            "base_directory": "./archive/EPOCH5",
            "logging": {
                "level": "INFO",
                "directory": "./archive/EPOCH5/logs"
            },
            "performance": {
                "batch_size": 100,
                "max_workers": 4,
                "timeout_seconds": 300
            },
            "security": {
                "enable_backup": True,
                "max_retries": 3,
                "validation_enabled": True
            },
            "sla_defaults": {
                "min_success_rate": 0.95,
                "max_failure_rate": 0.05,
                "max_retry_count": 3
            }
        }
        
        if self.config_file.exists():
            try:
                loaded_config = EPOCH5Utils.safe_json_load(self.config_file, default_config)
                # Merge with defaults to ensure all keys exist
                return {**default_config, **loaded_config}
            except Exception:
                return default_config
        else:
            # Save default config
            self._save_config(default_config)
            return default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        EPOCH5Utils.safe_json_save(config, self.config_file)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value with dot notation support"""
        keys = key.split('.')
        config_ref = self.config
        
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]
        
        config_ref[keys[-1]] = value
        self._save_config(self.config)
    
    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()


def get_logger(name: str, log_dir: str = None) -> EPOCH5Logger:
    """Factory function to get configured logger"""
    if log_dir is None:
        config = EPOCH5Config()
        log_dir = config.get('logging.directory', './archive/EPOCH5/logs')
    
    return EPOCH5Logger(name, log_dir)


def get_error_handler(logger: EPOCH5Logger) -> EPOCH5ErrorHandler:
    """Factory function to get error handler with logger"""
    return EPOCH5ErrorHandler(logger)