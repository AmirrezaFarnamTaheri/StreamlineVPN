"""
FastAPI app exposing the Strawberry GraphQL schema with subscriptions.
Run via uvicorn in parallel to the aiohttp server.
"""

from __future__ import annotations

import os
import time

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from strawberry.fastapi import GraphQLRouter

from ...monitoring.observability import get_meter_if_any
from .schema import schema


def create_graphql_app() -> FastAPI:
    app = FastAPI(title="VPN Merger GraphQL", version="1.0.0")
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    # Simple API token + rate limit middleware
    max_per_minute = int(
        os.getenv("GQL_RATE_LIMIT_PER_MINUTE", os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    )
    bucket = {}

    @app.middleware("http")
    async def auth_and_rate_limit(request: Request, call_next):
        # Rate limit
        ip = request.headers.get(
            "X-Forwarded-For", request.client.host if request.client else "unknown"
        )
        now = time.time()
        window = int(now // 60)
        info = bucket.get(ip)
        if not info or info["w"] != window:
            bucket[ip] = {"w": window, "c": 1}
        elif info["c"] >= max_per_minute:
            return fastapi_json({"error": "rate limit"}, 429)
        else:
            info["c"] += 1

        # Auth
        expected = os.getenv("API_TOKEN")
        if expected:
            token = request.headers.get("X-API-Token") or request.query_params.get("api_token")
            if token != expected:
                return fastapi_json({"error": "unauthorized"}, 401)

        # Metrics (OTEL if enabled)
        meter = get_meter_if_any()
        if meter:
            try:
                # lazy create counter once
                if not hasattr(app.state, "gql_counter"):
                    app.state.gql_counter = meter.create_counter(
                        name="graphql_requests_total",
                        unit="1",
                        description="GraphQL requests",
                    )
                app.state.gql_counter.add(1, {"path": request.url.path or "/graphql"})
            except Exception:
                pass

        return await call_next(request)

    # Prometheus metrics bridge
    registry = CollectorRegistry()
    gql_counter = Counter("graphql_requests_total", "GraphQL requests", ["path"], registry=registry)
    gql_latency = Histogram(
        "graphql_request_latency_seconds",
        "GraphQL request latency",
        ["path"],
        registry=registry,
        buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2),
    )

    @app.middleware("http")
    async def prometheus_metrics(request: Request, call_next):
        if request.url.path == "/metrics":
            data = generate_latest(registry)
            return Response(content=data, media_type=CONTENT_TYPE_LATEST)
        path = request.url.path
        start = time.perf_counter()
        try:
            gql_counter.labels(path=path).inc()
        except Exception:
            pass
        resp = await call_next(request)
        try:
            gql_latency.labels(path=path).observe(time.perf_counter() - start)
        except Exception:
            pass
        return resp

    return app


def fastapi_json(payload, status_code: int):
    from fastapi.responses import JSONResponse

    return JSONResponse(content=payload, status_code=status_code)
