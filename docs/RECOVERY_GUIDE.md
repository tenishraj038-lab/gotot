# GoTot Disaster Recovery Guide

Procedures for recovering from data loss, corruption, or infrastructure failure.

---

## Table of Contents

- [Restoring from Backup](#restoring-from-backup)
- [Rebuilding Docker Services](#rebuilding-docker-services)
- [Re-running Database Migrations](#re-running-database-migrations)
- [Verifying Data Integrity](#verifying-data-integrity)
- [Handling Corrupted Data](#handling-corrupted-data)
- [Emergency Procedures](#emergency-procedures)
- [Contact Information](#contact-information)

---

## Restoring from Backup

### Prerequisites

- A valid backup file at `/opt/gotot/backups/gotot_latest.sql.gz` (or specified path)
- Docker Compose services running (at least `postgres`)

### Step-by-Step Restore

```bash
# 1. Navigate to the project directory
cd /opt/gotot

# 2. Stop services that use the database
docker compose stop backend celery_worker celery_beat

# 3. Restore the database
#    This drops all tables and recreates them from the backup
docker compose run --rm backup /restore.sh

#    If restoring a specific backup file:
#    docker compose run --rm backup /restore.sh /backups/gotot_20260314_060000.sql.gz

# 4. Start services
docker compose start backend celery_worker celery_beat

# 5. Verify the application
curl http://localhost:8000/health
```

### Restoring from the Latest Backup Automatically

```bash
docker compose run --rm backup /bin/sh -c "
  LATEST=\$(ls -t /backups/gotot_*.sql.gz 2>/dev/null | head -1)
  if [ -z \"\$LATEST\" ]; then
    echo 'No backups found'
    exit 1
  fi
  gunzip -c \"\$LATEST\" | psql -U \$POSTGRES_USER -d \$POSTGRES_DB
  echo 'Restored from: \$LATEST'
"
```

### Restoring to a Specific Point in Time

If you have multiple backups and need to restore to a specific time:

```bash
# List available backups sorted by date
ls -lh /opt/gotot/backups/gotot_*.sql.gz

# Restore the one closest to your target time
docker compose run --rm backup /restore.sh /backups/gotot_20260315_120000.sql.gz
```

---

## Rebuilding Docker Services

### Full Rebuild

Use this when containers are corrupted, configuration has changed, or after a code update.

```bash
# 1. Stop all services
cd /opt/gotot
docker compose down

# 2. Rebuild images from source
docker compose build --no-cache

# 3. Start services
docker compose up -d

# 4. Check all services are healthy
docker compose ps
```

### Rebuilding a Single Service

```bash
# Rebuild and restart just the backend
docker compose build --no-cache backend
docker compose up -d backend

# Rebuild and restart frontend
docker compose build --no-cache frontend
docker compose up -d frontend
```

### Recreating Volumes

**Warning:** This destroys all data. Only do this if you have a backup.

```bash
# Stop and remove everything
docker compose down -v

# Recreate volumes and start fresh
docker compose up -d

# Restore from backup (see above)
```

---

## Re-running Database Migrations

After restoring from a backup, migrations are already applied (the backup includes the schema). However, if you need to migrate a restored database to a newer schema version:

```bash
# Check current migration version
docker compose exec backend alembic current

# Apply any pending migrations
docker compose exec backend alembic upgrade head

# If you need to go back
docker compose exec backend alembic downgrade -1
```

### Migration History

```bash
# View all migrations
docker compose exec backend alembic history

# View specific revision details
docker compose exec backend alembic show <revision_id>
```

### Handling Migration Conflicts

If a migration fails after restore:

```bash
# Check the error
docker compose logs backend

# Common fix: stamp the current revision manually
docker compose exec backend alembic stamp head

# Then retry
docker compose exec backend alembic upgrade head
```

---

## Verifying Data Integrity

### After Restore

Run these checks to confirm the restore was successful:

```bash
# 1. Check database connectivity
curl http://localhost:8000/health

# 2. Check critical tables
docker compose exec postgres psql -U gotot -d gotot -c "
  SELECT 'users' as table_name, count(*) as count FROM users
  UNION ALL
  SELECT 'download_history', count(*) FROM download_history
  UNION ALL
  SELECT 'subscriptions', count(*) FROM subscriptions
  UNION ALL
  SELECT 'payments', count(*) FROM payments
  UNION ALL
  SELECT 'api_keys', count(*) FROM api_keys
  UNION ALL
  SELECT 'referrals', count(*) FROM referrals
  ORDER BY table_name;
"

# 3. Check admin user exists
docker compose exec postgres psql -U gotot -d gotot -c "
  SELECT email, username, is_admin FROM users WHERE is_admin = true;
"

# 4. Check feature flags
docker compose exec postgres psql -U gotot -d gotot -c "
  SELECT key, enabled FROM feature_flags;
"
```

### Schema Verification

Confirm the schema matches expectations:

```bash
docker compose exec postgres psql -U gotot -d gotot -c "
  SELECT table_name FROM information_schema.tables
  WHERE table_schema = 'public'
  ORDER BY table_name;
"
```

Expected tables:
- `ad_impressions`
- `affiliate_links`
- `api_keys`
- `audit_logs`
- `download_history`
- `download_tasks`
- `feature_flags`
- `notifications`
- `payments`
- `referrals`
- `subscriptions`
- `users`
- `alembic_version`

### Application-Level Verification

```bash
# 1. API health check
curl http://localhost:8000/health

# 2. Test user registration
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@verify.com", "username": "verify", "password": "TestPass1"}'

# 3. Clean up test user
docker compose exec postgres psql -U gotot -d gotot -c "
  DELETE FROM users WHERE email = 'test@verify.com';
"
```

---

## Handling Corrupted Data

### Identifying Corruption

Signs of data corruption:
- `Health` endpoint returns `"database": "disconnected"`
- PostgreSQL error logs showing `"could not read block"` or `"invalid page"`
- Queries return incorrect results or fail with `"relation not found"`
- Application throws 500 errors on basic operations

### Recovery Options

#### 1. Restore from Backup (Recommended)

```bash
# Stop services, restore, verify
docker compose stop backend celery_worker celery_beat
docker compose run --rm backup /restore.sh /backups/gotot_latest.sql.gz
docker compose start backend celery_worker celery_beat
```

#### 2. PostgreSQL Repair (Last Resort)

```bash
# Attempt repair
docker compose exec postgres psql -U gotot -d gotot -c "VACUUM FULL;"
docker compose exec postgres psql -U gotot -d gotot -c "REINDEX DATABASE gotot;"

# If specific table is corrupted
docker compose exec postgres psql -U gotot -d gotot -c "VACUUM FULL VERBOSE users;"
docker compose exec postgres psql -U gotot -d gotot -c "REINDEX TABLE users;"
```

#### 3. Dump Known-Good Tables

If only some tables are corrupted:

```bash
# Dump all tables except the corrupted one
docker compose exec postgres pg_dump -U gotot gotot -T corrupted_table > partial_dump.sql

# Drop and recreate the corrupted table manually
docker compose exec postgres psql -U gotot -d gotot -c "DROP TABLE IF EXISTS corrupted_table CASCADE;"

# (Run migration to recreate the table)
docker compose exec backend alembic upgrade head

# Import data if you have a separate backup of this table
```

---

## Emergency Procedures

### Scenario 1: Complete Server Failure

If the server is unrecoverable:

1. **Provision a new server** with Docker and Docker Compose.
2. **Clone the repository** to `/opt/gotot`.
3. **Copy the backup files** from your off-server backup location (S3, rsync, etc.) to `./backups/`.
4. **Start infrastructure** (PostgreSQL + Redis only):
   ```bash
   docker compose up -d postgres redis
   ```
5. **Restore the database** from your latest backup.
6. **Run migrations** (if the backup schema is older than current code):
   ```bash
   docker compose run --rm backend alembic upgrade head
   ```
7. **Start all services**:
   ```bash
   docker compose up -d
   ```
8. **Verify**:
   - Health endpoint responds
   - Admin user can log in
   - Key metrics match expected values

### Scenario 2: Database Container Failure

```bash
# If postgres container won't start
docker compose logs postgres

# Remove the corrupted data volume
docker compose down
docker volume rm gotot_postgres_data

# Start fresh postgres
docker compose up -d postgres

# Restore from backup
docker compose run --rm backup /restore.sh
```

### Scenario 3: Redis Data Loss

Redis is a cache and message broker — data loss is non-critical:

```bash
# Restart Redis with empty data
docker compose restart redis

# Redis will rebuild cache and queue as services use it
```

### Scenario 4: Application Bug Causes Data Loss

1. **Stop the application** immediately:
   ```bash
   docker compose stop backend celery_worker
   ```
2. **Restore from the most recent backup** before the bug was introduced.
3. **Apply the fix** (deploy patched code).
4. **Restart services**:
   ```bash
   docker compose up -d
   ```

### Scenario 5: SSL Certificate Expired

```bash
# For Let's Encrypt
docker compose run --rm certbot renew
docker compose exec nginx nginx -s reload

# For self-signed (temporary)
docker compose exec nginx /bin/sh -c "
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem \
    -subj '/C=US/ST=State/L=City/O=GoTot/CN=gotot.app'
"
docker compose exec nginx nginx -s reload
```

---

## Contact Information

### Internal Contacts

| Role | Contact |
|------|---------|
| DevOps / Infrastructure | devops@gotot.app |
| Database Administrator | dba@gotot.app |
| Security Team | security@gotot.app |
| Development Team | dev@gotot.app |

### External Services

| Service | Support Contact | Account Info |
|---------|----------------|--------------|
| **Razorpay** | support@razorpay.com | Dashboard: https://dashboard.razorpay.com |
| **Sentry** | support@sentry.io | DSN in `backend/.env` |
| **SendGrid** (SMTP) | support@sendgrid.com | API key in `backend/.env` |
| **Docker Hub** | support@docker.com | Image registry |
| **Cloud Provider** | Provider support | Server console access |

### Emergency Response Times

| Severity | Description | Response Time | Resolution Target |
|----------|-------------|---------------|-------------------|
| **P0** | Complete outage / data loss | 15 min | 2 hours |
| **P1** | Major feature unavailable | 1 hour | 4 hours |
| **P2** | Minor feature impaired | 4 hours | 24 hours |
| **P3** | Cosmetic / non-urgent | 24 hours | 1 week |

### Incident Report Template

After recovery, document the incident:

```
Date: YYYY-MM-DD
Duration: HH:MM to HH:MM UTC
Severity: P0/P1/P2/P3
Root Cause: [Brief description]
Impact: [What was affected]
Resolution: [Steps taken]
Prevention: [How to prevent recurrence]
Action Items:
- [ ] Item 1
- [ ] Item 2
```
