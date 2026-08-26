#!/bin/sh
# Container entrypoint: ensure sqlite index exists, then serve the API.
set -e
cd /app

if [ ! -f .acl/index/snippets.db ] || [ "${ACL_REBUILD_ON_START:-1}" = "1" ]; then
  echo "[acl] building search index + catalog..."
  python3 scripts/indexer.py
  python3 scripts/build_tarball.py || true
fi

PORT="${PORT:-8000}"
exec python3 -m uvicorn webhook.main:app --host 0.0.0.0 --port "$PORT"
