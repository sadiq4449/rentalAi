import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database.connection import DATABASE_NAME, MONGODB_URL, init_db
from routes import admin, auth, bookings, chat, favorites, properties
from services import auth_service
from services.auth_service import DEFAULT_ADMIN_EMAIL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Railway: keep app up if DB is down; indexes vs admin seed are separate so one failure doesn't skip the other.
    try:
        await init_db()
    except Exception:
        logger.exception(
            "MongoDB init_db (indexes) failed — check MONGO_URL / MONGODB_URL in Railway Variables."
        )
    try:
        from database.connection import get_db

        logger.info(
            "Startup: DATABASE_NAME=%s (same name must be used for seed script & Railway)",
            DATABASE_NAME,
        )
        if not MONGODB_URL or MONGODB_URL == "mongodb://localhost:27017":
            logger.warning(
                "Mongo URL is default localhost — on Railway set MONGO_URL or MONGODB_URL."
            )
        force_pw = os.getenv("FORCE_SEED_ADMIN_PASSWORD", "").lower() in ("1", "true", "yes")
        await auth_service.ensure_default_admin(get_db(), force_password=force_pw)
        logger.info("ensure_default_admin finished for %s", DEFAULT_ADMIN_EMAIL)
    except Exception:
        logger.exception(
            "ensure_default_admin failed — admin not seeded until DB is reachable. "
            "Redeploy after fixing Mongo, or run: railway run python scripts/seed_admin.py"
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


@app.get("/api/health/db")
async def health_db():
    """Ping Mongo + show whether super-admin row exists (debug Railway vs local DB mismatch)."""
    from database.connection import get_db

    try:
        db = get_db()
        await db.command("ping")
        admin_doc = await db.users.find_one({"email": DEFAULT_ADMIN_EMAIL})
        return {
            "mongo": "ok",
            "database": DATABASE_NAME,
            "super_admin_email": DEFAULT_ADMIN_EMAIL,
            "super_admin_present": bool(admin_doc),
            "super_admin_role": admin_doc.get("role") if admin_doc else None,
        }
    except Exception as e:
        return {"mongo": "error", "database": DATABASE_NAME, "detail": str(e)}


@app.get("/health")
async def health_root():
    """Railway / probes often use /health"""
    return {"status": "ok"}


# Same-origin UI + API (Railway: one URL). Requires Frontend copied to ./static/ (see root Dockerfile).
_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
