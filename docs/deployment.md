# Deployment Guide

## Overview

This guide covers deployment strategies for AI Code Review Squad across different environments. The application is designed to be cloud-native and supports multiple deployment options.

## Prerequisites

- Docker & Docker Compose
- Kubernetes cluster (optional)
- PostgreSQL 15+
- Redis 7+
- Domain name with SSL certificate
- GitHub App credentials

## Environment Configuration

### Environment Variables

Create `.env` files for each environment:

#### Production (.env.prod)
```bash
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-super-secure-secret-key
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@db:5432/aicodereview
REDIS_URL=redis://redis:6379

# GitHub
GITHUB_APP_ID=123456
GITHUB_PRIVATE_KEY_PATH=/app/secrets/github-private-key.pem
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# AI Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Monitoring
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_PORT=9090

# Security
CORS_ORIGINS=https://yourdomain.com
JWT_EXPIRATION=3600
```

## Docker Deployment

### Single Server Setup

1. **Prepare the server**:
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo apt-get install docker-compose-plugin

# Create application directory
mkdir /opt/ai-code-review-squad
cd /opt/ai-code-review-squad
```

2. **Create docker-compose.prod.yml**:
```yaml
version: '3.8'

services:
  backend:
    image: yourdockerhub/ai-code-review-squad-backend:latest
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://aiuser:${DB_PASSWORD}@db:5432/aicodereview
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./secrets:/app/secrets:ro
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    networks:
      - app-network

  frontend:
    image: yourdockerhub/ai-code-review-squad-frontend:latest
    restart: unless-stopped
    networks:
      - app-network

  db:
    image: postgres:15
    restart: unless-stopped
    environment:
      - POSTGRES_DB=aicodereview
      - POSTGRES_USER=aiuser
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

3. **Configure Nginx**:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            proxy_pass http://frontend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

4. **Deploy**:
```bash
# Set environment variables
export DB_PASSWORD=your-secure-password

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Kubernetes Deployment

### Prerequisites

```bash
# Install kubectl and helm
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
curl https://get.helm.sh/helm-v3.10.0-linux-amd64.tar.gz | tar xz
```

### Kubernetes Manifests

1. **Namespace**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-code-review
```

2. **ConfigMap**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: ai-code-review
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  REDIS_URL: "redis://redis:6379"
```

3. **Secrets**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: ai-code-review
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret>
  DATABASE_URL: <base64-encoded-db-url>
  GITHUB_PRIVATE_KEY: <base64-encoded-key>
```

4. **Backend Deployment**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: ai-code-review
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: yourdockerhub/ai-code-review-squad-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: ENVIRONMENT
        envFrom:
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

5. **Deploy to Kubernetes**:
```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n ai-code-review
kubectl logs -f deployment/backend -n ai-code-review
```

## Cloud Provider Specific

### AWS ECS

1. **Create ECS cluster**:
```bash
aws ecs create-cluster --cluster-name ai-code-review-cluster
```

2. **Create task definition**:
```json
{
  "family": "ai-code-review-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "yourdockerhub/ai-code-review-squad-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ]
    }
  ]
}
```

### Google Cloud Run

```bash
# Deploy backend
gcloud run deploy ai-code-review-backend \
  --image=yourdockerhub/ai-code-review-squad-backend:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated

# Deploy frontend
gcloud run deploy ai-code-review-frontend \
  --image=yourdockerhub/ai-code-review-squad-frontend:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
# Create resource group
az group create --name ai-code-review-rg --location eastus

# Deploy container
az container create \
  --resource-group ai-code-review-rg \
  --name ai-code-review-backend \
  --image yourdockerhub/ai-code-review-squad-backend:latest \
  --dns-name-label ai-code-review-api \
  --ports 8000
```

## Database Setup

### PostgreSQL Configuration

1. **Create database and user**:
```sql
CREATE DATABASE aicodereview;
CREATE USER aiuser WITH ENCRYPTED PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE aicodereview TO aiuser;
```

2. **Performance tuning** (postgresql.conf):
```
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.7
wal_buffers = 16MB
```

### Backup Strategy

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Create backup
pg_dump $DATABASE_URL > $BACKUP_DIR/backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/backup_$DATE.sql

# Remove backups older than 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

## Monitoring and Logging

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-code-review-backend'
    static_configs:
      - targets: ['backend:8000']
```

### Grafana Dashboard

Import the provided dashboard configuration from `monitoring/grafana-dashboard.json`.

### Log Aggregation

```yaml
# fluentd.conf
<source>
  @type tail
  path /app/logs/*.log
  pos_file /var/log/fluentd-app.log.pos
  tag app.logs
  format json
</source>

<match app.logs>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name ai-code-review
</match>
```

## SSL/TLS Configuration

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificates
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Health Checks

### Backend Health Check

```bash
curl -f http://localhost:8000/health || exit 1
```

### Database Health Check

```bash
pg_isready -h localhost -p 5432 -U aiuser
```

## Scaling

### Horizontal Scaling

```bash
# Docker Compose
docker-compose up --scale backend=3

# Kubernetes
kubectl scale deployment backend --replicas=5 -n ai-code-review
```

### Vertical Scaling

Update resource limits in deployment configurations and restart services.

## Troubleshooting

### Common Issues

1. **Database connection issues**:
   - Check DATABASE_URL format
   - Verify network connectivity
   - Check database logs

2. **High memory usage**:
   - Review application logs
   - Check for memory leaks
   - Adjust resource limits

3. **GitHub webhook failures**:
   - Verify webhook URL
   - Check webhook secret
   - Review GitHub App permissions

### Debugging Commands

```bash
# Check container logs
docker-compose logs -f backend

# Connect to database
docker-compose exec db psql -U aiuser -d aicodereview

# Check Redis
docker-compose exec redis redis-cli ping

# Container shell access
docker-compose exec backend bash
```

## Security Considerations

1. **Secrets Management**:
   - Use environment variables for secrets
   - Consider using secret management services
   - Rotate secrets regularly

2. **Network Security**:
   - Use private networks where possible
   - Implement proper firewall rules
   - Enable HTTPS everywhere

3. **Access Control**:
   - Follow principle of least privilege
   - Use strong authentication
   - Implement proper RBAC

## Maintenance

### Regular Tasks

1. **Weekly**:
   - Review application logs
   - Check system resources
   - Verify backups

2. **Monthly**:
   - Update dependencies
   - Review security logs
   - Performance analysis

3. **Quarterly**:
   - Security audit
   - Capacity planning
   - Disaster recovery testing
