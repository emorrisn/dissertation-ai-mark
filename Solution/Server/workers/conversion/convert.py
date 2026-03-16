import os
import logging
from pathlib import Path

# Import Specific converters
from converters.image import ImageConverter
from converters.pdf import extract_pdf_text
from converters.docx import extract_docx_text
from converters.txt import extract_txt_text

logger = logging.getLogger(__name__)

class Converter:
    def __init__(self, server_dir: str):
        """Initialize the router and pass it the root Server directory."""
        self.server_dir = server_dir
        self.image_converter = ImageConverter()

        # Define supported extensions
        self.IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".heic", ".webp", ".bmp", ".gif"}
        self.TEXT_EXTS = {".txt", ".csv", ".py", ".md", ".json", ".html"}

    def load_models(self):
        """Pass-through to load the heavy OCR/LLM model into RAM."""
        self.image_converter.load()

    def unload_models(self):
        """Pass-through to purge the heavy OCR/LLM model from RAM."""
        self.image_converter.unload()

    def convert(self, storage_url: str) -> str:
        """
        The main facade function. 
        Reads the local file, determines its type, and routes it to the correct parser.
        """
        # Safely construct the absolute path to the file on disk
        # e.g., /path/to/Server + uploads/submissions/...
        full_path = os.path.join(self.server_dir, storage_url)
        
        if not os.path.exists(full_path):
            logger.error(f"File not found on disk: {full_path}")
            return ""

        # Extract the extension (e.g., '.jpg')
        ext = Path(full_path).suffix.lower()

        # Read the file into raw bytes
        try:
            with open(full_path, "rb") as f:
                file_bytes = f.read()
        except Exception as e:
            logger.error(f"Failed to read file at {full_path}: {e}")
            return ""

        # Route to the correct converter
        logger.info(f"Routing file with extension '{ext}'...")

        if ext == ".pdf":
            return extract_pdf_text(file_bytes, image_converter=self.image_converter) or ""
            
        elif ext == ".docx":
            return extract_docx_text(file_bytes) or ""
            
        elif ext in self.TEXT_EXTS:
            return extract_txt_text(file_bytes) or ""
            
        elif ext in self.IMAGE_EXTS:
            return self.image_converter.convert(file_bytes) or ""
            
        else:
            logger.warning(f"Unsupported file extension '{ext}'. Returning empty string.")
            return ""