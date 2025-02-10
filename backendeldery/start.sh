#!/bin/sh
set -e

# Wait for Postgres to be available
echo "Waiting for Postgres to be available..."
until nc -z db 5432; do
  echo "Waiting for Postgres..."
  sleep 1
done
echo "Postgres is up!"

# Run the table creation script
echo "Initializing database..."
python /app/backendeldery/create_tables.py

# Start FastAPI using uvicorn
echo "Starting FastAPI..."
uvicorn backendeldery.main:app --host 0.0.0.0 --port 8000 --reload