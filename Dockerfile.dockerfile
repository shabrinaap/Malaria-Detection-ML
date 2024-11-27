# Start from a Python Alpine image
FROM python:3.10-alpine

# Set environment variables (to prevent Python from writing .pyc files and set default encoding)
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Install system dependencies including OpenGL libraries
RUN apk update && \
    apk add --no-cache libgl mesa-gl

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app/

# Install Python dependencies from requirements.txt
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    gfortran \
    libatlas-base-dev \
    liblapack-dev \
    libblas-dev \
    python3-dev

RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the Flask app will run on
EXPOSE 8080

# Command to run the Flask app (replace with your entry point)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "app:app"]
