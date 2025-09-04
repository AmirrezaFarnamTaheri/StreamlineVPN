# Enhanced Features Installation Guide

## Overview

This guide provides detailed installation instructions for the enhanced features of the VPN Subscription Merger system. These features include machine learning capabilities, advanced caching, performance optimization, and comprehensive testing frameworks.

## Prerequisites

### System Requirements

| Feature | Minimum Requirements | Recommended |
|---------|---------------------|-------------|
| **Basic System** | 2GB RAM, 2 CPU cores | 8GB RAM, 4 CPU cores |
| **ML Features** | 4GB RAM, 4 CPU cores | 16GB RAM, 8 CPU cores |
| **Redis Caching** | 1GB RAM, 1 CPU core | 4GB RAM, 2 CPU cores |
| **Performance Monitoring** | 2GB RAM, 2 CPU cores | 8GB RAM, 4 CPU cores |

### Operating System Support

- **Linux**: Ubuntu 20.04+, CentOS 8+, Debian 11+
- **macOS**: macOS 10.15+ (Catalina or later)
- **Windows**: Windows 10+ with WSL2 or native Python

### Python Version

- **Minimum**: Python 3.8
- **Recommended**: Python 3.10+
- **Latest**: Python 3.11+

## Installation Methods

### Method 1: Complete Installation (Recommended)

Install all enhanced features at once:

```bash
# Clone the repository
git clone https://github.com/your-org/CleanConfigs-SubMerger.git
cd CleanConfigs-SubMerger

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all enhanced features
pip install -r requirements-enhanced.txt

# Verify installation
python -c "import vpn_merger; print('✅ VPN Merger installed successfully')"
```

### Method 2: Selective Installation

Install only the features you need:

```bash
# Basic installation first
pip install -r requirements.txt

# Machine Learning features
pip install scikit-learn pandas numpy joblib lightgbm xgboost

# Advanced caching with Redis
pip install redis aioredis

# Performance monitoring
pip install psutil

# Development tools
pip install pytest pytest-cov pytest-asyncio pytest-mock
```

### Method 3: Docker Installation

Use Docker for isolated installation:

```bash
# Build with enhanced features
docker build -t vpn-merger-enhanced -f Dockerfile.enhanced .

# Run with enhanced features
docker run -d \
  --name vpn-merger \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/output:/app/output:rw \
  vpn-merger-enhanced
```

## Feature-Specific Installation

### 1. Machine Learning Features

#### Installation

```bash
# Core ML libraries
pip install scikit-learn pandas numpy joblib

# Advanced ML libraries (optional)
pip install lightgbm xgboost

# Online learning (optional)
pip install river

# Feature selection (optional)
pip install feature-engine
```

#### Configuration

```bash
# Enable ML features
export VPN_ML_ENABLED=true
export VPN_ML_MODEL_PATH=models/
export VPN_ML_PREDICTION_THRESHOLD=0.7

# Create models directory
mkdir -p models/
```

#### Training ML Models

```bash
# Train quality prediction model
python scripts/train_ml_models.py --model quality_predictor

# Train with custom data
python scripts/train_ml_models.py \
  --model quality_predictor \
  --data-path data/training_data.csv \
  --output-path models/quality_model.pkl
```

#### Verification

```python
# Test ML features
from vpn_merger.ml import QualityPredictor

predictor = QualityPredictor()
score = await predictor.predict_quality("vless://...")
print(f"Quality score: {score}")
```

### 2. Advanced Caching with Redis

#### Installation

```bash
# Install Redis client libraries
pip install redis aioredis

# Install Redis server (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

# Install Redis server (CentOS/RHEL)
sudo yum install redis
sudo systemctl start redis
sudo systemctl enable redis

# Install Redis server (macOS)
brew install redis
brew services start redis

# Install Redis server (Windows)
# Download from https://github.com/microsoftarchive/redis/releases
```

#### Configuration

```bash
# Enable Redis caching
export VPN_CACHE_ENABLED=true
export VPN_REDIS_URL=redis://localhost:6379/0

# Advanced Redis configuration
export VPN_REDIS_URL=redis://user:password@localhost:6379/0
export VPN_CACHE_TTL=3600
export VPN_CACHE_MAX_SIZE=10000
```

#### Redis Configuration

```bash
# /etc/redis/redis.conf
# Memory optimization
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Network
tcp-keepalive 60
timeout 300

# Restart Redis
sudo systemctl restart redis
```

