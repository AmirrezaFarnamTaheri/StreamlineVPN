#!/bin/bash

# Free Nodes Aggregator Setup Script
# This script sets up the enhanced Free Nodes Aggregator with SQLite persistence

set -e

echo "🚀 Setting up Enhanced Free Nodes Aggregator..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create data directory
echo "📁 Creating data directory..."
mkdir -p ./data

# Check if we have the required files
if [ ! -f "free_nodes_api_sqla.py" ]; then
    echo "❌ free_nodes_api_sqla.py not found in current directory"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found in current directory"
    exit 1
fi

if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found in current directory"
    exit 1
fi

if [ ! -f "compose.free-nodes.yml" ]; then
    echo "❌ compose.free-nodes.yml not found in current directory"
    exit 1
fi

# Build and start the service
echo "🔨 Building and starting Free Nodes Aggregator..."
docker-compose -f compose.free-nodes.yml up -d --build

# Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 10

# Test the service
echo "🧪 Testing the service..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Service is running successfully!"
    echo ""
    echo "🌐 Service URL: http://localhost:8000"
    echo "📊 Health Check: http://localhost:8000/health"
    echo "📋 API Docs: http://localhost:8000/docs"
    echo ""
    echo "📝 Next steps:"
    echo "1. Add sources: POST /api/sources"
    echo "2. Trigger refresh: POST /api/refresh"
    echo "3. Get nodes: GET /api/nodes.json"
    echo ""
    echo "📁 Data is stored in: ./data/free-nodes.db"
    echo "🔄 Auto-refresh every 20 minutes"
    echo "🌙 Nightly pruning at 03:15"
else
    echo "❌ Service failed to start properly"
    echo "📋 Check logs with: docker-compose -f compose.free-nodes.yml logs -f"
    exit 1
fi

echo ""
echo "🎉 Setup complete! The Enhanced Free Nodes Aggregator is now running."
