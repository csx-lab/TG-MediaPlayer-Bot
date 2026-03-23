# Start with the base image
FROM python:3.10-slim

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

# Install Node.js (as required by your project)
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs

# Check Node.js installation
RUN echo "Checking Node.js installation..." \
    && node -v \
    && npm -v

# Set up a virtual environment
RUN python -m venv /env
ENV PATH="/env/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Reinstall ntgcalls explicitly to avoid any potential issues
RUN pip uninstall -y ntgcalls \
    && pip install ntgcalls

# Install py-tgcalls as an alternative in case ntgcalls still causes issues
RUN pip install py-tgcalls

# Install additional Python dependencies if required
RUN pip install aiofiles==0.8.0

# Copy the rest of your application code
COPY . .

# Set the entrypoint for your app (update as per your application entry point)
CMD ["python", "main.py"]