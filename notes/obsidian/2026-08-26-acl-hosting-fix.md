# ACL hosting fix — 2026-08-26

## Diagnosis
- `aicode.iamfaulty.com` resolves to Cloudflare (orange-cloud)
- TLS works; origin returns **502** (no healthy backend)
- FastAPI app is fine locally once indexed (`/healthz` → 51 snippets)
- No Railway/CF/HF credentials available in this cloud agent

## Fix shipped in-repo
1. `edge/` — Cloudflare Worker API (catalog from GitHub + KV for votes/usage/submit/board)
2. `.github/workflows/deploy-edge.yml` — deploy on push when secrets present
3. Root `Dockerfile` + `scripts/entrypoint.sh` — bake/rebuild index so containers don't boot empty
4. `railway.toml` / `fly.toml` / `DEPLOY.md`

## Blocked on user
- Add secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`
- Attach custom domain `aicode.iamfaulty.com` to Worker `acl-api`

Until then the read path stays on GitHub catalog fallback; writes remain unavailable on the public hostname.
