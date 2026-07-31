# app/services/access_log.py – Zählt und loggt Alexa-Zugriffe
import threading
from datetime import datetime
from typing import Optional


class AccessLog:
    """Singleton: Zählt Zugriffe auf /api/alexa/smart_home."""

    _instance: Optional["AccessLog"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._total = 0
        self._by_category: dict[str, int] = {}
        self._last_access: str | None = None
        self._last_action: str | None = None
        self._start_time = datetime.now()
        self._alexa_devices: set[str] = set()

    @classmethod
    def get(cls) -> "AccessLog":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def log_access(self, namespace: str, device_name: str = ""):
        """Wird bei jedem Alexa-Request aufgerufen."""
        self._total += 1
        self._last_access = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._last_action = f"{namespace}: {device_name}" if device_name else namespace
        category = namespace.replace("Alexa.", "")
        self._by_category[category] = self._by_category.get(category, 0) + 1

    def stats(self) -> dict:
        return {
            "total": self._total,
            "by_category": self._by_category,
            "last_access": self._last_access,
            "last_action": self._last_action,
        }

    def online_since(self) -> str:
        return self._start_time.strftime("%Y-%m-%d %H:%M")

    def track_alexa_device(self, endpoint_id: str):
        """Merkt sich welche Geräte Alexa per ReportState abfragt."""
        self._alexa_devices.add(endpoint_id)

    def alexa_devices(self) -> set[str]:
        """Geräte die Alexa kennt (aus ReportState-Requests)."""
        return self._alexa_devices
