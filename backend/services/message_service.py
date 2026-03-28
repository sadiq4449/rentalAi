from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.message import MessageOut


def _msg_out(doc: dict) -> MessageOut:
    return MessageOut(
        id=str(doc["_id"]),
        sender_id=str(doc["sender_id"]),
        receiver_id=str(doc["receiver_id"]),
        property_id=doc.get("property_id"),
        body=doc["body"],
        created_at=doc.get("created_at"),
    )


async def send_message(
    db: AsyncIOMotorDatabase,
    sender_id: str,
    receiver_id: str,
    body: str,
    property_id: Optional[str] = None,
) -> MessageOut:
    if sender_id == receiver_id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")
    try:
        ObjectId(receiver_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid receiver id")
    other = await db.users.find_one({"_id": ObjectId(receiver_id)})
    if not other:
        raise HTTPException(status_code=404, detail="Receiver not found")
    now = datetime.now(timezone.utc)
    doc = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "body": body.strip(),
        "created_at": now,
    }
    if property_id:
        doc["property_id"] = property_id
    r = await db.messages.insert_one(doc)
    doc["_id"] = r.inserted_id
    return _msg_out(doc)


async def get_messages_with_user(
    db: AsyncIOMotorDatabase, me: str, other_user_id: str
) -> List[MessageOut]:
    try:
        ObjectId(other_user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")
    q = {
        "$or": [
            {"sender_id": me, "receiver_id": other_user_id},
            {"sender_id": other_user_id, "receiver_id": me},
        ]
    }
    cursor = db.messages.find(q).sort("created_at", 1)
    out: List[MessageOut] = []
    async for doc in cursor:
        out.append(_msg_out(doc))
    return out


async def list_conversations(db: AsyncIOMotorDatabase, me: str) -> List[Dict[str, Any]]:
    pipeline = [
        {
            "$match": {
                "$or": [{"sender_id": me}, {"receiver_id": me}],
            }
        },
        {"$sort": {"created_at": -1}},
        {
            "$group": {
                "_id": {
                    "$cond": [
                        {"$eq": ["$sender_id", me]},
                        "$receiver_id",
                        "$sender_id",
                    ]
                },
                "last_message": {"$first": "$$ROOT"},
            }
        },
    ]
    convos: List[Dict[str, Any]] = []
    async for row in db.messages.aggregate(pipeline):
        other_id = row["_id"]
        lm = row["last_message"]
        user = await db.users.find_one({"_id": ObjectId(other_id)})
        convos.append(
            {
                "user_id": other_id,
                "name": user["name"] if user else "Unknown",
                "last_message": lm.get("body", ""),
                "created_at": lm.get("created_at"),
            }
        )
    return convos
