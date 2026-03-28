from typing import List

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from deps import get_current_user, get_database
from models.booking import BookingCreate, BookingOut
from models.user import Role, UserOut
from services import booking_service as booking_svc

router = APIRouter()


@router.post("", response_model=BookingOut)
async def create_booking(
    data: BookingCreate,
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if user.role not in (Role.seeker.value, Role.admin.value):
        raise HTTPException(status_code=403, detail="Seekers only")
    return await booking_svc.create_booking(db, user.id, data)


@router.get("", response_model=List[BookingOut])
async def list_bookings(
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if user.role == Role.owner.value:
        return await booking_svc.list_for_owner(db, user.id)
    if user.role == Role.seeker.value:
        return await booking_svc.list_for_seeker(db, user.id)
    if user.role == Role.admin.value:
        return await booking_svc.list_all(db)
    raise HTTPException(status_code=403, detail="Not allowed")


@router.put("/{booking_id}/approve", response_model=BookingOut)
async def approve_booking(
    booking_id: str,
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if user.role not in (Role.owner.value, Role.admin.value):
        raise HTTPException(status_code=403, detail="Owners only")
    return await booking_svc.set_status(db, booking_id, user.id, "approved", user.role)


@router.put("/{booking_id}/reject", response_model=BookingOut)
async def reject_booking(
    booking_id: str,
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if user.role not in (Role.owner.value, Role.admin.value):
        raise HTTPException(status_code=403, detail="Owners only")
    return await booking_svc.set_status(db, booking_id, user.id, "rejected", user.role)
