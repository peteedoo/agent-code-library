---
id: "f6a7b8c9-d0e1-2345-fabc-456789012345"
title: "Structured JSON Lines Logger"
lang: python
tags: [logging, json, observability]
dependencies: []
author: peteedoo
created: 2024-05-12
updated: 2024-05-12
description: "Python logging handler that emits JSON Lines for easy ingestion by log aggregators."
---

```python
import json
import logging
from datetime import datetime, timezone

class JSONLHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord):
        log_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            log_entry["exc"] = self.formatException(record.exc_info)
        self.stream.write(json.dumps(log_entry, default=str) + "\n")
        self.flush()

# Usage
logger = logging.getLogger("svc")
logger.handlers = [JSONLHandler()]
logger.setLevel(logging.INFO)
```
