from typing import List

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from deps import get_current_user, get_database
from models.property import PropertyOut
from models.user import UserOut
from services import favorite_service

router = APIRouter()


@router.get("", response_model=List[PropertyOut])
async def list_favorites(
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await favorite_service.list_favorite_properties(db, user.id)


@router.post("/{property_id}")
async def add_favorite(
    property_id: str,
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await favorite_service.add_favorite(db, user.id, property_id)


@router.delete("/{property_id}")
async def remove_favorite(
    property_id: str,
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    await favorite_service.remove_favorite(db, user.id, property_id)
    return {"ok": True}
