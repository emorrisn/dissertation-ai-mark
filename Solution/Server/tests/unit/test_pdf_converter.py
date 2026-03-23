import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from workers.conversion.converters.pdf import extract_pdf_text

@patch('pdfminer.high_level.extract_text')
def test_extract_text_from_pdf(mock_extract_text):
    """
    GIVEN a text-based PDF (as bytes)
    WHEN extract_pdf_text is called
    THEN it should call pdfminer's extract_text and return the text
    """
    mock_extract_text.return_value = "This is a test PDF."
    
    pdf_bytes = b'%PDF-1.4...irrelevant content...'
    
    result = extract_pdf_text(pdf_bytes)
    
    assert result == "This is a test PDF."
    mock_extract_text.assert_called_once()

@patch('workers.conversion.converters.pdf.pdf2image.convert_from_bytes')
@patch('pdfminer.high_level.extract_text')
def test_ocr_fallback_for_scanned_pdf(mock_extract_text, mock_convert_from_bytes):
    """
    GIVEN a scanned PDF (short text extracted)
    WHEN extract_pdf_text is called
    THEN it should use the OCR fallback
    """
    mock_extract_text.return_value = "short" # Less than 50 chars
    
    # Mock the image converter
    mock_image_converter = MagicMock()
    mock_image_converter.convert.return_value = "OCR text from page"
    
    # Mock pdf2image
    mock_page = MagicMock()
    mock_convert_from_bytes.return_value = [mock_page]
    
    pdf_bytes = b'%PDF-1.4...scanned content...'
    
    result = extract_pdf_text(pdf_bytes, image_converter=mock_image_converter)
    
    assert "OCR text from page" in result
    mock_convert_from_bytes.assert_called_once_with(pdf_bytes)
    mock_image_converter.convert.assert_called_once()

@patch('pdfminer.high_level.extract_text')
def test_pdf_extraction_exception(mock_extract_text):
    """
    GIVEN a pdf that causes an exception
    WHEN extract_pdf_text is called
    THEN it should return None
    """
    mock_extract_text.side_effect = Exception("PDF processing error")
    
    pdf_bytes = b'invalid pdf bytes'
    
    result = extract_pdf_text(pdf_bytes)
    
    assert result is None
