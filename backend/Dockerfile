FROM python:3.10-alpine

# Install ffmpeg and required dependencies
RUN apk add --no-cache \
    ffmpeg \
    gcc \
    musl-dev \
    linux-headers

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create directories for videos and captions
RUN mkdir -p /app/videos /app/captions

# Expose port
EXPOSE 8001

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV VIDEOS_DIR=/app/videos
ENV CAPTIONS_DIR=/app/captions

# Run the application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT:-8011}"]

