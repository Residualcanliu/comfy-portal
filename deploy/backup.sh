#!/usr/bin/env bash
# Postgres 备份（规格书 §11 W3：pg_dump 备份）
# 用法：在 VPS 的 /srv/comfy-portal 下执行 ./deploy/backup.sh
set -euo pipefail

BACKUP_DIR=/srv/comfy-portal/backups
mkdir -p "$BACKUP_DIR"

STAMP=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-comfy}" "${POSTGRES_DB:-comfyportal}" \
  > "$BACKUP_DIR/backup_${STAMP}.sql"

# 保留最近 7 份，多余的删除
ls -t "$BACKUP_DIR"/backup_*.sql 2>/dev/null | tail -n +8 | xargs -r rm -f

echo "备份完成: $BACKUP_DIR/backup_${STAMP}.sql"
