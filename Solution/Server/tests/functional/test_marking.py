import json
from io import BytesIO
from api.models import User, MarkingSession, StudentSubmission, MarkingFeedback

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

def test_create_session_success(client, app, db):
    """
    GIVEN a logged-in user
    WHEN a POST request is made to /marking/start with valid data
    THEN a new marking session is created
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']

    data = {
        'year': '2023',
        'studentsAmount': '50',
        'notes': 'Test session',
        'requiredOutputs[]': ['output1', 'output2'],
        'markschemes[0][contents]': 'Sample mark scheme'
    }

    response = client.post('/marking/start',
                           headers={'Authorization': f'Bearer {access_token}'},
                           data=data,
                           content_type='multipart/form-data')

    assert response.status_code == 201
    session_data = response.get_json()
    assert session_data['year'] == 2023
    assert session_data['notes'] == 'Test session'
    assert len(session_data['markschemes']) == 1
    assert session_data['markschemes'][0]['contents'] == 'Sample mark scheme'


def test_list_sessions(client, app, db):
    """
    GIVEN a user with marking sessions
    WHEN a GET request is made to /marking/sessions
    THEN the sessions are returned
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']
    user_id = tokens['user']['id']

    with app.app_context():
        session = MarkingSession(user_id=user_id, year=2023, status="ready")
        db.session.add(session)
        db.session.commit()

    response = client.get('/marking/sessions', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200
    sessions = response.get_json()
    assert len(sessions) == 1
    assert sessions[0]['year'] == 2023

def test_add_submission_success(client, app, db):
    """
    GIVEN a marking session
    WHEN a POST request is made to /marking/submission
    THEN a new submission is added
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']
    user_id = tokens['user']['id']

    with app.app_context():
        session = MarkingSession(user_id=user_id, year=2023, status="ready", students_amount=1)
        db.session.add(session)
        db.session.commit()
        session_id = session.id

    data = {
        'sessionId': session_id,
        'studentNo': '1',
        'pages[0]': (BytesIO(b"some initial text data"), 'test.txt')
    }

    response = client.post('/marking/submission',
                           headers={'Authorization': f'Bearer {access_token}'},
                           data=data,
                           content_type='multipart/form-data')
    
    assert response.status_code == 201
    submission_data = response.get_json()
    assert submission_data['message'] == "Submission added successfully"
    assert submission_data['nextStudent'] == 2
    
    with app.app_context():
        submission = StudentSubmission.query.filter_by(session_id=session_id, student_no=1).first()
        assert submission is not None
        assert len(submission.pages) == 1

def test_finish_session(client, app, db):
    """
    GIVEN a marking session in 'ready' state
    WHEN a POST request is made to /marking/finish
    THEN the session status is updated to 'pending'
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']
    user_id = tokens['user']['id']

    with app.app_context():
        session = MarkingSession(user_id=user_id, year=2023, status="ready")
        db.session.add(session)
        db.session.commit()
        session_id = session.id

    response = client.post('/marking/finish',
                           headers={'Authorization': f'Bearer {access_token}'},
                           data=json.dumps({'sessionId': session_id}),
                           content_type='application/json')
    
    assert response.status_code == 200
    finish_data = response.get_json()
    assert finish_data['message'] == "Session marked as pending and is ready for processing"
    assert finish_data['session']['status'] == 'pending'

    with app.app_context():
        finished_session = MarkingSession.query.get(session_id)
        assert finished_session.status == 'pending'

def test_select_feedback(client, app, db):
    """
    GIVEN a submission with feedback
    WHEN a POST request is made to /marking/select-feedback
    THEN the selected feedback is updated
    """
    tokens = _login_user(client, db, app)
    access_token = tokens['access_token']
    user_id = tokens['user']['id']

    submission_id = None
    feedback_id_to_select = None
    other_feedback_id = None

    with app.app_context():
        session = MarkingSession(user_id=user_id, year=2023, status="ready")
        db.session.add(session)
        db.session.flush()

        submission = StudentSubmission(session_id=session.id, student_no=1)
        db.session.add(submission)
        db.session.flush()

        feedback1 = MarkingFeedback(submission_id=submission.id, description="Good work")
        feedback2 = MarkingFeedback(submission_id=submission.id, description="Needs improvement")
        db.session.add_all([feedback1, feedback2])
        db.session.commit()

        submission_id = submission.id
        feedback_id_to_select = feedback1.id
        other_feedback_id = feedback2.id

    data = {
        'submissionId': submission_id,
        'feedbackId': feedback_id_to_select
    }

    response = client.post('/marking/select-feedback',
                           headers={'Authorization': f'Bearer {access_token}'},
                           data=json.dumps(data),
                           content_type='application/json')
    
    assert response.status_code == 200

    with app.app_context():
        selected_feedback = MarkingFeedback.query.get(feedback_id_to_select)
        assert selected_feedback.is_selected is True
        
        other_feedback = MarkingFeedback.query.get(other_feedback_id)
        assert other_feedback.is_selected is False
