# app/services/kpi_service.py – KPI-Daten für hc_alexa
import logging
from collections import Counter
from datetime import datetime

from app.core.device_loader import load_devices
from app.services.access_log import AccessLog
from app.schemas.kpi import KpiResponse, KpiHero, KpiMetric, KpiIndicator

logger = logging.getLogger(__name__)


class KpiService:
    """Aggregiert KPI-Daten für das zentrale Übersichts-Dashboard."""

    def __init__(self):
        self._devices = load_devices()
        self._access_log = AccessLog.get()

    def build_response(self) -> KpiResponse:
        device_count = len(self._devices)
        categories = Counter(d.category for d in self._devices)
        protocols = Counter(d.protocol for d in self._devices)

        stats = self._access_log.stats()
        total_calls = stats["total"]
        last_access = stats["last_access"]
        last_action = stats["last_action"]

        # Hero: Gesamtanzahl Geräte
        hero = KpiHero(value=device_count, unit="Geräte", label="Registriert")

        # Metriken
        metrics = [
            KpiMetric(label="Alexa Zugriffe", value=total_calls),
            KpiMetric(label="Letzter Zugriff", value=last_access or "–"),
            KpiMetric(label="Letzte Aktion", value=last_action or "–"),
            KpiMetric(label="Online seit", value=self._access_log.online_since()),
            KpiMetric(label="Rollläden", value=categories.get("INTERIOR_BLIND", 0)),
            KpiMetric(label="Sensoren", value=categories.get("TEMPERATURE_SENSOR", 0)),
            KpiMetric(label="Thermostate", value=categories.get("THERMOSTAT", 0)),
            KpiMetric(label="Schalter", value=categories.get("SWITCH", 0)),
            KpiMetric(label="Lichter", value=categories.get("LIGHT", 0)),
        ]

        # Indicator: Balken pro Protokoll
        protocol_colors = {
            "shelly": "#3b82f6",
            "z2m": "#10b981",
            "esphome": "#f59e0b",
            "mqtt": "#8b5cf6",
        }
        bars = [{"label": k, "value": v, "color": protocol_colors.get(k, "#94a3b8")} for k, v in protocols.items()]
        indicator = KpiIndicator(type="deltabars", bars=bars, label="Protokolle")

        return KpiResponse(
            app_id="hc_alexa",
            app_name="Smart Home Alexa",
            icon="🏠",
            url="/dashboardalexa/",
            status="ok",
            ts=datetime.now().isoformat(),
            hero=hero,
            detail=f"{total_calls} Zugriffe · {device_count} Geräte",
            metrics=metrics,
            indicator=indicator,
        )
