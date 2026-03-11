from api.extensions import db
from datetime import datetime
import uuid


class UserSession(db.Model):
    __tablename__ = "user_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)

    refresh_token_hash = db.Column(db.String(255), nullable=True)

    revoked = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "ipAddress": self.ip_address,
            "userAgent": self.user_agent,
            "revoked": self.revoked,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "lastActive": self.last_active.isoformat() if self.last_active else None,
        }