import logging
from sentence_transformers import SentenceTransformer
from app.config import get_settings

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def load_model() -> None:
    """Load the sentence-transformers model into memory. Called once at startup."""
    global _model
    settings = get_settings()
    logger.info(f"Loading embedding model: {settings.embedding_model} ...")
    _model = SentenceTransformer(settings.embedding_model)
    logger.info("Embedding model loaded successfully.")


def embed_text(text: str) -> list[float]:
    """
    Encode a text string into a 384-dimensional float vector.
    Lazily loads the model on first call if not already loaded.
    """
    global _model
    if _model is None:
        load_model()
    return _model.encode(text, show_progress_bar=False).tolist()
