# Deployment Guide

## Docker Deployment

### Build the Docker image
```bash
docker build -t cleanconfigs-submerger:latest -f Dockerfile .
```

### Run the container
```bash
docker run --rm -p 8001:8001 cleanconfigs-submerger:latest
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.19+)
- kubectl configured

### Deploy to Kubernetes
```bash
# Apply the deployment manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -l app=cleanconfigs-submerger
```

### Configuration
- Configure secrets, persistent volumes, and horizontal pod autoscaling as needed
- See `k8s/` directory for deployment manifests

## Production Considerations

- Set up proper logging and monitoring
- Configure resource limits and requests
- Use secrets for sensitive configuration
- Set up health checks and readiness probes
- Consider using a reverse proxy for API endpoints

