import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

class Settings(BaseSettings):
    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://api.dealscout.example.com/v1")
    API_KEY: str = os.getenv("API_KEY", "")
    
    # App Settings
    DEFAULT_ZIP_CODE: str = os.getenv("DEFAULT_ZIP_CODE", "78704")
    DEFAULT_RADIUS: int = int(os.getenv("DEFAULT_RADIUS", 5))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", 3600))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Create settings instance
settings = Settings()
