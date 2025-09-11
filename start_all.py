#!/usr/bin/env python3
"""Start all StreamlineVPN services."""

import subprocess
import time
import sys
import os


def check_port(port: int) -> bool:
    """Check if a port is available (True if free)."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(("localhost", port))
        return result != 0
    finally:
        try:
            sock.close()
        except Exception:
            pass


def main() -> None:
    """Start API and Web services."""
    print("🚀 Starting StreamlineVPN Services...")
    
    # Check ports
    if not check_port(8080):
        print("❌ Port 8080 is already in use (API)")
        sys.exit(1)
    if not check_port(8000):
        print("❌ Port 8000 is already in use (Web)")
        sys.exit(1)
    
    # Start API server
    print("📡 Starting API server on port 8080...")
    api_process = subprocess.Popen(
        [sys.executable, "run_api.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for API to start
    time.sleep(3)
    
    # Start Web interface
    print("🌐 Starting Web interface on port 8000...")
    web_process = subprocess.Popen(
        [sys.executable, "run_web.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    print(
        """
    ✅ Services Started Successfully!
    
    📡 API Server: http://localhost:8080
    📚 API Docs: http://localhost:8080/docs
    🌐 Web Interface: http://localhost:8000
    🎛️ Control Panel: http://localhost:8000/interactive.html
    
    Press Ctrl+C to stop all services
    """
    )
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        api_process.terminate()
        web_process.terminate()
        time.sleep(1)
        try:
            api_process.kill()
        except Exception:
            pass
        try:
            web_process.kill()
        except Exception:
            pass
        print("✅ Services stopped")


if __name__ == "__main__":
    main()

