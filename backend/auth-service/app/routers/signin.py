from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, EmailStr

from app.database import get_pool
from app.lib.auth import verify_password
from app.routers._helpers import create_session

router = APIRouter()


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signin")
async def signin(body: SigninRequest, request: Request, response: Response):
    try:
        pool = get_pool()

        user = await pool.fetchrow(
            "SELECT id, email, name, avatar_url, password_hash, is_verified FROM users WHERE email = $1",
            body.email,
        )

        if not user or not user["password_hash"]:
            response.status_code = 401
            return {"error": "Invalid email or password"}

        if not user["is_verified"]:
            response.status_code = 403
            return {"status": "pending_verification", "email": body.email}

        if not verify_password(body.password, user["password_hash"]):
            response.status_code = 401
            return {"error": "Invalid email or password"}

        access_token = await create_session(str(user["id"]), response, request)

        return {
            "accessToken": access_token,
            "user": {
                "id": str(user["id"]),
                "email": user["email"],
                "name": user["name"],
                "avatar_url": user["avatar_url"],
            },
        }

    except Exception as e:
        print(f"[signin] {e}")
        response.status_code = 500
        return {"error": "Internal server error"}
