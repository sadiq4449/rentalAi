from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr, Field

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


class SetupAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


@router.post("/setup-admin")
async def setup_admin(
    data: SetupAdminRequest, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    One-time endpoint to create the super admin account.
    Fails with 409 if any admin user already exists.
    """
    return await auth_service.setup_super_admin(db, data.email, data.password)
