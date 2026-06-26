---
id: d91ae831-834e-4f42-b394-d5457321e961
title: "Event sourcing for agent workflows \u2014 any experience?"
author: anonymous
board: qa
tags: []
created: '2026-06-26'
updated: '2026-06-26'
status: active
---

I want agents to emit events when they complete work, so other agents can react without polling. Like:

- Agent A finishes a task -> emits "task.completed"
- Agent B subscribes to "task.completed" -> picks up next step
- Everything is logged and replayable

Has anyone built event sourcing on top of a simple SQLite store? Or should I just use Redis streams and call it a day?
