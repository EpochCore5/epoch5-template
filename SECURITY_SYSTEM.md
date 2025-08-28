# EPOCH5 Security System Documentation

## Overview

The EPOCH5 Security System provides a comprehensive security framework for agent monitoring, audit logging, and ceiling enforcement. This document describes the key components and usage of the security system.

## Components

### 1. EpochAudit Module (`epoch_audit.py`)

The EpochAudit module provides the core audit and security functionality:

- **Secure Audit Logging**: Cryptographically sealed audit logs with tamper detection
- **Alpha Ceiling Enforcement**: Cap values that exceed defined thresholds
- **Audit Scrolls**: Generate human-readable reports of audit events
- **Seal Verification**: Verify the integrity of audit logs

#### Usage

```bash
# Log an event
python epoch_audit.py log <event_type> <note> --data '{"key": "value"}'

# Enforce ceiling on a value
python epoch_audit.py enforce <value_type> <value> --agent <agent_did>

# Update a ceiling value
python epoch_audit.py update-ceiling <value_type> <ceiling>

# Generate audit scroll
python epoch_audit.py scroll --output <output_file>

# Verify audit seals
python epoch_audit.py verify --max-events 100
```

### 2. Agent Security Controller (`agent_security.py`)

The Agent Security Controller integrates the audit system with the agent monitoring system to provide comprehensive security for EPOCH5 agents:

- **Agent Integrity Verification**: Verify agent status and integrity
- **Secure Command Execution**: Send commands to agents with security checks
- **Security Reports**: Generate reports on agent security status
- **Rate Limiting**: Enforce rate limits on agent operations

#### Usage

```bash
# Verify agent integrity
python agent_security.py verify <agent_did>

# Send a secure command to an agent
python agent_security.py secure-command <agent_did> <command> --parameters '{"key": "value"}'

# Generate a security report
python agent_security.py report --output <output_file>

# Run audit scroll
python agent_security.py scroll --output <output_file>

# Run emoji command
python agent_security.py emoji
```

### 3. Security Setup Script (`setup_security.sh`)

The Security Setup Script automates the setup of the EPOCH5 Security System:

- **Directory Creation**: Create required directories for the security system
- **Emoji Command Setup**: Set up emoji commands for easy access
- **Cron Job Setup**: Set up scheduled audit tasks
- **Security Controller Setup**: Configure the agent security controller
- **Clean Up**: Remove old script files

#### Usage

```bash
# Run the setup script
./setup_security.sh
```

### 4. Makefile Targets

The Makefile includes targets for common security operations:

```bash
# Set up EPOCH5 Security System
make security-setup

# Test EPOCH5 Security System
make security-test

# Generate EPOCH5 Audit Scroll
make security-scroll

# Run Agent Security Controller
make agent-security
```

## Emoji Commands 🧙🦿🤖

The security system includes emoji commands for easy access to common operations:

- **🧙🦿🤖**: Generate an audit scroll

To use emoji commands, run:

```bash
source ./archive/EPOCH5/scripts/emoji_alias.sh
```

Then use the emoji commands:

```bash
🧙🦿🤖
```

## Alpha Ceiling Enforcement

The Alpha Ceiling concept enforces maximum values for various metrics:

- **task_priority**: Maximum task priority (default: 100)
- **resource_allocation**: Maximum resource allocation (default: 100)
- **message_rate**: Maximum messages per minute (default: 20)
- **concurrent_tasks**: Maximum concurrent tasks (default: 10)

When a value exceeds the ceiling, it is automatically capped and an audit event is logged.

## Security Policies

The security system enforces the following policies:

- **max_task_priority**: Maximum task priority (default: 100)
- **max_resource_allocation**: Maximum resource allocation (default: 100)
- **max_message_rate**: Maximum messages per minute (default: 20)
- **max_concurrent_tasks**: Maximum concurrent tasks (default: 10)
- **required_heartbeat_interval**: Maximum time between agent heartbeats (default: 300 seconds)
- **max_execution_time**: Maximum execution time for tasks (default: 600 seconds)
- **max_agent_restart_attempts**: Maximum agent restart attempts (default: 5)
- **daily_resource_quota**: Maximum daily resource usage (default: 1000)

## GBTEpoch and Phone Audit Scroll

The security system preserves the concepts of GBTEpoch and Phone Audit Scroll from the original bash scripts:

- **GBTEpoch**: Standard epoch time reference for all audit events
- **Phone Audit Scroll**: Generate human-readable audit reports (accessible via emoji command 🧙🦿🤖)
