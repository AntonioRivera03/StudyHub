from fastapi import APIRouter

from app.api.routes import (
    cards,
    categories,
    dashboard,
    decks,
    health,
    reviews,
    sessions,
    settings,
    timers,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(categories.router)
api_router.include_router(settings.router)
api_router.include_router(timers.router)
api_router.include_router(sessions.router)
api_router.include_router(decks.router)
api_router.include_router(cards.router)
api_router.include_router(reviews.router)
api_router.include_router(dashboard.router)
