import pytest
from httpx import AsyncClient
from app.models.entity import Entity
from app.services.entity_service import EntityService
from uuid import uuid4

@pytest.mark.asyncio
async def test_entity_search(test_app, mongodb_client):
    # Create test entities
    service = EntityService()
    entities = []
    for i in range(3):
        entity = await service.create_or_update_entity(
            name=f"Test Entity {i}",
            entity_type="ORGANIZATION",
            risk_score=0.5,
            role="TEST",
            db=test_app.app.mongodb
        )
        entities.append(entity)

    # Search for entities
    response = test_app.get("/api/entities?query=Test")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3
    assert all("name" in entity for entity in data)
    assert all("risk_score" in entity for entity in data)

@pytest.mark.asyncio
async def test_get_entity_by_id(test_app, mongodb_client):
    # Create test entity
    service = EntityService()
    entity = await service.create_or_update_entity(
        name="Test Entity",
        entity_type="ORGANIZATION",
        risk_score=0.5,
        role="TEST",
        db=test_app.app.mongodb
    )

    # Get entity by ID
    response = test_app.get(f"/api/entities/{entity.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Test Entity"
    assert "risk_score" in data
    assert "enrichment_data" in data

@pytest.mark.asyncio
async def test_entity_enrichment(test_app, mongodb_client):
    # Create entity with enrichment data
    service = EntityService()
    entity = await service.create_or_update_entity(
        name="Risky Corp",
        entity_type="ORGANIZATION",
        risk_score=0.8,
        role="SENDER",
        db=test_app.app.mongodb
    )

    # Get enriched entity
    response = test_app.get(f"/api/entities/{entity.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "enrichment_data" in data
    assert "ofac" in data["enrichment_data"]
    assert "sec" in data["enrichment_data"]

@pytest.mark.asyncio
async def test_entity_relationships(test_app, mongodb_client, neo4j_driver):
    # Create related entities
    service = EntityService()
    entity1 = await service.create_or_update_entity(
        name="Parent Corp",
        entity_type="ORGANIZATION",
        risk_score=0.6,
        role="PARENT",
        db=test_app.app.mongodb
    )
    
    entity2 = await service.create_or_update_entity(
        name="Subsidiary Corp",
        entity_type="ORGANIZATION",
        risk_score=0.4,
        role="SUBSIDIARY",
        db=test_app.app.mongodb
    )

    # Create relationship in Neo4j
    async with neo4j_driver.session() as session:
        await session.run(
            """
            MATCH (e1:Entity {id: $id1})
            MATCH (e2:Entity {id: $id2})
            CREATE (e1)-[:OWNS]->(e2)
            """,
            {"id1": str(entity1.id), "id2": str(entity2.id)}
        )

    # Get entity with relationships
    response = test_app.get(f"/api/entities/{entity1.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "graph_data" in data
    assert len(data["graph_data"]) > 0

@pytest.mark.asyncio
async def test_invalid_entity_id(test_app):
    # Test with non-existent entity ID
    response = test_app.get(f"/api/entities/{uuid4()}")
    assert response.status_code == 404