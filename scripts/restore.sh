#!/bin/bash
# StreamlineVPN Restore Script

set -e

# Configuration
BACKUP_DIR="/backup/streamline"
S3_BUCKET="s3://streamline-backups"
RESTORE_DATE="$1"

if [ -z "$RESTORE_DATE" ]; then
  echo "Usage: $0 YYYYMMDD"
  exit 1
fi

echo "Restoring from backup date: $RESTORE_DATE"

# Download from S3
echo "Downloading backups from S3..."
aws s3 sync "$S3_BUCKET" "$BACKUP_DIR" --exclude "*" --include "*$RESTORE_DATE*"

# Stop services
echo "Stopping services..."
docker-compose down

# Restore database
echo "Restoring database..."
DB_BACKUP=$(ls -1 "$BACKUP_DIR"/db_"$RESTORE_DATE"*.sql.gz | head -1)
gunzip < "$DB_BACKUP" | psql postgresql://streamline@localhost/streamline

# Restore Redis
echo "Restoring Redis..."
REDIS_BACKUP=$(ls -1 "$BACKUP_DIR"/redis_"$RESTORE_DATE"*.rdb | head -1)
cp "$REDIS_BACKUP" /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/dump.rdb

# Restore configuration
echo "Restoring configuration..."
CONFIG_BACKUP=$(ls -1 "$BACKUP_DIR"/config_"$RESTORE_DATE"*.tar.gz | head -1)
tar -xzf "$CONFIG_BACKUP" -C /

# Restore data
echo "Restoring data..."
DATA_BACKUP=$(ls -1 "$BACKUP_DIR"/data_"$RESTORE_DATE"*.tar.gz | head -1)
tar -xzf "$DATA_BACKUP" -C /

# Start services
echo "Starting services..."
docker-compose up -d

echo "Restore completed successfully!"
