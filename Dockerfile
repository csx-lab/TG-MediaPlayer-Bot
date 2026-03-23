# Use official Node + Python image
FROM node:20-bullseye

# Set working directory
WORKDIR /app

# Install Python 3.11
RUN apt-get update && \
    apt-get install -y python3.11 python3.11-venv python3.11-dev ffmpeg git && \
    apt-get clean

# Copy project files
COPY . .

# Setup virtualenv
RUN python3.11 -m venv venv
RUN . venv/bin/activate

# Upgrade pip
RUN ./venv/bin/pip install --upgrade pip

# Install requirements
RUN ./venv/bin/pip install -r requirements.txt

# Ensure start.sh is executable
RUN chmod +x start.sh

# Set environment variable for PyTgCalls to find Node
ENV NODE_PATH=/usr/local/lib/node_modules

# Start bot
CMD ["./start.sh"]