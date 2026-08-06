---
id: "c1a2b3d4-0001-4e5f-9a01-0bserve00001"
title: "Span-Shaped Instrumentation Seam (Observer Hook)"
lang: typescript
tags: ["pattern:observability", "tracing", "spans", "instrumentation", "agents"]
dependencies: []
author: "peteedoo"
license: "MIT"
source_url: "https://github.com/cloudflare/computer/blob/main/packages/computer/src/observe.ts"
created: "2026-08-05"
updated: "2026-08-05"
description: "Instrument agent tool calls as nestable spans with a no-op default adapter — every action becomes traceable without coupling to a tracing backend."
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
 * Span-Shaped Instrumentation Seam
 * Adapted from cloudflare/computer (MIT) — packages/computer/src/observe.ts
 *
 * Why this shape and not a passive event stream
 * ---------------------------------------------
 * Some runtimes (Cloudflare Workers' ctx.tracing, many sandboxed
 * environments) expose user-defined spans through
 * `enterSpan(name, callback)` ONLY. The callback owns both ends of
 * the span; there is no way to start a span and end it from a
 * different stack. To stay compatible with that surface, hand the
 * adapter a callback to wrap rather than emitting separate
 * start/end events.
 *
 * An OpenTelemetry adapter is a strict superset: it can express
 * everything this minimal adapter can. A no-op observer (the
 * default) trivially supports both — and costs nothing when
 * observability is off.
 *
 * Design rules worth keeping:
 *  - One span per documented operation, named "<domain>.<op>"
 *    (e.g. "agent.tool.shell", "agent.memory.write").
 *  - Attribute values restricted to boolean | number | string —
 *    matches the Cloudflare Span.setAttribute signature; richer
 *    adapters can widen on their own side.
 *  - Keep span names under 64 bytes so strict runtimes accept
 *    them without truncation.
 *  - If the wrapped work throws/rejects, record the error on the
 *    span and rethrow — instrumentation must never swallow.
 */

export type SpanAttributeValue = boolean | number | string;

export interface Span {
  setAttribute(name: string, value: SpanAttributeValue): void;
  recordError(error: unknown): void;
}

export interface Observer {
  /** Wrap `work` in a span. The adapter owns span start AND end. */
  wrap<T>(name: string, attributes: Record<string, SpanAttributeValue>, work: (span: Span) => T): T;
}

/** Default: zero-cost pass-through. Observability off == this. */
export const noopObserver: Observer = {
  wrap<T>(_name: string, _attrs: Record<string, SpanAttributeValue>, work: (span: Span) => T): T {
    return work({ setAttribute() {}, recordError() {} });
  },
};

/* ---- example: instrumenting an agent's tool dispatch ---- */

export class ToolDispatcher {
  constructor(private observer: Observer = noopObserver) {}

  dispatch(toolName: string, args: Record<string, unknown>): Promise<unknown> {
    return this.observer.wrap(
      `agent.tool.${toolName}`.slice(0, 64),           // name budget: 64 bytes
      { "tool.name": toolName, "tool.arg_count": Object.keys(args).length },
      async (span) => {
        try {
          const result = await this.execute(toolName, args);
          span.setAttribute("tool.ok", true);
          return result;
        } catch (err) {
          span.recordError(err);                        // record, then rethrow
          span.setAttribute("tool.ok", false);
          throw err;
        }
      },
    );
  }

  private async execute(tool: string, args: Record<string, unknown>): Promise<unknown> {
    void tool; void args;
    throw new Error("implement me");
  }
}

/* ---- example: OpenTelemetry adapter (superset, optional dep) ----
 *
 * import { trace } from "@opentelemetry/api";
 * export const otelObserver: Observer = {
 *   wrap(name, attrs, work) {
 *     return trace.getTracer("agent").startActiveSpan(name, (otelSpan) => {
 *       for (const [k, v] of Object.entries(attrs)) otelSpan.setAttribute(k, v);
 *       try {
 *         return work({
 *           setAttribute: (k, v) => otelSpan.setAttribute(k, v),
 *           recordError: (e) => otelSpan.recordException(e as Error),
 *         });
 *       } finally { otelSpan.end(); }
 *     });
 *   },
 * };
 */
```
