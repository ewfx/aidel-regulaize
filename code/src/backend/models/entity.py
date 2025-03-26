from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID, uuid4
from bson import Binary

class EnrichmentData(BaseModel):
    sec: Optional[Dict] = None
    ofac: Optional[Dict] = None
    media: Optional[Dict] = None
    regulatory: Optional[Dict] = None
    legal: Optional[Dict] = None

class Entity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: str
    role: str
    enrichment_data: EnrichmentData = Field(default_factory=EnrichmentData)
    risk_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID: lambda v: Binary.from_uuid(v),
            datetime: lambda v: v.isoformat()
        }

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        # Convert UUID to Binary for MongoDB
        if 'id' in d and isinstance(d['id'], UUID):
            d['id'] = Binary.from_uuid(d['id'])
        return d