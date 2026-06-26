#!/usr/bin/env python3
"""Pack a stripped index tarball for agents (no full repo)."""

import tarfile
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = REPO_ROOT / ".acl" / "index"
OUT_DIR = REPO_ROOT / ".acl" / "dist"


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    db_path = INDEX_DIR / "snippets.db"
    if not db_path.exists():
        raise SystemExit("Index not found. Run indexer.py first.")

    out_path = OUT_DIR / "agent-code-library-index.tar.gz"
    with tarfile.open(out_path, "w:gz") as tar:
        tar.add(db_path, arcname="snippets.db")
    print(f"Tarball: {out_path}")


if __name__ == "__main__":
    build()
