import hashlib
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.dependencies import validate_api_key
from app.db import SessionLocal


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing API Key"}
            )

        db = SessionLocal()

        try:
            key = validate_api_key(api_key, db)

            if not key:
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid API Key"}
                )

            request.state.api_key = key

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error", "detail": str(e)}
            )

        finally:
            db.close()

        return await call_next(request)