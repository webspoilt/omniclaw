# --------------------------------------------------------------------------
# OmniClaw Base Image (v3.3.0+)
# --------------------------------------------------------------------------
FROM python:3.10-slim-bullseye

# Non-interactive apt installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 1. Install System Dependencies (from INSTALLATION.md)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libaudiodev-dev \
    portaudio19-dev \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy dependency files first (for Docker caching)
COPY requirements.txt .

# 3. Install Python Dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4. Copy the entire project codebase into the container
COPY . .

# 5. Run internal installation verification before completing build
RUN python scripts/verify_install.py

# 6. Default execution entrypoint
CMD ["python", "omniclaw.py", "daemon"]
