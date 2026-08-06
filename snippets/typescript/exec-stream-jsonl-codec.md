---
id: "c1a2b3d4-0006-4e5f-9a06-execwire0006"
title: "Streaming Exec over JSONL Wire Frames"
lang: typescript
tags: ["pattern:rpc", "streaming", "jsonl", "subprocess", "codec"]
dependencies: []
author: "peteedoo"
license: "MIT"
source_url: "https://github.com/cloudflare/computer/blob/main/packages/computer/src/exec-wire.ts"
created: "2026-08-05"
updated: "2026-08-05"
description: "Project a faithful stdout/stderr/exit event stream across a byte-only RPC boundary using newline-delimited JSON frames with base64 for binary chunks."
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
 * Streaming Exec over JSONL Wire Frames
 * Adapted from cloudflare/computer (MIT) — packages/computer/src/exec-wire.ts
 *
 * The problem: your RPC layer carries byte streams with flow control
 * but NOT arbitrary object streams. To project a faithful streaming
 * exec (stdout/stderr chunks as they arrive, then exit) across that
 * boundary, frame the event stream as JSONL bytes on the producer
 * side and parse back into events on the consumer side.
 *
 * Wire shape: one JSON object per line, each the encoding of one event:
 *
 *   {"id","seq","name":"stdout","enc":"utf8","value":"..."}   string chunk
 *   {"id","seq","name":"stdout","enc":"b64","value":"..."}    byte chunk
 *   {"id","seq","name":"exit","value":0}                      exit code
 *
 * Design details worth keeping:
 *  - Bytes are base64'd so the frame stays valid JSON regardless of
 *    the chunk's contents.
 *  - Text is carried as a JSON string, which already escapes newlines
 *    and quotes — a chunk containing newlines CANNOT be confused with
 *    the line delimiter.
 *  - `seq` is per-exec monotonic so the consumer can detect drops.
 *  - This costs one serialization pass per chunk. That is the price
 *    of one faithful interface on both sides of the wire — pay it.
 */

export type ExecEvent =
  | { id: string; seq: number; name: "stdout" | "stderr"; enc: "utf8"; value: string }
  | { id: string; seq: number; name: "stdout" | "stderr"; enc: "b64"; value: string }
  | { id: string; seq: number; name: "exit"; value: number };

/* ---- encoder (producer side): events -> JSONL byte stream ---- */

export function encodeExecEvents(events: AsyncIterable<ExecEvent>): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream<Uint8Array>({
    async start(controller) {
      try {
        for await (const event of events) {
          controller.enqueue(encoder.encode(JSON.stringify(event) + "\n"));
        }
        controller.close();
      } catch (err) {
        controller.error(err);
      }
    },
  });
}

/** Convenience: raw bytes -> b64 chunk event. */
export function byteChunk(id: string, seq: number, name: "stdout" | "stderr", bytes: Uint8Array): ExecEvent {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return { id, seq, name, enc: "b64", value: btoa(bin) };
}

/* ---- decoder (consumer side): JSONL bytes -> events ----
 *
 * Buffers partial lines across chunk boundaries — a TCP/RPC chunk is
 * NOT guaranteed to align with frame boundaries. This is the bug most
 * hand-rolled JSONL parsers ship with.
 */
export async function* decodeExecEvents(stream: ReadableStream<Uint8Array>): AsyncIterable<ExecEvent> {
  const decoder = new TextDecoder();
  const reader = stream.getReader();
  let buffer = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let nl: number;
      while ((nl = buffer.indexOf("\n")) >= 0) {
        const line = buffer.slice(0, nl);
        buffer = buffer.slice(nl + 1);
        if (line.length > 0) yield JSON.parse(line) as ExecEvent;
      }
    }
    buffer += decoder.decode(); // flush
    if (buffer.trim().length > 0) yield JSON.parse(buffer) as ExecEvent;
  } finally {
    reader.releaseLock();
  }
}
```
