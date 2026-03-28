from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.property import PropertyCreate, PropertyOut, PropertyUpdate

LISTING_PENDING = "pending"
LISTING_APPROVED = "approved"
LISTING_REJECTED = "rejected"


def _to_out(doc: dict) -> PropertyOut:
    return PropertyOut(
        id=str(doc["_id"]),
        owner_id=str(doc["owner_id"]),
        title=doc["title"],
        location=doc["location"],
        price=float(doc["price"]),
        bedrooms=int(doc["bedrooms"]),
        bathrooms=int(doc["bathrooms"]),
        property_type=doc["property_type"],
        description=doc.get("description") or "",
        amenities=list(doc.get("amenities") or []),
        images=list(doc.get("images") or []),
        listing_status=doc.get("listing_status", LISTING_PENDING),
        created_at=doc.get("created_at"),
    )


async def create_property(
    db: AsyncIOMotorDatabase, owner_id: str, data: PropertyCreate
) -> PropertyOut:
    now = datetime.now(timezone.utc)
    doc = {
        "owner_id": owner_id,
        "title": data.title.strip(),
        "location": data.location.strip(),
        "price": data.price,
        "bedrooms": data.bedrooms,
        "bathrooms": data.bathrooms,
        "property_type": data.property_type.strip(),
        "description": data.description.strip(),
        "amenities": data.amenities,
        "images": data.images,
        "listing_status": LISTING_PENDING,
        "created_at": now,
    }
    result = await db.properties.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _to_out(doc)


def _filter_query(
    location: Optional[str],
    price_min: Optional[float],
    price_max: Optional[float],
    bedrooms: Optional[str],
    only_approved: bool,
    property_type: Optional[str] = None,
) -> Dict[str, Any]:
    q: Dict[str, Any] = {}
    if only_approved:
        q["listing_status"] = LISTING_APPROVED
    if property_type:
        q["property_type"] = property_type.strip()
    if location:
        q["location"] = {"$regex": location.strip(), "$options": "i"}
    if price_min is not None:
        q.setdefault("price", {})["$gte"] = price_min
    if price_max is not None:
        q.setdefault("price", {})["$lte"] = price_max
    if bedrooms:
        if bedrooms == "4+":
            q["bedrooms"] = {"$gte": 4}
        elif bedrooms != "any":
            try:
                q["bedrooms"] = int(bedrooms)
            except ValueError:
                pass
    return q


async def list_properties(
    db: AsyncIOMotorDatabase,
    *,
    location: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    bedrooms: Optional[str] = None,
    property_type: Optional[str] = None,
    sort: str = "newest",
    only_approved: bool = True,
) -> List[PropertyOut]:
    q = _filter_query(location, price_min, price_max, bedrooms, only_approved, property_type)
    sort_key = "created_at"
    direction = -1
    if sort == "price-low":
        sort_key = "price"
        direction = 1
    elif sort == "price-high":
        sort_key = "price"
        direction = -1
    elif sort == "newest":
        sort_key = "created_at"
        direction = -1
    cursor = db.properties.find(q).sort(sort_key, direction)
    out: List[PropertyOut] = []
    async for doc in cursor:
        out.append(_to_out(doc))
    return out


async def get_property(db: AsyncIOMotorDatabase, prop_id: str) -> Optional[PropertyOut]:
    try:
        oid = ObjectId(prop_id)
    except Exception:
        return None
    doc = await db.properties.find_one({"_id": oid})
    if not doc:
        return None
    return _to_out(doc)


async def update_property(
    db: AsyncIOMotorDatabase, prop_id: str, owner_id: str, data: PropertyUpdate
) -> PropertyOut:
    try:
        oid = ObjectId(prop_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid property id")
    doc = await db.properties.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Property not found")
    if doc["owner_id"] != owner_id:
        raise HTTPException(status_code=403, detail="Not the owner")
    patch: Dict[str, Any] = {}
    if data.title is not None:
        patch["title"] = data.title.strip()
    if data.location is not None:
        patch["location"] = data.location.strip()
    if data.price is not None:
        patch["price"] = data.price
    if data.bedrooms is not None:
        patch["bedrooms"] = data.bedrooms
    if data.bathrooms is not None:
        patch["bathrooms"] = data.bathrooms
    if data.property_type is not None:
        patch["property_type"] = data.property_type.strip()
    if data.description is not None:
        patch["description"] = data.description.strip()
    if data.amenities is not None:
        patch["amenities"] = data.amenities
    if data.images is not None:
        patch["images"] = data.images
    if patch:
        await db.properties.update_one({"_id": oid}, {"$set": patch})
    updated = await db.properties.find_one({"_id": oid})
    return _to_out(updated)


async def delete_property(db: AsyncIOMotorDatabase, prop_id: str, owner_id: str) -> None:
    try:
        oid = ObjectId(prop_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid property id")
    doc = await db.properties.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Property not found")
    if doc["owner_id"] != owner_id:
        raise HTTPException(status_code=403, detail="Not the owner")
    await db.properties.delete_one({"_id": oid})
    await db.favorites.delete_many({"property_id": prop_id})


async def list_owner_properties(db: AsyncIOMotorDatabase, owner_id: str) -> List[PropertyOut]:
    cursor = db.properties.find({"owner_id": owner_id}).sort("created_at", -1)
    out: List[PropertyOut] = []
    async for doc in cursor:
        out.append(_to_out(doc))
    return out


async def set_listing_status(
    db: AsyncIOMotorDatabase, prop_id: str, status: str
) -> PropertyOut:
    if status not in (LISTING_APPROVED, LISTING_REJECTED):
        raise HTTPException(status_code=400, detail="Invalid status")
    try:
        oid = ObjectId(prop_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid property id")
    result = await db.properties.update_one(
        {"_id": oid}, {"$set": {"listing_status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    doc = await db.properties.find_one({"_id": oid})
    return _to_out(doc)


async def list_all_properties_admin(db: AsyncIOMotorDatabase) -> List[PropertyOut]:
    cursor = db.properties.find({}).sort("created_at", -1)
    out: List[PropertyOut] = []
    async for doc in cursor:
        out.append(_to_out(doc))
    return out
