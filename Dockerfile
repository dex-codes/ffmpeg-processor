# Multi-stage Dockerfile for Cloud Run video processing service
# Optimized for FFmpeg and Python dependencies

# Stage 1: Build stage with FFmpeg compilation
FROM ubuntu:22.04 as ffmpeg-builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    yasm \
    nasm \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Download and compile FFmpeg with essential codecs
WORKDIR /tmp
RUN wget https://ffmpeg.org/releases/ffmpeg-6.0.tar.xz && \
    tar -xf ffmpeg-6.0.tar.xz && \
    cd ffmpeg-6.0 && \
    ./configure \
        --enable-gpl \
        --enable-libx264 \
        --enable-libx265 \
        --enable-libvpx \
        --enable-libfdk-aac \
        --enable-libmp3lame \
        --enable-libopus \
        --enable-nonfree \
        --disable-debug \
        --disable-doc \
        --disable-ffplay \
        --prefix=/usr/local && \
    make -j$(nproc) && \
    make install

# Stage 2: Runtime stage
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libx264-164 \
    libx265-199 \
    libvpx7 \
    libfdk-aac2 \
    libmp3lame0 \
    libopus0 \
    && rm -rf /var/lib/apt/lists/*

# Copy FFmpeg from builder stage
COPY --from=ffmpeg-builder /usr/local/bin/ffmpeg /usr/local/bin/
COPY --from=ffmpeg-builder /usr/local/bin/ffprobe /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-cloudrun.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-cloudrun.txt

# Copy application code
COPY main.py .
COPY cloud_storage.py .
COPY video_processing_service.py .
COPY job_manager.py .
COPY video_processor.py .
COPY video_config.py .

# Create necessary directories
RUN mkdir -p /tmp/video_processing /tmp/video_jobs

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
