from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class BookingStatus:
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class BookingCreate(BaseModel):
    property_id: str = Field(min_length=1)
    visit_date: date
    visit_time: str = Field(min_length=1, max_length=40)
    notes: str = ""


class BookingOut(BaseModel):
    id: str
    seeker_id: str
    property_id: str
    owner_id: str
    visit_date: date
    visit_time: str
    notes: str
    status: str
    created_at: Optional[datetime] = None
    seeker_name: Optional[str] = None
    property_title: Optional[str] = None
