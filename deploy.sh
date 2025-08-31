#!/bin/bash
# VPN Subscription Merger - Production Deployment Script

echo "🚀 VPN Subscription Merger - Production Deployment"
echo "=================================================="

# Check Python environment
echo "📋 Checking Python environment..."
python --version
if [ $? -ne 0 ]; then
    echo "❌ Python not found. Please install Python 3.8+"
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."
python -c "import aiohttp, yaml, asyncio; print('✅ All dependencies available')"
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
fi

# Verify core functionality
echo "🔍 Verifying core functionality..."
python -c "from vpn_merger import VPNSubscriptionMerger, SourceManager; print('✅ Core components verified')"
if [ $? -ne 0 ]; then
    echo "❌ Core components failed to load"
    exit 1
fi

# Check sources
echo "📊 Checking sources..."
python -c "from vpn_merger import SourceManager; s = SourceManager(); print(f'✅ Sources loaded: {len(s.get_all_sources())}')"

# Create output directory
echo "📁 Setting up output directory..."
mkdir -p output

# Run production deployment
echo "🚀 Starting production deployment..."
python scripts/deploy_production.py

if [ $? -eq 0 ]; then
    echo "✅ Production deployment completed successfully!"
    echo ""
    echo "📊 Generated files:"
    ls -la output/
    echo ""
    echo "🎉 System is ready for production use!"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Monitor performance: python scripts/monitor_performance.py monitor"
    echo "  2. Run full test: python scripts/monitor_performance.py test"
    echo "  3. Generate report: python scripts/monitor_performance.py report"
else
    echo "❌ Production deployment failed"
    exit 1
fi
