from fastapi import APIRouter, Request
from app.processor.alexa_processor import AlexaProcessor

router = APIRouter()
processor = AlexaProcessor()

@router.post("/api/alexa/smart_home")
async def handle_alexa_smart_home(request: Request):
    payload = await request.json()
    response = await processor.process_request(payload)
    return response
