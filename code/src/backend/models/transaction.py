from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple, Union
from datetime import datetime
from uuid import UUID, uuid4
from .entity import Entity

class TransactionResponse(BaseModel):
    transaction_id: str
    extracted_entities: List[str]
    entity_types: List[str]
    risk_score: float
    supporting_evidence: List[str]
    confidence_score: float
    reason: str

class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    transaction_id: Optional[str] = None
    file_id: Optional[str] = None
    raw_data: str
    sender: Optional[Dict] = Field(default_factory=dict)
    receiver: Optional[Dict] = Field(default_factory=dict)
    amount: Optional[Dict] = Field(default_factory=dict)
    date: Optional[str] = None
    additional_notes: Optional[str] = None
    extracted_entities: Optional[Dict] = Field(default_factory=dict)
    entities: List[Entity] = Field(default_factory=list)
    risk_score: float = 0.0
    risk_factors: List[Dict] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    reason: Optional[str] = None
    status: str = "PENDING"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

class TransactionCreate(BaseModel):
    raw_data: str
    file_id: Optional[str] = None
    transaction_id: Optional[str] = None
    sender: Optional[Dict] = None
    receiver: Optional[Dict] = None
    amount: Optional[Dict] = None
    date: Optional[str] = None
    additional_notes: Optional[str] = None

class TransactionUpdate(BaseModel):
    status: Optional[str] = None
    risk_score: Optional[float] = None
    risk_factors: Optional[List[Dict]] = None
    entities: Optional[List[Entity]] = None
    extracted_entities: Optional[Dict] = None
    supporting_evidence: Optional[List[str]] = None
    confidence_score: Optional[float] = None
    reason: Optional[str] = None
    sender: Optional[Dict] = None
    receiver: Optional[Dict] = None
    amount: Optional[Dict] = None
    date: Optional[str] = None
    additional_notes: Optional[str] = None