# Start from Python 3.11 base image
FROM python:3.11-slim

# Set environment variables to non-interactive mode for apt-get
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies, including FFmpeg and Node.js (v15+)
RUN apt-get update && \
    apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (v15+)
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs

# Verify node and npm installation
RUN node -v && npm -v

# Create and set the working directory for the bot
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project files
COPY . /app

# Expose the necessary port for your bot (usually 80 or 5000)
EXPOSE 80

# Ensure Node.js is installed and visible
RUN python3 -c "import subprocess; subprocess.check_call(['node', '-v'])"

# Run your main.py file using Python
CMD ["python3", "main.py"]