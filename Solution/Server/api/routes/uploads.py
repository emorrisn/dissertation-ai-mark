from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.extensions import db
from api.models import SessionFile, StudentSubmission, MarkingSession, MarkScheme, SubmissionPage, UserUpdate
from werkzeug.utils import secure_filename
from sqlalchemy.orm import selectinload
from flask import send_from_directory
import uuid
import os

uploads_bp = Blueprint("uploads", __name__)

@uploads_bp.route('/<path:filepath>')
@jwt_required()
def serve_upload(filepath):
    # Step up one level from the 'api' folder to the project root
    project_root = os.path.dirname(current_app.root_path)
    
    # Now join it with 'uploads'
    uploads_folder = os.path.join(project_root, 'uploads')
    
    # Debugging prints to verify the paths
    print(f"Project Root: {project_root}")
    print(f"Target Uploads Folder: {uploads_folder}")
    print(f"Requested Filepath: {filepath}")

    return send_from_directory(uploads_folder, filepath)