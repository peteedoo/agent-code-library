#!/usr/bin/env python3
"""Pack a stripped index tarball for agents (no full repo)."""

import shutil
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = REPO_ROOT / ".acl" / "index"
OUT_DIR = REPO_ROOT / ".acl" / "dist"
WWW_DIR = REPO_ROOT / "www"


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    db_path = INDEX_DIR / "snippets.db"
    if not db_path.exists():
        raise SystemExit("Index not found. Run indexer.py first.")

    out_path = OUT_DIR / "agent-code-library-index.tar.gz"
    with tarfile.open(out_path, "w:gz") as tar:
        tar.add(db_path, arcname="snippets.db")
        catalog = WWW_DIR / "catalog.json"
        if catalog.exists():
            tar.add(catalog, arcname="catalog.json")
    catalog = WWW_DIR / "catalog.json"
    if catalog.exists():
        shutil.copy2(catalog, OUT_DIR / "catalog.json")
    print(f"Tarball: {out_path}")


if __name__ == "__main__":
    build()
