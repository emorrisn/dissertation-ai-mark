import os
import json
from api.models import User

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

def test_serve_upload_success(client, app, db):
    """
    GIVEN a file in the uploads directory
    WHEN a GET request is made to /uploads/<filepath> by an authenticated user
    THEN the file is served successfully
    """
    # Create a dummy file in the uploads directory
    uploads_dir = os.path.join(os.path.dirname(app.root_path), 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    dummy_filepath = os.path.join(uploads_dir, 'test_file.txt')
    with open(dummy_filepath, 'w') as f:
        f.write('hello world')

    response = None
    try:
        # Login user to get token
        tokens = _login_user(client, db, app)
        access_token = tokens['access_token']

        # Make request to serve the file
        response = client.get('/uploads/test_file.txt',
                              headers={'Authorization': f'Bearer {access_token}'})

        assert response.status_code == 200
        assert response.data == b'hello world'
    finally:
        if response:
            response.close()
        # Clean up the dummy file
        if os.path.exists(dummy_filepath):
            os.remove(dummy_filepath)
