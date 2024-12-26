from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://elderydb:teste123@localhost/elderly_care"
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "elderly_care"

settings = Settings()