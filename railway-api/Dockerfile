FROM python:3.11-slim

# Install system dependencies for whisper/ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV CACHE_BUST=3

# Copy all source files
COPY . .

# Expose port
EXPOSE 8000

# Run the API
CMD ["python", "server.py"]
