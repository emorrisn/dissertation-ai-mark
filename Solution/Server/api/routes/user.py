from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.extensions import db
from api.models.user import User
from api.models.user_update import UserUpdate

user_bp = Blueprint("user", __name__)

## Profile

@user_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    # Get the ID of the user making the request from the JWT
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()

    # Safely update fields if they are provided in the payload
    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        user.email = data["email"]
    if "username" in data:
        user.username = data["username"]
    if "writingStyle" in data:
        user.writing_style = data["writingStyle"] # Assuming snake_case in your DB

    try:
        db.session.commit()
        # Return the updated profile. Adjust the keys to match your UserProfile type
        return jsonify({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "username": user.username,
            "writingStyle": user.writing_style
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating profile: {e}")
        return jsonify({"error": "Failed to update profile"}), 500
    
@user_bp.route("/profile", methods=["DELETE"])
@jwt_required()
def delete_account():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Account deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete account"}), 500
    

## Password
    
@user_bp.route("/password", methods=["PUT"])
@jwt_required()
def change_password():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    current_password = data.get("currentPassword")
    new_password = data.get("newPassword")

    # Verify the current password before allowing a change
    if not user.check_password(current_password):
        return jsonify({"error": "Incorrect current password"}), 400

    if not new_password or len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400

    try:
        user.set_password(new_password)

        update = UserUpdate(
            user_id=user.id,
            type="SecurityUpdate",
            title="Password Changed",
            message="Your account password was successfully changed. If this wasn't you, please contact support immediately.",
            link="/dashboard/settings/security"
        )

        db.session.add(update)
        db.session.commit()
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update password"}), 500
    
## Updates

@user_bp.route("/updates", methods=["GET"])
@jwt_required()
def get_updates():
    current_user_id = get_jwt_identity()
    updates = UserUpdate.query.filter_by(user_id=current_user_id).order_by(UserUpdate.created_at.desc()).all()

    return jsonify([u.to_dict() for u in updates]), 200

@user_bp.route("/updates/<update_id>/read", methods=["POST"])
@jwt_required()
def mark_update_as_read(update_id):
    current_user_id = get_jwt_identity()
    update = UserUpdate.query.filter_by(id=update_id, user_id=current_user_id).first()

    if not update:
        return jsonify({"error": "Update not found"}), 404

    try:
        update.is_read = True
        db.session.commit()
        return jsonify({"message": "Update marked as read"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to mark update as read"}), 500