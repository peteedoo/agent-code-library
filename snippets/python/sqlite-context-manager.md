---
id: "b2c3d4e5-f6a7-8901-bcde-f12345678901"
title: "SQLite Connection Context Manager"
lang: python
tags: [sqlite, database, context-manager]
dependencies: []
author: peteedoo
created: 2024-05-12
updated: 2024-05-12
description: "Safe SQLite connection/transaction context manager with row factory."
---

```python
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

@contextmanager
def sqlite_conn(db_path: str, row_factory=sqlite3.Row) -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection with optional row factory. Commits on success, rolls back on exception."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = row_factory
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```
