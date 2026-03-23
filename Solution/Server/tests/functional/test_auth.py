import json
from api.models import User, UserSession

def _login_user(client, db, app, username="testuser", password="password", institute_code="test", email="test@test.com"):
    """Helper function to create a user and log them in."""
    with app.app_context():
        user = User(
            username=username,
            name="Test User",
            institute_code=institute_code,
            email=email
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

    response = client.post('/auth/login',
                             data=json.dumps({
                                 "username": username,
                                 "password": password,
                                 "institute_code": institute_code
                             }),
                             content_type='application/json')
    return response.get_json()

def test_login(client, app, db):
    """
    GIVEN a User model
    WHEN a POST request is made to /auth/login
    THEN check the response is valid
    """
    tokens = _login_user(client, db, app)
    assert 'access_token' in tokens
    assert 'refresh_token' in tokens

def test_register_success(client, app):
    """
    GIVEN a new user
    WHEN a POST request is made to /auth/register
    THEN check the response is valid and the user is created
    """
    response = client.post('/auth/register',
                             data=json.dumps({
                                 "username": "newuser",
                                 "password": "password",
                                 "institute_code": "test",
                                 "email": "new@test.com",
                                 "name": "New User"
                             }),
                             content_type='application/json')

    assert response.status_code == 201
    response_data = response.get_json()
    assert 'access_token' in response_data
    assert 'refresh_token' in response_data
    assert response_data['user']['username'] == 'newuser'

    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'new@test.com'

def test_register_existing_user(client, app, db):
    """
    GIVEN an existing user
    WHEN a POST request is made to /auth/register with the same details
    THEN check the response is a 400 error
    """
    _login_user(client, db, app, username="existinguser", email="existing@test.com")

    response = client.post('/auth/register',
                             data=json.dumps({
                                 "username": "existinguser",
                                 "password": "password",
                                 "institute_code": "test"
                             }),
                             content_type='application/json')

    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['message'] == "User already exists"

def test_register_missing_fields(client, app):
    """
    GIVEN a POST request to /auth/register with missing fields
    THEN check the response is a 400 error
    """
    response = client.post('/auth/register',
                             data=json.dumps({
                                 "username": "anotheruser",
                                 "institute_code": "test"
                             }),
                             content_type='application/json')

    assert response.status_code == 400
    response_data = response.get_json()
    assert response_data['message'] == "Missing required fields: username, password, or institute_code"

def test_logout(client, app, db):
    """
    GIVEN a logged-in user
    WHEN a POST request is made to /auth/logout
    THEN check the session is revoked
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']

    response = client.post('/auth/logout', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200
    assert response.get_json()['message'] == "Logged out"

    with app.app_context():
        # Verify session is revoked
        user = User.query.filter_by(username='testuser').first()
        session = UserSession.query.filter_by(user_id=user.id).first()
        assert session.revoked is True

def test_refresh(client, app, db):
    """
    GIVEN a logged-in user with a refresh token
    WHEN a POST request is made to /auth/refresh
    THEN a new access token is returned
    """
    tokens = _login_user(client, db, app)
    refresh_token = tokens['refresh_token']

    response = client.post('/auth/refresh', headers={'Authorization': f'Bearer {refresh_token}'})
    assert response.status_code == 200
    new_tokens = response.get_json()
    assert 'access_token' in new_tokens
    assert new_tokens['access_token'] != tokens['access_token']

def test_session(client, app, db):
    """
    GIVEN a logged-in user
    WHEN a GET request is made to /auth/session
    THEN the correct user data is returned
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']

    response = client.get('/auth/session', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200
    user_data = response.get_json()
    assert user_data['username'] == 'testuser'
    assert user_data['email'] == 'test@test.com'

