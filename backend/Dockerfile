# ─── Stage 1: Base ────────────────────────────────────────────────────────────
# Use slim Python 3.11 for a small, secure image
FROM python:3.11-slim

# ─── Environment ──────────────────────────────────────────────────────────────
# Prevents Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# ─── System Dependencies ──────────────────────────────────────────────────────
# libpq-dev is required by psycopg2; gcc for compiled packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ─── Working Directory ────────────────────────────────────────────────────────
WORKDIR /app

# ─── Install Python Dependencies ──────────────────────────────────────────────
# Copy requirements first for Docker layer caching — dependencies only
# reinstall when requirements.txt changes, not on every code change.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ─── Copy Application Code ────────────────────────────────────────────────────
COPY . .

# ─── Expose Port ──────────────────────────────────────────────────────────────
EXPOSE 8000

# ─── Startup Command ──────────────────────────────────────────────────────────
# Cloud Run injects $PORT at runtime; fall back to 8000 locally.
# Using shell form so $PORT is evaluated at container start time.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
