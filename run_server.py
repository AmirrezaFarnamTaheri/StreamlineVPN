import os
import sys
from streamline_vpn.web.api.server import APIServer
from streamline_vpn.settings import get_settings
from fastapi.middleware.cors import CORSMiddleware

def main():
    """Main entry point for running the API server with unified configuration."""
    settings = get_settings()
    redis_nodes = settings.redis_nodes or []
    
    # Get dynamic configuration
    host = os.getenv("HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8080"))
    web_port = int(os.getenv("WEB_PORT", "8000"))
    
    # Get allowed origins from environment or use defaults
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
    
    # Add default origins
    default_origins = [
        f"http://localhost:{web_port}",
        f"http://localhost:{api_port}",
        f"http://{host}:{web_port}",
        f"http://{host}:{api_port}",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080"
    ]
    
    # Combine and deduplicate origins
    all_origins = list(set(default_origins + allowed_origins))
    
    # Initialize API server
    api_server = APIServer(
        secret_key=settings.secret_key,
        redis_nodes=redis_nodes
    )
    
    # Single CORS configuration
    api_server.app.add_middleware(
        CORSMiddleware,
        allow_origins=all_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Start background scheduler
    try:
        from streamline_vpn.scheduler import setup_scheduler
        setup_scheduler()
    except ImportError:
        print("Warning: Scheduler not available")
    
    # Run server
    api_server.run(host=host, port=api_port)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down API server gracefully...")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
