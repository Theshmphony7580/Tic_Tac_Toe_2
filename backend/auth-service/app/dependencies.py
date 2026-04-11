from fastapi import Cookie, Header, HTTPException

from app.lib.auth import verify_access_token


async def require_auth(
    access_token: str | None = Cookie(None),
    authorization: str | None = Header(None),
) -> str:
    """FastAPI dependency — extracts user_id from JWT.

    Accepts auth via:
      1. Authorization: Bearer <token> header (preferred)
      2. access_token cookie (fallback)

    Returns the user_id string.
    Raises 401 if token is missing or invalid.
    """
    token: str | None = None

    # Prefer Authorization header
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = verify_access_token(token)
        user_id: str = payload["sub"]
        return user_id
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

