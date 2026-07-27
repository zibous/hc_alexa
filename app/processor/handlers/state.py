# app/processor/handlers/state.py – Status-Abfragen für Alexa ReportState
import logging
from typing import List

import httpx

from app.models.device import DeviceConfig
from app.infrastructure.status_cache import StatusCache
from app.processor.helpers import get_utc_timestamp
from app.config.settings import settings

logger = logging.getLogger(__name__)


class StateHandler:
    def handle(self, devices: List[DeviceConfig], directive: dict, header: dict) -> dict:
        endpoint_id = directive.get("endpoint", {}).get("endpointId")
        target_device = next((d for d in devices if d.id == endpoint_id), None)

        current_temp = 20.0  # Fallback

        if target_device and target_device.type == "sensor":
            current_temp = self._read_temperature(target_device)

        return {
            "context": {
                "properties": [{
                    "namespace": "Alexa.TemperatureSensor",
                    "name": "temperature",
                    "value": {"value": current_temp, "scale": "CELSIUS"},
                    "timeOfSample": get_utc_timestamp(),
                    "uncertaintyInMilliseconds": 1000,
                }]
            },
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "Response",
                    "payloadVersion": "3",
                    "messageId": header.get("messageId"),
                    "correlationToken": header.get("correlationToken"),
                },
                "endpoint": {"endpointId": endpoint_id},
                "payload": {},
            },
        }

    def _read_temperature(self, device: DeviceConfig) -> float:
        """Liest Temperatur je nach Protokoll."""
        try:
            if device.protocol == "esphome":
                return self._read_esphome(device)
            else:
                return self._read_cache(device)
        except Exception as e:
            logger.error("Status-Abfrage fehlgeschlagen [%s]: %s", device.id, e)
        return 20.0

    def _read_esphome(self, device: DeviceConfig) -> float:
        """GET http://{ip}/{endpoint_status} → JSON mit 'value'."""
        if not device.endpoint_status:
            return 20.0
        url = f"http://{device.ip}/{device.endpoint_status}"
        logger.info("ESPHome Status: GET %s", url)
        resp = httpx.get(url, timeout=3.0)
        data = resp.json()
        return float(data.get("value", data.get("state", 20.0)))

    def _read_cache(self, device: DeviceConfig) -> float:
        """Liest Temperatur aus dem StatusCache (z2m, mqtt/tasmota)."""
        cache = StatusCache.get()
        state_data = cache.get_state(device.id, device.topic_id)
        temp = state_data.get("temperature")
        if temp is None and device.value_path:
            val = state_data
            for key in device.value_path.split("."):
                val = val.get(key) if isinstance(val, dict) else None
            temp = val
        return float(temp) if temp is not None else 20.0
