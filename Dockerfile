# ================================================================
# Zero Touch App — Production Dockerfile
# Base: python:3.11-slim (smaller than 3.9-slim, faster builds)
# Server: Gunicorn (production WSGI — NOT Flask dev server)
# Optimised for AWS EC2 t3.micro (1GB RAM)
# ================================================================

# ── Stage 1: Build dependencies ─────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build deps in a separate layer for cache efficiency
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Production image ────────────────────────────────────
FROM python:3.11-slim

# Create a non-root user for security
RUN groupadd -r zerotouch && useradd -r -g zerotouch zerotouch

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy application code
COPY . .

# Create the instance directory for SQLite DB (will be mounted as volume)
RUN mkdir -p /app/instance && chown -R zerotouch:zerotouch /app

# Switch to non-root user
USER zerotouch

# Expose Flask port
EXPOSE 5000

# ── Health check (Docker native) ─────────────────────────────────
# Docker will restart the container if /health returns non-200
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# ── Start command ─────────────────────────────────────────────────
# 2 workers: conservative for 1GB RAM EC2 (formula: 2*CPU+1 = 3, but RAM-capped)
# --timeout 120: gives DB init time on first boot
# --access-logfile -: sends access logs to stdout (captured by Docker/Jenkins)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "app:app"]