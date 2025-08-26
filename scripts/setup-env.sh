#!/bin/bash
# EPOCH5 Environment Setup Script for CI/CD

set -e

ENVIRONMENT="${1:-development}"
echo "🚀 Setting up EPOCH5 environment: $ENVIRONMENT"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs archive/EPOCH5

# Set up environment-specific configuration
case $ENVIRONMENT in
    "production")
        echo "⚙️ Configuring production environment..."
        export PYTHONPATH="/app"
        export LOG_LEVEL="INFO"
        export ENVIRONMENT="production"
        ;;
    "staging")
        echo "⚙️ Configuring staging environment..."
        export PYTHONPATH="/app"
        export LOG_LEVEL="DEBUG"
        export ENVIRONMENT="staging"
        ;;
    "development")
        echo "⚙️ Configuring development environment..."
        export PYTHONPATH="$(pwd)"
        export LOG_LEVEL="DEBUG"
        export ENVIRONMENT="development"
        ;;
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Initialize system
echo "🔧 Initializing EPOCH5 system..."
python3 integration.py setup-demo

# Verify setup
echo "✅ Verifying setup..."
python3 integration.py status

echo "🎉 Environment setup complete!"
echo "Environment: $ENVIRONMENT"
echo "Python Path: $PYTHONPATH"
echo "Log Level: $LOG_LEVEL"