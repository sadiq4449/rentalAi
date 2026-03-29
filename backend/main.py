import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database.connection import init_db
from routes import admin, auth, bookings, chat, favorites, properties
from services import auth_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Railway has no local MongoDB — if MONGODB_URL is missing/wrong, startup used to crash → "Application failed to respond"
    try:
        await init_db()
        from database.connection import get_db

        await auth_service.ensure_default_admin(get_db())
    except Exception:
        logger.exception(
            "MongoDB init failed — set MONGODB_URL in Railway Variables (e.g. MongoDB Atlas). "
            "App will still start; API calls need DB."
        )
    yield


app = FastAPI(title="RentHome API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(properties.router, prefix="/api/properties", tags=["properties"])
app.include_router(favorites.router, prefix="/api/favorites", tags=["favorites"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/health")
async def health_root():
    """Railway / probes often use /health"""
    return {"status": "ok"}


# Same-origin UI + API (Railway: one URL). Requires Frontend copied to ./static/ (see root Dockerfile).
_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
