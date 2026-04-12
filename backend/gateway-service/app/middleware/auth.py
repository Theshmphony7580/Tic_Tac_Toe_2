import hashlib
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# 🔥 Temporary hardcoded key (DEV mode)
VALID_API_KEYS = {
    hashlib.sha256("sk_test_123".encode()).hexdigest()
}


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        # Skip CORS preflight requests (OPTIONS) — they never carry custom headers
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip public routes
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={"error": "Missing API Key"}
            )

        hashed = hashlib.sha256(api_key.encode()).hexdigest()

        if hashed not in VALID_API_KEYS:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API Key"}
            )

        return await call_next(request)