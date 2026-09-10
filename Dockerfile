# Single lightweight multi-arch Python 3.11 image for Prisma SASE 5G Manager
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr and generating .pyc
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CONFIG_DIR=/app/config \
    PORT=8000

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files and prepare persistent directories
RUN mkdir -p /app/config /app/static
COPY src/ /app/src/
COPY templates/ /app/templates/
COPY static/ /app/static/
COPY app.py /app/app.py
COPY manage_5g.py /app/manage_5g.py
COPY test_lifecycle.py /app/test_lifecycle.py
COPY .env.example /app/.env.example

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/status || exit 1

# Start FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
