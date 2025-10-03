"""
Configuration management routes.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import json

configurations_router = APIRouter()


class ConfigurationRoutes:
    @staticmethod
    def _get_merger():
        try:
            from ...unified_api import get_merger  # type: ignore

            return get_merger()
        except Exception:
            return None


@configurations_router.get(
    "/configurations",
    summary="Get Processed Configurations",
    description="Retrieve a list of processed and validated VPN configurations.",
    response_description="A list of VPN configurations with metadata.",
)
async def get_configurations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    format: Optional[str] = Query(None, description="Filter by format"),
):
    """
    Get processed configurations.

    - **limit**: The maximum number of configurations to return.
    - **offset**: The number of configurations to skip.
    - **format**: The format to filter by (e.g., `json`, `clash`).
    """
    try:
        from ...core.merger import StreamlineVPNMerger

        merger = StreamlineVPNMerger()
        configurations = merger.get_processed_configurations(
            limit=limit, offset=offset, format_filter=format
        )

        return {
            "configurations": configurations,
            "count": len(configurations),
            "limit": limit,
            "offset": offset,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve configurations: {str(e)}"
        )


@configurations_router.post(
    "/configurations/process",
    summary="Run Processing Pipeline",
    description="Trigger the VPN configuration processing pipeline.",
    response_description="A confirmation that the pipeline has been started.",
)
async def run_pipeline(request: Dict[str, Any]):
    """
    Run the processing pipeline.

    - **formats**: A list of output formats to generate (e.g., `["json", "clash"]`).
    - **max_concurrent**: The maximum number of concurrent requests.
    - **timeout**: The timeout for each request in seconds.
    - **force_refresh**: Whether to force a refresh of the sources.
    """
    try:
        from ...core.merger import StreamlineVPNMerger
        from ...core.source_manager import SourceManager

        source_manager = SourceManager()
        merger = StreamlineVPNMerger()

        # Get sources
        sources = source_manager.get_all_sources()
        if not sources:
            raise HTTPException(status_code=400, detail="No sources configured")

        # Process configurations
        result = await merger.process_sources(
            sources=sources,
            formats=request.get("formats", ["all"]),
            max_concurrent=request.get("max_concurrent", 5),
            timeout=request.get("timeout", 30),
            force_refresh=request.get("force_refresh", False),
        )

        return {
            "status": "success",
            "message": "Pipeline completed successfully",
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


@configurations_router.get(
    "/configurations/statistics",
    summary="Get Processing Statistics",
    description="Retrieve statistics about the configuration processing.",
    response_description="A dictionary of processing statistics.",
)
async def get_statistics():
    """Get processing statistics."""
    try:
        from ...core.merger import StreamlineVPNMerger

        merger = StreamlineVPNMerger()
        stats = merger.get_statistics()

        return {"statistics": stats, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


@configurations_router.get(
    "/configurations/export",
    summary="Export Configurations",
    description="Export configurations in various formats.",
    response_description="The configurations in the specified format.",
)
async def export_configurations(
    format: str = Query("json", description="Export format")
):
    """
    Export configurations in various formats.

    - **format**: The export format (e.g., `json`, `csv`, `yaml`).
    """
    try:
        from ...core.merger import StreamlineVPNMerger
        from ...core.output_manager import OutputManager

        merger = StreamlineVPNMerger()
        output_manager = OutputManager()

        # Get configurations
        configurations = merger.get_processed_configurations()

        # Export in requested format
        if format == "json":
            content = json.dumps(configurations, indent=2)
            media_type = "application/json"
            filename = "configurations.json"
        elif format == "csv":
            content = output_manager.export_csv(configurations)
            media_type = "text/csv"
            filename = "configurations.csv"
        elif format == "yaml":
            import yaml

            content = yaml.dump(configurations, default_flow_style=False)
            media_type = "application/x-yaml"
            filename = "configurations.yaml"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        return StreamingResponse(
            iter([content]),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@configurations_router.post(
    "/configurations/validate",
    summary="Validate Configurations",
    description="Validate a list of configurations.",
    response_description="The validation results.",
)
async def validate_configurations(configurations: List[Dict[str, Any]]):
    """Validate a list of configurations."""
    try:
        from ...core.processing.validator import ConfigurationValidator

        validator = ConfigurationValidator()
        results = []

        for config in configurations:
            is_valid, errors = validator.validate_configuration(config)
            results.append({"config": config, "valid": is_valid, "errors": errors})

        return {
            "results": results,
            "total": len(results),
            "valid": sum(1 for r in results if r["valid"]),
            "invalid": sum(1 for r in results if not r["valid"]),
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@configurations_router.delete(
    "/configurations/cache",
    summary="Clear Cache",
    description="Clear the configuration cache.",
    response_description="A confirmation that the cache has been cleared.",
)
async def clear_cache():
    """Clear configuration cache."""
    try:
        from ...caching.service import CacheService

        cache_service = CacheService()
        cache_service.clear_all()

        return {"status": "success", "message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
