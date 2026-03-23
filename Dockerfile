# Start with a Python base image
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Install system dependencies for the application
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    gnupg \
    lsb-release \
    build-essential \
    libsndfile1 \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (16.x version)
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - \
    && apt-get install -y nodejs

# Verify the Node.js and npm installation
RUN echo "Checking Node.js installation..." \
    && node -v \
    && npm -v

# Install Python dependencies (you can adjust the requirements.txt as needed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install pytgcalls and other dependencies for the bot
RUN pip install pytgcalls pyrogram

# Copy your application code into the container
COPY . /app

# Expose the necessary port for the bot (if needed, adjust this for your app)
EXPOSE 8080

# Set environment variables if necessary (e.g., for Telegram bot token)
# ENV TELEGRAM_API_TOKEN="your_telegram_api_token"
# ENV TELEGRAM_APP_ID="your_app_id"
# ENV TELEGRAM_APP_HASH="your_app_hash"

# Make sure the start script is executable (optional, adjust based on your code)
RUN chmod +x /app/main.py

# Command to run your bot (adjust this to run your bot, for example with Python)
CMD ["python", "main.py"]