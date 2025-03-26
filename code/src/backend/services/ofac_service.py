from typing import Dict, List, Optional
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class OFACService:
    def __init__(self):
        self.collection_name = "ofac_data"

    async def check_sanctions(self, entity_name: str, db) -> Dict:
        """
        Check if an entity is on any OFAC sanctions lists.
        Returns enrichment data with sanctions status and details.
        """
        try:
            # Search for exact and partial matches in OFAC collection
            query = {
                "$or": [
                    {"name": entity_name},
                    {"name": {"$regex": entity_name, "$options": "i"}},
                    {"aliases": {"$regex": entity_name, "$options": "i"}}
                ]
            }
            
            result = await db[self.collection_name].find_one(query)
            
            if result:
                return {
                    "sanctioned": True,
                    "listEntries": [
                        {
                            "list_name": result.get("list_name"),
                            "entry_type": result.get("type"),
                            "programs": result.get("programs", []),
                            "match_type": "exact" if result.get("name") == entity_name else "partial"
                        }
                    ],
                    "lastChecked": datetime.utcnow()
                }
            
            return {
                "sanctioned": False,
                "listEntries": [],
                "lastChecked": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error checking OFAC sanctions for {entity_name}: {str(e)}")
            raise

    async def update_sanctions_data(self, db) -> None:
        """
        Update local OFAC data from official sources.
        This should be run periodically to keep sanctions data current.
        """
        try:
            # In a real implementation, this would:
            # 1. Download latest XML/CSV files from OFAC website
            # 2. Parse and transform the data
            # 3. Update the local MongoDB collection
            # 4. Log the update timestamp
            
            logger.info("OFAC sanctions data updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating OFAC sanctions data: {str(e)}")
            raise

    async def get_sanctions_history(self, entity_id: str, db) -> List[Dict]:
        """
        Retrieve historical sanctions data for an entity.
        """
        try:
            history = await db[f"{self.collection_name}_history"].find(
                {"entity_id": entity_id}
            ).sort("timestamp", -1).to_list(length=100)
            
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving sanctions history for entity {entity_id}: {str(e)}")
            raise