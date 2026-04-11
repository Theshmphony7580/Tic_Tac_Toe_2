from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, Request, Response

from app.database import get_pool
from app.dependencies import require_auth
from app.lib.auth import hash_token
from app.routers._helpers import create_session

router = APIRouter()


# ─── POST /refresh — Token rotation ─────────────────────────────────

@router.post("/refresh")
async def refresh(request: Request, response: Response, refresh_token: str | None = Cookie(None)):
    try:
        if not refresh_token:
            response.status_code = 401
            return {"error": "No refresh token"}

        pool = get_pool()
        token_hash = hash_token(refresh_token)

        stored = await pool.fetchrow(
            """
            SELECT rt.id, rt.user_id, rt.expires_at,
                   u.id AS uid, u.email, u.name, u.avatar_url
            FROM refresh_tokens rt
            JOIN users u ON u.id = rt.user_id
            WHERE rt.token_hash = $1
            """,
            token_hash,
        )

        if not stored or stored["expires_at"] < datetime.now(timezone.utc):
            # Clean up expired token
            if stored:
                await pool.execute("DELETE FROM refresh_tokens WHERE id = $1", stored["id"])
            response.delete_cookie("refresh_token", path="/auth/refresh")
            response.delete_cookie("access_token", path="/")
            response.status_code = 401
            return {"error": "Session expired, please log in again"}

        # Delete old token (rotation)
        await pool.execute("DELETE FROM refresh_tokens WHERE id = $1", stored["id"])

        # Create new session
        access_token = await create_session(str(stored["user_id"]), response, request)

        return {
            "accessToken": access_token,
            "user": {
                "id": str(stored["uid"]),
                "email": stored["email"],
                "name": stored["name"],
                "avatar_url": stored["avatar_url"],
            },
        }

    except Exception as e:
        print(f"[refresh] {e}")
        response.status_code = 401
        return {"error": "Token refresh failed"}


# ─── POST /logout (protected) ───────────────────────────────────────

@router.post("/logout")
async def logout(
    response: Response,
    user_id: str = Depends(require_auth),
    refresh_token: str | None = Cookie(None),
):
    try:
        if refresh_token:
            pool = get_pool()
            token_hash = hash_token(refresh_token)
            await pool.execute("DELETE FROM refresh_tokens WHERE token_hash = $1", token_hash)

        response.delete_cookie("refresh_token", path="/auth/refresh")
        response.delete_cookie("access_token", path="/")
        return {"status": "logged_out"}

    except Exception as e:
        print(f"[logout] {e}")
        response.status_code = 500
        return {"error": "Internal server error"}


# ─── GET /me (protected) ────────────────────────────────────────────

@router.get("/me")
async def me(response: Response, user_id: str = Depends(require_auth)):
    try:
        pool = get_pool()
        user = await pool.fetchrow(
            """
            SELECT id, email, name, avatar_url, provider, is_verified, created_at
            FROM users WHERE id = $1
            """,
            user_id,
        )

        if not user:
            response.status_code = 404
            return {"error": "User not found"}

        return {
            "user": {
                "id": str(user["id"]),
                "email": user["email"],
                "name": user["name"],
                "avatar_url": user["avatar_url"],
                "provider": user["provider"],
                "is_verified": user["is_verified"],
                "createdAt": user["created_at"].isoformat() if user["created_at"] else None,
            }
        }

    except Exception as e:
        print(f"[me] {e}")
        response.status_code = 500
        return {"error": "Internal server error"}
