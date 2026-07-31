# app/services/change_report.py – Proaktive ChangeReports an Alexa Event Gateway
import logging
import threading
import uuid
from typing import Optional

import httpx

from app.processor.helpers import get_utc_timestamp

logger = logging.getLogger(__name__)

ALEXA_EVENT_GATEWAY = "https://api.eu.amazonalexa.com/v3/events"

# Minimum-Änderung damit ein Report gesendet wird (vermeidet Spam)
MIN_TEMP_CHANGE = 0.1


class ChangeReportService:
    """Sendet proaktive ChangeReports an Alexa wenn sich Sensorwerte ändern."""

    _instance: Optional["ChangeReportService"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._last_reported: dict[str, float] = {}  # endpoint_id → letzter gemeldeter Wert
        self._token: Optional[str] = None

    @classmethod
    def get(cls) -> "ChangeReportService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def set_token(self, token: str):
        """Speichert das Bearer-Token aus dem letzten Alexa-Request."""
        if token and token != self._token:
            self._token = token
            logger.info("ChangeReport: Token aktualisiert (…%s)", token[-8:])

    @property
    def has_token(self) -> bool:
        return self._token is not None

    def check_and_report(self, endpoint_id: str, temperature: float):
        """Prüft ob sich der Wert signifikant geändert hat und sendet ggf. einen Report."""
        if not self._token:
            return

        if temperature is None:
            return

        # Alexa endpoint_id Format: sensor#weather_kz2_temperature
        alexa_endpoint_id = endpoint_id.replace(".", "#")

        last = self._last_reported.get(alexa_endpoint_id)
        if last is not None and abs(temperature - last) < MIN_TEMP_CHANGE:
            return  # Keine signifikante Änderung

        self._last_reported[alexa_endpoint_id] = temperature

        # Async in Background-Thread senden (wir sind im MQTT-Callback)
        thread = threading.Thread(
            target=self._send_change_report,
            args=(alexa_endpoint_id, temperature),
            daemon=True,
        )
        thread.start()

    def _send_change_report(self, endpoint_id: str, temperature: float):
        """Sendet den ChangeReport an die Alexa Event Gateway."""
        event = {
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "ChangeReport",
                    "messageId": str(uuid.uuid4()),
                    "payloadVersion": "3",
                },
                "endpoint": {
                    "scope": {
                        "type": "BearerToken",
                        "token": self._token,
                    },
                    "endpointId": endpoint_id,
                },
                "payload": {
                    "change": {
                        "cause": {"type": "PERIODIC_POLL"},
                        "properties": [
                            {
                                "namespace": "Alexa.TemperatureSensor",
                                "name": "temperature",
                                "value": {"value": temperature, "scale": "CELSIUS"},
                                "timeOfSample": get_utc_timestamp(),
                                "uncertaintyInMilliseconds": 6000,
                            }
                        ],
                    }
                },
            },
            "context": {
                "properties": [
                    {
                        "namespace": "Alexa.EndpointHealth",
                        "name": "connectivity",
                        "value": {"value": "OK"},
                        "timeOfSample": get_utc_timestamp(),
                        "uncertaintyInMilliseconds": 0,
                    }
                ]
            },
        }

        try:
            resp = httpx.post(
                ALEXA_EVENT_GATEWAY,
                json=event,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                },
                timeout=10.0,
            )
            if resp.status_code == 202:
                logger.info("ChangeReport OK: %s → %.1f°C", endpoint_id, temperature)
            elif resp.status_code == 401:
                logger.warning("ChangeReport: Token abgelaufen (401) für %s", endpoint_id)
                self._token = None  # Token invalidieren
            else:
                logger.warning(
                    "ChangeReport: %d für %s → %s",
                    resp.status_code, endpoint_id, resp.text[:200],
                )
        except Exception as e:
            logger.error("ChangeReport fehlgeschlagen [%s]: %s", endpoint_id, e)
