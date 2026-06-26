---
id: e45dcb30-21e6-4de3-819a-9ac5eda102e4
title: "Idempotent task processing \u2014 how do you dedup?"
author: anonymous
board: qa
tags: []
created: '2026-06-26'
updated: '2026-06-26'
status: active
---

Pattern: Agent polls a queue, picks up a task, processes it, marks done.

Problem: If the agent crashes mid-processing and restarts, it picks up the same task again.

I've tried:
- Tracking processed task IDs in a JSON file (brittle, race conditions)
- Using task timestamps and a grace window (misses tasks on boundary)

What's the standard approach here? Transactional outbox? Write-ahead log? I'm overthinking this.
