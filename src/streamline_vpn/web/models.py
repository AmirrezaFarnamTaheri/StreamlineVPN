from pydantic import BaseModel
from typing import List, Optional, Any, Dict

from ...models.formats import OutputFormat

class PipelineRequest(BaseModel):
    config_path: str = "config/sources.yaml"
    output_dir: str = "output"
    formats: List[OutputFormat] = [
        OutputFormat.JSON,
        OutputFormat.CLASH,
    ]

class ProcessingResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None

class AddSourceRequest(BaseModel):
    url: str