"""
GraphQL API Schema with basic queries, mutations, and subscriptions.
Uses Strawberry and is mounted via FastAPI in a separate app.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime

import strawberry
from strawberry.schema.config import StrawberryConfig

from .jobs import job_manager


@strawberry.type
class VPNConfig:
    id: str
    host: str
    port: int
    protocol: str
    quality_score: float
    latency_ms: float | None
    created_at: datetime
    updated_at: datetime


@strawberry.type
class ProcessingStatus:
    status: str
    progress: float
    configs_processed: int
    current_operation: str


@strawberry.type
class JobStatus:
    id: str
    status: str
    total_configs: int
    valid_configs: int
    progress: float


@strawberry.type
class MergeResult:
    id: str
    total_configs: int
    valid_configs: int
    processing_time: float


@strawberry.type
class PageInfo:
    total: int
    has_more: bool
    has_next_page: bool
    end_cursor: str | None


@strawberry.type
class ConfigsPage:
    items: list[VPNConfig]
    page_info: PageInfo


@strawberry.type
class VPNConfigEdge:
    node: VPNConfig
    cursor: str


@strawberry.type
class VPNConfigConnection:
    edges: list[VPNConfigEdge]
    page_info: PageInfo
    total_count: int


@strawberry.type
class Query:
    @strawberry.field
    async def health(self) -> str:
        return "ok"

    @strawberry.field
    async def job(self, id: str) -> JobStatus | None:
        j = job_manager.get(id)
        if not j:
            return None
        return JobStatus(
            id=j.id,
            status=j.status,
            total_configs=j.total_configs,
            valid_configs=j.valid_configs,
            progress=j.progress,
        )

    @strawberry.field
    async def jobs(self) -> list[JobStatus]:
        js = []
        for j in job_manager.list():
            js.append(
                JobStatus(
                    id=j.id,
                    status=j.status,
                    total_configs=j.total_configs,
                    valid_configs=j.valid_configs,
                    progress=j.progress,
                )
            )
        return js

    @strawberry.field
    async def configs(
        self,
        limit: int = 50,
        offset: int = 0,
        protocol: str | None = None,
        host_regex: str | None = None,
        reachable: bool | None = None,
        sort: str | None = "quality_desc",
        sources: list[str] | None = None,
    ) -> list[VPNConfig]:
        import os

        from ...core.source_processor import SourceProcessor

        # Use provided sources; fallback to simulated when in test mode
        results = []
        async with SourceProcessor() as sp:
            if sources:
                results = await sp.process_sources(sources, max_concurrent=10)
            else:
                os.environ.setdefault("VPN_MERGER_TEST_MODE", "1")
                results = await sp.process_sources(
                    ["http://example.local/test.txt"], max_concurrent=5
                )

        # Filter by protocol if requested
        if protocol:
            p = protocol.lower()
            results = [r for r in results if (r.protocol or "").lower() == p]

        # Host regex filter
        if host_regex:
            import re

            try:
                rx = re.compile(host_regex, re.I)
                results = [r for r in results if (r.host and rx.search(r.host))]
            except re.error:
                pass

        # Reachability filter
        if reachable is not None:
            results = [r for r in results if bool(r.is_reachable) == bool(reachable)]

        # Sorting
        if sort in ("quality_desc", None):
            results.sort(key=lambda r: float(r.quality_score), reverse=True)
        elif sort == "quality_asc":
            results.sort(key=lambda r: float(r.quality_score))

        # Pagination
        start = max(0, int(offset))
        end = start + max(1, int(limit))
        page = results[start:end]
        out: list[VPNConfig] = []
        now = datetime.utcnow()
        for r in page:
            out.append(
                VPNConfig(
                    id=str(hash(r.config)),
                    host=r.host or "",
                    port=int(r.port or 0),
                    protocol=r.protocol,
                    quality_score=float(r.quality_score),
                    latency_ms=r.ping_time,
                    created_at=now,
                    updated_at=now,
                )
            )
        if not out:
            out.append(
                VPNConfig(
                    id="empty",
                    host="",
                    port=0,
                    protocol="unknown",
                    quality_score=0.0,
                    latency_ms=None,
                    created_at=now,
                    updated_at=now,
                )
            )
        return out

    @strawberry.field
    async def configsPage(
        self,
        limit: int = 50,
        offset: int = 0,
        protocol: str | None = None,
        host_regex: str | None = None,
        reachable: bool | None = None,
        sort: str | None = "quality_desc",
        sources: list[str] | None = None,
    ) -> ConfigsPage:
        items = await Query().configs(
            limit=limit,
            offset=offset,
            protocol=protocol,
            host_regex=host_regex,
            reachable=reachable,
            sort=sort,
            sources=sources,
        )
        # naive total: re-run with large limit (for demo) or infer from previous results
        # here, compute total by reprocessing once (kept simple to avoid refactor)
        import os

        from ...core.source_processor import SourceProcessor

        results = []
        async with SourceProcessor() as sp:
            if sources:
                results = await sp.process_sources(sources, max_concurrent=10)
            else:
                os.environ.setdefault("VPN_MERGER_TEST_MODE", "1")
                results = await sp.process_sources(
                    ["http://example.local/test.txt"], max_concurrent=5
                )
        total = len(results)
        page_size = max(1, int(limit))
        has_more = (offset + page_size) < total
        end_cursor = None
        try:
            end_index = min(total, offset + page_size) - 1
            if end_index >= 0 and items:
                import base64

                end_cursor = base64.b64encode(str(end_index).encode()).decode()
        except Exception:
            end_cursor = None
        return ConfigsPage(
            items=items,
            page_info=PageInfo(
                total=total, has_more=has_more, has_next_page=has_more, end_cursor=end_cursor
            ),
        )

    @strawberry.field
    async def configsConnection(
        self,
        first: int = 50,
        after: str | None = None,
        protocol: str | None = None,
        host_regex: str | None = None,
        reachable: bool | None = None,
        sort: str | None = "quality_desc",
        sources: list[str] | None = None,
    ) -> VPNConfigConnection:
        import base64
        
        # Resolve after to offset
        start_offset = 0
        if after:
            try:
                start_offset = int(base64.b64decode(after.encode()).decode()) + 1
            except Exception:
                start_offset = 0
        # Reuse configs for filtering
        items = await Query().configs(
            limit=first,
            offset=start_offset,
            protocol=protocol,
            host_regex=host_regex,
            reachable=reachable,
            sort=sort,
            sources=sources,
        )
        # Compute total via reprocessing (kept simple)
        import os
        from ...core.source_processor import SourceProcessor

        results = []
        if sources:
            async with SourceProcessor() as sp:
                results = await sp.process_sources(sources, max_concurrent=10)
        total = len(results) if results else 0

        return VPNConfigConnection(
            edges=[
                VPNConfigEdge(
                    node=item,
                    cursor=base64.b64encode(str(start_offset + i).encode()).decode(),
                )
                for i, item in enumerate(items)
            ],
            page_info=PageInfo(
                total=total,
                has_more=len(items) == first,
                has_next_page=len(items) == first,
                end_cursor=base64.b64encode(str(start_offset + len(items) - 1).encode()).decode() if items else None,
            ),
            total_count=total,
        )


@strawberry.type
class Mutation:
    @strawberry.mutation(name="startMerge")
    async def start_merge(self, sources: list[str] | None = None) -> MergeResult:
        sources = sources or ["http://example.local/test.txt"]
        # create async job
        job = job_manager.create_job(sources)
        return MergeResult(
            id=job.id,
            total_configs=0,
            valid_configs=0,
            processing_time=0.0,
        )

    @strawberry.mutation(name="cancelJob")
    async def cancel_job(self, id: str) -> bool:
        return job_manager.cancel(id)

    @strawberry.mutation(name="deleteJob")
    async def delete_job(self, id: str) -> bool:
        return job_manager.delete(id)

    @strawberry.mutation(name="cleanupJobs")
    async def cleanup_jobs(self) -> int:
        return job_manager.cleanup_now()


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def job_status(self, job_id: str) -> AsyncGenerator[JobStatus, None]:
        """Subscribe to job status updates."""
        while True:
            job = job_manager.get(job_id)
            if not job:
                break
            yield JobStatus(
                id=job.id,
                status=job.status,
                total_configs=job.total_configs,
                valid_configs=job.valid_configs,
                progress=job.progress,
            )
            if job.status in ("completed", "failed", "cancelled"):
                break
            await asyncio.sleep(1)


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(auto_camel_case=False),
)