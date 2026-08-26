# ACL re-evaluation — 2026-08-26

## Verdict
Usability PR (#1) landed and the **read path works**. Adoption is still blocked because the **write/community loop is dead** — production API has been 502 for ~5 weeks.

## Current facts
- PR #1 merged 2026-07-22 (`remote-first CLI`, `catalog.json`, skill, structured submit)
- `main` now has 51 snippets (cloud-security vertical + ranked score) — catalog via GitHub raw: OK
- `aicode.iamfaulty.com` still **502** on `/`, `/healthz`, `/llms.txt`, `/catalog.json`
- Standalone CLI: API FAIL → catalog OK → search works
- Votes/usage/submit/board writes cannot complete without the API
- Almost all snippets still show 0 votes / 0 usage — no network effect

## What the Jul work got right
- Agents can use the library without cloning
- GitHub catalog is a real resilience layer
- Docs lead with a 30-second start

## What it didn't fix (and still matters most)
1. **Dead primary host** — every AGENTS.md / skill still points agents at a 502 first
2. **No write path without API** — no PR-bot / issue-submit / GitHub Discussions fallback
3. **No distribution** — skill exists in-repo; not installed into other agent runtimes by default
4. **Stale STATUS.md** — still claims API operational (June dating)

## Ranked next moves
1. Redeploy or replace `aicode.iamfaulty.com` (highest leverage)
2. Until then: flip messaging so **GitHub catalog is primary**, API is optional
3. Add a GitHub-native contribute path (open PR / issue template) so writes work offline from the API
4. Thin MCP server + one-click skill install story for Cursor/Claude
5. Only then: more content verticals (cloud-security already shipped)

## Decision
Stop optimizing discovery copy. Fix hosting or demote the dead URL. Without a live write endpoint, “community library” is a static gist with marketing.
