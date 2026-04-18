# ── AuraGenesis Dockerfile ────────────────────────────────────────────────────────────────
# Ollama must be running on the HOST machine.
# The container calls it via host.docker.internal:11434.
# Quick start: docker compose up --build

FROM python:3.11-slim

WORKDIR /app

# System deps for dlib (face recognition) + torch + chromadb
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    curl \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (layer cache)
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . .

# Create required runtime dirs
RUN mkdir -p logs known_faces config

# Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Awaken Aura
CMD ["streamlit", "run", "main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
