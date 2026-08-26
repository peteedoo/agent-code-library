---
id: "382882b0-4cbe-418f-ae68-3fdb26760cb7"
title: "AWS S3 Public Access Auditor"
lang: python
tags: ["domain:cloud-security", "cloud:aws", "phase:config-audit", "control:storage"]
dependencies: ["boto3"]
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "Read-only audit of S3 buckets for public ACL grants and public bucket policies."
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
"""AWS S3 public access auditor (read-only config check)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore
    ClientError = Exception  # type: ignore

PUBLIC_URI = "http://acs.amazonaws.com/groups/global/AllUsers"
AUTH_URI = "http://acs.amazonaws.com/groups/global/AuthenticatedUsers"


def _acl_public_grants(acl: Dict[str, Any]) -> List[str]:
    hits: List[str] = []
    for grant in acl.get("Grants", []):
        grantee = grant.get("Grantee") or {}
        uri = grantee.get("URI", "")
        perm = grant.get("Permission", "")
        if uri in (PUBLIC_URI, AUTH_URI):
            hits.append(f"{uri.split('/')[-1]}:{perm}")
    return hits


def audit_bucket(client: Any, name: str) -> Dict[str, Any]:
    finding: Dict[str, Any] = {
        "bucket": name,
        "public_acl_grants": [],
        "policy_allows_public": None,
        "block_public_access": None,
        "issues": [],
    }
    try:
        acl = client.get_bucket_acl(Bucket=name)
        grants = _acl_public_grants(acl)
        finding["public_acl_grants"] = grants
        if grants:
            finding["issues"].append("public_or_authenticated_acl")
    except ClientError as exc:
        finding["acl_error"] = str(exc)

    try:
        pab = client.get_public_access_block(Bucket=name)["PublicAccessBlockConfiguration"]
        finding["block_public_access"] = pab
        if not all(pab.get(k) for k in (
            "BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"
        )):
            finding["issues"].append("incomplete_public_access_block")
    except ClientError as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
        if code == "NoSuchPublicAccessBlockConfiguration":
            finding["issues"].append("missing_public_access_block")
        else:
            finding["pab_error"] = str(exc)

    try:
        pol = client.get_bucket_policy(Bucket=name)
        text = pol.get("Policy", "")
        # Heuristic: Principal "*" with Allow is a strong public-policy smell
        publicish = '"Principal":"*"' in text.replace(" ", "") or '"AWS":"*"' in text.replace(" ", "")
        finding["policy_allows_public"] = publicish
        if publicish and '"Effect":"Allow"' in text.replace(" ", ""):
            finding["issues"].append("public_bucket_policy")
    except ClientError as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
        if code != "NoSuchBucketPolicy":
            finding["policy_error"] = str(exc)

    return finding


def audit_account(profile: Optional[str] = None, region: str = "us-east-1") -> List[Dict[str, Any]]:
    if boto3 is None:
        raise RuntimeError("boto3 is required")
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    client = session.client("s3", region_name=region)
    return [audit_bucket(client, b["Name"]) for b in client.list_buckets().get("Buckets", [])]


def example() -> None:
    """Dry-run shape when credentials are absent."""
    sample = {
        "bucket": "example-logs",
        "public_acl_grants": ["AllUsers:READ"],
        "policy_allows_public": False,
        "block_public_access": None,
        "issues": ["public_or_authenticated_acl", "missing_public_access_block"],
    }
    print(sample)


if __name__ == "__main__":
    example()
```
