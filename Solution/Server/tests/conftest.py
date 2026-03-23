import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api import create_app
from api.config import TestingConfig
from api.extensions import db as _db

@pytest.fixture(scope='function')
def app():
    """
    Creates a new Flask application for a test session.
    """
    app = create_app(TestingConfig)

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """
    Creates a test client for the Flask application.
    """
    return app.test_client()

@pytest.fixture
def db(app):
    """
    Returns a database instance for the test session.
    """
    with app.app_context():
        yield _db
