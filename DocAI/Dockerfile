# Multi-stage build for DocAI
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies including LibreOffice
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    libreoffice \
    libreoffice-writer \
    python3-uno \
    poppler-utils \
    tesseract-ocr \
    pandoc \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 docai

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/usr/lib/python3/dist-packages:$PYTHONPATH

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=docai:docai . .

# Create necessary directories
RUN mkdir -p /app/uploads/documents /app/uploads/embeddings /app/models /app/logs /app/data && \
    chown -R docai:docai /app

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Switch to non-root user
USER docai

# Expose port
EXPOSE 8090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

# Default command
CMD ["python", "main.py"]