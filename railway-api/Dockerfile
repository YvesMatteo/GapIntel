FROM python:3.11-slim

# Install system dependencies for whisper/ffmpeg/xgboost/opencv
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    libgomp1 \
    libsm6 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

ENV OPENBLAS_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OMP_NUM_THREADS=1
ENV NUMEXPR_NUM_THREADS=1
ENV VECLIB_MAXIMUM_THREADS=1

WORKDIR /app

# Install PyTorch CPU-only first to save space/time and avoid OOM
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Expose port
EXPOSE 8000

# Run the API
CMD ["python", "server.py"]
