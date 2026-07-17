# GoTot Deployment Guide

Guide for deploying GoTot to production using Docker Compose.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [SSL Certificate Setup](#ssl-certificate-setup)
- [Docker Compose Services](#docker-compose-services)
- [Production .env Configuration](#production-env-configuration)
- [Database Migrations](#database-migrations)
- [Health Checks](#health-checks)
- [Monitoring](#monitoring)
- [Backup Strategy](#backup-strategy)
- [CI/CD Pipeline](#cicd-pipeline)
- [Scaling Considerations](#scaling-considerations)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Minimum Server Requirements
- **CPU**: 2 cores (4+ recommended for production)
- **RAM**: 4 GB (8 GB recommended)
- **Storage**: 50 GB SSD (scale based on download volume)
- **OS**: Ubuntu 22.04+ or Debian 12+
- **Docker**: 24.0+
- **Docker Compose**: 2.20+

### Required Software
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Verify
docker --version
docker compose version
```

### Network Requirements
| Port | Service | Purpose |
|------|---------|---------|
| 80 | Nginx | HTTP (redirects to HTTPS) |
| 443 | Nginx | HTTPS traffic |
| 9090 | Prometheus | Metrics (internal only) |

---

## Environment Configuration

### Directory Structure
```
/opt/gotot/
├── docker-compose.yml
├── backend/
│   └── .env              # Backend environment
├── nginx/
│   └── nginx.conf        # Nginx configuration
├── scripts/
│   ├── backup.sh         # Database backup script
│   ├── restore.sh        # Database restore script
│   └── generate-ssl.sh   # SSL certificate generation
├── backups/              # Database backups (mounted volume)
├── prometheus.yml        # Prometheus configuration
└── .env                  # Docker Compose environment variables
```

### Clone & Setup

```bash
git clone https://github.com/your-org/gotot.git /opt/gotot
cd /opt/gotot

# Copy environment files
cp backend/.env.example backend/.env
cp .env.example .env  # Docker Compose variables

# Create backup directory
mkdir -p backups
```

---

## SSL Certificate Setup

### Option 1: Self-Signed (Development)

```bash
# Run the SSL generation script inside the nginx container
docker compose run --rm nginx /bin/sh -c "
  mkdir -p /etc/nginx/ssl && \
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem \
    -subj '/C=US/ST=State/L=City/O=GoTot/CN=gotot.app'
"
```

Or use the provided script:
```bash
# This script is designed to run inside the container
# Mount SSL volume before running
docker compose run --rm -v nginx_ssl:/etc/nginx/ssl nginx /scripts/generate-ssl.sh
```

### Option 2: Let's Encrypt (Production)

Replace the SSL section in `docker-compose.yml` with certbot:

```yaml
certbot:
  image: certbot/certbot
  volumes:
    - nginx_ssl:/etc/letsencrypt
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
  entrypoint: /bin/sh
  command: -c "certbot certonly --webroot -w /var/www/html -d gotot.app -d www.gotot.app --non-interactive --agree-tos --email admin@gotot.app"

nginx:
  volumes:
    - nginx_ssl:/etc/letsencrypt
```

Update `nginx.conf` to point to Let's Encrypt certificates:
```nginx
ssl_certificate     /etc/letsencrypt/live/gotot.app/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/gotot.app/privkey.pem;
```

### Auto-Renewal (Let's Encrypt)

Add a cron job:
```bash
0 3 * * * docker compose -f /opt/gotot/docker-compose.yml run --rm certbot renew && docker compose -f /opt/gotot/docker-compose.yml exec nginx nginx -s reload
```

---

## Docker Compose Services

### Services Overview

| Service | Image | Purpose |
|---------|-------|---------|
| `nginx` | nginx:alpine | Reverse proxy, SSL termination, static files |
| `frontend` | gotot-frontend:latest | Next.js SSR application |
| `backend` | gotot-backend:latest | FastAPI application server |
| `celery_worker` | gotot-backend:latest | Async download processing |
| `celery_beat` | gotot-backend:latest | Scheduled tasks (cleanup) |
| `postgres` | postgres:16-alpine | Primary database |
| `redis` | redis:7-alpine | Cache, Celery broker, pub/sub |
| `prometheus` | prom/prometheus | Metrics collection |
| `backup` | postgres:16-alpine | Automated DB backups (profile: backup) |

### Startup Order

1. `postgres` + `redis` (parallel) — health checks required
2. `backend` — depends on postgres + redis healthy
3. `frontend` — depends on backend
4. `nginx` — depends on frontend + backend
5. `celery_worker` + `celery_beat` — depend on backend + redis

### Logging

All services use JSON-file logging with:
```yaml
x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Production .env Configuration

### Docker Compose Variables (`.env`)

```bash
# PostgreSQL
POSTGRES_USER=gotot
POSTGRES_PASSWORD=<generate-a-strong-password>
POSTGRES_DB=gotot

# Redis
REDIS_REQUIREPASS=<generate-a-strong-password>

# Backend
UVICORN_WORKERS=4
CELERY_CONCURRENCY=4
```

### Backend Variables (`backend/.env`)

```bash
# Security
SECRET_KEY=<generate-with: openssl rand -hex 64>

# Database
DATABASE_URL=postgresql+asyncpg://gotot:<password>@postgres:5432/gotot

# Redis
REDIS_URL=redis://:<password>@redis:6379/0
CELERY_BROKER_URL=redis://:<password>@redis:6379/1

# Environment
ENVIRONMENT=production
LOG_LEVEL=info
ALLOWED_ORIGINS=https://gotot.app,https://www.gotot.app

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Tokens
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Frontend URL (for redirects)
FRONTEND_URL=https://gotot.app

# Downloads
DOWNLOAD_DIR=/tmp/downloads
MAX_FILE_SIZE_MB=500
FILE_RETENTION_HOURS=1

# Razorpay
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
RAZORPAY_PRO_PLAN_ID=plan_...
RAZORPAY_UNLIMITED_PLAN_ID=plan_...
CURRENCY=USD

# SMTP (Email)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=...
SMTP_FROM_EMAIL=noreply@gotot.app
ADMIN_EMAIL=admin@gotot.app

# Google OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://gotot.app/auth/google/callback

# Sentry (optional)
SENTRY_DSN=https://...
```

---

## Database Migrations

### Initial Migration

```bash
# Run migrations inside the backend container
docker compose exec backend alembic upgrade head

# Or run via a one-off container
docker compose run --rm backend alembic upgrade head
```

### Subsequent Migrations

```bash
# Auto-generate migration after model changes
docker compose run --rm backend alembic revision --autogenerate -m "description"

# Apply
docker compose run --rm backend alembic upgrade head

# Rollback
docker compose run --rm backend alembic downgrade -1
```

### Migration in CI/CD

The CI pipeline runs `alembic upgrade head` automatically before tests.

---

## Health Checks

### Docker Health Checks

Each service has a health check defined in `docker-compose.yml`:

| Service | Command | Interval |
|---------|---------|----------|
| `postgres` | `pg_isready -U gotot` | 10s |
| `redis` | `redis-cli ping` | 10s |
| `backend` | `curl -f http://localhost:8000/health` | 30s |
| `frontend` | `wget --spider http://localhost:3000` | 30s |
| `nginx` | `nginx -t` | 30s |

### Application Health Endpoint

```
GET /health
```

```json
{
  "status": "ok",
  "version": "3.0.0",
  "environment": "production",
  "database": "connected"
}
```

The `/health` endpoint checks:
- Database connectivity (executes `SELECT 1`)
- Returns `"degraded"` status if DB is down (app still serves cached data)

### Prometheus Metrics

```
GET /metrics
```

Exposes Prometheus metrics at `/metrics` for scraping.

---

## Monitoring

### Prometheus

Prometheus is configured to scrape:

| Target | URL | Interval |
|--------|-----|----------|
| Backend | `backend:8000` | 15s |
| Nginx | `nginx:80` | 15s |

Configuration (`prometheus.yml`):
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "backend"
    static_configs:
      - targets: ["backend:8000"]
  - job_name: "nginx"
    static_configs:
      - targets: ["nginx:80"]
```

### Grafana (Optional)

Add Grafana for visualization:

```yaml
grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  volumes:
    - grafana_data:/var/lib/grafana
    - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=<password>
```

### Key Metrics to Monitor

- **PostgreSQL**: Connection pool usage, query performance
- **Redis**: Memory usage, hit rate, connected clients
- **Backend**: Request latency, error rate, active connections
- **Celery**: Queue depth, task completion rate, failure rate
- **Nginx**: 5xx rate, request throughput, bandwidth

---

## Backup Strategy

See the dedicated [BACKUP_GUIDE.md](BACKUP_GUIDE.md) for full details.

### Automated Backups

The backup service runs via Docker Compose and:
- Dumps the database every 6 hours via cron
- Compresses with gzip
- Retains backups for 30 days
- Verifies integrity
- Maintains a `gotot_latest.sql.gz` symlink

### Manual Backup

```bash
# Run backup manually
docker compose run --rm backup /backup.sh

# Or execute inside container
docker compose exec backup /backup.sh
```

---

## CI/CD Pipeline

### GitHub Actions (`.github/workflows/ci.yml`)

The CI pipeline runs on push to `main`/`develop` and PRs to `main`:

**Backend jobs:**
1. Setup Python 3.12 with pip cache
2. Install dependencies
3. Run database migrations
4. Run pytest with coverage

**Frontend jobs:**
1. Setup Node.js 20 with npm cache
2. Install dependencies
3. TypeScript type check
4. ESLint
5. Jest tests
6. Next.js build

**Docker build (main only):**
1. Build backend Docker image
2. Build frontend Docker image
3. Uses GitHub Actions cache for layers

### Deployment Flow

```
PR merged to main
  → CI runs all checks
  → Docker images built
  → (Optional) Push to container registry
  → SSH to production
  → docker compose pull
  → docker compose up -d
  → alembic upgrade head
  → Health check verification
```

---

## Scaling Considerations

### Vertical Scaling

Increase resources in `docker-compose.yml`:

```yaml
backend:
  environment:
    - UVICORN_WORKERS=8  # Increase from 4

celery_worker:
  command: celery -A celery worker --concurrency=8  # Increase from 4
```

### Horizontal Scaling

For multiple backend instances:

```yaml
docker-compose.yml
backend:
  deploy:
    replicas: 3
```

Nginx upstream already uses `least_conn` load balancing:
```nginx
upstream backend {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=10s;
    keepalive 32;
}
```

### Database Scaling

- **Connection pool**: Current config: `pool_size=20`, `max_overflow=10`
- **Read replicas**: Add read-only replicas for analytics queries
- **Connection pooling**: Consider PgBouncer for high connection counts

### Redis Scaling

- **Max memory**: 512 MB (configurable via `REDIS_REQUIREPASS` and `--maxmemory`)
- **Eviction policy**: `allkeys-lru`
- **Persistence**: Append-only file enabled

### Storage Scaling

- **Downloads volume**: Downloads are stored in `/tmp/downloads` and cleaned after 1 hour
- **Static files**: Served via Nginx with 30-day cache headers
- **Database**: Regular `VACUUM` and index maintenance

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker compose logs <service>

# Check health
docker compose ps

# Force rebuild
docker compose build --no-cache <service>
```

### Database connection refused

```bash
# Verify PostgreSQL is healthy
docker compose exec postgres pg_isready -U gotot

# Check connection string in backend/.env
# Verify hostname matches docker compose service name (postgres, not localhost)
```

### Redis connection issues

```bash
# Test Redis connectivity
docker compose exec redis redis-cli ping

# With password
docker compose exec redis redis-cli -a <password> ping
```

### Celery tasks not processing

```bash
# Check worker logs
docker compose logs celery_worker

# Verify Redis broker
docker compose exec redis redis-cli LLEN celery

# Restart workers
docker compose restart celery_worker celery_beat
```

### Nginx 502 Bad Gateway

```bash
# Check if backend is running
docker compose ps backend

# Check backend logs for errors
docker compose logs backend

# Verify nginx config
docker compose exec nginx nginx -t
```

### Rate limiting issues

```bash
# Check current rate limit configuration
docker compose exec backend python -c "
from app.config import get_settings
s = get_settings()
print(f'Rate limit: {s.rate_limit_per_minute}/minute')
"
```

### Prometheus not collecting metrics

```bash
# Verify metrics endpoint
curl http://localhost:8000/metrics

# Check Prometheus target status
# View at http://localhost:9090/targets

# Reload Prometheus config
docker compose exec prometheus kill -HUP 1
```

### Common Errors

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| `Authorization: Bearer` missing | Token not provided | Check client sends token |
| `CSRF token missing` | Missing CSRF cookie | Check cookie settings, add `X-CSRF-Token` header |
| `relation "users" does not exist` | Migrations not run | Run `alembic upgrade head` |
| `could not translate host name "postgres"` | Wrong Docker network | Ensure `postgres` is the compose service name |
| `rate limit exceeded` | Too many requests | Wait or upgrade tier |
| `File not found or expired` | Retention period passed | File cleaned after 1 hour; re-download |
| `Worker lost connection` | Redis unavailable | Check `docker compose logs redis` |
