---
id: "61a31643-3268-4f93-889e-477d03b31d34"
title: "AWS IAM Access Key Age Checker"
lang: python
tags: ["domain:cloud-security", "cloud:aws", "phase:config-audit", "control:iam"]
dependencies: ["boto3"]
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "Flag IAM users with active access keys older than a threshold (credential hygiene)."
has_tests: false
has_types: true
cloud: aws
phase: config-audit
severity_default: medium
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```python
"""AWS IAM access key age checker (read-only credential hygiene)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore


def _age_days(create_date: datetime) -> int:
    if create_date.tzinfo is None:
        create_date = create_date.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - create_date).days


def stale_access_keys(
    max_age_days: int = 90,
    profile: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if boto3 is None:
        raise RuntimeError("boto3 is required")
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    iam = session.client("iam")
    findings: List[Dict[str, Any]] = []

    paginator = iam.get_paginator("list_users")
    for page in paginator.paginate():
        for user in page.get("Users", []):
            name = user["UserName"]
            keys = iam.list_access_keys(UserName=name).get("AccessKeyMetadata", [])
            for key in keys:
                if key.get("Status") != "Active":
                    continue
                age = _age_days(key["CreateDate"])
                if age >= max_age_days:
                    findings.append({
                        "user": name,
                        "access_key_id": key["AccessKeyId"],
                        "age_days": age,
                        "max_age_days": max_age_days,
                        "create_date": key["CreateDate"].isoformat(),
                    })
    return findings


def example() -> None:
    print([{
        "user": "ci-bot",
        "access_key_id": "AKIAEXAMPLE",
        "age_days": 214,
        "max_age_days": 90,
        "create_date": "2025-01-01T00:00:00+00:00",
    }])


if __name__ == "__main__":
    example()
```
