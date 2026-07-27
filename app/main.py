from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.alexa_router import router as alexa_router
from app.api.dashboard_router import router as dashboard_router
from app.config.logging_config import setup_logging
from app.infrastructure.status_cache import StatusCache

setup_logging()

app = FastAPI(title="Alexa Smart Home + Dashboard")

# MQTT Status-Cache beim Start initialisieren
StatusCache.get()


@app.get("/health")
async def health_check():
    return {"status": "online"}


# API-Router
app.include_router(alexa_router)
app.include_router(dashboard_router)

# Static Files (muss als letztes kommen – Catch-All für Frontend)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "static"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
