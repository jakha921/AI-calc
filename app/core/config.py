from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/customs_calc"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/customs_calc"
    DATABASE_URL_DOCKER: Optional[str] = None
    DATABASE_URL_SYNC_DOCKER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    # App settings
    APP_NAME: str = "Customs Calculator"
    DEBUG: bool | str = True  # str (e.g. "WARN") is accepted for SQLAlchemy echo
    SECRET_KEY: str = "dev-secret-key"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Central Bank API
    CBU_API_URL: str = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"

    # Base calculation values
    BRV_VALUE: float = 340000  # Базовая расчетная величина в UZS

    # Tax rates
    VAT_RATE: float = 12.0  # НДС (QQS) rate in %

@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
