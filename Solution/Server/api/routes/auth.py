from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from api.extensions import db
from api.models import UserSession, User
from flask import current_app, request as flask_request
import hashlib


auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Safely extract data to avoid KeyErrors
    username = data.get("username")
    password = data.get("password")
    institute_code = data.get("institute_code")

    # Ensure required fields are present
    if not all([username, password, institute_code]):
        return jsonify({"message": "Missing required fields: username, password, or institute_code"}), 400

    if User.query.filter_by(
        username=username,
        institute_code=institute_code
    ).first():
        return jsonify({"message": "User already exists"}), 400

    user = User(
        username=username,
        name=data.get("name", username), # Fallback to username if name isn't provided
        institute_code=institute_code,
        email=data.get("email")
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    session = UserSession(
        user_id=user.id,
        ip_address=flask_request.remote_addr,
        user_agent=flask_request.headers.get("User-Agent")
    )

    db.session.add(session)
    db.session.commit()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "session_id": session.id
        }
    )

    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={"session_id": session.id}
    )

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")
    institute_code = data.get("institute_code")

    user = User.query.filter_by(
        username=username,
        institute_code=institute_code
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid credentials"}), 401

    session = UserSession(
        user_id=user.id,
        ip_address=flask_request.remote_addr,
        user_agent=flask_request.headers.get("User-Agent")
    )

    db.session.add(session)
    db.session.flush()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"session_id": session.id}
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={"session_id": session.id}
    )

    session.refresh_token_hash = generate_password_hash(refresh_token)
    db.session.commit()

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    }), 200


@auth_bp.route("/session", methods=["GET"])
@jwt_required()
def session():

    user_id = get_jwt_identity()
    claims = get_jwt()

    session_id = claims.get("session_id")

    session = UserSession.query.get(session_id)

    if not session or session.revoked:
        return jsonify({"message": "Session revoked"}), 401

    user = User.query.get(user_id)

    return jsonify(user.to_dict()), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    claims = get_jwt()
    session_id = claims.get("session_id")

    # The raw token sent by the frontend in the Authorization header
    auth_header = flask_request.headers.get("Authorization")
    raw_refresh_token = auth_header.split(" ")[1] if auth_header else None

    # Find the session in your DB
    session = UserSession.query.get(session_id)

    # Security Checks
    if not session:
        return jsonify({"message": "Session not found"}), 401
        
    if session.revoked:
        return jsonify({"message": "Session revoked"}), 401

    if not session.refresh_token_hash or not check_password_hash(session.refresh_token_hash, raw_refresh_token):
        return jsonify({"message": "Invalid refresh token"}), 401

    # Update the last_active timestamp
    session.last_active = datetime.utcnow()
    db.session.commit()

    # Issue a new access token
    new_access_token = create_access_token(
        identity=user_id,
        additional_claims={"session_id": session_id}
    )

    return jsonify({"access_token": new_access_token}), 200

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():

    claims = get_jwt()
    session_id = claims.get("session_id")

    session = UserSession.query.get(session_id)

    if session:
        session.revoked = True
        db.session.commit()

    return jsonify({"message": "Logged out"}), 200