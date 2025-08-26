# Development Setup Guide

This guide will help you set up a development environment for the EPOCH5 Template project.

## Prerequisites

- Python 3.8 or higher
- Git

## Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/EpochCore5/epoch5-template.git
   cd epoch5-template
   ```

2. **Set up virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_integration.py -v
```

### Code Formatting and Linting

```bash
# Format code with Black
black .

# Check code with flake8
flake8 .

# Run security checks
bandit -r . --skip B101
```

### Running the System

```bash
# Set up demo environment
python integration.py setup-demo

# Check system status
python integration.py status

# Run complete workflow
python integration.py run-workflow

# Launch ceiling dashboard
bash ceiling_launcher.sh
```

## Project Structure

```
epoch5-template/
├── agent_management.py     # Agent DID and registry management
├── capsule_metadata.py     # Data integrity and storage
├── ceiling_manager.py      # Dynamic resource management
├── cycle_execution.py      # Task execution and consensus
├── dag_management.py       # Directed acyclic graph management
├── integration.py          # Main system integration
├── meta_capsule.py         # System state capture
├── policy_grants.py        # Security policies and grants
├── health_server.py        # HTTP health check server
├── tests/                  # Test suite
│   ├── test_integration.py
│   ├── test_agent_management.py
│   ├── test_policy_grants.py
│   └── test_capsule_metadata.py
├── .github/workflows/      # CI/CD pipelines
├── deployment/             # Deployment configurations
│   ├── kubernetes/         # Kubernetes manifests
│   ├── aws/               # AWS configurations
│   ├── azure/             # Azure configurations
│   └── README.md          # Deployment guide
├── infrastructure/         # Infrastructure as Code
│   └── terraform/         # Terraform configurations
├── monitoring/            # Monitoring stack configurations
│   ├── prometheus/        # Prometheus config and rules
│   ├── grafana/          # Grafana dashboards
│   ├── logstash/         # Log processing config
│   └── alertmanager/     # Alerting configuration
├── scripts/              # Deployment and utility scripts
│   ├── deploy-blue-green.sh  # Blue/green deployment
│   ├── deploy-canary.sh      # Canary deployment
│   ├── rollback.sh           # Emergency rollback
│   └── setup-env.sh          # Environment setup
├── Dockerfile            # Container build configuration
├── docker-compose.yml    # Full monitoring stack
├── docker-compose.dev.yml # Development environment
└── CICD_ENHANCEMENT.md   # CI/CD pipeline documentation
```

## Testing Guidelines

1. **Write tests for all new features**
2. **Aim for >80% test coverage**
3. **Use descriptive test names**
4. **Include both positive and negative test cases**
5. **Use fixtures for test data setup**

## Code Style Guidelines

- Follow PEP 8 style guide
- Use Black for automatic formatting
- Maximum line length: 88 characters
- Use type hints where appropriate
- Write clear docstrings

## Security Considerations

- Never commit secrets or credentials
- Use `secrets` module instead of `random` for cryptographic purposes
- Validate all user inputs
- Follow secure coding practices

## Troubleshooting

### Common Issues

**ImportError: No module named 'networkx'**
- NetworkX is optional. The system will use basic DAG validation if not installed.
- Install with: `pip install networkx`

**Permission denied on ceiling_launcher.sh**
- Make script executable: `chmod +x ceiling_launcher.sh`

**Tests failing with fixture errors**
- Ensure you're running tests from the project root directory
- Check that test dependencies are installed: `pip install pytest pytest-cov`

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes and add tests
3. Ensure all tests pass: `pytest`
4. Format your code: `black .`
5. Submit a pull request

For detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).