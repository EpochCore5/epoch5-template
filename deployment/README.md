# EPOCH5 Deployment Guide

This directory contains deployment configurations for the EPOCH5 Template project across different environments and cloud platforms.

## Directory Structure

```
deployment/
├── aws/              # AWS-specific configurations
├── azure/            # Azure-specific configurations
├── gcp/              # Google Cloud Platform configurations
└── kubernetes/       # Kubernetes manifests
    ├── deployment.yaml   # Application deployments (stable + canary)
    ├── service.yaml      # Services and ingress
    └── storage.yaml      # Persistent volumes and config maps
```

## Quick Deployment

### Kubernetes

```bash
# Apply all Kubernetes manifests
kubectl apply -f deployment/kubernetes/

# Check deployment status
kubectl get pods,svc,ingress -l app=epoch5

# Access the application
kubectl port-forward service/epoch5-stable 8080:80
```

### Docker Compose

```bash
# Full monitoring stack
docker-compose up -d

# Development environment
docker-compose -f docker-compose.dev.yml up
```

## Deployment Strategies

### 1. Blue/Green Deployment

Zero-downtime deployment by maintaining two identical environments:

```bash
./scripts/deploy-blue-green.sh blue latest
```

### 2. Canary Deployment

Gradual rollout with traffic splitting:

```bash
./scripts/deploy-canary.sh latest ghcr.io/epochcore5/epoch5-template 10
```

### 3. Rolling Deployment

Standard Kubernetes rolling update:

```bash
kubectl set image deployment/epoch5-stable epoch5-app=ghcr.io/epochcore5/epoch5-template:v1.1.0
kubectl rollout status deployment/epoch5-stable
```

## Monitoring

Access monitoring dashboards:

- **Application**: http://localhost:8080 (health, metrics, status)
- **Grafana**: http://localhost:3000 (admin/epoch5admin)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601

## Scaling

```bash
# Scale stable deployment
kubectl scale deployment/epoch5-stable --replicas=5

# Horizontal Pod Autoscaler
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: epoch5-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: epoch5-stable
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
EOF
```

## Troubleshooting

### Common Issues

1. **Pod not starting**: Check logs with `kubectl logs -l app=epoch5`
2. **Health check failing**: Verify `/health` endpoint accessibility
3. **Ingress not working**: Check ingress controller and DNS configuration

### Debugging Commands

```bash
# Check pod status
kubectl describe pod <pod-name>

# View application logs
kubectl logs -f -l app=epoch5

# Execute shell in pod
kubectl exec -it <pod-name> -- /bin/bash

# Check resource usage
kubectl top pods -l app=epoch5
```

## Security

- All containers run as non-root user (UID 1000)
- Network policies restrict inter-pod communication
- Secrets are mounted as environment variables
- TLS encryption for ingress traffic

## Backup and Recovery

```bash
# Backup persistent volumes
kubectl create job backup-$(date +%s) --from=cronjob/backup-cron

# Restore from backup
kubectl apply -f backup-restore-job.yaml
```

For detailed CI/CD pipeline documentation, see [CICD_ENHANCEMENT.md](../CICD_ENHANCEMENT.md).