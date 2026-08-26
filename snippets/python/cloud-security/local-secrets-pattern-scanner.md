---
id: "bd07979f-c2bd-4d0b-9756-ee180f009113"
title: "Local Secrets Pattern Scanner"
lang: python
tags: ["domain:cloud-security", "cloud:generic", "phase:config-audit", "control:secrets"]
dependencies: []
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "Scan a local directory for common secret patterns (API keys, tokens, private keys)."
has_tests: false
has_types: true
cloud: generic
phase: config-audit
severity_default: high
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```python
"""Local secrets pattern scanner for owner-operated trees."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterator, List, Pattern, Tuple, Union

PATTERNS: List[Tuple[str, Pattern[str]]] = [
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("generic_api_key", re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"][^'\"]{12,}['\"]")),
    ("private_key_header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", ".acl"}
TEXT_SUFFIXES = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".env", ".yml", ".yaml",
    ".json", ".toml", ".ini", ".cfg", ".sh", ".md", ".txt", ".tf",
}


def _iter_files(root: Path) -> Iterator[Path]:
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in TEXT_SUFFIXES and p.name not in {".env", "Dockerfile"}:
            continue
        yield p


def scan_tree(root: Union[str, Path], max_bytes: int = 1_000_000) -> List[Dict[str, object]]:
    base = Path(root)
    findings: List[Dict[str, object]] = []
    for path in _iter_files(base):
        try:
            data = path.read_bytes()[:max_bytes].decode("utf-8", errors="ignore")
        except OSError:
            continue
        for line_no, line in enumerate(data.splitlines(), 1):
            for name, cre in PATTERNS:
                if cre.search(line):
                    findings.append({
                        "path": str(path),
                        "line": line_no,
                        "pattern": name,
                        "snippet": line.strip()[:120],
                    })
    return findings


def example() -> None:
    print([{
        "path": "config/.env",
        "line": 3,
        "pattern": "aws_access_key",
        "snippet": "AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX",
    }])


if __name__ == "__main__":
    example()
```
