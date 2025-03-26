from motor.motor_asyncio import AsyncIOMotorClient
from app.models.entity import Entity
from app.services.ofac_service import OFACService
from app.services.sec_service import SECService
from app.services.vector_store import VectorStore
from app.services.graph_store import GraphStore
from typing import List, Optional, Dict
import logging
from datetime import datetime
from uuid import UUID, uuid4
from bson import Binary

logger = logging.getLogger(__name__)

class EntityService:
    def __init__(self):
        self.collection_name = "entities"
        self.ofac_service = OFACService()
        self.sec_service = SECService()
        self.vector_store = VectorStore()
        self.graph_store = GraphStore()

    async def create_or_update_entity(
        self,
        name: str,
        entity_type: str,
        risk_score: float = 0.0,
        role: str = "UNKNOWN",
        db: AsyncIOMotorClient = None
    ) -> Entity:
        """Create a new entity or update if it already exists"""
        try:
            # Check if entity already exists
            existing_entity = await db[self.collection_name].find_one({
                "name": name,
                "type": entity_type
            })

            if existing_entity:
                # Update existing entity
                update_data = {
                    "risk_score": risk_score,
                    "updated_at": datetime.utcnow()
                }
                
                await db[self.collection_name].update_one(
                    {"_id": existing_entity["_id"]},
                    {"$set": update_data}
                )
                
                existing_entity.update(update_data)
                # Convert Binary UUID back to UUID for Entity model
                if isinstance(existing_entity.get('id'), Binary):
                    existing_entity['id'] = existing_entity['id'].as_uuid()
                return Entity(**existing_entity)
            else:
                # Create new entity
                entity_id = uuid4()
                new_entity = Entity(
                    id=entity_id,
                    name=name,
                    type=entity_type,
                    role=role,
                    risk_score=risk_score,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                # Convert to dict with proper UUID encoding
                entity_dict = new_entity.dict()
                await db[self.collection_name].insert_one(entity_dict)
                return new_entity

        except Exception as e:
            logger.error(f"Error creating/updating entity {name}: {str(e)}")
            raise

    async def search(self, query: str, db) -> List[Entity]:
        try:
            # Search for entities in MongoDB
            cursor = db[self.collection_name].find({
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"type": {"$regex": query, "$options": "i"}},
                    {"role": {"$regex": query, "$options": "i"}}
                ]
            })
            
            entities = await cursor.to_list(length=100)
            
            # Convert Binary UUIDs back to UUID objects
            for entity in entities:
                if isinstance(entity.get('id'), Binary):
                    entity['id'] = entity['id'].as_uuid()
            
            # Enrich each entity with latest data
            enriched_entities = []
            for entity in entities:
                enriched = await self.enrich_entity(entity, db)
                enriched_entities.append(enriched)
            
            # Store entity data in Neo4j
            for entity in enriched_entities:
                await self.graph_store.create_entity(entity.dict())
            
            return enriched_entities
            
        except Exception as e:
            logger.error(f"Error searching entities: {str(e)}")
            raise

    async def get_by_id(self, entity_id: str, db) -> Optional[Entity]:
        try:
            # Convert string ID to Binary UUID for MongoDB query
            binary_id = Binary.from_uuid(UUID(entity_id))
            entity = await db[self.collection_name].find_one({"id": binary_id})
            
            if entity:
                # Convert Binary UUID back to UUID
                if isinstance(entity.get('id'), Binary):
                    entity['id'] = entity['id'].as_uuid()
                    
                enriched_entity = await self.enrich_entity(entity, db)
                
                # Get graph connections
                connections = await self.graph_store.get_entity_connections(entity_id)
                enriched_entity.graph_data = connections
                
                return enriched_entity
            return None
            
        except Exception as e:
            logger.error(f"Error getting entity by ID: {str(e)}")
            raise

    async def enrich_entity(self, entity: Dict, db) -> Entity:
        """
        Enrich entity data with OFAC, SEC information and store in vector/graph databases.
        """
        try:
            # Get OFAC sanctions data
            ofac_data = await self.ofac_service.check_sanctions(entity["name"], db)
            
            # Get SEC data if entity is an organization
            sec_data = None
            if entity.get("type") == "ORGANIZATION" and entity.get("sec_cik"):
                sec_data = await self.sec_service.get_company_info(entity["sec_cik"], db)
            
            # Update enrichment data
            entity["enrichment_data"] = {
                "ofac": ofac_data,
                "sec": sec_data,
                "last_updated": datetime.utcnow()
            }
            
            # Calculate risk score based on enrichment data
            entity["risk_score"] = await self._calculate_risk_score(entity)
            
            # Store entity embedding in ChromaDB
            # Note: In a real implementation, you would generate proper embeddings
            dummy_embedding = [0.0] * 384  # Example dimension
            await self.vector_store.store_entity_embedding(
                str(entity["id"]),
                entity["name"],
                dummy_embedding
            )
            
            # Update entity in MongoDB
            await db[self.collection_name].update_one(
                {"id": Binary.from_uuid(entity["id"]) if isinstance(entity["id"], UUID) else entity["id"]},
                {"$set": {
                    "enrichment_data": entity["enrichment_data"],
                    "risk_score": entity["risk_score"],
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return Entity(**entity)
            
        except Exception as e:
            logger.error(f"Error enriching entity data: {str(e)}")
            raise

    async def _calculate_risk_score(self, entity: Dict) -> float:
        """
        Calculate risk score based on enrichment data.
        Returns a score between 0 and 100.
        """
        try:
            base_score = 0
            
            # OFAC sanctions check (highest weight)
            if entity.get("enrichment_data", {}).get("ofac", {}).get("sanctioned"):
                base_score += 70
            
            # SEC violations check
            sec_data = entity.get("enrichment_data", {}).get("sec", {})
            if sec_data:
                if sec_data.get("violations", []):
                    base_score += len(sec_data["violations"]) * 5
                    
            # Media sentiment analysis (if available)
            media_data = entity.get("enrichment_data", {}).get("media", {})
            if media_data and "sentiment" in media_data:
                # Negative sentiment increases risk score
                if media_data["sentiment"] < 0:
                    base_score += abs(media_data["sentiment"]) * 10
            
            # Cap the score at 100
            return min(base_score, 100)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 50  # Return moderate risk score in case of error