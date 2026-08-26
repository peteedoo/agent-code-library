#!/usr/bin/env bash
# Ensure ACL_KV namespace exists and write wrangler.deploy.json with real IDs.
set -euo pipefail
cd "$(dirname "$0")/.."

NAME="${ACL_KV_NAME:-acl-stats}"

if [ -z "${LIST_JSON:-}" ]; then
  LIST_JSON="$(npx wrangler kv namespace list --format=json 2>/dev/null || echo '[]')"
fi
export LIST_JSON NAME

ID="$(python3 - <<'PY'
import json, os
raw = os.environ.get("LIST_JSON", "[]")
try:
    data = json.loads(raw)
except Exception:
    data = []
name = os.environ["NAME"]
for ns in data if isinstance(data, list) else []:
    if ns.get("title") == name or ns.get("name") == name:
        print(ns.get("id") or "")
        break
PY
)"

if [ -z "${ID}" ]; then
  echo "Creating KV namespace: $NAME"
  OUT="$(npx wrangler kv namespace create "$NAME" 2>&1)" || true
  echo "$OUT"
  ID="$(printf '%s\n' "$OUT" | python3 -c "
import sys, re
t = sys.stdin.read()
m = re.search(r'([a-f0-9]{32})', t, re.I)
print(m.group(1) if m else '')
")"
fi

if [ -z "${ID}" ]; then
  echo "ERROR: could not resolve KV namespace id for $NAME" >&2
  exit 1
fi

echo "Using KV id=$ID"
python3 - "$ID" <<'PY'
import json, sys
from pathlib import Path
kid = sys.argv[1]
cfg = {
  "name": "acl-api",
  "main": "src/index.js",
  "compatibility_date": "2026-08-01",
  "workers_dev": True,
  "vars": {
    "CATALOG_URL": "https://raw.githubusercontent.com/peteedoo/agent-code-library/main/www/catalog.json",
    "PUBLIC_URL": "https://aicode.iamfaulty.com",
    "REPO": "peteedoo/agent-code-library",
  },
  "kv_namespaces": [
    {"binding": "ACL_KV", "id": kid, "preview_id": kid}
  ],
  "observability": {"enabled": True},
}
Path("wrangler.deploy.json").write_text(json.dumps(cfg, indent=2) + "\n")
print("wrote wrangler.deploy.json")
PY

echo "$ID" > .kv_id
