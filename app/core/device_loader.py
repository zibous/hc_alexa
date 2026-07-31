import os
import yaml
from typing import List
from app.models.device import DeviceConfig
from app.config.settings import settings

_cache: List[DeviceConfig] = []
_last_mtime: float = 0


def load_devices() -> List[DeviceConfig]:
    """Lädt devices.yaml – automatischer Reload bei Dateiänderung."""
    global _cache, _last_mtime

    path = settings.DEVICES_YAML_PATH
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return _cache

    if mtime != _last_mtime:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            _cache = [DeviceConfig(**d) for d in data]
        _last_mtime = mtime

    return _cache
