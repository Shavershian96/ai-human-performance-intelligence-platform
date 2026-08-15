# AI Human Performance Intelligence Platform - API
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
# Refresh the packaging toolchain the base image ships: its bundled
# setuptools/wheel carry known HIGH CVEs that the Trivy gate rejects.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Strip pip from the runtime image. Nothing installs packages at run time, and
# pip ships a private _vendor tree (msgpack, setuptools) that image scanners
# flag and that cannot be upgraded independently of pip itself. Removing it
# drops the finding at source rather than suppressing it, and shrinks the
# attack surface.
RUN rm -rf /usr/local/lib/python3.11/site-packages/pip            /usr/local/lib/python3.11/site-packages/pip-*.dist-info            /usr/local/lib/python3.11/ensurepip            /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.11

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
