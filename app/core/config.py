from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/customs_calc"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/customs_calc"

    # App settings
    APP_NAME: str = "Customs Calculator"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key"

    # Central Bank API
    CBU_API_URL: str = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"

    # Base calculation values
    BRV_VALUE: float = 340000  # Базовая расчетная величина в UZS

    # Tax rates
    VAT_RATE: float = 12.0  # НДС (QQS) rate in %

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
