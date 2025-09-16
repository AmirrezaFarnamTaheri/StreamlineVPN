"""
API middleware setup.
"""

import uuid
import time
from typing import List
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger(__name__)


def setup_middleware(app: FastAPI) -> None:
    """Setup all middleware for the FastAPI application."""
    
    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    # CORS middleware
    cors_origins = _parse_cors_setting("CORS_ORIGINS", ["http://localhost:8080"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    trusted_hosts = _parse_cors_setting("TRUSTED_HOSTS", ["*"])
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=trusted_hosts
    )
    
    # Logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            url=str(request.url),
            request_id=getattr(request.state, 'request_id', None)
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            request_id=getattr(request.state, 'request_id', None)
        )
        
        return response


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup exception handlers for the FastAPI application."""
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, 'request_id', None)
        
        logger.error(
            "Unhandled exception",
            exception=str(exc),
            request_id=request_id,
            exc_info=True
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "request_id": request_id,
                "message": "An unexpected error occurred"
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        request_id = getattr(request.state, 'request_id', None)
        
        logger.warning(
            "Value error",
            exception=str(exc),
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad request",
                "request_id": request_id,
                "message": str(exc)
            }
        )
    
    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError):
        request_id = getattr(request.state, 'request_id', None)
        
        logger.warning(
            "File not found",
            exception=str(exc),
            request_id=request_id
        )
        
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not found",
                "request_id": request_id,
                "message": "The requested resource was not found"
            }
        )


def _parse_cors_setting(env_var: str, default: List[str]) -> List[str]:
    """Parse CORS setting from environment variable."""
    import os
    
    value = os.getenv(env_var)
    if not value:
        return default
    
    # Split by comma and strip whitespace
    return [item.strip() for item in value.split(",") if item.strip()]

