from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from ...models.formats import OutputFormat


class ProcessingRequest(BaseModel):
    config_path: Optional[str] = "config/sources.yaml"
    output_dir: Optional[str] = "output"
    formats: Optional[List[str]] = ["json", "clash"]
    max_concurrent: Optional[int] = 50


class ProcessingResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime: float


class PipelineRequest(BaseModel):
    config_path: str = "config/sources.yaml"
    output_dir: str = "output"
    formats: List[OutputFormat] = [
        OutputFormat.JSON,
        OutputFormat.CLASH,
    ]


class AddSourceRequest(BaseModel):
    url: str