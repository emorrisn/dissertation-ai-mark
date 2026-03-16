import logging
import tempfile
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)

def extract_pdf_text(file_source: Union[Path, str, bytes], image_converter=None) -> str | None:
    try:
        from pdfminer.high_level import extract_text  # type: ignore
    except ImportError as e:
        logger.error(f"[pdf] Import failed with exact error: {e}")
        return None
        
    try:
        extracted_text = ""
        
        # 1. Handle bytes via a temporary file
        if isinstance(file_source, bytes):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as temp_file:
                temp_file.write(file_source)
                temp_file.flush()
                extracted_text = extract_text(temp_file.name) or ""
        # 2. Handle file paths
        else:
            extracted_text = extract_text(str(file_source)) or ""

        # THE SCANNED PDF FALLBACK
        # If the text is suspiciously short, it's likely a scanned image.
        if len(extracted_text.strip()) < 50 and image_converter is not None:
            logger.info("[pdf] Minimal text detected. Treating as a scanned document. Falling back to OCR...")
            
            # TODO: Convert PDF to images using 'pdf2image' library
            # pages = pdf2image.convert_from_bytes(file_source)
            # for page in pages:
            #     extracted_text += image_converter.convert(page)
            
            pass # Placeholder until you implement pdf2image

        return extracted_text

    except Exception as e:
        logger.error(f"[pdf] ERROR converting file: {e}")
        return None