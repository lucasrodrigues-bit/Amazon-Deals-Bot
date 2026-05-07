FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir -e .

COPY . .

ENV PYTHONPATH=/app/src

COPY scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["/app/entrypoint.sh"]