from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from deps import get_current_user, get_current_user_optional, get_database
from models.property import PropertyCreate, PropertyOut, PropertyUpdate
from models.user import Role, UserOut
from services import property_service

router = APIRouter()


@router.get("", response_model=List[PropertyOut])
async def list_properties(
    db: AsyncIOMotorDatabase = Depends(get_database),
    location: Optional[str] = None,
    price_min: Optional[float] = Query(None, alias="price_min"),
    price_max: Optional[float] = Query(None, alias="price_max"),
    bedrooms: Optional[str] = None,
    property_type: Optional[str] = Query(None, alias="property_type"),
    sort: str = "newest",
):
    return await property_service.list_properties(
        db,
        location=location,
        price_min=price_min,
        price_max=price_max,
        bedrooms=bedrooms,
        property_type=property_type,
        sort=sort,
        only_approved=True,
    )


@router.get("/mine", response_model=List[PropertyOut])
async def my_properties(
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if user.role not in (Role.owner.value, Role.admin.value):
        raise HTTPException(status_code=403, detail="Owners only")
    return await property_service.list_owner_properties(db, user.id)


@router.get("/{property_id}", response_model=PropertyOut)
async def get_property(
    property_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user: Optional[UserOut] = Depends(get_current_user_optional),
):
    p = await property_service.get_property(db, property_id)
    if not p:
        raise HTTPException(status_code=404, detail="Property not found")
    if p.listing_status == property_service.LISTING_APPROVED:
        return p
    if user and (user.id == p.owner_id or user.role == Role.admin.value):
        return p
    raise HTTPException(status_code=404, detail="Property not found")


@router.post("", response_model=PropertyOut)
async def create_property(
    data: PropertyCreate,
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if user.role not in (Role.owner.value, Role.admin.value):
        raise HTTPException(status_code=403, detail="Owners only")
    return await property_service.create_property(db, user.id, data)


@router.put("/{property_id}", response_model=PropertyOut)
async def update_property(
    property_id: str,
    data: PropertyUpdate,
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await property_service.update_property(db, property_id, user.id, data)


@router.delete("/{property_id}")
async def delete_property(
    property_id: str,
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    await property_service.delete_property(db, property_id, user.id)
    return {"ok": True}
