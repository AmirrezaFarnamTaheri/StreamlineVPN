from __future__ import annotations

import time
from dataclasses import dataclass

from fastapi import HTTPException, Request

from .config import RATE_LIMIT_RPM


@dataclass
class RateBucket:
    count: int
    reset_at: float


RATE: dict[str, RateBucket] = {}


def rate_limit_ok(ip: str) -> bool:
    b = RATE.get(ip)
    now = time.time()
    if not b or now >= b.reset_at:
        RATE[ip] = RateBucket(count=0, reset_at=now + 60)
        return True
    return b.count < RATE_LIMIT_RPM


async def middleware(request: Request, call_next):
    ip = request.client.host if request.client else "0.0.0.0"
    if not rate_limit_ok(ip):
        raise HTTPException(429, detail="Too many requests; slow down")
    RATE[ip].count += 1
    return await call_next(request)


