import os
import sys
from pathlib import Path

# Ensure local src is preferred over any installed package
sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamline_vpn.web.unified_api import create_unified_app

def main():
    """Main entry point for running the API server with unified configuration."""
    # Get dynamic configuration
    host = os.getenv("HOST", "0.0.0.0")
    api_port = int(os.getenv("API_PORT", "8080"))
    
    # Create FastAPI app (CORS is already configured in unified API)
    app = create_unified_app()
    
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
