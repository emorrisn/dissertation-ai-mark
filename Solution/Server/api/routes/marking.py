from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.extensions import db
from api.models import SessionFile, StudentSubmission, MarkingSession, MarkScheme, SubmissionPage, UserUpdate
from werkzeug.utils import secure_filename
from sqlalchemy.orm import selectinload
import uuid
import os

marking_bp = Blueprint("marking", __name__)

@marking_bp.route("/start", methods=["POST"])
@jwt_required()
def create_session():
    user_id = get_jwt_identity()

    year = request.form.get("year")
    students_amount = request.form.get("studentsAmount")
    notes = request.form.get("notes")
    required_outputs = request.form.getlist("requiredOutputs[]")

    if not year:
        return jsonify({"error": "year is required"}), 400
    
    year = int(year)
    students_amount = int(students_amount) if students_amount else 0

    session = MarkingSession(
        user_id=user_id,
        year=year,
        students_amount=students_amount,
        required_outputs=required_outputs,
        notes=notes,
        status="ready"
    )

    db.session.add(session)
    db.session.flush()

    # handle markschemes
    index = 0
    while f"markschemes[{index}][contents]" in request.form or \
      f"markschemes[{index}][file]" in request.files:
        
        contents = request.form.get(f"markschemes[{index}][contents]")
        file = request.files.get(f"markschemes[{index}][file]")

        if not contents and not file:
            break

        file_record = None

        if file:
            upload_dir = f"uploads/markschemes/{session.id}" 

            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            storage_path = f"{upload_dir}/{filename}"
            size = file.content_length or 0

            os.makedirs(upload_dir, exist_ok=True)
            file.save(storage_path)

            file_record = SessionFile(
                name=filename,
                url=storage_path,
                storage_url=storage_path,
                size=size
            )

            db.session.add(file_record)
            db.session.flush()

        scheme = MarkScheme(
            session_id=session.id,
            contents=contents,
            file_id=file_record.id if file_record else None
        )

        db.session.add(scheme)

        index += 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create session"}), 500

    return jsonify({
        **session.to_dict(),
        "markschemes": [m.to_dict() for m in session.markschemes]
    }), 201


@marking_bp.route("/submission", methods=["POST"])
@jwt_required()
def add_submission():
    user_id = get_jwt_identity()
    
    # Extract sessionId from the form data instead of the URL
    session_id = request.form.get("sessionId")
    if not session_id:
        return jsonify({"error": "sessionId is required"}), 400

    # Verify session exists and belongs to user
    session = MarkingSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    if session.status != 'ready':
        return jsonify({"error": f"Cannot add submissions. Session is currently '{session.status}'."}), 403

    # Get Student Number
    student_no = request.form.get("studentNo", type=int)
    if not student_no:
        return jsonify({"error": "studentNo is required"}), 400

    # Create or update StudentSubmission
    submission = StudentSubmission.query.filter_by(session_id=session_id, student_no=student_no).first()
    if not submission:
        submission = StudentSubmission(session_id=session_id, student_no=student_no)
        db.session.add(submission)
        db.session.flush()

    # rocess Images (Pages)
    upload_dir = f"uploads/submissions/{session_id}/student_{student_no}"
    os.makedirs(upload_dir, exist_ok=True)

    index = 0
    while f"pages[{index}]" in request.files:
        file = request.files.get(f"pages[{index}]")
        if file:
            filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
            storage_path = f"{upload_dir}/{filename}"
            file.save(storage_path)
            
            # Create SessionFile
            file_record = SessionFile(
                name=filename,
                url=storage_path,
                storage_url=storage_path,
                size=file.content_length or 0
            )
            db.session.add(file_record)
            db.session.flush()
            
            # Create SubmissionPage linking to the File and Submission
            page = SubmissionPage(
                submission_id=submission.id,
                page_no=index + 1,
                file_id=file_record.id
            )
            db.session.add(page)
        
        index += 1

    # Determine the next student and update the session state
    next_student = student_no + 1
    session.selected_student = next_student
    
    # If we are adding a student beyond the initial amount, increase the max limit
    if next_student > session.students_amount:
        session.students_amount = next_student

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to save submission"}), 500

    return jsonify({
        "message": "Submission added successfully",
        "nextStudent": next_student,
        "submission": submission.to_dict()
    }), 201

@marking_bp.route("/finish", methods=["POST"])
@jwt_required()
def finish_session():
    user_id = get_jwt_identity()
    
    # Using JSON for this one since we just need the ID, no files
    data = request.get_json() or {}
    session_id = data.get("sessionId")

    if not session_id:
        return jsonify({"error": "sessionId is required"}), 400

    session = MarkingSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404

    if session.status != 'ready':
        return jsonify({"error": f"Session is already '{session.status}'"}), 400

    # Update the status and mark the end time
    session.status = "pending"
    session.ended_at = datetime.utcnow()

    update = UserUpdate(
        user_id=user_id,
        type="MarkingSessionUpdate",
        title="Processing Pending",
        message="Your marking session has been added to the processing queue, you will be notified with updates.",
    )

    db.session.add(update)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to finish session"}), 500

    return jsonify({
        "message": "Session marked as pending and is ready for processing",
        "session": session.to_dict()
    }), 200


@marking_bp.route("/sessions", methods=["GET"])
@jwt_required()
def list_sessions():
    user_id = get_jwt_identity()

    sessions = (
        MarkingSession.query
        .options(
            selectinload(MarkingSession.markschemes),
            selectinload(MarkingSession.student_submissions)
            .selectinload(StudentSubmission.pages)
            .selectinload(SubmissionPage.file)
        )
        .filter_by(user_id=user_id)
        .order_by(MarkingSession.created_at.desc())
        .limit(50)
        .all()
    )

    return jsonify([
        {
            **s.to_dict(),
            "markschemes": [m.to_dict() for m in s.markschemes],
            "studentSubmissions": [sub.to_dict() for sub in s.student_submissions]
        }
        for s in sessions
    ])