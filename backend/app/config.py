import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./sitesense.db"
    ZAP_API_KEY: str = ""
    ZAP_PORT: int = 8080
    ZAP_HOST: str = "localhost"
    CHROME_PATH: str = "/Users/ravinarayanaks/Library/Caches/ms-playwright/chromium-1194/chrome-mac/Chromium.app/Contents/MacOS/Chromium"
    
    class Config:
        env_file = ".env"

settings = Settings()
