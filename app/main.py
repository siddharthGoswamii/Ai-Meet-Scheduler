"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# 1. ADD THIS IMPORT
from starlette.middleware.sessions import SessionMiddleware 
from contextlib import asynccontextmanager
import logging
import uvicorn

from app.core.config import settings
from app.db.database import init_db, close_db
from app.api import api_router

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    yield
    logger.info("Shutting down application...")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Microsoft Teams Meeting Scheduler API",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)
#  ADD THE SESSION MIDDLEWARE HERE
# app.add_middleware(
#     SessionMiddleware,
#     secret_key="a-very-secure-random-secret-key-change-this",  # Or use settings.SECRET_KEY
#     session_cookie="teams_auth_session",
#     same_site="lax",   # Essential to allow cookies across Microsoft's redirect back to your app
#     https_only=False,  # Set to True in production (HTTPS), but False for local HTTP development
# )
# Add CORS middleware FIRST (order matters!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add Session middleware AFTER CORS
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="teams_auth_session",
    same_site="none" if settings.ENVIRONMENT == "production" else "lax",
    https_only=settings.ENVIRONMENT == "production",  # True in production, False in development
    domain=None
)

# # 2. ADD THE SESSION MIDDLEWARE HERE
# app.add_middleware(
#     SessionMiddleware,
#     secret_key="a-very-secure-random-secret-key-change-this",  # Or use settings.SECRET_KEY
#     session_cookie="teams_auth_session",
#     same_site="lax",   # Essential to allow cookies across Microsoft's redirect back to your app
#     https_only=False,  # Set to True in production (HTTPS), but False for local HTTP development
# )

# Include API router
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )