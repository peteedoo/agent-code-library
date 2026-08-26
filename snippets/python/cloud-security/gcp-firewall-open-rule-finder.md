---
id: "aab8e981-70dc-4b8b-b270-1e3a6f807d88"
title: "GCP Firewall Open Rule Finder"
lang: python
tags: ["domain:cloud-security", "cloud:gcp", "phase:config-audit", "control:network"]
dependencies: ["google-cloud-compute"]
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "List GCP VPC firewall rules that allow ingress from 0.0.0.0/0 on sensitive ports."
has_tests: false
has_types: true
cloud: gcp
phase: config-audit
severity_default: high
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```python
"""GCP firewall open-rule finder (read-only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

OPEN = {"0.0.0.0/0", "::/0"}
SENSITIVE = {22, 3389, 3306, 5432, 6379, 27017}


def _port_sensitive(allowed: List[Dict[str, Any]]) -> bool:
    for entry in allowed or []:
        for pr in entry.get("ports") or []:
            if "-" in pr:
                a, b = pr.split("-", 1)
                try:
                    lo, hi = int(a), int(b)
                except ValueError:
                    continue
                if any(lo <= p <= hi for p in SENSITIVE):
                    return True
            else:
                try:
                    if int(pr) in SENSITIVE:
                        return True
                except ValueError:
                    if pr.lower() == "all":
                        return True
        if not entry.get("ports"):
            # protocol without ports (e.g. all) — treat as sensitive
            return True
    return False


def find_open_ingress(project: str, client: Optional[Any] = None) -> List[Dict[str, Any]]:
    if client is None:
        try:
            from google.cloud import compute_v1
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("google-cloud-compute is required") from exc
        client = compute_v1.FirewallsClient()

    findings: List[Dict[str, Any]] = []
    for rule in client.list(project=project):
        if getattr(rule, "direction", "") != "INGRESS":
            continue
        if getattr(rule, "disabled", False):
            continue
        ranges = list(getattr(rule, "source_ranges", []) or [])
        open_ranges = [r for r in ranges if r in OPEN]
        if not open_ranges:
            continue
        allowed = [
            {"protocol": a.I_p_protocol if hasattr(a, "I_p_protocol") else getattr(a, "ip_protocol", ""),
             "ports": list(getattr(a, "ports", []) or [])}
            for a in (getattr(rule, "allowed", []) or [])
        ]
        # google client uses IPProtocol attribute
        allowed_norm: List[Dict[str, Any]] = []
        for a in (getattr(rule, "allowed", []) or []):
            proto = getattr(a, "I_p_protocol", None) or getattr(a, "ip_protocol", "") or ""
            allowed_norm.append({"protocol": proto, "ports": list(getattr(a, "ports", []) or [])})
        findings.append({
            "name": rule.name,
            "network": rule.network,
            "priority": rule.priority,
            "source_ranges": open_ranges,
            "allowed": allowed_norm or allowed,
            "sensitive": _port_sensitive(allowed_norm or allowed),
        })
    return findings


def example() -> None:
    print([{
        "name": "allow-ssh-world",
        "network": "global/networks/default",
        "priority": 1000,
        "source_ranges": ["0.0.0.0/0"],
        "allowed": [{"protocol": "tcp", "ports": ["22"]}],
        "sensitive": True,
    }])


if __name__ == "__main__":
    example()
```
