from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext

from models.user import Role, UserCreate, UserLogin, UserOut

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def register_user(db: AsyncIOMotorDatabase, data: UserCreate) -> UserOut:
    if data.role == Role.admin:
        raise HTTPException(status_code=400, detail="Cannot register as admin")
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    now = datetime.now(timezone.utc)
    doc = {
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "name": data.name.strip(),
        "role": data.role.value,
        "created_at": now,
    }
    result = await db.users.insert_one(doc)
    return UserOut(
        id=str(result.inserted_id),
        email=doc["email"],
        name=doc["name"],
        role=doc["role"],
        created_at=now,
    )


async def authenticate(db: AsyncIOMotorDatabase, data: UserLogin) -> UserOut:
    doc = await db.users.find_one({"email": data.email.lower()})
    if not doc or not verify_password(data.password, doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return UserOut(
        id=str(doc["_id"]),
        email=doc["email"],
        name=doc["name"],
        role=doc["role"],
        created_at=doc.get("created_at"),
    )


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> UserOut | None:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    doc = await db.users.find_one({"_id": oid})
    if not doc:
        return None
    return UserOut(
        id=str(doc["_id"]),
        email=doc["email"],
        name=doc["name"],
        role=doc["role"],
        created_at=doc.get("created_at"),
    )


async def ensure_default_admin(db: AsyncIOMotorDatabase) -> None:
    existing = await db.users.find_one({"email": "admin@local.test"})
    if existing:
        return
    now = datetime.now(timezone.utc)
    doc = {
        "email": "admin@local.test",
        "password_hash": hash_password("admin123"),
        "name": "Admin",
        "role": Role.admin.value,
        "created_at": now,
    }
    await db.users.insert_one(doc)


async def setup_super_admin(
    db: AsyncIOMotorDatabase, email: str, password: str
) -> dict:
    """Create a super admin user only if no admin account exists yet."""
    existing_admin = await db.users.find_one({"role": Role.admin.value})
    if existing_admin:
        raise HTTPException(
            status_code=409,
            detail="An admin account already exists. Setup is disabled.",
        )
    existing_email = await db.users.find_one({"email": email.lower()})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    now = datetime.now(timezone.utc)
    doc = {
        "email": email.lower(),
        "password_hash": hash_password(password),
        "name": "Super Admin",
        "role": Role.admin.value,
        "created_at": now,
    }
    result = await db.users.insert_one(doc)
    return {"message": "Super admin created successfully", "id": str(result.inserted_id)}
