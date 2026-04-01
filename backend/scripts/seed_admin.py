"""
One-off: ensure super admin exists on the configured MongoDB (e.g. Railway).

Usage (Railway CLI, from repo root or backend):
  cd backend
  railway run python scripts/seed_admin.py
  railway run python scripts/seed_admin.py --force   # reset password to default (sadiq123)

Or locally with .env pointing at Railway Mongo:
  python scripts/seed_admin.py
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from dotenv import load_dotenv

load_dotenv(os.path.join(_ROOT, ".env"))


async def main(force_password: bool) -> None:
    from database.connection import get_db, init_db
    from services import auth_service

    await init_db()
    await auth_service.ensure_default_admin(get_db(), force_password=force_password)
    msg = "OK: default admin ensured"
    if force_password:
        msg += " (password reset to default)"
    print(msg + " (see auth_service.DEFAULT_ADMIN_EMAIL).")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Seed super admin on MongoDB")
    p.add_argument(
        "--force",
        action="store_true",
        help="If admin exists, reset password hash to default (sadiq123)",
    )
    args = p.parse_args()
    asyncio.run(main(force_password=args.force))
