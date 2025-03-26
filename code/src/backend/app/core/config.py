from typing import Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "risk_analysis"
    SECRET_KEY: str = "your-secret-key"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # ChromaDB settings
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001  # Updated to match docker-compose port
    
    # Neo4j settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "regulaize123"
    
    class Config:
        env_file = ".env"

settings = Settings()