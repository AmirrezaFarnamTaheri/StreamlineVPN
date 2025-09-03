#!/bin/bash

# Cloudflare WS+TLS Fallback Pack Setup Script
# This script helps you set up the deployment pack quickly

set -e

echo "🚀 Cloudflare WS+TLS Fallback Pack Setup"
echo "========================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env with your domain and UUID before continuing"
    echo ""
    echo "Required changes:"
    echo "1. Set DOMAIN to your actual domain (e.g., vpn.yourdomain.com)"
    echo "2. Generate a UUID (run 'uuidgen' on Linux/macOS)"
    echo ""
    read -p "Press Enter after editing .env file..."
fi

# Check if certificates exist
if [ ! -f certs/origin.crt ] || [ ! -f certs/origin.key ]; then
    echo "🔐 Missing Cloudflare Origin Certificates"
    echo "Please follow these steps:"
    echo "1. Go to Cloudflare Dashboard → SSL/TLS → Origin Server"
    echo "2. Create a new Origin Certificate"
    echo "3. Download the certificate and private key"
    echo "4. Save them as certs/origin.crt and certs/origin.key"
    echo ""
    echo "See certs/README.md for detailed instructions"
    echo ""
    read -p "Press Enter after placing certificates in certs/ directory..."
fi

# Validate .env file
source .env
if [ "$DOMAIN" = "vpn.example.com" ] || [ "$UUID" = "00000000-0000-4000-9000-000000000000" ]; then
    echo "❌ Please update .env file with your actual domain and UUID"
    exit 1
fi

echo "✅ Configuration validated"
echo ""

# Pull Docker images
echo "📦 Pulling Docker images..."
docker compose pull

# Start services
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Your services are now running:"
echo "- Nginx: http://$DOMAIN (redirects to HTTPS)"
echo "- Nginx: https://$DOMAIN (main site)"
echo "- VLESS WebSocket: wss://$DOMAIN/ws"
echo ""
echo "Health checks:"
echo "curl -I http://$DOMAIN/health"
echo "curl -I https://$DOMAIN/health"
echo ""
echo "View logs:"
echo "docker compose logs -f nginx"
echo "docker compose logs -f xray"
echo ""
echo "Client configuration:"
echo "vless://$UUID@$DOMAIN:443?encryption=none&security=tls&type=ws&path=%2Fws&sni=$DOMAIN#CF-WS"
