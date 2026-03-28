from typing import List

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from services import property_service


async def add_favorite(db: AsyncIOMotorDatabase, user_id: str, property_id: str) -> dict:
    prop = await property_service.get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.listing_status != property_service.LISTING_APPROVED:
        raise HTTPException(status_code=400, detail="Property is not available")
    try:
        await db.favorites.insert_one({"user_id": user_id, "property_id": property_id})
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Already in favorites")
    return {"ok": True, "property_id": property_id}


async def remove_favorite(db: AsyncIOMotorDatabase, user_id: str, property_id: str) -> None:
    await db.favorites.delete_many({"user_id": user_id, "property_id": property_id})


async def list_favorite_properties(db: AsyncIOMotorDatabase, user_id: str):
    cursor = db.favorites.find({"user_id": user_id})
    ids: List[str] = []
    async for doc in cursor:
        ids.append(doc["property_id"])
    result = []
    for pid in ids:
        p = await property_service.get_property(db, pid)
        if p and p.listing_status == property_service.LISTING_APPROVED:
            result.append(p)
    return result


async def is_favorite(db: AsyncIOMotorDatabase, user_id: str, property_id: str) -> bool:
    n = await db.favorites.count_documents({"user_id": user_id, "property_id": property_id})
    return n > 0
