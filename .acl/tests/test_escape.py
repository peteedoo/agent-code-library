#!/usr/bin/env python3
"""
ACL Escape Test Suite

Attempts common sandbox breakout vectors:
- Network egress
- Filesystem traversal outside /sandbox
- Privilege escalation / setuid binaries
- Fork bombs / resource exhaustion
- Container introspection

Each test should be BLOCKED by the orchestrator + seccomp + Docker flags.
Run via orchestrator:
    python .acl/executor/orchestrator.py --snippet .acl/tests/test_escape.py --timeout 60
"""

import os
import socket
import sys


def test_network_egress():
    """Try to open a TCP connection to an external host."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("1.1.1.1", 53))
        s.close()
        print("NETWORK_EGRESS: FAIL (connection succeeded)")
        return False
    except Exception as exc:
        print(f"NETWORK_EGRESS: PASS ({exc})")
        return True


def test_filesystem_escape():
    """Try to read files outside /sandbox."""
    targets = ["/etc/passwd", "/etc/shadow", "/proc/1/environ", "/host/etc/passwd"]
    leaked = False
    for t in targets:
        try:
            with open(t) as f:
                data = f.read(256)
                if data:
                    print(f"FS_ESCAPE: FAIL read {t}")
                    leaked = True
        except Exception as exc:
            print(f"FS_ESCAPE: PASS blocked {t} ({exc})")
    return not leaked


def test_write_outside_sandbox():
    """Try to write to /tmp, /, or other paths."""
    paths = ["/tmp/pwned", "/pwned", "/home/acluser/pwned"]
    leaked = False
    for p in paths:
        try:
            with open(p, "w") as f:
                f.write("owned")
            print(f"FS_WRITE: FAIL wrote {p}")
            leaked = True
        except Exception as exc:
            print(f"FS_WRITE: PASS blocked {p} ({exc})")
    return not leaked


def test_privilege_escalation():
    """Try to become root via setuid or capabilities."""
    try:
        os.setuid(0)
        print("PRIV_ESC: FAIL became root")
        return False
    except Exception as exc:
        print(f"PRIV_ESC: PASS blocked ({exc})")
        return True


def test_fork_bomb():
    """Try to exhaust PIDs (should hit --pids-limit)."""
    try:
        children = []
        for _ in range(200):
            pid = os.fork()
            if pid == 0:
                os._exit(0)
            else:
                children.append(pid)
        for pid in children:
            os.waitpid(pid, 0)
        print("FORK_BOMB: FAIL (no limit enforced)")
        return False
    except Exception as exc:
        print(f"FORK_BOMB: PASS blocked ({exc})")
        return True


def test_container_introspection():
    """Try to read Docker socket or cgroup info."""
    targets = ["/var/run/docker.sock", "/.dockerenv", "/proc/self/cgroup"]
    leaked = False
    for t in targets:
        try:
            with open(t) as f:
                data = f.read(256)
                if data:
                    print(f"CONTAINER_INFO: FAIL read {t}")
                    leaked = True
        except Exception as exc:
            print(f"CONTAINER_INFO: PASS blocked {t} ({exc})")
    return not leaked


def test_module_load():
    """Try to trigger a syscall blocked by seccomp (bpf, mount, etc)."""
    try:
        # This will fail in many ways; we just want to see if seccomp blocks it.
        import ctypes
        libc = ctypes.CDLL(None)
        # attempt mount(NULL, NULL, NULL, 0, NULL) -> should get EPERM/ENOSYS
        libc.mount(None, None, None, 0, None)
        print("MODULE_LOAD: FAIL mount syscall succeeded")
        return False
    except Exception as exc:
        print(f"MODULE_LOAD: PASS blocked ({exc})")
        return True


def main():
    results = {
        "network_egress": test_network_egress(),
        "filesystem_escape": test_filesystem_escape(),
        "write_outside_sandbox": test_write_outside_sandbox(),
        "privilege_escalation": test_privilege_escalation(),
        "fork_bomb": test_fork_bomb(),
        "container_introspection": test_container_introspection(),
        "module_load": test_module_load(),
    }
    passed = sum(results.values())
    total = len(results)
    print(f"\nSUMMARY: {passed}/{total} tests passed")
    if passed == total:
        print("ALL ESCAPE VECTORS BLOCKED")
        return 0
    else:
        print("SOME VECTORS NOT BLOCKED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
