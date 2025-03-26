import pytest
from httpx import AsyncClient
import io
import json
from app.models.file import FileMetadata
from app.services.file_service import FileService

@pytest.mark.asyncio
async def test_file_upload(test_app, mongodb_client):
    # Create test file
    content = json.dumps({
        "transaction_id": "TEST001",
        "amount": 50000,
        "currency": "USD",
        "sender": "Test Sender",
        "receiver": "Test Receiver"
    })
    file = io.BytesIO(content.encode())
    file.name = "test.json"

    # Upload file
    response = test_app.post(
        "/api/files",
        files={"file": ("test.json", file, "application/json")}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "id" in data
    assert data["filename"] == "test.json"
    assert data["format"] == "JSON"
    assert data["status"] == "PENDING"

@pytest.mark.asyncio
async def test_list_files(test_app, mongodb_client):
    # Create multiple test files
    service = FileService()
    files = []
    for i in range(3):
        metadata = FileMetadata(
            id=f"test{i}",
            filename=f"test{i}.json",
            size=1000,
            format="JSON",
            uploadedBy="test-user",
            status="COMPLETED",
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await service.create_file_metadata(metadata, test_app.app.mongodb)
        files.append(metadata)

    # List files
    response = test_app.get("/api/files")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3
    assert all("id" in file for file in data)
    assert all("status" in file for file in data)

@pytest.mark.asyncio
async def test_get_file_status(test_app, mongodb_client):
    # Create test file
    service = FileService()
    metadata = FileMetadata(
        id="test123",
        filename="test.json",
        size=1000,
        format="JSON",
        uploadedBy="test-user",
        status="PROCESSING",
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )
    await service.create_file_metadata(metadata, test_app.app.mongodb)

    # Get file status
    response = test_app.get("/api/files/test123")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == "test123"
    assert data["status"] == "PROCESSING"

@pytest.mark.asyncio
async def test_file_deletion(test_app, mongodb_client):
    # Create test file
    service = FileService()
    metadata = FileMetadata(
        id="test_delete",
        filename="test.json",
        size=1000,
        format="JSON",
        uploadedBy="test-user",
        status="COMPLETED",
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow()
    )
    await service.create_file_metadata(metadata, test_app.app.mongodb)

    # Delete file
    response = test_app.delete("/api/files/test_delete")
    assert response.status_code == 200

    # Verify deletion
    response = test_app.get("/api/files/test_delete")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_invalid_file_format(test_app):
    # Try to upload invalid file format
    file = io.BytesIO(b"test content")
    file.name = "test.invalid"

    response = test_app.post(
        "/api/files",
        files={"file": ("test.invalid", file, "application/octet-stream")}
    )
    assert response.status_code == 400