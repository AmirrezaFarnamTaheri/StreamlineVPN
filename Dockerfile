# VPN Merger - Production-ready Multi-stage Docker Build
# ======================================================

# Build stage for dependencies
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/output /app/logs && \
    chmod 755 /app/output /app/logs

# Health check against REST API endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -sf http://localhost:${API_PORT:-8080}/health || curl -sf http://localhost:${API_PORT:-8080}/api/v1/health || exit 1

# Expose all necessary ports
EXPOSE 8080 8000

# Create and switch to non-root user for security
RUN useradd -m -u 1000 merger && \
    chown -R merger:merger /app
USER merger

# Environment variables for dynamic configuration
ENV HOST=0.0.0.0
ENV API_PORT=8080
ENV WEB_PORT=8000

# Default command - run the API server
CMD ["python", "run_server.py"]
