from pydantic import BaseModel
from typing import Optional


class DeviceConfig(BaseModel):
    id: str                              # Alexa endpoint ID
    name: str
    type: str                            # switch, dimmer, roller, thermostat, sensor, light
    category: str                        # Alexa display category
    protocol: str                        # shelly, z2m, mqtt, esphome
    topic_id: Optional[str] = None       # MQTT Gerätename (z2m friendly_name), falls ≠ id
    ip: Optional[str] = None             # Bei shelly + esphome
    channel: Optional[str] = "0"         # Bei shelly
    topic: Optional[str] = None          # Bei mqtt (vollständiges custom topic)
    endpoint_on: Optional[str] = None    # Bei esphome
    endpoint_off: Optional[str] = None   # Bei esphome
    endpoint_status: Optional[str] = None  # Bei esphome
    value_path: Optional[str] = None     # JSON-Pfad zum Wert (z.B. "SonoffSC.Temperature")
    unit: Optional[str] = None           # Einheit für Anzeige (z.B. "m³", "°C")
    alexa: bool = True                   # False = nur Dashboard, nicht in Alexa Discovery
    hardware: str = ""

    @property
    def mqtt_name(self) -> str:
        """Der Name wie er im MQTT Topic verwendet wird."""
        return self.topic_id or self.id
