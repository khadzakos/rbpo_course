# Build stage
FROM python:3.12-slim AS build
WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY requirements-dev.txt .
RUN pip install --no-cache-dir --user -r requirements-dev.txt

COPY . .

# Runtime stage
FROM python:3.12-slim AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    libmagic1 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /app /app/data && \
    chown -R appuser:appuser /app

WORKDIR /app

COPY --from=build --chown=appuser:appuser /root/.local /home/appuser/.local

COPY --chown=appuser:appuser . .

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HOST=0.0.0.0
ENV PORT=8000

RUN mkdir -p /app/data && chown appuser:appuser /app/data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host ${HOST} --port ${PORT}"]
