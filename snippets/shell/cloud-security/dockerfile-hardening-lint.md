---
id: "4aa88f97-271e-487a-8191-00b93e86efcb"
title: "Dockerfile Hardening Lint"
lang: shell
tags: ["domain:cloud-security", "cloud:generic", "phase:hardening", "control:hardening"]
dependencies: []
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "Shell linter that flags common Dockerfile hardening gaps (root user, latest tags, add)."
has_tests: false
has_types: false
cloud: generic
phase: hardening
severity_default: medium
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```bash
#!/usr/bin/env bash
# Dockerfile hardening lint — offline static checks for owner Dockerfiles.
set -euo pipefail

FILE="${1:-Dockerfile}"
if [[ ! -f "$FILE" ]]; then
  echo "usage: $0 <Dockerfile>" >&2
  exit 2
fi

issues=0
warn() { echo "WARN: $*"; issues=$((issues + 1)); }

# :latest tags
if grep -Eiq '^[[:space:]]*FROM[[:space:]].*:latest([[:space:]]|$)' "$FILE"; then
  warn "FROM uses :latest — pin a digest or immutable tag"
fi

# ADD instead of COPY (except remote URLs intentionally)
if grep -Eiq '^[[:space:]]*ADD[[:space:]]' "$FILE"; then
  warn "ADD found — prefer COPY unless you need remote/tar semantics"
fi

# running as root with no USER
if ! grep -Eiq '^[[:space:]]*USER[[:space:]]+' "$FILE"; then
  warn "no USER instruction — container may run as root"
fi

# secrets in ENV
if grep -Eiq '^[[:space:]]*ENV[[:space:]].*(SECRET|PASSWORD|TOKEN|API_KEY)' "$FILE"; then
  warn "ENV appears to embed a secret — use build secrets / runtime inject"
fi

# privileged-looking apt without cleanup (size/attack surface smell)
if grep -Eiq 'apt-get[[:space:]]+install' "$FILE" \
  && ! grep -Eq 'rm -rf /var/lib/apt/lists' "$FILE"; then
  warn "apt-get install without cleaning /var/lib/apt/lists"
fi

if [[ "$issues" -eq 0 ]]; then
  echo "OK: no basic hardening issues matched in $FILE"
  exit 0
fi
echo "Found $issues hardening issue(s) in $FILE"
exit 1
```
