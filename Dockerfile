# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    gnupg \
    lsb-release \
    build-essential \
    libsndfile1 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (16.x)
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs

# Verify installation of Node.js
RUN echo "Checking Node.js installation..." \
    && node -v \
    && npm -v

# Set working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .

# Install ntgcalls first (make sure it is compatible with the current Python version)
RUN pip install --no-cache-dir ntgcalls

# Install Python dependencies from requirements.txt (which includes py-tgcalls)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code into the container
COPY . .

# Run the bot or application
CMD ["python", "main.py"]