#### Verification

```python
# Test Redis connection
import redis
import asyncio

async def test_redis():
    r = redis.Redis.from_url("redis://localhost:6379/0")
    r.set("test", "value")
    value = r.get("test")
    print(f"Redis test: {value}")

asyncio.run(test_redis())
```

### 3. Performance Optimization

#### Installation

```bash
# Performance monitoring
pip install psutil

# Memory profiling
pip install memory-profiler

# CPU profiling
pip install py-spy

# Network monitoring
pip install netifaces
```

#### Configuration

```bash
# Performance optimization settings
export VPN_CONCURRENT_LIMIT=100
export VPN_CHUNK_SIZE=2097152
export VPN_SEMAPHORE_LIMIT=50
export VPN_BLOOM_FILTER_SIZE=2000000

# Memory management
export VPN_MAX_MEMORY_MB=1024
export VPN_CLEANUP_THRESHOLD=0.8
export VPN_MONITORING_INTERVAL=30
```

#### System Optimization

```bash
# Linux kernel tuning
echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_congestion_control = bbr' >> /etc/sysctl.conf
sysctl -p

# File descriptor limits
echo '* soft nofile 65536' >> /etc/security/limits.conf
echo '* hard nofile 65536' >> /etc/security/limits.conf
```

#### Verification

```python
# Test performance optimization
from vpn_merger.core import get_performance_optimizer

optimizer = get_performance_optimizer()
report = await optimizer.get_performance_report()
print(f"Performance report: {report}")
```

### 4. Comprehensive Testing Framework

#### Installation

```bash
# Core testing framework
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Performance testing
pip install pytest-benchmark pytest-xdist

# Security testing
pip install bandit safety

# Code quality
pip install black flake8 mypy

# All testing dependencies
pip install -r requirements-dev.txt
```

#### Configuration

```bash
# Test configuration
export VPN_TEST_MODE=true
export VPN_TEST_TIMEOUT=30
export VPN_TEST_CONCURRENT=10

# Coverage configuration
export COVERAGE_THRESHOLD=80
```

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vpn_merger --cov-report=html

# Run performance benchmarks
pytest tests/test_performance_advanced.py -m benchmark

# Run security tests
pytest tests/test_security_comprehensive.py -m security

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest -m "integration"  # Integration tests only
pytest -m "network"  # Network tests only
```

## Environment-Specific Installation

### Development Environment

```bash
# Development setup
export VPN_DEBUG=true
export VPN_DEVELOPMENT=true
export VPN_LOG_LEVEL=DEBUG
export VPN_TEST_MODE=true

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Staging Environment

```bash
# Staging configuration
export VPN_LOG_LEVEL=INFO
export VPN_CACHE_ENABLED=true
export VPN_REDIS_URL=redis://staging-redis:6379/0
export VPN_ML_ENABLED=true

# Install staging dependencies
pip install -r requirements-enhanced.txt
```

### Production Environment

```bash
# Production configuration
export VPN_LOG_LEVEL=WARNING
export VPN_CACHE_ENABLED=true
export VPN_REDIS_URL=rediss://user:password@prod-redis:6380/0
export VPN_ML_ENABLED=true
export VPN_API_KEY=production-api-key

# Install production dependencies
pip install -r requirements-enhanced.txt

# Security hardening
pip install --no-deps -r requirements-enhanced.txt
```

## Docker Compose Setup

### Complete Stack

```yaml
# docker-compose.enhanced.yml
version: '3.8'

services:
  vpn-merger:
    build:
      context: .
      dockerfile: Dockerfile.enhanced
    container_name: vpn-merger-enhanced
    environment:
      - VPN_CACHE_ENABLED=true
      - VPN_REDIS_URL=redis://redis:6379/0
      - VPN_ML_ENABLED=true
      - VPN_LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config:ro
      - ./output:/app/output:rw
      - ./models:/app/models:rw
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    container_name: vpn-merger-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  postgres:
    image: postgres:15-alpine
    container_name: vpn-merger-postgres
    environment:
      - POSTGRES_DB=vpn_merger
      - POSTGRES_USER=vpn_merger
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  redis_data:
  postgres_data:
```

### Usage

```bash
# Start enhanced stack
docker-compose -f docker-compose.enhanced.yml up -d

# View logs
docker-compose -f docker-compose.enhanced.yml logs -f

# Stop stack
docker-compose -f docker-compose.enhanced.yml down
```

