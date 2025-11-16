FROM python:3.11-slim

# Prevent Python buffering logs
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y \
    build-essential \
    && apt-get clean

# Copy Python files
COPY . /app

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt fastapi uvicorn[standard] aiohttp fastmcp

# Expose port Fly will route to
EXPOSE 8080

# Create persistent data folder (Fly volume mount)
RUN mkdir -p /data

# Default command using your HTTP wrapper
CMD ["uvicorn", "http_server:app", "--host", "0.0.0.0", "--port", "8080"]
