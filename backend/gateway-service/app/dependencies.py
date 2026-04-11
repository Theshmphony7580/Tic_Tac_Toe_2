from sqlalchemy.orm import Session
from app.db import get_db
import hashlib

def validate_api_key(api_key: str, db: Session):
    hashed = hashlib.sha256(api_key.encode()).hexdigest()

    result = db.execute(
        "SELECT * FROM api_keys WHERE key_hash = :key AND is_active = true",
        {"key": hashed}
    ).fetchone()

    return result