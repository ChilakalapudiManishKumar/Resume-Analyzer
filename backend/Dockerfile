# Backend — FastAPI + ML models
# NOTE: build context is the PROJECT ROOT (see docker-compose.yml), not
# backend/ — this is what lets us COPY the shared data/ folder in below.
FROM python:3.12-slim

WORKDIR /app

# System deps: psycopg2 needs libpq at build+runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY data/ /app/data

# Overrides the relative-path guess in app/core/paths.py — see that file
# for why this matters (container layout differs from local dev layout).
ENV APP_DATA_DIR=/app/data

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
