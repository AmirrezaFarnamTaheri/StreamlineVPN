#!/usr/bin/env python3
"""
run_all.py
==========

Run all StreamlineVPN services in development mode.
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from typing import List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


class ServiceManager:
    """Manage multiple services."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True
        
    def start_service(self, name: str, command: List[str], env: Optional[dict] = None) -> subprocess.Popen:
        """Start a service subprocess."""
        print(f"Starting {name}...")
        
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        process = subprocess.Popen(
            command,
            env=process_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        self.processes.append(process)
        print(f"✅ {name} started (PID: {process.pid})")
        
        return process
    
    def stop_all(self):
        """Stop all services."""
        print("\n🛑 Stopping all services...")
        
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                print(f"   Stopped PID {process.pid}")
        
        self.processes.clear()
        print("✅ All services stopped")
    
    def monitor(self):
        """Monitor services and restart if needed."""
        while self.running:
            time.sleep(5)
            
            for i, process in enumerate(self.processes):
                if process.poll() is not None:
                    print(f"⚠️  Service {i} exited with code {process.returncode}")
                    # Optionally restart the service here
    
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        print("\n📥 Received shutdown signal")
        self.running = False
        self.stop_all()
        sys.exit(0)


def main():
    """Main entry point."""
    manager = ServiceManager()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, manager.handle_shutdown)
    signal.signal(signal.SIGTERM, manager.handle_shutdown)
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║      StreamlineVPN Development Environment                  ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Start Redis if not running
        redis_check = subprocess.run(
            ["redis-cli", "ping"],
            capture_output=True,
            text=True
        )
        
        if redis_check.returncode != 0:
            print("Starting Redis...")
            manager.start_service(
                "Redis",
                ["redis-server"],
                env={"REDIS_PORT": "6379"}
            )
            time.sleep(2)
        else:
            print("✅ Redis already running")
        
        # Start API server
        manager.start_service(
            "API Server",
            [sys.executable, "run_unified.py"],
            env={
                "API_HOST": "0.0.0.0",
                "API_PORT": "8080",
                "VPN_ENVIRONMENT": "development",
                "VPN_DEBUG": "true"
            }
        )
        
        # Wait for API to start
        time.sleep(3)
        
        # Start web interface
        manager.start_service(
            "Web Interface",
            [sys.executable, "run_web.py"],
            env={
                "WEB_HOST": "0.0.0.0",
                "WEB_PORT": "8000",
                "API_BASE_URL": "http://localhost:8080"
            }
        )
        
        print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║  ✅ All services started successfully!                      ║
    ║                                                              ║
    ║  Access Points:                                             ║
    ║  • Web Interface: http://localhost:8000                     ║
    ║  • API Docs: http://localhost:8080/docs                     ║
    ║  • Health: http://localhost:8080/health                     ║
    ║                                                              ║
    ║  Press Ctrl+C to stop all services                          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Keep running
        manager.monitor()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        manager.stop_all()
        sys.exit(1)


if __name__ == "__main__":
    main()
