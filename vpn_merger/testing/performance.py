from __future__ import annotations

"""Performance helpers for testing runs."""

import time
from contextlib import contextmanager


@contextmanager
def time_block():
    t0 = time.time()
    yield lambda: time.time() - t0

