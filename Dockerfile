FROM python:3.10-slim



# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    python3-dev \
    gcc \
    gfortran \
    libatlas-base-dev \
    liblapack-dev \
    libblas-dev \
    # libxcrypt-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment and install Python dependencies
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip and setuptools to ensure precompiled wheels
COPY . /app
WORKDIR /app
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
