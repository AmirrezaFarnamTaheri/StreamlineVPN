#!/usr/bin/env python3
"""
Web Server Runner
=================

Runs a lightweight static file server for the control panel frontend.
"""

import os
import sys
import logging
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
import urllib.error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StreamlineWebHandler(SimpleHTTPRequestHandler):
    """Custom handler for serving static files and proxying API requests."""

    def __init__(self, *args, **kwargs):
        # Set the document root to docs directory
        self.docs_root = Path(__file__).parent / "docs"
        super().__init__(*args, directory=str(self.docs_root), **kwargs)

    def end_headers(self):
        """Add security headers."""
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-XSS-Protection', '1; mode=block')
        super().end_headers()

    def do_GET(self):
        """Handle GET requests with API proxying."""
        if self.path.startswith('/api/'):
            self.proxy_api_request()
        else:
            # Serve static files
            if self.path == '/':
                self.path = '/index.html'
            super().do_GET()

    def do_POST(self):
        """Handle POST requests by proxying to API."""
        if self.path.startswith('/api/'):
            self.proxy_api_request()
        else:
            self.send_error(404, "Not Found")

    def proxy_api_request(self):
        """Proxy API requests to the backend server."""
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:8080")
        api_url = f"{api_base_url}{self.path}"

        try:
            # Prepare request
            req = urllib.request.Request(api_url)

            # Copy headers (excluding host-specific ones)
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'connection']:
                    req.add_header(header, value)

            # Handle POST data
            if self.command == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                req.data = post_data

            # Make request
            with urllib.request.urlopen(req, timeout=30) as response:
                # Send response
                self.send_response(response.getcode())

                # Copy response headers
                for header, value in response.headers.items():
                    if header.lower() not in ['connection', 'transfer-encoding']:
                        self.send_header(header, value)

                self.end_headers()

                # Copy response body
                self.wfile.write(response.read())

        except urllib.error.HTTPError as e:
            self.send_error(e.code, e.reason)
        except urllib.error.URLError as e:
            logger.error(f"API proxy error: {e}")
            self.send_error(502, "Bad Gateway - API server unavailable")
        except Exception as e:
            logger.error(f"Unexpected proxy error: {e}")
            self.send_error(500, "Internal Server Error")

    def log_message(self, format, *args):
        """Override to use proper logging."""
        logger.info(f"{self.address_string()} - {format % args}")


def check_api_server():
    """Check if API server is running."""
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8080")
    health_url = f"{api_base_url}/health"
    
    try:
        with urllib.request.urlopen(health_url, timeout=5) as response:
            if response.getcode() == 200:
                logger.info(f"✅ API server is running at {api_base_url}")
                return True
    except Exception:
        pass

    logger.warning(f"⚠️  API server not responding at {api_base_url}")
    logger.warning("Some features may not work properly")
    return False


def main():
    """Main entry point for the web server."""
    try:
        # Configuration from environment
        host = os.getenv("WEB_HOST", "0.0.0.0")
        port = int(os.getenv("WEB_PORT", "8000"))

        # Check if docs directory exists
        docs_root = Path(__file__).parent / "docs"
        if not docs_root.exists():
            logger.error(f"Documentation directory not found: {docs_root}")
            logger.error("Please ensure the 'docs' directory exists with frontend files")
            sys.exit(1)

        # Check API server
        check_api_server()

        # Start server
        logger.info(f"Starting web server on {host}:{port}")
        logger.info(f"Serving files from: {docs_root}")
        logger.info(f"API proxy target: {os.getenv('API_BASE_URL', 'http://localhost:8080')}")

        httpd = HTTPServer((host, port), StreamlineWebHandler)

        logger.info("🌐 StreamlineVPN Control Panel is running!")
        logger.info(f"📂 Frontend: http://{host}:{port}")
        logger.info(f"🔧 Interactive: http://{host}:{port}/interactive.html")
        logger.info(f"⚙️  Config Gen: http://{host}:{port}/config_generator.html")
        logger.info("Press Ctrl+C to stop")

        httpd.serve_forever()

    except KeyboardInterrupt:
        logger.info("Shutting down web server...")
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
