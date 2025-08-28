FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    make \
    curl \
    wget \
    unzip \
    vim \
    jq \
    netcat \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspaces/epoch5-template

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/workspaces/epoch5-template

# Create a non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install pytest pytest-cov black flake8 mypy isort bandit pre-commit

# Create necessary directories
RUN mkdir -p /workspaces/epoch5-template/archive/EPOCH5/agents \
    /workspaces/epoch5-template/archive/EPOCH5/logs \
    /workspaces/epoch5-template/archive/EPOCH5/capsules \
    /workspaces/epoch5-template/archive/EPOCH5/policies \
    && chown -R $USERNAME:$USERNAME /workspaces/epoch5-template

# Set up pre-commit hooks
COPY .pre-commit-config.yaml .
RUN git init && pre-commit install

# Switch to non-root user
USER $USERNAME

# Port for ceiling dashboard
EXPOSE 8080

# Entry point - default command when the container starts
CMD ["/bin/bash"]
