---
id: "b3309c58-309c-4ac1-a84d-fd746f1a7b53"
title: "HTTP Security Headers Auditor"
lang: python
tags: ["domain:cloud-security", "cloud:generic", "phase:config-audit", "control:headers"]
dependencies: []
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "Check a URL response for missing or weak security headers (owner-authorized targets)."
has_tests: false
has_types: true
cloud: generic
phase: config-audit
severity_default: medium
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```python
"""HTTP security headers auditor for authorized targets."""

from __future__ import annotations

import ssl
import urllib.request
from typing import Dict, List, Optional, Tuple

EXPECTED = {
    "strict-transport-security": "HSTS missing",
    "content-security-policy": "CSP missing",
    "x-content-type-options": "X-Content-Type-Options missing",
    "x-frame-options": "X-Frame-Options / frame ancestors missing",
    "referrer-policy": "Referrer-Policy missing",
    "permissions-policy": "Permissions-Policy missing",
}


def fetch_headers(url: str, timeout: float = 10.0) -> Dict[str, str]:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "acl-sec-headers/1.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return {k.lower(): v for k, v in resp.headers.items()}


def audit_headers(headers: Dict[str, str]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    lower = {k.lower(): v for k, v in headers.items()}
    for name, msg in EXPECTED.items():
        if name not in lower:
            # frame ancestors may live inside CSP
            if name == "x-frame-options" and "content-security-policy" in lower:
                if "frame-ancestors" in lower["content-security-policy"].lower():
                    continue
            findings.append({"header": name, "issue": msg, "severity": "medium"})
    cto = lower.get("x-content-type-options", "")
    if cto and cto.lower() != "nosniff":
        findings.append({
            "header": "x-content-type-options",
            "issue": f"unexpected value: {cto}",
            "severity": "low",
        })
    return findings


def audit_url(url: str) -> Dict[str, object]:
    headers = fetch_headers(url)
    return {"url": url, "findings": audit_headers(headers), "observed": headers}


def example() -> None:
    sample = {
        "server": "example",
        "content-type": "text/html",
    }
    print(audit_headers(sample))


if __name__ == "__main__":
    example()
```
