# Dockerfile - Production-ready multi-stage build
FROM python:3.11-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .

RUN mkdir -p /app/output && chmod 755 /app/output

# Health check against REST API endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

EXPOSE 8000 8001

# Run as non-root user
RUN useradd -m -u 1000 merger && chown -R merger:merger /app
USER merger

ENV PYTHONUNBUFFERED=1
ENV VPN_MERGER_OUTPUT_DIR=/app/output

CMD ["python", "vpn_merger.py"]


