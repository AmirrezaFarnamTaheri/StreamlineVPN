from __future__ import annotations

"""Connection testing facade."""

from typing import Optional


async def quick_ping(host: str, port: int, timeout: float = 1.0) -> Optional[float]:
    try:
        import asyncio
        import time

        start = time.time()
        reader, writer = await asyncio.open_connection(host, port)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return time.time() - start
    except Exception:
        return None

