# syntax=docker/dockerfile:1.4

# Use an alpine-based Python image for the build stage
FROM --platform=$BUILDPLATFORM python:3.11-alpine AS builder

# Set working directory in container
WORKDIR /src

# Install system dependencies (for libraries like OpenCV, etc.)
RUN apk add --no-cache \
    build-base \
    libmagic \
    git \
    libffi-dev \
    && apk add --no-cache --virtual .build-deps gcc musl-dev

# Copy requirements.txt and install Python dependencies
COPY requirements.txt /src
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Final image build
FROM python:3.11-alpine AS final

# Set working directory in container
WORKDIR /src

# Install system dependencies for runtime (same as builder + others like OpenCV)
RUN apk add --no-cache \
    libmagic \
    libffi-dev \
    && apk add --no-cache --virtual .runtime-deps \
    opencv-dev \
    libpng-dev \
    libjpeg-turbo-dev

# Copy the installed Python environment and application files from the builder
COPY --from=builder /src /src

# Expose port 5000 (Flask default)
EXPOSE 5000

# Set environment variables for Flask (useful for production settings)
ENV FLASK_APP=server.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# Run the application
CMD ["python3", "appfix.py"]
