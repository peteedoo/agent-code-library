# 2026-08-26 — Cloud security library (defensive) + ranked voting

## Ask
Build structure + defensive tools for AI cloud security library. Keep ranked voting.
User does not want a platform ban on offensive submissions; open submit stays.

## Shipped (this phase)
- `CLOUD_SECURITY.md` — vertical taxonomy + ranking formula
- Schema extras: `cloud`, `phase`, `severity_default`
- Composite `score` sort on API/CLI top + search; `--tag` filter
- Seeded defensive snippets: AWS S3/SG/IAM/CloudTrail, GCP firewall, Azure storage,
  K8s privileged scan, secrets pattern scan, HTTP headers, Dockerfile lint,
  scope validator, finding report schema
- No content-policy ban added (open submit retained)
- Agent limitation still applies personally: will not author exploit/attack payloads

## Ranking
`score = (agent_rating * 20) + votes + (usage_count * 0.25)`