## Kubernetes Deployment

### Enhanced Deployment

```yaml
# k8s/enhanced-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vpn-merger-enhanced
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vpn-merger-enhanced
  template:
    metadata:
      labels:
        app: vpn-merger-enhanced
    spec:
      containers:
      - name: vpn-merger
        image: vpn-merger:enhanced
        env:
        - name: VPN_CACHE_ENABLED
          value: "true"
        - name: VPN_REDIS_URL
          value: "redis://redis-service:6379/0"
        - name: VPN_ML_ENABLED
          value: "true"
        - name: VPN_LOG_LEVEL
          value: "INFO"
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        - name: output-volume
          mountPath: /app/output
        - name: models-volume
          mountPath: /app/models
      volumes:
      - name: config-volume
        configMap:
          name: vpn-merger-config
      - name: output-volume
        persistentVolumeClaim:
          claimName: vpn-merger-output-pvc
      - name: models-volume
        persistentVolumeClaim:
          claimName: vpn-merger-models-pvc
```

## Troubleshooting

### Common Issues

#### 1. ML Dependencies Not Found

**Error**: `ModuleNotFoundError: No module named 'sklearn'`

**Solution**:
```bash
# Install scikit-learn
pip install scikit-learn

# Or install all ML dependencies
pip install -r requirements-enhanced.txt
```

#### 2. Redis Connection Failed

**Error**: `redis.exceptions.ConnectionError`

**Solution**:
```bash
# Check Redis status
sudo systemctl status redis

# Start Redis
sudo systemctl start redis

# Test connection
redis-cli ping
```

#### 3. Performance Issues

**Error**: High memory usage or slow performance

**Solution**:
```bash
# Check system resources
htop
free -h
df -h

# Optimize configuration
export VPN_CONCURRENT_LIMIT=50
export VPN_CHUNK_SIZE=1048576
export VPN_CACHE_ENABLED=true
```

#### 4. Test Failures

**Error**: Tests failing with import errors

**Solution**:
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests in verbose mode
pytest -v

# Run specific test
pytest tests/test_core_components.py::test_specific_function -v
```

### Verification Commands

```bash
# Check installation
python -c "import vpn_merger; print('✅ Basic installation OK')"

# Check ML features
python -c "from vpn_merger.ml import QualityPredictor; print('✅ ML features OK')"

# Check Redis connection
python -c "import redis; r=redis.Redis(); r.ping(); print('✅ Redis OK')"

# Check performance optimization
python -c "from vpn_merger.core import get_performance_optimizer; print('✅ Performance optimization OK')"

# Run basic tests
pytest tests/test_core_components.py -v
```

## Performance Tuning

### System-Level Tuning

```bash
# CPU governor
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Network optimization
echo 'net.core.rmem_max = 134217728' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' >> /etc/sysctl.conf
sysctl -p

# File descriptor limits
echo '* soft nofile 65536' >> /etc/security/limits.conf
echo '* hard nofile 65536' >> /etc/security/limits.conf
```

### Application-Level Tuning

```bash
# Optimal concurrency
export VPN_CONCURRENT_LIMIT=100

# Memory optimization
export VPN_CHUNK_SIZE=2097152
export VPN_MAX_MEMORY_MB=1024

# Cache optimization
export VPN_CACHE_TTL=7200
export VPN_CACHE_MAX_SIZE=10000
```

## Security Considerations

### Production Security

```bash
# Use secure Redis connection
export VPN_REDIS_URL=rediss://user:password@redis.example.com:6380/0

# Enable API authentication
export VPN_API_KEY=your-secure-api-key

# Use secure logging
export VPN_LOG_LEVEL=WARNING
export VPN_LOG_FILE=/var/log/vpn-merger.log

# Disable debug mode
export VPN_DEBUG=false
export VPN_DEVELOPMENT=false
```

### Network Security

```bash
# Firewall configuration
sudo ufw allow 8000/tcp
sudo ufw allow 6379/tcp  # Redis (if external)
sudo ufw enable

# SSL/TLS configuration
export VPN_SSL_CERT=/path/to/cert.pem
export VPN_SSL_KEY=/path/to/key.pem
```

This comprehensive installation guide ensures that all enhanced features are properly installed and configured for optimal performance and security.
