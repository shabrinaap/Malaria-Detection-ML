FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    gfortran \
    libatlas-base-dev \
    liblapack-dev \
    libblas-dev \
    libxcrypt-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment and install Python dependencies
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip and setuptools to ensure precompiled wheels
RUN pip install --upgrade pip setuptools wheel

# Copy application files and install dependencies
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "app.py"]
