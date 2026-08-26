---
id: "907fb12c-6dd9-4949-94ff-863e099b2afa"
title: "Engagement Scope Validator"
lang: python
tags: ["domain:cloud-security", "phase:scope", "cloud:multi", "control:governance"]
dependencies: []
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "Validate assessment targets against an authorized scope list before scanning."
has_tests: false
has_types: true
cloud: multi
phase: scope
severity_default: high
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```python
"""Engagement scope validator — refuse to assess out-of-scope targets."""

from __future__ import annotations

import fnmatch
import ipaddress
from dataclasses import dataclass, field
from typing import Iterable, List, Sequence


@dataclass
class ScopeViolation(Exception):
    target: str
    reason: str

    def __str__(self) -> str:
        return f"out of scope: {self.target} ({self.reason})"


@dataclass
class EngagementScope:
    """Authorized targets: hostnames, CIDRs, ARNs, k8s namespaces, glob patterns."""

    allowed: List[str] = field(default_factory=list)
    denied: List[str] = field(default_factory=list)

    def _match(self, target: str, patterns: Sequence[str]) -> bool:
        t = target.strip().lower()
        for pat in patterns:
            p = pat.strip().lower()
            if not p:
                continue
            if t == p or fnmatch.fnmatch(t, p):
                return True
            # CIDR containment for IP literals
            try:
                ip = ipaddress.ip_address(t.split("/")[0])
                net = ipaddress.ip_network(p, strict=False)
                if ip in net:
                    return True
            except ValueError:
                pass
        return False

    def is_allowed(self, target: str) -> bool:
        if self._match(target, self.denied):
            return False
        if not self.allowed:
            return False
        return self._match(target, self.allowed)

    def assert_in_scope(self, target: str) -> None:
        if self._match(target, self.denied):
            raise ScopeViolation(target, "explicitly denied")
        if not self.is_allowed(target):
            raise ScopeViolation(target, "not in allowed list")

    def filter_in_scope(self, targets: Iterable[str]) -> List[str]:
        return [t for t in targets if self.is_allowed(t)]


def example() -> None:
    scope = EngagementScope(
        allowed=["*.acme.internal", "10.0.0.0/8", "arn:aws:s3:::acme-*"],
        denied=["*.prod-payments.acme.internal"],
    )
    for t in ["api.acme.internal", "10.1.2.3", "evil.example.com"]:
        ok = scope.is_allowed(t)
        print(f"{t}: {'in-scope' if ok else 'BLOCKED'}")


if __name__ == "__main__":
    example()
```
