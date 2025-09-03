#!/bin/bash

# Free Nodes Aggregator API Startup Script
# -----------------------------------------

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_PORT=${API_PORT:-8000}
API_HOST=${API_HOST:-0.0.0.0}
WORKERS=${WORKERS:-4}
LOG_LEVEL=${LOG_LEVEL:-info}

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Function to check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    log "Python version: $PYTHON_VERSION"
}

# Function to check if pip is available
check_pip() {
    if ! command -v pip3 &> /dev/null; then
        error "pip3 is required but not installed"
    fi
    
    log "pip3 is available"
}

# Function to install dependencies
install_dependencies() {
    log "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
        log "Dependencies installed successfully"
    else
        error "requirements.txt not found"
    fi
}

# Function to create data directory
create_data_dir() {
    log "Creating data directory..."
    
    mkdir -p data
    log "Data directory created"
}

# Function to check if port is available
check_port() {
    if command -v netstat &> /dev/null; then
        if netstat -tlnp 2>/dev/null | grep -q ":$API_PORT "; then
            warning "Port $API_PORT is already in use"
            return 1
        fi
    elif command -v ss &> /dev/null; then
        if ss -tlnp 2>/dev/null | grep -q ":$API_PORT "; then
            warning "Port $API_PORT is already in use"
            return 1
        fi
    fi
    
    log "Port $API_PORT is available"
    return 0
}

# Function to start the API
start_api() {
    log "Starting Free Nodes Aggregator API..."
    
    # Check if free_nodes_api.py exists
    if [ ! -f "free_nodes_api.py" ]; then
        error "free_nodes_api.py not found"
    fi
    
    # Start the API with uvicorn
    exec uvicorn free_nodes_api:app \
        --host "$API_HOST" \
        --port "$API_PORT" \
        --workers "$WORKERS" \
        --log-level "$LOG_LEVEL" \
        --access-log \
        --reload
}

# Function to start with Docker
start_docker() {
    log "Starting with Docker Compose..."
    
    if [ ! -f "docker-compose.yml" ]; then
        error "docker-compose.yml not found"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is required but not installed"
    fi
    
    docker-compose up -d
    log "Docker container started"
    
    # Wait for service to be ready
    log "Waiting for service to be ready..."
    sleep 5
    
    # Check health
    if curl -f http://localhost:$API_PORT/health >/dev/null 2>&1; then
        log "Service is healthy"
    else
        warning "Service health check failed"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -d, --docker        Start with Docker Compose"
    echo "  -p, --port PORT     Set API port (default: 8000)"
    echo "  -w, --workers NUM   Set number of workers (default: 4)"
    echo "  -l, --log-level LVL Set log level (default: info)"
    echo
    echo "Environment variables:"
    echo "  API_PORT            API port (default: 8000)"
    echo "  API_HOST            API host (default: 0.0.0.0)"
    echo "  WORKERS             Number of workers (default: 4)"
    echo "  LOG_LEVEL           Log level (default: info)"
    echo
    echo "Examples:"
    echo "  $0                    # Start with default settings"
    echo "  $0 --docker           # Start with Docker"
    echo "  $0 --port 9000        # Start on port 9000"
    echo "  API_PORT=9000 $0      # Start on port 9000 (env var)"
}

# Main function
main() {
    # Parse command line arguments
    USE_DOCKER=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -d|--docker)
                USE_DOCKER=true
                shift
                ;;
            -p|--port)
                API_PORT="$2"
                shift 2
                ;;
            -w|--workers)
                WORKERS="$2"
                shift 2
                ;;
            -l|--log-level)
                LOG_LEVEL="$2"
                shift 2
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    # Show configuration
    log "Configuration:"
    log "  Port: $API_PORT"
    log "  Host: $API_HOST"
    log "  Workers: $WORKERS"
    log "  Log Level: $LOG_LEVEL"
    log "  Docker: $USE_DOCKER"
    echo
    
    # Check prerequisites
    check_python
    check_pip
    
    # Check port availability
    if ! check_port; then
        warning "Port $API_PORT is already in use. You may need to stop the existing service."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Create data directory
    create_data_dir
    
    if [ "$USE_DOCKER" = true ]; then
        start_docker
    else
        # Install dependencies
        install_dependencies
        
        # Start the API
        start_api
    fi
}

# Run main function
main "$@"
