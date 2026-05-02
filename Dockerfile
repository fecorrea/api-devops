# ===== ETAPA 1: CONSTRUCCION =====
FROM python:3.11-slim as builder

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt && \
    find /root/.local -type f -name '*.pyc' -delete && \
    find /root/.local -type d -name '__pycache__' -delete


# ===== ETAPA 2: EJECUCION =====
FROM python:3.11-slim

LABEL org.opencontainers.image.title="DevOps API" \
      org.opencontainers.image.description="Secure REST API with JWT and API Key authentication" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.url="https://github.com/fecorrea/api-devops" \
    org.opencontainers.image.source="https://github.com/fecorrea/api-devops" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="DevOps fcorrea"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    PYTHONPATH=/app/src \
    LOG_LEVEL=INFO

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 1000 appuser && \
    useradd --system --uid 1000 --gid appuser --home-dir /home/appuser appuser && \
    mkdir -p /home/appuser && \
    chown -R appuser:appuser /home/appuser /app

COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

COPY --chown=appuser:appuser ./src ./src
COPY --chown=appuser:appuser ./test ./test

RUN mkdir -p /app/data && \
    touch /app/data/replay_store.db && \
    chown -R appuser:appuser /app/data /app/src

HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=10s \
    CMD curl -f http://localhost:8000/health || exit 1

USER appuser

EXPOSE 8000

RUN chmod -R 755 /app/src

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]