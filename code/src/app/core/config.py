from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Risk Platform API"
    PROJECT_DESCRIPTION: str = "Advanced Transaction Risk Analysis Platform"
    VERSION: str = "1.0.0"
    
    # API Settings
    API_V1_STR: str = "/v1"
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # External API Keys
    HUGGINGFACE_API_KEY: str = ""
    OPENCORPORATES_API_KEY: str = ""
    SEC_API_KEY: str = ""
    
    # Cache Settings
    CACHE_TTL: int = 3600  # 1 hour
    
    # Risk Scoring
    HIGH_RISK_THRESHOLD: float = 75.0
    MEDIUM_RISK_THRESHOLD: float = 50.0
    
    class Config:
        env_file = ".env"

settings = Settings()