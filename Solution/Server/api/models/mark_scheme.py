import uuid
from api.extensions import db
from datetime import datetime

class MarkScheme(db.Model):
    __tablename__ = "mark_schemes"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    session_id = db.Column(
        db.String(36),
        db.ForeignKey("marking_sessions.id"),
        nullable=False
    )

    file_id = db.Column(db.String(36), db.ForeignKey("session_files.id"))
    file = db.relationship("SessionFile")

    contents = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "sessionId": self.session_id,
            "file": self.file.to_dict() if self.file else None,
            "contents": self.contents,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat()
        }