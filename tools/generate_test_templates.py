#!/usr/bin/env python3
"""
Generates test template files for modules that need test coverage improvement.
"""

import os
import sys
from pathlib import Path
import re
import ast


def parse_module(file_path):
    """
    Parse a Python module to extract classes and functions.
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        classes = []
        functions = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        methods.append(child.name)
                classes.append((node.name, methods))
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
        
        return classes, functions
    except SyntaxError:
        print(f"Error parsing {file_path}. Skipping...")
        return [], []


def generate_test_template(module_path, output_dir="tests"):
    """
    Generate a test template file for a module.
    """
    module_name = os.path.basename(module_path)
    module_name_without_ext = os.path.splitext(module_name)[0]
    test_file_name = f"test_{module_name_without_ext}.py"
    test_file_path = os.path.join(output_dir, test_file_name)
    
    # Check if test file already exists
    if os.path.exists(test_file_path):
        print(f"Test file {test_file_path} already exists. Skipping...")
        return
    
    classes, functions = parse_module(module_path)
    
    # Create test template
    template = f'''"""
Tests for {module_name_without_ext} functionality
"""

import pytest
import json
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from {module_name_without_ext} import {", ".join([cls[0] for cls in classes] + functions[:5])}
except ImportError as e:
    pytest.skip(f"Could not import {module_name_without_ext} module: {{e}}", allow_module_level=True)

'''
    
    # Add test classes
    for class_name, methods in classes:
        template += f'''
class Test{class_name}:
    """Test cases for {class_name} class"""
    
    @pytest.fixture
    def {module_name_without_ext.lower()}_instance(self, temp_dir):
        """Create a {class_name} instance for testing"""
        return {class_name}(base_dir=temp_dir)
    
    def test_initialization(self, {module_name_without_ext.lower()}_instance):
        """Test that {class_name} initializes correctly"""
        assert {module_name_without_ext.lower()}_instance is not None
        # Add more assertions based on the class attributes
'''
        
        # Add method tests
        for method in methods:
            if method.startswith('__') and method != '__init__':
                continue  # Skip special methods except __init__
                
            template += f'''
    def test_{method}(self, {module_name_without_ext.lower()}_instance):
        """Test {method} functionality"""
        # TODO: Implement test for {method}
        pass
'''
    
    # Add function tests
    for function in functions:
        template += f'''

def test_{function}():
    """Test {function} functionality"""
    # TODO: Implement test for {function}
    pass
'''
    
    # Write template to file
    os.makedirs(output_dir, exist_ok=True)
    with open(test_file_path, 'w') as f:
        f.write(template)
    
    print(f"Generated test template: {test_file_path}")
    return test_file_path


def main():
    """Main function to generate test templates."""
    if len(sys.argv) < 2:
        print("Usage: python generate_test_templates.py <module_file> [output_dir]")
        sys.exit(1)
    
    module_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "tests"
    
    if not os.path.exists(module_path):
        print(f"Module file {module_path} does not exist.")
        sys.exit(1)
    
    if os.path.isdir(module_path):
        # Process all Python files in directory
        for root, _, files in os.walk(module_path):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    file_path = os.path.join(root, file)
                    generate_test_template(file_path, output_dir)
    else:
        # Process single file
        generate_test_template(module_path, output_dir)


if __name__ == "__main__":
    main()
