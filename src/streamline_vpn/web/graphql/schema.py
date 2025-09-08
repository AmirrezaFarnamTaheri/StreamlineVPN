"""
GraphQL Schema - Complete Implementation with Dependency Injection
==================================================================
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

import strawberry
from strawberry.scalars import JSON
from strawberry.types import Info

from ...core.merger import StreamlineVPNMerger
from ...core.source_manager import SourceManager
from ...jobs.manager import JobManager
from ...jobs.models import JobStatus, JobType
from ...security.manager import SecurityManager
from ...utils.logging import get_logger


# Dependency injection context
class GraphQLContext:
    """Context for GraphQL resolvers with injected dependencies."""

    def __init__(self) -> None:
        self.merger: Optional[StreamlineVPNMerger] = None
        self.job_manager: Optional[JobManager] = None
        self.source_manager: Optional[SourceManager] = None
        self.security_manager: Optional[SecurityManager] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all services."""
        if not self._initialized:
            self.merger = StreamlineVPNMerger()
            self.job_manager = JobManager()
            self.source_manager = self.merger.source_manager
            self.security_manager = SecurityManager()
            await self.merger.initialize()
            self._initialized = True

    async def get_merger(self) -> StreamlineVPNMerger:
        """Get or create merger instance."""
        if not self._initialized:
            await self.initialize()
        assert self.merger is not None
        return self.merger

    async def get_job_manager(self) -> JobManager:
        """Get or create job manager instance."""
        if not self._initialized:
            await self.initialize()
        assert self.job_manager is not None
        return self.job_manager


# Global context instance
context = GraphQLContext()

logger = get_logger(__name__)


@strawberry.type
class VPNConfiguration:
    id: str
    protocol: str
    server: str
    port: int
    user_id: Optional[str] = None
    password: Optional[str] = None
    encryption: Optional[str] = None
    network: str = "tcp"
    path: Optional[str] = None
    host: Optional[str] = None
    tls: bool = False
    quality_score: float = 0.0
    source_url: Optional[str] = None
    created_at: str
    raw_config: Optional[str] = None


@strawberry.type
class SourceMetadata:
    url: str
    tier: str
    weight: float
    success_count: int
    failure_count: int
    reputation_score: float
    is_blacklisted: bool
    last_check: str
    avg_config_count: int
    avg_response_time: float


@strawberry.type
class ProcessingStatistics:
    total_sources: int
    successful_sources: int
    failed_sources: int
    total_configs: int
    valid_configs: int
    invalid_configs: int
    success_rate: float
    avg_response_time: float
    total_processing_time: float
    deduplication_rate: float
    quality_distribution: JSON


@strawberry.type
class JobInfo:
    id: str
    type: str
    status: str
    progress: float
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    parameters: Optional[str] = None


@strawberry.type
class Health:
    status: str
    timestamp: str
    version: str
    uptime: float
    services: JSON


@strawberry.type
class ProcessingResult:
    success: bool
    message: str
    job_id: Optional[str] = None
    statistics: Optional[ProcessingStatistics] = None
    output_files: Optional[List[str]] = None


@strawberry.type
class SourceOperationResult:
    success: bool
    message: str
    source_url: str
    operation: str


