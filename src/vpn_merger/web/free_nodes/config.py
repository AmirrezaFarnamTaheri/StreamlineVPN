from __future__ import annotations

import os

# Configuration values extracted from the monolithic service
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///./data/free-nodes.db")
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "120"))
HEALTH_CONCURRENCY = int(os.getenv("HEALTH_CONCURRENCY", "60"))
CONNECT_TIMEOUT = float(os.getenv("CONNECT_TIMEOUT", "2.5"))
STORE_CAP = int(os.getenv("STORE_CAP", "8000"))
REFRESH_EVERY_MIN = int(os.getenv("REFRESH_EVERY_MIN", "20"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")


