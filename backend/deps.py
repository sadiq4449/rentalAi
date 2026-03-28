import os
from typing import Annotated, Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorDatabase

from database.connection import get_db
from models.user import Role, UserOut

SECRET_KEY = os.getenv("JWT_SECRET", "local-dev-secret-change-me")
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


def get_database() -> AsyncIOMotorDatabase:
    return get_db()


def create_access_token(user_id: str, email: str, role: str) -> str:
    from datetime import datetime, timedelta, timezone

    expire = datetime.now(timezone.utc) + timedelta(days=7)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> Optional[UserOut]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        uid = payload.get("sub")
        if not uid:
            return None
        doc = await db.users.find_one({"_id": ObjectId(uid)})
        if not doc:
            return None
        return UserOut(
            id=str(doc["_id"]),
            email=doc["email"],
            name=doc["name"],
            role=doc["role"],
            created_at=doc.get("created_at"),
        )
    except (JWTError, InvalidId):
        return None


async def get_current_user(
    user: Annotated[Optional[UserOut], Depends(get_current_user_optional)],
) -> UserOut:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_admin(
    user: Annotated[UserOut, Depends(get_current_user)],
) -> UserOut:
    if user.role != Role.admin.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


def parse_oid(s: str) -> ObjectId:
    try:
        return ObjectId(s)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid id")