@strawberry.type
class Query:
    @strawberry.field
    async def health(self, info: Info) -> Health:
        """Health check with service status."""
        from ...web.api import start_time

        uptime = (datetime.now() - start_time).total_seconds()

        services: Dict[str, bool] = {}
        try:
            merger = await context.get_merger()
            services["merger"] = merger is not None
            services["source_manager"] = merger.source_manager is not None
            services["config_processor"] = merger.config_processor is not None
            services["output_manager"] = merger.output_manager is not None
        except Exception:
            services["merger"] = False

        try:
            job_manager = await context.get_job_manager()
            services["job_manager"] = job_manager is not None
        except Exception:
            services["job_manager"] = False

        return Health(
            status="healthy" if all(services.values()) else "degraded",
            timestamp=datetime.now().isoformat(),
            version="2.0.0",
            uptime=uptime,
            services=services,
        )

    @strawberry.field
    async def configurations(
        self,
        info: Info,
        limit: int = 100,
        offset: int = 0,
        protocol: Optional[str] = None,
        min_quality: float = 0.0,
    ) -> List[VPNConfiguration]:
        """Get VPN configurations with filtering."""
        merger = await context.get_merger()
        configs = await merger.get_configurations()

        filtered_configs = []
        for cfg in configs:
            if protocol and cfg.protocol.value != protocol:
                continue
            if cfg.quality_score < min_quality:
                continue
            filtered_configs.append(cfg)

        paginated = filtered_configs[offset : offset + limit]

        return [
            VPNConfiguration(
                id=getattr(cfg, "id", f"{cfg.server}:{cfg.port}"),
                protocol=cfg.protocol.value,
                server=cfg.server,
                port=cfg.port,
                user_id=cfg.user_id,
                password=cfg.password,
                encryption=cfg.encryption,
                network=cfg.network,
                path=cfg.path,
                host=cfg.host,
                tls=cfg.tls,
                quality_score=cfg.quality_score,
                source_url=cfg.source_url,
                created_at=cfg.created_at.isoformat(),
                raw_config=(
                    cfg.metadata.get("raw_config") if cfg.metadata else None
                ),
            )
            for cfg in paginated
        ]

    @strawberry.field
    async def sources(
        self,
        info: Info,
        tier: Optional[str] = None,
        blacklisted: Optional[bool] = None,
    ) -> List[SourceMetadata]:
        """Get sources with optional filtering."""
        merger = await context.get_merger()

        if not merger.source_manager:
            return []

        sources: List[SourceMetadata] = []
        for url, source in merger.source_manager.sources.items():
            if tier and source.tier.value != tier:
                continue
            if (
                blacklisted is not None
                and source.is_blacklisted != blacklisted
            ):
                continue

            sources.append(
                SourceMetadata(
                    url=url,
                    tier=source.tier.value,
                    weight=source.weight,
                    success_count=source.success_count,
                    failure_count=source.failure_count,
                    reputation_score=source.reputation_score,
                    is_blacklisted=source.is_blacklisted,
                    last_check=source.last_check.isoformat(),
                    avg_config_count=source.avg_config_count,
                    avg_response_time=source.avg_response_time,
                )
            )

        return sources

    @strawberry.field
    async def statistics(self, info: Info) -> ProcessingStatistics:
        """Get detailed processing statistics."""
        merger = await context.get_merger()
        stats = await merger.get_statistics()

        configs = await merger.get_configurations()
        quality_distribution = {
            "excellent": 0,
            "good": 0,
            "fair": 0,
            "poor": 0,
        }
        for cfg in configs:
            if cfg.quality_score >= 0.8:
                quality_distribution["excellent"] += 1
            elif cfg.quality_score >= 0.6:
                quality_distribution["good"] += 1
            elif cfg.quality_score >= 0.4:
                quality_distribution["fair"] += 1
            else:
                quality_distribution["poor"] += 1

        return ProcessingStatistics(
            total_sources=stats.get("total_sources", 0),
            successful_sources=stats.get("successful_sources", 0),
            failed_sources=stats.get("failed_sources", 0),
            total_configs=stats.get("total_configs", 0),
            valid_configs=stats.get("valid_configs", 0),
            invalid_configs=stats.get("invalid_configs", 0),
            success_rate=stats.get("success_rate", 0.0),
            avg_response_time=stats.get("avg_response_time", 0.0),
            total_processing_time=stats.get("total_processing_time", 0.0),
            deduplication_rate=stats.get("deduplication_rate", 0.0),
            quality_distribution=quality_distribution,
        )

    @strawberry.field
    async def jobs(
        self,
        info: Info,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[JobInfo]:
        """Get jobs with optional status filter."""
        job_manager = await context.get_job_manager()

        job_status = JobStatus(status) if status else None
        jobs = await job_manager.get_jobs(status=job_status, limit=limit)

        return [
            JobInfo(
                id=job.id,
                type=job.type.value,
                status=job.status.value,
                progress=job.progress / 100.0,
                created_at=job.created_at.isoformat(),
                started_at=(
                    job.started_at.isoformat() if job.started_at else None
                ),
                completed_at=(
                    job.completed_at.isoformat() if job.completed_at else None
                ),
                result=json.dumps(job.result) if job.result else None,
                error=job.error,
                parameters=(
                    json.dumps(job.parameters) if job.parameters else None
                ),
            )
            for job in jobs
        ]

    @strawberry.field
    async def job(self, info: Info, job_id: str) -> Optional[JobInfo]:
        """Get specific job by ID."""
        job_manager = await context.get_job_manager()
        job = await job_manager.get_job(job_id)

        if not job:
            return None

        return JobInfo(
            id=job.id,
            type=job.type.value,
            status=job.status.value,
            progress=job.progress / 100.0,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=(
                job.completed_at.isoformat() if job.completed_at else None
            ),
            result=json.dumps(job.result) if job.result else None,
            error=job.error,
            parameters=json.dumps(job.parameters) if job.parameters else None,
        )


@strawberry.type
class Mutation:
    @strawberry.field
    async def process_configurations(
        self,
        info: Info,
        config_path: Optional[str] = None,
        output_dir: str = "output",
        formats: Optional[List[str]] = None,
        run_async: bool = True,
    ) -> ProcessingResult:
        """Process VPN configurations."""
        try:
            job_manager = await context.get_job_manager()
            merger = await context.get_merger()

            if run_async:
                job = await job_manager.create_job(
                    JobType.PROCESS_CONFIGURATIONS,
                    parameters={
                        "config_path": config_path or "config/sources.yaml",
                        "output_dir": output_dir,
                        "formats": formats or ["json", "clash", "singbox"],
                    },
                )

                await job_manager.start_job(job.id)

                return ProcessingResult(
                    success=True,
                    message="Processing started successfully",
                    job_id=job.id,
                )
            else:
                results = await merger.process_all(
                    output_dir=output_dir, formats=formats
                )
                stats = await merger.get_statistics()

                return ProcessingResult(
                    success=results.get("success", False),
                    message=results.get("message", "Processing completed"),
                    statistics=ProcessingStatistics(
                        total_sources=stats.get("total_sources", 0),
                        successful_sources=stats.get("successful_sources", 0),
                        failed_sources=stats.get("failed_sources", 0),
                        total_configs=stats.get("total_configs", 0),
                        valid_configs=stats.get("valid_configs", 0),
                        invalid_configs=stats.get("invalid_configs", 0),
                        success_rate=stats.get("success_rate", 0.0),
                        avg_response_time=stats.get("avg_response_time", 0.0),
                        total_processing_time=stats.get(
                            "total_processing_time", 0.0
                        ),
                        deduplication_rate=stats.get(
                            "deduplication_rate", 0.0
                        ),
                        quality_distribution={},
                    ),
                    output_files=results.get("output_files", []),
                )

        except Exception as e:
            logger.error("Processing failed: %s", e)
            return ProcessingResult(
                success=False,
                message="Processing failed",
            )

    @strawberry.field
    async def blacklist_source(
        self, info: Info, source_url: str, reason: str = ""
    ) -> SourceOperationResult:
        """Blacklist a source."""
        try:
            merger = await context.get_merger()

            if merger.source_manager:
                merger.source_manager.blacklist_source(source_url, reason)
                return SourceOperationResult(
                    success=True,
                    message="Source blacklisted successfully",
                    source_url=source_url,
                    operation="blacklist",
                )
            return SourceOperationResult(
                success=False,
                message="Source manager not available",
                source_url=source_url,
                operation="blacklist",
            )

        except Exception as e:
            logger.error("Failed to blacklist source %s: %s", source_url, e)
            return SourceOperationResult(
                success=False,
                message="Failed to blacklist source",
                source_url=source_url,
                operation="blacklist",
            )

    @strawberry.field
    async def whitelist_source(
        self, info: Info, source_url: str
    ) -> SourceOperationResult:
        """Whitelist a source."""
        try:
            merger = await context.get_merger()

            if merger.source_manager:
                merger.source_manager.whitelist_source(source_url)
                return SourceOperationResult(
                    success=True,
                    message="Source whitelisted successfully",
                    source_url=source_url,
                    operation="whitelist",
                )
            return SourceOperationResult(
                success=False,
                message="Source manager not available",
                source_url=source_url,
                operation="whitelist",
            )

        except Exception as e:
            logger.error("Failed to whitelist source %s: %s", source_url, e)
            return SourceOperationResult(
                success=False,
                message="Failed to whitelist source",
                source_url=source_url,
                operation="whitelist",
            )

    @strawberry.field
    async def cancel_job(self, info: Info, job_id: str) -> ProcessingResult:
        """Cancel a running job."""
        try:
            job_manager = await context.get_job_manager()
            success = await job_manager.cancel_job(job_id)

            return ProcessingResult(
                success=success,
                message=(
                    "Job cancelled successfully"
                    if success
                    else "Failed to cancel job"
                ),
                job_id=job_id,
            )

        except Exception as e:
            logger.error("Failed to cancel job %s: %s", job_id, e)
            return ProcessingResult(
                success=False,
                message="Failed to cancel job",
                job_id=job_id,
            )

    @strawberry.field
    async def clear_cache(self, info: Info) -> ProcessingResult:
        """Clear all caches."""
        try:
            merger = await context.get_merger()
            await merger.clear_cache()
            return ProcessingResult(
                success=True, message="Cache cleared successfully"
            )

        except Exception as e:
            logger.error("Failed to clear cache: %s", e)
            return ProcessingResult(
                success=False,
                message="Failed to clear cache",
            )


# Create schema with context
schema = strawberry.Schema(query=Query, mutation=Mutation)
