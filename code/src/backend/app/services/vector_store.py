import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        try:
            # Use PersistentClient instead of HttpClient
            self.client = chromadb.PersistentClient(
                path="/tmp/chromadb",  # Store data in temporary directory
                settings=ChromaSettings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            # Initialize the collection
            self.collection = self._initialize_collection()
            logger.info("Successfully initialized ChromaDB connection")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise

    def _initialize_collection(self):
        """Initialize the collection with proper configuration"""
        try:
            return self.client.get_or_create_collection(
                name="entity_embeddings",
                metadata={"hnsw:space": "cosine"}  # Using cosine similarity for embeddings
            )
        except Exception as e:
            logger.error(f"Error initializing collection: {str(e)}")
            raise

    async def store_entity_embedding(self, entity_id: str, entity_name: str, embedding: List[float]):
        """Store entity embedding in ChromaDB"""
        try:
            # Ensure the embedding is properly formatted
            if not isinstance(embedding, list) or not all(isinstance(x, float) for x in embedding):
                raise ValueError("Embedding must be a list of float values")

            self.collection.upsert(
                ids=[entity_id],
                embeddings=[embedding],
                metadatas=[{
                    "name": entity_name,
                    "timestamp": str(datetime.utcnow())
                }]
            )
            logger.info(f"Stored embedding for entity {entity_name}")
            
        except Exception as e:
            logger.error(f"Error storing embedding for entity {entity_name}: {str(e)}")
            raise

    async def find_similar_entities(self, embedding: List[float], limit: int = 10) -> Dict:
        """Find similar entities based on embedding"""
        try:
            # Validate input
            if not isinstance(embedding, list) or not all(isinstance(x, float) for x in embedding):
                raise ValueError("Embedding must be a list of float values")

            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=min(limit, 100),  # Cap at 100 results
                include=["metadatas", "distances"]
            )
            
            return {
                "ids": results["ids"][0] if results["ids"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else []
            }
            
        except Exception as e:
            logger.error(f"Error querying similar entities: {str(e)}")
            raise

    async def delete_entity_embedding(self, entity_id: str):
        """Delete entity embedding from ChromaDB"""
        try:
            self.collection.delete(ids=[entity_id])
            logger.info(f"Deleted embedding for entity {entity_id}")
            
        except Exception as e:
            logger.error(f"Error deleting embedding for entity {entity_id}: {str(e)}")
            raise

    async def close(self):
        """Clean up resources"""
        try:
            # ChromaDB PersistentClient doesn't need explicit cleanup
            pass
        except Exception as e:
            logger.error(f"Error closing ChromaDB connection: {str(e)}")
            raise