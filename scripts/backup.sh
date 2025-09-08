#!/bin/bash
# StreamlineVPN Backup Script

set -e

# Configuration
BACKUP_DIR="/backup/streamline"
S3_BUCKET="s3://streamline-backups"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
echo "Backing up database..."
if [ -n "$DATABASE_URL" ]; then
    pg_dump "$DATABASE_URL" | gzip > "$BACKUP_DIR/db_$(date +%Y%m%d_%H%M%S).sql.gz"
else
    pg_dump postgresql://streamline@localhost/streamline | gzip > "$BACKUP_DIR/db_$(date +%Y%m%d_%H%M%S).sql.gz"
fi

# Backup Redis
echo "Backing up Redis..."
if [ -n "$REDIS_URL" ]; then
    redis-cli -u "$REDIS_URL" --rdb "$BACKUP_DIR/redis_$(date +%Y%m%d_%H%M%S).rdb"
else
    redis-cli --rdb "$BACKUP_DIR/redis_$(date +%Y%m%d_%H%M%S).rdb"
fi

# Backup configuration
echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/config_$(date +%Y%m%d_%H%M%S).tar.gz" /opt/streamline/config

# Backup data
echo "Backing up data..."
tar -czf "$BACKUP_DIR/data_$(date +%Y%m%d_%H%M%S).tar.gz" /opt/streamline/data

# Upload to S3
echo "Uploading to S3..."
aws s3 sync "$BACKUP_DIR" "$S3_BUCKET" --storage-class STANDARD_IA

# Clean old backups
echo "Cleaning old backups..."
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
aws s3 ls "$S3_BUCKET" | while read -r line; do
  createDate=$(echo $line | awk {'print $1" "$2'})
  createDate=$(date -d "$createDate" +%s)
  olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
  if [[ $createDate -lt $olderThan ]]; then
    fileName=$(echo $line | awk {'print $4'})
    aws s3 rm "$S3_BUCKET/$fileName"
  fi
done

echo "Backup completed successfully!"
