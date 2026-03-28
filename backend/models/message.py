from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    receiver_id: str = Field(min_length=1)
    body: str = Field(min_length=1, max_length=5000)
    property_id: Optional[str] = None


class MessageOut(BaseModel):
    id: str
    sender_id: str
    receiver_id: str
    property_id: Optional[str] = None
    body: str
    created_at: Optional[datetime] = None
