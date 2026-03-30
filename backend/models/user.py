from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class Role(str, Enum):
    owner = "owner"
    seeker = "seeker"
    admin = "admin"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=120)
    role: Role = Role.seeker


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_created_at(cls, v: Any) -> Optional[datetime]:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        # Handle MongoDB extended JSON format: {'$date': '...'} or {'$date': <ms>}
        if isinstance(v, dict) and "$date" in v:
            raw = v["$date"]
            if isinstance(raw, (int, float)):
                # Milliseconds since epoch
                return datetime.fromtimestamp(raw / 1000, tz=timezone.utc)
            if isinstance(raw, str):
                # ISO 8601 string, e.g. "2026-03-30T04:20:22.268Z"
                raw = raw.replace("Z", "+00:00")
                return datetime.fromisoformat(raw)
        # Last resort: let Pydantic attempt its own coercion
        return v


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
