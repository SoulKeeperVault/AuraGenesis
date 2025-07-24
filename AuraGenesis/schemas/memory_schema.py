from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import uuid

class Memory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    content: str
    source: str
    emotional_tags: List[str] = Field(default_factory=list)
    semantic_embedding: Optional[List[float]] = None

    class Config:
        from_attributes = True
