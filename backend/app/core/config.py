"""Application configuration using Pydantic Settings v2"""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_title: str = "TrueHire AI Backend"
    api_version: str = "0.1.0"
    api_description: str = "AI-powered reverse-interview platform with identity verification"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # CORS Configuration
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Database Configuration
    database_url: str = "sqlite:///./truehire.db"
    
    # Security Configuration
    openai_api_key: Optional[str] = None
    
    # Demo Mode Configuration (development only)
    demo_mode: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
