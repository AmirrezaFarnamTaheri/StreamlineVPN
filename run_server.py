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

    # Add CORS middleware with dynamic origins
    host = os.getenv("HOST", "0.0.0.0")
    web_port = int(os.getenv("WEB_PORT", "8000"))
    api_port = int(os.getenv("PORT", "8080"))

    api_server.app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://localhost:{web_port}",
            f"http://localhost:{api_port}",
            f"http://{host}:{web_port}",
            f"http://{host}:{api_port}",
            "http://localhost:8000",
            "http://localhost:8080",
            "*"  # For development - remove in production
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_server.run(
        host=host,
        port=api_port
    )

if __name__ == "__main__":
    main()
