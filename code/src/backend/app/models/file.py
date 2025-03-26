from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from uuid import UUID

class FileMetadata(BaseModel):
    id: str
    filename: str
    size: int
    format: Literal["JSON", "CSV", "EXCEL", "XML", "PDF", "TXT"]
    uploadedBy: str
    status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
    createdAt: datetime
    updatedAt: datetime