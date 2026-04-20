from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "BIPTInfoOrganizer"
    BIPTHELPER_URL: str = "http://localhost:8000"
    ORGANIZER_API_KEY: str = ""
    CRAWL_INTERVAL_MINUTES: int = 60
    CRAWL_DELAY_SECONDS: float = 2.0
    CRAWL_ARTICLE_DELAY: float = 1.0

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()