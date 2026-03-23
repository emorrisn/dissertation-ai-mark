import sys
import os
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from api.models import User

def test_user_set_password():
    """
    GIVEN a User model
    WHEN a password is set
    THEN the password hash should be stored and not the plain text password
    """
    u = User(username='testuser')
    u.set_password('password123')
    assert u.password_hash is not None
    assert u.password_hash != 'password123'

def test_user_check_password():
    """
    GIVEN a User model with a password set
    WHEN the password is checked
    THEN it should return True for the correct password and False for an incorrect one
    """
    u = User(username='testuser')
    u.set_password('password123')
    assert u.check_password('password123') is True
    assert u.check_password('wrongpassword') is False
