from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os

# You can move this later to config.py
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:password@localhost:5432/talentintel"
)

# Create engine
engine = create_engine(DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency (used in routes if needed)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()