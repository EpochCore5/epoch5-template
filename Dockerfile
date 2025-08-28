FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.4.2

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements to cache them in docker layer
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Development stage with extra tools
FROM base as development

# Install development tools
RUN pip install --no-cache-dir pytest pytest-cov black flake8 mypy isort bandit pre-commit

# Copy pre-commit configuration
COPY .pre-commit-config.yaml .
RUN git init && pre-commit install-hooks

# Copy source code
COPY . .

# Testing stage for running tests
FROM development as testing

# Run tests
RUN pytest

# Production stage with minimal dependencies
FROM base as production

# Copy source code
COPY . .

# Set the entrypoint
ENTRYPOINT ["python", "epoch5.sh"]

# Default command
CMD ["--help"]
