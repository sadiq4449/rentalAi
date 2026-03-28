from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class PropertyCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    location: str = Field(min_length=1, max_length=300)
    price: float = Field(gt=0)
    bedrooms: int = Field(ge=0)
    bathrooms: int = Field(ge=0)
    property_type: str = Field(min_length=1, max_length=50)
    description: str = ""
    amenities: List[str] = []
    images: List[str] = []


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    property_type: Optional[str] = None
    description: Optional[str] = None
    amenities: Optional[List[str]] = None
    images: Optional[List[str]] = None


class PropertyOut(BaseModel):
    id: str
    owner_id: str
    title: str
    location: str
    price: float
    bedrooms: int
    bathrooms: int
    property_type: str
    description: str
    amenities: List[str]
    images: List[str]
    listing_status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PropertyFilterParams(BaseModel):
    location: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    bedrooms: Optional[str] = None
    sort: Optional[str] = "newest"
