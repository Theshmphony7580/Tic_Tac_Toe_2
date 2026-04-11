import logging

logger = logging.getLogger(__name__)

def parse_txt(file_bytes: bytes) -> str:
    """
    Safely decode raw TXT bytes to string using fallback encodings.
    """
    try:
        return file_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        try:
            return file_bytes.decode("latin-1").strip()
        except Exception:
            return file_bytes.decode("utf-8", errors="replace").strip()
