FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
# ffmpeg for video processing
# libgl1-mesa-glx for opencv
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY README.md .

# Install dependencies
# --system flag installs packages into the system python environment
RUN uv sync --frozen

# Copy the rest of the application
COPY . .

# Copy local database for initial state (Warning: Data changes in Cloud Run won't persist!)
COPY data/db.sqlite3 /app/data/db.sqlite3

# Configure Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Expose Nginx port
EXPOSE 8080

# Make start script executable
RUN chmod +x scripts/start_docker.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"
ENV API_BASE_URL="http://127.0.0.1:8000"

# Command to run the application
CMD ["./scripts/start_docker.sh"]
