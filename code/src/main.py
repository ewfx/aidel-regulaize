import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import redis
import os

from app.core.config import settings
from app.core.logger import setup_logging

# Redis connection
redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

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

# Import routes after FastAPI app creation
from app.api.routes import router as api_router
app.include_router(api_router, prefix="/v1")

@app.get("/")
def read_root():
    return {"message": "FastAPI server is running!"}

# Test Redis Connection
@app.get("/redis-test")
def redis_test():
    try:
        redis_client.set("test_key", "Hello from Redis")
        value = redis_client.get("test_key")
        return {"redis_value": value}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)