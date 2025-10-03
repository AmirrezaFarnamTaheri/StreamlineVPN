#!/usr/bin/env python3
"""Web Server Runner for StreamlineVPN"""

import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

class StreamlineWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        docs_root = Path(__file__).parent / "docs"
        super().__init__(*args, directory=str(docs_root), **kwargs)

def main():
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "8000"))
    
    print(f"Starting web server on {host}:{port}")
    httpd = HTTPServer((host, port), StreamlineWebHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    main()