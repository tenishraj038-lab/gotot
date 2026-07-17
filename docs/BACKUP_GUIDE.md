# GoTot Backup Guide

Procedures for backing up and restoring GoTot data.

---

## Table of Contents

- [Backup Components](#backup-components)
- [Automated Backups](#automated-backups)
- [Manual Backup](#manual-backup)
- [Backup Contents](#backup-contents)
- [Retention Policy](#retention-policy)
- [Integrity Verification](#integrity-verification)
- [Restore Procedure](#restore-procedure)
- [Testing Backups](#testing-backups)

---

## Backup Components

The backup strategy covers two critical data stores:

| Component | Method | Frequency |
|-----------|--------|-----------|
| **PostgreSQL database** | `pg_dump` via `backup.sh` | Every 6 hours (automated) |
| **Uploaded files** | Not backed up (temp) | N/A |

**Note:** Download files are stored in `/tmp/downloads` and are automatically cleaned after 1 hour by the Celery beat task. These are **not** backed up — they are temporary artifacts.

---

## Automated Backups

The automated backup system runs as a Docker Compose service using the `backup` profile.

### How It Works

1. The `backup` service uses the `postgres:16-alpine` image (contains `pg_dump` and `psql`).
2. It runs a cron job defined in `docker-compose.yml`:

```yaml
command:
  - |
    echo "0 */6 * * * /backup.sh >> /var/log/backup.log 2>&1" | crontab -
    crond -f
```

3. Every 6 hours, `/backup.sh` is executed.
4. Backups are written to the `/backups` volume (mounted from `./backups` on the host).

### Starting the Backup Service

```bash
# Start with the backup profile
docker compose --profile backup up -d backup

# Check logs
docker compose logs backup
```

### Configuration

The backup service inherits database credentials from the Compose environment:

```yaml
environment:
  POSTGRES_USER: ${POSTGRES_USER:-gotot}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-gotot_pass}
  POSTGRES_DB: ${POSTGRES_DB:-gotot}
  PGHOST: postgres
```

---

## Manual Backup

### Using backup.sh

```bash
# Run inside the backup container
docker compose exec backup /backup.sh

# Or run as a one-off
docker compose run --rm backup /backup.sh
```

### Using pg_dump directly

```bash
# Dump via exec on the postgres container
docker compose exec postgres pg_dump -U gotot gotot | gzip > ./backups/manual_$(date +%Y%m%d_%H%M%S).sql.gz

# Or from the host with psql client
pg_dump -h localhost -p 5432 -U gotot gotot | gzip > ./backups/host_$(date +%Y%m%d_%H%M%S).sql.gz
```

### The backup.sh Script

```bash
#!/bin/bash
set -e

BACKUP_DIR=${BACKUP_DIR:-/backups}
RETENTION_DAYS=${RETENTION_DAYS:-30}
DB_NAME=${POSTGRES_DB:-gotot}
DB_USER=${POSTGRES_USER:-gotot}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/gotot_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"
pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

# Verify integrity
gunzip -t "$BACKUP_FILE"

# Cleanup old backups
find "$BACKUP_DIR" -name "gotot_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete

# Update latest symlink
ln -sf "$BACKUP_FILE" "${BACKUP_DIR}/gotot_latest.sql.gz"
```

---

## Backup Contents

Each backup is a gzip-compressed SQL dump file named `gotot_YYYYMMDD_HHMMSS.sql.gz`.

The dump contains:

- **Full database schema**: All tables, indexes, sequences, enums
- **All data rows**: Users, subscriptions, payments, download history, API keys, referrals, notifications, audit logs, feature flags, affiliate links, ad impressions
- **Extensions**: `uuid-ossp`, `pgcrypto`

**Not included:**
- Download files in `/tmp/downloads` (temporary, cleaned hourly)
- Docker volumes for Redis and Prometheus (cache/metrics — rebuilt automatically)

### Backup File Size Estimation

| Data Volume | Approx Size |
|-------------|-------------|
| 1,000 users, 50K downloads | ~10 MB |
| 10K users, 500K downloads | ~100 MB |
| 100K users, 5M downloads | ~1 GB |

---

## Retention Policy

| Setting | Default | Description |
|---------|---------|-------------|
| `RETENTION_DAYS` | 30 | Backup files older than 30 days are deleted |
| `BACKUP_DIR` | `/backups` | Where backup files are stored |

### Manual Cleanup

```bash
# Remove backups older than 30 days
docker compose exec backup find /backups -name "gotot_*.sql.gz" -mtime +30 -delete

# List current backups with sizes
docker compose exec backup ls -lh /backups/
```

### Storage Requirements

15 days of backups at:
- 10 MB each × 4 backups/day = 40 MB/day → **600 MB for 15 days**
- 100 MB each × 4 backups/day = 400 MB/day → **6 GB for 15 days**

Ensure the host volume has sufficient space. Monitor with:

```bash
du -sh /opt/gotot/backups/
```

---

## Integrity Verification

### Automatic Verification

The `backup.sh` script automatically verifies each backup:

```bash
gunzip -t "$BACKUP_FILE" && echo "Backup integrity verified" || echo "Backup integrity check FAILED"
```

The `gunzip -t` command tests the integrity of the gzip archive without decompressing. A FAILED check triggers a message in the log but does not delete the file (allows manual inspection).

### Manual Verification

```bash
# Test gzip integrity
docker compose exec backup gunzip -t /backups/gotot_20260315_120000.sql.gz

# Test restore by examining the SQL (without importing)
docker compose exec backup zcat /backups/gotot_20260315_120000.sql.gz | head -100

# Full restore test (see Testing Backups)
```

### Scheduled Verification

Add a weekly verification script:

```bash
docker compose exec backup /bin/sh -c "
  for f in /backups/gotot_*.sql.gz; do
    gunzip -t \"\$f\" || echo \"CORRUPT: \$f\"
  done
"
```

---

## Restore Procedure

See the dedicated [RECOVERY_GUIDE.md](RECOVERY_GUIDE.md) for disaster recovery.

### Quick Restore

```bash
# 1. Stop services (database clients)
docker compose stop backend celery_worker celery_beat

# 2. Restore from latest backup
docker compose run --rm backup /restore.sh

# 3. Restart services
docker compose start backend celery_worker celery_beat
```

### Restoring a Specific Backup

```bash
# List backups
docker compose exec backup ls -lh /backups/

# Restore a specific file
docker compose run --rm backup /restore.sh /backups/gotot_20260314_060000.sql.gz
```

### The restore.sh Script

```bash
#!/bin/bash
set -e

BACKUP_DIR=${BACKUP_DIR:-/backups}
DB_NAME=${POSTGRES_DB:-gotot}
DB_USER=${POSTGRES_USER:-gotot}

if [ -z "$1" ]; then
    LATEST="${BACKUP_DIR}/gotot_latest.sql.gz"
    BACKUP_FILE="$LATEST"
else
    BACKUP_FILE="$1"
fi

# Confirmation prompt
echo "WARNING: This will overwrite the current database!"
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

gunzip -c "$BACKUP_FILE" | psql -U "$DB_USER" -d "$DB_NAME"
echo "Database restore completed successfully"
```

---

## Testing Backups

Regular backup testing is essential for disaster recovery readiness.

### Weekly Test Procedure

1. **Verify backup exists**:
```bash
docker compose exec backup ls -lh /backups/gotot_latest.sql.gz
```

2. **Test gzip integrity**:
```bash
docker compose exec backup gunzip -t /backups/gotot_latest.sql.gz
```

3. **Restore to a test database**:
```bash
# Create a test database
docker compose exec postgres createdb -U gotot gotot_test

# Restore into test database
gunzip -c /backups/gotot_latest.sql.gz | \
  docker compose exec -T postgres psql -U gotot -d gotot_test

# Verify data
docker compose exec postgres psql -U gotot -d gotot_test -c "SELECT count(*) FROM users;"

# Drop test database
docker compose exec postgres dropdb -U gotot gotot_test
```

4. **Check backup size trend**:
```bash
docker compose exec backup du -sh /backups/
```

### Automated Test Script

Add this as a monthly cron job:

```bash
#!/bin/bash
# /opt/gotot/scripts/test-backup.sh

BACKUP_FILE="/backups/gotot_latest.sql.gz"

if [ ! -f "$BACKUP_FILE" ]; then
  echo "FAIL: No backup found"
  exit 1
fi

gunzip -t "$BACKUP_FILE" || { echo "FAIL: Backup corrupted"; exit 1; }

echo "PASS: Backup integrity check"
```

### What to Check After Restore

| Check | Command |
|-------|---------|
| User count matches | `SELECT count(*) FROM users;` |
| Active subscriptions | `SELECT count(*) FROM subscriptions WHERE status = 'active';` |
| Recent downloads exist | `SELECT count(*) FROM download_history WHERE created_at > now() - interval '7 days';` |
| Feature flags intact | `SELECT key, enabled FROM feature_flags;` |
| API keys present | `SELECT count(*) FROM api_keys WHERE is_active = true;` |
