# StreamlineVPN Deployment Guide

## 🚀 Complete Production Deployment Configuration

This guide provides comprehensive deployment configurations for StreamlineVPN in production environments.

## 📋 Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [Kubernetes Deployment](#kubernetes-deployment)
3. [Monitoring & Observability](#monitoring--observability)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Infrastructure as Code](#infrastructure-as-code)
6. [Backup & Recovery](#backup--recovery)
7. [Security Configuration](#security-configuration)

## 🐳 Docker Deployment

### Production Dockerfile

The production Dockerfile uses multi-stage builds for optimal image size and security:

```dockerfile
# Multi-stage build for production
FROM python:3.11-slim AS builder
# ... (see Dockerfile.production)
```

### Docker Compose Stack

Complete production stack with all services:

```bash
# Start the complete stack
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f streamline

# Scale the application
docker-compose -f docker-compose.production.yml up -d --scale streamline=3
```

**Services included:**
- **StreamlineVPN**: Main application
- **Redis**: Caching and session storage
- **PostgreSQL**: Primary database
- **Elasticsearch**: Log aggregation and search
- **Kibana**: Log visualization
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **Nginx**: Load balancer and reverse proxy

## ☸️ Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f kubernetes/namespace.yaml

# Deploy configuration
kubectl apply -f kubernetes/configmap.yaml

# Deploy application
kubectl apply -f kubernetes/deployment.yaml

# Deploy service
kubectl apply -f kubernetes/service.yaml

# Deploy ingress
kubectl apply -f kubernetes/ingress.yaml

# Deploy HPA
kubectl apply -f kubernetes/hpa.yaml
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n streamline-vpn

# Check services
kubectl get services -n streamline-vpn

# Check ingress
kubectl get ingress -n streamline-vpn

# View logs
kubectl logs -f deployment/streamline-deployment -n streamline-vpn
```

## 📊 Monitoring & Observability

### Prometheus Configuration

Prometheus is configured to scrape metrics from all services:

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'streamline'
    static_configs:
      - targets: ['streamline:9090']
```

### Grafana Dashboards

Pre-configured dashboards for:
- **System Overview**: CPU, memory, disk usage
- **Application Metrics**: Request rates, response times, error rates
- **Business Metrics**: Config processing, source reputation
- **Infrastructure**: Database, Redis, Elasticsearch health

### Alerting Rules

Key alerts configured:
- High error rate (>10% for 5 minutes)
- High memory usage (>90% for 5 minutes)
- High response time (p95 > 2 seconds)
- Low cache hit rate (<50% for 10 minutes)
- Source discovery failures

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Automated pipeline includes:

1. **Testing**: Unit tests, integration tests, security scans
2. **Building**: Multi-stage Docker build with caching
3. **Deployment**: Automated Kubernetes deployment
4. **Verification**: Smoke tests and health checks

### Pipeline Triggers

- **Push to main**: Full production deployment
- **Pull requests**: Testing and security scans
- **Manual trigger**: On-demand deployment

### Secrets Required

Configure these secrets in GitHub:
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password
- `KUBECONFIG`: Kubernetes configuration

## 🏗️ Infrastructure as Code

### Terraform Configuration

Complete AWS infrastructure setup:

```bash
# Initialize Terraform
cd terraform
terraform init

# Plan deployment
terraform plan -var="db_password=your_secure_password"

# Deploy infrastructure
terraform apply -var="db_password=your_secure_password"
```

**Resources created:**
- EKS cluster with managed node groups
- RDS PostgreSQL instance
- ElastiCache Redis cluster
- S3 buckets for configs and backups
- CloudFront distribution
- VPC with public/private subnets
- Security groups and IAM roles

### Ansible Deployment

For traditional server deployment:

```bash
# Install Ansible
pip install ansible

# Deploy to production servers
ansible-playbook -i ansible/inventory.yml ansible/playbook.yml
```

## 💾 Backup & Recovery

### Automated Backups

Daily backup script includes:
- Database dump (PostgreSQL)
- Redis persistence file
- Configuration files
- Application data
- S3 upload with lifecycle policies

```bash
# Run backup manually
./scripts/backup.sh

# Schedule with cron
0 2 * * * /path/to/scripts/backup.sh
```

### Disaster Recovery

Recovery script for complete system restoration:

```bash
# Restore from specific date
./scripts/restore.sh 20240115
```

## 🔒 Security Configuration

### SSL/TLS

- Let's Encrypt certificates via cert-manager
- TLS 1.2+ only
- Strong cipher suites
- HSTS headers

### Network Security

- Private subnets for databases
- Security groups with minimal access
- VPC endpoints for AWS services
- Network ACLs

### Application Security

- Non-root container user
- Read-only filesystems where possible
- Security scanning in CI/CD
- Regular dependency updates

## 📈 Performance Optimization

### Horizontal Pod Autoscaling

```yaml
# kubernetes/hpa.yaml
spec:
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Caching Strategy

- **L1**: In-memory cache (1000 items)
- **L2**: Redis cache (distributed)
- **L3**: Disk cache (persistent)

### Database Optimization

- Connection pooling
- Read replicas for scaling
- Automated backups
- Performance monitoring

## 🚨 Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   kubectl top pods -n streamline-vpn

   # Scale up if needed
   kubectl scale deployment streamline-deployment --replicas=5 -n streamline-vpn
   ```

2. **Database Connection Issues**
   ```bash
   # Check database connectivity
   kubectl exec -it deployment/streamline-deployment -n streamline-vpn -- psql $POSTGRES_URL
   ```

3. **Cache Performance**
   ```bash
   # Check Redis status
   kubectl exec -it deployment/streamline-deployment -n streamline-vpn -- redis-cli ping
   ```

### Log Analysis

```bash
# Application logs
kubectl logs -f deployment/streamline-deployment -n streamline-vpn

# System logs
kubectl logs -f deployment/streamline-deployment -n streamline-vpn -c streamline

# Elasticsearch logs
docker-compose -f docker-compose.production.yml logs elasticsearch
```

## 📞 Support

For deployment issues:
1. Check the troubleshooting section
2. Review logs and metrics
3. Consult the monitoring dashboards
4. Contact the development team

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Update application
kubectl set image deployment/streamline-deployment streamline=streamlinevpn/app:v2.1.0 -n streamline-vpn

# Monitor rollout
kubectl rollout status deployment/streamline-deployment -n streamline-vpn
```

### Maintenance Windows

- **Database**: Weekly maintenance window
- **Infrastructure**: Monthly updates
- **Security**: Immediate for critical patches

---

**🎉 Congratulations!** You now have a complete, production-ready deployment configuration for StreamlineVPN with enterprise-grade monitoring, security, and scalability features.
