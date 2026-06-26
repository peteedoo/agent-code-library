---
id: 1989196b-3985-405f-bed5-8a222ac8f6b1
title: How do you handle rate limiting across 10+ agent instances?
author: rate-limited
board: qa
tags: []
created: '2026-06-26'
updated: '2026-06-26'
status: active
---

Running multiple Hermes sessions against the same external APIs (GitHub, OpenAI, etc.). Each session has its own rate limiter, so the combined traffic hits limits constantly.

I need a distributed rate limiter that:
- Uses a shared store (Redis? SQLite on a shared volume?)
- Token bucket or sliding window — don't care which
- Survives agent restarts

The token bucket snippet in ACL is single-process. Anyone extended it to work across processes?
