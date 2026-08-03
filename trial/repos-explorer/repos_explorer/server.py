"""Tiny stdlib HTTP server: JSON API + static web frontend for the catalog.

    python -m repos_explorer serve --port 8100

Endpoints:
    GET /api/repos?q=&category=&language=   -> filtered repo list
    GET /api/repos/{id}                     -> single repo
    GET /api/categories                     -> category list
    GET /api/stats                          -> aggregate stats
    GET /healthz                            -> health check
    GET /                                    -> web UI (from web/)
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .catalog import Catalog, load_catalog

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_CATALOG: Catalog = load_catalog()


class Handler(BaseHTTPRequestHandler):
    server_version = "RepoExplorer/0.1"

    def log_message(self, *args) -> None:  # keep test/CLI output quiet
        pass

    def _send_json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            self._send_json({"error": "not found"}, 404)
            return
        ctype = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
        }.get(path.suffix, "application/octet-stream")
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        parsed = urlparse(self.path)
        path = parsed.path
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        if path == "/healthz":
            self._send_json({"status": "ok", "repos": len(_CATALOG)})
        elif path == "/api/repos":
            repos = _CATALOG.search(
                params.get("q", ""),
                category=params.get("category"),
                language=params.get("language"),
            )
            self._send_json({"count": len(repos), "repos": [r.to_dict() for r in repos]})
        elif path.startswith("/api/repos/"):
            repo = _CATALOG.get(path.rsplit("/", 1)[-1])
            if repo:
                self._send_json(repo.to_dict())
            else:
                self._send_json({"error": "repo not found"}, 404)
        elif path == "/api/categories":
            self._send_json({"categories": _CATALOG.categories, "languages": _CATALOG.languages})
        elif path == "/api/stats":
            self._send_json(_CATALOG.stats())
        elif path in ("/", "/index.html"):
            self._send_file(WEB_DIR / "index.html")
        else:
            candidate = (WEB_DIR / path.lstrip("/")).resolve()
            if WEB_DIR in candidate.parents and candidate.is_file():
                self._send_file(candidate)
            else:
                self._send_json({"error": "not found"}, 404)


def serve(host: str = "127.0.0.1", port: int = 8100) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"AI/ML Repo Explorer serving {len(_CATALOG)} repos on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        httpd.shutdown()
