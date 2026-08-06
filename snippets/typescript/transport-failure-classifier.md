---
id: "c1a2b3d4-0004-4e5f-9a04-transport004"
title: "Transport Failure Classifier (Tag Class + Conservative Patterns)"
lang: typescript
tags: ["pattern:reliability", "errors", "classification", "rpc", "self-healing"]
dependencies: []
author: "peteedoo"
license: "MIT"
source_url: "https://github.com/cloudflare/computer/blob/main/packages/computer/src/transport-failure.ts"
created: "2026-08-05"
updated: "2026-08-05"
description: "Decide 'is the transport dead?' via a tag class for your own errors plus conservative message matching for third-party ones — walks the whole cause chain."
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
 * Transport Failure Classifier
 * Adapted from cloudflare/computer (MIT) — packages/computer/src/transport-failure.ts
 *
 * The problem: a client caches a connection handle per peer and clears
 * it when the handle's `closed` promise resolves. But a wedged peer or
 * half-broken session often surfaces failures through an RPC rejection
 * LONG BEFORE that promise fires. Without a classifier you keep
 * handing the same broken stub to the next caller.
 *
 * Two ways to flag a transport failure:
 *
 *   1. Throw a tagged error class from code you OWN (heartbeat
 *      onFailure, lease renewal, the client itself). Direct — no
 *      string matching.
 *   2. Pattern-match the message for known phrases that EXTERNAL
 *      libraries surface (session shutdown, socket close, port
 *      unreachable). Conservative by design.
 *
 * The documented tradeoff, worth copying into your own comments:
 *   false POSITIVES invalidate a still-good handle — cost: a reconnect.
 *   false NEGATIVES keep a dead stub around until the next signal.
 * When in doubt, classify. Reconnects are cheap; zombie stubs are not.
 *
 * The classifier walks the `cause` chain so wrappers like
 * "watermark sync failed: <inner>" still classify when the inner
 * error is a transport failure.
 */

/** Tag class — class identity lets the classifier match without string
 *  inspection, and lets callers wrap an underlying cause for
 *  observability without losing the classification. */
export class TransportError extends Error {
  override readonly name = "TransportError";
  constructor(message: string, options?: { cause?: unknown }) {
    super(message, options);
  }
}

/** Known third-party phrases — extend only with strings you have
 *  actually observed in the wild. Keep it conservative. */
const TRANSPORT_PHRASES: readonly string[] = [
  "session shut down",
  "websocket closed",
  "websocket error",
  "econnrefused",
  "econnreset",
  "socket hang up",
  "connection refused",
  "connection reset",
  "network unreachable",
  "port unreachable",
];

export function isTransportFailure(error: unknown): boolean {
  let current: unknown = error;
  const seen = new Set<unknown>(); // cause cycles are possible in the wild
  while (current !== undefined && current !== null && !seen.has(current)) {
    seen.add(current);
    if (current instanceof TransportError) return true;
    if (current instanceof Error) {
      const msg = current.message.toLowerCase();
      if (TRANSPORT_PHRASES.some((phrase) => msg.includes(phrase))) return true;
      current = current.cause; // walk the chain
      continue;
    }
    break;
  }
  return false;
}

/* ---- usage: invalidate cached handles on match ----
 *
 * async function rpcThroughHandle(peerId: string, call: () => Promise<unknown>) {
 *   const handle = this.cache.get(peerId);
 *   try {
 *     return await call();
 *   } catch (err) {
 *     if (isTransportFailure(err)) {
 *       this.cache.delete(peerId);   // don't hand the broken stub to the next caller
 *       handle?.close().catch(() => {});
 *     }
 *     throw err;
 *   }
 * }
 */
```
