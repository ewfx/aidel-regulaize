
from app.database import mongo_db
from app.core.config import settings

sanctions_collection = mongo_db.get_collection(settings.MONGO_OFAC_COLLECTION)

def search_sanctioned_entity(name):
    result = sanctions_collection.find_one({"name": {"$regex": name, "$options": "i"}})
    return result if result else "No matching entity found."