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
        # Scope aus dem Request übernehmen (Alexa erwartet es in der Antwort)
        scope = directive.get("endpoint", {}).get("scope", {})
        target_device = next((d for d in devices if d.id == endpoint_id), None)

        properties = []

        if target_device:
            properties = self._build_properties(target_device)

        # Fallback: mindestens eine leere Property-Liste
        if not properties and target_device and target_device.type == "sensor":
            properties = [{
                "namespace": "Alexa.TemperatureSensor",
                "name": "temperature",
                "value": {"value": 20.0, "scale": "CELSIUS"},
                "timeOfSample": get_utc_timestamp(),
                "uncertaintyInMilliseconds": 1000,
            }]

        # EndpointHealth immer mitsenden
        properties.append({
            "namespace": "Alexa.EndpointHealth",
            "name": "connectivity",
            "value": {"value": "OK"},
            "timeOfSample": get_utc_timestamp(),
            "uncertaintyInMilliseconds": 0,
        })

        # Endpoint-Objekt mit scope (wenn vorhanden)
        endpoint_obj = {"endpointId": endpoint_id}
        if scope:
            endpoint_obj["scope"] = scope

        return {
            "context": {"properties": properties},
            "event": {
                "header": {
                    "namespace": "Alexa",
                    "name": "StateReport",
                    "payloadVersion": "3",
                    "messageId": header.get("messageId"),
                    "correlationToken": header.get("correlationToken"),
                },
                "endpoint": endpoint_obj,
                "payload": {},
            },
        }

    def _build_properties(self, device: DeviceConfig) -> list:
        """Baut die Properties je nach Gerätetyp."""
        if device.type == "sensor":
            temp = self._read_temperature(device)
            return [{
                "namespace": "Alexa.TemperatureSensor",
                "name": "temperature",
                "value": {"value": temp, "scale": "CELSIUS"},
                "timeOfSample": get_utc_timestamp(),
                "uncertaintyInMilliseconds": 1000,
            }]

        elif device.type == "thermostat":
            cache = StatusCache.get()
            state_data = cache.get_state(device.id, device.topic_id)
            setpoint = state_data.get("occupied_heating_setpoint",
                        state_data.get("current_heating_setpoint", 20.0))
            current = state_data.get("local_temperature", 20.0)
            mode = state_data.get("system_mode", "off")
            alexa_mode = "HEAT" if mode == "heat" else "AUTO" if mode == "auto" else "OFF"

            return [
                {
                    "namespace": "Alexa.ThermostatController",
                    "name": "targetSetpoint",
                    "value": {"value": float(setpoint), "scale": "CELSIUS"},
                    "timeOfSample": get_utc_timestamp(),
                    "uncertaintyInMilliseconds": 1000,
                },
                {
                    "namespace": "Alexa.ThermostatController",
                    "name": "thermostatMode",
                    "value": alexa_mode,
                    "timeOfSample": get_utc_timestamp(),
                    "uncertaintyInMilliseconds": 1000,
                },
                {
                    "namespace": "Alexa.TemperatureSensor",
                    "name": "temperature",
                    "value": {"value": float(current), "scale": "CELSIUS"},
                    "timeOfSample": get_utc_timestamp(),
                    "uncertaintyInMilliseconds": 1000,
                },
            ]

        elif device.type in ("switch", "light", "dimmer"):
            power_state = self._read_power_state(device)

            props = [{
                "namespace": "Alexa.PowerController",
                "name": "powerState",
                "value": power_state,
                "timeOfSample": get_utc_timestamp(),
                "uncertaintyInMilliseconds": 1000,
            }]

            # Brightness für Lichter/Dimmer
            if device.type in ("light", "dimmer"):
                brightness = self._read_brightness(device)
                props.append({
                    "namespace": "Alexa.BrightnessController",
                    "name": "brightness",
                    "value": brightness,
                    "timeOfSample": get_utc_timestamp(),
                    "uncertaintyInMilliseconds": 1000,
                })

            return props

        elif device.type == "roller":
            position = self._read_roller_position(device)
            power_state = "ON" if position > 0 else "OFF"
            return [
                {
                    "namespace": "Alexa.PowerController",
                    "name": "powerState",
                    "value": power_state,
                    "timeOfSample": get_utc_timestamp(),
                    "uncertaintyInMilliseconds": 1000,
                },
                {
                    "namespace": "Alexa.RangeController",
                    "instance": "cover.position",
                    "name": "rangeValue",
                    "value": int(position),
                    "timeOfSample": get_utc_timestamp(),
                    "uncertaintyInMilliseconds": 1000,
                },
            ]

        return []

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

    def _read_power_state(self, device: DeviceConfig) -> str:
        """Liest Power-Status je nach Protokoll."""
        try:
            if device.protocol == "shelly" and device.ip:
                return self._read_shelly_power(device)
            elif device.protocol == "esphome" and device.ip and device.endpoint_status:
                url = f"http://{device.ip}/{device.endpoint_status}"
                resp = httpx.get(url, timeout=3.0)
                data = resp.json()
                val = data.get("value", data.get("state", 0))
                return "ON" if val in (1, "1", True, "ON") else "OFF"
            else:
                # z2m, mqtt → aus Cache
                cache = StatusCache.get()
                state_data = cache.get_state(device.id, device.topic_id)
                raw_state = state_data.get("state", "")
                if not raw_state and device.value_path:
                    val = state_data
                    for key in device.value_path.split("."):
                        val = val.get(key) if isinstance(val, dict) else None
                    raw_state = str(val) if val else ""
                return "ON" if raw_state == "ON" else "OFF"
        except Exception as e:
            logger.debug("Power-Status fehlgeschlagen [%s]: %s", device.id, e)
            return "OFF"

    def _read_shelly_power(self, device: DeviceConfig) -> str:
        """Liest Shelly Power-Status per HTTP."""
        ch = device.channel or "0"
        if device.type == "dimmer":
            url = f"http://{device.ip}/light/{ch}"
        else:
            url = f"http://{device.ip}/relay/{ch}"
        resp = httpx.get(url, timeout=3.0)
        data = resp.json()
        return "ON" if data.get("ison", False) else "OFF"

    def _read_roller_position(self, device: DeviceConfig) -> int:
        """Liest Rollladen-Position je nach Protokoll."""
        try:
            if device.protocol == "shelly" and device.ip:
                ch = device.channel or "0"
                url = f"http://{device.ip}/roller/{ch}"
                resp = httpx.get(url, timeout=3.0)
                data = resp.json()
                return int(data.get("current_pos", 0))
            else:
                cache = StatusCache.get()
                state_data = cache.get_state(device.id, device.topic_id)
                return int(state_data.get("position", 0))
        except Exception as e:
            logger.debug("Roller-Status fehlgeschlagen [%s]: %s", device.id, e)
            return 0

    def _read_brightness(self, device: DeviceConfig) -> int:
        """Liest Brightness je nach Protokoll (0-100)."""
        try:
            if device.protocol == "shelly" and device.ip:
                ch = device.channel or "0"
                url = f"http://{device.ip}/light/{ch}"
                resp = httpx.get(url, timeout=3.0)
                data = resp.json()
                return int(data.get("brightness", 0))
            elif device.protocol == "z2m":
                cache = StatusCache.get()
                state_data = cache.get_state(device.id, device.topic_id)
                # Z2M brightness ist 0-254, Alexa erwartet 0-100
                raw = state_data.get("brightness", 0)
                if raw is not None and int(raw) > 100:
                    return round(int(raw) / 254 * 100)
                return int(raw) if raw else 0
            elif device.protocol == "mqtt":
                cache = StatusCache.get()
                state_data = cache.get_state(device.id, device.topic_id)
                # Tasmota: Dimmer ist 0-100
                return int(state_data.get("Dimmer", state_data.get("dimmer", 0)))
            return 0
        except Exception as e:
            logger.debug("Brightness fehlgeschlagen [%s]: %s", device.id, e)
            return 0
