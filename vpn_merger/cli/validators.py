from __future__ import annotations


def positive_int(value: str) -> int:
    try:
        n = int(value)
    except Exception as e:  # pragma: no cover
        raise ValueError("Not an integer") from e
    if n < 0:
        raise ValueError("Must be >= 0")
    return n

