# EPOCH5 Docker Development Container

This directory contains the configuration for the EPOCH5 development container, which provides a consistent and isolated environment for working with the EPOCH5 codebase.

## Features

- Pre-configured Python environment with all dependencies installed
- Development tools (linting, formatting, testing) pre-configured
- Support for VS Code Remote Development
- Instant onboarding for new contributors

## Getting Started

### Using VS Code

1. Install [VS Code](https://code.visualstudio.com/) and the [Remote Development extension pack](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)
2. Clone the repository: `git clone https://github.com/EpochCore5/epoch5-template.git`
3. Open the folder in VS Code
4. VS Code will prompt you to "Reopen in Container" - click this button
5. VS Code will build and start the container, and you'll be ready to develop

### Using Docker CLI

1. Clone the repository: `git clone https://github.com/EpochCore5/epoch5-template.git`
2. Navigate to the repository: `cd epoch5-template`
3. Build and run the development container:
   ```bash
   docker-compose -f .devcontainer/docker-compose.yml up -d
   ```
4. Attach to the container:
   ```bash
   docker exec -it epoch5-dev /bin/bash
   ```

## Development Workflow

Once inside the container, you can:

1. Run the test suite:
   ```bash
   pytest
   ```

2. Check code coverage:
   ```bash
   pytest --cov=. --cov-report=html
   ```

3. Run the demo:
   ```bash
   python integration.py setup-demo
   python integration.py status
   ```

4. Launch the dashboard:
   ```bash
   bash ceiling_launcher.sh
   ```

## Container Configuration

The development container is configured with:

- Python 3.10
- All dependencies from requirements.txt
- Development tools:
  - pytest
  - black
  - flake8
  - mypy
  - pre-commit
- VS Code extensions for Python development

## Customizing the Container

If you need to customize the container, you can modify:

- `.devcontainer/Dockerfile` - Container image definition
- `.devcontainer/devcontainer.json` - VS Code configuration
- `.devcontainer/docker-compose.yml` - Docker Compose configuration
