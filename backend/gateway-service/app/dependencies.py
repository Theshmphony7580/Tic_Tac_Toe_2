from sqlalchemy import text  # ADD THIS

def validate_api_key(api_key: str, db):
    import hashlib

    hashed = hashlib.sha256(api_key.encode()).hexdigest()

    result = db.execute(
        text("SELECT * FROM api_keys WHERE key_hash = :key AND is_active = true"),
        {"key": hashed}
    ).fetchone()

    return result