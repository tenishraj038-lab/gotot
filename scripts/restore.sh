#!/bin/bash
set -e

BACKUP_DIR=${BACKUP_DIR:-/backups}
DB_NAME=${POSTGRES_DB:-gotot}
DB_USER=${POSTGRES_USER:-gotot}

if [ -z "$1" ]; then
    LATEST="${BACKUP_DIR}/gotot_latest.sql.gz"
    if [ -f "$LATEST" ]; then
        BACKUP_FILE="$LATEST"
        echo "Using latest backup: ${BACKUP_FILE}"
    else
        echo "Usage: $0 [backup_file.sql.gz]"
        echo "Available backups:"
        ls -lh "${BACKUP_DIR}"/gotot_*.sql.gz 2>/dev/null || echo "No backups found"
        exit 1
    fi
else
    BACKUP_FILE="$1"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "[$(date +"%Y-%m-%d %H:%M:%S")] WARNING: This will overwrite the current database!"
echo "Backup file: ${BACKUP_FILE}"
echo "Database: ${DB_NAME}"
echo ""
read -p "Are you sure you want to proceed? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo "[$(date +"%Y-%m-%d %H:%M:%S")] Starting database restore..."

gunzip -c "$BACKUP_FILE" | psql -U "$DB_USER" -d "$DB_NAME"

echo "[$(date +"%Y-%m-%d %H:%M:%S")] Database restore completed successfully"
