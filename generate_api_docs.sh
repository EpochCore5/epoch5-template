#!/bin/bash
# Script to generate API documentation for EPOCH5

# Set up directories
mkdir -p docs/api
mkdir -p docs/images

# Install Sphinx if not already installed
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints myst-parser

# Initialize Sphinx if not already initialized
if [ ! -f docs/conf.py ]; then
    cd docs
    sphinx-quickstart -q --sep --project="EPOCH5 API Documentation" --author="EpochCore5" --language=en
    cd ..
fi

# Update conf.py to include autodoc and other extensions
cat <<EOT > docs/conf.py
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
project = 'EPOCH5 API Documentation'
copyright = '2024, EpochCore5'
author = 'EpochCore5'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = '_static/logo.png'
html_favicon = '_static/favicon.ico'

# -- Extension configuration -------------------------------------------------
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autoclass_content = 'both'
EOT

# Create logo directory
mkdir -p docs/_static

# Create a simple index.rst file
cat <<EOT > docs/index.rst
EPOCH5 API Documentation
========================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api/modules
   api/agent_management
   api/policy_grants
   api/capsule_metadata
   api/cycle_execution
   api/ceiling_manager
   api/dag_management
   api/meta_capsule
   api/integration

Introduction
-----------

This is the API documentation for EPOCH5, a comprehensive system for agent management, 
policy enforcement, and secure execution of tasks with advanced provenance tracking.

Getting Started
--------------

To get started with EPOCH5, check out the :doc:\`installation guide <installation>\`.

Indices and tables
==================

* :ref:\`genindex\`
* :ref:\`modindex\`
* :ref:\`search\`
EOT

# Create installation guide
cat <<EOT > docs/installation.rst
Installation Guide
=================

Prerequisites
------------

- Python 3.8 or higher
- Git

Installation Steps
-----------------

1. Clone the repository
   
   .. code-block:: bash
   
      git clone https://github.com/EpochCore5/epoch5-template.git
      cd epoch5-template

2. Install dependencies
   
   .. code-block:: bash
   
      pip install -r requirements.txt

3. Run demo setup
   
   .. code-block:: bash
   
      python integration.py setup-demo

Development Environment
----------------------

For a development environment, use the provided Docker container:

.. code-block:: bash

   # Using VS Code with Remote Containers extension
   code epoch5-template
   # Then click "Reopen in Container" when prompted

   # Or using Docker CLI
   docker-compose -f .devcontainer/docker-compose.yml up -d
   docker exec -it epoch5-dev /bin/bash
EOT

# Generate API documentation for each module
sphinx-apidoc -o docs/api . tests setup.py

# Build HTML documentation
cd docs
make html
cd ..

echo "API documentation generated in docs/_build/html/"
echo "To view the documentation, open docs/_build/html/index.html in your browser"
