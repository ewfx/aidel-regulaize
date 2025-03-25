from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Initialize MongoDB Client
mongo_client = AsyncIOMotorClient(f"mongodb://{settings.MONGO_HOST}:{settings.MONGO_PORT}/")

# Connect to the specified database
mongo_db = mongo_client[settings.MONGO_DB]

# Function to get a specific collection
def get_collection(collection_name: str):
    return mongo_db[collection_name]



