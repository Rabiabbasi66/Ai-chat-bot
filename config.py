from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "ai_chat_app"
    
    # Security
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI Configuration
    openai_api_key: Optional[str] = None
    ai_model: str = "gpt-3.5-turbo"
    ai_temperature: float = 0.7
    ai_max_tokens: int = 500
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

# This instance is what main.py refers to as 'settings'
settings = Settings()