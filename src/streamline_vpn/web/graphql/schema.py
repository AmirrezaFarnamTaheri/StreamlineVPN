"""
GraphQL Schema
==============

GraphQL schema definitions for StreamlineVPN.
"""

import strawberry
from typing import List, Optional
from datetime import datetime


@strawberry.type
class VPNConfiguration:
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


@strawberry.type
class SourceMetadata:
    url: str
    tier: str
    weight: float
    success_count: int
    failure_count: int
    reputation_score: float
    is_blacklisted: bool


@strawberry.type
class ProcessingStatistics:
    total_sources: int
    successful_sources: int
    failed_sources: int
    total_configs: int
    success_rate: float
    avg_response_time: float
    total_processing_time: float


@strawberry.type
class Health:
    status: str
    timestamp: str
    version: str
    uptime: float


@strawberry.type
class Query:
    @strawberry.field
    def health(self) -> Health:
        """Health check."""
        from ..api import start_time

        uptime = (datetime.now() - start_time).total_seconds()
        return Health(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="2.0.0",
            uptime=uptime,
        )

    @strawberry.field
    def configurations(self) -> List[VPNConfiguration]:
        """Get all configurations."""
        # Return empty list for now to avoid circular imports
        # In a real implementation, this would be injected
        return []

    @strawberry.field
    def sources(self) -> List[SourceMetadata]:
        """Get all sources."""
        # Return empty list for now to avoid circular imports
        # In a real implementation, this would be injected
        return []

    @strawberry.field
    def statistics(self) -> ProcessingStatistics:
        """Get processing statistics."""
        # Return default statistics to avoid circular imports
        # In a real implementation, this would be injected
        return ProcessingStatistics(
            total_sources=0,
            successful_sources=0,
            failed_sources=0,
            total_configs=0,
            success_rate=0.0,
            avg_response_time=0.0,
            total_processing_time=0.0,
        )


@strawberry.type
class Mutation:
    @strawberry.field
    def process_configurations(self, config_path: Optional[str] = None) -> str:
        """Process configurations."""
        # Return placeholder to avoid circular imports
        # In a real implementation, this would be injected
        return "Processing not available in GraphQL mode"

    @strawberry.field
    def blacklist_source(self, source_url: str, reason: str = "") -> str:
        """Blacklist a source."""
        # Return placeholder to avoid circular imports
        # In a real implementation, this would be injected
        return f"Blacklist not available in GraphQL mode"

    @strawberry.field
    def whitelist_source(self, source_url: str) -> str:
        """Whitelist a source."""
        # Return placeholder to avoid circular imports
        # In a real implementation, this would be injected
        return f"Whitelist not available in GraphQL mode"


# Create schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
