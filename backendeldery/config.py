from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
class Settings(BaseSettings):
    DATABASE_URL: str
    MONGO_URI: str
    MONGO_DB: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore"  # Ignora variáveis extras que não estejam declaradas
    )

settings = Settings()
