#!/bin/bash
# EPOCH5 Rollback Script

set -e

echo "🔄 EPOCH5 Rollback Process Started..."

# Get the last successful deployment
LAST_SUCCESSFUL_TAG=$(git describe --tags --abbrev=0)
CURRENT_ENV="${1:-production}"

echo "Rolling back to: $LAST_SUCCESSFUL_TAG"
echo "Environment: $CURRENT_ENV"

# Function to rollback different deployment targets
rollback_kubernetes() {
    echo "🎯 Rolling back Kubernetes deployment..."
    kubectl rollout undo deployment/epoch5-app
    kubectl rollout status deployment/epoch5-app --timeout=300s
}

rollback_docker_compose() {
    echo "🐳 Rolling back Docker Compose deployment..."
    export IMAGE_TAG=$LAST_SUCCESSFUL_TAG
    docker-compose down
    docker-compose up -d
}

rollback_aws_ecs() {
    echo "☁️ Rolling back AWS ECS service..."
    # Get the previous task definition
    TASK_DEF=$(aws ecs describe-services --cluster epoch5-cluster --services epoch5-service --query 'services[0].taskDefinition' --output text)
    PREV_TASK_DEF=$(aws ecs list-task-definitions --family-prefix epoch5 --status ACTIVE --sort DESC --query 'taskDefinitionArns[1]' --output text)
    
    # Update service to use previous task definition
    aws ecs update-service --cluster epoch5-cluster --service epoch5-service --task-definition $PREV_TASK_DEF
}

# Health check after rollback
health_check() {
    local max_attempts=30
    local attempt=1
    
    echo "🔍 Verifying rollback health..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f "http://localhost:8080/health" >/dev/null 2>&1; then
            echo "✅ Rollback health check passed"
            return 0
        fi
        
        echo "⏳ Attempt $attempt/$max_attempts, retrying in 10s..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    echo "❌ Rollback health check failed"
    return 1
}

# Perform rollback based on available tools
if command -v kubectl >/dev/null 2>&1; then
    rollback_kubernetes
elif [ -f "docker-compose.yml" ]; then
    rollback_docker_compose
elif command -v aws >/dev/null 2>&1; then
    rollback_aws_ecs
else
    echo "❌ No supported deployment platform found"
    exit 1
fi

# Verify rollback
if health_check; then
    echo "✅ Rollback completed successfully!"
    
    # Notify team
    echo "📧 Sending rollback notification..."
    # Add notification logic here (Slack, email, etc.)
    
else
    echo "❌ Rollback failed verification"
    exit 1
fi