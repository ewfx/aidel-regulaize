from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from app.models.entity import Entity
from app.services.entity_service import EntityService
from app.core.config import settings

router = APIRouter()
entity_service = EntityService()

@router.get("", response_model=List[Entity])
async def search_entities(
    request: Request,
    query: str,
    entity_type: Optional[str] = None,
    risk_threshold: Optional[float] = None
):
    """Search entities with optional filters"""
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        entities = await entity_service.search(query, request.app.mongodb)
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{entity_id}", response_model=Entity)
async def get_entity(entity_id: str, request: Request):
    """Get entity by ID"""
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        entity = await entity_service.get_by_id(entity_id, request.app.mongodb)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        return entity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{entity_id}/relationships", response_model=List[dict])
async def get_entity_relationships(
    entity_id: str,
    request: Request,
    depth: int = 2
):
    """Get entity relationships from graph database"""
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        relationships = await entity_service.graph_store.get_entity_connections(entity_id, depth)
        return relationships
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{entity_id}/risk-history", response_model=List[dict])
async def get_entity_risk_history(entity_id: str, request: Request):
    """Get historical risk scores for an entity"""
    try:
        if not hasattr(request, 'app') or not hasattr(request.app, 'mongodb'):
            raise HTTPException(status_code=500, detail="Database connection not available")
        history = await entity_service.get_risk_history(entity_id, request.app.mongodb)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))