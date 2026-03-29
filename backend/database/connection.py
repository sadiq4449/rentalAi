import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "rentalhome")

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        # Fail fast on Railway if MONGODB_URL wrong (default 30s is too long for startup)
        _client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=8000)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[DATABASE_NAME]


async def init_db() -> None:
    db = get_db()
    await db.users.create_index("email", unique=True)
    await db.favorites.create_index([("user_id", 1), ("property_id", 1)], unique=True)
    await db.properties.create_index("owner_id")
    await db.properties.create_index("listing_status")
    await db.messages.create_index([("sender_id", 1), ("receiver_id", 1), ("created_at", 1)])
    await db.bookings.create_index("seeker_id")
    await db.bookings.create_index("owner_id")
    await db.bookings.create_index("property_id")
