# CI/CD Pipeline

The EPOCH5 template repository is equipped with a robust CI/CD pipeline that ensures code quality, security, and reliable deployments.

![CI/CD Pipeline](https://mermaid.ink/img/pako:eNqVVE1v2zAM_SuEThkCdHHTbjlsQJFsWy_dhaCXgpZom4gsapSUxUXQ_76P_kh36C5rDrJI8T2-R5GXoCuFkIQ1vhkK2Dn6Bff01EB0IVWBZw6vBr9tSgXX6hkPxSsZ2_JWJynueLVzDbx5C46NPMNpTTLBjt9prQvrOZs6Urd4h5YWk0sGdmiZNnCnpLFLvHp_9-3Hz5_ffz1I07D7sXVMc2tEDW0xSk92PfVn2XtDLWXi4MjtYTnH5Sg_GxcRTOv4LN1o1ZJfUJGFfBYH_lKswkMR6yp1V7L7T-dO5osSxmNXkHRMhm2NJDO-kn8xRHM9Dew_Q0bCMQ4Ni9MqRgPCxlYOq9KaAjlrGXmOvZR66yydecq28MJacJKNOeQXnfV4eJrWYgcCIxZAVqsE58QpCMQZXA9uxWxU1gHJz73-vVJZsUu_OtPy0I7J0qBx5kAKUOV2CAtZCNUkTnuT_0jkGopGXBDYY5AYXejhkjgsCGgNkBJtUhQv4YrRRjMpqCuNRWzXYe0xNMqjZB_GDsGLB2bRaFo_CLBn5_wkq8kYGw5xkH8ZqCrPPbCXWYRpBh-s4n3ycXPNRQZJNxqSJFSb-O2KomrGdDRRGE5oTKbHLBcndGUyqvGH-sRe4qB8u4CQc-Ej_WbzEoKtVj2IpEgL4WI_Dd7D55XoOahBWR4UDWkS6tF6QqoG5ckkCLdO9mnWzx9UM9Zyaj84jAXUmtV32UR-KxOlfUyM5bBL8_VsNv1dZnQcJk9tIQdJQFNbRjzJGpzVWnIZGIaIAytR1n5j8-VyNgvGEBKfkz8B2lDe0w)

## CI/CD Pipeline Features

### 1. Automated Code Quality Checks
- **Linting & Formatting**: Enforces code standards with Black, Flake8, and Pylint
- **Static Type Checking**: Validates type annotations with MyPy
- **Import Sorting**: Ensures organized imports with isort
- **Pre-commit Hooks**: Catches issues before they enter the codebase

### 2. Comprehensive Testing Strategy
- **Multi-Platform Testing**: Tests across Linux, macOS, and Windows
- **Python Version Matrix**: Validates compatibility with Python 3.8-3.11
- **Coverage Enforcement**: Maintains minimum 80% code coverage
- **Strategic Test Categories**: Unit, integration, and end-to-end tests
- **StrategyDECK-specific Tests**: Dedicated testing for the StrategyDECK agent

### 3. Security Scanning
- **Dependency Vulnerability Scanning**: Checks for vulnerable packages with Safety
- **Code Security Analysis**: Identifies security issues with Bandit
- **Secret Detection**: Prevents credential leaks with GitLeaks
- **CodeQL Deep Analysis**: Advanced security analysis with GitHub CodeQL

### 4. Performance Testing
- **Benchmark Tests**: Tracks performance metrics over time
- **Load Testing**: Validates system behavior under heavy loads
- **StrategyDECK Performance**: Specialized testing for agent performance

### 5. Automated Documentation
- **API Documentation Generation**: Creates documentation with Sphinx
- **README Validation**: Ensures documentation stays current
- **Documentation Deployment**: Publishes to GitHub Pages

### 6. Containerization
- **Docker Image Building**: Creates optimized container images
- **Multi-stage Builds**: Separate development, testing, and production stages
- **Docker Compose**: Complete local development environment

### 7. Deployment Automation
- **Environment-based Deployment**: Different workflows for staging and production
- **GitHub Release Creation**: Automated versioning and release notes
- **Artifact Publishing**: Packaging and distribution

### 8. Continuous Monitoring
- **Status Reporting**: Comprehensive pipeline summary reports
- **Notification System**: Alerts via Slack for pipeline events
- **Performance Tracking**: Monitors execution times across pipeline stages

## Using the CI/CD Pipeline

### Local Development

Run the pipeline locally before pushing changes:

```bash
# Run all checks locally (equivalent to CI)
make pipeline-dry-run

# Run specific stages
make format lint type-check security test
```

### Docker Testing

Test in an isolated environment:

```bash
# Build and test with Docker
make docker-test

# Run full environment with docker-compose
make docker-compose-up
```

### GitHub Actions Workflows

The pipeline automatically runs on:
- **Push** to main or develop branches
- **Pull Requests** to main or develop
- **Weekly Schedule** for security scanning (Mondays at 2 AM)
- **Manual Trigger** through GitHub UI

### Deployment Process

1. **Create a Release Branch**: `release/vX.Y.Z`
2. **Push to Trigger CI**: Automated testing and validation
3. **Merge to Main**: Triggers production deployment
4. **Automated Release**: Creates GitHub Release with version tag

### CI/CD Configuration Files

- `.github/workflows/ci-cd.yml`: Main CI/CD pipeline
- `.github/workflows/codeql-analysis.yml`: Security analysis
- `.github/dependabot.yml`: Dependency updates
- `.pre-commit-config.yaml`: Pre-commit hooks
- `pyproject.toml`: Build and tool configuration
- `setup.cfg`: Package metadata and test settings
- `Dockerfile`: Container definition
- `docker-compose.yml`: Multi-service environment

## Pipeline Status and Monitoring

View the current status of the pipeline on the GitHub Actions tab:

- **Main Branch Status**: [![CI/CD Pipeline](https://github.com/EpochCore5/epoch5-template/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/EpochCore5/epoch5-template/actions/workflows/ci-cd.yml)
- **Develop Branch Status**: [![CI/CD Pipeline](https://github.com/EpochCore5/epoch5-template/actions/workflows/ci-cd.yml/badge.svg?branch=develop)](https://github.com/EpochCore5/epoch5-template/actions/workflows/ci-cd.yml)
- **CodeQL Analysis**: [![CodeQL Analysis](https://github.com/EpochCore5/epoch5-template/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/EpochCore5/epoch5-template/actions/workflows/codeql-analysis.yml)

## Best Practices for Contributors

1. **Run Pre-commit Hooks**: Install with `pre-commit install`
2. **Run Tests Locally**: Use `make test` before committing
3. **Check Security**: Run `make security` to identify issues
4. **Review Pipeline Results**: Address any failing checks promptly
5. **Update Documentation**: Keep README and docs in sync with code
6. **Follow Branching Strategy**: 
   - Feature branches: `feature/your-feature-name`
   - Bug fixes: `fix/issue-description`
   - Release branches: `release/vX.Y.Z`

## Continuous Improvement

The pipeline itself follows the principles of continuous improvement:

- **Weekly Dependency Updates**: Automated with Dependabot
- **Scheduled Security Scans**: Regular vulnerability checks
- **Pipeline Performance Metrics**: Tracked and optimized over time
- **Tool Version Updates**: Keeps analysis tools current
