# EPOCH5 Template Development Makefile

.PHONY: help setup test lint format security clean demo strategydeck docker-build docker-test ci-local release docs pipeline-dry-run security-setup security-test security-scroll agent-security

help: ## Show this help message
	@echo "EPOCH5 Template Development Commands"
	@echo "==================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Set up development environment
	@bash dev-setup.sh

test: ## Run all tests with coverage
	pytest --cov=. --cov-report=html --cov-report=xml --cov-report=term-missing

test-fast: ## Run tests without coverage (faster)
	pytest -x -v

test-strategydeck: ## Run only StrategyDECK tests
	pytest -xvs tests/test_strategydeck_agent.py

lint: ## Run linting checks
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

format: ## Format code with Black
	black .

format-check: ## Check if code needs formatting
	black --check --diff .

type-check: ## Run type checking with mypy
	mypy --ignore-missing-imports .

security: ## Run security scans
	@echo "Running security checks..."
	@bandit -r . --skip B101 -f txt || true
	@safety check || true

security-setup: ## Set up EPOCH5 Security System
	@echo "Setting up EPOCH5 Security System..."
	@chmod +x setup_security.sh
	@./setup_security.sh

security-test: ## Test EPOCH5 Security System
	@echo "Testing EPOCH5 Security System..."
	@python3 epoch_audit.py verify

security-scroll: ## Generate EPOCH5 Audit Scroll
	@echo "Generating EPOCH5 Audit Scroll..."
	@python3 epoch_audit.py scroll --output ./archive/EPOCH5/audit/scrolls/audit_$(shell date +%Y%m%d_%H%M%S).txt

agent-security: ## Run Agent Security Controller
	@echo "Running Agent Security Controller..."
	@python3 agent_security.py report

clean: ## Clean up generated files
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "logs" -exec rm -rf {} + 2>/dev/null || true

demo: ## Run demo workflow
	python3 integration.py setup-demo
	python3 integration.py status
	python3 integration.py run-workflow

strategydeck: ## Run StrategyDECK agent demo
	@echo "Running StrategyDECK agent demo..."
	@python3 strategydeck_agent.py
	@echo "\nRunning StrategyDECK integration demo..."
	@python3 strategydeck_integration.py register
	@python3 strategydeck_integration.py execute --goal "Optimize resource allocation" --priority high
	@python3 strategydeck_integration.py status
	@echo "\nRunning continuous improvement system..."
	@python3 strategydeck_integration.py improvement status

strategydeck-improvement: ## Run StrategyDECK improvement cycle
	@echo "Running StrategyDECK continuous improvement cycle..."
	@python3 strategydeck_integration.py improvement run-cycle

status: ## Show system status
	python3 integration.py status

validate: ## Validate system integrity
	python3 integration.py validate

dashboard: ## Launch web dashboard
	bash ceiling_launcher.sh

install: ## Install dependencies
	pip install -r requirements.txt

dev-install: ## Install dependencies including development tools
	pip install -r requirements.txt
	pip install pre-commit
	pre-commit install

all-checks: format lint type-check security test ## Run all quality checks

ci: ## Run CI-like checks
	@echo "Running CI checks..."
	@$(MAKE) format-check
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) security
	@$(MAKE) test-fast

# Docker commands
docker-build: ## Build Docker image
	docker build -t epoch5-template:latest .

docker-test: docker-build ## Run tests in Docker
	docker run --rm epoch5-template:latest pytest

docker-run: docker-build ## Run app in Docker
	docker run --rm epoch5-template:latest

docker-compose-up: ## Start all services with docker-compose
	docker-compose up -d

docker-compose-down: ## Stop all services
	docker-compose down

# CI/CD Pipeline commands
pipeline-dry-run: ## Run CI pipeline locally
	@echo "Running CI/CD pipeline locally (dry run)..."
	@$(MAKE) clean
	@$(MAKE) setup
	@$(MAKE) all-checks
	@$(MAKE) docker-build
	@$(MAKE) docker-test
	@echo "Local CI/CD pipeline dry run completed successfully!"

docs: ## Generate documentation
	@echo "Generating documentation..."
	@mkdir -p docs
	@pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints myst-parser
	@cd docs && sphinx-quickstart -q --sep --project="EPOCH5 Template" --author="EpochCore5" --language=en || true
	@echo "import os" >> docs/conf.py
	@echo "import sys" >> docs/conf.py
	@echo "sys.path.insert(0, os.path.abspath('..'))" >> docs/conf.py
	@echo "extensions.append('sphinx.ext.autodoc')" >> docs/conf.py
	@echo "extensions.append('sphinx.ext.viewcode')" >> docs/conf.py
	@echo "extensions.append('sphinx.ext.napoleon')" >> docs/conf.py
	@echo "extensions.append('sphinx_autodoc_typehints')" >> docs/conf.py
	@sphinx-apidoc -o docs . tests setup.py
	@cd docs && make html
	@echo "Documentation generated in docs/_build/html/"

changelog: ## Generate changelog since last tag
	@echo "Generating changelog..."
	@git log $(shell git describe --tags --abbrev=0)..HEAD --pretty=format:"%h %s" > CHANGELOG.md

release: ## Prepare for release
	@echo "Preparing release..."
	@$(MAKE) clean
	@$(MAKE) all-checks
	@$(MAKE) changelog
	@$(MAKE) docs
	@echo "Ready for release! Don't forget to tag the release."

# Development shortcuts
t: test
l: lint  
f: format
s: security
c: clean
d: demo
sd: strategydeck
dc-up: docker-compose-up
dc-down: docker-compose-down