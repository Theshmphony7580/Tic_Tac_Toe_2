from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

from app.config import FRONTEND_URL
from app.database import get_pool
from app.lib.auth import verify_verification_token, generate_verification_token
from app.lib.email import send_verification_email
from app.routers._helpers import create_session, can_resend

router = APIRouter()


# ─── GET /verify-email — User clicks magic link ─────────────────────

@router.get("/verify-email")
async def verify_email(request: Request, response: Response, token: str | None = None):
    try:
        if not token:
            return RedirectResponse(f"{FRONTEND_URL}/error?msg=Missing+verification+token")

        try:
            payload = verify_verification_token(token)
        except Exception:
            return RedirectResponse(f"{FRONTEND_URL}/error?msg=Invalid+or+expired+verification+link")

        pool = get_pool()
        user = await pool.fetchrow("SELECT id, is_verified FROM users WHERE id = $1", payload["sub"])

        if not user:
            return RedirectResponse(f"{FRONTEND_URL}/error?msg=User+not+found")

        if user["is_verified"]:
            access_token = await create_session(str(user["id"]), response, request)
            return RedirectResponse(f"{FRONTEND_URL}/dashboard?token={access_token}")

        # Mark as verified
        await pool.execute("UPDATE users SET is_verified = TRUE WHERE id = $1", payload["sub"])

        access_token = await create_session(str(user["id"]), response, request)
        redirect = RedirectResponse(f"{FRONTEND_URL}/analyser?token={access_token}")
        for header_value in response.headers.getlist("set-cookie"):
            redirect.headers.append("set-cookie", header_value)
        return redirect

    except Exception as e:
        print(f"[verify-email] {e}")
        return RedirectResponse(f"{FRONTEND_URL}/error?msg=Verification+failed")


# ─── POST /resend-verification (rate limited: 3 per 30 min) ─────────

class ResendRequest(BaseModel):
    email: EmailStr


@router.post("/resend-verification")
async def resend_verification(body: ResendRequest, response: Response):
    try:
        if not can_resend(body.email):
            response.status_code = 429
            return {"error": "Too many requests. Try again in 30 minutes."}

        pool = get_pool()
        user = await pool.fetchrow(
            "SELECT id, is_verified FROM users WHERE email = $1", body.email
        )

        # Silent success if user not found or already verified (security)
        if not user or user["is_verified"]:
            return {"status": "ok"}

        token = generate_verification_token(str(user["id"]), body.email)
        await send_verification_email(body.email, token)
        return {"status": "ok"}

    except Exception as e:
        print(f"[resend-verification] {e}")
        response.status_code = 500
        return {"error": "Internal server error"}


# ─── GET /verification-status — Poll by email ───────────────────────

@router.get("/verification-status")
async def verification_status(response: Response, email: str | None = None):
    try:
        if not email:
            response.status_code = 400
            return {"error": "Email is required"}

        pool = get_pool()
        user = await pool.fetchrow(
            "SELECT is_verified FROM users WHERE email = $1", email
        )

        return {"verified": user["is_verified"] if user else False}

    except Exception as e:
        print(f"[verification-status] {e}")
        response.status_code = 500
        return {"error": "Internal server error"}
