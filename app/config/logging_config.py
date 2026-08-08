import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging():
    os.makedirs("logs", exist_ok=True)

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    formatter = logging.Formatter(fmt)

    # Rotation: max 2 MB pro Datei, 3 Backups behalten (= max 8 MB total)
    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Root-Logger: nur WARNING+
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    # Unsere App: INFO (Alexa-Requests, Control-Befehle)
    logging.getLogger("app.api.alexa_router").setLevel(logging.INFO)
    logging.getLogger("app.api.dashboard_router").setLevel(logging.INFO)
    logging.getLogger("app.processor").setLevel(logging.INFO)
    logging.getLogger("app.services.access_log").setLevel(logging.INFO)

    # Infrastruktur: nur beim Start, danach still
    logging.getLogger("app.infrastructure.status_cache").setLevel(logging.INFO)
    logging.getLogger("app.infrastructure.mqtt_client").setLevel(logging.WARNING)

    # Externe Libs stumm schalten
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("paho").setLevel(logging.WARNING)
