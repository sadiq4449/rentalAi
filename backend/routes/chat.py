from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from deps import get_current_user, get_database
from models.message import MessageCreate, MessageOut
from models.user import UserOut
from services import message_service

router = APIRouter()


@router.get("/conversations", response_model=List[Dict[str, Any]])
async def conversations(
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await message_service.list_conversations(db, user.id)


@router.get("/messages/{other_user_id}", response_model=List[MessageOut])
async def get_messages(
    other_user_id: str,
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await message_service.get_messages_with_user(db, user.id, other_user_id)


@router.post("/send", response_model=MessageOut)
async def send(
    data: MessageCreate,
    user: UserOut = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    return await message_service.send_message(
        db,
        user.id,
        data.receiver_id,
        data.body,
        data.property_id,
    )
