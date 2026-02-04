# ===================================
# Dockerfile for BA-Agent Backend (Python FastAPI)
# Optimized for production with ChromaDB support
# ===================================

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for:
# - build-essential: compiling Python packages
# - curl: health checks
# - libpq-dev: PostgreSQL support (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application source code
COPY . .

# Create directories for data persistence
# - /app/db: ChromaDB vector store databases
RUN mkdir -p /app/db/chroma_db_with_metadata_analysis \
             /app/db/chroma_db_with_metadata_communication \
             /app/db/chroma_db_with_metadata_discovery \
             /app/db/chroma_db_with_metadata_documentation

# Default environment variables (overridden by docker-compose or runtime)
ENV MONGODB_URI=mongodb://mongodb:27017/ba-agent
ENV HOST=0.0.0.0
ENV PORT=8000

# Expose the API port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Start FastAPI with Uvicorn
# - host 0.0.0.0: accept connections from any IP
# - port 8000: default API port
# - workers: can be increased for production (default 1)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
