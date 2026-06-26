---
id: "a7b8c9d0-e1f2-3456-abcd-567890123456"
title: "Fetch with Retry and Timeout"
lang: typescript
tags: [fetch, http, retry, timeout]
dependencies: []
author: peteedoo
created: 2024-05-12
updated: 2024-05-12
description: "TypeScript wrapper around fetch with configurable retries, backoff, and timeout."
---

```typescript
export async function fetchWithRetry(
  url: string,
  options: RequestInit & { timeout?: number; retries?: number; backoff?: number } = {},
): Promise<Response> {
  const { timeout = 5000, retries = 3, backoff = 300, ...fetchOpts } = options;

  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);

    try {
      const res = await fetch(url, { ...fetchOpts, signal: controller.signal });
      clearTimeout(timer);
      if (!res.ok && attempt < retries) {
        await sleep(backoff * 2 ** attempt);
        continue;
      }
      return res;
    } catch (err) {
      clearTimeout(timer);
      if (attempt === retries) throw err;
      await sleep(backoff * 2 ** attempt);
    }
  }
  throw new Error("unreachable");
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
```
