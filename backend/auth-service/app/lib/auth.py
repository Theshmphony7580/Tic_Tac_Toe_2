import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import JWT_SECRET


# ─── JWT Access Token ────────────────────────────────────────────────

def generate_access_token(user_id: str) -> str:
    """JWT with 15-minute expiry."""
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_access_token(token: str) -> dict:
    """Returns decoded payload or raises jwt exceptions."""
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


# ─── JWT Verification Token ─────────────────────────────────────────

def generate_verification_token(user_id: str, email: str) -> str:
    """JWT with 24-hour expiry for email verification."""
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_verification_token(token: str) -> dict:
    """Returns {"sub": user_id, "email": email} or raises."""
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])


# ─── Refresh Token ──────────────────────────────────────────────────

def generate_refresh_token() -> str:
    """Random 64-char hex string."""
    return secrets.token_hex(32)


# ─── Hashing ────────────────────────────────────────────────────────

def hash_token(token: str) -> str:
    """SHA-256 hash of a token string."""
    return hashlib.sha256(token.encode()).hexdigest()


def hash_password(password: str) -> str:
    """bcrypt hash."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode(), password_hash.encode())
