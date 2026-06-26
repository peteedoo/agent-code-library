---
id: "e5f6a7b8-c9d0-1234-efab-345678901234"
title: "FastAPI Health Check Endpoint"
lang: python
tags: [fastapi, health, monitoring, http]
dependencies: [fastapi]
author: peteedoo
created: 2024-05-12
updated: 2024-05-12
description: "Standardized /healthz endpoint for FastAPI services with dependency checks."
---

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Callable

app = FastAPI()

class HealthResponse(BaseModel):
    status: str
    checks: Dict[str, str]

health_checks: Dict[str, Callable[[], bool]] = {}

@app.get("/healthz", response_model=HealthResponse)
async def healthz():
    checks = {name: "pass" if check() else "fail" for name, check in health_checks.items()}
    if any(v == "fail" for v in checks.values()):
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "checks": checks})
    return HealthResponse(status="healthy", checks=checks)

def register_health_check(name: str, check: Callable[[], bool]):
    health_checks[name] = check
```