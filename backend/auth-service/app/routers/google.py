import httpx
from urllib.parse import urlencode

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, APP_URL, FRONTEND_URL
from app.database import get_pool
from app.routers._helpers import create_session

router = APIRouter()

CALLBACK_URL = f"{APP_URL}/auth/google/callback"


# ─── GET /google — Redirect to Google consent screen ────────────────

@router.get("/google")
async def google_redirect():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return {"error": "Google OAuth not configured"}

    params = urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": CALLBACK_URL,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    })
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{params}")


# ─── GET /google/callback — Exchange code, upsert user ──────────────

@router.get("/google/callback")
async def google_callback(request: Request, response: Response, code: str | None = None, error: str | None = None):
    try:
        if error or not code:
            return RedirectResponse(f"{FRONTEND_URL}/error?msg=Google+login+cancelled")

        # Exchange authorization code for tokens
        async with httpx.AsyncClient() as client:
            token_res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": CALLBACK_URL,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if token_res.status_code != 200:
            print(f"[google] Token exchange failed: {token_res.text}")
            return RedirectResponse(f"{FRONTEND_URL}/error?msg=Google+login+failed")

        tokens = token_res.json()

        # Fetch user profile from Google
        async with httpx.AsyncClient() as client:
            user_res = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )

        if user_res.status_code != 200:
            print(f"[google] Failed to fetch user info: {user_res.text}")
            return RedirectResponse(f"{FRONTEND_URL}/error?msg=Google+login+failed")

        profile = user_res.json()

        if not profile.get("email"):
            return RedirectResponse(f"{FRONTEND_URL}/error?msg=No+email+from+Google")

        pool = get_pool()

        # Upsert user
        user = await pool.fetchrow("SELECT * FROM users WHERE email = $1", profile["email"])

        if not user:
            user = await pool.fetchrow(
                """
                INSERT INTO users (email, name, avatar_url, provider, is_verified)
                VALUES ($1, $2, $3, 'google', TRUE)
                RETURNING *
                """,
                profile["email"],
                profile.get("name") or profile["email"].split("@")[0] or "User",
                profile.get("picture"),
            )
        else:
            user = await pool.fetchrow(
                """
                UPDATE users SET
                    name = COALESCE(name, $2),
                    avatar_url = COALESCE(avatar_url, $3),
                    is_verified = TRUE
                WHERE email = $1
                RETURNING *
                """,
                profile["email"],
                profile.get("name"),
                profile.get("picture"),
            )

        # Upsert OAuthAccount
        await pool.execute(
            """
            INSERT INTO oauth_accounts (user_id, provider, provider_account_id, access_token, refresh_token)
            VALUES ($1, 'google', $2, $3, $4)
            ON CONFLICT (provider, provider_account_id) DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token
            """,
            str(user["id"]),
            profile["sub"],
            tokens["access_token"],
            tokens.get("refresh_token"),
        )

        # Create session (cookies handle everything)
        await create_session(str(user["id"]), response, request)
        return RedirectResponse(f"{FRONTEND_URL}/dashboard")

    except Exception as e:
        print(f"[google-callback] {e}")
        return RedirectResponse(f"{FRONTEND_URL}/error?msg=Google+login+failed")
