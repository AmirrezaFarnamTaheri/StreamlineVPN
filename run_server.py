import os

from fastapi.middleware.cors import CORSMiddleware

from streamline_vpn.scheduler import setup_scheduler
from streamline_vpn.settings import get_settings
from streamline_vpn.web.api.server import APIServer


def main():
    """
    Main entry point for running the API server.
    """
    settings = get_settings()

    # Default to an empty list if redis_nodes is None
    redis_nodes = settings.redis_nodes or []

    # Start the scheduler
    setup_scheduler()

    api_server = APIServer(
        secret_key=settings.secret_key,
        redis_nodes=redis_nodes,
    )

    api_server.app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_server.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
    )


if __name__ == "__main__":
    main()
