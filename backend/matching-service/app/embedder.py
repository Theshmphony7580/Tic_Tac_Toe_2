import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_model: SentenceTransformer | None = None

def load_model():
    """Called once during FastAPI lifespan startup."""
    global _model
    logger.info(f"Loading embedding model: {settings.embedding_model}...")
    _model = SentenceTransformer(settings.embedding_model)
    logger.info("Embedding model loaded successfully.")

def get_model() -> SentenceTransformer:
    if _model is None:
        raise RuntimeError("Embedding model not loaded.")
    return _model

def embed_text(text: str) -> list[float]:
    """Encode a single text string. Returns a 384-dim float list."""
    model = get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()
