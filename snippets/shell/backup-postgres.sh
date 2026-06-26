---
id: "e1f2a3b4-c5d6-7890-efab-901234567890"
title: "PostgreSQL Backup to S3 with Rotation"
lang: shell
tags: [postgres, backup, s3, aws]
dependencies: [aws-cli, pg_dump]
author: peteedoo
created: 2024-05-12
updated: 2024-05-12
description: "Dump a PostgreSQL database, compress it, and upload to S3 with lifecycle-aware naming."
---

#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${DB_NAME:?}"
DB_HOST="${DB_HOST:-localhost}"
S3_BUCKET="${S3_BUCKET:?}"
DATE=$(date +%Y%m%d_%H%M%S)
FILE="${DB_NAME}_${DATE}.sql.gz"

pg_dump -h "$DB_HOST" -Fc "$DB_NAME" | gzip > "/tmp/$FILE"
aws s3 cp "/tmp/$FILE" "s3://${S3_BUCKET}/backups/${FILE}"
rm -f "/tmp/$FILE"

echo "Backup uploaded: $FILE"
