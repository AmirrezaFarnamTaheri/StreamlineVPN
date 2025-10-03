import os
import json
import uuid
from typing import List
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from ..utils.logging import get_logger

logger = get_logger(__name__)

def _parse_cors_setting(env_var: str, default: List[str]) -> List[str]:
    """
    Parses a CORS setting from an environment variable.
    Supports both JSON arrays and comma-separated lists.
    """
    value = os.getenv(env_var)
    if not value:
        return default
    try:
        # Prefer JSON format
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        # Fallback to comma-separated string
        return [item.strip() for item in value.split(",") if item.strip()]


def setup_middleware(app: FastAPI):
    """
    Configures and adds all necessary middleware to the FastAPI application.
    """
    # Configure CORS
    allowed_origins = _parse_cors_setting("ALLOWED_ORIGINS", ["*"])
    allowed_methods = _parse_cors_setting("ALLOWED_METHODS", ["*"])
    allowed_headers = _parse_cors_setting("ALLOWED_HEADERS", ["*"])
    allow_credentials = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=allowed_methods,
        allow_headers=allowed_headers,
    )
    logger.info(f"CORS middleware configured with origins: {allowed_origins}")

    # Configure Request ID
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """
        Adds a unique X-Request-ID header to each request for tracking.
        """
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    logger.info("Request ID middleware configured.")