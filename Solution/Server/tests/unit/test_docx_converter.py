import sys
import os
import pytest
from unittest.mock import MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


@pytest.fixture
def mock_docx2txt_module():
    """Fixture to mock the docx2txt module."""
    mock = MagicMock()
    sys.modules['docx2txt'] = mock
    yield mock
    # Safely remove the mock
    if 'docx2txt' in sys.modules:
        del sys.modules['docx2txt']


def test_extract_docx_with_bytes(mock_docx2txt_module):
    """
    GIVEN byte content of a docx file
    WHEN extract_docx_text is called
    THEN it should use docx2txt to extract text
    """
    from workers.conversion.converters.docx import extract_docx_text
    mock_docx2txt_module.process.return_value = "Hello from docx"

    docx_bytes = b'some docx bytes'
    result = extract_docx_text(docx_bytes)

    assert result == "Hello from docx"
    mock_docx2txt_module.process.assert_called_once()


def test_extract_docx_with_path(mock_docx2txt_module):
    """
    GIVEN a file path to a docx file
    WHEN extract_docx_text is called
    THEN it should use docx2txt to extract text
    """
    from workers.conversion.converters.docx import extract_docx_text
    mock_docx2txt_module.process.return_value = "Hello from docx path"

    result = extract_docx_text("dummy/path/to/file.docx")

    assert result == "Hello from docx path"
    mock_docx2txt_module.process.assert_called_once_with("dummy/path/to/file.docx")


def test_extract_docx_exception(mock_docx2txt_module):
    """
    GIVEN a docx file that causes an exception
    WHEN extract_docx_text is called
    THEN it should return None
    """
    from workers.conversion.converters.docx import extract_docx_text
    mock_docx2txt_module.process.side_effect = Exception("DOCX processing error")

    result = extract_docx_text(b'some docx bytes')

    assert result is None
