# app/infrastructure/midea_client.py – Midea/Comfee Klimaanlage via LAN (msmart-ng)
import asyncio
import logging
import os
import time
from typing import Optional

from msmart.device import AirConditioner as AC_Device

from app.models.device import DeviceConfig

logger = logging.getLogger(__name__)

# Globaler Lock – die Klimaanlage akzeptiert nur eine Verbindung gleichzeitig
_midea_lock = asyncio.Lock()
_COOLDOWN = 3.0  # Sekunden zwischen Befehlen
_LOCK_TIMEOUT = 10.0  # Max. Wartezeit auf Lock (Alexa hat ~8s Timeout)
_CACHE_TTL = 30.0  # Status-Cache gültig für 30 Sekunden

# Status-Cache
_status_cache: dict = {}
_status_cache_time: float = 0.0


def _resolve_env(value: Optional[str]) -> Optional[str]:
    """Löst ${VAR_NAME} auf zu os.environ Werten."""
    if value and value.startswith("${") and value.endswith("}"):
        env_key = value[2:-1]
        return os.getenv(env_key, "")
    return value


class MideaClient:
    """Steuert Midea/Comfee Klimaanlagen über das lokale Netzwerk."""

    @staticmethod
    async def _connect(device: DeviceConfig) -> AC_Device:
        """Erstellt Verbindung, authentifiziert und refresht."""
        token = _resolve_env(device.token)
        key = _resolve_env(device.key)
        ac = AC_Device(ip=device.ip, port=6444, device_id=int(device.device_id))
        await ac.authenticate(token, key)
        await ac.refresh()
        return ac

    @staticmethod
    async def get_status(device: DeviceConfig) -> dict:
        """Liest den aktuellen Status. Nutzt Cache wenn möglich."""
        global _status_cache, _status_cache_time

        token = _resolve_env(device.token)
        key = _resolve_env(device.key)

        if not all([device.ip, device.device_id, token, key]):
            logger.error("MideaClient: Fehlende Konfiguration für %s", device.id)
            return {}

        # Cache prüfen
        now = time.time()
        if _status_cache and (now - _status_cache_time) < _CACHE_TTL:
            return _status_cache

        # Lock mit Timeout versuchen
        try:
            await asyncio.wait_for(_midea_lock.acquire(), timeout=_LOCK_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning("MideaClient: Lock-Timeout bei get_status, verwende Cache")
            return _status_cache if _status_cache else {}

        try:
            # Nochmal Cache prüfen nach Lock-Erwerb
            now = time.time()
            if _status_cache and (now - _status_cache_time) < _CACHE_TTL:
                return _status_cache

            ac = await MideaClient._connect(device)
            result = {
                "power_state": ac.power_state,
                "operational_mode": ac.operational_mode,
                "target_temperature": ac.target_temperature,
                "indoor_temperature": ac.indoor_temperature,
                "fan_speed": ac.fan_speed,
                "eco": getattr(ac, "eco", False),
                "turbo": getattr(ac, "turbo", False),
                "sleep": getattr(ac, "sleep", False),
            }
            _status_cache = result
            _status_cache_time = time.time()
            await asyncio.sleep(_COOLDOWN)
            return result
        except Exception as e:
            logger.error("MideaClient: Status-Abfrage fehlgeschlagen [%s]: %s", device.id, e)
            return _status_cache if _status_cache else {}
        finally:
            _midea_lock.release()

    @staticmethod
    async def set_power(device: DeviceConfig, power_on: bool):
        """Schaltet die Klimaanlage ein oder aus."""
        global _status_cache, _status_cache_time

        try:
            await asyncio.wait_for(_midea_lock.acquire(), timeout=_LOCK_TIMEOUT)
        except asyncio.TimeoutError:
            raise TimeoutError("Klimaanlage beschäftigt, bitte erneut versuchen")

        try:
            ac = await MideaClient._connect(device)
            ac.power_state = power_on
            await ac.apply()
            logger.info("MideaClient: Power %s → %s", device.name, "ON" if power_on else "OFF")
            _status_cache = {}
            _status_cache_time = 0.0
        except Exception as e:
            logger.error("MideaClient: Power-Befehl fehlgeschlagen [%s]: %s", device.id, e)
            raise
        finally:
            # Kurzer Cooldown im Hintergrund, Lock aber sofort freigeben
            _midea_lock.release()

    @staticmethod
    async def set_temperature(device: DeviceConfig, temperature: float):
        """Setzt die Zieltemperatur. Schaltet das Gerät ein falls nötig."""
        global _status_cache, _status_cache_time

        try:
            await asyncio.wait_for(_midea_lock.acquire(), timeout=_LOCK_TIMEOUT)
        except asyncio.TimeoutError:
            raise TimeoutError("Klimaanlage beschäftigt, bitte erneut versuchen")

        try:
            ac = await MideaClient._connect(device)
            if not ac.power_state:
                ac.power_state = True
            ac.target_temperature = temperature
            await ac.apply()
            logger.info("MideaClient: Temperatur %s → %s°C", device.name, temperature)
            _status_cache = {}
            _status_cache_time = 0.0
        except Exception as e:
            logger.error("MideaClient: Temperatur-Befehl fehlgeschlagen [%s]: %s", device.id, e)
            raise
        finally:
            _midea_lock.release()

    @staticmethod
    async def set_mode(device: DeviceConfig, mode: str):
        """Setzt den Betriebsmodus. Schaltet automatisch ein/aus."""
        global _status_cache, _status_cache_time
        mode_mapping = {"auto": 1, "cool": 2, "dry": 3, "heat": 4, "fan": 5}

        try:
            await asyncio.wait_for(_midea_lock.acquire(), timeout=_LOCK_TIMEOUT)
        except asyncio.TimeoutError:
            raise TimeoutError("Klimaanlage beschäftigt, bitte erneut versuchen")

        try:
            ac = await MideaClient._connect(device)
            if mode == "off":
                ac.power_state = False
            else:
                ac.power_state = True
                mode_id = mode_mapping.get(mode.lower(), 2)
                ac.operational_mode = mode_id
            await ac.apply()
            logger.info("MideaClient: Modus %s → %s", device.name, mode)
            _status_cache = {}
            _status_cache_time = 0.0
        except Exception as e:
            logger.error("MideaClient: Modus-Befehl fehlgeschlagen [%s]: %s", device.id, e)
            raise
        finally:
            _midea_lock.release()
