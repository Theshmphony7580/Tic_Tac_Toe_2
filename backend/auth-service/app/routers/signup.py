from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, EmailStr

from app.database import get_pool
from app.lib.auth import hash_password, generate_verification_token
from app.lib.email import send_verification_email

router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


@router.post("/signup")
async def signup(body: SignupRequest, response: Response):
    try:
        if len(body.password) < 8:
            response.status_code = 400
            return {"error": "Password must be at least 8 characters"}

        pool = get_pool()

        # Check if email already in use
        existing = await pool.fetchrow(
            "SELECT id FROM users WHERE email = $1", body.email
        )
        if existing:
            response.status_code = 409
            return {"error": "Email already in use"}

        # Create user
        password_hash = hash_password(body.password)
        user = await pool.fetchrow(
            """
            INSERT INTO users (email, name, password_hash, provider, is_verified)
            VALUES ($1, $2, $3, 'email', FALSE)
            RETURNING id, email
            """,
            body.email,
            body.name,
            password_hash,
        )

        # Send verification email
        token = generate_verification_token(str(user["id"]), body.email)
        await send_verification_email(body.email, token)

        response.status_code = 201
        return {"status": "pending_verification", "email": body.email}

    except Exception as e:
        print(f"[signup] {e}")
        response.status_code = 500
        return {"error": "Internal server error"}
