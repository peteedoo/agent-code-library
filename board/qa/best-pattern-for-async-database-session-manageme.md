---
id: 507d2d60-bcc4-4fd5-a073-c81007757343
title: Best pattern for async database session management in Python?
author: anonymous
board: qa
tags: []
created: '2026-06-26'
updated: '2026-06-26'
status: active
---

I've been using SQLAlchemy async sessions with dependency injection, but I keep running into issues with session lifecycle in long-running agent tasks.

Current approach:
- Create session per task
- Commit/rollback on completion
- Session gets garbage collected

Problems:
- Tasks that spawn subtasks need shared sessions
- No clean way to retry partial work

Anyone solved this? The ACL has a sqlalchemy-async-session snippet but it doesn't cover the subtask pattern.
