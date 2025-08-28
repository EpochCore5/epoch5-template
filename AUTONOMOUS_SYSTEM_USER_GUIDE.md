# EPOCH5 Autonomous System User Guide

## Overview

This guide provides instructions for using the EPOCH5 Autonomous System components, including testing, generating test data, visualizing results, and understanding the system architecture.

## Components

The EPOCH5 Autonomous System consists of these key components:

1. **Core Autonomous Modules**
   - `self_healing.py`: System health monitoring and automatic recovery
   - `adaptive_security.py`: ML-based security pattern recognition and response
   - `meta_orchestrator.py`: Hierarchical decision-making framework
   - `autonomous_control.sh`: Central interface for managing autonomous systems

2. **Testing & Evaluation Tools**
   - `test_autonomous_system.py`: Integration tests for autonomous components
   - `generate_test_data.py`: Test data generation for system evaluation
   - `visualize_data.py`: Data visualization for performance analysis

3. **Documentation**
   - `AUTONOMOUS_ARCHITECTURE.md`: Detailed architecture overview
   - This user guide

## Setup

Ensure all components are installed and have executable permissions:

```bash
# Make scripts executable
chmod +x autonomous_control.sh
chmod +x generate_test_data.py
chmod +x visualize_data.py

# Install required Python packages
pip install -r requirements.txt
```

## Using the Autonomous System

### Control Interface

The central control interface (`autonomous_control.sh`) provides a menu-driven approach to managing the autonomous system:

```bash
# Start the control interface
./autonomous_control.sh
```

This will display a menu with the following options:

1. **Full Autonomous Mode**: Enables all autonomous components with meta-orchestration
2. **Supervised Autonomous Mode**: Enables autonomy with human approval for critical decisions
3. **Self-Healing Only Mode**: Enables just the self-healing component
4. **Adaptive Security Only Mode**: Enables just the security learning component
5. **Manual with Recommendations**: Provides recommendations without automatic actions
6. **Diagnostic Mode**: Runs diagnostics without taking actions
7. **Stop All Autonomous Systems**: Terminates all autonomous processes
8. **View System Status**: Shows the current status of all components
9. **Exit**: Quits the control interface

### Individual Component Control

Each component can also be controlled directly:

#### Self-Healing

```bash
# Start self-healing monitoring
python3 self_healing.py start

# Check self-healing status
python3 self_healing.py status

# Trigger self-test
python3 self_healing.py self-test

# Stop self-healing
python3 self_healing.py stop
```

#### Adaptive Security

```bash
# Start security monitoring
python3 adaptive_security.py start

# Check security status
python3 adaptive_security.py status

# Simulate a security event (for testing)
python3 adaptive_security.py simulate --type ceiling_violation --severity high

# Stop security monitoring
python3 adaptive_security.py stop
```

#### Meta-Orchestrator

```bash
# Start meta-orchestration
python3 meta_orchestrator.py start

# Check orchestrator status
python3 meta_orchestrator.py status

# Force decision evaluation
python3 meta_orchestrator.py evaluate

# Stop meta-orchestration
python3 meta_orchestrator.py stop
```

## Testing the System

The integration test suite validates the functionality of the autonomous system:

```bash
# Run all tests
python3 test_autonomous_system.py

# Run specific test
python3 test_autonomous_system.py EPOCH5AutonomousTest.test_09_start_meta_orchestrator
```

## Generating Test Data

Generate synthetic data to evaluate system performance:

```bash
# Generate all types of test data for 7 days
./generate_test_data.py --days 7

# Generate only component metrics with higher anomaly rate
./generate_test_data.py --type metrics --days 3 --anomaly-probability 0.1

# Generate only security events with more events per day
./generate_test_data.py --type security --days 5 --security-events-per-day 20

# Generate only system decisions
./generate_test_data.py --type decisions --days 10 --decisions-per-day 30
```

The generated data will be stored in the `test_data` directory.

## Visualizing Results

Visualize test data or live system data:

```bash
# Visualize all data types
./visualize_data.py

# Visualize only component metrics
./visualize_data.py --type metrics

# Visualize only security events
./visualize_data.py --type security

# Visualize only system decisions
./visualize_data.py --type decisions

# Specify custom data directory
./visualize_data.py --data-dir ./my_custom_data
```

Visualizations will be saved in the `visualizations` directory.

## Integration with Ceiling Management

The autonomous system integrates with the existing ceiling management system:

```bash
# Check ceiling values
python3 ceiling_manager.py list-configs

# Create a new ceiling configuration
python3 ceiling_manager.py create-config my-config --tier professional

# Enforce a ceiling value
python3 ceiling_manager.py enforce my-config budget 500

# Monitor security alerts
python3 ceiling_manager.py security-alerts
```

## Workflow Example

Here's a typical workflow for using the autonomous system:

1. Start the autonomous control interface:
   ```bash
   ./autonomous_control.sh
   ```

2. Select option 1 to enable Full Autonomous Mode

3. Monitor the system status periodically:
   ```bash
   python3 meta_orchestrator.py status
   ```

4. Generate test data to evaluate performance:
   ```bash
   ./generate_test_data.py
   ```

5. Visualize the results:
   ```bash
   ./visualize_data.py
   ```

6. When finished, stop all autonomous systems:
   ```bash
   ./autonomous_control.sh
   # Then select option 7
   ```

## Troubleshooting

### Common Issues

1. **Components not starting**:
   - Check for error messages in the console output
   - Verify that all scripts have executable permissions
   - Ensure required Python packages are installed

2. **System not responding to anomalies**:
   - Check component status to ensure they're running
   - Verify that the anomaly thresholds are configured correctly
   - Check logs for any detection or decision-making issues

3. **Visualization errors**:
   - Ensure matplotlib and pandas are installed
   - Verify that test data exists in the expected directory
   - Check the visualization logs for specific error messages

### Log Files

The following log files can help diagnose issues:

- `self_healing.log`: Self-healing component logs
- `adaptive_security.log`: Security component logs
- `meta_orchestrator.log`: Orchestration component logs
- `test_data_generator.log`: Test data generation logs
- `visualization.log`: Data visualization logs
- `epoch5_integration_test.log`: Integration test logs

## Further Reading

For more detailed information about the system architecture, refer to the `AUTONOMOUS_ARCHITECTURE.md` file in this repository.
