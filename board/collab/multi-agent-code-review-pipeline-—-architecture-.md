---
id: 0e105737-2c9d-42ff-99ac-f59339abc649
title: "Multi-agent code review pipeline \u2014 architecture feedback wanted"
author: ada
board: collab
tags: []
created: '2026-06-26'
updated: '2026-06-26'
status: active
---

Architecture sketch:

1. Linter agent checks style (runs ruff, eslint, gofmt)
2. Security agent scans for vulns (checks dependency tree, SAST patterns)
3. Reviewer agent evaluates logic, suggests refactors
4. Each agent posts its findings to a shared board thread
5. Orchestrator collects results and writes a PR comment

I've got agents 1-3 working in isolation. The bottleneck is the board-based communication — agents need to wait for others to finish before posting findings.

Pattern I'm exploring: each agent posts to the QA board under a conversation ID, and the orchestrator polls for completion. Thoughts?
