from fastapi import APIRouter, Request
from app.processor.alexa_processor import AlexaProcessor
from app.services.access_log import AccessLog

router = APIRouter()
processor = AlexaProcessor()


@router.post("/api/alexa/smart_home")
async def handle_alexa_smart_home(request: Request):
    payload = await request.json()

    # Zugriff loggen
    directive = payload.get("directive", {})
    header = directive.get("header", {})
    namespace = header.get("namespace", "Unknown")
    endpoint_id = directive.get("endpoint", {}).get("endpointId", "")
    AccessLog.get().log_access(namespace, endpoint_id)

    response = await processor.process_request(payload)
    return response
