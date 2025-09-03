@echo off
REM Cloudflare WS+TLS Fallback Pack Setup Script for Windows
REM This script helps you set up the deployment pack quickly

echo 🚀 Cloudflare WS+TLS Fallback Pack Setup
echo ========================================

REM Check if .env exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env.example .env
    echo ✅ Created .env file
    echo ⚠️  Please edit .env with your domain and UUID before continuing
    echo.
    echo Required changes:
    echo 1. Set DOMAIN to your actual domain (e.g., vpn.yourdomain.com)
    echo 2. Generate a UUID (use PowerShell: [System.Guid]::NewGuid())
    echo.
    pause
)

REM Check if certificates exist
if not exist certs\origin.crt (
    echo 🔐 Missing Cloudflare Origin Certificates
    echo Please follow these steps:
    echo 1. Go to Cloudflare Dashboard → SSL/TLS → Origin Server
    echo 2. Create a new Origin Certificate
    echo 3. Download the certificate and private key
    echo 4. Save them as certs\origin.crt and certs\origin.key
    echo.
    echo See certs\README.md for detailed instructions
    echo.
    pause
)

if not exist certs\origin.key (
    echo 🔐 Missing Cloudflare Origin Private Key
    echo Please place certs\origin.key file
    echo.
    pause
)

echo ✅ Configuration validated
echo.

REM Pull Docker images
echo 📦 Pulling Docker images...
docker compose pull

REM Start services
echo 🚀 Starting services...
docker compose up -d

echo.
echo 🎉 Setup complete!
echo.
echo Your services are now running:
echo - Nginx: http://yourdomain.com (redirects to HTTPS)
echo - Nginx: https://yourdomain.com (main site)
echo - VLESS WebSocket: wss://yourdomain.com/ws
echo.
echo Health checks:
echo curl -I http://yourdomain.com/health
echo curl -I https://yourdomain.com/health
echo.
echo View logs:
echo docker compose logs -f nginx
echo docker compose logs -f xray
echo.
echo Client configuration:
echo vless://YOUR_UUID@yourdomain.com:443?encryption=none^&security=tls^&type=ws^&path=%%2Fws^&sni=yourdomain.com#CF-WS
echo.
pause
