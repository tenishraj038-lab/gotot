#!/bin/bash
set -e

BACKUP_DIR=${BACKUP_DIR:-/backups}
RETENTION_DAYS=${RETENTION_DAYS:-30}
DB_NAME=${POSTGRES_DB:-gotot}
DB_USER=${POSTGRES_USER:-gotot}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/gotot_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date +"%Y-%m-%d %H:%M:%S")] Starting database backup..."

pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date +"%Y-%m-%d %H:%M:%S")] Backup completed: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Verify backup integrity
gunzip -t "$BACKUP_FILE" 2>/dev/null && echo "Backup integrity verified" || echo "Backup integrity check FAILED"

# Cleanup old backups
find "$BACKUP_DIR" -name "gotot_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
echo "[$(date +"%Y-%m-%d %H:%M:%S")] Old backups cleaned (retention: ${RETENTION_DAYS} days)"

# Keep a latest symlink
ln -sf "$BACKUP_FILE" "${BACKUP_DIR}/gotot_latest.sql.gz"

echo "[$(date +"%Y-%m-%d %H:%M:%S")] Backup process completed"
