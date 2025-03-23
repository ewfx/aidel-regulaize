import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from pymongo import MongoClient
import redis
import os

from app.api.routes import router as api_router
from app.core.config import settings
from app.core.logger import setup_logging


# ✅ Use settings for Redis & MongoDB connections
redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)
mongo_client = MongoClient(f"mongodb://{settings.MONGO_HOST}:{settings.MONGO_PORT}/")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    # Initialize NLP models and caches here
    yield
    # Cleanup
    # Close any connections here

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/v1")

@app.get("/")
def read_root():
    return {"message": "FastAPI server is running!"}


# ✅ Test Redis Connection
@app.get("/redis-test")
def redis_test():
    try:
        redis_client.set("test_key", "Hello from Redis")
        value = redis_client.get("test_key")
        return {"redis_value": value}
    except Exception as e:
        return {"error": str(e)}

# ✅ Test MongoDB Connection
@app.get("/mongo-test")
def mongo_test():
    try:
        test_collection = mongo_client.test_db.test_collection
        test_collection.insert_one({"message": "Hello from MongoDB"})
        data = test_collection.find_one({}, {"_id": 0})  # Get first document
        return {"mongo_value": data}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)