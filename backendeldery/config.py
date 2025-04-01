from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL_SYNC: str
    DATABASE_URL_ASYNC: str
    MONGO_URI: str
    MONGO_DB: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",  # Ignora variáveis extras que não estejam declaradas
    )


settings = Settings()
