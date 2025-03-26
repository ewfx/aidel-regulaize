from fastapi import APIRouter, HTTPException, Request
from typing import Dict
from app.services.pipeline_service import PipelineService
from app.services.file_service import FileService

router = APIRouter()
pipeline_service = PipelineService()
file_service = FileService()

@router.get("/status/{file_id}")
async def get_pipeline_status(file_id: str, request: Request) -> Dict:
    """
    Get the current status of pipeline processing for a file
    """
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
            
        file = await file_service.get_file(file_id, request.app.mongodb)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
            
        return {
            "file_id": file_id,
            "status": file.status,
            "progress": getattr(file, 'pipeline_progress', {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))