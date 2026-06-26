---
id: "c3d4e5f6-a7b8-9012-cdef-123456789012"
title: "Dataclass Field Validation with Post-Init"
lang: python
tags: [dataclass, validation, pydantic-alternative]
dependencies: []
author: peteedoo
created: 2024-05-12
updated: 2024-05-12
description: "Lightweight dataclass validation using __post_init__ without pulling in Pydantic."
---

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Load:
    pro_number: str
    weight_lbs: int
    carrier: str
    stops: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.pro_number or len(self.pro_number) < 3:
            raise ValueError("pro_number must be at least 3 characters")
        if self.weight_lbs <= 0:
            raise ValueError("weight_lbs must be positive")
        if not self.stops:
            raise ValueError("at least one stop required")
```
