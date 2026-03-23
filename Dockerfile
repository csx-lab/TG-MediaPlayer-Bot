# Use the official Python 3.10 slim image as the base image
FROM python:3.10-slim

# Set environment variables (adjust these as needed)
ENV PYTHONUNBUFFERED=1

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    gnupg \
    lsb-release \
    build-essential \
    libsndfile1 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (since you also need it based on your initial setup)
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs

# --- Check if Node.js and npm are installed properly ---
RUN echo "Checking Node.js installation..." && \
    node -v && \
    npm -v

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Ensure virtual environment is created and activated ---
RUN python -m venv /env

# --- Install dependencies into virtual environment ---
RUN /env/bin/pip install --no-cache-dir -r requirements.txt

# --- Ensure py_tgcalls is installed if it’s a local module or PyPI package ---
# Option 1: Install py_tgcalls from PyPI (if available)
RUN pip install py_tgcalls==<version>  # Replace with the correct version if needed

# Option 2: If py_tgcalls is a local package, copy and install it
# COPY py_tgcalls /app/py_tgcalls
# RUN pip install /app/py_tgcalls

# Copy the application code into the container
COPY . .

# --- Ensure all relevant imports are patched ---
RUN find /env/lib/python3.10/site-packages/pytgcalls -type f -name "*.py" -exec sed -i 's/from ntgcalls import InputMode/from py_tgcalls import InputMode/g' {} \;

# Set the entrypoint for the application
CMD ["/env/bin/python", "main.py"]