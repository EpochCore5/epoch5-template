# Contributing to EPOCH5 Template

Thank you for your interest in contributing to the EPOCH5 Template project! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites
- Python 3.7+
- Node.js 14+ (for CI/CD pipeline)
- Bash shell environment
- Git

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/EpochCore5/epoch5-template.git
   cd epoch5-template
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Make scripts executable:
   ```bash
   chmod +x epoch5.sh
   ```

4. Test the installation:
   ```bash
   # Test Python integration
   python3 integration.py --help
   
   # Test Bash script
   DELAY_HOURS_P1_P2=0 DELAY_HOURS_P2_P3=0 ./epoch5.sh
   ```

## Development Workflow

### Making Changes
1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the coding standards below

3. Test your changes:
   ```bash
   # Test Python modules compile
   python3 -m py_compile *.py
   
   # Test shell script syntax
   bash -n epoch5.sh
   
   # Run integration tests
   python3 integration.py setup-demo
   python3 integration.py validate
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Brief description of your changes"
   ```

5. Push and create a pull request

### Coding Standards

#### Python Code
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Include docstrings for all functions and classes
- Handle exceptions gracefully with meaningful error messages
- Use the existing logging framework for integration events

#### Shell Scripts
- Use `set -euo pipefail` for error handling
- Quote variables to prevent word splitting
- Use meaningful function and variable names
- Include error checking for external dependencies

#### Documentation
- Update README.md if adding new features
- Add inline comments for complex logic
- Update CLI help text for new commands
- Include usage examples

## Testing Guidelines

### Python Modules
When adding or modifying Python code:
- Test that modules compile without errors
- Verify CLI commands work as expected
- Test error handling paths
- Ensure logging functions properly

### Shell Scripts  
When modifying shell scripts:
- Test syntax with `bash -n script.sh`
- Test with different environment variables
- Verify file operations work correctly
- Test error conditions

## Architecture Overview

The EPOCH5 Template consists of several integrated components:

### Core Components
- **Agent Management**: Decentralized identifiers and registry system
- **Policy & Security**: Rule enforcement with quorum requirements
- **DAG Management**: Directed Acyclic Graph execution
- **Cycle Execution**: Budget control and latency tracking
- **Data Integrity**: Capsule storage with Merkle proofs
- **Meta-Capsules**: System state capture and ledger integration

### Integration Layer
- `integration.py`: Main orchestration script providing unified CLI
- `epoch5.sh`: One-shot triple-pass capsule script for data processing

## Contribution Areas

We welcome contributions in these areas:

### High Priority
- Unit and integration test implementation
- Error handling improvements
- CLI usability enhancements
- Documentation and examples

### Medium Priority
- Performance optimizations
- Input validation enhancements
- Configuration management
- Security improvements

### Future Enhancements
- Plugin architecture development
- Advanced monitoring capabilities
- Extended API functionality
- Community examples and templates

## Code Review Process

1. All changes require pull request review
2. Ensure code follows the established patterns
3. Test changes thoroughly before submitting
4. Update documentation as needed
5. Address reviewer feedback promptly

## Questions and Support

For questions or support:
- Create an issue in the GitHub repository
- Include detailed information about your environment
- Provide steps to reproduce any problems
- Check existing issues for similar questions

## Commercial Use Policy

Please note that this repository is not open source. Commercial use, distribution, or modification requires explicit written permission. For commercial licensing inquiries, contact: jryan2k19@gmail.com

## License

All contributions will be subject to the same terms as the main project. By contributing, you agree that your contributions will be owned by EpochCore Business and subject to the project's licensing terms.