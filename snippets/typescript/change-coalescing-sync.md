---
id: "c1a2b3d4-0003-4e5f-9a03-coalesce0003"
title: "Per-Path Change Coalescing for Sync Streams"
lang: typescript
tags: ["pattern:sync", "coalescing", "tombstones", "streaming", "generators"]
dependencies: []
author: "peteedoo"
license: "MIT"
source_url: "https://github.com/cloudflare/computer/blob/main/packages/dofs/src/sync/coalesce.ts"
created: "2026-08-05"
updated: "2026-08-05"
description: "Collapse N mutations of the same path between watermarks into one latest-wins entry — tombstone loses to recreate — streamed, not buffered."
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
 * Per-Path Change Coalescing
 * Adapted from cloudflare/computer (MIT) — packages/dofs/src/sync/coalesce.ts
 *
 * The problem: between a peer's last watermark and now, the same path
 * may have been written five times, or deleted and recreated. Sending
 * every intermediate state wastes the wire and can resurrect wrong
 * orderings on the far side.
 *
 * The rules:
 *  - Latest state wins. Five rewrites between watermarks → one entry.
 *  - Tombstoned paths get a delete entry UNLESS they were recreated —
 *    then the live entry wins.
 *  - Emit in ascending rev order. Consumers rely on this to advance
 *    their cursor per committed batch: if entry N has rev R, every
 *    already-emitted entry has rev <= R, so checkpointing at R is safe.
 *  - STREAM, don't buffer: the coalesce step holds at most one slot
 *    per dirty path in memory (keyed by path), the same bound the
 *    underlying scans already pay.
 *  - Support an ignore list: path-segment patterns dropped before
 *    yield — the wire never carries entries under an ignored segment.
 */

export interface ChangeEntry {
  rev: number;          // rev of the LATEST mutation to this path
  path: string;
  kind: "upsert" | "delete";
}

interface RawChange {
  rev: number;
  path: string;
  deleted: boolean;
}

/** Segment matcher, e.g. ["node_modules", ".git"] drops anything under those segments. */
export function isIgnored(path: string, segments: string[]): boolean {
  const parts = path.split("/").filter(Boolean);
  return segments.some((seg) => parts.includes(seg));
}

/**
 * Coalesce a raw change scan into one entry per path.
 * `raw` must be iterable in ascending rev order (e.g. FROM vfs_changes
 * WHERE rev > ? ORDER BY rev ASC).
 */
export async function* coalesceChanges(
  raw: AsyncIterable<RawChange>,
  options: { ignore?: string[] } = {},
): AsyncIterable<ChangeEntry> {
  const ignore = options.ignore ?? [];
  // One slot per dirty path — the whole memory bound of the algorithm.
  const latest = new Map<string, RawChange>();

  for await (const change of raw) {
    if (isIgnored(change.path, ignore)) continue;
    latest.set(change.path, change); // latest wins, tombstone-or-not
  }

  // Recreated paths: a delete followed by a write collapses to the
  // live upsert because the final RawChange for the path is the write.
  const entries = [...latest.values()]
    .sort((a, b) => a.rev - b.rev) // ascending rev for safe cursor checkpoints
    .map<ChangeEntry>((c) => ({
      rev: c.rev,
      path: c.path,
      kind: c.deleted ? "delete" : "upsert",
    }));

  for (const entry of entries) yield entry;
}

/* ---- usage ----
 *
 * const raw = db.iterate<RawChange>(
 *   "SELECT rev, path, deleted FROM vfs_changes WHERE rev > ? ORDER BY rev ASC",
 *   peerWatermark,
 * );
 * for await (const entry of coalesceChanges(raw, { ignore: ["node_modules", ".git"] })) {
 *   await sendToPeer(entry);
 *   checkpoint(Math.max(checkpoint(), entry.rev)); // safe: ascending order
 * }
 */
```
