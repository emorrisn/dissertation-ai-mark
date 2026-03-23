import json
from api.models import User, UserUpdate

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

def test_update_profile_success(client, app, db):
    """
    GIVEN a logged-in user
    WHEN a PUT request is made to /user/profile with valid data
    THEN the user profile is updated
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']
    user_id = tokens['user']['id']

    new_data = {
        "name": "New Name",
        "email": "new.email@test.com",
        "username": "newusername",
        "writingStyle": ["Strict", "Encouraging"]
    }

    response = client.put('/user/profile',
                          headers={'Authorization': f'Bearer {access_token}'},
                          data=json.dumps(new_data),
                          content_type='application/json')

    assert response.status_code == 200
    updated_user_data = response.get_json()
    assert updated_user_data['name'] == new_data['name']

    with app.app_context():
        user_from_db = User.query.get(user_id)
        assert user_from_db.name == new_data['name']
        assert user_from_db.email == new_data['email']

def test_update_profile_invalid_data(client, app, db):
    """
    GIVEN a logged-in user
    WHEN a PUT request is made to /user/profile with invalid data
    THEN the request fails with a 400 error
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']

    response = client.put('/user/profile', headers={'Authorization': f'Bearer {access_token}'}, data=json.dumps({"email": "invalid-email"}), content_type='application/json')
    assert response.status_code == 400

    response = client.put('/user/profile', headers={'Authorization': f'Bearer {access_token}'}, data=json.dumps({"name": "a"}), content_type='application/json')
    assert response.status_code == 400

def test_delete_account(client, app, db):
    """
    GIVEN a logged-in user
    WHEN a DELETE request is made to /user/profile
    THEN the user account is deleted
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']
    user_id = tokens['user']['id']

    response = client.delete('/user/profile', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200

    with app.app_context():
        deleted_user = User.query.get(user_id)
        assert deleted_user is None

def test_change_password_success(client, app, db):
    """
    GIVEN a logged-in user
    WHEN a PUT request is made to /user/password with correct current password
    THEN the password is changed
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']

    response = client.put('/user/password', headers={'Authorization': f'Bearer {access_token}'}, data=json.dumps({
        "currentPassword": "password",
        "newPassword": "new-password"
    }), content_type='application/json')
    assert response.status_code == 200

    login_response = client.post('/auth/login', data=json.dumps({"username": "testuser", "password": "new-password", "institute_code": "test"}), content_type='application/json')
    assert login_response.status_code == 200

def test_change_password_incorrect_current(client, app, db):
    """
    GIVEN a logged-in user
    WHEN a PUT request is made to /user/password with incorrect current password
    THEN the request fails
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']

    response = client.put('/user/password', headers={'Authorization': f'Bearer {access_token}'}, data=json.dumps({
        "currentPassword": "wrong-password",
        "newPassword": "new-password"
    }), content_type='application/json')
    assert response.status_code == 400

def test_get_updates(client, app, db):
    """
    GIVEN a user with updates
    WHEN a GET request is made to /user/updates
    THEN the updates are returned
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']
    user_id = tokens['user']['id']
    with app.app_context():
        update = UserUpdate(user_id=user_id, title="Test Update", type="TestUpdate")
        db.session.add(update)
        db.session.commit()

    response = client.get('/user/updates', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200
    updates = response.get_json()
    assert len(updates) == 1
    assert updates[0]['title'] == "Test Update"

def test_mark_update_as_read(client, app, db):
    """
    GIVEN a user with an unread update
    WHEN a POST request is made to /user/updates/<update_id>/read
    THEN the update is marked as read
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']
    user_id = tokens['user']['id']

    with app.app_context():
        update = UserUpdate(user_id=user_id, title="Test Update", is_read=False, type="TestUpdate")
        db.session.add(update)
        db.session.commit()
        update_id = update.id

    response = client.post(f'/user/updates/{update_id}/read', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200

    with app.app_context():
        read_update = UserUpdate.query.get(update_id)
        assert read_update.is_read is True
