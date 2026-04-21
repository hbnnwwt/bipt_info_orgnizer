from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "BIPTInfoOrganizer"
    BIPTHELPER_URL: str = "http://localhost:8000"
    BIPTHELPER_PATH: str = "E:/code/bipthelper/backend"
    ORGANIZER_API_KEY: str = "a0e1a1ad56456186e97d1fe1bd10b649"
    CRAWL_INTERVAL_MINUTES: int = 60
    CRAWL_DELAY_SECONDS: float = 2.0
    CRAWL_ARTICLE_DELAY: float = 1.0
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()