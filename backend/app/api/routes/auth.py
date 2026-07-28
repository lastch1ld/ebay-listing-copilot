from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.integrations.ebay.oauth import EbayOAuth, OAuthStateError

router = APIRouter()


@router.get("/api/auth/ebay/begin")
async def begin_ebay_auth(request: Request) -> RedirectResponse:
    oauth: EbayOAuth = request.app.state.ebay_oauth
    authorization = oauth.begin()
    return RedirectResponse(authorization.authorization_url, status_code=302)


@router.get("/api/auth/ebay/callback")
async def ebay_auth_callback(request: Request, code: str, state: str) -> JSONResponse:
    oauth: EbayOAuth = request.app.state.ebay_oauth
    try:
        oauth.complete(code=code, state=state)
    except OAuthStateError as error:
        return JSONResponse(status_code=400, content={"detail": str(error)})
    return JSONResponse(status_code=200, content={"status": "connected"})
