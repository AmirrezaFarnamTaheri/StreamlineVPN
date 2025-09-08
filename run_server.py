import os
from streamline_vpn.web.api.server import APIServer
from streamline_vpn.settings import get_settings
from streamline_vpn.scheduler import setup_scheduler
from fastapi.middleware.cors import CORSMiddleware

def main():
    """
    Main entry point for running the API server.
    """
    settings = get_settings()
    redis_nodes = settings.redis_nodes or []

    # Start the scheduler
    setup_scheduler()

    api_server = APIServer(
        secret_key=settings.secret_key,
        redis_nodes=redis_nodes
    )

    # Unified CORS configuration with env overrides
    host = os.getenv("HOST", "0.0.0.0")
    web_port = int(os.getenv("WEB_PORT", "8000"))
    api_port = int(os.getenv("API_PORT", "8080"))

    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
    allowed_from_env = [o.strip() for o in allowed_origins_env.split(",") if o.strip()] if allowed_origins_env else []
    defaults = [
        f"http://localhost:{web_port}",
        f"http://localhost:{api_port}",
        f"http://{host}:{web_port}",
        f"http://{host}:{api_port}",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ]
    # Deduplicate while preserving order
    seen = set()
    all_origins = []
    for origin in defaults + allowed_from_env:
        if origin not in seen:
            seen.add(origin)
            all_origins.append(origin)

    api_server.app.add_middleware(
        CORSMiddleware,
        allow_origins=all_origins if all_origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    api_server.run(
        host=host,
        port=api_port
    )

if __name__ == "__main__":
    main()
