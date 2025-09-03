@echo off
REM Free Nodes Aggregator API Startup Script for Windows
REM ----------------------------------------------------

setlocal enabledelayedexpansion

REM Colors for output (Windows 10+)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Configuration
set "API_PORT=%API_PORT%"
if "%API_PORT%"=="" set "API_PORT=8000"

set "API_HOST=%API_HOST%"
if "%API_HOST%"=="" set "API_HOST=0.0.0.0"

set "WORKERS=%WORKERS%"
if "%WORKERS%"=="" set "WORKERS=4"

set "LOG_LEVEL=%LOG_LEVEL%"
if "%LOG_LEVEL%"=="" set "LOG_LEVEL=info"

REM Function to log messages
:log
echo %GREEN%[%date% %time%] %~1%NC%
goto :eof

REM Function to show error
:error
echo %RED%[ERROR] %~1%NC%
exit /b 1

REM Function to show warning
:warning
echo %YELLOW%[WARNING] %~1%NC%
goto :eof

REM Function to show info
:info
echo %BLUE%[INFO] %~1%NC%
goto :eof

REM Check if Python is available
call :log "Checking Python installation..."
python --version >nul 2>&1
if errorlevel 1 (
    call :error "Python is required but not installed"
    pause
    exit /b 1
)

REM Check if pip is available
call :log "Checking pip installation..."
pip --version >nul 2>&1
if errorlevel 1 (
    call :error "pip is required but not installed"
    pause
    exit /b 1
)

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    call :error "requirements.txt not found"
    pause
    exit /b 1
)

REM Check if free_nodes_api.py exists
if not exist "free_nodes_api.py" (
    call :error "free_nodes_api.py not found"
    pause
    exit /b 1
)

REM Create data directory
call :log "Creating data directory..."
if not exist "data" mkdir data

REM Install dependencies
call :log "Installing Python dependencies..."
pip install -r requirements.txt
if errorlevel 1 (
    call :error "Failed to install dependencies"
    pause
    exit /b 1
)

REM Check if port is available
call :log "Checking port availability..."
netstat -an | find ":%API_PORT% " >nul
if not errorlevel 1 (
    call :warning "Port %API_PORT% is already in use"
    set /p "CONTINUE=Continue anyway? (y/N): "
    if /i not "!CONTINUE!"=="y" (
        call :log "Exiting..."
        pause
        exit /b 1
    )
)

REM Show configuration
call :log "Configuration:"
call :info "  Port: %API_PORT%"
call :info "  Host: %API_HOST%"
call :info "  Workers: %WORKERS%"
call :info "  Log Level: %LOG_LEVEL%"
echo.

REM Start the API
call :log "Starting Free Nodes Aggregator API..."
call :info "API will be available at: http://%API_HOST%:%API_PORT%"
call :info "API documentation at: http://%API_HOST%:%API_PORT%/docs"
echo.

uvicorn free_nodes_api:app --host %API_HOST% --port %API_PORT% --workers %WORKERS% --log-level %LOG_LEVEL% --access-log --reload

REM If we get here, the service stopped
call :log "Service stopped"
pause
