---
id: "8e61bd52-02a8-48b8-b1d2-a53d13f95e96"
title: "Finding Report Schema"
lang: python
tags: ["domain:cloud-security", "phase:reporting", "control:reporting", "cloud:multi"]
dependencies: []
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "Normalize cloud security assessment findings into a comparable JSON report."
has_tests: false
has_types: true
cloud: multi
phase: reporting
severity_default: info
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```python
"""Finding report schema — normalize cloud security assessment findings for agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
import json
import uuid

SEVERITIES = ("info", "low", "medium", "high", "critical")


@dataclass
class Finding:
    title: str
    severity: str
    resource: str
    control: str
    description: str
    remediation: str = ""
    cloud: str = "generic"
    evidence: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    def __post_init__(self) -> None:
        sev = (self.severity or "info").lower()
        if sev not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}, got {self.severity!r}")
        self.severity = sev

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AssessmentReport:
    engagement: str
    scope: List[str]
    findings: List[Finding] = field(default_factory=list)
    author: str = "acl-agent"
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def by_severity(self) -> Dict[str, int]:
        counts = {s: 0 for s in SEVERITIES}
        for f in self.findings:
            counts[f.severity] += 1
        return counts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engagement": self.engagement,
            "scope": self.scope,
            "author": self.author,
            "generated_at": self.generated_at,
            "summary": self.by_severity(),
            "findings": [f.to_dict() for f in self.findings],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


def example() -> str:
    report = AssessmentReport(
        engagement="acme-prod-config-audit",
        scope=["arn:aws:s3:::acme-logs", "sg-0123456789abcdef0"],
    )
    report.add(
        Finding(
            title="Security group allows unrestricted SSH",
            severity="high",
            resource="sg-0123456789abcdef0",
            control="network",
            cloud="aws",
            description="Ingress 0.0.0.0/0 on tcp/22",
            remediation="Restrict SSH to bastion or VPN CIDRs",
            evidence={"from_port": 22, "cidr": "0.0.0.0/0"},
        )
    )
    return report.to_json()


if __name__ == "__main__":
    print(example())
```
