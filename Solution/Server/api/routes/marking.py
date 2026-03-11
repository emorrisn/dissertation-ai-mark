from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.extensions import db
from api.models import SessionFile, UserSession, MarkingSession, MarkScheme

marking_bp = Blueprint("marking", __name__)

@marking_bp.route("/", methods=["POST"])
@jwt_required()
def create_session():
    user_id = int(get_jwt_identity())

    year = request.form.get("year")
    students_amount = request.form.get("studentsAmount")
    notes = request.form.get("notes")
    required_outputs = request.form.getlist("requiredOutputs[]")

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
    while True:
        contents = request.form.get(f"markschemes[{index}][contents]")
        file = request.files.get(f"markschemes[{index}][file]")

        if not contents and not file:
            break

        file_record = None

        if file:
            storage_path = f"uploads/markschemes/{file.filename}"
            file.save(storage_path)

            file_record = SessionFile(
                name=file.filename,
                url=storage_path,
                storage_url=storage_path,
                size=len(file.read())
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

    db.session.commit()

    return jsonify(session.to_dict()), 201


@marking_bp.route("/", methods=["GET"])
@jwt_required()
def list_sessions():
    user_id = int(get_jwt_identity())

    sessions = MarkingSession.query.filter_by(user_id=user_id).all()

    return jsonify([
        {"id": s.id, "status": s.status, "created_at": s.created_at.isoformat() if s.created_at else None}
        for s in sessions
    ])
