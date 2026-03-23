# Start with the base Python image (3.10-slim)
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
RUN pip uninstall -y ntgcalls && pip install ntgcalls

# Install py-tgcalls as an alternative in case ntgcalls still doesn't work
RUN pip install py-tgcalls

# Install aiofiles==0.8.0 explicitly if needed
RUN pip install aiofiles==0.8.0

# Install any other necessary dependencies (in case of missing packages)
RUN pip install --upgrade pip

# Replace the `InputMode` import from `ntgcalls` with an alternative if needed
RUN sed -i 's/from ntgcalls import InputMode/from py_tgcalls import InputMode/g' /app/main.py

# Copy the rest of your application code
COPY . .

# Set the entrypoint for your app (update as per your application entry point)
CMD ["python", "main.py"]