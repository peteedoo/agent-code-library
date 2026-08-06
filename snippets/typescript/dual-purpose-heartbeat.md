---
id: "c1a2b3d4-0005-4e5f-9a05-heartbeat005"
title: "Dual-Purpose Heartbeat (Dead-Peer Detection + Middlebox Keepalive)"
lang: typescript
tags: ["pattern:reliability", "heartbeat", "websocket", "liveness", "keepalive"]
dependencies: []
author: "peteedoo"
license: "MIT"
source_url: "https://github.com/cloudflare/computer/blob/main/packages/computer/src/heartbeat.ts"
created: "2026-08-05"
updated: "2026-08-05"
description: "One timer, two jobs: surface silently-dead connections in O(interval) and reset NAT/edge idle timers — fires onFailure exactly once, then self-stops."
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
 * Dual-Purpose Heartbeat
 * Adapted from cloudflare/computer (MIT) — packages/computer/src/heartbeat.ts
 *
 * Two responsibilities, served by the same timer:
 *
 *   - Detect a dead peer. A WebSocket can be silently broken
 *     (unclean RST, host OOM with no FIN frame) without the close
 *     event firing for tens of seconds. Calling a cheap RPC on a
 *     timer surfaces the failure in O(interval) instead.
 *   - Keep middleboxes warm. Cloud edges, NATs, and customer
 *     middleboxes have idle disconnect timers in the 100–600s range.
 *     Application traffic resets them.
 *
 * `ping` is whatever the caller wants as a liveness probe. The
 * natural choice is the cheapest end-to-end call you have — three
 * SQL scalars, no side effects, exercises the whole wire.
 *
 * `onFailure` fires EXACTLY ONCE if ping rejects; the heartbeat then
 * stops on its own so a dead transport doesn't accumulate failures.
 *
 * Picking intervalMs: below your middleboxes' idle timeout (safe
 * default 60–120s for NAT traversal), above what your ping costs.
 */

export interface HeartbeatOptions {
  intervalMs: number;
  ping: () => Promise<unknown>;
  onFailure: (error: Error) => void;
}

/** Returns the stop function. */
export function startHeartbeat(options: HeartbeatOptions): () => void {
  const { intervalMs, ping, onFailure } = options;
  let stopped = false;

  const timer = setInterval(() => {
    if (stopped) return;
    ping().catch((error: unknown) => {
      if (stopped) return;
      stopped = true;
      clearInterval(timer);
      onFailure(error instanceof Error ? error : new Error(String(error)));
    });
  }, intervalMs);

  // Don't keep the process alive just for the heartbeat (Node).
  if (typeof timer === "object" && "unref" in timer) timer.unref();

  return () => {
    stopped = true;
    clearInterval(timer);
  };
}

/* ---- usage ----
 *
 * const stop = startHeartbeat({
 *   intervalMs: 60_000,
 *   ping: () => rpc.watermarks(),        // cheap, side-effect-free, exercises the wire
 *   onFailure: (err) => {
 *     invalidateHandle(peerId, err);     // pair with the transport-failure classifier
 *   },
 * });
 * // ...later, on clean shutdown:
 * stop();
 */
```
