# Deploy ACL API (fix the 502)

`aicode.iamfaulty.com` is on Cloudflare, but the old origin is dead (HTTP 502).
This repo now has two deployable origins:

| Option | Path | Best when |
|--------|------|-----------|
| **A. Cloudflare Worker (recommended)** | `edge/` | Domain already on Cloudflare |
| **B. Container (Railway / Fly / Docker)** | root `Dockerfile` | You want the full FastAPI + sqlite stack |

## A. Cloudflare Worker (recommended)

### 1. Secrets (GitHub repo → Settings → Secrets)

| Secret | Required |
|--------|----------|
| `CLOUDFLARE_API_TOKEN` | Yes — token with Workers Scripts Edit + Account Workers KV Storage Edit |
| `CLOUDFLARE_ACCOUNT_ID` | Yes — from Cloudflare dashboard URL / Workers overview |
| `ACL_GITHUB_TOKEN` | Optional — so `POST /api/v1/submit` opens a GitHub issue |

Or add the same names as Cursor / cloud-agent secrets and re-run the agent.

### 2. Deploy

```bash
cd edge
npm install
export CLOUDFLARE_API_TOKEN=...
export CLOUDFLARE_ACCOUNT_ID=...
chmod +x scripts/ensure-kv.sh
LIST_JSON="$(npx wrangler kv namespace list --format=json)" NAME=acl-stats bash scripts/ensure-kv.sh
npx wrangler deploy --config wrangler.deploy.json
```

Or push to `main` / run **Actions → Deploy ACL edge API**.

### 3. Point the domain

Cloudflare dashboard → **Workers & Pages → acl-api → Domains & Routes** → add:

`aicode.iamfaulty.com`

Keep the orange-cloud proxy. No separate origin server needed — the Worker *is* the origin.

### 4. Verify

```bash
curl -sS https://aicode.iamfaulty.com/healthz
curl -sS 'https://aicode.iamfaulty.com/api/v1/search?q=retry&limit=2'
python3 -c "import urllib.request; print(urllib.request.urlopen('https://aicode.iamfaulty.com/healthz').read().decode())"
```

CLI should report `backend: remote` again:

```bash
curl -fsSL -o /tmp/acl.py https://raw.githubusercontent.com/peteedoo/agent-code-library/main/cli/acl.py
python3 /tmp/acl.py doctor
```

## B. Container origin (Railway / Fly / Docker)

Image builds the sqlite index at build time and on start.

```bash
docker build -t acl-api .
docker run --rm -p 8000:8000 acl-api
# → http://127.0.0.1:8000/healthz
```

- Railway: `railway.toml` included; set root directory to repo root.
- Fly: `fly.toml` included; `fly launch` / `fly deploy`.

Then set Cloudflare DNS for `aicode` to that container host (Proxied).

## Why Worker is preferred here

The domain is already on Cloudflare. A Worker removes the dependency on a separate homelab/VPS that went dark and caused the multi-week 502.
