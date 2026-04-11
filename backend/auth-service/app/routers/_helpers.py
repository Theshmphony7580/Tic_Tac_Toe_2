"""Shared helpers for auth routers — mirrors helpers.ts."""

import time
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response

from app.config import NODE_ENV
from app.database import get_pool
from app.lib.auth import generate_access_token, generate_refresh_token, hash_token


async def create_session(user_id: str, response: Response, request: Request) -> str:
    """Create access + refresh tokens, store refresh in DB, set HttpOnly cookies.

    Returns the raw access token string.
    """
    access_token = generate_access_token(user_id)
    raw_refresh = generate_refresh_token()
    token_hash = hash_token(raw_refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    # Device info
    device_name = (request.headers.get("user-agent") or "")[:255] or None
    forwarded = request.headers.get("x-forwarded-for")
    ip_address = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else None)

    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO refresh_tokens (user_id, token_hash, device_name, ip_address, expires_at)
        VALUES ($1, $2, $3, $4, $5)
        """,
        user_id,
        token_hash,
        device_name,
        ip_address,
        expires_at,
    )

    is_prod = NODE_ENV == "production"

    # Access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=15 * 60,  # 15 minutes
    )

    # Refresh token cookie (scoped path)
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        path="/auth/refresh",
        max_age=30 * 24 * 60 * 60,  # 30 days
    )

    # Client-visible session indicator (non-httpOnly so Next.js middleware can read it)
    response.set_cookie(
        key="has_session",
        value="1",
        httponly=False,
        secure=is_prod,
        samesite="lax",
        path="/",
        max_age=30 * 24 * 60 * 60,  # 30 days
    )

    return access_token


# ─── In-memory rate limiter for resend-verification ─────────────────

_resend_tracker: dict[str, dict] = {}
RESEND_MAX = 3
RESEND_WINDOW_SECONDS = 30 * 60  # 30 minutes


def can_resend(email: str) -> bool:
    now = time.time()
    entry = _resend_tracker.get(email)

    if not entry or now - entry["window_start"] > RESEND_WINDOW_SECONDS:
        _resend_tracker[email] = {"count": 1, "window_start": now}
        return True

    if entry["count"] >= RESEND_MAX:
        return False

    entry["count"] += 1
    return True
