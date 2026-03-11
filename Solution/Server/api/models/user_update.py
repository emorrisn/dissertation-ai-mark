from api.extensions import db
from datetime import datetime
import uuid


class UserUpdate(db.Model):
    __tablename__ = "user_updates"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    type = db.Column(db.String(50), nullable=False)  # e.g., 'MarkingSessionUpdate', 'NewFeature', 'SystemMessage'
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(255), nullable=True)  # Optional link for more details
    related_id = db.Column(db.String(36), nullable=True)  # ID of related entity (e.g., marking session ID)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "isRead": self.is_read,
            "link": self.link,
            "relatedId": self.related_id,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }