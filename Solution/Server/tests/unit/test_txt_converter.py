import sys
import os
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from workers.conversion.converters.txt import extract_txt_text

def test_extract_txt_from_utf8_bytes():
    """
    GIVEN a byte string encoded in UTF-8
    WHEN extract_txt_text is called
    THEN it should decode it correctly
    """
    utf8_string = "This is a UTF-8 string with special characters like é, à, ç"
    utf8_bytes = utf8_string.encode('utf-8')
    
    result = extract_txt_text(utf8_bytes)
    assert result == utf8_string

def test_extract_txt_from_cp1252_bytes():
    """
    GIVEN a byte string encoded in cp1252 that would fail UTF-8
    WHEN extract_txt_text is called
    THEN it should fall back to cp1252 and decode it
    """
    # The smart quote character ’ is 0x92 in cp1252, which is invalid in UTF-8
    cp1252_string = "It’s a cp1252 string"
    cp1252_bytes = cp1252_string.encode('cp1252')

    result = extract_txt_text(cp1252_bytes)
    assert result == cp1252_string

def test_extract_txt_from_non_existent_file():
    """
    GIVEN a path to a non-existent file
    WHEN extract_txt_text is called
    THEN it should return None
    """
    # In a unit test, we shouldn't be hitting the filesystem, but this function
    # has a specific check for it, so we test that branch.
    result = extract_txt_text("path/to/non/existent/file.txt")
    assert result is None
