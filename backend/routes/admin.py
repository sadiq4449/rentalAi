from typing import List

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from deps import get_database, require_admin
from models.property import PropertyOut
from models.user import UserOut
from services import property_service

router = APIRouter()


@router.get("/properties", response_model=List[PropertyOut])
async def all_properties(
    _: UserOut = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await property_service.list_all_properties_admin(db)


@router.put("/properties/{property_id}/approve", response_model=PropertyOut)
async def approve_listing(
    property_id: str,
    _: UserOut = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await property_service.set_listing_status(
        db, property_id, property_service.LISTING_APPROVED
    )


@router.put("/properties/{property_id}/reject", response_model=PropertyOut)
async def reject_listing(
    property_id: str,
    _: UserOut = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await property_service.set_listing_status(
        db, property_id, property_service.LISTING_REJECTED
    )
