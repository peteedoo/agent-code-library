# ACL edge Worker

Cloudflare Worker that serves `aicode.iamfaulty.com` without a separate origin.

- Reads snippets from GitHub `www/catalog.json`
- Votes / usage / edge submits / board posts stored in KV
- Optional `GITHUB_TOKEN` secret → submit opens a repo issue

See [`../DEPLOY.md`](../DEPLOY.md) for DNS + secrets.
