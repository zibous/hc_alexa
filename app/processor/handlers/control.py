import logging
from typing import List

import httpx

from app.models.device import DeviceConfig
from app.config.settings import settings
from app.infrastructure.mqtt_client import MqttClient
from app.processor.helpers import get_utc_timestamp

logger = logging.getLogger(__name__)


class ControlHandler:
    def __init__(self):
        self.mqtt = MqttClient.get()

    async def handle(self, devices: List[DeviceConfig], directive: dict, header: dict) -> dict:
        namespace = header.get("namespace")
        name = header.get("name")
        endpoint_id = directive.get("endpoint", {}).get("endpointId")
        target_device = next((d for d in devices if d.id == endpoint_id), None)

        if not target_device:
            logger.warning("Alexa Zugriff auf unbekannte ID: %s", endpoint_id)
            return self._error(endpoint_id, "NO_SUCH_ENDPOINT", header)

        try:
            ctx = []

            if namespace == "Alexa.PowerController":
                state = "ON" if name == "TurnOn" else "OFF"
                self._send_power(target_device, state)
                ctx.append(self._prop("Alexa.PowerController", "powerState", state))

            elif namespace == "Alexa.BrightnessController":
                brightness = directive.get("payload", {}).get("brightness")
                self._send_brightness(target_device, brightness)
                ctx.append(self._prop("Alexa.BrightnessController", "brightness", brightness))

            elif namespace == "Alexa.RangeController":
                position = directive.get("payload", {}).get("rangeValue")
                self._send_position(target_device, position)
                ctx.append(self._prop("Alexa.RangeController", "rangeValue", position, instance="Blind.Position"))

            elif namespace == "Alexa.ThermostatController" and name in ("SetTargetSetpoint", "SetTargetTemperature"):
                temp = directive.get("payload", {}).get("targetSetpoint", {}).get("value")
                self._send_temperature(target_device, temp)
                ctx.append(self._prop("Alexa.ThermostatController", "targetSetpoint", {"value": temp, "scale": "CELSIUS"}))

            elif namespace == "Alexa.ThermostatController" and name == "SetThermostatMode":
                mode = directive.get("payload", {}).get("thermostatMode", {}).get("value", "AUTO")
                self._send_mode(target_device, mode.lower())
                ctx.append(self._prop("Alexa.ThermostatController", "thermostatMode", mode))

            return self._response(endpoint_id, header, ctx)

        except Exception as e:
            logger.exception("Steuerungsfehler '%s': %s", target_device.name, e)
            return self._error(endpoint_id, "ENDPOINT_UNREACHABLE", header)

    # ─── Protokoll-Dispatch ──────────────────────────────

    def _send_power(self, d: DeviceConfig, state: str):
        if d.protocol == "shelly":
            action = "on" if state == "ON" else "off"
            if d.type in ("dimmer", "light"):
                httpx.get(f"http://{d.ip}/light/{d.channel}?turn={action}", timeout=5)
            else:
                httpx.get(f"http://{d.ip}/relay/{d.channel}?turn={action}", timeout=5)
        elif d.protocol == "esphome":
            endpoint = d.endpoint_on if state == "ON" else d.endpoint_off
            if endpoint:
                httpx.post(f"http://{d.ip}/{endpoint}", timeout=5)
        elif d.protocol == "z2m":
            self.mqtt.publish(f"{settings.Z2M_TOPIC_BASE}/{d.mqtt_name}/set", {"state": state})
        elif d.protocol == "mqtt":
            self.mqtt.publish(d.topic, state)

    def _send_brightness(self, d: DeviceConfig, brightness: int):
        if d.protocol == "shelly":
            httpx.get(f"http://{d.ip}/light/{d.channel}?turn=on&brightness={brightness}", timeout=5)
        elif d.protocol == "z2m":
            self.mqtt.publish(f"{settings.Z2M_TOPIC_BASE}/{d.mqtt_name}/set", {"brightness": brightness})
        elif d.protocol == "mqtt" and d.topic:
            # Tasmota: cmnd/{device}/Dimmer → 0-100
            base_topic = d.topic.rsplit("/", 1)[0]  # cmnd/wzlicht2/POWER → cmnd/wzlicht2
            self.mqtt.publish(f"{base_topic}/Dimmer", str(brightness))

    def _send_position(self, d: DeviceConfig, position: int):
        if d.protocol == "shelly":
            httpx.get(f"http://{d.ip}/roller/{d.channel}?go=to_pos&roller_pos={position}", timeout=5)
        elif d.protocol == "z2m":
            self.mqtt.publish(f"{settings.Z2M_TOPIC_BASE}/{d.mqtt_name}/set", {"position": position})

    def _send_temperature(self, d: DeviceConfig, temp: float):
        if d.protocol == "z2m":
            self.mqtt.publish(f"{settings.Z2M_TOPIC_BASE}/{d.mqtt_name}/set", {"current_heating_setpoint": temp})

    def _send_mode(self, d: DeviceConfig, mode: str):
        if d.protocol == "z2m":
            self.mqtt.publish(f"{settings.Z2M_TOPIC_BASE}/{d.mqtt_name}/set", {"system_mode": mode})

    # ─── Response Builder ────────────────────────────────

    def _prop(self, namespace, name, value, instance=None):
        p = {
            "namespace": namespace,
            "name": name,
            "value": value,
            "timeOfSample": get_utc_timestamp(),
            "uncertaintyInMilliseconds": 0,
        }
        if instance:
            p["instance"] = instance
        return p

    def _response(self, endpoint_id, header, properties):
        return {
            "context": {"properties": properties},
            "event": {
                "header": {
                    "namespace": "Alexa", "name": "Response", "payloadVersion": "3",
                    "messageId": header.get("messageId"),
                    "correlationToken": header.get("correlationToken"),
                },
                "endpoint": {"endpointId": endpoint_id},
                "payload": {},
            },
        }

    def _error(self, endpoint_id, error_type, header):
        return {
            "event": {
                "header": {
                    "namespace": "Alexa", "name": "ErrorResponse", "payloadVersion": "3",
                    "messageId": header.get("messageId"),
                    "correlationToken": header.get("correlationToken"),
                },
                "endpoint": {"endpointId": endpoint_id},
                "payload": {"type": error_type, "message": "Gerät nicht erreichbar."},
            },
        }
