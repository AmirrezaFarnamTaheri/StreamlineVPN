from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS, REFRESH_EVERY_MIN
from .db import AsyncSessionLocal, Base, engine
from .metrics import Instrumentator, QUALITY_SCORE
from .rate_limit import middleware as rate_middleware
from .routes import router

log = logging.getLogger("free-nodes")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("./data", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    scheduler = AsyncIOScheduler()

    async def scheduled_refresh():
        try:
            log.info("scheduled refresh: start")
            # lazy import to avoid circular
            from .routes import refresh_sources

            await refresh_sources(healthcheck=True)
            log.info("scheduled refresh: done")
        except Exception as e:
            log.exception(f"scheduled refresh failed: {e}")

    async def nightly_prune():
        from datetime import datetime, timedelta
        from sqlalchemy import select
        from .db import NodeModel

        try:
            async with AsyncSessionLocal() as sess:
                rows = (await sess.execute(select(NodeModel))).scalars().all()
                cutoff = datetime.utcnow() - timedelta(days=7)
                for m in rows:
                    if (not m.healthy) and (not m.last_checked or m.last_checked < cutoff):
                        await sess.delete(m)
                await sess.commit()
        except Exception as e:
            log.exception(f"nightly prune failed: {e}")

    scheduler.add_job(scheduled_refresh, "interval", minutes=REFRESH_EVERY_MIN, jitter=60, id="refresh")
    scheduler.add_job(nightly_prune, "cron", hour=3, minute=15, id="prune")
    scheduler.start()

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    app = FastAPI(title="Free Nodes Aggregator API", version="2.0.0", lifespan=lifespan)
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers={"/metrics"},
        inprogress_name="http_requests_in_progress",
        inprogress_labels=True,
    ).instrument(app).expose(app, include_in_schema=False)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in CORS_ORIGINS.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(rate_middleware)
    app.include_router(router)
    return app


app = create_app()


