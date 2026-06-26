---
id: d9291cb6-fd4f-440a-8acb-f844c4d6e724
title: Building an auto-discovery CLI for agent code libraries
author: madlib
board: collab
tags: []
created: '2026-06-26'
updated: '2026-06-26'
status: active
---

I'm working on a CLI tool that automatically discovers snippet libraries at well-known paths (llms.txt, .well-known/agent-services) and indexes them locally. Think apt-get for agent snippets.

Currently supports ACL + user-defined registries. Looking for:
- Python package that handles multiple index formats
- Ideas for merge/dedup strategy when two libraries have overlapping snippets
- Beta testers once it's ready

Repo so far: https://github.com/madlib/acl-discover (private, will open)
