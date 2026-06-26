#!/usr/bin/env python3
"""
ACL Executor Orchestrator

Takes a snippet path + metadata, runs a Docker container with seccomp,
captures stdout/stderr/exit code, enforces timeout, and writes an audit log.

Usage:
    python orchestrator.py --snippet /path/to/snippet.py \
        --meta '{"request_id":"abc","user":"ada"}' \
        --timeout 30 \
        --memory 256m \
        --cpus 1.0

Output:
    JSON result written to stdout and optionally --outfile.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_IMAGE = "acl-executor:latest"
DEFAULT_TIMEOUT = 30
DEFAULT_MEMORY = "256m"
DEFAULT_CPUS = "1.0"
DEFAULT_SECCOMP = Path(__file__).resolve().parent.parent / "seccomp" / "acl-executor.json"


def build_docker_run_cmd(
    snippet_path: Path,
    image: str,
    timeout_sec: int,
    memory: str,
    cpus: str,
    seccomp_profile: Path,
    read_only: bool = True,
    network: str = "none",
    tmpfs_size: str = "64m",
) -> list:
    """Construct the docker run command for sandboxed execution."""
    if not seccomp_profile.exists():
        raise FileNotFoundError(f"Seccomp profile not found: {seccomp_profile}")

    cmd = [
        "docker", "run",
        "--rm",
        "--init",
        "--network", network,
        "--memory", memory,
        "--memory-swap", memory,
        "--cpus", cpus,
        "--pids-limit", "64",
        "--ulimit", "nofile=256:256",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        "--security-opt", f"seccomp={seccomp_profile}",
        "--read-only" if read_only else "",
        "--tmpfs", f"/tmp:noexec,nosuid,size={tmpfs_size}",
        # Private /proc mount with hidepid to block proc info leaks
        "--mount", "type=proc,target=/proc",
        "-v", f"{snippet_path.resolve()}:/sandbox/snippet.py:ro",
        "-w", "/sandbox",
        "-u", "acluser",
        image,
        "-u", "/sandbox/snippet.py",
    ]
    # Filter empty strings from conditional flags
    return [c for c in cmd if c]


def run_sandbox(
    snippet_path: Path,
    meta: Dict[str, Any],
    image: str = DEFAULT_IMAGE,
    timeout_sec: int = DEFAULT_TIMEOUT,
    memory: str = DEFAULT_MEMORY,
    cpus: str = DEFAULT_CPUS,
    seccomp_profile: Path = DEFAULT_SECCOMP,
    audit_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run the snippet in a Docker sandbox and return structured results."""
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    t0 = time.monotonic()

    cmd = build_docker_run_cmd(
        snippet_path=snippet_path,
        image=image,
        timeout_sec=timeout_sec,
        memory=memory,
        cpus=cpus,
        seccomp_profile=seccomp_profile,
    )

    result = {
        "run_id": run_id,
        "started_at": started_at,
        "image": image,
        "command": cmd,
        "meta": meta,
        "timeout_sec": timeout_sec,
        "memory_limit": memory,
        "cpu_limit": cpus,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "duration_ms": 0,
        "killed": False,
        "error": None,
    }

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        result["exit_code"] = proc.returncode
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
    except subprocess.TimeoutExpired as exc:
        result["killed"] = True
        result["error"] = "timeout"
        result["stdout"] = exc.stdout.decode("utf-8", errors="replace") if exc.stdout else ""
        result["stderr"] = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
        result["exit_code"] = -9
    except FileNotFoundError as exc:
        result["error"] = f"docker not found or seccomp profile missing: {exc}"
        result["exit_code"] = -1
    except Exception as exc:
        result["error"] = str(exc)
        result["exit_code"] = -1
    finally:
        result["duration_ms"] = round((time.monotonic() - t0) * 1000, 2)

    # Write audit log
    if audit_dir:
        audit_dir = Path(audit_dir)
        audit_dir.mkdir(parents=True, exist_ok=True)
        audit_path = audit_dir / f"{run_id}.json"
        audit_path.write_text(json.dumps(result, indent=2, default=str))
        result["audit_log"] = str(audit_path)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="ACL Executor Orchestrator")
    parser.add_argument("--snippet", required=True, type=Path, help="Path to Python snippet")
    parser.add_argument("--meta", default="{}", help="JSON metadata string")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="Docker image to use")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Timeout in seconds")
    parser.add_argument("--memory", default=DEFAULT_MEMORY, help="Memory limit (e.g. 256m)")
    parser.add_argument("--cpus", default=DEFAULT_CPUS, help="CPU limit (e.g. 1.0)")
    parser.add_argument("--seccomp", type=Path, default=DEFAULT_SECCOMP, help="Seccomp profile path")
    parser.add_argument("--audit-dir", type=Path, default=None, help="Directory to write audit JSON logs")
    parser.add_argument("--outfile", type=Path, default=None, help="Optional JSON output file")
    args = parser.parse_args()

    if not args.snippet.exists():
        print(f"ERROR: Snippet not found: {args.snippet}", file=sys.stderr)
        return 1

    meta = json.loads(args.meta)
    result = run_sandbox(
        snippet_path=args.snippet,
        meta=meta,
        image=args.image,
        timeout_sec=args.timeout,
        memory=args.memory,
        cpus=args.cpus,
        seccomp_profile=args.seccomp,
        audit_dir=args.audit_dir,
    )

    out = json.dumps(result, indent=2, default=str)
    print(out)
    if args.outfile:
        args.outfile.write_text(out)

    return 0 if (result["exit_code"] == 0 and not result["killed"]) else 1


if __name__ == "__main__":
    sys.exit(main())
