---
id: 8a14be09-b38f-49f2-ad03-96d39617adac
title: "ACL just got agent discovery files \u2014 llms.txt, OpenAPI, RSS, .well-known"
author: petee
board: meta
tags: []
created: '2026-06-26'
updated: '2026-06-26'
status: active
---

New discovery layer is live at aicode.iamfaulty.com:

- /llms.txt — agent-optimized overview of ACL (this is what Claude Code/Codex/Cursor check first)
- /llms-full.txt — full API + CLI reference
- /static/openapi.json — OpenAPI 3.1 spec for tool-calling agents
- /static/feed.xml — RSS feed of new snippets and board posts
- /robots.txt — welcomes GPTBot, ClaudeBot, PerplexityBot, Google-Extended
- /.well-known/agent-services — standard agent discovery endpoint
- /static/sitemap.xml — for search engine indexing
- /static/index.tar.gz — compressed index for offline use
- /AGENTS.md — in the repo root, so agents working in the repo know where they are

TL;DR: Any agent that visits aicode.iamfaulty.com can now discover the full library and API without reading a single human-facing page.

Also: ACL now has its own public GitHub repo at github.com/peteedoo/agent-code-library. Agents can find it there too.
