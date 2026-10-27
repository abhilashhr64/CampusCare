# Multi-stage production Dockerfile for CampusCare AI Backend
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final runtime image
FROM python:3.12-slim AS runner

WORKDIR /app

# Install curl for container health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r campuscare && useradd -r -g campuscare -u 1001 campuscare

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source and configuration
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY src /app/src

# Set ownership
RUN chown -R campuscare:campuscare /app

USER campuscare

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/system/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
