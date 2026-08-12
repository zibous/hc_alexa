# app/infrastructure/miio_client.py – Xiaomi Air Purifier via MIoT (python-miio)
import asyncio
import logging
import os
from typing import Optional

from miio import AirPurifierMiot

from app.models.device import DeviceConfig

logger = logging.getLogger(__name__)


def _resolve_env(value: Optional[str]) -> Optional[str]:
    """Löst ${VAR_NAME} auf zu os.environ Werten."""
    if value and value.startswith("${") and value.endswith("}"):
        env_key = value[2:-1]
        return os.getenv(env_key, "")
    return value


class MiioClient:
    """Steuert Xiaomi MIoT Geräte (Air Purifier) über das lokale Netzwerk."""

    @staticmethod
    async def get_status(device: DeviceConfig) -> dict:
        """Liest den aktuellen Status des Luftreinigers."""
        token = _resolve_env(device.token)

        if not device.ip or not token:
            logger.error("MiioClient: Fehlende Konfiguration für %s", device.id)
            return {}

        try:
            purifier = AirPurifierMiot(ip=device.ip, token=token, lazy_discover=False)
            loop = asyncio.get_event_loop()
            status = await loop.run_in_executor(None, purifier.status)

            return {
                "power_state": status.is_on,
                "mode": str(status.mode) if status.mode else "unknown",
                "aqi": status.aqi if hasattr(status, "aqi") else None,
                "temperature": status.temperature if hasattr(status, "temperature") else None,
                "humidity": status.humidity if hasattr(status, "humidity") else None,
                "filter_life_level": getattr(status, "filter_life_level", None),
                "filter_hours_used": getattr(status, "filter_hours_used", None),
            }
        except Exception as e:
            logger.error("MiioClient: Status-Abfrage fehlgeschlagen [%s]: %s", device.id, e)
            return {}

    @staticmethod
    async def set_power(device: DeviceConfig, power_on: bool):
        """Schaltet den Luftreiniger ein oder aus."""
        token = _resolve_env(device.token)
        purifier = AirPurifierMiot(ip=device.ip, token=token, lazy_discover=False)
        loop = asyncio.get_event_loop()

        if power_on:
            await loop.run_in_executor(None, purifier.on)
        else:
            await loop.run_in_executor(None, purifier.off)

        logger.info("MiioClient: Power %s → %s", device.name, "ON" if power_on else "OFF")

    @staticmethod
    async def set_mode(device: DeviceConfig, mode: str):
        """Setzt den Betriebsmodus (Auto, Silent, Favorite)."""
        from miio.integrations.airpurifier.zhimi.airpurifier_miot import OperationMode

        token = _resolve_env(device.token)
        purifier = AirPurifierMiot(ip=device.ip, token=token, lazy_discover=False)
        loop = asyncio.get_event_loop()

        # Mapping: Dashboard-Werte → OperationMode Enum
        mode_map = {
            "Auto": OperationMode.Auto,
            "auto": OperationMode.Auto,
            "Silent": OperationMode.Silent,
            "silent": OperationMode.Silent,
            "Favorite": OperationMode.Favorite,
            "favorite": OperationMode.Favorite,
        }
        target_mode = mode_map.get(mode, OperationMode.Auto)

        await loop.run_in_executor(None, purifier.set_mode, target_mode)
        logger.info("MiioClient: Modus %s → %s", device.name, mode)
