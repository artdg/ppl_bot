from fastapi import APIRouter

from app.api.routes.bets import router as bets_router
from app.api.routes.internal import router as internal_router
from app.api.routes.matches import router as matches_router
from app.api.routes.me import router as me_router

api_router = APIRouter()
api_router.include_router(me_router, tags=["me"])
api_router.include_router(matches_router, tags=["matches"])
api_router.include_router(bets_router, tags=["bets"])
api_router.include_router(internal_router, tags=["internal"])

