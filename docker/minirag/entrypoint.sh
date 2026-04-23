#!/bin/bash
set -e

echo "Running database migrations..."

cd /app/db_models/db_schemes/minirag/
alembic upgrade head
cd /app

exec "$@"
