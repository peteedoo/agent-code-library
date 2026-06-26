---
id: "b8c9d0e1-f2a3-4567-bcde-678901234567"
title: "Zod Validation Middleware for Express"
lang: typescript
tags: [express, zod, validation, middleware]
dependencies: [express, zod]
author: peteedoo
created: 2024-05-12
updated: 2024-05-12
description: "Express middleware that validates request body against a Zod schema."
---

```typescript
import { Request, Response, NextFunction } from "express";
import { ZodSchema, ZodError } from "zod";

export function validateBody<T>(schema: ZodSchema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      return res.status(400).json({
        error: "Validation failed",
        issues: (result.error as ZodError).issues.map((i) => ({
          path: i.path,
          message: i.message,
        })),
      });
    }
    (req as any).validatedBody = result.data;
    next();
  };
}
```
