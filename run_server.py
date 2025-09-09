import os
import sys
from pathlib import Path

# Ensure local src is preferred over any installed package
sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.web.api import create_app
from streamline_vpn.settings import get_settings
from fastapi.middleware.cors import CORSMiddleware

def main():
    """Main entry point for running the API server with unified configuration."""
    settings = get_settings()
    # Remove redis_nodes reference as it's not available in settings
    
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
    
    # Create FastAPI app
    app = create_app()
    
    # Single CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=all_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Setup background scheduler (don't start yet)
    try:
        from streamline_vpn.scheduler import setup_scheduler
        setup_scheduler()
        print("Scheduler configured")
    except ImportError:
        print("Warning: Scheduler not available")
    
    # Run server
    import uvicorn
    uvicorn.run(app, host=host, port=api_port, log_level="info")

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
