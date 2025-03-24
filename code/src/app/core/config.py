from pydantic_settings import BaseSettings
from typing import List
from pydantic import Field
from dotenv import load_dotenv

# Load .env file
load_dotenv()

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

    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")

    MONGO_HOST: str = Field(default="localhost", env="MONGO_HOST")
    MONGO_PORT: int = Field(default=27017, env="MONGO_PORT")
    MONGO_DATA_PATH: str = Field(default="data/db", env="MONGO_DATA_PATH")
    MONGO_DB: str = Field(default="regulaizedb", env="MONGO_DB")
    MONGO_OFAC_COLLECTION: str = Field(default="ofac", env="MONGO_OFAC_COLLECTION")
    MONGO_ENTITY_COLLECTION: str = Field(default="entity", env="MONGO_ENTITY_COLLECTION")
    
    class Config:
        env_file = ".env"

settings = Settings()