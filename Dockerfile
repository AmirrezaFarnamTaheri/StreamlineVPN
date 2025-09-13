# StreamlineVPN Production-ready Multi-stage Docker Build
# ========================================================

# Build stage for dependencies
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libssl-dev \
    libffi-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files with fallback handling
COPY requirements*.txt ./
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    if [ -f requirements-prod.txt ]; then \
        pip install --no-cache-dir -r requirements-prod.txt; \
    fi

# Production stage
FROM python:3.11-slim AS production

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code with proper structure
COPY src/ ./src/
COPY config/ ./config/
COPY docs/ ./docs/
COPY scripts/ ./scripts/
COPY run_unified.py run_api.py run_web.py cli.py ./

# Create necessary directories with proper permissions
RUN mkdir -p /app/output /app/logs /app/cache /app/data && \
    chmod 755 /app/output /app/logs /app/cache /app/data

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --user-group --uid 1000 streamline && \
    chown -R streamline:streamline /app

# Switch to non-root user
USER streamline

# Health check with fallback endpoints
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${API_PORT:-8080}/health || \
        curl -f http://localhost:${API_PORT:-8080}/api/v1/health || \
        exit 1

# Environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/src" \
    STREAMLINE_ENV=production \
    API_HOST=0.0.0.0 \
    API_PORT=8080 \
    WEB_HOST=0.0.0.0 \
    WEB_PORT=8000

# Expose ports
EXPOSE 8080 8000

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Default command with proper error handling
CMD ["python", "run_unified.py"]

