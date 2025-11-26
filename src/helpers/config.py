from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    OPENAPI_API_KEY: str
    
    FILE_MAX_SIZE_MB: int
    FILE_ALLOWED_TYPES: List[str]
    FILE_STORAGE_PATH: str
    FILE_DEFAULT_CHUNK_SIZE: int
    
    MONGO_URI: str
    MONGODB_NAME: str
    
    
    class Config:
        env_file = ".env" 
        extra = "ignore"


def get_settings() -> Settings:
    return Settings()
