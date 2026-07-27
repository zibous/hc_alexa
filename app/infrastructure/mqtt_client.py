# app/infrastructure/mqtt_client.py
import json
import logging
import threading

import paho.mqtt.client as mqtt

from app.config.settings import settings

logger = logging.getLogger(__name__)


class MqttClient:
    """Persistenter MQTT-Client mit automatischer Reconnection."""

    _instance: "MqttClient | None" = None
    _lock = threading.Lock()

    def __init__(self):
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="hc_alexa_publish")
        self._connected = False

        if settings.MQTT_USER:
            self._client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._connect()

    @classmethod
    def get(cls) -> "MqttClient":
        """Singleton-Zugriff."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def publish(self, topic: str, payload):
        if isinstance(payload, dict):
            final_payload = json.dumps(payload)
        else:
            final_payload = str(payload)

        if not self._connected:
            self._connect()

        try:
            result = self._client.publish(topic, final_payload)
            result.wait_for_publish(timeout=3.0)
        except Exception as e:
            logger.error("MQTT Publish fehlgeschlagen [%s]: %s", topic, e)
            self._connected = False

    def _connect(self):
        try:
            self._client.connect(settings.MQTT_HOST, settings.MQTT_PORT, settings.MQTT_KEEPALIVE)
            self._client.loop_start()
        except Exception as e:
            logger.error("MQTT Connect fehlgeschlagen: %s", e)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info("MQTT verbunden: %s:%d", settings.MQTT_HOST, settings.MQTT_PORT)
        else:
            logger.error("MQTT Verbindung fehlgeschlagen (rc=%d)", rc)

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning("MQTT Verbindung verloren (rc=%d), Reconnect...", rc)
