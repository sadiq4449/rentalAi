import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError

from models.user import Role, UserCreate, UserLogin, UserOut

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str | None) -> bool:
    """Return False on mismatch; never raise (bad/corrupt hashes caused 500 before)."""
    if not hashed or not isinstance(hashed, str) or not hashed.strip():
        return False
    try:
        return bool(pwd_context.verify(plain, hashed))
    except Exception:
        return False


def user_doc_to_out(doc: dict) -> UserOut:
    """Build UserOut from a Mongo user document (missing fields won't 500)."""
    return UserOut(
        id=str(doc["_id"]),
        email=doc.get("email") or "",
        name=(doc.get("name") or "").strip() or "User",
        role=str(doc.get("role") or "seeker"),
        created_at=doc.get("created_at"),
    )


async def register_user(db: AsyncIOMotorDatabase, data: UserCreate) -> UserOut:
    if data.role == Role.admin:
        n_admins = await db.users.count_documents({"role": Role.admin.value})
        if n_admins > 0:
            raise HTTPException(
                status_code=403,
                detail="Super Admin sign-up is only available when no admin exists yet. Log in with your admin account instead.",
            )
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
    email = (data.email or "").strip().lower()
    doc = await db.users.find_one({"email": email})
    pw_hash = doc.get("password_hash") if doc else None
    if not doc or not verify_password(data.password, pw_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user_doc_to_out(doc)


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> UserOut | None:
    try:
        oid = ObjectId(user_id)
    except Exception:
        return None
    doc = await db.users.find_one({"_id": oid})
    if not doc:
        return None
    return user_doc_to_out(doc)


DEFAULT_ADMIN_EMAIL = "sadiq@gmail.com"
_DEFAULT_ADMIN_PASSWORD = "sadiq123"


async def ensure_default_admin(db: AsyncIOMotorDatabase, *, force_password: bool = False) -> None:
    """Ensure super admin exists (seed on empty DB; promote same email if not admin).

    If admin already exists but login fails (wrong hash), run seed with --force or set
    FORCE_SEED_ADMIN_PASSWORD=1 once on Railway, then remove it.
    """
    existing = await db.users.find_one({"email": DEFAULT_ADMIN_EMAIL})
    if existing:
        if existing.get("role") == Role.admin.value:
            if force_password:
                await db.users.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"password_hash": hash_password(_DEFAULT_ADMIN_PASSWORD)}},
                )
                logger.info(
                    "Super admin password reset for %s (force_password)", DEFAULT_ADMIN_EMAIL
                )
            else:
                logger.info("Super admin already exists: %s", DEFAULT_ADMIN_EMAIL)
            return
        await db.users.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "role": Role.admin.value,
                    "password_hash": hash_password(_DEFAULT_ADMIN_PASSWORD),
                    "name": existing.get("name") or "Sadiq",
                }
            },
        )
        logger.info("Promoted existing user to super admin: %s", DEFAULT_ADMIN_EMAIL)
        return
    now = datetime.now(timezone.utc)
    doc = {
        "email": DEFAULT_ADMIN_EMAIL,
        "password_hash": hash_password(_DEFAULT_ADMIN_PASSWORD),
        "name": "Sadiq",
        "role": Role.admin.value,
        "created_at": now,
    }
    try:
        await db.users.insert_one(doc)
        logger.info("Created super admin user: %s", DEFAULT_ADMIN_EMAIL)
    except DuplicateKeyError:
        # Same email inserted elsewhere (race) — align role/password
        again = await db.users.find_one({"email": DEFAULT_ADMIN_EMAIL})
        if again and again.get("role") != Role.admin.value:
            await db.users.update_one(
                {"_id": again["_id"]},
                {
                    "$set": {
                        "role": Role.admin.value,
                        "password_hash": hash_password(_DEFAULT_ADMIN_PASSWORD),
                        "name": again.get("name") or "Sadiq",
                    }
                },
            )
            logger.info("Promoted user after duplicate-key race: %s", DEFAULT_ADMIN_EMAIL)
        elif again and force_password:
            await db.users.update_one(
                {"_id": again["_id"]},
                {"$set": {"password_hash": hash_password(_DEFAULT_ADMIN_PASSWORD)}},
            )
            logger.info("Password reset after duplicate-key race: %s", DEFAULT_ADMIN_EMAIL)
        else:
            logger.info("Super admin already present (duplicate insert skipped): %s", DEFAULT_ADMIN_EMAIL)


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
