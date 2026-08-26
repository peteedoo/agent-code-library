---
id: "26784683-5635-4aa9-8994-a9788633436b"
title: "Azure Storage Public Access Checker"
lang: python
tags: ["domain:cloud-security", "cloud:azure", "phase:config-audit", "control:storage"]
dependencies: ["azure-identity", "azure-mgmt-storage"]
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "Flag Azure storage accounts that allow blob public access."
has_tests: false
has_types: true
cloud: azure
phase: config-audit
severity_default: high
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```python
"""Azure storage public access checker (read-only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def check_subscription(
    subscription_id: str,
    credential: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    try:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.storage import StorageManagementClient
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("azure-identity and azure-mgmt-storage are required") from exc

    cred = credential or DefaultAzureCredential()
    client = StorageManagementClient(cred, subscription_id)
    findings: List[Dict[str, Any]] = []

    for account in client.storage_accounts.list():
        # allow_blob_public_access True means containers may be public
        allow_public = getattr(account, "allow_blob_public_access", None)
        https_only = getattr(account, "enable_https_traffic_only", None)
        min_tls = getattr(getattr(account, "minimum_tls_version", None), "value", None) or getattr(
            account, "minimum_tls_version", None
        )
        issues = []
        if allow_public is True:
            issues.append("blob_public_access_enabled")
        if https_only is False:
            issues.append("https_only_disabled")
        if min_tls and str(min_tls) not in ("TLS1_2", "TLS1_3", "Tls1_2", "Tls1_3"):
            issues.append(f"weak_tls:{min_tls}")
        if not issues:
            continue
        findings.append({
            "name": account.name,
            "id": account.id,
            "location": account.location,
            "allow_blob_public_access": allow_public,
            "https_only": https_only,
            "minimum_tls_version": str(min_tls) if min_tls else None,
            "issues": issues,
        })
    return findings


def example() -> None:
    print([{
        "name": "acmelogs",
        "id": "/subscriptions/.../storageAccounts/acmelogs",
        "location": "eastus",
        "allow_blob_public_access": True,
        "https_only": True,
        "minimum_tls_version": "TLS1_2",
        "issues": ["blob_public_access_enabled"],
    }])


if __name__ == "__main__":
    example()
```
