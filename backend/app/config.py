import os
import shutil
from typing import Optional
from pydantic_settings import BaseSettings

def get_chrome_path() -> str:
    """
    Attempt to find a suitable Chrome/Chromium executable.
    Prioritizes CHROME_PATH env var, then looks for Playwright's install,
    then system installations.
    """
    # 1. Check explicit env var
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]
        
    # 2. Check for Playwright's chromium
    # Playwright installs browsers in a predictable location based on OS
    # but the exact path depends on the version.
    # We can try to use playwright's python API to find it if installed
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser_type = p.chromium
            if browser_type.executable_path:
                return browser_type.executable_path
    except Exception:
        pass

    # 3. Fallback to system installations
    common_paths = [
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            return path
            
    # 4. Last resort: shutil.which
    which_chrome = shutil.which("chromium") or shutil.which("google-chrome")
    if which_chrome:
        return which_chrome
        
    return ""

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./sitesense.db"
    ZAP_API_KEY: str = ""
    ZAP_PORT: int = 8080
    ZAP_HOST: str = "localhost"
    
    # AI Configuration
    AI_PROVIDER: str = "gemini"
    AI_MODEL: str = "gemini-1.5-pro"
    GEMINI_API_KEY: Optional[str] = None
    
    # Dynamic Chrome Path
    CHROME_PATH: str = get_chrome_path()
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env

settings = Settings()

