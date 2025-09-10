#!/usr/bin/env python3
"""
StreamlineVPN Startup Script
Helps users start the application with proper configuration
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def check_requirements():
    """Check if required files and directories exist"""
    required_files = [
        "config/sources.yaml",
        "run_unified.py",
        "run_web.py",
        "docker-compose.yml"
    ]
    
    required_dirs = [
        "src/streamline_vpn",
        "docs",
        "output"
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_files or missing_dirs:
        print("❌ Missing required files/directories:")
        for item in missing_files + missing_dirs:
            print(f"   - {item}")
        return False
    
    print("✅ All required files and directories found")
    return True


def create_config_if_missing():
    """Create a basic config file if it doesn't exist"""
    config_path = Path("config/sources.yaml")
    if not config_path.exists():
        print("📝 Creating basic configuration file...")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        basic_config = """# StreamlineVPN Sources Configuration
sources:
  free:
    - "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt"
    - "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt"
    - "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2"
  
  premium:
    # Add your premium sources here
    # - "https://your-premium-source.com/subscription"
  
  custom:
    # Add your custom sources here
    # - "https://your-custom-source.com/config"

# Processing options
options:
  max_connections: 10
  timeout: 30
  retry_attempts: 3
  cache_duration: 3600
"""
        
        config_path.write_text(basic_config)
        print(f"✅ Created {config_path}")


def start_services():
    """Start the StreamlineVPN services"""
    print("🚀 Starting StreamlineVPN services...")
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("✅ Docker is available")
        
        # Start with Docker Compose
        print("🐳 Starting services with Docker Compose...")
        subprocess.run(["docker-compose", "up", "-d"], check=True)
        
        print("⏳ Waiting for services to start...")
        time.sleep(10)
        
        # Check service health
        print("🔍 Checking service health...")
        result = subprocess.run([
            "docker-compose", "ps"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Docker not available, starting services manually...")
        start_manual_services()


def start_manual_services():
    """Start services manually without Docker"""
    print("🔧 Starting services manually...")
    
    # Start API server
    print("📡 Starting API server...")
    api_process = subprocess.Popen([
        sys.executable, "run_unified.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(3)
    
    # Start web server
    print("🌐 Starting web server...")
    web_process = subprocess.Popen([
        sys.executable, "run_web.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(3)
    
    print("✅ Services started manually")
    print("📡 API Server: http://localhost:8080")
    print("🌐 Web Interface: http://localhost:8000")
    print("🎛️  Control Panel: http://localhost:8000/interactive.html")
    
    return api_process, web_process


def test_connection():
    """Test if services are responding"""
    import requests
    
    print("🧪 Testing service connections...")
    
    # Test API
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ API server is responding")
        else:
            print(f"⚠️  API server returned status {response.status_code}")
    except Exception as e:
        print(f"❌ API server not responding: {e}")
    
    # Test Web
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        if response.status_code == 200:
            print("✅ Web server is responding")
        else:
            print(f"⚠️  Web server returned status {response.status_code}")
    except Exception as e:
        print(f"❌ Web server not responding: {e}")


def main():
    """Main startup function"""
    print("🎯 StreamlineVPN Startup Script")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please ensure all required files are present")
        sys.exit(1)
    
    # Create config if missing
    create_config_if_missing()
    
    # Start services
    start_services()
    
    # Test connections
    test_connection()
    
    print("\n🎉 StreamlineVPN is ready!")
    print("\n📋 Quick Start Guide:")
    print("1. Open your browser and go to: http://localhost:8000/interactive.html")
    print("2. Click 'Test Connection' to verify API connectivity")
    print("3. Go to the 'Process' tab and click 'Start Processing'")
    print("4. Monitor progress in the 'Terminal' tab")
    print("5. View results in the 'Configurations' tab")
    
    print("\n🔧 Management Commands:")
    print("- View logs: docker-compose logs -f")
    print("- Stop services: docker-compose down")
    print("- Restart services: docker-compose restart")
    
    print("\n📚 Documentation:")
    print("- API Docs: http://localhost:8080/docs")
    print("- Health Check: http://localhost:8080/health")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
