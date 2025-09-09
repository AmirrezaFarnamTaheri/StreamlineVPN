# Multi-stage build for StreamlineVPN

# Stage 1: Builder
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash streamline

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/streamline/.local

# Copy application code
COPY --chown=streamline:streamline . .

# Create necessary directories
RUN mkdir -p /app/output /app/logs /app/data /app/cache \
    && chown -R streamline:streamline /app

# Switch to non-root user
USER streamline

# Add local bin to PATH
ENV PATH=/home/streamline/.local/bin:$PATH

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV VPN_ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8080 8000

# Default command
CMD ["python", "run_server.py"]