# app/api/alexa_admin.py – Admin-Endpunkte für Alexa Geräte-Management
import json
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin")

# Speichert das letzte Token das Alexa geschickt hat
_last_token: Optional[str] = None

ALEXA_EVENT_GATEWAY = "https://api.eu.amazonalexa.com/v3/events"


def store_token(token: str):
    """Wird vom alexa_router aufgerufen um das Token zu speichern."""
    global _last_token
    _last_token = token


class DeleteRequest(BaseModel):
    endpoint_ids: list[str]


@router.post("/delete-devices")
async def delete_devices(req: DeleteRequest):
    """Sendet DeleteReport an Alexa Event Gateway um Geräte zu entfernen."""
    if not _last_token:
        raise HTTPException(status_code=400, detail="Kein Alexa-Token vorhanden. Warte auf einen Alexa-Request.")

    if not req.endpoint_ids:
        raise HTTPException(status_code=400, detail="Keine endpoint_ids angegeben")

    # DeleteReport Event bauen
    import uuid
    event = {
        "event": {
            "header": {
                "namespace": "Alexa.Discovery",
                "name": "DeleteReport",
                "messageId": str(uuid.uuid4()),
                "payloadVersion": "3",
            },
            "payload": {
                "endpoints": [{"endpointId": eid} for eid in req.endpoint_ids],
                "scope": {
                    "type": "BearerToken",
                    "token": _last_token,
                },
            },
        }
    }

    logger.info("DeleteReport: %d Geräte → %s", len(req.endpoint_ids), req.endpoint_ids[:5])

    # An Alexa Event Gateway senden
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                ALEXA_EVENT_GATEWAY,
                json=event,
                headers={
                    "Authorization": f"Bearer {_last_token}",
                    "Content-Type": "application/json",
                },
            )
        logger.info("DeleteReport Response: %d %s", resp.status_code, resp.text[:200])
        return {
            "status": resp.status_code,
            "response": resp.text[:500],
            "deleted": req.endpoint_ids,
        }
    except Exception as e:
        logger.error("DeleteReport fehlgeschlagen: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/token-status")
async def token_status():
    """Zeigt ob ein Alexa-Token vorhanden ist."""
    from app.services.change_report import ChangeReportService
    cr = ChangeReportService.get()
    return {
        "has_token": _last_token is not None,
        "token_preview": _last_token[:20] + "..." if _last_token else None,
        "change_report_active": cr.has_token,
        "last_reported_count": len(cr._last_reported),
    }


@router.get("/compare-devices")
async def compare_devices():
    """Vergleicht devices.yaml mit den bei Alexa registrierten Geräten."""
    from app.core.device_loader import load_devices
    from app.services.access_log import AccessLog

    devices = load_devices()
    yaml_ids = {d.id.replace(".", "#") for d in devices if d.alexa}
    alexa_ids = AccessLog.get().alexa_devices()

    # Normalisiere Alexa-IDs (entferne evtl. Prefixes)
    alexa_normalized = set()
    for aid in alexa_ids:
        alexa_normalized.add(aid)

    in_yaml_not_alexa = sorted(yaml_ids - alexa_normalized)
    in_alexa_not_yaml = sorted(alexa_normalized - yaml_ids)
    matching = sorted(yaml_ids & alexa_normalized)

    return {
        "yaml_count": len(yaml_ids),
        "alexa_count": len(alexa_normalized),
        "matching": len(matching),
        "in_yaml_not_alexa": in_yaml_not_alexa,
        "in_alexa_not_yaml": in_alexa_not_yaml,
    }
