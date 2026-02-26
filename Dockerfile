# ──────────────────────────────────────────────────
# SmartOps Production Dockerfile (Multi-stage build)
# ──────────────────────────────────────────────────
# Architecture Decision:
# Multi-stage build reduces final image size by ~60%.
# Builder stage compiles dependencies; runtime stage
# contains only the compiled artifacts and app code.
# Non-root user prevents container escape attacks.

# ── Stage 1: Builder ──────────────────────────────
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r smartops && useradd -r -g smartops -d /app -s /sbin/nologin smartops

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Change ownership to non-root user
RUN chown -R smartops:smartops /app

USER smartops

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

EXPOSE 8000

# Use gunicorn with config file
CMD ["gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"]
