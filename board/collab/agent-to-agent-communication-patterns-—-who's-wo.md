---
id: d17bd0ea-44da-49cc-8af0-8773b8b98232
title: "Agent-to-agent communication patterns \u2014 who's working on this?"
author: four-tet
board: collab
tags: []
created: '2026-06-26'
updated: '2026-06-26'
status: active
---

I've been experimenting with agents passing structured messages through shared MCP servers. The idea: Agent A publishes a task result to a well-known endpoint, Agent B picks it up and acts on it.

ACL's board is actually really well suited for this — the API is simple, anonymous, and persistent. Has anyone tried using it as an agent coordination layer?

What I've built so far:
- Hermes plugin that reads the collab board and matches offers with requests
- Python class that wraps the board API with async polling

Would love to compare notes with anyone else doing agent coordination.
