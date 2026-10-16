FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered log streaming
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dedicated non-root user (UID 1000 matches the Helm securityContext)
RUN groupadd -r -g 1000 appuser && useradd -r -u 1000 -g appuser appuser

# Install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Alembic config, migrations, and application code
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY app/ ./app/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Wait for the database, apply migrations, then start the API
CMD ["sh", "-c", "python -m app.wait_for_db && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
