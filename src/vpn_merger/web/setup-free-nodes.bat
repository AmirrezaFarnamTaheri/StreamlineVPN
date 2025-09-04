@echo off
setlocal enabledelayedexpansion

echo 🚀 Setting up Enhanced Free Nodes Aggregator...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not available. Please ensure Docker Desktop is running.
    pause
    exit /b 1
)

REM Create data directory
echo 📁 Creating data directory...
if not exist "data" mkdir data

REM Check if we have the required files
if not exist "free_nodes_api_sqla.py" (
    echo ❌ free_nodes_api_sqla.py not found in current directory
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ❌ requirements.txt not found in current directory
    pause
    exit /b 1
)

if not exist "Dockerfile" (
    echo ❌ Dockerfile not found in current directory
    pause
    exit /b 1
)

if not exist "compose.free-nodes.yml" (
    echo ❌ compose.free-nodes.yml not found in current directory
    pause
    exit /b 1
)

REM Build and start the service
echo 🔨 Building and starting Free Nodes Aggregator...
docker-compose -f compose.free-nodes.yml up -d --build

REM Wait for service to be ready
echo ⏳ Waiting for service to be ready...
timeout /t 10 /nobreak >nul

REM Test the service
echo 🧪 Testing the service...
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Service failed to start properly
    echo 📋 Check logs with: docker-compose -f compose.free-nodes.yml logs -f
    pause
    exit /b 1
)

echo ✅ Service is running successfully!
echo.
echo 🌐 Service URL: http://localhost:8000
echo 📊 Health Check: http://localhost:8000/health
echo 📋 API Docs: http://localhost:8000/docs
echo.
echo 📝 Next steps:
echo 1. Add sources: POST /api/sources
echo 2. Trigger refresh: POST /api/refresh
echo 3. Get nodes: GET /api/nodes.json
echo.
echo 📁 Data is stored in: ./data/free-nodes.db
echo 🔄 Auto-refresh every 20 minutes
echo 🌙 Nightly pruning at 03:15
echo.
echo 🎉 Setup complete! The Enhanced Free Nodes Aggregator is now running.

pause
