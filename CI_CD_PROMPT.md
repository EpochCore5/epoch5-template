# Leveraged CI/CD Pipeline Development Prompt

## System Context and Objectives
Create a comprehensive, enterprise-grade CI/CD pipeline for the EPOCH5 template repository that emphasizes security, quality, reliability, and performance. The pipeline should support Python-based agent development with advanced testing, security scanning, and deployment capabilities.

## Repository Overview
EPOCH5 is an agent-based framework focused on workflow automation, policy enforcement, and secure execution of tasks with advanced provenance tracking. It includes the StrategyDECK AI agent that enables autonomous learning and optimization of strategic processes.

## Key Components
- Core Python modules for agent management, policy enforcement, and workflow execution
- StrategyDECK AI agent with continuous improvement capabilities
- Testing infrastructure for unit, integration, and performance tests
- Docker-based development and deployment environment

## Required CI/CD Pipeline Features

### Code Quality
- Automated linting and formatting checks (Black, Flake8, Pylint)
- Type checking with MyPy
- Pre-commit hook integration
- Import sorting
- Code complexity analysis

### Testing Strategy
- Multi-platform testing (Linux, macOS, Windows)
- Python version matrix (3.8, 3.9, 3.10, 3.11)
- Coverage enforcement (minimum 80%)
- Test categorization (unit, integration, end-to-end)
- StrategyDECK-specific testing
- Performance and benchmark testing

### Security Scanning
- Dependency vulnerability scanning (Safety)
- Code security analysis (Bandit)
- Secret detection (GitLeaks)
- Advanced security analysis with GitHub CodeQL
- Container scanning
- SAST (Static Application Security Testing)

### Documentation
- Automated API documentation generation (Sphinx)
- Documentation validation and deployment

### Build and Packaging
- Python package building
- Docker image creation with multi-stage builds
- Artifact management

### Deployment Automation
- Environment-based deployment (staging vs. production)
- Release automation with semantic versioning
- GitHub Release creation
- Deployment verification

### Monitoring and Reporting
- Pipeline status reporting
- Notification system (Slack integration)
- Test result aggregation
- Performance metrics tracking

## Pipeline Architecture
- GitHub Actions as the primary CI/CD platform
- Matrix builds for multi-platform testing
- Parallel job execution for efficiency
- Conditional workflow paths based on branch and event type
- Caching strategies for dependencies and build artifacts

## Development Process Integration
- Pull request workflow with automated checks
- Branch protection rules
- Required status checks
- Automated code review

## Implementation Guidelines
- Use YAML for configuration files
- Follow the principle of "configuration as code"
- Implement proper error handling and reporting
- Include detailed comments and documentation
- Ensure pipeline is maintainable and extensible
- Optimize for both speed and reliability

## Deliverables
1. Main CI/CD workflow file (.github/workflows/ci-cd.yml)
2. CodeQL analysis workflow (.github/workflows/codeql-analysis.yml)
3. Dependabot configuration (.github/dependabot.yml)
4. Docker and docker-compose configurations
5. Pre-commit configuration
6. Build system configuration (pyproject.toml, setup.cfg)
7. Comprehensive CI/CD documentation
8. Pull request template

## Additional Considerations
- Pipeline should be self-healing when possible
- Include appropriate timeout and retry mechanisms
- Implement proper caching strategies
- Ensure secrets are properly managed
- Consider resource usage and optimization

## Success Criteria
- All quality checks pass on the main branch
- Security vulnerabilities are identified and addressed
- Deployment process is reliable and consistent
- Documentation is comprehensive and up-to-date
- Development team can easily understand and modify the pipeline
- CI/CD process is as automated as possible
