# ── AuraGenesis Dockerfile ────────────────────────────────────────────
# NOTE: Ollama must be running on the HOST machine (not inside this
# container). The container calls it via host.docker.internal:11434.
# See docker-compose.yml for the full setup.

FROM python:3.11-slim

WORKDIR /app

# Install system deps (needed for torch + sentence-transformers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer cache)
COPY AuraGenesis/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy full project
COPY . .

# Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Awaken Aura
CMD ["streamlit", "run", "AuraGenesis/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
