import os
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MQTT Broker
    MQTT_HOST: str = Field(default="localhost", alias="MQTT_HOST")
    MQTT_PORT: int = Field(default=1883)
    MQTT_USER: str = Field(default="")
    MQTT_PASS: str = Field(default="")
    MQTT_KEEPALIVE: int = Field(default=60)

    # Zigbee2MQTT
    Z2M_TOPIC_BASE: str = Field(default="zigbee2mqtt")

    # OAuth (Alexa Account Linking)
    OAUTH_CLIENT_ID: str = Field(default="alexa-smarthome")
    OAUTH_TOKEN: str = Field(default="smarthome-alexa-token-2026")

    # Pfade
    DEVICES_YAML_PATH: str = Field(default="data/devices.yaml")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
