from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.entity import Entity
from app.services.entity_service import EntityService
from app.core.config import settings

router = APIRouter()
entity_service = EntityService()

@router.get("", response_model=List[Entity])
async def search_entities(query: str):
    try:
        entities = await entity_service.search(query)
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{entity_id}", response_model=Entity)
async def get_entity(entity_id: str):
    try:
        entity = await entity_service.get_by_id(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")
        return entity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))