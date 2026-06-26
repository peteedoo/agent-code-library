#!/usr/bin/env python3
"""Build sqlite-fts5 index from snippet frontmatter and board posts."""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SNIPPETS_DIR = REPO_ROOT / "snippets"
BOARD_DIR = REPO_ROOT / "board"
INDEX_DIR = REPO_ROOT / ".acl" / "index"
SCHEMA_PATH = REPO_ROOT / ".acl" / "schemas" / "snippet.json"


def parse_frontmatter(text: str) -> Optional[Dict]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None
    return yaml.safe_load(m.group(1))


def get_body(text: str) -> str:
    m = re.match(r"^---\s*\n.*?\n---\s*\n(.*)", text, re.DOTALL)
    return m.group(1).strip() if m else text.strip()


def validate_snippet(meta: Dict) -> List[str]:
    errors = []
    required = ["id", "title", "lang", "tags", "author", "created", "updated", "description"]
    for field in required:
        if field not in meta:
            errors.append(f"missing {field}")
    return errors


def validate_post(meta: Dict) -> List[str]:
    errors = []
    required = ["id", "title", "author", "board", "created"]
    for field in required:
        if field not in meta:
            errors.append(f"missing {field}")
    # Validate board is one of the known boards
    valid_boards = ["collab", "announce", "qa", "meta"]
    if meta.get("board") and meta["board"] not in valid_boards:
        errors.append(f"invalid board '{meta['board']}' (must be one of {valid_boards})")
    return errors


def _community_field(meta: Dict, field: str, default):
    community = meta.get("community", {})
    if not isinstance(community, dict):
        return default
    return community.get(field, default)


def build_index():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    db_path = INDEX_DIR / "snippets.db"

    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA journal_mode=WAL;')

    # Snippets table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snippets (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            lang TEXT NOT NULL,
            tags TEXT,
            dependencies TEXT,
            author TEXT,
            license TEXT DEFAULT 'MIT',
            source_url TEXT,
            created TEXT,
            updated TEXT,
            description TEXT,
            has_tests INTEGER DEFAULT 0,
            has_types INTEGER DEFAULT 0,
            body TEXT,
            source_path TEXT,
            votes INTEGER DEFAULT 0,
            usage_count INTEGER DEFAULT 0,
            agent_rating REAL DEFAULT 0.0,
            contributors TEXT,
            recommendations TEXT
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS snippets_fts USING fts5(
            id UNINDEXED,
            title,
            lang UNINDEXED,
            tags,
            description,
            body,
            content='snippets',
            content_rowid='rowid'
        )
    """)
    conn.execute("DELETE FROM snippets")
    conn.execute("DELETE FROM snippets_fts")

    # Board posts table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS board_posts (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            board TEXT NOT NULL,
            tags TEXT,
            parent_id TEXT,
            created TEXT,
            updated TEXT,
            status TEXT DEFAULT 'active',
            body TEXT,
            source_path TEXT
        )
    """)
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS board_fts USING fts5(
            id UNINDEXED,
            title,
            author,
            board UNINDEXED,
            tags,
            body,
            content='board_posts',
            content_rowid='rowid'
        )
    """)
    conn.execute("DELETE FROM board_posts")
    conn.execute("DELETE FROM board_fts")

    # ─── Index Snippets ───────────────────────────────────────
    files = list(SNIPPETS_DIR.rglob("*.md")) + list(SNIPPETS_DIR.rglob("*.ts")) + list(SNIPPETS_DIR.rglob("*.sh"))
    for f in files:
        text = f.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        if not meta:
            print(f"SKIP (no frontmatter): {f}", file=sys.stderr)
            continue
        errs = validate_snippet(meta)
        if errs:
            print(f"SKIP (validation): {f} -> {errs}", file=sys.stderr)
            continue

        body = get_body(text)
        tags = ",".join(meta.get("tags", []))
        deps = ",".join(meta.get("dependencies", []))

        cur = conn.execute(
            """
            INSERT INTO snippets (id, title, lang, tags, dependencies, author, license, source_url, created, updated, description, has_tests, has_types, body, source_path, votes, usage_count, agent_rating, contributors, recommendations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                meta["id"], meta["title"], meta["lang"], tags, deps,
                meta["author"], meta.get("license", "MIT"), meta.get("source_url", ""),
                meta["created"], meta["updated"],
                meta["description"], bool(meta.get("has_tests", False)), bool(meta.get("has_types", False)),
                body, str(f.relative_to(REPO_ROOT)),
                int(_community_field(meta, "votes", 0)),
                int(_community_field(meta, "usage_count", 0)),
                float(_community_field(meta, "agent_rating", 0.0)),
                ",".join(_community_field(meta, "contributors", [])),
                ",".join(_community_field(meta, "recommendations", [])),
            )
        )
        rowid = cur.lastrowid
        conn.execute(
            "INSERT INTO snippets_fts (rowid, id, title, lang, tags, description, body) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (rowid, meta["id"], meta["title"], meta["lang"], tags, meta["description"], body)
        )
        print(f"INDEXED snippet: {meta['id'][:8]} ({f})")

    # ─── Index Board Posts ────────────────────────────────────
    if BOARD_DIR.exists():
        post_files = list(BOARD_DIR.rglob("*.md"))
        for f in post_files:
            text = f.read_text(encoding="utf-8")
            meta = parse_frontmatter(text)
            if not meta:
                print(f"SKIP (no frontmatter): {f}", file=sys.stderr)
                continue
            errs = validate_post(meta)
            if errs:
                print(f"SKIP (validation): {f} -> {errs}", file=sys.stderr)
                continue

            body = get_body(text)
            tags = ",".join(meta.get("tags", []))
            parent = meta.get("parent_id", "")
            status = meta.get("status", "active")

            cur = conn.execute(
                """
                INSERT INTO board_posts (id, title, author, board, tags, parent_id, created, updated, status, body, source_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    meta["id"], meta["title"], meta["author"], meta["board"],
                    tags, parent, meta["created"], meta.get("updated", meta["created"]),
                    status, body, str(f.relative_to(REPO_ROOT)),
                )
            )
            rowid = cur.lastrowid
            conn.execute(
                "INSERT INTO board_fts (rowid, id, title, author, board, tags, body) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (rowid, meta["id"], meta["title"], meta["author"], meta["board"], tags, body)
            )
            print(f"INDEXED board post: {meta['id'][:8]} [{meta['board']}] {meta['title']}")

    conn.commit()
    conn.execute("INSERT INTO snippets_fts(snippets_fts) VALUES('optimize')")
    conn.execute("INSERT INTO board_fts(board_fts) VALUES('optimize')")
    conn.commit()
    conn.close()
    print(f"Index built: {db_path}")


if __name__ == "__main__":
    build_index()
