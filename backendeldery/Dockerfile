# Dockerfile (located in backendeldery folder, but build context is the repository root)
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

# Install required packages and Poetry
RUN apt-get update && apt-get install -y netcat-openbsd gcc libpq-dev \
    && pip install "poetry==1.5.1" \
    && apt-get clean

# Copy pyproject.toml and poetry.lock from the root (build context)
COPY pyproject.toml poetry.lock* /app/

# Install dependencies via Poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction --no-ansi

# Copy the entire repository (or adjust as needed)
COPY . /app

# Set executable permission on start.sh from the correct location:
RUN chmod +x /app/backendeldery/start.sh

# If your start.sh is intended to be the entrypoint, you can change CMD accordingly:
CMD ["/app/backendeldery/start.sh"]