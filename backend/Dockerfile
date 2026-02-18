FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .[dev]

# Copy application code
COPY . .

# Run migrations and start server (handled by docker-compose command)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
