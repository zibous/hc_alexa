# app/api/oauth_router.py – Minimaler OAuth2 Endpoint für Alexa Account Linking
import logging
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

from app.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/oauth/authorize")
async def oauth_authorize(
    client_id: str = "",
    redirect_uri: str = "",
    state: str = "",
    response_type: str = "code",
):
    """Alexa ruft diese URL auf beim Account Linking."""
    if client_id != settings.OAUTH_CLIENT_ID:
        return JSONResponse({"error": "unauthorized_client"}, status_code=403)
    logger.info("OAuth authorize: client_id=%s", client_id)
    return RedirectResponse(f"{redirect_uri}?code=fixed-auth-code&state={state}")


@router.post("/oauth/token")
async def oauth_token(request: Request):
    """Alexa tauscht den Code gegen ein Token."""
    form = await request.form()
    if form.get("client_id") != settings.OAUTH_CLIENT_ID:
        return JSONResponse({"error": "unauthorized_client"}, status_code=403)
    logger.info("OAuth token granted")
    return JSONResponse({
        "access_token": settings.OAUTH_TOKEN,
        "token_type": "Bearer",
        "expires_in": 31536000,
        "refresh_token": settings.OAUTH_TOKEN,
    })
