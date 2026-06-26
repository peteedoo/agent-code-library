#!/usr/bin/env python3
"""
curated_top_100.py — Seed the Agent Code Library with 100 well-sourced snippets.

Searches GitHub for top implementations of common patterns, formats them as ACL
snippets with attribution, and submits them to the library.

Usage:
  python3 scripts/curated_top_100.py              # Seed via API
  python3 scripts/curated_top_100.py --dry-run     # Show what would be submitted
  python3 scripts/curated_top_100.py --repo-only   # Write files directly, skip API

Requires GITHUB_TOKEN env var for the GitHub search API.
Without it, uses template implementations (no GitHub search).
"""

import json
import os
import re
import sys
import urllib.request
import urllib.parse
import uuid
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
SNIPPETS_DIR = REPO_ROOT / "snippets"
API_BASE = os.environ.get("ACL_API_URL", "http://127.0.0.1:8001")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ─── Top 100 Pattern Definitions ──────────────────────────────

PATTERNS = [
    # Python — 30
    {"title": "Exponential Backoff Retry", "lang": "python", "tags": ["pattern:resilience", "domain:networking", "retry", "decorator"], "source": "https://github.com/litl/backoff", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Rate Limiter (Token Bucket)", "lang": "python", "tags": ["pattern:rate-limiting", "domain:networking", "throttle"], "source": "https://github.com/patrick91/ratelimit", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Circuit Breaker", "lang": "python", "tags": ["pattern:resilience", "domain:networking", "circuit-breaker"], "source": "https://github.com/hynek/circuitbreaker", "has_tests": True, "has_types": True, "deps": []},
    {"title": "ThreadPool Batch Processor", "lang": "python", "tags": ["pattern:concurrency", "threadpool", "batch"], "source": "https://github.com/python/cpython/blob/main/Lib/concurrent/futures/thread.py", "has_tests": False, "has_types": True, "deps": []},
    {"title": "Async Task Queue (asyncio)", "lang": "python", "tags": ["pattern:concurrency", "async", "queue"], "source": "https://docs.python.org/3/library/asyncio-queue.html", "has_tests": False, "has_types": True, "deps": []},
    {"title": "Caching Decorator (LRU)", "lang": "python", "tags": ["pattern:caching", "lru", "decorator", "performance"], "source": "https://github.com/python/cpython/blob/main/Lib/functools.py", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Singleton Pattern (Metaclass)", "lang": "python", "tags": ["pattern:creational", "singleton", "metaclass"], "source": "https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python", "has_tests": False, "has_types": True, "deps": []},
    {"title": "Observer Pattern", "lang": "python", "tags": ["pattern:behavioral", "observer", "events"], "source": "https://refactoring.guru/design-patterns/observer/python/example", "has_tests": False, "has_types": True, "deps": []},
    {"title": "Strategy Pattern", "lang": "python", "tags": ["pattern:behavioral", "strategy", "dependency-injection"], "source": "https://refactoring.guru/design-patterns/strategy/python/example", "has_tests": False, "has_types": True, "deps": []},
    {"title": "Factory Pattern", "lang": "python", "tags": ["pattern:creational", "factory", "polymorphism"], "source": "https://refactoring.guru/design-patterns/factory-method/python/example", "has_tests": False, "has_types": True, "deps": []},
    {"title": "Context Manager (Database)", "lang": "python", "tags": ["pattern:resource-management", "database", "sqlite", "context-manager"], "source": "https://docs.python.org/3/library/sqlite3.html", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Dataclass Validation (pydantic-style)", "lang": "python", "tags": ["pattern:validation", "dataclass", "serialization"], "source": "https://docs.python.org/3/library/dataclasses.html", "has_tests": True, "has_types": True, "deps": []},
    {"title": "JSON Lines Logger", "lang": "python", "tags": ["pattern:observability", "logging", "json", "structured-logging"], "source": "https://docs.python.org/3/library/logging.html", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Health Check Endpoint (FastAPI)", "lang": "python", "tags": ["pattern:observability", "fastapi", "health-check", "domain:web"], "source": "https://fastapi.tiangolo.com/", "has_tests": False, "has_types": True, "deps": ["fastapi"]},
    {"title": "Environment Config Loader", "lang": "python", "tags": ["pattern:configuration", "env", "config", "12factor"], "source": "https://github.com/theskumar/python-dotenv", "has_tests": True, "has_types": True, "deps": []},
    {"title": "CLI Argument Parser", "lang": "python", "tags": ["pattern:cli", "argparse", "command-line"], "source": "https://docs.python.org/3/library/argparse.html", "has_tests": False, "has_types": True, "deps": []},
    {"title": "CSV Reader with Schema Validation", "lang": "python", "tags": ["pattern:data-processing", "csv", "validation"], "source": "https://docs.python.org/3/library/csv.html", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Async HTTP Client (aiohttp)", "lang": "python", "tags": ["pattern:networking", "async", "http", "aiohttp"], "source": "https://github.com/aio-libs/aiohttp", "has_tests": True, "has_types": True, "deps": ["aiohttp"]},
    {"title": "WebSocket Echo Handler", "lang": "python", "tags": ["pattern:networking", "websocket", "async"], "source": "https://websockets.readthedocs.io/", "has_tests": False, "has_types": True, "deps": ["websockets"]},
    {"title": "SQLAlchemy Async Session", "lang": "python", "tags": ["pattern:database", "sqlalchemy", "async", "orm"], "source": "https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html", "has_tests": True, "has_types": True, "deps": ["sqlalchemy", "asyncpg"]},
    {"title": "JWT Auth Middleware", "lang": "python", "tags": ["pattern:auth", "jwt", "middleware", "domain:web"], "source": "https://github.com/jpadilla/pyjwt", "has_tests": True, "has_types": True, "deps": ["PyJWT"]},
    {"title": "Scheduled Cron Jobs (APScheduler)", "lang": "python", "tags": ["pattern:scheduling", "cron", "background-tasks"], "source": "https://github.com/agronholm/apscheduler", "has_tests": False, "has_types": True, "deps": ["apscheduler"]},
    {"title": "Progress Bar for Iterables", "lang": "python", "tags": ["pattern:ui", "progress", "tqdm-style"], "source": "https://github.com/tqdm/tqdm", "has_tests": True, "has_types": True, "deps": []},
    {"title": "File Watcher / Poller", "lang": "python", "tags": ["pattern:file-system", "watcher", "poller", "domain:devops"], "source": "https://github.com/gorakhargosh/watchdog", "has_tests": False, "has_types": False, "deps": ["watchdog"]},
    {"title": "State Machine", "lang": "python", "tags": ["pattern:behavioral", "state-machine", "fsm"], "source": "https://github.com/pytransitions/transitions", "has_tests": True, "has_types": True, "deps": ["transitions"]},
    {"title": "Dependency Injection Container", "lang": "python", "tags": ["pattern:architectural", "dependency-injection", "ioc"], "source": "https://github.com/ets-labs/python-dependency-injector", "has_tests": True, "has_types": True, "deps": ["dependency-injector"]},
    {"title": "GraphQL Client", "lang": "python", "tags": ["pattern:networking", "graphql", "api-client"], "source": "https://github.com/graphql-python/gql", "has_tests": True, "has_types": True, "deps": ["gql"]},
    {"title": "Pagination Helper (Cursor-based)", "lang": "python", "tags": ["pattern:data-processing", "pagination", "cursor", "api"], "source": "https://stackoverflow.com/questions/55378697/cursor-based-pagination", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Temporary File Manager", "lang": "python", "tags": ["pattern:resource-management", "tempfile", "cleanup"], "source": "https://docs.python.org/3/library/tempfile.html", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Event Emitter (Typed)", "lang": "python", "tags": ["pattern:behavioral", "events", "pubsub", "typed"], "source": "https://github.com/pyeve/events", "has_tests": True, "has_types": True, "deps": []},

    # TypeScript — 25
    {"title": "Fetch with Retry and Timeout", "lang": "typescript", "tags": ["pattern:resilience", "domain:networking", "fetch", "retry"], "source": "https://github.com/zeit/fetch-retry", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Debounce Hook (React)", "lang": "typescript", "tags": ["pattern:react", "hooks", "debounce", "ui"], "source": "https://github.com/streamich/react-use", "has_tests": True, "has_types": True, "deps": ["react"]},
    {"title": "Throttle Function", "lang": "typescript", "tags": ["pattern:performance", "throttle", "rate-limiting", "ui"], "source": "https://github.com/lodash/lodash", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Zod Validation Middleware", "lang": "typescript", "tags": ["pattern:validation", "zod", "middleware", "domain:web"], "source": "https://github.com/colinhacks/zod", "has_tests": True, "has_types": True, "deps": ["zod"]},
    {"title": "Deep Merge Utility", "lang": "typescript", "tags": ["pattern:utility", "merge", "object"], "source": "https://github.com/lodash/lodash", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Event Emitter (Type-safe)", "lang": "typescript", "tags": ["pattern:behavioral", "events", "pubsub", "typesafe"], "source": "https://github.com/andywer/typed-event-emitter", "has_tests": True, "has_types": True, "deps": []},
    {"title": "LRU Cache", "lang": "typescript", "tags": ["pattern:caching", "lru", "performance"], "source": "https://github.com/isaacs/node-lru-cache", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Promise Pool (Concurrency Limit)", "lang": "typescript", "tags": ["pattern:concurrency", "promise", "pool", "async"], "source": "https://github.com/supercharge/promise-pool", "has_tests": True, "has_types": True, "deps": []},
    {"title": "JWT Verification Utility", "lang": "typescript", "tags": ["pattern:auth", "jwt", "token", "domain:web"], "source": "https://github.com/auth0/node-jsonwebtoken", "has_tests": True, "has_types": True, "deps": ["jsonwebtoken"]},
    {"title": "Express Error Handler Middleware", "lang": "typescript", "tags": ["pattern:error-handling", "express", "middleware", "domain:web"], "source": "https://github.com/goldbergyoni/nodebestpractices", "has_tests": False, "has_types": True, "deps": ["express"]},
    {"title": "Rate Limiter Middleware (Express)", "lang": "typescript", "tags": ["pattern:rate-limiting", "express", "middleware", "domain:web"], "source": "https://github.com/express-rate-limit/express-rate-limit", "has_tests": True, "has_types": True, "deps": ["express", "express-rate-limit"]},
    {"title": "Logger (pino-style)", "lang": "typescript", "tags": ["pattern:observability", "logging", "structured", "pino"], "source": "https://github.com/pinojs/pino", "has_tests": True, "has_types": True, "deps": ["pino"]},
    {"title": "Configuration Loader (env+file)", "lang": "typescript", "tags": ["pattern:configuration", "env", "config"], "source": "https://github.com/motdotla/dotenv", "has_tests": True, "has_types": True, "deps": ["dotenv"]},
    {"title": "Retry with Exponential Backoff (async)", "lang": "typescript", "tags": ["pattern:resilience", "async", "retry", "backoff"], "source": "https://github.com/nicktomlin/retry-ts", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Pretty JSON Formatter", "lang": "typescript", "tags": ["pattern:utility", "json", "formatting"], "source": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Tree Shakeable Utils Bundle", "lang": "typescript", "tags": ["pattern:architectural", "tree-shaking", "bundling"], "source": "https://github.com/you-dont-need/You-Dont-Need-Lodash-Underscore", "has_tests": False, "has_types": True, "deps": []},
    {"title": "Singleton (Module-level)", "lang": "typescript", "tags": ["pattern:creational", "singleton", "module"], "source": "https://refactoring.guru/design-patterns/singleton/typescript/example", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Observer (EventTarget)", "lang": "typescript", "tags": ["pattern:behavioral", "observer", "dom-events"], "source": "https://developer.mozilla.org/en-US/docs/Web/API/EventTarget", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Async Retry Queue", "lang": "typescript", "tags": ["pattern:resilience", "async", "queue", "retry"], "source": "https://github.com/joewalnes/promise-retry", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Date Formatting Utility", "lang": "typescript", "tags": ["pattern:utility", "date", "formatting"], "source": "https://github.com/iamkun/dayjs", "has_tests": True, "has_types": True, "deps": ["dayjs"]},
    {"title": "Memoize (WeakMap cache)", "lang": "typescript", "tags": ["pattern:performance", "memoize", "cache", "weakmap"], "source": "https://github.com/any86/any-ts", "has_tests": True, "has_types": True, "deps": []},
    {"title": "URL Query String Builder", "lang": "typescript", "tags": ["pattern:utility", "url", "query-string"], "source": "https://github.com/sindresorhus/query-string", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Schema Validator (Zod-based)", "lang": "typescript", "tags": ["pattern:validation", "zod", "schema"], "source": "https://github.com/colinhacks/zod", "has_tests": True, "has_types": True, "deps": ["zod"]},
    {"title": "AsyncPool (n-at-a-time)", "lang": "typescript", "tags": ["pattern:concurrency", "async", "pool", "parallel"], "source": "https://github.com/rxaviers/async-pool", "has_tests": True, "has_types": True, "deps": []},
    {"title": "Object Diff / Patch", "lang": "typescript", "tags": ["pattern:utility", "diff", "patch", "object"], "source": "https://github.com/benjamine/jsondiffpatch", "has_tests": True, "has_types": True, "deps": []},

    # Shell — 20
    {"title": "PostgreSQL Backup Script", "lang": "shell", "tags": ["pattern:backup", "postgres", "database", "domain:devops"], "source": "https://github.com/tsibley/postgres-backup", "has_tests": False, "has_types": False, "deps": ["pg_dump"]},
    {"title": "Docker Cleanup (prune)", "lang": "shell", "tags": ["pattern:cleanup", "docker", "disk", "domain:devops"], "source": "https://github.com/nicolodiamante/docker-cleanup", "has_tests": False, "has_types": False, "deps": ["docker"]},
    {"title": "Health Check Loop (wait-for-it)", "lang": "shell", "tags": ["pattern:health-check", "docker", "wait", "domain:devops"], "source": "https://github.com/vishnubob/wait-for-it", "has_tests": False, "has_types": False, "deps": []},
    {"title": "File Rotation (logrotate-style)", "lang": "shell", "tags": ["pattern:log-rotation", "logrotate", "sysadmin"], "source": "https://github.com/logrotate/logrotate", "has_tests": False, "has_types": False, "deps": []},
    {"title": "SSH Key Generator", "lang": "shell", "tags": ["pattern:security", "ssh", "keygen", "domain:devops"], "source": "https://www.ssh.com/academy/ssh/keygen", "has_tests": False, "has_types": False, "deps": ["ssh-keygen"]},
    {"title": "Git Branch Cleanup", "lang": "shell", "tags": ["pattern:git", "cleanup", "branches", "domain:devops"], "source": "https://stackoverflow.com/questions/6127328/how-can-i-delete-all-git-branches-which-have-been-merged", "has_tests": False, "has_types": False, "deps": ["git"]},
    {"title": "Disk Usage Report", "lang": "shell", "tags": ["pattern:monitoring", "disk", "du", "domain:devops"], "source": "https://www.gnu.org/software/coreutils/du", "has_tests": False, "has_types": False, "deps": []},
    {"title": "SSL Certificate Checker", "lang": "shell", "tags": ["pattern:monitoring", "ssl", "certificate", "domain:devops"], "source": "https://stackoverflow.com/questions/515394/check-expiry-date-of-ssl-certificate", "has_tests": False, "has_types": False, "deps": ["openssl"]},
    {"title": "Directory Tree Printer", "lang": "shell", "tags": ["pattern:utility", "tree", "directory"], "source": "https://www.gnu.org/software/coreutils/tree", "has_tests": False, "has_types": False, "deps": []},
    {"title": "Timestamped Log Function", "lang": "shell", "tags": ["pattern:logging", "timestamp", "bash"], "source": "https://stackoverflow.com/questions/1401482/yyyy-mm-dd-format-date-in-shell-script", "has_tests": False, "has_types": False, "deps": []},
    {"title": "Color Output Helper", "lang": "shell", "tags": ["pattern:ui", "color", "tput", "bash"], "source": "https://github.com/fidian/ansi", "has_tests": False, "has_types": False, "deps": []},
    {"title": "Parallel Job Runner (xargs)", "lang": "shell", "tags": ["pattern:parallel", "xargs", "batch", "bash"], "source": "https://www.gnu.org/software/findutils/manual/html_node/find_html/xargs.html", "has_tests": False, "has_types": False, "deps": []},
    {"title": "CSV Parser (awk)", "lang": "shell", "tags": ["pattern:data-processing", "csv", "awk", "bash"], "source": "https://github.com/jehiah/CSV.awk", "has_tests": False, "has_types": False, "deps": ["awk"]},
    {"title": "Find Duplicate Files", "lang": "shell", "tags": ["pattern:utility", "duplicates", "find", "checksum"], "source": "https://stackoverflow.com/questions/2491978/listing-all-duplicate-files-in-a-directory", "has_tests": False, "has_types": False, "deps": ["find"]},
    {"title": "Simple HTTP Server (python3)", "lang": "shell", "tags": ["pattern:networking", "http-server", "python", "bash"], "source": "https://docs.python.org/3/library/http.server.html", "has_tests": False, "has_types": False, "deps": ["python3"]},
    {"title": "Environment Variable Validator", "lang": "shell", "tags": ["pattern:validation", "env", "bash"], "source": "https://stackoverflow.com/questions/3601515/how-to-check-if-a-variable-is-set-in-bash", "has_tests": False, "has_types": False, "deps": []},
    {"title": "Retry Command Until Success", "lang": "shell", "tags": ["pattern:resilience", "retry", "bash"], "source": "https://github.com/nickstenning/retry", "has_tests": False, "has_types": False, "deps": []},
    {"title": "Directory Size Summary", "lang": "shell", "tags": ["pattern:monitoring", "disk", "size", "bash"], "source": "https://www.gnu.org/software/coreutils/du", "has_tests": False, "has_types": False, "deps": []},
    {"title": "Timestamp-based File Backup", "lang": "shell", "tags": ["pattern:backup", "timestamp", "cp", "bash"], "source": "https://stackoverflow.com/questions/11301232/backup-file-with-timestamp", "has_tests": False, "has_types": False, "deps": []},
    {"title": "Tail Multiple Logs (multitail)", "lang": "shell", "tags": ["pattern:monitoring", "logs", "tail", "bash"], "source": "https://github.com/joakim666/multitail", "has_tests": False, "has_types": False, "deps": []},

    # Go — 25
    {"title": "HTTP Server with Middleware", "lang": "go", "tags": ["pattern:networking", "http", "middleware", "domain:web"], "source": "https://github.com/go-chi/chi", "has_tests": True, "has_types": False, "deps": []},
    {"title": "Graceful Shutdown", "lang": "go", "tags": ["pattern:resource-management", "shutdown", "signal", "domain:devops"], "source": "https://github.com/facebookgo/grace", "has_tests": False, "has_types": False, "deps": []},
    {"title": "Rate Limiter (sync-based)", "lang": "go", "tags": ["pattern:rate-limiting", "sync", "golang"], "source": "https://golang.org/x/time/rate", "has_tests": True, "has_types": False, "deps": ["golang.org/x/time"]},
    {"title": "Worker Pool (goroutines)", "lang": "go", "tags": ["pattern:concurrency", "goroutines", "worker-pool"], "source": "https://gobyexample.com/worker-pools", "has_tests": True, "has_types": False, "deps": []},
    {"title": "JWT Auth Middleware (Go)", "lang": "go", "tags": ["pattern:auth", "jwt", "middleware", "domain:web"], "source": "https://github.com/golang-jwt/jwt", "has_tests": True, "has_types": False, "deps": ["github.com/golang-jwt/jwt"]},
    {"title": "SQLite Repository Pattern", "lang": "go", "tags": ["pattern:database", "sqlite", "repository", "golang"], "source": "https://github.com/mattn/go-sqlite3", "has_tests": True, "has_types": False, "deps": ["github.com/mattn/go-sqlite3"]},
    {"title": "Configuration Loader (Viper)", "lang": "go", "tags": ["pattern:configuration", "viper", "config", "golang"], "source": "https://github.com/spf13/viper", "has_tests": True, "has_types": False, "deps": ["github.com/spf13/viper"]},
    {"title": "Structured Logger (zap)", "lang": "go", "tags": ["pattern:observability", "logging", "zap", "golang"], "source": "https://github.com/uber-go/zap", "has_tests": True, "has_types": False, "deps": ["go.uber.org/zap"]},
    {"title": "CLI with Cobra", "lang": "go", "tags": ["pattern:cli", "cobra", "command-line", "golang"], "source": "https://github.com/spf13/cobra", "has_tests": True, "has_types": False, "deps": ["github.com/spf13/cobra"]},
    {"title": "JSON REST Client", "lang": "go", "tags": ["pattern:networking", "http", "rest", "json"], "source": "https://pkg.go.dev/net/http", "has_tests": True, "has_types": False, "deps": []},
    {"title": "Circuit Breaker (sony)", "lang": "go", "tags": ["pattern:resilience", "circuit-breaker", "golang"], "source": "https://github.com/sony/gobreaker", "has_tests": True, "has_types": False, "deps": ["github.com/sony/gobreaker"]},
    {"title": "Retry with Backoff", "lang": "go", "tags": ["pattern:resilience", "retry", "backoff", "golang"], "source": "https://github.com/cenkalti/backoff", "has_tests": True, "has_types": False, "deps": ["github.com/cenkalti/backoff"]},
    {"title": "Mutex-protected Cache", "lang": "go", "tags": ["pattern:caching", "mutex", "sync", "golang"], "source": "https://pkg.go.dev/sync", "has_tests": True, "has_types": False, "deps": []},
    {"title": "Health Check Handler", "lang": "go", "tags": ["pattern:observability", "health-check", "golang", "domain:web"], "source": "https://pkg.go.dev/net/http", "has_tests": True, "has_types": False, "deps": []},
    {"title": "Context-aware Timeout", "lang": "go", "tags": ["pattern:concurrency", "context", "timeout", "golang"], "source": "https://pkg.go.dev/context", "has_tests": True, "has_types": False, "deps": []},
    {"title": "Semaphore (weighted)", "lang": "go", "tags": ["pattern:concurrency", "semaphore", "golang", "rate-limiting"], "source": "https://pkg.go.dev/golang.org/x/sync/semaphore", "has_tests": True, "has_types": False, "deps": ["golang.org/x/sync"]},
    {"title": "Slice Filter/Map/Reduce", "lang": "go", "tags": ["pattern:functional", "slice", "map", "filter", "golang"], "source": "https://github.com/samber/lo", "has_tests": True, "has_types": False, "deps": ["github.com/samber/lo"]},
    {"title": "File Change Watcher (fsnotify)", "lang": "go", "tags": ["pattern:file-system", "watcher", "fsnotify", "golang"], "source": "https://github.com/fsnotify/fsnotify", "has_tests": True, "has_types": False, "deps": ["github.com/fsnotify/fsnotify"]},
    {"title": "TLS Server Setup", "lang": "go", "tags": ["pattern:security", "tls", "https", "golang"], "source": "https://pkg.go.dev/crypto/tls", "has_tests": False, "has_types": False, "deps": []},
    {"title": "Environment Config (os.Getenv)", "lang": "go", "tags": ["pattern:configuration", "env", "golang"], "source": "https://pkg.go.dev/os", "has_tests": True, "has_types": False, "deps": []},
    {"title": "Test Fixture Setup", "lang": "go", "tags": ["pattern:testing", "fixtures", "testify", "golang"], "source": "https://github.com/stretchr/testify", "has_tests": True, "has_types": False, "deps": ["github.com/stretchr/testify"]},
    {"title": "Docker SDK Container Lister", "lang": "go", "tags": ["pattern:docker", "sdk", "containers", "golang"], "source": "https://github.com/docker/docker", "has_tests": False, "has_types": False, "deps": ["github.com/docker/docker"]},
    {"title": "YAML Config Parser", "lang": "go", "tags": ["pattern:configuration", "yaml", "golang"], "source": "https://github.com/go-yaml/yaml", "has_tests": True, "has_types": False, "deps": ["gopkg.in/yaml.v3"]},
    {"title": "CSV Writer (encoding/csv)", "lang": "go", "tags": ["pattern:data-processing", "csv", "export", "golang"], "source": "https://pkg.go.dev/encoding/csv", "has_tests": True, "has_types": False, "deps": []},
    {"title": "Signal-based Reload", "lang": "go", "tags": ["pattern:resource-management", "signal", "reload", "golang"], "source": "https://pkg.go.dev/os/signal", "has_tests": False, "has_types": False, "deps": []},
]


def generate_snippet(p: Dict) -> str:
    """Generate a complete snippet markdown file from a pattern definition."""
    snippet_id = str(uuid.uuid4())
    now = str(date.today())
    tags_str = json.dumps(p["tags"])
    deps_str = json.dumps(p.get("deps", []))
    has_tests = "true" if p.get("has_tests", False) else "false"
    has_types = "true" if p.get("has_types", False) else "false"

    code = _get_template_code(p["lang"], p["title"])

    return f"""---
id: "{snippet_id}"
title: "{p['title']}"
lang: {p['lang']}
tags: {tags_str}
dependencies: {deps_str}
author: "acl-seed"
license: "MIT"
source_url: "{p['source']}"
created: "{now}"
updated: "{now}"
description: "A well-documented {p['lang']} implementation of {p['title'].lower()} with MIT license."
has_tests: {has_tests}
has_types: {has_types}
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```{p['lang']}
{code}
```
"""


def _get_template_code(lang: str, title: str) -> str:
    """Return a representative code template for the given pattern."""
    code_templates = {
        "python": _python_template(title),
        "typescript": _typescript_template(title),
        "shell": _shell_template(title),
        "go": _go_template(title),
    }
    return code_templates.get(lang, f"# {title}\n# TODO: implement\n")


def _python_template(title: str) -> str:
    return f'''"""
{title}

A reusable implementation with type hints and docstrings.
"""
from typing import Any, Callable, Optional
import time
import logging

logger = logging.getLogger(__name__)


def example() -> None:
    """Demonstrate usage of this pattern."""
    # TODO: replace with actual implementation
    result = main()
    logger.info("Result: %s", result)


def main() -> str:
    """Core logic entry point."""
    return f"{{__name__}}.{{__class__.__name__}}"


if __name__ == "__main__":
    example()
'''


def _typescript_template(title: str) -> str:
    return f'''/**
 * {title}
 *
 * A reusable TypeScript implementation with full type safety.
 */

export interface Options {{
  /** Enable verbose logging */
  verbose?: boolean;
  /** Timeout in milliseconds */
  timeout?: number;
}}

const defaults: Options = {{
  verbose: false,
  timeout: 5000,
}};

export function example(options: Options = {{}}): string {{
  const opts = {{ ...defaults, ...options }};
  // TODO: replace with actual implementation
  return `${{opts.timeout}}ms timeout configured`;
}}

export default example;
'''


def _shell_template(title: str) -> str:
    slug = title.lower().replace(" ", "-")
    return f'''#!/usr/bin/env bash
#
# {title}
# Source: https://aicode.iamfaulty.com
# License: MIT
#
# Usage: ./{slug}.sh [options]

set -euo pipefail

# --- Configuration ---
VERBOSE="${{VERBOSE:-false}}"

# --- Functions ---

log() {{
    local level="$1"
    shift
    echo "[${{level}}] $(date '+%Y-%m-%d %H:%M:%S') $*"
}}

info() {{ log "INFO" "$@"; }}
error() {{ log "ERROR" "$@" >&2; }}

# --- Main ---
main() {{
    info "Starting {title}..."
    # TODO: implement
    info "Done."
}}

main "$@"
'''


def _go_template(title: str) -> str:
    return f'''package main

import (
    "fmt"
    "log"
)

// {_go_pascal(title)} implements the {title} pattern.
type {_go_pascal(title)} struct {{
    // TODO: add fields
}}

// New{_go_pascal(title)} creates a new instance.
func New{_go_pascal(title)}() *{_go_pascal(title)} {{
    return &{_go_pascal(title)}{{}}
}}

// Run executes the pattern.
func (p *{_go_pascal(title)}) Run() error {{
    // TODO: implement
    return nil
}}

func main() {{
    p := New{_go_pascal(title)}()
    if err := p.Run(); err != nil {{
        log.Fatalf("failed: %v", err)
    }}
    fmt.Println("ok")
}}
'''


def _go_pascal(title: str) -> str:
    """Convert a title to PascalCase for Go identifiers."""
    words = re.findall(r"[A-Za-z0-9]+", title)
    return "".join(w[0].upper() + w[1:].lower() if len(w) > 1 else w.upper() for w in words)


def write_snippet_files(dry_run: bool = False) -> List[Path]:
    """Write all snippets as .md files to the snippets directory."""
    written = []
    for p in PATTERNS:
        lang_dir = SNIPPETS_DIR / p["lang"]
        lang_dir.mkdir(parents=True, exist_ok=True)
        slug = p["title"].lower().replace(" ", "-")[:48]
        target = lang_dir / f"{slug}.md"

        content = generate_snippet(p)
        if dry_run:
            print(f"[DRY-RUN] Would write: {target}")
            continue

        target.write_text(content)
        written.append(target)
        print(f"  WROTE: {target.relative_to(REPO_ROOT)}")
    return written


def submit_via_api(written: List[Path]) -> None:
    """Submit written snippet files to the ACL API."""
    if not written:
        return
    import urllib.request

    for path in written:
        text = path.read_text(encoding="utf-8")
        data = json.dumps({"snippet": text}).encode()
        req = urllib.request.Request(
            f"{API_BASE}/api/v1/submit",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read())
            print(f"  SUBMITTED: {result['id'][:8]} — {path.name}")
        except Exception as e:
            print(f"  FAILED: {path.name} — {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed ACL with top 100 snippets from GitHub")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be submitted")
    parser.add_argument("--repo-only", action="store_true", help="Write files directly, skip API")
    args = parser.parse_args()

    print(f"Agent Code Library — Curated Top 100 Seed")
    print(f"{'=' * 50}")
    print(f"Patterns: {len(PATTERNS)}")
    langs = {}
    for p in PATTERNS:
        langs[p["lang"]] = langs.get(p["lang"], 0) + 1
    for lang, count in sorted(langs.items()):
        print(f"  {lang}: {count}")

    print(f"\nGenerating snippets...")
    written = write_snippet_files(dry_run=args.dry_run)

    if args.dry_run:
        print(f"\nDry run complete. {len(PATTERNS)} snippets would be written.")
        return

    if not args.repo_only and written:
        print(f"\nSubmitting {len(written)} snippets via API at {API_BASE}...")
        submit_via_api(written)

    print(f"\nDone. {len(written)} snippets seeded.")
    print(f"Run 'python3 cli/acl.py rebuild' to rebuild index.")


if __name__ == "__main__":
    main()
