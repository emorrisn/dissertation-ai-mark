import logging
import tempfile
from pathlib import Path
from typing import Union

# Set up standard logging
logger = logging.getLogger(__name__)

def extract_docx_text(file_source: Union[Path, str, bytes]) -> str | None:
    try:
        import docx2txt  # type: ignore
    except ImportError:
        logger.error("[docx] Missing dependency docx2txt; skip conversion.")
        return None
        
    try:
        # 1. Handle raw bytes (e.g., straight from the database)
        if isinstance(file_source, bytes):
            # Create a temporary file on the hard drive that auto-deletes when done
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=True) as temp_file:
                temp_file.write(file_source)
                temp_file.flush() # Ensure it's fully written to disk
                return docx2txt.process(temp_file.name) or ""
                
        # 2. Handle standard file paths
        else:
            return docx2txt.process(str(file_source)) or ""
            
    except Exception as e:
        logger.error(f"[docx] ERROR converting file: {e}")
        return None