# app/infrastructure/status_cache.py – Z2M Status: Initial aus Datei, Live via MQTT
import json
import logging
import threading
import uuid
from pathlib import Path
from typing import Optional, Any

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion  # type: ignore[reportPrivateImportUsage]

from app.config.settings import settings

logger = logging.getLogger(__name__)

Z2M_STATE_FILE = Path("data/z2m_state.json")
Z2M_CONFIG_FILE = Path("data/z2m_config.yaml")


class StatusCache:
    """Initialer Load aus Z2M state.json, danach Live-Updates via MQTT."""

    _instance: Optional["StatusCache"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._name_map: dict[str, str] = {}  # ieee_addr → friendly_name
        self._msg_count = 0

        # 1. Initial: Z2M-Dateien laden (wenn vorhanden)
        self._load_z2m_files()

        # 2. MQTT für Live-Updates starten
        self._start_mqtt()

    @classmethod
    def get(cls) -> "StatusCache":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_state(self, device_id: str, topic_id: str | None = None) -> dict:
        """Liefert den gecachten Status eines Geräts."""
        key = topic_id or device_id
        return self._cache.get(key, {})

    # ─── Initialer Load ──────────────────────────────────

    def _load_z2m_files(self):
        """Lädt state.json + configuration.yaml und befüllt den Cache."""
        self._parse_config()
        self._parse_state()
        logger.info("StatusCache: %d Geräte aus Z2M-Dateien geladen", len(self._cache))

    def _parse_config(self):
        """Liest ieee_addr → friendly_name Mapping aus configuration.yaml."""
        if not Z2M_CONFIG_FILE.exists():
            logger.warning("StatusCache: %s nicht gefunden", Z2M_CONFIG_FILE)
            return
        try:
            current_ieee = None
            with open(Z2M_CONFIG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line_clean = line.strip()
                    if line_clean.startswith("#"):
                        continue
                    if "0x" in line_clean and ":" in line_clean:
                        for part in line_clean.split(":"):
                            part_clean = part.strip().replace("'", "").replace('"', '')
                            if part_clean.startswith("0x") and len(part_clean) >= 14:
                                current_ieee = part_clean
                                break
                    if current_ieee and "friendly_name:" in line_clean:
                        f_name = line_clean.split("friendly_name:", 1)[1].strip()
                        f_name = f_name.replace("'", "").replace('"', '')
                        self._name_map[current_ieee] = f_name
                        current_ieee = None
        except Exception as e:
            logger.error("StatusCache: Config-Parsing fehlgeschlagen: %s", e)

    def _parse_state(self):
        """Lädt state.json und befüllt den Cache with friendly_name als Key."""
        if not Z2M_STATE_FILE.exists():
            logger.warning("StatusCache: %s nicht gefunden", Z2M_STATE_FILE)
            return
        try:
            with open(Z2M_STATE_FILE, "r", encoding="utf-8") as f:
                z2m_data = json.load(f)
            for ieee_addr, state in z2m_data.items():
                if not isinstance(state, dict):
                    continue
                friendly_name = self._name_map.get(ieee_addr)
                if friendly_name:
                    self._cache[friendly_name] = state
        except Exception as e:
            logger.error("StatusCache: State-Parsing fehlgeschlagen: %s", e)

    # ─── MQTT Live-Updates ───────────────────────────────

    def _start_mqtt(self):
        """Startet MQTT-Client für Live-Updates im Hintergrund."""
        client_id = f"hc_alexa_{uuid.uuid4().hex[:6]}"
        self._client = mqtt.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=client_id,
            protocol=mqtt.MQTTv311,
        )
        if settings.MQTT_USER:
            self._client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)

        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        try:
            self._client.connect(settings.MQTT_HOST, settings.MQTT_PORT, keepalive=60)
            self._client.loop_start()
        except Exception as e:
            logger.error("StatusCache: MQTT Connect fehlgeschlagen: %s", e)

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Any, reason_code: Any, properties: Any = None):
        # Paho v2 nutzt reason_code anstelle von rc. Bei Erfolg ist reason_code.is_failure False oder reason_code == 0
        if reason_code == 0:
            # Z2M Topics
            z2m_topic = f"{settings.Z2M_TOPIC_BASE}/#"
            client.subscribe(z2m_topic)
            # Custom MQTT Topics (Tasmota, Sonoff, etc.) aus devices.yaml
            self._subscribe_custom_topics(client)
            logger.info("StatusCache: MQTT verbunden, subscribed auf %s + custom topics", z2m_topic)
        else:
            logger.error("StatusCache: MQTT Connect fehlgeschlagen (reason_code=%s)", reason_code)

    def _subscribe_custom_topics(self, client: mqtt.Client):
        """Subscribed auf alle topic_ids die nicht z2m sind."""
        from app.core.device_loader import load_devices
        for d in load_devices():
            if d.protocol == "mqtt" and d.topic_id:
                client.subscribe(d.topic_id)
                logger.debug("StatusCache: Custom subscribe → %s", d.topic_id)

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        topic = msg.topic

        # Z2M: conbee2mqtt/{device}
        prefix = settings.Z2M_TOPIC_BASE + "/"
        if topic.startswith(prefix):
            rest = topic[len(prefix):]
            if rest.startswith("bridge") or "/" in rest:
                return
            try:
                payload = json.loads(msg.payload.decode("utf-8"))
                if isinstance(payload, dict):
                    self._cache[rest] = payload
                    self._msg_count += 1
                    # Proaktive ChangeReports bei Temperaturänderung
                    if "temperature" in payload:
                        self._notify_change_report(rest, payload["temperature"])
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            return

        # Custom MQTT Topics (gespeichert unter vollem Topic als Key)
        try:
            raw = msg.payload.decode("utf-8").strip()
            # Plain-Text Payloads (z.B. Tasmota "ON"/"OFF")
            if raw in ("ON", "OFF"):
                self._cache[topic] = {"state": raw}
            else:
                payload = json.loads(raw)
                if isinstance(payload, dict):
                    self._cache[topic] = payload
                    # Proaktive ChangeReports bei Temperaturänderung
                    if "temperature" in payload:
                        self._notify_change_report(topic, payload["temperature"])
            self._msg_count += 1

            if self._msg_count <= 5 or self._msg_count % 100 == 0:
                logger.info("StatusCache: MQTT msg count: %d (last: %s)", self._msg_count, topic)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    def _notify_change_report(self, topic_id: str, temperature: Any):
        """Benachrichtigt den ChangeReport-Service über Temperaturänderungen."""
        try:
            from app.core.device_loader import load_devices
            from app.services.change_report import ChangeReportService

            cr = ChangeReportService.get()
            if not cr.has_token:
                return

            # topic_id → device.id Mapping (für Alexa endpoint_id)
            for d in load_devices():
                if d.type == "sensor" and (d.topic_id == topic_id or d.id == topic_id):
                    cr.check_and_report(d.id, float(temperature))
                    break
        except Exception as e:
            logger.debug("ChangeReport notify fehlgeschlagen: %s", e)
