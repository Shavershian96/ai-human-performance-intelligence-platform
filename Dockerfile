# AI Human Performance Intelligence Platform - API
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Unprivileged runtime user. /app/models is the mount point for the shared
# model volume, so it has to be owned by that user in the image - Docker seeds
# a new named volume with the ownership of the directory it shadows.
RUN useradd --create-home --uid 10001 appuser

# Copy application
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/models && chown -R appuser:appuser /app/models

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
