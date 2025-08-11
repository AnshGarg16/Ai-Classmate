# # Use Python 3.11 slim image as base
# FROM python:3.11-slim-bookworm

# # Install uv using the official method
# COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# # Install system dependencies required for building certain Python packages
# RUN apt-get update && apt-get upgrade -y && apt-get install -y \
#     gcc g++ git make \
#     libmagic-dev \
#     ffmpeg \
#     && rm -rf /var/lib/apt/lists/*

# # Set the working directory in the container to /app
# WORKDIR /app

# COPY . /app

# RUN uv sync


# EXPOSE 8502

# RUN mkdir -p /app/data

# CMD ["uv", "run", "streamlit", "run", "app_home.py"]

# Use Python 3.11 slim image as base
FROM python:3.11-slim-bookworm

# Install uv using the official method
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    gcc g++ git make \
    libmagic1 libmagic-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables to avoid Python buffering issues and set uv cache
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_CACHE_DIR=/root/.cache/uv

# Set working directory
WORKDIR /app

# Copy app code

COPY .env /app/.env

# Install Python dependencies
RUN uv sync

# Create data directory
RUN mkdir -p /app/data

# Expose Streamlit port
EXPOSE 8502

# Streamlit: Avoid browser auto-launch, set host to 0.0.0.0 for Docker
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8502

# Default command
CMD ["uv", "run", "streamlit", "run", "app_home.py"]
