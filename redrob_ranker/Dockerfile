# Use lightweight Python 3.11 slim image
FROM python:3.11-slim

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy dependency definition
COPY requirements.txt .

# Install CPU-only PyTorch first to save disk space and avoid CUDA GPU requirements,
# then install remaining packages from requirements.txt
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy project source code, configuration, precomputed artifacts, and local embedding models
COPY src/ ./src/
COPY config/ ./config/
COPY artifacts/ ./artifacts/
COPY models/ ./models/

# Create mount points for external data and output
RUN mkdir -p /app/data /app/output

# Set the entrypoint to run the main ranking pipeline
ENTRYPOINT ["python", "src/main.py"]

# Default arguments pointing to the mounted container directories
CMD ["--candidates", "/app/data/candidates.jsonl", "--out", "/app/output/submission.csv"]
