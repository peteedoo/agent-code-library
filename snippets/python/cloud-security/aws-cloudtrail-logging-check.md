---
id: "268de223-2a7f-48b8-87b9-cabd6e178ec7"
title: "CloudTrail Logging Enabled Check"
lang: python
tags: ["domain:cloud-security", "cloud:aws", "phase:config-audit", "control:logging"]
dependencies: ["boto3"]
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "Verify AWS CloudTrail trails exist, are multi-region, and log file validation is on."
has_tests: false
has_types: true
cloud: aws
phase: config-audit
severity_default: high
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```python
"""AWS CloudTrail logging enabled check (read-only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore


def audit_cloudtrail(profile: Optional[str] = None) -> Dict[str, Any]:
    if boto3 is None:
        raise RuntimeError("boto3 is required")
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    ct = session.client("cloudtrail")
    trails = ct.describe_trails(includeShadowTrails=True).get("trailList", [])
    report: Dict[str, Any] = {"trail_count": len(trails), "trails": [], "issues": []}
    if not trails:
        report["issues"].append("no_trails_configured")
        return report

    multi_region = False
    for t in trails:
        name = t.get("Name")
        status = ct.get_trail_status(Name=name)
        entry = {
            "name": name,
            "is_multi_region": bool(t.get("IsMultiRegionTrail")),
            "log_file_validation": bool(t.get("LogFileValidationEnabled")),
            "is_logging": bool(status.get("IsLogging")),
            "s3_bucket": t.get("S3BucketName"),
            "kms_key_id": t.get("KmsKeyId"),
        }
        report["trails"].append(entry)
        multi_region = multi_region or entry["is_multi_region"]
        if not entry["is_logging"]:
            report["issues"].append(f"not_logging:{name}")
        if not entry["log_file_validation"]:
            report["issues"].append(f"validation_disabled:{name}")
    if not multi_region:
        report["issues"].append("no_multi_region_trail")
    return report


def example() -> None:
    print({
        "trail_count": 1,
        "trails": [{
            "name": "org-trail",
            "is_multi_region": True,
            "log_file_validation": False,
            "is_logging": True,
            "s3_bucket": "org-trail-logs",
            "kms_key_id": None,
        }],
        "issues": ["validation_disabled:org-trail"],
    })


if __name__ == "__main__":
    example()
```
