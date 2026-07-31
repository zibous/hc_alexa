import logging
import os


def setup_logging():
    os.makedirs("logs", exist_ok=True)

    # Root-Logger: nur WARNING+
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

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
