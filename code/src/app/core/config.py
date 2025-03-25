from pydantic_settings import BaseSettings
from typing import List
from pydantic import Field
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    EMAIL: str = "shalini.thilakan@gmail.com"
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

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: str = "regulaize_redis"

    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_DATA_PATH: str = "data/db"
    MONGO_DB: str = "regulaizedb"
    MONGO_OFAC_COLLECTION: str = "ofac"
    MONGO_ENTITY_COLLECTION: str = "entity"
    MONGO_CIK_COLLECTION: str = "cik"

    ZOOKEEPER_CLIENT_PORT: int = 6379
    ZOOKEEPER_TICK_TIME: int = 2000
    KAFKA_BROKER_ID: int = 1
    KAFKA_PORT: int = 9092
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: str = "PLAINTEXT:PLAINTEXT"
    KAFKA_INTER_BROKER_LISTENER_NAME: str = "PLAINTEXT"
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: int = 1
    KAFKA_UI_PORT: int = 8080
    KAFKA_CLUSTERS_0_NAME: str = "regulaize-cluster"

    NEO4J_PORT: int = 7474
    NEO4J_HOST:str = "localhost"
    BOLT_PORT:int = 7687
    NEO4J_LOGIN: str = "neo4j"
    NEO4J_PASSWORD: str = "reg_neo4j"
    NEO4J_DATA_PATH: str = "/Users/shalini/Documents/Projects/Hackathon/regulaize/neo4j"
    
    class Config:
        env_file = ".env"

settings = Settings()