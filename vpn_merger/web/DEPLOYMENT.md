# Enhanced Free Nodes Aggregator - Deployment Guide

Complete deployment guide for the production-ready Free Nodes Aggregator with SQLite persistence and scheduling.

## 🚀 Quick Deployment

### 1. Prerequisites
- Docker and Docker Compose installed
- Port 8000 available
- 2GB+ RAM for health checks
- Network access to source URLs

### 2. One-Command Setup
```bash
cd vpn_merger/web
chmod +x setup-free-nodes.sh
./setup-free-nodes.sh
```

### 3. Verify Deployment
```bash
# Check service status
curl http://localhost:8000/health

# View running containers
docker-compose -f compose.free-nodes.yml ps
```

## 🐳 Docker Deployment

### Basic Deployment
```bash
# Build and start
docker-compose -f compose.free-nodes.yml up -d --build

# View logs
docker-compose -f compose.free-nodes.yml logs -f

# Stop service
docker-compose -f compose.free-nodes.yml down
```

### Production Configuration
```yaml
# docker-compose.prod.yml
version: "3.8"
services:
  free-nodes-api:
    build: .
    container_name: free_nodes_api_prod
    environment:
      - DB_URL=sqlite+aiosqlite:///./data/free-nodes.db
      - RATE_LIMIT_RPM=60
      - HEALTH_CONCURRENCY=40
      - REFRESH_EVERY_MIN=30
      - CORS_ORIGINS=https://yourdomain.com
      - API_KEY=your-secret-key
    volumes:
      - ./data:/app/data:rw
      - ./logs:/app/logs:rw
    ports:
      - "8000:8000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Environment Variables
| Variable | Production | Development | Description |
|----------|------------|-------------|-------------|
| `DB_URL` | `sqlite+aiosqlite:///./data/free-nodes.db` | Same | Database location |
| `RATE_LIMIT_RPM` | `60` | `120` | Rate limiting |
| `HEALTH_CONCURRENCY` | `40` | `60` | Health check concurrency |
| `REFRESH_EVERY_MIN` | `30` | `20` | Refresh interval |
| `CORS_ORIGINS` | `https://yourdomain.com` | `*` | Allowed origins |
| `API_KEY` | `your-secret-key` | Not set | API protection |

## 🔧 Local Development

### Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn free_nodes_api_sqla:app --host 0.0.0.0 --port 8000 --reload
```

### Database Setup
```bash
# Create data directory
mkdir -p ./data

# Initialize database (automatic on first run)
# The service will create tables and seed sample data
```

## 🌐 Production Deployment

### Reverse Proxy Setup (Nginx)
```nginx
# /etc/nginx/sites-available/free-nodes
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Systemd Service
```ini
# /etc/systemd/system/free-nodes.service
[Unit]
Description=Free Nodes Aggregator
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/vpn_merger/web
ExecStart=/usr/bin/docker-compose -f compose.free-nodes.yml up -d
ExecStop=/usr/bin/docker-compose -f compose.free-nodes.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

### Enable and Start
```bash
sudo systemctl enable free-nodes
sudo systemctl start free-nodes
sudo systemctl status free-nodes
```

## 🔒 Security Hardening

### Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 8000/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
```

### API Key Protection
```bash
# Set environment variable
export API_KEY="your-super-secret-key"

# Or in .env file
echo "API_KEY=your-super-secret-key" >> .env
```

### CORS Restriction
```bash
# Restrict to specific domains
export CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

## 📊 Monitoring & Logging

### Health Checks
```bash
# Manual health check
curl -f http://localhost:8000/health

# Scheduled monitoring
*/5 * * * * curl -f http://localhost:8000/health || echo "Service down"
```

### Log Management
```bash
# View container logs
docker-compose -f compose.free-nodes.yml logs -f

# Log rotation (if using systemd)
sudo journalctl -u free-nodes -f
```

### Metrics Collection
```bash
# Get node count
curl -s http://localhost:8000/api/nodes.json | jq length

# Check source count
curl -s http://localhost:8000/api/sources | jq '.sources'
```

## 🔄 Backup & Recovery

### Database Backup
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/free-nodes"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp ./data/free-nodes.db $BACKUP_DIR/free-nodes_$DATE.db
# Keep last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

### Recovery Procedure
```bash
# Stop service
docker-compose -f compose.free-nodes.yml down

# Restore database
cp /backup/free-nodes/free-nodes_20241201_120000.db ./data/free-nodes.db

# Restart service
docker-compose -f compose.free-nodes.yml up -d
```

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check Docker status
docker system info

# Check port availability
netstat -tlnp | grep :8000

# Check file permissions
ls -la free_nodes_api_sqla.py
ls -la requirements.txt
```

### Health Check Failures
```bash
# Check container logs
docker-compose -f compose.free-nodes.yml logs free-nodes-api

# Test network connectivity
docker exec free_nodes_api ping -c 3 google.com

# Check resource usage
docker stats free_nodes_api
```

### Database Issues
```bash
# Check database file
ls -la ./data/free-nodes.db

# Verify SQLite integrity
docker exec -it free_nodes_api sqlite3 /app/data/free-nodes.db "PRAGMA integrity_check;"

# Check disk space
df -h ./data
```

## 📈 Performance Tuning

### Resource Limits
```yaml
# Add to docker-compose.yml
services:
  free-nodes-api:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

### Database Optimization
```bash
# Optimize SQLite
docker exec -it free_nodes_api sqlite3 /app/data/free-nodes.db "VACUUM;"
docker exec -it free_nodes_api sqlite3 /app/data/free-nodes.db "ANALYZE;"
```

### Health Check Tuning
```bash
# Reduce concurrency for low-resource systems
export HEALTH_CONCURRENCY=20

# Increase timeout for slow networks
export CONNECT_TIMEOUT=5.0
```

## 🔄 Updates & Maintenance

### Update Procedure
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f compose.free-nodes.yml down
docker-compose -f compose.free-nodes.yml up -d --build

# Verify update
curl http://localhost:8000/health
```

### Scheduled Maintenance
```bash
# Add to crontab
# Weekly database optimization
0 3 * * 0 docker exec free_nodes_api sqlite3 /app/data/free-nodes.db "VACUUM;"

# Daily backup
0 2 * * * /path/to/backup.sh

# Monthly log rotation
0 4 1 * * docker system prune -f
```

## 📚 Advanced Configurations

### Multi-Instance Setup
```yaml
# docker-compose.scale.yml
version: "3.8"
services:
  free-nodes-api:
    build: .
    environment:
      - DB_URL=sqlite+aiosqlite:///./data/free-nodes.db
    volumes:
      - ./data:/app/data:rw
    ports:
      - "8000-8002:8000"
    deploy:
      replicas: 3
```

### Load Balancer
```nginx
# Nginx upstream configuration
upstream free_nodes {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://free_nodes;
    }
}
```

---

**Production Ready**: This deployment guide covers all aspects of running the Enhanced Free Nodes Aggregator in production environments with proper security, monitoring, and maintenance procedures.
