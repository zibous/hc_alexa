import yaml
from functools import lru_cache
from typing import List
from app.models.device import DeviceConfig
from app.config.settings import settings


@lru_cache(maxsize=1)
def _load_from_file(path: str) -> tuple:
    """Cached YAML-Parsing (tuple für hashability)."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return tuple(DeviceConfig(**d) for d in data)


def load_devices() -> List[DeviceConfig]:
    return list(_load_from_file(settings.DEVICES_YAML_PATH))
