---
id: "c9d0e1f2-a3b4-5678-cdef-789012345678"
title: "useDebounce React Hook"
lang: typescript
tags: [react, hook, debounce, frontend]
dependencies: [react]
author: peteedoo
created: 2024-05-12
updated: 2024-05-12
description: "React hook that debounces a value, useful for search inputs."
---

```typescript
import { useState, useEffect } from "react";

export function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);

  return debounced;
}
```
