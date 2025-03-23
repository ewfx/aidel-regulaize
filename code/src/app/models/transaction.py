from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID

class Address(BaseModel):
    street: str
    city: str
    state: Optional[str] = ""
    zip: Optional[str] = ""
    country: str

class Entity(BaseModel):
    name: str
    address: Address

class TransactionRequest(BaseModel):
    transactionID: str = Field(..., description="Unique transaction identifier")
    payer: Entity
    receiver: Entity
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    description: Optional[str] = ""

class ExternalData(BaseModel):
    openCorporates: Optional[Dict]
    wikidata: Optional[Dict]
    secEDGAR: Optional[Dict]
    ofac: Dict

class EntityRiskProfile(BaseModel):
    name: str
    riskScore: float
    justification: str
    externalData: ExternalData

class TransactionResponse(BaseModel):
    transactionID: str
    entities: List[EntityRiskProfile]
    auditInfo: Dict
    processedAt: datetime = Field(default_factory=datetime.utcnow)