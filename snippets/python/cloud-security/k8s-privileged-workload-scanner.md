---
id: "a389cf24-6eb5-4352-80dd-87faa44a9fbe"
title: "Kubernetes Privileged Workload Scanner"
lang: python
tags: ["domain:cloud-security", "cloud:k8s", "phase:config-audit", "control:hardening"]
dependencies: ["pyyaml"]
author: "cursor-agent"
license: "MIT"
created: "2026-08-26"
updated: "2026-08-26"
description: "Scan Kubernetes YAML for privileged pods, hostNetwork, and dangerous capability adds."
has_tests: false
has_types: true
cloud: k8s
phase: config-audit
severity_default: high
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```python
"""Kubernetes privileged workload scanner (manifest YAML, offline)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, List, Union

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

DANGEROUS_CAPS = {"SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE", "SYS_MODULE", "DAC_OVERRIDE"}


def _docs(path: Path) -> Iterator[Dict[str, Any]]:
    if yaml is None:
        raise RuntimeError("PyYAML is required")
    text = path.read_text(encoding="utf-8")
    for doc in yaml.safe_load_all(text):
        if isinstance(doc, dict):
            yield doc


def _pod_spec(obj: Dict[str, Any]) -> Dict[str, Any]:
    kind = obj.get("kind", "")
    if kind == "Pod":
        return obj.get("spec") or {}
    if kind in ("Deployment", "DaemonSet", "StatefulSet", "ReplicaSet", "Job"):
        return ((obj.get("spec") or {}).get("template") or {}).get("spec") or {}
    if kind == "CronJob":
        job = ((obj.get("spec") or {}).get("jobTemplate") or {}).get("spec") or {}
        return ((job.get("template") or {}).get("spec") or {})
    return {}


def scan_object(obj: Dict[str, Any], source: str = "") -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    spec = _pod_spec(obj)
    if not spec:
        return findings
    meta = obj.get("metadata") or {}
    base = {
        "source": source,
        "kind": obj.get("kind"),
        "name": meta.get("name"),
        "namespace": meta.get("namespace", "default"),
    }
    if spec.get("hostNetwork"):
        findings.append({**base, "issue": "hostNetwork", "severity": "high"})
    if spec.get("hostPID") or spec.get("hostIPC"):
        findings.append({**base, "issue": "hostPID_or_hostIPC", "severity": "high"})

    for c in list(spec.get("containers") or []) + list(spec.get("initContainers") or []):
        sc = c.get("securityContext") or {}
        cname = c.get("name", "?")
        if sc.get("privileged"):
            findings.append({**base, "container": cname, "issue": "privileged", "severity": "critical"})
        caps = ((sc.get("capabilities") or {}).get("add") or [])
        bad = sorted(set(caps) & DANGEROUS_CAPS)
        if bad:
            findings.append({
                **base, "container": cname, "issue": "dangerous_capabilities",
                "capabilities": bad, "severity": "high",
            })
        if sc.get("allowPrivilegeEscalation") is True:
            findings.append({
                **base, "container": cname, "issue": "allowPrivilegeEscalation",
                "severity": "medium",
            })
    return findings


def scan_path(path: Union[str, Path]) -> List[Dict[str, Any]]:
    p = Path(path)
    files = [p] if p.is_file() else sorted(p.rglob("*.y*ml"))
    out: List[Dict[str, Any]] = []
    for f in files:
        for doc in _docs(f):
            out.extend(scan_object(doc, source=str(f)))
    return out


def example() -> None:
    sample = {
        "kind": "Deployment",
        "metadata": {"name": "debug", "namespace": "default"},
        "spec": {"template": {"spec": {
            "hostNetwork": True,
            "containers": [{"name": "app", "securityContext": {"privileged": True}}],
        }}},
    }
    print(scan_object(sample, source="<memory>"))


if __name__ == "__main__":
    example()
```
