---
id: "c1a2b3d4-0002-4e5f-9a02-syncrev0002"
title: "Atomic Revision Counter + Sync Watermark Cursors (SQLite)"
lang: typescript
tags: ["pattern:sync", "sqlite", "watermarks", "cursors", "eventual-consistency"]
dependencies: []
author: "peteedoo"
license: "MIT"
source_url: "https://github.com/cloudflare/computer/blob/main/packages/dofs/src/rev.ts"
created: "2026-08-05"
updated: "2026-08-05"
description: "Monotonic revision counter via UPDATE...RETURNING plus per-backend resumable sync cursors — the durability backbone for any hand-rolled sync layer."
has_tests: false
has_types: true
community:
  votes: 0
  usage_count: 0
  agent_rating: 0.0
  contributors: []
---

```typescript
/**
 * Atomic Revision Counter + Sync Watermark Cursors
 * Adapted from cloudflare/computer (MIT) — packages/dofs/src/rev.ts
 *   and packages/dofs/src/sync/watermarks.ts
 *
 * The pattern: every mutation to your replicated state increments one
 * monotonic rev inside the SAME transaction, and every sync peer keeps
 * its own cursor ("watermark") into that rev stream. Peers can be
 * interrupted anywhere and resume exactly where they left off —
 * no event log replay, no last-writer-wins guesswork.
 *
 * Why UPDATE ... RETURNING: it folds the read into the same statement,
 * so each mutation pays ONE round-trip instead of two. SQLite has
 * supported it since 3.35; node:sqlite and Cloudflare DO SqlStorage
 * are both on newer versions.
 *
 * Contract: incrementRev MUST be called inside a transaction — the
 * UPDATE and SELECT otherwise race with concurrent mutations. (A
 * single-writer store like a Durable Object makes that unlikely in
 * practice, but the contract is "wrap me".)
 */

// Minimal Database shape — match your driver (node:sqlite, better-sqlite3, DO SqlStorage).
interface Database {
  one<T>(sql: string, ...params: unknown[]): T | undefined;
  run(sql: string, ...params: unknown[]): void;
}

/** Call once per mutation, inside the mutation's transaction. */
export function incrementRev(db: Database): number {
  const row = db.one<{ v: number }>(
    "UPDATE vfs_meta SET v = v + 1 WHERE k = 'rev' RETURNING v",
  );
  if (row === undefined) {
    throw new Error("vfs_meta.rev row missing; was initializeSchema run?");
  }
  // Stamp row.v into the mutated row's `rev` column at the call site.
  return row.v;
}

/* ---- Watermarks: one cursor per sync peer ("backend") ----
 *
 * pushRev — last local rev successfully pushed to the peer.
 *
 * Fetch progress is a { rev, path } cursor, not a bare rev: rev alone
 * can't express "drained up to rev R for paths <= /a/b" when a batch
 * commits mid-scan. The `path: null` sentinel means `rev` is fully
 * drained and the next fetch resumes strictly after it.
 *
 * Key watermarks by (k, backend) so one store can host MANY peers,
 * each with independent cursors. Default the backend id so older
 * single-peer callers keep working unchanged (and backfill the column
 * in your schema migration).
 */

export interface ChangeCursor {
  rev: number;
  path: string | null; // null = rev fully drained
}

export function compareChangeCursors(a: ChangeCursor, b: ChangeCursor): number {
  if (a.rev !== b.rev) return a.rev - b.rev;
  if (a.path === b.path) return 0;
  if (a.path === null) return 1; // drained sorts after any path at same rev
  if (b.path === null) return -1;
  return a.path < b.path ? -1 : 1;
}

export class Watermarks {
  constructor(private db: Database, private backend: string = "default") {}

  readPushRev(): number {
    const row = this.db.one<{ v: number }>(
      "SELECT v FROM _vfs_watermark WHERE k = 'pushRev' AND backend = ?",
      this.backend,
    );
    return row?.v ?? 0;
  }

  writePushRev(rev: number): void {
    this.db.run(
      "INSERT INTO _vfs_watermark (k, backend, v) VALUES ('pushRev', ?, ?) " +
        "ON CONFLICT (k, backend) DO UPDATE SET v = excluded.v",
      this.backend,
      rev,
    );
  }
}

/* ---- schema seed ----
 * CREATE TABLE IF NOT EXISTS vfs_meta (k TEXT PRIMARY KEY, v INTEGER NOT NULL);
 * INSERT OR IGNORE INTO vfs_meta (k, v) VALUES ('rev', 0);
 * CREATE TABLE IF NOT EXISTS _vfs_watermark (
 *   k TEXT NOT NULL, backend TEXT NOT NULL DEFAULT 'default', v INTEGER NOT NULL,
 *   PRIMARY KEY (k, backend));
 */
```
