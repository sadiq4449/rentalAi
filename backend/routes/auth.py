from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from deps import create_access_token, get_current_user, get_database
from models.user import Token, UserCreate, UserLogin, UserOut
from services import auth_service

router = APIRouter()


@router.post("/register", response_model=Token)
async def register(data: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    user = await auth_service.register_user(db, data)
    token = create_access_token(user.id, user.email, user.role)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncIOMotorDatabase = Depends(get_database)):
    user = await auth_service.authenticate(db, data)
    token = create_access_token(user.id, user.email, user.role)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: UserOut = Depends(get_current_user)):
    return user
