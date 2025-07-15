FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_DIR=/app/logs
ENV LOG_TO_CONSOLE=true
ENV LOG_TO_FILE=true

# Expose port (if using Flask web interface)
EXPOSE 5000

# Default command - can be overridden
CMD ["python", "engine_dag.py"]