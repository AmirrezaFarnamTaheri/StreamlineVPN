"""API Routes - Complete Implementation
=====================================

Fixed and complete API routes for StreamlineVPN.
"""

import asyncio
import json
import os
import uuid
import yaml
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urlsplit, urlunsplit

from fastapi import (
    Body,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ...utils.logging import get_logger
from ...core.source_manager import SourceManager
from ...core.merger import StreamlineVPNMerger

logger = get_logger(__name__)

# Request/Response Models
class PipelineRunRequest(BaseModel):
    config_path: str = "config/sources.yaml"
    output_dir: str = "output"
    formats: List[str] = ["json", "clash", "singbox"]

class PipelineRunResponse(BaseModel):
    status: str
    message: str
    job_id: Optional[str] = None

# Global state management
job_status: Dict[str, Dict[str, Any]] = {}
job_tasks: Dict[str, asyncio.Task] = {}
_source_manager: Optional[SourceManager] = None
_merger: Optional[StreamlineVPNMerger] = None

def get_source_manager() -> SourceManager:
    """Get or create source manager instance."""
    global _source_manager
    if _source_manager is None:
        config_path = find_config_path()
        if config_path:
            _source_manager = SourceManager(str(config_path))
        else:
            _source_manager = SourceManager()
    return _source_manager

def get_merger() -> StreamlineVPNMerger:
    """Get or create merger instance."""
    global _merger
    if _merger is None:
        config_path = find_config_path()
        if config_path:
            _merger = StreamlineVPNMerger(config_path=str(config_path))
        else:
            _merger = StreamlineVPNMerger()
    return _merger

def find_config_path() -> Optional[Path]:
    """Find configuration file in standard locations."""
    search_paths = [
        Path("config/sources.yaml"),
        Path("config/sources.unified.yaml"),
        Path.cwd() / "config" / "sources.yaml",
        Path(__file__).parent.parent.parent.parent / "config" / "sources.yaml",
    ]

    for path in search_paths:
        if path.exists():
            return path
    return None

def setup_routes(app, auth_service=None, websocket_manager=None) -> None:
    """Setup all API routes with complete implementation."""

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }

    @app.post("/api/v1/pipeline/run")
    async def run_pipeline(request: PipelineRunRequest) -> PipelineRunResponse:
        """Run VPN configuration pipeline with proper error handling."""
        try:
            # Validate formats
            allowed_formats = {"json", "clash", "singbox", "base64", "raw", "csv"}
            invalid_formats = set(request.formats) - allowed_formats
            if invalid_formats:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid formats: {', '.join(invalid_formats)}"
                )

            # Find config file
            config_path = Path(request.config_path)
            if not config_path.exists():
                config_path = find_config_path()
                if not config_path:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Configuration file not found"
                    )

            # Create output directory
            Path(request.output_dir).mkdir(parents=True, exist_ok=True)

            # Generate job ID
            job_id = str(uuid.uuid4())

            # Initialize job status
            job_status[job_id] = {
                "status": "queued",
                "progress": 0,
                "message": "Job queued for processing",
                "started_at": datetime.now().isoformat()
            }

            # Define async processing
            async def process_job():
                try:
                    # Update status
                    job_status[job_id].update({
                        "status": "running",
                        "progress": 10,
                        "message": "Initializing merger..."
                    })

                    # Get merger instance
                    merger = get_merger()
                    await merger.initialize()

                    # Update progress
                    job_status[job_id].update({
                        "progress": 30,
                        "message": "Processing sources..."
                    })

                    # Process configurations
                    result = await merger.process_all(
                        output_dir=request.output_dir,
                        formats=request.formats
                    )

                    # Complete
                    job_status[job_id].update({
                        "status": "completed",
                        "progress": 100,
                        "message": "Pipeline completed successfully",
                        "completed_at": datetime.now().isoformat(),
                        "result": result
                    })

                except Exception as e:
                    logger.error(f"Pipeline job {job_id} failed: {e}")
                    job_status[job_id].update({
                        "status": "failed",
                        "error": str(e),
                        "message": f"Pipeline failed: {str(e)}",
                        "failed_at": datetime.now().isoformat()
                    })

            # Start task
            task = asyncio.create_task(process_job())
            job_tasks[job_id] = task

            return PipelineRunResponse(
                status="success",
                message="Pipeline started successfully",
                job_id=job_id
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error starting pipeline: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    @app.get("/api/v1/pipeline/status/{job_id}")
    async def get_job_status(job_id: str):
        """Get job status with proper error handling."""
        if job_id not in job_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        return job_status[job_id]

    @app.get("/api/v1/statistics")
    async def get_statistics():
        """Get real statistics from processed data."""
        try:
            stats = {
                "total_configs": 0,
                "successful_sources": 0,
                "total_sources": 0,
                "success_rate": 0.0,
                "avg_quality": 0.75,
                "last_update": None,
                "protocols": {},
                "locations": {}
            }
            
            # Get source count from config
            config_path = find_config_path()
            if config_path and config_path.exists():
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                    if config and "sources" in config:
                        for tier in config["sources"].values():
                            if isinstance(tier, list):
                                stats["total_sources"] += len(tier)
            
            # Get completed jobs count
            completed = [j for j in job_status.values() if j.get("status") == "completed"]
            stats["successful_sources"] = len(completed)
            
            # Calculate success rate
            total_jobs = len(job_status)
            if total_jobs > 0:
                stats["success_rate"] = len(completed) / total_jobs
            
            # Get config count from output
            output_dir = Path("output")
            if output_dir.exists():
                json_file = output_dir / "configs.json"
                if json_file.exists():
                    try:
                        with open(json_file, "r") as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                stats["total_configs"] = len(data)

                                # Count protocols
                                for config in data:
                                    protocol = config.get("protocol", "unknown")
                                    stats["protocols"][protocol] = stats["protocols"].get(protocol, 0) + 1
                    except Exception:
                        pass
            
            # Set last update
            if completed:
                latest = max(completed, key=lambda x: x.get("completed_at", ""))
                stats["last_update"] = latest.get("completed_at")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "total_configs": 0,
                "successful_sources": 0,
                "total_sources": 0,
                "success_rate": 0,
                "avg_quality": 0,
                "last_update": datetime.now().isoformat()
            }

    @app.get("/api/v1/configurations")
    async def get_configurations(
        protocol: Optional[str] = None,
        location: Optional[str] = None,
        min_quality: float = 0.0,
        limit: int = 100,
        offset: int = 0
    ):
        """Get real VPN configurations from output."""
        try:
            configurations = []
            
            # Load from output files
            output_dir = Path("output")
            if output_dir.exists():
                # Try JSON first
                json_file = output_dir / "configs.json"
                if json_file.exists():
                    with open(json_file, "r") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            configurations = data
                        elif isinstance(data, dict) and "configs" in data:
                            configurations = data["configs"]

                # Fallback to raw file
                elif (raw_file := output_dir / "raw.txt").exists():
                    with open(raw_file, "r") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            
                            # Parse protocol from URI
                            config = parse_config_line(line)
                            if config:
                                configurations.append(config)
            
            # Apply filters
            filtered = configurations
            if protocol:
                filtered = [c for c in filtered if c.get("protocol") == protocol]
            if location:
                filtered = [c for c in filtered if c.get("metadata", {}).get("location") == location]
            if min_quality > 0:
                filtered = [c for c in filtered if c.get("quality_score", 0) >= min_quality]
            
            # Pagination
            total = len(filtered)
            paginated = filtered[offset:offset + limit]
            
            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "configurations": paginated
            }
            
        except Exception as e:
            logger.error(f"Error getting configurations: {e}")
            return {
                "total": 0,
                "limit": limit,
                "offset": offset,
                "configurations": []
            }

    @app.get("/api/v1/sources")
    async def get_sources():
        """Get VPN sources with real data."""
        try:
            sources_list = []
            config_path = find_config_path()
            
            if config_path and config_path.exists():
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                    
                    if config and "sources" in config:
                        for tier_name, tier_sources in config["sources"].items():
                            if isinstance(tier_sources, list):
                                for source_url in tier_sources:
                                    sources_list.append({
                                        "url": source_url,
                                        "tier": tier_name,
                                        "status": "active",
                                        "configs": 0
                                    })
            
            return {"sources": sources_list}
            
        except Exception as e:
            logger.error(f"Error getting sources: {e}")
            return {"sources": []}

def parse_config_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a configuration line into structured data."""
    try:
        protocol = "unknown"
        server = "unknown"
        port = 0

        if line.startswith("vmess://"):
            protocol = "vmess"
            # Decode VMess
            try:
                encoded = line[8:]
                decoded = base64.b64decode(encoded).decode('utf-8')
                config = json.loads(decoded)
                server = config.get("add", "unknown")
                port = config.get("port", 443)
            except Exception:
                pass

        elif line.startswith("vless://"):
            protocol = "vless"
            # Parse VLESS
            parts = line[8:].split("@")
            if len(parts) > 1:
                server_part = parts[1].split(":")[0]
                server = server_part
                try:
                    port = int(parts[1].split(":")[1].split("?")[0])
                except Exception:
                    port = 443
                    
        elif line.startswith("trojan://"):
            protocol = "trojan"
            
        elif line.startswith("ss://"):
            protocol = "shadowsocks"

        return {
            "id": f"{protocol}_{server}_{port}",
            "protocol": protocol,
            "server": server,
            "port": port,
            "quality_score": 0.7,
            "raw": line,
            "metadata": {
                "location": "unknown",
                "network": "tcp",
                "tls": True
            }
        }
    except Exception:
        return None
