import pytest
from httpx import AsyncClient
from app.models.file import FileMetadata
from app.services.pipeline_service import PipelineService
from app.services.file_service import FileService
from datetime import datetime

@pytest.mark.asyncio
async def test_pipeline_status(test_app, mongodb_client):
    # Create test file
    service = FileService()
    metadata = FileMetadata(
        id="pipeline_test",
        filename="test.json",
        size=1000,
        format="JSON",
        uploadedBy="test-user",
        status="PROCESSING",
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )
    await service.create_file_metadata(metadata, test_app.app.mongodb)

    # Get pipeline status
    response = test_app.get("/api/pipeline/status/pipeline_test")
    assert response.status_code == 200
    
    data = response.json()
    assert data["file_id"] == "pipeline_test"
    assert "status" in data
    assert "progress" in data

@pytest.mark.asyncio
async def test_pipeline_processing(test_app, mongodb_client):
    # Create test file with content
    content = {
        "transactions": [
            {
                "id": "TX001",
                "sender": "Test Corp",
                "receiver": "Partner LLC",
                "amount": 100000
            }
        ]
    }
    
    service = FileService()
    metadata = FileMetadata(
        id="process_test",
        filename="test.json",
        size=1000,
        format="JSON",
        uploadedBy="test-user",
        status="PENDING",
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )
    await service.create_file_metadata(metadata, test_app.app.mongodb)

    # Process file
    pipeline_service = PipelineService()
    await pipeline_service.process_file("process_test", test_app.app.mongodb)

    # Check status
    response = test_app.get("/api/pipeline/status/process_test")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] in ["PROCESSING", "COMPLETED"]

@pytest.mark.asyncio
async def test_invalid_file_pipeline(test_app):
    # Test with non-existent file
    response = test_app.get("/api/pipeline/status/nonexistent")
    assert response.status_code == 404