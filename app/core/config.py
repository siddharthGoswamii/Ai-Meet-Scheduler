"""
Application configuration settings
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict  # pyright: ignore[reportMissingImports]


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Google Meet Scheduler"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    DATABASE_ECHO: bool = False
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    # Google Calendar API
    GOOGLE_API_SCOPES: str = Field(
        default="https://www.googleapis.com/auth/calendar,https://www.googleapis.com/auth/calendar.events,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/userinfo.profile"
    )
    
    # Microsoft Graph API Configuration
    GRAPH_API_ENDPOINT: str = Field(default="https://graph.microsoft.com/v1.0")
    
    @property
    def google_scopes_list(self) -> List[str]:
        """Convert comma-separated scopes to list"""
        return [scope.strip() for scope in self.GOOGLE_API_SCOPES.split(",") if scope.strip()]
    
    # JWT Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"
    CORS_ALLOW_CREDENTIALS: bool = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # Encryption
    ENCRYPTION_KEY: str
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Meeting Configuration
    MIN_MEETING_DURATION_MINUTES: int = 15
    MAX_MEETING_DURATION_HOURS: int = 24
    MAX_ATTENDEES: int = 250
    
    # Timezone
    DEFAULT_TIMEZONE: str = "UTC"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Using lru_cache to avoid reading .env file multiple times
    """
    return Settings()


# Global settings instance
settings = get_settings()

# Made with Bob
