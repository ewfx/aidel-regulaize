from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from typing import List
from app.models.file import FileMetadata
from app.services.file_service import FileService
from app.core.config import settings
import uuid
from datetime import datetime

router = APIRouter()
file_service = FileService()

@router.post("", response_model=FileMetadata)
async def upload_file(file: UploadFile = File(...), request: Request = None):
    try:
        # Generate a unique ID for the file
        file_id = str(uuid.uuid4())
        
        # Get file size and format
        content = await file.read()
        size = len(content)
        format = file.filename.split('.')[-1].upper()
        
        # Create file metadata
        metadata = FileMetadata(
            id=file_id,
            filename=file.filename,
            size=size,
            format=format,
            uploadedBy="current-user",  # In a real app, get from auth context
            status="PENDING",
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        
        # Process and store the file
        if hasattr(request, 'app') and hasattr(request.app, 'mongodb'):
            await file_service.process_file(content, metadata, request.app.mongodb)
        else:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=List[FileMetadata])
async def list_files(request: Request, skip: int = 0, limit: int = 100):
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        files = await file_service.list_files(request.app.mongodb, skip, limit)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}", response_model=FileMetadata)
async def get_file(file_id: str, request: Request):
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        file = await file_service.get_file(file_id, request.app.mongodb)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        return file
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{file_id}")
async def delete_file(file_id: str, request: Request):
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        success = await file_service.delete_file(file_id, request.app.mongodb)
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        return {"message": "File deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))