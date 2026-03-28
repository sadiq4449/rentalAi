from datetime import date, datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.booking import BookingCreate, BookingOut
from models.user import Role
from services import property_service


def _parse_visit_date(v) -> date:
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        return date.fromisoformat(v[:10])
    raise ValueError("Invalid visit_date")


async def _enrich(db: AsyncIOMotorDatabase, doc: dict) -> dict:
    out = dict(doc)
    try:
        seeker = await db.users.find_one({"_id": ObjectId(doc["seeker_id"])})
        out["seeker_name"] = seeker["name"] if seeker else None
    except Exception:
        out["seeker_name"] = None
    try:
        prop = await db.properties.find_one({"_id": ObjectId(doc["property_id"])})
        out["property_title"] = prop["title"] if prop else None
    except Exception:
        out["property_title"] = None
    return out


def _out(doc: dict) -> BookingOut:
    vd = _parse_visit_date(doc.get("visit_date"))
    return BookingOut(
        id=str(doc["_id"]),
        seeker_id=str(doc["seeker_id"]),
        property_id=str(doc["property_id"]),
        owner_id=str(doc["owner_id"]),
        visit_date=vd,
        visit_time=doc["visit_time"],
        notes=doc.get("notes") or "",
        status=doc["status"],
        created_at=doc.get("created_at"),
        seeker_name=doc.get("seeker_name"),
        property_title=doc.get("property_title"),
    )


async def create_booking(
    db: AsyncIOMotorDatabase, seeker_id: str, data: BookingCreate
) -> BookingOut:
    prop = await property_service.get_property(db, data.property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if prop.listing_status != property_service.LISTING_APPROVED:
        raise HTTPException(status_code=400, detail="Property not available for booking")
    if prop.owner_id == seeker_id:
        raise HTTPException(status_code=400, detail="Cannot book your own property")
    now = datetime.now(timezone.utc)
    vd = data.visit_date
    if isinstance(vd, datetime):
        vd = vd.date()
    doc = {
        "seeker_id": seeker_id,
        "property_id": data.property_id,
        "owner_id": prop.owner_id,
        "visit_date": vd.isoformat(),
        "visit_time": data.visit_time.strip(),
        "notes": data.notes.strip(),
        "status": "pending",
        "created_at": now,
    }
    r = await db.bookings.insert_one(doc)
    doc["_id"] = r.inserted_id
    doc = await _enrich(db, doc)
    return _out(doc)


async def list_for_seeker(db: AsyncIOMotorDatabase, seeker_id: str) -> List[BookingOut]:
    cursor = db.bookings.find({"seeker_id": seeker_id}).sort("created_at", -1)
    out: List[BookingOut] = []
    async for doc in cursor:
        out.append(_out(doc))
    return out


async def list_for_owner(db: AsyncIOMotorDatabase, owner_id: str) -> List[BookingOut]:
    cursor = db.bookings.find({"owner_id": owner_id}).sort("created_at", -1)
    out: List[BookingOut] = []
    async for doc in cursor:
        out.append(_out(doc))
    return out


async def list_all(db: AsyncIOMotorDatabase) -> List[BookingOut]:
    cursor = db.bookings.find({}).sort("created_at", -1)
    out: List[BookingOut] = []
    async for doc in cursor:
        out.append(_out(doc))
    return out


async def set_status(
    db: AsyncIOMotorDatabase,
    booking_id: str,
    owner_id: str,
    new_status: str,
    user_role: str,
) -> BookingOut:
    if new_status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")
    try:
        oid = ObjectId(booking_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid booking id")
    doc = await db.bookings.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Booking not found")
    if doc["owner_id"] != owner_id and user_role != Role.admin.value:
        raise HTTPException(status_code=403, detail="Not allowed")
    await db.bookings.update_one({"_id": oid}, {"$set": {"status": new_status}})
    updated = await db.bookings.find_one({"_id": oid})
    updated = await _enrich(db, updated)
    return _out(updated)
