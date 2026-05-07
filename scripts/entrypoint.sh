#!/bin/bash
set -e

echo "[entrypoint] running database migrations..."
alembic upgrade head

echo "[entrypoint] starting bot..."
exec python -m amazon_deals_bot.main