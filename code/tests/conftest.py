import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import AsyncGraphDatabase
from fastapi.testclient import TestClient
from app.main import app
import asyncio
from typing import AsyncGenerator, Generator
import os

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mongodb_client() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """Create a MongoDB client for testing."""
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    yield client
    await client.close()

@pytest.fixture
async def neo4j_driver():
    """Create a Neo4j driver for testing."""
    driver = AsyncGraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(
            os.getenv("NEO4J_USER", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "password123")
        )
    )
    yield driver
    await driver.close()

@pytest.fixture
def test_app(mongodb_client):
    """Create a FastAPI test client."""
    app.mongodb_client = mongodb_client
    app.mongodb = mongodb_client[os.getenv("MONGODB_DB_NAME", "risk_analysis_test")]
    return TestClient(app)

@pytest.fixture(autouse=True)
async def cleanup_databases(mongodb_client, neo4j_driver):
    """Clean up test databases after each test."""
    yield
    
    # Clean up MongoDB
    db = mongodb_client[os.getenv("MONGODB_DB_NAME", "risk_analysis_test")]
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].delete_many({})
    
    # Clean up Neo4j
    async with neo4j_driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")