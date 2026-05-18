"""
API module initialization
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .meetings import router as meetings_router
from .ai_scheduling import router as ai_scheduling_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Include sub-routers
api_router.include_router(auth_router)
api_router.include_router(meetings_router)
api_router.include_router(ai_scheduling_router)

__all__ = ["api_router"]

# Made with Bob
