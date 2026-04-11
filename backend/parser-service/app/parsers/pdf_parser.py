import pymupdf4llm
import fitz
import logging

logger = logging.getLogger(__name__)

def parse_pdf(file_bytes: bytes) -> str:
    """
    Parses a PDF file from bytes using PyMuPDF and pymupdf4llm to extract
    clean, layout-aware Markdown text (which is optimal for LLMs).
    """
    doc = None
    try:
        # Open PDF from memory
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        # Extract markdown, preserving tables, headers, and multi-column layouts
        markdown_text = pymupdf4llm.to_markdown(doc)
        return markdown_text.strip()
    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        raise ValueError(f"PDF parsing failed: {e}")
    finally:
        if doc:
            doc.close()
