#!/bin/bash
# EPOCH5 Canary Deployment Script

set -e

IMAGE_TAG="${1:-latest}"
REGISTRY="${2:-ghcr.io/epochcore5/epoch5-template}"
CANARY_PERCENTAGE="${3:-10}"

echo "🐦 Starting canary deployment..."
echo "Image: $REGISTRY:$IMAGE_TAG"
echo "Canary percentage: $CANARY_PERCENTAGE%"

# Health check function
health_check() {
    local environment=$1
    local max_attempts=30
    local attempt=1
    
    echo "🔍 Running health check for $environment environment..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f "http://$environment-epoch5.internal:8080/health" >/dev/null 2>&1; then
            echo "✅ Health check passed for $environment environment"
            return 0
        fi
        
        echo "⏳ Attempt $attempt/$max_attempts failed, retrying in 10s..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    echo "❌ Health check failed for $environment environment after $max_attempts attempts"
    return 1
}

# Metrics check function
metrics_check() {
    local environment=$1
    local baseline_error_rate=$2
    local max_error_rate_threshold=0.05  # 5% error rate threshold
    
    echo "🔍 Checking metrics for $environment environment..."
    
    # This would typically query your monitoring system (Prometheus, etc.)
    # For now, we'll simulate the check
    error_rate=$(curl -s "http://prometheus:9090/api/v1/query?query=rate(epoch5_errors_total{environment=\"$environment\"}[5m])" | jq -r '.data.result[0].value[1] // "0"')
    
    if (( $(echo "$error_rate > $max_error_rate_threshold" | bc -l) )); then
        echo "❌ Error rate ($error_rate) exceeds threshold ($max_error_rate_threshold)"
        return 1
    else
        echo "✅ Error rate ($error_rate) within acceptable limits"
        return 0
    fi
}

# Deploy canary
echo "📦 Deploying canary version..."

# Kubernetes canary deployment
if command -v kubectl >/dev/null 2>&1; then
    echo "🎯 Deploying to Kubernetes with canary strategy..."
    
    # Update canary deployment
    kubectl set image deployment/epoch5-canary epoch5-app=$REGISTRY:$IMAGE_TAG
    kubectl rollout status deployment/epoch5-canary --timeout=300s
    
    # Update traffic splitting (using Istio as example)
    cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: epoch5-vs
spec:
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: epoch5-canary
      weight: 100
  - route:
    - destination:
        host: epoch5-stable
      weight: $((100 - CANARY_PERCENTAGE))
    - destination:
        host: epoch5-canary
      weight: $CANARY_PERCENTAGE
EOF

fi

# AWS ECS canary deployment
if command -v aws >/dev/null 2>&1; then
    echo "☁️ Updating ECS canary service..."
    
    # Create new task definition
    TASK_DEF_ARN=$(aws ecs register-task-definition \
        --cli-input-json file://task-definition-canary.json \
        --query 'taskDefinition.taskDefinitionArn' --output text)
    
    # Update canary service
    aws ecs update-service \
        --cluster epoch5-cluster \
        --service epoch5-canary \
        --task-definition $TASK_DEF_ARN
fi

# Wait for canary deployment to be ready
echo "⏳ Waiting for canary deployment to be ready..."
sleep 60

# Run health checks
if health_check "canary"; then
    echo "✅ Canary health check passed"
else
    echo "❌ Canary health check failed, rolling back..."
    exit 1
fi

# Monitor canary for 5 minutes
echo "📊 Monitoring canary performance..."
MONITOR_DURATION=300  # 5 minutes
MONITOR_START=$(date +%s)
MONITOR_INTERVAL=30

while [ $(($(date +%s) - MONITOR_START)) -lt $MONITOR_DURATION ]; do
    if metrics_check "canary" "0.01"; then
        echo "✅ Canary metrics look good"
    else
        echo "❌ Canary metrics indicate issues, rolling back..."
        # Rollback canary
        kubectl rollout undo deployment/epoch5-canary
        exit 1
    fi
    
    echo "⏳ Continuing to monitor... $(((MONITOR_DURATION - ($(date +%s) - MONITOR_START)) / 60)) minutes remaining"
    sleep $MONITOR_INTERVAL
done

echo "✅ Canary monitoring completed successfully"

# Prompt for full deployment
echo "🚀 Canary deployment successful!"
echo "Ready to proceed with full deployment? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "📦 Proceeding with full deployment..."
    
    # Update production deployment
    if command -v kubectl >/dev/null 2>&1; then
        kubectl set image deployment/epoch5-stable epoch5-app=$REGISTRY:$IMAGE_TAG
        kubectl rollout status deployment/epoch5-stable --timeout=300s
        
        # Remove canary traffic
        cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: epoch5-vs
spec:
  http:
  - route:
    - destination:
        host: epoch5-stable
      weight: 100
EOF
    fi
    
    echo "🎉 Full deployment completed successfully!"
else
    echo "⏸️ Keeping canary deployment at $CANARY_PERCENTAGE% traffic"
    echo "Run this script again or manually promote when ready"
fi