from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./hotel_booking.db"
    
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    BCRYPT_ROUNDS: int = 12
    
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    POSTGRES_PASSWORD: Optional[str] = None

    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False 

settings = Settings()