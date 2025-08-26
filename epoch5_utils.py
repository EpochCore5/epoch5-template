#!/usr/bin/env python3
"""
EPOCH5 Common Utilities
Shared utilities for EPOCH5 system including logging, error handling, configuration, and common operations.
Provides consistent interfaces across all EPOCH5 components.
"""

import json
import hashlib
import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable
from functools import wraps
import configparser
import argparse


class EPOCH5Logger:
    """Centralized logging configuration for EPOCH5 system"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str, log_file: Optional[str] = None, level: str = "INFO") -> logging.Logger:
        """Get or create a logger with consistent EPOCH5 formatting"""
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_format = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%SZ'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_format = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%dT%H:%M:%SZ'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger


class EPOCH5Config:
    """Configuration management for EPOCH5 system"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self._load_defaults()
        if config_file and Path(config_file).exists():
            self.config.read(config_file)
    
    def _load_defaults(self):
        """Load default configuration values"""
        self.config['DEFAULT'] = {
            'base_dir': './archive/EPOCH5',
            'log_level': 'INFO',
            'max_retries': '3',
            'timeout_seconds': '30',
            'batch_size': '100'
        }
        
        self.config['logging'] = {
            'console_level': 'INFO',
            'file_level': 'DEBUG',
            'max_log_size_mb': '10',
            'backup_count': '5'
        }
        
        self.config['performance'] = {
            'enable_batch_processing': 'true',
            'max_concurrent_operations': '10',
            'cache_size': '1000'
        }
        
        self.config['security'] = {
            'hash_algorithm': 'sha256',
            'min_password_length': '8',
            'session_timeout_minutes': '60'
        }
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """Get configuration value"""
        return self.config.get(section, key, fallback=str(fallback) if fallback is not None else None)
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """Get integer configuration value"""
        return self.config.getint(section, key, fallback=fallback)
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """Get boolean configuration value"""
        return self.config.getboolean(section, key, fallback=fallback)
    
    def save(self, config_file: Optional[str] = None):
        """Save configuration to file"""
        file_path = config_file or self.config_file
        if file_path:
            with open(file_path, 'w') as f:
                self.config.write(f)


class EPOCH5ErrorHandler:
    """Error handling utilities for EPOCH5 system"""
    
    @staticmethod
    def safe_file_operation(operation: Callable, *args, **kwargs) -> tuple[bool, Any, Optional[str]]:
        """
        Safely execute file operations with error handling
        
        Args:
            operation: Function to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            tuple: (success, result, error_message)
        """
        try:
            result = operation(*args, **kwargs)
            return True, result, None
        except FileNotFoundError as e:
            return False, None, f"File not found: {str(e)}"
        except PermissionError as e:
            return False, None, f"Permission denied: {str(e)}"
        except json.JSONDecodeError as e:
            return False, None, f"JSON decode error: {str(e)}"
        except Exception as e:
            return False, None, f"Unexpected error: {str(e)}"
    
    @staticmethod
    def safe_json_operation(operation: str, data: Any = None, file_path: Optional[str] = None) -> tuple[bool, Any, Optional[str]]:
        """
        Safely execute JSON operations
        
        Args:
            operation: 'load', 'loads', 'dump', or 'dumps'
            data: Data for dump/dumps operations
            file_path: File path for load/dump operations
            
        Returns:
            tuple: (success, result, error_message)
        """
        try:
            if operation == 'load' and file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                return True, result, None
            elif operation == 'loads' and data:
                result = json.loads(data)
                return True, result, None
            elif operation == 'dump' and file_path and data is not None:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                return True, None, None
            elif operation == 'dumps' and data is not None:
                result = json.dumps(data, indent=2, ensure_ascii=False)
                return True, result, None
            else:
                return False, None, f"Invalid JSON operation or missing parameters"
        except json.JSONDecodeError as e:
            return False, None, f"JSON decode error: {str(e)}"
        except Exception as e:
            return False, None, f"JSON operation error: {str(e)}"
    
    @staticmethod
    def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
        """
        Decorator for retrying operations on failure
        
        Args:
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds
        """
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                import time
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_retries:
                            time.sleep(delay)
                            continue
                        break
                
                raise last_exception
            return wrapper
        return decorator


