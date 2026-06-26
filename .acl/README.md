# ACL Executor

Sandboxed Python execution environment for the Agent Code Library.

## Structure

```
.acl/
├── executor/
│   ├── Dockerfile          # Multi-stage builder + runtime (<150MB target)
│   ├── requirements.txt    # Runtime Python deps (minimal)
│   ├── orchestrator.py     # Docker runner with seccomp, quotas, timeout
│   └── Makefile            # build / test / push / save helpers
├── seccomp/
│   └── acl-executor.json   # Seccomp v1 profile (default deny, allow-list)
└── tests/
    ├── test_hello.py       # Smoke test
    └── test_escape.py      # Escape/breakout tests
```

## Quick Start

```bash
cd .acl/executor
make build
make test
```

## Orchestrator Usage

```bash
python orchestrator.py \
    --snippet /path/to/snippet.py \
    --meta '{"request_id":"abc","user":"ada"}' \
    --timeout 30 \
    --memory 256m \
    --cpus 1.0 \
    --audit-dir ../audit
```

## Security Controls

| Control            | Implementation                                      |
|--------------------|-----------------------------------------------------|
| Seccomp            | `acl-executor.json` (default deny, allow-list)      |
| No new privileges  | `--security-opt no-new-privileges:true`             |
| Capabilities       | `--cap-drop ALL`                                    |
| User               | `acluser` (uid 1000)                                |
| Network            | `--network none`                                    |
| Filesystem         | Read-only root, tmpfs `/tmp`                        |
| Resources          | Memory, CPU, PIDs, fd limits                        |
| Timeout            | Orchestrator-enforced subprocess timeout            |

## Registry Fallback

If the local Gitea registry is down, use `make save` / `make load` to move the image as a tarball.
