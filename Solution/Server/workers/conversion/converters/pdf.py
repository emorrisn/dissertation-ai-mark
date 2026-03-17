import io
import logging
import tempfile
from pathlib import Path
from typing import Union
import pdf2image
import os

logger = logging.getLogger(__name__)

def extract_pdf_text(file_source: Union[Path, str, bytes], image_converter=None) -> str | None:
    try:
        from pdfminer.high_level import extract_text  # type: ignore
    except ImportError as e:
        logger.error(f"[pdf] Import failed with exact error: {e}")
        return None
        
    try:
        extracted_text = ""
        
        # Handle bytes via a temporary file
        if isinstance(file_source, bytes):
            file_bytes = file_source # Save for potential pdf2image fallback
            
            # Set delete=False and close the file before reading
            temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            temp_file.write(file_source)
            temp_file.close() # <-- This releases the Windows file lock
            
            try:
                extracted_text = extract_text(temp_file.name) or ""
            finally:
                os.remove(temp_file.name)
        # Handle file paths
        else:
            with open(file_source, "rb") as f:
                file_bytes = f.read() # Save for potential pdf2image fallback
            extracted_text = extract_text(str(file_source)) or ""

        # THE SCANNED PDF FALLBACK
        # If the text is suspiciously short, it's likely a scanned image.
        if len(extracted_text.strip()) < 50 and image_converter is not None and file_bytes:
            logger.info("[pdf] Minimal text detected. Treating as a scanned document. Falling back to OCR...")
            
            extracted_text = ""
            
            # Convert PDF bytes to a list of PIL Images
            # Note: poppler must be installed on your host machine for pdf2image to work
            pages = pdf2image.convert_from_bytes(file_bytes)
            
            for i, page in enumerate(pages):
                logger.info(f"[pdf] Running OCR on scanned PDF page {i+1}/{len(pages)}...")
                
                # Convert PIL Image to bytes so your ImageConverter can read it
                img_byte_arr = io.BytesIO()
                page.save(img_byte_arr, format='PNG')
                page_bytes = img_byte_arr.getvalue()
                
                # Run through the heavy LLM/OCR model
                page_text = image_converter.convert(page_bytes)
                if page_text:
                    extracted_text += page_text + "\n\n"

        return extracted_text.strip()

    except Exception as e:
        logger.error(f"[pdf] ERROR converting file: {e}")
        return None