class EPOCH5Utils:
    """Common utility functions for EPOCH5 system"""
    
    @staticmethod
    def timestamp() -> str:
        """Generate ISO timestamp consistent with EPOCH5 format"""
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    @staticmethod
    def sha256(data: Union[str, bytes]) -> str:
        """Generate SHA256 hash consistent with EPOCH5 format"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if necessary"""
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def safe_load_json(file_path: Union[str, Path], default: Any = None) -> Any:
        """Safely load JSON file with fallback to default"""
        success, result, error = EPOCH5ErrorHandler.safe_json_operation('load', file_path=str(file_path))
        if success:
            return result
        return default if default is not None else {}
    
    @staticmethod
    def safe_save_json(data: Any, file_path: Union[str, Path]) -> bool:
        """Safely save JSON file"""
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        success, _, error = EPOCH5ErrorHandler.safe_json_operation('dump', data=data, file_path=str(file_path))
        return success
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> tuple[bool, List[str]]:
        """Validate that required fields are present in data"""
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        return len(missing_fields) == 0, missing_fields
    
    @staticmethod
    def batch_process(items: List[Any], batch_size: int = 100, processor: Callable = None) -> List[Any]:
        """Process items in batches for performance optimization"""
        if not processor:
            return items
        
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = processor(batch)
            if isinstance(batch_results, list):
                results.extend(batch_results)
            else:
                results.append(batch_results)
        return results
    
    @staticmethod
    def create_cli_parser(description: str) -> argparse.ArgumentParser:
        """Create standardized CLI argument parser for EPOCH5 components"""
        parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Common arguments across all EPOCH5 components
        parser.add_argument(
            '--base-dir', 
            default='./archive/EPOCH5',
            help='Base directory for EPOCH5 data storage (default: ./archive/EPOCH5)'
        )
        parser.add_argument(
            '--config', 
            help='Configuration file path'
        )
        parser.add_argument(
            '--log-level', 
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO',
            help='Logging level (default: INFO)'
        )
        parser.add_argument(
            '--log-file', 
            help='Log file path for file logging'
        )
        parser.add_argument(
            '--batch-size', 
            type=int, 
            default=100,
            help='Batch size for bulk operations (default: 100)'
        )
        
        return parser


class EPOCH5Metrics:
    """Performance metrics and monitoring for EPOCH5 operations"""
    
    def __init__(self):
        self.metrics = {
            'operations': {},
            'timing': {},
            'errors': {}
        }
        self.start_time = None
    
    def start_operation(self, operation_name: str):
        """Start timing an operation"""
        self.start_time = datetime.utcnow()
        if operation_name not in self.metrics['operations']:
            self.metrics['operations'][operation_name] = 0
    
    def end_operation(self, operation_name: str, success: bool = True):
        """End timing an operation and record metrics"""
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            if operation_name not in self.metrics['timing']:
                self.metrics['timing'][operation_name] = []
            self.metrics['timing'][operation_name].append(duration)
            
            self.metrics['operations'][operation_name] += 1
            
            if not success:
                if operation_name not in self.metrics['errors']:
                    self.metrics['errors'][operation_name] = 0
                self.metrics['errors'][operation_name] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        summary = {
            'total_operations': sum(self.metrics['operations'].values()),
            'operation_counts': self.metrics['operations'].copy(),
            'average_timing': {},
            'error_rates': {}
        }
        
        for op, times in self.metrics['timing'].items():
            if times:
                summary['average_timing'][op] = sum(times) / len(times)
        
        for op, error_count in self.metrics['errors'].items():
            total_count = self.metrics['operations'].get(op, 1)
            summary['error_rates'][op] = error_count / total_count
        
        return summary


# Export commonly used functions for convenience
get_logger = EPOCH5Logger.get_logger
timestamp = EPOCH5Utils.timestamp
sha256 = EPOCH5Utils.sha256
ensure_directory = EPOCH5Utils.ensure_directory
safe_load_json = EPOCH5Utils.safe_load_json
safe_save_json = EPOCH5Utils.safe_save_json