FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py .
COPY gmail_client.py .
COPY document_processor.py .
COPY rag_engine.py .
COPY analysis_engine.py .
COPY main.py .

# Create necessary directories
RUN mkdir -p /app/vector_db /app/downloads

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from rag_engine import RAGEngine; RAGEngine().get_collection_info()" || exit 1

# Run the agent
CMD ["python", "main.py"]
