---
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
title: Exponential Backoff Retry Decorator
lang: python
tags:
- retry
- decorator
- http
- resilience
dependencies: []
author: peteedoo
created: 2024-05-12
updated: 2024-05-12
description: Decorator that retries a function with exponential backoff and optional
  jitter.
community:
  votes: 1
---

```python
import time
import random
from functools import wraps
from typing import Callable, Tuple, Type

def retry(
    max_attempts: int = 3,
    backoff_base: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    jitter: bool = True,
):
    """Retry decorator with exponential backoff."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        raise
                    delay = min(backoff_base * (2 ** (attempt - 1)), max_delay)
                    if jitter:
                        delay *= random.uniform(0.5, 1.5)
                    time.sleep(delay)
        return wrapper
    return decorator
```
