"""
File processing utilities for Cloud-Based AI Chatbot.

Handles:
- Validating uploaded files (extension, size, empty file checks, path safety)
- Extracting plain text from PDF / TXT / DOCX files
- Detecting whether a file is an image (handled directly by multimodal vision)

Defensive design: Every extraction function fails with clear, user-friendly messages.
"""

import os
import logging
from pypdf import PdfReader
import docx

logger = logging.getLogger("chatbot.file_processor")

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".txt", ".docx"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_EXTENSIONS = ALLOWED_DOCUMENT_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
MAX_EXTRACTED_CHARS = 8000  # Optimized context length to avoid in-flight credit budget exhaustion


class FileValidationError(Exception):
    """Raised when an uploaded file fails validation."""
    pass


def _get_extension(filename: str) -> str:
    """Returns the lowercased file extension including the leading dot."""
    return os.path.splitext(filename)[1].lower()


def is_image_file(filename: str) -> bool:
    """Returns True if the file is a supported image type."""
    return _get_extension(filename) in ALLOWED_IMAGE_EXTENSIONS


def validate_file(file_storage) -> None:
    """
    Validates a Flask FileStorage object before saving to disk.
    Raises FileValidationError with user-friendly explanations.
    """
    filename = file_storage.filename
    if not filename:
        raise FileValidationError("No file was selected for upload.")

    ext = _get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        allowed_list = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise FileValidationError(
            f"Unsupported file type '{ext}'. Supported formats: {allowed_list}"
        )

    # Determine size without reading full file into memory
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)

    if size == 0:
        raise FileValidationError("The uploaded file is empty (0 bytes). Please upload a valid document or image.")

    if size > MAX_FILE_SIZE_BYTES:
        mb_size = size / (1024 * 1024)
        max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        raise FileValidationError(
            f"File is too large ({mb_size:.1f} MB). Maximum allowed upload size is {max_mb:.0f} MB."
        )

    # Filename path traversal check
    sanitized = os.path.basename(filename)
    if ".." in filename or filename.startswith("/") or filename.startswith("\\") or not sanitized:
        raise FileValidationError("Invalid or insecure filename detected.")


def extract_text_from_file(filepath: str) -> str:
    """
    Extracts text from PDF, TXT, or DOCX file at filepath.
    Returns truncated text up to MAX_EXTRACTED_CHARS.
    """
    ext = _get_extension(filepath)

    if ext == ".txt":
        text = _extract_txt(filepath)
    elif ext == ".pdf":
        text = _extract_pdf(filepath)
    elif ext == ".docx":
        text = _extract_docx(filepath)
    else:
        raise ValueError(f"No text extractor available for '{ext}' files.")

    text = text.strip()
    if not text:
        raise ValueError("No readable text could be found in the uploaded file.")

    if len(text) > MAX_EXTRACTED_CHARS:
        text = text[:MAX_EXTRACTED_CHARS] + "\n\n[...content truncated for optimal AI processing...]"

    return text


def _extract_txt(filepath: str) -> str:
    """Reads a text file trying common encodings (UTF-8, Latin-1, CP1252)."""
    encodings = ["utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    # Fallback with replacement
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _extract_pdf(filepath: str) -> str:
    """Extracts text from all pages of a PDF document."""
    try:
        reader = PdfReader(filepath)
        pages_text = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages_text.append(f"--- Page {i + 1} ---\n{page_text}")
        return "\n\n".join(pages_text)
    except Exception as e:
        logger.error("PDF extraction error: %s", e)
        raise ValueError(f"Failed to extract text from PDF: {str(e)}") from e


def _extract_docx(filepath: str) -> str:
    """Extracts text from paragraphs and tables of a DOCX document."""
    try:
        document = docx.Document(filepath)
        content_parts = []
        
        # Paragraphs
        for p in document.paragraphs:
            if p.text.strip():
                content_parts.append(p.text.strip())

        # Tables (if any)
        for table in document.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    content_parts.append(row_text)

        return "\n\n".join(content_parts)
    except Exception as e:
        logger.error("DOCX extraction error: %s", e)
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}") from e
