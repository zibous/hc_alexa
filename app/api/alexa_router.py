import json
import logging
from fastapi import APIRouter, Request
from app.processor.alexa_processor import AlexaProcessor
from app.services.access_log import AccessLog
from app.api.alexa_admin import store_token
from app.services.change_report import ChangeReportService

logger = logging.getLogger(__name__)

router = APIRouter()
processor = AlexaProcessor()


@router.post("/api/alexa/smart_home")
async def handle_alexa_smart_home(request: Request):
    payload = await request.json()

    # ALLES loggen was reinkommt
    directive = payload.get("directive", {})
    header = directive.get("header", {})
    namespace = header.get("namespace", "?")
    name = header.get("name", "?")
    endpoint_id = directive.get("endpoint", {}).get("endpointId", "–")

    # ReportState ist Routine-Polling → nur DEBUG
    if namespace == "Alexa" and name == "ReportState":
        logger.debug("ALEXA REQUEST: %s.%s → %s", namespace, name, endpoint_id)
    else:
        logger.info("ALEXA REQUEST: %s.%s → %s", namespace, name, endpoint_id)

    # Zugriff loggen
    AccessLog.get().log_access(namespace, endpoint_id)

    # Token speichern für Admin-Operationen (DeleteReport)
    scope = directive.get("endpoint", {}).get("scope") or directive.get("payload", {}).get("scope")
    if scope and scope.get("token"):
        store_token(scope["token"])
        # Token auch für proaktive ChangeReports speichern
        ChangeReportService.get().set_token(scope["token"])

    # Alexa-bekannte Geräte tracken (aus ReportState Requests)
    if namespace == "Alexa" and name == "ReportState" and endpoint_id != "–":
        AccessLog.get().track_alexa_device(endpoint_id)

    response = await processor.process_request(payload)

    # StateReport Response loggen für Debugging (nur DEBUG)
    if namespace == "Alexa" and name == "ReportState":
        props = response.get("context", {}).get("properties", [])
        resp_name = response.get("event", {}).get("header", {}).get("name", "?")
        logger.debug("STATEREPORT RESPONSE [%s] header=%s props=%s", endpoint_id, resp_name, json.dumps(props)[:300])

    # Bei Discovery: Endpoint-IDs und Payload loggen
    if namespace == "Alexa.Discovery":
        endpoints = response.get("event", {}).get("payload", {}).get("endpoints", [])
        ids = [e["endpointId"] for e in endpoints]
        logger.info("DISCOVERY RESPONSE: %d Geräte → %s", len(ids), ids[:5])
        logger.info("DISCOVERY REQUEST PAYLOAD: %s", json.dumps(directive.get("payload", {}))[:200])

    return response
