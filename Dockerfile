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
RUN pip install --no-cache-dir --user -r requirements-prod.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/output /app/logs && \
    chmod 755 /app/output /app/logs

# Health check against REST API endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose ports
# 8000: Main API
# 8001: Metrics endpoint
EXPOSE 8000 8001

# Create and switch to non-root user for security
RUN useradd -m -u 1000 merger && \
    chown -R merger:merger /app
USER merger

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV VPN_MERGER_OUTPUT_DIR=/app/output
ENV VPN_MERGER_LOG_DIR=/app/logs
ENV PYTHONPATH=/app

# Default command - run the merger as a module
CMD ["python", "-m", "vpn_merger"]


