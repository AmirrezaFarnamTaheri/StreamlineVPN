"""
L3 Database Cache (SQLite)
=========================

Lightweight SQLite-backed key-value cache for fallback persistence.
Values are stored as text (typically JSON strings) with an expiry timestamp.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Optional
import asyncio


class L3DatabaseCache:
    """A minimal async-friendly SQLite-backed cache.

    Notes:
        - Values are stored as TEXT; callers typically pass JSON strings.
        - TTL is recorded as an epoch seconds expiry; expired entries are
          removed on access.
    """

    def __init__(self, db_path: str | Path = "vpn_configs.db") -> None:
        self.db_path = str(db_path)
        # Ensure DB initialized synchronously at construction time
        self._ensure_db()

    def _ensure_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON cache(expires_at)"
            )
            conn.commit()

    async def get(self, key: str) -> Optional[str]:
        now = time.time()

        def _get() -> Optional[str]:
            with sqlite3.connect(self.db_path) as conn:
                # delete expired rows first (best-effort)
                conn.execute("DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?", (now,))
                cur = conn.execute("SELECT value, expires_at FROM cache WHERE key = ?", (key,))
                row = cur.fetchone()
                if not row:
                    return None
                value, expires_at = row
                if expires_at is not None and expires_at < now:
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    conn.commit()
                    return None
                return value

        return await asyncio.to_thread(_get)

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        expires_at = None if ttl is None else time.time() + max(int(ttl), 0)

        def _set() -> bool:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO cache(key, value, expires_at) VALUES(?,?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value, expires_at=excluded.expires_at",
                    (key, value, expires_at),
                )
                conn.commit()
                return True

        return await asyncio.to_thread(_set)

    async def delete(self, key: str) -> bool:
        def _delete() -> bool:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                return cur.rowcount > 0

        return await asyncio.to_thread(_delete)

    async def clear(self) -> None:
        def _clear() -> None:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache")
                conn.commit()

        await asyncio.to_thread(_clear)

