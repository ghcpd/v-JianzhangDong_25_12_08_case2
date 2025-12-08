# Dockerfile for Security Audit Flask Application
# Builds a containerized environment for testing and running the secure Flask application

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_ENV=production \
    FLASK_DEBUG=False

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    zip \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools && \
    pip install -r requirements.txt

# Copy application files
COPY inputs.py .
COPY input_backup.py .
COPY auto_test.py .
COPY run_test.sh .
COPY .env.example .env

# Copy optional test configuration
COPY report.json . 2>/dev/null || true

# Create necessary directories
RUN mkdir -p logs config data && \
    chmod +x run_test.sh auto_test.py

# Create config directory content
RUN mkdir -p config && \
    cat > config/test.yaml << 'EOF'
# Test configuration file
app:
  name: secure_app
  version: 1.0.0
  debug: false
database:
  file: appdata.db
  timeout: 5000
EOF

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command - run tests
CMD ["python", "auto_test.py"]
