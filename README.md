# EPOCH5 Template - Enhanced Integration System

A comprehensive tool for logging, agent management, policy enforcement, and secure execution of tasks with advanced provenance tracking.

---

**Copyright (c) 2024 John Ryan, EpochCore Business, Charlotte NC. All rights reserved.**  
Unauthorized commercial use, distribution, or modification is prohibited without explicit written permission.  
For licensing or partnership inquiries, contact: jryan2k19@gmail.com

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Examples](#examples)
- [Contributing](#contributing)
- [Commercial Use Policy](#commercial-use-policy)
- [Support](#support)

## Overview

The EPOCH5 Template provides a complete ecosystem for secure data processing and system orchestration with advanced provenance tracking. Built for enterprise environments requiring high levels of security, auditability, and fault tolerance.

## Features

### Core Capabilities
- **🔐 Advanced Logging & Provenance**: Hash-chained ledger system with tamper-evident records
- **👥 Agent Management**: Decentralized identifiers (DIDs), registry, and real-time monitoring  
- **🛡️ Policy & Security**: Rule enforcement with quorum requirements and multi-signature approvals
- **🔄 DAG Management**: Directed Acyclic Graph execution with fault-tolerant mechanisms
- **⚡ Cycle Execution**: Budget control, latency tracking, and PBFT consensus
- **💾 Data Integrity**: Capsule storage with Merkle tree proofs and ZIP archiving
- **📋 Meta-Capsules**: Comprehensive system state capture and ledger integration

### Integration Features
- **Unified CLI**: Single point of control for all system components
- **Triple-Pass Processing**: Secure data processing with anchor, amplify, and crown phases
- **Real-time Monitoring**: System health and performance tracking
- **Extensible Architecture**: Plugin-ready design for custom components

## Quick Start

```bash
# Clone the repository
git clone https://github.com/EpochCore5/epoch5-template.git
cd epoch5-template

# Make scripts executable
chmod +x epoch5.sh

# Set up demo environment
python3 integration.py setup-demo

# Run a complete workflow
python3 integration.py run-workflow

# Check system status
python3 integration.py status
```

## Installation

### Prerequisites
- Python 3.7 or higher
- Bash shell (Linux/macOS/WSL)
- OpenSSL or shasum for cryptographic operations
- Node.js 14+ (for CI/CD pipeline)

### System Requirements
- Linux, macOS, or Windows with WSL
- 100MB disk space for archives
- Network access for dependency validation

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/EpochCore5/epoch5-template.git
   cd epoch5-template
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Make scripts executable:**
   ```bash
   chmod +x epoch5.sh
   ```

4. **Verify installation:**
   ```bash
   # Test Python integration
   python3 integration.py --help
   
   # Test Bash script syntax
   bash -n epoch5.sh
   
   # Run system validation
   python3 integration.py validate
   ```

## Usage

### Command Line Interface

The `integration.py` script provides a unified interface for all EPOCH5 operations:

#### Basic Commands

```bash
# System setup and demo
python3 integration.py setup-demo          # Initialize with sample data
python3 integration.py run-workflow        # Execute complete workflow
python3 integration.py status             # System status overview
python3 integration.py validate           # Validate system integrity
```

#### Agent Management

```bash
# List all agents
python3 integration.py agents list

# Create a new agent
python3 integration.py agents create skill1 skill2 skill3
```

#### Policy Management

```bash
# List policies
python3 integration.py policies list
```

#### One-liner Operations

```bash
# Quick operations for testing and demos
python3 integration.py oneliner quick-agent
python3 integration.py oneliner system-snapshot
```

### Triple-Pass Capsule Processing

The `epoch5.sh` script provides secure data processing with three phases:

```bash
# Basic usage with default delays
./epoch5.sh

# Skip delays for testing
DELAY_HOURS_P1_P2=0 DELAY_HOURS_P2_P3=0 ./epoch5.sh

# Custom data processing
P1_PAYLOAD="Your anchor data" P2_PAYLOAD="Amplification data" P3_PAYLOAD="Crown data" ./epoch5.sh
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DELAY_HOURS_P1_P2` | 6 | Hours between Pass 1 and Pass 2 |
| `DELAY_HOURS_P2_P3` | 6 | Hours between Pass 2 and Pass 3 |
| `P1_PAYLOAD` | Sample data | Pass 1 payload content |
| `P2_PAYLOAD` | Sample data | Pass 2 payload content |
| `P3_PAYLOAD` | Sample data | Pass 3 payload content |

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    EPOCH5 Integration Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  Agent Mgmt  │  Policy Mgmt  │  DAG Mgmt  │  Cycle Execution    │
├─────────────────────────────────────────────────────────────────┤
│  Capsule Metadata  │  Meta-Capsule Creator  │  Logging System   │
├─────────────────────────────────────────────────────────────────┤
│                    Archive Storage Layer                        │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input Processing**: Data enters through CLI or script interfaces
2. **Agent Validation**: Agents verify and process data according to policies
3. **DAG Execution**: Tasks execute in dependency order with fault tolerance
4. **Cycle Management**: Budget and latency controls ensure SLA compliance
5. **Capsule Storage**: Data stored with integrity proofs and metadata
6. **Meta-Capsule Creation**: System state captured for audit trails
7. **Archive Finalization**: Complete provenance chain sealed and stored

## Examples

### Example 1: Basic Setup and Validation

```bash
# Initialize the system
python3 integration.py setup-demo

# Validate everything is working
python3 integration.py validate

# Check system status
python3 integration.py status
```

### Example 2: Custom Data Processing

```bash
# Process custom data through triple-pass system
P1_PAYLOAD="Critical system configuration" \
P2_PAYLOAD="Security enhancement parameters" \
P3_PAYLOAD="Final validation and closure" \
DELAY_HOURS_P1_P2=0 DELAY_HOURS_P2_P3=0 \
./epoch5.sh
```

### Example 3: Agent and Policy Management

```bash
# Create agents with specific skills
python3 integration.py agents create "data-processing" "security-validation" "audit-compliance"

# List all registered agents
python3 integration.py agents list

# Check policy status
python3 integration.py policies list
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Development setup
- Coding standards
- Testing procedures
- Pull request process

### Development Quick Start

```bash
# Set up development environment
git clone https://github.com/EpochCore5/epoch5-template.git
cd epoch5-template
npm install

# Run tests
npm test

# Validate code
python3 -m py_compile *.py
bash -n epoch5.sh
```

## Commercial Use Policy

**Important**: This repository is NOT open source. All rights reserved.

- Commercial use, distribution, or modification is prohibited without explicit written permission
- For commercial licensing or partnership inquiries, contact: jryan2k19@gmail.com
- Supporting this project means supporting creators who build secure, innovative solutions for real businesses and families

EpochCore is a business founded and operated by John Ryan, a single father in Charlotte, NC.

## Support

### Getting Help

- **Issues**: Create an issue on GitHub with detailed information
- **Documentation**: Check the [CONTRIBUTING.md](CONTRIBUTING.md) guide
- **Commercial Support**: Contact jryan2k19@gmail.com for enterprise support

### System Requirements Help

If you encounter issues:

1. Verify Python 3.7+ is installed: `python3 --version`
2. Check Bash availability: `bash --version`  
3. Test script permissions: `ls -la epoch5.sh`
4. Validate dependencies: `python3 integration.py validate`

### Troubleshooting

| Issue | Solution |
|-------|----------|
| Permission denied | `chmod +x epoch5.sh` |
| Python module errors | Check Python 3.7+ is installed |
| Missing dependencies | Run `npm install` |
| Archive creation fails | Verify write permissions in current directory |

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Maintainer**: John Ryan, EpochCore Business