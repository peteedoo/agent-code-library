---
id: "d0e1f2a3-b4c5-6789-defa-890123456789"
title: "Docker System Prune with Exclusions"
lang: shell
tags: [docker, cleanup, maintenance]
dependencies: [docker]
author: peteedoo
created: 2024-05-12
updated: 2024-05-12
description: "Prune Docker resources while protecting named containers and volumes."
---

```bash
#!/usr/bin/env bash
set -euo pipefail

PROTECTED_CONTAINERS=("gitea" "jellyfin" "npm" "portainer")
PROTECTED_VOLUMES=("gitea_data" "jellyfin_config")

# Stop only unprotected containers
for c in $(docker ps -q); do
  name=$(docker inspect --format='{{.Name}}' "$c" | sed 's/\///')
  if [[ ! " ${PROTECTED_CONTAINERS[*]} " =~ ${name} ]]; then
    docker stop "$c" || true
  fi
done

# Prune
docker system prune -f --volumes

# Remove dangling volumes except protected
for v in $(docker volume ls -q -f dangling=true); do
  if [[ ! " ${PROTECTED_VOLUMES[*]} " =~ ${v} ]]; then
    docker volume rm "$v" || true
  fi
done

echo "Cleanup complete."
```
