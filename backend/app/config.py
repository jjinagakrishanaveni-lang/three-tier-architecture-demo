import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "FastAPI Docker Auth App"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database Settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "app_db")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        
    # Redis Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    
    # Registration Verification Settings
    PENDING_REGISTRATION_TTL: int = int(os.getenv("PENDING_REGISTRATION_TTL", "900"))  # 15 minutes in seconds
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-jwt-key-for-fastapi-app-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Frontend Base URL (for verification link generation)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8081")

settings = Settings()
