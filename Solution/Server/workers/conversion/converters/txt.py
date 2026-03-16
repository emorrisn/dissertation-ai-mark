import logging
from pathlib import Path
from typing import Union

# Set up standard logging
logger = logging.getLogger(__name__)

def extract_txt_text(file_source: Union[Path, str, bytes]) -> str | None:
    """
    Extracts text from raw text files (.txt, .csv, .py, .md, etc.).
    Handles both raw byte streams and file paths.
    """
    try:
        # 1. Handle raw bytes (e.g., straight from the database)
        if isinstance(file_source, bytes):
            try:
                # Try modern standard UTF-8 first
                return file_source.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback: Many Windows applications (like old Notepad) default to cp1252
                logger.warning("[txt] UTF-8 decode failed. Falling back to cp1252 encoding.")
                return file_source.decode('cp1252', errors='replace')
                
        # 2. Handle standard file paths
        else:
            path = Path(file_source)
            if not path.exists():
                logger.error(f"[txt] File not found: {path.name}")
                return None
                
            try:
                # Try modern standard UTF-8 first
                return path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # Fallback for Windows-encoded files
                logger.warning(f"[txt] UTF-8 read failed for {path.name}. Falling back to cp1252 encoding.")
                return path.read_text(encoding='cp1252', errors='replace')
                
    except Exception as e:
        logger.error(f"[txt] ERROR reading text file: {e}")
        return None