import json
import logging
import asyncpg
import redis.asyncio as redis
from typing import List, Optional
from app.config import get_settings
from app.schemas import TaxonomyRecord

logger = logging.getLogger(__name__)
settings = get_settings()

redis_client: Optional[redis.Redis] = None
TAXONOMY_CACHE_KEY = "talentintel:taxonomy"

# async def init_redis():
#     global redis_client
#     redis_client = redis.from_url(settings.redis_url, decode_responses=True)

# async def close_redis():
#     global redis_client
#     if redis_client:
#         await redis_client.aclose()

# async def fetch_taxonomy_from_db() -> List[TaxonomyRecord]:
#     """Fetches the entire skill taxonomy from postgres."""
#     logger.info("Connecting to Postgres to fetch taxonomy...")
#     conn = await asyncpg.connect(settings.database_url)
#     try:
#         query = "SELECT canonical_name, aliases, category FROM skill_taxonomy;"
#         rows = await conn.fetch(query)
        
#         taxonomy = []
#         for row in rows:
#             taxonomy.append(TaxonomyRecord(
#                 canonical_name=row["canonical_name"],
#                 aliases=row["aliases"] if row["aliases"] else [],
#                 category=row["category"]
#             ))
#         return taxonomy
#     finally:
#         await conn.close()

# async def get_taxonomy() -> List[TaxonomyRecord]:
#     """
#     Returns the taxonomy. First checks Redis cache; if missing, falls back to Postgres
#     and updates the cache.
#     """
#     global redis_client
#     if not redis_client:
#         await init_redis()

#     cached_data = await redis_client.get(TAXONOMY_CACHE_KEY)
#     if cached_data:
#         logger.debug("Taxonomy loaded from Redis cache.")
#         try:
#             records = json.loads(cached_data)
#             return [TaxonomyRecord.model_validate(record) for record in records]
#         except Exception as e:
#             logger.error(f"Failed to parse cached taxonomy: {e}")
#             # Fallthrough to DB fetch

#     # DB Fetch
#     taxonomy = await fetch_taxonomy_from_db()
    
#     # Store in cache
#     taxonomy_dicts = [record.model_dump() for record in taxonomy]
#     await redis_client.setex(
#         TAXONOMY_CACHE_KEY, 
#         settings.cache_ttl_seconds, 
#         json.dumps(taxonomy_dicts)
#     )
#     logger.info(f"Loaded {len(taxonomy)} taxonomy records from Postgres into Redis cache.")
    
#     return taxonomy

# 🔥 TEMP: disable Redis completely

async def init_redis():
    return None

async def close_redis():
    return None


async def get_taxonomy():
    # return dummy taxonomy OR empty
    return []