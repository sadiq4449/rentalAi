from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, model_validator


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
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)

    @model_validator(mode="after")
    def latitude_longitude_pair(self):
        if (self.latitude is None) ^ (self.longitude is None):
            raise ValueError("Provide both latitude and longitude, or neither")
        return self


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
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)

    @model_validator(mode="after")
    def latitude_longitude_pair(self):
        if (self.latitude is None) ^ (self.longitude is None):
            raise ValueError("Provide both latitude and longitude, or neither")
        return self


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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PropertyFilterParams(BaseModel):
    location: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    bedrooms: Optional[str] = None
    sort: Optional[str] = "newest"
