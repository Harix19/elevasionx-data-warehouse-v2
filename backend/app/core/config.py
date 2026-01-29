"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost/dev"

    # Security
    SECRET_KEY: str = "changeme-in-production-use-random-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Application
    DEBUG: bool = False
    APP_NAME: str = "Leads Data Warehouse API"
    CSV_IMPORT_BATCH_SIZE: int = 1000

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def convert_database_url(cls, v: str) -> str:
        """Convert postgresql:// to postgresql+asyncpg:// and fix SSL parameters for asyncpg."""
        if not v:
            return v

        # Convert postgresql:// to postgresql+asyncpg://
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Convert psycopg-specific SSL parameters to asyncpg format
        # asyncpg uses ssl=require instead of sslmode=require
        # asyncpg doesn't support channel_binding parameter
        v = v.replace("sslmode=require", "ssl=require")
        v = v.replace("&channel_binding=require", "")
        v = v.replace("channel_binding=require&", "")
        v = v.replace("?channel_binding=require", "")

        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
