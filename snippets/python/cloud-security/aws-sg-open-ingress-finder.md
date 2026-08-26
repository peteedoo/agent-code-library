---
id: "1660df53-1ccb-4a13-bbdc-de27fae51efb"
title: "AWS Security Group Open Ingress Finder"
lang: python
tags: ["domain:cloud-security", "cloud:aws", "phase:config-audit", "control:network"]
dependencies: ["boto3"]
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "Find security group ingress rules that allow 0.0.0.0/0 or ::/0 on sensitive ports."
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
"""AWS security group open-ingress finder (read-only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None  # type: ignore

OPEN_CIDRS = {"0.0.0.0/0", "::/0"}
SENSITIVE_PORTS = {22, 3389, 3306, 5432, 6379, 27017, 9200, 11211}


def _ports(perm: Dict[str, Any]) -> str:
    proto = perm.get("IpProtocol", "-1")
    if proto == "-1":
        return "all"
    fp = perm.get("FromPort")
    tp = perm.get("ToPort")
    if fp is None:
        return str(proto)
    if fp == tp:
        return f"{proto}/{fp}"
    return f"{proto}/{fp}-{tp}"


def _touches_sensitive(perm: Dict[str, Any]) -> bool:
    proto = perm.get("IpProtocol", "-1")
    if proto == "-1":
        return True
    fp = perm.get("FromPort")
    tp = perm.get("ToPort")
    if fp is None or tp is None:
        return False
    return any(fp <= p <= tp for p in SENSITIVE_PORTS)


def find_open_ingress(
    profile: Optional[str] = None,
    region: str = "us-east-1",
    sensitive_only: bool = False,
) -> List[Dict[str, Any]]:
    if boto3 is None:
        raise RuntimeError("boto3 is required")
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    ec2 = session.client("ec2", region_name=region)
    findings: List[Dict[str, Any]] = []

    paginator = ec2.get_paginator("describe_security_groups")
    for page in paginator.paginate():
        for sg in page.get("SecurityGroups", []):
            for perm in sg.get("IpPermissions", []):
                cidrs: Set[str] = set()
                for r in perm.get("IpRanges", []):
                    if r.get("CidrIp") in OPEN_CIDRS:
                        cidrs.add(r["CidrIp"])
                for r in perm.get("Ipv6Ranges", []):
                    if r.get("CidrIpv6") in OPEN_CIDRS:
                        cidrs.add(r["CidrIpv6"])
                if not cidrs:
                    continue
                if sensitive_only and not _touches_sensitive(perm):
                    continue
                findings.append({
                    "group_id": sg.get("GroupId"),
                    "group_name": sg.get("GroupName"),
                    "vpc_id": sg.get("VpcId"),
                    "ports": _ports(perm),
                    "open_cidrs": sorted(cidrs),
                    "sensitive": _touches_sensitive(perm),
                })
    return findings


def example() -> None:
    print([
        {
            "group_id": "sg-0123456789abcdef0",
            "group_name": "web",
            "vpc_id": "vpc-abc",
            "ports": "tcp/22",
            "open_cidrs": ["0.0.0.0/0"],
            "sensitive": True,
        }
    ])


if __name__ == "__main__":
    example()
```
