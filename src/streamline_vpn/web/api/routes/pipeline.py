import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Request

from streamline_vpn.core.merger import StreamlineVPNMerger
from streamline_vpn.jobs.pipeline_cleanup import cleanup_processing_jobs, processing_jobs
from streamline_vpn.web.dependencies import get_merger
from streamline_vpn.web.models import PipelineRequest, ProcessingResponse

pipeline_router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline"])


def update_job_progress(job_id: str, progress: int, message: str) -> None:
    if job_id in processing_jobs:
        processing_jobs[job_id]["progress"] = progress
        processing_jobs[job_id]["message"] = message


@pipeline_router.post("/run", status_code=status.HTTP_202_ACCEPTED, response_model=Dict[str, Any])
async def run_pipeline(
    fastapi_request: Request,
    background_tasks: BackgroundTasks,
    request: PipelineRequest,
) -> Dict[str, Any]:
    """Run the VPN configuration pipeline in the background."""
    config_file = Path(request.config_path)
    if not config_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration file not found: {request.config_path}",
        )

    Path(request.output_dir).mkdir(parents=True, exist_ok=True)

    job_id = str(uuid.uuid4())
    processing_jobs[job_id] = {
        "status": "running",
        "progress": 0,
        "message": "Starting pipeline...",
        "started_at": datetime.now().isoformat(),
    }

    shared_session = getattr(fastapi_request.app.state, "http_session", None)

    async def process_async() -> None:
        import aiohttp
        local_session = None
        try:
            session = shared_session
            if session is None or getattr(session, "closed", True):
                local_session = aiohttp.ClientSession()
                session = local_session

            update_job_progress(job_id, 10, "Initializing merger...")
            local_merger = StreamlineVPNMerger(config_path=str(config_file), session=session)
            await local_merger.initialize()

            update_job_progress(job_id, 50, "Processing configurations...")
            formats = [fmt.value for fmt in request.formats]
            result = await local_merger.process_all(
                output_dir=request.output_dir, formats=formats
            )

            processing_jobs[job_id]["status"] = "completed"
            update_job_progress(job_id, 100, "Pipeline completed successfully")
            processing_jobs[job_id]["result"] = result
            processing_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        except Exception as exc:
            processing_jobs[job_id]["status"] = "failed"
            processing_jobs[job_id]["error"] = str(exc)
            processing_jobs[job_id]["completed_at"] = datetime.now().isoformat()
            update_job_progress(job_id, 100, str(exc))
        finally:
            if local_session is not None and not local_session.closed:
                await local_session.close()

    background_tasks.add_task(process_async)
    return {"status": "accepted", "job_id": job_id}


@pipeline_router.get("/status/{job_id}", response_model=Dict[str, Any])
async def get_pipeline_status(job_id: str) -> Dict[str, Any]:
    """Return status of a background pipeline job."""
    if job_id not in processing_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )
    return processing_jobs[job_id]


@pipeline_router.post("/cleanup", response_model=Dict[str, Any])
async def manual_pipeline_cleanup() -> Dict[str, Any]:
    """Trigger cleanup of old pipeline jobs manually."""
    removed = cleanup_processing_jobs()
    return {"removed": removed, "remaining": len(processing_jobs)}


@pipeline_router.post("/process", response_model=ProcessingResponse)
async def process_configurations_legacy(
    request: PipelineRequest, merger: StreamlineVPNMerger = Depends(get_merger)
) -> ProcessingResponse:
    """Legacy endpoint for processing configurations directly."""
    results = await merger.process_all(
        output_dir=request.output_dir, formats=[fmt.value for fmt in request.formats]
    )
    return ProcessingResponse(
        success=results.get("success", False),
        message="Processing completed",
        statistics=results.get("statistics"),
    )