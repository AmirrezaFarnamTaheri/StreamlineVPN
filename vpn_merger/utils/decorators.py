from __future__ import annotations

import functools
import time
from typing import Callable, Any


def timeit(func: Callable[..., Any]) -> Callable[..., Any]:  # pragma: no cover - utility
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            _ = time.time() - t0
    return wrapper

