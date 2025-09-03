from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./local.db")
    APP_TITLE: str = "Etykiety API"
    DEFAULT_SHEET: str = "A4"

    class Config:
        env_file = ".env"

settings = Settings()
