# DocAI Deployment Guide

This guide provides comprehensive instructions for deploying DocAI in production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Traditional Server Deployment](#traditional-server-deployment)
6. [SSL/TLS Configuration](#ssltls-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Backup and Recovery](#backup-and-recovery)
9. [Performance Tuning](#performance-tuning)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

- Linux server (Ubuntu 20.04+ or CentOS 8+ recommended)
- Minimum 4GB RAM (8GB+ recommended for production)
- 20GB+ available disk space
- Docker and Docker Compose (for containerized deployment)
- PostgreSQL 13+ (for production database)
- Redis 6+ (for caching)
- Valid domain name with DNS configured (for SSL)

## Deployment Options

### Option 1: Docker Deployment (Recommended)

The easiest and most consistent deployment method using Docker Compose.

#### Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/docai.git
cd docai

# Copy and configure environment
cp .env.production.template .env.production
nano .env.production  # Edit with your settings

# Build and start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

#### Production Docker Configuration

1. **Update docker-compose.yml for production:**

```yaml
# Add resource limits
services:
  docai:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

2. **Configure persistent volumes:**

```bash
# Create volume directories
mkdir -p /data/docai/{uploads,logs,postgres,redis}
chown -R 1000:1000 /data/docai/{uploads,logs}
```

3. **Start with production profile:**

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Option 2: Kubernetes Deployment

For scalable, cloud-native deployments.

#### Kubernetes Manifests

Create `k8s/` directory with the following files:

**namespace.yaml:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: docai
```

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: docai
  namespace: docai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: docai
  template:
    metadata:
      labels:
        app: docai
    spec:
      containers:
      - name: docai
        image: yourusername/docai:latest
        ports:
        - containerPort: 8090
        env:
        - name: DATABASE_URI
          valueFrom:
            secretKeyRef:
              name: docai-secrets
              key: database-uri
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: docai-service
  namespace: docai
spec:
  selector:
    app: docai
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8090
  type: LoadBalancer
```

#### Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets
kubectl create secret generic docai-secrets \
  --from-literal=database-uri='postgresql://...' \
  --from-literal=groq-api-key='...' \
  -n docai

# Deploy application
kubectl apply -f k8s/
```

### Option 3: Traditional Server Deployment

For bare-metal or VPS deployments without containers.

#### System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib redis-server nginx \
  libreoffice poppler-utils tesseract-ocr

# Create application user
sudo useradd -m -s /bin/bash docai
sudo usermod -aG www-data docai
```

#### Application Setup

```bash
# Switch to docai user
sudo su - docai

# Clone repository
git clone https://github.com/yourusername/docai.git
cd docai

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.production.template .env.production
nano .env.production
```

#### Database Setup

```bash
# Create database and user
sudo -u postgres psql <<EOF
CREATE USER docai WITH PASSWORD 'secure_password';
CREATE DATABASE docai OWNER docai;
GRANT ALL PRIVILEGES ON DATABASE docai TO docai;
EOF

# Initialize database
python manage.py init
```

#### Systemd Service

Create `/etc/systemd/system/docai.service`:

```ini
[Unit]
Description=DocAI Document Intelligence Platform
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=docai
Group=docai
WorkingDirectory=/home/docai/docai
Environment="PATH=/home/docai/docai/venv/bin"
ExecStart=/home/docai/docai/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable docai
sudo systemctl start docai
sudo systemctl status docai
```

## SSL/TLS Configuration

### Using Let's Encrypt with Nginx

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Update Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;
    
    location / {
        proxy_pass http://localhost:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring Setup

### Prometheus & Grafana with Docker

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access interfaces
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin123)
```

### Configure Alerts

Edit `monitoring/alerts.yml` to customize alert rules:

```yaml
- alert: HighMemoryUsage
  expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Memory usage above 90%"
```

### Setup Alert Notifications

Configure Alertmanager for notifications:

```yaml
# alertmanager.yml
route:
  receiver: 'email-notifications'
  
receivers:
  - name: 'email-notifications'
    email_configs:
      - to: 'admin@yourdomain.com'
        from: 'alertmanager@yourdomain.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

## Backup and Recovery

### Automated Backups

Create `/home/docai/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/docai/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
pg_dump -U docai -h localhost docai | gzip > "$BACKUP_DIR/database.sql.gz"

# Backup uploads
tar -czf "$BACKUP_DIR/uploads.tar.gz" -C /home/docai/docai uploads/

# Backup configuration
cp /home/docai/docai/.env.production "$BACKUP_DIR/"

# Backup Redis
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/"

# Cleanup old backups (keep last 30 days)
find /backup/docai -type d -mtime +30 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR"
```

### Schedule Backups

```bash
# Add to crontab
0 2 * * * /home/docai/backup.sh >> /var/log/docai-backup.log 2>&1
```

### Recovery Procedure

```bash
# Restore database
gunzip -c /backup/docai/20240108_020000/database.sql.gz | psql -U docai -h localhost docai

# Restore uploads
tar -xzf /backup/docai/20240108_020000/uploads.tar.gz -C /home/docai/docai/

# Restore Redis
sudo systemctl stop redis
cp /backup/docai/20240108_020000/dump.rdb /var/lib/redis/
sudo systemctl start redis
```

## Performance Tuning

### PostgreSQL Optimization

Edit `/etc/postgresql/15/main/postgresql.conf`:

```ini
# Memory settings
shared_buffers = 1GB
effective_cache_size = 3GB
work_mem = 10MB
maintenance_work_mem = 256MB

# Connection settings
max_connections = 200

# Write performance
checkpoint_completion_target = 0.9
wal_buffers = 16MB
```

### Redis Configuration

Edit `/etc/redis/redis.conf`:

```ini
# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
```

### Application Performance

1. **Enable caching:**
```python
# In .env.production
CACHE_ENABLED=True
CACHE_TTL=3600
```

2. **Configure workers:**
```bash
# For Gunicorn
gunicorn main:app -w 4 -k gevent --worker-connections 1000
```

3. **Enable CDN for static files:**
```nginx
location /static {
    alias /var/www/docai/static;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check logs
docker-compose logs docai
journalctl -u docai -f

# Verify environment
python -c "from app.core.config import settings; print(settings)"
```

#### 2. Database Connection Issues

```bash
# Test connection
psql -U docai -h localhost -d docai -c "SELECT 1;"

# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*.log
```

#### 3. High Memory Usage

```bash
# Check memory usage
docker stats
free -h

# Analyze Python memory
pip install memory_profiler
python -m memory_profiler main.py
```

#### 4. Slow Performance

```bash
# Enable debug logging
DEBUG=True python main.py

# Profile requests
pip install flask-profiler
# Add profiler configuration to app
```

### Health Checks

```bash
# Application health
curl http://localhost:8090/health

# Database health
pg_isready -h localhost -U docai

# Redis health
redis-cli ping
```

### Log Analysis

```bash
# Parse error logs
grep -i error /var/log/docai/*.log | tail -50

# Analyze access patterns
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20
```

## Security Hardening

### Firewall Configuration

```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Fail2ban Setup

```bash
# Install fail2ban
sudo apt install fail2ban

# Create jail configuration
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[docai]
enabled = true
port = 80,443
filter = docai
logpath = /var/log/nginx/access.log
maxretry = 5
bantime = 3600
```

### Regular Updates

```bash
# Create update script
#!/bin/bash
cd /home/docai/docai
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
python manage.py migrate
sudo systemctl restart docai
```

## Maintenance Tasks

### Daily Tasks
- Monitor system health dashboards
- Check backup completion
- Review error logs

### Weekly Tasks
- Update dependencies
- Analyze performance metrics
- Review security logs

### Monthly Tasks
- Test disaster recovery
- Update SSL certificates
- Performance optimization review
- Security audit

## Support

For issues or questions:
- Check logs in `/var/log/docai/`
- Review monitoring dashboards
- Consult documentation at `/docs`
- Submit issues to GitHub repository