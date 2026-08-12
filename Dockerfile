FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Labels
LABEL maintainer="Peter Siebler <peter.siebler@gmail.com>" \
      application="Alexa Smart Home Controller" \
      version="1.0.0" \
      com.centurylinklabs.watchtower.enable="false" \
      dockerhand.check-update="false" \
      dockerhand.ignore="true"

WORKDIR /app

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendung kopieren (data, logs, frontend kommen per Volume)
COPY app/ app/

# Healthcheck
HEALTHCHECK --interval=60s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:5018/health || exit 1

# Starten
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5018"]
